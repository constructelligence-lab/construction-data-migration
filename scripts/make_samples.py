#!/usr/bin/env python3
"""Generate the synthetic sample data in ``samples/``.

Every job, vendor, figure and date produced here is invented. Nothing is taken from a real
project, a real company or any vendor's system. The generator is deterministic, so the samples
only change when this script does.

    python3 scripts/make_samples.py

Writes:
  samples/clean/           a migration that ties out to the cent
  samples/broken/          the same migration with twelve classic migration faults planted in it
  samples/legacy-export/   one job's cost detail as a typical old-system report export
  samples/schedules/       one schedule as P6 XER, as Project XML, and as a lossy conversion
"""

from __future__ import annotations

import copy
import csv
import datetime as dt
import os
import random
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cdm.schema import RECORDS, load_schema, write_rows  # noqa: E402

# CDM_SAMPLES_OUT lets the repository check regenerate into a scratch folder and diff the result.
SAMPLES = Path(os.environ.get("CDM_SAMPLES_OUT") or ROOT / "samples")
AS_OF = dt.date(2026, 8, 31)
CENT = Decimal("0.01")
rng = random.Random(20260831)
batch_counter = 0


def money(x) -> Decimal:
    return Decimal(str(x)).quantize(CENT, rounding=ROUND_HALF_UP)


def month_ends(start: dt.date, end: dt.date) -> list[dt.date]:
    out, y, m = [], start.year, start.month
    while True:
        nxt = dt.date(y + (m == 12), 1 if m == 12 else m + 1, 1)
        last = nxt - dt.timedelta(days=1)
        if last > end:
            return out
        out.append(last)
        y, m = nxt.year, nxt.month


# --------------------------------------------------------------------------- reference data

COST_CODES = [
    ("01-060", "Project supervision", "01", True),
    ("01-070", "Project management", "01", True),
    ("01-100", "Testing and inspection", "01", True),
    ("02-010", "Selective demolition", "02", True),
    ("03-100", "Concrete slab on grade", "03", True),
    ("05-040", "Miscellaneous metals", "05", True),
    ("06-010", "Rough carpentry", "06", False),
    ("06-050", "Architectural millwork", "06", True),
    ("07-070", "Firestopping", "07", True),
    ("08-040", "Door hardware sets", "08", True),
    ("09-010", "Metal stud framing", "09", True),
    ("09-020", "Gypsum board hanging", "09", True),
    ("09-060", "Resilient flooring", "09", True),
    ("09-090", "Painting interior", "09", True),
    ("22-010", "Sanitary drainage", "22", True),
    ("23-010", "Ductwork", "23", True),
    ("26-020", "Panelboards", "26", True),
]

# The old system's phase codes. Two old codes merge into one new code, which is normal and fine
# as long as the crosswalk says so and nobody renames a code that already carries postings.
LEGACY_CODES = {
    "01-060": ["0106.00"],
    "01-070": ["0107.00"],
    "01-100": ["0110.00"],
    "02-010": ["0201.00"],
    "03-100": ["0310.00"],
    "05-040": ["0504.00"],
    "06-010": ["0601.00"],
    "06-050": ["0605.00"],
    "07-070": ["0707.00"],
    "08-040": ["0804.00"],
    "09-010": ["0901.00"],
    "09-020": ["0902.00", "0902.10"],
    "09-060": ["0906.00"],
    "09-090": ["0909.00"],
    "22-010": ["2201.00"],
    "23-010": ["2301.00"],
    "26-020": ["2602.00"],
}
LEGACY_CATEGORY = {"labor": "L", "material": "M", "subcontract": "S", "equipment": "E", "other": "O"}

VENDORS = [
    ("V-2001", "Sample Drywall Co", "4821", False),
    ("V-2002", "Sample Mechanical Co", "1937", False),
    ("V-2003", "Sample Electric Co", "6604", False),
    ("V-2004", "Sample Flooring Co", "2210", True),
    ("V-2005", "Sample Painting Co", "8843", True),
    ("V-2006", "Sample Millwork Co", "5072", False),
    ("V-2007", "Sample Hardware Supply", "3318", False),
    ("V-2008", "Sample Testing Labs", "7461", True),
    ("V-2009", "Sample Concrete Co", "9025", False),
]

JOBS = [
    # job_id, name, status, customer, contract_type, original_contract, retainage_pct, start
    ("J-1104", "Riverside Clinic Fit-out", "open", "Sample Health Partners", "lump_sum", "2480000.00", "10", dt.date(2026, 2, 2)),
    ("J-1107", "Harbor Street Retail Shell", "open", "Sample Retail Holdings", "gmp", "985000.00", "5", dt.date(2026, 4, 6)),
    ("J-1098", "Oak Avenue Office Refresh", "warranty", "Sample Office Trust", "lump_sum", "498600.00", "10", dt.date(2025, 9, 8)),
]

