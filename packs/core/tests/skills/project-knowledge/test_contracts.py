from __future__ import annotations

import copy
import hashlib
import json

import pytest
from knowledge_test_support import (
    assert_strictly_rejected,
    assert_valid,
    bundled_contract_bytes,
    capture_request_with_duplicate_key_bytes,
    capture_request_with_non_finite_number_bytes,
    capture_request_with_oversized_lesson,
    capture_request_with_producer_supplied_capture_id,
    capture_request_with_unknown_field,
    capture_request_with_unsafe_unicode,
    capture_request_without_provenance,
    load_project_knowledge_module,
    load_public_schema,
    public_contract_bytes,
    valid_capture_request,
)


def test_ac1_public_capture_schema_is_strict_and_versioned() -> None:
    schema = load_public_schema("knowledge-captured-observation.schema.json")
    assert schema["additionalProperties"] is False
    assert schema["contract_version"] == "knowledge-captured-observation.v1"
    assert "capture_id" not in schema["properties"]
    assert_valid(schema, valid_capture_request())
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
        assert_strictly_rejected(schema, case)
    assert public_contract_bytes() == bundled_contract_bytes()


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

    schema = load_public_schema()
    git_anchored = valid_capture_request()
    git_anchored["freshness_anchor"]["digest"] = {
        "kind": "git-blob-v1",
        "algorithm": "sha256",
        "object_id": "b" * 64,
    }
    assert_valid(schema, git_anchored)


def test_ac37_diagnostics_are_typed_redacted_and_allowlisted() -> None:
    module = load_project_knowledge_module()
    codes = {
        "privacy",
        "provenance",
        "strict_parse",
        "confinement",
        "lock_contention",
        "lock_loss",
        "journal_capacity",
        "cursor_stale",
        "replay_required",
        "postimage_mismatch",
        "map_mismatch",
        "staged_dual_writer",
        "ambiguous_grouping",
        "forward_recovery_required",
    }
    assert set(module.REQUIRED_DIAGNOSTIC_CODES) == codes
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
