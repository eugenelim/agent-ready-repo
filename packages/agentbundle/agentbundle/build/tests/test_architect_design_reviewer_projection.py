"""Durable projection check for architect's `design-reviewer` subagent (RFC-0032).

architect-design-reviewer spec AC10: the agent must project across **all seven**
adapters architect declares in `allowed-adapters`. The per-adapter projection
*mechanism* is covered elsewhere with synthetic agents; this test pins the
*real* architect agent across every route so a future adapter change that drops
it fails here. It also lands RFC-0032's deferred `kiro-cli` confirmation
(`kiro-cli` is the one adapter architect ships that the research pack does not).

Naming varies per adapter (codex emits `.toml`, copilot `.agent.md`, kiro remaps
frontmatter, …), so the assertion globs `design-reviewer*` under the projected
output rather than hard-coding one extension.
"""

from __future__ import annotations

import tempfile
import tomllib
import unittest
from pathlib import Path

from agentbundle.build.adapters import ADAPTERS
from agentbundle.build.contract import load as load_contract

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"
ARCHITECT_PACK = REPO_ROOT / "packs" / "architect"
AGENT_NAME = "design-reviewer"


def _architect_allowed_adapters() -> list[str]:
    data = tomllib.loads((ARCHITECT_PACK / "pack.toml").read_text(encoding="utf-8"))
    return list(data["pack"]["install"]["allowed-adapters"])


class ArchitectDesignReviewerProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)
        cls.adapters = _architect_allowed_adapters()

    def test_source_agent_present(self) -> None:
        self.assertTrue(
            (ARCHITECT_PACK / ".apm" / "agents" / f"{AGENT_NAME}.md").exists(),
            "architect must ship .apm/agents/design-reviewer.md",
        )

    def test_allowed_adapters_are_the_expected_seven(self) -> None:
        # Pin the seven so this test (and AC10's "all seven") stays honest if the
        # list ever changes — update deliberately, with the projection re-checked.
        self.assertEqual(
            set(self.adapters),
            {"claude-code", "codex", "copilot", "kiro-ide", "kiro-cli", "cursor", "gemini"},
        )

    def test_design_reviewer_projects_for_every_allowed_adapter(self) -> None:
        for adapter in self.adapters:
            with self.subTest(adapter=adapter):
                self.assertIn(adapter, ADAPTERS, f"no projector registered for {adapter!r}")
                with tempfile.TemporaryDirectory() as tmp:
                    out = Path(tmp) / "out"
                    ADAPTERS[adapter](ARCHITECT_PACK, self.contract, out)
                    hits = list(out.rglob(f"{AGENT_NAME}*"))
                    self.assertTrue(
                        hits,
                        f"{adapter}: design-reviewer agent did not project under {out}",
                    )
                    self.assertTrue(
                        any("agents" in h.parts for h in hits),
                        f"{adapter}: design-reviewer projected but not under an agents/ route: {hits}",
                    )


if __name__ == "__main__":
    unittest.main()
