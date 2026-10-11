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

The payload comes first (T1): the export command builds one object from the same derivation and query functions `query` uses, so parity is construction rather than comparison. Publication safety (T2) and source links (T3) are independent of the page and land next. The page itself (T4) is a fixed HTML shell plus one CSS and one JavaScript asset, inlined and hash-pinned. T5 measures scale, sets the budget, runs the browser and activation evidence, and writes the docs and release entry. T6 is publication: after the slice pull request merges into `feature/intent-navigation`, that branch takes the default branch by merge commit and its pull request to the default branch is opened and made green.

The riskiest part is the page's inertness and rendered behaviour, because only a browser can observe it and the browser suite is not collected by CI. T4 therefore pushes every property a static check can see into collected pytest (CSP, data-block escaping, forbidden APIs, escape parity through `node`, contrast), leaving the browser suite only what needs rendering.

## Constraints

- RFC-0105 D4: one self-contained file in a scratch location; confined reads; inert record content; no automatic network request; source links only through a validated `https` mapping with an in-code host allowlist; a bounded representation when too large. D5: `notes/view-design.md` is advisory. § Experiment items 2 to 5 map to AC-0002/AC-0003/AC-0024, AC-0023, AC-0010 to AC-0016, and AC-0029.
- ADR-0007 and ADR-0074: an agent-invoked skill script, standard library only. ADR-0112: the view is generated, never committed.
- FEAT-0002 § Boundary: the view consumes the derivation and is never a second source of truth; its design route is `information-architecture` (analytical), `interaction-design`, then `frontend-engineering`.
- The catalogue authoring standards: no cross-skill imports; tests load modules under unique pack-and-skill names; any `.apm/` script that prints reconfigures both streams to UTF-8 first.
- `packs/AGENTS.md`: no internal-governance citations in shipped files (no criterion ids or `docs/specs/` paths under `.apm/`); eval updates with the pack change; self-host run twice with no diff on the second run.
- Versions: `core` stays 3.1.0 and this slice's notes fold into `## [core][3.1.0]`, per the owner decision recorded in `docs/specs/close-work-intent-graph-convergence/notes/verification-ledger.md`; `tests/roster/test_two_sided_prune_closure_invariant.py::test_pack_delivery_contract_is_complete_and_version_increased` admits one bump per release against `origin/main`.
- The brief's publication constraint, as the owner set it on 2026-10-11: the integration branch takes the default branch by merge commit (no force-push, as `cd6da752e` did), and the `navigate-intents` and `close-work` copies of `intent_delivery_relations.py` and `_file_safety.py` match the default branch's `adapter-root-bins` versions after that merge.
- `frontend-engineering` pre-flight: visual authority is `incumbent-system` for both composition and values (the `navigate-decisions` explorer's tokens, extended — no direction artifact covers this tool); token namespace is that incumbent's unprefixed custom properties; genre routing `information-architecture` loaded (analytical). Page contract and state matrix are in Design below.

## Construction tests

**Integration tests:** `test_export_payload.py` drives `navigate_intents.main(["export", ...])` end to end into a temporary directory and parses the written file, so the command, payload, HTML assembly, and publication are exercised together.

**Manual verification:** the real export over this repository (AC-0031) and the scale benchmark (AC-0029), both recorded in the ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User procedure — `guides/core/how-to/navigate-intents.md` | T5 | Guide lints | Section present with codes and bounded route |
| Skill instructions and activation — `SKILL.md`, `eval_queries.json` | T5 | Self-host re-run with no diff; activation run in the ledger | Usage, refusals, prompts present |
| Pack promise — `packs/core/README.md`, `guides/core/README.md` | T5 | Row diffs | Rows name the offline view |
| Architecture — `packs/core/DESIGN.md` | T5 | Section diff | Module, assets, schema, consumer rule named |
| Release history — `docs/product/changelog.md` `[core][3.1.0]` | T5, T6 | Changelog diff; `/now/` and version tests | Entry above the default branch's newest `core` entry, dated the integration PR's day |
| Executable proof | T1–T5 | Suites green; browser suite pass in the ledger | Run ids in the ledger |
| Verification record — `notes/verification-ledger.md` | T1–T6 | Ledger entries | Cited by both PRs |
| Advisory design — `notes/view-design.md` | written at shaping | File present | none (advisory) |
| Slice 1 closeout | T6 | Status lines and workspace diff | `lint-spec-status.py` clean |
| Design facts below | T1–T4 | Code, docstrings, tests | Mechanically inferable once merged |

## Design (LLD)

### Design decisions

- **The payload is built from query internals, not by re-running the CLI.** `navigate_intents.py` gains `build_view_payload(root, from_identity)` which derives once and calls the same `_op_summary`, `_build_intent_record`, and outstanding builders `run_query` uses, so a record in the file is the record `query` returns by construction. Rejected: shelling out per intent (168 processes) and a second derivation in `intent_view.py` (a second source of truth). Traces to AC-0002 to AC-0005.
- **`intent_view.py` owns HTML assembly, source links, and publication; it never reads the corpus.** It receives the payload and the root, so the derivation stays in one module. Loaded by `navigate_intents.py` through its existing co-located loader pattern. Traces to AC-0007, AC-0015, AC-0018.
- **Facts in the page are only the payload.** The static shell interpolates no record-controlled text; the script reads the data block and builds the DOM with `createElement` and `textContent`. Traces to AC-0018 to AC-0022.
- **No drawn graph.** Edges are labelled lists grouped by type; the tree is nested lists. A drawn graph adds a renderer and an accessibility equivalent for no question the IA names. Traces to AC-0024, AC-0025.

Owned by: T1, T2, T3, T4

### Component decomposition

- `navigate_intents.py`: `export` subparser; `build_view_payload`; envelope for `intent-navigation.export.v1`.
- `intent_view.py`: `build_html(payload) -> str`; `source_links(root, nodes) -> (links, commit)`; `validate_destination(root, destination, name)`; `publish(html, validated) -> path`; `EXPORT_BUDGET_BYTES`.
- `view_assets/view.css`: tokens (light, dark, system default), layout, focus styles; no motion.
- `view_assets/view.js`: data parsing and schema check, `escapeDisplay`, fixed label table, views (summary strip, Tree, Outstanding, Refused edges, Parentless), detail panel, filters, fragment routing, live-region announcements.

Owned by: T1, T2, T3, T4

### Data & schema

`intent-navigation.view.v1` data block: `schema`, `scope` (`{"from": <node id> | null}`), `provenance` (`generated_at`, `counts`, `untrusted_data`, `commit`), `summary`, `records` (object keyed by node id, in node-id order), `outstanding` (`{placed, no_parent}` or `{available: false, reason, limit}`), `nodes`, `edges`, `source_links` (object keyed by node id). Serialised with `json.dumps(..., ensure_ascii=False, separators=(",", ":"))`, then `<`, `>`, `&`, U+2028, U+2029 replaced by `<`, `>`, `&`, ` `, ` `; the spike at shaping showed this round-trips through `JSON.parse(textContent)` under the CSP from `file://`.

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
| critical states | content, first-run (no intents), no-results, error (damaged data), outstanding unavailable, nothing refused, large-data-set, keyboard-only, high-zoom, reduced-motion |
| responsive behavior | Two columns above 900 CSS px; one column below, detail after list |
| a11y requirements | WCAG 2.2 AA; focus moves on view switch and selection; polite live region |
| measurement event | none — offline file, no analytics |

State matrix: `loading` not applicable (data is inline, one synchronous render); `disabled`, `success`, `permission`, `offline`, `blocked`, `destructive-confirmation` not applicable (read-only, offline by design); `partial` is the `--from` scope banner; `long-content` and `large-data-set` handled by collapsed subtrees and per-view lists with counts, never silent slicing. Behaviour is in `notes/view-design.md`.

Routing: fragment `#view=<tree|outstanding|refused|parentless>&node=<id>&q=<text>&level=…&kind=…&status=…`; `hashchange` re-renders, so back and forward restore view, filters, and selection.

Owned by: T4

### Behavior & rules

- **Destination.** `os.path.realpath` of `--destination` (default `tempfile.gettempdir()`), then: must exist and be a directory; must not equal or lie under `realpath(root)`, compared by path components, and on a case-insensitive file system no ancestor of the destination is `os.path.samefile` with the root. Open it with `O_RDONLY | O_DIRECTORY | O_NOFOLLOW`, compare `(st_dev, st_ino)` with the validated `lstat`, create `.intent-graph-<hex>.tmp` with `O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW` and mode `0600` through `dir_fd`, `fchmod 0600`, write, `fsync`, check regular file with one link, `os.link` to the final name through `dir_fd` (fails on an existing name), unlink the temporary name in `finally`. Re-check the directory identity before linking. Without `dir_fd` support, fall back to `O_EXCL` creation of the final name and unlink on failure.
- **Budget.** The HTML is built in memory and measured as UTF-8 bytes before any file is created.
- **Source links.** Git is run with `shell=False`, a fixed argument list, `-C <root>`, `-c core.fsmonitor=false`, `GIT_TERMINAL_PROMPT=0`, and a 5-second timeout; any failure degrades to `latest` or `inert`. Calls: `rev-parse --show-toplevel`, `config --get remote.origin.url`, `rev-parse HEAD`, `status --porcelain -- docs/product/intents docs/product/briefs docs/specs`, `branch -r --contains HEAD`. The commit is accepted as 40 or 64 lowercase hex characters.
- **Escape parity.** `escapeDisplay` in `view.js` uses the same code-point set as `navigate_intents._UNSAFE_CHARS` and the `[U+XXXX]` form; T4's test runs it in `node` against the Python function.
- **Labels.** Edge groups and states render from a fixed table in `view.js`; record text is only ever a value cell.

Owned by: T2, T3, T4

### Quality attributes

- Accessibility: native controls only; `aria-expanded` on tree toggles; `aria-current` on the active view; one `h1`; landmarks; polite live region; 24×24 CSS px targets; visible `:focus-visible` outline at 3:1.
- Performance: one render pass; collapsed subtrees build children on first expand; thresholds in AC-0029.
- Security: CSP and data-block rules above; `rel="noopener noreferrer"` on source links.

Owned by: T4, T5

## Tasks

### T1: Export command and payload

**Depends on:** none
**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py`, `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py` (new, payload-facing stub of `build_html` only), `packs/core/tests/skills/navigate-intents/test_export_payload.py` (new), `packs/core/tests/skills/navigate-intents/fixtures/hostile/` (new corpus), `docs/specs/intent-navigation-export/notes/verification-ledger.md`
**Verification mode:** TDD

**Tests:**
- AC-0001, AC-0002, AC-0003: one parametrized test over every fixture corpus that derives cleanly, discovered the way slice 1's outstanding-manifest test discovers corpora; it exports, extracts the data block with a regex on the `id="intent-data"` element, and compares against `run_query` results and `_load_graph_mod().derive(root)` with `generated_at` removed.
- AC-0004: `run_query`'s `_delivery_provider` seam, through the payload builder's matching keyword, returning `complete: false`.
- AC-0005: `mixed` fixture, `--from` on a capability with a brief and specs beneath it; expected node and edge sets written by hand in the test.
- AC-0006: the absolute root string and `tmp_path` are absent from the file.
- AC-0007, AC-0008: `main()` called with captured streams; one case per slice 1 negative corpus code; `capsys` asserts empty stderr.
- The hostile corpus derives cleanly; its header values carry the AC-0019 strings, so T4 reuses it.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents/test_export_payload.py -q` passes and the slice 1 suites in the same folder still pass.

### T2: Destination and atomic publication

**Depends on:** T1
**Touches:** `intent_view.py`, `packs/core/tests/skills/navigate-intents/test_export_publication.py` (new)
**Verification mode:** TDD

**Tests:**
- AC-0009: monkeypatched `tempfile.gettempdir` to a `tmp_path` subdirectory; name pattern by regex.
- AC-0010: destination equal to the root, under it, under it through a symlink, a file, and a missing path; case-variant case skipped unless the temporary file system is case-insensitive (it runs on macOS APFS; the run is recorded in the ledger).
- AC-0011: bad names (`a/b.html`, `x.htm`, `.x.html`, 101-character stem) and existing file, directory, and symlink; the existing file's bytes and mtime unchanged.
- AC-0012: final mode and link count; failure injected at write, `fsync`, and `link` through monkeypatched `os` functions in the module, then the directory listing is empty.
- AC-0013: the directory is swapped by monkeypatching the open step to rename it and put a directory and then a symlink in its place.
- AC-0014: `EXPORT_BUDGET_BYTES` monkeypatched to one byte below the built size.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents/test_export_publication.py -q` passes.

### T3: Source links

**Depends on:** T1
**Touches:** `intent_view.py`, `packs/core/tests/skills/navigate-intents/test_export_source_links.py` (new)
**Verification mode:** TDD

**Tests:**
- AC-0015: temporary Git repositories built in the test with a bare `origin` whose URL is then rewritten to a GitHub form: clean pushed `HEAD` gives `commit`; a dirty file under `docs/specs/`, an unpushed commit, and a nested root each give `latest`; a path with `?`, `#`, `%`, and a space is percent-encoded per segment.
- AC-0016: the remote list in the criterion, each asserting every link `inert` and the remote text absent from the HTML.
- Git absent: `PATH` without `git` gives `inert` and the export still succeeds.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents/test_export_source_links.py -q` passes.

### T4: The page

**Depends on:** T1, T3
**Touches:** `intent_view.py`, `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view.css` (new), `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view.js` (new), `packs/core/tests/skills/navigate-intents/test_export_html.py` (new), `packs/core/tests/skills/navigate-intents/view_browser_checks.py` (new, not collected)
**Verification mode:** TDD for the static properties; scripted browser check for rendered ones

**Tests:**
- AC-0018: parse the HTML with `html.parser`, recompute both digests from the element bytes, assert the exact CSP string, the element and attribute bans, and no `url(` or `@import`.
- AC-0019: hostile fixture; the strings are searched in the HTML with the data block removed; the block is decoded and compared with `run_query`.
- AC-0020: token search over `view.js` with comments stripped.
- AC-0021: `node -e` loads `view.js`'s `escapeDisplay` (exported on a test hook guarded by `typeof module`) and prints JSON for the probe set; compared with `navigate_intents._escape_display`. Skipped only when `node` is absent; GitHub's Ubuntu runners have it.
- AC-0028: parse the custom properties for each theme from `view.css` and compute WCAG relative-luminance ratios for the pairs listed in the test; assert no `transition`, `animation`, `@keyframes`.
- `view_browser_checks.py` (AC-0017, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027): Playwright over `mixed`, `hostile`, an empty corpus, and a tampered data block; network events recorded; CSP violations read from `securitypolicyviolation` events and console; keyboard-only scripts use `page.keyboard` only; 320 px viewport checks `scrollWidth <= clientWidth`; target sizes from `getBoundingClientRect`; the search comparison calls `run_query` in-process for the expected ids.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents/test_export_html.py -q` passes, and `python3 -m pytest packs/core/tests/skills/navigate-intents/view_browser_checks.py -q` passes locally with its run recorded in the ledger.

### T5: Scale, activation, documentation, and release notes

**Depends on:** T2, T4
**Touches:** `packs/core/tests/skills/navigate-intents/view_bench.py` (new, not collected), `intent_view.py` (budget value only), `packs/core/.apm/skills/navigate-intents/SKILL.md`, `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json`, `guides/core/how-to/navigate-intents.md`, `guides/core/README.md`, `packs/core/README.md`, `packs/core/DESIGN.md`, `docs/product/changelog.md`, the self-host projections of `navigate-intents`, `docs/specs/intent-navigation-export/notes/verification-ledger.md`
**Verification mode:** goal-based check

**Tests:**
- AC-0029: `view_bench.py` builds N renumbered copies of this repository's intents, briefs, and specs in a scratch repository (slugs and ids suffixed `-cNN`, pointers rewritten), exports each, and measures in headless Chromium; the table goes to the ledger; `EXPORT_BUDGET_BYTES` is set by AC-0014's rule.
- AC-0030: new positives and near-misses in `eval_queries.json`, run through the in-harness procedure slice 1 used (`agentbundle pack evals run --pack core --mode in-harness`), result in the ledger.
- AC-0031: the real export command and the browser count check, recorded in the ledger.
- `SKILL.md` `metadata.boundaries` gains `filesystem_write`; the description stays under 1,024 characters.
- Guide lints, `agentbundle catalogue lint --root . --deep`, `agentbundle catalogue verify --root .`, and the shipped-text grep for criterion ids and `docs/specs/` under `packs/core/.apm/skills/navigate-intents/` return nothing.

**Done when:** each listed check passes, self-host leaves no diff on its second run, and the ledger holds the AC-0029, AC-0030, and AC-0031 entries.

### T6: Publication

**Depends on:** T5, and the slice pull request merged into `feature/intent-navigation`
**Touches:** `feature/intent-navigation` (merge commit of `origin/main`), `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packs/product-engineering/pack.toml`, `packs/product-engineering/.claude-plugin/plugin.json`, `docs/product/changelog.md`, every `navigate-intents` and `close-work` copy of `intent_delivery_relations.py` and `_file_safety.py` and their projections, conflicted eval files, `docs/specs/intent-navigation/spec.md`, `docs/specs/intent-navigation/plan.md`, this spec and plan, `docs/product/briefs/intent-navigation-delivery.md` (Constraints wording: "brought up to date by merging the default branch"), `workspace.toml`, `docs/specs/intent-navigation-export/notes/verification-ledger.md`
**Verification mode:** goal-based check

**Tests:**
- `git merge-base --is-ancestor origin/main HEAD` on the integration branch, and the merge commit has two parents.
- `core` is 3.1.0 in both manifests and its changelog entry sits above the default branch's newest `core` entry; `product-engineering` is 0.13.26 with its slice 3 entry renumbered above `[product-engineering][0.13.25]`; `test_pack_delivery_contract_is_complete_and_version_increased` passes.
- `cmp` of every resolver and `_file_safety.py` copy against `packs/core/.apm/adapter-root-bins/` on the merged tree; `packs/core/tests/pack/test_intent_delivery_relations_copies.py` passes.
- Slice 1 and this spec `Shipped`, both plans `Done`, both `workspace.toml` entries in `["ini-010".work]`'s shipped list, and `python .claude/skills/work-loop/scripts/lint-spec-status.py --root .` clean.
- The pull request `feature/intent-navigation` → `main` has every native check green, and dispatched `test-corpus` and `test-roster` runs on its head green, run ids in the ledger.

**Done when:** every listed check holds and the pull request waits on the owner's merge decision.

## Rollout

- **Delivery:** T1 to T5 are ordered commits in one pull request into `feature/intent-navigation`. Pull-request workflows trigger only for the default branch, so `build-check`, `test-corpus`, and `test-roster` are dispatched on its last non-ledger commit and recorded in a ledger-only final commit. T6 runs on the integration branch after that merge and ends at a green pull request to the default branch, merged only on the owner's go-ahead.
- **Infrastructure and external systems:** none. The export writes only outside the repository.
- **Reversal:** revert. Nothing is persisted.

## Risks

- The browser suite runs only locally. A change to `view.js` after its recorded run reopens the run.
- The default branch may move again before the owner merges; another merge commit, not a rebase, brings it in, and the version and changelog rules above are re-checked.
- `git` subprocess behaviour differs on Windows; source links degrade to `inert` there rather than fail.

## Changelog
