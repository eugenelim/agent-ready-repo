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

An implementer records execution observations without changing either approved, hash-pinned delivery artifact. `spec.md` acceptance criteria and `plan.md` task rows name obligations to discharge; `docs/specs/<feature>/notes/verification-ledger.md` records post-approval mutations, red results, assertion text, digest comparisons, and deviations.

One canonical source is the sole normative statement of the boundary. Three surfaces named in AC2 keep a consistent statement of their own because each is already correct and relied on elsewhere; every remaining operational site reaches the owner by pointer rather than restating it. Five review rounds established that distributed prose restatements cannot be held in agreement mechanically: widening a guarded region let one site's clause satisfy another's, and widening a phrase marker rejected correct prose. The reasoning and the rejected alternatives are in [`notes/redesign-decision.md`](notes/redesign-decision.md).

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| canonical authoring rule | Applicable | `packs/core/seeds/docs/CONVENTIONS.md` | core-pack maintainer | roster guard and regenerated projection | seed, projection, template, and public explanation agree on the post-approval boundary |
| portable execution procedure | Applicable | `packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md` | work-loop maintainer | roster guard and focused pytest | reference defines the ledger and keeps obligations in frozen `spec.md` and `plan.md` |
| executable contradiction guard | Applicable | `tests/roster/<new verification-ledger guard>.py` | test maintainer | mutation red and focused pytest | each enumerated pointer role, the canonical statement, and the real hash behaviour are independently killable |
| spec index | Applicable | `docs/specs/README.md` | `new-spec` authoring workflow | row resolves to this spec directory | index names `verification-ledger` |
| release history | Applicable | `docs/product/changelog.md` | release maintainer | version-parity and site-routing checks | topmost `[core]` release records this feature |
| delivery-local evidence | Applicable after approval | `docs/specs/verification-ledger/notes/verification-ledger.md` | executor | observations and stable references | created when execution produces observations; outside both approved hashes |
| corpus measurement | Applicable before approval | `docs/specs/verification-ledger/notes/measurement.md` | spec author | both instruments, their raw results, and the per-site adjudication | delivery-local research with no durable destination; reachable from the Measurement assumption above |

## Boundaries

### Always do

- Keep obligations in `spec.md` acceptance criteria or `plan.md` task rows; write execution-produced observations to the sibling verification ledger.
- Treat `packs/core/seeds/docs/CONVENTIONS.md` as the source of the projected `docs/CONVENTIONS.md`, regenerated through the existing self-host build.
- Keep the convention as the sole *normative* mutability-rule owner. The three surfaces AC2 names keep their existing consistent statements and stay guarded; every other operational site carries a pointer to the owner or to the lifecycle procedure and states no rule of its own.

### Ask first

- Ask before changing the freeze guard's canonicalisation exemptions or the engine/cohort state machine.
- Ask before changing the ledger path or making its observations a machine-readable state surface.

### Never do

- Never edit `_loop_guards.py`, `loop-engine.py`, or `loop-cohort.py`; no engine change occurs and no `Engine-Change-RFC:` trailer applies.
- Never add a prose-lint detector for self-recording `Done when:` text or a third canonicalisation exemption for execution evidence.
- Never edit `.claude/skills/**`, `.agents/skills/**`, the projected `docs/CONVENTIONS.md`, completed historical task sections in `docs/specs/cooling-scope-closure/`, or the nine frozen `packs/core/tests/skills/work-loop/fixtures/corpus/*/plan.md` matches.

## Testing Strategy

- **Authoring contradiction: TDD.** A remotely gated `tests/roster/` test exercises the real freeze guard, pins the owner and the three retained statements, and proves each enumerated pointer independently. How a site is addressed and how cross-satisfaction is prevented are implementation choices the plan selects on measured evidence, not properties this spec fixes.
- **Documentation, execution-pointer, and projection wiring: goal-based check.** The roster guard verifies the canonical owner, the three retained statements, and each enumerated pointer; `FORCE=1 make build-self` regenerates projections after source changes, and existing pack/repository gates validate the generated and release surfaces.
- **Release surface: goal-based check.** Existing release tests verify core pack/plugin version parity and require a current `now` projection whenever the release has a `Highlights` subsection.

## Acceptance Criteria

