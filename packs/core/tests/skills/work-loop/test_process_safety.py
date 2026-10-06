"""T3b TDD suite: safe-process invariants across supported hosts.

Mode: TDD through operating-system integration tests (plan.md T3b).

Tests AC-0012 (identity pin, argv, cwd, environment, stdin, timeout, output
volume, encoding, child trees, redaction) and AC-0021 (durable audit event
before acknowledgment; sink-unavailable fail-closed).

Each fixture is self-contained and uses ``sys.executable`` as the test
process so no external binary is required.  The suite runs on any POSIX
host where ``os.killpg`` is available; process-group tests skip on hosts
that cannot supply the primitive.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import os
import signal
import stat
import subprocess
import sys
import threading
import time
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
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        # Register temporarily so Python 3.13 dataclasses._is_type can
        # resolve the module's __dict__ via sys.modules during exec_module.
        sys.modules[name] = mod
        try:
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
        finally:
            sys.modules.pop(name, None)
        return mod
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def process_safety() -> ModuleType:
    """_process_safety.py loaded by path, unregistered."""
    return _load_module("ps_under_test", SCRIPTS / "_process_safety.py")


# ── Executable identity ───────────────────────────────────────────────────────

# Resolve sys.executable so the test always uses a non-symlink regular file.
# _open_hash_executable opens with O_NOFOLLOW, so the spec must name a
# regular file (not a symlink).  Path.resolve() gives the canonical target.
PYTHON = str(Path(sys.executable).resolve())


def _sha256(path: str) -> str:
    """SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


PYTHON_HASH = _sha256(PYTHON)


# ── Spec builder ──────────────────────────────────────────────────────────────


def _spec(cwd: str, **kw) -> dict:
    """Return a minimal valid safe-process.v1 spec dict for the Python interpreter."""
    base: dict = {
        "schema_version": 1,
        "executable": PYTHON,
        "executable_identity": PYTHON_HASH,
        "argv": ["-c", "pass"],
        "grant_id": "test-grant-t3b",
        "cwd": cwd,
        "environment_allowlist": [],
        "stdin_mode": "closed",
        "process_tree_timeout_s": 10,
        "output_bound_bytes": 65536,
    }
    base.update(kw)
    return base


# ── Helpers ───────────────────────────────────────────────────────────────────


def _recording_sink():
    """Return (events_list, sink_callable) for audit-event assertions."""
    events: list = []
    return events, events.append


def _failing_sink(exc):
    """Return a sink callable that raises *exc* on every call."""
    def _sink(_event):
        raise exc
    return _sink


def _launch(ps, spec, *, cwd_roots=None, **kw):
    """Thin wrapper around ps.launch_safe_process that defaults cwd_roots.

    When cwd_roots is not supplied the spec's own cwd is used as the sole
    declared root, which is sufficient for tests that exercise paths other
    than the cwd-root confinement invariant.
    """
    if cwd_roots is None:
        cwd_roots = (spec["cwd"],)
    return ps.launch_safe_process(spec, cwd_roots=cwd_roots, **kw)


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0012: process spec validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestSpecValidation:
    """validate_process_spec_dict covers all schema-invalid inputs."""

    def test_valid_spec_returns_ok(self, process_safety: ModuleType, tmp_path) -> None:
        """A complete, conforming spec returns (True, 'ok')."""
        ps = process_safety
        ok, code = ps.validate_process_spec_dict(_spec(str(tmp_path)))
        assert ok and code == "ok"

    def test_rejects_unknown_schema_version(self, process_safety: ModuleType, tmp_path) -> None:
        """Schema version 99 is refused with 'denied-unknown-schema-version'."""
        ps = process_safety
        bad = _spec(str(tmp_path), schema_version=99)
        ok, code = ps.validate_process_spec_dict(bad)
        assert not ok and code == "denied-unknown-schema-version"

    def test_rejects_missing_required_field(self, process_safety: ModuleType, tmp_path) -> None:
        """A spec missing 'cwd' is refused with 'denied-missing-required-field'."""
        ps = process_safety
        bad = _spec(str(tmp_path))
        del bad["cwd"]
        ok, code = ps.validate_process_spec_dict(bad)
        assert not ok and code == "denied-missing-required-field"

    def test_rejects_unknown_authority_field(self, process_safety: ModuleType, tmp_path) -> None:
        """An extra authority-shaped field is refused with 'denied-unknown-authority-field'."""
        ps = process_safety
        bad = _spec(str(tmp_path))
        bad["inject_escalation"] = "admin"
        ok, code = ps.validate_process_spec_dict(bad)
        assert not ok and code == "denied-unknown-authority-field"

    def test_rejects_invalid_stdin_mode(self, process_safety: ModuleType, tmp_path) -> None:
        """A stdin_mode outside the declared enum is refused with 'denied-invalid-stdin-mode'."""
        ps = process_safety
        bad = _spec(str(tmp_path), stdin_mode="shell")
        ok, code = ps.validate_process_spec_dict(bad)
        assert not ok and code == "denied-invalid-stdin-mode"

    def test_rejects_relative_executable(self, process_safety: ModuleType, tmp_path) -> None:
        """A non-absolute executable path is refused."""
        ps = process_safety
        bad = _spec(str(tmp_path), executable="python")
        ok, code = ps.validate_process_spec_dict(bad)
        assert not ok and code == "denied-non-absolute-executable"

    def test_rejects_zero_timeout(self, process_safety: ModuleType, tmp_path) -> None:
        """process_tree_timeout_s = 0 is refused (minimum is 1)."""
        ps = process_safety
        bad = _spec(str(tmp_path), process_tree_timeout_s=0)
        ok, code = ps.validate_process_spec_dict(bad)
        assert not ok and code == "denied-invalid-timeout"

    def test_rejects_negative_output_bound(self, process_safety: ModuleType, tmp_path) -> None:
        """output_bound_bytes = -1 is refused (minimum is 0)."""
        ps = process_safety
        bad = _spec(str(tmp_path), output_bound_bytes=-1)
        ok, code = ps.validate_process_spec_dict(bad)
        assert not ok and code == "denied-invalid-output-bound"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0021: audit sink unavailable → fail closed
# ═══════════════════════════════════════════════════════════════════════════════


