"""Parsing for the values that break migrations: money, dates, flags.

Every parser is strict on purpose. A migration that silently rounds a cent, or guesses whether
03/04/2026 is March or April, produces totals that nearly tie out -- which is worse than totals
that obviously do not.
"""

from __future__ import annotations

import datetime as dt
import re
from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")
_MONEY_JUNK = re.compile(r"[\s$£€,]")
_TRUE = {"yes", "y", "true", "t", "1"}
_FALSE = {"no", "n", "false", "f", "0"}


def parse_money(text: str) -> Decimal | None:
    """Parse an accounting-style amount to exact cents.

    Accepts ``1234.5``, ``$1,234.50``, ``(1,234.50)``, ``1,234.50-`` and ``-$1,234.50``.
    Refuses anything with more than two decimal places rather than rounding it: a sub-cent
    value in a money column usually means a unit price has landed in the wrong field.
    """
    raw = text.strip()
    if not raw:
        return None
    negative = False
    body = raw
    if body.startswith("(") and body.endswith(")"):
        negative, body = True, body[1:-1]
    if body.endswith("-"):
        negative, body = not negative, body[:-1]
    body = _MONEY_JUNK.sub("", body)
    if body.startswith("-"):
        negative, body = not negative, body[1:]
    if body.startswith("+"):
        body = body[1:]
    try:
        value = Decimal(body)
    except InvalidOperation:
        raise ValueError(f"not an amount: {raw!r}") from None
    if not value.is_finite():
        raise ValueError(f"not an amount: {raw!r}")
    if value != value.quantize(CENT):
        raise ValueError(f"more than two decimal places: {raw!r}")
    value = value.quantize(CENT)
    return -value if negative else value


def parse_decimal(text: str) -> Decimal | None:
    raw = text.strip().rstrip("%")
    if not raw:
        return None
    try:
        return Decimal(raw.replace(",", ""))
    except InvalidOperation:
        raise ValueError(f"not a number: {text!r}") from None


def parse_date(text: str, fmt: str = "%Y-%m-%d") -> dt.date | None:
    """Parse a date in exactly one format. There is no guessing between day-first and month-first."""
    raw = text.strip()
    if not raw:
        return None
    try:
        return dt.datetime.strptime(raw, fmt).date()
    except ValueError:
        raise ValueError(f"date {raw!r} does not match format {fmt}") from None


def parse_bool(text: str) -> bool | None:
    raw = text.strip().lower()
    if not raw:
        return None
    if raw in _TRUE:
        return True
    if raw in _FALSE:
        return False
    raise ValueError(f"not a yes/no value: {text!r}")


def parse_int(text: str) -> int | None:
    raw = text.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"not a whole number: {text!r}") from None


def format_money(value: Decimal) -> str:
    return f"{value:,.2f}"


_NAME_NOISE = re.compile(r"\b(inc|llc|ltd|limited|co|corp|corporation|company|the|and)\b|[^a-z0-9]")


def name_key(name: str) -> str:
    """Normalise a business name so 'Sample Drywall Co.' and 'SAMPLE DRYWALL, INC' compare equal."""
    return _NAME_NOISE.sub("", name.lower().replace("&", " and "))
