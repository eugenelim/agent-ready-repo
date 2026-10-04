"""T7 TDD suite: evidence transactions recover and rehydrate without cached authority.

Mode: TDD through append-log integration tests (plan.md T7).

Tests:
  AC-0008: crash injection at every frame boundary, all-or-none visibility,
           incomplete-final-frame truncation, checksum/reference corruption refusal,
           index deletion and rebuild, verdict equivalence from complete prefix.
  AC-0009: receipt and supersession fixtures — stale or inadmissible records
           cannot support a property; contradiction evaluated before support.
  AC-0020: producer-capability checks before staging durable bytes — missing,
           expired, mismatched, and out-of-scope authority expose no partial
           transaction; retry also fails.
  AC-0021: sink-available and sink-unavailable cases.

Red evidence (before _evidence_store.py existed):
  - Importing the module raised ModuleNotFoundError / AttributeError on any
    attribute access; the first test that opens the store would fail immediately.
  - TDD discipline verified by importing the module first in each test.

Follows the importlib.util.spec_from_file_location loader pattern so the
module remains unregistered in sys.modules between test sessions.
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

# ── Path anchor ───────────────────────────────────────────────────────────────

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)


# ── Module loader ─────────────────────────────────────────────────────────────


def _load_module(name: str, path: Path) -> ModuleType:
    """Load an unregistered copy of a scripts module via importlib."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    finally:
        sys.dont_write_bytecode = prev


@pytest.fixture(scope="module")
def es() -> ModuleType:
    """_evidence_store.py loaded by path."""
    return _load_module("ev_store_t7", SCRIPTS / "_evidence_store.py")


@pytest.fixture(scope="module")
def acc() -> ModuleType:
    """_acceptance.py loaded by path."""
    return _load_module("acc_t7", SCRIPTS / "_acceptance.py")


@pytest.fixture(scope="module")
def sc() -> ModuleType:
    """_security_capability.py loaded by path."""
    return _load_module("sc_t7", SCRIPTS / "_security_capability.py")


# ── Common fixtures ───────────────────────────────────────────────────────────


def _null_sink(event: object) -> None:
    """No-op audit sink (sink available; no-op storage)."""


def _failing_sink(event: object) -> None:
    """Audit sink that always raises an OSError (sink unavailable)."""
    raise OSError("audit sink unavailable in test")


def _make_grant(sc: ModuleType) -> tuple:
    """Return a valid (issuer, grant) pair for evidence append tests."""
    issuer = sc.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["evidence"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["evidence"],
        control_denies=[],
    )
    return issuer, grant


_CURRENT_FP = "fp-t7-test-001"


def _make_receipt(receipt_id: str, criterion_ref: str = "prop-001") -> dict:
    """Build a minimal valid evidence-receipt.v1 record."""
    return {
        "schema_version": 1,
        "receipt_id": receipt_id,
        "acceptance_fingerprint": _CURRENT_FP,
        "lineage": {"criterion_ref": criterion_ref},
        "selector": {"term": "test-run"},
        "freshness_mode": "exact-subject",
        "observation": {"type": "test-result"},
        "outcome": "passed",
        "producer": {"class": "ci-runner", "identity": "runner-generic"},
    }


def _make_supersession(
    supersession_id: str,
    superseded_receipt_ids: list[str],
) -> dict:
    """Build a minimal valid evidence-supersession.v1 record."""
    return {
        "schema_version": 1,
        "supersession_id": supersession_id,
        "superseded_receipt_ids": superseded_receipt_ids,
        "authority": {"identity": "evidence-authority-generic", "role": "evidence-authority"},
        "provenance": {"reason_code": "review-assessment-superseded"},
    }


def _make_property(criterion_ref: str) -> dict:
    """Build an approved acceptance-property.v1 record for verdict evaluation."""
    return {
        "schema_version": 1,
        "property_id": criterion_ref,
        "spec_ref": "docs/specs/test-spec/spec.md",
        "authority_ref": "approval:spec-policy:v1",
        "subject_selector": {"paths_or_artifacts": ["src/"], "fingerprint_algorithm": "sha256"},
        "required_observations": [
            {
                "term": "test-run",
                "observation_type": "test-result",
                "producer_class": "ci-runner",
                "outcomes": ["passed"],
            }
        ],
        "freshness_scope": "exact-subject",
        "satisfaction_rule": {"expression": "all"},
        "contradiction_rule": {"expression": "none"},
        "policy_version": "v1",
    }


def _open_fresh_store(es: ModuleType, log_path: Path) -> object:
    """Create and open a fresh EvidenceStore at log_path."""
    store = es.EvidenceStore(log_path)
    store.open()
    return store


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0008: all-or-none visibility, truncation, corruption, index rebuild
# ═══════════════════════════════════════════════════════════════════════════════


