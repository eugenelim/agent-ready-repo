# Self-application transcript: this spec's own criterion set

This spec's criterion set was authored with the procedure the spec specifies.
The run is recorded here because it is the procedure's first use, not because a
criterion reads it — no acceptance criterion in `spec.md` depends on this file.
Case zero, distinct from the three frozen evaluation cases the delivery gate
scores.

## Counts, as they stood on 2026-09-10 at the first authoring pass

The set has grown since, through the owner scope widenings and the review rounds
the addenda below record; `spec.md` is the only current statement of it. These
numbers are the state at the date in this heading and are kept because the
procedure's first run is what this file records.

- Candidates enumerated: 32
- Final criteria: 18 (14 admitted here; four were split during review — see the addendum)
- Dispositions: 14 `admit`, 7 `merge`, 10 `relocate`, 1 `remove`

Corpus position, from the brief's § "Corpus" instrument run 2026-09-10 over 249
shipped specs with this spec and the brief excluded: criteria median 12, p75 19,
max 78. The set of 14 recorded above sat between the median and p75 on that date,
so the set-level pass
ran at ordinary depth rather than heightened scrutiny. No bound rejected the set,
and its position is not evidence that the set is well-shaped.

## Step 1 — changed contract obligations

Nine obligations came out of the Objective and Boundaries: the ordered selection
procedure; a positive and disconfirming scenario per obligation; routing to a
named owner; the set-level pass; the recorded dispositions; count as descriptive
only; an adopter-readable home; the three frozen cases; and criterion shape
staying with its existing owner. Two non-waivable guardrails came from
Boundaries: no rule restated into a second file, and no fixed absolute
criterion count anywhere. The second guardrail was first written as "no count
threshold anywhere", which review showed contradicts the corpus-percentile
trigger the same contract requires; the narrower wording is the one that holds.

## Steps 2–4 — dispositions

| Candidate | Disposition | Reason |
| --- | --- | --- |
| Ordered selection procedure in the AC step | admit | Externally observable in shipped text; absence blocks |
| The procedure names five steps in order | merge → ordered procedure | Same remedy: order is the predicate, not a second claim |
| Named ship-blocking admission grounds | admit | Distinct outcome from the procedure's existence |
| Positive and disconfirming scenario per obligation | admit | Distinct failure and remedy |
| Several scenarios stay one criterion | merge → routing | One remedy: move the cases to Testing Strategy |
| Routing table with named destinations | admit | One predicate substituted over an enumerated destination set |
| Set-level pass over five checks | admit | One predicate over an enumerated check set |
| Coverage reaches Objective outcomes and Boundaries | merge → set-level pass | Defines the coverage member, not a separate outcome |
| Each check names what makes it red | merge → set-level pass | Wording of that criterion, not a criterion |
| Large irreducible set survives; clusters decompose | admit | Guards the owner's no-cap decision at the pass |
| Recorded dispositions and counts | relocate → Durable Outputs | Already homed as a durable output with an owner, expected evidence and closeout condition; a criterion would be a second home |
| Count recorded and orders scrutiny | admit | The Band's positive half |
| No count threshold rejects a spec | admit | The Band's refusal half, with its own green case |
| Reported criterion count of this spec | remove | Decoration — no criterion, gate or decision reads it |
| Guide section exists | admit | Adopter-facing promise; phase-slice doctrine |
| Guide frontmatter validates and title matches H1 | relocate → plan | Existing repository obligation with its own owner and linters |
| Guide leaves the per-criterion section to its slice | merge → single-homing | Same remedy: scope the guide and cite the shape owner |
| No owned rule restated in a second surface | admit | Non-waivable guardrail |
| Procedure cites rubric vocabulary, never restates it | merge → single-homing | Same predicate, same remedy |
| Procedure reachable from the AC step | merge → ordered procedure | The procedure is that step |
| Three frozen cases exist | admit | The gate's corpus |
| Seeded material pinned so a dropped seed reds | admit | Without it the case-existence criterion cannot fail |
| Shipped scoring order | admit | The gate's oracle |
| Recorded run's recall result | admit | The gate's verdict |
| Projections regenerated | relocate → plan | Existing self-host drift gate |
| Pack version bump and changelog entry | relocate → plan | Existing version bump rule |
| Workspace registration | relocate → plan | Existing lifecycle index obligation |
| Pre-existing warn-only warnings stay unsilenced | relocate → Boundaries | A rail, not an outcome |
| Traceability lint exits 0 | relocate → plan | Existing gate |
| The brief's body is untouched | relocate → Boundaries | A rail, not an outcome |
| No portable claim about written guidance | relocate → Boundaries | A non-goal; no wrong implementation is detectable by it |
| This spec was authored with its own procedure | relocate → this file | A criterion here would make the spec grade itself |

