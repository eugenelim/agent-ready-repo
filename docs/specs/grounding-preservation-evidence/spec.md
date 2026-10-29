# Spec: Independent preservation evidence

- **Status:** Implementing
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
- A Core patch release and its changelog fragment, at the version AC-0016
  states.
- The frozen evidence-sufficiency case in `work-loop`'s `evals/` is this
  change's eval harness; it stays unchanged.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Adopters running `work-loop` on a shared-substrate change meet the new reference | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | Platform Core | The paragraph names the reference's purpose and links it, without restating its rules | The guide links the shipped reference path |
| Current product truth | The brief tracks slice delivery | The brief's Spec map row | Platform Core | The coverage roll-up resolves this spec through its `Brief:` line | The row derives `Shipped` |
| Release history | Any `packs/core/` change ships under a new Core version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a fragment in `docs/product/changelog.d/` | Core pack release maintainers | The version AC-0016 states | AC-0016 holds |
| Reusable learning | The graded runs are the measurement C3 reuses | `notes/verification-ledger.md` in this spec directory | Platform Core | The graded and baseline runs' outputs and grades, each with the pack version it ran against | The ledger records the AC-0015 run and its baseline |

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

- **Evidence families and incompleteness (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012):** goal-based.
  The targeted pytest module passes. The evaluator already exists, so a TDD red
  is not available; each oracle's named mutant is the proof that it can fail,
  and AC-0002 makes that proof a criterion.
- **The reference and its routing row (AC-0013, AC-0014):** TDD. Content pins
  are written first and fail while the reference is absent.
- **Evidence-sufficiency case (AC-0015):** visual / manual QA of the rebuilt
  agent artifact. No CI gate grades eval output, so the case runs once as a
  graded run, beside one baseline graded run against the base's
  `.claude/skills/work-loop/` projection. If the baseline also holds all five
  assertions, AC-0015 shows only that the reference does not regress the case,
  and AC-0013 and AC-0014 carry the proof that the reference ships.
- **Release and scope (AC-0016, AC-0017):** goal-based; one command each.

## Acceptance Criteria

Terms:

- **The fixture substrate** is a test-local graph over a small corpus of source
  files whose lines are `def NAME`, `call NAME`, or `value NAME`. It has two
  implementations. **The base implementation** ignores `value` lines. **The
  head implementation** turns each `value` line into a value node.
- **The six properties** are: ordinary calls resolve to no value node; default
  search excludes value nodes; full and incremental construction give the same
  semantic model; a one-file edit stays within its stated invalidation bound;
  value nodes are created, updated, deleted, and rebuilt correctly; the public
  result type's supported construction and destructuring still work. Each
  property has one or more required terms under `all`, and each term has one
  oracle.
- **The queries** are every distinct NAME in the corpus.
- **A production path** is a public operation of an implementation: full
  build, one-file update, one-file removal, rebuild, call resolution, and
  search. A test-only helper that builds or edits internal state is not one.
- **An oracle's named mutation** is one stated source edit whose old text
  occurs exactly once in the head implementation's source and which makes that
  oracle fail. **Its named mutant** is the head source with that edit applied.
- **The producer** is the suite's receipt producer. Its inputs are one oracle
  and one implementation under test, given as source text. It runs the oracle
  on the implementation under test. When that run passes, it applies the
  oracle's named mutation to the same source and runs the oracle again. It
  emits `pass`, or `within-budget` for bounded work, only when the first run
  passes and the second run fails. When the first run fails it emits `fail`,
  or `over-budget` for bounded work. When the mutation's old text does not
  occur in the source, or the second run also passes, it emits `fail`. It emits
  no other outcome.
- **A receipt's fingerprint** is the SHA-256 of the implementation-under-test
  source the producer was given. **The subject fingerprint** is that hash for
  the head source.
- **A store verdict** is the verdict `EvidenceStore.evaluate_verdicts` returns
  for a property after the receipts are appended through `append_receipt`.
- **The base revision** is `git merge-base origin/main HEAD` after a fresh
  fetch, with every change committed.

### Every family

- [ ] **AC-0001.** For each of the six properties, the producer's receipts for
  its terms over the head source, evaluated against the subject fingerprint,
  give a store verdict of `supported`.
- [ ] **AC-0002.** For each term's oracle, run directly on that term's named
  mutant, the oracle returns a failing result, or a count over its bound for bounded work.
  The store verdict over the producer's receipts for all of that property's
  terms with the mutant as the implementation under test, evaluated against the
  mutant's fingerprint, is `insufficient`.

### Each oracle

