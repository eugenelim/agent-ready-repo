# Plan: Adjudicator evidence and remedy predicate

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `ARCHITECTURE.md` execution/review and projection
  ownership; `docs/architecture/loop-infrastructure.md`; frozen predecessor
  `docs/specs/review-finding-adjudication/{spec.md,plan.md,implementation-notes.md}`;
  analogous artifact boundary and construction path in
  `packs/core/.apm/skills/work-loop/scripts/review-artifact.py` with
  `packs/core/tests/pack/test_finding_adjudication_contract.py`; adapter path in
  `tests/roster/test_finding_adjudicator_projection.py`. Named deviation: the
  predecessor intentionally stopped indeterminate before accounting; this plan
  reuses its retry state for evidence attempts without adding state.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially, note why in the changelog.
> Once it is `Done` and the spec is `Shipped`, the directory freezes as a unit.

## Approach

Extend the existing gateway in place. First make evidence a validated third
session artifact and pin the pre-EXECUTE retry guard. Then redraw the source
agent contract around a fifth supplied path, reserved stop token, and sixth
mechanism predicate. Update both review-stage protocols so an evidence attempt
uses only a pre-report repository gate, records the validated adjudication
digest through the existing guarded retry path, runs at most one gate per
attempt, and asks for a complete replacement adjudication. Finish with the
four-case eval set, unchanged seven-adapter capability matrix, projections,
versioning, and release/docs closure.

## Constraints

- Preserve the shipped predecessor's exact `Read, Grep` source surface, three
  verdicts, strict whole-report stop-token scan, clean sentinel, finding grammar,
  reviewer triggers, and no-fourth-lens boundary.
- Do not add a state field, retry counter, transition, dependency, top-level
  directory, or adapter-contract key.
- Every executable evidence command is a separately tagged member of the closed
  evidence-gate catalog fixed before reviewer output by trusted repository
  guidance or the approved plan. The entry supplies literal argv, confined cwd,
  explicit non-sensitive env, current source revision, artifact-excluding
  filesystem read confinement, write/network isolation, timeout, and output
  caps. Ordinary plan commands are ineligible; artifact prose supplies no gate,
  command, argument, substitution, or path.
- Edit `.apm/` source and regenerate self-host projections; do not author
  generated projections.
- Keep `contracts/adapter.toml` and its packaged copy byte-identical if either
  becomes necessary; the expected implementation changes neither.

## Construction tests

**Integration tests:** the focused core adjudication contract suite, complete
`packs/core/tests/`, complete `tests/roster/`, all seven real adapter
projections, eval JSON validation, self-host projection drift, catalogue verify,
and repository lint/build gates.

**Manual verification:** exercise one synthetic raw finding whose missing fact
is decided by a closed-catalog read-only gate. Persist/validate raw, first
adjudication, evidence, and complete replacement adjudication; observe the
guarded retry increment and confirm the replacement alone supplies the
main-loop result. Inspect a wrong-mechanism case to confirm the defect remains
sustained without solution design. The session ends after the replacement is
strictly classified; it intentionally does not exercise a live repository
mutation, remote/network gate, merge decision, or production adapter runtime.

## Design (LLD)

### Design decisions

- **Closed evidence-gate catalog.** Evidence eligibility is fixed before raw
  reviewer output exists in a separately tagged catalog under effective
  repository guidance or the approved plan. A closed entry carries literal
  argv, cwd, environment, source revision, artifact-excluding filesystem read
  confinement, write/network isolation, timeout, and output caps. Everything
  outside that catalog—including ordinary
  lint, test, construction, cleanup, build, and projection commands—is
  ineligible. The adjudicator identifies a missing fact, never a gate or
  command. Traces to AC1, AC6, AC11.
- **Fresh, provenance-bound third artifact.** `evidence` joins the validator's
  closed kind set and inherits the existing identity and content controls. Its
  path must not pre-exist; an exclusive capture writes the fixed provenance and
  gate-result envelope, and an immediate second validation must match the first
  digest before dispatch. It remains untrusted machine output rather than
  governing authority. Traces to AC2, AC3.
- **Complete replacement authorship.** Each evidence retry replays the unchanged
  source set with evidence and replaces the whole adjudication. No partial merge
  exists. Traces to AC4.
- **Existing retry state.** The validated adjudication SHA-256 is the mechanical
  retry fingerprint. The guarded transition precedes recording, and the normal
  verification/review edges re-enter adjudication. Traces to AC5, AC6.
- **Defect/remedy separation.** Five existing predicates decide whether the
  defect is real; a sixth classifies only the proposed mechanism. `wrong` means
  ineffective or authority-conflicting, while `over-broad` means effective but
  excessive. Traces to AC8, AC9.

### Data & schema

