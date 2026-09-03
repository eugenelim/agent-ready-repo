# Brief: does written guidance activate, here and elsewhere?

- **Slug:** `guidance-activation-measurement`
- **Received:** 2026-09-02
- **Owner:** Repository maintainers (`ini-002`)
- **Status:** Draft

## Outcome

We know whether the written-guidance mechanism binds — graded on what an author
produced while a rule was in context, and on the run provenance of that
authoring, rather than on whether the rule was loaded. Today we cannot tell
binding from presence, so every rule this repository ships is unfalsifiable: it
can be loaded, tested, cited to a reviewer as authority, and complied with, and
still do nothing.

### Grading contract

The grading contract admits run and revision provenance. On 2026-09-02, a
spike tested the six floor rules against an authored-artifact-only contract and
found only two of them gradable: some rules are satisfied by *process* facts an
authored artifact cannot record. `new-spec` step 5a requires that a probe ran
before review, stayed side-effect-free, and was not committed; the razor's
bounded-search rung requires that a search ran and its hit was recognised.
Neither leaves a trace in the spec or plan that results from it. Grading those
from authored output alone would mean reading absence as "did not fire", which
fabricates observability the rules never asked for — so the contract admits tool
traces and git evidence for the process half. **What it still refuses is the
guidance file itself**: reading the rule to see whether the rule exists is the
conflation this brief was written to end.

### Portable estimand

The estimand is portable: does this mechanism work across adopter repositories,
not only here? External repositories have to be selected, read in temp
read in temp and set up, and each sampled rule needs a task that
makes it apply.

### Separate strata

The measurement runs a *local* stratum over
named rules in this repository and an *external* stratum over anonymized
adopter repositories read in temp, and the report keeps them separate. Aggregating them would
dissolve the thing the siblings consume: three of their slices read individual
local verdicts, and a blended score cannot resolve any of them. The local
stratum is mandatory; the external stratum is what makes the claim portable.

The graded artifacts are produced by the agent under test inside the eval run.
"On artifacts the author wrote" means the rule is judged against authored
output, not against the guidance file — it does not mean the corpus is
scavenged from history.

This brief produces one report. It ships no rule.

## The measurement is an ablation, not an inspection

**A compliant artifact does not show that a rule was used.** Webson and Pavlick
found irrelevant and misleading prompts performing as well as instructive ones
(NAACL 2022), so single-condition inspection cannot separate "the rule bound"
from "the model would have done it anyway". The evidence and its limits are in
[`agent-behavior-oracle-patterns-survey.md`](../research/agent-behavior-oracle-patterns-survey.md).

