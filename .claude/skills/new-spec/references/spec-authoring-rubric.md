# Spec-authoring rubric

Six failure classes that stop a review loop converging, in the order they
matter. Use this while **writing** a spec or plan, before review. It is
authoring guidance, not a review checklist — handed to a reviewer it becomes a
source of nits, which is the cost it exists to reduce.

Nothing here is a second copy of a rule another surface owns. Classes 2 and 5
defer criterion *shape* to `../assets/spec.md` § Acceptance Criteria, which owns
it; classes 1, 3 and 6 defer their repair mechanics to `SKILL.md`, which owns
those; class 4 states its two clauses here, with the one boundary it shares with
the template named in the class itself.

These six are the classes an author can pre-empt, ordered so that when several
describe the same defect, the earliest one names the repair worth making. The `shaping-reviewer` agent applies them cold
from the artifact alone, as part of a **larger** cold check set — so working
these six is not parity with review, and clearing them is not a prediction that
review will be clean.

## How to use it

**The order applies per defect, not per artifact.** Take one criterion or
section, walk the classes from 1, and stop at the first that fires — that class
names the repair, and the later ones would only redescribe it. Then move to the
next criterion and start again from 1. Work every defect the artifact has;
stopping early is about not over-classifying one of them, never about leaving
the others.

Class 1 precedes every other, because no amount of criterion craft repairs a
criterion that belongs to a different artifact.

Check the artifact you wrote, not your intentions for it. Guidance you restated
by hand is degraded at the point of writing, whatever you knew when you wrote
it — so read the text as a stranger would, and treat a hand-restated rule as a
defect on sight rather than as evidence you applied it.

## 1. The design should have delegated

An obligation is authored where an owner already exists, or is restated once
per consumer.

**Tell while writing.** You are explaining a rule rather than citing one. Or
the section decides something a downstream artifact exists to decide: a scope
document that fixes a contract, a contract that fixes a mechanism.

**Move.** Ask of every section: *does this decide something, or name something
for the next artifact to decide?* Naming a gap is the job; closing it early
converts a bounded gate into unbounded review surface. Before designing a
responsibility, record whether an owner for it already exists, and say so even
when the answer is no — an unrecorded search is indistinguishable from no
search.

**The repair is counter-intuitive.** Shortening or single-homing a long
restatement is the *wrong* fix, because a shorter restatement is still a second
home. Move it to the owning artifact and cite that. `SKILL.md` owns the
citation and duplicate-resolution rules; apply them here.

**No requirements-engineering standard covers this class.** The uniqueness
rules in that literature govern duplicated *text*; this class is duplicated
*responsibility*, which is why recognising it is an authoring habit rather than
a lookup.

## 2. The criterion cannot fail

No observation would falsify it, so a wrong implementation passes.

**Tells while writing.** It holds on empty state — no rows, no files, no
requests — and so is satisfied before any work happens. Or it asserts a
property whose comparison value the implementer supplies. Or it can only be
graded by reading the implementation's own account of itself.

**Move.** Name the failing state: the input, the state, or the absent artifact
that makes the criterion red. If you cannot name one, the criterion is
describing an intention, not an outcome. Prefer a criterion whose signal comes
from outside the work — a test, an exit code, a byte comparison, a rendered
surface — over one an implementer grades from its own output. An agent
correcting an error that arrives from outside itself succeeds far more often
than one grading its own prior output, so *where the signal comes from* is part
of the criterion's design rather than an implementation detail.

`../assets/spec.md` § Acceptance Criteria owns the detectability test and the
observable-outcome boundary; this class is the question that precedes them.

## 3. The criterion is unsatisfiable, or contradicts a sibling

No design satisfies it, or a neighbouring criterion forbids what it requires.

**Tells while writing.** It asserts an absolute — never fails, always
available, no false positives. It requires a guarantee at a boundary the system
does not control. Two criteria over one quantity pull in opposite directions.

**Move.** `SKILL.md`'s pre-review disconfirming-evidence step owns the probe
mechanism and its side-effect-free bound; point it at this criterion's
satisfiability rather than at the plan's mechanism, let the result change the
criterion, and cite it there. For a contradiction, reconcile the pair or drop
one; do not leave both and let review discover it.

Refusals need their positive path. A criterion set that only enumerates what is
rejected leaves undefined which valid input must still succeed, so an
implementation that refuses everything passes. Tie each refusal to a named
exclusion or budget, and state one representative input that must be accepted.

## 4. The criterion decays

It is true when written and false later, with nothing to notice the change.

**The tell is not the number, it is what the number counts.** A figure decays
only if the thing it counts can change after you publish it. A count of current
state — specs in a directory, files matching a glob, rules in a registry, rounds
a review has taken — is **live** and will go stale. A count of a past event,
dated, is **frozen** and cannot. Sort your figures that way first; auditing the
frozen ones is wasted effort, and it is how a live one gets missed.

**Live tells.** An exact count over a growing set. A count of the artifact's own
process or history, which looks like narration rather than measurement and so
escapes notice. A figure derived from another figure. A line-number citation. A
relative date. A revision identifier that only exists on a branch. A value
copied from a source that owns it.

**Move.** Ship the derivation, not the value: the glob, the predicate, the
command, or the query that recomputes it.

**Dating a value does not save it.** "Measured on <date> by <instrument>" makes
a stale figure honest, not current, and a bound that reads it still decays. So:
**if anything reads the figure — a bound, a gate, a decision — state the
derivation in the place that reads it**, not the value. Name the percentile, not
the number it evaluated to. A dated value may illustrate, and nothing may read
an illustration.

**A figure you have restated twice is the defect.** The second correction is the
signal: the cost is not in getting the number right, it is in storing a number
at all. Convert it to a derivation or delete it, and do not spend a third
attempt on the value.

