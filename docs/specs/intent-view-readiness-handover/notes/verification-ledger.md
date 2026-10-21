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

## T7 measurements

- **Commit:** `bdfaa5cdf9a04166c2015a254d24ab25c6def8e0`. The working tree carried the T7 edits (docs, SKILL.md, eval case, DESIGN.md, version bump, changelog fragment, the `--readiness` option of `view_bench.py`, the content check, and the scripts and screens in this directory) and the uncommitted lint fix in `test_export_readiness.py`. The controller re-runs the code-dependent measurements at the final code commit.
- **Inputs:** this repository's `status` and `reconcile` outputs, regenerated at the start of T7 with `.claude/skills/workspace-status/scripts/workspace_status.py` and saved under the gitignored `.context/readiness/`.
- **Collected tests at this tree:** `test_export_readiness.py` plus `packs/core/tests/pack`: 1,034 passed, 94.75 s. The new content check (two tests that read `navigate-intents/SKILL.md`) is inside that run.

### AC-0041: scale benchmark with readiness piped in

Command: `view_bench.py --source . --counts 1 10 25 50 --readiness .context/readiness/status.json` (`status.json` SHA-256 `238b42183e039afb184fc12f72d9a8ed8e746b616abe79ac3cde50e017707a10`, 122,156 bytes). Thresholds are the export spec's criterion 0066: at most 104,857,600 bytes, startup at most 3,000 ms, search at most 300 ms, heap at most 1,024 MiB. Every corpus meets every threshold.

| copies | outstanding available | default rows | file bytes | startup ms | search ms | heap MiB | meets all | readiness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | yes | 0 | 740,922 | 19 | 25 | 6 | yes | {"checked": true, "reason": null} |
| 10 | no (resource_limit, limit files) | 0 | 5,141,064 | 64 | 72 | 13 | yes | {"checked": true, "reason": null} |
| 25 | no (resource_limit, limit files) | 0 | 12,635,279 | 167 | 252 | 27 | yes | {"checked": true, "reason": null} |
| 50 | no (resource_limit, limit files) | 0 | 25,125,632 | 218 | 93 | 46 | yes | {"checked": true, "reason": null} |

- **Reading the table:** the saved input names this repository's own paths. A renumbered copy loads none of them, so the page drops every entry, readiness is checked with no rows (`default rows` 0), and the run measures reading, checking and projecting the input plus a page that carries the `readiness` member. `outstanding` is unavailable from 10 copies up (`resource_limit`, files), as in the export's own benchmark. The 25-copy search time (252 ms) was taken on a shared machine with a load average above 40.

### AC-0042: the largest admitted input

`notes/ac0042_generate_max_status.py` (SHA-256 `48a52ada3665df3f26b9329cac2636d56ebe84a9d5547362504937e2a6ae3c24`) writes a base status whose `canonical.blocked` list repeats one blocked entry per `docs/specs/*/spec.md` path (577 paths, 20,107 entries) and pads with spaces to exactly 4,194,304 bytes. Output SHA-256 `6ad5932ad9d1040668596fd9cf5929230290f8f1551654bf5f331f22d31e8057`. Every export returned `ok` with `readiness` `{"checked": true, "reason": null}`.

| Run | Condition | Without `--readiness` (s) | With the 4 MiB input (s) |
| --- | --- | --- | --- |
| A | load average 42 to 94 | 4.27, 3.99, 3.69 | 6.29, 5.06, 4.04, 3.90, 4.57, 4.31, 4.13, 4.14 |
| B | load average about 170 | 11.16, 11.29, 9.70, 6.62, 6.30 | 4.83, 14.03, 5.96, 8.67, 4.56 |

On run A, 7 of 8 piped exports finished within 5 seconds (median 4.14 s) and the export alone, with no readiness, takes 3.7 to 4.3 s of the same time. The one run above 5 s (6.29 s, the first) and every run in B were on a machine whose load average was 42 to 170, where the export without readiness also took up to 11 s. The criterion's 5 s bound is therefore met on a quiet-enough machine and not shown on a loaded one; the controller re-runs it at the final code commit.

