# Verification ledger: intent view for session start

## Activation (AC-0046)

- Case added to `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json` (index 42, id `q42`, `should_trigger: true`): "Export the offline intent view so I can pick what to work on this session". The file now holds 47 queries (28 positive, 19 negative); the description is unchanged.
- Procedure as the export ledger's "Activation (AC-0067)" entry: three fresh tool-less processes in an empty directory, `claude -p --safe-mode --disable-slash-commands --tools ""`, prompt on stdin, each seeing the description of every `core` skill plus `navigate-decisions` and the query as a delimited block, one call at a time (retries allowed, none needed). Fidelity is `reported`: a description-match judgement, not the real router.
- Claude Code 2.1.296: the three runs reported `navigate-intents`, `navigate-intents`, `navigate-intents`; 0 errored runs.
- Graded with `agentbundle pack evals run --pack core --mode in-harness --reports <file>` over a reports file holding only `q42`: `[ok ] q42 should_trigger=True trigger_rate=1.00`. The other 46 queries were not re-run (the description is unchanged since the export ledger's 45/45 run), so the command's per-skill total shows them as unmeasured; only the `q42` line is evidence here.
- Result: pass, trigger rate 1.00 (3 of 3).

## Scale (AC-0044)

- Command: `uv run --no-project -q --with playwright --with pytest --with pyyaml python packs/core/tests/skills/navigate-intents/view_bench.py --source . --counts 1 10 25 50` at `357de5732` (`view.js` `c44a8920ecf9e15cb618232a8377c450973bab3741e942d94531754bb1abce77`; `view-base.css` and `view.css` unchanged from `f8531dbd0`). Chromium headless, macOS. Corpora are N renumbered copies of this repository's records, as in the export ledger's scale entry.
- The bench loads each export with no fragment, so startup measures "What can I work on next?"; search is the median of 5 runs from the first `keydown` of typing `graph` into `#search` to the `list-updated` mark; "default rows" is `#list a.row-link` after load.
- Thresholds unchanged: file at most 104,857,600 bytes, startup at most 3,000 ms (median of 3 cold loads), search at most 300 ms (median of 5), heap at most 1,024 MiB.

| Copies | `outstanding` available | Default rows | File bytes | Startup ms | Search ms | Heap MiB | Meets every threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | yes | 32 | 656,863 | 10 | 11 | 5 | yes |
| 10 | no (`resource_limit`, limit `files`) | 0 | 4,989,046 | 30 | 43 | 13 | yes |
| 25 | no (`resource_limit`, limit `files`) | 0 | 12,377,886 | 70 | 44 | 28 | yes |
| 50 | no (`resource_limit`, limit `files`) | 0 | 24,692,615 | 105 | 45 | 46 | yes |

- Result: pass at every size.
- The first run at `f8531dbd0` failed search at 25 and 50 times (632 and 1,249 ms), because each keystroke re-sorted every node and rendered every matching row. `357de5732` sorts the search index once, caches each row's name and context, and renders a long list's first 150 rows at once and the rest in later batches.
- The default list is empty at 10 times and above because the delivery resolver reaches its file limit, so `outstanding` is unavailable there; at scale the default list is exercised only in that state. The largest corpus with `outstanding` available is 1 time, with 32 default rows.

## Real export (AC-0045)

- Command: `uv run --no-project -q --with playwright --with pyyaml python /tmp/s10/real_check2.py <repo root>` (the earlier `real_check.py` with the output name changed to `real-final2.html`, not committed), at `abf8d30bb`. The export ran `python packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py export --root . --destination /tmp/s10 --name real-final2.html`: exit 0, `status: ok`, `/private/tmp/s10/real-final2.html`, 669,590 bytes, mode 0600, outside the repository (not committed). Checked at 1280 by 900.
- Question counts in the nav: What can I work on next? 32; What is still open under a capability? 14; What has no parent? 105; What is broken? 10 ("Browse all intents" shows no count).
- After choosing "Browse all intents" and expanding every subtree toggle until none was collapsed: the list reads "169 intents", with 169 `a.row-link` rows, 169 distinct `data-node` values, and the set equals the 169 keys of the payload's `records` (each exactly once, none missing, none extra).
- Result: pass.

## Screenshots (AC-0047)

- Command: `uv run --no-project -q --with playwright --with pyyaml python /tmp/s10/shots_final.py <repo root> docs/specs/intent-view-session-start/notes/screens` (script outside the repository) at `abf8d30bb`. It exports this repository to `/tmp/s10/shots-final.html`, then for each width opens it with no fragment in a fresh context (`viewport` width by 900, `color_scheme` light or dark), waits for the `view-ready` performance mark, moves the mouse to (0, 0), waits 300 ms and saves the first screen.
- Eight files, one per width and theme:

| Width | Theme | File | SHA-256 |
| --- | --- | --- | --- |
| 320 | light | `screens/320-light.png` | `19172f39208397f9ded23ba9c05f9ede99d1c0afde114978b324c27b9458986e` |
| 320 | dark | `screens/320-dark.png` | `23b3f41bc909cbb2146c4a9ab953e688265977d3097c50c296cec33e807ea64a` |
| 1280 | light | `screens/1280-light.png` | `4077dc12c101e0f7c3bd3f5e6ff56ec7d9160e4c6b664ead829b8631abce5571` |
| 1280 | dark | `screens/1280-dark.png` | `493742a63b57c1ba0327a085f6834e2db8769b0236d33c1181d79f79d6584c45` |
| 1680 | light | `screens/1680-light.png` | `0b2893bfb78f625d290e483af8554b553c457fd3d077626fb38561053b299df2` |
| 1680 | dark | `screens/1680-dark.png` | `456209836e60fe092879511c239cf5254a7c92dc9e45e2f8cbe1cc35a4a11fbf` |
| 2560 | light | `screens/2560-light.png` | `83bff6e19dc9b310f3868a02567b039ea56b0955035b87636aad06c1193ed0bd` |
| 2560 | dark | `screens/2560-dark.png` | `56ca58b2042827a99bbe0abb343e5bfc4b53894ac7601e43b94ded2407df0031` |

- Looked at 320 light, 1280 dark, 1680 light and 2560 light. Each shows the default "What can I work on next?" list with its four counts and no clipped text. No defect seen beyond the deferred Minor items (rail labels wrap at 1680 and 2560).

## Final browser suite

- Commit `abf8d30bb`. Asset digests under `packs/core/.apm/skills/navigate-intents/scripts/view_assets/`:
  - `view.js` `6895f8028da02e4a5ba2480049cebdb54d22986dd12675018161af0e6aa8121a`
  - `view.css` `56c493387b5c57124720953044d8b2b129821f205d4370927011d2a7c54ed918`
  - `view-base.css` `52c618bea9b58edc484f5dde5945b3ccf1b75343b22f67f0e99fc93b1cb596c1`
- `uv run --no-project -q --with pytest --with playwright --with pyyaml python -m pytest packs/core/tests/skills/navigate-intents/view_browser_checks.py -q -rs -p no:cacheprovider`: 91 passed, none skipped, 29.62 s.
- `PYTHONPATH=packages/agentbundle:packages/credbroker uv run --no-project -q --with pytest --with pyyaml python -m pytest packs/core/tests/skills/navigate-intents/test_export_html.py -q -p no:cacheprovider`: 8 passed, none skipped, 0.66 s.

## Experience review (AC-0048)

Reports are under `.context/reviews/63e509d4-5537-4666-b9af-ae46a254bfa1/` (`5-experience-raw.md`, `6-experience-raw.md`, `7-experience-raw.md`).

- Round 1: SHIP WITH CHANGES, 5 Major (adjudicated advisory). All fixed.
- Round 2: SHIP WITH CHANGES, 4 Major from the clipping repair. All fixed.
- Round 3 at `d2b98cf36`: SHIP IT, no Blocker or Major. 4 Minor and 3 Nit deferred: parent name styling, "17 open" line break, trail order cue (since added in `657908ff5`), rail label wrap, hover in capture, wide-name gap.

## Reviews

- Adversarial: round 1 found 3 Blockers (including focus); round 2 found 1 Blocker (clipping); round 3 found 1 Concern; round 4 Clean.
- Security: round 1 Clean; round 2 Clean.
- Frontend stand-in: round 1 found 1 Blocker and 5 Concerns; round 2 found 1 Blocker; round 3 found 2 Nits, fixed.
- Every sustained finding is fixed.

## Owner check (AC-0049)

Pending.
