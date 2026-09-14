from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Risk:
    risk_id: str
    category: str
    severity: str
    title: str
    explanation: str
    evidence: dict


def detect_cash_flow_risks(
    runway_days: float,
    ending_balance: float,
    inflow_outflow_ratio: float,
    net_cash_flow: float,
    balance_slope: float = 0.0,
    average_daily_outflow: float = 0.0,
    top_inflow_counterparty_ratio: float = 0.0,
) -> list[Risk]:

    risks: list[Risk] = []

    # CF-001: Runway Depletion Risk
    if ending_balance <= 0 or runway_days < 15:
        severity = "CRITICAL"
    elif runway_days < 30:
        severity = "HIGH"
    elif runway_days < 60:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    if severity != "LOW":
        risks.append(
            Risk(
                risk_id="CF-001",
                category="cash_flow",
                severity=severity,
                title="Runway Depletion Risk",
                explanation=(
                    "Current cash reserves cover fewer than "
                    "30 days at recent spending rates."
                ),
                evidence={
                    "ending_balance": ending_balance,
                    "average_daily_outflow": average_daily_outflow,
                    "runway_days": runway_days,
                },
            )
        )

    # CF-002: Operating Deficit Risk
    if inflow_outflow_ratio < 0.60 and net_cash_flow < 0:
        severity = "CRITICAL"
    elif inflow_outflow_ratio < 0.85 and net_cash_flow < 0:
        severity = "HIGH"
    elif inflow_outflow_ratio < 1.00 and net_cash_flow < 0:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    if severity != "LOW":
        risks.append(
            Risk(
                risk_id="CF-002",
                category="cash_flow",
                severity=severity,
                title="Operating Deficit Risk",
                explanation=(
                    "Outgoing cash is exceeding incoming cash, "
                    "creating a negative operating cash flow."
                ),
                evidence={
                    "inflow_outflow_ratio": inflow_outflow_ratio,
                    "net_cash_flow": net_cash_flow,
                },
            )
        )

    # CF-003: Balance Trajectory Risk
    if balance_slope < 0 and average_daily_outflow > 0:
        relative_decline_ratio = (
            abs(balance_slope) / average_daily_outflow
        )
    else:
        relative_decline_ratio = 0.0

    if balance_slope < 0 and relative_decline_ratio >= 0.50:
        severity = "CRITICAL"
    elif balance_slope < 0 and relative_decline_ratio >= 0.20:
        severity = "HIGH"
    elif balance_slope < 0 and relative_decline_ratio >= 0.05:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    if severity != "LOW":
        risks.append(
            Risk(
                risk_id="CF-003",
                category="cash_flow",
                severity=severity,
                title="Balance Trajectory Risk",
                explanation=(
                    "The business balance is showing a declining "
                    "trajectory relative to recent spending."
                ),
                evidence={
                    "balance_slope": balance_slope,
                    "average_daily_outflow": average_daily_outflow,
                    "relative_decline_ratio": relative_decline_ratio,
                },
            )
        )

    # CF-004: Revenue Concentration Risk
    if top_inflow_counterparty_ratio >= 0.70:
        severity = "CRITICAL"
    elif top_inflow_counterparty_ratio >= 0.50:
        severity = "HIGH"
    elif top_inflow_counterparty_ratio >= 0.35:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    if severity != "LOW":
        risks.append(
            Risk(
                risk_id="CF-004",
                category="cash_flow",
                severity=severity,
                title="Revenue Concentration Risk",
                explanation=(
                    "A high proportion of incoming revenue depends "
                    "on a single customer or counterparty."
                ),
                evidence={
                    "top_inflow_counterparty_ratio":
                        top_inflow_counterparty_ratio,
                },
            )
        )

    return risks
