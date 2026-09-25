"""Turn an old system's CSV export into a neutral-schema record file, using a JSON mapping.

A mapping says, for each neutral field, where its value comes from and how to clean it. The point
of keeping it in a file rather than in code is that the controller can read it, the PM lead can
challenge it, and the same mapping runs identically in the trial load and the final load.

Mapping format (see ``mappings/`` for a worked example)::

    {
      "record": "cost_transactions",
      "skip_if": [{"column": "Job", "matches": "^(|Total.*)$"}],
      "fields": {
        "transaction_id": {"template": "{Batch}-{Line}"},
        "job_id":         {"from": "Job"},
        "cost_code":      {"from": "Phase", "crosswalk": "cost-code-crosswalk.csv"},
        "cost_type":      {"from": "Cat", "map": {"L": "labor", "M": "material"}},
        "posted_date":    {"from": "Date", "date_format": "%m/%d/%Y"},
        "amount":         {"from": "Amount"},
        "source":         {"value": "ap"}
      }
    }

Every problem is reported with its source line number. Nothing is guessed: an unmapped code, an
unknown category or an ambiguous date stops the row rather than being passed through.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from . import values
from .schema import Field, load_schema, write_rows


@dataclass
class MapResult:
    record: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    rows_read: int = 0
    rows_skipped: int = 0
    unmapped: Counter = field(default_factory=Counter)
    money_in: dict[str, Decimal] = field(default_factory=dict)
    money_out: dict[str, Decimal] = field(default_factory=dict)


def load_crosswalk(path: Path) -> dict[str, str]:
    """Read a two-column crosswalk (``old_code,new_code``); extra columns such as notes are ignored."""
    table: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for line, row in enumerate(csv.DictReader(handle), start=2):
            old, new = (row.get("old_code") or "").strip(), (row.get("new_code") or "").strip()
            if not old:
                continue
            if old in table and table[old] != new:
                raise ValueError(f"{path.name} line {line}: {old} is mapped twice, to {table[old]} and {new}")
            table[old] = new
    return table


def run_mapping(mapping_path: Path, input_path: Path) -> MapResult:
    spec = json.loads(mapping_path.read_text(encoding="utf-8"))
    record = spec["record"]
    schema = load_schema()
    fields: dict[str, Field] = {f.name: f for f in schema[record]}
    unknown = [name for name in spec["fields"] if name not in fields]
    if unknown:
        raise ValueError(f"mapping sets field(s) not in the {record} schema: {', '.join(unknown)}")

    crosswalks = {
        name: load_crosswalk(mapping_path.parent / rule["crosswalk"])
        for name, rule in spec["fields"].items()
        if "crosswalk" in rule
    }
    skips = [(rule["column"], re.compile(rule["matches"])) for rule in spec.get("skip_if", [])]
    encoding = spec.get("encoding", "utf-8-sig")
    delimiter = spec.get("delimiter", ",")

    result = MapResult(record)
    money_fields = [n for n, f in fields.items() if f.type == "money" and n in spec["fields"]]
    for name in money_fields:
        result.money_in[name] = Decimal("0.00")
        result.money_out[name] = Decimal("0.00")

    with input_path.open(newline="", encoding=encoding) as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        header = reader.fieldnames or []
        wanted = {rule["from"] for rule in spec["fields"].values() if "from" in rule}
        wanted |= {c for rule in spec["fields"].values() for c in re.findall(r"{([^}]+)}", rule.get("template", ""))}
        missing = sorted(wanted - set(header))
        if missing:
            raise ValueError(f"{input_path.name} has no column(s): {', '.join(missing)}")

        for line, raw in enumerate(reader, start=2):
            raw = {k: (v or "") for k, v in raw.items() if k is not None}
            if any(pattern.fullmatch(raw.get(col, "").strip()) for col, pattern in skips):
                result.rows_skipped += 1
                continue
            result.rows_read += 1
            row: dict[str, Any] = {}
            row_errors: list[str] = []
            for name, rule in spec["fields"].items():
                f = fields[name]
                try:
                    value = _value(rule, raw, f, crosswalks.get(name))
                except _Unmapped as exc:
                    result.unmapped[(name, exc.code)] += 1
                    row_errors.append(f"line {line}: {name}: no mapping for {exc.code!r}")
                    continue
                except ValueError as exc:
                    row_errors.append(f"line {line}: {name}: {exc}")
                    continue
                if value is None and f.required:
                    row_errors.append(f"line {line}: {name} is required but empty")
                if value is not None and f.allowed and value not in f.allowed:
                    row_errors.append(f"line {line}: {name} {value!r} is not one of {', '.join(f.allowed)}")
                if f.type == "money" and value is not None:
                    result.money_in[name] += value
                row[name] = value
            if row_errors:
                result.errors.extend(row_errors)
                continue
            for name in money_fields:
                if row.get(name) is not None:
                    result.money_out[name] += row[name]
            result.rows.append(row)
    return result


class _Unmapped(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _value(rule: dict[str, Any], raw: dict[str, str], f: Field, crosswalk: dict[str, str] | None) -> Any:
    if "value" in rule:
        text = str(rule["value"])
    elif "template" in rule:
        text = rule["template"].format(**{k: v.strip() for k, v in raw.items()})
    else:
        text = raw.get(rule["from"], "")
    text = text.strip()
    if rule.get("upper"):
        text = text.upper()
    if crosswalk is not None and text:
        if text not in crosswalk:
            raise _Unmapped(text)
        text = crosswalk[text]
    if "map" in rule and text:
        if text not in rule["map"]:
            raise _Unmapped(text)
        text = rule["map"][text]
    if f.type == "date":
        return values.parse_date(text, rule.get("date_format", "%Y-%m-%d"))
    if f.type == "money":
        return values.parse_money(text)
    if f.type == "decimal":
        return values.parse_decimal(text)
    if f.type == "int":
        return values.parse_int(text)
    if f.type == "bool":
        return values.parse_bool(text)
    return text or None


def write_result(result: MapResult, out: Path) -> None:
    write_rows(out, result.record, result.rows)


def summary(result: MapResult) -> str:
    lines = [
        f"{result.record}: {result.rows_read} rows read, {len(result.rows)} written, "
        f"{result.rows_read - len(result.rows)} rejected, {result.rows_skipped} skipped by skip_if"
    ]
    for name in result.money_in:
        lines.append(f"  {name}: {result.money_in[name]:,.2f} parsed, {result.money_out[name]:,.2f} written")
    if result.unmapped:
        lines.append("  unmapped values (add them to the crosswalk or map, then re-run):")
        for (name, code), n in sorted(result.unmapped.items()):
            lines.append(f"    {name} {code!r}: {n} row(s)")
    for error in result.errors[:50]:
        lines.append(f"  {error}")
    if len(result.errors) > 50:
        lines.append(f"  ... and {len(result.errors) - 50} more")
    return "\n".join(lines)
