#!/usr/bin/env python3
"""Enforce the DA3 paragraph budget and the DA10 size trigger on a design document.

`architect-design` ships two mechanizable document-architecture gates: `DA3`
flags a prose paragraph carrying more than three sentences, and `DA10` flags a
document over the size bound `references/design-doc-rubric.md` derives. This
script is a human- or CI-run accelerant outside the convergence loop —
`SKILL.md` step 6 states that the agent running the skill does not invoke it.

It never executes repository code and imports nothing beyond the Python
standard library and its co-located `file_safety.py` sibling, loaded by path
rather than by `import` so an adopter install with no `agentbundle` package
still runs it.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
MAX_BYTES = 1_048_576
SENTENCE_BUDGET = 3
WORD_BOUND = 3_300

_file_safety_module: Any = None


def _load_regular_sibling(path: Path, module_name: str, required: set[str]) -> Any:
    """Load a co-located module by path, refusing a link-like or incomplete one.

    Several skills ship a same-named `file_safety.py`, so this binds the
    module by path rather than by bare name — a bare import would bind
    whichever directory reached `sys.path` first, and cache that choice for
    every later importer — using
    `importlib.util.spec_from_file_location` under a private module name
    instead.
    """
    try:
        inspected = os.lstat(path)
    except OSError as exc:
        raise ImportError(f"required helper is unavailable: {path.name}") from exc
    if not stat.S_ISREG(inspected.st_mode) or stat.S_ISLNK(inspected.st_mode):
        raise ImportError(f"required helper is not a regular file: {path.name}")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"required helper cannot be loaded: {path.name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    missing = sorted(required - set(vars(module)))
    if missing:
        sys.modules.pop(module_name, None)
        raise ImportError(
            f"required helper is incomplete: {path.name}: {', '.join(missing)}"
        )
    return module


def file_safety() -> Any:
    """Load only the co-located byte projection of the blessed confinement helper."""
    global _file_safety_module
    if _file_safety_module is None:
        _file_safety_module = _load_regular_sibling(
            SCRIPT_DIR / "file_safety.py",
            "_architect_design_file_safety",
            {"UnsafeContentError", "read_confined_regular_file"},
        )
    return _file_safety_module


class Refusal(Exception):
    """A target the gate declines to read, carrying the path and why."""

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(reason)
        self.path = path
        self.reason = reason

    def render(self) -> str:
        """Render this refusal for stderr, with the path and reason both escaped.

        `reason` can embed the caller-supplied path again (`read_target`
        builds it from `str(exc)`), so it is escaped here too, not only
        `path`: a raw newline or ANSI escape inside either field must not
        reach the terminal or forge a second output line.
        """
        return f"{self.path!r}: refused: {self.reason!r}"


@dataclass(frozen=True)
class Finding:
    """One `DA3` or `DA10` finding, rendered as a single output line."""

    gate: str
    path: str
    message: str
    line: int | None = None

    def render(self) -> str:
        """Render this finding as one line, with the path escaped."""
        location = f"{self.path!r}:{self.line}" if self.line is not None else f"{self.path!r}"
        return f"{location}: {self.gate} — {self.message}"


_FRONTMATTER_PATTERN = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
_HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)


def _mask(match: re.Match[str]) -> str:
    """Blank a matched span to whitespace, keeping line numbers and word gaps intact."""
    return "".join("\n" if character == "\n" else " " for character in match.group(0))


def strip_excluded(text: str) -> str:
    """Blank YAML frontmatter and HTML-comment spans, which `DA3` and `DA10` both exclude.

    A matched span is replaced with whitespace of the same shape rather than
    deleted, so a line number reported downstream still points at the
    original file, and content on either side of a span is not joined into
    one token.
    """
    without_frontmatter = _FRONTMATTER_PATTERN.sub(_mask, text, count=1)
    return _HTML_COMMENT_PATTERN.sub(_mask, without_frontmatter)


_WORD_TOKEN_PATTERN = re.compile(r"\S+")
_ALPHANUMERIC_PATTERN = re.compile(r"[A-Za-z0-9]")


def count_words(text: str) -> int:
    """Count `DA10` words: whitespace-separated tokens carrying an alphanumeric character.

    Applied after `strip_excluded`, so frontmatter and HTML-comment spans are
    never counted.
    """
    stripped = strip_excluded(text)
    return sum(
        1
        for token in _WORD_TOKEN_PATTERN.findall(stripped)
        if _ALPHANUMERIC_PATTERN.search(token)
    )


_FENCE_PATTERN = re.compile(r"^ {0,3}(```|~~~)")
_HEADING_PATTERN = re.compile(r"^ {0,3}#{1,6}(\s|$)")
_TABLE_ROW_PATTERN = re.compile(r"^\s*\|")
_LIST_ITEM_PATTERN = re.compile(r"^\s*([-*+]|\d+[.)])(\s|$)")
_BLOCKQUOTE_PATTERN = re.compile(r"^\s*>")


def prose_paragraphs(text: str) -> Iterator[tuple[int, str]]:
    """Yield `(start_line, text)` for each blank-line-separated `DA3` prose paragraph.

    A fenced block is tracked as a span, so a table row or list marker inside
    it is not read as one outside a fence. A heading line ends any paragraph
    above it without starting a sticky exclusion, so wrapped prose directly
    under a heading still yields one paragraph holding the prose alone. A
    table row, list item or block-quote line starts a sticky exclusion that
    swallows its own wrapped continuation lines — lines carrying no marker of
    their own — until a blank line, a heading, or a fence boundary ends it.
    """
    in_fence = False
    fence_marker = ""
    non_prose_block = False
    current: list[str] = []
    current_start = 0

    def _flush() -> Iterator[tuple[int, str]]:
        if current:
            yield current_start, "\n".join(current)

    for index, line in enumerate(text.splitlines(), start=1):
        fence_match = _FENCE_PATTERN.match(line)
        if fence_match:
            yield from _flush()
            current.clear()
            if not in_fence:
                in_fence = True
                fence_marker = fence_match.group(1)
            elif fence_match.group(1) == fence_marker:
                in_fence = False
            non_prose_block = False
            continue
        if in_fence:
            continue
        if not line.strip():
            yield from _flush()
            current.clear()
            non_prose_block = False
            continue
        if _HEADING_PATTERN.match(line):
            yield from _flush()
            current.clear()
            non_prose_block = False
            continue
        if (
            _TABLE_ROW_PATTERN.match(line)
            or _LIST_ITEM_PATTERN.match(line)
            or _BLOCKQUOTE_PATTERN.match(line)
        ):
            yield from _flush()
            current.clear()
            non_prose_block = True
            continue
        if non_prose_block:
            continue
        if not current:
            current_start = index
        current.append(line)
    yield from _flush()


_ABBREVIATIONS = (
    "e.g.", "i.e.", "etc.", "vs.", "cf.", "et al.", "incl.", "approx.",
    "Fig.", "No.", "Sec.", "Ref.",
)
# An ellipsis is a terminator only in appearance; masking it keeps
# "...standards... live in ..." from reading as two sentences.
_ELLIPSIS_PATTERN = re.compile(r"\.{3}|…")
_DECIMAL_PATTERN = re.compile(r"(?<=\d)\.(?=\d)")
# A terminator keeps its boundary through any run of CLOSING delimiters
# standing between it and the whitespace. Only closers belong here: an
# opening delimiter after a terminator is already whitespace-separated from
# it. Both patterns below consult this class, and both have to: tolerating
# closers in the boundary alone lets the lone-letter mask lose sight of its
# own label through a code span, which turns an under-count into an
# over-count on `Set `a.` then continue.`
#
# The set is every Unicode close-punctuation and final-quote character
# (categories `Pe` and `Pf`), plus the ASCII quotes and the four Markdown
# marks that close a span. It is written out rather than swept from
# `unicodedata` at import, because the sweep costs about 130ms on every
# invocation to rebuild a set that changes only when Unicode does; a test
# regenerates it and fails on drift, so the literal is checked rather than
# trusted. Deriving it from the categories is what
# makes "a closing mark of any script" true instead of a hand-list that
# happens to cover the scripts its author thought of.
_CLOSING_CHARACTERS = (
    # Markdown span marks, the ASCII quotes, and the ASCII brackets.
    "*_`~\"')]}"
    # Unicode categories `Pe` (close punctuation) and `Pf` (final quote).
    "»༻༽᚜’”›⁆⁾₎⌉⌋〉❩❫❭❯❱❳❵⟆⟧⟩⟫⟭⟯⦄⦆⦈⦊⦌⦎"
    "⦐⦒⦔⦖⦘⧙⧛⧽⸃⸅⸊⸍⸝⸡⸣⸥⸧⸩⹖⹘⹚⹜〉》」』】〕〗〙〛〞"
    "〟﴾︘︶︸︺︼︾﹀﹂﹄﹈﹚﹜﹞）］｝｠｣"
)
_CLOSING_DELIMITERS = "[" + re.escape(_CLOSING_CHARACTERS) + "]*"
# Only a LOWERCASE lone letter is an enumeration label (`a.`, `b.`). An
# uppercase one is far more often a single-letter name ending a sentence
# ("...over Y. The record...") than an initial, and masking it drops a real
# boundary. The apostrophe classes keep a contraction or possessive
# ("doesn't.", "reviewer's.") from reading as a lone letter.
_INITIAL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9'’ʼ])[a-z]\.(?=" + _CLOSING_DELIMITERS + r"\s)"
)
# Any non-space opens a sentence. An allowlist of sentence-initial characters
# has unbounded holes -- a markdown link, a parenthesis or a non-Latin capital
# each silently drop a boundary, which is the under-count DA3 exists to catch.
# The masking above neutralises the prose cases that must not split
# (abbreviations, decimals, ellipses, lowercase enumeration labels). Two
# classes are knowingly accepted as over-counts rather than masked, because
# both are markup rather than prose and neither reaches a rendered design
# document's paragraph text: a line ending in a terminator immediately before
# a Starlight `:::` fence, and one before an unstripped `-->`. The stripping
# pass removes a COMPLETE `<!-- ... -->` span, so the second arises only from
# a `-->` with no opening `<!--` above it -- malformed source, but reachable
# on this gate's own input rather than impossible on it.
# A third joins them and does reach prose: a code span whose content ends in a
# terminator followed by another mark, as in "the pattern `foo.*` here", reads
# as a sentence end. It is accepted for the same reason the masking above is
# shaped the way it is -- the alternative is masking what a code span
# contains, which would stop counting a span that IS a sentence ("`Code.`")
# and trade a visible over-count for the silent under-count this gate exists
# to catch.
#
# The closer tolerance also widens one over-count that already existed: `!`
# and `?` are not always terminators, and "Compute n! before allocation."
# already read as two sentences because the `!` was followed by a space.
# Bracketing it ("Compute ⟨n!⟩ before allocation.") used to hide it and
# now does not, since `⟩` is close punctuation. That is the same accepted
# class reached through one more syntax rather than a new one, and narrowing
# the closer set to exclude mathematical brackets would not fix it -- the
# unbracketed form is the common one and stays over-counted either way.
#
# The closing side had the same unbounded-holes problem, and it was not
# reasoned about here originally. Requiring whitespace immediately after the
# terminator made any delimiter between the two swallow the boundary, so a
# bold lead-in, an emphasised or code-spanned sentence, a closing quote of
# any script, or a parenthesised aside each registered nothing -- and a
# paragraph delimiting every sentence read as one. Skipping the closer run
# fixes the class rather than an enumerated list of its instances.
# `(?<![.!?])` anchors the match to the START of a terminator run. Without
# it the engine retries the whole run from each position inside it, and each
# retry rescans the closer run behind the lookahead: quadratic in the length
# of a run of terminators, on an input this script accepts up to `MAX_BYTES`.
# The anchor changes no count, because `[.!?]+` already consumed the run
# greedily from its first character.
_SENTENCE_BOUNDARY_PATTERN = re.compile(
    r"(?<![.!?])[.!?]+(?=" + _CLOSING_DELIMITERS + r"\s+\S)"
)


def _mask_initial(match: re.Match[str]) -> str:
    """Blank only the period of a lone-letter token, e.g. an inline `a.` label."""
    return match.group(0)[0] + "․"


def count_sentences(paragraph: str) -> int:
    """Count sentences in one `DA3` prose paragraph.

    Abbreviation periods, decimal points, ellipses, and the period of a
    LOWERCASE lone letter (an inline enumeration label, `a.`) are masked
    first, by literal replacement, so none of them reads as a sentence
    boundary; every replacement is one character for one character, so no
    later offset shifts. An UPPERCASE lone letter is deliberately not masked:
    it is far more often a single-letter name ending a sentence
    ("...over Y. The record...") than an initial, so masking it dropped a
    real boundary. The cost is that a genuine initial over-counts
    ("J. Smith said." reads as two), which `_MUST_OVERCOUNT` pins.

    The boundary itself fires on any non-space opener rather than a listed
    set of characters, because an enumerated set has unbounded holes and each
    one silently under-counts. It also skips any run of closing delimiters
    between the terminator and the whitespace, for the same reason on the
    other side. The boundary pattern carries no nested quantifier and no
    alternation inside a repetition, the two constructs that make
    backtracking super-linear; the closer class and the whitespace class
    share no character, so the added repetition stays linear too.

    One residual is irreducible rather than unfixed. A one-letter sentence
    end behind a delimiter ("...is `x.` Three.") and an enumeration label
    behind one ("Set `a.` then continue.") are the same shape, and only what
    follows separates them; the mask cannot read that, so it treats both as
    labels and under-counts the first. Splitting instead would over-count
    the second, and the choice went to the reading that leaves ordinary
    prose alone.
    """
    masked = paragraph
    for abbreviation in _ABBREVIATIONS:
        masked = masked.replace(abbreviation, abbreviation.replace(".", "․"))
    masked = _DECIMAL_PATTERN.sub("․", masked)
    masked = _ELLIPSIS_PATTERN.sub(lambda m: "․" * len(m.group(0)), masked)
    masked = _INITIAL_PATTERN.sub(_mask_initial, masked)
    boundaries = len(_SENTENCE_BOUNDARY_PATTERN.findall(masked))
    return boundaries + 1 if masked.strip() else 0


def read_target(root: Path, path: Path, max_bytes: int) -> str:
    """Read and decode one confined target, refusing rather than raising.

    `root` is canonicalized here, before any comparison, so a symlinked root
    still confines to its real directory. `path` itself is never
    canonicalized: resolving it first would collapse the very symlink
    components the helper's no-follow descriptor walk exists to inspect.
    Instead `path` is re-expressed as `canonical_root` joined with its
    remainder relative to the *declared* root, so a relative `path` under a
    relative or symlinked `root` (`--root .`, the documented CLI invocation)
    still confines correctly — the vendored helper's own `relative_to(root)`
    check can only match when both operands share the same absolute base.
    The remainder is computed against `canonical_root` first, so a target
    already expressed through the root's resolved form (as one already
    walking through a symlinked root's real directory) still matches without
    a second attempt.
    """
    try:
        canonical_root = root.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise Refusal(str(path), "declared root cannot be resolved safely") from exc
    try:
        remainder = path.relative_to(canonical_root)
    except ValueError:
        try:
            remainder = path.relative_to(root)
        except ValueError as exc:
            raise Refusal(str(path), "source path is outside its declared root") from exc
    joined = canonical_root / remainder
    safety = file_safety()
    try:
        data = safety.read_confined_regular_file(canonical_root, joined, max_bytes=max_bytes)
    except safety.UnsafeContentError as exc:
        raise Refusal(str(path), str(exc)) from exc
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Refusal(str(path), f"target is not valid UTF-8: {exc}") from exc


def evaluate_target(root: Path, path: Path) -> list[Finding]:
    """Read one target and return every `DA3` and `DA10` finding it carries."""
    text = read_target(root, path, MAX_BYTES)
    findings: list[Finding] = []
    word_count = count_words(text)
    if word_count > WORD_BOUND:
        findings.append(
            Finding("DA10", str(path), f"{word_count} words (bound {WORD_BOUND})")
        )
    for start_line, paragraph in prose_paragraphs(strip_excluded(text)):
        sentence_count = count_sentences(paragraph)
        if sentence_count > SENTENCE_BUDGET:
            findings.append(
                Finding(
                    "DA3",
                    str(path),
                    f"paragraph of {sentence_count} sentences (budget {SENTENCE_BUDGET})",
                    line=start_line,
                )
            )
    return findings


def _parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="explicit confinement root")
    parser.add_argument("targets", nargs="+", type=Path, help="document paths to check")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the `DA3`/`DA10` gate CLI."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = _parser().parse_args(argv)
    try:
        file_safety()
    except ImportError as exc:
        print(f"check_document_architecture: {exc}", file=sys.stderr)
        return 2
    findings: list[Finding] = []
    refused = 0
    for target in args.targets:
        try:
            findings.extend(evaluate_target(args.root, target))
        except Refusal as refusal:
            refused += 1
            print(refusal.render(), file=sys.stderr)
    for finding in findings:
        print(finding.render())
    if refused:
        print(
            f"check_document_architecture: {refused} of {len(args.targets)} target(s) refused",
            file=sys.stderr,
        )
        return 2
    if findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
