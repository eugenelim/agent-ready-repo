"""The rung's precondition names the field wherever it is stated.

Positive exclusive property: within the swept Markdown scope, every sentence
that refers to a visual target and states a confirmation or approval condition
also contains the literal `visual_target`.

The two tests read different text, deliberately. A name is not a cue — both
`approved-visual-target` and the spaced `approved visual target` carry the word
`approved` as part of what the thing is called — so NAME_FORMS is stripped
before the cue test. A name is still a reference, so the target test reads the
unstripped sentence. Stripping it from both would exempt every carrier that
names the rung and then states its condition, which is most of the migration.

Two limits, stated so they are not rediscovered. A carrier that states the
condition using none of CONFIRMATION_CUES is outside this property, and so is
one whose only cue came from a stripped name. Widening either constant is a
deliberate edit, gated Ask-first by the owning spec.

This module lives in tests/roster/ because the sweep reads above any one pack;
tools/lint-pack-test-boundary.py refuses that from a pack suite.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SWEEP_ROOTS = ("packs", "guides", "web/src/content", "tests", "docs/design")
TARGET = re.compile(r"visual[ _-]target", re.I)
NAME_FORMS = re.compile(r"approved[ -]visual[ -]target", re.I)
CONFIRMATION_CUES = ("confirm", "approved")
SKIP_DIRS = {"__pycache__", "node_modules", ".git"}
NON_MARKDOWN_CARRIER_FLOOR = 13


def _sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+", " ".join(text.split()))


def _swept_files() -> list[Path]:
    found = []
    for root in SWEEP_ROOTS:
        for path in (REPO_ROOT / root).rglob("*"):
            if not path.is_file() or SKIP_DIRS & set(path.parts):
                continue
            found.append(path)
    return found


def _carries_target(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return TARGET.search(" ".join(text.split())) is not None


def test_every_confirmation_sentence_names_the_field() -> None:
    violations = []
    for path in _swept_files():
        # Limit 2: segmentation is meaningless outside prose. In JSON and
        # Python a whole file is one "sentence" — including this module's own
        # docstring, which explains the mechanism and would violate it.
        # AC-0011 covers the non-Markdown carriers over parsed structure.
        if path.suffix != ".md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not TARGET.search(" ".join(text.split())):
            continue
        for sentence in _sentences(text):
            # Reference test: the sentence as written.
            if not TARGET.search(sentence):
                continue
            # Cue test: name forms removed, so a name supplies no cue.
            cue_source = NAME_FORMS.sub("", sentence).lower()
            if not any(cue in cue_source for cue in CONFIRMATION_CUES):
                continue
            if "visual_target" not in sentence:
                violations.append(
                    f"{path.relative_to(REPO_ROOT)}: {sentence[:160]}"
                )
    assert not violations, "AC-0006: " + "\n".join(violations)


def test_the_non_markdown_carrier_count_has_not_fallen() -> None:
    """A sweep that finds nothing passes for the wrong reason.

    Counts the non-Markdown subset specifically. An aggregate floor over
    .md/.json/.py stays green while every non-Markdown carrier disappears and
    Markdown ones replace it, which is the shrinkage AC-0011 exists to catch.

    The floor is a measurement, so it goes stale when the tree gains a carrier.
    It read 12 until this slice's own release-pin docstring put the sweep phrase
    into test_visual_authority_release.py, taking the count to 13 excluding this
    module. Re-measure and raise it when that happens; do not add a per-file
    check, which is the closed surface set the owning spec forbids.
    """
    this_module = Path(__file__).resolve()
    reached = sum(
        1
        for path in _swept_files()
        # Exclude this module. Its own docstring says "visual target", so it
        # becomes a carrier the moment it lands and would inflate the floor by
        # one — letting a genuine carrier disappear with the guard still green.
        if path.suffix in {".json", ".py"}
        and path.resolve() != this_module
        and _carries_target(path)
    )
    assert reached >= NON_MARKDOWN_CARRIER_FLOOR, (
        f"AC-0011: sweep reached only {reached} non-Markdown carriers, "
        f"floor is {NON_MARKDOWN_CARRIER_FLOOR} (measured 2026-10-02)"
    )
