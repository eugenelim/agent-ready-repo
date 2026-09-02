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

The load-bearing finding, and it should shape every deliverable.

Across the eleven review rounds that produced this evidence, every mechanism that
caught a defect **on its first run** bound the document to something outside
itself: criterion-identifier parity between spec and plan, assumption-citation
parity in both directions, claims bound to a live symbol table, and mutation
proofs. The rules that lived only as prose — the cognitive-load simplification,
the cut-before-adding razor, the observable-outcome rule — were loaded in context
throughout and fired never.

So a rule's value here is not how well it is written. It is whether it binds to
code, to a sibling document, or to a mutation.

## Why rules here do not activate

Four instances, all from work in this repository.

- **Cognitive-load and cut-before-adding** were routed from the root context the
  whole time. The artifacts authored under them were long and dense with precise
  claims — the opposite of what they ask.
- **The observable-outcome rule** says a criterion naming a helper or a call
  sequence belongs in the plan. It was read, cited to reviewers as governing
  authority, and broken repeatedly.
- **The razor is the costliest.** Its second rung is one bounded search for an
  adequate repository solution, reusing a hit. The search *ran*: `work-loop`'s
  three-line delegation to the `project-knowledge` producer profile came back in
  the opening grep, and the architect pack's `knowledge-surfaces.md` was read in
  full, both inside ten minutes. Neither was recognised as the precedent for the
  contract being designed, and several rounds went into an inline-restatement
  design this repository had already rejected. **The failure is at recognition,
  not retrieval** — which is why "search first" cannot fix it.
- **Repository anchoring fails twice over.** Its tests assert that sentences
  exist in the skill files; nothing reads an authored plan to see whether it has
  anchors, whether they resolve, or whether they were used. And it was complied
  with anyway — the abandoned plan carried four anchors, all imitation, because
  the field asks what to copy rather than whether an owner exists.

That last one is the strongest argument here: **a rule can be shipped, tested,
and complied with, and still not do its job.**

Enforcement exists for some of these and is scoped elsewhere: the cognitive-load
gates read the packs, root guidance, seeds, and changelog, and the
progressive-disclosure lint has a case asserting an authored spec is *not* in its
results. Authored artifacts sit outside the enforcement boundary by design.

**So every rule this work ships carries three things:** an activation point (the
moment something changes if it is ignored, not the file it is written in), a
measurement (how to tell activation from presence, on artifacts the author
wrote), and a stated failure mode when it does not activate — because a rule that
silently does nothing is worse than an absent one.

## Where this is leaning: an explorer, not a designer

**Not an owner decision.** This is the lean and the facts it rests on; the
Ready review decides. Recorded this way so a reviewer can disagree with the
conclusion without re-deriving the evidence.

**A dedicated worker guarantees the rule activates, and that is the case for
one.** A rule in a template may or may not fire. A step a worker performs either
ran or did not — observably, and not by self-report. **The invocation is the
activation.** Any rule restatable as a delegated step becomes
activation-guaranteed; rules that can only be prose are the hard case.

**Scope: an ownership survey before criteria are written.** It returns a
*landscape* — what exists in the area, what each component owns, which are
reusable — not a verdict. Judging "is this an owner for the contract I am about
to write" needs the contract, which the worker does not have; forced to judge it
would return confident wrong answers. Recognition stays with the author, and
becomes cheap because the inventory is organised for that question.

**Why not the host's built-in explorer.** Only Claude Code's `Explore` was
inspectable; no claim is made about Codex, Cursor, Copilot, or Gemini. So the
case rests on ownership, not capability — which probably favours the built-in,
and that is fine, because searching was never the failure. A host built-in is not
ours to shape: its output form, its authority inputs, its versioning, its
shipping with the pack, and decisively **its instrumentation**. This brief's
premise is that we cannot tell activation from presence; delegating a rule to a
component whose firing we cannot measure reintroduces exactly that blindness one
layer down. Reuse a host's isolation where it is offered; the survey
instructions, return shape, authority binding, and eval surface stay ours.

**Its sources are role-scoped, and delegated.** An ownership survey and a spec
author ask different questions: the survey wants a code index or codebase model,
then manifests, agent and skill definitions, ownership-declaring references, with
reading the tree as the explicit expensive floor; a spec author wants decision
records, conventions, prior specs, distilled topics, with asking the owner as the
floor. The *contract* for using any such surface already exists in
`knowledge-surfaces.md` — detect by **capability rather than name**, treat
retrieved context as attributed and untrusted, degrade visibly when none is
usable. Capability-not-name admits whatever indexer an adopter has without naming
vendors. The survey cites that contract rather than restating it. The architect
pack is also the warning: it ships three role-scoped copies and two duplicate
their common half.

**Leaning against a designer agent.** The work splits three ways and only one
part is unowned.

| The job | Owner | Verdict |
| --- | --- | --- |
| Produce the design | `plan.md`'s `## Design (LLD)` | Exists; moving it earlier inverts the contract/strategy split |
| Critique a design artifact | `design-reviewer`, in the **architect** pack, which core does not depend on | Exists elsewhere. Core's answer is conditional routing with a named skip, as `new-spec` already does for `design-review` |
| Test whether a draft criterion is satisfiable by any design | **Nobody** | The real gap — and it is a probe, not a designer |