# job -> list of (commitment_id, vendor, type, cost_code, description, value, retainage %, progress 0-1)
COMMITMENTS = {
    "J-1104": [
        ("SC-1104-01", "V-2001", "subcontract", "09-020", "Framing, board and finishing", "412000.00", "10", 0.62),
        ("SC-1104-02", "V-2002", "subcontract", "23-010", "HVAC and ductwork", "538500.00", "10", 0.55),
        ("SC-1104-03", "V-2003", "subcontract", "26-020", "Electrical", "467250.00", "10", 0.58),
        ("SC-1104-04", "V-2004", "subcontract", "09-060", "Resilient flooring", "96400.00", "10", 0.0),
        ("SC-1104-05", "V-2006", "subcontract", "06-050", "Casework and millwork", "142800.00", "10", 0.18),
        ("PO-1104-01", "V-2007", "purchase_order", "08-040", "Door hardware sets", "38650.00", "0", 0.45),
        ("SC-1104-06", "V-2008", "subcontract", "01-100", "Special inspections", "24500.00", "0", 0.50),
    ],
    "J-1107": [
        ("SC-1107-01", "V-2009", "subcontract", "03-100", "Slab on grade and topping", "186300.00", "5", 0.92),
        ("SC-1107-02", "V-2002", "subcontract", "22-010", "Underground sanitary", "74200.00", "5", 0.80),
        ("SC-1107-03", "V-2003", "subcontract", "26-020", "Service and panels", "221900.00", "5", 0.30),
        ("SC-1107-04", "V-2001", "subcontract", "09-010", "Demising walls", "98750.00", "5", 0.10),
        ("PO-1107-01", "V-2007", "purchase_order", "05-040", "Misc metals: lintels and bollards", "31480.00", "0", 0.65),
        ("SC-1107-05", "V-2005", "subcontract", "09-090", "Painting", "27400.00", "5", 0.0),
    ],
    "J-1098": [
        ("SC-1098-01", "V-2001", "subcontract", "09-020", "Partitions and ceilings", "88600.00", "10", 1.0),
        ("SC-1098-02", "V-2005", "subcontract", "09-090", "Painting", "41250.00", "10", 1.0),
        ("SC-1098-03", "V-2004", "subcontract", "09-060", "Carpet and resilient", "63900.00", "10", 1.0),
        ("SC-1098-04", "V-2003", "subcontract", "26-020", "Lighting and power", "72400.00", "10", 1.0),
        ("PO-1098-01", "V-2007", "purchase_order", "08-040", "Door hardware", "12780.00", "0", 1.0),
    ],
}

# self-performed work: job -> list of (cost_code, cost_type, monthly amount)
SELF_PERFORMED = {
    "J-1104": [("01-060", "labor", 18400), ("01-070", "other", 12600), ("02-010", "labor", 9800), ("07-070", "material", 3100)],
    "J-1107": [("01-060", "labor", 16800), ("01-070", "other", 10400), ("02-010", "labor", 4200)],
    "J-1098": [("01-060", "labor", 9600), ("01-070", "other", 6100), ("02-010", "labor", 5200)],
}

# job -> list of (change_order_id, level, commitment_id, cost_code, cost_type, status, amount, description)
CHANGE_ORDERS = {
    "J-1104": [
        ("OCO-1104-001", "owner", "", "23-010", "subcontract", "approved", "46250.00", "Added exam room exhaust"),
        ("OCO-1104-002", "owner", "", "09-020", "subcontract", "approved", "18900.00", "Lead-lined partitions at imaging"),
        ("OCO-1104-003", "owner", "", "26-020", "subcontract", "pending", "27400.00", "Owner-requested nurse call rough-in"),
        ("OCO-1104-004", "owner", "", "06-050", "subcontract", "rejected", "15200.00", "Upgraded reception counter"),
        ("CCO-1104-001", "commitment", "SC-1104-02", "23-010", "subcontract", "approved", "41800.00", "Exam room exhaust"),
        ("CCO-1104-002", "commitment", "SC-1104-01", "09-020", "subcontract", "approved", "16450.00", "Lead-lined partitions"),
        ("CCO-1104-003", "commitment", "SC-1104-03", "26-020", "subcontract", "pending", "24100.00", "Nurse call rough-in"),
    ],
    "J-1107": [
        ("OCO-1107-001", "owner", "", "03-100", "subcontract", "approved", "-8400.00", "Deduct: slab thickness revised"),
        ("OCO-1107-002", "owner", "", "22-010", "subcontract", "pending", "12650.00", "Grease interceptor relocation"),
        ("CCO-1107-001", "commitment", "SC-1107-01", "03-100", "subcontract", "approved", "-7650.00", "Slab thickness revised"),
    ],
    "J-1098": [
        ("OCO-1098-001", "owner", "", "09-060", "subcontract", "approved", "9850.00", "Carpet upgrade in boardroom"),
        ("CCO-1098-001", "commitment", "SC-1098-03", "09-060", "subcontract", "approved", "8420.00", "Carpet upgrade"),
    ],
}

