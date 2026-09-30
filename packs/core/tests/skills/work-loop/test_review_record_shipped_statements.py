#!/usr/bin/env python3
"""Every remaining direct recording statement supplies a recomputable operation id.

Two properties, both about the shipped instructions rather than the writer:

1. Every `review record` command statement passes `--operation-id`. Without it the
   decidability the writer provides is unreachable, because nothing on disk names
   the round.
2. Every direct recording statement is guarded against a refused transition.
   Registered CODE-REVIEW effects are applied by the engine transition instead
   and must not be restored here as separate recording statements.

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
        self.assertEqual(total, 1, "expected the one pre-EXECUTE direct statement")

    def test_every_recording_is_guarded_against_a_refused_transition(self) -> None:
        """A recording must not be reachable after a transition that refused.

        Keyed on the nearest preceding transition anywhere in the enclosing fenced
        block, not a fixed line window. A window is the wrong shape here: adding
        an explanatory comment above a statement pushes its transition out of
        range and turns the check green without changing what it checks, which is
        exactly how an earlier version of this test came to exempt three of the
        four statements in `SKILL.md`.

        The guarantee is what is asserted, not the syntax. A shell `&&` and a
        stated obligation both satisfy it; requiring `&&` would forbid reading
        the sequence the operation id needs, which exists only after the
        transition returns.
        """
        examined, unguarded = [], []
        for path in _sources():
            lines = path.read_text(encoding="utf-8").splitlines()
            fences = [n for n, line in enumerate(lines) if line.lstrip().startswith("```")]
            for line, statement in _statements(path):
                index = line - 1
                block_start = max((f for f in fences if f < index), default=0)
                preceding = lines[block_start:index]
                if not any(TRANSITION_RE.search(item) for item in preceding):
                    continue  # no transition in this block: nothing to guard against
                examined.append(f"{path.relative_to(SKILL_DIR)}:{line}")
                if statement.lstrip().startswith("&&"):
                    continue
                prose = "\n".join(preceding).lower()
                if ("must succeed" in prose
                        or "only if it succeeded" in prose
                        or "never record when the transition is refused" in prose):
                    continue
                unguarded.append(f"{path.relative_to(SKILL_DIR)}:{line}")
        self.assertEqual(unguarded, [], "recordings reachable after a refused transition")
        # Non-vacuity coupled to the census, not to a literal. A floor set at the
        # residue of the defect it was added to catch still tolerates that defect:
        # every statement found must also have been examined.
        census = sum(len(_statements(path)) for path in _sources())
        self.assertEqual(
            len(examined), census,
            f"guard check skipped {census - len(examined)} statement(s): {examined}")

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

    def test_the_registered_effect_crash_window_case_survives(self) -> None:
        """Pin the engine-owned replay case and the behavior its id represents."""
        evals = json.loads((SKILL_DIR / "evals" / "evals.json").read_text(encoding="utf-8"))
        cases = {case["id"]: case for case in evals["evals"]}
        case_id = "durable-review-operation-id-crash-window"
        self.assertIn(case_id, cases)
        expected = cases[case_id]["expected_output"]
        self.assertTrue(expected.strip(), f"{case_id} has an empty expected_output")
        for phrase in (
            "Re-run the identical engine transition",
            "Do not issue a separate `loop-cohort review record`",
            "transition id as the review operation id",
        ):
            self.assertIn(phrase, expected, f"{case_id} lost {phrase!r}")
