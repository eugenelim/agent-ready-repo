"""The upstream-gap rule: when frontend work must hold and route an axis.

Every assertion reads the shipped rule tables rather than restating them, so
changing a rule moves `references/visual-observation.md` and not this file.
"""

from __future__ import annotations

import json

from frontend_engineering_visual_authority_rules import (
    FALLBACK_TOKENS,
    OBSERVATION,
    SKILL,
    WHOLE_EXPORT_TREE,
    observation_table,
    preflight,
    read,
    rule,
    section,
    shipped_files,
)

DESIGN_HANDOFF = OBSERVATION.parent / "design-handoff.md"
EVALS = SKILL.parent / "evals" / "evals.json"


def test_the_upstream_gap_table_states_its_rules() -> None:
    assert rule("Upstream gaps", "gap-demotes") == "never"
    assert rule("Upstream gaps", "gap-outcome") == (
        "hold the axis, stop that part of the implementation, and route it "
        "to the owner the artifact records"
    )
    assert rule("Upstream gaps", "gap-record") == "required"


def test_the_gap_names_both_of_its_sources() -> None:
    sources = rule("Upstream gaps", "gap-sources").lower()

    assert "direction/<slug>.md" in sources
    assert "tokens/<slug>.md" in sources
    assert "named skip" in sources
    assert "no incumbent system supplies the axis" in sources
    assert "conforming tokens/<slug>.md" in sources
    assert "domain unresolved" in sources
    assert "absence of a file" not in sources


def test_the_gap_holds_only_the_axes_it_names() -> None:
    scope = rule("Upstream gaps", "gap-scope").lower()

    assert "only" in scope
    assert "axes the gap names" in scope
    assert "every other axis resolves normally" in scope


def test_a_lower_rung_fills_only_a_genuinely_open_axis() -> None:
    rule_text = rule("Upstream gaps", "lower-rung-may-fill").lower()

    assert "every higher rung left it open" in rule_text
    assert "accepted owner" in rule_text


def test_the_terminal_rung_requires_no_upstream_gap() -> None:
    requires = observation_table("Authority precedence")["local-premise"][2].lower()

    assert "no-higher-rung-resolved" in requires
    assert "no-upstream-gap-held" in requires


def test_the_standalone_table_enumerates_its_three_conditions() -> None:
    admits = [part.strip() for part in rule("Standalone work", "admits").split(",")]

    assert admits == [
        "no-applicable-design-artifact",
        "no-incumbent-system",
        "no-upstream-authority-to-complete",
    ]
    assert rule("Standalone work", "record") == "required"


def test_the_standalone_table_requires_a_completed_read() -> None:
    assert rule("Standalone work", "requires") == "handoff-read-completed"


def test_the_gap_target_handling_states_its_display_rule() -> None:
    handling = rule("Upstream gaps", "gap-target-handling").lower()

    assert "owner or operation" in handling
    assert "display string" in handling
    for prohibited in (
        "loaded",
        "invoked",
        "executed",
        "resolved as a path",
        "opened",
        "used to locate another file",
        "matched against any skill, tool, command, or agent name",
    ):
        assert prohibited in handling


def test_a_refusal_never_becomes_a_gap() -> None:
    assert rule("Upstream gaps", "refusal-becomes-a-gap") == "never"


def test_the_gap_record_persists_no_person_identifying_value() -> None:
    record = rule("Upstream gaps", "gap-record-contents").lower()

    assert "persists only the axes held and one fixed operation kind" in record
    assert "taxonomy-supply-required" in record
    assert "domain-completion-required" in record
    assert "literal operation text" in record
    assert "never written" in record
    assert "person-identifying" in record
    assert "who resolves it" in record
    assert "surfaced live" in record
    assert "never written into a committed artifact" in record


def test_the_reference_names_no_upstream_producer() -> None:
    text = read(OBSERVATION)

    assert "experience-design" not in text
    assert "creative-direction" not in text
    assert "design-system" not in text


def test_the_preflight_states_the_gap_and_routes_to_the_reference() -> None:
    window = preflight().lower()

    assert "upstream gap" in window
    assert "hold" in window
    assert "route" in window
    assert OBSERVATION.name in window


def test_no_shipped_file_says_the_terminal_rung_is_always_available() -> None:
    hits = [
        str(path) for path in shipped_files(WHOLE_EXPORT_TREE)
        if "always available" in read(path).lower()
    ]

    assert not hits


def test_the_terminal_rung_is_standalone_only_in_the_entrypoint() -> None:
    paragraph = preflight().split("**`local-premise`**", 1)[1].split("\n\n", 1)[0].lower()

    assert "terminal" in paragraph
    assert "standalone" in paragraph
    for phrase in (
        "subject matter",
        "category alone",
        "reaction against it",
        "never a product",
    ):
        assert phrase in paragraph


def test_the_fallback_condition_carries_three_conjuncts() -> None:
    step = section(read(SKILL), "### 2. Resolve token values", "\n### ").lower()
    fallback = read(FALLBACK_TOKENS).lower()

    for text in (step, fallback):
        assert "no token taxonomy resolved" in text
        assert "no incumbent token system" in text
        assert "no upstream gap" in text

    assert "incumbent visual system" not in step
    assert "incumbent visual system" not in fallback


def test_unresolved_taxonomy_domains_stay_upstream_gaps() -> None:
    step = " ".join(
        section(read(SKILL), "### 2. Resolve token values", "\n### ").lower().split()
    )

    assert "explicitly unresolved taxonomy domain is an upstream gap" in step
    assert "resolved values remain as given" in step
    assert "relationships can still be resolved" in step
    for prohibited_source in (
        "incumbent habit",
        "platform habit",
        "fallback",
        "local premise",
        "category habit",
    ):
        assert prohibited_source in step
    assert "must not fill that domain" in step


def test_the_handoff_reference_hands_the_gap_forward() -> None:
    handoff = read(DESIGN_HANDOFF).lower()

    assert "direction/<slug>.md" in handoff
    assert "tokens/<slug>.md" in handoff
    assert "named skip" in handoff
    assert "upstream gap" in handoff
    assert "not permission" in handoff
    assert "lower rung" in handoff


def test_the_upstream_gap_evals_exist_and_route() -> None:
    payload = json.loads(read(EVALS))
    cases = {case["id"]: case for case in payload["evals"]}

    missing_taxonomy = cases["visual-authority-upstream-gap-missing-taxonomy"]
    missing_output = missing_taxonomy["expected_output"].lower()
    assert "upstream gap" in missing_output
    assert "tokens/<slug>.md" in missing_output
    assert "named skip" in missing_output
    assert "route" in missing_output
    assert "upstream" in missing_output
    assert "fallback block" in missing_output
    assert "does not take" in missing_output
    assert "local premise" in missing_output
    assert "does not state" in missing_output

    unresolved_domain = cases["visual-authority-unresolved-domain"]
    unresolved_output = unresolved_domain["expected_output"].lower()
    assert "needed domain unresolved" in unresolved_output
    assert "owner the artifact records" in unresolved_output
    assert "resolves no value" in unresolved_output
    assert "display-only data" in unresolved_output

    standalone = cases["visual-authority-standalone"]["expected_output"].lower()
    for condition in (
        "no-applicable-design-artifact",
        "no-incumbent-system",
        "no-upstream-authority-to-complete",
    ):
        assert condition in standalone
