# Spec: Reproducible preservation authoring on the shared-graph case

- **Status:** Draft
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** brief:repository-grounding-preservation
- **Discovery:** none
- **Depends on:** spec:grounding-preservation-authoring
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

A spec author following an installed Core pack's `new-spec` on a
shared-substrate change marks the consumer map as disposable working material,
writes a bounded preservation criterion for every reachable consumer it can
read even when code that feeds that consumer is out of view, and proves that
alternate construction paths agree with each other. Every graded run
of the frozen shared-graph case on the rebuilt guidance holds all six of its
assertions, so one lucky run no longer stands in for the brief's positive proof.

## What Changes

- `packs/core/.apm/skills/new-spec/references/shared-substrate-preservation.md`
  § When to stop: a reachable consumer that can be read gets a criterion bounded
  by its base-revision output, and an unseen producer of its input becomes an
  assumption beside that criterion; a named gap is reserved for a reachable class
  with no buildable oracle.
- The same reference § Where the consumer map lives: the map opens with one
  sentence stating it is working material whose deletion or rebuild changes no
  criterion.
- The same reference § What a preservation criterion adds: when two paths
  build the same structure, the criterion compares their results with the new
  member present, besides comparing each with the base revision.
- New content pins for the three rules in
  `packs/core/tests/skills/new-spec/test_shared_substrate_preservation.py`.
- A Core patch release and its changelog fragment, at the version AC-0004
  states.
- The frozen case `shared-substrate-change-expands-preservation-proof`, its
  fixture, and the negative control
  `isolated-private-change-does-not-expand-preservation-proof` stay unchanged;
  they are this change's eval harness.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | The brief's C3 positive-fixture proof rests on this spec | The brief's Spec map row and its C3 "Pass the integrated positive fixture" bullet; `docs/product/captured/new-spec-positive-case-reproducibility.md` | Platform Core | The row resolves this spec; the bullet links this spec's ledger; the captured item reads `Closed` and has no `[backlog].open` entry | The row derives `Shipped` and the bullet resolves |
| Release history | Any `packs/core/` change ships under a new Core version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a fragment in `docs/product/changelog.d/` | Core pack release maintainers | The version AC-0004 states | AC-0004 holds |
| Reusable learning | The repeated runs are the reproducibility evidence later work reuses | `notes/verification-ledger.md` in this spec directory | Platform Core | Every graded run's output and grade, with the pack version and revision it ran against | The ledger records every AC-0001 and AC-0002 run and both base baselines |

The adopter guide `guides/core/how-to/plan-and-execute-non-trivial-work.md`
names the path's purpose and links the reference without restating its rules,
so it needs no change.

## Agent Rules

### Always do

- Edit `packs/core/.apm/` sources, then regenerate the projections with
  self-host.
- Keep the reference portable: no catalogue-internal records or repository-only
  paths.
- Count every graded run on the final rebuilt projection; a run that misses an
  assertion is recorded, never dropped or replaced by a rerun.

### Ask first

- Any edit to a `new-spec` file other than the reference, including `SKILL.md`,
  `assets/`, and `evals/`.
- Any edit under `packs/core/.apm/skills/work-loop/`.

### Never do

- Weaken, remove, or reword an eval assertion, or edit an eval fixture, to make
  a run pass.
- Add a schema, a new module, a new dependency, or a new reference file.
- Edit a generated projection under `.agents/`, `.claude/`, or `.codex/` by
  hand.

## Testing Strategy

- **Positive and negative runs (AC-0001, AC-0002):** visual / manual QA of the
  rebuilt agent artifact. No CI gate grades eval output, so the behavior is
  proved by graded runs, repeated for the positive case because a single run
  has already passed and then failed to reproduce. One base graded run of each
  case is recorded beside them as the baseline.
- **Harness unchanged (AC-0003), release (AC-0004), scope (AC-0005):**
  goal-based; one command each.

## Acceptance Criteria

Terms:

- **The final rebuilt projection** is `.claude/skills/` and `.claude/agents/`
  after self-host at the commit that carries this spec's last reference edit.
- **A graded run** against a named projection is one fresh agent confined to a
  copy of that projection's Core skills and agents, with every `evals/`
  directory and `adapt-to-project` removed, working over an isolated copy of a
  case's `files` and given only that case's `prompt`; a separate grader
  receives only the output and the case's `assertions`.
- **The base** is `git merge-base origin/main HEAD` after a fresh fetch, with
  every change committed.

- [ ] **AC-0001.** At least three graded runs of
  `shared-substrate-change-expands-preservation-proof` against the final
  rebuilt projection are recorded, and every graded run of that case against it
  holds all six assertions.
- [ ] **AC-0002.** At least one graded run of
  `isolated-private-change-does-not-expand-preservation-proof` against the
  final rebuilt projection is recorded, and every graded run of that case
  against it holds all four assertions.
- [ ] **AC-0003.** `git diff --exit-code <base> HEAD -- packs/core/.apm/skills/new-spec/evals/`
  exits 0.
- [ ] **AC-0004.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  both read the patch version one above `packs/core/pack.toml` at the base,
  and a `docs/product/changelog.d/` fragment names `core` at that version.
- [ ] **AC-0005.** `git diff --name-only <base> HEAD` lists no path under
  `contracts/`, and its only path under `packs/core/.apm/` is
  `packs/core/.apm/skills/new-spec/references/shared-substrate-preservation.md`.

## Follow-ons

- Platform Core: brief:repository-grounding-preservation is ready for
  `close-work` once this spec ships.

## Assumptions

none
