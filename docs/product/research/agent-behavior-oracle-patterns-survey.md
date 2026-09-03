# Oracle designs for non-deterministic behavioral policies

> Discipline: applied (practitioner and peer-reviewed survey)

Commissioned 2026-09-02 for the `cross-adapter-behavior-enforcement` brief. Independent desk research; findings are cited to their sources and labelled by evidence class. Retained so the briefs can cite it rather than restate it.

---

# Prior art: oracle designs for non-deterministic behavioral and stylistic policies

The strongest conclusion is simple: no oracle becomes trustworthy merely because it returns `PASS` or `FAIL`. For an otherwise subjective policy, a blocking oracle needs an independently defined construct, evidence that it recognizes both compliant and violating cases, measured false-block and missed-violation rates, and proof that the check itself actually runs.

For the specific question “did this rule bind?”, outcome inspection is insufficient. The closest valid design is a randomized, paired ablation over a challenge set, backed by a calibrated policy-specific outcome measure. Even that establishes a population-level causal effect, not that the rule influenced any single output.

Source labels below distinguish peer-reviewed work from preprints and practitioner documentation.

## Summary by oracle pattern

| Oracle pattern | What it can establish | Binary gate? | Cost | Evidence |
|---|---|---:|---:|---|
| Formal or executable property | Artifact satisfies a specified predicate | Yes | Low–medium | High |
| Metamorphic relation | Related runs obey an expected relation | Yes, sometimes statistical | Medium | High |
| Differential or pseudo-oracle | Implementations or judges agree | Disagreement only; not correctness | Medium–high | High |
| Guidance ablation | Adding the rule causally changes measured behavior | Yes, at suite level | High | Moderate |
| Dedicated per-policy validator | One named policy was violated | Yes, after validation | Medium | Moderate |
| LLM-as-judge | Rubric-defined semantic compliance | Yes, conditionally | Medium plus high setup | Moderate |
| Human oracle | Human experts accept or reject | Yes | High | High, if labels are reliable |
| Process/step oracle | Observable steps or trace obey policy | Yes for observable steps | High | Moderate, domain-limited |
| Runtime monitor | Execution trace remains within a specification | Yes | Medium | High for formal properties |
| Critique/revise or self-consistency | A second pass or consensus prefers an answer | Not safely by itself | Medium–high | Mixed |
| Mutation oracle | The validator detects controlled policy violations | Yes; validates the validator | Medium–high | High |
| Linter/warning oracle | A recognizable pattern should be corrected | Yes only at high precision | Low–medium | High for developer tooling |

## 1. Specified properties and property-based testing

