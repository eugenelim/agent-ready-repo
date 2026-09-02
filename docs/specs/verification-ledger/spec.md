# Spec: Verification ledger

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none — this delivery exposes no interface surface
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An implementer records execution observations without changing either approved, hash-pinned delivery artifact. `spec.md` acceptance criteria and `plan.md` task rows name obligations to discharge; `docs/specs/<feature>/notes/verification-ledger.md` records post-approval mutations, red results, assertion text, digest comparisons, and deviations. The canonical guidance states the boundary: substantive edits end at approval; an execution observation is ledger evidence, not an amendment.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| canonical authoring rule | Applicable | `packs/core/seeds/docs/CONVENTIONS.md` | core-pack maintainer | roster guard and regenerated projection | seed, projection, template, and public explanation agree on the post-approval boundary |
| portable execution procedure | Applicable | `packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md` | work-loop maintainer | roster guard and focused pytest | reference defines the ledger and keeps obligations in frozen `spec.md` and `plan.md` |
| executable contradiction guard | Applicable | `tests/roster/<new verification-ledger guard>.py` | test maintainer | mutation red and focused pytest | test rejects an Executing-time edit licence in a governing source |
| spec index | Applicable | `docs/specs/README.md` | `new-spec` authoring workflow | row resolves to this spec directory | index names `verification-ledger` |
| release history | Applicable | `docs/product/changelog.md` | release maintainer | version-parity and site-routing checks | topmost `[core]` release records this feature |
| delivery-local evidence | Applicable after approval | `docs/specs/verification-ledger/notes/verification-ledger.md` | executor | observations and stable references | created when execution produces observations; outside both approved hashes |
| corpus measurement | Applicable before approval | `docs/specs/verification-ledger/notes/measurement.md` | spec author | both instruments, their raw results, and the per-site adjudication | delivery-local research with no durable destination; reachable from the Measurement assumption above |

## Boundaries

### Always do

- Keep obligations in `spec.md` acceptance criteria or `plan.md` task rows; write execution-produced observations to the sibling verification ledger.
- Treat `packs/core/seeds/docs/CONVENTIONS.md` as the source of the projected `docs/CONVENTIONS.md`, regenerated through the existing self-host build.
- Keep the convention as mutability-rule owner; the template and lifecycle material point to it rather than creating competing definitions.

### Ask first

- Ask before changing the freeze guard's canonicalisation exemptions or the engine/cohort state machine.
- Ask before changing the ledger path or making its observations a machine-readable state surface.

### Never do

- Never edit `_loop_guards.py`, `loop-engine.py`, or `loop-cohort.py`; no engine change occurs and no `Engine-Change-RFC:` trailer applies.
- Never add a prose-lint detector for self-recording `Done when:` text or a third canonicalisation exemption for execution evidence.
- Never edit `.claude/skills/**`, `.agents/skills/**`, the projected `docs/CONVENTIONS.md`, completed historical task sections in `docs/specs/cooling-scope-closure/`, or the nine frozen `packs/core/tests/skills/work-loop/fixtures/corpus/*/plan.md` matches.

## Testing Strategy

- **Authoring contradiction: TDD.** A new remotely gated `tests/roster/` test reads the freeze guard and governing authoring surfaces. It proves that both approved artifacts are hash-protected and that the sources direct post-approval observations to the ledger; it is a relationship test, not a phrase grep.
- **Documentation, execution-pointer, and projection wiring: goal-based check.** The roster guard verifies the four closed rule-bearing sources plus the pointer-only work-loop and pre-execute surfaces; `FORCE=1 make build-self` regenerates projections after source changes, and existing pack/repository gates validate the generated and release surfaces.
- **Release surface: goal-based check.** Existing release tests verify core pack/plugin version parity and require a current `now` projection whenever the release has a `Highlights` subsection.

## Acceptance Criteria

- [ ] **AC1 — Approved-artifact observations have a writable home.** The canonical convention, new-plan template, and lifecycle reference distinguish obligations in frozen `spec.md` and `plan.md` from observations recorded at `docs/specs/<feature>/notes/verification-ledger.md`; the reference states that the ledger is not hash-pinned and needs no amendment to either artifact.
- [ ] **AC2 — Executing does not license substantive artifact edits.** The canonical convention and template permit substantive revision only before approval; the public explanation points in-tree to the how-to surface that already states this fact and names the ledger destination; and work-loop and pre-execute guidance are pointer-only links to the lifecycle reference, stating no independent routing rule.
- [ ] **AC3 — Each closed rule-bearing source kills the contradiction when reverted.** A remotely gated `tests/roster/` guard reddens when the corrected post-approval rule is independently reverted in any of this closed set: the convention seed, new-plan template, lifecycle reference, or public explanation, while the freeze guard protects the approved artifacts.
- [ ] **AC4 — The shipped core release is traceable.** Core pack and plugin versions are equal, and the topmost `[core]` heading immediately beneath `[Unreleased]` records this feature; a changed `Highlights` subsection has its `now` projection refreshed.

## Follow-ons

- core-pack maintainer: separate governed evidence artifact — assess whether the status-token and progress-checkbox canonicalisation exemptions should shrink. This delivery does not touch the guard or its exemption list.
- backlog maintainer: the canonical `[backlog].open` entry for `docs/specs/cooling-scope-closure/notes/review-findings.md` remains open because this delivery closes only finding 1 of its nine findings.

## Assumptions

- Technical: `check_schedule_current` hashes `plan.md`, and `sha256_canonical_contract` removes only the plan status token and progress-checkbox contents (source: `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py:833-851,1129-1152`).
- Technical: approval and schedule paths name `spec.md` and `plan.md`; no `notes/` path participates in their hash (source: `_loop_guards.py:1056-1089,1129-1152`; `loop-cohort.py:1206-1215,1330-1360`).
- Process: `docs/CONVENTIONS.md` is projected from `packs/core/seeds/docs/CONVENTIONS.md` (source: `packages/agentbundle/agentbundle/build/self_host.py:567-569`).
- Process: `tests/roster/` is remote-gated, while `packs/core/tests/skills/new-spec/` has no workflow match (source: `.github/workflows/build-check.yml:366`; `rg -n 'packs/core/tests/skills/new-spec' .github/workflows`, no matches).
- Product: the desired contract/ledger split, ledger path, and no-engine scope are confirmed by the task brief on 2026-09-02.
- Measurement: the adjudicated union is **6 of 376** pre-existing plans across 7 task-level sites. The overlapping classes are 1 mutation table, 3 plan `## Changelog` destinations, 2 `spec.md` or acceptance-criterion artifact destinations, and 1 “recorded here” destination. A plan-only rule leaves 1 of 6 wholly unaddressed and 1 of 6 partially addressed; both approved artifacts are in scope because the guard pins both, not because corpus frequency decides the rule. Instrument A covered the 376-plan commit tree; Instrument B covered the then-working tree's 377 plans and returned 8, including this delivery's own plan and one negated-sense false positive. The figure excludes this delivery from numerator and denominator (source: [`notes/measurement.md`](notes/measurement.md)).
