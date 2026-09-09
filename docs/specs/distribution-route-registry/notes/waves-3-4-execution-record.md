# Waves 3–4 execution record

`plan.md` is sealed once `schedule` persists it, so decisions taken while executing
T4–T7 are recorded here instead. Nothing below changes the accepted contract.

## Recipe order is load-bearing, and now says so

Deriving `DEFAULT_RECIPES` from the recipe declarations also changed the order the
default build ran them in. Sorting by name put the portable route first, and two
shipped tests went red:

```
packages/agentbundle/tests/integration/test_hook_wiring_ingress.py
  ::test_render_boundary_rejects_before_output_creation
  ::test_plugin_route_requires_hook_consent_before_output_creation
AssertionError: assert not True   #  output.exists()
```

Cause: the portable route excluded the hazardous pack and created `output/`, and only
then did the Claude route raise its hook-consent refusal. The shipped invariant is that
a refusal leaves no output behind, and it had been holding only because the Claude
recipe happened to be written first in a hand-maintained tuple.

Fix: each route declares `build_order` on its own behavior, and shared code sorts by
it — aggregates last, refusal-capable route first. `DEFAULT_RECIPES` is byte-identical
to its pre-change value. The broken ordering is that invariant's killing mutation: it
was observed red, and reverting it green.

## Two shipped tests changed, with their reasons

AC5 forbids editing a shipped test to make a relocation pass. Neither change below is
that; both are recorded here because the distinction matters.

**`test_install_cmd.py::test_path_jail_probe_refused`** pinned the legacy install-route
recipe tuple as three literal names. That assertion *is* the install-route-emission
surface AC1 lists, and AC3 requires it to gain a fourth entry — so the change falsified
it by design. Per the spec's *Never do* — "Delete a regression test because the change
makes its assertion false; rewrite it" — only that assertion was rewritten, to pin the
members that must keep rendering. Its path-jail refusal assertions are untouched. Set
equality against the contract lives in `test_route_surface_parity.py`, so the rewrite
is not a weakening. The tautological form — asserting install matches its own constant
— was rejected: it cannot fail.

**`test_distribution_route_resolution.py::test_distribution_routes_have_no_registration_surface`**
was rewritten in T3 under AC5's explicit carve-out, for the reason the plan records.

## `--verify-baseline` is a pre-change proof, not a post-change gate

`--verify-baseline` runs `git diff --quiet <measuring-commit> -- <measured paths>` and
refuses with `measured inputs differ from the baseline commit` as soon as any
production file changes. It can only pass at the commit it pins. It is T1's
reproducibility evidence, discharged at `1134701ba584ce5375358943f2cbab4ea69574a0`; it
is not runnable as a closing gate and was not treated as one. The operative gate after
the change is `--check`, which must report zero decisions and zero residue.

T7 and the two review rounds extended the checker, so it measures the same tree more
completely than the original baseline did. The baseline was therefore re-measured at its
own commit with the final instrument — see the review section below — rather than
regenerated against the changed tree, which would have destroyed the evidence it exists
to hold.

## AC4 closure evidence

The spec asks that the goldens' capture commit be recorded and asserted to precede the
first behavioral change. Nothing in this slice was committed per task, so there is no
capture commit to cite. The stronger equivalent was measured instead:

1. A clean worktree at `1134701ba584ce5375358943f2cbab4ea69574a0`, with production code
   and `contracts/` byte-identical to that commit.
2. Overlaid with only the test inputs this slice adds — the `portable` witness pack, the
   extended golden suite, and `golden.json`.
3. `pytest packages/agentbundle/tests/build_pipeline/test_distribution_route_golden.py`
   → 4 passed.

So `golden.json` reproduces exactly from pre-change production code, and it also passes
on the changed tree. Published bytes are unchanged for all three routes.

Killing mutation, observed: flipping one base64 character of
`agent-plugin → portable/skills/example/SKILL.md` fails
`test_golden_oracle_declares_every_route_tree`. The file was restored by rewriting it
and its SHA-256 re-checked as `24ccc0e5f1f29cae10702e1c8ae9938403b32071b617c0102e03e7f3416c402a`.

## The dispatch exemption is earned by a declaration

Following route values through carrier dataclasses made one contract-selected dispatch
call — `resolved_route.behavior.run_per_pack(context, ...)` — read as an unclassified
escape. Exempting it by matching the attribute name `behavior` would have put a
hand-maintained name back into the checker, which is the shape this slice exists to
remove.

