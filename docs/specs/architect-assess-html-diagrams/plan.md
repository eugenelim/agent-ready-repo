# Plan: architect-assess HTML report draws diagrams on request

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** the renderer and its tests in `packs/architect/.apm/skills/architect-assess/scripts/render_html.py` and `packs/architect/tests/skills/architect-assess/test_render_html.py`; the stylesheet asset loader `load_stylesheet` and the `ASSET_NAMES` and `FORBIDDEN_ASSET_TEXT` constants, which the script asset follows; the exact-version CDN precedent in `docs/specs/cdn-sri-mermaid/spec.md`; the measured facts and options in `docs/specs/architect-assess-html-report/notes/diagram-rendering-decision.md`; the byte-identity roster tests in `tests/roster/test_architect_assess_*.py`.

> **Plan contract:** `Touches`, `Tests` and `Done when` are what a completion gate
> reads; `Design`, `Approach` and `Risks` are working material.

## Approach

Write the ADR and name the pinned build first, because the repository asks for a dependency record before the dependency is added. Then add the flag, the eligibility rules, the script elements and the policy to the renderer. Then write `diagrams.js`. Then the docs, eval, parent-rule amendments and release surface. A real-browser pass closes the work, because drawing, style confinement, the policy and the fallbacks only show there.

A spike on 2026-10-31 in Microsoft Edge fixed the main design choice. Mermaid 12.2.0, loaded from jsDelivr at the pinned URL with its integrity hash and `referrerpolicy="no-referrer"`, renders under `default-src 'none'` and a one-hash `style-src` only when the script moves each SVG's `<style>` into a constructable stylesheet before insertion. The `docs-site` lockfile pins the same version with a tarball integrity value; the tarball's `dist/mermaid.min.js` and the CDN's file were byte-identical, and the ADR records the hash.

The heat-map glyph and divider tweaks ship as a separate small change; they are not part of this spec.

## Constraints

- AGENTS.md: record a new dependency in an ADR before adding it; reuse the repository's solution first.
- The parent specs' security rules stay in force; the lists widen only as the acceptance criteria name, and only when the flag is present.
- `packs/AGENTS.md`: a non-cosmetic pack update also updates the pack's eval harness; a pack change bumps `pack.toml` and `plugin.json` together; shipped pack content cites no internal records.

## Construction tests

**Integration tests:** one test renders the sample fixture with and without the flag and checks the scripts, policy, note, labels, drawing markers, and that the default page has no script and no `src`.
**Manual verification:** T5.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| ADR and dependency record | T1 | the ADR | version, URL, hash, SRI, opt-in, CSP, audit path, revisit triggers |
| Pin parity (version, URL, hash) | T1 | roster test | passes against `docs-site` and the ADR |
| Parent rule amendments | T4 | diff, roster grep | each row of the table carries the exception |
| Decision note | T1 | diff | states the chosen option |
| Reference, skill, guides, eval | T4 | grep, eval JSON test | name the flag, host, offline default, sharing warning |
| Verification ledger | T5 | the ledger | observations, hash provenance, review results |
| Release surface | T4 | parity test, fragment | `validate` green |

## Design (LLD)

### Design decisions

