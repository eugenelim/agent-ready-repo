# Verification ledger: captured items stop being registered

## T1: the registry comparison before the stop

Run on 2026-10-27 on this spec's branch, before any writer instruction changed, as FEAT-0034's validation hook requires.

- **Command:** `python3 tools/compare-registry.py --root .`
- **Commit:** `d3f984349ca1910843622fd6fde99c56f8f2f47c`
- **Merge base with `origin/main`:** `dd4f7038cd60c649621d736358af7b1e87cd1961`
- **Exit code:** `0`, so no row is failing and captured-item registration may stop.

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
commit d3f984349ca1910843622fd6fde99c56f8f2f47c
workspace.toml sha256 b16a4b52934a492a2b05caf191b942890f82d375815539aa4d758c3790a428a4
```

The 48 `registry_omission` rows are outstanding items that no registry entry names. That class is allowed and never failing.
