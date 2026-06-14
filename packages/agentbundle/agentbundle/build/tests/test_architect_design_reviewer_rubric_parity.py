"""Rubric-parity guard for architect's `design-reviewer` subagent (RFC-0032).

The `design-reviewer` agent inlines a condensed copy of `architect-review`'s
verdict scheme, severity glossary, and 🔧/🧭 mechanical-judgment taxonomy
(agents bundle no `references/`, so the rubric is inlined — the pack's
duplication-over-DRY stance). The *prose* is free to be condensed, but three
token sets are a **cross-skill interop contract**: `architect-design`'s
convergence loop consumes mechanical/judgment-tagged findings and routes on the
verdict + severity vocabulary, so those tokens must stay identical wherever they
appear. This is the same reason `tools/lint-knowledge-surface-parity.py` guards
the knowledge-surface taxonomy despite the duplication principle.

This test is the guard the `design-reviewer-rubric-drift` backlog item asked
for. The canonical constants below are an **explicit allowlist** of the
interop tokens: a clean *rename or drop* in any carrier (e.g. retitling
`SHIP IT` in `architect-review/SKILL.md`) removes the token from that file,
fails the per-file assertion, and forces the rename to be reconciled across the
constant *and* every carrier in one change — that clean-rename drift is the
realistic case and what this catches. Two limits, by design: a reword that
keeps the token as a substring (`MAJOR REWRITE` → `MAJOR REWRITE REQUIRED`) is
not caught (AC2's one-time byte-faithful diff covers strict wording), and a
*newly added* verdict/glyph must be added to the constants here by hand — the
allowlist does not auto-discover vocabulary growth.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
ARCHITECT = REPO_ROOT / "packs" / "architect"

# The interop vocabulary, canonical. (Prose around these may be condensed in a
# copy; the tokens themselves may not drift.)
VERDICTS = ("SHIP IT", "SHIP WITH CHANGES", "MAJOR REWRITE", "WRONG ARTIFACT")
SEVERITY_GLYPHS = ("🟥", "🟧", "🟨", "⚪")
TAXONOMY_GLYPHS = ("🔧", "🧭")
ALL_TOKENS = VERDICTS + SEVERITY_GLYPHS + TAXONOMY_GLYPHS

# Every carrier of the rubric vocabulary. architect-review is canonical (its
# SKILL.md + rubric-well-architected.md own the verdict / severity / taxonomy);
# the design-reviewer agent is the inlined copy. All must carry every token.
CARRIERS = (
    ARCHITECT / ".apm" / "skills" / "architect-review" / "SKILL.md",
    ARCHITECT / ".apm" / "skills" / "architect-review" / "references" / "rubric-well-architected.md",
    ARCHITECT / ".apm" / "agents" / "design-reviewer.md",
)


class ArchitectRubricParityTests(unittest.TestCase):
    def test_every_carrier_exists(self) -> None:
        for path in CARRIERS:
            with self.subTest(path=str(path)):
                self.assertTrue(path.exists(), f"rubric carrier missing: {path}")

    def test_interop_tokens_consistent_across_carriers(self) -> None:
        for path in CARRIERS:
            text = path.read_text(encoding="utf-8")
            for token in ALL_TOKENS:
                with self.subTest(carrier=path.name, token=token):
                    self.assertIn(
                        token,
                        text,
                        f"{path.name} is missing interop token {token!r} — the "
                        f"design-reviewer agent and architect-review must share "
                        f"one verdict / severity / mechanical-judgment vocabulary; "
                        f"reconcile the rename across all carriers and the "
                        f"canonical constants in this test.",
                    )


if __name__ == "__main__":
    unittest.main()
