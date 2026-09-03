# Plan: Verification ledger

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packs/core/seeds/docs/CONVENTIONS.md` § *A spec directory freezes as a unit* and § 4 own the authoring rule; `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py:833-851,1129-1152` proves the scheduled-plan hash and `:1071-1081` the approved-spec hash; `docs/specs/cooling-scope-closure/notes/closeout-records.md` is the analogous ledger pattern; `.github/workflows/build-check.yml:366` establishes the remotely gated roster-test location; `packs/AGENTS.md` § *Version bump rule* decides T5's required patch increment. Named uncertainty: the guard test's final filename is selected during implementation under `tests/roster/`.

> **Plan contract:** this is implementation strategy, not execution evidence. It may change substantively only while `Drafting`, before `approve-plan` records its baseline. After approval, including while `Executing`, only status and task-progress bookkeeping are permitted; observations go to `docs/specs/<feature>/notes/verification-ledger.md`, which is not hash-pinned and needs no amendment to either approved artifact. A `Done when:` names a concrete observable, never a frozen artifact as an execution-evidence destination.

## Approach

Correct one false premise at its source: the plan freezes in substance when `approve-plan` pins it, not when the feature ships. Add the sibling verification-ledger contract to the existing lifecycle reference, then make the template and small work-loop pointers route execution evidence there. A roster test joins the freeze guard to those authoring sources so reverting any one cannot silently restore the contradiction. Source changes precede projection regeneration, the index, and the release surface.

**Amended 2026-09-03.** T1-T5 shipped the distributed-restatement design and it did not hold: five review rounds each found a real guard defect, and rounds 4 and 5 each introduced defects while repairing others. T6-T8 reanchor the same outcome on one canonical rule with guarded pointer roles. T1-T5 remain as executed; their sections are preserved unedited under the amendment.

This plan is subject to the freeze it describes, as is its sibling `spec.md`. If implementation produces a mutation red, digest comparison, assertion text, or deviation, the executor writes it to `docs/specs/verification-ledger/notes/verification-ledger.md`; the approved artifacts name that destination but never contain the observation.

## Constraints

- The source of truth is `packs/core/seeds/docs/CONVENTIONS.md`; never edit its `docs/CONVENTIONS.md` projection or `.claude/skills/**` / `.agents/skills/**` projections by hand. The supervisor runs `FORCE=1 make build-self` after a clean committed source change.
- Do not alter `_loop_guards.py`, `loop-engine.py`, or `loop-cohort.py`, add an `Engine-Change-RFC:` trailer, change canonicalisation exemptions, retrofit cooling-scope-closure work, or edit the nine frozen `packs/core/tests/skills/work-loop/fixtures/corpus/*/plan.md` matches.
- Keep `work-loop/SKILL.md` within its 1000-line roster limit (832 lines at planning); add at most two lines and retain its existing lifecycle-reference links.
- Update the template changelog instruction only for `Drafting`; no `Done when:` in this delivery names `spec.md` or `plan.md` as an execution-evidence destination.

## Construction tests

**Integration tests:** focused pytest of the new `tests/roster/` guard, including its checks of the how-to's two clauses and of `work-loop/SKILL.md`'s pointer, then supervisor-selected repository gates. `build-check.yml` runs `python -m pytest tests/ -q`, while no workflow matches `packs/core/tests/skills/new-spec/`.

**Manual verification:** none. This delivery changes authoring contracts; the roster test and regeneration/release checks are the observable surfaces.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| canonical authoring rule — convention seed and projection | T1, T5, T6, T8 | roster test; self-host regeneration | generated projection agrees with seed |
| portable verification-ledger procedure | T1, T2, T6 | roster test | every enumerated pointer role resolves |
| executable contradiction guard | T3, T7 | mutation red and focused pytest | remote `tests/` gate includes it |
| spec index | T4 | README row follows new-spec format | index points to this spec |
| release history | T5 | version-parity and site-routing checks | topmost core entry and any highlights projection |
| delivery-local execution evidence | execution after approval | ledger only when observations occur | ledger remains outside approved hash |

## Design (LLD)

### Design decisions

- The ledger is Markdown at `docs/specs/<feature>/notes/verification-ledger.md`. It holds observed mutations, red results, assertion text, digest comparisons, and deviations; `spec.md` criteria and `plan.md` task rows retain obligations. Traces to: AC1, AC2, AC3.
- **Amended 2026-09-03.** `packs/core/seeds/docs/CONVENTIONS.md` is the sole normative statement of the boundary. Every other operational site carries a pointer to that owner or to the lifecycle ledger procedure. The public how-to and `references/pre-execute-review.md` additionally keep the correct rule statements they already had, and those stay guarded; `references/state-schema.md` keeps its mechanism description unedited. The superseded design had six surfaces restate the boundary "in their own operational terms"; five review rounds established that distributed restatements cannot be held in agreement mechanically, because every repair either widened a region until one site's clause satisfied another's or widened a phrase marker until it rejected correct prose. `references/state-schema.md` § *What the pin covers* stays unedited and describes the hash mechanism only. Traces to: AC1, AC2.
- **`references/state-schema.md` § *What the pin covers* (:128-141) is already correct and this delivery does not edit it.** It is the most precise statement of the boundary in the repository — "Everything else stays pinned: acceptance-criterion text, task text, `Depends on:` edges" — and it already covers both artifacts. It joins the guard's agreement set so a later edit there cannot contradict the owner while every other mutation still reddens; naming the ledger there too would be a seventh home for one fact. Traces to: AC3.
- **Amended 2026-09-03.** The roster test exercises the real freeze guard, pins the single canonical statement, and checks each enumerated pointer role separately against its own target. Three properties are structural, not stylistic: no role may be satisfied from another site, no assertion may fall back to a whole file, and no check may key on general mutability vocabulary. Each was a measured defect, at V1, V2 and V3 respectively, in [`notes/verification-ledger.md`](notes/verification-ledger.md). Traces to: AC3.
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
- Change `guides/core/explanation/why-the-plan-owns-the-lld.md` with one phase-qualified clause and an in-tree pointer to `../how-to/plan-and-execute-non-trivial-work.md`; do not create an independent mutability rule there.
- Add `## Verification ledger` to `references/delivery-contract-lifecycle.md`, covering contents, both immutable approved artifacts, and the ledger's unpinned/no-amendment status.