### AC-0043: independent counts

`notes/ac0043_independent_count.py` (SHA-256 `5a9c892f20584ca1800d1123ff11c8304159c71670a69268f9898868da528654`) imports nothing from the navigator. It reads the loaded records from an export's data block and judges each status file by the spec's terms. Command: `ac0043_independent_count.py <export.html> status.json reconcile.json`, the export made with `export --readiness - < status.json`.

| File | SHA-256 | Bytes | Export | Independent script |
| --- | --- | --- | --- | --- |
| `status.json` | `238b42183e039afb184fc12f72d9a8ed8e746b616abe79ac3cde50e017707a10` | 122,156 | checked: active 0, ready 0, blocked 30 records, 32 codes, start `none` (`id` null, `held` false, `active_count` 0) | accepted: the same counts and start; the script's own comparison printed `MATCH` |
| `reconcile.json` | `743ea4d97b08ba496a268d23ce80fbdc36ade8b62cbef4c1da108ff8c5e47cb4` | 276,012 | `wrong_schema` (its `mode` is `reconcile`) | refused: `wrong_schema` |

Accepted 1, refused 1. The export's payload held 771 loaded records.

### AC-0044: the real export in headless Chromium

An export of this repository with `status.json` piped in, opened in headless Chromium.

| Question | Rows | Expected | Rail count |
| --- | --- | --- | --- |
| "What can I work on next?" | 30 | `readiness` holds 30 records (0 active, 0 ready, 30 blocked) | 30 |
| "What is broken?" | 32, each with the context "Workspace finding: <code>" | the 32 codes of the 30 blocked records | 32 |

### AC-0045 input: screenshots

Thirty-two PNGs in `screens/`, named `<state>-<width>-<theme>.png`, made by `notes/screenshots.py` (SHA-256 `d4485939b942669327f5d0731f0afbf25a1464030ffebf00eea84ecfe77bc7de`; run `python screenshots.py <repo root> <out dir>`) over real exports of the `mixed` fixture made with `export --readiness -`. Widths 320 (height 900), 1280 (900), 1680 (1000) and 2560 (1400), each in the light and dark theme; each is a true viewport capture.

- `checked-start`: checked; `spec:bravo-spec` carries the start tag, one blocked item shows two codes.
- `checked-ask`: checked; two active items, so no row is tagged and the line says which item count work-loop asks about.
- `check-failed`: the piped input was not JSON; the page shows its failure notice.
- `broken-findings`: "What is broken?" with the workspace findings of the blocked item.

The page prints its generation time, so a re-run changes every hash; these are the hashes of the files in `screens/`.

