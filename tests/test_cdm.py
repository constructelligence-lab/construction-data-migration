"""Tests for the migration toolkit. Run: python3 -m unittest discover -s tests"""

from __future__ import annotations

import csv
import datetime as dt
import json
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cdm import values  # noqa: E402
from cdm.mapping import run_mapping  # noqa: E402
from cdm.reconcile import CHECKS, reconcile  # noqa: E402
from cdm.schedule import read_mspdi, read_xer  # noqa: E402
from cdm.schedule.compare import compare  # noqa: E402
from cdm.schedule.mspdi import duration_hours  # noqa: E402
from cdm.schema import load_schema  # noqa: E402

SAMPLES = ROOT / "samples"


class Values(unittest.TestCase):
    def test_accounting_formats(self):
        cases = {
            "1234.5": "1234.50",
            "$1,234.50": "1234.50",
            "(1,234.50)": "-1234.50",
            "1,234.50-": "-1234.50",
            "-$1,234.50": "-1234.50",
            " 0 ": "0.00",
        }
        for text, expected in cases.items():
            self.assertEqual(values.parse_money(text), Decimal(expected), text)

    def test_money_refuses_to_round(self):
        with self.assertRaises(ValueError):
            values.parse_money("12.345")

    def test_money_refuses_junk(self):
        for text in ("abc", "1.2.3", "NaN"):
            with self.assertRaises(ValueError):
                values.parse_money(text)

    def test_blank_is_none(self):
        self.assertIsNone(values.parse_money("  "))
        self.assertIsNone(values.parse_date(""))

    def test_date_is_never_guessed(self):
        self.assertEqual(values.parse_date("03/04/2026", "%m/%d/%Y"), dt.date(2026, 3, 4))
        self.assertEqual(values.parse_date("03/04/2026", "%d/%m/%Y"), dt.date(2026, 4, 3))
        with self.assertRaises(ValueError):
            values.parse_date("03/04/2026")


class Schema(unittest.TestCase):
    def test_every_check_is_documented(self):
        text = (ROOT / "06-reconciliation.md").read_text(encoding="utf-8")
        for check in CHECKS:
            self.assertIn(f"`{check}`", text, f"{check} is not explained in chapter 6")

    def test_sample_headers_match_schema(self):
        schema = load_schema()
        for folder in ("clean", "broken"):
            for record, fields in schema.items():
                with (SAMPLES / folder / f"{record}.csv").open(newline="", encoding="utf-8") as handle:
                    header = next(csv.reader(handle))
                self.assertEqual(header, [f.name for f in fields], f"{folder}/{record}.csv")


class Reconcile(unittest.TestCase):
    def test_clean_sample_ties_out(self):
        result = reconcile(SAMPLES / "clean")
        self.assertTrue(result.passed, [i.message for i in result.errors])
        self.assertEqual(len(result.tie_outs), 21)
        self.assertTrue(all(t.ties for t in result.tie_outs))

    def test_broken_sample_catches_every_planted_fault(self):
        result = reconcile(SAMPLES / "broken")
        self.assertFalse(result.passed)
        self.assertEqual(result.checks_failed(), {"R01", "R03", "R05", "R06", "R09", "R10", "T01"})
        failed = {(t.job_id, t.metric) for t in result.tie_outs if not t.ties}
        self.assertEqual(
            failed,
            {
                ("J-1104", "cost_to_date"),
                ("J-1107", "contract_value"),
                ("J-1107", "committed_cost"),
                ("J-1107", "cost_to_date"),
                ("J-1107", "retainage_payable"),
                ("J-1098", "retainage_receivable"),
            },
        )

    def test_one_cent_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "data"
            shutil.copytree(SAMPLES / "clean", folder)
            path = folder / "cost_transactions.csv"
            rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
            rows[0]["amount"] = str(Decimal(rows[0]["amount"]) + Decimal("0.01"))
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            result = reconcile(folder)
            self.assertEqual(result.checks_failed(), {"T01"})
            self.assertEqual([t.difference for t in result.tie_outs if not t.ties], [Decimal("0.01")])

    def test_missing_control_totals_blocks_sign_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "data"
            shutil.copytree(SAMPLES / "clean", folder)
            (folder / "control_totals.csv").unlink()
            result = reconcile(folder)
            self.assertIn("T03", result.checks_failed())
            self.assertIn("T02", result.checks_failed())


