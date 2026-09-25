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
from cdm import manifest  # noqa: E402
from cdm.profile import CHECKS as PROFILE_CHECKS  # noqa: E402
from cdm.profile import profile_file  # noqa: E402
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
        chapter = (ROOT / "07-reconciliation.md").read_text(encoding="utf-8")
        catalogue = (ROOT / "CHECKS.md").read_text(encoding="utf-8")
        for check in CHECKS:
            self.assertIn(f"`{check}`", chapter, f"{check} is not explained in chapter 7")
            self.assertIn(f"`{check}`", catalogue, f"{check} is not in CHECKS.md")
        for check in PROFILE_CHECKS:
            self.assertIn(f"`{check}`", catalogue, f"{check} is not in CHECKS.md")

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
        self.assertEqual(result.checks_failed(), {"R01", "R03", "R05", "R06", "R09", "R10", "R14", "T01"})
        warnings = {i.check for i in result.issues if i.severity == "warning"}
        self.assertEqual(warnings, {"R13", "R16", "R20"})
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
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
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


def _edit(folder: Path, record: str, change) -> None:
    """Apply ``change(rows)`` to one record file in place."""
    path = folder / f"{record}.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    change(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class ConsistencyChecks(unittest.TestCase):
    """Each consistency check fires on a minimal change to the clean sample."""

    def run_with(self, record, change):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "data"
            shutil.copytree(SAMPLES / "clean", folder)
            _edit(folder, record, change)
            result = reconcile(folder)
            return {i.check for i in result.issues if i.severity != "info"}

    def test_r15_ap_line_without_vendor(self):
        def change(rows):
            next(r for r in rows if r["source"] == "ap")["vendor_id"] = ""
        self.assertEqual(self.run_with("cost_transactions", change), {"R15"})

    def test_r17_billed_beyond_contract(self):
        def change(rows):
            next(r for r in rows if r["job_id"] == "J-1107")["work_completed"] = "900000.00"
        self.assertIn("R17", self.run_with("billings", change))

    def test_r18_closed_commitment_with_retainage(self):
        def change(rows):
            next(r for r in rows if r["commitment_id"] == "SC-1104-01")["status"] = "closed"
        self.assertEqual(self.run_with("commitments", change), {"R18"})

    def test_r19_inactive_vendor_with_open_commitment(self):
        def change(rows):
            next(r for r in rows if r["vendor_id"] == "V-2006")["status"] = "inactive"
        self.assertEqual(self.run_with("vendors", change), {"R19"})

    def test_r21_approved_change_on_void_commitment(self):
        def change(rows):
            next(r for r in rows if r["commitment_id"] == "SC-1104-02")["status"] = "void"
        self.assertIn("R21", self.run_with("commitments", change))

    def test_r22_pending_change_on_closed_job(self):
        def change(rows):
            next(r for r in rows if r["job_id"] == "J-1107")["status"] = "closed"
        self.assertIn("R22", self.run_with("jobs", change))

    def test_r23_cost_on_inactive_code(self):
        def change(rows):
            next(r for r in rows if r["cost_code"] == "02-010")["active"] = "no"
        self.assertEqual(self.run_with("cost_codes", change), {"R23"})


class Profiles(unittest.TestCase):
    def test_vendor_list_problems_are_all_found(self):
        p = profile_file(SAMPLES / "legacy-export" / "vendor-list.csv")
        self.assertEqual({f.check for f in p.findings}, {"P01", "P04", "P06", "P07", "P10", "P12", "P13", "P14"})
        self.assertEqual([f.check for f in p.errors], ["P10"])
        kinds = {c.name: c.kind for c in p.columns}
        self.assertEqual(kinds["Tax ID"], "sensitive")
        self.assertEqual(kinds["YTD Paid"], "money")

    def test_job_cost_export_profiles_clean(self):
        p = profile_file(SAMPLES / "legacy-export" / "job-cost-detail.csv")
        self.assertEqual({f.check for f in p.findings}, {"P05"})
        kinds = {c.name: (c.kind, c.detail) for c in p.columns}
        self.assertEqual(kinds["Phase"][0], "code")
        self.assertEqual(kinds["Date"], ("date", "month-first"))
        self.assertTrue(kinds["Amount"][1].startswith("total 1,213,290.57"))

    def test_filtered_credits_are_suspicious(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.csv"
            lines = ["Job,Amount"] + [f'J-1,"${n},000.00"' for n in range(1, 30)]
            path.write_text("\n".join(lines), encoding="utf-8")
            self.assertIn("P11", {f.check for f in profile_file(path).findings})


class Manifests(unittest.TestCase):
    def test_copy_verified_and_changes_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a", Path(tmp) / "b"
            shutil.copytree(SAMPLES / "schedules", a)
            shutil.copytree(SAMPLES / "schedules", b)
            self.assertTrue(manifest.compare(manifest.build(a), manifest.build(b)).passed)
            (b / "fitout.xer").write_text("changed", encoding="utf-8")
            (b / "fitout.xml").rename(b / "moved.xml")
            (b / "fitout-lossy-conversion.xml").unlink()
            d = manifest.compare(manifest.build(a), manifest.build(b))
            self.assertEqual(d.changed, ["fitout.xer"])
            self.assertEqual(d.moved, [("fitout.xml", "moved.xml")])
            self.assertEqual(d.missing, ["fitout-lossy-conversion.xml"])
            self.assertFalse(d.passed)

    def test_manifest_round_trips_through_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = manifest.build(SAMPLES / "schedules")
            out = Path(tmp) / "m.csv"
            manifest.write(entries, out)
            self.assertEqual([e.sha256 for e in manifest.load(out)], [e.sha256 for e in entries])


class Mapping(unittest.TestCase):
    MAPPING = ROOT / "mappings" / "legacy-job-cost-detail.json"
    EXPORT = SAMPLES / "legacy-export" / "job-cost-detail.csv"

    def test_legacy_export_maps_back_to_clean_rows(self):
        result = run_mapping(self.MAPPING, self.EXPORT)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.rows_skipped, 11)
        with (SAMPLES / "clean" / "cost_transactions.csv").open(encoding="utf-8") as handle:
            clean = [r for r in csv.DictReader(handle) if r["job_id"] == "J-1104"]
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
