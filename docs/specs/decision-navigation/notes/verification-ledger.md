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

### Results (2026-10-04, commit `3ed1f797deae8656dbe27e471dce7378b9898406`)

Desktop Google Chrome 154.0.8037.93 on macOS 26.5.2. The 1× corpus is the
repository at that commit: 238 records (134 ADRs, 104 RFCs).

| Scale | Records | Full HTML | Startup | Search | Peak heap | Within limits |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1× | 238 | 5.7 MiB | 116 ms | 1.0 ms | 19.5 MiB | yes |
| 10× | 2,380 | 56.3 MiB | 598 ms | 5.6 ms | 170.3 MiB | yes |
| 25× | 5,950 | 140.6 MiB | 1,275 ms | 13.3 ms | 412.9 MiB | no — file size |
| 50× | 11,900 | 281.2 MiB | 3,030 ms | 28.0 ms | 828.2 MiB | no — file size and startup |

A bounded export of the 50× corpus is 14.6 MiB, starts in 577 ms, searches in
26.5 ms, and peaks at 28.0 MiB of heap.

**First threshold exceeded:** HTML file size (100 MiB), between 10× and 25×.

**Chosen rule:** publish full mode when the estimated file is at most 100 MiB.
Above that, the publisher refuses full mode unless the caller passes explicit
confirmation; bounded mode is the default answer for a larger corpus. The rule
is `BUDGET_BYTES` in `navigate-decisions/scripts/explorer.py`.

