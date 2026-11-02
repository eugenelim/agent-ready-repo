"""Header-only readiness: the rules `dispatch.py` applies to a repository's artifacts.

A port of the readiness rules `workspace-status`'s engine applied to the
header-derived queue, with the registry dropped: it holds no workspace parsing,
legacy entries or aliases, memberships from `workspace.toml`, initiatives, repair
or migration. `dispatch.py` builds the queue, active and shipped spec lists from
each spec's own `Status:` header and hands them to `run_canonical_reconciliation`.

Every function keeps the base name and semantics it had in the engine. The module
reads only the repository under the root it is given and writes nothing. It loads
nothing itself: `dispatch.py` passes a confined sibling loader for the cooling
chain.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import dataclasses  # noqa: E402
import datetime  # noqa: E402
import errno  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import stat  # noqa: E402
import tomllib  # noqa: E402
from collections.abc import Callable, Iterator, Mapping  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

# The callables the cooling chain reaches. The record attributes are guarded per
# record by `_COOLING_RECORD_FIELDS`, because a module can satisfy this contract
# while one record does not.
_COOLING_MODULE_CALLABLES = ("load_record", "is_due")
_CLOSE_WORK_CALLABLES = ("file_safety", "resolve_mutation_authority", "open_validated_parent")

WORKSPACE_ARTIFACT_KINDS = ("intent", "research", "design", "brief", "spec", "defect")


_MALFORMED_COMPLETION_RECEIPT = "malformed-completion-receipt"


# Matches close-work's MAX_TEXT_LENGTH so the producer cannot write a receipt
# this parser then refuses. Bounded here rather than at satisfaction time: an
# unbounded value is serialized into the routing identity on every run, long
# before any grammar is applied to it.
_COMPLETION_RECEIPT_MAX_FIELD_LENGTH = 512


_COMPLETION_RECEIPT_DELIVERY_ID_RE = r"^[a-z0-9][a-z0-9-]{0,127}$"


_COMPLETION_RECEIPT_EVENTS = ("merge", "release", "acceptance")


_COMPLETION_RECEIPT_EVIDENCE_REF_RE = (
    r"^(?:commit:[0-9a-f]{40}|pr:[0-9]+|run:[0-9]+)$"
)


_COMPLETION_RECEIPT_OUTCOMES = frozenset({"completed", "abandoned", "superseded"})


_FINDING_NEXT_ACTIONS = {
    "invalid_workspace": "Correct workspace.toml, then rerun reconciliation.",
    "unmigrated_workspace": (
        "Run workspace-status repair-plan, then repair-apply, to move the remaining "
        "workspace.toml entries onto their artifacts."
    ),
    "invalid_artifact_path": "Replace it with a confined canonical repository-relative path.",
    "missing_artifact": "Create and review the canonical artifact before dispatch.",
    "unreadable_artifact": "Restore readable repository state, then rerun reconciliation.",
    "invalid_captured_item": (
        "Fix the named field of that captured-item file, then rerun reconciliation."
    ),
    "missing_plan": "Create and approve the plan before dispatch.",
    "unapproved_spec": "Complete the spec approval gate.",
    "impossible_transition": (
        "Correct the artifact or membership through a reviewed transition."
    ),
    "cooled_child_scope_unknown": (
        "Set parent on the spec's lifecycle record: a resolving brief path, or "
        "none only when that spec has no parent brief; a tracker-origin entry "
        "declares source.parent instead."
    ),
    "refresh_conflict": "Resolve the conflict through the artifact's authority workflow.",
    "unsatisfied_dependency": "Complete or explicitly revise the dependency.",
    "missing_dependency": "Materialize or correct the dependency target.",
    "dependency_cycle": "Break the cycle through an explicit plan change.",
    "invalid_dependency": (
        "Rewrite the item as a typed reference or a captured-item path, "
        "or correct its receipt, in the waiting item's header."
    ),
    "invalid_receipt": (
        "Replace it with a reviewed receipt matching the pinned dependency."
    ),
    "invalid_completion_receipt": (
        "Replace it with a valid reviewed completion receipt for that dependency."
    ),
    "invalid_source_authority": (
        "Correct the closed source-authority block, then rerun reconciliation."
    ),
    "source_authority_migration_required": (
        "Add the reviewed source-authority block before using refresh."
    ),
    "invalid_lifecycle_record": (
        "Repair or remove that record; other records still cool."
    ),
    "cooling_state_unavailable": (
        "Install close-work or repair docs/lifecycle/; no artifact is excluded this run."
    ),
}


@dataclasses.dataclass(frozen=True)
class RoutingFinding:
    """Stable refusal emitted while parsing or evaluating workspace state."""

    code: str
    path: str
    detail: str
    next_action: str
    dispatchable: bool = False


@dataclasses.dataclass(frozen=True)
class SourceRecord:
    """Validated source provenance shared by intake and workspace entries."""

    mode: str
    ref: str | None = None
    revision: str | None = None
    parent: str | None = None
    coordination: str | None = None
    tracker_profile: dict[str, str] | None = None
    locator: str | None = None
    object_type: str | None = None


@dataclasses.dataclass(frozen=True)
class Dependency:
    """Validated local or cross-repository hard dependency."""

    type: str
    kind: str
    path: str
    containing_brief: str | None = None
    receipt_id: str | None = None
    accepted_revision: str | None = None
    receipt: dict[str, str] | str | None = None


@dataclasses.dataclass(frozen=True)
class WorkspaceLocator:
    """Validated non-path locator carried by an additive workspace entry."""

    kind: str
    value: str


@dataclasses.dataclass(frozen=True)
class WorkspaceEntry:
    """Validated target workspace entry; eligibility is evaluated separately."""

    path: str | None
    kind: str
    source: SourceRecord
    summary: str
    needs: list[Dependency]
    surface_role: str | None = None
    locator: WorkspaceLocator | None = None

    @property
    def slug(self) -> str:
        if self.path is None:
            return f"surface:{self.surface_role or 'unresolved'}"
        if self.path.startswith("docs/specs/") and self.path.endswith("/spec.md"):
            return self.path[len("docs/specs/"):-len("/spec.md")]
        return self.path.removeprefix("spec/")


@dataclasses.dataclass(frozen=True)
class WorkspaceMembership:
    """One header-derived spec entry at a `work.*` collection."""

    entry: WorkspaceEntry
    collection: str
    entry_index: int = 0


@dataclasses.dataclass(frozen=True)
class ArtifactMetadata:
    """Artifact metadata needed for T2 reconciliation."""

    path: str
    kind: str
    status: str | None
    exists: bool
    readable: bool = True
    invalid_path: bool = False
    plan_invalid_path: bool = False
    plan_readable: bool = True
    plan_exists: bool | None = None
    parent: str | None = None
    ref: str | None = None
    revision: str | None = None
    refresh_conflict: bool = False
    resolution: str | None = None
    authority_status: dict[str, object] | None = None
    authority_error: str | None = None
    # Set only for a migrated captured membership, from its record: the record's
    # `Kind:`, or the one finding an invalid or unreadable record gives.
    captured_kind: str | None = None
    captured_finding: RoutingFinding | None = None


@dataclasses.dataclass(frozen=True)
class DispatchEvaluation:
    """Positive dispatch predicate result for one parsed membership."""

    entry: WorkspaceEntry
    collection: str
    dispatchable: bool
    findings: list[RoutingFinding]
    authority_status: dict[str, object] | None


@dataclasses.dataclass(frozen=True)
class CanonicalWorkspaceResult:
    """Canonical T2 reconciliation result before CLI/MCP projection."""

    memberships: list[WorkspaceMembership]
    findings: list[RoutingFinding]
    evaluations: list[DispatchEvaluation]
    dispatch_by_path: dict[str, DispatchEvaluation]
    # `memberships` is deliberately unfiltered, so every consumer of it needs
    # the cooled set to know which entries it may not open. Carrying the set
    # here rather than threading a parameter is what makes that unmissable:
    # `canonical_repository_identity` consumed `memberships` and fingerprinted
    # each artifact by reading its body, which silently reopened every cooled
    # spec.md and plan.md on all four ordinary-orientation surfaces.
    cooled: frozenset[Path] = frozenset()
    # Each non-cooled local membership's header edges, keyed by waiting path.
    # They, not `entry.needs`, are what blocks and what the routing identity
    # fingerprints.
    header_edges: dict[str, tuple[Dependency, ...]] = dataclasses.field(
        default_factory=dict
    )


def _finding(code: str, path: str = "", detail: str = "") -> RoutingFinding:
    return RoutingFinding(
        code=code,
        path=path,
        detail=detail,
        next_action=_FINDING_NEXT_ACTIONS[code],
    )


def _is_bounded_text(value: object, max_length: int) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= max_length


def _is_safe_locator(value: object) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 1000 and not any(
        marker in value for marker in ("@", "?", "#")
    )


def _is_repository_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= 1000:
        return False
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return False
    if "\\" in value:
        return False
    if any(ord(character) <= 31 or ord(character) == 127 for character in value):
        return False
    parts = value.split("/")
    return not (".." in parts or "." in parts or "" in parts)


_SINGLE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,199}$")


# Upper bound on any untrusted workspace value emitted as a finding identifier.
_MAX_FINDING_IDENTIFIER = 200


def _is_canonical_spec_artifact_path(path: object) -> bool:
    if not isinstance(path, str) or not _is_repository_relative_path(path):
        return False
    parts = path.split("/")
    return (
        len(parts) == 4
        and parts[:2] == ["docs", "specs"]
        and _SINGLE_SEGMENT_RE.fullmatch(parts[2]) is not None
        and parts[3] == "spec.md"
    )


def _is_canonical_local_brief_path(path: object) -> bool:
    if not isinstance(path, str) or not _is_repository_relative_path(path):
        return False
    parts = path.split("/")
    return (
        len(parts) == 4
        and parts[:3] == ["docs", "product", "briefs"]
        and _SINGLE_SEGMENT_RE.fullmatch(parts[3].removesuffix(".md")) is not None
        and parts[3].endswith(".md")
    )


# `\Z`, not `$`: in Python `$` also matches just before a trailing newline,
# so `brief:slug\n` matched and normalised through with the newline silently
# dropped, while a trailing tab, space or carriage return was refused. One
# character of the excluded set leaked because of the anchor.
_BRIEF_POINTER_RE = re.compile(r"^brief:(?P<slug>.*)\Z", re.S)


def _normalized_brief_pointer(value: str) -> str:
    """Normalize a well-formed `brief:<slug>` value to its canonical path.

    `brief:<slug>` is the canonical `Brief:` form. Normalizing
    here — before `_is_canonical_local_brief_path` runs — is what keeps that
    helper itself unrelaxed: it also guards `workspace.toml` entry and
    dependency paths, where a slug is meaningless and must keep failing. A
    malformed `brief:` value (wrong slug shape, a second colon, a space) is
    returned unchanged, so it falls through the existing checks and is
    refused exactly as before.
    """
    match = _BRIEF_POINTER_RE.match(value)
    if match and _SINGLE_SEGMENT_RE.fullmatch(match.group("slug")):
        return f"docs/product/briefs/{match.group('slug')}.md"
    return value


def _bounded_finding_identifier(value: str) -> str:
    """Bound an untrusted workspace value before it becomes a finding identifier.

    Findings are rendered back into an agent's context, so an unbounded or
    control-character-bearing value read from `workspace.toml` is an
    output-injection surface. Unsafe but *path-shaped* values survive this
    bound on purpose, so `invalid_artifact_path` can still name them; only
    unrenderable ones degrade to the unattributed fallback.
    """
    if len(value) > _MAX_FINDING_IDENTIFIER:
        return ""
    if any(char < " " or char == "\x7f" for char in value):
        return ""
    return value


_ALLOWED_KIND_BY_COLLECTION = {
    "backlog.open": {"intent", "research", "design", "brief", "spec", "defect"},
    "backlog.closed": {"defect"},
    "shaping_queue.backlog": {"intent", "research", "design"},
    "shaping_queue.active": {"intent", "research", "design"},
    "brief_queue.draft": {"brief"},
    "brief_queue.ready": {"brief"},
    "brief_queue.executing": {"brief"},
    "brief_queue.shipped": {"brief"},
    "brief_queue.withdrawn": {"brief"},
    "brief_queue.cancelled": {"brief"},
    "work.queue": {"spec"},
    "work.active": {"spec"},
    "work.shipped": {"spec"},
}


_TERMINAL_STATUS_BY_KIND = {
    "spec": {"Shipped"},
    "defect": {"fixed"},
    "brief": {"Ready", "Executing", "Shipped"},
    "intent": {"Accepted", "Fulfilled"},
    "research": {"Complete"},
    "design": {"Approved"},
}


def _confined_artifact_path(root: Path, rel_path: str) -> Path | None:
    if not _is_repository_relative_path(rel_path):
        return None
    try:
        root_resolved = root.resolve()
        candidate = (root_resolved / rel_path).resolve()
        candidate.relative_to(root_resolved)
        return candidate
    except (OSError, RuntimeError, ValueError):
        return None


def _confined_briefs_path(root: Path, rel_path: str) -> bool:
    """Whether `rel_path`, once resolved with symlinks followed, stays
    beneath the resolved `docs/product/briefs/` directory, which must itself
    stay beneath the resolved repository root.

    This boundary is stricter than `_confined_artifact_path`'s repository-root
    confinement: a brief path whose symlink resolves to another directory
    inside the repository passes repo-root confinement and must still be
    refused here, because the boundary is the briefs directory, not the
    repository root.

    Both halves are load-bearing, and neither replaces the other. Confining
    the candidate alone leaves the boundary itself unanchored: make
    `docs/product/briefs/` a symlink to an external directory and every
    target under it is correctly beneath the resolved briefs root while the
    root has escaped the repository.

    Both halves are strict. `relative_to` succeeds on equal paths, so each
    comparison rejects its equal case separately: a briefs root symlinked to
    the repository root would otherwise admit any file in the repository, and
    a target symlinked to the briefs directory is not a file beneath it.
    """
    try:
        root_resolved = root.resolve()
        briefs_root = (root_resolved / "docs" / "product" / "briefs").resolve()
        # The briefs root is confined before the candidate is resolved, so a
        # briefs root that already escaped never sends resolution walking
        # through an untrusted tree.
        if briefs_root == root_resolved:
            return False
        briefs_root.relative_to(root_resolved)
        candidate = (root_resolved / rel_path).resolve()
        if candidate == briefs_root:
            return False
        candidate.relative_to(briefs_root)
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def _iter_preamble_lines(text: str) -> Iterator[str]:
    """Yield each preamble line with HTML comments hidden, in order.

    The preamble is the lines before the first `## ` heading, outside fenced
    blocks. A line that a fence or a multi-line comment hides is yielded as an
    empty string, so a caller that asks what directly follows a line never sees
    past hidden text.
    """
    fence_char: str | None = None
    fence_min_len = 0
    in_ml_comment = False
    for line in text.splitlines():
        if not in_ml_comment:
            fm = _FENCE_RE.match(line)
            if fm:
                marker = fm.group(1)
                char = marker[0]
                length = len(marker)
                if fence_char is None:
                    fence_char, fence_min_len = char, length
                    yield ""
                    continue
                rest = line[fm.end():]
                if char == fence_char and length >= fence_min_len and not rest.strip():
                    fence_char, fence_min_len = None, 0
                    yield ""
                    continue
        if fence_char is not None:
            yield ""
            continue
        if in_ml_comment:
            if "-->" in line:
                remainder = line[line.index("-->") + 3:]
                remainder_clean = _HTML_COMMENT_RE.sub("", remainder)
                in_ml_comment = "<!--" in remainder_clean
            yield ""
            continue
        if _SECTION_HEADING_RE.match(line):
            return
        clean = _HTML_COMMENT_RE.sub("", line)
        if "<!--" in clean:
            clean = clean[:clean.index("<!--")]
            in_ml_comment = True
        yield clean


def _parse_preamble_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    field_re = re.compile(r"^- \*\*(?P<name>[^*]+):\*\*\s*(?P<value>.*)$")
    for clean in _iter_preamble_lines(text):
        match = field_re.match(clean)
        if match:
            fields.setdefault(match.group("name").strip().lower(), match.group("value").strip())
    return fields


def _parse_generic_status(text: str, kind: str) -> str | None:
    if kind == "spec":
        status, _ = _parse_spec_status(text)
        return status
    value = _parse_preamble_fields(text).get("status")
    if not value:
        return None
    if "→" in value:
        if value.rstrip().endswith("→"):
            return None
        segments = _TRANSITION_ARROW_RE.findall(value)
        return segments[-1] if segments else None
    return value.split()[0] if value.split() else None


# Every attribute _cooling_projection reads off an accepted record. A record
# missing one raises AttributeError from inside the projection, which the
# top-level handler reports as configuration_mismatch with exit 2 — a record
# problem presented as a configuration one, and with no finding naming the file.
_COOLING_RECORD_FIELDS = (
    "delivery_id",
    "locator",
    "aliases",
    "disposition",
    "post_closeout_result",
    "completion_event",
    "completion_evidence_ref",
    "review_on",
    "exception",
)


_COOLING_PAIRS = frozenset(
    {
        ("cool-30-days", "Cooling"),
        ("cool-30-days", "Retired"),
        ("retain-exception", "Retired"),
        ("retain-exception", "Reclassified"),
    }
)


def _cooled_locators(
    root: Path, module: Any, records_out: list[Any] | None = None
) -> tuple[frozenset[Path], tuple[RoutingFinding, ...]]:
    """Read accepted lifecycle records and return their resolved artifact paths."""
    lifecycle_dir = root / "docs" / "lifecycle"
    if not lifecycle_dir.exists() and not lifecycle_dir.is_symlink():
        return frozenset(), ()
    try:
        resolved_root = root.resolve()
        resolved_lifecycle = lifecycle_dir.resolve()
        resolved_lifecycle.relative_to(resolved_root)
        if not lifecycle_dir.is_dir():
            raise ValueError("lifecycle is not a directory")
        records = sorted(lifecycle_dir.glob("*.json"))
    except (OSError, ValueError, RuntimeError):
        return frozenset(), (_finding("cooling_state_unavailable"),)
    cooled: set[Path] = set()
    findings: list[RoutingFinding] = []
    cooling_state_unavailable = False
    for record_path in records:
        relative_path = record_path.relative_to(root).as_posix()
        if record_path.is_symlink() or not record_path.is_file():
            findings.append(_finding("invalid_lifecycle_record", relative_path))
            continue
        try:
            result = module.load_record(root, record_path)
        except Exception:
            # The module can be an older cooling.py resolved from an installed
            # skills tree, so its behaviour is not this engine's to assume. The
            # callable guard proves the name exists, not that it returns rather
            # than raises. Unhandled, this left analyze() as
            # `configuration_mismatch` and exit 2 — a record problem reported as
            # a configuration one, with no finding naming the file.
            findings.append(_finding("invalid_lifecycle_record", relative_path))
            continue
        record = getattr(result, "record", None)
        if getattr(result, "code", None) == "cooling-state-unavailable":
            cooling_state_unavailable = True
            continue
        if (
            getattr(result, "code", None) is not None
            or record is None
            or any(not hasattr(record, name) for name in _COOLING_RECORD_FIELDS)
        ):
            findings.append(_finding("invalid_lifecycle_record", relative_path))
            continue
        if records_out is not None:
            records_out.append(record)
        if (record.disposition, record.post_closeout_result) not in _COOLING_PAIRS:
            continue
        for locator in (record.locator, *record.aliases):
            try:
                member = (root / locator).resolve()
            except (OSError, RuntimeError):
                continue
            if member.exists():
                cooled.add(member)
    if cooling_state_unavailable:
        # The complete record walk retains independent path-specific findings,
        # but no partial cooled set is safe to use when authority is unavailable.
        findings.append(_finding("cooling_state_unavailable"))
        return frozenset(), tuple(findings)
    return frozenset(cooled), tuple(findings)


def _load_cooling_module(load: Callable[[str, tuple[str, ...]], Any]) -> Any:
    """Load `close_work.py` and `cooling.py` as siblings through the caller's confined loader.

    `load(file_name, callable_names)` returns the module or raises. `cooling.py`
    finds its `close_work.py` lazily under the name `cooling_close_work`, and takes
    it only when that module's `__file__` is the sibling path it would load itself,
    so the confined module is registered first. The caller restores the name.
    """
    close_work = load("close_work.py", _CLOSE_WORK_CALLABLES)
    sys.modules["cooling_close_work"] = close_work
    module = load("cooling.py", _COOLING_MODULE_CALLABLES)
    sibling = str(Path(module.__file__).with_name("close_work.py"))
    if getattr(close_work, "__file__", None) != sibling:
        raise RuntimeError("cooling module unavailable")
    return module


def _resolve_cooled_state(
    root: Path,
    records_out: list[Any] | None = None,
    module_out: list[Any] | None = None,
    load: Callable[[str, tuple[str, ...]], Any] | None = None,
) -> tuple[frozenset[Path], tuple[RoutingFinding, ...]]:
    """Resolve cooling support once, then load the repository's cooled set.

    Without a `load` function, or when it fails, the result is the
    `cooling_state_unavailable` finding and no cooled artifact.
    """
    # An absent lifecycle directory is not a cooling failure, so decide it
    # before resolving the module. Resolving first meant an adopter with no
    # lifecycle records at all got `cooling_state_unavailable` on every run
    # whenever the closure was not installed. An absent lifecycle directory
    # must not raise that finding, while a directory that exists whose every
    # resolution route fails must; the two inputs overlapped here.
    lifecycle_dir = root / "docs" / "lifecycle"
    if not lifecycle_dir.exists() and not lifecycle_dir.is_symlink():
        return frozenset(), ()
    previous = sys.modules.get("cooling_close_work")
    try:
        if load is None:
            raise RuntimeError("cooling module unavailable")
        module = _load_cooling_module(load)
        if module_out is not None:
            module_out.append(module)
        return _cooled_locators(root, module, records_out)
    except Exception:
        return frozenset(), (_finding("cooling_state_unavailable"),)
    finally:
        if previous is None:
            sys.modules.pop("cooling_close_work", None)
        else:
            sys.modules["cooling_close_work"] = previous


def _parse_source_authority_status(
    text: str,
) -> tuple[dict[str, object] | None, str | None, str | None, str | None]:
    if "```toml source-authority" not in text:
        return None, "source_authority_migration_required", None, None
    try:
        authority = parse_source_authority(text)
    except ValueError:
        return None, "invalid_source_authority", None, None
    refresh: dict[str, object] = {
        "compared_revision": authority.source_revision,
        "conflict": any(
            conflict.get("status") == "unresolved"
            for conflict in authority.conflicts
        ),
    }
    if authority.accepted_revision is not None:
        refresh["accepted_revision"] = authority.accepted_revision
    return refresh, None, authority.source_ref, authority.source_revision


def _normalized_optional_artifact_value(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if stripped.lower() in {"", "none"}:
        return None
    return stripped


def _resolved_provenance_parent(
    value: str | None, *, require_local_brief: bool
) -> str | None:
    """The one resolved form of a provenance parent value.

    Every consumer of a provenance parent reads it through this function --
    the path check, the source-vs-artifact equality comparison, and the brief
    child-state attribution. Resolving inside the path check alone is what
    caused the defect this replaces: the raw `brief:<slug>` value stayed in
    scope, and the equality check a few lines below compared a typed header
    against a path-form `source.parent`, reporting `provenance_mismatch` for
    every migrated spec. Handing the caller a resolved value is what stops the
    next consumer reaching for an unresolved one -- there is none left in scope
    to reach for.

    `require_local_brief` is the spec-provenance gate. Only there does
    `brief:<slug>` denote a path. At the shared helper's other call sites --
    `workspace.toml` entry, dependency, legacy-queue and receipt paths -- a
    slug is meaningless, so the value is returned untouched and
    `_is_canonical_local_brief_path` keeps refusing it.

    A value that is neither admitted form is returned unchanged, so it still
    mismatches and is still refused by the path check.
    """
    normalized = _normalized_optional_artifact_value(value)
    if normalized is None or not require_local_brief:
        return normalized
    return _normalized_brief_pointer(normalized)


def _path_presence(path: Path) -> str:
    """Return `present`, `missing`, or `unreadable` for one confined path.

    `Path.exists()` swallows every `OSError` on newer interpreters, which would
    report a file under an unsearchable directory as missing. `stat` raises on
    every supported version, so only an absent name or one the filesystem
    cannot hold reads as missing; any other failure is an unreadable artifact.
    """
    try:
        path.stat()
    except OSError as exc:
        if exc.errno in (errno.ENOENT, errno.ENOTDIR, errno.ENAMETOOLONG, errno.EINVAL):
            return "missing"
        return "unreadable"
    return "present"


def _metadata_from_root(root: Path, entry: WorkspaceEntry) -> ArtifactMetadata | None:
    artifact_path = _confined_artifact_path(root, entry.path)
    if artifact_path is None:
        return ArtifactMetadata(
            path=entry.path,
            kind=entry.kind,
            status=None,
            exists=False,
            readable=False,
            invalid_path=True,
        )
    presence = _path_presence(artifact_path)
    if presence == "unreadable":
        return ArtifactMetadata(
            path=entry.path,
            kind=entry.kind,
            status=None,
            exists=True,
            readable=False,
        )
    if presence == "missing":
        return ArtifactMetadata(path=entry.path, kind=entry.kind, status=None, exists=False)
    try:
        text = artifact_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ArtifactMetadata(
            path=entry.path,
            kind=entry.kind,
            status=None,
            exists=True,
            readable=False,
        )
    status = _parse_generic_status(text, entry.kind)
    plan_exists = None
    plan_readable = True
    fields = _parse_preamble_fields(text)
    parent = _normalized_optional_artifact_value(
        fields.get("brief") or fields.get("source parent") or fields.get("parent")
    )
    ref = fields.get("source ref") or fields.get("ref")
    revision = fields.get("source revision") or fields.get("revision")
    refresh_conflict = fields.get("refresh conflict", "").lower() == "true"
    resolution = fields.get("resolution")
    authority_status = None
    authority_error = None
    if entry.source.mode == "tracker-origin":
        authority_status, authority_error, authority_ref, authority_revision = (
            _parse_source_authority_status(text)
        )
        if authority_status is not None:
            ref = authority_ref
            revision = authority_revision
        refresh_conflict = bool(
            authority_status is not None and authority_status.get("conflict")
        )
    plan_invalid_path = False
    if entry.kind == "spec":
        plan_path = _confined_artifact_path(
            root, entry.path.removesuffix("/spec.md") + "/plan.md"
        )
        if plan_path is None:
            plan_invalid_path = True
            plan_exists = False
        else:
            plan_exists = plan_path.exists()
            if plan_exists:
                try:
                    plan_readable = plan_path.is_file()
                    if plan_readable:
                        with plan_path.open("rb") as handle:
                            handle.read(0)
                except OSError:
                    plan_readable = False
    return ArtifactMetadata(
        path=entry.path,
        kind=entry.kind,
        status=status,
        exists=True,
        readable=True,
        plan_invalid_path=plan_invalid_path,
        plan_readable=plan_readable,
        plan_exists=plan_exists,
        parent=parent,
        ref=ref,
        revision=revision,
        refresh_conflict=refresh_conflict,
        resolution=resolution,
        authority_status=authority_status,
        authority_error=authority_error,
    )


def _captured_membership_form(path: str | None) -> str | None:
    """Classify a canonical membership's path from the path alone, opening nothing.

    `None` is a path that is not a captured-item reference; `migrated` names a
    captured-item file directly in the captured-item directory; anything else
    that is a captured-item reference is `unmigrated`.
    """
    if path is None or not _is_captured_item_reference(path):
        return None
    directory, _, name = path.rpartition("/")
    if directory == _CAPTURED_DIR and _CAPTURED_FILE_RE.fullmatch(name):
        return "migrated"
    return "unmigrated"


def _captured_record_metadata(root: Path, entry: WorkspaceEntry) -> ArtifactMetadata:
    """Metadata for a migrated captured membership, read from its record."""
    path = entry.path or ""
    # Presence is decided without following a link: a linked or dangling record
    # is present, and the confined reader below reports it unreadable.
    if not os.path.lexists(root / path):
        return ArtifactMetadata(path=path, kind=entry.kind, status=None, exists=False)
    # Not cooled by construction: every caller skips a cooled membership first.
    item, finding = read_captured_item(root, path.rpartition("/")[2], frozenset())
    if finding is not None:
        return ArtifactMetadata(
            path=path, kind=entry.kind, status=None, exists=True,
            readable=finding.code != "unreadable_artifact",
            captured_finding=finding,
        )
    return ArtifactMetadata(
        path=path, kind=entry.kind, status=item["status"], exists=True,
        resolution=item["resolution"], captured_kind=item["kind"],
    )


def _artifact_metadata(
    entry: WorkspaceEntry,
    root: Path | None,
    *,
    registered: bool = True,
) -> ArtifactMetadata | None:
    """Read an artifact's metadata. `registered` is False for a dependency probe.

    A registered, non-cooled captured membership reads from its record when
    migrated and is not opened at all when unmigrated.
    """
    if root is None:
        return None
    if registered:
        form = _captured_membership_form(entry.path)
        if form == "unmigrated":
            return None
        if form == "migrated":
            return _captured_record_metadata(root, entry)
    else:
        # A probe of a file in the captured-item directory is a confined read
        # too, and only under the file's exact name; any other spelling of it is
        # refused, so the outcome does not depend on the filesystem.
        spelling = _captured_dir_spelling(entry.path)
        if spelling == "variant":
            return ArtifactMetadata(
                path=entry.path, kind=entry.kind, status=None, exists=True, readable=False
            )
        if spelling == "canonical":
            return _captured_record_metadata(root, entry)
    return _metadata_from_root(root, entry)


def _metadata_from_membership(membership: WorkspaceMembership) -> ArtifactMetadata | None:
    status = _membership_status(membership)
    if status is None:
        return None
    return ArtifactMetadata(
        path=membership.entry.path,
        kind=membership.entry.kind,
        status=status,
        exists=True,
    )


_COORDINATION_RECEIPT_FIELDS = frozenset(
    {
        "id",
        "remote_kind",
        "remote_ref",
        "accepted_revision",
        "required_status",
        "reported_status",
        "reviewed_by",
        "reviewed_at",
        "refresh_conflict",
    }
)


_COORDINATION_FENCE_RE = re.compile(
    r"^ {0,3}(?P<marker>`{3,}|~{3,})(?P<info>[^\r\n]*)$"
)


_RFC3339_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def _parse_reviewed_at(value: object) -> bool:
    if not isinstance(value, str) or not _is_bounded_text(value, 100):
        return False
    if not _RFC3339_DATETIME_RE.fullmatch(value):
        return False
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _coordination_receipt_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    fence_marker: str | None = None
    fence_char: str | None = None
    capture = False
    captured: list[str] = []
    for line in text.splitlines():
        match = _COORDINATION_FENCE_RE.match(line)
        if fence_marker is None:
            if not match:
                continue
            marker = match.group("marker")
            info = match.group("info").strip()
            fence_marker = marker
            fence_char = marker[0]
            capture = info == "toml coordination-receipts"
            captured = []
            continue
        if match:
            marker = match.group("marker")
            info = match.group("info").strip()
            if (
                marker[0] == fence_char
                and len(marker) >= len(fence_marker)
                and info == ""
            ):
                if capture:
                    blocks.append("\n".join(captured))
                fence_marker = None
                fence_char = None
                capture = False
                captured = []
                continue
        if capture:
            captured.append(line)
    return blocks


def _validated_receipt_match(
    receipt: object,
    dep: Dependency,
    seen: set[str],
) -> tuple[bool, bool]:
    if not isinstance(receipt, dict) or set(receipt) != _COORDINATION_RECEIPT_FIELDS:
        return False, False
    receipt_id = receipt.get("id")
    if not _is_bounded_text(receipt_id, 200) or receipt_id in seen:
        return False, False
    seen.add(receipt_id)
    if receipt.get("remote_kind") not in {"brief", "spec"}:
        return False, False
    if not _is_safe_locator(receipt.get("remote_ref")):
        return False, False
    if not _is_bounded_text(receipt.get("accepted_revision"), 200):
        return False, False
    if not _is_bounded_text(receipt.get("reviewed_by"), 200):
        return False, False
    if not _parse_reviewed_at(receipt.get("reviewed_at")):
        return False, False
    if receipt.get("required_status") != "Shipped":
        return False, False
    if receipt.get("reported_status") != "Shipped":
        return False, False
    if receipt.get("refresh_conflict") is not False:
        return False, False
    matches = (
        receipt_id == dep.receipt_id
        and receipt.get("remote_kind") == dep.kind
        and receipt.get("accepted_revision") == dep.accepted_revision
    )
    return True, matches


def _cross_repo_receipt_satisfied(
    dep: Dependency,
    root: Path | None,
) -> tuple[bool, RoutingFinding | None]:
    if root is None or dep.containing_brief is None or dep.path != dep.containing_brief:
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    if not _is_canonical_local_brief_path(dep.path):
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    brief_path = _confined_artifact_path(root, dep.containing_brief)
    if brief_path is None:
        return False, _finding("invalid_artifact_path", dep.containing_brief, "receipt path")
    if not brief_path.exists():
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    try:
        text = brief_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    blocks = _coordination_receipt_blocks(text)
    if len(blocks) != 1:
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    try:
        parsed = tomllib.loads(blocks[0])
    except tomllib.TOMLDecodeError:
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    if set(parsed) != {"coordination_receipts"}:
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    receipts = parsed.get("coordination_receipts")
    if not isinstance(receipts, list):
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    seen: set[str] = set()
    matched = False
    for receipt in receipts:
        valid, matches = _validated_receipt_match(receipt, dep, seen)
        if not valid:
            return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
        matched = matched or matches
    if not matched:
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    return True, None


def _membership_status(membership: WorkspaceMembership) -> str | None:
    if membership.collection == "work.shipped":
        return "Shipped"
    if membership.collection == "brief_queue.draft":
        return "Draft"
    if membership.collection == "brief_queue.ready":
        return "Ready"
    if membership.collection == "brief_queue.executing":
        return "Executing"
    if membership.collection == "brief_queue.shipped":
        return "Shipped"
    if membership.collection == "brief_queue.withdrawn":
        return "Withdrawn"
    if membership.collection == "brief_queue.cancelled":
        return "Cancelled"
    return None


def _dependency_terminal_satisfied(
    kind: str,
    status: str | None,
    metadata: ArtifactMetadata,
) -> bool:
    if kind == "defect":
        return status == "Closed" and metadata.resolution == "fixed"
    terminals = _TERMINAL_STATUS_BY_KIND.get(kind, set())
    return status in terminals


def _provenance_path_is_invalid(
    root: Path | None,
    path: str | None,
    *,
    require_local_brief: bool = False,
) -> bool:
    if path is None:
        return False
    # `brief:<slug>` is normalized to its canonical path *here*, at the
    # provenance read, before any lexical check runs — never inside
    # `_is_canonical_local_brief_path`, which also guards `workspace.toml`
    # entry and dependency paths where a slug has no meaning.
    #
    # Callers inside this module pass a value already resolved by
    # `_resolved_provenance_parent`, and resolving is idempotent — a path form
    # has no `brief:` prefix to match. This line is kept so the helper stays
    # correct for a direct caller that holds only the declared value.
    candidate = _normalized_brief_pointer(path) if require_local_brief else path
    if not _is_repository_relative_path(candidate):
        return True
    if require_local_brief:
        if not _is_canonical_local_brief_path(candidate):
            return True
        # The boundary is the resolved briefs directory, stricter
        # than `_confined_artifact_path`'s repository-root confinement.
        return root is not None and not _confined_briefs_path(root, candidate)
    return root is not None and _confined_artifact_path(root, path) is None


def _dependency_metadata_safety_finding(
    path: str,
    kind: str,
    metadata: ArtifactMetadata | None,
    root: Path | None,
) -> RoutingFinding | None:
    if metadata is not None and metadata.captured_finding is not None:
        return metadata.captured_finding
    if metadata is not None and metadata.invalid_path:
        return _finding("invalid_artifact_path", path, "dependency path")
    if metadata is None or not metadata.exists:
        return _finding("missing_dependency", path, "dependency target missing")
    if not metadata.readable:
        return _finding("unreadable_artifact", path, "dependency unreadable")
    if _provenance_path_is_invalid(
        root,
        metadata.parent,
        require_local_brief=kind == "spec",
    ):
        return _finding("invalid_artifact_path", metadata.parent or "", "dependency parent")
    if metadata.refresh_conflict:
        return _finding("refresh_conflict", path, "dependency refresh conflict")
    return None


def _completion_receipt_satisfied(
    dep: Dependency,
) -> tuple[bool, RoutingFinding | None]:
    """Validate an absent local dependency's receipt and decide satisfaction."""
    receipt = dep.receipt
    if receipt == _MALFORMED_COMPLETION_RECEIPT or not isinstance(receipt, dict):
        return False, _finding(
            "invalid_completion_receipt", dep.path, "completion receipt shape is invalid"
        )
    if (
        re.fullmatch(_COMPLETION_RECEIPT_DELIVERY_ID_RE, receipt["delivery_id"])
        is None
        or receipt["completion_event"] not in _COMPLETION_RECEIPT_EVENTS
        or re.fullmatch(
            _COMPLETION_RECEIPT_EVIDENCE_REF_RE, receipt["evidence_ref"]
        )
        is None
        or receipt["outcome"] not in _COMPLETION_RECEIPT_OUTCOMES
    ):
        return False, _finding(
            "invalid_completion_receipt", dep.path, "completion receipt value is invalid"
        )
    if receipt["outcome"] == "completed":
        return True, None
    return False, _finding(
        "unsatisfied_dependency", dep.path, "dependency delivery did not complete"
    )


