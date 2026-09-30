# Plan: visual-target confirmation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` § Version bump rule and § Self-hosting
  projection; `packs/AGENTS.local.md` § Marketplace and release pipeline;
  `docs/product/changelog.md` header (an entry is owed in the change that bumps
  a version); `packs/frontend-engineering/tests/skills/frontend-engineering/frontend_engineering_visual_authority_rules.py`
  (the `observation_table` and `rule` helpers, whose `OBSERVATION` constant opens
  `references/visual-observation.md` and nothing else);
  `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_precedence.py`
  (the analogous shipped rung test and its exact-equality shape);
  `tools/lint-pack-test-boundary.py` § `pack-tests-stay-in-pack` (why cross-tree
  and guide-tree criteria live in `tests/roster/`);
  `packs/frontend-engineering/.apm/skills/frontend-engineering/references/design-handoff.md`
  (the read takes the frontmatter as found and requires only `type:`, which is
  what makes an added key compatible with artifacts that predate it).

## Approach

The state is one frontmatter key on an artifact that already exists, so the work
is a coordinated extension across the surfaces that already name the rung, not a
new mechanism. The producing side is gated in the same change as the consuming
side: gating only the top rung would leave an unconfirmed target's compositional
commitments in the artifact, where the rung below binds them.

## Constraints

- No new dependency, module boundary, or top-level directory.
- No sidecar file beside the direction artifact.
- `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` has a
  964-line body against `BODY_BUDGET = 968` in `test_visual_authority_entrypoint.py`,
  a ceiling owned by AC-0013 of the Shipped `design-to-build-value-handoff` spec.
  Raising it is an Ask-first bar in that spec. AC-0012 and AC-0013 therefore land
  as in-place edits to the existing rung bullet and evidence-manifest cell, not
  as added lines.
- A pack suite may not read another pack's tree, so the design-system criterion
  is asserted from the experience-design suite and the cross-pack drift
  criterion from `tests/roster/`.
- The `status` field's vocabulary is untouched.
- `design-handoff.md` must keep saying that only `type:` is required and that the
  read takes the frontmatter as found. `tests/roster/test_design_handoff_contract_matches_corpus.py`
  parses that contract and classifies every file under `docs/design/`, so a
  contract claiming direction artifacts carry `visual_target` would be false
  against the real artifacts there and would red.
- `test_visual_authority_slice_two.py` belongs to the `frontend-visual-authority`
  spec's own second slice. This plan's tests must not reuse that filename, and
  its `PROTECTED` tuple byte-pins two sentences, one of them inside the rung
  bullet AC-0012 edits: "It supplies no colour, type, spacing or motion values,
  so those always come from a lower rung." That edit must preserve it.
- `test_visual_authority_precedence.py` reds when `references/visual-observation.md`
  contains the literals `experience-design`, `creative-direction`, or
  `design-system` anywhere. The new `## Visual-target confirmation` table is
  therefore authored in adopter-address terms and never names the producing
  skill or pack.
- `test_visual_authority_release.py` hard-pins `pack.toml`'s version to the value
  its release ships at, and its own message states that a later delivery moves
  the pin with its own bump. This delivery is that later one, so T10 moves the
  pin rather than working around it.

## Construction tests

Every criterion's check is an assertion over a shipped file's bytes, except the
six eval criteria, whose check is the evals validator over a recorded case, and
the three release criteria, whose check is `tests/conformance/test_pack_metadata.py`
plus a version comparison against `origin/main`. The comparison is what makes a
missing bump observable: the conformance test asserts only that `pack.toml` and
`plugin.json` agree, which holds on an unchanged tree.

## Durable-output map

| Durable output | Task | Evidence |
| --- | --- | --- |
| Decision rationale (ADR-0131) | T2 | The ADR file, Accepted, cited by the spec header |
| Interface compatibility (the template) | T3 | Contract test over the template's frontmatter, body and comments |
| Interface compatibility (the frozen spec) | T11 | The annotation asserted by AC-0027 |
| Current product truth (the guide) | T7 | Roster test over the guide file |
| Release history (versions and changelog) | T10 | `tests/conformance/test_pack_metadata.py`, the version comparison, and the changelog entries |

## Design (LLD)

### Design decisions

Owned by: T3, T5

