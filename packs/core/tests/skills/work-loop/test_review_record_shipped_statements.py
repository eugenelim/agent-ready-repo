#!/usr/bin/env python3
"""Every shipped recording statement supplies a recomputable operation id.

Two properties, both about the shipped instructions rather than the writer:

1. Every `review record` command statement passes `--operation-id`. Without it the
   decidability the writer provides is unreachable, because nothing on disk names
   the round.
2. Every recording statement is guarded against a refused transition. The
   transition carries the retry-cap guard and the recording does not, so a
   recording that runs after a refused transition increments past the cap.

A *command statement* is a line naming the cohort script together with the
`review record` verb, extended through trailing-backslash continuations. A prose
mention that does not name the script is documentation, not an instruction — the
state-schema reference describes the flags in a field table and must not be
rewritten to satisfy a grep.

Scope is the pack source only. The regenerated adapter projections are covered by
the self-host drift gate, and `evals/evals.json` records expected transcripts
rather than instructions.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = PACK_ROOT / ".apm" / "skills" / "work-loop"
if not SKILL_DIR.is_dir():  # wrong parents[] depth after a move
    raise SystemExit(f"subject dir not found at {SKILL_DIR} — check the parents[] depth")

STATEMENT_RE = re.compile(r"loop-cohort\.py'?\s+review\s+record\b")
TRANSITION_RE = re.compile(r"loop-engine\.py'?\s+transition\b")


def _sources() -> list[Path]:
    return [SKILL_DIR / "SKILL.md", *sorted((SKILL_DIR / "references").rglob("*.md"))]


def _statements(path: Path) -> list[tuple[int, str]]:
    """Return `(line_number, full_statement)` for each recording command."""
    lines = path.read_text(encoding="utf-8").splitlines()
    found = []
    for index, line in enumerate(lines):
        if not STATEMENT_RE.search(line):
            continue
        statement, cursor = [line], index
        while lines[cursor].rstrip().endswith("\\") and cursor + 1 < len(lines):
            cursor += 1
            statement.append(lines[cursor])
        found.append((index + 1, "\n".join(statement)))
    return found


class ShippedRecordingStatements(unittest.TestCase):
    maxDiff = None

    def test_every_statement_supplies_an_operation_id(self) -> None:
        missing = [
            f"{path.relative_to(SKILL_DIR)}:{line}"
            for path in _sources()
            for line, statement in _statements(path)
            if "--operation-id" not in statement
        ]
        self.assertEqual(missing, [], "recording statements without --operation-id")

    def test_the_statement_set_is_not_empty(self) -> None:
        # Guards the check above against silently passing on zero statements, which
        # is how a renamed script or a changed quoting style would hide a gap.
        total = sum(len(_statements(path)) for path in _sources())
        self.assertGreaterEqual(total, 7, "expected at least the seven shipped statements")

    def test_every_recording_is_guarded_against_a_refused_transition(self) -> None:
        """A recording must not be reachable after a transition that refused.

        Satisfied either by a shell `&&` chaining it to its transition, or by a
        stated obligation in the preceding lines of the same fenced block. The
        operator matters less than the guarantee; pinning the operator would
        forbid reading the sequence the id needs, which only exists after the
        transition returns.
        """
        unguarded = []
        for path in _sources():
            lines = path.read_text(encoding="utf-8").splitlines()
            for line, statement in _statements(path):
                index = line - 1
                if statement.lstrip().startswith("&&"):
                    continue
                window = "\n".join(lines[max(0, index - 6):index]).lower()
                if TRANSITION_RE.search("\n".join(lines[max(0, index - 6):index])) and (
                    "must succeed" in window
                    or "only if it succeeded" in window
                    or "never record when the transition is refused" in window
                ):
                    continue
                if not TRANSITION_RE.search("\n".join(lines[max(0, index - 6):index])):
                    continue  # not preceded by a transition at all
                unguarded.append(f"{path.relative_to(SKILL_DIR)}:{line}")
        self.assertEqual(unguarded, [], "recordings reachable after a refused transition")

    def test_the_eval_corpus_covers_the_id_carrying_crash_window(self) -> None:
        evals = json.loads((SKILL_DIR / "evals" / "evals.json").read_text(encoding="utf-8"))
        cases = evals["evals"]
        carrying = [
            case for case in cases
            if "--operation-id" in case.get("prompt", "")
            or "operation_id" in case.get("expected_output", "")
            or "operation id" in case.get("expected_output", "")
        ]
        self.assertTrue(carrying, "no eval exercises a recording that carries an operation id")

    def test_the_two_pre_existing_crash_window_cases_survive(self) -> None:
        evals = json.loads((SKILL_DIR / "evals" / "evals.json").read_text(encoding="utf-8"))
        ids = {case["id"] for case in evals["evals"]}
        for case_id in ("phase1-surface-ambiguous-review-record",
                        "phase1-explicit-auth-clean-record-replay"):
            self.assertIn(case_id, ids)


if __name__ == "__main__":
    unittest.main()
