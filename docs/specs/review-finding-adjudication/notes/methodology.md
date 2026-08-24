# Review-finding adjudication methodology

> Discipline: applied (practitioner-pattern survey)

> **Final design decision (2026-08-23):** the shipped primitive is named
> `finding-adjudicator`, and every completed reviewer report passes through it
> before the controller classifies the report as clean or finding-bearing. The
> earlier `findings-refuter` name and selected/non-clean trigger below preserve
> the pre-clarification research path; they are superseded by the approved
> contract in
> [`docs/specs/review-finding-adjudication/spec.md`](docs/specs/review-finding-adjudication/spec.md).

- **Recommendation:** insert one bounded `findings-refuter` pass between a
  non-clean reviewer report and `FIX`. It validates the report's material
  findings; it does not review the diff again. The original report plus the
  refuter's filtered report form the review result.
- **Initial trigger:** in full mode, automatically validate every Blocker and
  Concern, plus any Nit whose proposed fix changes behavior, a contract, or
  structure. In light mode, automatically validate Blockers and validate other
  findings only when their fix is consequential or the orchestrator contests
  them. Batch the selected findings into one call.
- **Verdicts:** `sustained`, `refuted`, or `indeterminate`. Only `sustained`
  findings enter `FIX`; `refuted` findings close with evidence;
  `indeterminate` findings surface to the owner rather than causing speculative
  code changes.

# 1. Scope frame

- **Suppliers:** adversarial, quality, security, experience, and frontend
  reviewers; the accepted spec/plan; repository rules; current code and tests;
  the orchestrating work-loop.
- **Inputs:** a complete reviewer report; the exact review target; the finding's
  cited location and proposed fix; its governing rubric or contract; relevant
  executable evidence.
- **Process:** adjudicate whether each material review finding describes a real
  defect before changing the implementation.
- **Outputs:** a filtered findings report, evidence-backed dispositions, and a
  small round summary (`raised / sustained / refuted / indeterminate`).
- **Customers:** the implementing agent, future review rounds, and the human
  owner who currently has to discover bad review trajectories late.
- **In scope:** post-review finding validity across every reviewer role and both
  light and full work-loop modes. **Out of scope:** replacing reviewers,
  weakening security gates, scoring agent reputation, building a debate swarm,
  or automatically changing accepted intent.

