# Plan: jira epic outcome view

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/atlassian/.apm/skills/flow-metrics/SKILL.md`
  (metrics from changelogs, with no sample-size threshold on any of them —
  percentiles are nulled only when fewer than two values exist, which is
  `statistics.quantiles`' floor rather than a confidence bar — Jira-only by
  pack);
  `packs/atlassian/.apm/skills/jira/SKILL.md` (the read client);
  `packs/atlassian/pack.toml` (where ADR-0126 D4's bridge declaration lands).
  Named deviation: no skill in this pack composes two other skills today, so
  the composition boundary has no precedent here.


> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling

## Approach

Almost nothing is new. `flow-metrics` already answers the flow half for a Jira
scope, and the `jira` client already reads the fields the state half needs.
This slice groups that output by Epic and puts an outcome next to it.

`jira-team-status` is **not** composed, though it looks like the obvious
candidate. Its first lifecycle stage reads the working directory's git remote,
which the artifact-free criteria forbid outright; its declared dependencies
route to `new-spec`, this repository's spec machinery; and what it uniquely
provides — the readiness rule, the agent-execution bar, pick-up routing — is
exactly what this view is forbidden to render. Composing it would import four
transitive dependencies and a repository read to discard the capability.

The one real decision is where an elicited outcome lives between one run and
the next, because no repository artifact is permitted and no write to Jira is
either. **The outcome lives in Jira, written by the team.** The view reads it
from one fixed location; where it is absent, the view says so and asks the
team for an outcome, turning what they state into text they paste in
themselves. That keeps the skill read-only, keeps the outcome
beside the work it describes, and means the second run is better than the
first without anything of ours persisting. The alternative — re-eliciting
every run — was rejected because a view that forgets is a view nobody opens
twice, which is the failure the parent's success signal names directly.

The riskiest part is the absent-outcome path, and it is risky because it is
the tempting one to drop: an Epic with no outcome contributes nothing to a
view trying to look complete. Dropping it reproduces the selection effect the
capability's research measured, so it is asserted by removal rather than by
presence.

## Constraints

- **ADR-0126 D2** confines coupling to declared bridge skills and this is not
  one; **D3** forbids mixing a standalone capability with a coupled one;
  **D4** requires the pack to declare its bridges in `pack.toml`. **D1** is a
  pack-level existential `packs/atlassian` already satisfies through its other
  standalone skills; what obliges this skill to return value with no
  repository artifact present is the parent intent's own contract.
- **ADR-0077** governs tracker-origin reading. Nothing read here acquires
  authority over anything.
- The parent intent's guardrails: read-only, adoption stays optional, and the
  outcome is never authored by this feature.
- `flow-metrics` stays Jira-only and in its own pack. This slice composes it
  rather than moving or generalising it.
- **`packs/AGENTS.md`** binds every task here: tests never live under `.apm/`,
  a non-cosmetic pack change bumps `pack.toml` and `.claude-plugin/plugin.json`
  together and updates the eval harness, `.apm/` is the projection source and
  adapter output is never edited directly, and shipped pack content carries no
  internal-governance citation — no ADR number or repository-only path in a
  `SKILL.md`.
- The pack JSON Schema is closed under `pack`, so `pack.toml` admits no new
  top-level table. `[pack.metadata]` is the deliberate exception — an open
  extension table — and is where a declaration the schema does not model
  belongs.

## Construction tests

- A fixture Jira scope with Epics carrying outcomes and Epics carrying none,
  in both ADF and plain-text description shapes, including one Epic whose
  `Outcome` heading is present but empty, one with two `Outcome` headings, and
  one whose block is terminated by a nested heading.
- A removal assertion: taking any Epic out of the rendered view fails.
- A verbatim assertion comparing rendered outcome text to the source.
- A filesystem hash before and after, with `.context/flow-metrics/cache/`
  pre-populated, asserted byte-identical.
- A run from a non-repository working directory with adopter-repository paths
  denied, asserted to return a correct non-empty answer.
- A coupling grep over the skill's sources, plus a walk of its dependency and
  invocation graph for any path reaching a pack-declared bridge, with a
  bridge-calling fixture that must fail.
- A recording transport over every client in the declared invocation graph,
  asserted to see read methods only.
- Four inertness assertions over the new `flow-metrics` mode. Only the
  stale-temp one discriminates against `--no-cache`; the other three are
  regression assertions the flag also satisfies.
- A process-table comparison across a run.
- A lint run over the `pack.toml` carrying the bridge declaration.
- A composition assertion: the flow figures match what `flow-metrics` returns
  for the same scope and window.

## Durable-output map

| Output | Task | Evidence |
| --- | --- | --- |
| Composed delivery reading grouped by Epic | T1 | figures match the shipping skills |
| Outcome read and absent-outcome rendering | T2 | removal assertion fails for every Epic |
| Read-only and zero-coupling guarantees | T3 | no write verb on any outbound client, no file, no machinery reference |
| Inert cache mode in `flow-metrics` | T4 | no cache read, write, cleanup or directory creation; the stale-temp assertion reds under `--no-cache` |
| Bridge declaration in `pack.toml` | T5 | declared in `[pack.metadata]`, lint green, this skill absent from the list |
| The user-facing promise | T3 | what the view answers, and what it does not, in `guides/atlassian/` |
| Pack release: versions, evals, projections, changelog | T6 | both manifests match at the bumped minor; self-host re-runs to a zero diff |

## Design (LLD)

### Design decisions

- **The outcome lives in the Epic's `description`, under an `Outcome`
  heading, written by the team.** No repository artifact is permitted and this
  slice writes nothing, so Jira is the only home. Within Jira the choice is
  narrow: Atlassian's field reference lists no system field for a goal or
  outcome, and only `description` and `environment` are free-form multi-line
  system fields — `environment` means "where the bug reproduces" and is off
  most Epic screens. A custom field is semantically cleaner but needs an admin
  to create it per instance, and in team-managed projects custom fields cannot
  be reused across spaces, so it would not even port between projects on one
  site. That is the prerequisite the parent's guardrail forbids. Storing it in Jira keeps the outcome beside the work, survives
  between runs, and costs this skill no write authority.
- **Paste-ready text rather than a write.** Handing the team the exact string
  and its location gets the outcome recorded without this skill acquiring the
  authority to record it, which is the parent's guardrail.
- **Compose, do not recompute.** Re-deriving cycle time here would put a
  second definition of it in the same pack, and the two would drift with
  nothing comparing them.
- **`flow-metrics` gains an inert cache mode, and this slice owns that
  change.** Its `--no-cache` flag is not enough: `cleanup_stale_tmps` runs
  above the flag's branch against a cwd-relative directory, so a "read-only"
  view would still unlink files from an existing cache wherever it ran. The
  flag does suppress the read, the write and the directory creation.
  The alternative — composing it unchanged and accepting the writes — fails
  the parent's read-only guardrail, which is not waivable. The change is
  additive and default-off, so the slice still ships on its own.

### The per-Epic problem, and why `--per-issue`

`flow-metrics` emits no per-Epic breakdown. Its output schema carries
`aggregates`, `per_team`, and a `cohort_breakdown` that only appears with
`--cohort-jql` and is a two-sided cohort/control split. Nothing groups by Epic,
so a per-Epic figure is either grouped here or does not exist.

Three routes were weighed. Running `flow-metrics` once per Epic scoped by
`--jql` costs one Jira search per Epic and gives every row its own moment.
Dropping per-Epic flow entirely leaves the outcome beside a scope-wide number,
which answers a different question than the one the parent asks. The chosen
route runs `flow-metrics --per-issue` once and groups its rows here.

Two consequences are load-bearing and neither is hidden:

- **A per-issue row carries no Epic.** Its wire fields are `key`,
  `issue_created`, `first_commitment_at`, `first_delivery_at`,
  `cycle_eligible`, `cycle_time_hours`, `lead_time_hours`, `flow_efficiency`,
  `rework_count`, `issuetype_at_delivery`, `issuetype_bucket`, `team`,
  `delivered_in_window`, `cancelled_in_window`, `wip_at_to`, plus `cohort`
  only under `--cohort-jql`. The Epic join therefore comes from the view's own
  parent-link read.
- **`--per-issue` requires `--output FILE` and exits 2 without it.** So the
  view writes a JSONL file. It goes to a scratch path outside both hashed
  roots and is removed before returning. Calling the view "read-only" while it
  writes that file would be false; the guarantee is that no repository
  artifact, no Jira object and neither named root changes.

Aggregation stays honest because no percentile is rendered: every per-Epic
figure is a count over rows `flow-metrics` already derived. Re-deriving cycle
time per Epic would be the second definition this slice exists to avoid.

### Data & schema

Input is a Jira scope. Per Epic: the delivery reading from the two shipping
skills, plus the outcome text read from the documented location. Output
carries both, the throughput count with its window, and the moment each
reading was taken.

### Interfaces & contracts

The `jira` client is invoked as it stands. `flow-metrics` gains one
default-off inert cache mode, which is the only interface this slice adds and
the only way this view composes it.

### Component / module decomposition

One new skill in `packs/atlassian/.apm/skills/jira-epic-outcome-view/`, shaped
as a deterministic script like `flow-metrics` and `jira` rather than a
conversational skill body, so its figures are mechanically comparable against
what `flow-metrics` returns. Its `scripts/jira_epic_outcome_view/` package
carries `outcome.py` — `extract_outcome(description) -> str | None`, the pure
reader over both description shapes that T2's stub imports. Plus the
`pack.toml` bridge declaration.

### State & control flow

Computed on invocation. No cache, no resident state, and nothing written to
either named root. The one write is the transient per-issue JSONL that
`--per-issue` requires, which lands outside both roots and is removed before
the view returns.

### Behavior & rules

An Epic with no outcome renders with an explicit nothing and a prompt. Text
is labelled paste-ready only once the team has supplied its substance; a
scaffold nobody has filled in stays a prompt. An Epic whose outcome location
holds something unparseable renders the
raw text rather than discarding it, because discarding is indistinguishable
from absent.

### Failure, edge cases & resilience

A Jira error is surfaced rather than rendered as an empty scope, because "no
Epics" and "could not reach Jira" are different facts. A scope with zero
completed items still renders the state half, which needs no sample.

### Quality attributes (NFRs)

Read-only is the pass/fail bar: no write verb on any outbound client, and
both named roots byte-identical across a run apart from the transient JSONL,
which lands outside them and is removed.
The view renders no percentile at all, because `flow-metrics` applies no
sample-size threshold; the spec's criterion states the floor and is the one
place this slice describes it.

### Dependencies & integration

A Jira credential through the broker, already this pack's requirement. No new
dependency, and explicitly nothing from this repository's machinery.

## Criterion disposition

Every acceptance criterion, its owning task, and its verification mode. This
table is the binding record: it is total and disjoint by construction, so a
criterion cannot acquire two dispositions or lose its one. The spec's stub
tally is derived from it, and three rounds of drift came from maintaining
those numbers separately instead.

| Criterion | Task | Mode |
| --- | --- | --- |
| AC1 | T1 | TDD — validated red stub |
| AC2 | T1 | TDD — validated red stub |
| AC3 | T1 | TDD — validated red stub |
| AC4 | T1 | goal-based check — `no stub (goal-based check)` |
| AC5 | T1 | TDD — validated red stub |
| AC6 | T1 | TDD — validated red stub |
| AC7 | T1 | goal-based check — `no stub (goal-based check)` |
| AC8 | T1 | TDD — `no stub (implementation-discovered)` |
| AC9 | T1 | TDD — validated red stub |
| AC10 | T2 | goal-based check — `no stub (goal-based check)` |
| AC11 | T2 | TDD — `no stub (implementation-discovered)` |
| AC12 | T2 | TDD — validated red stub |
| AC13 | T2 | goal-based check — `no stub (goal-based check)` |
| AC14 | T2 | goal-based check — `no stub (goal-based check)` |
| AC15 | T2 | TDD — validated red stub |
| AC16 | T2 | TDD — validated red stub |
| AC17 | T2 | TDD — `no stub (implementation-discovered)` |
| AC18 | T2 | TDD — `no stub (implementation-discovered)` |
| AC19 | T2 | TDD — `no stub (implementation-discovered)` |
| AC20 | T2 | TDD — `no stub (implementation-discovered)` |
| AC21 | T2 | TDD — validated red stub |
| AC22 | T2 | TDD — validated red stub |
| AC23 | T2 | goal-based check — `no stub (goal-based check)` |
| AC24 | T2 | TDD — `no stub (implementation-discovered)` |
| AC25 | T2 | TDD — `no stub (implementation-discovered)` |
| AC26 | T2 | TDD — validated red stub |
| AC27 | T2 | TDD — `no stub (implementation-discovered)` |
| AC28 | T2 | TDD — `no stub (implementation-discovered)` |
| AC29 | T2 | TDD — `no stub (implementation-discovered)` |
| AC30 | T3 | goal-based check — `no stub (goal-based check)` |
| AC31 | T3 | goal-based check — `no stub (goal-based check)` |
| AC32 | T3 | goal-based check — `no stub (goal-based check)` |
| AC33 | T3 | goal-based check — `no stub (goal-based check)` |
| AC34 | T3 | goal-based check — `no stub (goal-based check)` |
| AC35 | T3 | goal-based check — `no stub (goal-based check)` |
| AC36 | T1 | goal-based check — `no stub (goal-based check)` |
| AC37 | T1 | goal-based check — `no stub (goal-based check)` |
| AC38 | T3 | goal-based check — `no stub (goal-based check)` |
| AC39 | T4 | TDD — validated red stub |
| AC40 | T3 | goal-based check — `no stub (goal-based check)` |
| AC41 | T3 | goal-based check — `no stub (goal-based check)` |
| AC42 | T3 | goal-based check — `no stub (goal-based check)` |
| AC43 | T3 | goal-based check — `no stub (goal-based check)` |
| AC44 | T6 | goal-based check — `no stub (goal-based check)` |
| AC45 | T3 | goal-based check — `no stub (goal-based check)` |
| AC46 | T5 | goal-based check — `no stub (goal-based check)` |
| AC47 | T6 | goal-based check — `no stub (goal-based check)` |
| AC48 | T6 | goal-based check — `no stub (goal-based check)` |
| AC49 | T6 | goal-based check — `no stub (goal-based check)` |
| AC50 | T6 | goal-based check — `no stub (goal-based check)` |
| AC51 | T6 | goal-based check — `no stub (goal-based check)` |
| AC52 | T6 | goal-based check — `no stub (goal-based check)` |
| AC53 | T1 | goal-based check — `no stub (goal-based check)` |
| AC54 | T1 | TDD — validated red stub |
| AC55 | T1 | TDD — validated red stub |
| AC56 | T3 | goal-based check — `no stub (goal-based check)` |
| AC57 | T6 | visual / manual QA — `no stub (manual QA)` |

## Tasks

### T1: the delivery reading is composed and grouped by Epic

**Depends on:** T4

**Tests:**
- Each Epic in the fixture scope renders a delivery reading and an outcome
  position, grouped under that Epic. Verifies *the view groups a Jira scope's
  work by Epic and renders, for each Epic, both*.
- Per-Epic flow figures are counts over `flow-metrics`' own per-issue rows,
  applying that skill's counting rule rather than a plain count of delivered
  rows. State and parent data carry the Jira-read moment and the flow reading
  carries its own; neither is asserted to be one atomic snapshot. Verifies
  *the flow reading is `flow-metrics` run once in `--per-issue` mode*,
  *per-Epic throughput applies that skill's own counting rule*, and *the view
  states the moment of the flow reading and the moment of the Jira read*.
- Every rendered reading states its moment, and no percentile is rendered;
  throughput appears as a count with its window beside the
  non-distributional observations. Verifies *every rendered reading states
  the moment*, *renders no percentile*, and *renders throughput as a count
  with its window*.

**Stubs:**
- `test_each_epic_carries_a_delivery_reading_and_an_outcome_position` (AC1) — stub: true
- `test_flow_figures_are_counts_over_flow_metrics_rows` (AC2) — stub: true
- `test_rows_are_grouped_to_epics_by_the_parent_link` (AC5) — stub: true
- `test_an_unresolved_parent_chain_is_rendered_not_dropped` (AC6) — stub: true
- `test_a_delivered_subtask_does_not_raise_throughput` (AC3) — stub: true
- `test_include_subtasks_counts_the_delivered_subtask` (AC3) — stub: true
- `test_no_percentile_is_rendered` (AC54) — stub: true
- `test_throughput_is_a_count_with_its_window` (AC55) — stub: true
- `test_both_moments_are_stated_separately` (AC9) — stub: true
- AC8 (the state observations: age, blocked, since when, what moved) —
  `no stub (implementation-discovered)`. **Discovery predicate:** `jira_state`
  is contracted as an input above, but which field carries "flagged" varies by
  instance and is resolved from the field catalogue at run time, so the
  per-observation derivation is settled when that resolution lands in this
  task. **Proof obligation:** in EXECUTE, each observation asserted against a
  fixture carrying an in-flight issue, a flagged issue, an instance with no
  flagged field, and an Epic with no in-flight issues at all.
- AC36, AC37 (the JSONL lands outside both hashed roots and is removed,
  including on failure) — `no stub (goal-based check)`: they assert
  process-level filesystem state, not a return value.

Validated in PLAN from disposable scratch outside the repository test tree:
`python -m py_compile` clean; `pytest` collected 9 tests and all 9 errored on
the absent `jira_epic_outcome_view.view` module — the intended red. The
fixtures use `flow-metrics`' real per-issue wire fields, read from
`output.py::_per_issue_row_to_dict`; an earlier draft invented an Epic-keyed
aggregate shape that skill does not emit. The counting rule is read from
`aggregate.py`: throughput increments only when a delivered row's bucket is
not `subtask` (absent `--include-subtasks`), while WIP increments on
`wip_at_to` with no filter. An earlier draft counted every delivered row. The
disposable copy was removed.

Deferred to EXECUTE: the out-of-process CLI surface — exit code and stdout
shape — is asserted on the full test rather than here, per the rule that an
out-of-process surface stubs the nearest in-process contract.

```python
# Stored and validated in PLAN's T1 Tests: subsection. Each test carries its
# own marker. Fixtures use flow-metrics' real per-issue wire contract, taken
# from `output.py::_per_issue_row_to_dict` — the field list is not invented.
from __future__ import annotations

