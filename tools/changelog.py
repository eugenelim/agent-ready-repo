#!/usr/bin/env python3
"""Shared product changelog parser, slugger, and /now/ projector."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import subprocess
import sys
import tomllib
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path
from types import ModuleType
from typing import NamedTuple
from uuid import UUID, uuid4

# Seven calendar days ending on launch day, inclusive (brief decision 19): the
# launch date itself plus the six dates before it.
NOW_WINDOW_DAYS = 7
MAX_FRAGMENT_DIR_ENTRIES = 65_536
MAX_FRAGMENT_FILES = 65_536
MAX_FRAGMENT_DEPTH = 1
MAX_FRAGMENT_BYTES = 1_048_576

# ADR-0143: monthly bundle parts.
# Separator that opens each record in a bundle part file.
BUNDLE_SEPARATOR_BYTES = b"+++ record +++\n"
BUNDLE_SEPARATOR_LINE = "+++ record +++"
# Per-file byte bounds for bundle parts, merge-base blobs, and the retraction list.
MAX_BUNDLE_BYTES = 1_048_576
MAX_RETRACTION_BYTES = 1_048_576
# Hard cap on records across both storage forms (ADR-0143 D10).
MAX_RECORD_COUNT = 65_536
# Traversal bounds for the bundle directory, matching fragment-directory limits.
MAX_BUNDLE_DIR_ENTRIES = 65_536
MAX_BUNDLE_FILES = 65_536
MAX_BUNDLE_DEPTH = 1
# `YYYY-MM-NN.bundle` — real month and unique two-digit NN.
_BUNDLE_NAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.bundle$")
# Retraction list schema.
_RETRACTION_CATEGORIES = frozenset({"credential", "personal-data", "legal", "other"})
_RETRACTION_FIELDS = frozenset({"id", "category"})
# Warning and refusal thresholds for build-site (ADR-0143 D9).
LOOSE_RELEASED_WARN_THRESHOLD = 375
LOOSE_RELEASED_REFUSE_THRESHOLD = 500
PENDING_WARN_THRESHOLD = 250

_FRAGMENT_FIELDS = frozenset({"schema", "id", "anchor", "date", "packages"})
_PACKAGE_FIELDS = frozenset({"name", "version"})
_PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_PACKAGE_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
_FRAGMENT_SECTION_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
_FRAGMENT_BULLET_RE = re.compile(r"^[ \t]*[-*+][ \t]+(.+)$")
_FRAGMENT_SCHEMA = 1
_FRAGMENT_SECTIONS = frozenset({
    "Highlights",
    "Added",
    "Changed",
    "Deprecated",
    "Removed",
    "Fixed",
    "Security",
})


class FragmentValidationError(ValueError):
    """A fragment source failed validation before it could enter the model."""


class DuplicateRecordIdError(FragmentValidationError):
    """A record id appears more than once across storage forms.

    Raised instead of the base class at the cross-form duplicate-id site so
    that ``compact_month``'s rerun-recovery path can dispatch on type rather
    than on a fragile message substring match.
    """

    def __init__(self, message: str, *, record_id: str) -> None:
        """Create a duplicate-id error carrying the offending id."""
        super().__init__(message)
        self.record_id = record_id


class ValidatedFragment(NamedTuple):
    """One validated fragment record."""

    path: Path
    schema: int
    id: str
    anchor: str
    date: str
    packages: list[dict[str, str]]
    sections: dict[str, list[str]]


class _GitResult(NamedTuple):
    """Captured Git command result for the identity boundary."""

    returncode: int
    stdout: str
    stderr: str


class _MergeBaseContext(NamedTuple):
    """Merge-base Git state resolved once for a whole validation pass.

    Every field here is one Git answer covering every fragment in the pass, so
    a pass costs a fixed number of subprocesses instead of one set per file.
    ``statuses`` maps a repository-relative path to its merge-base
    classification, ``tracked`` holds the paths Git has in the index, and
    ``unattributable`` holds paths whose diff line named a status this
    validator does not model, so that path refuses when it is validated rather
    than failing the whole set.
    """

    repo: Path
    merge_base: str
    statuses: dict[str, tuple[str, str | None]]
    tracked: frozenset[str]
    unattributable: frozenset[str]


def _file_safety() -> ModuleType:
    """Load the repository's blessed file-safety helper by path."""
    source = (
        Path(__file__).resolve().parent.parent
        / "packages"
        / "agentbundle"
        / "agentbundle"
        / "catalogue_tooling"
        / "file_safety.py"
    )
    spec = importlib.util.spec_from_file_location("_changelog_file_safety", source)
    if spec is None or spec.loader is None:
        raise ValueError("file-safety-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fragment_error(path: Path, field: str, expected: str) -> FragmentValidationError:
    """Create the standard fragment validation diagnostic."""
    return FragmentValidationError(f"{path}: {field}: expected {expected}")


def _split_fragment_source(path: Path, text: str) -> tuple[str, str]:
    """Return ``(front_matter, body)`` or refuse delimiter defects."""
    if not text.startswith("+++\n"):
        raise _fragment_error(path, "envelope delimiter", "file must start with +++")
    closing = text.find("\n+++\n", 4)
    if closing < 0:
        raise _fragment_error(path, "envelope delimiter", "closing +++ delimiter")
    return text[4:closing], text[closing + len("\n+++\n"):]


def _parse_fragment_toml(path: Path, front_matter: str) -> dict:
    """Parse fragment TOML and normalize syntax errors into diagnostics."""
    try:
        data = tomllib.loads(front_matter)
    except tomllib.TOMLDecodeError as exc:
        date_match = re.search(r"(?m)^date\s*=\s*(\d{4}-\d{2}-\d{2})\s*$", front_matter)
        if date_match is not None:
            try:
                date.fromisoformat(date_match.group(1))
            except ValueError:
                raise _fragment_error(
                    path, "date", "real ISO YYYY-MM-DD calendar date"
                ) from exc
        raise _fragment_error(path, "envelope TOML", "well-formed TOML") from exc
    if not isinstance(data, dict):
        raise _fragment_error(path, "envelope", "TOML table")
    return data


def _require_fragment_fields(path: Path, data: dict) -> None:
    """Refuse missing, unknown, or wrong-typed envelope fields."""
    for field in ("schema", "id", "anchor", "date", "packages"):
        if field not in data:
            raise _fragment_error(path, field, "required field")
    for field in data:
        if field not in _FRAGMENT_FIELDS:
            raise _fragment_error(path, field, "no unknown envelope fields")
    if not isinstance(data["schema"], int) or isinstance(data["schema"], bool):
        raise _fragment_error(path, "schema", "integer schema version 1")
    if data["schema"] != _FRAGMENT_SCHEMA:
        raise _fragment_error(path, "schema", "schema version 1")
    if not isinstance(data["id"], str):
        raise _fragment_error(path, "id", "lowercase UUIDv4 string")
    if not isinstance(data["anchor"], str):
        raise _fragment_error(path, "anchor", "slug-and-uuid string")
    if not isinstance(data["date"], date):
        raise _fragment_error(path, "date", "real ISO YYYY-MM-DD calendar date")
    if not isinstance(data["packages"], list) or not data["packages"]:
        raise _fragment_error(path, "packages", "one or more package records")


def _validate_fragment_id(
    path: Path, raw_id: str, *, check_stem: bool = True
) -> str:
    """Return a lowercase UUIDv4 string or refuse."""
    try:
        parsed = UUID(raw_id, version=4)
    except ValueError as exc:
        raise _fragment_error(path, "id", "lowercase UUIDv4 string") from exc
    if parsed.version != 4 or str(parsed) != raw_id:
        raise _fragment_error(path, "id", "lowercase UUIDv4 string")
    if check_stem and path.stem != raw_id:
        raise _fragment_error(path, "id", "filename stem must equal envelope id")
    return raw_id


def _validate_packages(path: Path, raw_packages: list) -> list[dict[str, str]]:
    """Validate package metadata before it reaches heading or identity sinks."""
    packages: list[dict[str, str]] = []
    for index, raw_package in enumerate(raw_packages, start=1):
        if not isinstance(raw_package, dict):
            raise _fragment_error(path, f"packages[{index}]", "package table")
        for field in raw_package:
            if field not in _PACKAGE_FIELDS:
                raise _fragment_error(
                    path, f"packages[{index}].{field}", "name and version only"
                )
        for field, grammar in (("name", _PACKAGE_NAME_RE), ("version", _PACKAGE_VERSION_RE)):
            value = raw_package.get(field)
            expected = (
                "[A-Za-z0-9][A-Za-z0-9._-]*"
                if field == "name"
                else "[A-Za-z0-9][A-Za-z0-9._+-]*"
            )
            if not isinstance(value, str) or grammar.fullmatch(value) is None:
                raise _fragment_error(path, f"packages[{index}].{field}", expected)
        packages.append({"name": raw_package["name"], "version": raw_package["version"]})
    return packages


def _fragment_heading(packages: list[dict[str, str]], fragment_date: str) -> str:
    """Compose the established changelog release heading for one fragment."""
    package_text = " and ".join(
        f"[{package['name']}][{package['version']}]" for package in packages
    )
    return f"{package_text} — {fragment_date}"


def _compose_fragment_anchor(
    packages: list[dict[str, str]], fragment_date: str, fragment_id: str
) -> str:
    """Compose the stable published anchor for a fragment."""
    return f"{_slug_base(_fragment_heading(packages, fragment_date))}-{UUID(fragment_id).hex}"


def _validated_new_fragment_inputs(
    path: Path,
    packages: list[dict[str, str]],
    fragment_date: str,
    fragment_id: str,
) -> tuple[list[dict[str, str]], str, str]:
    """Validate creation inputs through the same sink rules as fragments."""
    validated_id = _validate_fragment_id(path, fragment_id)
    try:
        parsed_date = date.fromisoformat(fragment_date)
    except ValueError as exc:
        raise _fragment_error(path, "date", "real ISO YYYY-MM-DD calendar date") from exc
    validated_packages = _validate_packages(path, packages)
    return validated_packages, parsed_date.isoformat(), validated_id


def _render_fragment_source(
    *,
    fragment_id: str,
    anchor: str,
    fragment_date: str,
    packages: list[dict[str, str]],
    highlights: list[str],
) -> str:
    """Render one new fragment source record."""
    lines = [
        "+++",
        "schema = 1",
        f'id = "{fragment_id}"',
        f'anchor = "{anchor}"',
        f"date = {fragment_date}",
    ]
    for package in packages:
        lines.extend([
            "[[packages]]",
            f'name = "{package["name"]}"',
            f'version = "{package["version"]}"',
        ])
    lines.extend(["+++", "## Highlights"])
    lines.extend(f"- {highlight}" for highlight in highlights)
    return "\n".join(lines) + "\n"


def create_fragment(
    directory: Path,
    *,
    packages: list[dict[str, str]],
    fragment_date: str,
    highlights: list[str],
    fragment_id: str | None = None,
) -> Path:
    """Create one changelog fragment and return its path.

    The anchor is derived only from this fragment's packages, date and UUID.
    No sibling fragment is read or enumerated, so concurrent creators do not
    race on a shared slug lookup.
    """
    if not highlights or any(not isinstance(item, str) or not item.strip() for item in highlights):
        preview = directory / f"{fragment_id or 'new-fragment'}.md"
        raise _fragment_error(preview, "Highlights", "one or more highlight bullets")
    fragment_id = fragment_id or str(uuid4())
    path = directory / f"{fragment_id}.md"
    validated_packages, validated_date, validated_id = _validated_new_fragment_inputs(
        path, packages, fragment_date, fragment_id
    )
    anchor = _compose_fragment_anchor(validated_packages, validated_date, validated_id)
    text = _render_fragment_source(
        fragment_id=validated_id,
        anchor=anchor,
        fragment_date=validated_date,
        packages=validated_packages,
        highlights=[item.strip() for item in highlights],
    )
    directory.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text)
    except FileExistsError as exc:
        raise _fragment_error(path, "id", "new fragment path must not already exist") from exc
    return path


