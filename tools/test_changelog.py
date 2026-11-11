# STUB: AC3 — a filename stem that differs from the envelope id is refused
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


_SCRIPT = Path(__file__).with_name("changelog.py")


def _lint_git_ignore():
    """Load the repository's one-subprocess gitignore resolver by path."""
    source = Path(__file__).with_name("lint_git_ignore.py")
    spec = importlib.util.spec_from_file_location("lint_git_ignore", source)
    assert spec is not None and spec.loader is not None
    module = sys.modules.get("lint_git_ignore") or importlib.util.module_from_spec(spec)
    if "lint_git_ignore" not in sys.modules:
        sys.modules["lint_git_ignore"] = module
        spec.loader.exec_module(module)
    return module


_SPEC = importlib.util.spec_from_file_location("product_changelog", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
changelog = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = changelog
_SPEC.loader.exec_module(changelog)


def test_validate_fragment_refuses_mismatched_stem() -> None:
    with TemporaryDirectory() as temp_dir:
        fragment = Path(temp_dir) / "11111111-1111-4111-8111-111111111111.md"
        fragment.write_text(
            """+++
schema = 1
id = "22222222-2222-4222-8222-222222222222"
anchor = "core300--2026-09-29-22222222222242228222222222222222"
date = 2026-09-29
[[packages]]
name = "core"
version = "3.0.0"
+++
## Highlights
- Adds per-update changelog sources.
""",
            encoding="utf-8",
        )

        try:
            changelog.validate_fragment(fragment)
        except changelog.FragmentValidationError as error:
            message = str(error)
        else:
            raise AssertionError("mismatched stem was accepted")

    assert str(fragment) in message
    assert "id" in message
    assert "filename stem must equal envelope id" in message


# ruff: noqa: I001, E402, UP022 -- approved construction stubs are byte-pinned.
def _temporary_directory():
    """Return a temp directory that tolerates this host's rmdir denial."""
    return __import__("tempfile").TemporaryDirectory(ignore_cleanup_errors=True)


TemporaryDirectory = _temporary_directory  # noqa: F811
_OS = __import__("os")


VALID_ID = "11111111-1111-4111-8111-111111111111"
VALID_ANCHOR = "core300--2026-09-29-11111111111141118111111111111111"


def _fragment_text(
    *,
    fragment_id: str = VALID_ID,
    anchor: str = VALID_ANCHOR,
    date: str = "2026-09-29",
    packages: str = '[[packages]]\nname = "core"\nversion = "3.0.0"',
    body: str = "## Highlights\n- Adds per-update changelog sources.\n",
    extra: str = "",
) -> str:
    return (
        "+++\n"
        "schema = 1\n"
        f'id = "{fragment_id}"\n'
        f'anchor = "{anchor}"\n'
        f"date = {date}\n"
        f"{packages}\n"
        f"{extra}"
        "+++\n"
        f"{body}"
    )


def _write_fragment(directory: Path, name: str = f"{VALID_ID}.md", **kwargs) -> Path:
    fragment = directory / name
    fragment.parent.mkdir(parents=True, exist_ok=True)
    fragment.write_text(_fragment_text(**kwargs), encoding="utf-8")
    return fragment


def _assert_refused(fragment: Path, field: str, expected: str, action=None) -> None:
    try:
        (action or changelog.validate_fragment)(fragment)
    except changelog.FragmentValidationError as error:
        message = str(error)
    else:
        raise AssertionError(f"{field} defect was accepted")
    assert str(fragment) in message
    assert field in message
    assert expected in message


def test_validate_fragment_accepts_well_formed_fragment(tmp_path: Path) -> None:
    fragment = _write_fragment(tmp_path)

    record = changelog.validate_fragment(fragment)

    assert record.id == VALID_ID
    assert record.anchor == VALID_ANCHOR
    assert record.date == "2026-09-29"
    assert record.packages == [{"name": "core", "version": "3.0.0"}]
    assert "Highlights" in record.sections


def test_validate_fragment_refuses_identity_classes(tmp_path: Path) -> None:
    cases = [
        ("not-a-uuid", "not-a-uuid", "id", "lowercase UUIDv4 string"),
        (
            "11111111-1111-1111-8111-111111111111",
            "11111111-1111-1111-8111-111111111111",
            "id",
            "lowercase UUIDv4 string",
        ),
        (
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA",
            "id",
            "lowercase UUIDv4 string",
        ),
    ]
    for index, (name, fragment_id, field, expected) in enumerate(cases):
        fragment = _write_fragment(
            tmp_path / f"case-{index}",
            name=f"{name}.md",
            fragment_id=fragment_id,
        )
        _assert_refused(fragment, field, expected)

    duplicate = _write_fragment(tmp_path / "duplicate")
    _assert_refused(
        duplicate,
        "id",
        "unique fragment id",
        action=lambda path: changelog.validate_fragment(path, seen_ids={VALID_ID}),
    )


def test_validate_fragment_refuses_envelope_classes(tmp_path: Path) -> None:
    malformed = {
        "missing-head": "schema = 1\n+++\n",
        "missing-closing": _fragment_text().replace("+++\n## Highlights", "## Highlights"),
        "missing-field": _fragment_text().replace(f'anchor = "{VALID_ANCHOR}"\n', ""),
        "unknown-field": _fragment_text().replace("[[packages]]", 'extra = "nope"\n[[packages]]'),
        "wrong-type": _fragment_text().replace("schema = 1", 'schema = "1"'),
        "malformed-toml": _fragment_text().replace("schema = 1", "schema = "),
        "bad-schema": _fragment_text().replace("schema = 1", "schema = 2"),
    }
    expectations = {
        "missing-head": ("envelope delimiter", "file must start with +++"),
        "missing-closing": ("envelope delimiter", "closing +++ delimiter"),
        "missing-field": ("anchor", "required field"),
        "unknown-field": ("extra", "no unknown envelope fields"),
        "wrong-type": ("schema", "integer schema version 1"),
        "malformed-toml": ("envelope TOML", "well-formed TOML"),
        "bad-schema": ("schema", "schema version 1"),
    }
    for name, text in malformed.items():
        fragment = tmp_path / name / f"{VALID_ID}.md"
        fragment.parent.mkdir()
        fragment.write_text(text, encoding="utf-8")
        field, expected = expectations[name]
        _assert_refused(fragment, field, expected)


def test_validate_fragment_refuses_sink_unsafe_metadata(tmp_path: Path) -> None:
    bad_names = [" core", "co/re", "co]re", 'co\\"re', "<core>", "co\\u0001re"]
    for index, value in enumerate(bad_names):
        packages = f'[[packages]]\nname = "{value}"\nversion = "3.0.0"'
        fragment = _write_fragment(tmp_path / f"name-{index}", packages=packages)
        _assert_refused(fragment, "packages[1].name", "[A-Za-z0-9][A-Za-z0-9._-]*")

    bad_versions = [" 3.0.0", "3/0/0", "3]0", '3\\"0', "<3>", "3\\u0001"]
    for index, value in enumerate(bad_versions):
        packages = f'[[packages]]\nname = "core"\nversion = "{value}"'
        fragment = _write_fragment(tmp_path / f"version-{index}", packages=packages)
        _assert_refused(
            fragment, "packages[1].version", "[A-Za-z0-9][A-Za-z0-9._+-]*"
        )

    impossible = _write_fragment(tmp_path / "date", date="2026-02-31")
    _assert_refused(impossible, "date", "real ISO YYYY-MM-DD calendar date")

    valid = _write_fragment(
        tmp_path / "valid-version",
        packages='[[packages]]\nname = "core.lib_1"\nversion = "3.0.0-alpha_1+build-7"',
        anchor="corelib_1300-alpha_1build-7--2026-09-29-11111111111141118111111111111111",
    )
    assert changelog.validate_fragment(valid).packages[0]["version"] == "3.0.0-alpha_1+build-7"


def test_validate_fragment_refuses_anchor_mismatch(tmp_path: Path) -> None:
    fragment = _write_fragment(tmp_path, anchor="core300--2026-09-29-bad")

    _assert_refused(fragment, "anchor", "recomputed anchor")


def test_validate_fragment_refuses_body_classes(tmp_path: Path) -> None:
    cases = {
        "unknown": ("## Surprise\n- no\n", "body", "known changelog section name"),
        "duplicate": (
            "## Highlights\n- one\n## Highlights\n- two\n",
            "Highlights",
            "section appears once",
        ),
        "release": (
            "## [core][3.0.0] — 2026-09-29\n- no\n",
            "body",
            "no release-level heading",
        ),
        "absent": ("## Added\n- no\n", "Highlights", "non-empty Highlights section"),
        "empty": (
            "## Highlights\n\n## Added\n- no\n",
            "Highlights",
            "non-empty Highlights section",
        ),
    }
    for name, (body, field, expected) in cases.items():
        fragment = _write_fragment(tmp_path / name, body=body)
        _assert_refused(fragment, field, expected)


def test_validate_fragments_refuses_unsafe_entries(tmp_path: Path) -> None:
    root = tmp_path / "symlink"
    root.mkdir()

    symlink = root / f"{VALID_ID}.md"
    symlink.symlink_to(tmp_path / "missing.md")
    _assert_refused(
        symlink,
        "path",
        "bounded direct regular fragment files",
        lambda _path: changelog.validate_fragments(root),
    )
    symlink.unlink()

    root = tmp_path / "directory"
    root.mkdir()
    directory = root / f"{VALID_ID}.md"
    directory.mkdir()
    _assert_refused(
        directory,
        "path",
        "bounded direct regular fragment files",
        lambda _path: changelog.validate_fragments(root),
    )

    root = tmp_path / "fifo"
    root.mkdir()
    fifo = root / f"{VALID_ID}.md"
    if hasattr(_OS, "mkfifo"):
        _OS.mkfifo(fifo)
        _assert_refused(
            fifo,
            "path",
            "bounded direct regular fragment files",
            lambda _path: changelog.validate_fragments(root),
        )
        fifo.unlink()


def test_validate_fragments_refuses_bound_overruns(tmp_path: Path) -> None:
    root = tmp_path / "fragments"
    root.mkdir()
    _write_fragment(root)
    _write_fragment(
        root,
        name="22222222-2222-4222-8222-222222222222.md",
        fragment_id="22222222-2222-4222-8222-222222222222",
        anchor="core300--2026-09-29-22222222222242228222222222222222",
    )

    original_entries = changelog.MAX_FRAGMENT_DIR_ENTRIES
    original_files = changelog.MAX_FRAGMENT_FILES
    original_depth = changelog.MAX_FRAGMENT_DEPTH
    try:
        changelog.MAX_FRAGMENT_DIR_ENTRIES = 1
        _assert_refused(
            root,
            "entries",
            "bounded direct regular fragment files",
            changelog.validate_fragments,
        )
        changelog.MAX_FRAGMENT_DIR_ENTRIES = original_entries
        changelog.MAX_FRAGMENT_FILES = 1
        _assert_refused(
            root,
            "files",
            "bounded direct regular fragment files",
            changelog.validate_fragments,
        )
        changelog.MAX_FRAGMENT_FILES = original_files
        changelog.MAX_FRAGMENT_DEPTH = 0
        _assert_refused(
            root,
            "depth",
            "bounded direct regular fragment files",
            changelog.validate_fragments,
        )
    finally:
        changelog.MAX_FRAGMENT_DIR_ENTRIES = original_entries
        changelog.MAX_FRAGMENT_FILES = original_files
        changelog.MAX_FRAGMENT_DEPTH = original_depth


def test_validate_fragment_refuses_byte_bound_overrun(tmp_path: Path) -> None:
    fragment = _write_fragment(tmp_path)
    original = changelog.MAX_FRAGMENT_BYTES
    try:
        changelog.MAX_FRAGMENT_BYTES = 32
        _assert_refused(fragment, "per-file-bytes", "confined regular fragment file")
    finally:
        changelog.MAX_FRAGMENT_BYTES = original


def test_create_fragment_writes_uuid_anchor_and_round_trips_without_sibling_reads(
    tmp_path: Path,
) -> None:
    fragment_dir = tmp_path / "docs" / "product" / "changelog.d"
    fixed_id = "33333333-3333-4333-8333-333333333333"
    blocked_scans = []
    original_file_safety = changelog._file_safety

    class NoSiblingReadSafety:
        def list_confined_regular_files(self, *args, **kwargs):
            blocked_scans.append((args, kwargs))
            raise AssertionError("new must not enumerate sibling fragments")

    changelog._file_safety = lambda: NoSiblingReadSafety()
    try:
        created = changelog.create_fragment(
            fragment_dir,
            packages=[{"name": "core", "version": "3.0.0"}],
            fragment_date="2026-09-29",
            highlights=["Adds per-update changelog sources."],
            fragment_id=fixed_id,
        )
    finally:
        changelog._file_safety = original_file_safety

    assert blocked_scans == []
    assert created == fragment_dir / f"{fixed_id}.md"
    assert created.exists()
    text = created.read_text(encoding="utf-8")
    assert f'id = "{fixed_id}"' in text
    assert (
        'anchor = "core300--2026-09-29-33333333333343338333333333333333"'
        in text
    )
    record = changelog.validate_fragment(created)
    assert record.id == fixed_id
    assert record.anchor == "core300--2026-09-29-33333333333343338333333333333333"


def test_create_fragment_same_slug_gets_distinct_anchor_without_reading_siblings(
    tmp_path: Path,
) -> None:
    fragment_dir = tmp_path / "docs" / "product" / "changelog.d"
    first = changelog.create_fragment(
        fragment_dir,
        packages=[{"name": "core", "version": "3.0.0"}],
        fragment_date="2026-09-29",
        highlights=["First."],
        fragment_id="44444444-4444-4444-8444-444444444444",
    )

    original_file_safety = changelog._file_safety

    class NoSiblingReadSafety:
        def list_confined_regular_files(self, *args, **kwargs):
            raise AssertionError("new must not enumerate sibling fragments")

    changelog._file_safety = lambda: NoSiblingReadSafety()
    try:
        second = changelog.create_fragment(
            fragment_dir,
            packages=[{"name": "core", "version": "3.0.0"}],
            fragment_date="2026-09-29",
            highlights=["Second."],
            fragment_id="55555555-5555-4555-8555-555555555555",
        )
    finally:
        changelog._file_safety = original_file_safety

    first_record = changelog.validate_fragment(first)
    second_record = changelog.validate_fragment(second)
    assert first_record.anchor != second_record.anchor
    assert first_record.anchor.startswith("core300--2026-09-29-")
    assert second_record.anchor.startswith("core300--2026-09-29-")


def test_validate_fragment_refuses_hand_edited_anchor(tmp_path: Path) -> None:
    fragment = changelog.create_fragment(
        tmp_path,
        packages=[{"name": "core", "version": "3.0.0"}],
        fragment_date="2026-09-29",
        highlights=["Adds per-update changelog sources."],
        fragment_id="66666666-6666-4666-8666-666666666666",
    )
    text = fragment.read_text(encoding="utf-8").replace(
        "core300--2026-09-29-66666666666646668666666666666666",
        "core300--2026-09-29-edited",
    )
    fragment.write_text(text, encoding="utf-8")

    _assert_refused(
        fragment,
        "anchor",
        "recomputed anchor core300--2026-09-29-66666666666646668666666666666666",
    )


def test_changelog_new_cli_prints_created_valid_fragment(tmp_path: Path) -> None:
    import subprocess  # noqa: PLC0415
    import sys as _sys  # noqa: PLC0415

    output_dir = tmp_path / "docs" / "product" / "changelog.d"
    result = subprocess.run(
        [
            _sys.executable,
            str(_SCRIPT),
            "new",
            "--directory",
            str(output_dir),
            "--package",
            "core",
            "--version",
            "3.0.0",
            "--date",
            "2026-09-29",
            "--highlight",
            "Adds per-update changelog sources.",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    created = Path(result.stdout.strip())
    assert created.parent == output_dir
    assert created.exists()
    assert changelog.validate_fragment(created).path == created


# STUB: AC4/AC5 — a committed fragment's date cannot be changed
import re
import subprocess
from contextlib import chdir


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_validate_fragment_refuses_date_edit_after_commit(tmp_path: Path) -> None:
    fragment_id = "11111111-1111-4111-8111-111111111111"
    repo = tmp_path
    fragment_dir = repo / "docs/product/changelog.d"
    fragment_dir.mkdir(parents=True)
    fragment = fragment_dir / f"{fragment_id}.md"
    original = """+++
schema = 1
id = "11111111-1111-4111-8111-111111111111"
anchor = "core300--2026-09-28-11111111111141118111111111111111"
date = 2026-09-28
[[packages]]
name = "core"
version = "3.0.0"
+++
## Highlights
- Adds per-update changelog sources.
"""
    edited = original.replace("2026-09-28", "2026-09-29")
    fragment.write_text(original, encoding="utf-8")
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test Author")
    _git(repo, "config", "user.email", "test.invalid")
    _git(repo, "add", str(fragment.relative_to(repo)))
    _git(repo, "commit", "-m", "test: add changelog fragment")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "checkout", "-b", "feature")
    fragment.write_text(edited, encoding="utf-8")

    with chdir(repo):
        try:
            changelog.validate_fragment(fragment)
        except changelog.FragmentValidationError as error:
            message = str(error)
        else:
            raise AssertionError("committed fragment date edit was accepted")

    assert str(fragment) in message
    assert "date" in message
    assert "must not change after merge" in message


class _FakeGit:
    def __init__(
        self,
        repo: Path,
        responses: dict[tuple[str, ...], tuple[int, str, str]],
    ):
        self.repo = repo
        self.responses = responses
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, cwd: Path, *args: str):
        self.calls.append(args)
        code, stdout, stderr = self.responses.get(
            args, (99, "", f"unexpected {args!r}")
        )
        return changelog._GitResult(code, stdout, stderr)


_VALID_FRAGMENT_REL = (
    "docs/product/changelog.d/11111111-1111-4111-8111-111111111111.md"
)
_RENAMED_FRAGMENT_REL = (
    "docs/product/changelog.d/00000000-0000-4000-8000-000000000000.md"
)


def _git_responses(repo: Path, *, diff: str, base_text: str | None = None):
    responses = {
        ("rev-parse", "--show-toplevel"): (0, f"{repo}\n", ""),
        ("merge-base", "origin/main", "HEAD"): (0, "base123\n", ""),
        ("diff", "--name-status", "--find-renames", "base123", "--", _VALID_FRAGMENT_REL): (
            0,
            diff,
            "",
        ),
        ("ls-files", "--", _VALID_FRAGMENT_REL): (
            0,
            f"{_VALID_FRAGMENT_REL}\n",
            "",
        ),
    }
    if base_text is not None:
        responses[("show", f"base123:{_VALID_FRAGMENT_REL}")] = (0, base_text, "")
        responses[("show", f"base123:{_RENAMED_FRAGMENT_REL}")] = (
            0,
            base_text,
            "",
        )
    return responses


def _repo_fragment(tmp_path: Path, **kwargs) -> Path:
    repo = tmp_path
    return _write_fragment(repo / "docs/product/changelog.d", **kwargs)


def test_validate_fragment_refuses_committed_package_edit(tmp_path: Path) -> None:
    fragment = _repo_fragment(
        tmp_path,
        packages='[[packages]]\nname = "core2"\nversion = "3.0.0"',
        anchor="core2300--2026-09-29-11111111111141118111111111111111",
    )
    git = _FakeGit(
        tmp_path,
        _git_responses(
            tmp_path,
            diff="M\tdocs/product/changelog.d/11111111-1111-4111-8111-111111111111.md\n",
            base_text=_fragment_text(),
        ),
    )

    _assert_refused(
        fragment,
        "packages",
        "must not change after merge",
        lambda path: changelog.validate_fragment(path, git_runner=git),
    )


def test_validate_fragment_refuses_committed_id_edit_on_rename(tmp_path: Path) -> None:
    new_id = "77777777-7777-4777-8777-777777777777"
    fragment = _repo_fragment(
        tmp_path,
        name=f"{new_id}.md",
        fragment_id=new_id,
        anchor="core300--2026-09-29-77777777777747778777777777777777",
    )
    git = _FakeGit(
        tmp_path,
        _git_responses(
            tmp_path,
            diff=(
                "R100\tdocs/product/changelog.d/00000000-0000-4000-8000-000000000000.md"
                f"\tdocs/product/changelog.d/{new_id}.md\n"
            ),
            base_text=_fragment_text(
                fragment_id="00000000-0000-4000-8000-000000000000",
                anchor="core300--2026-09-29-00000000000040008000000000000000",
            ),
        ),
    )
    git.responses[
        (
            "diff",
            "--name-status",
            "--find-renames",
            "base123",
            "--",
            f"docs/product/changelog.d/{new_id}.md",
        )
    ] = git.responses.pop(
        ("diff", "--name-status", "--find-renames", "base123", "--", _VALID_FRAGMENT_REL)
    )
    git.responses[("ls-files", "--", f"docs/product/changelog.d/{new_id}.md")] = (
        0,
        f"docs/product/changelog.d/{new_id}.md\n",
        "",
    )

    _assert_refused(
        fragment,
        "id",
        "must not change after merge",
        lambda path: changelog.validate_fragment(path, git_runner=git),
    )


def test_validate_fragment_accepts_committed_body_only_edit(tmp_path: Path) -> None:
    fragment = _repo_fragment(
        tmp_path,
        body="## Highlights\n- Body changed only.\n",
    )
    git = _FakeGit(
        tmp_path,
        _git_responses(
            tmp_path,
            diff="M\tdocs/product/changelog.d/11111111-1111-4111-8111-111111111111.md\n",
            base_text=_fragment_text(body="## Highlights\n- Original body.\n"),
        ),
    )

    assert changelog.validate_fragment(fragment, git_runner=git).id == VALID_ID


def test_validate_fragment_accepts_added_path_with_missing_base_blob(tmp_path: Path) -> None:
    fragment = _repo_fragment(tmp_path)
    git = _FakeGit(
        tmp_path,
        _git_responses(
            tmp_path,
            diff="A\tdocs/product/changelog.d/11111111-1111-4111-8111-111111111111.md\n",
        ),
    )

    assert changelog.validate_fragment(fragment, git_runner=git).id == VALID_ID
    # An added path has no published identity, so it must cost no blob fetch.
    assert not any(call[0] == "show" for call in git.calls)


def test_validate_fragment_refuses_modified_missing_base_blob(tmp_path: Path) -> None:
    fragment = _repo_fragment(tmp_path)
    responses = _git_responses(
        tmp_path,
        diff="M\tdocs/product/changelog.d/11111111-1111-4111-8111-111111111111.md\n",
    )
    responses[("show", f"base123:{_VALID_FRAGMENT_REL}")] = (128, "", "missing")
    git = _FakeGit(tmp_path, responses)

    _assert_refused(
        fragment,
        "base blob",
        "readable base blob for modified or renamed fragment",
        lambda path: changelog.validate_fragment(path, git_runner=git),
    )


def test_validate_fragment_refuses_renamed_missing_base_blob(tmp_path: Path) -> None:
    new_id = "77777777-7777-4777-8777-777777777777"
    fragment = _repo_fragment(
        tmp_path,
        name=f"{new_id}.md",
        fragment_id=new_id,
        anchor="core300--2026-09-29-77777777777747778777777777777777",
    )
    rel = f"docs/product/changelog.d/{new_id}.md"
    responses = {
        ("rev-parse", "--show-toplevel"): (0, f"{tmp_path}\n", ""),
        ("merge-base", "origin/main", "HEAD"): (0, "base123\n", ""),
        ("diff", "--name-status", "--find-renames", "base123", "--", rel): (
            0,
            f"R100\t{_RENAMED_FRAGMENT_REL}\t{rel}\n",
            "",
        ),
        ("ls-files", "--", rel): (0, f"{rel}\n", ""),
        ("show", f"base123:{_RENAMED_FRAGMENT_REL}"): (128, "", "missing"),
    }
    git = _FakeGit(tmp_path, responses)

    _assert_refused(
        fragment,
        "base blob",
        "readable base blob for modified or renamed fragment",
        lambda path: changelog.validate_fragment(path, git_runner=git),
    )


def test_validate_fragment_accepts_untracked_new_path(tmp_path: Path) -> None:
    """An untracked path is absent from `ls-files`, not an `ls-files` failure.

    The tracked-path read covers many paths at once, so a non-zero exit now
    means the read itself failed and refuses. Absence from a successful listing
    is what identifies a new file.
    """
    fragment = _repo_fragment(tmp_path)
    responses = _git_responses(tmp_path, diff="")
    responses[("ls-files", "--", _VALID_FRAGMENT_REL)] = (0, "", "")
    git = _FakeGit(tmp_path, responses)

    assert changelog.validate_fragment(fragment, git_runner=git).id == VALID_ID
    assert not any(call[0] == "show" for call in git.calls)


def test_validate_fragment_git_boundary_fail_closed_matrix(tmp_path: Path) -> None:
    fragment = _repo_fragment(tmp_path)
    cases = [
        (
            "missing-base",
            {("merge-base", "origin/main", "HEAD"): (1, "", "no merge base")},
            "merge base",
            "readable merge base against origin/main",
        ),
        (
            "shallow-base",
            {("merge-base", "origin/main", "HEAD"): (128, "", "shallow")},
            "merge base",
            "readable merge base against origin/main",
        ),
        (
            "unexpected-diff-failure",
            {
                (
                    "diff",
                    "--name-status",
                    "--find-renames",
                    "base123",
                    "--",
                    _VALID_FRAGMENT_REL,
                ): (2, "", "boom")
            },
            "changed path",
            "parseable Git changed-path status",
        ),
        (
            "malformed-diff",
            {
                (
                    "diff",
                    "--name-status",
                    "--find-renames",
                    "base123",
                    "--",
                    _VALID_FRAGMENT_REL,
                ): (0, "M\n", "")
            },
            "changed path",
            "parseable Git changed-path status",
        ),
        (
            "malformed-base",
            {("merge-base", "origin/main", "HEAD"): (0, "base123\nother\n", "")},
            "merge base",
            "readable merge base against origin/main",
        ),
    ]
    for _name, overrides, field, expected in cases:
        responses = _git_responses(
            tmp_path,
            diff="M\tdocs/product/changelog.d/11111111-1111-4111-8111-111111111111.md\n",
            base_text=_fragment_text(),
        )
        responses.update(overrides)
        git = _FakeGit(tmp_path, responses)
        _assert_refused(
            fragment,
            field,
            expected,
            lambda path, runner=git: changelog.validate_fragment(
                path, git_runner=runner
            ),
        )


def _assembly_fragment(
    directory: Path,
    fragment_id: str,
    fragment_date: str,
    highlight: str,
) -> Path:
    anchor = f"core300--{fragment_date}-{fragment_id.replace('-', '')}"
    return _write_fragment(
        directory,
        name=f"{fragment_id}.md",
        fragment_id=fragment_id,
        anchor=anchor,
        date=fragment_date,
        body=f"## Highlights\n- {highlight}\n",
    )


def _assembly_digest(baseline: str, fragments: list) -> str:
    return __import__("hashlib").sha256(
        changelog.assemble_changelog(baseline, fragments).encode("utf-8")
    ).hexdigest()


def test_assemble_changelog_is_deterministic_under_shuffled_collection(
    tmp_path: Path, capsys
) -> None:
    fragment_dir = tmp_path / "docs/product/changelog.d"
    paths = [
        _assembly_fragment(
            fragment_dir,
            "99999999-9999-4999-8999-999999999999",
            "2026-09-28",
            "Third.",
        ),
        _assembly_fragment(
            fragment_dir,
            "11111111-1111-4111-8111-111111111111",
            "2026-09-29",
            "First.",
        ),
        _assembly_fragment(
            fragment_dir,
            "22222222-2222-4222-8222-222222222222",
            "2026-09-29",
            "Second.",
        ),
    ]
    orders = [
        paths,
        [paths[2], paths[1], paths[0]],
        [paths[1], paths[0], paths[2]],
        [paths[0], paths[2], paths[1]],
        [paths[2], paths[0], paths[1]],
    ]

    canonical_digests = set()
    mutation_digests = set()
    for order in orders:
        fragments = changelog.collect_validated_fragments(
            fragment_dir,
            enumerator=lambda _directory, order=order: order,
        )
        canonical_digests.add(_assembly_digest("# Changelog\n", fragments))
        mutation_digests.add(
            __import__("hashlib").sha256(
                changelog.assemble_changelog(
                    "# Changelog\n", fragments, sort_fragments=False
                ).encode("utf-8")
            ).hexdigest()
        )

    summary = (
        f"T4 shuffle digests={len(canonical_digests)} "
        f"mutation digests={len(mutation_digests)}"
    )
    with capsys.disabled():
        print(summary)
    assert "shuffle digests=1" in summary
    assert "mutation digests=" in summary
    assert len(canonical_digests) == 1
    assert len(mutation_digests) >= 2


def test_assemble_changelog_orders_date_desc_then_id_asc(tmp_path: Path) -> None:
    fragment_dir = tmp_path / "docs/product/changelog.d"
    high_id = _assembly_fragment(
        fragment_dir,
        "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        "2026-09-29",
        "High id same date.",
    )
    older = _assembly_fragment(
        fragment_dir,
        "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "2026-09-28",
        "Older date.",
    )
    low_id = _assembly_fragment(
        fragment_dir,
        "11111111-1111-4111-8111-111111111111",
        "2026-09-29",
        "Low id same date.",
    )

    fragments = changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: [high_id, older, low_id]
    )
    output = changelog.assemble_changelog("# Changelog\n", fragments)

    assert output.index("Low id same date.") < output.index("High id same date.")
    assert output.index("High id same date.") < output.index("Older date.")