- The flag is the second command-line argument; nothing else is accepted. The default output has no script and no network reference, and `diagrams.js` is not read without the flag.
- The pinned version equals the `docs-site` pin, so the existing npm audit covers it and a bump in `docs-site` fails the parity test until the hash is refreshed. The URL is the exact `dist/mermaid.min.js` path; SRI with `crossorigin="anonymous"` is what binds the bytes, and the policy's URL source narrows where the script may come from.
- Both scripts are the last children of `body`, after `main`, external first. The inline script is the text of `report_assets/diagrams.js`, read through the confinement helper with a 64 KiB cap, refused if it holds `</script`, `<!--` or a carriage return (so the browser's text equals the hashed text), and hashed with SHA-256 for the policy.
- Eligibility is decided in Python over the same unescaped text `diagrams.js` reads from the `code` element's `textContent`: drawn only when the first non-blank line starts with an allowlisted diagram keyword, no line holds `%%{`, no statement (after a line start or a semicolon) starts with `click`, `link`, `links` or `callback`, the text holds no character an HTML parser drops or rewrites and no Unicode space other than ASCII space, tab and line feed, and the text is at most 50,000 UTF-8 bytes; the first 20 passing fences are drawn and later passing fences get the limit label.
- The script initializes Mermaid with `securityLevel: 'strict'`, `startOnLoad: false`, `suppressErrorRendering: true`, `maxTextSize: 50000`, `maxEdges: 500`, and a theme from `prefers-color-scheme`. For each marked block it renders the text under an id of the form `mmd_d<number>` (headings never produce an underscore), parses the SVG with `DOMParser`, accepts it only when it holds allowlisted SVG drawing elements (including the filter, gradient and symbol elements Mermaid 12.2.0 emits) and no navigating or loading attribute, rewrites any `id` that does not start with the render id, and the same-document `url(#…)` references to it, removes every `style` element and attribute, reads the removed styles into a `CSSStyleSheet` with `replaceSync`, and accepts the sheet only when every rule is a style rule, a `@keyframes` rule or a checked grouping rule, the root rule and keyframes declare no positioning, `transform`, `z-index` or `translate` (descendant rules are exempt because no HTML element can sit inside the drawing), no style rule holds a nested rule, and every style selector starts with exactly that `#id` followed by nothing, a descendant combinator or a child combinator and holds no `~` or `+`; then it adds the sheet to `document.adoptedStyleSheets` and inserts the parsed SVG above the source block. Any failure, including a `mermaid` global whose `initialize` or `render` is not a function, leaves the source, sets the label to `Diagram source (not drawn)`, and removes anything Mermaid left in the document. The security argument rests on strict mode, the policy, and this confinement, not on `DOMParser`.
- The privacy note is a `div` with class `note notice-diagrams` and the text given in the spec; the external script's `referrerpolicy="no-referrer"` keeps the page address out of the request.

## Tasks

### T1 — ADR, decision note, pinned constants

Depends on: none
Verification mode: goal-based
Touches: a new ADR in `docs/adr/`, `docs/specs/architect-assess-html-report/notes/diagram-rendering-decision.md`, a roster test that reads the constants from `render_html.py` and compares them with `docs-site/package.json` and the ADR, the constants in `scripts/render_html.py`
Tests: the roster parity test (version, URL, hash); the ADR holds each item the spec's ADR criterion names.
Done when: the T1 tests pass and the ADR is accepted.

### T2 — Flag, markup, eligibility, policy, asset loading

Depends on: T1
Verification mode: TDD
Touches: `scripts/render_html.py`, the test file including its element and attribute lists, a stub `scripts/report_assets/diagrams.js` (a one-line comment) until T3
Tests: argument handling and the usage token; default page with no script, no `src`, the old policy, and no read of `diagrams.js`; with the flag, the two scripts' position, order and attributes, the policy, the note, each eligibility rule and the limit, the labels in each state, the filter-sees-what-the-script-reads check with hostile text including NUL, U+FEFF, U+00A0 and semicolon statements, the asset loader's four refusals, the list membership, caps, and escaping in both modes.
Done when: the T2 tests pass.

### T3 — Script asset

Depends on: T2
Verification mode: TDD
Touches: `scripts/report_assets/diagrams.js`, the test file
Tests: text rules over `diagrams.js`: the `initialize` options, the theme rule, the selector, the `textContent` read, the render id form, the absent sinks; the loader accepts the real file. The runtime behaviors (confinement, fallbacks) are checked in T5 against hostile fixtures.
Done when: the T3 tests pass.

### T4 — Docs, parent amendments, eval, release

Depends on: T3
Verification mode: goal-based
Touches: `docs/specs/architect-assess-html-report/spec.md`, `docs/specs/architect-assess-html-report-style/spec.md`, `references/html-report.md`, `SKILL.md`, `guides/architect/reference/architecture-assessment.md`, `guides/architect/how-to/assess-a-repository.md`, `evals/evals.json`, `pack.toml`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` if it carries the version, a changelog fragment, roster tests for the amended text and the doc names, the contract test
Tests: the roster greps; the eval JSON test; the contract tests for the new reference and skill text; the version parity test.
Done when: the T4 tests pass, `FORCE=1 make build-self` leaves only the expected projection diff, and the lint gate passes.

### T5 — Browser QA and design review

Depends on: T4
Verification mode: manual QA
Touches: `docs/specs/architect-assess-html-diagrams/notes/verification-ledger.md`
Tests: render the fixture with `--diagrams` and open it in a real browser in light and dark; read the drawn flowchart and sequence diagram; run the hostile `classDef`, sentinel-payload, sibling-selector and syntax-error fences, a heading named `Mermaid` with the script blocked, and a stub `mermaid` (added through the DevTools protocol) that returns each hostile SVG and sheet; alter the integrity value; block the network; fetch the npm tarball, check its integrity against the `docs-site` lockfile, and compare the SHA-384 of its `dist/mermaid.min.js` with the constant and with the CDN's bytes; run `design-review` and `experience-reviewer` over the screenshots and adjudicate.
Done when: the observations and review results are in the ledger.

## Review

The change adds a third-party script to a generated page, so the security-reviewer fired on the spec and fires at REVIEW on T2 and T3, the frontend-reviewer on the script and markup, and the experience-reviewer on the rendered result.

## Risks

- The CDN could be unreachable or the file removed; the page degrades to source blocks with a note.
- A later Mermaid version could change how it emits styles; the parity test and the QA pass catch that when the `docs-site` pin moves.
- Constructable stylesheets are missing in older browsers; those readers see source blocks only.

## Changelog

<!-- Approvals only. -->
- 2026-10-31: plan approved by eugenelim
- 2026-10-31: plan amendment approved by eugenelim
