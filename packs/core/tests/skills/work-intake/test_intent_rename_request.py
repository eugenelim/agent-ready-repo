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
    """A git launch failure (OSError) is treated as dirty, not clean.

    A non-git directory or a missing git binary causes subprocess.run to
    raise OSError. The fail-closed rule maps that to ``path-dirty`` rather
    than silently passing the request.
    """
    _setup_standard(tmp_path)
    with patch("subprocess.run", side_effect=OSError("git not found")):
        result = validator.validate_rename_request(
            _SOURCE_REL, _TOKEN, repository_root=tmp_path
        )
    assert result == "path-dirty"


def test_is_dirty_timeout_returns_path_dirty(tmp_path: Path) -> None:
    """A git status timeout is treated as dirty, not clean."""
    _setup_standard(tmp_path)
    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["git"], timeout=10),
    ):
        result = validator.validate_rename_request(
            _SOURCE_REL, _TOKEN, repository_root=tmp_path
        )
    assert result == "path-dirty"


def test_is_dirty_nonzero_exit_returns_path_dirty(tmp_path: Path) -> None:
    """A nonzero git status exit code is treated as dirty, not clean.

    Running ``git status`` inside a directory that is not a git repository
    exits 128. The fail-closed rule maps any nonzero exit to ``path-dirty``.
    """
    _setup_standard(tmp_path)
    # tmp_path is not a git repository; git status exits nonzero.
    result = validator.validate_rename_request(
        _SOURCE_REL, _TOKEN, repository_root=tmp_path
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
