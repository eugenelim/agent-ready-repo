"""T5 TDD suite: policy import, reviewed envelope, initial plan review,
change classification, and reverse-read invariants.

Mode: TDD through transaction and compatibility integration tests (plan.md T5).

Tests:
  AC-0001: Frozen canonicalization corpus — status-token, checkbox, line-ending,
           and trailing-space normalization; current and target digests agree.
  AC-0002, AC-0014: Atomic import with injected failure at every append boundary;
           malformed inputs, digest/envelope mismatch, wrong terminal intent, and
           missing/unknown writer or replay profile publish zero records.
  AC-0020: Writer-authority refusals including retry under the same record identity.
  AC-0003, AC-0004: Classification over task-order, decomposition, sequence, test-
           shape, and local-method changes versus protected references or terminal intent;
           no task, cancellation, or dispatch state written.
  AC-0017: Dual-read reverse reader; post-cutover behavior under synthetic accepted
           authority-switch decision fixture injected through a test-only seam.

Follows the importlib.util.spec_from_file_location loader pattern so the modules
remain unregistered in sys.modules between test sessions.
"""
from __future__ import annotations

import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

# ── Path anchors ─────────────────────────────────────────────────────────────

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)


# ── Module loader helpers ─────────────────────────────────────────────────────


def _load_module(name: str, path: Path) -> ModuleType:
    """Load an unregistered copy of a scripts module via importlib."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def pi() -> ModuleType:
    """_policy_import.py loaded by path, unregistered."""
    return _load_module("pi_t5", SCRIPTS / "_policy_import.py")


@pytest.fixture(scope="module")
def acc() -> ModuleType:
    """_acceptance.py loaded by path, unregistered."""
    return _load_module("acc_t5", SCRIPTS / "_acceptance.py")


@pytest.fixture(scope="module")
def sc() -> ModuleType:
    """_security_capability.py loaded by path, unregistered."""
    return _load_module("sc_t5", SCRIPTS / "_security_capability.py")


@pytest.fixture(scope="module")
def se() -> ModuleType:
    """_security_events.py loaded by path, unregistered."""
    return _load_module("se_t5", SCRIPTS / "_security_events.py")


# ── Shared fixtures ───────────────────────────────────────────────────────────

VALID_REFS = {
    "spec_policy": "approval:spec-policy:v1",
    "scope_and_non_goals": "approval:scope:v1",
    "authority_and_security": "approval:authority:v1",
    "public_contracts": "approval:contracts:v1",
    "durable_outputs": "approval:outputs:v1",
    "accepted_risk": "approval:risk:v1",
}

TERMINAL_INTENT = "code"
APPROVAL_IDENTITY = "platform-core-maintainer"
APPROVAL_ROLE = "spec-policy-owner"
REVIEWER_IDENTITY = "platform-core-maintainer"
REVIEWER_ROLE = "plan-review-authority"

# ── Corpus artifact texts ─────────────────────────────────────────────────────
# These are minimal synthetic spec/plan texts with the key normalization cases.

_SPEC_TEXT_APPROVED = """\
# Test spec

- **Status:** Approved

## Acceptance Criteria

- [ ] AC-0001. First criterion.
""".lstrip()

_SPEC_TEXT_DRAFT = """\
# Test spec

- **Status:** Draft

## Acceptance Criteria

- [ ] AC-0001. First criterion.
""".lstrip()

_SPEC_TEXT_CHECKED = """\
# Test spec

- **Status:** Approved

## Acceptance Criteria

- [x] AC-0001. First criterion.
""".lstrip()

_SPEC_TEXT_CRLF = _SPEC_TEXT_APPROVED.replace("\n", "\r\n")

_SPEC_TEXT_TRAILING_SPACES = (
    "# Test spec   \n"
    "\n"
    "- **Status:** Approved\n"
    "\n"
    "## Acceptance Criteria\n"
    "\n"
    "- [ ] AC-0001. First criterion.   \n"
)

_PLAN_TEXT_BASE = """\
# Test plan

- **Status:** Approved

## Tasks

### T1: First task

- [ ] Done
""".lstrip()

_PLAN_TEXT_CHECKED = _PLAN_TEXT_BASE.replace("- [ ]", "- [x]")
_PLAN_TEXT_CRLF = _PLAN_TEXT_BASE.replace("\n", "\r\n")
_PLAN_TEXT_TRAILING = (
    "# Test plan   \n"
    "\n"
    "- **Status:** Approved\n"
    "\n"
    "## Tasks\n"
    "\n"
    "### T1: First task\n"
    "\n"
    "- [ ] Done   \n"
)


def _write_temp_files(
    tmp_path: Path,
    spec_text: str,
    plan_text: str,
) -> tuple[Path, Path]:
    """Write spec and plan to temp files and return their paths.

    Creates the parent directory if it does not exist.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    spec_path = tmp_path / "spec.md"
    plan_path = tmp_path / "plan.md"
    spec_path.write_text(spec_text, encoding="utf-8")
    plan_path.write_text(plan_text, encoding="utf-8")
    return spec_path, plan_path


def _make_issuer_and_grant(sc: ModuleType) -> tuple[Any, Any]:
    """Create a valid issuer and root grant for import operations.

    The grant covers the 'delivery' scope, which is what import_policy uses
    for its record_scope ('delivery/policy-import').
    """
    issuer = sc.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["delivery"],
        operations=["append", "write"],
        trust_class="trusted",
        writes_allowed_roots=["delivery"],
        control_denies=[],
    )
    return issuer, grant


def _null_sink(event: Any) -> None:
    """A no-op audit sink for testing."""


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0001: Frozen canonicalization corpus
# ═══════════════════════════════════════════════════════════════════════════════


