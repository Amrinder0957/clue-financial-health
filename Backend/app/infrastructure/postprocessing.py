from __future__ import annotations

from decimal import Decimal

import pandas as pd

from app.domain.ledger import CanonicalTransaction, QualityWarning
from app.infrastructure.normalization import (
    collapse_space,
    normalize_category,
    normalize_counterparty,
    warning,
)
from app.infrastructure.pipeline_types import ParsedRow


def postprocess(parsed: list[ParsedRow]) -> tuple[list[CanonicalTransaction], list[QualityWarning]]:
    warnings: list[QualityWarning] = [
        warning(
            "OPENING_BALANCE_ASSUMED_ZERO",
            "Computed balance starts from an opening balance of 0 because no opening balance was supplied. This is not the actual bank balance.",
        )
    ]

    prepared: list[ParsedRow] = []
    for row in parsed:
        row.description = collapse_space(row.description)
        row.counterparty = normalize_counterparty(row.counterparty)
        row.account = collapse_space(row.account)
        row.category = normalize_category(row.category)
        if not row.txn_id:
            row.txn_id = f"row-{row.source_row}"
        prepared.append(row)

    duplicate_flags = _mark_duplicates(prepared)
    computed_balances = _compute_balances(prepared)

    transactions: list[CanonicalTransaction] = []
    for row, is_duplicate in zip(prepared, duplicate_flags, strict=True):
        if is_duplicate:
            warnings.append(
                warning(
                    "DUPLICATE_TRANSACTION",
                    "Row matches an earlier transaction and was kept for anomaly review.",
                    row.source_row,
                )
            )
        transactions.append(
            CanonicalTransaction(
                txn_id=row.txn_id,
                date=row.date,
                amount=row.amount,
                direction=row.direction,  # type: ignore[arg-type]
                signed_amount=row.signed_amount,
                description=row.description,
                counterparty=row.counterparty,
                account=row.account,
                category=row.category,
                source_row=row.source_row,
                balance_reported=row.balance_reported,
                balance_computed=computed_balances[row.source_row],
                is_duplicate=is_duplicate,
            )
        )
        warnings.extend(row.warnings)

    return transactions, warnings


def _mark_duplicates(rows: list[ParsedRow]) -> list[bool]:
    seen: set[tuple] = set()
    flags: list[bool] = []
    for row in rows:
        key = (
            row.date,
            row.amount,
            row.direction,
            row.description,
            row.counterparty,
            row.account,
        )
        flags.append(key in seen)
        seen.add(key)
    return flags


def _compute_balances(rows: list[ParsedRow]) -> dict[int, Decimal]:
    if not rows:
        return {}
    frame = pd.DataFrame(
        {
            "source_row": [row.source_row for row in rows],
            "date": [row.date for row in rows],
            "signed_amount": [row.signed_amount for row in rows],
        }
    )
    frame = frame.sort_values(["date", "source_row"], kind="mergesort")
    running = Decimal("0")
    balances: dict[int, Decimal] = {}
    for source_row, signed in zip(frame["source_row"], frame["signed_amount"]):
        running += Decimal(str(signed))
        balances[int(source_row)] = running
    return balances