import json
import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_VIEW_PKG = (
    _PACK_ROOT / ".apm" / "skills" / "jira-epic-outcome-view"
    / "scripts" / "jira_epic_outcome_view"
)
_VIEW_NAME = "atlassian_jira_epic_outcome_view"


def _load_view_submodule(submodule: str):
    """Load the view's package under a pack-and-skill-qualified name, never by
    putting `scripts/` on `sys.path`: one bare name would otherwise bind to
    whichever pack's directory landed first. Red today - the skill does not
    exist, so there is no `__init__.py` to load."""
    spec = importlib.util.spec_from_file_location(
        _VIEW_NAME, _VIEW_PKG / "__init__.py",
        submodule_search_locations=[str(_VIEW_PKG)],
    )
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(_VIEW_NAME)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return importlib.import_module(f"{_VIEW_NAME}.{submodule}")

FLOW_MOMENT = "2026-09-24T11:30:00Z"
JIRA_MOMENT = "2026-09-24T11:30:12Z"
WINDOW = {"from": "2026-08-25", "to": "2026-09-24"}

# The Jira-side half of the read that also supplies the parent links. A
# per-issue row carries no status-category timestamp and no flagged field, so
# age, blocked and since-when are unreachable without this input.
JIRA_STATE = {
    "PROJ-1": {"status_category": "Done", "status_category_changed_at": "2026-08-06T09:00:00+00:00", "flagged": False, "flagged_changed_at": None},
    "PROJ-2": {"status_category": "Done", "status_category_changed_at": "2026-08-20T09:00:00+00:00", "flagged": False, "flagged_changed_at": None},
    "PROJ-3": {"status_category": "In Progress", "status_category_changed_at": "2026-09-10T09:00:00+00:00", "flagged": True, "flagged_changed_at": "2026-09-12T09:00:00+00:00"},
    "PROJ-4": {"status_category": "Done", "status_category_changed_at": "2026-09-01T09:00:00+00:00", "flagged": False, "flagged_changed_at": None},
}


