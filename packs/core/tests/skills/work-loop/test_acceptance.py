"""T4 TDD suite: pure acceptance projection, freshness, and verdict invariants.

Mode: TDD (plan.md T4).

Tests:
  AC-0003: reviewed-execution-envelope.v1 projection and fingerprint determinism.
  AC-0004: change classifier — no-approval-required vs approval-required.
  AC-0007: truth-table and permutation verdict tests across all supported adapters.
  AC-0009: freshness mutation tests — exact-subject and path-set modes.

Follows the importlib.util.spec_from_file_location loader pattern so the
module remains unregistered in sys.modules between test sessions.
"""

from __future__ import annotations

import importlib.util
import json
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
def acc() -> ModuleType:
    """_acceptance.py loaded by path, unregistered."""
    return _load_module("acc_t4", SCRIPTS / "_acceptance.py")


# ── Shared fixtures ───────────────────────────────────────────────────────────

VALID_REFS = {
    "spec_policy": "approval:spec-policy:v1",
    "scope_and_non_goals": "approval:scope:v1",
    "authority_and_security": "approval:authority:v1",
    "public_contracts": "approval:contracts:v1",
    "durable_outputs": "approval:outputs:v1",
    "accepted_risk": "approval:risk:v1",
}


def _make_property(
    property_id: str = "prop-001",
    authority_ref: str = "approval:spec-policy:v1",
    term: str = "test-run",
    outcomes: list[str] | None = None,
    satisfaction_expr: str = "all",
    contradiction_expr: str = "none",
    freshness_scope: str = "exact-subject",
) -> dict:
    """Build a minimal valid acceptance-property.v1 record."""
    return {
        "schema_version": 1,
        "property_id": property_id,
        "spec_ref": "docs/specs/test-spec/spec.md",
        "authority_ref": authority_ref,
        "subject_selector": {
            "paths_or_artifacts": ["src/"],
            "fingerprint_algorithm": "sha256",
        },
        "required_observations": [
            {
                "term": term,
                "observation_type": "test-result",
                "producer_class": "ci-runner",
                "outcomes": outcomes if outcomes is not None else ["passed"],
            }
        ],
        "freshness_scope": freshness_scope,
        "satisfaction_rule": {"expression": satisfaction_expr},
        "contradiction_rule": {"expression": contradiction_expr},
        "policy_version": "v1",
    }


