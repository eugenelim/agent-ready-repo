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


def test_admission_precedes_activity_so_a_queued_run_never_blocks_cleanup(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing may hold the cleanup-blocking role while still waiting for a slot.

    AC7 scopes the activity claim to "exactly one child's lifetime". Acquiring it
    before the admission wait meant a merely queued run refused cleanup for the whole
    wait budget with no child in existence. Observed at the moment the slot
    acquisition is entered, because a claim released by the wrapper's own unwind is
    invisible to any check made after the call returns -- which is why the ordering
    survived a suite that only inspected the aftermath.
    """
    monkeypatch.chdir(repository)
    common = coordination_lease.git_common_dir(repository)
    lease_dir = common / coordination_lease.LEASE_DIRECTORY
    claims_when_admission_began: list[list[str]] = []
    real_acquire = coordination_lease.acquire_run_slot

    def watching(*args: object, **kwargs: object) -> object:
        existing = sorted(p.name for p in lease_dir.glob("*.lease")) if lease_dir.is_dir() else []
        claims_when_admission_began.append(existing)
        return real_acquire(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(coordination_lease, "acquire_run_slot", watching)
    assert coordination_lease.main(
        ["with-lease", "--", sys.executable, "-c", "raise SystemExit(0)"]
    ) == 0
    assert claims_when_admission_began == [[]], (
        "a claim existed before admission was even attempted: "
        f"{claims_when_admission_began}"
    )


def test_nested_receipt_names_the_holder_and_never_the_marker(
    repository: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC8's receipt makes an inert limiter visible without publishing a bypass."""
    monkeypatch.chdir(repository)
    common = coordination_lease.git_common_dir(repository)
    holder = coordination_lease.acquire_run_slot(common, environ={})
    try:
        monkeypatch.setenv(
            coordination_lease.RUN_SLOT_NESTING_MARKER_ENV, holder.nesting_marker
        )
        assert coordination_lease.main(
            ["with-lease", "--", sys.executable, "-c", "raise SystemExit(0)"]
        ) == 0
    finally:
        holder.release()
    captured = capsys.readouterr().err
    assert "nested" in captured
    assert "limiter is inert" in captured
    assert f"pid {holder.pid}" in captured
    # The marker is the bypass; naming the holder is the point, echoing the token is not.
    assert holder.nesting_marker not in captured


def test_a_held_coordination_lock_refuses_rather_than_running_unleased(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Decision-lock exhaustion is contention, so the limiter may not switch off.

    A lock still held by a live peer when the budget runs out was reported as an
    unusable store, and the wrapper's fail-open branch then ran the child with no
    slot at all -- the limiter disabling itself under exactly the load it exists for.
    The child must not run.
    """
    monkeypatch.chdir(repository)
    common = coordination_lease.git_common_dir(repository)
    lease_dir = common / coordination_lease.LEASE_DIRECTORY
    lease_dir.mkdir(mode=coordination_lease.LEASE_DIRECTORY_MODE, parents=True, exist_ok=True)
    sentinel = tmp_path / "the-child-ran"
    # The admission path passes a budget scaled from the wait budget with a 30s floor,
    # so both must shrink for the exhaustion to be reachable inside a test.
    monkeypatch.setenv(coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV, "1")
    monkeypatch.setattr(
        coordination_lease, "MINIMUM_RUN_SLOT_DECISION_LOCK_SECONDS", 0.2
    )

    # A second open file description contends with this one even in-process, so the
    # wrapper meets a genuinely held lock rather than a mocked failure.
    with coordination_lease.coordination_lock(lease_dir, "coordination.lock"):
        code = coordination_lease.main(
            [
                "with-lease",
                "--",
                sys.executable,
                "-c",
                f"open({str(sentinel)!r}, 'w').close()",
            ]
        )

    assert code == 75
    captured = capsys.readouterr().err
    assert "WORKTREE_LEASE_DID_NOT_RUN" in captured
    assert "did not run" in captured
    assert not sentinel.exists(), "the child ran despite an unavailable slot decision"


def test_bootstrap_participates_in_no_lease() -> None:
    """The matrix's one non-participant, asserted so a future claim is deliberate.

    The previous plan claimed `bootstrap.py` published a claim when it never did, and
    froze at Done with that statement in it. The disposition is now falsifiable:
    bootstrap runs `npm ci --prefix`, which is per-worktree and concurrently safe, so
    it takes no claim. Adding one here should redden this test and force the matrix to
    be updated with it.
    """
    source = Path(coordination_lease.__file__).resolve().parent / "bootstrap.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(f"{node.module or ''}.{alias.name}" for alias in node.names)

    leasing = {name for name in imported if "coordination_lease" in name}
    assert not leasing, f"bootstrap.py now imports a lease module: {sorted(leasing)}"
    assert "coordination_lease" not in source.read_text(encoding="utf-8")


@pytest.mark.parametrize("child_code", [0, 23])
def test_a_failing_release_cannot_change_the_childs_exit_code(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    child_code: int,
) -> None:
    """AC7's exit-code integrity, in both directions.

    Teardown may not rewrite a real child outcome: a failing release must not redden a
    passing child, and it must not mask a failing one either. Both directions are
    parameterised because a wrapper that swallowed every failure would satisfy the
    first on its own.
    """
    monkeypatch.chdir(repository)

    def exploding_release(self: object) -> None:
        raise coordination_lease.ClaimStoreUnavailable("release refused")

    monkeypatch.setattr(coordination_lease.RunSlotClaim, "release", exploding_release)
    monkeypatch.setattr(coordination_lease.WorktreeClaim, "release", exploding_release)

    assert coordination_lease.main(
        ["with-lease", "--", sys.executable, "-c", f"raise SystemExit({child_code})"]
    ) == child_code
    assert "release failed" in capsys.readouterr().err


def test_a_marker_naming_no_live_claim_cannot_disable_the_limiter(
    repository: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC8: a stale export or a crashed run's leftover is not a free pass.

    Nesting is recognised only when the inherited marker names a claim still live in
    the same scope. The marker here names a claim file that really exists and whose
    lock is free -- a crashed run's leftover, which is the case that matters: a marker
    naming nothing at all is caught by the existence check alone, so a test using one
    cannot tell whether the liveness half of this clause is implemented.
    """
    monkeypatch.chdir(repository)
    budgets = {
        coordination_lease.MAX_CONCURRENT_RUNS_ENV: "1",
        coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV: "1",
    }
    for name, value in budgets.items():
        monkeypatch.setenv(name, value)
    common = coordination_lease.git_common_dir(repository)
    holder = coordination_lease.acquire_run_slot(common, environ=budgets)
    lease_dir = coordination_lease.read_lease_directory(common)
    assert lease_dir is not None
    leftover_token = "f" * 32
    leftover = coordination_lease._run_claim_path(
        lease_dir, coordination_lease.ClaimRole.RUN_SLOT, leftover_token
    )
    coordination_lease._unlock_and_close(
        coordination_lease.publish_claim_candidate(
            lease_dir,
            leftover,
            coordination_lease._run_claim_payload(leftover_token, common),
        )
    )
    assert leftover.exists()
    try:
        monkeypatch.setenv(
            coordination_lease.RUN_SLOT_NESTING_MARKER_ENV, leftover_token
        )
        assert coordination_lease.main(
            ["with-lease", "--", sys.executable, "-c", "raise SystemExit(0)"]
        ) == 75
    finally:
        holder.release()
    assert "WORKTREE_LEASE_DID_NOT_RUN" in capsys.readouterr().err


def test_an_unusable_store_warns_and_still_runs_the_wrapped_child(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """AC9: the lease may degrade, but it may not fail the job."""
    monkeypatch.chdir(repository)
    common = coordination_lease.git_common_dir(repository)
    # A regular file where the lease directory belongs: unusable, not contended.
    (common / coordination_lease.LEASE_DIRECTORY).write_text("not a directory", encoding="utf-8")
    sentinel = tmp_path / "the-child-ran"

    assert coordination_lease.main(
        [
            "with-lease",
            "--",
            sys.executable,
            "-c",
            f"open({str(sentinel)!r}, 'w').close()",
        ]
    ) == 0

    assert sentinel.exists()
    assert "running child unleased" in capsys.readouterr().err


def test_a_live_exclusive_claim_refuses_the_wrapper_with_the_reserved_code(
    repository: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A mutator may not run while cleanup holds the worktree.

    The wait budget must reach this wait too: it was hardcoded to the default, so a
    configured budget shortened only the admission wait and this case blocked for
    ninety minutes instead of refusing. A one-second budget proves the plumbing.
    """
    monkeypatch.chdir(repository)
    monkeypatch.setenv(coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV, "1")
    common = coordination_lease.git_common_dir(repository)
    holder = coordination_lease.acquire_exclusive(common, repository)
    try:
        assert coordination_lease.main(
            ["with-lease", "--", sys.executable, "-c", "raise SystemExit(0)"]
        ) == 75
    finally:
        holder.release()
    captured = capsys.readouterr().err
    assert "WORKTREE_LEASE_DID_NOT_RUN" in captured
    assert "did not run" in captured
