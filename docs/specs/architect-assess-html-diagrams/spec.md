# Spec: architect-assess HTML report draws diagrams on request

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs/specs/architect-assess-html-report/spec.md`](../architect-assess-html-report/spec.md) and [`docs/specs/architect-assess-html-report-style/spec.md`](../architect-assess-html-report-style/spec.md) — escaped values, closed element and attribute lists, one `<style>` named by a hash, confined I/O, fixed exit tokens. This spec relaxes the "no script, no network" rules only when the reader asks for diagrams, and the Amended parent rules table below lists every parent rule it touches. The decision record is [`docs/specs/architect-assess-html-report/notes/diagram-rendering-decision.md`](../architect-assess-html-report/notes/diagram-rendering-decision.md).
- **Brief:** none
- **Discovery:** none
- **Depends on:** spec:architect-assess-html-report-style
- **Contract:** none — a command-line flag, one script asset, and markup; no API, event, or RPC contract.
- **Shape:** ui — the look and behavior of a generated read-only page.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`, `What
> Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working material.

## Outcome

A maintainer who runs the renderer with `--diagrams` opens a report whose Mermaid diagrams are drawn in place, in the page's light or dark theme, with the source still shown beneath each drawing. Without the flag nothing changes: the page runs no script and makes no network request. With the flag, the page loads one pinned Mermaid build from one named host, bound by an integrity hash, runs one script of this pack's own, and tells the reader that opening the report contacts that host. A diagram that is unsafe to draw, or that fails to draw, stays as source with a visible note.

Drawing is opt-in because a report is built from untrusted repository text, and an opened report would otherwise tell the CDN host who opened it and when. The pinned build is the `mermaid` version `docs-site` already pins and the repository's npm audit already covers.

## What Changes

- The renderer accepts an optional `--diagrams` flag after the effort directory, marks eligible Mermaid fences, adds two script elements and an extended policy, and shows a privacy note — `scripts/render_html.py`.
- A script asset draws the diagrams, confines the styles Mermaid emits, and falls back to source on any failure — `scripts/report_assets/diagrams.js`.
- An ADR records the dependency before the code adds it; the decision note names the chosen option — `docs/adr/`, `notes/diagram-rendering-decision.md`.
- The parent specs' affected rules, the reference, the skill, both guides, the eval, and the release surface follow — listed in Durable Outputs.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale and dependency record | A third-party script now runs in a generated page, opt-in, pinned and hashed | `docs/adr/` (new record, accepted before the renderer change) | eugenelim | the ADR | names the version, URL, hash, the SRI-as-binding-control point, opt-in rule, CSP, audit path, and revisit triggers |
| Interface compatibility | Parent rules say "no script, no network" | the two parent specs, per the Amended parent rules table | eugenelim | diff, roster grep | each listed rule carries the exception and cites this spec |
| Current product truth | The decision note is the open question this answers | `notes/diagram-rendering-decision.md` | eugenelim | diff | states the chosen option and that drawing is opt-in |
| User-facing promise | The mode gains a flag and a privacy note | `references/html-report.md`, `SKILL.md`, `guides/architect/reference/architecture-assessment.md`, `guides/architect/how-to/assess-a-repository.md` | eugenelim | grep in `tests/roster` | each names `--diagrams`, the host, the offline default, and the sharing warning |
| Verification record | Real-browser drawing, confinement, CSP, and fallbacks are manual | `docs/specs/architect-assess-html-diagrams/notes/verification-ledger.md` | eugenelim | the ledger | holds the observations, hash provenance, and review results |
| Release history | A pack change ships by version bump | `pack.toml`, `plugin.json`, changelog fragment | eugenelim | parity test, fragment validates | patch bump above `origin/main`; the flag and asset live inside an existing skill, so no new primitive |

## Amended parent rules

Each row is amended in place to read "except with `--diagrams`, which `docs/specs/architect-assess-html-diagrams/spec.md` owns", and a roster check confirms the text.

| Parent spec | Rule (quoted start) |
| --- | --- |
| html-report | Ask first: "Any `<script>` element in the output" |
| html-report | Never do: "Load script, style, font, or image from a network location" |
| html-report | Never do: "Add a third-party dependency, a vendored third-party asset" |
| html-report | Criterion: "Each Mermaid fence appears as a `<pre>` under the visible label `Diagram source (not rendered)`" |
| html-report | Criterion: "`references/html-report.md` lists every exit 2 reason" |
| html-report | Criterion: "Opened in a real browser, a sample report shows shaded heat cells" (its "no script run") |
| html-report-style | Constrained by: "no script, no network" |
| html-report-style | Ask first: "Any element, attribute, or CSP source beyond those the acceptance criteria name" |
| html-report-style | Never do: "Add a script, a web font, an image, or any network reference to the page" |
| html-report-style | Criterion: "Every element in the parsed output is one of" |
| html-report-style | Criterion: "Every attribute in the parsed output is one of" |

## Agent Rules

### Always do

- Treat every byte of `assessment.md` as untrusted. Drawing never relaxes escaping, the closed lists, or the size caps.
- Set Mermaid's configuration in pack code only; no report text reaches it.
- Pass `--diagrams` only when the user asks for drawn diagrams.

### Ask first

- Any script source, CSP source, element, or attribute beyond those the acceptance criteria name.
- Changing the pinned version or hash; a bump is its own change, checked against the npm tarball.

### Never do

- Allow `unsafe-inline`, `unsafe-eval`, a wildcard, or a host-only source in `script-src`.
- Insert Mermaid output through an HTML-string sink (`innerHTML`, `insertAdjacentHTML`, `outerHTML`).
- Load any other third-party file, font, image, or style.

## Testing Strategy

- Flag parsing, markup, eligibility rules, policy text, script-tag attributes, asset loading and refusals, privacy note, caps, list membership, and the text rules over `diagrams.js`: TDD, because each is an input-to-output rule over rendered HTML or a text rule over a file.
- Parity of the pinned version, URL, and hash with the ADR and `docs-site`, and the amended parent text and doc names: goal-based roster checks outside the pack tree.
- Drawing, theme, SVG and style confinement, hostile fences, integrity failure, offline fallback, missing stylesheet support, syntax-error fence: manual QA in a real browser over the sample fixture, run against hostile fixtures that fail if the behavior is wrong, with `design-review` and `experience-reviewer` passes. The script is an inline file with no module exports, so the pure checks (selector splitting, scoping, id ownership, references, banned properties) run from the shipped file in one node process in the pack tests, and the DOM behaviour is left to the browser run.

## Acceptance Criteria

### Arguments and default page

- [x] `render_html.py <dir>` exits 0 on a valid report.
- [x] `render_html.py <dir> --diagrams` exits 0 on a valid report.
- [x] Zero arguments, more than two arguments, or a second argument other than `--diagrams` exit 2 with the usage token `render_html: usage: render_html.py <effort-dir> [--diagrams]`.
- [x] The first argument is always treated as the effort directory path, whatever its text.
- [x] Without `--diagrams`, the output has no `script` element.
- [x] Without `--diagrams`, the output has no `src` attribute.
- [x] Without `--diagrams`, the policy is `default-src 'none'; style-src 'sha256-` plus the hash of the page's own `<style>` text, then `'; base-uri 'none'; form-action 'none'`.
- [x] Without `--diagrams`, `diagrams.js` is not read.
- [x] Without `--diagrams`, a missing `diagrams.js` leaves the output and the exit code unchanged.