This brief is therefore the **second** of a two-test design (owner decision,
2026-09-02). The first test — a per-policy compliance validator — belongs to
[`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md),
and this brief consumes it. What remains here is the causal question: **does the
prose add behavioral value above the mechanical control?**

**The design, and every element is load-bearing:**

- **Three conditions per task:** the rule present, the rule removed, and a
  **length-matched placebo**. The placebo is not optional — deleting text also
  changes context length, position, and salience, so a two-condition test
  measures "less text" rather than "no rule".
- **Frozen for the run:** model, decoding configuration, surrounding prompt,
  tool set, and evaluator. A change to any of them starts a new run.
- **A challenge set with room to fail.** Tasks are selected so the control
  condition *can* violate the rule. A ceiling hides the effect, and this
  repository has a live ceiling: all three sibling briefs already pass the
  cognitive-load grade threshold.
- **The evaluator is blinded to condition**, or it rationalises the treatment
  arm.
- **Repetitions per task**, because generation is stochastic.
- **Paired analysis** — McNemar for paired binary outcomes — with a
  **pre-registered minimum effect**, not mere significance.
- **A non-inferiority check on unrelated quality**, because a rule can "work" by
  degrading the whole answer.

**Every statistical outcome maps to a verdict, and the mapping is
pre-registered.** M1 owns this table; without it the arms produce a result with
no defined reading.

| Outcome | Verdict |
| --- | --- |
| Treatment beats both removal and placebo, lower bound above the pre-registered effect | **fired** |
| Treatment beats removal but not the length-matched placebo | **not gradable** — the effect is attributable to context length, not the rule |
| Both arms comply | **not gradable** — redundant rule, ceiling, or blind evaluator; never read as fired |
| Both arms fail | **not gradable** — ineffective rule, incapable model, or blind evaluator |
| Treatment worse than removal | **did not fire**, and recorded as a rule that backfires |
| Confidence bound spans the pre-registered effect, or variance is high | **not gradable**; expand cases rather than widen the threshold |
| Non-inferiority fails on task correctness or another policy | **did not fire** — a rule that works by degrading the answer has not worked |

**The verdict is per rule at suite level, never per artifact.** An ablation
establishes a population-level effect; it cannot say a rule failed to influence
one document. Slices reading a verdict — A4, A5, B2 — read "this rule
demonstrated incremental behavioral value above the mechanical control, at or
above the pre-registered effect", which is a stronger and better-defined line
than compliance.

**Two failure modes this design must report rather than resolve.** Both
conditions good means the rule may be redundant, the set may have a ceiling, or
the evaluator may be blind. High variance means no gating claim at all — expand
the cases or improve the oracle, never widen the threshold.

## Why it is separate, and first

Two sibling briefs both ship written guidance, and both are worth building only
if written guidance activates:

- [`agent-authoring-input-quality.md`](agent-authoring-input-quality.md) — the
  contracts a review loop converges on.
- [`stage-input-readiness.md`](stage-input-readiness.md) — no stage starts on
  input it cannot work from.

Folding this measurement into either one would make the other wait on that
brief's first slice for a report it does not otherwise depend on. It is
separate so both can consume it, and first because neither can size its
deliverable without it.

`stage-input-readiness`'s gate half is mechanical by construction and never
needed this report; it runs in parallel.

Only the **local** stratum gates them. Both siblings read individual local
verdicts, so M3 is the unblocking point and M4's portability result is additive
— which is why the strata are separate slices rather than one pass.

## Success metrics

- The report states, **before the first run**, which result means written
  guidance binds. A decision rule written after the results is not a decision
  rule.
- Every rule in the corpus gets a per-rule verdict — fired, did not fire, or
  not gradable — rather than one aggregate score.
- **The two strata are reported separately.** A reader can find each local
  floor rule's verdict without reading the external stratum, and no figure in
  the report blends the two. This is the metric that protects the siblings: a
  portable claim that averaged the strata would leave A4, A5 and B2 unsourced.
- A rule that cannot be given a decision rule is dropped from the corpus and
  the drop is recorded, rather than graded loosely. This never applies to the
  six local floor rules.

## Scope / Non-goals

**In scope**

- **The corpus and the decision rule.** Which rules are under test, which
  authored output they are graded on, and what converts a result into "binds"
  or "does not bind".
- **The local stratum — six named rules, and it is a floor M1 may not silently
  drop.** Three are read directly by sibling slices: **repository anchoring**
  (decides A5), **`new-spec` step 5a** (decides A4), and **`work-intake`'s
  public routing precedence** — the rule at `work-intake/SKILL.md` § "Public
  routing precedence" that routes an explicit status request straight to
  `workspace-status`. As of 2026-09-02, this is the representative for prose in
  a routing surface and already carries an eval case in that
  skill's `evals/evals.json`. The other three widen the rule *shapes* covered:
  **cognitive-load simplification**, **the observable-outcome rule**, and **the
  razor's bounded-search rung**. Six rules chosen on purpose; this is not a
  claim to cover every sentence in the repository.
  If a floor rule comes back *not gradable*, that is an owner escalation, not a
  silent drop — the drop rule stated in § "Success metrics" applies to the rest
  of the corpus, never to the floor. A floor rule that fails blinded rubric validation is not
  replaced by an external or synthetic substitute; `not gradable` is the honest
  result.

  **The floor's locators and gradability, measured 2026-09-02.** M1 owns
  finalising this table; it is recorded here because two rows are the
  escalation the paragraph above anticipates, and because sibling slices read
  three of them.

  | Floor rule | Canonical home | Status |
  | --- | --- | --- |
  | `work-intake` public routing precedence | `work-intake/SKILL.md` § "Public routing precedence" | **Gradable.** B2's deciding line. |
  | The observable-outcome rule | `new-spec/assets/spec.md` § Acceptance Criteria | **Gradable** on authored criteria. |
  | `new-spec` step 5a | `new-spec/SKILL.md:475` | **Gradable only with run provenance** — its obligations are process facts. A4's deciding line. |
  | The razor's bounded-search rung | root `AGENTS.md`, the cut-before-adding ladder | **Gradable only with run provenance** — a search and its recognition leave no authored record. |
  | Repository anchoring | **`new-spec`'s plan `Repository anchors` field** (owner decision, 2026-09-02). The rule is a family — `adapt-to-project`, `contract-acquisition`, `new-spec` and `work-loop` each carry a normative span, plus `architect-design` in the architect pack — and this variant is selected because it is the only one with an authored artifact a grader can read, and it is the variant A5's question is about. | **Gradable.** A5's deciding line. |
  | Cognitive-load simplification | `.agents/rules/cognitive-load.md` § "Prose and artifacts" and § "Author load", activated by the `always` row in `AGENT_RULES.md`. The label is editorial — "simplification" appears nowhere in either file. **Not the readability target: the rule scopes that to chat prose.** | **Gradable in part; see below.** |
  **The readability score is not this rule's decision rule, and the rule says so
  itself.** Measured 2026-09-02, `tools/check-output-readability.py`
  ships here, computes Flesch reading ease and Flesch–Kincaid grade level, and
  accepts arbitrary paths, so grading an artifact with it is cheap. It is still
  the wrong oracle, for two reasons taken from the rule's own text:

  - **The target is scoped to chat prose.** The rule reads "For *common chat
    prose*, aim for a Flesch Reading Ease score of at least 70 and a US school
    grade of at most 8." A brief or a spec is not chat prose, so scoring one
    against that threshold measures an obligation the rule never imposed, and a
    failing score would be reported as "did not fire" for an artifact class the
    rule does not govern.
  - **The rule forbids the inference.** It states "A score is a clue. It is not
    a reason to cut needed facts", alongside "Keep all asked-for depth, proof,
    limits, warnings, code, diffs, errors, exact names, paths, and counts." A
    decision rule that treated a low score as non-compliance would push authors
    to delete substance to score well — the opposite of the rule.

  Measured anyway, because the numbers bound what any future oracle can claim:
  across 60 authored specs, grade level ran min 4.62, median 6.68, p90 10.58,
  and 44 of 60 passed a ceiling of 8, while reading ease ran median 60.70
  against a floor of 70 and the two together passed only 7 of 60. All three
  briefs in this split already pass the grade ceiling. So the score does not
  separate compliant from non-compliant authoring here; it mostly separates
  technical prose from chat.

  **What M1 grades instead**, and it is only part of the rule: the artifact-facing
  clauses in § "Prose and artifacts" and § "Author load" that have observable
  consequences — a form that fits the facts, one load-bearing point per part,
  long lists grouped, and no point stated twice. **M1 must name the exact
  clauses and their artifact class before M2b runs.** The remaining clauses are
  judgment ("short parts that are easy to stop and resume") and stay
  ungraded rather than being proxied by a score. If M1 cannot reduce the chosen
  clauses to a decision rule, `not gradable` is the honest result for this row.

- **The external stratum is one-time research, read in temp and anonymized**
  (owner decision, 2026-09-03). Candidate repositories are read from a temporary
  location, never vendored into this tree, and named generically in every
  artifact. The unit under test is still *our* selected rule, run in a different
  repository, because sampling their native rules would measure a different
  thing.
  **It is deliberately not reproducible, and that is the point.** Nothing is
  pinned, no snapshot is stored, and no licence apparatus is needed: reading a
  public repository is not redistribution, and storing one is what would have
  been. This drops the vendoring precedent, the provenance file, and the
  byte-identity test that a pinned corpus would have required.
  **The durable artifact is a synthetic corpus derived from the learnings**, not
  the external repositories. What survives M4 is a corpus we author and own,
  which is storable, runnable, and reproducible — and which satisfies the rule
  below, because the learnings shape *tasks* while the rules under test remain
  ours.
  **The two strata therefore carry different epistemic standards**, and this is
  the reason they are never blended: the local stratum's per-rule verdicts are
  consumed as decision inputs by A4, A5 and B2, so they must be reproducible,
  while **no sibling slice reads the external result**. Applying the local bar
  to exploratory research would reject it for failing a requirement it never
  had.
- **Synthetic material enters as tasks, not as rules.** Seeded tasks and
  known-compliant / known-violating artifacts under the named rules give
  verifier sensitivity and counterexamples. A synthetic *rule* cannot tell us
  whether a recorded rule binds.
- **The harness extension.** `docs/specs/pack-activation-evals/` is Shipped and
  its Phase 3 already runs a skill on a seeded prompt and grades post-conditions
  the runner re-derives. What it does not measure is whether an author who had a
  rule in context then followed it.
- **A rule-level corpus surface**, because the harness's unit is a skill: every
  eval home sits at `packs/*/.apm/skills/*/evals/`, and the runner hard-codes
  both `[pack.evals].skills` as the coverage unit and that path. Half the local
  stratum is root-context — cognitive-load routes from `AGENT_RULES.md`, the
  razor's rung lives in root `AGENTS.md` — and fabricating skills to host them
  would change the context being measured. So the corpus gets its own home while
  the runner and grader, which are one module, are extended rather than
  duplicated.
- **Generated evals rather than scavenged history**, because a past review
  report does not record which rules were in the author's context, so a rule's
  firing cannot be recovered from it. Not because the artifacts are missing:
  116 tracked files match `docs/specs/*/notes/` with `review` in the path, and
  none is ignored. What *is* machine-local is narrower — the loop's recorded
  verdicts (`docs/specs/**/state.json`, `engine-state.json`, `.loop-run/`) and
  implementer reports (`docs/specs/**/notes/implementer-*.md`).
- **The report**, applying the pre-registered decision rule to the run and
  keeping the two strata separate.

**Non-goals**

- Rewriting the cognitive-load or cut-before-adding rules. The question is why
  they do not activate, not whether they are well written.
- Shipping any rubric, gate, anchor, worker, or authoring instruction. Those
  belong to the two sibling briefs and wait on this report.
- Changing the review lens or how findings are adjudicated.

## Constraints / Appetite

### Current appetite

As of 2026-09-02, activation is the
expensive part and it gates the rest. If the
measurement says written guidance does not bind, the sibling deliverables
become machinery — and machinery leaves those briefs until an approved
amendment sets its appetite. The amendment rule is for what this measurement
*converts*, not for a half that was mechanical from the outset.

### Unconfirmed portability appetite

The portable estimand enlarges that appetite, and the enlargement is not yet
appetited. "First and alone" applies to the local measurement. The
external stratum adds repository selection and
per-repository setup, and it is the slice no sibling waits on. The cut below
keeps that separable: **the local stratum alone unblocks A and B**, so the
portability work can be re-appetited, deferred, or dropped without stranding
either sibling. Confirm the enlarged appetite before M4 is confirmed.

### Activation contract

The activation contract is defined here and cited by both siblings. Every
rule any of the three briefs ships carries three things:

1. an **activation point** — the moment something changes if the rule is
   ignored, not the file it is written in;
2. a **measurement** — how to tell activation from presence, on artifacts the
   author wrote; and
3. a **stated failure mode** when it does not activate.

A rule that silently does nothing is worse than an absent one.

## What is already known not to activate

The findings corpus and its exhibits are owned by
[`agent-authoring-input-quality.md`](agent-authoring-input-quality.md)
§ "What actually works, and what does not". The consequence for this
measurement is the only thing restated here: a rule can be shipped, tested and
complied with while still doing nothing, which is why presence is not the
measurement.

### Scope is not the variable

An artifact clause reaches an authoring skill by two independent routes at once:
the `always` row in root `AGENT_RULES.md`, and the block injected into
`packs/core/.apm/skills/author-delivery-brief/SKILL.md:37`. Artifacts produced
under it breached it anyway, so **delivery scope does not explain the failure**
and this measurement must vary something else. The exhibit and its measurements
are owned by
[`agent-authoring-input-quality.md`](agent-authoring-input-quality.md); the
consequence for the design is that a per-skill route and a global rule fail
alike, which is why the ablation varies the rule rather than its delivery path.

### Enforcement boundary

Enforcement exists for some of these and is scoped elsewhere: the
cognitive-load gates read the packs, root guidance, seeds, and changelog, and
the progressive-disclosure lint has a case asserting an authored spec is *not*
in its results. Authored artifacts sit outside the enforcement boundary by
design, which is the gap this measurement reads.

## Proposed slices

None is confirmed and no spec is authored. Slice sizes use the targets owned by
[`agent-authoring-input-quality.md`](agent-authoring-input-quality.md)
§ "Sizing discipline".

| # | Slice | Owning surface | Guide | AC ceiling | Gating |
| --- | --- | --- | --- | --- | --- |
| M1 | The corpus contract: the six-rule floor with one selected variant each, external selection and pinning, the stratification rule, and the pre-registered decision rule | `docs/product/research/guidance-activation-methodology.md` | none — ships no capability | 8 | none |
| M2a | The rule-corpus contract and its validator | `docs/product/research/guidance-activation-corpus/` plus a validator that does not require `skill_name` | none — ships no adopter-facing capability | 8 | after M1 |
| M2b | The rule-level runner mode, local stratum | a rule-level mode on `pack_evals.py`, reached through the existing `agentbundle pack evals run` surface | `guides/_shared/how-to/author-a-skill.md` | 10 | after M2a and `policy-arrival-validator` V1 — the validator is the compliance baseline this ablation measures against |
| M3 | Local run and report | `docs/product/research/guidance-activation-report.md` | none — ships no capability | 6 | after M2b |
| M4a | External selection and acquisition: candidate choice, the anonymization rule, and the temp read path | the selection rule in the methodology | `guides/_shared/how-to/author-a-skill.md` | 6 | after M3; **appetite not yet confirmed** |
| M4b | External execution, the synthetic corpus derived from the learnings, and the report's external section | the synthetic corpus and M3's report | `guides/_shared/how-to/author-a-skill.md` | 8 | after M4a |

### M2 seam

Measured 2026-09-02:

- **The runner and grader do not split.** They are one module and one public CLI
  surface (`agentbundle pack evals run`), with `grade_behavior`, `grade_judge`
  and mode dispatch as separate internal functions. M2b extends that one
  surface rather than creating a second.
- **The corpus and the runner do split.** No existing validator fits: the
  current one requires `skill_name` and confines fixtures beneath a skill
  directory, and eval discovery only looks inside skill directories. A
  rule-level corpus therefore needs its own contract and validator, which is a
  distinct surface from a runner mode — so M2a ships first and M2b reads it.

### M2b execution context

M2b requires new execution machinery. The existing activation detector
observes only the `Skill` tool event, and the
temporary projection it builds contains just the one pack's projected skills —
it never establishes the repository-root `AGENTS.md` plus `AGENT_RULES.md`
routing context that half the floor lives in. Executing a root-context rule is
**new execution machinery**, and that is the honest size of M2b.

### M4 sampled unit

M4 measures this repository's rules elsewhere, not other repositories' rules.
Rules native to adopter repositories would estimate whether written
guidance works across a population, not whether **our** six rules travel. M4
therefore reads the selected local rules against anonymized adopter repositories in temp and
measures them there.

### Destinations

The destinations fit their contract. Measured 2026-09-02,
`docs/product/research/`
imposes no mechanical contract on a new file — measured: no frontmatter, no
discipline line, no index or README to update, and no verifier reads that tree
for content — so it hosts a methodology and a report without ceremony.

Rejected: a `docs/specs/<feature>/` home. It would place M1's decision rule
inside the spec that implements M2b, which is the co-location the top-ranked
risk below forbids. Also rejected as a precedent claim: the
`architecture-assessment-*` trio does not hold "a methodology, its corpus and
the report over it" — its survey is desk research and its corpus is source
packets. The per-item-verdict precedent is
`docs/specs/bug-fix-systematic-debugging/notes/manual-invocation.md`.
`architecture-assessment-intents-survey.md` is a desk-research synthesis
answering a research question, and `architecture-assessment-corpus/` is living
maintenance evidence of source packets — not results produced by running the
methodology over the corpus. The real per-item-verdict precedent is
`docs/specs/bug-fix-systematic-debugging/notes/manual-invocation.md`, one row
per criterion with observed evidence and a verdict. A `docs/specs/<feature>/`
home would put M1's decision rule inside the spec that implements M2, which is
the co-location the top-ranked risk below forbids.

### M1 verification

M1's verification binds a revision to a run. A methodology document cannot
be verified by reading it — that is the "do not verify guidance by parsing the
guidance" rabbit hole. **M1 lands as its own revision-bound reviewed
change; every M2b run records the exact M1 revision it executed under; and M3
cites that same immutable run evidence.** Ordering alone is insufficient: a
commit proves sequence, not that the decision rule was reviewed before it ran.
So the check also names **an independently recorded review result bound to that
immutable M1 revision** — the same revision-bound form this repository already
requires of a shaping verdict — and a run whose recorded M1 revision carries no
such result is not a valid run. A post-run revision to the decision
rule then appears as a new reviewed M1 against a different revision, which is
visible rather than inferred, instead of an edit inside M3.

The ceiling and stall-threshold semantics come from that same sizing section.

### Slice relationships

- **M1 is not over-split.** It carries no code, and the over-splitting floor
  (below) warns against slices that small. It is separate for a correctness
  reason that outranks the size heuristic: **the decision rule has to land as its
  own reviewed change before M2b runs anything.** Folding M1 into M2a would not
  preserve that — the Phase 3 plan validates its grader live on a covered skill
  while that slice is being built, so M2 produces results as it is written, and a
  decision rule sharing that change can be tuned to them.

- **M2a and M2b are two slices.** The corpus needs its own contract and validator
  because no existing one fits, while the runner and grader are one surface. The
  sizing reason for that cut is the same one cited above.

- **M3 applies M1's rule and does not restate or amend it.** A revision to the
  decision rule after M2b has run is a new M1, reviewed as one, against a
  different M1 revision.

- **M3's report owns both strata's sections, and M4 amends it.** M3 runs the local
  stratum only, but the success metric requires both strata reported separately —
  so M3 creates the report with its external section reserved and explicitly not
  run, and M4 fills that section in the same file. Without this, no slice owns the
  external half of the report and the "reported separately" metric has no owning
  surface. **No figure in the report combines the two.**

## Assumptions / Risks

- **The decision rule gets written to fit the result.** The most likely
  failure. Guard: M1 lands as its own reviewed change before M2b runs anything.
- **The harness measures the eval rather than the author.** A generated eval
  can be satisfied by a runner that re-derives the post-condition without any
  author ever following the rule. Each graded post-condition names the authored
  artifact it reads.
- **The report is inconclusive.** "Some rules bind, some do not" is a real
  outcome and the per-rule verdict metric is what makes it usable rather than a
  reason to re-run.
- **This brief ships an unactivated measurement.** The measurement is itself
  written guidance, so it cannot escape by claiming a report exists — "the
  artifact is present" is the very conflation the Outcome condemns, and it
  cannot see the failure ranked most likely above. The escape is external and
  git-observable instead: M1's decision rule is committed and reviewed **before
  M2b runs anything**, and any post-run revision to it appears as a new reviewed
  M1 rather than an edit inside M3.

## Ready gaps (Draft only)

- Ready needs a revision-bound clean shaping review of this brief plus the
  owner's explicit confirmation. Neither has happened for the split.
- **M1's and M3's destinations are defined.** M1 is
  `docs/product/research/guidance-activation-methodology.md`, M2a's corpus is
  `docs/product/research/guidance-activation-corpus/`, and M3 is
  `docs/product/research/guidance-activation-report.md`. The per-item-verdict
  precedent is `docs/specs/bug-fix-systematic-debugging/notes/manual-invocation.md`.
  M1's
  verification is the git-observable ordering recorded in § "Proposed slices",
  not a read of its own text.
- **The guide shippability test is defined.** Applied per slice that
  changes adopter-visible behaviour: M2b and M4 extend
  `guides/_shared/how-to/author-a-skill.md`, which
  `docs/specs/pack-activation-evals/spec.md:225` already names as the guide for
  writing and running these evals. M1 and M3 ship a report rather than a
  capability, so the rule's own scoping to "the capability the phase
  introduces" leaves them out.
- **The enlarged appetite for the portable estimand is unconfirmed.** Placing
  local rules against anonymized
adopter repositories is exploratory research rather than a reproducible
  measurement. M4 cannot be confirmed until the appetite is confirmed. M1–M3
  are unaffected, and the local stratum alone unblocks A and B.
- **Dispositioned — candidates are surfaced at M4 confirmation** with the
  selection reasoning, for owner review. Choosing them needs a public-repository
  survey, so it cannot happen in this repository.

  Selecting them needs a public-repository survey, which requires network
  access the spike did not have, plus an owner-approved selection rule.
- **`docs/specs/pack-activation-evals/spec.md` names a runner that no longer
  exists** — `tools/run-pack-evals.py`, in a ticked criterion at `:207` and in
  the guide requirement at `:225`; the CLI now lives in
  `packages/agentbundle/agentbundle/commands/pack_evals.py`. M2b extends that
  module, so it will read a shipped contract whose path is stale. Not this
  brief's to fix, but it should not be discovered mid-slice.

## Rabbit holes

- **Do not verify guidance by parsing the guidance.** A check that a sentence
  exists in a file proves presence, which is the thing already known.
- **Do not scavenge past review artifacts.** They are gitignored and
  machine-local, so a result read from them is not reproducible by anyone else.
- **Do not grow the corpus to make a verdict come out.** A rule with no
  decision rule is dropped and recorded, not graded loosely.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Source: repository origin. The split provenance is owned by
  [`agent-authoring-input-quality.md`](agent-authoring-input-quality.md)
  § "Provenance".
