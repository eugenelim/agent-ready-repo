# Spec: Preservation properties from a bounded consumer map

- **Status:** Shipped
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** brief:repository-grounding-preservation
- **Discovery:** none
- **Depends on:** spec:grounding-preservation-contract-proof
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

When a spec author using an installed Core pack proposes a new or changed
member of a shared substrate — a model, registry, graph, index, schema,
namespace, or collection that existing generic operations observe without
opt-in — `new-spec` finds each existing behavior class the member can disturb
from repository files alone and authors one preservation criterion per class,
each with an allowed delta and an oracle that fails if the old behavior moves.
A private single-caller helper, or a new entity that every generic path already
excludes behind an explicit filter, gets no consumer map and no extra criteria.

## What Changes

- A conditional reference,
  `packs/core/.apm/skills/new-spec/references/shared-substrate-preservation.md`:
  the firing predicate and its two exclusions, the behavior classes to check,
  the stop rule by behavior class, the shape of a preservation criterion, where
  the consumer map lives, and how a later discovery is routed.
- One pointer in `new-spec` `SKILL.md` step 3 that loads the reference when the
  predicate fires.
- A pack test proving that deleting or rebuilding a plan-resident consumer map
  leaves the acceptance fingerprint and verdict unchanged.
- One paragraph in `guides/core/how-to/plan-and-execute-non-trivial-work.md`
  naming the path for adopters.
- A Core patch release and its changelog fragment, at the version AC-0005
  states.
- The frozen shared-substrate case and its private-helper negative control,
  already in `new-spec`'s `evals/`, are this change's eval harness; they stay
  unchanged.

Criterion selection and set building have no shipped `new-spec` home beyond
`assets/spec.md` § Acceptance Criteria and the authoring rubric.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Adopters running `new-spec` meet the new path | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | Platform Core | The paragraph names the predicate's purpose and links the reference, without restating its rules | The guide links the shipped reference path |
| Current product truth | The brief tracks slice delivery | The brief's Spec map row | Platform Core | The coverage roll-up resolves this spec through its `Brief:` line | The row derives `Shipped` |
| Release history | Any `packs/core/` change ships under a new Core version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a fragment in `docs/product/changelog.d/` | Core pack release maintainers | The version AC-0005 states | AC-0005 holds |
| Reusable learning | The baseline and shipped runs are the measurement later slices reuse | `notes/verification-ledger.md` in this spec directory | Platform Core | The four graded runs' outputs and grades, each with the pack version it ran against | The ledger records the AC-0001 and AC-0002 runs and both baseline runs |

## Agent Rules

### Always do

- Edit `packs/core/.apm/` sources, then regenerate the projections with
  self-host.
- Keep the reference portable: no catalogue-internal records or repository-only
  paths.
- Defer criterion shape to `new-spec`'s `assets/spec.md` § Acceptance Criteria
  and its authoring rubric; cite them rather than restating them.

### Ask first

- Any `SKILL.md` edit beyond the step-3 pointer.
- Any change under `contracts/` or to a `work-loop` script.

### Never do

- Add a schema, a schema field, a projector or evaluator change, or a new
  persistent state record.
- Add a repository index, stored topology, or a code-intelligence dependency.
- Add evidence implementation patterns or reviewer enforcement.
- Edit a generated projection under `.agents/` or `.claude/` by hand.

## Testing Strategy

- **Positive and negative runs (AC-0001, AC-0002):** visual / manual QA of
  the rebuilt agent artifact. No CI gate grades eval output, so each case runs
  once, as a graded run. A baseline graded run of each case against the base's
  `.claude/skills/new-spec/` projection is recorded beside it to show what the change moves.
- **Map deletion (AC-0003):** behavior pin of the shipped file-based subject
  projector and `_acceptance.evaluate_verdict`, over a temporary git
  repository. The projector already holds the property, so the pin guards the
  behavior this slice's rule relies on; the spec-resident mutation is the case
  that proves the comparison can fail.
- **Trigger controls unchanged (AC-0004), release (AC-0005), scope
  (AC-0006):** goal-based; one command each.

## Acceptance Criteria

Terms:

- **The rebuilt projection** is `.claude/skills/new-spec/` after self-host at
  this spec's Core version.
- **A graded run** against a named `new-spec` projection is one fresh agent
  following a copy of that projection with its `evals/` directory removed, over an isolated copy of a
  case's `files`, given only that case's `prompt`, and scored by a separate
  grader that receives the output and the case's `assertions`.
- **The base** is `git merge-base origin/main HEAD` after a fresh fetch, with
  every change committed.

- [x] **AC-0001.** A graded run of `shared-substrate-change-expands-preservation-proof`
  against the rebuilt projection holds all six of its assertions.
- [x] **AC-0002.** A graded run of `isolated-private-change-does-not-expand-preservation-proof`
  against the rebuilt projection holds all four of its assertions.
- [x] **AC-0003.** In a committed spec directory, a `plan.md` carrying a
  consumer map, the same plan with the map deleted, and the plan with the map
  rebuilt in a different row order each give the same acceptance fingerprint,
  and `evaluate_verdict` over one property with a receipt bound to that
  fingerprint decides `supported` for all three; the same map added to
  `spec.md` instead decides `insufficient`.
- [x] **AC-0004.** `git diff --exit-code <base> HEAD -- packs/core/.apm/skills/new-spec/evals/`
  exits 0.
- [x] **AC-0005.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  both read the patch version one above `packs/core/pack.toml` at the base,
  and a `docs/product/changelog.d/` fragment names `core` at that version.
- [x] **AC-0006.** `git diff --name-only <base> HEAD` lists no path under
  `contracts/` or `packs/core/.apm/skills/work-loop/`.

## Follow-ons

- Platform Core: brief:repository-grounding-preservation, slice C2 — evidence
  that satisfies the preservation criteria this slice authors.
- Platform Core: brief:repository-grounding-preservation, slice C3 — review
  that binds a sustained finding to the affected preservation property in the
  projected record.

## Assumptions

none
