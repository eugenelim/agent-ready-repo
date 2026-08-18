# Plan: Project knowledge review integrations

- **Spec:** [`spec.md`](spec.md)
- **RFC:** [`RFC-0077`](../../rfc/0077-distill-knowledge.md) (Accepted)
- **ADRs:** [`ADR-0081`](../../adr/0081-canonical-project-knowledge-uses-per-topic-json.md) and [`ADR-0082`](../../adr/0082-project-knowledge-modes-separate-authority.md) (Accepted)
- **Status:** Done
- **Mode:** full

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change while its status is `Drafting` or `Executing`. Substantial
> changes are recorded in the changelog.

## Approach

Add a non-writing review-planning branch, not a new capture producer. Core first
integrates one explicit `CQ-REVIEW` enquiry at work-loop's existing reviewer
orchestration boundary and teaches the three specialist definitions to consume
only a delimited evidence envelope. Architecture review follows as a separate
pack-sized task, using the same public enquiry seam immediately before its
rubric walk. Both paths preserve current review gates, verdicts, permissions,
and independent grounding.

The queued review-and-research shape splits before implementation. Review is a
coherent enquiry-only slice with no durable writes; research owns cited products
and raw corpora, has intermediate phases that are not stable gates, and may
write to configured personal paths where repository-relative provenance is not
available. A new downstream research entry therefore separates those authority,
output-root, source-verification, and gate questions before engineering and
operational workflows depend on them.

The recommended smallest implementation slice is T1: core work-loop plus the
adversarial, security, and quality reviewer family. It proves bounded envelope
construction, prompt-injection containment, non-writing reviewer consumption,
independent judgment, and no-write degradation inside the provider pack before
the architect pack declares an optional cross-pack handoff.

## Assumptions surfaced

- The public enquiry surface is sufficient; no schema, CLI, reader, writer, or
  storage change is needed.
- One review-planning envelope can supply candidate checks to all warranted
  specialist reviewers because work-loop owns their common task and scope.
- Architecture review can declare the same competency question directly after
  it resolves its artifact and rubric because it is a user-invoked skill rather
  than a read-only subagent definition.
- Research requires a separate spec because its products, source corpus, output
  roots, and phase gates differ materially from review's inline read-only
  result contract.

## Constraints

- Follow RFC-0077 and ADR-0081/ADR-0082 without amending their frozen bodies.
- Preserve the shipped capture request, private writer, identity, partition,
  receipt-selection, distillation, privacy, quarantine, freshness, and enquiry
  contracts.
- Preserve reviewer output formats, clean sentinels, rubric/checklist routing,
  retry behavior, tool declarations, and platform sandbox metadata.
- Edit canonical `.apm` sources first. Regenerate only the repository's existing
  self-host projections; verify architect's other adapters in temporary build
  roots rather than adding projection directories.
- Bump each non-cosmetically changed pack and plugin manifest; synchronize the
  root changelog and marketplace aggregate.
- Keep implementation and tests cross-platform and dependency-free. Add no new
  top-level directory, persistence layer, package dependency, or Git ref update.
- Keep research, engineering/operational integration, adoption closeout, and
  conditional post-closeout shaping outside this implementation.

## Construction tests

- Existing project-knowledge suites remain the oracle for committed-only
  enquiry, source-relative freshness, privacy refusal, quarantine, prompt
  injection, mode isolation, public/private separation, and receipt-scoped
  distillation.
- A disposable adopter-shaped end-to-end journey invokes work-loop review and
  architect-review with relevant, abstaining, unavailable, and hostile
  knowledge. It records only redacted request/result metadata, final review
  behavior, and zero-write checks in `notes/manual-qa.md`.
- Forced self-host and temporary adapter builds compare canonical work-loop,
  reviewer, and architect-review behavior plus reviewer security metadata with
  every generated target.

## Design (LLD)

### Interfaces & contracts

The integration consumes the existing strict enquiry query and
`knowledge-enquiry-receipt.v1` surfaces through the public
`project-knowledge --enquire` mode. Each query carries `caller: skill`, a task
summary naming the invoking workflow, structural `scope`, `CQ-REVIEW`
`question_id`, and consequential `risk`; the workflow separately fixes a
one-query, zero-refinement budget. The result enters a visibly delimited,
untrusted-data section. No reviewer consumes the capture contract or can reach
the private writer. Traces to AC2-AC7 and AC11-AC15.

