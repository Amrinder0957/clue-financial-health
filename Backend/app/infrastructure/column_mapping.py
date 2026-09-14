from __future__ import annotations

import re

from app.domain.exceptions import PipelineError
from app.domain.ledger import QualityWarning
from app.infrastructure.pipeline_types import ColumnMapping, IngestResult, MappedRow

CANONICAL_FIELDS = (
    "date",
    "amount",
    "debit",
    "credit",
    "direction",
    "description",
    "counterparty",
    "category",
    "account",
    "txn_id",
    "balance",
)

ALIASES: dict[str, frozenset[str]] = {
    "date": frozenset(
        {
            "date",
            "txn_date",
            "transaction_date",
            "posting_date",
            "value_date",
            "trans_date",
            "tran_date",
            "txn_dt",
        }
    ),
    "amount": frozenset(
        {
            "amount",
            "amt",
            "transaction_amount",
            "txn_amount",
            "value",
            "transaction_amt",
        }
    ),
    "debit": frozenset(
        {
            "debit",
            "dr",
            "withdrawal",
            "withdrawals",
            "money_out",
            "withdraw",
            "debit_amount",
        }
    ),
    "credit": frozenset(
        {
            "credit",
            "cr",
            "deposit",
            "deposits",
            "money_in",
            "credit_amount",
        }
    ),
    "direction": frozenset(
        {
            "direction",
            "type",
            "txn_type",
            "transaction_type",
            "dr_cr",
            "flow",
            "in_out",
        }
    ),
    "description": frozenset(
        {
            "description",
            "desc",
            "particulars",
            "narration",
            "details",
            "memo",
            "remarks",
            "narrative",
        }
    ),
    "counterparty": frozenset(
        {
            "counterparty",
            "payee",
            "payer",
            "merchant",
            "vendor",
            "beneficiary",
            "party",
            "name",
        }
    ),
    "category": frozenset(
        {
            "category",
            "cat",
            "classification",
            "expense_category",
        }
    ),
    "account": frozenset(
        {
            "account",
            "account_name",
            "account_no",
            "account_number",
            "acc",
            "bank_account",
        }
    ),
    "txn_id": frozenset(
        {
            "txn_id",
            "transaction_id",
            "id",
            "trans_id",
            "reference",
            "ref",
            "ref_no",
            "utr",
        }
    ),
    "balance": frozenset(
        {
            "balance",
            "running_balance",
            "running_bal",
            "closing_balance",
            "balance_after",
            "available_balance",
        }
    ),
}

OPTIONAL_FIELDS = (
    "direction",
    "description",
    "counterparty",
    "category",
    "account",
    "txn_id",
    "balance",
)


def normalize_header(header: str) -> str:
    text = header.strip().lower().replace("-", " ").replace("/", " ")
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", "_", text).strip("_")


def map_columns(ingest: IngestResult) -> tuple[ColumnMapping, list[MappedRow]]:
    warnings: list[QualityWarning] = []
    normalized = [normalize_header(h) for h in ingest.headers]

    for index, header in enumerate(ingest.headers):
        if not header.strip():
            warnings.append(
                QualityWarning(
                    code="BLANK_COLUMN",
                    message=f"Column {index + 1} has a blank header.",
                )
            )

    seen: dict[str, int] = {}
    for header in normalized:
        if not header:
            continue
        if header in seen:
            warnings.append(
                QualityWarning(
                    code="DUPLICATE_HEADER",
                    message=f"Duplicate header '{header}' was found.",
                )
            )
        seen[header] = seen.get(header, 0) + 1

    canonical_to_index: dict[str, int | None] = {field: None for field in CANONICAL_FIELDS}
    canonical_to_header: dict[str, str | None] = {field: None for field in CANONICAL_FIELDS}

    used_indexes: set[int] = set()
    for field in CANONICAL_FIELDS:
        for index, header in enumerate(normalized):
            if index in used_indexes or not header:
                continue
            if header in ALIASES[field]:
                canonical_to_index[field] = index
                canonical_to_header[field] = ingest.headers[index]
                used_indexes.add(index)
                break

    has_date = canonical_to_index["date"] is not None
    has_amount = canonical_to_index["amount"] is not None
    has_debit_credit = (
        canonical_to_index["debit"] is not None and canonical_to_index["credit"] is not None
    )
    if not has_date or not (has_amount or has_debit_credit):
        raise PipelineError(
            "Required columns are missing. Provide date and amount, or date with debit and credit."
        )

    for field in OPTIONAL_FIELDS:
        if canonical_to_index[field] is None:
            warnings.append(
                QualityWarning(
                    code="MISSING_OPTIONAL_FIELD",
                    message=f"Optional field '{field}' is not present in the CSV.",
                )
            )

    mapping = ColumnMapping(
        canonical_to_header=canonical_to_header,
        canonical_to_index=canonical_to_index,
        warnings=warnings,
    )
    mapped_rows = [
        MappedRow(source_row=source_row, values=_row_values(row, mapping))
        for source_row, row in zip(ingest.source_rows, ingest.rows, strict=True)
    ]
    return mapping, mapped_rows


def _row_values(row: list[str], mapping: ColumnMapping) -> dict[str, str]:
    values: dict[str, str] = {}
    for field, index in mapping.canonical_to_index.items():
        if index is None:
            continue
        raw = row[index] if index < len(row) else ""
        values[field] = "" if raw is None else str(raw).strip()
    return values
