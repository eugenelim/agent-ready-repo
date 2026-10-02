# Brief: preserve existing behavior when Core changes shared repository substrates

- **Slug:** `repository-grounding-preservation`
- **Received:** 2026-10-01
- **Owner:** Platform Core
- **Status:** Ready
- **Cut-closed:** <!-- Set only after the final slice cut and its evidence are confirmed. -->
- **Source / provenance:** Maintainer corrections to `mikeparcewski/wicked-estate`
  PR 207, comparing original commit `3124d82` with corrected commit `3257648`,
  plus the acceptance-centered work-loop architecture and brief at pi-mono
  revision `a673299cea2e2cd070b1649827b2b5a78ca4f42f`.

> **Ready boundary.** This brief records the outcome, contract-fit spike, and
> unconfirmed candidate slices. It creates no delivery spec. The `Spec map`
> stays empty until the owner separately confirms a slice cut.

## Outcome

Core recognizes when a change adds or alters a member of a shared repository
substrate: a model, registry, graph, index, schema, namespace, or collection
that existing code interprets generically. Before implementation, it derives a
bounded map of affected consumer classes and turns the existing behavior that
must survive into accepted preservation properties with admissible evidence.

The workflow works in a locally installed Core pack without
`adapt-to-project`, code intelligence, Pi, a repository index, or whole-repo
ingestion. Optional capabilities may accelerate discovery, but their absence
cannot weaken acceptance, review, or completion.

## Success metrics

- A frozen PR-207-shaped evaluation causes authoring to state preservation
  properties for ordinary call resolution, default search, full versus
  incremental equivalence, edit invalidation scope, value lifecycle cleanup,
  and supported public API compatibility.
- The same evaluation derives the relevant consumer classes through bounded
  repository-native reads and searches, without `adapt-to-project` or a code
  intelligence provider.
- A feature-only test set is insufficient when an accepted preservation
  property lacks current evidence; existing behavior is not inferred from the
  presence of new behavior.
- Deleting or rebuilding the consumer-map or task projection changes neither
  accepted scope nor the acceptance verdict.
- A private helper refactor and an isolated entity behind an explicit filter do
  not trigger the full shared-substrate path.
- Core's dependency, bundle, and default-selection checks pass with Pi,
  `adapt-to-project`, and code intelligence absent.

## Scope / Non-goals

**In scope:**

- A conditional shared-substrate trigger during spec and plan authoring.
- Approval-bound preservation properties and evidence policies for existing
  behavior that a change can disturb.
- A bounded, disposable consumer map grouped by behavior rather than a fixed
  number of nearby files.
- Conservation, alternate-path equivalence, lifecycle, compatibility, and
  bounded-work verification patterns for derived repository state.
- Reviewer-local checks for missed reachable consumers and weak preservation
  evidence, expressed through the generic typed review boundary.
- One integrated evaluation based on the failure classes exposed by PR 207,
  including negative controls that keep the trigger precise.

**Non-goals:**

- A general code search, semantic retrieval, symbol-index, or code-graph
  capability.
- Requiring or installing `adapt-to-project`, code intelligence, Pi, or any
  other optional pack or runtime.
- A static repository-topology index, ownership catalogue, or hand-maintained
  consumer inventory.
- Reviewer-specific orchestration, prompts, role branches, or finding
  taxonomies inside `work-loop`.
- A new workflow engine, reviewer, skill, persistent state record, or approval
  authority.
- Making a large real-repository benchmark mandatory for every shared-model
  change.

## Constraints / Appetite

- Reuse `new-spec`, `work-loop`, operational-safety, and the existing reviewer
  roles. Add a new mechanism only if the existing acceptance and evidence
  contracts cannot express the required property.
- Accepted criteria and their evidence policies own preservation. Plans,
  consumer maps, test shapes, and task projections remain replaceable means.