def test_assemble_changelog_ignores_wall_clock_and_git_history(tmp_path: Path) -> None:
    def commit_repo(repo: Path, author: str, email: str, date_value: str) -> str:
        _git(repo, "init", "-b", "main")
        _git(repo, "config", "user.name", author)
        _git(repo, "config", "user.email", email)
        subprocess.run(
            ["git", "-C", str(repo), "add", "."],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "test: source bytes"],
            check=True,
            capture_output=True,
            text=True,
            env={
                **__import__("os").environ,
                "GIT_AUTHOR_DATE": date_value,
                "GIT_COMMITTER_DATE": date_value,
            },
        )
        return subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def author_line(repo: Path) -> str:
        return subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%an <%ae> %aI"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    repo_one = tmp_path / "one"
    fragment_dir = repo_one / "docs/product/changelog.d"
    path = _assembly_fragment(
        fragment_dir,
        "11111111-1111-4111-8111-111111111111",
        "2026-09-29",
        "History independent.",
    )
    fragments = changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: [path]
    )

    first = changelog.assemble_changelog("# Changelog\n", fragments)
    second = changelog.assemble_changelog("# Changelog\n", fragments)
    assert first == second

    repo_two = tmp_path / "two"
    other_dir = repo_two / "docs/product/changelog.d"
    other = _assembly_fragment(
        other_dir,
        "11111111-1111-4111-8111-111111111111",
        "2026-09-29",
        "History independent.",
    )
    other_fragments = changelog.collect_validated_fragments(
        other_dir, enumerator=lambda _directory: [other]
    )
    assert path.read_bytes() == other.read_bytes()

    first_sha = commit_repo(
        repo_one, "First Author", "first@example.invalid", "2026-09-29T01:02:03Z"
    )
    second_sha = commit_repo(
        repo_two, "Second Author", "second@example.invalid", "2026-09-30T04:05:06Z"
    )
    assert first_sha != second_sha
    assert author_line(repo_one) != author_line(repo_two)

    assert first == changelog.assemble_changelog("# Changelog\n", other_fragments)