The last relocation is the one worth naming. Making self-application a criterion
was tempting because the sequence asked for it, and it is exactly the defect the
rubric's sixth class describes: the thing being measured would define the
measure. The evidence belongs in a note the contract does not read.

## Step 5 — set-level pass over the 14

**Necessity.** Every criterion's failure independently blocks shipment. The
weakest is count-recording: if it fails while the no-threshold criterion holds,
the set-level pass loses its ordering input. It stays because the owner decision
names both halves.

**Uniqueness.** Four pairs were close enough to test explicitly.

- *Large-set survival* and *no count threshold* are independent: a surface with
  no threshold can still compress a large set, and a threshold that never fires
  leaves survival intact.
- *Recorded dispositions* and *count orders scrutiny* live on different
  surfaces — the evaluation record and the procedure.
- *Cases exist* and *seeds pinned* are existence and gradability.
- *Scoring order* and *the run's result* are the rule and the outcome.

**Consistency.** One verdict per input, on the input that could split: a guide
containing the conjunction test verbatim reds single-homing and leaves the
guide-existence criterion green. Those are different questions, so the verdicts
do not conflict. Recording a count and forbidding a count gate are compatible
because recording is not thresholding.

**Joint feasibility.** No pair requires opposite states. The tightest pair is
count-recording against the no-threshold rule, feasible for the reason above.

**Coverage.** All nine obligations and both guardrails are represented, with no
criterion left tracing to nothing.

**Verdict.** Irreducible at 14. No independently shippable cluster exists: the
evaluation is the procedure's delivery gate and cannot ship apart from it, and
the guide is owed in the same slice by the phase-slice rule.

## Addendum — what shaping review found that this pass missed

Round 1 of independent shaping review returned eight findings, and adjudication
sustained all eight. Three of them changed the set, taking it from 14 to 17. The
pass above declared it "irreducible at 14", and that verdict was wrong on three
counts. Recording which ones, because a self-applied procedure that hides its
own misses is worth nothing.

- **A graft survived the uniqueness check.** The stage-order criterion carried a
  second predicate — that admission precedes every wording step — and the
  wording step is not one of the five enumerated stages, so the second clause
  reached material the first did not. That is `assets/spec.md`'s E1 shape
  exactly. The pass missed it because it tested the criteria against each
  *other* for duplication and never tested a single criterion against the
  conjunction cue. Split into two.
- **Coverage and routing gave two answers for one input.** The pass checked
  coverage of Objective outcomes and Boundaries, and separately checked that
  rejected candidates were routed to an owner, without ever asking whether a
  routed disposition *discharges* coverage. Five of this spec's own non-waivable
  Boundaries were neither criteria nor declared covered. A new criterion now
  defines coverage as criterion-or-routed-disposition, and the five resolve
  under it as routed dispositions: projection regeneration and the traceability
  gate to the self-host and lint owners, the synchronized version bump and the
  changelog to the pack release pipeline, warn-only lint preservation to the
  lint's own module contract, new-dependency avoidance to the pack manifest, and
  the portable-claim limit to `packs/AGENTS.md`'s no-internal-citations rule.
