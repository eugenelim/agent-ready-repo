# Verification ledger: intent view for session start

## Activation (AC-0046)

- Case added to `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json` (index 42, id `q42`, `should_trigger: true`): "Export the offline intent view so I can pick what to work on this session". The file now holds 47 queries (28 positive, 19 negative); the description is unchanged.
- Procedure as the export ledger's "Activation (AC-0067)" entry: three fresh tool-less processes in an empty directory, `claude -p --safe-mode --disable-slash-commands --tools ""`, prompt on stdin, each seeing the description of every `core` skill plus `navigate-decisions` and the query as a delimited block, one call at a time (retries allowed, none needed). Fidelity is `reported`: a description-match judgement, not the real router.
- Claude Code 2.1.296: the three runs reported `navigate-intents`, `navigate-intents`, `navigate-intents`; 0 errored runs.
- Graded with `agentbundle pack evals run --pack core --mode in-harness --reports <file>` over a reports file holding only `q42`: `[ok ] q42 should_trigger=True trigger_rate=1.00`. The other 46 queries were not re-run (the description is unchanged since the export ledger's 45/45 run), so the command's per-skill total shows them as unmeasured; only the `q42` line is evidence here.
- Result: pass, trigger rate 1.00 (3 of 3).

## Scale (AC-0044)

- Command: `uv run --no-project -q --with playwright --with pytest --with pyyaml python packs/core/tests/skills/navigate-intents/view_bench.py --source .` at `f8531dbd0` (assets unchanged by the bench edit; `view-base.css` `e4fde913a6173633dc4185f8bba4b1aea1aa075c94edeac6edb28d4b25918326`, `view.css` `68abab2fc83928eda6334fb890c739d45c2fb94344ddd7010258348a9e67197f`, `view.js` `90a04b99f7ea2462fe15e1314d33781204f1a1e850c39a47fd1418fb53e2485f`). Chromium headless, macOS, `--enable-precise-memory-info`. Corpora are N renumbered copies of this repository's records, as in the export ledger's AC-0066 entry.
- The bench loads each export with no fragment, so startup measures "What can I work on next?"; search is the median of 5 runs from the first `keydown` of typing `graph` into `#search` to the last `list-updated` mark; "default rows" is `#list a.row-link` after load.
- Thresholds unchanged: file at most 104,857,600 bytes, startup at most 3,000 ms (median of 3 cold loads), search at most 300 ms (median of 5), heap at most 1,024 MiB.

| Copies | `outstanding` available | Default rows | File bytes | Startup ms | Search ms | Heap MiB | Meets every threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | yes | 32 | 655,625 | 9 | 24 | 4 | yes |
| 10 | no (`resource_limit`, limit `files`) | 0 | 4,987,808 | 31 | 263 | 15 | yes |
| 25 | no (`resource_limit`, limit `files`) | 0 | 12,376,648 | 61 | 632 | 29 | no (search) |
| 50 | no (`resource_limit`, limit `files`) | 0 | 24,691,377 | 104 | 1,249 | 54 | no (search) |

- Result: FAIL at 25 and 50 times on the search threshold (632 ms and 1,249 ms against 300 ms). File size, startup and heap pass at every size. The 1 and 10 times corpora meet every threshold. Thresholds were not changed.
- Reading: the search now matches the name or id of every node (intents, briefs and specs; 14,100 specs at 25 times) and re-renders and re-sorts the full result list on each keystroke, so the 5-keystroke span grew from 87 and 177 ms in the export ledger to 632 and 1,249 ms. The default list is empty at 10 times and above because the delivery resolver reaches its file limit, so `outstanding` is unavailable there (as in the export ledger); the default list is therefore exercised at scale only as its empty or unavailable state.

## Real export (AC-0045)

- Command: `python packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py export --root . --destination /tmp/s10 --name real-final.html` at `f8531dbd0`, exit 0, `status: ok`, `/private/tmp/s10/real-final.html`, 635,840 bytes, mode 0600, outside the repository (not committed). Checked by a throwaway Playwright script (`/tmp/s10/real_check.py`, not committed) at 1280 by 900.
- Question counts in the nav: What can I work on next? 32; What is still open under a capability? 14; What has no parent? 105; What is broken? 10 ("Browse all intents" shows no count).
- After choosing "Browse all intents" and expanding every subtree toggle until none was collapsed: the list reads "169 intents", with 169 `a.row-link` rows, 169 distinct `data-node` values, and the set equals the 169 keys of the payload's `records` (each exactly once, none missing, none extra).
- Result: pass.
