# Plan: Intent view hand-over prompt

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** RFC-0108 D4; `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py` `_SCRIPT_PARTS` (a new part is one tuple entry); `view_src/detail.js` `nextStep` and `view_src/detail-render.js` `renderDetail` (the Next step part this extends); `view_src/escape.js` (the CommonJS export that `test_escape_function_matches_the_text_output` loads under `node`); `packs/core/tests/skills/navigate-intents/view_browser_checks.py` `test_ac_0015_next_step_sentences`, `_next_step` and `_rewrite` (the construction path). Deviation: the CommonJS export moves from the end of `escape.js` to the end of `handover.js`, so the node test reaches the prompt builder.

## Approach

Four tasks in one review unit. The prompt builder comes first, as a pure function, because the path rule is the security control and a collected test under `node` decides it without a browser. The detail zone then renders the prompt block from it. Copying and its failure path come next. Their oracle is real Chromium clipboard behaviour, chosen by granting or withholding the permission. Docs, the version and the measurements close the unit. The riskiest part is the hostile-path coverage: the derivation already skips hostile file names, so the view's own check is exercised through payload edits (AC-0004, AC-0008) as well as on disk (AC-0007).

## Constraints

- RFC-0108 D4: a closed template set; one path under the per-segment grammar; nothing else from a record in a prompt; a failing record gets no prompt and a plain reason; the copied string equals the visible prompt; a failed copy selects the prompt; the page launches nothing.
- RFC-0108 D1 rules 8 to 10 (as corrected by the 2026-10-16 errata entry for motion): every width and theme; WCAG 2.2 AA; inert and offline under the shipped content-security policy.
- The source-and-style spec's criteria 0001 to 0010 keep holding: one hashed script joined from parts, at most 400 lines a part, the banned-API scan, and the layout sheet's limits.
- `packs/AGENTS.md`: self-host after edits; bump `pack.toml` and `.claude-plugin/plugin.json` together; no internal-governance citations in `.apm/`; update the skill's eval harness.
- ADR-0074: standard-library-only Python; no build step for the view.

## Construction tests

**Integration tests:** `view_browser_checks.py` exports fixture corpora through `nav.run_export`, edits payloads through `_rewrite`, and opens each export in headless Chromium through `Opened`, which takes a new `clipboard` argument that grants `clipboard-read` and `clipboard-write`.
**Manual verification:** the real export, the 16 screenshots, the `experience-reviewer` pass and a visual-polish pass, recorded in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Amended-in-part headers | T4 | Header lines in the two amended specs | Each names this spec and its amended criterion or rules |
| User guide and skill | T4 | Guide lints; self-host no diff; eval case | The prompt, its copy paths and its limits described |
| Changelog and version | T4 | Fragment; both version files | Fragment validates at the bumped version |
| Verification ledger and screens | T4 | Ledger; `notes/screens/` | Cited by the PR |
| Coordination | T4 | `workspace.toml` entry; Spec map row | Follows spec status |

## Design (LLD)

### Component / module decomposition

Traces to: AC-0001, AC-0003, AC-0005, AC-0006, AC-0008, AC-0009.

Owned by: T1, T2

`view_src/handover.js` is a new part, placed second in the part list, right after `escape.js`. It holds the seven templates as a table keyed by next-step rule, the safe-path test, and `handoverPrompt(type, rule, path)`. That function returns `null` for a rule with no template, `{ refused: true }` for a path that fails the test, and `{ prompt: <string> }` otherwise. The CommonJS export and the early `return` for a document-less host move from the end of `escape.js` to the end of `handover.js`, exporting both `escapeDisplay` and `handoverPrompt`. The table and regular expressions are `var` assignments, which run before that return; the shipped escape parity test keeps working unchanged.

The safe-path test is written as three checks the spec's term names: a length check, a type-to-prefix table, and one anchored per-segment regular expression applied to each `split('/')` segment, with the `.md` suffix checked on the whole string. Doing the segment split in code, not in one large regular expression, keeps each limit visible against the spec's definition.

`detail.js` keeps `nextStep(id)` returning the sentence and gains `nextStepRule(id)`, which returns the rule number 1 to 10 that `nextStep` reads its sentence from. One table of sentences indexed by rule keeps the two in step.

### State & control flow

Traces to: AC-0010, AC-0011, AC-0012, AC-0013, AC-0017.

Owned by: T3

The "Copy prompt" click handler calls `navigator.clipboard.writeText(prompt)` with the same string the `code` element was built from. On success, the button text becomes "Copied" and `dom.live` announces "Prompt copied". On rejection, or when `navigator.clipboard` or its `writeText` is missing, the handler selects the `code` element's contents through `document.createRange`, `selectNodeContents` and the window selection. It also unhides the status line with the fixed failure sentence and announces it. Focus is not moved. "Until the next action" needs no timer: every pick, question, search or filter change re-renders the detail zone, which builds a fresh button.

### Quality attributes (NFRs)

Traces to: AC-0014, AC-0015, AC-0016, AC-0018.

Owned by: T2, T3

The prompt block is a wrapping flex row: the `code` element takes the remaining width with `min-width: 0`, and the button keeps its own width and wraps below when the row is too narrow. That adds no breakpoint. AC-0015's matrix still samples both sides of the detail zone's shipped 28rem container query and of the page's 40rem, 66rem and 90rem media queries. AC-0015's 200-character path, reached by a payload edit because no shipped fixture holds one, wraps anywhere through the shipped `code` rule's `overflow-wrap: anywhere`. The `code` element uses the monospace token, a raised background and a rule-coloured border in `view-base.css`; `view.css` carries only the flex layout and spacing. The status line uses the shipped meta text style. Any transition on the button reuses the shipped motion block under `prefers-reduced-motion: no-preference`.

