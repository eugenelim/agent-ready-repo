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
| AgentBundle packaged runtime and version owners | T4, T10, T6 | Package suite, built-artifact byte comparison, and publish evidence | `close-work` verifies the published package contains the candidate workspace-status engine and its two version owners match the release. |
| Core 3.0.0 release history | T4, T10, T6 | Version-pair, changelog, and published-pack checks | `close-work` verifies the free-standing release entry and `Highlights` disposition match the published pack. |
| Removal evidence in `notes/verification-ledger.md` | T5, T11, T6 | Exact candidate gate results, fresh authorization, and coordinated release receipts | `close-work` verifies the authorization predates publication and binds the released candidate and rollback target. |

## Design (LLD)

### Design decisions

Ordinary reconciliation and explicit migration stop sharing one accepted-legacy result. The historical decoder may remain behind migration-plan, apply, recovery, and rollback seams, but `run_canonical_reconciliation` no longer returns accepted legacy memberships or lets a legacy alias create a membership, cooling, satisfied dependency, or dispatch. A surviving alias may only refuse dispatch of its canonical twin (owner decision, 2026-10-08; implemented by T7). Removing all legacy decoding was rejected because it would also remove the reviewed recovery mechanism and contradict the preserved ledger and rollback boundary. Traces to: AC-0003–AC-0005. Owned by: T1.

The `capture-work` skill directory, pack registration, activation evals, alias-equivalence behavior case, and alias-only router branch leave together. Historical prose filenames and fixture identifiers are not renamed merely to reach zero textual matches; the current-surface audit classifies each surviving match by role. Traces to: AC-0001, AC-0002, AC-0007, AC-0008. Owned by: T2, T3.

### Interfaces & contracts

