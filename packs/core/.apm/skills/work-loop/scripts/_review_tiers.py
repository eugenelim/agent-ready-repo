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
from collections.abc import Iterable, Mapping, Sequence
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
_TREE_MODE = "040000"
# The most changed paths one classification looks up, so a lookup stays one short command line.
_MAX_DELTA_PATHS = 512
# The most files, beyond the instruction files themselves, the walk follows before it gives up.
_MAX_REACHED = 256
# The most lines either side of a compared file may hold; past it the file is not compared.
MAX_DIFF_LINES = 4000
# Characters that trail a reference in Markdown without belonging to its path.
_TRAILING_MARKUP = "*_`'\")]}>.,;:!?"
# An ``@`` reference that is not part of a word or an email address (``_`` may precede one).
_REFERENCE = re.compile(r"(?<![^\W_])(?<![.@])@([^\s`'\"()<>\[\]{}]+)")
# Characters a changed prose line may not carry: code, links, autolinks, markup, imports.
_FORBIDDEN_IN_PROSE = ("`", "[", "]", "<", ">", "@", "http://", "https://", "www.")
_BLOCK_STARTS = ("#", "|", ">", "<", "```", "~~~", ":::", "{", "$$", "[", "<!--")


class Uncertain(Exception):
    """A check could not decide; the subject classifies ``full``."""


class TierGit(Protocol):
    """The bounded Git reads the classifier needs."""

    def git_version(self) -> tuple[int, int]: ...

    def entries(self, rev: str, paths: Sequence[str]) -> Mapping[str, tuple[str, str]]:
        """``path -> (mode, object id)`` for each of *paths* present at *rev*.

        The paths are literal and read one level deep; a path that names a
        directory lists its children instead of itself. Raises ``Uncertain``
        or a Git refusal past ``READ_LIMIT``.
        """
        ...

    def matching_entries(
        self, rev: str, pathspecs: Sequence[str]
    ) -> Mapping[str, tuple[str, str]]:
        """``path -> (mode, object id)`` for every non-directory entry at *rev* a pathspec matches.

        Pathspecs may carry ``icase`` and ``glob`` magic. The read is bounded.
        """
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


_FENCE_OPEN = re.compile(r"(`{3,}|~{3,})")
# A setext underline, or a thematic break written with dashes, equals signs, stars, or underscores.
_UNDERLINE = re.compile(r"\s*(=+|-+)\s*")
_THEMATIC_BREAK = re.compile(r"\s*([-*_])(\s*\1){2,}\s*")
# A table cell separator: a pipe that a backslash does not escape.
_TABLE_PIPE = re.compile(r"(?<!\\)\|")


def _closes_fence(line: str, opener: str) -> bool:
    """CommonMark: a closing fence is indented at most three spaces, then repeats the
    opener's character at least as long, then ends. A tab or a fourth space of indent
    keeps the line inside the code block."""
    indent = len(line) - len(line.lstrip(" "))
    if indent > 3 or line[indent:indent + 1] == "\t":
        return False
    body = line.strip()
    return len(body) >= len(opener) and body == opener[0] * len(body)


