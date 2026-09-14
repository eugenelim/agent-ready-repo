#!/usr/bin/env python3
"""Describe an authored reply against the cognitive-load rule's readable effects.

Reports quantities. It asserts no direction and returns no verdict, because the
rule it serves does not say that fewer tables or fewer technical tokens are
better — it says a table is used "only when it makes a link much more clear" and
that depth, proof, limits, exact names and paths are all kept. Counting a
removed file path as an improvement would score against this repository's own
citation convention.

`check-output-readability.py` removes tables, code, links and technical tokens
before scoring, which is right for its job and wrong for this one: a table-heavy
reply scores well there because almost nothing dense survives to be scored. What
it discards is kept here as separate quantities.

Two cautions the caller must respect, both established by measurement:

  * `ease` and `grade` are affine functions of the same two ratios with opposite
    signs, so they are ONE dimension reported twice, never two agreeing signals.
  * A difference of two arm means is read against the standard error of a
    difference, never against the spread of single observations — those are
    different quantities giving different verdicts. `--stats` computes the
    pooled SD and that standard error; `--spread` reports a descriptive range
    only and is not the comparator.

Usage:
    python3 tools/score-cognition.py FILE [FILE ...]
    python3 tools/score-cognition.py --json FILE [FILE ...]
    python3 tools/score-cognition.py --pair CONTROL TREATMENT
    python3 tools/score-cognition.py --spread SAMPLE [SAMPLE ...]
"""

from __future__ import annotations

import argparse
import bisect
import importlib.util
import json
import re
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_readability", _TOOLS / "check-output-readability.py"
)
_READABILITY = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_READABILITY)

# Latin, Han, and digits count; a bare apostrophe run does not. Kana, Hangul,
# Cyrillic and Greek fall outside both ranges and yield no denominator, which
# reports as absent rather than as a clean score.
_WORD_RE = re.compile(r"[0-9A-Za-zÀ-ɏ一-鿿]+(?:'[A-Za-z]+)*")

# One dimension, reported twice. Never counted as two agreeing signals.
COUPLED = ("ease", "grade")
QUANTITIES = ("scored_pct", "table_density", "jargon_density")


def score(markdown: str) -> dict[str, object]:
    """Return the measured quantities for one authored reply."""
    raw_words = len(_WORD_RE.findall(markdown))
    prose = _READABILITY.extract_eligible_prose(markdown)
    # Counted in the readability module's own word unit, because scored_pct
    # describes that score's coverage. Its regex and this file's differ.
    scored_words = len(_READABILITY._WORD_RE.findall(prose))
    reading_words = len(_READABILITY._WORD_RE.findall(markdown))
    result = _READABILITY.evaluate_corpus([markdown])

    table_rows = sum(1 for line in markdown.splitlines() if line.strip().startswith("|"))

    # A dotted name inside an inline-code span matches both patterns; count the
    # span once. Overlapping hits are the common case in this repository.
    # Count technical tokens, then add inline spans that contain none — a
    # backticked dotted name must not count twice, and two distinct names inside
    # one span must not collapse to one.
    token_spans = [m.span() for m in _READABILITY._TECHNICAL_TOKEN_RE.finditer(markdown)]
    jargon = len(token_spans)
    # Bisect rather than scan: the input is model-generated and capped at 1 MiB,
    # so a reply dense in backticks and dotted names would otherwise cost
    # spans x tokens comparisons.
    starts = sorted(ts for ts, _ in token_spans)
    for match in _READABILITY._INLINE_CODE_RE.finditer(markdown):
        lo, hi = match.span()
        idx = bisect.bisect_left(starts, lo)
        if idx >= len(starts) or starts[idx] >= hi:
            jargon += 1

    def per_100(count: int) -> float | None:
        # No denominator means no density. Reporting 0.0 would be the best
        # possible score for a reply that could not be measured at all.
        return round(100 * count / raw_words, 2) if raw_words else None

    return {
        "scorable": result.reading_ease is not None,
        "ease": round(result.reading_ease, 2) if result.reading_ease is not None else None,
        "grade": round(result.grade_level, 2) if result.grade_level is not None else None,
        "raw_words": raw_words,
        "scored_words": scored_words,
        "scored_pct": round(100 * scored_words / reading_words, 1) if reading_words else None,
        "table_rows": table_rows,
        "table_density": per_100(table_rows),
        "jargon_density": per_100(jargon),
    }


def pair_delta(control: dict, treatment: dict) -> dict[str, object]:
    """Report treatment minus control per quantity. No direction is asserted.

    A reader decides what a movement means. `ease` and `grade` are reported
    together under one key so neither is mistaken for corroboration of the other.
    """
    deltas: dict[str, object] = {}
    for name in COUPLED + QUANTITIES:
        before, after = control.get(name), treatment.get(name)
        deltas[name] = None if before is None or after is None else round(after - before, 2)
    deltas["unmeasured"] = [k for k, v in deltas.items() if v is None]
    deltas["coupled_dimension"] = list(COUPLED)
    return deltas


