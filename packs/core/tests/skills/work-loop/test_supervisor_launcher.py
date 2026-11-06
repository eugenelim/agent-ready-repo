"""The pinned launcher and the run-concurrent verb, driven against the fixture launcher.

The fixture launcher (``fixture_launcher.py``) is a test fixture that simulates an attesting
host. Each case scripts it to emit one defect and asserts what the supervisor does about it,
never what the fixture says.
"""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_SUPPORT = Path(__file__).resolve().parent / "launcher_support.py"


def _support() -> ModuleType:
    alias = "core_work_loop_launcher_support"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _SUPPORT)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


ls = _support()
harness = ls.harness
L = ls.launcher_module
pytestmark = ls.sup.INTEGRATION

SPEC_DIR = ls.SPEC_DIR


@pytest.fixture(autouse=True)
def _reset_hooks() -> Any:
    yield
    ls.clear_kill_hook()


def _head(env: Any) -> str:
    return str(env.git("rev-parse", "HEAD")).strip()


def _outcome(payload: dict[str, Any]) -> dict[str, Any]:
    return payload["run_concurrent"]  # type: ignore[no-any-return]


def _received_types(env: Any) -> list[str]:
    return [m["type"] for m in env.received()]


def _settle_group(env: Any) -> None:
    """Test cleanup: end whatever the fixture left running."""
    path = env.log / "env.json"
    if path.exists():
        ls.kill_group(json.loads(path.read_text("utf-8"))["pgid"])


def _craft_record(env: Any, request: dict[str, Any], **changes: Any) -> dict[str, Any]:
    record = {
        "schema_version": 1, "run_id": request["run_id"], "request_id": request["request_id"],
        "task_id": request["task"]["task_id"], "revision": request["task"]["revision"],
        "attempt": 1, "state": "running", "source": _head(env),
        "verb_pid": 1, "verb_start": "gone", **changes,
    }
    ls.concurrent_module._write(harness.workspace(env.repo), request["run_id"], record, create=True)
    return record


# ── the pin at start (AC-0013, AC-0014) ─────────────────────────────────────


def test_a_named_launcher_is_copied_privately_and_pinned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    code, started = env.start()
    assert code == 0, started
    line = json.loads(env.git("show", f"HEAD:{SPEC_DIR}/delivery/approvals.jsonl").splitlines()[0])
    assert line["launcher_sha256"] == env.sha
    directory = env.store() / "launcher"
    copy = directory / "launcher"
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE(copy.stat().st_mode) == 0o700
    assert copy.stat().st_nlink == 1 and not copy.is_symlink()
    assert copy.read_bytes() == env.launcher.read_bytes()


def test_a_named_digest_with_no_matching_file_pins_nothing_and_records_an_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    env.launcher.write_bytes(env.launcher.read_bytes() + b"# changed\n")  # no longer the digest
    code, started = env.start()
    assert code == 0, started
    assert not (env.store() / "launcher").exists()
    assert [e["reason_code"] for e in ls.security_events(env.repo)] == ["launcher-pin-unmatched"]
    assert env.next()["request"]["kind"] == "implement-task"


def test_a_launcher_inside_the_work_tree_is_not_pinned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    inside = env.repo / "launcher"
    inside.write_bytes(env.launcher.read_bytes())
    inside.chmod(0o755)
    env.launcher = inside
    env.git("add", "launcher")
    env.git("commit", "-q", "-m", "launcher")
    code, started = env.start()
    assert code == 0, started
    assert not (env.store() / "launcher").exists()
    assert [e["reason_code"] for e in ls.security_events(env.repo)] == ["launcher-pin-unmatched"]


def test_no_named_digest_pins_nothing_and_records_no_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch, name=False)
    code, started = env.start()
    assert code == 0, started
    assert not (env.store() / "launcher").exists()
    assert ls.security_events(env.repo) == []


