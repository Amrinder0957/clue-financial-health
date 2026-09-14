from datetime import date
from decimal import Decimal

import pytest

from app.application.pipeline import run_data_pipeline
from app.domain.exceptions import PipelineError
from app.infrastructure.normalization import parse_amount, parse_date


def pipeline(csv_text: str, filename: str = "ledger.csv") -> object:
    return run_data_pipeline(csv_text.encode("utf-8"), filename)


def test_normal_csv() -> None:
    ledger = pipeline(
        """date,amount,direction,description,counterparty,category,account,txn_id
2024-01-15,1000,in,Sale,Acme,sales,HDFC,txn-1
2024-01-16,250,out,Rent,Landlord,rent,HDFC,txn-2
"""
    )
    assert len(ledger.transactions) == 2
    first, second = ledger.transactions
    assert first.date == date(2024, 1, 15)
    assert first.amount == Decimal("1000")
    assert first.direction == "in"
    assert first.signed_amount == Decimal("1000")
    assert first.source_row == 2
    assert second.direction == "out"
    assert second.signed_amount == Decimal("-250")
    assert second.source_row == 3
    assert ledger.quality.usable_rows == 2
    assert ledger.quality.quarantined_rows == 0
    assert ledger.quality.data_confidence == "low"


def test_messy_column_names() -> None:
    ledger = pipeline(
        """ Transaction Date ,AMT, Narration ,Payee, Type
15/01/2024,500,Office supplies,  Stationery Mart  ,OUT
"""
    )
    txn = ledger.transactions[0]
    assert ledger.column_mapping["date"] == "Transaction Date"
    assert ledger.column_mapping["amount"] == "AMT"
    assert txn.description == "Office supplies"
    assert txn.counterparty == "stationery mart"
    assert txn.direction == "out"


def test_rupee_and_comma_formatted_amounts() -> None:
    ledger = pipeline(
        """date,amount,direction
2024-03-01,"₹ 1,23,456.78",in
2024-03-02,"Rs. 2,000",out
2024-03-03,"INR 50.25",in
2024-03-04,"(1,000.00)",out
"""
    )
    amounts = [txn.amount for txn in ledger.transactions]
    assert amounts == [
        Decimal("123456.78"),
        Decimal("2000"),
        Decimal("50.25"),
        Decimal("1000.00"),
    ]
    assert ledger.transactions[3].signed_amount == Decimal("-1000.00")


def test_in_out_normalization() -> None:
    ledger = pipeline(
        """date,amount,direction
2024-01-01,10,IN
2024-01-02,10,OUT
2024-01-03,10,credit
2024-01-04,10,debit
"""
    )
    assert [txn.direction for txn in ledger.transactions] == ["in", "out", "in", "out"]
    assert [txn.signed_amount for txn in ledger.transactions] == [
        Decimal("10"),
        Decimal("-10"),
        Decimal("10"),
        Decimal("-10"),
    ]


def test_debit_credit_input() -> None:
    ledger = pipeline(
        """date,debit,credit,description
2024-02-01,400,
2024-02-02,,900
"""
    )
    assert ledger.transactions[0].direction == "out"
    assert ledger.transactions[0].amount == Decimal("400")
    assert ledger.transactions[1].direction == "in"
    assert ledger.transactions[1].amount == Decimal("900")


def test_invalid_dates_are_quarantined() -> None:
    ledger = pipeline(
        """date,amount,direction
2024-01-10,10,in
13/13/2024,10,in
not-a-date,10,in
"""
    )
    assert len(ledger.transactions) == 1
    assert len(ledger.quarantined) == 2
    assert all("date" in row.reason for row in ledger.quarantined)


def test_invalid_amounts_are_quarantined() -> None:
    ledger = pipeline(
        """date,amount,direction
2024-01-10,10,in
2024-01-11,12.34.56,in
2024-01-12,10%,in
2024-01-13,abc,in
"""
    )
    assert len(ledger.transactions) == 1
    assert len(ledger.quarantined) == 3
    assert all("amount" in row.reason for row in ledger.quarantined)


def test_missing_optional_columns() -> None:
    ledger = pipeline(
        """date,amount,direction
2024-01-01,25,in
"""
    )
    txn = ledger.transactions[0]
    assert txn.description == ""
    assert txn.counterparty == ""
    assert txn.category == ""
    assert txn.account == ""
    assert txn.txn_id == "row-2"
    codes = {item.code for item in ledger.quality.warnings}
    assert "MISSING_OPTIONAL_FIELD" in codes


