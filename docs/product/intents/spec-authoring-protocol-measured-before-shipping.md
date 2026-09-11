# Spec authoring and response protocols: deferred until a frozen-case run can score them

- **Status:** Draft
- **Kind:** outcome
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** work-loop-delivery-efficiency — [Work-loop delivery efficiency](work-loop-delivery-efficiency.md)

## Outcome

- **Steerable input:** Ship the selection procedure, the set-level sweep and the
  review-response protocol that `acceptance-criteria-set-construction` drafted,
  once a frozen-case run can show each change improves criterion selection
  rather than only sounding better.
- **Lagging outcome:** An author's criterion set is measurably better with the
  procedure than without it — higher recall of stated objectives and guardrails,
  lower admission of implementation detail, duplicate claims and example-only
  variants.
- **Guardrail:** No part of this ships on an argument. Each change is scored
  against the frozen cases before and after, and a change that lowers recall is
  refused however much it improves rejection.

## Why this is deferred rather than shipped

The protocols were authored, reviewed across sixteen adversarial rounds, and
never measured. The one measurement that exists says the guidance makes
selection **worse**.

A frozen case was built with four must-admit items (two objectives, a
non-waivable guardrail, a stated bound) and four must-reject items (a named
helper, a duplicate claim, a motivating example, an already-enforced property).
Two fresh models authored criteria for it — one with no guidance, one told to
follow the shipped criterion-shape guidance:

| | no guidance | with the shipped guidance |
| --- | --- | --- |
| criteria returned | 6 | 3 |
| decidable recall | 2/2 | **1/2** — lost the guardrail |
| decidable rejection | 1/3 | **2/3** — stopped naming the helper |
| determinism objective | stated | **absent** |

The guidance improved rejection and destroyed recall. By the scoring order the
same spec defines, a smaller set obtained by losing a guardrail is a failure,
not a success. Neither arm rejected the already-enforced property.

**That is the whole case for deferring.** Sixteen rounds argued the prose; two
subagent calls decided it. Nothing here ships until the run is built and the
score moves the right way.

## What the deferral also revealed

- **Twenty-three of forty criteria had no mechanical oracle.** Their only check
  was that a sentence exists, which an implementation satisfies by writing it and
  a reviewer can always object to. A contract made mostly of those does not
  converge: each round produces fresh plausible objections at about the rate the
  last round's are resolved, and nothing external decides between them.
- **The protection was never in the criteria.** The pack suite pins forty-seven
  rule-name keys and zero criterion identifiers, so demoting the criteria loses
  the ceremony and keeps every check.
- **The stable layer was already upstream.** Across fifty-six commits to the
  spec, the criteria changed in forty-six and the upstream outcome in none.
- **Two authoring rules landed in the skill from this analysis** — that an
  obligation whose only check is a sentence's existence is design material
  rather than a criterion, and that the upstream intent freezes when shaping
  closes and the spec cites it rather than restating it. Both are
  authoring-protocol prose and so belong to this intent's scope; they are
  recorded here because shipped guidance with no criterion needs a named owner.

## Boundary

- Includes the procedure, the set-level sweep, the response protocol, per-task
  grounding, disposition recording and the discovery pass — the criteria carried
  verbatim below.
- Includes building the frozen-case run that scores them, which
  `acceptance-criteria-set-construction` retains as its own criteria.
- Excludes the three shipped checkers, the identifier convention, the release
  surface and the eval register: those have mechanical oracles and stay in the
  delivering spec.
- Excludes shipping any of this on a review round's approval. The frozen-case
  score is the gate.

## Owner

- eugenelim, Platform Core maintainer.

## Unresolved questions

- Is the recall loss an artifact of one case, or does the guidance trim hard
  across all three shapes? One case cannot tell, and the answer decides whether
  the fix is a wording change or a rethink.
- Can a must-admit seed be made decidable without making it echoable? Scoring
  recall on a literal the prompt supplies is mechanical but rewards copying.
- Does the response protocol need the same gate? It has evidence of value —
  findings answered without an edit — but that lowers repair cost rather than
  the arrival rate, so it may be worth shipping on weaker evidence.

## The deferred criteria, carried verbatim

Preserved exactly as authored so nothing is lost in the move. Identifiers are
retained for traceability and are retired in the delivering spec; they are not
live criteria here.

- [ ] **AC-0001.** The skill's acceptance-criteria step carries a numbered selection
      procedure whose steps run in the order name-obligations, admit,
      attach-scenarios, route, set-level pass.
- [ ] **AC-0002.** The procedure's hand-off to the criterion-shape owner sits after the
      routing step and before the set-level pass, so selection is complete
      before any candidate is worded and the pass reads a worded set.
- [ ] **AC-0003.** At that hand-off the procedure instructs composing each criterion from
      the parts its earlier steps already named — the obligation, the surface
      that observes its failure, and its disconfirming and positive cases —
      rather than writing a sentence and testing it afterwards.