The published Core skill inventory contains `work-intake` and no `capture-work` entry. Ordinary workspace status accepts only canonical target entries as lifecycle memberships. Only explicit repair commands (migration, prune, Type 2 repair) and the unchanged status-analysis layer (`extract_initiatives` listings, Type 1/2/3 scans, engine `explain_item`) decode the historical shapes defined by RFC-0083, and none of them dispatches. Canonical reconciliation decodes an alias only to refuse dispatch of its canonical twin (T7). No new API contract, compatibility alias, fallback command, or result schema is introduced. Traces to: AC-0001–AC-0005. Owned by: T1, T2.

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

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, `packs/core/tests/skills/workspace-status/test_capture_work_removal.py`, `packs/core/tests/skills/workspace-status/test_workspace_status_engine_autonomous.py`, `packs/core/tests/skills/workspace-status/test_work_intake_migration_planning.py`, `packs/core/tests/skills/workspace-status/test_work_intake_migration_effects.py`, `packs/core/.apm/skills/workspace-status/scripts/workspace_status_prune.py`, `tests/roster/test_cooling_scope_closure.py`, `tests/roster/test_cooled_work_entry_classes.py`, `tests/roster/test_two_sided_prune_closure_invariant.py`, `tests/roster/test_workspace_status_progressive_disclosure.py`, `tests/roster/test_selection_scoped_membership_absence.py`, `tests/roster/test_status_projection_and_context_exclusion.py`, `tests/roster/test_cooling_brief_child_scope_closure.py`, `tools/test_workspace_status.py`, `tools/test_workspace_status_cli.py`, `packs/core/.apm/skills/workspace-status/evals/**`

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
- Move migration finding and selection setup to explicit migration parsing, and verify the CLI rollback path uses that same retained repair boundary. Preserve every existing planning, apply, interruption-recovery, and exact-byte rollback outcome assertion.
- Run the current writer and workspace-seed evidence selected by historical AC14 for AC-0006.
- Closeout keeps an open shaping or brief entry that no canonical parse accepts as `initiative-residue`, so a former legacy entry cannot make an initiative look empty. The legacy residue tests in `packs/core/tests/skills/workspace-status/test_closeout_initiative_residue.py` pass unchanged, and `test_capture_work_removal.py` covers shaping and brief shapes plus a canonical-only control.
- Update `tests/roster/test_cooling_scope_closure.py` where it pins removed ordinary-legacy behavior: cooled legacy entries are rejected rather than cooled, the migration realness helper proves its fixture through the explicit migration extractor, and the AC24 call-site count reflects the rollback path's move to that extractor. Keep every cooling-identity assertion for migration plan, apply, recovery, and rollback.
- In `tests/roster/test_cooled_work_entry_classes.py`, a former legacy `spec/<slug>` work entry is `unsupported_legacy` and is not a cooled closeout member, so the initiative's queue is not reported empty; the canonical bare-slug control stays unchanged.
- Prune stays a repair operation (owner decision, 2026-10-07): `workspace_status_prune.py` decodes historical legacy aliases through the retained decoder, so a surviving legacy alias still denies closure and a clean prune still removes a selected legacy string alias. `tests/roster/test_two_sided_prune_closure_invariant.py` keeps those outcomes; only setup that reads ordinary `legacy_memberships` moves to the explicit migration extractor.
- Update the remaining tests that pin ordinary accepted-legacy reconciliation so they expect `unsupported_legacy`, empty ordinary `legacy_memberships`, and no alias-derived membership or duplicate: `tests/roster/test_selection_scoped_membership_absence.py`, `tests/roster/test_status_projection_and_context_exclusion.py`, `tests/roster/test_cooling_brief_child_scope_closure.py`, `tools/test_workspace_status.py`, and `tools/test_workspace_status_cli.py`. Their migration CLI cases keep every plan, apply, recovery, and rollback outcome. Refresh the backend-script SHA-256 pins in `tests/roster/test_workspace_status_progressive_disclosure.py` to the candidate bytes.
- The status-analysis layer keeps its HEAD behavior (owner decision, 2026-10-08): `extract_initiatives`, `_parse_work_entry`, the shaping and brief-queue parsers, the Type 1/2/3 scans, and engine `explain_item` are unchanged, so Type 2 `repair-plan` and `repair-apply` keep moving or removing a shipped or archived former legacy queue entry, ordinary `status`/`reconcile` keep their `type2_cleanup_ops` and Type 1 output, and the `type2-queue-structured-entry-required` and `type2-queue-canonical-blocked` manual findings stay. `test_capture_work_removal.py` pins that layer's view of canonical entries (canonical shaping entries stay out of the legacy shaping lists; a typed local work need stays `unsupported-typed-need`) and passes on the HEAD engine. CLI `explain` resolves through canonical reconciliation: a canonical selector is `matched`, and a former legacy selector is `not_found` with an `unregistered_work` finding; the `tools/` explain cases expect that.
- No user-facing surface emits the migration finding after this change (owner decision, 2026-10-07; this repository has no migratable entry). The AC27 migration CLI tests in `tools/test_workspace_status_cli.py` build their selection from `extract_legacy_migration_memberships` and keep every plan, apply, recovery, and rollback outcome.
- Update the workspace-status eval harness: eval 12 expects a former legacy string to be absent from `selected-membership` with no legacy occurrence, and eval 10's cooled-path-collision case expects the legacy string to surface as `unsupported_legacy` rather than a cooled membership. Their fixture workspaces change only where the case needs it.

**Approach:**
- Keep the historical decoder reachable only from explicit migration seams. Route ordinary membership extraction through canonical parsing and unsupported-input findings without inventing a second parser module.

**Done when:** The AC-0003 focused test is green, the canonical positive control is evaluated, every historical legacy shape is unsupported in ordinary reconciliation, the migration planning/effects suites remain green, closeout counts a rejected open entry as residue, prune and Type 2 repair keep their legacy outcomes, the workspace-status evals match the new expectations, and every test file named in this task's Touches passes except `test_pack_delivery_contract_is_complete_and_version_increased`, which T4's version bump satisfies.

### T2: Core exposes no capture-work alias or alias-only runtime path

**Depends on:** none

**Touches:** `packs/core/.apm/skills/capture-work/**`, `packs/core/pack.toml`, `packs/core/.apm/skills/work-intake/scripts/intake_router.py`, `packs/core/.apm/skills/work-intake/evals/**`, `packs/core/tests/skills/capture-work/**`, `packs/core/tests/pack/test_work_intake_surface.py`, `Makefile`, `.github/workflows/catalogue-tooling-ci-gates.yml`, `tools/lint-ci-parity.py`, `tools/add-rendering-directives.py`, `tests/roster/test_shaping_intake_handoff_matrix.py`, `tests/roster/test_work_intake_migration_contracts.py`, `packs/agent-skill-engineering/tests/fixtures/skill-census.json`

