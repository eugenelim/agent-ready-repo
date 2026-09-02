# Brief: authoring contracts that survive review

- **Slug:** `agent-authoring-input-quality`
- **Received:** 2026-09-02
- **Owner:** Repository maintainers (`ini-002`)
- **Status:** Draft

## Outcome

An author — human or agent — writes a spec and plan that a review loop can
converge on, and does not open one at all when the upstream is not ready. Today
neither holds: a contract can be authored with no upstream and no registration
and nothing objects, and once authored, most of what review finds is not the
subject but the way it was written.

Two things change:

- **Criteria and tasks stop being fragile.** A criterion states an outcome that
  can fail, once, in one place. A task says what to verify rather than spelling
  out the assertion. Review then finds defects in the subject instead of in the
  prose about the subject.
- **A contract is not opened over an undefined outcome.** A pressure test at
  creation asks what the work descends from and whether its unknowns are closed,
  and hands the work to brief authoring when they are not.

This only **partially** prevents non-convergence, and that is deliberate. A
better contract still gets things wrong; what a loop does on that discovery is
[`agent-loop-escalation-recovery.md`](../intents/agent-loop-escalation-recovery.md).

## Success metrics

- Review rounds on a new contract find defects in the subject rather than in the
  criteria's wording — measured by classifying a round's findings, not by
  counting them.
- A contract whose upstream is missing or unready is redirected before its body
  is written, and the redirect is recorded rather than inferred.
- Every rule this work ships can be shown to have fired at least once. A rule
  with no firing is withdrawn, not re-worded.

## Scope / Non-goals

**In scope**

- The failure-point rubric, and the authoring instructions derived from it.
- The pre-creation pressure test and its redirect.
- The activation mechanism for both, and the measurement that says whether they
  activate.

**Non-goals**

- What a loop does once it has discovered the contract is wrong. Separate item,
  linked above.
- Rewriting the cognitive-load or cut-before-adding rules. The question is why
  they do not activate, not whether they are well written.
- Changing what reviewers do, or how findings are adjudicated.

## Appetite

The rubric and the instructions are cheap — they are distillation of evidence
already in this repository. The pressure test is a small gate with one open
design question (where it fires so it cannot be discharged by filling in a
missing field). **Activation is the expensive part, and it gates the rest**: if
the measurement says written guidance does not bind here, the deliverable becomes
machinery and the appetite changes.

## What actually works, and what does not

This is the load-bearing finding, and it should shape every deliverable.

Across the eleven rounds that produced this evidence, the mechanisms that caught
defects **on their first run** all bound the document to something outside
itself:

- criterion-identifier parity between the spec and the plan;
- assumption-citation parity, both directions;
- claims bound to a live symbol table rather than to prose;
- mutation proofs — delete the row, and a specific case must redden.

The rules that lived only as prose — the cognitive-load simplification, the
cut-before-adding razor, the observable-outcome rule — were loaded in context for
the whole of that work and fired never.

So a rule's value here is not how well it is written. It is whether it binds to
code, to a sibling document, or to a mutation. The rubric below is written as
prose because that is how it is legible; whether any row of it ships as prose is
the activation question's to answer.

## A rubric of known failure points

Distilled from this repository's memory and its `docs/knowledge/` topics, plus
the abandoned attempt. Each row is a shape that has actually produced review
findings here, not a hypothetical. The right-hand column is what an author does
instead — these are the candidate instructions, and per the activation section
above they must not ship as prose alone.

**The criterion cannot fail.** The most expensive class, because it reports
confidence.

| Shape | Instead |
| --- | --- |
| An absence or reachability claim whose walk resolves nothing | Pair it with a positive control: a root known to reach the thing, asserted to reach it |
| A negative-path claim where an unstubbed collaborator raises the same error | Stub every collaborator around the negative case, then delete the control and confirm it reddens |
| A bound asserted over a domain that cannot vary the bounded quantity | Assert it against a planted input as well as the domain |
| An instrument blind to the layer the claim is about | Name the interception layer in the criterion, and prove the detector fails on a planted violation |
| A pin that a sentence exists in a file | Presence is not behaviour. Pin what the sentence causes, or drop it |

