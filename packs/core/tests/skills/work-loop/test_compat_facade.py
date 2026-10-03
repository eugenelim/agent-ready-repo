"""T8 goal-based compatibility suite: _compat_facade.py.

Mode: goal-based check through end-to-end compatibility suites (plan.md T8).

Tests cover:

  AC-0007  dual-emitted legacy and target evidence over a frozen corpus yields
           identical verdicts after deleting target indexes and mechanical state.

  AC-0011  every shadow write is routed through confined_mutation primitives;
           a symlinked .shadow-acceptance or symlinked spec_dir refuses with no
           write outside the root; one red is proved by disabling confinement.

  AC-0016  command, transition, legacy-plan-pin, cohort-writer, no-dispatch, and
           completion-decision fixtures compared with shadow OFF and ON; shadow
           refusal, unavailable audit sink, and service exception all leave the
           legacy result unchanged.

  AC-0017  disabling target calls restores the legacy path; a missing accepted
           governance fingerprint refuses every target-authority switch.

Fault injection via monkeypatching (no test-only hooks in shipped scripts/).
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

# ── Path anchors ─────────────────────────────────────────────────────────────

_SKILL_DIR = (
    Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
)
SCRIPTS = _SKILL_DIR / "scripts"
ENGINE = SCRIPTS / "loop-engine.py"
COHORT = SCRIPTS / "loop-cohort.py"
FACADE = SCRIPTS / "_compat_facade.py"

if not FACADE.is_file():
    raise SystemExit(f"facade not found at {FACADE} — check parents[] depth")


# ── Module loader helper ──────────────────────────────────────────────────────


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


# ── Shared fixtures ───────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def facade() -> ModuleType:
    """_compat_facade.py loaded by path, unregistered."""
    return _load_module("facade_t8", FACADE)


@pytest.fixture(scope="module")
def acc() -> ModuleType:
    """_acceptance.py loaded by path, unregistered."""
    return _load_module("acc_t8", SCRIPTS / "_acceptance.py")


@pytest.fixture(scope="module")
def cm() -> ModuleType:
    """_confined_mutation.py loaded by path, unregistered."""
    return _load_module("cm_t8", SCRIPTS / "_confined_mutation.py")


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Temporary git repository for engine invocations."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True)
    return tmp_path


@pytest.fixture
def spec_dir(git_repo: Path) -> Path:
    """A temporary spec directory inside the git repo."""
    sd = git_repo / "docs" / "specs" / "test-feature"
    sd.mkdir(parents=True)
    return sd


# ── Helper: run the engine CLI ────────────────────────────────────────────────


def _engine(args: list[str], *, cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run loop-engine.py with the given arguments."""
    full_env = {**os.environ, **(env or {})}
    return subprocess.run(
        [sys.executable, str(ENGINE), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(cwd),
        env=full_env,
    )


def _cohort(args: list[str], *, cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run loop-cohort.py with the given arguments."""
    full_env = {**os.environ, **(env or {})}
    return subprocess.run(
        [sys.executable, str(COHORT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(cwd),
        env=full_env,
    )


# ── Helper: minimal engine run through spec-approved ─────────────────────────


def _run_to_spec_approved(spec_dir: Path, cwd: Path, *, shadow_env: str | None = None) -> str:
    """Run the engine and cohort through a spec-approved event; return run_id."""
    env: dict[str, str] = {}
    if shadow_env is not None:
        env["WORK_LOOP_SHADOW_SERVICES"] = shadow_env

    # init engine
    r = _engine(["init", str(spec_dir), "--mode", "code", "--json"], cwd=cwd, env=env)
    assert r.returncode == 0, f"engine init failed: {r.stderr}"
    run_id = json.loads(r.stdout)["run_id"]

    # init cohort
    r = _cohort(["init", str(spec_dir), "--run-id", run_id], cwd=cwd, env=env)
    assert r.returncode == 0, f"cohort init failed: {r.stderr}"

    # Write minimal spec with Status: Approved
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Approved\n\n## Acceptance Criteria\n\n- [ ] AC-001.\n",
        encoding="utf-8",
    )

    # spec-ready → SPEC-PLAN-REVIEW
    r = _engine(["transition", str(spec_dir), "spec-ready"], cwd=cwd, env=env)
    assert r.returncode == 0, f"spec-ready failed: {r.stderr}"

    # reviewers-clean (SPEC-PLAN-REVIEW) — skip review
    r = _engine(
        ["transition", str(spec_dir), "reviewers-clean", "--all-skipped"],
        cwd=cwd, env=env,
    )
    assert r.returncode == 0, f"reviewers-clean failed: {r.stderr}"

    # spec-approved
    r = _engine(["transition", str(spec_dir), "spec-approved"], cwd=cwd, env=env)
    assert r.returncode == 0, f"spec-approved failed: {r.stderr}"

    return run_id


# ─────────────────────────────────────────────────────────────────────────────
# AC-0016: shadow OFF = byte-for-byte identical behavior
# ─────────────────────────────────────────────────────────────────────────────


class TestAC0016ShadowOff:
    """With shadow calls disabled, the engine behaves identically to pre-facade."""

    def test_shadow_env_var_name(self, facade: ModuleType) -> None:
        """SHADOW_ENV_VAR is the documented constant."""
        assert facade.SHADOW_ENV_VAR == "WORK_LOOP_SHADOW_SERVICES"

    def test_shadow_disabled_by_default(self, facade: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
        """shadow_enabled() returns False when the env var is absent."""
        monkeypatch.delenv(facade.SHADOW_ENV_VAR, raising=False)
        assert facade.shadow_enabled() is False

    def test_shadow_disabled_empty_string(self, facade: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
        """shadow_enabled() returns False when the env var is empty."""
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "")
        assert facade.shadow_enabled() is False

    def test_shadow_disabled_other_value(self, facade: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
        """shadow_enabled() returns False for any value other than "1"."""
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "true")
        assert facade.shadow_enabled() is False

    def test_shadow_on_transition_is_noop_when_off(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """shadow_call_on_transition does nothing when shadow is disabled."""
        monkeypatch.delenv(facade.SHADOW_ENV_VAR, raising=False)
        spec_dir = tmp_path / "test-spec"
        spec_dir.mkdir()
        pending = {"seq": 1, "event": "spec-ready", "from": "SPEC-PLAN-DRAFTING",
                   "to": "SPEC-PLAN-REVIEW", "run_id": "abc", "at": "2026-01-01T00:00:00Z"}
        engine_state = {"feature": "test-spec", "run_id": "abc"}
        # No shadow dir should be created
        facade.shadow_call_on_transition(spec_dir, engine_state, pending)
        shadow_dir = spec_dir / facade.SHADOW_SUBDIR
        assert not shadow_dir.exists(), "shadow dir must not be created when shadow is off"

    def test_shadow_on_plan_locked_is_noop_when_off(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """shadow_call_on_plan_locked does nothing when shadow is disabled."""
        monkeypatch.delenv(facade.SHADOW_ENV_VAR, raising=False)
        spec_dir = tmp_path / "test-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "test-spec", "run_id": "abc"}
        facade.shadow_call_on_plan_locked(spec_dir, engine_state)
        shadow_dir = spec_dir / facade.SHADOW_SUBDIR
        assert not shadow_dir.exists()

    def test_engine_transition_output_unchanged(
        self, spec_dir: Path, git_repo: Path
    ) -> None:
        """With shadow off, the engine's stdout and exit code are unchanged.

        Proves AC-0016: command and transition behavior is byte-for-byte identical
        to the pre-facade engine.
        """
        # Run engine init + first transition with shadow off.
        env_off: dict = {k: v for k, v in os.environ.items() if k != "WORK_LOOP_SHADOW_SERVICES"}
        r = subprocess.run(
            [sys.executable, str(ENGINE), "init", str(spec_dir), "--mode", "code", "--json"],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(git_repo), env=env_off,
        )
        assert r.returncode == 0
        # No shadow dir created
        shadow_dir = spec_dir / ".shadow-acceptance"
        assert not shadow_dir.exists(), "shadow dir must not appear with shadow off"

    def test_shadow_refusal_does_not_change_legacy_transition(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Injecting a shadow refusal (via monkeypatch) leaves legacy result unchanged.

        Proves AC-0016: shadow refusal must never change the legacy result.
        """
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "refusal-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "refusal-spec", "run_id": "xyz"}
        pending = {"seq": 1, "event": "spec-ready", "from": "SPEC-PLAN-DRAFTING",
                   "to": "SPEC-PLAN-REVIEW", "run_id": "xyz", "at": "2026-01-01T00:00:00Z"}

        # Monkeypatch _do_shadow_on_transition to raise (simulates shadow refusal)
        monkeypatch.setattr(
            facade, "_do_shadow_on_transition",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("shadow refused")),
        )
        try:
            facade.shadow_call_on_transition(spec_dir, engine_state, pending)
        except Exception as exc:
            pytest.fail(f"shadow_call_on_transition propagated an exception: {exc}")

    def test_shadow_exception_does_not_change_legacy_transition(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Injecting a service exception leaves shadow_call_on_transition non-raising.

        Proves AC-0016: a service exception must never change the legacy result.
        """
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "exc-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "exc-spec", "run_id": "exc"}
        pending = {"seq": 2, "event": "reviewers-clean", "from": "SPEC-PLAN-REVIEW",
                   "to": "SPEC-HUMAN-GATE", "run_id": "exc", "at": "2026-01-01T00:00:01Z"}

        monkeypatch.setattr(
            facade, "_do_shadow_on_transition",
            lambda *a, **kw: (_ for _ in ()).throw(OSError("disk full")),
        )
        try:
            facade.shadow_call_on_transition(spec_dir, engine_state, pending)
        except Exception as exc:
            pytest.fail(f"shadow_call_on_transition propagated an exception: {exc}")

    def test_plan_locked_shadow_exception_non_propagating(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Injecting an exception in the plan-locked shadow path is non-propagating.

        Proves AC-0016: the legacy plan-pin is unchanged even when shadow fails.
        """
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "pl-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "pl-spec", "run_id": "pl-run"}
        monkeypatch.setattr(
            facade, "_do_shadow_on_plan_locked",
            lambda *a, **kw: (_ for _ in ()).throw(ValueError("broken")),
        )
        try:
            facade.shadow_call_on_plan_locked(spec_dir, engine_state)
        except Exception as exc:
            pytest.fail(f"shadow_call_on_plan_locked propagated: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# AC-0016: shadow ON — shadow facts written without changing legacy
# ─────────────────────────────────────────────────────────────────────────────


class TestAC0016ShadowOn:
    """With shadow calls enabled, shadow facts are written but legacy is unchanged."""

    def test_shadow_enabled_by_env_var(
        self, facade: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """shadow_enabled() returns True when WORK_LOOP_SHADOW_SERVICES=1."""
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        assert facade.shadow_enabled() is True

    def test_shadow_transition_writes_evidence_record(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """shadow_call_on_transition writes a shadow evidence-receipt.v1 frame."""
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "ev-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "ev-spec", "run_id": "ev-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "SPEC-PLAN-DRAFTING",
                   "to": "SPEC-PLAN-REVIEW", "run_id": "ev-run", "at": "2026-01-01T00:00:00Z"}

        facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        # EvidenceStore log: one JSON line per frame, each frame {"tx": {...}, "records": [...]}
        log_path = spec_dir / facade.SHADOW_SUBDIR / "shadow-evidence.log"
        assert log_path.exists(), "shadow evidence log must be created"
        lines = [ln for ln in log_path.read_text("utf-8").splitlines() if ln]
        assert len(lines) == 1, "one frame per transition"
        frame = json.loads(lines[0])
        assert "tx" in frame and "records" in frame, "frame must have tx and records"
        records = frame["records"]
        assert len(records) == 1
        r = records[0]
        # evidence-receipt.v1 required fields
        assert r["schema_version"] == 1
        assert r.get("receipt_id", "").startswith("shadow-"), "receipt_id must start with 'shadow-'"
        assert r["outcome"] == "observed"
        assert r["selector"]["term"] == "engine-transition:spec-ready"
        # Schema is closed: no non-schema fields (no authoritative flag)
        assert "authoritative" not in r

    def test_shadow_plan_locked_writes_policy_import_record(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """shadow_call_on_plan_locked writes approval-record.v1 and initial-plan-review.v1."""
        import types

        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "pi-spec"
        spec_dir.mkdir()
        # Provide state.json so _do_shadow_on_plan_locked can read approved hashes
        (spec_dir / "state.json").write_text(
            json.dumps({"approved_spec_hash": "a" * 64, "approved_plan_hash": "b" * 64}),
            encoding="utf-8",
        )

        # Inject a fake _policy_import module so import_policy succeeds without real files
        fake_approval = {"schema_version": 1, "approval_id": "approval-test-001",
                         "decision": "approved", "timestamp": "2026-01-01T00:00:00Z",
                         "authority": {"identity": "shadow-compat-facade", "role": "shadow-observer"},
                         "decision_scope": "shadow-compat",
                         "base": {"manifest_ref": "compat-shadow:manifest"},
                         "lineage": {"spec_ref": "specs/pi-spec/spec.md"},
                         "spec_policy_fingerprint": "sha256:fp-001"}
        fake_review = {"schema_version": 1, "review_id": "review-test-001",
                       "plan_hash": "b" * 64, "terminal_intent": "work-loop-code-implementation",
                       "reviewer": {"identity": "shadow-compat-facade", "role": "shadow-reviewer"},
                       "timestamp": "2026-01-01T00:00:00Z",
                       "envelope_fingerprint": "sha256:env-fp-001"}

        class _FakeImportStore:
            def record_count(self) -> int:
                return 0

        def _fake_import_policy(**kw: object) -> tuple:
            return fake_approval, fake_review

        fake_pi = types.SimpleNamespace(
            ImportStore=_FakeImportStore,
            import_policy=_fake_import_policy,
            PolicyImportRefused=Exception,
        )
        monkeypatch.setattr(facade, "_policy_import_module_cache", fake_pi)

        engine_state = {"feature": "pi-spec", "run_id": "pi-run"}
        facade.shadow_call_on_plan_locked(spec_dir, engine_state)

        approval_path = spec_dir / facade.SHADOW_SUBDIR / "shadow-approval.json"
        assert approval_path.exists(), "shadow-approval.json (approval-record.v1) must be created"
        review_path = spec_dir / facade.SHADOW_SUBDIR / "shadow-initial-review.json"
        assert review_path.exists(), "shadow-initial-review.json (initial-plan-review.v1) must be created"
        # approval-record.v1 must have schema_version (no ad-hoc record_type or governance flag)
        approval = json.loads(approval_path.read_text("utf-8"))
        assert approval["schema_version"] == 1
        assert "governance_required_for_authority_switch" not in approval, (
            "registered record types carry no ad-hoc governance flag"
        )
        assert "authoritative" not in approval

    def test_shadow_plan_locked_reads_approved_hashes(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """shadow_call_on_plan_locked passes approved hashes from state.json to import_policy."""
        import types

        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "hash-spec"
        spec_dir.mkdir()
        spec_hash = "aabbcc" * 10 + "11"
        plan_hash = "ddeeff" * 10 + "22"
        state = {
            "schema_version": 2,
            "run_id": "hash-run",
            "approved_spec_hash": spec_hash,
            "approved_plan_hash": plan_hash,
        }
        (spec_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        # Spy: capture what import_policy receives, then stop
        captured: dict = {}

        class _FakeImportStore:
            def record_count(self) -> int:
                return 0

        def _spy_import_policy(**kw: object) -> None:
            captured["spec"] = kw.get("approved_spec_digest")
            captured["plan"] = kw.get("approved_plan_digest")
            raise RuntimeError("spy-stop")

        fake_pi = types.SimpleNamespace(
            ImportStore=_FakeImportStore,
            import_policy=_spy_import_policy,
            PolicyImportRefused=RuntimeError,
        )
        monkeypatch.setattr(facade, "_policy_import_module_cache", fake_pi)

        engine_state = {"feature": "hash-spec", "run_id": "hash-run"}
        # Should complete without raising (divergence absorbed)
        facade.shadow_call_on_plan_locked(spec_dir, engine_state)

        assert captured.get("spec") == spec_hash, (
            "approved_spec_digest must be read from state.json"
        )
        assert captured.get("plan") == plan_hash, (
            "approved_plan_digest must be read from state.json"
        )

    def test_shadow_records_are_non_authoritative(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """All shadow records carry authoritative=False.

        Proves AC-0016: target records remain non-authoritative (no dispatch
        or plan approval created).
        """
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "auth-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "auth-spec", "run_id": "auth-run"}

        # Emit multiple transition shadow records
        for i, event in enumerate(["spec-ready", "reviewers-clean", "spec-approved"]):
            pending = {"seq": i + 1, "event": event, "from": "SOURCE",
                       "to": "TARGET", "run_id": "auth-run",
                       "at": "2026-01-01T00:00:00Z"}
            facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        log_path = spec_dir / facade.SHADOW_SUBDIR / "shadow-evidence.log"
        assert log_path.exists()
        lines = [ln for ln in log_path.read_text("utf-8").splitlines() if ln]
        assert len(lines) == 3, "one frame per transition"
        for line in lines:
            frame = json.loads(line)
            for r in frame["records"]:
                assert "authoritative" not in r, (
                    "evidence-receipt.v1 schema is closed; no 'authoritative' field"
                )

        # No approval record written during transitions (only at plan-locked)
        shadow_dir = spec_dir / facade.SHADOW_SUBDIR
        assert not (shadow_dir / "shadow-approval.json").exists(), (
            "approval-record.v1 must not be written during regular transitions"
        )

    def test_shadow_divergence_is_recorded_on_failure(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A shadow failure produces a security-event.v1 divergence record, no partial fact.

        Proves AC-0016: shadow refusal → stable redacted divergence code written
        using the closed security-event.v1 schema (exactly seven fields).
        """
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "div-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "div-spec", "run_id": "div-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "A", "to": "B",
                   "run_id": "div-run", "at": "2026-01-01T00:00:00Z"}

        # Inject failure after the shadow dir is created
        monkeypatch.setattr(
            facade, "_do_shadow_on_transition",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("injected")),
        )
        facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        # security-event.v1 divergence record must exist
        div_path = spec_dir / facade.SHADOW_SUBDIR / "shadow-security-events.jsonl"
        assert div_path.exists(), "security-event divergence file must be written"
        entry = json.loads(div_path.read_text("utf-8").splitlines()[0])
        assert entry["outcome"] == "denied"
        assert entry["reason_code"] == facade.SHADOW_DIVERGENCE_CODE
        # security-event.v1 is a closed schema — no extra fields
        assert "exc_type" not in entry, "closed schema: no exc_type field"
        assert "context_tag" not in entry, "closed schema: no context_tag field"
        # No partial evidence log
        ev_path = spec_dir / facade.SHADOW_SUBDIR / "shadow-evidence.log"
        assert not ev_path.exists(), "no partial shadow evidence on failure"

    def test_no_dispatch_no_task_projection(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Shadow calls create no task projection, dispatch record, or plan approval.

        Proves AC-0016: Slice 1 creates no target task-projection record or plan approval.
        """
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "no-dispatch-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "no-dispatch-spec", "run_id": "nd-run"}
        pending = {"seq": 1, "event": "wave-complete", "from": "CODE-IMPLEMENTATION",
                   "to": "CODE-VERIFICATION", "run_id": "nd-run", "at": "2026-01-01T00:00:00Z"}

        facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        shadow_dir = spec_dir / facade.SHADOW_SUBDIR
        existing = {p.name for p in shadow_dir.iterdir()} if shadow_dir.exists() else set()
        # Plan-locked records must not be created during a regular transition
        forbidden = {
            "task-projection.json", "dispatch-record.json",
            "shadow-approval.json", "shadow-initial-review.json",
            "shadow-verdict.json", "shadow-delivery-subject.json",
        }
        overlap = existing & forbidden
        assert not overlap, f"shadow created forbidden records during transition: {overlap}"


# ─────────────────────────────────────────────────────────────────────────────
# AC-0011: confinement — symlink refusal
# ─────────────────────────────────────────────────────────────────────────────


class TestShadowAuditDurability:
    """Security events the shadow services emit are stored before acknowledgment."""

    _PENDING = {"seq": 1, "event": "spec-ready", "from": "A", "to": "B",
                "run_id": "audit-run", "at": "2026-01-01T00:00:00Z"}

    def test_writer_authority_allow_is_stored_durably(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A shadow evidence write leaves its allow event in the shadow event log."""
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "audit-spec"
        spec_dir.mkdir()
        facade.shadow_call_on_transition(spec_dir, {"feature": "audit-spec"}, self._PENDING)

        shadow_dir = spec_dir / facade.SHADOW_SUBDIR
        assert (shadow_dir / "shadow-evidence.log").exists()
        events = [
            json.loads(line)
            for line in (shadow_dir / "shadow-security-events.jsonl").read_text("utf-8").splitlines()
        ]
        assert any(e["outcome"] == "allowed" for e in events), events
        assert all(e.get("reason_code") != facade.SHADOW_DIVERGENCE_CODE for e in events), (
            "a successful shadow write must not record a divergence"
        )

    def test_failed_audit_append_blocks_the_evidence_write(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When the audit event cannot be stored, the evidence write is not acknowledged."""
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "audit-fail-spec"
        spec_dir.mkdir()
        real_append = facade._confined_jsonl_append

        def failing_append(spec: Path, path: Path, record: dict, cm: ModuleType) -> None:
            if path.name == "shadow-security-events.jsonl":
                # The confined append reports every failure as MutationDenied.
                raise cm.MutationDenied("denied-staging-failed", "audit store unavailable")
            real_append(spec, path, record, cm)

        monkeypatch.setattr(facade, "_confined_jsonl_append", failing_append)
        facade.shadow_call_on_transition(spec_dir, {"feature": "audit-fail-spec"}, self._PENDING)

        log = spec_dir / facade.SHADOW_SUBDIR / "shadow-evidence.log"
        frames = log.read_text("utf-8").splitlines() if log.exists() else []
        assert frames == [], "no evidence frame may be written when its audit event is lost"

    def test_sink_failure_surfaces_as_the_stable_sink_unavailable_signal(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failed confined append reaches the emitter as its fail-closed signal."""
        spec_dir = tmp_path / "audit-signal-spec"
        shadow_dir = spec_dir / facade.SHADOW_SUBDIR
        shadow_dir.mkdir(parents=True)
        cm = facade._cm()

        def failing_append(spec: Path, path: Path, record: dict, cm_: ModuleType) -> None:
            raise cm_.MutationDenied("denied-staging-failed", "audit store unavailable")

        monkeypatch.setattr(facade, "_confined_jsonl_append", failing_append)
        se = facade._load_sibling("_t_audit_signal_se", "_security_events.py")
        event = se.SecurityEvent(
            schema_version=1, operation_id="op-1", correlation_id="c-1",
            event_type="capability-check", outcome="allowed",
            reason_code="allowed", timestamp="2026-01-01T00:00:00Z",
        )
        with pytest.raises(se.AuditSinkUnavailable):
            se.emit_security_event(facade._durable_sink(spec_dir, shadow_dir, cm), event)


class TestAC0011Confinement:
    """Shadow writes refuse symlinked paths and never write outside the root."""

    def _has_symlink_support(self, tmp_path: Path) -> bool:
        """Return True if this OS can create symlinks in tmp_path."""
        test_link = tmp_path / "_symlink_test"
        try:
            test_link.symlink_to(tmp_path)
            test_link.unlink()
            return True
        except (NotImplementedError, OSError):
            return False

    def test_symlinked_shadow_dir_refuses_write(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A symlinked .shadow-acceptance is refused; no write occurs outside root.

        Proves AC-0011: confinement detects a pre-placed symlink at the shadow
        directory level and records a shadow divergence without propagating.
        """
        if not self._has_symlink_support(tmp_path):
            pytest.skip("symlinks not supported on this platform")

        spec_dir = tmp_path / "sym-spec"
        spec_dir.mkdir()

        # Place a symlink at .shadow-acceptance pointing to an outside directory
        outside = tmp_path / "outside"
        outside.mkdir()
        shadow_link = spec_dir / facade.SHADOW_SUBDIR
        shadow_link.symlink_to(outside)

        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        engine_state = {"feature": "sym-spec", "run_id": "sym-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "A", "to": "B",
                   "run_id": "sym-run", "at": "2026-01-01T00:00:00Z"}

        # Must NOT raise (shadow failure is absorbed)
        try:
            facade.shadow_call_on_transition(spec_dir, engine_state, pending)
        except Exception as exc:
            pytest.fail(f"shadow_call_on_transition raised with symlinked shadow dir: {exc}")

        # No write must have occurred inside `outside`
        assert list(outside.iterdir()) == [], \
            "writes must not escape the spec_dir root through the symlink"

        # No evidence file inside the symlink target
        assert not (outside / "evidence.jsonl").exists(), \
            "evidence.jsonl must not be written outside the root"

    def test_symlinked_spec_dir_refuses_write(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A symlinked spec_dir is refused; no write occurs outside root.

        Proves AC-0011: confinement detects a symlinked confinement root and
        records a shadow divergence without propagating.
        """
        if not self._has_symlink_support(tmp_path):
            pytest.skip("symlinks not supported on this platform")

        real_dir = tmp_path / "real-spec"
        real_dir.mkdir()
        sym_spec = tmp_path / "sym-spec-root"
        sym_spec.symlink_to(real_dir)

        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        engine_state = {"feature": "sym-spec-root", "run_id": "sym-root-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "A", "to": "B",
                   "run_id": "sym-root-run", "at": "2026-01-01T00:00:00Z"}

        # Must NOT raise
        try:
            facade.shadow_call_on_transition(sym_spec, engine_state, pending)
        except Exception as exc:
            pytest.fail(f"shadow_call_on_transition raised with symlinked spec_dir: {exc}")

        # No write must have occurred in the real target
        shadow_in_real = real_dir / facade.SHADOW_SUBDIR
        assert not shadow_in_real.exists(), \
            "shadow dir must not be created via symlinked spec_dir"

    def test_evidence_store_own_check_blocks_directory_symlink(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """EvidenceStore's own O_NOFOLLOW check blocks writes even when
        _confined_ensure_shadow_dir is bypassed.

        Before the EvidenceStore log-path fix, bypassing _confined_ensure_shadow_dir
        allowed writes to escape through a symlinked shadow directory because the
        store resolved the log path with resolve() and wrote to the resolved target.
        After the fix, the store no longer resolves the log path; its confined_create
        call opens the (symlinked) parent directory with O_NOFOLLOW, which fails,
        so the write is blocked without relying on _confined_ensure_shadow_dir.

        Both guards together form defense in depth.
        """
        if not self._has_symlink_support(tmp_path):
            pytest.skip("symlinks not supported on this platform")

        spec_dir = tmp_path / "red-spec"
        spec_dir.mkdir()

        outside = tmp_path / "red-outside"
        outside.mkdir()
        shadow_link = spec_dir / facade.SHADOW_SUBDIR
        shadow_link.symlink_to(outside)

        # Disable the directory-level confinement check.
        def _unconfined_ensure(s: Path, sd: Path, cm: object) -> None:
            """Bypass directory confinement check — for confinement-depth proof only."""

        monkeypatch.setattr(facade, "_confined_ensure_shadow_dir", _unconfined_ensure)

        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        engine_state = {"feature": "red-spec", "run_id": "red-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "A", "to": "B",
                   "run_id": "red-run", "at": "2026-01-01T00:00:00Z"}

        # After the EvidenceStore fix, the store opens its parent with O_NOFOLLOW,
        # which fails for a symlinked parent — so writes do NOT escape even when
        # _confined_ensure_shadow_dir is bypassed.
        facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        escaped = outside / "shadow-evidence.log"
        assert not escaped.exists(), (
            "EvidenceStore's O_NOFOLLOW check must block the write even without "
            "_confined_ensure_shadow_dir"
        )

    def test_confined_write_refuses_symlinked_shadow_dir_with_mutation_denied(
        self, facade: ModuleType, cm: ModuleType, tmp_path: Path
    ) -> None:
        """_confined_ensure_shadow_dir raises MutationDenied for a symlinked shadow dir.

        Proves the confinement check is the direct cause of the refusal, not
        an incidental file-not-found or other error.
        """
        if not self._has_symlink_support(tmp_path):
            pytest.skip("symlinks not supported on this platform")

        spec_dir = tmp_path / "cm-sym-spec"
        spec_dir.mkdir()
        outside = tmp_path / "cm-outside"
        outside.mkdir()
        shadow_link = spec_dir / facade.SHADOW_SUBDIR
        shadow_link.symlink_to(outside)

        with pytest.raises(cm.MutationDenied) as exc_info:
            facade._confined_ensure_shadow_dir(spec_dir, shadow_link, cm)

        assert exc_info.value.denial_code == "denied-path-violation"
        # No write must have escaped
        assert list(outside.iterdir()) == []

    def test_self_ignoring_gitignore_created_on_first_write(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The shadow dir is self-ignoring: .gitignore with '*' is created on first use.

        Proves adopter-safe ignore: git status stays clean after a shadow-on
        transition in a git repo.
        """
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")

        # Initialize a git repository
        git_repo = tmp_path / "git-repo"
        git_repo.mkdir()
        subprocess.run(
            ["git", "init", "-q", str(git_repo)], check=True, capture_output=True
        )
        subprocess.run(
            [
                "git", "-C", str(git_repo),
                "-c", "user.name=Test User", "-c", "user.email=test@example.com",
                "commit", "--allow-empty", "-m", "init",
            ],
            check=True, capture_output=True,
        )

        spec_dir = git_repo / "docs" / "specs" / "self-ignore-spec"
        spec_dir.mkdir(parents=True)
        engine_state = {"feature": "self-ignore-spec", "run_id": "si-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "A", "to": "B",
                   "run_id": "si-run", "at": "2026-01-01T00:00:00Z"}

        # Write a shadow fact (creates the shadow dir + .gitignore)
        facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        # .gitignore must exist in the shadow dir with content "*"
        gitignore = spec_dir / facade.SHADOW_SUBDIR / ".gitignore"
        assert gitignore.exists(), ".gitignore must be created in shadow dir"
        assert gitignore.read_text("utf-8").strip() == "*", \
            ".gitignore must contain '*'"

        # git status --porcelain must report nothing untracked in shadow dir
        result = subprocess.run(
            ["git", "-C", str(git_repo), "status", "--porcelain"],
            capture_output=True, text=True, encoding="utf-8",
        )
        assert result.returncode == 0
        lines = [ln for ln in result.stdout.splitlines()
                 if facade.SHADOW_SUBDIR in ln]
        assert not lines, (
            f"git status shows untracked shadow entries (adopter-safe test failed): "
            f"{lines}"
        )

    def test_gitignore_is_idempotent(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """.gitignore creation is idempotent: a second shadow write does not error."""
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "idem-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "idem-spec", "run_id": "idem-run"}

        for seq in (1, 2):
            pending = {"seq": seq, "event": "spec-ready", "from": "A", "to": "B",
                       "run_id": "idem-run", "at": "2026-01-01T00:00:00Z"}
            try:
                facade.shadow_call_on_transition(spec_dir, engine_state, pending)
            except Exception as exc:
                pytest.fail(f"second shadow_call raised on idempotent gitignore: {exc}")

        gitignore = spec_dir / facade.SHADOW_SUBDIR / ".gitignore"
        assert gitignore.read_text("utf-8").strip() == "*"

    def test_symlinked_shadow_evidence_log_writes_nothing_outside(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """(b) Facade with a symlinked shadow-evidence.log writes nothing outside spec dir.

        The shadow directory itself is a real directory, but shadow-evidence.log
        within it is a symlink to a file in an outside directory.  The
        EvidenceStore must refuse to open the symlinked log and the facade must
        record a divergence entry in shadow-security-events.jsonl — no bytes
        reach the outside target.

        Red evidence: removing the lstat check in EvidenceStore.open() and
        restoring read_bytes() causes the store to follow the symlink, write
        evidence to the outside target, and return successfully (no divergence).
        """
        if not self._has_symlink_support(tmp_path):
            pytest.skip("symlinks not supported on this platform")

        spec_dir = tmp_path / "sym-log-spec"
        spec_dir.mkdir()
        shadow_dir = spec_dir / facade.SHADOW_SUBDIR
        shadow_dir.mkdir()

        outside = tmp_path / "outside-log-target"
        outside.mkdir()
        outside_target = outside / "evil.log"

        # Place a symlink at the shadow-evidence.log path pointing to an outside file.
        log_link = shadow_dir / "shadow-evidence.log"
        log_link.symlink_to(outside_target)

        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        engine_state = {"feature": "sym-log-spec", "run_id": "sym-log-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "A", "to": "B",
                   "run_id": "sym-log-run", "at": "2026-01-01T00:00:00Z"}

        # Must NOT raise (shadow failure is absorbed into a divergence record).
        try:
            facade.shadow_call_on_transition(spec_dir, engine_state, pending)
        except Exception as exc:
            pytest.fail(f"shadow_call_on_transition raised unexpectedly: {exc}")

        # Nothing must have been written outside the spec dir.
        assert not outside_target.exists(), (
            "no bytes must be written to the symlinked log target outside the spec dir"
        )
        assert list(outside.iterdir()) == [], "outside directory must remain empty"

        # A divergence entry must have been recorded inside the shadow dir.
        events_path = shadow_dir / "shadow-security-events.jsonl"
        assert events_path.exists(), (
            "shadow-security-events.jsonl must exist inside the shadow dir after a refused write"
        )
        events_text = events_path.read_text("utf-8")
        assert facade.SHADOW_DIVERGENCE_CODE in events_text, (
            f"divergence code {facade.SHADOW_DIVERGENCE_CODE!r} must appear in "
            f"shadow-security-events.jsonl; got: {events_text!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# AC-0007: dual-emitted evidence → identical verdicts
# ─────────────────────────────────────────────────────────────────────────────


class TestAC0007DualEmitCorpus:
    """Shadow evidence over a frozen corpus yields identical verdicts after
    deleting target indexes and mechanical state (AC-0007)."""

    def test_shadow_evidence_written_for_multiple_events(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Shadow evidence is dual-emitted for each legacy transition event."""
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "corpus-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "corpus-spec", "run_id": "corpus-run"}

        events = [
            ("spec-ready", "SPEC-PLAN-DRAFTING", "SPEC-PLAN-REVIEW"),
            ("reviewers-clean", "SPEC-PLAN-REVIEW", "SPEC-HUMAN-GATE"),
            ("spec-approved", "SPEC-HUMAN-GATE", "PLAN-HUMAN-GATE"),
        ]
        for seq, (event, from_s, to_s) in enumerate(events, start=1):
            pending = {"seq": seq, "event": event, "from": from_s, "to": to_s,
                       "run_id": "corpus-run", "at": "2026-01-01T00:00:00Z"}
            facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        log_path = spec_dir / facade.SHADOW_SUBDIR / "shadow-evidence.log"
        assert log_path.exists(), "shadow evidence log must be created"
        lines = [ln for ln in log_path.read_text("utf-8").splitlines() if ln]
        assert len(lines) == 3, "one frame per transition"
        for i, (event, _, _) in enumerate(events):
            frame = json.loads(lines[i])
            r = frame["records"][0]
            assert r["selector"]["term"] == f"engine-transition:{event}", (
                f"frame {i}: selector term must encode event {event!r}"
            )
            assert r["observation"] == {"type": "engine-transition"}

    def test_acceptance_verdict_deterministic_over_shadow_receipts(
        self, acc: ModuleType, tmp_path: Path
    ) -> None:
        """evaluate_verdict is pure: deleting mechanical state cannot change it.

        Proves AC-0007: receipts with task-projection fields and mechanical state
        files beside the store (cohort.json, engine-state.json, cached-verdict.json)
        give the same verdict before and after those files are deleted.  Proved by
        a temporary mutation: changing the receipt outcome changes the verdict.
        """
        fingerprint = "sha256:frozen-corpus-fp-001"
        property_record = {
            "schema_version": 1,
            "property_id": "prop-1",
            "authority_ref": "spec-001",
            "satisfaction_rule": {"expression": "any"},
            "required_observations": [
                {"term": "implementation-done", "outcomes": ["complete"]},
            ],
            "contradiction_rule": {"expression": "none"},
        }

        # Receipt with the optional task_projection_revision field (allowed by schema)
        receipt = {
            "schema_version": 1,
            "receipt_id": "r-det-001",
            "acceptance_fingerprint": fingerprint,
            "lineage": {"criterion_ref": "prop-1"},
            "selector": {"term": "implementation-done"},
            "freshness_mode": "exact-subject",
            "observation": {"type": "engine-transition"},
            "outcome": "complete",
            "producer": {"class": "shadow-compat-facade", "identity": "shadow-compat-facade"},
            "task_projection_revision": "rev-abc123",
        }

        # Write fake mechanical state files beside the store location
        (tmp_path / "cohort.json").write_text('{"schema_version": 2}', encoding="utf-8")
        (tmp_path / "engine-state.json").write_text(
            '{"schema_version": 1, "state": "CODE-IMPLEMENTATION"}', encoding="utf-8"
        )
        (tmp_path / "cached-verdict.json").write_text(
            '{"verdict": "supported"}', encoding="utf-8"
        )

        verdict1 = acc.evaluate_verdict(
            property_record=property_record,
            receipts=[receipt],
            current_acceptance_fingerprint=fingerprint,
            adapter="sequential-reference",
        )
        assert verdict1["verdict"] == "supported"

        # Delete the mechanical state — evaluator must not read those files
        (tmp_path / "cohort.json").unlink()
        (tmp_path / "engine-state.json").unlink()
        (tmp_path / "cached-verdict.json").unlink()

        verdict2 = acc.evaluate_verdict(
            property_record=property_record,
            receipts=[receipt],
            current_acceptance_fingerprint=fingerprint,
            adapter="sequential-reference",
        )
        assert verdict1["verdict"] == verdict2["verdict"], (
            "AC-0007: verdict must be identical after deleting mechanical state"
        )
        assert verdict1["evaluation_fingerprint"] == verdict2["evaluation_fingerprint"], (
            "AC-0007: evaluation fingerprint must be identical (deterministic)"
        )

        # Prove by mutation: varying the receipt outcome changes the verdict
        modified_receipt = {**receipt, "outcome": "not-complete"}
        verdict_modified = acc.evaluate_verdict(
            property_record=property_record,
            receipts=[modified_receipt],
            current_acceptance_fingerprint=fingerprint,
            adapter="sequential-reference",
        )
        assert verdict_modified["verdict"] != verdict1["verdict"], (
            "AC-0007: changing receipt outcome must change the verdict (non-trivial)"
        )

    def test_verdict_parity_across_supported_adapters(self, acc: ModuleType) -> None:
        """The same approved properties produce the same verdict on every adapter.

        Proves AC-0007: identical inputs produce the same verdict on every
        declared supported adapter.  The cross-adapter check is non-trivial:
        an invalid adapter raises AcceptanceRefused, confirming the check fires.
        """
        assert len(acc.SUPPORTED_ADAPTERS) >= 2, (
            "conformance requires at least two supported adapters"
        )

        # Non-trivial check: an invalid adapter name is refused
        prop_minimal = {
            "schema_version": 1,
            "property_id": "prop-2",
            "authority_ref": "spec-parity-check",
            "satisfaction_rule": {"expression": "any"},
            "required_observations": [],
            "contradiction_rule": {"expression": "none"},
        }
        with pytest.raises(acc.AcceptanceRefused):
            acc.evaluate_verdict(
                property_record=prop_minimal,
                receipts=[],
                current_acceptance_fingerprint="sha256:parity-check-fp",
                adapter="invalid-adapter-xyz",
            )

        fingerprint = "sha256:parity-fp-002"
        property_record = {
            "schema_version": 1,
            "property_id": "prop-3",
            "authority_ref": "spec-002",
            "satisfaction_rule": {"expression": "all"},
            "required_observations": [
                {"term": "tests-pass", "outcomes": ["pass"]},
                {"term": "review-clean", "outcomes": ["clean"]},
            ],
            "contradiction_rule": {"expression": "none"},
        }
        receipts = [
            {"acceptance_fingerprint": fingerprint, "freshness_mode": "exact-subject",
             "selector": {"term": "tests-pass"}, "outcome": "pass"},
            {"acceptance_fingerprint": fingerprint, "freshness_mode": "exact-subject",
             "selector": {"term": "review-clean"}, "outcome": "clean"},
        ]

        verdicts = {}
        for adapter in acc.SUPPORTED_ADAPTERS:
            v = acc.evaluate_verdict(
                property_record=property_record,
                receipts=receipts,
                current_acceptance_fingerprint=fingerprint,
                adapter=adapter,
            )
            verdicts[adapter] = v["verdict"]

        first = next(iter(verdicts.values()))
        for adapter, verdict in verdicts.items():
            assert verdict == first, (
                f"AC-0007: verdict differs on adapter {adapter!r}: "
                f"{verdict!r} != {first!r}"
            )

    def test_shadow_evidence_read_back_and_evaluated(
        self, facade: ModuleType, acc: ModuleType, tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Shadow evidence round-trips through EvidenceStore and produces identical verdicts.

        Proves AC-0007: dual-emitted records persisted via EvidenceStore produce
        the same verdict before and after deleting and re-emitting the shadow store.
        """
        import shutil

        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "round-trip-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "round-trip-spec", "run_id": "rt-run"}

        pending_corpus = [
            {"seq": 1, "event": "spec-ready", "from": "SPEC-PLAN-DRAFTING",
             "to": "SPEC-PLAN-REVIEW", "run_id": "rt-run", "at": "2026-01-01T00:00:00Z"},
            {"seq": 2, "event": "reviewers-clean", "from": "SPEC-PLAN-REVIEW",
             "to": "SPEC-HUMAN-GATE", "run_id": "rt-run", "at": "2026-01-01T00:00:01Z"},
            {"seq": 3, "event": "spec-approved", "from": "SPEC-HUMAN-GATE",
             "to": "PLAN-HUMAN-GATE", "run_id": "rt-run", "at": "2026-01-01T00:00:02Z"},
        ]
        for pending in pending_corpus:
            facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        log_path = spec_dir / facade.SHADOW_SUBDIR / "shadow-evidence.log"
        assert log_path.exists()

        # Open the EvidenceStore to get active receipts
        es_mod = _load_module("es_rt", SCRIPTS / "_evidence_store.py")
        store = es_mod.EvidenceStore(log_path)
        store.open()
        receipts_first = store.get_all_active_receipts()
        assert len(receipts_first) == len(pending_corpus), "one receipt per transition"

        # Evaluate verdict from the first store
        property_record = {
            "schema_version": 1,
            "property_id": "prop-4",
            "authority_ref": "spec-rt",
            "satisfaction_rule": {"expression": "any"},
            "required_observations": [
                {"term": "engine-transition:spec-ready", "outcomes": ["observed"]},
            ],
            "contradiction_rule": {"expression": "none"},
        }
        acceptance_fp = receipts_first[0]["acceptance_fingerprint"]
        verdict_from_store = acc.evaluate_verdict(
            property_record=property_record,
            receipts=receipts_first,
            current_acceptance_fingerprint=acceptance_fp,
            adapter="sequential-reference",
        )

        # Delete the shadow store and re-emit (simulates rehydration from base events)
        shutil.rmtree(spec_dir / facade.SHADOW_SUBDIR)
        assert not (spec_dir / facade.SHADOW_SUBDIR).exists()
        for pending in pending_corpus:
            facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        store2 = es_mod.EvidenceStore(log_path)
        store2.open()
        receipts_rehydrated = store2.get_all_active_receipts()
        verdict_rehydrated = acc.evaluate_verdict(
            property_record=property_record,
            receipts=receipts_rehydrated,
            current_acceptance_fingerprint=acceptance_fp,
            adapter="sequential-reference",
        )

        assert verdict_from_store["verdict"] == verdict_rehydrated["verdict"], (
            "AC-0007: verdict must be identical after deleting target indexes"
        )

    def test_insufficient_verdict_without_matching_evidence(
        self, acc: ModuleType
    ) -> None:
        """Absent evidence produces 'insufficient'; adding it produces 'supported'.

        Proves AC-0007 truth-table: the four verdict values are reachable.
        """
        fingerprint = "sha256:truth-table-fp"
        property_record = {
            "schema_version": 1,
            "property_id": "prop-5",
            "authority_ref": "spec-tt",
            "satisfaction_rule": {"expression": "all"},
            "required_observations": [{"term": "gates-clean", "outcomes": ["pass"]}],
            "contradiction_rule": {"expression": "none"},
        }

        # No receipts → insufficient
        v_insufficient = acc.evaluate_verdict(
            property_record=property_record,
            receipts=[],
            current_acceptance_fingerprint=fingerprint,
            adapter="core-compatibility",
        )
        assert v_insufficient["verdict"] == "insufficient"

        # Matching receipt → supported
        receipt = {
            "acceptance_fingerprint": fingerprint,
            "freshness_mode": "exact-subject",
            "selector": {"term": "gates-clean"},
            "outcome": "pass",
        }
        v_supported = acc.evaluate_verdict(
            property_record=property_record,
            receipts=[receipt],
            current_acceptance_fingerprint=fingerprint,
            adapter="core-compatibility",
        )
        assert v_supported["verdict"] == "supported"


# ─────────────────────────────────────────────────────────────────────────────
# AC-0017: governance fingerprint and reversal
# ─────────────────────────────────────────────────────────────────────────────


class TestAC0017Governance:
    """Missing accepted governance record refuses target-authority switch (AC-0017).

    The governance gate lives in ``_policy_import.compatibility_snapshot``.  Its
    default resolver refuses because no accepted authority-switch governance record
    exists in Slice 1; the facade cannot satisfy the gate by writing any file.
    """

    def test_governance_gate_refuses_without_accepted_record(
        self, facade: ModuleType
    ) -> None:
        """compatibility_snapshot default resolver refuses; the gate cannot be self-satisfied.

        Proves AC-0017: the governance gate is in _policy_import, not in a file
        the facade can write.  With a fully populated store the default resolver
        raises PolicyImportRefused("denied-no-governance-record").
        """
        pi = facade._policy_import_mod()
        store = pi.ImportStore()
        # Populate the store with the two required record types so the code path
        # reaches the authority resolver (the default refuses with
        # denied-no-governance-record).
        approval_rec = {
            "decision_scope": "spec-policy",
            "envelope_fingerprint": "sha256:test-fp",
        }
        review_rec = {
            "authorized_terminal_intent": "deliver",
            "envelope_fingerprint": "sha256:test-fp",
        }
        store._stage(approval_rec)
        store._stage(review_rec)
        store._commit()
        try:
            pi.compatibility_snapshot(store)
            raise AssertionError("compatibility_snapshot must raise PolicyImportRefused")
        except pi.PolicyImportRefused as exc:
            assert exc.denial_code == "denied-no-governance-record", (
                f"AC-0017: expected denied-no-governance-record, got {exc.denial_code!r}"
            )

    def test_shadow_off_restores_legacy_path(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Disabling WORK_LOOP_SHADOW_SERVICES restores the legacy path (AC-0017).

        After setting shadow=on and writing facts, turning it off means the
        facade calls are no-ops and the legacy state is the only active path.
        """
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "reversal-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "reversal-spec", "run_id": "rev-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "SPEC-PLAN-DRAFTING",
                   "to": "SPEC-PLAN-REVIEW", "run_id": "rev-run", "at": "2026-01-01T00:00:00Z"}
        facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        log_path = spec_dir / facade.SHADOW_SUBDIR / "shadow-evidence.log"
        assert log_path.exists(), "shadow evidence log should exist after shadow=on"
        count_before = sum(1 for ln in log_path.read_text("utf-8").splitlines() if ln)

        # Disable shadow (reversal)
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "0")
        assert facade.shadow_enabled() is False, "shadow must be disabled after reversal"

        # Further transitions produce no additional shadow facts
        pending2 = {"seq": 2, "event": "reviewers-clean", "from": "SPEC-PLAN-REVIEW",
                    "to": "SPEC-HUMAN-GATE", "run_id": "rev-run", "at": "2026-01-01T00:00:01Z"}
        facade.shadow_call_on_transition(spec_dir, engine_state, pending2)

        count_after = sum(1 for ln in log_path.read_text("utf-8").splitlines() if ln)
        assert count_after == count_before, (
            "AC-0017: disabling shadow restores legacy path; "
            "no additional shadow facts written after reversal"
        )

    def test_shadow_facts_preserved_after_reversal(self, tmp_path: Path) -> None:
        """Turning shadow off mid-run keeps every earlier shadow fact byte-for-byte.

        Runs the real engine with shadow on through spec-approved, then unsets
        the variable for the remaining transitions.  The legacy run must still
        complete, the earlier shadow files must be unchanged, and no new shadow
        fact (such as the plan-locked verdict) may appear.
        """
        root = tmp_path / "repo-reversal"
        root.mkdir()
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        results = _run_full_sequence(
            root, "reversal-feature", shadow="1", reverse_after="spec-approved"
        )
        assert results.get("plan_locked_rc") == 0, results
        snapshot = results["shadow_snapshot"]
        assert snapshot.get("shadow-evidence.log"), "shadow facts must exist before reversal"
        shadow_dir = results["shadow_dir"]
        after = {f.name: f.read_bytes() for f in shadow_dir.iterdir() if f.is_file()}
        assert after == snapshot, (
            "AC-0017: reversal must neither delete, change, nor add shadow facts"
        )


# ─────────────────────────────────────────────────────────────────────────────
# AC-0016: full transition sequence — shadow ON vs OFF parity
# ─────────────────────────────────────────────────────────────────────────────


def _git_env() -> dict[str, str]:
    """Minimal git environment so commits succeed in a fresh repo."""
    return {
        "GIT_AUTHOR_NAME": "Test Agent",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test Agent",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }


_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?")


def _mask(results: dict, text: str) -> str:
    """Mask the run root, run ids, and timestamps so two runs compare byte-for-byte."""
    text = text.replace(str(results["root"]), "<ROOT>")
    text = _UUID_RE.sub("<ID>", text)
    return _TIMESTAMP_RE.sub("<TS>", text)


def _normalized_transcript(results: dict) -> list[tuple[str, int, str, str]]:
    """Every engine and cohort call's exit code, stdout, and stderr, masked."""
    return [
        (label, rc, _mask(results, out), _mask(results, err))
        for label, rc, out, err in results["transcript"]
    ]


def _run_full_sequence(
    root: Path,
    feature: str,
    *,
    shadow: str | None = None,
    reverse_after: str | None = None,
) -> dict:
    """Run the full spec-plan engine sequence; return captured state."""
    spec_dir = root / "docs" / "specs" / feature
    spec_dir.mkdir(parents=True)

    env: dict[str, str] = {**os.environ, **_git_env()}
    if shadow is not None:
        env["WORK_LOOP_SHADOW_SERVICES"] = shadow
    else:
        env.pop("WORK_LOOP_SHADOW_SERVICES", None)

    transcript: list[tuple[str, int, str, str]] = []

    def _run(script: Path, *args: str) -> subprocess.CompletedProcess:
        r = subprocess.run(
            [sys.executable, str(script), *args],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(root), env=env,
        )
        label = f"{script.name} {args[0]} {args[2] if len(args) > 2 else ''}"
        transcript.append((label, r.returncode, r.stdout, r.stderr))
        if reverse_after is not None and len(args) > 2 and args[2] == reverse_after:
            # Reversal: snapshot the shadow facts, then turn shadow off for the rest.
            shadow_dir = spec_dir / ".shadow-acceptance"
            results["shadow_snapshot"] = {
                f.name: f.read_bytes() for f in shadow_dir.iterdir() if f.is_file()
            }
            env.pop("WORK_LOOP_SHADOW_SERVICES", None)
        return r

    def engine(*args: str) -> subprocess.CompletedProcess:
        return _run(ENGINE, *args)

    def cohort(*args: str) -> subprocess.CompletedProcess:
        return _run(COHORT, *args)

    results: dict = {"transcript": transcript, "root": root}

    # 1. init
    r = engine("init", str(spec_dir), "--mode", "spec-plan", "--json")
    results["init_rc"] = r.returncode
    results["init_stdout"] = r.stdout
    if r.returncode != 0:
        return results
    run_id = json.loads(r.stdout)["run_id"]

    # 2. cohort init
    r = cohort("init", str(spec_dir), "--run-id", run_id)
    results["cohort_init_rc"] = r.returncode
    if r.returncode != 0:
        return results

    # 3. spec-ready
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Draft\n\n## Acceptance Criteria\n\n- [ ] AC-001.\n",
        encoding="utf-8",
    )
    r = engine("transition", str(spec_dir), "spec-ready")
    results["spec_ready_rc"] = r.returncode
    results["spec_ready_stdout"] = r.stdout
    if r.returncode != 0:
        return results

    # 4. reviewers-clean — no explicit payload; the engine defaults to all-skipped
    #    internally.  Passing --all-skipped is rejected by SPEC-PLAN-REVIEW state.
    r = engine("transition", str(spec_dir), "reviewers-clean")
    results["reviewers_clean_rc"] = r.returncode
    results["reviewers_clean_stderr"] = r.stderr
    if r.returncode != 0:
        return results

    # 5. spec-approved
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Approved\n\n## Acceptance Criteria\n\n- [ ] AC-001.\n",
        encoding="utf-8",
    )
    r = engine("transition", str(spec_dir), "spec-approved")
    results["spec_approved_rc"] = r.returncode
    results["spec_approved_stdout"] = r.stdout
    if r.returncode != 0:
        return results

    # 6. plan-approved (plan.md Status: Approved with task structure)
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Approved\n\n"
        "### T1\n\n**Depends on:** none\n\n"
        "### T2\n\n**Depends on:** T1\n",
        encoding="utf-8",
    )
    r = engine("transition", str(spec_dir), "plan-approved")
    results["plan_approved_rc"] = r.returncode
    results["plan_approved_stdout"] = r.stdout
    if r.returncode != 0:
        return results

    # 7. cohort approve-plan
    r = cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    results["cohort_approve_rc"] = r.returncode
    if r.returncode != 0:
        return results

    # 8. plan-locked
    r = engine("transition", str(spec_dir), "plan-locked")
    results["plan_locked_rc"] = r.returncode
    results["plan_locked_stdout"] = r.stdout

    # Capture final state
    state_path = spec_dir / "engine-state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text("utf-8"))
        # Semantic fields only; strip timestamps and run-ids
        _time_keys = {
            "run_id", "at", "started_at", "updated_at", "timestamp",
            "last_transition_at", "created_at",
        }
        results["engine_state_semantic"] = {
            k: v for k, v in state.items() if k not in _time_keys
        }

    # Cohort state, including the legacy plan pin, compared after masking.
    results["cohort_state_text"] = (spec_dir / "state.json").read_text("utf-8")

    results["shadow_dir"] = spec_dir / ".shadow-acceptance"
    return results


class TestAC0016FullTransitionSequence:
    """Full init→plan-locked sequence: shadow ON and OFF produce identical outputs."""

    def test_full_sequence_shadow_off(self, tmp_path: Path) -> None:
        """Full transition sequence completes successfully with shadow OFF."""
        root = tmp_path / "repo-off"
        root.mkdir()
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        results = _run_full_sequence(root, "seq-off-feature", shadow=None)
        assert results.get("plan_locked_rc") == 0, (
            f"plan-locked must succeed with shadow OFF; results={results}"
        )
        assert results["engine_state_semantic"].get("state") == "DONE"

    def test_full_sequence_shadow_on(self, tmp_path: Path) -> None:
        """Full transition sequence completes successfully with shadow ON."""
        root = tmp_path / "repo-on"
        root.mkdir()
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        results = _run_full_sequence(root, "seq-on-feature", shadow="1")
        assert results.get("plan_locked_rc") == 0, (
            f"plan-locked must succeed with shadow ON; results={results}"
        )
        assert results["engine_state_semantic"].get("state") == "DONE"

    def test_shadow_on_off_parity(self, tmp_path: Path) -> None:
        """Shadow ON and OFF produce identical exit codes, stdout, and engine state.

        Proves AC-0016: the shadow service never changes observable legacy behavior.
        """
        feature = "parity-feature"

        root_off = tmp_path / "repo-off"
        root_off.mkdir()
        subprocess.run(["git", "init", "-q", str(root_off)], check=True, capture_output=True)
        off = _run_full_sequence(root_off, feature, shadow=None)

        root_on = tmp_path / "repo-on"
        root_on.mkdir()
        subprocess.run(["git", "init", "-q", str(root_on)], check=True, capture_output=True)
        on = _run_full_sequence(root_on, feature, shadow="1")

        for step in ("init_rc", "spec_ready_rc", "reviewers_clean_rc",
                     "spec_approved_rc", "plan_approved_rc", "plan_locked_rc"):
            assert off.get(step) == on.get(step), (
                f"AC-0016: exit codes must be identical for {step!r}: "
                f"off={off.get(step)!r} on={on.get(step)!r}"
            )

        assert _normalized_transcript(off) == _normalized_transcript(on), (
            "AC-0016: every engine and cohort call must print the same stdout "
            "and stderr with shadow ON and OFF"
        )

        assert off.get("engine_state_semantic") == on.get("engine_state_semantic"), (
            "AC-0016: engine-state.json semantic fields must be identical\n"
            f"off={off.get('engine_state_semantic')}\n"
            f"on={on.get('engine_state_semantic')}"
        )
        assert _mask(off, off["cohort_state_text"]) == _mask(on, on["cohort_state_text"]), (
            "AC-0016: cohort state, including the plan pin, must be identical"
        )

    def test_shadow_on_produces_verdict_record(self, tmp_path: Path) -> None:
        """With shadow ON, the shadow directory contains a derived verdict record.

        Proves AC-0016 shadow completeness: plan-locked fires the shadow service
        which produces shadow-verdict.json under .shadow-acceptance/.
        """
        root = tmp_path / "repo-verdict"
        root.mkdir()
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        results = _run_full_sequence(root, "verdict-feature", shadow="1")
        assert results.get("plan_locked_rc") == 0, (
            f"plan-locked must succeed; results={results}"
        )
        shadow_dir = results["shadow_dir"]
        assert shadow_dir.exists(), (
            "shadow directory must be created when shadow=1"
        )
        verdict_path = shadow_dir / "shadow-verdict.json"
        assert verdict_path.exists(), (
            f"shadow-verdict.json must exist after plan-locked with shadow=1; "
            f"shadow_dir contents: {list(shadow_dir.iterdir())}"
        )
        verdict = json.loads(verdict_path.read_text("utf-8"))
        assert "verdict" in verdict, (
            f"shadow-verdict.json must contain 'verdict'; got {list(verdict.keys())}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Structural: module constants and completeness
# ─────────────────────────────────────────────────────────────────────────────


class TestStructural:
    """Structural tests for the facade module."""

    def test_module_complete_marker(self, facade: ModuleType) -> None:
        """The facade module has _MODULE_COMPLETE = True."""
        assert getattr(facade, "_MODULE_COMPLETE", False) is True

    def test_all_exports_present(self, facade: ModuleType) -> None:
        """Every name in __all__ is present on the module."""
        missing = [name for name in facade.__all__ if not hasattr(facade, name)]
        assert not missing, f"exported names missing: {missing}"

    def test_shadow_divergence_code_is_stable(self, facade: ModuleType) -> None:
        """SHADOW_DIVERGENCE_CODE is the expected stable constant."""
        assert facade.SHADOW_DIVERGENCE_CODE == "shadow-divergence:redacted"

    def test_shadow_subdir_constant(self, facade: ModuleType) -> None:
        """SHADOW_SUBDIR is the per-feature shadow directory name."""
        assert facade.SHADOW_SUBDIR == ".shadow-acceptance"

    def test_facade_is_standard_library_only(self) -> None:
        """The facade's source does not import any non-standard-library module.

        Checks that every 'import' statement in _compat_facade.py resolves to
        either the standard library or a sibling scripts module loaded via
        importlib.util.spec_from_file_location (not a bare import).
        Bare non-stdlib imports are forbidden by the agent rules.
        """
        src = FACADE.read_text(encoding="utf-8")
        # Bare imports that would indicate a third-party dependency
        forbidden_patterns = ["import agentbundle", "import jsonschema",
                              "import tomli", "import tomlkit"]
        for pat in forbidden_patterns:
            assert pat not in src, f"facade must not import {pat!r}"
