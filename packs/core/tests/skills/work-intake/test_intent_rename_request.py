"""Construction tests for the rename-request validator.

Covers the request contract: every invalid request refuses with its own
fixed token, and a valid request returns a resolved request object. A
refusal token is one of the eleven fixed strings the module declares;
no other string may be returned.

Four cases pin the fail-closed direction: sources that are structurally
ambiguous must refuse rather than resolve. Two cases guard against
over-strictness: a real corpus-shaped preamble must pass, and a source
with a pointer field beside a damaged tombstone marker must refuse.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK_ROOT / ".apm" / "skills" / "work-intake" / "scripts"

MODULE_NAME = "core_work_intake_intent_rename_request"


def _load_module() -> Any:
    """Load the validator under a pack-and-skill-qualified name."""
    path = _SCRIPTS / "intent_rename_request.py"
    spec = importlib.util.spec_from_file_location(MODULE_NAME, path)
    assert spec and spec.loader, path
    module = importlib.util.module_from_spec(spec)
    # Register before exec so any dataclass defined in the module resolves
    # its own __module__ attribute correctly.
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


validator = _load_module()

# ── Constants ─────────────────────────────────────────────────────────────────

_INTENTS_PARENT = "docs/product/intents"
_SOURCE_REL = "docs/product/intents/FEAT-0001-rename-test.md"
_TOKEN = "FEAT"  # one of NAMESPACE_TOKENS

# ── Fixture helpers ───────────────────────────────────────────────────────────


def _make_intents_dir(root: Path) -> Path:
    """Create docs/product/intents/ under root and return its path."""
    d = root / "docs" / "product" / "intents"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _live_intent_text() -> str:
    """Minimal valid live-intent preamble with no tombstone markers."""
    return "\n".join([
        "# Rename test intent",
        "",
        "- **Slug:** `rename-test`",
        "- **Status:** Draft",
        "- **Level:** feature",
        "- **Owner:** test-owner",
        "",
        "## Outcome",
        "",
        "A placeholder outcome.",
    ])


def _corpus_shaped_intent_text() -> str:
    """Live-intent preamble modelled on a real corpus file.

    Includes an H1 title (not a field) and an annotation bullet (not a field)
    before the first field line, so a validator that requires the whole
    preamble to parse would refuse this source.
    """
    return "\n".join([
        "# Rename test intent: a corpus-shaped preamble",
        "",
        "- **Slug:** `corpus-shaped-rename-test` <!-- canonical identity -->",
        "- Not a field — just a prose annotation before the status.",
        "- **Status:** Accepted",
        "- **Accepted:** 2026-09-21 by the corpus",
        "- **Level:** feature",
        "- **Owner:** test-owner",
        "",
        "## Outcome",
        "",
        "A corpus-shaped preamble outcome.",
    ])


def _workspace_single_entry(source_rel: str) -> str:
    """workspace.toml registering source_rel exactly once."""
    entry = (
        f'path = "{source_rel}", kind = "intent",'
        ' source = {mode = "repo-origin"}, summary = "rename test", needs = []'
    )
    return f"[backlog]\nopen = [{{{entry}}}]\n"


def _workspace_two_entries(source_rel: str) -> str:
    """workspace.toml registering source_rel twice (ambiguous)."""
    entry = (
        f'path = "{source_rel}", kind = "intent",'
        ' source = {mode = "repo-origin"}, summary = "dupe", needs = []'
    )
    return f"[backlog]\nopen = [{{{entry}}}, {{{entry}}}]\n"


def _workspace_entry_with_needs_edge(source_rel: str) -> str:
    """workspace.toml: source_rel registered once; another entry has it in needs."""
    entry = (
        f'path = "{source_rel}", kind = "intent",'
        ' source = {mode = "repo-origin"}, summary = "rename test", needs = []'
    )
    other_rel = "docs/product/intents/FEAT-0002-other.md"
    other_entry = (
        f'path = "{other_rel}", kind = "intent",'
        ' source = {mode = "repo-origin"}, summary = "other",'
        f' needs = [{{type = "local", kind = "intent", path = "{source_rel}"}}]'
    )
    return f"[backlog]\nopen = [{{{entry}}}, {{{other_entry}}}]\n"


def _setup_standard(root: Path, *, registered: bool = True) -> None:
    """Write a valid live intent and an optionally-registering workspace."""
    _make_intents_dir(root)
    intent = root / _SOURCE_REL
    intent.write_text(_live_intent_text(), encoding="utf-8")
    if registered:
        (root / "workspace.toml").write_text(
            _workspace_single_entry(_SOURCE_REL), encoding="utf-8"
        )


# ── Git helpers for tests that need a real working tree ───────────────────────


def _init_git_repo(path: Path) -> None:
    """Initialise a minimal git repository at path."""
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Runner"],
        cwd=path, check=True, capture_output=True,
    )


def _commit_all(path: Path, message: str = "initial") -> None:
    """Stage everything in path and create a commit."""
    subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", message],
        cwd=path, check=True, capture_output=True,
    )


# ── Refusing cases ────────────────────────────────────────────────────────────


def test_absent_source_refuses_source_missing(tmp_path: Path) -> None:
    """A path inside the intent directory that does not exist refuses."""
    _make_intents_dir(tmp_path)
    # No file written; the path does not exist.
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "source-missing"


def test_source_outside_intents_refuses_source_outside_root(tmp_path: Path) -> None:
    """A source path outside docs/product/intents/ refuses."""
    outside = "docs/specs/some-spec/spec.md"
    (tmp_path / "docs" / "specs" / "some-spec").mkdir(parents=True)
    (tmp_path / outside).write_text(_live_intent_text(), encoding="utf-8")
    result = validator.validate_rename_request(
        outside, _TOKEN, repository_root=tmp_path
    )
    assert result == "source-outside-root"


def test_symlink_escaping_root_refuses_source_outside_root(tmp_path: Path) -> None:
    """A symlink whose target resolves outside the intent directory refuses."""
    _make_intents_dir(tmp_path)
    link_path = tmp_path / _SOURCE_REL
    # Point the symlink at a path outside the repository root.
    outside_target = tmp_path.parent / "outside_file.md"
    outside_target.write_text("irrelevant", encoding="utf-8")
    link_path.symlink_to(outside_target)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "source-outside-root"


def test_in_root_symlink_refuses_source_not_regular(tmp_path: Path) -> None:
    """A symlink whose target is inside the root is still not a regular file."""
    d = _make_intents_dir(tmp_path)
    other = d / "FEAT-0002-other.md"
    other.write_text(_live_intent_text(), encoding="utf-8")
    link_path = tmp_path / _SOURCE_REL
    # Symlink to a file inside the root — confinement passes, but it is a symlink.
    link_path.symlink_to(other)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "source-not-regular"


def test_tombstone_source_refuses_source_tombstone(tmp_path: Path) -> None:
    """A source whose preamble carries ``Tombstone:`` refuses."""
    _make_intents_dir(tmp_path)
    tombstone_text = "\n".join([
        "# Retired: rename test intent",
        "",
        "- **Slug:** `rename-test`",
        "- **Tombstone:** 2026-09-21",
        "- **Reissued as:** docs/product/intents/FEAT-0002-renamed.md",
    ])
    (tmp_path / _SOURCE_REL).write_text(tombstone_text, encoding="utf-8")
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "source-tombstone"


def test_unknown_token_refuses_token_unknown(tmp_path: Path) -> None:
    """A target token not in the allocator's namespace refuses."""
    _setup_standard(tmp_path)
    result = validator.validate_rename_request(
        _SOURCE_REL, "BOGUS", repository_root=tmp_path
    )
    assert result == "token-unknown"


