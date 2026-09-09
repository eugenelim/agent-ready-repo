# Plan: Cooling brief child scope closure

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** [`packs/AGENTS.md`](../../../packs/AGENTS.md) `:62-66` (`.apm/` is the source of truth; never edit adapter projections directly); [`packs/AGENTS.local.md`](../../../packs/AGENTS.local.md) `:21-24` (the `Engine-Change-RFC:` trailer and its non-engine carve-out) and `:29` (`FORCE=1 make build-self`); [`docs/CONVENTIONS.md`](../../CONVENTIONS.md) `:111` (Frozen), `:119-121` (the frozen unit is the spec directory), `:154-155` (the licensed Status-pointer form), `:160` (rule 1 — say which part), `:445-446` (cite upward, never downward; ADRs do not link to specs). Analogous implementation: Wave 6's attributed-child mechanism — `_brief_child_spec_states` feeding `briefs_with_cooled_children` into the `brief_scope_unknown` assignment in `_dependency_is_satisfied`, and into the `scope_unevaluable=entry.path in briefs_with_cooled_children` argument — with its fixtures in `tests/roster/test_status_projection_and_context_exclusion.py`. Cited by symbol throughout: Wave 7c's one-line `_COOLING_PAIRS` addition shifted every line literal this field previously carried, and a frozen plan cannot hold a line number. Named uncertainties: `_brief_child_spec_states` returns a 2-tuple and gains a third member, with exactly one call site (`brief_child_states, briefs_with_cooled_children = _brief_child_spec_states(`); and that suite's helpers need extending for four criteria, verified against the shipped signatures: `_brief_workspace` writes exactly one child entry into one collection and takes only `child_collection`, `child_source_parent`, `brief_collection` and `include_dependant`, so *The answer is per entry* (two children in `work.shipped`), *Unestablished scope does not refuse a non-brief dependency* (a second queued spec whose `needs` is `kind = "spec"`) and *An attributed cooled child still suppresses its parent's violation* (a second child in `work.queue`) each need it; `_cool_child` hard-codes `delivery_id="child"`, the locator `docs/specs/child/spec.md` and the filename `child.json`, so *The answer is per entry* and *A cooled brief is satisfied ahead of the refusal* each need a second record. Every other parent-scope criterion needs neither — `_brief_body(status=…)`, `_child_spec(status=…, brief=…)` and `include_dependant=False` already express their axes. This is the single home for that list.

## Approach

Widen one existing decision from two answers to three, and route the new answer
along one rail rather than two.

`_brief_child_spec_states` is the only place a cooled child's parent is
consulted. It reads `_normalized_optional_artifact_value(entry.source.parent)`,
which collapses a declared `"none"` and an absent key to the same `None`. The
change reads the raw attribute alongside the normalized one, resolves a declared
value against the brief memberships already parsed from `workspace.toml`, and
returns the entries whose scope is unestablished as a third member.

Only the dependency rail carries that answer. `scope_unevaluable` keeps its
shipped per-brief value untouched, so this delivery adds a finding and a refusal
and removes nothing. Probes 9 and 12 establish why: a repository-wide value in
that argument erases a real `impossible_transition` in the `executing` and
`cancelled` arms, and suppression buys no dispatch change in exchange.

## Constraints

Mechanism the criteria cannot state. Everything observable lives in `spec.md`.

- **Emit from `run_canonical_reconciliation`, never `_structural_findings`.** A
  finding raised in `_structural_findings` reaches
  `structurally_blocked_paths.add(membership.entry.path)`, and the
  `if dep.path in structurally_blocked_paths` guard at the top of
  `_dependency_is_satisfied` refuses every dependency on a blocked path before
  any kind test.
