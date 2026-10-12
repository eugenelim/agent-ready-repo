# Spec: Intent navigation export

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-11 by eugenelim, spec and plan together, after clean adjudicated shaping, adversarial, and security spec-stage reviews (reports under `.context/reviews/7bf5b45f-6717-4400-91a6-b177e303ee4b/`).
- **Re-approved:** 2026-10-11 by eugenelim after the older-Git amendment (AC-0024, AC-0025, AC-0073; plan T7), with clean adjudicated shaping, adversarial, and security reviews of the amendment.
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
- Never let the export or view code read `workspace.toml`.
- Never import from another skill, and never share code or a renderer with `navigate-decisions`.
- Never add a top-level directory, a new pack, or a new skill.

## Testing Strategy

- **TDD (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0072, AC-0073, AC-0029, AC-0030, AC-0031, AC-0032, AC-0033, AC-0065):** pytest contract tests over the slice 1 fixture corpora plus a hostile corpus own the payload parity, the command and publication rules, the source-link mapping, the static inertness of the generated HTML, the escape parity with the text output, and the absence of motion. They are invariants over constructed inputs and run in the collected suite. Two run only where their platform allows: AC-0016 needs a case-insensitive file system, so it is skipped on Linux CI and its macOS run is recorded in the ledger; AC-0033 needs `node`, which GitHub's Ubuntu runners provide.
- **Scripted browser check (AC-0028, AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0042, AC-0043, AC-0044, AC-0045, AC-0046, AC-0047, AC-0048, AC-0049, AC-0050, AC-0051, AC-0052, AC-0053, AC-0054, AC-0055, AC-0056, AC-0057, AC-0058, AC-0059, AC-0060, AC-0061, AC-0062, AC-0063, AC-0064, AC-0069, AC-0070, AC-0071):** a Playwright suite drives the generated file in headless Chromium from local disk. A browser is the only oracle for rendered behaviour. The suite is not collected by CI, so its pass at the final code commit, with that commit id, the SHA-256 of both view assets, and the count of tests run with none skipped, is recorded in the ledger.
- **Goal-based check (AC-0066, AC-0067, AC-0068):** the scale benchmark, the activation run, and the real export over this repository are measurements recorded in the ledger.

## Acceptance Criteria

Unless a criterion names another fixture, a view criterion is checked on a whole-corpus export of the slice 1 `mixed` fixture corpus.

### Payload and parity

- [x] **AC-0001.** A successful export's HTML contains exactly one `<script type="application/json" id="intent-data">` element, whose parsed content is an object with `schema` equal to `intent-navigation.view.v1` and exactly the keys `schema`, `scope`, `provenance`, `summary`, `records`, `outstanding`, `nodes`, `edges`, and `source_links`.
- [x] **AC-0002.** `summary` equals the `summary` field of `query --operation summary` over the same corpus, for every slice 1 fixture corpus that derives without a whole-operation failure.
- [x] **AC-0003.** For a whole-corpus export, `records` maps exactly the live intents' node ids, each to the `record` field of `query --operation record --id <that id>`, over every such fixture corpus.
- [x] **AC-0004.** For a whole-corpus export, `outstanding` equals the object made of the `placed` and `no_parent` fields of `query --operation outstanding`, over every such fixture corpus.
- [x] **AC-0005.** For a whole-corpus export, `nodes` equals the derivation's node list and `edges` its edge list, in the derivation's order, so the parent, pointer, related, and refused edges of terminal briefs and specs are present too.
- [x] **AC-0006.** When the delivery resolver reports incomplete delivery, the export succeeds and `outstanding` is `{"available": false, "reason": <reason>, "limit": <limit>}` with the values `query --operation outstanding` reports in `error.observed`.
- [x] **AC-0007.** `export --from <identity>` accepts every identity form `query --from` accepts, refuses an identity matching no live intent with `not_found`, and refuses an ordinal matching more than one file with `ambiguous_identity`.
- [x] **AC-0008.** For `export --from <identity>`, the in-scope intents are that intent and every intent below it by resolved parent edges; the in-scope briefs are those whose resolved `Parent intent:` names an in-scope intent; the in-scope specs are those whose resolved `Brief:` names an in-scope brief or whose resolved `Discovery:` names an in-scope intent. `scope` is `{"from": <node id>}`, `records` maps exactly the in-scope intents, `outstanding` equals `query --operation outstanding --from <identity>`'s `placed` and `no_parent`, `nodes` is the derivation's nodes that are in scope, and `edges` is every derivation edge whose `from` is an in-scope node. `summary` stays whole-corpus. A whole-corpus export has `scope` `{"from": null}`.
- [x] **AC-0009.** `provenance` carries `generated_at`, artifact counts by type, the untrusted-data statement, and the commit used for source links or null, and the HTML contains neither the absolute repository path nor the destination path.