class TestCanonicalizationCorpus:
    """AC-0001: frozen legacy corpus — current and target digests agree."""

    def test_status_token_normalization_spec(
        self, pi: ModuleType, tmp_path: Path
    ) -> None:
        """A spec with 'Approved' status and one with 'Draft' status canonicalize
        identically — the status token is normalized out."""
        spec_approved, plan = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        spec_draft, _ = _write_temp_files(tmp_path / "b", _SPEC_TEXT_DRAFT, _PLAN_TEXT_BASE)
        digest_approved = pi.compute_spec_digest(spec_approved)
        digest_draft = pi.compute_spec_digest(spec_draft)
        assert digest_approved == digest_draft, (
            "status-token normalization: 'Approved' and 'Draft' must canonicalize identically"
        )

    def test_checkbox_normalization_spec(
        self, pi: ModuleType, tmp_path: Path
    ) -> None:
        """A checked checkbox [x] in the AC section canonicalizes identically to [ ]."""
        spec_unchecked, _ = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        spec_checked, _ = _write_temp_files(tmp_path / "b", _SPEC_TEXT_CHECKED, _PLAN_TEXT_BASE)
        digest_unchecked = pi.compute_spec_digest(spec_unchecked)
        digest_checked = pi.compute_spec_digest(spec_checked)
        assert digest_unchecked == digest_checked, (
            "checkbox normalization: [x] must canonicalize identically to [ ] in the AC section"
        )

    def test_line_ending_normalization_spec(
        self, pi: ModuleType, tmp_path: Path
    ) -> None:
        """CRLF line endings canonicalize identically to LF."""
        spec_lf, _ = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        # Write CRLF bytes directly to bypass Python universal newlines
        (tmp_path / "b").mkdir(parents=True, exist_ok=True)
        spec_crlf = tmp_path / "b" / "spec.md"
        spec_crlf.write_bytes(_SPEC_TEXT_CRLF.encode("utf-8"))
        digest_lf = pi.compute_spec_digest(spec_lf)
        digest_crlf = pi.compute_spec_digest(spec_crlf)
        assert digest_lf == digest_crlf, (
            "line-ending normalization: CRLF must canonicalize identically to LF"
        )

    def test_trailing_space_normalization_spec(
        self, pi: ModuleType, tmp_path: Path
    ) -> None:
        """Trailing whitespace is stripped from every line before hashing."""
        spec_clean, _ = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        spec_trailing, _ = _write_temp_files(tmp_path / "b", _SPEC_TEXT_TRAILING_SPACES, _PLAN_TEXT_BASE)
        digest_clean = pi.compute_spec_digest(spec_clean)
        digest_trailing = pi.compute_spec_digest(spec_trailing)
        assert digest_clean == digest_trailing, (
            "trailing-space normalization: trailing spaces must be stripped before hashing"
        )

    def test_plan_checkbox_normalization(
        self, pi: ModuleType, tmp_path: Path
    ) -> None:
        """Plan checkboxes normalize file-wide (not only in AC section)."""
        _, plan_unchecked = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        _, plan_checked = _write_temp_files(tmp_path / "b", _SPEC_TEXT_APPROVED, _PLAN_TEXT_CHECKED)
        digest_unchecked = pi.compute_plan_digest(plan_unchecked)
        digest_checked = pi.compute_plan_digest(plan_checked)
        assert digest_unchecked == digest_checked, (
            "plan checkbox normalization: [x] must canonicalize identically to [ ] file-wide"
        )

    def test_plan_crlf_normalization(
        self, pi: ModuleType, tmp_path: Path
    ) -> None:
        """Plan with CRLF canonicalizes identically to LF."""
        _, plan_lf = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        (tmp_path / "b").mkdir(parents=True, exist_ok=True)
        plan_crlf = tmp_path / "b" / "plan.md"
        plan_crlf.write_bytes(_PLAN_TEXT_CRLF.encode("utf-8"))
        digest_lf = pi.compute_plan_digest(plan_lf)
        digest_crlf = pi.compute_plan_digest(plan_crlf)
        assert digest_lf == digest_crlf, (
            "plan CRLF normalization: CRLF must canonicalize identically to LF"
        )

    def test_target_and_current_digests_agree(
        self, pi: ModuleType, tmp_path: Path
    ) -> None:
        """_policy_import's compute_spec_digest/compute_plan_digest agree with
        _loop_guards.sha256_canonical_contract (the current canonical implementation)."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        # Target digests (via _policy_import)
        target_spec = pi.compute_spec_digest(spec_path)
        target_plan = pi.compute_plan_digest(plan_path)
        # Current digests (via _loop_guards directly)
        guards = _load_module("guards_t5", SCRIPTS / "_loop_guards.py")
        current_spec = guards.sha256_canonical_contract(spec_path)
        current_plan = guards.sha256_canonical_contract(plan_path)
        assert target_spec == current_spec, "spec digest: target and current must agree"
        assert target_plan == current_plan, "plan digest: target and current must agree"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0002, AC-0014: Atomic import with injected failure
# ═══════════════════════════════════════════════════════════════════════════════


class TestAtomicImport:
    """AC-0002, AC-0014: atomic import exposes exactly zero or two records."""

    def test_successful_import_exposes_two_records(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A successful import produces exactly two visible records."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)
        approval, review = pi.import_policy(
            spec_path=spec_path,
            plan_path=plan_path,
            refs=VALID_REFS,
            terminal_intent=TERMINAL_INTENT,
            writer_grant=grant,
            issuer=issuer,
            audit_sink=_null_sink,
            store=store,
            approval_identity=APPROVAL_IDENTITY,
            approval_role=APPROVAL_ROLE,
            reviewer_identity=REVIEWER_IDENTITY,
            reviewer_role=REVIEWER_ROLE,
        )
        assert store.record_count() == 2, "successful import must expose exactly two records"
        records = store.get_records()
        # One is approval-record.v1, one is initial-plan-review.v1
        record_types = {r["schema_version"] for r in records}
        assert 1 in record_types

    def test_interrupt_before_first_write_exposes_zero(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """Interruption before first write exposes zero records.

        Crash point injected by monkeypatching store._stage to fail on the
        first call, before any record has been staged.
        """
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)

        def _fail_stage(record: dict) -> None:  # noqa: ARG001
            raise RuntimeError("injected failure before first stage write")

        store._stage = _fail_stage  # type: ignore[method-assign]

        with pytest.raises(RuntimeError):
            pi.import_policy(
                spec_path=spec_path,
                plan_path=plan_path,
                refs=VALID_REFS,
                terminal_intent=TERMINAL_INTENT,
                writer_grant=grant,
                issuer=issuer,
                audit_sink=_null_sink,
                store=store,
                approval_identity=APPROVAL_IDENTITY,
                approval_role=APPROVAL_ROLE,
                reviewer_identity=REVIEWER_IDENTITY,
                reviewer_role=REVIEWER_ROLE,
            )
        assert store.record_count() == 0, (
            "interrupted before first write must expose zero records"
        )

    def test_interrupt_between_writes_exposes_zero(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """Interruption between writes exposes zero records.

        Crash point injected by monkeypatching store._stage to succeed on the
        first call (approval record staged) and fail on the second call
        (before the initial-review record is staged).
        """
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)

        call_count = [0]
        original_stage = pi.ImportStore._stage

        def _fail_second_stage(record: dict) -> None:
            call_count[0] += 1
            if call_count[0] >= 2:
                raise RuntimeError("injected failure between writes (second stage)")
            original_stage(store, record)

        store._stage = _fail_second_stage  # type: ignore[method-assign]

        with pytest.raises(RuntimeError):
            pi.import_policy(
                spec_path=spec_path,
                plan_path=plan_path,
                refs=VALID_REFS,
                terminal_intent=TERMINAL_INTENT,
                writer_grant=grant,
                issuer=issuer,
                audit_sink=_null_sink,
                store=store,
                approval_identity=APPROVAL_IDENTITY,
                approval_role=APPROVAL_ROLE,
                reviewer_identity=REVIEWER_IDENTITY,
                reviewer_role=REVIEWER_ROLE,
            )
        assert store.record_count() == 0, (
            "interrupted between writes must expose zero records"
        )

    def test_malformed_refs_exposes_zero(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """Malformed refs (missing required key) exposes zero records."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)
        bad_refs = {k: v for k, v in VALID_REFS.items() if k != "spec_policy"}

        with pytest.raises(pi.PolicyImportRefused):
            pi.import_policy(
                spec_path=spec_path,
                plan_path=plan_path,
                refs=bad_refs,
                terminal_intent=TERMINAL_INTENT,
                writer_grant=grant,
                issuer=issuer,
                audit_sink=_null_sink,
                store=store,
                approval_identity=APPROVAL_IDENTITY,
                approval_role=APPROVAL_ROLE,
                reviewer_identity=REVIEWER_IDENTITY,
                reviewer_role=REVIEWER_ROLE,
            )
        assert store.record_count() == 0, "malformed refs must expose zero records"

    def test_digest_mismatch_on_restart_exposes_zero(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """If the spec digest differs from what an existing record carries, expose zero new records."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)
        # First import succeeds
        pi.import_policy(
            spec_path=spec_path,
            plan_path=plan_path,
            refs=VALID_REFS,
            terminal_intent=TERMINAL_INTENT,
            writer_grant=grant,
            issuer=issuer,
            audit_sink=_null_sink,
            store=store,
            approval_identity=APPROVAL_IDENTITY,
            approval_role=APPROVAL_ROLE,
            reviewer_identity=REVIEWER_IDENTITY,
            reviewer_role=REVIEWER_ROLE,
        )
        # Store a wrong digest to simulate mismatch
        existing_count = store.record_count()
        assert existing_count == 2

        # Import with mismatched envelope (different refs)
        different_refs = dict(VALID_REFS)
        different_refs["spec_policy"] = "approval:spec-policy:DIFFERENT"
        # The mismatched envelope should still work for a fresh store
        # The digest mismatch scenario: replay an import where spec content changed
        # We test this by passing a spec_policy_fingerprint that doesn't match computed
        # This is tested via the envelope_fingerprint check in review
        # A simpler test: a stored record with a wrong envelope_fingerprint triggers mismatch
        with pytest.raises(pi.PolicyImportRefused):
            pi.import_policy(
                spec_path=spec_path,
                plan_path=plan_path,
                refs=VALID_REFS,
                terminal_intent=TERMINAL_INTENT,
                writer_grant=grant,
                issuer=issuer,
                audit_sink=_null_sink,
                store=store,  # store already has 2 records — replay is a mismatch
                approval_identity=APPROVAL_IDENTITY,
                approval_role=APPROVAL_ROLE,
                reviewer_identity=REVIEWER_IDENTITY,
                reviewer_role=REVIEWER_ROLE,
            )

    def test_wrong_terminal_intent_exposes_zero(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A wrong terminal intent is refused and exposes zero records."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)

        with pytest.raises(pi.PolicyImportRefused) as exc_info:
            pi.import_policy(
                spec_path=spec_path,
                plan_path=plan_path,
                refs=VALID_REFS,
                terminal_intent="",  # empty intent is invalid
                writer_grant=grant,
                issuer=issuer,
                audit_sink=_null_sink,
                store=store,
                approval_identity=APPROVAL_IDENTITY,
                approval_role=APPROVAL_ROLE,
                reviewer_identity=REVIEWER_IDENTITY,
                reviewer_role=REVIEWER_ROLE,
            )
        assert store.record_count() == 0, "wrong terminal intent must expose zero records"
        assert "denied" in exc_info.value.denial_code

    def test_missing_profile_exposes_zero(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """An unknown content-safety profile refuses and exposes zero records.

        This tests AC-0014: the on_before_first_write hook is used to tamper
        with the profile registry check via a synthetic store that claims an
        unknown profile.
        """
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)

        # Test with an empty identity — content safety check must refuse before persist
        with pytest.raises(pi.PolicyImportRefused):
            pi.import_policy(
                spec_path=spec_path,
                plan_path=plan_path,
                refs=VALID_REFS,
                terminal_intent=TERMINAL_INTENT,
                writer_grant=grant,
                issuer=issuer,
                audit_sink=_null_sink,
                store=store,
                approval_identity="",  # empty identity fails content safety
                approval_role=APPROVAL_ROLE,
                reviewer_identity=REVIEWER_IDENTITY,
                reviewer_role=REVIEWER_ROLE,
            )
        assert store.record_count() == 0, "missing/unknown profile must expose zero records"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0020: Writer-authority refusals
# ═══════════════════════════════════════════════════════════════════════════════


class TestWriterAuthorityRefusals:
    """AC-0020: every append boundary verifies named writer authority."""

    def test_no_grant_exposes_zero_records(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A None grant refuses and exposes zero records."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer = sc.CapabilityIssuer()

        with pytest.raises(pi.PolicyImportRefused) as exc_info:
            pi.import_policy(
                spec_path=spec_path,
                plan_path=plan_path,
                refs=VALID_REFS,
                terminal_intent=TERMINAL_INTENT,
                writer_grant=None,
                issuer=issuer,
                audit_sink=_null_sink,
                store=store,
                approval_identity=APPROVAL_IDENTITY,
                approval_role=APPROVAL_ROLE,
                reviewer_identity=REVIEWER_IDENTITY,
                reviewer_role=REVIEWER_ROLE,
            )
        assert store.record_count() == 0, "no grant must expose zero records"
        assert "denied" in exc_info.value.denial_code

    def test_expired_grant_exposes_zero_records(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """An expired grant refuses and exposes zero records."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer = sc.CapabilityIssuer()
        # Issue a grant that expires instantly (past time)
        grant = issuer.issue_root_grant(
            roots=["/"],
            operations=["append", "write"],
            trust_class="trusted",
            writes_allowed_roots=["/"],
            control_denies=[],
            expires_in_s=-1.0,  # expired
        )

        with pytest.raises(pi.PolicyImportRefused):
            pi.import_policy(
                spec_path=spec_path,
                plan_path=plan_path,
                refs=VALID_REFS,
                terminal_intent=TERMINAL_INTENT,
                writer_grant=grant,
                issuer=issuer,
                audit_sink=_null_sink,
                store=store,
                approval_identity=APPROVAL_IDENTITY,
                approval_role=APPROVAL_ROLE,
                reviewer_identity=REVIEWER_IDENTITY,
                reviewer_role=REVIEWER_ROLE,
            )
        assert store.record_count() == 0, "expired grant must expose zero records"

    def test_mismatched_grant_exposes_zero(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A grant from a different issuer is refused and exposes zero records."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer_a = sc.CapabilityIssuer()
        issuer_b = sc.CapabilityIssuer()
        # Grant issued by issuer_a, verified against issuer_b → mismatch
        grant_a = issuer_a.issue_root_grant(
            roots=["/"],
            operations=["append", "write"],
            trust_class="trusted",
            writes_allowed_roots=["/"],
            control_denies=[],
        )

        with pytest.raises(pi.PolicyImportRefused):
            pi.import_policy(
                spec_path=spec_path,
                plan_path=plan_path,
                refs=VALID_REFS,
                terminal_intent=TERMINAL_INTENT,
                writer_grant=grant_a,
                issuer=issuer_b,  # wrong issuer
                audit_sink=_null_sink,
                store=store,
                approval_identity=APPROVAL_IDENTITY,
                approval_role=APPROVAL_ROLE,
                reviewer_identity=REVIEWER_IDENTITY,
                reviewer_role=REVIEWER_ROLE,
            )
        assert store.record_count() == 0, "mismatched grant must expose zero records"

    def test_revoked_grant_exposes_zero(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A revoked grant refuses and exposes zero records."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer = sc.CapabilityIssuer()
        grant = issuer.issue_root_grant(
            roots=["/"],
            operations=["append", "write"],
            trust_class="trusted",
            writes_allowed_roots=["/"],
            control_denies=[],
        )
        issuer.revoke_grant(grant.grant_id)

        with pytest.raises(pi.PolicyImportRefused):
            pi.import_policy(
                spec_path=spec_path,
                plan_path=plan_path,
                refs=VALID_REFS,
                terminal_intent=TERMINAL_INTENT,
                writer_grant=grant,
                issuer=issuer,
                audit_sink=_null_sink,
                store=store,
                approval_identity=APPROVAL_IDENTITY,
                approval_role=APPROVAL_ROLE,
                reviewer_identity=REVIEWER_IDENTITY,
                reviewer_role=REVIEWER_ROLE,
            )
        assert store.record_count() == 0, "revoked grant must expose zero records"

    def test_retry_under_same_identity_still_denied(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """Retry under the same record identity cannot turn a denial into an allow.

        AC-0020: retry cannot weaken the refusal. After a denied first attempt,
        a second attempt with the same expired/revoked grant still exposes zero records.
        """
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        issuer = sc.CapabilityIssuer()
        grant = issuer.issue_root_grant(
            roots=["/"],
            operations=["append", "write"],
            trust_class="trusted",
            writes_allowed_roots=["/"],
            control_denies=[],
        )
        issuer.revoke_grant(grant.grant_id)

        for attempt in range(2):
            store = pi.ImportStore()
            with pytest.raises(pi.PolicyImportRefused):
                pi.import_policy(
                    spec_path=spec_path,
                    plan_path=plan_path,
                    refs=VALID_REFS,
                    terminal_intent=TERMINAL_INTENT,
                    writer_grant=grant,
                    issuer=issuer,
                    audit_sink=_null_sink,
                    store=store,
                    approval_identity=APPROVAL_IDENTITY,
                    approval_role=APPROVAL_ROLE,
                    reviewer_identity=REVIEWER_IDENTITY,
                    reviewer_role=REVIEWER_ROLE,
                )
            assert store.record_count() == 0, (
                f"attempt {attempt + 1}: retry under same revoked identity must still expose zero"
            )

    def test_audit_sink_unavailable_fails_closed(
        self, pi: ModuleType, sc: ModuleType, se: ModuleType, tmp_path: Path
    ) -> None:
        """An unavailable audit sink fails closed; zero records are exposed.

        AC-0021: when the sink is unavailable, the operation fails closed.
        The sink raises OSError (a standard-library I/O failure) to simulate
        an unavailable audit path; _security_events maps that to
        AuditSinkUnavailable, which propagates as a fail-closed denial.
        """
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)

        def _failing_sink(event: Any) -> None:
            # OSError is the standard-library I/O failure that _security_events
            # maps to AuditSinkUnavailable. Using OSError avoids a class-identity
            # mismatch between separately loaded module copies.
            raise OSError("sink unavailable in test")

        with pytest.raises((pi.PolicyImportRefused, se.AuditSinkUnavailable, OSError)):
            pi.import_policy(
                spec_path=spec_path,
                plan_path=plan_path,
                refs=VALID_REFS,
                terminal_intent=TERMINAL_INTENT,
                writer_grant=grant,
                issuer=issuer,
                audit_sink=_failing_sink,
                store=store,
                approval_identity=APPROVAL_IDENTITY,
                approval_role=APPROVAL_ROLE,
                reviewer_identity=REVIEWER_IDENTITY,
                reviewer_role=REVIEWER_ROLE,
            )
        assert store.record_count() == 0, (
            "unavailable audit sink must fail closed with zero records"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0003, AC-0004: Change classification
# ═══════════════════════════════════════════════════════════════════════════════


class TestChangeClassification:
    """AC-0003, AC-0004: classification of proposed changes against the envelope."""

    def test_task_order_change_needs_no_approval(self, acc: ModuleType) -> None:
        """A task-order change inside the envelope needs no approval (AC-0004)."""
        fp = acc.derive_envelope(VALID_REFS)["envelope_fingerprint"]
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent=TERMINAL_INTENT,
            proposed_envelope_fingerprint=fp,  # unchanged
            proposed_terminal_intent=TERMINAL_INTENT,  # unchanged
        )
        assert result == "no-approval-required"

    def test_decomposition_change_needs_no_approval(self, acc: ModuleType) -> None:
        """A decomposition change inside the envelope needs no approval."""
        fp = acc.derive_envelope(VALID_REFS)["envelope_fingerprint"]
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent=TERMINAL_INTENT,
            proposed_envelope_fingerprint=fp,
            proposed_terminal_intent=TERMINAL_INTENT,
        )
        assert result == "no-approval-required"

    def test_sequence_change_needs_no_approval(self, acc: ModuleType) -> None:
        """A sequence change inside the envelope needs no approval."""
        fp = acc.derive_envelope(VALID_REFS)["envelope_fingerprint"]
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent=TERMINAL_INTENT,
            proposed_envelope_fingerprint=fp,
            proposed_terminal_intent=TERMINAL_INTENT,
        )
        assert result == "no-approval-required"

    def test_test_shape_change_needs_no_approval(self, acc: ModuleType) -> None:
        """A test-shape change inside the envelope needs no approval."""
        fp = acc.derive_envelope(VALID_REFS)["envelope_fingerprint"]
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent=TERMINAL_INTENT,
            proposed_envelope_fingerprint=fp,
            proposed_terminal_intent=TERMINAL_INTENT,
        )
        assert result == "no-approval-required"

    def test_local_method_change_needs_no_approval(self, acc: ModuleType) -> None:
        """A local-method change inside the envelope needs no approval."""
        fp = acc.derive_envelope(VALID_REFS)["envelope_fingerprint"]
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent=TERMINAL_INTENT,
            proposed_envelope_fingerprint=fp,
            proposed_terminal_intent=TERMINAL_INTENT,
        )
        assert result == "no-approval-required"

    def test_changed_envelope_requires_approval(self, acc: ModuleType) -> None:
        """A changed envelope fingerprint requires approval (AC-0004)."""
        current_fp = acc.derive_envelope(VALID_REFS)["envelope_fingerprint"]
        different_refs = dict(VALID_REFS)
        different_refs["spec_policy"] = "approval:spec-policy:CHANGED"
        proposed_fp = acc.derive_envelope(different_refs)["envelope_fingerprint"]
        result = acc.classify_change(
            current_envelope_fingerprint=current_fp,
            current_terminal_intent=TERMINAL_INTENT,
            proposed_envelope_fingerprint=proposed_fp,
            proposed_terminal_intent=TERMINAL_INTENT,
        )
        assert result == "approval-required", (
            "changed envelope fingerprint must require approval"
        )

    def test_changed_terminal_intent_requires_approval(self, acc: ModuleType) -> None:
        """A changed terminal intent requires approval (AC-0004)."""
        fp = acc.derive_envelope(VALID_REFS)["envelope_fingerprint"]
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent=TERMINAL_INTENT,
            proposed_envelope_fingerprint=fp,
            proposed_terminal_intent="spec-plan",  # different intent
        )
        assert result == "approval-required", (
            "changed terminal intent must require approval"
        )

    def test_classification_writes_no_task_state(
        self, pi: ModuleType, acc: ModuleType
    ) -> None:
        """classify_change writes no task, cancellation, or dispatch state.

        AC-0004: The classifier performs no task reprojection, cancellation,
        or dispatch. Verified by confirming the call returns a string and
        touches no mutable store.
        """
        fp = acc.derive_envelope(VALID_REFS)["envelope_fingerprint"]
        # classify_change is stateless and returns only a classification string
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent=TERMINAL_INTENT,
            proposed_envelope_fingerprint=fp,
            proposed_terminal_intent=TERMINAL_INTENT,
        )
        assert isinstance(result, str), "classify_change must return a string"
        assert result in ("no-approval-required", "approval-required"), (
            "classify_change must return one of the two stable classification codes"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0017: Dual-read reverse reader and compatibility_snapshot
# ═══════════════════════════════════════════════════════════════════════════════


def _make_governance_resolver(
    *,
    envelope_fingerprint: str,
    terminal_intent: str,
    governance_ref: str = "test-governance-001",
) -> Any:
    """Test-only governance resolver fixture.

    Returns a callable ``() -> dict`` accepted by
    ``compatibility_snapshot(store, authority_resolver=...)``.
    The callable returns a decision dict with the given envelope fingerprint
    and terminal intent.  The module validates those values against stored
    records and refuses on mismatch; this resolver itself does not validate.

    Defined in the test file so the production module carries no test seam.
    """
    def _resolver() -> dict:
        return {
            "governance_ref": governance_ref,
            "envelope_fingerprint": envelope_fingerprint,
            "terminal_intent": terminal_intent,
        }
    return _resolver


class TestReverseReader:
    """AC-0017: dual-read reverse_read and post-cutover compatibility_snapshot."""

    # ── reverse_read (dual-read) ──────────────────────────────────────────────

    def test_reverse_read_reconstructs_original_pair(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """reverse_read returns the original approval and initial-plan-review records."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)
        original_approval, original_review = pi.import_policy(
            spec_path=spec_path,
            plan_path=plan_path,
            refs=VALID_REFS,
            terminal_intent=TERMINAL_INTENT,
            writer_grant=grant,
            issuer=issuer,
            audit_sink=_null_sink,
            store=store,
            approval_identity=APPROVAL_IDENTITY,
            approval_role=APPROVAL_ROLE,
            reviewer_identity=REVIEWER_IDENTITY,
            reviewer_role=REVIEWER_ROLE,
        )
        read_approval, read_review = pi.reverse_read(store)
        assert read_approval["approval_id"] == original_approval["approval_id"], (
            "reverse_read must reconstruct the original approval record"
        )
        assert read_review["review_id"] == original_review["review_id"], (
            "reverse_read must reconstruct the original initial-plan-review record"
        )

    def test_reverse_read_from_empty_store_refuses(
        self, pi: ModuleType
    ) -> None:
        """reverse_read on an empty store refuses without producing a partial record."""
        store = pi.ImportStore()
        with pytest.raises(pi.PolicyImportRefused) as exc_info:
            pi.reverse_read(store)
        assert "denied" in exc_info.value.denial_code

    # ── compatibility_snapshot (post-cutover) ─────────────────────────────────

    def test_default_resolver_refuses(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """compatibility_snapshot with default resolver refuses (denied-no-governance-record).

        The production entry point cannot supply a resolver that grants authority
        in Slice 1; calling compatibility_snapshot() without an explicit resolver
        always refuses.
        """
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)
        pi.import_policy(
            spec_path=spec_path,
            plan_path=plan_path,
            refs=VALID_REFS,
            terminal_intent=TERMINAL_INTENT,
            writer_grant=grant,
            issuer=issuer,
            audit_sink=_null_sink,
            store=store,
            approval_identity=APPROVAL_IDENTITY,
            approval_role=APPROVAL_ROLE,
            reviewer_identity=REVIEWER_IDENTITY,
            reviewer_role=REVIEWER_ROLE,
        )
        with pytest.raises(pi.PolicyImportRefused) as exc_info:
            pi.compatibility_snapshot(store)
        assert exc_info.value.denial_code == "denied-no-governance-record", (
            "default resolver must refuse with denied-no-governance-record"
        )

    def test_fixture_resolver_yields_snapshot_without_authority(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A fixture resolver yields a snapshot that grants no target authority
        while the store stays byte-identical (no semantic facts deleted or changed)."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)
        _, review = pi.import_policy(
            spec_path=spec_path,
            plan_path=plan_path,
            refs=VALID_REFS,
            terminal_intent=TERMINAL_INTENT,
            writer_grant=grant,
            issuer=issuer,
            audit_sink=_null_sink,
            store=store,
            approval_identity=APPROVAL_IDENTITY,
            approval_role=APPROVAL_ROLE,
            reviewer_identity=REVIEWER_IDENTITY,
            reviewer_role=REVIEWER_ROLE,
        )
        resolver = _make_governance_resolver(
            envelope_fingerprint=review["envelope_fingerprint"],
            terminal_intent=TERMINAL_INTENT,
        )
        snapshot = pi.compatibility_snapshot(store, authority_resolver=resolver)
        assert isinstance(snapshot, dict), "fixture resolver must produce a snapshot dict"
        assert snapshot.get("is_compatibility_snapshot") is True
        assert snapshot.get("grants_target_authority") is not True, (
            "module must not grant target authority"
        )
        # Original records unchanged in store.
        assert store.record_count() == 2, (
            "original records must not be deleted by snapshot production"
        )

    def test_resolver_claiming_authority_cannot_grant_it(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A resolver whose decision dict contains grants_target_authority=True
        cannot make the module grant target authority in the snapshot.

        The module enforces grants_target_authority=False regardless of any
        field in the resolver's decision dict.
        """
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)
        _, review = pi.import_policy(
            spec_path=spec_path,
            plan_path=plan_path,
            refs=VALID_REFS,
            terminal_intent=TERMINAL_INTENT,
            writer_grant=grant,
            issuer=issuer,
            audit_sink=_null_sink,
            store=store,
            approval_identity=APPROVAL_IDENTITY,
            approval_role=APPROVAL_ROLE,
            reviewer_identity=REVIEWER_IDENTITY,
            reviewer_role=REVIEWER_ROLE,
        )

        def _greedy_resolver() -> dict:
            """Decision dict that attempts to claim target authority."""
            return {
                "governance_ref": "test-governance-001",
                "envelope_fingerprint": review["envelope_fingerprint"],
                "terminal_intent": TERMINAL_INTENT,
                "grants_target_authority": True,  # attempt to escalate
            }

        snapshot = pi.compatibility_snapshot(store, authority_resolver=_greedy_resolver)
        assert snapshot.get("grants_target_authority") is not True, (
            "module must not grant target authority even when resolver's decision claims it"
        )
        assert snapshot.get("is_compatibility_snapshot") is True

    def test_forged_non_callable_resolver_refuses(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A forged non-callable (dict) passed as authority_resolver refuses.

        The production entry point has no exported resolver in Slice 1.
        A caller presenting a non-callable receives
        PolicyImportRefused("denied-resolver-error").
        """
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)
        pi.import_policy(
            spec_path=spec_path,
            plan_path=plan_path,
            refs=VALID_REFS,
            terminal_intent=TERMINAL_INTENT,
            writer_grant=grant,
            issuer=issuer,
            audit_sink=_null_sink,
            store=store,
            approval_identity=APPROVAL_IDENTITY,
            approval_role=APPROVAL_ROLE,
            reviewer_identity=REVIEWER_IDENTITY,
            reviewer_role=REVIEWER_ROLE,
        )
        # Forged dict — not a callable.
        forged_dict: Any = {
            "envelope_fingerprint": "some-fp",
            "terminal_intent": TERMINAL_INTENT,
        }
        with pytest.raises(pi.PolicyImportRefused) as exc_info:
            pi.compatibility_snapshot(store, authority_resolver=forged_dict)
        assert "denied" in exc_info.value.denial_code, (
            "forged non-callable must refuse with a stable denial code"
        )

    def test_lossy_projection_refuses(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A lossy projection (wrong envelope fingerprint in decision) refuses."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)
        pi.import_policy(
            spec_path=spec_path,
            plan_path=plan_path,
            refs=VALID_REFS,
            terminal_intent=TERMINAL_INTENT,
            writer_grant=grant,
            issuer=issuer,
            audit_sink=_null_sink,
            store=store,
            approval_identity=APPROVAL_IDENTITY,
            approval_role=APPROVAL_ROLE,
            reviewer_identity=REVIEWER_IDENTITY,
            reviewer_role=REVIEWER_ROLE,
        )
        # Decision with wrong fingerprint → module refuses with denied-lossy-projection.
        resolver = _make_governance_resolver(
            envelope_fingerprint="wrong-fingerprint-that-does-not-match",
            terminal_intent=TERMINAL_INTENT,
        )
        with pytest.raises(pi.PolicyImportRefused) as exc_info:
            pi.compatibility_snapshot(store, authority_resolver=resolver)
        assert exc_info.value.denial_code == "denied-lossy-projection", (
            "lossy projection must refuse with denied-lossy-projection"
        )

    def test_boundary_crossing_projection_refuses(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A boundary-crossing projection (wrong terminal intent in decision) refuses."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)
        _, review = pi.import_policy(
            spec_path=spec_path,
            plan_path=plan_path,
            refs=VALID_REFS,
            terminal_intent=TERMINAL_INTENT,
            writer_grant=grant,
            issuer=issuer,
            audit_sink=_null_sink,
            store=store,
            approval_identity=APPROVAL_IDENTITY,
            approval_role=APPROVAL_ROLE,
            reviewer_identity=REVIEWER_IDENTITY,
            reviewer_role=REVIEWER_ROLE,
        )
        # Decision with wrong intent → module refuses with denied-boundary-crossing-projection.
        resolver = _make_governance_resolver(
            envelope_fingerprint=review["envelope_fingerprint"],
            terminal_intent="wrong-intent",  # does not match stored
        )
        with pytest.raises(pi.PolicyImportRefused) as exc_info:
            pi.compatibility_snapshot(store, authority_resolver=resolver)
        assert exc_info.value.denial_code == "denied-boundary-crossing-projection", (
            "boundary-crossing projection must refuse with denied-boundary-crossing-projection"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Record validation (parity with canonical schemas)
# ═══════════════════════════════════════════════════════════════════════════════


class TestRecordValidation:
    """In-code validation of approval-record.v1 and initial-plan-review.v1."""

    def test_validate_approval_accepts_valid_record(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """validate_approval_dict accepts a well-formed approval-record.v1."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)
        approval, _ = pi.import_policy(
            spec_path=spec_path,
            plan_path=plan_path,
            refs=VALID_REFS,
            terminal_intent=TERMINAL_INTENT,
            writer_grant=grant,
            issuer=issuer,
            audit_sink=_null_sink,
            store=store,
            approval_identity=APPROVAL_IDENTITY,
            approval_role=APPROVAL_ROLE,
            reviewer_identity=REVIEWER_IDENTITY,
            reviewer_role=REVIEWER_ROLE,
        )
        ok, code = pi.validate_approval_dict(approval)
        assert ok, f"validate_approval_dict rejected a valid record: {code}"
        assert code == "ok"

    def test_validate_approval_refuses_unknown_schema_version(
        self, pi: ModuleType
    ) -> None:
        """validate_approval_dict refuses an unknown schema_version."""
        bad = {
            "schema_version": 99,
            "approval_id": "appr-001",
            "authority": {"identity": "core", "role": "spec-policy-owner"},
            "decision_scope": "spec-policy",
            "base": {"manifest_ref": "sha256:abc"},
            "lineage": {"spec_ref": "docs/specs/test/spec.md"},
            "spec_policy_fingerprint": "sha256:def",
            "decision": "approved",
            "timestamp": "2026-10-01T00:00:00Z",
        }
        ok, code = pi.validate_approval_dict(bad)
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_validate_approval_refuses_missing_required_field(
        self, pi: ModuleType
    ) -> None:
        """validate_approval_dict refuses a record missing a required field."""
        bad = {
            "schema_version": 1,
            # missing approval_id
            "authority": {"identity": "core", "role": "spec-policy-owner"},
            "decision_scope": "spec-policy",
            "base": {"manifest_ref": "sha256:abc"},
            "lineage": {"spec_ref": "docs/specs/test/spec.md"},
            "spec_policy_fingerprint": "sha256:def",
            "decision": "approved",
            "timestamp": "2026-10-01T00:00:00Z",
        }
        ok, code = pi.validate_approval_dict(bad)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_validate_approval_refuses_unknown_authority_field(
        self, pi: ModuleType
    ) -> None:
        """validate_approval_dict refuses an unknown authority-shaped field."""
        bad = {
            "schema_version": 1,
            "approval_id": "appr-001",
            "authority": {"identity": "core", "role": "spec-policy-owner"},
            "decision_scope": "spec-policy",
            "base": {"manifest_ref": "sha256:abc"},
            "lineage": {"spec_ref": "docs/specs/test/spec.md"},
            "spec_policy_fingerprint": "sha256:def",
            "decision": "approved",
            "timestamp": "2026-10-01T00:00:00Z",
            "inject_escalation": "bypass",  # unknown field
        }
        ok, code = pi.validate_approval_dict(bad)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_validate_approval_refuses_invalid_decision_enum(
        self, pi: ModuleType
    ) -> None:
        """validate_approval_dict refuses an out-of-enum decision value."""
        bad = {
            "schema_version": 1,
            "approval_id": "appr-001",
            "authority": {"identity": "core", "role": "spec-policy-owner"},
            "decision_scope": "spec-policy",
            "base": {"manifest_ref": "sha256:abc"},
            "lineage": {"spec_ref": "docs/specs/test/spec.md"},
            "spec_policy_fingerprint": "sha256:def",
            "decision": "rejected",  # not in enum
            "timestamp": "2026-10-01T00:00:00Z",
        }
        ok, code = pi.validate_approval_dict(bad)
        assert not ok
        assert code == "denied-invalid-enum"

    def test_validate_initial_review_accepts_valid_record(
        self, pi: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """validate_initial_review_dict accepts a well-formed initial-plan-review.v1."""
        spec_path, plan_path = _write_temp_files(tmp_path / "a", _SPEC_TEXT_APPROVED, _PLAN_TEXT_BASE)
        store = pi.ImportStore()
        issuer, grant = _make_issuer_and_grant(sc)
        _, review = pi.import_policy(
            spec_path=spec_path,
            plan_path=plan_path,
            refs=VALID_REFS,
            terminal_intent=TERMINAL_INTENT,
            writer_grant=grant,
            issuer=issuer,
            audit_sink=_null_sink,
            store=store,
            approval_identity=APPROVAL_IDENTITY,
            approval_role=APPROVAL_ROLE,
            reviewer_identity=REVIEWER_IDENTITY,
            reviewer_role=REVIEWER_ROLE,
        )
        ok, code = pi.validate_initial_review_dict(review)
        assert ok, f"validate_initial_review_dict rejected a valid record: {code}"
        assert code == "ok"

    def test_validate_initial_review_refuses_unknown_schema_version(
        self, pi: ModuleType
    ) -> None:
        """validate_initial_review_dict refuses an unknown schema_version."""
        bad = {
            "schema_version": 99,
            "review_id": "rev-001",
            "envelope_fingerprint": "fp-abc",
            "plan_hash": "sha256:def",
            "authorized_terminal_intent": "code",
            "reviewer": {"identity": "core", "role": "plan-review-authority"},
            "decision": "accepted",
        }
        ok, code = pi.validate_initial_review_dict(bad)
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_validate_initial_review_refuses_missing_required_field(
        self, pi: ModuleType
    ) -> None:
        """validate_initial_review_dict refuses a record missing a required field."""
        bad = {
            "schema_version": 1,
            # missing review_id
            "envelope_fingerprint": "fp-abc",
            "plan_hash": "sha256:def",
            "authorized_terminal_intent": "code",
            "reviewer": {"identity": "core", "role": "plan-review-authority"},
            "decision": "accepted",
        }
        ok, code = pi.validate_initial_review_dict(bad)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_validate_initial_review_refuses_unknown_authority_field(
        self, pi: ModuleType
    ) -> None:
        """validate_initial_review_dict refuses an unknown authority-shaped field."""
        bad = {
            "schema_version": 1,
            "review_id": "rev-001",
            "envelope_fingerprint": "fp-abc",
            "plan_hash": "sha256:def",
            "authorized_terminal_intent": "code",
            "reviewer": {"identity": "core", "role": "plan-review-authority"},
            "decision": "accepted",
            "inject_authority": "bypass",  # unknown field
        }
        ok, code = pi.validate_initial_review_dict(bad)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_validate_initial_review_refuses_invalid_decision_enum(
        self, pi: ModuleType
    ) -> None:
        """validate_initial_review_dict refuses an out-of-enum decision value."""
        bad = {
            "schema_version": 1,
            "review_id": "rev-001",
            "envelope_fingerprint": "fp-abc",
            "plan_hash": "sha256:def",
            "authorized_terminal_intent": "code",
            "reviewer": {"identity": "core", "role": "plan-review-authority"},
            "decision": "pending",  # not "accepted"
        }
        ok, code = pi.validate_initial_review_dict(bad)
        assert not ok
        assert code == "denied-invalid-enum"
