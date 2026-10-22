# Verification ledger: intent view record owners

## Base commit

- Base commit: `6e0456e83`, `origin/main` after PR #1595 merged, on 2026-10-21. The spec and plan were approved at `5a8a691e1` and rebased onto this base unchanged.

## T1

- Implemented by an `implementer` subagent, commit `7de8b4a7a`. `fixtures/owners/` holds 13 records: 10 intents, 1 brief and 2 specs. Its README hand-states 7 tables: 13 owner rows, 7 options, 15 owner-selector values, 5 non-owner selectors, 18 Browse rows, 6 roadmap rows and the scoping row. It covers every AC-0001 owner form, plus `Team  Two` and `TEAM TWO` as one owner key and `Édith Team` as a non-ASCII value.
- Red proof: `test_owners_cross_check_fails_for_an_unlisted_record` adds an unlisted record to a `tmp_path` copy and asserts that the cross-check fails. It then removes a listed record and asserts the failure again.
- Gates:
  - `test_derivation_contract.py`: 62 passed.
  - `lint-pack-test-boundary.py`: ok.
  - `make lint-ruff lint-mypy`: clean.
  - navigate-intents suite without the browser file: 529 passed, 4 skipped.

## T2

- Implemented by an `implementer` subagent, with one controller repair, in commit `dde88be7f`.
- Stub red before any production edit: `test_every_node_carries_owner_ac0001` failed with `assert False`.
- Anchor moved: `test_export_payload.py`'s golden digests now hash the payload with every `owner` member stripped. The recorded goldens therefore still prove that nothing else changed.
- Controller repair: the AC-0002 and AC-0003 comparisons first stripped every key named `root`, because the two corpora sat at different paths. That strip could hide a real `root` difference. Both comparisons now run before and after removing the `Owner:` lines from one `tmp_path` copy at one path, and strip only `owner` and `generated_at`, as AC-0002 states.
- The two `intent_graph.py` copies are byte-identical (`cmp`).
- Gates:
  - navigate-intents suite (without the browser file), `test_intent_delivery_relations_copies.py` and the close-work suite: 968 passed, 4 skipped in 148s.
  - `make lint-ruff lint-mypy`: clean.
  - `lint-pack-test-boundary.py`: ok.

## T3

- Implemented by an `implementer` subagent.
  - The new part `view_src/owners.js` is 78 lines, listed after `rows.js`. It holds the owner key, the options, the label, the match, the cell, the control and the route values `k:<key>` and `none`.
  - `rowLink` and `capabilityRow` append `span.c-owner`, and "Record details" gains "Owner".
  - Rail links now re-apply `questionHash(key, owner)` on each route, so a question switch keeps the owner choice.
  - No list is narrowed yet; T4 and T5 do that.
  - Named skip: the `frontend-engineering` craft file was not read. The repository's own view rules were applied instead.
- Shipped assertions moved, each as the spec's amendment table states:
  - the row shape now ends `c-owner`, for session-start 0009;
  - the roadmap row parts now end `c-owner`, for tree-and-roadmap 0012;
  - the "Record details" facts now end "Owner", for session-start 0019.
- Console check: an `owners` export opens in headless Chromium with no console message and no page error. Its 7 options match the README.
- Gates, all passing:
  - Full `view_browser_checks.py`: 329 passed in 300s, none skipped. The controller re-ran the whole suite after the moved assertions.
  - The navigate-intents suite without the browser file: 541 passed, 4 skipped.
  - Clean: `make lint-ruff lint-mypy`, `lint-pack-test-boundary.py` and `check_view_base_parity.py`.

## Rebase onto the readiness bridge