@pytest.fixture
def view():
    return _load_view_submodule("view")


def _row(key, *, delivered, wip, cycle_hours, bucket="feature"):
    """One flow-metrics per-issue row, exact wire fields."""
    return {
        "key": key,
        "issue_created": "2026-08-01T09:00:00+00:00",
        "first_commitment_at": "2026-08-02T09:00:00+00:00",
        "first_delivery_at": "2026-08-06T09:00:00+00:00" if delivered else None,
        "cycle_eligible": delivered,
        "cycle_time_hours": cycle_hours,
        "lead_time_hours": cycle_hours,
        "flow_efficiency": 0.5,
        "rework_count": 0,
        "issuetype_at_delivery": "Story",
        "issuetype_bucket": bucket,
        "team": "Atlas",
        "delivered_in_window": delivered,
        "cancelled_in_window": False,
        "wip_at_to": wip,
    }


@pytest.fixture
def per_issue_rows():
    return [
        _row("PROJ-1", delivered=True, wip=False, cycle_hours=96.0),
        _row("PROJ-2", delivered=True, wip=False, cycle_hours=12.0),
        _row("PROJ-3", delivered=False, wip=True, cycle_hours=None),
        # Delivered, but a subtask: flow-metrics excludes it from throughput
        # unless --include-subtasks is set, so the view must too.
        _row("PROJ-4", delivered=True, wip=False, cycle_hours=8.0, bucket="subtask"),
    ]


@pytest.fixture
def parents():
    """The view's own parent-link read, resolved to the Epic rung.

    Jira Software nests Epic > Story > Subtask, so a subtask's immediate
    parent is a Story and reaching its Epic takes two hops. This mapping is
    the resolved result the view supplies: issue key to Epic key, whatever
    the depth. PROJ-4 is a subtask of PROJ-1 and resolves to the same Epic.
    """
    return {
        "PROJ-1": "PROJ-100",
        "PROJ-2": "PROJ-100",
        "PROJ-3": "PROJ-100",
        "PROJ-4": "PROJ-100",
    }


def _build(view, rows, parents, outcomes, include_subtasks=False):
    return view.build_epic_rows(
        per_issue_rows=rows,
        parents=parents,
        jira_state=JIRA_STATE,
        outcomes=outcomes,
        include_subtasks=include_subtasks,
        window=WINDOW,
        flow_taken_at=FLOW_MOMENT,
        jira_taken_at=JIRA_MOMENT,
    )


# STUB: AC1
def test_each_epic_carries_a_delivery_reading_and_an_outcome_position(
    view, per_issue_rows, parents
):
    """An Epic with no outcome still carries the position — absent is an
    answer, not an omission."""
    rows = _build(view, per_issue_rows, parents, {"PROJ-100": None})

    assert len(rows) == 1
    assert rows[0]["epic"] == "PROJ-100"
    assert "delivery" in rows[0]
    assert rows[0]["outcome"]["recorded"] is False


# STUB: AC2
def test_flow_figures_are_counts_over_flow_metrics_rows(view, per_issue_rows, parents):
    """Composition, not recomputation: throughput is the count of rows
    flow-metrics marked delivered_in_window, and work in flight the count it
    marked wip_at_to."""
    delivery = _build(view, per_issue_rows, parents, {"PROJ-100": None})[0]["delivery"]

    assert delivery["throughput"]["count"] == 2
    assert delivery["work_in_flight"] == 1


# STUB: AC3
def test_a_delivered_subtask_does_not_raise_throughput(view, per_issue_rows, parents):
    """flow-metrics counts throughput as delivered-in-window AND not a subtask
    bucket, unless --include-subtasks. Counting every delivered row would
    report 3 here and publish a larger number under the same name."""
    delivery = _build(view, per_issue_rows, parents, {"PROJ-100": None})[0]["delivery"]

    assert delivery["throughput"]["count"] == 2


