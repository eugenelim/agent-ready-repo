"""T-C1 (RFC-0005 kiro-ide-hook): adapter.schema.json vocabulary fields.

Pre-bump tests pinning the two optional declarative-vocabulary fields
the schema now documents under ``projections.<primitive>.properties``:

  - ``ide-event-vocabulary`` — Kiro's IDE-surface event names
    (``fileSave``, ``promptSubmit``, etc.).
  - ``ide-action-vocabulary`` — Kiro's action types
    (``askAgent``, ``runCommand``).

Both are arrays-of-strings with ``minItems: 1`` — same shape as the
already-shipped ``agent-event-vocabulary``.

The fields land in the schema in T-C1 (this task). The
``[primitive."kiro-ide-hook"]`` declaration and the
``[adapter.kiro.projections.kiro-ide-hook]`` table that *use* the
fields land in T-CONTRACT (probe-gated). These tests therefore drive
synthesised schema instances rather than the on-disk contract — the
on-disk v0.3 contract carries no ``kiro-ide-hook`` projection yet,
and a test asserting "the on-disk contract validates" would only
cover the unchanged shape.
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from agentbundle.build import validate as v

REPO_ROOT = Path(__file__).resolve().parents[4]
ADAPTER_SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.schema.json"


def _load_schema() -> dict:
    return json.loads(ADAPTER_SCHEMA_PATH.read_text(encoding="utf-8"))


def _minimal_v0_3_contract() -> dict:
    """A schema-passing minimal contract dict the tests can mutate."""
    return {
        "contract": {"version": "0.3"},
        "primitive": {
            "skill": {"source-path": ".apm/skills/"},
            "agent": {"source-path": ".apm/agents/"},
            "hook-body": {"source-path": ".apm/hooks/"},
            "hook-wiring": {"source-path": ".apm/hook-wiring/"},
            "command": {"source-path": ".apm/commands/"},
        },
        "adapter": {
            "kiro": {
                "projection": [
                    {"primitive": "skill", "mode": "direct-directory", "target-path": ".kiro/skills/"},
                ],
                "projections": {
                    "kiro-ide-hook": {
                        "mode": "direct-file",
                        "ide-event-vocabulary": ["fileSave"],
                        "ide-action-vocabulary": ["askAgent", "runCommand"],
                    }
                },
            }
        },
    }


class IdeVocabularyAcceptanceTests(unittest.TestCase):
    """Schema accepts optional ``ide-event-vocabulary`` /
    ``ide-action-vocabulary`` array-of-string fields."""

    def setUp(self) -> None:
        self.schema = _load_schema()
        self.contract = _minimal_v0_3_contract()

    def test_accepts_ide_event_vocabulary_non_empty(self) -> None:
        errors = v.validate(self.contract, self.schema)
        self.assertEqual(errors, [])

    def test_accepts_ide_action_vocabulary_non_empty(self) -> None:
        # Same contract — both fields under the same projection.
        errors = v.validate(self.contract, self.schema)
        self.assertEqual(errors, [])

    def test_rejects_empty_ide_event_vocabulary(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["adapter"]["kiro"]["projections"]["kiro-ide-hook"][
            "ide-event-vocabulary"
        ] = []
        errors = v.validate(contract, self.schema)
        self.assertTrue(errors, msg="empty ide-event-vocabulary should fail minItems=1")

    def test_rejects_empty_ide_action_vocabulary(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["adapter"]["kiro"]["projections"]["kiro-ide-hook"][
            "ide-action-vocabulary"
        ] = []
        errors = v.validate(contract, self.schema)
        self.assertTrue(errors, msg="empty ide-action-vocabulary should fail minItems=1")

    def test_rejects_non_string_items_in_vocabulary(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["adapter"]["kiro"]["projections"]["kiro-ide-hook"][
            "ide-event-vocabulary"
        ] = ["fileSave", 42]
        errors = v.validate(contract, self.schema)
        self.assertTrue(errors, msg="non-string vocabulary item should fail items.type=string")


class ExistingContractStillValidates(unittest.TestCase):
    """The shipped v0.3 contract must continue to validate after the
    schema extension — the new fields are optional."""

    def test_on_disk_v0_3_contract_validates(self) -> None:
        import tomllib

        schema = _load_schema()
        contract_path = REPO_ROOT / "docs" / "contracts" / "adapter.toml"
        contract = tomllib.loads(contract_path.read_text(encoding="utf-8"))
        errors = v.validate(contract, schema)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