_HISTORICAL_CHANGELOG = _SCRIPT.parent.parent / "docs/product/changelog.md"
_HISTORICAL_DIGEST = "3c59288034aeaceb0a0977d43a36fc2b53f43698185ea3eb95bd75ee73b9fd1c"
_HISTORICAL_RELEASE_SECTION_DIGEST = (
    "0cecc3fb4f580832b564725da3c518bd623962ebeac630c43d84c906073bfbe7"
)
_MIGRATION_NOTICE = (
    "New product changelog updates are authored as fragments and rendered into "
    "the public `/changelog/` view with "
    "`python3 tools/changelog.py render --output build/product-changelog.md`."
)
_FREEZE_GATE_COMMAND = (
    "python3 tools/changelog.py render --output build/product-changelog.md"
)
_FRAGMENT_NEW_COMMAND = (
    "python3 tools/changelog.py new --package package-name --version 0.0.0 "
    '--date 2026-09-30 --highlight "Describe the released outcome."'
)
_FRAGMENT_TEMPLATE = _SCRIPT.parent.parent / "docs/product/changelog-fragment-template.md"


def _historical_release_sections(text: str) -> str:
    lines = text.splitlines(keepends=True)
    starts = [
        index
        for index, line in enumerate(lines)
        if re.match(r"^## \[[A-Za-z0-9][A-Za-z0-9._-]*\]\[[^\]]+\]", line)
    ]
    parts: list[str] = []
    for offset, start in enumerate(starts):
        end = starts[offset + 1] if offset + 1 < len(starts) else len(lines)
        parts.extend(lines[start:end])
    return "".join(parts)


