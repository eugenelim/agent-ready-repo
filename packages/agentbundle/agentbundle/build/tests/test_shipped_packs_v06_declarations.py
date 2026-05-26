"""T4 tests for the four shipped user-scope packs' v0.6 declarations
(RFC-0011 / pack-allowed-adapters AC4, AC5).

The four credentialed / portable packs (`atlassian`, `figma`,
`converters`, `contracts`) bump to v0.6 and declare
`allowed-adapters = ["claude-code", "kiro", "codex"]`. The four
repo-only packs (`core`, `governance-extras`, `user-guide-diataxis`,
`monorepo-extras`) do NOT bump — they project everywhere by default
at repo scope.
"""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
PACKS_DIR = REPO_ROOT / "packs"


def _load_pack_toml(name: str) -> dict:
    return tomllib.loads((PACKS_DIR / name / "pack.toml").read_text(encoding="utf-8"))


USER_SCOPE_PACKS = ("atlassian", "figma", "converters", "contracts")
REPO_ONLY_PACKS = ("core", "governance-extras", "user-guide-diataxis", "monorepo-extras")


class TestUserScopePacksV06(unittest.TestCase):
    def test_user_scope_packs_declare_v06_and_three_adapters(self) -> None:
        for name in USER_SCOPE_PACKS:
            with self.subTest(pack=name):
                pack = _load_pack_toml(name)
                self.assertEqual(
                    pack["pack"]["adapter-contract"]["version"],
                    "0.6",
                    f"{name} should bump to v0.6",
                )
                self.assertEqual(
                    pack["pack"]["install"]["allowed-adapters"],
                    ["claude-code", "kiro", "codex"],
                    f"{name} declared adapter set wrong",
                )


class TestRepoOnlyPacksUnchanged(unittest.TestCase):
    def test_repo_only_packs_do_not_declare_allowed_adapters(self) -> None:
        for name in REPO_ONLY_PACKS:
            with self.subTest(pack=name):
                pack = _load_pack_toml(name)
                install = pack.get("pack", {}).get("install", {})
                # Repo-only packs may or may not have an install table;
                # either way, no allowed-adapters declared.
                self.assertNotIn(
                    "allowed-adapters",
                    install,
                    f"{name} unexpectedly declares allowed-adapters",
                )


if __name__ == "__main__":
    unittest.main()
