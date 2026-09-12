"""Pytest coverage for the new-RFC ordinal allocator."""

import importlib.util
import os
import pathlib
import sys

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
