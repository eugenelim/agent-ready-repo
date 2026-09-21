from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
from argv_cases import ARGV_CASES
from knowledge_test_support import (
    KNOWLEDGE_STORE_SCRIPT,
    PACK_ROOT,
    PROJECT_KNOWLEDGE_SCRIPT,
    assert_strictly_rejected,
    capture_request_with_duplicate_key_bytes,
    capture_request_with_non_finite_number_bytes,
    capture_request_with_oversized_lesson,
    capture_request_with_producer_supplied_capture_id,
    capture_request_with_unknown_field,
    capture_request_with_unsafe_unicode,
    capture_request_without_provenance,
    initialize_empty_v1_repo,
    load_knowledge_store_module,
    load_project_knowledge_module,
    valid_capture_request,
    valid_work_item,
    valid_work_item_request,
)

# `PACK_ROOT` is `packs/core`; the kind-vocabulary sweep and the corpus
# replay both need paths outside the pack (the canonical schema, the
# packaged mirror, the work-loop linter, and the real committed corpus).
REPO_ROOT = PACK_ROOT.parents[1]
CANONICAL_SCHEMA = (
    REPO_ROOT / "contracts" / "jsonschema" / "knowledge-captured-observation.schema.json"
)
PACKAGED_SCHEMA_MIRROR = (
    REPO_ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / "knowledge-captured-observation.schema.json"
)
LINT_KNOWLEDGE_SCRIPT = (
    REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts" / "lint-knowledge.py"
)


def test_ac1_capture_parser_is_strict_and_versioned() -> None:
    module = load_project_knowledge_module()
    assert module.validate_capture_request(valid_capture_request())
    alternate_stream = valid_capture_request()
    alternate_stream["provenance"]["sources"][0]["path"] = "docs/source.txt:hidden"
    non_finite = capture_request_with_non_finite_number_bytes()
    assert b'"failed_attempts":NaN' in non_finite
    invalid_cases = (
        capture_request_with_unknown_field(),
        capture_request_with_duplicate_key_bytes(),
        non_finite,
        capture_request_with_unsafe_unicode(),
        capture_request_with_producer_supplied_capture_id(),
        capture_request_without_provenance(),
        capture_request_with_oversized_lesson(),
        alternate_stream,
    )
    for case in invalid_cases:
        assert_strictly_rejected(case)


def test_ac1_core_derives_capture_id_from_canonical_request() -> None:
    module = load_project_knowledge_module()
    request = valid_capture_request()
    compact = json.dumps(request, separators=(",", ":"), ensure_ascii=False).encode()
    reordered = json.dumps(
        dict(reversed(list(request.items()))),
        indent=2,
        ensure_ascii=True,
    ).encode("utf-8")

    expected = module.derive_capture_id_from_strict_json(compact)
    assert module.derive_capture_id_from_strict_json(reordered) == expected
    assert expected.startswith("kco-202608-")
    changed = copy.deepcopy(request)
    changed["lesson"] = "Prefer the published contract before adding a local format."
    assert module.derive_capture_id(changed) != expected
    assert "capture_id" not in module.capture_id_preimage_fields()


def test_ac19_fixed_v1_budgets_are_declared() -> None:
    module = load_project_knowledge_module()
    assert module.budget_contract() == {
        "capture_event_bytes": 16 * 1024,
        "journal_partition_bytes": 32 * 1024 * 1024,
        "journal_partition_events": 50_000,
        "retained_partitions": 240,
        "retained_journal_bytes": 512 * 1024 * 1024,
        "pending_page_partitions": 6,
        "pending_page_events": 10_000,
        "pending_page_bytes": 16 * 1024 * 1024,
        "topic_bytes": 128 * 1024,
        "occurrences_per_topic": 256,
        "topic_files": 50_000,
        "topic_corpus_bytes": 512 * 1024 * 1024,
        "map_entries": 50_000,
        "map_bytes": 32 * 1024 * 1024,
        "enquiry_bodies": 12,
        "enquiry_body_read_bytes": 1 * 1024 * 1024,
        "envelope_bytes": 32 * 1024,
        "script_seconds": 30,
        "automatic_retries": 0,
    }


def test_ac23_competency_question_vocabulary_is_exact() -> None:
    module = load_project_knowledge_module()
    assert module.competency_questions() == (
        "CQ-ORIENT",
        "CQ-DESIGN",
        "CQ-CHANGE",
        "CQ-DIAGNOSE",
        "CQ-REVIEW",
        "CQ-VERIFY",
        "CQ-OPERATE",
        "CQ-ROUTE",
        "CQ-RETIRE",
    )


def test_ac12_scope_serialization_is_platform_neutral_and_rejects_aliases() -> None:
    module = load_project_knowledge_module()
    assert module.serialize_scope(".") == "."
    assert module.serialize_scope(r"packages\core") == "packages/core"
    assert module.serialize_scope("cafe\u0301/component") == "caf\u00e9/component"
    for unsafe in (
        "con",
        "Con.txt",
        "../escape",
        "/absolute",
        "C:/absolute",
        "a//b",
        "docs/source.txt:hidden",
    ):
        with pytest.raises(ValueError):
            module.serialize_scope(unsafe)


