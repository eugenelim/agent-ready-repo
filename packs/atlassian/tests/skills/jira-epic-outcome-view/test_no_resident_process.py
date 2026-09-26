"""Nothing the view starts is still running when the view returns.

The view spawns, and must: it composes the flow skill, which in turn runs
the Jira client as a child of its own. So the property is not that nothing
is spawned. It is that nothing the view starts outlives it, and that what
it starts is a sibling skill rather than something else.

Two signals, both scoped to the view's own call sites. Scoping is the whole
design. Asserting that nothing spawns is impossible against the mandated
composition, and asserting that every spawn the run reaches is bounded and
skill-named reds on the flow skill's own unmodified code -- where the call
carries no timeout and the argv's first element is the interpreter. A check
that reds on code this slice does not own is not a check.

*Signal one, runtime.* Every subprocess the view's own code starts is
waited on and reaped before the view returns, and its target resolves
inside a skill directory the manifest declares.

*Signal two, source.* The view's own sources contain no detachment
primitive. Detachment is what actually leaves a process resident.

Neither subsumes the other: a recorder cannot cover a path no fixture
drives, and source absence cannot prove a dynamically assembled argv is
never built. Two things sit outside both signals and inside the criterion,
stated rather than papered over: a spawn made inside a sibling skill rather
than by the view, and any process such a sibling detaches. Closing either
needs a process-table enumeration the standard library does not offer and
no dependency here provides. What the view is accountable for is what the
view starts. Residency is treated as a binary fact throughout -- never as a
wall-clock threshold, which is machine-dependent and flaky.
"""

from __future__ import annotations

import ast
import subprocess
import sys

import atlassian_jira_epic_outcome_view_guarantees as guarantees
import pytest

#: Every way a Python process is deliberately detached from its parent.
DETACHMENT_PRIMITIVES = (
    "start_new_session",
    "creationflags",
    "DETACHED_PROCESS",
    "CREATE_NEW_PROCESS_GROUP",
    "setsid",
    "daemon",
    "nohup",
    "disown",
)

#: The calls that collect a child's exit status. A `Popen` handle no path
#: reaches with one of these is a process nobody is waiting for.
REAPING_CALLS = ("wait", "communicate", "check_output", "check_call", "run")


@pytest.fixture
def transport(tmp_path):
    return guarantees.build_recording_transport(tmp_path)


def _run(monkeypatch, load_module, transport, tmp_path, capsys):
    cli = load_module("")
    guarantees.apply_environment(monkeypatch, guarantees.view_environment(transport))
    working_dir = tmp_path / "team-working-directory"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)
    with guarantees.recording_spawns(monkeypatch) as spawns:
        exit_code = cli.main(list(guarantees.VIEW_ARGV))
    stdout = capsys.readouterr().out
    assert exit_code == 0, f"the view did not complete: {stdout}"
    guarantees.assert_answer_is_correct_and_non_empty(
        guarantees.parse_stdout_document(stdout)
    )
    return spawns


# ---------------------------------------------------------------------------
# Signal one: what the view's own code started
# ---------------------------------------------------------------------------
def test_the_run_really_started_subprocesses(
    monkeypatch, load_module, transport, tmp_path, capsys
):
    """Liveness. "Everything it started was reaped" is trivially true of a
    run that started nothing, and this composition always starts something."""
    spawns = _run(monkeypatch, load_module, transport, tmp_path, capsys)

    assert spawns.spawns, "the view started no subprocess, so it composed nothing"


def test_every_subprocess_the_view_starts_is_reaped_before_it_returns(
    monkeypatch, load_module, transport, tmp_path, capsys
):
    """Reaped, not merely finished: the exit status has been collected, so
    the child is gone rather than waiting to be noticed."""
    spawns = _run(monkeypatch, load_module, transport, tmp_path, capsys)

    unreaped = [spawn.argv for spawn in spawns.spawns if not spawn.reaped]

    assert not unreaped, f"these subprocesses were never waited on: {unreaped}"


