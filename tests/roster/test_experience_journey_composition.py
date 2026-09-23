"""Both journeys carry one depth ladder, one explore band, and one handoff.

The depth selector rides in a ``####`` sub-stage, which both journey lints skip
by construction: their per-stage label scan stops at the first line starting
``##``. So nothing else in the repository reads these numbers, and a field
re-tiered in the contract would leave two journeys promising a ladder that no
longer exists, with every gate green.

Two agreements are checked, and they fail differently. The **count** agreement
catches a field moving between tiers. The **explore-subset accessibility**
agreement catches the cheap path quietly dropping a state the shared map
records as accessibility-bearing — the half of the promise that is
non-waivable, and the half a count comparison cannot see.

Both counts are computed from the artifacts. Writing 10 / 25 / 32 into this
module would pin today's ladder rather than the agreement between the two
surfaces, and would keep passing after the contract moved.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

CONTRACT = (
    ROOT / "packs" / "frontend-engineering" / ".apm" / "skills"
    / "frontend-engineering" / "references" / "digital-experience-contract.md"
)
JOURNEYS = {
    "frontend-engineering": ROOT / "packs" / "frontend-engineering" / "JOURNEY.md",
    "experience-design": ROOT / "packs" / "experience-design" / "JOURNEY.md",
}

# Lowest tier first. `Required: <tier>+` means that tier and every tier above,
# so a tier's obligation is its own annotations plus every lower tier's.
TIERS = ("explore", "pilot", "production")

_ANNOTATION = re.compile(r"<!--\s*Required:\s*([a-z]+)\+\s*-->")
# `- **`explore`** — … 10 of the contract's 32 fields.` / `… 25 fields.`
_LADDER_ROW = re.compile(
    r"^- \*\*`(explore|pilot|production)`\*\* — .*?(\d+)"
    r"(?: of the contract's \d+)? fields",
    re.MULTILINE,
)
_EXPLORE_STATES = re.compile(
    r"^- \*\*`explore`\*\* — .*?States: (.+?)\.$", re.MULTILINE
)


def cumulative_obligations(contract: str) -> dict[str, int]:
    """Fields owed at each tier, counted from the contract's own annotations."""
    per_tier: dict[str, int] = dict.fromkeys(TIERS, 0)
    for tier in _ANNOTATION.findall(contract):
        assert tier in per_tier, (
            f"the contract annotates an unknown tier {tier!r}; this module's "
            f"TIERS would have to grow before its arithmetic means anything"
        )
        per_tier[tier] += 1
    running = 0
    cumulative: dict[str, int] = {}
    for tier in TIERS:
        running += per_tier[tier]
        cumulative[tier] = running
    assert running > 0, "the contract carries no Required: annotations at all"
    return cumulative


def stated_ladder(journey: str) -> dict[str, int]:
    """The field count each journey states per tier."""
    rows = _LADDER_ROW.findall(journey)
    ladder = {tier: int(count) for tier, count in rows}
    assert len(rows) == len(ladder), f"a tier is stated twice: {rows}"
    return ladder


def stated_explore_states(journey: str) -> list[str]:
    m = _EXPLORE_STATES.search(journey)
    assert m, (
        "the journey states no explore state subset in the single-line "
        "`States: `a`, `b`, ….` form this module parses"
    )
    return [s.strip().strip("`") for s in m.group(1).split(",")]


def map_rows(contract: str) -> list[list[str]]:
    after = contract.split("#### Shared state-coverage map", 1)
    assert len(after) == 2, "the shared state-coverage map is gone"
    rows: list[list[str]] = []
    seen_header = False
    for line in after[1].splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not seen_header:
            seen_header = True
            continue
        if all(set(c) <= {"-", ":"} for c in cells):
            continue
        rows.append(cells)
    assert rows, "the state-coverage map has no body rows"
    return rows


@pytest.fixture(scope="module")
def contract() -> str:
    return CONTRACT.read_text(encoding="utf-8")


@pytest.mark.parametrize("pack", sorted(JOURNEYS))
def test_the_journey_states_the_whole_ladder(contract: str, pack: str) -> None:
    """Verifies: every tier the contract annotates is stated by the journey.

    Asserted before the counts: a journey that simply omitted a tier would
    otherwise pass the comparison below over the tiers it happened to mention.
    """
    # The expected tier set comes from the contract's own annotations, not from
    # the module's TIERS constant: a tier the contract stops annotating should
    # stop being owed here, and a tier it starts annotating should start.
    expected = [tier for tier in TIERS if cumulative_obligations(contract)[tier]]
    ladder = stated_ladder(JOURNEYS[pack].read_text(encoding="utf-8"))
    missing = [tier for tier in expected if tier not in ladder]
    assert not missing, f"{pack}: the journey states no field count for {missing}"


