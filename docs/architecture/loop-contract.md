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

The design section is **shape-pruned, not fixed**. The spec's optional
`Shape:` field — `ui`, `service`, `data`, `integration` or `mixed` — selects
which of the plan's nine `## Design (LLD)` sub-sections scaffold; the rest are
deleted rather than left empty, and an omitted or `mixed` shape scaffolds the
full set to prune by hand. The field names the *kind* of work and never a
framework. The plan template carries the shape-to-subsection map, and labels
it a guide rather than a gate: nothing binds `Shape:` to it and nothing
enforces the pruning, so the map is a convention the author applies.

One category is deliberately not a design sub-heading. Rollout and deployment
is realised by `## Rollout`, which sits *after* `## Tasks` rather than in the
design block, and a design sub-section cross-links to it rather than restating
it. Keeping it out of the design block is what stops the same rollout
decision being written twice.

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

> **STATUS: PLANNED**, for the *per-item* mechanism this section describes.
> Nothing in the skill implements that; a whole-artifact approval pin is
> shipped and is described at the end of this section. It is recorded here
> because the pairing is what the identity decision is *for*; the decision
> itself is
> [ADR-0108](../adr/0108-opaque-append-only-loop-contract-identifiers.md), and
> the unbuilt half is carried by
> [its follow-on intent](../product/intents/loop-contract-item-identity-mechanism.md).
> No accepted record decides the change-detection half yet.

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

### What is shipped: the whole-artifact approval pin

The per-item fingerprint above is unbuilt. A **whole-artifact** one is not, and
reading this section without that distinction leaves the impression that
nothing compares a contract against its approved form.

`approve-plan` records a digest of each artifact's canonical form, and
`plan check-current` is the verb that recomputes both and compares them against
those recorded digests. The other two users of the canonical form do something
narrower: `schedule` computes and stores a fresh `plan_hash` of its own rather
than comparing with the approved one, and `schedule check-current` compares
against *that* scheduled hash. Approval drift and schedule drift are separate
questions, answered by separate values.

The canonical form normalises exactly four things:

- CRLF and CR to LF;
- per-line trailing whitespace;
- the status **token** only, on the preamble status line only;
- the **bracket contents** only of a ticked checkbox.

What it refuses to normalise carries as much weight. Leading whitespace and the
bullet run are preserved byte-for-byte, so re-indenting a criterion — which
changes what the list contains — still moves the digest. Checkbox
normalisation is scoped by artifact: a spec's applies only inside its
acceptance-criteria region, so a checkbox anywhere else in the spec stays
pinned, while a plan has no such region and its checkboxes are task progress,
so a plan normalises file-wide. The pin recognises that region more loosely
than the lint does — a lower-case or `###` heading, or a bold lead-in, opens
it — so the two agree on typical specs without agreeing by construction.

The contract this buys: **lifecycle bookkeeping does not break an approval pin;
substantive edits do.** Bumping a spec through `Approved → Implementing →
Shipped`, or ticking criteria off as they land, leaves the pin intact. Changing
what a criterion says does not.

The status and checkbox recognisers are imported from the spec-status lint
rather than re-implemented, which keeps one definition of what a status line
and a ticked box look like. It does not make the two identical: the pin has to
map its match back to a raw line number, so it strips HTML comments
newline-preservingly where the lint strips them outright, and a multi-line
comment before the status line can be read differently by each.

## 5. Grounding: which probes run when

A loop contract is authored against a repository that already has owners, gates
and accepted decisions. The expensive failure is not bad reasoning; it is a
well-formed artifact that conflicts with something nobody looked up. So the
probes are directed by *stage*, seeded by whatever paths that stage can resolve.

The explorer's own `PHASES` table is canonical for which probes each stage runs;
this page names the stages and what each is *for*, and does not restate the
probe sets — a second copy would be falsified by the next edit to the script
with nothing comparing them.

