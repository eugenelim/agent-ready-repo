"""Tests for adapter-contract v0.7 (RFC-0013 / credential-broker-contract).

Verifies the T1 atomic edit landed:
  - `[contract] version == "0.7"` in both the runtime data file and the
    docs mirror (AC1).
  - `allowed-prefixes.user` for each of the three user-scope-capable
    adapters (`claude-code`, `kiro`, `codex`) contains `.agentbundle/`
    (AC2 non-regression — the prefix was added in earlier contract
    versions; this test pins the post-v0.7-bump state).
"""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
DATA_CONTRACT_PATH = (
    REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / "adapter.toml"
)
DOCS_CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"


class TestContractV07(unittest.TestCase):
    def setUp(self) -> None:
        self.data_contract = tomllib.loads(
            DATA_CONTRACT_PATH.read_text(encoding="utf-8")
        )
        self.docs_contract = tomllib.loads(
            DOCS_CONTRACT_PATH.read_text(encoding="utf-8")
        )

    def test_data_contract_version_is_07(self) -> None:
        self.assertEqual(self.data_contract["contract"]["version"], "0.7")

    def test_docs_contract_version_is_07(self) -> None:
        self.assertEqual(self.docs_contract["contract"]["version"], "0.7")

    def test_all_user_scope_adapters_carry_agentbundle_prefix(self) -> None:
        for adapter in ("claude-code", "kiro", "codex"):
            with self.subTest(adapter=adapter):
                prefixes = (
                    self.data_contract["adapter"][adapter]["scope"]
                    ["allowed-prefixes"]["user"]
                )
                self.assertIn(
                    ".agentbundle/", prefixes,
                    f"{adapter} user-scope allowed-prefixes must include "
                    f"'.agentbundle/' (got {prefixes!r})",
                )


if __name__ == "__main__":
    unittest.main()
