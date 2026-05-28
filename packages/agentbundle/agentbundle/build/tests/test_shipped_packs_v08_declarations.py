"""Tests for T7 of docs/specs/dropped-primitives-coverage — the shipped
packs declaring ``[pack.adapter-contract] version = "0.8"``.

Per `dropped-primitives-coverage` AC12, eight packs bumped to v0.8:

  - atlassian, figma, converters, contracts (the four credentialed /
    consumer packs).
  - core, governance-extras, user-guide-diataxis, monorepo-extras (the
    four scaffold packs).

The `research` pack (shipped later by the `research-pack` spec) also
declares v0.8 at birth, bringing the in-tree v0.8 set to nine. A future
pack landing at v0.8 should add itself to ``V08_PACKS`` so this test
surfaces the new declaration.

Two other packs in-tree are NOT at v0.8:

  - ``architect``: still at v0.6 (older, pre-RFC-0013).
  - ``credential-brokers``: still at v0.7 (RFC-0013 shipped on v0.7 and
    a v0.7 pack continues to work under v0.8 — the legacy resolver path
    for codex drops agents/hooks per the v0.7 contract, fine for
    backward compat).
"""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
PACKS_DIR = REPO_ROOT / "packs"

V08_PACKS = (
    "atlassian",
    "contracts",
    "converters",
    "core",
    "figma",
    "governance-extras",
    "monorepo-extras",
    "research",
    "user-guide-diataxis",
)


class TestShippedPacksDeclareV08(unittest.TestCase):
    def test_each_named_pack_declares_v08(self) -> None:
        for name in V08_PACKS:
            with self.subTest(pack=name):
                pack_toml = PACKS_DIR / name / "pack.toml"
                self.assertTrue(pack_toml.exists(), f"missing {pack_toml}")
                data = tomllib.loads(pack_toml.read_text(encoding="utf-8"))
                version = data.get("pack", {}).get("adapter-contract", {}).get("version")
                self.assertEqual(
                    version,
                    "0.8",
                    f"pack {name!r} expected adapter-contract.version='0.8', got {version!r}",
                )

    def test_shipped_v08_packs_match_named_set(self) -> None:
        """The pack.tomls in-tree declaring v0.8 are exactly ``V08_PACKS``.
        A future pack landing at v0.8 should add itself to that tuple
        explicitly so this test surfaces the new declaration."""
        v08_seen: list[str] = []
        for pack_dir in sorted(PACKS_DIR.iterdir()):
            pack_toml = pack_dir / "pack.toml"
            if not pack_toml.exists():
                continue
            data = tomllib.loads(pack_toml.read_text(encoding="utf-8"))
            version = (
                data.get("pack", {}).get("adapter-contract", {}).get("version")
            )
            if version == "0.8":
                v08_seen.append(pack_dir.name)
        self.assertEqual(sorted(v08_seen), sorted(V08_PACKS))


if __name__ == "__main__":
    unittest.main()
