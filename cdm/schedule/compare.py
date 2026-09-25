"""Check that a schedule survived a conversion: same activities, same logic, same dates.

Converting between P6 and Microsoft Project (or into any new scheduling tool) is where logic
quietly disappears. A relationship dropped from the critical path moves the finish date and
nobody notices until the next update. This check compares the two files activity by activity
and link by link, and fails on anything that did not come across.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .model import Schedule


@dataclass
class Comparison:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


def _key(activity, match: str) -> str:
    return activity.name.strip().lower() if match == "name" else activity.activity_id


def compare(source: Schedule, target: Schedule, match: str = "id", date_tolerance_hours: float = 0.0) -> Comparison:
    c = Comparison()
    # WBS summary rows are structure, not work: P6 keeps WBS apart from activities while Project
    # turns it into summary tasks, so they are left out of the activity-by-activity comparison.
    src_work = [a for a in source.activities if a.type != "summary"]
    tgt_work = [a for a in target.activities if a.type != "summary"]
    src = {_key(a, match): a for a in src_work}
    tgt = {_key(a, match): a for a in tgt_work}
    if len(src) != len(src_work):
        c.errors.append(f"{source.source}: activity keys are not unique when matching by {match}")
    if len(tgt) != len(tgt_work):
        c.errors.append(f"{target.source}: activity keys are not unique when matching by {match}")

    src_ids = {a.activity_id: _key(a, match) for a in source.activities}
    tgt_ids = {a.activity_id: _key(a, match) for a in target.activities}

    missing = sorted(set(src) - set(tgt))
    added = sorted(set(tgt) - set(src))
    for k in missing:
        c.errors.append(f"activity {src[k].activity_id} {src[k].name!r} is missing from {target.source}")
    for k in added:
        c.warnings.append(f"activity {tgt[k].activity_id} {tgt[k].name!r} is new in {target.source}")

    tolerance = date_tolerance_hours * 3600
    for k in sorted(set(src) & set(tgt)):
        a, b = src[k], tgt[k]
        if a.type != b.type and not {a.type, b.type} <= {"task", "level_of_effort"}:
            c.errors.append(f"activity {a.activity_id}: type {a.type} became {b.type}")
        for attr in ("start", "finish"):
            x, y = getattr(a, attr), getattr(b, attr)
            if x and y and abs((x - y).total_seconds()) > tolerance:
                c.errors.append(f"activity {a.activity_id}: {attr} {x:%Y-%m-%d %H:%M} became {y:%Y-%m-%d %H:%M}")
            elif bool(x) != bool(y):
                c.errors.append(f"activity {a.activity_id}: {attr} present in only one file")
        for attr in ("actual_start", "actual_finish"):
            if bool(getattr(a, attr)) != bool(getattr(b, attr)):
                c.errors.append(f"activity {a.activity_id}: {attr.replace('_', ' ')} lost or invented in conversion")
        if a.duration_hours is not None and b.duration_hours is not None and abs(a.duration_hours - b.duration_hours) > 0.01:
            c.errors.append(f"activity {a.activity_id}: duration {a.duration_hours:g}h became {b.duration_hours:g}h")
        if a.percent_complete is not None and b.percent_complete is not None and abs(a.percent_complete - b.percent_complete) > 0.5:
            c.warnings.append(
                f"activity {a.activity_id}: percent complete {a.percent_complete:g} became {b.percent_complete:g} "
                "(P6 physical % and Project duration % are not the same measure)"
            )
        if a.calendar and b.calendar and a.calendar != b.calendar:
            c.warnings.append(f"activity {a.activity_id}: calendar {a.calendar!r} became {b.calendar!r}")

    def links(s: Schedule, ids: dict[str, str]):
        return {(ids[r.predecessor_id], ids[r.successor_id], r.type): r.lag_hours for r in s.relationships}

    src_links, tgt_links = links(source, src_ids), links(target, tgt_ids)
    for link in sorted(set(src_links) - set(tgt_links)):
        c.errors.append(f"relationship {link[0]} -> {link[1]} ({link[2]}) is missing from {target.source}")
    for link in sorted(set(tgt_links) - set(src_links)):
        c.warnings.append(f"relationship {link[0]} -> {link[1]} ({link[2]}) is new in {target.source}")
    for link in sorted(set(src_links) & set(tgt_links)):
        if abs(src_links[link] - tgt_links[link]) > 0.01:
            c.errors.append(f"relationship {link[0]} -> {link[1]}: lag {src_links[link]:g}h became {tgt_links[link]:g}h")

    if source.data_date and target.data_date and source.data_date.date() != target.data_date.date():
        c.errors.append(f"data date {source.data_date:%Y-%m-%d} became {target.data_date:%Y-%m-%d}")

    for s in (source, target):
        c.warnings.extend(f"{s.source}: {w}" for w in s.warnings)
        starts = [a.start for a in s.activities if a.start]
        finishes = [a.finish for a in s.activities if a.finish]
        span = f"{min(starts):%Y-%m-%d} to {max(finishes):%Y-%m-%d}" if starts and finishes else "no dates"
        summaries = sum(1 for a in s.activities if a.type == "summary")
        extra = f" (+{summaries} summary rows)" if summaries else ""
        c.summary.append(f"{s.source}: {len(s.activities) - summaries} activities{extra}, {len(s.relationships)} relationships, {span}")
    return c