def _run_render(
    cwd: Path,
    output: Path,
    *,
    baseline: Path | None = None,
    fragments: Path | None = None,
):
    command = [
        sys.executable,
        str(_SCRIPT),
        "render",
        "--output",
        str(output),
    ]
    if baseline is not None:
        command.extend(["--baseline", str(baseline)])
    if fragments is not None:
        command.extend(["--fragments", str(fragments)])
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def test_render_cli_preserves_frozen_history_digest_and_git_cleanliness(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    baseline = repo / "docs/product/changelog.md"
    baseline.parent.mkdir(parents=True)
    baseline.write_text(_HISTORICAL_CHANGELOG.read_text(encoding="utf-8"), encoding="utf-8")
    (repo / ".gitignore").write_text("build/\n", encoding="utf-8")

    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test Author")
    _git(repo, "config", "user.email", "test.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "test: clean checkout")
    # Set origin/main so _base_blob_text does not fail-closed on a missing ref
    # (Fix 2: exit 128 from git merge-base now raises instead of returning None).
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")

    output = repo / "build/product-changelog.md"
    result = _run_render(repo, output)

    assert result.returncode == 0, result.stderr
    rendered = output.read_text(encoding="utf-8")
    assert __import__("hashlib").sha256(rendered.encode("utf-8")).hexdigest() == (
        _HISTORICAL_DIGEST
    )
    assert rendered == baseline.read_text(encoding="utf-8")
    ignored_output = Path("build/product-changelog.md")
    resolution = _lint_git_ignore().git_ignored_paths(
        repo,
        [ignored_output],
        missing_git_policy=_lint_git_ignore().MissingGitPolicy.RAISE,
        timeout=30.0,
    )
    assert resolution.ignored == (ignored_output,)
    assert subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout == ""


def test_historical_changelog_notice_is_the_only_pre_section_change() -> None:
    text = _HISTORICAL_CHANGELOG.read_text(encoding="utf-8")

    assert _MIGRATION_NOTICE in text
    assert __import__("hashlib").sha256(
        _historical_release_sections(text).encode("utf-8")
    ).hexdigest() == _HISTORICAL_RELEASE_SECTION_DIGEST


def _repo_with_historical_changelog_base(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    baseline = repo / "docs/product/changelog.md"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("# Changelog\n\n## [core][1.0.0] — 2026-09-29\n\nOriginal body.\n", encoding="utf-8")
    (repo / ".gitignore").write_text("build/\n", encoding="utf-8")
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test Author")
    _git(repo, "config", "user.email", "test.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "test: base changelog")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "checkout", "-b", "feature")
    return repo, baseline


def test_render_cli_refuses_historical_release_edit_through_boundary(
    tmp_path: Path,
) -> None:
    repo, baseline = _repo_with_historical_changelog_base(tmp_path)
    baseline.write_text(
        "# Changelog\n\n## [core][1.0.0] — 2026-09-29\n\nEdited body.\n",
        encoding="utf-8",
    )

    result = _run_render(repo, repo / "build/product-changelog.md")

    assert result.returncode == 1
    assert "docs/product/changelog.md" in result.stderr
    assert "[core][1.0.0] — 2026-09-29" in result.stderr
    assert "historical release section" in result.stderr


def test_render_cli_accepts_notice_only_edit_through_boundary(tmp_path: Path) -> None:
    repo, baseline = _repo_with_historical_changelog_base(tmp_path)
    baseline.write_text(
        "# Changelog\n\n"
        f"> {_MIGRATION_NOTICE}\n\n"
        "## [core][1.0.0] — 2026-09-29\n\n"
        "Original body.\n",
        encoding="utf-8",
    )
    output = repo / "build/product-changelog.md"

    result = _run_render(repo, output)

    assert result.returncode == 0, result.stderr
    assert _MIGRATION_NOTICE in output.read_text(encoding="utf-8")


def test_pages_workflow_invokes_historical_changelog_freeze_gate() -> None:
    workflow = (
        _SCRIPT.parent.parent / ".github/workflows/pages.yml"
    ).read_text(encoding="utf-8")

    assert "docs/product/changelog.md" in workflow
    assert _FREEZE_GATE_COMMAND in workflow


def test_fragment_template_lives_outside_scanned_directory_and_is_refused() -> None:
    assert _FRAGMENT_TEMPLATE.is_file()
    assert _FRAGMENT_TEMPLATE.parent.name == "product"
    assert _FRAGMENT_TEMPLATE.parent.name != "changelog.d"

    try:
        changelog.validate_fragment(_FRAGMENT_TEMPLATE, enforce_immutability=False)
    except changelog.FragmentValidationError as exc:
        message = str(exc)
    else:
        raise AssertionError("unfilled fragment template validated")

    assert "changelog-fragment-template.md" in message
    assert "id" in message


def test_fragment_template_validates_once_filled_at_uuid_path(tmp_path: Path) -> None:
    fragment_id = "11111111-1111-4111-8111-111111111111"
    packages = [{"name": "core", "version": "0.0.0"}]
    anchor = changelog._compose_fragment_anchor(packages, "2026-09-30", fragment_id)
    source = (
        _FRAGMENT_TEMPLATE.read_text(encoding="utf-8")
        .replace("<uuid-v4>", fragment_id)
        .replace("<computed-anchor>", anchor)
        .replace("Replace this with the user-visible change details.", "Details.")
    )
    path = tmp_path / "docs/product/changelog.d" / f"{fragment_id}.md"
    path.parent.mkdir(parents=True)
    path.write_text(source, encoding="utf-8")

    record = changelog.validate_fragment(path, enforce_immutability=False)

    assert record.id == fragment_id
    assert record.anchor == anchor
    assert record.sections["Highlights"]


def test_render_cli_succeeds_with_tracked_template_present(tmp_path: Path) -> None:
    baseline = tmp_path / "docs/product/changelog.md"
    template = tmp_path / "docs/product/changelog-fragment-template.md"
    output = tmp_path / "build/product-changelog.md"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("# Changelog\n", encoding="utf-8")
    template.write_text(_FRAGMENT_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")

    result = _run_render(tmp_path, output, baseline=baseline)

    assert result.returncode == 0, result.stderr
    assert output.read_text(encoding="utf-8") == "# Changelog\n"


def test_live_author_guidance_uses_fragment_gesture() -> None:
    root = _SCRIPT.parent.parent
    surfaces = {
        "docs/product/AGENTS.md": root / "docs/product/AGENTS.md",
        "packs/AGENTS.local.md": root / "packs/AGENTS.local.md",
        "docs/product/changelog.md": root / "docs/product/changelog.md",
    }
    old_instructions = (
        "Edit the changelog and stop there",
        "Add the pack release entry to `docs/product/changelog.md`",
    )
    for label, path in surfaces.items():
        text = path.read_text(encoding="utf-8")
        assert _FRAGMENT_NEW_COMMAND in text, label
        assert "edit the created file" in text.casefold(), label
        assert "stop" in text.casefold(), label
        assert "docs/product/changelog-fragment-template.md" in text, label
        for old in old_instructions:
            assert old not in text, label

    assert "generated, gitignored" in surfaces[
        "docs/product/AGENTS.md"
    ].read_text(encoding="utf-8")


def test_render_cli_preserves_every_fragment_body_and_anchor(tmp_path: Path) -> None:
    baseline = tmp_path / "docs/product/changelog.md"
    fragments_dir = tmp_path / "docs/product/changelog.d"
    output = tmp_path / "build/product-changelog.md"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("# Changelog\n\n## Historical\nOld body.\n", encoding="utf-8")
    first = _write_fragment(
        fragments_dir,
        name="11111111-1111-4111-8111-111111111111.md",
        body=(
            "## Highlights\n"
            "- First highlight alpha.\n"
            "- First highlight beta.\n"
            "\n"
            "## Fixed\n"
            "Preserve the first fix paragraph.\n"
        ),
    )
    second = _write_fragment(
        fragments_dir,
        name="22222222-2222-4222-8222-222222222222.md",
        fragment_id="22222222-2222-4222-8222-222222222222",
        anchor="core300--2026-09-29-22222222222242228222222222222222",
        body=(
            "## Highlights\n"
            "- Second highlight.\n"
            "\n"
            "## Security\n"
            "Preserve the security paragraph.\n"
        ),
    )

    result = _run_render(
        tmp_path,
        output,
        baseline=baseline,
        fragments=fragments_dir,
    )

    assert result.returncode == 0, result.stderr
    rendered = output.read_text(encoding="utf-8")
    first_record = changelog.validate_fragment(first)
    second_record = changelog.validate_fragment(second)
    for record in (first_record, second_record):
        anchor_and_heading = (
            f'<a id="{record.anchor}"></a>\n'
            f"## {changelog._fragment_heading(record.packages, record.date)}"
        )
        assert rendered.count(anchor_and_heading) == 1
    for text in (
        "First highlight alpha.",
        "First highlight beta.",
        "Second highlight.",
        "Preserve the first fix paragraph.",
        "Preserve the security paragraph.",
    ):
        assert rendered.count(text) == 1
    first_highlights = rendered.index("### Highlights")
    first_fixed = rendered.index("### Fixed")
    second_highlights = rendered.index("### Highlights", first_highlights + 1)
    second_security = rendered.index("### Security")
    assert first_highlights < first_fixed < second_highlights < second_security


def test_render_cli_fails_closed_without_replacing_existing_output(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "docs/product/changelog.md"
    fragments_dir = tmp_path / "docs/product/changelog.d"
    output = tmp_path / "build/product-changelog.md"
    baseline.parent.mkdir(parents=True)
    output.parent.mkdir(parents=True)
    baseline.write_text("# Changelog\n", encoding="utf-8")
    output.write_text("existing output\n", encoding="utf-8")
    bad = _write_fragment(fragments_dir)
    bad.write_text(
        bad.read_text(encoding="utf-8").replace("schema = 1", "schema = 2"),
        encoding="utf-8",
    )

    result = _run_render(
        tmp_path,
        output,
        baseline=baseline,
        fragments=fragments_dir,
    )

    assert result.returncode == 1
    assert str(bad) in result.stderr
    assert "schema" in result.stderr
    assert "schema version 1" in result.stderr
    assert output.read_text(encoding="utf-8") == "existing output\n"


def test_render_cli_file_safety_refusal_leaves_existing_output_unchanged(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "docs/product/changelog.md"
    fragments_dir = tmp_path / "docs/product/changelog.d"
    output = tmp_path / "build/product-changelog.md"
    baseline.parent.mkdir(parents=True)
    fragments_dir.mkdir(parents=True)
    output.parent.mkdir(parents=True)
    baseline.write_text("# Changelog\n", encoding="utf-8")
    output.write_text("existing output\n", encoding="utf-8")
    directory_fragment = fragments_dir / f"{VALID_ID}.md"
    directory_fragment.mkdir()

    result = _run_render(
        tmp_path,
        output,
        baseline=baseline,
        fragments=fragments_dir,
    )

    assert result.returncode == 1
    assert str(directory_fragment) in result.stderr
    assert "path" in result.stderr
    assert "bounded direct regular fragment files" in result.stderr
    assert output.read_text(encoding="utf-8") == "existing output\n"


def _group_by_anchor(payload: dict) -> dict[str, dict]:
    return {group["changelogAnchor"]: group for group in payload["groups"]}


def _record_block(rendered: str, anchor: str) -> str:
    start = rendered.index(f'<a id="{anchor}"></a>')
    next_record = rendered.find("\n<a id=", start + 1)
    return rendered[start:] if next_record == -1 else rendered[start:next_record]


def test_unreleased_fragment_renders_pending_and_has_no_now_group(tmp_path: Path) -> None:
    fragment_dir = tmp_path / "docs/product/changelog.d"
    path = _assembly_fragment(
        fragment_dir,
        "11111111-1111-4111-8111-111111111111",
        "2026-09-29",
        "Pending highlight.",
    )
    fragments = changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: [path]
    )
    inventory = {"core": {"2.9.0"}}

    rendered = changelog.assemble_changelog(
        "# Changelog\n", fragments, released_versions=inventory
    )
    payload = changelog.project_fragment_now_highlights(fragments, inventory)

    assert "## [Unreleased]" in rendered
    assert "### [core][3.0.0] — 2026-09-29" in rendered
    assert "Pending highlight." in rendered
    assert payload["groups"] == []


def test_fragment_moves_to_released_group_without_source_mutation(tmp_path: Path) -> None:
    fragment_dir = tmp_path / "docs/product/changelog.d"
    path = _assembly_fragment(
        fragment_dir,
        "11111111-1111-4111-8111-111111111111",
        "2026-09-29",
        "Released highlight.",
    )
    before_bytes = path.read_bytes()
    fragments = changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: [path]
    )
    pending = {"core": {"2.9.0"}}
    released = {"core": {"3.0.0"}}

    assert changelog.project_fragment_now_highlights(fragments, pending)["groups"] == []
    payload = changelog.project_fragment_now_highlights(fragments, released)

    assert path.read_bytes() == before_bytes
    assert len(payload["groups"]) == 1
    group = payload["groups"][0]
    assert group["changelogAnchor"] == fragments[0].anchor
    assert group["highlights"][0]["source"] == "Released highlight."


def test_release_transition_preserves_other_records(tmp_path: Path) -> None:
    fragment_dir = tmp_path / "docs/product/changelog.d"
    other_path = _assembly_fragment(
        fragment_dir,
        "22222222-2222-4222-8222-222222222222",
        "2026-09-28",
        "Already released.",
    )
    pending_path = _write_fragment(
        fragment_dir,
        name="11111111-1111-4111-8111-111111111111.md",
        packages='[[packages]]\nname = "core"\nversion = "3.1.0"',
        anchor="core310--2026-09-29-11111111111141118111111111111111",
        body="## Highlights\n- Transitioning release.\n",
    )
    fragments = changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: [pending_path, other_path]
    )
    other = next(fragment for fragment in fragments if fragment.path == other_path)
    pending = {"core": {"3.0.0"}}
    released = {"core": {"3.0.0", "3.1.0"}}

    before_view = changelog.assemble_changelog(
        "# Changelog\n", fragments, released_versions=pending
    )
    after_view = changelog.assemble_changelog(
        "# Changelog\n", fragments, released_versions=released
    )
    before_payload = _group_by_anchor(
        changelog.project_fragment_now_highlights(fragments, pending)
    )
    after_payload = _group_by_anchor(
        changelog.project_fragment_now_highlights(fragments, released)
    )

    assert _record_block(before_view, other.anchor) == _record_block(
        after_view, other.anchor
    )
    assert before_payload[other.anchor] == after_payload[other.anchor]


def test_released_inventory_refuses_uncomparable_versions(tmp_path: Path) -> None:
    fragment_dir = tmp_path / "docs/product/changelog.d"
    path = _assembly_fragment(
        fragment_dir,
        "11111111-1111-4111-8111-111111111111",
        "2026-09-29",
        "Pending highlight.",
    )
    fragments = changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: [path]
    )

    try:
        changelog.project_fragment_now_highlights(fragments, {"core": {"3/0"}})
    except changelog.FragmentValidationError as error:
        message = str(error)
    else:
        raise AssertionError("bad released-version inventory was accepted")

    assert "<released-versions>" in message
    assert "core" in message
    assert "[A-Za-z0-9][A-Za-z0-9._+-]*" in message


_FRAGMENT_DIR_REL = "docs/product/changelog.d"


def _batch_fragment(directory: Path, index: int) -> tuple[Path, str]:
    """Write one fragment with a distinct id and its computed anchor."""
    fragment_id = f"{index:08d}-1111-4111-8111-111111111111"
    fragment_date = "2026-09-29"
    packages = [{"name": "core", "version": "3.0.0"}]
    anchor = changelog._compose_fragment_anchor(packages, fragment_date, fragment_id)
    path = _write_fragment(
        directory,
        name=f"{fragment_id}.md",
        fragment_id=fragment_id,
        anchor=anchor,
        date=fragment_date,
    )
    return path, f"{_FRAGMENT_DIR_REL}/{fragment_id}.md"


def _batch_corpus(tmp_path: Path, count: int) -> tuple[Path, list[Path], list[str]]:
    """Build a fragment directory of `count` distinct fragments."""
    directory = tmp_path / _FRAGMENT_DIR_REL
    paths: list[Path] = []
    relatives: list[str] = []
    for index in range(1, count + 1):
        path, relative = _batch_fragment(directory, index)
        paths.append(path)
        relatives.append(relative)
    return directory, paths, relatives


def _batch_git(
    repo: Path,
    relatives: list[str],
    *,
    diff: str = "",
    tracked: list[str] | None = None,
    base_text: str | None = None,
    overrides: dict[tuple[str, ...], tuple[int, str, str]] | None = None,
) -> _FakeGit:
    """Build a fake keyed on the directory-wide command shapes."""
    listed = relatives if tracked is None else tracked
    responses: dict[tuple[str, ...], tuple[int, str, str]] = {
        ("rev-parse", "--show-toplevel"): (0, f"{repo}\n", ""),
        ("merge-base", "origin/main", "HEAD"): (0, "base123\n", ""),
        (
            "diff",
            "--name-status",
            "--find-renames",
            "base123",
            "--",
            _FRAGMENT_DIR_REL,
        ): (0, diff, ""),
        ("ls-files", "--", _FRAGMENT_DIR_REL): (
            0,
            "".join(f"{relative}\n" for relative in listed),
            "",
        ),
    }
    if base_text is not None:
        for relative in relatives:
            responses[("show", f"base123:{relative}")] = (0, base_text, "")
    responses.update(overrides or {})
    return _FakeGit(repo, responses)


def _collect(directory: Path, paths: list[Path], git: _FakeGit):
    """Collect in a fixed order so the reported path is deterministic."""
    return changelog.collect_validated_fragments(
        directory, enumerator=lambda _directory: list(paths), git_runner=git
    )


def test_collect_validated_fragments_git_cost_is_constant(tmp_path: Path) -> None:
    """The Git cost of a pass must not scale with the fragment count.

    This is the control on the fan-out: five subprocesses per fragment used to
    make a ten-times corpus cost tens of thousands of spawns per build. A
    regression here is a reintroduced per-fragment loop, which no assertion
    about output would catch.
    """
    counts = {}
    for size in (1, 8):
        case = tmp_path / f"corpus-{size}"
        directory, paths, relatives = _batch_corpus(case, size)
        git = _batch_git(case, relatives)

        assert len(_collect(directory, paths, git)) == size

        counts[size] = len(git.calls)

    assert counts[1] == counts[8], counts
    # rev-parse, merge-base, diff, ls-files. No per-fragment call at all.
    assert counts[8] == 4, counts


def test_collect_validated_fragments_skips_the_blob_for_unchanged_paths(
    tmp_path: Path,
) -> None:
    """A path Git reports as unchanged is the published bytes already.

    Its identity fields cannot have moved, so fetching the base blob to compare
    them against themselves is pure cost. This asserts the skip, which is what
    removes the per-fragment `show`.
    """
    directory, paths, relatives = _batch_corpus(tmp_path, 4)
    git = _batch_git(tmp_path, relatives)

    records = _collect(directory, paths, git)

    assert len(records) == 4
    assert not any(call[0] == "show" for call in git.calls)


def test_collect_validated_fragments_refuses_repository_wide_git_failures(
    tmp_path: Path,
) -> None:
    """Each repository-wide Git failure refuses by path and correction.

    AC4 is fail-closed: identity validation must resolve the merge base and
    classify the path before comparing bytes, and any malformed or unexpected
    Git result refuses. Batching must not turn these into an anonymous
    whole-set error, so every case names the fragment and the correction.
    """
    diff_key = (
        "diff",
        "--name-status",
        "--find-renames",
        "base123",
        "--",
        _FRAGMENT_DIR_REL,
    )
    cases = [
        (
            "missing-merge-base",
            {("merge-base", "origin/main", "HEAD"): (1, "", "no merge base")},
            "merge base",
            "readable merge base against origin/main",
        ),
        (
            "shallow-history",
            {("merge-base", "origin/main", "HEAD"): (128, "", "shallow")},
            "merge base",
            "readable merge base against origin/main",
        ),
        (
            "malformed-merge-base",
            {("merge-base", "origin/main", "HEAD"): (0, "base123\nother\n", "")},
            "merge base",
            "readable merge base against origin/main",
        ),
        (
            "unexpected-changed-path-failure",
            {diff_key: (2, "", "boom")},
            "changed path",
            "parseable Git changed-path status",
        ),
        (
            "unattributable-changed-path-line",
            {diff_key: (0, "M\n", "")},
            "changed path",
            "parseable Git changed-path status",
        ),
        (
            "unreadable-tracked-listing",
            {("ls-files", "--", _FRAGMENT_DIR_REL): (2, "", "boom")},
            "changed path",
            "parseable Git changed-path status",
        ),
    ]
    for name, overrides, field, expected in cases:
        case = tmp_path / name
        directory, paths, relatives = _batch_corpus(case, 3)
        git = _batch_git(case, relatives, overrides=overrides)

        try:
            _collect(directory, paths, git)
        except changelog.FragmentValidationError as error:
            message = str(error)
        else:
            raise AssertionError(f"{name} was accepted")

        # The first enumerated fragment is the path a whole-pass failure names.
        assert str(paths[0]) in message, name
        assert field in message, name
        assert expected in message, name


def test_collect_validated_fragments_refuses_modified_missing_base_blob(
    tmp_path: Path,
) -> None:
    """A modified path with no readable base blob refuses, naming that path."""
    directory, paths, relatives = _batch_corpus(tmp_path, 3)
    target = relatives[1]
    git = _batch_git(
        tmp_path,
        relatives,
        diff=f"M\t{target}\n",
        overrides={("show", f"base123:{target}"): (128, "", "missing")},
    )

    _assert_refused(
        paths[1],
        "base blob",
        "readable base blob for modified or renamed fragment",
        lambda _path: _collect(directory, paths, git),
    )


def test_collect_validated_fragments_refuses_renamed_missing_base_blob(
    tmp_path: Path,
) -> None:
    """A renamed path with no readable base blob refuses, naming that path."""
    directory, paths, relatives = _batch_corpus(tmp_path, 3)
    target = relatives[2]
    former = f"{_FRAGMENT_DIR_REL}/00000000-0000-4000-8000-000000000000.md"
    git = _batch_git(
        tmp_path,
        relatives,
        diff=f"R100\t{former}\t{target}\n",
        overrides={("show", f"base123:{former}"): (128, "", "missing")},
    )

    _assert_refused(
        paths[2],
        "base blob",
        "readable base blob for modified or renamed fragment",
        lambda _path: _collect(directory, paths, git),
    )


def test_collect_validated_fragments_refuses_unmodelled_status_by_path(
    tmp_path: Path,
) -> None:
    """One bad line refuses its own path, not the whole set.

    A status this validator does not model still names a path, so the refusal
    has to be attributed to that fragment. Collecting the same corpus without
    the offending line must succeed, which is what proves the refusal was
    per-path rather than a whole-pass failure.
    """
    directory, paths, relatives = _batch_corpus(tmp_path, 3)
    target = relatives[1]
    git = _batch_git(tmp_path, relatives, diff=f"C100\t{relatives[0]}\t{target}\n")

    _assert_refused(
        paths[1],
        "changed path",
        "parseable Git changed-path status",
        lambda _path: _collect(directory, paths, git),
    )

    clean = _batch_git(tmp_path, relatives)
    assert len(_collect(directory, paths, clean)) == 3


def test_collect_validated_fragments_refuses_committed_identity_edit(
    tmp_path: Path,
) -> None:
    """The batch still enforces AC5 on a genuinely modified fragment."""
    directory, paths, relatives = _batch_corpus(tmp_path, 3)
    target = relatives[1]
    moved_date = _fragment_text(
        fragment_id="00000002-1111-4111-8111-111111111111",
        anchor=changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}],
            "2026-09-28",
            "00000002-1111-4111-8111-111111111111",
        ),
        date="2026-09-28",
    )
    git = _batch_git(
        tmp_path,
        relatives,
        diff=f"M\t{target}\n",
        overrides={("show", f"base123:{target}"): (0, moved_date, "")},
    )

    _assert_refused(
        paths[1],
        "date",
        "must not change after merge",
        lambda _path: _collect(directory, paths, git),
    )