class TestAuditSinkUnavailable:
    """AC-0021 fail-closed behaviour when the audit sink is absent or raises."""

    def test_none_sink_refuses_launch(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """audit_sink=None refuses with 'denied-audit-sink-unavailable'."""
        ps = process_safety
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, _spec(str(tmp_path)), audit_sink=None)
        assert exc_info.value.denial_code == "denied-audit-sink-unavailable"

    def test_raising_sink_refuses_launch_on_allow_event(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A sink that raises before the allow event is emitted → fail closed.

        Uses the AuditSinkError class from the same _security_events module
        instance that _process_safety loaded internally (stored as ``_se``),
        so the ``except AuditSinkError`` inside emit_security_event matches.
        """
        ps = process_safety
        # ps._se is the _security_events module instance loaded by _process_safety.
        bad_sink = _failing_sink(ps._se.AuditSinkError("injected failure"))
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, _spec(str(tmp_path)), audit_sink=bad_sink)
        assert exc_info.value.denial_code == "denied-audit-sink-unavailable"

    @pytest.mark.parametrize(
        "failure",
        [RuntimeError("boom /private/secret"), OSError("disk /private/secret-path full")],
    )
    def test_any_sink_failure_refuses_with_redacted_stable_code(
        self, process_safety: ModuleType, tmp_path, failure: Exception
    ) -> None:
        """Every sink failure on the allow path gives the stable code and no sink text."""
        ps = process_safety
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, _spec(str(tmp_path)), audit_sink=_failing_sink(failure))
        assert exc_info.value.denial_code == "denied-audit-sink-unavailable"
        assert "/private" not in str(exc_info.value)

    def test_credential_shaped_correlation_id_never_reaches_the_sink(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A denial carrying a credential-shaped correlation ID is audited redacted."""
        ps = process_safety
        events, sink = _recording_sink()
        outside = tmp_path / "outside"
        outside.mkdir()
        with pytest.raises(ps.ProcessDenied):
            _launch(
                ps, _spec(str(outside)), cwd_roots=(str(tmp_path / "root"),),
                audit_sink=sink, correlation_id="AKIAIOSFODNN7EXAMPLE",
            )
        assert events, "the denial must still be audited"
        assert all("AKIAIOSFODNN7EXAMPLE" not in repr(e) for e in events), events
        assert {e.correlation_id for e in events} == {"redacted"}

    def test_none_sink_leaves_no_output(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """No ProcessResult is produced when the sink is unavailable."""
        ps = process_safety
        result = None
        with contextlib.suppress(ps.ProcessDenied):
            result = _launch(ps, _spec(str(tmp_path)), audit_sink=None)
        assert result is None, "no ProcessResult must escape when sink is unavailable"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0021: event emitted before acknowledgment
# ═══════════════════════════════════════════════════════════════════════════════


class TestAuditEventOrder:
    """AC-0021: event reaches the sink before ProcessResult or ProcessDenied returns."""

    def test_allow_event_emitted_for_successful_launch(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """An allow event with outcome='allowed' appears in the sink."""
        ps = process_safety
        events, sink = _recording_sink()
        result = _launch(ps, _spec(str(tmp_path)), audit_sink=sink)
        assert isinstance(result, ps.ProcessResult)
        assert len(events) == 1
        ev = events[0]
        assert ev.outcome == "allowed"
        assert ev.event_type == "process-launch"

    def test_denial_event_emitted_for_identity_mismatch(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A denial event appears in the sink before ProcessDenied is raised."""
        ps = process_safety
        events, sink = _recording_sink()
        bad = _spec(str(tmp_path), executable_identity="a" * 64)  # wrong hash
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, bad, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-identity-mismatch"
        assert len(events) == 1
        ev = events[0]
        assert ev.outcome == "denied"
        assert ev.event_type == "process-launch"

    def test_denial_event_emitted_for_invalid_spec(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A denial event is emitted even when the spec itself is invalid."""
        ps = process_safety
        events, sink = _recording_sink()
        bad = _spec(str(tmp_path), schema_version=99)
        with pytest.raises(ps.ProcessDenied):
            _launch(ps, bad, audit_sink=sink)
        # Denial event must appear in the sink.
        assert len(events) == 1
        assert events[0].outcome == "denied"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0012: successful launch — identity, argv, exit code
# ═══════════════════════════════════════════════════════════════════════════════


class TestSuccessfulLaunch:
    """Happy-path process launch invariants."""

    def test_exit_zero_returned(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A process that exits 0 produces exit_code=0 in ProcessResult."""
        ps = process_safety
        events, sink = _recording_sink()
        result = _launch(
            ps,
            _spec(str(tmp_path), argv=["-c", "import sys; sys.exit(0)"]),
            audit_sink=sink,
        )
        assert result.exit_code == 0

    def test_exit_nonzero_returned(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A process that exits 1 produces exit_code=1 in ProcessResult."""
        ps = process_safety
        _, sink = _recording_sink()
        result = _launch(
            ps,
            _spec(str(tmp_path), argv=["-c", "import sys; sys.exit(1)"]),
            audit_sink=sink,
        )
        assert result.exit_code == 1

    def test_argv_is_fixed_list(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """The argv is passed as a list, not a shell string, so shell metacharacters
        do not expand."""
        ps = process_safety
        _, sink = _recording_sink()
        # A semicolon in argv should be passed literally, not as a shell separator.
        result = _launch(
            ps,
            _spec(str(tmp_path), argv=["-c", "print('hello; world')"]),
            audit_sink=sink,
        )
        assert result.exit_code == 0
        assert b"hello; world" in result.stdout_redacted


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0012: executable identity
# ═══════════════════════════════════════════════════════════════════════════════


class TestExecutableIdentity:
    """Identity-pin checks refuse on mismatch and accept on match."""

    def test_identity_mismatch_refuses(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """Wrong executable_identity pin → denied-identity-mismatch."""
        ps = process_safety
        _, sink = _recording_sink()
        bad = _spec(str(tmp_path), executable_identity="0" * 64)
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, bad, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-identity-mismatch"

    def test_correct_identity_allows(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """Correct executable_identity pin allows launch."""
        ps = process_safety
        _, sink = _recording_sink()
        result = _launch(ps, _spec(str(tmp_path)), audit_sink=sink)
        assert isinstance(result, ps.ProcessResult)


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0012: confined working directory
# ═══════════════════════════════════════════════════════════════════════════════


class TestWorkingDirectory:
    """CWD validation."""

    def test_nonexistent_cwd_refuses(
        self, process_safety: ModuleType, tmp_path  # noqa: ARG002
    ) -> None:
        """A cwd that does not exist → denied-cwd-not-found."""
        ps = process_safety
        _, sink = _recording_sink()
        bad = _spec("/nonexistent-dir-t3b-xyz-123456")
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, bad, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-cwd-not-found"

    def test_valid_cwd_is_respected(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A valid cwd is set for the child process."""
        ps = process_safety
        _, sink = _recording_sink()
        # Ask Python to print its cwd; it must match tmp_path.
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", "import os; print(os.getcwd())"],
            ),
            audit_sink=sink,
        )
        assert result.exit_code == 0
        cwd_out = result.stdout_redacted.strip()
        # On macOS, /tmp is a symlink to /private/tmp; resolve both.
        assert Path(cwd_out.decode()).resolve() == Path(str(tmp_path)).resolve()


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0012: environment isolation
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnvironmentIsolation:
    """Only allowlisted environment variable names reach the child process."""

    def test_no_ambient_env_without_allowlist(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """Empty allowlist → no user-controlled vars reach the child; PATH is absent.

        macOS injects ``__CF_USER_TEXT_ENCODING`` and ``LC_CTYPE`` into every
        subprocess even when ``env={}`` is passed to ``Popen``; those are
        OS-level platform artefacts, not ambient user-environment inheritance.
        The contract is that no user-controlled data leaks, not that the dict
        is empty.
        """
        ps = process_safety
        _, sink = _recording_sink()
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", "import os, json; print(json.dumps(dict(os.environ)))"],
                environment_allowlist=[],
            ),
            audit_sink=sink,
        )
        assert result.exit_code == 0
        import json
        child_env = json.loads(result.stdout_redacted.decode())
        # PATH must not be inherited; it is always present in the test runner's env.
        assert "PATH" not in child_env, (
            f"PATH must not be inherited with empty allowlist; got keys: {list(child_env)}"
        )
        # macOS may inject two platform-level vars; exclude those and assert
        # nothing else leaked from the parent process environment.
        _PLATFORM_INJECTED = frozenset({"__CF_USER_TEXT_ENCODING", "LC_CTYPE"})
        leaked = {k: v for k, v in child_env.items() if k not in _PLATFORM_INJECTED}
        assert not leaked, (
            f"non-platform env vars reached child with empty allowlist: {leaked}"
        )

    def test_allowlisted_var_reaches_child(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A var in environment_allowlist with a supplied value reaches the child."""
        ps = process_safety
        _, sink = _recording_sink()
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", "import os; print(os.environ.get('SAFE_VAR', 'absent'))"],
                environment_allowlist=["SAFE_VAR"],
            ),
            env_values={"SAFE_VAR": "hello-from-test"},
            sensitive_values=["hello-from-test"],  # redact before checking output
            audit_sink=sink,
        )
        assert result.exit_code == 0
        # The value is redacted (appears in env → sensitive list) but the process ran.
        # Verify output contains the redaction marker instead of the raw value.
        assert b"hello-from-test" not in result.stdout_redacted
        assert b"[REDACTED]" in result.stdout_redacted

    def test_non_allowlisted_var_absent_from_child(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A var not in environment_allowlist does not reach the child."""
        ps = process_safety
        _, sink = _recording_sink()
        # Supply the var as env_values but omit it from the allowlist.
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", "import os; print(os.environ.get('BLOCKED_VAR', 'absent'))"],
                environment_allowlist=[],  # not allowed
            ),
            env_values={"BLOCKED_VAR": "should-not-appear"},
            audit_sink=sink,
        )
        assert result.exit_code == 0
        assert b"absent" in result.stdout_redacted


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0012: stdin modes
# ═══════════════════════════════════════════════════════════════════════════════


class TestStdinModes:
    """Explicit bounded stdin; closed stdin means no input to the process."""

    def test_closed_stdin_gives_empty_read(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """With stdin_mode='closed', the child reads zero bytes from stdin."""
        ps = process_safety
        _, sink = _recording_sink()
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", "import sys; data = sys.stdin.buffer.read(); print(len(data))"],
                stdin_mode="closed",
            ),
            audit_sink=sink,
        )
        assert result.exit_code == 0
        assert b"0" in result.stdout_redacted

    def test_bounded_bytes_stdin_received_by_child(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """With stdin_mode='bounded-bytes', stdin_bytes are written to stdin.

        The child echoes the byte count; the value itself is redacted from output.
        """
        ps = process_safety
        _, sink = _recording_sink()
        payload = b"secret-payload-xyz"
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", "import sys; data = sys.stdin.buffer.read(); print(len(data))"],
                stdin_mode="bounded-bytes",
            ),
            stdin_bytes=payload,
            audit_sink=sink,
        )
        assert result.exit_code == 0
        # Child prints the byte count of stdin.
        assert str(len(payload)).encode() in result.stdout_redacted
        # Raw payload must NOT appear in the redacted output.
        assert payload not in result.stdout_redacted

    def test_confined_file_stdin_missing_path_refuses(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """stdin_mode='confined-file' without a stdin_path → denied-launch-failed."""
        ps = process_safety
        _, sink = _recording_sink()
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(str(tmp_path), stdin_mode="confined-file"),
                stdin_path=None,
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-launch-failed"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0012: process-tree timeout
# ═══════════════════════════════════════════════════════════════════════════════


_NEEDS_KILL = pytest.mark.skipif(
    not hasattr(os, "killpg"),
    reason="process-group kill (os.killpg) not available on this host",
)


class TestProcessTreeTimeout:
    """Timeout triggers tree kill; no durable success or orphan children."""

    @_NEEDS_KILL
    def test_timeout_raises_denied_timeout(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A slow process raises ProcessDenied('denied-timeout')."""
        ps = process_safety
        _, sink = _recording_sink()
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(
                    str(tmp_path),
                    argv=["-c", "import time; time.sleep(120)"],
                    process_tree_timeout_s=1,
                ),
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-timeout"

    @_NEEDS_KILL
    def test_no_output_on_timeout(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """ProcessDenied(timeout) carries no durable stdout or stderr."""
        ps = process_safety
        _, sink = _recording_sink()
        raised: ps.ProcessDenied | None = None
        try:
            _launch(
                ps,
                _spec(
                    str(tmp_path),
                    argv=["-c", "import time; time.sleep(120)"],
                    process_tree_timeout_s=1,
                ),
                audit_sink=sink,
            )
        except ps.ProcessDenied as exc:
            raised = exc

        assert raised is not None and raised.denial_code == "denied-timeout"

    @_NEEDS_KILL
    def test_child_processes_killed_on_timeout(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """All child processes spawned by the timed-out process are killed.

        The parent writes the child PID to a temp file; after the timeout we
        check the child is gone.
        """
        ps = process_safety
        pid_file = tmp_path / "child.pid"
        # Parent: spawns a sleeping child, writes child PID, sleeps itself.
        code = (
            "import subprocess, sys, pathlib, time\n"
            f"pid_file = {str(pid_file)!r}\n"
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
            "pathlib.Path(pid_file).write_text(str(child.pid))\n"
            "time.sleep(120)\n"
        )
        _, sink = _recording_sink()
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(
                    str(tmp_path),
                    argv=["-c", code],
                    process_tree_timeout_s=3,
                ),
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-timeout"

        # Allow OS time to reap killed processes.
        time.sleep(0.5)

        if pid_file.exists():
            child_pid = int(pid_file.read_text().strip())
            try:
                os.kill(child_pid, 0)
                pytest.fail(
                    f"child process {child_pid} is still alive after tree kill"
                )
            except (ProcessLookupError, OSError):
                pass  # process is gone — correct


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0012: bounded output
# ═══════════════════════════════════════════════════════════════════════════════


class TestBoundedOutput:
    """output_bound_bytes caps the combined stdout + stderr."""

    def test_output_truncated_when_exceeds_bound(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """Output exceeding the bound is truncated; output_was_truncated is True."""
        ps = process_safety
        _, sink = _recording_sink()
        # Print 100 bytes; bound to 50.
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", "print('A' * 100)"],
                output_bound_bytes=50,
            ),
            audit_sink=sink,
        )
        assert result.output_was_truncated
        assert len(result.stdout_redacted) + len(result.stderr_redacted) <= 50

    def test_zero_bound_drops_all_output(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """output_bound_bytes=0 drops all output."""
        ps = process_safety
        _, sink = _recording_sink()
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", "print('should be dropped')"],
                output_bound_bytes=0,
            ),
            audit_sink=sink,
        )
        assert result.stdout_redacted == b""
        assert result.stderr_redacted == b""
        assert result.output_was_truncated

    def test_output_within_bound_is_complete(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """Output within the bound is not truncated."""
        ps = process_safety
        _, sink = _recording_sink()
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", "print('hi')"],
                output_bound_bytes=65536,
            ),
            audit_sink=sink,
        )
        assert not result.output_was_truncated
        assert b"hi" in result.stdout_redacted


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0012: redaction
# ═══════════════════════════════════════════════════════════════════════════════


class TestOutputRedaction:
    """Sensitive values (env values, stdin bytes) are replaced with [REDACTED]."""

    def test_env_value_redacted_from_stdout(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """An environment variable value that appears in stdout is replaced."""
        ps = process_safety
        _, sink = _recording_sink()
        secret = "TOP_SECRET_VALUE_XYZ"
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", "import os; print(os.environ.get('SECRET', ''))"],
                environment_allowlist=["SECRET"],
            ),
            env_values={"SECRET": secret},
            audit_sink=sink,
        )
        assert result.exit_code == 0
        assert secret.encode() not in result.stdout_redacted
        assert b"[REDACTED]" in result.stdout_redacted
        assert result.output_was_redacted

    def test_stdin_bytes_redacted_from_stdout(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """Stdin bytes echoed to stdout are replaced with [REDACTED]."""
        ps = process_safety
        _, sink = _recording_sink()
        payload = b"super-secret-input-bytes"
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())"],
                stdin_mode="bounded-bytes",
            ),
            stdin_bytes=payload,
            audit_sink=sink,
        )
        assert result.exit_code == 0
        assert payload not in result.stdout_redacted
        assert b"[REDACTED]" in result.stdout_redacted
        assert result.output_was_redacted

    def test_additional_sensitive_values_redacted(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """Caller-supplied sensitive_values are redacted from output."""
        ps = process_safety
        _, sink = _recording_sink()
        secret = "caller-secret-token"
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", f"print({secret!r})"],
            ),
            sensitive_values=[secret],
            audit_sink=sink,
        )
        assert result.exit_code == 0
        assert secret.encode() not in result.stdout_redacted
        assert b"[REDACTED]" in result.stdout_redacted


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0012: encoding
# ═══════════════════════════════════════════════════════════════════════════════


class TestOutputEncoding:
    """Non-UTF-8 output bytes are captured at the bytes level without error."""

    def test_non_utf8_output_captured_as_bytes(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A process emitting raw non-UTF-8 bytes produces a valid ProcessResult."""
        ps = process_safety
        _, sink = _recording_sink()
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", "import sys; sys.stdout.buffer.write(b'\\xff\\xfe\\x00\\x01')"],
                output_bound_bytes=65536,
            ),
            audit_sink=sink,
        )
        assert result.exit_code == 0
        assert isinstance(result.stdout_redacted, bytes)
        # The non-UTF-8 bytes either appear as-is (no match) or are replaced.
        # Either way no exception was raised.


# ═══════════════════════════════════════════════════════════════════════════════
# Security invariants: redaction order, output cap, confined stdin, cwd safety
# ═══════════════════════════════════════════════════════════════════════════════


class TestSecurityInvariants:
    """Regression fixtures for the three blocker bugs.

    Each test must fail when its specific fix is reverted:

    - ``test_secret_straddling_output_bound_is_fully_redacted``: fails if
      truncation runs before redaction.
    - ``test_output_flood_exceeding_cap_terminates``: fails if
      ``communicate()`` is used without a hard cap.
    - ``test_confined_file_stdin_outside_root_refused``,
      ``test_confined_file_stdin_symlink_refused``,
      ``test_confined_file_stdin_oversize_refused``: fail if the confined-file
      stdin reader does not enforce its root and bounds.
    - ``test_cwd_symlink_escape_refused``: fails if the cwd check only calls
      ``is_dir()`` instead of checking for symlink components.
    """

    def test_secret_straddling_output_bound_is_fully_redacted(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A sensitive value that straddles the output bound must not survive.

        The process outputs 16 bytes of padding followed by the secret (8 bytes).
        With output_bound_bytes=20 the old code truncated to 20 bytes BEFORE
        redacting, leaving the first 4 bytes of the secret in the output.
        The fixed code redacts the full stream first, then truncates.
        """
        ps = process_safety
        _, sink = _recording_sink()
        secret = "XSECRETX"  # 8 bytes
        padding = "A" * 16   # 16 bytes, total output = 24 bytes
        # The process writes padding + secret to stdout.
        code = f"import sys; sys.stdout.buffer.write(({padding!r} + {secret!r}).encode())"
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                argv=["-c", code],
                # Bound at 20: secret starts at byte 16 and ends at byte 23.
                # Without the fix, bytes 16-19 (first 4 chars of secret) survive.
                output_bound_bytes=20,
            ),
            sensitive_values=[secret],
            audit_sink=sink,
        )
        assert result.exit_code == 0
        # No fragment of the secret may appear in the redacted output.
        for frag_len in range(1, len(secret) + 1):
            assert secret[:frag_len].encode() not in result.stdout_redacted, (
                f"sensitive fragment {secret[:frag_len]!r} survived in output"
            )

    @_NEEDS_KILL
    def test_output_flood_exceeding_cap_terminates(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A running process that floods stdout beyond the hard cap is terminated.

        The hard cap is output_bound_bytes + len(longest sensitive value).
        A process that exceeds the cap while still running raises
        ProcessDenied('denied-output-cap-exceeded') and kills the process tree.
        The process keeps running (sleeps) after writing so proc.poll() is None
        when the cap fires, guaranteeing the cap-exceeded path not the timeout.
        """
        ps = process_safety
        _, sink = _recording_sink()
        secret = "MYSECRET"  # 8 bytes; hard_cap = bound + 8
        bound = 64
        hard_cap = bound + len(secret)  # = 72
        # Flood: write 10× the hard cap, then sleep so the process stays alive.
        flood_bytes = hard_cap * 10
        code = (
            f"import sys, time\n"
            f"sys.stdout.buffer.write(b'X' * {flood_bytes})\n"
            f"sys.stdout.buffer.flush()\n"
            f"time.sleep(60)\n"
        )
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(
                    str(tmp_path),
                    argv=["-c", code],
                    output_bound_bytes=bound,
                    process_tree_timeout_s=10,
                ),
                sensitive_values=[secret],
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-output-cap-exceeded"

    def test_confined_file_stdin_outside_root_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """stdin_path outside the declared stdin_root is refused.

        Without the fix, the old code opened the file with no root check.
        The fixed code uses read_confined_regular_file which checks confinement.
        """
        ps = process_safety
        _, sink = _recording_sink()
        # root = a subdir; path = a file ABOVE the root.
        root_dir = tmp_path / "root"
        root_dir.mkdir()
        outside_file = tmp_path / "outside.txt"
        outside_file.write_bytes(b"secret data")
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(
                    str(root_dir),
                    stdin_mode="confined-file",
                ),
                stdin_path=str(outside_file),
                stdin_root=str(root_dir),
                audit_sink=sink,
            )
        assert exc_info.value.denial_code in (
            "denied-stdin-confinement-violation",
            "denied-launch-failed",
        )

    def test_confined_file_stdin_symlink_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A symlink as stdin_path is refused even when it resolves inside the root.

        Without the fix, the old open() follows the symlink silently.
        The fixed code uses read_confined_regular_file which calls lstat and
        detects symlinks via UnsafeContentError.
        """
        ps = process_safety
        _, sink = _recording_sink()
        root_dir = tmp_path / "root"
        root_dir.mkdir()
        real_file = root_dir / "real.txt"
        real_file.write_bytes(b"content")
        link_file = root_dir / "link.txt"
        try:
            link_file.symlink_to(real_file)
        except (OSError, NotImplementedError):
            pytest.skip("cannot create symlink on this host")

        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(
                    str(root_dir),
                    stdin_mode="confined-file",
                ),
                stdin_path=str(link_file),
                stdin_root=str(root_dir),
                audit_sink=sink,
            )
        assert exc_info.value.denial_code in (
            "denied-stdin-confinement-violation",
            "denied-launch-failed",
        )

    def test_confined_file_stdin_oversize_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A stdin file larger than the output bound is refused.

        The fixed code passes max_bytes=bound to read_confined_regular_file.
        A file exceeding that limit raises BoundExceeded → ProcessDenied.
        Without the fix, the old code reads the file with no size check.
        """
        ps = process_safety
        _, sink = _recording_sink()
        root_dir = tmp_path / "root"
        root_dir.mkdir()
        big_file = root_dir / "big.bin"
        bound = 16
        # Write more bytes than the bound.
        big_file.write_bytes(b"X" * (bound + 1))

        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(
                    str(root_dir),
                    stdin_mode="confined-file",
                    output_bound_bytes=bound,
                    process_tree_timeout_s=10,
                ),
                stdin_path=str(big_file),
                stdin_root=str(root_dir),
                audit_sink=sink,
            )
        assert exc_info.value.denial_code in (
            "denied-stdin-confinement-violation",
            "denied-launch-failed",
        )

    def test_cwd_symlink_escape_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A cwd path that is itself a symlink to a directory is refused.

        Path.is_dir() follows symlinks so the old code accepted symlink cwd
        paths.  The fixed code calls validate_confined_directory which uses
        lstat and detects the symlink component, raising ProcessDenied.
        """
        ps = process_safety
        _, sink = _recording_sink()
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        link_dir = tmp_path / "link"
        try:
            link_dir.symlink_to(real_dir)
        except (OSError, NotImplementedError):
            pytest.skip("cannot create symlink on this host")

        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, _spec(str(link_dir)), audit_sink=sink)
        assert exc_info.value.denial_code == "denied-cwd-unsafe"

    def test_cwd_outside_every_root_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A valid cwd that is not inside any declared root refuses with denied-cwd-unsafe.

        The cwd directory exists on disk; the only declared root is a sibling
        directory, so no root contains the cwd.
        """
        ps = process_safety
        _, sink = _recording_sink()
        cwd_dir = tmp_path / "cwd_dir"
        cwd_dir.mkdir()
        other_root = tmp_path / "other_root"
        other_root.mkdir()
        with pytest.raises(ps.ProcessDenied) as exc_info:
            ps.launch_safe_process(
                _spec(str(cwd_dir)),
                cwd_roots=(str(other_root),),
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-cwd-unsafe"

    def test_cwd_inside_root_via_symlink_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A cwd inside the root but reached via a symlink component refuses.

        The cwd path has a symlinked component between the root and the cwd,
        so validate_confined_directory raises and the launch is refused.
        """
        ps = process_safety
        _, sink = _recording_sink()
        real_sub = tmp_path / "real_sub"
        real_sub.mkdir()
        link_sub = tmp_path / "link_sub"
        try:
            link_sub.symlink_to(real_sub)
        except (OSError, NotImplementedError):
            pytest.skip("cannot create symlink on this host")

        with pytest.raises(ps.ProcessDenied) as exc_info:
            ps.launch_safe_process(
                _spec(str(link_sub)),
                cwd_roots=(str(tmp_path),),
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-cwd-unsafe"

    def test_cwd_empty_roots_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """An empty cwd_roots tuple refuses with denied-cwd-unsafe.

        No root means no confinement boundary can be established.
        """
        ps = process_safety
        _, sink = _recording_sink()
        with pytest.raises(ps.ProcessDenied) as exc_info:
            ps.launch_safe_process(
                _spec(str(tmp_path)),
                cwd_roots=(),
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-cwd-unsafe"

    def test_cwd_inside_root_accepted(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A cwd inside a declared root with no symlink components is accepted."""
        ps = process_safety
        _, sink = _recording_sink()
        sub_dir = tmp_path / "sub"
        sub_dir.mkdir()
        result = ps.launch_safe_process(
            _spec(str(sub_dir)),
            cwd_roots=(str(tmp_path),),
            audit_sink=sink,
        )
        assert isinstance(result, ps.ProcessResult)


# ═══════════════════════════════════════════════════════════════════════════════
# Finding 5: bounded-bytes stdin size limit
# ═══════════════════════════════════════════════════════════════════════════════


class TestStdinBound:
    """bounded-bytes stdin must be refused when it exceeds the ceiling.

    Each test must fail (grant the write) when the size check is reverted.
    """

    def test_oversized_bounded_bytes_refused_before_launch(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """stdin exceeding MAX_STDIN_BYTES is refused before any process starts.

        Reverts to failing if the bound check is removed.
        """
        ps = process_safety
        events, sink = _recording_sink()
        # One byte over the ceiling.
        oversized = b"x" * (ps.MAX_STDIN_BYTES + 1)
        spawned: list = []

        original_popen = __import__("subprocess").Popen

        def _spy_popen(*a, **kw):  # noqa: ANN001, ANN002, ANN003
            spawned.append(True)
            return original_popen(*a, **kw)

        import subprocess
        orig = subprocess.Popen
        subprocess.Popen = _spy_popen  # type: ignore[assignment]
        try:
            with pytest.raises(ps.ProcessDenied) as exc_info:
                _launch(
                    ps,
                    _spec(str(tmp_path), stdin_mode="bounded-bytes"),
                    stdin_bytes=oversized,
                    audit_sink=sink,
                )
        finally:
            subprocess.Popen = orig  # type: ignore[assignment]

        assert exc_info.value.denial_code == "denied-stdin-bound-exceeded", (
            f"expected denied-stdin-bound-exceeded; got {exc_info.value.denial_code!r}"
        )
        assert not spawned, "no process must be spawned for oversized stdin"
        # A denial event must have been emitted.
        assert len(events) >= 1 and events[-1].outcome == "denied", (
            "denial event must be emitted before the refusal"
        )

    def test_exactly_at_ceiling_accepted(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """stdin exactly at MAX_STDIN_BYTES is accepted (boundary condition)."""
        ps = process_safety
        _, sink = _recording_sink()
        # Exactly at the ceiling.
        at_ceiling = b"z" * ps.MAX_STDIN_BYTES
        result = _launch(
            ps,
            _spec(
                str(tmp_path),
                stdin_mode="bounded-bytes",
                argv=["-c", "import sys; sys.stdin.buffer.read(); print('ok')"],
            ),
            stdin_bytes=at_ceiling,
            audit_sink=sink,
        )
        assert result.exit_code == 0

    def test_caller_bound_above_ceiling_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A stdin_bound_bytes value above MAX_STDIN_BYTES is refused.

        The caller cannot widen the ceiling beyond MAX_STDIN_BYTES.
        Reverts to failing if the stdin_bound_bytes parameter check is removed.
        """
        ps = process_safety
        events, sink = _recording_sink()
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(str(tmp_path), stdin_mode="bounded-bytes"),
                stdin_bytes=b"x",
                stdin_bound_bytes=ps.MAX_STDIN_BYTES + 1,
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-stdin-bound-exceeded", (
            f"expected denied-stdin-bound-exceeded; got {exc_info.value.denial_code!r}"
        )
        assert len(events) >= 1 and events[-1].outcome == "denied"

    def test_caller_bound_zero_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A stdin_bound_bytes value of 0 is refused (must be >= 1)."""
        ps = process_safety
        events, sink = _recording_sink()
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(str(tmp_path), stdin_mode="bounded-bytes"),
                stdin_bytes=b"",
                stdin_bound_bytes=0,
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-stdin-bound-exceeded"

    def test_caller_bound_lowers_ceiling(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A stdin_bound_bytes below MAX_STDIN_BYTES acts as a tighter ceiling."""
        ps = process_safety
        events, sink = _recording_sink()
        caller_bound = 16
        oversized_for_caller = b"x" * (caller_bound + 1)
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(str(tmp_path), stdin_mode="bounded-bytes"),
                stdin_bytes=oversized_for_caller,
                stdin_bound_bytes=caller_bound,
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-stdin-bound-exceeded"


# ═══════════════════════════════════════════════════════════════════════════════
# Finding 4 (process half): post-allow failures must store a denial event
# ═══════════════════════════════════════════════════════════════════════════════


class TestPostAllowDenialEvents:
    """AC-0021: each post-allow failure stores a denied event before raising.

    Each test must fail (no denial event) when the fix is reverted.
    """

    @_NEEDS_KILL
    def test_timeout_stores_denial_event(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A process-tree timeout stores a denied event after the allow event."""
        ps = process_safety
        events, sink = _recording_sink()
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(
                    str(tmp_path),
                    argv=["-c", "import time; time.sleep(120)"],
                    process_tree_timeout_s=1,
                ),
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-timeout"
        outcomes = [e.outcome for e in events]
        assert "allowed" in outcomes, "allow event must be stored before the process"
        assert "denied" in outcomes, "denied event must be stored after timeout"

    @_NEEDS_KILL
    def test_output_cap_stores_denial_event(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """An output-cap breach stores a denied event after the allow event."""
        ps = process_safety
        events, sink = _recording_sink()
        bound = 64
        secret = "MYSECRET"
        hard_cap = bound + len(secret)
        flood = hard_cap * 10
        code = (
            f"import sys, time\n"
            f"sys.stdout.buffer.write(b'X' * {flood})\n"
            f"sys.stdout.buffer.flush()\n"
            f"time.sleep(60)\n"
        )
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(
                    str(tmp_path),
                    argv=["-c", code],
                    output_bound_bytes=bound,
                    process_tree_timeout_s=10,
                ),
                sensitive_values=[secret],
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-output-cap-exceeded"
        outcomes = [e.outcome for e in events]
        assert "allowed" in outcomes, "allow event must be stored before the process"
        assert "denied" in outcomes, "denied event must be stored after cap breach"

    def test_launch_failure_stores_denial_event(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A Popen failure after the allow event stores a denied event.

        Monkeypatches subprocess.Popen to raise OSError after the allow event
        has been stored, so the denial event must appear alongside the allow.
        """
        ps = process_safety
        events, sink = _recording_sink()

        _real_popen = subprocess.Popen

        def _failing_popen(*args, **kwargs):  # noqa: ANN002, ANN003
            raise OSError("injected Popen failure for test")

        subprocess.Popen = _failing_popen  # type: ignore[assignment]
        try:
            with pytest.raises(ps.ProcessDenied) as exc_info:
                _launch(ps, _spec(str(tmp_path)), audit_sink=sink)
        finally:
            subprocess.Popen = _real_popen  # type: ignore[assignment]

        assert exc_info.value.denial_code == "denied-launch-failed"
        outcomes = [e.outcome for e in events]
        assert "allowed" in outcomes, "allow event must be stored before Popen"
        assert "denied" in outcomes, "denied event must be stored after Popen failure"


# ═══════════════════════════════════════════════════════════════════════════════
# Finding 6: executable identity — no-follow, bounded, fd-based exec
# ═══════════════════════════════════════════════════════════════════════════════


class TestExecIdentityMechanism:
    """AC-0011/AC-0012: executable open is no-follow, bounded, regular-file only.

    Each test must fail when the fix is reverted to path-based hashing.
    """

    def test_symlink_executable_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A symlink at the executable path is refused before any allow event.

        Without the fix, the old code followed the symlink silently.
        """
        ps = process_safety
        events, sink = _recording_sink()
        link_path = tmp_path / "python_link"
        try:
            link_path.symlink_to(PYTHON)
        except (OSError, NotImplementedError):
            pytest.skip("cannot create symlink on this host")

        link_hash = _sha256(PYTHON)  # same content; hash matches the target
        spec = _spec(str(tmp_path), executable=str(link_path), executable_identity=link_hash)
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, spec, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-launch-failed", (
            f"symlink executable should be refused with denied-launch-failed; "
            f"got {exc_info.value.denial_code!r}"
        )
        # No allow event must be present (refusal happens before allow).
        assert not any(e.outcome == "allowed" for e in events), (
            "no allow event must be stored when the executable is a symlink"
        )

    def test_fifo_executable_refused_without_hang(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A FIFO at the executable path is refused promptly, without hanging.

        Without the fix, open() on a FIFO without O_NONBLOCK blocks until a
        writer appears.  A timeout guard in this test catches a hang.
        """
        ps = process_safety
        fifo_path = tmp_path / "exec_fifo"
        try:
            os.mkfifo(str(fifo_path))
        except (OSError, AttributeError):
            pytest.skip("mkfifo not available on this host")

        result: dict = {"denied": False, "timed_out": False}

        def _run() -> None:
            events, sink = _recording_sink()
            spec = _spec(
                str(tmp_path),
                executable=str(fifo_path),
                executable_identity="a" * 64,
            )
            try:
                _launch(ps, spec, audit_sink=sink)
            except ps.ProcessDenied:
                result["denied"] = True

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=5)
        if t.is_alive():
            result["timed_out"] = True

        assert not result["timed_out"], (
            "launch with FIFO executable hung — O_NONBLOCK not applied during open"
        )
        assert result["denied"], "launch with FIFO executable must be denied"

    def test_swap_after_verification_refused(
        self, process_safety: ModuleType, tmp_path, monkeypatch
    ) -> None:
        """A binary swap between verification and exec is detected and refused.

        This test exercises the macOS / non-Linux code path where the verified
        descriptor is closed and a final no-follow stat re-checks the inode
        before Popen.  On Linux the fd-based exec path is used instead (no
        TOCTOU window), so this test is skipped there.

        The test simulates a post-verification swap by monkeypatching
        ``_open_and_verify_executable`` to return a bogus inode number.
        When the caller re-stats the real path the inode does not match,
        so launch is refused with ``denied-executable-identity-changed``.

        This test MUST fail when the final identity re-check is removed.
        """
        ps = process_safety
        if ps._USE_PROC_FD:  # type: ignore[attr-defined]
            pytest.skip("Linux uses fd-based exec; TOCTOU check is macOS/non-Linux only")

        original_fn = ps._open_and_verify_executable  # type: ignore[attr-defined]

        def _fake_verify(path: str) -> tuple:
            hex_digest, fd, st_dev, st_ino = original_fn(path)
            # Return a bogus inode to simulate a post-verification swap.
            return hex_digest, fd, st_dev, st_ino + 99_999

        monkeypatch.setattr(ps, "_open_and_verify_executable", _fake_verify)

        events, sink = _recording_sink()
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, _spec(str(tmp_path)), audit_sink=sink)
        assert exc_info.value.denial_code == "denied-executable-identity-changed", (
            f"swap should be refused with 'denied-executable-identity-changed'; "
            f"got {exc_info.value.denial_code!r}"
        )
        # A denial event must have been emitted.
        assert any(e.outcome == "denied" for e in events), (
            "a denied event must be stored when inode check fails"
        )

    @pytest.mark.skipif(
        not (sys.platform.startswith("linux") and Path("/proc/self/fd").is_dir()),
        reason="Linux /proc/self/fd fd-based exec is Linux-only",
    )
    def test_linux_proc_fd_used_for_exec(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """On Linux, Popen's executable= is /proc/self/fd/<n>, not the original path.

        When _USE_PROC_FD is True, the verified descriptor is passed directly
        to Popen so the kernel executes exactly the inode that was hashed with
        no TOCTOU window.

        This test MUST fail when the fd-based exec path is replaced with the
        original-path exec.
        """
        ps = process_safety
        popen_calls: list[dict] = []
        _real_popen = subprocess.Popen

        def _spy_popen(argv, *, executable=None, **kwargs):  # noqa: ANN001, ANN002, ANN003
            popen_calls.append({"argv": argv, "executable": executable})
            return _real_popen(argv, executable=executable, **kwargs)

        events, sink = _recording_sink()
        subprocess.Popen = _spy_popen  # type: ignore[assignment]
        try:
            _launch(ps, _spec(str(tmp_path)), audit_sink=sink)
        finally:
            subprocess.Popen = _real_popen  # type: ignore[assignment]

        assert popen_calls, "Popen must have been called"
        exe = popen_calls[0]["executable"]
        assert exe is not None, "executable= must be set in the Popen call"
        assert exe.startswith("/proc/self/fd/"), (
            f"On Linux, Popen must use /proc/self/fd/<n>; got executable={exe!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Finding 7: bounded post-kill drain — escaped descendants cannot block timeout
# ═══════════════════════════════════════════════════════════════════════════════


class TestBoundedPostKillDrain:
    """AC-0012: timeout and cap paths complete in bounded time.

    Each test must fail (hang or exceed the time bound) when the fix is reverted
    to proc.communicate() with no timeout argument.
    """

    @_NEEDS_KILL
    def test_timeout_bounded_when_descendant_holds_pipe(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """Timeout path finishes within a fixed bound even if a grandchild holds the pipe.

        The Python script spawns a grandchild with close_fds=False (so the
        grandchild inherits the stdout/stderr pipe), then the grandchild calls
        os.setpgid to create its own process group.  After the parent (Python
        script) is killed, the grandchild is still alive and holds the pipes.
        Without a bounded drain, proc.communicate() blocks forever.
        """
        ps = process_safety
        events, sink = _recording_sink()
        # Child spawns a grandchild that creates its own process group and
        # inherits the pipe, then parent sleeps past the timeout.
        code = (
            "import os, sys, subprocess, time\n"
            "gc = subprocess.Popen(\n"
            "    [sys.executable, '-c',\n"
            "     'import os, time; os.setpgid(0, 0); time.sleep(60)'],\n"
            "    close_fds=False,\n"
            ")\n"
            "time.sleep(60)\n"
        )
        start = time.monotonic()
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(
                    str(tmp_path),
                    argv=["-c", code],
                    process_tree_timeout_s=1,
                ),
                audit_sink=sink,
            )
        elapsed = time.monotonic() - start
        assert exc_info.value.denial_code == "denied-timeout"
        # 1 s timeout + 5 s drain bound + generous overhead = 15 s ceiling.
        assert elapsed < 15, (
            f"Timeout path took {elapsed:.1f}s — bounded drain not applied"
        )
        # Denial event must have been stored (Finding 4 complement).
        assert any(e.outcome == "denied" for e in events), (
            "denied event must be stored after timeout"
        )

    @_NEEDS_KILL
    @pytest.mark.parametrize("escape", [False, True], ids=["in-group", "escaped"])
    def test_stdin_holder_past_timeout_is_a_timeout_and_returns_promptly(
        self, process_safety: ModuleType, tmp_path, escape: bool
    ) -> None:
        """A descendant holding stdin that cannot all be written cannot turn a timeout into success.

        The leader starts a child that inherits stdin but not the output pipes,
        never reads, and outlives the timeout; the leader exits at once.  The
        stdin payload is larger than a pipe buffer, so it is never all written
        into the pipe (input that fits counts as delivered, read or not).
        An escaped child (own session) must not delay the refusal either.
        """
        ps = process_safety
        events, sink = _recording_sink()
        child = "import os, time; " + ("os.setsid(); " if escape else "") + "time.sleep(30)"
        code = (
            "import subprocess, sys\n"
            f"subprocess.Popen([sys.executable, '-c', {child!r}],\n"
            "    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
        start = time.monotonic()
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(
                    str(tmp_path), argv=["-c", code], process_tree_timeout_s=2,
                    stdin_mode="bounded-bytes",
                ),
                stdin_bytes=b"x" * (512 * 1024),
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-timeout"
        assert time.monotonic() - start < 10
        assert [e.outcome for e in events][-1] == "denied"

    @_NEEDS_KILL
    def test_cap_flood_by_a_descendant_after_leader_exit_refuses(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """Passing the output cap while a descendant still writes is a flood, not truncated success."""
        ps = process_safety
        events, sink = _recording_sink()
        code = (
            "import subprocess, sys, time\n"
            "subprocess.Popen([sys.executable, '-c',\n"
            "    'import sys\\nwhile True: sys.stdout.write(\"y\" * 4096)'])\n"
            "time.sleep(0.3)\n"
        )
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(str(tmp_path), argv=["-c", code], output_bound_bytes=1024),
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-output-cap-exceeded"
        assert [e.outcome for e in events][-1] == "denied"

    @_NEEDS_KILL
    def test_early_leader_exit_timeout_holds_without_waitid(
        self, process_safety: ModuleType, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The poll() fallback used where os.waitid is missing reaches the same refusal."""
        ps = process_safety
        monkeypatch.delattr(os, "waitid", raising=False)
        code = (
            "import sys, subprocess\n"
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],\n"
            "    close_fds=False)\n"
        )
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(str(tmp_path), argv=["-c", code], process_tree_timeout_s=2),
                audit_sink=_recording_sink()[1],
            )
        assert exc_info.value.denial_code == "denied-timeout"

    @_NEEDS_KILL
    def test_early_leader_exit_with_pipe_held_past_timeout_is_a_timeout(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A leader that exits early does not turn a tree that outruns its timeout into success.

        The leader starts an in-group child that inherits the output pipes,
        writes, and sleeps past the timeout, then exits at once.  The launch
        must refuse as a timeout and return no output.
        """
        ps = process_safety
        events, sink = _recording_sink()
        code = (
            "import sys, subprocess\n"
            "subprocess.Popen(\n"
            "    [sys.executable, '-c',\n"
            "     'import sys, time; sys.stdout.write(\"x\"); sys.stdout.flush(); time.sleep(30)'],\n"
            "    close_fds=False,\n"
            ")\n"
        )
        start = time.monotonic()
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps,
                _spec(str(tmp_path), argv=["-c", code], process_tree_timeout_s=2),
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-timeout"
        assert time.monotonic() - start < 15
        assert any(e.outcome == "denied" for e in events)


# ═══════════════════════════════════════════════════════════════════════════════
# Finding 11: process spec type validation before the allow event
# ═══════════════════════════════════════════════════════════════════════════════


class TestProcessSpecTypeValidation:
    """validate_process_spec_dict refuses invalid field types with stable codes.

    Each test must fail (allow the launch) when the type checks are reverted.
    All refusals must happen before any allow event is stored.
    """

    def test_string_argv_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """argv='hello' (a string, not a list) is refused with denied-invalid-field-value."""
        ps = process_safety
        events, sink = _recording_sink()
        bad = _spec(str(tmp_path), argv="hello")  # type: ignore[arg-type]
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, bad, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-invalid-field-value", (
            f"string argv must be refused; got {exc_info.value.denial_code!r}"
        )
        assert not any(e.outcome == "allowed" for e in events), (
            "no allow event must be stored when argv has the wrong type"
        )

    def test_non_string_argv_item_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """argv=[1, 'hello'] (non-string item) is refused with denied-invalid-field-value."""
        ps = process_safety
        events, sink = _recording_sink()
        bad = _spec(str(tmp_path), argv=[1, "hello"])  # type: ignore[list-item]
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, bad, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-invalid-field-value", (
            f"non-string argv item must be refused; got {exc_info.value.denial_code!r}"
        )
        assert not any(e.outcome == "allowed" for e in events), (
            "no allow event must be stored when argv contains a non-string"
        )

    def test_non_list_environment_allowlist_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """environment_allowlist='PATH' (a string) is refused with denied-invalid-field-value."""
        ps = process_safety
        events, sink = _recording_sink()
        bad = _spec(str(tmp_path), environment_allowlist="PATH")  # type: ignore[arg-type]
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, bad, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-invalid-field-value", (
            f"non-list environment_allowlist must be refused; "
            f"got {exc_info.value.denial_code!r}"
        )
        assert not any(e.outcome == "allowed" for e in events), (
            "no allow event must be stored when environment_allowlist has wrong type"
        )

    def test_env_name_with_equals_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """An env name containing '=' is refused with denied-invalid-field-value.

        An env name with '=' would corrupt the environment key=value format
        on POSIX, potentially allowing environment injection.
        """
        ps = process_safety
        events, sink = _recording_sink()
        bad = _spec(str(tmp_path), environment_allowlist=["PATH=injected"])
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, bad, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-invalid-field-value", (
            f"env name with '=' must be refused; got {exc_info.value.denial_code!r}"
        )
        assert not any(e.outcome == "allowed" for e in events), (
            "no allow event must be stored when env name contains '='"
        )

    def test_env_name_with_nul_refused(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """An env name containing NUL is refused with denied-invalid-field-value.

        A NUL byte in an env name would truncate the key at the C-string boundary,
        potentially hiding or escaping the name.
        """
        ps = process_safety
        events, sink = _recording_sink()
        bad = _spec(str(tmp_path), environment_allowlist=["PATH\x00INJECTED"])
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, bad, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-invalid-field-value", (
            f"env name with NUL must be refused; got {exc_info.value.denial_code!r}"
        )
        assert not any(e.outcome == "allowed" for e in events), (
            "no allow event must be stored when env name contains NUL"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Finding 2: NUL bytes in argv, env values, and executable path
# ═══════════════════════════════════════════════════════════════════════════════


class TestNulByteDenial:
    """NUL bytes in argv, env values, and executable path are refused before allow.

    Each test must fail (allow the launch or raise without a denial event)
    when the corresponding NUL check is reverted.
    """

    def test_nul_in_argv_item_refused_before_allow(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """An argv item containing NUL is refused before the allow event.

        A NUL byte in an argv item terminates the C-string at the OS boundary,
        silently splitting or truncating the argument.
        """
        ps = process_safety
        events, sink = _recording_sink()
        bad = _spec(str(tmp_path), argv=["-c\x00injected", "pass"])
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, bad, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-invalid-field-value", (
            f"argv item with NUL must be refused; got {exc_info.value.denial_code!r}"
        )
        assert not any(e.outcome == "allowed" for e in events), (
            "no allow event must be stored when argv contains a NUL byte"
        )
        assert len([e for e in events if e.outcome == "denied"]) >= 1, (
            "a denied event must be stored for a NUL in argv"
        )

    def test_nul_in_env_value_refused_before_allow(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """An environment value containing NUL is refused before the allow event.

        A NUL byte in a value terminates the C-string at the OS boundary,
        silently truncating the value and potentially hiding injected content.
        """
        ps = process_safety
        events, sink = _recording_sink()
        spec = _spec(
            str(tmp_path),
            environment_allowlist=["SAFE_VAR"],
        )
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps, spec,
                env_values={"SAFE_VAR": "value\x00injected"},
                audit_sink=sink,
            )
        assert exc_info.value.denial_code == "denied-invalid-field-value", (
            f"env value with NUL must be refused; got {exc_info.value.denial_code!r}"
        )
        assert not any(e.outcome == "allowed" for e in events), (
            "no allow event must be stored when an env value contains a NUL byte"
        )
        assert len([e for e in events if e.outcome == "denied"]) >= 1, (
            "a denied event must be stored for a NUL in an env value"
        )

    def test_nul_in_executable_path_refused_before_allow(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """An executable path containing NUL is refused before the allow event.

        A NUL byte in the path terminates the C-string at the OS boundary,
        silently truncating the path and defeating identity pinning.
        """
        ps = process_safety
        events, sink = _recording_sink()
        bad = _spec(str(tmp_path), executable=PYTHON + "\x00garbage")
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, bad, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-invalid-field-value", (
            f"executable with NUL must be refused; got {exc_info.value.denial_code!r}"
        )
        assert not any(e.outcome == "allowed" for e in events), (
            "no allow event must be stored when the executable path contains NUL"
        )
        assert len([e for e in events if e.outcome == "denied"]) >= 1, (
            "a denied event must be stored for a NUL in the executable path"
        )

    def test_non_oserror_from_popen_mapped_to_process_denied(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A non-OSError raised by Popen after the allow event is mapped to ProcessDenied.

        Monkeypatches subprocess.Popen to raise ValueError (a non-OSError) so
        the post-allow exception handler is exercised.  The allow event must
        appear in the sink and a denial event must follow it.
        """
        ps = process_safety
        events, sink = _recording_sink()

        _real_popen = subprocess.Popen

        def _bad_popen(*args, **kwargs):  # noqa: ANN002, ANN003
            raise ValueError("injected non-OSError Popen failure")

        subprocess.Popen = _bad_popen  # type: ignore[assignment]
        try:
            with pytest.raises(ps.ProcessDenied) as exc_info:
                _launch(ps, _spec(str(tmp_path)), audit_sink=sink)
        finally:
            subprocess.Popen = _real_popen  # type: ignore[assignment]

        assert exc_info.value.denial_code == "denied-launch-failed", (
            f"non-OSError from Popen must map to denied-launch-failed; "
            f"got {exc_info.value.denial_code!r}"
        )
        # The exception message must not contain the injected text.
        assert "injected" not in str(exc_info.value), (
            "exception text must not leak into ProcessDenied message"
        )
        outcomes = [e.outcome for e in events]
        assert "allowed" in outcomes, "allow event must be stored before Popen"
        assert "denied" in outcomes, "denied event must be stored after non-OSError"


# ═══════════════════════════════════════════════════════════════════════════════
# Finding 3: process group cleanup on the success path
# ═══════════════════════════════════════════════════════════════════════════════


class TestProcessGroupCleanup:
    """No group member survives a successful launch.

    The test must fail (group member survives) when the success-path kill is
    reverted.
    """

    @_NEEDS_KILL
    @pytest.mark.skipif(
        not Path("/bin/sh").exists(),
        reason="/bin/sh not available on this host",
    )
    def test_success_path_kills_process_group(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A successful launch leaves no surviving group member.

        The shell backgrounds a long-running sleep, prints its own PID (which
        equals the process group ID because start_new_session=True), then
        exits normally.  launch_safe_process must kill the process group before
        returning so the background sleep does not survive.
        """
        ps = process_safety
        # Resolve /bin/sh so O_NOFOLLOW does not refuse a symlink.
        sh = str(Path("/bin/sh").resolve())
        if not Path(sh).is_file():
            pytest.skip("/bin/sh resolves to a non-regular file")
        sh_hash = _sha256(sh)
        events, sink = _recording_sink()
        result = _launch(
            ps,
            {
                "schema_version": 1,
                "executable": sh,
                "executable_identity": sh_hash,
                # Background a long sleep; print the shell's PID (= pgid) to stdout.
                "argv": ["-c", "sleep 30 >/dev/null 2>&1 & printf '%d\\n' $$"],
                "grant_id": "test-pgid-cleanup",
                "cwd": str(tmp_path),
                "environment_allowlist": [],
                "stdin_mode": "closed",
                "process_tree_timeout_s": 10,
                "output_bound_bytes": 65536,
            },
            audit_sink=sink,
        )
        assert isinstance(result, ps.ProcessResult), "launch must succeed"

        # The shell printed its own PID, which equals the process group ID.
        pgid = int(result.stdout_redacted.strip())

        # Wait briefly for SIGKILL to take effect, then assert the group is gone.
        deadline = time.monotonic() + 3.0
        group_gone = False
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)
            except (ProcessLookupError, OSError):
                group_gone = True
                break
            time.sleep(0.05)

        assert group_gone, (
            f"process group {pgid} survived after launch_safe_process returned; "
            "success-path process-group kill may be missing"
        )

    @_NEEDS_KILL
    def test_refusal_after_settle_still_kills_the_group(
        self, process_safety: ModuleType, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failure after the tree settles (here in redaction) leaves no in-group child.

        The success-path group kill runs before redaction and truncation, so a
        refusal raised there comes after the kill.  Reordering redaction before
        the kill fails this test.
        """
        ps = process_safety
        pid_file = tmp_path / "pgid"
        code = (
            "import os, subprocess, sys\n"
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],\n"
            "    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
            f"open({str(pid_file)!r}, 'w').write(str(os.getpid()))\n"
        )

        def broken_redaction(*_args: object, **_kwargs: object) -> object:
            raise RuntimeError("redaction failed")

        monkeypatch.setattr(ps, "_redact_bytes", broken_redaction)
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(
                ps, _spec(str(tmp_path), argv=["-c", code]),
                audit_sink=_recording_sink()[1],
            )
        # The outer guard's code: the failure came after the tree settled.
        assert exc_info.value.denial_code == "denied-launch-failed"
        pgid = int(pid_file.read_text())
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)
            except (ProcessLookupError, OSError):
                return
            time.sleep(0.05)
        os.killpg(pgid, signal.SIGKILL)
        pytest.fail(f"process group {pgid} survived a refusal raised after the tree settled")

    @_NEEDS_KILL
    def test_interrupt_during_io_kills_the_group(
        self, process_safety: ModuleType, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A KeyboardInterrupt during the I/O exchange still ends the process group."""
        ps = process_safety
        pid_file = tmp_path / "pgid"
        code = (
            "import os, time\n"
            f"open({str(pid_file)!r}, 'w').write(str(os.getpid()))\n"
            "time.sleep(30)\n"
        )

        def interrupted(*_args: object, **_kwargs: object) -> object:
            deadline = time.monotonic() + 5.0
            while not pid_file.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            raise KeyboardInterrupt

        monkeypatch.setattr(ps, "_communicate_bounded", interrupted)
        events, sink = _recording_sink()
        with pytest.raises(KeyboardInterrupt):
            _launch(ps, _spec(str(tmp_path), argv=["-c", code]), audit_sink=sink)
        assert [e.outcome for e in events] == ["allowed", "denied"], events
        pgid = int(pid_file.read_text())
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)
            except (ProcessLookupError, OSError):
                return
            time.sleep(0.05)
        os.killpg(pgid, signal.SIGKILL)
        pytest.fail(f"process group {pgid} survived an interrupt during the I/O exchange")

    @_NEEDS_KILL
    @pytest.mark.parametrize("path", ["timeout", "output-cap"])
    def test_refusal_signals_the_group_exactly_once(
        self, process_safety: ModuleType, tmp_path, monkeypatch: pytest.MonkeyPatch, path: str
    ) -> None:
        """A refusal kills the group once, before its reap, and never signals the freed ID again."""
        ps = process_safety
        real_killpg = os.killpg
        signalled: list[int] = []

        def recording_killpg(pgid: int, sig: int) -> None:
            if sig == signal.SIGKILL:
                signalled.append(pgid)
            real_killpg(pgid, sig)

        monkeypatch.setattr(os, "killpg", recording_killpg)
        if path == "timeout":
            spec = _spec(str(tmp_path), argv=["-c", "import time; time.sleep(30)"],
                         process_tree_timeout_s=1)
            expected = "denied-timeout"
        else:
            spec = _spec(str(tmp_path), output_bound_bytes=1024, argv=[
                "-c", "import sys\nwhile True: sys.stdout.write('y' * 4096)"])
            expected = "denied-output-cap-exceeded"
        with pytest.raises(ps.ProcessDenied) as exc_info:
            _launch(ps, spec, audit_sink=_recording_sink()[1])
        assert exc_info.value.denial_code == expected
        assert len(signalled) == 1, signalled

    def test_late_failure_denial_shares_the_allow_operation_id(
        self, process_safety: ModuleType, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failure after the tree settles stores one denial under the allow event's ID."""
        ps = process_safety

        def broken_redaction(*_args: object, **_kwargs: object) -> object:
            raise RuntimeError("redaction failed")

        monkeypatch.setattr(ps, "_redact_bytes", broken_redaction)
        events, sink = _recording_sink()
        with pytest.raises(ps.ProcessDenied):
            _launch(ps, _spec(str(tmp_path)), audit_sink=sink)
        allow, denial = events
        assert (allow.outcome, denial.outcome) == ("allowed", "denied")
        assert denial.operation_id == allow.operation_id


class TestSpecIdentifierFields:
    """cwd, grant_id, and executable_identity must be non-empty strings before any launch step."""

    @pytest.mark.parametrize(
        ("field", "value"),
        [("cwd", 123), ("cwd", ""), ("grant_id", ""), ("grant_id", None),
         ("executable_identity", 7), ("executable_identity", "abc\x00")],
    )
    def test_invalid_identifier_refused_before_allow(
        self, process_safety: ModuleType, tmp_path, field: str, value: object
    ) -> None:
        ps = process_safety
        events, sink = _recording_sink()
        spec = _spec(str(tmp_path))
        spec[field] = value
        with pytest.raises(ps.ProcessDenied) as exc_info:
            ps.launch_safe_process(spec, cwd_roots=(str(tmp_path),), audit_sink=sink)
        assert exc_info.value.denial_code == "denied-invalid-field-value"
        assert not [e for e in events if e.outcome == "allowed"]


class TestGroupKillBeforeReap:
    """The success-path group kill runs while the leader still reserves the group ID."""

    def test_leader_unreaped_when_group_is_signalled(
        self, process_safety: ModuleType, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ps = process_safety
        if not (hasattr(os, "waitid") and hasattr(os, "WNOWAIT")):
            pytest.skip("waitid with WNOWAIT is unavailable on this host")
        observed: list[bool] = []
        real_killpg = os.killpg

        def recording_killpg(pgid: int, sig: int) -> None:
            try:
                info = os.waitid(os.P_PID, pgid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                observed.append(info is not None)
            except ChildProcessError:
                observed.append(False)
            real_killpg(pgid, sig)

        monkeypatch.setattr(ps.os, "killpg", recording_killpg)
        _, sink = _recording_sink()
        result = _launch(ps, _spec(str(tmp_path)), audit_sink=sink)
        assert result.exit_code == 0
        assert observed and observed[-1], (
            "the group must be signalled before the exited leader is reaped"
        )


class TestRedactionOverlap:
    """No part of any sensitive value survives, whatever the overlap or order."""

    TOKEN = b"sk1live9secret1tokenvalue"

    @pytest.mark.parametrize(
        ("values", "must_vanish"),
        [
            ([b"1", TOKEN], [b"live9secret", b"tokenvalue"]),
            ([TOKEN, b"1"], [b"live9secret", b"tokenvalue"]),
            ([b"secret1token", TOKEN], [b"live9", b"value"]),
            ([b"abcdef", b"defghi"], [b"abc", b"ghi"]),
            ([b"defghi", b"abcdef"], [b"abc", b"ghi"]),
        ],
    )
    def test_overlapping_values_leave_no_fragment(
        self, process_safety: ModuleType, values: list[bytes], must_vanish: list[bytes]
    ) -> None:
        ps = process_safety
        data = b"before " + self.TOKEN + b" mid abcdefghi after"
        redacted, was_redacted = ps._redact_bytes(data, values)
        assert was_redacted
        for fragment in [*values, *must_vanish]:
            assert fragment not in redacted, (values, redacted)
        assert redacted.startswith(b"before ") and redacted.endswith(b" after")

    def test_nested_env_value_does_not_split_a_credential_in_launch_output(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """An allowlisted short value ahead of a credential still redacts the whole credential."""
        ps = process_safety
        _, sink = _recording_sink()
        spec = _spec(
            str(tmp_path),
            argv=["-c", "import os; print('token=' + os.environ['TOKEN'])"],
            environment_allowlist=["DEBUG", "TOKEN"],
        )
        result = _launch(
            ps, spec, audit_sink=sink,
            env_values={"DEBUG": "1", "TOKEN": "sk1live9secret1tokenvalue"},
        )
        out = result.stdout_redacted
        assert b"live9secret" not in out and b"tokenvalue" not in out, out
        assert result.output_was_redacted


class TestRedactionAtTheCapAndAtScale:
    """Cover, never cut: cut-off tails are covered, complete values stay whole, and cost is linear."""

    W = b"secretpasswordX"
    V = b"XQQQQQ"

    @staticmethod
    def _reference(data: bytes, values: list[bytes], limit: int, overflowed: bool) -> bytes:
        """Brute-force definition: mark every covered byte, then emit raw bytes before *limit*."""
        covered = [False] * len(data)
        for value in {v for v in values if v}:
            for i in range(len(data) - len(value) + 1):
                if data[i:i + len(value)] == value:
                    covered[i:i + len(value)] = [True] * len(value)
        if overflowed:
            for start in range(len(data)):
                tail = data[start:]
                if any(len(v) > len(tail) and v.startswith(tail) for v in values if v):
                    covered[start:] = [True] * (len(data) - start)
                    break
        out = bytearray()
        i = 0
        while i < min(limit, len(data)):
            if covered[i]:
                out += b"[REDACTED]"
                while i < len(data) and covered[i]:
                    i += 1
            else:
                out.append(data[i])
                i += 1
        return bytes(out)

    def test_matches_the_reference_with_bounds_and_overflow(
        self, process_safety: ModuleType
    ) -> None:
        import random

        ps = process_safety
        rng = random.Random(3)
        for _ in range(5000):
            values = [
                bytes(rng.choice(b"ab1") for _ in range(rng.randint(1, 6)))
                for _ in range(rng.randint(1, 4))
            ]
            data = bytes(rng.choice(b"ab1") for _ in range(rng.randint(0, 50)))
            limit = rng.randint(0, len(data) + 3)
            overflowed = rng.random() < 0.5
            got, _ = ps._redact_bytes(data, values, limit, overflowed)
            assert got == self._reference(data, values, limit, overflowed), (
                data, values, limit, overflowed,
            )

    def test_complete_value_ending_in_another_values_prefix_stays_covered(
        self, process_safety: ModuleType
    ) -> None:
        ps = process_safety
        out, redacted = ps._redact_bytes(b"hello secretpasswordXQQ", [self.W, self.V], 100, True)
        assert redacted and b"secret" not in out and b"password" not in out, out

    def test_self_overlapping_value_at_the_cut_stays_covered(
        self, process_safety: ModuleType
    ) -> None:
        ps = process_safety
        out, _ = ps._redact_bytes(b"xx abcab", [b"abcab"], 100, True)
        assert b"abc" not in out and b"ab" not in out.replace(b"[REDACTED]", b""), out

    def test_cut_off_value_containing_a_short_value_leaves_no_fragment(
        self, process_safety: ModuleType
    ) -> None:
        ps = process_safety
        secret = b"sk1live9secret1tokenvalue" + b"x" * 25
        raw = (secret + secret + b"f" * 30 + secret)[:150]
        out, _ = ps._redact_bytes(raw, [b"1", secret], 100, True)
        for fragment in (b"sk1", b"live9", b"secret", b"token"):
            assert fragment not in out, out

    def test_overflowed_launch_never_emits_part_of_a_complete_value(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        ps = process_safety
        _, sink = _recording_sink()
        payload = "'h' * 28 + 'secretpasswordX' + 'QQ' + 'z' * 100"
        spec = _spec(
            str(tmp_path),
            argv=["-c", f"import sys; sys.stdout.write({payload})"],
            output_bound_bytes=30,
        )
        result = _launch(
            ps, spec, audit_sink=sink, sensitive_values=[self.W.decode(), self.V.decode()],
        )
        assert b"se" not in result.stdout_redacted.replace(b"[REDACTED]", b""), result
        assert result.output_was_redacted

    def test_stderr_filling_the_cap_cannot_expose_stdout_fragments(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        ps = process_safety
        _, sink = _recording_sink()
        payload = (
            "import sys; sys.stderr.write('e' * 25); sys.stderr.flush(); "
            "sys.stdout.write('secretpasswordX' * 3)"
        )
        spec = _spec(str(tmp_path), argv=["-c", payload], output_bound_bytes=30)
        result = _launch(ps, spec, audit_sink=sink, sensitive_values=[self.W.decode()])
        visible = result.stdout_redacted.replace(b"[REDACTED]", b"")
        for fragment in (b"sec", b"pass", b"word"):
            assert fragment not in visible, result

    @pytest.mark.parametrize(
        ("label", "data", "values", "overflowed"),
        [
            ("many short occurrences", b"abcX" * (1 << 18), [b"abc"], False),
            ("env value 1 everywhere", b"x1" * (1 << 19), [b"1"], False),
            ("one long periodic run", b"a" * (2 << 20), [b"a" * (1 << 20)], False),
            ("large stdin, overflowed", b"z" * (1 << 20), [bytes(range(256)) * 4096], True),
            ("crafted tail, overflowed", b"a" * (1 << 20), [b"a" * ((1 << 20) - 1) + b"b"], True),
        ],
    )
    def test_redaction_cost_stays_linear(
        self, process_safety: ModuleType, label: str, data: bytes,
        values: list[bytes], overflowed: bool,
    ) -> None:
        import time

        ps = process_safety
        started = time.monotonic()
        ps._redact_bytes(data, values, len(data), overflowed)
        assert time.monotonic() - started < 5.0, label

    def test_echoed_periodic_stdin_is_redacted_promptly(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        import time

        ps = process_safety
        _, sink = _recording_sink()
        stdin = b"ab" * (256 * 1024)
        spec = _spec(
            str(tmp_path),
            argv=["-c", "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())"],
            stdin_mode="bounded-bytes",
            output_bound_bytes=len(stdin),
        )
        started = time.monotonic()
        result = _launch(ps, spec, audit_sink=sink, stdin_bytes=stdin)
        assert result.stdout_redacted == b"[REDACTED]"
        assert time.monotonic() - started < 20.0


class TestRedactionMatchesTheBoundaryEncoding:
    """The redaction set holds the exact bytes the child receives for every secret."""

    SECRET = "pw\udcffend-credential"

    def test_collected_forms_include_the_os_boundary_bytes(
        self, process_safety: ModuleType
    ) -> None:
        ps = process_safety
        forms = ps._collect_sensitive({"TOKEN": self.SECRET}, None, [self.SECRET])
        assert os.fsencode(self.SECRET) in forms

    @pytest.mark.skipif(os.name != "posix", reason="surrogate-escaped env values are POSIX-only")
    def test_echoed_surrogate_escaped_env_value_is_redacted(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        ps = process_safety
        _, sink = _recording_sink()
        spec = _spec(
            str(tmp_path),
            argv=["-c", "import os, sys; sys.stdout.buffer.write(os.environb[b'TOKEN'])"],
            environment_allowlist=["TOKEN"],
        )
        result = _launch(ps, spec, audit_sink=sink, env_values={"TOKEN": self.SECRET})
        assert os.fsencode(self.SECRET) not in result.stdout_redacted
        assert b"credential" not in result.stdout_redacted
        assert result.output_was_redacted
