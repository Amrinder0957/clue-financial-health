from __future__ import annotations

import csv
from io import StringIO

from app.domain.exceptions import PipelineError
from app.infrastructure.pipeline_types import IngestResult

MAX_CSV_BYTES = 5 * 1024 * 1024
XLSX_MAGIC = b"PK\x03\x04"
XLS_MAGIC = b"\xd0\xcf\x11\xe0"
ENCODINGS = ("utf-8-sig", "utf-8", "latin-1")


def ingest_csv(content: bytes, filename: str | None = None) -> IngestResult:
    _reject_spreadsheet(content, filename)
    if len(content) > MAX_CSV_BYTES:
        raise PipelineError("CSV exceeds the maximum size of 5 MB.")
    if not content.strip():
        raise PipelineError("CSV file is empty or unreadable.")

    text, encoding = _decode(content)
    if "\x00" in text:
        raise PipelineError("CSV file is unreadable.")

    reader = csv.reader(StringIO(text))
    raw_rows = list(reader)
    if not raw_rows:
        raise PipelineError("CSV has zero columns.")

    headers = [cell.strip() for cell in raw_rows[0]]
    if not any(headers):
        raise PipelineError("CSV has zero columns.")

    data_rows: list[list[str]] = []
    source_rows: list[int] = []
    width = len(raw_rows[0])
    for offset, row in enumerate(raw_rows[1:], start=2):
        if _is_blank_row(row):
            continue
        padded = list(row) + [""] * max(0, width - len(row))
        data_rows.append(padded[:width])
        source_rows.append(offset)

    if not data_rows:
        raise PipelineError("CSV has zero usable rows.")

    return IngestResult(
        headers=headers,
        rows=data_rows,
        encoding=encoding,
        source_rows=source_rows,
    )


def _reject_spreadsheet(content: bytes, filename: str | None) -> None:
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xls", ".xlsm", ".ods")):
        raise PipelineError("Only CSV files are accepted.")
    if content.startswith(XLSX_MAGIC) or content.startswith(XLS_MAGIC):
        raise PipelineError("Disguised spreadsheet files are not accepted.")


def _decode(content: bytes) -> tuple[str, str]:
    last_error: Exception | None = None
    for encoding in ENCODINGS:
        try:
            return content.decode(encoding), encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    raise PipelineError(f"CSV file is unreadable: {last_error}")


def _is_blank_row(row: list[str]) -> bool:
    return all(not str(cell).strip() for cell in row)