def test_the_pin_does_not_change_for_the_life_of_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    env.issued()
    other, other_sha = ls.make_launcher(tmp_path / "other", {"reads": ls.READS})
    code, again = env.run(
        "start", SPEC_DIR, "--intent", "code", "--code-trust", "trusted",
        "--authority-ref", "owner:0123456789ab",
        "--review-authority-ref", "plan-reviewer:0123456789ab",
        "--launcher-sha256", other_sha, "--launcher", str(other),
    )
    assert again["status"] == "current"
    assert (env.store() / "launcher" / "launcher").read_bytes() == env.launcher.read_bytes()


def test_a_changed_copy_goes_to_the_floor_at_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    env.issued()
    copy = env.store() / "launcher" / "launcher"
    copy.chmod(0o700)
    copy.write_bytes(b"x")
    assert env.next()["request"]["kind"] == "implement-task"
    assert ls.journal(env.repo)[-1]["floor_reason"] == "launcher-pin"


# ── the fixture marker (AC-0022) ────────────────────────────────────────────


def test_the_fixture_marker_refuses_whatever_candidate_switch_is_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in (
        "AGENTBUNDLE_ALLOW_FIXTURE_LAUNCHER", "WORK_SUPERVISOR_ALLOW_FIXTURE",
        "ALLOW_FIXTURE_LAUNCHER", "WORK_SUPERVISOR_FIXTURE", "AGENTBUNDLE_FIXTURE",
    ):
        monkeypatch.setenv(name, "1")
    env = ls.Env(
        tmp_path, monkeypatch, allow_fixture=False,
        policy={"allow_fixture_launcher": True, "fixture_launcher": True},
    )
    (tmp_path / "allow-fixture").write_text("1")
    code, refused = env.start()
    assert code == 1 and refused["refusal"]["code"] == "launcher-fixture-refused"
    code, usage = env.start("--allow-fixture-launcher")
    assert code == 2 and usage["error"] == "usage"
    assert not (env.store() if False else env.repo / ".git" / "agentbundle-supervisor").exists() or all(
        not (p / "launcher").exists()
        for p in (env.repo / ".git" / "agentbundle-supervisor").iterdir()
    )
    monkeypatch.setattr(L, "ALLOW_FIXTURE_LAUNCHER", True)
    code, started = env.start()
    assert code == 0, started


# ── the spawn (AC-0015, AC-0016) ────────────────────────────────────────────


def test_a_copy_changed_just_before_the_spawn_goes_to_the_floor_without_a_spawn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    request = env.issued()
    copy = env.store() / "launcher" / "launcher"

    def tamper() -> None:
        copy.chmod(0o700)
        copy.write_bytes(b"tampered")

    harness.commit_module.set_kill_hook(lambda name: tamper() if name == "request-consumed" else None)
    code, payload = env.verb(request["request_id"])
    assert _outcome(payload)["reason"] == "launcher-changed"
    assert not (env.log / "env.json").exists()  # nothing was spawned
    assert [e["reason_code"] for e in ls.security_events(env.repo)] == ["launcher-changed"]
    assert env.records()[0]["state"] == "floor"


def test_a_copy_changed_after_the_containment_line_goes_to_the_floor_without_a_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(
        tmp_path, monkeypatch,
        script={"tamper_glob": [str(tmp_path / "repo" / ".git" / "agentbundle-supervisor" / "*"
                                    / "launcher" / "launcher")]},
    )
    request = env.issued()
    code, payload = env.verb(request["request_id"])
    assert _outcome(payload)["reason"] == "launcher-changed"
    assert "release" not in _received_types(env)
    assert [e["reason_code"] for e in ls.security_events(env.repo)] == ["launcher-changed"]
    assert ls.group_dead(json.loads((env.log / "env.json").read_text())["pgid"])


