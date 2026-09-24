# Terminating a review loop that will not converge

> Discipline: applied (practitioner-pattern survey)

- **Question:** why do agentic review/repair loops fail to converge, and what
  stops one?
- **Round 1 — commissioned 2026-09-10.** Literature and practitioner survey.
  Occasion: a shaping-review loop on one specification ran 15 rounds and produced
  30 sustained findings; 60% fell in two families and each of the last eight
  rounds returned exactly one finding.
- **Round 2 — measured 2026-09-23/24.** Measurement over this repository's own
  corpus: ~4,300 session transcripts, 1,273 merged PRs, 431 spec/plan pairs,
  4,060 acceptance criteria, and five multi-round deliveries classified
  repair-by-repair. Round 2 tested eleven candidate mechanisms and shipped none;
  what it establishes is below.
- **Consumers:** `docs/architecture/loop-infrastructure.md` links here for the
  measured behaviour of the review loop.

## Findings

Each finding names the round that produced it. `R1` is survey evidence; `R2` is
measurement over this repository.

### The loop

- **F1 · No spec-driven framework ships a termination rule.** Four surveyed, none
  with an iteration cap, escalation route, or deferral-with-record. `[high]` `R1`
- **F2 · Every production harness bounds the loop, none on convergence.** They cap
  turns, cost or reflections, deliberately external to the quality signal.
  `[high]` `R1`
- **F3 · Self-correction has a stability threshold, not a plateau.** Past it,
  iteration subtracts rather than levels off. `[moderate]` `R1`
- **F4 · Naive repetition detection does not work.** Structural call-stack
  analysis alone scores **F1 = 0.08**; content similarity is what carries signal.
  `[moderate]` `R1`
- **F5 · No mature review process requires zero findings.** Google, Azure DevOps,
  Chromium and NASA SWE-088 all permit approval with outstanding non-blocking
  findings. `[high]` `R1`
- **F6 · Defect classification is never used to stop a review.** Four independent
  searches failed to find prior art. `[high]` for the absence. `R1`
- **F7 · Repair-origin findings dominate a diverging loop.** 9 of 30 (30%) in the
  R1 loop; 30 of 45 (67%) in one R2 delivery. Independently corroborated as
  "whack-a-mole" / output coupling, in a 1,801-round production pipeline, and in
  EvoCode-Bench. `[moderate]` `R1+R2`

### What this repository measures

- **F8 · The shipped spec/plan review cap cannot fire.** `("spec-plan",
  "findings-remain")` is guarded against `review_retry_count`, which only
  `review record --fingerprint` increments — a verb ordinary pre-EXECUTE rounds
  never call. Reproduced: twelve consecutive transitions in `mode=code`, counter
  at `0`. `[high]` `R2`
- **F9 · Repair *class* predicts nothing; replication depth does.** Pooled over
  406 repairs, additive 106/212 vs non-additive 96/194 — indistinguishable, and
  within-run orderings share no common rank. But surfaces-per-contested-claim
  against that claim's share of findings is monotone across four deliveries:
  5→15%, 7→32%, 11→21%, 11→37%. `[moderate]` `R2`
- **F10 · Goal-based delivery matches spec/plan on repair once size is
  controlled.** Matched on code-file count, repairs per file separate in no
  bucket and the sign flips three times. Full mode buys one class light mode
  cannot produce: 567 findings citing an acceptance criterion while pointing only
  at code. `[moderate]` `R2`
- **F11 · The record is most of the review surface.** 85.6% of non-blank
  `plan.md` lines are narrative no gate, task router or AC reference reads; 51%
  of full-mode findings land only on `spec.md`/`plan.md`, against 6% in light
  mode. One run logged 471 record-only findings against 13 elsewhere. `[high]`
  `R2`
- **F12 · The plan template and the engine contradict each other.** The template
  shipped in 210 plans says the plan "is allowed to change as you learn"; the
  engine hash-pins it and refuses substantive edits after `approve-plan`. Two
  deep runs ended with a parked or wiped engine because mid-run learning needed
  an edit the lock forbids, and the Phase-2 re-plan path that would resolve it
  was never built. `[high]` `R2`

### What does not work

- **F13 · Criterion atomicity is unevidenced.** Montgomery et al. screened 6,905
  papers to 105 primary studies; atomicity and singularity are not among the
  twelve empirically-studied quality attributes. INCOSE asserts the rule and
  cites nothing. `[high]` `R2`
- **F14 · Lexical quantifier detection is low-precision.** Femmer's own tool
  reports "average precision of 59% at an average recall of 82% with high
  variation", and negation is its weakest category. A bare quantifier regex fired
  on 73% of 3,990 local criteria, dominated by `no` in ordinary prose. `[high]`
  `R2`
- **F15 · No AC authoring feature predicts churn.** Over 4,060 numbered criteria:
  naming an executable oracle is null, enumerated-vs-open sets show no separable
  effect, and outcome-vs-method is unmeasurable because 99.8% are already
  outcome-shaped. Word count is the only signal and it inverts per-word (3.32
  findings per 100 words at >120 words, 14.92 at <30). `[moderate]` `R2`
- **F16 · Exact-match survivor detection fails.** Of 308 later sibling fixes
  traceable to an earlier edit, **0 were byte-identical** — 100% were rewordings.
  Flag precision 14.4%. `[high]` `R2`
- **F17 · Adjudication is robust to framing; review is not.** A primed and a
  neutral adjudicator sustained the same 3 of 8 findings. The same manipulation on
  the *reviewer* moved severity materially. `[moderate]` for adjudication;
  `[low]` for the reviewer effect, whose variance floor is unmeasured. `R2`

### Method cautions earned the hard way

- A pattern that looks exhaustive usually is not: four parser defects in one
  round, all under-counting. **188 of 431 specs** carry unnumbered checkbox
  criteria that `^- \[[ x]\] \*\*AC` never matches; multi-line continuation
  undercounts AC words by **3.12×**.
