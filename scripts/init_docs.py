#!/usr/bin/env python3
"""Scaffold the Ges-Talt docs convention into a repo. Idempotent.

    python3 scripts/init_docs.py [target-repo-root] [--sprint M-Y-DD-DD]

Creates:
    docs/backlog.md                     — the backlog table
    docs/enterprise.md                  — tiering/ontology/taxonomy/semantics
    docs/sprint-<m>-<y>-<dd>-<dd>/      — current sprint (default: today,
        prd.md                            7-day window)
        sprint-log/
        user-journeys/
    docs/templates/                     — copied from this repo if absent

Existing files are never overwritten.
"""
import argparse
import re
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SPRINT_RE = re.compile(r"^sprint-(\d{1,2})-(\d{2})-(\d{1,2})-(\d{1,2})$")


def find_current_sprint(docs):
    """Return the M-Y-DD-DD suffix of an existing sprint whose window
    covers today, or None. End day < start day means the window crosses
    into the next month."""
    today = date.today()
    for d in sorted(docs.glob("sprint-*")):
        m = SPRINT_RE.match(d.name)
        if not m:
            continue
        month, yy, d1, d2 = map(int, m.groups())
        try:
            start = date(2000 + yy, month, d1)
            if d2 >= d1:
                end = date(2000 + yy, month, d2)
            else:
                nm, ny = (month % 12) + 1, 2000 + yy + (month == 12)
                end = date(ny, nm, d2)
        except ValueError:
            continue
        if start <= today <= end:
            return d.name[len("sprint-"):]
    return None


BACKLOG = """# Backlog

Rows are added by the spec-driven PM (`agents/pm/project-manager`); one row
per issue. Status: todo / in-progress / blocked / done.

| ID | Item | Assignee (agent) | Sprint | Status | Issue |
|---|---|---|---|---|---|
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root", nargs="?", default=".", help="target repo root")
    p.add_argument("--sprint", help="sprint name suffix M-Y-DD-DD; default: today + 7 days")
    args = p.parse_args()

    root = Path(args.root).resolve()
    if not (root / ".git").exists():
        sys.exit(f"{root} is not a git repo root")

    docs = root / "docs"

    if args.sprint:
        suffix = args.sprint
    else:
        current = find_current_sprint(docs)
        if current:
            suffix = current
        else:
            start = date.today()
            end = start + timedelta(days=7)
            suffix = f"{start.month}-{start.year % 100}-{start.day}-{end.day}"

    sprint = docs / f"sprint-{suffix}"
    made = []

    for d in (sprint / "sprint-log", sprint / "user-journeys"):
        if not d.exists():
            d.mkdir(parents=True)
            (d / ".gitkeep").touch()
            made.append(str(d.relative_to(root)))

    backlog = docs / "backlog.md"
    if not backlog.exists():
        backlog.write_text(BACKLOG)
        made.append("docs/backlog.md")

    src_templates = HERE / "docs" / "templates"
    dst_templates = docs / "templates"
    if not dst_templates.exists() and src_templates.exists():
        shutil.copytree(src_templates, dst_templates)
        made.append("docs/templates/")

    prd = sprint / "prd.md"
    if not prd.exists():
        tpl = dst_templates / "prd.md"
        prd.write_text(tpl.read_text() if tpl.exists() else "# PRD\n")
        made.append(str(prd.relative_to(root)))

    enterprise = docs / "enterprise.md"
    if not enterprise.exists():
        tpl = dst_templates / "enterprise-doc.md"
        enterprise.write_text(tpl.read_text() if tpl.exists() else "# Enterprise Doc\n")
        made.append(str(enterprise.relative_to(root)))

    print("created: " + ", ".join(made) if made else "nothing to do — scaffold already present")


if __name__ == "__main__":
    main()
