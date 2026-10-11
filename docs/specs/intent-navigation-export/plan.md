# Plan: Intent navigation export

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/DESIGN.md` § Intent-edge derivation (source, copies, pins, consumers); analogous implementation: `packs/governance-extras/.apm/skills/navigate-decisions/scripts/explorer.py` with `explorer_assets/`, its tests `packs/governance-extras/tests/skills/navigate-decisions/test_html_publication.py` and the uncollected Playwright suite `browser_checks.py`, its scale and browser evidence in `docs/specs/decision-navigation/notes/verification-ledger.md`; second safety precedent `packs/core/.apm/skills/explain-diff/scripts/publish_explanation.py`. Deviations: no record bodies, so no Markdown renderer and no "bounded" body-free mode — the bounded route is `--from`; both the script and the style are hash-pinned, where the precedent allows inline style; the destination is resolved to its real path before validation instead of refusing a symlinked ancestor, because the default temporary directory on macOS sits under a symlink.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

## Approach

The payload comes first (T1): the export command builds one object from the same derivation and query functions `query` uses, so parity holds by construction and the tests confirm it. Publication safety (T2) and source links (T3) do not depend on the page and land next. The page itself (T4) is a fixed HTML shell plus one CSS and one JavaScript asset, inlined and hash-pinned. T5 measures scale, sets the budget, records the browser and activation evidence, and writes the docs and release notes. T6 is publication: after the slice pull request merges into `feature/intent-navigation`, that branch takes the default branch by merge commit, and its pull request to the default branch is opened and made green.

The riskiest part is the page's inertness and rendered behaviour, because only a browser can observe it and the browser suite is not collected by CI. T4 therefore puts every property a static check can see into collected pytest (CSP, data-block escaping, forbidden APIs, escape parity through `node`, absence of motion), and leaves the browser suite only what needs rendering.

## Constraints

- RFC-0105 D4 governs the file, its confinement, its inertness, its source links, and its bounded representation; D5 makes `notes/view-design.md` advisory. § Experiment item 2 maps to AC-0002 to AC-0005 and AC-0037 to AC-0041, item 3 to AC-0036, item 4 to AC-0015 to AC-0027, and item 5 to AC-0066.
- ADR-0007 and ADR-0074: an agent-invoked skill script, standard library only. ADR-0112: the view is generated, never committed.
- FEAT-0002 § Boundary: the view consumes the derivation and is never a second source of truth; its design route is `information-architecture` (analytical), `interaction-design`, then `frontend-engineering`.
- The catalogue authoring standards: no cross-skill imports; tests load modules under unique pack-and-skill names; any `.apm/` script that prints reconfigures both streams to UTF-8 first.
- `packs/AGENTS.md`: no internal-governance citations in shipped files (no criterion ids or `docs/specs/` paths under `.apm/`); eval updates with the pack change; self-host run twice with no diff on the second run.
- Versions: `core` stays 3.1.0 and this slice's notes fold into `## [core][3.1.0]`, per the owner decision recorded in `docs/specs/close-work-intent-graph-convergence/notes/verification-ledger.md`. `tests/roster/test_two_sided_prune_closure_invariant.py::test_pack_delivery_contract_is_complete_and_version_increased` admits one bump per release against `origin/main`.
- Publication, by owner decision on 2026-10-11: the integration branch takes the default branch by a merge commit, never a force-push or rebase, and after that merge the `navigate-intents` and `close-work` copies of `intent_delivery_relations.py` and `_file_safety.py` match the default branch's `adapter-root-bins` versions.
- Owner decisions of 2026-10-11 at the assumption checkpoint: the payload holds every intent's `record`, the full `outstanding` and `summary`, and the derivation's nodes and edges, with no bodies; the views are the summary strip, Tree, Outstanding, Refused edges, Parentless, and a detail panel, with edges as labelled lists; the scale thresholds are frozen as AC-0066 states; browser checks run locally with Playwright and are recorded in the ledger; visual authority is the `navigate-decisions` explorer's tokens.
- Owner decision of 2026-10-11 at spec review: the export refuses a destination inside any Git repository enclosing `--root` and inside every work tree of `--root`'s own repository, accepting that a user whose home directory is itself a Git repository must choose a destination outside it; the temporary-directory default is unaffected. The repository's work trees come from `git worktree list` (owner decision, same day), not from reading Git's pointer files by hand.
- `frontend-engineering` pre-flight: visual authority is `incumbent-system` for composition and values (no direction artifact covers this tool); the token namespace is that incumbent's unprefixed custom properties; genre routing loaded `information-architecture` (analytical). Page contract and state matrix are in Design below.

