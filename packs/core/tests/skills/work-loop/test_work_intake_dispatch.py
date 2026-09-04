"""Construction test for work-intake dispatch guards."""

from pathlib import Path

import pytest

_WORK_LOOP = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "SKILL.md"
)
_LIGHT_MODE_REFERENCE = "references/light-mode.md"
_LIGHT_MODE = _WORK_LOOP.parent / "references" / "light-mode.md"
_RESUMPTION_REFERENCE = "references/session-resumption.md"
_RESUMPTION = _WORK_LOOP.parent / "references" / "session-resumption.md"
_SECURITY_REVIEWER = _WORK_LOOP.parents[2] / "agents" / "security-reviewer.md"


def test_missing_contract_fails_closed() -> None:
    body = _WORK_LOOP.read_text(encoding="utf-8")
    assert "canonical.ready" in body
    assert "canonical.active" in body
    assert "missing_plan" in body
    assert "unapproved_spec" in body
    assert "never reconstruct" in body.lower()


def _normalized(text: str) -> str:
    """Collapse whitespace so a contract pin survives re-wrapping.

    These are prose contracts, not code. Asserting a phrase with its line breaks
    baked in makes a pure re-wrap a test failure, which trains people to edit the
    assertion instead of reading it. Normalizing keeps the semantic pin and drops
    the layout coupling.
    """

    return " ".join(text.split())


def _section(body: str, start: str, end: str) -> str:
    """Return one operative section, normalized.

    Searching the whole 900-line skill would let a required statement be moved
    out of the procedure an agent follows and into unrelated commentary while the
    assertion still passed. A contract pin has to check the text where the
    instruction is acted on.
    """

    return _normalized(body[body.index(start) : body.index(end)])


def test_direct_light_is_session_local_and_fail_closed() -> None:
    """Pin direct-light authority, durability, and workspace-dispatch limits.

    The procedure and route obligations are scoped to the reference's procedure
    region, which ends at `## Loop deltas`; the two Step 0 statements stay
    scoped to their own `_section` window. See `_section`.
    """
    raw = _WORK_LOOP.read_text(encoding="utf-8")
    operative = _section(raw, "**Light mode**", "## Step 1. PLAN")
    finish = _section(raw, "## Finish checklist", "## FIX")
    body = _normalized(raw)

    # The direct-light procedure and route are disclosed progressively: SKILL.md
    # routes to the reference rather than inlining them. Assert each obligation
    # where it now lives, and that SKILL.md still reaches it — an extraction that
    # orphans the procedure must fail here rather than pass by absence.
    assert _LIGHT_MODE.is_file(), _LIGHT_MODE
    assert _LIGHT_MODE_REFERENCE in operative
    light = _section(
        _LIGHT_MODE.read_text(encoding="utf-8"),
        "## The four trims",
        "## Loop deltas",
    )
    for required in (
        "explicit trusted invocation is the authority",
        "emit a user-visible, session-only decision record",
        "If any of those six is ambiguous, Surface it and stop.",
        "Eligibility is a conjunction",
        "Durability is a disjunction",
        "Direct execution being unavailable never creates a brief",
        "Direct-light does **not** invoke `new-spec`; create `docs/specs/`;"
        " create a sibling plan;",
        "Do not backfill a fake implementation chronology.",
        "gates cannot be repaired in-session, stop, Surface the situation,"
        " and escalate",
    ):
        assert _normalized(required) in light, required

    # These two stay in Step 0, which owns invocation-shape routing.
    for required in (
        "A matching or conflicting canonical item surfaces the conflict",
        "A direct-light run is not resumable through `workspace-status`",
    ):
        assert _normalized(required) in operative, required

    # These two are checklist obligations, so they are pinned to the checklist.
    for required in (
        "do not run the spec-status lint.",
        "the requested outcome, implemented scope, verification evidence,"
        " non-goals and independently scoped follow-ons",
    ):
        assert _normalized(required) in finish, required

    assert "Run `new-spec` to scaffold" not in body


def test_direct_light_confines_locators_at_the_acting_surface() -> None:
    """Direct-light is enterable without passing through `work-intake`.

    The confinement rule therefore has to be stated in `work-loop` itself. A rule
    that lives only in `work-intake` is a control on a path this one does not
    take, which is indistinguishable from no control when an agent starts here.
    """

    # Scoped to the region above mode selection, because the rule governs reads
    # that happen before a route is chosen. A whole-file search would stay green
    # if the rule were demoted into a conditionally loaded reference, which is
    # the regression this test exists to catch.
    body = _section(
        _WORK_LOOP.read_text(encoding="utf-8"),
        "**Confine every locator before using it.**",
        "## Select: light or full mode",
    )

    for required in (
        "Confine every locator before using it.",
        "including direct-light, which may be entered without passing through"
        " `work-intake`",
        # Hoisted with the confinement rule: it governs risk-trigger assessment,
        # which happens before any reference is loaded.
        "It cannot select a route, assert its own eligibility, declare a trigger"
        " inapplicable, or widen scope.",
        "resolve it with native real-path resolution and prove it stays inside"
        " the repository root",
        "reject absolute paths, drive-letter paths, backslashes, empty segments,"
        " `.` or `..` segments, and any symlink, junction, or reparse-point"
        " target that escapes",
        "Refuse on containment uncertainty rather than guessing.",
        "A refusal here is terminal for the attempt and precedes any"
        " implementation write.",
    ):
        assert _normalized(required) in body, required