`visual_target` is frontmatter rather than a body line because frontmatter is
where the artifact already carries machine-read lifecycle state, and because a
body line would put the same state beside the prose that describes the target,
where a reader could not tell which one a consumer obeys. The body's
`**Confirmation record:**` line and the existing `**Target:**` and `**Binding:**`
lines are provenance for a human reader; the section comment says so and names
the frontmatter key as canonical, which is what keeps the body's existing
`"none"` wording from becoming a second home for the state.

An absent field reads as `unconfirmed` rather than `none` because the two
readings differ only where a reader wants to know whether a target exists, and
because `unconfirmed` is the fail-closed answer for the only question the rung
asks. This makes older artifacts correct without migration.

Three obligations are living design rather than criteria, because the only check
available for each is that a sentence exists, which the repository's spec
template rules out as a criterion: that the frontmatter comment distinguishes
what `status` records from what `visual_target` records; that `converge` states
a delegated or still-proposed choice supplies no target confirmation; and that
the experience-design guide states confirming a direction does not confirm its
target. Each is protected by a content pin in its task rather than a checkbox
here.

### Data & schema

Owned by: T3

The closed set is `none | unconfirmed | confirmed`, written as a quoted
placeholder in the template exactly as `status` is.

### Interfaces & contracts

Owned by: T5, T11

The changed contract surfaces are the two rung tables (`visual-observation.md` §
Authority precedence, `design-system` § Design authority), the new
`visual-observation.md` § Visual-target confirmation rule table, and the frozen
`frontend-visual-authority` spec whose top-rung `requires` criterion this partly supersedes. Only the
first and third parse through the shipped `observation_table` and `rule`
helpers; the design-system table is read by that pack's own suite.

### Behavior & rules

Owned by: T3, T4, T5, T6, T8, T9

The six acceptance scenarios in the accepted request map to criteria as follows.

| Scenario | Criteria |
| --- | --- |
| Selected, target present, confirmation absent | AC-0004, AC-0019, AC-0025, AC-0029 |
| Target explicitly confirmed | AC-0006, AC-0024, AC-0028 |
| No target | AC-0009, AC-0018 |
| Choice delegated or still proposed | AC-0025 |
| Older artifact without the field | AC-0008, AC-0020 |
| `inherit` route | AC-0014, AC-0021 |

AC-0008 carries the absent-field row alone: its text is confined to an artifact
without the field, so citing it for a present-but-unconfirmed field would be a
trace to a criterion that cannot red there. AC-0029 is scoped to a selected
direction, so the delegated row rests on AC-0025, which gates commitments on the
confirmed reading and therefore reaches a `proposed` artifact too.

### Failure, edge cases & resilience

Owned by: T3, T5

The edge that matters is a partially updated tree: `visual-observation.md` naming
`visual_target: confirmed` while the template still lacks the field. T3 lands
before T5 for that reason. No test reads across the two packs except the T6
roster assertion, which is why that assertion exists.

### Quality attributes (NFRs)

Owned by: T3

No runtime performance surface. The privacy bar is that no acceptance criterion
or shipped instruction asks for a person-identifying value: the confirmation
record carries a date and a surface name.

### Dependencies & integration

Owned by: T5

Depends on the Shipped `design-to-build-value-handoff` slice for the upstream-gap
vocabulary the rung table already uses, and inherits its `SKILL.md` body-line
ceiling. Adds no new dependency.

## Tasks

### T1: The external readers of a direction artifact are covered

**Depends on:** none

**Tests:**
- `no stub (goal-based check)`. Four roster tests and two
  `web/src/content/journeys/` pages reach a direction artifact or its contract.
  Required outcome: each is either asserted unaffected by a green run, or listed
  as a T7 surface.

**Done when:** the verification ledger records the reader set, the green roster
run, and whether either journey page became a T7 surface.

### T2: ADR-0131 records the decision

**Depends on:** none

**Tests:**
- `no stub (goal-based check)`. `python3 .claude/skills/new-adr/scripts/index-records.py docs/adr`
  regenerates the index with the new record present.

**Done when:** `docs/adr/0131-visual-target-confirmation-is-an-explicit-state.md`
exists, is Accepted, and the ADR index lists it. *(Met during PLAN.)*

### T3: The direction template carries the field, its gate, and its provenance

**Depends on:** T1, T2

**Tests:**
- Contract test: the template's frontmatter carries a `visual_target` key whose
  placeholder enumerates exactly the three values. Verifies AC-0001.
