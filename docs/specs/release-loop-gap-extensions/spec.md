# Spec: release-loop-gap-extensions

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Mode:** full <!-- structural change (new module in core) + multi-feature risk triggers -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0074](../../rfc/0074-fidelity-ladder-and-ephemeral-env-qualification.md) (fidelity-ladder
    reference module + outer-loop qualification floor — D1–D5)
  - [RFC-0075](../../rfc/0075-polyrepo-value-stream-release-topology.md) (polyrepo / value-stream
    release topology — D1–D5)
  - [RFC-0049](../../rfc/0049-the-release-loop-and-company-os.md) (release-loop parent — Accepted;
    D3 defers the fidelity-ladder; OQ1/AC9 name the polyrepo mechanism)
  - [RFC-0072](../../rfc/0072-release-loop-deploy-doctrine.md) (G4 artifact format — Accepted; fleet
    manifest extends G4 per RFC-0075 D1)
  - [ADR-0031](../../adr/0031-infra-support-is-doctrine-on-existing-reviewers-not-a-new-reviewer-or-runtime.md)
    (no new executables; content + doctrine only)
- **Brief:** none
- **Contract:** none — doctrine/content changes only; no new `contracts/<type>/` surface.
- **Shape:** two content/methodology additions across two packs: a new EXECUTE/QUALIFY reference
  module in `core`'s `operational-safety`, two new sections in `release-loop/SKILL.md`, one new
  section in `work-loop/SKILL.md`, and cross-reference notes in `docs/specs/release-loop/spec.md`.
  No new executables, no new runtime, no new skill (the fidelity-ladder guidance lives as a
  reference module, not a standalone user-invocable skill).

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Implement the two secondary release-loop gaps deferred from the initial gap assessment —
one in `core`, one in `release-engineering`:

1. **(RFC-0074)** A new `fidelity-ladder` EXECUTE/QUALIFY reference module in
   `packs/core/.apm/skills/operational-safety/references/`, plus cross-references from
   the `work-loop` skill (inner-loop ladder section) and the `release-loop` skill (outer-loop
   qualification floor section). Closes RFC-0049 D3's deferred fidelity-ladder obligation and
   fills in the qualification test AC3/AC10(h) require but do not specify.

2. **(RFC-0075)** A new Polyrepo topology section in `release-loop/SKILL.md` specifying the
   fleet manifest format, the canonical e2e host repo definition, the five-term deploy
   sequencing vocabulary, and the collect-then-validate pre-deploy step. Fills in the
   "value-stream cross-repo mechanism" AC9 names but does not yet specify.

No executable code. No new reviewer agents. No new runtime. No new top-level directories.
The three new or updated SKILL.md files plus the new reference module plus cross-reference
notes are the full deliverable.

**Out of scope:** local infra tooling or automation (the ladder is doctrine, not a runtime);
ArgoCD, Flux, or Spinnaker configuration (adopter toolchain); changes to `work-loop`'s
loop mechanics (only a cross-reference section is added); the operate/incident loop; any
pack other than `core` and `release-engineering`.

## Boundaries

### Always do
- Content and doctrine only — no executables, no new reviewer agents (ADR-0031).
- Create `packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md` as a new
  EXECUTE/QUALIFY reference module (parallels `cloud-implementation-craft.md` in the same
  directory, not `environment-isolation.md` which is REVIEW).
- Add a fidelity-ladder cross-reference section to `packs/core/.apm/skills/work-loop/SKILL.md`
  after the existing `## Anti-patterns to refuse` section (the current last section).
- Add an ephemeral environment qualification section to
  `packs/release-engineering/.apm/skills/release-loop/SKILL.md` after the existing
  `## Artifact provenance verification` section (the current last section per RFC-0072).
- Add a Polyrepo topology section to the same `release-loop/SKILL.md`, after the ephemeral
  environment section.
- Add cross-reference notes to `docs/specs/release-loop/spec.md`: RFC-0074 on AC3 and AC10(h);
  RFC-0075 on AC9. No AC text changes.
- Bump `packs/core` version `0.15.4` → `0.15.5` in `pack.toml` and `plugin.json`.
- Bump `packs/release-engineering` version `0.1.5` → `0.1.6` in `pack.toml` and `plugin.json`.
- Add `[Unreleased]` entries to `docs/product/changelog.md` for both packs.
- Run `make build-self` to regenerate projections; run `make build-check`,
  `tools/lint-agent-artifacts.py`, and `tools/lint-agents-md.py`.
