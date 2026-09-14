from __future__ import annotations

from app.domain.exceptions import PipelineError
from app.domain.ledger import CleanLedger
from app.infrastructure.column_mapping import map_columns
from app.infrastructure.ingest import ingest_csv
from app.infrastructure.postprocessing import postprocess
from app.infrastructure.quality import build_quality_summary
from app.infrastructure.validation import validate_and_parse


def run_data_pipeline(content: bytes, filename: str | None = None) -> CleanLedger:
    ingested = ingest_csv(content, filename)
    mapping, mapped_rows = map_columns(ingested)
    validated = validate_and_parse(mapped_rows)
    if not validated.parsed:
        raise PipelineError("CSV has zero usable rows.")

    transactions, post_warnings = postprocess(validated.parsed)
    warnings = [*mapping.warnings, *post_warnings]
    quality = build_quality_summary(
        total_source_rows=len(ingested.rows),
        transactions=transactions,
        quarantined_count=len(validated.quarantined),
        warnings=warnings,
    )
    return CleanLedger(
        transactions=transactions,
        quarantined=validated.quarantined,
        quality=quality,
        column_mapping=mapping.canonical_to_header,
    )
