# Plan: intent-triad-execution-wiring

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` and `packs/AGENTS.local.md` (pack
  release pipeline and pack-local conventions); `packs/product-engineering/tests/pack/test_de_risk_intent_reviewer_boundary.py`
  and `test_frame_intent_shaping_review.py` as the two analogous pack tests this
  delivery's new test is modelled on — both resolve `PACK_ROOT` as
  `Path(__file__).resolve().parents[2]` and read only inside the pack, which is
  the constraint a pack test is under; `docs/adr/0111-intent-review-splits-well-formedness-from-assumption-attack.md`
  and `docs/rfc/0053-*.md` as the governing decisions.

## Approach

Three independent text edits, each with a pack test that reads the shipped
artifact. T1, T2 and T3 have no ordering relationship with one another: no
criterion requires the G3 prose to name the `delivery-contract` slot, so
documenting the slot types is not a precondition for the handoff edit. The one
real ordering constraint is that T4's version bump follows every task that can
touch pack content, T5 included.

The new test file sits beside the two existing pack tests and reads only within
`packs/product-engineering/`, because a pack test that reads above its pack
cannot run in the packaged tree.

## Constraints

- Markdown and its tests only. No new module, package, script, or dependency.
- The schema's blackboard `type` list is an open list ending in `…`; this
  delivery documents three members, and does not close the list.
- `tests/roster/test_shaping_handoff_pack_surface.py` asserts the literal
  substrings `"portable rendered"` and `"Core absence"` in `discovery-loop/SKILL.md`,
  and digest-pins `normalized-intake` against its projections. The G3 edit is
  additive around those strings.
- `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py:131`
  pins `frame-intent`'s `allowed-tools` value byte-for-byte, and
  `test_de_risk_intent_reviewer_boundary.py:45` asserts the no-dispatch boundary
  appears exactly once. Neither file is edited by this delivery.

## Construction tests

One new file, `packs/product-engineering/tests/pack/test_intent_triad_execution_wiring.py`,
carrying the tests T1, T2, T3 and T5 name — the task list is the single source of
which those are. It reads `sidecar-schema.md`, `discovery-lead.md`,
`discovery-loop/SKILL.md`, `decompose-intent/SKILL.md`, and
`recursive-decomposition.md`, and `frame-intent/SKILL.md` from `PACK_ROOT`, and nothing else.

AC14, AC15 and AC16 are verified outside this file by delivery-time checks, and
carry no `test_` function name. Their subjects — the two version files,
`guides/product-engineering/`, and `docs/product/changelog.md` — sit above
`packs/product-engineering/`, and a pack test may not read above its own pack.
T6 therefore contributes no test to this file.

T1's three tests split by assertion, not by surface. The criteria now read two
surfaces — the blackboard `type` field row and the "Data classification &
handling" section — and the conformance summary is deliberately unchanged. The
split is what catches the drift: a slot named in the field table but absent from
the classification section passes a whole-file grep.

The gate-ladder test slices `discovery-lead.md` to `^## How you run the loop$`
before asserting, and requires each skill name to sit beside its gate, because a
whole-file assertion passes on a mention added to any other section and a
section-scoped one passes on an unpaired list.

The G3 tests isolate one named sentence per surface before asserting. The spec's
Testing Strategy states why; this plan adds only the anchors — `portable
rendered`, `If Core is absent`, `Otherwise render` — chosen because the three
surfaces share no common phrasing for the Core-absent branch.

The `description` field is 866 characters against the `maxLength: 1024` in
`contracts/skill.schema.json:20`, leaving 158 for the exclusion-clause edit.

## Durable-output map

