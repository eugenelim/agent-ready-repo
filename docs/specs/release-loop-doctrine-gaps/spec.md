# Spec: release-loop-doctrine-gaps

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Mode:** full <!-- multi-feature + new-public-interface risk triggers -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0072](../../rfc/0072-release-loop-deploy-doctrine.md) (G4 artifact format +
    progressive delivery doctrine — D1–D6)
  - [RFC-0073](../../rfc/0073-slo-authoring-and-error-budget.md) (SLO-authoring capability
    + error-budget PRR integration — D1–D5)
  - [RFC-0049](../../rfc/0049-the-release-loop-and-company-os.md) (release-loop parent —
    Accepted; the SLO follow-on is deferred here per § Follow-on)
  - [ADR-0031](../../adr/0031-infra-support-is-doctrine-on-existing-reviewers-not-a-new-reviewer-or-runtime.md) (no new executables;
    content + doctrine only)
- **Brief:** none
- **Contract:** none — doctrine/content changes only; no new `contracts/<type>/` surface.
- **Shape:** content/methodology change — six new sections added to the `release-loop`
  skill, a new `define-slo` skill in the same pack, and cross-reference notes in
  `docs/specs/release-loop/spec.md`. No new executable, no new runtime.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Implement the three blocking deploy-side gaps identified in the release-loop gap
assessment by extending the shipped `release-engineering` pack with:

1. **(RFC-0072)** Six new doctrine sections in `release-loop/SKILL.md`: G4 handoff
   package schema, four-phase deploy ordering protocol, canary analysis defaults
   with four-outcome protocol, feature flag lifecycle, service vs. IaC rollback
   procedures, and SLSA L2 provenance verification.
2. **(RFC-0073)** A new `define-slo` skill producing OpenSLO v1 documents, and an
   update to the release-loop PRR error-budget section replacing `not-defined` with
   a four-state resolution protocol.

No executable code is added. No new reviewer agents. No new top-level directories.
The two existing skill files (`release-loop/SKILL.md` and `define-slo/SKILL.md`) plus
cross-reference notes in the existing spec are the full deliverable.

**Out of scope:** generating Prometheus recording/alerting rules; ongoing error-budget
monitoring; the operate/incident loop; changes to `work-loop`, `discovery-loop`, or
`core`; new runtime tooling; any other pack.

## Boundaries

### Always do
- Content and doctrine only — no executables, no new reviewer agents (ADR-0031).
- Produce a `define-slo` skill in `packs/release-engineering/.apm/skills/define-slo/`.
- Add all six RFC-0072 sections **after** the existing `Anti-patterns to refuse` section
  in `release-loop/SKILL.md` — additive diff, no structural changes to existing prose.
