# Spec: Intent navigation export

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105, ADR-0007, ADR-0074, ADR-0112
- **Brief:** brief:intent-navigation-delivery
- **Discovery:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer or reviewer runs one `navigate-intents export` command and gets a single HTML file, written outside the repository, that opens offline and shows the whole intent graph — every intent, brief, and spec header fact and every parent, pointer, delivery, related, and refused edge the query returns — so they can answer what sits under an intent, what is outstanding, which intents have no parent, and which pointers are broken, then open each source file. The file holds exactly the facts the query returns over the same corpus, runs no record-provided content, makes no network request on opening, and stays usable by keyboard at WCAG 2.2 AA and at 50 times today's corpus.

## What Changes

- New `export` command on the skill's script — `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py`.
- New view builder and publisher — `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py`.
- New hand-written view assets (one CSS file, one JavaScript file) — `packs/core/.apm/skills/navigate-intents/scripts/view_assets/`.
- Export usage, refusals, and activation prompts — the skill's `SKILL.md` and `evals/eval_queries.json`.
- Export section in the user guide — `guides/core/how-to/navigate-intents.md`.
- Publication: `feature/intent-navigation` takes the default branch by merge commit and opens its pull request to the default branch, with the `core` 3.1.0 release entry covering every slice.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User procedure | New user-invoked command | `guides/core/how-to/navigate-intents.md` (new "Export an offline view" section; whole-guide read for stale "query only" claims) | `core` maintainer | `tools/lint-guide-titles.py`, `tools/validate_guides.py`, `tools/lint-guides-no-repo-only-refs.py` pass | Section names the command, the default destination, every export refusal code, the `--from` bounded route, and what the file does and does not contain |
| Skill instructions and activation | New mode of an existing skill | `navigate-intents/SKILL.md`, `navigate-intents/evals/eval_queries.json` | `core` maintainer | Self-host projection with no diff on re-run; eval file holds the new prompts | Export usage, refusals, and safety controls documented; positives and near-misses present |
| Pack promise | Entry point gains a mode | `packs/core/README.md` § Entry points, `guides/core/README.md` | `core` maintainer | Rows mention the offline view | Each `navigate-intents` row names the offline view |
| Architecture | New module and asset boundary inside the skill | `packs/core/DESIGN.md` § Intent-edge derivation | `core` maintainer | Section diff | Names `intent_view.py`, `view_assets/`, the data-island schema, and that the view consumes the derivation and never re-derives |
| Release history | Publication of `navigate-intents` | `docs/product/changelog.md` `## [core][3.1.0]` entry, dated the day the integration pull request opens | `core` maintainer | Changelog and `/now/` tests green | Entry's Highlights and Added name the offline view; one `core` bump over the default branch |
| Executable proof | Contract tests | `packs/core/tests/skills/navigate-intents/` (pytest, collected) and `view_browser_checks.py` (Playwright, run locally) | `core` maintainer | Dispatched `build-check`, `test-corpus`, `test-roster` green on the slice pull request; native checks green on the integration pull request | Run ids in the ledger |
| Verification record | Scale, browser, accessibility, and publication evidence | `docs/specs/intent-navigation-export/notes/verification-ledger.md` (repository-durable) | Implementer | Entries the plan's durable-output map names | Ledger cited by both pull requests |
| Advisory design | Structure and behaviour of the view | `docs/specs/intent-navigation-export/notes/view-design.md` | `core` maintainer | File present | Non-binding under RFC-0105 D5; kept or discarded on its own lifecycle |
| Slice 1 closeout | Slice 1's spec stays `Implementing` until the integration branch reaches the default branch | `docs/specs/intent-navigation/spec.md`, `plan.md`, `workspace.toml` | Implementer | Spec `Shipped`, plan `Done`, entry in `["ini-010".work]` shipped list | `lint-spec-status.py` clean on the integration branch |

## Agent Rules

### Always do

- Build every fact in the view from the same derivation and query code the `query` command runs, in the same process, over one derivation.
- Read every corpus file and every view asset through the co-located `_file_safety.py`.
- Treat all record text as untrusted data: carry it only inside the JSON data block and insert it into the page only as text.
- Refuse rather than write a partial file, overwrite a file, or write inside the repository.
- Keep `close-work/scripts/intent_graph.py` byte-identical to `navigate-intents/scripts/intent_graph.py`.
- Fold every release note for this slice into the single `## [core][3.1.0]` entry; `core` stays 3.1.0.
- Merge this slice to `feature/intent-navigation`; bring that branch up to date with the default branch by a merge commit.