A named skip is acceptable for an optional enhancement and a hole for a
load-bearing check. Design critique at spec stage is currently optional, so on
this reading core needs nothing new; if this work later makes it load-bearing
before the spec gate, that changes.

**A consequence worth weighing: prose moves out of the always-loaded surface.**
If the explorer owns the ownership survey, then some of the repository-anchoring
prose currently carried in `work-loop` and `new-spec` no longer needs to be
carried there — the instruction becomes "the survey ran, here is its landscape"
rather than a restatement of how to search, what counts as an anchor, and what to
do on absence. That is the delegation form applied to the anchoring rule itself,
and it reduces an always-loaded surface rather than adding to one. It also means
the explorer is not purely additive: it has a prose budget on the other side of
the ledger, which the Ready review should net out rather than treating the worker
as pure cost.

**Sequence forbids merging the survey and the probe.** The survey must run
*before* criteria exist, because its output shapes which criteria to write. The
probe must run *after* a draft criterion exists, because it needs something to
test. Two moments, so not one worker.

### Pressure test

- **The survey is unnecessary if** the activation measurement shows authors
  already recognise precedents reliably — the known misses being unlucky rather
  than typical. Or if a knowledge surface returns ownership directly, leaving
  nothing to organise.
- **The satisfiability probe is unnecessary if** widening the existing
  disconfirming-evidence step actually fires. That is an activation question and
  the same measurement answers it.
- **A designer agent becomes necessary only if** one of the two existing owners
  turns out not to cover its half — which would be a finding about that owner,
  not grounds for a third agent beside it.
- **The honest cost:** three interventions around one authoring act is real
  ceremony and the per-spec cost is unmeasured. If written steps do fire, most of
  this collapses into widening rules that already exist. The brief should want
  that answer.

## The rubric is a deliverable, not content here

The failure-point rubric is distilled from this repository's memory and its
`docs/knowledge/` topics, and it is what the work produces rather than what the
brief carries. Its categories, in the order they matter:

1. **The design should have delegated** — an obligation restated per consumer,
   where an owner already exists. Precedes every other shape, because no
   criterion craft rescues it. Its counter-intuitive repair: shortening or
   single-homing a long restatement is the *wrong* fix.
2. **The criterion cannot fail** — absence claims without a positive control,
   negative paths passing on an unstubbed collaborator, bounds asserted over a
   domain that cannot vary them, instruments blind to their own layer.
3. **The criterion is unsatisfiable or contradicts a sibling.**
4. **The criterion decays** — exact counts over a growing corpus, line citations
   in portable artifacts, figures derived from other figures.
5. **The criterion is too big** — past roughly 150 words it holds several
   contracts, and a fix in one clause silently contradicts another.
6. **The property is not mechanizable** — a gate over a judgment, or an artifact
   measuring itself.

**For plan tasks:** name what to verify, not how. A bullet spelling out the
assertion, the fixture, and the expected message is pseudo-code — reviewed as
code while unable to run, and every detail in it is a claim the next round can
falsify.

## The pressure test at spec creation

Nothing today tests whether a spec should exist. `new-spec` elicits well — it
surfaces an Unverified list and waits — but that defends the spec's *content*.
Its triggers are a disjunction in which "the user explicitly requests a spec" is
sufficient; `Brief:` is stamped only when arriving from a confirmed slice, nothing
checks it resolves, and `none` is accepted almost everywhere. The one detector
that would notice, `unregistered_work`, fires at **dispatch**.

The abandoned spec is the demonstration: authored with no brief and no workspace
entry, nothing objected for its whole life, and registering it mid-flight
*satisfied* the only detector that would have flagged it.

So a test at the trigger, before any body is written: is there a defined outcome
or is this still shaping; what upstream does it descend from and is that upstream
Ready; are load-bearing unknowns still open; and if there is no upstream, is
direct authoring justified against the durability triggers and recorded rather
than assumed. **On a gap, redirect to `author-delivery-brief create`** rather than
refuse — an agent told no finds another route, and that skill already refuses to
invent missing content.

Open by design: whether the test can be mechanical at all, and where it fires so
it cannot be discharged the way the registration check was.

## The LLD: no change

The LLD lives in `plan.md`, authored after the spec's criteria and locked after
the spec's gate — so criteria are committed before the design that must satisfy
them exists. That is late for exactly one thing: **satisfiability**. The
abandoned contract had a criterion no design could satisfy, and an observability
premise that was a design question never asked.

But hoisting the LLD earlier inverts the contract/strategy split, and the plan is
deliberately the document allowed to change. The problem is not that the LLD is
late; it is that nothing tests satisfiability early.

**Recommendation: widen `new-spec`'s existing step 5a** — cheapest disconfirming
evidence, one fixture or measurement or read-only probe, uncommitted — so a
criterion making a claim about live behaviour gets its probe **before the spec
gate**, against the criterion's satisfiability rather than the plan's mechanism.
A scope change to a rule that exists, no new artifact, and it composes with the
pressure test and the survey as three answers to "what must be true before
criteria are written." No LLD change is recommended; this is answered, not open.

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