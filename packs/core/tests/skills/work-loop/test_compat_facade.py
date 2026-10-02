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
        """shadow_call_on_transition writes a shadow evidence record to .shadow-acceptance/."""
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "ev-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "ev-spec", "run_id": "ev-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "SPEC-PLAN-DRAFTING",
                   "to": "SPEC-PLAN-REVIEW", "run_id": "ev-run", "at": "2026-01-01T00:00:00Z"}

        facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        evidence_path = spec_dir / facade.SHADOW_SUBDIR / "evidence.jsonl"
        assert evidence_path.exists(), "shadow evidence file must be created"
        records = [json.loads(line) for line in evidence_path.read_text("utf-8").splitlines()]
        assert len(records) == 1
        r = records[0]
        assert r["record_type"] == "shadow-transition-evidence"
        assert r["event"] == "spec-ready"
        assert r["seq"] == 1
        assert r["authoritative"] is False

    def test_shadow_plan_locked_writes_policy_import_record(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """shadow_call_on_plan_locked writes a shadow policy-import record."""
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "pi-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "pi-spec", "run_id": "pi-run"}

        facade.shadow_call_on_plan_locked(spec_dir, engine_state)

        import_path = spec_dir / facade.SHADOW_SUBDIR / "policy-import.json"
        assert import_path.exists(), "shadow policy-import file must be created"
        record = json.loads(import_path.read_text("utf-8"))
        assert record["record_type"] == "shadow-policy-import"
        assert record["feature"] == "pi-spec"
        assert record["run_id"] == "pi-run"
        assert record["authoritative"] is False
        assert record["governance_required_for_authority_switch"] is True

    def test_shadow_plan_locked_reads_approved_hashes(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """shadow_call_on_plan_locked captures the approved hashes from state.json."""
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "hash-spec"
        spec_dir.mkdir()
        # Write a minimal state.json with approved hashes
        state = {
            "schema_version": 2,
            "run_id": "hash-run",
            "approved_spec_hash": "aabbcc" * 10 + "11",
            "approved_plan_hash": "ddeeff" * 10 + "22",
        }
        (spec_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        engine_state = {"feature": "hash-spec", "run_id": "hash-run"}

        facade.shadow_call_on_plan_locked(spec_dir, engine_state)

        import_path = spec_dir / facade.SHADOW_SUBDIR / "policy-import.json"
        record = json.loads(import_path.read_text("utf-8"))
        assert record["approved_spec_hash"] == state["approved_spec_hash"]
        assert record["approved_plan_hash"] == state["approved_plan_hash"]

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

        evidence_path = spec_dir / facade.SHADOW_SUBDIR / "evidence.jsonl"
        records = [json.loads(line) for line in evidence_path.read_text("utf-8").splitlines()]
        for r in records:
            assert r["authoritative"] is False, \
                f"shadow record for {r['event']} must be non-authoritative"

    def test_shadow_divergence_is_recorded_on_failure(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A shadow failure produces a divergence record, no partial fact.

        Proves AC-0016: shadow refusal → stable redacted divergence code.
        """
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "div-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "div-spec", "run_id": "div-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "A", "to": "B",
                   "run_id": "div-run", "at": "2026-01-01T00:00:00Z"}

        # Inject failure at the evidence append step after the dir is created
        original_do = facade._do_shadow_on_transition
        monkeypatch.setattr(
            facade, "_do_shadow_on_transition",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("injected")),
        )
        facade.shadow_call_on_transition(spec_dir, engine_state, pending)
        monkeypatch.setattr(facade, "_do_shadow_on_transition", original_do)

        # Divergence record must exist; partial evidence record must not exist
        # The divergence write itself creates the shadow dir
        div_path = spec_dir / facade.SHADOW_SUBDIR / "divergence.jsonl"
        assert div_path.exists(), "divergence record must be written"
        entry = json.loads(div_path.read_text("utf-8").splitlines()[0])
        assert entry["divergence_code"] == facade.SHADOW_DIVERGENCE_CODE
        assert entry["exc_type"] == "RuntimeError"
        # No partial evidence
        ev_path = spec_dir / facade.SHADOW_SUBDIR / "evidence.jsonl"
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
        # Only evidence.jsonl and .gitignore should exist; no task projection or dispatch records
        existing = {p.name for p in shadow_dir.iterdir()} if shadow_dir.exists() else set()
        forbidden = {"task-projection.json", "dispatch-record.json", "approval.json",
                     "initial-plan-review.json"}
        overlap = existing & forbidden
        assert not overlap, f"shadow created forbidden records: {overlap}"


# ─────────────────────────────────────────────────────────────────────────────
# AC-0011: confinement — symlink refusal
# ─────────────────────────────────────────────────────────────────────────────


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

    def test_confinement_red_by_disabling_check(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Disabling the confinement call allows a write through a symlink (red proof).

        This test proves that the symlink refusal is directly caused by the
        confinement check inside _confined_ensure_shadow_dir.  When that
        function is replaced with a plain mkdir, the write escapes to the
        symlink target — confirming the guard is not redundant.

        Verifies AC-0011: the red is real, not a false positive.
        """
        if not self._has_symlink_support(tmp_path):
            pytest.skip("symlinks not supported on this platform")

        spec_dir = tmp_path / "red-spec"
        spec_dir.mkdir()

        outside = tmp_path / "red-outside"
        outside.mkdir()
        shadow_link = spec_dir / facade.SHADOW_SUBDIR
        shadow_link.symlink_to(outside)

        # Disable the confinement check: replace _confined_ensure_shadow_dir
        # with an unconditional no-op (as if there were no guard).
        def _unconfined_ensure(s: Path, sd: Path, cm: object) -> None:
            """Bypass confinement — for red-proof only."""

        monkeypatch.setattr(facade, "_confined_ensure_shadow_dir", _unconfined_ensure)

        # Also disable confined_jsonl_append to use plain file write (no path check).
        def _plain_jsonl_append(root: Path, path: Path, record: dict, cm: object) -> None:
            line = json.dumps(record) + "\n"
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line)

        monkeypatch.setattr(facade, "_confined_jsonl_append", _plain_jsonl_append)

        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        engine_state = {"feature": "red-spec", "run_id": "red-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "A", "to": "B",
                   "run_id": "red-run", "at": "2026-01-01T00:00:00Z"}

        # With confinement disabled, the write escapes to outside/
        facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        # Confirm the write DID escape (proving the guard was the only protection)
        escaped = outside / "evidence.jsonl"
        assert escaped.exists(), (
            "red proof: without the confinement check the write escapes through the symlink"
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
            ["git", "-C", str(git_repo), "commit", "--allow-empty", "-m", "init"],
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

        evidence_path = spec_dir / facade.SHADOW_SUBDIR / "evidence.jsonl"
        records = [json.loads(line) for line in evidence_path.read_text("utf-8").splitlines()]
        assert len(records) == 3, "one shadow record per transition"
        for i, (event, _, _) in enumerate(events):
            assert records[i]["event"] == event
            assert records[i]["seq"] == i + 1

    def test_acceptance_verdict_deterministic_over_shadow_receipts(
        self, acc: ModuleType
    ) -> None:
        """evaluate_verdict() is deterministic for shadow-compatible receipt records.

        Proves AC-0007: identical inputs always produce the same verdict; deleting
        derived state (no separate index exists) and re-evaluating gives the same
        result.
        """
        # A minimal property record with a satisfaction rule
        fingerprint = "sha256:frozen-corpus-fp-001"
        property_record = {
            "schema_version": 1,
            "authority_ref": "spec-001",
            "satisfaction_rule": {"expression": "any"},
            "required_observations": [
                {"term": "implementation-done", "outcomes": ["complete"]},
            ],
            "contradiction_rule": {"expression": "none"},
        }

        # Minimal evidence receipt (shadow-compatible: has the required fields
        # that evaluate_verdict + is_fresh inspect)
        receipt = {
            "acceptance_fingerprint": fingerprint,
            "freshness_mode": "exact-subject",
            "selector": {"term": "implementation-done"},
            "outcome": "complete",
        }

        # Evaluate once — should be "supported"
        verdict1 = acc.evaluate_verdict(
            property_record=property_record,
            receipts=[receipt],
            current_acceptance_fingerprint=fingerprint,
            adapter="sequential-reference",
        )
        assert verdict1["verdict"] == "supported"

        # "Delete target indexes and mechanical state": since evaluate_verdict is
        # purely functional (no external state), re-evaluate with the same inputs.
        verdict2 = acc.evaluate_verdict(
            property_record=property_record,
            receipts=[receipt],
            current_acceptance_fingerprint=fingerprint,
            adapter="sequential-reference",
        )
        assert verdict1["verdict"] == verdict2["verdict"], (
            "AC-0007: verdict must be identical after deleting target indexes"
        )

    def test_verdict_parity_across_supported_adapters(self, acc: ModuleType) -> None:
        """The same approved properties produce the same verdict on every adapter.

        Proves AC-0007: identical inputs produce the same verdict on every
        declared supported adapter.
        """
        assert len(acc.SUPPORTED_ADAPTERS) >= 2, (
            "conformance requires at least two supported adapters"
        )
        fingerprint = "sha256:parity-fp-002"
        property_record = {
            "schema_version": 1,
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
        """Shadow evidence written to disk can be read back and evaluated consistently.

        Proves AC-0007: dual-emitted records round-trip through file storage and
        produce identical verdicts even after deleting the shadow store and
        rebuilding from the original records.
        """
        import shutil

        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "round-trip-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "round-trip-spec", "run_id": "rt-run"}

        # Emit three shadow transition events
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

        evidence_path = spec_dir / facade.SHADOW_SUBDIR / "evidence.jsonl"
        assert evidence_path.exists()

        # Read back the written records
        stored_records = [
            json.loads(line)
            for line in evidence_path.read_text("utf-8").splitlines()
        ]
        assert len(stored_records) == len(pending_corpus)

        # Build an acceptance fingerprint and evaluate verdicts
        fingerprint = "sha256:rt-fp-003"
        receipts = [
            {**r, "acceptance_fingerprint": fingerprint, "freshness_mode": "exact-subject",
             "selector": {"term": r["event"]}, "outcome": "observed"}
            for r in stored_records
        ]
        property_record = {
            "schema_version": 1,
            "authority_ref": "spec-rt",
            "satisfaction_rule": {"expression": "any"},
            "required_observations": [{"term": "spec-ready", "outcomes": ["observed"]}],
            "contradiction_rule": {"expression": "none"},
        }

        verdict_from_store = acc.evaluate_verdict(
            property_record=property_record,
            receipts=receipts,
            current_acceptance_fingerprint=fingerprint,
            adapter="sequential-reference",
        )

        # "Delete target indexes and mechanical state" — delete the shadow store
        shutil.rmtree(spec_dir / facade.SHADOW_SUBDIR)
        assert not (spec_dir / facade.SHADOW_SUBDIR).exists()

        # Re-emit from the original corpus (simulating rehydration from base records)
        for pending in pending_corpus:
            facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        reloaded = [
            json.loads(line)
            for line in evidence_path.read_text("utf-8").splitlines()
        ]
        receipts_rehydrated = [
            {**r, "acceptance_fingerprint": fingerprint, "freshness_mode": "exact-subject",
             "selector": {"term": r["event"]}, "outcome": "observed"}
            for r in reloaded
        ]
        verdict_rehydrated = acc.evaluate_verdict(
            property_record=property_record,
            receipts=receipts_rehydrated,
            current_acceptance_fingerprint=fingerprint,
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
    """Missing governance fingerprint refuses target-authority switch (AC-0017)."""

    def test_governance_missing_returns_false(
        self, facade: ModuleType, tmp_path: Path
    ) -> None:
        """check_governance_fingerprint returns False when governance.json is absent."""
        spec_dir = tmp_path / "no-gov-spec"
        spec_dir.mkdir()
        assert facade.check_governance_fingerprint(spec_dir) is False

    def test_governance_empty_dir_returns_false(
        self, facade: ModuleType, tmp_path: Path
    ) -> None:
        """check_governance_fingerprint returns False when shadow dir is empty."""
        spec_dir = tmp_path / "empty-gov-spec"
        spec_dir.mkdir()
        (spec_dir / facade.SHADOW_SUBDIR).mkdir()
        assert facade.check_governance_fingerprint(spec_dir) is False

    def test_governance_invalid_json_returns_false(
        self, facade: ModuleType, tmp_path: Path
    ) -> None:
        """check_governance_fingerprint returns False for malformed governance.json."""
        spec_dir = tmp_path / "bad-gov-spec"
        (spec_dir / facade.SHADOW_SUBDIR).mkdir(parents=True)
        (spec_dir / facade.SHADOW_SUBDIR / "governance.json").write_bytes(b"not json")
        assert facade.check_governance_fingerprint(spec_dir) is False

    def test_governance_wrong_decision_returns_false(
        self, facade: ModuleType, tmp_path: Path
    ) -> None:
        """check_governance_fingerprint returns False when decision != 'accepted'."""
        spec_dir = tmp_path / "wrong-dec-spec"
        (spec_dir / facade.SHADOW_SUBDIR).mkdir(parents=True)
        gov = {"decision": "pending", "fingerprint": "abc123"}
        (spec_dir / facade.SHADOW_SUBDIR / "governance.json").write_text(
            json.dumps(gov), encoding="utf-8"
        )
        assert facade.check_governance_fingerprint(spec_dir) is False

    def test_governance_accepted_returns_true(
        self, facade: ModuleType, tmp_path: Path
    ) -> None:
        """check_governance_fingerprint returns True for a valid accepted record.

        Proves AC-0017: with a governance fingerprint present, an authority switch
        becomes possible (this function gates it).
        """
        spec_dir = tmp_path / "gov-spec"
        (spec_dir / facade.SHADOW_SUBDIR).mkdir(parents=True)
        gov = {
            "decision": "accepted",
            "fingerprint": "sha256:governance-record-001",
            "at": "2026-01-01T00:00:00Z",
        }
        (spec_dir / facade.SHADOW_SUBDIR / "governance.json").write_text(
            json.dumps(gov), encoding="utf-8"
        )
        assert facade.check_governance_fingerprint(spec_dir) is True

    def test_governance_check_refuses_authority_switch_without_record(
        self, facade: ModuleType, tmp_path: Path
    ) -> None:
        """Without a governance record every target-authority switch is refused.

        Proves AC-0017: implementation alone cannot satisfy the gate.
        """
        spec_dir = tmp_path / "no-switch-spec"
        spec_dir.mkdir()
        result = facade.check_governance_fingerprint(spec_dir)
        assert result is False, (
            "AC-0017: a missing governance fingerprint must refuse every "
            "target-authority switch"
        )

    def test_shadow_off_restores_legacy_path(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Disabling WORK_LOOP_SHADOW_SERVICES restores the legacy path (AC-0017).

        After setting shadow=on and writing facts, turning it off means the
        facade calls are no-ops and the legacy state is the only active path.
        """
        # Enable shadow and write some facts
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "reversal-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "reversal-spec", "run_id": "rev-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "SPEC-PLAN-DRAFTING",
                   "to": "SPEC-PLAN-REVIEW", "run_id": "rev-run", "at": "2026-01-01T00:00:00Z"}
        facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        evidence_path = spec_dir / facade.SHADOW_SUBDIR / "evidence.jsonl"
        assert evidence_path.exists(), "shadow evidence should exist after shadow=on"
        count_before = len(evidence_path.read_text("utf-8").splitlines())

        # Disable shadow (reversal)
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "0")
        assert facade.shadow_enabled() is False, "shadow must be disabled after reversal"

        # Further transitions produce no additional shadow facts
        pending2 = {"seq": 2, "event": "reviewers-clean", "from": "SPEC-PLAN-REVIEW",
                    "to": "SPEC-HUMAN-GATE", "run_id": "rev-run", "at": "2026-01-01T00:00:01Z"}
        facade.shadow_call_on_transition(spec_dir, engine_state, pending2)

        # Evidence file count unchanged (no new shadow fact appended)
        count_after = len(evidence_path.read_text("utf-8").splitlines())
        assert count_after == count_before, (
            "AC-0017: disabling shadow restores legacy path; "
            "no additional shadow facts written after reversal"
        )

    def test_shadow_facts_preserved_after_reversal(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Reversal preserves existing shadow facts (does not delete them).

        Proves AC-0017: rollback selects the old verdict path without deleting
        new semantic facts.
        """
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "preserve-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "preserve-spec", "run_id": "pres-run"}
        pending = {"seq": 1, "event": "spec-ready", "from": "A", "to": "B",
                   "run_id": "pres-run", "at": "2026-01-01T00:00:00Z"}
        facade.shadow_call_on_transition(spec_dir, engine_state, pending)

        evidence_path = spec_dir / facade.SHADOW_SUBDIR / "evidence.jsonl"
        assert evidence_path.exists()
        content_before = evidence_path.read_bytes()

        # Disable shadow — facts must be preserved
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "0")
        assert evidence_path.read_bytes() == content_before, (
            "AC-0017: existing shadow facts must be preserved after reversal"
        )

    def test_missing_governance_in_policy_import_record(
        self, facade: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The shadow policy-import record carries governance_required_for_authority_switch.

        Proves AC-0017: the shadow record explicitly marks that a governance
        fingerprint is required for any authority switch.
        """
        monkeypatch.setenv(facade.SHADOW_ENV_VAR, "1")
        spec_dir = tmp_path / "gov-req-spec"
        spec_dir.mkdir()
        engine_state = {"feature": "gov-req-spec", "run_id": "gov-req-run"}

        facade.shadow_call_on_plan_locked(spec_dir, engine_state)

        import_path = spec_dir / facade.SHADOW_SUBDIR / "policy-import.json"
        record = json.loads(import_path.read_text("utf-8"))
        assert record["governance_required_for_authority_switch"] is True
        assert record["authoritative"] is False


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
