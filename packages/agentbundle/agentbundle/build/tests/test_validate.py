"""Tests for the stdlib JSON-Schema subset validator (T1a)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from agentbundle.build.validate import validate

REPO_ROOT = Path(__file__).resolve().parents[5]
SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.schema.json"


class TypeKeywordTests(unittest.TestCase):
    def test_object_accepts_dict(self) -> None:
        self.assertEqual(validate({}, {"type": "object"}), [])

    def test_object_rejects_list(self) -> None:
        errors = validate([], {"type": "object"})
        self.assertTrue(errors)
        self.assertIn("expected object", errors[0])

    def test_string_accepts_string(self) -> None:
        self.assertEqual(validate("x", {"type": "string"}), [])

    def test_string_rejects_integer(self) -> None:
        errors = validate(7, {"type": "string"})
        self.assertTrue(errors)

    def test_integer_rejects_boolean(self) -> None:
        # Python bool is a subclass of int; the validator must reject it.
        errors = validate(True, {"type": "integer"})
        self.assertTrue(errors)
        self.assertIn("boolean", errors[0])

    def test_boolean_accepts_true(self) -> None:
        self.assertEqual(validate(True, {"type": "boolean"}), [])

    def test_boolean_rejects_integer(self) -> None:
        errors = validate(1, {"type": "boolean"})
        self.assertTrue(errors)

    def test_array_accepts_list(self) -> None:
        self.assertEqual(validate([1, 2], {"type": "array"}), [])

    def test_array_rejects_string(self) -> None:
        errors = validate("nope", {"type": "array"})
        self.assertTrue(errors)


class RequiredKeywordTests(unittest.TestCase):
    def test_required_present(self) -> None:
        schema = {"type": "object", "required": ["a"]}
        self.assertEqual(validate({"a": 1}, schema), [])

    def test_required_missing(self) -> None:
        schema = {"type": "object", "required": ["a"]}
        errors = validate({}, schema)
        self.assertTrue(errors)
        self.assertIn("missing required property", errors[0])


class EnumKeywordTests(unittest.TestCase):
    def test_enum_accepts_member(self) -> None:
        self.assertEqual(validate("a", {"enum": ["a", "b"]}), [])

    def test_enum_rejects_non_member(self) -> None:
        errors = validate("c", {"enum": ["a", "b"]})
        self.assertTrue(errors)
        self.assertIn("not in enum", errors[0])


class PatternKeywordTests(unittest.TestCase):
    def test_pattern_match(self) -> None:
        self.assertEqual(validate("abc123", {"pattern": "^[a-z]+[0-9]+$"}), [])

    def test_pattern_mismatch(self) -> None:
        errors = validate("nope!", {"pattern": "^[a-z]+$"})
        self.assertTrue(errors)


class ItemsKeywordTests(unittest.TestCase):
    def test_items_homogeneous(self) -> None:
        schema = {"type": "array", "items": {"type": "string"}}
        self.assertEqual(validate(["a", "b"], schema), [])

    def test_items_rejects_wrong_type(self) -> None:
        schema = {"type": "array", "items": {"type": "string"}}
        errors = validate(["a", 1], schema)
        self.assertTrue(errors)


class PropertiesAndAdditionalTests(unittest.TestCase):
    def test_additional_properties_false(self) -> None:
        schema = {
            "type": "object",
            "properties": {"a": {"type": "string"}},
            "additionalProperties": False,
        }
        errors = validate({"a": "x", "b": "y"}, schema)
        self.assertTrue(errors)
        self.assertIn("additional property", errors[0])

    def test_additional_properties_default_allows(self) -> None:
        schema = {"type": "object", "properties": {"a": {"type": "string"}}}
        self.assertEqual(validate({"a": "x", "b": "y"}, schema), [])


class SchemaJsonSelfValidationTests(unittest.TestCase):
    """The shipped adapter.schema.json must load and validate at least one minimal
    contract — a smoke test for T1a's authored schema."""

    def test_schema_loads(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema.get("type"), "object")

    def test_schema_accepts_minimal_contract(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        minimal = {
            "contract": {"version": "0.1"},
            "primitive": {
                "skill": {"source-path": ".apm/skills/"},
                "agent": {"source-path": ".apm/agents/"},
                "hook-body": {"source-path": ".apm/hooks/"},
                "hook-wiring": {"source-path": ".apm/hook-wiring/"},
                "command": {"source-path": ".apm/commands/"},
            },
            "adapter": {
                "claude-code": {
                    "projection": [
                        {
                            "primitive": "skill",
                            "mode": "direct-directory",
                            "target-path": ".claude/skills/",
                            "on-conflict": "prompt-then-preserve",
                        }
                    ]
                }
            },
        }
        errors = validate(minimal, schema)
        self.assertEqual(errors, [], f"schema rejected minimal contract: {errors}")

    def test_schema_rejects_unknown_mode(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        bad = {
            "contract": {"version": "0.1"},
            "primitive": {
                "skill": {"source-path": ".apm/skills/"},
                "agent": {"source-path": ".apm/agents/"},
                "hook-body": {"source-path": ".apm/hooks/"},
                "hook-wiring": {"source-path": ".apm/hook-wiring/"},
                "command": {"source-path": ".apm/commands/"},
            },
            "adapter": {
                "claude-code": {
                    "projection": [
                        {
                            "primitive": "skill",
                            "mode": "bogus-mode",
                            "target-path": ".claude/skills/",
                            "on-conflict": "prompt-then-preserve",
                        }
                    ]
                }
            },
        }
        errors = validate(bad, schema)
        self.assertTrue(errors, "schema accepted an unknown projection mode")


class CliValidateSubcommandTests(unittest.TestCase):
    """`python -m agentbundle.build validate <path>` smoke test.

    Uses subprocess so the test exercises the actual argparse wiring.
    Does not rely on adapter.toml existing (T1b authors that); writes
    a temp TOML and validates it against the shipped schema.
    """

    def test_validate_subcommand_exits_zero_on_minimal_contract(self) -> None:
        import tempfile

        toml_text = """
[contract]
version = "0.1"

[primitive.skill]
source-path = ".apm/skills/"

[primitive.agent]
source-path = ".apm/agents/"

[primitive.hook-body]
source-path = ".apm/hooks/"

[primitive.hook-wiring]
source-path = ".apm/hook-wiring/"

[primitive.command]
source-path = ".apm/commands/"

[[adapter.claude-code.projection]]
primitive = "skill"
mode = "direct-directory"
target-path = ".claude/skills/"
on-conflict = "prompt-then-preserve"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as tmp:
            tmp.write(toml_text)
            tmp_path = tmp.name

        result = subprocess.run(
            [sys.executable, "-m", "agentbundle.build", "validate", tmp_path],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"validate subcommand failed: stderr={result.stderr}",
        )

    def test_help_exits_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "agentbundle.build", "--help"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("validate", result.stdout)

    def test_validate_help_exits_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "agentbundle.build", "validate", "--help"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