def test_unregistered_source_refuses_source_unregistered(tmp_path: Path) -> None:
    """A source with no workspace.toml entry refuses."""
    _setup_standard(tmp_path, registered=False)
    # workspace.toml absent — no entry for the source.
    (tmp_path / "workspace.toml").write_text(
        "[backlog]\nopen = []\n", encoding="utf-8"
    )
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "source-unregistered"


def test_unparseable_registry_refuses_registry_unparseable(tmp_path: Path) -> None:
    """A workspace.toml that is not valid TOML refuses."""
    _setup_standard(tmp_path, registered=False)
    (tmp_path / "workspace.toml").write_text(
        "[[this is not valid toml\n", encoding="utf-8"
    )
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "registry-unparseable"


def test_ambiguous_registry_refuses_registry_ambiguous(tmp_path: Path) -> None:
    """A workspace.toml carrying two entries for the source refuses."""
    _setup_standard(tmp_path, registered=False)
    (tmp_path / "workspace.toml").write_text(
        _workspace_two_entries(_SOURCE_REL), encoding="utf-8"
    )
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "registry-ambiguous"


def test_non_utf8_bytes_refuse_source_unreadable(tmp_path: Path) -> None:
    """A source whose bytes do not decode as UTF-8 refuses (fail-closed)."""
    _make_intents_dir(tmp_path)
    # Write raw bytes that are invalid UTF-8.
    (tmp_path / _SOURCE_REL).write_bytes(b"\xff\xfe invalid utf-8 \x80\x81")
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "source-unreadable"


def test_no_parseable_field_refuses_source_unreadable(tmp_path: Path) -> None:
    """A source whose preamble yields no parsed field refuses (fail-closed).

    An H1 title and blanks do not constitute fields; a validator that
    treats an empty field list as ``live`` would fail open.
    """
    _make_intents_dir(tmp_path)
    no_field_text = "\n".join([
        "# A title with no fields before the heading",
        "",
        "## Outcome",
        "",
        "No preamble fields above.",
    ])
    (tmp_path / _SOURCE_REL).write_text(no_field_text, encoding="utf-8")
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "source-unreadable"