- Update the release-loop PRR error-budget paragraph (currently "supplied by a follow-on
  SLO-authoring capability... `error-budget: not-defined`") with the four-state protocol.
- Add cross-reference notes to `docs/specs/release-loop/spec.md` AC5, AC6, AC7, AC10(e),
  and AC6b referencing the two RFCs. No AC text changes.
- Bump pack version 0.1.4 → 0.1.5 in `pack.toml` and `plugin.json`.
- Add a `[Unreleased]` entry to `docs/product/changelog.md` for the `release-engineering`
  pack 0.1.5 changes.
- Run `make build-self` to regenerate projections; run `make build-check`,
  `tools/lint-agent-artifacts.py`, and `tools/lint-agents-md.py`.
- Set this spec's Status to Shipped and check all ACs `[x]` in the implementing PR.
- Add `define-slo` to the `web/src/content/journeys/release.md` skills list — required
  to keep the web-journey-parity gate green (build-check will fail otherwise). Bundled fix.
- Backfill the `docs/rfc/README.md` index row for RFC-0071 (digital-experience-doctrine)
  — the row was absent from the index. Mechanical same-file index-hygiene ride-along;
  accepted here rather than opening a separate trivial PR.

### Never do
- Edit the projected `.claude/...` copies directly — `make build-self` reverts them.
- Change the loop's state machine, security controls, sidecar consumption convention,
  outer cap, or reuse wiring.
- Add a standalone schema file, error-budget script, or any executable artifact.
- Touch any pack other than `release-engineering`.

## Testing Strategy

Content/methodology change — same verification strategy as the release-loop spec itself:

- **Projection correctness:** goal-based — `make build-self` then drift/projection gates clean.
- **Lint conformance:** goal-based — `make build-check`, `tools/lint-agent-artifacts.py`,
  `tools/lint-agents-md.py` all exit 0.
- **Content presence:** goal-based — `grep` checks against each AC below.
- **Doctrine correctness:** judgmental — `adversarial-reviewer` spec-stage pass on the
  spec/plan (pre-EXECUTE, structural change trigger), and diff pass after EXECUTE.

## Acceptance Criteria

- [x] **AC1 — Six RFC-0072 sections present in `release-loop/SKILL.md`.**
  `grep -c "## The G4 handoff package\|## Deploy ordering\|## Canary analysis\|## Feature flag lifecycle\|## Rollback procedure\|## Artifact provenance verification" SKILL.md` = 6
- [x] **AC2 — G4 schema has all mandatory fields.**
  The G4 handoff section contains: `schema_version`, `built_at`, `built_by`,
  `component_manifest`, `provenance_ref`, `iac_plan_ref`, `test_evidence_summary`,
  `changelog_delta`, `deploy_phases` — all named in the YAML schema block. Verified by
  `grep`.
- [x] **AC2b — Deploy ordering section names the four canonical phases and floor rule.**
  Section contains the four phase names (`infra-apply`, `service-deploy`, `smoke`, `canary`)
  in order; the ordering-floor rule ("adopters may add phases" or equivalent) is stated.
- [x] **AC3 — Canary analysis section has the four traffic steps, threshold table, and four outcomes.**
  Section contains: "5%" and "25%" and "50%" and "100%" traffic progression; a table or list of
  `success rate`, `error rate`, `latency p99` defaults with at least one service-class
  tightening tier (≥99% or ≤1% or ≤200 ms); PROMOTE / ROLLBACK / PAUSE / HALT
  named as the four outcomes.
- [x] **AC4 — Feature flag section has all six lifecycle states.**
  Section contains: `created`, `deployed-off`, `enabled-pct`, `full-rollout`,
  `deprecated`, `removed` as named lifecycle states; four flag types listed.
- [x] **AC5 — Rollback section distinguishes service vs. IaC rollback.**
  Section uses "service rollback" and "IaC rollback" as distinct headings or bold
  terms; section contains "three-step" or equivalent verification protocol; IaC rollback
  is marked as a consent gate crossing.
- [x] **AC6 — Provenance section specifies SLSA L2, cosign/keyless, and failure = consent gate.**
  Section contains "SLSA" (L2 minimum), "cosign" or "keyless", and "consent gate" (failure path).
- [x] **AC7 — `define-slo` skill file exists with correct frontmatter.**
  `packs/release-engineering/.apm/skills/define-slo/SKILL.md` exists; `name: define-slo`
  in frontmatter; `lint-agent-artifacts.py` exits 0 on the skill.
- [x] **AC8 — `define-slo` skill body covers RFC-0073 D1–D5.**
  Skill contains: "OpenSLO" (D1); minimum required field names `objectives`, `target`,
  `budgetingMethod`, `timeWindow` (D2); `error_budget_policy` block with `halt_at` and
  `warn_at` fields (D2); four resolution states `not-defined` / `within-budget` /
  `warning` / `exhausted` (D3); `release-engineering` as the named skill home context (D4);
  "query-at-gate-time" or equivalent telemetry query instruction with `query-failed`
  state (D5); authoring-time query-validation step (D5 drawback mitigation).
- [x] **AC9 — release-loop PRR error-budget section updated to four-state resolution.**
  The old sentence beginning "The error-budget artifact is supplied by a follow-on
  SLO-authoring capability" is replaced; the section now names `not-defined`,
  `within-budget`, `warning`, and `exhausted` as the four resolution states.
- [x] **AC10 — `docs/specs/release-loop/spec.md` cross-reference notes added.**
  AC5, AC6, AC7, AC10(e) in the spec each contain a `(→ RFC-0072)` or equivalent
  cross-reference marker; AC6b contains a `(→ RFC-0073)` marker.
- [x] **AC11 — `pack.toml` and `plugin.json` at version `0.1.5`.**
- [x] **AC12 — All lint gates pass.**
  `make build-check`, `python tools/lint-agent-artifacts.py`, and
  `python tools/lint-agents-md.py` all exit 0 after `make build-self`.
- [x] **AC13 — Changelog updated.**
  `docs/product/changelog.md` contains a `[Unreleased]` or `[0.1.5]` entry for
  `release-engineering` describing the six RFC-0072 sections and the `define-slo` skill.
- [x] **AC14 — RFC-0072 and RFC-0073 both at Status: Accepted.**
  Both RFCs have `Status: Accepted` and a `Date closed` set before implementation ships.

## Assumptions

- The `packs/release-engineering/.apm/skills/define-slo/` directory does not exist yet
  and must be created (the skill is new).
- The `Anti-patterns to refuse` section at line ~353 is the last section in
  `release-loop/SKILL.md`; new RFC-0072 sections are appended after it.
- The PRR error-budget paragraph to replace is at approximately SKILL.md line 170–175
  (the "error-budget artifact is supplied by a follow-on" paragraph).
- Version 0.1.4 → 0.1.5 is a minor content addition; semver minor is appropriate.
- `make build-self` regenerates projected copies from `packs/` source; editing the
  projected copies directly would be reverted.
- `tools/lint-agent-artifacts.py` validates frontmatter for all skills in the pack.
