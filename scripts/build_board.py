#!/usr/bin/env python3
"""Check every ticket in problems/ and write board.json and the README table.

    python scripts/build_board.py           rewrite board.json and the README table
    python scripts/build_board.py --check   fail if a ticket is wrong or the files are stale

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBLEMS = ROOT / "problems"

OWNER = "gkakkineni-devops"
STATUSES = ("open", "building", "done")
AREAS = ("Delivery", "Observability", "Cost", "Security", "Infrastructure")
MAX_SUMMARY = 120

OPEN_HEADINGS = ("The ask", "Why it hurts", "Done when")
WORK_HEADINGS = (
    "The ask",
    "Why it hurts",
    "What I built",
    "How I know it works",
    "What went wrong on the way",
    "What it doesn't do yet",
)

TABLE_START = "<!-- board:start -->"
TABLE_END = "<!-- board:end -->"
STATUS_WORDS = {"open": "Open", "building": "Building", "done": "Done"}


class ProblemError(Exception):
    """A ticket breaks a rule. The message says which file and what to change."""


def split_front_matter(text: str, name: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ProblemError(f"{name}: the file must start with a --- line")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise ProblemError(f"{name}: the fields at the top need a closing --- line") from None
    fields: dict[str, str] = {}
    for number, line in enumerate(lines[1:end], 2):
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep or not key.strip():
            raise ProblemError(f"{name}:{number}: expected 'key: value', got: {line[:50]}")
        fields[key.strip()] = value.strip()
    return fields, "\n".join(lines[end + 1 :])


def strip_comments(body: str) -> str:
    return re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)


def sections(body: str) -> dict[str, list[str]]:
    """Map each '## Heading' to the lines under it."""
    found: dict[str, list[str]] = {}
    current: str | None = None
    for line in strip_comments(body).splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            found[current] = []
        elif current is not None:
            found[current].append(line)
    return found


def bullets(lines: list[str]) -> list[str]:
    return [line.strip()[2:].strip() for line in lines if line.strip().startswith("- ")]


def parse_problem(path: Path) -> dict:
    name = path.name
    fields, body = split_front_matter(path.read_text(encoding="utf-8"), name)

    pid = fields.get("id", "")
    if not re.fullmatch(r"\d{3}", pid):
        raise ProblemError(f"{name}: id must be three digits, got '{pid}'")
    if not name.startswith(pid + "-"):
        raise ProblemError(f"{name}: the file name must start with the id ({pid}-)")

    title = fields.get("title", "")
    if not title:
        raise ProblemError(f"{name}: title is empty")

    status = fields.get("status", "")
    if status not in STATUSES:
        raise ProblemError(f"{name}: status must be one of {', '.join(STATUSES)}, got '{status}'")

    area = fields.get("area", "")
    if area not in AREAS:
        raise ProblemError(f"{name}: area must be one of {', '.join(AREAS)}, got '{area}'")

    summary = fields.get("summary", "")
    if not summary:
        raise ProblemError(f"{name}: summary is empty")
    if len(summary) > MAX_SUMMARY:
        raise ProblemError(f"{name}: summary is {len(summary)} characters, the limit is {MAX_SUMMARY}")

    tools = [t.strip() for t in fields.get("tools", "").split(",") if t.strip()]
    if not tools:
        raise ProblemError(f"{name}: tools is empty")

    repo = fields.get("repo", "")
    if status == "open" and repo:
        raise ProblemError(f"{name}: an open ticket has no repo yet, so leave repo empty")
    if status != "open" and not repo:
        raise ProblemError(f"{name}: a {status} ticket needs the repo that holds the work")
    if repo and not re.fullmatch(r"[A-Za-z0-9._-]+", repo):
        raise ProblemError(f"{name}: repo should be just the repo name, got '{repo}'")

    for key in ("site_page", "post"):
        value = fields.get(key, "")
        if value and (value.startswith(("/", "http")) or not value.endswith("/")):
            raise ProblemError(f"{name}: {key} should be a path like work/my-page/, got '{value}'")

    found = sections(body)
    needed = OPEN_HEADINGS if status == "open" else WORK_HEADINGS
    for heading in needed:
        if heading not in found:
            raise ProblemError(f"{name}: missing the '## {heading}' section")
        if not "".join(found[heading]).strip():
            raise ProblemError(f"{name}: the '## {heading}' section is empty")

    done_when = bullets(found.get("Done when", []))
    if status == "open" and not done_when:
        raise ProblemError(f"{name}: 'Done when' needs at least one '- ' line")

    return {
        "id": pid,
        "title": title,
        "status": status,
        "area": area,
        "summary": summary,
        "tools": tools,
        "repo": repo or None,
        "workflow": fields.get("workflow") or "ci.yml",
        "site_page": fields.get("site_page") or None,
        "post": fields.get("post") or None,
        "file": f"problems/{name}",
        "done_when": done_when,
    }


def load_problems(folder: Path) -> list[dict]:
    problems = [parse_problem(p) for p in sorted(folder.glob("[0-9][0-9][0-9]-*.md"))]
    seen: set[str] = set()
    for problem in problems:
        if problem["id"] in seen:
            raise ProblemError(f"id {problem['id']} is used by more than one ticket")
        seen.add(problem["id"])
    return problems


def build_board(problems: list[dict]) -> dict:
    counts = {status: sum(1 for p in problems if p["status"] == status) for status in STATUSES}
    return {"schema": 1, "counts": counts, "problems": problems}


def render_table(problems: list[dict], owner: str) -> str:
    rows = ["| # | Problem | Status | Area | Where |", "|---|---|---|---|---|"]
    for p in problems:
        where = f"[{p['repo']}](https://github.com/{owner}/{p['repo']})" if p["repo"] else ""
        title = f"[{p['title']}]({p['file']})"
        rows.append(f"| {p['id']} | {title} | {STATUS_WORDS[p['status']]} | {p['area']} | {where} |")
    return "\n".join(rows)


def replace_table(readme: str, table: str) -> str:
    start = readme.find(TABLE_START)
    end = readme.find(TABLE_END)
    if start == -1 or end == -1 or end < start:
        raise ProblemError(f"README.md needs {TABLE_START} and {TABLE_END} around the board table")
    return readme[: start + len(TABLE_START)] + "\n" + table + "\n" + readme[end:]


def expected_files(root: Path) -> dict[Path, str]:
    problems = load_problems(root / "problems")
    readme_path = root / "README.md"
    return {
        root / "board.json": json.dumps(build_board(problems), indent=2) + "\n",
        readme_path: replace_table(readme_path.read_text(encoding="utf-8"), render_table(problems, OWNER)),
    }


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail instead of rewriting files")
    args = parser.parse_args(argv)

    try:
        wanted = expected_files(root)
    except ProblemError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    stale = [
        path for path, text in wanted.items() if not path.exists() or path.read_text(encoding="utf-8") != text
    ]
    if args.check:
        if stale:
            names = ", ".join(p.name for p in stale)
            print(f"error: {names} out of date. Run: python scripts/build_board.py", file=sys.stderr)
            return 1
        print(f"ok: {len(load_problems(root / 'problems'))} tickets, board.json and README are current")
        return 0

    for path in stale:
        path.write_text(wanted[path], encoding="utf-8")
        print(f"wrote {path.name}")
    if not stale:
        print("nothing to change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