- **A criterion asserted an ordering with no observable difference.** "Uses
  corpus position to order how hard the set-level pass looks" named no action
  an author takes differently at a higher position, so a phrase-presence check
  could confirm the words while the promise stayed empty — the rubric's second
  class, comparison value supplied by the implementer. It is now two criteria,
  the second naming the one action that differs above the p75.

Two further findings moved construction mechanics out of the spec's Testing
Strategy and one narrowed the single-homing claim to what its oracle actually
compares. Neither changed the obligation set.

**The lesson for the procedure itself.** Step 5's five checks are set-level and
found nothing, because all three real defects were *per-criterion* defects that
step 2 and step 3 should have caught on the way in. A set-level pass over
already-admitted criteria cannot see a graft inside one of them. The shipped
procedure therefore keeps the admission step ahead of every wording step, which
is the criterion this round added.

## Addendum 2 — round 3, and why the loop stopped there

Round 2 returned four findings: two sustained, two refuted because the existing
text already handled them. One refutation is worth keeping, because the
temptation it names recurs. The recorded run's candidate counts and dispositions
have no acceptance criterion, and that looked like a dropped obligation. It is
not: the outcome is homed in this spec's Durable Outputs table with an owner,
expected evidence and a closeout condition. Adding a criterion would have given
an already-owned obligation a second home, which is the rubric's first class —
the defect, not the repair. The disposition table above now records that
candidate as `relocate`, which is what it always was; recording it as `admit`
was a transcript error, and the table's arithmetic did not add up either.

Round 3 returned three findings and the loop stopped. Two were the same defect
class as round 2's: a repair creating the next round's finding.

- **The blocker was a contradiction I authored.** Round 1 added a criterion
  requiring a corpus-p75 scrutiny trigger and never re-read the Boundary that
  forbade "a criterion-count threshold, ceiling, budget or refusal to any
  surface". Those cannot both hold. The rubric's own repair check — take an input
  the rule already governed and confirm one verdict — is exactly the check that
  would have caught it, run on the clause the repair did not touch. It was not
  run.
- **A positive verification was missing.** The round-2 repair stopped the
  negative count assertion from forbidding the p75 trigger, and stopped there.
  Nothing asserted the heightened-scrutiny action itself, so the suite would
  have passed with the action absent.
- **One conjunction survived three rounds.** The guide criterion joined
  publishing the procedure with citing the shape owner — two predicates, two
  repairs, the E1 shape. Three passes of a procedure whose job is finding this
  did not find it, because every pass read that criterion as one obligation about
  one file.

**What the record shows about the procedure, stated against it rather than for
it.** Its step 5 set-level pass found nothing across three rounds. Every real
defect was per-criterion — a graft, a contradiction with a Boundary, a missing
observable — and a set-level pass over already-admitted criteria does not look
inside one. That is not an argument for a sixth step; it is an argument that
steps 2 and 3 carry the weight and that the shipped text should say so. The
delivery gate's three frozen cases are what test whether they do, and they are
authored after this record, not before it.

## Addendum 3 — the seven rounds, classified, and the two moves they bought

Seven shaping rounds raised 24 findings; 22 were sustained and 2 refuted.
Classifying the 22 by cause is the only thing in this record that generalises,
because it says which authoring move was missing rather than which sentence was
wrong.

| Cause | Findings | Nearest frame in the commissioned survey |
| --- | --- | --- |
| No observer, or an observer narrower than the claim | 11 | 29148 set-level *able to be validated* |
| A restatement that decayed | 3 | the shaping classes' own decay class |
| Two clauses, two answers for one input | 3 | 29148 set-level *consistent*, *feasible together* |
| A conjunction or a graft | 2 | 29148 *singular*; INCOSE R19 |
| Wrong owner, or the wrong artifact | 2 | the shaping classes' own delegation class |
| A universal claim wider than its oracle | 1 | 29148 *complete* |

