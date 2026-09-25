"""Profile a raw export before anyone writes a mapping for it.

Most mapping problems are visible in the export itself: a date column that could be read two ways, a
money column with no negative amounts because credits were filtered out, subtotal lines, codes that
Excel has turned into scientific notation, a column of full tax IDs that should never have left the
accounting system. ``profile`` finds these in seconds, before they become reconciliation differences.
"""

from __future__ import annotations

import csv
import datetime as dt
import re
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from . import values

CHECKS = {
    "P01": ("warning", "The file is not UTF-8; it was read as Windows-1252. Confirm accented names came through"),
    "P02": ("error", "Two columns have the same header"),
    "P03": ("error", "Rows have different numbers of columns: an unquoted comma or a broken line"),
    "P04": ("warning", "Whole rows are duplicated"),
    "P05": ("info", "Rows look like subtotals or totals: skip them in the mapping"),
    "P06": ("info", "Values have leading or trailing spaces"),
    "P07": ("warning", "A date column can be read both month-first and day-first: the mapping must say which"),
    "P08": ("warning", "A money column has values that do not parse as amounts"),
    "P09": ("info", "A column is entirely blank"),
    "P10": ("error", "A column appears to hold full tax IDs or social security numbers"),
    "P11": ("warning", "A money column has no negative amounts: check whether credits were filtered out"),
    "P12": ("warning", "Values look damaged by a spreadsheet: scientific notation or formula errors"),
    "P13": ("warning", "Codes in a column have inconsistent lengths or lost leading zeros"),
    "P14": ("warning", "Names in a name column look like the same business written differently"),
}

_SLASH_DATE = re.compile(r"^\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}$")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")
_MONEY = re.compile(r"^\(?-?[$£€]?\s?-?[\d,]*\.?\d+\)?-?$")
_TOTAL = re.compile(r"\b(sub)?totals?\b|\bgrand total\b", re.IGNORECASE)
_TAX_ID = re.compile(r"^(\d{2}-\d{7}|\d{3}-\d{2}-\d{4})$")
_SCIENTIFIC = re.compile(r"^-?\d+(\.\d+)?E[+-]?\d+$", re.IGNORECASE)
_EXCEL_ERROR = {"#REF!", "#N/A", "#VALUE!", "#DIV/0!", "#NAME?", "#NUM!", "#NULL!"}
_CODE = re.compile(r"^[0-9][0-9.\-]*$")
_PLAIN_CENTS = re.compile(r"^-?\d+\.\d{2}$")
_LEADING_ZERO = re.compile(r"^0\d")


@dataclass
class Finding:
    check: str
    severity: str
    message: str
    column: str = ""


@dataclass
class ColumnProfile:
    name: str
    filled: int = 0
    blank: int = 0
    distinct: int = 0
    kind: str = "text"
    detail: str = ""
    top: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class Profile:
    path: Path
    encoding: str
    rows: int = 0
    columns: list[ColumnProfile] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]


def _add(profile: Profile, check: str, message: str, column: str = "") -> None:
    profile.findings.append(Finding(check, CHECKS[check][0], message, column))


def _read(path: Path, encoding: str | None) -> tuple[str, str]:
    data = path.read_bytes()
    if encoding:
        return data.decode(encoding), encoding
    try:
        return data.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace"), "cp1252"