@pytest.mark.parametrize("pack", sorted(JOURNEYS))
def test_the_stated_counts_equal_the_contracts_cumulative_obligation(
    contract: str, pack: str
) -> None:
    """Verifies: each stated count equals the contract's own annotation count
    at that tier and every lower one."""
    expected = cumulative_obligations(contract)
    stated = stated_ladder(JOURNEYS[pack].read_text(encoding="utf-8"))
    wrong = {
        tier: (stated[tier], expected[tier])
        for tier in TIERS
        if stated.get(tier) != expected[tier]
    }
    assert not wrong, (
        f"{pack}: the journey's depth ladder disagrees with the contract "
        f"(tier: stated, owed): {wrong}"
    )


@pytest.mark.parametrize("pack", sorted(JOURNEYS))
def test_the_explore_subset_keeps_every_accessibility_bearing_state(
    contract: str, pack: str
) -> None:
    """Verifies: the cheap path drops no state the map flags WCAG-bearing.

    Scoped to the banded states. A WCAG-bearing state the map marks
    `conditional` is owed at every tier when its trigger fires and belongs to no
    band, so requiring the explore list to name it would contradict the map.
    """
    protected = {
        row[0].strip().strip("`")
        for row in map_rows(contract)
        if row[3].strip() == "yes" and row[2].strip() in TIERS
    }
    assert protected, "the map flags no banded state as accessibility-bearing"
    stated = set(stated_explore_states(JOURNEYS[pack].read_text(encoding="utf-8")))
    dropped = sorted(protected - stated)
    assert not dropped, (
        f"{pack}: the explore subset omits states whose absence fails "
        f"WCAG 2.2 AA: {dropped}"
    )


@pytest.mark.parametrize("pack", sorted(JOURNEYS))
def test_the_explore_subset_is_the_maps_explore_band(
    contract: str, pack: str
) -> None:
    """Verifies: the journey's explore list is the map's explore band exactly.

    The accessibility assertion above is one-directional by design, so a journey
    could satisfy it while listing a state the map owes only at `pilot`. That
    would make the cheap path more expensive than the contract asks, which is a
    quieter failure than dropping one but is still disagreement.
    """
    band = {
        row[0].strip().strip("`")
        for row in map_rows(contract)
        if row[2].strip() == "explore"
    }
    stated = set(stated_explore_states(JOURNEYS[pack].read_text(encoding="utf-8")))
    assert stated == band, (
        f"{pack}: the journey's explore subset is not the map's explore band "
        f"(journey only: {sorted(stated - band)}; map only: {sorted(band - stated)})"
    )


def test_both_journeys_state_the_same_ladder() -> None:
    """Verifies: the two packs promise one ladder, not two.

    Each journey is compared with the contract above, so this is implied while
    both comparisons pass — and it is what fails first, and legibly, when a
    contributor updates one journey and forgets the other.
    """
    ladders = {
        pack: stated_ladder(path.read_text(encoding="utf-8"))
        for pack, path in JOURNEYS.items()
    }
    distinct = {tuple(sorted(ladder.items())) for ladder in ladders.values()}
    assert len(distinct) == 1, f"the journeys state different ladders: {ladders}"


# ── composition ─────────────────────────────────────────────────────────────

XD = ROOT / "packs" / "experience-design"

CROSSING_ARTIFACTS = (
    "direction/<slug>.md",
    "screens/<slug>/<screen>.md",
    "tokens/<slug>.md",
)

# The frontend skill already carries these four; the journey has to say so, or an
# adopter reads a journey stricter than the skill it describes.
#
# Each cue set must be distinctive of the allowance's own statement, and all of
# a set's cues must land on one line. Whole-file cues do not decide this: the
# journey independently says "a proportional contract" in its mode summary and
# "narrows or expands the contract" of a retrofit, so the earlier
# ("proportional", "contract") and ("retrofit", "narrow") sets were satisfied by
# prose that predates the allowances and stayed green when the allowance
# sentences were deleted. The cues below name the phrase each allowance turns
# on, which is what makes deleting it red.
ALLOWANCES = {
    "a contract proportional to risk": ("proportional", "risk and scope"),
    "omitting inapplicable states": ("inapplicable", "omitted"),
    "a narrowed retrofit state matrix": ("narrows the state matrix", "absent or broken"),
    "the optional token gate": ("optional", "stylelint"),
}