**Half of every finding was one defect: a criterion existed and nothing was
named that would show its failure.** Not one finding said a criterion was
ambiguously worded. The six per-criterion failure classes caught almost none of
this, which is what the survey predicts — it records that the shaping classes
are all per-criterion and that 29148's three set-level characteristics have no
counterpart in the guidance.

Two moves follow, and both are self-checks the author runs while authoring
rather than gates another party applies:

- **Naming the observing surface is part of admission.** An obligation whose
  observer cannot be named stays a candidate. Choosing the observer later, in
  Testing Strategy, admits the criterion before anything is known to show its
  failure, and the gap is invisible because the criterion reads fine.
- **The set-level pass reads coverage from the criteria back to their
  observers**, not only from the obligations forward to the criteria. Those are
  different questions and only the first was being asked.

The OpenSpec import behind the first is narrower than "separate requirements
from scenarios", which this contract already did. It is that a requirement is
not admissible until a concrete scenario exists for it — the separation is only
load-bearing if the scenario is a precondition rather than a later attachment.

## Addendum 4 — the pairwise uniqueness re-run, because this set is above p75

Adding those two criteria took the set to 20 against a corpus p75 of 19, so the
procedure's own heightened-scrutiny trigger fires on this spec and the pairwise
whole-set uniqueness re-run is owed. Run at criterion granularity, grouped by
the surface each criterion observes: the skill's procedure span (12), the guide
page (2), the four authoring surfaces (1), the eval register (3), the recorded
run (1), and the ordering assertions over the span (1).

**One real duplicate, found and removed.** The new bidirectional-coverage
criterion opened by restating the coverage-definition criterion's content —
"every Objective outcome and non-waivable Boundary reaches a criterion or a
routed disposition" — before adding its new direction. Two criteria asserting
one claim is the defect this procedure exists to prevent, and it was authored
*while* adding the check designed to catch it. The criterion now states only
the criteria-to-observers direction and leaves the forward direction to its
owner.

**Four pairs tested and kept.** Admission grounds against the observer
requirement: different predicates, different reds. The scenario requirement
against the observer requirement — the closest pair, kept because a scenario is
a narrative and an observer is a surface, and a criterion can carry both
scenarios while naming no surface. Large-set survival against the no-cap rule,
independent for the reason recorded above. The p75 action against the
above-p75-passes rule: one is an action, the other a permission.

**What the run cost, honestly.** It found one duplicate in a set of 20, which is
a low yield for a whole-set pass. It is recorded as a single sample and not as
evidence the trigger is well-calibrated; the frozen cases are what test that.

## Addendum 5 — necessity pass over all 20, so each owns its keep

Method: for each criterion, name the input that makes it red, then ask whether
another criterion already reds on that same input. A criterion whose red input
is fully covered elsewhere does not own its keep.

**Result: no cuts, three defects.** Every criterion has a red input no sibling
catches. That is a weaker result than it sounds — it says the set is not
redundant, not that it is well-shaped — so the three defects the pass turned up
matter more than the zero cuts.

**Defect 1 — a criterion whose subject may not exist.** The
selection-before-wording criterion constrained "every step that words a
criterion, including the step that cites the criterion-shape owner". Neither is
a member of the five stages the neighbouring criterion enumerates, so the
criterion governed material the procedure need not contain, and an implementer
could satisfy both by shipping five stages and no wording step at all. It now
names the thing whose position actually carries the thesis: the hand-off to the
criterion-shape owner must follow admission rather than open the step. That is
falsifiable against the current shipped text, which opens with the shape
pointer and reaches selection afterwards — so the criterion's red case is the
present state, which is the strongest evidence it is worth having.

**Defect 2 — a criterion that held on empty state.** The single-homing criterion
read "no rule sentence pinned by the single-homing suite appears in more than
one of the four authoring surfaces". Pin nothing and it is vacuously true. It
now reads "each rule sentence the procedure introduces appears in exactly one",
which cannot be satisfied by an empty pinned set and still carries the
non-duplication rule as one substitutable predicate.

