# Plan: frontend-visual-authority

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (pack export boundary, version-bump
  rule, eval-harness obligation, self-host projection);
  `packs/frontend-engineering/.apm/skills/frontend-engineering/references/rendered-page-inspection.md`
  as the analogous shipped rule-table reference and
  `packs/frontend-engineering/tests/skills/frontend-engineering/frontend_engineering_rendered_page_rules.py`
  as its parser and construction path; `references/design-handoff.md` as the
  existing read contract this work consumes unchanged. Named uncertainty:
  whether the activation table's composition-change row should admit a
  state-restoring retrofit — recorded in the spec's Assumptions.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/frontend-visual-authority/notes/verification-ledger.md`.
> A genuine artifact error follows the controlled-amendment path.

## Approach

The pack already owns every mechanism this slice needs. Rendered observation,
capture/judgement separation, seven result states, a verdict and a
finding-class severity table ship at GATES step 5; the adopter's design tree is
already read under a hardened confinement contract; and the pack's established
idiom for a checkable rule is a Markdown table in a `references/` file that a
test-helper module parses. This work adds no runtime and no state machine: it
adds one reference carrying four rule tables, moves an existing block out of the
entrypoint to buy the line budget, and reuses the parser idiom for the tests.

The one structural decision is that visual authority is expressed over the three
adopter-owned read paths rather than over an upstream pack. Non-coupling has two
halves and the address is only the first: the rung conditions must also be
properties this pack defines, or a writer could satisfy every path and still
miss rung 1 by not emitting some upstream token. The existing read contract
forces the same discipline from the other direction —
`references/design-handoff.md` keys on no heading inside an artifact body, so a
precedence rule naming an upstream section would break a contract the corpus
already depends on.

## Constraints

- `skill_spec_lint.py:520` errors when `SKILL.md`'s post-frontmatter body
  exceeds 1000 lines, and the body starts within single digits of it. Read the
  current figure from `python3 -m agentbundle catalogue lint --root . --deep`
  rather than from a number stored here, which goes stale at T2. Every addition
  must be paid for by a removal before it lands, which is why T2 precedes T3.
- A new `## ` heading in `SKILL.md` truncates two section parsers. Both
  additions are `###` under existing `## ` headings.
- `PINNED_SKIP_COST` in `test_rendered_page_journey_promise.py` byte-pins three
  `accept-frontend-evidence` gate fields and one sentence; the manifest's
  `| unverified items |` row is pinned byte-exact in the same module.
- Every file added under `.apm/` is swept by the shipped-content guards: no
  repository identifier, no rate vocabulary, and any file naming a channel must
  use a declared channel name.
- A shipped-content file containing both `known exceptions` and
  `unverified items` must also name the inspection; the new references avoid
  that pair.
- `tools/lint-web-journey-parity.py` compares the web mirror's skill count to
  the number of skill directories; this slice adds no skill directory.
- `tests/roster/test_experience_journey_composition.py` requires four
  proportionality allowances, each with both of its cue words **on a single
  line** of the frontend journey. The stage-3 implementation-sequence line is
  the sole carrier of **two** allowances, not one: `narrows the state matrix`
  + `absent or broken`, and `inapplicable` + `omitted`. The rewrite must keep
  **each pair** co-located on one line. Splitting the sentence across lines
  reds `test_the_frontend_journey_carries_its_four_proportionality_allowances`
  even when every word survives.

## Construction tests

The new rule tables are parsed by a sibling helper module named for its pack and
skill, per `packs/AGENTS.md` § *Writing pack tests*. The helper states no rule:
it reads `references/visual-observation.md`, so a rule change moves the
reference rather than being restated in the suite. It reuses the existing
`table_rows` / `unique_keyed` readers rather than adding a second parser.

## Durable-output map

| Durable output (spec) | Task |
| --- | --- |
| Read contract: `references/design-handoff.md` refusal clauses renamed | T3 |
| Read contract: the `design-handoff-read` eval re-based off the deleted set | T3 |
| Guides: precedence order and observation loop | T7 |
| Guides: the tutorial's worked example re-based onto rung 4 | T7 |
| Journey stage 3 and the acceptance gate's `whatToCheck` | T6 |
| Matching bumped pack and plugin versions | T8 |
| Six eval cases A–F | T8 |
| Changelog entry | T8 |

