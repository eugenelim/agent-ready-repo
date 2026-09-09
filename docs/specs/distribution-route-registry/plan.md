# Plan: Distribution route registry

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `contracts/distribution-routes.toml` (read-only input);
  `build/main.py:1238-1345` (`_resolve_distribution_route`, the grounded seam);
  the bundled recipe TOMLs under `agentbundle/build/recipes/`, each declaring its
  `route` inside a `[recipe]` table; tests at
  `packages/agentbundle/tests/build_pipeline/test_distribution_route_{resolution,contract,golden}.py`;
  `notes/agent-plugin-surface-gaps.md` for the surface audit this is measured against.
  Named uncertainty: the shape of the contract-derived lookup is a build-time choice —
  this plan fixes its required outcome and leaves its form to implementation.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting` or
> `Executing`. When it changes substantially, note why in the changelog.

## Approach

Fourteen of fifteen route-consuming surfaces hand-maintain a route list, and every one
was written before the portable route existed. Replacing each list with a read of the
contract is what completes `agent-plugin` and what prevents the next route repeating
the omission.

The schema stays closed, so this slice proves genericity by *absence* — no shared code
decides by route name — and by *agreement* — every surface's route set equals the
declared set. Neither needs a synthetic route, which the closed schema could not admit
anyway. Because the route set is fixed at three, handler registration can be explicit;
dynamic discovery would be unused machinery and a trust boundary this slice does not
need. Opening the set, and the discovery it then requires, is the sibling slice.

Order. Two oracles come first and nothing may precede them: the branch inventory and
the Agent Plugin golden, both measured against the unmodified tree. Then the
contract-derived lookup, then the surfaces that consume it, then the closing guards.

Several tasks edit `build/main.py`; those are serialized. Each task that authors tests
names its own file so parallel work cannot collide.

## Constraints

- [RFC-0092](../../rfc/0092-first-class-distribution-routes.md) D1, D3, D4, D6 and its
  2026-09-03 erratum.
- [ADR-0090](../../adr/0090-distribution-routes-separate-from-runtime-adapters.md).
- Shipped [`distribution-route-contract`](../distribution-route-contract/spec.md) and
  [`portable-agent-plugin-projection`](../portable-agent-plugin-projection/spec.md) —
  their tests are AC5's oracle and must run unmodified.
- `contracts/README.md`, `tools/catalogue/check_contract_parity.py`.
- `packages/AGENTS.md` version-bump rule; `packages/AGENTS.local.md` release coupling
  and its test-authoring conventions.

## Construction tests

Per-task tests sit under each task and own disjoint files. Cross-cutting only:

**Integration tests:** the golden suite, extended by T2 to three routes, carries AC4.
`tests/integration/test_{apm_install_route,claude_plugins_install_route,plugin_route_membership}.py`
and the shipped contract and portable-projection suites run unmodified as AC5's oracle.

**Manual verification:** one full catalogue build through the CLI at T7; record stdout,
exit code, and the output directories produced.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current architecture — how a route is dispatched | T3-T7 | AC2 report empty outside the allowlist | `docs/architecture/` route-dispatch pointer (T7) |
| Maintainer procedure — adding a route | T3, T7 | AC1 holds for any declared route | That pointer states the contract-plus-schema-plus-handler steps (T7) |
| Interface compatibility — contract unchanged | T3 | Parity gate green; schema untouched in the diff | Canonical and `_data/` copies identical |
| Release history — the package bump | T7 | `version.py` and `pyproject.toml` bumped | `CHANGELOG.md` entry in the same commit |
| Reusable learning — a schema acting as a value snapshot | T1 | The probe result and the slice boundary it set | Routed through `project-knowledge` at `plan-locked` |

## Design (LLD)

Shape is `mixed`; `ui` sub-sections pruned.

### Design decisions

- **Route behavior is looked up, not branched on.** The form of the lookup is a
  build-time choice; the requirement is that no shared module decides by route name and
  that each decision is traceable to the contract. Traces to: AC2.
- **Registration is explicit while the route set is closed.** Dynamic discovery would
  add an import-time trust boundary this slice cannot exercise, since the schema admits
  no fourth route. It belongs with the sibling slice. Traces to: AC2.
- **Preservation is proved by the shipped tests, not by re-description.** Restating the
  relocated behaviors here would create a second home for them that can drift, and an
  earlier draft of this contract did describe two of them wrongly. Traces to: AC5, AC6.
- **Surfaces assert set equality against the contract,** so the assertion holds for any
  declared route rather than naming three. Traces to: AC1.

### Data & schema

`contracts/distribution-routes.schema.json` is not modified. The contract is read
through the existing bundled loader. Traces to: AC1, AC4.

### Interfaces & contracts

No new contract type and no new public flag. The legacy install-route emission gains a
fourth entry additively, its three existing outputs byte-identical. Traces to: AC3.

### Component / module decomposition

The contract-derived lookup and the per-route behavior it selects are new; their
placement and shape are build-time decisions constrained by AC2's allowlist — a module
the allowlist covers serves exactly one route, so shared code cannot hide a branch
there. The existing per-route projectors are reused rather than rewritten.

### Failure, edge cases & resilience

Refusal ordering, path and symlink handling, and diagnostic content are unchanged;
their shipped tests are the oracle. Where this slice must choose an order it does not
inherit, it resolves the route's behavior before producing that route's output.

### Quality attributes (NFRs)

No performance bar. Determinism is the operative NFR, proved by AC4.

### Dependencies & integration

No new dependency.

## Tasks

### T1: The pre-change route decisions are enumerated and their evidence established

**Depends on:** none
**Implements:** AC2 (evidence half)
**Touches:** `tools/`, `docs/specs/distribution-route-registry/`

**Verification mode:** goal-based, `no stub (implementation-discovered)`. Discovery
predicate: which mechanism can actually establish AC2's two properties over this
codebase — the forms a route decision takes here are only partly known before the
search runs. Constraint: no mechanism is frozen here, and none may be validated solely
against its own fixtures or against the audit it is reconciled with. Required outcome:
the four evidence outcomes below. Proof obligation: record the chosen mechanism, the
concrete mutations, and the completeness argument in the implementing PR, before T7
consumes any of them.

**Evidence outcomes this task must establish:**
- A pre-change enumeration of every site where a route name drives a decision, recorded
  as an artifact with its measuring commit, so later work compares against a fixed
  baseline rather than a moving one.
- A reproducible check that reports such sites, covering both forbidden forms — a shared
  module naming a route, and shared code deciding from a contract-derived route value.
- A completeness argument that is checkable rather than asserted. Agreement between the
  check and `notes/agent-plugin-surface-gaps.md` does not qualify: both were produced by
  searching for known forms, so their agreement says nothing about a third form. The
  argument must be reducible to a check someone else can run and that can come out
  negative — for example, enumerating consumers of route-dependent values from the
  contract loader outward and showing the residue is empty. Prose describing a manual
  review is not a completeness argument, because nothing about it can fail.
- A set of mutations that the check detects, each recorded with why the set covers both
  forbidden forms rather than only the form the check already recognises.

**Approach:** run the search, reconcile against the audit in both directions, update the
audit where it is short, and record what the reconciliation cannot establish.

**Done when:** the four outcomes exist, the baseline is reproducible at its recorded
commit, the audit and the enumeration agree with every difference explained, and the
completeness argument names its own limits rather than asserting exhaustiveness.

### T2: The Agent Plugin tree gains a pre-change golden

**Depends on:** none
**Implements:** AC4
**Touches:** `packages/agentbundle/tests/fixtures/distribution-routes/`, `packages/agentbundle/tests/build_pipeline/test_distribution_route_golden.py`

**Verification mode:** goal-based capture, then TDD comparison.

**Tests:** the suite inventories two routes at `:89` and asserts exactly two keys at
`:124`; both change to derive from the contract. Killing mutation: alter one byte of a
captured Agent Plugin file.

**Approach:** the existing witness packs carry non-skill primitives, so the portable
route admits nothing from them and a naive capture yields an empty tree — a present key
with a vacuous comparison. Establish a portable-eligible witness first, then capture,
then extend the comparison. Record the capture commit.

**Done when:** the Agent Plugin inventory is non-empty, all three routes compare green
on the unmodified tree, the mutation fails, and the capture commit precedes T3.

### T3: Route behavior is selected from the contract

**Depends on:** T1, T2
**Implements:** AC2 (dispatch half), AC5, AC6, AC7
**Touches:** `packages/agentbundle/agentbundle/build/main.py`, `packages/agentbundle/agentbundle/build/`, `packages/agentbundle/tests/build_pipeline/test_route_lookup.py` (new)

**Verification mode:** TDD. `no stub (implementation-discovered)` for the lookup
itself: its callable surface is created by this task, and the stub rule forbids
inventing a symbol to manufacture a stub. Discovery predicate: the lookup's entry point
and the shape of the per-route behavior it returns. Constraint: no invented helper,
module, or symbol; the allowlist in AC2 constrains where per-route code may live.
Required outcome: shared code obtains each route decision from the contract, and each
route retains its own controls. Proof obligation: on entering CODE-IMPLEMENTATION,
write the lookup and per-route-control assertions against the real surface and prove
each red before the production change.

**Tests:** in the new `test_route_lookup.py`. The grounded half is already
assertable: `_resolve_distribution_route` at `build/main.py:1236` currently restates
contract values as literals at `:1256` and `:1272`, and a test that reads those values
from the contract instead is red today. AC6's per-route control record is asserted
here. The shipped contract and portable-projection suites run unmodified throughout —
AC5 fails if either needs editing.

**Approach:** remove the restated literals so the resolver reads the declaration;
introduce the contract-derived lookup and register the existing per-route projectors
against it. Registration is explicit and internal, since the route set is closed.

`test_distribution_routes_have_no_registration_surface`
(`test_distribution_route_resolution.py:170`) asserts `build_main` exposes no
`ROUTE_REGISTRY` or `register_distribution_route`. That is the Phase-0 boundary this
slice supersedes, not a behavior to preserve, so it is rewritten under AC5's carve-out
to assert what now holds — registration is internal and no handler is discovered
dynamically — and the rewrite is recorded with its reason. Every other shipped
assertion runs unmodified.

**Done when:** the resolver reads the contract, each route's controls are recorded with
their proving test, route behavior for every route resolves before the build's first
output artifact with the AC7 sentinel untouched, every shipped suite is green except the
one carve-out rewrite, and goldens are untouched.

### T4: Build-pipeline sites take their route set from the lookup

**Depends on:** T3
**Implements:** AC1 (build-pipeline rows), AC2, AC5
**Touches:** `packages/agentbundle/agentbundle/build/main.py`, `build/lint_packs.py`

**Verification mode:** goal-based, plus the shipped suites as the behavioral net.

**Tests:** the T1 report is empty for these files. The existing build-pipeline suite
runs unmodified and stays green.

**Approach:** the sites the audit names in these two files — default-build recipe
membership and the capability lint's direct route read. If T1's enumeration surfaces a
decision in another build-pipeline module, it is added to the audit and to this task
rather than silently changed; `build/hook_wiring_rules.py` is deliberately excluded
because the audit names no route decision there.

**Done when:** the check reports no route decision in these files, every build-pipeline
module T1 added to the audit is covered here — a decision AC1 depends on cannot be
deferred out of this task; if one proves to belong elsewhere, it moves to a named task
in the same PR rather than to a reason — and the build-pipeline suite is green
unmodified.

### T5: CLI, install, validate, verify, diff, and upgrade take their route set from the lookup

**Depends on:** T3
**Implements:** AC1 (command-surface rows), AC2, AC3, AC5
**Touches:** `packages/agentbundle/agentbundle/commands/render.py`, `commands/install.py`, `commands/validate.py`, `commands/diff.py`, `commands/upgrade.py`, `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`, `packages/agentbundle/tests/unit/test_route_surface_parity.py` (new)

**Verification mode:** TDD. `stub: true` — every symbol this asserts on is grounded
today. Validated 2026-09-03: compiles, and red from disposable scratch with
`assert {'apm', 'claude-plugins'} == {'agent-plugin', 'apm', 'claude-plugins'}`, which
is exactly the gap this task closes. Note the recipe TOMLs nest under a `[recipe]`
table and recipe names do not derive from route names (`per-pack-apm-package`, not
`per-pack-apm`), so the route set is read from each recipe's declared `route` field;
an earlier draft of this stub was red for the wrong reason because it missed both.

```python
def test_every_declared_route_reaches_the_recipe_surfaces() -> None:
    """Each surface's recognised routes equal the set declared in the contract."""
    import tomllib
    from importlib import import_module
    from pathlib import Path

    build_main = import_module("agentbundle.build.main")
    validate_cmd = import_module("agentbundle.commands.validate")
    install_cmd = import_module("agentbundle.commands.install")

    build_dir = Path(build_main.__file__).resolve().parent
    contract = tomllib.loads(
        (build_dir.parent / "_data" / "distribution-routes.toml").read_text("utf-8")
    )
    declared = set(contract["route"])

    route_of = {}
    for path in sorted((build_dir / "recipes").glob("per-pack-*.toml")):
        body = tomllib.loads(path.read_text("utf-8"))["recipe"]
        if body.get("route"):
            route_of[body["name"]] = body["route"]

    def routes_on(recipe_names: object) -> set[str]:
        return {route_of[n] for n in recipe_names if n in route_of}

    assert routes_on(validate_cmd.VALID_RECIPES) == declared
    assert routes_on(install_cmd._LEGACY_INSTALL_ROUTE_RECIPES) == declared
