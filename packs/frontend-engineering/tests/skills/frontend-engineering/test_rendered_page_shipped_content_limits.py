"""The two prohibition guards on shipped pack content.

Both criteria are universal claims over authored prose, so each names the search
that makes it checkable — and thereby makes its own blind spot visible. Neither
guard is stronger than the list it searches for, and the lists are here, in the
open, rather than implied.

The rate guard's reach is its vocabulary **at the adjacency form below**: a
listed term with a number within a bounded window either side. A rate phrased
outside the vocabulary, or further from its number than that window, is not
caught. That is the accepted blind spot, and it is a property of asking a regex
to read prose — not a defect to tighten away. Two consecutive review rounds
attacked this control from opposite sides, one for being too loose and one for
being both too loose and too tight, which is the signal that the medium cannot
decide rate-versus-count. The window is therefore fixed and documented rather
than tuned again; widening it is how the shipped "Known-clean fixtures — 4"
heading started reading as a published rate.

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

# A number near one of those terms. Percentages, decimals and bare integers all
# count; "4 known-clean fixtures" is a count, not a rate, so the window stays
# anchored on the term rather than matching any number anywhere.
#
# The separator admits punctuation and a short intervening clause, because
# "The false-positive rate, measured locally, is 4%" is a published rate and an
# earlier `\s+`-only window missed it: the comma defeated the whitespace class
# and the clause overran a two-word gap. This widens HOW a listed term may be
# separated from its number. It does not widen WHICH terms are listed — the
# Testing Strategy fixes the guard's reach as the pack-stated vocabulary, and a
# rate phrased outside it is a named, accepted blind spot.
_NUMBER = r"\d+(?:\.\d+)?\s*%?"
# After a term, the gap is wide: a rate is normally written term-first, and the
# clause between it and its number can be long — "the false-positive rate,
# measured locally, is 4%".
_GAP_AFTER = r"[\s,;:()\[\]—–-]*(?:[\w-]+[\s,;:()\[\]—–-]+){0,6}"
# Before a term, the word budget stays tight — widening it makes an ordinary
# count collide with a term further down the page, which is what the shipped
# "Known-clean fixtures — 4" heading did six words above "the false-positive
# rate is measured over". But the SEPARATOR is the same punctuation class used
# after a term, so "4%—the false-positive rate" is caught. Which punctuation
# sits between a number and its term is not a signal about whether the sentence
# publishes a rate, and letting it decide the outcome is what produced opposite
# complaints in two consecutive review rounds.
_GAP_BEFORE = r"[\s,;:()\[\]—–-]+(?:[\w-]+[\s,;:()\[\]—–-]+){0,2}"


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
                rf"(?:{_NUMBER}{_GAP_BEFORE}{re.escape(term)}"
                rf"|{re.escape(term)}{_GAP_AFTER}(?:of\s+)?{_NUMBER})",
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
        # Punctuated and clause-separated forms, which an earlier `\s+`-only
        # window let through even though the term is in the vocabulary.
        "The false-positive rate, measured locally, is 4%.",
        "The false-positive rate (on our corpus) was 0.04.",
        "Detection rate: 92%.",
        "The false-positive rate — across every clean fixture — is 4%.",
        "In our environment the false-positive rate came out at about 4%.",
        # Number-first, which the before-window still has to catch — both
        # space-separated and punctuation-separated.
        "A 4% false-positive rate.",
        "4%—the false-positive rate.",
        "4% (the false-positive rate).",
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


# ── channel names carry no device name ──────────────────────────────────────
#
# The vocabulary is NOT stated here. It ships in the reference and this guard
# reads it, which is what lets deleting the row red the guard rather than
# silently emptying it. That is the shape
# `test_the_rate_vocabulary_matches_what_the_pack_states` above already uses;
# the genericity guard beside it legitimately states its own list, because
# repository identifiers are not a rule an adopter is held to.

from frontend_engineering_rendered_page_rules import (  # noqa: E402
    fallback_channels,
    forbidden_channel_name_tokens,
    read_rules,
    read_skill,
)

SKILL_MANIFEST_ROW = "| viewports |"


def _manifest_viewports_value() -> str:
    for line in read_skill().splitlines():
        if line.strip().startswith(SKILL_MANIFEST_ROW):
            return line
    raise AssertionError("SKILL.md no longer carries a manifest `viewports` row")


def test_no_channel_is_named_for_a_device() -> None:
    """Verifies: no channel name the reference declares, and no value in the
    manifest viewports row, contains a forbidden device name.

    Scoped to declared channel names rather than to prose. A channel name is only
    ever one of the declared names, so this reaches every `.apm/**` location one
    can ship in; searching prose instead would red on legitimate shipped
    sentences that name a device without naming a channel.
    """
    md = read_rules()
    tokens = forbidden_channel_name_tokens(md)
    assert tokens, "the reference states no forbidden tokens"
    for name, _, _ in fallback_channels(md):
        for token in tokens:
            assert token not in name.lower(), f"channel {name!r} carries {token!r}"
    row = _manifest_viewports_value().lower()
    for token in tokens:
        assert token not in row, (
            f"the manifest viewports row names the device {token!r}"
        )


def test_every_shipped_channel_name_is_one_the_reference_declares() -> None:
    """The premise the scope above rests on, checked rather than assumed."""
    md = read_rules()
    declared = {name for name, _, _ in fallback_channels(md)}
    assert declared == {"narrow", "wide"}, (
        f"the reference declares {sorted(declared)}; the guard's scope claim "
        f"covers exactly the declared set, so a new name needs a decision here"
    )


def test_the_device_guard_catches_a_planted_channel_name() -> None:
    """The guard must fail on the thing it names."""
    md = read_rules()
    tokens = forbidden_channel_name_tokens(md)
    planted = [("mobile-first", "", "<=480")]
    hits = [t for name, _, _ in planted for t in tokens if t in name.lower()]
    assert hits == ["mobile"], "the guard would not catch a device-named channel"


def test_the_forbidden_token_list_is_shipped_not_stated_here() -> None:
    """Deleting the reference's table reds this guard rather than emptying it."""
    import pytest as _pytest
    from frontend_engineering_rendered_page_rules import _channel_section_rows

    gone = read_rules().replace("\n## Channels\n", "\n## Removed\n", 1)
    with _pytest.raises(AssertionError, match="Channels"):
        _channel_section_rows(gone, 1)
