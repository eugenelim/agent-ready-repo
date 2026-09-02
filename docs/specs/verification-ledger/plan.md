# Plan: Verification ledger

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packs/core/seeds/docs/CONVENTIONS.md` § *A spec directory freezes as a unit* and § 4 own the authoring rule; `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py:833-851,1129-1152` proves the scheduled-plan hash and `:1071-1081` the approved-spec hash; `docs/specs/cooling-scope-closure/notes/closeout-records.md` is the analogous ledger pattern; `.github/workflows/build-check.yml:366` establishes the remotely gated roster-test location. Named uncertainty: the guard test's final filename is selected during implementation under `tests/roster/`.

> **Plan contract:** this is implementation strategy, not execution evidence. It may change substantively only while `Drafting`, before `approve-plan` records its baseline. After approval, including while `Executing`, only status and task-progress bookkeeping are permitted; observations go to `docs/specs/<feature>/notes/verification-ledger.md`, which is not hash-pinned and needs no amendment to either approved artifact. A `Done when:` names a concrete observable, never a frozen artifact as an execution-evidence destination.

## Approach

Correct one false premise at its source: the plan freezes in substance when `approve-plan` pins it, not when the feature ships. Add the sibling verification-ledger contract to the existing lifecycle reference, then make the template and small work-loop pointers route execution evidence there. A roster test joins the freeze guard to those authoring sources so reverting any one cannot silently restore the contradiction. Source changes precede projection regeneration, the index, and the release surface.

This plan is subject to the freeze it describes, as is its sibling `spec.md`. If implementation produces a mutation red, digest comparison, assertion text, or deviation, the executor writes it to `docs/specs/verification-ledger/notes/verification-ledger.md`; the approved artifacts name that destination but never contain the observation.

## Constraints

- The source of truth is `packs/core/seeds/docs/CONVENTIONS.md`; never edit its `docs/CONVENTIONS.md` projection or `.claude/skills/**` / `.agents/skills/**` projections by hand. The supervisor runs `FORCE=1 make build-self` after a clean committed source change.
- Do not alter `_loop_guards.py`, `loop-engine.py`, or `loop-cohort.py`, add an `Engine-Change-RFC:` trailer, change canonicalisation exemptions, retrofit cooling-scope-closure work, or edit the nine frozen `packs/core/tests/skills/work-loop/fixtures/corpus/*/plan.md` matches.
- Keep `work-loop/SKILL.md` within its 1000-line roster limit (832 lines at planning); add at most two lines and retain its existing lifecycle-reference links.
- Update the template changelog instruction only for `Drafting`; no `Done when:` in this delivery names `spec.md` or `plan.md` as an execution-evidence destination.

## Construction tests

**Integration tests:** focused pytest of the new `tests/roster/` guard, then supervisor-selected repository gates. `build-check.yml` runs `python -m pytest tests/ -q`, while no workflow matches `packs/core/tests/skills/new-spec/`.

**Manual verification:** none. This delivery changes authoring contracts; the roster test and regeneration/release checks are the observable surfaces.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| canonical authoring rule — convention seed and projection | T1, T5 | roster test; self-host regeneration | generated projection agrees with seed |
| portable verification-ledger procedure | T1, T2 | roster test | lifecycle reference and work-loop links resolve |
| executable contradiction guard | T3 | mutation red and focused pytest | remote `tests/` gate includes it |
| spec index | T4 | README row follows new-spec format | index points to this spec |
| release history | T5 | version-parity and site-routing checks | topmost core entry and any highlights projection |
| delivery-local execution evidence | execution after approval | ledger only when observations occur | ledger remains outside approved hash |

## Design (LLD)

### Design decisions

- The ledger is Markdown at `docs/specs/<feature>/notes/verification-ledger.md`. It holds observed mutations, red results, assertion text, digest comparisons, and deviations; `spec.md` criteria and `plan.md` task rows retain obligations. Traces to: AC1, AC2, AC3.
- `packs/core/seeds/docs/CONVENTIONS.md` owns mutability. The template mirrors it; the public explanation carries one phase-qualified clause and a pointer to that owner; the lifecycle reference owns operational detail; and `work-loop/SKILL.md` only points there. Traces to: AC1, AC2.
- The roster test reads the actual freeze guard as well as every governing authoring surface, testing their contradiction rather than a newly added phrase. Traces to: AC3.
- **Prose-lint detector:** rejected because detection leaves the impossible state representable; the ledger removes it from the contract shape.
- **A third freeze-guard exemption:** rejected because another carve-out repeats the category error; reducing existing exemptions is a separately governed follow-on.
- **Engine change:** rejected because the guard, engine, and cohort already enforce the freeze; this delivery changes authoring and evidence routing only.

### Failure, edge cases & resilience

- A genuine spec or plan error still follows the existing controlled-amendment path. A result discovered while carrying out an approved obligation is not that error and belongs in the ledger.
- No ledger before approval is required. It is created only when execution produces an observation, so the plan cannot demand its own later edit.

### Quality attributes (NFRs)

- The roster test has one focused invariant and failure message. It reads source content and guard behavior only; it introduces no runtime state or dependency.

## Tasks

### T1: Make the contract and template distinguish obligation from observation

**Depends on:** none

**Tests:**
- no stub (goal-based check): T3 reads the convention seed, plan template, lifecycle reference, and public explanation as its AC1/AC2 construction surface.

**Approach:**
- Correct the false `Drafting`-or-`Executing` substantive-edit licence in the convention owner and its § 4 restatement; add the verification-ledger entry to the existing `notes/` tree. State that both `spec.md` and `plan.md` are approved, hash-pinned artifacts whose obligations do not receive execution observations.
- Change `packs/core/.apm/skills/new-spec/assets/plan.md` to match the owner, limit changelog edits to Drafting, and prohibit `Done when:` from naming either frozen artifact as an execution-evidence destination.
- Change `guides/core/explanation/why-the-plan-owns-the-lld.md` with one phase-qualified clause and a pointer to the convention owner; do not create an independent mutability rule there.
- Add `## Verification ledger` to `references/delivery-contract-lifecycle.md`, covering contents, both immutable approved artifacts, and the ledger's unpinned/no-amendment status.