## Construction tests

**Integration tests:** `test_export_payload.py` drives `navigate_intents.main(["export", ...])` end to end into a temporary directory and parses the written file, so the command, payload, HTML assembly, and publication are exercised together.

**Manual verification:** the real export over this repository (AC-0068) and the scale benchmark (AC-0066), both recorded in the ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User procedure — `guides/core/how-to/navigate-intents.md` | T5 | Guide lints | Section present with codes and bounded route |
| Skill instructions and activation — `SKILL.md`, `eval_queries.json` | T5 | Self-host re-run with no diff; activation run in the ledger | Usage, refusals, prompts present |
| Pack promise — `packs/core/README.md`, `guides/core/README.md` | T5 | Row diffs | Rows name the offline view |
| Architecture — `packs/core/DESIGN.md` | T5 | Section diff | Module, assets, schema, consumer rule named |
| Release history — `docs/product/changelog.md` `[core][3.1.0]` | T5, T6 | Changelog diff; `/now/` and version tests | Entry above the default branch's newest `core` entry, dated the integration PR's day |
| Executable proof | T1–T5 | Suites green; browser suite pass with asset digests in the ledger | Run ids in the ledger |
| Verification record — `notes/verification-ledger.md` | T1–T6 | Ledger entries | Cited by both PRs |
| Advisory design — `notes/view-design.md` | written at shaping | File present | none (advisory) |
| Slice 1 closeout | T6 | Status lines and workspace diff | `lint-spec-status.py` clean |
| Design facts below | T1–T4 | Code, docstrings, tests | Mechanically inferable once merged |

## Design (LLD)

### Design decisions

- **The payload is built from query internals, not by re-running the CLI.** `navigate_intents.py` gains `build_view_payload(root, from_identity)`, which derives once and calls the same `_op_summary`, `_build_intent_record`, and outstanding builders `run_query` uses, so a record in the file is the record `query` returns. Rejected: one subprocess per intent, and a second derivation in `intent_view.py`, which would be a second source of truth. Traces to AC-0002 to AC-0008.
- **`intent_view.py` owns HTML assembly, source links, and publication, and never derives.** It receives the payload and the root, so the derivation stays in one module; its only corpus reads are the node files it hashes for source-link cleanliness, through `_file_safety.py`. `navigate_intents.py` loads it through its existing co-located loader pattern. Traces to AC-0010, AC-0023, AC-0029.
- **Facts in the page are only the payload.** The static shell interpolates no record-controlled text; the script reads the data block and builds the DOM with `createElement` and `textContent`. Traces to AC-0029 to AC-0035.
- **No drawn graph.** Edges are labelled lists grouped by type, and the tree is nested lists. A drawn graph adds a renderer and an accessibility equivalent for no question the IA names. Traces to AC-0038, AC-0042.
- **The summary strip scrolls with the page.** It is not fixed or sticky, so it cannot cover a focused element. Traces to AC-0058.

Owned by: T1, T2, T3, T4

### Component decomposition