def test_slug_beside_malformed_tombstone_marker_refuses_source_unreadable(
    tmp_path: Path,
) -> None:
    """A good Slug beside a bare ``Tombstone:`` line refuses (fail-closed).

    The preamble parses to a non-empty field list with no ``Tombstone:``
    field, which is exactly what a best-effort parser would call live. A
    validator that tests only the parsed pairs fails open here; the text
    scan on visible preamble lines must catch it.
    """
    _make_intents_dir(tmp_path)
    # ``Tombstone:`` without the ``- **…:**`` prefix does not match the field
    # grammar, so read_preamble returns only the Slug pair.
    malformed_text = "\n".join([
        "# Rename test intent",
        "",
        "- **Slug:** `rename-test`",
        "Tombstone: 2026-09-21",
        "",
        "## Outcome",
        "",
        "Body.",
    ])
    (tmp_path / _SOURCE_REL).write_text(malformed_text, encoding="utf-8")
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "source-unreadable"


def test_root_unresolved_refuses_before_reading(tmp_path: Path) -> None:
    """An invocation whose repository root does not resolve refuses immediately.

    No file is read — the refusal happens before any I/O.
    """
    nonexistent = tmp_path / "no" / "such" / "directory"
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=nonexistent
    )
    assert result == "root-unresolved"


def test_path_dirty_refuses_path_dirty(tmp_path: Path) -> None:
    """A source carrying an uncommitted change refuses before any write."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo)
    _commit_all(repo)

    # Modify the source file without committing.
    (repo / _SOURCE_REL).write_text(
        _live_intent_text() + "\n<!-- dirty change -->\n", encoding="utf-8"
    )
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert result == "path-dirty"


# ── Fail-closed: pointer field without Tombstone ──────────────────────────────


def test_damaged_field_name_tombstone_with_pointer_refuses_source_unreadable(
    tmp_path: Path,
) -> None:
    """``Reissued as:`` beside a field-name-damaged tombstone marker refuses.

    ``Tombstome:`` (typo) parses as a field, writes no ``Tombstone`` token
    anywhere, and leaves ``Reissued as:`` with no partner. A validator that
    checks only the literal ``tombstone`` token in visible lines passes this
    source; the pointer-field-without-Tombstone rule catches it.
    """
    _make_intents_dir(tmp_path)
    damaged_name_text = "\n".join([
        "# Rename test intent",
        "",
        "- **Slug:** `rename-test`",
        "- **Tombstome:** 2026-09-21",  # typo: 'm' instead of 'n'
        "- **Reissued as:** docs/product/intents/FEAT-0002-renamed.md",
        "",
        "## Outcome",
        "",
        "Body.",
    ])
    (tmp_path / _SOURCE_REL).write_text(damaged_name_text, encoding="utf-8")
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "source-unreadable"


# ── Anti-over-strictness ──────────────────────────────────────────────────────


def test_corpus_shaped_preamble_passes(tmp_path: Path) -> None:
    """A real corpus-shaped preamble — H1 title and annotation bullet — passes.

    A validator that requires every visible preamble line to match the
    field grammar would refuse this source, because the H1 title and the
    annotation bullet do not match ``_FIELD_LINE``. Strictness is scoped
    to the ``Tombstone:`` marker, not the whole preamble.

    Requires a git working tree: the dirty check (B1) now fails closed, so
    a non-git directory would refuse ``path-dirty``.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo, registered=False)
    (repo / _SOURCE_REL).write_text(_corpus_shaped_intent_text(), encoding="utf-8")
    (repo / "workspace.toml").write_text(
        _workspace_single_entry(_SOURCE_REL), encoding="utf-8"
    )
    _commit_all(repo)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert isinstance(result, validator.ResolvedRequest)


# ── Positive case ─────────────────────────────────────────────────────────────


def test_valid_request_returns_resolved_request(tmp_path: Path) -> None:
    """A fully valid request returns a ``ResolvedRequest``, not a string.

    Requires a git working tree: the dirty check (B1) now fails closed, so
    a non-git directory would refuse ``path-dirty``.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo)
    _commit_all(repo)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert isinstance(result, validator.ResolvedRequest)
    assert result.source_rel == _SOURCE_REL
    assert result.target_token == _TOKEN
    assert result.repository_root == repo.resolve()


# ── Repository root resolution ────────────────────────────────────────────────


def test_subdirectory_root_resolves_to_git_toplevel(tmp_path: Path) -> None:
    """Root discovered via git rev-parse is the toplevel, not the cwd.

    Validation invoked from a subdirectory must use the repository root
    rather than the working directory as the confinement boundary.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo)
    _commit_all(repo)

    subdir = repo / "docs" / "product"
    # subdir was already created by _setup_standard via _make_intents_dir.

    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, _cwd=subdir
    )
    assert isinstance(result, validator.ResolvedRequest), (
        f"expected ResolvedRequest, got {result!r}"
    )
    # The root must be the git toplevel (repo), not the subdirectory.
    assert result.repository_root == repo.resolve()


