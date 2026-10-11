# Verification ledger: intent navigation export

## T1

- The derivation reads header lines with `str.splitlines`, so a U+2028 or U+2029 inside a
  header value ends that line and the rest is dropped; neither character can reach a
  record, node, or edge value, and a spec directory named with U+2028 is not admitted as a
  spec. The committed `hostile` corpus therefore carries U+2028 and U+2029 in header text
  (the value is cut at the separator), and the data-block escaping of both characters is
  proved on a constructed payload in `test_build_html_escapes_line_separators_and_markup`.
  AC-0031's wording ("headers carry ... a U+2028 line separator") is not satisfiable
  through the derivation as written.
- `hostile` carries an `expected-outstanding.json`, so slice 1's manifest-discovery tests
  also run over it.
- `build_html`, `publish`, and `source_links` in `intent_view.py` are the minimal T1 forms:
  an unstyled document with only the data block, exclusive-create publication, and every
  source link `inert`. T2, T3, and T4 replace them.

## T2

- Gates: `python -m pytest packs/core/tests/skills/navigate-intents/ -q` gave 386 passed, 4 skipped
  (the 4 skips are in other suites; `test_export_publication.py` alone gave 40 passed, 0 skipped).
  `make lint-ruff lint-mypy` pass. `agentbundle catalogue self-host --root . --write --force`
  run twice (second run changed nothing); `agentbundle catalogue verify --root .` ok.
- AC-0016 ran, not skipped, on this macOS APFS machine (git 2.50.1): the probe
  `CaseProbe` / `caseprobe` resolved to one directory, and `Root/Inner` was refused when given
  as `root/inner`. The component-wise comparison does not catch it (macOS `realpath` keeps the
  spelling); the `samefile` check against each ancestor of the destination does.
- Observed Git behaviour pinned by the tests: for a `--separate-git-dir` main checkout and a
  submodule, `git worktree list` lists the git directory, not the checkout, and does not mark
  it `bare`. The listing therefore belongs to `--root` by the second form (the `.git` file's
  `gitdir:` target equals an entry). A linked worktree of a `--separate-git-dir` repository
  accepts its main checkout, as the accepted limit says.
- `intent_view.py` T1 source held literal U+2028 and U+2029 characters as the escape-table
  keys; they are now ` ` and ` ` escapes with the same value.
- `publish` now takes the `Destination` that `validate_destination` returns. The budget check,
  the platform-support check, and all file creation happen inside `publish`, after validation.
- A test that wraps `os.open` must also add the wrapper to `os.supports_dir_fd`, because the
  platform check compares `os.open` by identity.

## T3

- AC-0027 as written asks for a spec directory named with `?`, `#`, `%`, and a space. The
  derivation admits only slug-shaped spec directory names (such a directory yields no spec
  node), so the test puts those characters in the corpus root's directory name below the Git
  top level, which is part of every link path, and asserts `%3F`, `%23`, `%25`, `%20` in the
  commit URL. `_encode_path` is also tested directly.
- `ls-tree` is limited to the three corpus directories `docs/product/intents`,
  `docs/product/briefs`, and `docs/specs` (the only places a node path can be), passed as
  pathspecs relative to `--root`; `--full-name` makes the output paths top-level relative,
  which is how the link path is formed.
- A node file that is a symlink or a submodule entry in HEAD's tree, a failed or oversized
  read, or an unloadable `_file_safety.py` all give `latest`, never an exception.
- Gates: `python -m pytest packs/core/tests/skills/navigate-intents/ -q` passed (see commit
  report for counts); `make lint-ruff lint-mypy` pass; self-host run twice, second no diff;
  `agentbundle catalogue verify --root .` ok.

## T4