- `navigate_intents.py`: `export` subparser; `build_view_payload`; envelope for `intent-navigation.export.v1`.
- `intent_view.py`: `build_html(payload) -> str`; `source_links(root, nodes) -> (links, commit)`; `validate_destination(root, destination, name)`; `publish(html, validated) -> path`; `EXPORT_BUDGET_BYTES`.
- `view_assets/view.css`: tokens (light, dark, system default), layout, focus styles; no motion.
- `view_assets/view.js`: data parsing and schema check, `escapeDisplay`, fixed label table, views (summary strip, Tree, Outstanding, Refused edges, Parentless), detail panel, filters, fragment routing, live-region announcements, and the `view-ready` and `list-updated` performance marks.

Owned by: T1, T2, T3, T4

### Data & schema

`intent-navigation.view.v1` data block: `schema`, `scope` (`{"from": <node id> | null}`), `provenance` (`generated_at`, `counts`, `untrusted_data`, `commit`), `summary`, `records` (object keyed by node id, in node-id order), `outstanding` (`{placed, no_parent}` or `{available: false, reason, limit}`), `nodes`, `edges`, `source_links` (object keyed by node id). It is serialised with `json.dumps(..., ensure_ascii=False, separators=(",", ":"))`, and then `<`, `>`, `&`, U+2028, and U+2029 are replaced by `\u003c`, `\u003e`, `\u0026`, `\u2028`, `\u2029`. This round-trips through `JSON.parse(textContent)` under the CSP when the file is opened from `file://`.

`intent-navigation.export.v1` stdout envelope: `schema`, `status`, then `path`, `bytes`, `scope` on `ok`, or `error` (`code`, `message`, `limits`, `observed`) on `error`.

Owned by: T1

### State & control flow

Page contract (`frontend-engineering` create mode):

| Field | Value |
| --- | --- |
| target user | Maintainer or reviewer, possibly without the repository |
| primary job | See where an intent sits and what is open under it |
| primary action | Select a node to see its facts and edges |
| expected result | Detail panel with grouped edges and a source link |
| next action | Follow an edge, or open the source |
| first-screen content | Scope banner, summary strip, view switcher, tree roots |
| product proof | Summary counts equal to the query's |
| read/write consequence | Read-only; no state leaves the page |
| critical states | content, first-run (no intents), no-results, error (damaged data), outstanding unavailable, nothing refused, no parentless intents, scoped export, large-data-set, keyboard-only, high-zoom, reduced-motion |
| responsive behavior | Two columns above 900 CSS px; one column below, detail after list |
| a11y requirements | WCAG 2.2 AA; focus moves on view switch and selection; polite live region |
| measurement event | none — offline file, no analytics |

State matrix: `loading` does not apply (the data is inline and renders in one synchronous pass); `disabled`, `success`, `permission`, `offline`, `blocked`, and `destructive-confirmation` do not apply (read-only and offline by design); `partial` is the `--from` scope banner; `long-content` and `large-data-set` are handled by collapsed subtrees and per-view lists with counts, never silent slicing. Behaviour is in `notes/view-design.md`.

Routing: fragment `#view=<tree|outstanding|refused|parentless>&node=<id>&q=<text>&level=…&kind=…&status=…`; `hashchange` re-renders, so back and forward restore view, filters, and selection.

Owned by: T4

### Behavior & rules