def test_duplicate_rows_are_kept_and_marked() -> None:
    ledger = pipeline(
        """date,amount,direction,description,counterparty
2024-01-01,50,out,Fee,Bank
2024-01-01,50,out,Fee,Bank
"""
    )
    assert len(ledger.transactions) == 2
    assert ledger.transactions[0].is_duplicate is False
    assert ledger.transactions[1].is_duplicate is True
    assert ledger.quality.duplicate_count == 1


def test_zero_amounts_are_preserved() -> None:
    ledger = pipeline(
        """date,amount,direction
2024-01-01,0,out
"""
    )
    assert len(ledger.transactions) == 1
    assert ledger.transactions[0].amount == Decimal("0")
    assert ledger.transactions[0].signed_amount == Decimal("0")


def test_extreme_amounts_are_preserved() -> None:
    ledger = pipeline(
        """date,amount,direction
2024-01-01,999999999999.99,in
"""
    )
    assert ledger.transactions[0].amount == Decimal("999999999999.99")
    assert ledger.quality.quarantined_rows == 0


def test_running_balance_reported_and_computed() -> None:
    ledger = pipeline(
        """date,amount,direction,running_balance
2024-01-03,30,in,130
2024-01-01,100,in,100
2024-01-02,20,out,80
"""
    )
    by_row = {txn.source_row: txn for txn in ledger.transactions}
    assert by_row[3].balance_reported == Decimal("100")
    assert by_row[4].balance_reported == Decimal("80")
    assert by_row[2].balance_reported == Decimal("130")
    assert by_row[3].balance_computed == Decimal("100")
    assert by_row[4].balance_computed == Decimal("80")
    assert by_row[2].balance_computed == Decimal("110")
    codes = {item.code for item in ledger.quality.warnings}
    assert "OPENING_BALANCE_ASSUMED_ZERO" in codes


def test_missing_running_balance_still_computes_from_zero() -> None:
    ledger = pipeline(
        """date,amount,direction
2024-01-01,40,in
2024-01-02,15,out
"""
    )
    assert ledger.transactions[0].balance_reported is None
    assert ledger.transactions[0].balance_computed == Decimal("40")
    assert ledger.transactions[1].balance_computed == Decimal("25")
    assert any(item.code == "OPENING_BALANCE_ASSUMED_ZERO" for item in ledger.quality.warnings)


def test_empty_csv_hard_fails() -> None:
    with pytest.raises(PipelineError, match="empty|unreadable|zero"):
        pipeline("")


def test_header_only_csv_hard_fails() -> None:
    with pytest.raises(PipelineError, match="zero usable rows"):
        pipeline("date,amount,direction\n")


def test_missing_required_columns_hard_fail() -> None:
    with pytest.raises(PipelineError, match="Required columns"):
        pipeline("description,counterparty\nhello,world\n")


def test_all_invalid_rows_hard_fail() -> None:
    with pytest.raises(PipelineError, match="zero usable rows"):
        pipeline("date,amount,direction\nbad,nope,in\n")


def test_disguised_xlsx_is_rejected() -> None:
    with pytest.raises(PipelineError, match="spreadsheet|CSV"):
        run_data_pipeline(b"PK\x03\x04" + b"0" * 20, "transactions.csv")


def test_indian_ambiguous_date_prefers_dmy() -> None:
    ledger = pipeline(
        """date,amount,direction
01/02/2024,10,in
"""
    )
    assert ledger.transactions[0].date == date(2024, 2, 1)


def test_sign_conflict_keeps_row_and_warns() -> None:
    ledger = pipeline(
        """date,amount,direction
2024-01-01,-80,in
"""
    )
    assert len(ledger.transactions) == 1
    assert ledger.transactions[0].direction == "in"
    assert ledger.transactions[0].signed_amount == Decimal("80")
    assert any(item.code == "SIGN_OVERRIDE" for item in ledger.quality.warnings)


def test_both_debit_and_credit_populated_is_quarantined() -> None:
    ledger = pipeline(
        """date,debit,credit
2024-01-01,10,20
2024-01-02,15,
"""
    )
    assert len(ledger.transactions) == 1
    assert len(ledger.quarantined) == 1
    assert "debit and credit" in ledger.quarantined[0].reason


def test_category_synonyms_are_normalized() -> None:
    ledger = pipeline(
        """date,amount,direction,category
2024-01-01,10,out,Dining
"""
    )
    assert ledger.transactions[0].category == "food"


def test_parse_amount_helpers() -> None:
    assert parse_amount("₹ 1,234.50") == Decimal("1234.50")
    assert parse_amount("(200)") == Decimal("-200")
    assert parse_amount("10%") is None
    assert parse_amount("12.34.56") is None


def test_parse_date_helpers() -> None:
    assert parse_date("2024-03-09") == date(2024, 3, 9)
    assert parse_date("09/03/2024") == date(2024, 3, 9)
    assert parse_date("not-a-date") is None
