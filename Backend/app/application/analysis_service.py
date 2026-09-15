from __future__ import annotations

from dataclasses import dataclass, replace

import pandas as pd

from app.application.pipeline import run_data_pipeline
from app.domain.analytics.engine import calculate_features
from app.domain.explain.explain import Explanation, explain_risk
from app.domain.performance.performance import calculate_business_performance
from app.domain.prediction.prediction import (
    Prediction,
    calculate_prediction,
)
from app.domain.recommend.recommend import (
    Recommendation,
    recommend_for_risk,
)
from app.domain.risk.risk import (
    Risk,
    detect_anomaly_risks,
    detect_cash_flow_risks,
    detect_credit_debt_risks,
)
from app.domain.score.score import (
    HealthScore,
    calculate_anomaly_score,
    calculate_cash_flow_score,
    calculate_overall_score,
    score_debt_service_burden,
)


@dataclass(frozen=True)
class AnalysisReport:
    features: object
    score: HealthScore
    business_performance: object
    risks: list[Risk]
    explanations: list[Explanation]
    recommendations: list[Recommendation]
    prediction: Prediction


def build_analysis_report(
    content: bytes,
    filename: str | None = None,
) -> AnalysisReport:

    # 1. Clean and validate uploaded CSV
    ledger = run_data_pipeline(content, filename)
    transactions = ledger.transactions

    # 2. Calculate analytics
    features = calculate_features(transactions)

    # 3. Calculate Business Performance / cash-based P&L
    performance_rows = []

    for txn in transactions:
        performance_rows.append(
            {
                "date": getattr(txn, "date", None),
                "amount": float(getattr(txn, "amount", 0.0)),
                "direction": getattr(txn, "direction", ""),
            }
        )

    performance_df = pd.DataFrame(performance_rows)

    business_performance = calculate_business_performance(
        performance_df
    )

    # 4. Prepare anomaly indicators
    amounts = [
        float(txn.amount)
        for txn in transactions
    ]

    mean_amount = 0.0
    std_amount = 0.0
    max_z_score = 0.0

    if len(amounts) >= 2:
        mean_amount = sum(amounts) / len(amounts)

        variance = sum(
            (amount - mean_amount) ** 2
            for amount in amounts
        ) / len(amounts)

        std_amount = variance ** 0.5

        if std_amount > 0:
            max_z_score = max(
                abs((amount - mean_amount) / std_amount)
                for amount in amounts
            )

    # Count transactions with |Z| > 3
    zscore_count = 0

    if std_amount > 0:
        zscore_count = sum(
            1
            for amount in amounts
            if abs((amount - mean_amount) / std_amount) > 3
        )

    # Round-number transactions
    round_number_count = sum(
        1
        for txn in transactions
        if float(txn.amount).is_integer()
        and int(txn.amount) % 1000 == 0
    )

    round_number_percentage = (
        round_number_count / len(transactions)
        if transactions
        else 0.0
    )

    # Date-only CSVs have no time information
    off_hours_count = 0
    off_hours_percentage = 0.0

    # Counterparty concentration
    counterparty_concentration = max(
        features.top_inflow_counterparty_ratio,
        features.top_outflow_counterparty_ratio,
    )

    # 5. Detect risks
    anomaly_risks = detect_anomaly_risks(
        max_z_score=max_z_score,
        round_number_percentage=round_number_percentage,
        off_hours_percentage=off_hours_percentage,
        counterparty_concentration=counterparty_concentration,
    )

    cash_risks = detect_cash_flow_risks(
        runway_days=features.runway_days,
        ending_balance=float(features.ending_balance or 0),
        inflow_outflow_ratio=features.inflow_outflow_ratio,
        net_cash_flow=float(features.net_cash_flow),
        average_daily_outflow=features.average_daily_outflow,
        top_inflow_counterparty_ratio=(
            features.top_inflow_counterparty_ratio
        ),
    )

    credit_risks = detect_credit_debt_risks(
        debt_service_burden=features.debt_service_burden,
        min_balance=(
            float(features.minimum_balance)
            if features.minimum_balance is not None
            else None
        ),
        average_daily_outflow=features.average_daily_outflow,
        penalty_fee_count=0,
        total_inflow=float(features.total_inflow),
        debt_outflow=float(features.debt_outflow),
    )

    risks = [
        *cash_risks,
        *anomaly_risks,
        *credit_risks,
    ]

    # 6. Calculate authoritative pillar scores
    anomaly_score = calculate_anomaly_score(
        zscore_count=zscore_count,
        round_number_count=round_number_count,
        off_hours_count=off_hours_count,
    )

    cash_flow_score = calculate_cash_flow_score(
        features.runway_days,
        features.inflow_outflow_ratio,
    )

    credit_debt_score = score_debt_service_burden(
        features.debt_service_burden,
        float(features.total_inflow),
        float(features.debt_outflow),
    )

    score = calculate_overall_score(
        cash_flow_score,
        anomaly_score,
        credit_debt_score,
    )

    # Low-confidence datasets produce a provisional score
    if features.confidence == "LOW":
        score = replace(score, provisional=True)

    # 7. Prediction
    current_balance = (
        float(features.ending_balance)
        if features.ending_balance is not None
        else 0.0
    )

    prediction = calculate_prediction(
        current_balance=current_balance,
        average_daily_inflow=features.average_daily_inflow,
        average_daily_outflow=features.average_daily_outflow,
        balance_trend=features.balance_trend,
        confidence=features.confidence,
    )

    # 8. Explain every detected risk
    explanations = [
        explain_risk(
            risk_id=risk.risk_id,
            severity=risk.severity,
            evidence=risk.evidence,
        )
        for risk in risks
    ]

    # 9. Generate recommendations
    recommendations = [
        recommend_for_risk(
            risk_id=risk.risk_id,
            severity=risk.severity,
        )
        for risk in risks
    ]

    # 10. Final report
    return AnalysisReport(
        features=features,
        score=score,
        business_performance=business_performance,
        risks=risks,
        explanations=explanations,
        recommendations=recommendations,
        prediction=prediction,
    )