from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.domain.ledger import QualityWarning, QuarantinedRow


@dataclass
class IngestResult:
    headers: list[str]
    rows: list[list[str]]
    encoding: str
    source_rows: list[int]


@dataclass
class ColumnMapping:
    canonical_to_header: dict[str, str | None]
    canonical_to_index: dict[str, int | None]
    warnings: list[QualityWarning] = field(default_factory=list)


@dataclass
class MappedRow:
    source_row: int
    values: dict[str, str]


@dataclass
class ParsedRow:
    source_row: int
    date: date
    amount: Decimal
    direction: str
    signed_amount: Decimal
    description: str
    counterparty: str
    account: str
    category: str
    txn_id: str
    balance_reported: Decimal | None
    raw: dict[str, str]
    warnings: list[QualityWarning] = field(default_factory=list)


@dataclass
class ValidationResult:
    parsed: list[ParsedRow]
    quarantined: list[QuarantinedRow]
