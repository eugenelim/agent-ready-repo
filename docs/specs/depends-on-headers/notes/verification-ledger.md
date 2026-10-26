# Verification ledger: depends-on-headers

Execution observations recorded during the build. The spec and plan stay pinned; this file holds what the work learned.

## T1

- 2026-10-25: frozen `needs`-form expectations for 29 cases, commit `80c39a40f`; `test_depends_on_headers_equivalence.py` 3 passed.

## T2

- 2026-10-25: reader and resolution index, commit `155f213d8`; 64 reader tests red before, green after; workspace-status pack suite 344 passed, 1 skipped.
- 2026-10-25: a cooled intent cannot be indexed by slug, because its body is never opened and its lifecycle record carries only locators (`contracts/jsonschema/delivery-lifecycle-record.schema.json`). A typed reference to a cooled intent is therefore a missing target, which blocks, where a `needs` edge to it was satisfied by the lifecycle record. No live edge targets a cooled intent. The difference goes into the RFC-0106 errata entry (T7) as a recorded removal, for the Approver's signature.

## T3

- 2026-10-25: blocking moves to the header, commits `80399c5d8` (engine, `navigate-intents` table, eval fixtures, equivalence suite) and `6d59e6b67` (suite migration). The cooled brief cases' `needs`-form outcome, recorded from the engine at `1f9c27342` run from a `git worktree` of that commit, is in `fixtures/depends-on-headers/expected-cooled-brief.json`: both the `Slug:`-equals-stem case and the no-`Slug:` case were satisfied (no finding, waiting item dispatchable), and the header form reproduces it.
- Behaviors that changed with the switch, each pinned by a migrated assertion: a brief reference into a directory holding an unreadable or escaping entry is `unreadable_artifact` (AC-0027), where the `needs` edge gave `invalid_artifact_path`; a coordination receipt on a non-brief reference is `invalid_dependency`; a receipt with a missing or extra token is `invalid_dependency` at the waiting item, where a malformed `needs` receipt discarded the entry; a registry edge whose `path` differs from its `containing_brief`, and a `needs` kind that disagrees with the registered kind, have no header form and stay `unmigrated_needs` (AC-0020 refuses them in the repair).
- `queue-to-shipped` still moves an entry that carries `needs`: `_repair_entry_eligibility` admits `unmigrated_needs` beside `impossible_transition` and `unapproved_spec`, because the move leaves the `needs` array untouched.
- Red until a later task, at base and now: `test_workspace_status_projection.py::test_t4_repair_determinism_projection_and_release_surface` (SKILL.md and the schema guide need rows for `invalid_dependency` and `unmigrated_needs`, T5); `test_two_sided_prune_closure_invariant.py::test_pack_delivery_contract_is_complete_and_version_increased` (core version bump, T6).

## Amendment 1 — 2026-10-25

<a id="amendment-1"></a>

- **Trigger.** T2 added `invalid_dependency` to the engine's `_FINDING_NEXT_ACTIONS`, and T3 adds `unmigrated_needs`. `packs/core/tests/skills/navigate-intents/test_export_readiness.py::test_readiness_vocabulary_matches_workspace_status` requires `navigate-intents`' pinned copy, `_KNOWN_FINDINGS` in `intent_readiness.py`, to equal that table, so it fails at `155f213d8`. The spec's Never-do rule forbade any change to `navigate-intents`.
- **Owner decision.** eugenelim, 2026-10-25, in session: narrow the Never-do rule to admit one change in `navigate-intents`, adding the new finding codes to `_KNOWN_FINDINGS` as its parity test requires. The brief's non-goal about `navigate-intents` is read as narrowed the same way, for this copy only.
- **Also folded in.** The cooled-intent difference recorded under T2 becomes an Equivalence case (AC-0014) and a named removal in the RFC-0106 errata entry (T7).
- **Completed evidence.** T1 = commit `80c39a40f`; T2 = commit `155f213d8`.
- **Widened in review.** The amendment's adversarial review found the same cause for a cooled brief whose `Slug:` differs from its file stem: the index admits a cooled brief by stem alone, so a `brief:<Slug>` reference to it has no target once it cools. Both cases are one recorded removal, "the cooled target named by an unreadable slug". No brief in this repository has a `Slug:` that differs from its stem.
- **Deferred Nit (amendment review round 4).** A cooled brief with no `Slug:` field is named in neither AC-0003's cooled-brief case nor AC-0014's removal; it matches by stem and so behaves like AC-0003's case. Every live brief carries a `Slug:` line. Deferred with citation `.context/reviews/d123e014-033a-4fba-a583-8efe9ee0a4a4/9-pre-execute-adversarial-reviewer-raw.md`; T3 covers it with the cooled brief case.

