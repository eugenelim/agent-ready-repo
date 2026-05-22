"""Tests for pack.schema.json (T1c).

Verifies:
  - pack.schema.json accepts a governance-extras recommended-on-core
    example (AC 3).
  - pack.schema.json rejects a pack.toml missing [pack].
  - pack.schema.json rejects a pack.toml whose [pack.adaptation]
    infer-from value is a non-string.
  - pack.schema.json accepts a pack.toml without [pack.dependencies.required]
    (required array is optional).
  - pack.schema.json accepts [pack.seeds] entries that are relative-path
    strings, and rejects an absolute path or a non-string entry.
"""

from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
PACK_SCHEMA_PATH = (
    REPO_ROOT / "docs" / "contracts" / "pack.schema.json"
)


def _load_schema() -> dict:
    return json.loads(PACK_SCHEMA_PATH.read_text(encoding="utf-8"))


def _parse_toml(toml_text: str) -> dict:
    return tomllib.loads(toml_text)


class PackSchemaAcceptsValidExamplesTests(unittest.TestCase):
    """pack.schema.json accepts well-formed pack.toml structures."""

    def test_accepts_governance_extras_recommended_on_core(self) -> None:
        """Modeled on RFC-0001's governance-extras recommended-on-core example.

        Verifies AC 3: the schema accepts [pack], [pack.dependencies] with a
        recommended array of {catalogue, pack, version} objects.
        """
        from agentbundle.build.validate import validate

        schema = _load_schema()
        toml_text = """
[pack]
name = "governance-extras"
version = "0.1.0"
description = "RFC/ADR ceremony skills (new-rfc, new-adr, update-conventions)."

[pack.dependencies]
recommended = [
  { catalogue = "agent-ready-repo", pack = "core", version = ">=0.1.0" },
]
"""
        instance = _parse_toml(toml_text)
        errors = validate(instance, schema)
        self.assertEqual(
            errors,
            [],
            f"schema rejected valid governance-extras example:\n" + "\n".join(errors),
        )

    def test_accepts_pack_without_dependencies_required(self) -> None:
        """A pack.toml without [pack.dependencies.required] is valid.

        The required array is optional — missing-optional != malformed.
        """
        from agentbundle.build.validate import validate

        schema = _load_schema()
        toml_text = """
[pack]
name = "governance-extras"
version = "0.1.0"
description = "RFC/ADR ceremony skills."

[pack.dependencies]
recommended = [
  { catalogue = "agent-ready-repo", pack = "core", version = ">=0.1.0" },
]
"""
        instance = _parse_toml(toml_text)
        errors = validate(instance, schema)
        self.assertEqual(
            errors,
            [],
            f"schema rejected pack without dependencies.required:\n"
            + "\n".join(errors),
        )

    def test_accepts_pack_without_any_dependencies(self) -> None:
        """A pack.toml with no [pack.dependencies] section at all is valid."""
        from agentbundle.build.validate import validate

        schema = _load_schema()
        toml_text = """
[pack]
name = "core"
version = "0.1.0"
description = "Core agent skills."
"""
        instance = _parse_toml(toml_text)
        errors = validate(instance, schema)
        self.assertEqual(
            errors,
            [],
            f"schema rejected pack without any dependencies:\n" + "\n".join(errors),
        )

    def test_accepts_seeds_with_relative_paths(self) -> None:
        """[pack.seeds] entries that are relative-path strings are accepted.

        Verifies the [pack.seeds] shape clause of AC 3.
        """
        from agentbundle.build.validate import validate

        schema = _load_schema()
        toml_text = """
[pack]
name = "core"
version = "0.1.0"
description = "Core agent skills."
seeds = ["AGENTS.md", "docs/CHARTER.md", "docs/CONVENTIONS.md"]
"""
        instance = _parse_toml(toml_text)
        errors = validate(instance, schema)
        self.assertEqual(
            errors,
            [],
            f"schema rejected valid relative-path seeds:\n" + "\n".join(errors),
        )


