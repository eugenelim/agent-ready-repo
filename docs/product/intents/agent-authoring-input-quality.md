# Intent: authoring input good enough that the loop can converge

- **Slug:** `agent-authoring-input-quality`
- **Type:** `shape`
- **Raised:** 2026-09-02
- **Owner:** Repository maintainers (`ini-002`)
- **Stage:** Shaping — designable now

## Why this exists, and what it is not

A review-and-repair loop can run indefinitely without converging. Two things
would change that, and they are different kinds of work:

- **Prevention** — make the contract good enough going in that the loop has
  less to find, and refuse to start one over an undefined outcome. That is this
  item. It is designable now against evidence already in the repository.
- **Escalation** — when a loop discovers mid-flight that the contract is wrong
  anyway, decide which artifact level to return to. That is
  [`agent-loop-escalation-recovery.md`](agent-loop-escalation-recovery.md), and
  it is open research with competing hypotheses.

Prevention only *partially* solves non-convergence, and saying so is the point:
a better contract still gets things wrong, and the escalation item owns what
happens then. Neither waits on the other.

## The evidence

One spec-authoring loop ran eleven pre-EXECUTE review rounds in a single run
before a human intervened, and was abandoned. Most of what those rounds found
was not the mapping the contract existed to state — that part survived
independent re-derivation. It was everything authored around it: criteria that
could not fail, criteria that contradicted each other, counts that decayed,
mechanism inside criteria that then drifted against the plan's copy, and
explanatory prose in the normative section that nothing bound.

That is a quality-of-input problem, and it is addressable with instructions and
a gate rather than with research.

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
## The activation problem underneath all of them

Every hypothesis above proposes a rule. This repository has already shipped two
rules that should have prevented what happened, and neither fired. That is a
prior question, and it changes what any response has to include.

**The two instances, both in one session, with the authoring agent as subject.**

- The cognitive-load simplification and the cut-before-adding razor are both
  present, both routed from the root context, and both were in the agent's
  loaded context the whole time. The artifacts it then authored were long and
  dense with precise claims — the opposite of what the rules ask.
- The spec-authoring guidance already said a criterion names an observable
  outcome and that naming a helper or a call sequence means the content belongs
  in the plan. The agent read that rule, cited it to reviewers as governing
  authority, and still put mechanism into criteria repeatedly.

**Presence is not activation, and neither is enforcement — if the enforcement is
scoped elsewhere.** The cognitive-load rules are not prose-only; several gates
enforce them. But those gates read the packs, the root guidance, the seeds, and
the changelog. The progressive-disclosure lint goes further and has a case
asserting that an authored `docs/specs/<feature>/spec.md` is *not* in its
results. Authored work-loop artifacts are outside the enforcement boundary by
design.

So the rule is loaded at every turn and enforced nowhere near the moment it
would bind. An agent authoring a spec is holding the guidance in context and
receiving no signal from it.

**What this means for the work.** A response to non-convergence that is another
rule, shipped the same way, has no reason to behave differently. Any hypothesis
above must come with:

- **An activation point** — the moment in the loop where the rule is consulted
  and something changes as a result, not merely the file where it is written.
- **A measurement** — a way to tell activation from presence. The distinction is
  observable: compare what the rule asks for against what the agent produced,
  on artifacts the agent authored, not on the surfaces the rule was originally
  written to govern.
- **A failure mode when it does not activate.** A rule that silently does
  nothing is worse than an absent one, because it makes the gap look covered.

The cheapest available measurement is retrospective and needs no new mechanism:
the repository holds authored specs, plans, and briefs from many loops. Scoring
those against the guidance that was in force when each was written would say how
often these rules activate at all, and whether the two instances above are
typical or unlucky. That measurement should precede any new rule.
## Shape of the work

Three deliverables, in dependency order.

1. **Measure activation first.** Every item below is a rule, and this repository
   has evidence that rules of this kind do not fire. Score already-authored
   specs and briefs against the guidance in force when each was written. One
   retrospective pass; it decides whether any of this can be written guidance at
   all or has to be machinery in the loop.
2. **The rubric and the authoring instructions**, wherever activation says they
   will bind. Not as another bullet in a template that is loaded and unenforced.
3. **The pre-creation pressure test and its redirect**, designed against the open
   questions above rather than assumed.

## Not in scope here

- Detecting or responding to a loop already in trouble. That is the escalation
  item.
- Rewriting the cognitive-load or cut-before-adding rules themselves. The
  question here is why they do not activate, not whether they are well written.
- The `next` action projection, which is a delivery brief:
  `docs/product/briefs/work-loop-next-action.md`.
