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

## T7 measurements (superseded by the final code commit section below)

Superseded: these numbers were taken at `bdfaa5cdf` before the review fixes. The section "Final code commit `fd4d89546`" holds the current ones; these stay as the earlier record.

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

### AC-0045 input: screenshots (superseded)

The 32 hashes below were replaced when the screens were regenerated at `fd4d89546`; the current list is in the final section.

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

## Final code commit `fd4d89546`

All measurements below ran at `fd4d895469b87990bc50d55cea688a8bc3cc98aa` (HEAD). The only working-tree changes were the regenerated screens and this ledger. They ran on 21 October 2026, between 18:49 and 19:46 US Central, on a shared machine; the load average (`uptime`, 1, 5 and 15 minutes) is stated beside each timing. The same `status.json` and `reconcile.json` bytes as at `bdfaa5cdf` came out.

### Inputs

| File | SHA-256 | Bytes | Exit |
| --- | --- | --- | --- |
| `.context/readiness/status.json` | `238b42183e039afb184fc12f72d9a8ed8e746b616abe79ac3cde50e017707a10` | 122,156 | 0 |
| `.context/readiness/reconcile.json` | `743ea4d97b08ba496a268d23ce80fbdc36ade8b62cbef4c1da108ff8c5e47cb4` | 276,012 | 0 |

Made with `workspace_status.py status --root .` and `reconcile --root .`.

### AC-0043: independent counts (exit 0)

`ac0043_independent_count.py` (SHA-256 `5a9c892f20584ca1800d1123ff11c8304159c71670a69268f9898868da528654`) over a real export (`export --root . --readiness -`, exit 0, 727,234 bytes, `readiness` `{"checked": true, "reason": null}`), `status.json` and `reconcile.json`:

| File | Export's projection | Independent script |
| --- | --- | --- |
| `status.json` | active 0, ready 0, blocked 30 records, 32 codes, start `none` (`id` null, `held` false, `active_count` 0) | accepted: the same counts and start; the script printed `MATCH` |
| `reconcile.json` | n/a | refused: `wrong_schema` |

Accepted 1, refused 1; 771 loaded records. The repository now has no ready item (this spec is no longer ready), where the T1 run found one.

### AC-0044: the real export in headless Chromium (exit 0)

Export of this repository with `status.json` piped in, opened in headless Chromium (no page errors).

| Question | Rows | Expected |
| --- | --- | --- |
| "What can I work on next?" | 30 (30 carry the Blocked mark) | the projection's 30 records (0 active, 0 ready, 30 blocked) |
| "What is broken?" | 32 rows with the context "Workspace finding: <code>" | the projection's 32 codes; the sorted codes match |

The "What is broken?" lead reads: "Pointers that did not resolve, parent or dependency loops made of resolved pointers, problems the delivery resolver found, and findings workspace-status reported."

### AC-0042: the largest admitted input (every run exit 0)

`ac0042_generate_max_status.py` (SHA-256 `98389e847dd50ddbc063f149324cdfb8a68283f79c1c7670c569801be2e16bd1`; it differs from the `48a52ada...` recorded earlier because `--distinct-codes` was added) wrote two inputs of exactly 4,194,304 bytes:

| Mode | SHA-256 | Entries | Distinct spec paths |
| --- | --- | --- | --- |
| default | `6ad5932ad9d1040668596fd9cf5929230290f8f1551654bf5f331f22d31e8057` | 20,107 | 577 |
| `--distinct-codes` | `0b913a96bd5d3a7879f1a0cc5681fcbe1d7deb131654966204c07895f9280bae` | 21,131 | 577 |

Every export returned `ok` with `readiness` `{"checked": true, "reason": null}`.

| Run | Seconds | Within 5 s | Load average |
| --- | --- | --- | --- |
| default 1 | 5.28 | no | 40.87, 45.60, 91.33 |
| default 2 | 4.44 | yes | 39.92, 45.32, 90.96 |
| default 3 | 4.73 | yes | 40.01, 45.25, 90.67 |
| distinct 1 | 5.38 | no | 38.42, 44.73, 89.96 |
| distinct 2 | 3.65 | yes | 36.70, 44.27, 89.53 |
| distinct 3 | 3.66 | yes | 35.21, 43.83, 89.11 |
| no-flag baseline 1 | 3.79 | yes | 33.43, 43.32, 88.66 |
| no-flag baseline 2 | 3.52 | yes | 33.43, 43.32, 88.66 |
| no-flag baseline 3 | 3.94 | yes | 31.71, 42.80, 88.21 |

Four of six piped runs finished within 5 s. Two missed the bound, each its mode's first run (5.28 s and 5.38 s), at a load average of 38 to 41. The no-flag export alone took 3.5 to 3.9 s at a load of 32 to 33, so the 5 s bound is met in 4 of 6 runs on this loaded machine and is not shown for the first run of each mode. The bound holds for all six runs only when the first-run cost (about 0.6 to 1.7 s above the median of the others) is excluded; that exclusion is a reading of the data, not a claim of the criterion.