def test_the_launcher_starts_in_a_clean_private_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in (
        ("PATH", "/tmp/planted:/usr/bin:/bin"), ("HOME", "/tmp/planted-home"),
        ("PYTHONPATH", "/tmp/planted-python"), ("LD_PRELOAD", "/tmp/planted.so"),
        ("DYLD_INSERT_LIBRARIES", "/tmp/planted.dylib"), ("SECRET_TOKEN", "planted"),
        ("TMPDIR", "/tmp/planted-tmp"), ("LANG", "en_US.UTF-8"),
    ):
        monkeypatch.setenv(name, value)
    env = ls.Env(tmp_path, monkeypatch)
    request = env.issued()
    launched: list[dict[str, Any]] = []
    real = subprocess.Popen

    def spy(argv: list[str], **kwargs: Any) -> Any:
        launched.append(kwargs)
        return real(argv, **kwargs)

    monkeypatch.setattr(L.subprocess, "Popen", spy)
    code, payload = env.verb(request["request_id"])
    monkeypatch.undo()
    assert _outcome(payload)["outcome"] == "landed", payload
    (call,) = [k for k in launched if k.get("start_new_session")]  # the one launcher spawn
    assert set(call["env"]) == {"PATH", "LANG", "HOME", "TMPDIR"}  # what the supervisor passed
    assert call["close_fds"] is True and call["start_new_session"] is True
    seen = json.loads((env.log / "env.json").read_text("utf-8"))
    # What arrived, less the variable macOS itself adds to a process it starts.
    arrived = {k: v for k, v in seen["env"].items() if not k.startswith("__CF_")}
    assert set(arrived) == {"PATH", "LANG", "HOME", "TMPDIR"}
    assert seen["env"]["PATH"] == "/usr/bin:/bin" and seen["env"]["LANG"] == "C.UTF-8"
    assert seen["env"]["HOME"] != seen["env"]["TMPDIR"]
    for key in ("HOME", "TMPDIR"):
        assert not seen["env"][key].startswith(str(env.repo))
        assert "planted" not in seen["env"][key]
    assert seen["cwd_listing"] == []
    assert seen["extra_fds"] == []
    assert seen["argv"] == [str(env.store() / "launcher" / "launcher")]


# ── consumption (AC-0024) ───────────────────────────────────────────────────


def test_a_second_invocation_for_a_run_request_spawns_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    request = env.issued()
    first = env.verb(request["request_id"])[1]
    assert _outcome(first)["outcome"] == "landed"
    spawned = (env.log / "events.log").read_text("utf-8")
    code, again = env.verb(request["request_id"])
    assert code == 1 and again["refusal"]["code"] == "request-consumed"
    assert (env.log / "events.log").read_text("utf-8") == spawned


def test_a_request_that_was_never_issued_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    env.issued()
    code, refused = env.verb("conc:nothing:" + "0" * 64 + ":1")
    assert code == 1 and refused["refusal"]["code"] == "not-current-attempt"
    assert not (env.log / "env.json").exists()


# ── a whole attempt, and the process group before release (AC-0069) ─────────


def test_an_honest_attempt_lands_its_tree_and_completes_on_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch, plan=ls.TWO_TASKS)
    request = env.issued()
    before = _head(env)
    code, payload = env.verb(request["request_id"])
    outcome = _outcome(payload)
    assert outcome["outcome"] == "landed" and outcome["access_defect"] is None
    assert _head(env) != before and _head(env) == outcome["commit"]
    assert env.git("show", "HEAD:calc.py") == ls.HONEST_WRITE["calc.py"]
    assert (env.repo / "calc.py").read_text() == ls.HONEST_WRITE["calc.py"]
    assert ls.git_clean(env.repo)
    message = env.git("log", "-1", "--format=%B")
    assert "Supervisor-Operation: implement" in message and "Supervisor-Attempt: att-" in message
    stored = (env.store() / "results").glob("*.json")
    result = json.loads(next(iter(stored)).read_text("utf-8"))
    assert result["kind"] == "implement-task" and len(result["result_tree"]) in (40, 64)
    assert len(result["access_attestation_sha256"]) == 64
    code, admitted = env.report(request)
    assert code == 0 and admitted["admitted"] == "run-concurrent"
    follow = env.next()["request"]
    assert follow["kind"] == "run-concurrent" and follow["task"]["title"].startswith("Plain")


def test_the_process_group_is_durable_before_any_line_is_sent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    request = env.issued()
    seen: dict[str, Any] = {}

    def look(name: str) -> None:
        if name == "launcher-recorded":
            seen["record"] = env.records()[0]
            seen["received"] = env.received()

    harness.commit_module.set_kill_hook(look)
    assert _outcome(env.verb(request["request_id"])[1])["outcome"] == "landed"
    record = seen["record"]
    assert record["state"] == "running" and isinstance(record["pgid"], int)
    assert record["leader_pid"] == record["pgid"] and record["leader_start"]
    assert seen["received"] == []  # no line, release included, had been sent yet


