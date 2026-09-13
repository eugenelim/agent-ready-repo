"""The two prohibition guards on shipped pack content.

Both criteria are universal claims over authored prose, so each names the search
that makes it checkable — and thereby makes its own blind spot visible. Neither
guard is stronger than the list it searches for, and the lists are here, in the
open, rather than implied.

A bounded search for an existing guard to reuse came back empty:
`tools/lint-conformance-portability.py` covers `tests/conformance/**` only, and
`tools/lint-plugin-route-docs.py` covers named documentation files for route
offers. Neither reaches `packs/frontend-engineering/**`, so neither can carry
the adopter-genericity criterion.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from frontend_engineering_rendered_page_rules import PACK_ROOT

# `.apm/` is the runtime export boundary: everything under it is projected into
# an adopter's environment, and nothing else in the pack is. That is the reach
# of both guards, and it is the same reach the criteria name.
SHIPPED_ROOT = PACK_ROOT / ".apm"

# Text files an adopter can read. Fixtures are included deliberately — they ship.
SHIPPED_SUFFIXES = {".md", ".html", ".json", ".toml", ".yaml", ".yml", ".txt", ".css", ".js"}


def _label(path: Path) -> str:
    """A readable path label that also works for the tmp files the mutation
    tests below feed in, which are not under the pack root."""
    try:
        return path.relative_to(PACK_ROOT).as_posix()
    except ValueError:
        return path.name


def shipped_files() -> list[Path]:
    return sorted(
        p
        for p in SHIPPED_ROOT.rglob("*")
        if p.is_file() and p.suffix.lower() in SHIPPED_SUFFIXES
    )


# ── no published rate ───────────────────────────────────────────────────────

# The pack states this vocabulary itself, in the measurement reference. The
# guard's reach IS this list: a rate phrased outside it is not caught, and this
# list is the artifact a reviewer inspects to judge the claim.
RATE_VOCABULARY = [
    "false-positive rate",
    "false positive",
    "detection rate",
    "detected",
    "missed",
    "precision",
    "recall",
    "accuracy",
]

# A number next to one of those terms. Percentages, decimals, fractions and
# bare integers all count; "4 known-clean fixtures" is a count, not a rate, so
# the window is deliberately tight and anchored on the term.
_NUMBER = r"\d+(?:\.\d+)?\s*%?"


def test_the_rate_vocabulary_matches_what_the_pack_states() -> None:
    """The guard's reach is only honest if the list it searches is the list the
    pack publishes. If the reference adds a term, this guard must gain it too."""
    stated = (
        SHIPPED_ROOT
        / "skills"
        / "frontend-engineering"
        / "references"
        / "rendered-page-measurement.md"
    ).read_text(encoding="utf-8")
    section = stated.split("## Rate vocabulary", 1)
    assert len(section) == 2, "the measurement reference no longer states a vocabulary"
    rows = re.findall(r"^\| ([a-z][a-z -]+) \|$", section[1], re.MULTILINE)
    assert sorted(rows) == sorted(RATE_VOCABULARY), (
        f"the pack states {sorted(rows)} but this guard searches "
        f"{sorted(RATE_VOCABULARY)}"
    )


@pytest.mark.parametrize("path", shipped_files(), ids=lambda p: p.name)
def test_no_shipped_content_states_a_rate(path: Path) -> None:
    """Verifies: no shipped pack content states a detection rate or a
    false-positive rate."""
    text = " ".join(path.read_text(encoding="utf-8", errors="replace").split())
    for term in RATE_VOCABULARY:
        for match in re.finditer(re.escape(term), text, re.IGNORECASE):
            window = text[max(0, match.start() - 40) : match.end() + 40]
            # A number immediately before or after the term, within the window.
            adjacent = re.search(
                rf"(?:{_NUMBER}\s+(?:\w+\s+){{0,2}}{re.escape(term)}"
                rf"|{re.escape(term)}\s+(?:\w+\s+){{0,2}}(?:of\s+)?{_NUMBER})",
                window,
                re.IGNORECASE,
            )
            assert adjacent is None, (
                f"{_label(path)} states a rate: ...{window}..."
            )


def test_the_rate_guard_catches_a_planted_rate(tmp_path: Path) -> None:
    """The guard's own mutation. Without this, a regex that matches nothing would
    pass every file and the criterion would rest on a check that cannot fail."""
    planted = tmp_path / "planted.md"
    for bad in (
        "The false-positive rate is 4%.",
        "A detection rate of 92% was measured.",
        "precision 0.91 across the corpus",
        "It missed 3 defects.",
    ):
        planted.write_text(bad, encoding="utf-8")
        with pytest.raises(AssertionError, match="states a rate"):
            test_no_shipped_content_states_a_rate(planted)


def test_the_rate_guard_allows_a_count(tmp_path: Path) -> None:
    """The green path: counts and prose about rates are fine, numbers attached to
    them are not. A guard that rejected both would make the reference unwritable."""
    ok = tmp_path / "ok.md"
    for good in (
        "The denominator is the number of known-clean fixtures you measured — 4.",
        "This pack publishes no false-positive rate.",
        "How often the step reports a page that is fine is a property of your setup.",
        "8 fixtures x 4 captures = 32 captures",
    ):
        ok.write_text(good, encoding="utf-8")
        test_no_shipped_content_states_a_rate(ok)


# ── adopter genericity ──────────────────────────────────────────────────────

# This repository's identifiers: its sites, routes, build directory and test
# harness, which is exactly what the criterion names. The guard's reach IS this
# set; an identifier outside it is not caught, and this list is what a reviewer
# inspects to judge the criterion.
#
# Deliberately NOT here, because they are an adopter's vocabulary too and
# excluding them would make the guard fire on things that are not the defect:
# `agentbundle` (the CLI an adopter installs and runs — it appears in nine
# pre-existing skills in this pack), `AGENTS.md` (adopters author their own),
# and `.apm/` (present in any catalogue, not just this one).
REPO_IDENTIFIERS = [
    "agent-ready-repo",
    "workspace.toml",
    "docs/specs/",
    "docs/rfc/",
    "docs/adr/",
    "docs/product/",
    "packs/frontend-engineering/",
    "web/src/",
    "docs-site",
    "tools/lint-",
    "make build-check",
    "make pre-pr",
    "make build-self",
    "catalogue self-host",
    "loop-engine",
    "loop-cohort",
    "CAT-S003",
]


@pytest.mark.parametrize("path", shipped_files(), ids=lambda p: p.name)
def test_no_shipped_content_names_this_repository(path: Path) -> None:
    """Verifies: no shipped pack content names this repository's sites, routes,
    build directory, or test harness.

    Reach is shipped pack content — everything under `.apm/`, fixtures included.
    The guide page is covered by its own walkability check, not by this search.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    for identifier in REPO_IDENTIFIERS:
        assert identifier not in text, (
            f"{_label(path)} names {identifier!r}, which only "
            f"exists in the repository this pack is developed in"
        )


def test_the_genericity_guard_catches_a_planted_identifier(tmp_path: Path) -> None:
    """The guard's own mutation, for the same reason as the rate guard's."""
    planted = tmp_path / "planted.md"
    for bad in (
        "See docs/specs/rendered-page-visual-inspection/spec.md for the criteria.",
        "Run make build-check before pushing.",
        "The rule lives in workspace.toml.",
    ):
        planted.write_text(bad, encoding="utf-8")
        with pytest.raises(AssertionError, match="which only exists in"):
            test_no_shipped_content_names_this_repository(planted)


def test_the_guards_actually_reach_this_deliverys_files() -> None:
    """A guard that runs over an empty file list passes trivially. This pins that
    both guards see the files this delivery ships, fixtures included."""
    names = {p.name for p in shipped_files()}
    for expected in (
        "rendered-page-inspection.md",
        "rendered-page-measurement.md",
        "defect-occlusion.html",
        "defect-clipped-at-rest-top.html",
        "clean-article.html",
        "clean-nav.html",
        "SKILL.md",
    ):
        assert expected in names, f"{expected} is not covered by the shipped-content guards"
