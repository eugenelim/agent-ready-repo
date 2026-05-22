"""Tests for plugin-manifest-schema.json (T1c).

Verifies:
  - plugin-manifest-schema.json accepts a minimal hand-authored
    .claude-plugin/plugin.json (AC 4).
  - The schema loads with the expected top-level shape.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
PLUGIN_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "docs" / "specs" / "adapter-contract" / "plugin-manifest-schema.json"
)


def _load_schema() -> dict:
    return json.loads(PLUGIN_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))


class PluginManifestSchemaAcceptsValidExamplesTests(unittest.TestCase):
    """plugin-manifest-schema.json accepts well-formed plugin.json structures."""

    def test_accepts_minimal_plugin_manifest(self) -> None:
        """A minimal hand-authored .claude-plugin/plugin.json is accepted.

        Verifies AC 4: the schema validates the hand-authored per-pack manifest.
        """
        from agentbundle.build.validate import validate

        schema = _load_schema()
        minimal = {
            "name": "agent-ready-core",
            "version": "0.1.0",
            "description": "Core agent skills for the agent-ready-repo template.",
        }
        errors = validate(minimal, schema)
        self.assertEqual(
            errors,
            [],
            f"schema rejected minimal plugin.json:\n" + "\n".join(errors),
        )

    def test_accepts_plugin_manifest_with_skills_and_agents(self) -> None:
        """A plugin.json with optional skills and agents arrays is accepted."""
        from agentbundle.build.validate import validate

        schema = _load_schema()
        full = {
            "name": "agent-ready-governance-extras",
            "version": "0.1.0",
            "description": "RFC/ADR ceremony skills.",
            "skills": ["new-rfc", "new-adr", "update-conventions"],
            "agents": ["adversarial-reviewer"],
        }
        errors = validate(full, schema)
        self.assertEqual(
            errors,
            [],
            f"schema rejected plugin.json with skills and agents:\n"
            + "\n".join(errors),
        )

    def test_accepts_plugin_manifest_without_optional_fields(self) -> None:
        """A plugin.json with only required fields (no skills, no agents) is accepted."""
        from agentbundle.build.validate import validate

        schema = _load_schema()
        minimal = {
            "name": "agent-ready-user-guide-diataxis",
            "version": "0.2.0",
            "description": "Diátaxis user-guide scaffolding.",
        }
        errors = validate(minimal, schema)
        self.assertEqual(
            errors,
            [],
            f"schema rejected plugin.json with only required fields:\n"
            + "\n".join(errors),
        )


class PluginManifestSchemaRejectsInvalidExamplesTests(unittest.TestCase):
    """plugin-manifest-schema.json rejects malformed plugin.json structures."""

    def test_rejects_missing_name(self) -> None:
        """A plugin.json without a name field is rejected."""
        from agentbundle.build.validate import validate

        schema = _load_schema()
        instance = {
            "version": "0.1.0",
            "description": "Missing name.",
        }
        errors = validate(instance, schema)
        self.assertTrue(errors, "schema accepted plugin.json missing 'name'")
        self.assertTrue(
            any("name" in e for e in errors),
            f"error should mention 'name'; got: {errors}",
        )

    def test_rejects_missing_version(self) -> None:
        """A plugin.json without a version field is rejected."""
        from agentbundle.build.validate import validate

        schema = _load_schema()
        instance = {
            "name": "agent-ready-core",
            "description": "Missing version.",
        }
        errors = validate(instance, schema)
        self.assertTrue(errors, "schema accepted plugin.json missing 'version'")

    def test_rejects_missing_description(self) -> None:
        """A plugin.json without a description field is rejected."""
        from agentbundle.build.validate import validate

        schema = _load_schema()
        instance = {
            "name": "agent-ready-core",
            "version": "0.1.0",
        }
        errors = validate(instance, schema)
        self.assertTrue(errors, "schema accepted plugin.json missing 'description'")


class PluginManifestSchemaLoadsTests(unittest.TestCase):
    """Smoke test: the schema file loads and has the expected top-level shape."""

    def test_schema_loads(self) -> None:
        schema = _load_schema()
        self.assertEqual(schema.get("type"), "object")

    def test_schema_requires_name_version_description(self) -> None:
        schema = _load_schema()
        required = schema.get("required", [])
        self.assertIn("name", required)
        self.assertIn("version", required)
        self.assertIn("description", required)


if __name__ == "__main__":
    unittest.main()