- **Destination.** Take `os.path.realpath` of `--destination` (default `tempfile.gettempdir()`). It must exist and be a directory, and must not equal or lie under any containment root, compared by path components: `realpath(root)`; every ancestor of it holding a `.git` entry (a directory, or the file a linked worktree or submodule uses); and every work tree of the repository `--root` is in: each `worktree` line of `git worktree list --porcelain -z`, run under the Source-links hardening, skipping entries marked `bare`, each `realpath`ed. Git resolves relative pointers, submodule and `--separate-git-dir` layouts, and `core.worktree` itself; for `--separate-git-dir` it also lists the git directory, which only adds a root. When an ancestor holds a `.git` entry and that call fails, times out, or prints nothing, the export refuses with `invalid_destination`; it never proceeds with a partial root set. On a case-insensitive file system, no ancestor of the destination may be `os.path.samefile` with a containment root. Open it with `O_RDONLY | O_DIRECTORY | O_NOFOLLOW`, compare `(st_dev, st_ino)` with the validated `lstat`, create `.intent-graph-<hex>.tmp` with `O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW` and mode `0600` through `dir_fd`, `fchmod 0600`, write, `fsync`, check it is a regular file with one link, re-check the directory identity, `os.link` to the final name through `dir_fd` (which fails on an existing name), and unlink the temporary name in `finally`. A platform without `O_NOFOLLOW`, `O_DIRECTORY`, or `dir_fd` support for `open` and `link` (`os.supports_dir_fd`) refuses with `publish_failed`; there is no non-atomic fallback.
- **Budget.** The HTML is built in memory and measured as UTF-8 bytes before any file is created.
- **Source links.** Git runs with `shell=False`, a fixed argument list, `-C <root>`, `-c core.fsmonitor=false`, `GIT_TERMINAL_PROMPT=0`, stdout and stderr both captured, and a 5-second timeout; any failure degrades to `latest` or `inert`. Calls: `worktree list --porcelain -z` (for the destination check), `rev-parse --show-toplevel`, `config --get remote.origin.url`, `rev-parse HEAD`, `rev-parse --show-object-format`, `ls-tree -r -z --full-name HEAD -- <corpus dirs>`, and `for-each-ref --contains HEAD refs/remotes/origin/` (non-empty output means `HEAD` is on `origin`). None of these refreshes the index or reads the work tree through Git, so no clean filter or fsmonitor hook runs; there is no `git status`. Cleanliness is decided in Python: each node file is read through `_file_safety.py` and hashed as a Git blob (`blob <length>\0<bytes>`, SHA-1 or SHA-256 per the object format) and compared with the blob id `ls-tree` records at its link path; a missing entry (untracked or ignored) or a mismatch gives `latest`. A commit is 40 or 64 lowercase hex characters. The link path prefix is `relpath(realpath(root), toplevel)` when it is not `.`.
- **Escape parity.** `escapeDisplay` in `view.js` uses the same code-point set as `navigate_intents._UNSAFE_CHARS` and the `[U+XXXX]` form; T4's test runs it in `node` against the Python function.
- **Labels.** Edge groups, states, and trust classes render from a fixed table in `view.js`; record text only ever fills a value cell.
- **Out-of-scope targets.** An edge target missing from `nodes` renders as text marked "outside this export".

Owned by: T2, T3, T4

### Quality attributes

- Accessibility: native controls only; `aria-expanded` on tree toggles; `aria-current` on the active view; one `h1`; landmarks; polite live region; 24×24 CSS px targets; visible `:focus-visible` outline at 3:1.
- Performance: one render pass; collapsed subtrees build their children on first expand; thresholds in AC-0066.
- Security: the CSP and data-block rules above; `rel="noopener noreferrer"` on source links.

Owned by: T4, T5

## Tasks

### T1: Export command and payload

**Depends on:** none
**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py`, `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py` (new; `build_html` and `publish` minimal enough for T1's tests), `packs/core/tests/skills/navigate-intents/test_export_payload.py` (new), `packs/core/tests/skills/navigate-intents/fixtures/hostile/` (new corpus), `docs/specs/intent-navigation-export/notes/verification-ledger.md`
**Verification mode:** TDD

**Tests:**
- AC-0001, AC-0002, AC-0003, AC-0004, AC-0005: one parametrized test over every fixture corpus that derives cleanly, discovered the way slice 1's outstanding-manifest test discovers corpora. It exports, extracts the data block by its `id="intent-data"` element, and compares against `run_query` results and `_load_graph_mod().derive(root)` with `generated_at` removed.
- AC-0006: `run_query`'s `_delivery_provider` seam, reached through the payload builder's matching keyword, returning `complete: false`.
- AC-0007, AC-0008: `mixed` fixture, `--from` on a capability with a brief and specs beneath it and a related edge leaving the subtree; the expected node and edge id sets are listed in the test, derived by hand from the fixture files.
- AC-0009: the absolute root string and the destination path are absent from the file.
- AC-0010, AC-0011: `main()` called with captured streams.
- AC-0013: `main()` over the committed `duplicate_identity` and `malformed_record` corpora and over builder-generated `unsafe_input` and `input_too_large` corpora; `resolver_unavailable` by copying the skill's `scripts/` into `tmp_path` without `intent_delivery_relations.py` and running `export` from that copy in a subprocess.
- AC-0012: `main()` run in a subprocess with a non-Git root and a Git root, asserting empty fd-level stderr.
- The hostile corpus derives cleanly; its header values carry the AC-0031 strings, so T4 reuses it.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents/test_export_payload.py -q` passes and the slice 1 suites in the same folder still pass.

