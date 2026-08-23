"""T11: Integration test for ``agentbundle install --scope local``.

Full install → verify → uninstall cycle for the local scope.  Uses a
fixture catalogue under ``tests/fixtures/local_scope/``.

Test matrix:
- Happy path (install + list-installed + uninstall): files appear in tree,
  git-invisible, exclude block written; uninstall removes files and block.
- State schema version.
- No seeds written.
- Same-scope reinstall refused.
- repo↔local mutual exclusion (force-immune).
- Docstring content checks.
- Rollback: exclude block and file state restored on write failure.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURE_CATALOGUE = (
    Path(__file__).parent.parent / "fixtures" / "local_scope" / "catalogue"
)
PACK_NAME = "local-test-pack"
_ADAPTER = "claude-code"

# The claude-code adapter projects .apm/skills/<name>/SKILL.md to
# .claude/skills/<name>/SKILL.md — assert this file exists after install.
_EXPECTED_SKILL_RELPATH = ".claude/skills/local-test/SKILL.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _git_init(repo: Path) -> None:
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Test"], check=True
    )


def _install_args(repo: Path, *, scope: str = "local", adapter: str | None = _ADAPTER,
                  force: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        pack=PACK_NAME,
        catalogue=str(FIXTURE_CATALOGUE),
        output=str(repo),
        scope=scope,
        adapter=adapter,
        force=False,
        force_merge=False,
        dry_run=False,
        yes=True,
        emit_install_routes=False,
    )


def _uninstall_args(repo: Path, *, scope: str = "local",
                    adapter: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        pack=PACK_NAME,
        root=str(repo),
        scope=scope,
        adapter=adapter,
        dry_run=False,
        yes=True,
    )


def _git_status(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "status", "--short"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _exclude_content(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--git-path", "info/exclude"],
        capture_output=True,
        text=True,
    )
    exclude_raw = result.stdout.strip()
    exclude_path = Path(exclude_raw) if Path(exclude_raw).is_absolute() else repo / exclude_raw
    return exclude_path.read_text() if exclude_path.exists() else ""


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    return repo


# ---------------------------------------------------------------------------
# T11a: Happy path install cycle
# ---------------------------------------------------------------------------


def test_install_local_happy_path(git_repo: Path) -> None:
    """Files appear in tree, git-invisible, list-installed shows local row."""
    import io

    from agentbundle.commands.install import run as install_run

    out = io.StringIO()
    import contextlib
    with contextlib.redirect_stdout(out):
        rc = install_run(_install_args(git_repo))
    assert rc == 0, f"install failed: {out.getvalue()}"

    install_output = out.getvalue()

    # AC: files appear in working tree (guards against silent-zero-file hazard)
    skill_path = git_repo / _EXPECTED_SKILL_RELPATH
    assert skill_path.exists(), (
        f"Expected skill file not found at {skill_path}; "
        f"install output: {install_output!r}"
    )

    # AC: git status --short is empty (files not visible to git)
    status = _git_status(git_repo)
    assert status == "", f"Expected clean git status; got: {status!r}"

    # AC: exclude block contains the keyed pack block
    exclude = _exclude_content(git_repo)
    assert f"agentbundle:local:{PACK_NAME}" in exclude, (
        f"Expected exclude block in info/exclude; got: {exclude!r}"
    )

    # AC: install line contains "@ local (excluded via"
    assert "@ local (excluded via" in install_output, (
        f"Expected local exclude line; got: {install_output!r}"
    )

    # State file contains schema-version = "0.4"
    state_path = git_repo / ".agentbundle-local-state.toml"
    assert state_path.exists(), "Local state file should exist"
    state_content = state_path.read_text()
    assert 'schema-version = "0.4"' in state_content, (
        f"Expected schema-version = '0.4' in state file; got: {state_content!r}"
    )

    # No seeds written (AGENTS.md and docs/CHARTER.md absent)
    assert not (git_repo / "AGENTS.md").exists(), "AGENTS.md should not be written at local scope"
    assert not (git_repo / "docs" / "CHARTER.md").exists(), (
        "docs/CHARTER.md should not be written at local scope"
    )


def test_install_local_list_installed_shows_row(git_repo: Path) -> None:
    """list-installed --scope local includes the pack row."""
    import contextlib
    import io

    from agentbundle.commands.install import run as install_run
    from agentbundle.commands.list_installed import run as list_run

    rc = install_run(_install_args(git_repo))
    assert rc == 0

    out = io.StringIO()
    list_args = SimpleNamespace(
        root=str(git_repo),
        scope="local",
        format="table",
    )
    with contextlib.redirect_stdout(out):
        rc2 = list_run(list_args)
    assert rc2 == 0
    output = out.getvalue()
    assert PACK_NAME in output, f"Pack not in list-installed output: {output!r}"


# ---------------------------------------------------------------------------
# T11b: Uninstall cycle
# ---------------------------------------------------------------------------

def test_uninstall_local_cleans_up(git_repo: Path) -> None:
    """Uninstall removes files, strips exclude block, deletes state file."""
    from agentbundle.commands.install import run as install_run
    from agentbundle.commands.uninstall import run as uninstall_run

    rc = install_run(_install_args(git_repo))
    assert rc == 0

    skill_path = git_repo / _EXPECTED_SKILL_RELPATH
    assert skill_path.exists()

    rc2 = uninstall_run(_uninstall_args(git_repo))
    assert rc2 == 0

    # Files removed
    assert not skill_path.exists(), "Skill file should be removed after uninstall"

    # Exclude block stripped
    exclude = _exclude_content(git_repo)
    assert f"agentbundle:local:{PACK_NAME}" not in exclude, (
        f"Exclude block should be stripped after uninstall; exclude: {exclude!r}"
    )

    # git status still clean
    status = _git_status(git_repo)
    assert status == "", f"Expected clean git status after uninstall; got: {status!r}"

    # State file deleted (was the only pack)
    state_path = git_repo / ".agentbundle-local-state.toml"
    assert not state_path.exists(), "Empty state file should be deleted"


# ---------------------------------------------------------------------------
# T11c: same-scope reinstall refused
# ---------------------------------------------------------------------------

def test_same_scope_reinstall_refused(git_repo: Path) -> None:
    """Reinstalling the same pack/adapter at local scope is refused."""
    import contextlib
    import io

    from agentbundle.commands.install import run as install_run

    rc1 = install_run(_install_args(git_repo))
    assert rc1 == 0

    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc2 = install_run(_install_args(git_repo))
    assert rc2 != 0, "Reinstall of same adapter should be refused"
    assert "already installed" in err.getvalue().lower(), (
        f"Expected 'already installed' error; got: {err.getvalue()!r}"
    )


# ---------------------------------------------------------------------------
# T11d: repo↔local mutual exclusion (force-immune)
# ---------------------------------------------------------------------------

def test_local_refused_when_repo_installed(git_repo: Path) -> None:
    """Installing at local scope is refused when already at repo scope."""
    import contextlib
    import io

    from agentbundle.commands.install import run as install_run

    # Install at repo scope first
    rc1 = install_run(_install_args(git_repo, scope="repo"))
    assert rc1 == 0

    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc2 = install_run(_install_args(git_repo, scope="local"))
    assert rc2 != 0, "Local install should be refused when repo-installed"


def test_repo_refused_when_local_installed(git_repo: Path) -> None:
    """Installing at repo scope is refused when already at local scope."""
    import contextlib
    import io

    from agentbundle.commands.install import run as install_run

    rc1 = install_run(_install_args(git_repo, scope="local"))
    assert rc1 == 0

    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc2 = install_run(_install_args(git_repo, scope="repo"))
    assert rc2 != 0, "Repo install should be refused when local-installed"


# ---------------------------------------------------------------------------
# T11e: docstring content checks
# ---------------------------------------------------------------------------

def test_write_exclude_block_docstring_ac26(tmp_path: Path) -> None:
    """write_exclude_block docstring documents the concurrent-write limitation."""
    from agentbundle.local_exclude import write_exclude_block
    docstring = write_exclude_block.__doc__ or ""
    # Key phrase
    assert any(
        phrase in docstring
        for phrase in ("lost-update", "concurrent", "last-writer")
    ), f"concurrent-write limitation not documented in docstring; got: {docstring[:200]!r}"


def test_write_exclude_block_docstring_ac27(tmp_path: Path) -> None:
    """write_exclude_block docstring documents the cross-worktree side-effect."""
    from agentbundle.local_exclude import write_exclude_block
    docstring = write_exclude_block.__doc__ or ""
    # Key phrase (cross-worktree)
    assert "linked worktrees" in docstring, (
        f"cross-worktree side-effect not documented in docstring; got: {docstring[:200]!r}"
    )


# ---------------------------------------------------------------------------
# T11f: Rollback — exclude block and files restored on write failure
# ---------------------------------------------------------------------------

def test_rollback_on_write_failure(git_repo: Path) -> None:
    """If state write fails, exclude block and projected files are rolled back.

    Injects a RuntimeError into persist_state_locked; verifies that:
    - install exits non-zero (exception propagated → rc = 1)
    - the projected skill file is gone (file rollback ran)
    - the exclude block is absent (exclude rollback ran)
    - the local state file does not exist
    """
    from agentbundle import statelock
    from agentbundle.commands.install import run as install_run
    from agentbundle.local_exclude import get_exclude_path, snapshot_exclude

    exclude_path = get_exclude_path(git_repo)
    prior_exclude = snapshot_exclude(exclude_path)

    # Patch persist_state_locked to raise on first call so the state write fails
    # after files have been projected to disk (file writes happen before state write).
    _original_persist = statelock.persist_state_locked
    call_count = [0]

    def _failing_persist(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("simulated state write failure")
        return _original_persist(*args, **kwargs)

    import contextlib
    import io
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        try:
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(statelock, "persist_state_locked", _failing_persist)
                rc = install_run(_install_args(git_repo))
        except RuntimeError:
            rc = 1  # RuntimeError propagates after rollback (re-raised by install)

    assert rc != 0, "install should exit non-zero when state write fails"

    # Projected files rolled back
    skill_path = git_repo / _EXPECTED_SKILL_RELPATH
    assert not skill_path.exists(), (
        "Projected skill file should be removed by rollback; "
        f"skill_path={skill_path}, err={err.getvalue()!r}"
    )

    # Local state file never committed
    state_path = git_repo / ".agentbundle-local-state.toml"
    assert not state_path.exists(), "Local state file should not exist after rollback"

    # Exclude block rolled back to prior state.
    # snapshot_exclude returns bytes | None (None = file was absent before install).
    # After rollback: if prior was None the file should be gone; if prior was bytes
    # the file should contain those bytes.
    if prior_exclude is None:
        assert not exclude_path.exists(), (
            "Exclude file should be absent after rollback (was absent before install)"
        )
    else:
        current_exclude = exclude_path.read_bytes() if exclude_path.exists() else b""
        assert current_exclude == prior_exclude, (
            "Exclude block should be restored to pre-install state after rollback"
        )


# ---------------------------------------------------------------------------
# AC10 / AC12b — local-scope pre-flight refusals
#
# Local scope promises to leave no trace: files are git-invisible via an
# exclude block, and uninstall restores the tree exactly. Each case below is
# one where that promise cannot be kept, so the install must refuse BEFORE
# writing anything. All three are --force-immune: --force cannot make a
# deletion reversible.
# ---------------------------------------------------------------------------


def _assert_no_footprint(repo: Path) -> None:
    """A refusal must leave nothing of *ours* behind.

    Deliberately does not assert the projected path is absent: several of these
    cases refuse precisely because a file is already sitting there, and that
    file belongs to someone else. What must be absent is anything this tool
    would have created — the exclude block and the local state file.
    """
    assert "agentbundle:local" not in _exclude_content(repo), (
        "a refusal left an exclude block behind"
    )
    assert not (repo / ".agentbundle-local-state.toml").exists(), (
        "a refusal left a state file behind"
    )


def test_ac10a_refuses_when_a_target_is_tracked_by_git(tmp_path, capsys) -> None:
    """A tracked target cannot be taken over.

    Writing over it makes the file dirty in git while the exclude block claims
    it is invisible, and uninstall would delete a file the repository owns.
    """
    from agentbundle.commands.install import run as install_run
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    target = repo / _EXPECTED_SKILL_RELPATH
    target.parent.mkdir(parents=True)
    target.write_text("committed content\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "seed"],
        check=True,
    )

    assert install_run(_install_args(repo)) == 1
    err = capsys.readouterr().err
    assert "tracked by git" in err
    assert "--force" in err, "the message must say the refusal is not forceable"
    assert target.read_text(encoding="utf-8") == "committed content\n", (
        "the tracked file was modified by a run that refused"
    )


def test_ac10a_refusal_is_force_immune(tmp_path, capsys) -> None:
    from agentbundle.commands.install import run as install_run
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    target = repo / _EXPECTED_SKILL_RELPATH
    target.parent.mkdir(parents=True)
    target.write_text("committed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "seed"],
        check=True,
    )

    args = _install_args(repo)
    args.force = True
    assert install_run(args) == 1
    assert "tracked by git" in capsys.readouterr().err


def test_ac10b_refuses_an_untracked_unowned_target(tmp_path, capsys) -> None:
    from agentbundle.commands.install import run as install_run
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    target = repo / _EXPECTED_SKILL_RELPATH
    target.parent.mkdir(parents=True)
    target.write_text("someone else's file\n", encoding="utf-8")

    assert install_run(_install_args(repo)) == 1
    err = capsys.readouterr().err
    assert "not owned by any agentbundle install" in err
    assert target.read_text(encoding="utf-8") == "someone else's file\n"
    _assert_no_footprint(repo)


def test_ac10b_identical_content_does_not_grant_ownership(tmp_path, capsys) -> None:
    """The case the AC calls out by name.

    A pre-existing file whose bytes happen to match the projection is still not
    ours. Treating content equality as ownership would delete it on uninstall,
    breaking exact restoration for a file this tool never created.
    """
    from agentbundle.commands.install import run as install_run
    from agentbundle.commands.uninstall import run as uninstall_run
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)

    # Install once to learn the exact projected bytes, then start clean.
    assert install_run(_install_args(repo)) == 0
    projected = (repo / _EXPECTED_SKILL_RELPATH).read_text(encoding="utf-8")
    assert uninstall_run(_uninstall_args(repo)) == 0

    target = repo / _EXPECTED_SKILL_RELPATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(projected, encoding="utf-8")  # byte-identical, still not ours

    assert install_run(_install_args(repo)) == 1
    assert "Identical content would not make them ours" in capsys.readouterr().err
    assert target.exists(), "the unowned file was removed by a refusing run"


def test_a_clean_repo_still_installs(tmp_path) -> None:
    """The guards must not refuse the ordinary case."""
    from agentbundle.commands.install import run as install_run
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    assert install_run(_install_args(repo)) == 0
    assert (repo / _EXPECTED_SKILL_RELPATH).exists()
    assert _git_status(repo) == "", "a local install must stay git-invisible"


def test_reinstalling_over_our_own_files_is_not_refused(tmp_path) -> None:
    """Ownership is what the guard keys on, not mere existence.

    Without this, AC10b would refuse every legitimate reinstall — the files it
    is looking at are the ones we put there.
    """
    from agentbundle.commands.install import run as install_run
    from agentbundle.commands.uninstall import run as uninstall_run
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    assert install_run(_install_args(repo)) == 0
    assert uninstall_run(_uninstall_args(repo)) == 0
    assert install_run(_install_args(repo)) == 0, "a clean reinstall was refused"


def test_ac12b_refuses_a_path_owned_by_a_different_repo_scope_pack(
    tmp_path, capsys
) -> None:
    """Path-level cross-scope collision, across DIFFERENT packs.

    The pack-level mutual exclusion upstream (AC11/AC12) only catches the *same*
    pack installed at both scopes. Two different packs projecting the same path
    slipped through entirely, and the local install would silently take
    ownership of a file the repo-scope pack owns — so uninstalling either would
    delete the other's file.
    """
    from agentbundle.commands.install import run as install_run

    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)

    # A *different* pack already owns the path this install would project.
    (repo / ".agentbundle-state.toml").write_text(
        'schema-version = "0.4"\n\n'
        '[pack.some-other-pack.adapters.claude-code]\n'
        'installed-version = "1.0.0"\n'
        'source = "/nonexistent"\n'
        'install-route = "cli"\n'
        'scope = "repo"\n'
        'user-root = "~/.agentbundle"\n'
        'primitives = ["skill"]\n\n'
        '[pack.some-other-pack.adapters.claude-code.files]\n'
        f'"{_EXPECTED_SKILL_RELPATH}" = {{ from-pack-version = "1.0.0", sha = "x" }}\n',
        encoding="utf-8",
    )

    assert install_run(_install_args(repo)) == 1
    err = capsys.readouterr().err
    assert "already owned by" in err
    assert "some-other-pack" in err, "the message must name the colliding owner"
    assert _EXPECTED_SKILL_RELPATH in err, "the message must name the colliding path"
    assert "--force" in err
    _assert_no_footprint(repo)
