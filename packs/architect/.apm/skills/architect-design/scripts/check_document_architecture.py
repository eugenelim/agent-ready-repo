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


_ABBREVIATIONS = ("e.g.", "i.e.", "etc.", "vs.")
_DECIMAL_PATTERN = re.compile(r"(?<=\d)\.(?=\d)")
_INITIAL_PATTERN = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]\.(?=\s)")
_SENTENCE_INITIAL_CLASS = (
    r"[A-Z0-9"  # ASCII capitals and digits
    r"`"  # inline code
    r"\"'“‘"  # straight and curly opening quotes
    r"\*"  # markdown emphasis/bold marker
    r"—"  # em dash
    r"À-ÖØ-Þ"  # Latin-1 Supplement capitals
    r"☀-➿"  # dingbats and misc symbols (emoji-adjacent)
    r"\U0001f300-\U0001faff"  # emoji blocks
    r"]"
)
_SENTENCE_BOUNDARY_PATTERN = re.compile(
    r"[.!?]+(?=\s+" + _SENTENCE_INITIAL_CLASS + r")"
)


def _mask_initial(match: re.Match[str]) -> str:
    """Blank only the period of a lone-letter token, e.g. an inline `a.` label."""
    return match.group(0)[0] + "․"


def count_sentences(paragraph: str) -> int:
    """Count sentences in one `DA3` prose paragraph.

    Abbreviation periods, decimal points, and a lone letter's period (an
    inline enumeration label, e.g. `a.`, or an initial) are masked first, by
    literal replacement, so none of them reads as a sentence boundary; every
    replacement is one character for one character, so no later offset
    shifts. The boundary itself fires on any sentence-initial token, not only
    an ASCII capital: a digit, a backtick, a straight or curly quote, a
    markdown emphasis marker, an em dash, a Latin-1 accented capital, or an
    emoji all open a new sentence. The boundary pattern carries no nested
    quantifier and no alternation inside a repetition, the two constructs
    that make backtracking super-linear.
    """
    masked = paragraph
    for abbreviation in _ABBREVIATIONS:
        masked = masked.replace(abbreviation, abbreviation.replace(".", "․"))
    masked = _DECIMAL_PATTERN.sub("․", masked)
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
