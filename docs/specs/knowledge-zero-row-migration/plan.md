# Plan: knowledge-zero-row-migration

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/AGENTS.md` (runtime export boundary, self-host
  projection, pack test loader rule) and `packs/core/AGENTS.md`. Analogous
  implementation: `_stage_legacy_migration_locked` and its sibling
  `activate_staged_migration` in
  `packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py`.
  Corresponding tests: `packs/core/tests/skills/project-knowledge/test_migration.py`.
  Named uncertainty: no test in the repository covers the empty-`imports` path,
  so there is no precedent for how a zero-row fixture is built — T2 establishes
  one.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/knowledge-zero-row-migration/notes/verification-ledger.md`.
> A genuine artifact error follows the controlled-amendment path.

## Approach

Two commits. The first repairs the crash and lands the coverage that would have
caught it; the second documents the promotion step and pins it. Order is forced:
the new tests cannot pass before the repair, and the repair's mutation proof is
only meaningful against the tests, so both live in commit one.

The repair is one statement in
`packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py`, placed
inside the existing `try` so the `except Exception:
_clear_staged_migration_unlocked(...); raise` cleanup covers it. That placement
closes a narrow window: `mkdir(parents=True)` can create an intermediate
directory and then fail, and outside the `try` that residue would survive. The
window is real but unreachable from any current hook, so the placement rests on
review rather than on a check — T4 records that rather than claiming a mutation
proof for it.

Test work concentrates in `test_migration.py`. The existing
`_commit_staged_activation` helper copies a `topics` directory, so the zero-row
lifecycle case needs its own commit path rather than a reuse of that helper.

The complete change set bumps the two pack manifests once, in T7, after every
source and seed edit is in place; neither commit bumps independently. T7 also
regenerates the `.claude/` and `.agents/` projections, which is a command, not a
hand edit.

## Constraints

- ADR-0081 fixes the canonical topic representation, so the staged artifact this
  change makes reachable is the existing `knowledge-topic-map.v1` map rather than
  a new empty-state encoding.
- ADR-0082 keeps capture, distillation, and enquiry authority separate. The
  documentation task describes the existing lifecycle and adds no mode, so it
  does not touch that separation.
- `packs/AGENTS.md` § Shipped pack content carries no internal-governance
  citations: the prose added in T5 states the rule directly and cites no spec,
  AC, or repository-only path.
- `packs/AGENTS.md` § Writing pack tests: load the module under a unique name.
  `knowledge_test_support.load_knowledge_store_module()` already does this, so
  new cases reuse it rather than adding a loader.
- `packs/AGENTS.md` § Security and authoring rules requires a non-cosmetic pack
  update to also update that pack's eval harness. This change is non-cosmetic, so
  the obligation does trigger. **The rule's owner waived it for this change on
  2026-09-13**, on the ground that the migration lifecycle is not worth eval
  coverage. Recorded as a waiver, not as a non-trigger: the supporting facts
  below explain why the waiver is cheap to grant, but they do not by themselves
  discharge the rule. The harness at
  `packs/core/.apm/skills/project-knowledge/evals/` measures which prompts select
  this skill and which mode it picks; this change adds no mode, no flag, and no
  frontmatter `description` vocabulary, and the runner `pack.toml` names for it,
  `tools/run-pack-evals.py`, is absent from this checkout, so no row added there
  could be scored.
- Correction, recorded 2026-09-13 during T7: an earlier note here claimed
  self-host has no clean-tree precondition, and that claim was false. It came
  from grepping `catalogue_tooling/self_host.py`, the thin wrapper, instead of
  `build/self_host.py`, the implementation that holds the check. The round-1
  reviewer's sequencing finding was correct on its own premise; the supervisor's
  refutation of it was the error. T7's Approach now carries the real sequence.
- `lint-contract-item-alignment.py` does **not** cover this spec, and its exit 0
  here is not evidence. It is forward-only: it skips any spec whose criteria are
  not labelled `AC-NNNN.`, and it reported this one "skipped as unlabelled". A
  probe against a relabelled scratch copy showed adopting that form also requires
  restructuring Testing Strategy into verification groups — a material edit that
  would invalidate the completed shaping review. Criterion-to-task alignment here
  rests on the four review rounds, not on that lint.
- Commit topology: the crash repair and the documentation change land as separate
  commits. This is delivery guidance, not a product obligation, so it lives here
  rather than in the spec's Boundaries.

