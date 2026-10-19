# Spec: Intent view hand-over prompt

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0108 (D1 rules 1 to 10 as corrected by its errata entries, and D4), RFC-0105 (D4, through RFC-0108 D4's exception), ADR-0007, ADR-0074
- **Amends:** [intent-view-session-start](../intent-view-session-start/spec.md) — its criterion 0015 and one Never-do rule; [intent-dependency-graphs](../intent-dependency-graphs/spec.md) — one Never-do rule. The table "Amended criteria and rules" at the end of § Acceptance Criteria states each disposition. Every other criterion and rule of those specs, of [intent-view-source-and-style](../intent-view-source-and-style/spec.md), of [intent-view-tree-and-roadmap](../intent-view-tree-and-roadmap/spec.md) and of [intent-navigation-export](../intent-navigation-export/spec.md) carries over unchanged.
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

A maintainer who picks an item in the offline intent view gets, under "Next step", a ready-to-paste prompt that starts the named skill on that item's file, and copies it with one click or by hand when the browser refuses the clipboard. The prompt is always one of seven fixed sentences with only the item's checked file path filled in, so no text written inside a record can reach an agent through it, and the page stays inert and offline.

## What Changes

- "Next step" in the detail zone gains a prompt block, a "Copy prompt" button and a copy status line — a new script part `view_src/handover.js`, added to the part list in `intent_view.py`, and `view_src/detail-render.js`.
- The next-step rule names which of its sentences carry a prompt — `view_src/detail.js`.
- The prompt block, button and status line get their style — `view_assets/view-base.css`, `view_assets/view.css`.
- Collected tests check the template set and the path rule through `node`; browser checks cover the prompt, copying, the failure path, hostile paths and layout — `test_export_html.py`, `view_browser_checks.py`.
- The skill instructions, user guide and evaluations describe the prompt — `navigate-intents/SKILL.md`, `guides/core/how-to/navigate-intents.md`, `navigate-intents/evals/eval_queries.json`.
- Core moves to its next unused patch version.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | Two shipped specs' rules and one criterion change | `Amended in part by:` header line of `docs/specs/intent-view-session-start/spec.md` and of `docs/specs/intent-dependency-graphs/spec.md` | This spec's implementer | Header lines present | Each names this spec and what this spec's `Amends:` line names for it |
| User procedure | The detail panel gains a prompt and a copy control | `guides/core/how-to/navigate-intents.md` § Export an offline view (whole section re-read for "names which skill to use" claims) | `core` maintainer | `tools/lint-guide-titles.py`, `tools/validate_guides.py`, `tools/lint-guides-no-repo-only-refs.py` pass | The section says the prompt holds only a fixed sentence and the file path, how to copy it, and what shows when the path does not fit |
| Skill instructions and activation | The described output changes | `navigate-intents/SKILL.md` § Export an offline view; `navigate-intents/evals/eval_queries.json` | `core` maintainer | Self-host re-run shows no diff; the eval file holds a new case | SKILL.md describes the prompt and its limits; a `should_trigger: true` case asks for a copyable prompt to hand an item to a skill |
| Release history | A pack content change | A changelog fragment under `docs/product/changelog.d/` from `tools/changelog.py new` | Pack release workflow (`packs/AGENTS.local.md`) | Fragment validates; Highlights decided | Fragment present at the bumped version |
| Verification record | Browser, width, scale and review evidence | `docs/specs/intent-view-handover-prompt/notes/verification-ledger.md` and `notes/screens/` (repository-durable) | Implementer | Ledger entries with commit, test counts and screenshot SHA-256 values | Ledger cited by the pull request |
| Coordination | A confirmed brief slice | `workspace.toml` `["ini-010".work]`; the brief's Spec map | Implementer | Entry and Spec-map row present | Entry follows the spec's status |

## Agent Rules

### Always do

- Build a prompt only from the seven templates of AC-0001, filled with the picked record's payload `path` and nothing else.
- Put prompt text into the page only as text, through the view's existing element helpers.
- Keep the shipped content-security policy string, with only its two digests changing.
- Record every browser, width, scale and review result in this spec's verification ledger with the commit it ran against.

### Ask first

- Any change to a template's wording, any added template, or any template for a rule that AC-0005 leaves without one.
- Any change to the payload, a `query` output, or any derivation.
- Any copy mechanism other than the browser clipboard's write call on the click, such as a deprecated copy command.

### Never do

- Never put a heading, title, slug, status, edge value, diagnostic or any other record text except the checked path into a prompt.
- Never repair, trim, escape or shorten a path that fails the path rule to make a prompt from it.
- Never launch anything: no link with a scheme other than `https`, no custom-scheme link, no `window.open`, no loopback server and no terminal integration.
- Never show readiness, read `workspace.toml`, or accept piped input; that is a separate slice.
- Never add a JavaScript library, a dependency outside the Python standard library, or a script part beyond `handover.js`.

## Testing Strategy

- **TDD (AC-0009):** the launch-API ban is a property of the joined script's text, so a collected pytest test scans it on every CI run.
- **Scripted browser check (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018):** `view_browser_checks.py` drives exported fixture files in headless Chromium at true viewport sizes. The clipboard's success and refusal paths are both real browser behaviour, chosen by granting or withholding the clipboard permission, so neither is mocked. The suite is not collected by CI, so its full pass at the final code commit, with the count run and none skipped, is recorded in the ledger. AC-0008's probe set is also run on every CI build by a collected test that loads the joined script under `node`, so a regression in the path rule fails CI before the browser suite runs.
- **Goal-based check (AC-0019, AC-0020):** the scale benchmark and the real export are measurements recorded in the ledger.
- **Visual / manual QA (AC-0021):** an adjudicated `experience-reviewer` pass over screenshots of every prompt state decides the design outcome no script can. It is a completion gate by owner decision on 2026-10-19, as the session-start spec's criterion 0048 is.

## Acceptance Criteria

Unless a criterion names another fixture, it is checked on a whole-corpus export of the `mixed` fixture corpus, opened from local disk. Terms used below:

- **Status word, display name, open item:** as the session-start spec defines them.
- **Next-step rule n:** the n-th rule of the session-start spec's criterion 0015, the first that matches the picked record.
- **Prompt rule:** next-step rule 3, 4, 5, 6, 7, 9 or 10.
- **Record path:** the `path` value of the picked record's node in the export's payload.
- **Safe path:** a string of at most 200 characters that starts with `docs/specs/` when the record is a spec, `docs/product/briefs/` when it is a brief, and `docs/product/intents/` when it is an intent; ends with `.md`; and whose every `/`-separated segment matches `[A-Za-z0-9][A-Za-z0-9._-]{0,99}`, so that no segment is empty, `.` or `..`.
- **Hostile probes:** a space, a tab, a newline, U+2028, U+202E, the phrase `ignore previous instructions`, a backtick, `$(`, `|`, `;`, `&`, `>`, `'`, `"`, a backslash and `é`. None holds `/` or NUL.
- **Prompt block:** the element in "Next step" holding the prompt's `code` element and the "Copy prompt" button.
- **Prompt matrix:** true viewport widths of 320, 360, 640, 1056, 1280, 1440, 1500, 1680 and 2560 CSS px, each in the light and the dark theme.

### The prompt

- [ ] **AC-0001.** Given a picked record whose next-step rule is a prompt rule and whose record path is a safe path, "Next step" shows its sentence followed by a prompt block whose `code` element's text is that rule's template with `<path>` replaced by the record path:
  - rule 3: "Use the work-loop skill to continue building \`<path>\`."
  - rule 4: "Use the work-loop skill to implement \`<path>\`."
  - rule 5: "Use the new-spec skill to finish the spec at \`<path>\`."
  - rule 6: "Use the author-delivery-brief skill in continue mode on \`<path>\`."
  - rule 7: "Use the intent skill to decompose \`<path>\`."
  - rule 9: "Use the close-work skill to check whether \`<path>\` can close."
  - rule 10: "Use the intent skill to keep shaping \`<path>\`."

  Over the `mixed` fixture, `spec:bravo-spec` shows "Use the work-loop skill to continue building \`docs/specs/bravo-spec/spec.md\`.".
- [ ] **AC-0002.** The prompt block's "Copy prompt" control is a `button` that follows the `code` element in document order inside the "Next step" part.
- [ ] **AC-0003.** Given a picked record whose next-step rule is a prompt rule and whose record path is not a safe path, "Next step" shows its sentence followed by the line "No prompt shown: this file's path is too long or uses characters a prompt cannot carry safely. Start the skill yourself from Open the file." and holds no prompt block, `code` element or "Copy prompt" button. Over a copy of the `mixed` fixture with an `Implementing` spec in the directory `long-` followed by 115 `a` characters, that spec shows this line.
- [ ] **AC-0004.** Over exports of the `mixed` fixture whose payloads are rewritten so that each hostile probe is carried by the record path of at least one record with a prompt rule, each such path otherwise being a safe path for its record, every record whose record path carries a hostile probe shows AC-0003's line and no prompt block.
- [ ] **AC-0005.** Given a picked record whose next-step rule is 1, 2 or 8, "Next step" holds no prompt block, no `code` element, no "Copy prompt" button and no AC-0003 line.
- [ ] **AC-0006.** Over the `mixed` export, the `india_parent` export and the `roadmap` export, every record with a prompt rule shows a prompt block whose `code` text is AC-0001's template for its rule with its record path, and each of the seven prompt rules is shown by at least one record.
- [ ] **AC-0007.** Over an export of a copy of the `hostile` fixture to which, for each hostile probe, an intent file, a brief file and a spec directory whose names carry that probe are added, no payload node's `path` contains a hostile probe, and every record of the unmodified `hostile` fixture with a prompt rule still shows a prompt block.

### The path rule and the launch ban

- [ ] **AC-0008.** For each record type, and for every string of a fixed probe set written as the record path of a record of that type with a prompt rule, "Next step" shows a prompt block exactly when the string is a safe path for that type. The set holds: a safe path of each type; a 100- and a 101-character segment; a 200- and a 201-character path; each prefix given with a mismatched type; a path without `.md`; an empty, a `.` and a `..` segment; a leading `/`; and a safe path with each hostile probe inserted.
- [ ] **AC-0009.** The joined script, comments removed, contains no `location` identifier that is not followed by `.hash`, and none of `window.open`, `open(` as an identifier call, `execCommand`, `showModalDialog` or `navigator.share`. Links stay bound by the export spec's criterion 0028, which this spec carries over.

### Copying

- [ ] **AC-0010.** With the clipboard permission granted, activating "Copy prompt" by a click, by Enter and by Space each leaves on the clipboard a string equal, code unit for code unit, to the prompt's `code` element's text content.
- [ ] **AC-0011.** After a successful copy, the button reads "Copied" and the polite live region announces "Prompt copied".
- [ ] **AC-0012.** After a successful copy, when the reader picks another record with a prompt, chooses a question, searches or changes a filter, every "Copy prompt" button then shown reads "Copy prompt".
- [ ] **AC-0013.** Given the clipboard write is refused, or `navigator.clipboard` is absent, activating "Copy prompt" leaves the document selection's text equal to the prompt's `code` element's text content, a status line inside the prompt block reads "Copy didn't work here. Press Ctrl+C or ⌘C to copy the selected prompt.", the polite live region announces that line, and the button still reads "Copy prompt".
- [ ] **AC-0014.** Over a session that copies a prompt successfully and one whose copy is refused, the page makes no network request and raises no content-security-policy violation.

### Layout and access

- [ ] **AC-0015.** Across the prompt matrix, over an export of the `mixed` fixture whose payload is rewritten so that `spec:bravo-spec`'s record path is the 200-character safe path `docs/specs/` followed by a 100-character segment, `/`, an 80-character segment and `/spec.md`, with that record picked, the prompt's `code` element and the "Copy prompt" button do not overlap, each lies within 1 CSS px of the detail zone's box, and the document's `scrollWidth` does not exceed the viewport width.
- [ ] **AC-0016.** Across the prompt matrix, with a record with a prompt rule picked and after a refused copy, the session-start spec's criteria 0034, 0035, 0036, 0037 and 0041 hold.
- [ ] **AC-0017.** Using the keyboard alone, a reader can move focus from the detail heading to "Copy prompt" and activate it, and focus stays on "Copy prompt" after a successful or a refused copy.
- [ ] **AC-0018.** With `prefers-reduced-motion` set to `reduce`, every element of the prompt block computes every `transition-duration` and `animation-duration` as `0s`.

### Measurement and review

- [ ] **AC-0019.** The export spec's scale benchmark (its criterion 0066), re-run on this view, meets its thresholds at 1, 10, 25 and 50 times this repository's corpus, and the ledger records each result.
- [ ] **AC-0020.** An export over this repository at the final code commit, opened in headless Chromium with the clipboard permission granted, copies for one record of each prompt rule that the corpus holds a prompt equal to AC-0001's template with that record's path, and the ledger records each prompt and the prompt rules the corpus did not hold.
- [ ] **AC-0021.** An `experience-reviewer` pass over screenshots of four states — a prompt shown, a path that fails the rule, a hostile-probe path, and a refused copy — at 320 and 2560 CSS px in light and dark, against RFC-0108 D1 rules 1 to 10 as corrected and the `skill-html-views` direction's ranked goals, leaves no Major or Blocker finding after adjudication, recorded in the ledger with the 16 screenshots' SHA-256 values.

### Amended criteria and rules

| Amended spec: criterion or rule | Disposition |
| --- | --- |
| Session-start 0015, its ten sentences and rule order | Carried unchanged |
| Session-start 0015, "and no prompt, `code` element or copy control" | Replaced by AC-0001 to AC-0007 |
| Session-start Never-do "Never show a copyable prompt, launch anything, reach the network, or write anywhere but the export destination" | Narrowed to admit this spec's prompt; launching, network and writing carried unchanged |
| Dependency-graphs Never-do "Show readiness or a copyable prompt, launch anything, reach the network, or change the shipped content-security policy string" | Narrowed to admit this spec's prompt; readiness, launching, network and the policy string carried unchanged |

## Follow-ons

- eugenelim: `docs/product/briefs/intent-navigation-delivery.md` slice 11b — the readiness bridge, `export --readiness -`.

## Assumptions

none
