"""The per-issue file lands outside both protected roots and is removed.

The flow skill's per-issue mode requires an output file, so this view
writes one. These assertions are about process-level filesystem state:
where that file goes, and that it is gone by the time the view returns --
including when the run raises, which is the path a `finally`-free
implementation leaves behind.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

WINDOW = {"from": "2026-08-25", "to": "2026-09-24"}

_ROW = {
    "key": "PROJ-1",
    "issuetype_bucket": "feature",
    "delivered_in_window": True,
    "wip_at_to": False,
}


@pytest.fixture
def flow(load_module):
    return load_module("flow")


class _Completed:
    def __init__(self, returncode=0, stderr=b""):
        self.returncode = returncode
        self.stdout = b""
        self.stderr = stderr


def _output_path(argv) -> Path:
    return Path(argv[argv.index("--output") + 1])


def _recording_runner(seen, *, returncode=0, write_rows=True, raises=None):
    """Stand in for the flow skill: record the output path, optionally
    write the JSONL it would write, and optionally fail the way it would."""

    def runner(argv, **_kwargs):
        path = _output_path(argv)
        seen["argv"] = list(argv)
        seen["path"] = path
        seen["existed_during_run"] = path.parent.is_dir()
        if write_rows:
            path.write_text(json.dumps(_ROW) + "\n", "utf-8")
        if raises is not None:
            raise raises
        return _Completed(returncode=returncode, stderr=b"upstream said no")

    return runner


def _run(flow, runner, tmp_path, pack_root):
    return flow.run_flow_metrics(
        scripts_dir=tmp_path / "scripts",
        scope_args=["--project", "PROJ"],
        window=WINDOW,
        include_subtasks=False,
        cwd_root=tmp_path,
        pack_root=pack_root,
        runner=runner,
    )


def test_the_per_issue_file_lands_outside_both_protected_roots(flow, tmp_path, pack_root):
    """Neither the invocation working directory tree nor the installed pack
    tree may hold it, because both are asserted byte-identical across a run."""
    seen = {}

    rows = _run(flow, _recording_runner(seen), tmp_path, pack_root)

    assert rows == [_ROW]
    path = seen["path"].resolve()
    for root in (tmp_path.resolve(), pack_root.resolve()):
        with pytest.raises(ValueError):
            path.relative_to(root)


def test_the_per_issue_file_is_removed_before_the_view_returns(flow, tmp_path, pack_root):
    """It existed during the run and is gone afterwards. Asserting only the
    second half would pass an implementation that never wrote it."""
    seen = {}

    _run(flow, _recording_runner(seen), tmp_path, pack_root)

    assert seen["existed_during_run"] is True
    assert not seen["path"].exists()
    assert not seen["path"].parent.exists()


def test_the_per_issue_file_is_removed_when_the_run_raises(flow, tmp_path, pack_root):
    """A failed run leaves nothing behind either. This is the case a
    cleanup written after the call site, rather than in a `finally`, misses."""
    seen = {}
    runner = _recording_runner(seen, raises=RuntimeError("the flow reading died"))

    with pytest.raises(RuntimeError):
        _run(flow, runner, tmp_path, pack_root)

    assert seen["existed_during_run"] is True
    assert not seen["path"].exists()
    assert not seen["path"].parent.exists()


def test_a_non_zero_flow_exit_is_surfaced_and_still_cleans_up(flow, tmp_path, pack_root):
    """"Could not reach Jira" and "no Epics" are different facts, so the
    failure is raised rather than rendered as an empty reading."""
    seen = {}
    runner = _recording_runner(seen, returncode=3)

    with pytest.raises(flow.FlowMetricsError) as excinfo:
        _run(flow, runner, tmp_path, pack_root)

    assert "upstream said no" in str(excinfo.value)
    assert not seen["path"].parent.exists()


def test_a_scratch_directory_inside_a_protected_root_is_refused(
    flow, tmp_path, pack_root, monkeypatch
):
    """A temporary directory configured under the working directory would
    turn the one disclosed write into a breach. It is refused before
    anything is written, and the probe directory is still cleaned up."""
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    seen = {}

    with pytest.raises(flow.ScratchLocationError):
        _run(flow, _recording_runner(seen), tmp_path, pack_root)

    assert "path" not in seen  # the runner never started
    assert list(tmp_path.iterdir()) == []


def test_the_flow_skill_is_composed_only_through_the_inert_cache_mode(flow, tmp_path, pack_root):
    """The bypass flag still unlinks stale temporary files from a cache
    directory relative to the working directory, and deleting a file is a
    write. Only the inert mode performs no cache operation at all."""
    seen = {}

    _run(flow, _recording_runner(seen), tmp_path, pack_root)

    argv = seen["argv"]
    assert "--inert-cache" in argv
    assert "--no-cache" not in argv
    assert "--per-issue" in argv
    assert "--output" in argv


def test_nothing_is_created_before_the_location_is_checked(
    flow, tmp_path, pack_root, monkeypatch
):
    """"Refused before anything is written" is a claim about ordering, and
    only the order can test it. Creating the directory and then deciding it
    sits in the wrong place has already written into a root the view
    promises to leave unchanged -- and a tidy removal afterwards is not the
    same guarantee."""
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    made = []
    real_mkdtemp = tempfile.mkdtemp

    def recording_mkdtemp(*args, **kwargs):
        made.append((args, kwargs))
        return real_mkdtemp(*args, **kwargs)

    monkeypatch.setattr(tempfile, "mkdtemp", recording_mkdtemp)

    with pytest.raises(flow.ScratchLocationError):
        _run(flow, _recording_runner({}), tmp_path, pack_root)

    assert made == [], "a directory was created inside the protected root first"


def test_a_removal_that_fails_is_surfaced_rather_than_swallowed(
    flow, tmp_path, pack_root, monkeypatch
):
    """Removing the scratch directory is how the disclosed write is undone.
    Ignoring an error there makes a directory left behind indistinguishable
    from one removed, and the guarantee then rests on nothing."""
    seen = {}
    real_rmtree = shutil.rmtree

    def failing_rmtree(path, *args, **kwargs):
        raise OSError(f"removal refused: {path}")

    monkeypatch.setattr(shutil, "rmtree", failing_rmtree)

    with pytest.raises(OSError, match="removal refused"):
        _run(flow, _recording_runner(seen), tmp_path, pack_root)

    monkeypatch.undo()
    real_rmtree(seen["path"].parent, ignore_errors=True)