## Design (LLD)

### Design decisions

**Authority is resolved over slots, not sections.** The four rungs name the
three read paths and the repository's own visual system. A rung is *supplied*
when its slot resolved and carries content; silence on an axis hands that axis
down, but a rung never hands down an axis it decided. This is the whole
non-coupling mechanism: any tool writing those addresses satisfies the rule.

**The top rung is keyed on a property this pack defines, not on an upstream
enum member.** Rung 1 requires that the artifact *records a human confirmation*
of the composition. That is a condition any writer can satisfy and any reader
can state without naming an upstream producer. Keying it on a particular
frontmatter literal would store a value whose owner is another pack's template,
which goes wrong at the next upstream edit and is a semantic dependency that no
declared-dependency check can see. An artifact recording no confirmation
resolves to `direction-and-taxonomy`, because a composition nobody confirmed is
design intent rather than an approved target. What this buys is bounded, and
the spec's Assumptions records the bound.

**The EXECUTE loop is not a gate.** Adding a sixth gate would move the
gate-count prose that verify mode derives and would put rendered observation
behind completion again, which is the failure this slice exists to fix. The loop
lives under `## EXECUTE phase — Craft Rules` and its captures are a
representative subset that does not discharge GATES step 5.

**The bound is stated as data, not prose.** `correction-passes: 1` in a parsed
table is a value a test can fail against; "iterate a couple of times" is not.

### Behavior & rules

`references/visual-observation.md` carries five rule tables. Their row keys and
cell values are fixed by the criteria the coverage table assigns to T3 and T4;
this section records only why each table exists, and deliberately restates none
of their content.

- `## Authority precedence` — the rung chain, and the demotion edge each rung
  takes when its condition is unmet.
- `## Authority limits` — what visual authority never controls, so a rung can
  never be read as licence over behaviour, accessibility, or security.
- `## Activation` — which work the observation loop applies to, and the record
  a skip owes.
- `## Loop bound` — where the loop stops, stated as data so a completion gate
  can read it.
- `## Divergence classes` — the perceptual axes a comparison reads. Guidance
  the loop consumes, not a gate; no criterion pins it.

### Failure, edge cases & resilience

- No design artifact resolves → rung 3, then rung 4; the run records which.
- No browser reachable → the observation loop records the shipped
  `skipped-no-browser` result state, claims no visual verification, and the
  remaining gates continue. This reuses the existing result-state vocabulary
  rather than adding an eighth state.
- A direction resolves but the surface is non-visual → activation skips, and the
  skip is recorded with its reason; authority is still recorded.

### Dependencies & integration

No new dependency. No new top-level directory. No new skill directory. The
`experience-design` entry in `pack.toml` stays `recommended`.

## Tasks

**How a task cites a criterion.** A `Tests:` bullet names the *mechanism* only —
which suite, which seam, which fixture, which shipped assertion moves. It names
no criterion identifier and re-enumerates no criterion content. Which criteria a
task discharges is stated once, in the coverage table below, and nowhere else:
a bullet that also listed them would be a second mapping that drifts on the next
criterion split, which is how this plan broke three rounds running. Three review rounds re-broke this plan at exactly those joins: a
criterion split in the spec left a stale paraphrase in a task, and the paraphrase
was sometimes broader than the criterion it claimed to implement. The coverage
table below is the single join between the two documents; there is no second one.

### Criterion coverage

Every criterion has exactly one owning task, and every task owns at least one.