### AC-0045 input: screenshots (exit 0)

Thirty-two PNGs in `screens/`, regenerated by `notes/screenshots.py` (SHA-256 `d4485939b942669327f5d0731f0afbf25a1464030ffebf00eea84ecfe77bc7de`; `python screenshots.py <repo root> <out dir>`) at `fd4d89546`. The view changed since the earlier set: blocked-row codes are `.value` elements and the "What is broken?" lead names workspace findings. The states and widths are those described in the superseded entry above. These hashes replace that list.

| SHA-256 | File |
| --- | --- |
| `8651e0bf39bf57ea632707463b3a66901c89d0d634cb0b94c938b0fe09f33798` | `screens/broken-findings-1280-dark.png` |
| `ab086698564fedff84f38f77af1d274e5ad8ac1b40c218f139ccff8f5be2b194` | `screens/broken-findings-1280-light.png` |
| `3cef726a6c1bda60fb9c120c03d4662ec0734333e060c14b597f5f3234a27ee6` | `screens/broken-findings-1680-dark.png` |
| `b1ca3a6e84e9c5abdb90a0cf148024d24f1880358165dc598a47f555ef20a74d` | `screens/broken-findings-1680-light.png` |
| `b8664b6930d4fba3461df2fffee79e52a0b3983def273f1fdf15d9eb8d6a5408` | `screens/broken-findings-2560-dark.png` |
| `da5b9c67c61ab2072bb0de138eb66d5f139ff05c0e9f05f5551617ecfbe6a324` | `screens/broken-findings-2560-light.png` |
| `38d92a7085fe64924ed777c914931752d59c02d1630074f1e89d230ec4416164` | `screens/broken-findings-320-dark.png` |
| `68b2cf7ee97ce036720615563e69969c4146b29bdd4808b135fd221856b8abd0` | `screens/broken-findings-320-light.png` |
| `e799f2a132ac933e0be6cda06fa8210891ce43631f3cf94ca9b78d8b6fdac4d0` | `screens/check-failed-1280-dark.png` |
| `b894b92ef9ab6c90e6681051d9c449860a678880fc4234e662558ec09ae7c257` | `screens/check-failed-1280-light.png` |
| `a34f752cdb6175bf520f538f553c0462a4664608c2f0797d0bb35187ac4a039b` | `screens/check-failed-1680-dark.png` |
| `621929f40000c439060efc5fb5e304de27529e1467f9e5cd8183d26a45fff9f2` | `screens/check-failed-1680-light.png` |
| `700a86f123f79ea7a8f63bf67a26c8731f62faed91f6fd4fc89613b9a0f1a30e` | `screens/check-failed-2560-dark.png` |
| `a24c73e40815abcb981d1dcc7b3d9658ab909cffb010b7f4e0dc446ea5854a7c` | `screens/check-failed-2560-light.png` |
| `46a04f474605f720233a2aeab27f2443efba7cc0f9ab87c760759cd8816f9363` | `screens/check-failed-320-dark.png` |
| `051d3c5275b5658138479d0003d07d9e0f404a318f2b76c039fb7f3927891e93` | `screens/check-failed-320-light.png` |
| `51403fd84a3b03f7c0313e5db76c75f84b5d1d8dadd1d8cb8917759f47dadd86` | `screens/checked-ask-1280-dark.png` |
| `105110f070276903d9eefe75d81735d08e9faa5dc8ae46a61dc7024a04ef6507` | `screens/checked-ask-1280-light.png` |
| `d5e1da46bd666767582ae243902032707be8cc7b6e48235b71b73495189abc88` | `screens/checked-ask-1680-dark.png` |
| `74346cf291a533fb2f413ee160ce5dbbd1e80f746ac0b5cd2f8995060117caad` | `screens/checked-ask-1680-light.png` |
| `f11112e8202bb047ee35ab2833d929cfd9e55288965a6e31e78498863464ba88` | `screens/checked-ask-2560-dark.png` |
| `ee1c9f78d04bed8ce7d3a61bbff155c1eb45c203a7de622e3b42c27173dfac06` | `screens/checked-ask-2560-light.png` |
| `818b492003e451de33f1057252f617f3f6bb75b126ebad3f70125495496701c6` | `screens/checked-ask-320-dark.png` |
| `ee7998ef298ac3b5d30b20cad5041bfa0c39ccf11191526441c331b127248f47` | `screens/checked-ask-320-light.png` |
| `97721934bb5ae4abccd1d6064bf0050ab10fd18fce8f0f2f2c6c8e81b3e1b9ac` | `screens/checked-start-1280-dark.png` |
| `8377a5f024adcaaa53d968bbfa97d1c32ff9a4aa94bb2f4d661499c9d5f2803d` | `screens/checked-start-1280-light.png` |
| `3618ea4fe13901c7676e9368a02eebf4d80f70e466fc33e03fd9d5b48093c1b7` | `screens/checked-start-1680-dark.png` |
| `c155c5f4f724ec16f3f07fe706111414cdf9d1d70728491336d8da53a634e2c3` | `screens/checked-start-1680-light.png` |
| `6c91b21c4dfd2fd0bd1680027136860325b763af71652848b001a1d893194867` | `screens/checked-start-2560-dark.png` |
| `e027a6366f889a5d1a34602a81776c959421088e4addb559bd4d1c81a59ba097` | `screens/checked-start-2560-light.png` |
| `183d809e098617f254708e61079422c9e2e47dd712bda0ecfeab207c6798cc14` | `screens/checked-start-320-dark.png` |
| `8c0c25f017486d2478f3e12cdd9b626b2f54f113c64702df5476c1e5e3bdb633` | `screens/checked-start-320-light.png` |

