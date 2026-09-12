"""Pytest coverage for the new-RFC ordinal allocator."""

import importlib.util
import os
import pathlib
import subprocess
import sys
import time

import pytest

sys.dont_write_bytecode = True

SCRIPTS = pathlib.Path(__file__).resolve().parents[3] / ".apm/skills/new-rfc/scripts"
SPEC = importlib.util.spec_from_file_location("new_rfc_next_ordinal", SCRIPTS / "next-ordinal.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

ADR_SCRIPT = SCRIPTS.parents[1] / "new-adr/scripts/next-ordinal.py"


def run_check(directory: pathlib.Path) -> int:
    """Run the check mode without adding another module loader."""
    return MODULE.main(["--check", os.fspath(directory)])


def run_git(arguments: list[str | pathlib.Path], directory: pathlib.Path) -> None:
    """Run a local Git setup command for an integration fixture."""
    subprocess.run(
        ["git", *arguments],
        cwd=directory,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )


def remote_checkout(tmp_path: pathlib.Path, directory_name: str = "records") -> pathlib.Path:
    """Build a clone whose fetched remote has a newer record than its tree.

    Defaults to a SUBDIRECTORY, not the repository root. Git resolves a
    pathspec relative to the current directory, so a root-only fixture passes
    against an implementation that looks for the directory nested under
    itself and matches nothing — which is how every real caller is shaped.
    """
    origin = tmp_path / "origin"
    origin.mkdir()
    run_git(["init"], origin)
    origin_directory = origin / directory_name
    origin_directory.mkdir(exist_ok=True)
    (origin_directory / "0001-a.md").touch()
    run_git(["add", "--all"], origin)
    run_git(
        [
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "seed",
        ],
        origin,
    )

    checkout = tmp_path / "checkout"
    run_git(["clone", os.fspath(origin), os.fspath(checkout)], tmp_path)
    (origin_directory / "0009-b.md").touch()
    run_git(["add", "--all"], origin)
    run_git(
        [
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "remote record",
        ],
        origin,
    )
    run_git(["fetch", "origin"], checkout)

    checkout_directory = checkout / directory_name
    (checkout_directory / "0001-a.md").unlink()
    return checkout_directory


def assert_next_output(
    directory: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Assert the command-style interface reports the remote-inclusive result."""
    assert MODULE.main([os.fspath(directory)]) == 0
    assert capsys.readouterr().out == "0010\n"


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        ([], 1),
        (["README.md", "index.html"], 1),
        (["0001-foo.md", "0002-bar.md", "0007-baz.md", "README.md"], 8),
        (["0099-foo.md", "00099-bar.md", "0010-baz.md"], 100),
        (["12345-foo.md"], 12346),
        (["0042.md", "0042foo.md", "42-foo.md"], 43),
    ],
)
def test_next_ordinal_from_existing_names(
    tmp_path: pathlib.Path,
    names: list[str],
    expected: int,
) -> None:
    """The largest complete numeric prefix determines the next ordinal."""
    for name in names:
        (tmp_path / name).touch()
    assert MODULE.next_ordinal(tmp_path) == expected


def test_missing_directory_starts_at_one(tmp_path: pathlib.Path) -> None:
    """A directory that does not yet exist starts at ordinal one."""
    assert MODULE.next_ordinal(tmp_path / "does-not-exist") == 1


def test_next_ordinal_unions_working_tree_and_remote_default_branch(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A fetched remote record remains reserved after local deletion."""
    assert_next_output(remote_checkout(tmp_path), capsys)


@pytest.mark.parametrize(
    "case", ["not-repository", "no-remote", "unset-remote-head"]
)
def test_next_ordinal_git_metadata_fallbacks_keep_successful_local_answer(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str], case: str
) -> None:
    """Unavailable remote metadata leaves the command successful and local."""
    if case == "not-repository":
        directory = tmp_path / "records"
        directory.mkdir()
    else:
        repository = tmp_path / "repository"
        repository.mkdir()
        run_git(["init"], repository)
        directory = repository / "records"
        directory.mkdir()
        if case == "unset-remote-head":
            run_git(
                ["remote", "add", "origin", "https://example.invalid/origin.git"],
                repository,
            )
    (directory / "0002-local.md").touch()

    assert MODULE.main([os.fspath(directory)]) == 0
    assert capsys.readouterr().out == "0003\n"


def test_next_ordinal_without_git_keeps_successful_local_answer(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A missing Git executable is a local-only allocation, not a command failure."""
    (tmp_path / "0002-local.md").touch()
    monkeypatch.setenv("PATH", "")

    assert MODULE.main([os.fspath(tmp_path)]) == 0
    assert capsys.readouterr().out == "0003\n"


def test_next_ordinal_times_out_blocking_git_and_keeps_local_answer(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A Git process that never responds cannot block allocation indefinitely."""
    blocking_bin = tmp_path / "bin"
    blocking_bin.mkdir()
    blocking_git = blocking_bin / "git"
    blocking_git.write_text("#!/bin/sh\nexec /bin/sleep 30\n", encoding="utf-8")
    blocking_git.chmod(0o755)
    (tmp_path / "0002-local.md").touch()
    monkeypatch.setenv("PATH", os.fspath(blocking_bin))

    started = time.monotonic()
    assert MODULE.main([os.fspath(tmp_path)]) == 0
    elapsed = time.monotonic() - started
    assert elapsed < MODULE._GIT_TIMEOUT_SECONDS + 1
    assert capsys.readouterr().out == "0003\n"


@pytest.mark.parametrize(
    "variable",
    [
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ],
)
def test_next_ordinal_ignores_git_redirect_environment(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    variable: str,
) -> None:
    """Repository-routing variables cannot redirect the remote record lookup."""
    directory = remote_checkout(tmp_path)
    decoy = tmp_path / "decoy"
    decoy.mkdir()
    run_git(["init"], decoy)
    (decoy / "9999-decoy.md").touch()
    run_git(["add", "--all"], decoy)
    run_git(
        [
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "decoy",
        ],
        decoy,
    )
    values = {
        "GIT_DIR": decoy / ".git",
        "GIT_WORK_TREE": decoy,
        "GIT_COMMON_DIR": decoy / ".git",
        "GIT_OBJECT_DIRECTORY": decoy / ".git/objects",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": decoy / ".git/objects",
    }
    monkeypatch.setenv(variable, os.fspath(values[variable]))

    assert_next_output(directory, capsys)


def test_next_ordinal_unions_remote_when_records_sit_at_the_repository_root(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Records kept at the repository root union the same way."""
    assert_next_output(remote_checkout(tmp_path, "."), capsys)


def test_next_ordinal_treats_pathspec_magic_directory_name_literally(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A record directory named like a Git pathspec still selects itself only."""
    assert_next_output(remote_checkout(tmp_path, ":(glob)records"), capsys)


def test_check_seeded_collision_is_red_before_clean_cases(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A duplicate record ordinal makes the check fail."""
    (tmp_path / "0001-first.md").touch()
    (tmp_path / "0001-second.md").touch()

    assert run_check(tmp_path) == 1
    assert "duplicate ordinal 0001" in capsys.readouterr().err


def test_check_reports_every_duplicate(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The report contains every collided ordinal and its record names."""
    for name in ["0001-alpha.md", "0001-beta.md", "0002-gamma.md", "0002-delta.md"]:
        (tmp_path / name).touch()

    assert run_check(tmp_path) == 1
    assert capsys.readouterr().err == (
        "duplicate ordinal 0001: 0001-alpha.md, 0001-beta.md\n"
        "duplicate ordinal 0002: 0002-delta.md, 0002-gamma.md\n"
    )


def test_check_ignores_companion_directory_and_research_file(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Companions with a record's prefix do not make a collision."""
    (tmp_path / "0001-record.md").touch()
    (tmp_path / "0001-notes").mkdir()
    (tmp_path / "0001-record-research.md").touch()

    assert run_check(tmp_path) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        (["0042.md", "0042-other.md"], {42: ["0042-other.md", "0042.md"]}),
        (["12345-foo.md", "12345-bar.md"], {12345: ["12345-bar.md", "12345-foo.md"]}),
        (["42-foo.md", "42-bar.md"], {}),
        (["0042foo.md", "0042-bar.md"], {}),
    ],
)
def test_duplicate_ordinals_uses_the_strict_record_prefix(
    tmp_path: pathlib.Path, names: list[str], expected: dict[int, list[str]]
) -> None:
    """Only four-or-more-digit prefixes ending in a dash or dot are records."""
    for name in names:
        (tmp_path / name).touch()
    assert MODULE.duplicate_ordinals(tmp_path) == expected


def test_duplicate_ordinals_returns_empty_mapping_for_clean_directory(tmp_path: pathlib.Path) -> None:
    """The helper exposes a clean result as an empty mapping."""
    (tmp_path / "0001-record.md").touch()
    assert MODULE.duplicate_ordinals(tmp_path) == {}


@pytest.mark.parametrize(
    "target_kind", ["missing", "file"], ids=["missing-directory", "regular-file"]
)
def test_check_refuses_non_directory_targets(
    tmp_path: pathlib.Path, target_kind: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """A target that cannot be a complete directory scan fails closed."""
    target = tmp_path / "target"
    if target_kind == "file":
        target.touch()

    assert run_check(target) == 1
    assert "could not inspect" in capsys.readouterr().err


def test_check_refuses_unenumerable_directory(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Losing directory read permission is an inspection failure."""
    target = tmp_path / "unreadable"
    target.mkdir()
    target.chmod(0)
    try:
        assert run_check(target) == 1
    finally:
        target.chmod(0o700)
    assert "could not inspect" in capsys.readouterr().err


def test_check_refuses_record_looking_symlink(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A record-shaped symlink is an integrity failure."""
    target = tmp_path / "0001-link.md"
    target.symlink_to(tmp_path / "outside.md")

    assert run_check(tmp_path) == 1
    assert "record-looking symlink" in capsys.readouterr().err


def test_check_refuses_entry_that_cannot_be_classified(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An entry classification error cannot produce a clean result."""
    target = tmp_path / "0001-uninspectable.md"
    target.touch()
    original_is_symlink = MODULE.Path.is_symlink

    def raise_for_target(path: pathlib.Path) -> bool:
        if path == target:
            raise OSError("classification denied")
        return original_is_symlink(path)

    monkeypatch.setattr(MODULE.Path, "is_symlink", raise_for_target)
    assert run_check(tmp_path) == 1
    assert "cannot classify entry" in capsys.readouterr().err


def test_shipped_adr_and_rfc_scripts_are_byte_identical() -> None:
    """The two published copies stay synchronized."""
    assert (SCRIPTS / "next-ordinal.py").read_bytes() == ADR_SCRIPT.read_bytes()
