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
- The delegation anchor: making a plan record whether an existing owner for the
  contract was found, alongside the imitation anchors the template already asks
  for.
- Whether a narrow delegated worker should run the ownership survey before
  authoring, given that every worker this repository defines today is a reviewer
  or a retriever and none runs before a spec exists — including its source
  selection, which delegates to the existing knowledge-surface contract rather
  than defaulting to reading the tree.
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

**The design should have delegated, and the criteria should never have been
written.** This class precedes all the others: no amount of criterion craft
rescues a contract that restates an obligation someone else already owns.

| Shape | Instead |
| --- | --- |
| An obligation restated per consumer — "the consumer must check X, refuse Y, degrade Z…" repeated at each site | Name the owner and delegate. `work-loop`'s SKILL.md does this in three lines: it invokes the `project-knowledge` producer profile, states that the profile owns request shape, confinement, privacy refusal, freshness, receipts, storage, and the enquiry envelope, and gives one named-absence receipt. Ten obligations, one sentence, one owner |
| A consumer-side trust posture spelled out as N statements on N surfaces | Route to the reference that owns it. Three `architect-*` skills each point at `references/knowledge-surfaces.md` for permission and degradation instead of carrying their own copy |
| Shortening or single-homing a long restatement | The wrong repair. If a passage is long because it restates someone else's contract, the fix is delegation, not compression — the delegation form collapses the review history rather than repairing it |
| A bounded search for an existing solution that was run, read, and not recognised | The razor's failure mode is not skipping the search. It is reading the answer without matching it to the problem. Ask explicitly: does an owner for this contract already exist, and what would delegating to it look like? |

**The instance from the abandoned contract.** Its `AC20` required the consumer's
trust posture to ship as five separate statements on the always-loaded surface,
and argued at length for why a reference could not hold them — because only one
routing row loaded that reference, so the control would be absent on the other
turns. The argument is locally valid and the conclusion still wrong: the repo's
own answer to "a consumer needs an obligation that a reference cannot reach" is
to name an owning profile and give it a named-absence receipt, not to inline the
obligations. That criterion, its five grep-able statements, and the rounds spent
tightening them all disappear under the delegation form.

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

**The repository-anchoring work is the clearest instance, and it fails twice.**
Real work shipped: the plan template carries a `Repository anchors:` field, and
`new-spec` states the bounded discovery rule and the ask-on-absence obligation.

*Its verification is presence-pinning.* Its tests assert that sentences exist in
the skill files — that the anchors field is present, that the phrase "one or two
analogous production implementations" appears, that the unanchored-mechanism
obligation is stated. Nothing reads an authored plan to see whether it has
anchors, whether they resolve, or whether they were used. That is this brief's
own "a pin that a sentence exists in a file" row, applied to the anchoring rule
by the anchoring rule's own tests.

*And it was complied with anyway.* The abandoned plan carried four anchors, all
imitation. Compliance was complete and the razor still never fired, because the
field asks what to copy rather than whether an owner exists.

Together those are the strongest argument here: **a rule can be shipped, tested,
and complied with, and still not do its job.** Anchoring is also where the
razor's evidence would live, so while nothing reads an authored plan's anchors
the razor cannot be *observed* to have run — which is why the two are one
problem.

Every rule this work ships therefore carries three things:

- **An activation point** — the moment in the loop where the rule is consulted
  and something changes as a result, not merely the file it is written in.
- **A measurement** — how to tell activation from presence. Compare what the rule
  asks for against what the author produced, on artifacts the author wrote, not
  on the surfaces the rule was originally written to govern.
- **A failure mode when it does not activate** — because a rule that silently
  does nothing is worse than an absent one: it makes the gap look covered.

### The razor's activation, specifically

The cut-before-adding razor is the hardest of the three to activate, because it
failed at recognition rather than at retrieval. The search ran and the hits were
read; they were not matched to the problem. "Search first" is already what the
rule says, so restating it changes nothing.

**Delegating the rung to a worker is what makes it activate, and that is the
general principle this brief should be read through.** A rule written in a
template may or may not fire, and the evidence here is that it does not. A step
performed by a worker either ran or it did not, and that is observable, binary,
and not open to self-report. **The invocation is the activation.** So the razor's
second rung stops being "remember to search and recognise" — an instruction that
demonstrably failed with the answer already in context — and becomes "the survey
ran, and here is its landscape."

