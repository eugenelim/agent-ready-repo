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


# ============================================================================
# T17: Monthly bundle parts, cross-form identity, compact, retract (AC-B2 – B11)
# ============================================================================

# ── helpers ──────────────────────────────────────────────────────────────────

VALID_ID_B = "22222222-2222-4222-8222-222222222222"
VALID_ANCHOR_B = "core300--2026-10-01-22222222222242228222222222222222"


def _bundle_fragment_text(
    *,
    fragment_id: str = VALID_ID_B,
    anchor: str = VALID_ANCHOR_B,
    date: str = "2026-10-01",
    packages: str = '[[packages]]\nname = "core"\nversion = "3.0.0"',
    body: str = "## Highlights\n- Bundle test highlight.\n",
) -> str:
    return (
        "+++\n"
        "schema = 1\n"
        f'id = "{fragment_id}"\n'
        f'anchor = "{anchor}"\n'
        f"date = {date}\n"
        f"{packages}\n"
        "+++\n"
        f"{body}"
    )


def _make_bundle_part(
    directory: Path,
    name: str,
    records: list[str],
) -> Path:
    """Write a bundle part file from a list of record-text strings."""
    content = b""
    for rec in records:
        content += changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part = directory / name
    part.parent.mkdir(parents=True, exist_ok=True)
    part.write_bytes(content)
    return part


# ── AC-B2: container validation ───────────────────────────────────────────────


def test_bundle_part_refuses_missing_leading_separator(tmp_path: Path) -> None:
    """AC-B2: a part not starting with the separator is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(b"schema = 1\n")
    try:
        changelog._parse_bundle_part(part, part.read_bytes())
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and "separator" in str(e).lower()
    else:
        raise AssertionError("missing leading separator was accepted")


def test_bundle_part_refuses_empty_record(tmp_path: Path) -> None:
    """AC-B2: an empty record (two consecutive separators) is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    part = bundle_dir / "2026-10-00.bundle"
    # Two consecutive separators = one empty record.
    content = changelog.BUNDLE_SEPARATOR_BYTES + changelog.BUNDLE_SEPARATOR_BYTES
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and ("empty" in str(e).lower() or "record" in str(e).lower())
    else:
        raise AssertionError("empty record was accepted")


def test_bundle_part_refuses_record_without_final_lf(tmp_path: Path) -> None:
    """AC-B2: a record missing its final LF is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Record text without trailing newline.
    rec = _bundle_fragment_text().encode("utf-8").rstrip(b"\n")
    part = bundle_dir / "2026-10-00.bundle"
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and ("LF" in str(e) or "lf" in str(e).lower() or "record" in str(e).lower())
    else:
        raise AssertionError("record without final LF was accepted")


def test_bundle_part_refuses_bom(tmp_path: Path) -> None:
    """AC-B2: a part with a BOM is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    part = bundle_dir / "2026-10-00.bundle"
    rec = _bundle_fragment_text().encode("utf-8")
    content = b"\xef\xbb\xbf" + changelog.BUNDLE_SEPARATOR_BYTES + rec
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and ("bom" in str(e).lower() or "byte-order" in str(e).lower())
    else:
        raise AssertionError("BOM was accepted")


def test_bundle_part_refuses_cr(tmp_path: Path) -> None:
    """AC-B2: a part containing a CR is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    rec = _bundle_fragment_text().encode("utf-8")
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.replace(b"\n", b"\r\n")
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and ("cr" in str(e).lower() or "lf" in str(e).lower() or "line" in str(e).lower())
    else:
        raise AssertionError("CR in bundle part was accepted")


def test_bundle_part_refuses_non_utf8(tmp_path: Path) -> None:
    """AC-B2: a part with non-UTF-8 bytes in a record is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    rec = b"\xff\xfe some garbage bytes\n"
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and "utf" in str(e).lower()
    else:
        raise AssertionError("non-UTF-8 bytes were accepted")


def test_bundle_part_refuses_duplicate_ids(tmp_path: Path) -> None:
    """AC-B2: two records with equal canonical keys (same id) are refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    rec1 = _bundle_fragment_text()
    rec2 = _bundle_fragment_text()  # same id = VALID_ID_B
    content = (
        changelog.BUNDLE_SEPARATOR_BYTES + rec1.encode("utf-8")
        + changelog.BUNDLE_SEPARATOR_BYTES + rec2.encode("utf-8")
    )
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    seen: set[str] = set()
    try:
        changelog._parse_bundle_part(part, content, seen_ids=seen)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and "duplicate" in str(e).lower()
    else:
        raise AssertionError("duplicate id was accepted")


def test_bundle_part_refuses_out_of_order_records(tmp_path: Path) -> None:
    """AC-B2: records out of canonical order are refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # rec_b is later by date, so it should come first in canonical order (date desc).
    id_a = "33333333-3333-4333-8333-333333333333"
    anchor_a = "core300--2026-10-01-33333333333343338333333333333333"
    id_b = "44444444-4444-4444-8444-444444444444"
    anchor_b = "core300--2026-10-02-44444444444444448444444444444444"
    # Put the earlier date first (wrong order for date desc).
    rec_a = _bundle_fragment_text(fragment_id=id_a, anchor=anchor_a, date="2026-10-01")
    rec_b = _bundle_fragment_text(fragment_id=id_b, anchor=anchor_b, date="2026-10-02")
    content = (
        changelog.BUNDLE_SEPARATOR_BYTES + rec_a.encode("utf-8")
        + changelog.BUNDLE_SEPARATOR_BYTES + rec_b.encode("utf-8")
    )
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and ("order" in str(e).lower() or "canonical" in str(e).lower())
    else:
        raise AssertionError("out-of-order records were accepted")


def test_bundle_part_accepts_fenced_diff_line(tmp_path: Path) -> None:
    """AC-B2: a fenced `+++ b/path` line in a body is accepted."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Body with a diff header inside a fenced code block.
    body = "## Highlights\n- Has a diff.\n\n```diff\n+++ b/some/path\n```\n"
    rec = _bundle_fragment_text(body=body)
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    # Should not raise.
    result = changelog._parse_bundle_part(part, content)
    assert len(result) == 1


# ── AC-B2a: bundle-ready fragment validation ──────────────────────────────────


def test_validate_fragment_refuses_non_utf8(tmp_path: Path) -> None:
    """AC-B2a: a fragment holding a byte that is not UTF-8 is refused by path."""
    text = _fragment_text(fragment_id=VALID_ID, anchor=VALID_ANCHOR)
    path = tmp_path / f"{VALID_ID}.md"
    path.write_bytes(text.encode("utf-8").replace(b"Adds", b"Ad\x80ds", 1))
    assert b"\x80" in path.read_bytes(), "fixture lost its non-UTF-8 byte"
    try:
        changelog.validate_fragment(path, enforce_immutability=False)
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and "utf-8" in str(e).lower()
    else:
        raise AssertionError("a non-UTF-8 byte was accepted")


def test_validate_fragment_refuses_bom(tmp_path: Path) -> None:
    """AC-B2a: a fragment with a BOM is refused."""
    frag_id = VALID_ID
    anchor = VALID_ANCHOR
    text = _fragment_text(fragment_id=frag_id, anchor=anchor)
    path = tmp_path / f"{frag_id}.md"
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    try:
        changelog.validate_fragment(path, enforce_immutability=False)
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and ("bom" in str(e).lower() or "byte-order" in str(e).lower())
    else:
        raise AssertionError("BOM was accepted")


def test_validate_fragment_refuses_cr(tmp_path: Path) -> None:
    """AC-B2a: a fragment with a CR is refused."""
    frag_id = VALID_ID
    text = _fragment_text()
    path = tmp_path / f"{frag_id}.md"
    path.write_bytes(text.encode("utf-8").replace(b"\n", b"\r\n"))
    try:
        changelog.validate_fragment(path, enforce_immutability=False)
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and ("cr" in str(e).lower() or "lf" in str(e).lower())
    else:
        raise AssertionError("CR in fragment was accepted")


def test_validate_fragment_refuses_missing_final_lf(tmp_path: Path) -> None:
    """AC-B2a: a fragment without a final LF is refused."""
    frag_id = VALID_ID
    text = _fragment_text().rstrip("\n")
    path = tmp_path / f"{frag_id}.md"
    path.write_bytes(text.encode("utf-8"))
    try:
        changelog.validate_fragment(path, enforce_immutability=False)
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and "final" in str(e).lower()
    else:
        raise AssertionError("missing final LF was accepted")


def test_validate_fragment_refuses_separator_line(tmp_path: Path) -> None:
    """AC-B2a: a fragment containing a separator line is refused."""
    frag_id = VALID_ID
    body = f"## Highlights\n- OK.\n{changelog.BUNDLE_SEPARATOR_LINE}\n"
    text = _fragment_text(body=body)
    path = tmp_path / f"{frag_id}.md"
    path.write_text(text, encoding="utf-8")
    try:
        changelog.validate_fragment(path, enforce_immutability=False)
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and "separator" in str(e).lower()
    else:
        raise AssertionError("separator line in fragment was accepted")


# ── AC-B3: part names ─────────────────────────────────────────────────────────


def test_validate_bundle_part_name_accepts_valid_name(tmp_path: Path) -> None:
    """AC-B3: a valid YYYY-MM-NN.bundle name is accepted."""
    part = tmp_path / "2026-10-00.bundle"
    yyyy, mm, nn = changelog._validate_bundle_part_name(part, tmp_path)
    assert yyyy == "2026" and mm == "10" and nn == "00"


def test_validate_bundle_part_name_refuses_bad_format(tmp_path: Path) -> None:
    """AC-B3: a name not matching YYYY-MM-NN.bundle is refused."""
    for bad in ("2026-10.bundle", "2026-10-001.bundle", "2026-10-0.bundle",
                "notadate.bundle", "2026-13-00.bundle"):
        part = tmp_path / bad
        try:
            changelog._validate_bundle_part_name(part, tmp_path)
        except changelog.FragmentValidationError:
            pass
        else:
            raise AssertionError(f"bad name {bad!r} was accepted")


def test_bundle_part_refuses_record_date_mismatch(tmp_path: Path) -> None:
    """AC-B3: a record whose date month differs from the part month is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Record is dated 2026-09 but part is for 2026-10.
    id_a = "55555555-5555-4555-8555-555555555555"
    anchor_a = "core300--2026-09-01-55555555555545558555555555555555"
    rec = _bundle_fragment_text(fragment_id=id_a, anchor=anchor_a, date="2026-09-01")
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content, part_month="2026-10")
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and "month" in str(e).lower()
    else:
        raise AssertionError("date-month mismatch was accepted")


# ── AC-B3a: read confinement ──────────────────────────────────────────────────


def test_bundle_dir_confinement_refuses_symlink(tmp_path: Path) -> None:
    """AC-B3a: a symlink in the bundle directory is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    target = tmp_path / "real_file.bundle"
    target.write_bytes(changelog.BUNDLE_SEPARATOR_BYTES + _bundle_fragment_text().encode())
    link = bundle_dir / "2026-10-00.bundle"
    link.symlink_to(target)
    fs = changelog._file_safety()
    try:
        changelog._collect_bundle_records(bundle_dir, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError):
        pass
    else:
        raise AssertionError("symlink in bundle dir was accepted")


def test_retraction_list_confinement_refuses_symlink(tmp_path: Path) -> None:
    """AC-B3a: a symlink at the retraction list path is refused."""
    real = tmp_path / "real_retractions.toml"
    real.write_text("", encoding="utf-8")
    retraction_path = tmp_path / "changelog-retractions.toml"
    retraction_path.symlink_to(real)
    fs = changelog._file_safety()
    try:
        changelog._read_retraction_list(retraction_path, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError):
        pass  # symlink correctly refused
    else:
        raise AssertionError(
            "symlink at retraction list path was accepted; expected "
            "FragmentValidationError or UnsafeContentError"
        )


# ── AC-B4: cross-form identity (seam-level) ───────────────────────────────────


def test_missing_git_binary_refuses_rather_than_passing(tmp_path: Path) -> None:
    """AC-B4/AC4 fail-closed: a missing git binary must refuse, not silently skip.

    When the git runner raises FileNotFoundError (git not on PATH), identity
    enforcement must raise FragmentValidationError rather than treating the
    situation as 'not a git repository' (which would disable enforcement).
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    def git_raises_file_not_found(cwd: Path, *args: str) -> None:
        raise FileNotFoundError("git: No such file or directory")

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=git_raises_file_not_found,
        )
    except changelog.FragmentValidationError as e:
        assert "git" in str(e).lower(), (
            f"expected git-related error, got: {e}"
        )
    else:
        raise AssertionError(
            "missing git binary was treated as 'not a repo' (fail-open); "
            "expected FragmentValidationError"
        )


def test_compute_git_object_id_sha1_matches_known_hash() -> None:
    """AC-B4: object id is computed as git's blob hash (SHA-1)."""
    import hashlib as _hashlib
    data = b"hello world\n"
    header = b"blob " + str(len(data)).encode() + b"\0"
    expected = _hashlib.sha1(header + data, usedforsecurity=False).hexdigest()
    result = changelog._compute_git_object_id(data, "sha1")
    assert result == expected


def test_compute_git_object_id_sha256_matches_known_hash() -> None:
    """AC-B4: object id uses SHA-256 when the repo uses it."""
    import hashlib as _hashlib
    data = b"hello world\n"
    header = b"blob " + str(len(data)).encode() + b"\0"
    expected = _hashlib.sha256(header + data).hexdigest()
    result = changelog._compute_git_object_id(data, "sha256")
    assert result == expected


def test_collect_changelog_records_returns_two_lists(tmp_path: Path) -> None:
    """AC-B8: collect_changelog_records returns (loose, bundled) lists."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Write one loose fragment.
    _write_fragment(frag_dir)
    loose, bundled = changelog.collect_changelog_records(
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        retraction_path=tmp_path / "changelog-retractions.toml",
    )
    assert len(loose) == 1
    assert len(bundled) == 0


def test_collect_changelog_records_includes_bundle_records(tmp_path: Path) -> None:
    """AC-B8: bundled records are returned in the second list."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    rec = _bundle_fragment_text()
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    (bundle_dir / "2026-10-00.bundle").write_bytes(content)
    loose, bundled = changelog.collect_changelog_records(
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        retraction_path=tmp_path / "changelog-retractions.toml",
    )
    assert len(loose) == 0
    assert len(bundled) == 1
    assert bundled[0].id == VALID_ID_B


# ── AC-B5: raw bytes ──────────────────────────────────────────────────────────


def test_raw_bytes_comparison_detects_cr_in_moved_record() -> None:
    """AC-B5: raw-byte comparison detects a CR introduced in a moved record."""
    # The object id of bytes-with-CR will differ from bytes-without-CR.
    data_clean = b"hello\n"
    data_dirty = b"hello\r\n"
    id_clean = changelog._compute_git_object_id(data_clean, "sha1")
    id_dirty = changelog._compute_git_object_id(data_dirty, "sha1")
    assert id_clean != id_dirty


# ── AC-B7: bounds ─────────────────────────────────────────────────────────────


def test_bundle_part_refused_if_over_size_limit(tmp_path: Path) -> None:
    """AC-B7: a part over 1,048,576 bytes is refused by the reader."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Create a bundle part that is just over the size limit.
    part = bundle_dir / "2026-10-00.bundle"
    # Write a file that's too big (content does not matter; testing the byte bound).
    part.write_bytes(b"x" * (changelog.MAX_BUNDLE_BYTES + 1))
    fs = changelog._file_safety()
    try:
        changelog._collect_bundle_records(bundle_dir, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError) as exc:
        assert (
            str(changelog.MAX_BUNDLE_BYTES) in str(exc)
            or "bound" in str(exc).lower()
            or "bytes" in str(exc).lower()
            or "size" in str(exc).lower()
        ), f"error message does not reference the byte bound: {exc}"
    else:
        raise AssertionError(
            "over-size bundle part was accepted; expected FragmentValidationError "
            "or UnsafeContentError naming the byte bound"
        )


def test_record_count_cap_is_enforced(tmp_path: Path, monkeypatch) -> None:
    """AC-B7: more than 65,536 records across both forms is refused.

    Constant check: the cap is set to the specified value.

    Behavioural check: monkeypatches ``MAX_RECORD_COUNT`` to 3, builds a
    mixed record set (1 loose fragment + 1 bundle part holding 3 records = 4
    total), asserts the reader raises ``BundleValidationError`` naming the
    bound; and that a set of exactly 3 records (1 loose + 1 part with 2
    records) is accepted.
    """
    assert changelog.MAX_RECORD_COUNT == 65_536

    monkeypatch.setattr(changelog, "MAX_RECORD_COUNT", 3)

    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    SEPARATOR = "+++ record +++\n"

    # Loose fragment (counts as 1).
    frag_id = "11111111-1111-4111-8111-111111111111"
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", frag_id
    )
    frag_text = _fragment_text(fragment_id=frag_id, anchor=anchor, date="2026-10-01")
    (frag_dir / f"{frag_id}.md").write_text(frag_text, encoding="utf-8")

    # Bundle part with 3 records (counts as 3 more = total 4 → over the cap).
    # All bundled records use version "3.0.0" to match _fragment_text's default
    # packages string so the anchor recomputation inside the validator agrees.
    def _bundled(idx: int) -> str:
        bid = f"2222222{idx}-2222-4222-8222-222222222222"
        banc = changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-09-01", bid
        )
        return _fragment_text(fragment_id=bid, anchor=banc, date="2026-09-01")

    part_content = SEPARATOR + _bundled(0) + SEPARATOR + _bundled(1) + SEPARATOR + _bundled(2)
    (bundle_dir / "2026-09-01.bundle").write_text(part_content, encoding="utf-8")

    # 4 total (1 loose + 3 bundled) > cap of 3 → must refuse with a diagnostic.
    try:
        changelog.collect_changelog_records(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert "3" in msg, (
            f"FragmentValidationError does not name the bound (3): {msg!r}"
        )
    else:
        raise AssertionError(
            "collect_changelog_records did not refuse 4 records when cap=3"
        )

    # 3 total (1 loose + 2 bundled) == cap → must accept.
    part_content_2 = SEPARATOR + _bundled(0) + SEPARATOR + _bundled(1)
    (bundle_dir / "2026-09-01.bundle").write_text(part_content_2, encoding="utf-8")
    loose, bundled = changelog.collect_changelog_records(
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )
    assert len(loose) + len(bundled) == 3, (
        f"collect_changelog_records refused exactly-3 records: got {len(loose) + len(bundled)}"
    )


# ── AC-B8: single reader and ceiling ─────────────────────────────────────────


def test_file_safety_helper_loads_once_for_collect_changelog_records(
    tmp_path: Path, monkeypatch,
) -> None:
    """AC-B1 extended: one helper load for collect_changelog_records."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    _write_fragment(frag_dir)
    loads = 0
    original = changelog._file_safety

    def counted():
        nonlocal loads
        loads += 1
        return original()

    monkeypatch.setattr(changelog, "_file_safety", counted)
    changelog.collect_changelog_records(
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        retraction_path=tmp_path / "no-retractions.toml",
    )
    assert loads == 1