- [ ] **AC-0003.** Conservation of ordinary calls: the oracle resolves every
  call name in the corpus with the base implementation and with the
  implementation under test, and passes only when, for every call name, the two
  results agree on every field of the base implementation's result type. The
  new field is the allowed delta and is not compared.
- [ ] **AC-0004.** Conservation of default search has two terms. The default
  term runs every query through both implementations' default
  search and passes only when the results are equal. The explicit term runs
  every query through the implementation under test with values requested, and
  passes only when, for each query, the result equals the base
  implementation's default result for that query plus one entry for each
  corpus `value` line whose NAME equals the query. The oracle derives the
  expected value entries from the corpus text, without calling the
  implementation under test. Both terms compare each query's results as
  collections of kind, file, and name that ignore order and keep multiplicity.
- [ ] **AC-0005.** Equivalence: the oracle compares a full build of the edited
  corpus with a full build of the original corpus followed by a one-file update,
  in a semantic form that ignores internal identifiers and insertion order, and
  passes only when the two are equal. Two graphs that differ by a single edge
  compare unequal in that form.
- [ ] **AC-0006.** Lifecycle has four terms, each observed only through
  production paths and compared with value names read from the corpus text:
  create, where a build holds exactly the corpus's value names; update, where
  after a one-file edit the graph holds exactly the edited corpus's value
  names; delete, where after removing a file no node or edge names that file's
  values and the graph holds exactly the remaining corpus's value names; and
  rebuild, where a rebuild holds exactly the current corpus's value
  names.
- [ ] **AC-0007.** Compatibility: the oracle compiles and runs a consumer
  snippet that uses only the base implementation's public result-type fields.
  It builds the type by position and by keyword and destructures it by
  position. It passes only when the snippet raises nothing, a pattern matches,
  and each destructured value equals the value it was built from.
- [ ] **AC-0008.** Bounded work: the receipt has observation type
  `command-result`. The bound is the count of `def` and `value` lines in the
  edited file's text before the edit plus that count after the edit. The oracle
  compares it with the number of nodes the one-file update reports as
  invalidated. The suite's one-file edit gives `within-budget` on the head
  source.

### Incomplete evidence

- [ ] **AC-0009.** Missing: for each of the six properties, with every other
  property's receipts present and its own absent, its store verdict is
  `insufficient`.
- [ ] **AC-0010.** Stale: for each of the six properties, receipts produced over
  an earlier head source that differs only by a behavior-neutral edit carry
  every term's passing outcome and give `supported` against that source's
  fingerprint, and give `insufficient` against the subject fingerprint.
- [ ] **AC-0011.** Tautological: a variant of the ordinary-calls oracle that
  resolves both sides with the implementation under test still passes on the
  named mutant, so the producer emits `fail` and the store verdict is
  `insufficient`.
- [ ] **AC-0012.** Feature-only: the value-creation feature test, run through
  the producer as the oracle for every term of the six properties, using each
  term's named mutation and bound to each property's own ID and term, earns
  `pass` only for the lifecycle create term and `fail` for every other term,
  and leaves every one of the six store verdicts `insufficient`.

### The reference

- [ ] **AC-0013.** Exactly one row in `work-loop` `SKILL.md`
  § Conditional-reference routing links `references/preservation-evidence.md`,
  and its predicate names a preservation property in the accepted criteria.
- [ ] **AC-0014.** `references/preservation-evidence.md` names the five
  evidence families, the rule that an oracle counts only after it fails on a
  named mutation, and the four kinds of incomplete evidence: missing, stale,
  tautological, and feature-only. It links `new-spec`'s shared-substrate
  preservation reference and `work-loop`'s `references/mutation-proof.md`, and
  it names no path under `docs/`.

### Agent behavior, release, and scope

- [ ] **AC-0015.** A graded run of `shared-substrate-feature-tests-do-not-prove-preservation`
  against the rebuilt `.claude/skills/work-loop/` projection holds all five of
  its assertions. A graded run is one fresh agent following a copy of that
  projection with its `evals/` directory removed, given only the case's
  `prompt`, and scored by a separate grader that receives the output and the
  case's `assertions`.
- [ ] **AC-0016.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  both read the patch version one above `packs/core/pack.toml` at the base
  revision, and a `docs/product/changelog.d/` fragment names `core` at that
  version.
- [ ] **AC-0017.** `git diff --name-only <base revision> HEAD` lists no path
  under `contracts/`, `packs/core/.apm/skills/work-loop/scripts/`,
  `packs/core/.apm/skills/work-loop/evals/`, or `packs/core/.apm/agents/`. The
  Agent Rules alone govern the other forbidden surfaces.

## Follow-ons

- Platform Core: brief:repository-grounding-preservation, slice C3 — review
  that binds a sustained finding to the affected preservation property.

## Assumptions

none