- **Widen the `brief_scope_unknown` assignment; leave the `if brief_scope_unknown`
  refusal alone.** The assignment computes the boolean and the refusal consumes
  it, with the three precedences the spec's *Always do* rail names in between —
  a `cross-repo` receipt, the cooled brief's own lifecycle record
  (`if cooled_dependency`), and the metadata-safety finding
  (`return False, safety_finding`). A `kind` mismatch also returns ahead of the
  refusal, so this is the set of cooling-relevant precedences rather than every
  early return. Widening the computation inherits each of them unchanged, which
  is the intended order. *A cooled brief is satisfied ahead of the refusal* rests
  on the second: `if cooled_dependency: return True, None` is the only one that
  returns `True`, and that criterion asserts the dependant is present in
  `canonical.ready`. The metadata-safety precedence returns `False`, so it cannot
  carry that criterion.
- **Cite the engine by symbol, not by line.** Every line literal this plan
  carried against `workspace_status_engine.py` shifted when Wave 7c added one
  entry to `_COOLING_PAIRS`. A frozen plan cannot hold a line number, so each
  site above names its symbol and a distinguishing token instead.
- `_brief_child_spec_states` returning a 3-tuple is an internal signature change;
  this module is its only caller.
- The finding code and both documentation rows land in one commit;
  `test_t4_repair_determinism_projection_and_release_surface` reads both homes
  over `set(engine._FINDING_NEXT_ACTIONS)`, and that node also asserts the
  release version, so it can only pass once T4 has run.
- `plan.md` is hash-frozen from approval. Mutation observations go to
  `notes/mutation-proofs.md`.
- **Two commits, two questions, both read locally.** *Did this delivery move the
  release surface?* is answered against the merge base,
  `git merge-base HEAD origin/main` — the comparison the criterion makes, and the
  one that catches a bump that agrees with its source but was never mine. *Does
  the bump collide?* is answered against the remote-tracking tip,
  `git show origin/main:packs/core/pack.toml`. Both are re-read in the same
  command as the commit, and **neither is written down here**. This plan freezes
  at approval and the floor has already moved twice during review — `2.25.2` at
  the reviewed base, `2.25.3` after one merge, `2.25.4` fifteen commits later —
  so any literal in a frozen plan is wrong by the time it is read. The bump is
  whatever exceeds the derived floor when T4 runs. A stale remote-tracking ref
  makes the collision check best-effort, so it is a guard, not a proof.

## Construction tests

New suite: `tests/roster/test_cooling_brief_child_scope_closure.py`, in
`tests/roster/` rather than under `packs/core/tests/` because it reads
repository-level contracts that `tools/lint-pack-test-boundary.py` refuses inside
a pack test. It loads the engine from source by path, so a stale editable install
cannot satisfy it, and imports the Wave 6 suite's fixture helpers rather than
copying them. Each case builds its own root under `tmp_path`.

## Durable-output map

