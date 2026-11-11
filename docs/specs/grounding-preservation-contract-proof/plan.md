# Plan: Preservation records through the acceptance evaluator

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** none — non-structural. The suite follows the loader
  and fixture pattern of `packs/core/tests/skills/work-loop/test_acceptance.py`
  and `test_evidence_store.py`.

## Approach

One new test module builds the six samples once as data, then drives them
through the shipped validators, the evidence store, and the evaluator. Valid,
rejection, mutation, and limit cases are parametrized over the same sample
table, so a seventh property is one new row.

## Constraints

- Slice 1 contracts and entry points at revision
  `42d02f315f22c4f25653644212c7615ada79f1d7`
  ([`acceptance-authority-and-evidence`](../acceptance-authority-and-evidence/spec.md)).
- `packs/AGENTS.md` § Writing pack tests: load each script by path under a
  pack-and-skill-qualified module name.
- `packs/AGENTS.md` § Version bump rule, as `tests/roster/test_two_sided_prune_closure_invariant.py`
  enforces it: any change under `packs/core/`, tests included, bumps the Core
  patch version.
- `tools/lint-pack-test-boundary.py`: a pack test reads nothing above its pack.

## Construction tests

**Integration tests:** the store verdict path (`append_receipt` then
`evaluate_verdicts`) is the integration surface for AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current product truth — spec `Contract-fit result` and brief Spec map | T1, T2 | Green targeted suite | Section states verdict and revision; Spec map row derives `Shipped` |
| Release history — Core `3.1.30` | T2 | Manifests, changelog fragment, roster version-bump test | No `.apm/` or `seeds/` path changed |

## Design (LLD)

### Data & schema

Each sample row names a property identifier, its observation type, its
required terms, and the passing outcome. The lifecycle row has four terms
(create, update, delete, rebuild) so a missing term is observable; every other
row has one. Every property's contradiction rule is
`supported-review-failure`. Schema conformance goes through the shipped in-code
validators; the roster parity suites own their agreement with the schema files.

Traces to: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009 · `contracts/delivery/acceptance-property.v1.schema.json`, `contracts/delivery/evidence-receipt.v1.schema.json`.

Owned by: T1.

## Tasks

### T1: The preservation suite passes for valid, rejected, mutated, and limit cases

**Depends on:** none

**Touches:** `packs/core/tests/skills/work-loop/test_preservation_contract_proof.py`

**Tests:** (goal-based)
- AC-0001, AC-0007: parametrized over the six sample rows; store opened in
  `tmp_path` with a root grant from `_security_capability.CapabilityIssuer`.
- AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0008: one test each, using the sample rows; AC-0004
  parametrized over the six rows.
- AC-0009: direct `evaluate_verdict` calls, because the limits are evaluator
  behavior the store routing hides.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_preservation_contract_proof.py -q`
passes, and `make lint-ruff lint-mypy` passes.

### T2: The contract-fit result and scope are recorded

**Depends on:** T1

**Touches:** `docs/specs/grounding-preservation-contract-proof/spec.md`, `docs/product/briefs/repository-grounding-preservation.md`, `workspace.toml`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/*`, `docs/specs/workspace-retirement/inventory.toml`

**Tests:** (goal-based)
- AC-0010: `grep -n "Existing contract sufficient" spec.md` and the full
  revision in the same section.
- AC-0011: the scope check the criterion names.

**Done when:** both checks hold, `lint-spec-status.py`, `lint-brief-coverage.py`,
and `workspace-status` report clean for this spec and brief.

## Changelog

- 2026-10-28: spec and plan approved by the owner (Platform Core) after clean shaping and adversarial reviews.
- 2026-10-28: done; T1 and T2 complete.
- 2026-10-28: amendment approved by the owner after CI. AC-0001 relies on the
  shipped validators and the roster parity suites instead of reading schema
  files; the Core patch bump to `3.1.30`, its changelog fragment, and a
  workspace-retirement inventory row join AC-0011's allowed paths.
