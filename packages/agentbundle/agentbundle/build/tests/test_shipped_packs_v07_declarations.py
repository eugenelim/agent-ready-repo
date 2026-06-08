"""Tests for the eight shipped packs' v0.7 declarations (RFC-0012 /
repo-scope-per-adapter-projection AC5-AC6).

Two cohorts:

  - Four user-scope-capable packs (`atlassian`, `figma`, `converters`,
    `contracts`) bump `[pack.adapter-contract] version` from 0.6 to
    0.7. `allowed-adapters` carries the RFC-0011 three-harness set,
    de-staled to current adapter names (`["claude-code", "kiro-ide",
    "codex"]`) — the bare `kiro` alias was renamed by RFC-0022.
  - Four repo-only packs (`core`, `governance-extras`,
    `user-guide-diataxis`, `monorepo-extras`) bump from 0.2 to 0.7 —
    load-bearing per Drawback #7: without this bump the legacy
    heuristic at step 5 still fires at repo scope for these packs and
    cannot return codex / copilot via the no-flag default. They remain
    implicit-default (no `allowed-adapters` declared).
"""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
PACKS_DIR = REPO_ROOT / "packs"

USER_SCOPE_PACKS = ("atlassian", "figma", "converters", "contracts")
REPO_ONLY_PACKS = ("core", "governance-extras", "user-guide-diataxis", "monorepo-extras")


def _load_pack_toml(name: str) -> dict:
    return tomllib.loads((PACKS_DIR / name / "pack.toml").read_text(encoding="utf-8"))


class TestUserScopePacksV07(unittest.TestCase):
    def test_user_scope_packs_bump_to_v07(self) -> None:
        """Test name preserved across bumps; the version assertion now
        pins v0.8 (post docs/specs/dropped-primitives-coverage T7).
        See test_shipped_packs_v08_declarations.py for the load-bearing
        v0.8 pin; this preserves the structural invariant that the
        four user-scope packs all share the same contract version."""
        for name in USER_SCOPE_PACKS:
            with self.subTest(pack=name):
                pack = _load_pack_toml(name)
                self.assertEqual(
                    pack["pack"]["adapter-contract"]["version"],
                    "0.8",
                    f"{name} must bump to v0.8",
                )

    def test_user_scope_packs_allowed_adapters(self) -> None:
        """allowed-adapters is the RFC-0011 three-harness set, de-staled
        to current adapter names (RFC-0022 renamed bare `kiro` →
        `kiro-ide`). The harness set is unchanged; only the spelling is."""
        for name in USER_SCOPE_PACKS:
            with self.subTest(pack=name):
                pack = _load_pack_toml(name)
                self.assertEqual(
                    pack["pack"]["install"]["allowed-adapters"],
                    ["claude-code", "kiro-ide", "codex"],
                    f"{name} declared adapter set wrong",
                )


class TestRepoOnlyPacksV07(unittest.TestCase):
    def test_repo_only_packs_bump_to_v07(self) -> None:
        """Drawback #7 mitigation — without the bump the legacy
        heuristic at step 5 fires at repo scope for these packs. Test
        name preserved; version assertion pins v0.8, except `core` which
        docs/specs/copilot-full-parity bumps to v0.10 (its 4 subagents +
        hook-wiring now project to copilot)."""
        expected = {
            "core": "0.10",
            "governance-extras": "0.8",
            "user-guide-diataxis": "0.8",
            "monorepo-extras": "0.8",
        }
        for name in REPO_ONLY_PACKS:
            with self.subTest(pack=name):
                pack = _load_pack_toml(name)
                self.assertEqual(
                    pack["pack"]["adapter-contract"]["version"],
                    expected[name],
                    f"{name} must declare contract v{expected[name]}",
                )

    def test_repo_only_packs_remain_implicit_default(self) -> None:
        """Repo-only packs declare no allowed-adapters — they project
        to every adapter when targeted via --adapter at repo scope."""
        for name in REPO_ONLY_PACKS:
            with self.subTest(pack=name):
                pack = _load_pack_toml(name)
                install = pack.get("pack", {}).get("install", {})
                self.assertNotIn(
                    "allowed-adapters",
                    install,
                    f"{name} unexpectedly declares allowed-adapters",
                )


if __name__ == "__main__":
    unittest.main()