def test_every_subprocess_the_view_starts_targets_a_declared_sibling(
    monkeypatch, load_module, transport, tmp_path, capsys
):
    """The permitted-spawn set is exactly the siblings the manifest declares.

    Two packaging shapes reach a skill and both are legitimate here: a
    script path in the argv, and `-m <package>` with the skill's own scripts
    directory on the child's import path, which is how a skill shipping a
    package rather than a single file is run without losing its package
    context. Anything resolving outside every declared skill fails.
    """
    declared = guarantees.declared_dependency_skills()
    spawns = _run(monkeypatch, load_module, transport, tmp_path, capsys)

    targets = {
        tuple(spawn.argv): guarantees.spawn_target_skill(spawn, declared)
        for spawn in spawns.spawns
    }
    stray = [argv for argv, target in targets.items() if target is None]

    assert not stray, f"these spawns target nothing the manifest declares: {stray}"
    assert set(targets.values()) == declared, (
        f"the run reached {sorted(t for t in targets.values() if t)}, "
        f"declared {sorted(declared)}"
    )


def test_no_subprocess_the_view_starts_is_detached(
    monkeypatch, load_module, transport, tmp_path, capsys
):
    """The runtime half of signal two: a detached child survives its parent
    whether or not the parent waits."""
    spawns = _run(monkeypatch, load_module, transport, tmp_path, capsys)

    assert not [spawn.argv for spawn in spawns.spawns if spawn.detached]


def test_the_runtime_signal_catches_a_process_nobody_waits_for(monkeypatch):
    """The control. Without it, "everything was reaped" could be a predicate
    that never says otherwise. A real child is started and deliberately left
    unwaited, and the same predicates must name it."""
    with guarantees.recording_spawns(monkeypatch) as spawns:
        leaked = subprocess.Popen(  # noqa: S603 - a deliberate leak, reaped below
            [sys.executable, "-c", "import time; time.sleep(30)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    try:
        assert spawns.spawns, "the recorder saw no spawn at all"
        recorded = spawns.spawns[0]

        assert not recorded.reaped, "an unwaited child was reported as reaped"
        assert recorded.detached, "a detached child was reported as attached"
        assert (
            guarantees.spawn_target_skill(recorded, guarantees.declared_dependency_skills())
            is None
        ), "a spawn outside every declared skill resolved to one"
    finally:
        leaked.kill()
        leaked.wait()


# ---------------------------------------------------------------------------
# Signal two: what the view's own sources contain
# ---------------------------------------------------------------------------
def _detachment_offences(texts) -> list[str]:
    offences = []
    for path, text in texts.items():
        for primitive in DETACHMENT_PRIMITIVES:
            for line_number, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#") or primitive not in line:
                    continue
                offences.append(f"{path.name}:{line_number}: {primitive}")
    return offences


def _unwaited_popen_offences(texts) -> list[str]:
    """Every `Popen` in a scope that reaches no call collecting an exit status.

    A `Popen` is not itself a defect -- streaming needs one -- but a handle
    no path waits on is exactly the shape that leaves a process behind, so
    the scope holding it has to reach a reaping call.
    """
    offences = []
    for path, text in texts.items():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Module):
                continue
            spawns, reaps = [], False
            for inner in ast.walk(node):
                if not isinstance(inner, ast.Call):
                    continue
                name = inner.func.attr if isinstance(inner.func, ast.Attribute) else (
                    inner.func.id if isinstance(inner.func, ast.Name) else ""
                )
                if name == "Popen":
                    spawns.append(getattr(inner, "lineno", 0))
                elif name in REAPING_CALLS:
                    reaps = True
            if spawns and not reaps:
                where = getattr(node, "name", "<module>")
                offences.append(f"{path.name}:{spawns[0]}: Popen in {where} with no wait")
    return offences


def test_the_sources_contain_no_detachment_primitive():
    """Detachment is what actually leaves a process resident, so its absence
    is asserted over the sources rather than left to whichever paths a
    fixture happens to drive."""
    texts = guarantees.python_source_text(guarantees.VIEW_SKILL_DIR)
    assert texts, "no sources were scanned"

    assert not _detachment_offences(texts)


def test_the_sources_hold_no_popen_handle_nobody_waits_on():
    texts = guarantees.python_source_text(guarantees.VIEW_SKILL_DIR)

    assert not _unwaited_popen_offences(texts)


def test_the_source_signal_catches_a_detaching_source(tmp_path):
    """The control for both source predicates. A scan that found nothing in
    a file written to be found would be a scan that finds nothing anywhere."""
    detaching = tmp_path / "detaching.py"
    detaching.write_text(
        "import subprocess\n"
        "def go():\n"
        "    subprocess.Popen(['sleep', '30'], start_new_session=True)\n",
        encoding="utf-8",
    )
    texts = {detaching: detaching.read_text(encoding="utf-8")}

    assert _detachment_offences(texts)
    assert _unwaited_popen_offences(texts)