# The eighteen states, read from the skill rather than restated, so this module
# cannot drift from the set the map is checked against.
def floor_states() -> set[str]:
    skill = (
        ROOT / "packs" / "frontend-engineering" / ".apm" / "skills"
        / "frontend-engineering" / "SKILL.md"
    ).read_text(encoding="utf-8")
    after = skill.split("### 3. State matrix", 1)[1]
    names = set()
    seen_header = False
    for line in after.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if names:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not seen_header:
            seen_header = True
            continue
        if all(set(c) <= {"-", ":"} for c in cells):
            continue
        names.add(cells[0].strip().strip("`"))
    assert names, "the skill's state matrix parsed to nothing"
    return names


def test_each_journey_names_the_other_pack_in_related_journeys() -> None:
    """Verifies: the handoff is reciprocal.

    A one-way link only helps a reader who already arrived from the right side,
    which is the same asymmetry the frozen-record convention calls out.
    """
    for pack, other in (
        ("frontend-engineering", "experience-design"),
        ("experience-design", "frontend-engineering"),
    ):
        text = JOURNEYS[pack].read_text(encoding="utf-8")
        block = text.split("relatedJourneys:", 1)
        assert len(block) == 2, f"{pack}: the journey has no relatedJourneys key"
        listed = []
        for line in block[1].splitlines()[1:]:
            if not line.startswith("  - "):
                break
            listed.append(line[4:].strip())
        assert other in listed, (
            f"{pack}: relatedJourneys does not name {other} (has {listed})"
        )


@pytest.mark.parametrize("pack", sorted(JOURNEYS))
def test_each_journey_names_the_three_crossing_artifacts(pack: str) -> None:
    """Verifies: both sides of the handoff name the same three addresses.

    Named by their output-directory-relative paths, because the absolute
    location is an adopter's configuration and the relative path is the part
    both packs agree about.
    """
    text = JOURNEYS[pack].read_text(encoding="utf-8")
    # Matched in the backticked form both journeys write, not as a bare
    # substring: `tokens/<slug>.md` is a prefix of `tokens/<slug>.mdx`, so a
    # containment check stays green when the extension is changed underneath it.
    missing = [a for a in CROSSING_ARTIFACTS if f"`{a}`" not in text]
    assert not missing, f"{pack}: the journey does not name {missing}"


def test_the_frontend_journey_carries_its_four_proportionality_allowances() -> None:
    """Verifies: the journey is no stricter than the skill it describes.

    Each allowance is matched on the words that carry it rather than on a fixed
    sentence, so rewording the prose does not fail the check and deleting the
    allowance does. The cues for one allowance must co-occur on a single line:
    matched across the whole file, two of the four sets were satisfied by prose
    that predates these allowances, and the check stayed green with the
    allowance deleted.
    """
    lines = JOURNEYS["frontend-engineering"].read_text(encoding="utf-8").lower().splitlines()
    missing = [
        name for name, cues in ALLOWANCES.items()
        if not any(all(cue in line for cue in cues) for line in lines)
    ]
    assert not missing, (
        f"the frontend journey states no proportionality allowance for: {missing}"
    )


def test_the_design_journey_names_its_minimal_viable_thread() -> None:
    """Verifies: the cheapest coherent path through the pack is named."""
    text = JOURNEYS["experience-design"].read_text(encoding="utf-8")
    assert "minimal viable thread" in text.lower(), (
        "the design journey does not name the minimal viable thread"
    )


def illustrative_state_files() -> list[Path]:
    """Every Markdown file under `packs/experience-design/` that carries an
    illustrative state list.

    Derived from the tree rather than a pinned pair, because AC-0024 and AC-0025
    quantify over `packs/experience-design/` and a transcript added to a third
    file would otherwise be untested with nothing reporting the gap. The
    middle-dot shape is still the scoping device: it is what the transcripts
    use, and it keeps ordinary prose out.
    """
    found = [
        path for path in sorted(XD.rglob("*.md"))
        if any(
            "States" in line and "\u00b7" in line
            for line in path.read_text(encoding="utf-8").splitlines()
        )
    ]
    assert found, "no file under packs/experience-design/ carries a state list"
    return found


