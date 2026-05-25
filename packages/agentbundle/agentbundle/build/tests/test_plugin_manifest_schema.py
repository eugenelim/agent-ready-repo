"""Tests for plugin-manifest.schema.json and plugin-manifest.derived.schema.json.

Verifies:
  - plugin-manifest.schema.json (source shape) accepts a minimal hand-authored
    .claude-plugin/plugin.json (AC 4).
  - The source schema loads with the expected top-level shape.
  - T2: source schema forbids the hooks property (AC10 gate 1).
  - T2: derived schema accepts the synthesised hooks.SessionStart block (AC10 gate 1).
  - T5: every source-tree packs/*/.claude-plugin/plugin.json carries no hooks
    block (AC10).
  - T5: every source-tree packs/*/.claude-plugin/plugin.json validates against
    the source-shape schema (AC10).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
PLUGIN_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "docs" / "contracts" / "plugin-manifest.schema.json"
)
PLUGIN_MANIFEST_DERIVED_SCHEMA_PATH = (
    REPO_ROOT / "docs" / "contracts" / "plugin-manifest.derived.schema.json"
)


def _load_schema() -> dict:
    return json.loads(PLUGIN_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_derived_schema() -> dict:
    return json.loads(PLUGIN_MANIFEST_DERIVED_SCHEMA_PATH.read_text(encoding="utf-8"))


class PluginManifestSchemaAcceptsValidExamplesTests(unittest.TestCase):
    """plugin-manifest.schema.json accepts well-formed plugin.json structures."""

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
    """plugin-manifest.schema.json rejects malformed plugin.json structures."""

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


class PluginManifestSchemaSplitTests(unittest.TestCase):
    """T2: Source schema forbids hooks; derived schema accepts synthesised hooks (AC10 gate 1).

    test_source_plugin_manifest_schema_forbids_hooks
    test_derived_plugin_manifest_schema_accepts_synthesised_hooks
    """

    def test_source_plugin_manifest_schema_forbids_hooks(self) -> None:
        """Source-shape schema rejects any manifest carrying a hooks property.

        AC10 gate 1 (Blocker-5 rail): a stray hooks block in a source-tree
        plugin.json must fail schema validation. The additionalProperties: false
        + explicit property list is the mechanism — hooks is not in the list.
        """
        from agentbundle.build.validate import validate

        schema = _load_schema()

        # Minimal manifest (no hooks) must still validate.
        minimal = {
            "name": "agent-ready-core",
            "version": "0.1.0",
            "description": "Core agent skills.",
        }
        errors = validate(minimal, schema)
        self.assertEqual(
            errors,
            [],
            f"source schema rejected a valid manifest with no hooks:\n"
            + "\n".join(errors),
        )

        # Manifest with hooks must be rejected — hooks is not in the source
        # schema's properties enumeration and additionalProperties is false.
        with_hooks = {
            "name": "agent-ready-core",
            "version": "0.1.0",
            "description": "Core agent skills.",
            "hooks": {
                "SessionStart": [
                    {
                        "command": 'python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"'
                    }
                ]
            },
        }
        errors = validate(with_hooks, schema)
        self.assertTrue(
            errors,
            "source schema must reject a manifest carrying a hooks property "
            "(hooks is not in the source schema's properties list; "
            "additionalProperties: false should block it)",
        )

    def test_derived_plugin_manifest_schema_accepts_synthesised_hooks(self) -> None:
        """Derived-shape schema accepts a manifest with the synthesised hooks.SessionStart block.

        AC10 gate 1: the build pipeline validates derived-tree manifests against
        the derived schema. The derived schema adds hooks to the properties
        enumeration so additionalProperties: false still holds.
        """
        from agentbundle.build.validate import validate

        derived_schema = _load_derived_schema()

        # Minimal manifest (no hooks) must also be valid under the derived schema.
        minimal = {
            "name": "agent-ready-core",
            "version": "0.1.0",
            "description": "Core agent skills.",
        }
        errors = validate(minimal, derived_schema)
        self.assertEqual(
            errors,
            [],
            f"derived schema rejected a valid manifest with no hooks:\n"
            + "\n".join(errors),
        )

        # Manifest with synthesised hooks.SessionStart block must be accepted.
        derived = {
            "name": "agent-ready-core",
            "version": "0.1.0",
            "description": "Core agent skills.",
            "hooks": {
                "SessionStart": [
                    {
                        "command": 'python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"'
                    }
                ]
            },
        }
        errors = validate(derived, derived_schema)
        self.assertEqual(
            errors,
            [],
            f"derived schema rejected a manifest with the synthesised hooks block:\n"
            + "\n".join(errors),
        )


class SourcePluginJsonAuditTests(unittest.TestCase):
    """T5: Audit every source-tree packs/*/.claude-plugin/plugin.json (AC10).

    test_no_source_plugin_json_carries_hooks
    test_source_plugin_json_validates_against_schema
    """

    def _source_manifests(self) -> list[Path]:
        """Return paths for all source-tree per-pack plugin.json files."""
        return sorted((REPO_ROOT / "packs").glob("*/.claude-plugin/plugin.json"))

    def test_no_source_plugin_json_carries_hooks(self) -> None:
        """Every source-tree plugin.json must not declare a hooks block.

        AC10: the hooks block is synthesised by the build pipeline; hand-authored
        source manifests must never pre-declare it. This test pins that invariant
        permanently so a future accidental hooks block is caught immediately.
        """
        manifests = self._source_manifests()
        self.assertTrue(
            manifests,
            "No packs/*/.claude-plugin/plugin.json found — "
            "check that REPO_ROOT resolves correctly.",
        )
        for manifest_path in manifests:
            with self.subTest(pack=manifest_path.parent.parent.name):
                content = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertNotIn(
                    "hooks",
                    content,
                    f"{manifest_path.relative_to(REPO_ROOT)}: "
                    f"source-tree plugin.json must not carry a 'hooks' block "
                    f"(the build pipeline synthesises it). "
                    f"Remove the stray hooks block from the source file.",
                )

    def test_source_plugin_json_validates_against_schema(self) -> None:
        """Every source-tree plugin.json must validate against the source-shape schema.

        AC10: the source schema (plugin-manifest.schema.json) explicitly forbids
        hooks via additionalProperties: false. Validating every source-tree
        manifest against it here provides a second gate that catches both missing
        required fields and any stray additional properties (including hooks).
        """
        from agentbundle.build.validate import validate

        schema = _load_schema()
        manifests = self._source_manifests()
        self.assertTrue(
            manifests,
            "No packs/*/.claude-plugin/plugin.json found — "
            "check that REPO_ROOT resolves correctly.",
        )
        for manifest_path in manifests:
            with self.subTest(pack=manifest_path.parent.parent.name):
                content = json.loads(manifest_path.read_text(encoding="utf-8"))
                errors = validate(content, schema)
                self.assertEqual(
                    errors,
                    [],
                    f"{manifest_path.relative_to(REPO_ROOT)} failed schema "
                    f"validation against plugin-manifest.schema.json:\n"
                    + "\n".join(errors),
                )


if __name__ == "__main__":
    unittest.main()