REPORTS = {
    "contract_value": "Contract status report",
    "revised_budget": "Job cost summary",
    "committed_cost": "Commitment register",
    "cost_to_date": "Job cost summary",
    "billed_to_date": "Billing history report",
    "retainage_receivable": "Retainage receivable report",
    "retainage_payable": "Retainage payable report",
}


# --------------------------------------------------------------------------- build

def build():
    global batch_counter
    data = {r: [] for r in RECORDS}
    for code, desc, div, active in COST_CODES:
        data["cost_codes"].append({"cost_code": code, "description": desc, "csi_division": div, "active": active})
    for vid, name, tin, is1099 in VENDORS:
        data["vendors"].append({"vendor_id": vid, "vendor_name": name, "tin_last4": tin, "reports_1099": is1099, "status": "active"})

    for job_id, name, status, customer, ctype, contract, ret, start in JOBS:
        data["jobs"].append(
            {
                "job_id": job_id,
                "job_name": name,
                "status": status,
                "customer": customer,
                "contract_type": ctype,
                "original_contract": money(contract),
                "retainage_pct": Decimal(ret),
                "start_date": start,
            }
        )
        end = AS_OF if status == "open" else dt.date(2026, 3, 31)
        months = month_ends(start, end)
        budget: dict[tuple[str, str], Decimal] = {}

        for cid, vendor, ctype_c, code, desc, value, ret_c, progress in COMMITMENTS[job_id]:
            data["commitments"].append(
                {
                    "commitment_id": cid,
                    "job_id": job_id,
                    "vendor_id": vendor,
                    "commitment_type": ctype_c,
                    "description": desc,
                    "original_value": money(value),
                    "retainage_pct": Decimal(ret_c),
                    "status": "closed" if status != "open" else "open",
                }
            )
            ctype_line = "subcontract" if ctype_c == "subcontract" else "material"
            budget[(code, ctype_line)] = budget.get((code, ctype_line), Decimal(0)) + money(value) * Decimal("1.06")

        for co in CHANGE_ORDERS[job_id]:
            coid, level, cid, code, ctyp, st, amount, desc = co
            data["change_orders"].append(
                {
                    "change_order_id": coid,
                    "job_id": job_id,
                    "level": level,
                    "commitment_id": cid or None,
                    "cost_code": code,
                    "cost_type": ctyp,
                    "status": st,
                    "amount": money(amount),
                    "description": desc,
                }
            )

        approved_co_budget: dict[tuple[str, str], Decimal] = {}
        for co in CHANGE_ORDERS[job_id]:
            if co[1] == "commitment" and co[5] == "approved":
                key = (co[3], co[4])
                approved_co_budget[key] = approved_co_budget.get(key, Decimal(0)) + money(co[6])

        # AP against commitments, spread over the months, with retainage withheld
        committed = {c[0]: money(c[5]) for c in COMMITMENTS[job_id]}
        for co in CHANGE_ORDERS[job_id]:
            if co[1] == "commitment" and co[5] == "approved":
                committed[co[2]] += money(co[6])
        for cid, vendor, ctype_c, code, desc, value, ret_c, progress in COMMITMENTS[job_id]:
            target = money(committed[cid] * Decimal(str(progress)))
            if target == 0:
                continue
            active_months = months[max(0, len(months) - rng.randint(2, max(2, len(months)))):]
            weights = [rng.uniform(0.6, 1.4) for _ in active_months]
            total_w = sum(weights)
            remaining = target
            for i, (month, w) in enumerate(zip(active_months, weights)):
                amt = remaining if i == len(active_months) - 1 else money(target * Decimal(str(w / total_w)))
                remaining -= amt
                batch_counter += 1
                ret_amt = money(amt * Decimal(ret_c) / 100)
                data["cost_transactions"].append(
                    {
                        "transaction_id": f"B{month:%y%m}-{batch_counter:03d}",
                        "job_id": job_id,
                        "cost_code": code,
                        "cost_type": "subcontract" if ctype_c == "subcontract" else "material",
                        "posted_date": month - dt.timedelta(days=rng.randint(0, 6)),
                        "amount": amt,
                        "source": "ap",
                        "commitment_id": cid,
                        "vendor_id": vendor,
                        "retainage_withheld": ret_amt if ret_amt else None,
                    }
                )
            if status != "open" and Decimal(ret_c) > 0:
                # warranty job: retainage released to the vendor at closeout
                withheld = sum(
                    (t["retainage_withheld"] or Decimal(0)) for t in data["cost_transactions"] if t["commitment_id"] == cid
                )
                batch_counter += 1
                data["cost_transactions"].append(
                    {
                        "transaction_id": f"B2604-{batch_counter:03d}",
                        "job_id": job_id,
                        "cost_code": code,
                        "cost_type": "subcontract",
                        "posted_date": dt.date(2026, 4, 30),
                        "amount": Decimal("0.00"),
                        "source": "ap",
                        "commitment_id": cid,
                        "vendor_id": vendor,
                        "retainage_withheld": -withheld,
                    }
                )

        # self-performed payroll and job costs
        for month in months:
            for code, ctyp, base in SELF_PERFORMED[job_id]:
                batch_counter += 1
                amt = money(base * rng.uniform(0.8, 1.2))
                data["cost_transactions"].append(
                    {
                        "transaction_id": f"B{month:%y%m}-{batch_counter:03d}",
                        "job_id": job_id,
                        "cost_code": code,
                        "cost_type": ctyp,
                        "posted_date": month,
                        "amount": amt,
                        "source": "payroll" if ctyp == "labor" else "journal",
                        "commitment_id": None,
                        "vendor_id": None,
                        "retainage_withheld": None,
                    }
                )
                budget[(code, ctyp)] = budget.get((code, ctyp), Decimal(0)) + amt * Decimal("1.08")
        # one credit: a returned material, which is exactly the kind of line that goes missing
        batch_counter += 1
        data["cost_transactions"].append(
            {
                "transaction_id": f"B{months[-1]:%y%m}-{batch_counter:03d}",
                "job_id": job_id,
                "cost_code": "07-070" if job_id == "J-1104" else "02-010",
                "cost_type": "material" if job_id == "J-1104" else "labor",
                "posted_date": months[-1],
                "amount": money(-rng.randint(200, 900)),
                "source": "journal",
                "commitment_id": None,
                "vendor_id": None,
                "retainage_withheld": None,
            }
        )

        for (code, ctyp), amt in sorted(budget.items()):
            data["budgets"].append(
                {
                    "job_id": job_id,
                    "cost_code": code,
                    "cost_type": ctyp,
                    "original_budget": money(round(amt, -2)),
                    "approved_changes": approved_co_budget.get((code, ctyp), Decimal("0.00")).quantize(CENT),
                }
            )

        # owner billing: one application per month, earned roughly in line with cost
        contract_value = money(contract) + sum(money(c[6]) for c in CHANGE_ORDERS[job_id] if c[1] == "owner" and c[5] == "approved")
        job_cost = sum(t["amount"] for t in data["cost_transactions"] if t["job_id"] == job_id)
        revised_budget = sum(b["original_budget"] + b["approved_changes"] for b in data["budgets"] if b["job_id"] == job_id)
        pct_complete = min(Decimal("1"), job_cost / revised_budget) if status == "open" else Decimal("1")
        earned_total = money(contract_value * pct_complete)
        per_month = [money(earned_total / len(months))] * len(months)
        per_month[-1] = earned_total - sum(per_month[:-1])
        for n, (month, amount) in enumerate(zip(months, per_month), start=1):
            held = money(amount * Decimal(ret) / 100)
            data["billings"].append(
                {
                    "job_id": job_id,
                    "application_number": n,
                    "period_end": month,
                    "work_completed": amount,
                    "retainage_held": held,
                    "retainage_released": Decimal("0.00"),
                    "status": "approved" if month < AS_OF else "submitted",
                }
            )
        if status != "open":
            total_held = sum(b["retainage_held"] for b in data["billings"] if b["job_id"] == job_id)
            data["billings"].append(
                {
                    "job_id": job_id,
                    "application_number": len(months) + 1,
                    "period_end": dt.date(2026, 5, 31),
                    "work_completed": Decimal("0.00"),
                    "retainage_held": Decimal("0.00"),
                    "retainage_released": money(total_held / 2),
                    "status": "approved",
                }
            )
        if status == "open":
            data["billings"].append(
                {
                    "job_id": job_id,
                    "application_number": len(months) + 1,
                    "period_end": dt.date(2026, 9, 30),
                    "work_completed": money(contract_value * Decimal("0.04")),
                    "retainage_held": money(contract_value * Decimal("0.04") * Decimal(ret) / 100),
                    "retainage_released": Decimal("0.00"),
                    "status": "draft",
                }
            )

    data["control_totals"] = control_totals(data)
    return data


