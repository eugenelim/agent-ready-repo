# Plan: Intent view readiness bridge

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** RFC-0108 D3; `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py` `run_export`, `build_view_payload`, `_build_cli_parser` and the `_load_view_mod` loader pattern (a co-located module loaded by path under a unique name); `scripts/intent_view.py` `_SCRIPT_PARTS` and `data_block_json`; `view_src/lists.js` `startableIds` and `brokenEntries`, `view_src/list-bodies.js` `bodyNext` and `brokenRow`; `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` `_canonical_projection` and `_canonical_failure_payload` (the input's producer), and `workspace_status_engine.py` `_FINDING_NEXT_ACTIONS`; tests `test_independence.py` `test_workspace_toml_absent_present_unreadable_give_identical_results`, `view_browser_checks.py` `_export`, `_rewrite` and `Opened`. Deviation: the export gains its first non-Git input, standard input, under the checks of spec AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011 and AC-0012.

## Approach

Seven tasks in two review units. Unit A (T1 to T3) is the trust boundary, all in Python and all decided by collected tests: the readiness module first, as pure functions over bytes, because its checks are the security control. Then its wiring into `export`, then the hostile `workspace.toml` fixture through the real `workspace-status`. Unit B (T4 to T7) renders the projection, checks layout, and closes with docs, version and measurements. The riskiest part is the start mark: it must be decided over the checked lists before dropping, or a dropped first-ready entry silently moves the mark onto the wrong record. T1 tests that case directly, and spec AC-0021 pins it with an example.

## Constraints

- RFC-0108 D3: piped input only; the export never runs `workspace-status`, locates it or reads `workspace.toml`; size cap, schema version, mode, root and typed lists; allowlisted projection; locators, unconfined paths and every other field dropped; unknown `next_action` as inert text under a generic label; data-block escape and hostile fixtures; bridge data marks only loaded records; a failed check leaves readiness unchecked and the export succeeds; "ready" only for the canonical ready set; the argless mark follows `work-loop`'s order.
- RFC-0108 D1 rules 8 to 10, as corrected by its 2026-10-16 errata entry: every width and theme, WCAG 2.2 AA, inert and offline under the shipped content-security policy.
- The source-and-style spec's criteria 0001 to 0010 keep holding: one hashed script joined from parts, at most 400 lines a part, the banned-API scan, and the layout sheet's limits.
- `packs/AGENTS.md`: self-host after edits; bump `pack.toml` and `.claude-plugin/plugin.json` together; no internal-governance citations under `packs/`; update the skill's eval harness; reconfigure output streams to UTF-8.
- ADR-0007 and ADR-0074: a standard-library-only skill script; no build step for the view.

## Construction tests

**Integration tests:** `test_export_readiness.py` drives `nav.run_export` with pipe and file descriptors through a `readiness_stream` seam. `view_browser_checks.py` exports through `_export` with that seam and opens each export through `Opened`.
**Manual verification:** the real-input corpus, the real export, the 32 screenshots, the `experience-reviewer` pass and a visual-polish pass, recorded in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Amended-in-part headers | T7 | Header lines in every spec the spec's Durable Outputs row names | Each names this spec and what it amends there |
| User guide | T7 | `notes/guide-draft.md` merged into the guide section; guide lints | Pipe command, the three page states, and the never-runs-it boundary described |
| Skill instructions and eval | T7 | SKILL.md sections; self-host no diff; eval case | Pipe instruction present; eval case present |
| Core design note | T7 | `packs/core/DESIGN.md` paragraph | Bridge, projection and the unchanged `workspace.toml` boundary named |
| Changelog and version | T7 | Fragment; both version files | Fragment validates at the bumped version |
| Verification ledger and screens | T1, T7 | Ledger; `notes/screens/` | Cited by the PR |
| Coordination | T7 | `workspace.toml` entry; Spec map row | Follows spec status |

## Design (LLD)

### Design decisions

Traces to: AC-0013, AC-0014, AC-0018, AC-0020, AC-0021, AC-0049.

Owned by: T1, T2

- **One new module, `scripts/intent_readiness.py`.** The trust boundary sits in one file a security review reads whole, rather than inside the 2,800-line `navigate_intents.py`. It is loaded with the `_load_view_mod` pattern (by path, as a regular non-symlink file, under a unique module name), and `run_export` loads it on every export, with or without `--readiness`, so both open the same files (AC-0020).
- **The projection and the mark are decided in Python.** The page receives only the projected member, so no raw status byte reaches the HTML, and the view never decides readiness.
- **A pinned copy of the finding table.** `intent_readiness.py` holds `_KNOWN_FINDINGS`, a copy of `workspace-status`'s code-to-sentence table, because a skill may not import from another. A collected test reads the source table with `ast.literal_eval` on the `_FINDING_NEXT_ACTIONS` assignment in `workspace_status_engine.py`, without executing that file, and fails on any difference. A new upstream code therefore reds the suite. Meanwhile the view stays safe, because an unknown pair renders under the generic label.
- **A held mark, by owner decision on 2026-10-21.** `work-loop`'s Step 0 says a matching `canonical.findings` entry blocks autonomous start, and a top-level finding can name a ready path whose own evaluation is clean, such as a dependent's `unsatisfied_dependency` naming its prerequisite. So the mark is withheld whenever any finding's `path` equals the chosen entry's path (AC-0049), and the page never claims a start that `work-loop`'s own text might refuse. The shaping-item guard reads `workspace.toml` and stays out of reach; the spec's Assumptions record that residual.
- **Fail closed per input, drop per entry.** A failed check unchecks all readiness, because a partly trusted input is not trusted. A well-formed entry that names nothing loaded is dropped, because D3 requires unconfined and unloaded paths to go while the rest still marks.

### Data & schema

Traces to: AC-0003, AC-0004, AC-0005, AC-0014, AC-0021.

Owned by: T1, T2

The payload member and the result field are the shapes the spec states. `readiness.blocked[].findings[].next_action` is the input's string unchanged; `data_block_json` escapes it with the rest of the payload. Node ids come from a `{path: id}` map over the payload's `nodes`, built after `--from` scoping, so a scoped export marks only its scope.

### Interfaces & contracts

Traces to: AC-0001, AC-0002, AC-0006, AC-0007, AC-0046, AC-0047.

Owned by: T1, T2

- `--readiness` is a free-text option on the `export` parser. An argparse `choices` list would exit 2.
- `run_export` gains `readiness: str | None = None` and `readiness_stream: Callable[[], int | None] | None = None`. It refuses any `readiness` other than `None` and `"-"` with `invalid_query`, alongside its shipped UTF-8 argument check and before anything else runs (AC-0001). It hands `readiness_stream` to `read` only when `readiness == "-"`. `main` passes a callable that returns `sys.stdin.fileno()`, or `None` when `sys.stdin` is `None`. `read` calls it inside its own catch, so an exception from `fileno()`, such as `io.UnsupportedOperation`, gives `unreadable`. The annotation is `Callable[[], int | None]`. Tests pass a callable that returns a pipe's read descriptor. Nothing touches standard input otherwise (AC-0002).
- `intent_readiness.read(opener, limit, deadline_seconds)` returns the bytes or a reason. It first calls `opener()` for the descriptor `fd`. It returns `unreadable` for a `None` descriptor or when `os.fstat` raises, and also for a directory. It returns `empty` without reading when `os.isatty(fd)` is true. Otherwise a daemon thread loops `os.read(fd, min(65536, limit + 1 - len(buffer)))` into a buffer until end of file or `limit + 1` bytes, so the total read never passes `limit + 1`, while the caller waits with `thread.join(deadline_seconds)`. The thread's target catches every exception from `os.read` and records it in a shared slot, so nothing reaches `threading.excepthook` or standard error. After the join, a recorded exception gives `unreadable` and the buffer is discarded unread. `os.read` holds no `BufferedReader` lock, so a thread still blocked when the process exits cannot deadlock interpreter shutdown, as a thread reading `sys.stdin.buffer` can. A thread still alive at the deadline gives `timed_out`, and its buffer is never read again; more than `limit` bytes give `too_large`. `READ_DEADLINE_SECONDS = 60` and `INPUT_LIMIT_BYTES = 4_194_304` are module constants. Tests shorten the deadline through the `deadline_seconds` argument and assert both constants' values.

### Component / module decomposition

Traces to: AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0032 and AC-0033.

Owned by: T1, T4, T5

- `intent_readiness.py`: `read`, `check` (returns the checked lists or a reason), `project(checked, path_to_id)` and `start(checked, path_to_id)`.
- `view_src/readiness.js`, a new part placed after `lists.js`: `readinessChecked()`, `readinessGroups()`, `startTagText(id)`, `startLine()`, and the reason-sentence table.
- `data.js` validates the member's shape. A member that fails is read as unchecked with `wrong_schema`, never as a damaged payload, so a hand-edited file still opens.
- `lists.js`: `brokenEntries` adds `{holder, workspace: {code, next_action, known}}` entries. `list-bodies.js`: `bodyNext` branches on `readinessChecked()`, and `brokenRow` renders the workspace context. `detail-render.js` renders AC-0031's lines. `labels.js` and `chrome.js` carry the new labels and Key rows.
- `view-base.css` gains `.mark[data-mark="ready"]` on `--c-ok`/`--c-ok-bg` and `.mark[data-mark="blocked"]` on `--c-bad`/`--c-bad-bg`, the token file's values. `view.css` gains only the start tag's spacing.

### State & control flow

Traces to: AC-0001, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0021, AC-0048, AC-0050.

Owned by: T1, T2

`run_export` validates every argument, including `--readiness`, before reading anything. It then reads the stream, builds the payload, attaches `project(...)` or the unchecked member, builds the HTML and publishes. Inside `check`, the order is the spec's AC-0012 order:
1. `read` gives `unreadable`, `timed_out` or `too_large`.
2. Bytes that are empty after stripping ASCII space, tab, LF and CR give `empty`.
3. UTF-8 strict decode. A leading U+FEFF is refused, because `json.loads` rejects a byte-order mark.
4. `json.loads` with an `object_pairs_hook` that raises on a repeated name and a `parse_constant` that raises on `NaN`, `Infinity` and `-Infinity`. `RecursionError` and `ValueError`, which covers the integer-digit limit, are caught as `not_json`.
5. A top-level object whose `workspace_present` is `False` gives `no_workspace`.
6. The typed walk, including the surrogate scan of each `next_action`.
7. The workspace-failure codes.

`start` reads the checked lists before `project` drops anything. With `--readiness -`, `run_export` first builds the unchecked baseline from the payload, `generated_at` included, and measures `len(html.encode("utf-8"))`, the same UTF-8 byte count `publish` refuses on. A baseline over `EXPORT_BUDGET_BYTES` refuses with `export_too_large` before anything else is built, raising the same `ViewRefusal` fields `publish` builds, with the baseline's byte count as `observed.bytes` (AC-0050). Otherwise it builds the page with the real `readiness` member. When readiness is checked and that page's UTF-8 size is over the budget, it writes the page with `{"checked": false, "reason": "page_too_big"}` instead (AC-0048). An unchecked page is never larger than the baseline, because every reason token is ASCII and no longer than `not_requested`, so every page written after a baseline that fits is within the budget, and `publish`'s own refusal never fires on that path. The budget is read through a module attribute so a test can lower it. `_provenance` takes its time from a module-level `_now()` so a test can pin the clock.

### Failure, edge cases & resilience

Traces to: AC-0010, AC-0013, AC-0015, AC-0017, AC-0048, AC-0050.

Owned by: T1, T2

Any exception raised inside `check`, `project` or `start` becomes `wrong_schema`, and any `OSError` or `ValueError` inside `read` becomes `unreadable`. No exception the status input causes reaches `run_export`'s caller, and nothing is written to standard error (AC-0013). Tests drive every branch, so this catch is not where a bug hides. A lone surrogate is refused in the typed walk (AC-0010), so a projected string always encodes as UTF-8 in `publish`. A path in more than one list is `wrong_schema`. A repeat within `canonical.blocked` is lawful, because `workspace-status` emits one evaluation per membership and a duplicate membership gives two.

### Quality attributes (NFRs)

Traces to: AC-0039, AC-0040, AC-0041, AC-0042.

Owned by: T4, T6, T7

Subheadings reuse the "What has no parent?" subheading style. The start tag is a meta-text span inside the row link that wraps under the name at narrow widths, so it adds no breakpoint. Any transition reuses the shipped motion block under `prefers-reduced-motion: no-preference`. Projection cost is linear in the input: one parse and one pass, with a dictionary lookup per entry.

## Tasks

### T1: The readiness module and the real-input corpus

**Depends on:** none

**Mode:** TDD

**Tests:**
- Criteria: AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0014, AC-0017, AC-0018, AC-0021, AC-0046, AC-0047, AC-0049.
- First, record the real-input corpus. Save this repository's `status` and `reconcile` outputs at the task's starting commit, plus the hostile `workspace.toml` probe output, under the gitignored `.context/`. Run `check` and `project` over them, and record in the ledger each input's SHA-256, its accepted or refused reason, and its counts. Today's expectation: `status` checked with 0 active, 0 ready and 31 blocked records carrying 43 codes, rule `none`; `reconcile` refused as `wrong_schema`. A result that contradicts a criterion stops the task for a spec amendment under the Ask-first rule.
- `test_export_readiness.py` holds a table of named byte streams, one per check case of AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0046 and AC-0047. The oracle for each is the reason the spec names; the reasons are not read from the module.
- AC-0006's limit cases build the base status padded with spaces to exactly 4,194,304 and 4,194,305 bytes. The never-ending case writes into an `os.pipe()` from a thread until the reader stops, and asserts no more than 4,194,305 bytes were read.
- AC-0047's cases hold an `os.pipe()` write end open with zero bytes and with 100 bytes written, call `read` with `deadline_seconds=0.5`, and assert `timed_out` within 2 seconds. A separate assertion pins `READ_DEADLINE_SECONDS == 60`.
- AC-0046 passes openers returning `None`, a closed descriptor, a descriptor opened on `tmp_path` with `os.open(..., os.O_RDONLY)`, a file opened `O_WRONLY`, an empty `os.pipe()` read end set non-blocking with `os.set_blocking(fd, False)` while its write end stays open for the whole read, and an opener that raises `io.UnsupportedOperation`. It captures standard error with `capfd` and asserts it is empty. AC-0007's terminal case uses `os.openpty()` and asserts that nothing was read.
- The start-rule tests build checked lists over `mixed` paths, including AC-0021's dropped-first-ready example, a two-active list where one path is unloaded, and AC-0049's held example, plus a held case where the finding sits in another entry's `findings`.
- `test_readiness_vocabulary_matches_workspace_status` compares `_KNOWN_FINDINGS` with the `ast.literal_eval` of `workspace_status_engine.py`'s `_FINDING_NEXT_ACTIONS`, located from the test file through the repository's `packs/core/.apm/skills/workspace-status/scripts/` path.

**Done when:** `test_export_readiness.py`'s module tests pass under the collected run, and the ledger holds the corpus entry.

### T2: `export --readiness -` and the payload member

**Depends on:** T1

**Mode:** TDD

**Tests:**
- Criteria: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0013, AC-0015, AC-0016, AC-0019, AC-0020, AC-0034, AC-0048, AC-0050.
- AC-0001 and AC-0002 run `main` in a child interpreter whose standard input is an open, never-written pipe, under a 30-second timeout: with `--readiness foo` it returns `invalid_query`, and with no flag it returns `ok`.
- AC-0013 runs every failing case of T1's table through `run_export`, plus a `\ud800` next-action case, with standard error captured. It compares each payload with a no-flag export of the same corpus, with `provenance.generated_at` and `readiness.reason` removed from both, and asserts that standard error is empty. AC-0048 pins `_now()` to one instant, exports without `--readiness` to measure the page's UTF-8 size, lowers the budget to exactly that size, and then runs AC-0048's over-budget checked input, whose not-known `next_action` values are multi-byte text, and every failing case of T1's table under it. Each must meet AC-0013 in full: `ok`, exit 0, file written, empty standard error, and a payload equal to the pinned-clock no-flag payload with `readiness.reason` and `provenance.generated_at` removed. AC-0050 repeats those runs with the budget one byte below the no-flag size and expects `export_too_large` with no file written, `error.limits.budget_bytes` equal to the lowered budget, `error.limits.bounded_route` equal to `--from`, and `error.observed.bytes` equal to the measured baseline size. The closed-standard-input case runs `main` in a child interpreter whose descriptor 0 is closed before it starts, through `sh -c 'exec 0<&-; exec "$0" "$@"'`, so `sys.stdin` is `None`.
- AC-0015 checks the data block and the text of a headless parse of the page with its script and style elements removed. The browser-rendered half is in T4. AC-0016 searches the whole HTML file for each marker string.
- AC-0019 extends `test_workspace_toml_absent_present_unreadable_give_identical_results`'s four workspace states to the export with one fixed status input.
- AC-0020 runs two exports, with and without `--readiness -`, each in a child `python -I` that installs a `sys.addaudithook`. The hook records `open` paths and every process-start event: `subprocess.Popen`, `os.system`, `os.exec`, `os.spawn`, `os.posix_spawn`, `os.fork`, `os.forkpty` and `os.startfile`. The test then compares the sets. A child process is used because an audit hook cannot be removed.
- AC-0034 reuses export criterion 0031's string list and its outside-the-data-block scanner from `test_export_html.py`.

**Done when:** those tests, the rest of `test_export_readiness.py`, and the shipped `test_export_*.py` and `test_independence.py` suites pass.

### T3: The hostile `workspace.toml` fixture

**Depends on:** T2

**Mode:** TDD

**Tests:**
- Criteria: AC-0038.
- `fixtures/hostile_workspace/workspace.toml` holds valid TOML in the shape of the T1 probe: a `[backlog].open` intent entry, an `["ini-001".work]` queue and active spec, and an entry whose path carries `<img src=x onerror=alert(1)>`. Every free-text field and `ref` carries export criterion 0031's strings. The test copies `mixed` and this file into `tmp_path`.
- The status output comes from loading `workspace_status.py` by path under a unique name and calling `main(["status", "--root", <copy>])` with standard output captured. The test asserts the output contains the hostile strings, so the fixture cannot silently stop exercising the drop.
- Discovery predicate: if `workspace-status` stops accepting the fixture, the test's own assertion that readiness is checked reds. The fixture is then revised to an input that `workspace-status` accepts, not loosened.

**Done when:** the AC-0038 test passes in the collected run.

### T4: "What can I work on next?" with readiness

**Depends on:** T2

**Mode:** visual / manual QA (scripted browser check)

**Tests:**
- Criteria: AC-0015, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0036, AC-0037.
- `_with_readiness(name, status_obj)` exports `mixed`, or a named corpus, with the status object's bytes written to a temporary file whose read descriptor `readiness_stream` returns. Named status objects: `start` (two ready, one blocked), `resume` (one active), `ask` (two active), `outside` (AC-0021's example), `held` (AC-0049's example), `none` (only blocked), `empty_lists`, `all_dropped`, and one failing input per reason that a byte stream can produce. `page_too_big` comes from T2's lowered-budget seam.
- AC-0015's rendered half reads `document.body.innerText` after every question and pick.
- AC-0027 collects the glyph of every state-mark element and Key entry, the Key opened, for every named status object, for one whose not-known `next_action` holds ▶ and ■, and for the no-flag export.
- AC-0036 collects every `href` and, by picking each record, every prompt block's text, with and without readiness over the same corpus.
- AC-0037 reads the shipped `Opened` request and policy-violation evidence after `_visit_everything` plus opening the Key.

**Done when:** those tests, and the full `view_browser_checks.py` run, pass with none skipped.

### T5: Workspace findings in "What is broken?", detail and Key

**Depends on:** T4

**Mode:** visual / manual QA (scripted browser check)

**Tests:**
- Criteria: AC-0030, AC-0031, AC-0032 and AC-0033, AC-0035.
- AC-0030's unavailable-`outstanding` case reuses the shipped `_incomplete` resolver seam with a checked status object.
- AC-0032 uses a status object built as that criterion states.
- AC-0033 runs the shipped closed-label scan over the `hostile` corpus with a checked status object naming `spec:hostile-spec`, with the label set extended as the criterion lists.
- AC-0035 reuses the shipped text-node escape scanner on an export whose not-known `next_action` carries each escaped code point.

**Done when:** those tests, and the full `view_browser_checks.py` run, pass with none skipped.

### T6: Layout and access across the readiness matrix

**Depends on:** T5

**Mode:** visual / manual QA (scripted browser check)

**Tests:**
- Criteria: AC-0039, AC-0040.
- One status object holds an active, a ready and a blocked entry, with the start tag. Its blocked finding has a 64-character code and a 500-code-point not-known `next_action`. The test parametrises over the eight readiness-matrix cells and reuses the shipped geometry, target-size, contrast and focus helpers that session-start criteria 0034 to 0038 and 0041 use.
- AC-0040 reads computed durations under `reduced_motion="reduce"`.

**Done when:** those tests, and the full `view_browser_checks.py` run, pass with none skipped.

### T7: Docs, version, measurements and review evidence

**Depends on:** T3, T6

**Mode:** goal-based check, then visual / manual QA

**Tests:**
- Criteria: AC-0041, AC-0042, AC-0043, AC-0044 and AC-0045.
- `view_bench.py` gains `--readiness <file>`, which pipes a saved status output into each export. Run `view_bench.py --source . --counts 1 10 25 50 --readiness <this repository's status output>` at the final code commit; the ledger records its table.
- AC-0042's input is generated by a ledger-recorded script that repeats blocked entries over this repository's loaded spec paths up to exactly 4,194,304 bytes.
- AC-0043 and AC-0044 re-run the T1 corpus at the final code commit. The independent counting script is written from the spec's terms, not from `intent_readiness.py`.
- Screenshots of the four states across the readiness matrix go to `notes/screens/`, with SHA-256 values in the ledger. They feed the `experience-reviewer` pass and a separate visual-polish pass.
- A `test-corpus.yml` dispatch at the final code commit passes; the ledger records its run id.
- A collected content check in `test_export_readiness.py` reads `navigate-intents/SKILL.md` and asserts that § Export an offline view holds the pipe command with the `status` subcommand and `--readiness -`, and that § Safety controls holds the rule that no other `workspace-status` subcommand is piped and that the output passes straight into the export unread.
- Goal checks: `tools/lint-guide-titles.py`, `tools/validate_guides.py` and `tools/lint-guides-no-repo-only-refs.py`; `FORCE=1 make build-self` twice with no second diff; `tools/changelog.py` validation of the new fragment; the `packs/AGENTS.local.md` citation grep over `packs/`.

**Done when:** each goal check above exits 0, and the ledger holds the bench table, the corpus counts, the screenshot hashes and the review dispositions.

## Rollout

Ships in the next `core` patch release. Nothing migrates. Without `--readiness -` the export behaves as before, apart from the payload's `readiness` member and the result's `readiness` field, both reading `not_requested`. An export made before this release has no member, and the view reads that as not checked.

## Risks

- Windows PowerShell 5.1 re-encodes native-command pipes. `workspace-status` writes ASCII-only JSON, so the bytes survive, but a different encoding default could add a byte-order mark, which reads as `not_json`. The SKILL.md instruction names POSIX shells and PowerShell 7, and the failure notice tells the reader how to check by hand.
- A snapshot can go stale between export and use. The lead line ties readiness to the snapshot time, and `work-loop` re-checks readiness before it starts.
- `workspace-status` may add a finding code. The vocabulary test reds the suite, and until the copy is refreshed the page shows that finding under "Note from workspace-status".

## Changelog

- 2026-10-21: spec approved by eugenelim
- 2026-10-21: plan approved by eugenelim
