"""Read a Microsoft Project XML file (MSPDI) into the neutral schedule model.

Microsoft documents the format publicly as Project XML Data Interchange. This reader takes the
task list, the predecessor links, calendars and the status date. Two conversions matter:

* durations are ISO 8601 (``PT16H0M0S``) and are converted to working hours;
* link lag (``LinkLag``) is stored in tenths of a minute, so 4800 means 8 hours.

Microsoft Project has no P6-style activity ID. By default a task is identified by its unique ID;
``id_source`` can use the row ID, the WBS code, or the task name instead, so that a schedule
converted from P6 can be matched back to its source.
"""

from __future__ import annotations

import datetime as dt
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .model import Activity, Relationship, Schedule

NS = "{http://schemas.microsoft.com/project}"
LINK_TYPES = {"0": "FF", "1": "FS", "2": "SF", "3": "SS"}
PERCENT_LAG_FORMATS = {"19", "20"}
DURATION = re.compile(r"^-?P(?:(\d+(?:\.\d+)?)D)?(?:T(?:(\d+(?:\.\d+)?)H)?(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?)?$")


def _t(el: ET.Element, name: str) -> str:
    child = el.find(NS + name)
    return (child.text or "").strip() if child is not None else ""


def _date(text: str) -> dt.datetime | None:
    if not text:
        return None
    return dt.datetime.strptime(text[:19], "%Y-%m-%dT%H:%M:%S")


def duration_hours(text: str, hours_per_day: float = 8.0) -> float | None:
    if not text:
        return None
    m = DURATION.match(text)
    if not m:
        raise ValueError(f"unrecognised duration {text!r}")
    days, hours, minutes, seconds = (float(g) if g else 0.0 for g in m.groups())
    total = days * hours_per_day + hours + minutes / 60 + seconds / 3600
    return -total if text.startswith("-") else total


def read_mspdi(path, id_source: str = "uid") -> Schedule:
    path = Path(path)
    root = ET.parse(path).getroot()
    if root.tag != NS + "Project":
        raise ValueError(f"{path.name} is not Microsoft Project XML (root element is {root.tag})")
    schedule = Schedule(source=path.name)
    schedule.project = _t(root, "Title") or _t(root, "Name")
    schedule.data_date = _date(_t(root, "StatusDate"))
    minutes_per_day = _t(root, "MinutesPerDay")
    hours_per_day = float(minutes_per_day) / 60 if minutes_per_day else 8.0

    calendars = root.find(NS + "Calendars")
    if calendars is not None:
        for cal in calendars.findall(NS + "Calendar"):
            schedule.calendars[_t(cal, "UID")] = _t(cal, "Name")
    default_calendar = schedule.calendars.get(_t(root, "CalendarUID"), "")

    uid_to_id: dict[str, str] = {}
    pending_links: list[tuple[str, ET.Element]] = []
    tasks = root.find(NS + "Tasks")
    for task in tasks.findall(NS + "Task") if tasks is not None else []:
        uid = _t(task, "UID")
        if uid == "0" or _t(task, "IsNull") == "1":
            continue
        key = {"uid": uid, "id": _t(task, "ID"), "wbs": _t(task, "WBS"), "name": _t(task, "Name")}[id_source]
        uid_to_id[uid] = key
        if _t(task, "Summary") == "1":
            kind = "summary"
        elif _t(task, "Milestone") == "1":
            kind = "milestone"
        else:
            kind = "task"
        pct = _t(task, "PercentComplete")
        cal_uid = _t(task, "CalendarUID")
        schedule.activities.append(
            Activity(
                activity_id=key,
                name=_t(task, "Name"),
                type=kind,
                wbs=_t(task, "WBS") or _t(task, "OutlineNumber"),
                start=_date(_t(task, "Start")),
                finish=_date(_t(task, "Finish")),
                actual_start=_date(_t(task, "ActualStart")),
                actual_finish=_date(_t(task, "ActualFinish")),
                duration_hours=duration_hours(_t(task, "Duration"), hours_per_day),
                remaining_hours=duration_hours(_t(task, "RemainingDuration"), hours_per_day),
                percent_complete=float(pct) if pct else None,
                total_float_hours=None,
                calendar=schedule.calendars.get(cal_uid, "") if cal_uid and cal_uid != "-1" else default_calendar,
            )
        )
        for link in task.findall(NS + "PredecessorLink"):
            pending_links.append((uid, link))

    for succ_uid, link in pending_links:
        pred_uid = _t(link, "PredecessorUID")
        if pred_uid not in uid_to_id:
            schedule.warnings.append(f"link to predecessor UID {pred_uid} points outside this file")
            continue
        lag_format = _t(link, "LagFormat")
        if lag_format in PERCENT_LAG_FORMATS:
            schedule.warnings.append(
                f"link {uid_to_id[pred_uid]} -> {uid_to_id[succ_uid]} uses a percentage lag; check it by hand"
            )
        lag = _t(link, "LinkLag")
        schedule.relationships.append(
            Relationship(
                uid_to_id[pred_uid],
                uid_to_id[succ_uid],
                LINK_TYPES.get(_t(link, "Type") or "1", "FS"),
                float(lag) / 600 if lag else 0.0,
            )
        )
    return schedule
