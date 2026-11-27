# Plan: Durable Outputs contract alignment

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md; packs/core/.apm/skills/work-loop/scripts/_supervisor_projector.py; packs/core/tests/skills/work-loop/test_supervisor_projector.py

## Approach

Correct the stale template classification and pin agreement with the current
amendment reference. Package the correction as a core patch release.

## Constraints

The existing supervisor protection and amendment authority govern the correction.
No new product dependency, schema, tool surface, or supervisor mechanism is needed.
The verification environment supplies pytest, ruff, mypy, bandit, and PyYAML.
The supervisor runs the declared tests and lint in its scratch tree; precheck
and render/install/diff run in the working checkout where Git is available.

## Construction tests

None beyond the task checks below.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Author guidance | T1 | Content check, eval, installed template | Source and generated copies agree |
| Release history | T1 | Core version and fragment checks | Patch fragment names the correction |

## Design (LLD)

### Behavior and rules

T1 implements AC-0001. Replace the template's tier note with:

> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` define completion. `Durable Outputs` is also protected
> after approval: changing it needs an amendment. See
> new-spec’s `references/spec-and-plan-contract.md`, “What needs an amendment
> after approval,” for the full protected-section rule. `Outcome`, `What Changes`, `Follow-ons`
> and `Assumptions` are working material: they orient a reader and an author
> corrects them in place as the work teaches, without an amendment and without a review round.
> A review finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is
> the spec's job; honouring them when a finding is adjudicated is the reviewing
> surface's.

The content check slices this note before the durable-spec-fill comment and
separates the protected and working lists. It compares Durable Outputs with
the reference's amendment section, so a phrase elsewhere cannot mask drift.
The existing renamed-section assertion stops pinning the obsolete list.

The eval asks whether an approved Durable Outputs destination can be edited
as working material; the expected answer uses the amendment path. No runtime
implementation change is needed.

## Tasks

### T1: Template and amendment contract agree

**Depends on:** none
**Touches:** packs/core/.apm/skills/new-spec/assets/spec.md, packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py, packs/core/.apm/skills/new-spec/evals/evals.json, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.d/, .agents/, .claude/, .codex/, .github/
**Verification mode:** TDD

**Tests:**

- Replace the stale list assertion with a section-bounded content check for AC-0001; show failure on the original template and success on the correction.
- Run the new-spec prose and acceptance-criteria discipline suites, durable-output suite, and supervisor projector suite.
- Validate the updated eval JSON and review its expected amendment answer.
- Run `make lint-ruff lint-mypy`, `make build-self`, and `make precheck`.
- Exercise the render/install/diff recipe in docs/VERIFICATION.md and read the installed template note.

**Done when:** The task checks pass and AC-0001 is met in the installed template.

## Risks

Duplicating the full protected-section list would create another drift surface;
the template links to its owner instead. Broad regeneration may expose unrelated
drift, which must be identified before including generated changes.

## Review shape

One bounded correction. Generated adapter copies derive from the pack source;
tests and the eval cover the source rule. No independent feature is bundled.

## Changelog

- 2026-11-27: spec approved by owner (scope)
