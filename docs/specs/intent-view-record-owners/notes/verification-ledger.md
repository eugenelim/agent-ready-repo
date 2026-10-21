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