**Defect 3 — a criterion asserting of the wrong actor.** "The procedure records
the criterion count" — the author records; the procedure requires it. Reworded.

**The four closest pairs, with the input that separates them.** Recording these
because "they are different" is the claim a later reader cannot check.

| Pair | Input that reds one and not the other |
| --- | --- |
| Observer at admission vs. observer in the set-level pass | A procedure requiring an observer only at the pass: the pass criterion is green, the admission criterion red. The distinction is *when* the gap is caught, and it is the whole point of the move. |
| Scenario per obligation vs. observing surface | A criterion carrying both scenarios and naming no surface. A scenario is a narrative; an observer is a surface. |
| Large irreducible set survives vs. no fixed count cap | A guide page stating "keep specs under 20 criteria": the survival criterion stays green, the no-cap criterion reds. Reverse: a pass instructing compression with no count language anywhere. |
| Guide cites the shape owner vs. single-homing | The guide inlining the conjunction test. The single-homing criterion covers four authoring surfaces and the guide is not one of them, so only the guide criterion reds. |

**Weakest keep, named rather than hidden.** The observer-at-admission criterion
is the one whose independence rests on timing rather than on outcome: the
set-level pass would eventually catch an unobserved criterion anyway. It stays
because catching it at admission is the change this slice exists to make, and
because its second clause — that a candidate without a namable observer stays a
candidate — has its own red case. If a later reader wants to cut one criterion
from this set, that is the one to argue about first.

## Addendum 6 — the writing move the shipped skill never had

Checked against the merged skill text: the acceptance-criteria step ships a
motivation, a deferral for shape, an instruction to work the failure classes,
and two pointers. Every rule it reaches is either a constraint a finished
criterion must satisfy or a class to diagnose after the fact. **Nothing tells an
author how to produce a criterion.** The shape owner's section opens the same
way — it names what it owns, then lists constraints.

That is the better explanation of this record than any individual defect. The
21 criteria were written whole and then diagnosed over seven rounds; the rounds
were the production process. Both grafts entered because a sentence was composed
before its parts were settled, and no instruction existed to do it the other way
round.

The material for the fix was already present and unused. The procedure's own
steps make an author name the obligation, the ground on which it blocks
shipment, the surface that observes its failure, and a positive and
disconfirming case — a subject, an outcome, an observer, a red case and a green
case, all decided before any sentence exists. The added criterion puts
composition at the hand-off to the shape owner: compose from those parts rather
than write and then test. Parts that are singular before composition begins are
hard to graft a second predicate onto.

Two lines held while adding it. It is not a template or a syntax, which the
EARS measurement settled as suggest-never-mandate. It is not a restatement of
any shape rule, because composition order is not a shape constraint — the
sentence still goes to the shape owner to be judged, one step later.

**Necessity, checked before the round.** Its red input is a hand-off that lists
the parts but omits the compose-rather-than-check direction. The neighbouring
criterion reds only on the hand-off's *position*, so a correctly placed hand-off
that says nothing about composing leaves that one green and this one red. The
five stages are untouched: composition is the hand-off's content, not a sixth
stage, so the stage-order criterion and the guide's five-stage criterion both
stand unchanged.

## Addendum 7 — plan writing rules and plan set passes, from 12 measured findings

Rounds 4 through 11 returned almost no criteria defects. They returned **plan**
defects, twelve of them, and they fall into five causes. The acceptance-criteria
side got writing rules and a set pass this slice; the plan side has neither, and
that asymmetry is the better explanation of the late rounds than any single
mistake.