def test_ac36_digest_contract_hashes_exact_bytes_without_normalization() -> None:
    module = load_project_knowledge_module()
    assert module.digest_bytes(b"line\r\n") != module.digest_bytes(b"line\n")
    assert module.digest_bytes(b"line\n") == {
        "kind": "sha256-bytes-v1",
        "sha256": hashlib.sha256(b"line\n").hexdigest(),
        "byte_length": 5,
    }
    with pytest.raises(ValueError):
        module.parse_digest({"kind": "sha1-bytes-v1", "sha1": "a" * 40})
    assert module.parse_digest(
        {"kind": "git-blob-v1", "algorithm": "sha1", "object_id": "a" * 40}
    )["kind"] == "git-blob-v1"
    with pytest.raises(ValueError):
        module.parse_digest(
            {"kind": "git-blob-v1", "algorithm": "sha1", "object_id": "a" * 64}
        )

    git_anchored = valid_capture_request()
    git_anchored["freshness_anchor"]["digest"] = {
        "kind": "git-blob-v1",
        "algorithm": "sha256",
        "object_id": "b" * 64,
    }
    assert module.validate_capture_request(git_anchored)


def test_ac37_diagnostics_are_typed_redacted_and_allowlisted() -> None:
    module = load_project_knowledge_module()
    codes = {
        "privacy",
        "provenance",
        "strict_parse",
        "confinement",
        "lock_contention",
        "lock_loss",
        "deadline_exceeded",
        "journal_capacity",
        "cursor_stale",
        "replay_required",
        "postimage_mismatch",
        "map_mismatch",
        "staged_dual_writer",
        "ambiguous_grouping",
        "forward_recovery_required",
    }
    # § D4's baseline: fifteen values before this spec's eleven additions.
    # `test_ac0037_every_d4_added_code_is_a_required_diagnostic_code` below
    # covers the addition, quantified over the D4 table rather than a
    # literal count, so this set stays the pre-existing floor rather than
    # growing into a second hand-written list of the same eleven codes.
    assert codes <= set(module.REQUIRED_DIAGNOSTIC_CODES)
    diagnostic = module.render_diagnostic(
        module.KnowledgeDiagnostic(
            reason_code="strict_parse",
            retryable=False,
            recovery_action="fix_request",
            path="contracts/jsonschema/knowledge-captured-observation.schema.json",
            line=1,
        )
    )
    assert set(diagnostic) <= module.SAFE_DIAGNOSTIC_FIELDS
    assert diagnostic["version"] == "knowledge-diagnostic.v1"
    assert "body" not in json.dumps(diagnostic)
    with pytest.raises(ValueError):
        module.KnowledgeDiagnostic(reason_code="unknown", retryable=False)


def test_version_selection_dispatches_on_payload_field() -> None:
    module = load_project_knowledge_module()
    validator = module.select_validator(
        {"request": {"contract_version": "knowledge-captured-observation.v1"}}
    )
    assert validator is module.CAPTURE_VALIDATORS["knowledge-captured-observation.v1"]
    assert module.select_validator({}) is None


def test_ac15_a_v1_record_validates_under_the_v1_validator_unchanged() -> None:
    module = load_project_knowledge_module()
    v1_request = valid_capture_request(contract_version="knowledge-captured-observation.v1")
    validator = module.select_validator({"request": v1_request})
    assert validator is module.CAPTURE_VALIDATORS["knowledge-captured-observation.v1"]
    assert validator(copy.deepcopy(v1_request)) == v1_request


def test_ac15_a_v2_record_validates_under_the_v2_validator() -> None:
    module = load_project_knowledge_module()
    v2_request = valid_capture_request(contract_version="knowledge-captured-observation.v2")
    validator = module.select_validator({"request": v2_request})
    assert validator is module.CAPTURE_VALIDATORS["knowledge-captured-observation.v2"]
    assert validator(copy.deepcopy(v2_request)) == v2_request
    assert module.validate_capture_request(copy.deepcopy(v2_request)) == v2_request


def test_ac16_a_record_with_no_request_object_never_reaches_version_selection() -> None:
    module = load_project_knowledge_module()
    disposition_shaped = {
        "event_type": "observation.dispositioned",
        "schema_version": "observation-event.v1",
    }
    assert module.select_validator(disposition_shaped) is None


def test_ac62_a_request_with_no_contract_version_is_refused() -> None:
    module = load_project_knowledge_module()
    payload = valid_capture_request()
    del payload["contract_version"]
    with pytest.raises(ValueError):
        module.select_validator({"request": payload})
    with pytest.raises(ValueError):
        module.validate_capture_request(payload)


