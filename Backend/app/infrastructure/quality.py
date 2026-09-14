from __future__ import annotations

from app.domain.ledger import CanonicalTransaction, DataConfidence, QualitySummary, QualityWarning


def build_quality_summary(
    *,
    total_source_rows: int,
    transactions: list[CanonicalTransaction],
    quarantined_count: int,
    warnings: list[QualityWarning],
) -> QualitySummary:
    dates = [txn.date for txn in transactions]
    date_start = min(dates) if dates else None
    date_end = max(dates) if dates else None
    span_days = (date_end - date_start).days + 1 if date_start and date_end else 0
    usable = len(transactions)
    return QualitySummary(
        total_source_rows=total_source_rows,
        usable_rows=usable,
        quarantined_rows=quarantined_count,
        warning_count=len(warnings),
        duplicate_count=sum(1 for txn in transactions if txn.is_duplicate),
        date_start=date_start,
        date_end=date_end,
        span_days=span_days,
        data_confidence=_confidence(usable, span_days),
        warnings=warnings,
    )


def _confidence(usable_rows: int, span_days: int) -> DataConfidence:
    if span_days < 14 or usable_rows < 15:
        return "low"
    if span_days >= 30 and usable_rows >= 30:
        return "high"
    return "medium"