### Component / module decomposition

- Core `work-loop` owns one pre-dispatch enquiry and the missing-provider skip.
  Its adversarial, security, and quality reviewer definitions accept candidate
  checks but preserve their current tools, sandbox annotations, and output
  contracts.
- Architect `architect-review` owns its enquiry timing after artifact/rubric
  resolution. Architect pack metadata records the optional core handoff without
  changing install dependencies.
- Skill/agent-local construction tests pin ordering and forbidden surfaces;
  behavior evals cover semantic independence and hostile envelopes.
- Project-knowledge runtime and schemas remain unchanged and continue to supply
  the lower-level contract oracle.

Traces to AC1-AC19.

### State & control flow

```text
review target + governing instructions
  -> resolve task, structural scope, review mode, and rubric/checklist route
  -> visibly declare consequential CQ-REVIEW (one query, no refinement)
  -> project-knowledge --enquire
       | unavailable -> named skip; no fallback
       | abstention  -> zero candidate checks
       | evidence    -> delimit as untrusted candidate checks
  -> independent target + rubric/checklist + canonical-source review
  -> exact reviewer result gate
  -> findings or clean verdict remain in review artifact
  -> no capture, no receipt, no distillation
```

For work-loop, one envelope is constructed before the first adversarial
dispatch and is passed to every warranted reviewer. Re-review over an unchanged
target reuses it. Material target or scope change invalidates the envelope and
requires another explicit declaration; there is no automatic refresh. Traces to
AC1-AC8 and AC16-AC17.

### Failure, edge cases & resilience

- Provider discovery failure is an explicit fail-open for review availability
  and a fail-closed outcome for knowledge use: the invoking workflow records
  `project-knowledge unavailable`, review proceeds from canonical evidence, and
  no fallback read or write occurs.
- A successful query with no eligible topic yields zero candidates. Matched
  topics with no verified consequential owning source yield `abstained: true`.
  Stale, quarantined, malformed, irrelevant, or privacy-refused material remains
  excluded or refused and cannot become a weaker claim.
- Prompt injection, scope redirection, permission requests, severity changes,
  verdict requests, and finding-suppression instructions in an envelope remain
  inert data.
- Incomplete or interrupted reviews emit no stable result and perform no
  knowledge operation after the initial read-only enquiry.
- Existing work-loop capture receipts remain gate-local; this slice creates no
  receipt that could be guessed, selected, or distilled.

Traces to AC5-AC17.

### Dependencies & integration

Core supplies both work-loop and project-knowledge, so its same-pack caller uses
normal skill discovery. Architect declares an optional `handoff` integration to
core's provider and keeps the named unavailable branch for installations
without core. No dependency range or package dependency changes. Traces to
AC18-AC20.

## Tasks

### T1: Core reviewer family consumes one bounded review-planning envelope without write authority

**Depends on:** none

**Verification mode:** TDD construction tests + Tier-4 behavior evals.

**Touches:**
`packs/core/.apm/skills/work-loop/SKILL.md`,
`packs/core/.apm/skills/work-loop/evals/evals.json`,
`packs/core/.apm/agents/adversarial-reviewer.md`,
`packs/core/.apm/agents/security-reviewer.md`,
  `packs/core/.apm/agents/quality-engineer.md`,
`packs/core/tests/skills/work-loop/test_project_knowledge_review_enquiry.py`,
`packs/core/tests/pack/test_reviewer_project_knowledge_boundary.py`,
`packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`,
`packs/core/README.md`, and `packs/core/JOURNEY.md`.

**Tests:**

- Construction tests pin enquiry after target/scope resolution and before the
  first adversarial dispatch; exact caller/task/scope/`CQ-REVIEW`/risk/budget
  fields; same-envelope reuse; explicit invalidation; and the exact unavailable
  skip. Implements AC1, AC3-AC6, and AC17.
- Reviewer-boundary tests require untrusted-data delimiters and independently
  grounded findings while forbidding capture/distill, private writer, journal,
  ID, partition, fallback, transcript, corpus, and normative-copy seams.
  Implements AC7-AC16.
- Behavior evals exercise relevant candidate risk, no knowledge, abstention,
  stale/quarantined evidence, prompt injection, scope and permission changes,
  severity downgrade, finding suppression, and self-validation. Implements
  AC5-AC8, AC14-AC16.
