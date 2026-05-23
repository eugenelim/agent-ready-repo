"""T11: `pack.schema.json` enforces `[pack.install]` under contract v0.2.

Verifies AC #15 (RFC-0004) for the distribution-adapters spec. Six test
rows from the plan:

  1. A v0.2 pack with no [pack.install] table is rejected.
  2. A v0.2 pack with default-scope="repo", allowed-scopes=["repo"] accepted.
  3. A v0.2 pack with default-scope="user", allowed-scopes=["repo"] rejected
     by the default-scope ∈ allowed-scopes invariant.
  4. A v0.2 pack omitting allowed-scopes (only default-scope declared) is
     accepted — the implied `[default-scope]` default lands at CLI
     consumption time, not at schema validation time.
  5. A v0.1 pack (declares 0.1 or omits the adapter-contract field) without
     [pack.install] is accepted (legacy).
  6. A v0.1 pack carrying a stray [pack.install] table is accepted — the
     table is ignored at CLI consumption time.

The cross-field invariant lives in `pack.schema.json` (jsonschema
`if`/`then`) so catalogue indexers and third-party validators refuse a
malformed pack identically.

Tests live in a new file (not extending test_pack_schema.py owned by T1c)
to avoid the merge-conflict pattern the plan calls out for parallel
worktrees.
"""

from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
PACK_SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "pack.schema.json"


def _load_schema() -> dict:
    return json.loads(PACK_SCHEMA_PATH.read_text(encoding="utf-8"))


def _parse(toml_text: str) -> dict:
    return tomllib.loads(toml_text)


class V02PackInstallRequiredTests(unittest.TestCase):
    """Row 1: v0.2 pack without [pack.install] is rejected."""

    def test_v02_without_install_rejected(self) -> None:
        from agentbundle.build.validate import validate

        instance = _parse(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"
"""
        )
        errors = validate(instance, _load_schema())
        self.assertTrue(errors, "v0.2 pack without [pack.install] was accepted")
        self.assertTrue(
            any("install" in e for e in errors),
            f"error should name 'install'; got: {errors}",
        )


class V02PackInstallValidTests(unittest.TestCase):
    """Row 2: v0.2 pack with a well-formed install table is accepted."""

    def test_v02_with_valid_install_accepted(self) -> None:
        from agentbundle.build.validate import validate

        instance = _parse(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
"""
        )
        errors = validate(instance, _load_schema())
        self.assertEqual(errors, [], f"valid v0.2 pack rejected: {errors}")


class DefaultInAllowedInvariantTests(unittest.TestCase):
    """Row 3: default-scope ∉ allowed-scopes is rejected."""

    def test_user_default_with_repo_only_allowed_rejected(self) -> None:
        from agentbundle.build.validate import validate

        instance = _parse(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "user"
allowed-scopes = ["repo"]
"""
        )
        errors = validate(instance, _load_schema())
        self.assertTrue(
            errors,
            "default-scope='user' with allowed-scopes=['repo'] was accepted",
        )

    def test_repo_default_with_user_only_allowed_rejected(self) -> None:
        """Mirror invariant: default-scope='repo' but allowed-scopes=['user']."""
        from agentbundle.build.validate import validate

        instance = _parse(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
allowed-scopes = ["user"]
"""
        )
        errors = validate(instance, _load_schema())
        self.assertTrue(
            errors,
            "default-scope='repo' with allowed-scopes=['user'] was accepted",
        )

    def test_both_scopes_allowed_with_user_default_accepted(self) -> None:
        """default='user' but allowed=['repo','user'] is fine."""
        from agentbundle.build.validate import validate

        instance = _parse(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "user"
allowed-scopes = ["repo", "user"]
"""
        )
        errors = validate(instance, _load_schema())
        self.assertEqual(errors, [], f"valid dual-scope pack rejected: {errors}")


class AllowedScopesOmittedTests(unittest.TestCase):
    """Row 4: omitting allowed-scopes is accepted.

    The implied `allowed-scopes = [default-scope]` is a CLI consumption-time
    behaviour (per § *Install-scope dimension*); the schema simply does not
    require the field.
    """

    def test_only_default_scope_accepted(self) -> None:
        from agentbundle.build.validate import validate

        instance = _parse(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
"""
        )
        errors = validate(instance, _load_schema())
        self.assertEqual(
            errors,
            [],
            f"pack with only default-scope was rejected: {errors}",
        )


class V01LegacyTests(unittest.TestCase):
    """Rows 5 + 6: v0.1 packs are accepted, with or without a stray install."""

    def test_v01_no_install_accepted(self) -> None:
        from agentbundle.build.validate import validate

        instance = _parse(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.1"
"""
        )
        errors = validate(instance, _load_schema())
        self.assertEqual(errors, [], f"v0.1 pack rejected: {errors}")

    def test_v01_omitting_adapter_contract_accepted(self) -> None:
        """A pack omitting [pack.adapter-contract] is treated as v0.1 — accepted."""
        from agentbundle.build.validate import validate

        instance = _parse(
            """
[pack]
name = "demo"
version = "0.1.0"
"""
        )
        errors = validate(instance, _load_schema())
        self.assertEqual(errors, [], f"adapter-contract-less pack rejected: {errors}")

    def test_v01_with_stray_install_accepted(self) -> None:
        """A v0.1 pack carrying a stray [pack.install] table is accepted.

        The schema must not validate the install table when the pack declares
        an older contract version; CLI consumption ignores the table per
        § *Install-scope dimension*. As long as the rest of the pack is
        well-formed, the pack is accepted.
        """
        from agentbundle.build.validate import validate

        instance = _parse(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.1"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
"""
        )
        errors = validate(instance, _load_schema())
        self.assertEqual(
            errors,
            [],
            f"v0.1 pack with stray install was rejected: {errors}",
        )


class AllowedScopesShapeTests(unittest.TestCase):
    """Allowed-scopes accepts only the two-value alphabet."""

    def test_allowed_scopes_unknown_value_rejected(self) -> None:
        from agentbundle.build.validate import validate

        instance = _parse(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo", "global"]
"""
        )
        errors = validate(instance, _load_schema())
        self.assertTrue(
            errors,
            "schema accepted unknown allowed-scopes value 'global'",
        )

    def test_allowed_scopes_empty_array_rejected(self) -> None:
        from agentbundle.build.validate import validate

        instance = {
            "pack": {
                "name": "demo",
                "version": "0.1.0",
                "adapter-contract": {"version": "0.2"},
                "install": {"default-scope": "repo", "allowed-scopes": []},
            }
        }
        errors = validate(instance, _load_schema())
        self.assertTrue(errors, "schema accepted allowed-scopes=[]")


if __name__ == "__main__":
    unittest.main()
