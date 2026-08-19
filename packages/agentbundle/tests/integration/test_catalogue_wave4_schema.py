"""Public catalogue-index schema tests."""

from __future__ import annotations

import copy
import json
from importlib.resources import files

import pytest
from agentbundle.build.validate import validate

BUNDLED_SCHEMA = files("agentbundle").joinpath("_data/catalogue-index.schema.json")


def _minimal_index() -> dict[str, object]:
    return {
        "schema_version": "1",
        "catalogue": {"name": "Example", "description": "Example catalogue."},
        "packs": [],
        "profiles": [],
    }


def _full_index() -> dict[str, object]:
    journey = {
        "journey_id": "example-journey",
        "pack": "example-pack",
        "start_state": "read-only",
        "end_state": "confirmed-write",
        "scope": "repo",
        "tagline": "Example journey.",
        "contract": {
            "useItWhen": "You need an example.",
            "youProvide": "Example input.",
            "youReceive": "Example output.",
            "yourDecisions": ["Whether to proceed."],
        },
    }
    integration = {
        "id": "example-link",
        "pack": "other-pack",
        "kind": "augment",
        "role": "consumer",
    }
    return {
        "schema_version": "1",
        "generated_at": "2026-08-01T00:00:00Z",
        "catalogue": {"name": "Example", "description": "Example catalogue."},
        "packs": [
            {
                "name": "example-pack",
                "version": "1.0.0",
                "description": "Example pack.",
                "scope": "repo",
                "adapters": ["claude-code"],
                "journeys": [journey],
                "integrations": [integration],
                "integrations_inverse": [integration],
                "effects": [
                    {"kind": "network-call", "description": "Calls a service."}
                ],
                "content": {
                    "skills": ["example-skill"],
                    "agents": ["example-agent"],
                    "commands": ["example-command"],
                    "hooks": ["example-hook"],
                    "scripts": [".apm/skills/example-skill/scripts/run.py"],
                    "seeds": ["README.md"],
                    "shared-libs": ["shared.py"],
                    "user-libs": ["user.py"],
                },
                "execution": ["example-hook"],
                "documentation": "https://example.com/docs",
                "digest": "a" * 64,
            }
        ],
        "profiles": [
            {
                "name": "example-profile",
                "scope": "repo",
                "description": "Example profile.",
                "packs": ["example-pack"],
            }
        ],
    }


def _schema() -> dict[str, object]:
    return json.loads(BUNDLED_SCHEMA.read_text(encoding="utf-8"))


def test_schema_parses_as_valid_json() -> None:
    assert isinstance(_schema(), dict)


def test_normative_fields_only_fixture_validates() -> None:
    assert validate(_minimal_index(), _schema()) == []


def test_full_fields_fixture_validates() -> None:
    assert validate(_full_index(), _schema()) == []


def test_missing_schema_version_fails_validation() -> None:
    instance = _minimal_index()
    del instance["schema_version"]
    assert validate(instance, _schema())


@pytest.mark.parametrize(
    ("path", "extra"),
    [
        ((), {"unknown": True}),
        (("catalogue",), {"unknown": True}),
        (("packs", 0), {"unknown": True}),
        (("packs", 0, "journeys", 0), {"unknown": True}),
        (("packs", 0, "journeys", 0, "contract"), {"unknown": True}),
        (("packs", 0, "effects", 0), {"unknown": True}),
        (("packs", 0, "integrations", 0), {"unknown": True}),
        (("packs", 0, "content"), {"unknown": True}),
        (("profiles", 0), {"unknown": True}),
    ],
)
def test_unknown_properties_fail_validation(
    path: tuple[str | int, ...],
    extra: dict[str, object],
) -> None:
    instance = _full_index()
    target: object = instance
    for part in path:
        target = target[part]  # type: ignore[index]
    assert isinstance(target, dict)
    target.update(extra)
    assert validate(instance, _schema())


def test_contract_requires_all_journey_contract_fields() -> None:
    schema = _schema()
    for field in ("useItWhen", "youProvide", "youReceive", "yourDecisions"):
        instance = copy.deepcopy(_full_index())
        del instance["packs"][0]["journeys"][0]["contract"][field]  # type: ignore[index]
        assert validate(instance, schema)


@pytest.mark.parametrize(
    ("field", "value"),
    [("integrations", "companion"), ("integrations_inverse", "companion")],
)
def test_invalid_integration_kind_fails_validation(field: str, value: str) -> None:
    instance = _full_index()
    instance["packs"][0][field][0]["kind"] = value  # type: ignore[index]

    assert validate(instance, _schema())


def test_invalid_effect_kind_fails_validation() -> None:
    instance = _full_index()
    instance["packs"][0]["effects"][0]["kind"] = "network"  # type: ignore[index]

    assert validate(instance, _schema())
