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

## T2: the grammar and the closed state

Implemented in `f7d99bd90` (red), `d5617b253` (engine), `f8e7a36ce` (core 3.1.25), and `e4c002566` (packaged and projected copies). The three frozen fixtures are byte-identical to `dd4f7038c`.

AC-0005's pins were recorded once from the engine at `dd4f7038c`:

- A missing captured-item path with no receipt gives `missing_dependency` on the path.
- A missing path with a completion receipt gives `invalid_dependency` on the waiter and `missing_dependency` on the path, because the header reader refuses a completion receipt on a captured-item reference. No receipt settles a captured-item dependency at either commit.
- A cooled unregistered file gives `invalid_dependency` on the waiter, because its kind is never read.

`test_workspace_status_engine_autonomous.py::test_t2_positive_dispatch_and_reconciliation_surface` plants a registered `Closed` design record. It gains `Resolution: fixed`, as the equivalence cases do, and keeps `impossible_transition`.

## T5: the errata entries

The owner, eugenelim, approved the wording of all four entries on 2026-10-27 before they were committed: ADR-0053 § Errata, RFC-0063 § Errata, RFC-0083 § Errata, and RFC-0106 § Errata. Each is committed exactly as approved. `lint-adr-shape.py docs/adr` and both record-index checks pass.