**Done when:** AC1's governing authoring surfaces agree that execution observations are written to the sibling ledger, not to frozen `spec.md` or `plan.md`.

### T2: Route execution guidance to the canonical ledger procedure

**Depends on:** T1

**Tests:**
- no stub (goal-based check): T3 confirms the lifecycle reference is the operational source, and a focused source read confirms the work-loop pointer and mid-EXECUTE sentence use it without a fourth rule.

**Approach:**
- Add one or two lines in `work-loop/SKILL.md` Step 2 that point to the lifecycle reference for execution observations.
- Add one sentence in `references/pre-execute-review.md` distinguishing an execution observation from a plan error and directing it to the ledger rather than surfacing-and-stopping.

**Done when:** AC2's execution guidance routes observations to the lifecycle ledger procedure while preserving the amendment path for plan errors.

### T3: Guard the frozen-plan contradiction in a remotely gated roster test

**Depends on:** T1

**Tests:**
- TDD: add `tests/roster/<verification-ledger guard>.py`. It reads `_loop_guards.py` to establish that both artifacts are canonically hashed and that `Executing` is legal post-approval, then reads the convention seed, plan template, lifecycle reference, and public explanation as one relationship. It fails if any source restores an Executing-time substantive-edit licence or lacks the ledger rule/pointer.
- Mutation proof: independently restore the Executing-time substantive-edit licence in the convention seed, plan template, lifecycle reference, or public explanation, then run `pytest tests/roster/<verification-ledger guard>.py -q`. Expected failure text: `post-approval mutability guidance must agree with the approved-artifact hash guards`.

**Approach:**
- Use section-scoped semantic assertions: prove the guard/source contradiction, not merely a new phrase.
- Keep the test in `tests/roster/`, which the remote `tests/` pytest job runs; do not add it under the un-gated `packs/core/tests/skills/new-spec/`.

**Done when:** AC3's focused test is green unmutated and each planned single-source mutation produces the stated red.

### T4: Index the durable spec

**Depends on:** T1

**Tests:**
- no stub (goal-based check): the `docs/specs/README.md` active-list row resolves to this spec directory.

**Approach:**
- Add one `verification-ledger` row to `docs/specs/README.md` using the existing new-spec index shape.

**Done when:** the spec index contains one valid row for `docs/specs/verification-ledger/spec.md`.

### T5: Publish the core release and regenerate projections

**Depends on:** T1, T2, T3, T4

**Tests:**
- no stub (goal-based check): version-parity and relevant roster/site tests pass after source regeneration; if the release entry has `Highlights`, `web/src/lib/now-highlights.generated.json` is current.

**Approach:**
- At task start, read current `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` versions and bump both together from that live value; do not use a version literal recorded in this plan.
- Add this feature as the topmost `[core]` release heading directly beneath `[Unreleased]` in `docs/product/changelog.md`. Reproject the `now` highlights JSON when the entry uses a `Highlights` subsection.
- After the source commit and on the supervisor's clean worktree, run `FORCE=1 make build-self`; do not hand-edit generated skill projections.

**Done when:** AC4's three release surfaces agree, the core changelog entry is topmost in the required position, and any applicable highlights projection is fresh.

## Rollout

This is a source-first core-pack documentation and test release. Regenerate projections only after source changes commit cleanly; no migration, feature flag, external service, or rollback sequence applies. Reverting the release commit restores the prior guidance and test surface.

## Risks

- Repeating the rule across too many files would recreate drift. The convention seed remains the owner; the template mirrors it, the lifecycle reference owns operational detail, and the work-loop uses only a pointer.
- A phrase-only test could pass while restoring the contradiction. T3 joins source claims to the scheduled-hash guard and proves a mutation red for each governing file.
- Releasing from a stale version literal would create drift. T5 reads live manifests at task start.

## Changelog

- 2026-09-02: initial plan.
- 2026-09-02: while `Drafting`, extended the rule from `plan.md` to both frozen
  artifacts, added the public explanation guide as a fourth governed surface,
  and replaced the loose term count with the adjudicated 6-of-376 measurement in
  [`notes/measurement.md`](notes/measurement.md). Reason: `spec.md` carries
  `approved_spec_hash` on the same comparison, and 3 of the 6 measured sites
  name `spec.md` or the plan `## Changelog` rather than a mutation table, so a
  plan-only rule would have left half the corpus unaddressed.