# STUB: AC3
def test_include_subtasks_counts_the_delivered_subtask(view, per_issue_rows, parents):
    """The other side of the same rule: with the flag set, flow-metrics counts
    the subtask, so the view must report 3 rather than holding 2 fixed."""
    delivery = _build(
        view, per_issue_rows, parents, {"PROJ-100": None}, include_subtasks=True
    )[0]["delivery"]

    assert delivery["throughput"]["count"] == 3


# STUB: AC6
def test_an_unresolved_parent_chain_is_rendered_not_dropped(view, per_issue_rows, parents):
    """A chain that never reaches an in-scope Epic must still surface its
    issue and the reason, and must not withhold the rest of the view."""
    orphaned = {k: v for k, v in parents.items() if k != "PROJ-2"}

    rows = _build(view, per_issue_rows, orphaned, {"PROJ-100": None})

    groups = {r["epic"]: r for r in rows}
    # PROJ-2 alone is unresolvable; the other three still group normally, so
    # the partial answer survives rather than the whole view being withheld.
    assert set(groups) == {"PROJ-100", "unattributed"}
    unattributed = groups["unattributed"]
    assert "PROJ-2" in unattributed["issues"]
    assert unattributed["reason"]


# STUB: AC5
def test_rows_are_grouped_to_epics_by_the_parent_link(view, per_issue_rows):
    """The join comes from the view's own read; a per-issue row has no Epic
    field, so two parents must produce two Epic rows from the same input."""
    split = {
        "PROJ-1": "PROJ-100",
        "PROJ-2": "PROJ-200",
        "PROJ-3": "PROJ-200",
        "PROJ-4": "PROJ-100",
    }

    rows = _build(view, per_issue_rows, split, {"PROJ-100": None, "PROJ-200": None})

    by_epic = {r["epic"]: r for r in rows}
    # Every fixture row resolves here, so no unattributed group appears. The
    # sibling test omits one mapping on purpose and expects that group.
    assert set(by_epic) == {"PROJ-100", "PROJ-200"}
    assert by_epic["PROJ-100"]["delivery"]["throughput"]["count"] == 1
    assert by_epic["PROJ-200"]["delivery"]["throughput"]["count"] == 1


# STUB: AC54
def test_no_percentile_is_rendered(view, per_issue_rows, parents):
    """flow-metrics applies no sample-size threshold, so a p50 over two
    completions would reach a reader as fact. No derived duration may survive
    into the row at any depth."""
    rows = _build(view, per_issue_rows, parents, {"PROJ-100": None})

    serialized = json.dumps(rows)
    for marker in ("p50", "p75", "p90", "percentile", "cycle_time", "lead_time"):
        assert marker not in serialized


# STUB: AC55
def test_throughput_is_a_count_with_its_window(view, per_issue_rows, parents):
    """A bare count without its window is unreadable."""
    throughput = _build(view, per_issue_rows, parents, {"PROJ-100": None})[0][
        "delivery"
    ]["throughput"]

    assert throughput["count"] == 2
    assert throughput["window"] == WINDOW


# STUB: AC9
def test_both_moments_are_stated_separately(view, per_issue_rows, parents):
    """Two passes over Jira. A single timestamp implying one atomic snapshot
    is the claim this pins against."""
    row = _build(view, per_issue_rows, parents, {"PROJ-100": None})[0]

    assert row["flow_taken_at"] == FLOW_MOMENT
    assert row["jira_taken_at"] == JIRA_MOMENT
```

**Verification mode:** TDD. Artifacts live in
`packs/atlassian/tests/skills/jira-epic-outcome-view/`; `packs/AGENTS.md`
forbids tests under `.apm/`.

**Approach:**
- `flow-metrics` is composed through T4's inert mode rather than recomputed:
  re-deriving cycle time would create a second definition of it inside one
  pack. The state fields carry no such definition — they are direct reads —
  so taking them from the `jira` client clones nothing.

**Done when:** the composition assertion holds against the fixture scope.

**Touches:** packs/atlassian/.apm/skills/jira-epic-outcome-view/**,
packs/atlassian/tests/skills/jira-epic-outcome-view/**

### T2: every Epic appears, and one without an outcome says so

**Depends on:** T1

**Tests:**
- An Epic's recorded outcome is reproduced verbatim from the block under the
  description's `Outcome` heading, with the surrounding description not
  rendered as outcome text, against fixtures in both ADF and plain-text
  shapes. A missing heading and a present-but-empty heading both render the
  explicit nothing and the prompt. Verifies *the outcome location is the
  Epic's `description`*, *reproduced verbatim from that block*, *the heading
  is located in both description shapes*, and *an Epic whose description has
  no `Outcome` heading, and one whose heading is present with an empty block*.
- The expected Epic set is derived from the fully paginated Jira result for
  the calling credential and the rendered set equals it exactly; each member
  is a failing removal control; and every run carries the browse-permission
  disclosure. Verifies *the expected Epic set is derived from the fully
  paginated Jira result*, *the rendered view's Epic set equals that expected
  set exactly*, *removing any single member fails the check*, and *every run
  states that the set covers only what the calling credential can browse*.
- Every outcome-less Epic in a fixture holding several renders both the
  explicit nothing and the prompt. Verifies *renders an explicit statement
  that none is recorded* and *also renders a prompt asking the team to state
  an outcome*.
- A run where the team states an outcome renders those exact words as
  paste-ready text naming the one fixed location; a run where the team
  declines renders the prompt and no paste-ready text. An assertion fails if
  the paste-ready output omits that location or names a different one.
  Verifies *the view accepts an outcome the team states*, *renders those exact
  words back as paste-ready text, naming the location*, and *a run where the
  team supplies nothing*.
- A fixture where the feature would supply outcome substance fails. Verifies
  *a run that offers invented outcome substance fails*.
- Output labelled paste-ready is asserted to carry team-supplied substance,
  and a fixed scaffold with no team input is asserted to render as a prompt
  under a different label. Verifies *text is called paste-ready only when it
  carries outcome substance the team supplied*.
- No score, grade or judgement appears. Verifies *renders no score, grade or
  judgement*.

**Stubs:**
- `test_reads_the_block_under_the_heading_from_server_plain_text` (AC12) — stub: true
- `test_reads_the_block_under_the_heading_from_cloud_adf` (AC12) — stub: true
- `test_text_outside_the_block_is_not_returned_as_the_outcome` (AC16) — stub: true
- `test_absent_or_empty_block_is_no_outcome_recorded` (AC15, 5 cases) — stub: true
- `test_outcome_less_epic_renders_an_explicit_nothing` (AC21) — stub: true
- `test_outcome_less_epic_also_renders_a_prompt` (AC22) — stub: true
- `test_no_score_grade_or_judgement_is_rendered` (AC26) — stub: true
- AC17, AC18, AC19, AC20 (Epic-set derivation, exact equality, the browse
  disclosure and the removal control) — `no stub (implementation-discovered)`. **Discovery
  predicate:** the callable seam is the paginated-search wrapper over the
  `jira` client, whose shape is settled when T1 fixes how the view invokes it.
  **Proof obligation:** in EXECUTE, a removal control that reds for every
  member of the expected set, plus an assertion that the disclosure is present
  on every run.
- AC10 (the location is fixed, documented in `SKILL.md`, and not configurable
  per invocation) — `no stub (goal-based check)`: it is asserted by reading the
  shipped documentation and the CLI surface, not by a return value.
- AC11, AC24, AC25, AC27, AC28, AC29 (the same fixed location in both texts, the answer-input edge cases, the paste-ready
  label rule, the authorship refusal, and both elicitation directions) —
  `no stub (implementation-discovered)`. **Discovery predicate:** the input
  surface is now contracted as a repeatable `--outcome EPIC-KEY=<text>`
  argument, but the row-level representation it produces — how a supplied
  answer reaches `build_epic_rows` — is settled when the CLI layer lands in
  this task. **Proof obligation:** in EXECUTE, a run passing `--outcome` for
  one Epic renders those exact words as paste-ready text naming the location,
  a run omitting it renders the prompt and no paste-ready text, and a fixture
  in which the view would supply substance fails. AC23's three decided cases
  are each their own obligation: a key outside the queried scope exits
  non-zero naming that key, the same key given twice exits non-zero the same
  way, and `EPIC-KEY=` with empty text renders the prompt and exits as a
  normal decline. **Discovery
  predicate:** these cross the interactive boundary, and the seam that carries
  a team-supplied answer is defined by T1's invocation shape. **Proof
  obligation:** in EXECUTE, a supplied-substance run rendering those exact
  words as paste-ready text, and a declined run rendering the prompt with no
  paste-ready text.

Validated in PLAN from disposable scratch outside the repository test tree:
`python -m py_compile` clean; `pytest` collected 11 tests and all 11 errored
on the absent `jira_epic_outcome_view` modules — the intended red. The
disposable copy was removed.

```python
# Stored and validated in PLAN's T2 Tests: subsection. Each test carries its
# own marker and pins one criterion. These are full assertions: the criteria
# pin the behaviour exactly, so nothing here is a shape placeholder. The
# Epic-set and elicitation criteria are not stubbed here — see T2's `no stub`
# dispositions.
from __future__ import annotations

