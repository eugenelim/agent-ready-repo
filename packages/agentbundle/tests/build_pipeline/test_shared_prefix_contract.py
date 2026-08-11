"""T5: the `shared` prefix class + cohort routing.

The adapter contract gains a `[contract.shared-prefixes]` registry mapping each
shared prefix to its reader cohort (shipped adapters); every other prefix is
`private` by derivation. cursor/gemini/copilot route the `skill` primitive to
the shared `.agents/skills/` home (joining codex) and include it in
`allowed-prefixes` at both scopes.
"""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
_DATA_COPY = _PACKAGE_ROOT / "agentbundle" / "_data" / "adapter.toml"


def _contract() -> dict:
    return tomllib.loads(_DATA_COPY.read_text(encoding="utf-8"))


class SharedPrefixRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = _contract()
        self.shared = self.contract["contract"]["shared-prefixes"]

    def test_contract_version_bumped(self) -> None:
        self.assertEqual(self.contract["contract"]["version"], "0.18")

    def test_agents_skills_shared_with_full_cohort(self) -> None:
        self.assertEqual(
            sorted(self.shared[".agents/skills/"]),
            ["codex", "copilot", "cursor", "gemini"],
        )

    def test_kiro_skills_shared_with_kiro_cohort(self) -> None:
        self.assertEqual(
            sorted(self.shared[".kiro/skills/"]),
            ["kiro-cli", "kiro-ide"],
        )

    def test_only_known_shared_prefixes_declared(self) -> None:
        # Everything not in the registry is `private` by derivation; the
        # registry itself holds exactly the two shared prefixes.
        self.assertEqual(
            set(self.shared), {".agents/skills/", ".kiro/skills/"}
        )

    def test_private_prefix_not_in_registry(self) -> None:
        # A representative private prefix (claude-code's `.claude/`) is absent.
        self.assertNotIn(".claude/", self.shared)


class CohortSkillRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = _contract()

    def _skill_target(self, adapter: str) -> str:
        for p in self.contract["adapter"][adapter]["projection"]:
            if p.get("primitive") == "skill":
                return p["target-path"]
        raise AssertionError(f"no skill projection for {adapter}")

    def test_cohort_skill_targets_shared_home(self) -> None:
        for adapter in ("codex", "cursor", "gemini", "copilot"):
            self.assertEqual(
                self._skill_target(adapter), ".agents/skills/",
                f"{adapter} skill must route to the shared .agents/skills/ home",
            )

    def test_cohort_allowed_prefixes_include_shared_home_both_scopes(self) -> None:
        for adapter in ("cursor", "gemini", "copilot"):
            scope = self.contract["adapter"][adapter]["scope"]
            for which in ("repo", "user"):
                self.assertIn(
                    ".agents/skills/", scope["allowed-prefixes"][which],
                    f"{adapter}.{which} must admit the shared skill prefix",
                )

    def test_cohort_agents_stay_native(self) -> None:
        # Only the skill primitive moves; agents stay native.
        for adapter, native in (
            ("cursor", ".cursor/agents/"),
            ("gemini", ".gemini/agents/"),
            ("copilot", ".github/agents/"),
        ):
            agent = next(
                p for p in self.contract["adapter"][adapter]["projection"]
                if p.get("primitive") == "agent"
            )
            self.assertEqual(agent["target-path"], native)


if __name__ == "__main__":
    unittest.main()
