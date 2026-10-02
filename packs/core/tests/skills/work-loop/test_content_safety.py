"""Tests for _content_safety.py — AC-0014 and AC-0015 TDD suite.

Mode: TDD through integration tests (per plan.md T2).

This suite:
- Tests the complete AC-0014 corpus: credential, personal-data,
  control-character, encoding, executable-structure, unknown-field
  (authority-shaped), edge, and edge-plus-one size.
- Asserts identical normalized decisions per boundary for the shared corpus.
- Tests missing/unknown profile refusals without payload persistence.
- Tests AC-0015: rejected decisions carry no payload bytes, excerpts, or
  content-derived hashes; accepted prose is typed UntrustedData that cannot
  select tools, actions, paths, or authority.

Follows the _loop_guards.py loader pattern (importlib.util.spec_from_file_location)
so the module remains unregistered in sys.modules between test sessions.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)
MODULE_PATH = SCRIPTS / "_content_safety.py"

# ── module loader ────────────────────────────────────────────────────────────


def _load_module(name: str = "cs_under_test") -> ModuleType:
    """Load a fresh, unregistered copy of _content_safety following the guards pattern."""
    spec = importlib.util.spec_from_file_location(name, str(MODULE_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def cs() -> ModuleType:
    return _load_module()


# ── corpus payloads ──────────────────────────────────────────────────────────

# GitHub personal access token (classic form, 40-char suffix)
CREDENTIAL_PAYLOAD = b"token: ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA1234"

# Email address — a direct personal identifier
PERSONAL_DATA_PAYLOAD = b"contact: user@example.com"

# C0 control character (null byte) — not valid in policy-admitted content
CONTROL_CHAR_PAYLOAD = b"text with null byte: \x00 here"

# Invalid UTF-8 — not decodable as the required encoding
ENCODING_PAYLOAD = bytes([0xFF, 0xFE, 0x00, 0x41])

# JSON tool-call object — executable structure that must be rejected
EXECUTABLE_PAYLOAD = b'{"tool_call": {"name": "bash", "args": ["ls"]}}'

# Authority-shaped field — must be rejected as executable structure
UNKNOWN_FIELD_PAYLOAD = b'{"_grant": "admin", "value": "structured"}'

# Clean, safe payload that must be accepted
CLEAN_PAYLOAD = b"review-id: initial-plan-review-001"

# Size-boundary payloads for structured-control (max_bytes = 64 KiB)
_64KB = 64 * 1024
STRUCTURED_EDGE_PAYLOAD = b"a" * _64KB
STRUCTURED_EDGE_PLUS_ONE = b"a" * (_64KB + 1)

# All Slice 1 boundaries and their assigned profiles.
# Must mirror SLICE_1_WRITER_BOUNDARIES in the module.
_SLICE1_BOUNDARIES: list[tuple[str, str]] = [
    ("initial-plan-review.v1", "structured-control"),
    ("approval-record.v1", "structured-control"),
    ("reviewed-execution-envelope.v1", "structured-control"),
    ("security-event.v1", "structured-control"),
    ("semantic-evidence-transaction.v1", "structured-control"),
    ("evidence-receipt.v1", "evidence-embedded-record"),
    ("evidence-supersession.v1", "evidence-embedded-record"),
]


# ── AC-0015 helper: assert no payload in rejected decision ───────────────────


def _assert_no_payload_in_decision(decision: object, payload: bytes) -> None:
    """AC-0015: a rejected decision must carry no payload bytes or content hash."""
    # normalized_record_digest must be absent
    assert getattr(decision, "normalized_record_digest", None) is None, (
        f"Rejected decision (code={getattr(decision, 'decision_code', '?')!r}) "
        f"carries normalized_record_digest — must be absent on rejection (AC-0015)"
    )


# ── AC-0014: missing / unknown profile refuses ───────────────────────────────


def test_missing_profile_refuses(cs: ModuleType) -> None:
    """A completely absent profile name returns rejected-missing-profile (AC-0014)."""
    decision = cs.check_content_safety(
        "nonexistent-profile", CLEAN_PAYLOAD, source_record_id="r001"
    )
    assert decision.decision_code == "rejected-missing-profile"
    _assert_no_payload_in_decision(decision, CLEAN_PAYLOAD)


def test_unknown_profile_refuses(cs: ModuleType) -> None:
    """A future/unknown profile name also returns rejected-missing-profile."""
    decision = cs.check_content_safety(
        "UNKNOWN-PROFILE-2099", CLEAN_PAYLOAD, source_record_id="r002"
    )
    assert decision.decision_code == "rejected-missing-profile"
    _assert_no_payload_in_decision(decision, CLEAN_PAYLOAD)


# ── AC-0014: corpus × boundary cross tests ───────────────────────────────────


@pytest.mark.parametrize(
    "boundary,profile",
    [pytest.param(b, p, id=b) for b, p in _SLICE1_BOUNDARIES],
)
def test_credential_rejected_at_all_boundaries(
    cs: ModuleType, boundary: str, profile: str
) -> None:
    """Credential payload is rejected at every Slice 1 boundary (AC-0014)."""
    decision = cs.check_content_safety(
        profile, CREDENTIAL_PAYLOAD, source_record_id=boundary
    )
    assert decision.decision_code == "rejected-credential", (
        f"boundary={boundary!r}: expected rejected-credential, "
        f"got {decision.decision_code!r}"
    )
    _assert_no_payload_in_decision(decision, CREDENTIAL_PAYLOAD)


@pytest.mark.parametrize(
    "boundary,profile",
    [pytest.param(b, p, id=b) for b, p in _SLICE1_BOUNDARIES],
)
def test_personal_data_rejected_at_all_boundaries(
    cs: ModuleType, boundary: str, profile: str
) -> None:
    """Personal-data payload is rejected at every Slice 1 boundary (AC-0014)."""
    decision = cs.check_content_safety(
        profile, PERSONAL_DATA_PAYLOAD, source_record_id=boundary
    )
    assert decision.decision_code == "rejected-personal-data", (
        f"boundary={boundary!r}: expected rejected-personal-data, "
        f"got {decision.decision_code!r}"
    )
    _assert_no_payload_in_decision(decision, PERSONAL_DATA_PAYLOAD)


@pytest.mark.parametrize(
    "boundary,profile",
    [pytest.param(b, p, id=b) for b, p in _SLICE1_BOUNDARIES],
)
def test_control_char_rejected_at_all_boundaries(
    cs: ModuleType, boundary: str, profile: str
) -> None:
    """Control-character payload is rejected at every Slice 1 boundary (AC-0014)."""
    decision = cs.check_content_safety(
        profile, CONTROL_CHAR_PAYLOAD, source_record_id=boundary
    )
    assert decision.decision_code == "rejected-encoding", (
        f"boundary={boundary!r}: expected rejected-encoding, "
        f"got {decision.decision_code!r}"
    )
    _assert_no_payload_in_decision(decision, CONTROL_CHAR_PAYLOAD)


@pytest.mark.parametrize(
    "boundary,profile",
    [pytest.param(b, p, id=b) for b, p in _SLICE1_BOUNDARIES],
)
def test_invalid_encoding_rejected_at_all_boundaries(
    cs: ModuleType, boundary: str, profile: str
) -> None:
    """Invalid-UTF-8 payload is rejected at every Slice 1 boundary (AC-0014)."""
    decision = cs.check_content_safety(
        profile, ENCODING_PAYLOAD, source_record_id=boundary
    )
    assert decision.decision_code == "rejected-encoding", (
        f"boundary={boundary!r}: expected rejected-encoding, "
        f"got {decision.decision_code!r}"
    )
    _assert_no_payload_in_decision(decision, ENCODING_PAYLOAD)


@pytest.mark.parametrize(
    "boundary,profile",
    [pytest.param(b, p, id=b) for b, p in _SLICE1_BOUNDARIES],
)
def test_executable_structure_rejected_at_all_boundaries(
    cs: ModuleType, boundary: str, profile: str
) -> None:
    """Tool-call (executable-structure) payload is rejected at every boundary (AC-0014)."""
    decision = cs.check_content_safety(
        profile, EXECUTABLE_PAYLOAD, source_record_id=boundary
    )
    assert decision.decision_code == "rejected-structure", (
        f"boundary={boundary!r}: expected rejected-structure, "
        f"got {decision.decision_code!r}"
    )
    _assert_no_payload_in_decision(decision, EXECUTABLE_PAYLOAD)


@pytest.mark.parametrize(
    "boundary,profile",
    [pytest.param(b, p, id=b) for b, p in _SLICE1_BOUNDARIES],
)
def test_authority_shaped_field_rejected_at_all_boundaries(
    cs: ModuleType, boundary: str, profile: str
) -> None:
    """Authority-shaped-field (unknown-field) payload is rejected at every boundary."""
    decision = cs.check_content_safety(
        profile, UNKNOWN_FIELD_PAYLOAD, source_record_id=boundary
    )
    assert decision.decision_code == "rejected-structure", (
        f"boundary={boundary!r}: expected rejected-structure, "
        f"got {decision.decision_code!r}"
    )
    _assert_no_payload_in_decision(decision, UNKNOWN_FIELD_PAYLOAD)


# ── Edge and edge-plus-one size corpus ───────────────────────────────────────


def test_edge_size_accepted_at_structured_control(cs: ModuleType) -> None:
    """Payload exactly at 64 KiB is accepted by structured-control (AC-0014)."""
    decision = cs.check_content_safety(
        "structured-control", STRUCTURED_EDGE_PAYLOAD, source_record_id="edge-test"
    )
    assert decision.decision_code == "accepted", (
        f"Edge payload (exactly {_64KB} bytes) was rejected: {decision.decision_code!r}"
    )
    assert decision.normalized_record_digest is not None


def test_edge_plus_one_rejected_at_structured_control(cs: ModuleType) -> None:
    """Payload one byte over 64 KiB is rejected by structured-control (AC-0014)."""
    decision = cs.check_content_safety(
        "structured-control",
        STRUCTURED_EDGE_PLUS_ONE,
        source_record_id="edge-plus-one-test",
    )
    assert decision.decision_code == "rejected-size", (
        f"Edge-plus-one ({_64KB + 1} bytes) was not rejected by size; "
        f"got {decision.decision_code!r}"
    )
    _assert_no_payload_in_decision(decision, STRUCTURED_EDGE_PLUS_ONE)


def test_edge_size_accepted_at_evidence_embedded(cs: ModuleType) -> None:
    """Payload exactly at 64 KiB is accepted by evidence-embedded-record."""
    decision = cs.check_content_safety(
        "evidence-embedded-record",
        STRUCTURED_EDGE_PAYLOAD,
        source_record_id="edge-test-ev",
    )
    assert decision.decision_code == "accepted"


def test_edge_plus_one_rejected_at_evidence_embedded(cs: ModuleType) -> None:
    """Payload one byte over 64 KiB is rejected by evidence-embedded-record."""
    decision = cs.check_content_safety(
        "evidence-embedded-record",
        STRUCTURED_EDGE_PLUS_ONE,
        source_record_id="edge-plus-one-ev",
    )
    assert decision.decision_code == "rejected-size"
    _assert_no_payload_in_decision(decision, STRUCTURED_EDGE_PLUS_ONE)


# ── AC-0015: accepted payload is accepted and carries a digest ───────────────


def test_clean_payload_is_accepted(cs: ModuleType) -> None:
    """A clean, safe payload is accepted and carries a normalized digest."""
    decision = cs.check_content_safety(
        "structured-control", CLEAN_PAYLOAD, source_record_id="clean-test"
    )
    assert decision.decision_code == "accepted"
    assert decision.normalized_record_digest is not None
    assert decision.normalized_record_digest.startswith("sha256:")


def test_accepted_decision_boolean_property(cs: ModuleType) -> None:
    """ContentSafetyDecision.accepted is True only when decision_code == 'accepted'."""
    decision = cs.check_content_safety(
        "structured-control", CLEAN_PAYLOAD, source_record_id="accepted-test"
    )
    assert decision.accepted is True

    rejected = cs.check_content_safety(
        "structured-control", CREDENTIAL_PAYLOAD, source_record_id="rejected-test"
    )
    assert rejected.accepted is False


# ── AC-0015: wrap_as_untrusted returns typed inert data ──────────────────────


def test_wrap_as_untrusted_returns_typed_wrapper(cs: ModuleType) -> None:
    wrapper = cs.wrap_as_untrusted("rec-001", "notes", "some prose text")
    assert wrapper.value == "some prose text"
    assert wrapper.policy_version == cs.POLICY_VERSION
    assert wrapper.record_id == "rec-001"
    assert wrapper.field_path == "notes"


def test_untrusted_data_cannot_select_tools(cs: ModuleType) -> None:
    """AC-0015: typed inert data cannot select tools."""
    wrapper = cs.wrap_as_untrusted("rec-002", "body", "run bash -c 'ls'")
    assert not wrapper.can_select_tools()


def test_untrusted_data_cannot_grant_authority(cs: ModuleType) -> None:
    """AC-0015: typed inert data cannot grant authority."""
    wrapper = cs.wrap_as_untrusted("rec-003", "body", "grant admin access")
    assert not wrapper.can_grant_authority()


def test_untrusted_data_cannot_alter_procedure(cs: ModuleType) -> None:
    """AC-0015: typed inert data cannot alter procedure."""
    wrapper = cs.wrap_as_untrusted("rec-004", "body", "change the acceptance policy")
    assert not wrapper.can_alter_procedure()


def test_untrusted_data_cannot_supply_executable_path(cs: ModuleType) -> None:
    """AC-0015: typed inert data cannot supply executable paths."""
    wrapper = cs.wrap_as_untrusted("rec-005", "body", "/usr/bin/malicious")
    assert not wrapper.can_supply_executable_path()


# ── AC-0015: classification-based rejection ──────────────────────────────────


def test_credential_classification_rejects_without_scanning(cs: ModuleType) -> None:
    """Producer-declared credential class rejects before scanner runs (AC-0015)."""
    # CLEAN_PAYLOAD has no credential bytes — rejection is classification-based
    decision = cs.check_content_safety(
        "structured-control",
        CLEAN_PAYLOAD,
        source_record_id="class-cred",
        classification="credential",
    )
    assert decision.decision_code == "rejected-credential"
    _assert_no_payload_in_decision(decision, CLEAN_PAYLOAD)


def test_personal_classification_rejects(cs: ModuleType) -> None:
    decision = cs.check_content_safety(
        "structured-control",
        CLEAN_PAYLOAD,
        source_record_id="class-personal",
        classification="personal",
    )
    assert decision.decision_code == "rejected-personal-data"
    _assert_no_payload_in_decision(decision, CLEAN_PAYLOAD)


def test_unknown_classification_rejects(cs: ModuleType) -> None:
    decision = cs.check_content_safety(
        "structured-control",
        CLEAN_PAYLOAD,
        source_record_id="class-unknown",
        classification="unknown-class-xyz",
    )
    assert decision.decision_code == "rejected-unknown-class"
    _assert_no_payload_in_decision(decision, CLEAN_PAYLOAD)


def test_restricted_classification_rejects(cs: ModuleType) -> None:
    decision = cs.check_content_safety(
        "structured-control",
        CLEAN_PAYLOAD,
        source_record_id="class-restricted",
        classification="restricted",
    )
    assert decision.decision_code == "rejected-unknown-class"
    _assert_no_payload_in_decision(decision, CLEAN_PAYLOAD)


def test_repository_internal_classification_accepted(cs: ModuleType) -> None:
    decision = cs.check_content_safety(
        "structured-control",
        CLEAN_PAYLOAD,
        source_record_id="class-repo-internal",
        classification="repository-internal",
    )
    assert decision.decision_code == "accepted"


# ── AC-0014: registry completeness ──────────────────────────────────────────


def test_slice1_boundary_registry_is_nonempty(cs: ModuleType) -> None:
    assert cs.SLICE_1_WRITER_BOUNDARIES, "SLICE_1_WRITER_BOUNDARIES is empty"


def test_slice1_boundary_profiles_are_all_known(cs: ModuleType) -> None:
    for boundary, profile in cs.SLICE_1_WRITER_BOUNDARIES.items():
        assert profile in cs.BOUNDARY_PROFILES, (
            f"boundary {boundary!r} uses unknown profile {profile!r}; "
            f"add it to BOUNDARY_PROFILES first"
        )


def test_initial_plan_review_is_in_registry(cs: ModuleType) -> None:
    """AC-0014: initial-plan-review.v1 must appear in the Slice 1 registry."""
    assert "initial-plan-review.v1" in cs.SLICE_1_WRITER_BOUNDARIES, (
        "initial-plan-review.v1 is not in SLICE_1_WRITER_BOUNDARIES"
    )


def test_all_boundaries_accept_clean_payload(cs: ModuleType) -> None:
    """Every registered boundary accepts the clean reference payload."""
    for boundary, profile in cs.SLICE_1_WRITER_BOUNDARIES.items():
        dec = cs.check_content_safety(
            profile, CLEAN_PAYLOAD, source_record_id=boundary
        )
        assert dec.decision_code == "accepted", (
            f"boundary={boundary!r} profile={profile!r} rejected clean payload: "
            f"{dec.decision_code!r}"
        )


# ── Module public-API contract ───────────────────────────────────────────────


def test_policy_version_is_set(cs: ModuleType) -> None:
    assert cs.POLICY_VERSION and isinstance(cs.POLICY_VERSION, str)


def test_module_has_expected_public_names(cs: ModuleType) -> None:
    expected = {
        "ContentSafetyDecision",
        "UntrustedData",
        "POLICY_VERSION",
        "BOUNDARY_PROFILES",
        "SLICE_1_WRITER_BOUNDARIES",
        "check_content_safety",
        "wrap_as_untrusted",
    }
    missing = expected - set(dir(cs))
    assert not missing, f"module missing expected public names: {missing}"