import json
import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_VIEW_PKG = (
    _PACK_ROOT / ".apm" / "skills" / "jira-epic-outcome-view"
    / "scripts" / "jira_epic_outcome_view"
)
_VIEW_NAME = "atlassian_jira_epic_outcome_view"


def _load_view_submodule(submodule: str):
    """Load the view's package under a pack-and-skill-qualified name, never by
    putting `scripts/` on `sys.path`: one bare name would otherwise bind to
    whichever pack's directory landed first. Red today - the skill does not
    exist, so there is no `__init__.py` to load."""
    spec = importlib.util.spec_from_file_location(
        _VIEW_NAME, _VIEW_PKG / "__init__.py",
        submodule_search_locations=[str(_VIEW_PKG)],
    )
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(_VIEW_NAME)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return importlib.import_module(f"{_VIEW_NAME}.{submodule}")


@pytest.fixture
def outcome():
    return _load_view_submodule("outcome")


def _adf(*nodes: dict) -> dict:
    return {"type": "doc", "version": 1, "content": list(nodes)}


def _heading(text: str) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": 2},
        "content": [{"type": "text", "text": text}],
    }


def _para(text: str) -> dict:
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


# STUB: AC12
def test_reads_the_block_under_the_heading_from_server_plain_text(outcome):
    """Server/DC REST v2 shape: description is plain text."""
    description = (
        "Build the new returns flow for self-serve customers.\n"
        "\n"
        "## Outcome\n"
        "Customers resolve a return without contacting support.\n"
    )

    assert (
        outcome.extract_outcome(description)
        == "Customers resolve a return without contacting support."
    )


# STUB: AC12
def test_reads_the_block_under_the_heading_from_cloud_adf(outcome):
    """Cloud REST v3 shape: description is an ADF document. A reader that
    handles only plain text returns nothing here, which is indistinguishable
    from an Epic with no outcome — the failure this pins."""
    description = _adf(
        _para("Build the new returns flow for self-serve customers."),
        _heading("Outcome"),
        _para("Customers resolve a return without contacting support."),
    )

    assert (
        outcome.extract_outcome(description)
        == "Customers resolve a return without contacting support."
    )


# STUB: AC16
def test_text_outside_the_block_is_not_returned_as_the_outcome(outcome):
    """The description is shared with scope and acceptance criteria, so
    verbatim reproduction is scoped to the block, not the whole field."""
    description = (
        "Scope: self-serve only.\n"
        "\n"
        "## Outcome\n"
        "Customers resolve a return without contacting support.\n"
        "\n"
        "## Acceptance criteria\n"
        "- Returns portal ships.\n"
    )

    extracted = outcome.extract_outcome(description)

    assert extracted == "Customers resolve a return without contacting support."
    assert "Scope: self-serve only." not in extracted
    assert "Returns portal ships." not in extracted


@pytest.mark.parametrize(
    "description",
    [
        pytest.param(
            "Build the new returns flow.\n\n## Scope\nSelf-serve only.\n",
            id="heading-absent-plain-text",
        ),
        pytest.param(
            "Build the new returns flow.\n\n## Outcome\n\n## Scope\nSelf-serve.\n",
            id="heading-present-but-empty-plain-text",
        ),
        pytest.param(
            _adf(_para("Build the new returns flow.")),
            id="heading-absent-adf",
        ),
        pytest.param(
            _adf(_heading("Outcome"), _heading("Scope"), _para("Self-serve.")),
            id="heading-present-but-empty-adf",
        ),
        pytest.param(None, id="description-null"),
    ],
)
# STUB: AC15
def test_absent_or_empty_block_is_no_outcome_recorded(outcome, description):
    """A missing heading and a present-but-empty heading are the same
    answer to the reader. Treating only the first as absent renders a blank
    for the second, which is the failure the absent-outcome path exists to
    prevent."""
    assert outcome.extract_outcome(description) is None


# The three tests below assert the row builder rather than the extractor,
# which is why they sit alongside the extraction tests in the same task.
@pytest.fixture
def view():
    return _load_view_submodule("view")


# One contract, shared with T1: per-issue rows in flow-metrics' wire shape, the
# view's own parent-link read, and the two moments stated separately. An
# earlier draft called this with an Epic-keyed aggregate that flow-metrics does
# not emit, which would have pinned two incompatible signatures for one
# function.
def _rows(view, outcome_text):
    return view.build_epic_rows(
        per_issue_rows=[
            {
                "key": "PROJ-1",
                "issue_created": "2026-08-01T09:00:00+00:00",
                "first_commitment_at": "2026-08-02T09:00:00+00:00",
                "first_delivery_at": "2026-08-06T09:00:00+00:00",
                "cycle_eligible": True,
                "cycle_time_hours": 96.0,
                "lead_time_hours": 96.0,
                "flow_efficiency": 0.5,
                "rework_count": 0,
                "issuetype_at_delivery": "Story",
                "issuetype_bucket": "feature",
                "team": "Atlas",
                "delivered_in_window": True,
                "cancelled_in_window": False,
                "wip_at_to": False,
            }
        ],
        parents={"PROJ-1": "PROJ-100"},
        jira_state={"PROJ-1": {"status_category": "Done", "status_category_changed_at": "2026-08-06T09:00:00+00:00", "flagged": False, "flagged_changed_at": None}},
        outcomes={"PROJ-100": outcome_text},
        window={"from": "2026-08-25", "to": "2026-09-24"},
        flow_taken_at="2026-09-24T11:30:00Z",
        jira_taken_at="2026-09-24T11:30:12Z",
    )


# STUB: AC21
def test_outcome_less_epic_renders_an_explicit_nothing(view):
    """An explicit statement that none is recorded, not a blank and not
    an omitted row."""
    row = _rows(view, None)[0]

    assert row["outcome"]["recorded"] is False
    assert row["outcome"]["statement"].strip() != ""


# STUB: AC22
def test_outcome_less_epic_also_renders_a_prompt(view):
    """The prompt names the location to write the outcome into."""
    row = _rows(view, None)[0]

    prompt = row["outcome"]["prompt"]
    assert prompt.strip() != ""
    assert "Outcome" in prompt
    assert "description" in prompt.lower()


# STUB: AC26
def test_no_score_grade_or_judgement_is_rendered(view):
    """The view reports the outcome, it does not assess it."""
    serialized = json.dumps(_rows(view, "Customers resolve a return."))

    for marker in ("score", "grade", "rating", "judgement", "judgment"):
        assert marker not in serialized.lower()