# ── AC-B6: compaction ────────────────────────────────────────────────────────


def test_compact_requires_real_month(tmp_path: Path) -> None:
    """AC-B6: compact refuses a non-real month."""
    try:
        changelog.compact_month(
            "2026-13",
            fragment_dir=tmp_path / "d",
            bundle_dir=tmp_path / "m",
        )
    except changelog.FragmentValidationError as e:
        assert "month" in str(e).lower() or "YYYY-MM" in str(e)
    else:
        raise AssertionError("invalid month was accepted")


def test_compact_does_not_read_clock(tmp_path: Path, monkeypatch) -> None:
    """AC-B6: compact must not read the wall clock; the month is the only time source.

    Creates real released fragments for 2026-10, patches every clock entry
    point reachable from changelog.compact_month (date.today via the module's
    ``date`` attribute, and time.time/time.localtime within the module
    namespace), runs compaction, and asserts it succeeded. The patched wrappers
    raise AssertionError on any clock call, so the test fails if compact ever
    queries the wall time.
    """
    import datetime as _dt

    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    # Write a real released fragment for 2026-10.
    frag_id = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", frag_id
    )
    text = _fragment_text(
        fragment_id=frag_id,
        anchor=anchor,
        date="2026-10-01",
    )
    (frag_dir / f"{frag_id}.md").write_text(text, encoding="utf-8")

    # Build a proxy for the `date` class that raises if any clock method is called.
    # The metaclass overrides __instancecheck__ so that isinstance(x, _NoClock)
    # accepts any real datetime.date instance; without this, the fragment validator's
    # ``isinstance(data["date"], date)`` check would always fail once date is patched.
    real_date = _dt.date

    class _NoClockMeta(type(real_date)):
        def __instancecheck__(cls, instance: object) -> bool:
            return isinstance(instance, real_date)

    class _NoClock(real_date, metaclass=_NoClockMeta):
        @classmethod
        def today(cls):  # type: ignore[override]
            raise AssertionError("compact_month called date.today() — clock read forbidden")

        @classmethod
        def fromtimestamp(cls, *a, **kw):  # type: ignore[override]
            raise AssertionError(
                "compact_month called date.fromtimestamp() — clock read forbidden"
            )

    # Patch changelog.date with our no-clock proxy.
    monkeypatch.setattr(changelog, "date", _NoClock)

    # Also intercept time module if compact somehow reaches it.
    import time as _time

    def _no_time(*a, **kw):
        raise AssertionError("compact_month called time.time() — clock read forbidden")

    def _no_localtime(*a, **kw):
        raise AssertionError("compact_month called time.localtime() — clock read forbidden")

    monkeypatch.setattr(_time, "time", _no_time)
    monkeypatch.setattr(_time, "localtime", _no_localtime)

    # Run the real compaction — it must move the fragment without reading the clock.
    created, deleted = changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )

    assert len(created) == 1, f"expected 1 bundle part created, got {created}"
    assert len(deleted) == 1, f"expected 1 fragment deleted, got {deleted}"
    assert not (frag_dir / f"{frag_id}.md").exists(), "fragment should have been deleted"
    # Verify the bundle part contains the moved record.
    part_bytes = created[0].read_bytes()
    records = changelog._parse_bundle_part(created[0], part_bytes)
    assert len(records) == 1 and records[0][1].id == frag_id, (
        "bundle part does not contain the expected record"
    )


def test_compact_moves_released_fragment_to_bundle(tmp_path: Path) -> None:
    """AC-B6: compact moves a released fragment into a bundle part."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Write a fragment dated 2026-10.
    frag_id = "66666666-6666-4666-8666-666666666666"
    anchor = "core300--2026-10-01-66666666666646668666666666666666"
    text = _fragment_text(
        fragment_id=frag_id,
        anchor=anchor,
        date="2026-10-01",
    )
    (frag_dir / f"{frag_id}.md").write_text(text, encoding="utf-8")
    created, deleted = changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    assert len(created) == 1
    assert len(deleted) == 1
    assert not (frag_dir / f"{frag_id}.md").exists()
    # Bundle part should contain the record.
    part_bytes = created[0].read_bytes()
    records = changelog._parse_bundle_part(created[0], part_bytes)
    assert len(records) == 1
    assert records[0][1].id == frag_id


def test_compact_leaves_pending_fragment(tmp_path: Path) -> None:
    """AC-B6: compact does not move an unreleased (pending) fragment."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_id = "77777777-7777-4777-8777-777777777777"
    anchor = "core400--2026-10-01-77777777777747778777777777777777"
    text = _fragment_text(
        fragment_id=frag_id,
        anchor=anchor,
        date="2026-10-01",
        packages='[[packages]]\nname = "core"\nversion = "4.0.0"',
    )
    (frag_dir / f"{frag_id}.md").write_text(text, encoding="utf-8")
    # core 4.0.0 is NOT in the released inventory.
    created, deleted = changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    assert len(created) == 0
    assert len(deleted) == 0
    assert (frag_dir / f"{frag_id}.md").exists()


def test_compact_reruns_complete_deletion(tmp_path: Path) -> None:
    """AC-B6: a rerun of compact for a month that was partially deleted completes."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_id = "88888888-8888-4888-8888-888888888888"
    anchor = "core300--2026-10-01-88888888888848888888888888888888"
    text = _fragment_text(fragment_id=frag_id, anchor=anchor, date="2026-10-01")
    frag_path = frag_dir / f"{frag_id}.md"
    frag_path.write_text(text, encoding="utf-8")
    # First compact: creates the bundle part.
    created, _ = changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    assert len(created) == 1
    # Simulate the fragment NOT being deleted (simulating a crash).
    frag_path.write_text(text, encoding="utf-8")
    # Rerun: the fragment is already bundled, so it should be deleted.
    created2, deleted2 = changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    # The spec (AC-B6) is unambiguous: the rerun completes the deletion.
    assert not frag_path.exists()


def test_compact_leaves_view_byte_identical(tmp_path: Path) -> None:
    """AC-B6: the complete view is byte-identical after compaction."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_id = "99999999-9999-4999-8999-999999999999"
    anchor = "core300--2026-10-01-99999999999949998999999999999999"
    text = _fragment_text(fragment_id=frag_id, anchor=anchor, date="2026-10-01")
    (frag_dir / f"{frag_id}.md").write_text(text, encoding="utf-8")
    baseline = "# Changelog\n\n## [1.0.0] — 2020-01-01\n\n### Highlights\n- Old.\n"
    released = {"core": {"3.0.0"}}
    # Assemble before compact.
    loose_before = changelog.collect_validated_fragments(
        frag_dir, enumerator=lambda _: [frag_dir / f"{frag_id}.md"]
    )
    view_before = changelog.assemble_changelog(baseline, loose_before, released_versions=released)
    # Compact.
    changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions=released,
    )
    # Assemble after compact.
    loose_after, bundled_after = changelog.collect_changelog_records(
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        retraction_path=tmp_path / "no-retractions.toml",
    )
    all_records = loose_after + bundled_after
    view_after = changelog.assemble_changelog(baseline, all_records, released_versions=released)
    assert view_before == view_after


# ── AC-B4a: retraction ────────────────────────────────────────────────────────


def test_retract_removes_record_and_appends_list_entry(tmp_path: Path) -> None:
    """AC-B4a: retract removes the record from its part and appends to the list."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"
    rec = _bundle_fragment_text()
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    (bundle_dir / "2026-10-00.bundle").write_bytes(content)
    changelog.retract_record(
        VALID_ID_B, "other",
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )
    # Part should be deleted (only record removed).
    assert not (bundle_dir / "2026-10-00.bundle").exists()
    # Retraction list should exist and contain the entry.
    assert retraction_path.exists()
    import tomllib as _tomllib
    data = _tomllib.loads(retraction_path.read_text(encoding="utf-8"))
    retractions = data.get("retraction", [])
    assert any(e.get("category") == "other" for e in retractions)


def test_retract_rerun_completes_when_record_already_removed(tmp_path: Path) -> None:
    """AC-B4a: rerunning retract for an already-retracted id completes."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"
    rec = _bundle_fragment_text()
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    (bundle_dir / "2026-10-00.bundle").write_bytes(content)
    # First retraction.
    changelog.retract_record(
        VALID_ID_B, "credential",
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )
    # Rerun should not raise.
    changelog.retract_record(
        VALID_ID_B, "credential",
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )


def test_retract_last_record_deletes_part(tmp_path: Path) -> None:
    """AC-B4a: retracting the last record of a part deletes the part."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"
    rec = _bundle_fragment_text()
    part_path = bundle_dir / "2026-10-00.bundle"
    part_path.write_bytes(changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8"))
    changelog.retract_record(
        VALID_ID_B, "legal",
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )
    assert not part_path.exists(), "part should be deleted after retracting last record"


def test_retraction_list_entry_has_required_fields(tmp_path: Path) -> None:
    """AC-B4a: each retraction list entry has a UUIDv4 id and a valid category."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"
    rec = _bundle_fragment_text()
    (bundle_dir / "2026-10-00.bundle").write_bytes(
        changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    )
    changelog.retract_record(
        VALID_ID_B, "personal-data",
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )
    import tomllib as _tomllib
    data = _tomllib.loads(retraction_path.read_text(encoding="utf-8"))
    for entry in data.get("retraction", []):
        assert "id" in entry and "category" in entry
        from uuid import UUID as _UUID
        parsed = _UUID(entry["id"], version=4)
        assert parsed.version == 4
        assert entry["category"] in changelog._RETRACTION_CATEGORIES


def test_validate_retraction_list_refuses_unknown_fields(tmp_path: Path) -> None:
    """AC-B4a: retraction list entries with unknown fields are refused."""
    path = tmp_path / "changelog-retractions.toml"
    path.write_text(
        '[[retraction]]\nid = "11111111-1111-4111-8111-111111111111"\n'
        'category = "other"\nextra = "not allowed"\n',
        encoding="utf-8",
    )
    try:
        changelog._validate_retraction_list(path, [
            {"id": "11111111-1111-4111-8111-111111111111",
             "category": "other", "extra": "not allowed"}
        ])
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and "known" in str(e).lower()
    else:
        raise AssertionError("unknown field was accepted")


def test_validate_retraction_list_refuses_duplicate_ids(tmp_path: Path) -> None:
    """AC-B4a: duplicate retraction ids are refused."""
    path = tmp_path / "changelog-retractions.toml"
    try:
        changelog._validate_retraction_list(path, [
            {"id": "11111111-1111-4111-8111-111111111111", "category": "other"},
            {"id": "11111111-1111-4111-8111-111111111111", "category": "credential"},
        ])
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and "unique" in str(e).lower()
    else:
        raise AssertionError("duplicate retraction id was accepted")


# ── AC-B4b: retraction procedure text is present ─────────────────────────────


def test_retraction_procedure_text_in_agents_md() -> None:
    """AC-B4b: docs/product/AGENTS.md states the retraction procedure."""
    agents_md = Path(__file__).resolve().parent.parent / "docs/product/AGENTS.md"
    text = agents_md.read_text(encoding="utf-8")
    # Three required statements.
    assert "contain" in text.lower() or "rotate" in text.lower(), (
        "AGENTS.md does not say to contain/rotate a leaked credential first"
    )
    assert "diff" in text.lower() or "git history" in text.lower(), (
        "AGENTS.md does not mention that the diff/history still discloses"
    )
    assert "history rewrite" in text.lower() or "separate decision" in text.lower(), (
        "AGENTS.md does not state that any history rewrite is a separate decision"
    )


# ── AC-B8: ceiling thresholds ─────────────────────────────────────────────────


def test_ceiling_constants_match_adr_0143() -> None:
    """AC-B8: the threshold constants match ADR-0143 D9."""
    assert changelog.LOOSE_RELEASED_WARN_THRESHOLD == 375
    assert changelog.LOOSE_RELEASED_REFUSE_THRESHOLD == 500
    assert changelog.PENDING_WARN_THRESHOLD == 250


# ── AC-B8a: release evidence rules ───────────────────────────────────────────


# (AC-B8a tests live in test_check_release_impact.py — see below.)


# ── AC-B8b: release checklist compact step ───────────────────────────────────


def test_release_checklist_mentions_compact_step() -> None:
    """AC-B8b: packs/AGENTS.local.md states the compact step in the checklist."""
    agents_local = (
        Path(__file__).resolve().parent.parent / "packs" / "AGENTS.local.md"
    )
    text = agents_local.read_text(encoding="utf-8")
    assert "compact" in text.lower(), (
        "packs/AGENTS.local.md does not mention the compact step"
    )


# ── AC-B11: validate command exists ──────────────────────────────────────────


def test_validate_command_exits_zero_outside_git(tmp_path: Path) -> None:
    """AC-B11: `changelog.py validate` exits 0 when not in a git repo."""
    import subprocess as _subprocess
    result = _subprocess.run(
        [
            "python3",
            str(Path(__file__).resolve().parent / "changelog.py"),
            "validate",
        ],
        capture_output=True,
        cwd=str(tmp_path),  # not a git repo
    )
    assert result.returncode == 0


# ── AC-B9: merge replay with bundle parts on base ────────────────────────────


