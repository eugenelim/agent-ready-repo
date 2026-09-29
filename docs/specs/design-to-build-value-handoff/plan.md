# Plan: design-to-build value handoff

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> record why in the changelog.

## Approach

Add one named state — the **upstream gap** — to the frontend visual-authority
rules, and let every other surface state it. The gap is not a rung: a rung
supplies a decision, and a gap withholds one. Modelling it as a fifth rung would
put a "stop here" row inside a table whose whole grammar is "resolve from here",
and would break the demotion chain the precedence table pins.

So the frontend reference grows a sibling section to `## Refusals are not
demotions`, with the same shape: a small rule table whose rows the existing
table readers already sweep. The entrypoint states the contract in a few lines
and routes to that reference for the rules. The fallback token block and
`local-premise` stop being reachable by default and become admissible only for
work that is genuinely standalone.

On the design side the change is smaller, because `design-system` already
derives concrete values and already records an unresolved domain with its owner.
It gains the one field the frontend needs to route on — the operation that
supplies the domain — and one sentence forbidding a consumer from filling the
gap. The rest of the design-side work is orchestration prose: the journey, the
maintainer doc and the public how-to stop calling the skill broadly optional and
state the condition instead.

## Repository anchors

- **Governing decision:** `docs/adr/0130-design-to-build-handoff-is-conditional-and-gap-routed.md`,
  authored during PLAN because the supersession convention requires the pointer
  in a superseded document's `Status` field to name an ADR, and no existing ADR
  records this decision. ADR-0128 is the closest and stops one step short: it
  decides that `design-system` resolves project values, not who owns a value it
  did not resolve.