## Construction tests

**Integration tests:** T3's lifecycle case is the only one spanning tasks — it
drives stage, promotion, commit, and activation across the git boundary, and so
depends on both the repair and the zero-row fixture.

**Manual verification:** one real invocation of the shipped CLI
(`project_knowledge.py --migrate-legacy`) against a scratch repository with a
zero-byte corpus, reading stdout and the exit code. The Finish checklist's
user-invoked-artifact item is not satisfied by a passing unit test.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — skill body and README seed | T5, T6 | T6's content pin green in the pack suite | Both surfaces name the promote-and-commit step |
| Current product truth — README seed | T5 | Seed and skill body reviewed in one diff | The four-step sequence reads the same in both |
| Release history — pack version | T7 | `pack.toml` and `plugin.json` both read 2.25.20 | PR description names 2.25.20 |
| Reusable learning | closeout | Capture receipt at `plan-locked`, or a recorded `project-knowledge unavailable` | The learning is admitted or explicitly discarded |

## Design (LLD)

`Shape: service` selects interfaces and contracts, behavior and rules, and
failure and edge cases. The others are pruned: no schema moves, no module is
added, and there is no UI.

### Interfaces & contracts

No signature, flag, or schema changes. `stage_legacy_migration` keeps its
`(repo_root, *, inject=None)` shape and its `{"counts", "diagnostics",
"map_digest"}` return. Satisfies AC1, AC3 by making the existing return
reachable for an input partition that previously raised.

### Behavior & rules

The stage root's existence is currently a side effect of writing the first
topic: `_write_staged_topic` calls `path.parent.mkdir(parents=True,
exist_ok=True)`. That coupling is the defect — the directory's lifetime is owned
by a loop that an empty `imports` never enters, while the map write after the
loop assumes it unconditionally. The repair gives the stage root an owner that
does not depend on the loop running. Satisfies AC1, AC2.

### Failure, edge cases & resilience

Two inputs reach the empty-`imports` path and they are not the same case: a
zero-byte corpus (`input_rows == 0`) and a corpus whose every row takes the
`refused` disposition and is skipped before `imports` is populated
(`input_rows == n`, `refused == n`). They differ in the returned counts, which
is why AC3 is separate from AC1 rather than a second assertion inside it.

The existing failure contract is unchanged and stays owned by
`test_ac20_migration_failures_leave_source_and_staging_unchanged`: the three
injected failures must still leave nothing under the stage root. The repair
creates a directory that this contract must clean up, and it still does —
`_clear_staged_migration_unlocked` removes the stage root whoever created it.
Placement inside the `try` therefore matters by review, not by test: no current
hook discriminates it, and T4 records that as a negative result.

## Tasks

### T1: zero-row and all-refused staging return the specified counts and the canonical map

**Depends on:** none

**Touches:** packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py

**Tests:** verified by T2's cases; this task carries no test of its own, and is
separated from T2 only so the mutation proof in T4 has a single statement to
remove.

**Approach:**
- Create the stage root explicitly as the first statement inside the existing
  `try` in `_stage_legacy_migration_locked`, before the topic loop.

**Done when:** T2's zero-row and all-refused cases pass, and the pre-existing
`test_migration.py` cases still pass unchanged.

### T2: the migration harness covers both empty-import partitions

**Depends on:** none

**Touches:** packs/core/tests/skills/project-knowledge/test_migration.py

**Tests:**
Both cases assert AC1, AC2, and AC3 **as written**, comparing against the
criterion text rather than a paraphrase of it. What follows is only the mechanism
the criteria do not give you.

- A zero-byte case (AC1, AC2) and an all-refused case (AC3). Build the
  all-refused input from rows whose `body` is empty or whitespace:
  `_legacy_disposition` returns `refused` on a blank body, which is the only
  disposition route that skips `imports` without refusing the whole run.
- Both cases run the same three assertions over the staged tree, so write them
  once and call them from each case rather than restating them: the returned
  `counts` dict compared whole, the staged path list compared whole against the
  single expected relative path, and the map compared as **raw bytes**. Each
  "compared whole" is load-bearing — a subset assertion on `counts` passes with a
  wrong nonzero import counter, a suffix match on the path passes with the map
  written in the wrong directory, and a parsed-object comparison passes on
  reformatted JSON and on a document with duplicate keys.
- `stub: true` for both — the seam is `store.stage_legacy_migration(repo)`, which
  the existing `store` and `repo` fixtures already reach.

