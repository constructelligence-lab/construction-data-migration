"""Reports for a reconciliation: a terminal summary, a sign-off document and JSON for other tools."""

from __future__ import annotations

import json
from collections import defaultdict

from .reconcile import CHECKS, METRICS, Result


def text_report(result: Result) -> str:
    lines = [f"Reconciliation of {result.folder}", f"Cutover date: {result.as_of or 'unknown'}", ""]
    by_job = defaultdict(list)
    for t in result.tie_outs:
        by_job[t.job_id].append(t)
    for job, ties in by_job.items():
        name = result.jobs.get(job, {}).get("job_name") or ""
        lines.append(f"{job}  {name}")
        for t in ties:
            mark = "ok  " if t.ties else "FAIL"
            lines.append(f"  {mark} {t.metric:<22} {t.control:>16,.2f} {t.migrated:>16,.2f} {t.difference:>+14,.2f}")
        lines.append("")
    counts = {s: sum(1 for i in result.issues if i.severity == s) for s in ("error", "warning", "info")}
    for issue in result.issues:
        where = issue.where()
        job = f"[{issue.job_id}] " if issue.job_id else ""
        lines.append(f"{issue.severity.upper():<7} {issue.check} {job}{issue.message}" + (f"  ({where})" if where else ""))
    lines.append("")
    verdict = "PASS: every control total ties out" if result.passed else "FAIL: do not cut over"
    lines.append(f"{verdict}  ({counts['error']} errors, {counts['warning']} warnings, {counts['info']} notes)")
    return "\n".join(lines) + "\n"


def markdown_report(result: Result) -> str:
    """A sign-off document the controller, the PM lead and the data owner can each put a name to."""
    out = [
        "# Migration reconciliation sign-off",
        "",
        f"**Cutover date:** {result.as_of or 'unknown'}  ",
        f"**Result:** {'PASS: every control total ties out to the cent' if result.passed else 'FAIL: differences below must be resolved before cutover'}",
        "",
        "Each figure below was printed by the old system's own report at cutover (the control) and recomputed",
        "independently from the migrated records. The difference must be zero.",
        "",
    ]
    by_job = defaultdict(list)
    for t in result.tie_outs:
        by_job[t.job_id].append(t)
    for job, ties in by_job.items():
        name = result.jobs.get(job, {}).get("job_name") or ""
        out += [f"## {job} {name}".rstrip(), "", "| Figure | Old system | Migrated | Difference | Source report |", "| --- | ---: | ---: | ---: | --- |"]
        for t in ties:
            flag = "" if t.ties else " **✗**"
            out.append(
                f"| {METRICS[t.metric]} | {t.control:,.2f} | {t.migrated:,.2f} | {t.difference:+,.2f}{flag} | {t.source_report} |"
            )
        out.append("")
    if result.issues:
        out += ["## Findings", "", "| Severity | Check | Job | Finding | Where |", "| --- | --- | --- | --- | --- |"]
        for i in result.issues:
            out.append(f"| {i.severity} | {i.check} | {i.job_id} | {i.message} | {i.where()} |")
        out += ["", "| Check | Meaning |", "| --- | --- |"]
        for check in sorted({i.check for i in result.issues}):
            out.append(f"| {check} | {CHECKS[check][1]} |")
        out.append("")
    out += [
        "## Sign-off",
        "",
        "| Role | Name | Signature | Date |",
        "| --- | --- | --- | --- |",
        "| Controller |  |  |  |",
        "| Project management lead |  |  |  |",
        "| Migration data owner |  |  |  |",
        "",
        "Attach the printed control reports named above. A sign-off without them is an opinion.",
        "",
    ]
    return "\n".join(out)


def json_report(result: Result) -> str:
    return json.dumps(
        {
            "folder": str(result.folder),
            "as_of": str(result.as_of) if result.as_of else None,
            "passed": result.passed,
            "tie_outs": [
                {
                    "job_id": t.job_id,
                    "metric": t.metric,
                    "control": str(t.control),
                    "migrated": str(t.migrated),
                    "difference": str(t.difference),
                    "source_report": t.source_report,
                }
                for t in result.tie_outs
            ],
            "issues": [
                {"check": i.check, "severity": i.severity, "job_id": i.job_id, "record": i.record, "line": i.line, "message": i.message}
                for i in result.issues
            ],
        },
        indent=2,
    )