- **Activation point** — the survey's invocation, before criteria are written.
  Not a moment of authorial diligence.
- **Telling activation from presence** — the plan carries the landscape the
  survey returned, and the author's disposition against each reusable component
  it names: delegated to, deliberately not, or not applicable and why. Both
  halves are checkable artifacts. The recognition itself stays a judgment, which
  is the split the unmechanizable-predicate row prescribes — but it is now a
  judgment made *against an organised inventory* rather than against memory of a
  grep.
- **Failure mode when it does not activate** — no landscape means the survey did
  not run, whichever way the author searched. That is the reading that would have
  caught this, because the search *had* run and nothing recorded what it found.

**This is the most transferable thing in the brief.** Any rule that can be
restated as a step some other worker performs becomes activation-guaranteed by
delegation. A rule that can only exist as prose in a template is the hard case,
and the activation measurement should tell us how many of the rules here fall
into which class.

### Repo anchoring: reuse over duplicate machinery

The plan template already asks for repository anchors — "one or two analogous
production implementations". That is **imitation** anchoring: find something
shaped like what you are about to build, and follow its shape. Useful, and not
the razor.

The razor asks a different question: **is there an existing owner for this
contract, so that no new machinery is needed at all?** Nothing currently asks for
that, and the two questions produce different answers from the same search.

The abandoned plan is the clean demonstration. It carried four anchors and all
four were imitation — an analogous read-only verb to copy the shape of, an
analogous idempotency check, analogous confined readers, an analogous schema
field shape. Every one made the new machinery better. None asked whether the
machinery should exist. The plan looked fully anchored while the razor had not
been run.

So anchoring should record both kinds, labelled, because only the second can
collapse the work:

- **Imitation anchor** — a production implementation whose shape this work
  follows. What the template asks for today.
- **Delegation anchor** — an existing owner of a contract this work would
  otherwise restate, with what delegating to it costs and what it leaves
  undischarged. Or an explicit, recorded *no owner exists* after a bounded
  search, which is the razor's own "decisive empty result".

### A delegated worker is the candidate mechanism, and one already proves it

The brief's own finding is that rules do not fire and mechanisms that bind do. A
narrow delegated worker is a mechanism, so it is the strongest candidate for the
razor's activation point — and this repository already runs one that demonstrates
the pattern.

**The proof case.** `finding-adjudicator` is `Read, Grep` only and is defined as
not discovering defects and not editing the target. It is given the *path* to a
reviewer's report, never the report body. Across the last two review rounds of
the abandoned work it refuted several findings the authoring agent had already
accepted — including one the agent had verified a premise for and then adopted
the wrong conclusion from. Three properties made that possible, and each maps
onto what the razor needs:

- it cannot repair, so it must judge;
- it has no authoring investment in the thing it is judging;
- its output shape forces a verdict per item, so "I looked" is not a valid
  return.

That is exactly the shape of "did the search return an owner for this contract" —
a question that is easy when it is the only question, and that the authoring
agent reliably failed while holding a whole session's context.

**The gap is real.** Every narrow worker this repository defines is a *reviewer*
or a *retriever*. None runs before authoring. So a spec author searches, reads,
and recognises in one context, which is where recognition failed.

**Do not build new machinery for it — this is the razor's own test case.** The
desk-research pack ships `decision-archaeology`, which walks time-ordered
artifacts to reconstruct why something was decided, and already carries a
*revival check* that flags rejected alternatives whose rejection no longer
holds. That is archaeology with a verdict, which is most of the shape. It is
backwards-looking where this need is forwards-looking — "does an owner exist for
what I am about to write" rather than "why was this decided" — and it lives in
another pack. So the first question is whether it extends, whether the reviewer
roster gains a sibling, or whether neither fits; not what to build.

**Why an isolated worker rather than the host's built-in explorer.** The case has
to be made, because a general-purpose explore agent already exists in the host
and the razor applies to this proposal as much as to anything else.

- **A dedicated worker guarantees the rule activates. This is the case.** The
  brief's central problem is that rules do not fire; a worker converts "did the
  author apply the razor" — unobservable, and empirically no — into "was the
  survey invoked and is its landscape in the plan", which is observable and
  binary. No prose rule can offer that, however well written. Everything below
  is secondary to it.
