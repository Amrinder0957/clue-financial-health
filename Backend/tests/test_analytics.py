from decimal import Decimal
from datetime import date

from app.domain.analytics.engine import calculate_features
from app.domain.ledger import CanonicalTransaction


def make_txn(amount, direction, day):
    return CanonicalTransaction(
        txn_id=f"txn-{day}",
        date=date(2024, 1, day),
        amount=Decimal(str(amount)),
        direction=direction,
        signed_amount=(
            Decimal(str(amount))
            if direction == "in"
            else -Decimal(str(amount))
        ),
        description="test",
        counterparty="test",
        account="test",
        category="test",
        source_row=day + 1,
        balance_reported=None,
        balance_computed=Decimal("100000"),
        is_duplicate=False,
    )


def test_basic_financial_metrics():
    transactions = [
        make_txn(50000, "in", 1),
        make_txn(40000, "out", 2),
    ]

    result = calculate_features(transactions)

    assert result.total_inflow == Decimal("50000")
    assert result.total_outflow == Decimal("40000")
    assert result.net_cash_flow == Decimal("10000")
    assert result.inflow_outflow_ratio == 1.25

def test_runway_and_debt_metrics():
    transactions = [
        make_txn(100000, "in", 1),
        make_txn(10000, "out", 2),
        make_txn(20000, "out", 3),
    ]

    result = calculate_features(transactions)

    assert result.total_inflow == Decimal("100000")
    assert result.total_outflow == Decimal("30000")
    assert result.net_cash_flow == Decimal("70000")
    assert result.runway_days > 0
    assert result.debt_service_burden == 0.0


def test_counterparty_concentration():
    transactions = [
        make_txn(80000, "in", 1),
        make_txn(20000, "in", 2),
        make_txn(10000, "out", 3),
    ]

    # Change counterparties for this test
    transactions[0] = transactions[0].__class__(
        **{**transactions[0].__dict__, "counterparty": "Major Client"}
    )
    transactions[1] = transactions[1].__class__(
        **{**transactions[1].__dict__, "counterparty": "Other Client"}
    )

    result = calculate_features(transactions)

    assert result.top_inflow_counterparty_ratio == 0.8


def test_low_confidence_for_small_dataset():
    transactions = [
        make_txn(1000, "in", 1),
        make_txn(500, "out", 2),
    ]

    result = calculate_features(transactions)

    assert result.confidence == "LOW"   