def test_a_kill_before_the_group_is_recorded_sends_no_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    request = env.issued()
    ls.crash_at("launcher-spawned")
    try:
        with pytest.raises(harness.Crash):
            env.verb(request["request_id"])
        record = env.records()[0]
        assert "pgid" not in record
        for _ in range(100):  # the fixture is a separate process: wait for it to start
            if (env.log / "env.json").exists():
                break
            time.sleep(0.05)
        assert env.received() == []
    finally:
        _settle_group(env)


# ── the containment attestation (AC-0017, AC-0018) ──────────────────────────

_ZERO = "0" * 64
CONTAINMENT = [
    ("silent", {"silent": True}, "containment-timeout"),
    ("oversized", {"containment_pad": 4_300_000}, "containment-oversized"),
    ("not-json", {"containment_raw": "not json"}, "containment-schema"),
    ("schema", {"containment_drop": ["limits"]}, "containment-schema"),
    ("run-id", {"binding_override": {"run_id": "run-0000000000000000"}}, "binding-run-id"),
    ("attempt-id", {"binding_override": {"attempt_id": "att-other"}}, "binding-attempt-id"),
    ("grant-id", {"binding_override": {"grant_id": "grant-other"}}, "binding-grant-id"),
    ("nonce", {"binding_override": {"nonce": _ZERO}}, "binding-nonce"),
    ("launcher", {"binding_override": {"launcher_sha256": _ZERO}}, "binding-launcher"),
    ("enforcement", {"containment": {"read_enforcement": "trace"}}, "read-enforcement"),
    (
        "allowlist",
        {"containment": {"read_allowlist": ["README.md", "secret.txt"]}},
        "allowlist-mismatch",
    ),
    ("network", {"containment": {"network": {"allowed": True}}}, "network-allowed"),
    ("write-roots", {"containment": {"write_roots": ["/tmp"]}}, "write-roots"),
    ("no-write-roots", {"containment_drop": ["write_roots"]}, "write-roots"),
    ("roots", {"containment": {"roots": ["/"]}}, "broader-than-grant"),
    *[
        (f"denial-{name}", {"denied_drop": [name]}, "denial-missing")
        for name in L.DENIALS
    ],
]
EVENTS = {"binding-run-id", "binding-attempt-id", "binding-grant-id", "binding-nonce",
          "binding-launcher"}


@pytest.mark.parametrize(("label", "script", "reason"), CONTAINMENT, ids=[c[0] for c in CONTAINMENT])
def test_a_containment_defect_goes_to_the_floor_without_a_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str, script: dict[str, Any], reason: str
) -> None:
    # Only the silent launcher needs the deadline to fire; every other defect
    # keeps the real 60-second window so a loaded host cannot turn it into a timeout.
    if reason == "containment-timeout":
        monkeypatch.setattr(L, "CONTAINMENT_TIMEOUT_S", 0.5)
    env = ls.Env(tmp_path, monkeypatch, script=script)
    request = env.issued()
    before = _head(env)
    code, payload = env.verb(request["request_id"])
    assert code == 0 and _outcome(payload) == {
        "outcome": "floor", "reason": reason, "task": request["task"]["task_id"]
    }
    assert "release" not in _received_types(env)
    assert ls.group_dead(json.loads((env.log / "env.json").read_text())["pgid"])
    assert _head(env) == before and not (env.repo / "calc.py").exists()
    events = [e["reason_code"] for e in ls.security_events(env.repo)]
    assert events == ([reason] if reason in EVENTS else [])
    assert env.records()[0]["reason"] == reason
    assert reason in ls.concurrent_module.CLOSED_REASONS
    floor = env.next()["request"]
    assert floor["kind"] == "implement-task"
    assert ls.journal(env.repo)[-1]["floor_reason"] == reason