```

**Verification mode:** TDD for every criterion carrying a stub below, in
`packs/atlassian/tests/skills/jira-epic-outcome-view/`, with the fixture
carrying several outcome-less Epics. AC14 is the exception and is goal-based:
it defines what `verbatim` preserves — the ADF traversal and separator rules —
and is checked by reading the reader against that grammar, which is why the
disposition table records it as goal-based rather than TDD. Verbatim rendering is asserted here
against the reader that produces it; the end-to-end comparison of rendered
output against the source Jira text belongs to T6's installed-CLI pass, so no
criterion in this task carries two modes.

**Approach:**
- Completeness is asserted by removal. An omitted Epic raises no error
  anywhere, so a presence assertion passes while the set silently shrinks.

**Done when:** the removal fixture fails for every Epic in scope, and both
elicitation directions hold — stated words come back as paste-ready text, a
declined prompt yields none.

**Touches:** packs/atlassian/.apm/skills/jira-epic-outcome-view/**,
packs/atlassian/tests/skills/jira-epic-outcome-view/**

### T3: the skill writes nothing and couples to nothing

**Depends on:** T1, T2, T5

**Tests:**
- The two named roots — the invocation working directory tree and the
  installed pack tree — are byte-identical across a run with a populated cache
  and a stale `*.tmp` seeded, and the view composes `flow-metrics` only
  through the inert mode T4 ships. Verifies *leaves two named roots
  byte-identical* and *composes `flow-metrics` only through that mode*.
- Writes under `~/.agentbundle/` are attributed: the run is exercised with the
  broker seam recording its own writes, and any write not originating in the
  broker fails. Verifies *the broker's `~/.agentbundle/` is excluded from that
  comparison, and the view is asserted instead to issue no write there
  itself*. Excluding the root from the hash without this would let the view
  write there freely.
- The invoked-sibling set is derived from the sources, and `manifest.json`
  `deps.skills` is asserted equal to it; a skill invoked but undeclared fails.
  Verifies *the set of sibling skills the sources actually invoke is derived
  from the sources*, *the declaration is asserted equal to the derived set*,
  and *a sibling skill invoked by the sources but absent from `deps.skills`
  fails*.
- Every client in that derived set records read methods only, Jira write verbs
  included. Verifies *issues no Jira write verb* and *every client reached
  from that derived set issues read methods only*.
- The process table is unchanged across a run. Verifies *runs only when
  invoked and leaves no resident process*.
- The view returns its answer with no repository artifact present, and with
  every adopter-repository path denied. Verifies *invoked from a working
  directory that is not a repository* and *with every adopter-repository path
  denied*.
- The new skill's sources contain no machinery reference. Verifies *the
  skill's sources contain no reference to*.
- The new skill's sources carry no ADR number, acceptance criterion or
  repository-only path. The pack-wide sweep over every file T1-T6 ship is
  T6's, because T6 is the only task every other one precedes; running it here
  would let T2's and T6's own additions land after the check. Verifies the
  new skill's half of *no file this slice ships under `packs/` cites an ADR
  number*.
- The source-derived invocation set is walked transitively and no path
  reaches a pack-declared bridge, with a bridge-calling fixture that must
  fail. The traversal starts from what the sources invoke, not from
  `deps.skills`, so an undeclared hop into a bridge is still caught. Verifies
  *no path from that declared set reaches a skill the
  pack declares as a bridge*.

**Stubs:** no stub (goal-based check).

**Verification mode:** goal-based checks, run as one script per guarantee in
`packs/atlassian/tests/skills/jira-epic-outcome-view/`. Each is a check rather
than a unit test because each asserts an absence over a whole run.

**Approach:**
- The graph the outbound-mutation check enumerates is the same one the
  coupling walk traverses, so the two share a traversal rather than each
  defining a boundary.

**Done when:** the read-only, outbound, process and coupling checks are green,
and `guides/atlassian/` states what the view answers and what it does not.

**Touches:** packs/atlassian/.apm/skills/jira-epic-outcome-view/**,
packs/atlassian/tests/skills/jira-epic-outcome-view/**, guides/atlassian/**

### T4: `flow-metrics` gains a genuinely inert cache mode

**Depends on:** none

**Tests:**
- With `.context/flow-metrics/cache/` pre-seeded with a `*.tmp` older than an
  hour, a run under the new mode leaves that temp in place. Run under
  `--no-cache` instead, the same assertion fails. That pairing is the whole
  control: the stale-temp unlink is the one mutation the flag does not
  already suppress, so it is the only property whose control discriminates.
  Verifies *no cache operation of any kind occurs, stale-temp cleanup
  included*.
- The run performs no cache read and no cache write, asserted separately.
  `--no-cache` passes these too, so they are held as regression assertions
  rather than as controls — a mode that suppressed cleanup while
  reintroducing a read would satisfy the pairing above.
- From a working directory with no cache directory, the run creates none.
  `--no-cache` also creates none, for the same reason: the directory is made
  only on the write path.

**Stubs:**
- `test_inert_mode_does_not_invoke_the_stale_temp_cleanup` (AC39) — stub: true
- `test_no_cache_alone_still_invokes_the_cleanup` (AC39) — control, green today; not a stub
- `test_cleanup_is_a_noop_when_the_cache_directory_is_absent` (AC39) — control, green today; not a stub

Validated in PLAN from disposable scratch outside the repository test tree:
`python -m py_compile` clean; `pytest` gave **1 failed, 2 passed**. The red is
behavioural, not lexical: the failing test drives `main()` with the Jira
fetch substituted and the cleanup spied, then asserts the fetch was reached
and the cleanup never invoked. The `--no-cache` control passing is what proves
the assertion is not vacuous — the same run reaches the same fetch and does
invoke the cleanup. Every run is offline, so nothing depends on ambient
credentials. Earlier drafts asserted only that argparse accepted the flag,
then inferred suppression from a surviving file, then pinned an internal cache
seam a conforming implementation may skip, then pinned an exit code that a
credentialed machine would not produce. The disposable copy was removed.

Deferred to EXECUTE: the assertions that the mode also performs no cache read
and no cache write need a completed fetch, so they are recorded as deferred
assertions for the full test rather than stubbed here.

```python
# Stored and validated in PLAN's T4 Tests: subsection. The subject is loaded
# under a pack-and-skill-qualified module name via `spec_from_file_location`,
# never by putting `scripts/` on `sys.path` — the catalogue authoring standard
# forbids the latter because one bare name would then bind to whichever pack's
# directory landed first.
from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_FM_PKG = _PACK_ROOT / ".apm" / "skills" / "flow-metrics" / "scripts" / "flow_metrics"
_FM_NAME = "atlassian_flow_metrics"