| Task | Slice | Criteria |
| --- | --- | --- |
| T1 | 1 | none — baseline |
| T2 | 1 | AC-0007, AC-0008, AC-0009 |
| T3 | 1 | AC-0000, AC-0000b, AC-0001, AC-0002, AC-0003, AC-0003a, AC-0003b, AC-0004, AC-0004a, AC-0005, AC-0006 |
| T4 | 1 | AC-0000a, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014 |
| T5 | 1 | AC-0015, AC-0015a, AC-0016, AC-0017, AC-0018, AC-0018a, AC-0019a |
| T5r | 1 | AC-0019b, AC-0020, AC-0021, AC-0022, AC-0025 |
| T6 | 2 | AC-0019, AC-0019c |
| T7 | 2 | AC-0023, AC-0023a, AC-0024, AC-0024a, AC-0024b |
| T8 | 2 | AC-0025a |

T1 owns no criterion: it establishes the pre-change baseline the later tasks are
measured against.

### T1: The pre-change baseline and the anchor inventory exist

**Depends on:** none

**Touches:** docs/specs/frontend-visual-authority/notes/

**Tests:**
- `python -m pytest packs/frontend-engineering/tests/skills/frontend-engineering/ -q` green before any edit, recorded in the verification ledger as the pre-change reading.
- An inventory, in the ledger, of every shipped assertion this slice moves, each naming the task that moves it: the lens-count and stale-phrase guards in `test_rendered_page_reviewer_sight.py`, the field-count derivation in `test_rendered_page_result_recording.py`, and the byte-pinned gate fields in `test_rendered_page_journey_promise.py`.

**Done when:** the ledger carries the baseline reading and the inventory, and every inventory entry names a task.

### T2: The seed token block leaves the entrypoint and the line budget is recovered

**Depends on:** T1

**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md, packs/frontend-engineering/.apm/skills/frontend-engineering/references/fallback-tokens.md

**Tests:**
- New assertions in the pack suite for the token-block removal and the body budget.
- Both halves of the token-removal predicate are anchored rather than bare containment, and both are exercised against the pre-change file: the token half must not reach the prose mention or the focus-visible rule, and the block half must reach the print companion as well as the seed block.
- `python3 -m agentbundle catalogue lint --root . --deep` exits zero, with `--deep` as the spec's Agent Rules requires. It is necessary but not sufficient: the body budget is what holds the line.

**Approach:**
- This task lands before T3 because the body sits within single digits of the hard error; an addition made first fails the build gate regardless of its merit.

**Done when:** every criterion the coverage table assigns to this task is green and the deep lint exits zero.

### T3: Visual authority is resolved by a stated precedence and the product-reference table is gone

**Depends on:** T2

**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md, packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md, packs/frontend-engineering/.apm/skills/frontend-engineering/references/design-handoff.md, packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json, packs/frontend-engineering/tests/skills/frontend-engineering/

**Tests:**
- A new helper module, named for its pack and skill, reads the rule tables in `references/visual-observation.md`. It extends the existing rendered-page rules module's `table_rows` / `unique_keyed` readers rather than adding a second table parser, so one pipe policy governs both references. Probe result: both readers already take markdown as an argument and are generic; only `read_rules` is path-bound.
- Assertions over those tables for the rung chain, its `requires`, `falls-to` and `source` cells, and the authority-limits set.
- A separate assertion that reads `SKILL.md` itself and requires the pre-flight to carry the four rung keys in order and to name the reference. Every other bullet in this task reads the reference or greps for absence; without this one the reference can be perfectly correct and the always-loaded entrypoint can route to none of it, with every criterion green.
- Literal-list assertions, each taking its list, its case handling and its cell scoping from the criterion rather than restating one here. The cell-scoped upstream-vocabulary check is the one that can newly fail on semantic coupling; the declared-dependency checks in T8 already hold today.

**Approach:**
- Every occurrence the stranded-pointer predicate matches is renamed to the standalone fallback rung, never dropped. Some are refusal clauses, and there the semantics is the point: a refusal must not fall through to a fallback, and that outlives the table's name.
- The `design-handoff-read` eval currently asserts the agent reaches the canonical product-reference set from a named skip. Deleting the set makes that assertion unsatisfiable, so it is re-based onto the fallback rung in this task rather than left to fail against a correct implementation.

**Done when:** every criterion the coverage table assigns to this task is green and the precedence table is the only place stating the rung order.

### T4: Significant visual work is rendered, observed, and corrected within a stated bound