**Approach:**
- Reuse the module-level `repo` and `store` fixtures and the `_write_legacy`
  helper. `_write_legacy` with an empty row list already emits zero bytes.

**Done when:** both cases are green against T1 and red without it.

### T3: the zero-row migration activates end to end

**Depends on:** T1, T2

**Touches:** packs/core/tests/skills/project-knowledge/test_migration.py

**Tests:**
- A lifecycle case: stage, copy the staged map into `docs/knowledge/`, `git add`
  and commit `patterns.jsonl` and `topics.index.json`, take
  `committed_knowledge_snapshot`, then activate. Asserts AC4 as written.
- Assert the directory's absence with `Path.exists()`, not the emptiness of
  `staged_migration_files`: that helper lists files, so a surviving empty
  directory tree satisfies it while AC4 is violated.
- It does not call `_commit_staged_activation`, and does not modify it. That
  helper copies `stage/topics`, which zero-row never creates, and `git add`s a
  path that does not exist. The zero-row case gets its own commit path: changing
  the shared helper would move the regression surface of the four existing AC21
  activation cases for no gain here.

**Approach:**
- Follow the promotion sequence T5 documents, so the test and the prose describe
  one sequence rather than two.

**Done when:** the lifecycle case is green and the four pre-existing AC21
activation cases still pass.

### T4: the repair's placement is proven, not asserted

**Depends on:** T1, T2

**Touches:** docs/specs/knowledge-zero-row-migration/notes/verification-ledger.md

**Tests:**
- Mutation 1 — restore the 2.25.18 staging behaviour by deleting the statement,
  leaving the stage root's existence a side effect of writing a topic. Expect
  T2's zero-row case to fail with an unhandled `FileNotFoundError` naming
  `topics.index.json`. Verifies AC5.
- Mutation 2 — move the statement above the `try` instead of deleting it. The
  whole suite stays green. This is a recorded negative result, not an expected
  red: `_clear_staged_migration_unlocked` removes the stage root whoever created
  it, and the two injected failures that could reach the statement (`privacy`,
  `accounting`) refuse before it. The placement the spec's Boundaries require is
  still correct — it closes the window where `mkdir(parents=True)` creates an
  intermediate directory and then fails — but no current hook reaches that
  window, so the placement rests on review, not on a check. Record the negative
  result rather than inventing a hook that would exist only to be proven by.

**Approach:**
- Restore each mutation by editing. Never `git checkout`, `git reset`, or
  `git stash` — the stash stack is shared across worktrees here.
- Record mutation 1's observed failure and mutation 2's observed all-green in the
  verification ledger.

**Done when:** mutation 1's failure is recorded with its exact message, mutation
2's negative result is recorded, and the tree is back to its post-T1 state.

### T5: the promotion step is documented on both shipped surfaces

**Depends on:** none

**Touches:** packs/core/.apm/skills/project-knowledge/SKILL.md, packs/core/seeds/docs/knowledge/README.md

**Tests:** verified by T6.

**Approach:**
- State the four-step sequence once per surface: migrate, copy the staged
  `docs/knowledge/` tree into `docs/knowledge/`, commit, activate with the
  committed snapshot on stdin.
- Say why the commit is mandatory — `--activate-staged` compares against `HEAD` —
  so a reader can tell the step is a review boundary, not a formality.

**Done when:** both surfaces carry the sequence and T6 is green.

### T6: the documented promotion step is pinned against silent removal

**Depends on:** T5

**Touches:** packs/core/tests/skills/project-knowledge/test_migration.py

**Tests:**
- A case asserting AC6 as written against both surfaces. Derive the expected
  steps from the criterion; do not restate them here.
- Mechanism: locate each surface's migration section by its heading and slice to
  it, then assert the steps appear **within that one slice, in order**. Both
  halves matter, and for opposite reasons — an unsliced or unordered search
  passes on a document where the terms survive scattered across unrelated
  paragraphs and the sequence itself is gone, while a byte- or line-pinned check
  reds on any nearby rewording and gets deleted rather than maintained.
- The copy step is matched on its action only, and the check does not claim to
  validate its operands. Two review rounds established that a regex cannot
  decide them from prose: requiring a destination after a directional word still
  admits "Do not copy the staged `docs/knowledge/` tree into `docs/knowledge/`"
  and refuses the correct "…tree, replacing the current `docs/knowledge/`
  directory". A predicate that admits a negation and refuses a synonym is not
  measuring what it claims. The proxy is named rather than the stronger
  property: the check decides presence and order; whether the copy step names
  the right source and destination rests on review, against the wording AC6
  states.

