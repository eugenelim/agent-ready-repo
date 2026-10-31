# Spec: architect-assess orientation sections and per-section provenance

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs/specs/architect-assessment/spec.md`](../architect-assessment/spec.md) — its saved-report section order (Bottom line through Next decision) stays unchanged. This spec adds subsections inside `Conceptual current state` and one charter field, and amends one rule: the Map and Focus checkpoints pause for the user only on a host that can pause; on a host that cannot, the run proceeds and records `Checkpoints: accepted-without-pause`.
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the saved `assessment.md` template gains optional subsections and one charter field; no API, event, or RPC contract changes.
- **Shape:** mixed — a template extension, skill guidance, one reference, evals, and guide pages.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`, `What
> Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working material.

## Outcome

A reader of a saved architecture assessment is oriented first on the whole system, then on each subsystem, then on the physical deployment, and sees which sources were checked for each part. A run that could not pause for the Map and Focus checkpoints says so in the charter, so the reader knows the model was not user-confirmed.

## What Changes

- Three subsections inside `Conceptual current state` — Overall architecture, Architecture by subsystem, Physical architecture — each ending in a `Sources checked` table — `packs/architect/.apm/skills/architect-assess/assets/assessment.md`.
- A `Checkpoints:` charter field and a recorded cannot-pause behavior — the same template and `SKILL.md`.
- Map-step guidance for the orientation views, the `Sources checked` table, and the field — `SKILL.md`.
- A reference that routes diagram authoring to `architect-diagram` and the physical view to `architect-design`'s `references/physical-bom.md`, and says a physical view with no deployment evidence is `not assessed` — `references/orientation-views.md`.
- Two eval cases and the guide pages — `evals/evals.json`, `guides/architect/reference/architecture-assessment.md`, `guides/architect/how-to/assess-a-repository.md`.
- An amendment note at the checkpoint rule in the shipped parent — `docs/specs/architect-assessment/spec.md`.
- The release surface — `packs/architect/pack.toml`, `packs/architect/.claude-plugin/plugin.json`, a changelog fragment.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | The saved report format gains subsections and a field | `assets/assessment.md` | eugenelim | template contract test | the shipped order test still passes |
| User-facing promise | Users need the new sections and field described | `guides/architect/reference/architecture-assessment.md`, `guides/architect/how-to/assess-a-repository.md` | eugenelim | page diff | pages name the sections, table, and field |
| Maintainer procedure | The pack's design record lists one helper and its references | `packs/architect/DESIGN.md` | eugenelim | diff or a recorded no-change reason | the record matches the shipped files |
| Decision rationale | The checkpoint rule changes for hosts that cannot pause | `docs/specs/architect-assessment/spec.md` | eugenelim | amendment note linking here | parent and child state the same rule |
| Release history | A pack change ships by version bump | `pack.toml`, `plugin.json`, `tools/changelog.py new` fragment | eugenelim | version parity test, fragment validates | bump above fetched main, `Highlights` decided |

## Agent Rules

### Always do

- Keep the shipped saved-report section order intact.
- Cite `references/evidence-method.md` for the evidence-class words rather than defining them again.
- Run `FORCE=1 make build-self` after the version bump.

### Ask first

- Placing any new section outside `Conceptual current state`.
- Adding a required (rather than optional) section.

### Never do

- Edit `architect-diagram` or `architect-design` to make this work.
- Add a script, a dependency, or a new top-level directory.

## Testing Strategy

- Template shape (subsections, tables, field, preserved order): goal-based check through the pack's contract tests, because the template is static text with exact headings.
- Run behavior (the field appears when a run cannot pause; a physical view without deployment evidence is `not assessed`): eval cases graded on the produced report, because only a model run produces the behavior.
- Guides, release parity: goal-based check by grep and the version-parity test.

## Acceptance Criteria

- [x] `assets/assessment.md` contains, between `## Conceptual current state` and `### Map checkpoint`, the headings `### Overall architecture`, `### Architecture by subsystem`, and `### Physical architecture` in that order.
- [x] The existing template order test in `test_skill_contract.py` still passes unchanged.
- [x] Each of the three subsections in the template ends with a `Sources checked` table whose header is `Source | Locator | Evidence class | Limit`.
- [x] The template's `Evidence class` comment lists `observed`, `inferred`, `reported`, and `unknown`, and cites `references/evidence-method.md` § Claim calibration as their definition.
- [x] No `.md` file under `packs/architect/.apm/skills/architect-assess/` other than `references/evidence-method.md` has a line matching `^\s*(?:[-*]\s+|\d+\.\s+)?\*\*(Observed|Inferred|Reported|Unknown)\*\*`.
- [x] The template comment states that an unassessed subsection begins with the line `not assessed` followed by a reason, and still ends with its `Sources checked` table.
- [x] The template's `Assessment charter` block contains a `Checkpoints:` line with the values `confirmed | accepted-without-pause`.
- [x] `SKILL.md` defines a host that cannot pause as one with no interactive channel to the user (a headless or scheduled run), and states that an interactive session never skips the pause.
- [x] `SKILL.md` states, at each of its Map and Focus checkpoint rules, that on a host that cannot pause the run proceeds and records `Checkpoints: accepted-without-pause`.
- [x] `SKILL.md` states that in that case the `### Map checkpoint` and `### Focus checkpoint` subsections each hold the line `not user-confirmed`.
- [x] `docs/specs/architect-assessment/spec.md` carries, at its Map and Focus checkpoint rules, a note that links to this spec and states the cannot-pause exception.
- [x] `evals/evals.json` contains a case whose prompt says the session cannot pause, with assertions that the report records `Checkpoints: accepted-without-pause` and that both checkpoint subsections hold `not user-confirmed`.
- [x] `evals/evals.json` contains a case whose repository has no deployment evidence, with assertions that the Physical architecture subsection begins `not assessed`, names no invented component, and ends with a `Sources checked` table.
- [x] `guides/architect/reference/architecture-assessment.md` names the three subsections, the `Sources checked` table, and the `Checkpoints:` field.
- [x] `pack.toml` and `.claude-plugin/plugin.json` carry the same version, one patch above the version on fetched main.
- [x] `tools/changelog.py validate` passes with the new fragment present.

## Terminal Intent

`code` — change the template, skill guidance, reference, evals, guides, parent-spec note, and release surface.

## Follow-ons

- eugenelim: HTML report renderer — a stdlib script that renders a saved `assessment.md`, with these sections, into one offline HTML file; drafted separately and not part of this change.

## Assumptions

none

## Changelog

<!-- Approvals only. -->

- 2026-10-30: spec approved by eugenelim