def _validate_fragment_body(path: Path, body: str) -> dict[str, list[str]]:
    """Validate fragment Markdown sections and return their exact lines."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        heading = _FRAGMENT_SECTION_RE.match(line)
        if heading is not None:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if level == 2 and _parse_release_identity(title) is not None:
                raise _fragment_error(path, "body", "no release-level heading")
            if level != 2:
                raise _fragment_error(path, "body", "section headings at ## only")
            if title not in _FRAGMENT_SECTIONS:
                raise _fragment_error(path, "body", "known changelog section name")
            if title in sections:
                raise _fragment_error(path, title, "section appears once")
            sections[title] = []
            current = title
            continue
        if current is not None:
            sections[current].append(line)
    if "Highlights" not in sections:
        raise _fragment_error(path, "Highlights", "non-empty Highlights section")
    if not any(_FRAGMENT_BULLET_RE.match(line) for line in sections["Highlights"]):
        raise _fragment_error(path, "Highlights", "non-empty Highlights section")
    return sections


def _check_bundle_ready_bytes(path: Path, data: bytes) -> None:
    """Refuse raw fragment bytes that would not bundle unchanged under ADR-0143 D4.

    Called for every loose fragment as part of AC-B2a: a BOM, a CR, non-UTF-8
    bytes, a missing final LF, or a line equal to the bundle separator makes the
    fragment unbundleable and must be caught at validation time.
    """
    if data[:3] == b"\xef\xbb\xbf":
        raise _fragment_error(path, "encoding", "no byte-order mark (BOM)")
    if b"\r" in data:
        raise _fragment_error(path, "line endings", "LF-only; no CR allowed")
    if not data.endswith(b"\n"):
        raise _fragment_error(path, "fragment", "must end with a final LF")
    # Non-UTF-8 is caught later when we decode; a separator-line check is in
    # _parse_validated_fragment once we have text.


def _read_fragment_text(path: Path, safety: ModuleType | None = None) -> str:
    """Read one fragment through the blessed confined-file helper.

    ``safety`` is the already-loaded file-safety module for the current
    projection.  When absent the helper is loaded fresh, which keeps direct
    callers working without a projection context.  Within a projection, the
    caller supplies the handle loaded once by ``collect_validated_fragments``
    so that every confined read in the projection shares one module load.
    """
    fs = safety if safety is not None else _file_safety()
    try:
        data = fs.read_confined_regular_file(
            path.parent, path, max_bytes=MAX_FRAGMENT_BYTES
        )
    except fs.UnsafeContentError as exc:
        field = getattr(exc, "budget", None) or "path"
        raise _fragment_error(path, str(field), "confined regular fragment file") from exc
    _check_bundle_ready_bytes(path, data)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _fragment_error(path, "encoding", "UTF-8 text") from exc


def _parse_validated_fragment(
    path: Path, text: str, *, check_stem: bool = True
) -> ValidatedFragment:
    """Validate already-read fragment source text.

    When ``check_stem`` is False (bundle records), the filename stem is not
    compared to the envelope id — the record lives inside a part, not as a
    standalone file whose name carries identity.
    """
    # AC-B2a: no line may equal the bundle separator.
    for raw_line in text.splitlines():
        if raw_line == BUNDLE_SEPARATOR_LINE:
            raise _fragment_error(
                path, "body", f"no line may equal the bundle separator {BUNDLE_SEPARATOR_LINE!r}"
            )
    front_matter, body = _split_fragment_source(path, text)
    data = _parse_fragment_toml(path, front_matter)
    _require_fragment_fields(path, data)
    fragment_id = _validate_fragment_id(path, data["id"], check_stem=check_stem)
    packages = _validate_packages(path, data["packages"])
    fragment_date = data["date"].isoformat()
    expected_anchor = _compose_fragment_anchor(packages, fragment_date, fragment_id)
    if data["anchor"] != expected_anchor:
        raise _fragment_error(path, "anchor", f"recomputed anchor {expected_anchor}")
    sections = _validate_fragment_body(path, body)
    return ValidatedFragment(
        path=path,
        schema=data["schema"],
        id=fragment_id,
        anchor=data["anchor"],
        date=fragment_date,
        packages=packages,
        sections=sections,
    )


def _run_git(cwd: Path, *args: str) -> _GitResult:
    """Run one Git command for identity validation.

    A ``FileNotFoundError`` from subprocess.run means either the ``cwd`` does
    not exist (caller should guarantee it does) or git is not installed; both
    are propagated to the caller rather than silently mapped to "not a repo",
    which would disable identity enforcement when git is missing (fail-open).
    """
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return _GitResult(completed.returncode, completed.stdout, completed.stderr)


def _single_line_or_refuse(
    path: Path, field: str, expected: str, result: _GitResult
) -> str:
    """Return one Git output line or refuse malformed output."""
    lines = [line for line in result.stdout.splitlines() if line]
    if result.returncode != 0:
        raise _fragment_error(path, field, expected)
    if len(lines) != 1:
        raise _fragment_error(path, field, expected)
    return lines[0]


def _discover_git_repo(path: Path, git_runner=_run_git) -> Path | None:
    """Return the containing Git repo root, or ``None`` outside Git.

    Returns ``None`` when git runs successfully and reports "not a git
    repository" — that is the only case where identity enforcement is skipped.
    A missing git binary (``FileNotFoundError``) is a refusal: enforcement must
    not silently drop when git is unavailable (AC4 fail-closed).
    """
    parent = path.parent
    # Walk up to the first existing ancestor so git can run from a real directory.
    while parent != parent.parent and not parent.exists():
        parent = parent.parent
    if not parent.exists():
        return None
    try:
        result = git_runner(parent, "rev-parse", "--show-toplevel")
    except FileNotFoundError as exc:
        raise FragmentValidationError(
            f"{path}: git executable available: "
            "git is not installed or not on PATH; cannot enforce identity"
        ) from exc
    if result.returncode != 0:
        if "not a git repository" in result.stderr.lower():
            return None
        raise _fragment_error(path, "git repository", "parseable Git repository root")
    lines = [line for line in result.stdout.splitlines() if line]
    if len(lines) != 1:
        raise _fragment_error(path, "git repository", "parseable Git repository root")
    return Path(lines[0]).resolve()


def _parse_changed_paths(
    report_path: Path, stdout: str
) -> tuple[dict[str, tuple[str, str | None]], frozenset[str]]:
    """Parse one ``diff --name-status`` result covering many paths.

    Splitting on newlines is safe here because every path that reaches identity
    enforcement has already passed ``_validate_fragment_id``, so its filename is
    a lowercase UUIDv4 plus ``.md`` and holds nothing Git would quote.
    """
    statuses: dict[str, tuple[str, str | None]] = {}
    unattributable: set[str] = set()
    for line in stdout.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        if status == "A" and len(parts) == 2:
            statuses[parts[1]] = ("A", None)
        elif status == "M" and len(parts) == 2:
            statuses[parts[1]] = ("M", parts[1])
        elif status.startswith("R") and len(parts) == 3:
            statuses[parts[2]] = ("R", parts[1])
        elif len(parts) >= 2 and parts[-1]:
            # A status this validator does not model, but the line still names
            # a path, so refuse that path when it is validated.
            unattributable.add(parts[-1])
        else:
            # No path to attribute the line to, so the whole result is unusable
            # and no per-path refusal can be honest about it.
            raise _fragment_error(
                report_path, "changed path", "parseable Git changed-path status"
            )
    return statuses, frozenset(unattributable)


def _classify_fragment_path(
    path: Path, context: _MergeBaseContext, relative: str
) -> tuple[str, str | None]:
    """Classify one fragment against the pass-wide merge-base maps."""
    if relative in context.unattributable:
        raise _fragment_error(path, "changed path", "parseable Git changed-path status")
    entry = context.statuses.get(relative)
    if entry is not None:
        return entry
    return ("tracked", relative) if relative in context.tracked else ("A", None)


def _base_blob_text(path: Path, *, git_runner=_run_git) -> str | None:
    """Return this path's merge-base blob text when a PR base is available."""
    repo = _discover_git_repo(path, git_runner)
    if repo is None:
        return None
    try:
        relative = path.resolve().relative_to(repo).as_posix()
    except ValueError as exc:
        raise _fragment_error(path, "git repository", "path inside Git repository") from exc
    merge_base = git_runner(repo, "merge-base", "origin/main", "HEAD")
    if merge_base.returncode != 0:
        # Exit 1 with "no merge base" means no common ancestor — valid orphan
        # or detached-HEAD case; return None so callers skip the baseline check.
        # Any other non-zero exit (e.g. 128 for a repo or network error) is a
        # genuine failure that must refuse fail-closed, mirroring the dispatch
        # in validate_changelog_cross_form_identity.
        if merge_base.returncode == 1 and "no merge base" in merge_base.stderr.lower():
            return None
        raise FragmentValidationError(
            f"{path}: merge-base: git merge-base failed with exit "
            f"{merge_base.returncode}: {merge_base.stderr.strip()}"
        )
    base = _single_line_or_refuse(
        path,
        "merge base",
        "readable merge base against origin/main",
        merge_base,
    )
    blob = git_runner(repo, "show", f"{base}:{relative}")
    if blob.returncode != 0:
        return None
    return blob.stdout


def _resolve_merge_base_context(
    report_path: Path, pathspec_root: Path, *, git_runner=_run_git
) -> _MergeBaseContext | None:
    """Resolve every pass-wide Git answer at once, or ``None`` outside Git.

    ``pathspec_root`` scopes the changed-path and tracked-path reads: the
    fragment directory for a whole pass, or one file when a caller validates a
    single path. ``report_path`` names the fragment a repository-wide Git
    failure refuses against, so a missing merge base or an unreadable
    changed-path result still reports a path and an expected correction rather
    than an anonymous whole-set error.
    """
    repo = _discover_git_repo(report_path, git_runner)
    if repo is None:
        return None
    merge_base = _single_line_or_refuse(
        report_path,
        "merge base",
        "readable merge base against origin/main",
        git_runner(repo, "merge-base", "origin/main", "HEAD"),
    )
    pathspec = _fragment_relative_path(pathspec_root, repo)
    changed = git_runner(
        repo, "diff", "--name-status", "--find-renames", merge_base, "--", pathspec
    )
    if changed.returncode != 0:
        raise _fragment_error(
            report_path, "changed path", "parseable Git changed-path status"
        )
    statuses, unattributable = _parse_changed_paths(report_path, changed.stdout)
    listed = git_runner(repo, "ls-files", "--", pathspec)
    if listed.returncode != 0:
        raise _fragment_error(
            report_path, "changed path", "parseable Git changed-path status"
        )
    tracked = frozenset(line for line in listed.stdout.splitlines() if line)
    return _MergeBaseContext(
        repo=repo,
        merge_base=merge_base,
        statuses=statuses,
        tracked=tracked,
        unattributable=unattributable,
    )


def _fragment_relative_path(path: Path, repo: Path) -> str:
    """Return this fragment's repository-relative POSIX path."""
    try:
        return path.resolve().relative_to(repo).as_posix()
    except ValueError as exc:
        raise _fragment_error(
            path, "git repository", "fragment path inside Git repository"
        ) from exc


def _base_fragment_record(
    path: Path, context: _MergeBaseContext, base_relative: str, *, git_runner=_run_git
) -> ValidatedFragment:
    """Parse the merge-base blob behind a modified or renamed fragment."""
    base = git_runner(context.repo, "show", f"{context.merge_base}:{base_relative}")
    if base.returncode != 0:
        raise _fragment_error(
            path, "base blob", "readable base blob for modified or renamed fragment"
        )
    return _parse_validated_fragment(context.repo / base_relative, base.stdout)


def _enforce_committed_identity(
    path: Path,
    current: ValidatedFragment,
    context: _MergeBaseContext,
    *,
    git_runner=_run_git,
) -> None:
    """Refuse edits to published identity fields present at the merge base."""
    relative = _fragment_relative_path(path, context.repo)
    status, base_relative = _classify_fragment_path(path, context, relative)
    if status == "A":
        # Not present at the merge base, so it has no published identity yet.
        return
    if status == "tracked":
        # Git reports no difference against the merge base, so this file is the
        # published bytes. Its identity fields cannot have moved, and fetching
        # the blob to compare them against themselves is the whole fan-out.
        return
    assert base_relative is not None
    base = _base_fragment_record(path, context, base_relative, git_runner=git_runner)
    for field in ("packages", "date", "id"):
        if getattr(current, field) != getattr(base, field):
            raise _fragment_error(path, field, "must not change after merge")


def validate_fragment(
    path: Path,
    seen_ids: set[str] | None = None,
    *,
    enforce_immutability: bool = True,
    git_runner=_run_git,
    merge_base_context: _MergeBaseContext | None = None,
    safety: ModuleType | None = None,
) -> ValidatedFragment:
    """Validate one fragment source file.

    ``merge_base_context`` lets a caller validating many fragments resolve the
    repository root and merge base once. Omitting it keeps this function usable
    on a single path, which resolves its own context.

    ``safety`` is the already-loaded file-safety module for the current
    projection.  When absent the helper is loaded fresh, keeping direct callers
    working without a projection context.  Within a projection,
    ``collect_validated_fragments`` supplies the handle it loaded once so that
    every confined read shares one module load.
    """
    text = _read_fragment_text(path, safety)
    record = _parse_validated_fragment(path, text)
    if seen_ids is not None:
        if record.id in seen_ids:
            raise _fragment_error(path, "id", "unique fragment id")
        seen_ids.add(record.id)
    if enforce_immutability:
        context = merge_base_context
        if context is None:
            context = _resolve_merge_base_context(path, path, git_runner=git_runner)
        if context is not None:
            _enforce_committed_identity(path, record, context, git_runner=git_runner)
    return record


def _unsafe_entry_path(directory: Path, error: Exception) -> Path:
    """Return the most specific unsafe path the file-safety error names."""
    relative = getattr(error, "path", None)
    if relative is None:
        message = str(error)
        if ": " in message:
            relative = message.rsplit(": ", 1)[1]
    return directory / relative if relative else directory


def validate_fragments(directory: Path) -> list[ValidatedFragment]:
    """Validate every direct child fragment in a bounded fragment directory."""
    return collect_validated_fragments(directory)


def collect_validated_fragments(
    directory: Path,
    *,
    enumerator=None,
    git_runner=_run_git,
    safety: ModuleType | None = None,
) -> list[ValidatedFragment]:
    """Collect validated fragments from the source boundary in enumerated order."""
    if safety is None:
        safety = _file_safety()
    if enumerator is None:
        try:
            directories = safety.list_confined_directories(directory, directory)
            if directories:
                raise _fragment_error(
                    directories[0], "path", "bounded direct regular fragment files"
                )
        except FragmentValidationError:
            raise
        except safety.UnsafeContentError as exc:
            path = _unsafe_entry_path(directory, exc)
            raise _fragment_error(path, "path", "bounded direct regular fragment files") from exc
        try:
            paths = safety.list_confined_regular_files(
                directory,
                directory,
                max_entries=MAX_FRAGMENT_DIR_ENTRIES,
                max_files=MAX_FRAGMENT_FILES,
                max_depth=MAX_FRAGMENT_DEPTH,
            )
        except safety.UnsafeContentError as exc:
            field = getattr(exc, "budget", None) or "path"
            path = _unsafe_entry_path(directory, exc)
            raise _fragment_error(
                path, str(field), "bounded direct regular fragment files"
            ) from exc
    else:
        paths = list(enumerator(directory))
    seen_ids: set[str] = set()
    ordered = list(paths)
    context = (
        _resolve_merge_base_context(ordered[0], directory, git_runner=git_runner)
        if ordered
        else None
    )
    return [
        validate_fragment(
            path,
            seen_ids=seen_ids,
            git_runner=git_runner,
            merge_base_context=context,
            safety=safety,
        )
        for path in ordered
    ]


def _normalize_released_versions(
    released_versions,
) -> dict[str, set[str]]:
    """Validate the explicit released-version inventory."""
    normalized: dict[str, set[str]] = {}
    source = Path("<released-versions>")
    if not isinstance(released_versions, dict):
        raise _fragment_error(source, "released_versions", "package version inventory")
    for package_name, versions in released_versions.items():
        if (
            not isinstance(package_name, str)
            or _PACKAGE_NAME_RE.fullmatch(package_name) is None
        ):
            raise _fragment_error(
                source,
                str(package_name),
                "[A-Za-z0-9][A-Za-z0-9._-]*",
            )
        if isinstance(versions, (str, bytes)) or not hasattr(versions, "__iter__"):
            raise _fragment_error(
                source, package_name, "iterable released package versions"
            )
        normalized[package_name] = set()
        for version in versions:
            if (
                not isinstance(version, str)
                or _PACKAGE_VERSION_RE.fullmatch(version) is None
            ):
                raise _fragment_error(
                    source,
                    package_name,
                    "[A-Za-z0-9][A-Za-z0-9._+-]*",
                )
            normalized[package_name].add(version)
    return normalized


def is_fragment_released(
    fragment: ValidatedFragment, released_versions
) -> bool:
    """Return whether every package in `fragment` is in the release inventory."""
    inventory = _normalize_released_versions(released_versions)
    return _fragment_in_released_inventory(fragment, inventory)


def _fragment_in_released_inventory(
    fragment: ValidatedFragment, inventory: dict[str, set[str]]
) -> bool:
    """Return whether one fragment is released against a normalized inventory."""
    return all(
        package["version"] in inventory.get(package["name"], set())
        for package in fragment.packages
    )


def _ordered_fragments(
    fragments: list[ValidatedFragment], *, sort_fragments: bool
) -> list[ValidatedFragment]:
    """Apply the canonical changelog ordering when requested."""
    if not sort_fragments:
        return list(fragments)
    return sorted(
        fragments,
        key=lambda fragment: (
            -date.fromisoformat(fragment.date).toordinal(),
            fragment.id,
        ),
    )


def _serialized_fragment_update(
    fragment: ValidatedFragment, *, heading_level: int = 2
) -> str:
    """Serialize one validated fragment into the deterministic complete view."""
    heading = _fragment_heading(fragment.packages, fragment.date)
    update_heading = "#" * heading_level
    section_heading = "#" * (heading_level + 1)
    lines = [f'<a id="{fragment.anchor}"></a>', f"{update_heading} {heading}"]
    for section, body_lines in fragment.sections.items():
        lines.append("")
        lines.append(f"{section_heading} {section}")
        lines.extend(body_lines)
    return "\n".join(lines).rstrip() + "\n"


def assemble_changelog(
    baseline: str,
    fragments: list[ValidatedFragment],
    *,
    sort_fragments: bool = True,
    released_versions=None,
) -> str:
    """Return the complete changelog from baseline plus fragment records."""
    ordered = _ordered_fragments(fragments, sort_fragments=sort_fragments)
    if released_versions is None:
        pending: list[ValidatedFragment] = []
        released = ordered
    else:
        inventory = _normalize_released_versions(released_versions)
        pending = []
        released = []
        for fragment in ordered:
            if _fragment_in_released_inventory(fragment, inventory):
                released.append(fragment)
            else:
                pending.append(fragment)
    output = baseline.rstrip() + "\n"
    if pending:
        output += "\n## [Unreleased]\n\n"
        output += "\n".join(
            _serialized_fragment_update(fragment, heading_level=3)
            for fragment in pending
        )
    if released:
        output += "\n"
        output += "\n".join(
            _serialized_fragment_update(fragment) for fragment in released
        )
    return output


def _fragment_highlight_sources(fragment: ValidatedFragment) -> list[str]:
    """Return exact Highlights bullet sources from one fragment."""
    sources: list[str] = []
    for line in fragment.sections["Highlights"]:
        bullet = _FRAGMENT_BULLET_RE.match(line)
        if bullet is not None:
            sources.append(bullet.group(1))
    return sources


def project_fragment_now_highlights(
    fragments: list[ValidatedFragment], released_versions
) -> dict:
    """Project fragment-backed released Highlights into the `/now/` payload."""
    inventory = _normalize_released_versions(released_versions)
    released = [
        fragment
        for fragment in _ordered_fragments(fragments, sort_fragments=True)
        if _fragment_in_released_inventory(fragment, inventory)
    ]
    return {
        "schemaVersion": 1,
        "groups": [
            {
                "packages": fragment.packages,
                "date": fragment.date,
                "heading": _fragment_heading(fragment.packages, fragment.date),
                "changelogAnchor": fragment.anchor,
                "highlights": [
                    {"source": source, "segments": highlight_segments(source)}
                    for source in _fragment_highlight_sources(fragment)
                ],
            }
            for fragment in released
        ],
    }


def _historical_release_sections(text: str) -> list[tuple[str, str]]:
    """Return versioned release sections as ``(heading, exact_source)``."""
    lines = text.splitlines(keepends=True)
    starts: list[tuple[int, str]] = []
    heading_lines: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        match = _CHANGELOG_HEADING_RE.match(line.rstrip("\n"))
        if match is None:
            continue
        level = len(match.group(1))
        title = match.group(2).strip()
        heading_lines.append((index, level, title))
        if level == 2 and _parse_release_identity(title) is not None:
            starts.append((index, title))
    sections: list[tuple[str, str]] = []
    for start, title in starts:
        end = len(lines)
        for index, level, _title in heading_lines:
            if index > start and level <= 2:
                end = index
                break
        sections.append((title, "".join(lines[start:end])))
    return sections


def validate_historical_changelog_baseline(
    baseline: Path, *, git_runner=_run_git
) -> None:
    """Refuse edits to historical release headings or section bodies.

    If the merge base holds the file but the working tree does not, refuses
    with a message naming the baseline path and the expected correction.
    If neither the merge base nor the working tree has the file, returns
    silently (pre-cutover repository state).
    """
    base_text = _base_blob_text(baseline, git_runner=git_runner)
    if base_text is None:
        # Neither merge base has the file nor could we resolve a base —
        # pre-cutover state or orphan branch; skip the baseline check.
        return
    if not baseline.exists():
        # Merge base has the file; working tree does not — the frozen baseline
        # has been deleted, which the spec forbids.
        raise _fragment_error(
            baseline,
            "frozen historical changelog",
            "restore docs/product/changelog.md; deleting the frozen baseline is not allowed",
        )
    current_text = baseline.read_text(encoding="utf-8")
    if current_text == base_text:
        return
    base_sections = _historical_release_sections(base_text)
    current_sections = _historical_release_sections(current_text)
    if len(base_sections) != len(current_sections):
        heading = (
            base_sections[0][0]
            if len(current_sections) < len(base_sections)
            else current_sections[0][0]
        )
        raise _fragment_error(
            baseline,
            heading,
            "historical release section unchanged; add a changelog fragment",
        )
    for (base_heading, base_section), (current_heading, current_section) in zip(
        base_sections, current_sections, strict=True
    ):
        if base_heading != current_heading:
            raise _fragment_error(
                baseline,
                base_heading,
                "historical release heading unchanged; add a changelog fragment",
            )
        if base_section != current_section:
            raise _fragment_error(
                baseline,
                base_heading,
                "historical release section unchanged; add a changelog fragment",
            )


def render_complete_changelog(
    *,
    baseline: Path = Path("docs/product/changelog.md"),
    fragments: Path = Path("docs/product/changelog.d"),
) -> str:
    """Render frozen history plus every record, in either storage form, as one view.

    Reads through the one reader, so bundled records render exactly as their
    fragments did (ADR-0143 D10).
    """
    validate_historical_changelog_baseline(baseline)
    baseline_text = baseline.read_text(encoding="utf-8")
    loose, bundled = collect_changelog_records(fragment_dir=fragments)
    return assemble_changelog(baseline_text, [*loose, *bundled])


def render_changelog_to_output(
    output: Path,
    *,
    baseline: Path = Path("docs/product/changelog.md"),
    fragments: Path = Path("docs/product/changelog.d"),
) -> None:
    """Atomically publish the complete changelog after all validation passes."""
    rendered = render_complete_changelog(baseline=baseline, fragments=fragments)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(rendered)
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()


# ---------------------------------------------------------------------------
# Released changelog Highlights → the public /now/ projection.
#
# `spec/site-now-surface`. The only content source is an optional `Highlights`
# subsection of an existing `docs/product/changelog.md` release entry. Two rules
# make an entry eligible, and both are structural rather than textual:
#
#   1. it carries a package/version identity AND a release date, and
#   2. it is not beneath an `[Unreleased]` heading.
#
# Rule 2 is relative, not positional. `changelog.md` currently holds three
# separate `## [Unreleased]` regions, and the newest release-shaped entries are
# nested *inside* the first one as `###` children. A date beneath `Unreleased`
# does not make an entry released — the spec is explicit that Unreleased content
# never projects "even if they contain Highlights" — so eligibility has to be
# decided by enclosing structure. An `Unreleased` heading at level N opens a
# region that every following heading deeper than N belongs to; the region ends
# at the next heading of level N or shallower.
#
# The projection is pure: same source bytes in, same JSON out, no clock, no
# network, no model. `--now-date` supplies the launch day so a fixture can pin
# the window instead of drifting with the calendar.
# ---------------------------------------------------------------------------

_CHANGELOG_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
# Any heading that says "unreleased" and is not itself a release entry opens an
# Unreleased region. Deliberately broad, and it FAILS CLOSED.
#
# Three narrower rules were tried and each leaked. An exact `^\[?unreleased\]?$`
# anchor missed `## [Unreleased] — 2026-08-18`. Adding `(?:\W|$)` still missed
# `## (Unreleased)`, `## **Unreleased**`, `## _Unreleased_`, `## 🚧 Unreleased`,
# `## — Unreleased —` and `## Next (unreleased)`. Leading-token matching misses
# the last of those. In every miss the region was recorded as RELEASED and every
# dated child beneath it published — and the emitted vocabulary check cannot see
# it, because the leaked bullet need not contain the word "unreleased" at all.
#
# The two error directions are not symmetric. A false positive withholds content
# from `/now/`, which the generation report names out loud and an author fixes by
# rewording a heading. A false negative publishes in-progress work, which the
# spec forbids outright. So this errs toward withholding.
_UNRELEASED_RE = re.compile(r"unreleased", re.IGNORECASE)
# `[core][2.7.4] and [architect][0.14.5] — 2026-08-17` — one entry may release
# several packages at once, so identity is a list, not a scalar.
_RELEASE_PKG_RE = re.compile(r"\[([A-Za-z0-9][A-Za-z0-9._-]*)\]\[([^\]]+)\]")
# The pair must LEAD the heading. Markdown reference links share the `[a][b]`
# shape, so searching anywhere makes ordinary prose look like a release:
# `## Thanks to [everyone][credits] who filed issues` and
# `## Migrating from [v1][v1-docs] to [v2][v2-docs]` each hard-failed the whole
# site build before this was anchored.
_RELEASE_LEAD_RE = re.compile(r"^\[([A-Za-z0-9][A-Za-z0-9._-]*)\]\[([^\]]+)\]")
_RELEASE_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})\s*$")
_HIGHLIGHTS_RE = re.compile(r"^highlights$", re.IGNORECASE)
_BULLET_RE = re.compile(r"^[ \t]*[-*+][ \t]+(.*)$")
# Two orthogonal rules, and conflating them cost a regression each way.
#
# 1. Capture the marker CHARACTER and run LENGTH. A bare `(```|~~~)` closes a
#    ````-fenced block on the ``` inside it, and the trailing markers then
#    restore parity so the unterminated-fence raise never fires — sample content
#    publishes as a real release.
# 2. Keep the leading-whitespace allowance permissive. Tightening it to
#    `^ {0,3}` while fixing (1) lost 4-space-indented fences, so a sample nested
#    under a list item stopped being skipped and its ```bash lines published as
#    highlight prose. Being permissive here fails closed: more content skipped,
#    never less.
_FENCE_RE_CHANGELOG = re.compile(r"^([ \t]*)(`{3,}|~{3,})(.*)$")


# `_backtick_runs` and the run-pairing rule below are COPIED from
# packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py:158
# (`_code_span_ranges`), not imported: tools/ must not couple to a
# content-pinned, independently versioned pack tree. Copied as a run scanner
# plus an interleaved pairing step rather than as one whole-line helper,
# because a whole-line span list cannot express "a comment's interior
# contributes no delimiters" -- see `_strip_changelog_comments`. The pairing
# is also precomputed here instead of probed per run: upstream's probe loop
# rescans on every unmatched run, which is quadratic when many distinct-length
# runs precede a long tail of equal-length ones -- measured 2.25 s against this
# file's 0.06 s on 300 distinct-length runs followed by 120,000 length-1 runs.
def _backtick_runs(line: str) -> list[tuple[int, int]]:
    """Every maximal backtick run on one line, as ``(start, length)``.

    The run scan of lint-spec-status.py's `_code_span_ranges`, split from its
    pairing half so the comment stripper can pair runs as it goes. The scan
    itself is byte-identical to the original.
    """
    runs: list[tuple[int, int]] = []
    index, length = 0, len(line)
    while index < length:
        if line[index] == "`":
            end = index
            while end < length and line[end] == "`":
                end += 1
            runs.append((index, end - index))
            index = end
        else:
            index += 1
    return runs


def _span_splits_a_comment(line: str, span_start: int, span_end: int) -> bool:
    """Does this code span hold a comment opener whose closer is outside it?

    That is the authoring mistake worth reporting: the span swallows the
    `<!--`, so the comment is never stripped and its body publishes. A `<!--`
    fully enclosed with its `-->`, or one with no closer anywhere, is an
    ordinary backticked mention -- the changelog carries many, and reporting
    those would bury the real signal.
    """
    opener = line.find("<!--", span_start, span_end)
    while opener >= 0:
        closer = line.find("-->", opener + len("<!--"))
        if closer >= 0 and closer + len("-->") > span_end:
            return True
        opener = line.find("<!--", opener + len("<!--"), span_end)
    return False


class _StrippedLine(NamedTuple):
    """One changelog line with its real HTML comments removed.

    `masks_split_comment` is the authoring diagnostic: a code span swallowed
    the opener of a comment whose closer sits outside it, so that comment's
    body survives into published copy.
    """

    text: str
    opens_comment: bool
    masks_split_comment: bool


def _strip_changelog_comments(line: str) -> _StrippedLine:
    r"""Strip real HTML comments and report an unclosed opener on this line.

    ONE left-to-right pass in which comment detection and code-span pairing
    interleave; whichever construct starts earlier at the cursor consumes its
    extent. An opener inside a code span is a mention. Once a real opener is
    found, its closer search is code-span blind -- Markdown is not parsed
    inside an HTML comment.

    The interleaving is the correctness argument, and two earlier shapes got it
    wrong in ways worth naming, because both looked right:

    1. Pair over the WHOLE line, then mask openers that fall inside a span. A
       backtick inside one real comment paired with a backtick inside the NEXT
       one; the bogus span covered the second comment's opener, so it read as a
       mention and its body published. Measured leak:
       ``- Ship it <!-- don`t publish --> <!-- TODO: internal `note` -->``.
    2. Same, plus discarding spans that start before the current segment. That
       stops a comment interior CREATING a bogus span, but not from STEALING
       the partner of a later legitimate mention -- the interior still supplies
       a delimiter, one level down. Measured hard failure:
       ``<!-- drop the ` here --> Write `<!--` to mention it`` raised
       "unterminated HTML comment" on a line containing no such thing, failing
       the whole site build.

    Both are the same root cause: filtering the OUTPUT of a whole-line pairing
    cannot express "a comment's interior contributes no delimiters". Only
    interleaving can, because a skipped comment's runs are never examined.

    Linear by construction. `next_same` below is precomputed in one backward
    pass, so pairing is O(1) per run and never rescans -- no quadratic recompute
    (a per-segment re-pair measured 4.6 s on 3,000 inline pairs) and no
    backtracking regex (measured 74 s on a 12 KB backtick run).

    Leftmost-wins, so it is CommonMark-faithful, and that has a consequence:
    an UNBALANCED backtick in prose pairs into a following real comment, so
    that comment's body sits inside a code span, is literal text, and
    publishes. The old whole-line regex stripped it. Rendering stays
    CommonMark, but the pipeline errs toward withholding (see the module note
    on Highlights above), so the third return value reports it rather than
    letting it publish in silence.

    Reported only when the span CUTS A COMMENT IN HALF -- its extent holds a
    `<!--` whose matching `-->` is not also inside it. A fully enclosed
    ``` `<!-- x -->` ``` is an ordinary mention, and so is a `<!--` with no
    closer at all; the changelog is full of both, and flagging them would make
    the diagnostic fire on every correct line.
    """
    runs = _backtick_runs(line)
    # run index -> index of the next run of identical length, or -1.
    next_same: list[int] = [-1] * len(runs)
    latest: dict[int, int] = {}
    for index in range(len(runs) - 1, -1, -1):
        next_same[index] = latest.get(runs[index][1], -1)
        latest[runs[index][1]] = index
    run_at = {start: index for index, (start, _) in enumerate(runs)}

    pieces: list[str] = []
    kept_from = 0
    position = 0
    length = len(line)
    masks_split_comment = False

    while position < length:
        if line.startswith("<!--", position):
            # A real comment: emit what precedes it and skip its whole extent.
            # Its interior is never scanned, so nothing inside it can pair.
            pieces.append(line[kept_from:position])
            closer = line.find("-->", position + len("<!--"))
            if closer < 0:
                return _StrippedLine("".join(pieces), True, masks_split_comment)
            kept_from = closer + len("-->")
            position = kept_from
            continue
        if line[position] == "`":
            # `position` always lands on a run START, never mid-run, so this
            # subscript cannot KeyError: an unpaired run advances to its own
            # end, a paired one to its partner's end, the comment branch to
            # just after `>`, and `+= 1` from a non-backtick -- and a run is
            # maximal, so the character after one is never a backtick.
            index = run_at[position]
            partner = next_same[index]
            if partner < 0:
                # An unpaired run is literal text, not a delimiter.
                position += runs[index][1]
            else:
                # A code span: skip it whole, mention and all.
                span_end = runs[partner][0] + runs[partner][1]
                if not masks_split_comment:
                    masks_split_comment = _span_splits_a_comment(
                        line, position, span_end
                    )
                position = span_end
            continue
        position += 1

    pieces.append(line[kept_from:])
    return _StrippedLine("".join(pieces), False, masks_split_comment)


def _slug_base(text: str) -> str:
    """Reproduce `github-slugger`'s slug for one heading's text.

    Starlight generates heading anchors with `github-slugger`, so the fragment a
    Now source link must point at is decided by that algorithm — not by anything
    this repository chooses. Reimplemented rather than guessed: the accompanying
    construction test asserts this function reproduces every `<h2>` id in the
    emitted changelog page, which is the only evidence that the two agree.
    """
    slug = text.strip().lower()
    # github-slugger strips a fixed control/punctuation set and keeps word
    # characters, spaces and hyphens. Notably `[`, `]`, `.` and the em dash all
    # vanish, while the spaces around a removed em dash each survive as one
    # hyphen — which is why the emitted ids carry a `--`.
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    return slug.replace(" ", "-")


class _Slugger:
    """github-slugger's duplicate handling: the Nth repeat gains a `-N` suffix.

    Load-bearing for correctness, not tidiness. `changelog.md` repeats
    `[core][2.3.0] — 2026-08-07`, so the second occurrence is emitted as
    `core230--2026-08-07-1`. A slug derived from heading text alone would send a
    Now source link to the wrong release.
    """

    def __init__(self) -> None:
        self._seen: dict[str, int] = {}

    def slug(self, text: str) -> str:
        base = _slug_base(text)
        count = self._seen.get(base, 0)
        self._seen[base] = count + 1
        return base if count == 0 else f"{base}-{count}"


def _parse_release_identity(title: str) -> dict | None:
    """Return package/version/date identity for a release heading, else None.

    None means "not a release entry" — an `[Unreleased]` heading, a `### Added`
    group, or prose. A heading that looks like a release but carries a malformed
    date is a source defect and raises, because silently dropping it would
    under-report the launch window.
    """
    if _RELEASE_LEAD_RE.match(title) is None:
        return None
    packages = [
        {"name": name, "version": version}
        for name, version in _RELEASE_PKG_RE.findall(title)
    ]
    # `## [Unreleased][unreleased] — 2026-08-18` is a RELEASE-SHAPED heading that
    # means the opposite: it is the Markdown reference-link form older Keep a
    # Changelog templates ship, and this file still carries the matching
    # `[Unreleased]: https://…compare/v1.0.0...HEAD` definition it pairs with.
    #
    # Returning None hands it to the Unreleased region test, which is the only
    # correct destination. The two alternatives both fail: treating it as a
    # release publishes every dated child beneath it, and letting it reach the
    # date check hard-fails the site build on the undated form.
    #
    # Checked across EVERY pair and BOTH slots. Scoping it to the first pair's
    # name left two live bypasses: `## [agentbundle][unreleased] — 2026-08-18`
    # published its Highlights and rendered the public label
    # "agentbundle unreleased" — a version left as `unreleased` while the number
    # is still being cut is the realistic trigger — and the multi-package form
    # `## [Unreleased][unreleased] and [core][2.7.4] — 2026-08-17`, which is a
    # shape this changelog actually uses, skipped the guard entirely. Neither
    # produced any diagnostic, so the required pin could not see them either.
    #
    # An exact-token test, not a substring one, so `unreleased-tools` and
    # `my-unreleased` keep releasing. The guard this replaced compared through
    # `_UNRELEASED_RE` and died silently when that pattern was broadened to a
    # bare `unreleased` — `.match` against a string starting with `[` can never
    # succeed.
    if any(
        part.casefold() == "unreleased"
        for pkg in packages
        for part in (pkg["name"], pkg["version"])
    ):
        return None
    date_match = _RELEASE_DATE_RE.search(title)
    if date_match is None:
        # Package identity but no trailing date — e.g.
        # `## [pkg][1.0.0] — 2026-08-17 (yanked)`. Returning None here treats it
        # as "not a release", which silently drops its Highlights or donates
        # them to whichever entry happens to be open. Fail closed instead; the
        # real changelog has no such heading (verified), so this can only fire
        # on a genuine authoring mistake.
        raise ValueError(
            "changelog release heading carries a package version but no "
            f"trailing release date: {title!r}"
        )
    year, month, day = (int(g) for g in date_match.groups())
    try:
        # `date()` rather than a 1..31 range check: the range accepts
        # 2026-02-31, which then renders as "31 February 2026" behind an invalid
        # <time datetime>.
        release_date = date(year, month, day)
    except ValueError as exc:
        raise ValueError(
            f"changelog release heading has an impossible date: {title!r}"
        ) from exc
    return {"packages": packages, "date": release_date.isoformat()}


class ChangelogHeading(NamedTuple):
    """One heading this parser recognizes as real, with its source position."""

    lineno: int
    level: int
    title: str


class ParsedChangelog(NamedTuple):
    """Release records plus the authoring problems worth reporting.

    Diagnostics are returned, not stashed on the function: as a function attribute
    they were hidden module state assigned only on the success path, and they
    forced a second parse.
    """

    releases: list[dict]
    diagnostics: dict
    # Every real heading, in source order. Exported because "which `##` lines
    # are real headings" is decided here, by the fence and comment state machine
    # below, and a second scanner that re-derives it drifts: a naive `^## ` sweep
    # of the real file picks up the commented-out `## [1.0.0] — YYYY-MM-DD`
    # release template. A caller needing heading POSITION takes it from here
    # rather than writing that state machine again.
    headings: tuple[ChangelogHeading, ...]


def parse_changelog_releases(text: str) -> ParsedChangelog:
    """Extract every release entry, its optional Highlights, and any diagnostics.

    Releases are source-order records carrying package identity, release date,
    heading text, anchor slug, whether the entry sits beneath `Unreleased`, and
    the Highlights bullets when the entry declares them.
    """
    lines = text.splitlines()
    slugger = _Slugger()
    releases: list[dict] = []

    # (level, is_unreleased) for every heading currently enclosing this line.
    stack: list[tuple[int, bool]] = []
    current: dict | None = None
    # Heading level of the release entry `current` refers to. Tracked because a
    # release entry's scope has to CLOSE: without it, `current` survives every
    # following non-release heading, and a `### Highlights` under a later
    # `## Notes for maintainers` appends its bullets to the previous release.
    entry_level: int | None = None
    # Level of the Highlights heading whose bullets we are collecting, if any.
    highlights_level: int | None = None
    # Content column of the open Highlights bullet, or None once it has ended.
    # After a blank line CommonMark continues a list item only with text
    # indented to that column; anything shallower ends the item for good. That
    # keeps the rendered changelog's `<a id="..."></a>` anchor before each
    # release out of the previous release's last bullet.
    bullet_column: int | None = None
    blank_after_bullet = False
    in_fence = False
    fence_opened_at: int | None = None
    fence_marker: str | None = None
    in_comment = False
    comment_opened_at: int | None = None
    ambiguous: list[tuple[int, str]] = []
    misplaced: list[tuple[int, int, str]] = []
    split_comments: list[tuple[int, str]] = []
    headings: list[ChangelogHeading] = []

    for lineno, raw in enumerate(lines, start=1):
        # Fenced code wins over comment syntax: `<!--` inside a shell sample is
        # sample text, not a comment.
        if in_fence:
            closer = _FENCE_RE_CHANGELOG.match(raw)
            # CommonMark's closer rule has THREE parts, and each missing one was
            # its own fail-open: same marker character, run at least as long as
            # the opener, and nothing but whitespace after the run. Without the
            # third, ```` ```bash ```` closes a ```` ``` ```` block, the sample's
            # release heading becomes a real entry, and the two trailing markers
            # restore parity so the unterminated-fence raise never fires.
            if (
                closer is not None
                and fence_marker is not None
                and closer.group(2)[0] == fence_marker[0]
                and len(closer.group(2)) >= len(fence_marker)
                and closer.group(3).strip() == ""
            ):
                in_fence = False
                fence_opened_at = None
                fence_marker = None
            # A `#` inside a fenced block is shell syntax, not a heading, and a
            # `-` inside one is not a bullet.
            continue

        # HTML comments must be skipped, not merely ignored as unmatched text.
        # `changelog.md` ships a commented-out `## [1.0.0] — YYYY-MM-DD` release
        # template, and without this a commented-out entry publishes its
        # Highlights — trailing `-->` and all. It also consumes a `_Slugger`
        # slot that `github-slugger` never sees, which would shift every later
        # `-N` suffix and point source links at the wrong release.
        if in_comment:
            # Deliberately code-span blind: Markdown is not parsed inside an
            # HTML comment, so backticks cannot mask its real closer.
            if "-->" not in raw:
                continue
            in_comment = False
            comment_opened_at = None
            raw = raw.split("-->", 1)[1]
        stripped = _strip_changelog_comments(raw)
        raw = stripped.text
        if stripped.masks_split_comment:
            # An unbalanced backtick paired into a real comment, so that
            # comment's body would publish. Rendering stays CommonMark; this
            # reports the authoring mistake instead of shipping it in silence.
            split_comments.append((lineno, lines[lineno - 1].strip()))

        opener = _FENCE_RE_CHANGELOG.match(raw)
        if opener is not None:
            # A fence shallower than the open bullet's content ends that item.
            if bullet_column is not None and len(opener.group(1)) < bullet_column:
                bullet_column = None
            # A `<!--` that left this fence marker behind was in its info string,
            # so it is sample text rather than cross-line comment state.
            # The opener is matched LOOSELY on indentation. A fence indented four
            # spaces is the ordinary shape inside a list item, and tightening
            # this to `^ {0,3}` while fixing the closer rule regressed those into
            # published copy — literal backticks and sample lines reaching the
            # public page. For this parser a loose opener fails closed (more
            # content skipped) and a strict closer fails closed (the fence stays
            # open, and if it never closes the raise below fires).
            in_fence = True
            fence_opened_at = lineno
            fence_marker = opener.group(2)
            continue

        if stripped.opens_comment:
            in_comment = True
            comment_opened_at = lineno
            # Deliberate divergence from lint-spec-status.py: this builder does
            # not treat an unterminated real opener as literal text. The final
            # raise prevents one typo from silently swallowing later releases.

        heading = _CHANGELOG_HEADING_RE.match(raw)
        if heading is None:
            if highlights_level is not None and current is not None:
                bullet = _BULLET_RE.match(raw)
                if bullet is not None:
                    body = bullet.group(1).strip()
                    if body:
                        current["highlights"].append(body)
                    bullet_column = bullet.start(1) if body else None
                    blank_after_bullet = False
                elif not raw.strip():
                    blank_after_bullet = True
                elif bullet_column is None:
                    pass
                elif blank_after_bullet and len(raw) - len(raw.lstrip()) < bullet_column:
                    # A paragraph or HTML after the list ends the item.
                    bullet_column = None
                else:
                    blank_after_bullet = False
                    # A continuation line of the previous bullet: changelog
                    # bullets wrap, and dropping the tail would truncate copy
                    # mid-sentence on the public page.
                    current["highlights"][-1] += " " + raw.strip()
            continue

        level = len(heading.group(1))
        title = heading.group(2).strip()
        slug = slugger.slug(title)
        # Recorded here, before any routing decision below, so the index covers
        # every real heading and not merely the ones that become releases.
        headings.append(ChangelogHeading(lineno, level, title))

        while stack and stack[-1][0] >= level:
            stack.pop()
        bullet_column = None
        blank_after_bullet = False
        if highlights_level is not None and level <= highlights_level:
            highlights_level = None
        # A heading at or above the open entry's level ends that entry, whatever
        # it is. `### Added` under `## [pkg][1.0.0]` is deeper and leaves the
        # entry open, which is correct; `## Notes for maintainers` is a sibling
        # and closes it.
        if entry_level is not None and level <= entry_level:
            current = None
            entry_level = None

        beneath_unreleased = any(is_unreleased for _, is_unreleased in stack)

        identity = _parse_release_identity(title)

        # Release identity is decided FIRST. A release heading is never an
        # Unreleased region opener, so a package literally named `unreleased-foo`
        # cannot suppress its own entry.
        if identity is None and _UNRELEASED_RE.search(title):
            stack.append((level, True))
            current = None
            entry_level = None
            if title.strip().strip("[]").casefold() != "unreleased":
                # A non-canonical opener. Honoured — nothing beneath it publishes
                # — but reported, so an author whose section stopped publishing
                # can see which heading did it.
                ambiguous.append((lineno, title))
            continue

        if identity is not None:
            current = {
                "packages": identity["packages"],
                "date": identity["date"],
                "heading": title,
                "anchor": slug,
                "unreleased": beneath_unreleased,
                "highlights": [],
            }
            entry_level = level
            releases.append(current)
            stack.append((level, False))
            continue

        # A `Highlights` heading counts only as the entry's IMMEDIATE child. At
        # any other depth it belongs to something else, and attaching its
        # bullets to the nearest open release publishes copy under a release
        # that does not claim it.
        if _HIGHLIGHTS_RE.match(title):
            if entry_level is not None and level == entry_level + 1:
                highlights_level = level
            else:
                # Refused — and silently so without this. A `#### Highlights`
                # under `### Changed` is the second-likeliest authoring mistake
                # and produced output identical to writing nothing.
                misplaced.append((lineno, level, title))
        stack.append((level, False))

    if in_fence:
        # One stray fence would otherwise swallow every release after it, and
        # the drift gate cannot see the loss because expected and committed
        # values come from this same parser.
        raise ValueError(
            "changelog has an unterminated code fence opened at line "
            f"{fence_opened_at}; every release after it would be ignored"
        )
    if in_comment:
        raise ValueError(
            "changelog has an unterminated HTML comment opened at line "
            f"{comment_opened_at}; every release after it would be ignored"
        )

    return ParsedChangelog(
        releases=releases,
        diagnostics={
            "withheld_unreleased": [
                (r["heading"], len(r["highlights"]))
                for r in releases
                if r["unreleased"] and r["highlights"]
            ],
            "misplaced_highlights": misplaced,
            "unreleased_regions": ambiguous,
            "code_span_split_comments": split_comments,
        },
        headings=tuple(headings),
    )


_INLINE_MD_RE = re.compile(r"\*\*(.+?)\*\*|`(.+?)`", re.DOTALL)


def highlight_segments(bullet: str) -> list[dict]:
    """Split one Highlights bullet into typed render segments.

    Changelog bullets are Markdown, and the Now renderer must not receive raw
    Markdown (it would print literal asterisks) nor a raw HTML string (it would
    hand an authored file an injection seam into a public page). Segments keep
    the emphasis the house style relies on — `**Lead.** Body` — while leaving
    escaping to the template, which escapes text nodes by default.

    Only the two inline forms the changelog actually uses are recognised. An
    unsupported form stays literal rather than being silently dropped, so the
    text on the page is never less than what the source says.
    """
    segments: list[dict] = []
    cursor = 0
    for match in _INLINE_MD_RE.finditer(bullet):
        if match.start() > cursor:
            segments.append({"type": "text", "value": bullet[cursor:match.start()]})
        strong, code = match.group(1), match.group(2)
        if strong is not None:
            segments.append({"type": "strong", "value": strong})
        else:
            segments.append({"type": "code", "value": code})
        cursor = match.end()
    if cursor < len(bullet):
        segments.append({"type": "text", "value": bullet[cursor:]})
    return segments


def launch_window(end_date: str, days: int = NOW_WINDOW_DAYS) -> tuple[str, str]:
    """Inclusive [start, end] ISO dates for the `days`-long launch-seed window.

    Sole caller is the construction test that pins the launch seed's released
    entries. Deliberately not called by the generator — see below.

    The window is an AUTHORING rule, not a render filter. It decides which
    released entries should have gained a `Highlights` block by launch day; it
    never limits what `/now/` publishes afterwards. Keeping it out of the
    projection is what makes the projection deterministic — a date window
    evaluated at build time would change the page every midnight from unchanged
    source, which the spec forbids.
    """
    end = date.fromisoformat(end_date)
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def project_now_highlights(text: str) -> dict:
    """Project the public `/now/` payload from changelog source.

    Only released entries — versioned, dated, and outside every `Unreleased`
    region — that declare Highlights reach the payload. Groups sort by release
    date descending and preserve source order for equal dates.

    Pure and clock-free: the same source bytes always produce the same payload.
    """
    return _project_parsed(parse_changelog_releases(text))


def _project_parsed(parsed: ParsedChangelog) -> dict:
    """Build the payload from an already-parsed changelog."""
    eligible = [
        r for r in parsed.releases if not r["unreleased"] and r["highlights"]
    ]

    # `sorted` is stable, so equal dates keep source order without a tiebreak
    # key. An index tiebreak would have to be reversed alongside the date and is
    # easy to get backwards; leaning on stability cannot drift.
    ordered = sorted(eligible, key=lambda r: r["date"], reverse=True)

    return {
        "schemaVersion": 1,
        "groups": [
            {
                "packages": r["packages"],
                "date": r["date"],
                "heading": r["heading"],
                "changelogAnchor": r["anchor"],
                "highlights": [
                    {"source": bullet, "segments": highlight_segments(bullet)}
                    for bullet in r["highlights"]
                ],
            }
            for r in ordered
        ],
    }


# ====================================================================
# ADR-0143: Monthly bundle parts, cross-form identity, compact, retract.
# ====================================================================


def _bundle_error(path: Path, field: str, expected: str) -> FragmentValidationError:
    """Create the standard bundle validation diagnostic."""
    return FragmentValidationError(f"{path}: {field}: expected {expected}")


def _validate_bundle_part_name(part_path: Path, bundle_dir: Path) -> tuple[str, str, str]:
    """Return ``(YYYY, MM, NN)`` or refuse an invalid bundle part name.

    Checks that the name fullmatches ``YYYY-MM-NN.bundle`` with a real month.
    """
    name = part_path.name
    m = _BUNDLE_NAME_RE.fullmatch(name)
    if m is None:
        raise _bundle_error(
            part_path, "name", "YYYY-MM-NN.bundle with a real month and two-digit NN"
        )
    yyyy, mm, nn = m.group(1), m.group(2), m.group(3)
    try:
        date(int(yyyy), int(mm), 1)
    except ValueError as exc:
        raise _bundle_error(
            part_path, "name", "YYYY-MM-NN.bundle with a real month"
        ) from exc
    return yyyy, mm, nn


def _parse_bundle_part(
    path: Path,
    raw_bytes: bytes,
    seen_ids: set[str] | None = None,
    part_month: str | None = None,
) -> list[tuple[bytes, ValidatedFragment]]:
    """Parse one bundle part into a list of (raw_record_bytes, fragment).

    ``seen_ids`` is shared across parts so a duplicate across parts is caught.
    ``part_month`` is the ``YYYY-MM`` derived from the part name for AC-B3.
    Returns tuples of (record_raw_bytes_without_separator, validated_fragment).
    """
    if raw_bytes[:3] == b"\xef\xbb\xbf":
        raise _bundle_error(path, "bundle part", "no byte-order mark (BOM)")
    if b"\r" in raw_bytes:
        raise _bundle_error(path, "bundle part", "LF-only line endings; CR found")
    if not raw_bytes.startswith(BUNDLE_SEPARATOR_BYTES):
        raise _bundle_error(
            path, "record 0", f"must start with separator {BUNDLE_SEPARATOR_LINE!r}"
        )
    # Split on separator; parts[0] is the empty prefix before the first separator.
    parts = raw_bytes.split(BUNDLE_SEPARATOR_BYTES)
    record_bytes_list = parts[1:]  # skip the leading empty string
    if not record_bytes_list:
        raise _bundle_error(path, "bundle part", "must contain at least one record")
    results: list[tuple[bytes, ValidatedFragment]] = []
    prev_key: tuple[int, str] | None = None
    for idx, record_bytes in enumerate(record_bytes_list):
        record_label = f"record {idx}"
        if not record_bytes:
            raise _bundle_error(path, record_label, "empty record")
        if not record_bytes.endswith(b"\n"):
            raise _bundle_error(path, record_label, "record must end with LF")
        # AC-B2: trailing bytes — any bytes after the record body's final LF
        # are refused. A well-formed record (authored by create_fragment or
        # compact) ends with exactly one LF; a double-LF at the end means
        # extra bytes were appended after the body.
        if len(record_bytes) >= 2 and record_bytes[-2:] == b"\n\n":
            raise _bundle_error(
                path,
                record_label,
                f"trailing bytes after record body; "
                f"next {BUNDLE_SEPARATOR_LINE!r} separator expected",
            )
        # Decode to text for fragment parsing.
        try:
            text = record_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise _bundle_error(path, record_label, "UTF-8 text") from exc
        # Use a synthetic path that carries the part name and record index.
        synthetic_path = path.with_name(f"{path.name}:record[{idx}]")
        fragment = _parse_validated_fragment(synthetic_path, text, check_stem=False)
        # AC-B3: record date month must match the part month.
        if part_month is not None and not fragment.date.startswith(part_month + "-"):
            raise _bundle_error(
                path,
                record_label,
                f"date {fragment.date!r} must be in part month {part_month}",
            )
        # Duplicate id check across forms.
        if seen_ids is not None:
            if fragment.id in seen_ids:
                err = _bundle_error(path, record_label, f"duplicate id {fragment.id!r}")
                raise DuplicateRecordIdError(str(err), record_id=fragment.id)
            seen_ids.add(fragment.id)
        # Canonical order: date descending then id ascending.
        key = (-date.fromisoformat(fragment.date).toordinal(), fragment.id)
        if prev_key is not None and key <= prev_key:
            raise _bundle_error(
                path, record_label, "records must be in canonical order (date desc, id asc)"
            )
        prev_key = key
        results.append((record_bytes, fragment))
    return results


def _read_bundle_part(
    path: Path, bundle_dir: Path, safety: ModuleType
) -> bytes:
    """Read one bundle part through the blessed confined-file helper."""
    try:
        data = safety.read_confined_regular_file(
            bundle_dir, path, max_bytes=MAX_BUNDLE_BYTES
        )
    except safety.UnsafeContentError as exc:
        field = getattr(exc, "budget", None) or "path"
        raise _bundle_error(path, str(field), "confined regular bundle part file") from exc
    return data


def _collect_bundle_records(
    bundle_dir: Path,
    safety: ModuleType,
    seen_ids: set[str] | None = None,
) -> list[tuple[Path, str, bytes, ValidatedFragment]]:
    """Collect all bundle records from the monthly bundle directory.

    Returns a list of ``(part_path, part_month, raw_record_bytes, fragment)``
    tuples. Validates part names, directory confinement and record contents.
    ``seen_ids`` accumulates ids across calls (shared with fragment collection).
    """
    if not bundle_dir.exists():
        return []
    # Refuse non-regular and unsafe entries.
    try:
        directories = safety.list_confined_directories(bundle_dir, bundle_dir)
        if directories:
            raise _bundle_error(
                directories[0], "path", "bounded direct regular bundle part files"
            )
    except FragmentValidationError:
        raise
    except safety.UnsafeContentError as exc:
        path = _unsafe_entry_path(bundle_dir, exc)
        raise _bundle_error(path, "path", "bounded direct regular bundle part files") from exc
    try:
        part_paths = safety.list_confined_regular_files(
            bundle_dir,
            bundle_dir,
            max_entries=MAX_BUNDLE_DIR_ENTRIES,
            max_files=MAX_BUNDLE_FILES,
            max_depth=MAX_BUNDLE_DEPTH,
        )
    except safety.UnsafeContentError as exc:
        field = getattr(exc, "budget", None) or "path"
        path = _unsafe_entry_path(bundle_dir, exc)
        raise _bundle_error(path, str(field), "bounded direct regular bundle part files") from exc

    # Validate each part name and check for duplicate NNs within a month.
    month_nns: dict[str, set[str]] = {}
    month_parts: dict[str, list[Path]] = {}
    for part_path in part_paths:
        yyyy, mm, nn = _validate_bundle_part_name(part_path, bundle_dir)
        month_key = f"{yyyy}-{mm}"
        if nn in month_nns.get(month_key, set()):
            raise _bundle_error(
                part_path, "name", f"duplicate NN={nn!r} for month {month_key}"
            )
        month_nns.setdefault(month_key, set()).add(nn)
        month_parts.setdefault(month_key, []).append(part_path)

    results: list[tuple[Path, str, bytes, ValidatedFragment]] = []
    for part_paths_for_month in month_parts.values():
        for part_path in sorted(part_paths_for_month):
            month_key = f"{part_path.name[:4]}-{part_path.name[5:7]}"
            raw = _read_bundle_part(part_path, bundle_dir, safety)
            records = _parse_bundle_part(
                part_path, raw, seen_ids=seen_ids, part_month=month_key
            )
            for record_bytes, fragment in records:
                results.append((part_path, month_key, record_bytes, fragment))
    return results


def _read_retraction_list(
    retraction_path: Path, safety: ModuleType
) -> list[dict]:
    """Read and parse the retraction list through the blessed helper.

    Returns a list of retraction entries. Returns empty list when absent.
    """
    if not retraction_path.exists():
        return []
    parent = retraction_path.parent
    try:
        raw = safety.read_confined_regular_file(
            parent, retraction_path, max_bytes=MAX_RETRACTION_BYTES
        )
    except safety.UnsafeContentError as exc:
        field = getattr(exc, "budget", None) or "path"
        raise _bundle_error(
            retraction_path, str(field), "confined regular retraction list file"
        ) from exc
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise _bundle_error(retraction_path, "retraction list", "valid UTF-8 TOML") from exc
    if not isinstance(data, dict):
        raise _bundle_error(retraction_path, "retraction list", "TOML table")
    retractions = data.get("retraction", [])
    if not isinstance(retractions, list):
        raise _bundle_error(retraction_path, "retraction", "array of retraction tables")
    _validate_retraction_list(retraction_path, retractions)
    return retractions


def _validate_retraction_list(path: Path, entries: list) -> None:
    """Validate each retraction entry has required fields and no unknown ones."""
    seen_retraction_ids: set[str] = set()
    for idx, entry in enumerate(entries):
        label = f"retraction[{idx}]"
        if not isinstance(entry, dict):
            raise _bundle_error(path, label, "table")
        for field in entry:
            if field not in _RETRACTION_FIELDS:
                raise _bundle_error(
                    path, label, f"known fields only ({sorted(_RETRACTION_FIELDS)})"
                )
        for field in ("id", "category"):
            if field not in entry:
                raise _bundle_error(path, f"{label}.{field}", "required field")
        entry_id = entry["id"]
        if not isinstance(entry_id, str):
            raise _bundle_error(path, f"{label}.id", "lowercase UUIDv4 string")
        try:
            parsed_uuid = UUID(entry_id, version=4)
        except ValueError as exc:
            raise _bundle_error(path, f"{label}.id", "lowercase UUIDv4 string") from exc
        if parsed_uuid.version != 4 or str(parsed_uuid) != entry_id:
            raise _bundle_error(path, f"{label}.id", "lowercase UUIDv4 string")
        if entry_id in seen_retraction_ids:
            raise _bundle_error(
                path, f"{label}.id",
                f"unique retraction id; {entry_id!r} already listed",
            )
        seen_retraction_ids.add(entry_id)
        category = entry["category"]
        if category not in _RETRACTION_CATEGORIES:
            raise _bundle_error(
                path, f"{label}.category", f"one of {sorted(_RETRACTION_CATEGORIES)}"
            )


def collect_changelog_records(
    *,
    fragment_dir: Path = Path("docs/product/changelog.d"),
    bundle_dir: Path | None = None,
    retraction_path: Path | None = None,
    safety: ModuleType | None = None,
    git_runner=_run_git,
) -> tuple[list[ValidatedFragment], list[ValidatedFragment]]:
    """Return ``(loose_fragments, bundled_records)`` from both storage forms.

    This is the one reader every consumer calls. No consumer may pass a
    substitute enumerator, helper handle or Git runner (AC-B8).

    ``safety`` is loaded once when absent and passed through every confined
    read in this call, per AC-B1. A second call loads it afresh.
    """
    if bundle_dir is None:
        bundle_dir = fragment_dir.parent / "changelog.months"
    if retraction_path is None:
        retraction_path = fragment_dir.parent / "changelog-retractions.toml"
    if not (fragment_dir.exists() or bundle_dir.exists() or retraction_path.exists()):
        # Nothing to read, so no confined read happens and no helper is needed.
        return [], []
    fs = safety if safety is not None else _file_safety()
    seen_ids: set[str] = set()
    # Collect loose fragments. An absent directory holds none; the merge-base
    # comparison still runs against it.
    loose = (
        collect_validated_fragments(fragment_dir, safety=fs, git_runner=git_runner)
        if fragment_dir.exists()
        else []
    )
    for f in loose:
        seen_ids.add(f.id)
    # Collect retracted ids.
    retractions = _read_retraction_list(retraction_path, fs)
    retracted_ids = {e["id"] for e in retractions}
    # Collect bundled records.
    bundle_tuples = _collect_bundle_records(bundle_dir, fs, seen_ids=seen_ids)
    bundled = [fragment for _, _, _, fragment in bundle_tuples]
    _refuse_unsafe_record_set(loose, bundled, retracted_ids, bundle_dir)
    return loose, bundled


def _refuse_unsafe_record_set(
    loose: list[ValidatedFragment],
    bundled: list[ValidatedFragment],
    retracted_ids: set[str],
    bundle_dir: Path,
) -> None:
    """Refuse a record set over the record cap or holding a retracted id.

    Shared by the one reader and by compact's rerun recovery, which collects
    each form separately, so neither path can skip these checks. A record in
    both forms mid-compaction counts once toward the cap.
    """
    # Check total record count cap (AC-B7).
    total = len({record.id for record in [*loose, *bundled]})
    if total > MAX_RECORD_COUNT:
        raise _bundle_error(
            bundle_dir,
            "record count",
            f"at most {MAX_RECORD_COUNT} records across both forms; got {total}",
        )
    # A retracted id must never reappear, so its presence in either form is a
    # refusal rather than something to hide from the output (AC-B4a).
    for record in [*loose, *bundled]:
        if record.id in retracted_ids:
            raise _fragment_error(
                record.path, "id", f"retracted id {record.id!r} absent from every form"
            )


# ---------------------------------------------------------------------------
# Cross-form identity: git object-id comparison for AC-B4/AC-B5.
# ---------------------------------------------------------------------------


def _compute_git_object_id(data: bytes, object_format: str) -> str:
    """Compute the git blob object id for the given bytes.

    ``object_format`` is the output of ``git rev-parse --show-object-format``
    — either ``sha1`` or ``sha256``.
    """
    header = b"blob " + str(len(data)).encode() + b"\0"
    payload = header + data
    if object_format == "sha256":
        return hashlib.sha256(payload).hexdigest()
    # A Git object id, not a security digest; FIPS hosts allow it only so marked.
    return hashlib.sha1(payload, usedforsecurity=False).hexdigest()


def _get_repo_object_format(repo: Path, git_runner=_run_git) -> str:
    """Return the repo's hash algorithm name (``sha1`` or ``sha256``)."""
    result = git_runner(repo, "rev-parse", "--show-object-format")
    if result.returncode != 0:
        return "sha1"  # safe default for old Git versions
    lines = [line for line in result.stdout.splitlines() if line]
    return lines[0].strip() if lines else "sha1"


def _ls_tree_object_ids(
    repo: Path,
    merge_base: str,
    *pathspecs: str,
    git_runner=_run_git,
) -> dict[str, str]:
    """Return a mapping of repo-relative path → blob object id at the merge base.

    Uses ``git ls-tree -r`` which does not read blob contents.
    """
    result = git_runner(repo, "ls-tree", "-r", merge_base, "--", *pathspecs)
    if result.returncode != 0:
        # An absent pathspec returns exit 0 with empty output, so a non-zero
        # exit is a real failure.
        raise FragmentValidationError(
            f"git ls-tree failed for merge base {merge_base!r}: {result.stderr.strip()}"
        )
    mapping: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if not line:
            continue
        # Format: `<mode> <type> <object-id>\t<path>`
        tab = line.find("\t")
        if tab < 0:
            continue
        parts = line[:tab].split()
        if len(parts) != 3:
            continue
        _mode, _type, obj_id = parts
        path_str = line[tab + 1:]
        mapping[path_str] = obj_id
    return mapping


def _git_runner_bytes(repo: Path, *args: str) -> tuple[int, bytes, str]:
    """Run git and return (returncode, stdout_bytes, stderr_text)."""
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    return (
        completed.returncode,
        completed.stdout,
        completed.stderr.decode("utf-8", errors="replace"),
    )


def _read_blob_bytes(
    repo: Path,
    obj_id: str,
    *,
    max_bytes: int,
) -> bytes:
    """Read one blob by object id as raw bytes, with a size check."""
    size_rc, size_out, size_err = _git_runner_bytes(
        repo, "cat-file", "-s", obj_id
    )
    if size_rc != 0:
        raise FragmentValidationError(
            f"git cat-file -s {obj_id!r} failed: {size_err.strip()}"
        )
    try:
        blob_size = int(size_out.strip())
    except ValueError as exc:
        raise FragmentValidationError(
            f"git cat-file -s returned non-integer size for {obj_id!r}"
        ) from exc
    if blob_size > max_bytes:
        raise FragmentValidationError(
            f"merge-base blob {obj_id!r} is {blob_size} bytes; "
            f"maximum is {max_bytes}"
        )
    rc, blob_bytes, err = _git_runner_bytes(repo, "cat-file", "blob", obj_id)
    if rc != 0:
        raise FragmentValidationError(
            f"git cat-file blob {obj_id!r} failed: {err.strip()}"
        )
    return blob_bytes


class _RecordChange:
    """Classification of how one record changed from the merge base."""

    ADDED = "added"        # not in merge base, present now
    UNCHANGED = "unchanged"  # same bytes as merge base
    MODIFIED = "modified"  # different bytes from merge base
    REMOVED = "removed"    # in merge base, absent now


def validate_changelog_cross_form_identity(
    *,
    fragment_dir: Path = Path("docs/product/changelog.d"),
    bundle_dir: Path = Path("docs/product/changelog.months"),
    retraction_path: Path = Path("docs/product/changelog-retractions.toml"),
    git_runner=_run_git,
    safety: ModuleType | None = None,
) -> None:
    """Validate cross-form record identity against the merge base (AC-B4, AC-B5).

    Called by the ``validate`` command. Checks:
    - No duplicate ids across forms.
    - No bundled record modified from its merge-base bytes.
    - No unretracted removal of a bundled record.
    - No new id added directly to a bundle part.
    - Part-adding changes respect the three allowed operations.
    - No change to a fragment's packages, date or id (already done per-fragment).
    - Retraction list is append-only.
    Reads merge-base blobs only when the object id differs from the computed one.
    """
    fs = safety if safety is not None else _file_safety()
    # Resolve the repo root.
    report_path = fragment_dir / "<validate>"
    repo = _discover_git_repo(report_path, git_runner)
    if repo is None:
        return  # Not in a git repo; skip (e.g., direct invocation outside git).
    # Get the merge base.
    mb_result = git_runner(repo, "merge-base", "origin/main", "HEAD")
    if mb_result.returncode != 0:
        # Exit 1 with "no merge base" in stderr means no common ancestor —
        # a valid case for a freshly-detached or orphan branch: skip.
        # Any other non-zero exit (e.g., 128 for a repository or network error)
        # is a genuine failure and must refuse fail-closed.
        if mb_result.returncode == 1 and "no merge base" in mb_result.stderr.lower():
            return
        raise FragmentValidationError(
            f"git merge-base failed with exit {mb_result.returncode}: "
            f"{mb_result.stderr.strip()}"
        )
    mb_lines = [line for line in mb_result.stdout.splitlines() if line]
    if len(mb_lines) != 1:
        raise FragmentValidationError(
            f"git merge-base returned unexpected output: {mb_result.stdout!r}"
        )
    merge_base = mb_lines[0].strip()
    object_format = _get_repo_object_format(repo, git_runner)

    # Get the merge-base tree for all relevant paths.
    frag_rel = _safe_relative(fragment_dir, repo)
    bundle_rel = _safe_relative(bundle_dir, repo)
    retract_rel = _safe_relative(retraction_path, repo)
    base_tree = _ls_tree_object_ids(
        repo, merge_base, frag_rel, bundle_rel, retract_rel, git_runner=git_runner
    )

    # Collect current records.
    loose, _ = collect_changelog_records(
        fragment_dir=fragment_dir,
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
        safety=fs,
        git_runner=git_runner,
    )
    # Also collect raw bundle data for byte comparison.
    seen_ids_all: set[str] = set()
    bundle_tuples = _collect_bundle_records(bundle_dir, fs, seen_ids=seen_ids_all)

    # Collect current retraction list entries.
    retractions = _read_retraction_list(retraction_path, fs)
    retracted_ids = {e["id"] for e in retractions}

    # For each current bundle part, check byte-immutability against merge base.
    for part_path, _part_month, _record_bytes, _fragment in bundle_tuples:
        rel_part = _safe_relative(part_path, repo)
        base_obj_id = base_tree.get(rel_part)
        if base_obj_id is None:
            # This part was added in this change. Records in it must have
            # existed as fragments at the merge base. (Checked later.)
            continue
        # Part exists at the merge base. Its bytes must not have changed,
        # unless it was modified by a retraction.
        # Compute current part's object id.
        part_raw = _read_bundle_part(part_path, bundle_dir, fs)
        current_obj_id = _compute_git_object_id(part_raw, object_format)
        if current_obj_id == base_obj_id:
            continue  # unchanged, no blob read needed
        # Object IDs differ — read the merge-base blob for comparison.
        base_bytes = _read_blob_bytes(repo, base_obj_id, max_bytes=MAX_BUNDLE_BYTES)
        if part_raw == base_bytes:
            continue  # identical bytes despite object-id mismatch (unlikely, but safe)
        # Part was modified. Check each record: it must still be present and
        # unchanged, OR the record must be newly retracted.
        base_records = _parse_bundle_part(part_path, base_bytes)
        current_records = _parse_bundle_part(part_path, part_raw)
        base_by_id = {f.id: rb for rb, f in base_records}
        current_by_id = {f.id: rb for rb, f in current_records}
        for record_id, base_rb in base_by_id.items():
            if record_id in retracted_ids:
                continue  # legitimately retracted
            if record_id not in current_by_id:
                raise FragmentValidationError(
                    f"{part_path}: record {record_id!r}: "
                    "unretracted bundled record removed"
                )
            if current_by_id[record_id] != base_rb:
                raise FragmentValidationError(
                    f"{part_path}: record {record_id!r}: "
                    "bundled record bytes changed"
                )

    # --- AC-B4 deferred check: reconstruct the merge-base record set ---
    #
    # The first loop only covers bundle parts that still exist in the current
    # state.  Parts removed entirely (or when the months directory is gone) are
    # absent from bundle_tuples and were never examined.  Also, a new bundle
    # part (base_obj_id is None in the first loop) requires that every record
    # it carries was already a loose fragment at the merge base — that must be
    # checked here.
    #
    # Build base_frag_ids from filenames in base_tree under changelog.d/.
    # Build base_bundle_ids by reading merge-base blobs for changelog.months/.
    base_frag_ids: set[str] = set()
    base_bundle_ids: set[str] = set()
    # Map record id → raw record bytes and source part path from the merge-base
    # blob-reading path. Used by the AC-B4 moved-bundled-record check below.
    base_bundle_record_bytes: dict[str, bytes] = {}
    base_bundle_record_part: dict[str, Path] = {}

    # Build a quick lookup: repo-relative part path → list of current ids.
    current_bundle_rel_ids: dict[str, set[str]] = {}
    for pp, _, _, ff in bundle_tuples:
        rel = _safe_relative(pp, repo)
        current_bundle_rel_ids.setdefault(rel, set()).add(ff.id)

    frag_prefix = frag_rel.rstrip("/") + "/"
    bundle_prefix = bundle_rel.rstrip("/") + "/"

    for path_str, base_obj in base_tree.items():
        if path_str.startswith(frag_prefix):
            # Fragment id comes from the filename stem.
            stem = Path(path_str).stem
            try:
                parsed = UUID(stem, version=4)
                if str(parsed) == stem:
                    base_frag_ids.add(stem)
            except ValueError:
                pass  # non-UUID filename at merge base; skip
        elif bundle_rel and path_str.startswith(bundle_prefix):
            # Need the record ids inside this bundle part.
            # Optimisation: if the current part has the same object id, its
            # records ARE the merge-base records, so use the already-parsed list.
            current_ids_for_part = current_bundle_rel_ids.get(path_str)
            if current_ids_for_part is not None:
                # Find the actual part path and check its object id.
                current_part_path = None
                for pp2, _, _, _ in bundle_tuples:
                    if _safe_relative(pp2, repo) == path_str:
                        current_part_path = pp2
                        break
                if current_part_path is not None:
                    part_raw2 = _read_bundle_part(current_part_path, bundle_dir, fs)
                    current_obj2 = _compute_git_object_id(part_raw2, object_format)
                    if current_obj2 == base_obj:
                        base_bundle_ids.update(current_ids_for_part)
                        continue
            # Either the part is absent or its bytes differ — read the blob.
            blob_bytes = _read_blob_bytes(repo, base_obj, max_bytes=MAX_BUNDLE_BYTES)
            fake_path = bundle_dir / Path(path_str).name
            try:
                # A fresh id set refuses an id repeated within this one part.
                base_recs = _parse_bundle_part(fake_path, blob_bytes, seen_ids=set())
            except FragmentValidationError as _parse_exc:
                # Malformed merge-base blob cannot be parsed; refuse.
                raise FragmentValidationError(
                    f"{fake_path}: merge-base bundle blob {base_obj!r} "
                    "could not be parsed; cannot verify record identity"
                ) from _parse_exc
            for rb, bf in base_recs:
                base_bundle_ids.add(bf.id)
                # Track raw bytes and source path for the moved-record check.
                base_bundle_record_bytes[bf.id] = rb
                base_bundle_record_part[bf.id] = fake_path

    all_base_ids = base_frag_ids | base_bundle_ids

    # Refusal 1b: a bundled record moved into a new added part with its bytes
    # changed (AC-B4: "a bundled record moved into an added part with its date
    # changed"). The first loop only covers parts that still exist at the same
    # path; records from old parts that are now in a newly-added part slip
    # through without this check.
    for part_path, _part_month, record_bytes, fragment in bundle_tuples:
        rel_part = _safe_relative(part_path, repo)
        if rel_part in base_tree:
            continue  # existing part already covered by the first loop above
        if fragment.id not in base_bundle_record_bytes:
            continue  # record was loose at the merge base, not a bundled record
        if record_bytes != base_bundle_record_bytes[fragment.id]:
            base_src = base_bundle_record_part.get(fragment.id, bundle_dir)
            raise FragmentValidationError(
                f"{part_path}: record {fragment.id!r}: "
                f"bundled record bytes changed; "
                f"merge-base record was in {base_src} (AC-B4)"
            )

    # Current state.
    current_bundled_ids: set[str] = {ff.id for _, _, _, ff in bundle_tuples}
    current_loose_ids: set[str] = {f.id for f in loose}
    current_all_ids = current_bundled_ids | current_loose_ids

    # Is this a part-adding change? Any current bundle part not in base_tree.
    current_bundle_rels: set[str] = {
        _safe_relative(pp, repo) for pp, _, _, _ in bundle_tuples
    }
    is_part_adding = any(rel not in base_tree for rel in current_bundle_rels)

    # Refusal 1: a new id added directly to a part (not at merge base in any form).
    for _, _, _, ff in bundle_tuples:
        if ff.id not in all_base_ids and ff.id not in retracted_ids:
            raise FragmentValidationError(
                f"{ff.path}: record {ff.id!r}: "
                "new id added directly to a bundle part; "
                "new records must be authored as loose fragments first "
                "(AC-B4 D1)"
            )

    # Refusal 2: a merge-base bundled record missing from current forms and
    # not retracted. This covers both individual-record removal and removal
    # of the entire months directory.
    for base_id in base_bundle_ids:
        if base_id not in current_all_ids and base_id not in retracted_ids:
            raise FragmentValidationError(
                f"{bundle_dir}: record {base_id!r}: "
                "merge-base bundled record absent from current forms "
                "and not listed in the retraction list (AC-B4)"
            )

    # Refusal 3: in a part-adding change, a merge-base loose fragment that is
    # not bundled into a new part and not retracted.
    if is_part_adding:
        for base_id in base_frag_ids:
            if base_id not in current_all_ids and base_id not in retracted_ids:
                raise FragmentValidationError(
                    f"{fragment_dir}: record {base_id!r}: "
                    "part-adding change drops a merge-base fragment that is "
                    "not bundled into any new part and not retracted (AC-B4)"
                )

    # Validate retraction list is append-only against merge base.
    retract_rel_str = _safe_relative(retraction_path, repo)
    base_retract_obj = base_tree.get(retract_rel_str)
    if base_retract_obj is not None and not retraction_path.exists():
        # Deleting the list would erase every retraction, letting a retracted
        # record be re-published, so the list itself is append-only (AC-B4a).
        raise _bundle_error(
            retraction_path, "retraction list", "present while the merge base lists retractions"
        )
    if base_retract_obj is not None:
        base_retract_bytes = _read_blob_bytes(
            repo, base_retract_obj, max_bytes=MAX_RETRACTION_BYTES
        )
        try:
            retract_raw = fs.read_confined_regular_file(
                retraction_path.parent, retraction_path, max_bytes=MAX_RETRACTION_BYTES
            )
        except fs.UnsafeContentError as exc:
            field = getattr(exc, "budget", None) or "path"
            raise _bundle_error(
                retraction_path, str(field), "confined regular retraction list file"
            ) from exc
        if not retract_raw.startswith(base_retract_bytes.rstrip(b"\n")):
            # Allow appending only: parse the base list and verify every base
            # entry is still present and byte-identical (same id and category).
            try:
                base_data = tomllib.loads(base_retract_bytes.decode("utf-8"))
                base_entries = base_data.get("retraction", [])
            except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
                # Fix D: a malformed merge-base retraction list cannot be
                # verified, so the check must fail closed rather than silently
                # passing. An attacker who lands malformed TOML on main would
                # otherwise bypass all append-only enforcement.
                raise FragmentValidationError(
                    f"{retraction_path}: retraction list: "
                    "merge-base content is not valid UTF-8 TOML; "
                    "cannot verify append-only invariant"
                ) from exc
            current_by_id = {e["id"]: e for e in retractions if isinstance(e, dict)}
            for base_entry in base_entries:
                if not isinstance(base_entry, dict):
                    continue
                entry_id = base_entry.get("id")
                if entry_id not in current_by_id:
                    raise FragmentValidationError(
                        f"{retraction_path}: retraction list: "
                        f"entry {entry_id!r} removed"
                    )
                current_entry = current_by_id[entry_id]
                # AC-B4a: refuse an edited entry — same id but changed fields.
                if current_entry != base_entry:
                    raise FragmentValidationError(
                        f"{retraction_path}: retraction list: "
                        f"entry {entry_id!r} edited (category or other field changed)"
                    )


def _safe_relative(path: Path, repo: Path) -> str:
    """Return the repo-relative POSIX path, or the path itself if outside repo."""
    try:
        return path.resolve().relative_to(repo).as_posix()
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Released-version inventory — moved here from build-site.py so compact() and
# the site build share one inventory (AC1 import direction preserved).
# ---------------------------------------------------------------------------


def released_versions_from_parsed(parsed: ParsedChangelog) -> dict[str, set[str]]:
    """Return every released package version present in the historical changelog.

    Iterates only over released (non-unreleased) entries.  This is the public
    form of the function that tools/build-site.py previously kept private as
    ``_released_versions_from_parsed``.
    """
    released: dict[str, set[str]] = {}
    for release in parsed.releases:
        if release["unreleased"]:
            continue
        for package in release["packages"]:
            released.setdefault(package["name"], set()).add(package["version"])
    return released


def current_pack_versions(root: Path, site_toml: Path) -> list[dict]:
    """Return a minimal pack list (name, version) from ``packs/*/pack.toml``.

    Mirrors the name/version subset that ``discover_packs`` in build-site.py
    returns, skipping slugs that start with ``_``.  Does not read ``site_toml``
    for ordering — suitable as ``discover_packs_fn`` for
    ``released_versions_from_packs`` when only inventory membership matters.
    """
    packs_dir = root / "packs"
    if not packs_dir.is_dir():
        return []
    result: list[dict] = []
    for pack_toml in sorted(packs_dir.glob("*/pack.toml")):
        slug = pack_toml.parent.name
        if slug.startswith("_"):
            continue
        with pack_toml.open("rb") as fh:
            data = tomllib.load(fh)
        p = data.get("pack", {})
        name = p.get("name", slug)
        version = p.get("version", "")
        if not name or not version:
            continue
        result.append({"name": name, "version": version})
    return result


def _version_parts(version: str) -> tuple[int, ...] | None:
    """Return comparable dotted integer version parts, or None if ambiguous."""
    if not re.fullmatch(r"\d+(?:\.\d+)*", version):
        return None
    return tuple(int(part) for part in version.split("."))


def _version_lte(candidate: str, current: str) -> bool:
    """Deterministically compare two pack versions, failing closed on ambiguity."""
    if candidate == current:
        return True
    candidate_parts = _version_parts(candidate)
    current_parts = _version_parts(current)
    if candidate_parts is None or current_parts is None:
        return False
    length = max(len(candidate_parts), len(current_parts))
    padded_candidate = candidate_parts + (0,) * (length - len(candidate_parts))
    padded_current = current_parts + (0,) * (length - len(current_parts))
    return padded_candidate <= padded_current


def released_versions_from_packs(
    *,
    root: Path,
    site_toml: Path,
    fragments: list[ValidatedFragment],
    historical: dict[str, set[str]],
    discover_packs_fn=None,
) -> dict[str, set[str]]:
    """Build the release inventory from pack manifests and historical changelog.

    Moved from ``tools/build-site.py`` to ``tools/changelog.py`` so that
    ``compact`` and the site build share one inventory, and AC1's import
    direction (build-site imports changelog, never the reverse) holds.

    ``discover_packs_fn`` is injected by build-site.py so changelog.py does not
    import build-site.py.
    """
    inventory = {name: set(versions) for name, versions in historical.items()}
    if discover_packs_fn is None or not site_toml.exists() or not (root / "packs").exists():
        return inventory
    current_versions = {
        str(pack["name"]): str(pack["version"])
        for pack in discover_packs_fn(root, site_toml)
        if pack.get("name") and pack.get("version")
    }
    for package_name, current_version in current_versions.items():
        inventory.setdefault(package_name, set()).add(current_version)
    for fragment in fragments:
        for package in fragment.packages:
            current_version = current_versions.get(package["name"])
            if current_version is None:
                continue
            if _version_lte(package["version"], current_version):
                inventory.setdefault(package["name"], set()).add(package["version"])
    return inventory


def compact_inventory_fn(
    historical: dict[str, set[str]],
) -> Callable[[list[ValidatedFragment]], dict[str, set[str]]]:
    """Return the inventory function the compact CLI passes to compact_month.

    The returned function derives the released-version inventory from pack
    manifests and the historical changelog — the same sources the site build
    uses — so compact classifies the same fragments as released (AC-B6 / spec
    AC1: changelog.py never loads build-site.py).

    ``historical`` is the parsed inventory from the historical changelog baseline.
    """
    def _fn(records: list[ValidatedFragment]) -> dict[str, set[str]]:
        return released_versions_from_packs(
            root=Path(),
            site_toml=Path("site.toml"),
            fragments=records,
            historical=historical,
            discover_packs_fn=current_pack_versions,
        )
    return _fn


# ---------------------------------------------------------------------------
# Bundle part writer — used by both compact and T18.
# ---------------------------------------------------------------------------


def write_bundle_part(
    records: list[ValidatedFragment],
    directory: Path,
    part_name: str,
    raw_bytes_map: dict[str, bytes] | None = None,
) -> Path:
    """Write one bundle part from an explicit ordered record set.

    ``raw_bytes_map`` maps fragment id → raw bytes. When absent, each
    fragment's bytes are serialised fresh from its validated fields.
    Returns the written path. Uses exclusive create (``x`` flag).
    """
    part_path = directory / part_name
    lines: list[bytes] = []
    for fragment in records:
        if raw_bytes_map is not None and fragment.id in raw_bytes_map:
            raw = raw_bytes_map[fragment.id]
        else:
            # Reconstruct the fragment bytes from its validated fields.
            raw = _reconstruct_fragment_bytes(fragment)
        lines.append(BUNDLE_SEPARATOR_BYTES + raw)
    content = b"".join(lines)
    directory.mkdir(parents=True, exist_ok=True)
    try:
        # Exclusive create; the mode follows the process umask like any checkout file.
        part_file = part_path.open("xb")
    except FileExistsError as exc:
        raise FragmentValidationError(
            f"{part_path}: part already exists; refusing to overwrite"
        ) from exc
    try:
        with part_file as fh:
            fh.write(content)
    except Exception:
        import contextlib as _contextlib
        with _contextlib.suppress(OSError):
            part_path.unlink(missing_ok=True)
        raise
    return part_path


def _reconstruct_fragment_bytes(fragment: ValidatedFragment) -> bytes:
    """Reconstruct the canonical bytes for one ValidatedFragment."""
    lines = [
        "+++",
        "schema = 1",
        f'id = "{fragment.id}"',
        f'anchor = "{fragment.anchor}"',
        f"date = {fragment.date}",
    ]
    for package in fragment.packages:
        lines.extend([
            "[[packages]]",
            f'name = "{package["name"]}"',
            f'version = "{package["version"]}"',
        ])
    lines.append("+++")
    for section, body_lines in fragment.sections.items():
        lines.append(f"## {section}")
        lines.extend(body_lines)
    text = "\n".join(lines) + "\n"
    return text.encode("utf-8")


# ---------------------------------------------------------------------------
# compact command (AC-B6).
# ---------------------------------------------------------------------------