- **Explicit source:** `docs/specs/frontend-visual-authority/spec.md` (the rung
  contract and AC-0009's body budget), `docs/specs/design-handoff-read/spec.md`
  (the read contract and its six refusals),
  `docs/specs/frontend-experience-composition/spec.md` AC-0020/AC-0021 (the
  say-this optionality vocabulary and its cross-surface agreement).
- **Analogous implementations:** `## Refusals are not demotions` in
  `packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md`
  is the exact precedent for a non-rung rule table beside the precedence table;
  `## Activation` in the same file is the precedent for an enumerated-value rule
  table.
- **Their tests:** `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_precedence.py`
  and `test_visual_authority_refusal_boundary.py` read those tables through
  `frontend_engineering_visual_authority_rules.py`; the new module reuses the
  same readers, so a rule change moves the reference and not the suite.
- **Named uncertainty:** whether an adopter with a partially-covering incumbent
  system should be routed upstream for the remainder. Recorded in the spec's
  Assumptions; this delivery routes only genuinely open axes.

## Constraints

- `references/visual-observation.md` may not name an upstream pack or skill:
  `test_the_reference_names_no_upstream_producer` enforces it, and the frontend
  pack installs standalone. The routing target is the owner an artifact records,
  or the operation that writes `tokens/<slug>.md`.
- `SKILL.md`'s body budget is contract. Spec AC-0013 raises it from 960 to 968
  and says so; raising the test constant without the AC is forbidden.
- The say-this optionality vocabulary is contract. Spec AC-0018 adds
  `Conditional` and says so; the roster test's `OPTIONALITY` tuple and the guide
  reader both move with it.
- The guide `Needed?` cell must be exactly one vocabulary member — the roster
  reader skips any cell that is not — so the condition goes in prose beside the
  table, never inside the cell.
- Pack tests may not read above their own pack
  (`tools/test-lint-pack-test-boundary.py`), so every cross-tree assertion
  extends an existing `tests/roster/` module rather than a pack suite. No new
  roster file, which would also oblige a named CI step and a
  `tools/lint-ci-parity.py` entry.
- `packs/experience-design/` may carry no design value;
  `tools/lint-experience-agnostic.py` and the pack contract suite both check it.
- Non-cosmetic `.apm/**` changes bump matching `pack.toml` and
  `.claude-plugin/plugin.json` versions and update the pack's eval harness.
- `web/src/content/journeys/experience-design.md` is generated; regenerate with
  `make build-self`, never edit.
- Four phrases must survive the `local-premise` amendment **inside the first
  paragraph after the `**`local-premise`**` marker**, because
  `test_visual_authority_precedence.py` reads only up to the first blank line:
  `subject matter`, `category alone`, `reaction against it`, `never a product`.
  Removing `always available` must not split that paragraph.
- A superseded frozen spec takes its pointer in its `Status` field and nowhere
  else, in the form `Shipped (superseded in part by ADR-NNNN — <what changed>;
  everything else stands)`. The status linter truncates at the first ` (`, so an
  annotated status still satisfies the vocabulary rule.

## PLAN record

### Assumption trio

- **Files:** this spec directory; four files under
  `packs/frontend-engineering/.apm/skills/frontend-engineering/` (`SKILL.md`,
  `references/visual-observation.md`, `references/design-handoff.md`,
  `references/fallback-tokens.md`) plus its `evals/evals.json`; three files under
  `packs/experience-design/.apm/skills/design-system/` (`SKILL.md`,
  `assets/token-taxonomy-template.md`, `evals/evals.json`);
  `packs/experience-design/JOURNEY.md` and `DESIGN.md`; two guide pages;
  both packs' `pack.toml` and `.claude-plugin/plugin.json`;
  `docs/product/changelog.md`; `workspace.toml`; one new pack test module and
  three existing test modules; generated projections.
- **Done tests:** the new and extended construction tests pass; `make lint-ruff
  lint-mypy` clean; the catalogue lint and verify exit zero;
  `tools/lint-experience-agnostic.py` exits zero; the six acceptance scenarios
  each resolve to their required result under the shipped rules.
- **Not changing:** the four rungs and their order; the six refusals and the
  rule that a refusal never demotes; the standalone greenfield path; the
  handoff read's confinement, bounds and confirmation controls; the number of
  skills in either pack.

### Declined patterns

- **A fifth `upstream-gap` rung in the precedence table** — declined under
  `Cut before adding` rung 1 (skip an addition that is not genuinely needed):
  the gap withholds a decision rather than supplying one, so it does not belong
  in a table of suppliers, and inserting it would break the pinned demotion
  chain for no behavioural gain.
- **A new `routing` reference file** — declined under rung 2 (one bounded search
  for an adequate repository solution): `visual-observation.md` already owns the
  precedence and the refusal boundary, and a second file would split one rule
  across two places.
- **A machine-readable gap record (JSON/front-matter field)** — declined under
  rung 1: nothing in this repository consumes such a field, and the evidence
  manifest's `visual authority` row is already the recording surface.
- **A shared cross-pack vocabulary module** — declined under rung 1 and the
  spec's Never-do: the frontend pack installs standalone, so a shared module
  would create the dependency the precedence rules exist to avoid.
- **A fourth optionality value spelled `Required (conditional)`** — declined
  because the roster reader matches vocabulary members by substring, so that
  spelling would silently register as `Required` and the two surfaces could
  disagree while the agreement check passed.

### Resolve-vs-surface disposition record

- **Resolved in PLAN:** the gap is a rule table, not a rung; the routing target
  is artifact-recorded rather than pack-named; cross-tree assertions extend
  existing roster modules; the body budget and optionality vocabulary are
  amended in the spec rather than in the tests.
- **Surface during EXECUTE:** an inability to state the entrypoint contract
  within the 968-line budget; a pinned literal in another delivery's suite that
  the gap wording breaks; a concurrent pack-version advance on either pack.
- **Status:** open until DECIDE.

## Construction tests

**New module** —
`packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_upstream_gap.py`,
importing `frontend_engineering_visual_authority_rules` so the tables are read,
never restated:

- `test_the_upstream_gap_table_states_its_rules` — AC-0001.
- `test_the_gap_names_both_of_its_sources` — AC-0002.
- `test_the_gap_holds_only_the_axes_it_names` — AC-0003.
- `test_a_lower_rung_fills_only_a_genuinely_open_axis` — AC-0004.
- `test_the_terminal_rung_requires_no_upstream_gap` — AC-0005.
- `test_the_standalone_table_enumerates_its_three_conditions` — AC-0006, AC-0007.
- `test_the_standalone_table_requires_a_completed_read` — AC-0037.
- `test_the_preflight_states_the_gap_and_routes_to_the_reference` — AC-0009,
  scoped to the PLAN pre-flight window via the shared `preflight()` reader.
- `test_no_shipped_file_says_the_terminal_rung_is_always_available` — AC-0010,
  sweeping `WHOLE_EXPORT_TREE`.
- `test_the_fallback_condition_carries_three_conjuncts` — AC-0011, AC-0012.
- `test_the_handoff_reference_hands_the_gap_forward` — AC-0014.
- `test_the_gap_target_handling_states_its_display_rule` — AC-0032.
- `test_a_refusal_never_becomes_a_gap` — AC-0033.
- `test_the_gap_record_persists_no_person_identifying_value` — AC-0034.
- `test_the_upstream_gap_evals_exist_and_route` — AC-0023, AC-0024, AC-0025.

**Extended** —
`packs/experience-design/tests/skills/design-system/test_design_system_contract.py`:
AC-0015 (template column set), AC-0016 (consumer may not fill), AC-0026 (eval
names the operation).

**Extended** — `tests/roster/test_experience_journey_composition.py`:

- `test_the_say_this_optionality_agrees_with_the_how_to_guides` and
  `test_every_say_this_row_carries_exactly_one_optionality`, with `Conditional`
  added to the module's `OPTIONALITY` tuple — AC-0017, AC-0018.
- `test_the_journey_states_when_the_design_system_is_required` — AC-0019, a
  phrase-presence check on the journey's condition prose.
- `test_the_how_to_states_both_halves_of_the_condition` — AC-0020, the same
  check over the guide, plus the incumbent-covered exemption.
- `test_the_aesthetic_direction_gate_does_not_call_the_system_optional` —
  AC-0021, a gate-trigger reader; the module has no gate-reading pattern today,
  so this one is structurally new rather than an extension of an existing
  assertion.

**Extended** — `tests/roster/test_frontend_visual_authority_adopter_prose.py`:
`test_the_handoff_how_to_describes_the_upstream_gap` — AC-0022.

**Extended** — `tests/roster/test_experience_journey_composition.py` or a
sibling roster module, whichever already reads `docs/specs/`:
`test_both_superseded_specs_annotate_their_status` — AC-0035, AC-0036. If no
roster module reads `docs/specs/`, these two are goal-based instead, checked by
the `lint-spec-status.py` run listed under the goal-based checks below;
record which route was taken — the two routes are not equivalent evidence.

**Goal-based checks:**

- AC-0008 — `! grep -qE 'experience-design|creative-direction|design-system'
  packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md`.
  The bare `grep` form is wrong here: `grep`
  exits 1 on no match, so the passing case would read as a failure. Also
  asserted by the existing `test_the_reference_names_no_upstream_producer`.
- AC-0013 — the existing `test_the_entrypoint_body_stays_within_budget` with its
  constant moved to 968.
- AC-0027, AC-0028 — `python3 -c` comparison of the two version pairs.
- AC-0029 — for each of the two new pack headings, confirm the first `###`
  line inside that heading's block is `### Highlights`. A bare
  `grep -n '^## '` only proves the headings exist and passes with the
  `Highlights` subsection missing, which is the half AC-0029 actually requires.
- AC-0030 — `agentbundle catalogue lint --root . --deep`; `agentbundle catalogue
  verify --root .`.
- AC-0031 — `python3 tools/lint-experience-agnostic.py`.
- AC-0035, AC-0036 — `python3 '<skill-dir>/scripts/lint-spec-status.py' --root .`
  stays clean with both annotated statuses, proving the linter's leading-token
  truncation accepts them.

**Manual verification:** walk each of the spec's six acceptance scenarios
against the shipped text in one reading pass and record, per scenario, the rung
or state the rules select and the sentence that selects it.

## Design (LLD)

### Design decisions

- **The gap is a state, not a rung.** Traces to AC-0001 through AC-0005. A rung
  answers "where does this value come from"; the gap answers "may this value be
  chosen here at all". Keeping them in separate tables means the precedence
  chain stays four rungs deep and the existing demotion pins keep working.
- **The routing target comes from the artifact, not from a pack name.** Traces
  to AC-0008 and AC-0015. `design-system` already records who resolves an
  unresolved domain; adding the operation that supplies it gives the frontend a
  concrete target it can name without knowing which pack wrote the file.
- **Standalone admission and the fallback condition are two gates, not one.**
  Traces to AC-0006, AC-0011 and AC-0037. Step 1's `incumbent-system` rung is
  the repository's existing *visual* system; step 2's second source is its
  incumbent *token* system. A repository with a house style and no token file
  stands on the incumbent rung for composition and still reaches the fallback
  for values, so a single gate would mis-state that brownfield case. The
  standalone table governs `local-premise` with three admission grounds plus a
  `requires: handoff-read-completed` row — the same shape the sibling
  `## Refusals are not demotions` table already uses for `demotion-requires`.
  The fallback keeps its own three conjuncts. Round 2 found this by disagreeing
  with itself: one adjudication sustained a fourth conjunct, the other refuted
  it with the mode-halt at step 0, and the conflict was the conflation.
- **`Conditional` is a first-class vocabulary member.** Traces to AC-0017 and
  AC-0018. Marking the skill `Required` with a prose exemption would make the
  journey's own table wrong for the incumbent-covered case, which is exactly the
  drift this delivery closes elsewhere.

### Behavior & rules

The handoff rule, stated once:

> After a design handoff, implementation resolves a visual value itself only for
> an axis that every higher rung left open **and** no upstream authority still
> owes. Where upstream owes it, implementation holds that axis, stops that part
> of the work, and routes it to the owner or operation the artifact records.

Upstream owes an axis in exactly two cases:

1. `direction/<slug>.md` resolved, the `tokens/<slug>.md` slot recorded as a
   named skip by a read that completed, and no incumbent system supplies the
   axis.
2. A conforming `tokens/<slug>.md` records the axis's domain unresolved.

In case 1 an incumbent system that does supply the axis is the accepted owner
and fills it; that is the scenario in which a new design system is not
mandatory. In case 2 no lower rung fills the axis, because an explicit
unresolved record already means every rung `design-system` itself consults —
including the incumbent system — failed to reach it.

### Failure, edge cases & resilience

- **Refusal.** Unchanged and untouched: a refusal halts the mode, reaches no
  rung, and is never demoted into a gap. The gap is reached only from a read
  that completed.
- **Partial incumbent coverage.** The existing "extend its best-supported
  pattern and record the rung as partial" rule still governs the axes the
  incumbent reaches; the gap holds only the axes it does not.
- **Gap plus genuine standalone work in one repository.** The standalone
  admission set is evaluated per surface, not per repository, because the
  handoff read is already slug-scoped.

## Tasks

### T1: The frontend rules state the upstream gap

**Depends on:** none

**Tests:** the new module's `test_the_upstream_gap_table_states_its_rules`,
`test_the_gap_names_both_of_its_sources`,
`test_the_gap_holds_only_the_axes_it_names`,
`test_a_lower_rung_fills_only_a_genuinely_open_axis`,
`test_the_terminal_rung_requires_no_upstream_gap`,
`test_the_standalone_table_enumerates_its_three_conditions`,
`test_the_standalone_table_requires_a_completed_read`,
`test_the_gap_target_handling_states_its_display_rule`,
`test_a_refusal_never_becomes_a_gap`, and
`test_the_gap_record_persists_no_person_identifying_value`. Mode: TDD; the
stubs go red against the shipped reference, which carries neither table.

**Approach:** add `## Upstream gaps` and `## Standalone work` to
`references/visual-observation.md`, beside `## Refusals are not demotions`, and
amend the `local-premise` row's `Requires` cell. Covers AC-0001 – AC-0008,
AC-0032, AC-0033, AC-0034, AC-0037. AC-0008 is T1's to hold, not just T1's to
be checked on: this task is the one that writes new prose into the file that
may name no upstream producer.

### T2: The always-loaded entrypoint carries the contract

**Depends on:** T1

**Tests:** `test_the_preflight_states_the_gap_and_routes_to_the_reference`,
`test_no_shipped_file_says_the_terminal_rung_is_always_available`,
`test_the_fallback_condition_carries_three_conjuncts`,
`test_the_handoff_reference_hands_the_gap_forward`, and the existing
`test_the_entrypoint_body_stays_within_budget` at 968. Mode: TDD.

**Approach:** amend `SKILL.md` step 1 (gap paragraph, `local-premise` wording)
and step 2 (three-conjunct fallback condition); amend
`references/fallback-tokens.md`'s opening condition and
`references/design-handoff.md`'s skip semantics.

Two edits inside this task are easy to get wrong and neither is optional.
Removing `always available` from the `local-premise` bullet must leave
`subject matter`, `category alone`, `reaction against it` and `never a product`
in the *same* paragraph, because `test_visual_authority_precedence.py` stops
reading at the first blank line. And raising `BODY_BUDGET` to 968 in
`test_visual_authority_entrypoint.py` must also rewrite that assertion's
message, which currently sends a future editor to `AC-0009` in
`docs/specs/frontend-visual-authority/spec.md` — the criterion this delivery
supersedes. Covers AC-0009 – AC-0014.

### T3: The design artifact names the operation that closes a gap

**Depends on:** none

**Tests:** the three extensions to the design-system contract suite. Mode: TDD.

**Approach:** add the fourth column to the template's `## Unresolved decisions`
table; state in `design-system`'s `SKILL.md` that an unresolved record is not
silence and that a consumer resolves no value for it. Covers AC-0015, AC-0016.

### T4: The design thread states when the system is required

**Depends on:** T1, T3

**Tests:** the four extensions to
`tests/roster/test_experience_journey_composition.py`, plus the AC-0022
extension to the adopter-prose module. Mode: TDD.

**Approach:** change both optionality cells to `Conditional`, add the condition
prose to the journey and the how-to, correct the
`approve-aesthetic-direction` gate trigger, update `DESIGN.md`'s dependency
statement, and add the upstream-gap section to
`guides/frontend-engineering/how-to/read-the-design-handoff.md`. Covers AC-0017
– AC-0022.

### T5: The evals grade the routing behaviour

**Depends on:** T1, T2, T3

**Tests:** `test_the_upstream_gap_evals_exist_and_route`; the AC-0026 extension.
Mode: TDD.

**Approach:** add two frontend cases, amend `visual-authority-standalone`, and
add one design-system case. Covers AC-0023 – AC-0026.

### T6: The superseded specs point forward

**Depends on:** none

**Tests:** `test_both_superseded_specs_annotate_their_status`, or the goal-based
`lint-spec-status.py` route recorded in Construction tests. Mode: TDD where a
roster module already reads `docs/specs/`, goal-based otherwise.

**Approach:** annotate the `Status` field of
`docs/specs/frontend-visual-authority/spec.md` and
`docs/specs/frontend-experience-composition/spec.md`, each pointing at ADR-0130
and naming the part superseded. The pointer goes in `Status` and nowhere else.
Covers AC-0035, AC-0036.

### T7: Release surface and projections

**Depends on:** T1-T6

**Tests:** goal-based — the version-pair comparison, the per-heading
`### Highlights` check, the catalogue lint and verify,
`tools/validate_guides.py`, `tools/lint-experience-agnostic.py`, and `make
build-self` leaving a clean tree on re-run.

**Approach:** minor-bump both packs, write both changelog entries with
`### Highlights`, register the spec in `workspace.toml` under `["ini-003".work]`,
and regenerate projections. Covers AC-0027 – AC-0031.

## Rollout

One pull request. The change is prose and tests inside two packs plus their
guides; there is no runtime, no migration, and no persisted state. Reverting is
a revert.

## Risks

- **A pinned literal elsewhere breaks.** Several suites pin exact sentences in
  the files T1 and T2 touch. Mitigated by running the anchor-test sweep over
  every touched file before editing, and by leaving the pinned sentences
  (`PROTECTED` in `test_visual_authority_slice_two.py`) intact.
- **The 968-line budget still does not fit.** Mitigated by keeping the
  entrypoint's gap statement to the contract and its route, with every rule in
  the reference. If it does not fit, Surface rather than trim unrelated contract
  prose.
- **`Conditional` reaches a surface that expects three values.** Mitigated by
  grepping every reader of the vocabulary before the edit;
  `tests/roster/test_experience_journey_composition.py` is the only one found.

## Changelog

- 2026-09-29 — Plan approved (build strategy) by eugenelim.
- 2026-09-29 — Spec approved (scope) by eugenelim.
- 2026-09-29 — Round 5: 2 adversarial Blockers sustained. T7 now runs the
  guide validator required by the spec's Testing Strategy, and AC-0008's
  absence check names the repository-root frontend reference path.
- 2026-09-29 — Round 2: 7 findings sustained across both reviewers, 1 refuted,
  and one conflict escalated to the owner. Two adjudications disagreed on
  whether the fallback condition needed a fourth conjunct; the refutation's
  evidence — a refusal halts the mode at step 0 — exposed that the real defect
  was conflating two different gates. Step 1's incumbent rung is the
  repository's visual system; step 2's is its incumbent *token* system, and a
  house style with no token file reaches the fallback without being standalone.
  The owner chose to split them: AC-0006 keeps three admission grounds, AC-0037
  adds the `requires: handoff-read-completed` row, AC-0011 names the token
  system explicitly, and ADR-0130 gains D5 for the separate gate. D-IDs were
  renumbered, so AC-0013 now cites D7 and AC-0018 cites D6. AC-0002 gained the
  incumbent qualifier, ADR-0130 D8 gained three prohibitions AC-0032 already
  carried, and AC-0008 gained T1 as its owning task.
- 2026-09-28 — Revised from 14 sustained pre-EXECUTE findings (5 security, 9
  adversarial; 1 security finding refuted). The largest change: ADR-0130 was
  authored, because the supersession convention requires a superseded spec's
  `Status` pointer to name an ADR and none existed. The gap's two sources are
  now expressed over the handoff read's named-skip outcomes rather than over a
  file's absence, which closes a refusal→gap route the original wording left
  open; `handoff-read-completed` joins the standalone admission set for the same
  reason. AC-0032 gained an instruction-authority clause, AC-0034 bounds what
  the gap record may persist, and every task now declares `Depends on:`.
- 2026-09-28 — Plan drafted. Two contract amendments are carried in the spec
  rather than applied silently: AC-0013 raises the entrypoint body budget from
  960 to 968 (superseding `frontend-visual-authority` AC-0009), and AC-0018 adds
  `Conditional` to the say-this optionality vocabulary (superseding
  `frontend-experience-composition` AC-0020). Both are listed under the spec's
  *Ask first* rules, so spec approval is their sign-off.