| SHA-256 | File |
| --- | --- |
| `1a8d94a3799cc7ba90dfd984eca8f843d852e95f5c803c466a139f1f584040db` | `screens/broken-findings-1280-dark.png` |
| `01eb3842239021b2fb0ed94bfbf3aab008710966f73228ea589d628c66ee1f7f` | `screens/broken-findings-1280-light.png` |
| `44b7c7b78ef657e234f1ed3734bdc5ab51a029799494c12875d5b95fcc1f968b` | `screens/broken-findings-1680-dark.png` |
| `6957df211484dbb67d63e288a3caeb03135b2d9d6eba9c8cad44a9c68558d72b` | `screens/broken-findings-1680-light.png` |
| `b411d4c441315869d77041d45bdb9b8c0e92dc68520d0ca6475f3e6af0377611` | `screens/broken-findings-2560-dark.png` |
| `77d9e372c078f667aaff1f5c1b6c97213381418369e25a72ba38c44f63f32828` | `screens/broken-findings-2560-light.png` |
| `3f799ad83905880b746c3e27d6c57f6d26c6baf2e14b1e001bd9abe4c4f144a4` | `screens/broken-findings-320-dark.png` |
| `0ab9b68cd00b5eeaf4bcffc079a98c52cd154dfeca3faa81a20b4b8c0eb9ef7c` | `screens/broken-findings-320-light.png` |
| `7bf1eb5e24ae4401243457f95c5f12ac1517ffd9164c57af457eaa9023500a12` | `screens/check-failed-1280-dark.png` |
| `e445491efcae5f243c28b3073475e44bc2a23c43b734f8df69abb97a8b544c56` | `screens/check-failed-1280-light.png` |
| `c26c6c32198e868348f29597ce7eafdce71849d146b660bc8e7eab30824b195d` | `screens/check-failed-1680-dark.png` |
| `22baa0a8b8477ad25c6ee64193a89e7883ad0219dba994fa7b447e2c06860e37` | `screens/check-failed-1680-light.png` |
| `968a2804093d04597c8a555fe1a34bcbf630e994cbacceef873f67cf97e21da4` | `screens/check-failed-2560-dark.png` |
| `52f9b580445324f6686c7d90edd4ce6facc870777e3a6ddcfb679f9e48c83c89` | `screens/check-failed-2560-light.png` |
| `0e403357a2597fd111ad8a2c15e56e6ccb8d761718d7c6fdef3986f4007cc1bf` | `screens/check-failed-320-dark.png` |
| `d845fa10d76bd5d8aac93174c63eb8c89364a7f4152c88fef64d41140e4ffd4f` | `screens/check-failed-320-light.png` |
| `a69cb5c3071911ae78d3d233a007bef9d960cddad77c8ba630f6620e3a0c7001` | `screens/checked-ask-1280-dark.png` |
| `3f746db072cf8c0e35e2df4f25da5feaf74423c677e81b158190e6ed38c2ce17` | `screens/checked-ask-1280-light.png` |
| `a0b807b59229199c68a116aa21c826a21e78bbf001f48efae8b21f97d1b6dd10` | `screens/checked-ask-1680-dark.png` |
| `24bd75efa6b80de23d46de0f0681d837a803c9dedcc1829626fad69f17aeb8d7` | `screens/checked-ask-1680-light.png` |
| `0e4d2526f9d2e5381cd1a0bde95156b7a7446a8906b04c806f611479d836d450` | `screens/checked-ask-2560-dark.png` |
| `ac5cbf94130029a7116703ee5a41ed09040b973687a7d70d2faaf808bac5d11a` | `screens/checked-ask-2560-light.png` |
| `741a6d8749d3194daf51084a2ec9374295c4726261ce49a610b43df61a123772` | `screens/checked-ask-320-dark.png` |
| `a9ebac9a193b603feee6a1cba0ea3f77b3e9646beb094fd31e61941605bc9cd4` | `screens/checked-ask-320-light.png` |
| `951e9c8531fcc5da2063e2826cab6160b904101b1435e128eea65d686d47fad5` | `screens/checked-start-1280-dark.png` |
| `887fe86b2e36de278bdb93924482bc57efb4e50838f1c19dd6933f9716fb3152` | `screens/checked-start-1280-light.png` |
| `8aaddffa0dd6358e4e982399d36a763e55a7d320c133d606d005929401b5b1f6` | `screens/checked-start-1680-dark.png` |
| `a621b29a229f3f6b672b928e9501b1bb1ee0c1a49c14e8a9ee029ac485dcad27` | `screens/checked-start-1680-light.png` |
| `15a41871006d1e540ff667dd5e910fadb025000b79b806b8bb082d0fc58eceb7` | `screens/checked-start-2560-dark.png` |
| `f0e62d8ef0129750feaf1e0cfd7d290d7044079c52d901c402a8389cbb1e69d6` | `screens/checked-start-2560-light.png` |
| `a688d467fd0c9f8c1f6a1d98a42aa3550f02bdd914585326dac31a55eb96b707` | `screens/checked-start-320-dark.png` |
| `7c51f56111dd440f198e35865df9a2acf3cea4183f2bf124552fc62ea20985a9` | `screens/checked-start-320-light.png` |

The `experience-reviewer` pass over these files and its dispositions are the controller's, and are not recorded here yet.