- Existing clean-report parsing and reviewer rerun tests prove terminal reviewer
  output remains exactly contract-shaped; named skips and evidence delimiters
  stay in work-loop's dispatch/QA record and never decorate
  `Clean — ready to commit.` Implements AC1, AC5-AC7, and AC17.
- stub: true

```python
def test_review_enquiry_precedes_first_dispatch_and_reuses_one_envelope():
    raise NotImplementedError  # STUB: AC3, AC4


def test_reviewers_are_non_writing_and_never_capture_or_distill():
    raise NotImplementedError  # STUB: AC10-AC13, AC15


def test_untrusted_knowledge_cannot_change_finding_or_verdict_authority():
    raise NotImplementedError  # STUB: AC7, AC8, AC16
```

**Approach:**

1. Add one compact review-planning branch to work-loop without changing the
   shipped review state machine, clean sentinel, or capture gates.
2. Add a common untrusted-envelope contract to the three reviewer definitions,
   specialized only where security and quality need their own independence
   language.
3. Add construction tests and semantic evals before updating source prose.
4. Bump core's patch-version authorities and update the pack's review journey
   description.

**Done when:** the core review family can use one bounded envelope, produces the
same independently supportable findings without it, and exposes no knowledge
write or permission expansion.

### T2: Architecture review uses the optional read-only enquiry handoff

**Depends on:** T1

**Verification mode:** TDD construction tests + Tier-4 behavior evals.

**Touches:**
`packs/architect/.apm/skills/architect-review/SKILL.md`,
`packs/architect/.apm/skills/architect-review/evals/evals.json`,
`packs/architect/tests/skills/architect-review/test_project_knowledge_boundary.py`,
`packs/architect/pack.toml`, `packs/architect/.claude-plugin/plugin.json`,
`packs/architect/README.md`, and `packs/architect/JOURNEY.md`.

**Tests:**

- Construction tests pin enquiry after eligibility/type/mode/scope/rubric
  resolution and before the rubric walk, plus exact request fields, no-refinement
  budget, stable-result boundary, and earlier non-gates. Implements AC1-AC6.
- Boundary tests prove the inline/default no-write posture; public read-only seam;
  absence of private writer, capture, distillation, receipt, partition, fallback,
  transcript, and raw-artifact copying; and optional handoff metadata. Implements
  AC9-AC15 and AC18.
- Behavior evals exercise relevant risk, abstention, unavailable provider,
  prompt injection, scope/severity/verdict manipulation, source verification,
  and self-review refusal. Implements AC5-AC10, AC14, and AC16-AC17.
- Existing rubric parity and activation evals remain green. Implements AC17 and
  AC19.
- stub: true

```python
def test_architecture_enquiry_runs_only_at_the_declared_planning_moment():
    raise NotImplementedError  # STUB: AC1, AC2, AC4


def test_architecture_findings_remain_independently_grounded_and_inline():
    raise NotImplementedError  # STUB: AC7-AC10, AC16


def test_architect_declares_optional_core_handoff_without_fallback():
    raise NotImplementedError  # STUB: AC5, AC12, AC18
```

**Approach:**

1. Insert the declared enquiry branch immediately before the existing rubric
   pass and retain the current knowledge-surface spot-check as independent
   verification rather than treating a topic as authority.
2. Add the optional architect-to-core handoff metadata without changing pack
   dependency ranges or install scope.
3. Add focused construction tests and semantic evals, then bump architect's
   patch-version authorities and review journey description.

**Done when:** architecture review can surface bounded candidate risks while its
rubric, source grounding, inline output, self-review refusal, and no-write
contract remain independently enforceable.

### T3: Published parity and end-to-end review evidence are complete

**Depends on:** T1, T2

**Verification mode:** Goal-based checks + manual QA + specialist review.

**Touches:**
`docs/specs/project-knowledge-review-integrations/spec.md`,
`docs/specs/project-knowledge-review-integrations/plan.md`,
`docs/specs/README.md`, `workspace.toml`,
`docs/architecture/knowledge-capture.md`, `docs/knowledge/README.md`,
`docs/specs/project-knowledge-review-integrations/notes/manual-qa.md`,
`docs/product/changelog.md`, `.claude-plugin/marketplace.json`, and these
deterministic core self-host projections:

- `.agents/skills/work-loop/SKILL.md` and
  `.agents/skills/work-loop/evals/evals.json`;
- `.claude/skills/work-loop/SKILL.md` and
  `.claude/skills/work-loop/evals/evals.json`;