def test_complete_trace_demands_trace_enforcement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(
        tmp_path, monkeypatch, mode="complete-trace",
        script={"containment": {"read_enforcement": "allowlist"}},
    )
    request = env.issued()
    assert _outcome(env.verb(request["request_id"])[1])["reason"] == "read-enforcement"


# ── the access attestation (AC-0067, AC-0029) ───────────────────────────────

ACCESS = [
    ("oversized", {"access_pad": 4_300_000}, "access-oversized"),
    ("not-json", {"access_raw": "garbage"}, "access-schema"),
    ("schema", {"access_drop": ["denied_reads"]}, "access-schema"),
    ("binding", {"access_binding_override": {"nonce": _ZERO}}, "access-binding"),
    ("envelope-binding", {"envelope_binding": {"attempt_id": "att-x"}}, "access-binding"),
    ("token", {"token": "ab" * 32}, "access-token"),
    ("extra-line", {"access_extra": "{}"}, "access-extra-line"),
    ("second-access", {"access_extra": '{"type":"access"}'}, "access-extra-line"),
    ("not-ended", {"processes_ended": False}, "processes-not-ended"),
    ("child", {"child": True}, "processes-not-ended"),
]
ACCESS_EVENTS = {"access-oversized", "access-schema", "access-binding", "access-token",
                 "access-extra-line"}


@pytest.mark.parametrize(("label", "script", "reason"), ACCESS, ids=[a[0] for a in ACCESS])
def test_an_access_defect_fails_the_attempt_without_integrating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str, script: dict[str, Any], reason: str
) -> None:
    env = ls.Env(tmp_path, monkeypatch, script=script)
    request = env.issued()
    before = _head(env)
    code, payload = env.verb(request["request_id"])
    assert _outcome(payload)["reason"] == reason, payload
    assert _head(env) == before and not (env.repo / "calc.py").exists()
    assert ls.git_clean(env.repo)
    assert ls.group_dead(json.loads((env.log / "env.json").read_text())["pgid"])
    events = [e["reason_code"] for e in ls.security_events(env.repo)]
    assert events == ([reason] if reason in ACCESS_EVENTS else [])
    floor = env.next()["request"]
    assert floor["kind"] == "implement-task"
    assert ls.journal(env.repo)[-1]["floor_reason"] == reason


# Each reason leaves an integration by exact source in place: it names only what the supervisor
# cannot rest on, so the result lands and the journal says why it is exact-source only.
INCOMPLETE = [
    ("incomplete", {"complete": False}, "access-incomplete"),
    ("mode", {"access": {"mode": "trace"}}, "access-mode"),
    (
        "read-outside",
        {"access_reads": [{"path": "README.md", "kind": "file"},
                          {"path": "secret.txt", "kind": "file"}]},
        "access-read-outside",
    ),
    (
        "bad-path",
        {"access_writes": [{"path": "calc.py", "kind": "write"}, {"path": "/abs", "kind": "write"}]},
        "access-bad-path",
    ),
    (
        "too-many",
        {"access_writes": [{"path": "calc.py", "kind": "write"}]
         + [{"path": f"w{i}", "kind": "write"} for i in range(20_001)]},
        "access-too-many",
    ),
    ("write-missing", {"access_writes": []}, "access-write-missing"),
]


@pytest.mark.parametrize(("label", "script", "reason"), INCOMPLETE, ids=[i[0] for i in INCOMPLETE])
def test_an_incomplete_access_attestation_integrates_by_exact_source_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str, script: dict[str, Any], reason: str
) -> None:
    env = ls.Env(tmp_path, monkeypatch, script=script)
    request = env.issued()
    outcome = _outcome(env.verb(request["request_id"])[1])
    assert outcome["outcome"] == "landed"
    assert outcome["exact_source_only"] is True and outcome["access_defect"] == reason
    assert reason in ls.concurrent_module.CLOSED_REASONS


def test_a_trace_read_outside_the_declared_set_is_not_a_defect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(
        tmp_path, monkeypatch, mode="complete-trace",
        script={"access_reads": [{"path": "README.md", "kind": "file"},
                                 {"path": "secret.txt", "kind": "missing"}]},
    )
    request = env.issued()
    outcome = _outcome(env.verb(request["request_id"])[1])
    assert outcome["outcome"] == "landed" and outcome["access_defect"] is None


