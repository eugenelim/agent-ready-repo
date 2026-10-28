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
