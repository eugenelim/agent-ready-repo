"""Contract tests for upstream shaping finding-response guidance."""

import re
from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parents[2]
INTAKE_INTENT = CORE / ".apm" / "skills" / "intake-intent" / "SKILL.md"
AUTHOR_BRIEF = CORE / ".apm" / "skills" / "author-delivery-brief" / "SKILL.md"
NEW_SPEC = CORE / ".apm" / "skills" / "new-spec" / "SKILL.md"
SHAPING_REVIEWER = CORE / ".apm" / "agents" / "shaping-reviewer.md"

NEW_SECTIONS = {
    "intent": (INTAKE_INTENT, "## What a finding against an intent can move"),
    "brief": (AUTHOR_BRIEF, "## What a finding against a brief can move"),
    "spec": (NEW_SPEC, "## Answering a shaping-review finding"),
    "reviewer": (SHAPING_REVIEWER, "## A settled decision is not a finding"),
}

ANSWER_TOKENS = (
    "drop-the-claim",
    "cut-the-item",
    "demote-the-claim",
    "narrow-the-claim",
    "route-to-owner",
    "bound-out-of-scope",
    "repair-the-generator",
    "repair-the-artifact",
    "dismiss-and-re-present",
    "accept-as-proportionate",
)

REST_OF_LADDER = (
    "cut-the-item",
    "narrow-the-claim",
    "route-to-owner",
    "bound-out-of-scope",
    "repair-the-generator",
    "repair-the-artifact",
    "dismiss-and-re-present",
    "accept-as-proportionate",
)


def _section(path: Path, heading: str) -> str:
    """Return exactly one Markdown section, refusing anything ambiguous."""
    text = path.read_text(encoding="utf-8")
    level = len(heading) - len(heading.lstrip("#"))
    matches = list(re.finditer(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE))
    assert len(matches) == 1, (
        f"{path}: {heading!r} matched {len(matches)} heading lines"
    )
    opening = matches[0]
    following = re.search(
        rf"^#{{1,{level}}} ", text[opening.end() :], flags=re.MULTILINE
    )
    end = len(text) if following is None else opening.end() + following.start()
    return text[opening.start() : end]


def _prefix_region(path: Path, start_prefix: str, end_prefix: str) -> str:
    """Return one prefix-anchored region while refusing duplicate anchors."""
    text = path.read_text(encoding="utf-8")
    starts = list(
        re.finditer(rf"^{re.escape(start_prefix)}.*$", text, flags=re.MULTILINE)
    )
    ends = list(re.finditer(rf"^{re.escape(end_prefix)}.*$", text, re.MULTILINE))
    assert len(starts) == 1, (
        f"{path}: start {start_prefix!r} matched {len(starts)} lines"
    )
    assert len(ends) == 1, f"{path}: end {end_prefix!r} matched {len(ends)} lines"
    assert starts[0].start() < ends[0].start(), f"{path}: region anchors are reversed"
    return text[starts[0].start() : ends[0].start()]


def _flat(text: str) -> str:
    """Normalize layout-only whitespace for stable prose assertions."""
    return " ".join(text.split())


def _new_section(label: str) -> str:
    """Return one named response section from its owning shaping surface."""
    path, heading = NEW_SECTIONS[label]
    return _section(path, heading)


@pytest.mark.parametrize("label", ("intent", "brief", "spec"))
def test_each_authoring_skill_points_to_work_loop_decide(label: str) -> None:
    """Keep the answer vocabulary in work-loop's DECIDE step alone."""
    section = _flat(_new_section(label))
    pointer = (
        "The answers available to a sustained finding are stated once, in the "
        "`work-loop` skill's DECIDE step."
    )
    assert pointer in section, f"{label}: missing the work-loop DECIDE pointer"


def test_intent_demotion_destinations_and_authority_are_pinned() -> None:
    """Keep intent demotion mapped to its two destinations and owner decision."""
    section = _flat(_new_section("intent"))
    assert (
        "A settled ground for the outcome or the boundary goes to `Opportunity`."
        in section
    ), "intent: settled ground no longer routes to Opportunity"
    assert (
        "A matter the assertion decided without the authority to decide it goes "
        "to `Unresolved questions`." in section
    ), "intent: unauthorized decisions no longer route to Unresolved questions"
    assert (
        "the destination follows what the assertion was doing" in section
    ), "intent: destination decision rule is missing"
    assert (
        "What demotion costs \u2014 the pin it carries and the authority it needs "
        "\u2014 is stated in the DECIDE step and holds here unchanged." in section
    ), "intent: no longer defers demotion's cost to DECIDE"


