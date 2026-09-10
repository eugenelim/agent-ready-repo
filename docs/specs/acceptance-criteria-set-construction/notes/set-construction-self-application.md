# Self-application transcript: this spec's own criterion set

This spec's criterion set was authored with the procedure the spec specifies.
The run is recorded here because it is the procedure's first use, not because a
criterion reads it — no acceptance criterion in `spec.md` depends on this file.
Case zero, distinct from the three frozen evaluation cases the delivery gate
scores.

## Counts

- Candidates enumerated: 32
- Final criteria: 18 (14 admitted here; four were split during review — see the addendum)
- Dispositions: 14 `admit`, 7 `merge`, 10 `relocate`, 1 `remove`

Corpus position, from the brief's § "Corpus" instrument run 2026-09-10 over 249
shipped specs with this spec and the brief excluded: criteria median 12, p75 19,
max 78. A final set of 14 sits between the median and p75, so the set-level pass
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
