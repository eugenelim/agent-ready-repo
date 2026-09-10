# Work-loop repair correctness

- **Status:** Draft
- **Kind:** outcome
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** work-loop-delivery-efficiency — [Work-loop delivery efficiency](work-loop-delivery-efficiency.md)

## Outcome

- **Steerable input:** Give the repair implementer a compact closure packet containing the complete adjudicated finding set and remedy predicates for one repair event, affected contract and paths, touched-path repository obligations, unresolved owner-only decisions that must stop the repair, and the smallest targeted verifiers required before return.
- **Lagging outcome:** Sustained findings are closed with fewer repair-induced defects, repeated review-and-repair cycles, model tokens, and elapsed time because predictable obligations are satisfied during the repair rather than rediscovered afterward.
- **Guardrail:** The packet does not narrow accepted requirements, authorize owner decisions, replace applicable repository gates, constrain evidence-seeking outside the packet, or hide newly observed defects. Candidate repairs must close every original finding in the repair event and introduce no additional protected-class, Blocker, or High-severity defect relative to the current repair path.

## Opportunity

- **Functional job:** Apply an adjudicated repair once, prove the named defect is closed, and avoid breaking a nearby contract or repository obligation in the process.
- **Emotional job:** Trust that a repair request is bounded and executable rather than the beginning of another open-ended review cycle.
- **Social job:** Give reviewers and maintainers evidence that a repair is complete without asking them to rediscover mechanical obligations or reconstruct the requested remedy.
- **Struggling moment:** A reviewer sustains a valid finding, but the repair implementer receives incomplete closure context or does not activate the repository rules implied by the touched paths. The six-case economics spike recorded 28 repair-induced sustained findings—24 baseline and 4 candidate—and found 22 of 67 sustained findings in deterministic repository conventions. Some of that evidence came from experimental repairs that were forbidden from running the full gate suite, so it identifies a costly failure class but does not yet prove that a richer repair packet has marginal benefit over the repository's real current path.

## Boundary

- Includes closure-packet preparation, repair dispatch after adjudication, remedy and closure-predicate fidelity, touched-path obligation selection, bounded repair scope, required targeted verification, repair-induced finding measurement, and cost from arm preparation through post-repair verdict.
- One repair event is one natural repair revision responding to one adjudicated review round. Every sustained finding answered by that revision stays in the case; findings may not be split or selected after results are visible.
- A closure packet contains only evidence already authorized by the accepted contract and effective repository guidance: the complete sustained finding set and adjudicated fixes, affected files and contract bytes, triggered projection, release, register, approval, or verification obligations, exact applicable checks, and explicit non-goals or owner-only decisions. It is additive evidence, not an assertion that no other dependency matters; the repairer may inspect beyond it and must stop on contradiction, missing authority, or an owner-only decision.
- The baseline arm uses the current implementer dispatch and all currently required gates. The candidate uses that same baseline plus the closure packet. Both start from the same pre-repair tree and accepted finding set, use the same model and permissions, and receive the same broad post-repair review and adjudication.
- Excludes upstream spec and plan authoring, deciding what to do when the accepted contract itself is wrong, changing reviewer or adjudicator semantics, focused re-review policy, general gate scheduling, new state machinery, and adding new repository conventions.
- This is distinct from `agent-authoring-input-quality`, which prevents bad contracts before implementation, and `agent-loop-escalation-recovery`, which routes discoveries that invalidate an upstream artifact. This child begins only after a finding and its repair authority are valid.
- The validation probe may hand-author closure packets from existing guidance. It does not build an obligation-discovery engine or change shipped repair policy.

## Owner

- eugenelim, Platform Core maintainer.

## Assumptions

- A material share of repair-induced defects comes from missing or ambiguous repair inputs rather than irreducible implementation difficulty.
- Applicable touched-path obligations can be selected into a compact packet without loading every repository rule or adding comparable authoring cost.
- An explicit closure predicate and targeted verifier reduce both failure to close the original finding and collateral defects.
- The candidate's added prompt and verification cost is repaid by avoiding later adjudication, repair, and re-review work.
- The prior spike is directional evidence only: its repairs did not run the repository's full gate suite and projections were synchronized by hand, so this experiment must compare against the real current implementer path rather than that weakened baseline.
- External repair and error-localization studies support supplying known location and remedy evidence, while patch-assessment research shows that a passing targeted test cannot certify the whole repair. The [agentic loop effectiveness survey](../research/agentic-loop-effectiveness-survey.md#2-repair-packets-have-evidence-but-verification-remains-independent) owns that evidence and its transfer limits.

## De-risking

- **Door:** Two-way. Closure packets can be tested in disposable worktrees and discarded without changing shipped repair behavior.
- **Approach:** `validate-first`, overriding the two-way-door default because an incorrect repair can create a material defect and the mechanism must show marginal value over current required gates.
- **What would have to be true:** Both arms must start from identical pre-repair bytes and the same complete adjudicated finding set; the baseline must receive the repository's real current implementer context and gates; the packet must be compact, additive, and derivable from existing authority; the candidate must close every original finding, introduce fewer defects, and reduce total closure cost rather than merely moving work into packet preparation.
- **Riskiest assumption:** A compact, obligation-aware closure packet plus targeted verification materially reduces repair-induced defects and total repair-to-verdict cost beyond the real current implementer contract and gates.
- **Kill condition (predeclared 2026-09-09):** Kill or reshape if the candidate fails to close every original finding in any case; introduces any independently adjudicated candidate-only protected-class, Blocker, or High-severity cluster; fails to reduce repair-induced sustained clusters by at least 50% when the baseline produces two or more, or the baseline produces fewer than two and therefore demonstrates no material opportunity in the corpus; fails to reduce median model tokens from arm preparation through terminal verdict or the two-cycle cap by at least 20% across the three non-high-risk cases; or fails to reduce median uncontaminated elapsed time over that interval by at least 15%.
- **Measurement accounting:** The deciding token and elapsed intervals begin when either arm starts preparing its dispatch context and end at terminal verdict or the two-cycle cap. Record packet construction, repair, gates, review, adjudication, and further cycles separately so preparation cost cannot disappear. Also report total critical-path elapsed time with permission wait and model or queue stall split out; this operational clock does not replace the predeclared uncontaminated threshold.
- **Measurement admissibility:** Both arms must run every current gate applicable to the repair; a case is inadmissible if the experiment forbids, hand-simulates, or silently skips one. The targeted verifier must fail on the frozen pre-repair revision and pass on the repair when an executable oracle exists; document or contract cases need a deterministic before/after predicate. Elapsed time is uncontaminated only when neither arm records a human permission wait and model or queue stall is no more than 10% of elapsed time. Re-run one contaminated case once on a quiet host; persistent contamination leaves the wall-clock clause unmeasured and the intent cannot survive.
- **Corpus:** Preselect four natural repair events before either arm runs: one low-risk, two ordinary, and one high-risk. Preserve all sustained findings from the adjudicated review round answered by each natural repair revision. Include two events whose repairs trigger projection, release, register, approval, or verification obligations and two whose repairs change logic or an executable control. Each case preserves the accepted contract, adjudication, pre-repair revision, applicable gates, and usable timing and provider-token telemetry. Do not split an event or replace a case after seeing a result.
- **Activity:** Run baseline and candidate repairs from the same frozen pre-repair revision and complete finding set with arm order alternated. After each repair, run the same current gates, broad reviewer, and adjudicator. Permit at most one further repair-and-review cycle per arm, stopping earlier on a terminal verdict. Blind arm identity, independently adjudicate and cluster repair-induced findings, and compare closure of every original finding, new defects, preparation and execution tokens, admissible elapsed time, and total critical-path time. Stop immediately on a candidate-only protected-class, Blocker, or High defect; otherwise run all four cases.
- **Status:** Run 2026-09-09/10; killed on the immediate-stop safety clause after two of four cases.
  Evidence in [the spike record](../research/work-loop-repair-correctness-spike.md).

## Validation result (2026-09-10)

**Verdict: killed.** The deciding clause is the Activity clause's immediate stop — *"Stop
immediately on a candidate-only protected-class, Blocker, or High defect."* On P2, four
candidate-only repair-induced clusters qualified on severity alone: `C-W2-AC16-PROSE-BROKEN`
(Blocker, public contract — a rewritten sentence broke the roster gate pinning a Shipped spec's
AC16), `C-W2-NOW-PAGE-OVERCLAIM` (High, public contract), `C-W2-NEW-TOPLEVEL-DIR` (High, human
approval) and `C-W2-INVALID-VERDICT-RECORD` (High, human approval — a `review-verdict.v1` block
carrying 2 of 12 required keys, so both Nit deferrals are refused). Two further candidate-only
repair-induced Concerns carry a `public-contract` class and would qualify under the clause's
protected-class limb; that reading is left to the owner. Each was ruled by an independent
adjudicator blind to arm identity, against the pre-repair tree.

P3 and P4 were **not run**. That is the frozen protocol, not a truncation: the Activity clause
directs an immediate stop, and it fired.

**Repair-induced clusters went up, not down:** baseline 4 → candidate 6, a 50% increase where the
clause requires a 50% reduction.

**The cost clauses are UNMEASURED**, not failed. Both require a median across three non-high-risk
cases and only two cases executed. Directionally the candidate was worse in both — 2.37% on P1,
43.7% on P2 — but that is evidence, not a verdict, and it is not treated as a second deciding
clause. Elapsed time is separately unmeasured: both cases breached the 10% stall ceiling on a host
carrying concurrent peer workloads, with zero permission wait and one agent at a time.

**Assumptions falsified.** The third assumption fails: an explicit closure predicate and targeted
verifier did not reduce collateral defects — they rose. The fourth fails with it: the added
preparation cost was not repaid. The first is untouched either way, because the mechanism's
failures were not missing inputs.

**Assumptions that survived.** The second held in part: touched-path obligations *can* be selected
into a compact packet without loading every rule — the packets ran 16–29 KB and their premises were
independently re-measured rather than asserted. And on P2 the packet did produce the killing control
the baseline's first repair lacked. Neither survives into a delivery case on its own.

**What is killed is the packet as designed, across the two executed cases.** The mechanism failed in
exactly the area it was meant to improve: it supplied obligations and still induced public-contract
and approval violations. The bundle's breadth is what widened the repair surface, and the widened
surface is where the violations occurred.

**What is not killed** is a narrower mechanism carrying only the frozen adjudicated closure
predicate, exact repair authority and non-goals, one killing control, and no obligation bundle or
expanded repair surface. Nothing measured here speaks against that shape.

**Method limitations.** The blind adjudicator was instructed to run gates it has no tools to run;
it reported the constraint and settled 13 of 14 findings by reading, and the controller had already
executed both gate claims independently. Future adjudicator briefs must supply already-executed gate
and ancestry evidence, never ask the read-only adjudicator to produce it. Separately, the
controller made the arms' cycle-2 deferral-destination wording asymmetric in the baseline's favour
after seeing a candidate failure; that comparison is excluded. P2's first baseline arm copied the
historical repair, was voided and re-run.

```yaml
validation_hook:
  assumption: An obligation-aware closure packet plus targeted verification reduces repair-induced defects and total preparation-to-verdict cost beyond the real current implementer path.
  kill_condition: Kill or reshape if the candidate fails to close every original finding, adds any protected-class/Blocker/High cluster, does not cut repair-induced sustained clusters by at least 50%, or misses the 20% token or 15% uncontaminated elapsed-time bars.
  activity: Preselect four natural repair events without splitting their adjudicated finding sets, run current and closure-packet repairs from identical pre-repair bytes through a maximum of two repair-review cycles, independently adjudicate the blinded outputs, and compare closure, induced defects, preparation and execution tokens, and elapsed time.
  status: run 2026-09-09/10; killed on the immediate-stop safety clause after two of four cases. Four candidate-only repair-induced clusters (1 Blocker, 3 High; public-contract and human-approval) where the clause requires none, and repair-induced clusters rose 4 -> 6. The token and elapsed clauses are unmeasured, needing a median over three non-high-risk cases. Evidence in docs/product/research/work-loop-repair-correctness-spike.md
```

## Projection

- The hook was killed, so no delivery brief is projected from this intent as shaped. The
  immediate-stop safety clause decided it; the cost clauses are unmeasured and are not an
  independent basis. The [spike record](../research/work-loop-repair-correctness-spike.md#survivekill-the-immediate-stop-rule-fired)
  holds the calculation.
- A reshape is not foreclosed, and its shape is constrained by what failed. The packet's *breadth*
  widened the repair surface, and the widened surface is where the public-contract and
  human-approval violations occurred. A narrower successor would carry only the frozen adjudicated
  closure predicate, exact repair authority and non-goals, and one killing control — no obligation
  bundle, no expanded repair surface. That is a new hypothesis needing its own predeclared test,
  not a reinterpretation of this one.
- Before any such reshape, the parent should run the deterministic
  [repair provability audit](../research/repair-provability-audit-design.md): 113 natural repair
  commits, zero model calls, measuring how often a shipped repair carries a control that fails when
  the repair is reversed. Both arms here produced unfalsifiable fixes, so the base rate of that
  defect is the prerequisite measurement — and it is two orders of magnitude cheaper than this
  spike.
- The touched-path convention subset should compose with, not duplicate, `agent-authoring-input-quality`: that brief remains responsible for spec and plan authoring, while this child owns only post-adjudication repair inputs.
- Focused re-review remains an independent sibling. This experiment uses the current broad post-repair review in both arms so its result does not depend on whether focused re-review later survives.

## Source

- Mode: repo-origin
- Locator: docs/product/intents/work-loop-delivery-efficiency.md
- Revision: sha256-bytes-v1:1ba9dc16641283eb1b72d4cad80f0f9700124b68a71afb0001f466fafbbb47d1
- Authority: repo-origin