### T2: Destination and atomic publication

**Depends on:** T1
**Touches:** `intent_view.py`, `packs/core/tests/skills/navigate-intents/test_export_publication.py` (new)
**Verification mode:** TDD

**Tests:**
- AC-0014: `tempfile.gettempdir` monkeypatched to a `tmp_path` subdirectory; the name checked by regex.
- AC-0015: a destination equal to the root, under it, under it through a symlink, a file, and a missing path; and a temporary Git work tree (`git init`) with the corpus at `sub/dir/`, exported with that root, refusing a destination at the top level and at a sibling `sub/other/`; a linked worktree added under its main checkout (`git worktree add`), exported from inside it, refusing a destination in the main checkout; a linked worktree added outside its main checkout, refusing a destination in the main checkout and in a second linked worktree; a linked worktree added with `-c worktree.useRelativePaths=true`, refusing a destination in its main checkout; a `--separate-git-dir` checkout exporting to the default destination successfully; an outer `git init` enclosing the repository, refusing a destination inside it; and `PATH` without `git` while a `.git` entry encloses the root, refusing; each refusal message naming the containment root.
- AC-0016: skipped unless the temporary file system is case-insensitive; it runs on macOS APFS and the run is recorded in the ledger.
- AC-0017: `a/b.html`, `x.htm`, `.x.html`, and a 101-character stem.
- AC-0018: existing file, directory, and symlink; the file's bytes and modification time compared before and after.
- AC-0019: final mode and link count; failures injected at write, `fsync`, and `link` through monkeypatched `os` functions in the module, then the directory listing is compared.
- AC-0020: the open step is monkeypatched to rename the directory and put a directory, and then a symlink, in its place.
- AC-0021: `os.supports_dir_fd` and the `O_NOFOLLOW` attribute monkeypatched away in the module.
- AC-0022: `EXPORT_BUDGET_BYTES` monkeypatched to one byte below the built size.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents/test_export_publication.py -q` passes.

### T3: Source links

**Depends on:** T1
**Touches:** `intent_view.py`, `packs/core/tests/skills/navigate-intents/test_export_source_links.py` (new)
**Verification mode:** TDD

**Tests:**
- Temporary Git repositories are built in the test with a local bare repository as `origin`, pushed, and then the remote URL is rewritten to the form under test; `for-each-ref --contains` still reads the local remote-tracking refs.
- AC-0023: the remote list in the criterion, each asserting every link `inert` and the remote text absent from the HTML; a corpus with no enclosing `.git` entry and `PATH` without `git` also gives `inert` and the export still succeeds.
- AC-0024: clean pushed `HEAD` gives `commit` with the full URL.
- AC-0025: a modified file under `docs/specs/`, an untracked spec, a spec matched by `.gitignore`, an unpushed commit, and a detached unpushed `HEAD` each give `latest`; a second remote holding `HEAD` while `origin` does not also gives `latest`.
- AC-0072: `subprocess.run` wrapped by a recording seam asserts each call's argument list, `shell`, `timeout`, and environment; the fixture repository sets `core.fsmonitor` and `filter.mark.clean` to a script writing a marker, `.gitattributes` applies `filter=mark` to the corpus, one corpus file is modified, and the marker is absent after the export.
- AC-0026: the corpus placed under `sub/dir/` of the repository and exported with that root; every URL path starts `sub/dir/`, and a clean, pushed export of it gives kind `commit` with the full commit URL.
- AC-0027: a spec directory named with `?`, `#`, `%`, and a space where the file system allows it.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents/test_export_source_links.py -q` passes.

