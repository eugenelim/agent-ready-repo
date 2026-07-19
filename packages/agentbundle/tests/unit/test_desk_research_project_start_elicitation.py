"""RFC-0064 M3 bug-fix contract — desk-research-project-start resolution order.

Asserts that the skill body:
  1. Does NOT use `.context/research` (or `.context/desk-research`) as a
     silent fallback — the fix removed that default from the resolution order.
  2. DOES specify elicitation (two-branch: repo vs personal workspace) when
     no config resolves.
  3. Uses `output_dir` as the config key (not the pre-fix `parent` key).
  4. Checks user-scope config before repo-scope (user wins — personal vault
     should always apply regardless of which repo is active).

These are content assertions on the SKILL.md — the skill is prompt-only (no
runnable code), so the contract lives in the prose the agent reads.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_MD = (
    REPO_ROOT
    / "packs"
    / "desk-research"
    / ".apm"
    / "skills"
    / "desk-research-project-start"
    / "SKILL.md"
)


class DeskResearchProjectStartElicitationContract(unittest.TestCase):
    """The resolution-order contract lives in the SKILL.md prose.

    The skill is prompt-only — the agent reads these instructions and
    decides where to write. The test guards against regressions where a
    future edit re-introduces the silent .context/ default that D8 removed.
    """

    def setUp(self) -> None:
        self.body = SKILL_MD.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # 1. No silent .context/research fallback
    # ------------------------------------------------------------------

    def test_no_context_research_fallback_in_resolution_order(self) -> None:
        """The skill body must not describe .context/research as a fallback
        step in the resolution order — that was the pre-fix default the M3
        fix removed."""
        # We allow the phrase to appear in "what this is not" / historical
        # prose but NOT in the numbered resolution steps. Look for a pattern
        # that would indicate it is still a fallback step.
        fallback_patterns = [
            r"fall back.*\.context/research",
            r"\.context/research.*default",
            r"default.*\.context/research",
            r"Fall back to.*\.context",
        ]
        for pattern in fallback_patterns:
            self.assertNotRegex(
                self.body,
                pattern,
                f"SKILL.md still describes .context/research as a fallback "
                f"(matched {pattern!r}) — remove this from resolution order "
                f"per RFC-0064 M3 D8 fix",
            )

    def test_no_context_scratch_as_step_two(self) -> None:
        """The numbered resolution steps must not describe .context/ as a
        fallback option. The pre-fix skill had `.context/research` as step 2.
        `.context/` may appear in the 'never default to' warning — that is
        valid and expected; the test guards against it appearing as a step."""
        # Extract only the numbered list items (lines starting with "1.", "2.",
        # "3.") — the "Never default to .context/" sentence appears on a plain
        # prose line, not as a numbered step, so it is excluded from this check.
        step_lines = [
            line for line in self.body.splitlines()
            if re.match(r"^\d+\.\s+\*\*", line)
        ]
        for line in step_lines:
            self.assertNotIn(
                ".context/",
                line,
                f"A numbered resolution step describes .context/ as an option: "
                f"{line!r} — remove the silent scratch fallback per RFC-0064 M3 fix",
            )

    # ------------------------------------------------------------------
    # 2. Elicitation is present as the fallback
    # ------------------------------------------------------------------

    def test_elicitation_described_as_fallback(self) -> None:
        """When no config resolves the skill must elicit — the SKILL.md must
        describe an elicitation step (two-branch: repo vs personal workspace)."""
        elicitation_tokens = [
            "elicit",
            "two-branch",
            "Repo branch",
            "Personal branch",
        ]
        for token in elicitation_tokens:
            self.assertIn(
                token,
                self.body,
                f"SKILL.md missing elicitation token {token!r} — "
                f"the two-branch fallback must be described per RFC-0064 M3 D8",
            )

    def test_never_default_to_context_stated(self) -> None:
        """The skill must explicitly state it never defaults to .context/."""
        self.assertRegex(
            self.body,
            r"[Nn]ever.*\.context",
            "SKILL.md must explicitly state that .context/ is not a default "
            "— this guards against a silent regression",
        )

    # ------------------------------------------------------------------
    # 3. output_dir is the config key (not the pre-fix `parent`)
    # ------------------------------------------------------------------

    def test_output_dir_key_present(self) -> None:
        """The skill must reference `output_dir` as the layout key."""
        self.assertIn(
            "output_dir",
            self.body,
            "SKILL.md does not reference `output_dir` — the key was renamed "
            "from `parent` to `output_dir` in the M3 fix",
        )

    def test_parent_key_not_used_as_config_key(self) -> None:
        """The pre-fix `parent` key must not appear in the config examples
        or resolution steps (it may appear in prose context but not as the
        active key name in code blocks or step descriptions)."""
        # Find code blocks that show the TOML schema.
        code_blocks = re.findall(r"```toml(.*?)```", self.body, re.DOTALL)
        for block in code_blocks:
            self.assertNotIn(
                "parent =",
                block,
                "A TOML code block still uses `parent =` — rename to "
                "`output_dir =` per the M3 key-rename fix",
            )

    # ------------------------------------------------------------------
    # 4. User-scope checked before repo-scope
    # ------------------------------------------------------------------

    def test_user_scope_before_repo_scope(self) -> None:
        """User-scope config must appear as an earlier resolution step than
        repo-scope config — personal vault always wins."""
        user_pos = self.body.find("User-scope")
        repo_pos = self.body.find("Repo-scope")
        if user_pos == -1:
            # Try alternate phrasing.
            user_pos = self.body.find("user-scope")
        if repo_pos == -1:
            repo_pos = self.body.find("repo-scope")
        self.assertNotEqual(user_pos, -1, "SKILL.md missing user-scope step")
        self.assertNotEqual(repo_pos, -1, "SKILL.md missing repo-scope step")
        self.assertLess(
            user_pos,
            repo_pos,
            "User-scope must appear before repo-scope in the resolution order "
            "— personal workspace config takes priority over team convention",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
