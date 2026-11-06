"""_review_tiers — the review tier a repaired subject earns from its diff.

A tier decides which selected roles report again on a new review subject. It
never adds or removes a role. Every check fails closed: a doubt, an error, an
oversized read, or a construct the scan does not recognise classifies ``full``.

The classifier reads only what the caller hands it: the anchor facts recorded
when the last full-set round closed, the current result, and a Git port whose
reads are bounded. It holds no state and writes nothing.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import difflib
import fnmatch
import posixpath
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

__all__ = [
    "FULL",
    "MINOR_FIX",
    "READ_LIMIT",
    "REBASE",
    "TIERS",
    "WORDING_ONLY",
    "AnchorFacts",
    "Tier",
    "TierGit",
    "Uncertain",
    "classify",
    "glob_match",
    "instruction_reached",
    "scan_markdown",
]

FULL = "full"
MINOR_FIX = "minor-fix"
REBASE = "rebase"
WORDING_ONLY = "wording-only"
TIERS = (WORDING_ONLY, REBASE, MINOR_FIX, FULL)

# The most bytes any single Git process or blob read may return.
READ_LIMIT = 1024 * 1024
# `git patch-id --verbatim` first shipped in Git 2.39.
_VERBATIM_GIT = (2, 39)
# The import depth agent hosts follow from an instruction file.
_MAX_HOPS = 5
_REGULAR_MODES = frozenset({"100644", "100755"})
_SYMLINK_MODE = "120000"
# An ``@`` reference that is not part of a word or an email address.
_REFERENCE = re.compile(r"(?<![\w.@])@([^\s`'\"()<>\[\]{}]+)")
# Characters a changed prose line may not carry: code, links, autolinks, markup, imports.
_FORBIDDEN_IN_PROSE = ("`", "[", "]", "<", ">", "@", "http://", "https://", "www.")
_BLOCK_STARTS = ("#", "|", ">", "<", "```", "~~~", ":::", "{", "$$", "[", "<!--")


class Uncertain(Exception):
    """A check could not decide; the subject classifies ``full``."""


class TierGit(Protocol):
    """The bounded Git reads the classifier needs."""

    def git_version(self) -> tuple[int, int]: ...

    def entries(self, rev: str) -> Mapping[str, tuple[str, str]]:
        """``path -> (mode, object id)`` for every entry at *rev*."""
        ...

    def blob(self, oid: str) -> bytes:
        """The bytes of *oid*; raises ``Uncertain`` past ``READ_LIMIT``."""
        ...

    def patch_id(self, base: str, result: str, path: str) -> str:
        """``git patch-id --verbatim`` of the diff of *path* from *base* to *result*."""
        ...


@dataclass(frozen=True)
class AnchorFacts:
    """What the supervisor recorded when the anchor round closed."""

    anchor_result: str
    run_base: str | None
    changed_paths: frozenset[str]
    patch_ids: Mapping[str, str] | None


@dataclass(frozen=True)
class Tier:
    """A tier and the reason it was chosen."""

    name: str
    reason: str


def glob_match(pattern: str, path: str) -> bool:
    """Match a POSIX path against a glob whose ``*`` never crosses ``/``.

    A ``**`` segment matches zero or more whole segments; every other segment
    matches one path segment with ``fnmatch`` rules, case-sensitively.
    """
    return _segments_match(pattern.split("/"), path.split("/"))


def _segments_match(pattern: list[str], parts: list[str]) -> bool:
    if not pattern:
        return not parts
    if pattern[0] == "**":
        return any(_segments_match(pattern[1:], parts[i:]) for i in range(len(parts) + 1))
    return (
        bool(parts)
        and fnmatch.fnmatchcase(parts[0], pattern[0])
        and _segments_match(pattern[1:], parts[1:])
    )


# ── the Markdown line scan ──────────────────────────────────────────────────


def scan_markdown(text: str) -> list[str]:
    """One block kind per line: ``prose``, ``blank``, or a kind no wording edit may touch.

    The kinds are ``frontmatter``, ``fence``, ``comment``, ``indented``, and
    ``markup``. A line that starts a construct the scan does not model is
    ``markup``, so it can never pass as prose.
    """
    lines = text.split("\n")
    kinds: list[str] = []
    fence: str | None = None
    in_comment = False
    in_front = bool(lines) and lines[0].strip() == "---"
    for number, line in enumerate(lines):
        stripped = line.strip()
        if in_front:
            kinds.append("frontmatter")
            if number > 0 and stripped in ("---", "..."):
                in_front = False
            continue
        if fence is not None:
            kinds.append("fence")
            if stripped.startswith(fence):
                fence = None
            continue
        if in_comment:
            kinds.append("comment")
            if "-->" in line:
                in_comment = False
            continue
        if stripped.startswith(("```", "~~~")):
            fence = stripped[:3]
            kinds.append("fence")
            continue
        if stripped.startswith("<!--"):
            kinds.append("comment")
            in_comment = "-->" not in stripped[4:]
            continue
        if not stripped:
            kinds.append("blank")
        elif line.startswith(("    ", "\t")):
            kinds.append("indented")
        elif stripped.startswith(_BLOCK_STARTS) or "<!--" in line:
            kinds.append("markup")
        else:
            kinds.append("prose")
    return kinds


def _plain_prose(line: str) -> bool:
    return not any(token in line for token in _FORBIDDEN_IN_PROSE)


def _wording_only_file(old: str, new: str) -> bool:
    """True when every changed line is plain prose and every unchanged line keeps its kind."""
    old_lines, new_lines = old.split("\n"), new.split("\n")
    old_kinds, new_kinds = scan_markdown(old), scan_markdown(new)
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            if old_kinds[i1:i2] != new_kinds[j1:j2]:
                return False
            continue
        for kinds, lines in (
            (old_kinds[i1:i2], old_lines[i1:i2]),
            (new_kinds[j1:j2], new_lines[j1:j2]),
        ):
            for kind, line in zip(kinds, lines, strict=True):
                if kind != "prose" or not _plain_prose(line):
                    return False
    return True


def _changed_line_count(old: str, new: str) -> int:
    """Added plus removed lines between two texts."""
    count = 0
    matcher = difflib.SequenceMatcher(a=old.split("\n"), b=new.split("\n"), autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            count += (i2 - i1) + (j2 - j1)
    return count


# ── instruction-reached files ───────────────────────────────────────────────


def _instruction_named(path: str, names: Iterable[str]) -> bool:
    base = posixpath.basename(path).casefold()
    return any(base == name.casefold() for name in names)


def _text(git: TierGit, oid: str) -> str:
    data = git.blob(oid)
    if b"\0" in data:
        raise Uncertain("a scanned file holds a NUL byte")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Uncertain("a scanned file is not UTF-8") from exc


def _resolve_reference(referrer: str, reference: str) -> str:
    if reference.startswith(("/", "~")):
        raise Uncertain(f"an @ reference in {referrer} is absolute or home-relative")
    joined = posixpath.normpath(posixpath.join(posixpath.dirname(referrer), reference))
    if joined == ".." or joined.startswith("../") or posixpath.isabs(joined):
        raise Uncertain(f"an @ reference in {referrer} leaves the repository")
    return joined


def _regular_target(
    entries: Mapping[str, tuple[str, str]], git: TierGit, path: str
) -> str | None:
    """The regular file *path* names, following one symlink; None when absent.

    A reference through a symlinked directory, to a submodule, or to a symlink
    whose target is not a regular file is uncertain.
    """
    parts = path.split("/")
    for depth in range(1, len(parts)):
        prefix = "/".join(parts[:depth])
        if prefix in entries:
            raise Uncertain(f"{path} passes through a non-directory entry")
    entry = entries.get(path)
    if entry is None:
        return None
    mode, oid = entry
    if mode in _REGULAR_MODES:
        return path
    if mode == _SYMLINK_MODE:
        target = _resolve_reference(path, _text(git, oid))
        found = entries.get(target)
        if found is None or found[0] not in _REGULAR_MODES:
            raise Uncertain(f"the symlink {path} does not name a regular file")
        return target
    raise Uncertain(f"{path} is neither a regular file nor a symlink")


def instruction_reached(
    git: TierGit, result: str, names: Iterable[str]
) -> frozenset[str]:
    """Every file an instruction-named file reaches by ``@`` references, within five hops.

    The instruction-named files themselves are included, each at its symlink
    target when it is a symlink. A reference found past the fifth hop, or one
    that cannot be resolved safely, raises ``Uncertain``.
    """
    names = tuple(names)
    entries = git.entries(result)
    frontier: set[str] = set()
    for path in entries:
        if _instruction_named(path, names):
            target = _regular_target(entries, git, path)
            if target is not None:
                frontier.add(target)
    reached: set[str] = set(frontier)
    for hop in range(_MAX_HOPS + 1):
        following: set[str] = set()
        for path in sorted(frontier):
            for match in _REFERENCE.finditer(_text(git, entries[path][1])):
                reference = match.group(1).rstrip(".,;:!?")
                if "/" not in reference and "." not in reference:
                    continue  # a handle or mention, not a path
                if hop == _MAX_HOPS:
                    raise Uncertain("an @ reference lies beyond the fifth hop")
                target = _regular_target(entries, git, _resolve_reference(path, reference))
                if target is not None and target not in reached:
                    following.add(target)
        reached |= following
        frontier = following
        if not frontier:
            break
    return frozenset(reached)


# ── the classifier ──────────────────────────────────────────────────────────


def _delta_paths(
    anchor_entries: Mapping[str, tuple[str, str]],
    current_entries: Mapping[str, tuple[str, str]],
    paths: Iterable[str],
) -> dict[str, tuple[str, str]]:
    """``path -> (anchor oid, current oid)`` for each path whose content differs."""
    delta: dict[str, tuple[str, str]] = {}
    for path in sorted(set(paths)):
        before, after = anchor_entries.get(path), current_entries.get(path)
        if before is None and after is None:
            continue
        if before is None or after is None:
            raise Uncertain(f"{path} was added or deleted since the anchor")
        if before[0] not in _REGULAR_MODES or after[0] not in _REGULAR_MODES:
            raise Uncertain(f"{path} is not a regular file on both sides")
        if before[0] != after[0]:
            raise Uncertain(f"{path} changed mode since the anchor")
        if before[1] != after[1]:
            delta[path] = (before[1], after[1])
    return delta


def _rebase(
    git: TierGit,
    anchor: AnchorFacts,
    current: str,
    run_base: str | None,
    changed: frozenset[str],
) -> bool:
    if git.git_version() < _VERBATIM_GIT or anchor.patch_ids is None or run_base is None:
        return False
    if changed != anchor.changed_paths:
        return False
    return all(
        git.patch_id(run_base, current, path) == anchor.patch_ids.get(path)
        for path in sorted(changed)
    )


def classify(
    git: TierGit,
    rules: Mapping[str, Any],
    anchor: AnchorFacts | None,
    *,
    current: str,
    changed: Iterable[str],
    run_base: str | None,
    open_findings: bool,
    adopted_reanchor: bool,
    spec_dir_changed: bool,
    selection_changed: bool,
    review_tier: str | None,
) -> Tier:
    """The tier the current subject earns; any doubt is ``full``."""
    try:
        return _classify(
            git,
            rules,
            anchor,
            current=current,
            changed=frozenset(changed),
            run_base=run_base,
            open_findings=open_findings,
            adopted_reanchor=adopted_reanchor,
            spec_dir_changed=spec_dir_changed,
            selection_changed=selection_changed,
            review_tier=review_tier,
        )
    except Uncertain as exc:
        return Tier(FULL, str(exc))
    except Exception as exc:  # noqa: BLE001 - a classifier error must never lower the tier
        return Tier(FULL, f"classifier error: {type(exc).__name__}")


def _classify(
    git: TierGit,
    rules: Mapping[str, Any],
    anchor: AnchorFacts | None,
    *,
    current: str,
    changed: frozenset[str],
    run_base: str | None,
    open_findings: bool,
    adopted_reanchor: bool,
    spec_dir_changed: bool,
    selection_changed: bool,
    review_tier: str | None,
) -> Tier:
    if review_tier is not None:
        return Tier(FULL, "the selection asks for the full set")
    if anchor is None:
        return Tier(FULL, "no anchor facts")
    if selection_changed:
        return Tier(FULL, "the resolved roles, kinds, or classes changed since the anchor")
    if (
        adopted_reanchor
        and not spec_dir_changed
        and not open_findings
        and _rebase(git, anchor, current, run_base, changed)
    ):
        return Tier(REBASE, "the run's own patch is unchanged after an adopted reanchor")
    anchor_entries = git.entries(anchor.anchor_result)
    current_entries = git.entries(current)
    delta = _delta_paths(anchor_entries, current_entries, anchor.changed_paths | changed)
    texts: dict[str, tuple[str, str]] = {
        path: (_text(git, old), _text(git, new)) for path, (old, new) in delta.items()
    }
    allowlist = rules["prose_allowlist"]
    if not open_findings and _wording_only(git, current, allowlist, texts):
        return Tier(WORDING_ONLY, "every changed line is plain prose")
    if open_findings and set(delta) <= anchor.changed_paths:
        lines = sum(_changed_line_count(old, new) for old, new in texts.values())
        if lines <= int(rules["minor_fix_max_lines"]):
            return Tier(MINOR_FIX, f"{lines} changed lines from the anchor result")
    return Tier(FULL, "the change earns no lower tier")


def _wording_only(
    git: TierGit,
    current: str,
    allowlist: Mapping[str, Any],
    texts: Mapping[str, tuple[str, str]],
) -> bool:
    names = allowlist["instruction_names"]
    globs = allowlist["globs"]
    for path in texts:
        if not any(glob_match(glob, path) for glob in globs):
            return False
        if _instruction_named(path, names):
            return False
    reached = instruction_reached(git, current, names) if texts else frozenset()
    if any(path in reached for path in texts):
        return False
    return all(_wording_only_file(old, new) for old, new in texts.values())