### T4: The page

**Depends on:** T1, T3
**Touches:** `intent_view.py`, `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view.css` (new), `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view.js` (new), `packs/core/tests/skills/navigate-intents/test_export_html.py` (new), `packs/core/tests/skills/navigate-intents/view_browser_checks.py` (new, not collected), `packs/core/tests/skills/navigate-intents/fixtures/` (an empty corpus, an all-parented corpus, and a no-refusal corpus where `mixed` and `hostile` do not cover those states)
**Verification mode:** TDD for the static properties; scripted browser check for rendered ones

**Tests:**
- AC-0029, AC-0030: parse the HTML with `html.parser`, recompute both digests from the element content, assert the exact CSP string, then the element and attribute bans and no `url(` or `@import`.
- AC-0031: hostile fixture; the strings are searched in the HTML with the data block removed, and the block is decoded and compared with `run_query`.
- AC-0032: token search over `view.js` with comments stripped.
- AC-0033: `node -e` loads `view.js`'s `escapeDisplay` (exported on a test hook guarded by `typeof module`) and prints JSON for the probe set, compared with `navigate_intents._escape_display`; skipped only when `node` is absent.
- AC-0065: token search over `view.css`.
- `view_browser_checks.py`, one test per criterion for AC-0028, AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0042, AC-0043, AC-0044, AC-0045, AC-0046, AC-0047, AC-0048, AC-0049, AC-0050, AC-0051, AC-0052, AC-0053, AC-0054, AC-0055, AC-0056, AC-0057, AC-0058, AC-0059, AC-0060, AC-0061, AC-0062, AC-0063, AC-0064, AC-0069, AC-0070, AC-0071: Playwright over `mixed`, `hostile`, the three state corpora, a `--from` export, a delivery-incomplete export, and a tampered data block. Network events are recorded; CSP violations are read from `securitypolicyviolation` events and the console; keyboard-only scripts use `page.keyboard` only; the 320 px viewport checks `scrollWidth <= clientWidth`; target sizes and occlusion come from `getBoundingClientRect` and `elementFromPoint`; contrast walks every text node's computed colour and nearest opaque background in both themes; the search comparison calls `run_query` in-process for the expected ids.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents/test_export_html.py -q` passes, and `python3 -m pytest packs/core/tests/skills/navigate-intents/view_browser_checks.py -q -rs` passes locally with zero skipped tests. The browser suite fails, rather than skips, when Playwright or Chromium is missing.

### T5: Scale, activation, documentation, and release notes

**Depends on:** T2, T4
**Touches:** `packs/core/tests/skills/navigate-intents/view_bench.py` (new, not collected), `intent_view.py` (budget value only), `packs/core/.apm/skills/navigate-intents/SKILL.md`, `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json`, `guides/core/how-to/navigate-intents.md`, `guides/core/README.md`, `packs/core/README.md`, `packs/core/DESIGN.md`, `docs/product/changelog.md`, the self-host projections of `navigate-intents`, `docs/specs/intent-navigation-export/notes/verification-ledger.md`
**Verification mode:** goal-based check

**Tests:**
- AC-0066: `view_bench.py` builds N renumbered copies of this repository's intents, briefs, and spec directories (each copied whole) in a scratch repository, with slugs and ids suffixed `-cNN` and pointers rewritten, exports each, and measures in headless Chromium. The table goes to the ledger, and `EXPORT_BUDGET_BYTES` is set by AC-0022's rule.
- AC-0067: new positives and near-misses in `eval_queries.json`, run through the in-harness procedure slice 1 used (`agentbundle pack evals run --pack core --mode in-harness`), with the result in the ledger.
- AC-0068: the real export command and the browser count check, recorded in the ledger.
- After the budget value is set, the last code change of T1 to T5, the browser suite is run again with zero skips; the ledger records that commit id, the SHA-256 of `view.js` and `view.css`, and the count of tests run.
- `SKILL.md` `metadata.boundaries` is exactly `[filesystem_read_untrusted, filesystem_write]`, and the description stays under 1,024 characters.
- Guide lints, `agentbundle catalogue lint --root . --deep`, `agentbundle catalogue verify --root .`, and the shipped-text grep for criterion ids and `docs/specs/` under `packs/core/.apm/skills/navigate-intents/` return nothing.

