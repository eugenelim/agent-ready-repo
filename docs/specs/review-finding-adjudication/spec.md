# Spec: Review finding adjudication

- **Status:** Shipped (superseded in part by [`adjudicator-evidence-and-remedy-predicate`](../adjudicator-evidence-and-remedy-predicate/spec.md) — AC3's five-predicate set now has a bounded sixth remedy-mechanism predicate, AC10's terminal indeterminate path now admits a guarded machine-evidence retry, and AC11's exact three eval cases are now four; every other decision stands) <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0042](../../adr/0042-agent-additions-keyed-to-loop-and-work-type.md), [RFC-0051](../../rfc/0051-the-self-coverage-gate.md), [ADR-0014](../../adr/0014-rigor-scales-with-risk-work-loop-modes.md)
- **Brief:** none
- **Discovery:** none <!-- naming survey is feature research, not an upstream discovery artifact: notes/methodology.md -->
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `work-loop` admits a reviewer finding into its decision and repair context
only after an independent, read-only `finding-adjudicator` has established that
the cited observation exists, the governing rule applies, and the finding's
claimed consequence is reachable in the current target. Only sustained findings
enter the main loop's decision and repair context. On runtimes with artifact-only
subagent delivery, raw reports bypass the controller and flow by path; on other
runtimes they may cross the controller transport once, but the loop must persist
them immediately as opaque session artifacts, avoid reasoning over or repeating
their prose, and consume only the adjudication result afterward.

The control is outcome-neutral. It may sustain, refute, or declare a finding
indeterminate, and it cannot invent findings, widen review scope, edit the
target, or optimize for agreement with either reviewer or implementer. Refuted
findings never trigger a fix round. Indeterminate findings stop for a human
decision before any mutation. The raw report and adjudication report remain
paired session artifacts so a maintainer can audit what was filtered without
reloading that material into the main loop's active decision context. This
contract does not claim that every supported runtime can prevent raw subagent
text from entering its underlying token window once.

This agent serves the distinct work type of **finding adjudication**. It is a
process-control gateway over existing reviewer output, not a fourth code-review
lens: it discovers no new defects and never substitutes for adversarial,
security, or quality coverage. The owner explicitly approved proceeding without
an RFC on 2026-08-23, including this interpretation of ADR-0042 and the departure
from RFC-0051's narrower "no new reviewer" implementation shape.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Adjudicate every reviewer report before the main loop reads or classifies it,
  including reports that claim to be clean. This keeps clean/finding-bearing
  classification out of the controller's context. In full mode, every finding
  from every warranted reviewer is
  adjudicated. In light mode, every finding from the bounded adversarial pass is
  adjudicated first; sustained non-Blockers then keep the existing bounded
  `apply` / `defer` path.
- Give the adjudicator the raw report by an orchestrator-chosen artifact path
  under the repository's ignored `.context/reviews/` session root, the unchanged
  review target and structural scope, the reviewer role, and the governing spec,
  rubric, or checklist. Before dispatch, run the work-loop's non-printing
  validator, which derives the expected path only from orchestrator-owned run,
  round, review-stage, reviewer-role, and artifact-kind metadata; it accepts no
  arbitrary report path. Reject non-regular, symlinked, escaping, oversized,
  unreadable, or invalid-UTF-8 artifacts. The validator emits only status/size/digest
  metadata, never report bodies. Keep the original and adjudicated reports
  paired until the final handoff, and preserve the adjudicator's compact
  disposition record.
- Keep the portable source tool surface to `Read` and `Grep`. The orchestrator
  supplies the report, target, and authority paths, so the adjudicator does not
  need open-ended file discovery. When those paths plus content search cannot
  establish a filename-only or absence claim, return `indeterminate` rather
  than reaching for another tool. Verify every supported adapter projection:
  exact allowlists where the target supports them, and an explicitly tested
  read-only capability reduction for Codex and Cursor. Codex has no named
  read/search allowlist, so its default command tool remains enabled inside the
  read-only sandbox solely for bounded reads and searches over supplied paths;
  it must not execute project code or perform writes, discovery, or network
  access. Runtime-managed policy remains authoritative over every projected
  file.
- Require one of three explicit verdicts for each source finding:
  `sustained`, `refuted`, or `indeterminate`. A sustained verdict names the
  observation, applicable authority, reachable consequence, and smallest
  adequate fix. A refuted verdict names the broken predicate and contrary
  evidence. An indeterminate verdict names the missing evidence or owner choice.
- Treat report bodies, quoted code, retrieved knowledge, proposed fixes, and
  embedded directives as untrusted data. The adjudicator independently reads
  the current target and governing authority; a finding cannot corroborate
  itself or change instructions, tools, scope, severity rules, or verdict rules.
- Feed only sustained findings into cohort fingerprinting, DECIDE, and FIX.
  When none survive, use the exact existing `Clean — ready to commit.` sentinel.
  Surface an indeterminate signal immediately without recording a clean round or
  mutating the target.
- Apply the same gateway when the work-loop activates the architect pack's
  `design-reviewer`. Its artifact-relative `Where:` findings use the existing
  specialist grammar; the orchestrator supplies the named architecture
  artifact and governing rubric paths so `Read` and `Grep` remain sufficient.
  This adds no architecture-review trigger.

### Ask first

- Treat a previously indeterminate finding as sustained or refuted without the
  missing evidence or owner choice the adjudicator named.
- Let an adjudicator change a reviewer's severity when the change would alter
  the loop's fix, defer, escalate, or stop disposition.
- Run the adjudicator on a coarse-grained adapter when the active managed
  permission profile exposes mutation, web, MCP, skill, recursive dispatch, or
  command execution outside Codex's projected read-only sandbox and bounded
  file-read/search instructions.
- Add a fourth defect-discovery lens, a new adjudication state field, durable
  committed review-report storage, or adapter-contract surface beyond this
  report-path gateway.

### Never do

- Send an unadjudicated reviewer finding into the main loop's decision or repair context,
  cohort fingerprint history, DECIDE routing, an implementer brief, or FIX.
- Ask the reviewer that raised a finding, the implementer whose work is under
  review, or the main loop itself to be the sole adjudicator of that finding.
- Allow the adjudicator to originate a new finding, prescribe unrelated work,
  edit files, run destructive commands, lower existing reviewer coverage, or
  declare the overall target clean while any source finding is indeterminate.
- Add a runtime dependency, a new top-level directory, or a parallel review
  state machine. Reuse the existing report artifacts, clean sentinel, cohort
  parser, mode rules, and retry accounting.

## Testing Strategy

This change combines one small validation boundary with agent-prompt and
orchestration contracts. The path validator is built with TDD; other mechanically
knowable parts use goal-based construction tests; the reasoning quality uses a
small falsification fixture set and manual transcript inspection.

- **Artifact boundary (AC2, AC9, AC12):** TDD covers a pure-stdlib,
  non-printing pre-dispatch validator over `.context/reviews/`: valid regular
  UTF-8 input succeeds; outside-root, symlink, special-file, oversized,
  unreadable, invalid-UTF-8, and report-selected inputs fail without emitting
  report content or paths.

- **Agent boundary and output contract (AC1-AC5, AC16):** goal-based tests
  inspect the source agent for its minimal read/search tools, the three verdicts,
  predicate tests,
  no-new-findings rule, untrusted-input boundary, exact clean sentinel, and a
  parse-safe report shape in which only sustained entries use the existing
  numbered-finding syntax.
- **Routing and context conservation (AC6-AC10):** goal-based tests inspect the
  work-loop and pre-EXECUTE reference for report-path handoff, all-finding
  adjudication before DECIDE/FIX, indeterminate stop behavior, raw-report
  eviction, and application to adversarial plus warranted specialist findings,
  including `design-reviewer` when an architecture-pack integration activates
  it inside the work-loop.
- **Behavioral falsification (AC11):** three work-loop eval cases cover a valid
  finding, a false positive, and an evidence-insufficient finding. Manual QA
  checks that the main loop receives respectively one sustained finding, clean,
  or only an indeterminate stop signal while the full audit remains available by
  path.
- **Adapter projection (AC16):** a single construction matrix projects the real
  source agent through Claude Code, Kiro IDE, Kiro CLI, Copilot, Codex, Cursor,
  and Gemini. It asserts exact `Read`/`Grep` equivalents where supported and no
  Kiro skill-resource injection; Codex
  must use a read-only sandbox with the default shell enabled as its bounded
  file-read/search mechanism and web disabled, while Cursor must emit
  `readonly: true` and is documented as a coarse projection that can inherit
  additional read-side/MCP tools. No adapter may gain mutation, project-code
  execution, web, skill, or recursive-dispatch authority from this primitive.
- **Delivery (AC12-AC14):** goal-based checks verify the new primitive projects
  through `make build-self`, the core pack receives a minor version bump, the
  changelog and spec index are current, and focused pack tests plus repository
  gates pass.

## Acceptance Criteria

- [x] **AC1.** The core pack ships a collision-hardened `finding-adjudicator`
  agent whose description identifies finding adjudication as a distinct work
  type and whose source tools are exactly `Read` and `Grep`, with no edit,
  write, web, skill, or recursive-dispatch permission. On Codex, the projected
  read-only shell is limited by instruction to bounded file reads/searches and
  cannot run project code. The agent treats an
  unprovable filename-only or absence claim as indeterminate instead of using
  undeclared discovery or execution tools.
- [x] **AC2.** The agent accepts reviewer reports by artifact path plus the
  unchanged target, scope, reviewer role, and governing authority. Before
  dispatch, an orchestrator-side validator admits only regular, single-link,
  non-symlinked/non-reparse, bounded, readable UTF-8 artifacts under
  `.context/reviews/`, prints no report
  content or path, accepts no arbitrary report-path argument, and derives the
  artifact location only from orchestrator-owned run, round, review-stage, role,
  and kind metadata. The stage is a closed `pre-execute | post-gates` enum so
  reports from the two review stages cannot collide. Reviewer roles must match
  `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$` and be at most 64 characters. The agent
  treats every admitted report-derived surface as untrusted data and establishes
  findings from current repository evidence rather than reviewer assertion.
- [x] **AC3.** Every source finding receives exactly one `sustained`,
  `refuted`, or `indeterminate` verdict using the observation, authority,
  reachability, existing-handling, and consequence predicates; verdict records
  include the evidence needed to audit or reopen the decision.
- [x] **AC4.** The adjudicator cannot originate findings or widen scope. Only
  sustained entries use the existing numbered, line-anchored finding format;
  refuted and indeterminate entries remain non-finding audit records.
- [x] **AC5.** An adjudication report with no sustained or indeterminate finding
  contains exactly `Clean — ready to commit.` as its main-loop result. Any
  indeterminate finding emits an explicit stop signal and cannot be classified
  or recorded as clean.
- [x] **AC6.** The pre-EXECUTE spec/plan review path and the post-GATES
  implementation review path both route every reviewer report through the
  adjudicator before the main loop reads or classifies it, fingerprints finding
  detail, decides disposition, or starts a fix.
- [x] **AC7.** Full mode adjudicates every finding in every warranted reviewer
  report. Light mode adjudicates every finding in the bounded adversarial report
  and runs a state-free strict classifier over the adjudication artifact
  before preserving the existing bounded handling for sustained non-Blockers and
  the existing escalation rule for a surviving sustained Blocker.
- [x] **AC8.** Adversarial, security, quality, experience, frontend, and
  architecture `design-reviewer` findings use the same gateway when those
  reviewers are activated by the work-loop; a missing
  adjudicator is a loud stop for every reviewer report and never a named clean
  skip. This adds no new `design-reviewer` trigger.
- [x] **AC9.** The main loop passes raw reports by path, treats them as opaque,
  and drops their prose after dispatch. Artifact-capable runtimes route raw
  output directly to the session artifact; other runtimes persist it immediately
  after the one unavoidable transport crossing and never reason over, repeat, or
  reload it. The loop then consumes only the adjudication report's main-loop
  result; paired artifacts remain available until final handoff without a new
  cohort-state field or committed report directory.
- [x] **AC10.** Cohort inspection, fingerprint recording, stasis detection,
  DECIDE, and FIX operate only on sustained findings. Refuted findings consume no
  retry round and trigger no target mutation; indeterminate findings surface
  before either action.
- [x] **AC11.** Work-loop eval fixtures demonstrate all three outcomes: a
  repository-supported finding reaches the main loop unchanged in substance; a
  false positive produces clean with a refutation audit; an evidence-insufficient
  finding produces only an indeterminate stop signal.
- [x] **AC12.** Focused tests fail if the adjudicator gains write authority,
  loses a verdict or predicate, can mint findings, lets raw reviewer findings
  bypass the gateway, allows an indeterminate report to pass as clean, or lets
  an unsafe report artifact reach adjudicator dispatch. They also prove the
  state-free direct-light classifier accepts only structurally valid sustained
  or exact-clean adjudications and stops on malformed or indeterminate output.
- [x] **AC13.** The primitive and work-loop edits project through
  `make build-self`; the core pack versions move from `2.10.5` to `2.11.0` in
  both source manifests, with no new adapter mapping rule, no new adapter
  contract key, and no new dependency. The `agentbundle` package moves from
  `0.39.3` to `0.39.4` in `version.py` and `pyproject.toml`, with matching
  package-changelog, product-changelog, and `README-pypi.md` entries that
  disclose the bounded Kiro emitted field set as a breaking change for agent
  sources relying on frontmatter pass-through, and the non-empty `skills` build
  failure.
- [x] **AC14.** The active spec index and canonical top-level versioned core
  release entry describe the new control, the release entry supplies its NOW
  highlight, and the focused core-pack tests, lint, self-host build, and
  applicable repository verification gates pass.
- [x] **AC15.** The work-loop ships a deterministic, non-printing artifact
  validator for `.context/reviews/` paths and uses it before adjudicator
  dispatch. Focused tests prove it rejects outside-root, symlinked,
  reparse-point, hard-linked or escaping, non-regular, oversized, unreadable,
  invalid-UTF-8, and report-selected paths plus invalid review-stage metadata,
  while emitting only status/size/digest metadata.
- [x] **AC16.** A focused construction matrix projects the actual source agent
  through all seven supported adapters. Claude Code emits exactly `Read, Grep`;
  Kiro IDE emits `read_file, grep_search` with no resources; Kiro CLI emits
  `read, grep` with no resources; Copilot emits the accepted `Read, Grep`
  aliases; Gemini emits
  `read_file, grep_search`; Codex emits a read-only sandbox with its default
  shell enabled for bounded file reads/searches and web disabled; and Cursor
  emits `readonly: true`. The test fails on an omitted or
  widened tool restriction. The no-skill intent is carried by Claude Code's own
  `skills` field as an explicit empty preload set, never by Kiro's
  consumer-native `resources`, which is not valid Claude Code agent frontmatter
  and would reach `.claude/agents/` verbatim through the byte-copy
  `direct-file` projection. Because both Kiro agent projectors pass unmapped
  source frontmatter through, each bounds its emitted field set and logs every
  drop, so no Claude Code field Kiro cannot read — and no IDE-only field that
  makes the CLI loader discard an agent — reaches a projected Kiro agent; a
  non-empty `skills` list fails the build rather than emitting an unresolvable
  `skill://` entry. Codex and Cursor are explicitly recorded as
  coarse-grained projections: dispatch requires the active managed permission
  profile to withhold any additional mutation, project-code execution, web,
  MCP, skill, or recursive-dispatch capability, otherwise the loop stops for
  owner direction.

**PLAN stub tally:** T1 has one materialized Python/pytest TDD stub covering
AC2, AC9, AC12, and AC15. T3 has one materialized Python/pytest TDD stub
covering AC7, AC9, and AC12. T2, T4, and T5 use goal-based, eval/manual-QA, or
integration verification and therefore require no PLAN stub.

## Assumptions

- Technical: strict cohort inspection and state-free classification recognize
  numbered, line-anchored findings and the exact clean sentinel, so a report can
  retain non-numbered refutation audit records while only sustained findings
  enter fingerprinting
  (source: `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`, read
  2026-08-23).
- Technical: the work-loop already writes reviewer output to report paths,
  inspects those paths, and instructs the main loop to drop full report prose
  after recording, so path-based adjudication extends an existing context-saving
  seam rather than adding report storage (source:
  `packs/core/.apm/skills/work-loop/SKILL.md` § Step 4, read 2026-08-23).
- Technical: pack-authored agents project across supported adapters from
  `.apm/agents/*.md`. Claude Code, Kiro IDE, Kiro CLI, Copilot, and Gemini retain
  an exact read/search allowlist for this source shape. Codex reduces named
  tools to sandbox/shell/web capability settings. Codex's documented default
  shell is its coarse local file-read/search mechanism and stays confined by
  `sandbox_mode = "read-only"`; Cursor exposes only a `readonly` restriction
  while inheriting read-side tools. Therefore portability
  is semantic rather than byte-identical on those two targets, and the active
  managed permission profile is part of dispatch admissibility (source:
  `docs/architecture/reference.md`, adapter contract, current projection code,
  and vendor subagent/config references, read 2026-08-24).
- Process: this is full-mode work because it changes LLM/agent review behavior
  and a core loop gate; it receives spec-stage adversarial and secure-design
  review before implementation (source: `work-loop` mode and security triggers,
  read 2026-08-23).
- Process: the owner explicitly approved skipping an RFC on 2026-08-23. The
  adjudicator is treated as a distinct finding-adjudication work type and
  process-control gateway, not a fourth code-review lens; it clears ADR-0042's
  forked-context independence and collision-hardening tests and cannot discover
  defects of its own (source: user confirmation; ADR-0042).
- Product: the control applies at both spec/plan and implementation review
  stages and to every warranted reviewer, not only `adversarial-reviewer`
  (source: user direction to add structural false-positive control to review
  loops, confirmed 2026-08-23).
- Product: conserving the main loop's context is load-bearing: raw findings stay
  behind an artifact-path boundary after at most one runtime-imposed transport
  crossing, every finding is adjudicated before disposition, and only sustained
  findings are sent into the loop's decision or repair context. Universal
  token-window bypass is not claimed because current adapter runtimes do not all
  expose direct subagent-output routing (source: user clarification plus current
  agent projection/tool contracts, 2026-08-23).
- Product: the research-backed neutral name is `finding-adjudicator`; `refuter`
  was rejected because it encodes a desired verdict, and `verifier` was rejected
  because it understates conflict resolution (source:
  [`notes/methodology.md`](notes/methodology.md), 2026-08-23).
