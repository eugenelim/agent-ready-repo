# Verification ledger: intent view readiness bridge

Each entry names the commit it ran against, what ran, and the result.

## T1 real-input corpus

- **Commit:** `5acc664400c7938a3177e868f8c0ef4850cac218` (main at the task's start). The working tree held uncommitted changes when this ran: the new `intent_readiness.py`, `test_export_readiness.py` and this file, plus the uncommitted spec and plan edits.
- **Inputs:** this repository's `status` and `reconcile` outputs, and the output of `workspace_status.py status` over a copy of the `mixed` fixture with a hostile `workspace.toml` (a `[backlog].open` intent entry, an `["ini-001".work]` queue holding a spec and an entry whose path carries `<img src=x onerror=alert(1)>`, and an active spec; summaries, `ref` and names carry `</script><script>`, `<img src=x onerror=alert(1)>`, `javascript:`, `"><svg onload=alert(1)>`, U+2028 and a bidirectional control). Saved under the gitignored `.context/readiness/`. Node ids for the repository inputs come from this repository's payload (769 nodes); for the probe, from the `mixed` copy (15 nodes).
- **Method:** `intent_readiness.check` then `project` over each file's bytes. "Raw findings" counts the findings in `canonical.blocked` entries as `workspace-status` emitted them; "projected codes" counts the findings in `readiness.blocked` after the per-record repeat removal of the spec's criterion on repeated paths and codes.

| Input | SHA-256 | Bytes | Result | Active | Ready | Blocked records | Raw findings | Projected codes | Start rule (id) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `status.json` | `aa3ae1b8897567a4dced33b0a646e9fd1c50a7ded8f1e9f99c0fd0f3276ea451` | 123,374 | checked | 0 | 1 (this spec) | 31 | 43 | 32 | `start` (`spec:intent-view-readiness-handover`, held `false`) |
| `reconcile.json` | `fa207fde22d3dc10ee16fcb4737ccabed2f718e81131ecb8ab30037114fe85c0` | 277,506 | refused `wrong_schema` | n/a | n/a | n/a | n/a | n/a | n/a |
| `hostile-probe.json` | `b5901e83cc807a0e2041b18c12c6a6036a3e36dd575bf7bbe7f29cc8dd7b4b86` | 5,463 | checked | 0 | 0 | 3 | 5 | 5 | `none` (`null`) |

- **Difference from the plan's orientation figure:** the plan's "43 codes" is the raw finding count. Several `status` records carry the same code more than once (one `unsatisfied_dependency` per prerequisite), and the projection removes those repeats within a record, so it holds 32 codes. This does not contradict a criterion: repeats removed is the stated rule for a record's codes.
- **Reconcile:** refused as `wrong_schema` because its `mode` is `reconcile`.