- **Current structural gap:** full mode iterates the adversarial reviewer to an
  exact clean string, while light mode names only `apply` or `defer` at the
  review boundary. The loop records fingerprints and detects repeated findings,
  but says that no pre-filtered open-findings file exists and leaves validity to
  DECIDE. DECIDE routes by intent fit, not truth. See
  [`work-loop` REVIEW and DECIDE](packs/core/.apm/skills/work-loop/SKILL.md#step-4-review).
  The reviewer is deliberately recall-biased: “when in doubt, flag,” with a
  closed suppression list. See
  [`adversarial-reviewer` lines 300–309](packs/core/.apm/agents/adversarial-reviewer.md#what-not-to-flag).
  [high]

# 2. Stage spine

- **Discipline: process discovery + hierarchical task decomposition.** The
  adjudication sits inside REVIEW, before the loop records actionable
  fingerprints or mutates code.

## Stage 1 — Freeze a finding packet

- For each selected finding, copy only: stable finding ID/fingerprint; reviewer
  role; severity; exact allegation; cited `file:line`; proposed fix; governing
  rule/AC; review-target description; and the minimum relevant diff/context.
- Require the reviewer-side observation, standard, and fix already demanded by
  the current report contract. A finding without a specific location and
  falsifiable defect predicate is malformed, not automatically true.
- Do not let the implementing agent edit code for a selected finding before the
  packet is adjudicated. This prevents the fix itself from destroying the best
  evidence that the finding was false.

## Stage 2 — Try to falsify the finding

- Dispatch one independent `findings-refuter` agent for the batch. It must not be
  the original reviewer or the implementer, and it must not generate new review
  findings.
- Check the finding's necessary predicates in this order: **observation** (does
  the cited condition exist?); **authority** (does the cited rule/AC apply?);
  **reachability** (can the alleged path execute in the target environment?);
  **coverage** (is the case handled elsewhere in the same diff/call graph?);
  **counterfactual** (would the proposed fix change the relevant behavior, and
  would it improve rather than violate the accepted contract?).
- Prefer executable or mechanically inspectable evidence. Passing broad tests
  alone does not refute a finding; a focused test, trace, caller proof, schema,
  or authoritative contract can. Recent code-review research found that
  validating original and proposed-fix behavior with executable counterfactuals
  substantially reduced false rejection compared with trusting a textual
  rationale alone. [moderate] — the evidence is benchmark-based and may not
  transfer uniformly to documentation or architecture findings.

## Stage 3 — Render a closed verdict

- **`sustained`:** the alleged defect is reproduced or the governing contract is
  demonstrably violated. Include the smallest decisive evidence; retain the
  finding unchanged for `FIX`.
- **`refuted`:** a necessary predicate is false. Name the refutation class
  (`observation absent`, `authority inapplicable`, `path unreachable`, `handled
  elsewhere`, or `fix violates contract`) and cite decisive evidence. Cost,
  inconvenience, scope, and “tests pass” are not refutations.
- **`indeterminate`:** evidence is missing or two legitimate authorities
  conflict. Name exactly what evidence or owner decision would settle it. Do not
  guess and do not modify code.
- Emit the same findings-only shape consumed today, containing only sustained
  findings; emit the exact clean string when every finding is refuted. Preserve
  the original report and the refutation report as a pair in the existing
  disposition record. This reuses `review inspect` and fingerprinting rather
  than adding a new state machine or database. [moderate] — repository-specific
  synthesis.

## Stage 4 — Route only adjudicated work

- `sustained` -> current intent-fit routing -> `FIX` -> GATES -> reviewer again.
- `refuted` -> resolved, no code mutation. Feed its compact evidence disposition
  to later reruns for the same target. The reviewer may raise the predicate again
  only with materially new evidence or after the cited contract/code changed.
- `indeterminate` -> surface once to the owner with the finding, both sides, and
  the missing deciding evidence. This is the point at which the user's
  end-to-end judgment belongs, rather than after several repair rounds.
- Record retry fingerprints only from the filtered report. Otherwise false
  findings consume the same retry/stasis budget as real defects and make the
  existing loop safeguards trigger too late.

## Stage 5 — Close and learn lightly

- Finish when gates are green and every raised finding is either fixed after a
  `sustained` verdict or evidence-refuted; an `indeterminate` material finding
  still requires the owner.
- Add only four counts to the final handoff: raised, sustained, refuted,
  indeterminate. Do not build reviewer leaderboards or long-lived analytics in
  the first version. After roughly 10–20 representative loops, inspect the counts
  and the reasons before changing trigger thresholds.

# 3. Contingency branches

- **if full mode produces Blockers or Concerns -> automatically run one batched
  refuter pass before `FIX`.** This does not rely on an agreeable implementer to
  notice that a finding is questionable.
- **if the refuter runs -> keep the already-selected loop mode.** It adjudicates
  a completed review report and does not become another builder or a second
  general review of the diff, so its presence alone must not promote light work
  to full mode.
- **if light mode produces a Blocker -> automatically refute-check it.** The
  current one-re-review budget makes a wrong Blocker disproportionately costly.
- **if a lower-severity finding prescribes a behavior, contract, architecture,
  dependency, or multi-file change -> treat it as material regardless of its
  label.** Severity and fix blast radius are separate.
- **if a Nit is local, reversible, and obviously evidenced -> use the current
  disposition path.** Do not pay an extra agent call merely to arbitrate polish.
- **if the report repeats a prior refuted predicate without new evidence -> keep
  it refuted and do not spend a retry.** A changed cited contract or code path
  invalidates the prior refutation and permits fresh adjudication.
- **if the finding comes from a specialist reviewer -> give the refuter that
  reviewer's governing checklist slice.** A security finding is refutable, but
  uncertainty remains blocking; absence of proof is never treated as proof of
  safety.
- **if executable verification is available -> compare original and proposed-fix
  behavior.** If not, use contract, call-graph, schema, rendered-artifact, or
  primary-source evidence appropriate to the finding type.
- **if no independent refuter is installed -> material findings surface for human
  adjudication or follow the current fix path; the implementer may not silently
  dismiss them.** This is a named degraded mode, not an excuse to self-certify.

# 4. Maturity ladder

- **Crawl — recommended first release:** one `findings-refuter` role, a short
  packet/output contract, and work-loop prose that invokes it for material
  findings. Reuse existing report files, exact-clean parsing, and the
  resolve-vs-surface record. No engine schema change.
- **Walk:** after observed use, add structured verdict parsing and make the cohort
  count only sustained fingerprints. Add contract tests for all-refuted,
  mixed-verdict, indeterminate, stale-refutation, and malformed-output cases.
- **Run:** only if data justifies it, tune triggers per reviewer/domain and track
  false-positive reasons over time. Do not add reviewer reputation scores,
  majority voting, or multi-round debate unless measured failures show the
  narrow pass is inadequate.
- **Competence shift:** the practice moves from “review output is authority,” to
  “the implementer may object,” to “material findings receive independent,
  evidence-bound adjudication,” to “thresholds are calibrated from observed
  precision without weakening recall.”

# 5. Failure modes

- **The refuter becomes a second general reviewer** · easy to miss because extra
  findings look like diligence · guard: it can only sustain/refute/abstain on the
  supplied finding IDs; adjacent discoveries return to the ordinary review path.
- **The refuter is prompted to agree with the implementer** · easy to miss because
  a fluent rebuttal sounds evidential · guard: supply the allegation and evidence,
  not the implementer's preferred verdict; require a disproven necessary
  predicate for `refuted`.
- **Majority vote replaces evidence** · easy to miss because three agents look
  independent while sharing model priors and context · guard: one adjudicator,
  technical facts and executable evidence over vote count. [moderate] —
  inference; direct evidence about correlation for this exact agent roster is not
  available.
- **Validity and scope are conflated** · easy to miss because “out of scope” can
  make a true defect disappear and “in scope” can make a false defect look
  mandatory · guard: adjudicate truth first, then run the existing intent-fit
  table.
- **A refutation becomes a permanent suppression** · easy to miss because the
  same fingerprint looks stable · guard: bind it to its cited authority and code
  evidence; reopen when either changes or new evidence appears.
- **Every Nit pays the arbitration tax** · easy to miss because the policy sounds
  simpler when universal · guard: batch automatically only material findings;
  lower-severity local polish stays on the bounded path.
- **The original reviewer keeps re-raising an adjudicated false positive** · easy
  to miss because stasis catches it only after another round · guard: include the
  compact disposition on reruns and require new evidence to reopen it.

# 6. Evidence & confidence

- **LLM critics improve defect discovery but can hallucinate bugs, and more
  explanation/fix-oriented review prompting can increase false rejection of
  correct implementations.** OpenAI's CriticGPT study explicitly reports
  hallucinated bugs and lower hallucination when humans and critics work
  together; a 2026 multi-model code-review study finds systematic over-correction
  and misleading causal explanations; an industrial static-analysis study shows
  the operational cost of conservative high-recall alerting and uses separate
  false-alarm validation. [high] Sources:
  [CriticGPT paper](https://arxiv.org/abs/2407.00215),
  [systematic over-correction study](https://link.springer.com/article/10.1007/s10515-026-00638-5),
  [Tencent industrial false-alarm study](https://arxiv.org/abs/2601.18844).

- **The implementing agent's own second thought is not a sufficient control.** A
  critical survey finds prompted self-correction succeeds reliably mainly when
  grounded by external feedback; a separate reasoning study reports that
  intrinsic self-correction can degrade performance; Anthropic found consistent
  sycophancy across five assistants and that preference feedback sometimes
  favors convincing agreement over correctness. [high] Sources:
  [self-correction critical survey](https://arxiv.org/abs/2406.01297),
  [DeepMind self-correction study](https://arxiv.org/abs/2310.01798),
  [Anthropic sycophancy study](https://www.anthropic.com/research/towards-understanding-sycophancy-in-language-models).

- **Mature finding systems make non-fix outcomes explicit, justified, auditable,
  and reopenable.** SARIF models external suppressions with
  `accepted / underReview / rejected` state and a justification; GitHub code
  scanning records dismissal reasons/comments, supports audit and reopening;
  this repository's SAST plan already distinguishes real fixes from justified
  tool false positives. [high] Sources:
  [SARIF 2.1.0 suppression object](https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html#_Toc34317881),
  [GitHub code-scanning dismissal workflow](https://docs.github.com/en/code-security/how-tos/manage-security-alerts/manage-code-scanning-alerts/resolve-alerts),
  [local SAST/SCA false-positive disposition](docs/specs/sast-sca-tooling/plan.md#t3-disposition-the-false-positives--harden-the-arxiv-parse).

- **Disagreement should resolve against evidence, with narrow independent
  arbitration when consensus fails.** Google's engineering guidance says
  technical facts override preferences and escalates unresolved author-reviewer
  conflicts; Cochrane resolves ordinary disagreements through discussion and
  interpretation disputes through another person; SARIF/GitHub preserve the
  resulting justification. [high] Sources:
  [Google's code-review standard](https://google.github.io/eng-practices/review/reviewer/standard.html),
  [Cochrane study-selection adjudication](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-04),
  [SARIF](https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html#_Toc34317881),
  [GitHub code scanning](https://docs.github.com/en/code-security/how-tos/manage-security-alerts/manage-code-scanning-alerts/resolve-alerts).

- **For this repository, a single conditional refuter is the smallest mechanism
  that closes the gap.** The existing reviewer already supplies a finding packet;
  the cohort already parses filtered findings and fingerprints; the work-loop
  already owns disposition and human surfacing. Reusing those seams avoids a new
  debate protocol, persistence service, or general reviewer. [moderate] —
  synthesis from the cited patterns and local architecture; effectiveness must be
  measured in this loop.

- **Retriever note:** this applied study used local repository inspection and
  first-party/primary web sources. No authenticated research connector or useful
  domain-specific script retriever was exposed for this software-process
  question. The final unused-snippet pass strengthened the counterfactual-testing
  recommendation with the 2026 code-review filter study; no retrieved
  counter-evidence displaced the recommended narrow adjudication pattern.

## Known unknowns

- **Known-unknown:** the actual material-finding false-positive rate in these
  loops, split by reviewer and severity. Would be closed by: adjudicating 10–20
  representative non-clean rounds and recording the four terminal counts.
- **Known-unknown:** whether automatic Concern validation pays for itself in
  latency and tokens. Would be closed by: comparing avoided fix/re-review cost
  with one batched refuter call over the pilot.
- **Known-unknown:** how independent the refuter remains when it shares the same
  model family as a reviewer. Would be closed by: a small seeded evaluation with
  known true and false findings, run across same-model and different-model
  pairings.
- **Known-unknown:** which refutation evidence should remain valid across a
  changed diff. Would be closed by: pilot examples identifying the minimum
  stable dependency set (contract anchor, call path, or focused test).
- **Unknowable:** exactly how many past review rounds this control would have
  saved. Why not: the historical reports do not carry independent ground-truth
  adjudications, and rerunning old loops would change model and repository state.