def test_a_denied_read_does_not_enter_the_attested_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The worker tried secret.txt and the containment denied it: it is listed as denied, and
    # also among the reads, yet the attested set holds only what was read.
    env = ls.Env(
        tmp_path, monkeypatch,
        script={
            "denied_reads": ["secret.txt"],
            "access_reads": [{"path": "README.md", "kind": "file"},
                             {"path": "secret.txt", "kind": "file"}],
        },
    )
    request = env.issued()
    outcome = _outcome(env.verb(request["request_id"])[1])
    assert outcome["outcome"] == "landed" and outcome["access_defect"] is None
    assert L.attested_reads(
        {"reads": [{"path": "a", "kind": "file"}, {"path": "b", "kind": "file"}],
         "denied_reads": ["b"]}
    ) == [{"path": "a", "kind": "file"}]


# ── the release token (AC-0019) ─────────────────────────────────────────────


def _forms(token: str) -> list[bytes]:
    raw = bytes.fromhex(token)
    standard, url = base64.b64encode(raw), base64.urlsafe_b64encode(raw)
    return [
        raw, token.encode(), token.upper().encode(), standard, standard.rstrip(b"="), url,
        url.rstrip(b"="),
    ]


def _leaks(channels: dict[str, bytes], token: str) -> list[str]:
    return sorted(
        name for name, data in channels.items() if any(form in data for form in _forms(token))
    )


def test_the_release_token_appears_in_no_output_channel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch, plan=ls.TWO_TASKS)
    request = env.issued()
    printed: list[dict[str, Any]] = [request]
    code, verb = env.verb(request["request_id"])
    printed.append(verb)
    printed.append(env.report(request)[1])
    printed.append(env.next())
    printed.append(env.run("status", SPEC_DIR)[1])
    token = next(m["release_token"] for m in env.received() if m["type"] == "release")
    channels = {k: v for k, v in env.output_channels().items() if not k.endswith("recv.log")}
    channels["printed"] = json.dumps(printed).encode()
    channels["git-log"] = env.git("log", "--all", "-p", "--format=%B").encode()
    assert (env.log / "recv.log").read_text().count(token) == 1  # the one place it travels
    assert _leaks(channels, token) == []
    # The positive control: the same search finds a token planted in one channel.
    journal = env.repo / SPEC_DIR / ".supervisor" / "journal.jsonl"
    for planted in (token, token.upper(), base64.b64encode(bytes.fromhex(token)).decode()):
        journal.write_text(journal.read_text("utf-8") + planted + "\n", "utf-8")
        found = _leaks({k: v for k, v in env.output_channels().items()
                        if not k.endswith("recv.log")}, token)
        assert found == [str(journal)]
        journal.write_text(journal.read_text("utf-8").replace(planted + "\n", ""), "utf-8")


def test_the_release_token_is_not_in_the_launchers_argument_or_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    request = env.issued()
    env.verb(request["request_id"])
    token = next(m["release_token"] for m in env.received() if m["type"] == "release")
    seen = (env.log / "env.json").read_bytes()
    assert not any(form in seen for form in _forms(token))


# ── report (AC-0021) ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "fact",
    [
        {"attestation": {}},
        {"reads": [{"path": "a", "kind": "file"}]},
        {"writes": [{"path": "a", "kind": "write"}]},
        {"binding": {"run_id": "x"}},
        {"access_attestation_sha256": "0" * 64},
        {"gate": {"passed": True}},
    ],
    ids=["attestation", "reads", "writes", "binding", "access-sha", "gate"],
)
def test_a_run_concurrent_report_asserting_a_fact_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fact: dict[str, Any]
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    request = env.issued()
    env.verb(request["request_id"])
    before = _head(env)
    code, refused = env.report(request, **fact)
    assert code == 1 and refused["refusal"]["code"] == "result-fact-refused"
    assert _head(env) == before


def test_a_bare_report_before_the_attempt_lands_is_not_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    request = env.issued()
    code, refused = env.report(request)
    assert code == 1 and refused["refusal"]["code"] == "not-current-attempt"