| Cause | Findings | What it looked like |
| --- | --- | --- |
| A `Done when` narrower than its own `Tests` | 3 | The task could close with a required observation unmade |
| A condition restated in a second place, then going stale | 4 | A stale AC trace, a map repeating a task's condition, a threshold that no longer matched, a hand-listed set of criterion numbers |
| An obligation left in `Approach` | 2 | No completion gate reads `Approach`, so the counts and the version parity were never observed |
| A criterion with no construction evidence at all | 2 | A stage order and a scoring rule that nothing asserted |
| A claim about a check the oracle cannot support | 1 | Prose said "derived"; the suite iterates a hand-declared tuple |

### Writing rules, applied per task while drafting

1. **A `Done when` points at its `Tests`; it never restates them.** A pointer
   cannot be narrower than its target and cannot go stale when the target
   changes. Three findings came from copies.
2. **If a completion gate must read an obligation, it belongs in `Tests`.**
   `Approach` is instruction and nothing observes it. Two obligations sat there
   and were invisible.
3. **A `Tests` bullet names the criterion it verifies.** Untraceable evidence
   cannot be walked, and a bullet naming a bare plural is satisfied by any
   subset.
4. **A claim about what a check proves names the comparison the oracle actually
   performs.** If the oracle cannot perform it, say so and state the proxy.
   Calling a hand-declared tuple a derivation was itself the defect.
5. **One home per condition; cite the owner elsewhere.** Every restatement in
   this plan decayed, including three written specifically as repairs.

### Set passes, run over the whole plan before review

1. **Coverage both ways.** Every criterion has construction evidence, and every
   `Tests` bullet traces to a criterion. One direction alone leaves orphans at
   the other end.
2. **Each `Done when` against its own `Tests`.** Walk all tasks, not the one a
   reviewer named.
3. **No condition with two homes**, across the spec and between tasks.
4. **Every claim about an oracle is one the oracle can perform.**
5. **Necessity.** A task whose outputs another task fully produces is merged.
6. **Every shared bound is defined once.** Two assertions naming the same region
   separately is how the span bound came to disagree with itself.

### The audit, run on this plan

Rules 1, 2, 3 and 5 pass. Rule 4 failed once and is repaired: the pin bullet
claimed a derivation and now states the proxy and its floor. Set pass 6 was
added *because* running it found a live contradiction — the floor assertion
closed the fifth interval at "the end of the procedure span" while the count
assertion sliced "first step marker to last", so the fifth interval was empty.
The span is now defined once in the design section and cited by both.

Set pass 1 holds by reference rather than by enumeration: sixteen criteria are
named directly in a `Tests` bullet and the remaining seven are covered by the
pin, which points at the spec's own criterion group rather than keeping a second
list. That is traceability, not a mechanical guarantee, and the note says so.

**Scope, stated rather than assumed.** These rules are about plan authoring, not
about acceptance-criteria set construction, so they are not this spec's contract
and no criterion here carries them. They are recorded as delivery learning. If
they should ship as guidance, that is a slice of its own against the plan
template, and the owner cuts it.

## Addendum 8 — accepted residual concerns, under the repository's own rule

Fifteen shaping rounds produced no `Clean` verdict. The residue is accepted here
under the mechanism `work-loop-review-economics` already states in its Boundary:
*"Owners may explicitly accept residual concerns outside protected risk classes.
Acceptance must name the concern and consequence; silence, arbitrary round caps,
and elapsed budget are not acceptance."* Owner-authorized 2026-09-10.

That rule is deliberately the instrument rather than a round count, because the
same Boundary rejects a round cap as acceptance. Fifteen rounds is not why this
is accepted; each concern below is named with its consequence, and none falls in
a protected class.

**Protected-class check.** The named classes are security, privacy, data-loss,
migration, mixed-version, public-contract, destructive-operation and
human-approval. All five concerns below are properties of this repository's own
test oracle or plan prose. None changes what an adopter may rely on, so none is
public-contract; none touches the other seven. Stated as a judgement, not a
mechanical result.