def test_bundle_merge_properties(tmp_path: Path) -> None:
    """AC-B9: bundle parts on the base do not conflict with fragment-adding branches.

    Replays five scenarios with ``git merge-tree --write-tree --name-only
    --merge-base=<base>`` in a throwaway git repository in tmp_path using
    Git's default merge behaviour (no merge.renames override):

    1. Twenty fragment-adding branches built on a base that contains a bundle
       part: all 190 unordered pairs are clean (0 conflicts, 0 errors).
    2. A fragment-adding branch (new file) vs a compaction commit (deletes a
       different fragment, creates a bundle part): clean merge.
    3. A body edit to a fragment vs a compaction that bundles it together with
       two other records (3-record part): modify/delete conflict (rc=1).
    3a. A body edit to a fragment vs a compaction into a 1-record part: either
        rc=1 (git detects the conflict), OR the merged bundle bytes are
        identical to the original compact bytes (the edit did not land). If
        git rename-merges silently AND the bundle content changed, the test
        fails — the edit would have landed without any conflict.
    4. Two concurrent compactions of the same month that each write the same
       bundle-part path with different content: add/add conflict (rc=1).
    """
    import itertools
    import os
    import subprocess

    _GIT_REDIRECTS = (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    )
    env: dict[str, str] = {
        k: v for k, v in os.environ.items() if k not in _GIT_REDIRECTS
    }
    env.update(
        {
            "GIT_AUTHOR_NAME": "changelog-b9-test",
            "GIT_AUTHOR_EMAIL": "test@invalid",
            "GIT_COMMITTER_NAME": "changelog-b9-test",
            "GIT_COMMITTER_EMAIL": "test@invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
        }
    )

    def _run(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"git {' '.join(args)}: {result.stderr.strip()}"
            )
        return result.stdout.strip()

    def _merge_tree(
        base: str, ours: str, theirs: str
    ) -> tuple[int, str, tuple[str, ...]]:
        """Return (returncode, raw_stdout, named_paths)."""
        result = subprocess.run(
            [
                "git",
                "-C",
                str(tmp_path),
                "merge-tree",
                "--write-tree",
                "--name-only",
                f"--merge-base={base}",
                ours,
                theirs,
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        paths = tuple(line for line in result.stdout.splitlines() if line)
        return result.returncode, result.stdout, paths

    # ── Initialise repository (default Git merge behaviour, no renames override) ─
    _run("init")
    _run("config", "user.email", "test@invalid")
    _run("config", "user.name", "changelog-b9-test")

    bundle_dir = tmp_path / "docs" / "product" / "changelog.months"
    bundle_dir.mkdir(parents=True)
    frag_dir = tmp_path / "docs" / "product" / "changelog.d"
    frag_dir.mkdir(parents=True)

    SEPARATOR = "+++ record +++\n"

    # Base: a bundle part for 2026-08 (already released) plus two loose
    # fragments for 2026-09.  fragment-X will be compacted; fragment-W is a
    # bystander that keeps changelog.d/ non-empty after compaction.
    (bundle_dir / "2026-08-01.bundle").write_text(
        SEPARATOR
        + "## Released\n\n### core 2.0.0 — 2026-08-01\n- base entry\n"
        + "<!-- aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa -->\n",
        encoding="utf-8",
    )

    frag_x_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    frag_x_path = frag_dir / f"{frag_x_id}.md"
    frag_x_content = (
        "## Released\n\n### core 3.0.0 — 2026-09-01\n- feature X\n"
        f"<!-- {frag_x_id} -->\n"
    )
    frag_x_path.write_text(frag_x_content, encoding="utf-8")

    frag_w_id = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
    frag_w_path = frag_dir / f"{frag_w_id}.md"
    (frag_w_path).write_text(
        "## Released\n\n### core 3.0.1 — 2026-09-02\n- feature W\n"
        f"<!-- {frag_w_id} -->\n",
        encoding="utf-8",
    )

    _run("add", ".")
    _run("commit", "-m", "base")
    base_sha = _run("rev-parse", "HEAD")

    def _checkout_base() -> None:
        _run("checkout", "--detach", base_sha)

    # ── Scenario 1: twenty fragment-adding branches on a base with bundle part ─
    # All 190 unordered pairs must merge cleanly (0 conflicts, 0 errors).

    BRANCH_COUNT = 20
    fragment_shas: list[str] = []
    for idx in range(BRANCH_COUNT):
        _checkout_base()
        branch = f"add-frag-{idx:02d}"
        _run("checkout", "-b", branch)
        new_frag_id = f"cc{idx:06d}00-cccc-4ccc-8ccc-cccccccccccc"
        frag_content = (
            "## Released\n\n### core 3.1.0 — 2026-09-15\n"
            f"- feature {idx}\n<!-- {new_frag_id} -->\n"
        )
        (frag_dir / f"{new_frag_id}.md").write_text(frag_content, encoding="utf-8")
        _run("add", ".")
        _run("commit", "-m", f"add fragment {idx:02d}")
        fragment_shas.append(_run("rev-parse", "HEAD"))

    pairs = list(itertools.combinations(fragment_shas, 2))
    assert len(pairs) == BRANCH_COUNT * (BRANCH_COUNT - 1) // 2 == 190
    clean_1 = conflicts_1 = errors_1 = 0
    for sha_a, sha_b in pairs:
        rc, _, _ = _merge_tree(base_sha, sha_a, sha_b)
        if rc == 0:
            clean_1 += 1
        elif rc == 1:
            conflicts_1 += 1
        else:
            errors_1 += 1

    assert errors_1 == 0, (
        f"Scenario 1: {errors_1} harness errors in {len(pairs)} fragment-adding pairs"
    )
    assert conflicts_1 == 0, (
        f"Scenario 1: {conflicts_1} of {len(pairs)} fragment-adding pairs conflicted"
    )
    assert clean_1 == 190

    # ── Scenario 2: fragment-adding branch vs compaction → clean ─────────────

    _checkout_base()
    _run("checkout", "-b", "compact-a")
    compact_bundle_path = bundle_dir / "2026-09-01.bundle"
    # 1-record part: contains only frag-X.
    compact_1rec_bytes = (SEPARATOR + frag_x_content).encode("utf-8")
    compact_bundle_path.write_bytes(compact_1rec_bytes)
    frag_x_path.unlink()
    _run("add", ".")
    _run("commit", "-m", "compact 2026-09 (1-record)")
    compact_sha = _run("rev-parse", "HEAD")

    rc_2, _, paths_2 = _merge_tree(base_sha, fragment_shas[0], compact_sha)
    assert rc_2 == 0, (
        f"Scenario 2: fragment-adding vs compaction conflicted "
        f"(rc={rc_2}, paths={paths_2})"
    )

    # Build the edit-sha used by Scenario 3 (and documented end-to-end in
    # test_one_record_bundle_edit_caught_by_validator for Scenario 3a).
    _checkout_base()
    _run("checkout", "-b", "edit-x")
    frag_x_path.write_text(
        frag_x_content.replace("feature X", "feature X — updated"),
        encoding="utf-8",
    )
    _run("add", ".")
    _run("commit", "-m", "edit fragment X body")
    edit_sha = _run("rev-parse", "HEAD")

    # ── Scenario 3: body edit vs 3-record compaction → modify/delete conflict ─
    # A bundle with three records drops below git's rename-similarity threshold
    # so git treats the delete as a true delete, not a rename.

    _checkout_base()
    _run("checkout", "-b", "compact-3rec")
    pad1 = (
        "## Released\n\n### core 3.0.2 — 2026-09-03\n- pad 1\n"
        "<!-- eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee -->\n"
    )
    pad2 = (
        "## Released\n\n### core 3.0.3 — 2026-09-04\n- pad 2\n"
        "<!-- ffffffff-ffff-4fff-8fff-ffffffffffff -->\n"
    )
    compact_bundle_path.write_text(
        SEPARATOR + frag_x_content + SEPARATOR + pad1 + SEPARATOR + pad2,
        encoding="utf-8",
    )
    frag_x_path.unlink()
    _run("add", ".")
    _run("commit", "-m", "compact 2026-09 (3-record)")
    compact_3rec_sha = _run("rev-parse", "HEAD")

    rc_3, _, paths_3 = _merge_tree(base_sha, edit_sha, compact_3rec_sha)
    assert rc_3 == 1, (
        f"Scenario 3: body-edit vs 3-record compaction did not produce a conflict "
        f"(rc={rc_3}, paths={paths_3})"
    )

    # ── Scenario 4: two compactions of the same month → conflict ─────────────
    # Both branches compact frag-X into 2026-09-01.bundle but include different
    # padding records so the two bundles are distinct and cannot be resolved by
    # a textual 3-way merge.  Three-record bundles also fall below git's
    # rename-similarity threshold so git treats each as an independent ADD (not
    # a rename of frag-X), producing a true add/add conflict.

    pad3 = (
        "## Released\n\n### core 3.0.4 — 2026-09-05\n- pad 3\n"
        "<!-- gggggggg-gggg-4ggg-8ggg-gggggggggggg -->\n"
    )
    pad4 = (
        "## Released\n\n### core 3.0.5 — 2026-09-06\n- pad 4\n"
        "<!-- hhhhhhhh-hhhh-4hhh-8hhh-hhhhhhhhhhhh -->\n"
    )

    _checkout_base()
    _run("checkout", "-b", "compact-4a")
    compact_bundle_path.write_text(
        SEPARATOR + frag_x_content + SEPARATOR + pad1 + SEPARATOR + pad2,
        encoding="utf-8",
    )
    frag_x_path.unlink()
    _run("add", ".")
    _run("commit", "-m", "compact 2026-09 (4a: frag-X+pad1+pad2)")
    compact_4a_sha = _run("rev-parse", "HEAD")

    _checkout_base()
    _run("checkout", "-b", "compact-4b")
    compact_bundle_path.write_text(
        SEPARATOR + frag_x_content + SEPARATOR + pad3 + SEPARATOR + pad4,
        encoding="utf-8",
    )
    frag_x_path.unlink()
    _run("add", ".")
    _run("commit", "-m", "compact 2026-09 (4b: frag-X+pad3+pad4)")
    compact_4b_sha = _run("rev-parse", "HEAD")

    rc_4, _, paths_4 = _merge_tree(base_sha, compact_4a_sha, compact_4b_sha)
    assert rc_4 == 1, (
        f"Scenario 4: two concurrent compactions did not conflict "
        f"(rc={rc_4}, paths={paths_4})"
    )


# ── AC-B9 Scenario 3a: validator catches rename-merged bundle edit ────────────


def test_one_record_bundle_edit_caught_by_validator(tmp_path: Path) -> None:
    """AC-B9 Scenario 3a: validate_changelog_cross_form_identity catches a body
    edit that git silently applied to a one-record bundle via rename detection.

    Setup (throwaway git repo in ``tmp_path``):
    - Base commit: one released fragment (frag-X) plus a bystander (frag-W
      with an unreleased version, keeping ``changelog.d/`` non-empty after
      compaction).
    - ``compact`` branch: ``compact_month`` bundles frag-X into a one-record
      part and deletes the fragment.  Committed.  ``refs/remotes/origin/main``
      is set to this commit so the validator has a merge base.
    - ``edit-body`` branch: the fragment body is modified.  Committed.
    - Merge: ``git merge-tree`` merges edit-body into the compact commit and
      the result is materialised as a real merge commit (via ``commit-tree``).
      The merge is expected to be clean (rc=0) because git's rename detection
      treats the compaction as a rename and applies the edit to the bundle.
    - Validator: ``validate_changelog_cross_form_identity`` compares the
      bundle bytes at the merge-base (compact commit) against the bundle bytes
      at HEAD (merged result) and raises ``FragmentValidationError`` naming the
      record id and "bundled record bytes changed".
    """
    import os
    import subprocess

    _GIT_REDIRECTS = (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    )
    env: dict[str, str] = {
        k: v for k, v in os.environ.items() if k not in _GIT_REDIRECTS
    }
    env.update(
        {
            "GIT_AUTHOR_NAME": "changelog-b9-test",
            "GIT_AUTHOR_EMAIL": "test@invalid",
            "GIT_COMMITTER_NAME": "changelog-b9-test",
            "GIT_COMMITTER_EMAIL": "test@invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
        }
    )

    def _run(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
        return result.stdout.strip()

    # ── Initialise throwaway repo ─────────────────────────────────────────────
    _run("init")
    _run("config", "user.email", "test@invalid")
    _run("config", "user.name", "changelog-b9-test")

    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # ── Fragments ─────────────────────────────────────────────────────────────
    # frag-X: released (version 3.0.0), to be compacted.
    frag_x_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    frag_x_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-09-01", frag_x_id
    )
    frag_x_text = _fragment_text(
        fragment_id=frag_x_id, anchor=frag_x_anchor, date="2026-09-01"
    )
    frag_x_path = frag_dir / f"{frag_x_id}.md"
    frag_x_path.write_text(frag_x_text, encoding="utf-8")

    # frag-W: bystander with version 3.0.1 (not in released_versions).
    # Keeps changelog.d/ non-empty after frag-X is deleted, preventing git's
    # directory rename heuristic from firing on the containing folder.
    frag_w_id = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
    frag_w_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.1"}], "2026-09-02", frag_w_id
    )
    frag_w_text = _fragment_text(
        fragment_id=frag_w_id,
        anchor=frag_w_anchor,
        date="2026-09-02",
        packages='[[packages]]\nname = "core"\nversion = "3.0.1"',
    )
    (frag_dir / f"{frag_w_id}.md").write_text(frag_w_text, encoding="utf-8")

    # ── Base commit ───────────────────────────────────────────────────────────
    _run("add", ".")
    _run("commit", "-m", "base")
    base_sha = _run("rev-parse", "HEAD")

    # Set origin/main to base temporarily so collect_validated_fragments
    # can resolve the merge-base context when compact_month calls it.
    _run("update-ref", "refs/remotes/origin/main", base_sha)

    # ── Compact branch ────────────────────────────────────────────────────────
    _run("checkout", "-b", "compact")
    created, deleted = changelog.compact_month(
        "2026-09",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    assert len(created) == 1, f"compact_month should create 1 bundle part; got {created}"
    assert len(deleted) == 1, f"compact_month should delete 1 fragment; got {deleted}"
    _run("add", ".")
    _run("commit", "-m", "compact 2026-09")
    compact_sha = _run("rev-parse", "HEAD")

    # Update origin/main to the compact commit: this is the "merge base" the
    # validator will compare the merged bundle against.
    _run("update-ref", "refs/remotes/origin/main", compact_sha)

    # ── Edit-body branch ──────────────────────────────────────────────────────
    _run("checkout", "--detach", base_sha)
    _run("checkout", "-b", "edit-body")
    # Restore frag-X (checkout restores it from base_sha).
    edited_frag_x_text = frag_x_text.replace(
        "- Adds per-update changelog sources.",
        "- Adds per-update changelog sources.\n- EDITED",
    )
    frag_x_path.write_text(edited_frag_x_text, encoding="utf-8")
    _run("add", ".")
    _run("commit", "-m", "body edit to frag-X")
    edit_sha = _run("rev-parse", "HEAD")

    # ── Materialise the merge commit ──────────────────────────────────────────
    # git merge-tree (default rename detection) should merge cleanly (rc=0):
    # the compaction looks like a rename of frag-X into the bundle, and git
    # applies the body edit to the new bundle location.
    mt = subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "merge-tree",
            "--write-tree",
            "--name-only",
            f"--merge-base={base_sha}",
            edit_sha,
            compact_sha,
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert mt.returncode == 0, (
        f"Scenario 3a: expected clean rename-merge (rc=0) but got rc={mt.returncode}.\n"
        f"stdout: {mt.stdout!r}\nstderr: {mt.stderr!r}"
    )
    merged_tree_sha = next(ln for ln in mt.stdout.splitlines() if ln)

    # Create a real merge commit so git history contains the merge-base.
    merge_commit = _run(
        "commit-tree", merged_tree_sha,
        "-p", edit_sha,
        "-p", compact_sha,
        "-m", "merge edit-body into compact (rename-merged)",
    )

    # Check out the merge commit to update the working tree.
    _run("checkout", "-b", "on-merged", merge_commit)

    # ── Validator assertion ───────────────────────────────────────────────────
    # HEAD = merge_commit (parents: edit_sha, compact_sha).
    # origin/main = compact_sha.
    # git merge-base origin/main HEAD = compact_sha.
    # The validator compares the bundle bytes at compact_sha (original) against
    # the bundle bytes at HEAD (edited via rename-merge) and must raise.
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert frag_x_id in msg, (
            f"FragmentValidationError does not name the record id {frag_x_id!r}: "
            f"{msg!r}"
        )
        assert "bundled record bytes changed" in msg, (
            f"FragmentValidationError does not say 'bundled record bytes changed': "
            f"{msg!r}"
        )
    else:
        raise AssertionError(
            "validate_changelog_cross_form_identity did not refuse the "
            "rename-merged bundle (edit landed without detection)"
        )


# ── AC-B10: pages.yml triggers ───────────────────────────────────────────────


def test_pages_yml_triggers_on_bundle_paths() -> None:
    """AC-B10: pages.yml triggers on changelog.months and changelog-retractions.toml."""
    pages_yml = (
        Path(__file__).resolve().parent.parent / ".github/workflows/pages.yml"
    )
    text = pages_yml.read_text(encoding="utf-8")
    assert "changelog.months" in text, (
        "pages.yml does not trigger on docs/product/changelog.months/"
    )
    assert "changelog-retractions.toml" in text, (
        "pages.yml does not trigger on docs/product/changelog-retractions.toml"
    )


# ── inventory parity: compact and build classify the same fragments ───────────


def test_compact_and_collect_agree_on_released_fragments(tmp_path: Path) -> None:
    """AC-B6: compact uses the same released-inventory predicate as collect."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Write two fragments: one released, one pending.
    released_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    released_anchor = "core300--2026-10-01-aaaaaaaaaaaaaaaaa4aaa8aaaaaaaaaaaaaaaa"[:64]
    # Recompute proper anchor.
    released_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", released_id
    )
    released_text = _fragment_text(
        fragment_id=released_id,
        anchor=released_anchor,
        date="2026-10-01",
    )
    (frag_dir / f"{released_id}.md").write_text(released_text, encoding="utf-8")

    pending_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    pending_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "4.0.0"}], "2026-10-02", pending_id
    )
    pending_text = _fragment_text(
        fragment_id=pending_id,
        anchor=pending_anchor,
        date="2026-10-02",
        packages='[[packages]]\nname = "core"\nversion = "4.0.0"',
    )
    (frag_dir / f"{pending_id}.md").write_text(pending_text, encoding="utf-8")

    released_versions = {"core": {"3.0.0"}}
    inventory = changelog._normalize_released_versions(released_versions)
    loose_frags = changelog.collect_validated_fragments(frag_dir)
    released_by_collect = {
        f.id for f in loose_frags
        if changelog._fragment_in_released_inventory(f, inventory)
    }
    created, _ = changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions=released_versions,
    )
    # compact should have bundled only the released fragment.
    if created:
        part_bytes = created[0].read_bytes()
        bundled_records = changelog._parse_bundle_part(created[0], part_bytes)
        bundled_ids = {f.id for _, f in bundled_records}
        assert bundled_ids == released_by_collect


# =============================================================================
# Review-finding fixes: A-G (sustained, adjudication 2026-10-11)
# =============================================================================

# ---------------------------------------------------------------------------
# Fix F — AC-B2 trailing bytes after the last record
# ---------------------------------------------------------------------------


def test_bundle_part_refused_if_trailing_bytes(tmp_path: Path) -> None:
    """Fix F / AC-B2: trailing bytes after the last record are refused.

    A bundle part whose content is SEP + valid_record + extra_LF must be
    refused with a diagnostic naming the 'trailing bytes' invariant.
    """
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    part = bundle_dir / "2026-10-00.bundle"
    rec = _bundle_fragment_text()
    # Add one extra LF after the valid record — this is the 'trailing bytes' case.
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8") + b"\n"
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as exc:
        msg = str(exc).lower()
        assert "trailing" in msg or "separator" in msg, (
            f"error does not name trailing bytes: {exc}"
        )
    else:
        raise AssertionError(
            "bundle part with trailing bytes was accepted; expected FragmentValidationError"
        )


# ---------------------------------------------------------------------------
# Fix C — git merge-base non-zero exit handling
# ---------------------------------------------------------------------------


def test_validate_cross_form_raises_on_merge_base_exit_128(tmp_path: Path) -> None:
    """Fix C: git merge-base exit 128 raises FragmentValidationError (not a skip).

    Exit 1 + 'no merge base' is the only allowed skip; any other non-zero exit
    (e.g., 128 for a repository error) must refuse fail-closed.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    retraction_path = tmp_path / "changelog-retractions.toml"

    _GitResult = changelog._GitResult

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            # Simulate a repository error (e.g., unresolvable remote ref).
            return _GitResult(128, "", "fatal: ambiguous argument 'origin/main'")
        return _GitResult(0, "", "")

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        assert "128" in str(exc) or "merge-base" in str(exc).lower() or "fatal" in str(exc).lower(), (
            f"error does not describe the merge-base failure: {exc}"
        )
    else:
        raise AssertionError(
            "exit-128 from git merge-base was silently skipped; "
            "expected FragmentValidationError"
        )


# ---------------------------------------------------------------------------
# Fix D — malformed merge-base retraction TOML raises instead of pass
# ---------------------------------------------------------------------------


def test_validate_cross_form_raises_on_malformed_base_retraction_toml(
    tmp_path: Path, monkeypatch
) -> None:
    """Fix D: a malformed merge-base retraction list raises FragmentValidationError.

    When the merge-base blob for the retraction list is not valid UTF-8 TOML,
    the append-only check must fail closed rather than silently passing.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Write a current retraction list that differs from the base (triggers the comparison).
    new_entry = '[[retraction]]\nid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"\ncategory = "other"\n'
    retraction_path.write_text(new_entry, encoding="utf-8")

    # Compute a fake object id for the base retraction blob.
    import hashlib as _hashlib
    malformed_blob = b"\xff\xfe not valid utf-8 TOML"  # invalid UTF-8
    header = b"blob " + str(len(malformed_blob)).encode() + b"\0"
    base_retract_obj = _hashlib.sha1(header + malformed_blob, usedforsecurity=False).hexdigest()

    # Valid current retraction content differs from malformed base,
    # so the startswith check fails and we try to parse the base TOML.
    retract_rel = "changelog-retractions.toml"
    ls_tree_output = f"100644 blob {base_retract_obj}\t{retract_rel}\n"

    _GitResult = changelog._GitResult

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, "deadbeef" * 5 + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            return _GitResult(0, ls_tree_output, "")
        return _GitResult(128, "", f"unexpected: {args}")

    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            return (0, str(len(malformed_blob)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            return (0, malformed_blob, "")
        return (128, b"", "unexpected")

    monkeypatch.setattr(changelog, "_git_runner_bytes", fake_bytes)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc).lower()
        assert "toml" in msg or "utf" in msg or "malformed" in msg or "retraction" in msg, (
            f"error does not name the malformed TOML issue: {exc}"
        )
    else:
        raise AssertionError(
            "malformed merge-base retraction TOML was silently passed; "
            "expected FragmentValidationError"
        )


# ---------------------------------------------------------------------------
# Fix B — edited retraction entry is refused
# ---------------------------------------------------------------------------


def test_validate_cross_form_refuses_edited_retraction_entry(
    tmp_path: Path, monkeypatch
) -> None:
    """Fix B / AC-B4a: an edited retraction entry (same id, changed category) is refused.

    When a base entry's category is changed in the current list, validation
    must refuse by name rather than only checking id presence.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Base retraction list: entry with category 'other'.
    base_content = (
        '[[retraction]]\n'
        'id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"\n'
        'category = "other"\n'
    )
    # Current list: same id, different category → edited entry.
    current_content = (
        '[[retraction]]\n'
        'id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"\n'
        'category = "credential"\n'
    )
    retraction_path.write_text(current_content, encoding="utf-8")

    import hashlib as _hashlib
    blob_data = base_content.encode("utf-8")
    header = b"blob " + str(len(blob_data)).encode() + b"\0"
    base_retract_obj = _hashlib.sha1(header + blob_data, usedforsecurity=False).hexdigest()

    # The current content doesn't start with the base (different category line),
    # so the startswith check fails and we fall into per-entry comparison.
    retract_rel = "changelog-retractions.toml"
    ls_tree_output = f"100644 blob {base_retract_obj}\t{retract_rel}\n"

    _GitResult = changelog._GitResult

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, "badbadba" * 5 + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            return _GitResult(0, ls_tree_output, "")
        return _GitResult(128, "", f"unexpected: {args}")

    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            return (0, str(len(blob_data)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            return (0, blob_data, "")
        return (128, b"", "unexpected")

    monkeypatch.setattr(changelog, "_git_runner_bytes", fake_bytes)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        assert "edited" in str(exc).lower() or "changed" in str(exc).lower() or "bbbbbbbb" in str(exc), (
            f"error does not name the edited entry: {exc}"
        )
    else:
        raise AssertionError(
            "edited retraction entry (changed category) was accepted; "
            "expected FragmentValidationError"
        )


def test_validate_cross_form_refuses_deleted_retraction_list(
    tmp_path: Path, monkeypatch
) -> None:
    """AC-B4a: deleting a retraction list the merge base holds is refused.

    Without the list, a retracted id has nothing to collide with, so the
    record could be re-published.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    retraction_path = tmp_path / "changelog-retractions.toml"
    base_content = (
        '[[retraction]]\n'
        'id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"\n'
        'category = "credential"\n'
    )
    blob_data = base_content.encode("utf-8")
    header = b"blob " + str(len(blob_data)).encode() + b"\0"
    base_retract_obj = __import__("hashlib").sha1(header + blob_data, usedforsecurity=False).hexdigest()
    ls_tree_output = f"100644 blob {base_retract_obj}\tchangelog-retractions.toml\n"
    _GitResult = changelog._GitResult

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, "badbadba" * 5 + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            return _GitResult(0, ls_tree_output, "")
        return _GitResult(128, "", f"unexpected: {args}")

    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            return (0, str(len(blob_data)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            return (0, blob_data, "")
        return (128, b"", "unexpected")

    monkeypatch.setattr(changelog, "_git_runner_bytes", fake_bytes)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        assert "present while the merge base lists retractions" in str(exc), (
            f"refused for the wrong reason: {exc}"
        )
    else:
        raise AssertionError("a deleted retraction list was accepted")


# ---------------------------------------------------------------------------
# Fix A — AC-B4 merge-base record set reconstruction (four cases)
# ---------------------------------------------------------------------------

# ── Helper for validate_changelog_cross_form_identity tests ──────────────────

def _fake_validate_git_runner(repo_path: Path, merge_base: str, ls_tree_lines: list):
    """Return a fake git_runner for cross-form identity tests."""
    _GitResult = changelog._GitResult
    ls_output = "\n".join(ls_tree_lines)

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(repo_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, merge_base + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            return _GitResult(0, ls_output + "\n" if ls_output else "", "")
        return _GitResult(128, "", f"unexpected git call: {' '.join(str(a) for a in args)}")

    return fake_git


def _sha1_obj_id(data: bytes) -> str:
    """Compute the git SHA-1 blob object id for raw bytes."""
    import hashlib as _hashlib
    header = b"blob " + str(len(data)).encode() + b"\0"
    return _hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


# ── Test A-1: new id added directly to a part ────────────────────────────────

def test_validate_cross_form_refuses_new_id_added_to_part(tmp_path: Path) -> None:
    """Fix A / AC-B4: a new id added directly to a bundle part is refused.

    The merge base has no records anywhere. The current state has a bundle
    part containing a record whose id was not at the merge base as a loose
    fragment or a bundled record — so the id was authored directly into the
    part, bypassing the loose-fragment authoring step.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Write a bundle part with a record whose id has no merge-base presence.
    brand_new_id = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
    brand_new_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", brand_new_id
    )
    rec = _bundle_fragment_text(
        fragment_id=brand_new_id, anchor=brand_new_anchor, date="2026-10-01"
    )
    part_content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    (bundle_dir / "2026-10-00.bundle").write_bytes(part_content)

    # Merge-base ls-tree: empty — no fragments or bundle parts at base.
    fake_git = _fake_validate_git_runner(tmp_path, "abc1234" * 5, [])

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc).lower()
        assert brand_new_id in str(exc) or "new id" in msg or "directly" in msg, (
            f"error does not name the new-id violation: {exc}"
        )
    else:
        raise AssertionError(
            "new id added directly to a bundle part was accepted; "
            "expected FragmentValidationError"
        )


# ── Test A-2: removed months directory ───────────────────────────────────────

def test_validate_cross_form_refuses_removed_months_directory(
    tmp_path: Path, monkeypatch
) -> None:
    """Fix A / AC-B4: removing the months directory drops all bundled records.

    The merge base has a bundle part. The current state has no months directory.
    Validation must refuse because the bundled ids are absent from current forms.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    # Do NOT create bundle_dir — simulates a removed directory.
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Build the merge-base bundle part content.
    base_id = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
    base_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", base_id
    )
    rec = _bundle_fragment_text(fragment_id=base_id, anchor=base_anchor, date="2026-10-01")
    base_part_bytes = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    base_obj = _sha1_obj_id(base_part_bytes)

    bundle_rel = "changelog.months"
    part_rel = f"{bundle_rel}/2026-10-00.bundle"
    ls_lines = [f"100644 blob {base_obj}\t{part_rel}"]

    fake_git = _fake_validate_git_runner(tmp_path, "def5678" * 5, ls_lines)

    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            return (0, str(len(base_part_bytes)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            return (0, base_part_bytes, "")
        return (128, b"", "unexpected")

    monkeypatch.setattr(changelog, "_git_runner_bytes", fake_bytes)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc).lower()
        assert base_id in str(exc) or "bundled" in msg or "absent" in msg or "missing" in msg, (
            f"error does not name the missing bundled record: {exc}"
        )
    else:
        raise AssertionError(
            "removed months directory (bundled record absent) was accepted; "
            "expected FragmentValidationError"
        )


# ── Test A-3: part-adding change drops an unbundled merge-base fragment ───────

def test_validate_cross_form_refuses_part_adding_drops_fragment(tmp_path: Path) -> None:
    """Fix A / AC-B4: in a part-adding change, dropping a merge-base fragment is refused.

    The merge base has TWO loose fragments (A and B). The current change bundles
    fragment A into a new part (which is correctly in the merge-base ls-tree as
    a loose fragment so check 1 passes for it). Fragment B is gone from the
    current state entirely — not bundled, not retracted. The part-adding check
    must refuse because B is absent.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Fragment A: was loose at merge base, now bundled into the new part.
    frag_a_id = "aaaabbbb-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    frag_a_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", frag_a_id
    )
    rec_a = _bundle_fragment_text(
        fragment_id=frag_a_id, anchor=frag_a_anchor, date="2026-10-01"
    )

    # Fragment B: was loose at merge base, now GONE (not bundled, not retracted).
    frag_b_id = "bbbbcccc-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

    # Current state: new bundle part containing only fragment A.
    part_content = changelog.BUNDLE_SEPARATOR_BYTES + rec_a.encode("utf-8")
    (bundle_dir / "2026-10-00.bundle").write_bytes(part_content)

    # Merge-base ls-tree: both A and B were loose fragments.
    # Fragment A's id is in base_frag_ids → check 1 passes for it.
    # Fragment B's id is in base_frag_ids → check 3 fires (not in current forms).
    frag_a_obj = "a" * 40  # fake object id
    frag_b_obj = "b" * 40  # fake object id
    ls_lines = [
        f"100644 blob {frag_a_obj}\tchangelog.d/{frag_a_id}.md",
        f"100644 blob {frag_b_obj}\tchangelog.d/{frag_b_id}.md",
    ]

    fake_git = _fake_validate_git_runner(tmp_path, "fedc1234" * 5, ls_lines)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc).lower()
        assert (
            frag_b_id in str(exc)
            or "drops" in msg
            or "part-adding" in msg
            or "unbundled" in msg
            or "missing" in msg
        ), f"error does not name the dropped fragment B: {exc}"
    else:
        raise AssertionError(
            "part-adding change that drops a merge-base fragment was accepted; "
            "expected FragmentValidationError"
        )