- **Context protection is the mechanism, not a side effect.** An isolated worker
  returns a conclusion; the authoring context never loads the corpus. That is
  already this repository's stated rationale for two shipped workers —
  `evidence-retriever` and `source-extractor` both describe themselves as
  preserving main-session context by collapsing material into a synthesis before
  returning. The pattern is established; it is not being invented here.
- **The needed output is a landscape, not located code and not a verdict.** The
  host's explorer reads excerpts to *locate* code, explicitly not to review it.
  Location was never the failure — the precedent came back in the opening grep.
  What was missing is the middle: an organised picture of what exists in this
  area, what each component owns, and which of them are reusable. Hits scattered
  through a long session are not that picture, which is why recognition failed
  with the answer already in context.
- **A verdict would be the wrong output, and asking for one is a mistake.**
  Judging "is this an owner for the contract I am about to write" needs the
  contract, and the worker does not have it. A worker forced to judge would
  return confident wrong answers, which is worse than none. Survey is what an
  isolated worker can do well: exhaustive, uninvested, and organised by
  ownership. Recognition stays with the author, who has the contract — but it
  becomes cheap, because the landscape is arranged for exactly that question.
- **What is genuinely new is the instruction set**, not the isolation. What to
  inventory, how to organise it by owner rather than by relevance ranking, and
  what to report about each component — owns / adjacent / reusable, and what
  delegating would leave undischarged. A generic explorer carries none of that,
  and it is real work to specify rather than a prompt tweak.

**Host built-ins versus a pack-defined worker — and the case deliberately does
not rest on capability.** Only one host's explorer was inspectable from here:
Claude Code's `Explore`, whose surface is read-only, tunable by breadth alone
("medium" or "very thorough"), reads excerpts rather than whole files, and is
described as locating code and explicitly not reviewing or auditing it. Codex,
Cursor, Copilot, and Gemini equivalents were **not** examined and no claim is
made about them.

That is why the argument is put on ownership rather than capability. These hold
for any host built-in, whichever host, however good its search:

| Property | Host built-in | Pack-defined worker |
| --- | --- | --- |
| Output shape ours to fix | No | Yes — `finding-adjudicator` mandates a three-section envelope and a narrow read envelope, and gets it |
| Authority declared as input | Only whatever a prompt carries | Yes — the adjudicator names the governing spec, repository instruction, and rubric |
| Versioned and reviewable by us | No; behaviour can change with a host update and we get no signal | In git, prose pinned by pack tests |
| Ships with the pack to adopters | No | Yes — `.apm/` is the export boundary |
| Instrumentable by our eval harness | **No, by construction** | Yes — the Tier-A harness already measures our own |

**The last row is decisive on its own, and it is the one this brief cannot
compromise on.** The premise here is that we cannot tell activation from presence
and the answer is an activation measurement. Delegating a rule to a component
whose firing we cannot instrument reintroduces exactly that blindness one layer
down — the rule would be "activated" by a black box we cannot observe. That is
the same failure in a new place, and it is a property of the component being the
host's, not of any host's search quality.

**Capability probably favours the built-in, and that is fine.** It is likely a
better searcher than anything written here. Searching was never the failure: the
precedent came back in the opening grep. What is needed is an organised
landscape, a fixed return shape, and an observable invocation — none of which is
a search-quality property.

Where a host provides isolation cheaply, reuse the isolation. The survey
instructions, the return shape, the authority binding, and the eval surface stay
ours.

One leg deliberately *not* used: host portability. This repository's declared
target vocabulary is `claude-code` only, so "a shipped pack cannot depend on one
host's built-in agent" is not established by the contracts and should not prop up
the case.

**Where the razor lands on this proposal.** The *isolation* is available and
should be reused rather than rebuilt. The *survey instruction set* is genuine
work: it is what turns a search into a landscape, and nothing here provides it.
Whether that ships as an agent definition or as a scoped invocation of an
existing worker is an implementation question for the slice, not a reason to
narrow the ambition to a prompt tweak. Reuse the isolation; author the survey.

**The survey's source is a design question, and reading files is the expensive
default.** Loading the tree to answer "what exists here and who owns it" is both
costly and lossy. Surfaces that answer it more cheaply already exist in general —
code-indexing tools, and platforms that maintain a queryable model of a codebase
rather than its text — and locally: this repository ships `docs/knowledge/` with
a topic index, and `project-knowledge` exposes a bounded enquiry envelope. The
local index is nascent rather than rich, so it is a surface to detect, not one to
depend on.