The exemption is instead derived: a route type's field whose declared annotation names
a collaborator rather than a plain value is a dispatch field, read from the class
definition. A call through such a field that passes only carriers is dispatch, not a
decision. `test_dispatch_exemption_requires_a_declared_collaborator_field` pins that
the rule is earned by the declaration — with `behavior: str` the same call is reported.
The limit is recorded in the checker's own `limits` list.

## Release-coupling determination

**A release is required.** `packages/AGENTS.local.md` names published output layout as a
release boundary, and `agentbundle install --emit-install-routes` now also writes
`agent-plugins/<pack>/`. `agentbundle validate` additionally accepts a recipe it
rejected before, and two user-visible install messages change. Every change is additive:
no previously valid file becomes invalid, and no existing output byte moves.

Bumped `0.41.1 → 0.42.0` in `version.py` and `pyproject.toml`, with the `CHANGELOG.md`
entry in the same commit. `origin/main` carries `0.41.1`, so the bump does not collide.

## Spec wording corrected at closeout

AC4 said the existing witness packs would yield an empty Agent Plugin tree. Measured,
`repo-only` is admitted and contributes two entries, so the tree would have been
non-empty. The requirement held and still fails under mutation; only the stated reason
was wrong. The plan changelog recorded it during T2 because the spec was sealed; the
spec wording is corrected at closeout under the doc-drift invariants.

## AC5 — each relocated decision, its proving test, and the relocated path

Every test named here is a shipped test that runs unmodified. "Reaches" states how
the test's own call path arrives at the relocated code rather than the code it
replaced.

| Relocated decision | Now at | Shipped test that proves it | How the test reaches the relocated path |
| --- | --- | --- | --- |
| Portable pack discovery — no-follow roots, confined metadata | `route_agent_plugin.discover_packs` → `main._discover_packs_confined` | `test_agent_plugin_projection.py::test_agent_plugin_discovery_refuses_unsafe_pack_roots_and_metadata` | Call `discover_packs(..., diagnostic_route=...)`, which now resolves the behavior and delegates; the generic branch it used to take is a separate function |
| Portable pre-uniqueness controls | `route_agent_plugin.prepare_pack` → `main._preflight_confined_pack` | `test_agent_plugin_projection.py::test_agent_plugin_dropped_primitive_roots_are_no_follow` | `run_recipe` calls `resolved_route.behavior.prepare_pack` before `validate_pack_uniqueness`; the old inline branch is gone, so a green refusal can only come from the behavior |
| Portable diagnostic normalisation | `route_agent_plugin.normalize_pack_error` → `main._normalize_confined_error` | `test_agent_plugin_projection.py::test_agent_plugin_projection_refuses_unsafe_or_oversize_skill_trees` | `run_recipe`'s `except` calls `behavior.normalize_pack_error`; the sanitised class is produced nowhere else |
| Claude hook-consent refusal and publishable filter | `route_claude_plugins.run_per_pack` → `main._run_per_pack_adapter` | `test_hook_wiring_ingress.py::test_plugin_route_requires_hook_consent_before_output_creation`; `test_plugin_route_membership.py` | `_run_per_pack` builds the context and calls `behavior.run_per_pack`; the `route_filtered` guard that used to gate these was deleted |
| Claude adapter projection contract | `route_claude_plugins.projection_contract` | `test_build_derivation_claude_plugins.py` projection assertions | `_projection_contract_for_route` now only delegates; the rewriting body moved to the route module |
| APM source-tree preflight and projector | `route_apm.run_per_pack` → `main._run_per_pack_apm` | `test_apm_install_route.py`; the APM golden rows | Same `behavior.run_per_pack` seam |
| Package-projector selection | `RouteBehavior.run_per_pack` | the three-route golden suite | The golden compares complete built trees, which can only be produced through the new dispatch |
| Install-marker drift expectations | `RouteBehavior.lifecycle_marker_relative_path` + `admits_lifecycle_marker_pack` | `test_build_check_drift_gates.py::test_make_build_check_fails_on_writer_drift` and `::test_make_build_check_fails_on_apm_writer_drift` | One derived loop is the only remaining producer of these failures |

## AC6 — per-route controls and their killing mutations

