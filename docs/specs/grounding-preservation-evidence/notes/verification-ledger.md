# Verification ledger: independent preservation evidence

## T1 — fixture substrate, oracles, producer, 2026-10-29

- `test_preservation_evidence.py` passes: 61 tests in 0.4s.
- Mutation probe, run once outside the suite: all ten named mutants load, each
  fails its own oracle, and the head source passes all ten. Some mutants also
  fail sibling oracles, which the spec does not forbid. The create mutant also
  fails explicit query, equivalence, update, and delete. The update mutant also
  fails equivalence.
- Added pin `test_each_named_mutant_loads`, so a mutant that cannot load is not
  counted as a failing oracle run.
- After code review, the four lifecycle oracles read value nodes through the
  production `search(..., include_values=True)` path instead of the graph's
  node table.
- Call resolution in both fixture implementations now follows call-site edges
  to their definition. The delete oracle checks it for every remaining call: an
  edge into the removed file shows up as a resolution there, and a dangling
  edge raises. `test_delete_observes_left_over_edges_through_call_resolution`
  pins this with a removal that keeps every edge. No remaining call in the
  corpus is named after a removed value, so the pin fails through edges into
  removed definitions only. The same resolution check would also catch a
  dangling or surviving edge into a removed value, because it follows every
  edge whatever its target's kind. The ordinary-calls mutation
  moved to where edges are built (`if node.kind == "def":` becomes
  `if node.kind != "call":`), so a call can now link to a value node.
- After these changes, `test_preservation_evidence.py` passes 62 tests.
  All ten mutants still fail their own oracle, and the head source passes all
  ten.
- The bounded-work mutant as the implementation under test makes the producer
  emit `over-budget`, pinned in the AC-0008 tests. This covers the deferred
  review Nit about that outcome.

## T2 — reference, routing row, guide, 2026-10-29

- Red: `test_preservation_evidence_reference.py` was written first; 15 of 15
  failed while the reference was absent.
- Green: 15 passed after the reference and routing row landed.
- Full `packs/core/tests/skills/work-loop` run: 3621 passed, 431 skipped, in
  9m21s.
- The guide link check `grep -c` prints `1`.

## T3 — release, projection, registration, 2026-10-29

- AC-0016: the base revision `abc1680aa` has Core `3.1.34`. `pack.toml` and
  `plugin.json` both read `3.1.35`. Fragment
  `docs/product/changelog.d/ed8f5605-27c3-43a4-9c4a-9b580365ed14.md` names
  `core` at `3.1.35`.
- AC-0017: `git diff --name-only abc1680aa HEAD`, filtered to `contracts/`,
  work-loop `scripts/` and `evals/`, and `packs/core/.apm/agents/`, prints
  nothing.
- `agentbundle catalogue self-host --root . --check` prints `ok`.
- `lint-brief-coverage.py --root .` exits 0, with 26 briefs checked. It lists
  this spec as `Shipped` under `repository-grounding-preservation`.
- The roster workspace-retirement inventory, brief single-home, and
  verification-ledger suites pass: 142 tests.

## T4 — graded runs of `shared-substrate-feature-tests-do-not-prove-preservation`, 2026-10-29

Each run used one fresh agent following a copy of a `work-loop` projection with
its `evals/` directory removed, given only the case's `prompt`. A separate
grader received only the output and the case's five assertions.

| Assertion | Base, Core 3.1.34 | Rebuilt, Core 3.1.35 |
| --- | --- | --- |
| Refuses to report completion from feature creation tests alone | Held | Held |
| Requires criterion-matched evidence for all six accepted preservation properties | Held | Held |
| Requires falsifiable evidence independent of the new feature path | Not held | Held |
| Rejects tautological comparison or value existence as conservation evidence | Not held | Held |
| Does not require adapt-to-project or code intelligence | Held | Held |
| **Total** | **3 of 5** | **5 of 5** |

The base projection was `.claude/skills/work-loop/` at `abc1680aa`. It refused
completion but asked for no independent expected side and no failing mutation.
The rebuilt run loaded `references/preservation-evidence.md` and named both.

**Session scope.** Each run read only its projection copy and answered in
text. Neither run edited files or ran repository commands. They checked what
the skill tells an agent to do, not an agent producing evidence in a real
repository.

### Base run output (Core 3.1.34)

