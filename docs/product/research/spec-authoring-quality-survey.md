# Spec-authoring quality, and the spec as an agent's control surface

> Discipline: applied (practitioner-pattern survey)

Commissioned 2026-09-04 to place this repository's spec-authoring failure
classes against prior art, and to settle what a spec and plan can actually
control in an agent's loop. Independent desk research; every claim carries a
source and a confidence tag. Retained so briefs and skills can cite it rather
than restate it.

Confidence tags rank how far a claim can be trusted, strongest first:
`[high]`, `[moderate]`, `[low]`. Two further tags mark claims that are not
graded on that scale because no single source states them — `[synthesis]`, a
conclusion drawn across cited material, and `[inference]`, a deduction from it.
Both inherit the weakest confidence of what they rest on, so neither outranks
`[low]` on its own. Applied-mode overlay: peer review is not a downgrade factor
for practitioner sources; survivorship bias and stale prior art are.

---

## Bottom line

Four results change what this repository should write.

1. **Adherence collapses as simultaneous constraints multiply.** Joint
   satisfaction of independent verifiable constraints falls from 77.7% at one to
   two constraints to 33.0% at four to eight — a 44.7-point drop — and a second
   study measures 57.1% at two constraints against 7.5% at eight. This is the
   first evidence of the right *shape* for an acceptance-criteria ceiling. It
   does not measure an implementation loop, so it supports a screening threshold
   rather than a gate. `[moderate]`
2. **An identical error is corrected far more often when it arrives from
   outside.** Presenting byte-identical wrong claims as a tool response or user
   message rather than the model's own prior thought raises correction rates by
   23 to 93 points, across seven model families. Independent review is not a
   process nicety; it is the mechanism. `[high]`
3. **Success falls steeply with the number of surfaces a change touches.**
   File-level localization accuracy of 81.7% degrades to 56.3% by the time an
   edit location is chosen, and multi-file benchmark resolution sits near 23%
   against over 70% for near-single-line work. `[high]` That localization is
   where the success is *lost*, rather than one measured stage among several, is
   an attribution no published ablation makes. `[synthesis]`
4. **Nobody has measured whether spec-first helps an agent.** Every vendor
   claim that spec-driven development improves quality or reduces rework is
   asserted without a controlled comparison. The defensible claims are about
   instruction shape, not about specs. `[high]`

---

## 1. Requirements quality has three mature frames, and none names six of our classes

### The frames