- Discover consumers with repository-native evidence: effective guidance,
  direct readers and writers, constructors, serializers, update paths, tests,
  manifests, compilers, and repository gates. Stop when each distinct consumer
  class has an oracle or a named gap.
- A newly discovered consumer that changes accepted behavior, scope, a public
  contract, a durable output, or accepted risk routes through its owning
  amendment and fresh initial review. A discovery that only improves task
  order, decomposition, local method, or test shape does not gain approval
  authority.
- Complete the capability before acceptance-centered Slice 4 transfers
  procedure ownership to the supervisor. Do not expand the already approved
  Slice 1 implementation unless its evaluator cannot represent a required
  preservation property.
- Prefer one contract-proof slice and three independently shippable behavior
  slices rather than one broad grounding rewrite.

## Contract-fit spike — 2026-10-01

The spike tested whether the pi-mono Slice 1 contracts can represent the six
preservation properties exposed by PR 207. It inspected
`acceptance-property.v1`, `evidence-receipt.v1`, the acceptance/evidence
architecture, and the approved Slice 1 construction plan at revision
`a673299cea2e2cd070b1649827b2b5a78ca4f42f`.

| Preservation property | Proposed observation | Contract fit | Remaining proof |
| --- | --- | --- | --- |
| Ordinary `Calls` do not acquire synthetic-value targets | `test-result` from a differential resolver fixture | Fits: one stable property, exact-subject freshness, `pass`/`fail` outcomes, review failure as contradiction | Run through the Slice 1 projector and evaluator after they exist |
| Default search excludes synthetic values unless requested | `test-result` from default and explicit-query fixtures | Fits with the same exact-subject policy | Prove the fixture uses the real default query path |
| Full and incremental builds produce the same semantic model | `test-result` from an equivalence harness | Fits as one required observation term | Define semantic equality outside the evidence schema and mutation-test it |
| A one-file edit stays within its accepted invalidation budget | normalized `benchmark-result` or repository gate result | Schema fits because observation types and outcomes are policy-defined strings | Slice 1 evaluator must prove it accepts the normalized producer and outcome vocabulary |
| Added values are contained, reachable, updated, and removable | `test-result` from create/update/delete/rebuild fixtures | Fits as lifecycle evidence over the selected artifacts | Prove deletion and rebuild through production construction paths |
| Existing supported Rust consumers still compile | `command-result` from a downstream compile fixture | Fits as compatibility evidence | Name the supported construction and destructuring surface in the criterion |

**Spike verdict:** no Slice 1 schema amendment is justified by the six cases.
`acceptance-property.v1` already carries a stable criterion identity, artifact
selector, required observation terms, producer class, normalized outcomes,
freshness, satisfaction, and contradiction. `evidence-receipt.v1` binds one
producer observation to one criterion term, and the reserved supported review
failure can contradict the affected property.

The fit is proven only at the architecture and schema level. The Slice 1 plan
still marks the projector/evaluator API as implementation-discovered, and no
evaluator exists at the pinned revision. An attempted executable sample-record
validation was refused by the managed environment because inline code in the
pi-mono worktree lacked an action-specific execution approval. This did not
change repository state. Evaluator-level construction and mutation tests remain
C0's first delivery gate.

## Light-mode reductions pulled forward — 2026-10-01

The current Core change establishes the measurement floor without changing
skill guidance or waiting for the acceptance-centered contracts:

- `new-spec` has a fixture-backed shared-substrate case that must discover the
  generic consumers from repository files rather than repeat them from the
  prompt.
- The paired private-helper fixture is a negative control against turning the
  trigger into generic “search more” ceremony.
- `work-loop` has a separate evidence-sufficiency case that refuses completion
  when creation tests pass but the accepted preservation properties have no
  matching evidence.
- Construction tests keep the fixtures present and parseable, keep the positive
  prompt free of the expected consumer list, and keep all six PR-207-shaped
  preservation classes in the expected results.