| Route | Control it keeps | Shipped test that proves it | Cross-route mutation and observed result |
| --- | --- | --- | --- |
| Agent Plugin | Confined, no-follow discovery; sanitised diagnostics; skills-only admission | `test_agent_plugin_projection.py` unsafe-source suite; `test_route_lookup.py::test_default_build_discovers_packs_with_the_strictest_declared_control` | `discovery_priority` 1 → 0 points the default build at APM's generic discovery. **Observed:** `assert 'generic' == 'confined'` — the test records which discovery `run_default_build` actually called. Restored; file SHA-256 re-verified |
| Claude Plugins | `plugin.json` + `pack_is_publishable` admission for the marker gate; its own marker path | `test_build_check_drift_gates.py::test_make_build_check_passes_on_clean_tree` | Admission widened to all packs → red for the repo-only pack; marker path pointed at APM's → red for four admitted packs |
| APM | All-pack admission; `.apm/hooks/install-marker.py` | `test_build_check_drift_gates.py::test_make_build_check_fails_on_apm_writer_drift` | Admission disabled → the mutated marker goes undetected, red; marker path pointed at Claude's → red for all five packs |

Before this round the discovery control had **no** killing test: lowering
`discovery_priority` survived `build_pipeline/`, `test_hook_wiring_ingress.py`, and the
parity suite. That gap is what the new `test_route_lookup.py` case closes.

## AC4 — the re-runnable procedure

The goldens reproduce from production code at base commit
`1134701ba584ce5375358943f2cbab4ea69574a0`. To re-run:

```bash
git worktree add --detach /tmp/ac4-base 1134701ba
cp -R packages/agentbundle/tests/fixtures/distribution-routes/witness-packs \
      /tmp/ac4-base/packages/agentbundle/tests/fixtures/distribution-routes/witness-packs
cp packages/agentbundle/tests/fixtures/distribution-routes/golden.json \
   /tmp/ac4-base/packages/agentbundle/tests/fixtures/distribution-routes/golden.json
cp packages/agentbundle/tests/build_pipeline/test_distribution_route_golden.py \
   /tmp/ac4-base/packages/agentbundle/tests/build_pipeline/test_distribution_route_golden.py
cd /tmp/ac4-base && git diff --stat -- packages/agentbundle/agentbundle contracts   # must be empty
PYTHONPATH=packages/agentbundle:packages/credbroker python3 -m pytest \
  packages/agentbundle/tests/build_pipeline/test_distribution_route_golden.py -q
git worktree remove --force /tmp/ac4-base
```

Only test inputs are copied in; the empty `git diff --stat` is what proves production
code and `contracts/` are byte-identical to the base commit. Observed: 4 passed.

## Deviations from the plan's declared Touches

- **The AC2 guard lives at `tools/test_route_branch_guard.py`,** not the
  `packages/agentbundle/tests/build_pipeline/` path T7 names. The engine's test tree
  ships inside the sdist and the guard reads a repository-only `tools/` script, so the
  release gate failed with `FileNotFoundError`. A `skipif` was not an option either:
  that gate allowlists skip reasons and rejects unexpected ones. `packages/AGENTS.md`
  puts a repository tool's tests beside its script, which is where it now sits.
- **`Makefile` and `.github/workflows/build-check.yml` gained two test modules,** and
  `tools/test_local_ci_shared_test_deduplication.py` was re-pinned to match. Nothing
  globs `tools/test_*.py`, so both the checker's mutation suite and the guard ran in no
  gate at all — an ungated guard proves nothing. The dedup guard pins the exact batch
  composition by SHA-256; its documented protocol was followed: with the Makefile line
  reverted, this worktree reproduced both recorded digests exactly, proving the pins
  were current and this change is their sole cause.
- **The golden suite reads the packaged contract** through `_read_bundled` rather than
  the repository `contracts/` copy, for the same sdist reason. The contract-parity gate
  keeps the two byte-identical.

## Build-check drift messages that changed text

The two near-duplicate gates became one derived loop, so five message templates
changed. No shipped test pins any of them — `test_build_check_drift_gates.py` asserts
return codes — and each still names the route through its own `drift_label`.