**ISO/IEC/IEEE 29148:2018** defines nine characteristics of a single
requirement — necessary, appropriate, unambiguous, complete, singular,
feasible, verifiable, correct, conforming — and five of a requirement *set*:
complete, consistent, feasible together, comprehensible, able to be validated
([ISO catalogue entry](https://www.iso.org/standard/72089.html), primary;
[ModernRequirements exposition](https://www.modernrequirements.com/blogs/iso-29148-explained/),
secondary). The standard presents these as properties to evaluate, not as a
weighted checklist with pass or fail thresholds; practitioner summaries
routinely add that scoring themselves, and several omit the ninth
characteristic. `[high]` for the lists; `[moderate]` that "conforming" is in the
2018 text, since it is confirmed by cross-referencing research rather than by
the paywalled standard.

**INCOSE's Guide for Writing Requirements** V4 carries 42 numbered rules in 14
categories ([reqi.io rule guide](https://reqi.io/articles/incose-requirements-quality-42-rule-guide),
secondary; [Jama exposition](https://www.jamasoftware.com/legacy/requirements-management-guide/writing-requirements/incose-requirements-writing-guide/),
secondary). Four families bear directly on criterion authoring: singularity
(R18–R23, including R19's explicit ban on conjunctions joining requirements),
non-ambiguity (R12–R17, covering escape clauses such as "where possible" and
open-ended clauses), quantification (R32–R35, measurable targets and real
bounds), and uniqueness (R29–R30, no duplication and no contradiction). The
guide supplies rules, not evidence that following them lowers defect rates.
`[moderate]`, downgraded because the full guide is member-restricted and both
citations are secondary.

**Requirements smells** (Femmer, Méndez Fernández, Wagner and Eder, *Journal of
Systems and Software* 123, 2017;
[preprint](https://arxiv.org/pdf/1611.08847), primary) catalogue eight lexical
tells: subjective language, ambiguous adverbs and adjectives, loopholes,
non-verifiable terms, superlatives, comparatives, negative statements, and
vague pronouns. Each maps to a 29148 characteristic. `[high]`

### The number that settles advisory versus blocking

The authors' `Smella` detector reached **48% precision at 87% recall** on
industrial German-language requirements. The authors read the low precision as
acceptable *because the tool triages candidates for a human rather than issuing
verdicts*. A later re-validation of the same smell catalogue on English
financial-domain requirements — Veizaga et al.'s `Paska` tool
([arXiv:2404.11106](https://arxiv.org/html/2404.11106v1), secondary) — reported
far higher precision, so the ceiling is domain- and language-dependent rather
than intrinsic. `[high]` for Smella's reported figures; `[moderate]` for the
re-validation, whose figures reach this survey through a secondary exposition
rather than the paper itself; `[moderate]` for transfer.

What transfers is the design response, and the two measurements do not even
measure the same quantity. Smella reports **precision**: 48% of its flags were
true, on one corpus. This repository's own attempt reports a **block rate**: an
emphasis-density predicate would have blocked 405 of 1,477 files, 27.4%,
against a 0.4% per-family budget, with precision never measured. One says half
the flags were wrong; the other says the volume alone was 68 times the budget.
Neither licenses a general false-positive figure. What both support is the same
design response: calibrate a family on its own corpus before proposing to block
on it, and advise until then. `[synthesis]`

### Where our classes have no prior-art home

Mapping this repository's shaping failure classes onto the three frames leaves
**five with no equivalent, and a sixth — draft narration — with only a weak
one.** That is the survey's most useful single result for authoring guidance,
because it says which classes cannot be imported and must be taught. The table
below marks the five with `none.`; read the sixth row's match as too weak to
import from.

| Our class | Nearest prior art |
| --- | --- |
| Too big — several independently verifiable outcomes | 29148 *singular*; INCOSE R18–R23, R19 no combinators; Gherkin one-rule-per-scenario |
| Cannot fail | 29148 *verifiable*; smell *non-verifiable terms* |
| Unsatisfiable or contradicts a sibling | 29148 *feasible* and set-level *consistent*; INCOSE R26, R30 |
| Not mechanizable | 29148 *verifiable*; smell *subjective language* |
| Unframed quantity | INCOSE R32–R35; smells *comparatives*, *superlatives* |
| Ungrounded claim, floating citation | 29148 *complete*; INCOSE R25 standalone reading |
| Said twice | INCOSE R29 no duplication |
| Decorative precision | INCOSE R10–R11 concision |
| **Wrong owner — the design should have delegated** | **none.** Uniqueness rules govern duplicated *text*, not duplicated *responsibility* |
| **Decays — a value or citation changes at its source** | **none.** The literature has requirements *volatility*, which is the requirement changing, not its evidence going stale underneath it |
| **Targets a projection rather than its source** | **none.** No frame distinguishes generated from authored artifacts |
| **Cuts a non-waivable control** | **none.** 29148 *necessary* asks whether a requirement is needed, never whether removing one drops a safety control |
| **Derivable enumeration** | **none.** No frame asks whether a hand-written set has a machine-readable source |
| **Draft narration** | weakest match: INCOSE concision, which trims words rather than stale reasoning. None of the three frames addresses tense or superseded content, because none assumes a reader who cannot tell current from historical |

**Four of the six share one cause** — decays, targets a projection, draft
narration, and derivable enumeration. Prior art assumes a
**human** reader of a **hand-maintained** document, and an agent reader cannot
tell a projection from a source, a stale citation from a live one, or a
superseded paragraph from a current one. The other two have their own causes,
given in the rows above: the delegation class is duplicated *responsibility*
rather than duplicated text, and the non-waivable-control class asks a question
29148's *necessary* does not. This paragraph is the one home for that grouping;
other artifacts cite it rather than recount it. `[inference]`

### What prior art has that we do not

**EARS**, the Easy Approach to Requirements Syntax (Mavin et al., IEEE RE'09,
developed at Rolls-Royce for jet-engine control;
[author's site](https://alistairmavin.com/ears/), primary) supplies five
sentence templates — ubiquitous ("the system shall X"), event-driven ("when T,
the system shall X"), state-driven ("while P, the system shall X"), unwanted
behaviour ("if T, then the system shall X"), and optional feature ("where F is
included, the system shall X"). AWS Kiro adopts EARS verbatim for
agent-consumed requirements
([Kiro feature-specs docs](https://kiro.dev/docs/specs/feature-specs/),
primary vendor). We ship no criterion syntax at all.

The evidence for EARS is weak: the original paper reports qualitative
practitioner assessment, and no controlled experiment with a defect-rate
outcome appears in accessible sources. `[low]`, downgraded for absent
controlled evidence. Its defensible value is *mechanical*: a fixed clause order
makes a missing trigger or a missing response visible without judgement, and
its "unwanted behaviour" template pairs a refusal with the positive path that
must still succeed.

**Set-level characteristics** are the second gap. Our failure classes are all
per-criterion. 29148's set-level *complete*, *consistent* and *able to be
validated* have no counterpart in our authoring guidance, and our one
set-level control is a size bound rather than a coverage one. `[synthesis]`

### The cost-of-late-defects claim does not hold at the quoted multipliers

Boehm's 1981 cost-of-change curve, popularised as 1:10:100, rests on 1970s
project data with small samples; Bossavit's citation audit found the graph
reproduced without its original confidence intervals
([ReworkCost analysis](https://reworkcost.com/boehm-cost-of-change-curve),
secondary). Boehm and Turner later put the agile-context slope nearer 1:5 to
1:20. The direction survives; the multipliers are heuristics. Do not cite a
number here. `[moderate]` for the direction, `[low]` for any multiplier.

---

## 2. What the spec and plan actually control in an agent's loop

### Simultaneous constraints decay near-multiplicatively

Two studies measure the same effect on different populations.

- A multi-dimensional constraint framework
  ([arXiv:2505.07591](https://arxiv.org/html/2505.07591v1), primary) reports
  average accuracy of **77.67% at level 1 (one to two constraints) falling to
  32.96% at level 4 (four to eight)**, a 44.71-point decline consistent across
  model families; the strongest model tested fell from 82.67% to 55.00%.
- *When Instructions Multiply*
  ([arXiv:2509.21051](https://arxiv.org/pdf/2509.21051), primary) reports an
  instruction-prompt rate of **57.08% at two constraints against 7.50% at
  eight**, decaying near-multiplicatively in the count.

`[moderate]`. The downgrade is a transfer gap, not a quality one: both
benchmarks score *one generation* against independent, stateless, verifiable
constraints such as format and word count. An acceptance-criteria set is
consumed over many turns, by an implementer with gates and tests between
attempts, and its criteria are not independent. The result therefore justifies
a **screening threshold that starts a conversation**, and cannot justify a
blocking count.

Adjacent evidence points the same way. *IFEval* (541 prompts, 25 verifiable
instruction types) saturates on strong models that then score below 50% on
*IFBench*'s 58 unseen constraint types, so a high score on a familiar
constraint set is not transferable capability
([IFBench summary](https://ai.miraheze.org/wiki/IFBench), secondary).
`[moderate]`

### An external verifier is the mechanism; self-review is not

*The Self-Correction Illusion*
([arXiv:2606.05976](https://arxiv.org/html/2606.05976v1), primary) placed
byte-identical erroneous claims in four chat-template roles — the model's own
thought block, a user message, a tool response, and system memory — and
measured correction rates. Presenting the error as externally sourced raised
correction by **23 to 93 percentage points**, significant at p<0.001 in 10 of
13 conditions, across seven model families. The failure is role-dependent, not
content-dependent. `[high]`

Two results qualify it rather than contradict it. `Reflexion`
([arXiv:2303.11366](https://arxiv.org/abs/2303.11366), primary) reaches 91%
pass@1 on HumanEval against 80% for its base model, but only because an
external correctness signal triggers each reflection. `CRITIC`
([arXiv:2305.11738](https://arxiv.org/abs/2305.11738), primary) shows genuine
self-correction *when the model calls a tool* — execution, search — rather than
introspecting. The consistent reading: correction needs an outside signal, and
a tool result counts as outside. `[high]`

Outcome reward models make the same point quantitatively. Best-of-N selection
under a trained outcome model lifts two coder models from 51.6% to 62.0% and
from 67.0% to 74.6% on SWE-bench Verified
([arXiv:2512.21919](https://arxiv.org/html/2512.21919), primary). `[moderate]`

**Consequence for authoring.** A criterion's value is the external signal it
creates. A criterion an implementer can only grade by reading its own output is
not a control, and the measured penalty for grading your own work is large
enough to treat as a design rule rather than a preference. `[inference]`

### Surface count, not task difficulty, is where multi-file work is lost

`Agentless` ([arXiv:2407.01489](https://huggingface.co/papers/2407.01489),
primary) measures a hierarchical localize-then-repair pipeline: **81.67%
file-level accuracy, 58.33% at function level, 56.33% at edit-location level**.
Accuracy is lost at each narrowing stage. `SWE-bench Pro`
([arXiv:2509.16941](https://arxiv.org/html/2509.16941v1), primary) reports the
best models near **23%** on tasks averaging 4.1 files and 107 lines, against
over 70% pass@1 on `SWE-bench Verified`, which is dominated by one- and
two-line fixes; `identified_incorrect_file` is a named failure category in its
analysis. `[high]`

This corroborates the one-primary-surface-per-slice bound from a second and
third independent source, and localizes the cause: the failure is choosing
where to edit, which is exactly what a spec's scope statement constrains.
`[synthesis]`

### Task length predicts success, and the curve is steep

METR's time-horizon work
([arXiv:2503.14499](https://arxiv.org/pdf/2503.14499), primary) defines the
50%-completion horizon as the human duration at which a model succeeds half the
time. Models approach 100% success on tasks a human finishes in under four
minutes and fall below 10% beyond four hours; step count correlates negatively
with success across every model tested, and one point of added "messiness"
costs about 8% mean success. A follow-on
([arXiv:2505.05115](https://arxiv.org/pdf/2505.05115), primary) models this as
exponential decay with a constant per-minute failure hazard, and flags its own
generalization as unknown. `[high]` for the measured curve, `[low]` for the
half-life model's transfer.

### A fixed plan is the wrong artifact; an adaptive one wins

`ADaPT` ([arXiv:2311.05772](https://arxiv.org/abs/2311.05772), primary)
decomposes recursively *only when the executor fails a subtask*, and beats
baselines by 28, 27 and 33 points on three environments. Depth-2 decomposition
reaches 44% and 52% where `ReAct` reaches 32% and 19% and a flat
plan-and-execute reaches 17% and 27%; returns diminish past depth 3. The stated
cause is cascade: under a fixed plan, one failed subtask fails the task.
`[moderate]`, downgraded because the environments are games and shopping, not
repositories.

The practical reading is a granularity *window*, not a floor: too coarse fails
on complexity, too fine wastes context. It is also direct support for keeping
the plan the document allowed to change while the contract stays fixed.
`[inference]`

### Over-compressing a step costs more than it saves

Cutting per-step context from 8,500 to 2,100 tokens raised average
turns-to-solve from 4.0 to 14.0 while total consumption fell only 14%, from
34K to 29.4K
([Augment Code engineering writeup](https://www.augmentcode.com/guides/ai-agent-loop-token-cost-context-constraints),
tertiary). `[low]` — a single practitioner report with no controlled arm. It is
the only published number on this trade-off and should be cited as
illustrative. Anywhere this figure is currently labelled *measured*, the label
overstates it.

Position effects are better evidenced. *Lost in the Middle*
([arXiv:2307.03172](https://arxiv.org/abs/2307.03172), primary) finds accuracy
highest when relevant content sits at the start or end of context and over 30
points lower when it sits centrally, persisting in explicitly long-context
models. Measured on retrieval and multi-document QA, not agent loops.
`[moderate]`

### Length is itself an anti-pattern, on the vendors' own account

Anthropic's Claude Code guidance states that an over-long project instruction
file gets half-ignored because important rules are lost in the noise, and
advises pruning to rules that would cause mistakes if absent and using emphasis
on one line rather than many
([Claude Code best practices](https://code.claude.com/docs/en/best-practices),
primary vendor). Its context-engineering post names *context rot* — a
performance gradient with token count rather than a cliff — and prescribes
sectioned instructions and a small set of canonical examples over exhaustive
edge-case lists
([Anthropic Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents),
primary vendor). `[moderate]`; vendor-sourced but consistent with the
constraint-count and position findings above.

---

## 3. Spec-driven development for agents: three products, no measurement

**GitHub Spec Kit** prescribes constitution → specify → clarify → plan → tasks
→ analyze → implement, with the "constitution" holding durable project
principles that scope every later step, and `clarify` and `checklist` as
explicit gates
([GitHub blog](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/),
primary vendor). Its stated rationale is that models complete patterns rather
than read minds, so vague prompts force wrong assumptions.

**AWS Kiro** splits a feature into `requirements.md` in EARS syntax,
`design.md`, and a `tasks.md` whose every step traces back to a named
requirement, alongside persistent steering files and event-driven hooks
([Kiro docs](https://kiro.dev/docs/specs/feature-specs/),
[hooks](https://kiro.dev/docs/hooks/), primary vendor).

**Tessl** distinguishes spec-assisted, spec-driven, and spec-centric practice,
the last treating code as disposable and regenerable. Its own expert roundup
names three failure modes: inconsistent regeneration within one build, loss of
design rationale once implementation exists, and **over-specification rigidity**
— excessive technical detail removing agent adaptability without adding
correctness
([Tessl roundup](https://tessl.io/blog/taming-agents-with-specifications-what-the-experts-say/),
secondary vendor).

Practitioner failure reports converge on four modes: vagueness with no concrete
anchor; spec-to-code drift, where the spec becomes a historical artifact while
tests still pass; over-specification rigidity; and context overload without
structure, where early directives are satisfied and later ones overlooked
([Osmani, *How to write a good spec for AI agents*](https://addyosmani.com/blog/good-spec/),
secondary practitioner). `[moderate]`, with a survivorship-bias downgrade: the
negative reports are sparser than the launch posts, so absence of a failure
mode here is not evidence it does not occur.

**No controlled comparison of spec-first against a baseline exists.** Every
improvement claim in this section is vendor-asserted or anecdotal, and all
three products are 2025-vintage with no longitudinal data. `[high]` — this is a
claim about the literature's contents, and it is the boundary on what any
authoring rubric may promise.

---

## 4. What this changes here

| Change | Evidence |
| --- | --- |
| An acceptance-criteria count ceiling has adjacent-regime evidence for its shape. Keep it a screening threshold and name the transfer gap; drop any claim that no evidence exists. | §2, arXiv:2505.07591 and arXiv:2509.21051 |
| Independent review is load-bearing, with a measured effect size. Warm self-review stays disqualified. | §2, arXiv:2606.05976 |
| The one-primary-surface bound now has three independent sources. Its per-stage figures are measured; that localization rather than repair is where the success is lost is a synthesis, not a measurement. | §2, Agentless and SWE-bench Pro |
| Five failure classes have no equivalent in requirements engineering and a sixth has only a weak one, so all six must be taught. The shared cause, and which classes it covers, is stated in § 1 § "Where our classes have no prior-art home"; the rest have their own, in that section's table. | §1 |
| A criterion syntax is the one clearly missing import. Adopt EARS shapes as an optional aid, never a gate — the evidence is practitioner-grade. | §1 |
| No set-level criteria checks exist here. 29148's set-level characteristics are the frame if that gap is taken. | §1 |
| The 8,500-to-2,100-token figure is a practitioner report, not a measurement. Relabel it where it is cited as measured. | §2, Augment writeup |
| Do not quote a cost-of-late-defect multiplier. | §1, Bossavit audit |

---

## Known unknowns

- **Known-unknown:** does an acceptance-criteria count above some threshold
  actually reduce delivery success in an agent loop with gates between
  attempts? Would be closed by an ablation over matched specs differing only in
  criteria count, scored on rounds-to-clean — the same paired-ablation design
  this repository's oracle survey already recommends.
- **Known-unknown:** does EARS syntax reduce defects, as against reducing
  syntactic variance? Would be closed by a controlled authoring experiment with
  a defect-rate outcome; none exists for EARS in 16 years.
- **Known-unknown:** what fraction of agent repair failures originate in
  localization rather than patch generation? `Agentless` publishes per-stage
  accuracy but no ablation attributing final failures, so the dominant-cause
  claim is inferential. Would be closed by that ablation.
- **Known-unknown:** does the constraint-count decay curve hold for stateful,
  sequential, partially conflicting instructions? Every benchmark found tests
  independent stateless constraints. Would be closed by a procedural-instruction
  benchmark; none was located.
- **Unknowable as posed:** whether this repository's own six unmatched failure
  classes are novel or merely absent from accessible literature. The
  member-restricted INCOSE guide and the paywalled 29148 text were read through
  secondary expositions, so an unmatched class may be matched in text not
  retrievable here.
- **Unknowable:** the effect of spec quality isolated from model capability in
  the 2025 product cohort. The counterfactual runs were never recorded, the
  products shipped without instrumented baselines, and the model generation
  changed underneath them.
