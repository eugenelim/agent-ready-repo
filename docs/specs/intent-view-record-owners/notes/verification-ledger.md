# Verification ledger: intent view record owners

## Base commit

- Base commit: `6e0456e83`, `origin/main` after PR #1595 merged, on 2026-10-21. The spec and plan were approved at `5a8a691e1` and rebased onto this base unchanged.

## T1

- Implemented by an `implementer` subagent, commit `53c598f00`. `fixtures/owners/` holds 13 records: 10 intents, 1 brief and 2 specs. Its README hand-states 7 tables: 13 owner rows, 7 options, 15 owner-selector values, 5 non-owner selectors, 18 Browse rows, 6 roadmap rows and the scoping row. It covers every AC-0001 owner form, plus `Team  Two` and `TEAM TWO` as one owner key and `Édith Team` as a non-ASCII value.
- Red proof: `test_owners_cross_check_fails_for_an_unlisted_record` adds an unlisted record to a `tmp_path` copy and asserts that the cross-check fails. It then removes a listed record and asserts the failure again.
- Gates:
  - `test_derivation_contract.py`: 62 passed.
  - `lint-pack-test-boundary.py`: ok.
  - `make lint-ruff lint-mypy`: clean.
  - navigate-intents suite without the browser file: 529 passed, 4 skipped.

## T2

- Implemented by an `implementer` subagent, with one controller repair, in commit `5de6840bb`.
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