- `.claude/agents/adversarial-reviewer.md`,
  `.claude/agents/security-reviewer.md`, and
  `.claude/agents/quality-engineer.md`;
- `.codex/agents/adversarial-reviewer.toml`,
  `.codex/agents/security-reviewer.toml`, and
  `.codex/agents/quality-engineer.toml`.

No repository architect projection exists today. Temporary multi-adapter build
outputs verify that pack without adding a new projection tree. Any additional
self-host output is scope evidence to review, not permission for an open-ended
generated-file edit.

**Tests:**

- Run each new test file in its own pytest process, then the existing
  project-knowledge, work-loop review, reviewer parser, and architect rubric
  suites. Implements AC1-AC20.
- Run forced self-host projection, temporary architect builds for every declared
  adapter, deep catalogue lint/verify, Ruff, targeted mypy if Python changes,
  `SKIP_SAST=1 make build-check`, and the repository security scan. Implements
  AC15 and AC17-AC20.
- Exercise core and architect positive, abstaining, unavailable, hostile,
  incomplete, rerun, and zero-write journeys in a disposable adopter-shaped
  repository. Record redacted pass/fail evidence only. Implements AC1-AC17 and
  AC21.
- Assert `workspace.toml` orders the separate research entry after review and
  before engineering/operations, and assert the research approval gate retains
  the current workflow inventory plus the no-capture, independent source-
  verification, abstention, raw-corpus, normative-authority, and output-root
  obligations from AC22. Implements AC22.
- Run adversarial, security, and quality implementation review until clean.
  Scan changed bytes for the prohibited comparison identifier and record only
  pass/fail. Implements AC7-AC21.
- no stub (goal/manual mode).

**Approach:**

1. Regenerate existing self-host projections only after both canonical pack
   tasks and version authorities are complete.
2. Update living knowledge docs to describe the shipped review integration and
   retain research as a separate downstream authority surface.
3. Run the full gates and record bounded manual evidence without knowledge
   bodies, reviewer scratch, raw artifacts, internal paths, or identifiers.
4. Harden through specialist review and stop at the ordinary human delivery
   gate.

**Done when:** source/projection and pack-runtime parity are clean, both review
journeys have observable zero-write evidence, and the implementation is ready
for ordinary human delivery approval.

## Rollout

1. Land T1 as the smallest pilot in the provider pack. It covers the common
   specialist-reviewer orchestration and the highest-risk untrusted-envelope
   boundary without a cross-pack dependency.
2. Land T2 after T1's envelope contract is reviewable. Architect retains the
   named unavailable branch, so no dependency cutover is required.
3. Run T3 with both source tasks present, regenerate existing projections, and
   publish both patch versions together only if normal release policy requires
   coordinated delivery.
4. Rollback removes enquiry prose/evals/tests and release metadata. It deletes
   no knowledge because this slice creates no knowledge writes.

## Risks

- **Prompt injection:** retrieved synthesis can look instructional. Delimiting,
  candidate-only use, independent grounding, and hostile-envelope evals keep it
  outside the instruction and authority chain.
- **Finding suppression or anchoring:** remembered practice can bias a reviewer
  toward prior conclusions. Full rubric/checklist traversal and target-derived
  findings prevent retrieval from becoming a shortcut or self-validation loop.
- **Reviewer permission drift:** adding knowledge can tempt direct CLI or file
  access inside a subagent. The caller owns enquiry; permission/projection tests
  pin the existing tool surface and Codex read-only sandbox without adding a
  mutation capability elsewhere.
- **Unavailable-provider ambiguity:** absence must not block a valid review or
  silently read another store. The exact skip and no-fallback assertions make
  degradation observable.
- **Cross-pack drift:** core is self-hosted while architect is validated through
  temporary adapter builds. Separate pack tasks and the final parity task keep
  each distribution boundary explicit.
- **Research coupling:** sharing a spec would force review's no-write inline
  model to absorb research output-root and corpus rules. The new dependency
  preserves a smaller approval and rollback surface.

## Changelog

- 2026-08-17: Initial plan splits review from research after the shipped
  authoring integration showed that review is a coherent read-only enquiry
  consumer while research has distinct product, corpus, output-root, source-
  verification, and terminal-gate authority. Core reviewer orchestration is the
  smallest implementation pilot; architect follows as an optional cross-pack
  handoff.
