# Criterion shape and size: what the evidence supports

**Question.** Is there science on acceptance-criterion shape and size, and does it
transfer to agent/LLM development?

**Discipline.** Mixed. Findings F1–F7 and F10 are academic (primary sources,
triangulated where marked). Findings F8–F9 are practitioner grey literature under
the applied overlay: same-vendor sources collapse to one, and survivorship bias is
named where it applies.

**Motivating local corpus.** 252 specs, 3,990 acceptance criteria: 30% exceed 60
words, 73% contain a universal or negative quantifier. One criterion was restated
across 15 places in a spec/plan pair. Mined transcripts show 30 of 45 findings in
one round originating in prior repairs.

---

## Findings

> **Model-generation sensitivity.** F5, F6 and F7 concern LLM behaviour and are
> vulnerable to model progress; they are dated and downgraded accordingly.
> F1–F4 and F10 concern human comprehension, requirements practice, and detector
> precision over text. Those do not decay with model generation, and the findings
> that decide the criterion-shape question rest on them.

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

## What this means for a criterion-shape gate

1. **A size threshold would encode folklore.** F1 is the decisive finding: the
   atomicity rule has no empirical footprint in 105 studies.
2. **A lexical quantifier trigger is a known dead end.** F2 — 59% precision in the
   field's own benchmark, and negation detection is its weakest category.
3. **Size is the wrong axis; verifiability is the right one.** F3's remedy —
   enumerate or bound the set — targets the property that actually breaks review,
   and it is what F6's mechanism would predict hurts an agent too.
4. **Any threshold is capability-moderated, and the model evidence is dated.** F7
   means a fixed number cannot be correct across models — and F5–F7 all rest on
   superseded model generations, so the LLM half of this survey should not be
   load-bearing for a durable rule. The findings that kill the size gate (F1–F3)
   are about humans and text, and do not decay.
5. **The additive-repair loop (F9) is the mechanism our own corpus shows**, and the
   only proposed remedy is subtractive. Adding a gate is the move that failed.

---

## Known unknowns

- **Known-unknown:** Does mid-context degradation still hold on current-generation
  models? The evidence base (F6) tests Claude 1.3, GPT-3.5-Turbo, MPT-30B and
  LongChat-13B — all superseded, on the axis where models have improved most.
  Would be closed by a position-bias replication on current frontier models. A
  targeted arXiv search found none. Until then F6's mechanism should not carry a
  design decision on its own.
- **Known-unknown:** Does criterion word count causally affect agent success,
  holding content constant? Would be closed by an ablation varying AC length with
  fixed semantics on a coding-agent benchmark. F6 gives the mechanism; nobody has
  run it on acceptance criteria.
- **Known-unknown:** Is our 73% quantifier hit rate high, normal, or low? No
  published base rate exists for "percent of criteria flagged by a bare quantifier
  regex", so the number cannot be compared to prior art.
- **Known-unknown:** Does requirement size predict the number of review cycles to
  agreement? No study found. This is the question our transcripts raise and the
  literature does not answer.
- **Known-unknown:** Is the additive-repair loop (F9) general? Would be closed by
  round-over-round finding counts from several independent multi-round review
  systems.
- **Unknowable as posed:** Whether "the right AC size" exists as a transferable
  number. F7 makes it model-dependent and F10 makes relevance
  lifecycle-dependent, so a single threshold has no fixed referent to measure
  against.

## Retrieval limitations

- arXiv returned zero results on the first pass — HTTP 429 rate-limiting on all
  three queries, not absence of evidence. Re-run sequentially with 25s spacing,
  which succeeded. Broad free-text queries also returned noise (824,184 matches);
  usable results required fielded `--abstract` plus `cs.SE` category.
- Two retrievers reported PDF extraction failures (Wohlin et al. 2002; the
  requirements-quality roadmap). Claims resting on those are marked down.
- Femmer's 59%/82% figure was independently verified against the primary full text
  rather than taken from a retriever summary.
- No verifiable Reddit thread was found with a stable URL; Reddit is not cited.
- Practitioner failure reports skew toward people who tried the tooling and blogged
  about friction. Silent successes are absent by construction.

## Sources

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

**Grey literature (vendor — each counts as one)**
- GitHub Blog. *Spec-driven development with AI.*
- Tessl. *Spec-driven development: 10 things you need to know about specs.*
- Amazon Kiro documentation.

**Grey literature (independent practitioner)**
- Burton, M. (2025-11-06). *A Deeper Dive into GitHub Spec-Kit — Learning from Initial Missteps.*
- GitHub Spec Kit Discussion #152, *Evolving specs.*
- Ospina, D. *agent-infra* Issue #1089 — additive-repair loop with per-cycle counts.
- Zaninotto, F. (2025-11-12). *Spec-Driven Development: Waterfall Strikes Back.* Marmelab; and HN discussion 45935763.
- Paddo.dev (2026-01-28). *The Framework Trap.*
- Wavect. *GitHub Spec Kit Review for Production Teams.*
- Fowler, M. *Understanding Spec-Driven-Development.*