def test_no_illustrative_state_list_names_a_state_outside_the_floor() -> None:
    """Verifies: the design pack's worked examples use the floor's vocabulary.

    The transcripts are illustrative, not a registry — but a five-state example
    naming `default`, two screens below a depth selector promising ten named
    states, makes the pack argue with itself. Scoped to the middle-dot lists the
    transcripts use, so ordinary prose is untouched.
    """
    floor = floor_states()
    offenders: dict[str, list[str]] = {}
    for path in illustrative_state_files():
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "States" not in line or "·" not in line:
                continue
            listed = [
                s.strip().rstrip("✓").strip()
                for s in line.split(":", 1)[1].split("·")
            ]
            outside = [s for s in listed if s and s not in floor]
            if outside:
                offenders[f"{path.name}:{n}"] = outside
    assert not offenders, (
        f"these illustrative state lists name states the quality floor does not "
        f"carry: {offenders}"
    )


# ── the say-this table ──────────────────────────────────────────────────────

OPTIONALITY = ("Required", "Optional", "Choose one")

# Each say-this row names a skill an adopter types. The guide table that owns
# that skill's optionality is the how-to step it belongs to; a row with no
# owning guide (the reviewer agent) is checked for shape only.
HOW_TO = ROOT / "guides" / "experience-design" / "how-to"


def _say_this_rows() -> list[list[str]]:
    text = (XD / "JOURNEY.md").read_text(encoding="utf-8")
    body = text.split("\n---\n", 1)[1]
    rows, seen_header = [], False
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not seen_header:
            seen_header = True
            continue
        if all(set(c) <= {"-", ":"} for c in cells):
            continue
        rows.append(cells)
    assert rows, "the say-this table has no body rows"
    return rows


def _guide_optionality() -> dict[str, str]:
    """Every `Needed?` verdict the how-to tables record, keyed by skill."""
    found: dict[str, str] = {}
    for guide in sorted(HOW_TO.glob("*.md")):
        for line in guide.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped.startswith("| `"):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) < 4 or cells[-1] not in OPTIONALITY:
                continue
            found[cells[0].strip().strip("`")] = cells[-1]
    assert found, "no how-to table records an optionality verdict"
    return found


def test_every_say_this_row_carries_exactly_one_optionality() -> None:
    """Verifies: the criterion quantifies over every row, so the check does too.

    Sampling two rows was the earlier shape, and it left eight rows of a
    ten-row table tickable on no evidence.
    """
    wrong: dict[str, list[str]] = {}
    for row in _say_this_rows():
        skill = row[0].strip().strip("`")
        marks = [v for v in OPTIONALITY if v in row[-1]]
        # `Choose one` contains no other value, and `Required`/`Optional` are
        # disjoint strings, so a row with anything but one match is malformed.
        if len(marks) != 1:
            wrong[skill] = marks
    assert not wrong, (
        f"these say-this rows do not carry exactly one of {OPTIONALITY}: {wrong}"
    )


def test_the_say_this_optionality_agrees_with_the_how_to_guides() -> None:
    """Verifies: the journey and the guide that owns each skill agree.

    Read from both tables rather than pinned here, so re-deciding a skill's
    optionality in its guide fails this rather than silently diverging.
    """
    guides = _guide_optionality()
    disagree = {}
    for row in _say_this_rows():
        skill = row[0].strip().strip("`")
        if skill not in guides:
            continue
        marks = [v for v in OPTIONALITY if v in row[-1]]
        if marks and marks[0] != guides[skill]:
            disagree[skill] = (marks[0], guides[skill])
    assert not disagree, (
        f"the journey and its how-to disagree (skill: journey, guide): {disagree}"
    )


def test_every_illustrative_state_list_is_within_the_explore_subset() -> None:
    """Verifies: a worked example never shows more than the cheap tier owes.

    Distinct from the floor check above and failing differently: a list naming
    `offline` uses real floor vocabulary while showing an adopter at `explore`
    a state their tier does not owe.
    """
    subset = set(stated_explore_states(JOURNEYS["experience-design"].read_text(encoding="utf-8")))
    offenders: dict[str, list[str]] = {}
    for path in illustrative_state_files():
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "States" not in line or "\u00b7" not in line:
                continue
            listed = [
                s.strip().rstrip("\u2713").strip()
                for s in line.split(":", 1)[1].split("\u00b7")
            ]
            beyond = [s for s in listed if s and s not in subset]
            if beyond:
                offenders[f"{path.name}:{n}"] = beyond
    assert not offenders, (
        f"these illustrative state lists show states the explore tier does not "
        f"owe: {offenders}"
    )