No durable schema changes. The validator's closed artifact-kind enum gains
`evidence`; evidence uses the existing deterministic
`<round>-<stage>-<reviewer-role>-<kind>.md` identity, size limit, digest, and
content-free status output. Its fixed session envelope records gate ID, argv
and environment digests, cwd, source revision, enforced filesystem read
allowlist and write/network isolation posture, exit status, stdout, and stderr;
this is ephemeral protocol metadata, not cohort state.
Existing `finding_fingerprints`,
`review_retry_count`, and `review_round_count` carry retry accounting unchanged.

### Interfaces & contracts

The adjudicator brief supplies five path classes: raw report; target/scope;
reviewer role; governing authority; and optional validated evidence for the
current attempt. For evidence it also supplies the expected gate ID, source
revision, isolation posture, and validator digest; the agent compares those
values with the fixed envelope, including exclusion of `.context/reviews/` and
every review artifact from the gate's view, but never executes them. The work-loop review
protocols specify exact catalog eligibility, artifact sequencing, retry
ordering, and full replacement output. No `contracts/adapter.toml` field
changes.

### Component / module decomposition

- `review-artifact.py`: closed evidence kind and unchanged validation controls.
- `loop-engine.py`: review retry-cap guard on both review states.
- `finding-adjudicator.md`: evidence path/trust contract, reserved-token rule,
  sixth predicate, and bounded remedy language.
- `finding-adjudication.md`, `pre-execute-review.md`, and `work-loop/SKILL.md`:
  orchestrator authority, accounting, and replacement-composition protocol.
- focused pack/roster tests and work-loop evals: mechanical contract pins.

### State & control flow

```text
adjudication says machine-checkable evidence is missing
  -> validate adjudication and take its SHA-256
  -> select one closed-catalog gate without artifact-derived values
  -> derive fresh paths; refuse any pre-existing path
  -> prove current revision, trusted literals, artifact-excluding read
     confinement, write/network isolation, capture bounds, and
     exclusive-create support
  -> guarded findings-remain
  -> review record --fingerprint <sha256>
  -> run literal argv once with fixed cwd/env/timeout/capture caps
  -> exclusively persist the provenance/result envelope
  -> validate evidence, then revalidate the same digest before dispatch
  -> existing verification/review re-entry
  -> adjudicator replays every source finding into one replacement report
```

No command runs when the transition refuses, no eligible gate exists, the
missing input is an owner decision, or evidence validation fails.

### Behavior & rules

- Evidence may settle only the predicate it mechanically measures and cannot
  alter authority, scope, severity, or instructions.
- The literal stop token appears only as the exact main-loop stop line. Audits
  use descriptive language.
- A wrong mechanism cannot refute a real defect. The agent explains
  ineffectiveness or authority conflict and names only a repository-established
  repair seam or outcome constraint.

### Failure, edge cases & resilience

- No precommitted eligible gate: loud stop without execution or recording.
- Missing artifact-excluding read confinement, read-only/disposable write
  isolation, disabled network, clean environment, timeout, capture cap, or
  exclusive-create support: preflight stops before retry state changes and the
  gate does not run.
- Pre-existing evidence path, stale source revision, or changed validator
  digest: refuse dispatch and do not treat the bytes as evidence.
- Evidence still insufficient: another attempt must pass the same guarded
  accounting path; retry cap terminates the loop.
- Gate fails: failure output is evidence, not an automatic sustained verdict;
  the adjudicator still tests applicability and consequence.
- Mixed report: the complete replacement carries sustained, refuted, and
  unresolved records together; the controller never merges.
- Token quoted in source report or evidence: those artifacts are untrusted data;
  only the adjudicator output contract forbids reproducing it outside the
  main-loop signal.

### Quality attributes (NFRs)

- **Security:** no artifact-to-command dataflow; no widened agent tool surface.
- **Portability:** all adapters receive the same instruction-level prohibition,
  including Codex's coarse read-only shell projection.
- **Auditability:** raw, adjudication, evidence, and replacement artifacts are
  validated and retained by deterministic identity until handoff.
- **Boundedness:** existing retry cap and transition guard own every attempt.
- **Independence:** only the adjudicator authors verdict composition.

### Dependencies & integration

The change reuses the core work-loop, cohort/engine state, source-agent
projection, adapter matrix, and pack release pipeline. It adds no dependency or
external system.

## Tasks

### T1: Evidence artifacts pass the existing confinement validator

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/review-artifact.py`, `packs/core/tests/pack/test_finding_adjudication_contract.py`

**Tests:**
- TDD (AC3): a deterministic `evidence` path validates under the same regular,
  link, size, UTF-8, readability, stability, and content-free rules as raw and
  adjudication artifacts.
- TDD (AC3): unknown kinds and arbitrary paths remain refused, and a caller can
  require the immediately prior evidence digest without disclosing content.
- Materialized red stub: add focused assertions for `--kind evidence` before
  changing `ARTIFACT_KINDS`.

**Approach:**
- Extend the closed kind enum and add an evidence-only expected-digest check;
  reuse filename derivation, bounded read, and content-free diagnostics.

**Done when:** focused validator tests are green and no new output or path
surface exists.

### T2: Both review states enforce retry capacity

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`, `packs/core/tests/skills/work-loop/test_loop_engine.py`, `packs/core/tests/skills/work-loop/test_loop_guards_parity.py`