- [ ] **AC-0004.** The procedure admits a candidate only on a named ship-blocking ground:
      an externally observable behaviour, a required refusal or recovery path,
      a compatibility or safety guardrail, or a measurable quality property
      under named conditions.
- [ ] **AC-0005.** Admission additionally requires naming the surface on which the
      candidate's failure would be observed, and the procedure states that a
      candidate whose observing surface cannot be named stays a candidate
      rather than becoming a criterion.
- [ ] **AC-0007.** Each admitted obligation carries one positive and one disconfirming
      scenario.
- [ ] **AC-0008.** The procedure routes each rejected candidate to a named destination:
      implementation choices to the plan, concrete cases and fixtures to
      Testing Strategy, an existing repository obligation to its owner,
      explanatory prose to the body, a duplicate or decoration out of the
      contract, and an obligation whose content only the build can settle to the
      plan as a discovery predicate carrying its constraint, required outcome
      and verification mode.
- [ ] **AC-0009.** The set-level pass runs over the loop contract as one set — the spec's
      criteria together with the plan entries that trace to them — rather than
      over the criteria alone, and tests necessity, uniqueness, consistency —
      which reads the body's own prose against the criteria, not only criterion
      against criterion, because the Objective, the Boundaries and the durable
      outputs all make claims a criterion can contradict. Consistency also tests
      the body for the two claim kinds that decay with no edit at all: narrated
      delivery history, which the retcon discipline sends to the changelog, and a
      count standing beside the set it enumerates, which AC-0018 forbids. It also
      re-reads each criterion against the criterion-shape rules `assets/spec.md`
      owns in its `## Acceptance Criteria` section, which the skill already
      names as their single owner, and never restates them here. Where a rule
      carries a pinned name the pack itself resolves — `observable-outcome` —
      the member names the pin, which obliges the re-read as specifically as
      reproducing the rule would while leaving one home for the wording. The
      remaining rules are reached through that section, because a pinned name
      the pack does not define is a token an adopter cannot resolve. The member exists because a rule with an
      owner is read when a criterion is written and never again, which is how a
      criterion accretes rationale round over round —
      joint feasibility, coverage, propagation, and residual freshness. The
      members carrying a stated plan-side question are named: uniqueness asks whether a
      criterion and a construction test claim the same thing, coverage asks
      whether every admitted criterion has a plan entry, and propagation asks
      whether a touched criterion's entry still matches it. The rest read the
      criteria. Propagation cites the rubric's sibling
      check as its owner rather than restating it, adding only its scope and its
      timing: it re-reads each touched criterion's construction test and
      verification entry against that criterion's current wording, because a
      text search cannot see a test that still describes the pre-repair claim,
      and it re-reads in the other direction too: every sentence citing a
      criterion is checked against what that criterion now says, because a
      citation can resolve and still name the wrong criterion, which no
      mechanical check detects. It completes in the same round before the round
      is reported. Residual
      freshness re-tests each recorded residual against current state rather
      than carrying it forward on its last wording.
- [ ] **AC-0010.** The procedure defines coverage as satisfied for an Objective outcome or a
      non-waivable Boundary when it is either an admitted criterion or a routed
      disposition naming its owner, so no item can be both uncovered and
      correctly routed.
- [ ] **AC-0012.** The set-level pass reads the criteria back to what they serve: every
      admitted criterion names the Objective outcome, non-waivable Boundary, or
      applicable Durable Output its failure would leave unmet. A criterion that
      names none of those is decoration and is cut.
- [ ] **AC-0013.** The procedure defines the necessity check operationally: for each
      criterion, state its whole failure predicate — the input, the expected
      outcome, and the observing surface — then confirm no sibling criterion and
      no existing repository control already enforces that same predicate. A
      matching input alone is not coverage: two controls can red on one input
      while asserting different outcomes. A criterion whose predicate is already
      enforced is merged, removed, or reduced to a citation of that owner.
- [ ] **AC-0014.** `guides/core/reference/acceptance-criteria-authoring.md` publishes the
      procedure's stages AC-0001 enumerates.
- [ ] **AC-0015.** That guide cites the criterion-shape owner by document name, and none of
      that owner's pinned rule sentences appears on the page.
- [ ] **AC-0016.** The set-level pass states that a large irreducible set survives it, and
      that an independently shippable cluster becomes a decomposition proposal
      rather than a compound criterion.
- [ ] **AC-0017.** The procedure cites the rubric's threshold section as the owner of how a
      count threshold is derived and what an above-threshold count means, and
      states the threshold it branches on rather than deriving one: the rubric owns
      how an author measures a corpus and arrives at a percentile, this procedure
      owns only what happens on each side of whatever threshold that produced.
      While the set is at or above the author's stated threshold, the procedure
      requires the uniqueness check to be re-run pairwise across the whole set
      with its result recorded; below that one position it requires only the
      per-criterion check against neighbours. One threshold, both branches, no
      band left undefined.