# ── the attempt directory and the manifest (AC-0049) ────────────────────────


def test_each_attempt_runs_in_a_fresh_directory_outside_every_denied_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch, plan=ls.TWO_TASKS)
    seen: list[Path] = []

    def look(name: str) -> None:
        if name == "launcher-recorded":
            seen.append(
                Path([r for r in env.records() if r["state"] == "running"][-1]["attempt_dir"])
            )
            assert (seen[-1] / "README.md").is_file() and not (seen[-1] / ".git").exists()
            assert stat.S_IMODE(seen[-1].stat().st_mode) == 0o700

    harness.commit_module.set_kill_hook(look)
    first = env.issued()
    env.verb(first["request_id"])
    env.report(first)
    second = env.next()["request"]
    env.verb(second["request_id"])
    assert len(seen) == 2 and seen[0] != seen[1]
    for path in seen:
        real = Path(os.path.realpath(path))
        for denied in (env.repo, env.repo / ".git", env.store()):
            denied = Path(os.path.realpath(denied))
            assert real != denied and denied not in real.parents and real not in denied.parents
        assert not path.exists()  # removed once its result landed


def test_a_trusted_file_changed_during_an_attempt_refuses_it_as_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    request = env.issued()
    before = _head(env)
    spec = env.repo / SPEC_DIR / "spec.md"
    original = spec.read_bytes()

    def edit(name: str) -> None:
        if name == "released":
            spec.write_bytes(original + b"\nedited\n")

    harness.commit_module.set_kill_hook(edit)
    code, refused = env.verb(request["request_id"])
    assert code == 1 and refused["refusal"]["code"] == "attempt-residue"
    spec.write_bytes(original)
    assert _head(env) == before and not (env.repo / "calc.py").exists()


# ── cancellation and an end that is not confirmed (AC-0068 semantics) ───────


def test_an_attempt_silent_past_its_timeout_is_cancelled_and_never_integrates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(
        tmp_path, monkeypatch, script={"never_access": True, "on_abort": "ignore"},
        policy={"attempt_timeout_seconds": 60},
    )
    request = env.issued()
    monkeypatch.setattr(L, "CLOCK", ls.StepClock(5.0))
    before = _head(env)
    code, payload = env.verb(request["request_id"])
    assert _outcome(payload)["outcome"] == "cancelled" and _outcome(payload)["reason"] == "access-timeout"
    assert ls.group_dead(json.loads((env.log / "env.json").read_text())["pgid"])
    assert _head(env) == before
    monkeypatch.setattr(L, "CLOCK", L._RealClock())
    assert env.next()["request"]["kind"] == "implement-task"


def test_an_end_that_never_confirms_leaves_residue_and_goes_to_the_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(
        tmp_path, monkeypatch, script={"never_access": True},
        policy={"attempt_timeout_seconds": 60},
    )
    request = env.issued()
    seen: list[Path] = []
    harness.commit_module.set_kill_hook(
        lambda name: seen.append(
                Path([r for r in env.records() if r["state"] == "running"][-1]["attempt_dir"])
            )
        if name == "launcher-recorded" else None
    )
    monkeypatch.setattr(L, "CLOCK", ls.StepClock(20.0))
    monkeypatch.setattr(L, "group_alive", lambda pgid: True)  # an end the window cannot confirm
    try:
        code, payload = env.verb(request["request_id"])
    finally:
        _settle_group(env)
    assert _outcome(payload)["outcome"] == "residue"
    assert env.records()[0]["state"] == "residue" and seen[0].exists()
    monkeypatch.undo()
    assert env.next()["request"]["kind"] == "implement-task"


# ── recovery (AC-0025, AC-0065, AC-0066) ────────────────────────────────────


