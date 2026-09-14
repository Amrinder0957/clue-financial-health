from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import date

from app.domain.ledger import CanonicalTransaction


@dataclass(frozen=True)
class LedgerFeatures:
    total_inflow: Decimal
    total_outflow: Decimal
    net_cash_flow: Decimal
    inflow_outflow_ratio: float

    average_daily_inflow: float
    average_daily_outflow: float

    minimum_balance: Decimal | None
    ending_balance: Decimal | None
    balance_trend: str

    monthly_burn_rate: float
    runway_days: float

    top_inflow_counterparty_ratio: float
    top_outflow_counterparty_ratio: float

    debt_outflow: Decimal
    debt_service_burden: float

    transaction_count: int
    data_days: int
    confidence: str


def calculate_features(
    transactions: list[CanonicalTransaction],
) -> LedgerFeatures:

    if not transactions:
        return LedgerFeatures(
            total_inflow=Decimal("0"),
            total_outflow=Decimal("0"),
            net_cash_flow=Decimal("0"),
            inflow_outflow_ratio=0.0,
            average_daily_inflow=0.0,
            average_daily_outflow=0.0,
            minimum_balance=None,
            ending_balance=None,
            balance_trend="INSUFFICIENT_DATA",
            monthly_burn_rate=0.0,
            runway_days=0.0,
            top_inflow_counterparty_ratio=0.0,
            top_outflow_counterparty_ratio=0.0,
            debt_outflow=Decimal("0"),
            debt_service_burden=0.0,
            transaction_count=0,
            data_days=0,
            confidence="LOW",
        )

    total_inflow = sum(
        (txn.amount for txn in transactions if txn.direction == "in"),
        Decimal("0"),
    )

    total_outflow = sum(
        (txn.amount for txn in transactions if txn.direction == "out"),
        Decimal("0"),
    )

    net_cash_flow = total_inflow - total_outflow

    ratio = (
        float(total_inflow / total_outflow)
        if total_outflow > 0
        else float("inf") if total_inflow > 0 else 0.0
    )

    dates = {txn.date for txn in transactions}
    data_days = max((max(dates) - min(dates)).days + 1, 1)

    average_daily_inflow = float(total_inflow) / data_days
    average_daily_outflow = float(total_outflow) / data_days

    # Balance metrics
    balances = [
        txn.balance_computed
        for txn in transactions
        if txn.balance_computed is not None
    ]

    minimum_balance = min(balances) if balances else None
    ending_balance = balances[-1] if balances else None

    # Simple balance trend
    if len(balances) < 2:
        balance_trend = "INSUFFICIENT_DATA"
    elif balances[-1] > balances[0]:
        balance_trend = "IMPROVING"
    elif balances[-1] < balances[0]:
        balance_trend = "DETERIORATING"
    else:
        balance_trend = "STABLE"

    # Monthly burn rate based on historical average daily outflow
    monthly_burn_rate = average_daily_outflow * 30

    # Runway
    if ending_balance is None:
        runway_days = 0.0
    elif average_daily_outflow == 0:
        runway_days = float("inf")
    else:
        runway_days = float(ending_balance) / average_daily_outflow

    # Counterparty concentration
    inflows_by_counterparty = {}
    outflows_by_counterparty = {}

    for txn in transactions:
        name = txn.counterparty or "Unknown"

        if txn.direction == "in":
            inflows_by_counterparty[name] = (
                inflows_by_counterparty.get(name, Decimal("0"))
                + txn.amount
            )
        else:
            outflows_by_counterparty[name] = (
                outflows_by_counterparty.get(name, Decimal("0"))
                + txn.amount
            )

    top_inflow_counterparty_ratio = (
        float(max(inflows_by_counterparty.values()) / total_inflow)
        if inflows_by_counterparty and total_inflow > 0
        else 0.0
    )

    top_outflow_counterparty_ratio = (
        float(max(outflows_by_counterparty.values()) / total_outflow)
        if outflows_by_counterparty and total_outflow > 0
        else 0.0
    )

    # Debt-related transactions
    debt_keywords = (
        "loan",
        "emi",
        "debt",
        "interest",
        "repayment",
        "credit card",
    )

    debt_outflow = sum(
        (
            txn.amount
            for txn in transactions
            if txn.direction == "out"
            and any(
                keyword in (txn.description or "").lower()
                for keyword in debt_keywords
            )
        ),
        Decimal("0"),
    )

    debt_service_burden = (
        float(debt_outflow / total_inflow)
        if total_inflow > 0
        else 0.0
    )

    # Data confidence
    if data_days >= 30 and len(transactions) >= 30:
        confidence = "HIGH"
    elif data_days >= 14 and len(transactions) >= 15:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return LedgerFeatures(
        total_inflow=total_inflow,
        total_outflow=total_outflow,
        net_cash_flow=net_cash_flow,
        inflow_outflow_ratio=ratio,
        average_daily_inflow=average_daily_inflow,
        average_daily_outflow=average_daily_outflow,
        minimum_balance=minimum_balance,
        ending_balance=ending_balance,
        balance_trend=balance_trend,
        monthly_burn_rate=monthly_burn_rate,
        runway_days=runway_days,
        top_inflow_counterparty_ratio=top_inflow_counterparty_ratio,
        top_outflow_counterparty_ratio=top_outflow_counterparty_ratio,
        debt_outflow=debt_outflow,
        debt_service_burden=debt_service_burden,
        transaction_count=len(transactions),
        data_days=data_days,
        confidence=confidence,
    )