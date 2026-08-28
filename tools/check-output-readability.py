#!/usr/bin/env python3
"""Score eligible prose and check quiet multi-tool transcripts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple, Sequence

SOURCE_ROOT = Path(__file__).parent.parent
WORD_FLOOR = 30
READING_EASE_FLOOR = 70.0
GRADE_LEVEL_CEILING = 8.0
MAX_INPUT_BYTES = 1024 * 1024
ALLOWED_INTERRUPTIONS = frozenset(
    {
        "safety",
        "blocker",
        "user-decision",
        "material-scope-change",
        "long-wait",
        "host-requirement",
    }
)

_PROTECTED_BLOCK_RE = re.compile(
    r"<!--\s*readability:exclude:start\s*-->.*?"
    r"<!--\s*readability:exclude:end\s*-->",
    re.DOTALL | re.IGNORECASE,
)
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_INDENTED_CODE_RE = re.compile(r"^(?: {4}|\t)")
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
_CITATION_RE = re.compile(r"\[(?:\^?\d+|[A-Za-z][A-Za-z0-9_-]*,?\s+\d{4})\]")
_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_BLOCKQUOTE_RE = re.compile(r"^\s{0,3}(?:>\s?)+")
_QUOTED_FIDELITY_RE = re.compile(
    r"^(?:error|warning|source|citation)\s*:|^traceback\b|^[A-Za-z_.]*Error\s*:",
    re.IGNORECASE,
)
_TECHNICAL_TOKEN_RE = re.compile(
    r"(?<!\w)(?:--?[A-Za-z0-9-]+|[A-Za-z0-9_.-]*[/\\][A-Za-z0-9_./\\-]+|"
    r"[A-Za-z][A-Za-z0-9]*(?:_|::|\.)[A-Za-z0-9_.:-]+)(?!\w)"
)
_WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_VOWEL_GROUP_RE = re.compile(r"[aeiouy]+")


class Score(NamedTuple):
    """Estimated scores from aggregate counts."""

    reading_ease: float
    grade_level: float


class CorpusResult(NamedTuple):
    """Aggregate readability result."""

    status: str
    reason: str
    files: int
    words: int
    sentences: int
    syllables: int
    reading_ease: float | None
    grade_level: float | None


class QuietResult(NamedTuple):
    """Aggregate quiet-work transcript result."""

    status: str
    transcripts: int
    optional_messages: int
    required_messages: int


def _file_safety() -> ModuleType:
    """Load the repository's blessed file-safety code from a source checkout."""
    source = (
        SOURCE_ROOT
        / "packages"
        / "agentbundle"
        / "agentbundle"
        / "catalogue_tooling"
        / "file_safety.py"
    )
    spec = importlib.util.spec_from_file_location("_readability_file_safety", source)
    if spec is None or spec.loader is None:
        raise ValueError("file-safety-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def score_counts(*, words: int, sentences: int, syllables: int) -> Score:
    """Apply the standard Flesch formulas to validated aggregate counts."""
    if words <= 0 or sentences <= 0 or syllables <= 0:
        raise ValueError("counts-must-be-positive")
    words_per_sentence = words / sentences
    syllables_per_word = syllables / words
    reading_ease = 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word
    grade_level = 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59
    return Score(round(reading_ease, 2), round(grade_level, 2))


def estimate_syllables(word: str) -> int:
    """Return a deterministic English syllable estimate for one word."""
    normalized = re.sub(r"[^a-z]", "", word.lower())
    if not normalized:
        return 0
    count = len(_VOWEL_GROUP_RE.findall(normalized))
    syllabic_le = (
        normalized.endswith("le")
        and len(normalized) > 2
        and normalized[-3] not in "aeiouy"
    )
    if normalized.endswith("e") and not syllabic_le and count > 1:
        count -= 1
    if normalized.endswith("ed") and count > 1:
        if not normalized.endswith(("ted", "ded")):
            count -= 1
    elif normalized.endswith("es") and count > 1:
        base = normalized[:-1]
        syllabic_plural = (
            normalized.endswith(("ses", "zes", "xes", "ches", "shes", "ges", "ces"))
            or (
                base.endswith("le")
                and len(base) > 2
                and base[-3] not in "aeiouy"
            )
        )
        if not syllabic_plural:
            count -= 1
    return max(1, count)


def extract_eligible_prose(markdown: str) -> str:
    """Remove protected Markdown and technical tokens before scoring."""
    text = _PROTECTED_BLOCK_RE.sub(" ", markdown)
    kept: list[str] = []
    in_fence = False
    fence_marker = ""
    for raw_line in text.splitlines():
        fence = _FENCE_RE.match(raw_line)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        line = raw_line
        stripped = line.strip()
        if in_fence or not stripped or _INDENTED_CODE_RE.match(raw_line):
            continue
        if stripped.startswith("<!--"):
            continue
        if stripped.startswith(">"):
            line = _BLOCKQUOTE_RE.sub("", line)
            stripped = line.strip()
            if not stripped or _QUOTED_FIDELITY_RE.search(stripped):
                continue
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        if re.fullmatch(r"\s*\[[^]]+\]:\s+\S+", line):
            continue
        line = re.sub(r"^\s{0,3}(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+)", "", line)
        line = _INLINE_CODE_RE.sub(" ", line)
        line = _MARKDOWN_LINK_RE.sub(" ", line)
        line = _CITATION_RE.sub(" ", line)
        line = _URL_RE.sub(" ", line)
        line = _TECHNICAL_TOKEN_RE.sub(" ", line)
        line = re.sub(r"<[^>]+>", " ", line)
        line = re.sub(r"[*_~]", "", line)
        if _WORD_RE.search(line):
            kept.append(re.sub(r"\s+", " ", line).strip())
    return "\n".join(kept)


def _count_sentences(text: str) -> int:
    punctuated = len(re.findall(r"[.!?]+(?=\s|$)", text))
    unpunctuated_lines = sum(
        1 for line in text.splitlines() if _WORD_RE.search(line) and not re.search(r"[.!?]", line)
    )
    return punctuated + unpunctuated_lines


def evaluate_corpus(documents: Sequence[str]) -> CorpusResult:
    """Score documents as one corpus after Markdown protection."""
    eligible = "\n".join(extract_eligible_prose(document) for document in documents)
    words = _WORD_RE.findall(eligible)
    word_count = len(words)
    sentence_count = _count_sentences(eligible)
    syllable_count = sum(estimate_syllables(word) for word in words)
    if word_count < WORD_FLOOR:
        return CorpusResult(
            "insufficient",
            "below-word-floor",
            len(documents),
            word_count,
            sentence_count,
            syllable_count,
            None,
            None,
        )
    if sentence_count <= 0:
        return CorpusResult(
            "insufficient",
            "no-sentences",
            len(documents),
            word_count,
            sentence_count,
            syllable_count,
            None,
            None,
        )
    score = score_counts(
        words=word_count,
        sentences=sentence_count,
        syllables=syllable_count,
    )
    passed = (
        score.reading_ease >= READING_EASE_FLOOR
        and score.grade_level <= GRADE_LEVEL_CEILING
    )
    return CorpusResult(
        "pass" if passed else "fail",
        "thresholds-met" if passed else "thresholds-missed",
        len(documents),
        word_count,
        sentence_count,
        syllable_count,
        score.reading_ease,
        score.grade_level,
    )


def evaluate_quiet_transcript(events: Sequence[dict[str, Any]]) -> QuietResult:
    """Count optional assistant messages between the first and last tool call."""
    tool_indexes = [
        index
        for index, event in enumerate(events)
        if event.get("kind") == "tool_call"
    ]
    if len(tool_indexes) < 2:
        return QuietResult("insufficient", 1, 0, 0)
    optional = 0
    required = 0
    for event in events[tool_indexes[0] + 1 : tool_indexes[-1]]:
        if event.get("kind") != "assistant":
            continue
        if event.get("reason") in ALLOWED_INTERRUPTIONS:
            required += 1
        else:
            optional += 1
    return QuietResult("pass" if optional == 0 else "fail", 1, optional, required)


def aggregate_quiet_results(results: Sequence[QuietResult]) -> QuietResult:
    """Combine transcript results without letting a short sample hide a failure."""
    optional = sum(result.optional_messages for result in results)
    required = sum(result.required_messages for result in results)
    if any(result.status == "fail" for result in results):
        status = "fail"
    elif any(result.status == "insufficient" for result in results):
        status = "insufficient"
    else:
        status = "pass"
    return QuietResult(status, len(results), optional, required)


def _read_text_inputs(paths: Sequence[str]) -> list[str]:
    safety = _file_safety()
    root = Path.cwd()
    documents: list[str] = []
    for raw_path in paths:
        try:
            if any(part in {".", ".."} for part in raw_path.replace("\\", "/").split("/")):
                raise ValueError("input-path-invalid")
            path = Path(raw_path)
            if not path.is_absolute():
                path = root / path
            data = safety.read_confined_regular_file(
                root, path, max_bytes=MAX_INPUT_BYTES
            )
            documents.append(data.decode("utf-8"))
        except (OSError, UnicodeDecodeError, ValueError, safety.UnsafeContentError) as exc:
            raise ValueError("input-unreadable") from exc
    return documents


def _read_transcripts(paths: Sequence[str]) -> list[list[dict[str, Any]]]:
    transcripts: list[list[dict[str, Any]]] = []
    for document in _read_text_inputs(paths):
        try:
            parsed = json.loads(document)
        except json.JSONDecodeError as exc:
            raise ValueError("transcript-invalid") from exc
        events = parsed.get("events") if isinstance(parsed, dict) else parsed
        if not isinstance(events, list) or not all(isinstance(item, dict) for item in events):
            raise ValueError("transcript-invalid")
        transcripts.append(events)
    return transcripts


def _json_result(result: CorpusResult | QuietResult) -> str:
    return json.dumps(result._asdict(), sort_keys=True, separators=(",", ":"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit aggregate JSON")
    parser.add_argument("--transcript", action="store_true", help="check quiet-work JSON")
    parser.add_argument("paths", nargs="+", help="input files")
    args = parser.parse_args(argv)
    try:
        if args.transcript:
            transcripts = _read_transcripts(args.paths)
            parts = [evaluate_quiet_transcript(events) for events in transcripts]
            result: CorpusResult | QuietResult = aggregate_quiet_results(parts)
        else:
            result = evaluate_corpus(_read_text_inputs(args.paths))
    except ValueError as exc:
        print(f"output-readability: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(_json_result(result))
    elif isinstance(result, CorpusResult):
        ease = "n/a" if result.reading_ease is None else f"{result.reading_ease:.2f}"
        grade = "n/a" if result.grade_level is None else f"{result.grade_level:.2f}"
        print(
            "output-readability: "
            f"status={result.status} files={result.files} words={result.words} "
            f"sentences={result.sentences} syllables={result.syllables} "
            f"reading_ease={ease} grade_level={grade} reason={result.reason}"
        )
    else:
        print(
            "quiet-work: "
            f"status={result.status} transcripts={result.transcripts} "
            f"optional={result.optional_messages} required={result.required_messages}"
        )
    return 1 if result.status == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
