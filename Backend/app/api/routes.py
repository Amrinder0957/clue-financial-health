import json
import math
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from app.application.analysis_service import build_analysis_report
from app.infrastructure.database import SessionLocal, AnalysisRecord
from app.domain.prediction.simulator import simulate_expense_reduction


router = APIRouter()


# =========================
# WHAT-IF REQUEST
# =========================

class WhatIfRequest(BaseModel):
    current_balance: float
    average_daily_inflow: float
    average_daily_outflow: float
    reduction_percent: float = Field(
        ge=0,
        le=100,
    )


# =========================
# JSON CLEANING
# =========================

def clean_json_value(value):
    if isinstance(value, float) and math.isinf(value):
        return "infinite"

    if isinstance(value, float) and math.isnan(value):
        return None

    if isinstance(value, dict):
        return {
            key: clean_json_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            clean_json_value(item)
            for item in value
        ]

    return value


# =========================
# HEALTH
# =========================

@router.get("/health")
def health():
    return {
        "status": "ok",
        "message": "CLUE API is running",
    }


# =========================
# SCHEMA
# =========================

@router.get("/meta/schema")
def schema():
    return {
        "required": ["date", "amount"],
        "optional": [
            "direction",
            "description",
            "counterparty",
            "category",
            "account",
            "txn_id",
            "balance",
        ],
    }


# =========================
# CREATE ANALYSIS
# =========================

@router.post("/analyses")
async def create_analysis(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A CSV file is required.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    try:

        report = build_analysis_report(
            content=content,
            filename=file.filename,
        )

        analysis_id = str(uuid.uuid4())

        report_data = clean_json_value({

            "score": report.score.overall_score,

            "band": report.score.band,

            "provisional": report.score.provisional,

            "cash_flow_score":
                report.score.cash_flow_score,

            "anomaly_score":
                report.score.anomaly_score,

            "credit_debt_score":
                report.score.credit_debt_score,

            "prediction":
                report.prediction.__dict__,

            "risks":
                [
                    risk.__dict__
                    for risk in report.risks
                ],

            "explanations":
                [
                    item.__dict__
                    for item in report.explanations
                ],

            "recommendations":
                [
                    item.__dict__
                    for item in report.recommendations
                ],
        })

        db = SessionLocal()

        try:

            record = AnalysisRecord(
                id=analysis_id,
                filename=file.filename,
                report_json=json.dumps(
                    report_data,
                    default=str,
                ),
            )

            db.add(record)
            db.commit()

        finally:
            db.close()

        return {
            "status": "completed",
            "analysis_id": analysis_id,
            "filename": file.filename,
            **report_data,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================
# GET SAVED ANALYSIS
# =========================

@router.get("/analyses/{analysis_id}")
def get_analysis(
    analysis_id: str
):

    db = SessionLocal()

    try:

        record = (
            db.query(AnalysisRecord)
            .filter(
                AnalysisRecord.id == analysis_id
            )
            .first()
        )

        if record is None:

            raise HTTPException(
                status_code=404,
                detail="Analysis not found.",
            )

        return {
            "analysis_id": record.id,
            "filename": record.filename,
            "created_at": record.created_at,
            "report": json.loads(
                record.report_json
            ),
        }

    finally:
        db.close()


# =========================
# WHAT-IF SIMULATOR
# =========================

@router.post("/what-if")
def run_what_if(
    request: WhatIfRequest
):

    try:

        result = simulate_expense_reduction(

            current_balance=
                request.current_balance,

            average_daily_inflow=
                request.average_daily_inflow,

            average_daily_outflow=
                request.average_daily_outflow,

            reduction_percent=
                request.reduction_percent,
        )

        return clean_json_value({

            "reduction_percent":
                request.reduction_percent,

            "original_runway_days":
                result.original_runway_days,

            "scenario_runway_days":
                result.scenario_runway_days,

            "runway_change_days":
                result.runway_change_days,

            "description":
                 result.scenario_description,
    
        })

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )