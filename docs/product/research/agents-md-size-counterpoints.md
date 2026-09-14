# Counterpoints — [`agents-md-size-survey.md`](agents-md-size-survey.md)

Adversarial pass, auto-invoked by desk-research deep mode, 2026-09-13.

**Headline: the review overturns more of the survey than it confirms.** One
finding must be retracted outright, one downgrade cascades into the survey's
central recommendation, and the survey committed the exact fallacy it warned the
requester against. The corrected reading of the evidence points *away* from the
proposed change, or at least away from doing it without a kill condition.

Two verification passes drove most of this. First, every arXiv abstract cited in
the survey was read directly — the survey had verified only that titles resolved,
which is not content verification. Second, Anthropic's published guidance was
fetched and quoted firsthand rather than through a retriever.

---

## Finding 7 — "The displacement cost of promotion has never been measured" `[uncertain]`

- **Counter-position:** It has been measured, the survey cited the paper that
  measures it, and the survey described that paper as something else entirely.
  This is not a weakening — it is a factual error that inverts the finding.

- **Counter-evidence:** The survey reported arXiv:2603.13351 as "models reach
  only 68% at maximum instruction density, with three decay curves and a
  measured bias toward earlier instructions." Those are IFScale's results
  (arXiv:2507.11538). The actual abstract of 2603.13351 reads:

  > We tested STAR inside InterviewMate's 60+ line production prompt, which had
  > evolved through iterative additions of style guidelines, format
  > instructions, and profile features. Three conditions, 20 trials each, on
  > Claude Sonnet 4.6 … C scored 100% (verified at n=100). A and B scored 0% and
  > 30%. … Prompt complexity dilutes structured reasoning. STAR achieves 100% in
  > isolation but degrades to 0-30% when surrounded by competing instructions.
  > The mechanism: directives like "Lead with specifics" force conclusion-first
  > output, reversing the reason-then-conclude order that makes STAR effective.

  This is a direct measurement of displacement, and the displacing content is
  *accumulated style guidelines in a grown instruction file* — the exact change
  under consideration. The named mechanism is a prose-style directive overriding
  a reasoning behaviour.

  Corroborating, from arXiv:2601.22047's abstract: inserting a **self-evident
  constraint** — one "naturally met by the original successful model output and
  extracted from it" — produces "substantial performance drops, even for advanced
  models such as Claude-Sonnet-4.5", and "failed cases allocate significantly
  more attention to constraints compared to successful ones." A constraint that
  is *already satisfied* still costs performance. That is displacement with the
  benefit side held at zero.

- **Verdict:** **Retraction, not downgrade.** The claim "nobody has measured
  this" is false and must be struck from the survey. Replace with: displacement
  has been measured twice, both times negative for adding instructions, at
  `[low]` confidence — 2603.13351 is n=20 per condition on a single problem by a
  single author citing their own prior work, and 2601.22047 measures task
  performance rather than per-rule adherence. Weak evidence pointing one
  direction still outranks a false claim that no evidence exists.

---

## Finding 1 — "File size does not detectably change adherence" `[moderate]`

- **Counter-position:** The survey leaned the whole "size is safe" conclusion on
  a single unreplicated preprint, treated "affirmative-null Bayes factor" as
  though it settled the matter, and never checked whether the study's
  manipulated size range even contains this repository's file.

- **Counter-evidence:**

  **The Bayes factor is weaker than "affirmative" implies.** BF10 = 0.05–0.10 is
  BF01 = 10–20. On Jeffreys' scale that is "Strong" (10–31.6); on Kass & Raftery
  it straddles the "Positive" (3–20) / "Strong" (20–150) boundary. Neither scale
  calls it decisive, and the survey's phrasing implied more.

  **No prior-sensitivity analysis is reported.** The Bayes Factor Reversal
  Paradox (arXiv:2511.22152, 2025) shows that for realistic sample sizes, two
  scientifically plausible prior variances can yield opposite BF conclusions from
  identical data. Published guidance (AMPPS 2018) treats BF-across-prior-scales
  as mandatory for a robustness claim. Without it, BF01 = 10–20 is a point
  estimate under an undisclosed default prior.

  **No SESOI, so "null" has no practical referent.** Lakens (2017) is explicit
  that a non-significant result is not evidence for absence; only a
  pre-registered equivalence test against a declared smallest effect size of
  interest can support one. A 10% adherence difference would matter operationally
  here. Whether the study could detect one is unknown.

  **The factorial design is a standard underpowering trap.** Four variables plus
  three two-way interactions, seven tests under multiple-testing correction, with
  per-cell N diluted across 2 codebases × 3 models × 5 tasks. Lakens & Caldwell
  (2021) built the Superpower package precisely because standard tools
  underestimate factorial sample requirements; ordinal interactions carry roughly
  half the effect size of the corresponding simple effect. "No detectable
  contrast after correction" in a 7-test design is routinely a power artifact.
  The abstract reports no prospective power calculation.

  **Zero independent scrutiny.** Four months post-publication, the paper has no
  academic citations, no replication, no critique, and no domain response — only
  automated aggregator listings. Single author, no peer review.

  **Applicability is unverified.** The survey needed to know whether this
  repository's file (~120 lines, proposed ~137) sits inside the manipulated size
  range. A retriever reported the range as 25–500 lines. That is **not in the
  abstract**, no HTML version of the paper exists (arxiv.org/html returns a stub),
  and no PDF extractor is available in this environment. So the single most
  important applicability fact about the survey's single most load-bearing
  citation **could not be verified**.

  **Construct validity.** The compliance target was "a trivial target
  annotation." The rule this decision concerns is prose style — reading level,
  table use, closing filler. There is no evidence these behave alike.

- **Verdict:** **Rating downgrade — `[moderate]` → `[low]`.** Downgrade factors:
  single unreplicated source (triangulation absent), no peer review, no prior
  sensitivity, no SESOI, probable interaction underpowering, construct mismatch,
  and unverified applicability range.

---

## Finding 2 — "Vendor guidance says the opposite, and cites nothing" `[high]`

- **Counter-position:** The survey resolved a vendor-versus-preprint conflict in
  favour of the preprint. That resolution is scientism: it prefers a visible weak
  measurement to an invisible possibly-strong one. Anthropic observes Claude Code
  at a scale no academic study can reach. Worse, the survey omitted the vendor
  sentence that describes this repository's exact failure and prescribes the
  opposite remedy.

- **Counter-evidence:** All quotes verified firsthand from
  `code.claude.com/docs/en/best-practices` and
  `anthropic.com/engineering/effective-context-engineering-for-ai-agents`.

  The sentence the survey missed:

  > If Claude keeps doing something you don't want despite having a rule against
  > it, the file is probably too long and the rule is getting lost.

  That is a named diagnosis of the observed symptom — a rule in the file, ignored
  in practice — and its prescription is to prune, not to inline. Alongside it:

  > Bloated CLAUDE.md files cause Claude to ignore your actual instructions!

  But the same vendor supplies both halves of the tension. Also from the best
  practices page:

  > CLAUDE.md is loaded every session, so only include things that apply broadly.
  > For domain knowledge or workflows that are only relevant sometimes, use
  > skills instead.

  The cognitive-load rule *does* apply broadly — it governs every reply. By
  Anthropic's own routing test it belongs in the always-loaded file, not behind
  an on-demand pointer. And from the context-engineering post:

  > minimal does not necessarily mean short; you still need to give the agent
  > sufficient information up front to ensure it adheres to the desired
  > behaviour.

  Two further considerations cut against pure deference to the vendor. Anthropic
  frames context rot as a function of "the number of tokens in the **context
  window**" accumulating through a conversation — not as a property of a fixed
  file loaded at session start. The survey and the vendor page may be discussing
  different mechanisms. And there is an unruled-out commercial explanation: every
  always-loaded line is billed input on cache miss, so "write shorter files" is
  also a cost-control message, and adherence framing is the version users act on.

  Vendor prompt guidance has a measured track record of failing to replicate:
  chain-of-thought is not a uniform improvement and harms some non-reasoning
  tasks (arXiv:2510.22251); politeness guidance reverses under measurement, with
  impolite phrasing scoring better on multiple choice (arXiv:2510.04950).

- **Verdict:** **Do-not-resolve.** Both positions are well-evidenced and hold
  under different conditions, and the dividing variable is signal density, not
  length. The vendor's claim holds when added text is low-signal — filler,
  redundancy, stale content, things the model could infer — which is what
  "bloated" describes and what "would removing this cause Claude to make
  mistakes?" tests for. The study's null holds when added text is high-signal and
  broadly applicable. More evidence would not collapse this, because the two
  sides are answering different questions: "does length cause failure?" versus
  "does low-signal content cause failure, with length as its symptom?"

  The operational reading: **the survey's question was mis-posed.** "Can we grow
  the file to ~2,150 tokens" is the wrong question. "Is every line we are adding
  load-bearing" is the question both sides actually answer, and it has a test
  Anthropic supplies directly — would removing this line cause a mistake?

---

## Finding 8 — "Long sessions, not file structure, carry the largest effect" `[moderate]`

- **Counter-position:** The survey laundered a post-hoc finding by triangulating
  it with two studies that measure different phenomena, then used the result to
  drive its central recommendation.

- **Counter-evidence:** The survey's own text concedes McMillan's session-decay
  effect was "identified during analysis rather than pre-specified" and is
  "non-monotonic rather than a constant per-step effect." Post-hoc, in a design
  with no pre-registration, in a domain where arXiv:2606.11217 argues AI-agent
  experiments carry unusually high researcher degrees of freedom because "model
  selection, prompt wording, settings, and outcome-contingent redesign are easy
  to exploit and difficult to detect."

  The triangulation does not hold on inspection of the abstracts:

  - **Multi-IF** (arXiv:2410.15553) is **three turns**, multilingual, and each
    turn *adds new instructions*. The o1-preview 0.877 → 0.707 drop measures
    accumulating instruction load across turns, not decay of a rule set at turn
    one. It also attributes much of the error to non-Latin scripts.
  - **MT-Eval** (arXiv:2401.16745) names its key factors as "distance to relevant
    content and susceptibility to error propagation", and reports degradation
    "not correlated with the models' fundamental capabilities." The survey's
    claim that "every model except GPT-4 struggles to hold initial global
    instructions" **does not appear in the abstract** and came from a retriever's
    characterisation.
  - **McMillan** measures odds of compliance per *generated function* within a
    session.

  Three different constructs: added-instruction load, retrieval distance plus
  error propagation, and per-artifact generation decay. Calling that convergence
  is generous.

- **Verdict:** **Rating downgrade — `[moderate]` → `[low]`.** Downgrade factors:
  post-hoc identification without pre-registration, non-monotonic effect, and
  invalid triangulation across distinct constructs. The *direction* — long
  sessions erode adherence — retains modest support across all three, and matches
  the observed failure. The specific OR = 0.944 figure should not be quoted as
  established.

---

## Finding 6 — "Short-context evidence points toward recency" `[low]`

- **Counter-position:** Labelling this an `[inference]` was still too generous.
  The paper explicitly excludes the conditions the survey extrapolated it to.

- **Counter-evidence:** From arXiv:2601.04098's abstract, the design is "a layer
  conductance framework within a sliding-window design, applied to short-context
  next-word prediction **to isolate model-internal behavior from task and
  context-window pressure**." The paper deliberately removes task pressure — and
  instruction compliance *is* task pressure. Using it to argue a rule belongs
  last is extrapolating a result from a setting constructed to exclude the
  phenomenon of interest.

- **Verdict:** **Rating downgrade — `[low]` → `[uncertain]`,** with the
  "rule belongs last" suggestion struck entirely rather than restated. Downgrade
  factor: construct exclusion by design. Finding 6's defensible core — that no
  study tests position effects on compliance at ~2k tokens — survives untouched.

---

## Cross-cutting: claims sourced from retriever characterisation, not read

The survey verified that 16 arXiv identifiers resolved with matching titles, then
presented retriever-supplied numbers as if verified. Reading the abstracts
directly, the following survey claims are **not supported by the abstracts** and
must be marked as unverified or removed:

| Survey claim | Status against abstract |
| --- | --- |
| ManyIFEval per-model table (GPT-4o 0.94/0.57/0.21, etc.) | Not in abstract. Abstract confirms only "performance consistently degrades", ten LLMs, ≤10 instructions, ~10% regression error |
| IFScale decay patterns *named* threshold/linear/exponential, assigned to o3, Gemini 2.5 Pro, Claude 3.7 | Not in abstract. Abstract says only "model size and reasoning capability correlate with 3 distinct performance degradation patterns" |
| IFScale "~150–250 instruction knee" | Not in abstract |
| Control Illusion: 74.8–90.8%, 9.6–45.8%, 0.1–20.3% | Not in abstract |
| PRIME: 70% / 30% / 48–50% first-directive bias | Not in abstract. Abstract also limits scope to **five open-weight models** — no frontier closed models, which the survey did not disclose |
| Agent READMEs word medians (485 / 535 / 335) | Not in abstract. The instruction-type percentages (75.9 / 70.8 / 68.1 / 14.8 / 14.5) **are** confirmed |
| MT-Eval "all models except GPT-4" | Not in abstract |
| McMillan tested size range 25–500 lines | Not in abstract; unverifiable — no HTML version, no PDF extractor available |

**A finding the survey omitted, and should not have.** Control Illusion's abstract
reports that "societal hierarchy framings (e.g., authority, expertise, consensus)
show stronger influence on model behavior than system/user roles, suggesting that
pretraining-derived social structures function as latent behavioral priors with
potentially greater impact than post-training guardrails." If that holds, *how a
rule is framed* is a larger lever than *where it sits* — which is more actionable
than anything in the survey's position section, and it went unreported.

---

## Cross-cutting: the survey committed the fallacy it warned against

- **Counter-position:** The survey concluded "inlining is cheap, carries no
  evidenced downside, and removes two demonstrably-skipped hops, so there is no
  reason not to do it." That conclusion rests on findings that are — by the
  survey's own ratings — one `[moderate]` null (now `[low]`), two unknowns, one
  `[uncertain]`, and a gap section listing six known-unknowns. Absence of
  evidence of harm was converted into evidence of absence of harm, in a document
  written to warn the requester against unfalsifiable claims.

- **Counter-evidence:** The survey's own Finding 7 gap text, and the retracted
  claim above — displacement evidence existed and pointed the other way.

- **Verdict:** **The recommendation is sustained in direction but must carry a
  kill condition.** Inlining still removes two hops that were provably skipped,
  which is a mechanism-level gain independent of any adherence measurement. But
  it must ship as a falsifiable change, not a settled one. Minimum:

  1. Name what would count as failure before making the change — a specific rule
     in `AGENTS.md` whose adherence is expected to hold, and the observation that
     would show it did not.
  2. Apply Anthropic's own test line by line to the 17 added bullets: would
     removing this cause a mistake? The do-not-resolve verdict on Finding 2 says
     signal density, not length, is the live variable.
  3. Prefer promoting-and-pruning to pure addition. Every source that measured
     displacement measured it for *added* instructions; none measured net-neutral
     replacement.

---

## Summary of verdicts

| Survey finding | Verdict | Result |
| --- | --- | --- |
| 7 — displacement never measured | Retraction | Claim is false; two measurements exist, both negative for addition |
| 1 — size null | Downgrade | `[moderate]` → `[low]` |
| 2 — vendor contradiction | Do-not-resolve | Signal density, not length, is the real variable |
| 8 — session decay | Downgrade | `[moderate]` → `[low]`; triangulation invalid |
| 6 — recency in short context | Downgrade | `[low]` → `[uncertain]`; "rule belongs last" struck |
| 4, 5, 9 | Sustained with corrections | Specific figures unverified; see table above |
| Overall recommendation | Sustained with conditions | Direction holds; must ship with a kill condition |

## Counterpoint citations

| Work | Identifier | Primacy |
| --- | --- | --- |
| Anthropic, Claude Code best practices | [code.claude.com/docs/en/best-practices](https://code.claude.com/docs/en/best-practices) | Primary (quoted firsthand) |
| Anthropic, Effective context engineering for AI agents | [anthropic.com/engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Primary (quoted firsthand) |
| *Prompt Complexity Dilutes Structured Reasoning* | [2603.13351](https://arxiv.org/abs/2603.13351) | Primary (abstract read) |
| *On the Paradoxical Interference…* | [2601.22047](https://arxiv.org/abs/2601.22047) | Primary (abstract read) |
| *The Bayes Factor Reversal Paradox* | [2511.22152](https://arxiv.org/abs/2511.22152) | Primary |
| Lakens & Caldwell, *Simulation-Based Power Analysis for Factorial ANOVA Designs* | [AMPPS 2021](https://journals.sagepub.com/doi/10.1177/2515245920951503) | Primary |
| Lakens, *Equivalence Tests: A Practical Primer* (TOST / SESOI) | [SPPS 2017](https://journals.sagepub.com/doi/10.1177/1948550617697177) | Primary |
| *Preregistration for Experiments with AI Agents* | [2606.11217](https://arxiv.org/abs/2606.11217) | Primary |
| Linde et al., TOST vs. Bayes-factor interval nulls | [2104.07834](https://arxiv.org/abs/2104.07834) | Primary |
| *Mind Your Tone: How Prompt Politeness Affects LLM Accuracy* | [2510.04950](https://arxiv.org/abs/2510.04950) | Primary |
| *You Don't Need Prompt Engineering Anymore* (CoT non-universality) | [2510.22251](https://arxiv.org/abs/2510.22251) | Primary |
| Jeffreys scale reference | [StatLect](https://www.statlect.com/fundamentals-of-statistics/Jeffreys-scale) | Secondary |
| Kass & Raftery thresholds (`pcal` docs) | [ptfonseca.github.io/pcal](https://ptfonseca.github.io/pcal/reference/bfactor_interpret.html) | Secondary |
| Prior-robustness guidance | [AMPPS 2018](https://journals.sagepub.com/doi/pdf/10.1177/2515245918779348) | Secondary |
| Gelman, 16× sample size for interactions | [statmodeling.stat.columbia.edu](https://statmodeling.stat.columbia.edu/2023/11/09/you-need-16-times-the-sample-size-to-estimate-an-interaction-than-to-estimate-a-main-effect-explained/) | Secondary |