**Review shape:** MIXED removal across one skill, one manifest, and its direct tests/evals.

**Grounding:** The alias has no independent behavior; `test_capture_work_alias.py` and the `alias-equivalence` routing case enumerate its current compatibility contract.

**Tests:**
- Goal-based AC-0001 checks assert the authored skill directory, manifest entry, activation evals, alias-equivalence case, and alias-only router branch are absent while the canonical `work-intake` route and its `remember` behavior remain.
- Update Core surface tests so a missing `capture-work` primitive is the expected inventory, not a skipped test.
- Remove the deleted test directory from the `Makefile` suite list, the catalogue-tooling CI gate loop, and the CI-parity map; drop the `capture-work` rendering-directive key and skill-census entry; and replace the alias route record in the shaping-intake handoff matrix and the alias skill path in the migration contracts test. `python3 tools/lint-ci-parity.py`, `python3 tools/test-lint-ci-parity.py`, `tests/roster/test_skill_census.py`, and both roster tests pass.
- Record `no stub (mode)`: this is a filesystem and manifest removal proved by inventory/build checks rather than a callable TDD surface.

**Done when:** Focused Core pack tests pass with `work-intake` present, no authored `capture-work` surface, and no alias-only execution branch; `python3 tools/lint-ci-parity.py`, `python3 tools/test-lint-ci-parity.py`, `tests/roster/test_skill_census.py`, and the two named roster tests pass.

### T3: Current guidance describes one intake name and a recovery-only migration path

**Depends on:** T1, T2

**Touches:** `guides/**/*.md`, `docs/guides/**/*.md`, `docs/architecture/*.md`, `packs/core/README.md`, `packs/core/DESIGN.md`, `packs/core/JOURNEY.md`, `packs/core/docs/*.md`, `packs/core/.apm/skills/work-intake/**/*.md`, `packs/core/.apm/skills/workspace-status/**/*.md`, `packs/product-engineering/.apm/skills/map-capabilities/SKILL.md`, `packs/product-engineering/.apm/skills/place-bet/SKILL.md`, `packs/product-engineering/.apm/skills/place-bet/examples/placing-a-bet.md`, `packs/product-engineering/.apm/skills/diverge-solutions/examples/opportunity-to-options.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/evals/**`, `workspace.toml`

**Review shape:** WIDE prose reconciliation with a closed current-surface audit; historical records and stable migration URLs remain outside rewrite scope.

**Grounding:** The current-surface set is derived at execution with a repository-confined search over the Touches globs for `capture-work`, `legacy_entry`, `legacy_memberships`, `Legacy Compatibility`, `accepted legacy`, and `legacy reader`; this includes the workspace-status skill and workspace schema surfaces omitted by the first draft.

**Tests:**
- Goal-based AC-0007 audit enumerates every `capture-work` match in maintained current guidance and fails any instruction, example, skill inventory, or journey step that invokes or advertises the removed alias.
- Goal-based AC-0008 audit classifies every derived current-surface match and rejects any unclassified match or current-state claim that the alias or ordinary accepted-legacy reader remains installed; surviving matches must be demonstrably historical or recovery-only.
- Goal-based AC-0012 checks run guide, journey, site-generation, and rendered-link validation over the changed documentation surfaces.
- Run guide-authoring, guide-index, journey, documentation-link, site-generation, and rendered-link checks.
- Product-engineering skill guidance and examples that direct users to `capture-work` direct them to `work-intake` instead; the AC-0007 audit includes those four files.
- The work-loop skill's orientation step no longer describes retained ordinary `legacy_memberships`; it states that former legacy entries surface as `unsupported_legacy` findings and never dispatch. The AC-0008 audit includes that file, and the work-loop eval harness gains or updates a case for the changed sentence.
- `guides/core/how-to/migrate-capture-work.md` and `packs/core/.apm/skills/workspace-status/references/mutate.md` tell adopters to rewrite a former legacy entry in canonical form by hand, and describe the retained migration tooling only as recovery or rollback of an operation already in a migration ledger. The guide URL stays stable.
- Goal-based AC-0007 hand-rewrite audit: a repository-confined search over every T3 Touches surface for migration planning, `--migration-selection`, `legacy_entry`, `legacy_finding_id`, and `migration` finding classifies each match; it fails any match that starts a new migration from a legacy finding, and passes only recovery or rollback of an existing ledger operation, historical records, or the hand-rewrite instruction. Surfaces known to need edits include `guides/_shared/how-to/use-work-intake.md`, `guides/_shared/reference/work-intake-routing-and-lifecycle.md`, `guides/core/reference/workspace-toml-schema.md`, `guides/core/README.md`, `guides/core/how-to/orient-at-session-start.md`, `guides/core/how-to/capture-work.md`, `packs/core/README.md`, `packs/core/JOURNEY.md`, `packs/core/.apm/skills/workspace-status/SKILL.md`, and `docs/guides/reference/work-intake-maintenance.md`.
- The `workspace.toml` header comment no longer says entries reconcile as `legacy_entry`.
- Record `no stub (mode)`: content and link gates verify maintained prose surfaces.