**Done when:** AC1's governing authoring surfaces agree that execution observations are written to the sibling ledger, not to frozen `spec.md` or `plan.md`.

### T2: Route execution guidance to the canonical ledger procedure

**Depends on:** T1

**Tests:**
- no stub (goal-based check): T3's roster guard verifies that `pre-execute-review.md`'s retained :205-215 rule agrees with the convention owner and that its observation destination is a pointer to the lifecycle reference; and separately that `work-loop/SKILL.md` carries a resolvable pointer to that reference and no rule of its own. The guard never asserts that `pre-execute-review.md` is free of a licence statement — it retains one deliberately.

**Approach:**
- Add one or two pointer-only lines in `work-loop/SKILL.md` Step 2 that link to the lifecycle reference; do not state an independent observation-routing rule.
- In `references/pre-execute-review.md` § *Mid-EXECUTE re-plan*, **keep** the existing rule at :205-215 — "immutable in substance", the bookkeeping exemption, "any substantive edit still causes a refusal", and "surface to the human and stop" are all correct, and this is the only work-loop surface that already states the boundary. It is therefore a rule-bearing surface. Extend it twice: name `spec.md` alongside `plan.md`, and add a pointer to the lifecycle reference for where an execution observation goes. Delete no correct guidance. The observation destination is a pointer; the retained edit-set rule stays a rule.
- Add one ledger-destination clause to `guides/core/how-to/plan-and-execute-non-trivial-work.md`, retaining its existing immutability fact and pointing operational detail to the lifecycle reference.

**Done when:** AC2's how-to names the ledger destination, while work-loop and pre-execute guidance reach that procedure only through resolvable lifecycle-reference pointers and preserve the amendment path for genuine errors.

### T3: Guard the frozen-plan contradiction in a remotely gated roster test

**Depends on:** T1