def test_release_inventory_is_normalized_once_per_projection(
    tmp_path: Path, monkeypatch,
) -> None:
    fragment_dir = tmp_path / "docs/product/changelog.d"
    paths = [
        _assembly_fragment(
            fragment_dir,
            f"{index + 1:08d}-1111-4111-8111-111111111111",
            "2026-09-29",
            f"Highlight {index + 1}.",
        )
        for index in range(2)
    ]
    fragments = changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: paths
    )
    inventory = {"core": {"3.0.0"}}
    calls = 0
    original = changelog._normalize_released_versions

    def counted(value):
        nonlocal calls
        calls += 1
        return original(value)

    monkeypatch.setattr(changelog, "_normalize_released_versions", counted)
    changelog.assemble_changelog(
        "# Changelog\n", fragments, released_versions=inventory
    )
    assert calls == 1

    calls = 0
    changelog.project_fragment_now_highlights(fragments, inventory)
    assert calls == 1


def test_file_safety_helper_loads_once_per_projection(
    tmp_path: Path, monkeypatch,
) -> None:
    fragment_dir = tmp_path / "docs/product/changelog.d"
    paths = [
        _assembly_fragment(
            fragment_dir,
            f"{index + 1:08d}-1111-4111-8111-111111111111",
            "2026-09-29",
            f"Highlight {index + 1}.",
        )
        for index in range(3)
    ]
    loads = 0
    bounds: list[int | None] = []
    original = changelog._file_safety

    def counted():
        nonlocal loads
        loads += 1
        module = original()
        real_read = module.read_confined_regular_file

        def read(directory, path, *, max_bytes=None):
            bounds.append(max_bytes)
            return real_read(directory, path, max_bytes=max_bytes)

        module.read_confined_regular_file = read
        return module

    monkeypatch.setattr(changelog, "_file_safety", counted)
    changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: paths
    )
    assert loads == 1
    assert bounds == [changelog.MAX_FRAGMENT_BYTES] * 3

    changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: paths
    )
    assert loads == 2