### Diagrams page markup

- [x] With `--diagrams`, the last two children of `body`, after `main`, are two `script` elements, the external one first.
- [x] The external `script` has `src` equal to the pinned URL, `integrity` equal to the pinned `sha384-` value, `crossorigin` equal to `anonymous`, `referrerpolicy` equal to `no-referrer`, and the `defer` attribute, and the inline script starts the drawing once the document has loaded.
- [x] The inline `script` holds the text of `report_assets/diagrams.js`.
- [x] With `--diagrams`, the policy's `script-src` holds exactly the `sha256-` hash of the inline script text and the pinned URL.
- [x] With `--diagrams`, the policy's other directives equal the default page's, so `style-src` stays one `sha256-` hash.
- [x] With `--diagrams`, a `div` with class `note notice-diagrams` follows the untrusted-content notice and reads: `Diagrams are drawn by Mermaid <version>, loaded from cdn.jsdelivr.net. Opening this report sends your IP address, the time, and your browser details to that host, and the report's web address if it is served from a web host; no report text is sent.`
- [x] The closed element list admits `script` only in `--diagrams` output.
- [x] The closed attribute list admits `src`, `integrity`, `crossorigin`, `referrerpolicy`, and `defer` on a `script` only in `--diagrams` output.
- [x] The pinned version is one constant in `render_html.py` equal to the `mermaid` version in `docs-site/package.json`, confirmed by a roster check.
- [x] The pinned URL is `https://cdn.jsdelivr.net/npm/mermaid@<version>/dist/mermaid.min.js`, built from the version constant.
- [x] The pinned `sha384-` value is one constant in `render_html.py` equal to the value in the ADR, confirmed by a roster check.

