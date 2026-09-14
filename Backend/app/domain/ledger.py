from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

Direction = Literal["in", "out"]
DataConfidence = Literal["low", "medium", "high"]


class CanonicalTransaction(BaseModel):
    txn_id: str
    date: date
    amount: Decimal
    direction: Direction
    signed_amount: Decimal
    description: str = ""
    counterparty: str = ""
    account: str = ""
    category: str = ""
    source_row: int
    balance_reported: Decimal | None = None
    balance_computed: Decimal | None = None
    is_duplicate: bool = False


class QuarantinedRow(BaseModel):
    source_row: int
    reason: str
    raw: dict[str, str] = Field(default_factory=dict)


class QualityWarning(BaseModel):
    code: str
    message: str
    source_row: int | None = None


class QualitySummary(BaseModel):
    total_source_rows: int
    usable_rows: int
    quarantined_rows: int
    warning_count: int
    duplicate_count: int
    date_start: date | None = None
    date_end: date | None = None
    span_days: int = 0
    data_confidence: DataConfidence = "low"
    warnings: list[QualityWarning] = Field(default_factory=list)


class CleanLedger(BaseModel):
    """Canonical ledger produced by the data pipeline. Analytics must consume this, not raw CSV."""

    transactions: list[CanonicalTransaction]
    quarantined: list[QuarantinedRow]
    quality: QualitySummary
    column_mapping: dict[str, str | None] = Field(default_factory=dict)