- Contract test: the template's `## Approved visual target` section carries a
  `**Confirmation record:**` line. Verifies AC-0002.
- Contract test: the compositional-commitments comment contains the literal
  `visual_target: confirmed`. Verifies AC-0024.
- Contract test: the `## Approved visual target` comment names the frontmatter
  key as canonical and the body lines as provenance. Verifies AC-0026.
- Content pin: the frontmatter comment names both `status` and `visual_target`
  and says what each records. Protects the living-design obligation; not a
  criterion.
- `stub: true` — one compilable red assertion over the template's frontmatter
  before the template changes.

**Touches:** packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** the creative-direction contract suite is green and the four
assertions above fail against the pre-change template.

### T4: `converge` writes the disposition and gates the commitments on it

**Depends on:** T3

**Tests:**
- Contract test: `converge.md` contains `visual_target: confirmed` in the
  disposition instruction and `visual_target: unconfirmed` in the
  present-without-confirmation instruction. Verifies AC-0004.
- Contract test: the compositional-commitments instruction is gated on the
  `confirmed` reading. Verifies AC-0025.
- Contract test: `visualize.md`'s instruction to record a target's binding
  boundaries is scoped to the confirmed reading, so an unconfirmed target records
  identity and disposition without a `**Binding:**` claim. Verifies AC-0034.
- Content pin: `converge.md` states that a delegated or still-proposed choice
  supplies no target confirmation. Protects the living-design obligation; not a
  criterion.

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/converge.md, packs/experience-design/.apm/skills/creative-direction/references/visualize.md, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** the creative-direction contract suite is green.

### T5: The frontend surfaces require the confirmed state

**Depends on:** T3

**Tests:**
- Update the shipped exact-equality assertion at
  `test_visual_authority_precedence.py::test_the_top_rung_requires_a_recorded_confirmation`
  to the new cell value. Verifies AC-0006.
- Contract test: the new `## Visual-target confirmation` rule table carries its
  five row keys in order. Verifies AC-0007.
- Contract test: the `absent-field` row reads `unconfirmed`. Verifies AC-0008.
- Contract test: the `states` row enumerates the three values. Verifies AC-0009.
- Contract test: the `never-binds` row names all six value axes. Verifies AC-0010.
- Assertion over the frontend `SKILL.md` text, not the rung-table helpers, which
  never open that file: the rung bullet names the field. Verifies AC-0012.
- Assertion over the same file: the evidence-manifest cell records the artifact's
  reading. Verifies AC-0013.
- Per-surface assertion over the frontend members of the confirmation-reading
  set: the rung-1 bullet and the evidence-manifest row in `SKILL.md`,
  `visual-observation.md`'s `## Why the top rung needs a recorded confirmation`
  section, and `.apm/agents/frontend-reviewer.md`. Verifies AC-0031 for those
  members and AC-0032 for the rung-2 bullet.
- Retired-reading sweep over the same members, whitespace-normalized, for the
  set recorded by this task's sweep step. Verifies AC-0033 for them.

**Approach:**
- The precedence assertion is an exact string equality, so it reds on the
  pre-change cell. Update it in the same commit as the table.
- AC-0012 and AC-0013 are in-place edits within the 964/968 body-line ceiling.
  Measure the body with `skill_body_lines()` before and after.
- AC-0012's edit replaces the rung bullet's prose precondition rather than
  adding beside it, which is what AC-0031 then proves. The bullet's protected
  sentence about supplying no values stays byte-identical.
- Derive the retired-reading set before editing, not from memory: sweep both
  trees for statements of the rung condition in terms of what the artifact
  records, and record the resulting set and the command in the verification
  ledger. Three rounds of review each found a paraphrase the previous round's
  phrase list missed, which is why the set is a recorded output rather than a
  contract literal.

**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md, packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md, packs/frontend-engineering/.apm/agents/frontend-reviewer.md, packs/frontend-engineering/tests/skills/frontend-engineering/

**Done when:** the frontend pack's visual-authority suite is green, including
`test_visual_authority_entrypoint.py`'s body-budget assertion.

### T6: The field name cannot drift between the two packs

**Depends on:** T3, T5

**Tests:**
- Roster assertion: the `visual_target` values declared in the template and the
  values named in `visual-observation.md` and `design-system`'s `SKILL.md` agree;
  it reds when any one is renamed. Verifies AC-0017.
- Contract test in the experience-design suite: the design-system authority
  table's source cell names the field. Verifies AC-0011.
