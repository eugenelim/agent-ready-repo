# Verification ledger: specs stop being registered

## Registry comparison before the stop (AC-0035)

Run 2026-10-29 on this branch at commit `62ed2dddfbb369d2d5b086facac4b1f0513b6ee6`, whose merge base with `origin/main` is `c8d1d817a536e72b19a0f5733752c50ac1e3d77b`, before any writer instruction, router branch, repair step, or registry entry changed:

```
python3 tools/compare-registry.py --root .
```

Exit code: `0`.

```
registry comparison: pass
captured_item 0
legacy_shape 0
registry_stale 0
registry_closed_stale 0
registry_omission 164
registry_live_only 0
result_terminal 0
unclassified 0
commit 62ed2dddfbb369d2d5b086facac4b1f0513b6ee6
workspace.toml sha256 cd2bb92c4a952ee5acbddfc9f05fbaae79179ad474529238144732cc32644ddc
```
