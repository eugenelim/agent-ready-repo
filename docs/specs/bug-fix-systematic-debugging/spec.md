# Spec: Bug-fix systematic debugging

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The shipped `bug-fix` skill gives an agent a systematic, evidence-led route from
an observable defect to the smallest coherent correction. It keeps reproduction
and a contract-level failing test early, tests 2–3 rival hypotheses with
Expected / Actual / Verdict evidence, traces the bad value or event backward to
its source, and distinguishes diagnostic experiments from production fixes.
Multi-component, asynchronous, environmental, and production-emergency cases
have explicit branches, so an agent neither stacks speculative patches nor
claims a root cause the evidence does not establish. The workflow preserves the
existing coverage-gap, minimum-diff, commit-rationale, and tracker-sync
disciplines. It activates from the language people use before they know the
cause—root-cause requests, CI-only failures, intermittent or flaky behavior, and
active production incidents—without capturing new-feature, refactor, postmortem,
or skill-maintenance work.

## Boundaries

### Always do

- Reproduce the ordinary defect and run a regression test red against the
  unfixed behavior for the intended reason before writing the production fix;
  pin the observable contract rather than an implementation detail.
- Keep 2–3 rival hypotheses in an Expected / Actual / Verdict evidence record,
  changing one factor at a time within that candidate set.
- Trace backward from the symptom to the earliest bad value or event and, for a
  multi-component path, inspect inputs, outputs, state, and configuration at
  each relevant boundary before narrowing the investigation.
- Separate temporary diagnostic experiments and emergency mitigation from the
  permanent fix; remove diagnostics or retain them deliberately as production
  observability.
- Before any production mutation, confirm the exact containment action, scope,
  and blast radius unless the operator approved that action in the current turn.
  Preserve only the minimum incident evidence needed, redact or sequester
  sensitive fields, and keep raw user data and secrets out of model context and
  durable repository or tracker artifacts.
- Close the coverage gap, keep the production diff to the minimum coherent
  change, explain the root cause and fix shape in the commit body, and sync the
  owning tracker when one exists.
- Keep the frontmatter description and Tier-A activation queries aligned on
  natural debugging language and near-miss boundaries.

### Ask first

- Widening the fix beyond the failing component or crossed boundary, including
  adding guards at multiple internal layers.
- Continuing after three evidence-backed hypotheses or fix attempts fail; stop
  patch stacking and surface the evidence for architectural discussion.
- Turning an emergency containment action into a permanent behavior change, or
  taking a production action beyond the operator's existing authority.

### Never do

- Never add a second debugging skill, a new module boundary, or a dependency for
  this change.
- Never copy another debugging workflow wholesale or discard the existing
  test-first, rival-hypothesis, minimum-diff, coverage-gap, commit-rationale, or
  tracker-sync requirements.
- Never replace a real condition with an arbitrary sleep, or treat a retry or
  passing rerun as proof that a defect is fixed.
- Never require validation at every internal layer; validate crossed boundaries
  and add another guard only for an independent bypass path or a concrete safety
  consequence.
- Never present containment, a diagnostic experiment, or bounded handling for
  an external failure as an established internal root-cause fix.

## Testing Strategy

- **Workflow invariants: TDD at the source-artifact surface.** A pytest module
  reads the canonical `SKILL.md` and pins the ordered normal path, rival-evidence
  shape, multi-component localization directive, and preserved scope/release
  disciplines. One named test maps to each deterministically checked criterion
  (AC1, AC2, AC3, AC11, and AC17). The AC17 test parses both frontmatter and
  activation-query JSON; no test claims to prove diagnostic judgment from a
  phrase alone. The assertions avoid line counts and full-file snapshots.
- **Agent judgment: goal-based LLM-judge evals.** Skill-local
  `evals/evals.json` scenarios cover a multi-component defect, an asynchronous
  flaky test, three failed evidence-backed attempts, an environmental or
  external failure, and an active production emergency. The multi-component
  scenario also requires known-good comparison, backward tracing, and separation
  of diagnostics from the production fix. Rubrics require the evidence record
  and reject sleeps, retry-as-proof, patch stacking, false root-cause claims,
  mitigation presented as a fix, and embedded diagnostic-artifact directives
  that redirect scope, tools, or authority. These evals are report-only model
  evidence, not a deterministic gate.