Two clauses, and the second does not follow from the first:

- **Nothing hand-enumerated that is derivable.** If a set has a
  machine-readable source, read it. A parallel enumeration creates a
  completeness obligation that did not exist before, cannot be discharged by
  more machinery, and is wrong at the next upstream edit. Compare against the
  definition *at the level it is stated* — a finer decomposition of a coarser
  definition is legitimate.
- **Nothing precise that is decoration.** A figure or enumeration no criterion
  depends on is surface that decays and that every review round re-litigates
  for no gain. Test it by deleting it: if no criterion, gate, or decision
  changes, it was decoration. This is a test over the *artifact's* precise
  surface, wherever it sits; `../assets/spec.md` § Acceptance Criteria owns the
  narrower question of whether a claim inside a criterion makes a wrong
  implementation detectable. The two intersect on a figure inside a criterion
  and answer different questions about it.

**Related class: the criterion targets a projection.** A scope statement or
criterion that names a generated, built, or projected file pins an output
rather than the source that produces it, so the fix lands where the next build
overwrites it. Retarget to the owning source and name the regeneration
mechanism. This class has no analogue in requirements-engineering literature,
which assumes a hand-maintained document.

## 5. The criterion is too big

It carries several independently verifiable outcomes, so a coverage check
passes while part of it is unimplemented.

**The shape rule is not here.** `../assets/spec.md` § Acceptance Criteria owns
the conjunction and substitution test and its worked examples, and those
examples — not an adjective in a rule — decide where the boundary falls. Read
them before splitting anything.

**What belongs here is the ordering and the threshold.**

- **Order by length, longest first, and apply the shape test in that order.**
  Length is a sampler that finds candidates; it is not a bound, and there is no
  per-criterion word budget. Long criteria are where a review loop's findings
  concentrate.
- **Treat a criteria count above a screening threshold as a signal to stop and
  talk, never as a refusal.** Derive the threshold rather than inheriting a
  number: measure your own shipped corpus — a defined glob, a status predicate,
  and a stated percentile — and date the measurement. A slice with fewer
  genuine criteria ships with fewer; the threshold is a ceiling and a stall
  point, never a floor.

The evidence behind a count threshold is real but adjacent: an agent's joint
satisfaction of independent, verifiable constraints falls steeply as their
number rises, measured on single-generation benchmarks rather than on an
implementation loop with gates between attempts. That justifies a conversation,
not a gate.

**Altitude precedes size.** Every bound above measures a property *within* an
artifact, and none asks whether this is the right artifact. Three tells that an
artifact sits above its altitude: it proposes no slice the next author could
confirm, and the missing input is a decision rather than a detail; it carries a
design position, an evidence base, an inventory, or a governance concern rather
than citing one; it changes the gating of its siblings, which a peer cannot
do. **A criterion that
is too big is cut; an artifact at the wrong altitude is moved** — trimming
never repairs it.

## 6. The property is not mechanizable

The criterion is a gate over a judgement, or over an artifact grading itself.

**Tells while writing.** Its verdict needs taste, tone, or reasonableness. The
thing being measured is the same thing that defines the measure. The check
would run against prose whose author chose the wording.

**Move.** Ship it as advisory guidance and say so, or convert it to a
mechanical proxy and accept that the proxy is what you get. Do not gate on it.
Published measurements of a lexical predicate over authored prose disagree
enough between corpora that no single false-positive rate carries across them,
and the low end has been low enough that such detectors are built to triage
candidates for a human rather than to issue verdicts. So calibrate a check on
your own corpus before proposing to block on it, and treat a check that cannot
be calibrated as guidance that never blocks.

**Two classes sit here and cannot be moved out.**

- **Cuts a non-waivable control.** A non-goal or deferral drops trust-boundary
  validation, data-loss handling, security, privacy, accessibility, a required
  test, a migration, documentation, or an approval. Return it to scope, or
  record an explicit named owner waiver. Whether a control is waivable is a
  judgement, so no predicate replaces reading the deferral list.
- **Draft narration.** The body carries errata, withdrawals, dead ends,
  superseded trade-offs, hedged claims, unrequested advice, or an account of
  your own searches. `SKILL.md`'s present-tense body rule owns the repair and
  the reason for it. What belongs to this class is only why it stays a reading:
  no predicate decides which sentence is superseded.

## Optional: a criterion syntax

Fixed clause order makes a missing trigger or a missing response visible
without judgement. Five shapes cover most criteria — these are the EARS
patterns (Easy Approach to Requirements Syntax), named so you can look up the
originals:

| Shape | Form |
| --- | --- |
| Ubiquitous | `the <system> shall <response>` |
| Event-driven | `when <trigger>, the <system> shall <response>` |
| State-driven | `while <precondition>, the <system> shall <response>` |
| Unwanted behaviour | `if <trigger>, then the <system> shall <response>` |
| Optional feature | `where <feature is included>, the <system> shall <response>` |

The unwanted-behaviour shape pairs with a positive shape over the same subject,
which is the cheapest guard against the one-sided contract in class 3.

Use this when a criterion reads ambiguously, not as a house style. The evidence
for a fixed syntax is practitioner-grade, and no controlled study shows it
reduces defects — so it is an aid and never a gate.

## What this rubric does not claim

No published controlled comparison shows that writing a spec first improves an
agent's success rate. What is measured is narrower and still useful: adherence
falls as simultaneous constraints multiply, correction improves sharply when the
signal comes from outside the actor, and success falls steeply as the number of
surfaces a change touches rises. The first two are why this rubric prefers
few criteria and external signals. The third bears on how a slice is scoped,
which this rubric does not govern. Anything stronger than that is not yet
evidence.