def scan_markdown(text: str) -> list[str]:
    """One block kind per line: ``prose``, ``blank``, or a kind no wording edit may touch.

    The kinds are ``frontmatter``, ``fence``, ``comment``, ``indented``, and
    ``markup``. A line that starts a construct the scan does not model is
    ``markup``, so it can never pass as prose. Any line holding an unescaped
    pipe is ``markup`` (a table row may omit its leading pipe), and a setext
    underline marks the lines of the heading it underlines as ``markup`` too.
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
            if _closes_fence(line, fence):
                fence = None
            continue
        if in_comment:
            kinds.append("comment")
            if "-->" in line:
                in_comment = False
            continue
        opener = _FENCE_OPEN.match(stripped)
        if opener is not None:
            fence = opener.group(1)
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
        elif (
            stripped.startswith(_BLOCK_STARTS)
            or "<!--" in line
            or _TABLE_PIPE.search(line)
            or _UNDERLINE.fullmatch(line)
            or _THEMATIC_BREAK.fullmatch(line)
        ):
            kinds.append("markup")
        else:
            kinds.append("prose")
    for number, line in enumerate(lines):
        if kinds[number] == "markup" and _UNDERLINE.fullmatch(line):
            back = number - 1
            while back >= 0 and kinds[back] == "prose":
                kinds[back] = "markup"
                back -= 1
    return kinds


def _plain_prose(line: str) -> bool:
    return not any(token in line for token in _FORBIDDEN_IN_PROSE)


def _line_matcher(old: str, new: str) -> difflib.SequenceMatcher[str]:
    """A line matcher whose cost is bounded: ``autojunk`` drops lines that repeat too often.

    A junked line only makes the match coarser, so more lines read as changed and
    the tier can only rise; it never reads a changed line as unchanged.
    """
    return difflib.SequenceMatcher(a=old.split("\n"), b=new.split("\n"))


# A line whose first non-blank character opens markup, a code fence, or raw HTML.
_MARKUP_LEADS = ("<", "`", "~")


def _plain_text(text: str) -> bool:
    """True when *text* holds only printable characters, newline, and tab, and no line
    starts (after spaces and tabs) with ``<``, a backtick, or ``~``.

    An allowlist rather than a model of Markdown: a carriage return, a byte-order mark,
    a format character, unusual whitespace, raw HTML, or anything fence-like keeps the
    file out of the wording-only tier, whatever a renderer would make of it.
    """
    if any(not (ch.isprintable() or ch in "\n\t") for ch in text):
        return False
    return not any(line.lstrip(" \t").startswith(_MARKUP_LEADS) for line in text.split("\n"))


def _has_fence_like_line(text: str) -> bool:
    """True when any line, stripped of every kind of whitespace, starts a code fence.

    Fence boundaries depend on indentation and whitespace rules a line scan can get
    wrong, so a file that holds anything fence-like is never compared line by line.
    """
    return any(line.strip().startswith(("```", "~~~")) for line in text.split("\n"))


def _wording_only_file(old: str, new: str) -> bool:
    """True when every changed line is plain prose and every unchanged line keeps its kind.

    A file holding any fence-like line at either revision is never wording-only.
    """
    if not (_plain_text(old) and _plain_text(new)):
        return False
    if _has_fence_like_line(old) or _has_fence_like_line(new):
        return False
    old_lines, new_lines = old.split("\n"), new.split("\n")
    old_kinds, new_kinds = scan_markdown(old), scan_markdown(new)
    for tag, i1, i2, j1, j2 in _line_matcher(old, new).get_opcodes():
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


def _changed_line_count(old: str, new: str, ceiling: int) -> int:
    """Added plus removed lines between two texts; counting stops once it passes *ceiling*."""
    count = 0
    for tag, i1, i2, j1, j2 in _line_matcher(old, new).get_opcodes():
        if tag != "equal":
            count += (i2 - i1) + (j2 - j1)
            if count > ceiling:
                break
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


def _glob_escape(text: str) -> str:
    """*text* as a ``glob`` pathspec that matches only itself."""
    return re.sub(r"([*?\[\\])", r"\\\1", text)


def _reference_variants(reference: str) -> set[str]:
    """Every path a Markdown reference could name once fragment and trailing markup are dropped."""
    found = {reference}
    for _ in range(2):
        for text in tuple(found):
            found.add(text.rstrip(_TRAILING_MARKUP))
            found.add(text.split("#", 1)[0])
    return {text for text in found if text}


def _lookup(
    git: TierGit, rev: str, paths: Iterable[str]
) -> dict[str, tuple[str, str] | None]:
    """The entry at each path, ``None`` for an absent path or a directory.

    A path that passes through a non-directory entry, such as a symlinked
    directory, raises ``Uncertain``.
    """
    wanted: set[str] = set()
    for path in paths:
        parts = path.split("/")
        wanted.update("/".join(parts[: depth + 1]) for depth in range(len(parts)))
    found = git.entries(rev, sorted(wanted)) if wanted else {}
    result: dict[str, tuple[str, str] | None] = {}
    for path in paths:
        parts = path.split("/")
        for depth in range(1, len(parts)):
            held = found.get("/".join(parts[:depth]))
            if held is not None and held[0] != _TREE_MODE:
                raise Uncertain(f"{path} passes through a non-directory entry")
        entry = found.get(path)
        result[path] = None if entry is None or entry[0] == _TREE_MODE else entry
    return result


def _regular(path: str, entry: tuple[str, str]) -> str:
    """The object id of a regular-file *entry*; a symlink or anything else is uncertain."""
    if entry[0] in _REGULAR_MODES:
        return entry[1]
    if entry[0] == _SYMLINK_MODE:
        raise Uncertain(f"an @ reference reaches the symlink {path}")
    raise Uncertain(f"{path} is neither a regular file nor a symlink")


def _instruction_files(
    git: TierGit, result: str, names: tuple[str, ...]
) -> dict[str, str]:
    """``path -> object id`` of every instruction-named file, a symlink read at its target."""
    specs = [":(icase,glob)**/" + _glob_escape(name) for name in names]
    found = git.matching_entries(result, specs)
    files: dict[str, str] = {}
    for path, (mode, oid) in sorted(found.items()):
        if not _instruction_named(path, names):
            continue
        if mode in _REGULAR_MODES:
            files[path] = oid
        elif mode == _SYMLINK_MODE:
            target = _resolve_reference(path, _text(git, oid))
            entry = _lookup(git, result, [target])[target]
            if entry is None or entry[0] not in _REGULAR_MODES:
                raise Uncertain(f"the symlink {path} does not name a regular file")
            files[target] = entry[1]
        else:
            raise Uncertain(f"{path} is neither a regular file nor a symlink")
    return files


def _named_by(git: TierGit, result: str, wanted: set[str]) -> dict[str, str]:
    """``path -> object id`` of every regular file the candidate paths could name.

    A candidate names an entry exactly or under ASCII case folding. A reference
    that holds non-ASCII text could name an entry under Unicode normalisation, which
    Git cannot match, so it is uncertain. A candidate that names a symlink, a
    submodule, or passes through a non-directory entry is uncertain.
    """
    if not wanted:
        return {}
    exact = _lookup(git, result, sorted(wanted))
    specs = [":(icase,glob)" + _glob_escape(path) for path in sorted(wanted)]
    folded = git.matching_entries(result, specs)
    named = {path.lower() for path in wanted}
    entries = {path: entry for path, entry in exact.items() if entry is not None}
    entries.update({p: e for p, e in folded.items() if p.lower() in named})
    return {path: _regular(path, entry) for path, entry in sorted(entries.items())}


def instruction_reached(
    git: TierGit, result: str, names: Iterable[str]
) -> frozenset[str]:
    """Every file an instruction-named file reaches by ``@`` references, within five hops.

    The instruction-named files themselves are included, each at its symlink
    target when it is a symlink. A reference counts as reaching every entry it
    could name: under case folding, with a ``#fragment`` or trailing Markdown
    dropped. A reference found past the fifth hop, to a symlink, to a non-ASCII
    name, or one that cannot be resolved safely, raises ``Uncertain``.
    """
    names = tuple(names)
    oids = _instruction_files(git, result, names)
    reached = set(oids)
    frontier = set(oids)
    roots = len(reached)
    for hop in range(_MAX_HOPS + 1):
        wanted: set[str] = set()
        for path in sorted(frontier):
            for match in _REFERENCE.finditer(_text(git, oids[path])):
                reference = match.group(1)
                trimmed = reference.rstrip(".,;:!?")
                if "/" not in trimmed and "." not in trimmed:
                    continue  # a handle or mention, not a path
                if hop == _MAX_HOPS:
                    raise Uncertain("an @ reference lies beyond the fifth hop")
                for variant in _reference_variants(reference):
                    if not variant.isascii():
                        raise Uncertain(f"an @ reference in {path} holds non-ASCII text")
                    wanted.add(_resolve_reference(path, variant))
        named = _named_by(git, result, wanted)
        following = {path: oid for path, oid in named.items() if path not in reached}
        oids.update(following)
        reached |= set(following)
        if len(reached) - roots > _MAX_REACHED:
            raise Uncertain("instruction files reach too many files to check")
        frontier = set(following)
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


def _rebase_refusal(
    git: TierGit,
    anchor: AnchorFacts,
    current: str,
    run_base: str | None,
    changed: frozenset[str],
    *,
    open_findings: bool,
    spec_dir_changed: bool,
) -> str | None:
    """Why the run's own patch cannot be called unchanged, or ``None`` when it is."""
    if spec_dir_changed:
        return "the adopted change touched the spec directory"
    if open_findings:
        return "a finding is open"
    if git.git_version() < _VERBATIM_GIT:
        return "Git is older than 2.39, which has no verbatim patch ids"
    if anchor.patch_ids is None:
        return "the anchor line records no patch ids"
    if run_base is None:
        return "the run base is undefined"
    if changed != anchor.changed_paths:
        return "the changed paths differ from the anchor's"
    for path in sorted(changed):
        if git.patch_id(run_base, current, path) != anchor.patch_ids.get(path):
            return f"the patch for {path} changed"
    return None


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
    """The tier the current subject earns; any doubt is ``full``.

    The reason of a ``full`` tier names the predicate that refused, or the Git
    refusal code that stopped a read.
    """
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
        code = getattr(exc, "code", None)
        note = f" ({code})" if code else ""
        return Tier(FULL, f"classifier error: {type(exc).__name__}{note}")