**Approach:**
- Keep the stable migration guide URL and historical term where needed for adopters arriving from old releases, but frame the page as explicit recovery and direct all new intake to `work-intake`.

**Done when:** The current-surface audit has no instructional alias use or installed-compatibility claim; the AC-0007 hand-rewrite audit has no match that starts a new migration from a legacy finding; the product-engineering redirects, the work-loop sentence and its eval case, the migration guide and `mutate.md` edits, and the `workspace.toml` header comment are in place; and every guide, journey, site, and link check is green.

### T7: Review corrections keep dispatch fail-closed and restore lost test coverage

**Depends on:** T1, T2

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, `packs/core/tests/skills/workspace-status/**`, `tests/roster/test_cooling_scope_closure.py`, `tests/roster/test_workspace_status_progressive_disclosure.py`, `tests/roster/test_status_projection_and_context_exclusion.py`, `tests/roster/test_selection_scoped_membership_absence.py`, `tools/test_workspace_status.py`, `tools/test_workspace_status_cli.py`, `packs/core/.apm/skills/workspace-status/evals/**`

**Review shape:** DEEP but localized: one refusal guard and test restorations.

**Grounding:** Implementation review round 1 (ledger section "Implementation review — round 1") and the owner's alias-refusal decision recorded there. The owner reversed the shaping-listing decision, so T1's status-analysis outcome stands unchanged.

**Tests:**
- Alias refusal: the guard maps each historical entry through the retained decoder's canonical-alias rule `_legacy_canonical_alias`, whose branches are: work-collection `spec/<slug>` strings and the five-key `type = "spec"` `[backlog].open` object map to `docs/specs/<slug>/spec.md`; brief path strings map to that brief path; shaping-queue `{slug, type}` objects of type `research` or `design` map to `docs/product/research/<slug>.md` or `docs/product/design/<slug>.md`. Shapes the decoder maps nowhere (for example a bare shaping slug or a top-level `{slug, type}` shaping object) never refuse. A canonical entry whose path matches a surviving alias stays non-dispatchable with a `duplicate_membership` finding on the canonical path and its existing next-action text. Cases: a `spec/alpha` alias in the same collection, in each other work collection, in another initiative, and as the five-key `[backlog].open` spec object; a brief path string beside a canonical brief entry; a shaping research or design object beside its canonical entry; a negative control where an unmapped shape does not refuse; and controls where the same workspace without the alias dispatches. The alias cases in `test_t2_legacy_aliases_do_not_participate_in_duplicate_detection` (`test_workspace_status_engine_autonomous.py`) flip to expect the refusal. The alias itself still reports `unsupported_legacy`, and no legacy membership, cooling, or satisfied dependency comes from it. Update `test_capture_work_removal.py` and any test that asserted no alias-derived duplicate.
- A workspace-status eval case covers the alias refusal: the agent reports the canonical entry as blocked by the leftover alias and tells the user to delete the alias.
- A security-reviewer pass over the refusal guard is recorded in the verification ledger, and its findings are resolved.
- CLI `explain`: a canonical path under two initiatives returns exit 0, `selector_status: "ambiguous"`, and two `matches` with both `ini_slug` values; a matched canonical item asserts the documented `explained_item` keys; former-legacy `not_found` cases stay separate. `_canonical_explain` and `_explain_selector_targets` docstrings describe canonical-only resolution, and their dead `legacy_memberships`/`legacy_path` candidate matching is removed while the `spec/<slug>` selector spelling still maps to the canonical path.
- Cooling realness: `assert_migration_fixture_is_real` also proves the cooled fixture's lifecycle record resolves the legacy artifact's locator in the status `cooling` projection.
- Extractor positions: a test pins `extract_legacy_migration_memberships` `(ini_slug, collection, entry_index)` for every RFC-0083 section 10 shape across top-level and initiative collections, including multi-entry lists and the scalar `brief_queue.executing` form.
- Focused-test hygiene: the duplicate AC-0003 matrix test either adds a shape the stub lacks or is removed (the stub stays byte-identical), and the cooling test name matches what it asserts.
- Refresh the backend-script SHA-256 pins and update every test file in Touches whose expectation the guard moves.
- Record `no stub (implementation-discovered)`: review findings define these cases.