- Pin the tree for a *reading* instrument, not just a writing one. A live peer
  session advanced a target worktree six rounds mid-experiment, turning
  "refuted" into "already repaired" in both arms.
- Orchestrator self-reports overclaim in the same direction as the defect they
  describe. One brief asserted three rounds found a class "and nothing else";
  9 of those 19 findings were not that class.

## Round 1 — literature and practitioner survey

*Commissioned 2026-09-10. Question: do agentic spec-driven-development frameworks
solve the review/repair spiral, and should a "reviewer must return clean" gate be
relaxed?*

### Round 1 bottom line

**Nobody has solved this, and a hard clean-verdict gate is contrary to every
mature review practice examined.** The four spec-driven frameworks surveyed
split three ways — one requires a clean verdict and leaves the spiral
unaddressed, one gates on a human, one refuses to block at all, one has no
mechanism — and **not one of the four ships an iteration cap, an escalation
route, or a deferral-with-record for a review loop.** `[high]`

Meanwhile every production *agent harness* bounds its loop, and none bounds it
on convergence: they cap turns, cost, or reflections and then stop. `[high]`

The load-bearing finding for our decision is not a practice but a measurement.
Self-correction has a **stability threshold**, and past it iteration degrades
deterministically rather than plateauing. That reframes the problem: our loop
was not failing to converge, it was operating past the point where another round
is expected to subtract. `[moderate]`

### 1. Spec-driven frameworks: three postures, zero termination rules

| Framework | Clean verdict required? | Iteration cap | Escalation | Defer with record |
| --- | --- | --- | --- | --- |
| GitHub Spec Kit | **Yes** | none | none | **no** |
| AWS Kiro | human approval, or none | none | n/a (human-gated) | no |
| OpenSpec | **no — non-blocking** | none | none | no |
| Microsoft Amplifier | no reviewer gate at all | `max_iterations = -1` | none | no |

**Spec Kit has our design and our problem.** Its documented rule is
*"re-run `/speckit.analyze` until it comes back clean"*, and its post-implementation
loop instructs *"Repeat until it reports converged."* No cap, no escape hatch,
and nothing addressing an analyser that keeps returning findings. `[high]`

Spec Kit carries a **richer finding taxonomy than we do** — `missing`,
`partial`, `contradicts`, `unrequested`, crossed with CRITICAL/HIGH/MEDIUM/LOW —
and still **does not use it to terminate**: every finding, CRITICAL included,
feeds back into the task queue rather than halting to a human. Classification
for routing, never for stopping. `[high]`