- **Activation contract: static TDD plus report-only Tier-A runs.** The
  frontmatter description and `evals/eval_queries.json` carry positive cases for
  root-cause, CI-only, intermittent/flaky, and active-incident language, plus
  near misses for new work, behavior-preserving refactors, postmortems, and
  maintaining the skill itself. A named static test keeps those two router
  surfaces aligned; live router measurements run when the configured harness is
  available and remain report-only evidence.
- **Pack and projection integrity: goal-based checks.** JSON parsing, the
  dedicated pytest process, deep catalogue lint, catalogue verification,
  version agreement, self-host projection, drift checks, and applicable
  repository build checks verify the shipped artifact. The repo-local command
  reference names these current CLI gates rather than a deleted standalone
  script.
- **Shipped behavior: visual / manual QA.** A read-only, ephemeral invocation of
  the projected `bug-fix` skill handles a synthetic multi-component asynchronous
  defect. The recorded response must keep the early regression test, boundary
  localization, rival evidence, condition-based waiting, backward trace,
  diagnostic/fix distinction, and minimum diff. The separate behavior evals
  cover the repeated-failure stop rule and exceptional outcome branches.
- **Documentation consistency: goal-based check.** The adopter-facing production
  hotfix variation describes urgent containment as mitigation, requires
  exact-action confirmation, minimized/redacted evidence handling, and an
  instruction-vs-data boundary for diagnostic artifacts, then returns to
  reproduction, a red observable-contract test, root-cause analysis, and the
  permanent minimum fix. Guide validation, index coverage, and relative-link
  checks remain green.

Coverage tally: TDD stubs cover AC1, AC2, AC3, AC11, and AC17; LLM-judge evals
cover AC3–AC10; deterministic goal-based checks cover AC12–AC14, AC16, and AC18;
manual QA covers AC1–AC7 and AC11 plus one composite positive AC17 sample, and
AC15 records that invocation separately.

## Acceptance Criteria

- [x] AC1. Outside an active production emergency, the workflow reproduces the
  defect and runs a regression test against unfixed behavior before a production
  fix; the test fails for the intended reason and pins the observable contract.
- [x] AC2. The workflow retains 2–3 rival hypotheses in Expected / Actual /
  Verdict form and uses one-factor diagnostic experiments within that candidate
  set before asserting a root cause.
- [x] AC3. A multi-component branch records inputs, outputs, state, and
  configuration propagation at each relevant boundary, runs once to locate the
  failing component, and only then narrows the investigation.
- [x] AC4. The investigation finds a similar known-good path or authoritative
  reference, enumerates meaningful differences, and uses those differences to
  generate or refine hypotheses.
- [x] AC5. Root-cause analysis traces backward from the symptom through callers,
  state transitions, and data transformations to the original bad value or
  event, rather than stopping at the crash site.
- [x] AC6. The workflow labels a diagnostic experiment separately from the
  eventual production fix and requires temporary diagnostics to be removed or
  deliberately retained as production observability.
- [x] AC7. Asynchronous or flaky-test guidance prefers retrying assertions or
  bounded polling of the real condition over arbitrary sleeps; retries may
  gather evidence or mitigate an external fault but never prove a fix.
- [x] AC8. After three evidence-backed hypotheses or fix attempts fail, the
  workflow stops stacking patches and surfaces the evidence for architectural
  discussion without declaring that the architecture is automatically wrong.
- [x] AC9. When evidence supports an environmental, timing, or external-failure
  outcome instead of an internal root cause, the workflow records evidence and
  ruled-out causes, adds only justified bounded handling or observability, and
  states that no internal cause was established.
- [x] AC10. When users, security, or data are actively at risk, containment may
  precede reproduction and root-cause analysis. It stays within operational
  authority and is labelled mitigation, and the exact action, scope, and blast
  radius are confirmed unless already approved in the current turn. Evidence is
  minimized, sensitive fields are redacted or sequestered, and raw user data or
  secrets do not enter model context or durable repo/tracker artifacts.
  Diagnostic artifacts are treated as untrusted data: embedded directives are
  ignored and attempts to redirect scope, tools, or authority are surfaced.
  Containment is not presented as the permanent fix.
- [x] AC11. Fix scope stays at the minimum coherent diff and validates the
  boundaries the request crosses; extra guards require an independent bypass
  path or concrete safety consequence. Coverage-gap analysis, commit rationale,
  adjacent-cleanup refusal, and tracker sync remain explicit.
