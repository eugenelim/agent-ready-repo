# Plan: Verification ledger

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/core/seeds/docs/CONVENTIONS.md` § *A spec directory freezes as a unit* and § 4 own the authoring rule; `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py:833-851,1129-1152` proves the scheduled-plan hash and `:1071-1081` the approved-spec hash; `docs/specs/cooling-scope-closure/notes/closeout-records.md` is the analogous ledger pattern; `.github/workflows/build-check.yml:366` establishes the remotely gated roster-test location; `packs/AGENTS.md` § *Version bump rule* decides T5's required patch increment. Named uncertainty: the guard test's final filename is selected during implementation under `tests/roster/`.

> **Plan contract:** this is implementation strategy, not execution evidence. It may change substantively only while `Drafting`, before `approve-plan` records its baseline. After approval, including while `Executing`, only status and task-progress bookkeeping are permitted; observations go to `docs/specs/<feature>/notes/verification-ledger.md`, which is not hash-pinned and needs no amendment to either approved artifact. A `Done when:` names a concrete observable, never a frozen artifact as an execution-evidence destination.

## Approach

Correct one false premise at its source: the plan freezes in substance when `approve-plan` pins it, not when the feature ships. Add the sibling verification-ledger contract to the existing lifecycle reference, then make the template and small work-loop pointers route execution evidence there. A roster test joins the freeze guard to those authoring sources so reverting any one cannot silently restore the contradiction. Source changes precede projection regeneration, the index, and the release surface.

**Amended 2026-09-03.** T1-T5 shipped the distributed-restatement design and it did not hold: five review rounds each found a real guard defect, and rounds 4 and 5 each introduced defects while repairing others. The prose those tasks shipped is correct — measured against the merge-base, no surface carries the false premise in either vocabulary — so the defects are guard-side and T6 repairs them there. T1-T5 remain as executed; their sections are preserved unedited under the amendment.

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
| canonical authoring rule — convention seed and projection | T1, T5 | roster test; self-host regeneration | generated projection agrees with seed |
| portable verification-ledger procedure | T1, T2 | roster test | the shipped pointers resolve to the ledger procedure |
| executable contradiction guard | T3, T6 | mutation red and focused pytest | remote `tests/` gate includes it |
| spec index | T4 | README row follows new-spec format | index points to this spec |
| release history | T5 | version-parity and site-routing checks | topmost core entry and any highlights projection |
| delivery-local execution evidence | execution after approval | ledger only when observations occur | ledger remains outside approved hash |

## Design (LLD)

### Design decisions

- The ledger is Markdown at `docs/specs/<feature>/notes/verification-ledger.md`. It holds observed mutations, red results, assertion text, digest comparisons, and deviations; `spec.md` criteria and `plan.md` task rows retain obligations. Traces to: AC1, AC2, AC3.
- **Amended 2026-09-03, reduced the same day.** `packs/core/seeds/docs/CONVENTIONS.md` is the sole normative statement of the boundary; the how-to and `references/pre-execute-review.md` keep the correct statements they already had, and `references/state-schema.md` keeps its mechanism description unedited. T1-T2 already shipped that topology, and measurement against the merge-base confirms it: only the convention seed, the plan template and the public explanation ever carried the false premise in either vocabulary, and none of the eight surfaces carries it now. A first amendment proposed restructuring every surface into a pointer role; that was cut, because it reshaped correct shipped prose to make the test easier to write and the measured defects are all guard-side. Traces to: AC1, AC2.
- **`references/state-schema.md` § *What the pin covers* (:128-141) is already correct and this delivery does not edit it.** It is the most precise statement of the boundary in the repository — "Everything else stays pinned: acceptance-criterion text, task text, `Depends on:` edges" — and it already covers both artifacts. It joins the guard's agreement set so a later edit there cannot contradict the owner while every other mutation still reddens; naming the ledger there too would be a seventh home for one fact. Traces to: AC3.
- **Amended 2026-09-03.** The roster test exercises the real freeze guard and pins each guarded clause against its own bounded region. Three properties are structural, not stylistic: no clause may be satisfied from another region — including another region of the same file — no assertion may fall back to a whole file, and no check may key on general mutability vocabulary. Each was a measured defect, at V1, V2 and V3 respectively, in [`notes/verification-ledger.md`](notes/verification-ledger.md). Traces to: AC3.
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

### T6: Close the three measured guard defects

**Depends on:** T3

**Tests:**
- TDD: repair `tests/roster/test_verification_ledger_contract.py`. Remove the by-path region concatenation in the destination check (V1) and the whole-file `anchor=None` fallback for the plan template (V2); give the template's `Plan contract`, `Done when:` and `## Changelog` instructions one bounded region each, which closes V5; and delete `RESTATED_RULE_MARKERS`, whose general mutability vocabulary rejected correct Step 2 prose (V3). Keep exercising `assert_status_legal` and `canonical_contract` against the real module rather than pinning its source text.
- Mutation proof: one killing mutation per guarded clause — the canonical convention statement; each of the three retained statements, being the how-to's immutability sentence, `pre-execute-review.md`'s permitted-edit-set rule, and `state-schema.md`'s `Everything else stays pinned`; each of the template's three instructions; the ledger procedure's path and its unpinned/no-amendment clause; `work-loop/SKILL.md`'s Step 2 pointer; and the guarded region roster itself. Innocent-edit probes must include a re-wrap of each bounded region and ordinary Step 2 prose using the words "change substantively". Record every observed result in [`notes/verification-ledger.md`](notes/verification-ledger.md), never here.

**Approach:**
- Assert each clause against its own bounded region, and fail loudly on a missing or ambiguous anchor rather than widening. V1 and V2 were both widenings that let one region satisfy another's clause.
- Keep the region roster pinned independently of the table that drives the assertions, so deleting a region reddens instead of shrinking coverage. That defect recurred twice — at review round 2, and again inside round 4's own fix.
- Change no prose, no projection, and no release surface. Measurement against the merge-base shows the shipped guidance already correct, so this task is guard repair only. Dropping `RESTATED_RULE_MARKERS` also means the guard no longer claims `SKILL.md` is free of an independent rule; AC2 claims only a resolvable pointer, which is what remains mechanically checkable.

**Done when:** AC3's guard is green unmutated, every planned killing mutation reddens the clause it targets, and every innocent-edit probe stays green.

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
  boundary, and added one guard-repair task. Reason: review rounds 4 and 5 measured five
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
  sites. Reduced again the same day, before approval, on owner instruction to
  apply the razor to the whole contract: the proposed prose restructuring was
  cut entirely, leaving one guard-repair task. Measurement decided it — only the
  convention seed, the plan template and the public explanation ever carried the
  false premise in either vocabulary, all three corrections already shipped in
  T1-T2, and V1, V2 and V5 are repairable inside the guard module. Round 4
  sustained a Blocker on the first cut for leaving ten pointer-mandating clauses
  and a dangling `Depends on:` behind; this entry records the reconciled
  version.
- 2026-09-02: while `Drafting`, added `references/state-schema.md` § *What the
  pin covers* as the sixth rule-bearing source (eight killing mutations), and
  corrected the site total from 7 to 8. Reason: review round 3, both findings
  pre-existing and its verdict `CONVERGING`. The state-schema page
  independently states the pinned/exempt split and is already correct, so it
  takes guard coverage but no edit; and the union table's sites sum to 8, of
  which 7 are `Done when:` statements and one is a mutation-table row.