- Code commits: `9490629c5` (page, assets, empty fixture) and `0b8dd0c33` (tests). Chromium 153.0.8010.12 (Playwright, headless).
- Asset digests (SHA-256): `view.js` `93d4d39d4b9ed81e6c1a7d8817eaf10cf7a550cc1c9559bf993b7bd9696733a7`; `view.css` `823d4bf4c130075b6d75b97f9ef279a8a629391d21447aed9c85f5da719f996d`.
- Static suite: `test_export_html.py` 6 passed (CSP and both digests, element and attribute bans, hostile strings outside the data block, forbidden script tokens, `node` escape parity over every unsafe code point plus its neighbours, no motion in the stylesheet). The whole `navigate-intents` folder: 427 passed, 4 skipped (the four skips are the slice 1 whole-operation-failure corpora, unchanged).
- Browser suite `view_browser_checks.py -q -rs`: 40 tests run (35 criteria; AC-0058, AC-0059 at 320 and 1280 px, AC-0064 in four theme setups), 0 skipped, 0 failed, 8.2 s. A mutation check (escape disabled, muted text colour lightened) made AC-0034 and AC-0064 fail, so those checks bite.
- Gates: `make lint-ruff lint-mypy` pass; self-host run twice with an identical tree; `catalogue verify` ok; `catalogue lint --deep` has no `navigate-intents` finding; no `uv.lock`.
- Real export over this repository (AC-0068 preview, not the final record): `export --root .` wrote 564,451 bytes outside the repository; in Chromium the summary strip read 196 outstanding, 0 refused, 100 parentless, 168 intents, 23 briefs, 547 specs, and the Tree view listed 168 intents after expanding every subtree. Screenshot `/tmp/s4-real-repo-detail.png` (not in the repository): header and summary strip on top, view switcher and filters at the left over the tree, the selected intent's facts, "Open on GitHub" link with the "may be newer than this export" mark, and grouped edges at the right; focus ring on the detail heading is a 3 px blue outline.
- Observations: (1) No all-parented corpus exists: the derivation always leaves one root, so AC-0053 is checked on the empty corpus and on a valid export whose data block was rewritten so every record has a resolved parent. (2) The `mixed` corpus has no refused edge, so it is the no-refusal corpus and a separate fixture was not added. (3) `view.js` holds the GitHub prefix as one fixed literal (corrected in review round 1; an earlier note said it was assembled in parts). That text is fixed asset text, not remote text under AC-0023, and the page only builds a link for a URL that starts with it; the slice 3 inert test checks that no remote-derived text reaches an inert page. (4) The CSP blocks Playwright's string predicates, so the suite passes functions to `wait_for_function`. (5) Keyboard selection in the level filter is by type-ahead; arrow keys do not change a closed select in headless Chromium on macOS.

## T5

### Scale (AC-0066)

- Command: `python packs/core/tests/skills/navigate-intents/view_bench.py` (Chromium 153.0.8010.12, headless, macOS, `--enable-precise-memory-info` so heap is not bucketed). Each corpus is N copies of this repository's 168 intents, 23 briefs, and 547 specs (each spec directory copied whole), slugs, directory names, and file stems suffixed `-cNN`, and every `Slug:`, `Parent intent:`, `Brief:`, `Discovery:`, `Related intents:`, and `Superseded by:` value rewritten. The scratch tree is a Git repository with a GitHub `origin` and one empty commit, so every source link is the larger `latest` shape. Each copy is a self-consistent graph: the exported summary scales exactly with N (at N=2: 336 intents, 46 briefs, 1,094 specs, 392 outstanding, 200 parentless, 0 refused edges), and the search `graph` lists 5 intents at N=1 and 10 at N=2.
- Startup is the median of 3 cold loads in fresh contexts; search is the median of 5 runs from the first `keydown` of typing `graph` to the last `list-updated` mark; heap is `usedJSHeapSize` after the fifth search.

| Copies | `outstanding` available | File bytes | Startup ms | Search ms | Heap MiB | Meets every threshold |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | yes | 583,603 | 9 | 6 | 4 | yes |
| 10 | no (`resource_limit`, limit `files`) | 4,561,808 | 32 | 36 | 12 | yes |
| 25 | no (`resource_limit`, limit `files`) | 11,332,678 | 70 | 87 | 19 | yes |
| 50 | no (`resource_limit`, limit `files`) | 22,617,456 | 121 | 177 | 45 | yes |

- Thresholds: file at most 104,857,600 bytes, startup at most 3,000 ms, search at most 300 ms, heap at most 1,024 MiB. The corpora that meet every threshold are the 1, 10, 25, and 50 times corpora. No threshold fails, so `EXPORT_BUDGET_BYTES` stays 104,857,600 and `intent_view.py` is unchanged.
- At 10 times and above the delivery resolver reaches its file limit, so `outstanding` is `{"available": false, ...}`; the Outstanding list and per-intent delivery relations are therefore not exercised at scale. The measured search, startup, and heap cover the Tree and the filters, which is where the work is.

### Activation (AC-0067)