### AC-0041: scale benchmark with readiness piped in (exit 0)

Command: `view_bench.py --source . --counts 1 10 25 50 --readiness .context/readiness/status.json`, with the `status.json` above, started 18:51 and finished before 19:46; it took about 55 minutes. Load average at the start: 25.63, 40.01, 85.36; from 19:02 to 19:46 it ranged from 149 to 245 (1-minute readings 149, 204, 188, 175). Thresholds are the export spec's AC-0066: at most 104,857,600 bytes, startup at most 3,000 ms, search at most 300 ms, heap at most 1,024 MiB.

| copies | outstanding available | default rows | file bytes | startup ms | search ms | heap MiB | meets all | readiness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | yes | 0 | 741,657 | 24 | 26 | 6 | yes | {"checked": true, "reason": null} |
| 10 | no (resource_limit, limit files) | 0 | 5,141,799 | 76 | 96 | 14 | yes | {"checked": true, "reason": null} |
| 25 | no (resource_limit, limit files) | 0 | 12,636,014 | 186 | 107 | 21 | yes | {"checked": true, "reason": null} |
| 50 | no (resource_limit, limit files) | 0 | 25,126,367 | 207 | 108 | 49 | yes | {"checked": true, "reason": null} |

Every corpus meets every threshold; all four are named as meeting them. The saved input names this repository's own paths, so a renumbered copy loads none of them: readiness is checked with no rows (`default rows` 0), and the run measures reading, checking and projecting the input plus a page that carries the `readiness` member. `outstanding` is unavailable from 10 copies up, as in the export's own benchmark.

### Gates at this commit

Measured by the controller on the identical tree just before committing (not re-run here):

- Lint and mypy (`make lint-ruff lint-mypy`): clean.
- Collected navigate-intents and core pack suites: 1,557 passed, 6 skipped, 8 min 54 s.
- `view_browser_checks.py`: 439 passed, 0 skipped, 15 min 7 s.

### Reviews

Report paths are under `.context/reviews/116dcdd2-c25d-41bc-81f5-09e52d745a7a/`, named `<round>-<phase>-<reviewer>-raw.md` and `-adjudication.md`.

| Review | Outcome after adjudication |
| --- | --- |
| Pre-execute adversarial and security rounds (the drift amendment, three amendment rounds and the `view.css` amendment; files `1-` to `7-pre-execute-*`) | all clean |
| Post-gates round 1, adversarial (`1-post-gates-adversarial-reviewer-*`) | 3 Concerns sustained and fixed |
| Post-gates round 1, security (`1-post-gates-security-reviewer-*`) | 1 Concern sustained and fixed |
| Post-gates round 1, quality (`1-post-gates-quality-engineer-*`) | 1 Concern and 3 Nits sustained and fixed; 4 refuted |
| Post-gates round 1, frontend (`1-post-gates-frontend-reviewer-raw.md`) | clean |
| Post-gates round 1, experience (`1-post-gates-experience-reviewer-*`) | no Blocker or Major; 4 Minors sustained (the code typeface and the broken-list lead fixed; row wrap and start-tag prominence left as considered, by owner decision); 5 refuted |
| Post-gates round 2, adversarial (`2-post-gates-adversarial-reviewer-raw.md`) | clean |
| Post-gates round 2, security (`2-post-gates-security-reviewer-*`) | clean after adjudication |
| Post-gates round 2, quality (`2-post-gates-quality-engineer-raw.md`) | 1 Nit deferred: no test for the readiness-module refusal message |

AC-0045, experience re-review of the 32 screens regenerated at `fd4d89546` (hashes above): verdict "SHIP IT", no Blocker, Major or Minor (`2-post-gates-experience-reviewer-raw.md`). One Nit, deferred and not acted on: a short "What is broken?" list card keeps the rail's height at 1680 and 2560 px, leaving blank space under its last row. With round 1's Majors refuted and its Minors resolved as above, no Major or Blocker finding remains after adjudication.