## For T7

- 2026-10-25: a cooled captured item with no registry membership is `invalid_dependency` in header form, because its `Kind:` line is never read; a `needs` edge to a non-defect one was satisfied by its lifecycle record. This is a fourth difference of the same kind as the cooled target named by an unreadable slug, and it goes into the RFC-0106 errata entry and an Equivalence row for the Approver's signature. No live edge targets one.
- 2026-10-25: an escaping brief target gives `unreadable_artifact` (AC-0027) where the `needs` form gave `invalid_artifact_path`; both block. The Equivalence record notes the code change.

## T4

- 2026-10-26: `needs-to-header` and `needs-drop-cooled` in `repair-plan` and `repair-apply`, commits `4f4e4e4c0` (script, engine text-reader split, `mutate.md`, repair suite, packaged copies) and `6abe3d4b3` (re-pinned `workspace_status.py` and engine digests in `test_workspace_status_progressive_disclosure.py`; the inline-object queue-to-shipped CLI assertion now expects the same plan to clear `needs` and add `Depends on: spec:other`). `test_depends_on_headers_repair.py` 31 passed; workspace-status pack suite 439 passed, 2 skipped; `tools/test_workspace_status.py` and `_cli.py` 255 passed; roster `-k "workspace or repair or prune or receipt or cooling"` 744 passed, 2 failed (the two known T5/T6 reds).
- Engine change: `header_dependencies_from_text` split out of `read_header_dependencies`, so the repair reads a planned header exactly as the engine reads a file.
- Echo and edge decisions: plan stdout echoes each part per AC-0028 while the plan file holds every value whole. `header_edges_before` counts every raw header item and `header_edges_after` counts only items the reader accepts alone, so a hand-planted refused item makes `edges_equal` false; an operation whose per-file read-back differs keeps its `needs`. A non-expressible, duplicate-membership, or cooling-unreadable case is a manual finding of `finding_type` 4.

## T5

- 2026-10-26: instruction sites (AC-0018) name `Depends on:` and `Dependency receipts:`: `close-work` SKILL.md and its eval 10, `workspace-status` SKILL.md (an `Where an edge lives` paragraph and the `invalid_dependency` and `unmigrated_needs` finding rows) and `references/reconcile.md`, the `new-spec` contract reference and template, the schema guide, the architect how-to, `packs/architect/DESIGN.md`, and `docs/product/workspace-toml-deps.md` (rewritten as the header reference, with a legacy-`needs`-is-repair-input section). `test_t4_repair_determinism_projection_and_release_surface` passes.
- AC-0016: the only offender was `guides/architect/how-to/establish-reference-architecture.md`; fixed. `tests/roster/test_depends_on_headers_instructions.py` enforces AC-0016 and AC-0018, wired in `build-check.yml` and `STEP_DISPOSITION`.
- The plan expected a `workspace-status` SKILL.md §1 to §5 anchor hash in `tools/test_workspace_status.py`; that file pins only the `work-loop` windows now, so no hash changed.
- ADR-0148 drafted as `Proposed` with `Supersedes in part: ADR-0103 D6`. `lint-adr-shape.py` reports ADR-S010 twice, because ADR-0103 lacks the mirrored `Superseded in part: ADR-0148 D6`. The mirror is held as `.context/adr-0103-superseded-in-part-mirror.patch`, to apply with the Approver's acceptance; with it applied the lint is clean.
- Inventory: `packs/architect/DESIGN.md` row removed (last registry mention gone); ADR-0110, the `cooling-brief-child-scope-closure` spec directory, and the two cooling roster tests re-owned to 8 (`source.parent`); the `dependency-scoped-completion-receipts` spec directory and its roster test re-owned to 9; ADR-0103, CAP-0004, FEAT-0002, and `workspace-toml-deps.md` stay at 2 with new consumer text; rows added for ADR-0148 and the new roster test.
- No core version bump here (T6). `packs/architect/DESIGN.md` is outside `.apm/` and `seeds/`, so architect needs no bump.

