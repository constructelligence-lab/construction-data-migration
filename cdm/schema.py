"""The neutral schema, and reading migration files against it.

The schema lives in ``schema/fields.csv`` so that a controller can read it in Excel and a script
can read it in CI. Each record is one CSV file named after the record (``jobs.csv``,
``cost_transactions.csv`` ...), with a header row of field names.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from . import values

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "fields.csv"

RECORDS = [
    "jobs",
    "cost_codes",
    "budgets",
    "vendors",
    "commitments",
    "change_orders",
    "cost_transactions",
    "billings",
    "control_totals",
]


@dataclass(frozen=True)
class Field:
    record: str
    name: str
    type: str
    required: bool
    key: bool
    allowed: tuple[str, ...]
    description: str


@dataclass
class Issue:
    check: str
    severity: str  # error | warning | info
    message: str
    record: str = ""
    line: int = 0
    job_id: str = ""

    def where(self) -> str:
        if self.record and self.line:
            return f"{self.record}.csv line {self.line}"
        return self.record or ""


@dataclass
class Table:
    record: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    lines: list[int] = field(default_factory=list)
    present: bool = True


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, list[Field]]:
    schema: dict[str, list[Field]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            schema.setdefault(row["record"], []).append(
                Field(
                    record=row["record"],
                    name=row["field"],
                    type=row["type"],
                    required=row["required"] == "yes",
                    key=row["key"] == "yes",
                    allowed=tuple(a for a in row["allowed"].split("|") if a),
                    description=row["description"],
                )
            )
    return schema


PARSERS: dict[str, Callable[[str], Any]] = {
    "text": lambda s: s.strip() or None,
    "money": values.parse_money,
    "decimal": values.parse_decimal,
    "date": values.parse_date,
    "bool": values.parse_bool,
    "int": values.parse_int,
    "enum": lambda s: s.strip() or None,
}


def read_table(folder: Path, record: str, fields: list[Field], issues: list[Issue]) -> Table:
    """Read one record file, converting every value and reporting every problem found."""
    path = folder / f"{record}.csv"
    table = Table(record)
    if not path.exists():
        table.present = False
        return table
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        known = {f.name for f in fields}
        missing = [f.name for f in fields if f.required and f.name not in header]
        if missing:
            issues.append(Issue("R02", "error", f"missing required column(s): {', '.join(missing)}", record))
            return table
        extra = [h for h in header if h not in known]
        if extra:
            issues.append(Issue("R02", "warning", f"column(s) not in the schema, ignored: {', '.join(extra)}", record))
        keys: dict[tuple, int] = {}
        key_fields = [f.name for f in fields if f.key]
        for line, raw in enumerate(reader, start=2):
            row: dict[str, Any] = {}
            job = (raw.get("job_id") or "").strip()
            for f in fields:
                text = raw.get(f.name) or ""
                try:
                    value = PARSERS[f.type](text)
                except ValueError as exc:
                    issues.append(Issue("R02", "error", f"{f.name}: {exc}", record, line, job))
                    value = None
                if value is None and f.required:
                    if text.strip() == "":
                        issues.append(Issue("R02", "error", f"{f.name} is required", record, line, job))
                if value is not None and f.allowed and value not in f.allowed:
                    issues.append(
                        Issue("R02", "error", f"{f.name} {value!r} is not one of {', '.join(f.allowed)}", record, line, job)
                    )
                row[f.name] = value
            key = tuple(row[k] for k in key_fields)
            if key_fields and all(k is not None for k in key):
                if key in keys:
                    issues.append(
                        Issue(
                            "R01",
                            "error",
                            f"duplicate key {'/'.join(map(str, key))} (first seen on line {keys[key]})",
                            record,
                            line,
                            job,
                        )
                    )
                else:
                    keys[key] = line
            table.rows.append(row)
            table.lines.append(line)
    return table


def read_folder(folder: Path, schema: dict[str, list[Field]] | None = None) -> tuple[dict[str, Table], list[Issue]]:
    schema = schema or load_schema()
    issues: list[Issue] = []
    tables = {record: read_table(folder, record, schema[record], issues) for record in RECORDS}
    return tables, issues


def write_rows(path: Path, record: str, rows: list[dict[str, Any]], schema: dict[str, list[Field]] | None = None) -> None:
    """Write rows in schema column order, formatting values the way ``read_table`` reads them."""
    schema = schema or load_schema()
    names = [f.name for f in schema[record]]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(names)
        for row in rows:
            writer.writerow([_cell(row.get(n)) for n in names])


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)