- Description: 1,015 characters (limit 1,024), every existing routing signal kept; it now routes an offline HTML export of the intent graph or outstanding work here and names HTML views of ADRs and RFCs as `navigate-decisions`. `metadata.boundaries` is `[filesystem_read_untrusted, filesystem_write]`.
- New queries in `eval_queries.json`: 5 positives ("Export the intent graph as an HTML file I can open offline", "Give me a shareable offline view of outstanding work", "Make a self-contained HTML page of our intent hierarchy", "Create an HTML view of the intent graph I can send to a reviewer", "Export the outstanding work under this capability as a single HTML file") and 4 near-misses (ADR and RFC HTML or offline explorer, index, and browser prompts). The file now holds 45 queries (25 positive, 20 negative).
- Procedure as slice 1: each query 3 times per detector, each run a fresh tool-less process started in an empty directory (`claude -p --safe-mode --disable-slash-commands --tools ""`; `codex exec -s read-only --ephemeral --skip-git-repo-check -m gpt-5.5 -`), each seeing the descriptions of every `core` skill plus `navigate-decisions` and the query as a delimited block, one call at a time with up to two retries, graded with `agentbundle pack evals run --pack core --mode in-harness --reports <file>`. Fidelity is `reported`: a description-match judgement, not the real router.
- Claude Code 2.1.296: `navigate-intents: 45/45 queries passed`, 0 errored runs. All 5 new positives at trigger rate 1.00; all 4 new near-misses at 0.00, routed to `navigate-decisions`.
- Codex 0.142.5 with `-m gpt-5.5`: `navigate-intents: 43/45 queries passed`, 0 errored runs. All 9 new prompts pass (positives 1.00, near-misses 0.00, routed to `navigate-decisions`). The 2 failures are slice 1 queries: "What work is still open?" routed to `workspace-status` and "What brief links to this spec?" to `author-delivery-brief`, both at rate 0.00. They fail the same way under the unchanged pre-slice description (re-run 3 times each: `workspace-status` x3; `repository-exploration`, none, `workspace-status`), so the cause is the detector, not this edit. Slice 1's 35/35 on Codex used the CLI's default model, which this account now rejects ("model not supported when using Codex with a ChatGPT account"); `gpt-5.5` was the model that ran.

### Real export (AC-0068)

- Command: `python packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py export --root . --destination /tmp/s4real --name real.html` at `8b735ea84`, exit 0, `status: ok`, `/private/tmp/s4real/real.html`, 564,441 bytes, mode 0600, outside the repository (the temporary directory; not committed).
- Opened from `file://` in headless Chromium: summary strip 196 outstanding, 0 refused edges, 100 parentless, 168 intents, 23 briefs, 547 specs; after expanding every subtree the Tree view reads "168 intents", has 168 intent links, and all 168 live intent ids in the payload's `records` appear in the tree text (0 missing).

### Final browser run

- Budget unchanged, so the last code change of T1 to T5 is `93f18fdcc` (the `view.js` GitHub prefix fix); T5 added no code under `.apm/` besides skill text. `python -m pytest packs/core/tests/skills/navigate-intents/view_browser_checks.py -q -rs` at `8b735ea84`: 40 passed, 0 skipped, 0 failed, 8.4 s.
- SHA-256 `view.js` `52d4b4ce50a65148d8db56a8849a4acdb85fedfc6c171f65d9bdbf66d9800867`; `view.css` `823d4bf4c130075b6d75b97f9ef279a8a629391d21447aed9c85f5da719f996d`. The T4 entry's `view.js` digest (`93d4d39d...`) predates `93f18fdcc`; this one supersedes it.

### Gates

- `python -m pytest packs/core/tests/skills/navigate-intents/ -q`: 427 passed, 4 skipped (the slice 1 whole-operation-failure corpora). `python -m pytest packs/core/tests/pack/ -q`: 416 passed. `tests/roster/test_skill_census.py`, `test_verification_ledger_contract.py`, `test_cognitive_load_repository_contract.py`, `test_two_sided_prune_closure_invariant.py`: passed.
- `make lint-ruff lint-mypy` pass. Guide lints (`lint-guide-titles.py`, `validate_guides.py`, `lint-guides-no-repo-only-refs.py`) pass. Self-host run twice, second run changed nothing; `catalogue verify` ok; `catalogue lint --deep` has no `navigate-intents` finding; no `uv.lock`. No criterion id or `docs/specs/` path appears in `SKILL.md`, the guide, or either README.

## Review round 1 fixes

