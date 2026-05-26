"""Tests for adapter-contract v0.7 (RFC-0012 / repo-scope-per-adapter-projection
and RFC-0013 / credential-broker-contract co-residing at v0.7).

Verifies the T1 edits landed:

  - ``[contract] version == "0.7"`` in both the runtime data file
    (`_data/adapter.toml`) and the docs mirror
    (`docs/contracts/adapter.toml`). The two files must stay byte-
    aligned per the v0.3-schema sync test; this module pins the
    version on both as belt-and-braces (AC1 for both RFCs).
  - **RFC-0012 surface:**
    * ``[adapter.copilot.scope]`` exists with ``repo = "."``,
      ``allowed-prefixes.repo`` enumerating the per-IDE skill /
      hook-body targets, and NO ``user`` key (Copilot is admissible
      at repo scope only).
    * Every shipped adapter declares ``allowed-prefixes.repo`` as a
      non-empty list of trailing-slash strings.
    * Schema validator refuses fixtures that omit the ``repo`` key
      or ``allowed-prefixes.repo`` from any adapter's scope table.
  - **RFC-0013 surface:**
    * Each user-scope-capable adapter (`claude-code`, `kiro`, `codex`)
      still carries `.agentbundle/` in `allowed-prefixes.user`
      (non-regression — the prefix is what `metadata.auth: creds`
      writes its credential cache under).
  - Property-based ``allowed-prefixes.user`` invariants for every
    user-scope-capable adapter (header-comment edits and
    list-order changes don't trip the assertion).
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
DOCS_CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"
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
        self.docs_contract = tomllib.loads(
            DOCS_CONTRACT_PATH.read_text(encoding="utf-8")
        )

    def test_contract_version_is_07(self) -> None:
        """RFC-0012 + RFC-0013 co-residing at v0.7 on the runtime file."""
        self.assertEqual(self.contract["contract"]["version"], "0.7")

    def test_docs_contract_version_is_07(self) -> None:
        """RFC-0013 AC1 — docs mirror also pinned at v0.7."""
        self.assertEqual(self.docs_contract["contract"]["version"], "0.7")

    def test_copilot_scope_table_shape(self) -> None:
        copilot_scope = self.contract["adapter"]["copilot"].get("scope")
        self.assertIsNotNone(copilot_scope, "copilot scope table missing")
        self.assertEqual(copilot_scope["repo"], ".")
        # `.github/instructions/` is the Copilot skill / instruction
        # target; `tools/hooks/` is the legacy hook-body target
        # (matching copilot's hook-body array entry).
        self.assertEqual(
            copilot_scope["allowed-prefixes"]["repo"],
            [".github/instructions/", "tools/hooks/"],
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
        prefix list still carries its load-bearing entries. RFC-0013's
        `.agentbundle/` non-regression rolls into this same shape."""
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

    def test_all_user_scope_adapters_carry_agentbundle_prefix(self) -> None:
        """RFC-0013 AC2 — `.agentbundle/` is the credential-cache root
        every user-scope-capable adapter must admit."""
        for adapter in ("claude-code", "kiro", "codex"):
            with self.subTest(adapter=adapter):
                prefixes = (
                    self.contract["adapter"][adapter]["scope"]
                    ["allowed-prefixes"]["user"]
                )
                self.assertIn(
                    ".agentbundle/", prefixes,
                    f"{adapter} user-scope allowed-prefixes must include "
                    f"'.agentbundle/' (got {prefixes!r})",
                )

    def test_schema_refuses_repo_omission(self) -> None:
        """RFC-0012 AC4 — fixture contract with the ``repo`` key removed
        from any adapter's scope table fails validation."""
        from agentbundle.build.validate import validate

        schema = json.loads(DATA_SCHEMA_PATH.read_text(encoding="utf-8"))
        broken = copy.deepcopy(self.contract)
        del broken["adapter"]["claude-code"]["scope"]["repo"]
        errors = validate(broken, schema)
        self.assertTrue(
            errors,
            "schema accepted a scope table missing the 'repo' key",
        )

    def test_schema_refuses_allowed_prefixes_repo_omission(self) -> None:
        """RFC-0012 AC4 — fixture contract with ``allowed-prefixes.repo``
        removed from any adapter's scope table fails validation."""
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