def control_totals(data) -> list[dict]:
    """The figures the old system's own reports would print at cutover.

    Deliberately computed here with plain loops rather than by calling ``cdm.reconcile``, so the
    samples are an independent check on the reconciliation code rather than a copy of it.
    """
    rows = []
    for job in data["jobs"]:
        j = job["job_id"]
        cos = [c for c in data["change_orders"] if c["job_id"] == j and c["status"] == "approved"]
        commits = [c for c in data["commitments"] if c["job_id"] == j and c["status"] != "void"]
        txns = [t for t in data["cost_transactions"] if t["job_id"] == j and t["posted_date"] <= AS_OF]
        bills = [b for b in data["billings"] if b["job_id"] == j and b["status"] != "draft"]
        figures = {
            "contract_value": job["original_contract"] + sum(c["amount"] for c in cos if c["level"] == "owner"),
            "revised_budget": sum(b["original_budget"] + b["approved_changes"] for b in data["budgets"] if b["job_id"] == j),
            "committed_cost": sum(c["original_value"] for c in commits) + sum(c["amount"] for c in cos if c["level"] == "commitment"),
            "cost_to_date": sum(t["amount"] for t in txns),
            "billed_to_date": sum(b["work_completed"] for b in bills),
            "retainage_receivable": sum(b["retainage_held"] - b["retainage_released"] for b in bills),
            "retainage_payable": sum((t["retainage_withheld"] or Decimal(0)) for t in txns),
        }
        for metric, value in figures.items():
            rows.append({"job_id": j, "metric": metric, "value": money(value), "source_report": REPORTS[metric], "as_of": AS_OF})
    return rows