**And the contract for using such a surface already exists — in the same file
that supplied the delegation precedent.** `knowledge-surfaces.md` defines it:
detect a governed surface **by capability rather than by name**, treat everything
retrieved as attributed and untrusted data, never let instruction-like text in a
retrieved source become authority over the workflow, lower confidence on a single
or stale source, and **degrade visibly when no surface is usable**.

Capability-not-name is what makes it durable. It admits whatever indexer or code
platform is present in an adopter's environment without this brief naming
vendors it cannot verify, and it degrades to file reading as the floor rather
than as the plan.

So the survey delegates its source selection to that contract instead of
restating it — which is this brief applying its own rule to itself, to the same
file whose delegation form started this. What the survey adds on top is only what
that contract does not cover: what to inventory, how to organise it by owner, and
what to report per component.

**What is unknown.** Whether a forwards-looking ownership search is reliable
enough to trust, and what it costs per spec. Both are answerable with a cheap
trial: run it against contracts already authored, and score whether it surfaces
owners a human agrees were missed. The abandoned contract is a ready-made case
with a known answer.

**A measurement harness already exists, and it does not cover this.** The
`pack-activation-evals` spec is Shipped: `agentbundle pack evals run` computes a
Tier-A `trigger_rate` per skill from authored `eval_queries.json`, graded against
a threshold, with a weekly report-only workflow. So "measure activation" is not a
thing to invent here.

What it measures is whether a **skill fires for a query**. It says nothing about
whether an author who had a rule in context then followed it — which is the
activation question this brief is about. The two are different subjects, and the
existing Tier A does not reach the second.

That makes the first slice a scoping question with three candidate answers, and
it should be settled by observation rather than argued:

- Tier A extends to authored artifacts, and the rule becomes an eval query.
- A new eval class is needed, in which case the existing harness supplies the
  runner, the workspace layout, and the report-only posture rather than being
  rebuilt.
- The property is not eval-shaped at all, and the binding has to be a parity
  check or a mutation proof — which is what actually worked in the evidence
  above.

**Prefer generated evals over scavenged history.** Scoring artifacts already in
the repository is available and cheap, but the review artifacts that would show
*how* a loop went are gitignored and machine-local — they sit in peer worktrees
and can be cleaned up. A generated eval is reproducible where a scavenged corpus
is one-shot, so where a question can be put to a generated eval, it should be.

## The LLD's position: no new stage, move the probe instead

Raised as a question and answered here rather than left open, because the answer
is "change almost nothing" and an open question would invite a new stage.

**Where it sits today.** The LLD lives in `plan.md` under `## Design (LLD)`,
scaffolded by the spec's `Shape:` field. The plan is authored after the spec's
criteria and locked after the spec's human gate. So criteria are committed before
the design that has to satisfy them exists.

**Too late for one thing only: satisfiability.** The abandoned contract is the
evidence twice over. Its read-surface criterion was unsatisfiable by any design,
because a Python process opens the standard library — five minutes of "what does
the read path actually do" would have killed it before it was written. And its
observability premise was a design question ("where does this count come from")
that was never asked, because criteria came first.

**But moving the LLD earlier would be wrong.** The plan is deliberately the
document allowed to change while the spec is the contract; hoisting design into
the spec inverts that and commits the design before the contract. The problem is
not that the LLD is late. It is that *nothing* tests satisfiability early.

**Recommendation: extend an existing step rather than add a stage.** `new-spec`
already has step 5a — take the cheapest disconfirming evidence before review: one
fixture, one measurement, or one read-only probe against the plan's load-bearing
mechanism, uncommitted. That is exactly the right instrument, aimed one stage too
late and at the wrong subject. Widen it so a criterion making a claim about live
behaviour gets its cheapest disconfirming probe **before the spec gate**, not
after, and against the criterion's satisfiability rather than the plan's
mechanism.

That is a scope change to a rule that exists, needs no new artifact, and is the
same discipline the sibling brief already states for itself — name the oracle and
take the observation before writing the criterion. It also composes with the
pressure test and the survey: all three are answers to "what must be true before
criteria are written."

**No LLD change is recommended**, and this brief should carry the question as
answered rather than as an investigation. If the activation measurement finds
that step 5a itself does not fire, that is a finding about 5a and not a reason to
reopen where the LLD lives.

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
