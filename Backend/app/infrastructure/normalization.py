from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd

from app.domain.ledger import QualityWarning

DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y.%m.%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%d/%m/%y",
    "%d-%m-%y",
    "%d.%m.%y",
    "%d %b %Y",
    "%d %B %Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
)

IN_TOKENS = frozenset(
    {"in", "inflow", "incoming", "credit", "cr", "deposit", "income", "received"}
)
OUT_TOKENS = frozenset(
    {"out", "outflow", "outgoing", "debit", "dr", "withdrawal", "expense", "payment", "paid"}
)

CURRENCY_PATTERN = re.compile(r"(₹|\$|\binr\b|rs\.?)", re.IGNORECASE)
LETTERS_PATTERN = re.compile(r"[a-zA-Z%]")

CATEGORY_SYNONYMS = {
    "food": "food",
    "dining": "food",
    "restaurant": "food",
    "restaurants": "food",
    "meals": "food",
    "groceries": "food",
    "grocery": "food",
    "rent": "rent",
    "rental": "rent",
    "salary": "salary",
    "wages": "salary",
    "payroll": "salary",
    "utilities": "utilities",
    "utility": "utilities",
    "electricity": "utilities",
    "water": "utilities",
    "internet": "utilities",
    "travel": "travel",
    "transport": "travel",
    "transportation": "travel",
    "fuel": "travel",
    "petrol": "travel",
    "diesel": "travel",
    "transfer": "transfer",
    "transfers": "transfer",
    "refund": "refund",
    "fee": "fees",
    "fees": "fees",
    "charge": "fees",
    "charges": "fees",
}


def parse_date(raw: str) -> date | None:
    text = (raw or "").strip()
    if not text:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    parsed = pd.to_datetime(text, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def parse_amount(raw: str) -> Decimal | None:
    text = (raw or "").strip()
    if not text:
        return None

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    text = CURRENCY_PATTERN.sub("", text)
    text = text.replace(" ", "").replace("\u00a0", "")
    text = text.replace(",", "")

    if text.startswith("+"):
        text = text[1:]
    elif text.startswith("-"):
        negative = True
        text = text[1:]

    if not text or LETTERS_PATTERN.search(text):
        return None
    if text.count(".") > 1 or text in {".", "-", "+"}:
        return None
    if not re.fullmatch(r"\d+(\.\d+)?", text):
        return None

    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    return -value if negative else value


def parse_direction_label(raw: str) -> str | None:
    token = re.sub(r"\s+", " ", (raw or "").strip().lower())
    token = token.replace("-", " ")
    compact = token.replace(" ", "_")
    if compact in IN_TOKENS or token in IN_TOKENS:
        return "in"
    if compact in OUT_TOKENS or token in OUT_TOKENS:
        return "out"
    return None


def is_populated_amount(raw: str) -> bool:
    parsed = parse_amount(raw)
    return parsed is not None and parsed != 0


def signed_amount_for(direction: str, amount: Decimal) -> Decimal:
    if direction == "in":
        return amount.copy_abs()
    return -amount.copy_abs()


def normalize_category(raw: str) -> str:
    text = collapse_space(raw).lower()
    if not text:
        return ""
    return CATEGORY_SYNONYMS.get(text, text)


def normalize_counterparty(raw: str) -> str:
    text = collapse_space(raw)
    if not text:
        return ""
    return text.casefold()


def collapse_space(raw: str) -> str:
    return re.sub(r"\s+", " ", (raw or "").strip())


def warning(code: str, message: str, source_row: int | None = None) -> QualityWarning:
    return QualityWarning(code=code, message=message, source_row=source_row)