| Durable output (spec) | Task | Evidence |
| --- | --- | --- |
| Interface compatibility — `sidecar-schema.md` | T1 | `test_each_new_slot_type_is_named_and_shaped`, `test_the_classification_section_states_the_starting_level`, `test_the_classification_section_states_the_floor_rule` |
| Current product truth — `discovery-lead.md` | T2 | `test_the_gate_ladder_walk_pairs_each_triad_skill_with_its_gate` |
| Current product truth — `discovery-loop` description | T2 | `test_the_standalone_exclusion_keeps_two_names_and_drops_one` |
| Interface compatibility — G3 handoff surfaces | T3 | `test_the_skill_fallback_sentence_names_work_intake`, `test_the_decompose_skill_core_absent_sentence_names_work_intake`, `test_the_recursive_decomposition_fallback_sentence_names_work_intake`, plus the unchanged roster test |
| Current product truth — the `frame-intent` `## Pick a route` section | T5 | `test_frame_intent_carries_the_pick_a_route_section`, `test_the_route_menu_names_three_routes_with_a_fit_line`, `test_the_menu_names_no_six_step_skill_but_frame_situation`, `test_discovery_loop_points_at_the_menu` |
| Release history — versions, `.claude-plugin/marketplace.json`, changelog | T4 | the delivery-time version-parity read against the merge-base, plus the `[Unreleased]`-anchored changelog-heading check |
| User-facing promise — the two named guide passages | T6 | the delivery-time `run-a-discovery.md` route check (AC15), plus the recorded no-op read of `the-discovery-loop.md` |

## Design (LLD)

### Design decisions

- **The G3 fallback names `work-intake`, matching the negotiated branch.** The
  shipped `shaping-intake-handoff` spec states that Core absence "retains the
  current standalone core classification and direct-core behavior", so the seam
  is the same on both branches and only the envelope differs. Routing the
  fallback to `new-spec` instead would skip workspace registration and force a
  second fallback target for the delivery-brief role.

### Data & schema

`assumption-test` carries the `de-risk-intent` verdict: the riskiest assumption,
the predeclared kill condition, the chosen prototype-approach, and the
`validation_hook` the skill already emits. Classification `internal` — it holds
product strategy, which is the level the schema's own table assigns to that.

`delivery-contract` carries the G3 leaf projection. Classification `internal`.

`shaping-review` is **not** in this delivery. Storing text authored outside the
loop in the blackboard is a data-handling design, and two spec-stage security
rounds established it needs its own shaping pass; the spec's Follow-ons carry the
five questions those rounds raised.

### Interfaces & contracts

No contract file, and the sidecar schema's "Conformance summary" is unchanged:
its five points are guarantees about the instance as a whole, and naming two more
slot types adds no guarantee a consumer relies on.

### Failure, edge cases & resilience

A discovery that ran before this change has neither new slot. Absence is the
existing state and stays legal: no criterion requires either slot to be present,
only that its shape and starting classification are documented when one is
written.

## Tasks

### T1: The two slot types carry a name, a field set, and a starting classification

**Depends on:** none

**Tests:**
- `test_each_new_slot_type_is_named_and_shaped` — for each of `assumption-test` and `delivery-contract`, assert the name appears in the blackboard `type` field row and that its field set is stated. Verifies AC1, AC4.
- `test_the_classification_section_states_the_starting_level` — assert the classification section names `internal` as the level a controller starts from for both types. Verifies AC2.
- `test_the_classification_section_states_the_floor_rule` — assert the section states, beneath its existing "assigns at write time" opening, that a starting level named for a slot type is a floor a write-time assessment may raise. Assert only the floor sentence: the write-time sentence is shipped text and asserting it would make half the guard green before the edit. Verifies AC3.
- Whitespace: every assertion against `sidecar-schema.md` prose normalises first. The anchor sentence wraps mid-phrase across two source lines — `Each slot carries — or the skill assigns at write time — a **data-classification` / `level**:` — so a literal comparison reds on a correct edit. Both existing pack tests already carry the idiom (`_flat()`, `re.sub(r"\s+", " ", text)`); reuse it rather than re-deriving one.

**Done when:** `test_each_new_slot_type_is_named_and_shaped`, `test_the_classification_section_states_the_starting_level`, and `test_the_classification_section_states_the_floor_rule` are all green.