One Spec Kit design is worth importing: `/clarify` is **bounded per call** ("up
to five targeted questions") and unbounded in total invocations. It bounds the
round, not the loop. `[high]`

**OpenSpec is the explicit counter-example.** Its validation gate "runs
validation checks without blocking progress", and even CRITICAL is advisory —
"must fix before archive" is a recommendation. Its stated philosophy is
anti-gate: *"there are no phases and nothing is locked — you fix it and move
on."* `[high]`

**Kiro's answer is a human.** Feature Specs place explicit human review and
approval between requirements, design and tasks; Quick Spec "runs all three
phases automatically without approval gates between them." No machine
clean-verdict in either mode. `[moderate]` — vendor-authored docs, and one
promising source on a possible formal gate model was unreachable (see Known
unknowns).

**Amplifier has no reviewer gate to relax.** Its loop module defaults to
`max_iterations = -1` (unlimited) with a 300-second timeout as the only bound;
what loop control exists is at the wrong altitude — network retries, a recursion
depth cap, step-level `on_error`. It never names the
repair-introduces-a-new-defect failure mode anywhere in its documentation.
Calibrate this as weak evidence: Amplifier self-describes as an early-preview
research demonstrator whose "safety systems haven't been implemented yet."
`[moderate]`, downgraded for `stale prior art` inapplicability but flagged for
project immaturity.

### 2. Production harnesses all bound the loop, none on convergence

| Harness | Bound | Default |
| --- | --- | --- |
| SWE-agent | cost per instance | **$3.00**; `max_requeries = 3` for malformed actions |
| OpenHands | hard iteration ceiling | **~100**, then `MaxIterationsReached` and ERROR |
| Aider | reflections per stage | **`max_reflections = 3`** |
| Claude Agent SDK | `max_turns` / `max_budget_usd` | **unlimited**, docs advise setting one; example uses 30 |
| Devin, Cursor | not documented | — |

SWE-agent's rationale is worth noting: it caps **cost rather than steps**
because step counts vary roughly fivefold across model families, making cost the
more stable control variable. `[high]`

Two of these ship documented defects that bear directly on our situation.
OpenHands' system prompt **contains no mention of the iteration budget**, so the
agent cannot plan within it or produce a best-effort partial result before being
cut off — a graceful-termination gap raised as a design issue. And Aider carries
an open bug where the outer loop **did not honour the inner reflection bound**,
consuming tokens indefinitely on a lint error the model could not fix. `[high]`

**The synthesis:** the industry's answer to a non-converging loop is a budget,
not a convergence condition — and the budget is deliberately *external* to the
quality signal. `[synthesis]`

### 3. Self-correction has a stability threshold, not a plateau

This is the finding that reframes the problem.

*Self-Correction as Feedback Control* models self-correction as a two-state
Markov system and derives a stability criterion: iteration pays only while

> ECR / EIR > Acc / (1 − Acc)

— the error-correction rate over the **error-introduction rate** must exceed the
odds of already being correct. Its practical threshold is an EIR **below about
0.5%**. Measured degradation over four iterations: GPT-4o-mini 91.2% → 85.0%
(−6.2pp), GPT-5 96.2% → 94.4%, Claude Sonnet 4 96.8% → 95.6%. Only three tested
models avoided degradation, each with EIR at or near zero. `[moderate]` —
single study, four-iteration window, one task family; the mechanism is
compelling but the threshold should not be treated as portable.

**Why this matters more than a plateau story.** The criterion has `Acc` on the
right-hand side, so **the better the artifact gets, the higher the correction
ratio has to be to keep paying.** A loop does not converge and stop; past the
threshold it actively subtracts. That predicts exactly the shape we observed:
early rounds with many findings and real gains, then a long tail of one finding
per round where repairs generate the next round's work.

Corroborating results, independently sourced:

- Without external feedback, performance **consistently dropped** after
  intrinsic self-correction across GSM8K, CommonSenseQA and HotpotQA on
  GPT-3.5, GPT-4, GPT-4-Turbo and Llama-2. `[high]`
- A critical survey concludes **"no prior work shows successful self-correction
  of responses from LLMs using feedback generated by prompting themselves under
  fair settings in general tasks"** — it works only with decomposable verifiable
  sub-answers, external tools, or fine-tuning. `[high]`
- Iterative self-refinement produces **spontaneous reward hacking**: the
  evaluator's ratings improve while real quality stagnates or drops. Severity
  scales with **context sharing between generator and evaluator** and is
  heightened when both are the same underlying model. `[moderate]`
- Refinement frameworks that work converge in **~3 rounds** and rely on external
  signal: Self-Refine saturates after about three feedback loops; a
  tool-interactive critique framework achieves its gains in three correction
  rounds. `[moderate]`
- Reflexion, the strongest case for long iteration, improves across 12 trials —
  but on an environment with a **reward signal**, and it stops one benchmark
  after **4 trials due to no measurable improvement** and retries another only
  until **3 consecutive failures**. It also shows a measured reversal on one
  benchmark (77.1% against an 80.1% baseline). `[high]`

**One mitigation we already have by accident.** The reward-hacking result keys on
shared model and shared context. Our reviewer is a fresh session on a different
model family with no access to the authoring context, which is the configuration
the paper identifies as least susceptible. That is worth making deliberate rather
than incidental. `[inference]`

**One practice we have been getting wrong.** A cross-model study reports that
**"providing error location hints hurts all models"**, and that stronger models
make fewer but deeper errors which resist correction. Every round of our loop
hands the repairer an exact file and line. `[low]` — single study, small n, and
the mechanism is not established; recorded because it is directly actionable and
cheap to test, not because it is settled.

### 4. Oscillation is detectable, and the naive detector does not work

Two primary results:

- Hybrid structural-plus-semantic cycle detection reaches **F1 = 0.72**
  (precision 0.62, recall 0.86) over 1,575 agent trajectories. The components
  alone are near-useless: **structural call-stack analysis alone scores F1 =
  0.08**, semantic similarity alone 0.28. `[moderate]`
- A study of 6,549 agent repositories confirmed **68 infinite-loop failures
  across 47 projects**, attributing them to agent logic design, framework
  feedback semantics, and missing termination mechanisms. `[moderate]`

The practical lesson is the F1 = 0.08: **detecting a spiral by repeated
structure — "we have been here before" — does not work.** What works is
structure plus semantic similarity of the *content*. A stop rule keyed on
finding *family* rather than finding *location* is the cheap analogue of that
hybrid. `[inference]`

### 5. Mature review practice: no process requires zero findings

Every named process examined permits approval with outstanding non-blocking
findings. This is the clearest and best-triangulated result in the survey.
`[high]`

- **Google's** standard: *"reviewers should favor approving a CL once it is in a
  state where it definitely improves the overall code health of the system being
  worked on, even if the CL isn't perfect"*, adding *"there is no such thing as
  'perfect' code — there is only better code."* It explicitly cautions against
  letting a change sit because author and reviewer cannot agree.
- **Microsoft Azure DevOps** makes non-blocking approval a first-class vote
  state: *Approve with suggestions* satisfies required-reviewer policy and does
  not block merge. Comments can be closed or marked "Won't fix" unacted.
- **Chromium** merges on obtaining the required +1 votes, not on resolving every
  comment thread.
- **NASA SWE-088**, a normative standard, sets inspection exit at **major**
  defects addressed, with *"the project manager defines the criteria to be used
  to determine if an inspection ends"* — criteria fixed in advance, never a
  finding count. Minor findings become tracked action items.

**Our pattern has a name.** Simon Tatham's practitioner catalogue calls it
**"Death of a Thousand Round Trips"**: the reviewer stops reading after each
finding, so each round surfaces one new issue and iterations are unbounded. His
remedy is the inverse of iterating harder — *"Try to minimise round trips,
rather than maximising them. Ask for important rewrites (if needed) before
picking all the trivial nits."* Adjacent anti-patterns he names: **Priority
Inversion** (cosmetic demands first, fundamental rewrites later, invalidating
the earlier work) and **Double Team**. `[high]` for the catalogue's existence
and content; `[moderate]` that our case is an instance, since that is our own
classification of our own loop.

**Yield curves support stopping.** Fagan-tradition inspection is logarithmic:
one team found 35% of defects in a requirements document where nine teams found
78%. Sauer et al. put the optimum at two reviewers, past which marginal cost
exceeds marginal detection. `[moderate]` — the parallel-reviewer curve is
measured; extending it to sequential rounds is an inference.

**Blocking versus non-blocking is a solved authoring problem.** The `Nit:`
convention and the Conventional Comments taxonomy (`issue`, `issue
(non-blocking)`, `nitpick`, `suggestion`, `question`, `thought`, `praise`) exist
precisely so a reviewer's intent is explicit. The failure mode they address is
ours: **an unqualified finding is ambiguous, so a conscientious author treats
every finding as blocking.** `[high]`

#### Defect classification is never used to stop a review

Worth stating because it is the obvious place to look for prior art and it is
empty. Orthogonal Defect Classification exists and its stated purpose includes
using the defect-trigger distribution to *"evaluate the effectiveness and
eventually the completeness of verification processes"* — which sounds exactly
like a termination signal. But **no primary source found uses ODC, or any defect
classification scheme, as a criterion for terminating an individual review.** It
is applied to release readiness in industrial and aerospace quality processes,
not to deciding that a document has been reviewed enough. `[moderate]` for
ODC's purpose; `[high]` for the absence, which four independent searches failed
to fill.

The nearest prior art is weaker and older than a classification rule: NASA's
"major defects addressed" exit condition, and the Fagan tradition of exit
criteria fixed in advance by the project manager. Both are severity gates, not
family gates.

**Consequence for us:** a family-recurrence stop rule is an **extension we
would own**, not an import. The measured cycle-detection result supports the
*shape* — content similarity beats structural repetition — but nobody has
applied it to review findings. That is a reason to ship it as advisory and
calibrate it, not a reason to avoid it. `[inference]`

### 6. What this implies for a clean-verdict gate

Stated as options rather than a single answer, because the choice is an owner's.

1. **Keep the gate, add a bound.** Every harness surveyed does this, and none
   bounds on convergence. The bound must be external to the quality signal —
   rounds, cost, or wall-clock — and the artifact must be **accepted with a
   recorded residue** when the bound fires, which is Google's and NASA's
   posture.
2. **Split the verdict.** Adopt a blocking/non-blocking distinction so a
   reviewer can return "clean of blocking findings, N advisory". This is the
   single highest-value import: it is standard practice, it is cheap, and it
   directly dissolves the ambiguity that makes an author treat a nit as a gate.
3. **Key the stop rule on family recurrence, not round count.** Two consecutive
   rounds whose sustained findings share a family means the loop is sampling one
   generator. Round count is a poor trigger — it fires late and says nothing
   about why. The F1 = 0.08 result is the supporting evidence: structural
   repetition alone is a bad detector; content similarity is what carries signal.
4. **Track repair-origin rate as the health metric.** The stability criterion
   makes the error-introduction rate the quantity that decides whether another
   round pays. It is already recordable — the review protocol marks each finding
   `draft-origin` or `prior-round-repair`. When repair-origin findings dominate a
   round, the loop is past its threshold.

   **Our own occasioning loop, measured rather than recalled:** of 30 sustained
   findings, **9 (30%) were introduced by a previous round's repair.** That is
   internal session data, not survey evidence, and the comparison to the
   published sub-1% threshold is not like-for-like — that threshold is measured
   on reasoning accuracy, not on document findings. What survives the mismatch is
   the ordering: a 30% repair-origin rate is nowhere near a regime where more
   iteration is expected to pay.

**None of the four is invented here.** 1 and 2 are established practice, 3 is an
analogue of a measured detection result, and 4 is instrumentation for a published
criterion. `[synthesis]`

## Round 2 — measurement over this repository

*Measured 2026-09-23/24. Question: which of Round 1's candidate mechanisms
survives contact with this repository's own corpus?*

**Eleven candidate mechanisms were tested and none shipped.** That is the round's
primary result: each one needed a semantic judgement it could not make, or failed
its own precision bar. The measurements that survive are diagnostic, not
mechanical.

### Corpus

~4,300 session transcripts; 1,273 merged PRs; 431 `spec.md`/`plan.md` pairs;
4,060 numbered acceptance criteria across 254 specs; 20,637 criterion references;
five multi-round deliveries classified repair-by-repair (406 repairs); four
pre-implementation specs reviewed fresh to generate a spec-stage finding corpus
(93 findings); and one commit reviewed under three briefs.

### What the review loop actually does here

Review rounds reach a maximum ordinal of 63 on one run, but a high ordinal is
**not** one loop iterating — the ordinal is monotone per `run-id` across many
review loops. Of 112 runs carrying review artifacts, 50 exceed five rounds. The
shipped cap never fires (F8): 3 genuine firings across the whole corpus, and the
one override observed was self-granted by an agent, passed to one half of the
pair only.

None of the five deliveries examined converged under repair alone. One reached
clean only after a **scope cut** removed the contested analysis.

### The repair classification that failed

Repairs were classified `ADD-CONTROL` / `ADD-CLAIM (outcome|status)` / `REPLACE`
/ `DELETE` / `NARROW` and joined to next-round findings. A single-delivery pilot
(n=44) suggested `DELETE` was worst at 6/7 and `ADD-CONTROL` cheap at 2/7;
pooled over three further deliveries those become 6/14 and 63/119. **Treat the
pilot table as noise.** Three hypotheses died here: "non-additive repair", "ban
added claims", and "added claims carry a delayed sweep cost" (9 of 13
missed-surface findings were on claims original to the delivery).