**The criterion is unsatisfiable, or contradicts a sibling.**

| Shape | Instead |
| --- | --- |
| Two bounds over one quantity where one dominates | Order them so each fires first for some input, or declare the dominated one non-binding and name what fires instead |
| A criterion whose literal text forbids the mechanism it mandates | State the forbidden operation class, not "no access of any kind" |
| Two criteria that cannot both hold | One rule, one home. If a second criterion carves an exception, the first must say so |
| A criterion demanding an artifact no task produces | Every artifact a criterion requires needs a durable-output row and an owning task |

**The criterion decays.**

| Shape | Instead |
| --- | --- |
| An exact count over a corpus that grows | State the property, not the count. A count needs an owner and a regeneration step |
| A line-number citation in a portable artifact | Cite the symbol, or the commit |
| A figure derived from another figure | One home per number; the other site references it |
| A table inventorying what the change will invalidate | Ship a regenerator, not a snapshot |

**The criterion is too big, which is what drives nit volume.**

| Shape | Instead |
| --- | --- |
| An AC past roughly 150 words | Re-partition, do not summarise. Measured elsewhere in this repo: the three longest ACs absorbed the majority of ~60 findings across sixteen rounds, while the median AC stayed quiet |
| One checkbox over predicates with separate failure modes and separate remedies | Split, each with its own box and its own plan bullet |
| Mechanism inside a criterion | It gets re-litigated every round and drifts against the plan's copy |
| Explanatory prose inside the normative section | Bound by nothing, so it decays on every edit |

**The property is not mechanizable at all.**

| Shape | Instead |
| --- | --- |
| A gate over a judgment ("is this well-founded?") | Split it: the gate asserts declared shape and required fields; a named human owns the judgment, recorded per item. Widening a defeated gate a second time is the tell |
| An artifact that measures a property of itself | No fixpoint exists; it settles into a two-cycle. Break the self-reference rather than looping |

**Process shapes, not criterion shapes.**

| Shape | Instead |
| --- | --- |
| A criterion resting on an unverified claim about live behaviour | Name the oracle and take the observation before writing the criterion. This is what ended the abandoned attempt |
| Remediating a finding against the file as it is now | A reviewer reports against the file at dispatch. Re-check before repairing; one grep |
| A large repair on a long contract | It introduces defects at roughly the rate it removes them. Keep contracts small enough that a repair is local |

**For plan tasks specifically.** Tasks name what to verify, not how. A bullet that
spells out the assertion, the fixture, and the expected message is pseudo-code:
it will be reviewed as code while being unable to run, and every detail in it is
a claim the next round can falsify. State the mutation that would redden the
check in one line; leave the matrix to the implementer.
## The undefended boundary: what triggers a spec

Detection, response, and activation are all mid-loop. There is a fourth guardrail
missing before the loop starts, and it is the one that would have prevented this
specific failure most cheaply.

**What is defended today.** `new-spec` does elicit — it surfaces an Unverified
assumption list and waits for human confirmation before writing the spec body.
That is a real gate, and it defends the spec's *content*.

**What is not.** Nothing tests whether the spec should exist yet. The skill's
invocation triggers are a disjunction in which "the user explicitly requests a
spec" is sufficient on its own. The `Brief:` header is stamped only when the
author arrived from a confirmed brief slice; nothing checks it resolves, nothing
checks the upstream is Ready, and `none` is accepted everywhere — it is the value
in the overwhelming majority of this repository's specs. The spec-status lint has
no provenance invariant. The one detector that would notice, `unregistered_work`,
fires at **dispatch**, not at creation.

**How that played out here.** The abandoned spec was authored by an earlier
session with no brief and no workspace entry. Nothing objected for the artifact's
whole life. The controller then registered it mid-session — which *satisfied* the
only detector that would have flagged it. The guardrail was discharged by filling
in the missing entry rather than by answering whether the spec was warranted, and
ten review rounds followed.

**Shape of the guardrail, to be designed rather than assumed.** A pressure test at
the trigger, before any body is written, asking roughly:

- Is there a defined outcome, or is this still shaping?
- What upstream does this descend from, and is that upstream Ready?
- Are there load-bearing unknowns still open — claims about live behaviour with no
  oracle taken? (This one had three, none named at the time.)
- If there is no upstream: is direct authoring actually justified against the
  durability triggers, and is that justification recorded rather than assumed?

**On a gap, redirect rather than refuse.** The useful response is probably not
"you may not write this spec" — an agent told no will find another route. It is to
hand the work to `author-delivery-brief create`, which is built for exactly this
input and which refuses to invent missing content, then return when the upstream
is Ready. That keeps the elicitation where a human is already expected.

Open design questions, and the reason this is shaped rather than specified: what
distinguishes a legitimate direct spec from one that skipped shaping, given
direct authoring is explicitly allowed; whether the test can be mechanical at all
or is another judgment that needs a named human; where it fires so that it cannot
be discharged the way the registration check was; and whether the redirect is a
hard stop or a recorded override. The activation section above applies to this
guardrail as much as to any other — a pressure test nobody runs is a rule that
does not fire.
## Activation design and measurement

Required of this brief and of every rule it produces, because the evidence is
that rules of this kind do not fire.

The cognitive-load rules are not prose-only — several gates enforce them. Those
gates read the packs, the root guidance, the seeds, and the changelog. The
progressive-disclosure lint has a case asserting that an authored
`docs/specs/<feature>/spec.md` is *not* in its results. Authored work-loop
artifacts sit outside the enforcement boundary by design, so the guidance is
loaded at every turn and enforced nowhere near where it would bind.

Every rule this work ships therefore carries three things:

- **An activation point** — the moment in the loop where the rule is consulted
  and something changes as a result, not merely the file it is written in.
- **A measurement** — how to tell activation from presence. Compare what the rule
  asks for against what the author produced, on artifacts the author wrote, not
  on the surfaces the rule was originally written to govern.
- **A failure mode when it does not activate** — because a rule that silently
  does nothing is worse than an absent one: it makes the gap look covered.

**The first measurement needs no new mechanism.** Score specs, plans, and briefs
already in this repository against the guidance in force when each was written.
That says how often these rules activate at all, and whether the two known
instances are typical or unlucky. It runs before anything else here is designed.

## Risks

- **This brief ships another unactivated rule.** The most likely failure, and the
  reason activation is scoped in rather than assumed. The withdrawal metric above
  is the guard.
- **The pressure test is discharged rather than answered.** The existing
  registration check was satisfied by filling in the missing entry, not by
  answering whether the spec was warranted. A gate at creation can fail the same
  way.
- **The rubric grows into doctrine on one instance.** A rule was shipped from
  this same evidence, as a minor release, and withdrawn a day later as unearned.
  The hypothesis is recorded in `[backlog].open` with what would earn it.

## Rabbit holes

- **Do not mechanize a judgment.** "Is this criterion well-founded?" is not a
  predicate. Where the same gate is defeated twice by different surfaces, split
  it: the gate asserts declared shape and required fields, a named human owns the
  soundness call.
- **Do not verify guidance by parsing the guidance.** A check that a sentence
  exists in a file proves presence, which is the thing already known.
- **Do not let the rubric become a review checklist.** It is authoring guidance.
  Handed to reviewers it becomes a source of nits, which is the problem it exists
  to reduce.

## Ready gaps

- **No appetite is set**, and activation's answer changes it.
- **No slices are proposed.** `continue` selects them. The retrospective
  activation measurement is the natural first, and it can run before any of the
  rest is designed.
- **Where the pressure test fires is undecided**, and it is the open design
  question that matters most — see the boundary section above.

## Spec map

None. No slices confirmed, no spec derived.

## Provenance

- Source: repository origin. Distilled from this repository's memory, its
  `docs/knowledge/` topics, and one abandoned delivery attempt whose spec and
  plan are preserved at commit `e1bdde746`.
- Promoted from a shaping intent of the same slug on 2026-09-02, which was itself
  split out of `docs/product/briefs/work-loop-next-action.md`.
