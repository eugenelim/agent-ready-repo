"""The `work-loop-next-projection` contract's tables are self-consistent and match the engine.

Four pre-EXECUTE review rounds on this spec sustained 78 findings, and roughly two
thirds of them were one class: a table changed and a reference to it did not. Row
numbers shifted under mutation proofs that then named a row carrying no
discriminator; a repaired criterion landed in `spec.md` and not in `plan.md`; a
count was restated in five places and four went stale. Every one of those is
mechanically decidable, and every one was found by a human-equivalent reading
instead. This module is that reading, executed.

It checks the contract documents against each other and against the live engine.
It does **not** check an emitter — `loop-engine next` does not exist yet, and the
conformance half of T4 lands with it. Scope here is drift, which is what the
review rounds actually kept finding.

It lives in `tests/roster/` rather than beside the work-loop pack suite because a
pack test may not read above its own pack, and the contract sits under `docs/`.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/specs/work-loop-next-projection/spec.md"
PLAN = ROOT / "docs/specs/work-loop-next-projection/plan.md"
ENGINE = ROOT / "packs/core/.apm/skills/work-loop/scripts/loop-engine.py"

pytestmark = pytest.mark.skipif(
    not SPEC.is_file(), reason="work-loop-next-projection contract not present"
)


def _load_engine():
    """Import the shipped engine for its transition tables, without spawning it."""
    spec = importlib.util.spec_from_file_location("_wlnp_engine", ENGINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rows(text: str, pattern: str) -> list[list[str]]:
    """Return Markdown table rows matching `pattern`, split into stripped cells."""
    out = []
    for line in text.splitlines():
        if re.match(pattern, line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            out.append(cells)
    return out


def _ticks(cell: str) -> set[str]:
    """Every backticked token in a table cell."""
    return set(re.findall(r"`([^`]+)`", cell))


# ── the four tables, parsed from the spec ──────────────────────────────────


def routing_rows() -> list[dict]:
    rows = []
    for cells in _rows(SPEC.read_text(), r"^\| R\d+ \|"):
        row_id, mode, state, last_event, disc, action = cells[:6]
        rows.append(
            {
                "id": row_id,
                "modes": {"code", "spec-plan"} if mode == "both" else {mode},
                "state": _ticks(state).pop() if _ticks(state) else state,
                # `*` means "any base key reaching this state". The literal
                # token `null` is the JSON null `engine-state.json` carries
                # before a run's first transition, so it maps to Python None.
                "events": (
                    None
                    if last_event.strip() == "`*`"
                    else {None if t == "null" else t for t in _ticks(last_event)}
                ),
                "disc": _ticks(disc),
                "action": _ticks(action).pop(),
            }
        )
    return rows


def action_rows() -> dict[str, dict]:
    out = {}
    for cells in _rows(SPEC.read_text(), r"^\| `[a-z.\-]+` \| `(agent|command|wait|done|stop)` \|"):
        action, kind, params, load, human_wait = cells[:5]
        out[_ticks(action).pop()] = {
            "kind": _ticks(kind).pop(),
            "params": set() if params == "—" else _ticks(params),
            "load": set() if load == "—" else _ticks(load),
            "human_wait": human_wait.strip() == "true",
        }
    return out


def precondition_ids() -> list[str]:
    return [cells[0] for cells in _rows(SPEC.read_text(), r"^\| P\d+ \|")]


DISCRIMINATORS = {
    "SPEC-HUMAN-GATE": ["Draft", "Approved", "other"],
    "PLAN-HUMAN-GATE": ["Drafting", "Approved", "other"],
    "SPEC-PLAN-APPROVED": [
        "pending+unscheduled", "pending+scheduled",
        "approved+unscheduled", "approved+scheduled", "malformed",
    ],
    "REVIEW": ["within-budget", "cap-reached", "stasis", "malformed"],
    "FINDINGS-REMAIN": ["matches", "does-not-match"],
}


def _discriminator_for(state: str, event: str | None) -> list[str | None]:
    if state in ("SPEC-PLAN-REVIEW", "CODE-REVIEW"):
        return DISCRIMINATORS["REVIEW"]
    if state == "CODE-IMPLEMENTATION" and event == "findings-remain":
        return DISCRIMINATORS["FINDINGS-REMAIN"]
    return DISCRIMINATORS.get(state, [None])


def domain() -> list[tuple]:
    """Every (mode, state, last_event, discriminator) the verb can be asked."""
    engine = _load_engine()
    members = []
    for mode, table in engine._TRANSITIONS_BY_MODE.items():
        keys = {(event, target) for (_src, event), target in table.items()}
        keys.add((None, "SPEC-PLAN-DRAFTING"))
        keys.add(
            ("plan-approved", "CODE-IMPLEMENTATION") if mode == "code"
            else ("plan-approved", "DONE")
        )
        for event, state in keys:
            for value in _discriminator_for(state, event):
                members.append((mode, state, event, value))
    return members


def _matches(row: dict, member: tuple) -> bool:
    mode, state, event, value = member
    if mode not in row["modes"] or state != row["state"]:
        return False
    if row["events"] is not None and event not in row["events"]:
        return False
    if row["disc"]:
        return value in row["disc"]
    return True


# ── the properties the criteria assert ─────────────────────────────────────


def test_the_tables_parse_at_all() -> None:
    assert len(routing_rows()) >= 20, "Routing table did not parse"
    assert len(action_rows()) >= 15, "Action attributes table did not parse"
    assert len(precondition_ids()) >= 5, "Preconditions table did not parse"


def test_ac1_totality_every_domain_member_matches_a_row() -> None:
    rows = routing_rows()
    uncovered = [m for m in domain() if not any(_matches(r, m) for r in rows)]
    assert not uncovered, f"{len(uncovered)} domain members match no Routing row: {uncovered[:5]}"


def test_ac2_determinism_no_member_matches_two_rows() -> None:
    rows = routing_rows()
    ambiguous = [
        (m, [r["id"] for r in rows if _matches(r, m)])
        for m in domain()
        if sum(_matches(r, m) for r in rows) > 1
    ]
    assert not ambiguous, f"ambiguous members: {ambiguous[:5]}"


def test_ac1_mutation_deleting_any_row_leaves_a_member_uncovered() -> None:
    """The property the Discriminators table exists to buy.

    Rounds 1-2 shipped a version where only the discriminator-free rows reddened,
    because the domain was crossed with values read out of the Routing table
    itself. Deleting such a row deleted the member that would have exposed it.
    """
    rows = routing_rows()
    members = domain()
    survivors = [
        row["id"]
        for row in rows
        if all(
            any(_matches(o, m) for o in rows if o["id"] != row["id"])
            for m in members
        )
    ]
    assert not survivors, (
        "deleting these rows leaves the domain fully covered, so AC1's mutation "
        f"cannot fail for them: {survivors}"
    )


def test_ac4_closure_between_the_two_tables() -> None:
    routed = {r["action"] for r in routing_rows()}
    declared = set(action_rows())
    assert routed == declared, (
        f"routed-but-undeclared={sorted(routed - declared)} "
        f"declared-but-unrouted={sorted(declared - routed)}"
    )


def test_human_wait_is_exactly_the_wait_kinds() -> None:
    for action, attrs in action_rows().items():
        assert attrs["human_wait"] == (attrs["kind"] == "wait"), (
            f"{action}: human_wait={attrs['human_wait']} but kind={attrs['kind']}"
        )


def test_the_stated_domain_size_matches_the_computed_one() -> None:
    """The spec calls itself the sole home of this figure. Hold it to that."""
    text = SPEC.read_text()
    match = re.search(r"\*\*(\d+) domain members in `code` mode and (\d+) in `spec-plan`, (\d+) in all\*\*", text)
    assert match, "the spec no longer states the domain size in the expected form"
    code, spec_plan, total = (int(g) for g in match.groups())
    members = domain()
    actual_code = sum(1 for m in members if m[0] == "code")
    actual_sp = sum(1 for m in members if m[0] == "spec-plan")
    assert (actual_code, actual_sp, len(members)) == (code, spec_plan, total), (
        f"spec says {code}/{spec_plan}/{total}; computed {actual_code}/{actual_sp}/{len(members)}"
    )


def test_every_row_and_precondition_reference_resolves() -> None:
    """The drift class that produced most of four rounds' findings.

    A mutation proof naming a row that has since moved is a proof that cannot
    fail, so this is a correctness check on the criteria, not a typo sweep.
    """
    valid_rows = {r["id"] for r in routing_rows()}
    valid_pre = set(precondition_ids())
    problems = []
    for path in (SPEC, PLAN):
        text = path.read_text()
        # The Changelog is a historical record; its identifiers are frozen in time.
        body = text.split("## Changelog")[0]
        for ref in sorted(set(re.findall(r"\bR\d+\b", body))):
            if ref not in valid_rows:
                problems.append(f"{path.name}: {ref} is not a Routing row")
        for ref in sorted(set(re.findall(r"\bP\d+\b", body))):
            if ref not in valid_pre:
                problems.append(f"{path.name}: {ref} is not a Preconditions row")
    assert not problems, "\n".join(problems)


def test_the_plan_cites_exactly_the_criteria_the_spec_defines() -> None:
    spec_acs = set(re.findall(r"\*\*(AC\d+a?)", SPEC.read_text()))
    plan_acs = set(re.findall(r"\b(AC\d+a?)\b", PLAN.read_text()))
    assert not (plan_acs - spec_acs), f"plan cites undefined criteria: {sorted(plan_acs - spec_acs)}"
    assert not (spec_acs - plan_acs), f"criteria no task covers: {sorted(spec_acs - plan_acs)}"


def test_the_plan_does_not_contradict_the_spec_on_the_parameters_value_domain() -> None:
    """AC11 rules a boolean out; a task that re-admits it inverts the guard it routes through."""
    assert "or is a boolean" not in PLAN.read_text().split("## Changelog")[0], (
        "plan re-admits a boolean parameters value that AC11 excludes"
    )


def test_complete_with_is_derivable_from_the_live_transition_tables() -> None:
    """Every state the Routing table names must exist in the engine's own tables."""
    engine = _load_engine()
    known = set()
    for table in engine._TRANSITIONS_BY_MODE.values():
        for (src, _event), target in table.items():
            known.update((src, target))
    unknown = sorted({r["state"] for r in routing_rows()} - known)
    assert not unknown, f"Routing names states the engine does not have: {unknown}"


def test_every_load_identifier_resolves_to_a_shipped_reference() -> None:
    refs = ROOT / "packs/core/.apm/skills/work-loop/references"
    available = {
        "ref:" + str(p.relative_to(refs).with_suffix("")).replace("/", "-")
        for p in refs.rglob("*.md")
    }
    cited = {tok for attrs in action_rows().values() for tok in attrs["load"]}
    assert cited <= available, f"unresolvable load identifiers: {sorted(cited - available)}"