def compact_month(
    month: str,
    *,
    fragment_dir: Path = Path("docs/product/changelog.d"),
    bundle_dir: Path = Path("docs/product/changelog.months"),
    retraction_path: Path = Path("docs/product/changelog-retractions.toml"),
    released_versions: dict | None = None,
    inventory_fn: Callable[[list[ValidatedFragment]], dict[str, set[str]]] | None = None,
    safety: ModuleType | None = None,
    git_runner=_run_git,
) -> tuple[list[Path], list[Path]]:
    """Move released fragments for ``month`` into a new bundle part.

    ``month`` is ``YYYY-MM``. Returns ``(created_parts, deleted_fragments)``.
    Reads no clock. Follows the failure semantics in ADR-0143 D8:
    - Plans and validates in memory.
    - Writes new parts with exclusive create.
    - Re-reads written parts.
    - Only then deletes fragments.
    - On failure before deletion: removes created parts.
    - On failure during deletion: parts stay; rerun completes.

    ``released_versions`` and ``inventory_fn`` are mutually exclusive.
    When ``inventory_fn`` is given, the released-version inventory is derived
    from the collected records after the collection step (supporting the rerun
    path without a pre-collection call).  When both are absent, the inventory
    is empty (compact nothing).
    """
    # Validate month format.
    try:
        yyyy_s, mm_s = month.split("-")
        date(int(yyyy_s), int(mm_s), 1)
    except (ValueError, AttributeError) as exc:
        raise FragmentValidationError(
            f"compact: {month!r} is not a valid YYYY-MM month"
        ) from exc

    if released_versions is not None and inventory_fn is not None:
        raise FragmentValidationError(
            "compact_month: released_versions and inventory_fn are mutually exclusive"
        )
    fs = safety if safety is not None else _file_safety()

    # Compute the inventory eagerly when released_versions is given (the common
    # call-with-explicit-inventory path used by tests).  When inventory_fn is
    # given, the inventory is deferred until after record collection so the
    # rerun path (which calls collect_changelog_records inside compact_month and
    # catches DuplicateRecordIdError there) can supply records to inventory_fn
    # without triggering a pre-collection call at the CLI level.
    if inventory_fn is None:
        if released_versions is None:
            released_versions = {}
        inventory = _normalize_released_versions(released_versions)

    # Collect all current records.  In the rerun case (bundle part written but
    # fragment not yet deleted), the same id may appear in both forms, causing
    # collect_changelog_records to raise "duplicate id".  Detect this by first
    # trying the strict collection; on duplicate, fall back to collecting loose
    # and bundle records separately without cross-form deduplication.
    # Rerun recovery only: ids already bundled, mapped to their exact record bytes.
    already_bundled_bytes: dict[str, bytes] = {}
    try:
        loose, bundled = collect_changelog_records(
            fragment_dir=fragment_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            safety=fs,
            git_runner=git_runner,
        )
    except DuplicateRecordIdError:
        # Rerun recovery: a previous compact wrote the part but failed to delete
        # some fragments, so the same id appears in both forms.  Collect each
        # form independently.  Pass seen_ids=set() to _collect_bundle_records so
        # a genuine duplicate across two bundle parts still raises rather than
        # being swallowed.
        loose = (
            collect_validated_fragments(fragment_dir, safety=fs, git_runner=git_runner)
            if fragment_dir.exists()
            else []
        )
        bundle_tuples = _collect_bundle_records(bundle_dir, fs, seen_ids=set())
        already_bundled_bytes = {ff.id: raw_record for _, _, raw_record, ff in bundle_tuples}
        bundled = [ff for _, _, _, ff in bundle_tuples]
        retracted_ids = {e["id"] for e in _read_retraction_list(retraction_path, fs)}
        _refuse_unsafe_record_set(loose, bundled, retracted_ids, bundle_dir)
    if inventory_fn is not None:
        # Compute inventory after collecting records so inventory_fn receives all
        # records regardless of which collection path was taken.  IDs appearing in
        # both forms count once (released_versions_from_packs adds to sets).
        inventory = _normalize_released_versions(inventory_fn([*loose, *bundled]))

    # Select fragments for this month that are released.
    # Read each fragment via the confined helper (no raw path.read_bytes()) and
    # build raw_bytes_map in the same pass to avoid a second read later.
    to_compact: list[ValidatedFragment] = []
    # Loose fragments a failed earlier run already bundled byte-exactly: the
    # rerun only finishes deleting them, so they are never bundled twice.
    already_bundled: list[ValidatedFragment] = []
    raw_bytes_map: dict[str, bytes] = {}
    oversized: list[Path] = []
    for fragment in loose:
        if not fragment.date.startswith(month + "-"):
            continue
        if not _fragment_in_released_inventory(fragment, inventory):
            continue
        # Read via the blessed confined helper (Fix E: no path.read_bytes()).
        try:
            raw = fs.read_confined_regular_file(
                fragment.path.parent, fragment.path, max_bytes=MAX_FRAGMENT_BYTES
            )
        except fs.UnsafeContentError as exc:
            raise _fragment_error(
                fragment.path, "path", "confined fragment file during compact"
            ) from exc
        if fragment.id in already_bundled_bytes:
            if raw != already_bundled_bytes[fragment.id]:
                raise _fragment_error(
                    fragment.path, "id", "loose bytes equal to its already-bundled record"
                )
            already_bundled.append(fragment)
            continue
        record_size = len(BUNDLE_SEPARATOR_BYTES) + len(raw)
        if record_size > MAX_BUNDLE_BYTES:
            oversized.append(fragment.path)
            print(
                f"compact: {fragment.path.name}: fragment too large to fit a part "
                f"({record_size} > {MAX_BUNDLE_BYTES}); leaving loose",
                file=sys.stderr,
            )
            continue
        raw_bytes_map[fragment.id] = raw
        to_compact.append(fragment)

    if not to_compact and not already_bundled:
        return [], []

    # Sort in canonical order.
    to_compact_sorted = _ordered_fragments(to_compact, sort_fragments=True)

    # Determine the next NN for this month using the confined helper so that
    # symlinks and non-regular entries in the bundle directory are refused.
    bundle_dir.mkdir(parents=True, exist_ok=True)
    existing_nns: set[int] = set()
    if bundle_dir.exists():
        try:
            existing_parts_enum = fs.list_confined_regular_files(
                bundle_dir,
                bundle_dir,
                max_entries=MAX_BUNDLE_DIR_ENTRIES,
                max_files=MAX_BUNDLE_FILES,
                max_depth=MAX_BUNDLE_DEPTH,
            )
        except fs.UnsafeContentError as exc:
            raise _bundle_error(
                bundle_dir, "path", "confined bundle directory for NN enumeration"
            ) from exc
        for p in existing_parts_enum:
            m = _BUNDLE_NAME_RE.fullmatch(p.name)
            if m and f"{m.group(1)}-{m.group(2)}" == month:
                existing_nns.add(int(m.group(3)))
    next_nn = 0
    while next_nn in existing_nns:
        next_nn += 1

    # raw_bytes_map is already populated above; no second read needed.

    current_part: list[ValidatedFragment] = []
    current_size = 0
    parts_to_write: list[list[ValidatedFragment]] = []
    for fragment in to_compact_sorted:
        raw = raw_bytes_map[fragment.id]
        record_size = len(BUNDLE_SEPARATOR_BYTES) + len(raw)
        if current_part and current_size + record_size > MAX_BUNDLE_BYTES:
            parts_to_write.append(current_part)
            current_part = [fragment]
            current_size = record_size
        else:
            current_part.append(fragment)
            current_size += record_size
    if current_part:
        parts_to_write.append(current_part)

    # Write parts with exclusive create, then re-read to verify.
    created_parts: list[Path] = []
    try:
        for part_records in parts_to_write:
            nn_str = f"{next_nn:02d}"
            part_name = f"{month}-{nn_str}.bundle"
            part_path = write_bundle_part(
                part_records, bundle_dir, part_name, raw_bytes_map
            )
            # Re-read the written part to verify.
            try:
                re_read_bytes = fs.read_confined_regular_file(
                    bundle_dir, part_path, max_bytes=MAX_BUNDLE_BYTES
                )
            except fs.UnsafeContentError as exc:
                field = getattr(exc, "budget", None) or "path"
                raise _bundle_error(part_path, str(field), "confined regular bundle part") from exc
            _parse_bundle_part(part_path, re_read_bytes)
            created_parts.append(part_path)
            existing_nns.add(next_nn)
            next_nn += 1
            while next_nn in existing_nns:
                next_nn += 1
    except Exception:
        # Failure before deletion: remove created parts.
        import contextlib as _contextlib
        for p in created_parts:
            with _contextlib.suppress(OSError):
                p.unlink(missing_ok=True)
        raise

    # Delete the compacted fragments. Compute bundled_ids once before the loop
    # (Fix G: avoid O(n²) re-reads of all parts per fragment).
    deleted: list[Path] = []
    failed: list[Path] = []
    bundled_ids = {
        ff.id for _, _, _, ff in _collect_bundle_records(bundle_dir, fs)
    }
    for fragment in [*to_compact_sorted, *already_bundled]:
        if fragment.id not in bundled_ids:
            continue
        try:
            fragment.path.unlink()
            deleted.append(fragment.path)
        except OSError as exc:
            failed.append(fragment.path)
            print(
                f"compact: failed to delete {fragment.path}: {exc}",
                file=sys.stderr,
            )
    if failed:
        # The parts stay, so every record is still present; a rerun completes.
        raise _fragment_error(
            failed[0], "compact", f"deletion of {len(failed)} bundled fragment(s); rerun compact"
        )

    return created_parts, deleted


# ---------------------------------------------------------------------------
# retract command (AC-B4a).
# ---------------------------------------------------------------------------


def retract_record(
    record_id: str,
    category: str,
    *,
    bundle_dir: Path = Path("docs/product/changelog.months"),
    retraction_path: Path = Path("docs/product/changelog-retractions.toml"),
    safety: ModuleType | None = None,
) -> Path:
    """Remove one bundled record and append a retraction list entry.

    Returns the modified part path. Rewrites the part first, then appends to
    the retraction list. Each write is atomic (exclusive temp + rename).
    A failure between the two writes leaves the record removed and unlisted,
    which validation refuses; rerunning `retract` for the same id completes.
    """
    # Validate inputs.
    try:
        parsed_uuid = UUID(record_id, version=4)
    except ValueError as exc:
        raise FragmentValidationError(
            f"retract: {record_id!r} is not a valid UUIDv4"
        ) from exc
    if parsed_uuid.version != 4 or str(parsed_uuid) != record_id:
        raise FragmentValidationError(
            f"retract: {record_id!r} is not a lowercase UUIDv4"
        )
    if category not in _RETRACTION_CATEGORIES:
        raise FragmentValidationError(
            f"retract: {category!r} is not a valid category; "
            f"use one of {sorted(_RETRACTION_CATEGORIES)}"
        )
    fs = safety if safety is not None else _file_safety()

    # Check if already retracted (idempotent rerun).
    retractions = _read_retraction_list(retraction_path, fs)
    already_retracted = any(e["id"] == record_id for e in retractions)

    # Find the bundle part containing this record.
    bundle_tuples = _collect_bundle_records(bundle_dir, fs)
    target_part: Path | None = None
    for part_path, _part_month, _record_bytes, fragment in bundle_tuples:
        if fragment.id == record_id:
            target_part = part_path
            break

    if target_part is None and not already_retracted:
        # Intermediate-state rerun: the record was already removed from the part
        # (phase 1 succeeded) but the retraction list entry was never written
        # (phase 2 did not complete).  Validation refuses this state; rerunning
        # retract with the same id and category completes phase 2.  Fall through
        # to the list-append block below.
        pass

    if target_part is not None:
        # Read the part raw bytes.
        part_raw = _read_bundle_part(target_part, bundle_dir, fs)
        # Remove the target record from the part.
        all_records = _parse_bundle_part(target_part, part_raw)
        remaining = [(rb, f) for rb, f in all_records if f.id != record_id]

        if not remaining:
            # Last record: delete the part entirely.
            _atomic_delete(target_part)
        else:
            # Rewrite the part without the retracted record.
            new_content = b"".join(
                BUNDLE_SEPARATOR_BYTES + rb for rb, _ in remaining
            )
            _atomic_write_bytes(target_part, new_content)

    if not already_retracted:
        # Rebuild the retraction list from the already-confined parsed read
        # (Fix E: no raw read_text — avoids symlink bypass and size-cap bypass).
        # Reconstruct existing entries in TOML form from the parsed list, then
        # append the new entry.
        new_entry_block = (
            f'[[retraction]]\nid = "{record_id}"\ncategory = "{category}"\n'
        )
        if retractions:
            existing_blocks = "\n".join(
                f'[[retraction]]\nid = "{e["id"]}"\ncategory = "{e["category"]}"'
                for e in retractions
            )
            new_content_text = existing_blocks + "\n\n" + new_entry_block
        else:
            new_content_text = new_entry_block
        _atomic_write_text(retraction_path, new_content_text)

    return target_part if target_part is not None else retraction_path


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    """Atomically write bytes to path via a temp file and rename.

    Uses exclusive create (``O_EXCL``) for the temp file, matching
    ``_atomic_write_text`` and ``write_bundle_part``.
    """
    tmp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        tmp_file = tmp.open("xb")
        try:
            with tmp_file as fh:
                fh.write(content)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _atomic_write_text(path: Path, content: str) -> None:
    """Atomically write text to path via a temp file and rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with tmp.open("x", encoding="utf-8") as fh:
            fh.write(content)
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _atomic_delete(path: Path) -> None:
    """Delete path atomically by rename-to-temp then unlink."""
    tmp = path.with_name(f".{path.name}.{uuid4().hex}.deleting")
    # A failed rename must stop the caller: retract would otherwise list a
    # record as retracted while it stays published.
    path.rename(tmp)
    import contextlib as _contextlib
    with _contextlib.suppress(OSError):
        tmp.unlink()


def _parse_package_argument(value: str, version: str | None = None) -> dict[str, str]:
    """Parse CLI package arguments."""
    name, separator, inline_version = value.partition("=")
    if version is not None:
        if separator:
            raise argparse.ArgumentTypeError("use --package NAME with --version VERSION")
        return {"name": name, "version": version}
    if not separator:
        raise argparse.ArgumentTypeError("expected NAME=VERSION")
    return {"name": name, "version": inline_version}


def main(argv: list[str] | None = None) -> int:
    """Run the changelog command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    new_parser = subcommands.add_parser("new", help="create one changelog fragment")
    new_parser.add_argument(
        "--directory",
        type=Path,
        default=Path("docs/product/changelog.d"),
        help="fragment directory to write into",
    )
    new_parser.add_argument(
        "--package",
        dest="packages",
        action="append",
        required=True,
        metavar="NAME",
        help="package name or NAME=VERSION; repeat NAME=VERSION for multi-package releases",
    )
    new_parser.add_argument("--version", help="package version for a single --package NAME")
    new_parser.add_argument("--date", dest="fragment_date", required=True)
    new_parser.add_argument(
        "--highlight",
        dest="highlights",
        action="append",
        required=True,
        help="Highlights bullet text; repeat for multiple bullets",
    )
    render_parser = subcommands.add_parser(
        "render", help="render the complete product changelog"
    )
    render_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="complete changelog output path",
    )
    render_parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("docs/product/changelog.md"),
        help="frozen historical changelog input",
    )
    render_parser.add_argument(
        "--fragments",
        type=Path,
        default=Path("docs/product/changelog.d"),
        help="fragment directory to validate and render",
    )
    validate_parser = subcommands.add_parser(  # noqa: F841
        "validate", help="validate cross-form record identity against the merge base"
    )
    compact_parser = subcommands.add_parser(
        "compact", help="move released fragments for a month into a bundle part"
    )
    compact_parser.add_argument(
        "--month",
        required=True,
        help="month to compact, as YYYY-MM",
    )
    compact_parser.add_argument(
        "--fragment-dir",
        type=Path,
        default=Path("docs/product/changelog.d"),
    )
    compact_parser.add_argument(
        "--bundle-dir",
        type=Path,
        default=Path("docs/product/changelog.months"),
    )
    retract_parser = subcommands.add_parser(
        "retract", help="retract one bundled record by id"
    )
    retract_parser.add_argument("--id", required=True, dest="record_id")
    retract_parser.add_argument(
        "--category",
        required=True,
        choices=sorted(_RETRACTION_CATEGORIES),
    )
    retract_parser.add_argument(
        "--bundle-dir",
        type=Path,
        default=Path("docs/product/changelog.months"),
    )
    retract_parser.add_argument(
        "--retraction-list",
        type=Path,
        default=Path("docs/product/changelog-retractions.toml"),
    )
    args = parser.parse_args(argv)
    if args.command == "new":
        if args.version is not None and len(args.packages) != 1:
            parser.error("--version can only be used with one --package")
        packages = [
            _parse_package_argument(package, args.version)
            if args.version is not None
            else _parse_package_argument(package)
            for package in args.packages
        ]
        path = create_fragment(
            args.directory,
            packages=packages,
            fragment_date=args.fragment_date,
            highlights=args.highlights,
        )
        print(path)
        return 0
    if args.command == "render":
        try:
            render_changelog_to_output(
                args.output,
                baseline=args.baseline,
                fragments=args.fragments,
            )
        except FragmentValidationError as exc:
            print(exc, file=sys.stderr)
            return 1
        print(args.output)
        return 0
    if args.command == "validate":
        try:
            validate_changelog_cross_form_identity()
            validate_historical_changelog_baseline(Path("docs/product/changelog.md"))
        except FragmentValidationError as exc:
            print(exc, file=sys.stderr)
            return 1
        return 0
    if args.command == "compact":
        try:
            # Build the historical inventory from the baseline changelog.  The
            # pack-manifest portion of the inventory is deferred to compact_month
            # via inventory_fn so that the rerun path (where the CLI must not
            # call collect_changelog_records itself) can still derive a correct
            # inventory after the internal DuplicateRecordIdError recovery.
            baseline_path = Path("docs/product/changelog.md")
            if baseline_path.exists():
                parsed_cl = parse_changelog_releases(
                    baseline_path.read_text(encoding="utf-8")
                )
                historical_inv = released_versions_from_parsed(parsed_cl)
            else:
                historical_inv = {}
            created, deleted = compact_month(
                args.month,
                fragment_dir=args.fragment_dir,
                bundle_dir=args.bundle_dir,
                inventory_fn=compact_inventory_fn(historical_inv),
            )
        except FragmentValidationError as exc:
            print(exc, file=sys.stderr)
            return 1
        for p in created:
            print(f"created: {p}")
        for p in deleted:
            print(f"deleted: {p}")
        return 0
    if args.command == "retract":
        try:
            result = retract_record(
                args.record_id,
                args.category,
                bundle_dir=args.bundle_dir,
                retraction_path=args.retraction_list,
            )
        except FragmentValidationError as exc:
            print(exc, file=sys.stderr)
            return 1
        print(f"retracted: {result}")
        return 0
    parser.error(f"unsupported command {args.command!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