# ── B1: fail-closed dirty check ───────────────────────────────────────────────


def test_is_dirty_git_launch_failure_returns_path_dirty(tmp_path: Path) -> None:
    """A git status OSError is treated as dirty, not clean.

    The ls-files probe runs first and succeeds (both paths are tracked with
    tag ``H``). Only the subsequent status probe is failed with OSError.
    A blanket ``subprocess.run`` patch would fire on ls-files and never reach
    the status branch, so the patch inspects argv: ls-files calls are
    forwarded to the real subprocess.run; status raises OSError. Deleting
    the OSError branch in ``_is_dirty`` leaves this test red.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo)
    _commit_all(repo)

    _real_run = subprocess.run

    def _fail_status_oserror(*args, **kwargs):
        cmd = list(args[0]) if args else []
        if "ls-files" in cmd:
            return _real_run(*args, **kwargs)
        if "status" in cmd:
            raise OSError("simulated git failure")
        return _real_run(*args, **kwargs)

    with patch("subprocess.run", side_effect=_fail_status_oserror):
        result = validator.validate_rename_request(
            _SOURCE_REL, _TOKEN, repository_root=repo
        )
    assert result == "path-dirty"


def test_is_dirty_timeout_returns_path_dirty(tmp_path: Path) -> None:
    """A git status TimeoutExpired is treated as dirty, not clean.

    The ls-files probe succeeds; only the status probe is failed with
    TimeoutExpired. The patch inspects argv so ls-files is forwarded to the
    real subprocess.run. Deleting the TimeoutExpired branch in ``_is_dirty``
    leaves this test red.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo)
    _commit_all(repo)

    _real_run = subprocess.run

    def _fail_status_timeout(*args, **kwargs):
        cmd = list(args[0]) if args else []
        if "ls-files" in cmd:
            return _real_run(*args, **kwargs)
        if "status" in cmd:
            raise subprocess.TimeoutExpired(cmd=["git"], timeout=10)
        return _real_run(*args, **kwargs)

    with patch("subprocess.run", side_effect=_fail_status_timeout):
        result = validator.validate_rename_request(
            _SOURCE_REL, _TOKEN, repository_root=repo
        )
    assert result == "path-dirty"


def test_is_dirty_nonzero_exit_returns_path_dirty(tmp_path: Path) -> None:
    """A nonzero git status exit code is treated as dirty, not clean.

    The ls-files probe succeeds; only the status probe returns exit code 128.
    The patch inspects argv so ls-files is forwarded to the real subprocess.run
    while status returns a nonzero CompletedProcess. Deleting the nonzero-
    returncode branch in ``_is_dirty`` leaves this test red.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo)
    _commit_all(repo)

    _real_run = subprocess.run

    def _fail_status_nonzero(*args, **kwargs):
        cmd = list(args[0]) if args else []
        if "ls-files" in cmd:
            return _real_run(*args, **kwargs)
        if "status" in cmd:
            return subprocess.CompletedProcess(
                args=cmd, returncode=128, stdout=b"", stderr=b""
            )
        return _real_run(*args, **kwargs)

    with patch("subprocess.run", side_effect=_fail_status_nonzero):
        result = validator.validate_rename_request(
            _SOURCE_REL, _TOKEN, repository_root=repo
        )
    assert result == "path-dirty"


# ── B2: workspace.toml included in dirty check ────────────────────────────────


def test_dirty_workspace_toml_returns_path_dirty(tmp_path: Path) -> None:
    """A dirty workspace.toml beside a clean source refuses with ``path-dirty``.

    The rename transaction touches workspace.toml, so any uncommitted change
    there must block the request even when the source file itself is clean.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo)
    _commit_all(repo)
    # Modify workspace.toml without committing; leave the source unchanged.
    (repo / "workspace.toml").write_text(
        _workspace_single_entry(_SOURCE_REL) + "# dirty\n", encoding="utf-8"
    )
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert result == "path-dirty"


# ── B3: registry matching counts only entry-level paths ───────────────────────


def test_needs_edge_not_counted_as_registration(tmp_path: Path) -> None:
    """An intent listed in another entry's ``needs`` is not double-counted.

    When entry A is registered and entry B lists A in its ``needs`` array,
    the count for A must be 1, not 2. A count of 2 would refuse with
    ``registry-ambiguous`` even though A has exactly one real registration.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo, registered=False)
    (repo / "workspace.toml").write_text(
        _workspace_entry_with_needs_edge(_SOURCE_REL), encoding="utf-8"
    )
    _commit_all(repo)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert isinstance(result, validator.ResolvedRequest), (
        f"expected ResolvedRequest, got {result!r}"
    )


def test_needs_only_entry_is_unregistered(tmp_path: Path) -> None:
    """An intent named only in a ``needs`` edge is not considered registered.

    If the source appears only as a ``needs`` edge inside another entry's
    array, it has no own registration and must refuse with
    ``source-unregistered``.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _make_intents_dir(repo)
    other_rel = "docs/product/intents/FEAT-0002-other.md"
    (repo / _SOURCE_REL).write_text(_live_intent_text(), encoding="utf-8")
    (repo / other_rel).write_text(_live_intent_text(), encoding="utf-8")
    # Only other_rel is registered; _SOURCE_REL appears only in needs.
    other_entry = (
        f'path = "{other_rel}", kind = "intent",'
        ' source = {mode = "repo-origin"}, summary = "other",'
        f' needs = [{{type = "local", kind = "intent", path = "{_SOURCE_REL}"}}]'
    )
    (repo / "workspace.toml").write_text(
        f"[backlog]\nopen = [{{{other_entry}}}]\n", encoding="utf-8"
    )
    _commit_all(repo)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert result == "source-unregistered"


