#!/usr/bin/env python3
"""Check the repository: links resolve, chapters are complete, samples are current, tools behave.

Run from anywhere:  python3 scripts/check_repo.py
Exits non-zero on any error, so it runs in CI on every push.
"""

from __future__ import annotations

import csv
import filecmp
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)

CHAPTERS = [
    "01-why-migrations-fail.md",
    "02-plan-the-migration.md",
    "03-the-records-that-matter.md",
    "04-source-data-quality.md",
    "05-cost-codes-and-crosswalks.md",
    "06-financial-cutover.md",
    "07-reconciliation.md",
    "08-project-records-and-documents.md",
    "09-schedules.md",
    "10-integrations-and-reports.md",
    "11-cutover-runbook.md",
    "12-after-go-live.md",
    "13-handling-migration-data-safely.md",
    "14-working-with-vendors-and-implementers.md",
    "15-faq.md",
    "16-worked-example.md",
    "CHECKS.md",
    "GLOSSARY.md",
    "AGENTS.md",
]
TEMPLATES = [
    "templates/migration-inventory.csv",
    "templates/scope-decisions.csv",
    "templates/cost-code-crosswalk.csv",
    "templates/field-mapping.csv",
    "templates/integration-inventory.csv",
    "templates/report-rebuild-list.csv",
    "templates/issue-log.csv",
    "templates/parallel-run-log.csv",
    "templates/vendor-and-implementer-questions.md",
    "templates/cutover-checklist.md",
    "templates/go-no-go.md",
    "templates/reconciliation-sign-off.md",
]
SITE = "https://constructelligence.co"
HELP = "https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose"

errors: list[str] = []


def slug(text: str) -> str:
    text = re.sub(r"`", "", text.strip().lower())
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text).strip("-")


def check_links() -> None:
    for path in sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts):
        text = FENCE_RE.sub("", path.read_text(encoding="utf-8"))
        for target in LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            file_part, _, anchor = target.partition("#")
            dest = (path.parent / file_part).resolve() if file_part else path
            rel = path.relative_to(ROOT)
            if not dest.exists():
                errors.append(f"{rel}: broken link {target}")
                continue
            if anchor and dest.suffix == ".md":
                anchors = {slug(h) for h in HEADING_RE.findall(dest.read_text(encoding="utf-8"))}
                if anchor not in anchors:
                    errors.append(f"{rel}: no heading #{anchor} in {file_part or rel}")


def check_structure() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for chapter in CHAPTERS + TEMPLATES:
        if not (ROOT / chapter).exists():
            errors.append(f"missing {chapter}")
        elif chapter not in readme:
            errors.append(f"README does not link {chapter}")
    for chapter in CHAPTERS:
        path = ROOT / chapter
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("# "):
            errors.append(f"{chapter}: must start with a level-one heading")
        if SITE not in text:
            errors.append(f"{chapter}: footer must link {SITE}")
    for must in (SITE, HELP):
        if must not in readme:
            errors.append(f"README must link {must}")
    for template in TEMPLATES:
        path = ROOT / template
        if path.suffix == ".csv" and path.exists():
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
            widths = {len(r) for r in rows}
            if len(widths) != 1:
                errors.append(f"{template}: rows have different column counts {sorted(widths)}")


def check_samples_current() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, CDM_SAMPLES_OUT=tmp)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "make_samples.py")], check=True, env=env, stdout=subprocess.DEVNULL)
        fresh = Path(tmp)
        for new in sorted(fresh.rglob("*")):
            if new.is_file():
                old = ROOT / "samples" / new.relative_to(fresh)
                if not old.exists() or not filecmp.cmp(new, old, shallow=False):
                    errors.append(f"samples/{new.relative_to(fresh)} is stale: run python3 scripts/make_samples.py")


def check_tests() -> None:
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests")], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        errors.append("unit tests failed:\n" + proc.stderr[-3000:])


def main() -> int:
    check_links()
    check_structure()
    check_samples_current()
    check_tests()
    for e in errors:
        print(f"ERROR {e}")
    print(f"{'OK' if not errors else 'FAILED'}: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