class TestAllOrNoneVisibility:
    """AC-0008: a committed frame exposes all embedded records or none."""

    def test_committed_receipt_is_visible_after_open(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A receipt appended to the store is visible after a fresh open."""
        log_path = tmp_path / "evidence.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)
        receipt = _make_receipt("r-001")
        store.append_receipt(
            receipt, transaction_id="tx-001", issuer=issuer, grant=grant, audit_sink=_null_sink
        )
        assert store.receipt_count == 1
        assert store.transaction_count == 1

        # Re-open and verify persistence
        store2 = _open_fresh_store(es, log_path)
        assert store2.receipt_count == 1
        active = store2.get_active_receipts("prop-001")
        assert len(active) == 1
        assert active[0]["receipt_id"] == "r-001"

    def test_incomplete_final_frame_is_truncated(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0008: an incomplete final frame (no trailing newline) is truncated on restart.

        Red before: _evidence_store didn't exist, so the import itself would fail.
        After: store opens, appends a complete frame, then we inject an incomplete
        frame (bytes without trailing newline), and verify the store drops it.
        """
        log_path = tmp_path / "evidence.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)

        # Write one complete frame
        receipt = _make_receipt("r-complete")
        store.append_receipt(
            receipt,
            transaction_id="tx-complete",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
        assert store.receipt_count == 1

        # Simulate a crash mid-write: append bytes WITHOUT a trailing newline
        # (the frame boundary was written but not the terminating newline).
        # This represents a crash between writing bytes and writing the final "\n".
        partial_bytes = b'{"tx":{"schema_version":1,"transaction_id":"tx-crash",'
        log_path.write_bytes(log_path.read_bytes() + partial_bytes)

        # Re-open: should truncate the incomplete frame and retain only the complete one.
        store2 = _open_fresh_store(es, log_path)
        assert store2.receipt_count == 1, (
            "incomplete final frame must be truncated, not admitted"
        )
        assert store2.transaction_count == 1

        # The log file should end with a newline (all frames complete).
        assert log_path.read_bytes().endswith(b"\n")

    def test_zero_complete_frames_after_total_crash(
        self, es: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0008: when all bytes are an incomplete frame (no newline), the log truncates to empty."""
        log_path = tmp_path / "evidence-empty.log"
        # Manually create a log with ONLY incomplete bytes.
        log_path.write_bytes(b'{"tx":{"schema_version":1},"records":[]')

        store = _open_fresh_store(es, log_path)
        assert store.receipt_count == 0
        assert store.transaction_count == 0

    def test_crash_before_any_write_leaves_empty_store(
        self, es: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0008 boundary: a crash before any bytes are written leaves an empty store."""
        log_path = tmp_path / "evidence-pre-crash.log"
        store = _open_fresh_store(es, log_path)
        # No appends — verify empty store.
        assert store.receipt_count == 0
        store2 = _open_fresh_store(es, log_path)
        assert store2.receipt_count == 0


class TestChecksumAndReferenceCorruption:
    """AC-0008: checksum or reference corruption causes a hard refusal on open."""

    def _write_log_with_bad_checksum(self, es: ModuleType, log_path: Path) -> None:
        """Write a log file containing a frame with a wrong checksum."""
        receipt = _make_receipt("r-corrupt-ck")
        records = [receipt]
        tx_body = {
            "schema_version": 1,
            "transaction_id": "tx-corrupt-ck",
            "ordered_record_ids": ["r-corrupt-ck"],
            "acceptance_fingerprint": _CURRENT_FP,
        }
        # Deliberately use a wrong checksum value.
        tx = {**tx_body, "checksum": "sha256:deadbeefdeadbeefdeadbeefdeadbeef" + "0" * 32}
        frame = es._canonical_json({"tx": tx, "records": records}) + "\n"
        log_path.write_bytes(frame.encode("utf-8"))

    def test_bad_checksum_refuses_open(self, es: ModuleType, tmp_path: Path) -> None:
        """AC-0008: a frame with a bad checksum raises EvidenceStoreError on open.

        Red before: EvidenceStore didn't exist.
        Verify red by mutating the guard: if we remove the checksum check in
        _verify_frame, this test would fail (no error raised).
        """
        log_path = tmp_path / "corrupt-ck.log"
        self._write_log_with_bad_checksum(es, log_path)
        store = es.EvidenceStore(log_path)
        with pytest.raises(es.EvidenceStoreError, match="checksum"):
            store.open()

    def _write_log_with_bad_reference(self, es: ModuleType, log_path: Path) -> None:
        """Write a log file containing a frame where ordered_record_ids mismatches."""
        receipt = _make_receipt("r-real-id")
        records = [receipt]
        tx_body = {
            "schema_version": 1,
            "transaction_id": "tx-ref-corrupt",
            "ordered_record_ids": ["r-WRONG-id"],  # mismatch!
            "acceptance_fingerprint": _CURRENT_FP,
        }
        # Compute a valid checksum for this (deliberately wrong) tx_body.
        checksum = es._compute_frame_checksum(tx_body, records)
        tx = {**tx_body, "checksum": checksum}
        frame = es._canonical_json({"tx": tx, "records": records}) + "\n"
        log_path.write_bytes(frame.encode("utf-8"))

    def test_bad_reference_refuses_open(self, es: ModuleType, tmp_path: Path) -> None:
        """AC-0008: a frame with a reference mismatch raises EvidenceStoreError on open."""
        log_path = tmp_path / "corrupt-ref.log"
        self._write_log_with_bad_reference(es, log_path)
        store = es.EvidenceStore(log_path)
        with pytest.raises(es.EvidenceStoreError, match="reference mismatch"):
            store.open()


class TestIndexDeleteAndRebuild:
    """AC-0008 NFR: deleting and rebuilding indexes does not change the verdict."""

    def test_verdict_equivalent_before_and_after_index_rebuild(
        self, es: ModuleType, sc: ModuleType, acc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0008: index rebuild yields identical verdicts from the complete prefix."""
        log_path = tmp_path / "evidence-rebuild.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)

        # Append a receipt that satisfies prop-001.
        receipt = _make_receipt("r-rebuild-01")
        store.append_receipt(
            receipt, transaction_id="tx-rebuild-01", issuer=issuer, grant=grant, audit_sink=_null_sink
        )

        prop = _make_property("prop-001")
        verdicts_before = store.evaluate_verdicts([prop], _CURRENT_FP, acc)
        assert verdicts_before[0]["verdict"] == "supported"

        # Create a NEW store instance (deletes in-memory indexes), re-open (rebuilds).
        store2 = es.EvidenceStore(log_path)
        store2.open()
        verdicts_after = store2.evaluate_verdicts([prop], _CURRENT_FP, acc)

        assert verdicts_before[0]["verdict"] == verdicts_after[0]["verdict"]
        assert (
            verdicts_before[0]["evaluation_fingerprint"]
            == verdicts_after[0]["evaluation_fingerprint"]
        ), "evaluation fingerprint must be identical after index rebuild"

    def test_rebuild_indexes_method_preserves_verdict(
        self, es: ModuleType, sc: ModuleType, acc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0008: rebuild_indexes() call on the same store preserves the verdict."""
        log_path = tmp_path / "evidence-rebuild2.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)

        receipt = _make_receipt("r-rb2-01")
        store.append_receipt(
            receipt, transaction_id="tx-rb2-01", issuer=issuer, grant=grant, audit_sink=_null_sink
        )
        prop = _make_property("prop-001")
        verdicts_before = store.evaluate_verdicts([prop], _CURRENT_FP, acc)

        # Call rebuild_indexes on the same store object.
        store.rebuild_indexes()
        verdicts_after = store.evaluate_verdicts([prop], _CURRENT_FP, acc)

        assert verdicts_before[0]["verdict"] == verdicts_after[0]["verdict"]

    def test_verdict_equivalence_from_complete_prefix_after_crash(
        self, es: ModuleType, sc: ModuleType, acc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0008: the verdict from the complete prefix matches the pre-crash verdict."""
        log_path = tmp_path / "evidence-prefix.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)

        # Append several complete frames.
        for i in range(3):
            receipt = _make_receipt(f"r-prefix-{i:02d}")
            store.append_receipt(
                receipt,
                transaction_id=f"tx-prefix-{i:02d}",
                issuer=issuer,
                grant=grant,
                audit_sink=_null_sink,
            )

        prop = _make_property("prop-001")
        verdict_complete = store.evaluate_verdicts([prop], _CURRENT_FP, acc)

        # Inject an incomplete frame (crash simulation).
        log_path.write_bytes(log_path.read_bytes() + b"partial-crash-data")

        # Re-open: should truncate the incomplete frame.
        store2 = _open_fresh_store(es, log_path)
        verdict_from_prefix = store2.evaluate_verdicts([prop], _CURRENT_FP, acc)

        # The verdict must be "supported" in both cases since complete receipts are present.
        assert verdict_complete[0]["verdict"] == "supported"
        assert verdict_from_prefix[0]["verdict"] == "supported"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0009: freshness and contradiction
# ═══════════════════════════════════════════════════════════════════════════════


class TestFreshnessAndContradiction:
    """AC-0009: stale or superseded records cannot support a property."""

    def test_stale_receipt_does_not_support_verdict(
        self, es: ModuleType, sc: ModuleType, acc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0009: a receipt with the wrong acceptance_fingerprint is stale and yields insufficient."""
        log_path = tmp_path / "evidence-stale.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)

        # Append a receipt with an OLD acceptance fingerprint.
        old_fp = "fp-old-subject-001"
        stale_receipt: dict = {
            "schema_version": 1,
            "receipt_id": "r-stale-001",
            "acceptance_fingerprint": old_fp,  # old subject
            "lineage": {"criterion_ref": "prop-001"},
            "selector": {"term": "test-run"},
            "freshness_mode": "exact-subject",
            "observation": {"type": "test-result"},
            "outcome": "passed",
            "producer": {"class": "ci-runner", "identity": "runner-generic"},
        }
        store.append_receipt(
            stale_receipt,
            transaction_id="tx-stale-001",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )

        prop = _make_property("prop-001")
        # Evaluate against the CURRENT fingerprint (not old_fp).
        current_fp = "fp-current-001"
        verdicts = store.evaluate_verdicts([prop], current_fp, acc)
        assert verdicts[0]["verdict"] == "insufficient", (
            "a stale receipt must not support the verdict"
        )

    def test_superseded_receipt_does_not_support_verdict(
        self, es: ModuleType, sc: ModuleType, acc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0009: a superseded receipt is excluded from the active set and yields insufficient."""
        log_path = tmp_path / "evidence-superseded.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)

        # Append a supporting receipt.
        receipt = _make_receipt("r-to-supersede")
        store.append_receipt(
            receipt, transaction_id="tx-sup-01", issuer=issuer, grant=grant, audit_sink=_null_sink
        )
        prop = _make_property("prop-001")
        verdict_before = store.evaluate_verdicts([prop], _CURRENT_FP, acc)
        assert verdict_before[0]["verdict"] == "supported"

        # Now supersede that receipt.
        sup = _make_supersession("sup-001", ["r-to-supersede"])
        store.append_supersession(
            sup,
            transaction_id="tx-sup-02",
            acceptance_fingerprint=_CURRENT_FP,
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )

        # The receipt is now superseded — it must not support the verdict.
        verdict_after = store.evaluate_verdicts([prop], _CURRENT_FP, acc)
        assert verdict_after[0]["verdict"] == "insufficient", (
            "superseded receipt must not support the verdict"
        )

    def test_contradiction_evaluated_before_support(
        self, es: ModuleType, sc: ModuleType, acc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0009: contradiction is evaluated before satisfaction (AC-0007 ordering)."""
        log_path = tmp_path / "evidence-contradict.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)

        # Build a property that can be contradicted.
        prop_with_contradiction: dict = {
            "schema_version": 1,
            "property_id": "prop-contradict",
            "spec_ref": "docs/specs/test-spec/spec.md",
            "authority_ref": "approval:spec-policy:v1",
            "subject_selector": {"paths_or_artifacts": ["src/"], "fingerprint_algorithm": "sha256"},
            "required_observations": [
                {
                    "term": "test-run",
                    "observation_type": "test-result",
                    "producer_class": "ci-runner",
                    "outcomes": ["passed"],
                },
                {
                    "term": "review-failure",
                    "observation_type": "review-failure",
                    "producer_class": "review-bridge",
                    "outcomes": ["failed"],
                },
            ],
            "freshness_scope": "exact-subject",
            "satisfaction_rule": {"expression": "any"},
            "contradiction_rule": {"expression": "review-failure"},
            "policy_version": "v1",
        }

        # Append both a supporting receipt and a contradicting receipt.
        supporting_receipt = _make_receipt("r-support", "prop-contradict")
        store.append_receipt(
            supporting_receipt,
            transaction_id="tx-support",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )

        contradicting_receipt: dict = {
            "schema_version": 1,
            "receipt_id": "r-contradict",
            "acceptance_fingerprint": _CURRENT_FP,
            "lineage": {"criterion_ref": "prop-contradict"},
            "selector": {"term": "review-failure"},
            "freshness_mode": "exact-subject",
            "observation": {"type": "review-failure"},
            "outcome": "failed",
            "producer": {"class": "review-bridge", "identity": "review-bridge-generic"},
        }
        store.append_receipt(
            contradicting_receipt,
            transaction_id="tx-contradict",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )

        # Contradiction must fire before satisfaction — verdict is "contradicted".
        verdicts = store.evaluate_verdicts([prop_with_contradiction], _CURRENT_FP, acc)
        assert verdicts[0]["verdict"] == "contradicted", (
            "contradiction must be evaluated before support"
        )

    def test_inadmissible_supersession_cannot_support(
        self, es: ModuleType, sc: ModuleType, acc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0009: a supersession does not create a receipt; it only withdraws existing ones."""
        log_path = tmp_path / "evidence-sup-only.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)

        # Append ONLY a supersession with no matching receipt.
        sup = _make_supersession("sup-no-receipt", ["r-nonexistent"])
        store.append_supersession(
            sup,
            transaction_id="tx-sup-only",
            acceptance_fingerprint=_CURRENT_FP,
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )

        prop = _make_property("prop-001")
        verdicts = store.evaluate_verdicts([prop], _CURRENT_FP, acc)
        assert verdicts[0]["verdict"] == "insufficient", (
            "a supersession with no matching receipt must leave the verdict insufficient"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0020: producer capability checks before staging bytes
# ═══════════════════════════════════════════════════════════════════════════════


class TestProducerCapabilityChecks:
    """AC-0020: missing, expired, mismatched, and out-of-scope authority expose no partial transaction."""

    def test_missing_grant_refuses_append(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0020: a None grant refuses the append with a stable code; no bytes are staged."""
        log_path = tmp_path / "ev-missing-grant.log"
        store = _open_fresh_store(es, log_path)
        issuer = sc.CapabilityIssuer()
        receipt = _make_receipt("r-no-grant")

        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            store.append_receipt(
                receipt,
                transaction_id="tx-no-grant",
                issuer=issuer,
                grant=None,
                audit_sink=_null_sink,
            )
        assert exc_info.value.denial_code == "denied-invalid-grant"
        assert store.receipt_count == 0

    def test_missing_grant_with_failing_sink_uses_stable_redacted_code(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0021: a None grant whose denial cannot be audited refuses with the sink code."""
        store = _open_fresh_store(es, tmp_path / "ev-missing-grant-sink.log")

        def failing_sink(event: object) -> None:
            raise OSError("disk /private/path full")

        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            store.append_receipt(
                _make_receipt("r-no-grant-sink"),
                transaction_id="tx-no-grant-sink",
                issuer=sc.CapabilityIssuer(),
                grant=None,
                audit_sink=failing_sink,
            )
        assert exc_info.value.denial_code == "denied-audit-sink-unavailable"
        assert "/private/path" not in str(exc_info.value)
        assert store.receipt_count == 0

    def test_expired_grant_refuses_append(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0020: an expired grant refuses the append; no partial bytes staged."""
        log_path = tmp_path / "ev-expired-grant.log"
        store = _open_fresh_store(es, log_path)
        issuer = sc.CapabilityIssuer()
        # Issue a grant that expires immediately (expires_in_s=0).
        import time
        grant = issuer.issue_root_grant(
            roots=["evidence"],
            operations=["append"],
            trust_class="trusted",
            writes_allowed_roots=["evidence"],
            control_denies=[],
            expires_in_s=0,
        )
        time.sleep(0.01)  # Ensure expiry.
        receipt = _make_receipt("r-expired")

        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            store.append_receipt(
                receipt,
                transaction_id="tx-expired",
                issuer=issuer,
                grant=grant,
                audit_sink=_null_sink,
            )
        assert exc_info.value.denial_code in (
            "denied-invalid-grant",
            "denied-producer-authority",
        ), f"unexpected code: {exc_info.value.denial_code}"
        assert store.receipt_count == 0

    def test_revoked_grant_refuses_append(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0020: a revoked grant refuses the append; no partial bytes staged."""
        log_path = tmp_path / "ev-revoked-grant.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)
        issuer.revoke_grant(grant.grant_id)
        receipt = _make_receipt("r-revoked")

        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            store.append_receipt(
                receipt,
                transaction_id="tx-revoked",
                issuer=issuer,
                grant=grant,
                audit_sink=_null_sink,
            )
        assert exc_info.value.denial_code in (
            "denied-invalid-grant",
            "denied-producer-authority",
        ), f"unexpected code: {exc_info.value.denial_code}"
        assert store.receipt_count == 0

    def test_out_of_scope_grant_refuses_append(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0020: a grant with wrong writes.allowed_roots is out-of-scope; no partial bytes staged."""
        log_path = tmp_path / "ev-out-scope.log"
        store = _open_fresh_store(es, log_path)
        issuer = sc.CapabilityIssuer()
        # Grant access to "other-scope", NOT "evidence".
        grant = issuer.issue_root_grant(
            roots=["other-scope"],
            operations=["append"],
            trust_class="trusted",
            writes_allowed_roots=["other-scope"],  # wrong scope
            control_denies=[],
        )
        receipt = _make_receipt("r-wrong-scope")

        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            store.append_receipt(
                receipt,
                transaction_id="tx-wrong-scope",
                issuer=issuer,
                grant=grant,
                audit_sink=_null_sink,
            )
        assert exc_info.value.denial_code == "denied-producer-authority"
        assert store.receipt_count == 0

    def test_missing_operation_refuses_append(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0020: a grant without 'append' operation refuses the append; no bytes staged."""
        log_path = tmp_path / "ev-no-op.log"
        store = _open_fresh_store(es, log_path)
        issuer = sc.CapabilityIssuer()
        # Grant only "read", not "append".
        grant = issuer.issue_root_grant(
            roots=["evidence"],
            operations=["read"],  # no append
            trust_class="trusted",
            writes_allowed_roots=["evidence"],
            control_denies=[],
        )
        receipt = _make_receipt("r-no-op")

        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            store.append_receipt(
                receipt,
                transaction_id="tx-no-op",
                issuer=issuer,
                grant=grant,
                audit_sink=_null_sink,
            )
        assert exc_info.value.denial_code == "denied-producer-authority"
        assert store.receipt_count == 0

    def test_retry_under_denied_identity_stays_denied(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0020: retry with the same denied transaction_id still refuses; no partial record."""
        log_path = tmp_path / "ev-retry.log"
        store = _open_fresh_store(es, log_path)
        issuer = sc.CapabilityIssuer()
        # Grant without "append".
        grant = issuer.issue_root_grant(
            roots=["evidence"],
            operations=["read"],
            trust_class="trusted",
            writes_allowed_roots=["evidence"],
            control_denies=[],
        )
        receipt = _make_receipt("r-retry")

        for _attempt in range(3):
            with pytest.raises(es.EvidenceStoreRefused):
                store.append_receipt(
                    receipt,
                    transaction_id="tx-retry-same-id",  # same on every attempt
                    issuer=issuer,
                    grant=grant,
                    audit_sink=_null_sink,
                )
        assert store.receipt_count == 0, "retry must not expose a partial transaction"

    def test_supersession_also_validates_producer_authority(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0020: supersession append also validates producer authority before staging."""
        log_path = tmp_path / "ev-sup-no-op.log"
        store = _open_fresh_store(es, log_path)
        issuer = sc.CapabilityIssuer()
        grant = issuer.issue_root_grant(
            roots=["evidence"],
            operations=["read"],  # no append
            trust_class="trusted",
            writes_allowed_roots=["evidence"],
            control_denies=[],
        )
        sup = _make_supersession("sup-no-op", ["r-nonexistent"])

        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            store.append_supersession(
                sup,
                transaction_id="tx-sup-no-op",
                acceptance_fingerprint=_CURRENT_FP,
                issuer=issuer,
                grant=grant,
                audit_sink=_null_sink,
            )
        assert exc_info.value.denial_code == "denied-producer-authority"
        assert store.supersession_count == 0


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0021: sink-available and sink-unavailable cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestAuditSinkBehavior:
    """AC-0021: security events are emitted before success/refusal is acknowledged."""

    def test_sink_available_event_emitted_before_append(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0021: when the sink is available, an event is emitted before success is returned."""
        log_path = tmp_path / "ev-sink-avail.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)
        emitted_events: list = []

        def capturing_sink(event: object) -> None:
            emitted_events.append(event)

        receipt = _make_receipt("r-sink-avail")
        store.append_receipt(
            receipt,
            transaction_id="tx-sink-avail",
            issuer=issuer,
            grant=grant,
            audit_sink=capturing_sink,
        )

        assert len(emitted_events) >= 1, "at least one security event must be emitted"
        assert store.receipt_count == 1, "receipt must be committed"

    def test_sink_unavailable_fails_closed_no_bytes_staged(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0021: when the sink is unavailable, the operation fails closed; no frame is staged."""
        log_path = tmp_path / "ev-sink-unavail.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)

        receipt = _make_receipt("r-sink-unavail")
        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            store.append_receipt(
                receipt,
                transaction_id="tx-sink-unavail",
                issuer=issuer,
                grant=grant,
                audit_sink=_failing_sink,  # unavailable
            )

        assert exc_info.value.denial_code == "denied-audit-sink-unavailable", (
            f"expected denied-audit-sink-unavailable, got {exc_info.value.denial_code}"
        )
        assert store.receipt_count == 0, "no bytes must be staged when sink is unavailable"
        # The log must have no frames.
        assert log_path.read_bytes() == b""

    def test_sink_unavailable_no_durable_event_claimed(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0021: when the sink is unavailable, no durable-event claim is made."""
        log_path = tmp_path / "ev-sink-no-claim.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)

        receipt = _make_receipt("r-no-claim")
        with contextlib.suppress(es.EvidenceStoreRefused):
            store.append_receipt(
                receipt,
                transaction_id="tx-no-claim",
                issuer=issuer,
                grant=grant,
                audit_sink=_failing_sink,
            )

        # Re-open: the store must be empty (no frame was committed).
        store2 = _open_fresh_store(es, log_path)
        assert store2.receipt_count == 0

    def test_denial_emits_event_before_refusal(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """AC-0021: even a denied append emits a security event before refusing."""
        log_path = tmp_path / "ev-denial-event.log"
        store = _open_fresh_store(es, log_path)
        issuer = sc.CapabilityIssuer()
        # Grant without append operation.
        grant = issuer.issue_root_grant(
            roots=["evidence"],
            operations=["read"],
            trust_class="trusted",
            writes_allowed_roots=["evidence"],
            control_denies=[],
        )
        emitted_events: list = []

        def capturing_sink(event: object) -> None:
            emitted_events.append(event)

        receipt = _make_receipt("r-denial-event")
        with pytest.raises(es.EvidenceStoreRefused):
            store.append_receipt(
                receipt,
                transaction_id="tx-denial-event",
                issuer=issuer,
                grant=grant,
                audit_sink=capturing_sink,
            )

        assert len(emitted_events) >= 1, (
            "a denied append must emit a security event before refusing"
        )
        event = emitted_events[0]
        assert event.outcome == "denied"


# ═══════════════════════════════════════════════════════════════════════════════
# validate_*_dict: in-code schema validation for all three record types
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidateTransactionDict:
    """In-code validation for semantic-evidence-transaction.v1."""

    def test_valid_transaction_passes(self, es: ModuleType, sc: ModuleType, tmp_path: Path) -> None:
        log_path = tmp_path / "ev-val-tx.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)
        receipt = _make_receipt("r-val-tx")
        tx = store.append_receipt(
            receipt, transaction_id="tx-val-tx", issuer=issuer, grant=grant, audit_sink=_null_sink
        )
        ok, code = es.validate_transaction_dict(tx)
        assert ok, f"validate_transaction_dict must accept a valid record: {code}"
        assert code == "ok"

    def test_refuses_unknown_schema_version(self, es: ModuleType) -> None:
        bad = {
            "schema_version": 99,
            "transaction_id": "tx-001",
            "ordered_record_ids": ["r-001"],
            "acceptance_fingerprint": "fp-001",
            "checksum": "sha256:abc",
        }
        ok, code = es.validate_transaction_dict(bad)
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_refuses_missing_required_field(self, es: ModuleType) -> None:
        bad = {
            "schema_version": 1,
            # transaction_id omitted
            "ordered_record_ids": ["r-001"],
            "acceptance_fingerprint": "fp-001",
            "checksum": "sha256:abc",
        }
        ok, code = es.validate_transaction_dict(bad)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_refuses_unknown_authority_field(self, es: ModuleType) -> None:
        bad = {
            "schema_version": 1,
            "transaction_id": "tx-001",
            "ordered_record_ids": ["r-001"],
            "acceptance_fingerprint": "fp-001",
            "checksum": "sha256:abc",
            "inject_escalation": "bypass",
        }
        ok, code = es.validate_transaction_dict(bad)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_refuses_empty_ordered_record_ids(self, es: ModuleType) -> None:
        bad = {
            "schema_version": 1,
            "transaction_id": "tx-001",
            "ordered_record_ids": [],  # empty
            "acceptance_fingerprint": "fp-001",
            "checksum": "sha256:abc",
        }
        ok, code = es.validate_transaction_dict(bad)
        assert not ok
        assert code == "denied-empty-ordered-record-ids"


class TestValidateReceiptDict:
    """In-code validation for evidence-receipt.v1."""

    def test_valid_receipt_passes(self, es: ModuleType) -> None:
        ok, code = es.validate_receipt_dict(_make_receipt("r-valid"))
        assert ok, f"validate_receipt_dict must accept a valid record: {code}"
        assert code == "ok"

    def test_refuses_unknown_schema_version(self, es: ModuleType) -> None:
        bad = {**_make_receipt("r-bad-sv"), "schema_version": 99}
        ok, code = es.validate_receipt_dict(bad)
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_refuses_missing_required_field(self, es: ModuleType) -> None:
        bad = {k: v for k, v in _make_receipt("r-miss").items() if k != "receipt_id"}
        ok, code = es.validate_receipt_dict(bad)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_refuses_unknown_authority_field(self, es: ModuleType) -> None:
        bad = {**_make_receipt("r-extra"), "inject_escalation": "bypass"}
        ok, code = es.validate_receipt_dict(bad)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_refuses_out_of_enum_freshness_mode(self, es: ModuleType) -> None:
        bad = {**_make_receipt("r-bad-fm"), "freshness_mode": "full-tree"}
        ok, code = es.validate_receipt_dict(bad)
        assert not ok
        assert code == "denied-invalid-enum"


class TestValidateSupersessionDict:
    """In-code validation for evidence-supersession.v1."""

    def test_valid_supersession_passes(self, es: ModuleType) -> None:
        sup = _make_supersession("sup-valid", ["r-001"])
        ok, code = es.validate_supersession_dict(sup)
        assert ok, f"validate_supersession_dict must accept a valid record: {code}"
        assert code == "ok"

    def test_refuses_unknown_schema_version(self, es: ModuleType) -> None:
        bad = {**_make_supersession("sup-bad-sv", ["r-001"]), "schema_version": 99}
        ok, code = es.validate_supersession_dict(bad)
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_refuses_missing_required_field(self, es: ModuleType) -> None:
        bad = {
            k: v
            for k, v in _make_supersession("sup-miss", ["r-001"]).items()
            if k != "supersession_id"
        }
        ok, code = es.validate_supersession_dict(bad)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_refuses_unknown_authority_field(self, es: ModuleType) -> None:
        bad = {**_make_supersession("sup-extra", ["r-001"]), "inject_escalation": "bypass"}
        ok, code = es.validate_supersession_dict(bad)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_refuses_empty_superseded_ids(self, es: ModuleType) -> None:
        bad = {**_make_supersession("sup-empty", ["r-001"]), "superseded_receipt_ids": []}
        ok, code = es.validate_supersession_dict(bad)
        assert not ok
        assert code == "denied-empty-superseded-ids"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0008 / AC-0011: partial-write rollback and store-poison invariants
# ═══════════════════════════════════════════════════════════════════════════════


class TestAppendFaultInjection:
    """AC-0008: a partial write is rolled back; a subsequent append lands cleanly.

    Monkeypatches os.write in the confined_mutation module (via the shared os
    object) to simulate a mid-write ENOSPC failure, then verifies that:
      1. The failed append leaves the log at its pre-append size.
      2. A subsequent successful append lands correctly.
      3. A fresh reopen yields exactly the complete records (no partial bytes).
    Also verifies that rollback failure poisons the store: all further appends
    refuse with a stable denial code until the store is reopened.
    """

    def test_partial_write_rolled_back_and_store_reopens_clean(
        self,
        es: ModuleType,
        sc: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A mid-append ENOSPC is rolled back; the store reopens with only complete records.

        Red before the fix: os.write in confined_append had no rollback, so the
        partial bytes survived. After the fix: ftruncate restores the file to its
        pre-append size, so the next append and a fresh reopen see only complete
        frames.
        """
        import errno

        log_path = tmp_path / "fault-rollback.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)

        # Append one complete frame before the fault.
        receipt_a = _make_receipt("r-fault-a")
        store.append_receipt(
            receipt_a,
            transaction_id="tx-fa",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
        assert store.receipt_count == 1
        pre_fault_size = log_path.stat().st_size

        # Monkeypatch os.write to write 1 byte then raise ENOSPC.
        original_write = os.write

        def _partial_then_fail(fd: int, data: bytes) -> int:
            original_write(fd, data[:1])
            raise OSError(errno.ENOSPC, "no space left on device")

        monkeypatch.setattr(os, "write", _partial_then_fail)
        try:
            receipt_b = _make_receipt("r-fault-b")
            with pytest.raises(es.EvidenceStoreRefused):
                store.append_receipt(
                    receipt_b,
                    transaction_id="tx-fb",
                    issuer=issuer,
                    grant=grant,
                    audit_sink=_null_sink,
                )
        finally:
            monkeypatch.setattr(os, "write", original_write)

        # Log must be back to pre-fault size (rollback succeeded).
        assert log_path.stat().st_size == pre_fault_size, (
            "partial write bytes must be rolled back to the pre-append position"
        )

        # A subsequent append must succeed cleanly.
        receipt_c = _make_receipt("r-fault-c")
        store.append_receipt(
            receipt_c,
            transaction_id="tx-fc",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
        assert store.receipt_count == 2  # r-fault-a and r-fault-c only

        # Fresh reopen must yield exactly the two complete records.
        store2 = _open_fresh_store(es, log_path)
        assert store2.receipt_count == 2
        active = store2.get_active_receipts("prop-001")
        ids = {r["receipt_id"] for r in active}
        assert "r-fault-a" in ids
        assert "r-fault-c" in ids
        assert "r-fault-b" not in ids, "rolled-back receipt must not appear after reopen"

    def test_rollback_failure_poisons_store(
        self,
        es: ModuleType,
        sc: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When a rollback truncation fails, the store is poisoned and refuses further appends.

        Red before the fix: rollback did not exist, so the store had no way to
        detect or signal the unknown-file-state condition. After the fix: the
        store sets a poisoned flag and refuses any subsequent append with
        ``denied-store-poisoned`` until reopened.
        """
        import errno

        log_path = tmp_path / "fault-poison.log"
        store = _open_fresh_store(es, log_path)
        issuer, grant = _make_grant(sc)

        original_write = os.write
        original_ftruncate = os.ftruncate

        def _partial_then_fail(fd: int, data: bytes) -> int:
            original_write(fd, data[:1])
            raise OSError(errno.ENOSPC, "no space left on device")

        def _ftruncate_fail(fd: int, length: int) -> None:
            raise OSError(errno.EIO, "simulated IO error during rollback truncation")

        monkeypatch.setattr(os, "write", _partial_then_fail)
        monkeypatch.setattr(os, "ftruncate", _ftruncate_fail)
        try:
            receipt_a = _make_receipt("r-poison-a")
            with pytest.raises(es.EvidenceStoreRefused) as exc_info:
                store.append_receipt(
                    receipt_a,
                    transaction_id="tx-poa",
                    issuer=issuer,
                    grant=grant,
                    audit_sink=_null_sink,
                )
            assert "rollback-failed" in exc_info.value.denial_code, (
                f"expected rollback-failed denial, got {exc_info.value.denial_code!r}"
            )
        finally:
            monkeypatch.setattr(os, "write", original_write)
            monkeypatch.setattr(os, "ftruncate", original_ftruncate)

        # Store is now poisoned: any further append must refuse.
        receipt_b = _make_receipt("r-poison-b")
        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            store.append_receipt(
                receipt_b,
                transaction_id="tx-pob",
                issuer=issuer,
                grant=grant,
                audit_sink=_null_sink,
            )
        assert "poisoned" in exc_info.value.denial_code, (
            f"expected poisoned denial, got {exc_info.value.denial_code!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Log-path confinement: symlink and non-regular log refusal
# ═══════════════════════════════════════════════════════════════════════════════


class TestLogPathConfinement:
    """Evidence store refuses a symlinked or non-regular log path.

    Tests (a) and (c) from the log-path symlink fix.  Each must fail when
    the fix is reverted (i.e. when resolve() is restored in __init__ and
    read_bytes() is restored in _load_and_truncate).
    """

    @staticmethod
    def _has_symlink_support(tmp_path: Path) -> bool:
        test_link = tmp_path / "_symlink_test_es"
        try:
            test_link.symlink_to(tmp_path)
            test_link.unlink()
            return True
        except (NotImplementedError, OSError):
            return False

    def test_store_refuses_symlinked_log_nothing_written_outside(
        self, es: ModuleType, tmp_path: Path
    ) -> None:
        """(a) Store refuses to open when the log is a symlink; no bytes reach the target.

        Red evidence: restoring ``log_path.resolve()`` in ``EvidenceStore.__init__``
        and ``read_bytes()`` in ``_load_and_truncate`` makes this test pass by
        following the symlink, opening successfully, and writing to the target.
        """
        if not self._has_symlink_support(tmp_path):
            pytest.skip("symlinks not supported on this platform")

        outside = tmp_path / "outside-target"
        outside.mkdir()
        target_file = outside / "evil.log"

        log_link = tmp_path / "evidence.log"
        log_link.symlink_to(target_file)

        store = es.EvidenceStore(log_link)
        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            store.open()

        assert exc_info.value.denial_code == "denied-log-not-regular", (
            f"expected denied-log-not-regular, got {exc_info.value.denial_code!r}"
        )
        # Nothing must have been written to or created in the outside directory.
        assert not target_file.exists(), (
            "no bytes must be written to the symlink target"
        )
        assert list(outside.iterdir()) == [], (
            "outside directory must remain empty"
        )

    def test_store_refuses_symlinked_log_that_points_to_existing_file(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """(a) Store refuses to open when the symlink target already exists.

        A symlink to an existing file is also refused — the lstat check sees
        S_ISLNK and refuses before any read.
        """
        if not self._has_symlink_support(tmp_path):
            pytest.skip("symlinks not supported on this platform")

        outside = tmp_path / "outside-existing"
        outside.mkdir()
        target_file = outside / "existing.log"
        target_file.write_bytes(b"")  # target exists

        log_link = tmp_path / "evidence-existing.log"
        log_link.symlink_to(target_file)

        store = es.EvidenceStore(log_link)
        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            store.open()

        assert exc_info.value.denial_code == "denied-log-not-regular"

    def test_store_refuses_directory_as_log_path(
        self, es: ModuleType, tmp_path: Path
    ) -> None:
        """(c) Store refuses to open when the log path is a directory.

        Red evidence: restoring ``read_bytes()`` without the lstat check in
        ``open()`` allows the open call to succeed (``is not self._log_path.exists()``
        returns False for a directory that exists), and read_bytes() raises
        ``IsADirectoryError``, giving a different exception type.
        """
        log_dir = tmp_path / "evidence.log"
        log_dir.mkdir()

        store = es.EvidenceStore(log_dir)
        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            store.open()

        assert exc_info.value.denial_code == "denied-log-not-regular", (
            f"expected denied-log-not-regular, got {exc_info.value.denial_code!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Advisory-lock confinement: symlink swap, FIFO, and inode change
# ═══════════════════════════════════════════════════════════════════════════════


class TestAdvisoryLockConfinement:
    """Advisory lock and truncation refuse a swapped-in symlink, FIFO, or changed inode.

    These tests exercise the no-follow, regular-file, and identity checks
    added to _advisory_lock.  Each must fail when the fix is reverted
    (i.e. when _advisory_lock is restored to the bare os.open-by-path form).

    All tests skip when fcntl is unavailable (non-POSIX platforms fall back
    to atomic replace, bypassing _advisory_lock entirely) or when the host
    does not supply the relevant OS primitive.
    """

    @staticmethod
    def _require_fcntl(es: ModuleType) -> None:
        """Skip the test when fcntl is not available on this platform."""
        if not getattr(es, "_HAS_FCNTL", False):
            pytest.skip("fcntl not available; advisory lock is not used on this platform")

    def test_symlink_swap_after_read_refused_outside_file_unchanged(
        self, es: ModuleType, tmp_path: Path
    ) -> None:
        """A symlink placed at the log path after the read is refused; the link target is untouched.

        Red evidence: the old _advisory_lock opened by path with no O_NOFOLLOW,
        so a symlink swapped in after the read was followed and the outside file
        was truncated.  With the fix, O_NOFOLLOW causes os.open to raise ELOOP,
        which is converted to EvidenceStoreError before any bytes are written.
        """
        self._require_fcntl(es)
        if not hasattr(os, "O_NOFOLLOW"):
            pytest.skip("O_NOFOLLOW not available on this platform")
        try:
            _test_link = tmp_path / "_sym_probe"
            _test_link.symlink_to(tmp_path)
            _test_link.unlink()
        except (NotImplementedError, OSError):
            pytest.skip("symlinks not supported on this platform")

        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        outside_file = outside_dir / "outside.log"
        outside_file.write_bytes(b"original-content")

        log_path = tmp_path / "sym-swap.log"
        store = es.EvidenceStore(log_path)
        store.open()

        # Record the identity of the real log file.
        log_stat = os.lstat(log_path)
        store._log_identity = (log_stat.st_dev, log_stat.st_ino)  # type: ignore[attr-defined]

        # Swap the log for a symlink pointing to the outside file.
        log_path.unlink()
        log_path.symlink_to(outside_file)

        # Truncation must refuse rather than follow the symlink.
        with pytest.raises(es.EvidenceStoreError):
            store._truncate_log_safe(b"", bytes_read=0)  # type: ignore[attr-defined]

        # The outside file must be completely unchanged.
        assert outside_file.read_bytes() == b"original-content", (
            "symlink target must not be modified by the refused truncation"
        )

    def test_fifo_at_log_path_does_not_block(
        self, es: ModuleType, tmp_path: Path
    ) -> None:
        """A FIFO placed at the log path is refused without blocking.

        Red evidence: the old _advisory_lock opened by path with no O_NONBLOCK,
        so a FIFO at the log path could block the advisory-lock open indefinitely.
        With the fix, O_NONBLOCK prevents the block and the S_ISREG check
        then refuses the FIFO with EvidenceStoreError.
        """
        import threading

        self._require_fcntl(es)
        if not hasattr(os, "mkfifo"):
            pytest.skip("mkfifo not available on this platform")

        log_path = tmp_path / "fifo-test.log"
        store = es.EvidenceStore(log_path)
        store.open()

        log_stat = os.lstat(log_path)
        store._log_identity = (log_stat.st_dev, log_stat.st_ino)  # type: ignore[attr-defined]

        # Replace the log file with a FIFO.
        log_path.unlink()
        os.mkfifo(str(log_path))

        exc_holder: list[BaseException | None] = [None]

        def _run() -> None:
            try:
                store._truncate_log_safe(b"", bytes_read=0)  # type: ignore[attr-defined]
            except BaseException as exc:
                exc_holder[0] = exc

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join(timeout=2.0)

        assert not thread.is_alive(), (
            "truncation blocked on FIFO — O_NONBLOCK or S_ISREG check is missing"
        )
        assert isinstance(exc_holder[0], es.EvidenceStoreError), (
            f"expected EvidenceStoreError for FIFO, got {type(exc_holder[0])}: {exc_holder[0]}"
        )

    def test_inode_change_between_read_and_truncate_is_refused(
        self, es: ModuleType, tmp_path: Path
    ) -> None:
        """An inode change between read and truncation is detected and refused.

        Red evidence: the old _advisory_lock compared nothing against the read
        identity, so a file atomically replaced between read and truncation was
        silently truncated.  With the fix, the (st_dev, st_ino) recorded at read
        time is compared against the descriptor opened for locking, and a mismatch
        raises EvidenceStoreError before any truncation occurs.
        """
        self._require_fcntl(es)

        log_path = tmp_path / "inode-change.log"
        store = es.EvidenceStore(log_path)
        store.open()

        # Record the current log identity (simulating what _load_and_truncate stores).
        log_stat = os.lstat(log_path)
        original_identity = (log_stat.st_dev, log_stat.st_ino)
        store._log_identity = original_identity  # type: ignore[attr-defined]

        # Atomically replace the log file so the new file has a different inode.
        replacement = tmp_path / "replacement.log"
        replacement.write_bytes(b"new-content\n")
        replacement.rename(log_path)

        # The new file's inode differs from original_identity.
        new_stat = os.lstat(log_path)
        assert (new_stat.st_dev, new_stat.st_ino) != original_identity, (
            "test setup error: rename did not change the inode"
        )

        # Truncation must refuse because the inode changed.
        with pytest.raises(es.EvidenceStoreError):
            store._truncate_log_safe(b"", bytes_read=100)  # type: ignore[attr-defined]

        # The replacement file must not have been truncated.
        assert log_path.read_bytes() == b"new-content\n", (
            "replacement file must not be truncated after identity-change refusal"
        )