# ── Test A-4: merge-base bundled id missing (part deleted, not dir removed) ───

def test_validate_cross_form_refuses_missing_bundled_id_part_deleted(
    tmp_path: Path, monkeypatch
) -> None:
    """Fix A / AC-B4: a merge-base bundled id is refused when its part is deleted.

    The merge base has a bundle part. The current months directory exists but
    that specific part file has been deleted (not the whole directory). The
    bundled record's id is no longer in any current form.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Build the merge-base part (now deleted from current state).
    gone_id = "12345678-1234-4234-8234-123456789012"
    gone_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-09-01", gone_id
    )
    rec = _bundle_fragment_text(
        fragment_id=gone_id, anchor=gone_anchor, date="2026-09-01"
    )
    gone_part_bytes = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    gone_obj = _sha1_obj_id(gone_part_bytes)

    # The part file does NOT exist in the current months directory.
    part_rel = "changelog.months/2026-09-00.bundle"
    ls_lines = [f"100644 blob {gone_obj}\t{part_rel}"]

    fake_git = _fake_validate_git_runner(tmp_path, "cafebabe" * 5, ls_lines)

    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            return (0, str(len(gone_part_bytes)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            return (0, gone_part_bytes, "")
        return (128, b"", "unexpected")

    monkeypatch.setattr(changelog, "_git_runner_bytes", fake_bytes)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc).lower()
        assert gone_id in str(exc) or "bundled" in msg or "absent" in msg or "missing" in msg, (
            f"error does not name the missing bundled record: {exc}"
        )
    else:
        raise AssertionError(
            "deleted bundle part with unretracked record was accepted; "
            "expected FragmentValidationError"
        )


# ---------------------------------------------------------------------------
# Fix E — confinement: symlink in bundle directory refused during NN enumeration
# ---------------------------------------------------------------------------


def test_compact_refuses_symlink_in_bundle_dir_during_nn_enumeration(
    tmp_path: Path,
) -> None:
    """Fix E / AC-B3a: compact refuses a symlink in the bundle directory.

    When enumerating existing NN values to determine the next part number,
    compact_month must refuse symlinks in the bundle directory via the blessed
    confined helper rather than using iterdir() which would follow them.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    # Write a real fragment to compact.
    frag_id = "abcdef01-0001-4001-8001-000000000001"
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-11-01", frag_id
    )
    text = _fragment_text(fragment_id=frag_id, anchor=anchor, date="2026-11-01")
    (frag_dir / f"{frag_id}.md").write_text(text, encoding="utf-8")

    # Put a symlink in the bundle directory with a valid bundle name.
    real_target = tmp_path / "elsewhere.bundle"
    real_target.write_bytes(changelog.BUNDLE_SEPARATOR_BYTES + _bundle_fragment_text().encode())
    link = bundle_dir / "2026-11-00.bundle"
    link.symlink_to(real_target)

    # compact_month should refuse because the blessed helper rejects the symlink.
    try:
        changelog.compact_month(
            "2026-11",
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            released_versions={"core": {"3.0.0"}},
        )
    except (changelog.FragmentValidationError, Exception) as exc:
        # Accept any error: the confined helper raises UnsafeContentError which
        # compact_month wraps into FragmentValidationError, or it may propagate
        # the UnsafeContentError directly.
        error_text = str(exc).lower()
        assert (
            "confined" in error_text
            or "symlink" in error_text
            or "unsafe" in error_text
            or "link" in error_text
            or "regular" in error_text
        ), f"error does not name the confinement violation: {exc}"
    else:
        raise AssertionError(
            "compact_month accepted a symlink in the bundle directory "
            "during NN enumeration; expected a confinement error"
        )


# ---------------------------------------------------------------------------
# Fix B / QE-F3 — retract intermediate state: injected-failure fixture
# ---------------------------------------------------------------------------


