"""The real `docs/adr` corpus is partitioned exhaustively by the ADR shape lint.

Governing contract: `docs/specs/checkable-adr-metadata/spec.md`, AC-0005.

This suite reads the real `docs/adr` rather than a fixture, following
`test_index_records.py` and `test_decision_record_ordinal_uniqueness.py`
(also in this directory): a fixture proves the predicate, only the recorded
corpus proves the repository. Every walk asserts a non-empty floor before
asserting its property, so a walk that reached nothing cannot read like a
clean corpus.

The assertion is about the PARTITION, not the finding count or the exit code:
the lint reports findings against today's corpus (cleared by a later plan
task) and that residual must not make this suite red. AC-0005's predicate
covers every `*.md` directory entry less `README.md`, whatever its file
type — read, refused, and unreadable are exhaustive of every outcome an entry
can have, including a classification that raised. Membership is derived from
the directory listing at run time here, never a stored count, so a corpus
edit that adds or removes entries cannot silently escape the partition.

The lint is invoked as a subprocess against the pack source path, not the
`.claude/` projection, so this suite does not depend on a self-host run.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADR_DIR = ROOT / "docs/adr"
LINT_SCRIPT = (
    ROOT
    / "packs/governance-extras/.apm/skills/new-adr/scripts/lint-adr-shape.py"
)

_SUMMARY_RE = re.compile(
    r"^read: (\d+)  refused: (\d+)  unreadable: (\d+)$", re.MULTILINE
)


def _candidate_count() -> int:
    """Every `*.md` entry in `docs/adr` less `README.md`, whatever its type.

    Derived from the directory listing at run time — this is AC-0005's
    membership rule, read directly off `Path.iterdir()` rather than through
    the lint's own classifier, so the test does not just re-run the
    implementation against itself.
    """
    return sum(
        1
        for entry in ADR_DIR.iterdir()
        if entry.name.endswith(".md") and entry.name != "README.md"
    )


def test_the_corpus_has_candidates_to_partition() -> None:
    """Non-empty floor before the property: a walk that reached nothing must
    not be indistinguishable from a clean partition."""
    assert _candidate_count() > 0, "docs/adr holds no *.md entry besides README.md"


def test_every_candidate_lands_in_exactly_one_bucket() -> None:
    """read + refused + unreadable accounts for every candidate entry.

    Not an assertion on the finding count or the exit code: those change
    independently (a later plan task clears today's findings), while the
    partition must hold both before and after.
    """
    expected = _candidate_count()

    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), str(ADR_DIR)],
        capture_output=True,
        text=True,
    )

    match = _SUMMARY_RE.search(result.stdout)
    assert match, (
        "lint did not print the read/refused/unreadable summary line:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    read, refused, unreadable = (int(g) for g in match.groups())

    assert read + refused + unreadable == expected, (
        f"partition does not cover every candidate: read={read} "
        f"refused={refused} unreadable={unreadable} "
        f"(sum {read + refused + unreadable}) vs {expected} candidates"
    )