| Before | After |
| --- | --- |
| `packs_dir … cannot enumerate Claude-plugins-route packs for drift check` | `… cannot enumerate lifecycle-marker packs for drift check` |
| `writer-template drift — pack X has a source plugin.json but no projected install-marker.py at …` | `writer-template drift — pack X has no projected install-marker.py at …` |
| `APM writer-template drift — dist/apm/ not present at … (run make build before make build-check)` | `… (run make build before make build-check, or use the build-check target which depends on build)` |
| `APM writer-template drift — pack X has no projected APM install-marker.py at … (APM derivation rail broken …)` | `APM writer-template drift — pack X has no projected install-marker.py at … (derivation rail broken …)` |
| `APM writer-template drift — dist/apm/X/.apm/hooks/install-marker.py diverges …` | `APM writer-template drift — X/.apm/hooks/install-marker.py diverges …` |

## Post-gates review: two rounds, and what the second one found

Round 1 raised 21 findings; adjudication sustained 17 and refuted 4. Round 2 reviewed
the fixes and raised 14 more — and three of its four blockers were in code written to
close round 1. They are recorded here because each is a case of a control that looked
like it worked.

- **The cross-module taint fix only recognised a bare-name call.** Every production
  consumer spells it `route_lookup.read_route_declarations(...)`, so 12 of 14 call sites
  stayed untainted and the fix barely applied. The taint source is now the resolved
  callee, however it is qualified.
- **The discriminator field set was a hand-maintained six-name list** that omitted
  `output_subdir` — the field every derived surface actually keys on. It is now read from
  the route types' own field declarations. `adapter_projector` is deliberately excluded
  and recorded as a limit: reading it is how shared code reaches the projector the route
  declares, so treating it as a decision would report the dispatch the contract exists to
  provide.
- **The single-route exemption could be minted by any file.** A three-line module naming
  `main.behavior_from_declaration` in a tuple silenced a planted route literal in
  `main.py`. The exemption now also requires the named module to define that factory.
- **The AC6 discovery test passed under its own mutation for the wrong reason.** The
  `ValueError` it caught came from the per-pack confined preflight, not from discovery, so
  the only assertion that could fail compared two docstrings. It now records which
  discovery implementation `run_default_build` actually called; under the mutation it
  fails with `assert 'generic' == 'confined'`.

Round 2 also produced two substantive non-blocker changes:

- **The install messages are additive again.** Sorting the declared output subdirectories
  alphabetically put `agent-plugins` first and swapped `apm` and `claude-plugins`, which
  AC3 forbids — it admits inclusion of a declared route, never a change to what a surface
  does for the other two. They are now ordered by each route's declared build order, so
  the pre-existing pair keeps its positions and the new route appends.
- **The pre-change baseline is reproducible again.** `--verify-baseline` compared the
  checker's own `limits` and `mutations` prose along with the measurement, so extending
  the checker made the pinned baseline unverifiable at its own commit. It now compares
  measured evidence only — findings, residue, coverage, scope. The baseline was then
  re-measured **at `1134701ba` in a clean worktree**, with the shipped instrument, on
  unmodified production code, and `--verify-baseline` reports `baseline reproduced
  exactly` there. It records **50** pre-change decisions. An intermediate re-measurement
  during this round read 46; that instrument still carried a whole-function exemption
  that round 3 removed, and the four findings it was hiding are the resolver literals
  this slice exists to remove — so 50 is the figure, and 46 was the undercount.

## Round 3, and the regression three rounds of gates missed

Round 3 raised 12 findings. The first was a **user-facing regression no gate covered**:
`agentbundle catalogue build --recipe composite-agents-md` exited 0 at
`1134701ba` and exited 1 on this branch with `field 'route' names unknown distribution
route None`. `cmd_build` resolved a route unconditionally, but `composite`, `overlay`,
and `self-host` recipes declare none. Nothing in the suite drove `--recipe` with a
routeless recipe, so 5,599 passing tests and a green `build-check` said nothing about it.
`test_explicit_recipe_build_accepts_a_recipe_that_declares_no_route` now covers all
three; removing the guard makes it fail `assert 1 == 0`.

The rest were in the checker, and two were exemptions that had become escape hatches:

- **The single-route exemption was still mintable.** A two-line factory stub plus a
  one-line tuple in a sibling file silenced route literals in that module. The exemption
  now also requires the collection to be one its own module iterates — the registry the
  lookup actually resolves through. The round-2 mutation that claimed to cover this
  could not fail (it named the module in itself, hitting the self-registration guard);
  it is replaced by a genuine two-file pair, verified red without the fix.
- **The producer exemption was too broad.** Skipping every function whose return
  annotation is a route value hid decisions inside `_resolve_distribution_route`, the
  function most likely to regrow a branch. It is gone. The false positive that motivated
  it — the resolver comparing a recipe's declared `output-subdir` against the route's —
  is now handled precisely: a recipe-typed value carries only the route it *names*, so
  its other attributes are recipe data. A real route decision in the resolver
  (`recipe.route == other`) is reported.