- `stub: true` — the roster assertion compiles and reds against a deliberately
  mismatched value.

**Approach:**
- `tests/roster/` is the only place allowed to read both pack trees, which is
  what makes this criterion placeable at all.

**Touches:** packs/experience-design/.apm/skills/design-system/SKILL.md, packs/experience-design/tests/skills/design-system/test_design_system_contract.py, tests/roster/

**Done when:** the roster suite and the experience-design suite are green, and
`python3 tools/lint-pack-test-boundary.py` reports no violation.

### T7: The handoff guide describes the field

**Depends on:** T5

**Tests:**
- Roster test: `read-the-design-handoff.md` states the field, its three values,
  and the absent-field reading. Verifies AC-0015.
- Per-surface assertion over the guide members of the confirmation-reading set:
  the rung-1 clause states the precondition as the field (AC-0031), the rung-2
  clause states its condition as a non-`confirmed` reading (AC-0032), and
  neither carries a retired reading (AC-0033). The guide currently routes rung 1
  with "the artifact says somewhere that the composition was approved or signed
  off" and rung 2 with "nothing in it records a human confirming the
  composition"; both are replaced, not supplemented.
- Content pin: `establish-design-intent.md` states that confirming a direction
  does not confirm its visual target. Protects the living-design obligation; not
  a criterion.

**Touches:** guides/frontend-engineering/how-to/read-the-design-handoff.md, guides/experience-design/how-to/establish-design-intent.md, tests/roster/

**Done when:** the roster suite is green.

### T8: `inherit` runs no fresh interrogation

**Depends on:** none

**Tests:**
- Contract test: the sentence in `creative-direction/SKILL.md` containing
  `Run the interrogation` also contains `inherit` and excludes that route. The
  assertion reads the sentence, so moving the qualifier to a neighbouring
  sentence reds. Verifies AC-0014.

**Touches:** packs/experience-design/.apm/skills/creative-direction/SKILL.md, packs/experience-design/tests/skills/creative-direction/test_contract.py

**Done when:** the creative-direction contract suite is green and the route table
and the `frame` operation no longer state opposite things about interrogation on
`inherit`.

### T9: The evals cover the model-behaviour decisions

**Depends on:** T4, T5, T8

**Tests:**
- `no stub (visual / manual QA)`. Five added cases and one restated: `none`
  recorded (AC-0018); an explicit `unconfirmed` reading resolving to
  `direction-and-taxonomy` (AC-0019); no key at all resolving the same way
  (AC-0020); `inherit` running no interrogation (AC-0021); the shipped
  `visual-authority-approved-target` case restated against the field (AC-0028);
  and `converge` recording `unconfirmed` for a selected direction with a named,
  unapproved target (AC-0029). The `visual-authority-direction-only` case is
  restated against the field rather than added (AC-0019), and both shipped cases
  clear the retired-reading sweep (AC-0031, AC-0033). Observable result: the evals validator accepts
  each case and the recorded expected output names the rung or state.

**Approach:**
- AC-0028 edits a shipped case rather than adding one. Left as shipped, it would
  grade the opposite of the new behaviour, because its prose precondition reads
  `unconfirmed` under the absent-field rule.
- That case's `expected_output` is pinned by `test_visual_authority_slice_two.py`
  to hold the literal `resolved`, and the same test pins the
  `visual-authority-direction-only` case id. Both restatements keep those pins.
- Both shipped cases are members of the confirmation-reading set, so AC-0031 and
  AC-0033 reach `evals.json`. T9 is the last writer of that file, so the sweep
  for those members runs here rather than in T5.

**Touches:** packs/experience-design/.apm/skills/creative-direction/evals/evals.json, packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json

**Done when:** the evals validator passes for both packs and all six cases are
present in their recorded form.

### T10: The release surface is consistent

**Depends on:** T3, T4, T5, T6, T7, T8, T9

**Tests:**
- `no stub (goal-based check)`. `tests/conformance/test_pack_metadata.py` passes,
  and each pack's version in `pack.toml`, `plugin.json` and `marketplace.json` is
  the same and strictly greater than the version on `origin/main`. Verifies
  AC-0022, AC-0023.
- `no stub (goal-based check)`. `docs/product/changelog.md` carries a
  free-standing `##` release entry per pack version, with a `### Highlights`
  subsection under any entry that owes one. Verifies AC-0030.