def _dependency_is_satisfied(
    dep: Dependency,
    by_path: dict[str, list[WorkspaceMembership]],
    structurally_blocked_paths: set[str],
    root: Path | None,
    cooled: frozenset[Path],
    briefs_with_cooled_children: frozenset[str] = frozenset(),
    cooled_scope_unknown: frozenset[str] = frozenset(),
    brief_child_states: dict[str, set[str]] | None = None,
) -> tuple[bool, RoutingFinding | None]:
    """Decide whether one dependency is satisfied, or return the finding why not.

    A captured-item file that no membership names settles by its own `Status:`
    and `Resolution:`; every other dependency follows its membership or its
    artifact's terminal state. An unregistered brief also has to keep the brief
    child-state rule, which reads only its `Status:` and its child specs.
    """
    if (
        dep.type != "cross-repo"
        and any(
            _captured_membership_form(match.entry.path) == "unmigrated"
            for match in by_path.get(dep.path, [])
        )
        and not (root is not None and _confined_artifact_path(root, dep.path) in cooled)
    ):
        return False, _finding("unsatisfied_dependency", dep.path, "captured item unmigrated")
    if dep.path in structurally_blocked_paths:
        return False, _finding("unsatisfied_dependency", dep.path, "dependency has findings")
    # Fail closed when a brief's child scope is unknown. A cooled child may
    # have changed the brief's terminal state without the workspace membership
    # reflecting it, so the brief's apparent state is not evidence.
    #
    # The refused set has two parts. Per brief: the `source.parent` values
    # declared by cooled spec memberships that resolve to a registered brief.
    # Repository-wide: every `kind = "brief"` dependency, while any cooled
    # entry's scope is unestablished — because the brief such an entry belongs
    # to is exactly what is unknown. Neither part is initiative-scoped and
    # neither considers initiative status: a cooled spec in a paused initiative
    # that declares a brief owned by an active one still refuses that brief. A
    # declared value is unvalidated against the artifact body, because the
    # cooled branch of `_structural_findings` returns before the provenance
    # check —
    # for a cooled child the declaration is unverifiable by construction, which
    # is the point of failing closed rather than trusting it.
    # Two ways a brief dependency's child scope is not established. A cooled
    # child that *declares* this brief makes that brief's scope unevaluable.
    # A cooled child whose parent is undeclared or unresolvable makes *every*
    # brief's scope unevaluable, because the brief it belongs to is exactly
    # what is unknown; a maintainer clears that by declaring a resolving path,
    # or `none` when the spec has no parent.
    brief_scope_unknown = dep.kind == "brief" and (
        dep.path in briefs_with_cooled_children or bool(cooled_scope_unknown)
    )
    cooled_dependency = (
        root is not None and _confined_artifact_path(root, dep.path) in cooled
    )
    if dep.type == "cross-repo":
        if cooled_dependency:
            # A cooled body is never opened, with no exception.
            # `_cross_repo_receipt_satisfied`
            # opens the brief body unconditionally, and the evidence it needs
            # is only there: the four-field receipt match asserted for this one
            # dependency. A lifecycle record cannot stand in — it is completion
            # evidence for the brief as a whole, and projecting the receipt
            # from its coordination surface is deliberately not done here.
            # Refusing surfaces
            # a real inconsistency rather than concealing one: a brief with a
            # live cross-repo dependant is retained as an exception, not cooled.
            return False, _finding(
                "unsatisfied_dependency",
                dep.path,
                "cooled dependency receipt is not readable",
            )
        return _cross_repo_receipt_satisfied(dep, root)

    matches = by_path.get(dep.path, [])
    if matches and not any(match.entry.kind == dep.kind for match in matches):
        return False, _finding("unsatisfied_dependency", dep.path, "dependency kind mismatch")
    if (
        not matches
        and root is not None
        and dep.kind
        and _captured_dir_spelling(dep.path) == "canonical"
        and not cooled_dependency
    ):
        # An unregistered captured item settles by its own file: one read, and
        # only `Closed` with `Resolution: fixed` satisfies.
        item, finding = read_captured_item(
            root, dep.path[len(_CAPTURED_DIR) + 1:], cooled
        )
        if finding is not None:
            return False, finding
        if item.get("cooled") or "status" not in item:
            # The reader re-checks the cooled set; a path that became cooled
            # between the two checks is refused without opening the file.
            return False, _finding(
                "unsatisfied_dependency", dep.path, "captured item became cooled"
            )
        if item["status"] == "Closed" and item["resolution"] == "fixed":
            return True, None
        return False, _finding(
            "unsatisfied_dependency", dep.path, "captured item is not closed as fixed"
        )
    if dep.kind == "defect" and not any(
        match.collection == "backlog.closed" for match in matches
    ):
        if cooled_dependency:
            return False, _finding(
                "unsatisfied_dependency", dep.path, "defect lacks closed membership"
            )
        probe = WorkspaceEntry(
            path=dep.path,
            kind=dep.kind,
            source=SourceRecord(mode="repo-origin"),
            summary="dependency probe",
            needs=[],
        )
        metadata = _artifact_metadata(probe, root, registered=False)
        safety_finding = _dependency_metadata_safety_finding(
            dep.path, dep.kind, metadata, root
        )
        if safety_finding is not None:
            return False, safety_finding
        return False, _finding(
            "unsatisfied_dependency", dep.path, "defect lacks closed membership"
        )
    # Decide every cooled dependency here, before any probe is built. Keying
    # this on `dep.kind == "spec"` let intent/research/design fall through to
    # the probe below and read the cooled body. The per-kind *outcome* is
    # preserved: `defect` already returned above when it lacks a closed
    # membership, so reaching this line means the dependency is satisfied by
    # its lifecycle record — which is completion evidence, and the only
    # evidence available once the body may not be read.
    if cooled_dependency:
        return True, None
    if matches:
        metadata = _artifact_metadata(matches[0].entry, root)
    else:
        probe = WorkspaceEntry(
            path=dep.path,
            kind=dep.kind,
            source=SourceRecord(mode="repo-origin"),
            summary="dependency probe",
            needs=[],
        )
        metadata = _artifact_metadata(probe, root, registered=False)
    safety_finding = _dependency_metadata_safety_finding(
        dep.path, dep.kind, metadata, root
    )
    if safety_finding is not None:
        if (
            not matches
            and dep.receipt is not None
            and safety_finding.code == "missing_dependency"
        ):
            return _completion_receipt_satisfied(dep)
        return False, safety_finding
    if brief_scope_unknown:
        # Deliberately after the safety check: a missing, unreadable or
        # invalid-path brief has a concrete cause, and reporting "re-establish
        # the child scope" for a brief that does not exist sends the maintainer
        # to the wrong repair.
        return False, _finding(
            "unsatisfied_dependency", dep.path, "brief child scope is unknown"
        )
    if not matches and dep.kind == "brief" and brief_child_states is not None:
        collection = f"brief_queue.{(metadata.status or '').lower()}"
        if collection in _ALLOWED_KIND_BY_COLLECTION and not _brief_child_scope_is_valid(
            collection,
            brief_child_states.get(dep.path, set()),
            scope_unevaluable=dep.path in briefs_with_cooled_children,
        ):
            return False, _finding(
                "unsatisfied_dependency", dep.path, "brief child state rule broken"
            )
    status = metadata.status
    if status is None and matches:
        status = _membership_status(matches[0])
    if _dependency_terminal_satisfied(dep.kind, status, metadata):
        return True, None
    return False, _finding("unsatisfied_dependency", dep.path, "dependency not terminal")


def _dependency_cycles(
    memberships: list[WorkspaceMembership],
    header_edges: dict[str, tuple[Dependency, ...]],
) -> set[str]:
    graph: dict[str, list[str]] = {}
    paths = {membership.entry.path for membership in memberships}
    for membership in memberships:
        graph[membership.entry.path] = [
            dep.path for dep in header_edges.get(membership.entry.path, ())
            if dep.type == "local" and dep.path in paths
        ]
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: set[str] = set()

    def visit(path: str, stack: list[str]) -> None:
        if path in visiting:
            cycles.update(stack[stack.index(path):])
            return
        if path in visited:
            return
        visiting.add(path)
        for child in graph.get(path, []):
            visit(child, [*stack, child])
        visiting.remove(path)
        visited.add(path)

    for path in graph:
        visit(path, [path])
    return cycles


_TYPED_REFERENCE_RE = re.compile(
    r"(?P<kind>spec|brief|intent|outcome|opportunity|capability):"
    r"(?P<slug>[a-z0-9][a-z0-9-]*)"
)


_CAPTURED_SEGMENT_RE = re.compile(r"[A-Za-z0-9._-]+")


_LIVE_INTENT_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\.md")


_COORDINATION_TOKEN_RE = re.compile(r"[A-Za-z0-9._:/@+-]{1,200}")