def break_it(clean) -> dict:
    """Plant the faults that real migrations actually suffer. Each one is listed in samples/README.md."""
    d = copy.deepcopy(clean)
    tx = d["cost_transactions"]

    # 1. a payroll line exported twice under a new reference (a re-run export appended to the first)
    dup = next(t for t in tx if t["job_id"] == "J-1104" and t["source"] == "payroll")
    tx.append(dict(dup, transaction_id=dup["transaction_id"] + "-R"))
    # 2. a cost code renamed in the new system without updating the crosswalk
    next(t for t in tx if t["job_id"] == "J-1104" and t["cost_code"] == "09-020")["cost_code"] = "09-025"
    # 3. a pending owner change order mapped to approved
    next(c for c in d["change_orders"] if c["change_order_id"] == "OCO-1107-002")["status"] = "approved"
    # 4. a full tax ID pasted into the vendor file
    next(v for v in d["vendors"] if v["vendor_id"] == "V-2005")["tin_last4"] = "00-0000000"  # obviously invalid: never plant a number that could be real
    # 5. retainage release keyed as the whole amount rather than the half actually released
    rel = next(b for b in d["billings"] if b["job_id"] == "J-1098" and b["retainage_released"] > 0)
    rel["retainage_released"] = rel["retainage_released"] * 3
    # 6. a September invoice posted into the August cutover load
    next(t for t in tx if t["job_id"] == "J-1107" and t["source"] == "ap")["posted_date"] = dt.date(2026, 9, 3)
    # 7. a commitment change order attached to the right number on the wrong job
    next(c for c in d["change_orders"] if c["change_order_id"] == "CCO-1107-001")["commitment_id"] = "SC-1104-01"
    # 8. a credit note dropped by a filter that kept positive amounts only
    credit = next(t for t in tx if t["job_id"] == "J-1107" and t["amount"] < 0)
    tx.remove(credit)
    # 9. the same commitment line loaded twice with the same key
    d["commitments"].append(dict(next(c for c in d["commitments"] if c["commitment_id"] == "PO-1107-01")))
    # 10. an AP invoice keyed to the wrong vendor against the right subcontract
    next(t for t in tx if t["commitment_id"] == "SC-1104-02")["vendor_id"] = "V-2003"
    # 11. pay applications renumbered from 3 onwards, leaving a gap the owner will ask about
    for b in d["billings"]:
        if b["job_id"] == "J-1107" and b["application_number"] >= 3:
            b["application_number"] += 1
    # 12. the same subcontractor set up twice under two vendor numbers
    d["vendors"].append({"vendor_id": "V-2010", "vendor_name": "SAMPLE DRYWALL CO.", "tin_last4": "4821", "reports_1099": False, "status": "active"})
    return d


def legacy_export(clean, job_id: str) -> None:
    """Write one job's cost detail the way an old system's report export usually looks."""
    folder = SAMPLES / "legacy-export"
    folder.mkdir(parents=True, exist_ok=True)
    rows = sorted((t for t in clean["cost_transactions"] if t["job_id"] == job_id), key=lambda t: (t["cost_code"], t["posted_date"], t["transaction_id"]))

    def fmt(amount: Decimal | None) -> str:
        if amount is None:
            return ""
        return f"({-amount:,.2f})" if amount < 0 else f"${amount:,.2f}"

    source_letter = {"ap": "AP", "payroll": "PR", "journal": "JE", "equipment": "EQ", "opening_balance": "OB"}
    with (folder / "job-cost-detail.csv").open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle, lineterminator="\r\n")
        w.writerow(["Job", "Phase", "Cat", "Date", "Src", "Batch", "Line", "Vendor", "Commitment", "Amount", "Ret"])
        current = None
        subtotal = Decimal(0)
        for t in rows:
            if current and t["cost_code"] != current:
                w.writerow(["", f"Total {LEGACY_CODES[current][0]}", "", "", "", "", "", "", "", fmt(subtotal), ""])
                subtotal = Decimal(0)
            current = t["cost_code"]
            subtotal += t["amount"]
            batch, line = t["transaction_id"].split("-", 1)
            codes = LEGACY_CODES[t["cost_code"]]
            legacy_code = codes[int(line) % len(codes)]
            w.writerow(
                [
                    t["job_id"],
                    legacy_code,
                    LEGACY_CATEGORY[t["cost_type"]],
                    t["posted_date"].strftime("%m/%d/%Y"),
                    source_letter[t["source"]],
                    batch,
                    line,
                    t["vendor_id"] or "",
                    t["commitment_id"] or "",
                    fmt(t["amount"]),
                    fmt(t["retainage_withheld"]),
                ]
            )
        w.writerow(["", f"Total {LEGACY_CODES[current][0]}", "", "", "", "", "", "", "", fmt(subtotal), ""])
        w.writerow(["Total Job", job_id, "", "", "", "", "", "", "", fmt(sum(t["amount"] for t in rows)), ""])

    with (folder / "cost-code-crosswalk.csv").open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle, lineterminator="\n")
        w.writerow(["old_code", "new_code", "note"])
        for new, olds in LEGACY_CODES.items():
            for old in olds:
                note = "merged: old codes 0902.00 and 0902.10 were the same scope" if len(olds) > 1 else ""
                w.writerow([old, new, note])


