"""Tie migrated job data out to the old system's own reports, to the cent.

The rule this module enforces: a migration is finished when, for every open job, each control
figure printed by the old system at cutover equals the same figure recomputed from the migrated
records. Not "close", not "within tolerance" -- equal. A difference of one cent is a symptom; the
cause is usually a duplicated line, a dropped credit or a change order in the wrong status.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from .schema import Issue, Table, read_folder

ZERO = Decimal("0.00")

METRICS = {
    "contract_value": "Original contract plus approved owner change orders",
    "revised_budget": "Original budget plus approved budget changes, all lines",
    "committed_cost": "Original value of non-void commitments plus their approved change orders",
    "cost_to_date": "All cost transactions posted on or before the cutover date",
    "billed_to_date": "Work completed on submitted and approved pay applications",
    "retainage_receivable": "Retainage held by the owner less retainage released, non-draft applications",
    "retainage_payable": "Retainage withheld from vendors less retainage released to them",
}

CHECKS = {
    "R01": ("error", "Duplicate key: the same record appears twice"),
    "R02": ("error", "A value is missing, malformed or not an allowed option"),
    "R03": ("error", "A reference points at a job, cost code, vendor or commitment that is not in the migration"),
    "R04": ("warning", "Cost is posted to a job, cost code and cost type with no budget line"),
    "R05": ("error", "A transaction or pay application is dated after the cutover date"),
    "R06": ("error", "The owner has released more retainage on a job than was held"),
    "R07": ("warning", "A commitment has been invoiced beyond its committed value"),
    "R08": ("warning", "A closed job still has open commitments"),
    "R09": ("error", "A vendor record carries more than the last four digits of a tax ID"),
    "R10": ("error", "A commitment change order has no commitment, or its commitment is on another job"),
    "R11": ("info", "Pending change orders exist: they are not in contract value, so check they migrated as pending"),
    "R12": ("error", "More retainage has been released to a vendor than was withheld from it"),
    "T01": ("error", "A recomputed figure does not equal the old system's control total"),
    "T02": ("error", "A job is in the control totals but not in the migration, or an open job has no control totals"),
    "T03": ("error", "The control totals are incomplete or carry more than one cutover date"),
}


@dataclass
class TieOut:
    job_id: str
    metric: str
    control: Decimal
    migrated: Decimal
    source_report: str

    @property
    def difference(self) -> Decimal:
        return self.migrated - self.control

    @property
    def ties(self) -> bool:
        return self.difference == ZERO


@dataclass
class Result:
    folder: Path
    as_of: dt.date | None
    issues: list[Issue] = field(default_factory=list)
    tie_outs: list[TieOut] = field(default_factory=list)
    jobs: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def passed(self) -> bool:
        return not self.errors

    def checks_failed(self) -> set[str]:
        return {i.check for i in self.errors}


def _sum(values) -> Decimal:
    total = ZERO
    for v in values:
        if v is not None:
            total += v
    return total


def _rows(table: Table):
    return zip(table.lines, table.rows)


def compute_metrics(tables: dict[str, Table], as_of: dt.date | None) -> dict[str, dict[str, Decimal]]:
    """Recompute every control metric per job from the migrated records alone."""
    out: dict[str, dict[str, Decimal]] = defaultdict(lambda: {m: ZERO for m in METRICS})

    for row in tables["jobs"].rows:
        if row["job_id"]:
            out[row["job_id"]]["contract_value"] += row["original_contract"] or ZERO

    commitments = {r["commitment_id"]: r for r in tables["commitments"].rows if r["commitment_id"]}
    for row in tables["change_orders"].rows:
        if row["status"] != "approved" or not row["job_id"]:
            continue
        if row["level"] == "owner":
            out[row["job_id"]]["contract_value"] += row["amount"] or ZERO
        elif row["level"] == "commitment":
            parent = commitments.get(row["commitment_id"])
            if parent and parent["status"] != "void":
                out[row["job_id"]]["committed_cost"] += row["amount"] or ZERO

    for row in tables["budgets"].rows:
        if row["job_id"]:
            out[row["job_id"]]["revised_budget"] += (row["original_budget"] or ZERO) + (row["approved_changes"] or ZERO)

    # Every row counts, duplicates included: a commitment loaded twice is committed twice in the new system.
    for row in tables["commitments"].rows:
        if row["status"] != "void" and row["job_id"]:
            out[row["job_id"]]["committed_cost"] += row["original_value"] or ZERO

    for row in tables["cost_transactions"].rows:
        if not row["job_id"]:
            continue
        if as_of is None or (row["posted_date"] and row["posted_date"] <= as_of):
            out[row["job_id"]]["cost_to_date"] += row["amount"] or ZERO
            out[row["job_id"]]["retainage_payable"] += row["retainage_withheld"] or ZERO

    for row in tables["billings"].rows:
        if row["status"] == "draft" or not row["job_id"]:
            continue
        if as_of is not None and row["period_end"] and row["period_end"] > as_of:
            continue
        m = out[row["job_id"]]
        m["billed_to_date"] += row["work_completed"] or ZERO
        m["retainage_receivable"] += (row["retainage_held"] or ZERO) - (row["retainage_released"] or ZERO)

    return dict(out)


def _integrity(tables: dict[str, Table], as_of: dt.date | None, issues: list[Issue]) -> None:
    jobs = {r["job_id"]: r for r in tables["jobs"].rows if r["job_id"]}
    codes = {r["cost_code"] for r in tables["cost_codes"].rows if r["cost_code"]}
    vendors = {r["vendor_id"] for r in tables["vendors"].rows if r["vendor_id"]}
    commitments = {r["commitment_id"]: r for r in tables["commitments"].rows if r["commitment_id"]}
    budget_lines = {(r["job_id"], r["cost_code"], r["cost_type"]) for r in tables["budgets"].rows}

    def ref(record: str, line: int, job: str, kind: str, value: Any, known) -> None:
        if value and value not in known:
            issues.append(Issue("R03", "error", f"{kind} {value!r} is not in the migration", record, line, job or ""))

    for line, r in _rows(tables["budgets"]):
        ref("budgets", line, r["job_id"], "job", r["job_id"], jobs)
        ref("budgets", line, r["job_id"], "cost code", r["cost_code"], codes)

    for line, r in _rows(tables["commitments"]):
        ref("commitments", line, r["job_id"], "job", r["job_id"], jobs)
        ref("commitments", line, r["job_id"], "vendor", r["vendor_id"], vendors)

    for line, r in _rows(tables["change_orders"]):
        ref("change_orders", line, r["job_id"], "job", r["job_id"], jobs)
        ref("change_orders", line, r["job_id"], "cost code", r["cost_code"], codes)
        if r["level"] == "commitment":
            parent = commitments.get(r["commitment_id"])
            if not r["commitment_id"]:
                issues.append(Issue("R10", "error", "commitment change order has no commitment_id", "change_orders", line, r["job_id"] or ""))
            elif parent is None:
                ref("change_orders", line, r["job_id"], "commitment", r["commitment_id"], commitments)
            elif parent["job_id"] != r["job_id"]:
                issues.append(
                    Issue(
                        "R10",
                        "error",
                        f"commitment {r['commitment_id']} is on job {parent['job_id']}, not {r['job_id']}",
                        "change_orders",
                        line,
                        r["job_id"] or "",
                    )
                )

    unbudgeted: dict[tuple, int] = {}
    invoiced: dict[str, Decimal] = defaultdict(lambda: ZERO)
    withheld: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for line, r in _rows(tables["cost_transactions"]):
        job = r["job_id"] or ""
        ref("cost_transactions", line, job, "job", r["job_id"], jobs)
        ref("cost_transactions", line, job, "cost code", r["cost_code"], codes)
        ref("cost_transactions", line, job, "vendor", r["vendor_id"], vendors)
        ref("cost_transactions", line, job, "commitment", r["commitment_id"], commitments)
        if as_of and r["posted_date"] and r["posted_date"] > as_of:
            issues.append(
                Issue("R05", "error", f"posted {r['posted_date']} is after the cutover date {as_of}", "cost_transactions", line, job)
            )
        key = (r["job_id"], r["cost_code"], r["cost_type"])
        if r["cost_code"] in codes and r["job_id"] in jobs and key not in budget_lines and key not in unbudgeted:
            unbudgeted[key] = line
        if r["commitment_id"]:
            invoiced[r["commitment_id"]] += r["amount"] or ZERO
            withheld[r["commitment_id"]] += r["retainage_withheld"] or ZERO

    for (job, code, ctype), line in unbudgeted.items():
        issues.append(
            Issue("R04", "warning", f"cost posted to {code} / {ctype} with no budget line", "cost_transactions", line, job)
        )

    approved_changes: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for r in tables["change_orders"].rows:
        if r["level"] == "commitment" and r["status"] == "approved" and r["commitment_id"]:
            approved_changes[r["commitment_id"]] += r["amount"] or ZERO
    for cid, total in sorted(invoiced.items()):
        parent = commitments.get(cid)
        if not parent or parent["status"] == "void":
            continue
        committed = (parent["original_value"] or ZERO) + approved_changes[cid]
        if total > committed:
            issues.append(
                Issue(
                    "R07",
                    "warning",
                    f"commitment {cid} invoiced {total:,.2f} against {committed:,.2f} committed: a missing change order, or cost coded to the wrong commitment",
                    "commitments",
                    0,
                    parent["job_id"] or "",
                )
            )
    for cid, total in sorted(withheld.items()):
        if total < ZERO:
            job = commitments[cid]["job_id"] if cid in commitments else ""
            issues.append(
                Issue("R12", "error", f"commitment {cid}: {-total:,.2f} more retainage released than withheld", "commitments", 0, job or "")
            )

    for line, r in _rows(tables["commitments"]):
        parent_job = jobs.get(r["job_id"])
        if parent_job and parent_job["status"] == "closed" and r["status"] == "open":
            issues.append(
                Issue("R08", "warning", f"commitment {r['commitment_id']} is open on a closed job", "commitments", line, r["job_id"])
            )

    for line, r in _rows(tables["vendors"]):
        tin = (r["tin_last4"] or "").replace("-", "").replace(" ", "")
        if len(tin) > 4:
            issues.append(
                Issue(
                    "R09",
                    "error",
                    f"vendor {r['vendor_id']} carries a full tax ID; keep the last four digits only and remove this file from wherever it has been",
                    "vendors",
                    line,
                )
            )

    held: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for line, r in _rows(tables["billings"]):
        job = r["job_id"] or ""
        ref("billings", line, job, "job", r["job_id"], jobs)
        if as_of and r["period_end"] and r["period_end"] > as_of and r["status"] != "draft":
            issues.append(Issue("R05", "error", f"pay application period {r['period_end']} is after the cutover date", "billings", line, job))
        if r["status"] != "draft":
            held[job] += (r["retainage_held"] or ZERO) - (r["retainage_released"] or ZERO)
    for job, balance in sorted(held.items()):
        if balance < ZERO:
            issues.append(Issue("R06", "error", f"owner has released {-balance:,.2f} more retainage than was held", "billings", 0, job))

    pending: dict[str, list[Decimal]] = defaultdict(list)
    for r in tables["change_orders"].rows:
        if r["status"] == "pending" and r["job_id"]:
            pending[r["job_id"]].append(r["amount"] or ZERO)
    for job, amounts in sorted(pending.items()):
        issues.append(
            Issue(
                "R11",
                "info",
                f"{len(amounts)} pending change order(s) worth {_sum(amounts):,.2f}; confirm they are pending in the new system too",
                "change_orders",
                0,
                job,
            )
        )


def reconcile(folder: Path) -> Result:
    tables, issues = read_folder(folder)
    for record in ("jobs", "control_totals"):
        if not tables[record].present:
            issues.append(Issue("T03", "error", f"{record}.csv is missing; nothing can be signed off without it", record))

    controls = tables["control_totals"].rows
    dates = {r["as_of"] for r in controls if r["as_of"]}
    as_of = min(dates) if dates else None
    if len(dates) > 1:
        issues.append(
            Issue("T03", "error", f"control totals carry {len(dates)} different cutover dates: {', '.join(sorted(map(str, dates)))}", "control_totals")
        )

    _integrity(tables, as_of, issues)
    metrics = compute_metrics(tables, as_of)
    jobs = {r["job_id"]: r for r in tables["jobs"].rows if r["job_id"]}

    result = Result(folder, as_of, issues, [], jobs)
    seen: dict[str, set[str]] = defaultdict(set)
    for r in controls:
        job, metric = r["job_id"], r["metric"]
        if not job or not metric or r["value"] is None:
            continue
        if job not in jobs:
            issues.append(Issue("T02", "error", f"job {job} has control totals but is not in the migration", "control_totals", 0, job))
            continue
        seen[job].add(metric)
        migrated = metrics.get(job, {}).get(metric, ZERO)
        tie = TieOut(job, metric, r["value"], migrated, r["source_report"] or "")
        result.tie_outs.append(tie)
        if not tie.ties:
            issues.append(
                Issue(
                    "T01",
                    "error",
                    f"{metric}: old system {tie.control:,.2f}, migrated {tie.migrated:,.2f}, difference {tie.difference:+,.2f}",
                    "control_totals",
                    0,
                    job,
                )
            )

    for job, row in sorted(jobs.items()):
        if row["status"] in ("open", "warranty") and job not in seen:
            issues.append(Issue("T02", "error", f"open job {job} has no control totals, so it cannot be signed off", "control_totals", 0, job))
        elif job in seen:
            missing = [m for m in METRICS if m not in seen[job]]
            if missing:
                issues.append(Issue("T03", "error", f"no control total for {', '.join(missing)}", "control_totals", 0, job))

    order = {"error": 0, "warning": 1, "info": 2}
    issues.sort(key=lambda i: (order[i.severity], i.job_id, i.check, i.record, i.line))
    result.tie_outs.sort(key=lambda t: (t.job_id, list(METRICS).index(t.metric)))
    return result
