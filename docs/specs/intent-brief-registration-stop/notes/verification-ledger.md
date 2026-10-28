# Verification ledger: intents and briefs stop being registered

## T1: the registry comparison before the stop

Run on 2026-10-27 on this spec's branch, before any writer instruction or registry entry changed, as FEAT-0034's validation hook requires. It ran over a `git archive` of the commit below, so the uncommitted spec files and this spec's own registry entry are not part of what it read.

- **Command:** `python3 tools/compare-registry.py --root <git archive of the commit below>`
- **Commit:** `47e1b2836df32852bf3d3d7011283c19f26296e7`
- **Merge base with `origin/main`:** `47e1b2836df32852bf3d3d7011283c19f26296e7`
- **Exit code:** `0`, so no row is failing and repo-origin intent and brief registration may stop.

Full default output:

```text
registry comparison: pass
captured_item 0
legacy_shape 0
registry_stale 0
registry_closed_stale 0
registry_omission 48
registry_live_only 0
result_terminal 0
unclassified 0
commit 47e1b2836df32852bf3d3d7011283c19f26296e7
workspace.toml sha256 53cf9ad7f5d971c878e8178acc6744b1a6254fc4db90173413c1cc9ae4ad28d7
```

The 48 `registry_omission` rows are outstanding items that no registry entry names. That class is allowed and never failing.

## T6: the errata and amendments

On 2026-10-27 the owner, eugenelim, approved all ten wordings as drafted, and each was committed unchanged:

- W1: ADR-0119 `Superseded in part:` line and § Errata entry on D4.
- W2: ADR-0134 § Errata entry on D4 and `Applies to`.
- W3: ADR-0110 § Errata entry on D2, D4, D7, and D9.
- W4: RFC-0064 erratum row 12 and history entry.
- W5: RFC-0083 § Errata entry on § 6 and § 8.
- W6: RFC-0106 § Errata entry naming three accepted removals, two intended changes, and the tracker-origin limit.
- W7, W8, W9: amendments on FEAT-0001 (C3), FEAT-0005 (§ Boundary item 7 and the brief terminal move), and FEAT-0007 (§ Opportunity's remember route).
- W10: the delivery brief's slice 7 and slice 9 text, with a dated note on its `Slices confirmed` line.

## Controlled amendment: captured memberships stay registered

On 2026-10-28, during T3, the owner, eugenelim, decided that the `intent-brief-drop` repair does not drop a captured membership (an entry whose `path` lies under `docs/product/captured/`), even when its `kind` is `intent`. That keeps slice 3's RFC-0083 erratum, under which an already registered captured item keeps its entry until the registry is retired. The spec's "Repo-origin intent or brief entry" term is narrowed to say so. This repository holds no such entry: its 95 intent entries all point under `docs/product/intents/` and its 23 brief entries under `docs/product/briefs/`.

On 2026-10-28, after the amendment's review, the owner chose the positive rule: the repair drops a repo-origin entry only when it is `kind = "intent"` with a path under `docs/product/intents/` or `kind = "brief"` with a path under `docs/product/briefs/`, so every captured item keeps its entry, including one the same run moves into `docs/product/captured/`. The owner also approved this sentence, added to RFC-0083's 2026-10-27 slice-7 erratum: "An entry that points at a captured item, including one whose `kind` is `intent`, is not removed; it keeps its entry until the registry is retired."

## T7: the repair on this repository

On 2026-10-28 the owner, eugenelim, saw the whole plan and approved applying it.

- **Plan:** `repair-plan --root .`, `plan_id` `cb07e11d98013c69914733a90f4645baaca2b24a00f2d276c239a5c1518cd1e8`, read against `workspace.toml` SHA-256 `af96f57ad2fd053d1acf260e6c5dd97a785437eb1855b794ff5c1210dab847f0`. It held 118 operations, every one `intent-brief-drop`: 95 for intents and 23 for briefs. Its one manual finding, `type1-untracked` for `spec/plan-evolution-experiments`, predates this slice and is untouched.
- **Apply:** `repair-apply --root . --plan-file <that plan> --yes`, run with `tomlkit` 0.15.1 available, returned `applied: true` with `operations_applied: 118`, every operation applied and none refused, and moved `workspace.toml` from SHA-256 `af96f57a…` to `006e75bf51bbffab648aa6874905a341754cb4f49c01ffa73ed00a8fda8ae3e9`. The pre-repair file is kept under `.context/` for T9's comparison.
- **Entries removed:** 118, 95 intent and 23 brief entries. The diff removes only entry lines and blank lines, and turns one `executing` list into `executing = []`; no comment line is removed.
- **Second plan:** a following `repair-plan` holds no `intent-brief-drop` operation.

`tests/roster/test_workspace_initiative_provenance.py` is deleted with its inventory row. It cross-checked a spec entry's initiative against its brief's `brief_queue` membership, so with no repo-origin brief entry it reaches nothing; initiative membership is a deliberate removal in the retirement record.

On 2026-10-28 the owner approved one rewording in W6, the RFC-0106 erratum: its last sentence now opens "A tracker-origin intent or brief stays registered", so AC-0025's `tracker-origin` literal matches with its case, and the roster check compares literals exactly.

## T8: the retirement record and the inventory

On 2026-10-28 the owner, eugenelim, re-approved the `workspace-retirement` spec and plan as amended by this slice. AC-0028 admits `the child-state check on a brief that never had an entry` and `the cooled child of a brief that never had an entry`, and that plan gains T10. The record gains eight slice-7 Equivalence rows, and its eleven Owner-7 Disposition rows move to slice 9, because tracker-origin entries stay until slice 9. The inventory's 34 other Owner-7 rows move to slice 9 when they still cover the rename or tracker-origin registration, and to slice 8 when only spec registration remains.

## Controlled amendment: deferral anchors resolve to an intent or brief file

On 2026-10-28, after T7, the spec-status lint's invariant (iv) failed once: `docs/specs/m6-role-journey-guides/spec.md` cites `(deferred: role-journey-agent-swarm-section)`, which resolved only through that intent's `[backlog].open` entry, and the repair removed it. The inventory did not list `lint-spec-status.py` as a reader of intent entries. The owner, eugenelim, chose to have the lint also resolve an anchor that names an existing file `docs/product/intents/<anchor>.md` or `docs/product/briefs/<anchor>.md`, through a new criterion and task.

On 2026-10-28, after the amendment's review, the owner narrowed the rule: an intent or brief file resolves a deferral anchor only while its `Status:` is not terminal (an intent not `Fulfilled`, `Withdrawn`, `Cancelled`, or `Superseded`; a brief not `Shipped`, `Withdrawn`, or `Cancelled`), so closing it still invalidates every deferral that cites it.