This removes evaluation design from all three later behavior outcomes. C1 no
longer needs to invent its trigger control or first consumer-discovery fixture,
C2 no longer needs to define the feature-only completion failure, and C3 can
reuse the frozen cases instead of building an integrated benchmark first.

More work can stay in light mode when it measures or pins a contract without
changing shipped procedure:

1. Run the paired behavior cases against the current `new-spec` and store the
   outputs as a baseline. Add one mutation variant only if the baseline shows
   that a consumer class is visible from wording rather than repository
   evidence.
2. Once acceptance-centered Slice 1 lands, add valid, invalid, and mutated
   preservation-property and evidence-receipt samples directly to its existing
   evaluator tests. This is C0 evidence, not a schema or guidance change, unless
   a sample proves inexpressible.
3. Once Slice 2 fixes the typed review vocabulary, add report fixtures for a
   missed reachable consumer and weak preservation evidence. This can remove
   report-shape design from C3 before reviewer behavior changes.

Do not pre-author the Slice 1 producer vocabulary or the Slice 2 report fields
here. Those are inputs from the other brief. Guessing them would create a
parallel contract and turn a light measurement change into a full amendment.

## Candidate delivery slices — not confirmed

The four candidates below are outcome slices, not component batches. Each can
ship with its own observable proof and leave the repository usable. Their labels
are local to this brief and do not renumber the acceptance-centered work.

### C0 — prove the preservation records through the acceptance evaluator

**Outcome:** The shipped acceptance projector and evaluator can represent and
decide the six PR-207-shaped preservation properties without a grounding-specific
schema or authority path.

**Required input:** The merged acceptance-centered Slice 1 revision, including
the final `acceptance-property.v1` and `evidence-receipt.v1` schemas, projector
and evaluator entry points, producer vocabulary, normalized outcomes, freshness
rules, and contradiction behavior. The schema-level spike in this brief is the
starting evidence, not a substitute for that input.

**Included work and proof:**

- Build valid property-and-receipt samples for ordinary-call isolation,
  default-search exclusion, full/incremental equivalence, bounded invalidation,
  lifecycle removal, and supported public compilation.
- Prove rejection for a missing required term, wrong subject, stale receipt,
  unsupported outcome, and contradiction.
- Mutate each representative sample so the evaluator or its named oracle is
  shown to fail for the intended reason.
- Record whether `benchmark-result` or another existing producer term carries
  bounded-work evidence. If no existing term can, stop and route an amendment
  to the acceptance-centered owner before any Core guidance changes.

**Excluded:** `new-spec` guidance, consumer discovery, operational-safety
patterns, reviewer behavior, and any new persistent state.

**Completion boundary:** Targeted evaluator tests pass for valid, invalid, and
mutated samples, and the result records either “existing contract sufficient”
or an upstream amendment reference. This test-only slice is independently
shippable.

### C1 — author preservation properties from a bounded consumer map

**Outcome:** `new-spec` recognizes a shared-substrate change, discovers the
existing behavior classes it can disturb with repository-native evidence, and
authors accepted preservation properties without taxing an isolated local
change.

**Required input:** C0 is green. Reuse the criterion-selection and set-building
rules owned by `docs/product/briefs/agent-authoring-input-quality.md`; do not
copy them. Treat `docs/product/briefs/internal-repo-topology.md` as the owner of
reusable repository topology; this slice owns only a task-local disposable map.

**Firing predicate:** The path fires when a proposed addition or change becomes
a member of a model, registry, graph, index, schema, namespace, or collection
that existing generic operations can observe without an explicit opt-in. It
does not fire for a private single-caller helper or for a new entity whose
existing generic paths already exclude its kind behind an explicit filter.

**Included work and proof:**

- Inspect direct readers and writers, selection and resolution, default search
  or presentation, ranking and traversal, full and alternate construction,
  invalidation and update, lifecycle and cleanup, serialization, and supported
  public compatibility when those classes are reachable.
