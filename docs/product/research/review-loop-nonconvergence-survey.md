# Terminating a review loop that will not converge

> Discipline: applied (practitioner-pattern survey)

- **Commissioned:** 2026-09-10
- **Question:** do agentic spec-driven-development frameworks solve the
  review/repair spiral, and should a "reviewer must return clean" gate be
  relaxed?
- **Occasion:** a shaping-review loop on one specification ran 15 rounds and
  produced 30 sustained findings. 60% fell in two families, and each of the last
  eight rounds returned exactly one finding.

## Bottom line

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

## 1. Spec-driven frameworks: three postures, zero termination rules

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

## 2. Production harnesses all bound the loop, none on convergence

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

## 3. Self-correction has a stability threshold, not a plateau

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

## 4. Oscillation is detectable, and the naive detector does not work

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

## 5. Mature review practice: no process requires zero findings

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

### Defect classification is never used to stop a review

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

## 6. What this implies for a clean-verdict gate

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