_HEADER_FIELD_RE = re.compile(r"^- \*\*(?P<name>[^*]+):\*\*\s*(?P<value>.*)$")


_BRIEFS_DIR = "docs/product/briefs"


_INTENTS_DIR = "docs/product/intents"


@dataclasses.dataclass(frozen=True)
class ResolutionIndex:
    """Brief slugs and live-intent `(kind, slug)` pairs, built once per run.

    A directory whose listing failed, or one of whose admitted entries could not
    be read, is flagged unreadable: a reference into it is never a missing target.
    """

    briefs: dict[str, tuple[str, ...]]
    intents: dict[tuple[str, str], tuple[str, ...]]
    briefs_unreadable: bool = False
    intents_unreadable: bool = False


@dataclasses.dataclass(frozen=True)
class HeaderDependencies:
    """One waiting item's header edges and the findings its header earned."""

    dependencies: tuple[Dependency, ...]
    findings: tuple[RoutingFinding, ...]


def _normalized_field_value(value: str | None, *, first_word: bool = False) -> str:
    """A preamble field value with one pair of surrounding backticks stripped.

    The preamble walk already hides HTML comments. `Kind:` and `Level:` take
    their first word.
    """
    text = (value or "").strip()
    if len(text) >= 2 and text[0] == "`" and text[-1] == "`":
        text = text[1:-1]
    if first_word:
        words = text.split()
        return words[0] if words else ""
    return text


def _intent_kind(fields: dict[str, str]) -> str:
    kind = _normalized_field_value(fields.get("kind"), first_word=True)
    if kind in ("outcome", "opportunity"):
        return kind
    if _normalized_field_value(fields.get("level"), first_word=True) == "capability":
        return "capability"
    return "intent"


def _admitted_directory_names(root: Path, relative_dir: str) -> list[str] | None:
    """Names in `relative_dir` that match the live intent name pattern.

    `[]` when the directory is absent, `None` when it cannot be listed or its
    resolved location leaves the repository.
    """
    directory = root / relative_dir
    if _path_presence(directory) == "missing" and not directory.is_symlink():
        return []
    try:
        root_resolved = root.resolve()
        resolved = directory.resolve()
        resolved.relative_to(root_resolved)
        if resolved == root_resolved or not resolved.is_dir():
            return None
        names = sorted(entry.name for entry in resolved.iterdir())
    except (OSError, RuntimeError, ValueError):
        return None
    return [name for name in names if _LIVE_INTENT_NAME_RE.fullmatch(name)]


def _read_directory_entry(root: Path, relative_dir: str, name: str) -> str | None:
    """Read one admitted entry, or `None` when it is refused or unreadable."""
    relative = f"{relative_dir}/{name}"
    if relative_dir == _BRIEFS_DIR and not _confined_briefs_path(root, relative):
        return None
    candidate = _confined_artifact_path(root, relative)
    if candidate is None:
        return None
    try:
        candidate.relative_to((root.resolve() / relative_dir).resolve())
        if not candidate.is_file():
            return None
        return candidate.read_text(encoding="utf-8", errors="replace")
    except (OSError, RuntimeError, ValueError):
        return None


def build_resolution_index(
    root: Path, *, cooled: frozenset[Path] = frozenset()
) -> ResolutionIndex:
    """List `docs/product/briefs/` and `docs/product/intents/` once.

    A cooled entry's body is never opened: a cooled brief is indexed by its file
    stem and a cooled intent is left out, since neither can be matched by a
    `Slug:` field it was not allowed to read.
    """
    briefs: dict[str, list[str]] = {}
    intents: dict[tuple[str, str], list[str]] = {}
    unreadable = {_BRIEFS_DIR: False, _INTENTS_DIR: False}
    for relative_dir in (_BRIEFS_DIR, _INTENTS_DIR):
        names = _admitted_directory_names(root, relative_dir)
        if names is None:
            unreadable[relative_dir] = True
            continue
        for name in names:
            relative = f"{relative_dir}/{name}"
            if _confined_artifact_path(root, relative) in cooled:
                if relative_dir == _BRIEFS_DIR:
                    briefs.setdefault(name.removesuffix(".md"), []).append(relative)
                continue
            text = _read_directory_entry(root, relative_dir, name)
            if text is None:
                unreadable[relative_dir] = True
                continue
            fields = _parse_preamble_fields(text)
            slug = _normalized_field_value(fields.get("slug"))
            if relative_dir == _BRIEFS_DIR:
                if "slug" not in fields:
                    slug = name.removesuffix(".md")
                briefs.setdefault(slug, []).append(relative)
            elif "tombstone" not in fields and slug:
                intents.setdefault((_intent_kind(fields), slug), []).append(relative)
    return ResolutionIndex(
        briefs={key: tuple(paths) for key, paths in briefs.items()},
        intents={key: tuple(paths) for key, paths in intents.items()},
        briefs_unreadable=unreadable[_BRIEFS_DIR],
        intents_unreadable=unreadable[_INTENTS_DIR],
    )


def _captured_dir_spelling(path: str) -> str | None:
    """How `path` names the captured-item directory, if it names it at all.

    `canonical` is a captured-item file name directly in the directory, spelled
    exactly. `variant` is any other path that a case-insensitive or
    trailing-dot-dropping filesystem could map into the directory; it is
    refused, because it would reach a captured file under a name the confined
    reader and the cooled check do not compare. `None` is a path elsewhere.
    """
    folded = "/".join(part.rstrip(".").casefold() for part in path.split("/"))
    if not folded.startswith(f"{_CAPTURED_DIR}/"):
        return None
    name = path[len(_CAPTURED_DIR) + 1:] if path.startswith(f"{_CAPTURED_DIR}/") else ""
    return "canonical" if _CAPTURED_FILE_RE.fullmatch(name) else "variant"


def _is_captured_item_reference(item: str) -> bool:
    parts = item.split("/")
    if any(
        part in (".", "..") or _CAPTURED_SEGMENT_RE.fullmatch(part) is None
        for part in parts
    ):
        return False
    if len(parts) == 4 and parts[:2] == ["docs", "specs"] and parts[3] == "spec.md":
        return False
    return parts[:3] not in (
        _BRIEFS_DIR.split("/"),
        _INTENTS_DIR.split("/"),
    )


def _echoable_reference(item: str) -> str:
    """The item as a finding may echo it, or `""` when it must be withheld."""
    if _TYPED_REFERENCE_RE.fullmatch(item) is None and not _is_captured_item_reference(
        item
    ):
        return ""
    return _bounded_finding_identifier(item)


# The captured-item file grammar and the listing of its directory. A captured
# item is one file in `_CAPTURED_DIR`; its preamble fields say what it is. The
# listing is built from the directory and the cooled set only, never from the
# registry, so two registries over one tree give one listing.
_CAPTURED_DIR = "docs/product/captured"


_CAPTURED_FILE_RE = re.compile(r"[a-z0-9][a-z0-9-]*\.md")


_CAPTURED_STATUSES = frozenset({"Open", "Closed"})


_CAPTURED_KINDS = frozenset({"defect", "design", "research", "intent"})


_CAPTURED_RESOLUTIONS = frozenset({"fixed", "declined", "superseded"})


_CAPTURED_PARENT_KINDS = frozenset({"intent", "outcome", "opportunity", "capability"})


# Each shaping type routes to a skill, in the order the spec lists them.
_SHAPING_TYPE_ROUTES = {
    "shape": "intent",
    "research": "desk-research-project-start",
    "strategy": "frame-situation",
    "design": "experience-status",
    "signal": "(signal — no action)",
}


# The captured-item fields, in the order the first failing one is named.
_CAPTURED_FIELD_ORDER = (
    ("status", "Status"),
    ("kind", "Kind"),
    ("type", "Type"),
    ("resolution", "Resolution"),
    ("parent intent", "Parent intent"),
    ("detail", "Detail"),
)


@dataclasses.dataclass(frozen=True)
class CapturedListing:
    """The `captured` object: one entry per file, and the findings they give."""

    items: list[dict[str, Any]]
    findings: tuple[RoutingFinding, ...]


def _captured_field_value(raw: str, name: str) -> str:
    """A preamble field's value: backticks off once, first word for `Kind`."""
    value = raw.strip()
    if len(value) >= 2 and value[0] == "`" and value[-1] == "`":
        value = value[1:-1].strip()
    if name == "kind":
        words = value.split()
        value = words[0] if words else ""
    return value


def parse_captured_item(text: str) -> tuple[dict[str, str | None] | None, str | None]:
    """Check one captured-item file's preamble against the grammar.

    `Resolution:` is required exactly when `Status:` is `Closed`, for every kind.

    Returns `(fields, None)` when valid and `(None, <first failing field>)`
    otherwise. Field lines are counted here through `_iter_preamble_lines`,
    because `_parse_preamble_fields` keeps only the first value of a repeat.
    """
    values: dict[str, list[str]] = {}
    for line in _iter_preamble_lines(text):
        match = _HEADER_FIELD_RE.match(line)
        if match:
            name = match.group("name").strip().lower()
            values.setdefault(name, []).append(
                _captured_field_value(match.group("value"), name)
            )

    def single(name: str) -> str | None:
        found = values.get(name, [])
        return found[0] if len(found) == 1 else None

    status, kind = single("status"), single("kind")
    for key, label in _CAPTURED_FIELD_ORDER:
        found = values.get(key, [])
        value = single(key)
        if len(found) > 1:
            return None, label
        if key == "status" and value not in _CAPTURED_STATUSES:
            return None, label
        if key == "kind" and value not in _CAPTURED_KINDS:
            return None, label
        if key == "type" and found and value not in _SHAPING_TYPE_ROUTES:
            return None, label
        if key == "resolution":
            required = status == "Closed"
            if required != bool(found) or (
                found and value not in _CAPTURED_RESOLUTIONS
            ):
                return None, label
        if key == "parent intent" and found:
            typed = _TYPED_REFERENCE_RE.fullmatch(value or "")
            if typed is None or typed.group("kind") not in _CAPTURED_PARENT_KINDS:
                return None, label
        if key == "detail" and found and not _is_captured_item_reference(value or ""):
            return None, label
    return {
        "status": status,
        "kind": kind,
        "type": single("type"),
        "resolution": single("resolution"),
        "parent_intent": single("parent intent"),
        "detail": single("detail"),
    }, None