- Stop when every distinct reachable behavior class has an accepted
  preservation property with an allowed delta and falsifiable oracle, or a
  named gap that blocks review. The stop rule is by behavior class, never by a
  fixed file or analogue count.
- Keep the consumer map in replaceable plan or review material. Deleting and
  rebuilding it cannot alter accepted scope or the acceptance verdict.
- Route a newly discovered change to accepted behavior, scope, a public
  contract, durable output, or accepted risk through its owning amendment and
  fresh initial review. Local task order and test-shape discoveries remain
  plan changes.
- Pass the fixture-backed shared-graph evaluation and the isolated-helper
  negative control already carried by `new-spec`.

**Excluded:** A repository index, stored topology, code-intelligence dependency,
new acceptance schema, evidence implementation patterns, and reviewer
enforcement.

**Completion boundary:** A locally installed Core pack derives the six
consumer classes from the positive fixture, avoids the negative trigger, and
authors the matching preservation properties using only repository-native
reads and searches.

### C2 — produce independent preservation evidence

**Outcome:** An implementation cannot complete a shared-substrate change on
feature evidence alone; it produces criterion-matched conservation,
equivalence, lifecycle, compatibility, and bounded-work evidence through
existing operational-safety and repository-gate seams.

**Required input:** C1 supplies accepted preservation properties and their
allowed deltas. Use the acceptance evidence contract proven by C0.

**Included work and proof:**

- Define a differential conservation oracle whose expected side does not reuse
  the implementation under test.
- Define semantic equality for full and incremental construction, then mutate
  one path to prove the comparison can fail.
- Exercise create, update, delete, and rebuild through production lifecycle
  paths rather than fixture-only helpers.
- Measure a one-file edit against the criterion's accepted invalidation bound;
  do not turn the PR-207 counts into universal limits.
- Compile the supported external construction or destructuring surface named
  by the compatibility property.
- Make missing, stale, tautological, or feature-only evidence leave the work
  incomplete. Pass the existing `work-loop` evidence-sufficiency evaluation.

**Excluded:** New gate infrastructure, repository-specific commands in portable
Core guidance, reviewer prompt changes, and any weakening when optional tools
are absent.

**Completion boundary:** Each evidence family has a production-path fixture or
repository-gate example, a mutation that proves its oracle can fail, and a
current receipt that the acceptance evaluator attributes to the right property.

### C3 — enforce preservation through typed review

**Outcome:** Existing opaque reviewers report a missed reachable consumer or
weak preservation evidence against the affected accepted property, and the
integrated PR-207-shaped evaluation passes without reviewer-specific branches
in `work-loop`.

**Required input:** C2 is green. The merged acceptance-centered Slice 2 revision
must supply the final typed report, finding identity, affected-criterion, and
review-failure vocabulary. This slice must finish before acceptance-centered
Slice 4 transfers procedure ownership to the supervisor.

**Included work and proof:**

- Give the adversarial review path the shared-substrate reachability question
  and the quality review path the oracle-independence and evidence-sufficiency
  question, while keeping reviewer implementations opaque to `work-loop`.
- Express findings only through the generic typed review boundary and bind a
  preservation failure to its affected criterion. Do not add a grounding-only
  finding taxonomy or orchestration branch.
- Prove that deleting and rebuilding the consumer map or task projection cannot
  change accepted scope, reviewer authority, or the final verdict.
- Pass the integrated positive fixture, the isolated-change negative control,
  and a weak-evidence case with Pi, `adapt-to-project`, and code intelligence
  absent.

**Excluded:** New reviewer roles, supervisor migration, review authority,
project-knowledge storage, and code-graph requirements.

**Completion boundary:** Both reviewer lenses emit the final Slice 2 report
shape, the generic work-loop path consumes it unchanged, the integrated
evaluation passes, and Core's dependency and default-selection tests remain
green without optional packs.

## Ordering with the acceptance-centered brief

1. Acceptance-centered Slice 1 lands, then C0 proves its concrete evaluator
   against the preservation samples.