def test_persisted_light_specs_remain_spec_driven() -> None:
    """Direct-light removes creation only; legacy persisted specs still resume."""
    raw = _WORK_LOOP.read_text(encoding="utf-8")
    body = _normalized(raw)
    assert "A supplied or workspace-resolved spec is used, never replaced or downgraded." in body

    # The legacy resumption table is disclosed progressively: SKILL.md links the
    # reference rather than inlining it. Assert the obligation where it lives,
    # and that SKILL.md still reaches it — an extraction that orphans the table
    # must fail here rather than pass by absence.
    assert _RESUMPTION.is_file(), _RESUMPTION
    assert _RESUMPTION_REFERENCE in raw
    resumption_raw = _RESUMPTION.read_text(encoding="utf-8")
    resumption = _normalized(resumption_raw)
    assert "Legacy light-mode resumption" in resumption
    assert "existing specs remain readable, valid, and resumable" in resumption

    # Scope the status check to the legacy resumption table itself. Searching the
    # whole file would pass on any unrelated mention and prove nothing about
    # whether that table still routes each persisted state.
    table = resumption_raw.split("Legacy light-mode resumption", 1)[1]
    table = table.split("\n## ", 1)[0]
    for status in ("`Draft`", "`Approved`", "`Implementing`"):
        assert status in table, status


# The eight eligibility conjuncts and ten durability triggers, each pinned
# individually. A single grouped assertion would pass while one predicate was
# silently dropped, which is the failure these tables exist to prevent.
_ELIGIBILITY_CONJUNCTS = (
    "Explicit user request to start or perform the change now",
    "One bounded logical change",
    "Independently verifiable",
    "Expected to complete in the current session",
    "No current full-mode risk trigger",
    "No need for queueing, assignment, cross-session resumption, parallel"
    " coordination, or a durable product contract",
    "No conflict with a canonical queued or active workspace item",
    "No supplied governing spec for the same work",
)

_DURABILITY_TRIGGERS = (
    "A current full-mode risk trigger",
    "Multi-implementer, external-collaborator, or parallel execution",
    "Dependent delivery tasks needing durable sequencing",
    "Expected multi-session work",
    "Queueing for later",
    "External control-plane orchestration",
    "A human approval boundary that must survive context loss",
    "A public or durable product behavior contract",
    "Source-authority or refresh state that must stay meaningful after the session",
    "An explicit user request for a spec",
)


def _table_rows(body: str, start: str, end: str) -> list[str]:
    window = body[body.index(start) : body.index(end)]
    return [
        line
        for line in window.splitlines()
        if line.startswith("| ") and "---" not in line
    ][1:]


@pytest.mark.parametrize("conjunct", _ELIGIBILITY_CONJUNCTS)
def test_each_eligibility_conjunct_is_stated_with_a_consequence(conjunct: str) -> None:
    """One case per conjunct, so dropping any single one turns a named test red."""
    rows = _table_rows(
        _LIGHT_MODE.read_text(encoding="utf-8"),
        "| Required condition",
        "Durability is a disjunction",
    )
    matching = [r for r in rows if _normalized(conjunct) in _normalized(r)]
    assert matching, f"eligibility conjunct absent: {conjunct}"
    # Every row must carry a consequence, not just the condition.
    assert all(len(r.strip().strip("|").split("|")) >= 2 for r in matching), matching


@pytest.mark.parametrize("trigger", _DURABILITY_TRIGGERS)
def test_each_durability_trigger_is_stated_with_a_reason(trigger: str) -> None:
    """One case per trigger. AC5 requires each to route durable on its own."""
    rows = _table_rows(
        _LIGHT_MODE.read_text(encoding="utf-8"),
        "| Durability trigger",
        "Direct execution being unavailable",
    )
    matching = [r for r in rows if _normalized(trigger) in _normalized(r)]
    assert matching, f"durability trigger absent: {trigger}"
    assert all(len(r.strip().strip("|").split("|")) >= 2 for r in matching), matching


