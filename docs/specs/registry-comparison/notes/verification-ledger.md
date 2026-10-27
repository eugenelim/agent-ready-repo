# Verification ledger: registry comparison

Execution observations for `docs/specs/registry-comparison/`. The spec and plan stay pinned; this file records what the build found.

## T1 — the comparison tool

- **Bytecode check scope.** The AC-0014 prefix check ignores cache files whose mirrored path contains `/site-packages/`. The local gate venv lives at `.context/venv`, under the repository root, and its `_distutils_hack` `.pth` startup hook caches a file before any tool code runs. That write is the interpreter's, not the tool's. The control run that loads `closure_terminality.py` without the flag is still flagged on both the resolved and as-invoked roots.
- **Non-UTF-8 typed file.** AC-0010's non-UTF-8 case is tested through `classify`. A non-UTF-8 spec in a fixture tree makes the navigator itself refuse (`delivery_incomplete`), so the CLI reaches AC-0019's navigator refusal first.
- **Read bound.** A typed-file target is read with a 64 MiB cap, and a larger one is `unclassified`. A non-typed target's content is never read: the confined reader runs with a zero cap, so every confinement and regular-file check runs, and the bound refusal that follows marks it `captured_item` at any size.
- **Exact spelling.** Every part of a target must equal a real directory entry name exactly, so a case or normalization alias of a file on an insensitive filesystem counts as missing and is `unclassified` (owner decision, 2026-10-27, from the post-gates security review).
- **Refusal input names.** `workspace.toml`, `navigator`, `graph`, `captured-items`, `arguments`, and `internal`.

## T2 — records and wiring

- **Registry placement.** T2's Tests name `ini-002`'s `work` collection. The slice siblings live under `ini-010` (`workspace-retirement` in `active`, `priority-header-field` in `shipped`), so this spec's entry is in `ini-010.work.active`. `lint-brief-coverage.py --root .` exits 0 and lists `registry-comparison: Implementing` under the brief, which is the check T2 names. `workspace_status.py --root .` places the spec in `canonical.active` with no finding.
- **Checks.** `tests/roster/test_workspace_retirement_inventory.py`: 120 passed. `tools/test-lint-ci-parity.py`: 218 cases passed. `tools/lint-ci-parity.py`: exit 0 (under the gate venv; bare `python3` lacks PyYAML).

## T3 — run over this repository

Command: `python3 tools/compare-registry.py --root .` (run once, at HEAD, clean tree)

Output:

```
registry comparison: pass
captured_item 0
legacy_shape 0
registry_stale 0
registry_closed_stale 0
registry_omission 48
registry_live_only 0
result_terminal 0
unclassified 0
commit 684215378020e0867a44dd196a556e2b2eb3eef0
workspace.toml sha256 5157ac4fa09c7e6df495ddbcdc2e23eca37d44afab0237edfb0ca6699a877f3b
```

- Exit code: 0 (stderr empty)
- Commit: 684215378020e0867a44dd196a556e2b2eb3eef0
- Merge base with origin/main: 1ecd9b5db0b48de578ec5212fecf352b3fdae919
- No row failed: result is pass; the 48 registry_omission rows are reported, not failing.
- Supporting observation: the ignored and untracked file listing was identical before and after the run (not the AC-0014 proof, which is T1's test).
