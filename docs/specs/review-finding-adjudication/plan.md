# Plan: Review finding adjudication

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn while its status is `Drafting` or
> `Executing`. Once it is `Done` and the spec is `Shipped`, the directory
> freezes as a unit.

## Approach

Add one read-only core agent as a gateway between existing reviewers and the
main loop, then route every pre-EXECUTE and post-GATES reviewer report through
it before the controller decides whether the report is clean. Keep the raw
reviewer report opaque and path-addressed; the
adjudicator independently checks the target and produces a parse-safe result
whose numbered findings are only the sustained subset. Existing `loop-cohort`
classification and fingerprinting then work unchanged. Refutation and
indeterminate records remain in non-finding sections of the adjudication
artifact, so the audit survives without occupying the main loop's resident
context or requiring a new state schema.

The portable guarantee is about the loop's **decision and repair context**, not
an adapter promise the catalogue cannot enforce. When the runtime can route
subagent output directly to an artifact, raw reports bypass the controller.
Otherwise they cross controller transport once, are persisted immediately and
treated as opaque, and are never reasoned over, repeated, or reloaded.

The implementation deliberately changes prose contracts and tests, not the FSM:
agent source first, work-loop routing second, falsification fixtures third,
release/projection last. This follows the reference architecture's authored
pack-source to generated-projection path and adds no dependency or adapter
surface.

## Constraints

- ADR-0042 caps the core code-review lenses at three and requires new agents to
  clear a loop/work-type value test plus collision-hardening. The owner approved
  the no-RFC classification recorded in the spec: `finding-adjudicator` is a
  path-fed process-control agent for a distinct finding-adjudication work type,
  cannot discover defects, and earns its existence through forked-context
  independence.
- RFC-0051's self-coverage implementation rejected a new reviewer. This change
  does not expand checklist coverage; it adds a false-positive control after
  existing coverage and records the owner's explicit 2026-08-23 approval to
  depart from that RFC's implementation shape without amending it.
- Edit `packs/core/.apm/` source, then regenerate projections with
  `agentbundle catalogue self-host --root . --write` / `make build-self`; never
  author generated agent or skill projections.
- Preserve the current cohort state schema, finding grammar, clean sentinel,
  reviewer triggers, retry limits, and light/full escalation rules.
- Agent/report content crosses an LLM trust boundary. The security-reviewer
  brief must receive the relevant `security-checklists` LLM/agent module.

## Construction tests

**Integration tests:** focused pytest over a new core pack contract test and the
existing work-loop tests; existing pack/build projection tests through
`make build-self`; work-loop eval JSON validation; then the repository's lint,
build-check, and CI-equivalent gates allowed by the enterprise environment.

**Manual verification:** run three synthetic raw reports against an unchanged
fixture target: one true finding, one false positive, and one missing-authority
case. Capture raw and adjudication reports by path, inspect only the main-loop
result slice, and confirm the loop receives respectively a sustained finding,
clean, or an indeterminate stop while the complete audit stays recoverable from
the artifact.

## Design (LLD)

### Design decisions

- **A gateway, not a fourth lens.** The adjudicator is invoked for every
  completed reviewer report before the controller classifies it. It may test
  and filter the claims the report contains but may not walk the target for
  additional defects. This preserves the three-lens ceiling and makes
  disagreement structurally independent from both reviewer and implementer.
- **Path-fed, result-sliced context boundary.** Artifact-capable harnesses route
  reviewer output directly under `.context/reviews/`; other harnesses persist it
  there immediately after the unavoidable one-time transport crossing. The main
  loop never reasons over, repeats, or reloads raw prose. It gives the adjudicator
  only the artifact path and consumes only the adjudication report's main-loop
  result after that response is persisted.
- **Orchestrator-owned path authority.** Report paths come only from the
  orchestrator's ignored `.context/reviews/` root, never from reviewer prose. A
  pure-stdlib pre-dispatch validator rejects non-regular, symlinked, escaping,
  oversized, unreadable, or invalid-UTF-8 artifacts without printing report
  bodies. It accepts no arbitrary report path: it constructs the expected
  location solely from orchestrator-owned run, round, review-stage,
  reviewer-role, and artifact-kind metadata. Report-cited paths therefore
  cannot select an artifact or widen the authorized target set.