### Ask first

- Any runtime dependency outside the Python standard library, any JavaScript library, any build step for the assets, or any new CI workflow or job.
- Adding a host to the source-link allowlist, or a scheme other than `https`.
- Changing the query schema, the derivation, or any `query` operation's output.
- Merging the integration pull request to the default branch, force-pushing any shared branch, or rewriting its history.

### Never do

- Never write the export inside the repository, and never commit a generated view.
- Never embed an artifact body, the absolute repository path, or any part of the remote URL other than the host, owner, and repository name.
- Never use `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, `Function`, or a string-argument timer in the view.
- Never read `workspace.toml`.
- Never import from another skill, and never share code or a renderer with `navigate-decisions`.
- Never add a top-level directory, a new pack, or a new skill.

## Testing Strategy

- **TDD (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0018, AC-0019, AC-0020, AC-0021, AC-0028):** pytest contract tests over the slice 1 fixture corpora plus a hostile corpus own the payload parity, the publication and destination rules, the source-link mapping, the static inertness of the generated HTML, the escape parity with the text output, and the colour contrast. These are invariants over constructed inputs, so they run in the collected suite on every CI run.
- **Scripted browser check (AC-0017, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027):** a Playwright suite drives the generated file in headless Chromium from local disk: the rendered views, the keyboard-only paths, network silence, reflow, and the rendered escape of controls. A browser is the only oracle for rendered behaviour; the suite is not collected by CI, so its pass at the final code commit is recorded in the ledger.
- **Goal-based check (AC-0029, AC-0030, AC-0031):** the scale benchmark, the activation run, and the real export over this repository are measurements recorded in the ledger.

## Acceptance Criteria

### Payload and parity

- [ ] **AC-0001.** A successful export's HTML contains exactly one `<script type="application/json" id="intent-data">` element, whose parsed content is an object with `schema` equal to `intent-navigation.view.v1` and the keys `scope`, `provenance`, `summary`, `records`, `outstanding`, `nodes`, `edges`, and `source_links`.
- [ ] **AC-0002.** For a whole-corpus export, `summary` equals the `summary` field of `query --operation summary`, `records` maps every live intent's node id to the `record` field of `query --operation record --id <that id>`, and `outstanding` equals the object made of the `placed` and `no_parent` fields of `query --operation outstanding`, over the same corpus. Checked over every slice 1 fixture corpus that derives without a whole-operation failure.
- [ ] **AC-0003.** `nodes` equals the derivation's node list and `edges` equals its edge list for the same corpus, in the derivation's order, so every parent, pointer, related, and refused edge the query reads is present, including those of terminal briefs and specs.
- [ ] **AC-0004.** When the delivery resolver reports incomplete delivery, the export succeeds, and `outstanding` is `{"available": false, "reason": <reason>, "limit": <limit>}` with the same values `query --operation outstanding` reports in `error.observed`.
- [ ] **AC-0005.** `export --from <identity>` accepts the identities `query --from` accepts, refuses an unknown one with `not_found` and an ambiguous ordinal with `ambiguous_identity`, and produces `scope` `{"from": <node id>}`, `records` for that intent and every intent below it by resolved parent edges, `outstanding` equal to `query --operation outstanding --from <identity>`, and `nodes` and `edges` restricted to those intents, the briefs whose resolved `Parent intent:` names one of them, and the specs whose resolved `Brief:` names such a brief or whose resolved `Discovery:` names one of them. `summary` stays whole-corpus. A whole-corpus export has `scope` `{"from": null}`.
- [ ] **AC-0006.** `provenance` carries `generated_at`, artifact counts by type, the untrusted-data statement, and the commit used for source links or null, and contains neither the absolute repository path nor any path outside the repository.

### Command and publication

- [ ] **AC-0007.** `navigate_intents.py export --root <dir> [--destination <dir>] [--name <file>] [--from <identity>]` prints one JSON object to standard output with `schema` `intent-navigation.export.v1` and `status` `ok` or `error`, and exits 0 on `ok`, 1 on `error`, and 2 when the argument parser rejects the command. An `ok` result carries `path` (the written file's absolute path), `bytes`, and `scope`. An `error` result carries `error.code`, `error.message`, `error.limits`, and `error.observed`, and no file is left at the destination. Nothing is written to standard error except on exit 2.
- [ ] **AC-0008.** A corpus failure refuses the export with the code `query` returns for the same corpus: `unsafe_input`, `input_too_large`, `malformed_record`, `duplicate_identity`, or `resolver_unavailable`.
- [ ] **AC-0009.** Without `--destination`, the file is written to the real path of the platform's temporary directory. Without `--name`, it is named `intent-graph-<UTC time as YYYYMMDDTHHMMSSZ>.html`.
- [ ] **AC-0010.** The export refuses with `invalid_destination`, and writes nothing, when the destination's real path does not exist, is not a directory, or is the repository root or inside it. Inside is decided by comparing real paths component by component, and on a case-insensitive file system a case-variant spelling of a path inside the repository is refused.
- [ ] **AC-0011.** The export refuses with `invalid_destination` a `--name` that is not one path segment matching `^[A-Za-z0-9][A-Za-z0-9._-]{0,99}\.html$`, and refuses with `destination_exists` when an entry of that name already exists at the destination, whether a file, directory, or symlink. An existing file is never changed.
- [ ] **AC-0012.** The written file is a regular file with one link and mode `0600`. It appears at its final name complete or not at all: a failure at any step leaves neither a partial file nor a temporary file at the destination.
- [ ] **AC-0013.** When the destination directory is replaced, between validation and writing, by another directory or by a symlink, the export refuses with `publish_failed` and writes nothing in either location.
- [ ] **AC-0014.** When the generated HTML is larger than the export budget, the export refuses with `export_too_large`, `error.limits` naming `budget_bytes` and `bounded_route` `--from`, and `error.observed.bytes` the measured size, and writes nothing. The budget is 104,857,600 bytes unless the AC-0029 benchmark finds a threshold failing below that size, in which case it is the file size of the largest synthetic corpus that met every threshold, rounded down to a whole MiB.

### Source links

- [ ] **AC-0015.** `source_links` maps each node id in `nodes` to an object with `kind` and `path`. `kind` is `commit` with `url` `https://github.com/<owner>/<repo>/blob/<commit>/<path>` when the repository's `origin` remote is a recognised GitHub remote, the repository root is the Git top level, `HEAD` is a full commit id contained in a remote-tracking branch of `origin`, and the working tree has no change under `docs/product/intents/`, `docs/product/briefs/`, or `docs/specs/`. It is `latest` with `url` `https://github.com/<owner>/<repo>/blob/HEAD/<path>` when only the remote condition holds. Otherwise it is `inert` with no `url`. Each path segment is percent-encoded with no safe characters.
- [ ] **AC-0016.** A recognised GitHub remote is exactly `https://github.com/<owner>/<repo>` or `git@github.com:<owner>/<repo>` or `ssh://git@github.com/<owner>/<repo>`, each with an optional `.git` suffix, where owner and repository match `^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$` and are not `.` or `..`. The host comparison is exact and the allowlist is `github.com` alone, fixed in the code. Fixtures for an `http://` remote, a `file:` remote, a `javascript:` value, another host, a host suffix such as `github.com.example`, a URL carrying a user name or password, an owner of `..`, and a missing remote each give every node `kind` `inert`, and none of their remote text appears in the HTML.
- [ ] **AC-0017.** In the rendered view, every source link of kind `latest` carries the visible label "may be newer than this export", every `inert` source shows its repository-relative path as plain text with no link, and every element with an `href` either targets a fragment of the page or begins with `https://github.com/`.