def test_brief_demotion_destinations_and_fallthrough_are_pinned() -> None:
    """Keep brief demotion out of transient gaps and routed to useful homes."""
    section = _flat(_new_section("brief"))
    assert "goes to `Rabbit holes`" in section, "brief: Rabbit holes route is missing"
    assert (
        "goes to `Design artifacts`" in section
    ), "brief: Design artifacts route is missing"
    assert (
        "`Ready gaps` is not a destination" in section
    ), "brief: Ready gaps became a demotion destination"
    assert (
        "Where neither destination fits, the assertion had no work left to do "
        "and the answer was `drop-the-claim`." in section
    ), "brief: unmatched demotion no longer falls through to drop-the-claim"


def test_spec_template_owns_the_contract_working_material_split() -> None:
    """Keep assets/spec.md as the single owner of the spec tier split."""
    section = _flat(_new_section("spec"))
    assert (
        "the bundled `assets/spec.md`, their single owner" in section
    ), "spec: assets/spec.md is no longer the single owner"
    assert (
        "The template owns that split and nothing else about the move; what the "
        "move costs is stated in the DECIDE step" in section
    ), "spec: the template is named as the owner of what demotion costs"


def test_reviewer_does_not_reopen_settled_decisions_or_hide_defects() -> None:
    """Keep settled choices closed while preserving pre-existing defect review."""
    section = _flat(_new_section("reviewer"))
    assert (
        "do not raise a finding that reopens it" in section
    ), "reviewer: settled decisions may be reopened"
    assert (
        "A pre-existing defect is a different thing and stays in scope however "
        "late it is found." in section
    ), "reviewer: pre-existing defect carve-out is missing"
    assert (
        "an applicable governing obligation the supplied evidence carries" in section
    ), "reviewer: conflict scope is no longer an applicable governing obligation"
    assert (
        "A superseded, rejected, or lower-authority obligation does not qualify."
        in section
    ), "reviewer: superseded obligations may reopen a settled decision"
    assert (
        "A recorded ground never settles a conflict with a non-waivable control."
        in section
    ), "reviewer: a recorded ground can immunise a decision"


def test_upstream_surfaces_do_not_copy_the_rest_of_the_ladder() -> None:
    """Keep every non-upstream answer token out of all four shaping surfaces."""
    for path, _heading in NEW_SECTIONS.values():
        text = path.read_text(encoding="utf-8")
        for token in REST_OF_LADDER:
            assert token not in text, f"{path}: copied ladder token {token!r}"


def test_upstream_tokens_appear_only_inside_the_new_sections() -> None:
    """Keep demote and drop references confined to the new pointer sections."""
    for label, (path, heading) in NEW_SECTIONS.items():
        text = path.read_text(encoding="utf-8")
        section = _section(path, heading)
        outside = text.replace(section, "", 1)
        for token in ("demote-the-claim", "drop-the-claim"):
            assert token not in outside, (
                f"{label}: {token!r} appears outside the new response section"
            )


GATE_REGIONS = {
    "intent shaping-review gate": lambda: _section(
        INTAKE_INTENT, "## Shaping-review gate"
    ),
    "brief shaping-review stage": lambda: _section(
        AUTHOR_BRIEF, "### 2. Run shaping review before the Ready decision"
    ),
    "brief human-confirmation stage": lambda: _section(
        AUTHOR_BRIEF, "### 3. Write back only after human confirmation"
    ),
    "brief DoR gate": lambda: _section(AUTHOR_BRIEF, "## DoR gate"),
    "spec shaping-review step": lambda: _prefix_region(
        NEW_SPEC, "6. Shaping spec review.", "7. Spec-mode adversarial review."
    ),
    "reviewer output contract": lambda: _section(
        SHAPING_REVIEWER, "## Output contract"
    ),
    "reviewer intent mode": lambda: _section(SHAPING_REVIEWER, "### intent mode"),
    "reviewer delivery-brief mode": lambda: _section(
        SHAPING_REVIEWER, "### delivery-brief mode"
    ),
    "reviewer spec mode": lambda: _section(SHAPING_REVIEWER, "### spec mode"),
}


@pytest.mark.parametrize("label", GATE_REGIONS)
def test_gate_regions_cannot_read_advisory_answers(label: str) -> None:
    """Keep response vocabulary and metadata out of every gate-deciding region."""
    region = _flat(GATE_REGIONS[label]()).lower()
    for prohibited in (*ANSWER_TOKENS, "the answer", "the reason"):
        assert prohibited not in region, (
            f"{label}: gate region contains prohibited guidance {prohibited!r}"
        )


GATE_SENTENCES = (
    (
        "intent shaping-review gate",
        "every unresolved token keeps the intent at `Draft` and blocks `Accepted`.",
    ),
    (
        "brief shaping-review stage",
        "every unresolved finding keeps the brief at `Draft` and blocks `Ready`.",
    ),
    ("spec shaping-review step", "Resolve findings until it returns `Clean`."),
)


@pytest.mark.parametrize(("label", "sentence"), GATE_SENTENCES)
def test_gate_sentences_remain_exact(label: str, sentence: str) -> None:
    """Keep each gate sentence inside the region that decides that gate.

    Scoped to the region, not the whole file. A file-wide search stays green
    when the sentence is moved out of the gate and into the advisory guidance
    beside it, which is the one change this guard exists to catch.
    """
    region = _flat(GATE_REGIONS[label]())
    assert sentence in region, f"{label}: gate no longer states {sentence!r}"