### Eligibility

Eligibility reads the fence text after one normalisation: the renderer refuses, as not drawable, any fence holding a character an HTML parser drops or rewrites (NUL, carriage return, U+FEFF, U+2028, U+2029, U+0085) any whitespace character other than ASCII space, tab, and line feed (so U+00A0, U+1680, U+2000–U+200A, U+202F, U+205F, and U+3000), or any other control character except tab and line feed, so the text the rules read equals the browser's `textContent`.

- [x] With `--diagrams`, a fence is drawn only when its first non-blank line, where blank means ASCII space, tab, and line feed only, starts with `flowchart`, `graph`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`, or `erDiagram`, matched case-sensitively after trimming leading ASCII space and tab.
- [x] With `--diagrams`, a fence is not drawn when any line contains `%%{`.
- [x] With `--diagrams`, a fence is not drawn when any statement starts, ignoring case, with the letters `click`, `link`, or `callback` (a prefix match, so a node named `linkerd` is refused), except a statement starting with the keyword `linkStyle`, where a statement starts after a line start or a semicolon, after trimming ASCII whitespace.
- [x] With `--diagrams`, a fence is not drawn when its text exceeds 50,000 UTF-8 bytes.
- [x] With `--diagrams`, the first 20 fences in document order that pass every rule are drawn; a refused fence is not counted.
- [x] With `--diagrams`, a fence that passes every rule and is among the first 20 has class `diagram-drawn` on its `div.diagram` and the label `Diagram source (not drawn yet)`, which the script changes to `Diagram (source below)` after a successful draw.
- [x] With `--diagrams`, a fence refused by a rule has no `diagram-drawn` class and the label `Diagram source (not drawn: unsafe)`.
- [x] With `--diagrams`, a fence that passes every rule but follows the first 20 has no `diagram-drawn` class and the label `Diagram source (not drawn: limit)`.
- [x] Without `--diagrams`, every Mermaid fence keeps the label `Diagram source (not rendered)`.
- [x] A hostile fence set holding a NUL-split `%%{`, a NUL-split `click`, a U+FEFF-led `---`, a U+00A0-led first line, a U+00A0-led `click` and a U+3000-led `link` after a semicolon, `A-->B; click A href "x"`, a `link` line, a `callback` line, and a frontmatter block is refused by the rules above.

### Script text rules (`diagrams.js`)

- [x] `diagrams.js` calls `mermaid.initialize` with `securityLevel` `strict`, `startOnLoad` `false`, `suppressErrorRendering` `true`, `htmlLabels` `false`, `maxTextSize` `50000`, and `maxEdges` `500`.
- [x] `diagrams.js` always renders with the theme `neutral`, and `report.css` inverts the drawing on a dark screen and not in print.
- [x] `diagrams.js` draws only `.diagram-drawn` blocks and passes `mermaid.render` exactly the `textContent` of the block's `code` element.
- [x] `diagrams.js` gives each render an id of the form `mmd_d<number>`, an id the page's heading ids can never take because they hold no underscore.
- [x] `diagrams.js` holds none of `innerHTML`, `insertAdjacentHTML`, `outerHTML`, `eval`, `Function(`, `document.write`.

### Script behavior (ledger)

- [x] The inserted SVG holds no `style` element and no `style` attribute: its `style` elements go to the checked sheet, and each inline style becomes a rule in the same sheet, marked important, selecting the element by the render id and a `data-mmd` number.
- [x] The inserted SVG holds only these elements: `svg`, `g`, `path`, `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, `text`, `tspan`, `defs`, `marker`, `title`, `desc`, `clipPath`, `filter`, `feDropShadow`, `linearGradient`, `stop`, `symbol`; any other element, such as `a`, `use`, `image`, `foreignObject`, or `script`, leaves the block as source.
- [x] Every `id` inside the inserted SVG equals the SVG's render id or starts with the render id followed by `-` or `_`, because the script rewrites any other `id` to start with the render id and a `-`, and rewrites the same-document `url(#…)` references to match.
- [x] The inserted SVG holds no attribute whose name, ignoring any namespace prefix, is `href`, `src`, or starts with `on`, and no `url(` reference except to a fragment of the same document.
- [x] The page adopts a drawn SVG's stylesheet only when every rule is a style rule, a `@keyframes` rule, or a grouping rule (`@media`, `@supports`, `@layer` block, `@container`) whose contents pass the same test, and each style rule's selectors, split at the commas a CSS parser splits at (quoted text and escaped characters are data, and a list that cannot be split with certainty refuses the sheet), start with exactly that SVG's `#id` followed by nothing, a descendant combinator, or a child combinator, and hold no `~` or `+`.
- [x] A style rule that holds a nested rule leaves the block as source.
- [x] A sheet holding a `@keyframes` rule named other than `dash` or `edge-animation-frame` leaves the block as source.
- [x] `report.css` gives `.diagram-render` horizontal overflow of `auto` and a `max-width` of `100%`, so a drawing cannot paint outside its block, and avoids a page break inside it in print.
- [x] `report.css` gives a drawing's `svg` a `min-width` of `32rem`, so its text stays readable and a narrow screen scrolls sideways inside the block.
- [x] `report.css` sets `animation` to `none !important` on a drawing and everything in it, so a drawing never moves.
- [x] The script gives the drawing's holder `role` `region` and an `aria-label` of `Drawn diagram <n> of <total>` followed by `: ` and the section name when the source block has one, and sets `tabindex` `0` on it only while the drawing is wider than the holder.
- [x] A sheet in which the root rule (the selector `#id` or one ending in `svg`) or any keyframe declares `position`, `float`, `top`, `right`, `bottom`, `left`, `transform`, `z-index`, `translate`, `rotate`, `scale`, or any property whose name is or starts with `margin`, `inset`, or `offset` leaves the block as source; descendant rules are exempt because only the outer `svg` takes part in page layout and no HTML element can sit inside the drawing.
- [x] A sheet holding any other rule, such as `@import`, `@font-face`, `@namespace`, `@property`, or `@page`, or any unscoped rule, leaves the block as source.
- [x] `diagrams.js` treats the Mermaid global as missing unless `mermaid.initialize` and `mermaid.render` are functions, and any exception at any stage leaves the block as source.
- [x] On any failure, `diagrams.js` sets the block's label to `Diagram source (not drawn)` and removes every element Mermaid left in the document.
- [x] A heading whose slug is `mermaid` leaves every drawn-eligible block labelled `Diagram source (not drawn)` and raises no uncaught script error when the CDN script is blocked.

### Asset and caps

- [x] With `--diagrams`, a `diagrams.js` the confinement helper reports as missing or unsafe, including a symlink or a non-regular file, is refused with exit 3 and the token `render_html: failed: script asset missing or unsafe`.
- [x] With `--diagrams`, a `diagrams.js` over 64 KiB is refused with exit 3 and the token `render_html: failed: script asset over the size cap`.
- [x] With `--diagrams`, a `diagrams.js` that is not UTF-8 is refused with exit 3 and the token `render_html: failed: script asset unreadable`.
- [x] With `--diagrams`, a `diagrams.js` holding `</script`, `<!--`, or a carriage return, matched ignoring case, is refused with exit 3 and the token `render_html: failed: script asset holds forbidden text`.
- [x] The 2 MiB source cap and the 16 MiB page cap hold with the flag.
- [x] Fence text and every attribute value stay escaped in both modes.

### Real browser (ledger)

- [x] Opened with network access to `cdn.jsdelivr.net`, each `div.diagram-drawn` shows a drawn SVG above its source block in light and in dark, with node text legible, recorded in the ledger.
- [x] A drawn fence using `classDef`, `style`, and `linkStyle`, with a class named like the notices, leaves the notices, the banner, and the state mark visible, unchanged, and on top, recorded in the ledger.
- [x] A fence label carrying a script payload that would set a visible sentinel leaves the sentinel unset, recorded in the ledger.
- [x] With a stub `mermaid` whose sheet hides a comma inside a quoted string and another behind an escape, the block stays as source, recorded in the ledger.
- [x] With a stub `mermaid` whose `render` returns an SVG holding an `a`, an `image`, an `href`, an `onclick`, a nested style rule, an `@import`, a root rule with `position`, a sibling selector, or a plus selector, each case leaves its block as source and the page outside the block, including the label and the source block, unchanged, recorded in the ledger.
- [x] A fence with a syntax error shows the label `Diagram source (not drawn)` and no other graphic, recorded in the ledger.
- [x] With the `integrity` value altered, no diagram is drawn and each drawn-eligible block shows the label `Diagram source (not drawn)`, recorded in the ledger.
- [x] With the network blocked, the report is fully readable and each drawn-eligible block shows the label `Diagram source (not drawn)`, recorded in the ledger.
- [x] With `CSSStyleSheet` removed before the script runs, each drawn-eligible block shows the label `Diagram source (not drawn)`, recorded in the ledger.
- [x] The ledger records that the tarball's integrity equals the `docs-site` lockfile value.
- [x] The ledger records that the tarball's `dist/mermaid.min.js` SHA-384 equals the constant.
- [x] The ledger records that the bytes the CDN serves equal the tarball's `dist/mermaid.min.js`.
- [x] An `experience-reviewer` pass over the light, dark, narrow, and offline screenshots, and a `design-review` self-review of the same, leave no Major or Blocker after adjudication, recorded in the ledger.

### Docs and release

- [x] The ADR has status Accepted with a date, and states the decision, version, URL, and hash.
- [x] The ADR states that SRI binds the bytes, that drawing is opt-in, the policy, that `docs-site`'s npm audit covers the pinned version, and the revisit triggers: a published advisory against the pinned version, or a change to the CDN host.
- [x] Each row of the Amended parent rules table carries the exception text and cites this spec, confirmed by a roster check.
- [x] `references/html-report.md` names `--diagrams`, the host, the offline default, the new usage token, and the new exit 3 tokens.
- [x] `references/html-report.md` scopes its statement that diagrams are source blocks, not drawings, to the page without `--diagrams`.
- [x] `SKILL.md`, the reference guide, and the how-to guide each name `--diagrams` and the host.
- [x] `SKILL.md`, the reference guide, and the how-to guide each state that drawn reports contact the host and should not be shared with readers who expect the offline default.
- [x] `SKILL.md` states that `--diagrams` is passed only when the user asks for drawn diagrams.
- [x] `evals/evals.json` holds one case that asks for drawn diagrams and asserts the flag is used.
- [x] `evals/evals.json` holds one plain HTML request that asserts the flag is absent.
- [x] The decision note states the chosen option and that drawing is opt-in.
- [x] `pack.toml` and `plugin.json` carry matching versions, a patch bump above `origin/main`.
- [x] A changelog fragment for the release validates.

## Terminal Intent

`code` — add the flag, the script asset, the eligibility rules, the policy change, and the docs, ADR, and release surface.

## Follow-ons

- eugenelim: vendoring or a local `--mermaid-js` file, if offline drawing is wanted later.

## Assumptions

- Product: drawing is opt-in, not the default — whether the default should flip once the owner has seen the page (settled by: the owner).
- Technical: Mermaid 12.2.0 draws the fixture's flowchart and sequence diagram under the strict policy — settled by browser QA, which showed it needs the extra elements and the id rewrite above; cylinder labels sit off-centre with `htmlLabels` off, accepted as a cosmetic limit.
- Technical: `@keyframes` names in an adopted sheet are page-wide, so one diagram can rename another's animation — whether to prefix them (settled by: the owner; no security effect).
- Technical: Mermaid 12.2.0 places cylinder-shaped node labels off-centre, which this work leaves because the fix belongs upstream — whether to hide that shape or wait for a fix (settled by: the owner).
- Technical: a browser without constructable stylesheets shows source blocks only with the label `Diagram source (not drawn)` — whether that is acceptable (settled by: the owner).

## Changelog

<!-- Approvals only. -->
- 2026-10-31: spec approved by eugenelim (opt-in flag, pinned CDN with integrity hash)
- 2026-10-31: spec amendment approved by eugenelim (SVG elements, id rewrite, root-scoped ban, selector splitting, keyframe names)