### Inert content

- [ ] **AC-0018.** The first child of `<head>` is a `<meta http-equiv="Content-Security-Policy">` whose content is exactly `default-src 'none'; script-src 'sha256-<S>'; style-src 'sha256-<C>'; img-src 'none'; base-uri 'none'; form-action 'none'`, where `<S>` and `<C>` are the base64 SHA-256 digests of the bytes of the page's one executable `<script>` element and its one `<style>` element, and the page has no other executable script, no `style` attribute, no `<link>`, `<img>`, `<iframe>`, `<object>`, `<embed>`, or `<base>` element, and no `url(` or `@import` in its style.
- [ ] **AC-0019.** In the data block, every `<`, `>`, `&`, U+2028, and U+2029 is written as a JSON `\u` escape. A hostile fixture corpus whose headers carry `</script><script>`, `<img src=x onerror=…>`, `javascript:` values, `"><svg onload=…>`, U+2028, and bidirectional controls produces HTML in which none of those strings appears outside the data block and the data block parses back to values equal to the query's.
- [ ] **AC-0020.** The view's script contains none of `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval(`, `Function(`, `srcdoc`, or `javascript:`, and passes no string as the first argument of `setTimeout` or `setInterval`.
- [ ] **AC-0021.** The view's escape function maps every string in a fixed probe set, including each bidirectional, zero-width, C0, and C1 control the text output escapes, to the same value as the text output's escape, so a control shows as `[U+XXXX]`.
- [ ] **AC-0022.** Over the hostile fixture, the rendered page's text nodes contain no bidirectional or other control character the text output escapes, every such character in a header value appears as its `[U+XXXX]` escape, and every edge-type, state, and trust-class label is a member of the view's fixed label set, whatever the record text says.
- [ ] **AC-0023.** Opening the exported file from local disk in Chromium, and then visiting every view and selecting every node of the hostile fixture, issues no network request other than loading the file itself and raises no Content-Security-Policy violation.