- Set RFC-0074 and RFC-0075 Status: Accepted + Date closed before the PR merges.
- Set this spec's Status to Shipped and check all ACs `[x]` in the implementing PR.

### Never do
- Edit the projected `.claude/...` copies directly — `make build-self` reverts them.
- Extend `environment-isolation.md` inline — that module is REVIEW; the fidelity-ladder
  module is EXECUTE/QUALIFY. Conflating them corrupts the role distinction.
- Create a standalone `fidelity-ladder` skill — the reference module is consumed by other
  skills, not user-invocable; a skill is premature until a second consumer appears.
- Create a fleet-manifest.md reference file — the schema is fully specified inline in the
  skill section; extract only when a second consumer appears.
- Add a new cross-repo coordinator runtime or script (ADR-0031; fleet assembly is doctrine).
- Touch any pack other than `core` and `release-engineering`.
- Change `work-loop` loop mechanics, gates, or state machine — only a cross-reference
  section is added.

## Testing Strategy

Content/methodology change — same verification strategy as the release-loop-doctrine-gaps spec:

- **Projection correctness:** goal-based — `make build-self` then drift/projection gates clean.
- **Lint conformance:** goal-based — `make build-check` (includes skill-spec lint, catalogue
  verify, and agents-md hygiene) exits 0. `python tools/lint-agents-md.py` exits 0.
- **Content presence:** goal-based — `grep` checks against each AC below.
- **Doctrine correctness:** judgmental — `adversarial-reviewer` spec/plan pass (pre-EXECUTE,
  structural change trigger fires), and diff pass after EXECUTE.

No TDD (no testable logic added — the deliverables are doctrine documents).

## Acceptance Criteria

### RFC-0074 — Fidelity-ladder reference module

- [x] **AC1 — `fidelity-ladder.md` reference module created.**
  `packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md` exists.
  Verified by `test -f`.

- [x] **AC2 — Module covers the seven-level ladder (L0–L6 including L4+).**
  File contains: `L0`, `L1`, `L2`, `L3`, `L4`, `L4+`, `L5`, `L6` as named levels.
  Verified by `grep -c "^Level: L" fidelity-ladder.md` = 8 (or equivalent level-count match).

- [x] **AC3 — Module names the three provability classes.**
  File contains: `Self-evident`, `Requires policy audit` (or `requires-policy-audit`),
  and `Programmatically auditable` (or `programmatically-auditable`) as named classes.
  Verified by `grep`.

- [x] **AC4 — Module names the three qualification dimensions.**
  File contains: `Prod reachability`, `Data isolation`, and `Inter-env isolation` (or
  equivalent headings). Verified by `grep`.

- [x] **AC5 — `work-loop` SKILL.md gains a fidelity-ladder section with heuristic and ladder summary.**
  `packs/core/.apm/skills/work-loop/SKILL.md` contains a heading with "fidelity" (case-
  insensitive); section cross-references `operational-safety/references/fidelity-ladder.md`
  or equivalent path pointer; section body contains the "push up the ladder" budget heuristic
  (grep for `push up` or `sub-5` or `budget`) and at least the level tokens `L0` and `L5`.
  Verified by `grep -i "fidelity" SKILL.md`, `grep "sub-5\|push up" SKILL.md`,
  `grep "L0\|L5" SKILL.md`.

- [x] **AC6 — `release-loop` SKILL.md gains an ephemeral environment qualification section.**
  `packs/release-engineering/.apm/skills/release-loop/SKILL.md` contains a heading with
  "Ephemeral" (case-insensitive) and the section body contains: `L5` (the floor level),
  references to the three qualification dimensions, `consent gate` (the consequence of
  falling below the floor), the provability classification trio (`self-evident` or
  `requires policy audit` or `programmatically auditable`), and an `L4`/`L4+` conditional
  path (policy-audit condition for namespace isolation). Verified by `grep`.

- [x] **AC7 — `docs/specs/release-loop/spec.md` cross-reference notes added (RFC-0074).**
  The file contains `RFC-0074` at least twice — once near AC3 and once near AC10(h).
  Verified by `grep -c "RFC-0074" docs/specs/release-loop/spec.md` ≥ 2.

- [x] **AC8 — `packs/core` at version `0.15.5`.**
  `packs/core/pack.toml` contains `version = "0.15.5"` and
  `packs/core/.claude-plugin/plugin.json` contains `"version": "0.15.5"`.