- **Reuse the parser behind explicit boundaries.** Only sustained findings use
  the existing bold-numbered, line-anchored grammar. Full mode uses strict
  `review inspect --adjudication`; direct-light uses the same parser through a
  state-free strict `review classify` command. The flagless inspect behavior
  remains for legacy callers, and direct-light creates no cohort state.
- **Asymmetric uncertainty.** Refutation requires contrary evidence;
  sustainment requires evidence for every load-bearing predicate. Missing
  evidence produces `indeterminate`, never an optimistic clean or speculative
  fix.
- **Automatic adjudication.** Invocation does not depend on the implementer
  objecting, on a severity cutoff, or on the controller first deciding whether
  a report is clean. Every reviewer report is adjudicated; ordinary mode rules
  run only after the adjudicator returns its bounded main-loop result.

### Data & schema

No durable schema changes. Two existing session artifacts are paired by naming
or orchestration metadata:

1. `raw-review-report` — opaque output from one reviewer pass.
2. `adjudication-report` — main-loop result plus refuted and indeterminate audit
   sections.

Each adjudication entry carries the source reviewer role and finding ordinal,
verdict, tested predicates, repository evidence, authority, and either smallest
adequate fix, broken predicate, or missing evidence/owner choice. The main-loop
result is one of:

- numbered sustained findings in existing reviewer format;
- exact `Clean — ready to commit.` when all source findings are refuted; or
- `ADJUDICATION-INDETERMINATE` with source IDs and no clean sentinel.

### Interfaces & contracts

The orchestrator brief to `finding-adjudicator` supplies:

- `raw_report_path`;
- `target_paths` and structural review scope;
- reviewer role and review stage;
- spec/plan paths and the applicable rubric/checklist paths or inlined slices;
- the unchanged project-knowledge envelope or named skip, if the reviewer used
  one.

`raw_report_path` is derived as
`<repo>/.context/reviews/<run-id>/<round>-<review-stage>-<reviewer-role>-raw.md`,
and the paired output path is
`<repo>/.context/reviews/<run-id>/<round>-<review-stage>-<reviewer-role>-adjudication.md`;
none of their segments comes from the report. Each path must already have passed
`review-artifact.py validate` for those metadata fields: confined, regular,
non-symlinked, bounded, readable, and valid UTF-8. The adjudicator itself
enumerates every source finding; the main loop does not parse raw ordinals.
Spec-backed runs reuse the loop run ID and review-round counter. Direct-light
runs generate one fresh ephemeral UUID before the bounded review, use round 1
for the initial pass, and use round 2 only for the permitted Blocker re-review;
this supplies path identity only and creates no cohort state. Run IDs must be
UUIDs, rounds positive integers, review stages the closed
`pre-execute | post-gates` enum, reviewer
roles satisfy AC2's canonical reviewer-role grammar, and artifact kinds use
closed enum values.

After artifact validation, direct-light runs the state-free strict
`loop-cohort review classify --report <adjudication-path> --json` command before
any clean, apply, defer, or escalation decision. It shares the adjudication
envelope parser with full mode but performs no state read, stasis comparison,
fingerprint history write, or retry mutation.

The adjudicator reads repository instructions, the target, and authority itself.
It returns a report with `## Main-loop result`, `## Refuted audit`, and
`## Indeterminate audit`. The work-loop persists that response. Spec-backed
runs check it through strict cohort inspection; direct-light uses only the
state-free strict classifier. Both branches stop on indeterminate output before
any disposition. Only when a sustained finding reaches FIX does the loop load
that finding's bounded detail from the adjudication report.

### Component / module decomposition

- `packs/core/.apm/agents/finding-adjudicator.md` — independent evidence test,
  prompt-injection boundary, verdict and output contract.
- `packs/core/.apm/skills/work-loop/scripts/review-artifact.py` — non-printing,
  stateless pre-dispatch path/content-shape validator for ignored session reports.
- `packs/core/.apm/skills/work-loop/SKILL.md` — post-GATES report routing,
  artifact-path dispatch, result routing, specialist parity, termination, and
  FIX wording.
- `packs/core/.apm/skills/work-loop/references/pre-execute-review.md` — the same
  gateway at the spec/plan stage.