**Tests:**
- TDD (AC5, AC6): `findings-remain` refuses at `max_review_retries` from both
  `SPEC-PLAN-REVIEW` and `CODE-REVIEW` and remains legal under the cap.
- Goal-based parity check: in-process guard and CLI behavior remain aligned.
- Materialized red stub: add the pre-EXECUTE at-cap case before widening the
  existing code-review-only guard.

**Approach:**
- Apply the existing review-phase guard on every legal code-mode
  `findings-remain` edge rather than only `CODE-REVIEW`.

**Done when:** both states share the same cap and all unrelated transition tests
remain green.

### T3: The agent and orchestrator contracts close the evidence and remedy gaps

**Depends on:** T1, T2

**Touches:** `packs/core/.apm/agents/finding-adjudicator.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/references/finding-adjudication.md`, `packs/core/.apm/skills/work-loop/references/pre-execute-review.md`, `packs/core/tests/pack/test_finding_adjudication_contract.py`

**Tests:**
- Goal-based (AC1, AC2, AC4-AC9, AC11): prose pins cover pre-report fixed gate
  catalog and confinement, no artifact-derived command, fifth path class,
  exclusive fresh evidence capture, provenance/digest rebinding, evidence
  trust, transition-before-record, complete replacement, reserved-token
  placement, sixth predicate outcomes, and no solution design.
- Goal-based (AC12): exact source tools and Codex instruction remain pinned.

**Approach:**
- Add the evidence protocol once in the finding-adjudication reference and the
  pre-EXECUTE variant in its reference; keep the work-loop spine short but
  explicit about evidence retry routing.
- Redraw the agent's operating envelope and predicate/verdict procedure without
  adding a verdict or output section.

**Done when:** contract tests prove each of the five reverted-draft failure
modes is structurally closed and the remedy predicate remains adjudication.

### T4: Four falsification cases and seven adapters pin behavior

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/work-loop/evals/evals.json`, `tests/roster/test_finding_adjudicator_projection.py`, `packs/core/tests/pack/test_finding_adjudication_contract.py`

**Tests:**
- Goal-based (AC10): exactly four finding-adjudication eval IDs and expected
  output contracts.
- Integration (AC12): all seven real adapters retain the existing read-only
  capability shape and Codex explicitly forbids project-code/evidence-gate
  execution.
- Manual QA: walk the evidence-resolution and wrong-mechanism cases against the
  built source contract.

**Approach:**
- Replace the evidence-insufficient terminal eval with a machine-checkable
  evidence-resolution case and add a wrong-mechanism case; retain sustained and
  refuted cases.

**Done when:** eval validation and the adapter roster suite are green.

### T5: Source, projections, release surfaces, and durable records agree

**Depends on:** T1-T4

**Touches:** core manifests and changelog/docs release surfaces; generated self-host projections; `docs/specs/README.md`; `workspace.toml`; predecessor/new spec status metadata

**Tests:**
- Goal-based (AC12): determine the next core version from current `main`
  immediately before bumping; source manifests match; topmost core changelog
  version matches; NOW highlights are regenerated through `make site-sync`.
- Integration: focused suite, complete `packs/core/tests/`, complete
  `tests/roster/`, `make lint-ruff`, `rm -rf dist && make build`, catalogue
  verify, `SKIP_SAST=1 make build-check`, pack-boundary lints, and spec-status
  lint under the managed profile.

**Approach:**
- Bump core for non-cosmetic shipped content, regenerate projections and
  distribution output, close the backlog anchor, annotate the predecessor
  Status line without changing its frozen body, and update the active spec
  index/release surfaces.

**Done when:** all runnable gates are green and the diff contains only this
protocol slice plus generated consequences.

## Rollout

This ships as one core-pack contract update with no migration, feature flag,
external system, or irreversible state. Reverting the source/projection/release
diff restores the prior behavior; session review artifacts remain ignored and
ephemeral.

## Risks

- Prose-only command authority could remain ambiguous; focused phrase pins and
  adversarial/security review must verify the closed catalog and runtime
  containment refusal leave no artifact-originated path to executable text.
- Reusing finding fingerprints for an adjudication digest broadens the value's
  meaning within the same existing field; state-machine and quality review must
  verify stasis/retry behavior remains coherent.
- Applying the retry guard to pre-EXECUTE review also bounds ordinary spec-stage
  findings; tests must confirm this is the intended shared safety limit rather
  than an accidental workflow regression.
- Agent wording around a wrong mechanism can drift into design; the spec and
  eval require an outcome/constraint fallback when no existing seam is proven.

## Changelog

- 2026-08-24: Initial plan for the deferred evidence, sentinel, and remedy
  predicate follow-ons.