# ── B5: liveness scan does not over-fire on field values ──────────────────────


def test_leading_h1_title_containing_tombstone_passes(tmp_path: Path) -> None:
    """A leading H1 title containing ``tombstone`` does not refuse a live source.

    Blank lines and HTML comments do not consume the single leading-title
    exemption. The exemption is deliberately limited to the title: later
    non-field lines with the token remain damaged markers.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _make_intents_dir(repo)
    text = "\n".join([
        "   ",
        "   <!-- title metadata -->",
        "",
        "# Tombstone migration plan",
        "",
        "- **Slug:** `tombstone-migration`",
        "- **Status:** Draft",
        "- **Level:** feature",
        "- **Owner:** test-owner",
        "",
        "## Outcome",
        "",
        "Body.",
    ])
    (repo / _SOURCE_REL).write_text(text, encoding="utf-8")
    (repo / "workspace.toml").write_text(
        _workspace_single_entry(_SOURCE_REL), encoding="utf-8"
    )
    _commit_all(repo)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert isinstance(result, validator.ResolvedRequest), (
        f"expected ResolvedRequest, got {result!r}"
    )


def test_second_h1_containing_tombstone_refuses_source_unreadable(
    tmp_path: Path,
) -> None:
    """A second H1 containing ``tombstone`` remains a damaged marker.

    Only one leading H1 title is exempt. A later H1 is a token-bearing
    non-field preamble line and must refuse rather than widening the
    authorized exception to every heading.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _make_intents_dir(repo)
    text = "\n".join([
        "# Rename test intent",
        "",
        "# Tombstone migration plan",
        "",
        "- **Slug:** `rename-test`",
        "- **Status:** Draft",
        "",
        "## Outcome",
        "",
        "Body.",
    ])
    (repo / _SOURCE_REL).write_text(text, encoding="utf-8")
    (repo / "workspace.toml").write_text(
        _workspace_single_entry(_SOURCE_REL), encoding="utf-8"
    )
    _commit_all(repo)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert result == "source-unreadable"


def test_comment_spliced_pseudo_title_refuses_source_unreadable(
    tmp_path: Path,
) -> None:
    """A ``# `` exposed only by comment removal is not a title and refuses.

    The heading marker must open the authored line. Here it does not: the
    line begins with an HTML comment, so the token-bearing remainder is a
    damaged marker rather than the document title, and the leading-title
    exemption must not reach it.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _make_intents_dir(repo)
    text = "\n".join([
        "<!-- metadata --># Tombstone: 2026-09-28",
        "",
        "- **Slug:** `rename-test`",
        "- **Status:** Draft",
        "",
        "## Outcome",
        "",
        "Body.",
    ])
    (repo / _SOURCE_REL).write_text(text, encoding="utf-8")
    (repo / "workspace.toml").write_text(
        _workspace_single_entry(_SOURCE_REL), encoding="utf-8"
    )
    _commit_all(repo)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert result == "source-unreadable"


def test_h1_title_with_trailing_comment_passes(tmp_path: Path) -> None:
    """A leading H1 title carrying a trailing comment keeps the exemption.

    The marker opens the authored line, so removing a trailing comment does
    not make the line anything other than the document title.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _make_intents_dir(repo)
    text = "\n".join([
        "# Tombstone migration plan <!-- rename me -->",
        "",
        "- **Slug:** `tombstone-migration`",
        "- **Status:** Draft",
        "",
        "## Outcome",
        "",
        "Body.",
    ])
    (repo / _SOURCE_REL).write_text(text, encoding="utf-8")
    (repo / "workspace.toml").write_text(
        _workspace_single_entry(_SOURCE_REL), encoding="utf-8"
    )
    _commit_all(repo)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert isinstance(result, validator.ResolvedRequest), (
        f"expected ResolvedRequest, got {result!r}"
    )