### Command and publication

- [x] **AC-0010.** `navigate_intents.py export --root <dir> [--destination <dir>] [--name <file>] [--from <identity>]` prints exactly one JSON object to standard output, with `schema` `intent-navigation.export.v1` and `status` `ok` or `error`. An `ok` object carries `path` (the written file's absolute path), `bytes`, and `scope`. An `error` object carries `error.code`, `error.message`, `error.limits`, and `error.observed`.
- [x] **AC-0011.** The command exits 0 on `ok`, 1 on `error`, and 2 when the argument parser rejects the command.
- [x] **AC-0012.** Except on exit 2, nothing reaches the process's standard error file descriptor, including the output of any Git subprocess, for a root that is a Git repository and for one that is not.
- [x] **AC-0013.** A corpus failure refuses the export with the code `query` returns for the same corpus: `duplicate_identity` and `malformed_record` shown by the committed slice 1 negative fixtures, `unsafe_input` and `input_too_large` by corpora the slice 1 fixture builders generate, and `resolver_unavailable` by a copy of the skill's scripts with the bundled resolver removed.
- [x] **AC-0014.** Without `--destination`, the file is written to the real path of the platform's temporary directory, and without `--name` it is named `intent-graph-<UTC time as YYYYMMDDTHHMMSSZ>.html`.
- [x] **AC-0015.** The export refuses with `invalid_destination`, and writes nothing, when the destination's real path does not exist, is not a directory, or equals or lies under any containment root, compared path component by path component. The containment roots are `--root`'s real path; every ancestor of it that holds a `.git` entry; and, when `--root` lies in a Git work tree, every non-bare work tree `git worktree list` reports for that repository — the main work tree as Git records it and each linked worktree — each taken at its real path. When a `.git` entry encloses `--root` and Git cannot list the work trees, or the listing belongs to another repository, the export refuses with `invalid_destination`. The listing belongs to `--root`'s repository when an entry equals or encloses `--root`'s real path, or when the nearest `.git` entry enclosing `--root` is a file whose `gitdir:` target's real path equals an entry. A main checkout that Git records nowhere — that of a `--separate-git-dir` repository, or one moved by `core.worktree` — is not a containment root when `--root` is in one of its linked worktrees; this limit is accepted. A destination reaching inside a containment root through a symlink; with `--root` a subdirectory of a Git work tree, a destination at the work tree's top level or at a sibling of `--root` inside it; with `--root` in a linked worktree created inside its main checkout, a destination in that main checkout; with `--root` in a linked worktree created outside its main checkout, a destination in that main checkout and in a second linked worktree; with `--root` in a linked worktree whose pointers are relative paths, a destination in its main checkout; with an unrelated Git repository enclosing the one `--root` is in, a destination inside that outer repository; with `GIT_DIR` set to an unrelated repository in the export's environment, a destination in a second linked worktree of `--root`'s repository; with Git's listing belonging to another repository, any destination; and, with `git` unavailable, exiting non-zero, timing out, or listing nothing while a `.git` entry encloses `--root`, any destination, are each refused. The refusal's message names the containment root the destination lies under.
- [x] **AC-0016.** On a case-insensitive file system, a destination spelled as a case variant of a directory inside a containment root is refused with `invalid_destination`.
- [x] **AC-0017.** The export refuses with `invalid_destination` a `--name` that is not one path segment matching `^[A-Za-z0-9][A-Za-z0-9._-]{0,99}\.html$`, and writes nothing.
- [x] **AC-0018.** The export refuses with `destination_exists` when an entry of the chosen name already exists at the destination, whether a file, a directory, or a symlink, and leaves that entry's bytes and modification time unchanged.
- [x] **AC-0019.** The written file is a regular file with one link and mode `0600`, and it appears at its final name complete or not at all: a failure injected at writing, syncing, or linking leaves the destination directory's listing unchanged.
- [x] **AC-0020.** When the destination directory is replaced between validation and writing, by another directory or by a symlink, the export refuses with `publish_failed` and writes nothing in either location.
- [x] **AC-0021.** On a platform whose `os` module lacks `O_NOFOLLOW`, `O_DIRECTORY`, or `dir_fd` support for `open` and `link`, the export refuses with `publish_failed` and writes nothing.
- [x] **AC-0022.** When the generated HTML is larger than the export budget, the export refuses with `export_too_large`, `error.limits` carrying `budget_bytes` and `bounded_route` `--from`, and `error.observed.bytes` the HTML's UTF-8 length, and writes nothing. The budget is 104,857,600 bytes unless the AC-0066 benchmark finds a threshold failing below that size, in which case it is the file size of the largest synthetic corpus that met every threshold, rounded down to a whole MiB.

### Source links

- [x] **AC-0023.** The repository's `origin` remote is recognised only when it is exactly `https://github.com/<owner>/<repo>`, `git@github.com:<owner>/<repo>`, or `ssh://git@github.com/<owner>/<repo>`, each with an optional `.git` suffix, where owner and repository match `^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$` and are not `.` or `..`. Fixtures for an `http://` remote, a `file:` remote, a `javascript:` value, another host, the host `github.com.example`, a URL carrying a user name or password, an owner of `..`, and a missing remote each give every entry of `source_links` kind `inert` with no `url`, and none of their remote text appears in the HTML.
- [x] **AC-0024.** With a recognised remote, an entry's kind is `commit`, with `url` `https://github.com/<owner>/<repo>/blob/<commit>/<link path>`, when `HEAD` is a full commit id contained in a remote-tracking branch of `origin`, every node file's bytes hash to the blob that `HEAD`'s tree records at its link path, and the local Git accepts `--no-lazy-fetch` (Git 2.44 or later).
- [x] **AC-0025.** With a recognised remote and at least one of AC-0024's other conditions failing, an entry's kind is `latest`, with `url` `https://github.com/<owner>/<repo>/blob/HEAD/<link path>`. A modified corpus file, an untracked corpus file, a git-ignored corpus file, an unpushed commit, a detached unpushed `HEAD`, and a Git that rejects `--no-lazy-fetch` each give `latest`.
- [x] **AC-0026.** The link path is the node's path relative to the Git top level: when `--root` is a directory below the top level, the root's path relative to the top level comes before the node's path, so the link names the same file the node names.
- [x] **AC-0027.** Each segment of the link path is percent-encoded with no character left unencoded except unreserved letters, digits, `-`, `.`, `_`, and `~`; a fixture path containing `?`, `#`, `%`, and a space produces those as `%3F`, `%23`, `%25`, and `%20`.
- [x] **AC-0072.** Every Git process the export starts is given a fixed argument list with no shell, may run at most 5 seconds, cannot prompt, inherits no `GIT_`-prefixed environment variable other than `GIT_TERMINAL_PROMPT=0`, and runs no program the repository configures: a fixture repository whose configuration sets `core.fsmonitor` and a `clean` filter that `.gitattributes` applies to a modified corpus file, each pointing at a script that writes a marker file, leaves no marker after an export.
- [x] **AC-0073.** On a Git that rejects `--no-lazy-fetch`, the export starts no Git call that reads repository objects, and AC-0015's destination check is unchanged.
- [x] **AC-0028.** In the rendered view, every `latest` source link carries the visible label "may be newer than this export", every `inert` source shows its repository-relative path as plain text with no link, and every element with an `href` either targets a fragment of the page or begins with `https://github.com/`.

### Inert content

- [x] **AC-0029.** The first child of `<head>` is a `<meta http-equiv="Content-Security-Policy">` whose content is exactly `default-src 'none'; script-src 'sha256-<S>'; style-src 'sha256-<C>'; img-src 'none'; base-uri 'none'; form-action 'none'`, where `<S>` and `<C>` are the base64 SHA-256 digests of the UTF-8 bytes of the content of the page's one executable `<script>` element and its one `<style>` element.
- [x] **AC-0030.** The page has no executable script other than that one element, no `style` attribute, no `<link>`, `<img>`, `<iframe>`, `<object>`, `<embed>`, or `<base>` element, and no `url(` or `@import` in its style.
- [x] **AC-0031.** In the data block, every `<`, `>`, `&`, U+2028, and U+2029 is written as a JSON backslash-u escape. A hostile fixture corpus whose headers carry `</script><script>`, `<img src=x onerror=alert(1)>`, a `javascript:` value, `"><svg onload=alert(1)>`, a U+2028 line separator, and bidirectional controls produces HTML in which none of those strings appears outside the data block, and the data block parses back to values equal to the query's.
- [x] **AC-0032.** The view's script contains none of `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval(`, `Function(`, `srcdoc`, or `javascript:`, and passes no string as the first argument of `setTimeout` or `setInterval`.
- [x] **AC-0033.** The view's escape function maps every string in a fixed probe set, which includes each code point the text output escapes, to the same value as the text output's escape, so a control shows as `[U+XXXX]`.
- [x] **AC-0034.** Over the hostile fixture, the rendered page's text nodes contain no code point the text output escapes, and each such code point in a header value appears as its `[U+XXXX]` escape.
- [x] **AC-0035.** Over the hostile fixture, every edge-group, state, and trust-class label the view renders is a member of this closed set, whatever the record text says: the groups `Parent`, `Child intents`, `Briefs`, `Specs`, `Delivery relations`, `Delivery diagnostics`, `Related, written here`, `Related, written elsewhere`, and `Pointers`; the states `dangling`, `retired_target`, `kind_mismatch`, `out_of_type`, `multiple_values`, `cycle`, `unparseable`, and `self_reference`; and the trust classes `delivery_contract`, `pointer_checked`, and `pointer_unchecked`.
- [x] **AC-0036.** Opening the exported file of the hostile fixture from local disk in Chromium, then visiting every view and selecting every node, issues no network request other than loading the file itself and raises no Content-Security-Policy violation.

### Views

- [x] **AC-0037.** The summary strip shows the outstanding count, the refused-edge total, the parentless-intent count, and the intent, brief, and spec counts, each equal to the value in `summary`.
- [x] **AC-0038.** The Tree view lists every live intent exactly once under its resolved parent, roots and siblings ordered by node id, each row showing its node id, its level (`unrecorded` when absent), its kind when present, and its status, and an intent with a refused parent edge marked refused with its state.
- [x] **AC-0039.** The Outstanding view lists every `placed` and `no_parent` item of `outstanding`, each under its ancestor chain, with terminal ancestors marked terminal.
- [x] **AC-0040.** The Refused edges view lists every edge in `edges` that carries a state, showing its source node, field, escaped value, and state, and its count equals the sum of `summary`'s refused-edge counts.
- [x] **AC-0041.** The Parentless view lists exactly the live intents with no resolved parent.
- [x] **AC-0042.** Selecting an intent shows its node id, heading, path, level, kind, status, and source link, and under separately labelled groups its parent edge (resolved or refused), its child intents, its briefs, its specs, its delivery relations with relation type and trust class, its delivery diagnostics, its related intents written here (resolved or refused), and its related intents written elsewhere.
- [x] **AC-0043.** Selecting a brief or spec shows its id, path, status, source link, every edge in `edges` leaving it, and every delivery relation naming it.
- [x] **AC-0044.** The detail panel carries a legend that names and explains each edge group it can show.
- [x] **AC-0045.** A resolved edge whose `to` is not in `nodes` shows that id as plain text marked "outside this export", not as a link.
- [x] **AC-0046.** Given an export with `--from`, the page shows a banner naming the scoped intent, and the summary strip labels its counts as covering the whole corpus.
- [x] **AC-0069.** Given an export with `--from`, the Tree view's only root is the scoped intent, with every in-scope intent once beneath it.
- [x] **AC-0070.** Given an export with `--from`, the Refused edges view lists every edge in `edges` that carries a state, and its count equals the number of such edges.
- [x] **AC-0071.** Given an export with `--from`, search and each filter list only in-scope intents: the in-scope subset of what `query --operation search` returns for the same selectors.
- [x] **AC-0047.** Given an export whose `outstanding` is unavailable, selecting an intent shows, in place of its delivery relations and delivery diagnostics, a statement that delivery mapping was unavailable with its reason.
- [x] **AC-0048.** A search text matching a slug, and each of the filters by level, kind, and exact status, lists the same intents as `query --operation search` with the same selectors.
- [x] **AC-0049.** Given a filter that matches nothing, the list states which filters emptied it and offers a control that clears them.
- [x] **AC-0050.** Given an export whose `outstanding` is unavailable, the Outstanding view states that delivery mapping was unavailable and its reason instead of a list.
- [x] **AC-0051.** Given a corpus with no intents, the Tree view states that no intents were found.
- [x] **AC-0052.** Given a corpus with no refused edge, the Refused edges view states that every pointer resolved.
- [x] **AC-0053.** Given a corpus where every intent has a resolved parent, the Parentless view states that every intent has a parent.
- [x] **AC-0054.** Given a data block that fails to parse or carries another `schema`, the page shows one alert that the file is damaged and must be exported again, and no view.
- [x] **AC-0055.** Given scripting disabled, the page shows a notice that the view needs JavaScript.

### Accessibility

- [x] **AC-0056.** Using the keyboard alone, a reader can switch to each view, search, filter, expand and collapse a subtree, select a node, follow an edge to its target node, and return with the browser's back command to the previous view and selection.
- [x] **AC-0057.** Every focused element shows a visible focus indicator, and focus moves to the new view's heading after a view switch and to the selected node's heading after a selection.
- [x] **AC-0058.** At viewport widths of 320 and 1280 CSS pixels, no focused element is entirely hidden by other page content.
- [x] **AC-0059.** Every interactive target is at least 24 by 24 CSS pixels.
- [x] **AC-0060.** At a 320 CSS pixel wide viewport the page needs no horizontal scrolling.
- [x] **AC-0061.** The page has exactly one `h1` and one each of the `header`, `nav`, and `main` landmarks.
- [x] **AC-0062.** A polite live region announces the view's name and result count after each view switch, search, and filter change.
- [x] **AC-0063.** Every interactive control has an accessible name that contains its visible label text, and every tree toggle's name includes the node id it toggles.
- [x] **AC-0064.** In both the light and the dark theme, every rendered text node's computed colour has a contrast ratio of at least 4.5:1 against its computed background, and the focus indicator at least 3:1 against the background it sits on.
- [x] **AC-0065.** The stylesheet declares no `transition`, `animation`, or `@keyframes`.

### Scale, activation, and real use

- [x] **AC-0066.** Synthetic corpora at 1, 10, 25, and 50 times this repository's intent, brief, and spec count are exported and opened from local disk in headless Chromium. For each the ledger records whether `outstanding` was available, the file size, startup as the median over three cold loads in fresh browser contexts of the `view-ready` performance mark the page sets after its first render, search as the median over five runs of the time from typing `graph` into the search box to the `list-updated` mark, and heap as `performance.memory.usedJSHeapSize` after the last search. The thresholds are a file of at most 104,857,600 bytes, startup at most 3,000 ms, search at most 300 ms, and heap at most 1,024 MiB, and the ledger names each corpus that meets every threshold.
- [x] **AC-0067.** Activation evaluations trigger `navigate-intents` on prompts asking for an offline, shareable, or HTML view of the intent graph or outstanding work, and do not trigger it on prompts asking for an HTML view of ADRs or RFCs. Every new prompt passes the harness's bar.
- [x] **AC-0068.** An export over this repository at the final code commit exits 0 and writes a file outside the repository that, opened in headless Chromium, lists every live intent in the Tree view; the ledger records the command, the file size, and the counts shown.

## Follow-ons

- eugenelim: `docs/product/briefs/intent-navigation-delivery.md` slice 8 — intent dependency edges in the query, text, and this view.
- eugenelim: `docs/product/intents/FEAT-0002-intent-graph-navigation.md` § Validation hook — the 4-of-6 usefulness comparison over the first published build.

## Assumptions

none