Also from round 3: the import-time build-order fallback returned `{}` on an unreadable
contract, which fell back to name order — the exact ordering that let a refused build
leave `output/` behind. A safety invariant must not fail open, so it refuses instead, and
`test_default_recipe_order_is_derived_and_refusal_capable_route_runs_first` pins that the
order is non-empty, total, aggregate-last, and led by the route carrying the refusal.
`diff` and `upgrade` no longer inherit an import-time contract read from `install`, and
the build-check drift gate reports an unusable contract as a named failure rather than
raising out of the gate chain.

## Rounds 4 and 5: the review stopped converging, and why

Round 4 raised 9 findings, round 5 raised 10. Findings per round ran 21, 14, 12, 9, 10 —
and by round 5 the dominant source of new defects was the previous round's fixes rather
than the original change.

Round 4's four blockers: the baseline had gone stale again (round 3 changed the
instrument and nothing re-measured it); import-time contract reads turned every CLI verb
into a traceback on a corrupt bundled contract; a route-keyed `.get()` escaped the guard
because `"get"` sat in a skip set; and `install --emit-install-routes` gained an
unrecorded stderr line.

Round 5 then found that **two of round 4's own fixes were regressions**:

- Gating the portable route's exclusion notice on `aggregate_scope` **deleted a shipped
  diagnostic**. `per-pack-agent-plugin` was already in the default recipe set at
  `1134701ba`, so `render packs/core` printed that exclusion at base and printed nothing
  after the change — measured in both trees. The spec's *Always do* requires preserving
  each route's existing diagnostic behavior, and the in-code justification ("this route
  now runs there too") was simply false. Reverted; base and current stderr now match
  byte for byte.
- Deferring the contract read behind module `__getattr__` did not reach the command
  modules, which resolve `DEFAULT_RECIPES` at *their* import. `agentbundle validate`
  exited 0 at base and exited 1 with a traceback after the change. The command modules
  now obtain the recipe set through call-time accessors, and `import
  agentbundle.commands.diff` no longer raises on a corrupt contract.

Round 5 also reopened the `.get()` hole for mappings built by a comprehension or
`dict()`, which the round-4 rule keyed on syntax rather than on the key. It is now judged
on whether the key is a route value and whether the mapping was assembled in the scanned
module by any syntax; the three spellings are guard cases.

**The pattern.** Every round's findings concentrated in one artifact:
`tools/check_distribution_route_decisions.py`, the AC2 evidence checker. It began as a
bounded literal scanner and became a small interprocedural taint analyser carrying twelve
recorded exemptions, and each widening opened a hole the next round found. The
production change — the fifteen surfaces reading their route set from the contract — has
been stable since round 1; no round after the first found a defect in it.

## The split, and what this slice ships

After round 5 the owner chose to split rather than keep iterating. What ships here is
the route derivation — the fifteen surfaces reading their route set from
`contracts/distribution-routes.toml` — plus the checker at a bounded scope: the literal
form covered everywhere, the contract-derived-value form covered where the route types
are annotated, which is module-local.

That is the shape the checker had when round 1 reviewed it, and it is the shape that was
stable. The deeper analysis attempted across rounds 1–5 — cross-module taint,
projector-identity vocabulary, a derived discriminator field set, `.get()` dispatch, and
a registration-derived single-route exemption — is removed from this slice and tracked by
`docs/product/intents/route-decision-analysis-depth.md`, which records what it must do,
why it needs its own contract, and that working code for all of it existed and is
recoverable from this branch's history.

AC2 now states its bound rather than implying completeness, and the checker's `limits`
names the module-local boundary explicitly. The pre-change baseline was re-measured at
`1134701ba` with the shipped bounded instrument: **50 decisions**, `baseline reproduced
exactly`, and `tools/test_route_branch_guard.py::test_recorded_baseline_reproduces_at_its_measuring_commit`
now fails if the instrument drifts from what the baseline records.

Removed with the depth work, and recorded here so their absence is deliberate: five
checker fixture tests and seven guard mutations covering the cross-module, projector-
identity, derived-field, module-qualified-reader, `.get()`-dispatch and minted-exemption
forms. The eight mutations that remain cover both forbidden forms within the stated
bound.