| Concern | Consequence if it bites | Protected? |
| --- | --- | --- |
| **The single-homing oracle compares presence and absence of hand-declared exact phrases.** Three consequences from one root: a stage's second rule sentence can be unpinned and uncovered by the floor; a paraphrased second home is invisible; an occurrence repeated inside one file is never counted. | A rule could reach a second authoring surface, or be stated twice in one, without the suite noticing. Reachable at review by the rubric's first class, and by nothing mechanical. | No |

Three earlier rows are retired rather than carried. Plan traceability by
reference is **decided**, not residual: ADR-0108 settles identity and change
detection, leaving implementation rather than an open question. The
`Tests:Approach` ratio row is **dissolved**: once a task's tests are identified
verification items, a word-ratio instrument measures nothing, so the row was an
artifact of the old shape. And the relocated-design-facts disagreement is
**resolved**: measured per verification item rather than per task, three of five
facts govern two or more items and stay in the design, two govern one each and
returned to their task.

The surviving concern is bounded by a decided design and unimplemented. Rule
identifiers would make the pinned set derivable rather than hand-declared, which
closes the first and third consequences; fingerprints bound the second by
flagging the next edit to either location for re-review. Neither is built.

The last one is the only concern with a *measured* consequence, so it is accepted
with a reason rather than as trivia. Two things bound it. The eliminator
disposition now routes exact assertion wording to build-discovery, which is what
took T1 down by 36%. And the residual height is partly an instrument artifact:
the ~2× smell divides by `Approach`, which for a task whose deliverable *is*
prose compresses to a line or two — "write the procedure" — so the ratio inflates
without indicating over-specification. That is a finding about the smell's
calibration on prose-authoring tasks, and it belongs to whoever owns the
template rather than to this slice.

**What acceptance does not cover.** No `Clean` verdict exists, so the spec stays
`Draft` and unindexed until the owner approves it on this record. Acceptance of
these five concerns is not approval of the contract.

## Addendum 9 — T1 was a design outline, not an over-specified task

Owner observation, 2026-09-10: T1 is not merely a large task. It is a detailed
design outline written as a set of TDD assertions — a mini-module whose content
maps to the low-level design — and in some practices each test *is* an
acceptance criterion in itself.

That reframing is correct and it corrects an earlier entry in this record. The
`Tests:Approach` smell fired accurately; what was wrong was the remedy. Two
passes measured:

| Pass | T1 `Tests` | Ratio | What changed |
| --- | --- | --- | --- |
| as authored | 851w | 19.8× | — |
| reduction | 548w | 12.7× | compressed prose, routed exact wording to build-discovery |
| relocation | **242w** | **5.6×** | moved the design facts to `### Behavior & rules` |

The plan's total barely moved (≈3,700 words both sides of the relocation) while
`## Design (LLD)` grew to 1,042 words. **The content was never surplus — it was
in the wrong section.** Roughly three-quarters of the excess was misplaced
design; the remaining ~5.6× is where the earlier "instrument artifact" claim has
some force, since a task whose deliverable is prose has a legitimately one-line
`Approach`. That claim was mostly wrong and is corrected here rather than left
standing.

**On each test being a criterion.** That is a real tradition — specification by
example, ATDD, executable specifications — and it is coherent. This repository
has already chosen against it at a level neither this slice nor its brief can
move: `docs/CONVENTIONS.md` § *Contract vs. construction tests* puts the contract
in `spec.md` and construction tests in `plan.md`, and the brief's own rabbit
holes say not to count scenarios as requirements. The brief's phrasing carries an
escape clause worth preserving — the testing strategy owns concrete cases
*unless a case changes the obligation itself* — so the position is a considered
separation with an admitted exception, not a flat rejection.

Recorded because the option should not be lost silently. Adopting
test-as-criterion would be a change to the document hierarchy, which routes
through the repository decision process, not through this slice.


## Addendum 10 — the residual record went stale, which is the point

The row above first stored `12.7×`. By the time the owner asked for the
residuals it read `5.6×`, because the relocation pass had happened in between
and nothing linked the two. A stored figure in a document that warns against
stored figures, caught only because the owner asked for the facts plainly
rather than accepting a summary.

