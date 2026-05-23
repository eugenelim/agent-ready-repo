"""Tests for the RFC-0004 v0.2 `[scope]` table on the adapter contract.

Verifies AC #14 (RFC-0004) for the distribution-adapters spec:
  - adapter.schema.json accepts a well-formed [adapter.<name>.scope] block.
  - adapter.schema.json rejects each malformed `allowed-prefixes.user` shape
    enumerated in the spec: ["/"], [""], ["../"], [".."],
    ["no-trailing-slash"], ["/begins-with-slash/"], and [].
  - adapter.toml validates against the v0.2 schema with [contract] version =
    "0.2" and the two-prefix [adapter."claude-code".scope] block.
  - The other three reference adapters (kiro, copilot, codex) omit the
    optional [scope] block and remain valid.
"""

from __future__ import annotations

import copy
import json
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"
SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.schema.json"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_contract() -> dict:
    return tomllib.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


class ContractVersionTests(unittest.TestCase):
    """Contract version bumps to 0.2 with this RFC."""

    def test_contract_version_is_0_2(self) -> None:
        contract = _load_contract()
        self.assertEqual(contract["contract"]["version"], "0.2")


class ClaudeCodeScopeBlockTests(unittest.TestCase):
    """The Claude Code adapter declares the v0.2 [scope] block."""

    def test_claude_code_scope_present(self) -> None:
        contract = _load_contract()
        scope = contract["adapter"]["claude-code"].get("scope")
        self.assertIsNotNone(scope, "Claude Code [scope] block missing")
        self.assertEqual(scope["repo"], ".")
        self.assertEqual(scope["user"], "~")

    def test_claude_code_allowed_prefixes_user_two_entries(self) -> None:
        """Two prefixes ship: projected primitives + CLI infrastructure."""
        contract = _load_contract()
        prefixes = (
            contract["adapter"]["claude-code"]["scope"]["allowed-prefixes"]["user"]
        )
        self.assertEqual(prefixes, [".claude/", ".agent-ready/"])

    def test_contract_validates_against_schema(self) -> None:
        from agentbundle.build.validate import validate

        errors = validate(_load_contract(), _load_schema())
        self.assertEqual(errors, [], f"v0.2 contract did not validate: {errors}")


class OtherAdaptersOmitScopeTests(unittest.TestCase):
    """Adapters omitting [scope] are accepted as repo-only."""

    def test_kiro_copilot_codex_omit_scope(self) -> None:
        contract = _load_contract()
        for name in ("kiro", "copilot", "codex"):
            with self.subTest(adapter=name):
                self.assertNotIn("scope", contract["adapter"][name])

    def test_contract_minus_claude_code_scope_still_valid(self) -> None:
        from agentbundle.build.validate import validate

        contract = _load_contract()
        contract["adapter"]["claude-code"].pop("scope", None)
        errors = validate(contract, _load_schema())
        self.assertEqual(errors, [], f"validate rejected scope-less contract: {errors}")


class AllowedPrefixesRejectionTests(unittest.TestCase):
    """`allowed-prefixes.<scope>` constraints — every bad shape is rejected."""

    def _validate_with_prefixes(self, prefixes: list[str]) -> list[str]:
        from agentbundle.build.validate import validate

        schema = _load_schema()
        contract = _load_contract()
        contract["adapter"]["claude-code"]["scope"]["allowed-prefixes"]["user"] = list(prefixes)
        return validate(contract, schema)

    def test_rejects_root_only(self) -> None:
        errors = self._validate_with_prefixes(["/"])
        self.assertTrue(errors, "schema accepted allowed-prefixes.user = ['/']")

    def test_rejects_empty_string(self) -> None:
        errors = self._validate_with_prefixes([""])
        self.assertTrue(errors, "schema accepted allowed-prefixes.user = ['']")

    def test_rejects_dotdot_slash(self) -> None:
        errors = self._validate_with_prefixes(["../"])
        self.assertTrue(errors, "schema accepted allowed-prefixes.user = ['../']")

    def test_rejects_bare_dotdot(self) -> None:
        errors = self._validate_with_prefixes([".."])
        self.assertTrue(errors, "schema accepted allowed-prefixes.user = ['..']")

    def test_rejects_no_trailing_slash(self) -> None:
        errors = self._validate_with_prefixes(["no-trailing-slash"])
        self.assertTrue(errors, "schema accepted allowed-prefixes.user = ['no-trailing-slash']")

    def test_rejects_leading_slash(self) -> None:
        errors = self._validate_with_prefixes(["/begins-with-slash/"])
        self.assertTrue(errors, "schema accepted allowed-prefixes.user = ['/begins-with-slash/']")

    def test_rejects_empty_array(self) -> None:
        errors = self._validate_with_prefixes([])
        self.assertTrue(errors, "schema accepted allowed-prefixes.user = []")

    def test_rejects_dotdot_in_middle(self) -> None:
        """Defence in depth: `..` as an interior segment is also rejected."""
        errors = self._validate_with_prefixes([".claude/../etc/"])
        self.assertTrue(errors, "schema accepted allowed-prefixes.user = ['.claude/../etc/']")

    def test_accepts_nested_path(self) -> None:
        """A nested path like `.claude/skills/` is legal — non-empty, trailing /."""
        errors = self._validate_with_prefixes([".claude/skills/"])
        self.assertEqual(errors, [], f"schema rejected nested path: {errors}")


class StdlibValidatorExtensionsTests(unittest.TestCase):
    """Cross-keyword tests for the validator extensions T10 needs."""

    def test_min_items_rejects_short_array(self) -> None:
        from agentbundle.build.validate import validate

        schema = {"type": "array", "minItems": 1}
        self.assertTrue(validate([], schema))
        self.assertEqual(validate(["a"], schema), [])

    def test_pattern_rejects_dotdot_segment(self) -> None:
        from agentbundle.build.validate import validate

        # The exact pattern shipped on allowed-prefixes.<scope>.items.
        pattern = r"^((?!\.\.(\/|$))[^/]+/)+$"
        schema = {"type": "string", "pattern": pattern}
        for bad in ("../", "..", "/", "", "no-slash", "/abs/"):
            with self.subTest(value=bad):
                self.assertTrue(
                    validate(bad, schema),
                    f"pattern accepted forbidden value: {bad!r}",
                )
        for good in (".claude/", ".agent-ready/", "deep/nested/path/"):
            with self.subTest(value=good):
                self.assertEqual(
                    validate(good, schema),
                    [],
                    f"pattern rejected legal value: {good!r}",
                )


if __name__ == "__main__":
    unittest.main()