- [ ] **AC1 — Approved-artifact observations have one writable procedure.** The canonical convention states that approved `spec.md` and `plan.md` retain obligations while an execution observation goes to `docs/specs/<feature>/notes/verification-ledger.md`; the lifecycle reference owns the ledger's contents, path, unpinned status, and the consequence that recording there needs no amendment to either approved artifact.
- [ ] **AC2 — One rule owner; every other site either points at it or keeps a statement that is itself guarded.** `packs/core/seeds/docs/CONVENTIONS.md` is the sole normative statement of the post-approval boundary. Three surfaces retain a consistent statement of their own because each is already correct and is cited or relied on elsewhere: the public how-to's immutability sentence, `references/pre-execute-review.md` § *Mid-EXECUTE re-plan*'s permitted-edit-set rule, and `references/state-schema.md` § *What the pin covers*, which describes the hash mechanism and takes no edit. Every remaining operational site states no rule and carries a resolvable pointer to the owner or to the lifecycle ledger procedure: the convention's § 4 plan description and its `Lifecycle` paragraph; the new-plan template's `Plan contract`, `Done when:`, and `## Changelog` instructions; the lifecycle reference; the public explanation; and `work-loop/SKILL.md` Step 2.
- [ ] **AC3 — Every enumerated site is independently killable.** A remotely gated `tests/roster/` guard exercises the real status and canonical-hash behaviour, and reddens when any single enumerated site regresses on its own — an owner or retained statement reverted, or a pointer removed or repointed away from the canonical destination. No site's compliance may be satisfied by another site's text; no check may key on general mutability vocabulary; and the roster is pinned independently of whatever table drives the assertions, so deleting a site reddens instead of shrinking coverage. The roster is the current operational authoring and execution surface; accepted RFCs, ADRs, and other decision records are governing evidence outside it. New operational guidance that states the boundary rather than pointing at it requires a contract amendment adding a named guarded site.
- [ ] **AC4 — The shipped core release is traceable.** Core pack and plugin versions are equal, and the topmost `[core]` heading immediately beneath `[Unreleased]` records this feature; a changed `Highlights` subsection has its `now` projection refreshed.

## Follow-ons

- core-pack maintainer: separate governed evidence artifact — assess whether the status-token and progress-checkbox canonicalisation exemptions should shrink. This delivery does not touch the guard or its exemption list.
- backlog maintainer: the canonical `[backlog].open` entry for `docs/specs/cooling-scope-closure/notes/review-findings.md` remains open because this delivery closes only finding 1 of its nine findings.
- decision-record maintainer: `docs/adr/0061-loop-infrastructure-phase-1.md:12` states that "any post-approval plan change requires a full reset", which predates guarded baseline replacement and now reads stale beside RFC-0099 and ADR-0099. Out of scope here; this delivery neither cites nor relies on it.
- core-pack maintainer: this contract deliberately gives up global contradiction detection. The guard proves one canonical definition, a named pointer roster, one mechanism statement, and the real hash behaviour — not that arbitrary prose anywhere cannot contradict the boundary. Widening that claim needs a mechanism that does not depend on matching prose sentences.

## Assumptions

- Technical: `check_schedule_current` hashes `plan.md`, and `sha256_canonical_contract` removes only the plan status token and progress-checkbox contents (source: `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py:833-851,1129-1152`).
- Technical: approval and schedule paths name `spec.md` and `plan.md`; no `notes/` path participates in their hash (source: `_loop_guards.py:1056-1089,1129-1152`; `loop-cohort.py:1206-1215,1330-1360`).
- Process: `docs/CONVENTIONS.md` is projected from `packs/core/seeds/docs/CONVENTIONS.md` (source: `packages/agentbundle/agentbundle/build/self_host.py:567-569`).
- Process: `tests/roster/` is remote-gated, while `packs/core/tests/skills/new-spec/` has no workflow match (source: `.github/workflows/build-check.yml:366`; `rg -n 'packs/core/tests/skills/new-spec' .github/workflows`, no matches).
- Product: the desired contract/ledger split, ledger path, and no-engine scope are confirmed by the task brief on 2026-09-02.
- Product: the redesign from distributed prose restatements to one canonical rule with guarded pointer roles, and the narrowing of AC3's universe to current operational guidance, are authorized by the scope owner on 2026-09-03 (source: [`notes/redesign-decision.md`](notes/redesign-decision.md)).
- Measurement: the adjudicated union is **6 of 376** pre-existing plans across 8 obligation sites — 7 task `Done when:` statements plus one mutation-table row (`cooling-scope-closure:136`), which is why the `Done when:` parser alone cannot see it. The overlapping classes are 1 mutation table, 3 plan `## Changelog` destinations, 2 `spec.md` or acceptance-criterion artifact destinations, and 1 “recorded here” destination. A plan-only rule leaves 1 of 6 wholly unaddressed and 1 of 6 partially addressed; both approved artifacts are in scope because the guard pins both, not because corpus frequency decides the rule. Instrument A covered the 376-plan commit tree; Instrument B covered the then-working tree's 377 plans and returned 8, including this delivery's own plan and one negated-sense false positive. The figure excludes this delivery from numerator and denominator (source: [`notes/measurement.md`](notes/measurement.md)).