def detect_anomaly_risks(
    max_z_score: float,
    round_number_percentage: float,
    off_hours_percentage: float,
    counterparty_concentration: float,
) -> list[Risk]:

    risks: list[Risk] = []

    # ANOMALY-001: Statistical Outlier
    if max_z_score >= 4:
        severity = "CRITICAL"
    elif max_z_score >= 3:
        severity = "HIGH"
    elif max_z_score >= 2:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    if severity != "LOW":
        risks.append(
            Risk(
                risk_id="ANOMALY-001",
                category="anomaly",
                severity=severity,
                title="Statistical Transaction Outlier",
                explanation="One or more transactions are unusually large compared with the rest of the dataset.",
                evidence={"max_z_score": max_z_score},
            )
        )

    # ANOMALY-002: Round Number Pattern
    if round_number_percentage > 35:
        severity = "CRITICAL"
    elif round_number_percentage >= 20:
        severity = "HIGH"
    elif round_number_percentage >= 10:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    if severity != "LOW":
        risks.append(
            Risk(
                risk_id="ANOMALY-002",
                category="anomaly",
                severity=severity,
                title="Round Number Pattern",
                explanation="A high proportion of transactions use round-number amounts and may require review.",
                evidence={"round_number_percentage": round_number_percentage},
            )
        )

    # ANOMALY-003: Off-Hours Activity
    if off_hours_percentage > 30:
        severity = "CRITICAL"
    elif off_hours_percentage > 15:
        severity = "HIGH"
    elif off_hours_percentage >= 5:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    if severity != "LOW":
        risks.append(
            Risk(
                risk_id="ANOMALY-003",
                category="anomaly",
                severity=severity,
                title="Off-Hours Activity",
                explanation="A significant proportion of transactions occurred outside normal operating hours.",
                evidence={"off_hours_percentage": off_hours_percentage},
            )
        )

    # ANOMALY-004: Counterparty Concentration
    if counterparty_concentration >= 0.75:
        severity = "CRITICAL"
    elif counterparty_concentration >= 0.50:
        severity = "HIGH"
    elif counterparty_concentration >= 0.30:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    if severity != "LOW":
        risks.append(
            Risk(
                risk_id="ANOMALY-004",
                category="anomaly",
                severity=severity,
                title="Counterparty Concentration",
                explanation="A large share of transaction value is concentrated with one counterparty.",
                evidence={"counterparty_concentration": counterparty_concentration},
            )
        )

    return risks
def detect_credit_debt_risks(
    debt_service_burden: float,
    min_balance: float | None,
    average_daily_outflow: float,
    penalty_fee_count: int,
    total_inflow: float,
    debt_outflow: float,
) -> list[Risk]:

    risks: list[Risk] = []

    # CD-001: Debt Service Burden
    if total_inflow == 0:
        severity = "CRITICAL" if debt_outflow > 0 else "LOW"
    elif debt_service_burden > 0.45:
        severity = "CRITICAL"
    elif debt_service_burden > 0.30:
        severity = "HIGH"
    elif debt_service_burden > 0.15:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    if severity != "LOW":
        risks.append(
            Risk(
                risk_id="CD-001",
                category="credit_debt",
                severity=severity,
                title="Debt Service Burden",
                explanation="Debt-related payments consume a significant share of incoming cash.",
                evidence={
                    "debt_service_burden": debt_service_burden,
                    "debt_outflow": debt_outflow,
                    "total_inflow": total_inflow,
                },
            )
        )

    # CD-002: Overdraft Distress
    if min_balance is not None:
        if (
            min_balance < 0
            and min_balance < -average_daily_outflow
        ):
            severity = "CRITICAL"
        elif min_balance < 0:
            severity = "HIGH"
        elif min_balance == 0:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        if severity != "LOW":
            risks.append(
                Risk(
                    risk_id="CD-002",
                    category="credit_debt",
                    severity=severity,
                    title="Overdraft Distress",
                    explanation="The recorded balance indicates possible cash-balance distress.",
                    evidence={
                        "minimum_balance": min_balance,
                        "average_daily_outflow": average_daily_outflow,
                    },
                )
            )

    # CD-003: Penalty and Fee Frequency
    if penalty_fee_count > 3:
        severity = "CRITICAL"
    elif penalty_fee_count >= 2:
        severity = "HIGH"
    elif penalty_fee_count == 1:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    if severity != "LOW":
        risks.append(
            Risk(
                risk_id="CD-003",
                category="credit_debt",
                severity=severity,
                title="Penalty and Fee Frequency",
                explanation="Repeated penalties or financial distress fees were detected.",
                evidence={
                    "penalty_fee_count": penalty_fee_count,
                },
            )
        )

    return risks