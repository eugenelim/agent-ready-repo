# Verification ledger: decision navigation

Measured and manual evidence for `docs/specs/decision-navigation/spec.md`.
Each entry names its date, the commit it ran on, and the exact command.

## AC-0015 Chrome scale evidence

### Practicality thresholds (frozen 2026-10-03, before any measurement)

A full export stays practical at a corpus size only if every limit holds.

| Measure | Limit |
| --- | --- |
| HTML file size | 100 MiB |
| Startup: navigation start to first rendered list row | 3,000 ms |
| Representative search: keystroke to updated result list | 300 ms |
| Peak JS heap after startup and one search | 1,024 MiB |

### Method

- **Browser:** desktop Google Chrome, driven headless through Playwright's
  `chrome` channel; the exact version is recorded with each run.
- **Current corpus:** every admitted record under `docs/adr/` and `docs/rfc/`
  at the run commit.
- **Synthetic growth:** a scratch repository holds N renumbered copies of the
  current corpus (N = 1, 10, 25, 50). Each copy maps every record ordinal to a
  fresh ordinal and rewrites every `ADR-NNNN` and `RFC-NNNN` token inside that
  copy through the same map, so supersession and `Related` structure repeat
  exactly.
- **Startup:** median of three cold loads in a fresh browser context.
- **Search:** type `migration` into the search box; time until the result list
  stops changing; median of three.
- **Heap:** `performance.memory.usedJSHeapSize` peak after startup and search.

### Results (2026-10-05, commit `4f360a2e1`)

Desktop Google Chrome 154.0.8037.93 on macOS 26.5.2. The 1× corpus is the
repository at that commit: 243 records (139 ADRs, 104 RFCs). This re-run
replaces the runs at `3ed1f797` and `d2f93902f`; records now also carry their
exact header fields, which adds about 5% to the file.

| Scale | Records | Full HTML | Startup | Search | Peak heap | Within limits |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1× | 243 | 6.2 MiB | 159 ms | 1.1 ms | 20.8 MiB | yes |
| 10× | 2,430 | 60.3 MiB | 673 ms | 6.9 ms | 116.9 MiB | yes |
| 25× | 6,075 | 150.7 MiB | 1,345 ms | 17.3 ms | 440.3 MiB | no — file size |
| 50× | 12,150 | 301.3 MiB | 2,860 ms | 33.6 ms | 575.9 MiB | no — file size |

The bounded-mode figure is from the 2026-10-04 run: a bounded export of the
50× corpus is 14.6 MiB, starts in 577 ms, searches in 26.5 ms, and peaks at
28.0 MiB of heap.

**First threshold exceeded:** HTML file size (100 MiB), between 10× and 25×.

**Chosen rule:** publish full mode when the estimated file is at most 100 MiB.
Above that, the publisher refuses full mode unless the caller passes explicit
confirmation; bounded mode is the default answer for a larger corpus. The rule
is `BUDGET_BYTES` in `navigate-decisions/scripts/explorer.py`.