def vendor_export() -> None:
    """A vendor list exported the way it should NOT leave an accounting system, for ``cdm profile``.

    Every problem in it is deliberate. The tax IDs all start with 00, which is not a valid prefix, so
    none of them can be a real number.
    """
    rows = [
        ["Vendor No", "Name", "Tax ID", "Type", "1099", "Last Payment", "YTD Paid"],
        ["002001", "Sample Drywall Co", "00-0000001", "Sub", "N", "08/07/2026", "184,220.15"],
        ["002002", "Sample Mechanical Co", "00-0000002", "Sub", "N", "08/12/2026", "221,904.40"],
        ["2003", "Sample Electric Co", "00-0000003", "Sub", "N", "07/11/2026", "198,310.00"],
        ["002004", "Sample Flooring Co ", "00-0000004", "Sub", "Y", "06/02/2026", "12,480.00"],
        ["002005", "Sample Painting Co", "00-0000005", "Sub", "Y", "05/09/2026", "9,875.50"],
        ["002006", "Sample Millwork Co", "00-0000006", "Sub", "N", "08/03/2026", "26,110.75"],
        ["002007", "Sample Hardware Supply", "00-0000007", "Supplier", "N", "08/10/2026", "31,642.18"],
        ["002008", "Sample Testing Labs", "00-0000008", "Service", "Y", "04/06/2026", "12,250.00"],
        ["002009", "Sample Concrete Co", "00-0000009", "Sub", "N", "07/01/2026", "171,396.00"],
        ["002010", "SAMPLE DRYWALL CO.", "00-0000010", "Sub", "N", "03/02/2026", "4,100.00"],
        ["002011", "Sample Démolition Société", "00-0000011", "Sub", "N", "02/10/2026", "2.51E+04"],
        ["002011", "Sample Démolition Société", "00-0000011", "Sub", "N", "02/10/2026", "2.51E+04"],
    ]
    folder = SAMPLES / "legacy-export"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "vendor-list.csv").open("w", newline="", encoding="cp1252") as handle:
        csv.writer(handle, lineterminator="\r\n").writerows(rows)


# --------------------------------------------------------------------------- schedules

ACTIVITIES = [
    # id, name, wbs, type, start, working days, pct complete
    ("A1000", "Notice to proceed", "PRE", "milestone", dt.date(2026, 2, 2), 0, 100),
    ("A1010", "Selective demolition", "PRE", "task", dt.date(2026, 2, 2), 15, 100),
    ("A1020", "Overhead MEP rough-in", "L1", "task", dt.date(2026, 2, 23), 30, 100),
    ("A1030", "Wall framing", "L1", "task", dt.date(2026, 3, 9), 25, 100),
    ("A1040", "In-wall MEP rough-in", "L1", "task", dt.date(2026, 4, 13), 20, 100),
    ("A1050", "In-wall inspections", "L1", "task", dt.date(2026, 5, 11), 5, 100),
    ("A1060", "Hang and finish board", "L1", "task", dt.date(2026, 5, 18), 30, 80),
    ("A1070", "Ceiling grid", "L1", "task", dt.date(2026, 6, 22), 20, 60),
    ("A1080", "Prime and first coat paint", "L1", "task", dt.date(2026, 7, 20), 15, 30),
    ("A1090", "Casework and millwork", "L1", "task", dt.date(2026, 8, 17), 20, 10),
    ("A1100", "Resilient flooring", "L1", "task", dt.date(2026, 9, 14), 15, 0),
    ("A1110", "MEP trim and devices", "L1", "task", dt.date(2026, 9, 14), 20, 0),
    ("A1120", "Door hardware", "L1", "task", dt.date(2026, 10, 5), 8, 0),
    ("A1130", "Test and balance", "CLOSE", "task", dt.date(2026, 10, 12), 10, 0),
    ("A1140", "Punch list", "CLOSE", "task", dt.date(2026, 10, 26), 10, 0),
    ("A1150", "Substantial completion", "CLOSE", "milestone", dt.date(2026, 11, 6), 0, 0),
]
LINKS = [
    ("A1000", "A1010", "FS", 0),
    ("A1010", "A1020", "SS", 40),
    ("A1010", "A1030", "FS", 0),
    ("A1030", "A1040", "SS", 80),
    ("A1020", "A1040", "FS", 0),
    ("A1040", "A1050", "FS", 0),
    ("A1050", "A1060", "FS", 0),
    ("A1060", "A1070", "SS", 120),
    ("A1070", "A1080", "SS", 80),
    ("A1060", "A1080", "FF", 16),
    ("A1080", "A1090", "SS", 40),
    ("A1080", "A1100", "FS", 0),
    ("A1070", "A1110", "FS", 0),
    ("A1090", "A1120", "SS", 24),
    ("A1110", "A1130", "FS", 0),
    ("A1100", "A1140", "FS", 0),
    ("A1120", "A1140", "FS", 0),
    ("A1130", "A1140", "SS", 16),
    ("A1140", "A1150", "FF", 0),
]
DATA_DATE = dt.datetime(2026, 8, 31, 17, 0)
WBS_NAMES = {"PRE": "Preconstruction and demolition", "L1": "Level 1 fit-out", "CLOSE": "Closeout"}