- `packs/core/tests/pack/test_finding_adjudication_contract.py` — source and
  orchestration construction tests.
- `packs/core/.apm/skills/work-loop/evals/evals.json` — three outcome fixtures.
- core manifests, spec index, and product changelog — delivery surfaces.

### State & control flow

```text
reviewer -> raw report artifact -> finding-adjudicator -> adjudication artifact
                                                       |
               +------------------+--------------------+
               |                  |                    |
           sustained           refuted            indeterminate
               |                  |                    |
        main loop / cohort    clean if all        Surface and stop
        -> DECIDE -> FIX      all source refuted  before mutation
```

The raw report and refutation prose never enter DECIDE or FIX. Existing cohort
retry and stasis accounting begins only at the sustained branch. A refuted-only
round records the adjudication clean result through the existing clean path; it
does not increment the findings retry counter.

### Behavior & rules

- Every reviewer report is dispatched before the controller classifies it as
  clean or finding-bearing. The adjudicator enumerates every source finding;
  ordinary work-loop mode rules run only after it confirms which findings are
  sustained.
- The adjudicator tests: cited observation exists; named authority is current
  and applies; execution/data path is reachable; existing handling does not
  already satisfy the rule; claimed consequence follows at the reported
  severity. It separates a valid issue from an over-broad fix.
- In light mode, sustained non-Blockers keep the existing bounded `apply` /
  `defer` handling, but only after the adjudicator confirms the finding is real.
- A malformed raw report, missing authority, unreadable target, or conflicting
  standards cannot yield clean. The adjudicator returns indeterminate with the
  precise missing input.
- A missing adjudicator blocks every completed reviewer report. It is not
  equivalent to the existing optional-reviewer named-skip behavior.

### Failure, edge cases & resilience

- **Reviewer prompt injection:** report text is quoted data; embedded tool or
  scope directives are ignored and noted if relevant to the verdict.
- **Path redirection:** reviewer text cannot choose the raw report path or add
  target paths. The validator has no arbitrary path option and derives the
  artifact from orchestrator metadata; it stops non-regular, symlinked, escaping,
  oversized, unreadable, invalid-UTF-8, or unavailable artifacts before
  adjudication and emits no report content or path.
- **Stale target:** if target evidence differs from what the report cites, test
  the current target and identify the mismatch; use indeterminate when the
  intended review revision cannot be established.
- **Mixed true/false report:** sustain and forward only valid entries; refute
  others in the audit. Cohort fingerprints only the sustained subset.
- **Wrong fix, valid issue:** sustain the issue but replace the proposed fix
  with the smallest adequate correction, explicitly recording why the original
  prescription was over-broad.
- **Duplicate cross-reviewer finding:** adjudicate each source claim against the
  same evidence, then retain existing work-loop deduplication for sustained
  overlaps.
- **Artifact unavailable after context eviction:** stop and surface; never ask
  the main loop to reconstruct the raw report from memory or tool history.

### Quality attributes (NFRs)

- **Context efficiency:** the main loop consumes paths, bounded status, and
  sustained detail only when fixing; raw and refuted prose do not remain resident.
- **Auditability:** every filtered claim has a paired source ID, verdict,
  evidence, and reopen condition or missing-input statement.
- **Neutrality:** the prompt contains symmetrical sustain/refute burdens and no
  target refutation rate.
- **Portability:** the source grants only `Read` and `Grep`. Claude Code, Kiro
  IDE, Kiro CLI, Copilot, and Gemini retain exact read/search allowlists. Codex
  and Cursor reduce that intent to native coarse-grained read-only controls, so
  dispatch on those adapters also requires the active managed permission
  profile to withhold mutation, shell, web, MCP, skill, and recursive-dispatch
  capabilities. No runtime, dependency, or adapter-contract change is planned.
- **Fail-closed behavior:** malformed, missing, stale, or conflicting evidence
  cannot become clean.

### Dependencies & integration

The new agent uses the existing agent primitive and projection routes. The
work-loop supplies repository-local authority and inlines any progressive
security depth; the agent does not self-discover skills. The validator is a
stdlib-only sibling script under the existing work-loop skill and carries no
state; `loop-cohort.py` and its state schema remain unchanged. Core pack source
manifests receive the new primitive's minor version bump, and self-host
regenerates target-runtime projections.

