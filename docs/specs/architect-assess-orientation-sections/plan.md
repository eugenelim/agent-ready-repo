# Plan: architect-assess orientation sections and per-section provenance

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing
- **Repository anchors:** template and its order test in `packs/architect/tests/skills/architect-assess/test_skill_contract.py`; Map step in `packs/architect/.apm/skills/architect-assess/SKILL.md`; physical view rules in `packs/architect/.apm/skills/architect-design/references/physical-bom.md`; release steps in `packs/AGENTS.md` and `packs/AGENTS.local.md`.

> **Plan contract:** `Touches`, `Tests` and `Done when` are what a completion gate
> reads; the rest is working material.

## Approach

Insert three H3 subsections and a `Sources checked` table into the template under the existing `Conceptual current state`, add the charter field, and teach the Map step to fill them. Orientation content is delegated: the new reference tells the assessor to write a diagram brief per view and hand it to `architect-diagram`, and to hand the physical view to the `physical-bom.md` rules. The two evals prove the behaviors a static test cannot. The release surface follows `packs/AGENTS.md`.

## Constraints

- The shipped section order and its AC stay intact.
- Docs guidance: Mermaid in repository docs carries no raw HTML and no `;` in labels.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** run the two new evals once and record the result.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Template | T1 | contract test | order test green |
| Guides, DESIGN.md | T3 | page diff | grep of section names |
| Release surface | T4 | parity test, fragment | `validate` green |

## Design (LLD)

### Design decisions

- Subsections live under `Conceptual current state` so the shipped order stays true and the overlap with that section is explicit: they refine it. Traces to: ACs 1-2.
- The evidence-class words are owned by `references/evidence-method.md` § Claim calibration; the template comment cites it and nothing re-defines them. Traces to: evidence-class ACs.
- Delegation is working material with a content pin in T2: the reference names `architect-diagram` and `physical-bom.md`. Owned by: T2.

## Tasks

### T1 — Template and Map step

Depends on: none
Verification mode: TDD
Touches: `assets/assessment.md`, `SKILL.md`, `tests/skills/architect-assess/test_skill_contract.py`
Tests: extend the contract test with the heading order relative to `### Map checkpoint`, the table header, the evidence-class comment and its citation, the line-pattern search from the evidence-class criterion over the named files, the shipped test `test_progressive_stages_modes_and_correction_points_are_explicit` passing unchanged (reworded checkpoint text must not repeat the phrase `say **continue**`), the not-assessed form comment, the `Checkpoints:` line, and the `SKILL.md` cannot-pause statements; keep the existing order test as is.
Done when: the architect pack's contract tests pass.

### T2 — Orientation reference and evals

Depends on: T1
Verification mode: goal-based
Touches: `references/orientation-views.md`, `evals/evals.json`, `test_skill_contract.py`, `docs/specs/architect-assess-orientation-sections/notes/eval-results.md`
Tests: a content pin that the reference names `architect-diagram` and `physical-bom.md`; the two eval cases exist with the stated assertions.
Done when: the contract tests pass and the eval results are recorded in `notes/eval-results.md`.

### T3 — Guides and design record

Depends on: T1
Verification mode: goal-based
Touches: `docs/specs/architect-assessment/spec.md` (amendment note), `guides/architect/reference/architecture-assessment.md`, `guides/architect/how-to/assess-a-repository.md`, `packs/architect/DESIGN.md`
Tests: grep for the three section names, the table, and the field in the reference guide.
Done when: the grep passes.

### T4 — Release surface

Depends on: T2, T3
Verification mode: goal-based
Touches: `packs/architect/pack.toml`, `packs/architect/.claude-plugin/plugin.json`, a `tools/changelog.py new` fragment
Tests: version parity between the two files and one patch above fetched main; `tools/changelog.py validate`.
Done when: `FORCE=1 make build-self` leaves no diff beyond the expected projection and `make lint-ruff lint-mypy` passes.

## Risks

- An eval is model-graded and may flake; record the run and rerun once before treating it as a regression.

## Changelog

- 2026-10-30: plan approved by eugenelim