def add_workdays(start: dt.date, days: int) -> dt.date:
    d, n = start, 0
    while n < days - 1:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return d


def schedule_rows():
    out = []
    for aid, name, wbs, kind, start, days, pct in ACTIVITIES:
        s = dt.datetime.combine(start, dt.time(8, 0))
        f = s if days == 0 else dt.datetime.combine(add_workdays(start, days), dt.time(17, 0))
        done = pct == 100
        started = pct > 0
        out.append(
            {
                "id": aid,
                "name": name,
                "wbs": wbs,
                "kind": kind,
                "start": s,
                "finish": f,
                "hours": days * 8,
                "remaining": 0 if done else round(days * 8 * (100 - pct) / 100),
                "pct": pct,
                "act_start": s if started else None,
                "act_finish": f if done else None,
            }
        )
    return out


def write_xer(path: Path, rows) -> None:
    def d(x):
        return x.strftime("%Y-%m-%d %H:%M") if x else ""

    lines = ["ERMHDR\t19.12\t2026-08-31\tProject\tadmin\tSample\tdbxDatabaseNoName\tProject Management\tUSD"]
    lines += ["%T\tPROJECT", "%F\tproj_id\tproj_short_name\tlast_recalc_date\tplan_start_date", f"%R\t4501\tJ-1104-FITOUT\t{d(DATA_DATE)}\t2026-02-02 08:00"]
    lines += ["%T\tCALENDAR", "%F\tclndr_id\tclndr_name\tday_hr_cnt", "%R\t71\tStandard 5-day\t8"]
    lines += ["%T\tPROJWBS", "%F\twbs_id\tproj_id\tparent_wbs_id\twbs_short_name\twbs_name\tproj_node_flag", "%R\t900\t4501\t\tJ-1104-FITOUT\tRiverside Clinic Fit-out\tY"]
    wbs_ids = {}
    for n, (code, name) in enumerate(WBS_NAMES.items(), start=901):
        wbs_ids[code] = str(n)
        lines.append(f"%R\t{n}\t4501\t900\t{code}\t{name}\tN")
    task_fields = [
        "task_id", "proj_id", "wbs_id", "clndr_id", "task_code", "task_name", "task_type", "status_code",
        "phys_complete_pct", "target_drtn_hr_cnt", "remain_drtn_hr_cnt", "act_start_date", "act_end_date",
        "early_start_date", "early_end_date", "target_start_date", "target_end_date", "total_float_hr_cnt",
    ]
    lines += ["%T\tTASK", "%F\t" + "\t".join(task_fields)]
    task_ids = {}
    for n, r in enumerate(rows, start=10001):
        task_ids[r["id"]] = str(n)
        kind = {"task": "TT_Task", "milestone": "TT_FinMile" if r["id"] == "A1150" else "TT_Mile"}[r["kind"]]
        status = "TK_Complete" if r["act_finish"] else ("TK_Active" if r["act_start"] else "TK_NotStart")
        early_s = None if r["act_start"] else r["start"]
        early_f = None if r["act_finish"] else r["finish"]
        cells = [
            str(n), "4501", wbs_ids[r["wbs"]], "71", r["id"], r["name"], kind, status, f"{r['pct']}",
            f"{r['hours']}", f"{r['remaining']}", d(r["act_start"]), d(r["act_finish"]), d(early_s), d(early_f),
            d(r["start"]), d(r["finish"]), "0",
        ]
        lines.append("%R\t" + "\t".join(cells))
    lines += ["%T\tTASKPRED", "%F\ttask_pred_id\ttask_id\tpred_task_id\tproj_id\tpred_proj_id\tpred_type\tlag_hr_cnt"]
    for n, (p, s, t, lag) in enumerate(LINKS, start=20001):
        lines.append(f"%R\t{n}\t{task_ids[s]}\t{task_ids[p]}\t4501\t4501\tPR_{t}\t{lag}")
    lines += ["%T\tACTVCODE", "%F\tactv_code_id\tactv_code_type_id\tshort_name\tactv_code_name", "%R\t1\t1\tL1\tLevel 1", "%E"]
    path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")