### RFC-0075 — Polyrepo topology

- [x] **AC9 — `release-loop` SKILL.md gains a Polyrepo topology section.**
  `packs/release-engineering/.apm/skills/release-loop/SKILL.md` contains a heading with
  "Polyrepo" (case-insensitive). Verified by `grep -i "## Polyrepo"`.

- [x] **AC10 — Polyrepo section documents the fleet manifest schema fields.**
  The section contains: `schema_version`, `fleet_name`, `assembled_at`, `components`,
  `deploy_sequence` (marked optional — defaults to parallel), `image_ref`, `g4_package_ref`,
  `e2e_suite_ref`. Verified by `grep`.

- [x] **AC11 — Polyrepo section specifies the collect-then-validate pre-deploy step.**
  The section describes a "collect" phase (or equivalent name) that runs before
  `infra-apply`; the phase reads each component's `g4_package_ref`, runs provenance
  verification, and confirms `image_ref` consistency.
  Contains: "collect" and "provenance" and "infra-apply".
  Verified by `grep`.

- [x] **AC11b — Polyrepo section specifies the e2e host repo Must-NOT rule (RFC-0075 D2).**
  The section states that the e2e host repo must NOT contain component application source code.
  Contains: "Must NOT contain" (or equivalent phrasing) and "component" and "source".
  Verified by `grep -i "must not contain\|no component source"`.

- [x] **AC11c — Polyrepo section includes the five-term harness-neutral vocabulary (RFC-0075 D3).**
  The section contains all five terms: `Component`, `Stage`, `Gate`, `Depends-on`,
  `Release manifest` as named vocabulary terms (table or list). The two distinctive tokens
  (`Depends-on` and `Release manifest`) are individually present.
  Verified by `grep "Depends-on"` and `grep "Release manifest"` each returning ≥ 1 match.

- [x] **AC11d — Polyrepo section includes the courier snapshot discipline note (RFC-0075 D4).**
  The section contains "courier snapshot" and states that the fleet manifest does not fork
  component G4 packages (grep for "does not fork" or "never fork" or "read-only reference").
  Verified by `grep -i "courier snapshot"` and `grep -i "does not fork\|never fork\|read-only reference"`.

- [x] **AC12 — `docs/specs/release-loop/spec.md` cross-reference note added (RFC-0075).**
  The file contains `RFC-0075` at least once, near AC9.
  Verified by `grep "RFC-0075" docs/specs/release-loop/spec.md`.

- [x] **AC13 — `packs/release-engineering` at version `0.1.6`.**
  `packs/release-engineering/pack.toml` contains `version = "0.1.6"` and
  `packs/release-engineering/.claude-plugin/plugin.json` contains `"version": "0.1.6"`.

### Shared gates

- [x] **AC14 — All lint gates pass.**
  `make build-check` and `python tools/lint-agents-md.py` both exit 0 after `make build-self`.
  (`lint-agent-artifacts.py` was consolidated into `make build-check`.)

- [x] **AC15 — Changelog updated.**
  `docs/product/changelog.md` contains `[Unreleased]` or version entries for both
  `core` (describing the fidelity-ladder module) and `release-engineering` (describing
  the ephemeral env qualification + polyrepo topology sections).

- [x] **AC16 — RFC-0074 and RFC-0075 both at Status: Accepted.**
  Both RFCs have `Status: Accepted` and a `Date closed` set before implementation ships.

## Assumptions

- `packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md` does not yet
  exist (confirmed: directory listing shows seven existing modules, none named `fidelity-ladder`).
- `## Anti-patterns to refuse` is the current last section in `work-loop/SKILL.md`
  (confirmed at line 912); the new fidelity-ladder section is appended after it.
- `## Artifact provenance verification` is the current last section in `release-loop/SKILL.md`
  (confirmed at line 573); the ephemeral environment qualification section and Polyrepo topology
  section are appended after it, in that order.
- `packs/core` is at version `0.15.4` and `packs/release-engineering` is at `0.1.5`
  (confirmed from pack.toml and plugin.json).
- The release-loop spec's AC3 and AC10(h) already mandate the isolation conditions and the
  consequence (consent-gate crossing); this spec adds only a cross-reference note, not AC text
  changes.
- `make build-self` regenerates projected copies from `packs/` source; editing the
  projected copies directly would be reverted.
