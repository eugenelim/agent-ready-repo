"""Tests for plugin-manifest.schema.json and plugin-manifest.derived.schema.json.

Verifies:
  - plugin-manifest.schema.json (source shape) accepts a minimal hand-authored
    .claude-plugin/plugin.json.
  - The source schema loads with the expected top-level shape.
  - T2: source schema forbids the hooks property (gate 1).
  - T2: derived schema accepts the synthesised hooks.SessionStart block (gate 1).
  - T5: every source-tree packs/*/.claude-plugin/plugin.json carries no hooks
    block.
  - T5: every source-tree packs/*/.claude-plugin/plugin.json validates against
    the source-shape schema.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_MANIFEST_SCHEMA_PATH = (
    PACKAGE_ROOT / "agentbundle" / "_data" / "plugin-manifest.schema.json"
)
PLUGIN_MANIFEST_DERIVED_SCHEMA_PATH = (
    PACKAGE_ROOT / "agentbundle" / "_data" / "plugin-manifest.derived.schema.json"
)


def _load_schema() -> dict:
    return json.loads(PLUGIN_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_derived_schema() -> dict:
    return json.loads(PLUGIN_MANIFEST_DERIVED_SCHEMA_PATH.read_text(encoding="utf-8"))


class PluginManifestSchemaAcceptsValidExamplesTests(unittest.TestCase):
    """plugin-manifest.schema.json accepts well-formed plugin.json structures."""

    def test_accepts_minimal_plugin_manifest(self) -> None:
        """A minimal hand-authored .claude-plugin/plugin.json is accepted.

        The schema validates the hand-authored per-pack manifest.
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
            "schema rejected minimal plugin.json:\n" + "\n".join(errors),
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
            "schema rejected plugin.json with skills and agents:\n"
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
            "schema rejected plugin.json with only required fields:\n"
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


class PluginManifestSchemaProjectableSubsetTests(unittest.TestCase):
    """enriched-pack-manifest T3: both schemas admit the projectable subset.

    The build derives `author`, `license`, `homepage`, `repository`,
    `keywords`, `category`, and `displayName` from each pack's `pack.toml`
    into the plugin.json / marketplace.json entry. Both schemas widen their
    allow-list to admit this named subset while keeping
    `additionalProperties: false` (a genuinely unknown key still fails).
    """

    # category is marketplace-only — not a valid field in plugin.json (derived schema).
    # It is kept in the source schema's allow-list for hand-authored files only.
    _SUBSET = {
        "author": {"name": "Example User", "email": "example@example.com"},
        "license": "Apache-2.0",
        "homepage": "https://example.com",
        "repository": "https://github.com/example/repo",
        "keywords": ["osint", "synthesis"],
        "displayName": "Research",
        "source": {
            "source": "git-subdir",
            "url": "https://github.com/example/repo.git",
            "path": "research",
            "ref": "claude-plugins-dist",
        },
    }
    # category is valid in the source schema but not the derived schema.
    _SOURCE_ONLY_FIELDS = {"category": "research"}

    def test_source_schema_admits_projectable_subset(self) -> None:
        from agentbundle.build.validate import validate

        manifest = {
            "name": "agent-ready-research",
            "version": "0.1.0",
            "description": "Research.",
            **self._SUBSET,
            **self._SOURCE_ONLY_FIELDS,  # category is valid in source schema
        }
        errors = validate(manifest, _load_schema())
        self.assertEqual(errors, [], "\n".join(errors))

    def test_derived_schema_admits_projectable_subset(self) -> None:
        """Derived schema accepts plugin.json fields; category is stripped (marketplace-only)."""
        from agentbundle.build.validate import validate

        manifest = {
            "name": "agent-ready-research",
            "version": "0.1.0",
            "description": "Research.",
            **self._SUBSET,
            # category excluded: it is marketplace-only, stripped before plugin.json is written
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": 'python3 "${CLAUDE_PLUGIN_ROOT}/x.py"',
                            }
                        ]
                    }
                ]
            },
        }
        errors = validate(manifest, _load_derived_schema())
        self.assertEqual(errors, [], "\n".join(errors))

    def test_both_schemas_still_reject_genuinely_unknown_key(self) -> None:
        """additionalProperties:false holds — a non-subset key is rejected."""
        from agentbundle.build.validate import validate

        manifest = {
            "name": "agent-ready-research",
            "version": "0.1.0",
            "description": "Research.",
            "totally-unknown-key": "nope",
        }
        self.assertTrue(
            validate(manifest, _load_schema()),
            "source schema accepted an unknown key",
        )
        self.assertTrue(
            validate(manifest, _load_derived_schema()),
            "derived schema accepted an unknown key",
        )


