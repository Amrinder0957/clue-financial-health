from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Recommendation:
    risk_id: str
    priority: str
    action: str
    reason: str


def recommend_for_risk(
    risk_id: str,
    severity: str,
) -> Recommendation:

    if risk_id == "CF-001":
        action = (
            "Review upcoming expenses and reduce non-essential spending "
            "to protect short-term cash reserves."
        )
        reason = (
            "Your estimated cash runway is low, so controlling outflows "
            "can help prevent a cash shortfall."
        )

    elif risk_id == "CF-002":
        action = (
            "Review operating expenses and improve incoming cash collection."
        )
        reason = (
            "Cash outflows are putting pressure on incoming cash."
        )

    elif risk_id == "CF-003":
        action = (
            "Review the recent balance decline and identify the main "
            "sources of increasing cash pressure."
        )
        reason = (
            "The balance trend is deteriorating based on recent "
            "cash-flow movement."
        )

    elif risk_id == "CF-004":
        action = (
            "Reduce dependency on the largest customer by developing "
            "additional revenue sources."
        )
        reason = (
            "A large share of incoming revenue depends on one counterparty."
        )

    elif risk_id == "ANOMALY_001":
        action = (
            "Review unusually large transactions and verify their "
            "business purpose before taking further action."
        )
        reason = (
            "Statistical analysis identified unusually large transaction "
            "amounts."
        )

    elif risk_id == "ANOMALY_002":
        action = (
            "Review repeated round-number transactions for supporting "
            "invoices or business records."
        )
        reason = (
            "A high number of transactions follow a round-number pattern."
        )

    elif risk_id == "ANOMALY_003":
        action = (
            "Review transactions occurring outside normal operating hours "
            "and verify that they are expected."
        )
        reason = (
            "Transactions were detected outside the available normal "
            "activity window."
        )

    elif risk_id == "ANOMALY_004":
        action = (
            "Review dependency on major counterparties and consider "
            "diversifying important business relationships."
        )
        reason = (
            "A large share of transaction value is concentrated with "
            "one counterparty."
        )

    elif risk_id == "CD-001":
        action = (
            "Review debt repayments and consider restructuring or "
            "reducing high-cost debt where appropriate."
        )
        reason = (
            "Debt-related payments represent a significant share "
            "of incoming cash."
        )

    elif risk_id == "CD-002":
        action = (
            "Review the account balance buffer and upcoming payments "
            "to reduce overdraft pressure."
        )
        reason = (
            "The recorded balance indicates possible overdraft distress."
        )

    elif risk_id == "CD-003":
        action = (
            "Review recurring penalties and fees and identify the "
            "transactions causing them."
        )
        reason = (
            "Repeated penalty or fee transactions were detected."
        )

    else:
        action = (
            "Review the flagged financial activity and verify the "
            "underlying transactions."
        )
        reason = (
            "The analysis identified a financial pattern that requires review."
        )

    return Recommendation(
        risk_id=risk_id,
        priority=severity,
        action=action,
        reason=reason,
    )