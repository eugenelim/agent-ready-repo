"""Tests for adapter-contract v0.7 (RFC-0012 / repo-scope-per-adapter-projection).

Verifies the T1 atomic edit landed:

  - ``[contract] version == "0.7"`` (AC1).
  - ``[adapter.copilot.scope]`` exists with ``repo = "."``,
    ``allowed-prefixes.repo = [".github/instructions/"]``, and NO ``user``
    key (AC2 — Copilot is admissible at repo scope only).
  - Every shipped adapter declares ``allowed-prefixes.repo`` as a
    non-empty list of trailing-slash strings (AC2 + AC4).
  - Pre-existing ``allowed-prefixes.user`` invariants survive the edit
    (property-based, not snapshot — header-comment edits and list-order
    changes are out of scope).
  - The schema validator refuses a fixture contract that omits the
    ``repo`` key from any adapter's ``scope`` table (AC4 — validator
    pins the v0.7 invariant).
"""

from __future__ import annotations

import copy
import json
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
DATA_CONTRACT_PATH = (
    REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / "adapter.toml"
)
DATA_SCHEMA_PATH = (
    REPO_ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / "adapter.schema.json"
)


class TestContractV07(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = tomllib.loads(DATA_CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_contract_version_is_07(self) -> None:
        self.assertEqual(self.contract["contract"]["version"], "0.7")

    def test_copilot_scope_table_shape(self) -> None:
        copilot_scope = self.contract["adapter"]["copilot"].get("scope")
        self.assertIsNotNone(copilot_scope, "copilot scope table missing")
        self.assertEqual(copilot_scope["repo"], ".")
        self.assertEqual(
            copilot_scope["allowed-prefixes"]["repo"],
            [".github/instructions/"],
        )
        self.assertNotIn(
            "user",
            copilot_scope,
            "copilot scope must not declare a user root at v0.7",
        )
        self.assertNotIn(
            "user",
            copilot_scope.get("allowed-prefixes", {}),
            "copilot must not declare allowed-prefixes.user at v0.7",
        )

    def test_every_adapter_has_allowed_prefixes_repo(self) -> None:
        for name, block in self.contract["adapter"].items():
            with self.subTest(adapter=name):
                scope = block.get("scope")
                self.assertIsNotNone(
                    scope, f"adapter {name!r} has no scope table at v0.7"
                )
                repo_prefixes = scope.get("allowed-prefixes", {}).get("repo")
                self.assertIsInstance(
                    repo_prefixes,
                    list,
                    f"adapter {name!r} missing allowed-prefixes.repo",
                )
                self.assertTrue(
                    repo_prefixes,
                    f"adapter {name!r} allowed-prefixes.repo is empty",
                )
                for entry in repo_prefixes:
                    self.assertTrue(
                        entry.endswith("/"),
                        f"adapter {name!r} prefix {entry!r} must end with '/'",
                    )

    def test_existing_user_prefixes_invariants(self) -> None:
        """Property-based assertion — every user-scope-capable adapter's
        prefix list still carries its load-bearing entries. The form
        survives header-comment edits and list-order changes (avoiding a
        snapshot fixture that would be its own maintenance surface)."""
        cc = self.contract["adapter"]["claude-code"]["scope"]
        cc_user = cc["allowed-prefixes"]["user"]
        self.assertIn(".claude/", cc_user)
        self.assertIn(".agentbundle/", cc_user)

        kiro = self.contract["adapter"]["kiro"]["scope"]
        kiro_user = kiro["allowed-prefixes"]["user"]
        self.assertIn(".kiro/", kiro_user)
        self.assertIn(".agentbundle/", kiro_user)

        codex = self.contract["adapter"]["codex"]["scope"]
        codex_user = codex["allowed-prefixes"]["user"]
        self.assertIn(".agents/skills/", codex_user)
        self.assertIn(".agentbundle/", codex_user)

    def test_schema_refuses_repo_omission(self) -> None:
        """AC4 — fixture contract with the ``repo`` key removed from any
        adapter's scope table fails validation."""
        from agentbundle.build.validate import validate

        schema = json.loads(DATA_SCHEMA_PATH.read_text(encoding="utf-8"))
        broken = copy.deepcopy(self.contract)
        # Strip ``repo`` from claude-code's scope table.
        del broken["adapter"]["claude-code"]["scope"]["repo"]
        errors = validate(broken, schema)
        self.assertTrue(
            errors,
            "schema accepted a scope table missing the 'repo' key",
        )

    def test_schema_refuses_allowed_prefixes_repo_omission(self) -> None:
        """AC4 — fixture contract with ``allowed-prefixes.repo`` removed
        from any adapter's scope table fails validation."""
        from agentbundle.build.validate import validate

        schema = json.loads(DATA_SCHEMA_PATH.read_text(encoding="utf-8"))
        broken = copy.deepcopy(self.contract)
        del broken["adapter"]["kiro"]["scope"]["allowed-prefixes"]["repo"]
        errors = validate(broken, schema)
        self.assertTrue(
            errors,
            "schema accepted a scope table missing allowed-prefixes.repo",
        )


if __name__ == "__main__":
    unittest.main()