**Tests:**
- TDD: add `tests/roster/<verification-ledger guard>.py`. It reads `_loop_guards.py` to establish that both artifacts are canonically hashed and that `Executing` is legal post-approval, then reads the closed six-source set — convention seed, plan template, lifecycle reference, public explanation, `pre-execute-review.md` § *Mid-EXECUTE re-plan*, `state-schema.md` § *What the pin covers* — as one relationship. It separately verifies the how-to's retained immutability statement and its ledger clause, and `work-loop/SKILL.md`'s pointer.
- Mutation proof: **eight mutations, each verified to redden before the fix is believed.** Independently restore the Executing-time substantive-edit licence in each of the six rule-bearing sources (six mutations); delete the how-to's ledger clause (seven); remove `work-loop/SKILL.md`'s pointer (eight). After each, run `pytest tests/roster/<verification-ledger guard>.py -q` and restore by editing the file back, never by `git checkout`, `reset`, or `stash`. Expected failure text for the six: `post-approval mutability guidance must agree with the approved-artifact hash guards`. A mutation that does not redden means the guard is wrong, not that the mutation was unnecessary. Record each observed red in `notes/verification-ledger.md`, never here.

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

### T6: Make the convention the sole rule and every other site a pointer

**Depends on:** T1, T2

**Tests:**
- no stub (goal-based check): T7 reads each site as its own role and fails when a role's pointer is absent, wrong, or satisfiable from elsewhere.

**Approach:**
- In `packs/core/seeds/docs/CONVENTIONS.md`, keep one canonical boundary statement under a stable anchor. Reduce the § 4 plan description and the `Lifecycle` paragraph to pointers at that anchor. Delete no correct guidance: the two-stage distinction (pinned in substance at approval, frozen when the spec ships) must survive, because three frozen specs and one owner decision cite the section for the ship-time freeze.
- Give the new-plan template's `Plan contract`, `Done when:`, and `## Changelog` instructions a pointer each, so reverting any one of the three reddens on its own. `## Changelog` was unguarded and is the V5 defect.
- Give the lifecycle reference, the public explanation, and `work-loop/SKILL.md` Step 2 a pointer each. The how-to's mid-flight section and `references/pre-execute-review.md` § *Mid-EXECUTE re-plan* keep their **retained rule statements** as well as a pointer; round 2 established that `pre-execute-review.md:205-215` independently states the permitted edit set and is rule-bearing, not pointer-only, so treating it as a pure pointer would delete correct guidance and drop a killing mutation. `references/state-schema.md` takes no edit.
- Add no synthetic marker where existing structure already addresses a site. Measured: six of the guarded sites are unique real headings, and the template's `Done when:` instruction occurs exactly once. Only the convention's § 4 paragraphs, `state-schema.md` (one heading in the whole file), and the template's opening `Plan contract` blockquote lack a natural address, and T7 resolves those by assertion shape rather than by marking the prose. Nothing added cites anything under `docs/specs/`, so shipped pack content stays free of internal-governance citations.

**Done when:** every site AC2 enumerates resolves to the canonical owner or the lifecycle procedure, and the convention is the only *normative* statement of the boundary — the three surfaces AC2 names keep their existing statements.

### T7: Rebuild the roster guard on per-role assertions

**Depends on:** T6

**Tests:**
- TDD: rewrite `tests/roster/test_verification_ledger_contract.py`. Remove `RESTATED_RULE_MARKERS`, the whole-file `anchor=None` fallback, and the by-path region concatenation — each is a measured defect. Keep exercising `assert_status_legal` and `canonical_contract` against the real module rather than pinning its source text.
- Mutation proof: one killing mutation per enumerated site. That means each pointer removed and each pointer repointed at a non-canonical destination; the canonical statement reverted; each of the three retained statements reverted — the how-to's immutability sentence, `pre-execute-review.md`'s permitted-edit-set rule, and `state-schema.md`'s `Everything else stays pinned`; the roster itself shrunk by one entry; and the `` `Clean — ready to commit.` `` sentinel changed at its classification site. Innocent-edit probes must include a re-wrap of the canonical sentence, an unrelated mention of a non-canonical path outside every role, and ordinary Step 2 prose using the words "change substantively". Record every observed result in [`notes/verification-ledger.md`](notes/verification-ledger.md), never here.

**Approach:**
- Prefer absence over region extraction. Region extraction existed only to stop one site satisfying another's claim, and it broke three times — a bold-lead terminator on a re-wrap, a heading region ending before two further restatements, and a whole-file fallback that let clauses borrow. Asserting that **no non-canonical destination appears anywhere in the roster** achieves the same end with no anchor at all and is immune to re-wrapping, because a link target is not prose. Measured: `notes/*.md` across the eight roster files resolves to exactly one value today, `notes/verification-ledger.md`, so the absence assertion is clean on entry. Use a bounded region only where one file must carry several independent pointers, and fail loudly rather than widening when an address is missing or ambiguous.
- Absence-scanning cannot notice a site that drops its pointer while a sibling pointer survives in the same file, so pair it with a per-file pointer count or a heading-scoped presence check for the template's three instructions.
- Pin the role roster independently of the table that drives the assertions, so deleting a role reddens instead of shrinking coverage. That defect recurred twice, at round 2 and at round 4's own fix.

