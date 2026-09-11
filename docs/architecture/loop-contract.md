# Loop contract

## 1. Purpose and boundary

The loop contract is the pair of artifacts a work loop runs against: `spec.md`,
which states what done means, and `plan.md`, which states how it gets built and
verified. [Loop infrastructure](loop-infrastructure.md) records that the harness
"does not create requirements or implement work. It consumes approved
specification and plan artifacts." This page owns those artifacts — what each
one holds, how the items inside them are identified, and how that identity
survives a loop that rewrites them.

The distinguishing condition is the reader. A document written for a person is
read once and interpreted generously. A loop contract is re-read at every
iteration by an agent that cannot tell a stale reference from a live one, so a
broken cross-reference is a defect rather than untidiness, and identity has to
outlive editing.

Out of scope: how the loop advances between phases ([loop
infrastructure](loop-infrastructure.md)); how work reaches an artifact in the
first place ([work intake and artifact
routing](work-intake-and-artifact-routing.md)); and what verifies the repository
([verification facts](verification-graph.md)).

## 2. Which artifact owns which fact

| Fact | Home | Why there |
| --- | --- | --- |
| An observable outcome that closes the work | `spec.md` acceptance criteria | The contract is what any valid implementation must satisfy |
| The verification mode for each outcome | `spec.md` testing strategy | The mode is part of the contract; the artifact realising it is not |
| Why an assertion must take a given shape | `plan.md` `## Design (LLD)` | Design reasoning outlives any one task and is cited, not repeated |
| What to do and what to observe | `plan.md` task `Tests:` / `Approach:` | A task is a job to be done, not a container for facts |
| A lasting record the delivery must leave | `spec.md` durable outputs | Named before approval so closeout can verify it |
| Content only the build can settle | `plan.md`, as a discovery predicate | Approval cannot bless detail that does not exist yet |

The load-bearing rule: **a fact belongs in the design unless a task must
implement or verify it.** A task cites the design for why; it does not restate
it. The reverse error is equally live — an acceptance criterion never lives in
the design, and a criterion's verification mode never does either.

## 3. Item identity

[ADR-0108](../adr/0108-opaque-append-only-loop-contract-identifiers.md) decides
how acceptance criteria and verification items are identified, and owns the
convention's wording; the skill's `assets/spec.md` states it to authors. This
section records only that the decision exists and where it binds: identity is
**opaque and append-only, scoped to a spec directory**, so an item's identifier
is not its position and a reader cannot infer order from it. Cross-spec citation
uses the `spec:<slug>/` marker the plan template already carries for cross-spec
task dependencies.

Three reasons, evidenced in [the identifier comparison
matrix](../product/research/item-id-management-comparison-matrix.md):

- **Positional numbering makes identity a function of position**, so an
  insertion silently invalidates every existing reference. Requirements tooling
  separates the two for this reason — DOORS keeps a permanent absolute number
  alongside a positional heading number and resolves links against the absolute
  one, leaving gaps rather than reusing.
- **A derived identifier inherits its parent's instability**, which is why
  independent test-management tools keep a test's identifier separate from the
  requirement it verifies.
- **Scope is the spec directory rather than the repository** because a global
  counter is a shared mutable resource across concurrent worktrees. This
  repository collided on one such counter — the released pack version — twice in
  a single day.

## 4. Change detection

Stable identity makes a reference *resolve*. It does not tell you whether what
it resolves to still says what the referrer assumed. Those are different
failures, and the second is the one a loop produces constantly, because every
repair round edits an artifact that something else was written against.

Requirements tooling answers it the same way across vendors: a content change to
a source artifact marks its downstream links **suspect** rather than breaking
them, and a person clears the flag after looking. Doorstop implements the same
idea in a text repository with a per-item hash over the item's identifier, text,
references and links; when a parent changes, its children are flagged for
re-review.

The loop contract adopts that pairing. **Identity survives editing; a fingerprint
notices it.** Concretely:

- A criterion's recorded fingerprint covers its own text. When the text changes,
  every verification item and construction test tracing to that criterion is
  suspect until re-checked.
- A pinned rule sentence's fingerprint covers the sentence. When the shipped
  rule changes, the assertion pinning it is suspect even where the assertion
  still passes.

**What this reaches, and what it does not.** It converts a silent blind spot
into a prompted re-check. It does not close one. A fingerprint detects
*identity*, not *similarity*: a rule restated elsewhere in different words has
its own fingerprint and is not recognised as a duplicate of anything. So
fingerprinting bounds the paraphrase gap — the next edit to either location
raises a flag — without detecting the paraphrase itself. Say that plainly rather
than let a hash imply a guarantee it does not give.