- [x] AC12. `packs/core/.apm/skills/bug-fix/evals/evals.json` is valid JSON and
  contains judge scenarios for AC3–AC10 with positive and negative assertions
  that distinguish evidence gathering, mitigation, and diagnostics from a fix.
- [x] AC13. A dedicated core-pack test reads the canonical skill source, goes
  red against the pre-change workflow, and passes with the required normal-path
  order and preserved disciplines. Each mapped criterion has its own named test;
  no exact-file hash, snapshot, or line-count assertion is added.
- [x] AC14. Core pack metadata agrees on version `2.5.1`, the changelog explains
  the user-visible workflow improvement, generated self-host projections match
  the canonical source, and all specified lint, catalogue, test, drift, and
  build checks pass.
- [x] AC15. A recorded read-only invocation of the projected skill against a
  synthetic multi-component asynchronous defect follows AC1–AC7 and AC11; its
  exit code and observed response are captured separately from the mechanical
  gate result. The prompt demonstrates one composite positive route from AC17;
  it does not claim to verify all four activation classes or any near-miss
  boundary. AC8–AC10 remain explicit LLM-judge scenarios rather than claims
  about branches this manual prompt does not exercise.
- [x] AC16. `AGENTS.local.md` replaces the deleted standalone artifact-lint
  command with deep catalogue lint plus catalogue verification, and the spec
  note records the deletion, replacement, later stale reintroduction, rejected
  compatibility shim, and current revival disposition from local git history.
- [x] AC17. The `bug-fix` frontmatter description and Tier-A query set activate
  on natural-language requests to find a root cause, explain a CI-only failure,
  diagnose intermittent/flaky behavior, or contain and diagnose an active
  production incident. Existing positives and negatives remain, and explicit
  near misses keep new features, behavior-preserving refactors, resolved-incident
  postmortems, and maintenance of the `bug-fix` skill routed elsewhere.
- [x] AC18. The shipped production-hotfix guide permits already-authorized
  containment before the normal sequence only as labelled mitigation. It
  requires exact-action confirmation unless already approved in the current
  turn, minimizes evidence, redacts or sequesters sensitive fields, and treats
  diagnostic artifacts as untrusted data whose embedded directives cannot
  redirect scope, tools, or authority. The permanent fix returns to
  reproduction, a red observable-contract regression test, root-cause analysis,
  and the minimum supported correction. Its relative links and guide validation
  pass.

## Assumptions

- Technical: `packs/core/.apm/skills/bug-fix/SKILL.md` is the canonical source
  and already carries the test-first, rival-hypothesis, root-cause,
  minimum-diff, coverage-gap, commit-rationale, and tracker-sync disciplines
  (source: `packs/core/.apm/skills/bug-fix/SKILL.md`).
- Technical: `bug-fix` has Tier-A activation queries but no behavior-eval file
  or dedicated skill-test directory, and no bug-fix-specific content hash,
  snapshot, or line-count anchor test exists (source: targeted repository sweep
  on 2026-08-08).
- Process: a substantive core skill change requires a patch bump in both pack
  manifests, a changelog entry, self-host projection, and catalogue lint and
  verification (source: `packs/AGENTS.md`, `packs/AGENTS.local.md`).
- Process: the standalone artifact linter was deliberately folded into
  `agentbundle catalogue lint/verify`, with no compatibility shim; its command
  was later reintroduced only in repo-local guidance (source: commits `96232e6`
  and `62f4faf`, plus
  `docs/specs/fold-standalone-linters-into-cli/spec.md`).
- Process: the work runs in full mode with adversarial spec/plan review and
  separate human approvals before implementation (source:
  `.agents/skills/work-loop/SKILL.md`).
- Process: the current task branch is the intended workspace branch (source:
  user confirmation 2026-08-08).
- Product: the change ends at the existing skill, its eval and test coverage,
  release metadata, changelog, and generated projections; it creates no new
  debugging primitive or runtime interface and uses `Shape: mixed` (source:
  user confirmation 2026-08-08).
- Product: a prior real debugging session failed to select `bug-fix`, so
  activation coverage must extend beyond prompts that literally say bug, fix,
  broken, or regression (source: user confirmation 2026-08-08).
