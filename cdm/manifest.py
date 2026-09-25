"""File manifests: prove that a document export or archive arrived complete and unaltered.

A manifest lists every file under a folder with its size and SHA-256 hash. Take one of the export as it
left the old system, and one of the archive or upload folder after the copy. If the two agree, every file
arrived, none was added, and none was changed. That includes the silent changes that happen when a tool
"helpfully" re-saves a PDF or re-compresses a photo and strips its metadata.
"""

from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

SKIP = {".DS_Store", "Thumbs.db", "desktop.ini"}


@dataclass
class Entry:
    path: str
    size: int
    sha256: str


@dataclass
class ManifestDiff:
    missing: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    moved: list[tuple[str, str]] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not (self.missing or self.added or self.changed)


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def build(folder) -> list[Entry]:
    root = Path(folder)
    if not root.is_dir():
        raise FileNotFoundError(f"{root} is not a folder")
    entries = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name not in SKIP):
        entries.append(Entry(path.relative_to(root).as_posix(), path.stat().st_size, _hash(path)))
    return entries


def write(entries: list[Entry], out) -> None:
    with Path(out).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["path", "size", "sha256"])
        for e in entries:
            writer.writerow([e.path, e.size, e.sha256])


def load(source) -> list[Entry]:
    """Read a manifest CSV, or build one on the fly if given a folder."""
    path = Path(source)
    if path.is_dir():
        return build(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return [Entry(r["path"], int(r["size"]), r["sha256"]) for r in csv.DictReader(handle)]


def summarise(entries: list[Entry]) -> str:
    by_ext = Counter(Path(e.path).suffix.lower() or "(none)" for e in entries)
    size = sum(e.size for e in entries)
    parts = ", ".join(f"{n} {ext}" for ext, n in by_ext.most_common(6))
    return f"{len(entries)} files, {size:,} bytes ({parts})"


def compare(before: list[Entry], after: list[Entry]) -> ManifestDiff:
    diff = ManifestDiff()
    a = {e.path: e for e in before}
    b = {e.path: e for e in after}
    for p in sorted(set(a) & set(b)):
        if a[p].sha256 != b[p].sha256:
            diff.changed.append(p)
    gone = sorted(set(a) - set(b))
    new = sorted(set(b) - set(a))
    # a file that moved folder keeps its hash: report it as moved rather than missing plus added
    new_by_hash: dict[str, list[str]] = defaultdict(list)
    for p in new:
        new_by_hash[b[p].sha256].append(p)
    for p in gone:
        candidates = new_by_hash.get(a[p].sha256)
        if candidates:
            target = candidates.pop(0)
            diff.moved.append((p, target))
            new.remove(target)
        else:
            diff.missing.append(p)
    diff.added = new
    diff.summary = [f"before: {summarise(before)}", f"after:  {summarise(after)}"]
    return diff