Post-gates review round 1, sustained findings only. Final `view.js` SHA-256 `f95747ed832be5d2f32aae48552f7f520f22557a205eef060505156f4290bcbc`; `view.css` `88f4ca1f84d929de8f74cee659f5314a3db54f1c9c368d6084247036655e2a5a` (these supersede the T4 and T5 digests). Browser suite `view_browser_checks.py -q -rs`: 49 passed, 0 skipped.

- Adversarial 1 (Blocker, relation on a non-`intent:` node shown as "outside this export"): `view.js` resolves a relation's `intent:<slug>` to the exported node with that slug (`intentNodeId`) in the relation line; the payload is unchanged. Proof: `test_delivery_relation_on_a_non_intent_node_renders_as_a_link` (an opportunity corpus built in the test; the relation keeps `intent:beta-feat`, the node is `opportunity:beta-feat`; the link renders on the opportunity and on its brief, no "outside" mark, and the link opens the node). A row built when a subtree opens now also carries `aria-current` (found by the back-to-list test).
- Adversarial 2 and QE 5 (stale prefix comment, ledger note): comment and the T4 observation above now describe the single literal.
- Adversarial 3 (guide `boundary` claim): limited to `query` responses; the guide says `export` carries none. Adversarial 4 (`invalid_query`): named, with its non-UTF-8 cause, in the guide's export table sentence and in SKILL.md's refusal list.
- Adversarial 5 (shipped-text grep scope): `grep -rnE "AC-[0-9]{4}|docs/specs" packs/core/.apm/skills/navigate-intents/` returns 5 hits, none a criterion id and none a governance citation: `intent_view.py:206` (`_LINK_DIRS`), `intent_delivery_relations.py:564` and `:566` (resource-limit scope names), `intent_graph.py:481` and `:782` (corpus-path prefixes). Each is a corpus-path code literal.
- Security 1 (lazy fetch): `_git_run` adds `-c protocol.allow=never` to every export Git call; env wording unchanged. Proof: `test_a_treeless_clone_never_starts_a_lazy_fetch` (a `--filter=tree:0` clone of a local bare repository whose upload-pack writes a marker; a control `ls-tree` without the flag writes the marker, the export does not, and links degrade to `latest`). Removing the flag makes it fail. The AC-0072 argument-list assertions in both hardening tests include the new pair.
- QE 1 (`publish_failed`): guide row and SKILL.md entry name the OS write-failure cause and the remedy; `error.observed` carries `stage` and the errno name, never a path. Proof: `test_publish_failed_names_the_stage_and_errno_without_a_path`.
- QE 2 (race tests), mutated on a scratch copy under `/tmp`: `test_directory_replaced_after_the_temporary_file_links_nothing` fails when the pre-link `_same_directory` re-check is removed (the file is linked into the moved directory); `test_entry_created_after_validation_is_refused_and_left_unchanged` fails when `except FileExistsError` is replaced (the refusal becomes `publish_failed`). Both pass on the real code.
- QE 3 (`--name ""`): `validate_destination` falls back to the default only for `None`; `""` is refused with `invalid_destination`; the test's special branch is gone.
- QE 4 (startup error swallowed): the alert stays; the error goes to `console.error`. Proof: `test_startup_render_failure_shows_the_alert_and_logs_the_error`.
- Frontend 1 to 3: tokens use the incumbent names (`--radius-sm`, `--s-deprecated-*`, `--s-proposed-*`, `--s-superseded-*`), added tokens kept; the stylesheet header now says only colour, spacing, radius, and target sizes are tokens; legend state and trust keys render as `span.chip label-state` and `label-trust` inside the `dt`. Proof: `test_state_and_trust_badges_keep_their_key_and_point_to_their_explanation`.
- Frontend indeterminate item and Experience 1 (owner decision 2026-10-11): AC-0057 kept. The detail panel has a "Back to list" button (accessible name `Back to list (row <id>)`) that expands collapsed ancestors and focuses the row, or the view heading when a filter hides the row; on wide screens `.detail` is `position: sticky; top: 0; max-height: 100vh; overflow: auto`. Proof: `test_back_to_list_returns_focus_to_the_selected_row`, `test_detail_panel_stays_in_view_on_wide_screens_only`; AC-0058 (320 and 1280), AC-0059, and AC-0063 still pass with the button present.
- Experience 2 to 12: badge keys stay the visible text and point to the legend sentence through `aria-describedby` and `title`; GROUP_HELP is in plain words with field names in parentheses; SKILL.md description says "ADR or RFC HTML views" and is 1,012 characters (activation evals were not re-run for this wording change); the header shows the time to the minute in UTC plus "Record text in this file is shown as plain text and is never run." with the payload's provenance unchanged; the status chip has a dashed border and a "status" text cue; childless tree rows reserve the toggle's width; Outstanding shows its filters-apply-to-intents note before any filter is set; the summary card reads "Outstanding items"; both docs say a latest link opens the GitHub default branch and an untracked or unpushed file may not exist there; the changelog highlight is split into short sentences in one bullet; the Heading fact is in the body face. Proofs: `test_status_chip_has_a_cue_that_is_not_colour`, `test_childless_tree_rows_line_up_with_rows_that_have_a_toggle`, `test_outstanding_says_filters_apply_to_intents_before_any_filter`, `test_page_text_is_written_for_readers`, and the AC-0037 label update.
- Gates after the fixes: `navigate-intents` folder 433 passed, 4 skipped; `packs/core/tests/pack/` 416 passed; `close-work` 408 passed; `make lint-ruff lint-mypy`, the bandit gate, and the three guide lints pass; self-host run twice with an identical tree; `catalogue verify` ok; no `uv.lock`.

