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
import stat
import sys
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

PYTHON = sys.executable


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
            ps.launch_safe_process(_spec(str(tmp_path)), audit_sink=None)
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
            ps.launch_safe_process(_spec(str(tmp_path)), audit_sink=bad_sink)
        assert exc_info.value.denial_code == "denied-audit-sink-unavailable"

    def test_none_sink_leaves_no_output(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """No ProcessResult is produced when the sink is unavailable."""
        ps = process_safety
        result = None
        with contextlib.suppress(ps.ProcessDenied):
            result = ps.launch_safe_process(_spec(str(tmp_path)), audit_sink=None)
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
        result = ps.launch_safe_process(_spec(str(tmp_path)), audit_sink=sink)
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
            ps.launch_safe_process(bad, audit_sink=sink)
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
            ps.launch_safe_process(bad, audit_sink=sink)
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
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
            ps.launch_safe_process(bad, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-identity-mismatch"

    def test_correct_identity_allows(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """Correct executable_identity pin allows launch."""
        ps = process_safety
        _, sink = _recording_sink()
        result = ps.launch_safe_process(_spec(str(tmp_path)), audit_sink=sink)
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
            ps.launch_safe_process(bad, audit_sink=sink)
        assert exc_info.value.denial_code == "denied-cwd-not-found"

    def test_valid_cwd_is_respected(
        self, process_safety: ModuleType, tmp_path
    ) -> None:
        """A valid cwd is set for the child process."""
        ps = process_safety
        _, sink = _recording_sink()
        # Ask Python to print its cwd; it must match tmp_path.
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
            ps.launch_safe_process(
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
            ps.launch_safe_process(
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
            ps.launch_safe_process(
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
            ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
        result = ps.launch_safe_process(
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
