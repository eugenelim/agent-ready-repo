"""Tests for adapter-contract v0.6 (RFC-0011 / pack-allowed-adapters).

Verifies the T1 atomic edit landed:
  - `[contract] version == "0.6"` (AC1).
  - `[adapter.codex.scope]` table shape (AC2).
  - The two existing user-scope-capable adapters' scope tables
    (claude-code, kiro) are unchanged by this PR — compared as parsed
    table bodies, not file bytes, so unrelated header-comment edits
    don't break the assertion.
"""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
DATA_CONTRACT_PATH = (
    REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / "adapter.toml"
)


# Snapshot of the v0.5 [adapter.claude-code.scope] and [adapter.kiro.scope]
# table bodies, captured before T1 landed. The "no other scope table
# modified" test compares the parsed v0.6 contract against these dicts.
V05_CLAUDE_CODE_SCOPE = {
    "repo": ".",
    "user": "~",
    "allowed-prefixes": {"user": [".claude/", ".agentbundle/"]},
}

V05_KIRO_SCOPE = {
    "repo": ".",
    "user": "~",
    "allowed-prefixes": {"user": [".kiro/", ".agentbundle/"]},
}


class TestContractV06(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = tomllib.loads(DATA_CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_contract_version_is_06(self) -> None:
        self.assertEqual(self.contract["contract"]["version"], "0.6")

    def test_codex_scope_table_shape(self) -> None:
        codex_scope = self.contract["adapter"]["codex"]["scope"]
        self.assertEqual(codex_scope["repo"], ".")
        self.assertEqual(codex_scope["user"], "~")
        self.assertEqual(
            codex_scope["allowed-prefixes"]["user"],
            [".agents/skills/", ".agentbundle/"],
        )

    def test_no_other_scope_table_modified(self) -> None:
        # Parsed-body equality (not byte-identity) so header-comment edits
        # in T1 itself don't trip the assertion.
        cc_scope = self.contract["adapter"]["claude-code"]["scope"]
        kiro_scope = self.contract["adapter"]["kiro"]["scope"]
        self.assertEqual(cc_scope, V05_CLAUDE_CODE_SCOPE)
        self.assertEqual(kiro_scope, V05_KIRO_SCOPE)


if __name__ == "__main__":
    unittest.main()