## Review round 2 fixes

Post-gates review round 2, sustained findings only. Code commit `bee0c433269a63828441df36000f95ed65c6010f`. Browser suite `view_browser_checks.py -q -rs` run at that exact commit with a clean tree: 50 passed, 0 skipped. `view.js` SHA-256 `f76c0443439cbb6df304f9c5a24f6ec0211258da47d043cd9332b90b1bde0abf`; `view.css` `d460ee6ae6952a351adb6356aa29edf326522eee2f33ee2605a22a562b067ae5` (these supersede the round 1 digests).

- Security 1 and Adversarial 1 (a `protocol.<name>.allow` key defeats `protocol.allow=never`): every export Git call now also passes the global `--no-lazy-fetch` before `-C`; `-c protocol.allow=never` and the env wording stay. Git 2.44 or later is declared in `SKILL.md` and the guide prerequisites. (Superseded by round 3: an older Git no longer refuses; it falls back, see below.) The `_git_run` docstring is corrected. Proof: `test_a_treeless_clone_never_starts_a_lazy_fetch`, whose fixture now sets `protocol.file.allow=always`; the AC-0072 argument assertions in `test_git_calls_are_hardened` and the link hardening test include the new option. Mutation (run on the working copy and then restored, not a scratch copy): removing `--no-lazy-fetch` makes the test fail; with it, it passes. On Git 2.50.1, `protocol.allow=never` alone lazy-fetched under that key and `--no-lazy-fetch` refused (rc 128).
- Adversarial 2 (browser record lacked a commit id): this entry names the commit, the digests, and the count.
- Adversarial 3 and Experience 2 (docs said every link opens the default branch): both docs say an unmarked link opens the file at the exported commit, and a link marked "may be newer than this export" opens it on the GitHub default branch, where an untracked or unpushed file may not exist yet; one fact per sentence.
- Experience 1 and Frontend 1 (detail panel not keyboard-reachable): `<div class="detail">` is `tabindex="0" role="region" aria-labelledby="detail-heading"`; `.detail:focus-visible` joins the focus-ring list; sticky behaviour is unchanged. Proof: `test_detail_panel_is_a_named_tab_stop_that_scrolls_to_the_legend_end` (1280 by 900, no selection: the region is in the Tab order with the name "Details" and PageDown brings the last legend row into view; it fails without the attributes). The AC-0058 sweep now probes the part of a focused element inside the viewport, because a tall static panel at 320 wide has its centre below the fold. AC-0058 and AC-0061 pass; AC-0061 still counts one each of `h1`, `header`, `nav`, `main`.
- Experience 4 (Back to list with no row): focus stays on the view heading and the polite live region reads "This item is not in the current list." Proof: the hidden-row step of `test_back_to_list_returns_focus_to_the_selected_row`.
- QE 1 (unreachable relation-index mapping): `rel.intent` is passed unchanged to the index; the relation-line mapping stays. The round 1 wording above is corrected.
- Gates: `navigate-intents` folder 433 passed, 4 skipped; `packs/core/tests/pack/` 416 passed; `close-work` 408 passed; `make lint-ruff lint-mypy`, the bandit gate, and the three guide lints pass; self-host run twice with an identical tree; `catalogue verify` ok; no `uv.lock`.

## Review round 3 fixes

Post-gates review round 3, sustained findings only. The code commit and browser record are at the end of this section.

