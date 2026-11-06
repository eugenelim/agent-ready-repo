"""The closed reason set: every code the spec names exists, every code is emitted, no launcher text.

The expected set below is written out by hand from the spec's lists, not read from the
production table. Each code is driven through a real run (the fixture launcher, a real
repository) and must appear in ``status`` and in the journal.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_HERE = Path(__file__).resolve().parent
# Each shared module by literal path, so every file this suite loads stays visibly in this pack.
_PATHS = {
    "launcher_support": _HERE / "launcher_support.py",
    "test_supervisor_integration": _HERE / "test_supervisor_integration.py",
    "test_supervisor_failure_handling": _HERE / "test_supervisor_failure_handling.py",
    "test_supervisor_launcher": _HERE / "test_supervisor_launcher.py",
    "test_supervisor_concurrency_admission": _HERE / "test_supervisor_concurrency_admission.py",
}


def _load(name: str) -> ModuleType:
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


ls = _load("launcher_support")
ti = _load("test_supervisor_integration")
fh = _load("test_supervisor_failure_handling")
lt = _load("test_supervisor_launcher")
adm = _load("test_supervisor_concurrency_admission")
harness = ls.harness
L = ls.launcher_module
conc = ls.concurrent_module
integ = ti.integ
pytestmark = ls.sup.INTEGRATION

# ── what the spec requires, by hand ─────────────────────────────────────────

# AC-0002's members that fall to the floor with a code (the policy opt-in is the run's mode,
# which `status` reports as ``concurrency.mode``), and AC-0010's malformed-entry reasons.
AC_0002 = {
    "reads-missing", "writes-missing", "stub-fence", "reprojection-bound", "non-posix-host",
    "git-version", "merge-config", "launcher-pin",
    "invalid-path", "invalid-glob", "writes-listing", "protected-path",
}
# AC-0017: each check of a containment attestation.
AC_0017 = {
    "containment-timeout", "containment-oversized", "containment-schema",
    "binding-run-id", "binding-attempt-id", "binding-grant-id", "binding-nonce",
    "binding-launcher", "read-enforcement", "allowlist-mismatch", "network-allowed",
    "write-roots", "broader-than-grant", "denial-missing",
}
# AC-0020: each defect of an access attestation that leaves an exact-source-only integration.
AC_0020 = {
    "access-mode", "access-read-outside", "access-bad-path", "access-too-many",
    "access-write-missing", "access-incomplete",
}
# AC-0067: each defect that fails an attempt outright.
AC_0067 = {
    "access-oversized", "access-schema", "access-binding", "access-token", "access-extra-line",
}
# The refusal reasons of integration-conflict.v1.
REFUSALS = {
    "meets", "content", "merge-attribute", "merge-config", "outside-changed-paths",
    "stale-authority", "cas-lost", "incomplete-attestation", "link-target",
}
# AC-0068 and AC-0052..0055: a silent attempt, a cancelled one, and one whose end is not confirmed.
CANCELLATION = {"access-timeout", "sibling-failed", "end-unconfirmed", "plan-changed"}
EXPECTED = AC_0002 | AC_0017 | AC_0020 | AC_0067 | REFUSALS | CANCELLATION

SECRET = "sk-live-0123456789abcdefSECRET"


def test_the_production_table_names_every_code_the_spec_requires() -> None:
    missing = EXPECTED - set(conc.CLOSED_REASONS)
    assert not missing, f"the closed reason set lacks {sorted(missing)}"


# ── one scenario per code ───────────────────────────────────────────────────

Scenario = Callable[[Path, pytest.MonkeyPatch], Any]


def _env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **kwargs: Any) -> Any:
    return ls.Env(tmp_path, monkeypatch, **kwargs)


def _ran(env: Any) -> Any:
    """Issue the request, run its verb, and ask what `next` makes of the task."""
    request = env.issued()
    env.verb(request["request_id"])
    env.next()
    return env


def _verb_scenario(script: dict[str, Any], **kwargs: Any) -> Scenario:
    return lambda tmp, mp: _ran(_env(tmp, mp, script=script, **kwargs))


def _plan_scenario(plan: str, **kwargs: Any) -> Scenario:
    def run(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
        env = _env(tmp, mp, plan=plan, **kwargs)
        adm._first(env)
        return env

    return run


def _refused(reason: str) -> Scenario:
    def run(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
        env = ti.make_env(tmp, mp, plan=ls.ONE_TASK)
        mp.setattr(
            integ, "apply_result",
            lambda *a, **k: (_ for _ in ()).throw(integ.Refused(reason, ["calc.py"])),
        )
        return _ran(env)

    return run


def _first_of(table: list[tuple[str, dict[str, Any], str]]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for _label, script, reason in table:
        found.setdefault(reason, script)
    return found


def _silent_containment(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    clock = ls.ScriptedClock()
    mp.setattr(L, "CLOCK", clock)
    env = _env(tmp, mp, script={"silent": True})
    harness.commit_module.set_kill_hook(
        lambda name: clock.arm(100.0, after=1) if name == "launcher-spawned" else None
    )
    request = env.issued()
    env.verb(request["request_id"])
    mp.setattr(L, "CLOCK", L._RealClock())
    ls.clear_kill_hook()
    env.next()
    return env


def _silent_access(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    env = fh.silent_env(tmp, mp, ls.ScriptedClock())
    request = env.issued()
    env.verb(request["request_id"])
    mp.setattr(L, "CLOCK", L._RealClock())
    ls.clear_kill_hook()
    env.next()
    return env


def _end_unconfirmed(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    env = _env(tmp, mp)
    request = env.issued()
    leftover = tmp / "agentbundle-attempt-leftover"
    leftover.mkdir()
    lt._craft_record(
        env, request, leader_pid=99_999_998, pgid=99_999_999, leader_start="x",
        attempt_dir=str(leftover),
    )
    mp.setattr(L, "group_alive", lambda pgid: True)
    mp.setattr(L, "CLOCK", ls.ScriptedClock(sleep_step=4.0))
    env.next()
    return env


def _attempt_lost(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    env = _env(tmp, mp)
    request = env.issued()
    lt._craft_record(env, request)
    env.next()
    return env


def _spawn_failed(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    original = L.process_start
    mp.setattr(L, "process_start", lambda pid: original(pid) if pid == os.getpid() else None)
    return _ran(_env(tmp, mp))


def _release_refused(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    original = L.send
    mp.setattr(
        L, "send", lambda proc, message: False if message["type"] == "release" else original(proc, message)
    )
    return _ran(_env(tmp, mp))


def _launcher_changed(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    env = _env(tmp, mp)
    request = env.issued()
    copy = env.store() / "launcher" / "launcher"

    def tamper(name: str) -> None:
        if name == "request-consumed":
            copy.chmod(0o700)
            copy.write_bytes(b"tampered")

    harness.commit_module.set_kill_hook(tamper)
    env.verb(request["request_id"])
    ls.clear_kill_hook()
    env.next()
    return env


def _attempt_error(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    env = _env(tmp, mp)
    request = env.issued()
    mp.setattr(integ, "hold", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("disk")))
    env.verb(request["request_id"])
    env.next()
    return env


def _attempt_location(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    env = _env(tmp, mp)
    request = env.issued()
    make = tempfile.mkdtemp

    def inside_the_run_store(*args: Any, **kwargs: Any) -> str:
        if kwargs.get("prefix") == "agentbundle-attempt-":
            kwargs["dir"] = str(env.store())  # an attempt directory inside the run store
        return make(*args, **kwargs)

    mp.setattr(tempfile, "mkdtemp", inside_the_run_store)
    env.verb(request["request_id"])
    mp.setattr(tempfile, "mkdtemp", make)
    env.next()
    return env


def _ingestion_refused(code: str) -> Scenario:
    def run(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
        env = _env(tmp, mp)

        def refuse(*args: Any, **kwargs: Any) -> Any:
            raise conc._conc.AttemptRefused(code, "refused")

        mp.setattr(conc._conc, "ingest_attempt_directory", refuse)
        return _ran(env)

    return run


def _sibling_failed(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    fh.name_meeting_tasks_together(mp)
    script = {"per_task": {
        "calculator-answers": fh.FAILS,
        "plain-note-is-written": {**fh.T2_SCRIPT, "never_access": True},
    }}
    env = ti.make_env(tmp, mp, plan=fh.MEETING_PAIR, script=script)
    _ran(env)
    return env


def _plan_changed(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    script = {"per_task": {
        "calculator-answers": fh.FAILS, "plain-note-is-written": {"write": {"plain.txt": ti.NOTE}},
    }}
    env = ti.make_env(tmp, mp, plan=ti.PAIR, script=script)
    request = env.issued()
    env.verb(request["request_id"])
    env.report(request)
    fh.edit_plan(env, "Build it, and say so.")
    env.next()
    return env


def _merge_config(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    env = _env(tmp, mp)
    env.git("config", "merge.default", "union")
    adm._first(env)
    return env


def _non_posix(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    mp.setattr(conc, "_posix_host", lambda: False)
    return _plan_scenario(ls.ONE_TASK)(tmp, mp)


def _old_git(tmp: Path, mp: pytest.MonkeyPatch) -> Any:
    git_module = ls.cli._supervisor("_supervisor_git.py")
    mp.setattr(git_module.HardenedGit, "git_version", property(lambda self: (2, 40)))
    return _plan_scenario(ls.ONE_TASK)(tmp, mp)


SPEC_FILE = f"{ls.SPEC_DIR}/spec.md"
SCENARIOS: dict[str, Scenario] = {
    # the admission set
    "reads-missing": _plan_scenario(adm._task(None, "`calc.py`")),
    "writes-missing": _plan_scenario(adm._task("`README.md`", None)),
    "invalid-path": _plan_scenario(adm._task("`../x`", "`calc.py`")),
    "invalid-glob": _plan_scenario(adm._task("`READ*.md`", "`calc.py`")),
    "writes-listing": _plan_scenario(adm._task("`README.md`", "`out/`")),
    "protected-path": _plan_scenario(adm._task("`README.md`", "`delivery/x`")),
    "stub-fence": _plan_scenario(adm._task("`README.md`", "`calc.py`", fence=True)),
    "reprojection-bound": _plan_scenario(ls.ONE_TASK, policy={"reprojection_bound": 0}),
    "non-posix-host": _non_posix,
    "git-version": _old_git,
    "merge-config": _merge_config,
    "launcher-pin": _plan_scenario(ls.ONE_TASK, name=False),
    # the containment attestation
    **{
        reason: _verb_scenario(script)
        for reason, script in _first_of(lt.CONTAINMENT).items()
        if reason != "containment-timeout"
    },
    "containment-timeout": _silent_containment,
    "containment-missing": _verb_scenario({"exit_before_containment": True}),
    # the launcher and the access attestation
    "launcher-changed": _launcher_changed,
    "launcher-closed": _release_refused,
    "launcher-spawn-failed": _spawn_failed,
    "access-timeout": _silent_access,
    "access-missing": _verb_scenario({"exit_after_release": True}),
    **{reason: _verb_scenario(script) for reason, script in _first_of(lt.ACCESS).items()},
    # a valid but incomplete attestation: integrated by exact source only
    **{reason: _verb_scenario(script) for reason, script in _first_of(lt.INCOMPLETE).items()},
    # ingestion
    "attempt-location": _attempt_location,
    "attempt-too-large": _ingestion_refused("attempt-too-large"),
    "attempt-changed": _ingestion_refused("attempt-changed"),
    "attempt-unreadable": _ingestion_refused("attempt-unreadable"),
    "attempt-special-file": _verb_scenario({"fifo": "pipe"}),
    "attempt-hard-link": _verb_scenario({"hardlinks": {"twin.py": "calc.py"}}),
    "attempt-bad-path": _verb_scenario({"write": {"a\\b": "x"}}),
    "attempt-git-name": _verb_scenario({"write": {".git/x": "x"}}),
    "attempt-unsafe-link": _verb_scenario({"links": {"ln": f"../{SPEC_FILE}"}}),
    "protected-path-changed": _verb_scenario({"write": {SPEC_FILE: "changed\n"}}),
    # integration
    **{reason: _refused(reason) for reason in REFUSALS - {"merge-config"}},
    # recovery, cancellation, and plan changes
    "attempt-lost": _attempt_lost,
    "end-unconfirmed": _end_unconfirmed,
    "attempt-error": _attempt_error,
    "sibling-failed": _sibling_failed,
    "plan-changed": _plan_changed,
}


def _reasons_in_status(env: Any) -> set[str]:
    payload = env.run("status", ls.SPEC_DIR)[1]
    assert "concurrency" in payload, payload
    view = payload["concurrency"]
    found = {a["reason"] for a in view["attempts"]}
    found.add(view["floor_reason"])
    return {r for r in found if r}


def _reasons_in_journal(env: Any) -> set[str]:
    found: set[str] = set()
    for line in ls.journal(env.repo):
        found |= {line.get("reason"), line.get("floor_reason")}
    return {r for r in found if r}


def test_every_code_in_the_table_has_a_scenario_and_every_scenario_a_code() -> None:
    table = set(conc.CLOSED_REASONS)
    assert not table - set(SCENARIOS), f"no scenario drives {sorted(table - set(SCENARIOS))}"
    assert not set(SCENARIOS) - table, f"scenario for a non-code {sorted(set(SCENARIOS) - table)}"


@pytest.mark.parametrize("code", sorted(SCENARIOS))
def test_each_code_is_emitted_in_status_and_in_the_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, code: str
) -> None:
    try:
        env = SCENARIOS[code](tmp_path, monkeypatch)
        in_status, in_journal = _reasons_in_status(env), _reasons_in_journal(env)
    finally:
        ls.clear_kill_hook()
        for path in tmp_path.glob("**/env.json"):
            ls.kill_group(json.loads(path.read_text("utf-8"))["pgid"])
    assert code in in_status, f"{code} is not in status: {sorted(in_status)}"
    assert code in in_journal, f"{code} is not in the journal: {sorted(in_journal)}"
    assert code in conc.CLOSED_REASONS
    assert in_status <= conc.CLOSED_REASONS and in_journal <= conc.CLOSED_REASONS


# ── no launcher-supplied text ───────────────────────────────────────────────

# Every free-text field the fixture controls carries the secret-shaped string.
LEAKY: dict[str, Any] = {
    "containment": {
        "host_mechanism": SECRET, "principal_or_sandbox": SECRET, "limits": {"note": SECRET},
        "notes": SECRET,
    },
    "access": {"note": SECRET},
    "denied_reads": [SECRET],
    "write": {"calc.py": f"SECRET = {SECRET!r}\n"},
}


@pytest.mark.parametrize(
    ("label", "script"),
    [
        ("honest", {}),
        ("schema", {"access_raw": SECRET}),
        ("containment", {"containment_raw": SECRET}),
        ("binding", {"access_binding_override": {"nonce": SECRET}}),
        ("token", {"token": SECRET}),
        ("extra-line", {"access_extra": SECRET}),
        ("incomplete", {"complete": False}),
        ("path", {"access_writes": [{"path": SECRET + "/\\", "kind": "write"}]}),
    ],
)
def test_no_launcher_supplied_byte_reaches_status_or_the_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str, script: dict[str, Any]
) -> None:
    env = _env(tmp_path, monkeypatch, script={**LEAKY, **script})
    request = env.issued()
    code, ran = env.verb(request["request_id"])
    nxt = env.next()
    view = env.run("status", ls.SPEC_DIR)[1]
    journal = (env.repo / ls.SPEC_DIR / ".supervisor" / "journal.jsonl").read_text("utf-8")
    for name, text in (
        ("the verb's answer", json.dumps(ran)), ("next", json.dumps(nxt)),
        ("status", json.dumps(view)), ("the journal", journal),
    ):
        assert SECRET not in text, f"launcher text reached {name}"
    assert "SECRET" not in journal and "SECRET" not in json.dumps(view["concurrency"])