What replaced them is F9: replication depth of a *contested* claim. An ADR
ordinal renumbered across 17 surfaces produced **zero** findings, because the
churn was merge-driven rather than contested.

### The mechanisms that failed their precision bar

- **Citation-resolution classifier** — intended to detect rounds arguing about
  unbuilt code. Over 93 spec-stage findings on four pre-implementation specs,
  **100% of citations resolved and 0% classified unbuilt**, even though every
  reviewer was explicitly licensed to cite files that do not exist. Spec-stage
  review argues about the contract (91%) and the existing system, never about
  unwritten code.
- **Removed-line survivor detection** — F16. 10.0% fire rate after path
  suppressions, 14.4% flag precision, and 0.4% when restricted to the same spec
  directory. Its true positives were mostly spec prose duplicated into `packs/`,
  which is the self-hosting projection and is supposed to lag.
- **Criterion-token staleness** — the resolver is sound (20,636 of 20,637
  expressions resolve; naive `\bAC<N>\b` misses **16.19%** of mentions), but a
  check built on it fires on 17% of commits, median 8 flags, max 246. Keep the
  resolver as an advisory library; do not gate on it. Two range dash variants
  exist, not three — an em-dash in range position appeared once and was prose.
- **Trajectory hashing** — not tested, because Round 1 § 4 already measured the
  answer (F1 = 0.08 for structural repetition) and `ADR-0104` had already retired
  this repository's stasis stop as unreachable.

### Reviewer and adjudicator behaviour

