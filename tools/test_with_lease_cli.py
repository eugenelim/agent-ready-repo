"""End-to-end command-line coverage for the cooperative worktree lease."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.repo import coordination_lease, managed_child


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Create one real Git worktree and its common directory for each case."""
    root = (tmp_path / "repository").resolve()
    root.mkdir()
    subprocess.run(("git", "init", "-q", str(root)), check=True)
    return root


def test_main_strips_argparse_remainder_separator(repository: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The documented ``with-lease -- command`` form reaches the real child argv."""
    monkeypatch.chdir(repository)
    assert coordination_lease.main(
        ["with-lease", "--", sys.executable, "-c", "raise SystemExit(19)"]
    ) == 19


def test_main_refuses_malformed_slot_configuration(
    repository: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An operator budget error refuses at the shipped CLI boundary."""
    monkeypatch.chdir(repository)
    monkeypatch.setenv(coordination_lease.MAX_CONCURRENT_RUNS_ENV, "zero")
    assert coordination_lease.main(["with-lease", "--", "git", "status"]) == 75
    captured = capsys.readouterr()
    assert "WORKTREE_LEASE_DID_NOT_RUN" in captured.err
    assert "did not run" in captured.err


def test_main_refuses_a_missing_wrapped_command(
    repository: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An empty ``--`` tail is a reserved wrapper refusal, not a spawn attempt."""
    monkeypatch.chdir(repository)
    assert coordination_lease.main(["with-lease", "--"]) == 75
    captured = capsys.readouterr()
    assert "WORKTREE_LEASE_DID_NOT_RUN" in captured.err
    assert "did not run" in captured.err


def test_release_claim_releases_an_undeterminable_claim(
    repository: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The explicit recovery path removes an uninspectable worktree claim."""
    if os.name == "nt":
        pytest.skip("Windows ACLs do not make chmod(0) a reliable unreadability probe")
    monkeypatch.chdir(repository)
    common = coordination_lease.git_common_dir(repository)
    lease_dir = coordination_lease.prepare_lease_directory(common)
    identifier = "activity-undeterminable.lease"
    path = lease_dir / identifier
    path.write_text("not-json", encoding="utf-8")
    path.chmod(0)
    try:
        assert coordination_lease.main(["release-claim", "--apply", "--claim", identifier]) == 0
    finally:
        if path.exists():
            path.chmod(0o600)
    assert not path.exists()
    assert "override of a claim that may be live" in capsys.readouterr().out


def test_release_claim_refuses_a_live_holder(
    repository: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A recovery command never removes a claim whose ownership lock is observable."""
    monkeypatch.chdir(repository)
    common = coordination_lease.git_common_dir(repository)
    claim = coordination_lease.acquire_activity(common, repository, wait_seconds=1)
    try:
        assert coordination_lease.main(
            ["release-claim", "--apply", "--claim", claim.path.name]
        ) == 75
    finally:
        claim.release()
    captured = capsys.readouterr()
    assert "WORKTREE_LEASE_DID_NOT_RUN" in captured.err
    assert "did not run" in captured.err


def test_queued_wrapper_reports_its_holders(
    repository: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A saturated real slot emits a queue notice before its bounded refusal."""
    monkeypatch.chdir(repository)
    monkeypatch.setenv(coordination_lease.MAX_CONCURRENT_RUNS_ENV, "1")
    monkeypatch.setenv(coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV, "1")
    common = coordination_lease.git_common_dir(repository)
    holder = coordination_lease.acquire_run_slot(
        common,
        environ={
            coordination_lease.MAX_CONCURRENT_RUNS_ENV: "1",
            coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV: "1",
        },
    )
    try:
        assert coordination_lease.main(["with-lease", "--", "git", "status"]) == 75
    finally:
        holder.release()
    assert "with-lease queued behind process ids:" in capsys.readouterr().err


def test_status_is_read_only_and_emits_recovery_identifier(
    repository: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Status names claims safely and gives the exact recovery command input."""
    monkeypatch.chdir(repository)
    common = coordination_lease.git_common_dir(repository)
    claim = coordination_lease.acquire_activity(common, repository, wait_seconds=1)
    try:
        before = claim.path.read_bytes()
        assert coordination_lease.main(["lease-status"]) == 0
        assert claim.path.read_bytes() == before
    finally:
        claim.release()
    output = capsys.readouterr().out
    assert claim.path.name in output
    assert f"release-claim --apply --claim {claim.path.name}" in output
    assert str(repository) not in output


def test_nested_recursive_make_completes(repository: Path) -> None:
    """A real recursive make inherits the live slot rather than waiting for itself."""
    makefile = repository / "Lease.mk"
    makefile.write_text(
        "outer:\n"
        f"\t{sys.executable} tools/repo/coordination_lease.py with-lease -- $(MAKE) -f $(firstword $(MAKEFILE_LIST)) inner\n"
        "inner:\n"
        f"\t{sys.executable} tools/repo/coordination_lease.py with-lease -- {sys.executable} -c \"print('nested-complete')\"\n",
        encoding="utf-8",
    )
    source = Path(coordination_lease.__file__).resolve()
    tools_dir = source.parent.parent
    link = repository / "tools"
    link.symlink_to(tools_dir, target_is_directory=True)
    result = subprocess.run(
        ("make", "-f", str(makefile), "outer"),
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "nested-complete" in result.stdout


def test_wrapper_has_exactly_one_reachable_child_runner() -> None:
    """The wrapper delegates child lifecycle ownership to the shared runner.

    Counted over the PARSED TREE, not the source text. A substring count also
    matches the string inside a comment or docstring, and it did: an explanatory
    comment naming `managed_child.run_child(...)` reddened this test while there was
    exactly one real call. A structural check that prose can break is worse than no
    check, because the next person deletes the prose rather than the duplication.
    """
    tree = ast.parse(Path(coordination_lease.__file__).read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run_child"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "managed_child"
    ]
    assert len(calls) == 1, (
        f"expected exactly one managed_child.run_child call, found {len(calls)} at "
        f"lines {[c.lineno for c in calls]}"
    )
    # And it is the shared runner, not a local shadow.
    assert managed_child.run_child.__module__.endswith("managed_child")


def test_wrapper_only_adds_the_nesting_marker(repository: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The child sees the inherited environment plus only the slot identity marker."""
    monkeypatch.chdir(repository)
    # The invariant is a DELTA, not an absolute set. macOS injects LC_CTYPE and
    # __CF_USER_TEXT_ENCODING into a spawned process even when a restricted env is
    # passed, so asserting `set(os.environ) == {MARKER}` fails for a reason that has
    # nothing to do with the wrapper. Name the platform's additions and assert what
    # the WRAPPER added.
    platform_injected = {"LC_CTYPE", "__CF_USER_TEXT_ENCODING"}
    script = (
        "import os; "
        "added = set(os.environ) - " + repr(platform_injected) + "; "
        "raise SystemExit(0 if added == {"
        + repr(coordination_lease.RUN_SLOT_NESTING_MARKER_ENV)
        + "} else 1)"
    )
    assert coordination_lease.with_lease(
        (sys.executable, "-c", script), repository=repository, environ={}
    ) == 0

    # And the delta really is a delta: a pre-existing key survives untouched.
    inherited = (
        "import os; "
        "raise SystemExit(0 if os.environ.get('CARRIED') == 'yes' else 1)"
    )
    assert coordination_lease.with_lease(
        (sys.executable, "-c", inherited), repository=repository,
        environ={"CARRIED": "yes"},
    ) == 0
