"""A neutral schedule model: the parts of a CPM schedule that have to survive a conversion."""

from __future__ import annotations

import csv
import datetime as dt
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

ACTIVITY_TYPES = ("task", "milestone", "level_of_effort", "summary")
RELATIONSHIP_TYPES = ("FS", "SS", "FF", "SF")


@dataclass
class Activity:
    activity_id: str
    name: str
    type: str = "task"
    wbs: str = ""
    start: dt.datetime | None = None
    finish: dt.datetime | None = None
    actual_start: dt.datetime | None = None
    actual_finish: dt.datetime | None = None
    duration_hours: float | None = None
    remaining_hours: float | None = None
    percent_complete: float | None = None
    total_float_hours: float | None = None
    calendar: str = ""


@dataclass
class Relationship:
    predecessor_id: str
    successor_id: str
    type: str = "FS"
    lag_hours: float = 0.0


@dataclass
class Schedule:
    source: str
    project: str = ""
    data_date: dt.datetime | None = None
    activities: list[Activity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    calendars: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def by_id(self) -> dict[str, Activity]:
        return {a.activity_id: a for a in self.activities}

    def write_csv(self, folder: Path) -> tuple[Path, Path]:
        folder.mkdir(parents=True, exist_ok=True)
        paths = folder / "activities.csv", folder / "relationships.csv"
        for path, rows, cls in ((paths[0], self.activities, Activity), (paths[1], self.relationships, Relationship)):
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow([f.name for f in fields(cls)])
                for row in rows:
                    writer.writerow([_cell(v) for v in asdict(row).values()])
        return paths


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, dt.datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)