The largest single-manipulation effects measured sit in the instrument, not the
artifact. On one pinned commit, a 486-word steered brief naming the class to hunt
returned 11 findings with 7 Blockers; a 165-word neutral brief returned 7 with 2.
Volume moves little; **severity moves a lot**, and only a Blocker forces another
round through `DECIDE`. Against that, adjudication did not move: a primed and a
neutral adjudicator sustained the same 3 of 8 findings (F17).

Earlier unpinned arms are excluded from that comparison — a live peer session
advanced the target worktree six rounds mid-experiment.

### Criterion shape — the literature behind F13-F15

Merged from a separate criterion-shape survey run in this round. Confidence tags
are that survey's own; `R2-lit` marks findings from published sources rather than
from this repository's corpus.

### F1. "Keep criteria atomic and small" is expert consensus, not an empirical result. `[high]`

Montgomery et al. (2022) screened 6,905 papers to 105 primary studies and
identified twelve empirically-studied requirements-quality attributes: ambiguity,
completeness, consistency, correctness, complexity, redundancy, relevancy,
reusability, traceability, understandability, verifiability, and undefined.
**Atomicity and singularity are not among them.**

INCOSE's *Guide for Writing Requirements* asserts singularity improves
verifiability and cites no controlled study. The QUS framework's "atomic" and
"minimal" criteria were validated against 1,023 user stories from 18 companies —
but that validation measured **detection accuracy**, not downstream effect. No
study in this line connects an atomicity violation to measured rework, review
effort, or defects.

Triangulated: Montgomery 2022 (mapping study), INCOSE GtWR (normative text,
self-evidently uncited), Lucassen et al. 2016 (validation scope).

### F2. Lexical detection of quantifier and negation words is known to be low-precision. `[high]`

Femmer et al.'s Smella tool reports, in the authors' own words verified from the
primary full text: *"The automatic detection yields an average precision of 59% at
an average recall of 82% with high variation."* The same paper notes prior work at
34–75% precision, and that Krisch and Houdek report lower precision still in an
industrial setting.

Critically, Femmer's "true positive" means **a human reviewer agreed the flagged
sentence was a defect** — not that the flag predicted any downstream outcome.

Veizaga et al. (2024) reach high-80s precision on 2,725 annotated requirements,
but only by combining NLP, glossary, and syntactic techniques; the paper's framing
is that no single lexical-only technique suffices.

**This is the wall our own detector hit.** A bare quantifier regex fired on 73% of
3,990 criteria, dominated by `no` at 1,986 hits — mostly ordinary prose, not
universal quantification. The literature's response to this problem has never been
to accept the raw hit rate; it is to narrow the trigger to syntactic context, or
to require human triage after detection.

Triangulated: Femmer 2017 (verified primary), Veizaga 2024, Berry & Kamsties 2005.

### F3. The named remedy is to bound the set, not to detect the word. `[moderate]`

Berry & Kamsties (2005) address our exact failure mode. "All" plus a plural noun is
ambiguous between a **distributive** reading (the property holds of each member)
and a **collective** reading (it holds of the group as an aggregate); their example,
*"all software modules must be tested"*, licenses different acceptance tests under
each. The danger compounds when the quantified set is never enumerated, because
then neither reading can be checked.

Their prescription is explicitly **not** lexical detection. It is to force the
author to enumerate or bound the domain, or to restate the claim as an explicit
conditional over a named, bounded set.

Downgraded from `high`: one primary source carries the prescription, though it is
consistent with Veizaga's multi-technique direction and Berry & Kamsties (2004) on
ambiguity requiring domain knowledge rather than surface analysis.

### F4. Negated quantification specifically costs comprehension. `[moderate]`

Winter, Femmer & Vogelsang (2020) ran a controlled experiment with 51 participants
across 9 quantifiers, comparing affirmative against logically equivalent negative
phrasings ("at least N" vs "not less than N"). For 5 of 9 quantifiers the
affirmative form produced fewer reading errors and less effort; only 1 of 9 favoured
the negative form.

This is about phrasing, not about detector base rates. Downgraded from `high`:
single study, and it does not address whether the quantified set is bounded.

### F5. Requirement smells measurably degrade LLM-generated code. `[moderate]` — model-dated

Villamizar et al. took clean requirements with system tests for four applications,
**progressively injected smells**, and measured test-suite functional correctness of
LLM-generated code. Increasing smell density was associated with lower correctness,
with effects varying by smell category, model, and application. Korn (RE 2025
Doctoral Symposium, IEEE) reports that increasing smell count significantly degrades
LLM performance on traceability tasks.

Downgraded from `high`: the two sources belong to the same research programme, so
they are not fully independent, and Korn is framed as initial results.

### F6. Longer input degrades model reasoning independent of content. `[moderate]` — staleness-downgraded

Levy, Jacoby & Goldberg (ACL 2024) hold task difficulty constant and pad input
length alone: reasoning performance degrades measurably. Liu et al. (TACL 2024)
show a U-shaped position curve — performance drops by **over 30%** when the needed
information sits mid-context — replicated across GPT-3.5-Turbo, GPT-4, Claude 1.3,
LongChat-13B, MPT-30B, and Cohere Command.

This is the strongest mechanism by which a 596-word acceptance criterion could
actually hurt an agent: a load-bearing clause buried in the middle is the exact
shape these papers show being lost.

**Transfer caveat.** Neither paper studies acceptance criteria or coding agents.
Applying them to a long AC is an inference, not a measurement.

**Staleness caveat — this is why the rating is not `high`.** Liu et al. tested
GPT-3.5-Turbo, GPT-4, **Claude 1.3**, LongChat-13B, MPT-30B and Cohere Command.
Not one is a current production model, and long-context handling is precisely the
axis on which models have advanced most since. A 2024 result about mid-context
degradation may substantially overstate the effect for current models, or may not
transfer at all.

