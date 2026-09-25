"""Command line: ``python3 -m cdm <command>``.

Commands
  validate DIR                    check record files against the neutral schema
  reconcile DIR                   tie migrated records out to the old system's control totals
  map MAPPING INPUT --out FILE    turn an old system's CSV export into a neutral record file
  schedule FILE --out DIR         read a P6 XER or Project XML file into neutral CSV
  schedule-compare SOURCE TARGET  check a schedule survived a conversion
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, mapping, report
from .reconcile import reconcile
from .schedule import read_schedule
from .schedule.compare import compare
from .schedule.mspdi import read_mspdi
from .schema import read_folder


def _validate(args) -> int:
    tables, issues = read_folder(Path(args.folder))
    for record, table in tables.items():
        state = f"{len(table.rows)} rows" if table.present else "not present"
        print(f"  {record:<18} {state}")
    for i in issues:
        print(f"{i.severity.upper():<7} {i.check} {i.message}  ({i.where()})")
    errors = sum(1 for i in issues if i.severity == "error")
    print(f"\n{'PASS' if not errors else 'FAIL'}: {errors} errors")
    return 1 if errors else 0


def _reconcile(args) -> int:
    result = reconcile(Path(args.folder))
    sys.stdout.write(report.text_report(result))
    if args.markdown:
        Path(args.markdown).write_text(report.markdown_report(result), encoding="utf-8")
        print(f"sign-off report written to {args.markdown}")
    if args.json:
        Path(args.json).write_text(report.json_report(result), encoding="utf-8")
    return 0 if result.passed else 1


def _map(args) -> int:
    result = mapping.run_mapping(Path(args.mapping), Path(args.input))
    print(mapping.summary(result))
    if result.errors and not args.allow_rejects:
        print("\nnothing written: fix the rejected rows, or pass --allow-rejects to write the clean rows only")
        return 1
    mapping.write_result(result, Path(args.out))
    print(f"written to {args.out}")
    return 1 if result.errors else 0


def _load(path: str, id_source: str):
    if path.lower().endswith(".xml"):
        return read_mspdi(path, id_source=id_source)
    return read_schedule(path)


def _schedule(args) -> int:
    s = _load(args.file, args.id_source)
    print(f"{s.source}: project {s.project or '?'}, data date {s.data_date or '?'}")
    work = [a for a in s.activities if a.type != "summary"]
    summaries = len(s.activities) - len(work)
    print(
        f"  {len(work)} activities" + (f" (+{summaries} summary rows)" if summaries else "")
        + f", {len(s.relationships)} relationships, {len(s.calendars)} calendars"
    )
    has_pred = {r.successor_id for r in s.relationships}
    has_succ = {r.predecessor_id for r in s.relationships}
    no_pred = [a.activity_id for a in work if a.activity_id not in has_pred]
    no_succ = [a.activity_id for a in work if a.activity_id not in has_succ]
    print(f"  open starts (no predecessor): {len(no_pred)}  {' '.join(no_pred[:10])}")
    print(f"  open ends (no successor):     {len(no_succ)}  {' '.join(no_succ[:10])}")
    for w in s.warnings:
        print(f"  WARNING {w}")
    if args.out:
        for p in s.write_csv(Path(args.out)):
            print(f"  written {p}")
    return 0


def _schedule_compare(args) -> int:
    source, target = _load(args.source, args.id_source), _load(args.target, args.id_source)
    c = compare(source, target, match=args.match, date_tolerance_hours=args.date_tolerance_hours)
    for line in c.summary:
        print(line)
    for e in c.errors:
        print(f"ERROR   {e}")
    for w in c.warnings:
        print(f"WARNING {w}")
    print(f"\n{'PASS: the schedule came across intact' if c.passed else 'FAIL'}  ({len(c.errors)} errors, {len(c.warnings)} warnings)")
    return 0 if c.passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m cdm", description="Construction data migration toolkit")
    parser.add_argument("--version", action="version", version=f"cdm {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="check record files against the neutral schema")
    p.add_argument("folder")
    p.set_defaults(run=_validate)

    p = sub.add_parser("reconcile", help="tie migrated records out to control totals")
    p.add_argument("folder")
    p.add_argument("--markdown", help="write a sign-off report to this file")
    p.add_argument("--json", help="write a machine-readable result to this file")
    p.set_defaults(run=_reconcile)

    p = sub.add_parser("map", help="turn an old system's CSV export into a neutral record file")
    p.add_argument("mapping")
    p.add_argument("input")
    p.add_argument("--out", required=True)
    p.add_argument("--allow-rejects", action="store_true", help="write the clean rows even if some rows were rejected")
    p.set_defaults(run=_map)

    p = sub.add_parser("schedule", help="read a P6 XER or Project XML file")
    p.add_argument("file")
    p.add_argument("--out", help="write activities.csv and relationships.csv to this folder")
    p.add_argument("--id-source", default="uid", choices=["uid", "id", "wbs", "name"], help="Project XML only: what identifies a task")
    p.set_defaults(run=_schedule)

    p = sub.add_parser("schedule-compare", help="check a schedule survived a conversion")
    p.add_argument("source")
    p.add_argument("target")
    p.add_argument("--match", default="id", choices=["id", "name"], help="match activities by ID or by name")
    p.add_argument("--id-source", default="uid", choices=["uid", "id", "wbs", "name"], help="Project XML only: what identifies a task")
    p.add_argument("--date-tolerance-hours", type=float, default=0.0)
    p.set_defaults(run=_schedule_compare)

    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
