"""The `work-loop-next-projection` contract's tables are self-consistent and match the engine.

Repeated pre-EXECUTE review on this spec has sustained findings dominated by one
class: a table changed and a reference to it did not. Row
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
SKILL = ROOT / "packs/core/.apm/skills/work-loop/SKILL.md"


def test_the_contract_documents_are_where_this_module_expects_them() -> None:
    """Fail loudly rather than skipping.

    A module-level skip on a missing target silently deletes every check below
    and leaves the suite green — which is exactly the control-that-cannot-fail
    shape this module exists to catch. The repository precedent fails.
    """
    missing = [str(p.relative_to(ROOT)) for p in (SPEC, PLAN, ENGINE, SKILL) if not p.is_file()]
    assert not missing, f"contract targets missing (renamed or moved?): {missing}"


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


def _one_tick(cell: str) -> str:
    """The single backticked token in a cell that must carry exactly one.

    Popping an arbitrary element of a set is deterministic only while every such
    cell happens to hold one token; a second token would make the parse vary per
    process under hash randomization instead of failing.
    """
    found = re.findall(r"`([^`]+)`", cell)
    assert len(found) == 1, f"expected exactly one token in cell {cell!r}, got {found}"
    return found[0]


# ── the four tables, parsed from the spec ──────────────────────────────────


def routing_rows() -> list[dict]:
    rows = []
    for cells in _rows(SPEC.read_text(), r"^\| R\d+ \|"):
        row_id, mode, state, last_event, disc, action = cells[:6]
        rows.append(
            {
                "id": row_id,
                "modes": {"code", "spec-plan"} if mode == "both" else {mode},
                "state": _one_tick(state) if "`" in state else state.strip(),
                # `*` means "any base key reaching this state". The literal
                # token `null` is the JSON null `engine-state.json` carries
                # before a run's first transition, so it maps to Python None.
                "events": (
                    None
                    if last_event.strip() == "`*`"
                    else {None if t == "null" else t for t in _ticks(last_event)}
                ),
                "disc": _ticks(disc),
                "action": _one_tick(action),
            }
        )
    return rows


def action_rows() -> dict[str, dict]:
    out = {}
    for cells in _rows(SPEC.read_text(), r"^\| `[a-z.\-]+` \| `(agent|command|wait|done|stop)` \|"):
        action, kind, params, load, human_wait = cells[:5]
        out[_one_tick(action)] = {
            "kind": _one_tick(kind),
            "params": set() if params == "—" else _ticks(params),
            "load": set() if load == "—" else _ticks(load),
            "human_wait": human_wait.strip() == "true",
        }
    return out


def precondition_ids() -> list[str]:
    return [cells[0] for cells in _rows(SPEC.read_text(), r"^\| P\d+ \|")]


def discriminators() -> list[dict]:
    """Parse the Discriminators table: which key each applies to, and its values.

    Transcribing this table instead of parsing it was the round-5 defect: an edit
    to any of its cells was invisible to every check, including the domain-size
    check that the spec calls the sole home of that figure.
    """
    out = []
    for cells in _rows(SPEC.read_text(), r"^\| D\d+ \|"):
        did, applies, read_from, values = cells[0], cells[1], cells[2], cells[3]
        states = {t for t in _ticks(applies) if t.isupper() or "-" in t and t.upper() == t}
        event = None
        if "last_event:" in applies:
            event = applies.split("last_event:")[1].strip().strip("`").strip()
        out.append({
            "id": did,
            "states": states,
            "event": event,
            "values": sorted(_ticks(values)),
            "reads": sorted(_ticks(read_from)),
            # The raw cell, so a checker can see what the tick parser could not.
            "reads_raw": read_from,
        })
    return out


def extra_base_keys() -> list[tuple]:
    """Parse the extra-base-keys table (initial and legacy keys)."""
    out = []
    for cells in _rows(SPEC.read_text(), r"^\| (both|code|spec-plan) \| `"):
        mode, last_event, state = cells[0].strip(), cells[1], cells[2]
        ev = _one_tick(last_event)
        modes = ("code", "spec-plan") if mode == "both" else (mode,)
        for m in modes:
            out.append((m, None if ev == "null" else ev, _one_tick(state)))
    return out


def _discriminator_for(state: str, event: str | None) -> list[str | None]:
    for d in discriminators():
        if state in d["states"] and (d["event"] is None or d["event"] == event):
            return d["values"]
    return [None]


def domain() -> list[tuple]:
    """Every (mode, state, last_event, discriminator) the verb can be asked."""
    engine = _load_engine()
    members = []
    for mode, table in engine._TRANSITIONS_BY_MODE.items():
        keys = {(event, target) for (_src, event), target in table.items()}
        for m, ev, state in extra_base_keys():
            if m == mode:
                keys.add((ev, state))
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


def _assumption_ids(text: str) -> set[str]:
    """Identifiers declared by an Assumptions bullet: `- <category> (**An**):`."""
    body = text.split("## Assumptions", 1)[-1]
    return set(re.findall(r"^- \w+ \(\*\*(A\d+)\*\*\):", body, re.M))


def _cited_assumption_ids(text: str) -> set[str]:
    """Identifiers a criterion cites, above the Assumptions section."""
    above = text.split("## Assumptions", 1)[0]
    return set(re.findall(r"\*\*(A\d+)\*\*", above))


def test_every_assumption_a_criterion_cites_actually_exists() -> None:
    """The restructure's own new drift class, mechanized.

    Moving grounding evidence out of the criteria created a citation direction
    that did not exist before: a criterion saying "the Assumptions record X" is
    load-bearing, and round 9 found two instances where the cited home was
    empty or held a claim the same document refuted elsewhere. Prose citations
    cannot be checked, so the citations are identifiers and this binds them.

    Both directions matter. A dangling citation points a reader at nothing; an
    uncited assumption carrying an identifier is a rename or a deletion that
    silently orphaned its criterion.
    """
    text = SPEC.read_text()
    declared, cited = _assumption_ids(text), _cited_assumption_ids(text)
    assert not (cited - declared), (
        f"criteria cite assumptions that do not exist: {sorted(cited - declared)}"
    )
    assert not (declared - cited), (
        f"assumptions carry an identifier no criterion cites: {sorted(declared - cited)}"
    )
    assert declared, "no identified assumptions parsed — the citation check would be vacuous"


def test_the_guard_facts_a3_and_a4_rest_on_still_hold() -> None:
    """Bind the symbol-level claims, because the citation check binds only names.

    A3 was inverted for a full round -- it said the engine independently refuses
    the clean event at the cap -- and the identifier check above would not have
    noticed, because the identifier was present and cited the whole time. That
    matters more than a documentation slip: an inverted A3 is an argument for
    weakening AC10a, which is the projection's only false-clean backstop.

    Scope is deliberate. Only the facts that are symbol-level and that a
    criterion depends on are asserted here; A4's "no hash comparison" and A5's
    loader behaviours are natural-language predicates over function bodies with
    no mechanical seam, and pinning prose for them would be the general
    non-contradiction check this module already declines to write.
    """
    guards = _load_engine()._GUARDS
    assert ("spec-plan", "reviewers-clean") not in guards, (
        "A3 says spec-plan's clean edge is unguarded, so AC10a is its only backstop; "
        "a guard now exists and A3's grounding is stale"
    )
    assert guards.get(("code", "reviewers-clean")).__name__ == (
        "_guard_check_spec_status_on_code_review"
    ), "A3 says code's clean edge carries only a Status-token check"
    for mode in ("code", "spec-plan"):
        assert guards.get((mode, "findings-remain")).__name__ == "_guard_check_phase_review", (
            f"A3 places the cap-consulting guard on {mode}'s findings-remain, not on its clean edge"
        )
    assert not any(event == "spec-ready" for _, event in guards), (
        "A4 says nothing guards spec-ready, which is why the Draft reset AC11c pins "
        "is the whole of the mitigation"
    )


def test_the_assumption_citation_check_can_fail() -> None:
    """Prove both directions redden, since the check above is green by design."""
    dangling = "A criterion citing **A99**.\n## Assumptions\n- Technical (**A1**): body\n"
    orphan = "A criterion citing **A1**.\n## Assumptions\n- Technical (**A1**): a\n- Technical (**A2**): b\n"
    assert _cited_assumption_ids(dangling) - _assumption_ids(dangling) == {"A99"}
    assert _assumption_ids(orphan) - _cited_assumption_ids(orphan) == {"A2"}


def test_the_plan_cites_exactly_the_criteria_the_spec_defines() -> None:
    """Parity over criterion identifiers, INCLUDING their letter suffixes.

    The suffix class was `a?` for one round, which silently truncated `AC15b` to
    `AC15` on the spec side and matched nothing on the plan side. Both sets then
    agreed on a token neither document contained, so the criterion added that
    round was outside this control entirely and deleting its only plan bullet
    left the module green. `[a-z]*` is greedy and covers every suffix the spec
    can define, so a newly lettered criterion is inside the check the day it is
    written -- which is how the eight added by the AC restructure were caught.
    """
    spec_acs = set(re.findall(r"\*\*(AC\d+[a-z]*)", SPEC.read_text()))
    plan_acs = set(re.findall(r"\b(AC\d+[a-z]*)\b", PLAN.read_text()))
    assert not (plan_acs - spec_acs), f"plan cites undefined criteria: {sorted(plan_acs - spec_acs)}"
    assert not (spec_acs - plan_acs), f"criteria no task covers: {sorted(spec_acs - plan_acs)}"


def test_the_parity_check_can_see_a_lettered_criterion() -> None:
    """Prove the control above can fail for a suffixed identifier.

    Asserting parity is green proves nothing about whether a suffixed criterion
    is inside the check — that was exactly the round-8 defect. This drives the
    same two patterns over a synthetic pair where a lettered criterion is
    spec-only, and requires it to surface.
    """
    # Synthetic identifiers, deliberately not ones the spec defines: this proves
    # the patterns, and must not start passing or failing because a real
    # criterion was added or renumbered.
    spec_pat, plan_pat = r"\*\*(AC\d+[a-z]*)", r"\b(AC\d+[a-z]*)\b"
    spec_acs = set(re.findall(spec_pat, "**AC99.** body\n**AC99z.** body\n"))
    plan_acs = set(re.findall(plan_pat, "covers AC99 only\n"))
    assert spec_acs == {"AC99", "AC99z"}, f"spec-side pattern lost a suffix: {spec_acs}"
    assert spec_acs - plan_acs == {"AC99z"}, (
        f"a spec-only lettered criterion did not surface as a gap: {spec_acs - plan_acs}"
    )


def test_the_plan_does_not_readmit_the_exact_boolean_phrase_ac11_removed() -> None:
    """A single-phrase regression pin, named as one.

    This is not general non-contradiction over AC11's value domain — that is a
    natural-language entailment with no mechanizable seam here. It pins one
    historical phrase that a task once carried and AC11 removed.
    """
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


# ── AC27: the two review references are conditionally loaded ───────────────

REVIEW_REFS = {"ref:finding-adjudication", "ref:review-verdict-record"}
DISPATCH_ACTIONS = ("run-review", "spec.review")


def test_ac27_no_reviewer_dispatch_action_loads_a_review_reference() -> None:
    """Both are needed only after a raw report exists, which is after dispatch.

    Naming them in `load` would pull ~3,000 words onto every dispatch, most of
    them on turns that never adjudicate and never aggregate — and it would
    contradict the shipped conditional-reference table, which already predicates
    both correctly.
    """
    attrs = action_rows()
    offenders = {
        action: sorted(attrs[action]["load"] & REVIEW_REFS)
        for action in DISPATCH_ACTIONS
        if action in attrs and attrs[action]["load"] & REVIEW_REFS
    }
    assert not offenders, f"review references loaded at dispatch time: {offenders}"


def test_ac27_the_shipped_surface_still_owns_the_conditional_routing() -> None:
    """The saving is only real if the shipped surface routes what `load` stopped naming.

    Deleting a `load` cell without this is not conditional loading, it is a
    reference nobody loads at all.
    """
    skill = SKILL.read_text()
    required = {
        "adjudication reference predicated on a dispatch":
            "Before every `finding-adjudicator` dispatch",
        "verdict reference predicated on emit/validate":
            "Emitting or validating the verdict record",
        # `raw-classify` alone occurs in three other places and survives deleting
        # the whole gateway section, so pin text unique to the gateway itself.
        "classification gates adjudication":
            "Then run `review raw-classify",
        "the Not checked footer is never fast-pathed":
            "## Not checked",
    }
    missing = [name for name, needle in required.items() if needle not in skill]
    assert not missing, f"shipped surface no longer states: {missing}"


def test_ac27_the_footer_carve_out_is_not_weakened() -> None:
    """A `## Not checked` footer must keep a clean-looking report off the fast path."""
    skill = SKILL.read_text()
    assert "never fast-pathed" in skill, (
        "the `## Not checked` carve-out no longer states that such a report "
        "cannot take the clean fast path"
    )


def test_every_state_field_a_discriminator_reads_is_covered_by_its_catch_all() -> None:
    """The Read-from column must not outgrow the closure bullet that guards it.

    Round 6 found a fifth field added to D5's Read-from while the closure bullet
    still said "any of its four fields", so an unrecognised value of the new
    field fell through the catch-all into a routing branch instead of `halt`.

    Round 8 found that binding the *count* was not enough. `fields` is parsed
    from backticked tokens, so a fifth field written WITHOUT backticks was
    invisible to the parser and left the count at four, and swapping one field
    for another kept the count at four as well. Both mutations passed. The guard
    therefore binds three things now:

    1. every snake_case identifier in the Read-from cell is backticked, so a
       field cannot hide from the parser by dropping its ticks;
    2. the closure bullet NAMES each field, and that set equals the Read-from
       set, so a substitution cannot survive on an unchanged count;
    3. the count word still agrees, which keeps the prose honest for a reader.

    Fails closed: a multi-field discriminator with no parsable closure bullet is
    a missing binding, not an exemption.
    """
    words = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}
    prose = SPEC.read_text()
    problems = []
    for d in discriminators():
        # state.json / spec.md / plan.md name the *file*; the fields are the rest
        fields = {f for f in d["reads"] if "." not in f and "<" not in f}
        # (1) nothing that looks like a field may sit in the cell unticked.
        #     `<...>` spans are placeholders for a composed value, not reads --
        #     D4 compares against `<run_id>:<transition_sequence>` -- so they are
        #     removed before the scan rather than reported as hidden fields.
        cell = re.sub(r"<[^>]*>", "", d["reads_raw"])
        bare = set(
            re.findall(r"(?<![`\w])([a-z][a-z0-9]*(?:_[a-z0-9]+)+)(?![`\w])", cell)
        )
        if bare:
            problems.append(
                f"{d['id']}: Read-from carries un-backticked identifier(s) {sorted(bare)}, "
                f"which the field parser cannot see"
            )
        m = re.search(
            rf"\*\*{d['id']} `malformed`\*\*.{{0,80}}?any of its \*{{0,2}}(\w+)\*{{0,2}} fields",
            prose,
            re.S,
        )
        if not m:
            if len(fields) > 1:
                problems.append(
                    f"{d['id']}: Read-from names {len(fields)} fields {sorted(fields)} but no "
                    f"'any of its <N> fields' closure bullet binds that count"
                )
            continue
        # (3) the count word agrees.
        stated = words.get(m.group(1))
        assert stated is not None, f"{d['id']}: unrecognised count word {m.group(1)!r}"
        if stated != len(fields):
            problems.append(
                f"{d['id']}: Read-from names {len(fields)} fields {sorted(fields)} "
                f"but the malformed bullet says '{m.group(1)}'"
            )
        # (2) the bullet names the same fields the cell does. A list item ends at
        #     the next blank line or the next top-level bullet, whichever comes
        #     first -- slicing to the next "\n- " alone swallowed the rest of the
        #     document, which made this comparison meaningless.
        tail = prose[m.start():]
        bullet = min(
            (tail.split(sep)[0] for sep in ("\n\n", "\n- ")), key=len
        )
        named = {t for t in _ticks(bullet) if "_" in t}
        if named != fields:
            problems.append(
                f"{d['id']}: the malformed bullet names {sorted(named)} but Read-from "
                f"names {sorted(fields)}; a same-count substitution would go unseen"
            )
    assert not problems, "\n".join(problems)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "AC27 path 2 is false on the shipped surface today: the always-loaded body "
        "still instructs an unconditional read of the adjudication reference before "
        "a review unit's first report, contradicting the same file's "
        "conditional-reference table. T8 owns the reconciliation. strict=True means "
        "this reddens the suite the moment T8 lands, forcing the marker off rather "
        "than letting a fixed defect sit behind a stale xfail."
    ),
)
def test_ac27_path_2_the_shipped_body_has_no_unconditional_adjudication_read() -> None:
    """Path 2 says a footer-free clean report loads neither reference.

    That is not true while the always-loaded body carries an unconditional read.
    The criterion had no failing artifact, so T8 could complete green without
    doing the reconciliation AC27 assigns it. This is that artifact.
    """
    body = SKILL.read_text()
    # The unconditional instruction wraps across two lines, so match on the
    # clause that makes it unconditional rather than on a single-line phrase.
    collapsed = " ".join(body.split())
    assert "Before the first report in a review unit, read" not in collapsed, (
        "the always-loaded body still instructs an unconditional read of the "
        "adjudication reference before any report exists; AC27 path 2 cannot hold "
        "until T8 reconciles it with the conditional-reference table"
    )