@pytest.fixture(scope="module")
def fm():
    """Load `flow_metrics` under a unique pack-and-skill-qualified name."""
    spec = importlib.util.spec_from_file_location(
        _FM_NAME, _FM_PKG / "__init__.py", submodule_search_locations=[str(_FM_PKG)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fm_cache(fm):
    return importlib.import_module(f"{_FM_NAME}.cache")


def _seed_stale_temp(root: Path, fm_cache) -> Path:
    cache_dir = root / ".context" / "flow-metrics" / "cache"
    cache_dir.mkdir(parents=True)
    stale = cache_dir / "abc123.jsonl.999.tmp"
    stale.write_text("{}\n", encoding="utf-8", newline="\n")
    old = time.time() - (fm_cache.STALE_TMP_AGE_SECONDS + 60)
    os.utime(stale, (old, old))
    return stale


_SCOPE_ARGS = ["--project", "PROJ", "--from", "2026-01-01", "--to", "2026-01-31"]


def _stub_fetch(fm, monkeypatch) -> dict:
    """Substitute the Jira fetch so no test reaches the network.

    `packs/AGENTS.md` requires a seam in front of an external binary, and
    without one these runs would make real Jira calls on any credentialed
    machine — slow, non-deterministic, and dependent on someone's instance.
    The seam also gives the liveness signal directly: reaching it proves the
    run travelled past the whole cache section.
    """
    import importlib

    per_issue = importlib.import_module(f"{_FM_NAME}.per_issue")
    seen = {"fetched": 0}

    def fake_rows(*_args, **_kwargs):
        seen["fetched"] += 1
        return iter(())

    monkeypatch.setattr(per_issue, "iter_per_issue_rows", fake_rows)
    return seen


def _spy_cleanup(fm_cache, monkeypatch) -> dict:
    """Record whether the stale-temp cleanup was invoked.

    `flow_metrics` imports it from `.cache` inside the pipeline function, so
    the name resolves against the module object at call time and patching it
    here intercepts.
    """
    seen = {"cleanup": 0}
    monkeypatch.setattr(
        fm_cache, "cleanup_stale_tmps", lambda _dir: seen.__setitem__("cleanup", seen["cleanup"] + 1)
    )
    return seen


# STUB: AC39
def test_inert_mode_does_not_invoke_the_stale_temp_cleanup(fm, fm_cache, tmp_path, monkeypatch):
    """Observes the decision directly rather than inferring it from the
    filesystem, because an absent side effect cannot distinguish suppression
    from an execution that never arrived.

    Liveness is the substituted fetch being reached. That seam sits after the
    whole cache section, so reaching it proves the run did the normal work
    rather than returning early, while leaving an implementation free to
    bypass every cache operation — `cache_key` included. Pinning an internal
    cache seam would reject a conforming inert mode; pinning an exit code
    would fail on any machine with working Jira credentials, because
    `flow-metrics` inherits the ambient environment.

    Red three ways: today argparse rejects the flag; an implementation that
    accepts it and returns early never reaches the fetch; one that accepts it
    without suppressing the cleanup trips the spy.
    """
    monkeypatch.chdir(tmp_path)
    fetched = _stub_fetch(fm, monkeypatch)
    seen = _spy_cleanup(fm_cache, monkeypatch)

    try:
        fm.main([*_SCOPE_ARGS, "--inert-cache"])
    except SystemExit as exc:
        pytest.fail(f"--inert-cache was rejected by the parser (exit {exc.code})")

    assert fetched["fetched"] == 1, (
        "the run never reached the fetch, so it did not travel past the cache "
        "section and a suppressed cleanup here proves nothing"
    )
    assert seen["cleanup"] == 0, "inert mode must not invoke the stale-temp cleanup"


def test_no_cache_alone_still_invokes_the_cleanup(fm, fm_cache, tmp_path, monkeypatch):
    """The control that makes the assertion above falsifiable: `--no-cache`
    reaches the same fetch and still invokes the cleanup, which is the one
    mutation it does not suppress and the whole reason a separate mode is
    needed. Green today and must stay green."""
    monkeypatch.chdir(tmp_path)
    fetched = _stub_fetch(fm, monkeypatch)
    seen = _spy_cleanup(fm_cache, monkeypatch)

    fm.main([*_SCOPE_ARGS, "--no-cache"])

    assert fetched["fetched"] == 1
    assert seen["cleanup"] == 1, "--no-cache is expected to still run the cleanup"


def test_cleanup_is_a_noop_when_the_cache_directory_is_absent(fm_cache, tmp_path):
    """Pins the other half of the correction: a bypassed run does not
    materialise `.context/`, because the directory is created only on the
    write path. Guards against a fix that creates the directory to clean it."""
    absent = tmp_path / ".context" / "flow-metrics" / "cache"

    fm_cache.cleanup_stale_tmps(absent)

    assert not absent.exists()
```

**Verification mode:** TDD, in `packs/atlassian/tests/skills/flow-metrics/`
alongside that skill's existing suite, because the change is to `flow-metrics`
rather than to the view.

**Approach:**
- `cleanup_stale_tmps(cache_dir)` is called unconditionally at module
  entry, above the branch that consults `--no-cache`, against a
  `Path.cwd()`-relative `cache_dir`. The mode has to gate that call and the
  directory computation. Symbols and ordering are named rather than line
  numbers, because this task edits the file those numbers point into.
- `--no-cache` is narrower than it looks: it gates both the cache read and
  the cache-write tee, and the cache directory is created only inside that
  tee. A bypassed run therefore neither reads, writes, nor materialises
  `.context/` — it only unlinks stale temps from a directory that already
  exists. That single residual write is what forces the new mode, and an
  earlier draft of this plan overstated it.
- The change is additive and default-off: every existing caller keeps today's
  behaviour, which is what keeps this slice revertible.

**Done when:** the stale-temp assertion is green under the new mode and red
under `--no-cache`, the read, write and directory assertions are green,
`flow-metrics`' `SKILL.md` documents the mode, and its own suite still
passes.

**Touches:** packs/atlassian/.apm/skills/flow-metrics/**,
packs/atlassian/tests/skills/flow-metrics/**

### T5: `atlassian` declares its bridge skills

**Depends on:** none

**Tests:**
- The declaration is `[pack.metadata]` key `bridge-skills`;
  `agentbundle catalogue lint --root .` passes on the amended `pack.toml`;
  every declared name matches a skill directory in this pack; and every skill
  carrying the coupled machinery appears in the list. The last assertion is
  what stops a suffix-derived list passing while a coupled skill sits outside
  it. Verifies *declares the pack's bridge skills in `[pack.metadata]`*.
- This skill is absent from the declared list. Verifies *this skill is not
  among them*.

**Stubs:** no stub (goal-based check).

**Verification mode:** goal-based check. The catalogue lint proves only that
the table is accepted; `[pack.metadata]` is unconstrained by the schema, so
the lint cannot enforce the list's shape or membership. The artifact that
does is `packs/atlassian/tests/test_bridge_declaration.py`, asserting the key
is present and a list of unique strings, every name matches a skill directory
in this pack, every skill carrying the coupled machinery is named, and this
skill is not. Without it an empty list passes the lint.

**Approach:**
- The declaration goes in `[pack.metadata]`, the schema's open extension
  table — its own description records `additionalProperties` as intentionally
  unrestricted. Verified by adding the key and running the lint, which passes.
  No schema edit, no `agentbundle` release, and no compatibility break: every
  version shipped since the enriched pack manifest accepts arbitrary keys
  there. The pack is at `0.9.3`; `0.48.0` is `agentbundle`'s own version, and
  an earlier draft cited it here by mistake.
- A new top-level `[pack.bridges]` table was rejected for the opposite
  reason: the schema is closed under `pack`, so it reds with `CAT-L006`, and
  that verdict comes from the validator an adopter already has installed. No
  change made here could soften it for them.
- The shape is the minimum that carries D4: a list of skill names, each
  matching a skill directory in this pack, no duplicates, absent meaning no
  bridges. Anything richer decides something ADR-0126 owns.
- Membership is derived by inspecting which skills actually carry the coupled
  machinery, not by matching the `-refresh` and `-brief-intake` suffixes. D4
  is explicit that the naming convention is a convention and the declaration
  is the contract, so a suffix-derived list would restate the convention and
  miss a coupled skill named outside it.
- The open table buys compatibility at the cost of schema validation: nothing
  type-checks the list. The two membership assertions above are what replace
  that check.

**Done when:** the bridge list is declared as `[pack.metadata].bridge-skills`, names only
skills this pack ships, omits this skill, and `catalogue lint --deep` and
`catalogue verify` pass.

**Touches:** packs/atlassian/pack.toml, packs/atlassian/tests/test_bridge_declaration.py

### T6: the pack releases

**Depends on:** T1, T2, T3, T4, T5

**Tests:**
- `pack.toml` and `.claude-plugin/plugin.json` carry the same bumped minor
  version. Verifies *carry the same bumped version*.
- The eval harness covers the new skill. Verifies *the pack's eval harness
  covers the new skill*.
- `.claude-plugin/marketplace.json` carries the bumped version, and
  re-running `make build-self` leaves a zero diff. **Conflicting guidance,
  reported not worked around:** `packs/AGENTS.local.md` step 2 says to run
  `FORCE=1 make build-self`, while root `AGENTS.local.md` says never to pass
  `FORCE=1` from automation. A maintainer may force the regeneration by hand;
  this task's automated check must not, so it runs the unforced build and
  fails on a non-zero diff instead. Verifies
  *`marketplace.json` carries the bumped version* and *every generated output
  is regenerated by its build rather than edited*.
- The `docs/product/changelog.md` entry is free-standing at `##`, not nested
  under `[Unreleased]`, and carries a `### Highlights` subsection of
  outcome-led bullets. Verifies *the changelog entry carries its Highlights*.
  This slice adds a skill an adopter can run, so the answer to "does this
  change what a consumer of the pack can do?" is yes and the subsection is
  obligatory. `packs/AGENTS.local.md` sets that test, and nothing downstream
  makes the call: `/now/` is a pure byte parser, so an unwritten Highlights
  block is a release the public page never mentions.
- The installed CLI is invoked end-to-end against a real Jira scope, and the
  observed command, stdout, exit code and per-Epic rendering are recorded in
  `docs/specs/jira-epic-outcome-view/notes/manual-qa.md`, with the session
  scope stating what was exercised and what was not. Verifies *the installed
  CLI is exercised end-to-end through its documented happy path*.
- Every file under `packs/` created or changed by T1-T6 — the new skill,
  T4's `flow-metrics` edit, T5's `pack.toml` and T6's eval content — is
  scanned for an ADR number, an acceptance criterion or a repository-only
  path, and any hit fails. This lands here because T6 runs last. Verifies
  *no file this slice ships under `packs/` cites an ADR number*.
- `agentbundle catalogue lint --root . --deep` and
  `agentbundle catalogue verify --root .` pass. Verifies that criterion.

**Stubs:** no stub (goal-based check) for the release surfaces; `no stub
(manual QA)` for the installed-CLI happy path, which `work-loop` requires of
any artifact a user invokes directly and which no unit gate may stand in for.

**Verification mode:** mixed. **Visual / manual QA** for the installed-CLI
happy path: the artifact is invoked as an adopter would, and the assertion is
on the observed stdout, exit code and rendering — never on a passing unit
gate. Session boundary: one sitting against one real Jira scope, ending when
both Epic shapes have rendered; repeat use across two sittings is documented
as *not* exercised, because it is the parent's `to-validate` hook rather than
this slice's gate. Otherwise goal-based — the catalogue lint, the self-host
zero-diff re-run, and the eval harness run are the artifacts.

**Approach:**
- `packs/AGENTS.md` makes all four obligatory for a non-cosmetic pack change
  and sets the bump at minor for a new primitive. They land in one task
  because a partial release is what leaves a generated output stale.
- The generated output that moves for this pack is
  `.claude-plugin/marketplace.json`, which aggregates every
  `packs/*/.claude-plugin/plugin.json` and so tracks the version bump. This
  pack's skills are not projected into the repository's own `.claude/` or
  `.agents/` trees — those carry the self-hosted core packs — so a self-host
  zero-diff run would not have verified anything about `atlassian`.
- Release history goes to `docs/product/changelog.md` as a
  `## [atlassian][<version>] — <date>` entry. A pack keeps no `CHANGELOG.md`
  of its own.

**Done when:** both manifests match at the bumped version, the eval harness
covers the new skill, `marketplace.json` carries that version and
`make build-self` re-runs to a zero diff, the changelog carries a
free-standing `##` entry with its `### Highlights` bullets, and
`agentbundle catalogue lint --root . --deep` and
`agentbundle catalogue verify --root .` are green.

**Touches:** packs/atlassian/pack.toml,
packs/atlassian/.claude-plugin/plugin.json,
packs/atlassian/.apm/skills/jira-epic-outcome-view/evals/**,
docs/product/changelog.md, .claude-plugin/marketplace.json,
docs/specs/jira-epic-outcome-view/notes/manual-qa.md

The repository's own adapter trees are deliberately absent from that list.
`.claude/` and `.agents/` carry the self-hosted core packs, not `atlassian`,
and everything generated is written by its build rather than edited here.

## Rollout

No existing caller changes behaviour: the `jira` client is invoked
unmodified, `flow-metrics` gains a default-off mode that leaves its current
paths untouched, and the `pack.toml` addition is a declaration in a table the
schema already leaves open, so no validator anywhere changes behaviour. The
slice is revertible by deleting one skill directory, one declaration and one
default-off flag.

## Risks

- **The absent-outcome row gets dropped as noise.** Mitigated by asserting
  removal rather than presence.
- **A team never records an outcome.** Then the view degrades to the delivery
  half, which is what already ships — a weak product rather than a broken one.
  This is the parent's `to-validate` hook, not something this plan settles.
- **The composition drifts from its sources.** Mitigated by asserting the
  figures match `flow-metrics` rather than snapshotting expected numbers.

## Changelog

- 2026-09-25 — **spec approved** by eugenelim, lifecycle owner. Scope
  accepted at 57 acceptance criteria after fifteen cold adversarial review
  rounds. The basis: every round's findings adjudicated against repository
  and source evidence rather than adopted on authority; the composed skills'
  behaviour read from `flow-metrics`' own source rather than its
  documentation; and three structural generators of repeat findings closed by
  construction — criterion numbering anchored to text, the disposition ledger
  derived rather than hand-maintained, and the cache assertion observing the
  decision rather than inferring it.
- 2026-09-25 — **plan approved** by eugenelim, lifecycle owner. Implementation
  strategy accepted: six tasks, three carrying validated red stubs, one
  installed-CLI manual-QA pass. From this entry both documents are pinned in
  substance; a genuine error follows the controlled-amendment path and
  execution observations go to `notes/verification-ledger.md`.
- 2026-09-25 — **approval caveat, recorded rather than left implicit.** Round
  15's repairs were not themselves reviewed and round 16 was not run. Fifteen
  of fifteen rounds returned findings, so the base rate says defects remain.
  The owner approved on that basis; the closing rounds found defects in
  repairs and in bookkeeping rather than in scope, boundaries or the composed
  skills' behaviour.

- 2026-09-24 — plan drafted.
- 2026-09-24 — cold spec-mode review round 4; T4 added for the inert
  `flow-metrics` cache mode, T1 and T2 tests reconciled with the spec.
- 2026-09-24 — adversarial review round 5; T5 added for the bridge
  declaration, T6 for the pack release, task scopes narrowed to their own
  trees and the test root moved out of `.apm/`.
- 2026-09-25 — adversarial review round 15; two stubs reconciled so both can
  be green at once; the criterion identifiers in the task bullets re-derived
  from their markers after a two-stage shift double-applied to four of them;
  verbatim rendering given one owning gate; and the Jira fetch substituted so
  no test reaches the network, which also supplies the liveness signal
  directly.
- 2026-09-25 — adversarial review round 14; T4's liveness signal derived from
  the control run rather than a literal exit code, since `flow-metrics`
  inherits the ambient environment and a credentialed machine ends elsewhere;
  verbatim rendering's second mode removed from T2's declaration; and an
  unresolved parent chain given a defined caller-visible result — an
  unattributed group with its reason, exiting zero, rather than a silent drop
  or a withheld view.
- 2026-09-25 — adversarial review rounds 12 and 13; the parent's "no write of
  any kind" reconciled with the scratch write it forbade; T4's assertion moved
  off an internal cache seam onto the post-cache fetch, so a conforming inert
  mode that skips `cache_key` is no longer rejected; subtask-to-Epic resolution
  contracted through the Story rung with both `--include-subtasks` states
  pinned; verbatim rendering given one mode; and a `## Criterion disposition`
  table added as the binding, total and disjoint record.
- 2026-09-25 — adversarial review rounds 10 and 11; T4's reachability guard
  rebuilt twice — first isolated to its own directory after it was found to
  delete the file its own assertion needed, then made to compare the inert
  run's outcome against the control's so an early return cannot pass; the
  ledger re-derived from the plan's markers rather than maintained by hand;
  AC4 dropped as construction detail; T3 ordered after T2; the bridge
  traversal moved onto the source-derived set; and the installed CLI given the
  manual-QA record `work-loop` requires of a directly invoked artifact.
- 2026-09-24 — adversarial review round 9; throughput corrected to
  `flow-metrics`' own counting rule (delivered and not a subtask bucket), the
  two stub blocks reconciled onto one `build_epic_rows` contract, T4 guarded
  against a vacuous pass, every `# STUB:` marker renumbered against the
  current criteria, the state observations and `Outcome` grammar made
  determinate, and the answer-input boundary contracted as `--outcome`.
- 2026-09-24 — adversarial review round 8; `flow-metrics` emits no per-Epic
  breakdown, so the flow reading becomes one `--per-issue` run grouped here by
  the view's own parent-link read; the `--output` write that mode requires is
  disclosed and bounded; the single-snapshot claim is withdrawn for two stated
  moments; all three stubs reloaded under pack-qualified module names, T4's red
  made behavioural, and the `Outcome` block grammar pinned.
- 2026-09-24 — the view is a deterministic script, not a skill body; the
  composition drops `jira-team-status` for `jira` + `flow-metrics`; the outcome
  location is fixed to the Epic description's `Outcome` block; T1, T2 and T4
  carry validated red stubs.
- 2026-09-24 — adversarial review round 6; the `--no-cache` defect corrected
  to its true scope, the invocation boundary pinned to `manifest.json`
  `deps.skills`, T6 retargeted to `marketplace.json`, and the bridge
  declaration moved to `[pack.metadata]`, which removes the schema change.