def spread(samples: list[dict]) -> dict[str, object]:
    """Descriptive range across same-arm samples. NOT the comparator — see --stats."""
    out: dict[str, object] = {}
    for name in COUPLED + QUANTITIES:
        values = [s[name] for s in samples if s.get(name) is not None]
        out[name] = round(max(values) - min(values), 2) if len(values) > 1 else None
    out["samples"] = len(samples)
    return out


def arm_stats(arms: list[list[float]]) -> dict[str, object]:
    """Pooled within-arm SD and the standard error of a difference of means.

    Written here because hand-computation produced a mean-of-standard-deviations
    where a pooled figure was named, and then read a difference of means against
    the spread of single observations. Pooled SD is `sqrt(SS/df)`; the standard
    error of a difference between two arms of n is `s_p * sqrt(2/n)`.
    """
    usable = [a for a in arms if len(a) > 1]
    if not usable:
        return {"pooled_sd": None, "se_of_difference": None, "arms": len(arms), "df": 0}
    ss = 0.0
    df = 0
    for arm in usable:
        mean = sum(arm) / len(arm)
        ss += sum((v - mean) ** 2 for v in arm)
        df += len(arm) - 1
    pooled = (ss / df) ** 0.5
    n = min(len(a) for a in usable)
    return {
        "pooled_sd": round(pooled, 2),
        "se_of_difference": round(pooled * (2 / n) ** 0.5, 2),
        "sum_of_squares": round(ss, 2),
        "df": df,
        "arms": len(usable),
        "n_per_arm": n,
    }


def _read(paths: list[str]) -> list[tuple[str, str]]:
    """Read each input through the repository's blessed confinement helper.

    Scored artifacts are untrusted model output. `check-output-readability.py`
    routes the same class of input through `file_safety`; this tool must not be
    the weaker sibling in the same directory.
    """
    safety = _READABILITY._file_safety()
    # The repository this tool ships in, resolved from the tool's own location.
    # NOT the caller's cwd: `check-output-readability.py:283` roots at `cwd` and
    # therefore reads whatever tree it is invoked from. Copying it ships the hole.
    root = _TOOLS.parent
    out: list[tuple[str, str]] = []
    for raw in paths:
        if any(part in {".", ".."} for part in raw.replace("\\", "/").split("/")):
            raise ValueError(f"input-path-invalid: {raw}")
        path = Path(raw)
        if not path.is_absolute():
            path = root / path
        data = safety.read_confined_regular_file(
            root, path, max_bytes=_READABILITY.MAX_INPUT_BYTES
        )
        out.append((raw, data.decode("utf-8")))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--pair", action="store_true", help="two paths: control then treatment")
    parser.add_argument("--spread", action="store_true", help="same-arm samples")
    parser.add_argument(
        "--stats",
        action="store_true",
        help="pooled SD and the standard error of a difference; one arm per --arm group",
    )
    parser.add_argument(
        "--arm",
        action="append",
        default=[],
        metavar="FILE,FILE,...",
        help="one arm's samples, repeatable; used with --stats",
    )
    args = parser.parse_args()
    if not args.paths and not args.arm:
        parser.error("give at least one path, or --arm groups with --stats")

    try:
        documents = _read(args.paths)
    except Exception as exc:
        print(f"score-cognition: error: {type(exc).__name__}: {exc}")
        return 2

    scores = [(name, score(text)) for name, text in documents]

    if args.pair:
        if len(scores) != 2:
            parser.error("--pair takes exactly two paths")
        print(json.dumps(pair_delta(scores[0][1], scores[1][1]), indent=2))
        return 0

    if args.stats:
        groups = args.arm or [",".join(args.paths)]
        arms: list[list[float]] = []
        for group in groups:
            members = _read([x for x in group.split(",") if x])
            # `score` returns mixed value types, and a reply under the word
            # floor scores `ease` as None, so the narrowing is a real filter
            # rather than a cast: an unmeasured run must not enter the arm.
            eases = [score(text)["ease"] for _, text in members]
            arms.append([e for e in eases if isinstance(e, float)])
        print(json.dumps(arm_stats(arms), indent=2))
        return 0

    if args.spread:
        print(json.dumps(spread([s for _, s in scores]), indent=2))
        return 0

    if args.json:
        print(json.dumps(dict(scores), indent=2))
        return 0

    columns = COUPLED + QUANTITIES
    print(f"{'file':<26}" + "".join(f"{c:>16}" for c in columns))
    for path, values in scores:
        row = f"{Path(path).name:<26}"
        row += "".join(f"{values[c]!s:>16}" for c in columns)
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