AC16 is the canonical seven-adapter projection matrix. The focused construction
test projects the real source file through each named adapter rather than
testing mapping tables in isolation. The deprecated `kiro` alias inherits
AC16's Kiro IDE assertion and is not counted as an eighth independent adapter.

## Tasks

### T1: Build the report-artifact validation boundary

**Depends on:** none

**Tests:**
- `stub: true`
- TDD (AC2, AC9, AC12, AC15): valid regular UTF-8 input under `.context/reviews/`
  succeeds; outside-root, symlink, FIFO/special file, oversized, unreadable,
  invalid-UTF-8, and unavailable inputs fail before dispatch; the CLI exposes no
  arbitrary report-path option, and invalid run/round/stage/role/kind metadata
  fails.
- TDD privacy check: success and every refusal reveal no report body or path;
  fixed status tokens, size, digest, and exit codes are the
  complete output surface.

**Materialized red stub:**
`packs/core/tests/pack/test_finding_adjudication_contract.py` compiles now and
is red because the validator does not exist. EXECUTE starts from that file and
fills out the remaining negative cases named above before green. Its test
functions carry the required `# STUB: AC...` markers.

**Approach:**
- Add a pure-stdlib `review-artifact.py validate --root <repo> --run-id <id>
  --round <n> --review-stage <pre-execute|post-gates> --reviewer-role <slug>
  --kind <raw|adjudication>` sibling script with a fixed size ceiling and no
  state mutation. It constructs the expected path rather than accepting one.
- Resolve the repository and `.context/reviews/` roots, use no-follow metadata
  checks before a bounded UTF-8 read, and keep diagnostics enumerated and generic.

**Done when:** the validator's falsification suite is green and the command
cannot be used to echo, follow, or validate a report outside the session root.

### T2: Add the `finding-adjudicator` contract and construction tests

**Depends on:** T1

**Tests:**
- Goal-based (AC1-AC5, AC12): add a failing source-contract test for exact
  `Read, Grep` tools, collision-hardened metadata, three verdicts, five
  predicates, all-finding enumeration, no-new-findings rule, untrusted-data
  boundary, exact clean and indeterminate signals, and parse-safe
  sustained-only numbered output.
- Goal-based security check (AC2, AC4): assert report content cannot alter
  instructions, tools, scope, severity rules, or verdict rules, and the agent
  cannot edit, run shell commands, or dispatch work.
- Cross-adapter construction (AC16): project the actual source agent through all
  seven supported adapters and assert AC16's canonical matrix. Fail on an omitted or
  widened restriction; record Codex and Cursor as coarse projections rather
  than pretending they preserve named-tool parity.

**Approach:**
- Create `packs/core/.apm/agents/finding-adjudicator.md` with a neutral mandate,
  context-loading order, evidence predicate table, verdict burden, and report
  template.
- Restrict it to `Read, Grep`; explicitly forbid mutations, shell/web
  execution, new findings, self-generated follow-on work, and recursive dispatch.
  The orchestrator supplies report, target, and authority paths. When those
  paths plus content search cannot establish a predicate, including a
  filename-only or absence claim, require `indeterminate` with the missing
  verification named.
- Add the focused pack test before filling the agent body, then make it green.

**Done when:** the focused contract test passes and a manual read confirms the
agent can disagree with either reviewer or implementer without optimizing for a
particular verdict.

### T3: Route pre-EXECUTE and post-GATES findings through the gateway

**Depends on:** T1, T2

**Tests:**
- `stub: true`
- Goal-based (AC6-AC10, AC12): extend the focused test to assert both review
  stages route every report through path-based adjudication before clean/finding
  classification, fingerprint/DECIDE/FIX; all-finding routing and specialist
  parity exist; missing adjudicator and indeterminate are loud stops; only
  adjudicated sustained reports reach cohort inspection.
- TDD (AC7, AC9, AC12): the state-free direct-light classifier accepts a valid
  sustained result and the exact clean sentinel, while malformed envelopes and
  indeterminate outcomes stop without requiring or creating cohort state.
- Goal-based context check (AC9): assert the work-loop says raw reports are
  opaque, passed by path, not pasted into the brief, and evicted before the main
  result is consumed.

