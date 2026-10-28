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