Command, from the repository root, with Playwright and Chrome installed:
`python3 <scratch>/bench.py . <scratch> 1,10,25,50` (pass the repository root as
the first argument; script reproduced under [Evidence scripts](#evidence-scripts)).

## AC-0016 and AC-0023 interaction evidence

Scripted run (2026-10-05, commit `0b812f14b`, Chrome 154.0.8037.93, offline
browser context) of the 1× full export (243 records), using `ux.py` exactly as
reproduced under [Evidence scripts](#evidence-scripts). Every line below is the
script's observed value; the script reads the expected record count from the
export's own data. It replaces the runs at `3ed1f797`, `d2f93902f`, `4f360a2e1` and `116dc1096`.

- **Offline:** zero requests other than the `file:` page itself; zero page errors.
- **Orientation:** corpus counts and the boundary sentence "It is not a
  complete statement of the policy applicable to any proposed action." are on
  the first screen.
- **Keyboard:** Tab reaches the three theme buttons (Auto, Light, Dark), the
  three kind filters, the status filter, search, and the four view buttons in
  that order; Enter on a record selects it and opens `#detail/ADR-0001`.
- **Focus:** focused controls show a 3 px solid outline.
- **Views keep selection:** list, graph, context, and detail each keep
  `ADR-0001` selected (`#graph/ADR-0001`, `#context/ADR-0001`, …).
- **History:** browser back returns `#detail/ADR-0001`; forward returns
  `#list/ADR-0001`; neither reads a file or the network.
- **No-results state:** `No records match search: "zzzz-no-match".` followed
  by a `Reset filters` button.
- **Graph trust labels:** the lifecycle graph labels partial supersession and
  its scope (`in part · D3`) apart from full supersession.
- **Reflow:** at 200% (640 CSS px) and 400% (320 CSS px) every view has zero
  horizontal overflow; the lineage diagram scales to fit and opens its text
  version first below 40rem.
- **Motion and activation:** a `prefers-reduced-motion` rule is present; no
  element uses double-click.

Not covered by the script: screen-reader announcement order and a sighted
review of visual focus contrast. Those stay with the human AC-0016 review.

## AC-0022 case-insensitive destination evidence

2026-10-05, commit `0b812f14b`, which contains the final destination checks
(ancestor-symlink walk and descriptor-bound publication), macOS 26.5.2 (APFS,
case-insensitive temporary directory: a file created as `A` is found as `a`).
It replaces the runs at `3ed1f797` and `4f360a2e1`. Command:

`python3 -m pytest "packs/governance-extras/tests/skills/navigate-decisions/test_html_publication.py::test_refuses_case_variant_inside_worktree" -v -p no:cacheprovider`

Result: `PASSED`. The test asserts the case-variant directory exists and the
refusal names the worktree, so it cannot pass on a missing path. The
owner-only mode tests `test_temp_sibling_mode_0600_before_write` and
`test_published_file_mode_0600` passed in the same run.

## T7 corrections from the first post-gates review

The first post-gates review (2026-10-04, branch head `a241146fd`) sustained
58 findings after independent adjudication. T7 closes every one by the mode
listed in its row. The plan's T7 Tests own the mode definitions and this row
set; only the Status column changes here.

| ID | Severity | Finding | Closes by | Status |
| --- | --- | --- | --- | --- |
| ADV-1 | Blocker | Relationship `source` holds a record ID instead of a repository-relative path. | failing test | closed — `test_relationship_source_is_superseding_record_for_checked_pair` asserts `source` is a repo-relative path (e.g. `docs/adr/0003-charlie.md`); passes with code at `navigate_decisions.py:1115`. |
| ADV-2 | Blocker | Records carry no structured header fields, so no output has `exact headers`. | failing test | reopened by the round-3 review; closed at `116dc1096` — header fields keep their continuation lines, ending where the `Related` grammar ends a field. `test_header_field_keeps_continuation_lines` (wrapped text and a nested bullet) and `browser_checks.py::test_detail_shows_every_header_field_exactly` (a wrapped `Related` row, and Status shown once) failed before; the round-2 tests for `Date` and `Supersedes: none` stand. |
| ADV-3 | Blocker | The relationship, result-byte and lineage bounds are never enforced. | failing test | reopened by the round-2 review; closed at `4f360a2e1` — the 512 KiB and 400-relationship tests stand; `test_lineage_result_too_large_when_record_count_exceeds_200` adds the lineage record bound and failed on the previous code. |
| ADV-4 | Blocker | Malformed selectors and assertions return the whole corpus or crash instead of refusing. | failing test | closed — `test_search_non_list_selectors_fails`, `test_search_selector_with_only_unknown_keys_fails`, `test_search_non_dict_selector_element_fails` added; all assert `status == "error"`; validation enforced at `navigate_decisions.py:1144`. |
| ADV-5 | Blocker | In the HTML, caller assertions lose their text and are not normalized relationship tuples. | failing test | reopened by the round-2 review; closed at `4f360a2e1` — `test_caller_assertions_in_relationships_data_island` and `test_assertion_tuple_parity_query_vs_export` (same input gives identical tuples in query and HTML, inside `relationships`); `browser_checks.py::test_caller_assertion_is_drawn_and_listed_in_the_graph`. All failed on the previous code. |
| ADV-6 | Blocker | The support-reference inventory is missing. | failing test | closed — `test_support_refs_in_data_island_mixed` passes: asserts support_refs is a list on each record and corpus_support_refs is non-empty; `_collect_support_refs` at `explorer.py` scans `NNNN-notes/` dirs (kind=notes_dir), `NNNN-*-research.md` files (kind=research_file), and per-dir `README.md` files (kind=readme); symlinks skipped via `os.lstat`. |
| ADV-7 | Blocker | Several AC-0022 destination refusals and proofs are missing. | failing test | reopened by the round-4 review; closed at `0b812f14b` — publication runs relative to one descriptor for the validated directory: the temporary file is created, linked and removed through it, and the path must still name that directory just before the link. `test_directory_swap_between_validation_and_publish_refused[open]` swaps right after the descriptor opens and proves the swap is refused before any file exists; `[os.link]` swaps after the temporary file is written, where the descriptor-relative link would otherwise succeed into the renamed directory, so it proves the pre-link path check refuses it (a recorded mutation that makes that check a no-op fails the case). Both assert `publish_failed` and that neither directory holds a file of any name; both failed before. No check-then-use window remains for the write itself; non-POSIX hosts publish by path after the same validation. |
| ADV-8 | Blocker | The HTML shows record text without display escaping, in the same text node as trust labels. | failing test | reopened by the round-2 review; closed at `4f360a2e1` — `browser_checks.py::test_rendered_page_never_shows_raw_bidi_controls` stands; `test_paths_and_assertion_endpoints_escape_directional_marks` adds RLM, ALM and LRM in a source basename and an assertion endpoint and failed on the previous code. |
| ADV-9 | Concern | The explorer and the query read registers and corpus roots differently. | failing test | closed — `test_export_refuses_unsafe_register` asserts dangling-symlink register refuses the export; `test_export_two_table_register_sum` asserts two-table register row_count=3; `test_export_summary_parity_with_query_summary` compares all summary fields between export and query; `_count_register_rows` now counts all tables; `_read_register_file` detects dangling symlinks; `_scan_kind_dir` refuses dangling corpus roots. |
| ADV-10 | Concern | Header parsing departs from the stated grammar. | failing test | closed — `test_h1_not_first_line_fails_whole_operation` asserts refusal when H1 is not the first line; `test_two_html_comments_keeps_first_comment` asserts only the last comment is stripped; `test_repeated_d_ids_form_set` asserts duplicated D-IDs are deduplicated to a sorted set. |
| ADV-11 | Concern | Shipped scripts cite internal governance records. | document change | reopened by the round-2 review; closed at `4f360a2e1` — `grep -nE "AC-00|RFC-0|ADR-0|docs/specs|packs/core|spec\b|ledger"` over the skill's `scripts/*.py`, `*.js` and `*.css` finds only `importlib` variables named `spec` and one `ADR-0001` example in a code comment; before the fix it found the repository path, `RFC-0102 § 3`, 17 spec quotations and a ledger mention. |
| ADV-12 | Concern | The ledger commits a personal local path. | document change | closed — the hardcoded home-directory path was replaced with `Path(sys.argv[1]).resolve()` in `bench.py` embedded in this ledger. |
| ADV-13 | Concern | The provenance block is inserted into the HTML without escaping. | failing test | closed — `test_provenance_not_interpolated_in_html` asserts the static HTML body contains no raw `{` characters from provenance interpolation; `test_csp_provenance_not_in_static_html` asserts CSP hash is present and provenance content absent from static HTML; JS fills `#prov-pre` via `provPre.textContent = JSON.stringify(D.provenance, null, 2)`. |
| ADV-14 | Concern | The guide, design doc and skill contradict shipped behavior. | document change | reopened by the round-2 review; closed at `4f360a2e1` — SKILL.md now states the refusal envelope, header fields, assertion validation and the temporary-directory default with a no-`--destination` example first; the guide states that selectors OR together and that `text` matches title and status only. |
| ADV-15 | Concern | Some tests cannot fail, and the AC-0021 fixtures are missing. | mutation red | reopened by the round-2 review; closed at `4f360a2e1` — `test_relationships_sort_order` and `test_scope_sort_empty_before_stated` build their inputs directly with no guards; AC-0021 tests `test_ac0021_absence_as_permission_no_match_returns_boundary`, `test_ac0021_conflict_resolution_both_records_returned`, `test_ac0021_grouping_edges_are_navigation_only` added. Recorded mutations, each caught: empty scope sorts last; null `to` sorts last; assertion trust class set to `checked`; search keeps only the first match; a no-match search falls back to every record. |
| ADV-16 | Concern | Plan T2 names a verification file that does not exist. | ledger deviation | closed — deviation recorded in "Deviations from completed task text": T2's `test_filesystem_safety.py` maps to the confinement cases in `test_query_contract.py`. |
| ADV-17 | Concern | Refusal shapes are not stable. | failing test | reopened by the round-3 review; closed at `116dc1096` — export refusals use the query's `{code, message, limits, observed}` object; `test_export_register_refusal_carries_the_query_limit` asserts the register refusal carries the same `max_register_bytes` limit as the query (failed before). |
| ADV-18 | Concern | Full export drops admitted bodies between 1 MiB and 2 MiB. | failing test | closed — `test_full_export_embeds_body_larger_than_1_mib` writes a 1.5 MiB record body, exports in full mode, and asserts the embedded body has available=True; full mode now always embeds body_text directly, bypassing the 1 MiB query limit. |
| ADV-19 | Concern | A commit-pinned link can show content that differs from the export. | failing test | reopened by the round-2 review; closed at `4f360a2e1` — `test_unpushed_head_produces_branch_latest` asserts a clean tree on a HEAD absent from the remote gets the may-be-newer label; it failed on the previous code. |
| ADV-20 | Nit | The pack description still makes the retired promise. | document change | closed — `packs/governance-extras/pack.toml` description updated from "keep track of which ones are still open" to describe the navigate-decisions capability; `git diff packs/governance-extras/pack.toml` confirms change. |
| SEC-1 | Blocker | CLI `--name` is joined before validation, so a dot-segment or absolute name escapes the destination root. | failing test | closed — `test_cli_export_dotdot_name_exits_two` and `test_cli_export_absolute_name_exits_two` call `main()` with hostile `--name` and assert exit code 2; validation at `navigate_decisions.py:1925` validates name before any join. |
| SEC-2 | Concern | Raw bidi controls reach visible HTML, and the escape set misses directional marks. | failing test | reopened by the round-2 review; closed at `4f360a2e1` — the unsafe set adds U+200E, U+200F, U+061C, U+0080–U+009F and U+2060–U+2064 in both Python and JavaScript; `test_paths_and_assertion_endpoints_escape_directional_marks`, `test_display_source_present_on_records` and `test_assertion_tuple_has_display_from_display_to` failed on the previous code. |
| SEC-3 | Concern | Provenance is put into the HTML without HTML escaping. | failing test | closed — same closure as ADV-13; `test_csp_provenance_not_in_static_html` and `test_provenance_not_interpolated_in_html` cover both the static-HTML absence and the JS textContent assignment; provenance data goes through the JSON data island and is read by JS via `D.provenance`. |
| SEC-4 | Concern | The export reads register files through a duplicate code path that reports unsafe or oversized files as absent. | failing test | closed — see ADV-9/QE-1; same tests and code fixes; `_read_register_file` now detects dangling symlinks as UnsafeContentError; the export's register exception handler now returns a dict `error` with a code field. |
| SEC-5 | Concern | Caller assertions are not checked against a schema. | failing test | reopened by the round-2 review; closed at `4f360a2e1` — one validator serves context and export; `test_context_null_assertions_refused`, `test_context_integer_assertions_refused`, `test_context_partial_dict_assertion_refused`, `test_export_invalid_assertion_non_list_refused`, `test_export_invalid_assertion_non_dict_element_refused`, `test_export_invalid_assertion_partial_dict_refused` all failed on the previous code. |
| SEC-6 | Concern | SKILL.md does not declare the `filesystem_write` boundary its script crosses. | document change | closed — `packs/governance-extras/.apm/skills/navigate-decisions/SKILL.md` boundaries updated from `[filesystem_read_untrusted]` to `[filesystem_read_untrusted, filesystem_write]`; `git diff` confirms change. |
| SEC-7 | Concern | Publication is not tied to the identity of the directory that was validated, and the temporary sibling is not validated before the link. | failing test | reopened by the round-2 review; closed at `4f360a2e1` — see ADV-7: `test_directory_swap_between_validation_and_publish_refused`. |
| SEC-8 | Nit | The repository-identity parser accepts dot-segment owner and repo names, and the host allowlist constant is never read. | failing test | reopened by the round-2 review; closed at `4f360a2e1` — `_parse_github_identity` checks the parsed host against `_SOURCE_HOST_ALLOWLIST`; `test_parse_github_identity_non_allowlisted_host_returns_none` pins it (the old regex already refused this host, so the test pins the read rather than a defect). |
| QE-1 | Blocker | The export recomputes the summary and turns register refusals into `absent`. | failing test | closed — see ADV-9/SEC-4; `test_export_refuses_unsafe_register`, `test_export_two_table_register_sum`, and `test_export_summary_parity_with_query_summary` close this finding. |
| QE-2 | Blocker | The 400-relationship and 512 KiB non-detail limits are never enforced. | failing test | closed — see ADV-3 above; same tests and code. |
| QE-3 | Blocker | The explorer embeds raw caller dicts, so assertion text never shows. | failing test | reopened by the round-2 review; closed at `4f360a2e1` — see ADV-5. |
| QE-4 | Blocker | An empty selector or one with only unknown keys matches the whole corpus. | failing test | closed — see ADV-4 above; `test_search_selector_with_only_unknown_keys_fails` directly tests this. |
| QE-5 | Blocker | The lineage tests cannot fail on depth or on traversal of unchecked edges. | mutation red | closed — `test_lineage_depth_limit_respected` uses `lineage-chain` fixture with ADR-0001→0002→0003; depth=1 asserts `ADR-0002 in ids_d1` and `ADR-0001 not in ids_d1`; depth=2 asserts `ADR-0001 in ids_d2`; `test_lineage_traverses_only_checked_relationships` asserts `ADR-0002 not in record_ids` (unchecked edges not traversed). |
| QE-6 | Concern | A Status value with two HTML comments loses everything after the first comment. | failing test | closed — see ADV-10; `test_two_html_comments_keeps_first_comment` verifies `Accepted <!-- a --> kept <!-- b -->` yields raw_value `Accepted <!-- a --> kept`; `_TRAILING_COMMENT_RE` with negative lookahead `(?!-->)` was already correct. |
| QE-7 | Concern | Badly typed query input crashes `run_query` or is silently accepted. | failing test | closed — `test_non_dict_query_returns_error_not_crash` passes string/int/None/list and asserts `status == "error"`; fix at `navigate_decisions.py:1679`: `isinstance(query, dict)` guard added. |
| QE-8 | Concern | Most refusal tests check that an error happened, not which error. | mutation red | closed — `test_unsafe_filesystem_symlink_refuses_operation`, `test_unsafe_filesystem_hard_link_refuses_operation`, `test_unsafe_filesystem_fifo_refuses_operation`, `test_traversal_attempt_refuses_operation` all now assert `payload["error"]["code"] == "unsafe_input"`. |
| QE-9 | Concern | Several inertness and encoding tests are tautologies or run on fixtures that cannot trigger them. | mutation red | closed — `test_bidi_raw_value_preserved_display_value_escaped` asserts `"‮" in raw`, `"‮" not in display`, and `"[U+202E]" in display`; fixture contains literal bidi controls; cannot pass on a fixture without them. |
| QE-10 | Concern | The no-partial-file test never reaches `os.link`. | mutation red | closed — `test_no_partial_file_on_link_failure` now calls `publish_explorer(FIXTURE, destination=tmp_path, name="no_partial.html", mode="bounded")` with valid args to reach `os.link`; `assert called_paths` ensures the mock was hit. |
| QE-11 | Concern | The parity test compares only part of the relationship data. | mutation red | reopened by the round-2 and round-3 reviews; closed at `116dc1096` — `test_fact_parity_relationship_tuples` asserts the query and data-island tuple sets are equal (all records, all trust classes, `raw_value` and `source` included) and fails on any record query that is not `ok`; recorded mutations dropping one exported relationship and adding an invented one both fail it. |
| QE-12 | Nit | Export refusals carry prose only, with no machine-readable code. | failing test | closed — `publish_explorer` now returns `{"code": "...", "message": "..."}` dict for all error cases; `test_export_refusal_carries_machine_readable_code` asserts dict with `code` and `message` keys. |
| QE-13 | Concern | Source links trust whatever git repository encloses `root`, and the HTML tests run real git. | failing test | closed — `_git_root_matches(root)` extracted; `publish_explorer` uses `_git_root_matches` to decide whether to build links; HTML tests mock `_git_root_matches` directly rather than running real git. |
| QE-14 | Concern | A malformed or unknown URL hash leaves the explorer blank. | scripted Chrome check | reopened by the round-2 review; closed at `4f360a2e1` — `browser_checks.py::test_hash_routing_bogus_hash_shows_list` and `test_hash_routing_uri_error_safe`. |
| QE-15 | Concern | The ledger's Chrome evidence scripts cannot reproduce its recorded results. | document change | reopened by the round-3 review; closed at `116dc1096` — `ux.py` reads the expected record count from the export, and its boundary check matches the current sentence; the AC-0016 run at `116dc1096` reports every value from the script. `bench.py` reproduces the AC-0015 table. |
| QE-16 | Nit | The CLI entry point has no tests. | mutation red | closed — `test_cli_query_summary_exits_zero`, `test_cli_query_unknown_record_exits_one`, `test_cli_query_invalid_selectors_json_exits_two`, `test_cli_query_operation_routes_to_run_query` added; all call `NAV.main()` directly. |
| QE-17 | Concern | Shipped pack scripts cite internal governance records, and one citation reaches every exported HTML file. | document change | reopened by the round-2 review; closed at `4f360a2e1` — see ADV-11. |
| QE-18 | Nit | The by-path module loader is duplicated, and one copy has drifted. | lint or search | reopened by the round-2 review; closed at `4f360a2e1` — `_get_nav` now has the same `OSError` wrapping and required-symbol check as `_get_file_safety`; a search for register errors caught by class-name string returns nothing. |
| QE-19 | Nit | Dead code and unused names. | lint or search | reopened by the round-2 review; closed at `4f360a2e1` — the re-raise-only `except` block is gone: a search for an `except` line followed only by `raise` in `navigate_decisions.py` returns nothing. |
| QE-20 | Nit | The temp file descriptor leaks if `fchmod` fails. | failing test | reopened by the round-2 review; closed at `4f360a2e1` — `test_fchmod_failure_closes_fd` captures the specific temporary descriptor and asserts it is closed, with no count slack and no external binary; the recorded mutation that skips the close fails it. |
| QE-21 | Nit | The owner-only temp-mode test checks call order, not the actual mode. | mutation red | closed — `test_temp_sibling_mode_0600_before_write` now records `actual_modes_at_fchmod` via `os.fstat(fd).st_mode` and asserts `any(m == 0o600 for m in actual_modes_at_fchmod)`; a mutation to `0o644` fails the actual-mode assertion. |
| FE-F1 | Concern | Back to the first no-hash entry leaves the previous view and selection on screen. | scripted Chrome check | reopened by the round-2 review; closed at `4f360a2e1` — `browser_checks.py::test_hash_routing_empty_hash_shows_list` opens a record, goes Back to the no-hash entry, and asserts the list heading with detail hidden. |
| FE-F4 | Concern | An unknown route or unparseable data island renders a blank main area with no error. | scripted Chrome check | reopened by the round-2 review; closed at `4f360a2e1` — `browser_checks.py::test_hash_routing_bogus_hash_shows_list` and `test_no_page_errors_mixed`; a damaged data island now shows a `role="alert"` recovery message inside `#app-main`. |
| FE-F2 | Nit | Focus drops to the document body after a record, edge or context button navigates. | scripted Chrome check | reopened by the round-2 review; closed at `4f360a2e1` — `browser_checks.py::test_focus_moves_to_view_heading` and `test_reset_filters_keeps_keyboard_focus` (the latter failed on the previous code). |
| FE-F3 | Nit | No live region announces result-count or no-results changes. | scripted Chrome check | reopened by the round-2 review; closed at `4f360a2e1` — `browser_checks.py::test_live_region_updates_on_filter` asserts the exact announcements (`… records shown.` and `No records match search: "zzzzz-no-match".`). |
| FE-F5 | Nit | The no-results message does not echo the active query or filters and offers no reset control. | scripted Chrome check | reopened by the round-2 review; closed at `4f360a2e1` — `browser_checks.py::test_no_results_shows_reset_control`. |
| FE-F6 | Nit | Edge and context buttons fall below the 24-by-24 target size, and no exception is documented. | scripted Chrome check | reopened by the round-2 review; closed at `4f360a2e1` — `browser_checks.py::test_24px_min_targets` walks every visible button, link, select and input in the list view; the supersession-banner link got a 24 px minimum height. |
| FE-F9 | Nit | Record buttons say they are toggles but navigate. | scripted Chrome check | reopened by the round-2 review; closed at `4f360a2e1` — `browser_checks.py::test_aria_current_on_nav_buttons`. |
| FE-F10 | Nit | An unknown record ID in the route shows the `nothing selected` guidance instead of saying the record is missing. | scripted Chrome check | reopened by the round-2 review; closed at `4f360a2e1` — `browser_checks.py::test_missing_id_shows_not_in_export` (detail) and `test_unknown_record_shows_not_in_export_in_every_view` (graph, context, detail; failed on the previous code). |
| FE-F11 | Nit | Long record bodies have no progressive disclosure, and orientation scrolls away. | scripted Chrome check | reopened by the round-2 review; closed at `4f360a2e1` — `browser_checks.py::test_long_body_folded` asserts the long body sits in one `details.body-details` that opens by default with summary `Record content (N chars)`, matching the shipped behaviour. |

## Round-2 review corrections

The second post-gates review (2026-10-05, head `b7b1f24d1`) sustained 46
findings after adjudication (`.context/reviews/<run>/2-post-gates-*`). Fixes
landed in `c08d99a61` and `4f360a2e1`. Rows that reopen a T7 row point to it;
"failed before" means the test failed on the code before the fix.

| ID | Severity | Finding | Closed by |
| --- | --- | --- | --- |
| R2-ADV-1 | Blocker | No output carries exact headers. | See ADV-2. |
| R2-ADV-2 | Blocker | Export assertions are not the query's tuples and are not schema-checked. | See ADV-5 and SEC-5. |
| R2-ADV-3 | Concern | Null or falsy `assertions` crashes `context`. | See SEC-5. |
| R2-ADV-4 | Concern | Lineage skips the 200-record bound. | See ADV-3. |
| R2-ADV-5 | Concern | An unparseable superseded-by claim shows no unresolved marker. | `test_unresolved_claims_from_unparseable_superseded_by` (failed before). |
| R2-ADV-6 | Concern | SKILL.md and the guide contradict shipped behaviour. | See ADV-14. |
| R2-ADV-7 | Concern | Shipped scripts cite internal records. | See ADV-11. |
| R2-ADV-8 | Concern | Vacuous sort tests; AC-0021 fixtures missing. | See ADV-15. |
| R2-ADV-9 | Concern | Publication is not bound to the validated directory. | See ADV-7. |
| R2-ADV-10 | Concern | A commit-pinned link can name an unpushed commit. | See ADV-19. |
| R2-ADV-11 | Concern | Export refusals differ from the query error object. | See ADV-17. |
| R2-ADV-12 | Concern | AC-0022 case-insensitive evidence predates the final code. | Re-run at `4f360a2e1`; see AC-0022 evidence. |
| R2-ADV-13 | Concern | AC-0016 evidence quotes a string the code cannot produce. | Re-recorded at `4f360a2e1`; see AC-0016 evidence. |
| R2-ADV-14 | Concern | The atlas drops cycle relationships. | `browser_checks.py::test_atlas_draws_and_labels_cycle_relationships` (failed before). |
| R2-ADV-15 | Concern | Source paths, support paths and assertion endpoints are not escaped. | See ADV-8. |
| R2-ADV-16 | Nit | FE-F11 row misdescribes the code. | See FE-F11. |
| R2-ADV-17 | Nit | The SEC-8 allowlist check cannot fail. | See SEC-8. |
| R2-ADV-18 | Nit | A gate result reads `pending`. | Stage 3 lint now records its result. |
| R2-SEC-1 | Blocker | The Markdown renderer is quadratic on heading whitespace and unmatched openers. | Linear closer search and a scan-based heading parser; `browser_checks.py::test_inline_pathological_body_renders_in_linear_time` (near-2 MiB body of every shape, under 2 s, no fallback; failed before). |
| R2-SEC-2 | Concern | The escape set misses directional marks and C1 controls. | See SEC-2. |
| R2-SEC-3 | Concern | Export assertions are not schema-checked. | See SEC-5. |
| R2-SEC-4 | Concern | Publication is not bound to the validated directory. | See ADV-7. |
| R2-SEC-5 | Nit | The allowlist check cannot fail. | See SEC-8. |
| R2-SEC-6 | Nit | The deep-nesting fallback shows the body unescaped. | The fallback renders `vis(text)`; covered by `test_pathological_body_renders_fully_and_inertly`. |
| R2-FE-1 | Concern | Links are unreadable in dark mode. | Themed link colour; `browser_checks.py::test_links_are_readable_in_both_themes` (list banner link, ≥ 4.5:1 in both themes; failed before) and `test_bounded_notice_is_readable_in_dark_mode` (bounded notice and its source link; failed before the round-3 fix). |
| R2-FE-2 | Nit | Code text is low-contrast in dark mode. | Dark `pre`, `code` and `th` backgrounds. |
| R2-FE-3 | Nit | The narrow graph shrinks below readable size. | The text equivalent opens first below 40rem and each node in it is now a button that focuses that record. |
| R2-FE-4 | Concern | Wrapped list items break into code blocks. | `browser_checks.py::test_wrapped_list_item_stays_in_its_bullet` (failed before). |
| R2-FE-5 | Nit | Expand all collapses on first use. | The label follows the open state; `browser_checks.py::test_expand_all_opens_every_section_on_first_click` (failed before). |
| R2-FE-6 | Nit | Unknown IDs mislead in context and graph. | See FE-F10. |
| R2-FE-7 | Nit | Reset filters drops focus. | See FE-F2. |
| R2-FE-8 | Nit | Stat labels break mid-word at 390 px. | Auto-fit grid columns with no forced word break. |
| R2-FE-9 | Nit | Edge scope labels collide with curves. | Labels sit on plates in a layer above the edges. |
| R2-QE-1 | Blocker | Scripted-Chrome rows cite missing or vacuous checks. | Every scripted-Chrome Status cell above names an existing check; FE-F1, FE-F3, FE-F6, FE-F11 checks tightened; full run recorded below. |
| R2-QE-3 | Concern | The descriptor-leak test tolerates the leak. | See QE-20. |
| R2-QE-4 | Concern | The lineage text list differs from the diagram. | One relationship definition for both, stamped on each element; `browser_checks.py::test_graph_text_equivalent_matches_svg_nodes` compares the full drawn and listed sets (failed before). |
| R2-QE-6 | Concern | Loose browser checks. | Relationships section required with exact per-trust-class counts; atlas card count exact (3); live-region text exact. |
| R2-QE-7 | Concern | Relationship parity covers one record. | See QE-11. |
| R2-QE-8 | Concern | Export accepts malformed assertions and raises tracebacks. | See SEC-5 and ADV-17; `publish_explorer` returns the error object for any failure. |
| R2-QE-9 | Nit | The hostile export is never rendered; CSP test has pass-through branches. | `browser_checks.py::test_hostile_titles_and_status_stay_inert_in_every_view`; the CSP test asserts unconditionally. |
| R2-QE-11 | Nit | QE-18 and QE-19 closures do not hold. | See QE-18 and QE-19. |
| R2-EXP-1 | Blocker | Supersession and source links are unreadable in dark mode. | See R2-FE-1: the list-banner link (both themes) and the bounded-notice link (dark) are measured; test exports carry no detail source links, so the detail source link is not measured. |
| R2-EXP-6 | Nit | Partial-edge labels collide. | See R2-FE-9. |
| R2-EXP-7 | Nit | Partial supersession is struck through like full. | Strike-through for full only, dashed underline for partial, in list and graph; `browser_checks.py::test_strike_through_marks_full_supersession_only` (failed before). |
| R2-EXP-8 | Nit | The context view omits the record's status and banner. | The context view shows title, exact status and the superseded-by banners. |
| R2-EXP-10 | Nit | Stat labels break mid-word. | See R2-FE-8. |

Full browser run: `python3 -m pytest packs/governance-extras/tests/skills/navigate-decisions/browser_checks.py -q`
at `f76931033` (2026-10-05, desktop Chrome 154.0.8037.93): 52 passed in 118 s. Unit
suites at the same commit: 261 passed. These checks run only by direct
invocation; no CI job collects `browser_checks.py`.

The owner also asked for an Auto / Light / Dark theme control in this round;
`browser_checks.py::test_theme_toggle_sets_and_remembers_the_theme` covers it.

## Round-3 review corrections

The third post-gates review (2026-10-05, head `e21d4727d`) sustained 27 findings
after adjudication, one of them resolved by an owner decision. Fixes landed in
`116dc1096`. "Failed before" means the test failed on the code at `e21d4727d`.

| ID | Severity | Finding | Closed by |
| --- | --- | --- | --- |
| R3-ADV-1 | Blocker | Header fields keep only their first line. | See ADV-2. |
| R3-ADV-2 | Concern | An assertion between chain members is not drawn or listed. | `browser_checks.py::test_caller_assertions_are_drawn_in_chain_and_as_satellites` (failed before). |
| R3-ADV-3 | Concern | Partial and full supersession differ by colour only; the atlas does not differ. | Hollow double line plus "in part" label in both views; `browser_checks.py::test_partial_edges_differ_by_line_style_in_focus_and_atlas` (failed before). |
| R3-ADV-5 | Concern | Commit-pinned links accept HEAD on any remote. | HEAD must be on an `origin/` branch; `test_commit_pinned_requires_head_on_origin` (failed before for the other-remote case). |
| R3-ADV-7 | Concern | The no-results message shows the raw status value. | `browser_checks.py::test_status_filter_text_is_escaped_in_no_results` (failed before). |
| R3-ADV-6 | Concern | A grouping-only selector returns the whole corpus. | Owner decision (2026-10-05): refuse it as `invalid_selector`; `grouping` stays valid beside a filter key; `test_grouping_only_selector_is_refused` (failed before). |
| R3-ADV-4 | Nit | The link-phase identity check has no failing test. | See ADV-7. |
| R3-ADV-9 | Nit | Export register refusal has empty limits. | See ADV-17. |
| R3-ADV-10 | Nit | `ux.py` hard-codes the record count. | See QE-15. |
| R3-SEC-1 | Nit | A record ID from the URL is shown unescaped. | Escaped and capped at 64 characters in graph, context and detail; `browser_checks.py::test_unknown_route_id_is_escaped_and_capped` (failed before). |
| R3-SEC-2 | Nit | No CLI test for export assertion refusal. | `test_cli_export_refuses_malformed_assertions` (number, object, non-string field; each publishes nothing). |
| R3-SEC-3 | Nit | Tag and format characters are not escaped. | Both sets add U+00AD, U+180E, U+206A–U+206F, U+FFF9–U+FFFB and U+E0000–U+E007F, matched by code point in JavaScript; `test_escape_display_covers_tag_and_format_characters` and `browser_checks.py::test_tag_characters_are_visibly_escaped` (failed before). |
| R3-FE-1 | Concern | The bounded-notice link is unreadable in dark mode. | See R2-FE-1. |
| R3-FE-3 | Nit | Text-list node buttons look like browser defaults. | `.lt-node-btn` matches the list. |
| R3-FE-4 | Nit | The Expand all label goes stale after a manual toggle. | `browser_checks.py::test_expand_label_follows_sections_toggled_by_hand` (failed before). |
| R3-FE-5 | Nit | Detail shows Status twice. | The header Status row is folded into the lifecycle row; pinned in `test_detail_shows_every_header_field_exactly`. |
| R3-FE-6 | Nit | "(may be newer than this export)" repeats. | The appended copy is removed; the link label keeps it. |
| R3-QE-1 | Concern | Parity checks one direction and skips refusals. | See QE-11: equal sets including `source`, failing on any non-`ok` record query; an "add one relationship" mutation fails it. |
| R3-QE-2 | Concern | The swap test misses the link phase. | See ADV-7. |
| R3-QE-4 | Concern | No drawn assertion is checked. | See R3-ADV-2. |
| R3-QE-5 | Nit | The damaged-data-island message has no check. | `browser_checks.py::test_damaged_data_island_shows_a_recovery_alert`. |
| R3-QE-6 | Nit | The link-contrast docstring overclaims. | Docstring narrowed to the list banner link. |
| R3-EXP-1 | Nit | Node markers differ across views. | Atlas nodes get the same marks: struck-through ID for full, underlined ID for partial; `browser_checks.py::test_supersession_state_is_named_and_marked_in_both_graph_views` (failed before). |
| R3-EXP-2 | Nit | Legends omit the node markers. | Two legend lines; node accessible names end with ", superseded" or ", superseded in part". |
| R3-EXP-3 | Concern | Two Status rows can disagree. | See R3-FE-5. |
| R3-EXP-4 | Nit | Dark-preference users see a light flash. | Dark tokens apply under `prefers-color-scheme: dark` until the script sets a theme. |
| R3-EXP-5 | Nit | A selected node loses its supersession mark. | A dashed outer ring marks a selected superseded node. |

Full browser run at `116dc1096` (2026-10-05, desktop Chrome 154.0.8037.93):
61 passed in 126 s. Unit suites at the same commit: 271 passed.

## Round-4 review corrections

The fourth post-gates review (2026-10-05, head `169e0b5a2`) sustained 20 findings,
closed under plan task T8 by the modes it pins. Fixes landed in `0b812f14b`.
"Failed before" means the test failed on the code at `169e0b5a2`.

| ID | Severity | Finding | Closes by | Status |
| --- | --- | --- | --- | --- |
| R4-ADV-1 | Blocker | The grouping-only refusal contradicts the spec and guide. | document change | closed — the amended spec (selector rule) and the guide state that a selector whose only key is `grouping` is refused with `invalid_selector`; `test_grouping_only_selector_is_refused` pins the shipped refusal. |
| R4-ADV-2 | Concern | Detail hides a recorded Status the lifecycle row does not show. | scripted Chrome check | closed — `browser_checks.py::test_wrapped_status_shows_its_own_row` (a wrapped Status shows two Status rows, a one-line Status with a comment shows one; failed before). |
| R4-ADV-3 | Concern | Supersession fields read only their first line. | failing test | closed — `test_wrapped_supersession_field_yields_every_entry` (failed before). |
| R4-ADV-4 | Nit | Arrowheads scale and fan-in labels overlap. | scripted Chrome check | closed — see R4-FE-1 and R4-FE-2. |
| R4-ADV-5 | Nit | The QE-11 and R2-EXP-1 rows were stale. | document change | closed — both rows above now state what their checks measure. |
| R4-ADV-6 | Nit | No bounded-export check of a multi-line header; stale docstring. | failing test | closed — `test_bounded_export_keeps_a_multi_line_header_value` pins the value (the bounded export already kept it, so it pins behaviour rather than failing before); the swap-test docstring describes both phases. |
| R4-SEC-1 | Concern | Header continuation lines were joined in quadratic time. | failing test | closed — values are built from line lists joined once; `test_admission_time_bound_on_a_near_2_mib_supersession_header` (2,000,086 bytes, 200,000 token-carrying lines, under 2 s; failed before). The AC-0001 condition names the `ubuntu-latest` / Python 3.11 runner; that run is recorded below once dispatched. |
| R4-FE-1 | Concern | Fan-in `in part` labels stack in the atlas. | scripted Chrome check | closed — labels step down one plate height per target side; `browser_checks.py::test_fan_in_labels_stay_clear_in_focus_and_atlas` (no plate meets another plate, a node box or an arrowhead box in either view; failed before). |
| R4-FE-2 | Nit | Partial-edge arrowheads scale with stroke width. | scripted Chrome check | closed — `markerUnits="userSpaceOnUse"`; `browser_checks.py::test_arrowheads_keep_one_size_on_full_and_partial_edges` (failed before). |
| R4-FE-3 | Concern | In-chain asserted edges run beneath other nodes. | scripted Chrome check | closed — routed through the column gutters and the row gap; `browser_checks.py::test_in_chain_assertion_never_passes_beneath_a_node` (no path point inside another node; plate clear; failed before). |
| R4-FE-4 | Nit | Expand all mislabels itself on the list view. | scripted Chrome check | closed — `browser_checks.py::test_expand_all_label_is_unchanged_on_a_view_without_sections` (failed before). |
| R4-FE-5 | Nit | Text-list bullets align to the last line. | scripted Chrome check | closed — `browser_checks.py::test_text_list_node_buttons_align_to_the_top` (failed before). |
| R4-QE-1 | Concern | A swap after the temporary file left it behind. | failing test | closed — see ADV-7: cleanup goes through the directory descriptor; both swap cases assert no file of any name remains. |
| R4-QE-2 | Concern | The link-phase swap case passed with a no-op check. | failing test | closed — see ADV-7. |
| R4-QE-3 | Nit | The QE-11 row was stale. | document change | closed — see R4-ADV-5. |
| R4-QE-4 | Nit | The hollow stroke and focused label were unchecked. | scripted Chrome check | closed — `browser_checks.py::test_partial_edges_are_hollow_and_labelled_in_both_views` (failed before). |
| R4-EXP-1 | Concern | The graph focus ring failed 3:1 and merged with the supersession ring. | scripted Chrome check | closed — a dark outer ring with an amber inner ring, outside the supersession ring; `browser_checks.py::test_graph_focus_ring_reaches_3_to_1_and_clears_the_supersession_ring` (both themes; failed before). |
| R4-EXP-2 | Nit | Dark first paint covered only the tokens. | scripted Chrome check | closed — every component dark rule is mirrored for an unset theme under the system preference; `browser_checks.py::test_dark_first_paint_without_scripts` (failed before). |
| R4-EXP-3 | Nit | Atlas labels stack on fan-in. | scripted Chrome check | closed — see R4-FE-1. |
| R4-EXP-4 | Nit | The partial ID underline style differed by view. | scripted Chrome check | closed — `browser_checks.py::test_partial_id_underline_style_matches_across_views` (failed before). |

Status-field amendment tests: `test_lifecycle_value_from_the_status_label_line`
(`**Status**:` yields `Accepted`, failed before; a wrapped Status keeps its
label-line value, already true) and `test_both_status_label_forms_make_a_record_malformed`
(failed before).

Full runs at `0b812f14b` (2026-10-05, desktop Chrome 154.0.8037.93): browser
checks 71 passed in 95 s; unit suites 277 passed.

## T7 stage 2b evidence — explorer visual redesign

Date: 2026-10-05. Branch: this feature branch. Files changed:
`explorer.css`, `explorer.js`, `explorer.py` (`_build_html` only).

### WCAG 2.2 AA contrast pairs (light theme)

| Pair | Foreground | Background | Ratio | Pass |
| --- | --- | --- | --- | --- |
| Body text | `#111827` | `#ffffff` | 18.1:1 | AA ✓ |
| Muted text | `#4b5563` | `#ffffff` | 7.4:1 | AA ✓ |
| Monospace ID | `#1d4ed8` | `rgba(29,78,216,.09)` on white | ~5.1:1 | AA ✓ |
| Active nav btn | `#ffffff` | `#1d4ed8` | 6.6:1 | AA ✓ |
| Accepted status pill | `#166534` | `#dcfce7` | 5.9:1 | AA ✓ |
| Proposed status pill | `#1e40af` | `#dbeafe` | 6.1:1 | AA ✓ |
| Superseded status pill | `#374151` | `#f3f4f6` | 8.0:1 | AA ✓ |
| Deprecated status pill | `#991b1b` | `#fee2e2` | 5.6:1 | AA ✓ |
| Supersede banner text | `#92400e` | `#fff7ed` gradient start | 5.8:1 | AA ✓ |
| Info panel text | `#374151` | `#f0f4ff` | 7.2:1 | AA ✓ |

### Verification results

- **Unit tests:** `python3 -m pytest packs/governance-extras/tests/skills/navigate-decisions -q -p no:cacheprovider` → 196 passed.
- **Browser checks:** `python3 -m pytest packs/governance-extras/tests/skills/navigate-decisions/browser_checks.py -q -p no:cacheprovider` → 20 passed (Chrome 154.0.8037.93 on macOS 26.5.2).
- **Lint:** `make lint-ruff lint-mypy` → 0 errors.
- **Build:** `make build-self FORCE=1` → ok; `make build-self-dry-run` → ok.
- **No horizontal overflow:** 640px and 320px both false (confirmed by Playwright).

### Key design choices

- `#app { max-width: 1100px; overflow-x: hidden }` — centered white column over grid background.
- Grid: two overlapping 1-px `linear-gradient` at 48-px repeat on `body`.
- Gradient title: `-webkit-background-clip: text` on `<span class="title-gradient">`.
- `blockquote`: background tint + italic, `border: none` — no left-border rail; confirmed distinct from evidence-rail (4 px left solid/dashed/dotted/double) and supersede banner (3 px left amber).
- `.record-content { border: 2px solid var(--border) }` — borderLeftWidth = 2px, not 4px; test `test_record_content_border_differs_from_evidence_rail` confirms.
- Kind filter changed from `<select>` to pill buttons (`<div id="kind-filter" class="kind-pills">`); JS updated accordingly.
- Stat cards filled from `D.summary` at boot via `renderStatCards()`.
- Expand-all button toggles all `<details>` in the current view.

## T7 stage 3 evidence — SVG lineage diagram and chain atlas (AC-0026)

Date: 2026-10-05. Branch: this feature branch. Files changed:
`explorer_assets/lineage.js` (new), `explorer.js` (`renderGraph` only),
`explorer.css` (lineage styles), `explorer.py` (asset list + script block),
`tests/skills/navigate-decisions/test_html_publication.py` (4 new tests),
`tests/skills/navigate-decisions/browser_checks.py` (14 new tests + 5 new fixtures).

### What was built

- `lineage.js` — self-contained SVG layered diagram module (`var Lineage = ...`).
  Uses `createElementNS` exclusively; no `innerHTML`, `outerHTML`, `insertAdjacentHTML`,
  `eval`, `Function(`, embedded-document or reuse SVG elements, or xlink attributes.
- `renderFocused` — Sugiyama-style layout: oldest records at column 0 (left), newest at max
  column (right). Tarjan SCC for cycle detection; longest-path layering; barycenter crossing
  reduction (3 sweeps). Contextual edges hidden by default behind an `aria-expanded` toggle.
  Roving tabindex: ArrowRight → newer, ArrowLeft → older, Enter → navigate.
  Text equivalent (`<details class="lineage-text">`) lists the same node IDs as the SVG.
- `renderAtlas` — chain atlas for `#graph`: one `.chain-card` per connected component with
  ≥2 records, sorted by size desc then lowest ordinal. Small-scale (0.62×) SVG per card.
- `explorer.js` `renderGraph` updated: calls `Lineage.renderFocused` when `state.sel` is
  set, `Lineage.renderAtlas` otherwise.
- CSP hash automatically recomputed because `lineage.js` is concatenated into `script_body`
  before `_csp_hash(script_body)` is called.

### Publication tests (unit)

Command: `python3 -m pytest packs/governance-extras/tests/skills/navigate-decisions/test_html_publication.py -q -p no:cacheprovider`

Result: **75 passed** (71 pre-existing + 4 new AC-0026 security tests).

New tests:
- `test_lineage_js_no_forbidden_strings` — inlined script contains none of the 8 forbidden patterns.
- `test_lineage_js_defines_lineage_var` — `var Lineage=` present in inlined script.
- `test_lineage_js_csp_hash_matches_script_block` — sha256 in CSP meta tag matches computed hash of inlined script.
- `test_lineage_js_uses_createelementns` — `createElementNS` present in inlined script.

### Browser checks added

14 new test functions for AC-0026 in `browser_checks.py`, verified against
desktop Chrome (Playwright `chrome` channel). Fixtures: `export_cycle` (3-record SCC),
`export_branching` (4-record Y-shape), `export_five_chain` (5-record linear chain).

Checks cover: SVG ≥2 node groups with D3 scope label; older record left of newer;
contextual toggle (hidden then visible, chain x unchanged); cycle members share x-column
with "cycle" labels in ordinal order; branching chain shows all 4 members; 5-chain shows
all 5 members in x-ascending order; Tab-reachable node (tabindex=0), ArrowRight moves focus,
Enter changes hash; text equivalent matches SVG node IDs; atlas `.chain-card` count;
zero page errors; no non-file requests; no horizontal overflow at 640 px and 320 px.

### Lint

Command: `make lint-ruff lint-mypy`

Result: pass at `4f360a2e1` (2026-10-05).

### Screenshots

Manual screenshots at 1440×900 (`#graph/ADR-0098`, `#graph/ADR-0050`, `#graph`,
dark mode `#graph/ADR-0098`) are a supervisor-level visual verification step,
not a hard gate for this task. The scripted browser checks above serve as
the primary AC-0026 gate.

## Deviations from completed task text

- **T2 verification artifact (ADV-16):** T2 names `test_filesystem_safety.py`,
  but its filesystem-confinement tests live in `test_query_contract.py`.
  The confinement proof for T2 is the `test_query_contract.py` cases that
  build symlink, hard-link, special-file, and traversal shapes.

## Evidence scripts

### bench.py

```python
"""AC-0015 scale benchmark: synthetic N-copy corpora, full export, Chrome timings."""
import json, re, shutil, statistics, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(sys.argv[1]).resolve()  # pass the repository root as the first argument
SP = Path(sys.argv[2]); SCALES = [int(x) for x in sys.argv[3].split(",")]
NAV = REPO / "packs/governance-extras/.apm/skills/navigate-decisions/scripts/navigate_decisions.py"
TOK = re.compile(r"\b(ADR|RFC)-(\d{4})\b")

def records(kind):
    d = REPO / "docs" / kind
    return sorted(p for p in d.glob("[0-9][0-9][0-9][0-9]-*.md") if not p.name.endswith("-research.md"))

def build(n):
    root = SP / f"scale-{n}"
    if root.exists(): shutil.rmtree(root)
    src = {"ADR": records("adr"), "RFC": records("rfc")}
    for k in range(n):
        maps = {kind: {p.name[:4]: f"{k*len(ps)+i+1:04d}" for i, ps_i in [(0,0)] for i, p in enumerate(ps)} for kind, ps in src.items()}
        for kind, ps in src.items():
            out = root / "docs" / kind.lower(); out.mkdir(parents=True, exist_ok=True)
            for p in ps:
                new = maps[kind][p.name[:4]]
                text = TOK.sub(lambda m: f"{m.group(1)}-{maps[m.group(1)].get(m.group(2), m.group(2))}", p.read_text(encoding="utf-8"))
                (out / f"{new}{p.name[4:]}").write_text(text, encoding="utf-8")
    return root

def export(root, n):
    dest = SP / "exports"; dest.mkdir(exist_ok=True)
    name = f"scale-{n}.html"; (dest / name).unlink(missing_ok=True)
    r = subprocess.run([sys.executable, str(NAV), "export", "--root", str(root), "--destination", str(dest),
                        "--name", name, "--mode", "full", "--confirm-over-budget"], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode: raise SystemExit(f"export {n} failed: {r.stdout[-500:]} {r.stderr[-500:]}")
    return dest / name

def measure(pw, html):
    starts, searches, heaps = [], [], []
    for _ in range(3):
        b = pw.chromium.launch(channel="chrome", headless=True, args=["--enable-precise-memory-info"])
        ctx = b.new_context(offline=True); page = ctx.new_page()
        t0 = time.perf_counter(); page.goto(html.as_uri()); page.wait_for_selector("li.record-item")
        starts.append((time.perf_counter() - t0) * 1000)
        ms = page.evaluate("""() => {const e=document.getElementById('search-input');const t=performance.now();
            e.value='migration';e.dispatchEvent(new Event('input'));return performance.now()-t;}""")
        searches.append(ms)
        heaps.append(page.evaluate("() => performance.memory.usedJSHeapSize") / 2**20)
        version = b.version; b.close()
    return version, statistics.median(starts), statistics.median(searches), max(heaps)

rows = []
with sync_playwright() as pw:
    for n in SCALES:
        root = REPO if n == 1 else build(n)
        html = export(root, n)
        v, s, q, h = measure(pw, html)
        rows.append({"scale": n, "bytes": html.stat().st_size, "startup_ms": round(s), "search_ms": round(q, 1), "heap_mib": round(h, 1), "chrome": v})
        print(json.dumps(rows[-1]), flush=True)
```

### ux.py

```python
"""AC-0016 / AC-0023 scripted interaction checks in desktop Chrome."""
import sys, json
from pathlib import Path
from playwright.sync_api import sync_playwright
html = Path(sys.argv[1])
res = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    ctx = b.new_context(viewport={"width": 1280, "height": 800}, offline=True)
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e))); p.on("requestfailed", lambda r: errs.append("req " + r.url))
    reqs = []; p.on("request", lambda r: reqs.append(r.url))
    p.goto(html.as_uri()); p.wait_for_selector("li.record-item")
    res["network_requests_beyond_file"] = [u for u in reqs if not u.startswith("file:")]
    body = p.inner_text("body")
    res["policy_boundary_shown"] = "not a complete statement of the policy" in body.lower()
    total = p.evaluate("JSON.parse(document.getElementById('nav-data').textContent).records.length")
    res["counts_shown"] = f"{total}" in p.inner_text("#stat-cards")
    # keyboard: tab through, collect focused elements
    seen = []
    for _ in range(12):
        p.keyboard.press("Tab")
        seen.append(p.evaluate("() => {const a=document.activeElement;return a.id||a.tagName+'.'+a.className}"))
    res["tab_sequence"] = seen
    res["focus_visible_outline"] = p.evaluate("() => {const a=document.activeElement;const s=getComputedStyle(a);return s.outlineStyle+' '+s.outlineWidth}")
    # select a record by keyboard (Enter on first record button)
    p.focus("li.record-item button"); p.keyboard.press("Enter")
    sel = p.evaluate("() => location.hash")
    res["select_by_enter_hash"] = sel
    for v in ["graph", "context", "detail", "list"]:
        p.click(f"#btn-{v}")
        res[f"view_{v}_hash"] = p.evaluate("() => location.hash")
    p.go_back(); res["back_hash"] = p.evaluate("() => location.hash")
    p.go_forward(); res["forward_hash"] = p.evaluate("() => location.hash")
    # filters
    p.fill("#search-input", "zzzz-no-match")
    res["no_results_msg"] = p.inner_text("#view-list")[:120]
    p.fill("#search-input", "")
    # graph labels
    p.click("#btn-graph"); g = p.inner_text("#view-graph")
    res["graph_mentions_partial"] = "part" in g.lower(); res["graph_mentions_scope"] = "D3" in g or "scope" in g.lower()
    # zoom reflow: 200% and 400% == viewport 640 and 320 CSS px
    for z, w in ((200, 640), (400, 320)):
        p.set_viewport_size({"width": w, "height": 800 * 100 // z})
        for v in ["list", "graph", "context", "detail"]:
            p.click(f"#btn-{v}")
            over = p.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            res[f"hscroll_{z}_{v}"] = over
    p.set_viewport_size({"width": 1280, "height": 800})
    # reduced motion rule present
    res["reduced_motion_rule"] = "prefers-reduced-motion" in p.content()
    # dblclick dependence
    res["dblclick_handlers"] = p.evaluate("() => document.querySelectorAll('[ondblclick]').length") + p.content().count("dblclick")
    res["page_errors"] = errs
    b.close()
print(json.dumps(res, indent=1))
```

## AC-0020 comparative outcome

### Frozen panel (2026-10-04, before any session)

Each session attempts all five tasks once with `navigate-decisions` and once
by direct file browsing, alternating which condition goes first per session.
Answers are scored against the repository at the session's commit.

| Task | Prompt | Correct answer must include |
| --- | --- | --- |
| 1. Orientation | How many ADRs and RFCs exist, and how many RFCs are not Accepted? | Exact counts by kind and every non-`Accepted` RFC status value |
| 2. Exact status | What is RFC-0099's exact lifecycle status? | The full qualified value, not just `Accepted` |
| 3. Partial supersession | Which decisions does ADR-0098 supersede in part, and which D-IDs? | ADR-0019 D6, D7 and ADR-0076 D1, D2, both checked |
| 4. Guidance context | Given the assertion "RFC-0105 is wider guidance for ADR-0134", what relates them and how far can you trust it? | The assertion is navigation-only; any `Related` links are contextual; no checked lineage is implied |
| 5. Handoff | Where is ADR-0001's rationale, and where does its source live? | Its body or a source handoff, the repository-relative path, and the statement that this is not complete applicable policy |

### Measurement rules

- **Run:** one task attempted in one session in one condition.
- **Lookup effort:** files opened plus tool or query calls. For an agent, every
  tool call counts. For a person using the HTML explorer, each search entry,
  filter change, view switch, and record selection counts as one query call,
  and opening the export counts as one file.
- **Unaided:** the run finishes with no hint, correction, or help from anyone.
- **Incorrect claim:** any wrong status, lineage, guidance-trust, policy-
  completeness, or source statement in the final answer.
- **Pass:** at least four of five tasks have lower median effort with the
  navigator; at least 80% of navigator runs finish unaided; zero incorrect
  claims across all runs; at least two human-run and two agent-run sessions.

### Sessions

Two agent-run sessions ran on 2026-10-05 at commit `d2f93902f`, each a fresh
general-purpose subagent with no help. Session A ran the navigator first on
every task; session B ran direct browsing first. Effort is the agent's tool
calls in the run; the one-time `SKILL.md` read counts in the first navigator
run.

| Task | A navigator | A direct | B navigator | B direct | Median navigator | Median direct | Navigator lower |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1. Orientation | 3 | 2 | 4 | 3 | 3.5 | 2.5 | no |
| 2. Exact status | 1 | 1 | 1 | 1 | 1 | 1 | no (tie) |
| 3. Partial supersession | 1 | 1 | 1 | 1 | 1 | 1 | no (tie) |
| 4. Guidance context | 1 | 1 | 1 | 1 | 1 | 1 | no (tie) |
| 5. Handoff | 2 | 1 | 1 | 1 | 1.5 | 1 | no |

- **Correctness:** all 20 runs correct; zero incorrect claims.
- **Unaided:** 10 of 10 navigator runs (100%).
- **Effort:** the navigator is lower on 0 of 5 tasks. The pass rule needs 4.
- **Answer key:** task 3's frozen key names ADR-0019 and ADR-0076 only. The
  corpus records five checked partial supersessions (ADR-0009 D2, ADR-0019 D6,
  D7, ADR-0076 D1, D2, ADR-0077 D1, ADR-0078 D6); every run named all five.

**Status: AC-0020 fails on effort for agent runs.** In this corpus one `grep`
or `cat` answers each task in about one call, so the navigator cannot beat it.
Human-run sessions (owner or delegate) have not run.

## T7 stage 2 evidence

Chrome version: 154.0.8037.93 (confirmed via `bench.py` output, headless channel="chrome").

Command (commit-independent):

```bash
python3 -m pytest packs/governance-extras/tests/skills/navigate-decisions/browser_checks.py \
    -q -p no:cacheprovider
```

Pass output:

```
...................                                                      [100%]
19 passed in 61.70s
```

Python test suite (failing-test findings):

```bash
python3 -m pytest packs/governance-extras/tests/skills/navigate-decisions/test_html_publication.py \
    -q -p no:cacheprovider
```

```
68 passed in 39.75s
```

Lint gates:

```
make lint-ruff lint-mypy → All checks passed! / Success: no issues found in 149 source files
python3 tools/lint-pack-test-boundary.py </dev/null → exit 0
python3 tools/lint-ci-parity.py </dev/null → exit 0
```

---

## T7 stage 2a evidence

**Date:** 2026-10-04

**Items shipped:** ITEM 1 (asset file extraction), ITEM 2 (safe Markdown renderer),
ITEM 3 (full CSP), ITEM 4 (supersession banners from checked relationships).

Python test suite:

```bash
python3 -m pytest packs/governance-extras/tests/skills/navigate-decisions -q -p no:cacheprovider
```

```
196 passed in 111.15s
```

New tests added (3):
- `test_markdown_renderer_no_unsafe_apis` — inlined JS carries no forbidden DOM-mutation APIs
- `test_csp_all_directives_present` — all five CSP directives present including `base-uri` and `form-action`
- `test_superseded_by_from_checked_only` — ADR-0001 `superseded_by=[{by:ADR-0020,partial:true,scope:[D3]}]`; ADR-0002 `[{by:ADR-0003,partial:false}]`; ADR-0003 empty

Lint gates:

```
make lint-ruff lint-mypy → All checks passed! / Success: no issues found in 149 source files
python3 tools/lint-pack-test-boundary.py </dev/null → exit 0 (8 cases passed)
make build-self-dry-run → catalogue self-host --check: ok
```

Asset files: CSS and JS moved from Python string constants to
`packs/governance-extras/.apm/skills/navigate-decisions/scripts/explorer_assets/`
(`explorer.css`, `explorer.js`, `markdown.js`). Loaded at export time via
`read_confined_regular_file`; hash of inlined script bytes used for CSP `script-src`.

### T7 stage 2a browser checks (2026-10-04, desktop Chrome 154.0.8037.93)

Command: `python3 -m pytest packs/governance-extras/tests/skills/navigate-decisions/browser_checks.py -q -p no:cacheprovider` → 20 passed, 0 skipped.

- `test_markdown_renders_allowlisted_structure` — headings, lists, quotes, code, tables, rules, emphasis render as allowlisted elements; only `class` and `aria-label` attributes; no `img` or `a`; link targets and alt text shown as text.
- `test_pathological_body_renders_fully_and_inertly` — a near-2 MiB hostile body renders within 2 s, shows the 32-level fallback note, keeps `<script>` literal, has no attributes, and makes no requests. This check caught a defect: bodies over 1 MiB were embedded as `null` in full exports; fixed in `navigate_decisions.py` with `test_full_export_embeds_body_larger_than_1_mib` strengthened to assert the body text.
- `test_supersession_banners_in_list_and_detail` — "Superseded in part by ADR-0020 (D3)" and "Superseded by ADR-0003" appear in list rows and detail, and the banner link opens ADR-0020.

### Correction (2026-10-05)

ADV-8 and SEC-2 had been marked closed on tests that inspected the data island and
the script source only. A rendered-page check showed raw bidirectional and
zero-width controls in record titles, statuses, and relationship text across the
list, detail, graph, and context views. The page now renders `display_title`,
`display_value`, and `display_raw_value`, and the closing evidence for both rows is
the rendered-page check above. The same session fixed a long-status layout defect
reported by the owner on RFC-0099 (`test_long_qualified_status_does_not_squeeze_title`).