def test_a_dead_verb_whose_commit_landed_is_recorded_as_landed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch, plan=ls.TWO_TASKS)
    request = env.issued()
    ls.crash_at("integration-before-record")
    with pytest.raises(harness.Crash):
        env.verb(request["request_id"])
    ls.clear_kill_hook()
    landed = _head(env)
    assert not (env.repo / "calc.py").exists()  # the working tree was not brought along
    record = env.records()[0]
    assert record["state"] == "held"  # the result was recorded; its landing was not
    ls.concurrent_module._write(
        harness.workspace(env.repo), request["run_id"], {**record, "verb_start": "gone"}
    )
    follow = env.next()["request"]
    assert follow["kind"] == "run-concurrent" and follow["task"]["title"].startswith("Plain")
    assert _head(env) == landed  # recovery made no commit
    record = env.records()[0]
    assert record["state"] == "landed" and record["commit"] == landed
    assert (env.repo / "calc.py").read_text() == ls.HONEST_WRITE["calc.py"]
    assert ls.git_clean(env.repo)


def test_a_dead_leader_with_a_live_group_member_has_its_group_ended(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(
        tmp_path, monkeypatch,
        script={"child": True, "hold": True, "gate": str(tmp_path / "never")},
    )
    request = env.issued()
    ls.crash_at("released")
    with pytest.raises(harness.Crash):
        env.verb(request["request_id"])
    ls.clear_kill_hook()
    record = env.records()[0]
    pid, pgid = record["leader_pid"], record["pgid"]
    try:
        os.kill(pid, 9)
        os.waitpid(pid, 0)  # the leader is gone and reaped; its sleeping child remains
        assert L.group_alive(pgid)
        ls.concurrent_module._write(
            harness.workspace(env.repo), request["run_id"], {**record, "verb_start": "gone"}
        )
        payload = env.next()
        assert "request" in payload, payload
        floor = payload["request"]
        assert floor["kind"] == "implement-task"
        assert ls.group_dead(pgid)
        assert env.records()[0]["state"] == "cancelled"
        assert ls.journal(env.repo)[-1]["floor_reason"] == "attempt-lost"
    finally:
        ls.kill_group(pgid)


def test_a_recorded_group_whose_leader_id_another_process_holds_is_never_signalled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    request = env.issued()
    bystander = subprocess.Popen(["sleep", "60"], start_new_session=True)
    try:
        _craft_record(
            env, request, leader_pid=bystander.pid, pgid=bystander.pid, leader_start="not-its-start"
        )
        assert env.next()["request"]["kind"] == "implement-task"
        assert bystander.poll() is None  # not signalled
        record = env.records()[0]
        assert record["state"] == "cancelled" and record["reason"] == "attempt-lost"
    finally:
        bystander.kill()
        bystander.wait()


def test_an_end_recovery_cannot_confirm_is_residue_and_the_task_goes_to_the_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    request = env.issued()
    leftover = tmp_path / "agentbundle-attempt-leftover"
    leftover.mkdir()
    (leftover / "kept").write_text("x")
    _craft_record(
        env, request, leader_pid=99_999_998, pgid=99_999_999, leader_start="x",
        attempt_dir=str(leftover),
    )
    monkeypatch.setattr(L, "group_alive", lambda pgid: True)
    monkeypatch.setattr(L, "CLOCK", ls.StepClock(4.0))
    floor = env.next()["request"]
    assert floor["kind"] == "implement-task"
    record = env.records()[0]
    assert record["state"] == "residue" and record["reason"] == "end-unconfirmed"
    assert (leftover / "kept").exists()
    assert ls.journal(env.repo)[-1]["floor_reason"] == "end-unconfirmed"


def test_the_fixture_launcher_is_never_reachable_from_the_pack_runtime() -> None:
    pack = Path(__file__).resolve().parents[3]
    assert "tests" in Path(__file__).resolve().parts
    assert not list((pack / ".apm").rglob("fixture_launcher*"))


def test_start_settles_a_dead_verbs_attempt_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch, plan=ls.TWO_TASKS)
    request = env.issued()
    ls.crash_at("integration-before-record")
    with pytest.raises(harness.Crash):
        env.verb(request["request_id"])
    ls.clear_kill_hook()
    record = env.records()[0]
    ls.concurrent_module._write(
        harness.workspace(env.repo), request["run_id"], {**record, "verb_start": "gone"}
    )
    code, again = env.start()
    assert again["status"] == "current"
    assert env.records()[0]["state"] == "landed"
    assert (env.repo / "calc.py").exists() and ls.git_clean(env.repo)