def _captured_finding(code: str, path: str, field: str = "") -> RoutingFinding:
    """A finding that echoes `path` only when it fits the reference grammar."""
    return _finding(code, _echoable_reference(path), field)


def read_captured_item(
    root: Path, name: str, cooled: frozenset[Path]
) -> tuple[dict[str, Any], RoutingFinding | None]:
    """List one captured-item file, `name` being a name in the file grammar.

    A cooled file is never opened. Any other is read through the identity-checked
    reader, so a link, a non-regular file, or a swap between check and open is
    unreadable and none of its content is used.
    """
    relative = f"{_CAPTURED_DIR}/{name}"
    entry: dict[str, Any] = {"path": relative, "slug": name.removesuffix(".md")}
    if _confined_artifact_path(root, relative) in cooled:
        return {**entry, "cooled": True}, None
    content = _migration_file_bytes(root, relative)
    try:
        text = content.decode("utf-8") if content is not None else None
    except UnicodeDecodeError:
        text = None
    if text is None:
        return (
            {**entry, "unreadable": True},
            _captured_finding("unreadable_artifact", relative),
        )
    fields, failing = parse_captured_item(text)
    if fields is None:
        return (
            {**entry, "invalid": True},
            _captured_finding("invalid_captured_item", relative, failing or ""),
        )
    routed = fields["type"]
    return {
        **entry,
        "status": fields["status"],
        "kind": fields["kind"],
        "type": routed,
        "routes_to": _SHAPING_TYPE_ROUTES[routed] if routed else None,
        "resolution": fields["resolution"],
        "parent_intent": fields["parent_intent"],
        "detail": fields["detail"],
    }, None


def list_captured_items(root: Path, cooled: frozenset[Path]) -> CapturedListing:
    """List the captured-item directory, one entry per captured-item file."""
    unreadable = CapturedListing(
        [], (_captured_finding("unreadable_artifact", _CAPTURED_DIR),)
    )
    directory = confine_migration_path(root, _CAPTURED_DIR)
    if directory is None:
        return unreadable
    try:
        if not os.path.lexists(directory):
            return CapturedListing([], ())
        if not stat.S_ISDIR(directory.lstat().st_mode):
            return unreadable
        names = sorted(
            entry.name for entry in directory.iterdir()
            if _CAPTURED_FILE_RE.fullmatch(entry.name)
        )
    except OSError:
        return unreadable
    items: list[dict[str, Any]] = []
    findings: list[RoutingFinding] = []
    for name in names:
        item, finding = read_captured_item(root, name, cooled)
        items.append(item)
        if finding is not None:
            findings.append(finding)
    return CapturedListing(items, tuple(findings))


def _header_finding(
    code: str, waiting_path: str, reason: str, item: str | None = None
) -> RoutingFinding:
    echoed = _echoable_reference(item) if item is not None else ""
    return _finding(
        code,
        _bounded_finding_identifier(waiting_path),
        f"{reason}: {echoed}" if echoed else reason,
    )


def _header_field_lines(text: str) -> list[tuple[str, str, bool]]:
    """Every `Depends on:` and `Dependency receipts:` preamble line.

    Each is `(lowercased name, value, followed by an indented non-blank line)`.
    """
    lines = list(_iter_preamble_lines(text))
    found: list[tuple[str, str, bool]] = []
    for position, line in enumerate(lines):
        match = _HEADER_FIELD_RE.match(line)
        if not match:
            continue
        name = match.group("name").strip().lower()
        if name not in ("depends on", "dependency receipts"):
            continue
        following = lines[position + 1] if position + 1 < len(lines) else ""
        wrapped = following[:1] in (" ", "\t") and following.strip() != ""
        found.append((name, match.group("value").strip(), wrapped))
    return found