**The flag's consumer is the next review's scope.** A suspect mark with nothing
reading it is a control that cannot fail, so the edge is named here rather than
assumed: a suspect item enters the scope of the next re-review, alongside the
sustained findings being repaired and the bytes their repair touched. That is
the one part of this repository's review-economics experiment that survived
measurement — focused re-review of a repair, its findings and the affected
contract bytes retained closure verification and caught repair-induced defects,
while the broad resample around it mostly resampled its own repairs.

**It scopes; it never blocks.** A suspect flag selects what the next round
*looks at*. It does not decide whether the change may proceed, and it never
becomes a blocking verdict of its own. That boundary is deliberate: blocking on
a derived signal is consequence-bound blocking, which was built, measured and
killed here for missing protected-class findings. A flag that blocks would
rebuild it under a new name. Clearing a flag is a reviewer's act after looking,
recorded like any other review disposition.

**A fingerprint baseline is the one stored value that is allowed to go stale**,
because its going stale *is* the mechanism. Compute the fingerprint from the
source at check time and compare it against a recorded baseline; the mismatch is
the signal. That is the deliberate exception to the rule against storing a value
a check reads, and it only holds while the stored side is the baseline and never
the answer.

## 5. Grounding: which probes run when

A loop contract is authored against a repository that already has owners, gates
and accepted decisions. The expensive failure is not bad reasoning; it is a
well-formed artifact that conflicts with something nobody looked up. So the
probes are directed by *stage*, seeded by whatever paths that stage can resolve.

| Stage | Seeds | Probes | What it is for |
| --- | --- | --- | --- |
| **Discovery** — durable outputs resolved, body not yet written | the resolved destinations | surfaces, scoped rules, path refs, phrase pins, gates | Learn what already owns and governs these surfaces, *before* a design is committed to. Nothing is authored yet, so dead references cannot exist. |
| **Task grounding** — per plan task | that task's `Touches` | scoped rules, path refs, phrase pins, gates, co-change | Find the checks that will run against this task's files, and the files that historically move with them. |
| **Review sweep** — after a repair round | the spec and plan themselves | path refs, dead refs, co-change | Find what the repair broke: a reference to something that moved, a path that no longer resolves. |

Two rules make the staging honest rather than decorative.

**A probe reports; it never decides.** No stage gates on a probe result. Blocking
on a derived signal is the consequence-bound blocking this repository built,
measured and killed for missing protected-class findings.

**Each stage runs only the probes its inputs support.** At discovery there is no
authored text, so asking for dead references wastes a scan and returns a
reassuring empty result. At review the artifacts *are* the seeds, and their
references are the whole question.

**Degradation is reported, never silent.** Every probe distinguishes *found*,
*none found* and *input unavailable*. Co-change has no fallback without history —
this loop is used on repositories before git is initialised — and a probe that
returns empty when its input is missing is indistinguishable from a clean run.
The report also carries a surface inventory: which known grounding surfaces
exist, which carry content, and what a thin one cost, so an adopter who has never
run `adapt-to-project` gets a weaker report that says it is weaker.

**Calibration is what separates a probe from noise.** A phrase found in more than
a few files is shipped boilerplate rather than a pin; a commit touching dozens of
files is a formatting sweep rather than a coupling; a file matching most of a
seed's sampled phrases is a copy of it, not a reference to it. Every threshold is
a flag with a documented default, because the right value is repository-specific
and no source converges on a universal one.

## 6. Dependencies and allowed edges

- The contract is authored by `new-spec` and consumed by `work-loop`. The
  harness reads it; it never writes requirements into it.
- A spec cites the decisions that govern it and never the reverse: ADRs and RFCs
  do not cite specs.
- A derived spec points up to its delivery brief with a `Brief:` header, and the
  brief's coverage map rolls up from those back-links rather than being written
  by hand.
- Criterion *shape* — whether a sentence is one criterion or two — is owned by
  the `new-spec` skill's bundled spec template, not by this page.

## 7. Mechanical invariants

- Every acceptance criterion is a task-list item, and a newly shipped spec has
  none open.
- Both artifacts are pinned in substance once the plan is approved; an
  observation produced by execution goes to the sibling verification ledger.
- A rule that governs criterion authoring appears in exactly one of the skill's
  four authoring surfaces; the pack-local discipline suite enforces this per
  pinned sentence.

## 8. Relevant records

- [Identifier comparison matrix](../product/research/item-id-management-comparison-matrix.md)
  — the identifier decision and its alternatives.
- [Grounding-probes survey](../product/research/repository-grounding-probes-survey.md)
  — what each probe found here, the three ranked but unbuilt, and five checking
  mechanisms this repository built and killed.
- [Review-loop non-convergence survey](../product/research/review-loop-nonconvergence-survey.md)
  — why a review loop over these artifacts terminates on a residue rather than
  on a clean verdict.
- [`docs/CONVENTIONS.md`](../CONVENTIONS.md) § 4 — the spec metadata contract and
  the contract-versus-construction split, which this page describes rather than
  redefines.