**Approach:**
- `marketplace.json` is generated: run `FORCE=1 make build-self` after the bump
  rather than editing it. Nothing tests version parity there for these two packs,
  so an unregenerated file ships green.
- `test_visual_authority_release.py` pins `frontend-engineering`'s `pack.toml`
  version by equality. Move the pin to this delivery's version in the same
  commit as the bump; the criterion owns the direction, the pin owns the value.
  `experience-design` has no equivalent pin.
- Where no highlight is owed, the verdict's reason goes in the pull request's
  *What did you not change that you considered?* answer, which is where
  `packs/AGENTS.local.md` § Marketplace and release pipeline puts it. No
  changelog byte records it, so no check here looks for one.
- Last, because a bump recorded before the content it describes lands is a
  version claiming content the tree does not have.

**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_release.py, .claude-plugin/marketplace.json, docs/product/changelog.md

**Done when:** `make lint-ruff lint-mypy`, `tests/conformance/test_pack_metadata.py`
and both packs' suites are green, and the version comparison against `origin/main`
holds for both packs.

### T11: The superseded criterion is annotated

**Depends on:** T5

**Tests:**
- Assertion over `docs/specs/frontend-visual-authority/spec.md`'s `Status` field:
  it carries a supersession annotation naming ADR-0131 and the superseded
  `requires` value `recorded-human-confirmation`. Verifies AC-0027.

**Approach:**
- Follows the shape `design-to-build-value-handoff` used for the same obligation,
  where the annotation was itself a criterion rather than a convention.

**Touches:** docs/specs/frontend-visual-authority/spec.md, tests/roster/

**Done when:** the annotation is present and `python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root .`
reports no violation.

## Rollout

- **Delivery:** big bang within one PR. Reversible by reverting the PR; no
  migration, because the absent-field rule makes an un-migrated artifact correct.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T3 before T5, so the consuming table never names a
  field the template does not carry. T10 last.

## Risks

- A direction artifact written before this slice reads as `unconfirmed` and
  loses any top-rung binding it previously had by inference. That is the intended
  correction, and the guide states it, but it is a behaviour change for an
  existing artifact. This repository's own corpus shows the scale: of the four
  files under `docs/design/direction/`, the handoff read admits three as
  direction artifacts — `token-verification.md` carries `type: design-system`
  and is skipped — and all three read `unconfirmed` after this change. None of
  the four carries the template's `proposed` or `selected` vocabulary today.
- The six eval criteria are the only ones whose check is a recorded model gesture
  rather than a byte assertion, so they carry the weakest verification in the set.
- `marketplace.json` version drift is caught here only by AC-0022 and AC-0023.
  No shipped test asserts parity for these two packs, so the criteria are the
  control.
- `tests/roster/` runs only through a dispatch-only workflow, so AC-0015,
  AC-0017, AC-0027 and the guide members of AC-0031 to AC-0033 — including the
  sole cross-pack drift control — are not
  reached by any pull-request gate. This is the repository's existing gate
  topology rather than something this slice introduces, so T6 and T7 record a
  local roster run as their evidence instead of relying on CI.

## Changelog

- 2026-09-29: Drafted.
- 2026-09-29: Revised from pre-EXECUTE review round 3. The round-2 repair was
  itself the defect: a closed retired-phrase set cannot enumerate an English
  reading, and three rounds each found a paraphrase the last one missed. The
  criteria now work over a closed set of surfaces, with the retired-reading set
  derived from a recorded sweep rather than guessed. Also recorded the
  contract-tier Always-do rule in the frozen spec that keying the rung on an
  upstream-produced value reverses, which AC-0027 now annotates and ADR-0131
  now justifies.
- 2026-09-29: Revised from pre-EXECUTE review round 2 — eight sustained findings
  and the verified shaping set. Added two retired-phrase sweeps, because every
  other criterion is a presence check and a tree carrying both the new rule and
  the superseded prose reading satisfied all of them. Corrected the scenario map,
  scoped AC-0030 to what the changelog owns, made AC-0017's comparison explicit,
  and recorded three shipped pins the tasks must respect.
- 2026-09-29: Revised from pre-EXECUTE review round 1 — ten sustained findings
  and four verified shaping findings. Cut three criteria with no available
  oracle, reworded five, and added seven covering the producing-side gate, the
  supersession annotation, the shipped eval case, cross-pack drift, and the
  release surface.