@pytest.mark.parametrize("label", NEW_SECTIONS)
def test_new_sections_are_count_neutral(label: str) -> None:
    """Keep the pointer guidance free of a stale adjacent answer count."""
    section = _new_section(label).lower()
    assert "eight answers" not in section, f"{label}: contains 'eight answers'"
    assert "ten answers" not in section, f"{label}: contains 'ten answers'"
    assert not re.search(r"one of the \w+ answers", section), (
        f"{label}: contains a counted answer-set construction"
    )
    for counted in ("both destinations", "the two destinations", "two destinations"):
        assert counted not in section, (
            f"{label}: counts the destinations it enumerates ({counted!r})"
        )
    assert not re.search(
        r"\ball (?:\w+|\d+) (?:answers|responses|destinations)\b", section
    ), f"{label}: contains a counted set beside its enumeration"


@pytest.mark.parametrize("label", NEW_SECTIONS)
def test_new_sections_do_not_cite_internal_records(label: str) -> None:
    """Keep shipped pointer guidance free of repository-internal record citations."""
    section = _new_section(label)
    for internal_path in ("docs/specs/", "docs/product/"):
        assert internal_path not in section, (
            f"{label}: cites internal record path {internal_path!r}"
        )
    match = re.search(
        r"\bAC-[A-Za-z0-9][A-Za-z0-9_-]*(?:\([a-z]\))?",
        section,
        flags=re.IGNORECASE,
    )
    assert match is None, f"{label}: cites internal AC identifier {match.group(0)!r}"


@pytest.mark.parametrize("label", ("intent", "brief"))
def test_upstream_sections_do_not_redefine_what_demotion_costs(label: str) -> None:
    """Keep DECIDE the sole definition of what `demote-the-claim` costs.

    A local surface that points at DECIDE must not redefine one of its answers
    in passing. DECIDE moves the obligation *with* a content pin and records the
    pin that catches its removal; guidance asserting no pin is needed describes
    a different answer under the same name.
    """
    section = _flat(_new_section(label))
    lowered = section.lower()
    for contradiction in (
        "no new pin",
        "needs no pin",
        "no pin is required",
        "pin is not required",
        "requires no pin",
        "without a pin",
    ):
        assert contradiction not in lowered, (
            f"{label}: redefines demotion's cost with {contradiction!r}"
        )
    assert "is stated in the DECIDE step and holds here unchanged." in section, (
        f"{label}: no longer defers demotion's cost to DECIDE"
    )


DISCLAIMER = (
    "They are not the contract and working-material tiers a spec carries, and "
    "nothing reads them to grade a finding"
)

SPEC_OWN_SPLIT = (
    "Which parts of a spec are contract and which are working material is stated "
    "by the bundled `assets/spec.md`, their single owner."
)


@pytest.mark.parametrize("label", ("intent", "brief"))
def test_upstream_sections_never_classify_with_the_spec_tiers(label: str) -> None:
    """Keep the spec's operative tier vocabulary out of these sections entirely.

    `working material` is operative elsewhere in this pack: a finding whose every
    cited surface is working material sustains at advisory severity at most. Any
    use here that classifies one of this artifact's own sections can therefore
    grade down a finding that blocks `Accepted` or `Ready`.

    Checks every occurrence in the section, not a list of spellings: the only
    admitted use is the disclaimer that explicitly denies the tiers apply. A bold
    label, a plain-text "moves it into working material", and any future phrasing
    all fail alike.
    """
    section = _flat(_new_section(label))
    assert DISCLAIMER in section, f"{label}: lost the sentence disclaiming the tiers"
    remainder = section.replace(DISCLAIMER, "", 1)
    for tier_term in ("working material", "working-material"):
        assert tier_term not in remainder, (
            f"{label}: classifies a section with the spec tier term "
            f"{tier_term!r} outside the disclaimer"
        )
    assert "**Deciding sections**" in section, f"{label}: lost its deciding-sections label"
    assert "**Recording sections**" in section, (
        f"{label}: lost its recording-sections label"
    )


def test_spec_section_uses_the_tiers_only_for_the_spec_split() -> None:
    """Allow the spec's own tiers, which are real, and nothing beyond them.

    Unlike the intent and brief, a spec genuinely has contract and working
    material, and `assets/spec.md` owns that split. The one admitted sentence is
    the one naming that owner.
    """
    section = _flat(_new_section("spec"))
    assert SPEC_OWN_SPLIT in section, "spec: lost the sentence naming the split's owner"
    remainder = section.replace(SPEC_OWN_SPLIT, "", 1)
    for tier_term in ("working material", "working-material"):
        assert tier_term not in remainder, (
            f"spec: uses {tier_term!r} beyond the sentence naming its owner"
        )