| Stage | Seeds | What it is for |
| --- | --- | --- |
| **Discovery** — durable outputs resolved, body not yet written | the resolved destinations | Learn what already owns and governs these surfaces, *before* a design is committed to. Nothing is authored yet, so dead references cannot exist. |
| **Task grounding** — per plan task | that task's `Touches` | Find the checks that will run against this task's files, and the files that historically move with them. |
| **Review sweep** — after a repair round | the spec and plan themselves | Find what the repair broke: a reference to something that moved, a path that no longer resolves. |

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
- `workspace.toml` `[backlog].open` is the sole authoritative register for a
  historical deferred marker; `docs/backlog.md` is not consulted. A marker
  resolves through either a legacy `slug` field or a canonical artifact path
  reduced to its canonical anchor. A `(deferred: <anchor>)` marker no longer
  makes a *new* ship transition valid — separable work leaves the final
  criterion list through an approved amendment and a non-criterion follow-on.
- The canonical status vocabulary is `{Draft, Approved, Implementing, Shipped,
  Archived}`, matched against the **leading token** only: the first word after
  `Status:`, truncated at the first ` (`, ` →` or `<!--`. An annotated frozen
  status such as `Shipped (2026-05-26)` or `Approved → Shipped (…)` therefore
  passes, while a genuine out-of-vocabulary token such as `Drafting` fails.
- The every-criterion-closed check is **diff-triggered**, not a standing scan.
  It fires on a spec whose header status *changes to* `Shipped` in the diff
  against the base ref; specs already `Shipped` on the base are grandfathered,
  and where no base ref resolves the invariant is skipped with a warning.
- These invariants read the artifact, not the system it describes. Several
  reach well into the body — dangling intra-repo doc and code references,
  body-wide deferral markers, and the Acceptance Criteria section itself — so
  "metadata only" understates them. What none
  of them can see is whether a spec still describes the code it was written
  against. That is semantic drift, and it is the adversarial reviewer's job,
  not a lint's.

## 8. Present-tense bodies

A body is *written* in the present tense, as built. It carries no future-tense
promise, no previously-X-now-Y narration, no deprecation timeline and no
version-stamped history; decision history belongs in the ADR that owns it.
`plan.md` is not exempt — its changelog records approvals rather than evolving
strategy.

The rule governs authoring, not the whole lifetime. Freezing pins a body at the
moment it shipped, and § 9 admits only two narrow edits afterwards — neither of
which re-tenses prose — so a frozen body states what was true when it froze and
is not rewritten to track a later decision. The `Status` annotation, not the
prose, carries that news.

The failure the rule prevents is context poisoning: confident error caused by
stale or self-contradictory documentation. Duplication is the separate concern
§ 2 owns.

## 9. Editing a frozen contract

A shipped spec directory freezes as a unit, covering `spec.md` and `plan.md`
together. Two allowances survive the freeze, and nothing else does.

**A parenthetical on the existing `Status` token is the only edit the frozen
body accepts**, in exactly two licensed shapes: a supersession pointer
(`Shipped (superseded in part by ADR-NNNN — …)`), and a pointer recording that a
`[backlog].open` anchor the body names has been closed. The linter truncates at
the first ` (`, so an annotated status still satisfies the vocabulary rule.
There is no `Superseded` token, and `Archived` is not a substitute — a
superseded spec usually shipped and is still live.

**Meaning-preserving mechanical rewrites are the carve-out** — a path or link
rename, a moved file's reference, a repository-wide identifier change. The
reason is stated as a trade: a frozen document with dangling links is a worse
outcome than one whose references were mechanically corrected. A rewrite that
changes what was decided is not mechanical and is not covered.

## 10. Relevant records

- [Identifier comparison matrix](../product/research/item-id-management-comparison-matrix.md)
  — the identifier decision and its alternatives.
- [Grounding-probes survey](../product/research/repository-grounding-probes-survey.md)
  — what each probe found here, the three ranked but unbuilt, and five checking
  mechanisms this repository built and killed.
- [Review-loop non-convergence survey](../product/research/review-loop-nonconvergence-survey.md)
  — why a review loop over these artifacts terminates on a residue rather than
  on a clean verdict.
- [Repair-origin gating survey](../product/research/repair-origin-gating-survey.md)
  — why the repair-origin rate stays advisory: across four measured loops a
  threshold on it fires on a converging loop as readily as a diverging one, and
  the response it earns is cutting scope rather than stopping.
- the `new-spec` skill's `references/spec-and-plan-contract.md` — the spec metadata contract and
  the contract-versus-construction split, which this page describes rather than
  redefines.
