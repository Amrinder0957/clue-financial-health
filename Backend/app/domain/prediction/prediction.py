from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Prediction:
    runway_days: float
    trend: str
    warning: str
    confidence: str

    # Values used by the What-If Simulator
    current_balance: float
    average_daily_inflow: float
    average_daily_outflow: float


def calculate_prediction(
    current_balance: float,
    average_daily_inflow: float,
    average_daily_outflow: float,
    balance_trend: str,
    confidence: str,
) -> Prediction:

    net_daily_cash_flow = (
        average_daily_inflow - average_daily_outflow
    )

    if net_daily_cash_flow >= 0:
        runway_days = float("inf")

    elif current_balance <= 0:
        runway_days = 0.0

    else:
        runway_days = (
            current_balance / abs(net_daily_cash_flow)
        )

    if balance_trend == "IMPROVING":
        trend = "IMPROVING"

    elif balance_trend == "DETERIORATING":
        trend = "DETERIORATING"

    elif balance_trend == "STABLE":
        trend = "STABLE"

    else:
        trend = "INSUFFICIENT_DATA"

    if runway_days == float("inf"):

        warning = (
            "Current cash flow is not showing cash depletion "
            "if the present pattern continues."
        )

    elif runway_days <= 15:

        warning = (
            "At the current cash-flow rate, available cash "
            "may be depleted within 15 days."
        )

    elif runway_days <= 30:

        warning = (
            "At the current cash-flow rate, available cash "
            "may be depleted within 30 days."
        )

    else:

        warning = (
            "Current cash-flow patterns provide more than "
            "30 days of estimated runway."
        )

    return Prediction(
        runway_days=runway_days,
        trend=trend,
        warning=warning,
        confidence=confidence,
        current_balance=current_balance,
        average_daily_inflow=average_daily_inflow,
        average_daily_outflow=average_daily_outflow,
    )