def test_slug_value_containing_tombstone_passes(tmp_path: Path) -> None:
    """A source whose Slug value contains ``tombstone`` is not refused.

    A validator that scans field values rather than only non-field lines
    would refuse this source with ``source-unreadable``. The tombstone token
    check applies only to lines that do NOT parse as any well-formed field.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _make_intents_dir(repo)
    text = "\n".join([
        "# Migration intent",
        "",
        "- **Slug:** `tombstone-migration`",
        "- **Status:** Draft",
        "- **Level:** feature",
        "- **Owner:** test-owner",
        "",
        "## Outcome",
        "",
        "Body.",
    ])
    (repo / _SOURCE_REL).write_text(text, encoding="utf-8")
    (repo / "workspace.toml").write_text(
        _workspace_single_entry(_SOURCE_REL), encoding="utf-8"
    )
    _commit_all(repo)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert isinstance(result, validator.ResolvedRequest), (
        f"expected ResolvedRequest, got {result!r}"
    )


def test_annotation_bullet_mentioning_tombstone_passes(tmp_path: Path) -> None:
    """A field whose value mentions ``tombstone`` in prose is not refused.

    An annotation field like ``- **Note:** supersedes the tombstone approach``
    parses as a well-formed field, so it is exempt from the damaged-marker
    scan regardless of its value.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _make_intents_dir(repo)
    text = "\n".join([
        "# Some intent",
        "",
        "- **Slug:** `some-intent`",
        "- **Note:** supersedes the tombstone approach",
        "- **Status:** Draft",
        "- **Level:** feature",
        "- **Owner:** test-owner",
        "",
        "## Outcome",
        "",
        "Body.",
    ])
    (repo / _SOURCE_REL).write_text(text, encoding="utf-8")
    (repo / "workspace.toml").write_text(
        _workspace_single_entry(_SOURCE_REL), encoding="utf-8"
    )
    _commit_all(repo)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert isinstance(result, validator.ResolvedRequest), (
        f"expected ResolvedRequest, got {result!r}"
    )


# ── B7: registry read through the blessed confinement helper ──────────────────


def test_symlinked_workspace_toml_refuses_registry_unparseable(
    tmp_path: Path,
) -> None:
    """A workspace.toml that is a symlink refuses with ``registry-unparseable``.

    The confinement helper refuses symlinks before reading. Mapping that
    safety violation onto ``registry-unparseable`` keeps the source-registration
    decision from being steered by a symlinked registry.
    """
    _make_intents_dir(tmp_path)
    (tmp_path / _SOURCE_REL).write_text(_live_intent_text(), encoding="utf-8")
    # Write a valid workspace file outside the root, then symlink to it.
    outside = tmp_path.parent / "outside_workspace.toml"
    outside.write_text(_workspace_single_entry(_SOURCE_REL), encoding="utf-8")
    (tmp_path / "workspace.toml").symlink_to(outside)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "registry-unparseable"


# ── B2: dirty probe requires positive proof of cleanliness ────────────────────


def test_ignored_untracked_source_refuses_path_dirty(tmp_path: Path) -> None:
    """A source that is ignored and untracked refuses with ``path-dirty``.

    ``git status --porcelain`` prints nothing for an ignored-and-untracked
    path, so absence of output alone cannot establish cleanliness. The
    positive ls-files check detects that the path is not tracked and reports
    dirty.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _make_intents_dir(repo)

    # Commit workspace.toml and a .gitignore that hides the source — but
    # intentionally do NOT add the source to the index.
    (repo / "workspace.toml").write_text(
        _workspace_single_entry(_SOURCE_REL), encoding="utf-8"
    )
    (repo / ".gitignore").write_text(_SOURCE_REL + "\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "workspace.toml", ".gitignore"],
        cwd=repo, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init without source"],
        cwd=repo, check=True, capture_output=True,
    )

    # Write the source after committing; it is now ignored and untracked.
    (repo / _SOURCE_REL).write_text(_live_intent_text(), encoding="utf-8")

    result = validator.validate_rename_request(_SOURCE_REL, _TOKEN, repository_root=repo)
    assert result == "path-dirty"


def test_assume_unchanged_modified_source_refuses_path_dirty(tmp_path: Path) -> None:
    """A source modified after ``--assume-unchanged`` refuses with ``path-dirty``.

    ``git status --porcelain`` skips the working-tree stat check for files
    flagged assume-unchanged, so a modification is invisible to it.  The
    ls-files -v check detects the ``h`` flag and reports dirty regardless of
    whether the file is actually modified.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo)
    _commit_all(repo)

    subprocess.run(
        ["git", "update-index", "--assume-unchanged", _SOURCE_REL],
        cwd=repo, check=True, capture_output=True,
    )
    # Modify the source; git won't notice due to the assume-unchanged flag.
    (repo / _SOURCE_REL).write_text(
        _live_intent_text() + "\n<!-- assume-unchanged edit -->\n",
        encoding="utf-8",
    )

    result = validator.validate_rename_request(_SOURCE_REL, _TOKEN, repository_root=repo)
    assert result == "path-dirty"


