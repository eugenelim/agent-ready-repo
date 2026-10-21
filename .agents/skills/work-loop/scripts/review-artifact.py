#!/usr/bin/env python3
"""Validate review artifacts and run the finding-adjudication commands.

`validate` checks an orchestrator-owned review artifact without disclosing its
path or body. `classify`, `raw-classify`, `inspect`, and `record` are the
finding-adjudication commands. They live here so they outlast `loop-cohort.py`,
and the `loop-cohort.py review` verbs call the same code, so both command sets
print identical text.

With cohort state (a spec directory holding `state.json`), `inspect` and
`record` read and write that state exactly as the `loop-cohort.py review` verbs
always have, and write no review artifact. Without cohort state, `--run-id`
names a run, and each recorded round becomes one `record` artifact,
`.context/reviews/<run-id>/<round>-record.md`, so the next round and the review
budget read from artifacts alone.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, BinaryIO, NoReturn, Sequence

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REVIEW_RULES_PATH = SKILL_ROOT / "review-rules.json"

MAX_REPORT_BYTES = 1_048_576
REVIEW_STAGES = frozenset({"pre-execute", "post-gates"})
ARTIFACT_KINDS = frozenset({"raw", "adjudication", "evidence", "record"})
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ROLE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
MAX_ROLE_LENGTH = 64

# The authority role that may lift the review retry cap without cohort state.
# `work-supervisor.py start --authority-ref` takes the same role.
OVERRIDE_AUTHORITY_ROLE = "owner"
# Round files are `<round>-record.md`; a round is a positive decimal integer
# with no leading zero, so two spellings never name one round.
_RECORD_NAME_RE = re.compile(r"(?P<round>[1-9][0-9]{0,8})-record\.md")
RECORD_VERSION = 1
RECORD_FORMS = frozenset({"findings", "clean", "all-skipped"})

# Control-character neutralisation for this tool's own diagnostics: a refusal
# can interpolate a filename or exception text that came from a planted file.
_CONTROL_ESCAPES = str.maketrans({c: f"\\x{c:02x}" for c in [*range(32), 127]})

ReadText = Callable[[Path, str], str]


def _diag(text: object) -> str:
    """One-line, control-character-safe text for a warning or a refusal."""
    return " ".join(str(text).split()).translate(_CONTROL_ESCAPES)


class UsageError(ValueError):
    """The CLI shape or orchestrator-owned metadata is invalid."""


class ArtifactError(RuntimeError):
    """A report artifact failed the validation boundary."""

    def __init__(self, code: str) -> None:
        """Create a non-sensitive, fixed-code refusal."""
        super().__init__(code)
        self.code = code


class QuietArgumentParser(argparse.ArgumentParser):
    """Argument parser that never reflects attacker-controlled values on errors."""

    def error(self, message: str) -> NoReturn:
        """Convert argparse diagnostics into a fixed caller-owned refusal."""
        del message
        raise UsageError("invalid-command")


@dataclass(frozen=True)
class ArtifactMetadata:
    """Validated metadata from which the report location is derived."""

    root: Path
    run_id: str
    round_number: int
    review_stage: str | None
    reviewer_role: str | None
    kind: str
    expected_sha256: str | None = None

    @property
    def filename(self) -> str:
        """Return the deterministic report filename."""
        if self.kind == "record":
            return f"{self.round_number}-record.md"
        return (
            f"{self.round_number}-{self.review_stage}-"
            f"{self.reviewer_role}-{self.kind}.md"
        )


def _parse_run_id(value: object) -> str:
    """Accept only a canonical lowercase UUID, the one spelling of a run id."""
    try:
        parsed_run_id = uuid.UUID(str(value))
    except (AttributeError, TypeError, ValueError) as exc:
        raise UsageError("invalid-metadata") from exc
    if str(parsed_run_id) != value:
        raise UsageError("invalid-metadata")
    return str(parsed_run_id)


def _resolve_root(raw: str) -> Path:
    """Resolve the repository root the artifact tree hangs from."""
    try:
        root = Path(raw).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ArtifactError("unsafe-artifact") from exc
    if not root.is_dir():
        raise ArtifactError("unsafe-artifact")
    return root


def _parse_metadata(args: argparse.Namespace) -> ArtifactMetadata:
    """Validate CLI metadata without using it in diagnostics."""
    run_id = _parse_run_id(getattr(args, "run_id", None))

    round_text = str(args.round_number)
    if not round_text.isascii() or not round_text.isdecimal():
        raise UsageError("invalid-metadata")
    round_number = int(round_text)
    if round_number < 1:
        raise UsageError("invalid-metadata")

    if args.kind not in ARTIFACT_KINDS:
        raise UsageError("invalid-metadata")
    if args.kind == "record":
        # A record is named by its round alone; a stage or role would name a
        # different file, so supplying either refuses rather than being ignored.
        if args.review_stage is not None or args.reviewer_role is not None:
            raise UsageError("invalid-metadata")
        stage: str | None = None
        role: str | None = None
    else:
        stage = args.review_stage
        role = None if args.reviewer_role is None else str(args.reviewer_role)
        if role is None or len(role) > MAX_ROLE_LENGTH or ROLE_RE.fullmatch(role) is None:
            raise UsageError("invalid-metadata")
        if stage not in REVIEW_STAGES:
            raise UsageError("invalid-metadata")
    expected_sha256 = args.expected_sha256
    if expected_sha256 is not None and (
        args.kind != "evidence" or SHA256_RE.fullmatch(expected_sha256) is None
    ):
        raise UsageError("invalid-metadata")

    return ArtifactMetadata(
        root=_resolve_root(args.root),
        run_id=run_id,
        round_number=round_number,
        review_stage=stage,
        reviewer_role=role,
        kind=args.kind,
        expected_sha256=expected_sha256,
    )


def _descriptor_walk_supported() -> bool:
    """Return whether descriptor-relative, no-follow opens are available."""
    return os.open in os.supports_dir_fd and bool(getattr(os, "O_NOFOLLOW", 0))


def _open_run_directory(root: Path, run_id: str, *, create: bool = False) -> int:
    """Return a descriptor for `.context/reviews/<run-id>` beneath `root`.

    Every segment opens no-follow from its parent's descriptor, so a symlinked
    segment refuses instead of redirecting. With `create`, a missing segment is
    made under the same descriptor.
    """
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    current_fd = os.open(root, directory_flags | close_on_exec)
    try:
        for segment in (".context", "reviews", run_id):
            try:
                next_fd = os.open(
                    segment,
                    directory_flags | nofollow | close_on_exec,
                    dir_fd=current_fd,
                )
            except FileNotFoundError:
                if not create:
                    raise
                with contextlib.suppress(FileExistsError):
                    os.mkdir(segment, 0o777, dir_fd=current_fd)
                next_fd = os.open(
                    segment,
                    directory_flags | nofollow | close_on_exec,
                    dir_fd=current_fd,
                )
            os.close(current_fd)
            current_fd = next_fd
    except BaseException:
        os.close(current_fd)
        raise
    return current_fd


def _open_with_descriptor_walk(metadata: ArtifactMetadata) -> BinaryIO:
    """Open the report beneath no-follow directory descriptors."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    nonblock = getattr(os, "O_NONBLOCK", 0)
    current_fd = _open_run_directory(metadata.root, metadata.run_id)
    try:
        report_info = os.stat(
            metadata.filename,
            dir_fd=current_fd,
            follow_symlinks=False,
        )
        if not stat.S_ISREG(report_info.st_mode) or report_info.st_nlink > 1:
            raise ArtifactError("unsafe-artifact")
        report_fd = os.open(
            metadata.filename,
            os.O_RDONLY | nonblock | nofollow | close_on_exec,
            dir_fd=current_fd,
        )
        opened = os.fstat(report_fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink > 1:
            os.close(report_fd)
            raise ArtifactError("unsafe-artifact")
    finally:
        os.close(current_fd)
    return os.fdopen(report_fd, "rb", closefd=True)


def _create_with_descriptor_walk(
    root: Path, run_id: str, filename: str, data: bytes
) -> None:
    """Create `filename` exclusively in the run directory and write `data`.

    The directory opens through the same no-follow walk as a read, creating the
    tree when absent. `O_EXCL` makes a second writer of the same round refuse
    instead of overwriting the first.
    """
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    directory_fd = _open_run_directory(root, run_id, create=True)
    try:
        try:
            file_fd = os.open(
                filename,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow | close_on_exec,
                0o600,
                dir_fd=directory_fd,
            )
        except FileExistsError as exc:
            raise ArtifactError("record-conflict") from exc
        with os.fdopen(file_fd, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(directory_fd)


def _is_windows_reparse_point(info: os.stat_result) -> bool:
    """Return whether stat metadata identifies a Windows reparse point."""
    marker = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    attributes = getattr(info, "st_file_attributes", 0)
    return bool(attributes & marker)


def _require_resolved_under(path: Path, root: Path) -> None:
    """Reject a resolved fallback component that escapes the repository root."""
    try:
        path.resolve(strict=True).relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ArtifactError("unsafe-artifact") from exc


def _open_with_path_checks(metadata: ArtifactMetadata) -> BinaryIO:
    """Portable fallback when descriptor-relative opens are unavailable."""
    current = metadata.root
    for segment in (".context", "reviews", metadata.run_id):
        current /= segment
        info = os.lstat(current)
        if (
            stat.S_ISLNK(info.st_mode)
            or _is_windows_reparse_point(info)
            or not stat.S_ISDIR(info.st_mode)
        ):
            raise ArtifactError("unsafe-artifact")
        _require_resolved_under(current, metadata.root)
    report = current / metadata.filename
    info = os.lstat(report)
    if (
        stat.S_ISLNK(info.st_mode)
        or _is_windows_reparse_point(info)
        or info.st_nlink > 1
        or not stat.S_ISREG(info.st_mode)
    ):
        raise ArtifactError("unsafe-artifact")
    _require_resolved_under(report, metadata.root)
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    fd = os.open(report, flags)
    opened = os.fstat(fd)
    if opened.st_nlink > 1 or (opened.st_dev, opened.st_ino) != (
        info.st_dev,
        info.st_ino,
    ):
        os.close(fd)
        raise ArtifactError("unsafe-artifact")
    return os.fdopen(fd, "rb", closefd=True)


def _open_report(metadata: ArtifactMetadata) -> BinaryIO:
    """Open the expected report without following target or parent symlinks."""
    try:
        if _descriptor_walk_supported():
            return _open_with_descriptor_walk(metadata)
        return _open_with_path_checks(metadata)
    except PermissionError as exc:
        raise ArtifactError("unreadable") from exc
    except ArtifactError:
        raise
    except OSError as exc:
        raise ArtifactError("unsafe-artifact") from exc


def read_artifact(metadata: ArtifactMetadata) -> bytes:
    """Return the bytes of one safe UTF-8 artifact."""
    with _open_report(metadata) as report:
        before = os.fstat(report.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink > 1:
            raise ArtifactError("unsafe-artifact")
        if before.st_size > MAX_REPORT_BYTES:
            raise ArtifactError("too-large")
        data = report.read(MAX_REPORT_BYTES + 1)
        after = os.fstat(report.fileno())

    if len(data) > MAX_REPORT_BYTES or after.st_size > MAX_REPORT_BYTES:
        raise ArtifactError("too-large")
    # `before` and `after` fstat the same open file description, so their
    # (st_dev, st_ino) are identical by construction — comparing them would read
    # as a substitution-during-read control while being unable to fail. The
    # re-checks that DO carry information are st_nlink (a hard link created
    # while the descriptor was open) and st_size below.
    if after.st_nlink > 1:
        raise ArtifactError("unsafe-artifact")
    if after.st_size != len(data):
        raise ArtifactError("unstable-artifact")
    try:
        data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ArtifactError("invalid-utf8") from exc
    return data


def validate_artifact(metadata: ArtifactMetadata) -> tuple[int, str]:
    """Return the byte size and SHA-256 digest for one safe UTF-8 report."""
    data = read_artifact(metadata)
    return len(data), hashlib.sha256(data).hexdigest()


# ── relocated finding-adjudication logic ──────────────────────────────────
#
# Moved from `loop-cohort.py` without changing what it prints. The `loop-cohort:`
# prefix on its diagnostics is part of that output, so it stays.

def _load_sibling(filename: str, module_name: str) -> ModuleType:
    """Load a sibling script by path, never through `sys.path`.

    A plain import resolves under file-path invocation but not under a harness
    that does not put this directory on `sys.path`. Bytecode writing is off across
    the load and restored to its prior value, so a stale `__pycache__` entry
    cannot be executed. The module is registered only while its body runs, because
    a `@dataclass` resolves its own module by name, and the entry must not outlive
    a failed load.
    """
    path = SCRIPT_DIR / filename
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        if not stat.S_ISREG(os.lstat(path).st_mode):
            raise ImportError(f"{filename} is not a regular file")
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {filename}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(module_name, None)
    finally:
        sys.dont_write_bytecode = previous
    return module


_guards_module: ModuleType | None = None


def _loop_guards() -> ModuleType:
    """Load the sibling `_loop_guards.py` once per process."""
    global _guards_module
    if _guards_module is None:
        try:
            module = _load_sibling("_loop_guards.py", "_loop_guards")
        except Exception as exc:
            raise ArtifactError("guards-unavailable") from exc
        if not getattr(module, "_MODULE_COMPLETE", False):
            raise ArtifactError("guards-unavailable")
        _guards_module = module
    return _guards_module


def _read_managed_text(path: Path, label: str) -> str:
    """Bounded text read from the guard layer, the default report reader."""
    reader: ReadText = _loop_guards().read_managed_text
    return reader(path, label)


CLEAN_SUBSTRING = "Clean — ready to commit."
INDETERMINATE_SENTINEL = "ADJUDICATION-INDETERMINATE"
# Specialist reviewers (experience-reviewer, frontend-reviewer) emit "SHIP IT"
# on its own line as their clean verdict instead of CLEAN_SUBSTRING.
_SHIP_IT_RE = re.compile(r"^SHIP IT\s*$", re.MULTILINE)
# Fingerprints are SHA-256 (64 hex). The 40-hex SHA-1 form is still accepted
# so a cohort that was mid-review when core upgraded can finish: its
# state.json holds SHA-1 values and `review record --fingerprint` would
# otherwise hard-reject them. Stasis detection compares sets computed by the
# same binary, so a straddling run misses a match for exactly one round and
# self-heals on the next. Drop the 40-hex alternative once no in-flight
# cohort predates core 2.3.0.
_RE_FINGERPRINT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


FINDING_LINE_RE = re.compile(
    r"^(?P<title>\*\*\d+\.[^*]+\*\*)\s*[\.\s]*\s*`(?P<citation>[^`]+)`"
)
# frontend-reviewer: **title.** file:line. (unquoted file:line after title)
FINDING_LINE_RE_UNQUOTED = re.compile(
    r"^(?P<title>\*\*\d+\.[^*]+\*\*)\s*[\.\s]*\s*(?P<citation>\S+:\d+)"
)
# experience-reviewer: **title.** Where: <location>. (no file:line)
FINDING_LINE_RE_WHERE = re.compile(
    r"^(?P<title>\*\*\d+\.[^*]+\*\*)\s*[\.\s]*\s*Where:\s*(?P<location>[^.]+)"
)
ADJUDICATION_HEADINGS = (
    "## Main-loop result",
    "## Refuted audit",
    "## Indeterminate audit",
)
NUMBERED_FINDING_MARKER_RE = re.compile(r"\*\*\d+\.")
NOT_CHECKED_HEADING = "## Not checked"
# Shape only, deliberately. Two earlier revisions tried to make footer bullets
# safe to skip adjudication — first by rejecting finding-shaped markers, then by
# requiring a `Did not ` opener. Both were defeated, because separating
# disclosure prose from finding prose is undecidable by pattern
# ("- Did not complete authorization review: unauthenticated requests can set
# is_admin=true" satisfies both). The footer's content is therefore never
# trusted: `not_checked_present` disqualifies a report from the clean fast path
# and routes it to full adjudication, which reads the whole body. That makes a
# content rule here non-load-bearing, and a guard that looks load-bearing but
# is not is worse than none.
NOT_CHECKED_BULLET_RE = re.compile(r"^- ")
STRICT_SUSTAINED_FINDING_LINE_RE = re.compile(
    r"^\*\*\d+\.[^*\n]+\*\*\s*"
    r"(?:`[^`\n]+:\d+[^`\n]*`|\S+:\d+|Where:\s+[^.\n]+)\.\s+"
    r"\S(?:.*\S)?\s+Fix:\s+\S.*$"
)


# Closed on purpose: the three-bucket scheme, the major/minor pair, and the
# CRITICAL/HIGH/MEDIUM/LOW scheme the reviewer agents map onto on request.
# Stripping any bracketed text would also strip a reviewer-assigned finding id.
_STABLE_TITLE_SEVERITY_RE = re.compile(
    r"^\[(?:blocker|concern|nit|major|minor|critical|high|medium|low)\]\s*",
    re.IGNORECASE,
)


def stable_title(title: str) -> str:
    """Return a finding title without its ordinal or severity tag."""
    unwrapped = title.strip()
    if unwrapped.startswith("**") and unwrapped.endswith("**"):
        unwrapped = unwrapped[2:-2]
    without_ordinal = re.sub(r"^\d+\.\s*", "", unwrapped)
    return _STABLE_TITLE_SEVERITY_RE.sub("", without_ordinal)


def parse_finding_identities(report_text: str) -> tuple[list[str], list[str]]:
    """Return fingerprint and family digests for findings in a reviewer report.

    Algorithm pinned by the work-loop SKILL §REVIEW:
        sha256("<file>|<line>|<title>")
    where <file> is the cited path exactly as written, <line> is the first
    integer after the first colon in the citation, and <title> is the
    bolded heading including the surrounding `**` markers.

    Supports three formats:
    - adversarial-reviewer: **title** `file:line`  (backtick-quoted citation)
    - frontend-reviewer:    **title.** file:line.  (unquoted file:line)
    - experience-reviewer:  **title.** Where: loc. (location; key uses loc|0|title)
    """
    fingerprints: list[str] = []
    families: list[str] = []

    def add_finding(location: str, line_number: str, title: str) -> None:
        """Append both identities for one parsed finding."""
        fingerprint_preimage = f"{location}|{line_number}|{title}"
        family_preimage = f"{location}|{stable_title(title)}"
        fingerprints.append(
            hashlib.sha256(fingerprint_preimage.encode("utf-8")).hexdigest()
        )
        families.append(
            hashlib.sha256(family_preimage.encode("utf-8")).hexdigest()
        )

    for raw in report_text.splitlines():
        line = raw.strip()
        if not line.startswith("**"):
            continue
        # Try backtick-quoted citation first (adversarial-reviewer)
        m = FINDING_LINE_RE.match(line)
        if m:
            title = m.group("title").strip()
            citation = m.group("citation").strip()
            if ":" not in citation:
                continue
            file_part, _, rest = citation.partition(":")
            line_match = re.match(r"\d+", rest)
            if not line_match:
                continue
            add_finding(file_part, line_match.group(0), title)
            continue
        # Try Where: <location> (experience-reviewer)
        m = FINDING_LINE_RE_WHERE.match(line)
        if m:
            title = m.group("title").strip()
            location = m.group("location").strip()
            add_finding(location, "0", title)
            continue
        # Try unquoted file:line (frontend-reviewer)
        m = FINDING_LINE_RE_UNQUOTED.match(line)
        if m:
            title = m.group("title").strip()
            citation = m.group("citation").strip()
            file_part, _, rest = citation.partition(":")
            line_match = re.match(r"\d+", rest)
            if not line_match:
                continue
            add_finding(file_part, line_match.group(0), title)
    return fingerprints, families


def parse_findings(report_text: str) -> list[str]:
    """Return SHA-256 fingerprints while preserving the legacy parser API."""
    return parse_finding_identities(report_text)[0]


def _is_strict_actionable_result(actionable: str) -> bool:
    """Accept exact clean or complete parser-compatible sustained lines."""
    if actionable == CLEAN_SUBSTRING:
        return True

    finding_lines = [line for line in actionable.splitlines() if line.strip()]
    return bool(finding_lines) and all(
        STRICT_SUSTAINED_FINDING_LINE_RE.fullmatch(line.strip()) is not None
        and len(NUMBERED_FINDING_MARKER_RE.findall(line)) == 1
        and len(parse_findings(line)) == 1
        for line in finding_lines
    )


def _invalid(reason: str) -> dict:
    """Refuse a report, naming which rule refused it.

    `invalid` returns at exit 0 and stops the loop, so an unnamed refusal costs
    the operator a parser read to act on. The reason is enumerated and
    content-free, matching `review-artifact.py`'s refusal codes.
    """
    print(
        f"loop-cohort: report classified invalid ({reason})",
        file=sys.stderr,
    )
    return {
        "classification": "invalid",
        "fingerprints": [],
        "families": [],
        "matches_previous_round": False,
        "reason": reason,
    }


def _actionable_review_text(
    report_text: str,
    *,
    require_adjudication: bool = False,
) -> tuple[str, str | None]:
    """Return the main-loop result and a refusal reason, or None when accepted.

    Legacy reviewer reports have no adjudication headings and remain unchanged.
    When any adjudication heading is present, require the exact three-section
    envelope, keep only the main-loop result, and reject finding-shaped audit
    text rather than allowing it to reach fingerprinting.

    The second element is `None` when the structure is acceptable, otherwise an
    enumerated, content-free code naming which rule refused it. Codes mirror
    `review-artifact.py`'s `INVALID <code>` refusal vocabulary — the other half
    of this gateway — so a fail-closed stop is diagnosable without reopening the
    artifact or reverse-engineering the parser. They carry no report content,
    no path, and no line text.
    """
    lines = report_text.splitlines()
    found_headings = [
        line.strip() for line in lines if line.strip().startswith("## ")
    ]
    if not any(heading in found_headings for heading in ADJUDICATION_HEADINGS):
        return report_text, "legacy-report" if require_adjudication else None
    if found_headings != list(ADJUDICATION_HEADINGS):
        return "", "envelope-headings"

    heading_indexes = [
        next(index for index, line in enumerate(lines) if line.strip() == heading)
        for heading in ADJUDICATION_HEADINGS
    ]
    if any(line.strip() for line in lines[: heading_indexes[0]]):
        return "", "prose-before-envelope"

    main_start, refuted_start, indeterminate_start = heading_indexes
    audit_lines = lines[refuted_start + 1 :]
    if any(NUMBERED_FINDING_MARKER_RE.search(line) for line in audit_lines):
        return "", "audit-numbered-finding"

    actionable = "\n".join(lines[main_start + 1 : refuted_start]).strip()
    indeterminate_audit = "\n".join(lines[indeterminate_start + 1 :]).strip()

    # The refusals below are NOT gated on `require_adjudication`. Reaching here
    # already proves the exact three-section envelope is present, so the report
    # is an adjudication whichever flag the caller passed — and an indeterminate
    # verdict must never classify as clean (AC5), including on a flagless
    # `review inspect` or a replayed `review record`. Envelope-free legacy
    # reports returned earlier and are unaffected.
    #
    # Order matters for the operator, not for soundness — every `if` below
    # refuses. Report the most specific cause first: an indeterminate verdict is
    # a decision the adjudicator made and the owner must resolve, whereas a
    # shape complaint about the same report would send them to the wrong place.
    if INDETERMINATE_SENTINEL in report_text:
        return "", "indeterminate-present"
    if indeterminate_audit != "None.":
        return "", "indeterminate-audit-not-none"
    if not _is_strict_actionable_result(actionable):
        return "", "sustained-line-shape"
    return actionable, None


def _resolved_report(candidate: str) -> Path:
    """Normalise the CLI-supplied `--report` path at the argv boundary.

    Normalise-only, deliberately. The two `--root` linters in this skill raise
    on an unusable path, but `--report` must not: `review inspect` classifies an
    unreadable report as `invalid`, which the work-loop SKILL documents as a
    Surface signal rather than a crash. Raising here would convert a defined
    outcome into an operational error.

    The `resolve()` still does the job it is here for — it puts the
    normalisation adjacent to the argv read, where a taint analyser can see it,
    instead of leaving a raw `Path(args.report)` as the boundary.
    """
    try:
        return Path(candidate).resolve()
    except (OSError, ValueError, RuntimeError):
        # resolve() raises on an embedded null (ValueError) and on Windows
        # reserved names (OSError). Falling back to the unresolved path keeps
        # the value flowing to _classify_report, which classifies it `invalid`
        # at exit 0 — the defined outcome. Raising here would reintroduce
        # exactly the operational error this helper's docstring rules out.
        return Path(candidate)


def _classify_raw_report(
    report_path: Path, *, read_text: ReadText | None = None
) -> dict[str, object]:
    """Classify a raw reviewer return without widening adjudication semantics.

    This remains separate from `_classify_report`: that function's optional
    adjudication envelope is a high-stakes path, where a third mode could
    silently weaken strict classification.
    """
    reader = read_text or _read_managed_text
    reason: str | None = None
    try:
        report_text = reader(report_path.resolve(), report_path.name)
    except (OSError, UnicodeDecodeError, ValueError):
        classification = "invalid"
        finding_count = 0
        classified_digest = None
        reason = "unreadable"
        lines: list[str] = []
    else:
        # Digest the bytes this call actually classified, not a second read.
        # the bounded reader decodes bytes strictly without folding newlines, so
        # re-encoding is byte-identical to the file. A caller that re-opened the
        # path for its audit anchor could digest content nobody classified.
        classified_digest = hashlib.sha256(report_text.encode("utf-8")).hexdigest()
        # LF and CRLF only (AC2.3b). `str.splitlines()` also breaks on \v, \f,
        # \x1c-\x1e, \x85, U+2028 and U+2029, so a single visual line could be
        # split into a grammar that reads clean. Any of those left embedded here
        # makes its line unequal to the sentinel, which fails closed.
        lines = report_text.replace("\r\n", "\n").split("\n")
        finding_count = len(parse_findings(report_text))
        if finding_count:
            classification = "findings"
        else:
            sentinel_count = sum(line == CLEAN_SUBSTRING for line in lines)
            sentinel_index = next(
                (index for index, line in enumerate(lines) if line == CLEAN_SUBSTRING),
                -1,
            )
            footer_started = False
            clean_shape = sentinel_count == 1
            if not clean_shape:
                reason = "sentinel-absent" if sentinel_count == 0 else "sentinel-repeated"
            for index, line in enumerate(lines):
                if not clean_shape:
                    break
                if not line or index == sentinel_index:
                    continue
                if index < sentinel_index:
                    clean_shape = False
                    reason = "content-before-sentinel"
                    break
                if line == NOT_CHECKED_HEADING:
                    if footer_started:
                        clean_shape = False
                        reason = "footer-heading-repeated"
                        break
                    footer_started = True
                    continue
                if footer_started and NOT_CHECKED_BULLET_RE.match(line):
                    continue
                clean_shape = False
                reason = (
                    "footer-bullet-malformed" if footer_started else "unpermitted-content"
                )
                break
            classification = "clean" if clean_shape else "invalid"

    # Disclosure metadata is deliberately computed after classification.
    not_checked_present = NOT_CHECKED_HEADING in lines
    return {
        "classification": classification,
        "finding_count": finding_count,
        "not_checked_present": not_checked_present,
        # Internal only — never emitted in the JSON payload.
        # `_raw_classification_payload` projects the closed public field set so a
        # key added here cannot leak into the documented contract. The reason is
        # a fixed, content-free code surfaced on stderr, mirroring
        # `_actionable_review_text`'s refusal vocabulary: a bare `invalid` leaves
        # an operator unable to tell a missing sentinel from a malformed footer.
        "_classified_digest": classified_digest,
        "_reason": reason,
    }


RAW_REFUSAL_REASONS = frozenset(
    {
        "unreadable",
        "sentinel-absent",
        "sentinel-repeated",
        "content-before-sentinel",
        "footer-heading-repeated",
        "footer-bullet-malformed",
        "unpermitted-content",
    }
)


def _warn_raw_refusal(result: dict[str, object]) -> None:
    """Name which grammar rule refused the report, without echoing its content."""
    reason = result.get("_reason")
    if result["classification"] == "invalid" and reason:
        print(f"loop-cohort: raw report refused ({reason})", file=sys.stderr)


RAW_CLASSIFICATION_FIELDS = ("classification", "finding_count", "not_checked_present")


def _raw_classification_payload(result: dict[str, object]) -> dict[str, object]:
    """Project the closed emitted field set for the raw-classify contract."""
    return {field: result[field] for field in RAW_CLASSIFICATION_FIELDS}


def _classify_report(
    report_path: Path,
    state: dict,
    *,
    require_adjudication: bool = False,
    read_text: ReadText | None = None,
) -> dict:
    """Classify a reviewer report. Exits 0 for all report-content outcomes.

    Every return carries classification, fingerprints, families, and
    matches_previous_round; an ``invalid`` return also carries reason.
    """
    # Bounded read, reached from `cmd_review_record`, which holds the state lock — so a
    # reviewer report that is a FIFO or an arbitrarily large file would otherwise block
    # or read without limit inside the critical section.
    #
    # The path is RESOLVED first, deliberately. Unlike `spec.md` / `plan.md` this is a
    # user-supplied `--report` argument, not managed state: it carries no confinement
    # claim, and a symlinked report worked before this change. Reading the unresolved
    # path would make `O_NOFOLLOW` refuse it, narrowing a shipped CLI's accepted inputs
    # for no security benefit — the author chose the path. Resolving keeps the size and
    # FIFO bounds, which are the parts that matter under the lock.
    reader = read_text or _read_managed_text
    try:
        report_text = reader(report_path.resolve(), report_path.name)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        # The reason is REPORTED, not discarded. This returns `invalid` at exit 0, so
        # without a diagnostic an unreadable report is indistinguishable from one that
        # genuinely contains no findings — and that classification feeds the review
        # retry accounting.
        print(
            f"loop-cohort: warning — {_diag(report_path.name)} could not be read "
            f"({_diag(exc)}); classified invalid",
            file=sys.stderr,
        )
        return _invalid("unreadable")

    actionable_text, refusal = _actionable_review_text(
        report_text,
        require_adjudication=require_adjudication,
    )
    if refusal is not None:
        return _invalid(refusal)

    fps, families = parse_finding_identities(actionable_text)
    if require_adjudication:
        has_clean = actionable_text == CLEAN_SUBSTRING
    else:
        has_clean = (
            CLEAN_SUBSTRING in actionable_text
            or _SHIP_IT_RE.search(actionable_text) is not None
        )

    if fps:
        classification = "findings"
    elif has_clean:
        classification = "clean"
    else:
        # No fingerprints and no clean sentinel. Reachable on the flagless
        # legacy path; name it like every other refusal so a consumer reading
        # `reason` never sees a missing key.
        return _invalid("no-actionable-result")

    canonical_fps = sorted(set(fps))
    previous = sorted(set(state.get("finding_fingerprints", [])))

    # Empty-vs-empty is always false (not stasis — no meaningful comparison)
    matches_prev = bool(canonical_fps and canonical_fps == previous)

    return {
        "classification": classification,
        "fingerprints": canonical_fps,
        "families": sorted(set(families)),
        "matches_previous_round": matches_prev,
    }


def _print_review_result(result: dict, *, as_json: bool, verb: str) -> None:
    """Print one review classification without report content or path data."""
    if as_json:
        print(json.dumps(result))
        return
    print(
        f"loop-cohort: review {verb} classification={result['classification']} "
        f"fingerprints={len(result['fingerprints'])} "
        f"matches_previous_round={result['matches_previous_round']}"
    )


# ── review-record idempotency ─────────────────────────────────────────────
#
# `--operation-id` names the round being recorded, so a session that re-issues a
# recording after losing its own record of whether the write landed gets one
# write rather than two. The id is `<run_id>:<transition_sequence>` supplied by
# the caller and validated here; this module never reads `engine-state.json`.
#
# The payload digest is STORED, not derived on read. Deriving it is unsound: the
# fingerprint and all-skipped branches overwrite `finding_fingerprints` and never
# touch `last_review_clean_source`, the clean branches do the reverse, and no
# field records which form closed a round — so `state.json` stops describing a
# round's payload as soon as the next round lands.

# `\A`/`\Z`, not `^`/`$`: Python's `$` also matches before a trailing newline,
# so `"<run>:1\n"` would pass and then compare unequal to `"<run>:1"` -- two
# spellings of one round, each recording separately. `[0-9]` rather than `\d`
# for the same reason: `\d` accepts Unicode decimal digits.
_REVIEW_OP_ID_RE = re.compile(r"\A(?P<run>[^:\n]+):(?P<seq>[0-9]{1,18})\Z")
_REVIEW_OP_ID_MAX = 200


def _review_payload_digest(form: str, payload: str) -> str:
    r"""`sha256(form + "\n" + payload)`. The form prefix stops two forms colliding."""
    return hashlib.sha256(f"{form}\n{payload}".encode()).hexdigest()


def _review_operation_decision(
    state: dict,
    operation_id: str | None,
    payload_digest: str | None,
    *,
    expect_run_id: str,
    spec_name: str,
    allow_durable_operation_id: bool = False,
) -> tuple[str, str | None]:
    """Decide the recorded round's fate before any mutation.

    Returns `(outcome, reason)`. `outcome` is one of:

    - `"unflagged"` — no id supplied; behave exactly as before and leave the two
      recorded fields alone. They name the last round recorded *under an id*,
      which a flagless round does not become.
    - `"already"`   — this id and this payload are already recorded; no mutation.
    - `"record"`    — proceed with the mutation and set both fields.
    - `"refuse"`    — caller must surface the accompanying reason.
    """
    if operation_id is None:
        return "unflagged", None

    if len(operation_id) > _REVIEW_OP_ID_MAX:
        # Its own message. Folding this into the format refusal below would tell
        # an operator the format was wrong when the format may be perfectly
        # correct and only the length is not.
        return "refuse", (
            f"review record: --operation-id is {len(operation_id)} characters, "
            f"over the {_REVIEW_OP_ID_MAX}-character limit, for {spec_name}"
        )

    if allow_durable_operation_id:
        if not SHA256_RE.fullmatch(operation_id):
            return "refuse", (
                "review record: internal transition operation id must be a "
                f"SHA-256 transition id (got {operation_id!r}) for {spec_name}"
            )
        matched = None
    else:
        matched = _REVIEW_OP_ID_RE.match(operation_id)

    # A leading zero is a second spelling of the same sequence, and the recorded
    # id is compared by exact string equality, so `:01` and `:1` would each
    # record the round once.
    if not allow_durable_operation_id:
        canonical = matched is not None and (
            matched.group("seq") == "0" or not matched.group("seq").startswith("0")
        )
        if not canonical:
            return "refuse", (
                f"review record: --operation-id must be "
                f"'<expect-run-id>:<decimal-sequence>' with no leading zero "
                f"(got {operation_id!r}) for {spec_name}"
            )
        if matched.group("run") != expect_run_id:
            return "refuse", (
                f"review record: --operation-id names run {matched.group('run')!r} "
                f"but --expect-run-id is {expect_run_id!r} for {spec_name}"
            )
    if payload_digest is None:
        # Refusing here is what keeps a later repeat decidable: an id recorded
        # without a comparison value could never be judged a replay.
        return "refuse", (
            "review record: this round's payload digest could not be computed, "
            "so recording it under an operation id would leave a later repeat "
            f"undecidable; re-run once the payload is readable, for {spec_name}"
        )

    recorded_id = state.get("last_review_record_operation_id")
    if recorded_id == operation_id:
        if state.get("last_review_record_payload_digest") == payload_digest:
            return "already", (
                f"review record already recorded for operation "
                f"{operation_id!r} (idempotent no-op) for {spec_name}"
            )
        return "refuse", (
            f"review record: operation {operation_id!r} is already recorded with "
            f"a different payload; a replay must carry the payload it recorded. "
            f"Compare against last_review_record_payload_digest in "
            f"`loop-cohort status --json` for {spec_name}"
        )
    return "record", None


def _record_review_state(
    state: dict,
    *,
    expected_run_id: str,
    spec_name: str,
    form: str,
    operation_id: str | None,
    payload_digest: str | None,
    fingerprints: list[str] | None = None,
    clean_source: str | None = None,
    clean_digest: str | None = None,
    allow_retry_cap_override: bool = False,
    allow_durable_operation_id: bool = False,
    non_negative_int: Callable[..., Any] | None = None,
    default_cap: int | None = None,
) -> tuple[dict, str]:
    """Return state after recording a review round through a shared mutator.

    `non_negative_int` and `default_cap` come from the caller that owns the
    counters' validation and default; omitted, the guard layer's are used.
    """
    if non_negative_int is None or default_cap is None:
        guards = _loop_guards()
        non_negative_int = non_negative_int or guards.non_negative_int
        if default_cap is None:
            default_cap = guards.DEFAULTS["max_review_retries"]
    outcome, reason = _review_operation_decision(
        state,
        operation_id,
        payload_digest,
        expect_run_id=expected_run_id,
        spec_name=spec_name,
        allow_durable_operation_id=allow_durable_operation_id,
    )
    if outcome == "refuse":
        raise ValueError(str(reason))
    if outcome == "already":
        return copy.deepcopy(state), "already"
    updated = copy.deepcopy(state)
    if outcome == "record":
        updated["last_review_record_operation_id"] = operation_id
        updated["last_review_record_payload_digest"] = payload_digest
    updated["previous_finding_fingerprints"] = list(
        updated.get("finding_fingerprints", [])
    )
    rounds = non_negative_int(updated, "review_round_count", 0)
    if isinstance(rounds, str):
        raise ValueError(f"review record: {rounds} for {spec_name}")
    if form == "findings":
        stored_fingerprints = sorted(set(fingerprints or []))
        retries = non_negative_int(updated, "review_retry_count", 0)
        cap = non_negative_int(
            updated, "max_review_retries", default_cap
        )
        if isinstance(retries, str):
            raise ValueError(f"review record: {retries} for {spec_name}")
        if isinstance(cap, str):
            raise ValueError(f"review record: {cap} for {spec_name}")
        if retries >= cap and not allow_retry_cap_override:
            raise ValueError(
                f"review record: review retry cap reached ({retries}/{cap}) for "
                f"{spec_name}; a findings round past the cap is the runaway "
                f"the cap exists to stop — stop and surface it. Only a human "
                f"directing this run may continue: reset and start a new run, or "
                f"pass --allow-retry-cap-override to this command AND to the "
                f"`loop-engine transition findings-remain` that opens the round "
                f"(either half alone leaves the cohort and the engine a round apart)"
            )
        updated["finding_fingerprints"] = stored_fingerprints
        updated["review_retry_count"] = retries + 1
        updated["review_round_count"] = rounds + 1
        return updated, "recorded"
    if form == "all-skipped":
        updated["finding_fingerprints"] = []
        updated["review_round_count"] = rounds + 1
        return updated, "recorded"
    if form == "clean":
        updated["finding_fingerprints"] = []
        updated["review_round_count"] = rounds + 1
        updated["last_review_clean_source"] = clean_source
        updated["last_review_clean_digest"] = clean_digest
        return updated, "recorded"
    raise ValueError(f"review record: unknown form {form!r}")


@dataclass(frozen=True)
class RecordForm:
    """One round's payload, read from the command line and the files it names."""

    form: str
    fingerprints: list[str]
    clean_source: str | None
    clean_digest: str | None
    digest: str | None


def _resolve_record_form(
    args: argparse.Namespace,
    state: dict,
    *,
    read_text: ReadText | None,
) -> RecordForm | str:
    """Read a round's payload; return it, or the one-line reason it is refused.

    Every clean form rests on bytes read back from disk, so a recorded clean
    round is never the caller's own assertion about what a reviewer said.
    """
    if getattr(args, "all_skipped", False):
        # All-skipped branch: every warranted reviewer was a named skip
        return RecordForm(
            "all-skipped", [], None, None, _review_payload_digest("all-skipped", "")
        )

    if args.fingerprint:
        # Findings branch: --fingerprint <hex> ...
        fingerprints = sorted(set(args.fingerprint))
        bad = [fp for fp in fingerprints if not _RE_FINGERPRINT.match(fp)]
        if bad:
            return (
                f"review record: --fingerprint must be lowercase 64-char SHA-256 hex "
                f"(40-char SHA-1 still accepted for a run that predates core 2.3.0); "
                f"invalid: {bad!r}"
            )
        digest = _review_payload_digest("fingerprint", "\n".join(fingerprints))
        return RecordForm("findings", fingerprints, None, None, digest)

    # Clean branches: a persisted byte-equal or structural raw return, or a
    # validated adjudication report.
    direct_clean_file = getattr(args, "direct_clean_file", None)
    if direct_clean_file is not None:
        if args.adjudication:
            return (
                "review record: --direct-clean-file and --adjudication name two "
                "different recording forms; use --report <path> --adjudication "
                "for an adjudicated clean"
            )
        artifact_path = _resolved_report(direct_clean_file)
        try:
            raw = artifact_path.read_bytes()
        except OSError:
            return (
                "review record: --direct-clean-file is unreadable; persist the "
                "reviewer's complete return before recording"
            )
        # Byte comparison, not a decode-then-compare: an encoding that merely
        # round-trips to the sentinel is not the sentinel.
        if raw != CLEAN_SUBSTRING.encode("utf-8"):
            return "review record: --direct-clean-file requires the exact clean sentinel"
        clean_source = "direct-clean"
        clean_digest: str | None = hashlib.sha256(raw).hexdigest()
    elif structural_clean_file := getattr(args, "structural_clean_file", None):
        if args.adjudication:
            return (
                "review record: --structural-clean-file and --adjudication name two "
                "different recording forms"
            )
        artifact_path = _resolved_report(structural_clean_file)
        result = _classify_raw_report(artifact_path, read_text=read_text)
        if result["classification"] != "clean":
            _warn_raw_refusal(result)
            return (
                "review record: --structural-clean-file requires a clean raw-report classification"
            )
        # A disclosure footer is prose, and prose is what the adjudicator exists
        # to read. Its content is never trusted here, so a footer-bearing report
        # is never fast-pathed however well-formed it looks. This reads
        # `not_checked_present` for ROUTING only; classification above is
        # decided without it (AC2.4).
        if result["not_checked_present"]:
            return (
                "review record: a report carrying a '## Not checked' footer is not "
                "eligible for the clean fast path; route it through "
                "finding-adjudicator and record with --report … --adjudication"
            )
        clean_source = "structural-clean"
        # The digest comes from the same read that classified the artifact. A
        # second read here would let a concurrent write make the recorded audit
        # anchor attest to content that was never classified clean.
        clean_digest = result["_classified_digest"]
        if not isinstance(clean_digest, str):
            return (
                "review record: --structural-clean-file produced no digest for "
                "the classified bytes; re-persist the reviewer's return"
            )
    else:
        if not args.report:
            return (
                "review record: one of --direct-clean-file, --structural-clean-file, --report, or "
                "--fingerprint is required"
            )
        if not args.adjudication:
            return (
                "review record: --report requires --adjudication; use "
                "--direct-clean-file for a persisted exact raw clean return"
            )
        report_path = _resolved_report(args.report)
        classified = _classify_report(
            report_path,
            state,
            require_adjudication=True,
            read_text=read_text,
        )
        if classified["classification"] != "clean":
            cls = classified["classification"]
            return (
                f"review record --report: report classified as {cls!r}; "
                "use --fingerprint for a findings round"
            )
        clean_source = "report"
        try:
            clean_digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
        except OSError:
            # _classify_report already read it; a race here loses provenance
            # but must not undo a classification that succeeded.
            clean_digest = None

    digest = (
        None
        if clean_digest is None
        else _review_payload_digest(clean_source, clean_digest)
    )
    return RecordForm("clean", [], clean_source, clean_digest, digest)


def _record_success_line(form: RecordForm, updated: dict, name: str) -> str:
    """Return the one line a recorded round prints."""
    if form.form == "all-skipped":
        return (
            f"loop-cohort: review record (all-skipped) "
            f"round={updated['review_round_count']} for {name}"
        )
    if form.form == "findings":
        return (
            f"loop-cohort: review record (findings) "
            f"round={updated['review_round_count']} retry={updated['review_retry_count']} "
            f"fingerprints={len(form.fingerprints)} for {name}"
        )
    return (
        f"loop-cohort: review record (clean:{form.clean_source}) "
        f"round={updated['review_round_count']} "
        f"retry={updated['review_retry_count']} for {name}"
    )


# ── commands: state-free classification ───────────────────────────────────


def run_classify(args: argparse.Namespace, *, read_text: ReadText | None = None) -> int:
    """Strictly classify an adjudication report without cohort state."""
    report_path = _resolved_report(args.report)
    result = _classify_report(
        report_path,
        {},
        require_adjudication=True,
        read_text=read_text,
    )
    _print_review_result(result, as_json=args.json, verb="classify")
    return 0


def run_raw_classify(args: argparse.Namespace, *, read_text: ReadText | None = None) -> int:
    """Classify a raw reviewer report without cohort state."""
    full = _classify_raw_report(_resolved_report(args.report), read_text=read_text)
    _warn_raw_refusal(full)
    result = _raw_classification_payload(full)
    if args.json:
        print(json.dumps(result))
    else:
        print(
            "loop-cohort: review raw-classify "
            f"classification={result['classification']} "
            f"finding_count={result['finding_count']} "
            f"not_checked_present={result['not_checked_present']}"
        )
    return 0


# ── commands: with cohort state ───────────────────────────────────────────
#
# `host` is the object that owns cohort state I/O: `loop-cohort.py` passes its
# own, and this script's CLI loads `loop-cohort.py` for one. It supplies
# `resolve_spec_dir`, `state_path_for`, `read_state`, `write_state_atomic`,
# `validate_run_id`, `with_state_lock`, `stop`, `emit`, `read_text`,
# `non_negative_int`, and `default_cap`.


def run_inspect(args: argparse.Namespace, host: Any) -> int:
    """Classify a report against the cohort's previous round, read-only."""
    try:
        spec_dir = host.resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return int(host.stop(str(exc)))
    try:
        state = host.read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        # Operational error (spec-dir unresolvable or state.json unreadable)
        return int(host.stop(str(exc)))

    report_path = _resolved_report(args.report)
    result = _classify_report(
        report_path,
        state,
        require_adjudication=args.adjudication,
        read_text=host.read_text,
    )

    _print_review_result(result, as_json=args.json, verb="inspect")
    return 0  # content outcomes always exit 0


def run_record(args: argparse.Namespace, host: Any) -> int:
    """Record one review round into the cohort's `state.json`, under its lock."""
    try:
        spec_dir = host.resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return int(host.stop(str(exc)))
    return int(
        host.with_state_lock(
            spec_dir, "review record", lambda: _record_with_state(args, spec_dir, host)
        )
    )


def _record_with_state(args: argparse.Namespace, spec_dir: Path, host: Any) -> int:
    """Body of `run_record`, run while the cohort state lock is held."""
    try:
        state = host.read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return int(host.stop(str(exc)))
    reason = host.validate_run_id(state, args.expect_run_id, verb="review record")
    if reason is not None:
        return int(host.stop(reason))

    operation_id = getattr(args, "operation_id", None)
    form = _resolve_record_form(args, state, read_text=host.read_text)
    if isinstance(form, str):
        return int(host.stop(form))
    try:
        updated, status = _record_review_state(
            state,
            expected_run_id=args.expect_run_id,
            spec_name=spec_dir.name,
            form=form.form,
            operation_id=operation_id,
            payload_digest=form.digest,
            fingerprints=form.fingerprints,
            clean_source=form.clean_source,
            clean_digest=form.clean_digest,
            allow_retry_cap_override=getattr(args, "allow_retry_cap_override", False),
            non_negative_int=host.non_negative_int,
            default_cap=host.default_cap,
        )
    except ValueError as exc:
        return int(host.stop(str(exc)))
    if status == "already":
        host.emit(
            f"review record already recorded for operation "
            f"{operation_id!r} (idempotent no-op) for {spec_dir.name}"
        )
        return 0
    host.write_state_atomic(spec_dir, updated)
    print(_record_success_line(form, updated, spec_dir.name))
    return 0


# ── commands: without cohort state ────────────────────────────────────────


def _reject_constant(name: str) -> NoReturn:
    """Refuse `NaN` and `Infinity`, which strict JSON does not have."""
    raise ValueError(f"non-finite JSON constant {name}")


def _load_review_cap() -> int:
    """Return `max_review_retries` from `review-rules.json`."""
    try:
        info = os.lstat(REVIEW_RULES_PATH)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_REPORT_BYTES:
            raise ArtifactError("rules-unavailable")
        rules = json.loads(
            REVIEW_RULES_PATH.read_bytes().decode("utf-8"),
            parse_constant=_reject_constant,
        )
    except (OSError, ValueError, RecursionError) as exc:
        raise ArtifactError("rules-unavailable") from exc
    cap = rules.get("max_review_retries") if isinstance(rules, dict) else None
    if isinstance(cap, bool) or not isinstance(cap, int) or cap < 0:
        raise ArtifactError("rules-unavailable")
    return cap


_admission_module: ModuleType | None = None


def _check_override_authority(reference: str | None) -> bool:
    """Return whether `reference` is an owner authority reference.

    Asks the supervisor's own checker, so the accepted form cannot drift from
    what `work-supervisor.py start --authority-ref` accepts. A checker that cannot
    load refuses the override.
    """
    global _admission_module
    if reference is None:
        return False
    try:
        if _admission_module is None:
            _admission_module = _load_sibling(
                "_supervisor_admission.py", "_review_artifact_supervisor_admission"
            )
        return bool(_admission_module.check_authority_ref(reference, OVERRIDE_AUTHORITY_ROLE))
    except Exception:
        return False


def _parse_record(data: bytes, run_id: str, round_number: int) -> dict[str, Any]:
    """Return one `record` artifact's body, or refuse it as `invalid-record`."""
    try:
        body = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (ValueError, RecursionError) as exc:
        raise ArtifactError("invalid-record") from exc

    def counter(key: str) -> bool:
        value = body.get(key)
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0

    def text_or_none(key: str) -> bool:
        return body.get(key) is None or isinstance(body.get(key), str)

    fingerprints = body.get("fingerprints") if isinstance(body, dict) else None
    well_formed = (
        isinstance(body, dict)
        and body.get("record_version") == RECORD_VERSION
        and body.get("run_id") == run_id
        and body.get("round") == round_number
        and body.get("form") in RECORD_FORMS
        and isinstance(fingerprints, list)
        and all(isinstance(f, str) and _RE_FINGERPRINT.match(f) for f in fingerprints)
        and all(
            text_or_none(k)
            for k in ("clean_source", "clean_digest", "operation_id", "payload_digest",
                      "authority_ref")
        )
        and all(
            counter(k)
            for k in ("review_round_count", "review_retry_count", "max_review_retries")
        )
        and isinstance(body.get("override"), bool)
        and isinstance(body.get("stdout"), str)
    )
    if not well_formed:
        raise ArtifactError("invalid-record")
    return body


def _load_records(root: Path, run_id: str) -> list[dict[str, Any]]:
    """Return a run's `record` artifacts in round order.

    The run directory opens through the no-follow descriptor walk. A name that
    ends in `-record.md` but is not a canonical round, a gap in the rounds, and
    a record that does not parse each refuse the command; none is skipped.
    """
    if not _descriptor_walk_supported():
        raise ArtifactError("unsafe-artifact")
    try:
        directory_fd = _open_run_directory(root, run_id)
    except FileNotFoundError:
        return []
    except PermissionError as exc:
        raise ArtifactError("unreadable") from exc
    except OSError as exc:
        raise ArtifactError("unsafe-artifact") from exc
    try:
        # A descriptor, not a path: `Path.iterdir` would re-resolve the run
        # directory and give up the no-follow guarantee.
        names = os.listdir(directory_fd)  # noqa: PTH208
    finally:
        os.close(directory_fd)

    rounds: list[int] = []
    for name in names:
        if not name.endswith("-record.md"):
            continue
        matched = _RECORD_NAME_RE.fullmatch(name)
        if matched is None:
            raise ArtifactError("invalid-record")
        rounds.append(int(matched.group("round")))
    rounds.sort()
    if rounds != list(range(1, len(rounds) + 1)):
        raise ArtifactError("invalid-record")
    return [
        _parse_record(
            read_artifact(ArtifactMetadata(root, run_id, number, None, None, "record")),
            run_id,
            number,
        )
        for number in rounds
    ]


def _previous_state(records: list[dict[str, Any]]) -> dict:
    """The cohort-shaped counters a run's `record` artifacts add up to."""
    return {
        "review_round_count": len(records),
        "review_retry_count": sum(r["form"] == "findings" for r in records),
        "finding_fingerprints": list(records[-1]["fingerprints"]) if records else [],
    }


def run_inspect_run(args: argparse.Namespace) -> int:
    """`inspect` without cohort state: the previous round comes from `record` artifacts."""
    run_id = _parse_run_id(args.run_id)
    records = _load_records(_resolve_root(args.root), run_id)
    result = _classify_report(
        _resolved_report(args.report),
        _previous_state(records),
        require_adjudication=args.adjudication,
    )
    _print_review_result(result, as_json=args.json, verb="inspect")
    return 0


def _refuse(code: str, reason: str) -> int:
    """Print a fixed refusal code, with the human reason on stderr."""
    print(f"INVALID {code}")
    print(f"review-artifact: {_diag(reason)}", file=sys.stderr)
    return 3


def run_record_run(args: argparse.Namespace) -> int:
    """`record` without cohort state: one `record` artifact per recorded round."""
    run_id = _parse_run_id(args.run_id)
    if getattr(args, "expect_run_id", None) not in (None, run_id):
        raise UsageError("invalid-metadata")
    override = bool(args.allow_retry_cap_override)
    if args.authority_ref is not None and not override:
        raise UsageError("invalid-command")
    if override and not _check_override_authority(args.authority_ref):
        return _refuse(
            "authority-refused",
            "--allow-retry-cap-override needs --authority-ref holding an "
            f"{OVERRIDE_AUTHORITY_ROLE} authority reference",
        )
    root = _resolve_root(args.root)
    cap = _load_review_cap()
    records = _load_records(root, run_id)
    previous = _previous_state(records)

    form = _resolve_record_form(args, previous, read_text=None)
    if isinstance(form, str):
        return _refuse("invalid-form", form)

    operation_id = getattr(args, "operation_id", None)
    matching = next(
        (r for r in records if operation_id is not None and r["operation_id"] == operation_id),
        None,
    )
    state = {
        **previous,
        "max_review_retries": cap,
        "last_review_record_operation_id": matching and matching["operation_id"],
        "last_review_record_payload_digest": matching and matching["payload_digest"],
    }
    outcome, reason = _review_operation_decision(
        state, operation_id, form.digest, expect_run_id=run_id, spec_name=run_id
    )
    if outcome == "refuse":
        return _refuse("operation-refused", str(reason))
    if outcome == "already" and matching is not None:
        print(matching["stdout"])
        return 0
    if form.form == "findings" and previous["review_retry_count"] >= cap and not override:
        return _refuse(
            "retry-cap-reached",
            f"review retry cap reached ({previous['review_retry_count']}/{cap}) for {run_id}",
        )
    try:
        updated, _status = _record_review_state(
            state,
            expected_run_id=run_id,
            spec_name=run_id,
            form=form.form,
            operation_id=operation_id,
            payload_digest=form.digest,
            fingerprints=form.fingerprints,
            clean_source=form.clean_source,
            clean_digest=form.clean_digest,
            allow_retry_cap_override=override,
            default_cap=cap,
        )
    except ValueError as exc:
        return _refuse("record-refused", str(exc))

    line = _record_success_line(form, updated, run_id)
    body = {
        "record_version": RECORD_VERSION,
        "run_id": run_id,
        "round": updated["review_round_count"],
        "form": form.form,
        "fingerprints": updated["finding_fingerprints"],
        "clean_source": form.clean_source,
        "clean_digest": form.clean_digest,
        "operation_id": operation_id,
        "payload_digest": form.digest,
        "review_round_count": updated["review_round_count"],
        "review_retry_count": updated["review_retry_count"],
        "max_review_retries": cap,
        "override": override,
        "authority_ref": args.authority_ref if override else None,
        "stdout": line,
    }
    data = (json.dumps(body, allow_nan=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _create_with_descriptor_walk(root, run_id, f"{body['round']}-record.md", data)
    print(line)
    return 0


# ── CLI ───────────────────────────────────────────────────────────────────


def _load_cohort_host() -> Any:
    """Load `loop-cohort.py`, the owner of cohort state I/O, and return its host."""
    try:
        module = _load_sibling("loop-cohort.py", "_review_artifact_cohort")
    except Exception as exc:
        raise ArtifactError("cohort-unavailable") from exc
    if getattr(module, "_g", None) is None:
        raise ArtifactError("cohort-unavailable")
    return module._review_host()


def _cohort_host_for(args: argparse.Namespace) -> Any | None:
    """Return the cohort host when cohort state governs this call, else `None`.

    A spec directory holding `state.json` is cohort state; `--run-id` then plays
    no part. No spec directory, or one with no `state.json`, plus `--run-id` is
    the no-cohort path.
    """
    if args.spec_dir is None:
        if args.run_id is None:
            raise UsageError("invalid-command")
        return None
    host = _load_cohort_host()
    if args.run_id is None:
        return host
    try:
        spec_dir = host.resolve_spec_dir(args.spec_dir)
    except ValueError:
        return host  # the cohort path words this refusal
    return host if os.path.lexists(host.state_path_for(spec_dir)) else None


def _run_validate(args: argparse.Namespace) -> int:
    """Validate one report and emit only fixed status, size, and digest fields."""
    metadata = _parse_metadata(args)
    size, digest = validate_artifact(metadata)
    if metadata.expected_sha256 is not None and digest != metadata.expected_sha256:
        raise ArtifactError("unstable-artifact")
    print(f"VALID size={size} sha256={digest}")
    return 0


def _build_parser() -> QuietArgumentParser:
    """Build the closed CLI; every path argument is a root, a report, or a spec dir."""
    parser = QuietArgumentParser(prog="review-artifact", add_help=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", add_help=True)
    validate.add_argument("--root", required=True)
    validate.add_argument("--run-id", required=True)
    validate.add_argument("--round", dest="round_number", required=True)
    validate.add_argument("--review-stage")
    validate.add_argument("--reviewer-role")
    validate.add_argument("--kind", required=True)
    validate.add_argument("--expected-sha256")

    classify = subparsers.add_parser("classify", add_help=True)
    classify.add_argument("--report", required=True)
    classify.add_argument("--json", action="store_true")

    raw = subparsers.add_parser("raw-classify", add_help=True)
    raw.add_argument("--report", required=True)
    raw.add_argument("--json", action="store_true")

    inspect = subparsers.add_parser("inspect", add_help=True)
    inspect.add_argument("spec_dir", nargs="?")
    inspect.add_argument("--report", required=True)
    inspect.add_argument("--adjudication", action="store_true")
    inspect.add_argument("--json", action="store_true")
    inspect.add_argument("--run-id")
    inspect.add_argument("--root", default=".")

    record = subparsers.add_parser("record", add_help=True)
    record.add_argument("spec_dir", nargs="?")
    forms = record.add_mutually_exclusive_group(required=True)
    forms.add_argument("--direct-clean-file", default=None)
    forms.add_argument("--structural-clean-file", default=None)
    forms.add_argument("--report", default=None)
    forms.add_argument("--fingerprint", action="append", default=None)
    forms.add_argument("--all-skipped", action="store_true", default=False)
    record.add_argument("--adjudication", action="store_true")
    record.add_argument(
        "--allow-retry-cap-override",
        action="store_true",
        dest="allow_retry_cap_override",
    )
    record.add_argument("--authority-ref")
    record.add_argument("--operation-id", default=None, dest="operation_id")
    record.add_argument("--expect-run-id", dest="expect_run_id")
    record.add_argument("--run-id")
    record.add_argument("--root", default=".")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one command, printing only fixed status text on a refusal."""
    try:
        args = _build_parser().parse_args(argv)
        if args.command == "validate":
            return _run_validate(args)
        if args.command == "classify":
            return run_classify(args)
        if args.command == "raw-classify":
            return run_raw_classify(args)
        host = _cohort_host_for(args)
        if args.command == "inspect":
            return run_inspect(args, host) if host else run_inspect_run(args)
        if host is None:
            return run_record_run(args)
        if args.expect_run_id is None:
            raise UsageError("invalid-command")
        return run_record(args, host)
    except UsageError:
        print("INVALID invalid-metadata")
        return 2
    except ArtifactError as exc:
        print(f"INVALID {exc.code}")
        return 3
    except (OSError, ValueError):
        print("INVALID unsafe-artifact")
        return 3


if __name__ == "__main__":
    sys.exit(main())