def _delta_texts(
    git: TierGit, delta: Mapping[str, tuple[str, str]]
) -> dict[str, tuple[str, str]]:
    """The two texts of each delta path; one past ``MAX_DIFF_LINES`` lines is not compared."""
    texts: dict[str, tuple[str, str]] = {}
    for path, (old, new) in delta.items():
        pair = (_text(git, old), _text(git, new))
        if any(text.count("\n") >= MAX_DIFF_LINES for text in pair):
            raise Uncertain(f"{path} is too long to compare line by line")
        texts[path] = pair
    return texts


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
    if adopted_reanchor:
        # An adopted reanchor changed the product under the anchor's paths, so a
        # path comparison proves nothing: only an unchanged patch earns a tier.
        why = _rebase_refusal(
            git, anchor, current, run_base, changed,
            open_findings=open_findings, spec_dir_changed=spec_dir_changed,
        )
        if why is not None:
            return Tier(FULL, f"an adopted reanchor is not a rebase: {why}")
        return Tier(REBASE, "the run's own patch is unchanged after an adopted reanchor")
    paths = sorted(anchor.changed_paths | changed)
    if len(paths) > _MAX_DELTA_PATHS:
        raise Uncertain(f"{len(paths)} paths changed, more than {_MAX_DELTA_PATHS} to compare")
    delta = _delta_paths(
        git.entries(anchor.anchor_result, paths), git.entries(current, paths), paths
    )
    texts = _delta_texts(git, delta)
    allowlist = rules["prose_allowlist"]
    if not open_findings and _wording_only(git, current, allowlist, texts):
        return Tier(WORDING_ONLY, "every changed line is plain prose")
    if open_findings and set(delta) <= anchor.changed_paths:
        ceiling = int(rules["minor_fix_max_lines"])
        lines = 0
        for old, new in texts.values():
            lines += _changed_line_count(old, new, ceiling - lines)
            if lines > ceiling:
                break
        if lines <= ceiling:
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