def test_skip_worktree_modified_source_refuses_path_dirty(tmp_path: Path) -> None:
    """A source modified after ``--skip-worktree`` refuses with ``path-dirty``.

    Like assume-unchanged, skip-worktree hides working-tree modifications
    from ``git status``. The ls-files -v check detects the ``S`` flag.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo)
    _commit_all(repo)

    subprocess.run(
        ["git", "update-index", "--skip-worktree", _SOURCE_REL],
        cwd=repo, check=True, capture_output=True,
    )
    (repo / _SOURCE_REL).write_text(
        _live_intent_text() + "\n<!-- skip-worktree edit -->\n",
        encoding="utf-8",
    )

    result = validator.validate_rename_request(_SOURCE_REL, _TOKEN, repository_root=repo)
    assert result == "path-dirty"


def test_combined_index_flags_modified_source_refuses_path_dirty(tmp_path: Path) -> None:
    """A source modified after both ``--assume-unchanged`` and ``--skip-worktree`` refuses.

    git emits the lowercase tag ``s`` when both flags are set simultaneously.
    The previous denylist recognised ``h`` and ``S`` but missed ``s`` (the
    combined state). The current allowlist — only ``H`` is clean — rejects every
    non-H tag, including ``s``. Reverting to a denylist that omits ``s`` leaves
    this test red.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo)
    _commit_all(repo)

    subprocess.run(
        ["git", "update-index", "--assume-unchanged", _SOURCE_REL],
        cwd=repo, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "update-index", "--skip-worktree", _SOURCE_REL],
        cwd=repo, check=True, capture_output=True,
    )
    (repo / _SOURCE_REL).write_text(
        _live_intent_text() + "\n<!-- combined-flags edit -->\n",
        encoding="utf-8",
    )

    result = validator.validate_rename_request(_SOURCE_REL, _TOKEN, repository_root=repo)
    assert result == "path-dirty"


def test_non_ascii_filename_clean_resolves(tmp_path: Path) -> None:
    """A committed intent with a non-ASCII filename resolves without ``path-dirty``.

    Without ``-z``, git renders non-ASCII paths in octal-escaped form when
    ``core.quotePath`` is true; a clean tracked file whose name carries a
    non-ASCII character would never match the name we asked about, and would
    refuse with ``path-dirty``. NUL-separated records from ``-z`` are byte-exact
    regardless of ``core.quotePath``. This test would fail if ``-z`` were removed
    from the ``ls-files`` invocation.

    ``core.quotePath`` is set to true explicitly so the test pins this behaviour
    regardless of the runner's global git config.
    """
    non_ascii_rel = "docs/product/intents/FEAT-0001-café.md"
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    subprocess.run(
        ["git", "config", "core.quotePath", "true"],
        cwd=repo, check=True, capture_output=True,
    )
    _make_intents_dir(repo)
    (repo / non_ascii_rel).write_text(_live_intent_text(), encoding="utf-8")
    (repo / "workspace.toml").write_text(
        _workspace_single_entry(non_ascii_rel), encoding="utf-8"
    )
    _commit_all(repo)
    result = validator.validate_rename_request(
        non_ascii_rel, _TOKEN, repository_root=repo
    )
    assert isinstance(result, validator.ResolvedRequest), (
        f"expected ResolvedRequest for non-ASCII filename, got {result!r}"
    )


# ── B3: registry matching counts only declared collection entries ─────────────


def test_decoy_table_is_not_counted_as_registered(tmp_path: Path) -> None:
    """A bare TOML table carrying ``path`` but outside a collection array is not counted.

    ``[decoy]\\npath = "..."`` puts a dict value at the document level, not
    inside any collection array. The old generic dict traversal counted it
    because any dict with a ``path`` key was treated as an entry. The new
    structural traversal requires position inside an array.
    """
    _setup_standard(tmp_path, registered=False)
    decoy_toml = (
        f'[decoy]\npath = "{_SOURCE_REL}"\n'
    )
    (tmp_path / "workspace.toml").write_text(decoy_toml, encoding="utf-8")
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "source-unregistered"


@pytest.mark.parametrize(
    ("shape", "registry_toml"),
    [
        ("array of tables", '[[decoy]]\npath = "{p}"\n'),
        ("inline array of dicts", '[decoy]\nitems = [ {{ path = "{p}" }} ]\n'),
        ("nested two deep", '[a.b]\nitems = [ {{ path = "{p}" }} ]\n'),
        ("collection name under the wrong parent", '[notes]\nopen = [ {{ path = "{p}" }} ]\n'),
        ("initiative collection outside an initiative", '[other]\nshaping_queue = [ {{ path = "{p}" }} ]\n'),
        # Initiative keys must match ^ini-\d{3}$ exactly. A non-digit suffix
        # and a two-digit ordinal both fail the canonical check, so entries
        # under those tables must not be counted as registrations.
        ("ini-decoy prefix not canonical", '[ini-decoy.work]\nqueue = [ {{ path = "{p}" }} ]\n'),
        ("ini-01 two-digit key not canonical", '[ini-01.work]\nqueue = [ {{ path = "{p}" }} ]\n'),
    ],
)
def test_decoy_arrays_outside_a_registry_collection_are_not_counted(
    tmp_path: Path, shape: str, registry_toml: str
) -> None:
    """A path inside any array outside a declared collection is unregistered.

    Position inside *some* array is not registration. Each shape here puts a
    matching ``path`` in an array the register does not own, and an earlier
    revision counted every one of them because it asked only whether a dict
    sat in a list. Registration is decided by the whole key path, so these
    stay unregistered however entry-shaped they look.
    """
    _setup_standard(tmp_path, registered=False)
    (tmp_path / "workspace.toml").write_text(
        registry_toml.format(p=_SOURCE_REL), encoding="utf-8"
    )
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
    )
    assert result == "source-unregistered", f"{shape} was counted as a registration"