```

**Tests:** the stub above grows to cover the remaining command-surface rows of AC1.
All five of AC3's minimum change groups are pinned before and after — the pack-declarable
recipe, the install-route emission, the render target set, catalogue verification, and
the dist-tree detections, the last covering install, diff, and upgrade as three distinct
surfaces rather than one. Any further surface whose route set changes is pinned the same
way. The shipped install integration suites run unmodified, and because this task
relocates decisions, AC5 applies here too: each relocated behavior's proving test is
named and shown exercising the relocated path.

**Approach:** the sites the audit names in these six files. The dist-tree prefix
detections derive their prefixes from the declared output subdirectories. The audit
names sites by their current symbol only to locate them; an implementation that replaces
a hand-maintained collection with a contract-derived call satisfies this task, and the
stub's assertions move with it — the requirement is the observable route set, not the
survival of `VALID_RECIPES` or `_LEGACY_INSTALL_ROUTE_RECIPES` as names.

**Done when:** the check reports no route decision in the six files, AC1 holds for
every command-surface row, all five AC3 groups are pinned before and after, and the
install integration suites are green unmodified.

### T6: Build-check expectations come from the lookup

**Depends on:** T3
**Implements:** AC1 (build-check row), AC2
**Touches:** `packages/agentbundle/agentbundle/build/self_host.py`

**Verification mode:** goal-based. `no stub (goal-based)`.

**Tests:** the T1 report is empty for `self_host.py`, and `make build-check` is green.
Per repository memory it cannot run concurrently with pytest, so it runs alone.

**Approach:** derive the checked output directories and expected lifecycle artifacts
from the resolved route rather than the hard-coded pairs the audit names.

**Done when:** the report is empty for the file and `make build-check` is green.

### T7: The guard closes, docs land, and bytes are proved unchanged

**Depends on:** T4, T5, T6
**Implements:** AC2 (guard), AC4 (closure)
**Touches:** `packages/agentbundle/tests/build_pipeline/test_route_branch_guard.py` (new), `docs/architecture/`, `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/pyproject.toml`, `packages/agentbundle/CHANGELOG.md`

**Verification mode:** TDD. `no stub (implementation-discovered)`: the guard consumes
the report interface T1 defines. Discovery predicate: that interface. Constraint: no
invented symbol. Required outcome: the guard fails under each AC2 mutation. Proof
obligation: prove every mutation in T1's recorded set red against the real interface
before landing the
guard.

**Tests:** the guard in its own file, exercised by the mutation set T1 recorded —
however many that set contains, since T1 discovers what is sufficient to cover both
forbidden decision forms. Every mutation in that set must fail the guard. The golden
suite runs over three routes against fixtures unmodified since their capture.

**Approach:** land the guard; write the `docs/architecture/` route-dispatch pointer;
run the full gate set; apply the version bump with its `CHANGELOG.md` entry in the same
commit and record the release-coupling determination; run the manual CLI build and
record stdout and exit code.

**Done when:** every gate is green, every mutation T1 recorded kills the guard, the
goldens are
byte-identical to their captured state with that commit proved earlier, the pointer
exists, and the bump carries its changelog entry.

## Rollout

- **Delivery:** one reversible unit; revert restores the prior dispatch. No flag.
- **Infrastructure:** none.
- **External-system integration:** none. No published package byte changes; AC3's four
  completions are additive and pinned before and after.
- **Deployment sequencing:** T1 and T2 before everything else is the only ordering that
  is load-bearing for correctness, since both measure the unmodified tree.

## Risks

- **A golden is regenerated during debugging**, turning AC4 into a tautology. T7
  asserts byte-identity to the captured state and that the capture came first.
- **The Agent Plugin baseline is empty**, since the existing witnesses admit nothing to
  that route. T2 establishes an eligible witness before capturing.
- **A relocation quietly changes a preserved behavior.** AC5 makes the shipped tests
  the oracle and forbids editing them, so this surfaces as a red suite rather than as a
  silently updated assertion.
- **`make build-check` and pytest void each other** — pytest writes `.apm/__pycache__`.
  T6 runs alone.
- **AC3 turns a green gate red for a pre-existing reason.** Extending catalogue
  verification to the `agent-plugins` tree can report a latent defect that was never
  checked. That is the intent; triage it as pre-existing rather than reverting.

## Changelog

- 2026-09-03: split from a larger slice. The earlier contract bundled two changes —
  extracting route dispatch, and opening the route set by generalizing the schema —
  and seven review rounds showed they conflict. `route.additionalProperties` is
  `false`, `route.required` names exactly the three shipped routes, and
  `build/main.py:1297` validates against the bundled schema, so a synthetic fourth
  route cannot reach the production resolver while the schema is closed; yet the
  extensibility criteria required exactly that. Opening the schema instead removes 33
  single-value pins per route that four of the eight shipped refusals rest on, and
  three review rounds of replacement mechanisms each came back weaker. This plan keeps
  only the extraction and the surface completion, both provable against the three real
  routes. Opening the set moved to its own intent.
- 2026-09-03: acceptance criteria reduced from sixteen to seven and reworded to state
  outcomes rather than mechanism, after the criteria began prescribing implementation
  detail that cannot be settled before code exists — a registration-table key, an
  enumerated admission matrix that misread the shipped predicate, an escape-case list.
  Preservation is now proved by the shipped tests staying green unmodified, which is a
  stronger oracle than re-describing behaviors this slice does not change and cannot
  drift from them.
- 2026-09-03 (EXECUTE, T2): a factual claim in AC4 and in T2's approach is wrong and is
  corrected here rather than silently worked around. Both say the existing witness packs carry
  non-skill primitives and would yield an empty Agent Plugin tree. Measured: `publishable` is
  excluded — the build prints `agent-plugin: pack "publishable" excluded by dropped primitives
  ["agent","command","hook-body","hook-wiring"]` — but `repo-only` is admitted and contributes
  two entries, so the tree would have been non-empty without any new witness. T2 added an
  explicit skills-only `portable` witness anyway, which is still worth having: it makes
  eligibility intentional and auditable rather than incidental, and it is what the assertion
  pins by name. AC4's requirement — a non-empty inventory — is met and remains falsifiable; only
  its stated reason was false. The spec is sealed, so this correction lives here; the spec's
  wording is fixed at closeout under the doc-drift invariants.
  Capturing the new witness also legitimately grew the `apm` inventory from 20 to 25 entries,
  since APM admits all packs. That is a pre-change recapture with no production code altered,
  so it does not weaken AC4: the goldens still pin a state that predates every behavioral
  change, and the one-byte mutation was observed to fail the comparison.
- 2026-09-03 (EXECUTE, wave 1 close): recording a loop-state gap so a resuming session is not
  misled. Wave 1 (T1, T2) is complete and its gates passed — 5494 passed, 57 skipped, 1 xfailed
  across `packages/agentbundle/tests/` and `tests/roster/`, with ruff, mypy, the docs lint, and
  the spec-status lint all clean. The engine transition and the cohort advance were issued in
  one block; the engine refused `wave-passed` because `wave-complete` must precede it
  (`CODE-IMPLEMENTATION -> CODE-VERIFICATION`), but the cohort advanced regardless. The cohort
  therefore sits at wave index 1 with no engine-side record that wave 0 passed. There is no
  rewind verb, and the guard requires `current_wave_index == --wave-index`, so the only way to
  satisfy the engine now would be to record `completed_wave_index: 1` — false, and it would
  cause a resuming session to skip T3. That was rejected. The owner chose to proceed and record
  the gap instead. Operative state: cohort wave index 1 selects T3, which is correct; the engine
  is in `CODE-IMPLEMENTATION`, which is the correct state for implementation work; the approved
  baseline is intact. The gate output above is the evidence wave 0 passed. Later waves must fire
  `wave-complete` before `wave-passed`, and must never issue the cohort advance in the same
  block as the transition it depends on.