def write_mspdi(path: Path, rows, drop_link: tuple | None = None, lag_change: tuple | None = None) -> None:
    def d(x):
        return x.strftime("%Y-%m-%dT%H:%M:%S") if x else None

    type_code = {"FF": 0, "FS": 1, "SF": 2, "SS": 3}
    x = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', '<Project xmlns="http://schemas.microsoft.com/project">']
    x += ["  <Name>J-1104-FITOUT.xml</Name>", "  <Title>J-1104-FITOUT</Title>", f"  <StatusDate>{d(DATA_DATE)}</StatusDate>"]
    x += ["  <MinutesPerDay>480</MinutesPerDay>", "  <CalendarUID>1</CalendarUID>"]
    x += ["  <Calendars>", "    <Calendar><UID>1</UID><Name>Standard 5-day</Name></Calendar>", "  </Calendars>", "  <Tasks>"]
    x.append("    <Task><UID>0</UID><ID>0</ID><Name>J-1104-FITOUT</Name><Summary>1</Summary></Task>")
    uid = 0
    uids: dict[str, int] = {}
    tasks: list[str] = []
    for w_index, (code, wname) in enumerate(WBS_NAMES.items(), start=1):
        uid += 1
        members = [r for r in rows if r["wbs"] == code]
        tasks.append(
            f"    <Task><UID>{uid}</UID><ID>{uid}</ID><Name>{escape(wname)}</Name><WBS>{w_index}</WBS>"
            f"<OutlineNumber>{w_index}</OutlineNumber><Summary>1</Summary><Milestone>0</Milestone>"
            f"<Start>{d(min(r['start'] for r in members))}</Start><Finish>{d(max(r['finish'] for r in members))}</Finish></Task>"
        )
        for m_index, r in enumerate(members, start=1):
            uid += 1
            uids[r["id"]] = uid
            r["_outline"] = f"{w_index}.{m_index}"
            r["_uid"] = uid
    for r in rows:
        parts = [
            f"<UID>{r['_uid']}</UID>", f"<ID>{r['_uid']}</ID>", f"<Name>{escape(r['name'])}</Name>",
            f"<WBS>{r['_outline']}</WBS>", f"<OutlineNumber>{r['_outline']}</OutlineNumber>",
            "<Summary>0</Summary>", f"<Milestone>{1 if r['kind'] == 'milestone' else 0}</Milestone>",
            f"<Start>{d(r['start'])}</Start>", f"<Finish>{d(r['finish'])}</Finish>",
            f"<Duration>PT{r['hours']}H0M0S</Duration>", f"<RemainingDuration>PT{r['remaining']}H0M0S</RemainingDuration>",
            f"<PercentComplete>{r['pct']}</PercentComplete>",
        ]
        if r["act_start"]:
            parts.append(f"<ActualStart>{d(r['act_start'])}</ActualStart>")
        if r["act_finish"]:
            parts.append(f"<ActualFinish>{d(r['act_finish'])}</ActualFinish>")
        parts.append("<CalendarUID>-1</CalendarUID>")
        for p, s, t, lag in LINKS:
            if s != r["id"] or (p, s) == drop_link:
                continue
            if lag_change and (p, s) == lag_change[:2]:
                lag = lag_change[2]
            parts.append(
                f"<PredecessorLink><PredecessorUID>{uids[p]}</PredecessorUID><Type>{type_code[t]}</Type>"
                f"<LinkLag>{lag * 600}</LinkLag><LagFormat>7</LagFormat></PredecessorLink>"
            )
        tasks.append("    <Task>" + "".join(parts) + "</Task>")
    x += tasks + ["  </Tasks>", "</Project>"]
    path.write_text("\n".join(x) + "\n", encoding="utf-8")


def main() -> None:
    schema = load_schema()
    clean = build()
    broken = break_it(clean)
    for name, data in (("clean", clean), ("broken", broken)):
        for record in RECORDS:
            write_rows(SAMPLES / name / f"{record}.csv", record, data[record], schema)
    legacy_export(clean, "J-1104")
    vendor_export()
    sched = SAMPLES / "schedules"
    sched.mkdir(parents=True, exist_ok=True)
    rows = schedule_rows()
    write_xer(sched / "fitout.xer", rows)
    write_mspdi(sched / "fitout.xml", rows)
    # a conversion that lost one link on the critical path and turned a 10-day lag into a 1-day lag
    write_mspdi(sched / "fitout-lossy-conversion.xml", rows, drop_link=("A1060", "A1080"), lag_change=("A1060", "A1070", 16))
    print(f"samples written to {SAMPLES}")


if __name__ == "__main__":
    main()