A targeted arXiv search for replications on current-generation models
(`cs.CL`, 2025-09 onward, position-bias and long-context-degradation queries)
**returned no matching work**. The retriever was verified healthy, so this is
absence of retrieved evidence, not retrieval failure — and absence of a
replication is not evidence the effect has gone. It is an open question (see
Known unknowns).

Triangulated for the original claim: Levy 2024, Liu 2024, corroborated by
Mehtiyev & Assunção 2026 — all on superseded model generations.

### F7. Instruction elaboration helps weak models and not strong ones. `[low]` — model-dated

Mehtiyev & Assunção analysed 9,374 trajectories across 19 agents on 500 SWE-bench
Verified tasks. Comparing a terse 350-character prompt against a structured
5,602-character 8-phase prompt **on the same model**: near-identical behavioural
metrics, a 4-point resolution difference, and *more* steps for the longer prompt
(60 vs 56). On a weaker model the richer prompt gained 19.4 points.

They also found patch complexity does not explain difficulty — 12 "simple" tasks
(≤10 lines, single file) were unsolved by all 19 agents because of an architectural
reasoning gap.

Downgraded to `low`: unreviewed 2026 preprint, and the prompt comparison is a
natural experiment rather than a controlled granularity ablation. Large N.

If it holds, the moderator is **model capability**, not criterion size — which means
a fixed size threshold is the wrong instrument shape regardless of its value.

### F8. Vendor claims that structured specs improve agent success are unmeasured. `[high]`

GitHub's Spec Kit announcement asserts that clear up-front specification "gives the
coding agent more clarity, improving its overall efficacy" and cites no benchmark,
dataset, or effect size. A widely-recirculated "3–10× first-pass success rate"
figure could not be traced to any primary methodologically-described source. An
independent production review states plainly that no independent benchmark
establishes a defect-reduction figure for Spec Kit, and that it has had no
independent academic evaluation.

Kiro and Tessl make parallel structural claims with no measurement. Tessl's claim
runs the *opposite* way to the size intuition: more spec detail enables **bigger**
unsupervised scope, not smaller.

Independence: GitHub, Amazon and Tessl each count as one vendor source. The
independent confirmations are the Wavect review and Fowler's commentary.

### F9. Repairs adding text create the next round's findings — the additive-repair loop. `[low]`

One independent practitioner logged a plan-review loop at
`37 → 39 → 35 → 54 → 52 → 46 → 45 → 45` findings across cycles with **no repeated
defects** and no convergence. Diagnosed mechanism: the fixer *adds* normative text
to satisfy the reviewer, and that new text becomes fresh surface for the next
reviewer — a positive feedback loop. Proposed remedy: **non-additive repair**, where
a review cycle may only replace or delete text, never add a new normative claim.

This matches our own corpus closely. Ours: `21 → 14 → 12 → 9 → 10`, flat, with 30 of
45 findings originating in prior repairs, and one criterion restated across 15
surfaces so that repairing one leaves fourteen able to contradict it.

`[low]`: a single author on a niche tool, not peer-reviewed or replicated. Two
independent observations of the same mechanism is suggestive, not established.

> **Tested and refuted after this survey was written.** Classifying all 42 repair
> units in a 7-round local review loop (44 findings) by what each repair did, then
> measuring which caused a next-round finding: additive repairs fired **7/16**
> against **16/26** for non-additive ones — the proposed rule points the wrong way
> and would have raised the count. `DELETE` was the *worst* class at **6/7**,
> because a deletion is only as complete as its sweep. The narration this remedy
> targets was the cheapest class measured (`STATUS-CLAIM` 1/4); adding a new
> required outcome was among the most expensive (`OUTCOME-CLAIM` 4/5).
> What the same corpus does support: **one claim restated across ~11 surfaces
> produced 21% of that loop's findings.** The driver is replication depth, not
> repair direction. Single delivery, small n (p = 0.21 on the outcome/status
> split); replication across further deliveries was in progress when this note
> was written.

Counter-position worth holding: Marmelab's "Waterfall Strikes Back" and the ~200
comment HN thread argue **granularity is the wrong axis entirely** — the problem is
process rigidity reimporting Waterfall, independent of any spec's size.

### F10. No study links smell density to field defects or rework. `[moderate]`

The requirements-quality roadmap literature states that the connection between
smell density and downstream defects or rework remains an open research question,
and criticises existing smell definitions as vague and empirically ungrounded.
Gentili & Falessi (2024), interviewing ten practitioners in a safety-critical
setting, add that whether a flagged instance is a real problem is
**context- and lifecycle-dependent** — the same phrasing can be benign early and
harmful late.

Downgraded: one roadmap source was retrieved through unreliable PDF extraction and
its exact wording is unverified.

---

**Model-generation sensitivity.** The LLM-behaviour findings above rest on
superseded model generations — Liu et al. tested Claude 1.3, GPT-3.5-Turbo,
MPT-30B and LongChat-13B, on the axis where models have improved most. A targeted
search for replications on current frontier models returned nothing, which is
absence of retrieved evidence rather than evidence of absence. The requirements-
engineering findings (F13, F14) concern human comprehension and detector
precision over text and do not decay with model generation; those are the ones
that decide the criterion-shape question.

### Sources for the criterion-shape findings