def _date_formats(samples: list[str]) -> list[str]:
    """Which of month-first and day-first can read every value in the column."""
    candidates = []
    for label, fmts in (("month-first", ("%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m.%d.%Y")), ("day-first", ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d.%m.%Y"))):
        ok = True
        for value in samples:
            if not any(_parses(value, f) for f in fmts):
                ok = False
                break
        if ok:
            candidates.append(label)
    return candidates


def _parses(value: str, fmt: str) -> bool:
    try:
        dt.datetime.strptime(value, fmt)
        return True
    except ValueError:
        return False


def profile_file(path, delimiter: str = ",", encoding: str | None = None) -> Profile:
    path = Path(path)
    text, used = _read(path, encoding)
    result = Profile(path, used)
    if used == "cp1252":
        _add(result, "P01", "decoded as Windows-1252; pass the right encoding to the mapping if names look wrong")

    rows = list(csv.reader(text.splitlines(), delimiter=delimiter))
    if not rows:
        return result
    header, body = rows[0], [r for r in rows[1:] if any(c.strip() for c in r)]
    result.rows = len(body)

    dupes = [h for h, n in Counter(header).items() if n > 1]
    if dupes:
        _add(result, "P02", f"duplicated header(s): {', '.join(dupes)}")
    widths = Counter(len(r) for r in body)
    wrong = sum(n for w, n in widths.items() if w != len(header))
    if wrong:
        _add(result, "P03", f"{wrong} row(s) do not have {len(header)} columns")

    whole = Counter(tuple(r) for r in body)
    repeated = sum(n - 1 for n in whole.values() if n > 1)
    if repeated:
        _add(result, "P04", f"{repeated} row(s) are exact copies of another row")

    totals = [i for i, r in enumerate(body, start=2) if any(_TOTAL.search(c) for c in r)]
    if totals:
        _add(result, "P05", f"{len(totals)} row(s) look like subtotals or totals (first on line {totals[0]}); add a skip_if rule")

    padded = set()
    for index, name in enumerate(header):
        cells = [r[index] if index < len(r) else "" for r in body]
        data_cells = [c for i, c in enumerate(cells, start=2) if i not in set(totals)]
        filled = [c.strip() for c in data_cells if c.strip()]
        col = ColumnProfile(name, len(filled), len(data_cells) - len(filled), len(set(filled)))
        col.top = Counter(filled).most_common(3)
        result.columns.append(col)
        if any(c != c.strip() and c.strip() for c in data_cells):
            padded.add(name)
        if not filled:
            col.kind = "blank"
            _add(result, "P09", "no values in any row", name)
            continue

        damaged = [c for c in filled if c in _EXCEL_ERROR or _SCIENTIFIC.match(c)]
        if damaged:
            _add(result, "P12", f"{len(damaged)} value(s) such as {damaged[0]!r}: re-export from the source system, not from a spreadsheet", name)
            filled = [c for c in filled if c not in damaged]
            if not filled:
                continue

        if "name" in name.lower():
            groups: dict[str, set[str]] = {}
            for c in filled:
                groups.setdefault(values.name_key(c), set()).add(c)
            similar = [sorted(v) for k, v in groups.items() if k and len(v) > 1]
            if similar:
                _add(result, "P14", f"{len(similar)} group(s), e.g. {' / '.join(repr(x) for x in similar[0])}: merge before mapping", name)

        tax = [c for c in filled if _TAX_ID.match(c)]
        if len(tax) >= max(1, len(filled) // 2):
            col.kind = "sensitive"
            _add(result, "P10", "looks like full tax IDs: drop this column at export, keep the last four digits at most", name)
            continue

        if all(_ISO_DATE.match(c) for c in filled):
            col.kind, col.detail = "date", "ISO (YYYY-MM-DD)"
            continue
        if all(_SLASH_DATE.match(c) for c in filled):
            formats = _date_formats(filled)
            col.kind = "date"
            if len(formats) == 2:
                col.detail = "ambiguous"
                _add(result, "P07", "every value has day and month of 12 or less; confirm the format from the source system's settings", name)
            elif formats:
                col.detail = formats[0]
            else:
                col.detail = "unparseable"
                _add(result, "P08", "looks like dates but not all values parse", name)
            continue

        money_like = [c for c in filled if _MONEY.match(c.replace(" ", ""))]
        marked = any(("$" in c or "(" in c or "," in c or c.endswith("-")) for c in filled)
        plain_cents = all(_PLAIN_CENTS.match(c) for c in filled) and not any(_LEADING_ZERO.match(c) for c in filled)
        if (marked or plain_cents) and len(money_like) >= 0.9 * len(filled):
            col.kind = "money"
            bad, negatives, total = [], 0, Decimal("0.00")
            for c in filled:
                try:
                    v = values.parse_money(c)
                except ValueError:
                    bad.append(c)
                    continue
                if v is not None:
                    total += v
                    negatives += v < 0
            col.detail = f"total {total:,.2f}, {negatives} negative"
            if bad:
                _add(result, "P08", f"{len(bad)} value(s) do not parse, such as {bad[0]!r}", name)
            if not negatives and len(filled) >= 20:
                _add(result, "P11", f"{len(filled)} amounts and not one negative", name)
            continue

        if all(_CODE.match(c) for c in filled) and col.distinct > 1:
            lengths = Counter(len(c) for c in filled)
            col.kind = "code"
            if len(lengths) > 1 and any(c.startswith("0") for c in filled):
                shortest = min(lengths)
                sample = next(c for c in filled if len(c) == shortest)
                _add(result, "P13", f"code lengths vary ({', '.join(map(str, sorted(lengths)))}), e.g. {sample!r}: leading zeros may have been dropped", name)

    if padded:
        _add(result, "P06", f"column(s) {', '.join(sorted(padded))}; the mapper strips them, but lookups built elsewhere may not")
    return result


def text_report(p: Profile) -> str:
    out = [f"{p.path.name}: {p.rows} data rows, {len(p.columns)} columns, {p.encoding}", ""]
    width = max((len(c.name) for c in p.columns), default=6)
    out.append(f"  {'column':<{width}}  {'filled':>7} {'blank':>6} {'distinct':>8}  kind       detail / most common")
    for c in p.columns:
        common = ", ".join(f"{v!r}×{n}" for v, n in c.top) if c.kind in ("text", "code") else ""
        detail = c.detail or common
        if c.kind == "sensitive":
            detail = "(values withheld)"
        out.append(f"  {c.name:<{width}}  {c.filled:>7} {c.blank:>6} {c.distinct:>8}  {c.kind:<10} {detail}")
    out.append("")
    order = {"error": 0, "warning": 1, "info": 2}
    for f in sorted(p.findings, key=lambda f: (order[f.severity], f.check)):
        col = f"[{f.column}] " if f.column else ""
        out.append(f"{f.severity.upper():<7} {f.check} {col}{f.message}")
    out.append("")
    out.append(f"{'FAIL' if p.errors else 'OK'}: {len(p.errors)} errors, {sum(f.severity == 'warning' for f in p.findings)} warnings")
    return "\n".join(out) + "\n"