class Mapping(unittest.TestCase):
    MAPPING = ROOT / "mappings" / "legacy-job-cost-detail.json"
    EXPORT = SAMPLES / "legacy-export" / "job-cost-detail.csv"

    def test_legacy_export_maps_back_to_clean_rows(self):
        result = run_mapping(self.MAPPING, self.EXPORT)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.rows_skipped, 11)
        clean = [r for r in csv.DictReader((SAMPLES / "clean" / "cost_transactions.csv").open(encoding="utf-8")) if r["job_id"] == "J-1104"]
        self.assertEqual(len(result.rows), len(clean))
        total = sum(Decimal(r["amount"]) for r in clean)
        self.assertEqual(result.money_out["amount"], total)

    def test_unmapped_code_stops_the_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            export = Path(tmp) / "export.csv"
            text = self.EXPORT.read_text(encoding="utf-8").replace("0106.00", "0199.00", 1)
            export.write_text(text, encoding="utf-8")
            result = run_mapping(self.MAPPING, export)
            self.assertEqual(len(result.errors), 1)
            self.assertIn(("cost_code", "0199.00"), result.unmapped)

    def test_mapping_rejects_unknown_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = json.loads(self.MAPPING.read_text(encoding="utf-8"))
            spec["fields"]["not_a_field"] = {"value": "x"}
            path = Path(tmp) / "m.json"
            path.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaises(ValueError):
                run_mapping(path, self.EXPORT)


class Schedules(unittest.TestCase):
    def test_xer(self):
        s = read_xer(SAMPLES / "schedules" / "fitout.xer")
        self.assertEqual((len(s.activities), len(s.relationships)), (16, 19))
        a = s.by_id()
        self.assertEqual(a["A1000"].type, "milestone")
        self.assertEqual(a["A1060"].wbs, "L1")
        self.assertEqual(a["A1060"].percent_complete, 80)
        self.assertIsNone(a["A1060"].actual_finish)
        link = next(r for r in s.relationships if (r.predecessor_id, r.successor_id) == ("A1060", "A1070"))
        self.assertEqual((link.type, link.lag_hours), ("SS", 120.0))
        self.assertEqual(s.data_date, dt.datetime(2026, 8, 31, 17, 0))

    def test_mspdi(self):
        s = read_mspdi(SAMPLES / "schedules" / "fitout.xml", id_source="name")
        work = [a for a in s.activities if a.type != "summary"]
        self.assertEqual(len(work), 16)
        link = next(r for r in s.relationships if (r.predecessor_id, r.successor_id) == ("Hang and finish board", "Ceiling grid"))
        self.assertEqual((link.type, link.lag_hours), ("SS", 120.0))

    def test_durations(self):
        self.assertEqual(duration_hours("PT16H0M0S"), 16)
        self.assertEqual(duration_hours("PT7H30M0S"), 7.5)
        self.assertEqual(duration_hours("P2DT4H0M0S", hours_per_day=8), 20)
        with self.assertRaises(ValueError):
            duration_hours("16 hours")

    def test_faithful_conversion_passes(self):
        c = compare(read_xer(SAMPLES / "schedules" / "fitout.xer"), read_mspdi(SAMPLES / "schedules" / "fitout.xml"), match="name")
        self.assertTrue(c.passed, c.errors)

    def test_lossy_conversion_fails(self):
        c = compare(
            read_xer(SAMPLES / "schedules" / "fitout.xer"),
            read_mspdi(SAMPLES / "schedules" / "fitout-lossy-conversion.xml"),
            match="name",
        )
        self.assertEqual(len(c.errors), 2, c.errors)
        self.assertTrue(any("missing" in e for e in c.errors))
        self.assertTrue(any("lag 120h became 16h" in e for e in c.errors))


if __name__ == "__main__":
    unittest.main()