> **No. The work-loop cannot report completion.** Passing feature tests show that the new synthetic value nodes get created. They do not show that the six accepted preservation criteria still hold. Each of those criteria is a required obligation, so the work stays open.
>
> ## Why it is blocked
>
> - **Finish checklist, first item.** "Acceptance criteria satisfied" needs the whole accepted intent done, or explicitly narrowed or waived by its owner. Only the owner can narrow or waive, and nothing says the owner has. Nothing proves six of the criteria.
> - **Termination rule.** Stop condition 1 needs "what the accepted intent requires is done, verification passes." An accepted criterion found incomplete is one of only three things that reopen the work.
> - **DECIDE table.** Each missing criterion is "Required." That leaves two choices: add the work to the current plan, or "stop incomplete unless the owner explicitly narrows or waives the accepted intent."
> - **Anti-pattern.** This is "declaring victory because gates pass." Gates are necessary, not sufficient.
> - **Mode.** This work is full mode. Changing what the shared graph stores fires the persistent-representation trigger. A public result type that outside code builds fires the public-interface trigger. A change to persisted state also makes it high-risk, which adds a `quality-engineer` review on top of `adversarial-reviewer`.
>
> ## What the evidence set needs
>
> Each criterion needs its own proof aimed at that exact property, not a side effect of it:
>
> 1. **Ordinary calls avoid synthetic targets.** A test that resolves ordinary calls and asserts none land on a value node.
> 2. **Default search excludes values.** A default-search test that asserts no value nodes come back.
> 3. **Full and incremental builds agree.** Build the same input both ways and compare the two graphs.
> 4. **A small edit stays within its invalidation bound.** Make a small edit, count what gets invalidated, and check the count against the stated bound. This is a measurement, so record the baseline and the after number with the same command.
> 5. **Delete and rebuild remove values.** Exercise both paths and assert the old value nodes are gone afterward.
> 6. **External construction still compiles.** Compile a consumer outside the crate or package that builds the public result type through the supported path. This is a goal-based check whose "done when" is that the build succeeds.
>
> After that, run GATES again, run the warranted reviewers until no Blocker or Concern remains, emit the `review-verdict.v1` record, and prepare the completion evidence handoff. That handoff lists the six criteria as either proven or still open.
>
> ## Missing tools change nothing
>
> Not having adapt-to-project or code intelligence waives none of this. When dependents evidence is needed, `repository-exploration` gets it from a plain repository search. The proofs above need only the project's normal build and test commands.

### Rebuilt run output (Core 3.1.35)

> No. The work-loop cannot report completion. The tests you have only show that the new synthetic value nodes exist. They do not show that any existing behavior survived. That makes them feature-only evidence, and a preservation property without supporting evidence blocks the "Acceptance criteria satisfied" item on the finish checklist.
>
> ## Why the feature tests do not count
>
> The rule is in `references/preservation-evidence.md` § "When the work stays incomplete". It names four kinds of evidence that do not count: missing, stale, tautological, and feature-only. Your evidence set has two of them:
>
> - **Feature-only:** the creation tests prove only that the new member exists.
> - **Missing:** none of the six preservation criteria has a result.
>
> Passing feature tests also doesn't clear the gates. "Declaring victory because gates pass" is a named anti-pattern.
>
> ## What each criterion needs
>
> Every family a criterion names must be covered. Each oracle (the check that compares what you got with what you expected) must take its expected side from outside the code under test: the base revision, a reading of the input that never calls the implementation, or a written-out table. Each oracle also counts only after it fails on one named single-edit mutation, recorded per `references/mutation-proof.md`.
>
> | Criterion | Family | Mutation the oracle must catch |
> |---|---|---|
> | Ordinary calls avoid synthetic targets | Conservation (base vs head, same inputs) | Drop the step that keeps calls off value nodes |
> | Default search excludes values | Conservation | Drop the default-search exclusion |
> | Full and incremental builds agree | Equivalence (state what "the same" means, and show the comparison can tell two results apart) | Leave one member out of one build |
> | Small edit stays within its invalidation bound | Bounded work (edit one file, report within or over the criterion's stated bound, never a universal count) | Make invalidation cover the whole graph |
> | Delete and rebuild remove values | Lifecycle (production paths, nothing dangling) | Skip cleanup in one path |
> | External construction of the public result type compiles | Compatibility (the repository's own compiler or runtime) | Change one signature or field callers rely on |
>
> Each result must be recorded against the current revision. A result from any other revision is stale. Use the repository's existing tests and gates, and don't add a new harness or tool for this.
>
> ## The missing tools change nothing
>
> `adapt-to-project` and code intelligence are not installed. That does not lower any bar. If a family can't be produced with what the repository already has, its property stays unsatisfied. Only the owner can unblock it, by explicitly narrowing or waiving the criterion. Until then, these criteria are required work, and this loop has to produce the evidence or stop incomplete.
>
> ## What happens next
>
> The work stays at `Status: Implementing`. It returns to EXECUTE to add the six independent, mutation-checked oracles, then runs GATES and REVIEW again.
>
> This change also runs in full mode: it alters a shared structure, and it touches a public result type that outside code constructs. Full mode needs `adversarial-reviewer` with no unresolved Blocker or Concern. It also needs `quality-engineer`, because a structural or persistent-state change counts as high-risk.