**Approach:**
- Resolve both paths from the harness's existing `PACK_ROOT` anchor rather than
  a new path constant.

**Done when:** the case is green, and red when either surface's sequence is
removed or reordered.

### T7: the pack release surface matches the change

**Depends on:** T1, T5

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, .claude/skills/project-knowledge/**, .agents/skills/project-knowledge/**

**Tests:** goal-based — `agentbundle catalogue lint --root . --deep` and
`agentbundle catalogue verify --root .` pass, and the self-host projection
re-run produces no further diff.

**Approach:**
- Bump both version files to 2.25.20 once every `.apm/` and `seeds/` edit from T1
  and T5 is in place.
- **Commit the source changes before running self-host.** `agentbundle catalogue
  self-host --write` refuses a dirty working tree — `build/self_host.py:1307`,
  "working tree is dirty — refusing to write", exit 1. `--force` overrides that
  check alone; do not use it here, because the refusal is doing its job. The
  separate `CAT-SH-001` guard is unrelated: it refuses a `packs` path pointing
  into a fixture tree.
- Then run `agentbundle catalogue self-host --root . --write` and commit the
  regenerated projections. Delivery is therefore: source commit, projection
  commit, and the documentation commit, in that order.

**Done when:** both version files read 2.25.20, a second self-host run is a
zero diff, and the catalogue gates pass.

## Rollout

Pure-logic and documentation change with no infrastructure, external system, or
sequencing dimension. Delivery is a pack version bump; rollback is reverting the
commits, and nothing is irreversible — the repair only makes a previously
crashing path produce the artifact the lifecycle already specified.

## Risks

- The content pin in T6 is prose-coupled. If it is written against a long quoted
  sentence it will red on ordinary editing and be deleted. Mitigated by pinning
  semantic tokens, and visible because T6 states the failure mode it must avoid.
- Self-host projection drift: editing `.apm/` without regenerating leaves the
  `.claude/` and `.agents/` copies stale, which some gates read. Mitigated by
  T7's zero-diff re-run.
- Splitting delivery across two commits while the version bumps once means the
  first commit is not independently installable. Accepted: both land in one PR,
  and the pack is released from the merged state, not from an intermediate commit.

## Changelog

- 2026-09-13: Drafted.
- 2026-09-13: T4 corrected before review. A pre-review probe disconfirmed the
  drafted claim that moving the statement above the `try` would red the
  failure-residue control; it does not, and the plan now records that as a
  negative result with the reason.
- 2026-09-13: Round 1 shaping and adversarial review. Ten Concerns and two Nits
  sustained and repaired across the spec and plan. One reviewer premise was
  refuted first: self-host has no clean-tree precondition, so that finding was
  repaired by deleting a false claim of mine rather than by resequencing T7.
- 2026-09-13: Round 2 delta review, no Blocker. Three Concerns and one Nit, all
  one failure class — the round-1 criterion repairs left the plan's companion
  `Tests:` bullets pinned to the weaker assertions. Every `Tests:` bullet was
  walked against the repaired criteria, not only the two cited. The eval-harness
  obligation is now recorded as an owner waiver rather than as my own
  non-trigger reasoning.
- 2026-09-13: Round 3 delta review, no Blocker, three Concerns — the same class
  for the third round running. Repaired structurally rather than by tightening
  the prose again: the plan's `Tests:` bullets were paraphrasing the criteria,
  which is a second home for each fact with nothing keeping the two in sync, so
  each round found a fresh paraphrase that had drifted. The bullets now assert
  the criteria as written and carry only mechanism. This is a claim-shrinking
  repair, not another round of assertion.
- 2026-09-13: T7 corrected in place. Self-host does refuse a dirty tree
  (`build/self_host.py:1307`), so the plan now names the commit-before-projection
  sequence that round 1 asked for and the supervisor wrongly dismissed.
- 2026-09-13: T6's check shrunk after three quality-engineer rounds on that one
  control. Rounds 1 and 2 were real defects; round 3 proved the operand claim
  unmechanizable in prose and advised SHRINK. The control now asserts presence
  and order, which it can decide, and the operand wording moved to review. Two
  holes in one control across two rounds is the signal to shrink the claim
  rather than harden it a third time.