2. C1 follows C0. C2 follows C1 and may run while the acceptance-centered
   review and knowledge slices continue.
3. C3 waits for both C2 and the acceptance-centered Slice 2 typed review
   boundary, then completes before acceptance-centered Slice 4 supervisor
   inversion.

No candidate is confirmed by this ordering. A Ready transition and a later,
separate owner decision still control which candidate becomes a spec.

## Relationships to existing work

- `agent-authoring-input-quality` owns general acceptance-criterion selection,
  set construction, and its conditional ownership survey. This brief owns the
  narrower trigger and proof for shared-substrate preservation; it must reuse
  that authoring contract rather than create a competing rubric.
- `internal-repo-topology` asks how repository-specific structural facts reach
  an agent without gate failure. This brief does not create that topology. Its
  bounded consumer map is task-local and disposable.
- The acceptance-centered work-loop brief in the pi-mono worktree owns
  acceptance authority, evidence, typed review, and supervisor migration. This
  brief consumes those boundaries and must complete before supervisor
  inversion; it does not join or renumber that migration's eight slices.
- The code-graph review benchmark remains a separate question about review-time
  finding yield. Neither a favorable benchmark nor a code-intelligence install
  is a prerequisite here.

## Assumptions / Risks

- **Assumption:** Slice 1's eventual evaluator preserves the schema's open
  observation vocabulary and can normalize a bounded-work result without a
  schema change. C0 must disconfirm this before authoring changes land.
- **Assumption:** A behavior-class stop rule finds materially distinct
  consumers more reliably than the current fixed one-or-two-analogue rule while
  remaining bounded.
- **Risk:** The shared-substrate trigger becomes a generic “search more” rule
  and taxes ordinary edits. Negative controls and a precise discriminator must
  fail that expansion.
- **Risk:** A differential test becomes tautological because expected and
  actual results use the same implementation. Quality review must require an
  independent baseline or a mutation that proves the oracle can fail.
- **Risk:** The consumer map becomes hidden authority. Cache-deletion and
  reprojection tests must show that its loss cannot change accepted scope or
  the derived verdict.
- **Risk:** The brief duplicates `agent-authoring-input-quality` or
  `internal-repo-topology`. Their ownership boundaries above must survive
  shaping review, or this work should route into an existing owner instead of
  becoming Ready.
- **Risk:** Waiting until after supervisor inversion bakes weak planning into
  the new procedure owner; changing Slice 1 while it is already implementing
  expands a reviewed contract unnecessarily. The C0-before-C1 and
  C3-before-Slice-4 gates hold that middle path.

## Materialization dependencies

- The pinned pi-mono revision is accepted as provisional design provenance for
  this brief. C0 must replace it with the merged acceptance-centered Slice 1
  revision before its spec is authored.
- C3 must record the merged acceptance-centered Slice 2 revision and its final
  typed report vocabulary before its spec is authored.
- An inexpressible C0 sample is a stop condition and upstream amendment, not
  permission for C1 to invent a parallel acceptance contract.
- Candidate details above are authoring packets, not confirmed slices. The
  owner confirms the Ready transition first and the slice cut separately.

## Rabbit holes

- Do not solve recognition by requiring a larger context window, whole-repo
  scan, code graph, or another retrieval product. PR 207 had strong repository
  guidance and still missed preservation obligations.
- Do not store the consumer map as accepted scope or approval state. Accepted
  properties survive its deletion; the map is one way to derive tasks and
  evidence.
- Do not add reviewer-specific branches to work-loop. Reviewer implementations
  remain opaque behind selected obligations and typed reports.
- Do not treat “existing tests pass” as conservation evidence. Name the old
  behavior, its allowed delta, and the oracle that would fail if it moved.
- Do not make a real adopter corpus the only oracle. Keep a minimized
  adversarial fixture and use a real corpus only where it adds a distinct scale
  or distribution claim.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |
