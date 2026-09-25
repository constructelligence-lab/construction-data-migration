"""Read a Primavera P6 XER export into the neutral schedule model.

XER is a tab-delimited text export. Each table starts with ``%T <name>``, its field names follow on
a ``%F`` line, each row is a ``%R`` line, and the file ends with ``%E``. This reader uses only
what is visible in the file itself and reads the tables a conversion check needs: PROJECT,
CALENDAR, PROJWBS, TASK and TASKPRED. Everything else is ignored, and says so.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from .model import Activity, Relationship, Schedule

TASK_TYPES = {
    "TT_Task": "task",
    "TT_Rsrc": "task",
    "TT_Mile": "milestone",
    "TT_FinMile": "milestone",
    "TT_LOE": "level_of_effort",
    "TT_WBS": "summary",
}
REL_TYPES = {"PR_FS": "FS", "PR_SS": "SS", "PR_FF": "FF", "PR_SF": "SF"}
READ = {"PROJECT", "CALENDAR", "PROJWBS", "TASK", "TASKPRED"}


def parse_tables(text: str) -> dict[str, list[dict[str, str]]]:
    tables: dict[str, list[dict[str, str]]] = {}
    current: str | None = None
    columns: list[str] = []
    for raw in text.splitlines():
        parts = raw.rstrip("\r\n").split("\t")
        tag = parts[0]
        if tag == "%T":
            current = parts[1].strip()
            tables.setdefault(current, [])
        elif tag == "%F":
            columns = parts[1:]
        elif tag == "%R" and current is not None:
            cells = parts[1:] + [""] * (len(columns) - len(parts) + 1)
            tables[current].append(dict(zip(columns, cells)))
        elif tag == "%E":
            break
    return tables


def _read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def _date(text: str) -> dt.datetime | None:
    text = (text or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"unrecognised XER date {text!r}")


def _num(text: str) -> float | None:
    text = (text or "").strip()
    return float(text) if text else None


def read_xer(path) -> Schedule:
    path = Path(path)
    text = _read_text(path)
    if not text.startswith("ERMHDR"):
        raise ValueError(f"{path.name} does not start with an ERMHDR line; it is not an XER export")
    tables = parse_tables(text)
    schedule = Schedule(source=path.name)

    projects = tables.get("PROJECT", [])
    if projects:
        schedule.project = projects[0].get("proj_short_name", "")
        schedule.data_date = _date(projects[0].get("last_recalc_date", ""))
    if len(projects) > 1:
        schedule.warnings.append(f"{len(projects)} projects in one file; activity IDs are prefixed with the project")

    for cal in tables.get("CALENDAR", []):
        schedule.calendars[cal.get("clndr_id", "")] = cal.get("clndr_name", "")

    wbs_rows = {w["wbs_id"]: w for w in tables.get("PROJWBS", []) if w.get("wbs_id")}

    def wbs_path(wbs_id: str) -> str:
        names: list[str] = []
        seen: set[str] = set()
        while wbs_id in wbs_rows and wbs_id not in seen:
            seen.add(wbs_id)
            node = wbs_rows[wbs_id]
            if node.get("proj_node_flag") == "Y":
                break
            names.append(node.get("wbs_short_name", ""))
            wbs_id = node.get("parent_wbs_id", "")
        return ".".join(reversed(names))

    project_names = {p["proj_id"]: p.get("proj_short_name", "") for p in projects}
    multi = len(projects) > 1
    by_task_id: dict[str, str] = {}
    for t in tables.get("TASK", []):
        code = t.get("task_code", "")
        if multi:
            code = f"{project_names.get(t.get('proj_id', ''), t.get('proj_id', ''))}:{code}"
        by_task_id[t["task_id"]] = code
        actual_start, actual_finish = _date(t.get("act_start_date", "")), _date(t.get("act_end_date", ""))
        pct = _num(t.get("phys_complete_pct", ""))
        schedule.activities.append(
            Activity(
                activity_id=code,
                name=t.get("task_name", ""),
                type=TASK_TYPES.get(t.get("task_type", ""), "task"),
                wbs=wbs_path(t.get("wbs_id", "")),
                start=actual_start or _date(t.get("early_start_date", "")) or _date(t.get("target_start_date", "")),
                finish=actual_finish or _date(t.get("early_end_date", "")) or _date(t.get("target_end_date", "")),
                actual_start=actual_start,
                actual_finish=actual_finish,
                duration_hours=_num(t.get("target_drtn_hr_cnt", "")),
                remaining_hours=_num(t.get("remain_drtn_hr_cnt", "")),
                percent_complete=pct,
                total_float_hours=_num(t.get("total_float_hr_cnt", "")),
                calendar=schedule.calendars.get(t.get("clndr_id", ""), t.get("clndr_id", "")),
            )
        )
        if t.get("task_type", "") not in TASK_TYPES:
            schedule.warnings.append(f"activity {code}: unknown task_type {t.get('task_type')!r}, read as a task")

    for p in tables.get("TASKPRED", []):
        pred, succ = by_task_id.get(p.get("pred_task_id", "")), by_task_id.get(p.get("task_id", ""))
        if pred is None or succ is None:
            schedule.warnings.append(
                f"relationship {p.get('task_pred_id', '?')} points outside this file (external link); it will not survive a conversion"
            )
            continue
        schedule.relationships.append(
            Relationship(pred, succ, REL_TYPES.get(p.get("pred_type", ""), "FS"), _num(p.get("lag_hr_cnt", "")) or 0.0)
        )

    ignored = sorted(set(tables) - READ)
    if ignored:
        schedule.warnings.append(
            f"not read (check these by hand after any conversion): {', '.join(ignored)}"
        )
    return schedule