### Views

- [ ] **AC-0024.** Given a whole-corpus export of the `mixed` fixture, the summary strip shows the outstanding count, the refused-edge total, the parentless-intent count, and the intent, brief, and spec counts from `summary`; the Tree view lists every live intent exactly once under its resolved parent, roots ordered by node id, each showing its node id, level (`unrecorded` when absent), kind when present, and status; the Outstanding view lists the `placed` and `no_parent` items, terminal ancestors marked; the Refused edges view lists every edge in `edges` that carries a state, its source node, field, escaped value, and state, and its count equals the sum of `summary`'s refused-edge counts; and the Parentless view lists the intents with no resolved parent.
- [ ] **AC-0025.** Selecting an intent shows its header facts, heading, and source link, and under separately labelled groups its parent edge (resolved or refused), its child intents, its briefs, its specs, its delivery relations with their relation type and trust class, its delivery diagnostics, its related intents written here (resolved or refused) and written elsewhere, and every edge in `edges` leaving it. Selecting a brief or spec shows its id, path, status, source link, every edge in `edges` leaving it, and every delivery relation naming it. A legend names each edge group.
- [ ] **AC-0026.** Given the `mixed` fixture, a search for a text that matches a slug, and filters by level, kind, and exact status, each list the same intents as `query --operation search` with the same selectors; given a filter that matches nothing, the list says which filters emptied it and offers to clear them; given an export whose `outstanding` is unavailable, the Outstanding view states the reason instead of a list; given a corpus with no intents, the Tree view says no intents were found; given a data block that fails to parse or has another schema, the page shows one alert that the file is damaged and must be exported again; given scripting disabled, a notice says the view needs JavaScript.
- [ ] **AC-0027.** Using the keyboard alone, a reader can switch to each view, filter and search, expand and collapse a subtree, select a node, follow an edge to its target node, and return with the browser's back command to the previous view and selection. Focus is always visible, moves to the new view's or selected node's heading, and every interactive target is at least 24 by 24 CSS pixels. At a 320 CSS pixel wide viewport the page needs no horizontal scrolling. The page has one `h1`, a `header`, `nav`, and `main` landmark, and a polite live region that announces the view's name and result count after each view switch, filter, or search.
- [ ] **AC-0028.** In both the light and the dark theme, every text colour pair the stylesheet defines has a contrast ratio of at least 4.5:1, and every focus-indicator and control-border colour against its background at least 3:1. The stylesheet declares no `transition`, `animation`, or `@keyframes`.

### Scale, activation, and real use

- [ ] **AC-0029.** Synthetic corpora at 1, 10, 25, and 50 times this repository's intent, brief, and spec count are exported and opened in headless Chromium from local disk. For each the ledger records the file size, the median of three cold loads from navigation start to the summary strip rendering, the time from typing a search to its list updating, and the peak JavaScript heap. The thresholds are a file of at most 104,857,600 bytes, startup at most 3,000 ms, search at most 300 ms, and heap at most 1,024 MiB, and the ledger names each corpus that meets every threshold.
- [ ] **AC-0030.** Activation evaluations trigger `navigate-intents` on prompts asking for an offline, shareable, or HTML view of the intent graph or outstanding work, and do not trigger it on prompts asking for an HTML view of ADRs or RFCs. Every new prompt passes the harness's bar.
- [ ] **AC-0031.** An export over this repository at the final code commit exits 0, writes a file outside the repository, and the file, opened in headless Chromium, shows every live intent in the Tree view; the ledger records the command, the file size, and the counts shown.

## Follow-ons

- eugenelim: `docs/product/briefs/intent-navigation-delivery.md` slice 8 — intent dependency edges in the query, text, and this view.
- eugenelim: `docs/product/intents/FEAT-0002-intent-graph-navigation.md` § Validation hook — the 4-of-6 usefulness comparison over the first published build.

## Assumptions

none