def _make_receipt(
    receipt_id: str = "r-001",
    criterion_ref: str = "prop-001",
    acceptance_fingerprint: str = "fp-current",
    term: str = "test-run",
    outcome: str = "passed",
    freshness_mode: str = "exact-subject",
) -> dict:
    """Build a minimal valid evidence-receipt.v1 record."""
    return {
        "schema_version": 1,
        "receipt_id": receipt_id,
        "acceptance_fingerprint": acceptance_fingerprint,
        "lineage": {"criterion_ref": criterion_ref},
        "selector": {"term": term},
        "freshness_mode": freshness_mode,
        "observation": {"type": "test-result"},
        "outcome": outcome,
        "producer": {"class": "ci-runner", "identity": "runner-generic"},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0003: Reviewed execution envelope
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnvelopeProjection:
    """AC-0003: reviewed-execution-envelope.v1 projection invariants."""

    def test_identical_inputs_produce_same_fingerprint(self, acc: ModuleType) -> None:
        """Identical ordered inputs always produce one fingerprint."""
        env_a = acc.derive_envelope(VALID_REFS)
        env_b = acc.derive_envelope(VALID_REFS)
        assert env_a["envelope_fingerprint"] == env_b["envelope_fingerprint"]
        assert env_a["envelope_fingerprint"]  # non-empty

    def test_equivalent_dicts_regardless_of_insertion_order_produce_same_fingerprint(
        self, acc: ModuleType
    ) -> None:
        """Dict insertion order must not change the fingerprint."""
        refs_a = dict(VALID_REFS)
        # Reverse insertion order
        refs_b = {k: VALID_REFS[k] for k in reversed(list(VALID_REFS))}
        fp_a = acc.derive_envelope(refs_a)["envelope_fingerprint"]
        fp_b = acc.derive_envelope(refs_b)["envelope_fingerprint"]
        assert fp_a == fp_b

    def test_changing_one_ref_changes_fingerprint(self, acc: ModuleType) -> None:
        """Each protected approval ref independently changes the fingerprint."""
        base_fp = acc.derive_envelope(VALID_REFS)["envelope_fingerprint"]
        for key in acc.ENVELOPE_REFS_KEYS:
            altered = {**VALID_REFS, key: VALID_REFS[key] + "-v2"}
            altered_fp = acc.derive_envelope(altered)["envelope_fingerprint"]
            assert altered_fp != base_fp, f"fingerprint unchanged after mutating {key!r}"

    def test_emitted_record_structure(self, acc: ModuleType) -> None:
        """Emitted envelope record has schema_version, envelope_fingerprint, refs."""
        env = acc.derive_envelope(VALID_REFS)
        assert env["schema_version"] == 1
        assert isinstance(env["envelope_fingerprint"], str)
        assert set(env["refs"].keys()) == set(acc.ENVELOPE_REFS_KEYS)

    def test_envelope_grants_no_authority_by_itself(self, acc: ModuleType) -> None:
        """The envelope record has no 'grants' or 'authority' field — it summarises."""
        env = acc.derive_envelope(VALID_REFS)
        assert "grants" not in env
        assert "authority" not in env

    def test_refuses_missing_required_ref(self, acc: ModuleType) -> None:
        """Missing any required ref raises AcceptanceRefused with a stable code."""
        for key in acc.ENVELOPE_REFS_KEYS:
            incomplete = {k: v for k, v in VALID_REFS.items() if k != key}
            with pytest.raises(acc.AcceptanceRefused) as exc_info:
                acc.derive_envelope(incomplete)
            assert exc_info.value.denial_code == "denied-missing-or-empty-ref"

    def test_refuses_empty_ref_value(self, acc: ModuleType) -> None:
        """An empty string ref value raises AcceptanceRefused."""
        empty = {**VALID_REFS, "spec_policy": ""}
        with pytest.raises(acc.AcceptanceRefused) as exc_info:
            acc.derive_envelope(empty)
        assert exc_info.value.denial_code == "denied-missing-or-empty-ref"

    def test_refuses_unknown_ref_key(self, acc: ModuleType) -> None:
        """An unknown key in refs raises AcceptanceRefused."""
        bad = {**VALID_REFS, "inject_escalation": "bypass"}
        with pytest.raises(acc.AcceptanceRefused) as exc_info:
            acc.derive_envelope(bad)
        assert exc_info.value.denial_code == "denied-unknown-authority-field"

    def test_refuses_non_dict_input(self, acc: ModuleType) -> None:
        """A non-dict refs input raises AcceptanceRefused."""
        with pytest.raises(acc.AcceptanceRefused) as exc_info:
            acc.derive_envelope("not-a-dict")  # type: ignore[arg-type]
        assert exc_info.value.denial_code == "denied-invalid-refs-type"

    def test_validate_envelope_dict_accepts_valid_record(self, acc: ModuleType) -> None:
        """validate_envelope_dict accepts a record produced by derive_envelope."""
        env = acc.derive_envelope(VALID_REFS)
        ok, code = acc.validate_envelope_dict(env)
        assert ok, f"validate_envelope_dict rejected valid record: {code}"
        assert code == "ok"

    def test_validate_envelope_dict_refuses_unknown_schema_version(
        self, acc: ModuleType
    ) -> None:
        """validate_envelope_dict refuses an out-of-enum schema_version."""
        env = acc.derive_envelope(VALID_REFS)
        bad = {**env, "schema_version": 99}
        ok, code = acc.validate_envelope_dict(bad)
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_validate_envelope_dict_refuses_missing_required_field(
        self, acc: ModuleType
    ) -> None:
        """validate_envelope_dict refuses a record missing a required field."""
        env = acc.derive_envelope(VALID_REFS)
        bad = {k: v for k, v in env.items() if k != "envelope_fingerprint"}
        ok, code = acc.validate_envelope_dict(bad)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_validate_envelope_dict_refuses_unknown_authority_field(
        self, acc: ModuleType
    ) -> None:
        """validate_envelope_dict refuses an unknown authority-shaped field."""
        env = acc.derive_envelope(VALID_REFS)
        bad = {**env, "inject_escalation": "bypass"}
        ok, code = acc.validate_envelope_dict(bad)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_validate_envelope_dict_refuses_unknown_refs_key(
        self, acc: ModuleType
    ) -> None:
        """validate_envelope_dict refuses an unknown key inside refs."""
        env = acc.derive_envelope(VALID_REFS)
        bad_env = dict(env)
        bad_env["refs"] = {**env["refs"], "inject_escalation": "bypass"}
        ok, code = acc.validate_envelope_dict(bad_env)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_supported_adapters_has_at_least_two_members(self, acc: ModuleType) -> None:
        """Conformance test: SUPPORTED_ADAPTERS must have at least two members."""
        assert len(acc.SUPPORTED_ADAPTERS) >= 2, (
            "SUPPORTED_ADAPTERS must declare at least two adapters so conformance "
            "tests always compare at least two runtimes"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0004: Change classification
# ═══════════════════════════════════════════════════════════════════════════════


class TestChangeClassifier:
    """AC-0004: change classifier — task/sequence/decomposition vs protected changes."""

    def _derive_fp(self, acc: ModuleType) -> str:
        return acc.derive_envelope(VALID_REFS)["envelope_fingerprint"]

    def test_identical_fingerprint_and_intent_is_no_approval_required(
        self, acc: ModuleType
    ) -> None:
        """Working-plan changes that leave envelope and intent unchanged need no approval."""
        fp = self._derive_fp(acc)
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent="code",
            proposed_envelope_fingerprint=fp,
            proposed_terminal_intent="code",
        )
        assert result == "no-approval-required"

    def test_changed_envelope_fingerprint_requires_approval(
        self, acc: ModuleType
    ) -> None:
        """A changed envelope fingerprint requires approval."""
        fp = self._derive_fp(acc)
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent="code",
            proposed_envelope_fingerprint=fp + "-changed",
            proposed_terminal_intent="code",
        )
        assert result == "approval-required"

    def test_changed_terminal_intent_requires_approval(self, acc: ModuleType) -> None:
        """A changed terminal intent requires approval."""
        fp = self._derive_fp(acc)
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent="code",
            proposed_envelope_fingerprint=fp,
            proposed_terminal_intent="spec-plan",
        )
        assert result == "approval-required"

    def test_both_changed_requires_approval(self, acc: ModuleType) -> None:
        """Changing both envelope and intent requires approval."""
        fp = self._derive_fp(acc)
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent="code",
            proposed_envelope_fingerprint="fp-changed",
            proposed_terminal_intent="spec-plan",
        )
        assert result == "approval-required"

    @pytest.mark.parametrize("task_change", [
        "add new task T10",
        "reorder tasks T1 and T2",
        "split T4 into T4a and T4b",
        "refine test method in T3",
        "update local implementation approach",
    ])
    def test_working_plan_provenance_changes_are_no_approval_required(
        self, acc: ModuleType, task_change: str
    ) -> None:
        """Task, sequence, decomposition, test-shape, and method changes need no approval."""
        fp = self._derive_fp(acc)
        # The classifier receives the (unchanged) fingerprint and intent — the
        # semantic meaning of the change is in the caller's framing, not here.
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent="code",
            proposed_envelope_fingerprint=fp,
            proposed_terminal_intent="code",
        )
        assert result == "no-approval-required", f"task change {task_change!r} should not require approval"

    def test_classifier_returns_no_task_state(self, acc: ModuleType) -> None:
        """The classifier returns only a string — no task, cancellation, or dispatch record."""
        fp = self._derive_fp(acc)
        result = acc.classify_change(
            current_envelope_fingerprint=fp,
            current_terminal_intent="code",
            proposed_envelope_fingerprint=fp,
            proposed_terminal_intent="code",
        )
        assert isinstance(result, str)
        assert result in ("no-approval-required", "approval-required")


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0007: Verdict truth-table and adapter conformance
# ═══════════════════════════════════════════════════════════════════════════════