class PluginManifestSchemaSplitTests(unittest.TestCase):
    """T2: Source schema forbids hooks; derived schema accepts synthesised hooks (gate 1).

    test_source_plugin_manifest_schema_forbids_hooks
    test_derived_plugin_manifest_schema_accepts_synthesised_hooks
    """

    def test_source_plugin_manifest_schema_forbids_hooks(self) -> None:
        """Source-shape schema rejects any manifest carrying a hooks property.

        Gate 1: a stray hooks block in a source-tree
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
            "source schema rejected a valid manifest with no hooks:\n"
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

        Gate 1: the build pipeline validates derived-tree manifests against
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
            "derived schema rejected a valid manifest with no hooks:\n"
            + "\n".join(errors),
        )

        # Manifest with synthesised hooks.SessionStart block must be accepted.
        # Shape: {hooks: [{type, command, timeout}]} — the 2.1.209+ contract.
        derived = {
            "name": "agent-ready-core",
            "version": "0.1.0",
            "description": "Core agent skills.",
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": 'python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"',
                                "timeout": 10,
                            }
                        ]
                    }
                ]
            },
        }
        errors = validate(derived, derived_schema)
        self.assertEqual(
            errors,
            [],
            "derived schema rejected a manifest with the synthesised hooks block:\n"
            + "\n".join(errors),
        )

    def test_derived_schema_accepts_multiple_events_and_matcher(self) -> None:
        from agentbundle.build.validate import validate

        derived = {
            "name": "agent-ready-core",
            "version": "0.1.0",
            "description": "Core agent skills.",
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "startup|resume",
                        "hooks": [
                            {
                                "type": "command",
                                "command": 'python "${CLAUDE_PLUGIN_ROOT}/hooks/a.py"',
                                "timeout": 12,
                            }
                        ],
                    }
                ],
                "UserPromptSubmit": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": 'sh "${CLAUDE_PLUGIN_ROOT}/hooks/b.sh"',
                            }
                        ]
                    }
                ],
            },
        }
        self.assertEqual(validate(derived, _load_derived_schema()), [])

    def test_derived_schema_rejects_non_command_and_unknown_keys(self) -> None:
        from agentbundle.build.validate import validate

        base = {
            "name": "agent-ready-core",
            "version": "0.1.0",
            "description": "Core agent skills.",
        }
        non_command = {
            **base,
            "hooks": {
                "SessionStart": [
                    {"hooks": [{"type": "http", "command": "https://example.com"}]}
                ]
            },
        }
        unknown_inner = {
            **base,
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {"type": "command", "command": "true", "async": True}
                        ]
                    }
                ]
            },
        }
        unknown_outer = {
            **base,
            "hooks": {
                "SessionStart": [
                    {"label": "x", "hooks": [{"type": "command", "command": "true"}]}
                ]
            },
        }
        self.assertTrue(validate(non_command, _load_derived_schema()))
        self.assertTrue(validate(unknown_inner, _load_derived_schema()))
        self.assertTrue(validate(unknown_outer, _load_derived_schema()))


if __name__ == "__main__":
    unittest.main()