It is now a pointer to the measurement rather than a copy of it. That is
class 4's own repair applied to this record: ship the derivation, not the value.

**And it is the argument for the decision-facts step** added to the skill in
core 2.25.14. Three of the five residuals were one root — the single-homing
oracle compares presence and absence of hand-declared exact phrases, which
leaves an unpinned sentence uncovered, a paraphrase invisible, and a reworded
copy inside one file green. Nobody had said that out loud across fifteen rounds;
it took an owner asking what the residuals actually were. A skill that reports
the trend and each residue with its consequence surfaces that without the owner
having to ask.

## Addendum 11 — review counters reset, and what the next round is a spike for

The scope widened on 2026-09-10 from acceptance-criteria set construction to
loop-contract authoring: the same three moves an author makes, plus the
plan-authoring rules brought under contract and a review-response protocol the
skill does not have. The sixteen rounds behind us reviewed a different contract,
so the counter resets and the next round is round 1 of a new cycle.

It is also a spike, and predeclaring what would count as better is the only way
that claim can fail.

**Baseline, the old cycle.** Round 1 returned 8 findings over 14 criteria —
0.57 per criterion. The whole cycle ran 16 rounds, raised 32 findings, sustained
30, refuted 2, and 9 of the 30 (30%) were introduced by a previous round's
repair. The dominant family was **a claim wider than its oracle**: a criterion
asserting a scope its check could not reach.

**Prediction for round 1 of the new cycle, over 27 criteria.**

- **Primary:** at most **2** findings in the claim-wider-than-its-oracle family.
  Three of the shipped moves aim at it directly — the contribution test, the
  rule that a claim names the comparison its oracle performs, and the widened
  earn-its-keep scope. If that family lands at its old share, those moves did
  not bind.
- **Secondary:** no blocker.
- **Descriptive, not a bar:** total findings, and findings per criterion against
  the old 0.57.

**What a miss would mean, stated now rather than after.** If the families recur
at the old rate, the honest reading is not that the guidance is wrong but that
written guidance did not change what this author wrote — which is the activation
question the brief assigns elsewhere, arriving as evidence from a case rather
than as a claim. A miss is a result, not a failure to be explained away.

**One confound recorded in advance.** The author of the artifact and the author
of the guidance are the same, in one session, so this measures whether the rules
bind *the person who wrote them*. That is the weakest form of the activation
question and it cannot be strengthened from inside this session.

## Addendum 12 — the four residuals, dispositioned

**Bound and deferred (two).** The single-homing oracle's blind spots and the
propagation sweep's missing mechanical backing are one root and one follow-on:
[`loop-contract-item-identity-mechanism`](../../../product/intents/loop-contract-item-identity-mechanism.md).
The test that settled it: the phrase-based oracle is how single-homing already
works, so leaving it is declining to repair a pre-existing gap rather than
shipping new debt, and everything this spec delivers works identically
underneath it. The Boundary now says this spec does not build that mechanism.

This produced a seventh response in the protocol. Routing assumes an owner
exists; here none did, so the response is to bound the work out of scope and
record a follow-on that names its new owner. Without that, the only honest
options were to build it here — scope creep — or to leave the residue unowned.

**Dismissed (one).** "Eight criteria are verified by presence alone" overstated
the gap. The pins are *exact phrases*, so presence establishes that the
procedure says precisely what was pinned. What it does not establish is that an
author reading it acts on it, and that is the activation question the brief
assigns elsewhere. The residue as written claimed a gap that is not there.

**Accepted with its reason (one).** The stop-decision report is verified as an
instruction in prose, not as a produced report. A fourth frozen evaluation case
would close it and was declined: the report's reader *is* the owner, so a
missing field is visible on first use, where a missing seed in an evaluation
case is invisible and degrades the gate silently. Self-revealing failures do not
need mechanical oracles, and a fourth case would add roughly a third to the
delivery gate to catch what the audience catches free.