**Primary, peer-reviewed**
- Montgomery, L. et al. (2022). *Empirical research on requirements quality: a systematic mapping study.* Requirements Engineering 27:183–209.
- Femmer, H., Méndez Fernández, D., Wagner, S., Eder, S. (2017). *Rapid quality assurance with Requirements Smells.* Journal of Systems and Software 123:190–213. Preprint arXiv:1611.08847.
- Berry, D.M., Kamsties, E. (2005). *The Syntactically Dangerous All and Plural in Specifications.* IEEE Software 22(1):55–57.
- Kamsties, E., Berry, D.M., Paech, B. (2001). *Detecting Ambiguities in Requirements Documents Using Inspections.* WISE.
- Winter, K., Femmer, H., Vogelsang, A. (2020). *How Do Quantifiers Affect the Quality of Requirements?* REFSQ. arXiv:2002.02672.
- Veizaga, A., Shin, S.Y., Briand, L.C. (2024). *Automated Smell Detection and Recommendation in Natural Language Requirements.* IEEE TSE. arXiv:2305.07097.
- Lucassen, G., Dalpiaz, F., van der Werf, J.M.E.M., Brinkkemper, S. (2016). *Improving Agile Requirements: The Quality User Story Framework and Tool.* Requirements Engineering 21:383–403.
- Liu, N.F. et al. (2024). *Lost in the Middle: How Language Models Use Long Contexts.* TACL.
- Levy, M., Jacoby, A., Goldberg, Y. (2024). *Same Task, More Tokens: The Impact of Input Length on the Reasoning Performance of LLMs.* ACL.
- Sclar, M. et al. (2024). *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design.* ICLR.
- Fenton, N., Ohlsson, N. (2000). *Quantitative Analysis of Faults and Failures in a Complex Software System.* IEEE TSE 26(8):797–814.
- Fagan, M. (1976). *Design and Code Inspections to Reduce Errors in Program Development.* IBM Systems Journal 15(3):182–211.
- Korn (2025). *Smells Like Trouble: Investigating the Impact of Requirements Quality on LLM-Supported Software Engineering.* RE 2025 Doctoral Symposium, IEEE.
- Gentili, E., Falessi, D. (2024). *Characterizing Requirements Smells.* arXiv:2404.11106, DOI 10.1007/978-3-031-49266-2_27.

**Primary, preprint (unreviewed)**
- Mehtiyev, Assunção (2026). *Beyond Resolution Rates: Behavioral Drivers of Coding Agent Success and Failure.* arXiv:2604.02547.
- Villamizar et al. *On the Impact of Requirement Smells in LLM-Based Code Generation.* Replication package: Zenodo 17441075.
- *Requirements Quality Research: a harmonized Theory, Evaluation, and Roadmap.* arXiv:2309.10355. (Extraction unreliable.)

**Normative, uncited within**
- INCOSE (2023). *Guide for Writing Requirements*, v4 (INCOSE-TP-2010-006-04).
- ISO/IEC/IEEE 29148; IEEE 830-1998.

### Where the prose goes

F11 and F12 are the round's most actionable findings and need no mechanism at
all — 85.6% of plan lines have no mechanical consumer, and the plan's own
template already declares it working material while the engine hash-pins it.

### The severity ceiling: measured, and what it costs

**Retraction.** An earlier pass reported that findings against working-material
fields sustain at Blocker 37% of the time when the artifact declares tiers
against 30% when it does not, and named 356 conformance violations. That
classifier matched the words `Approach`, `Design`, `Grounding` and `Risks`
anywhere in a finding's text, not the tier of the cited surface. An audit found
**54% of its population also named a gate-read field**, and none of six sampled
entries was a finding whose cited surfaces were working material. Those figures
measured word presence. They are withdrawn.

**What replaces them.** Adjudicator finding-entries were re-extracted on output
structure (`**N. [Severity] …`) rather than on prose, which excludes the contract
text being read. Of **23,412 entries across 60 runs**, 2,062 declare a
consequence advisory, and **98% of those sustained at Concern or Nit** — 27 at
Blocker. Per run, **13 of 15** runs with at least 20 advisory entries were
perfectly compliant, 14 of 15 above 90%, and all violations came from 4 of 29
runs. `[moderate]` `R2` — the ceiling is honoured when invoked.

**Recall is not measurable from entry text, and that is the finding.** Fifty
entries sustained at Blocker without declaring advisory were labelled
independently by two raters: one returned 9 of 50 that should have been advisory,
the other 23 of 50. **18% or 46% of Blockers, depending on the rater.** `[low]`
`R2`

The disagreement sits on one axis, and it is a defect in the rule's wording
rather than in either rater. `adversarial-reviewer` defined mechanical as *"one
correct resolution … with no choice left open"* and then justified the ceiling
with *"nothing external decides it and the next round will raise another"*. The
first clause asks how many **repairs** exist; the second asks whether anything
establishes the **defect**. A count that says three where the tree holds five is
determinate as a defect and indeterminate as a remedy, so the two readings
diverge by a factor of two and a half.

This mattered in production because **no runtime is named in the reviewer
contracts**: the same prose is executed by whichever model the session uses, so
the divergence is a live per-runtime variance in how strictly a delivery is
gated, not an artefact of this measurement.

The remedy was two sentences, not a mechanism: say that the repair may take
several defensible forms and that what makes a finding mechanical is that the
*defect* is decided, not the *remedy*.

**Shipped 2026-09-24, in `core` 2.26.40.** Both contracts now tag severity by
whether anything external establishes the defect. `adversarial-reviewer` states
that the repair may take several defensible forms; `finding-adjudicator`'s
fifth predicate states that determinacy of the remedy is not the test. The
vocabulary, the Concern ceiling and who applies the test are unchanged.

**The paired re-label narrowed the spread from six to zero.** Two raters on two
runtimes labelled the same 50 entries under both wordings, paired so the
before-and-after sits on one rater rather than on two unknown ones. Old
wording: 2 and 8. Corrected wording: 1 and 1. Under the old wording, seven of
the eight entries the higher rater returned were reasoned as remedy
indeterminacy — "which AC is correct is undetermined", "unresolvable without a
design decision" — and the lower rater reached that reading once. Under the
corrected wording neither rater gives a remedy-indeterminacy reason; the two
single hits are a framing preference and a `notes/` surface tier, both advisory
under either wording. `[low]` `R2`

This does not replicate the 9-versus-23 measurement: different raters, and
absolute levels of 2 and 8 rather than 9 and 23. What it establishes is that
replacing the clause removes the reading that produced the divergence on this
sample. Read on entries rather than counts, the two raters overlap on one
entry of nine before and on none of two after, so the entry-level symmetric
difference falls from eight to two. Counts converge further than entries do:
the raters agree on how many, not on which.

