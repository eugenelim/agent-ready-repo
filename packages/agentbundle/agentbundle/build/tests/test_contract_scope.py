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
    """Contract version: bumped to 0.2 by RFC-0004, then to 0.3 by RFC-0005,
    then to 0.4 by RFC-0008 (T2 / spec claude-plugins-install-route), then to
    0.5 by RFC-0010 (T2 / spec apm-install-route-parity), then to 0.6 by
    RFC-0011 / pack-allowed-adapters (codex user-scope table), then to 0.7
    by RFC-0012 / repo-scope-per-adapter-projection (every adapter declares
    `allowed-prefixes.repo`; copilot gains a scope table) and RFC-0013 /
    credential-broker-contract (governance bump) co-residing at v0.7, then
    to 0.8 by docs/specs/dropped-primitives-coverage (codex agent +
    hook-wiring move from `dropped` to first-class projections)."""

    def test_contract_version_is_0_5(self) -> None:
        # Class/method name preserved; exact version lives in test_contract.py.
        # Assert >= 0.8 so v0.8 scope features survive future bumps.
        contract = _load_contract()
        self.assertGreaterEqual(contract["contract"]["version"], "0.8")


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
        self.assertEqual(prefixes, [".claude/", ".agentbundle/"])

    def test_contract_validates_against_schema(self) -> None:
        from agentbundle.build.validate import validate

        errors = validate(_load_contract(), _load_schema())
        self.assertEqual(errors, [], f"v0.2 contract did not validate: {errors}")


class OtherAdaptersOmitScopeTests(unittest.TestCase):
    """v0.3 (RFC-0005) adds a `[scope]` table to Kiro alongside Claude
    Code's existing one; v0.6 (RFC-0011) adds one to Codex; v0.7
    (RFC-0012) adds one to Copilot — every shipped adapter now carries
    a `[scope]` table at v0.7."""

    def test_copilot_has_scope_per_rfc_0012(self) -> None:
        contract = _load_contract()
        scope = contract["adapter"]["copilot"].get("scope")
        self.assertIsNotNone(scope, "copilot [scope] block missing at v0.7")
        self.assertEqual(scope["repo"], ".")
        # Two repo prefixes: `.github/instructions/` (skill /
        # instruction target) and `tools/hooks/` (legacy hook-body
        # target — copilot's hook-body array entry still projects
        # there).
        self.assertEqual(
            scope["allowed-prefixes"]["repo"],
            [".github/instructions/", "tools/hooks/"],
        )
        # Copilot is admissible at repo scope only — no user-scope analogue
        # exists in the Copilot ecosystem (RFC-0012).
        self.assertNotIn("user", scope)
        self.assertNotIn("user", scope.get("allowed-prefixes", {}))

    def test_codex_has_scope_per_rfc_0011(self) -> None:
        contract = _load_contract()
        scope = contract["adapter"]["codex"].get("scope")
        self.assertIsNotNone(scope, "Codex [scope] block missing (RFC-0011)")
        self.assertEqual(scope["repo"], ".")
        self.assertEqual(scope["user"], "~")
        # v0.8 (dropped-primitives-coverage) adds `.codex/` to allow
        # codex agent + hook-wiring projection.
        self.assertEqual(
            scope["allowed-prefixes"]["user"],
            [".agents/skills/", ".codex/", ".agentbundle/"],
        )

    def test_kiro_has_scope_per_rfc_0005(self) -> None:
        contract = _load_contract()
        scope = contract["adapter"]["kiro"].get("scope")
        self.assertIsNotNone(scope, "Kiro [scope] block missing")
        self.assertEqual(scope["repo"], ".")
        self.assertEqual(scope["user"], "~")

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
        for good in (".claude/", ".agentbundle/", "deep/nested/path/"):
            with self.subTest(value=good):
                self.assertEqual(
                    validate(good, schema),
                    [],
                    f"pattern rejected legal value: {good!r}",
                )


if __name__ == "__main__":
    unittest.main()