- On 2026-10-22 the branch was rebased onto `origin/main` at `d291eefe1`, which holds the readiness bridge (#1602) and core 3.1.15. Three conflicts were resolved:
  - `workspace.toml`: the readiness bridge had moved to `shipped`, so only this spec stays in the queue.
  - The golden-payload test now strips both `readiness` and `owner` before hashing.
  - `view.css` and `view_browser_checks.py`: both sides had added rules and tests, and all of them were kept.
- Gates after the rebase:
  - Full `view_browser_checks.py`: 448 passed in 484s, none skipped.
  - The navigate-intents suite without the browser file, plus the copies and close-work suites, under `-n auto`: 1542 passed, 6 skipped, 17 failed, 2 errors. Every failure was a Git-dependent export test, refused with `invalid_destination` ("cannot confirm the work trees…") while 10 workers ran Git at once.
  - The same failing files, run serially: `test_export_payload.py`, `test_export_publication.py`, `test_export_source_links.py` and `test_export_html.py` gave 172 passed and 2 skipped; `test_export_readiness.py` gave 595 passed. The failures come from parallel load on Git, not from this change.

## Owner-directed fixes to the readiness bridge's deferred Nits

- Added at the owner's request on 2026-10-22. These are outside this spec's criteria.
- **Readiness-module refusal message.** `test_an_unloadable_readiness_module_refuses_and_writes_nothing` in `test_export_readiness.py` pins `resolver_unavailable` with "readiness module is unavailable", and checks that no file is written. Mutation proof: with the message changed to "view module is unavailable", the test failed, 1 of 1; with the message restored from Git, it passed.
- **Short list card at rail widths.** From 90rem, `view.css` now sets `.worklist { align-self: start; }`, so a short "What is broken?" card keeps its own height instead of stretching to the rail. `test_a_short_list_card_keeps_its_own_height_beside_the_rail[1680, 2560]` checks two things: the card is shorter than the rail, and the card ends within 48px of its last child. Mutation proof: without the rule, 2 of 2 failed; with it, 2 of 2 passed.
- Left as the owner decided: the Blocked-row codes still wrap at 1280 and 1680px, and the start tag keeps its quiet style.

## T4

- Implemented by an `implementer` subagent. The five flat lists narrow through `ownerOnly` and `ownerEntries` in `owners.js`. The lists are "What can I work on next?" (checked and unchecked), "What is broken?" (by holder, workspace findings included), "What is still open under a capability?", "What has no parent?" and search.
  - Rail counts are refreshed in `handleRoute` on each owner change, and "unknown" stays "unknown".
  - The header line is a `p.lead.owner-line`. The empty states and the "Clear owner" control are added.
  - The live region already announced on an owner change, so it only gained a check.
- Readiness export: a `tmp_path` copy of `mixed` with `owner-two` on `bravo-spec` and `charlie-spec` and `owner-one` elsewhere. The status input is ready = [bravo, charlie] and blocked = [golf]. Its three term conditions are asserted under `k:owner-one`.
- Red proofs (temporary mutations, each restored):

  | Criterion | Mutation | Checks failed |
  | --- | --- | ---: |
  | AC-0012 | the owner filter returns every id | 5 |
  | AC-0013 | the open count follows the owner | 2 |
  | AC-0014 | the start tag lands on every row | 1 |
  | AC-0017 | no announcement on an owner change | 1 |
  | AC-0020 | rail counts are not refreshed | 2 |
  | AC-0020, "unknown" | the count stops returning "unknown" | 1 |
  | AC-0021 | the header line is empty | 4 |
  | AC-0022 | the owner words are dropped | 3 |
  | AC-0030 | "Clear owner" clears the search | 1 |

  AC-0008's readiness clause rests on T3's unchanged row cell.
- Open for T5: `listSummary` in `detail-render.js`, the detail pane's "In this list:" line, is built from unnarrowed data, but it is gated on the narrowed count. AC-0032's differential check decides whether that holds.
- Gates:
  - Full `view_browser_checks.py`: 457 passed, none skipped, in 293s.
  - The navigate-intents suite without the browser file, run under `-n 4`: 1134 passed, 6 skipped. The controller re-ran the 16 owner browser checks, which passed.
  - Clean: `make lint-ruff lint-mypy`, `lint-pack-test-boundary.py` and `check_view_base_parity.py`.

## T5 — contract amendment (owner decision, 2026-10-22)

- T5's differential check, `test_owner_narrowing_is_the_only_difference_ac_0032`, found one text node that AC-0032 does not admit: the detail pane's "In this list: …" summary, which `listSummary` in `detail-render.js` builds. It counts the unnarrowed list but disappears when the owner choice leaves no row. This was the only residual difference in 588 page pairs: 16 states across the `owners`, `scoped` and `readiness` exports.
- Owner decision on 2026-10-22 by eugenelim: under an owner choice, the summary follows the narrowed list and is absent when no row link is left. AC-0032's admitted difference 3 is amended to say so, and T5 gains a check of the summary's value.
- Completed tasks are untouched: T1 at `7de8b4a7a`, T2 at `dde88be7f`, T3 at `d15a372b4` and T4 at `e5f106e4f`, as this ledger records under each task.

## T5

- Implemented by an `implementer` subagent under the AC-0032 amendment, re-approved at `7bd2592bb`.
  - **Browse.** A Browse match is the Show match and `ownerMatches` together. Non-matching ancestors stay as context rows, and subtrees open on render whenever Show or the owner choice narrows.
  - **Roadmap.** A capability is listed when it matches or holds a listed nested capability. Non-matching listed capabilities show "context" and "shown for context". Sections with no listed capability are hidden.
  - **List summary.** `listSummary` counts only the shown rows, which meets difference 3. `readinessSummary()` in `readiness.js` had no caller left, so it was deleted.
  - The readiness export's status input is now ready = [bravo] and blocked = [golf (owner-one), charlie (owner-two)]. "What is broken?" therefore holds findings from both owners.
- **Differential check.** `test_owner_narrowing_is_the_only_difference_ac_0032` runs over the `owners`, `scoped`, `unavailable` and `readiness` exports. It covers 716 page states: 128 Any-owner pages and 588 owner pairs. It strips only the differences AC-0032 admits. Leaving any one of those differences unstripped makes the check fail, with residual counts from 54 to 2398.
- **Red proofs.** Each was a temporary mutation, restored byte-identical:

  | Mutation | Checks that failed |
  |---|---|
  | Browse ignores the owner | 4 |
  | Context tag removed | the README check and the general rule |
  | Roadmap section shown with no listed capability | 2 |
  | Nested capability not listed | 2 |
  | Roadmap rail count left unnarrowed | 1 |
  | Capabilities summary unnarrowed | `owners` |
  | Next summary unnarrowed | `owners` and `scoped` |
  | Checked-readiness summary unnarrowed | `readiness` |
  | Broken summary unnarrowed | `readiness` (expected "2 workspace findings") |

  The broken-summary check stayed green until the readiness export held findings from two owners.
- **Gates**
  - Full `view_browser_checks.py`: 473 passed in 322s, none skipped.
  - In two earlier full runs, a record-details wait timed out once each. It did not happen again, and the 59 record and detail tests passed on a targeted rerun.
  - The navigate-intents suite without the browser file, under `-n 4`: 1134 passed and 6 skipped.
  - `make lint-ruff lint-mypy`, `lint-pack-test-boundary.py` and `check_view_base_parity.py` are clean.
  - The controller re-ran the AC-0032 checks: 10 passed.

## T6

- Implemented by an `implementer` subagent. Five `hostile` records now carry hostile `Owner:` values: `</script><script>`, `<img … onerror>`, `"><svg onload>`, U+200B, U+202E and U+2066. U+2028 is left out because the preamble reader splits a line at it.
- **Stub red.** Before the fixture edit, `test_hostile_owner_values_stay_inside_the_data_block_ac0009` failed with `assert False`.
- **AC-0025 found two overflows.** With a 200-code-point owner chosen, the owner line and the empty-state text scrolled the page to 1558px. `view.css` now gives `.owner-line` and `.empty` the rules `min-width: 0` and `overflow-wrap: anywhere`.
- **AC-0026 found a label-in-name defect.** Session-start 0041 failed on context rows in all 8 matrix cells: the hidden "shown for context" text sat in the middle of the link's accessible name. `browse.js` and `roadmap.js` now append that span as the link's last child. The browser checks' tree reader now looks for it there.
- **Red proofs.**
  - AC-0031: with the owner cell set through raw `textContent`, the check failed.
  - AC-0025: without `overflow-wrap: anywhere` on `.c-owner`, 6 of 8 cells failed.
  - AC-0026: with the old span position, 8 of 8 cells failed.
- **Gates.**
  - Full `view_browser_checks.py`: 490 passed in 358s, none skipped.
  - The navigate-intents suite without the browser file: 1135 passed, 6 skipped.
  - `make lint-ruff lint-mypy`, `lint-pack-test-boundary.py` and `check_view_base_parity.py` are clean.
  - The controller re-ran 51 of the layout, escape and context checks, and they passed.

## T8

- **Commit:** `aa8e4f2d3256a0b2cd1e2a81490f149a1148a924`, the final code commit. Every figure below was taken at it. The working tree also held the bench change below and the scripts and screens in this directory. The controller dispatches the CI workflows and the `experience-reviewer` pass; AC-0029's review disposition is recorded separately.
- **Machine:** shared, load average about 31 at the start of the bench.

### AC-0027: scale benchmark with an owner in every record

Command: `python3.13 packs/core/tests/skills/navigate-intents/view_bench.py --source . --counts 1 10 25 50`. The bench's generator copied records unchanged, and 46 of this repository's 786 records (tombstones) carry no `Owner:` line. A minimal bench change (`_with_owner` in `view_bench.py`) now inserts `- **Owner:** bench-owner` after the first line of any record with none; a check over a 1-copy corpus found all 786 records carry an owner. Thresholds are the export spec's AC-0066: at most 104,857,600 bytes, startup at most 3,000 ms, search at most 300 ms, heap at most 1,024 MiB. Every corpus meets every threshold.

| copies | outstanding available | default rows | file bytes | startup ms | search ms | heap MiB | meets all |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | yes | 28 | 776,823 | 21 | 30 | 6 | yes |
| 10 | no (resource_limit, limit files) | 0 | 5,357,704 | 67 | 80 | 20 | yes |
| 25 | no (resource_limit, limit files) | 0 | 13,160,676 | 171 | 91 | 42 | yes |
| 50 | no (resource_limit, limit files) | 0 | 26,165,632 | 221 | 94 | 88 | yes |

- `outstanding` is unavailable from 10 copies up (`resource_limit`, files), as in the export's own benchmark and the earlier slices; the default list is then empty.

### AC-0028: the real export

Commands: `python3.13 packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py export --root . --destination <tmp>` (756,878 bytes, no readiness), then `python3.13 -I docs/specs/intent-view-record-owners/notes/ac0028_owner_counts.py <export.html>`. The script reads the page in headless Chromium (viewport 1280 wide) and computes the same figures from the payload by the spec's terms. "What can I work on next?" rows are the page's row links. "Browse all intents" rows are row links without a context tag after "Expand all" and the closed disclosure are opened; the header count (170 intents under Any owner) matches.

Option count: 26 on the page and 26 from the script. Result: `agree`.

| option | page next | script next | page browse | script browse |
| --- | --- | --- | --- | --- |
| Any owner | 28 | 28 | 170 | 170 |
| @eugenelim | 0 | 0 | 0 | 0 |
| Core maintainer | 0 | 0 | 0 | 0 |
| Core work-intake maintainers | 0 | 0 | 0 | 0 |
| Core work-intake maintainers; RFC-0083 Approver for removal | 0 | 0 | 1 | 1 |
| Documentation maintainers | 0 | 0 | 0 | 0 |
| eugenelim | 15 | 15 | 162 | 162 |
| eugenelim, Platform Core maintainer | 5 | 5 | 0 | 0 |
| example-user | 0 | 0 | 0 | 0 |
| experience-design maintainers | 0 | 0 | 0 | 0 |
| maintainer | 0 | 0 | 0 | 0 |
| maintainers | 0 | 0 | 0 | 0 |
| mubeen-acn | 0 | 0 | 0 | 0 |
| Platform Core | 2 | 2 | 0 | 0 |
| Platform Core (`ini-002`) | 1 | 1 | 0 | 0 |
| Platform Core maintainer | 0 | 0 | 5 | 5 |
| Product documentation maintainers | 0 | 0 | 1 | 1 |
| Product Engineering maintainers | 0 | 0 | 0 | 0 |
| project-maintainer | 0 | 0 | 0 | 0 |
| repository maintainer | 0 | 0 | 0 | 0 |
| Repository maintainers | 1 | 1 | 0 | 0 |
| Repository maintainers (`ini-002`) | 2 | 2 | 1 | 1 |
| Repository maintainers (`ini-003`) | 1 | 1 | 0 | 0 |
| Repository maintainers (`ini-009`) | 1 | 1 | 0 | 0 |
| unassigned | 0 | 0 | 0 | 0 |
| No owner recorded | 0 | 0 | 0 | 0 |
agree

### AC-0029: screenshots

Command: `python3.13 -I docs/specs/intent-view-record-owners/notes/screenshots.py <export.html> docs/specs/intent-view-record-owners/notes/screens`, over the same export, with a Playwright viewport (asserted `innerWidth` equals the width). Heights 900, 900, 1000 and 1400 for widths 320, 1280, 1680 and 2560. Owners chosen (most non-context rows, leaving out the dominant `eugenelim`):

- next: rows by owner, top three [('k:eugenelim', 15), ('k:eugenelim, platform core maintainer', 5), ('k:platform core', 2)]
- browse: rows by owner, top three [('k:eugenelim', 162), ('k:platform core maintainer', 5), ('k:core work-intake maintainers; rfc-0083 approver for removal', 1)]
- roadmap: rows by owner, top three [('k:eugenelim', 21), ('k:platform core maintainer', 1), ('k:@eugenelim', 0)]

SHA-256 of each file in `notes/screens/`:

```
31fbaf7fe970bd627bde71fdfdb03fc51776b52a65738225f4ab6b3f0af1d7c2 browse-1280-dark.png
9b9152e9c7cff2ec4ef0ecb6b94a69b45a6248456056c543e22a92bed0fc5e87 browse-1280-light.png
e4fee24718c93e2b4d694c91c5e09d102c911ff0341bc29f2654bbed894ea25e browse-1680-dark.png
9411c18066d40a0c8c192d20d5a8ccd4087e08f12c3328c39fc7686911b72832 browse-1680-light.png
7798cbde4ee7f1d09c8eaf5e12ff2be4e8db35272df119c2b92855c0d180fe0b browse-2560-dark.png
efab5ae03be15425defd80795ae4d74af3fcd30a3bde236caaa8e6376a224bc1 browse-2560-light.png
0fc035a61966e754ceda0a1d2126414fdda45005534303328d1a78f0fcff8ad9 browse-320-dark.png
efe49569bd054ac486495c76628fa22ba108d877ec24a8224b1296eff2ae348c browse-320-light.png
46b241e6022b218145c1a9866f8ae6c5912890f329141a181d027a67e347b69b next-1280-dark.png
9e1bfee6910d70e2042676ee7a611714c2fa82dc136ea9f2831a5864899ad397 next-1280-light.png
e1fc3e4793dd6ab3ae7d1cd530e6144800ecce818341a8de799af1dae0625311 next-1680-dark.png
d3c5410857ece2e44e29eee1bf61b693d77cf27ca81493d04afa4a8b542ca567 next-1680-light.png
b7eb52c348c64b640a75061390ba65e86f56a1dbc49c76ad572f85e9a3541265 next-2560-dark.png
77492fdd0918b7e74b5365cd510fae6d127d03cfc06a8aa179cc9c9248168393 next-2560-light.png
58d1d1f61f16f363928f7dff5f26bb477cba64cfd6b42f1104a387171cad386d next-320-dark.png
b906aa668aea4e5e95d53bb925342544f2b0055c07d7ba42d22f3ae165f53cb1 next-320-light.png
fbb80f1482b4d97071a9dd0cc7d95cbb78e183664f9610a8a0f3354b1b023a66 roadmap-1280-dark.png
e215db526c45f6a04e6da74ee3da1e55c79a167596a4fd830c956aeb38a1c3f0 roadmap-1280-light.png
0fc53e1fe6890f8d279b61154fdaf6d3d1b011358d29b0962ced74309bae1efb roadmap-1680-dark.png
20c7c411e2c30ecf80651f046dccbfb8ce4d1808d865aa5bf8ace96ec4df12da roadmap-1680-light.png
f5756088daf1a452987cc1677f64de8a12c3f96dd4e388d79ede0260d2dca7ec roadmap-2560-dark.png
f5573f03c3e6bbd017c6a93d2760b2a5f8efd6ab0ae8383cc389aa57c89b076e roadmap-2560-light.png
d9c3d6015be489a85b4950db172a3b8f9f482247c9a9f8b5a7508ee9f3359f6c roadmap-320-dark.png
95179f048fbb95e68875bdb01e78a24de619e483ea2fe62980f30163e9ce00ac roadmap-320-light.png
```
- The 24 images were recaptured from an export of `845ea3fba` plus the owner-cell layout fix in `view.css` (the owner now sits in the name column under the name at every multi-column width). The first set showed the owner cell drifting toward the next row, and the detail zone caught mid-fade. The script now uses reduced motion and scrolls to the top before each capture, so the header shows the Owner control and the owner line. The same states and owners were chosen as before.
- The T8 measurements ran against `29007336b`. The later commit `aa8e4f2d3` changes only tests, `SKILL.md` and the guide. It leaves the view code and the payload untouched. So the bench, the counts and the screenshots still describe the final code.