def test_release_membership_decision_is_linear_and_public_helper_validates(
    tmp_path: Path, monkeypatch,
) -> None:
    fragment_dir = tmp_path / "docs/product/changelog.d"
    paths = [
        _assembly_fragment(
            fragment_dir,
            f"{index + 1:08d}-1111-4111-8111-111111111111",
            "2026-09-29",
            f"Highlight {index + 1}.",
        )
        for index in range(2)
    ]
    fragments = changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: paths
    )
    inventory = {"core": {"3.0.0"}}
    decisions = 0
    original = changelog._fragment_in_released_inventory

    def counted(fragment, normalized):
        nonlocal decisions
        decisions += 1
        return original(fragment, normalized)

    monkeypatch.setattr(changelog, "_fragment_in_released_inventory", counted)
    changelog.assemble_changelog(
        "# Changelog\n", fragments, released_versions=inventory
    )
    assert decisions == len(fragments)

    decisions = 0
    changelog.project_fragment_now_highlights(fragments, inventory)
    assert decisions == len(fragments)

    def forbidden_membership(_fragment, _normalized):
        raise AssertionError("membership was checked before inventory validation")

    monkeypatch.setattr(
        changelog, "_fragment_in_released_inventory", forbidden_membership
    )
    for malformed in ({"bad/name": {"3.0.0"}}, {"core": {"3/0"}}):
        try:
            changelog.is_fragment_released(fragments[0], malformed)
        except changelog.FragmentValidationError:
            pass
        else:
            raise AssertionError("malformed released inventory was accepted")