The inputs and rater output for this run are not retained in the repository.
They were session-local, so the numbers above are the record, and re-deriving
them means running the labelling again rather than re-reading a corpus.

A standing cross-runtime test is still absent. The instrument is described in
[`cross-model-steering-survey.md`](cross-model-steering-survey.md) Mechanism 1,
clause accuracy; what is missing is that `packs/core/.apm/agents/` ships no
`evals/` directory of its own, so the contracts whose prose decides severity
have no repeatable cross-runtime check and the re-label above is a one-off.

## Known unknowns

- **Known-unknown:** does Kiro ship a formal review-gateway model with
  `PASS` / `NEEDS_CHANGES` / `ERROR` verdicts? A source referencing exactly that
  surfaced in search and returned no readable content. Would be closed by
  retrieving that article or an equivalent AWS-authored description.
- **Known-unknown:** how often do the harness caps actually fire, and what
  fraction of instances benefit from iterations beyond N? No surveyed harness
  publishes this. Would be closed by vendor telemetry or an independent
  benchmark sweeping the cap.
- **Known-unknown:** does the error-introduction-rate threshold hold for
  document review rather than reasoning tasks? Would be closed by running the
  same measurement on an artifact-authoring loop.
- **Known-unknown:** is the "error location hints hurt" result real? Would be
  closed by an ablation withholding locations from the repairer on our own
  corpus — cheap, and directly testable here.
- **Unknowable, as posed:** whether our 15-round loop would have reached clean
  at round 20. The counterfactual cannot be run: each repair changed the
  artifact, so the later rounds reviewed a different document than an unrepaired
  one would have.
- **Known-unknown (R2):** the reviewer-variance floor. Two neutral arms on one
  pinned commit are needed to know whether the severity gap exceeds run-to-run
  noise; without it F17's reviewer half stays `[low]`.
- **Known-unknown (R2):** whether the 188 specs carrying unnumbered checkbox
  criteria behave like the numbered ones. Every AC census here used a `**AC`
  pattern and never saw them.
- **Unknowable:** the per-round defect-yield curve for specification review.
  Fagan-tradition data measures parallel reviewers on code and requirements
  documents, not sequential rounds on agent-authored specs; the population does
  not exist because the practice is two years old.

## Citations

**Spec-driven frameworks.** [Spec Kit `converge.md`](https://github.com/github/spec-kit/blob/main/templates/commands/converge.md) · [Spec Kit Agentic SDD reference](https://github.github.com/spec-kit/reference/agentic-sdd.html) · [Kiro Quick Spec](https://kiro.dev/docs/specs/quick-spec/) · [Kiro Feature Specs](https://kiro.dev/docs/specs/feature-specs/) · [OpenSpec reviewing-changes](https://github.com/Fission-AI/OpenSpec/blob/main/docs/reviewing-changes.md) · [OpenSpec issue #381](https://github.com/Fission-AI/OpenSpec/issues/381) · [microsoft/amplifier](https://github.com/microsoft/amplifier) · [amplifier-module-loop-basic](https://github.com/microsoft/amplifier-module-loop-basic) · [amplifier `repo-audit.yaml`](https://raw.githubusercontent.com/microsoft/amplifier/main/recipes/repo-audit.yaml)

**Harnesses.** [SWE-agent config reference](https://swe-agent.com/latest/reference/agent_config/) · [SWE-agent competitive runs](https://swe-agent.com/latest/usage/competitive_runs/) · [OpenHands issue #6857](https://github.com/OpenHands/OpenHands/issues/6857) · [OpenHands graceful-termination #2406](https://github.com/OpenHands/software-agent-sdk/issues/2406) · [Aider lint/test](https://aider.chat/docs/usage/lint-test.html) · [Aider infinite-loop #1090](https://github.com/Aider-AI/aider/issues/1090) · [Claude Agent SDK agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)

**Self-correction.** [Self-Correction as Feedback Control](https://arxiv.org/html/2604.22273v2) · [LLMs Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798) · [When Can LLMs Actually Correct Their Own Mistakes?](https://arxiv.org/html/2406.01297v3) · [Spontaneous Reward Hacking in Iterative Self-Refinement](https://arxiv.org/abs/2407.04549) · [Self-Refine](https://arxiv.org/abs/2303.17651) · [CRITIC](https://arxiv.org/abs/2305.11738) · [Reflexion](https://proceedings.neurips.cc/paper_files/paper/2023/file/1b44b878bb782e6954cd888628510e90-Paper-Conference.pdf) · [Decomposing LLM Self-Correction](https://arxiv.org/abs/2601.00828)

**Oscillation.** [Unsupervised Cycle Detection in Agentic Applications](https://arxiv.org/abs/2511.10650) · [When Agents Do Not Stop](https://arxiv.org/abs/2607.01641)

**Review practice.** [Google — The Standard of Code Review](https://google.github.io/eng-practices/review/reviewer/standard.html) · [Azure DevOps — review pull requests](https://learn.microsoft.com/en-us/azure/devops/repos/git/review-pull-requests?view=azure-devops) · [Chromium code reviews](https://chromium.googlesource.com/chromium/src/+/lkgr/docs/code_reviews.md) · [NASA SWE-088](https://swehb.nasa.gov/spaces/SWEHBVB/pages/32604575/SWE-088+-+Software+Peer+Reviews+and+Inspections+-+Checklist+Criteria+and+Tracking) · [Tatham — Code Review Antipatterns](https://www.chiark.greenend.org.uk/~sgtatham/quasiblog/code-review-antipatterns/) · [Conventional Comments](https://graphite.com/guides/conventional-comments) · [Blocking comments vs nitpicks](https://graphite.com/guides/blocking-comments-vs-nitpicks) · [A Roadmap on Modern Code Review](https://arxiv.org/pdf/2405.18216) · [Fagan inspection case study](https://eprints.bournemouth.ac.uk/18183/3/JearyPhalpMilsomHughesWebsterHolroyd.pdf)
