"""The core how-to describes the spec sections that exist.

Repository-scope by necessity: `lint-pack-test-boundary` forbids a pack test
from reading above `packs/<pack>/`, and this reads `guides/core/`. The rest of
the contract is pinned in
`packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py`.

This suite is dispatch-only (`test-roster.yml`), so treat it as partial
evidence: it is not a required PR check.

Spec: docs/specs/spec-plan-prose-discipline/spec.md — AC-0009, guide half.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "guides" / "core" / "how-to" / "plan-and-execute-non-trivial-work.md"


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class TheGuideNamesTheCurrentSpecSections(unittest.TestCase):
    def setUp(self) -> None:
        self.body = flat(GUIDE.read_text(encoding="utf-8"))

    def test_the_retired_section_names_are_gone(self) -> None:
        for stale in ("Objective", "Boundaries", "before `Approach:`"):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, self.body)

    def test_the_current_names_are_present(self) -> None:
        # Paired with the absence arm: deleting the passages would pass that
        # one alone, and a guide that describes no sections is not the goal.
        for current in ("Agent Rules", "Outcome", "What Changes"):
            with self.subTest(current=current):
                self.assertIn(current, self.body)

    def test_the_conditional_approach_rule_replaced_the_unconditional_one(self) -> None:
        self.assertIn(
            "an `Approach:` only where the task carries an ordering or seam decision",
            self.body,
        )


if __name__ == "__main__":
    unittest.main()