| Spec durable output | Task | Evidence handed to close-work |
| --- | --- | --- |
| Decision rationale (ADR-0106, `notes/ask-first-review.md`) | T0 | *The pointer takes the licensed form* |
| Current architecture (the frozen spec's Status token) | T0, T2 | *The frozen body is otherwise unchanged*; *Both sites pinning the edited file carry its new digest*; *The three superseded Wave 6 cases are updated, not deleted* |
| User documentation (both adopter guide surfaces) | T1 | *The adopter closeout procedure states the precondition*; *The `parent` field's reference entry states the cooling interaction* |
| Interface compatibility (both documentation homes) | T1 | *The code is documented where the gate looks*; *The next action says when the empty answer is correct* |
| Reusable learning (`notes/probes.md`) | written at PLAN | Every probe section in `notes/probes.md`, each with its printed output |
| Release history (changelog `[core]` heading) | T4 | *This delivery moved the release surface* |

## Design (LLD)

### Design decisions

Each rests on a probe rather than an argument.

- **The read-free link is `source.parent`, and its third state is raw
  presence.** Probes 1 and 2: the parsed entry keeps the raw string, and the
  published schema already admits `none`. The cut-before-adding ladder stops at
  rung 3.
- **A declared value must resolve to a brief membership.** Probe 7:
  `Brief-1.md` against a registered `brief-1.md` leaves the dependant
  dispatchable with an empty findings list. Membership resolution reads
  `workspace.toml` only.
- **The emission site is settled.** Probe 8: the `_structural_findings` route
  refuses a direct spec dependant.
- **Suppression is left alone.** Probes 9 and 12, as above.

### State & control flow

The cooled arm of `_brief_child_spec_states` gains a third branch on raw presence
and membership resolution. `run_canonical_reconciliation` turns the returned list
into one finding per path and one repository-wide boolean, and passes that
boolean only to `_dependency_is_satisfied`.

The finding's `path` is always the child's entry path, for both unknown causes.
Nothing in the emitted finding distinguishes them — `detail` reaches no consumer
(probe 10) and `next_action` is keyed one per code — so *The next action says when the empty answer is correct*'s next action names
both repairs, and the declared value is readable in the entry the finding
names.

### Failure, edge cases & resilience

The refusal presupposes a resolved cooled set. When cooling cannot be resolved
no entry is cooled and the new branch is unreachable — including for a `Cooling`
record whose artifact has been deleted, which `_cooled_locators` drops before any
parent is consulted. This plan's *Constraints* are the stated home for both the
presupposition and that residual; neither is changed here, and neither appears in
the spec, whose criteria state outcomes over resolvable fixtures.

Measured at base `9ab376dcc`: `docs/lifecycle/` holds a `README.md` and no
records, so nothing in this repository is cooled and the refusal has no live
subject (`notes/probes.md` probe 15). Failing closed therefore cannot block a
dependency that resolves today, and every Group 1 criterion is carried by a
constructed fixture rather than by repository state.

## Tasks

### T0: Record the supersession before anything depends on it

**Depends on:** none

**Touches:** docs/adr/0106-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md, docs/adr/README.md, docs/specs/status-projection-and-context-exclusion/spec.md, docs/specs/cooling-scope-closure/spec.md, tests/roster/test_cooling_scope_closure.py

**Tests:** goal-based, no stub (goal-based). *The pointer takes the licensed form* and *The frozen body is otherwise unchanged*. *The pointer takes the licensed form* pins the pointer's wording and *The frozen body is otherwise unchanged* the body's integrity; they fail for different reasons and take different repairs. The digest moves in two places: the dict inside `test_ac23_pinned_files_are_byte_unchanged` in `tests/roster/test_cooling_scope_closure.py`, and `cooling-scope-closure`'s AC23 table row naming `docs/specs/status-projection-and-context-exclusion/spec.md`. Both are found by searching for `2cac21ca`, which is what T0's Done-when asserts is gone. The suite hashes only its own dict, so the prose copy has no oracle and needs an explicit check.

**Approach:**
- Re-check that `0106` is still the next free ADR ordinal immediately before committing; ordinals do not hold across parallel sessions. This already fired once: `0104` was taken upstream by an unrelated ADR while this delivery was in review, and `0105` is now merged as `retained-lifecycle-records-may-terminate-as-reclassified`, so the gap at `0105` is a landed fact rather than a reservation.
- Write the Status parenthetical in the `docs/CONVENTIONS.md:154-155` form, changing no other line.
- Recompute the digest and update both sites.
- Add the `docs/adr/README.md` index row.

**Done when:** the frozen spec's Status line matches the licensed form and names ADR-0106; `git diff <the base T0 started from> -- <that file>` shows exactly one changed line, taken against a named revision rather than the index, since T0 commits within the task; both digest sites carry the recomputed value and neither retains `2cac21ca`; `docs/adr/README.md` carries an ADR-0106 row; and `tests/roster/test_cooling_scope_closure.py` passes.

### T1: Resolve parent scope, fail closed on the unestablished answer, document the code

**Depends on:** none

This field is machine-parsed for task tokens, so the reasoning sits here rather
than inside it: T1 consumes nothing T0 produces and touches no frozen spec. Only
the ADR-0106 assertion messages need T0, and the task that rewrites them reaches
it anyway. Rollout still sequences T0 first, for the reason Rollout states.

**Touches:** packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py, packs/core/.apm/skills/workspace-status/SKILL.md, guides/core/reference/workspace-toml-schema.md, guides/core/how-to/close-and-disposition-work.md, tests/roster/test_cooling_brief_child_scope_closure.py, tests/roster/test_status_projection_and_context_exclusion.py

**Tests:** mixed — TDD for the read-free parent scope criteria (the stub below), goal-based for the two documentation criteria. The new suite covers the read-free parent scope criteria, and also *The next action says when the empty answer is correct*'s two documentation halves — the shipped gate — `assert reason` and `assert action` inside `test_t4_repair_determinism_projection_and_release_surface` — asserts only that each row's reason and action are non-empty and never reads a substring, so the literal needs its own assertion in the new suite over both rows and over `_FINDING_NEXT_ACTIONS`. Without it *The code is documented where the gate looks* stays presence-only, which is what *The next action says when the empty answer is correct* exists to prevent. *The code is documented where the gate looks* gets its assertion in **the new suite**, not from the projection suite. Measured: the shipped assertion `set(documented_findings) >= finding_codes` lives inside `test_t4_repair_determinism_projection_and_release_surface`, a single 312-line node that in the same body asserts repair determinism and the release version — so it cannot pass until T4 has moved the version, and there is no narrower node to select. The `_data/` and `.claude/` byte-equality assertions are separate narrower nodes in the same file; they are T4's for the projection reason, not this one. `pytest -k` against a substring of the assertion collects nothing and **exits 0**, so a selector is not a usable oracle either. T1 therefore asserts documentation coverage itself, over both rows and `_FINDING_NEXT_ACTIONS`, and that whole projection node is run in T4. It also owns the two adopter-documentation criteria, *The adopter closeout procedure states the precondition* and *The `parent` field's reference entry states the cooling interaction*, whose literals are checked in the same suite as the next action's. The helper extensions this task owns are the ones the Repository-anchors field enumerates; it is the single home for that list, and *The three superseded Wave 6 cases are updated, not deleted*'s merge-base basis is what keeps those edits visible at T2. Mutation proofs for the refusal, the finding, and the two `path` cases go to `notes/mutation-proofs.md`.

**Compilable red contract-surface assertion** (`stub: true`) — materialize
unchanged, then fill the remaining cases.

**PLAN-time validation result.** Validated from disposable scratch at base
`9ab376dcc`, outside the repository test tree: `python3 -m py_compile` succeeds,
and `python3 -m pytest -q` reports `4 failed in 0.48s`. Each red lands on the
assertion the criterion is about, not on collection or import:

| Case | Criterion | Observed failure |
| --- | --- | --- |
| `test_undeclared_parent_on_a_cooled_entry_is_named` | *An absent parent on a cooled entry is named* | `assert 0 == 1` — no finding emitted |
| `test_undeclared_parent_refuses_a_brief_dependency` | *Unestablished scope refuses a brief dependency* | `assert 'docs/specs/dependant/spec.md' not in {'docs/specs/dependant/spec.md'}` — the dependant still dispatches |
| `test_an_unresolvable_declared_parent_is_unknown_scope` | *A declared parent resolving to no membership is unestablished* | `assert 0 == 1` — no finding emitted |
| `test_the_parent_is_read_from_the_entry_not_the_body` | *The parent is read from the entry, never the body* | `assert 0 == 1` — no finding emitted |

The second case fails at its refusal assertion and never reaches its control, so
the control is not a co-failure. It is also not yet discriminating: with nothing
implemented both arms dispatch, so the control acquires its power only once the
refusal exists. That is the state a PLAN-time red should be in — the refusal
assertion is what must flip, and the control is what must not.

```python
"""RFC-0096 Wave 7b — read-free parent scope for a cooled child."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
sys.path.insert(0, str(ROOT / "tests/roster"))
import test_status_projection_and_context_exclusion as wave6  # noqa: E402

BRIEF_PATH = wave6.BRIEF_PATH
CHILD_PATH = "docs/specs/child/spec.md"
DEPENDANT_PATH = "docs/specs/dependant/spec.md"


@pytest.fixture()
def engine():
    """Load the source engine, never an installed projection."""
    spec = importlib.util.spec_from_file_location("wave7b_engine", ENGINE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def _fixture(root, engine, *, parent, body_brief="none", cool=True,
             include_dependant=True):
    """Build one brief/child/dependant tree and reconcile it.

    `parent` is the raw `source.parent` for the child entry, or None to omit the
    key — the distinction under test. `body_brief` is the child's body-declared
    link, which a read-free implementation must never consult.
    """
    root.mkdir(parents=True, exist_ok=True)
    wave6._brief_body(root, status="Shipped")
    wave6._child_spec(root, status="Shipped", brief=body_brief)
    # `_child_spec` writes no sibling plan; every fixture in spec.md pins one, and
    # `_append_plan_findings` runs after the cooled early return, so an uncooled
    # arm would draw `missing_plan` and falsify its criterion. Supplied here rather
    # than by extending the Wave 6 helper, which a criterion bounds.
    (root / "docs/specs/child/plan.md").write_text("# Plan\n\n- **Status:** Done\n")
    if include_dependant:
        wave6._spec(root, "dependant", status="Approved", brief="none")
    wave6._brief_workspace(
        root,
        child_collection="shipped",
        child_source_parent=parent,
        brief_collection="shipped",
        include_dependant=include_dependant,
    )
    if cool:
        wave6._cool_child(root)
    return wave6._reconcile_canonical(root, engine)


def _ready(result):
    return {e.entry.path for e in result.evaluations if e.dispatchable}


def _codes(result, code):
    return [f for f in result.findings if f.code == code]


def test_undeclared_parent_on_a_cooled_entry_is_named(tmp_path, engine) -> None:
    """*An absent parent on a cooled entry is named*: the entry to repair is named, not merely refused."""
    result = _fixture(tmp_path / "undeclared", engine, parent=None)
    found = _codes(result, "cooled_child_scope_unknown")
    assert len(found) == 1
    assert found[0].path == CHILD_PATH


def test_undeclared_parent_refuses_a_brief_dependency(tmp_path, engine) -> None:
    """*Unestablished scope refuses a brief dependency*: fail closed, with a control proving the refusal is escapable."""
    unknown = _fixture(tmp_path / "unknown", engine, parent=None)
    assert DEPENDANT_PATH not in _ready(unknown)
    assert any(
        f.code == "unsatisfied_dependency" and f.path == BRIEF_PATH
        for f in unknown.findings
    )

    declared = _fixture(tmp_path / "declared", engine, parent="none")
    assert DEPENDANT_PATH in _ready(declared), (
        "control never dispatched; the refusal above proves nothing"
    )
    assert not _codes(declared, "cooled_child_scope_unknown")


def test_an_unresolvable_declared_parent_is_unknown_scope(tmp_path, engine) -> None:
    """*A declared parent resolving to no membership is unestablished*: a case variant is unknown scope, named on the child entry."""
    result = _fixture(
        tmp_path / "variant", engine, parent="docs/product/briefs/Brief-1.md"
    )
    found = _codes(result, "cooled_child_scope_unknown")
    assert len(found) == 1
    assert found[0].path == CHILD_PATH


def test_the_parent_is_read_from_the_entry_not_the_body(tmp_path, engine) -> None:
    """*The parent is read from the entry, never the body*: the criterion a body-reading implementation fails.

    No `kind = "brief"` dependant is present, so the only observable is the
    finding itself — an implementation that opened the body would attribute the
    brief and emit nothing.
    """
    result = _fixture(
        tmp_path / "bodyonly",
        engine,
        parent=None,
        body_brief=BRIEF_PATH,
        include_dependant=False,
    )
    found = _codes(result, "cooled_child_scope_unknown")
    assert len(found) == 1
    assert found[0].path == CHILD_PATH
```

**Approach:**
- Keep the normalized value for attribution; resolve it against the brief memberships; collect unestablished entries as a third return member.
- Emit one finding per collected entry from `run_canonical_reconciliation`, with the `path` rule from § *State & control flow*.
- Add the disjunct to the `brief_scope_unknown` assignment. Leave the `scope_unevaluable` argument alone.
- Register the code in `_FINDING_NEXT_ACTIONS` with a next action containing the *The next action says when the empty answer is correct* literal, and add the matching row to both documentation homes in this task. Keep the next action in family: the 25 shipped values run 32-79 characters, so the register-repair explanation belongs in the two prose rows rather than in the string. Nothing in the emitted finding distinguishes the two unknown causes — the `path` is the child's for both and `detail` reaches no consumer — so *The code is documented where the gate looks*'s next action has to name both repairs.
- Replace the two residual comments inside `_brief_child_spec_states` with what the code now does, and correct the `brief_queue.shipped` arm's claim in `_brief_child_scope_is_valid` that a coverage lint reads the brief's Spec map — probe 6 measured that no such lint exists.

**Done when:** `python3 -m pytest tests/roster/test_cooling_brief_child_scope_closure.py -q` passes and its report names a non-zero collected count; and `notes/mutation-proofs.md` records an observed red for each new refusal, the finding, and both `path` cases. `test_workspace_status_projection.py` is deliberately **not** run here — its documentation assertion is welded into a node that also asserts the projections and the release version, both of which T4 produces.

### T2: Update the three superseded Wave 6 cases

**Depends on:** T1

**Touches:** tests/roster/test_status_projection_and_context_exclusion.py

**Tests:** goal-based, no stub (goal-based). *The three superseded Wave 6 cases are updated, not deleted*. Its merge-base basis is what makes T1's helper edit visible here rather than reading as clean.

**Approach:**
- Flip each of the three cases to the behaviour ADR-0106 records, keeping each function's name and its role as the control for the same observable.
- Keep the third case's ini-003 spec undeclared and cooled. Its own docstring records that there is no initiative filter and that its killing mutation is the behaviour this delivery ships, so re-declaring that entry would restore a premise the docstring refutes. Assert instead that the floor crosses initiative boundaries.
- Rewrite both copies of the assertion message `the residual is closed — update AC59 and remove the Follow-ons row` to point at ADR-0106; as written they instruct an edit the spec's Boundaries forbid.

**Done when:** all three functions still exist, none carries the string `the residual is closed`, and `python3 -m pytest tests/roster/test_status_projection_and_context_exclusion.py -q` passes.

### T3: Append the eval case

**Depends on:** T1

**Touches:** packs/core/.apm/skills/workspace-status/evals/evals.json, packs/core/.apm/skills/workspace-status/evals/files/cooled-child-scope-unknown/ (the fixture tree the case reconciles: `workspace.toml`, the cooled child's `spec.md` and `plan.md`, and its lifecycle record)

**Tests:** goal-based, no stub (goal-based). *The eval harness names the code* and *The eval ids stay distinct*. Id uniqueness is the load-bearing half.

**Approach:** append one eval whose `id` is derived from the file at execution time as one past its current maximum. Do not name an id here: `id: 10` was free when this plan was drafted and is now taken by a `cooled-path-collision` case in this same file, which would have failed *The eval ids stay distinct* on merge. All nine shipped cases carry a `files` array and `skill_spec_lint.py` raises CAT-S005 for an entry that does not exist, so this case ships its own fixture tree under `evals/files/cooled-child-scope-unknown/`.

**Done when:** the file parses, its `evals` ids are distinct, the new case names the code, and every path in its `files` array exists.

### T4: Register the work, regenerate the projections, move the release surface

**Depends on:** T0, T1, T2, T3

**Touches:** workspace.toml, .claude/skills/workspace-status/scripts/workspace_status_engine.py, .agents/skills/workspace-status/scripts/workspace_status_engine.py, packages/agentbundle/agentbundle/_data/workspace_status_engine.py, .claude/skills/workspace-status/SKILL.md, .agents/skills/workspace-status/SKILL.md, .claude/skills/workspace-status/evals/evals.json, .agents/skills/workspace-status/evals/evals.json, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md, docs/specs/README.md

**Tests:** goal-based, no stub (goal-based). *Every projection matches its source*, *This delivery moved the release surface* and *The shipped command emits the finding*. Runs last: a projection regenerated before the final engine byte is stale, and the projection byte-equality nodes T1 defers are asserted here.

**Approach:**
- Add exactly two `workspace.toml` lines: the `[work]` entry for this spec **into `shipped`**, and the `[backlog].open` entry whose `path` is `docs/specs/cooling-brief-child-scope-closure/notes/follow-ons.md`. The collection is not a free choice — the engine raises `impossible_transition` ("queue spec status") for a `work.queue` spec whose Status is `Implementing` or `Shipped`, that code is zero-tolerance over the real `workspace.toml`, and this PR ends with the spec at `Shipped`. Do not touch the cooled cross-repo deferral entry that Wave 7a-ii deliberately left stale.
- Run `FORCE=1 make build-self`.
- Add the *The shipped command emits the finding* assertion to the new suite, driving `workspace_status.py reconcile` as a subprocess under `sys.executable` from inside the checkout against the **Absent** fixture, and asserting exit 0 plus the code in the parsed stdout. It lands in T4 rather than T1 because the script it invokes is a projection T4 regenerates.
- Decide the `Highlights` disposition in the same step as the changelog entry, as `packs/AGENTS.local.md` requires. This delivery adds a refusal code and a fail-closed dependency answer a pack consumer can observe, so the expected answer is yes and the outcome-led bullets are drafted under `### Highlights`. If the answer is no, record that verdict and its reason in the PR's *What did you not change that you considered?* answer. Nothing downstream makes this call: the `/now/` projection is a pure parser over the file's bytes.
- Carry `Engine-Change-RFC: 0096` on the commit that touches `packages/agentbundle/`. `tools/lint-catalogue-curation-guard.py` carves out only `build/recipes/` and any `/tests/` path, so `_data/workspace_status_engine.py` is protected with no exemption, and the guard reads commit messages over `origin/main...HEAD` — it cannot see an uncommitted tree, so this is a step on the commit, not a check afterwards.
- Re-derive both version answers immediately before committing, per § *Constraints*: the floor from `git merge-base HEAD origin/main`, the collision check from `git show origin/main:packs/core/pack.toml`.
- After any merge of main, re-read both added `workspace.toml` blocks and assert they survived, **and** assert this delivery's `[core]` heading is still topmost — `_product_release_heading_version` takes the *first* matching heading, and a concurrent `[core]` release is expected.

**Done when:** the projections are byte-equal to source; the three release surfaces carry one identical version above the merge base's; `workspace.toml`'s `[work].shipped` carries this spec and `[backlog].open` carries an entry whose `path` is `docs/specs/cooling-brief-child-scope-closure/notes/follow-ons.md` and that path resolves; `docs/specs/README.md` carries a row for this spec, which `new-spec` step 8 requires and no gate checks; the changelog's topmost `[core]` heading is this delivery's and its `Highlights` disposition is recorded either way; the commit touching `packages/agentbundle/` carries `Engine-Change-RFC: 0096`; `python3 -m pytest tests/roster/ -q` passes, which is the only invocation that collects the three roster suites this delivery changes — `SKIP_SAST=1 make build-check`'s chain runs four targeted pytest modules and no `tests/` path, so it is not their oracle; and `SKIP_SAST=1 make build-check` passes against a clean `build/` and `dist/`.

`AGENTS.md`'s command list also offers CI dispatch across `build-check.yml`, `test-corpus.yml`, `test-roster.yml` and `pages.yml`, which it marks *partial evidence, never required*. Those runs need a push, so they are the reviewer's evidence rather than this task's gate; `.github/workflows/test-roster.yml` runs `python -m pytest tests/roster/ -q -rs -n auto --dist loadfile` and is the remote mirror of the local invocation above.

## Rollout

One PR, no flag. The behaviour is unreachable on this checkout — `docs/lifecycle/`
holds no records — so it activates when an artifact first cools. Revert is the
commit; no persisted state is written or migrated. T0 first, because the ADR
licenses every later change to the frozen spec; T4 last, so the projections and
release surface reflect final engine bytes.

## Risks

- **Two sessions converge on one digest table.** This delivery moves `cooling-scope-closure`'s AC23 row 3 and Wave 7c has merged, moving four other rows of the same table — `cooling.py`, `delivery-lifecycle-record.schema.json`, and both `thirty-day-cooling-and-retirement` files. `auto-mechanical-chores-run-21` is **discharged**: it merged, so its AC29 rewording of `docs/specs/cooling-scope-closure/spec.md` is inherited and its changes are not a coordination risk. Verified after the fast-forward to `9ab376dcc`, which is both `HEAD` and `git merge-base HEAD origin/main`: the AC23 digest row and the test pin in `tests/roster/test_cooling_scope_closure.py` both still carry `2cac21ca`. Cited by content rather than line, because Wave 7c's merge moved both. Mitigation: re-read the row after any further merge of main.
- **Wave 7c's `_COOLING_PAIRS` edit is a semantic dependency, not just a textual one.** Every parent-scope fixture reaches the new branch only because `("cool-30-days", "Cooling")` is in `_COOLING_PAIRS` — the frozenset Wave 7c added to. Line-disjointness is a merge property and does not protect the premise: if that pair set changes shape, the cooled set changes and every criterion's input changes with it. Re-check the pair set after any merge of their work, not just the diff. **Discharged as of `9ab376dcc`:** their merge added `("retain-exception", "Reclassified")`, taking the set to four pairs, and moved the suite's own `COOLING_PAIRS` mirror in step, so `assert frozenset(COOLING_PAIRS) == engine._COOLING_PAIRS` holds. Probe 15 re-derived the corpus and the gap's population against the new set: 118 spec entries, 101 omitting `source.parent`, and no cooled artifact at all, so no criterion's input changed.
- **A concurrent session moves the core version, repeatedly.** The merge base has carried 2.24.0, 2.24.1, 2.24.3, 2.25.2, 2.25.3 and 2.25.4 across this delivery's review, the last two within one day. No target is named here for that reason; § *Constraints* carries the derivation. *This delivery moved the release surface*'s floor is therefore whatever `packs/core/pack.toml` reads at the merge base when T4 runs, and this delivery must exceed it. *This delivery moved the release surface* compares against the merge base rather than a literal, so a further bump arriving from main moves the floor with it and cannot satisfy the criterion on its own.
- **ADR-0106's ordinal is taken by a parallel session.** Re-check immediately before committing.

## Changelog

- 2026-09-03 — Drafted. Scope is the mechanism half of RFC-0096 Wave 7b per its
  2026-09-03 Errata. The portable classification contract that erratum withdraws
  is not in scope, and `rfc0096-wave7b-historical-classification` is closed as
  withdrawn.
- 2026-09-04 — Approach settled on three points, each resting on a probe rather
  than an argument: the read-free link is `source.parent`'s raw value (probes 1
  and 2); a declared value must resolve to a brief membership (probe 7); and the
  emission site must not populate `structurally_blocked_paths` (probe 8).
  Suppression is left exactly as shipped, because a repository-wide value in
  that argument erases real violations (probe 9) and buys no dispatch change
  (probe 12).
- 2026-09-04 — Criteria are transcribed from probe 14's matrix, which pins all
  seven fixture axes and records its own construction. The engine slug retag is
  out of scope; `notes/owner-decisions.md` holds that decision.
- 2026-09-08 — Rebased onto Wave 7c's merge (`9ab376dcc`) and repaired against a
  dedicated plan review. Engine sites are cited by symbol rather than line, since
  Wave 7c's one-line `_COOLING_PAIRS` addition shifted every literal this plan
  carried. T1's oracle moved into the new suite: the shipped documentation
  assertion is welded into a 312-line node that also asserts the projections and
  the release version, and a `pytest -k` selector against it collects nothing and
  exits 0. T4 now names the `[work]` collection, the `Engine-Change-RFC` trailer,
  the `Highlights` disposition, the roster invocation, and the topmost-heading
  re-read. The stub carries its PLAN-time validation result.
