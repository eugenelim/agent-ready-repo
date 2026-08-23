"""Contract tests for the versioned legacy work-intake migration corpus."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

_ROOT = Path(__file__).resolve().parents[2]
_SCHEMAS = _ROOT / "contracts" / "jsonschema"
_FIXTURES = (
    _ROOT
    / "packs/core/tests/skills/workspace-status/fixtures/work-intake-migration"
)


def _json_files(relative: str) -> list[Path]:
    """Return the versioned JSON fixtures below one migration fixture group."""
    return sorted((_FIXTURES / relative).glob("*.json"))


def _schema(name: str) -> dict[str, object]:
    """Load one authored JSON Schema by filename."""
    return json.loads((_SCHEMAS / name).read_text(encoding="utf-8"))


def _registry() -> Registry:
    """Return a registry that resolves authored sibling-schema references."""
    registry = Registry()
    for path in sorted(_SCHEMAS.glob("*.schema.json")):
        contents = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(contents)
        registry = registry.with_resource(str(contents["$id"]), resource)
    return registry


def _validator(name: str) -> Draft202012Validator:
    """Build a strict migration-contract validator with format checks."""
    return Draft202012Validator(
        _schema(name), registry=_registry(), format_checker=FormatChecker()
    )


_CONTRACTS = {
    "selection": "work-intake-migration-selection.schema.json",
    "confirmation": "work-intake-migration-confirmation.schema.json",
    "ledger": "work-intake-migration-manifest.schema.json",
    "result": "work-intake-migration-result.schema.json",
}


def test_ac1_every_accepted_legacy_shape_has_an_exact_fixture() -> None:
    expected = {
        "work-queue-string.toml": 'queue   = [\n  "spec/engine-export-boundary",\n]\n',
        "shaping-string.toml": 'backlog = [\n  "ini-002-initiative-brief",\n]\n',
        "shaping-object.toml": (
            'backlog = [\n  {slug = "opp-assessment-pe-pack",  '
            'needs = "work:spec/m2-frame-situation"},\n]\n'
        ),
        "brief-string.toml": (
            'ready = [\n  "docs/product/briefs/example-brief.md",\n]\n'
        ),
        "backlog-object.toml": (
            "[backlog]\nopen = [\n"
            "  # Captured prose remains comment-rich until a human selects its route.\n"
            '  { slug = "captured-prose", source = "capture-work", summary = '
            '"Follow up on the accepted intake", needs = [], type = "spec" },\n]\n'
        ),
    }
    actual = {
        path.name: path.read_text(encoding="utf-8")
        for path in (_FIXTURES / "legacy" / "valid").glob("*.toml")
    }
    assert actual == expected


def test_ac1_inventory_is_resolvable_at_the_pinned_acceptance_ref() -> None:
    inventory = (
        _ROOT
        / "docs/specs/work-intake-migration-docs/notes/legacy-source-inventory.md"
    ).read_text(encoding="utf-8")
    ref = "352595bd2bcf25bbbffb03deabfa8f5a9e4b248d"
    sources = [
        "workspace.toml",
        "packs/core/seeds/workspace.toml",
        "packs/core/.apm/skills/workspace-status/evals/files/workspace.toml",
        "packs/core/.apm/skills/capture-work/SKILL.md",
        "packs/core/.apm/skills/author-brief/SKILL.md",
        "packs/core/.apm/skills/receive-brief/SKILL.md",
        "packs/atlassian/.apm/skills/jira-brief-intake/SKILL.md",
        "packs/atlassian/.apm/skills/jira-align-brief-intake/SKILL.md",
        "packs/atlassian/.apm/skills/jira-story-triage/SKILL.md",
        "packs/github/.apm/skills/github-brief-intake/SKILL.md",
        "packs/linear/.apm/skills/linear-brief-intake/SKILL.md",
    ]
    assert ref in inventory
    for source in sources:
        assert source in inventory
        completed = subprocess.run(
            ["git", "cat-file", "-e", f"{ref}:{source}"],
            cwd=_ROOT,
            check=False,
            capture_output=True,
        )
        assert completed.returncode == 0, source


def test_ac1_manual_variants_pin_malformed_and_missing_inputs() -> None:
    expected = {"malformed-entry.toml", "missing-artifact.toml", "missing-plan.toml"}
    actual = {path.name for path in (_FIXTURES / "legacy" / "manual").glob("*.toml")}
    assert expected <= actual


def test_ac5_unknown_extensions_have_byte_stability_fixtures() -> None:
    before = _FIXTURES / "legacy" / "manual" / "private-extension.before.toml"
    after = _FIXTURES / "legacy" / "manual" / "private-extension.after.toml"
    assert before.is_file() and after.is_file()
    assert before.read_bytes() == after.read_bytes()


def test_ac6_ledger_fixtures_validate_against_the_public_schema() -> None:
    fixtures = _json_files("ledger/valid")
    assert fixtures
    validator = _validator("work-intake-migration-manifest.schema.json")
    for fixture in fixtures:
        validator.validate(json.loads(fixture.read_text(encoding="utf-8")))


def test_ac6_schema_invalid_ledger_fixtures_are_rejected() -> None:
    validator = _validator("work-intake-migration-manifest.schema.json")
    fixtures = _json_files("ledger/invalid")
    assert fixtures
    for fixture in fixtures:
        assert not validator.is_valid(json.loads(fixture.read_text(encoding="utf-8")))


def test_ac6_semantic_invalid_ledgers_remain_schema_valid_runtime_cases() -> None:
    expected = {
        "apply-after-rollback.json",
        "duplicate-authorization-subject.json",
        "duplicate-confirmation-id.json",
        "duplicate-operation-id.json",
        "operation-digest-mismatch.json",
        "receipt-binding-mismatch.json",
        "rollback-without-receipt.json",
        "skipped-state.json",
    }
    paths = sorted((_FIXTURES / "ledger" / "invalid-semantic").glob("*.json"))
    assert {path.name for path in paths} == expected
    validator = _validator("work-intake-migration-manifest.schema.json")
    for path in paths:
        validator.validate(json.loads(path.read_text(encoding="utf-8")))


def test_ac6_schema_publishes_runtime_semantic_invariants() -> None:
    schema = _schema("work-intake-migration-manifest.schema.json")
    assert schema["x-semantic-invariants"] == [
        {
            "code": "ledger_invalid",
            "rule": (
                "each operation_digest binds its immutable operation material to "
                "the ledger repository_identity and effect-time recomputation "
                "rejects a changed identity"
            ),
        },
        {"code": "ledger_invalid", "rule": "operation_id is globally unique within the ledger"},
        {
            "code": "confirmation_reused",
            "rule": (
                "confirmation_id and authorization_subject are each globally unique "
                "across all operation receipts"
            ),
        },
        {
            "code": "confirmation_binding_mismatch",
            "rule": "every receipt operation_id and operation_digest equals its containing operation",
        },
        {
            "code": "operation_state_conflict",
            "rule": (
                "receipt actions are ordered apply before rollback and justify "
                "pending/applied/rollback_pending/rolled_back state without skipped "
                "or reversed transitions"
            ),
        },
    ]


def test_ac7_sensitive_legacy_content_has_non_echoing_refusal_fixtures() -> None:
    fixtures = sorted((_FIXTURES / "legacy" / "sensitive").glob("*.toml"))
    expected = _json_files("results/sensitive")
    assert fixtures and len(fixtures) == len(expected)
    for result_path in expected:
        result = json.loads(result_path.read_text(encoding="utf-8"))
        assert result["result_code"] == "sensitive_legacy_content"
        assert "matched_text" not in result
        source = fixtures[expected.index(result_path)].read_bytes()
        assert b"ghp_" in source
        assert b"ghp_" not in result_path.read_bytes()


def test_ac28_all_four_migration_contracts_have_valid_and_invalid_fixtures() -> None:
    stems = {
        "selection",
        "confirmation",
        "ledger",
        "result",
    }
    assert stems == {
        path.name
        for path in _FIXTURES.iterdir()
        if path.is_dir() and (path / "valid").is_dir() and (path / "invalid").is_dir()
    }

    for stem, schema_name in _CONTRACTS.items():
        validator = _validator(schema_name)
        valid = _json_files(f"{stem}/valid")
        invalid = _json_files(f"{stem}/invalid")
        assert valid and invalid
        for fixture in valid:
            validator.validate(json.loads(fixture.read_text(encoding="utf-8")))
        for fixture in invalid:
            assert not validator.is_valid(json.loads(fixture.read_text(encoding="utf-8")))


def test_ac28_migration_contracts_are_closed_and_reject_unknown_fields() -> None:
    for stem, schema_name in _CONTRACTS.items():
        fixture = json.loads(_json_files(f"{stem}/valid")[0].read_text(encoding="utf-8"))
        fixture["unknown_private_field"] = True
        assert not _validator(schema_name).is_valid(fixture)


def test_ac28_confirmation_opaque_fields_reject_human_identifiers() -> None:
    validator = _validator("work-intake-migration-confirmation.schema.json")
    base = json.loads(_json_files("confirmation/valid")[0].read_text(encoding="utf-8"))
    for field, values in {
        "confirmation_id": ["Jane Doe", "jane@example.com", "account-123", "ExampleOrg"],
        "authorization_subject": ["Jane Doe", "jane@example.com", "user-jane", "team-platform"],
    }.items():
        for value in values:
            candidate = dict(base)
            candidate[field] = value
            assert not validator.is_valid(candidate), (field, value)


def test_ac28_contract_inventory_has_truthful_authored_not_bundled_rows() -> None:
    readme = (_ROOT / "contracts/README.md").read_text(encoding="utf-8")
    for schema_name in [
        "normalized-intake.schema.json",
        "workspace-entry.schema.json",
        *_CONTRACTS.values(),
    ]:
        row = next(line for line in readme.splitlines() if f"`jsonschema/{schema_name}`" in line)
        assert row.rstrip().endswith("| no |")
    assert "[work-intake-migration]" in readme
