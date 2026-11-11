# Spec: Reproducible preservation authoring on the shared-graph case

- **Status:** Shipped
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
alternate construction paths agree with each other. Every graded run of the
frozen shared-graph case on the rebuilt guidance holds all six of its
assertions.

## What Changes

- `packs/core/.apm/skills/new-spec/references/shared-substrate-preservation.md`
  § When to stop: a reachable consumer that can be read gets a criterion bounded
  by its base-revision output, and an unseen producer of its input becomes an
  assumption marked as bounded by that criterion; a named gap, marked as one, is
  reserved for a reachable class with no buildable oracle.
- The same reference § Where the consumer map lives: the map opens with one
  sentence stating it is working material whose deletion or rebuild changes no
  criterion.
- The same reference § What a preservation criterion adds: when two paths
  build the same structure, the criterion compares their results with the new
  member present, besides comparing each with the base revision.
- New content pins for the three rules in
  `packs/core/tests/skills/new-spec/test_shared_substrate_preservation.py`.
- A Core patch release and its changelog fragment, at the version AC-0008
  states.
- The frozen case `shared-substrate-change-expands-preservation-proof`, its
  fixture, and the negative control
  `isolated-private-change-does-not-expand-preservation-proof` stay unchanged;
  they are this change's eval harness.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | The brief's C3 positive-fixture proof rests on this spec | The brief's Spec map row and its C3 "Pass the integrated positive fixture" bullet; `docs/product/captured/new-spec-positive-case-reproducibility.md` | Platform Core | The row resolves this spec; the bullet links this spec's ledger; the captured item reads `Closed` and has no `[backlog].open` entry | The row derives `Shipped` and the bullet resolves |
| Release history | Any `packs/core/` change ships under a new Core version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a fragment in `docs/product/changelog.d/` | Core pack release maintainers | The version AC-0008 states | AC-0008 and AC-0009 hold |
| Reusable learning | The repeated runs are the reproducibility evidence later work reuses | `notes/verification-ledger.md` in this spec directory | Platform Core | Every graded run made under this spec — the pre-approval spike runs, one base run of each case as the baseline, and every AC-0001 to AC-0004 run — with its output, grade, pack version, and revision | The ledger records every graded run made under this spec |

The adopter guide `guides/core/how-to/plan-and-execute-non-trivial-work.md`
names the path's purpose and links the reference without restating its rules,
so it needs no change.

## Agent Rules

### Always do

- Edit `packs/core/.apm/` sources, then regenerate the projections with
  self-host.
- Keep the reference portable: no catalogue-internal records or repository-only
  paths.
- Record every graded run made under this spec, on every projection; a run
  that misses an assertion is recorded, never dropped or replaced by a rerun.

### Ask first

- Any edit under `packs/core/.apm/skills/new-spec/` other than the reference
  and `evals/`, such as `SKILL.md` or `assets/`, or any edit under
  `packs/core/.apm/skills/work-loop/`. Approval takes a controlled amendment
  that revises AC-0010.

### Never do

- Edit anything under `packs/core/.apm/skills/new-spec/evals/`, including
  weakening, removing, or rewording an eval assertion or editing a fixture to
  make a run pass.
- Add a schema, a new module, a new dependency, or a new reference file.
- Edit a generated projection under `.agents/`, `.claude/`, or `.codex/` by
  hand.

## Testing Strategy

- **Positive and negative runs (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006):** visual / manual QA of
  the rebuilt agent artifact. No CI gate grades eval output, so the behavior is
  proved by graded runs, repeated for the positive case because a single run
  has already passed and then failed to reproduce.
- **Eval harness (AC-0007):** goal-based. The frozen case is the harness for
  all three edits: its assertion 4 covers the gap rule and path agreement, and
  its assertion 5 covers the disposability sentence. On that ground Platform
  Core — owner of brief:repository-grounding-preservation and maintainer of the
  Core pack this change releases — waives `packs/AGENTS.md` § Security and
  authoring rules ("A non-cosmetic pack update also updates that pack's eval
  harness") for this change. Because each edit is a generic rule rather than
  fixture-specific wording, Platform Core also accepts that no held-out
  positive case tests the edits on another substrate. Both were decided
  2026-10-29.
- **Release (AC-0008, AC-0009), scope (AC-0010):** goal-based; one command
  each.

## Acceptance Criteria

Terms:

- **The final rebuilt projection** is `.claude/skills/` and `.claude/agents/`
  after self-host at the commit that carries this spec's last reference edit.
- **A graded run** against a named projection is one fresh agent confined to a
  copy of only that projection's Core entries — the `.claude/skills/` and
  `.claude/agents/` entries whose names appear under `packs/core/.apm/skills/`
  and `packs/core/.apm/agents/` at the same revision — with every `evals/`
  directory and `adapt-to-project` removed. The agent has no Pi and no
  code-intelligence capability. It works over an isolated copy of a case's
  `files`, given only that case's `prompt`; a separate grader receives only the
  output and the case's `assertions`.
- **The base** is `git merge-base origin/main HEAD` after a fresh fetch, with
  every change committed.

- [x] **AC-0001.** Every graded run of
  `shared-substrate-change-expands-preservation-proof` against the final
  rebuilt projection holds all six assertions.
- [x] **AC-0002.** At least three graded runs of
  `shared-substrate-change-expands-preservation-proof` against the final
  rebuilt projection are recorded in `notes/verification-ledger.md`.
- [x] **AC-0003.** Every graded run of
  `isolated-private-change-does-not-expand-preservation-proof` against the
  final rebuilt projection holds all four assertions.
- [x] **AC-0004.** At least one graded run of
  `isolated-private-change-does-not-expand-preservation-proof` against the
  final rebuilt projection is recorded in `notes/verification-ledger.md`.
- [x] **AC-0005.** For every run AC-0001, AC-0002, AC-0003, and AC-0004
  count, the ledger lists the skill and agent entries its copy held, and that
  list equals the entries under `packs/core/.apm/skills/` and
  `packs/core/.apm/agents/` at the run's revision, less `adapt-to-project`;
  and the ledger records the output of `find <copy> -type d -name evals` over
  that copy, which is empty.
- [x] **AC-0006.** For every run AC-0001, AC-0002, AC-0003, and AC-0004
  count, the ledger names the agent type and tool set the run agent was given,
  and that set holds no Pi tool and no code-intelligence capability.
- [x] **AC-0007.** `git diff --exit-code <base> HEAD -- packs/core/.apm/skills/new-spec/evals/`
  exits 0.
- [x] **AC-0008.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  both read the patch version one above `packs/core/pack.toml` at the base.
- [x] **AC-0009.** A `docs/product/changelog.d/` fragment names `core` at the
  version AC-0008 states.
- [x] **AC-0010.** `git diff --name-only <base> HEAD` lists no path under
  `contracts/`, and its only path under `packs/core/.apm/` is
  `packs/core/.apm/skills/new-spec/references/shared-substrate-preservation.md`.

## Follow-ons

- Platform Core: brief:repository-grounding-preservation is ready for
  `close-work` once this spec ships.

## Assumptions

- Technical: no held-out positive case on another substrate — the three
  edits' generality beyond the frozen case they were designed against is
  ungrounded; only the negative control guards against over-triggering.
  Accepted; see Testing Strategy, Eval harness (AC-0007).
