"""Pytest coverage for the new-RFC ordinal allocator."""

import importlib.util
import pathlib
import sys

import pytest

sys.dont_write_bytecode = True

SCRIPTS = pathlib.Path(__file__).resolve().parents[3] / ".apm/skills/new-rfc/scripts"
SPEC = importlib.util.spec_from_file_location("new_rfc_next_ordinal", SCRIPTS / "next-ordinal.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


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