**Done when:** Every bullet above holds, every test file in Touches passes, and `make lint-ruff lint-mypy` is green.

### T8: Review corrections make current guidance match Core 3.0.0

**Depends on:** T3, T7

**Touches:** `guides/**/*.md`, `docs/guides/**/*.md`, `docs/architecture/*.md`, `packs/core/README.md`, `packs/core/DESIGN.md`, `packs/core/JOURNEY.md`, `packs/core/.apm/skills/workspace-status/**/*.md`, `packs/core/.apm/skills/work-intake/**/*.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/evals/**`, `packs/product-engineering/.apm/skills/frame-situation/SKILL.md`, `packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md`, `workspace.toml`

**Review shape:** WIDE prose reconciliation against the sustained experience and adversarial findings.

**Grounding:** Implementation review round 1 adjudications under `.context/reviews/09925534-68c8-4cf6-894a-a085439b8d0f/impl/`.

**Tests:**
- Each sustained guidance finding is resolved: the session-start next-action row, the schema reference migration subsection and line 42, the shared explanation's compatibility-window section, the product-engineering frame-a-situation note, architecture flow 6 and lines 14 and 80, the hand-rewrite pointer to the schema Target Entry, Lifecycle Membership, and Legacy Forms sections, JOURNEY lines 18 and 72, the recovery page's duplicated procedure, the README "compatibility forms" phrase, and the schema findings-table columns.
- The recovery guide and `references/mutate.md` tell users to recover with the operation ID recorded in `.workspace-migrations.json`, and do not present a re-derived plan's ID as usable for an operation planned under an earlier Core version.
- Guidance that says former legacy entries never dispatch also states that old shaping entries still appear in the information-only shaping lists until rewritten. This includes `work-loop/SKILL.md` (whose Step 0 eval case is updated with it) and the product-engineering `frame-situation` and `diverge-solutions` skills, whose content change rides T4's product-engineering patch release.
- The hand-rewrite instruction says to replace the legacy entry in the same edit, because a canonical entry is refused dispatch while its old alias survives. The schema findings table documents that `duplicate_membership` cause and its action.
- No work-intake eval expectation moves: T8 changes only explanatory prose there; workspace-status eval coverage for the changed behavior lives in T7.
- Re-run the T3 audits (AC-0007 `capture-work`, AC-0008 installed-compatibility, AC-0007 hand-rewrite) with search terms widened to `compatibility window`, `reviewed route selection`, `migration planner`, and `supported legacy`; every match is fixed or classified historical, recovery-only, or hand-rewrite.
- Record `no stub (mode)`: content and link gates verify prose.

**Done when:** Every bullet above holds, and the guide, guide-index, journey, and documentation-link checks are green.

### T9: Round-2 review corrections close the remaining contract gaps

**Depends on:** T7, T8