A specified oracle turns the policy into an executable predicate. Property-based testing then supplies many generated inputs; the property, not the generator, remains the oracle. QuickCheck established this separation: users formulate properties and the system generates and shrinks counterexamples ([Claessen and Hughes, *QuickCheck*, ICFP 2000](https://research.chalmers.se/en/publication/237427), peer-reviewed).

What it needs:

- A precise observable: section count, repeated semantic proposition, reading level, prohibited operation, required source evidence.
- A definition of equivalence where surface wording varies.
- Generators that exercise boundary and adversarial cases.
- A reviewed mapping from the prose policy to the predicate.

Failure modes:

- The executable property is only a proxy for the intended style.
- Goodharting: authors satisfy the metric while defeating the purpose.
- Generator blind spots.
- Threshold disputes and unstable semantic clustering.
- A “property-based” test without a real property merely generates more unjudgeable outputs.

Cost is low once the predicate exists, but formalizing a subjective policy can be expensive. It yields a clean binary verdict and is the best blocking option when possible.

Barr et al.’s test-oracle taxonomy puts this under “specified oracles.” The other categories are derived oracles, implicit failure signals, and cases where no automated oracle exists and human effort can only be reduced ([*The Oracle Problem in Software Testing: A Survey*, IEEE TSE 2015](https://discovery.ucl.ac.uk/id/eprint/1471263/), peer-reviewed).

## 2. Metamorphic oracles

Metamorphic testing avoids requiring the exact correct output. It states a relation that must hold across related executions. For example:

- Reordering irrelevant source material must not change which claims are selected.
- Paraphrasing the policy must not materially change compliance.
- Duplicating a fact in the input must not cause duplicate summary claims.
- Tightening “at most two” to “at most one” must not increase the measured count.
- Removing irrelevant guidance should not change the target behavior.

The established definition is a relation across multiple executions of one implementation. The main research challenge is discovering sound metamorphic relations; stochastic systems may require statistical rather than equality-based relations ([Segura et al., *A Survey on Metamorphic Testing*, IEEE TSE 2016](https://www.isa.us.es/publications/type/article-journal/2016/survey-metamorphic-testing), peer-reviewed; [Barr et al.](https://philmcminn.com/publications/barr2015.pdf), peer-reviewed).

What it needs:

- A transformation known not to change, or known predictably to change, the intended answer.
- A measurable relation between outputs.
- Repeated samples and a statistical tolerance for stochastic models.

Failure modes:

- A plausible but false relation.
- Two outputs that differ harmlessly at the surface.
- Both executions violating the policy in the same way.
- Large sampling requirements for small behavioral effects.

It can produce a binary gate. For stochastic generation, the binary is normally “the estimated violation exceeds a predeclared limit” rather than “one pair differs.”

## 3. Differential testing, back-to-back testing, and pseudo-oracles

Differential testing presents the same cases to comparable systems and flags disagreement. A pseudo-oracle is an independently produced alternative implementation. Neither requires knowing the exact answer beforehand ([McKeeman, *Differential Testing for Software*, Digital Technical Journal 1998](https://vmssoftware.com/docs/dtj-v10-01-1998.pdf), practitioner research journal; [Barr et al.](https://philmcminn.com/publications/barr2015.pdf), peer-reviewed).

For agent guidance, comparators could include:

- Different model families.
- A model and a human reviewer.
- A general judge and a policy-specific classifier.
- Independent rubric implementations.
- The current guidance and a known-good previous version.

What it needs:

- Genuine implementation diversity.
- Output normalization that preserves material differences.
- Adjudication for disagreements.

Failure modes:

- Shared training data and correlated blind spots.
- Both systems being wrong.
- Multiple valid stylistic outputs.
- Treating majority vote as truth.
- A “different” judge that is another checkpoint from the same model family.

It yields a reliable binary for “disagreement occurred,” not for “the artifact is wrong.” A blocker therefore needs an adjudication rule or a trusted tie-breaker.

## 4. Guidance ablation as a causal oracle

This is the most direct pattern for determining whether a rule contributes behavior:

\[
\text{effect of rule} =
\Pr(\text{violation}\mid\text{without rule})
-
\Pr(\text{violation}\mid\text{with rule})
\]

The valid experiment is not one before/after output. It is a randomized, repeated comparison over tasks selected to make the policy consequential.

What it needs:

1. A frozen model, decoding configuration, surrounding prompt, tools, and evaluator.
2. A task set with room for the control to fail; otherwise ceiling effects hide the rule.
3. Treatment and control prompts differing only in the rule.
4. Preferably a length-matched placebo control, since deleting text also changes attention and context position.
5. A predeclared policy-specific outcome measure.
6. Multiple samples per task when generation is stochastic.
7. Paired analysis: McNemar’s test for paired binary outcomes, or a hierarchical model when tasks and repetitions both vary.
8. A minimum effect size, not merely statistical significance.
9. A non-inferiority check on unrelated quality dimensions, since a rule can “work” by damaging the whole answer.

The literature does support counterfactual prompt interventions as the identification strategy for prompt influence, but it does not yet provide a mature, standardized “instruction-binding oracle” for arbitrary prose rules:

- Webson and Pavlick found that irrelevant or misleading prompts could perform as well as instructive prompts, showing why satisfactory output does not prove instruction use ([NAACL 2022](https://aclanthology.org/2022.naacl-main.167/), peer-reviewed).
- Prompt-sensitivity work compares controlled prompt variants, although later results warn that rigid output metrics can manufacture apparent sensitivity ([Hua et al., EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1006/), peer-reviewed).
- Anthropic’s recent CHIVE work explicitly treats counterfactual prompt edits and their measured outcomes as evidence, while refusing to treat a model-generated explanation as ground truth ([*Would This Change Your Answer?*, 2026](https://alignment.anthropic.com/2026/chive/), practitioner research, not yet established peer-reviewed prior art).
- IFEval largely sidesteps the subjective-oracle problem by selecting mechanically verifiable instructions ([Zhou et al., *Instruction-Following Evaluation for Large Language Models*](https://arxiv.org/abs/2311.07911), preprint).

Ablation failure modes:

- **Ceiling:** both conditions comply because the behavior is already learned.
- **Floor:** neither condition can perform the task.
- **Low power:** the challenge set rarely activates the rule.
- **Prompt spillover:** removal changes context length, placement, or salience.
- **Evaluator blindness:** the rule changes behavior that the metric does not capture.
- **Evaluator leakage:** a judge shown the treatment condition rationalizes that the rule worked.
- **Overfitting:** the rule was tuned on the same challenge cases.
- **Interaction effects:** the rule only works in combination with another clause.

Binary verdict: yes, at suite level. A defensible gate is:

> Block if the lower confidence bound on the rule’s improvement is below the minimum useful effect, or if the rule causes a predeclared unacceptable regression.

That gate answers “this rule has not demonstrated incremental behavioral value on the tested distribution.” It does not prove the rule failed to affect a particular artifact.

## 5. Per-policy validators and policy-as-code

OPA/Rego represents policies as separately versioned, executable decisions over structured input. Conftest applies those assertions to configuration artifacts ([OPA documentation](https://www.openpolicyagent.org/docs), official practitioner documentation; [Conftest](https://github.com/open-policy-agent/conftest), official project documentation).

Guardrails AI uses the same modular shape for LLM output: each validator returns `PassResult` or `FailResult`, with a validator-specific failure action ([validator documentation](https://guardrailsai.com/guardrails/docs/concepts/validators), vendor documentation). NeMo Guardrails composes checks at input, retrieval, dialog, tool-execution, and output stages ([NeMo architecture](https://docs.nvidia.com/nemo/guardrails/about-nemo-guardrails-library/how-it-works), vendor documentation; its programmable-rails paper appeared as an [EMNLP 2023 system demonstration](https://aclanthology.org/2023.emnlp-demo.40.pdf), peer-reviewed demonstration paper).

The advantage of one validator per policy is primarily operational:

- Each policy has its own confusion matrix and owner.
- A failure identifies the clause that fired.
- Policies can be enabled, calibrated, or retired separately.
- Different oracle types can coexist: deterministic checks first, learned checks only where necessary.
- Mutation cases can target one policy.
- Changes in one rubric do not silently redefine all other verdicts.

Evidence that it is always more accurate than a global reviewer is weak:

- EvalLM found that application-specific criteria produced 0.713 agreement and Fleiss’ κ of 0.485 with humans, versus 0.699 and κ 0.430 for overall-quality judgments. This is supportive but modest and task-specific ([Kim et al., CHI 2024](https://doi.org/10.1145/3613904.3642216), peer-reviewed).
- The same study observed that equal weighting of separate criteria can be wrong when one criterion should dominate.
- A 2026 prompt-controlled preprint found matched holistic judging equal or better than self-decomposing atomic judging on two of three reference-grounded QA benchmarks. Its scope does not cover independently implemented per-policy validators, but it is a useful counterexample to “decomposition always wins” ([Zhang, arXiv:2603.28005](https://arxiv.org/abs/2603.28005), preprint).

### False-positive accumulation

If a build fails when any of \(m\) independent validators falsely fires, the family-wise false-block probability is:

\[
1-(1-\alpha)^m
\]

For 132 validators:

- At 1% false-positive probability each: about **73.5%** chance of at least one false block.
- At 0.1% each: about **12.4%**.
- To keep the total below 5% under independence, each validator needs roughly **0.039%** false-positive probability.

Independence rarely holds, so those are illustrative rather than predictive. The union bound still gives a worst-case upper bound of \(\sum \alpha_i\).

The practical answer is not one flat `AND` across every rule. Use applicability routing, severity tiers, correlated-rule consolidation, and explicit aggregation:

- Deterministic safety or contract violations: block.
- Calibrated high-confidence semantic violations: block or require review.
- Low-confidence stylistic findings: advisory.
- Multiple related validators: aggregate as one policy family.
- Abstentions and validator disagreement: human review, not automatic pass.

## 6. LLM-as-judge

An LLM judge converts a rubric into a semantic classifier or ranker. It is useful precisely where a deterministic check is unavailable, but its output is still a learned measurement instrument.

Evidence is mixed:

- GPT-4 judges achieved over 80% agreement with human preferences in MT-Bench/Chatbot Arena, comparable to reported human-human agreement, while also showing position, verbosity, self-enhancement, and reasoning biases ([Zheng et al., NeurIPS 2023 Datasets and Benchmarks](https://papers.neurips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html), peer-reviewed).
- G-Eval reached Spearman correlation 0.514 with human summary judgments and warned of preference for LLM-generated text ([Liu et al., EMNLP 2023](https://aclanthology.org/2023.emnlp-main.153/), peer-reviewed).
- Position alone can reverse pairwise results; balanced-order evaluation mitigates but does not eliminate this ([Wang et al., ACL 2024](https://aclanthology.org/2024.acl-long.511/), peer-reviewed).
- LLM evaluators recognize and favor their own generations ([Panickssery et al., NeurIPS 2024](https://papers.nips.cc/paper_files/paper/2024/hash/7f1f0218e45f5414c79c0679633e47bc-Abstract-Conference.html), peer-reviewed).
- LLMBar used 419 curated instruction-following pairs with 94% expert agreement. Some judges performed below chance on adversarial cases where a more attractive answer violated the instruction; even the best GPT-4 judge remained below experts ([Zeng et al., ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/file/afc8b034823271816d14f7c1aefe1dff-Paper-Conference.pdf), peer-reviewed).
- JudgeBench found many strong models only slightly above random guessing on challenging knowledge, reasoning, math, and coding pairs ([Tan et al., ICLR 2025](https://openreview.net/pdf?id=G0dksFayVq), peer-reviewed).

What a gating judge needs:

- One operational criterion per verdict, or a documented precedence rule.
- Positive, negative, boundary, and adversarial examples.
- References or source material when the judgment depends on facts.
- Blind model identity and blind treatment assignment.
- Pair-order swaps for comparative evaluation.
- Length- and formatting-controlled adversarial cases.
- Structured output with `pass`, `fail`, and preferably `abstain`.
- Exact offending spans or criterion evidence. This improves auditability, though the rationale is not proof.
- A pinned judge model and prompt.
- A held-out human-labelled calibration set from the actual artifact distribution.
- Revalidation after judge, generator, rubric, or artifact-distribution changes.

Metrics should include the full confusion matrix, false-block rate, missed-violation rate, and confidence intervals. Raw agreement should accompany Cohen’s κ or Krippendorff’s α; chance-corrected coefficients can behave oddly when violations are rare. Cohen’s original coefficient is documented in [*A Coefficient of Agreement for Nominal Scales*, 1960](https://doi.org/10.1177/001316446002000104), peer-reviewed.

There is no defensible universal calibration-set size or κ threshold. Size follows the tolerated error rate:

- If zero false blocks are seen in \(n\) clean examples, the approximate 95% upper bound is \(3/n\), the “rule of three” ([Hanley and Lippman-Hand, JAMA 1983](https://jamanetwork.com/journals/jama/articlepdf/385438/jama_249_13_031.pdf?resultClick=1), peer-reviewed).
- To claim an observed zero-error false-block rate is below roughly 1%, about 300 clean cases are needed.
- The same calculation applies separately to missed violations, requiring seeded or independently labelled violating cases.
- Subgroup and policy-specific claims need their own effective sample sizes.

An uncalibrated judge may be useful as an advisory reviewer. It is not evidence sufficient to block a build.

## 7. Human and hybrid oracles

When no automated oracle exists, the classical fallback is human judgment. Barr et al. treat reducing human-oracle cost as a distinct research category rather than pretending the oracle has been automated.

A blocking human oracle needs:

- A decision rubric with examples and boundary cases.
- At least two independent labels during calibration.
- Blinding to author, model, and treatment where possible.
- Agreement measurement before consensus.
- A documented adjudication path.
- Periodic relabelling to detect drift.

Failure modes include low agreement, expertise gaps, fatigue, halo effects, and consensus masking an ambiguous policy.

A strong hybrid is “machine flags, human adjudicates.” OpenAI’s critic work found model critiques could help humans find code defects, but critics also hallucinated bugs; human–machine teams hallucinated fewer bugs than critics alone ([McAleese et al., *LLM Critics Help Catch LLM Bugs*](https://arxiv.org/abs/2407.00215), preprint/industry research).

## 8. Process supervision and step-level verification

Outcome supervision scores the final result. Process supervision scores intermediate steps. On math tasks:

- Uesato et al. found similar final-answer error from pure outcome supervision with less labelling, but process feedback was needed to reduce reasoning errors among answers that happened to be correct ([*Solving Math Word Problems with Process- and Outcome-Based Feedback*](https://arxiv.org/abs/2211.14275), preprint).
- Lightman et al. found process supervision outperformed outcome supervision on MATH ([*Let’s Verify Step by Step*, ICLR 2024](https://openreview.net/pdf?id=v8L0pN6EOi), peer-reviewed).

The transfer to document policy is conditional. Step-level checks help when the policy concerns observable work:

- Each material claim has a source.
- Each identifier is resolved against a symbol table.
- Each section passes a local redundancy check before assembly.
- The agent ran the prescribed mutation or counterfactual.
- A tool action was authorized before execution.

They do not solve a subjective final-output oracle merely by asking for chain of thought. Private reasoning may be unavailable, unfaithful, or itself generated to satisfy the reviewer. Process reward models are also learned judges and require the same calibration as outcome judges.

Binary gating is sound when the steps are externally observable and their predicates are executable. It is conditional when a learned process reward model supplies the step labels.

## 9. Runtime verification and monitors

Runtime verification checks an observed execution trace against a formal specification, often expressed as temporal logic, state machines, or rules ([Leucker and Schallhart, *A Brief Account of Runtime Verification*, Journal of Logic and Algebraic Programming 2009](https://christian.schallhart.net/publications/2009--jlap--a-brief-account-of-runtime-verification.pdf), peer-reviewed; [Falcone, Havelund, and Reger, *A Tutorial on Runtime Verification*, 2013](https://havelund.com/Publications/rv-tutorial-ios-2012.pdf), peer-reviewed book chapter).

This transfers well to agent policies such as:

- Never write outside the workspace.
- Do not call a tool before approval.
- Every external claim must be followed by a citation event.
- Once a destructive action is proposed, execution requires an approval event.
- Do not declare completion before required gates succeed.

It transfers poorly to “be concise” or “emphasize only one point,” unless those are first reduced to an observable predicate. A runtime monitor changes when the check happens; it does not create the missing oracle.

AgentSpec applies a DSL of triggers, predicates, and enforcement actions to agent execution. Its reported results are promising but domain-specific, and LLM-generated rules had high precision but materially lower recall in one embodied-agent setting ([Wang, Poskitt, and Sun, *AgentSpec*, ICSE 2026 author manuscript](https://cposkitt.github.io/files/publications/agentspec_llm_enforcement_icse26.pdf), peer-reviewed conference work).

Runtime monitors yield strong binary gates for finite-trace safety properties. They cannot certify unobservable intent or arbitrary semantic quality.

## 10. Constitutional critique, revision, self-consistency, and verifier–generator separation

Constitutional AI asks a model to critique and revise its answer against written principles, then uses AI preferences for training ([Bai et al., *Constitutional AI: Harmlessness from AI Feedback*](https://arxiv.org/abs/2212.08073), industry preprint).

Related patterns include:

- Generate, critique, revise.
- Generate many answers and take the modal answer.
- Generate candidates and rank them with a verifier.
- Use a distinct critic to assist a human.

There is real evidence for verifier leverage in constrained domains:

- Self-consistency improved arithmetic and commonsense reasoning by sampling diverse paths and selecting the common answer ([Wang et al., ICLR 2023](https://openreview.net/pdf?id=1PL1NIMMrw), peer-reviewed).
- Trained verifiers improved selection among GSM8K candidates and scaled better than a fine-tuning baseline ([Cobbe et al., *Training Verifiers to Solve Math Word Problems*](https://arxiv.org/abs/2110.14168), preprint).
- Process reward models likewise improve mathematical selection.

But the “verifier is easier than generator” gap is not universal, especially for stylistic judgments where both generation and verification use the same latent preferences. Intrinsic self-correction can fail or degrade correct reasoning ([Huang et al., ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/8b4add8b0aa8749d80a34ca5d941c355-Abstract-Conference.html), peer-reviewed). Other work finds improvement when verification is narrowed to key conditions, so the evidence is task- and feedback-dependent ([Wu et al., EMNLP 2024](https://aclanthology.org/2024.emnlp-main.714/), peer-reviewed).

These patterns do not safely yield a blocking verdict by themselves. They become usable when the verifier is separately calibrated or grounded in external evidence.

## 11. Mutation testing of the oracle

Mutation testing asks whether a validator fails when controlled defects are introduced. It is especially valuable here because a check can execute, parse, and return green without being capable of detecting its target violation.

For each policy validator, create:

- A clean artifact.
- A minimal violating mutation.
- A near-boundary clean case.
- A misleading case with attractive surface quality.
- An unrelated mutation that must not trigger the validator.
- Mutations of the rule itself: deletion, negation, weakened threshold, changed scope.

The validator should:

- Kill the violating mutations.
- Preserve the clean and unrelated controls.
- Fail closed if it cannot evaluate.
- Report which policy and evidence caused the verdict.

Mutation analysis is a mature test-adequacy technique ([Jia and Harman, IEEE TSE 2011](https://doi.org/10.1109/TSE.2010.62), peer-reviewed). Research specifically connects undetected mutants with inadequate oracles and shows mutation score reveals weaknesses missed by coverage ([Fraser and Zeller, IEEE TSE 2012](https://www.evosuite.org/wp-content/papercite-data/pdf/tse12_mutation.pdf), peer-reviewed; [Jain et al., *Mind the Gap*](https://clairelegoues.com/assets/papers/jainOracleGap.pdf), peer-reviewed version/preprint copy).

This is one of the strongest additions to the listed patterns: use mutation testing not only on generated code, but on the policy evaluators and on the guidance treatment itself.

## 12. Linters, blocking, autofix, and warning fatigue

The static-analysis literature shows that warnings influence authors when they are timely, local, actionable, and trusted. False positives and poor presentation are major adoption barriers ([Johnson et al., ICSE 2013](https://research.google/pubs/why-dont-software-developers-use-static-analysis-tools-to-find-bugs/), peer-reviewed; [Christakis and Bird, ASE 2016](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/08/ASE-2016.pdf), peer-reviewed).

Google’s Tricorder experience imposed a practical admission bar: warnings should be understandable, actionable, important, and perceived as correct at least 90% of the time. It integrated findings into code review, tracked “not useful” feedback, and supported suggested fixes. The paper reports codebase violations dropping or levelling off after checks were introduced, although this is observational rather than a randomized causal estimate ([Sadowski et al., ICSE 2015](https://research.google.com/pubs/archive/43322.pdf), peer-reviewed industrial study).

For behavioral-policy linters:

- Advisory mode is appropriate while precision is unknown.
- Blocking should begin only after shadow-mode calibration.
- Autofix is suitable for local, semantics-preserving transformations.
- A proposed fix can also clarify the warning even when not applied.
- Suppression must require a reason and remain observable.
- Noisy validators should be demoted or disabled, not normalized as permanent build noise.

Warnings can change behavior, but repeated low-value warnings train authors to ignore the system. The literature supports actionability and low false-positive rates far more strongly than it supports a universal “warnings always work” claim.

## Which patterns are trustworthy enough to block?

| Pattern | Blocking status | Minimum prior evidence |
|---|---|---|
| Deterministic contract or property | Strong | Reviewed mapping to policy; boundary tests; policy mutations killed |
| External-reference check | Strong | Authoritative, versioned reference; explicit equivalence rules |
| Runtime safety monitor | Strong | Observable event trace; monitorable property; fail-safe enforcement |
| Metamorphic relation | Strong–conditional | Valid relation; repeated stochastic trials where needed |
| Human adjudication | Strong–conditional | Independent trained raters; adequate agreement; conflict process |
| Dedicated statistical classifier | Conditional | Held-out local labels; per-policy confusion matrix and confidence bounds |
| LLM judge | Conditional | Same as classifier plus bias, swap, verbosity, self-preference, and drift tests |
| Guidance ablation | Strong for suite-level causal regression | Randomized control; challenge set; minimum effect; confidence bound |
| Differential agreement | Escalation signal | Independent comparators and trusted adjudicator |
| Process reward model | Conditional | Observable steps or independently calibrated step labels |
| Global LLM reviewer | Advisory by default | Full local calibration is harder because error causes are entangled |
| Self-critique/self-consistency | Advisory or candidate selection | Independent final oracle still required |

## Recommended design for detecting that a rule did not fire

Use two separate tests because “artifact acceptable” and “rule contributed” are different hypotheses.

### A. Outcome-compliance test

A policy-specific validator asks whether the artifact violates the rule. It should be mutation-tested and locally calibrated. This is the ordinary artifact gate.

### B. Instruction-contribution test

A scheduled or change-time experiment asks whether the rule changes behavior:

1. Build policy-challenge tasks from real failures plus minimal synthetic cases.
2. Freeze a held-out set before editing the rule.
3. Run treatment, removal, and length-matched placebo conditions.
4. Blind the evaluator to the condition.
5. Run enough repetitions to estimate the paired violation-rate difference.
6. Require a lower confidence bound above a predeclared useful effect.
7. Require non-inferiority on task correctness and other critical policies.
8. Mutate or invert the rule and verify that the suite notices.
9. Re-run after model or surrounding-context changes.

Interpretation:

- **Treatment better than control:** evidence that the rule binds on this distribution.
- **Both good:** the rule may be redundant, the test may have a ceiling, or the rule may still influence unmeasured aspects.
- **Both bad:** the rule is ineffective, the model is incapable, or the evaluator is blind.
- **Treatment worse:** the rule backfires or competes with higher-priority objectives.
- **High variance:** no gating claim; expand cases or improve the oracle.

For a single execution, there is no output-only test that proves the rule fired. Instrumentation can prove that the rule was loaded or referenced, but access is not causal use. If per-run proof is required, the policy must be moved into an externally enforced step: a structured decision record, a per-section validator, or a runtime monitor.

## Avoiding the self-reference trap

In descending order of independence:

1. Executable properties tied to an external specification or live system.
2. Metamorphic relations and mutations whose expected relation is human-reviewed.
3. Independently labelled human gold cases.
4. A frozen policy-specific classifier trained and tested on separated data.
5. A judge from a different model family, blinded and calibrated against humans.
6. Multiple LLM judges.
7. The generator reviewing its own output.

Different model families reduce direct self-preference but do not guarantee independence: training corpora, preference data, and superficial quality biases may still overlap. Inter-LLM agreement is therefore evidence of consistency, not truth.

## Evidence gaps

- **Known-unknown:** No strong head-to-head literature establishes that one-validator-per-policy is universally more accurate than a single global reviewer for arbitrary prose guidance. Existing evidence supports better auditability and sometimes better agreement, but counterexamples exist.
- **Known-unknown:** There is no universal calibration-set size, κ threshold, or acceptable false-block rate for LLM judges. These depend on policy prevalence and the cost of false blocks versus missed violations.
- **Known-unknown:** Prompt ablation is recognizable causal methodology, but “instruction binding” is not yet a mature named oracle class with accepted build-gating standards.
- **Known-unknown:** Linter evidence concerns human developers, not coding agents authoring documents. Transfer should be treated as a hypothesis and measured.
- **Unknowable from output alone:** Whether one policy causally affected one already-acceptable artifact. That counterfactual execution was not observed.

The repository was not modified, and no git write or remote-freshness command was run.