**Approach:**
- Amend `pre-execute-review.md` immediately before its iterate-to-clean branch.
- Amend `work-loop/SKILL.md` after each warranted reviewer report and before
  `review inspect`; validate the raw path, dispatch by path, then replace the
  direct raw-report path in documented cohort commands with the adjudication path.
- Add a state-free strict `review classify` command that reuses the same
  adjudication-envelope parser and require it before every direct-light
  disposition.
- Update DECIDE, termination, and FIX language so retry/stasis accounting and
  repairs reference sustained findings only while the existing FSM stays intact.

**Done when:** construction tests prove there is no documented path from a raw
reviewer finding to fingerprinting, DECIDE, or FIX.

### T4: Add falsification evals and run manual context-boundary QA

**Depends on:** T3

**Tests:**
- Goal-based (AC11): add three eval entries for sustained, refuted-only, and
  indeterminate outcomes; validate the eval JSON with existing pack tooling.
- Manual QA (AC3-AC5, AC9-AC11): run the three synthetic report fixtures and
  record the bounded main-loop result plus artifact paths in an implementation
  note or PR evidence.

**Approach:**
- Use one small repository fixture target and vary only the finding's evidentiary
  status so the verdict, not fixture complexity, is what changes.
- Include an over-broad proposed fix in the true-finding case to verify the agent
  can sustain the issue while rejecting the prescription.
- Confirm no refuted reasoning appears in the main-loop result slice and no
  indeterminate case contains the clean sentinel.

**Done when:** all three expected routes are evidenced and the main loop's
consumed content contains no raw or refuted finding prose.

### T5: Ship the core primitive and generated projections

**Depends on:** T1, T2, T3, T4

**Tests:**
- Goal-based (AC13, AC14, AC16): core manifest versions match AC13's canonical bump,
  the canonical versioned changelog entry, its NOW highlight, and the spec index
  mention finding adjudication, and no
  adapter-contract version or dependency changes; the seven-adapter matrix is
  green or any coarse projection stops under a widening managed profile.
- Integration (AC13, AC14): `make build-self`, focused core-pack pytest,
  `make lint-ruff`, `SKIP_SAST=1 make build-check`, and the applicable CI-equivalent
  suite pass under the managed enterprise profile.

**Approach:**
- Apply AC13's canonical minor bump to `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json`.
- Add the canonical top-level versioned core release entry, its NOW highlight,
  and the active-spec index entry.
- Regenerate projections from `.apm` source and inspect Git diff for unexpected
  generated or unrelated changes; do not stage or commit in this environment.

**Done when:** source and generated surfaces agree, all runnable gates are green,
and only intended changes remain in the worktree.

## Rollout

Ship as a core minor release. The control activates after each completed
`work-loop` reviewer pass; it adds no user command, data migration, runtime
service, or persistent schema. Rollback is a source revert of the agent,
routing prose, tests/evals, version bump, and projections. Because the
missing-adjudicator path is fail-closed for every reviewer report, adopters
with stale partial projections receive a loud stop rather than silently reverting
to trust.

## Risks

- **The platform cannot keep raw subagent output out of the controller's token
  window.** Mitigation: the portable contract remains path-first and instructs
  immediate persistence/eviction; the main loop never reasons over or repeats raw
  prose. The final QA records actual behavior on the available harness.
- **The adjudicator becomes a covert fourth reviewer.** Mitigation: agent and
  tests prohibit new findings, checklist walks, and scope widening; it can only
  classify enumerated source findings.
- **False refutation becomes the new blind spot.** Mitigation: symmetrical
  evidence predicates, `indeterminate` fail-closed outcome, paired audit, and
  manual falsification cases. No target refutation rate or agreement metric.
- **Parser accidentally fingerprints refuted audit entries.** Mitigation: only
  sustained entries use the parser's numbered finding grammar; strict full-mode
  inspection and state-free direct-light classification reject malformed audit
  sections in construction tests.
- **Sequential adjudication adds latency.** Mitigation: batch all source
  findings from one reviewer pass into one adjudicator invocation; do not create
  one agent call per finding.

## Changelog

- 2026-08-23: initial plan, including the owner's no-RFC approval and the
  context-conserving path-first review gateway.
- 2026-08-23: approved replan adds state-free strict adjudication classification
  for direct-light without cohort state.
