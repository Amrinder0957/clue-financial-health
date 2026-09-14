from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Explanation:
    risk_id: str
    title: str
    severity: str
    explanation: str
    evidence: dict


def explain_risk(
    risk_id: str,
    severity: str,
    evidence: dict,
) -> Explanation:

    if risk_id == "CF-001":
        runway = evidence.get("runway_days", 0)
        explanation = (
            f"Your estimated cash runway is {runway:.1f} days "
            "at the current spending rate."
        )
        title = "Cash Runway Risk"

    elif risk_id == "CF-002":
        ratio = evidence.get("inflow_outflow_ratio", 0)
        explanation = (
            f"Your inflow-to-outflow ratio is {ratio:.2f}, "
            "showing that cash outflows are putting pressure on inflows."
        )
        title = "Operating Deficit Risk"

    elif risk_id == "CF-003":
        explanation = (
            "Your balance is showing a deteriorating trend "
            "based on recent cash-flow movement."
        )
        title = "Balance Trend Risk"

    elif risk_id == "CF-004":
        ratio = evidence.get("top_inflow_counterparty_ratio", 0)
        explanation = (
            f"Your largest incoming counterparty contributes "
            f"{ratio:.0%} of total inflows."
        )
        title = "Revenue Concentration Risk"

    elif risk_id == "ANOMALY_001":
        z_score = evidence.get("max_z_score_amount", 0)
        explanation = (
            f"The most unusual transaction has a statistical "
            f"z-score of {z_score:.2f}."
        )
        title = "Unusual Transaction Amount"

    elif risk_id == "ANOMALY_002":
        count = evidence.get("round_number_txn_count", 0)
        explanation = (
            f"{count} transactions match a round-number pattern "
            "and should be reviewed."
        )
        title = "Round-Number Transaction Pattern"

    elif risk_id == "ANOMALY_003":
        count = evidence.get("off_hours_txn_count", 0)
        explanation = (
            f"{count} transactions occurred outside normal hours "
            "and should be reviewed."
        )
        title = "Off-Hours Activity"

    elif risk_id == "ANOMALY_004":
        ratio = evidence.get("counterparty_concentration", 0)
        explanation = (
            f"A single counterparty represents approximately "
            f"{ratio:.0%} of transaction value."
        )
        title = "Counterparty Concentration"

    elif risk_id == "CD-001":
        burden = evidence.get("debt_service_burden", 0)
        explanation = (
            f"Debt-related outflows represent approximately "
            f"{burden:.0%} of total inflows."
        )
        title = "Debt Service Burden"

    elif risk_id == "CD-002":
        balance = evidence.get("minimum_balance", 0)
        explanation = (
            f"Your minimum recorded balance reached {balance}, "
            "indicating possible overdraft pressure."
        )
        title = "Overdraft Distress"

    elif risk_id == "CD-003":
        count = evidence.get("penalty_fee_count", 0)
        explanation = (
            f"{count} penalty or fee transactions were detected "
            "in the uploaded data."
        )
        title = "Penalty and Fee Frequency"

    else:
        explanation = "This risk was identified from the uploaded financial data."
        title = "Financial Risk"

    return Explanation(
        risk_id=risk_id,
        title=title,
        severity=severity,
        explanation=explanation,
        evidence=evidence,
    )