def test_ac47_an_unknown_contract_version_is_refused_with_a_catalog_code() -> None:
    module = load_project_knowledge_module()
    payload = valid_capture_request(contract_version="knowledge-captured-observation.v3")
    with pytest.raises(ValueError):
        module.select_validator({"request": payload})
    with pytest.raises(ValueError):
        module.validate_capture_request(payload)
    assert "strict_parse" in module.REQUIRED_DIAGNOSTIC_CODES


def test_ac48_a_non_writable_version_is_refused_rather_than_re_stamped() -> None:
    module = load_project_knowledge_module()
    v1_request = valid_capture_request(contract_version="knowledge-captured-observation.v1")
    with pytest.raises(ValueError):
        module.select_validator({"request": v1_request}, require_writable=True)
    # validate_capture_request stays version-agnostic on purpose: knowledge_store
    # calls it from the read path too, so requiring writability here refuses every
    # stored legacy record. Binding the selector to the write path is T4's, per
    # docs/specs/work-item-capture/notes/amendment-002.md.
    assert module.validate_capture_request(dict(v1_request))


def test_ac18_the_writer_emits_the_writable_contract_version(tmp_path: Path) -> None:
    module = load_project_knowledge_module()
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    spec_dir = tmp_path / "docs" / "specs" / "example"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_bytes(b"# Example governing spec\n")
    semantic_input = {
        "lesson": "Keep producer-owned persistence fields out of workflow prose.",
        "kind": "pattern",
        "project_scope": {"paths": ["packs/core"], "audience": "project"},
        "competency_facets": ["CQ-CHANGE"],
        "destination_hint": {"type": "topic", "path": "docs/knowledge/example.md"},
        "provenance": {
            "sources": [
                {"path": "docs/specs/example/spec.md", "line_start": 1, "line_end": 1}
            ]
        },
        "privacy_attestation": {
            "reviewed": True,
            "contains_private_data": False,
            "contains_secrets": False,
            "contains_instructions": False,
        },
    }
    emitted = module.build_work_loop_capture_request(
        semantic_input,
        semantic_gate="spec-approved",
        artifact="docs/specs/example/spec.md",
        repo_root=tmp_path,
    )
    assert emitted["contract_version"] == "knowledge-captured-observation.v2"
    assert emitted["contract_version"] == module.CONTRACT_VERSION


def _journal_bytes(repo: Path) -> bytes:
    root = repo / "docs" / "knowledge" / "observations"
    if not root.exists():
        return b""
    return b"".join(path.read_bytes() for path in sorted(root.glob("*/*.jsonl")))


def test_element_beginning_with_dash_is_refused() -> None:
    """`stub: true` red case named in the plan: an option is never read-only."""

    module = load_project_knowledge_module()
    request = valid_capture_request(
        verification_route={"command": ["ls", "-la", "docs"], "path": "docs"}
    )
    with pytest.raises(module.VerificationRouteRefusal) as refused:
        module.validate_capture_request(request)
    assert refused.value.reason_code == "work_item_command_option"


@pytest.mark.parametrize(
    "argv,expected_code,why",
    ARGV_CASES,
    ids=[f"{index:02d}" for index in range(len(ARGV_CASES))],
)
def test_every_d6_case_row_reproduces_its_recorded_verdict(
    argv: object, expected_code: str | None, why: str
) -> None:
    """Drives every row of `argv_cases.py` — generated from the spike, not
    retyped from the spec table — through the same seam § D6 binds
    (AC-0049 - AC-0060). A row whose verdict changes here is a contract
    change to docs/specs/work-item-capture/spec.md § D6, not a fixture
    edit.
    """

    module = load_project_knowledge_module()
    request = valid_capture_request(
        verification_route={"command": argv, "path": "docs/x.md"}
    )
    if expected_code is None:
        assert module.validate_capture_request(copy.deepcopy(request))
    else:
        with pytest.raises(module.VerificationRouteRefusal) as refused:
            module.validate_capture_request(copy.deepcopy(request))
        assert refused.value.reason_code == expected_code, why