class TestVerdictEvaluation:
    """AC-0007: verdict truth-table and cross-adapter determinism."""

    FP = "fp-current-001"

    def test_unapproved_when_no_authority_ref(self, acc: ModuleType) -> None:
        """Verdict is 'unapproved' when the property has an empty authority_ref."""
        prop = _make_property(authority_ref="")
        receipt = _make_receipt(acceptance_fingerprint=self.FP)
        verdict = acc.evaluate_verdict(
            property_record=prop,
            receipts=[receipt],
            current_acceptance_fingerprint=self.FP,
            adapter="sequential-reference",
        )
        assert verdict["verdict"] == "unapproved"

    def test_supported_when_fresh_receipt_satisfies_term(self, acc: ModuleType) -> None:
        """Verdict is 'supported' when a fresh receipt satisfies the required term."""
        prop = _make_property(satisfaction_expr="all", contradiction_expr="none")
        receipt = _make_receipt(
            term="test-run", outcome="passed", acceptance_fingerprint=self.FP
        )
        verdict = acc.evaluate_verdict(
            property_record=prop,
            receipts=[receipt],
            current_acceptance_fingerprint=self.FP,
            adapter="sequential-reference",
        )
        assert verdict["verdict"] == "supported"

    def test_insufficient_when_no_fresh_receipts(self, acc: ModuleType) -> None:
        """Verdict is 'insufficient' when there are no fresh receipts."""
        prop = _make_property()
        verdict = acc.evaluate_verdict(
            property_record=prop,
            receipts=[],
            current_acceptance_fingerprint=self.FP,
            adapter="sequential-reference",
        )
        assert verdict["verdict"] == "insufficient"

    def test_insufficient_when_receipt_is_stale(self, acc: ModuleType) -> None:
        """Verdict is 'insufficient' when the receipt's fingerprint does not match."""
        prop = _make_property()
        stale_receipt = _make_receipt(acceptance_fingerprint="fp-old")
        verdict = acc.evaluate_verdict(
            property_record=prop,
            receipts=[stale_receipt],
            current_acceptance_fingerprint=self.FP,
            adapter="sequential-reference",
        )
        assert verdict["verdict"] == "insufficient"

    def test_contradicted_when_contradiction_term_matched(self, acc: ModuleType) -> None:
        """Verdict is 'contradicted' when a fresh receipt matches a contradiction term."""
        prop = _make_property(
            contradiction_expr="supported-review-failure",
            satisfaction_expr="all",
        )
        # Fresh receipt for the contradictory term
        contradiction_receipt = _make_receipt(
            term="supported-review-failure",
            outcome="review-failure",
            acceptance_fingerprint=self.FP,
        )
        verdict = acc.evaluate_verdict(
            property_record=prop,
            receipts=[contradiction_receipt],
            current_acceptance_fingerprint=self.FP,
            adapter="sequential-reference",
        )
        assert verdict["verdict"] == "contradicted"

    def test_contradiction_precedes_support(self, acc: ModuleType) -> None:
        """Contradicted fires even when the satisfaction term is also met."""
        prop = _make_property(
            term="test-run",
            outcomes=["passed"],
            contradiction_expr="supported-review-failure",
            satisfaction_expr="all",
        )
        receipts = [
            _make_receipt(
                receipt_id="r-pass",
                term="test-run",
                outcome="passed",
                acceptance_fingerprint=self.FP,
            ),
            _make_receipt(
                receipt_id="r-fail",
                term="supported-review-failure",
                outcome="review-failure",
                acceptance_fingerprint=self.FP,
            ),
        ]
        verdict = acc.evaluate_verdict(
            property_record=prop,
            receipts=receipts,
            current_acceptance_fingerprint=self.FP,
            adapter="sequential-reference",
        )
        assert verdict["verdict"] == "contradicted"

    @pytest.mark.parametrize("adapter", ["sequential-reference", "core-compatibility"])
    def test_same_inputs_same_verdict_across_adapters(
        self, acc: ModuleType, adapter: str
    ) -> None:
        """Identical inputs produce the same verdict on every supported adapter."""
        prop = _make_property()
        receipt = _make_receipt(acceptance_fingerprint=self.FP)
        verdict = acc.evaluate_verdict(
            property_record=prop,
            receipts=[receipt],
            current_acceptance_fingerprint=self.FP,
            adapter=adapter,
        )
        assert verdict["verdict"] == "supported"
        assert verdict["evaluation_fingerprint"]

    def test_verdict_derives_from_evidence_log_ignoring_cached_verdict(
        self, acc: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verdict is re-derived from the evidence log; a planted cached-verdict is ignored.

        Proves AC-0007 through the persisted path: the facade writes a receipt to
        the shadow evidence log, EvidenceStore reads it back, and evaluate_verdict
        returns 'supported' even when shadow-verdict.json beside the log says 'unapproved'.
        Deleting state.json and engine-state.json (mechanical state) does not change
        the result.
        """
        facade = _load_module("facade_t4a", SCRIPTS / "_compat_facade.py")
        es_mod = _load_module("es_t4a", SCRIPTS / "_evidence_store.py")

        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "persist-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "persist-spec", "run_id": "persist-run"}
        pending = {
            "seq": 1, "event": "spec-ready",
            "from": "SPEC-PLAN-DRAFTING", "to": "SPEC-PLAN-REVIEW",
            "run_id": "persist-run", "at": "2026-01-01T00:00:00Z",
        }
        facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        shadow_dir = spec_dir / facade.SHADOW_SUBDIR
        log_path = shadow_dir / "shadow-evidence.log"
        assert log_path.exists(), "evidence log must be written by shadow_call_on_transition"

        # Read receipts back through the persisted evidence log.
        store = es_mod.EvidenceStore(log_path)
        store.open()
        receipts = store.get_all_active_receipts()
        assert len(receipts) == 1, "one receipt per transition event"
        acceptance_fp = receipts[0]["acceptance_fingerprint"]

        # Plant a cached-verdict file that disagrees — the evaluator must ignore it.
        (shadow_dir / "shadow-verdict.json").write_text(
            json.dumps({"verdict": "unapproved"}), encoding="utf-8"
        )
        # Plant then delete mechanical state files beside the store root.
        for name in ("state.json", "engine-state.json"):
            (spec_dir / name).write_text('{"state": "DONE"}', encoding="utf-8")
        for name in ("state.json", "engine-state.json"):
            (spec_dir / name).unlink()

        property_record = {
            "schema_version": 1,
            "property_id": "prop-persist-001",
            "authority_ref": "approval:persist-test:v1",
            "satisfaction_rule": {"expression": "any"},
            "required_observations": [
                {"term": "engine-transition:spec-ready", "outcomes": ["observed"]},
            ],
            "contradiction_rule": {"expression": "none"},
        }
        verdict = acc.evaluate_verdict(
            property_record=property_record,
            receipts=receipts,
            current_acceptance_fingerprint=acceptance_fp,
            adapter="sequential-reference",
        )
        assert verdict["verdict"] == "supported", (
            "AC-0007: verdict from the evidence log must be 'supported'; "
            f"got {verdict['verdict']!r}; the planted 'unapproved' cached-verdict is ignored"
        )

        # Mutation proof: changing receipt outcome changes the verdict.
        bad_receipt = {**receipts[0], "outcome": "not-observed"}
        v_bad = acc.evaluate_verdict(
            property_record=property_record,
            receipts=[bad_receipt],
            current_acceptance_fingerprint=acceptance_fp,
            adapter="sequential-reference",
        )
        assert v_bad["verdict"] != "supported", (
            "AC-0007: mutating receipt outcome must change the verdict"
        )

    def test_verdict_ignores_task_projection_field_on_receipt(
        self, acc: ModuleType
    ) -> None:
        """The evaluator ignores the task_projection_revision field on receipts.

        Proves AC-0007: mechanical task-projection state carried on a receipt must
        not enter the verdict or its evaluation_fingerprint.
        """
        prop = _make_property()
        base_receipt = _make_receipt(acceptance_fingerprint=self.FP)
        v_base = acc.evaluate_verdict(
            property_record=prop,
            receipts=[base_receipt],
            current_acceptance_fingerprint=self.FP,
            adapter="sequential-reference",
        )
        assert v_base["verdict"] == "supported"

        for other in (
            {**base_receipt, "task_projection_revision": "rev-abc"},
            {**base_receipt, "task_projection_revision": "rev-other"},
            {k: v for k, v in base_receipt.items() if k != "task_projection_revision"},
        ):
            v_other = acc.evaluate_verdict(
                property_record=prop,
                receipts=[other],
                current_acceptance_fingerprint=self.FP,
                adapter="sequential-reference",
            )
            assert v_other["verdict"] == v_base["verdict"], (
                "task_projection_revision must not change the verdict"
            )
            assert v_other["evaluation_fingerprint"] == v_base["evaluation_fingerprint"], (
                "task_projection_revision must not enter the evaluation_fingerprint"
            )

    def test_verdict_record_satisfies_schema_structure(self, acc: ModuleType) -> None:
        """The emitted verdict record contains all required fields."""
        prop = _make_property()
        receipt = _make_receipt(acceptance_fingerprint=self.FP)
        v = acc.evaluate_verdict(
            property_record=prop,
            receipts=[receipt],
            current_acceptance_fingerprint=self.FP,
            adapter="sequential-reference",
        )
        assert v["schema_version"] == 1
        assert isinstance(v["evaluation_fingerprint"], str) and v["evaluation_fingerprint"]
        assert v["verdict"] in ("unapproved", "contradicted", "supported", "insufficient")
        assert isinstance(v["criteria_refs"], list)
        assert isinstance(v["receipt_refs"], list)

    def test_refuses_unsupported_adapter(self, acc: ModuleType) -> None:
        """evaluate_verdict refuses an adapter not in SUPPORTED_ADAPTERS."""
        prop = _make_property()
        with pytest.raises(acc.AcceptanceRefused) as exc_info:
            acc.evaluate_verdict(
                property_record=prop,
                receipts=[],
                current_acceptance_fingerprint=self.FP,
                adapter="unknown-adapter",
            )
        assert exc_info.value.denial_code == "denied-unsupported-adapter"

    def test_validate_property_dict_accepts_valid_record(self, acc: ModuleType) -> None:
        """validate_property_dict accepts a valid acceptance-property.v1 record."""
        prop = _make_property()
        ok, code = acc.validate_property_dict(prop)
        assert ok, f"validate_property_dict rejected valid record: {code}"
        assert code == "ok"

    def test_validate_property_dict_refuses_unknown_schema_version(
        self, acc: ModuleType
    ) -> None:
        """validate_property_dict refuses an unknown schema_version."""
        bad = {**_make_property(), "schema_version": 99}
        ok, code = acc.validate_property_dict(bad)
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_validate_property_dict_refuses_missing_required_field(
        self, acc: ModuleType
    ) -> None:
        """validate_property_dict refuses a record missing a required field."""
        prop = _make_property()
        bad = {k: v for k, v in prop.items() if k != "authority_ref"}
        ok, code = acc.validate_property_dict(bad)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_validate_property_dict_refuses_unknown_authority_field(
        self, acc: ModuleType
    ) -> None:
        """validate_property_dict refuses an unknown authority-shaped field."""
        bad = {**_make_property(), "inject_escalation": "bypass"}
        ok, code = acc.validate_property_dict(bad)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_validate_property_dict_refuses_out_of_enum_freshness_scope(
        self, acc: ModuleType
    ) -> None:
        """validate_property_dict refuses a freshness_scope outside enum."""
        bad = {**_make_property(), "freshness_scope": "full-tree"}
        ok, code = acc.validate_property_dict(bad)
        assert not ok
        assert code == "denied-invalid-enum"

    def test_validate_verdict_dict_accepts_valid_record(self, acc: ModuleType) -> None:
        """validate_verdict_dict accepts a valid acceptance-verdict.v1 record."""
        prop = _make_property()
        receipt = _make_receipt(acceptance_fingerprint=self.FP)
        v = acc.evaluate_verdict(
            property_record=prop,
            receipts=[receipt],
            current_acceptance_fingerprint=self.FP,
            adapter="sequential-reference",
        )
        ok, code = acc.validate_verdict_dict(v)
        assert ok, f"validate_verdict_dict rejected valid record: {code}"
        assert code == "ok"

    def test_validate_verdict_dict_refuses_unknown_schema_version(
        self, acc: ModuleType
    ) -> None:
        """validate_verdict_dict refuses an unknown schema_version."""
        v = {
            "schema_version": 2,
            "evaluation_fingerprint": "fp",
            "verdict": "supported",
            "criteria_refs": [],
            "receipt_refs": [],
        }
        ok, code = acc.validate_verdict_dict(v)
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_validate_verdict_dict_refuses_missing_required_field(
        self, acc: ModuleType
    ) -> None:
        """validate_verdict_dict refuses a record missing a required field."""
        bad = {
            "schema_version": 1,
            "evaluation_fingerprint": "fp",
            # verdict omitted
            "criteria_refs": [],
            "receipt_refs": [],
        }
        ok, code = acc.validate_verdict_dict(bad)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_validate_verdict_dict_refuses_unknown_authority_field(
        self, acc: ModuleType
    ) -> None:
        """validate_verdict_dict refuses an unknown authority-shaped field."""
        bad = {
            "schema_version": 1,
            "evaluation_fingerprint": "fp",
            "verdict": "supported",
            "criteria_refs": [],
            "receipt_refs": [],
            "inject_escalation": "bypass",
        }
        ok, code = acc.validate_verdict_dict(bad)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_validate_verdict_dict_refuses_out_of_enum_verdict(
        self, acc: ModuleType
    ) -> None:
        """validate_verdict_dict refuses a verdict value outside the enum."""
        bad = {
            "schema_version": 1,
            "evaluation_fingerprint": "fp",
            "verdict": "maybe",
            "criteria_refs": [],
            "receipt_refs": [],
        }
        ok, code = acc.validate_verdict_dict(bad)
        assert not ok
        assert code == "denied-invalid-enum"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0009: Freshness evaluation
# ═══════════════════════════════════════════════════════════════════════════════


class TestFreshnessEvaluation:
    """AC-0009: exact-subject and path-set freshness mutation tests."""

    CURRENT_FP = "fp-current-v2"
    OLD_FP = "fp-old-v1"

    def test_exact_subject_fresh_when_fingerprint_matches(self, acc: ModuleType) -> None:
        """Exact-subject receipt is fresh when acceptance_fingerprint matches."""
        receipt = _make_receipt(
            acceptance_fingerprint=self.CURRENT_FP,
            freshness_mode="exact-subject",
        )
        assert acc.is_fresh(
            receipt=receipt,
            current_acceptance_fingerprint=self.CURRENT_FP,
        )

    def test_exact_subject_stale_when_fingerprint_differs(self, acc: ModuleType) -> None:
        """Exact-subject receipt is stale when acceptance_fingerprint does not match."""
        receipt = _make_receipt(
            acceptance_fingerprint=self.OLD_FP,
            freshness_mode="exact-subject",
        )
        assert not acc.is_fresh(
            receipt=receipt,
            current_acceptance_fingerprint=self.CURRENT_FP,
        )

    def test_path_set_fresh_when_fingerprint_and_attrs_match(
        self, acc: ModuleType
    ) -> None:
        """Path-set receipt is fresh when fingerprint and all path_set_attrs match."""
        receipt = {
            **_make_receipt(
                acceptance_fingerprint=self.CURRENT_FP,
                freshness_mode="path-set",
            ),
            "claim": "sha256:abc",
            "policy_ref": "policy-v1",
        }
        path_set_attrs = {"claim": "sha256:abc", "policy_ref": "policy-v1"}
        assert acc.is_fresh(
            receipt=receipt,
            current_acceptance_fingerprint=self.CURRENT_FP,
            path_set_attrs=path_set_attrs,
        )

    def test_path_set_stale_when_one_attr_differs(self, acc: ModuleType) -> None:
        """Path-set receipt is stale when any declared attribute does not match."""
        receipt = {
            **_make_receipt(
                acceptance_fingerprint=self.CURRENT_FP,
                freshness_mode="path-set",
            ),
            "claim": "sha256:abc",
            "policy_ref": "policy-v1",
        }
        # Change one attribute
        path_set_attrs = {"claim": "sha256:abc", "policy_ref": "policy-v2-changed"}
        assert not acc.is_fresh(
            receipt=receipt,
            current_acceptance_fingerprint=self.CURRENT_FP,
            path_set_attrs=path_set_attrs,
        )

    def test_path_set_falls_back_to_exact_subject_when_no_attrs(
        self, acc: ModuleType
    ) -> None:
        """Missing attestor (path_set_attrs=None) uses exact-subject fallback."""
        receipt = _make_receipt(
            acceptance_fingerprint=self.CURRENT_FP,
            freshness_mode="path-set",
        )
        # No path_set_attrs supplied → fall back to exact-subject: fingerprint match passes
        assert acc.is_fresh(
            receipt=receipt,
            current_acceptance_fingerprint=self.CURRENT_FP,
            path_set_attrs=None,
        )

    def test_path_set_stale_fingerprint_even_with_matching_attrs(
        self, acc: ModuleType
    ) -> None:
        """Path-set receipt is stale when fingerprint does not match, regardless of attrs."""
        receipt = {
            **_make_receipt(
                acceptance_fingerprint=self.OLD_FP,
                freshness_mode="path-set",
            ),
            "claim": "sha256:abc",
        }
        path_set_attrs = {"claim": "sha256:abc"}
        assert not acc.is_fresh(
            receipt=receipt,
            current_acceptance_fingerprint=self.CURRENT_FP,
            path_set_attrs=path_set_attrs,
        )

    @pytest.mark.parametrize("changed_field,new_value", [
        ("acceptance_fingerprint", "fp-old"),
        ("claim", "sha256:different"),
        ("policy_ref", "policy-v2"),
        ("toolchain", "python-3.12"),
        ("environment", "env-changed"),
    ])
    def test_path_set_stale_at_first_mismatch(
        self, acc: ModuleType, changed_field: str, new_value: str
    ) -> None:
        """Path-set evidence becomes stale at the first field mismatch."""
        base = {
            "acceptance_fingerprint": self.CURRENT_FP,
            "claim": "sha256:abc",
            "policy_ref": "policy-v1",
            "toolchain": "python-3.11",
            "environment": "env-original",
        }
        receipt = {
            **_make_receipt(freshness_mode="path-set"),
            **base,
        }
        receipt[changed_field] = new_value
        path_set_attrs = {k: v for k, v in base.items() if k != "acceptance_fingerprint"}
        # If the acceptance_fingerprint itself changed, the floor check catches it
        current_fp = (
            self.CURRENT_FP if changed_field != "acceptance_fingerprint" else self.CURRENT_FP
        )
        assert not acc.is_fresh(
            receipt=receipt,
            current_acceptance_fingerprint=current_fp,
            path_set_attrs=path_set_attrs,
        )

    def test_non_dict_receipt_is_always_stale(self, acc: ModuleType) -> None:
        """A non-dict receipt is always stale."""
        assert not acc.is_fresh(
            receipt="not-a-dict",  # type: ignore[arg-type]
            current_acceptance_fingerprint=self.CURRENT_FP,
        )

    def test_verdict_reflects_freshness_for_stale_exact_subject(
        self, acc: ModuleType
    ) -> None:
        """A stale exact-subject receipt cannot contribute to a supported verdict."""
        prop = _make_property()
        stale = _make_receipt(acceptance_fingerprint=self.OLD_FP)
        v = acc.evaluate_verdict(
            property_record=prop,
            receipts=[stale],
            current_acceptance_fingerprint=self.CURRENT_FP,
            adapter="sequential-reference",
        )
        assert v["verdict"] == "insufficient"