## T6, first run (superseded)

This run was on the branch's first base, `1f9c27342`. The branch was rebuilt on `5cec6ac3e` (#1614), and the migration was rerun there; see § T6 below.

- 2026-10-26: normalized the four Shipped specs' `Depends on:` lines (commit before the repair); `status` then reported no `invalid_dependency`.
- 2026-10-26: before-capture ran `workspace_status.py status --root .` from a `git worktree` of `1f9c27342` at `.context/base-1f9c273` (removed afterwards) over the tree the repair read: canonical ready 0, active 3, blocked 28, findings 65.
- 2026-10-26: `repair-plan`: 78 `needs-to-header` operations, 113 registry edges (91 `spec:`, 16 `intent:`, 4 `brief:`, 2 `capability:`), no refusal, no `needs-drop-cooled`; plan sha256 `96c83cab88117652164097e6fd80b4981900dcf11c703df0fee940961c5da8fb`, plan_id `f479cc64b9d06018…`. The owner confirmed this exact plan.
- 2026-10-26: `repair-apply --yes`: 78 applied, `header_edges_before` 1, `registry_edges` 113, `dropped_cooled` 0, `header_edges_after` 113, `edges_equal` true. No registry entry carries typed `needs` afterwards.
- 2026-10-26: AC-0015 comparison, this slice's engine over the migrated tree against the base engine over the tree the repair read: canonical ready, active, and blocked paths, canonical findings by code and path, legacy work ready and blocked lists, and shaping lists all equal.
- 2026-10-26: AC-0017: `navigate-intents query --operation dependencies` over the 17 migrated intents reports no fault-state diagnostic; `spec:` items are `outside_scope`.
- 2026-10-26: `core` 3.1.18 → 3.1.19 in `pack.toml` and `.claude-plugin/plugin.json`; changelog fragment `bb02c266`; `make build-self` clean.

## Amendment 2 — 2026-10-26

<a id="amendment-2"></a>

- **Trigger.** T7's review of the drafted RFC-0106 errata entry found that the cooled captured item without a membership (recorded under "For T7") has no case in AC-0014 and no row in T7, and that the cooled-waiting-item removal fails open: a live member of a cycle through a cooled item can become dispatchable, because the cooled item's edges are not read and its own dependency on the cooled item counts as satisfied.
- **Owner decision.** eugenelim, 2026-10-26, in session: add the cooled captured item without a membership to AC-0014 and the errata entry, and keep the cooled-waiting-item removal with its effect stated plainly.
- **Completed evidence.** T1 `80c39a40f`; T2 `155f213d8`; T3 `80399c5d8`, `6d59e6b67`; T4 `4f4e4e4c0`; T5 `e3770947f`, `a41742e44`; T6 `3078c3857`, `8ba2210ab`.
- **Deferred Nit (amendment 2 review round 3).** workspace-retirement plan T7 Done when does not repeat the no-skip collection clause its Tests bullet names; a failing planted-row run already shows the tests ran. Citation `.context/reviews/d123e014-033a-4fba-a583-8efe9ee0a4a4/12-pre-execute-adversarial-reviewer-raw.md`.