**Touches:** `packs/core/.apm/skills/workspace-status/SKILL.md`, `packs/core/.apm/skills/workspace-status/references/mutate.md`, `packs/core/.apm/skills/workspace-status/evals/**`, `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, `packs/core/.apm/skills/work-intake/SKILL.md`, `packs/core/.apm/skills/work-intake/evals/**`, `packs/core/tests/skills/workspace-status/**`, `packs/core/tests/pack/test_work_intake_surface.py`, `tests/roster/test_workspace_status_progressive_disclosure.py`, `docs/architecture/work-intake-and-artifact-routing.md`, `guides/core/how-to/capture-work.md`, `guides/core/reference/workspace-toml-schema.md`, `guides/product-engineering/how-to/frame-a-situation.md`, `docs/product/changelog.md`

**Review shape:** MIXED: agent-facing skill text, one comment, tests, and guidance.

**Grounding:** Implementation review round 2 adjudications (`.context/reviews/09925534-68c8-4cf6-894a-a085439b8d0f/impl/3-*-adjudication.md`) and the base-revision read of `references/mutate.md` recorded in the ledger.

**Tests:**
- `workspace-status/SKILL.md` names a surviving historical alias for the same artifact path as a cause of `duplicate_membership` and tells the agent to have the user delete the alias; the engine's next-action text is unchanged. Eval 16 gains a cross-initiative variant whose fixture puts the alias in another initiative, so naming the cause requires the skill guidance rather than matching slugs.
- `references/mutate.md` restores the four agent restrictions the T3 rewrite dropped, scoped to recovery and rollback: never create, edit, prefill, or suggest substantive values for a selection or confirmation file; never choose among candidates; migration planning is read-only and rejects `--plan-file`; when the human needs opaque test-safe identifiers, tell them to run the `secrets` one-liner themselves and do not run it for them. Its `selected-membership` description lists only `canonical` and `parse-blocked` occurrence forms. A security-reviewer pass over the restored text is recorded in the ledger.
- `work-intake/SKILL.md` no longer tells the agent to pass an alias signal, no longer routes compatibility-alias delegation through `work-intake`, and its description drops the older compatibility alias; `test_work_intake_surface.py` passes unchanged and `work-intake/evals/eval_queries.json` holds no query that depends on the dropped alias wording.
- The Type 2 repair seam's alias check stays as defence in depth with a comment that states canonical reconciliation already refuses the alias.
- Alias-refusal tests: the test is renamed to describe the refusal; a `work.shipped` alias case is added; one control with an Approved spec and plan on disk (a `tmp_path` root) asserts `dispatchable` true without the alias and false with it.
- `docs/architecture/work-intake-and-artifact-routing.md` states the real decoder boundary: refuse-only alias decoding in canonical reconciliation, the repair seams (migration recovery and rollback, prune, Type 2 repair), and the information-only status-analysis readers.
- `guides/core/how-to/capture-work.md` says old shaping entries still appear in the information-only shaping lists until rewritten (with a plain-words gloss), and says the canonical entry stays blocked with `duplicate_membership` while the old alias survives. `frame-a-situation.md` describes the canonical entry's shaping-queue listing without "`shape`-typed". The schema reference summary and intro drop "compatibility" for "former legacy forms" and "an `unsupported_legacy` or reconciliation finding".
- `docs/product/changelog.md`: the Core 3.0.0 Highlight says to rewrite the entry in canonical form by hand and delete the old alias in the same edit; the product-engineering 0.13.23 entry names `frame-situation` and the shaping-list note.
- Refresh the backend-script SHA-256 pins the engine comment moves.
- Record `no stub (implementation-discovered)`: review findings define these cases.

**Done when:** Every bullet above holds, every test file in Touches passes, the guide, guide-index, journey, and documentation-link checks pass, and `make lint-ruff lint-mypy` is green.

### T4: Core 3.0.0 and the synchronized AgentBundle runtime are release-ready

**Depends on:** T1, T2, T3, T7, T8, T9

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`, `tools/check-core-release.py`, `tools/test_check_core_release.py`, `packages/agentbundle/pyproject.toml`, `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/agentbundle/_data/workspace_status_engine.py`, `packages/agentbundle/agentbundle/_data/workspace_status_prune.py`, `packages/agentbundle/tests/**`, `web/src/content/journeys/core.md`, `packs/product-engineering/pack.toml`, `packs/product-engineering/.claude-plugin/plugin.json`, `packs/{code-intelligence,governance-extras,iac-terraform,monorepo-extras,release-engineering}/pack.toml`, `packs/{code-intelligence,governance-extras,iac-terraform,monorepo-extras,release-engineering}/.claude-plugin/plugin.json`, `tests/roster/test_shipped_pack_manifests.py`, `packs/governance-extras/tests/skills/new-rfc/test_project_knowledge_handoff.py`, `packs/code-intelligence/tests/pack/test_manifest.py`, `packs/monorepo-extras/README.md`, `profiles/full-ceremony.toml`, generated self-host projections and marketplace metadata

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
- Regenerate `web/src/content/journeys/core.md` with `python3 tools/build-site.py --journeys-only` and run `python3 tools/lint-web-journey-parity.py`.
- Change the `core` requirement in code-intelligence, governance-extras, iac-terraform, monorepo-extras, and release-engineering from `^2.0` to `^3.0`, bump each pack's two version owners to the same next patch version, and record each in the changelog. `agentbundle catalogue verify --root .` reports no `CAT-V-007` against Core 3.0.0.
- Update the pins of those values: `tests/roster/test_shipped_pack_manifests.py` and `packs/governance-extras/tests/skills/new-rfc/test_project_knowledge_handoff.py` expect `^3.0`; `packs/code-intelligence/tests/pack/test_manifest.py` expects code-intelligence's new patch version in both manifests; `packs/monorepo-extras/README.md` and the `profiles/full-ceremony.toml` comments state `^3.0`. All three test files pass.
- In `packages/agentbundle/tests/test_workspace_mcp_tools.py`, the MCP `workspace_status` result for a former legacy entry carries an `unsupported_legacy` finding, is absent from `ready` and `blocked`, and leaves the `legacy_memberships` key present and empty; `workspace_mcp.py` is unchanged.
- In `packages/agentbundle/tests/test_workspace_mcp_tools.py`, after the package-data resync, a canonical entry with a surviving historical alias appears in MCP `blocked` with a `duplicate_membership` finding and not in `ready`.
- The Core 3.0.0 Highlights are outcome-led bullets: send intake to `work-intake`, rewrite an `unsupported_legacy` entry by hand, and use `repair-plan --migration-selection`, `repair-apply`, and `repair-rollback` only to recover or roll back an operation already in the migration ledger. The agentbundle Highlight uses plain words without the RFC number.
- Bump product-engineering's two version owners to the same next patch version and record it in the changelog, because T3 changes its shipped guidance.
- Record `no stub (mode)`: version, changelog, build, and projection properties are goal-based.

**Done when:** Authored sources and generated outputs agree, both Core version owners read 3.0.0, the explicit next-major Core release check passes while its default patch mode remains pinned, both AgentBundle version owners match their package release, the built package contains the candidate runtime and prune module, both product-engineering version owners and those of the five Core-dependent packs read their next patch versions, catalogue verify passes against Core 3.0.0, the three version-pin test files pass, `test_pack_delivery_contract_is_complete_and_version_increased` passes, the web journey parity lint passes, the release record is complete, and all required local gates are green.

### T5: The exact Core 3.0.0 candidate receives fresh removal authorization

**Depends on:** T1-T4

**Touches:** `docs/specs/capture-work-alias-removal/notes/verification-ledger.md`

**Review shape:** DEEP evidence and human-authorization gate over an otherwise frozen candidate.

**Grounding:** RFC-0083's 2026-10-02 Errata requires the authorization to bind the exact removal diff, release version, evidence checklist, and rollback target.

**Tests:**
- Re-run the AC-0003 focused test; migration planning/effects suites; writer/seed/fixture checks; Core pack tests; the Core release checker in explicit major mode; projection parity; guide/link checks; `make lint-ruff lint-mypy`; and `git diff --check` against one candidate identity.
- Record each command, result, candidate identity, Core 3.0.0 version, and the immediately preceding dual-reader release selected as rollback target in the verification ledger, together with the prior versions of code-intelligence, governance-extras, iac-terraform, monorepo-extras, and release-engineering that must be restored with it.
- Manual QA for AC-0013: the RFC-0083 Approver reviews that exact ledger and records an authorize or reject decision before publication.
- Record `no stub (mode)`: this task verifies candidate evidence and a human authorization boundary.

**Done when:** Every required candidate check is current and passing, the authorization record binds the exact candidate and rollback target, including the restored versions of the five Core-dependent packs, and no release or merge effect occurred before authorization.

### T10: Release surfaces and pins match the 0.52.0 and 3.0.0 candidate

**Depends on:** T4, T5

**Touches:** `docs/product/changelog.md`, `packages/agentbundle/README-pypi.md`, `tests/roster/test_tracker_intake_adapters.py`, `tests/roster/test_okf_catalogue_discovery.py`, `tools/check-artifact-contents.py`, `tools/test_local_ci_shared_test_deduplication.py`, generated self-host projections and package data

**Review shape:** WIDE pin and release-record update proved by the five CI failure families it clears.

**Grounding:** PR #1525 CI (ledger section "T6 — CI on PR #1525 and the release-surface gap").

**Tests:**
- `docs/product/changelog.md`: the `[core][3.0.0]` entry sits directly beneath `[Unreleased]`, and the `[agentbundle][0.52.0]` entry stays the first `[agentbundle]` heading; `tests/roster/test_verification_ledger_contract.py` passes.
- `packages/agentbundle/README-pypi.md` opens its release notes with `## What's new in 0.52.0`, describing the MCP `workspace_status` change in plain words; `tests/roster/test_okf_catalogue_discovery.py` pins 0.52.0 (with its bump comment) and passes.
- `tests/roster/test_tracker_intake_adapters.py` pins 70 routing results, with a comment that the alias-equivalence case was removed, and passes.
- `tools/check-artifact-contents.py` pins the current SHA-256 of `packages/agentbundle/tests/test_workspace_mcp_tools.py`; `python3 -m pytest tools/test_check_artifact_contents.py` passes, including the real-sdist case.
- `tools/test_local_ci_shared_test_deduplication.py` re-pins the `tools/test_workspace_status_cli.py` test-method counts (166 to 168, for the two canonical `explain` tests T7 added) and the approved standalone and composed Make plan digests (moved by removing the `capture-work` test directory from the `Makefile`), each with a reason in the file's existing comment style, and passes.
- Run the full `tests/roster/` suite and every `gate-main` pytest step of `.github/workflows/build-check.yml` locally, so no pin is left for CI to find.
- Record `no stub (mode)`: pins and release records are goal-based.

**Done when:** Every bullet above holds, `make build-self` leaves no drift, `make lint-ruff lint-mypy` is green, and the full roster suite, the dedup guard, and every local `gate-main` pytest step pass.

### T11: The corrected candidate receives fresh removal authorization

**Depends on:** T10

**Touches:** `docs/specs/capture-work-alias-removal/notes/verification-ledger.md`

**Review shape:** DEEP evidence and human-authorization gate over the corrected candidate.

**Grounding:** RFC-0083's 2026-10-02 Errata binds the authorization to the exact diff; T10 changes the T5-authorized candidate.

**Tests:**
- Re-run the T5 checklist on the corrected candidate, plus the full roster suite, and record the results in the ledger.
- PR #1525 CI (build-check, release-agentbundle, and the other PR workflows) and the dispatch-only test-roster and test-corpus workflows are green on the exact corrected candidate commit; their run IDs are recorded in the ledger.
- Manual QA: the RFC-0083 Approver records a fresh authorize or reject decision before T6 merges anything. It binds the corrected candidate commit, Core 3.0.0, AgentBundle 0.52.0, the five dependent packs' versions, the checklist, and the dual-reader rollback target (Core 2.30.1 with the five dependent packs, product-engineering, and AgentBundle at their prior versions). The T5 authorization is superseded and not reused.
- Record `no stub (mode)`.

**Done when:** The checklist and the named CI runs are green on the corrected candidate commit, and the fresh authorization record binds every item the Tests bullet names.

### T6: The authorized Core and AgentBundle releases carry one candidate

**Depends on:** T5, T11

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
- **Deployment sequencing:** finish the implementation tasks, freeze the candidate, and complete the T11 authorization, which supersedes T5's. T6 merges that exact candidate to `main`, records the resulting commit as the repo-only Core 3.0.0 release, then immediately pushes the AgentBundle version tag to trigger its synchronized package release. AgentBundle publication is registry-backed; Core evidence remains repository-backed.
- **Rollback:** return to the immediately preceding published dual-reader Core release named in the fresh authorization, and restore code-intelligence, governance-extras, iac-terraform, monorepo-extras, and release-engineering to their recorded prior versions with it. Existing migration ledgers, canonical artifacts, and receipts remain in place; no reverse data migration or deletion occurs.
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
- 2026-10-07: owner approved the bounded T1 amendment for explicit migration consumers and retained rollback verification.
- 2026-10-08: amended spec approved by owner
- 2026-10-08: amended plan approved by owner
- 2026-10-08: second amended spec approved by owner
- 2026-10-08: second amended plan approved by owner
- 2026-10-08: third amended spec approved by owner
- 2026-10-08: third amended plan approved by owner
- 2026-10-09: fourth amended spec approved by owner
- 2026-10-09: fourth amended plan approved by owner