**Depends on:** T3

**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md, packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md, packs/frontend-engineering/tests/skills/frontend-engineering/

**Tests:**
- Table assertions for the loop bound and the activation rubric.
- A separate assertion that reads `SKILL.md` itself and requires the EXECUTE phase to state the render → observe → correct sequence, the one-correction bound, and the reference pointer. Same seam and same reason as T3's entrypoint assertion.
- A rejection test driving candidate values through the same predicate shape `observations_value_is_acceptable` already uses for the observations field.
- `test_verify_mode_enumerates_every_gate_in_order` still passes unchanged, proving the loop did not become a sixth gate and the gate-count prose did not move.

**Approach:**
- The loop goes under the existing `## EXECUTE phase` heading as a `###`. A new `## ` anywhere would truncate a section parser; adding a gate would move the count that verify mode derives and would put rendered observation back behind completion, which is the failure this slice exists to fix.

**Done when:** every criterion the coverage table assigns to this task is green and the gate-order assertion is untouched.

### T5: The manifest records which authority was used, and the reviewer can test that claim

**Depends on:** T4

**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md, packs/frontend-engineering/.apm/skills/fe-status/SKILL.md, packs/frontend-engineering/.apm/agents/frontend-reviewer.md, packs/frontend-engineering/tests/skills/frontend-engineering/

**Tests:**
- An assertion for the new manifest row. The shipped `test_the_manifest_field_count_matches_the_table` derives the heading count from the table and supplies the coherence consequence for free; this task adds no second assertion for it.
- Reviewer assertions for the new lens, its confirmation scoping, the lens count, the banned count-phrases, and the agent's routing description — each taking its literals and case handling from the criterion by reference.
- The body-budget assertion T2 introduced is still green. T3, T4 and T5 each add to `SKILL.md` after T2 freed the room, and T5 is the last of them to write it.

**Approach:**
- The confirmation-scoping criterion exists because the shipped guard only asserts the Lens 1-5 and Lens 6 strings are present. A seventh lens can otherwise land with no confirmation scoping and nothing reds — which is the failure that once left Lens 6 unable to produce a finding at all.
- `fe-status` moves from `12-field` to `13-field` here, with the manifest row, because the two are one fact with two homes and splitting them ships a contradiction. The frontend skill's own `12-field contract` at a separate site is the page/screen contract — a different twelve — and is deliberately untouched.

**Done when:** every criterion the coverage table assigns to this task is green, T2's body-budget criterion is still green, and the full pack suite passes.

### T5r: Slice 1 ships as a coherent release

**Depends on:** T5

**Touches:** packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json, docs/product/changelog.md

**Tests:**
- Assertions for the first-value strings, the absence of a required cross-pack dependency, the empty prerequisite-pack list, and the six eval ids, with `test_pack_and_plugin_versions_match[frontend-engineering]` carrying the version pair.
- The eval-harness shape lint passes over the added cases.
- `python -m agentbundle catalogue self-host --root . --check` reports no drift.

**Approach:**
- This task exists because the split made slice 1 a standalone pack change. The pack rule obliges every non-cosmetic pack update to carry its own version bump and to update its own eval harness, so slice 1 cannot borrow slice 2's release.
- The six control-flow eval cases land here rather than in slice 2: they exercise the precedence and the observation loop, which are slice 1's behaviour.

**Done when:** every criterion the coverage table assigns to this task is green and the pack installs at `0.3.4` with the new pre-flight described in its first-value strings.

---

## Slice 2 — the documentation and release surface

Everything below ships as a second, independently reviewable PR against this
same spec, after slice 1 merges. The spec stays `Implementing` until T8 closes.

### T6: The journey and its web mirror describe the shipped behaviour

**Depends on:** T5

**Touches:** packs/frontend-engineering/JOURNEY.md, web/src/content/journeys/frontend-engineering.md

