# Plan: Capture-work alias removal

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** [RFC-0083 section 10 and 2026-10-02 Errata](../../rfc/0083-work-intake-and-artifact-routing.md); historical [`work-intake-migration-docs` AC14](../work-intake-migration-docs/spec.md); `packs/core/.apm/skills/capture-work/`; `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` (`parse_legacy_workspace_entry`, `_extract_canonical_memberships`, `run_canonical_reconciliation`, and migration-planning seams); focused migration and projection tests under `packs/core/tests/skills/workspace-status/` and `tests/roster/test_workspace_status_projection.py`. Named deviation: accepted-legacy parsing currently serves both ordinary reconciliation and explicit migration, so the implementation must separate those consumers before removing compatibility behavior.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/capture-work-alias-removal/notes/verification-ledger.md`. A genuine
> artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval.

## Approach

Separate ordinary reconciliation from the accepted-legacy parser used by explicit migration, then remove the `capture-work` skill and every published alias registration. Refresh current documentation and Core 3.0.0 release metadata, regenerate all projections from `.apm` sources, and collect the unchanged RFC-0083 evidence against the exact candidate. The release stays inert until the RFC-0083 Approver records fresh authorization over that candidate and its dual-reader rollback target.

## Constraints

- [RFC-0083](../../rfc/0083-work-intake-and-artifact-routing.md) section 10 owns the accepted legacy shapes, migration model, and rollback boundary; its 2026-10-02 Errata removes only the 90-day and separate advance-notice requirements and names Core 3.0.0.
- Historical [AC14](../work-intake-migration-docs/spec.md) remains the evidence definition for the unchanged fixture, writer, guide, rollback, separate-specification, and fresh-authorization predicates. The shipped spec is not edited.
- `packs/AGENTS.md` and `packs/AGENTS.local.md` govern pack source ownership, version and eval coupling, shipped-content boundaries, self-host projection, and release-record obligations.
- `packages/AGENTS.md`, `packages/AGENTS.local.md`, and the AgentBundle scoped guidance govern packaged-runtime ownership, package version coupling, package tests, and publishing.
- No repo-root `contracts/` artifact applies: this removes a skill name and ordinary parser behavior rather than defining an API schema.
- The spec/plan pair is repository-durable at `docs/specs/capture-work-alias-removal/`. Core maintainers, the RFC-0083 Approver, reviewers, and CI must be able to read it; the verification ledger is the stable post-closeout evidence owner.
- Pre-review disconfirming probe: `rg -n 'parse_legacy_workspace_entry\\(|_accepted_legacy_entry\\(|def run_canonical_reconciliation|def compute_migration_plan' packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` shows that ordinary membership parsing and explicit migration share the accepted-legacy decoder, so T1 splits those consumers before removing compatibility behavior.

## Construction tests

Most construction tests live under **Tasks** below.

**Integration tests:** Run the focused canonical-reconciliation test, the complete historical migration-planning and migration-effects suites, Core work-intake surface tests, workspace-status projection tests, AgentBundle package tests and built-artifact parity, Core pack verification, self-host regeneration, and current-guide/link checks against one candidate revision.

**Manual verification:** Review the candidate's user-facing guide set for instructional `capture-work` usage. After all machine checks pass, record the RFC-0083 Approver's exact candidate, Core 3.0.0 version, checklist result, dual-reader rollback target, and decision in the verification ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User promise in Core and shared guides | T3 | Current-guide audit, guide tests, and rendered-link checks | `close-work` verifies only `work-intake` is taught for ordinary intake and the migration guide is explicitly recovery-only. |
| Current architecture in `docs/architecture/work-intake-and-artifact-routing.md` and `packs/core/DESIGN.md` | T1, T3 | Reconciliation and migration regression suites plus document audit | `close-work` verifies the ordinary-read and explicit-repair boundaries match shipped behavior. |
| Maintainer procedure in `docs/guides/reference/work-intake-maintenance.md` | T3, T5 | Candidate checklist and authorization record | `close-work` verifies the procedure names the release gate and selected rollback evidence. |
| Pack navigation in `packs/core/README.md`, `packs/core/JOURNEY.md`, and `packs/core/docs/index.md` | T2, T3, T4 | Pack inventory tests and self-host build | `close-work` verifies generated adapters and current navigation expose `work-intake` and not `capture-work`. |
| AgentBundle packaged runtime and version owners | T4, T6 | Package suite, built-artifact byte comparison, and publish evidence | `close-work` verifies the published package contains the candidate workspace-status engine and its two version owners match the release. |
| Core 3.0.0 release history | T4, T6 | Version-pair, changelog, and published-pack checks | `close-work` verifies the free-standing release entry and `Highlights` disposition match the published pack. |
| Removal evidence in `notes/verification-ledger.md` | T5, T6 | Exact candidate gate results, fresh authorization, and coordinated release receipts | `close-work` verifies the authorization predates publication and binds the released candidate and rollback target. |

## Design (LLD)

### Design decisions

Ordinary reconciliation and explicit migration stop sharing one accepted-legacy result. The historical decoder may remain behind migration-plan, apply, recovery, and rollback seams, but `run_canonical_reconciliation` no longer returns accepted legacy memberships or uses legacy aliases in duplicate, cooling, dependency, or dispatch derivation. Removing all legacy decoding was rejected because it would also remove the reviewed recovery mechanism and contradict the preserved ledger and rollback boundary. Traces to: AC-0003–AC-0005. Owned by: T1.

The `capture-work` skill directory, pack registration, activation evals, alias-equivalence behavior case, and alias-only router branch leave together. Historical prose filenames and fixture identifiers are not renamed merely to reach zero textual matches; the current-surface audit classifies each surviving match by role. Traces to: AC-0001, AC-0002, AC-0007, AC-0008. Owned by: T2, T3.

### Interfaces & contracts

The published Core skill inventory contains `work-intake` and no `capture-work` entry. Ordinary workspace status accepts only canonical target entries as lifecycle memberships. Explicit repair commands remain the sole current surface allowed to decode the historical shapes defined by RFC-0083. No new API contract, compatibility alias, fallback command, or result schema is introduced. Traces to: AC-0001–AC-0005. Owned by: T1, T2.

### Component / module decomposition

`workspace_status_engine.py` keeps canonical parsing and migration repair in their existing module; T1 narrows call paths instead of introducing a new parser module. `packs/core/.apm/skills/capture-work/` is deleted at the authored source. `work-intake` loses alias-only branches and eval inputs while retaining its canonical `remember` route. Build tooling remains unchanged and regenerates installed adapters and the packaged workspace-status engine. Traces to: AC-0001–AC-0005, AC-0011. Owned by: T1, T2, T4.

### State & control flow

Ordinary status and reconciliation map canonical entries into memberships and classify former accepted legacy shapes as unsupported, non-dispatchable input. An explicit repair-plan request can still select a reviewed legacy record, and apply, recovery, or rollback continues through the existing authorization, confirmation, ledger, and fingerprint states. Release flow is source change, focused evidence, generated projections, full candidate evidence, fresh authorization, then publication. Traces to: AC-0003–AC-0006, AC-0013. Owned by: T1, T4, T5.

### Failure, edge cases & resilience

A former legacy shape cannot silently disappear into an empty success: each representative fixture produces `unsupported_legacy` during ordinary reconciliation, while a canonical positive control still follows the normal path. The migration regression suite prevents separation of the ordinary reader from weakening explicit repair, exact-byte rollback, idempotence, recovery, confinement, or credential redaction. A stale or incomplete authorization stops publication rather than falling back to the elapsed release clock or version number. Traces to: AC-0003–AC-0006, AC-0013. Owned by: T1, T5.

### Dependencies & integration

Core pack and plugin manifests move together to 3.0.0 before self-host regeneration. Generated adapter directories, marketplace metadata, packaged workspace-status data, guide sites, and journey indexes are build outputs from the authored sources. No infrastructure, external service, dependency, or data migration is added. Traces to: AC-0002, AC-0009–AC-0012. Owned by: T3, T4.

## Tasks

### T1: Ordinary reconciliation rejects former legacy memberships while explicit repair stays green

**Depends on:** none

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, `packs/core/tests/skills/workspace-status/test_capture_work_removal.py`, `packs/core/tests/skills/workspace-status/test_workspace_status_engine_autonomous.py`

**Review shape:** DEEP but localized parser-consumer split; review the ordinary and explicit-repair call graphs together.

**Grounding:** `parse_legacy_workspace_entry` currently feeds `_extract_canonical_memberships` and migration planning. Existing migration behavior is pinned by `test_work_intake_migration_planning.py` and `test_work_intake_migration_effects.py`.

**Tests:**
- Materialize the following candidate red pytest stub unchanged as `packs/core/tests/skills/workspace-status/test_capture_work_removal.py`. It covers AC-0003 and is marked `stub: true`.

```python
"""Removal contract for ordinary accepted-legacy reconciliation."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_PACK_ROOT = Path(__file__).resolve().parents[3]
_ENGINE = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "workspace-status"
    / "scripts"
    / "workspace_status_engine.py"
)


def _load_engine():
    spec = importlib.util.spec_from_file_location(
        "core_workspace_status_capture_work_removal",
        _ENGINE,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# STUB: AC-0003
def test_ordinary_reconciliation_rejects_former_legacy_memberships() -> None:
    engine = _load_engine()
    source = {"mode": "repo-origin"}
    workspace = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": [
                    "spec/legacy-work",
                    {
                        "path": "docs/specs/canonical/spec.md",
                        "kind": "spec",
                        "source": source,
                        "summary": "Canonical control",
                        "needs": [],
                    },
                ],
                "active": [],
                "shipped": [],
            },
            "shaping_queue": {
                "active": [],
                "backlog": [
                    "legacy-shape",
                    {"slug": "legacy-design", "type": "design", "needs": []},
                ],
            },
            "brief_queue": {
                "draft": [],
                "ready": ["docs/product/briefs/legacy-brief.md"],
                "executing": [],
                "shipped": [],
            },
        },
        "backlog": {
            "open": [
                {
                    "slug": "legacy-backlog",
                    "source": "capture-work",
                    "summary": "Legacy backlog",
                    "needs": [],
                    "type": "spec",
                }
            ],
            "closed": [],
        },
    }

    result = engine.run_canonical_reconciliation(workspace)
    codes = [finding.code for finding in result.findings]

    assert result.legacy_memberships == []
    assert "legacy_entry" not in codes
    assert codes.count("unsupported_legacy") == 5
    assert any(
        evaluation.entry.path == "docs/specs/canonical/spec.md"
        for evaluation in result.evaluations
    )
```

- Stub validation on 2026-10-02: `python3 -m py_compile` exited 0 from disposable scratch, and the user-approved isolated execution failed at `assert result.legacy_memberships == []`, proving the intended red against the current ordinary reader. No repository test file was created.
- Extend the focused test with the RFC-0083 section 10 item 2 fixture matrix and assertions that legacy aliases no longer affect duplicate, cooling, dependency, or dispatch derivation.
- Run `test_work_intake_migration_planning.py` and `test_work_intake_migration_effects.py` unchanged in outcome for AC-0004 and AC-0005.
- Run the current writer and workspace-seed evidence selected by historical AC14 for AC-0006.

**Approach:**
- Keep the historical decoder reachable only from explicit migration seams. Route ordinary membership extraction through canonical parsing and unsupported-input findings without inventing a second parser module.

**Done when:** The AC-0003 focused test is green, the canonical positive control is evaluated, every historical legacy shape is unsupported in ordinary reconciliation, and the migration planning/effects suites remain green.

### T2: Core exposes no capture-work alias or alias-only runtime path

**Depends on:** none

**Touches:** `packs/core/.apm/skills/capture-work/**`, `packs/core/pack.toml`, `packs/core/.apm/skills/work-intake/scripts/intake_router.py`, `packs/core/.apm/skills/work-intake/evals/**`, `packs/core/tests/skills/capture-work/**`, `packs/core/tests/pack/test_work_intake_surface.py`

**Review shape:** MIXED removal across one skill, one manifest, and its direct tests/evals.

**Grounding:** The alias has no independent behavior; `test_capture_work_alias.py` and the `alias-equivalence` routing case enumerate its current compatibility contract.

**Tests:**
- Goal-based AC-0001 checks assert the authored skill directory, manifest entry, activation evals, alias-equivalence case, and alias-only router branch are absent while the canonical `work-intake` route and its `remember` behavior remain.
- Update Core surface tests so a missing `capture-work` primitive is the expected inventory, not a skipped test.
- Record `no stub (mode)`: this is a filesystem and manifest removal proved by inventory/build checks rather than a callable TDD surface.

**Done when:** Focused Core pack tests pass with `work-intake` present, no authored `capture-work` surface, and no alias-only execution branch.

### T3: Current guidance describes one intake name and a recovery-only migration path

**Depends on:** T1, T2

**Touches:** `guides/**/*.md`, `docs/guides/**/*.md`, `docs/architecture/*.md`, `packs/core/README.md`, `packs/core/DESIGN.md`, `packs/core/JOURNEY.md`, `packs/core/docs/*.md`, `packs/core/.apm/skills/work-intake/**/*.md`, `packs/core/.apm/skills/workspace-status/**/*.md`

**Review shape:** WIDE prose reconciliation with a closed current-surface audit; historical records and stable migration URLs remain outside rewrite scope.

**Grounding:** The current-surface set is derived at execution with a repository-confined search over the Touches globs for `capture-work`, `legacy_entry`, `legacy_memberships`, `Legacy Compatibility`, `accepted legacy`, and `legacy reader`; this includes the workspace-status skill and workspace schema surfaces omitted by the first draft.

**Tests:**
- Goal-based AC-0007 audit enumerates every `capture-work` match in maintained current guidance and fails any instruction, example, skill inventory, or journey step that invokes or advertises the removed alias.
- Goal-based AC-0008 audit classifies every derived current-surface match and rejects any unclassified match or current-state claim that the alias or ordinary accepted-legacy reader remains installed; surviving matches must be demonstrably historical or recovery-only.
- Goal-based AC-0012 checks run guide, journey, site-generation, and rendered-link validation over the changed documentation surfaces.
- Run guide-authoring, guide-index, journey, documentation-link, site-generation, and rendered-link checks.
- Record `no stub (mode)`: content and link gates verify maintained prose surfaces.

**Approach:**
- Keep the stable migration guide URL and historical term where needed for adopters arriving from old releases, but frame the page as explicit recovery and direct all new intake to `work-intake`.

**Done when:** The current-surface audit has no instructional alias use or installed-compatibility claim, and every guide, journey, site, and link check is green.

### T4: Core 3.0.0 and the synchronized AgentBundle runtime are release-ready

**Depends on:** T1, T2, T3

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`, `tools/check-core-release.py`, `tools/test_check_core_release.py`, `packages/agentbundle/pyproject.toml`, `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/agentbundle/_data/workspace_status_engine.py`, `packages/agentbundle/tests/**`, generated self-host projections and marketplace metadata

**Review shape:** WIDE mechanically generated projection update with source-to-output equality checks.

**Grounding:** `packs/AGENTS.md` and `packs/AGENTS.local.md` own the major-version, projection, and release-history coupling.

**Tests:**
- Goal-based AC-0002 checks inspect the clean self-host output across supported adapters and Core journey inventory for `work-intake` presence and `capture-work` absence.
- Goal-based AC-0009 checks require version `3.0.0` in both Core manifests and a free-standing Core 3.0.0 changelog entry with a `Highlights` disposition.
- Extend `tools/check-core-release.py` with an explicit release-kind selector whose default retains the patch-successor rule and whose `major` mode accepts only the next major with minor and patch reset to zero. Extend `tools/test_check_core_release.py` with positive next-major coverage and refusals for a minor successor, an unchanged version, and a major overshoot, then run the checker for the Core 3.0.0 candidate in major mode.
- Run `make build-self`, inspect generated changes, then run the projection and packaged-runtime parity suites.
- Run `make lint-ruff lint-mypy` for AC-0010.
- Run self-host, catalogue, adapter-projection, and packaged-runtime parity checks for AC-0011.
- Update both AgentBundle version owners to the same release version selected under the package release process, run `python3 -m pytest packages/agentbundle/tests/ -q`, and verify the built package contains a byte-identical candidate `workspace_status_engine.py`.
- Record `no stub (mode)`: version, changelog, build, and projection properties are goal-based.

**Done when:** Authored sources and generated outputs agree, both Core version owners read 3.0.0, the explicit next-major Core release check passes while its default patch mode remains pinned, both AgentBundle version owners match their package release, the built package contains the candidate runtime, the release record is complete, and all required local gates are green.

### T5: The exact Core 3.0.0 candidate receives fresh removal authorization

**Depends on:** T1-T4

**Touches:** `docs/specs/capture-work-alias-removal/notes/verification-ledger.md`

**Review shape:** DEEP evidence and human-authorization gate over an otherwise frozen candidate.

**Grounding:** RFC-0083's 2026-10-02 Errata requires the authorization to bind the exact removal diff, release version, evidence checklist, and rollback target.

**Tests:**
- Re-run the AC-0003 focused test; migration planning/effects suites; writer/seed/fixture checks; Core pack tests; the Core release checker in explicit major mode; projection parity; guide/link checks; `make lint-ruff lint-mypy`; and `git diff --check` against one candidate identity.
- Record each command, result, candidate identity, Core 3.0.0 version, and the immediately preceding dual-reader release selected as rollback target in the verification ledger.
- Manual QA for AC-0013: the RFC-0083 Approver reviews that exact ledger and records an authorize or reject decision before publication.
- Record `no stub (mode)`: this task verifies candidate evidence and a human authorization boundary.

**Done when:** Every required candidate check is current and passing, the authorization record binds the exact candidate and rollback target, and no release or merge effect occurred before authorization.

### T6: The authorized Core and AgentBundle releases carry one candidate

**Depends on:** T5

**Touches:** `docs/specs/capture-work-alias-removal/notes/verification-ledger.md`

**Review shape:** DEEP coordinated release evidence across two published artifacts.

**Grounding:** Core is repo-only: its release evidence is the authorized `main` commit carrying matching 3.0.0 manifests, changelog, and projections, not a Claude-plugin registry receipt. AgentBundle ships the synchronized package-data engine; its package workflow accepts only a tag on `main`, and package guidance requires that tag to be pushed immediately after the version-bumping merge.

**Tests:**
- Goal-based AC-0014 checks record the authorized candidate's merge identity on `main`, the matching Core 3.0.0 manifest and changelog identity at that commit, the immediate AgentBundle tag push, the published AgentBundle package version, and the SHA-256 equality between the package's `workspace_status_engine.py` and the authorized candidate source.
- Verify both AgentBundle version owners equal the published package version and the package publish workflow is green.
- Merge the exact authorized candidate to `main`, record that commit as the Core 3.0.0 release identity, and tag and push the AgentBundle version immediately after the version-bumping merge so its package workflow publishes the synchronized runtime.
- Wait for the AgentBundle release workflow and package registry to confirm publication. Record the Core commit evidence and AgentBundle publication receipt separately; do not invent a Core registry receipt.
- Record `no stub (mode)`: published registry state and artifact bytes are goal-based release evidence.

**Done when:** The exact authorized candidate is merged to `main` with Core 3.0.0 release evidence, its AgentBundle version tag is pushed immediately, the coordinated AgentBundle package is published from that commit, the distinct Core and AgentBundle evidence is in the verification ledger, and the published package runtime is byte-identical to the candidate source.

## Rollout

- **Delivery:** Core 3.0.0 removes the alias and ordinary compatibility reader in one major-release cutover; there is no feature flag or partial adapter rollout.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** finish T1–T4, freeze the candidate, and complete T5 authorization. T6 merges that exact candidate to `main`, records the resulting commit as the repo-only Core 3.0.0 release, then immediately pushes the AgentBundle version tag to trigger its synchronized package release. AgentBundle publication is registry-backed; Core evidence remains repository-backed.
- **Rollback:** return to the immediately preceding published dual-reader Core release named in the fresh authorization. Existing migration ledgers, canonical artifacts, and receipts remain in place; no reverse data migration or deletion occurs.
- **Irreversibility:** publication removes a public skill name for 3.0.0 consumers. The repository change is revertible, but restoring compatibility requires another Core release.

## Risks

- The shared legacy decoder currently supports both ordinary reconciliation and explicit repair; deleting it wholesale would satisfy alias removal while breaking migration and rollback.
- A token-wide purge could rename historical fixtures, stable migration URLs, or evidence records without changing current behavior; T3 classifies matches by semantic role instead.
- Hand-editing installed adapters could appear complete until the next self-host build restores the alias; T4 treats `.apm` as the source and generated equality as the oracle.
- Version or build success could be mistaken for removal authority; T5 keeps fresh RFC authorization as the final check-before-effect gate.
- Another Core release landing before candidate freeze could change the correct rollback target; T5 resolves and records the immediately preceding dual-reader release rather than relying on this draft's current version.

## Changelog

<!-- Approval entries are added only by the spec and plan approval gates. -->

- 2026-10-02: spec approved by owner
- 2026-10-02: plan approved by owner