class PackSchemaRejectsInvalidExamplesTests(unittest.TestCase):
    """pack.schema.json rejects malformed pack.toml structures."""

    def test_rejects_missing_pack_section(self) -> None:
        """A pack.toml without a [pack] section is rejected."""
        from agentbundle.build.validate import validate

        schema = _load_schema()
        # Instance missing the required "pack" key entirely.
        instance = {"metadata": {"name": "orphan"}}
        errors = validate(instance, schema)
        self.assertTrue(
            errors,
            "schema accepted a document missing the required [pack] section",
        )
        self.assertTrue(
            any("pack" in e for e in errors),
            f"error message should mention 'pack'; got: {errors}",
        )

    def test_rejects_adaptation_infer_from_non_string(self) -> None:
        """[pack.adaptation] infer-from must be a string; non-string is rejected.

        Shape-only check; the semantic set of legal values lives in the
        adapt-to-project skill (out of scope here).
        """
        from agentbundle.build.validate import validate

        schema = _load_schema()
        toml_text = """
[pack]
name = "core"
version = "0.1.0"

[pack.adaptation]
infer-from = 42
"""
        instance = _parse_toml(toml_text)
        errors = validate(instance, schema)
        self.assertTrue(
            errors,
            "schema accepted [pack.adaptation] infer-from as a non-string (integer)",
        )

    def test_rejects_adaptation_substitution_infer_from_non_string(self) -> None:
        """infer-from inside a substitutions entry must be a string."""
        from agentbundle.build.validate import validate

        schema = _load_schema()
        # Build the instance directly because TOML inline-table syntax
        # would require tomllib to parse the mixed-type array, which is
        # not the goal here — this verifies the schema constraint itself.
        instance = {
            "pack": {
                "name": "core",
                "version": "0.1.0",
                "adaptation": {
                    "substitutions": [
                        {"marker": "<adapt:project-name>", "infer-from": 99}
                    ]
                },
            }
        }
        errors = validate(instance, schema)
        self.assertTrue(
            errors,
            "schema accepted substitutions[].infer-from as non-string (integer)",
        )

    def test_rejects_seeds_with_absolute_path(self) -> None:
        """A seeds entry starting with '/' is an absolute path and must be rejected.

        Verifies the [pack.seeds] shape clause of AC 3.
        """
        from agentbundle.build.validate import validate

        schema = _load_schema()
        toml_text = """
[pack]
name = "core"
version = "0.1.0"
seeds = ["/etc/foo"]
"""
        instance = _parse_toml(toml_text)
        errors = validate(instance, schema)
        self.assertTrue(
            errors,
            "schema accepted an absolute path in seeds (must start with non-'/')",
        )

    def test_rejects_seeds_with_non_string_entry(self) -> None:
        """A seeds entry that is not a string (e.g. an inline table) is rejected.

        Verifies the [pack.seeds] shape clause of AC 3.
        """
        from agentbundle.build.validate import validate

        schema = _load_schema()
        # Cannot express an inline-table in a seeds array via TOML easily
        # for this validator, so construct the instance dict directly.
        instance = {
            "pack": {
                "name": "core",
                "version": "0.1.0",
                "seeds": [{"path": "AGENTS.md"}],  # dict, not string
            }
        }
        errors = validate(instance, schema)
        self.assertTrue(
            errors,
            "schema accepted a non-string (dict) entry in seeds",
        )


class PackSchemaLoadsTests(unittest.TestCase):
    """Smoke test: the schema file loads and has the expected top-level shape."""

    def test_schema_loads(self) -> None:
        schema = _load_schema()
        self.assertEqual(schema.get("type"), "object")

    def test_schema_requires_pack(self) -> None:
        schema = _load_schema()
        self.assertIn("pack", schema.get("required", []))


if __name__ == "__main__":
    unittest.main()