def _split_items(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _parse_receipt_line(
    waiting_path: str,
    item: str,
    items: set[str],
    receipts: dict[str, tuple[str, tuple[str, ...]]],
) -> RoutingFinding | None:
    """Validate one receipt; record it under its reference when it is sound."""
    tokens = item.split()
    reference = tokens[0]
    keyword = tokens[1] if len(tokens) > 1 else ""
    refuse = lambda reason: _header_finding(  # noqa: E731
        "invalid_dependency", waiting_path, f"dependency receipt {reason}", reference
    )
    if keyword not in ("completion", "coordination"):
        return refuse("has an unknown keyword")
    if len(tokens) != (6 if keyword == "completion" else 5):
        return refuse("has the wrong token count")
    if reference not in items:
        return refuse("names no dependency item")
    if reference in receipts:
        return refuse("repeats a reference")
    typed = _TYPED_REFERENCE_RE.fullmatch(reference)
    if keyword == "coordination":
        if typed is None or typed.group("kind") != "brief":
            return refuse("coordination applies to a brief reference only")
        remote_kind, receipt_id, revision = tokens[2:]
        if remote_kind not in ("brief", "spec"):
            return _header_finding(
                "invalid_entry", waiting_path, "cross-repo need kind is invalid", reference
            )
        for value in (receipt_id, revision):
            if _COORDINATION_TOKEN_RE.fullmatch(value) is None:
                return _header_finding(
                    "invalid_entry", waiting_path, "receipt value is invalid", reference
                )
    elif typed is None and _is_captured_item_reference(reference):
        return refuse("completion does not apply to a captured item")
    receipts[reference] = (keyword, tuple(tokens[2:]))
    return None


def _brief_path_for(slug: str, index: ResolutionIndex) -> str:
    matches = index.briefs.get(slug, ())
    return matches[0] if len(matches) == 1 else f"{_BRIEFS_DIR}/{slug}.md"


def read_header_dependencies(
    root: Path,
    waiting_path: str,
    *,
    index: ResolutionIndex,
    membership_kinds: dict[str, str],
    cooled: frozenset[Path],
) -> HeaderDependencies:
    """Read one waiting item's header edges.

    `membership_kinds` maps each canonical membership path to its `kind`. A
    cooled waiting item is never opened and contributes nothing. A missing or
    unconfined waiting item contributes nothing here: reconciliation reports it.
    """
    waiting_file = _confined_artifact_path(root, waiting_path)
    if waiting_file is None or waiting_file in cooled:
        return HeaderDependencies((), ())
    presence = _path_presence(waiting_file)
    if presence == "missing":
        return HeaderDependencies((), ())
    unreadable = HeaderDependencies(
        (), (_header_finding("unreadable_artifact", waiting_path, "waiting item unreadable"),)
    )
    if presence == "unreadable":
        return unreadable
    try:
        text = waiting_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return unreadable
    return header_dependencies_from_text(
        root,
        waiting_path,
        text,
        index=index,
        membership_kinds=membership_kinds,
        cooled=cooled,
    )


def header_dependencies_from_text(
    root: Path,
    waiting_path: str,
    text: str,
    *,
    index: ResolutionIndex,
    membership_kinds: dict[str, str],
    cooled: frozenset[Path],
) -> HeaderDependencies:
    """Read header edges from a waiting item's text.

    The same rules `read_header_dependencies` applies to the file, so the repair
    can check what a planned header would read as before it writes one.
    """
    findings: list[RoutingFinding] = []
    items: list[str] = []
    receipt_lines: list[str] = []
    for name, value, wrapped in _header_field_lines(text):
        if wrapped:
            label = "Depends on:" if name == "depends on" else "Dependency receipts:"
            findings.append(
                _header_finding(
                    "invalid_dependency",
                    waiting_path,
                    f"an indented line follows {label} and would be dropped",
                )
            )
        if name == "dependency receipts":
            receipt_lines.extend(_split_items(value))
        elif value.split()[:1] and value.split()[0].lower() != "none":
            items.extend(_split_items(value))
    item_set = set(items)
    receipts: dict[str, tuple[str, tuple[str, ...]]] = {}
    for line in receipt_lines:
        finding = _parse_receipt_line(waiting_path, line, item_set, receipts)
        if finding is not None:
            findings.append(finding)
    dependencies: list[Dependency] = []
    for item in items:
        target, finding = _resolve_header_item(
            root, waiting_path, item, index, membership_kinds, cooled
        )
        if finding is not None:
            findings.append(finding)
        if target is None:
            continue
        kind, path, brief_slug = target
        receipt = receipts.get(item)
        if receipt is not None and receipt[0] == "coordination" and brief_slug:
            remote_kind, receipt_id, revision = receipt[1]
            brief_path = _brief_path_for(brief_slug, index)
            dependencies.append(
                Dependency(
                    type="cross-repo",
                    kind=remote_kind,
                    path=brief_path,
                    containing_brief=brief_path,
                    receipt_id=receipt_id,
                    accepted_revision=revision,
                )
            )
            continue
        completion: dict[str, str] | str | None = None
        if receipt is not None and receipt[0] == "completion":
            delivery_id, outcome, event, evidence = receipt[1]
            completion = {
                "delivery_id": delivery_id,
                "outcome": outcome,
                "completion_event": event,
                "evidence_ref": evidence,
            }
            if not all(
                _is_bounded_text(value, _COMPLETION_RECEIPT_MAX_FIELD_LENGTH)
                for value in completion.values()
            ):
                completion = _MALFORMED_COMPLETION_RECEIPT
        dependencies.append(
            Dependency(type="local", kind=kind, path=path, receipt=completion)
        )
    return HeaderDependencies(tuple(dependencies), tuple(findings))


def _resolve_header_item(
    root: Path,
    waiting_path: str,
    item: str,
    index: ResolutionIndex,
    membership_kinds: dict[str, str],
    cooled: frozenset[Path],
) -> tuple[tuple[str, str, str] | None, RoutingFinding | None]:
    """Resolve one item to `(kind, path, brief slug or "")`, or a finding.

    A typed reference with no target keeps the path the satisfaction logic needs
    to report it missing, and a captured item with no file and no membership
    keeps its path with no kind.
    """
    typed = _TYPED_REFERENCE_RE.fullmatch(item)
    if typed is not None:
        ref_kind, slug = typed.group("kind", "slug")
        if ref_kind == "spec":
            return ("spec", f"docs/specs/{slug}/spec.md", ""), None
        if ref_kind == "brief":
            unreadable, matches = index.briefs_unreadable, index.briefs.get(slug, ())
            kind = "brief"
        else:
            unreadable = index.intents_unreadable
            matches = index.intents.get((ref_kind, slug), ())
            kind = "intent"
        if unreadable:
            return None, _header_finding(
                "unreadable_artifact", waiting_path, "dependency directory unreadable", item
            )
        if len(matches) > 1:
            return None, _header_finding(
                "invalid_dependency", waiting_path, "dependency reference is ambiguous", item
            )
        return (kind, matches[0] if matches else item, slug if kind == "brief" else ""), None
    if not _is_captured_item_reference(item):
        return None, _header_finding(
            "invalid_dependency",
            waiting_path,
            "dependency item is neither a typed reference nor a captured-item path",
            item,
        )
    member_kind = membership_kinds.get(item)
    if member_kind:
        return (member_kind, item, ""), None
    spelling = _captured_dir_spelling(item)
    if spelling == "variant":
        return None, _header_finding(
            "unreadable_artifact", waiting_path, "captured item unreadable", item
        )
    captured_file = _confined_artifact_path(root, item)
    if captured_file is None:
        return ("", item, ""), None
    captured_presence = _path_presence(captured_file)
    if captured_presence == "unreadable":
        return None, _header_finding(
            "unreadable_artifact", waiting_path, "captured item unreadable", item
        )
    if captured_presence == "missing":
        return ("", item, ""), None
    kind = ""
    if captured_file not in cooled:
        try:
            if spelling == "canonical":
                # A captured-item file is read only as a confined file.
                content = _migration_file_bytes(root, item)
                if content is None:
                    raise OSError(item)
                text = content.decode("utf-8", errors="replace")
            else:
                text = captured_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None, _header_finding(
                "unreadable_artifact", waiting_path, "captured item unreadable", item
            )
        kind = _normalized_field_value(
            _parse_preamble_fields(text).get("kind"), first_word=True
        )
    if kind not in WORKSPACE_ARTIFACT_KINDS:
        return None, _header_finding(
            "invalid_dependency", waiting_path, "captured item has no kind", item
        )
    return (kind, item, ""), None


def _membership_is_cooled(
    membership: WorkspaceMembership,
    root: Path | None,
    cooled: frozenset[Path],
) -> bool:
    """True when this membership's artifact is named by a lifecycle record.

    The single membership-key rule for the whole engine: resolve through
    `_confined_artifact_path`, because every read site canonicalizes before
    opening and a raw string can never match a resolved cooled path.
    """
    if root is None or not cooled:
        return False
    return _confined_artifact_path(root, membership.entry.path or "") in cooled


def _listed_brief_files(root: Path | None) -> frozenset[str]:
    """Return the paths of the regular files listed in the briefs directory.

    `docs/product/briefs/`, `docs/product/`, and `docs/` must each be a real
    directory, not a symbolic link, resolving beneath the resolved root. Any
    failed condition or `OSError` lists nothing, so a cooled child's scope stays
    unknown. Nothing is opened and no declared value is resolved through the
    filesystem: the caller compares strings against this listing.
    """
    if root is None:
        return frozenset()
    try:
        resolved_root = root.resolve()
        for directory in ("docs/product/briefs", "docs/product", "docs"):
            path = root / directory
            if not stat.S_ISDIR(os.lstat(path).st_mode):
                return frozenset()
            if not path.resolve().is_relative_to(resolved_root):
                return frozenset()
        directory_path = root / "docs/product/briefs"
        return frozenset(
            f"docs/product/briefs/{name}"
            for name in os.listdir(directory_path)  # noqa: PTH208
            if stat.S_ISREG(os.lstat(directory_path / name).st_mode)
        )
    except OSError:
        return frozenset()


def _brief_child_spec_states(
    memberships: list[WorkspaceMembership],
    root: Path | None,
    cooled: frozenset[Path],
) -> tuple[dict[str, set[str]], frozenset[str], frozenset[str]]:
    """Map each brief to its children's observed states; flag unevaluable scope.

    Returns (states, briefs_with_cooled_children, cooled_scope_unknown).

    states maps each brief path to the set of states contributed by its
    non-cooled child spec memberships. A cooled child contributes no state at
    all: its status would come from `_membership_status`, which derives state
    from the collection alone and so fabricates "Shipped" for anything in
    `work.shipped`.

    briefs_with_cooled_children names the briefs a cooled child declares
    through `source.parent` **and whose declaration resolves** to a registered
    brief membership or a listed brief file. A declaration naming no registered
    brief membership and no listed brief file goes to
    cooled_scope_unknown instead. For the resolving briefs `invalid_child_scope`
    is unevaluable and a `kind="brief"` dependency on that brief fails closed,
    so a lifecycle record cannot erase or create a finding about a different
    artifact.

    cooled_scope_unknown names every cooled spec entry whose parent scope is
    not established: the `source.parent` key is absent, or it holds a value that
    names no registered brief membership and no listed brief file. Those entries are named in a
    `cooled_child_scope_unknown` finding and every `kind="brief"` dependency
    fails closed while any of them exists, because the brief such a child
    belongs to is precisely what is unknown.

    A declared *empty* value is a third, distinct answer: it says the spec has
    no parent brief, attributes nothing, and releases every dependency. That is
    what makes failing closed affordable — a maintainer clears the refusal by
    declaring the truth either way, rather than by having no way out.

    Accepted limitation: a declared empty value on an already-cooled entry is
    trusted rather than verified. The comparison against the artifact body runs
    only while the artifact is uncooled, so a value declared after the lifecycle
    record lands is never checked against anything.
    """
    states: dict[str, set[str]] = {}
    briefs_affected: set[str] = set()
    scope_unknown: set[str] = set()
    # Resolution is by entry *kind*, never by collection name. Three separate
    # reviews found the collection test wrong in both directions: it admitted a
    # mis-collected spec sitting in a brief queue, which resolved a declared
    # value that names no brief at all; and it missed a brief legitimately
    # registered in `backlog.open`, which refused a correctly declared child
    # with no repair available — declaring a resolving path was already done,
    # and declaring empty would be false.
    #
    brief_membership_paths = {
        membership.entry.path
        for membership in memberships
        if membership.entry.kind == "brief" and membership.entry.path is not None
    }
    # Listed on first need, once per reconciliation.
    brief_files: frozenset[str] | None = None
    for membership in memberships:
        entry = membership.entry
        if entry.kind != "spec":
            continue
        if _membership_is_cooled(membership, root, cooled):
            # A cooled child's state is not observable without reading its
            # body, and its parent may be absent from the read-free source
            # record.  Both facts make the parent brief's child scope
            # unevaluable.  Exclude the child from states and record the
            # affected briefs instead.
            # Three answers, read from the entry alone. The raw attribute is
            # what separates the second from the third: the normalizer collapses
            # a declared "none" and an absent key to the same None, so it cannot
            # tell "this spec has no parent" from "nobody recorded whether it
            # has one".
            raw_parent = entry.source.parent
            source_parent = _resolved_provenance_parent(
                raw_parent, require_local_brief=True
            )
            if source_parent is not None:
                if brief_files is None and source_parent not in brief_membership_paths:
                    brief_files = _listed_brief_files(root)
                if source_parent in brief_membership_paths or source_parent in (
                    brief_files or ()
                ):
                    briefs_affected.add(source_parent)
                else:
                    # A declared value naming no registered brief establishes
                    # nothing. Compared as declared, not through the filesystem:
                    # a case-insensitive volume would resolve `Brief-1.md` onto
                    # `brief-1.md` and silently attribute the child to a brief
                    # its entry does not name.
                    scope_unknown.add(entry.path)
            elif raw_parent is None:
                scope_unknown.add(entry.path)
            continue
        metadata = _artifact_metadata(entry, root)
        # Both sides resolved through the same function the routing checks
        # use. Read raw, a typed header would key `states` by `brief:<slug>`,
        # which no brief path lookup matches.
        parent_paths = {
            path for path in (
                _resolved_provenance_parent(
                    entry.source.parent, require_local_brief=True
                ),
                _resolved_provenance_parent(
                    metadata.parent if metadata is not None else None,
                    require_local_brief=True,
                ),
            )
            if path is not None
        }
        if not parent_paths:
            continue
        status = metadata.status if metadata is not None else None
        if membership.collection == "work.active":
            child_state = "Implementing"
        elif membership.collection == "work.queue":
            child_state = "Queued"
        elif status == "Shipped":
            child_state = "Shipped"
        elif status is None:
            child_state = "Unknown"
        else:
            child_state = status
        for parent_path in parent_paths:
            states.setdefault(parent_path, set()).add(child_state)
    return states, frozenset(briefs_affected), frozenset(scope_unknown)


def _append_impossible_transition(
    findings: list[RoutingFinding],
    entry: WorkspaceEntry,
    metadata: ArtifactMetadata,
    expected: set[str],
    detail: str,
) -> None:
    if metadata.status not in expected:
        findings.append(_finding("impossible_transition", entry.path, detail))


def _append_captured_lifecycle_findings(
    findings: list[RoutingFinding],
    membership: WorkspaceMembership,
    metadata: ArtifactMetadata,
) -> None:
    """Check a migrated captured membership against its record's `Status:`."""
    entry = membership.entry
    collection = membership.collection
    if metadata.captured_kind != entry.kind:
        findings.append(_finding("impossible_transition", entry.path, "captured kind"))
    elif metadata.status == "Closed" and collection in {
        "backlog.open",
        "shaping_queue.backlog",
        "shaping_queue.active",
    }:
        findings.append(
            _finding("impossible_transition", entry.path, "captured status is Closed")
        )
    elif collection == "backlog.closed":
        if entry.kind != "defect":
            findings.append(
                _finding("impossible_transition", entry.path, "closed backlog kind")
            )
        elif metadata.status != "Closed" or metadata.resolution not in {
            "fixed",
            "declined",
            "superseded",
        }:
            findings.append(
                _finding("impossible_transition", entry.path, "closed defect status")
            )


def _append_lifecycle_findings(
    findings: list[RoutingFinding],
    membership: WorkspaceMembership,
    metadata: ArtifactMetadata,
) -> None:
    entry = membership.entry
    collection = membership.collection
    if metadata.captured_kind is not None:
        _append_captured_lifecycle_findings(findings, membership, metadata)
        return
    if collection == "backlog.open":
        if entry.kind == "defect":
            if metadata.status == "Closed":
                findings.append(
                    _finding("impossible_transition", entry.path, "open defect status")
                )
        else:
            _append_impossible_transition(
                findings, entry, metadata, {"Draft"}, "open backlog status"
            )
        return
    if collection == "backlog.closed":
        if entry.kind != "defect":
            findings.append(
                _finding("impossible_transition", entry.path, "closed backlog kind")
            )
        elif metadata.status != "Closed" or metadata.resolution not in {
            "fixed",
            "declined",
            "superseded",
        }:
            findings.append(
                _finding("impossible_transition", entry.path, "closed defect status")
            )
        return
    if entry.kind == "spec":
        if collection == "work.active":
            _append_impossible_transition(
                findings, entry, metadata, {"Implementing"}, "active spec status"
            )
        elif collection == "work.shipped":
            _append_impossible_transition(
                findings, entry, metadata, {"Shipped"}, "shipped spec status"
            )
        elif collection == "work.queue" and metadata.status in {"Implementing", "Shipped"}:
            findings.append(_finding("impossible_transition", entry.path, "queue spec status"))
    elif entry.kind == "brief":
        expected_by_collection = {
            "brief_queue.draft": {"Draft"},
            "brief_queue.ready": {"Ready"},
            "brief_queue.executing": {"Executing"},
            "brief_queue.shipped": {"Shipped"},
            "brief_queue.withdrawn": {"Withdrawn"},
            "brief_queue.cancelled": {"Cancelled"},
        }
        expected = expected_by_collection.get(collection)
        if expected is not None:
            _append_impossible_transition(
                findings, entry, metadata, expected, "brief lifecycle status"
            )
    elif collection.startswith("shaping_queue."):
        terminal = _TERMINAL_STATUS_BY_KIND.get(entry.kind, set())
        if collection == "shaping_queue.active" and metadata.status in terminal:
            findings.append(
                _finding("impossible_transition", entry.path, "active shaping status")
            )
        elif collection == "shaping_queue.backlog" and metadata.status in terminal:
            findings.append(
                _finding("impossible_transition", entry.path, "backlog shaping status")
            )


def _append_collection_kind_findings(
    findings: list[RoutingFinding],
    membership: WorkspaceMembership,
) -> bool:
    allowed_kinds = _ALLOWED_KIND_BY_COLLECTION.get(membership.collection)
    if allowed_kinds is None or membership.entry.kind in allowed_kinds:
        return False
    findings.append(
        _finding("impossible_transition", membership.entry.path, "collection kind")
    )
    return True


def _append_plan_findings(
    findings: list[RoutingFinding],
    membership: WorkspaceMembership,
    metadata: ArtifactMetadata,
) -> None:
    if membership.entry.kind != "spec" or not membership.collection.startswith("work."):
        return
    if metadata.plan_invalid_path:
        findings.append(
            _finding("invalid_artifact_path", membership.entry.path, "sibling plan path")
        )
    elif metadata.plan_exists is False:
        findings.append(_finding("missing_plan", membership.entry.path, "sibling plan missing"))
    elif not metadata.plan_readable:
        findings.append(
            _finding("unreadable_artifact", membership.entry.path, "sibling plan unreadable")
        )


def _authority_status_for_entry(
    entry: WorkspaceEntry,
    metadata: ArtifactMetadata | None,
) -> dict[str, object] | None:
    if (
        entry.source.mode == "tracker-origin"
        and metadata is not None
        and metadata.authority_error is not None
    ):
        return None
    profile = entry.source.tracker_profile
    refresh_available: bool | str = "unknown"
    write_back_available: bool | str = "unknown"
    if profile is None or entry.source.mode == "repo-origin":
        # No resolved profile, or a repo-origin entry that is definitionally
        # write-back incapable. Neither can report availability as True.
        refresh_available = False
        write_back_available = False
    elif metadata is not None and metadata.status in {
        "Implementing",
        "Executing",
        "Shipped",
    }:
        refresh_available = False
        if metadata.status != "Shipped":
            write_back_available = False
    refresh: dict[str, object] = {
        "available": refresh_available,
        "write_back_available": write_back_available,
        "conflict": bool(metadata.refresh_conflict) if metadata is not None else False,
    }
    if entry.source.revision is not None:
        refresh["compared_revision"] = entry.source.revision
    if metadata is not None and metadata.authority_status is not None:
        authority_refresh = metadata.authority_status
        if "compared_revision" in authority_refresh:
            refresh["compared_revision"] = authority_refresh["compared_revision"]
        if "accepted_revision" in authority_refresh:
            refresh["accepted_revision"] = authority_refresh["accepted_revision"]
        refresh["conflict"] = bool(refresh["conflict"]) or bool(
            authority_refresh.get("conflict")
        )
    status: dict[str, object] = {
        "origin_mode": entry.source.mode,
        "refresh": refresh,
    }
    if profile is not None:
        status["profile"] = dict(profile)
    return status


def _structural_findings(
    membership: WorkspaceMembership,
    metadata: ArtifactMetadata | None,
    cycle_paths: set[str],
    brief_child_states: dict[str, set[str]],
    root: Path | None = None,
    cooled: bool = False,
    briefs_with_cooled_children: frozenset[str] = frozenset(),
) -> list[RoutingFinding]:
    entry = membership.entry
    findings: list[RoutingFinding] = []
    if entry.path in cycle_paths:
        findings.append(_finding("dependency_cycle", entry.path, "dependency cycle"))
    require_local_brief_parent = entry.kind == "spec"
    source_parent = _resolved_provenance_parent(
        entry.source.parent, require_local_brief=require_local_brief_parent
    )
    if _provenance_path_is_invalid(
        root,
        source_parent,
        require_local_brief=require_local_brief_parent,
    ):
        findings.append(_finding("invalid_artifact_path", source_parent or "", "source parent"))
    skip_status_lifecycle = _append_collection_kind_findings(findings, membership)
    if cooled:
        # Everything above is derived from the membership: the workspace entry,
        # its collection, and the duplicate/cycle sets. Everything below reads
        # the artifact body — existence, readability, parent provenance, plan
        # state, status lifecycle. For a cooled artifact those predicates are
        # not observable, so they are not evaluated rather than evaluated
        # against absent values. Passing read-free metadata down instead would
        # report a live artifact as `missing_artifact` and its declared parent
        # as a `provenance_mismatch`, which is how a cooled defect came to
        # block its own live dependants.
        return findings
    if metadata is not None and metadata.captured_finding is not None:
        findings.append(metadata.captured_finding)
        return findings
    if metadata is not None and metadata.invalid_path:
        findings.append(_finding("invalid_artifact_path", entry.path, "artifact path"))
        return findings
    if metadata is None or not metadata.exists:
        findings.append(_finding("missing_artifact", entry.path, "artifact is missing"))
        return findings
    if not metadata.readable:
        findings.append(_finding("unreadable_artifact", entry.path, "artifact is unreadable"))
        return findings
    if metadata.captured_kind is not None:
        # A record carries no provenance, plan, or authority block: only the
        # lifecycle rule applies.
        if not skip_status_lifecycle:
            _append_lifecycle_findings(findings, membership, metadata)
        return findings
    if metadata.authority_error is not None:
        findings.append(
            _finding(metadata.authority_error, entry.path, "source authority block")
        )
    if metadata.refresh_conflict:
        findings.append(_finding("refresh_conflict", entry.path, "unresolved refresh conflict"))
    artifact_parent = _resolved_provenance_parent(
        metadata.parent, require_local_brief=require_local_brief_parent
    )
    if _provenance_path_is_invalid(
        root,
        artifact_parent,
        require_local_brief=require_local_brief_parent,
    ):
        findings.append(
            _finding("invalid_artifact_path", artifact_parent or "", "artifact parent")
        )
    if entry.kind == "brief" and membership.collection.startswith("brief_queue."):
        child_states = brief_child_states.get(entry.path, set())
        if not _brief_child_scope_is_valid(
            membership.collection,
            child_states,
            scope_unevaluable=entry.path in briefs_with_cooled_children,
        ):
            findings.append(_finding("impossible_transition", entry.path, "brief child scope"))
    _append_plan_findings(findings, membership, metadata)
    if not skip_status_lifecycle:
        _append_lifecycle_findings(findings, membership, metadata)
    return findings


def _header_edges_by_path(
    memberships: list[WorkspaceMembership],
    root: Path | None,
    cooled: frozenset[Path],
) -> dict[str, HeaderDependencies]:
    """Read each non-cooled local membership's header once, by waiting path.

    A cooled membership is never opened and contributes no entry. Without a
    root nothing can be read, so no edge exists.
    """
    if root is None:
        return {}
    waiting = [
        membership for membership in memberships
        if membership.entry.path is not None
        and not _membership_is_cooled(membership, root, cooled)
        and _captured_membership_form(membership.entry.path) != "unmigrated"
    ]
    if not waiting:
        return {}
    index = build_resolution_index(root, cooled=cooled)
    kinds = {
        membership.entry.path: membership.entry.kind
        for membership in memberships
        if membership.entry.path is not None
    }
    headers: dict[str, HeaderDependencies] = {}
    for membership in waiting:
        path = membership.entry.path
        assert path is not None
        if path in headers:
            continue
        if _captured_membership_form(path) == "migrated":
            # A captured record is read only as a confined file, so a link or a
            # hard link to a cooled body is never opened; its lifecycle check
            # already reports it unreadable.
            content = _migration_file_bytes(root, path)
            headers[path] = (
                HeaderDependencies((), ())
                if content is None
                else header_dependencies_from_text(
                    root,
                    path,
                    content.decode("utf-8", errors="replace"),
                    index=index,
                    membership_kinds=kinds,
                    cooled=cooled,
                )
            )
            continue
        headers[path] = read_header_dependencies(
            root, path, index=index, membership_kinds=kinds, cooled=cooled
        )
    return headers


def evaluate_dispatch(
    membership: WorkspaceMembership,
    by_path: dict[str, list[WorkspaceMembership]],
    cycle_paths: set[str],
    structurally_blocked_paths: set[str],
    brief_child_states: dict[str, set[str]],
    root: Path | None = None,
    cooled: frozenset[Path] = frozenset(),
    briefs_with_cooled_children: frozenset[str] = frozenset(),
    cooled_scope_unknown: frozenset[str] = frozenset(),
    header: HeaderDependencies | None = None,
) -> DispatchEvaluation:
    """Evaluate the positive T2 dispatch predicate for one canonical membership.

    `header` holds the waiting item's dependency edges. `entry.needs` decides
    nothing: a non-empty array only earns `unmigrated_needs`.
    """
    entry = membership.entry
    metadata = _artifact_metadata(entry, root) or _metadata_from_membership(membership)
    findings = _structural_findings(
        membership,
        metadata,
        cycle_paths,
        brief_child_states,
        root,
        briefs_with_cooled_children=briefs_with_cooled_children,
    )
    if (
        entry.kind == "spec"
        and membership.collection == "work.queue"
        and metadata is not None
        and metadata.exists
        and metadata.readable
    ):
        if not (entry.path.startswith("docs/specs/") and entry.path.endswith("/spec.md")):
            findings.append(_finding("invalid_artifact_path", entry.path, "spec path shape"))
        if metadata.status != "Approved":
            findings.append(_finding("unapproved_spec", entry.path, "spec is not Approved"))
    for header_finding in (header.findings if header is not None else ()):
        if header_finding.code == "unreadable_artifact" and any(
            existing.code == header_finding.code and existing.path == header_finding.path
            for existing in findings
        ):
            continue
        findings.append(header_finding)
    for dep in (header.dependencies if header is not None else ()):
        satisfied, finding = _dependency_is_satisfied(
            dep,
            by_path,
            structurally_blocked_paths,
            root,
            cooled,
            briefs_with_cooled_children=briefs_with_cooled_children,
            cooled_scope_unknown=cooled_scope_unknown,
            brief_child_states=brief_child_states,
        )
        if not satisfied and finding is not None:
            # The path came from a header item, so it is bounded like any other
            # echoed value: a failing path loses its content, not its code.
            findings.append(
                dataclasses.replace(
                    finding, path=_bounded_finding_identifier(finding.path)
                )
            )
    dispatchable = (
        entry.kind == "spec"
        and membership.collection == "work.queue"
        and metadata is not None
        and metadata.exists
        and metadata.readable
        and metadata.status == "Approved"
        and metadata.plan_exists is True
        and metadata.plan_readable
        and entry.path.startswith("docs/specs/")
        and entry.path.endswith("/spec.md")
        and not findings
    )
    return DispatchEvaluation(
        entry=entry,
        collection=membership.collection,
        dispatchable=dispatchable,
        findings=findings,
        authority_status=_authority_status_for_entry(entry, metadata),
    )


# Captures the status content before any annotation (parenthetical or HTML comment).
# A spaced arrow inside "(root → leaf)" must never be read as a transition.
_STATUS_FIELD_RE = re.compile(r'\*\*Status:\*\*\s+(.*?)(?:\s*\(|\s*<!--|$)')


# Finds ALL segments after → (non-whitespace, non-arrow chars), so compact multi-hop
# "Draft→Approved→Shipped" yields ["Approved", "Shipped"] and a non-letter final
# segment (e.g. "→ 2026", trailing "→") still forces None instead of backtracking.
_TRANSITION_ARROW_RE = re.compile(r'→\s*([^→\s]+)')


# Stop at the first ##+ heading — status lines in body examples or tables are
# never authoritative. Matches lint-spec-status.py's canonical preamble boundary.
_SECTION_HEADING_RE = re.compile(r"^ {0,3}#{2,}(?:[ \t]|$)")


# HTML comments; stripped before the status-field check so that
# "<!-- - **Status:** Shipped -->" cannot satisfy the preamble guard.
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


# CommonMark fence opener/closer: 0-3 spaces indentation, then 3+ backticks or
# 3+ tildes. Opening type and minimum length must match the closer.
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


VALID_STATUSES = frozenset({"Draft", "Approved", "Implementing", "Shipped", "Archived"})


def _parse_spec_status(text: str) -> tuple[str | None, str | None]:
    """Parse a spec.md string and return (status_token, raw_status_line).

    Scans the preamble (before the first ## heading), skipping fenced code
    blocks and HTML comments, and returns the first `- **Status:**` field.
    Returns (None, None) when no valid status is found.
    """
    fence_char: str | None = None  # None = not in fence; "`" or "~" = in fence
    fence_min_len: int = 0         # minimum closing fence length
    in_ml_comment = False          # inside a multi-line HTML comment
    for line in text.splitlines():
        # Fence tracking — CommonMark: 0–3 spaces of indentation; opening delimiter
        # type (` or ~) and minimum length must match the closer. A `~~~` inside a
        # ``` fence does NOT close it; it is treated as fence body content.
        if not in_ml_comment:
            fm = _FENCE_RE.match(line)
            if fm:
                marker = fm.group(1)
                char = marker[0]
                length = len(marker)
                if fence_char is None:
                    # Opener: info strings (e.g. ```python) are allowed after the marker.
                    fence_char, fence_min_len = char, length
                    continue
                # Closer: same type, >= length, and NO non-whitespace after the marker.
                # A line like "```python" inside a fence is body content, not a closer.
                rest = line[fm.end():]
                if char == fence_char and length >= fence_min_len and not rest.strip():
                    fence_char, fence_min_len = None, 0
                    continue
                # else: different type or has trailing text — treat as fence body
        if fence_char is not None:
            continue
        # Multi-line HTML comment: skip until closing -->.
        if in_ml_comment:
            if "-->" in line:
                # After the closer, strip any COMPLETE inline comments from the
                # remainder (e.g. "--> <!-- note -->") before testing for an unclosed
                # opener. Without this, "--> <!-- note -->" sets in_ml_comment=True
                # even though the comment is fully closed on the same line.
                remainder = line[line.index("-->") + 3:]
                remainder_clean = _HTML_COMMENT_RE.sub("", remainder)
                in_ml_comment = "<!--" in remainder_clean
            continue
        # Stop at the first section heading — body examples live after ## headings.
        if _SECTION_HEADING_RE.match(line):
            break
        # Strip single-line HTML comments. If an unclosed <!-- remains, the rest of
        # this line and all subsequent lines until --> are inside a comment.
        clean = _HTML_COMMENT_RE.sub("", line)
        if "<!--" in clean:
            clean = clean[:clean.index("<!--")]
            in_ml_comment = True
        # Anchor to the canonical list-item field form: "- **Status:** ..."
        # A prose line containing **Status:** (example, comment) is not the field.
        if not clean.startswith("- **Status:**"):
            continue
        # Strip annotations before scanning — a spaced arrow in "(root → leaf)"
        # must never be read as a transition arrow.
        m = _STATUS_FIELD_RE.search(clean)
        if not m:
            continue
        content = m.group(1).strip()
        if "→" in content:
            # Transition form: "Draft → Approved → Shipped" (any arrow spacing).
            # A trailing bare arrow ("Draft → Approved →") has no final segment;
            # reject it explicitly so the preceding segment is never backtracked to.
            if content.rstrip().endswith("→"):
                return None, None
            # Take the LAST segment; if not a known status, return None — no backtrack.
            segments = _TRANSITION_ARROW_RE.findall(content)
            if segments:
                last = segments[-1]
                return (last, line) if last in VALID_STATUSES else (None, None)
        else:
            word = content.split()[0] if content.split() else ""
            return (word, line) if word in VALID_STATUSES else (None, None)
    return None, None


def _brief_child_scope_is_valid(
    collection: str,
    child_states: set[str],
    scope_unevaluable: bool = False,
) -> bool:
    """Return whether child progress is compatible with a brief lifecycle.

    `scope_unevaluable` is True when a child this brief declares has cooled, so
    `child_states` may be missing a state that is really there. Only the arms
    that assert a state is PRESENT are suppressed, because only they are
    non-monotone: a missing child can flip them from satisfied to violated, and
    cooling would plant a finding on live work. The arms that assert a state is
    ABSENT read the states actually observed — an unknown extra child can only
    add a state, never remove one — so a violation found among live, readable
    children stays a violation whatever the cooled child is. Suppressing every
    arm would let cooling one child erase an `impossible_transition` that a
    different, fully readable child caused.
    """

    execution_evidence = bool(child_states & {"Implementing", "Shipped"})
    if collection in {
        "brief_queue.draft",
        "brief_queue.ready",
        "brief_queue.withdrawn",
    }:
        # Asserts execution evidence is absent: monotone, never suppressed.
        return not execution_evidence
    if collection in {"brief_queue.executing", "brief_queue.cancelled"}:
        # Asserts evidence is present: a cooled child can hide the only child
        # carrying it.
        return execution_evidence or scope_unevaluable
    if collection == "brief_queue.shipped":
        # Asserts no child is in a state other than Shipped: monotone, never
        # suppressed. Deliberately does NOT require the set to be non-empty.
        # Most specs declare no `source.parent`, so an empty set here means
        # "no child is attributed to this brief", not "this brief shipped
        # nothing". The non-empty requirement is enforced elsewhere, against a
        # different source: the brief-coverage lint reads the brief's own Spec
        # map and fails when a Shipped brief's mapped children are empty or not
        # all shipped. This projection deliberately does not read that section,
        # so the two checks cover the same rule over different inputs and
        # neither substitutes for the other.
        return all(state == "Shipped" for state in child_states)
    return True


def confine_migration_path(
    root: Path,
    relative_path: str,
    *,
    require_file: bool = False,
) -> Path | None:
    """Resolve a repository-relative path while refusing link and alias escapes."""
    if not _is_repository_relative_path(relative_path):
        return None
    try:
        resolved_root = root.resolve(strict=True)
        if not resolved_root.is_dir() or root.is_symlink():
            return None
        candidate = resolved_root.joinpath(*relative_path.split("/"))
        cursor = resolved_root
        for part in relative_path.split("/"):
            cursor = cursor / part
            if cursor.exists() or cursor.is_symlink():
                info = cursor.lstat()
                if stat.S_ISLNK(info.st_mode):
                    return None
                reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
                if reparse and getattr(info, "st_file_attributes", 0) & reparse:
                    return None
        resolved = candidate.resolve(strict=require_file)
        resolved.relative_to(resolved_root)
        if require_file:
            before = resolved.stat()
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                return None
        return resolved
    except (FileNotFoundError, NotADirectoryError, OSError, RuntimeError, ValueError):
        return None


def _migration_file_bytes(root: Path, relative_path: str) -> bytes | None:
    """Read a confined regular single-link file with pre/post identity checks."""
    path = confine_migration_path(root, relative_path, require_file=True)
    if path is None:
        return None
    descriptor: int | None = None
    try:
        before = path.stat()
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            return None
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            return None
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        after = path.stat()
        if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            return None
        return b"".join(chunks)
    except (OSError, RuntimeError, ValueError):
        return None
    finally:
        if descriptor is not None:
            os.close(descriptor)


# --- source authority: a port of `work-intake`'s `parse_source_authority` ----------


class RefreshRefusal(ValueError):
    """A stable, redacted refusal safe to return to the caller."""


@dataclasses.dataclass(frozen=True)
class Approval:
    """Recorded approval evidence embedded in the local artifact."""

    identity: str
    role: str
    decided_at: str
    authorization_source: str


@dataclasses.dataclass(frozen=True)
class SourceAuthority:
    """Parsed source-authority contract from one artifact."""

    source_ref: str
    source_revision: str
    accepted_revision: str | None
    owned_fields: Mapping[str, str]
    acceptance: Approval | None
    source_decisions: tuple[Mapping[str, object], ...] = ()
    conflicts: tuple[Mapping[str, object], ...] = ()
    local_receipts: tuple[Mapping[str, object], ...] = ()
    remote_actions: tuple[Mapping[str, object], ...] = ()
    mode: str = "tracker-origin"
    tracker_profile: dict[str, str] | None = None


_AUTHORITY_FENCE = re.compile(
    r"^```toml source-authority\s*$\n(?P<body>.*?)^```\s*$",
    re.MULTILINE | re.DOTALL,
)


_TOP_AUTHORITY_KEYS = {
    "contract_version",
    "mode",
    "source_ref",
    "source_revision",
    "accepted_revision",
    "tracker_profile",
    "owned_fields",
    "acceptance",
    "source_decisions",
    "conflicts",
    "local_receipts",
    "remote_actions",
}


_APPROVAL_KEYS = {"identity", "role", "decided_at", "authorization_source"}


_DECISIONS = {"keep-local", "accept-source", "revise-both"}


_REMOTE_ACTIONS = {
    "trace-link",
    "display-status",
    "comment",
    "pull-request-link",
    "closure",
}


def _require_exact_keys(
    value: Mapping[str, object],
    allowed: set[str],
    required: set[str],
    code: str,
) -> None:
    if set(value) - allowed or not required.issubset(value):
        raise RefreshRefusal(code)


def _nonempty_string(value: object, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RefreshRefusal(code)
    return value


def _bounded_string(value: object, maximum: int, code: str) -> str:
    text = _nonempty_string(value, code)
    if len(text) > maximum:
        raise RefreshRefusal(code)
    return text


def _timestamp(value: object, code: str) -> str:
    text = _bounded_string(value, 40, code)
    try:
        parsed = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RefreshRefusal(code) from exc
    if parsed.tzinfo is None:
        raise RefreshRefusal(code)
    return text


def _digest(value: object, code: str) -> str:
    text = _nonempty_string(value, code)
    if re.fullmatch(r"[a-f0-9]{64}", text) is None:
        raise RefreshRefusal(code)
    return text


_PROFILE_BOUNDS = {"id": 200, "version": 100}


def _profile_table(value: object) -> dict[str, str]:
    """Validate a profile table: exactly ``id`` and ``version``, bounded, one line."""

    if not isinstance(value, dict) or set(value) != set(_PROFILE_BOUNDS):
        raise RefreshRefusal("invalid_source_authority")
    for key, maximum in _PROFILE_BOUNDS.items():
        item = value[key]
        if (
            not isinstance(item, str)
            or not 1 <= len(item) <= maximum
            or "\r" in item
            or "\n" in item
        ):
            raise RefreshRefusal("invalid_source_authority")
    return {key: value[key] for key in _PROFILE_BOUNDS}


def parse_source_authority(markdown: str) -> SourceAuthority:
    """Parse the artifact's one closed ``source-authority`` TOML block."""

    matches = list(_AUTHORITY_FENCE.finditer(markdown))
    if len(matches) != 1:
        reason = "duplicate_source_authority" if len(matches) > 1 else "missing_source_authority"
        raise RefreshRefusal(reason)
    try:
        data = tomllib.loads(matches[0].group("body"))
        _require_exact_keys(
            data,
            _TOP_AUTHORITY_KEYS,
            {
                "contract_version",
                "mode",
                "source_ref",
                "source_revision",
                "owned_fields",
            },
            "invalid_source_authority",
        )
        if data["contract_version"] != "source-authority.v1" or data["mode"] != "tracker-origin":
            raise RefreshRefusal("invalid_source_authority")
        owned = data["owned_fields"]
        acceptance = data.get("acceptance")
        if not isinstance(owned, dict) or len(owned) > 200:
            raise RefreshRefusal("invalid_source_authority")
        if any(
            not isinstance(key, str)
            or not key
            or len(key) > 200
            or value not in {"local", "source"}
            for key, value in owned.items()
        ):
            raise RefreshRefusal("invalid_source_authority")

        def closed_records(
            name: str,
            allowed: set[str],
            required: set[str],
        ) -> tuple[Mapping[str, object], ...]:
            raw = data.get(name, [])
            if not isinstance(raw, list) or len(raw) > 1000:
                raise RefreshRefusal("invalid_source_authority")
            records: list[Mapping[str, object]] = []
            for item in raw:
                if not isinstance(item, dict):
                    raise RefreshRefusal("invalid_source_authority")
                _require_exact_keys(
                    item, allowed, required, "invalid_source_authority"
                )
                records.append(dict(item))
            return tuple(records)

        decisions = closed_records(
            "source_decisions",
            {
                "source_revision",
                "field",
                "decision",
                "value_digest",
                "identity",
                "role",
                "decided_at",
                "authorization_source",
            },
            {
                "source_revision",
                "field",
                "decision",
                "identity",
                "role",
                "decided_at",
                "authorization_source",
            },
        )
        if any(item["decision"] not in _DECISIONS for item in decisions):
            raise RefreshRefusal("invalid_source_authority")
        for item in decisions:
            _bounded_string(item["source_revision"], 200, "invalid_source_authority")
            _bounded_string(item["field"], 200, "invalid_source_authority")
            _bounded_string(item["identity"], 200, "invalid_source_authority")
            _bounded_string(item["role"], 200, "invalid_source_authority")
            _timestamp(item["decided_at"], "invalid_source_authority")
            _bounded_string(
                item["authorization_source"], 200, "invalid_source_authority"
            )
            if "value_digest" in item:
                _digest(item["value_digest"], "invalid_source_authority")
        decision_keys = [
            (str(item["source_revision"]), str(item["field"]))
            for item in decisions
        ]
        if len(set(decision_keys)) != len(decision_keys):
            raise RefreshRefusal("invalid_source_authority")
        conflicts = closed_records(
            "conflicts",
            {"source_revision", "field", "status", "decision"},
            {"source_revision", "field", "status"},
        )
        if any(
            item["status"] not in {"unresolved", "resolved"}
            or ("decision" in item and item["decision"] not in _DECISIONS)
            for item in conflicts
        ):
            raise RefreshRefusal("invalid_source_authority")
        for item in conflicts:
            _bounded_string(item["source_revision"], 200, "invalid_source_authority")
            _bounded_string(item["field"], 200, "invalid_source_authority")
        conflict_keys = [
            (str(item["source_revision"]), str(item["field"]))
            for item in conflicts
        ]
        if len(set(conflict_keys)) != len(conflict_keys):
            raise RefreshRefusal("invalid_source_authority")
        local_receipts = closed_records(
            "local_receipts",
            {
                "update_id",
                "artifact_digest",
                "workspace_digest",
                "policy_digest",
                "status",
                "recorded_at",
            },
            {
                "update_id",
                "artifact_digest",
                "status",
                "recorded_at",
            },
        )
        for item in local_receipts:
            _bounded_string(item["update_id"], 200, "invalid_source_authority")
            _digest(item["artifact_digest"], "invalid_source_authority")
            if ("workspace_digest" in item) == ("policy_digest" in item):
                raise RefreshRefusal("invalid_source_authority")
            _digest(
                item["workspace_digest" if "workspace_digest" in item else "policy_digest"],
                "invalid_source_authority",
            )
            if item["status"] not in {"pending", "failed", "committed"}:
                raise RefreshRefusal("invalid_source_authority")
            _timestamp(item["recorded_at"], "invalid_source_authority")
        update_ids = [str(item["update_id"]) for item in local_receipts]
        if len(set(update_ids)) != len(update_ids):
            raise RefreshRefusal("invalid_source_authority")
        remote_actions = closed_records(
            "remote_actions",
            {
                "confirmation_id",
                "mutation_digest",
                "profile_version",
                "payload_digest",
                "identity",
                "role",
                "confirmed_at",
                "authorization_source",
                "action",
                "target",
                "status",
            },
            {
                "confirmation_id",
                "mutation_digest",
                "profile_version",
                "payload_digest",
                "identity",
                "role",
                "confirmed_at",
                "authorization_source",
                "action",
                "target",
                "status",
            },
        )
        for item in remote_actions:
            _bounded_string(item["confirmation_id"], 200, "invalid_source_authority")
            _digest(item["mutation_digest"], "invalid_source_authority")
            _bounded_string(item["profile_version"], 100, "invalid_source_authority")
            _digest(item["payload_digest"], "invalid_source_authority")
            _bounded_string(item["identity"], 200, "invalid_source_authority")
            _bounded_string(item["role"], 200, "invalid_source_authority")
            _timestamp(item["confirmed_at"], "invalid_source_authority")
            _bounded_string(
                item["authorization_source"], 200, "invalid_source_authority"
            )
            if item["action"] not in _REMOTE_ACTIONS or item["status"] not in {
                "pending",
                "failed",
                "succeeded",
            }:
                raise RefreshRefusal("invalid_source_authority")
            _bounded_string(item["target"], 1000, "invalid_source_authority")
        confirmation_ids = [str(item["confirmation_id"]) for item in remote_actions]
        if len(set(confirmation_ids)) != len(confirmation_ids):
            raise RefreshRefusal("invalid_source_authority")
        approval = None
        if acceptance is not None:
            if not isinstance(acceptance, dict):
                raise RefreshRefusal("invalid_source_authority")
            _require_exact_keys(
                acceptance, _APPROVAL_KEYS, _APPROVAL_KEYS, "invalid_source_authority"
            )
            approval = Approval(
                identity=_bounded_string(
                    acceptance["identity"], 200, "invalid_source_authority"
                ),
                role=_bounded_string(
                    acceptance["role"], 200, "invalid_source_authority"
                ),
                decided_at=_timestamp(
                    acceptance["decided_at"], "invalid_source_authority"
                ),
                authorization_source=_bounded_string(
                    acceptance["authorization_source"], 200, "invalid_source_authority"
                ),
            )
        return SourceAuthority(
            source_ref=_bounded_string(
                data["source_ref"], 1000, "invalid_source_authority"
            ),
            source_revision=_bounded_string(
                data["source_revision"], 200, "invalid_source_authority"
            ),
            accepted_revision=(
                _bounded_string(
                    data["accepted_revision"], 200, "invalid_source_authority"
                )
                if "accepted_revision" in data
                else None
            ),
            tracker_profile=(
                _profile_table(data["tracker_profile"])
                if "tracker_profile" in data
                else None
            ),
            owned_fields=dict(owned),
            acceptance=approval,
            source_decisions=decisions,
            conflicts=conflicts,
            local_receipts=local_receipts,
            remote_actions=remote_actions,
        )
    except (KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        raise RefreshRefusal("invalid_source_authority") from exc


def run_canonical_reconciliation(
    collections: Mapping[str, list[WorkspaceEntry]],
    root: Path,
    cooled: frozenset[Path] = frozenset(),
) -> CanonicalWorkspaceResult:
    """Evaluate the header-derived `queue`, `active` and `shipped` spec lists.

    `collections` maps each of those names to its entries, in order. Every fact is
    derived from the artifacts' headers; a cooled artifact is seen as cooled, and
    its body is never opened.
    """
    memberships = [
        WorkspaceMembership(entry, f"work.{name}", index)
        for name in ("queue", "active", "shipped")
        for index, entry in enumerate(collections.get(name, ()))
    ]
    by_path: dict[str, list[WorkspaceMembership]] = {}
    for membership in memberships:
        by_path.setdefault(membership.entry.path, []).append(membership)
    headers = _header_edges_by_path(memberships, root, cooled)
    header_edges = {path: header.dependencies for path, header in headers.items()}
    cycle_paths = _dependency_cycles(memberships, header_edges)
    brief_child_states, briefs_with_cooled_children, cooled_scope_unknown = (
        _brief_child_spec_states(memberships, root, cooled)
    )
    cooled_scope_findings = [
        _finding("cooled_child_scope_unknown", path, "cooled child parent scope")
        for path in sorted(cooled_scope_unknown)
    ]
    structurally_blocked_paths: set[str] = set()
    cooled_membership_findings: list[RoutingFinding] = []
    for membership in memberships:
        membership_cooled = _membership_is_cooled(membership, root, cooled)
        metadata = (
            None
            if membership_cooled
            else (
                _artifact_metadata(membership.entry, root)
                or _metadata_from_membership(membership)
            )
        )
        member_findings = _structural_findings(
            membership,
            metadata,
            cycle_paths,
            brief_child_states,
            root,
            cooled=membership_cooled,
            briefs_with_cooled_children=briefs_with_cooled_children,
        )
        if member_findings:
            structurally_blocked_paths.add(membership.entry.path)
            if membership_cooled:
                # A cooled membership is excluded from `evaluations`, so what is
                # raised here would reach no output; these findings come from the
                # membership alone and are still owed.
                cooled_membership_findings.extend(member_findings)
    evaluations = [
        evaluate_dispatch(
            membership,
            by_path,
            cycle_paths,
            structurally_blocked_paths,
            brief_child_states,
            root,
            cooled,
            briefs_with_cooled_children=briefs_with_cooled_children,
            cooled_scope_unknown=cooled_scope_unknown,
            header=headers.get(membership.entry.path),
        )
        for membership in memberships
        if not _membership_is_cooled(membership, root, cooled)
    ]
    findings = [
        *cooled_membership_findings,
        *cooled_scope_findings,
        *(finding for evaluation in evaluations for finding in evaluation.findings),
    ]
    return CanonicalWorkspaceResult(
        cooled=cooled,
        memberships=memberships,
        findings=findings,
        evaluations=evaluations,
        dispatch_by_path={evaluation.entry.path: evaluation for evaluation in evaluations},
        header_edges=header_edges,
    )