**Done when:** each listed check passes, self-host leaves no diff on its second run, and the ledger holds the AC-0066, AC-0067, and AC-0068 entries and the final browser-suite record.

### T6: Publication

**Depends on:** T5, and the slice pull request merged into `feature/intent-navigation`
**Touches:** `feature/intent-navigation` (merge commit of `origin/main`), `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packs/product-engineering/pack.toml`, `packs/product-engineering/.claude-plugin/plugin.json`, `docs/product/changelog.md`, every `navigate-intents` and `close-work` copy of `intent_delivery_relations.py` and `_file_safety.py` and their projections, conflicted eval files, `docs/specs/intent-navigation/spec.md`, `docs/specs/intent-navigation/plan.md`, this spec and plan, `docs/product/briefs/intent-navigation-delivery.md` (Constraints wording: "brought up to date by merging the default branch"), `workspace.toml`, `docs/specs/intent-navigation-export/notes/verification-ledger.md`
**Verification mode:** goal-based check

**Tests:**
- `git merge-base --is-ancestor origin/main HEAD` on the integration branch, and the merge commit has two parents.
- `core` is 3.1.0 in both manifests, and its changelog entry sits above the default branch's newest `core` entry. `product-engineering` is 0.13.26, with its slice 3 entry renumbered above `[product-engineering][0.13.25]`. `test_pack_delivery_contract_is_complete_and_version_increased` passes.
- `cmp` of every resolver and `_file_safety.py` copy against `packs/core/.apm/adapter-root-bins/` on the merged tree; `packs/core/tests/pack/test_intent_delivery_relations_copies.py` passes.
- Slice 1 and this spec `Shipped`, both plans `Done`, both `workspace.toml` entries in `["ini-010".work]`'s shipped list, and `python .claude/skills/work-loop/scripts/lint-spec-status.py --root .` clean. These edits ride in the integration pull request and take effect when it merges.
- On the merged integration head, after the copy refresh: `view_browser_checks.py -q -rs` runs with zero skips, and the AC-0068 export is repeated; the ledger records that commit id, the SHA-256 of `view.js` and `view.css`, the test count, and the export's command, size, and counts.
- The pull request `feature/intent-navigation` → `main` has every native check green, and dispatched `test-corpus` and `test-roster` runs on its head are green, with run ids in the ledger.

**Done when:** every listed check holds, the ledger holds the post-merge browser and export record, and the pull request waits on the owner's merge decision.

## Rollout

- **Delivery:** T1 to T5 are ordered commits in one pull request into `feature/intent-navigation`. Pull-request workflows trigger only for the default branch, so `build-check`, `test-corpus`, and `test-roster` are dispatched on its last non-ledger commit and recorded in a ledger-only final commit. T6 runs on the integration branch after that merge and ends at a green pull request to the default branch, merged only on the owner's go-ahead.
- **Infrastructure and external systems:** none. The export writes only outside the repository.
- **Reversal:** revert. Nothing is persisted.

## Risks

- The browser suite runs only locally. Any code change after its final recorded run reopens the run.
- A repository whose `.git/config` is hostile can still influence what `git config` and `rev-parse` report, but it cannot extend the host allowlist, and no Git call the export makes runs a configured program.
- The default branch may move again before the owner merges. Another merge commit brings it in, and the version and changelog rules above are checked again.
- Windows lacks `dir_fd` support, so the export refuses there with `publish_failed`; the guide says so.

## Changelog