- Adversarial 1 (older Git refusal), owner decision 2026-10-11 supersedes the proposed remedy wording: older Git falls back safely instead of refusing. `intent_view.py` probes once per export with `git --no-lazy-fetch version` (same scrubbed environment, no shell, timeout; cached for the process, which is one export). When Git accepts the option, every call carries `--no-lazy-fetch` as before. When Git starts and rejects it (older than 2.44), `worktree list --porcelain -z` still runs without the option, so the destination check and its refusals are unchanged; `ls-tree` and `for-each-ref --contains`, the two calls that read objects, are skipped, so links are `latest` for a recognised remote or `inert`. `-c protocol.allow=never`, `-c core.fsmonitor=false`, and the `GIT_` scrub stay on every call. Reasoning that the calls that still run read no objects: `worktree list` reads the worktree administrative files and refs; `rev-parse --show-toplevel` reads the directory layout; `config --get` reads config; `rev-parse HEAD` resolves a ref name to a hash without opening the object; `rev-parse --show-object-format` reads config. None opens a commit, tree, or blob, so none can reach a promisor remote. A Git that cannot start behaves as before (the probe reports supported, and the later calls fail as they did). Proof: `test_older_git_exports_with_latest_links_and_reads_no_objects` (a `git` shim on `PATH` that rejects `--no-lazy-fetch`; an export into a directory outside the enclosing repository succeeds, every link is `latest`, the commit is none, the recording seam sees one probe and no `ls-tree` or `for-each-ref`, no `--no-lazy-fetch` on any later call, and `worktree list` once) and `test_unsupported_probe_seam_keeps_destination_check` (probe seam reports unsupported; a destination inside the repository is still refused). The supported path keeps `test_a_treeless_clone_never_starts_a_lazy_fetch` and the AC-0072 argument assertions, which now also check the single probe call. Mutations: replacing the skip guard in `source_links` with `True`, and always adding `--no-lazy-fetch`, each make the older-Git test fail; both restored. Docs: the guide prerequisite and `SKILL.md` say Git 2.44 or later gives commit-pinned links and an older Git still exports with every link marked "may be newer than this export".
- Experience 1 and 2 (link marks): guide and `SKILL.md` say a link marked "at commit ..." opens the file at the exported commit, a link marked "may be newer than this export" opens it on the GitHub default branch, every link carries the second mark when the exported commit is not on origin, when any intent file differs from it, or when Git is older than 2.44, and an untracked or unpushed file may not exist there yet. The word "unmarked" is gone. No test: prose only; the marks already exist in `view.js` and are covered by the source-link browser test.
- Experience 4 (stale live region): `backToList` clears `dom.live.textContent` before writing "This item is not in the current list." No new test; the existing hidden-row step of the back-to-list test still passes.
- Frontend 1 (ring outside the viewport): `.detail:focus-visible` is split from the shared selector with `outline-offset: calc(-1 * var(--outline))`; the other rings are unchanged. Proof: the tab-stop browser test now computes the ring box (border box grown by offset plus width) at 1280 by 900 and requires it inside the viewport, with two pixels of slack because focusing can scroll the page by a sub-pixel amount. Mutation: setting the offset back to `2px` makes it fail (ring top at -6.1, bottom at 903.9); restored.
- QE nit (legend scroll): the legend loop also requires the last row inside the viewport (`top >= 0`, `bottom <= innerHeight + 1`). Removing `max-height` and `overflow` from the sticky `.detail` rule did not fail that condition alone, because the page then scrolls instead, so the test also requires the region's own `scrollTop > 0` after the scroll. Mutation: with the rule removed (and the ring assertion bypassed to isolate it) the test fails on `scrollTop` 0; restored.
- Gates: `navigate-intents` folder 435 passed, 4 skipped; `packs/core/tests/pack/` 416 passed; `close-work` 408 passed; `make lint-ruff lint-mypy`, the bandit gate over the skill and its tests, and the three guide lints pass; self-host run twice with an identical tree; `catalogue verify` ok; no `uv.lock`; no criterion id or `docs/specs/` path in `SKILL.md` or the guide.

Browser record: code commit `1a5975d5321376565d253e14a97f316a75ebfe3d`; `view_browser_checks.py -q -rs` run at that exact commit with a clean tree: 50 passed, 0 skipped. `view.js` SHA-256 `ef5fa99a0eb54121a8028146edf4541f45b9c33ae9214869734cef842ed0c690`; `view.css` `e76d4990aa6fc080af8419275fa7b1f48dd272f82359afb828baeb665f4b540c` (these supersede the round 2 digests).
