import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build_board  # noqa: E402

OPEN_TICKET = """---
id: 004
title: Nobody knows what is wasting money
status: open
area: Cost
repo:
tools: Python, Terraform
summary: A weekly report of idle resources.
---

## The ask

Give us a list.

## Why it hurts

It costs money.

## Done when

- A function finds idle volumes.
- Terraform deploys it.
"""

DONE_TICKET = """---
id: 001
title: A bad release reaches every user
status: done
area: Delivery
repo: gitops-canary-rollouts
site_page: work/gitops-canary-rollouts/
tools: Helm, Argo Rollouts
summary: Release in steps.
---

## The ask

Releases go to everyone.

## Why it hurts

Everyone sees a bad one.

## What I built

A chart.

## How I know it works

CI ships a bad release.

## What went wrong on the way

A typo.

## What it doesn't do yet

Exact weights.
"""

README = f"""# Board

{build_board.TABLE_START}
{build_board.TABLE_END}

More text.
"""


def make_repo(root: Path, tickets: dict[str, str], readme: str = README) -> None:
    (root / "problems").mkdir()
    for name, text in tickets.items():
        (root / "problems" / name).write_text(text, encoding="utf-8")
    (root / "README.md").write_text(readme, encoding="utf-8")


class ParseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def parse(self, name: str, text: str) -> dict:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return build_board.parse_problem(path)

    def test_open_ticket_is_read(self):
        problem = self.parse("004-idle.md", OPEN_TICKET)
        self.assertEqual(problem["status"], "open")
        self.assertIsNone(problem["repo"])
        self.assertEqual(problem["tools"], ["Python", "Terraform"])
        self.assertEqual(problem["done_when"], ["A function finds idle volumes.", "Terraform deploys it."])

    def test_done_ticket_is_read(self):
        problem = self.parse("001-release.md", DONE_TICKET)
        self.assertEqual(problem["repo"], "gitops-canary-rollouts")
        self.assertEqual(problem["site_page"], "work/gitops-canary-rollouts/")
        self.assertEqual(problem["workflow"], "ci.yml")
        self.assertEqual(problem["done_when"], [])

    def assertRejected(self, name: str, text: str, message: str):
        with self.assertRaises(build_board.ProblemError) as caught:
            self.parse(name, text)
        self.assertIn(message, str(caught.exception))

    def test_bad_status(self):
        self.assertRejected(
            "004-idle.md", OPEN_TICKET.replace("status: open", "status: wip"), "status must be"
        )

    def test_bad_area(self):
        self.assertRejected("004-idle.md", OPEN_TICKET.replace("area: Cost", "area: Magic"), "area must be")

    def test_id_must_match_the_file_name(self):
        self.assertRejected("005-idle.md", OPEN_TICKET, "must start with the id")

    def test_open_ticket_must_not_have_a_repo(self):
        self.assertRejected(
            "004-idle.md", OPEN_TICKET.replace("repo:", "repo: some-repo"), "leave repo empty"
        )

    def test_done_ticket_needs_a_repo(self):
        self.assertRejected(
            "001-release.md", DONE_TICKET.replace("repo: gitops-canary-rollouts", "repo:"), "needs the repo"
        )

    def test_missing_section(self):
        text = DONE_TICKET.replace("## What went wrong on the way", "## Something else")
        self.assertRejected("001-release.md", text, "missing the '## What went wrong on the way'")

    def test_empty_section(self):
        text = DONE_TICKET.replace("A chart.", "")
        self.assertRejected("001-release.md", text, "'## What I built' section is empty")

    def test_done_when_needs_bullets(self):
        text = OPEN_TICKET.replace("- A function finds idle volumes.\n- Terraform deploys it.", "Just words.")
        self.assertRejected("004-idle.md", text, "at least one")

    def test_long_summary(self):
        text = OPEN_TICKET.replace("A weekly report of idle resources.", "x" * 121)
        self.assertRejected("004-idle.md", text, "limit is 120")

    def test_site_page_must_be_a_relative_path(self):
        text = DONE_TICKET.replace("work/gitops-canary-rollouts/", "/work/gitops-canary-rollouts")
        self.assertRejected("001-release.md", text, "site_page should be a path")

    def test_comments_do_not_count_as_content(self):
        text = OPEN_TICKET.replace("It costs money.", "<!-- nothing here -->")
        self.assertRejected("004-idle.md", text, "'## Why it hurts' section is empty")

    def test_missing_front_matter(self):
        self.assertRejected("004-idle.md", "## The ask\n\nHi\n", "must start with a ---")


class BoardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_duplicate_ids_are_rejected(self):
        make_repo(self.root, {"004-a.md": OPEN_TICKET, "004-b.md": OPEN_TICKET})
        with self.assertRaises(build_board.ProblemError) as caught:
            build_board.load_problems(self.root / "problems")
        self.assertIn("more than one ticket", str(caught.exception))

    def test_template_and_other_files_are_ignored(self):
        make_repo(self.root, {"004-a.md": OPEN_TICKET, "_template.md": "not a ticket"})
        self.assertEqual(len(build_board.load_problems(self.root / "problems")), 1)

    def test_board_counts_and_order(self):
        make_repo(self.root, {"004-a.md": OPEN_TICKET, "001-b.md": DONE_TICKET})
        board = build_board.build_board(build_board.load_problems(self.root / "problems"))
        self.assertEqual([p["id"] for p in board["problems"]], ["001", "004"])
        self.assertEqual(board["counts"], {"open": 1, "building": 0, "done": 1})

    def test_write_then_check_passes(self):
        make_repo(self.root, {"004-a.md": OPEN_TICKET, "001-b.md": DONE_TICKET})
        self.assertEqual(build_board.main([], root=self.root), 0)
        self.assertEqual(build_board.main(["--check"], root=self.root), 0)
        board = json.loads((self.root / "board.json").read_text())
        self.assertEqual(board["counts"]["done"], 1)
        readme = (self.root / "README.md").read_text()
        self.assertIn("| 001 | [A bad release reaches every user](problems/001-b.md) | Done |", readme)
        self.assertIn("More text.", readme)

    def test_check_fails_when_a_ticket_changes_and_board_does_not(self):
        make_repo(self.root, {"004-a.md": OPEN_TICKET})
        build_board.main([], root=self.root)
        ticket = self.root / "problems" / "004-a.md"
        ticket.write_text(OPEN_TICKET.replace("status: open", "status: open\nworkflow: other.yml"))
        self.assertEqual(build_board.main(["--check"], root=self.root), 1)

    def test_check_fails_when_board_is_missing(self):
        make_repo(self.root, {"004-a.md": OPEN_TICKET})
        self.assertEqual(build_board.main(["--check"], root=self.root), 1)

    def test_readme_needs_the_markers(self):
        make_repo(self.root, {"004-a.md": OPEN_TICKET}, readme="# No markers here\n")
        self.assertEqual(build_board.main([], root=self.root), 1)


if __name__ == "__main__":
    unittest.main()