**Tests:**
- Assertions for the review gate naming the new lens, and for the empty prerequisite-pack list.
- `python3 tools/lint-pack-journeys.py`, `python3 tools/lint-journey-contract.py` and `python3 tools/lint-web-journey-parity.py` all exit zero.
- `test_rendered_page_journey_promise.py` passes with `PINNED_SKIP_COST` untouched, proving the edit stayed outside the byte-pinned gate fields. The `visual authority` addition goes in the gate's `whatToCheck`, which is not among them.
- The roster composition test still finds the three crossing-artifact strings in both journey files.

**Approach:**
- The web mirror is regenerated with `python3 tools/build-site.py --journeys-only` rather than hand-edited: two committed homes with no lint between them drift silently.

**Done when:** every criterion the coverage table assigns to this task is green and the three lints exit zero.

### T7: Adopter guidance states the precedence and names no product as an anchor

**Depends on:** T6

**Touches:** guides/frontend-engineering/how-to/read-the-design-handoff.md, guides/frontend-engineering/tutorials/scaffold-a-component.md, guides/frontend-engineering/how-to/run-an-audit.md, guides/frontend-engineering/README.md, guides/frontend-engineering/reference/frontend-engineering.md

**Tests:**
- Assertions for the guide tree carrying no product anchor, and for the how-to naming the rung order.
- `test_every_manifest_describing_surface_names_the_inspection` still passes over the guide tree it sweeps.
- `python3 tools/lint-guide-titles.py` and `python3 tools/check-guide-index.py` exit zero.

**Approach:**
- The tutorial is the real work, not a wording pass: it uses one product as its worked example throughout and carries a whole step named for choosing one. Its brief states a visual premise in the pack's own words instead, and that step becomes the standalone fallback rung — so the tutorial demonstrates the rung an adopter without a design tree actually walks.
- The two guide manifest examples gain the `visual authority` line, so a reader comparing an example against the field list does not find a shorter manifest.

**Done when:** every criterion the coverage table assigns to this task is green, both lints exit zero, and the tutorial's worked example names no product.

### T8: The pack ships as a coherent release

**Depends on:** T7

**Touches:** packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, docs/product/changelog.md

**Tests:**
- `test_pack_and_plugin_versions_match[frontend-engineering]` carries the slice-2 version pair.
- `python -m agentbundle catalogue self-host --root . --check` reports no drift after the write.

**Done when:** every criterion the coverage table assigns to this task is green, the conformance suite passes, and the changelog entry names the documentation surface slice 2 corrected.

## Rollout

**Version level.** `0.3.4`, a patch. `packs/README.md` § Versioning
expectations gives three increments — patch for changed bodies, minor for new
primitives, major for removals — and primitives there are the `.apm/`
directories: skills, agents, commands, hooks. This slice adds no primitive: two
files under an existing skill's `references/` and a seventh lens inside an
existing agent are both changed bodies. It removes no primitive either, so the
major clause does not fire; what it removes is guidance *within* a skill.
An earlier draft argued minor on the ground that the change is new capability
rather than a pure content edit. That is a fourth category the rule does not
define, so it is not a trigger the rule supplies, and the rule governs.

Additive to the pack's guidance surface. An adopter on the prior version keeps
a working pre-flight; the removed product table had no mechanical consumer, and
the new manifest field is recorded by the same run that writes the rest of the
manifest. No migration, no data change, no deployment step.

## Risks

- The `SKILL.md` body sits within single digits of the 1000-line hard error,
  which makes ordering load-bearing. T2 is sequenced first for exactly this
  reason. Read the current figure from the lint, not from this document.
- Moving the stale-phrase guard from six to seven lenses touches a test whose
  purpose is to catch exactly that kind of edit. The mitigation is that the
  guard moves in the same task as the lens it guards, so a half-applied change
  reds rather than passing quietly.

## Changelog

- Drafted.
- Build strategy approved by the owner; baseline locked. Slice 1 implementing.
- Scope approved by the owner, with the delivery split at the T5/T6 boundary:
  slice 1 is the executable contract in `packs/frontend-engineering/.apm/`,
  slice 2 is the journey, guide tree and their release. The owner also settled
  the version level at patch and declined the cross-pack correction of the two
  `experience-design` sentences, which is recorded as a Follow-on.