- [ ] **AC-0022.** The skill's plan step carries the plan-authoring rules: a fact belongs in
      the design unless a task must implement or verify it; a `Done when` points
      at its own `Tests`; an obligation a completion gate must read belongs in
      `Tests` rather than `Approach`; a claim about a check names the comparison
      its oracle performs; a `Done when` closes on every command its own
      `Tests` names, by reference to that list rather than by restating it,
      since a closing condition that omits one closes green while that command
      reds — and a second copy of the list is itself the drift this rule was
      written after; a `Tests`-outruns-`Approach` ratio is read before
      it is cut; the fields a completion gate reads — `Touches`, `Tests`,
      `Done when` — are contract while `Design`, `Approach`, `Grounding` and
      `Risks` are working material an implementer corrects in place, because
      treating every field as contract spends review rounds on prose no gate
      consumes; a stated mutation is executed and its red recorded, because
      describing a mutation is not performing one and a criterion whose required
      mutation nobody ran stays green while the thing it pins is deleted; a task
      added after these rules landed is walked against all of them in the round
      that adds it, since a rule applied to the tasks that existed when it
      shipped and to no later one is a rule that decays silently; and a
      whole-plan walk precedes review.
- [ ] **AC-0023.** The skill's review step names the responses available to a sustained
      finding — repair the artifact, narrow the claim to what its check reaches,
      cut the item the finding is about, dismiss the finding with its reason
      recorded and re-present it to the next round, repair the generator rather
      than the instance, route it to an owner that already covers it, bound it
      out of scope and record a follow-on that names its new owner, or accept it
      with the reason it is proportionate recorded — and
      states that a sustained finding does not by itself require an edit. Where
      a sustained finding instantiates a rule the contract already carries, the
      response includes a count of every other instance before any repair, and
      the procedure says why: repairing the named instance leaves the class, and
      a reviewer sees the instances it happened to look at rather than the set.
      Repair also carries a rider, scoped to what the set-level pass cannot
      reach: it sweeps the prose adjacent to a changed artifact outside the loop
      contract — a module docstring describing the predicate beneath it, a header
      naming a set the code no longer has. Inside the contract AC-0009's
      propagation member owns that re-read, and this rider adds nothing to it.
- [ ] **AC-0024.** Where a finding is that a claim and its check disagree in reach, the
      procedure states both directions and how to choose. A claim reaching
      further than its check is strengthened when some check can reach the
      stated obligation and narrowed when none can. A *check* reaching further
      than any claim — shipped behaviour no criterion authorises — is brought
      under a criterion or cut. The procedure states why the second direction
      needs saying: the first shows up as a criterion nothing can verify, while
      the second is invisible, because the artifact works and nothing is
      missing from it.
- [ ] **AC-0025.** Where a finding is that a criterion demands content the guidance
      governing its destination surface forbids, the procedure states that the
      criterion changes and the forbidden content is never authored to satisfy
      it. A criterion no implementation can satisfy is a defect in the
      criterion, and a repair round is where one is most often introduced.
- [ ] **AC-0026.** The skill's review step instructs the stop-decision report to carry the
      finding trend by round, split into findings against text that was settled
      before the round and findings against text the round itself changed, and
      for each remaining residual its consequence,
      the responses available to it, and what each would cost — so the owner
      chooses between stated options rather than reading a list of problems. It
      states the protected-risk-class condition directly and enumerates no class
      list, because shipped pack content carries no citation to an internal
      record. The owner of that class set is
      `docs/product/intents/work-loop-review-economics.md`, its `## Outcome`
      section's **Guardrail** bullet, named
      here in the contract and deliberately not in the pack. The split is
      load-bearing for the stop decision: an undivided count cannot distinguish a
      contract still yielding defects from one whose remaining findings are
      churn the repairs themselves introduced, and those two states call for
      opposite decisions — keep reviewing, or stop and build.
- [ ] **AC-0027.** The procedure names the earn-its-keep test and states what it
      is: the conjunction of the checks its siblings define — a criterion
      names the outcome its failure would leave unmet, and no sibling criterion
      or existing repository control already enforces its predicate. Without the
      name stated over both halves, this criterion scopes a test the contract
      never establishes. That test applies to every criterion in the set rather than
      only to those added during review, and runs while rounds are still
      running rather than only after they converge.
- [ ] **AC-0034.** The procedure requires each candidate's disposition to be recorded,
      and the candidate and final counts that follow from those dispositions. The
      rubric owns deriving a count threshold from the author's shipped corpus and
      what an above-threshold count means; it owns no record of what this
      selection did. That record is the procedure's own output — without it
      nothing distinguishes an obligation admitted from one routed to an owner,
      and the set-level pass has no list to read back against.
- [ ] **AC-0036.** Once durable outputs are planned and their destinations resolved,
      and before the spec body is written, the procedure runs a grounding pass
      over those destinations and records what it returned. This is discovery,
      not validation: no criterion exists yet, and the output is design input —
      what already owns these surfaces, what already governs them, what already
      runs them, and what an accepted decision has already settled about them.
      The procedure says why the placement is load-bearing: before durable
      outputs there are no destinations to ground, and after the body is written
      the same facts arrive one criterion at a time, against a design they would
      have changed.