**Done when:** AC3's guard is green unmutated, every planned killing mutation reddens the role it targets, and every innocent-edit probe stays green.

### T8: Regenerate projections and re-verify the release surface

**Depends on:** T6, T7

**Tests:**
- no stub (goal-based check): the convention projection is byte-identical to its seed, and the core release surfaces still agree.

**Approach:**
- After the source commit and on a clean worktree, run `FORCE=1 make build-self`; hand-edit no generated projection.
- Re-read `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` at task start. Core is already at 2.22.1 from T5 against `origin/main`'s 2.22.0, so confirm whether this amendment's content changes need a further increment rather than assuming either answer.

**Done when:** the projection matches its seed byte-for-byte and AC4's three release surfaces agree.

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
  `approved_spec_hash` on the same comparison, and the overlapping measurement
  classes include three plan Changelog and two `spec.md` destinations; a
  plan-only rule would leave one plan wholly and one partially unaddressed.
- 2026-09-02: while `Drafting`, added the durable spec-index output, corrected
  the measurement populations and overlap counts, and made work-loop and
  pre-execute guidance pointer-only. Reason: the index is a new-spec-required
  durable surface; Instrument B measured 377 working-tree plans; and only the
  closed four-source rule set receives the contradiction mutations.
- 2026-09-02: while `Drafting`, changed T2 from replacing to extending the
  `pre-execute-review.md` § *Mid-EXECUTE re-plan* note. Reason: that note at
  :205-215 already states the rule correctly and is the only work-loop surface
  that does; it is incomplete in naming `plan.md` alone, not conflicting, so a
  replacement would have deleted correct guidance.
- 2026-09-02: while `Drafting`, reclassified `pre-execute-review.md` from
  pointer-only to rule-bearing and widened AC3's closed set from four sources
  to five, with seven killing mutations. Reason: the previous amendment created
  a contradiction — it ordered the file's licence rule retained while AC2, AC3,
  the Testing Strategy and T2's own test bullet all asserted the file carried
  no such rule. Review round 2 caught it as fix-induced; adjudication
  established that :205-215 holds no cross-reference and independently states
  the permitted edit set, so "pointer-only" was false of it. `work-loop/SKILL.md`
  is now the only pure pointer. The how-to was already treated consistently and
  did not change category.
- 2026-09-03: **contract amendment** under scope-owner authority
  ([`notes/redesign-decision.md`](notes/redesign-decision.md)). Replaced AC1-AC3
  and the two design decisions that required six surfaces to restate the
  boundary, and added T6-T8. Reason: review rounds 4 and 5 measured five
  defects in the shipped guard, three of them introduced by the round-4 repair.
  Reverting the literal retired licence into the rule owner's § 4 restatement
  left the suite at `12 passed`, and the template's corrected `## Changelog`
  rule was unguarded entirely. AC3's closing sentence was also overclaimed:
  accepted RFCs and ADRs state the same boundary outside any path the guard
  reads. The redesign gives up global contradiction detection and says so in
  the criterion. Revised before approval on owner challenge: AC2 and AC3 now
  state outcomes only, because the first draft encoded mechanism into AC3 —
  "no assertion may fall back to a whole file" would have forbidden the
  stronger destination-absence check. The same pass restored guarded coverage
  of the how-to's and `pre-execute-review.md`'s retained rule statements, which
  the proposed design had reclassified as pointers, and dropped synthetic role
  markers after measuring that existing structure addresses seven of eleven
  sites.
- 2026-09-02: while `Drafting`, added `references/state-schema.md` § *What the
  pin covers* as the sixth rule-bearing source (eight killing mutations), and
  corrected the site total from 7 to 8. Reason: review round 3, both findings
  pre-existing and its verdict `CONVERGING`. The state-schema page
  independently states the pinned/exempt split and is already correct, so it
  takes guard coverage but no edit; and the union table's sites sum to 8, of
  which 7 are `Done when:` statements and one is a mutation-table row.