def test_retract_intermediate_state_refused_by_validation(tmp_path: Path, monkeypatch) -> None:
    """Fix B / AC-B4a / QE-F3: intermediate state after part rewrite but before list append.

    Constructs the intermediate state manually (part rewritten without the
    matching list entry), asserts that validate_changelog_cross_form_identity
    refuses it as an unlisted removal, and that a subsequent retract_record
    call with the same id and category completes the retraction.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Write a bundle part with two records: one to retract, one to keep.
    rec_id = VALID_ID_B
    rec_anchor = VALID_ANCHOR_B
    rec_text = _bundle_fragment_text(fragment_id=rec_id, anchor=rec_anchor, date="2026-10-01")

    keep_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    keep_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-02", keep_id
    )
    keep_text = _bundle_fragment_text(
        fragment_id=keep_id, anchor=keep_anchor, date="2026-10-02"
    )

    part_path = bundle_dir / "2026-10-00.bundle"
    # Sort in canonical order (date desc then id asc): rec_id date="2026-10-01" < keep_id date="2026-10-02"
    # canonical order: date descending → keep_id (2026-10-02) first, then rec_id (2026-10-01)
    original_content = (
        changelog.BUNDLE_SEPARATOR_BYTES + keep_text.encode("utf-8")
        + changelog.BUNDLE_SEPARATOR_BYTES + rec_text.encode("utf-8")
    )
    part_path.write_bytes(original_content)

    # Simulate intermediate state: part rewritten without rec_id, but NO list entry.
    new_part_content = changelog.BUNDLE_SEPARATOR_BYTES + keep_text.encode("utf-8")
    part_path.write_bytes(new_part_content)
    # The retraction list does NOT have rec_id yet — this is the "crashed between writes" state.

    # Build base state: the original part (with both records) was at merge base.
    orig_obj = _sha1_obj_id(original_content)
    part_rel = "changelog.months/2026-10-00.bundle"
    ls_lines = [f"100644 blob {orig_obj}\t{part_rel}"]

    _GitResult = changelog._GitResult

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, "1234abcd" * 5 + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            return _GitResult(0, "\n".join(ls_lines) + "\n", "")
        return _GitResult(128, "", f"unexpected: {args}")

    # Monkeypatch _git_runner_bytes so blob reads return the original part content.
    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            return (0, str(len(original_content)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            return (0, original_content, "")
        return (128, b"", f"unexpected bytes call: {args}")

    monkeypatch.setattr(changelog, "_git_runner_bytes", fake_bytes)

    # Validation should refuse the intermediate state: rec_id removed but not listed.
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        # Good — the intermediate state is correctly refused.
        assert rec_id in str(exc) or "removed" in str(exc).lower() or "retract" in str(exc).lower(), (
            f"error does not name the missing retraction: {exc}"
        )
    else:
        raise AssertionError(
            "intermediate state (part rewritten, list not yet appended) "
            "was accepted; expected FragmentValidationError"
        )

    # Now rerun retract_record to complete the retraction.
    changelog.retract_record(
        rec_id, "other",
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )

    # The retraction list should now have rec_id.
    import tomllib as _tomllib
    data = _tomllib.loads(retraction_path.read_text(encoding="utf-8"))
    listed_ids = {e["id"] for e in data.get("retraction", [])}
    assert rec_id in listed_ids, (
        f"retract_record rerun did not add {rec_id} to the list; got: {listed_ids}"
    )
    # The part should still have keep_id only.
    assert part_path.exists()
    remaining = changelog._parse_bundle_part(part_path, part_path.read_bytes())
    remaining_ids = {f.id for _, f in remaining}
    assert keep_id in remaining_ids and rec_id not in remaining_ids


# ---------------------------------------------------------------------------
# Fix G — compact injected-failure fixtures (QE-F2)
# ---------------------------------------------------------------------------


def test_compact_second_part_write_failure_rolls_back_first_part(
    tmp_path: Path, monkeypatch
) -> None:
    """J1 / AC-B6: a failure writing the second bundle part removes all created parts.

    Two fragments are forced into separate parts by patching MAX_BUNDLE_BYTES to
    exactly one record's size.  The first write_bundle_part call succeeds; the
    second raises.  After the exception:
    - compact_month propagates the failure (raises).
    - The first (already-created) part is removed from disk (pre-deletion cleanup).
    - Both original fragment files still exist (no data loss before deletion phase).
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    id1 = "c1000001-0001-4001-8001-100000000001"
    id2 = "c2000002-0002-4002-8002-200000000002"

    for fid in (id1, id2):
        anchor = changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-12-01", fid
        )
        text = _fragment_text(
            fragment_id=fid,
            anchor=anchor,
            date="2026-12-01",
            packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
        )
        (frag_dir / f"{fid}.md").write_text(text, encoding="utf-8")

    # Measure the raw fragment bytes so the byte bound allows exactly one record per part.
    one_raw = (frag_dir / f"{id1}.md").read_bytes()
    one_record_size = len(changelog.BUNDLE_SEPARATOR_BYTES) + len(one_raw)
    monkeypatch.setattr(changelog, "MAX_BUNDLE_BYTES", one_record_size)

    # Fail on the second write_bundle_part call (first write succeeds, creating one part).
    call_count = [0]
    original_write = changelog.write_bundle_part

    def _failing_write(records, directory, part_name, raw_bytes_map=None):
        call_count[0] += 1
        if call_count[0] >= 2:
            raise RuntimeError("injected second-write failure")
        return original_write(records, directory, part_name, raw_bytes_map)

    monkeypatch.setattr(changelog, "write_bundle_part", _failing_write)

    raised = False
    try:
        changelog.compact_month(
            "2026-12",
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            released_versions={"core": {"3.0.0"}},
        )
    except RuntimeError:
        raised = True

    assert raised, "compact_month did not propagate the injected second-write failure"
    assert call_count[0] >= 2, (
        "write_bundle_part was not called a second time; the split did not produce two parts"
    )

    # Pre-deletion cleanup: the first created part must be gone.
    remaining_parts = list(bundle_dir.iterdir())
    assert not remaining_parts, (
        f"created parts were not removed after second-write failure: "
        f"{[p.name for p in remaining_parts]}"
    )

    # No data loss: both original fragment files must still exist.
    assert (frag_dir / f"{id1}.md").exists(), (
        "fragment 1 was deleted despite write failure"
    )
    assert (frag_dir / f"{id2}.md").exists(), (
        "fragment 2 was deleted despite write failure"
    )


def test_compact_deletion_failure_is_completed_by_rerun(
    tmp_path: Path, monkeypatch
) -> None:
    """J2 / AC-B6: a failure partway through deletion is finished by a rerun.

    The failed run leaves its part and every record present in at least one
    form, refuses visibly, and the rerun deletes the leftover fragment without
    bundling it a second time.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    id1 = "d1000001-0001-4001-8001-100000000001"
    id2 = "d2000002-0002-4002-8002-200000000002"
    for fid in (id1, id2):
        anchor = changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-11-01", fid
        )
        (frag_dir / f"{fid}.md").write_text(
            _fragment_text(
                fragment_id=fid,
                anchor=anchor,
                date="2026-11-01",
                packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
            ),
            encoding="utf-8",
        )
    inventory = {"core": {"3.0.0"}}
    original_unlink = Path.unlink

    def failing_unlink(self, *args, **kwargs):
        if self.name == f"{id2}.md":
            raise OSError("injected deletion failure")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", failing_unlink)
    try:
        changelog.compact_month(
            "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
            released_versions=inventory,
        )
    except changelog.FragmentValidationError as exc:
        assert "rerun compact" in str(exc), f"refused for the wrong reason: {exc}"
    else:
        raise AssertionError("a partial deletion was reported as success")
    monkeypatch.setattr(Path, "unlink", original_unlink)

    parts = sorted(p.name for p in bundle_dir.iterdir())
    assert len(parts) == 1, f"expected the one written part to remain: {parts}"
    bundled = {ff.id for _, _, _, ff in changelog._collect_bundle_records(
        bundle_dir, changelog._file_safety()
    )}
    assert bundled == {id1, id2}
    assert (frag_dir / f"{id2}.md").exists() and not (frag_dir / f"{id1}.md").exists()
    try:
        changelog.collect_changelog_records(fragment_dir=frag_dir, bundle_dir=bundle_dir)
    except changelog.FragmentValidationError as exc:
        assert "duplicate id" in str(exc).lower()
    else:
        raise AssertionError("the interrupted state was accepted despite a duplicate id")

    changelog.compact_month(
        "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
        released_versions=inventory,
    )
    assert sorted(p.name for p in bundle_dir.iterdir()) == parts, (
        "the rerun wrote a new part instead of finishing the deletion"
    )
    assert not list(frag_dir.glob("*.md")), "a fragment of the month is still loose"
    loose, bundled_records = changelog.collect_changelog_records(
        fragment_dir=frag_dir, bundle_dir=bundle_dir
    )
    assert sorted(r.id for r in [*loose, *bundled_records]) == sorted([id1, id2])


def test_compact_rerun_refuses_a_retracted_id_in_the_interrupted_state(
    tmp_path: Path, monkeypatch
) -> None:
    """AC-B4a / AC-B6: rerun recovery applies the reader's retraction refusal.

    A record retracted while it sits in both forms after an interrupted
    compaction must make the rerun refuse, not report success while the
    retracted bytes stay in the part.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"
    id1 = "d1000001-0001-4001-8001-100000000001"
    id2 = "d2000002-0002-4002-8002-200000000002"
    for fid in (id1, id2):
        anchor = changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-11-01", fid
        )
        (frag_dir / f"{fid}.md").write_text(
            _fragment_text(
                fragment_id=fid,
                anchor=anchor,
                date="2026-11-01",
                packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
            ),
            encoding="utf-8",
        )
    inventory = {"core": {"3.0.0"}}
    original_unlink = Path.unlink

    def failing_unlink(self, *args, **kwargs):
        if self.name == f"{id2}.md":
            raise OSError("injected deletion failure")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", failing_unlink)
    try:
        changelog.compact_month(
            "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
            retraction_path=retraction_path, released_versions=inventory,
        )
    except changelog.FragmentValidationError:
        pass
    else:
        raise AssertionError("a partial deletion was reported as success")
    monkeypatch.setattr(Path, "unlink", original_unlink)
    assert (frag_dir / f"{id2}.md").exists(), "setup did not leave the interrupted state"

    retraction_path.write_text(
        f'[[retraction]]\nid = "{id2}"\ncategory = "credential"\n', encoding="utf-8"
    )
    try:
        changelog.compact_month(
            "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
            retraction_path=retraction_path, released_versions=inventory,
        )
    except changelog.FragmentValidationError as exc:
        message = str(exc)
        assert "retracted id" in message and id2 in message, message
    else:
        raise AssertionError("the rerun accepted a retracted id present in both forms")
    assert (frag_dir / f"{id2}.md").exists(), "the refused rerun still deleted the fragment"


def test_compact_rerun_counts_a_record_in_both_forms_once_toward_the_cap(
    tmp_path: Path, monkeypatch
) -> None:
    """AC-B6 / AC-B7: a rerun at exactly the cap's unique count is not refused.

    Mid-compaction one record sits loose and bundled; counting it twice would
    refuse the very rerun AC-B6 requires to finish the move.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    id1 = "d1000001-0001-4001-8001-100000000001"
    id2 = "d2000002-0002-4002-8002-200000000002"
    for fid in (id1, id2):
        anchor = changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-11-01", fid
        )
        (frag_dir / f"{fid}.md").write_text(
            _fragment_text(
                fragment_id=fid,
                anchor=anchor,
                date="2026-11-01",
                packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
            ),
            encoding="utf-8",
        )
    inventory = {"core": {"3.0.0"}}
    original_unlink = Path.unlink

    def failing_unlink(self, *args, **kwargs):
        if self.name == f"{id2}.md":
            raise OSError("injected deletion failure")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", failing_unlink)
    try:
        changelog.compact_month(
            "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
            released_versions=inventory,
        )
    except changelog.FragmentValidationError:
        pass
    else:
        raise AssertionError("a partial deletion was reported as success")
    monkeypatch.setattr(Path, "unlink", original_unlink)
    assert (frag_dir / f"{id2}.md").exists(), "setup did not leave the interrupted state"

    # Two unique records, three physical copies: the cap admits exactly two.
    monkeypatch.setattr(changelog, "MAX_RECORD_COUNT", 2)
    changelog.compact_month(
        "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
        released_versions=inventory,
    )
    assert not (frag_dir / f"{id2}.md").exists(), "the rerun did not finish the move"

# ---------------------------------------------------------------------------
# Fix QE-F6 — zero blob reads for unchanged bundle in cross-form identity
# ---------------------------------------------------------------------------


def test_validate_cross_form_reads_zero_blobs_for_unchanged_bundle(tmp_path: Path) -> None:
    """QE-F6 / ADR-0143 confirmation: unchanged bundle reads no blobs.

    When the merge-base object id of a bundle part matches the current computed
    object id, validate_changelog_cross_form_identity skips the git show call.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Write a bundle part.
    rec = _bundle_fragment_text()
    part_content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part_path = bundle_dir / "2026-10-00.bundle"
    part_path.write_bytes(part_content)

    # Compute the actual SHA-1 object id for this part.
    actual_obj = _sha1_obj_id(part_content)

    # The base tree reports the SAME object id → no blob read should occur.
    bundle_rel = "changelog.months/2026-10-00.bundle"
    ls_lines = [f"100644 blob {actual_obj}\t{bundle_rel}"]

    fake_git = _fake_validate_git_runner(tmp_path, "00abcdef" * 5, ls_lines)

    blob_read_calls: list[str] = []

    def counting_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "blob":
            blob_read_calls.append(str(args))
        # Delegate to the captured original, never to this patched name.
        return original(repo, *args)

    # Monkeypatch is NOT available here (no monkeypatch fixture), so patch manually.
    original = changelog._git_runner_bytes
    changelog._git_runner_bytes = counting_bytes
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    finally:
        changelog._git_runner_bytes = original

    assert blob_read_calls == [], (
        f"expected 0 blob reads for unchanged bundle, got {len(blob_read_calls)}: "
        f"{blob_read_calls}"
    )


# ---------------------------------------------------------------------------
# AC-B4a: a retracted id may never reappear, and a failed retract lists nothing
# ---------------------------------------------------------------------------


def _write_released_fragment(frag_dir: Path, fragment_id: str, day: str) -> Path:
    """Write one valid released core 3.0.0 fragment and return its path."""
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], day, fragment_id
    )
    path = frag_dir / f"{fragment_id}.md"
    path.write_text(
        _fragment_text(
            fragment_id=fragment_id,
            anchor=anchor,
            date=day,
            packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
        ),
        encoding="utf-8",
    )
    return path


def _retraction_list_text(record_id: str) -> str:
    """Return a one-entry retraction list naming record_id."""
    return f'[[retraction]]\nid = "{record_id}"\ncategory = "credential"\n'