### Failure, edge cases & resilience

Traces to: AC-0003, AC-0004, AC-0007, AC-0008, AC-0013.

Owned by: T1, T2, T3

A refused path shows the fixed reason sentence and never a partial prompt. A copy failure leaves the prompt visible and selected, so a reader can always copy by hand. A missing clipboard API is handled the same as a refusal.

## Tasks

### T1: The prompt builder and the launch-ban scan

**Depends on:** none

**Tests:**
- Criteria: AC-0008, AC-0009.
- `test_handover_prompt_matches_the_safe_path_rule` in `test_export_html.py` loads the joined script under `node`, as `test_escape_function_matches_the_text_output` does, and calls `handoverPrompt` over AC-0008's probe set for each type and each prompt rule. Its oracle is a Python `_safe_path(type, path)` written in the test from the spec's term, not from the view's source. It also checks each returned prompt against a template table written in the test from AC-0001, and that rules 1, 2 and 8 return nothing. It is the browser-free construction guard for AC-0008, AC-0001 and AC-0005, run in `make test`; the rendered outcome is decided in T2.
- `test_view_script_has_no_launch_api` scans the joined script, comments removed, with the identifier-boundary matcher `test_the_token_match_respects_identifier_boundaries` already covers.
- The node test skips when `node` is absent, as the shipped escape test does. GitHub's Ubuntu runners provide it.

**Done when:** both tests and `test_escape_function_matches_the_text_output` pass under the collected run of `test_export_html.py`.

### T2: "Next step" shows the prompt block or the reason

**Depends on:** T1

**Tests:**
- Criteria: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0015, AC-0016.
- `_next_step` in `view_browser_checks.py` reads only the `p.next-step` sentence; `test_ac_0015_next_step_sentences` keeps every sentence assertion. The "no `code`, button or link" assertion moves to rules 1, 2 and 8 in a new AC-0005 test.
- AC-0001 and AC-0006 read rule 4 from the `roadmap` export's `spec:anchor-sub-spec-two` and rule 9 from the India-parent corpus, built by the shipped `_india_parent_corpus`.
- `_long_path_corpus` copies `mixed` and adds an `Implementing` spec directory named `long-` plus 115 `a` characters (AC-0003).
- `_with_paths(export, {node_id: path})` uses `_rewrite` to set record paths in `nodes` and in every payload place the view reads a node's path from. AC-0004 assigns the 16 hostile probes round-robin over `mixed`'s records with a prompt rule, writing as many exports as that takes. AC-0008 writes one export per probe string, with a spec, a brief and an intent each carrying it. AC-0015 sets `spec:bravo-spec`'s 200-character two-segment path.
- `_hostile_names_corpus` copies `hostile` and writes, under `tmp_path`, an intent file, a brief file and a spec directory per hostile probe, creating each parent directory first (AC-0007).
- AC-0015 and AC-0016 run over every width and theme of the prompt matrix in one parametrised test each, reusing the shipped geometry, target-size, contrast and focus helpers.

**Done when:** those tests, and the full `view_browser_checks.py` run, pass with none skipped.

### T3: Copying works, and a refused copy selects the prompt

**Depends on:** T2

**Tests:**
- Criteria: AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0017, AC-0018.
- `Opened` gains `clipboard: bool = False`, which creates the context with `permissions=["clipboard-read", "clipboard-write"]`. A granted run reads back with `navigator.clipboard.readText()`. A refused run uses the default context, where Chromium rejects the write with `NotAllowedError`.
- The absent-API case adds an init script that deletes `navigator.clipboard` before the page script runs.
- AC-0014 reads the shipped `Opened` request and policy-violation evidence after both runs.

**Done when:** those tests, and the full `view_browser_checks.py` run, pass with none skipped.

### T4: Docs, version, ledger and review evidence

**Depends on:** T3

**Tests:**
- Criteria: AC-0019, AC-0020, AC-0021.
- `view_bench.py --source . --counts 1 10 25 50` at the final code commit; the ledger records its table.
- A `test-corpus.yml` dispatch at the final code commit passes; the ledger records its run id (Testing Strategy, AC-0008 and AC-0009).
- The real export is opened by a ledger-recorded script that picks one record per rule present, copies with the permission granted, and records each prompt.
- Screenshots of the four states at 320 and 2560 in light and dark go to `notes/screens/` with SHA-256 values in the ledger, and feed the `experience-reviewer` pass and a separate visual-polish pass.
- Goal checks: `tools/lint-guide-titles.py`, `tools/validate_guides.py`, `tools/lint-guides-no-repo-only-refs.py`; `FORCE=1 make build-self` twice with no second diff; `tools/changelog.py` validation of the new fragment; the `packs/AGENTS.local.md` citation grep over `packs/`.

**Done when:** each goal check above exits 0, and the ledger holds the bench table, the real-export prompts and the review dispositions.

## Rollout

Ships in the next `core` patch release. Nothing migrates: the payload, query and derivation are unchanged, and an export made before this release simply has no prompt.

## Risks

- Headless Chromium's clipboard behaviour could differ from a desktop browser opening a local file. The refused path covers that case by design, and the real-export check records the desktop-style granted path.
- A hyphen-joined instruction such as `ignore-previous-instructions` passes the path rule, because the rule bounds characters and length, not meaning. The prompt carries it only as a backtick-quoted path inside a fixed sentence, and only for a file the navigator loaded.

## Changelog

- 2026-10-19: spec approved by eugenelim
- 2026-10-19: plan approved by eugenelim
