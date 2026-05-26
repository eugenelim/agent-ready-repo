"""Tests for T7 of docs/specs/dropped-primitives-coverage — the eight
shipped packs declare ``[pack.adapter-contract] version = "0.8"``.

Per spec AC12, exactly these eight packs bump in this PR:

  - atlassian, figma, converters, contracts (the four credentialed /
    consumer packs).
  - core, governance-extras, user-guide-diataxis, monorepo-extras (the
    four scaffold packs).

Two other packs in-tree are NOT bumped here:

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

    def test_eight_packs_declare_v08(self) -> None:
        """Exactly eight pack.tomls in-tree declare v0.8 — the named set
        above. A future pack landing at v0.8 should add itself to this
        list explicitly so the test surfaces the new declaration."""
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
