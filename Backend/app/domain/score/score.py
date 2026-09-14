from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthScore:
    cash_flow_score: float
    anomaly_score: float
    credit_debt_score: float
    overall_score: int
    band: str
    provisional: bool


def score_runway(runway_days: float) -> float:
    if runway_days == float("inf") or runway_days >= 90:
        return 100.0
    if runway_days >= 30:
        return 80.0
    if runway_days >= 15:
        return 50.0
    if runway_days > 0:
        return 20.0
    return 0.0


def score_inflow_outflow_ratio(ratio: float) -> float:
    if ratio == float("inf"):
        return 100.0
    if ratio >= 1.20:
        return 100.0
    if ratio >= 1.00:
        return 80.0
    if ratio >= 0.80:
        return 50.0
    return 20.0


def calculate_cash_flow_score(
    runway_days: float,
    inflow_outflow_ratio: float,
) -> float:
    runway_score = score_runway(runway_days)
    ratio_score = score_inflow_outflow_ratio(inflow_outflow_ratio)

    return (runway_score + ratio_score) / 2


def calculate_anomaly_score(
    zscore_count: int,
    round_number_count: int,
    off_hours_count: int,
) -> float:
    score = (
        100
        - (zscore_count * 10)
        - (round_number_count * 5)
        - (off_hours_count * 5)
    )

    return max(0.0, float(score))


def score_debt_service_burden(
    debt_service_burden: float,
    total_inflow: float,
    debt_outflow: float,
) -> float:
    if total_inflow == 0:
        return 0.0 if debt_outflow > 0 else 0.0

    if debt_service_burden <= 0:
        return 100.0
    if debt_service_burden <= 0.15:
        return 90.0
    if debt_service_burden <= 0.30:
        return 70.0
    if debt_service_burden <= 0.45:
        return 40.0

    return 0.0


def calculate_overall_score(
    cash_flow_score: float,
    anomaly_score: float,
    credit_debt_score: float,
) -> HealthScore:

    overall = round(
        (cash_flow_score * 0.40)
        + (anomaly_score * 0.30)
        + (credit_debt_score * 0.30)
    )

    if overall >= 80:
        band = "Stable"
    elif overall >= 60:
        band = "Watch"
    elif overall >= 40:
        band = "Strained"
    else:
        band = "Critical"

    return HealthScore(
        cash_flow_score=cash_flow_score,
        anomaly_score=anomaly_score,
        credit_debt_score=credit_debt_score,
        overall_score=overall,
        band=band,
        provisional=False,
    )