def test_listed_retracted_id_present_as_fragment_is_refused(tmp_path: Path) -> None:
    """AC-B4a: a retracted id re-added as a loose fragment is refused, not hidden."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    record_id = "e1000001-0001-4001-8001-100000000001"
    _write_released_fragment(frag_dir, record_id, "2026-11-01")
    retraction_path = tmp_path / "changelog-retractions.toml"
    retraction_path.write_text(_retraction_list_text(record_id), encoding="utf-8")
    try:
        changelog.collect_changelog_records(
            fragment_dir=frag_dir, bundle_dir=bundle_dir, retraction_path=retraction_path
        )
    except changelog.FragmentValidationError as exc:
        assert record_id in str(exc) and "retracted id" in str(exc), exc
    else:
        raise AssertionError("a retracted id present as a fragment was accepted")


def test_listed_retracted_id_present_in_part_is_refused(tmp_path: Path) -> None:
    """AC-B4a: a retracted id still inside a bundle part is refused, not hidden."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    record_id = "e2000002-0002-4002-8002-200000000002"
    _write_released_fragment(frag_dir, record_id, "2026-11-02")
    changelog.compact_month(
        "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    retraction_path = tmp_path / "changelog-retractions.toml"
    retraction_path.write_text(_retraction_list_text(record_id), encoding="utf-8")
    try:
        changelog.collect_changelog_records(
            fragment_dir=frag_dir, bundle_dir=bundle_dir, retraction_path=retraction_path
        )
    except changelog.FragmentValidationError as exc:
        assert record_id in str(exc) and "retracted id" in str(exc), exc
    else:
        raise AssertionError("a retracted id still present in a part was accepted")


def test_retract_rename_failure_raises_and_lists_nothing(
    tmp_path: Path, monkeypatch
) -> None:
    """AC-B4a: a failed part removal stops retract before the list is written."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    record_id = "e3000003-0003-4003-8003-300000000003"
    _write_released_fragment(frag_dir, record_id, "2026-11-03")
    changelog.compact_month(
        "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    retraction_path = tmp_path / "changelog-retractions.toml"
    parts_before = {p.name: p.read_bytes() for p in bundle_dir.iterdir()}

    def failing_rename(self, target):
        raise OSError("injected rename failure")

    monkeypatch.setattr(Path, "rename", failing_rename)
    try:
        changelog.retract_record(
            record_id, "credential", bundle_dir=bundle_dir, retraction_path=retraction_path
        )
    except OSError:
        pass
    else:
        raise AssertionError("retract reported success although the part was not removed")
    monkeypatch.undo()
    assert not retraction_path.exists() or record_id not in retraction_path.read_text(
        encoding="utf-8"
    ), "the record was listed as retracted while it stays published"
    assert {p.name: p.read_bytes() for p in bundle_dir.iterdir()} == parts_before


def test_validate_cli_with_absent_record_directories(tmp_path: Path) -> None:
    """AC-B11: the gate's command passes with no record directories, yet still compares.

    A repository before cutover has neither `changelog.d/` nor
    `changelog.months/`. The required gate must pass there, and an absent
    directory must not skip the merge-base comparison: deleting a months
    directory the merge base holds is refused.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    env = {**__import__("os").environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True
        ).stdout.strip()

    def validate() -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(_SCRIPT), "validate"],
            cwd=repo, env=env, capture_output=True, text=True,
        )

    git("init", "-q", "-b", "main")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "base")
    git("update-ref", "refs/remotes/origin/main", git("rev-parse", "HEAD"))
    result = validate()
    assert result.returncode == 0, f"validate refused an empty repository: {result.stderr}"

    frag_dir = repo / "docs/product/changelog.d"
    frag_dir.mkdir(parents=True)
    bundle_dir = repo / "docs/product/changelog.months"
    _write_released_fragment(frag_dir, "f1000001-0001-4001-8001-100000000001", "2026-11-01")
    changelog.compact_month(
        "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    git("add", "-A")
    git("commit", "-qm", "compacted")
    git("update-ref", "refs/remotes/origin/main", git("rev-parse", "HEAD"))
    assert validate().returncode == 0
    git("rm", "-rq", "docs/product/changelog.months")
    git("commit", "-qm", "drop months")
    result = validate()
    assert result.returncode == 1, "deleting a merge-base months directory was accepted"
    assert "f1000001-0001-4001-8001-100000000001" in result.stderr, result.stderr


def test_compact_cli_moves_released_fragment(tmp_path: Path) -> None:
    """Fix 4 / AC-B6: compact CLI auto-discovers the released-version inventory.

    The compact subcommand must derive the released-version inventory from
    the repository's pack manifests and the historical changelog — the same
    sources the site build uses — so it moves exactly the fragments the build
    would classify as released.  A CLI test in a minimal temp layout confirms
    that `compact --month YYYY-MM` moves a released fragment without any
    additional argument.
    """
    repo = tmp_path / "repo"
    repo.mkdir()

    # Pack manifest: core 3.0.0 is the current released version.
    pack_dir = repo / "packs" / "core"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text(
        "[pack]\n"
        'name = "core"\n'
        'version = "3.0.0"\n',
        encoding="utf-8",
    )
    (repo / "site.toml").write_text(
        "[[groups]]\n"
        'label = "Foundation"\n'
        'packs = ["core"]\n',
        encoding="utf-8",
    )

    # Historical changelog: core 3.0.0 is released.
    product_dir = repo / "docs" / "product"
    product_dir.mkdir(parents=True)
    (product_dir / "changelog.md").write_text(
        "# Changelog\n\n"
        "## [core][3.0.0] — 2026-09-28\n\n"
        "### Highlights\n\n"
        "- Historical release.\n",
        encoding="utf-8",
    )

    # One fragment for core 3.0.0 in the target month.
    frag_id = "cc111111-1111-4111-8111-111111111111"
    frag_dir = product_dir / "changelog.d"
    frag_dir.mkdir()
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-09-15", frag_id
    )
    (frag_dir / f"{frag_id}.md").write_text(
        _fragment_text(
            fragment_id=frag_id,
            anchor=anchor,
            date="2026-09-15",
            packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "compact", "--month", "2026-09"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"compact CLI failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    # The loose fragment must be gone and a bundle part must exist.
    assert not (frag_dir / f"{frag_id}.md").exists(), (
        "compact CLI did not delete the loose fragment"
    )
    bundle_parts = list((product_dir / "changelog.months").glob("*.bundle"))
    assert len(bundle_parts) == 1, (
        f"expected one bundle part, got: {bundle_parts}"
    )


def test_compact_cli_rerun_completes_interrupted_state(tmp_path: Path) -> None:
    """Fix A / AC-B6: compact CLI rerun completes a partially-compacted state.

    The CLI must not call collect_changelog_records itself before compact_month,
    because in the interrupted state (bundle part written, loose fragment still
    present) that raises DuplicateRecordIdError and the CLI exits 1 before
    compact_month's internal rerun-recovery path can run.

    The test constructs the interrupted state directly — both fragments are
    compacted (first CLI run succeeds), then one loose fragment is restored
    byte-exactly — and confirms that a second CLI run exits 0 and deletes the
    remaining fragment without creating a second bundle part.

    Mutation proof: restoring a pre-call to collect_changelog_records in the CLI
    compact branch causes DuplicateRecordIdError to propagate and the CLI to
    exit 1, failing the returncode == 0 assertion.
    """
    repo = tmp_path / "repo"
    repo.mkdir()

    pack_dir = repo / "packs" / "core"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text(
        "[pack]\nname = \"core\"\nversion = \"3.0.0\"\n",
        encoding="utf-8",
    )
    (repo / "site.toml").write_text(
        "[[groups]]\nlabel = \"Foundation\"\npacks = [\"core\"]\n",
        encoding="utf-8",
    )
    product_dir = repo / "docs" / "product"
    product_dir.mkdir(parents=True)
    (product_dir / "changelog.md").write_text(
        "# Changelog\n\n## [core][3.0.0] — 2026-09-28\n\n### Highlights\n\n- Historical release.\n",
        encoding="utf-8",
    )

    frag_dir = product_dir / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = product_dir / "changelog.months"
    bundle_dir.mkdir()

    id1 = "f1000001-0001-4001-8001-100000000001"
    id2 = "f2000002-0002-4002-8002-200000000002"

    def _make_text(fid: str) -> str:
        anchor = changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-10-01", fid
        )
        return _fragment_text(
            fragment_id=fid,
            anchor=anchor,
            date="2026-10-01",
            packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
        )

    id2_text = _make_text(id2)
    for fid in (id1, id2):
        (frag_dir / f"{fid}.md").write_text(_make_text(fid), encoding="utf-8")

    # First compact run: bundles both fragments and deletes them.
    result1 = subprocess.run(
        [sys.executable, str(_SCRIPT), "compact", "--month", "2026-10"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert result1.returncode == 0, (
        f"first compact CLI run failed:\nstdout: {result1.stdout}\nstderr: {result1.stderr}"
    )
    assert not (frag_dir / f"{id2}.md").exists(), "first run did not delete id2"

    # Construct the interrupted state: restore id2 as a loose fragment (byte-exact copy).
    (frag_dir / f"{id2}.md").write_text(id2_text, encoding="utf-8")

    # Verify the interrupted state raises DuplicateRecordIdError on strict collection.
    try:
        changelog.collect_changelog_records(fragment_dir=frag_dir, bundle_dir=bundle_dir)
    except changelog.DuplicateRecordIdError:
        pass
    else:
        raise AssertionError("interrupted state was not detected as a duplicate")

    parts_before = sorted(p.name for p in bundle_dir.glob("*.bundle"))

    # Rerun: the CLI must complete the deletion and exit 0.
    result2 = subprocess.run(
        [sys.executable, str(_SCRIPT), "compact", "--month", "2026-10"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0, (
        f"compact CLI rerun failed:\nstdout: {result2.stdout}\nstderr: {result2.stderr}"
    )
    assert not (frag_dir / f"{id2}.md").exists(), "rerun did not delete the loose fragment"
    parts_after = sorted(p.name for p in bundle_dir.glob("*.bundle"))
    assert parts_after == parts_before, (
        f"rerun created a second bundle part: {parts_after}"
    )


def test_render_cli_includes_bundled_records(tmp_path: Path) -> None:
    """D10 / AC-B8: `render` reads bundled records through the one reader.

    The same records render byte-identically whether loose or compacted into a
    part, including when compaction leaves no `changelog.d/` behind.
    """
    repo = tmp_path / "repo"
    product = repo / "docs/product"
    frag_dir = product / "changelog.d"
    frag_dir.mkdir(parents=True)
    (product / "changelog.md").write_text(
        _HISTORICAL_CHANGELOG.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (repo / ".gitignore").write_text("build/\n", encoding="utf-8")
    ids = ["a7000001-0001-4001-8001-100000000001", "a7000002-0002-4002-8002-200000000002"]
    for fid in ids:
        _write_released_fragment(frag_dir, fid, "2026-11-04")
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test Author")
    _git(repo, "config", "user.email", "test.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "loose")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")

    loose_out = repo / "build/loose.md"
    result = _run_render(repo, loose_out)
    assert result.returncode == 0, result.stderr
    loose_text = loose_out.read_text(encoding="utf-8")
    assert all(fid.replace("-", "") in loose_text for fid in ids)

    changelog.compact_month(
        "2026-11", fragment_dir=frag_dir, bundle_dir=product / "changelog.months",
        released_versions={"core": {"3.0.0"}},
    )
    if frag_dir.exists() and not any(frag_dir.iterdir()):
        frag_dir.rmdir()
    assert not frag_dir.exists(), "compaction should leave no loose fragment"
    bundled_out = repo / "build/bundled.md"
    result = _run_render(repo, bundled_out)
    assert result.returncode == 0, result.stderr
    assert bundled_out.read_text(encoding="utf-8") == loose_text, (
        "render output changed when the records moved into a bundle part"
    )


# ---------------------------------------------------------------------------
# T14: Dependency and privacy posture
#
# Two checks per § 7 Dependency and privacy posture:
#   1. Static: no third-party import added to any touched tools/ entry point.
#   2. Offline: the Python projection runs with socket.connect blocked.
# ---------------------------------------------------------------------------


def test_no_third_party_import_added_by_delivery() -> None:
    """T14 static check: no third-party import added to any touched tools/ entry point.

    For files this delivery creates (untracked in Git) every import must be
    standard library.  For files that already existed only imports absent from
    the merge-base version count as violations.  Pre-existing third-party
    imports in existing files are out of scope.
    """
    import ast

    ROOT = _SCRIPT.parent.parent
    STDLIB = sys.stdlib_module_names

    # Closed set from T14's Touches fields (all touched tools/ files, test
    # suites included — tools/AGENTS.md's pure-stdlib rule binds new additions
    # without distinguishing a suite from an entry point).
    CLOSED_SET = [
        ROOT / "tools/changelog.py",
        ROOT / "tools/build-site.py",
        ROOT / "tools/check-core-release.py",
        ROOT / "tools/repo/check_release_impact.py",
        ROOT / "tools/measure-changelog-fragment-merges.py",
        ROOT / "tools/measure-changelog-anchor-drift.py",
        ROOT / "tools/test-pages-workflow.py",
        ROOT / "tools/test_build_site_routing.py",
        ROOT / "tools/test_check_core_release.py",
        ROOT / "tools/test_check_release_impact.py",
        ROOT / "tools/lint-ci-parity.py",
        ROOT / "tools/test_changelog.py",
    ]

    def _top_level(name: str) -> str:
        return name.split(".")[0]

    def _collect_imports(source: str) -> set[str]:
        """Return every top-level module name imported anywhere in source."""
        tree = ast.parse(source)
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(_top_level(alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names.add(_top_level(node.module))
        return names

    def _is_local(name: str) -> bool:
        """True when name maps to a .py file inside the repository."""
        for candidate in [
            ROOT / "tools" / f"{name}.py",
            ROOT / "tools" / "repo" / f"{name}.py",
            ROOT / f"{name}.py",
        ]:
            if candidate.is_file():
                return True
        return False

    def _third_party(imports: set[str]) -> set[str]:
        return {n for n in imports if n not in STDLIB and not _is_local(n)}

    base_result = subprocess.run(
        ["git", "merge-base", "origin/main", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert base_result.returncode == 0, f"git merge-base: {base_result.stderr}"
    merge_base = base_result.stdout.strip()

    # Identify untracked paths — those are files this delivery created.
    status_result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    untracked: set[str] = set()
    for line in status_result.stdout.splitlines():
        if line.startswith("??"):
            rel = line[3:].strip().rstrip("/")
            untracked.add(str((ROOT / rel).resolve()))

    violations: list[str] = []

    for path in CLOSED_SET:
        if not path.exists():
            violations.append(f"MISSING: {path}")
            continue
        current_imports = _collect_imports(path.read_text(encoding="utf-8"))
        current_third = _third_party(current_imports)

        if str(path.resolve()) in untracked:
            # File created by this delivery — every import must be stdlib.
            if current_third:
                violations.append(
                    f"CREATED {path.relative_to(ROOT)}: "
                    f"third-party imports: {sorted(current_third)}"
                )
        else:
            # Existing file — only newly added third-party imports are violations.
            rel = str(path.relative_to(ROOT))
            show = subprocess.run(
                ["git", "show", f"{merge_base}:{rel}"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if show.returncode != 0:
                # Absent at merge base — treat as created.
                if current_third:
                    violations.append(
                        f"ADDED {rel}: third-party imports: {sorted(current_third)}"
                    )
                continue
            base_third = _third_party(_collect_imports(show.stdout))
            added = current_third - base_third
            if added:
                violations.append(
                    f"MODIFIED {rel}: new third-party imports: {sorted(added)}"
                )

    assert not violations, "Third-party import violations:\n" + "\n".join(violations)


def test_offline_build_runs_without_network_access(tmp_path: Path) -> None:
    """T14 offline check: end-to-end Python projection completes with socket blocked.

    A wrapper script patches socket.connect to raise before loading the
    changelog module, then exercises the render view (T5) and the /now/
    projection (T7 Python path).  A sentinel file records any connection
    attempt; the test asserts none was made.
    """
    import textwrap

    sentinel = tmp_path / "connection_attempted.txt"
    wrapper = tmp_path / "offline_runner.py"
    baseline = tmp_path / "docs" / "product" / "changelog.md"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("# Changelog\n", encoding="utf-8")
    output = tmp_path / "build" / "product-changelog.md"
    # Point --fragments at a path that does not exist so that
    # collect_changelog_records returns ([], []) without any git or I/O calls.
    fragments = tmp_path / "nonexistent_changelog.d"

    wrapper.write_text(
        textwrap.dedent(
            f"""\
            import socket as _sock
            _sentinel = {str(sentinel)!r}
            def _blocked(self, address):
                with open(_sentinel, "a", encoding="utf-8") as _f:
                    _f.write(f"connect {{address!r}}\\n")
                raise OSError(f"T14 offline guard: connection to {{address!r}} blocked")
            _sock.socket.connect = _blocked

            import importlib.util as _ilu
            import sys
            _spec = _ilu.spec_from_file_location("product_changelog", {str(_SCRIPT)!r})
            assert _spec is not None and _spec.loader is not None
            _mod = _ilu.module_from_spec(_spec)
            sys.modules[_spec.name] = _mod
            _spec.loader.exec_module(_mod)

            # T5: render the complete changelog view.
            rc = _mod.main([
                "render",
                "--output", {str(output)!r},
                "--baseline", {str(baseline)!r},
                "--fragments", {str(fragments)!r},
            ])
            assert rc == 0, f"render returned {{rc}}"

            # T7 Python path: project the /now/ payload from zero fragments.
            result = _mod.project_fragment_now_highlights([], {{}})
            assert isinstance(result, dict)

            print("offline-ok")
            """
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(wrapper)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Offline build failed:\n{result.stderr}"
    assert "offline-ok" in result.stdout, (
        f"Wrapper did not complete successfully:\n{result.stdout}"
    )
    assert not sentinel.exists(), (
        "Network connection attempted during offline build:\n"
        + sentinel.read_text(encoding="utf-8")
    )


# ---------------------------------------------------------------------------
# Fix 1 — validate CLI enforces historical-baseline refusal (T14 repair)
# ---------------------------------------------------------------------------


def test_validate_cli_refuses_edited_historical_release_section(tmp_path: Path) -> None:
    """Fix 1 / spec AC: the required validate gate refuses an edited release section.

    A change that edits a historical release section in docs/product/changelog.md
    must be refused by a gate naming the edited heading, and the required gate
    is `python3 tools/changelog.py validate` (AC-B11).
    """
    import os as _os

    repo = tmp_path / "repo"
    repo.mkdir()
    env = {
        **_os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid",
    }

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo, env=env, check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def validate() -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(_SCRIPT), "validate"],
            cwd=repo, env=env, capture_output=True, text=True,
        )

    # Baseline changelog with one historical release section.
    # Use the TOML-style heading format [name][version] that _parse_release_identity
    # recognises, so _historical_release_sections returns a non-empty list.
    changelog_dir = repo / "docs" / "product"
    changelog_dir.mkdir(parents=True)
    changelog_path = changelog_dir / "changelog.md"
    heading = "## [core][3.0.0] — 2026-01-15"
    changelog_path.write_text(
        f"# Changelog\n\n{heading}\n\n### Highlights\n- Initial release.\n",
        encoding="utf-8",
    )
    git("init", "-q", "-b", "main")
    git("add", "docs/product/changelog.md")
    git("commit", "-qm", "base")
    git("update-ref", "refs/remotes/origin/main", git("rev-parse", "HEAD"))

    # Edit the historical release section body (working tree only, not committed).
    changelog_path.write_text(
        f"# Changelog\n\n{heading}\n\n### Highlights\n- EDITED initial release.\n",
        encoding="utf-8",
    )

    result = validate()
    assert result.returncode == 1, (
        f"validate accepted an edited historical release section (exit 0):\n{result.stderr}"
    )
    # The error names the heading text (without the "## " prefix — the field in
    # _fragment_error is the extracted title, not the full Markdown heading line).
    heading_text = heading.lstrip("# ").strip()
    assert heading_text in result.stderr, (
        f"validate did not name the edited heading in its error:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# Fix 2 — _base_blob_text fail-closed (T14 repair)
# ---------------------------------------------------------------------------


def test_base_blob_text_raises_on_exit_128(tmp_path: Path) -> None:
    """Fix 2: _base_blob_text raises FragmentValidationError on unexpected git failure.

    A non-zero exit that is NOT exit 1 with "no merge base" must refuse
    fail-closed rather than silently disabling the historical-baseline check.
    """
    _GitResult = changelog._GitResult
    baseline = tmp_path / "docs" / "product" / "changelog.md"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("# Changelog\n", encoding="utf-8")

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            # Simulate a repository or network error.
            return _GitResult(128, "", "fatal: not a git repository")
        return _GitResult(128, "", f"unexpected: {args}")

    try:
        changelog._base_blob_text(baseline, git_runner=fake_git)
    except changelog.FragmentValidationError as exc:
        assert "128" in str(exc) or "merge-base" in str(exc), (
            f"error does not name exit code or context: {exc}"
        )
    else:
        raise AssertionError(
            "_base_blob_text returned None for a git exit-128 failure "
            "instead of raising FragmentValidationError"
        )


def test_base_blob_text_returns_none_for_no_merge_base(tmp_path: Path) -> None:
    """Fix 2: exit 1 with 'no merge base' in stderr returns None (orphan branch).

    validate_historical_changelog_baseline must silently return when there is
    no common ancestor, consistent with validate_changelog_cross_form_identity.
    """
    _GitResult = changelog._GitResult
    baseline = tmp_path / "docs" / "product" / "changelog.md"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("# Changelog\n\n## [core 3.0.0] — 2026-01-15\n\n- Original.\n",
                        encoding="utf-8")

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(1, "", "fatal: no merge base")
        return _GitResult(128, "", f"unexpected: {args}")

    # Should return None → validate_historical_changelog_baseline returns silently.
    try:
        changelog.validate_historical_changelog_baseline(baseline, git_runner=fake_git)
    except changelog.FragmentValidationError as exc:
        raise AssertionError(
            f"validate_historical_changelog_baseline raised for an orphan branch: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Fix 3 — typed rerun dispatch in compact_month (T14 repair)
# ---------------------------------------------------------------------------


def test_compact_two_bundle_parts_with_same_id_raises(tmp_path: Path) -> None:
    """Fix 3b: the same id in two bundle parts raises from the rerun-recovery path.

    When compact_month catches DuplicateRecordIdError from the initial
    collect_changelog_records (cross-form duplicate), the recovery path calls
    _collect_bundle_records with seen_ids=set().  A duplicate id across two
    bundle parts then raises DuplicateRecordIdError again, which is not caught
    by the recovery handler and propagates out of compact_month.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    dup_id = "ffffffff-ffff-4fff-8fff-ffffffffffff"
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-11-01", dup_id
    )
    rec = _bundle_fragment_text(fragment_id=dup_id, anchor=anchor, date="2026-11-01")

    # Also write the same id as a loose fragment to trigger the initial
    # cross-form DuplicateRecordIdError so the recovery path is entered.
    (frag_dir / f"{dup_id}.md").write_text(
        _fragment_text(
            fragment_id=dup_id,
            anchor=anchor,
            date="2026-11-01",
            packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
        ),
        encoding="utf-8",
    )

    # Put the same id into two separate bundle parts.
    (bundle_dir / "2026-11-00.bundle").write_bytes(
        changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    )
    (bundle_dir / "2026-11-01.bundle").write_bytes(
        changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    )

    try:
        changelog.compact_month(
            "2026-11",
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            released_versions={"core": {"3.0.0"}},
        )
    except changelog.FragmentValidationError as exc:
        assert "duplicate id" in str(exc).lower(), (
            f"expected 'duplicate id' in the error, got: {exc}"
        )
    else:
        raise AssertionError(
            "compact_month accepted two bundle parts with the same id"
        )


def test_compact_non_duplicate_fragment_validation_error_is_reraised(
    tmp_path: Path, monkeypatch
) -> None:
    """Fix 3c: a FragmentValidationError that is not DuplicateRecordIdError is re-raised.

    A generic FragmentValidationError whose message happens to contain 'duplicate id'
    (but whose type is not DuplicateRecordIdError) must not be swallowed by the
    rerun-recovery handler.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    sentinel_error = changelog.FragmentValidationError(
        "duplicate id in some other context"
    )

    def fake_collect(*args, **kwargs):
        raise sentinel_error

    monkeypatch.setattr(changelog, "collect_changelog_records", fake_collect)

    try:
        changelog.compact_month(
            "2026-11",
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            released_versions={"core": {"3.0.0"}},
        )
    except changelog.FragmentValidationError as exc:
        assert exc is sentinel_error, (
            f"a different error was raised instead of the injected one: {exc}"
        )
    else:
        raise AssertionError(
            "compact_month swallowed a non-DuplicateRecordIdError FragmentValidationError"
        )


# ---------------------------------------------------------------------------
# Fix 6 — AC-B4 ride-along acceptance fixture (T14 repair / adversarial F1)
# ---------------------------------------------------------------------------


def test_validate_cross_form_accepts_part_adding_with_new_fragment(
    tmp_path: Path,
) -> None:
    """Fix 6 / AC-B4: a part-adding change that also adds a new fragment passes.

    Merge base: one loose fragment (A).
    Current state: fragment A compacted into a new bundle part (loose file deleted);
    a fresh loose fragment (B) absent at the merge base and not bundled also present.
    validate_changelog_cross_form_identity must raise nothing.

    Mutation check: if Refusal 3 also fired for non-base fragment ids, this
    fixture would fail because B is not in base_frag_ids.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Fragment A: was loose at merge base, now bundled (loose file deleted).
    frag_a_id = "aabbccdd-aabb-4aab-8aab-aabbccddaabb"
    frag_a_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", frag_a_id
    )
    rec_a = _bundle_fragment_text(
        fragment_id=frag_a_id, anchor=frag_a_anchor, date="2026-10-01"
    )

    # Fragment B: absent at merge base, not bundled — a genuine new contribution.
    frag_b_id = "11223344-1122-4112-8112-112233441122"
    frag_b_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-02", frag_b_id
    )
    frag_b_path = frag_dir / f"{frag_b_id}.md"
    frag_b_path.write_text(
        _fragment_text(
            fragment_id=frag_b_id,
            anchor=frag_b_anchor,
            date="2026-10-02",
            packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
        ),
        encoding="utf-8",
    )

    # Current bundle part: contains only fragment A (byte-exact copy).
    part_content = changelog.BUNDLE_SEPARATOR_BYTES + rec_a.encode("utf-8")
    (bundle_dir / "2026-10-00.bundle").write_bytes(part_content)

    # Merge-base ls-tree: only fragment A was present (loose); fragment B is new.
    frag_a_obj = "a" * 40
    merge_base = "12345678" * 5
    ls_lines = [f"100644 blob {frag_a_obj}\tchangelog.d/{frag_a_id}.md"]

    _GitResult = changelog._GitResult

    def fake_git(cwd, *args):
        """Extended fake git runner that also handles diff/ls-files for fragment validation."""
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, merge_base + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            ls_output = "\n".join(ls_lines)
            return _GitResult(0, ls_output + "\n" if ls_output else "", "")
        if args[0] == "diff" and "--name-status" in args:
            # Fragment B is newly added; fragment A is gone (deleted then bundled).
            diff_out = f"A\tchangelog.d/{frag_b_id}.md\n"
            return _GitResult(0, diff_out, "")
        if args[0] == "ls-files":
            # Only fragment B is tracked in the current working tree.
            return _GitResult(0, f"changelog.d/{frag_b_id}.md\n", "")
        return _GitResult(128, "", f"unexpected git call: {' '.join(str(a) for a in args)}")

    # Because the bundle part's object id differs from the base ls-tree,
    # the validator reads the merge-base blob for A to compare bytes.
    original_bytes_runner = changelog._git_runner_bytes

    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            # Return the size of the loose fragment A bytes.
            return (0, str(len(rec_a.encode("utf-8"))).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            # Return the base loose fragment A bytes (plain, not bundled).
            return (0, rec_a.encode("utf-8"), "")
        return original_bytes_runner(repo, *args)

    changelog._git_runner_bytes = fake_bytes
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        raise AssertionError(
            f"ride-along acceptance fixture raised unexpectedly: {exc}"
        ) from exc
    finally:
        changelog._git_runner_bytes = original_bytes_runner


# ============================================================================
# T14 repair round: eight acceptance fixtures (QE adjudication round 6)
# Fixtures F1–F8 add the missing coverage identified in the adjudication.
# ============================================================================


def test_bundle_part_refuses_separator_line_in_record_body(tmp_path: Path) -> None:
    """F1 (AC-B2): a separator line in a bundled record body causes refusal.

    The part is split on the separator line, so an embedded separator yields
    an extra element instead of reaching any in-body check. Here it ends the
    body, so the guard that fires is the "empty record" check on the trailing
    zero-byte element the split produces.
    """
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Body ends with the separator line; after split, the second element is empty.
    body = "## Highlights\n- OK.\n" + changelog.BUNDLE_SEPARATOR_LINE + "\n"
    rec = _bundle_fragment_text(body=body)
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert str(part) in msg, f"part path not in error: {msg}"
        # "record 1" names the spurious second element from the split.
        assert "record" in msg.lower(), f"record position not in error: {msg}"
    else:
        raise AssertionError(
            "bundle part with separator line in record body was accepted; "
            "expected FragmentValidationError"
        )


def test_collect_bundle_records_refuses_duplicate_nn(tmp_path: Path) -> None:
    """F2 (AC-B3): duplicate month+NN is refused through _collect_bundle_records.

    A duplicate NN cannot occur through the real ``list_confined_regular_files``
    helper because two files with the same name cannot coexist in one directory.
    This fixture stubs the helper to return two paths sharing the same name,
    which produces the same month+NN pair and triggers the guard at
    ``changelog.py`` lines 1893-1898.
    """
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    class _StubSafety:
        class UnsafeContentError(Exception):
            pass

        def list_confined_directories(self, root, directory):  # noqa: ANN001
            return []

        def list_confined_regular_files(self, root, directory, **kwargs):  # noqa: ANN001
            # Two paths with the same name → same month+NN.
            return [directory / "2026-10-00.bundle", directory / "2026-10-00.bundle"]

        def read_confined_regular_file(self, root, path, *, max_bytes=None):  # noqa: ANN001
            raise AssertionError("read should not be reached before the NN check")

    try:
        changelog._collect_bundle_records(bundle_dir, _StubSafety())
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert "2026-10-00.bundle" in msg, f"part path not in error: {msg}"
        assert (
            "duplicate" in msg.lower() or "nn" in msg.lower()
        ), f"duplicate NN not named in error: {msg}"
    else:
        raise AssertionError(
            "duplicate month+NN was accepted; expected FragmentValidationError"
        )


def test_collect_bundle_records_refuses_stray_non_bundle_file(tmp_path: Path) -> None:
    """F3 (AC-B3): a non-.bundle regular file in the bundle directory is refused.

    ``list_confined_regular_files`` returns regular files regardless of
    extension; ``_validate_bundle_part_name`` then refuses names that do not
    fullmatch ``YYYY-MM-NN.bundle``, naming the stray path.
    """
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    stray = bundle_dir / "README.txt"
    stray.write_text("stray content\n", encoding="utf-8")
    fs = changelog._file_safety()
    try:
        changelog._collect_bundle_records(bundle_dir, fs)
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert str(stray) in msg or "README.txt" in msg, (
            f"stray file path not in error: {msg}"
        )
        # The name-validation error names "name" in the field; a downstream
        # content-parsing error says "record 0".  This distinguishes the two.
        assert "name" in msg or "YYYY-MM-NN" in msg, (
            f"name-validation field not in error (got downstream guard instead): {msg}"
        )
    else:
        raise AssertionError(
            "stray non-.bundle file in bundle directory was accepted; "
            "expected FragmentValidationError"
        )


# ── F4 (AC-B3a): hard link and FIFO fixtures for bundle dir and retraction list ──


def test_bundle_dir_confinement_refuses_hard_link(tmp_path: Path) -> None:
    """F4 (AC-B3a): a hard link in the bundle directory is refused by path.

    A hard-linked file has ``st_nlink > 1``.  ``list_confined_regular_files``
    does not check link counts and returns the path; ``_read_bundle_part`` then
    calls ``read_confined_regular_file``, which detects the hard link and raises
    ``UnsafeContentError``.
    """
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    src = tmp_path / "source.bundle"
    src.write_bytes(changelog.BUNDLE_SEPARATOR_BYTES + _bundle_fragment_text().encode())
    target = bundle_dir / "2026-10-00.bundle"
    _OS.link(src, target)  # target.stat().st_nlink == 2
    fs = changelog._file_safety()
    try:
        changelog._collect_bundle_records(bundle_dir, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError) as exc:
        msg = str(exc)
        assert "2026-10-00.bundle" in msg or "hard link" in msg.lower(), (
            f"offending path not named in error: {msg}"
        )
    else:
        raise AssertionError(
            "hard link in bundle directory was accepted; expected refusal"
        )


def test_bundle_dir_confinement_refuses_fifo(tmp_path: Path) -> None:
    """F4 (AC-B3a): a FIFO in the bundle directory is refused by path.

    ``walk_confined_regular_files`` rejects non-regular, non-directory,
    non-link entries (the ``else`` branch at ``file_safety.py`` line 206)
    and raises ``UnsafeContentError`` naming the FIFO's relative path.
    """
    if not hasattr(_OS, "mkfifo"):
        return  # platform does not support FIFOs
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    fifo = bundle_dir / "2026-10-00.bundle"
    _OS.mkfifo(fifo)
    fs = changelog._file_safety()
    try:
        changelog._collect_bundle_records(bundle_dir, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError) as exc:
        msg = str(exc)
        assert "2026-10-00.bundle" in msg or "regular" in msg.lower(), (
            f"offending path not named in error: {msg}"
        )
    else:
        fifo.unlink()
        raise AssertionError(
            "FIFO in bundle directory was accepted; expected refusal"
        )
    if fifo.exists():
        fifo.unlink()


def test_retraction_list_confinement_refuses_hard_link(tmp_path: Path) -> None:
    """F4 (AC-B3a): a hard link at the retraction-list path is refused.

    ``read_confined_regular_file`` detects ``st_nlink > 1`` and raises
    ``UnsafeContentError``, which ``_read_retraction_list`` wraps into
    ``FragmentValidationError``.
    """
    src = tmp_path / "source-retractions.toml"
    src.write_text("", encoding="utf-8")
    retraction_path = tmp_path / "changelog-retractions.toml"
    _OS.link(src, retraction_path)  # retraction_path.stat().st_nlink == 2
    fs = changelog._file_safety()
    try:
        changelog._read_retraction_list(retraction_path, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError) as exc:
        msg = str(exc)
        assert "changelog-retractions.toml" in msg or "hard link" in msg.lower(), (
            f"offending path not named in error: {msg}"
        )
    else:
        raise AssertionError(
            "hard link at retraction list path was accepted; expected refusal"
        )


def test_retraction_list_confinement_refuses_fifo(tmp_path: Path) -> None:
    """F4 (AC-B3a): a FIFO at the retraction-list path is refused.

    ``read_confined_regular_file`` checks ``S_ISREG`` before opening; a FIFO
    fails that check and raises ``UnsafeContentError``.
    """
    if not hasattr(_OS, "mkfifo"):
        return  # platform does not support FIFOs
    retraction_path = tmp_path / "changelog-retractions.toml"
    _OS.mkfifo(retraction_path)
    fs = changelog._file_safety()
    try:
        changelog._read_retraction_list(retraction_path, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError) as exc:
        msg = str(exc)
        assert "changelog-retractions.toml" in msg or "regular" in msg.lower(), (
            f"offending path not named in error: {msg}"
        )
    else:
        if retraction_path.exists():
            retraction_path.unlink()
        raise AssertionError(
            "FIFO at retraction list path was accepted; expected refusal"
        )
    if retraction_path.exists():
        retraction_path.unlink()


# ── F5 (AC-B4 ident) ─────────────────────────────────────────────────────────


def test_ident_expanded_bundle_part_is_refused(tmp_path: Path) -> None:
    """F5 (AC-B4 ident): a bundle part expanded by git's ident filter is refused.

    AC-B4 requires "changed" to be decided by an object id over the exact loaded
    filesystem bytes, with no ident filter conversion.  After ``git checkout``
    applies the smudge filter (``$Id$`` → ``$Id: <blob-sha>$``), the working-tree
    bytes differ from the stored blob bytes.  The validator reads filesystem bytes
    directly, computes their sha1, finds it differs from the stored blob sha, reads
    the blob, compares bytes, and refuses.

    Mutation that kills this test: replace ``_compute_git_object_id(part_raw, ...)``
    with ``git hash-object --path=<part>`` (which applies the clean filter, strips
    the expansion, and recomputes the original hash) → no refusal, assertion
    fails.
    """
    import os as _os_f5
    import subprocess as _sp_f5

    _GIT_REDIRECTS = (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    )
    env_f5 = {k: v for k, v in _os_f5.environ.items() if k not in _GIT_REDIRECTS}
    env_f5.update({
        "GIT_AUTHOR_NAME": "changelog-f5-test",
        "GIT_AUTHOR_EMAIL": "test@invalid",
        "GIT_COMMITTER_NAME": "changelog-f5-test",
        "GIT_COMMITTER_EMAIL": "test@invalid",
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
    })

    def _run_f5(*args: str) -> str:
        r = _sp_f5.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, env=env_f5,
        )
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    _run_f5("init")
    _run_f5("config", "user.email", "test@invalid")
    _run_f5("config", "user.name", "changelog-f5-test")

    # Enable git's ident attribute for bundle files.
    (tmp_path / ".gitattributes").write_text("*.bundle ident\n", encoding="utf-8")

    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Bundle part body contains the bare $Id$ token that git will expand on
    # checkout (smudge filter replaces $Id$ with $Id: <blob-sha>$).
    body_with_ident = "## Highlights\n- $Id$\n"
    rec = _bundle_fragment_text(body=body_with_ident)
    part_content_unexpanded = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part_path = bundle_dir / "2026-10-00.bundle"
    part_path.write_bytes(part_content_unexpanded)

    _run_f5("add", ".")
    _run_f5("commit", "-m", "base")
    base_sha = _run_f5("rev-parse", "HEAD")
    _run_f5("update-ref", "refs/remotes/origin/main", base_sha)

    # Check the part out afresh so the smudge filter expands $Id$; a checkout
    # of an up-to-date path would leave the file untouched.
    part_path.unlink()
    _run_f5("checkout", "--", "changelog.months/2026-10-00.bundle")
    assert b"$Id: " in part_path.read_bytes(), "git did not apply the ident filter"

    # Edit the part inside the keyword. Git's filtered view collapses any
    # $Id: ... $ back to $Id$, so it reports no change; raw bytes differ.
    part_path.write_bytes(
        part_content_unexpanded.replace(b"$Id$", b"$Id: 0000000000 $")
    )
    hidden = _sp_f5.run(
        ["git", "-C", str(tmp_path), "diff", "--quiet"], env=env_f5
    )
    assert hidden.returncode == 0, "fixture no longer hides the edit from git diff"
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert "2026-10-00.bundle" in msg or str(bundle_dir) in msg, (
            f"part path not in error: {msg}"
        )
        assert VALID_ID_B in msg or "bytes changed" in msg.lower(), (
            f"record id or diagnostic not in error: {msg}"
        )
    else:
        raise AssertionError(
            "ident-expanded bundle part was accepted as unchanged; the "
            "comparator must use raw filesystem bytes, not git-filtered bytes "
            "(AC-B4)"
        )


# ── F6 (AC-B4 SHA-256) ───────────────────────────────────────────────────────


def test_sha256_unchanged_part_passes_without_blob_read(tmp_path: Path) -> None:
    """F6 (AC-B4 SHA-256): in a sha256 repo, an unchanged bundle part passes via
    the sha256 early-exit optimisation (no blob read required).

    Mutation that kills this test: hard-code sha1 in ``_compute_git_object_id``
    → the computed sha1 does not match the stored sha256 blob id → the validator
    falls through to read the blob → the counting runner below records the call
    → the ``cat_file_blob_calls == 0`` assertion fails.
    """
    import os as _os_f6
    import subprocess as _sp_f6

    _GIT_REDIRECTS = (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    )
    env_f6 = {k: v for k, v in _os_f6.environ.items() if k not in _GIT_REDIRECTS}
    env_f6.update({
        "GIT_AUTHOR_NAME": "changelog-f6-test",
        "GIT_AUTHOR_EMAIL": "test@invalid",
        "GIT_COMMITTER_NAME": "changelog-f6-test",
        "GIT_COMMITTER_EMAIL": "test@invalid",
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
    })

    probe = _sp_f6.run(
        ["git", "-C", str(tmp_path), "init", "--object-format=sha256"],
        capture_output=True, text=True, env=env_f6,
    )
    if probe.returncode != 0:
        return  # sha256 not supported; skip gracefully

    def _run_f6(*args: str) -> str:
        r = _sp_f6.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, env=env_f6,
        )
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    _run_f6("config", "user.email", "test@invalid")
    _run_f6("config", "user.name", "changelog-f6-test")

    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    rec = _bundle_fragment_text()
    part_content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part_path = bundle_dir / "2026-10-00.bundle"
    part_path.write_bytes(part_content)

    _run_f6("add", ".")
    _run_f6("commit", "-m", "base")
    base_sha = _run_f6("rev-parse", "HEAD")
    _run_f6("update-ref", "refs/remotes/origin/main", base_sha)

    # Patch _git_runner_bytes to count cat-file blob calls.  With correct sha256
    # handling, the early-exit optimisation fires and no blob is read.
    original_bytes_runner = changelog._git_runner_bytes
    cat_file_blob_calls: list[int] = [0]

    def _counting_runner(repo, *args):  # type: ignore[no-untyped-def]
        if args and args[0] == "cat-file" and len(args) >= 2 and args[1] == "blob":
            cat_file_blob_calls[0] += 1
        return original_bytes_runner(repo, *args)

    changelog._git_runner_bytes = _counting_runner
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
        )
    except changelog.FragmentValidationError as exc:
        raise AssertionError(
            f"unchanged sha256 bundle part was unexpectedly refused: {exc}"
        ) from exc
    finally:
        changelog._git_runner_bytes = original_bytes_runner

    assert cat_file_blob_calls[0] == 0, (
        f"cat-file blob was called {cat_file_blob_calls[0]} time(s) on an unchanged "
        "part; the sha256 early-exit optimisation did not fire — check that "
        "_compute_git_object_id uses the repo's object format, not hard-coded sha1"
    )


def test_sha256_changed_part_is_refused(tmp_path: Path) -> None:
    """F6 (AC-B4 SHA-256): a one-byte change to a bundle part in a sha256 repo
    is detected and refused via ``validate_changelog_cross_form_identity``."""
    import os as _os_f6b
    import subprocess as _sp_f6b

    _GIT_REDIRECTS = (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    )
    env_f6b = {k: v for k, v in _os_f6b.environ.items() if k not in _GIT_REDIRECTS}
    env_f6b.update({
        "GIT_AUTHOR_NAME": "changelog-f6b-test",
        "GIT_AUTHOR_EMAIL": "test@invalid",
        "GIT_COMMITTER_NAME": "changelog-f6b-test",
        "GIT_COMMITTER_EMAIL": "test@invalid",
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
    })

    probe = _sp_f6b.run(
        ["git", "-C", str(tmp_path), "init", "--object-format=sha256"],
        capture_output=True, text=True, env=env_f6b,
    )
    if probe.returncode != 0:
        return  # sha256 not supported

    def _run_f6b(*args: str) -> str:
        r = _sp_f6b.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, env=env_f6b,
        )
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    _run_f6b("config", "user.email", "test@invalid")
    _run_f6b("config", "user.name", "changelog-f6b-test")

    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    rec = _bundle_fragment_text()
    part_content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part_path = bundle_dir / "2026-10-00.bundle"
    part_path.write_bytes(part_content)

    _run_f6b("add", ".")
    _run_f6b("commit", "-m", "base")
    base_sha = _run_f6b("rev-parse", "HEAD")
    _run_f6b("update-ref", "refs/remotes/origin/main", base_sha)

    # Introduce a one-byte change.
    changed = part_content.replace(b"- Bundle test", b"- Changed!!!")
    assert changed != part_content, "replacement did not change the content"
    part_path.write_bytes(changed)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert "bytes changed" in msg.lower() or VALID_ID_B in msg, (
            f"error does not name the byte change or record id: {msg}"
        )
    else:
        raise AssertionError(
            "one-byte change to a sha256 bundle part was accepted; "
            "expected FragmentValidationError"
        )


# ── F7 (AC-B4 moved bundled record) ──────────────────────────────────────────


def test_validate_cross_form_refuses_bundled_record_moved_with_date_changed(
    tmp_path: Path,
) -> None:
    """F7 (AC-B4): a bundled record moved into a new added part with its date
    changed is refused, naming the record id and both the original and new part paths.

    This test drove a production fix: the first loop in
    ``validate_changelog_cross_form_identity`` only checks byte immutability for
    parts that still exist at the same path.  A record moved from an old part to
    a newly-added part with changed bytes (e.g. a different ``date``) slipped
    through without refusal.  The fix adds Refusal 1b, which compares record bytes
    in new parts against the merge-base blob record bytes collected during the
    second loop's blob-reading path.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Merge-base: old bundle part containing VALID_ID_B with date=2026-10-01.
    old_rec = _bundle_fragment_text()  # VALID_ID_B, date=2026-10-01
    old_part_bytes = changelog.BUNDLE_SEPARATOR_BYTES + old_rec.encode("utf-8")
    # The old part is ABSENT from the current state (not written to bundle_dir).

    # Current state: new bundle part with VALID_ID_B but date=2026-11-01 (changed).
    new_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-11-01", VALID_ID_B
    )
    new_rec = _bundle_fragment_text(anchor=new_anchor, date="2026-11-01")
    new_part_bytes = changelog.BUNDLE_SEPARATOR_BYTES + new_rec.encode("utf-8")
    new_part = bundle_dir / "2026-11-00.bundle"
    new_part.write_bytes(new_part_bytes)

    old_part_sha = _sha1_obj_id(old_part_bytes)
    merge_base = "deadbeef" * 5

    _GitResult = changelog._GitResult

    def _fake_git_f7(cwd, *args):  # type: ignore[no-untyped-def]
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, merge_base + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            # Base has only the old part at 2026-10-00.bundle.
            line = (
                f"100644 blob {old_part_sha}\t"
                "changelog.months/2026-10-00.bundle"
            )
            return _GitResult(0, line + "\n", "")
        return _GitResult(
            128, "", f"unexpected git call: {' '.join(str(a) for a in args)}"
        )

    original_bytes_runner = changelog._git_runner_bytes

    def _fake_bytes_f7(repo, *args):  # type: ignore[no-untyped-def]
        if args[0] == "cat-file" and args[1] == "-s" and args[2] == old_part_sha:
            return (0, str(len(old_part_bytes)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob" and args[2] == old_part_sha:
            return (0, old_part_bytes, "")
        return original_bytes_runner(repo, *args)

    changelog._git_runner_bytes = _fake_bytes_f7
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=_fake_git_f7,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert VALID_ID_B in msg, (
            f"record id {VALID_ID_B!r} not in error: {msg}"
        )
        assert "2026-11-00.bundle" in msg, (
            f"new part path not in error: {msg}"
        )
        assert "2026-10-00.bundle" in msg, (
            f"original part path not in error: {msg}"
        )
    else:
        raise AssertionError(
            "bundled record moved to a new part with its date changed was accepted; "
            "expected FragmentValidationError naming the record id and both part paths"
        )
    finally:
        changelog._git_runner_bytes = original_bytes_runner


def _validate_against_fake_base(
    tmp_path: Path, base_entries: dict[str, bytes]
) -> None:
    """Run cross-form validation against a fake merge base holding base_entries.

    ``base_entries`` maps repo-relative paths to their merge-base blob bytes;
    the current state is whatever the test wrote under ``tmp_path``.
    """
    _GitResult = changelog._GitResult
    blobs = {_sha1_obj_id(data): data for data in base_entries.values()}
    tree = "".join(
        f"100644 blob {_sha1_obj_id(data)}\t{path}\n"
        for path, data in sorted(base_entries.items())
    )

    def fake_git(cwd, *args):  # type: ignore[no-untyped-def]
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, "deadbeef" * 5 + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            return _GitResult(0, tree, "")
        return _GitResult(128, "", f"unexpected git call: {' '.join(map(str, args))}")

    original_bytes_runner = changelog._git_runner_bytes

    def fake_bytes(repo, *args):  # type: ignore[no-untyped-def]
        if args[0] == "cat-file" and args[2] in blobs:
            data = blobs[args[2]]
            if args[1] == "-s":
                return (0, str(len(data)).encode() + b"\n", "")
            if args[1] == "blob":
                return (0, data, "")
        return original_bytes_runner(repo, *args)

    changelog._git_runner_bytes = fake_bytes
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=tmp_path / "changelog.d",
            bundle_dir=tmp_path / "changelog.months",
            retraction_path=tmp_path / "changelog-retractions.toml",
            git_runner=fake_git,
        )
    finally:
        changelog._git_runner_bytes = original_bytes_runner


def test_validate_cross_form_accepts_byte_exact_move_of_a_bundled_record(
    tmp_path: Path,
) -> None:
    """AC-B4: a bundled record moved byte-exactly into an added part is accepted.

    Pins the accepting side of Refusal 1b, so the moved-record check cannot
    start refusing a move whose record bytes are unchanged.
    """
    (tmp_path / "changelog.d").mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    record = changelog.BUNDLE_SEPARATOR_BYTES + _bundle_fragment_text().encode("utf-8")
    (bundle_dir / "2026-10-01.bundle").write_bytes(record)
    _validate_against_fake_base(
        tmp_path, {"changelog.months/2026-10-00.bundle": record}
    )


def test_validate_cross_form_accepts_loose_fragment_deletion_without_a_part(
    tmp_path: Path,
) -> None:
    """AC-B4: deleting a loose fragment in a change that adds no part is accepted."""
    (tmp_path / "changelog.d").mkdir()
    (tmp_path / "changelog.months").mkdir()
    fragment = _fragment_text().encode("utf-8")
    _validate_against_fake_base(tmp_path, {f"changelog.d/{VALID_ID}.md": fragment})


def test_validate_cross_form_refuses_duplicate_id_inside_a_merge_base_part(
    tmp_path: Path,
) -> None:
    """AC-B4: an id twice within one merge-base part is refused, not overwritten.

    Without the refusal the later copy silently replaces the earlier one in
    the moved-record comparison, which then checks the wrong bytes.
    """
    (tmp_path / "changelog.d").mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Distinct dates keep the part in canonical order, so only an id check
    # can catch the repeat.
    first = _bundle_fragment_text(
        date="2026-10-02",
        anchor=changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-10-02", VALID_ID_B
        ),
    )
    second = _bundle_fragment_text()
    base_part = b"".join(
        changelog.BUNDLE_SEPARATOR_BYTES + text.encode("utf-8") for text in (first, second)
    )
    (bundle_dir / "2026-10-01.bundle").write_bytes(
        changelog.BUNDLE_SEPARATOR_BYTES + second.encode("utf-8")
    )
    try:
        _validate_against_fake_base(
            tmp_path, {"changelog.months/2026-10-00.bundle": base_part}
        )
    except changelog.FragmentValidationError as exc:
        message = str(exc)
        assert "2026-10-00.bundle" in message, message
        cause = exc.__cause__
        assert isinstance(cause, changelog.DuplicateRecordIdError), message
        assert VALID_ID_B in str(cause), str(cause)
    else:
        raise AssertionError("a merge-base part holding one id twice was accepted")

# ── F8 (AC-B6 oversized fragment) ────────────────────────────────────────────


def test_compact_leaves_oversized_fragment_loose(tmp_path: Path, monkeypatch) -> None:
    """F8 (AC-B6): compact_month reports a fragment too large for a part and
    leaves it as a loose file rather than bundling it.

    Patches ``MAX_BUNDLE_BYTES`` to one byte below the fragment's record size so
    the oversized check at ``changelog.py`` lines 2783-2791 fires.  The fragment
    must still exist afterwards, no part may be written, and stderr must name the
    fragment as oversized.
    """
    import io as _io_f8

    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    fid = "f8000001-0001-4001-8001-f80000000001"
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-12-01", fid
    )
    text = _fragment_text(
        fragment_id=fid,
        anchor=anchor,
        date="2026-12-01",
        packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
    )
    frag_path = frag_dir / f"{fid}.md"
    frag_path.write_text(text, encoding="utf-8")

    raw = frag_path.read_bytes()
    record_size = len(changelog.BUNDLE_SEPARATOR_BYTES) + len(raw)
    # Set the bound one byte below the record's own size.
    monkeypatch.setattr(changelog, "MAX_BUNDLE_BYTES", record_size - 1)

    captured_stderr = _io_f8.StringIO()
    monkeypatch.setattr(sys, "stderr", captured_stderr)

    created, deleted = changelog.compact_month(
        "2026-12",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )

    stderr_text = captured_stderr.getvalue()

    assert frag_path.exists(), (
        "oversized fragment was deleted despite being too large for a bundle part"
    )
    assert not list(bundle_dir.iterdir()), (
        "a bundle part was written even though every fragment is oversized"
    )
    assert created == [] and deleted == [], (
        f"compact_month returned non-empty lists for an all-oversized run: "
        f"created={created!r}, deleted={deleted!r}"
    )
    assert (
        fid in stderr_text or "too large" in stderr_text or "oversized" in stderr_text
    ), (
        f"oversized fragment not reported in stderr: {stderr_text!r}"
    )
