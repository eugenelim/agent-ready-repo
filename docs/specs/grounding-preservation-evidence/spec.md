# Spec: Independent preservation evidence

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

When an agent using an installed Core pack implements a change whose accepted
criteria include preservation properties, `work-loop` tells it how to produce
evidence for each one: conservation, full and incremental equivalence,
lifecycle, compatibility, and bounded work, each from an oracle whose expected
side does not come from the implementation under test and which has been seen
to fail on a named mutation. Success is a fixture suite in which every such
receipt is `supported` through the shipped evidence store, and missing, stale,
tautological, or feature-only evidence leaves every affected property short of
`supported`.

## What Changes

- A conditional reference,
  `packs/core/.apm/skills/work-loop/references/preservation-evidence.md`: what
  counts as independent evidence, the five evidence families and what each
  oracle compares and mutates, how bounded work is reported, and the four ways
  evidence leaves the work incomplete.
- One row in `work-loop` `SKILL.md` § Conditional-reference routing that loads
  the reference when the accepted criteria include a preservation property.
- A pack test module and a small fixture substrate under
  `packs/core/tests/skills/work-loop/` that produce each family's receipts
  through the fixture's production paths, run each oracle against its mutant,
  and decide every property through the shipped evidence store and evaluator.
- One paragraph in `guides/core/how-to/plan-and-execute-non-trivial-work.md`
  naming the path for adopters.
- A Core patch release and its changelog fragment, at the version AC-0013
  states.
- The frozen evidence-sufficiency case in `work-loop`'s `evals/` is this
  change's eval harness; it stays unchanged.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Adopters running `work-loop` on a shared-substrate change meet the new reference | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | Platform Core | The paragraph names the reference's purpose and links it, without restating its rules | The guide links the shipped reference path |
| Current product truth | The brief tracks slice delivery | The brief's Spec map row | Platform Core | The coverage roll-up resolves this spec through its `Brief:` line | The row derives `Shipped` |
| Release history | Any `packs/core/` change ships under a new Core version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a fragment in `docs/product/changelog.d/` | Core pack release maintainers | The version AC-0013 states | AC-0013 holds |
| Reusable learning | The graded runs are the measurement C3 reuses | `notes/verification-ledger.md` in this spec directory | Platform Core | The graded and baseline runs' outputs and grades, each with the pack version it ran against | The ledger records the AC-0012 run and its baseline |

## Agent Rules

### Always do

- Edit `packs/core/.apm/` sources, then regenerate the projections with
  self-host.
- Keep the reference portable: no catalogue-internal records, no
  repository-specific commands, and no language- or tool-specific build
  command presented as required.
- Cite `new-spec`'s shared-substrate preservation reference for criterion
  shape and `work-loop`'s mutation-proof reference for the proof record,
  rather than restating them.
- Drive every verdict in the suite through the shipped
  `EvidenceStore.append_receipt` and `EvidenceStore.evaluate_verdicts`.

### Ask first

- Any `SKILL.md` edit beyond the one routing row.
- Any change under `contracts/` or to a `work-loop` script.

### Never do

- Add a schema, a schema field, a new observation type or outcome term, an
  evaluator or evidence-store change, or a new persistent state record.
- Ship an evidence producer, harness, or gate under `.apm/`; the producer in
  this change is test code.
- Change a reviewer agent definition or reviewer brief.
- State a numeric invalidation bound as a universal limit.
- Let the absence of an optional pack, code-intelligence capability, or
  benchmark tool lower the evidence the reference requires.
- Edit a generated projection under `.agents/` or `.claude/` by hand.

## Testing Strategy

- **Evidence families and incompleteness (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011):** goal-based.
  The targeted pytest module passes. The evaluator already exists, so a TDD red
  is not available; each family's mutant is the proof that its oracle can fail,
  and AC-0002 makes that proof a criterion.
- **Evidence-sufficiency case (AC-0012):** visual / manual QA of the rebuilt
  agent artifact. No CI gate grades eval output, so the case runs once as a
  graded run, beside one baseline graded run against the base's
  `.claude/skills/work-loop/` projection.
- **Release and scope (AC-0013, AC-0014):** goal-based; one command each.

## Acceptance Criteria

Terms:

- **The fixture substrate** is a test-local graph over a small corpus of source
  files with two implementations. **The base implementation** has no synthetic
  value nodes. **The head implementation** adds them and is the implementation
  under test.
- **The six properties** are: ordinary calls resolve to no value node; default
  search excludes value nodes; full and incremental construction give the same
  semantic model; a one-file edit stays within its stated invalidation bound;
  value nodes are created, updated, deleted, and rebuilt correctly; the public
  result type's supported construction and destructuring still work.