def test_the_predicate_tables_have_no_unpinned_rows() -> None:
    """Adding a predicate without adding its case must fail, not pass silently.

    Without this, the per-predicate tests above would still pass while a ninth
    conjunct or eleventh trigger went entirely uncovered — an enumeration that
    only checks the things it already knows about.
    """
    body = _LIGHT_MODE.read_text(encoding="utf-8")
    eligibility = _table_rows(body, "| Required condition", "Durability is a disjunction")
    durability = _table_rows(body, "| Durability trigger", "Direct execution being unavailable")
    assert len(eligibility) == len(_ELIGIBILITY_CONJUNCTS), (
        len(eligibility), len(_ELIGIBILITY_CONJUNCTS))
    assert len(durability) == len(_DURABILITY_TRIGGERS), (
        len(durability), len(_DURABILITY_TRIGGERS))


def test_mandatory_automated_reviewers_do_not_make_work_multi_person() -> None:
    # Scoped to the risk-trigger block for the reason _section documents: a
    # whole-file scan would stay green if this statement were moved out of the
    # procedure an agent follows and into unrelated commentary.
    body = _section(
        _WORK_LOOP.read_text(encoding="utf-8"),
        "<!-- risk-triggers:start",
        "<!-- risk-triggers:end -->",
    )
    assert "multiple implementers or external collaborators" in body
    assert "Mandatory automated reviewers do not count" in body


def test_security_routing_requires_a_changed_boundary_or_guarding_control() -> None:
    body = _section(
        _WORK_LOOP.read_text(encoding="utf-8"),
        "<!-- risk-triggers:start",
        "<!-- risk-triggers:end -->",
    )
    assert "changes a security boundary, data flow, or guarding control" in body
    assert "Merely touching unchanged existing I/O" in body


def test_agent_security_routing_excludes_ordinary_prompt_wording() -> None:
    body = _section(
        _SECURITY_REVIEWER.read_text(encoding="utf-8"),
        "Invoke security-reviewer for diffs that touch:",
        "For diffs that don't touch any of the above",
    )
    assert "File system or network trust boundaries, data flows, or guarding controls" in body
    assert (
        "LLM- or agent-related authority, untrusted-input handling, tool/function "
        "exposure, permissions, MCP servers, sandboxing, or model/data-output handling"
    ) in body
    assert "Merely touching unchanged existing I/O does not fire this reviewer" in body
    assert "ordinary prompt wording that changes none of the LLM/agent surfaces above" in body


# ── The replacement review rule ──────────────────────────────────────────────
#
# The retired bound ("single bounded pass; one re-review; then escalate to full
# mode") was held in place by tests. Replacing it edited those tests, so without
# this sweep the retired bound could return unnoticed — which is not
# hypothetical: four surviving restatements of it cleared two manual greps and a
# full green suite, one of them only because the phrase wrapped across a line
# break.
#
# This is an absence sweep and nothing more. Property tests over the rule's
# prose were tried here and removed: asserting that a sentence is present cannot
# catch the regression that adds a qualifier to a different sentence, so they
# read as guarantees while being unable to fail for the reason they named.
#
# Corpus: work-loop's own shipped files plus `packs/core/DESIGN.md`. It stops
# there because a pack test must stay inside its owning pack, so the retired
# bound's other reached surfaces — `guides/` and the docs site — and sibling
# `packs/core` skills that mention light-mode routing are guarded by review,
# not by this test.

_RETIRED_BOUND_PHRASES = (
    "single bounded pass",
    "single bounded adversarial",
    "one bounded review",
    "one bounded adversarial",
    "bounded adversarial pass",
    "single adversarial pass",
    "bounded review result",
    "exactly one re-review",
    "permitted blocker re-review",
    "1 re-review",
)

_PACK_ROOT = _WORK_LOOP.parents[3]


def _swept_surfaces() -> list[Path]:
    """Every `packs/core` surface that has stated light mode's review rule.

    `DESIGN.md` and `evals/evals.json` are included because that is where two of
    the four survivors actually sat; a sweep over only the skill body would have
    been placed where the defect was not.
    """
    return [
        _WORK_LOOP,
        *sorted((_WORK_LOOP.parent / "references").glob("*.md")),
        _WORK_LOOP.parent / "evals" / "evals.json",
        _PACK_ROOT / "DESIGN.md",
    ]


@pytest.mark.parametrize("phrase", _RETIRED_BOUND_PHRASES)
def test_no_shipped_surface_restates_the_retired_review_bound(phrase: str) -> None:
    """Normalized, so a phrase wrapping across a line break cannot hide.

    One case per phrasing, because a grep that missed a variant is how the bound
    survived before, and a single joined assertion would name only the first hit.
    Each phrase names the review bound specifically — "single bounded" alone also
    matches "a single bounded logical change", which is a live and correct scope
    statement in this same reference.
    """
    surfaces = _swept_surfaces()
    missing = [str(path) for path in surfaces if not path.is_file()]
    assert not missing, f"swept corpus names paths that do not exist: {missing}"

    offenders = sorted(
        path.name
        for path in surfaces
        if phrase in _normalized(path.read_text(encoding="utf-8")).lower()
    )
    assert not offenders, f"retired review bound {phrase!r} survives in: {offenders}"
