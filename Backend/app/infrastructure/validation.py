from __future__ import annotations

from decimal import Decimal

from app.domain.ledger import QuarantinedRow
from app.infrastructure.normalization import (
    is_populated_amount,
    parse_amount,
    parse_date,
    parse_direction_label,
    signed_amount_for,
    warning,
)
from app.infrastructure.pipeline_types import MappedRow, ParsedRow, ValidationResult


def validate_and_parse(rows: list[MappedRow]) -> ValidationResult:
    parsed: list[ParsedRow] = []
    quarantined: list[QuarantinedRow] = []

    for row in rows:
        result, quarantine = _parse_row(row)
        if quarantine is not None:
            quarantined.append(quarantine)
        elif result is not None:
            parsed.append(result)

    return ValidationResult(parsed=parsed, quarantined=quarantined)


def _parse_row(row: MappedRow) -> tuple[ParsedRow | None, QuarantinedRow | None]:
    raw = dict(row.values)
    txn_date = parse_date(row.values.get("date", ""))
    if txn_date is None:
        return None, _quarantine(row, "date cannot be parsed")

    amount, direction, row_warnings, amount_error = _resolve_amount_and_direction(row)
    if amount_error:
        return None, _quarantine(row, amount_error)

    assert amount is not None and direction is not None
    canonical_amount = amount.copy_abs()

    txn_id = row.values.get("txn_id", "").strip()
    balance_raw = row.values.get("balance", "")
    balance_reported = parse_amount(balance_raw) if balance_raw else None
    if balance_raw and balance_reported is None:
        row_warnings.append(
            warning(
                "INVALID_REPORTED_BALANCE",
                "Running balance could not be parsed and was ignored.",
                row.source_row,
            )
        )

    return (
        ParsedRow(
            source_row=row.source_row,
            date=txn_date,
            amount=canonical_amount,
            direction=direction,
            signed_amount=signed_amount_for(direction, canonical_amount),
            description=row.values.get("description", ""),
            counterparty=row.values.get("counterparty", ""),
            account=row.values.get("account", ""),
            category=row.values.get("category", ""),
            txn_id=txn_id,
            balance_reported=balance_reported,
            raw=raw,
            warnings=row_warnings,
        ),
        None,
    )


def _resolve_amount_and_direction(
    row: MappedRow,
) -> tuple[Decimal | None, str | None, list, str | None]:
    warnings = []
    has_debit = "debit" in row.values
    has_credit = "credit" in row.values
    debit_raw = row.values.get("debit", "")
    credit_raw = row.values.get("credit", "")
    amount_raw = row.values.get("amount", "")
    direction_raw = row.values.get("direction", "")

    debit_value = parse_amount(debit_raw) if debit_raw else None
    credit_value = parse_amount(credit_raw) if credit_raw else None
    if debit_raw and debit_value is None:
        return None, None, warnings, "amount cannot be parsed"
    if credit_raw and credit_value is None:
        return None, None, warnings, "amount cannot be parsed"

    debit_populated = has_debit and is_populated_amount(debit_raw)
    credit_populated = has_credit and is_populated_amount(credit_raw)

    sources: list[tuple[str, str, Decimal]] = []

    if has_debit and has_credit:
        if debit_populated and credit_populated:
            return None, None, warnings, "both debit and credit are incorrectly populated"
        if debit_populated:
            sources.append(("debit_credit", "out", debit_value.copy_abs()))  # type: ignore[union-attr]
        elif credit_populated:
            sources.append(("debit_credit", "in", credit_value.copy_abs()))  # type: ignore[union-attr]

    explicit_direction = parse_direction_label(direction_raw) if direction_raw else None
    if direction_raw and explicit_direction is None:
        return None, None, warnings, "required direction information is unavailable"

    signed_from_amount = parse_amount(amount_raw) if amount_raw else None
    if amount_raw and signed_from_amount is None:
        return None, None, warnings, "amount cannot be parsed"

    if explicit_direction:
        amount_for_direction = (
            signed_from_amount.copy_abs()
            if signed_from_amount is not None
            else (sources[0][2] if sources else None)
        )
        if amount_for_direction is None:
            return None, None, warnings, "amount cannot be parsed"
        sources.append(("explicit_direction", explicit_direction, amount_for_direction))

    if signed_from_amount is not None and signed_from_amount != 0:
        inferred = "in" if signed_from_amount > 0 else "out"
        sources.append(("signed_amount", inferred, signed_from_amount.copy_abs()))
    elif signed_from_amount == 0 and not sources:
        return None, None, warnings, "required direction information is unavailable"

    if not sources:
        return None, None, warnings, "required direction information is unavailable"

    unique_directions = {item[1] for item in sources}
    unique_amounts = {item[2] for item in sources}
    winner_source, direction, amount = sources[0]

    if len(unique_directions) > 1 or (signed_from_amount is not None and _sign_conflicts(signed_from_amount, direction)):
        warnings.append(
            warning(
                "SIGN_OVERRIDE",
                (
                    f"Direction from {winner_source} overrode a conflicting sign or direction label."
                ),
                row.source_row,
            )
        )

    if len(unique_amounts) > 1:
        warnings.append(
            warning(
                "AMOUNT_SOURCE_CONFLICT",
                "Multiple amount sources differed; the highest-priority source was used.",
                row.source_row,
            )
        )

    return amount, direction, warnings, None


def _sign_conflicts(signed_from_amount: Decimal, direction: str) -> bool:
    if signed_from_amount == 0:
        return False
    amount_direction = "in" if signed_from_amount > 0 else "out"
    return amount_direction != direction


def _quarantine(row: MappedRow, reason: str) -> QuarantinedRow:
    return QuarantinedRow(source_row=row.source_row, reason=reason, raw=dict(row.values))