def test_ac0049_an_admitted_argv_round_trips_through_the_store_unchanged(
    tmp_path: Path,
) -> None:
    store = load_knowledge_store_module()
    repo = initialize_empty_v1_repo(tmp_path, store)
    submitted = ["grep", "pattern", "src/a.py"]
    request = valid_capture_request(
        verification_route={"command": submitted, "path": "src/a.py"}
    )
    request["observed_at"] = "2026-08-13T12:34:56Z"
    store.capture_observation(repo, request, writer_time="2026-08-13T12:40:00Z")
    root = repo / "docs" / "knowledge" / "observations"
    events = [
        json.loads(line)
        for path in sorted(root.glob("*/*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(events) == 1
    read_back = events[0]["request"]["verification_route"]["command"]
    assert read_back == submitted
    for submitted_element, read_back_element in zip(submitted, read_back, strict=True):
        assert submitted_element == read_back_element


def test_every_d6_refusal_leaves_the_store_byte_equal(tmp_path: Path) -> None:
    store = load_knowledge_store_module()
    repo = initialize_empty_v1_repo(tmp_path, store)
    before = _journal_bytes(repo)
    for argv, expected_code, _why in ARGV_CASES:
        if expected_code is None:
            continue
        request = valid_capture_request(
            verification_route={"command": argv, "path": "docs/x.md"}
        )
        request["observed_at"] = "2026-08-13T12:34:56Z"
        with pytest.raises(store.KnowledgeStoreError):
            store.capture_observation(repo, request, writer_time="2026-08-13T12:40:00Z")
        assert _journal_bytes(repo) == before


def test_ac0065_verification_route_path_refuses_a_dot_leading_component() -> None:
    module = load_project_knowledge_module()
    for unsafe_path in (".ssh/id_rsa", ".env", ".git/config", "."):
        request = valid_capture_request(
            verification_route={"command": ["cat", "docs/x.md"], "path": unsafe_path}
        )
        with pytest.raises(module.VerificationRouteRefusal) as refused:
            module.validate_capture_request(request)
        assert refused.value.reason_code == "work_item_command_path"


def test_defect_missing_finished_state_is_refused() -> None:
    """`stub: true` red case named in the plan: every base field § D2
    requires is enforced, `finished_state` among them."""

    module = load_project_knowledge_module()
    request = valid_work_item_request("defect")
    del request["work_item"]["finished_state"]
    with pytest.raises(module.WorkItemRefusal) as refused:
        module.validate_capture_request(request)
    assert refused.value.reason_code == "work_item_incomplete"


def test_ac0003_a_work_item_missing_any_shape_required_field_is_refused() -> None:
    """Walks `WORK_ITEM_SHAPES` — the closed set — rather than a hardcoded
    list, so a shape added there without a matching entry in
    `WORK_ITEM_SHAPE_REQUIRED_FIELDS` fails this test with a `KeyError`
    instead of going unchecked."""

    module = load_project_knowledge_module()
    for shape in module.WORK_ITEM_SHAPES:
        required_fields = set(module.WORK_ITEM_BASE_REQUIRED_FIELDS) | set(
            module.WORK_ITEM_SHAPE_REQUIRED_FIELDS[shape]
        )
        for field in required_fields:
            request = valid_work_item_request(shape)
            del request["work_item"][field]
            with pytest.raises(ValueError):
                module.validate_capture_request(request)


@pytest.mark.parametrize("shape", ["defect", "question", "decision"])
def test_ac0004_a_complete_work_item_record_of_each_shape_is_written(shape: str) -> None:
    module = load_project_knowledge_module()
    request = valid_work_item_request(shape)
    assert module.validate_capture_request(request)


def test_ac0005_a_defect_without_a_route_but_with_observed_and_intended_is_written() -> None:
    module = load_project_knowledge_module()
    request = valid_work_item_request("defect")
    del request["verification_route"]
    assert module.validate_capture_request(request)


@pytest.mark.parametrize("shape", ["question", "decision"])
def test_ac0006_a_question_or_decision_without_a_route_is_written(shape: str) -> None:
    module = load_project_knowledge_module()
    request = valid_work_item_request(shape)
    del request["verification_route"]
    assert module.validate_capture_request(request)


def test_ac0046_verification_route_is_validated_regardless_of_kind() -> None:
    """`verification_route` is a kind-agnostic top-level property validated
    by one shared function (§ D6): a `work-item` and a `gotcha` carrying the
    identical option-bearing command are both refused, with the same code,
    which is what proves the binding is not scoped to the `work-item`
    branch alone."""

    module = load_project_knowledge_module()
    bad_route = {"command": ["bash", "-c", "echo hi"], "path": "docs/x.md"}

    work_item_request = valid_work_item_request("defect", verification_route=bad_route)
    with pytest.raises(module.VerificationRouteRefusal) as work_item_refusal:
        module.validate_capture_request(work_item_request)

    non_work_item_request = valid_capture_request(verification_route=bad_route)
    with pytest.raises(module.VerificationRouteRefusal) as other_kind_refusal:
        module.validate_capture_request(non_work_item_request)

    assert (
        work_item_refusal.value.reason_code
        == other_kind_refusal.value.reason_code
        == "work_item_command_option"
    )


def test_ac0007_an_absent_blocker_is_refused_with_work_item_incomplete() -> None:
    module = load_project_knowledge_module()
    request = valid_work_item_request("question")
    del request["work_item"]["blocker"]
    with pytest.raises(module.WorkItemRefusal) as refused:
        module.validate_capture_request(request)
    assert refused.value.reason_code == "work_item_incomplete"


def test_ac0008_an_out_of_set_blocker_is_refused_with_work_item_not_blocked() -> None:
    module = load_project_knowledge_module()
    request = valid_work_item_request("question")
    request["work_item"] = valid_work_item("question", blocker="urgency")
    with pytest.raises(module.WorkItemRefusal) as refused:
        module.validate_capture_request(request)
    assert refused.value.reason_code == "work_item_not_blocked"
    # AC-0007 and AC-0008 must carry different codes.
    assert refused.value.reason_code != "work_item_incomplete"


def test_ac0009_a_decision_with_empty_significance_is_refused() -> None:
    module = load_project_knowledge_module()
    request = valid_work_item_request("decision")
    request["work_item"] = valid_work_item("decision", significance=[])
    with pytest.raises(module.WorkItemRefusal) as refused:
        module.validate_capture_request(request)
    assert refused.value.reason_code == "work_item_threshold"


def test_ac0013_a_written_work_item_record_carries_a_necessity_rationale() -> None:
    module = load_project_knowledge_module()
    request = valid_work_item_request("question")
    validated = module.validate_capture_request(request)
    assert validated["work_item"]["necessity_rationale"]


def test_work_item_statement_reaches_privacy_scan() -> None:
    """`stub: true` red case named in the plan: `work_item.statement` is one
    of the six free-text fields `AC-0031` requires the deterministic privacy
    scan to reach. Before that scan is wired, a violating string here is
    admitted rather than refused."""

    module = load_project_knowledge_module()
    request = valid_work_item_request("question")
    request["work_item"]["statement"] = "Reach out to agent@example.com about this."
    with pytest.raises(module.PrivacyRefusal):
        module.validate_capture_request(request)


# --- T5: the scanned field set is derived from the schema, not hand-written -
#
# AC-0031 requires the six `work_item` free-text fields the privacy scan
# reaches to be *derived* from the canonical schema document at test time —
# every `work_item` property that resolves (through its `$ref`, where
# present) to `type: string` with no `enum` — rather than compared against a
# second hand-written list beside the implementation's own list. The
# derivation below is that mechanism; `WORK_ITEM_SCANNED_FREE_TEXT_FIELDS` in
# `project_knowledge.py` is the only hand-written list, and this file checks
# it against the schema rather than repeating it.


def _work_item_schema_properties() -> tuple[dict[str, Any], dict[str, Any]]:
    schema = json.loads(CANONICAL_SCHEMA.read_text(encoding="utf-8"))
    return schema["properties"]["work_item"]["properties"], schema["$defs"]


def _resolve_schema_ref(prop: dict[str, Any], definitions: dict[str, Any]) -> dict[str, Any]:
    """Resolve a `{"$ref": "#/$defs/<name>"}` property to its definition.

    Every `work_item` free-text field is written in the schema as a `$ref`
    to `safeText2000`, not an inline `type: string` — a walk that reads
    `prop.get("type")` without resolving the ref first would see nothing and
    silently derive an empty set.
    """

    if "$ref" in prop:
        name = prop["$ref"].removeprefix("#/$defs/")
        return definitions[name]
    return prop


def _derive_work_item_free_text_fields() -> set[str]:
    """§ D2's rule, run against the schema **document** — every `work_item`
    property that is string-typed and carries no `enum` — not a record
    instance, which would drop an unset optional field."""

    properties, definitions = _work_item_schema_properties()
    return {
        name
        for name, prop in properties.items()
        if (resolved := _resolve_schema_ref(prop, definitions)).get("type") == "string"
        and "enum" not in resolved
    }


def test_ac0031_the_scanned_field_set_is_derived_from_the_schema() -> None:
    module = load_project_knowledge_module()
    derived = _derive_work_item_free_text_fields()
    # The comparison, not this loop, is what makes a `work_item` property
    # added later without a matching production update fail this suite.
    assert derived == set(module.WORK_ITEM_SCANNED_FREE_TEXT_FIELDS)
    assert derived == {
        "statement",
        "finished_state",
        "necessity_rationale",
        "observed",
        "intended",
        "answered_by",
    }


def test_ac0031_every_work_item_property_reaches_a_scan_or_is_excluded_on_a_stated_ground() -> (
    None
):
    """Without this, a `work_item` property added later as an array of free
    text is excluded by "string-typed", reaches no scan, and the
    derived-set comparison above still passes — the string case fails
    loudly and the array case would not. Walking **every** property, not
    only the string-typed ones, is what closes that gap. `shape` and
    `blocker` are string-typed but enumerated; `significance` is an array of
    enumerated values. All three are excluded on the same ground: a
    violating value in a closed set is refused by the enum check before any
    scan runs, so the case could not fail."""

    properties, _definitions = _work_item_schema_properties()
    scanned = _derive_work_item_free_text_fields()
    excluded_on_stated_ground = {"shape", "blocker", "significance"}
    assert set(properties) == scanned | excluded_on_stated_ground


# The shape each field needs to be present under § D2 — domain knowledge
# about *which record carries which field*, distinct from the *set itself*
# the two tests above already pin against the schema.
_WORK_ITEM_FREE_TEXT_FIELD_SHAPES = {
    "statement": "question",
    "finished_state": "question",
    "necessity_rationale": "question",
    "observed": "defect",
    "intended": "defect",
    "answered_by": "question",
}


@pytest.mark.parametrize(
    "field,shape", sorted(_WORK_ITEM_FREE_TEXT_FIELD_SHAPES.items())
)
def test_ac0031_each_work_item_free_text_field_reaches_the_privacy_scan(
    field: str, shape: str
) -> None:
    module = load_project_knowledge_module()
    request = valid_work_item_request(shape)
    request["work_item"][field] = "Reach out to agent@example.com about this."
    with pytest.raises(module.PrivacyRefusal):
        module.validate_capture_request(request)


# --- T5: every § D6 command element after argv[0] reaches the text scan ----


def test_ac0061_each_command_element_after_argv0_reaches_the_text_scan_only() -> None:
    """The claim AC-0061 makes is **which scan function each element
    reached**, not that the element was refused: a refusal assertion passes
    with the wrong scan wired, because most discriminating strings are
    refused by § D6 before any scan runs. `argv[0]` is outside the
    quantifier because the four-member allowlist refuses anything else
    before the scan runs, so an index-0 case could not fail."""

    module = load_project_knowledge_module()
    text_calls: list[tuple[str, ...]] = []
    path_calls: list[tuple[str, ...]] = []
    original_text = module.assert_persistable_text
    original_paths = module.assert_persistable_paths

    def spy_text(*values: str) -> None:
        text_calls.append(values)
        original_text(*values)

    def spy_paths(*values: str) -> None:
        path_calls.append(values)
        original_paths(*values)

    module.assert_persistable_text = spy_text
    module.assert_persistable_paths = spy_paths

    # `path` is deliberately distinct from every command element: it
    # legitimately reaches `assert_persistable_paths` in its own right
    # (`verification_route.path`), and sharing a value with a command
    # element would make that field's own scan look like the command
    # element's, defeating the discrimination this test drives.
    command = ["cat", "docs/a-b_c.py"]
    request = valid_capture_request(
        verification_route={"command": command, "path": "tools/catalogue/check_contract_parity.py"}
    )
    assert module.validate_capture_request(request)

    scanned_text_values = {value for call in text_calls for value in call}
    scanned_path_values = {value for call in path_calls for value in call}
    for element in command[1:]:
        assert element in scanned_text_values
        assert element not in scanned_path_values


def test_ac0061_two_end_to_end_cases_discriminate_the_text_scan_from_the_path_scan() -> None:
    """`_URL` and `_NON_HTTP_LOCATOR` both need a colon, which the
    re-anchored `repositoryPath` rule refuses before any scan runs, so a
    plain refusal assertion does not discriminate which scan ran. These two
    cases clear every § D6 rule and are refused by `assert_persistable_text`
    alone; wiring the wrong scan (`assert_persistable_paths`, which carries
    `_EMAIL`, `_USER_PATH`, `_SECRET_SHAPE` and `_PRIVATE_IDENTIFIER` but not
    `_URL`, `_NON_HTTP_LOCATOR` or `_BARE_HOSTNAME`) would admit both."""

    module = load_project_knowledge_module()
    bare_hostname_request = valid_capture_request(
        verification_route={"command": ["cat", "example.com"], "path": "docs/x.md"}
    )
    with pytest.raises(module.PrivacyRefusal):
        module.validate_capture_request(bare_hostname_request)

    grep_pattern_url_request = valid_capture_request(
        verification_route={
            "command": ["grep", "https://evil.example.com/x", "docs"],
            "path": "docs/x.md",
        }
    )
    with pytest.raises(module.PrivacyRefusal):
        module.validate_capture_request(grep_pattern_url_request)


# --- T5: every § D4-added code is a `REQUIRED_DIAGNOSTIC_CODES` member ------


def test_ac0037_every_d4_added_code_is_returned_by_its_refusal_and_is_a_catalog_member() -> (
    None
):
    """Quantified over § D4's table rather than a literal count: the seven
    command-shaped codes are read straight from `ARGV_CASES` — T3's own
    fixture, not a second hand list — so a row added there with a new code
    becomes a case here automatically. `work_item_unnecessary` has no
    validator-level trigger: it is the necessity razor's own verdict, a
    reasoning-tier judgement `docs/specs/work-item-capture/plan.md`'s T7
    wires the dispatch for; it is asserted as a catalog member only."""

    module = load_project_knowledge_module()

    def refuse_incomplete() -> None:
        request = valid_work_item_request("question")
        del request["work_item"]["blocker"]
        module.validate_capture_request(request)

    def refuse_not_blocked() -> None:
        request = valid_work_item_request("question")
        request["work_item"] = valid_work_item("question", blocker="urgency")
        module.validate_capture_request(request)

    def refuse_threshold() -> None:
        request = valid_work_item_request("decision")
        request["work_item"] = valid_work_item("decision", significance=[])
        module.validate_capture_request(request)

    triggers: dict[str, Any] = {
        "work_item_incomplete": refuse_incomplete,
        "work_item_not_blocked": refuse_not_blocked,
        "work_item_threshold": refuse_threshold,
    }
    for argv, code, _why in ARGV_CASES:
        if code is None or code in triggers:
            continue

        def trigger(argv: object = argv) -> None:
            request = valid_capture_request(
                verification_route={"command": argv, "path": "docs/x.md"}
            )
            module.validate_capture_request(request)

        triggers[code] = trigger

    for code, trigger in triggers.items():
        with pytest.raises(ValueError) as excinfo:
            trigger()
        assert getattr(excinfo.value, "reason_code", None) == code
        assert code in module.REQUIRED_DIAGNOSTIC_CODES

    assert "work_item_unnecessary" in module.REQUIRED_DIAGNOSTIC_CODES


# --- T4: the kind-vocabulary sweep and its negative control ----------------
#
# Five capture-kind sites must hold exactly the same four values, and four
# other literal sets holding the same three old values must not move (§ D1's
# complement argument: a work item is generalisable practice's complement,
# so admitting it into a synthesis or legacy-lint vocabulary would
# contradict the contract). Both checks parse each site's own enum from its
# source rather than `grep`-ing for a fixed string, because a site holding
# the old set and one holding the new set both match the same `grep`. Each
# helper returns `None` for a site whose pattern no longer matches, so a
# site silently dropped from its source shows up as a falling count against
# the floor below rather than a passed, empty sweep.

_OLD_KIND_VOCABULARY = {"pattern", "gotcha", "antipattern"}
_CAPTURE_KIND_VOCABULARY = _OLD_KIND_VOCABULARY | {"work-item"}
_MIN_CAPTURE_KIND_SITES = 5
_MIN_NON_CAPTURE_KIND_SITES = 4


def _schema_kind_enum(path: Path) -> set[str] | None:
    schema = json.loads(path.read_text(encoding="utf-8"))
    enum = schema.get("properties", {}).get("kind", {}).get("enum")
    return set(enum) if isinstance(enum, list) else None


def _quoted_literal_set(source: str, pattern: str) -> set[str] | None:
    match = re.search(pattern, source)
    if match is None:
        return None
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def _capture_kind_sites() -> dict[str, set[str]]:
    store_source = KNOWLEDGE_STORE_SCRIPT.read_text(encoding="utf-8")
    validator_source = PROJECT_KNOWLEDGE_SCRIPT.read_text(encoding="utf-8")
    candidates = {
        "canonical schema `properties.kind.enum`": _schema_kind_enum(CANONICAL_SCHEMA),
        "packaged schema mirror `properties.kind.enum`": _schema_kind_enum(
            PACKAGED_SCHEMA_MIRROR
        ),
        "project_knowledge.py request validator": _quoted_literal_set(
            validator_source, r'request\["kind"\]\s+not in\s+\{([^}]+)\}'
        ),
        "knowledge_store.py partition allowlist": _quoted_literal_set(
            store_source, r'parts\[1\]\s+not in\s+\{([^}]+)\}'
        ),
        "knowledge_store.py kind enumerator": _quoted_literal_set(
            store_source, r'for kind in\s+\(([^)]+)\):'
        ),
    }
    return {name: values for name, values in candidates.items() if values is not None}


def _non_capture_kind_sites() -> dict[str, set[str]]:
    store_source = KNOWLEDGE_STORE_SCRIPT.read_text(encoding="utf-8")
    lint_source = LINT_KNOWLEDGE_SCRIPT.read_text(encoding="utf-8")
    candidates = {
        "knowledge_store.py topic synthesis kind": _quoted_literal_set(
            store_source, r'topic\["synthesis"\]\["kind"\]\s+not in\s+\{([^}]+)\}'
        ),
        "knowledge_store.py proposal synthesis kind": _quoted_literal_set(
            store_source, r'proposal\["synthesis"\]\.get\("kind"\)\s+not in\s+\{([^}]+)\}'
        ),
        "knowledge_store.py legacy row kind": _quoted_literal_set(
            store_source, r'row\["kind"\]\s+not in\s+\{([^}]+)\}'
        ),
        "lint-knowledge.py ALLOWED_KINDS": _quoted_literal_set(
            lint_source, r'ALLOWED_KINDS\s*=\s*\{([^}]+)\}'
        ),
    }
    return {name: values for name, values in candidates.items() if values is not None}


def test_the_five_capture_kind_sites_agree_on_the_same_four_values() -> None:
    sites = _capture_kind_sites()
    assert len(sites) >= _MIN_CAPTURE_KIND_SITES, (
        f"found only {len(sites)} capture-kind site(s): {sorted(sites)}; "
        f"the sweep must reach at least {_MIN_CAPTURE_KIND_SITES}, so a site "
        "that stopped matching its pattern is a regression, not a pass."
    )
    mismatched = {
        name: sorted(values)
        for name, values in sites.items()
        if values != _CAPTURE_KIND_VOCABULARY
    }
    assert not mismatched, (
        f"expected every capture-kind site to hold {sorted(_CAPTURE_KIND_VOCABULARY)}; "
        f"found {mismatched}"
    )


def test_the_four_non_capture_kind_sets_still_hold_the_old_three_values() -> None:
    sites = _non_capture_kind_sites()
    assert len(sites) >= _MIN_NON_CAPTURE_KIND_SITES, (
        f"found only {len(sites)} non-capture kind site(s): {sorted(sites)}; "
        f"the control must reach at least {_MIN_NON_CAPTURE_KIND_SITES}, so a "
        "site that stopped matching its pattern is a regression, not a pass."
    )
    widened = {
        name: sorted(values)
        for name, values in sites.items()
        if values != _OLD_KIND_VOCABULARY
    }
    assert not widened, (
        f"these sites must still hold only {sorted(_OLD_KIND_VOCABULARY)} — "
        f"widening any of them admits `work-item` into a distillation or "
        f"legacy-lint vocabulary § D1 forbids it from: {widened}"
    )


# --- T4: the write path refuses a non-writable version; the read path does not

def test_capture_observation_refuses_a_non_writable_version_and_writes_nothing(
    tmp_path: Path,
) -> None:
    """`_check_pre_admission` is bound to
    `select_validator(..., require_writable=True)`: a v1 submission at the
    write path is refused with a catalog code and nothing is written
    (AC-0048). `_validate_event`, the read-path sibling, stays
    version-agnostic — proved by the corpus replay below, per
    docs/specs/work-item-capture/notes/amendment-002.md."""

    store = load_knowledge_store_module()
    repo = initialize_empty_v1_repo(tmp_path, store)
    before = _journal_bytes(repo)
    request = valid_capture_request(contract_version="knowledge-captured-observation.v1")
    request["observed_at"] = "2026-08-13T12:34:56Z"
    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.capture_observation(repo, request, writer_time="2026-08-13T12:40:00Z")
    assert refused.value.diagnostic["reason_code"] == "provenance"
    assert _journal_bytes(repo) == before


def test_a_work_item_record_round_trips_through_the_store(tmp_path: Path) -> None:
    """Running the write path during PLAN showed the request validator
    refuses the kind first and the partition validator refuses the
    directory second, so both must widen before this passes."""

    store = load_knowledge_store_module()
    repo = initialize_empty_v1_repo(tmp_path, store)
    request = valid_work_item_request("question")
    request["observed_at"] = "2026-08-13T12:34:56Z"
    receipt = store.capture_observation(repo, request, writer_time="2026-08-13T12:40:00Z")
    assert receipt["partition"] == "observations/work-item/2026-08.jsonl"
    events = [
        json.loads(line)
        for path in sorted((repo / "docs" / "knowledge" / "observations").glob("*/*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(events) == 1
    assert events[0]["request"]["kind"] == "work-item"
    assert events[0]["capture_id"] == receipt["capture_id"]


def test_the_real_corpus_replays_through_version_selection_and_bytes_are_unchanged() -> None:
    """The store replay `## Construction tests` schedules to T4: every
    record in the real corpus, partitioned on whether it carries a capture
    payload, reads clean, and no file's bytes are touched (AC-0015,
    AC-0016, AC-0017). No record count appears anywhere — the store is
    append-only and grows on every capture, so a literal count would be
    stale before this test runs again."""

    pk_module = load_project_knowledge_module()
    store = load_knowledge_store_module()
    knowledge_root = REPO_ROOT / "docs" / "knowledge"
    jsonl_paths = sorted((knowledge_root / "observations").glob("*/*.jsonl"))
    assert jsonl_paths, "the real corpus must hold at least one partition to replay"
    before = {path: path.read_bytes() for path in jsonl_paths}

    capture_payload_seen = False
    envelope_only_seen = False
    for path, raw in before.items():
        for line in raw.decode("utf-8").splitlines():
            if not line:
                continue
            record = json.loads(line)
            if "request" in record:
                validator = pk_module.select_validator(record)
                assert validator is not None
                validator(copy.deepcopy(record["request"]))
                capture_payload_seen = True
            else:
                # No capture payload: outside version selection entirely,
                # read through the `observation-event.v1` envelope only.
                assert pk_module.select_validator(record) is None
                envelope_only_seen = True
        # The real read path, not a reimplementation of it: this is what
        # amendment-002's regression broke, and a 221-test green suite did
        # not catch it because nothing exercised real legacy content here.
        partition = path.relative_to(knowledge_root).as_posix()
        list(store._read_events(path, partition))

    assert capture_payload_seen, "the corpus must exercise the capture-payload partition"
    assert envelope_only_seen, "the corpus must exercise the envelope-only partition"
    for path, raw in before.items():
        assert path.read_bytes() == raw
