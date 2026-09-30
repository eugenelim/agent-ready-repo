"""Repository-level contract tests for spec-retirement candidate output (T7)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from agentbundle.catalogue_tooling.file_safety import (
    list_confined_regular_files,
    read_confined_regular_file,
    validate_confined_directory,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "packs/core/.apm/skills/workspace-status/scripts"
SCHEMA_REL = "contracts/jsonschema/spec-retirement-candidates.schema.json"


def _load(name: str, filename: str):
    """Load one workspace-status module under a roster-unique name."""
    module_name = f"workspace_status_{name}_t7_roster"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _live_schema() -> dict:
    """Read the live schema through the shipped confined substrate reader."""
    retirement = _load("retirement", "workspace_status_retirement.py")
    schema = retirement.read_json_substrate(ROOT, SCHEMA_REL, {})
    assert isinstance(schema, dict), "the live retirement schema must be readable"
    return schema


def _emitted_document() -> dict:
    """Build the smallest complete document emitted by the T7 formatter."""
    candidates = _load(
        "retirement_candidates", "workspace_status_retirement_candidates.py"
    )
    return candidates.build_retirement_document(
        run_date="2026-09-25",
        stale_after_days=30,
        area_map={
            "present": True,
            "freshness": "in-memory",
            "namespaces": [],
        },
        candidates=[
            {
                "slug": "contract-probe",
                "status": "Shipped",
                "last_touched": "2020-01-01",
                "area": "unscoped",
                "eligible": True,
                "held_back_by": [],
                "obligations": [],
            }
        ],
        refusals=[],
        inbound_surfaces_not_reached=[],
        inbound_forms_recognised=[],
        inbound_forms_not_reached=[],
    )


def _validation_errors(document: dict, schema: dict) -> list[str]:
    contract = _load(
        "retirement_contract", "workspace_status_retirement_contract.py"
    )
    return contract.validate_document(document, schema)


def test_emitted_document_validates_against_live_schema() -> None:
    """The formatter's emitted document satisfies the schema in contracts/."""
    assert _validation_errors(_emitted_document(), _live_schema()) == []


def test_blocker_absent_from_live_schema_enum_fails_validation() -> None:
    """The validator reads the blocker vocabulary from the live schema."""
    schema = _live_schema()
    blocker_enum = schema["$defs"]["reason"]["properties"]["code"]["enum"]
    unlisted = "schema-enum-mutation-probe"
    assert unlisted not in blocker_enum

    document = _emitted_document()
    candidate = document["candidates"][0]
    candidate["eligible"] = False
    candidate["held_back_by"] = [{"code": unlisted}]

    errors = _validation_errors(document, schema)
    assert errors
    assert any("candidates/0/held_back_by/0/code" in error for error in errors)


def test_detector_blocker_codes_match_live_schema_enum() -> None:
    """A schema code without detector coverage fails instead of going unnoticed."""
    schema = _live_schema()
    blocker_enum = schema["$defs"]["reason"]["properties"]["code"]["enum"]
    candidates = _load(
        "retirement_candidates", "workspace_status_retirement_candidates.py"
    )
    assert frozenset(blocker_enum) == candidates.BLOCKER_CODES


def test_live_schema_xspec_resolves_to_its_declaring_spec() -> None:
    """The live x-spec pointer resolves to the spec that declares this contract."""
    schema = _live_schema()
    spec_files = [
        path
        for path in list_confined_regular_files(
            ROOT,
            ROOT / "docs/specs",
            max_files=5000,
            max_depth=8,
            max_entries=10000,
        )
        if path.name == "spec.md"
    ]
    declaring_dirs: list[Path] = []
    schema_name = Path(SCHEMA_REL).name
    for spec_path in spec_files:
        text = read_confined_regular_file(
            ROOT, spec_path, max_bytes=8 * 1024 * 1024
        ).decode("utf-8")
        contract_lines = [
            line for line in text.splitlines() if line.startswith("- **Contract:**")
        ]
        if any(schema_name in line for line in contract_lines):
            declaring_dirs.append(spec_path.parent)

    assert len(declaring_dirs) == 1
    expected = declaring_dirs[0].relative_to(ROOT).as_posix() + "/"
    assert schema.get("x-spec") == [expected]

    target = ROOT / expected
    validate_confined_directory(ROOT, target)
    read_confined_regular_file(ROOT, target / "spec.md", max_bytes=8 * 1024 * 1024)


RFC_REL = "docs/rfc/0096-portable-delivery-artifact-lifecycle.md"


def _section_two_roles() -> set[str]:
    """Return the roles RFC-0096 section 2's "Other roles are separate" sentence names.

    The sentence writes each role in prose and bolds it, so two are plural where
    the schema is singular (``decision records``, ``interface contracts``).  A
    byte-equality pin would therefore fail on correct data, so the comparison
    normalises a trailing ``s`` on the final word.  That normalisation is the
    whole licence this check takes: everything else must match exactly.
    """
    import re

    text = read_confined_regular_file(
        ROOT, ROOT / RFC_REL, max_bytes=8 * 1024 * 1024
    ).decode("utf-8")
    start = text.index("Other roles are separate")
    sentence = text[start : text.index("Runtime and handoff state", start)]
    roles: set[str] = set()
    for phrase in re.findall(r"\*\*([^*]+)\*\*", sentence):
        slug = re.sub(r"[^a-z]+", "-", phrase.lower()).strip("-")
        head, _, tail = slug.rpartition("-")
        roles.add(f"{head}-{tail[:-1]}" if head and tail.endswith("s") else slug)
    return roles


def test_semantic_role_enum_equals_rfc_section_two() -> None:
    """The schema's role enum is exactly what RFC-0096 section 2 names.

    The enum is a copy of a set another record owns, and this delivery has
    already watched a copied set drift.  Without this pin a role added to the
    schema, or removed from the RFC, goes unnoticed in both directions.
    """
    schema = _live_schema()
    enum = set(schema["$defs"]["obligation"]["properties"]["semantic_role"]["enum"])
    rfc_roles = _section_two_roles()

    assert len(rfc_roles) == 10, (
        f"RFC-0096 section 2 should name ten roles; extracted {sorted(rfc_roles)}"
    )
    assert enum == rfc_roles, (
        "The schema's semantic_role enum and RFC-0096 section 2 disagree.\n"
        f"  only in schema: {sorted(enum - rfc_roles)}\n"
        f"  only in RFC   : {sorted(rfc_roles - enum)}"
    )