@pytest.mark.parametrize(
    "registry_toml",
    [
        '[ini-010.work]\nqueue = [ {{ path = "{p}" }} ]\n',
        '[ini-010.work]\nactive = [ {{ path = "{p}" }} ]\n',
        '[ini-010.work]\nshipped = [ {{ path = "{p}" }} ]\n',
        '[ini-010.shaping_queue]\nbacklog = [ {{ path = "{p}" }} ]\n',
        '[ini-010.shaping_queue]\nactive = [ {{ path = "{p}" }} ]\n',
        '[backlog]\nopen = [ {{ path = "{p}" }} ]\n',
    ],
)
def test_every_declared_registry_collection_registers(
    tmp_path: Path, registry_toml: str
) -> None:
    """Each collection the register actually uses counts as a registration.

    The companion decoy test constrains position; this one keeps that
    constraint from being drawn too tightly. An earlier revision admitted
    only the work collections and silently stopped counting the seventeen
    intents registered under an initiative's shaping backlog.

    Needs a committed working tree: the dirty check proves each guarded path
    is tracked and unchanged, so a bare directory refuses before the
    registration result is reachable.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _setup_standard(repo, registered=False)
    (repo / "workspace.toml").write_text(
        registry_toml.format(p=_SOURCE_REL), encoding="utf-8"
    )
    _commit_all(repo)
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=repo
    )
    assert not isinstance(result, str), f"expected a resolved request, got {result!r}"


# ── C2: root-discovery failures refuse before reading ─────────────────────────


def test_cwd_oserror_refuses_root_unresolved_before_reading(tmp_path: Path) -> None:
    """When ``Path.cwd()`` raises ``OSError``, root-unresolved is returned before
    any file is read.

    The ``_cwd`` seam is absent (``None``), so discovery calls ``Path.cwd()``.
    Patching it to raise ``OSError`` exercises the guarded branch and asserts
    that no I/O happens before the refusal.
    """
    with (
        patch.object(Path, "cwd", side_effect=OSError("no cwd")),
        patch.object(
            validator._file_safety,
            "read_confined_regular_file",
        ) as mock_read,
    ):
        result = validator.validate_rename_request(_SOURCE_REL, _TOKEN)
    assert result == "root-unresolved"
    mock_read.assert_not_called()


def test_non_git_cwd_refuses_root_unresolved_before_reading(tmp_path: Path) -> None:
    """When git discovery fails from ``_cwd``, root-unresolved is returned before
    any file is read.

    A directory that is not a git working tree causes ``git rev-parse``
    to exit nonzero, so ``_git_toplevel`` returns ``None``, and
    ``validate_rename_request`` returns ``root-unresolved`` without reading
    any file.
    """
    non_git = tmp_path / "non_git_dir"
    non_git.mkdir()
    with patch.object(
        validator._file_safety,
        "read_confined_regular_file",
    ) as mock_read:
        result = validator.validate_rename_request(
            _SOURCE_REL, _TOKEN, _cwd=non_git
        )
    assert result == "root-unresolved"
    mock_read.assert_not_called()


# ── C3: sys.dont_write_bytecode is restored after module load ─────────────────


@pytest.mark.parametrize("flag", [True, False])
def test_dont_write_bytecode_preserved_after_import(flag: bool) -> None:
    """sys.dont_write_bytecode equals its preset value after the module loads.

    The module saves and restores sys.dont_write_bytecode around the sibling
    loads. This test presets the flag to each boolean and asserts the preset
    is unchanged after a fresh execution of the module body. Deleting the
    save/restore would leave the flag True (the value set by the module body)
    regardless of the preset.
    """
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = flag
    unique_name = f"{MODULE_NAME}_bytecode_test_{flag}"
    try:
        path = _SCRIPTS / "intent_rename_request.py"
        spec = importlib.util.spec_from_file_location(unique_name, path)
        assert spec and spec.loader, path
        module = importlib.util.module_from_spec(spec)
        sys.modules[unique_name] = module
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        assert sys.dont_write_bytecode == flag, (
            f"sys.dont_write_bytecode changed from {flag!r} to "
            f"{sys.dont_write_bytecode!r} after module load"
        )
    finally:
        sys.dont_write_bytecode = prev
        sys.modules.pop(unique_name, None)