Command, from the repository root, with Playwright and Chrome installed:
`python3 <scratch>/bench.py . <scratch> 1,10,25,50` (pass the repository root as
the first argument; script reproduced under [Evidence scripts](#evidence-scripts)).

## AC-0016 and AC-0023 interaction evidence

Scripted run (2026-10-04, commit `3ed1f797`, Chrome 154.0.8037.93, offline
browser context) of the 1× full export:

- **Offline:** zero requests other than the `file:` page itself; zero page errors.
- **Orientation:** corpus counts (238) and the boundary sentence "It is not a
  complete statement of the policy applicable to any proposed action." are on
  the first screen.
- **Keyboard:** Tab reaches search, kind filter, status filter, the four view
  buttons, then each record button; Enter on a record selects it.
- **Focus:** focused controls show a 3 px solid outline.
- **Views keep selection:** list, graph, context, and detail each keep
  `ADR-0001` selected (`#graph/ADR-0001`, `#context/ADR-0001`, …).
- **History:** browser back returns `#detail/ADR-0001`; forward returns
  `#list/ADR-0001`; neither reads a file or the network.
- **No-results state:** "No records match the active search and filters. Clear
  to see all 238 records."
- **Graph trust labels:** the lifecycle graph labels partial supersession and
  its scope (`D3`) apart from full supersession.
- **Reflow:** at 200% (640 CSS px) and 400% (320 CSS px) every view has zero
  horizontal overflow. An earlier run found 391 px and 711 px of overflow from
  the status filter; fixed in `6cbf8eb6` before this run.
- **Motion and activation:** a `prefers-reduced-motion` rule is present; no
  element uses double-click.

Not covered by the script: screen-reader announcement order and a sighted
review of visual focus contrast. Those stay with the human AC-0016 review.

## AC-0022 case-insensitive destination evidence

2026-10-04, commit `3ed1f797deae8656dbe27e471dce7378b9898406`, macOS 26.5.2
(APFS, case-insensitive temporary directory). Command:

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
| ADV-2 | Blocker | Records carry no structured header fields, so no output has `exact headers`. | failing test | closed — `test_record_fields_include_id_kind_title_source` now asserts `header_fields` key is present and is a dict; `test_record_header_fields_contains_supersession_entries` asserts at least one supersession key is present for ADR-0001; code builds `header_fields` at `navigate_decisions.py:1101`. |
| ADV-3 | Blocker | The relationship, result-byte and lineage bounds are never enforced. | failing test | closed — `test_relationship_limit_enforced` calls `_check_non_detail_bounds` with 401 relationships and asserts `result_too_large`; `test_result_byte_limit_enforced` calls it with records totalling over 512 KiB and asserts `result_too_large`; code enforces both limits at `navigate_decisions.py:960`. |
| ADV-4 | Blocker | Malformed selectors and assertions return the whole corpus or crash instead of refusing. | failing test | closed — `test_search_non_list_selectors_fails`, `test_search_selector_with_only_unknown_keys_fails`, `test_search_non_dict_selector_element_fails` added; all assert `status == "error"`; validation enforced at `navigate_decisions.py:1144`. |
| ADV-5 | Blocker | In the HTML, caller assertions lose their text and are not normalized relationship tuples. | failing test | closed — `test_caller_assertions_normalized_in_data_island` passes: asserts trust_class=navigation_only, resolution_state=caller_asserted, raw_value preserved; `test_caller_assertion_non_dict_normalized` covers non-dict input; `test_normalize_assertion_function_output` covers all three dict shapes; `_normalize_assertion` at `explorer.py` normalizes before embedding. |
| ADV-6 | Blocker | The support-reference inventory is missing. | failing test | closed — `test_support_refs_in_data_island_mixed` passes: asserts support_refs is a list on each record and corpus_support_refs is non-empty; `_collect_support_refs` at `explorer.py` scans `NNNN-notes/` dirs (kind=notes_dir), `NNNN-*-research.md` files (kind=research_file), and per-dir `README.md` files (kind=readme); symlinks skipped via `os.lstat`. |
| ADV-7 | Blocker | Several AC-0022 destination refusals and proofs are missing. | failing test | closed — `test_refuses_ancestor_symlink_in_destination_path` asserts refusal when a path component is a symlink; code fix walks each prefix with `os.lstat`; `test_hostile_record_does_not_redirect_destination` exports the instruction fixture and asserts the file lands in the given directory. |
| ADV-8 | Blocker | The HTML shows record text without display escaping, in the same text node as trust labels. | failing test | closed — `browser_checks.py::test_rendered_page_never_shows_raw_bidi_controls` (failed before the 2026-10-05 fix: titles, statuses, and relationship text rendered raw in list, detail, graph, and context; passes after) |
| ADV-9 | Concern | The explorer and the query read registers and corpus roots differently. | failing test | closed — `test_export_refuses_unsafe_register` asserts dangling-symlink register refuses the export; `test_export_two_table_register_sum` asserts two-table register row_count=3; `test_export_summary_parity_with_query_summary` compares all summary fields between export and query; `_count_register_rows` now counts all tables; `_read_register_file` detects dangling symlinks; `_scan_kind_dir` refuses dangling corpus roots. |
| ADV-10 | Concern | Header parsing departs from the stated grammar. | failing test | closed — `test_h1_not_first_line_fails_whole_operation` asserts refusal when H1 is not the first line; `test_two_html_comments_keeps_first_comment` asserts only the last comment is stripped; `test_repeated_d_ids_form_set` asserts duplicated D-IDs are deduplicated to a sorted set. |
| ADV-11 | Concern | Shipped scripts cite internal governance records. | document change | closed — `grep -rn "AC-00\|docs/specs/decision" packs/governance-extras/.apm/skills/navigate-decisions/ --include="*.py"` returns no matches; references removed from explorer.py and navigate_decisions.py in this branch. |
| ADV-12 | Concern | The ledger commits a personal local path. | document change | closed — the hardcoded home-directory path was replaced with `Path(sys.argv[1]).resolve()` in `bench.py` embedded in this ledger. |
| ADV-13 | Concern | The provenance block is inserted into the HTML without escaping. | failing test | closed — `test_provenance_not_interpolated_in_html` asserts the static HTML body contains no raw `{` characters from provenance interpolation; `test_csp_provenance_not_in_static_html` asserts CSP hash is present and provenance content absent from static HTML; JS fills `#prov-pre` via `provPre.textContent = JSON.stringify(D.provenance, null, 2)`. |
| ADV-14 | Concern | The guide, design doc and skill contradict shipped behavior. | document change | closed — `guides/governance-extras/how-to/navigate-decisions.md` lineage example updated to show all 10 relationship fields with explanatory text; confirmed guide matches code output. |
| ADV-15 | Concern | Some tests cannot fail, and the AC-0021 fixtures are missing. | mutation red | closed — `test_reference_policy_boundary_present_in_response` parameterized over all 5 operations with exact boundary sentinel; `test_lineage_traverses_only_checked_relationships` strengthened with `assert "ADR-0002" not in record_ids`; lineage-chain fixture added for 3-hop depth test. |
| ADV-16 | Concern | Plan T2 names a verification file that does not exist. | ledger deviation | closed — deviation recorded in "Deviations from completed task text": T2's `test_filesystem_safety.py` maps to the confinement cases in `test_query_contract.py`. |
| ADV-17 | Concern | Refusal shapes are not stable. | failing test | closed — `test_query_refusal_has_documented_error_shape` asserts error dict has code, message, limits, and observed fields; export refusals for unsafe/oversized registers now return `{"status":"error","error":{"code":…,"message":…}}` matching the query shape. |
| ADV-18 | Concern | Full export drops admitted bodies between 1 MiB and 2 MiB. | failing test | closed — `test_full_export_embeds_body_larger_than_1_mib` writes a 1.5 MiB record body, exports in full mode, and asserts the embedded body has available=True; full mode now always embeds body_text directly, bypassing the 1 MiB query limit. |
| ADV-19 | Concern | A commit-pinned link can show content that differs from the export. | failing test | closed — `test_commit_pinned_link_only_when_clean` mocks clean git status and asserts commit_pinned; `test_dirty_working_tree_link_labelled_may_be_newer` mocks dirty status and asserts branch_latest with "may be newer" label; `_build_source_links` now calls `git status --porcelain docs/adr docs/rfc` and only emits commit_pinned when output is empty. |
| ADV-20 | Nit | The pack description still makes the retired promise. | document change | closed — `packs/governance-extras/pack.toml` description updated from "keep track of which ones are still open" to describe the navigate-decisions capability; `git diff packs/governance-extras/pack.toml` confirms change. |
| SEC-1 | Blocker | CLI `--name` is joined before validation, so a dot-segment or absolute name escapes the destination root. | failing test | closed — `test_cli_export_dotdot_name_exits_two` and `test_cli_export_absolute_name_exits_two` call `main()` with hostile `--name` and assert exit code 2; validation at `navigate_decisions.py:1925` validates name before any join. |
| SEC-2 | Concern | Raw bidi controls reach visible HTML, and the escape set misses directional marks. | failing test | closed — `browser_checks.py::test_rendered_page_never_shows_raw_bidi_controls` (failed before the 2026-10-05 fix: titles, statuses, and relationship text rendered raw in list, detail, graph, and context; passes after) |
| SEC-3 | Concern | Provenance is put into the HTML without HTML escaping. | failing test | closed — same closure as ADV-13; `test_csp_provenance_not_in_static_html` and `test_provenance_not_interpolated_in_html` cover both the static-HTML absence and the JS textContent assignment; provenance data goes through the JSON data island and is read by JS via `D.provenance`. |
| SEC-4 | Concern | The export reads register files through a duplicate code path that reports unsafe or oversized files as absent. | failing test | closed — see ADV-9/QE-1; same tests and code fixes; `_read_register_file` now detects dangling symlinks as UnsafeContentError; the export's register exception handler now returns a dict `error` with a code field. |
| SEC-5 | Concern | Caller assertions are not checked against a schema. | failing test | closed — `test_context_non_list_assertions_refused`, `test_context_non_dict_assertion_element_refused`, `test_context_assertion_non_string_field_refused`, `test_context_valid_assertion_accepted` added; `_validate_assertions` at `navigate_decisions.py:1350` validates schema. |
| SEC-6 | Concern | SKILL.md does not declare the `filesystem_write` boundary its script crosses. | document change | closed — `packs/governance-extras/.apm/skills/navigate-decisions/SKILL.md` boundaries updated from `[filesystem_read_untrusted]` to `[filesystem_read_untrusted, filesystem_write]`; `git diff` confirms change. |
| SEC-7 | Concern | Publication is not tied to the identity of the directory that was validated, and the temporary sibling is not validated before the link. | failing test | closed — `_publish_atomically` checks `st_nlink == 1` before `os.link`; `test_publish_atomically_rejects_extra_hard_link` patches `os.stat` to return nlink=2 and asserts `OSError`; `test_validated_dir_used_for_publication` asserts output is in the resolved canonical directory. |
| SEC-8 | Nit | The repository-identity parser accepts dot-segment owner and repo names, and the host allowlist constant is never read. | failing test | closed — `test_dot_segment_owner_repo_degrades_to_inert` asserts `_parse_github_identity("https://github.com/../..")` returns None and the resulting link is inert; `_SOURCE_HOST_ALLOWLIST` is checked at line 207; dot-segment owner/repo check was already present. |
| QE-1 | Blocker | The export recomputes the summary and turns register refusals into `absent`. | failing test | closed — see ADV-9/SEC-4; `test_export_refuses_unsafe_register`, `test_export_two_table_register_sum`, and `test_export_summary_parity_with_query_summary` close this finding. |
| QE-2 | Blocker | The 400-relationship and 512 KiB non-detail limits are never enforced. | failing test | closed — see ADV-3 above; same tests and code. |
| QE-3 | Blocker | The explorer embeds raw caller dicts, so assertion text never shows. | failing test | closed — same closure as ADV-5; `test_normalize_assertion_function_output` directly calls `_normalize_assertion` for dict, non-dict, and minimal-key inputs; `test_caller_assertions_normalized_in_data_island` exports the mixed fixture and asserts raw_value, trust_class, and resolution_state in the embedded data island. |
| QE-4 | Blocker | An empty selector or one with only unknown keys matches the whole corpus. | failing test | closed — see ADV-4 above; `test_search_selector_with_only_unknown_keys_fails` directly tests this. |
| QE-5 | Blocker | The lineage tests cannot fail on depth or on traversal of unchecked edges. | mutation red | closed — `test_lineage_depth_limit_respected` uses `lineage-chain` fixture with ADR-0001→0002→0003; depth=1 asserts `ADR-0002 in ids_d1` and `ADR-0001 not in ids_d1`; depth=2 asserts `ADR-0001 in ids_d2`; `test_lineage_traverses_only_checked_relationships` asserts `ADR-0002 not in record_ids` (unchecked edges not traversed). |
| QE-6 | Concern | A Status value with two HTML comments loses everything after the first comment. | failing test | closed — see ADV-10; `test_two_html_comments_keeps_first_comment` verifies `Accepted <!-- a --> kept <!-- b -->` yields raw_value `Accepted <!-- a --> kept`; `_TRAILING_COMMENT_RE` with negative lookahead `(?!-->)` was already correct. |
| QE-7 | Concern | Badly typed query input crashes `run_query` or is silently accepted. | failing test | closed — `test_non_dict_query_returns_error_not_crash` passes string/int/None/list and asserts `status == "error"`; fix at `navigate_decisions.py:1679`: `isinstance(query, dict)` guard added. |
| QE-8 | Concern | Most refusal tests check that an error happened, not which error. | mutation red | closed — `test_unsafe_filesystem_symlink_refuses_operation`, `test_unsafe_filesystem_hard_link_refuses_operation`, `test_unsafe_filesystem_fifo_refuses_operation`, `test_traversal_attempt_refuses_operation` all now assert `payload["error"]["code"] == "unsafe_input"`. |
| QE-9 | Concern | Several inertness and encoding tests are tautologies or run on fixtures that cannot trigger them. | mutation red | closed — `test_bidi_raw_value_preserved_display_value_escaped` asserts `"‮" in raw`, `"‮" not in display`, and `"[U+202E]" in display`; fixture contains literal bidi controls; cannot pass on a fixture without them. |
| QE-10 | Concern | The no-partial-file test never reaches `os.link`. | mutation red | closed — `test_no_partial_file_on_link_failure` now calls `publish_explorer(FIXTURE, destination=tmp_path, name="no_partial.html", mode="bounded")` with valid args to reach `os.link`; `assert called_paths` ensures the mock was hit. |
| QE-11 | Concern | The parity test compares only part of the relationship data. | mutation red | closed — `test_fact_parity_relationship_tuples` now includes `raw_value` and `source` in the compared tuple; uses `mode="bounded"` to ensure the export runs on the fixture. |
| QE-12 | Nit | Export refusals carry prose only, with no machine-readable code. | failing test | closed — `publish_explorer` now returns `{"code": "...", "message": "..."}` dict for all error cases; `test_export_refusal_carries_machine_readable_code` asserts dict with `code` and `message` keys. |
| QE-13 | Concern | Source links trust whatever git repository encloses `root`, and the HTML tests run real git. | failing test | closed — `_git_root_matches(root)` extracted; `publish_explorer` uses `_git_root_matches` to decide whether to build links; HTML tests mock `_git_root_matches` directly rather than running real git. |
| QE-14 | Concern | A malformed or unknown URL hash leaves the explorer blank. | scripted Chrome check | closed — `test_empty_hash_shows_list_view` and `test_bogus_hash_shows_list_view` pass in browser_checks.py; `parseHash()` validates view name against `VALID_VIEWS` and returns `{view:'list',sel:null}` for empty or unknown hash; URIError from `decodeURIComponent` is caught and falls back to list. |
| QE-15 | Concern | The ledger's Chrome evidence scripts cannot reproduce its recorded results. | document change | closed — `bench.py` command corrected (adds `. <scratch>` args); `ux.py` policy_boundary_shown check updated to match exact boundary text; both scripts now reproduce the documented commands. |
| QE-16 | Nit | The CLI entry point has no tests. | mutation red | closed — `test_cli_query_summary_exits_zero`, `test_cli_query_unknown_record_exits_one`, `test_cli_query_invalid_selectors_json_exits_two`, `test_cli_query_operation_routes_to_run_query` added; all call `NAV.main()` directly. |
| QE-17 | Concern | Shipped pack scripts cite internal governance records, and one citation reaches every exported HTML file. | document change | closed — `grep -rn "AC-00\|docs/specs/decision" packs/governance-extras/.apm/ --include="*.py"` returns no matches; removed from both explore.py and navigate_decisions.py. |
| QE-18 | Nit | The by-path module loader is duplicated, and one copy has drifted. | lint or search | closed — `grep -n "_stat\.S_ISREG\|stat\.S_ISREG" navigate_decisions.py` shows all three occurrences use `_stat` (no bare `stat` reference); `import stat` was removed as dead code, forcing alignment; both loaders at lines 57 and 1894 use identical `_stat.S_ISREG/ISLNK` checks. |
| QE-19 | Nit | Dead code and unused names. | lint or search | closed — `make lint-ruff` reports 0 errors; `python3 -m ruff check --select F401,F811,F841 packs/governance-extras/.apm/skills/navigate-decisions/scripts/` passes; removed: `PurePath as _PP`, inline `_re`, `import stat`, `import tempfile`. |
| QE-20 | Nit | The temp file descriptor leaks if `fchmod` fails. | failing test | closed — `test_fchmod_failure_closes_fd` patches `os.fchmod` to raise, calls `_publish_atomically`, and checks fd count before/after; `fd_owned_by_fdopen` flag at `explorer.py:901` ensures the fd is closed in the finally block when fdopen has not taken ownership. |
| QE-21 | Nit | The owner-only temp-mode test checks call order, not the actual mode. | mutation red | closed — `test_temp_sibling_mode_0600_before_write` now records `actual_modes_at_fchmod` via `os.fstat(fd).st_mode` and asserts `any(m == 0o600 for m in actual_modes_at_fchmod)`; a mutation to `0o644` fails the actual-mode assertion. |
| FE-F1 | Concern | Back to the first no-hash entry leaves the previous view and selection on screen. | scripted Chrome check | closed — `test_empty_hash_shows_list_view` navigates to `#detail/ADR-0001` then clears the hash and asserts `h2` inner text equals "Corpus list"; `render()` always re-renders the full view on every `hashchange` event. |
| FE-F4 | Concern | An unknown route or unparseable data island renders a blank main area with no error. | scripted Chrome check | closed — `test_bogus_hash_shows_list_view` asserts an unknown route falls back to list; top-level try/catch on `JSON.parse` sets `document.body.textContent = 'Integrity error: ...'` on parse failure; `test_no_page_errors` asserts no uncaught JS errors on clean export. |
| FE-F2 | Nit | Focus drops to the document body after a record, edge or context button navigates. | scripted Chrome check | closed — `test_focus_management_after_navigation` passes: after hash change to detail view, `document.activeElement.tagName` is `H2`; `focusViewHeading()` sets `tabindex="-1"` on the view's h2 or h1 and calls `.focus({preventScroll:false})`. |
| FE-F3 | Nit | No live region announces result-count or no-results changes. | scripted Chrome check | closed — `test_live_region_announces_count` passes: `#live-region` textContent contains a non-empty string after list renders; `<div aria-live="polite" aria-atomic="true" id="live-region" class="sr-only">` added; `updateLive(msg)` sets `liveEl.textContent` after each `renderList()` call. |
| FE-F5 | Nit | The no-results message does not echo the active query or filters and offers no reset control. | scripted Chrome check | closed — `test_no_results_reset_button_present` passes: after filtering to zero results, `button.reset-btn` is visible and its textContent is non-empty; `renderList()` renders a reset button and echoes active filters in the no-results message. |
| FE-F6 | Nit | Edge and context buttons fall below the 24-by-24 target size, and no exception is documented. | scripted Chrome check | closed — `test_touch_target_size` passes: computed min-height and min-width for all interactive elements are ≥ 24 px; `button{min-height:24px;min-width:24px}` added to CSS; test iterates all `button,a,select,input` elements in the list view and fails if any are below threshold. |
| FE-F9 | Nit | Record buttons say they are toggles but navigate. | scripted Chrome check | closed — `test_nav_buttons_use_aria_current` passes: nav-view buttons carry `aria-current="page"` on the active view and no `aria-pressed` attribute; `render()` uses `setAttribute("aria-current","page")` and `removeAttribute("aria-current")` only; `aria-pressed` removed from static HTML and JS. |
| FE-F10 | Nit | An unknown record ID in the route shows the `nothing selected` guidance instead of saying the record is missing. | scripted Chrome check | closed — `test_unknown_record_id_shows_message` passes: detail view for an ID not in the export shows text matching `{id} is not in this export.`; JS `renderDetail()` checks `if(!rec)` and sets the main area to that message via textContent. |
| FE-F11 | Nit | Long record bodies have no progressive disclosure, and orientation scrolls away. | scripted Chrome check | closed — `test_long_body_folded` passes: a record with a 900 KB body renders its content inside a `details.body-details` element that is closed by default; JS `renderDetail()` wraps `content.length > 3000` in `<details class="body-details"><summary>Body …</summary>…</details>`. |

## T7 stage 2b evidence — explorer visual redesign

Date: 2026-10-05. Branch: `eugenelim/adr-summary`. Files changed:
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

Date: 2026-10-05. Branch: `eugenelim/adr-summary`. Files changed:
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

Result: pending (run by supervisor gates after merge).

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
    res["counts_shown"] = "238" in body
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
