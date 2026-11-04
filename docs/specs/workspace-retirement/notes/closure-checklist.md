# Closure checklist for the workspace.toml retirement

This checklist tracks RFC-0105 D3's four gates and the slice 9 items of
[the delivery brief](../../../product/briefs/workspace-registry-retirement-delivery.md). The
[retirement record](../retirement-record.md) holds the per-fact dispositions, the
equivalence rows and the certification; its § Certification stays empty until
the maintainer writes it.

The four gates are RFC-0105 D3's. Each slice 9 item is the brief's. A row reads `done` only where its evidence resolves in the tree. The maintainer's certification is not recorded here; § Certification stays empty until the maintainer writes it.

| Item | State | Evidence | Owner of what is open |
| --- | --- | --- | --- |
| Gate 1, consumer inventory | done | `inventory.toml` holds 621 rows; `tests/roster/test_workspace_retirement_inventory.py` runs on every pull request | none |
| Gate 2, state disposition | done | § Disposition names a home and an owner for every fact; AC-0011 to AC-0016 pass | none |
| Gate 3, behavioral equivalence | recorded, not certified | § Equivalence holds rows for the slices that changed behavior, and the verification ledgers of `last-registry-entries` and `repair-only-workspace-status` hold the final replays | Platform Core maintainer judges completeness at certification |
| Gate 4, compatibility closure | open | the rows below | slice 9 |
| Stop registering tracker-origin work | done | `tracker-origin-registration-stop`, `core` 4.0.1 | none |
| Retire `close-work`'s registry field | done | `pre-cutover-closure`, `core` 4.0.2 | none |
| Re-own the inventory rows slices 2 to 8 owned | done | `pre-cutover-closure`: 10 became `historical`, 9 moved to slice 9 | none |
| Publish the upgrade notes | done | `registry-upgrade-notes`, `core` 4.0.14: `guides/core/how-to/upgrade-from-a-workspace-registry.md`; the `pre-cutover-closure` draft stays as that spec's record | none |
| Move the engine rules dispatch needs into `work-loop` | done | `repair-only-workspace-status`, `core` 4.0.10 | none |
| Shrink `workspace-status` to the repair | done | the same spec: `workspace-status` keeps `repair-plan` and `repair-apply` | none |
| Remove the legacy registry entries and re-point the spec-status lint anchors | done | `last-registry-entries`, `core` 4.0.5 | none |
| Give `[authorization.refresh]` and `[authorization.migration]` a home | done | refresh policy moves to `.work-intake.toml` (`last-registry-entries`); `[authorization.migration]` is retired (`repair-only-workspace-status`) | none |
| Move seeds, manifests, guides and operative references | partly done | `registry-upgrade-notes`, `core` 4.0.14, deletes the `core` seed and routes every operative guide, page, manifest and skill to `dispatch.py`, held by a roster check over 1,521 files. 298 inventory rows still name slice 9 as owner: 114 `contract`, 89 `fixture`, 48 `guide`, 20 `projection`, 11 `promise`, 8 `reader`, 7 `writer`, 1 `seed` | slice 9: re-own or retire each row |
| Pass the activation and corpus gates | open | no run is recorded here | slice 9 |
| Record the certification in this spec and the retiring change | open | § Certification is empty | Platform Core maintainer |
| Delete `workspace.toml` | open | the registry file is still tracked and still holds initiative tables; it is deleted only after certification and with the maintainer's confirmation | Platform Core maintainer |
