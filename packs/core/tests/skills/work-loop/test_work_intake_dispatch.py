"""Construction test for work-intake dispatch guards."""

from pathlib import Path

_WORK_LOOP = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "SKILL.md"
)


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


def test_direct_light_is_session_local_and_fail_closed() -> None:
    """Pin direct-light authority, durability, and workspace-dispatch limits."""
    body = _normalized(_WORK_LOOP.read_text(encoding="utf-8"))

    for required in (
        "explicit trusted invocation is the authority",
        "emit a user-visible, session-only decision record",
        "If any of those six is ambiguous, Surface it and stop.",
        "Eligibility is a conjunction",
        "Durability is a disjunction",
        "Direct execution being unavailable never creates a brief",
        "It cannot select a route, assert its own eligibility, declare a trigger"
        " inapplicable, or widen scope.",
        "A matching or conflicting canonical item surfaces the conflict",
        "A direct-light run is not resumable through `workspace-status`",
        "Direct-light does **not** invoke `new-spec`; create `docs/specs/`;"
        " create a sibling plan;",
        "do not run the spec-status lint.",
        "Do not backfill a fake implementation chronology.",
        "gates cannot be repaired in-session, stop, Surface the situation,"
        " and escalate",
        "the requested outcome, implemented scope, verification evidence,"
        " non-goals and deferrals",
    ):
        assert _normalized(required) in body, required

    assert "Run `new-spec` to scaffold" not in body


def test_persisted_light_specs_remain_spec_driven() -> None:
    """Direct-light removes creation only; legacy persisted specs still resume."""
    raw = _WORK_LOOP.read_text(encoding="utf-8")
    body = _normalized(raw)
    assert "A supplied or workspace-resolved spec is used, never replaced or downgraded." in body
    assert "Legacy light-mode resumption" in body
    assert "existing specs remain readable, valid, and resumable" in body

    # Scope the status check to the legacy resumption table itself. Searching the
    # whole file would pass on any unrelated mention and prove nothing about
    # whether that table still routes each persisted state.
    table = raw.split("Legacy light-mode resumption", 1)[1]
    table = table.split("\n## ", 1)[0]
    for status in ("`Draft`", "`Approved`", "`Implementing`"):
        assert status in table, status