### T2: `discovery-lead`'s walk names the triad and the exclusion stops routing `frame-intent` away

**Depends on:** none

**Tests:**
- `test_the_gate_ladder_walk_pairs_each_triad_skill_with_its_gate` — slice `discovery-lead.md` to `^## How you run the loop$`; assert `frame-intent` sits beside G0, `de-risk-intent` beside G1, and `decompose-intent` beside both G1 and G3. Verifies AC5.
- `test_the_standalone_exclusion_keeps_two_names_and_drops_one` — parse `discovery-loop/SKILL.md`'s frontmatter `description`; assert the exclusion clause names `frame-domain` and `explore-options` and does not name `frame-intent`. Verifies AC6.

**Approach:**
- The description edit removes `frame-intent` from the exclusion list rather than deleting the clause: `frame-domain` and `explore-options` are genuinely standalone-authorable and the clause still holds for them.

**Done when:** `test_the_gate_ladder_walk_pairs_each_triad_skill_with_its_gate` and `test_the_standalone_exclusion_keeps_two_names_and_drops_one` are both green, and the `description` stays within its 1024-character cap (`contracts/skill.schema.json`).

### T3: The Core-absent branch names `work-intake` on all three surfaces

**Depends on:** none

**Tests:**
- `test_the_skill_fallback_sentence_names_work_intake` — isolate the sentence containing `portable rendered` in `discovery-loop/SKILL.md`'s "Capability-negotiated G3 handoff"; assert it names `work-intake`. Verifies AC7.
- `test_the_decompose_skill_core_absent_sentence_names_work_intake` — isolate the sentence beginning `If Core is absent` in `decompose-intent/SKILL.md`; assert it names `work-intake`. Verifies AC8.
- `test_the_recursive_decomposition_fallback_sentence_names_work_intake` — isolate the sentence beginning `Otherwise render` in `recursive-decomposition.md`; assert it names `work-intake`. Verifies AC9.

**Done when:** `test_the_skill_fallback_sentence_names_work_intake`, `test_the_decompose_skill_core_absent_sentence_names_work_intake` and `test_the_recursive_decomposition_fallback_sentence_names_work_intake` are all green, and `python3 -m pytest tests/roster/test_shaping_handoff_pack_surface.py packs/product-engineering/tests/pack -q` passes with no edits to `test_shaping_handoff_pack_surface.py`, `test_frame_intent_shaping_review.py`, or `test_de_risk_intent_reviewer_boundary.py`.

### T4: The four-step release pipeline completes

**Depends on:** T1, T2, T3, T5, T6

**Tests:**
- Goal-based, delivery-time: the two version files carry equal versions ordering after the baseline AC14 defines, compared as semantic versions. Deliberately not a shipped pack test — the baseline is a fact about this delivery, and an assertion pinned to one version string asserts nothing once this PR merges. Verifies AC14.
- Goal-based, delivery-time: the new `## [product-engineering][<version>] — <date>` heading is the first `## ` heading after `## [Unreleased]`, and its version equals the bumped pack version. This check reads `docs/product/changelog.md`, which sits above the pack, so it cannot be a pack test either. Verifies AC16.

**Approach:**
- Ordering: all four steps of `packs/AGENTS.local.md` § "Marketplace and release pipeline" run here in its stated order — bump both versions, `FORCE=1 make build-self` to regenerate `marketplace.json`, the free-standing `##` changelog entry, then the `Highlights` disposition. Steps 1 and 2 have no mechanized guard, which is why they are a task rather than a convention.
- The changelog check anchors on `[Unreleased]` rather than the first `## ` heading: `docs/product/changelog.md:63` is a permanent `## [Unreleased]`, so a first-heading check reports the same line whether or not the entry landed.

**Done when:** both delivery-time checks pass, `.claude-plugin/marketplace.json` is regenerated, and the changelog entry carries an explicit `Highlights` disposition.

### T5: `frame-intent` carries the cross-sequence `## Pick a route` section

**Depends on:** none

**Tests:**
- `test_frame_intent_carries_the_pick_a_route_section` — assert `frame-intent/SKILL.md` has a `## Pick a route` heading, and that it falls between `## When to invoke` and `## Procedure`. Verifies AC10.
- `test_the_route_menu_names_three_routes_with_a_fit_line` — slice to the `## Pick a route` section; assert three routes, each with a one-line fit statement, naming respectively the three triad skills, `discovery-loop`, and `frame-situation`. Verifies AC11.
- `test_the_menu_names_no_six_step_skill_but_frame_situation` — within that slice only, assert `frame-situation` is present and `identify-opportunities`, `diverge-solutions`, `place-bet`, `map-capabilities` are absent. The slice is what makes this safe: `identify-opportunities` is named legitimately in `frame-intent`'s step 5 opportunity-scoring pointer, which this delivery does not touch. Verifies AC12.
- `test_discovery_loop_points_at_the_menu` — read `discovery-loop/SKILL.md`'s "When to invoke"; assert it references the `## Pick a route` section. Verifies AC13.

**Done when:** all four tests green.

### T6: The guides and eval harnesses reconcile with the shipped artifacts

**Depends on:** T1, T2, T3, T5

**Tests:**
- Goal-based, delivery-time: `run-a-discovery.md`'s "When it hands off" section names the same G3 continuation route as `discovery-loop/SKILL.md`'s gate-table G3 row. Reads above the pack, so it carries no `test_` name and does not enter the pack test file. Verifies AC15.

**Approach:**
- Seam: `the-discovery-loop.md` is a **verified no-op**, and carries no criterion for that reason. The read that establishes it: line 48 already names `work-intake` as the admitting route and lines 50-53 already state the Core-absent branch renders the same bounded content. The guide leads the skill here, so T3's edit brings the skill up to the guide rather than the reverse. `run-a-discovery.md:70` says G3 hands to `work-loop` and names no route — that is the passage AC15 covers.
- `discovery-loop` and `decompose-intent` each ship `evals/eval_queries.json` and `evals/evals.json`, and this delivery edits `discovery-loop`'s frontmatter `description`, which is the trigger surface evals measure. Update both harnesses, or record in the verification ledger that the edit changes no eval-visible behavior and why.

**Done when:** AC15's delivery-time route check passes, the `the-discovery-loop.md` no-op read is recorded in the verification ledger, and each edited skill's eval harness is either updated or carries a verification-ledger entry stating why it needed no change.

## Rollout

- **Delivery:** big bang, single PR. Reversible by reverting the PR; no runtime state, no migration, no deployed surface.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** carried in `Depends on:`, not in this prose — T1, T2, T3 and T5 are independent; T6 follows them because it reconciles the guides against what they ship; T4 follows all five, because T6 may edit `.apm/**` eval harnesses and `packs/AGENTS.md` § "Version bump rule" makes every non-cosmetic `.apm/**` change bump the version T4 sets.

## Risks

- A roster or pack test reads a string this delivery moves and was not found by the sweep. Mitigated by running the full `packs/product-engineering/tests/pack` directory plus the two roster handoff suites before review, not only the new file.
- The `discovery-loop` description edit pushes the field over its 1024-character cap. T2's `Done when:` checks it.

## Changelog

<!-- approvals only; not how the approach evolved -->

- 2026-09-20 — spec approved by eugenelim. 16 acceptance criteria over 6 tasks.
  Pre-EXECUTE review: `adversarial-reviewer` clean after seven rounds;
  `security-reviewer` clean after four spec-stage rounds. The `shaping-review`
  slot was cut from scope during those rounds and is carried as a follow-on.
- 2026-09-20 — plan approved by eugenelim. Six tasks: T1, T2, T3 and T5 are
  independent; T6 follows them; T4 last, because T6 may edit `.apm/**` eval
  harnesses and the version bump must cover them.