- **A production path** is a public operation of the head implementation:
  full build, one-file update, one-file removal, rebuild, call resolution, and
  search. A test-only helper that builds or edits internal state is not one.
- **The named mutant** of a property is the head implementation with one
  stated source edit applied, which breaks that property alone.
- **The producer** is the suite's receipt producer. It runs one oracle against
  the head implementation and against that property's named mutant, and emits
  outcome `pass`, or `within-budget` for bounded work, only when the head run
  passes and the mutant run fails. Otherwise it emits `fail`, `over-budget`, or
  `unproven`.
- **The subject fingerprint** is the SHA-256 of the head implementation's
  source bytes, standing in for the projected acceptance fingerprint.
- **A store verdict** is the verdict `EvidenceStore.evaluate_verdicts` returns
  for a property after the receipts are appended through `append_receipt`.

### Every family

- [ ] **AC-0001.** For each of the six properties, the producer's receipts,
  bound to the subject fingerprint, give a store verdict of `supported`.
- [ ] **AC-0002.** For each of the six properties, with its named mutant as the
  implementation under test, its oracle fails, and the producer's receipts,
  bound to the mutant's fingerprint and evaluated against it, give a store
  verdict other than `supported`.

### Each oracle

- [ ] **AC-0003.** Conservation of ordinary calls: the oracle resolves every
  call name in the corpus with the base implementation and the head
  implementation and requires the two results to be equal, with no allowed
  delta.
- [ ] **AC-0004.** Conservation of default search: the oracle runs every query
  in the corpus through both implementations' default search and requires equal
  results. With values explicitly requested, the head result equals the base
  result plus exactly the matching value nodes.
- [ ] **AC-0005.** Equivalence: the oracle compares a full build of the edited
  corpus with a full build of the original corpus followed by a one-file update,
  in a semantic form that ignores internal identifiers and insertion order. Two
  graphs that differ by a single edge compare unequal in that form.
- [ ] **AC-0006.** Lifecycle: the property requires four terms, create, update,
  delete, and rebuild, under `all`, each observed only through production
  paths. Removing the file that declares a value leaves no node and no edge
  that names it.
- [ ] **AC-0007.** Compatibility: the oracle compiles and runs a consumer
  snippet that builds the public result type by position and by keyword and
  destructures it by position, and passes when the snippet raises nothing.
- [ ] **AC-0008.** Bounded work: the receipt has observation type
  `command-result`. The bound is stated in the fixture's criterion as the
  number of declarations in the edited file before and after the edit, counted
  from the file text rather than from the implementation. An update that
  invalidates more nodes than that bound decides `insufficient`.

### Incomplete evidence

- [ ] **AC-0009.** Missing: for each of the six properties, with every other
  property's receipts present and its own absent, its store verdict is
  `insufficient`.
- [ ] **AC-0010.** Stale: for each of the six properties, receipts produced
  against an earlier head source and bound to that source's fingerprint give a
  store verdict of `insufficient` when evaluated against the current subject
  fingerprint.
- [ ] **AC-0011.** Tautological and feature-only: a conservation oracle whose
  expected side is computed by the head implementation still passes on its
  named mutant, so the producer emits `unproven` and the store verdict is
  `insufficient`. A receipt set holding only value-creation feature receipts,
  bound to a feature criterion, leaves all six store verdicts `insufficient`.

### Agent behavior, release, and scope

- [ ] **AC-0012.** A graded run of `shared-substrate-feature-tests-do-not-prove-preservation`
  against the rebuilt `.claude/skills/work-loop/` projection holds all five of
  its assertions. A graded run is one fresh agent following a copy of that
  projection with its `evals/` directory removed, given only the case's
  `prompt`, and scored by a separate grader that receives the output and the
  case's `assertions`.
- [ ] **AC-0013.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  both read the patch version one above `packs/core/pack.toml` at the base,
  `git merge-base origin/main HEAD` after a fresh fetch, and a
  `docs/product/changelog.d/` fragment names `core` at that version.
- [ ] **AC-0014.** `git diff --name-only <base> HEAD` lists no path under
  `contracts/`, `packs/core/.apm/skills/work-loop/scripts/`,
  `packs/core/.apm/skills/work-loop/evals/`, or `packs/core/.apm/agents/`.

## Follow-ons

- Platform Core: brief:repository-grounding-preservation, slice C3 — review
  that binds a sustained finding to the affected preservation property.

## Assumptions

none
