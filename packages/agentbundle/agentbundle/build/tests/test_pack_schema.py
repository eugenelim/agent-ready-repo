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


class PackSchemaEnrichedMetadataTests(unittest.TestCase):
    """enriched-pack-manifest T1: optional first-class metadata fields.

    pack.schema.json gains optional `readme`, `display_name`, `license`,
    `[[pack.maintainers]]`, `[pack.links]`, `categories` (≤5),
    `keywords` (≤5), `[pack].catalogue`, and an opaque `[pack.metadata.*]`
    table. Every field is optional — a manifest omitting all of them must
    still validate (legacy invariance).
    """

    def test_accepts_all_enriched_fields(self) -> None:
        """A manifest carrying every new field validates."""
        from agentbundle.build.validate import validate

        schema = _load_schema()
        toml_text = """
[pack]
name = "research"
version = "0.1.0"
description = "Evidence-grounded research."
readme = "README.md"
display_name = "Research"
license = "Apache-2.0"
catalogue = "agent-ready-repo"
categories = ["research", "documentation"]
keywords = ["osint", "synthesis", "citations"]

[[pack.maintainers]]
name = "Eugene Lim"
email = "eugenelim@users.noreply.github.com"
url = "https://github.com/eugenelim"

[pack.links]
homepage = "https://example.com"
repository = "https://github.com/example/repo"
documentation = "https://example.com/docs"
changelog = "https://example.com/changelog"
issues = "https://example.com/issues"
icon = "https://example.com/icon.png"

[pack.metadata.cursor]
some-cursor-only-key = "anything"
nested = { a = 1, b = [1, 2, 3] }
"""
        instance = _parse_toml(toml_text)
        errors = validate(instance, schema)
        self.assertEqual(
            errors,
            [],
            "schema rejected a manifest with all enriched fields:\n"
            + "\n".join(errors),
        )

    def test_accepts_manifest_omitting_all_enriched_fields(self) -> None:
        """Optionality: a manifest with none of the new fields validates."""
        from agentbundle.build.validate import validate

        schema = _load_schema()
        toml_text = """
[pack]
name = "core"
version = "0.4.0"
description = "Core skills."
"""
        instance = _parse_toml(toml_text)
        errors = validate(instance, schema)
        self.assertEqual(errors, [], "\n".join(errors))

    def test_rejects_more_than_five_categories(self) -> None:
        from agentbundle.build.validate import validate

        schema = _load_schema()
        instance = {
            "pack": {
                "name": "core",
                "version": "0.1.0",
                "categories": ["a", "b", "c", "d", "e", "f"],
            }
        }
        errors = validate(instance, schema)
        self.assertTrue(errors, "schema accepted >5 categories")

    def test_accepts_exactly_five_categories(self) -> None:
        """Boundary: maxItems=5 admits exactly five (the new validator keyword)."""
        from agentbundle.build.validate import validate

        schema = _load_schema()
        instance = {
            "pack": {
                "name": "core",
                "version": "0.1.0",
                "categories": ["a", "b", "c", "d", "e"],
            }
        }
        self.assertEqual(validate(instance, schema), [])

    def test_rejects_more_than_five_keywords(self) -> None:
        from agentbundle.build.validate import validate

        schema = _load_schema()
        instance = {
            "pack": {
                "name": "core",
                "version": "0.1.0",
                "keywords": ["a", "b", "c", "d", "e", "f"],
            }
        }
        errors = validate(instance, schema)
        self.assertTrue(errors, "schema accepted >5 keywords")

    def test_rejects_maintainer_missing_name(self) -> None:
        from agentbundle.build.validate import validate

        schema = _load_schema()
        instance = {
            "pack": {
                "name": "core",
                "version": "0.1.0",
                "maintainers": [{"email": "nobody@example.com"}],
            }
        }
        errors = validate(instance, schema)
        self.assertTrue(errors, "schema accepted a maintainer with no name")

    def test_rejects_non_string_license(self) -> None:
        from agentbundle.build.validate import validate

        schema = _load_schema()
        instance = {
            "pack": {"name": "core", "version": "0.1.0", "license": 42}
        }
        errors = validate(instance, schema)
        self.assertTrue(errors, "schema accepted a non-string license")

    def test_metadata_table_is_opaque_object(self) -> None:
        """`[pack.metadata.<tool>]` is an arbitrary object — accepted as-is."""
        from agentbundle.build.validate import validate

        schema = _load_schema()
        instance = {
            "pack": {
                "name": "core",
                "version": "0.1.0",
                "metadata": {"anything": {"deeply": {"nested": [1, 2]}}},
            }
        }
        errors = validate(instance, schema)
        self.assertEqual(errors, [], "\n".join(errors))


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
