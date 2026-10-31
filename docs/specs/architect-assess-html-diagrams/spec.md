# Spec: architect-assess HTML report draws diagrams on request

- **Status:** Draft
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
- Drawing, theme, SVG and style confinement, hostile fences, integrity failure, offline fallback, missing stylesheet support, syntax-error fence: manual QA in a real browser over the sample fixture, run against hostile fixtures that fail if the behavior is wrong, with `design-review` and `experience-reviewer` passes. The script is an inline file with no module exports, so a node suite would test a copy; pack JavaScript elsewhere uses node suites, and this deviation is deliberate.

## Acceptance Criteria

### Arguments and default page

- [ ] `render_html.py <dir>` exits 0 on a valid report.
- [ ] `render_html.py <dir> --diagrams` exits 0 on a valid report.
- [ ] Zero arguments, more than two arguments, or a second argument other than `--diagrams` exit 2 with the usage token `render_html: usage: render_html.py <effort-dir> [--diagrams]`.
- [ ] The first argument is always treated as the effort directory path, whatever its text.
- [ ] Without `--diagrams`, the output has no `script` element.
- [ ] Without `--diagrams`, the output has no `src` attribute.
- [ ] Without `--diagrams`, the policy is `default-src 'none'; style-src 'sha256-` plus the hash of the page's own `<style>` text, then `'; base-uri 'none'; form-action 'none'`.
- [ ] Without `--diagrams`, `diagrams.js` is not read.
- [ ] Without `--diagrams`, a missing `diagrams.js` leaves the output and the exit code unchanged.

### Diagrams page markup

- [ ] With `--diagrams`, the last two children of `body`, after `main`, are two `script` elements, the external one first.
- [ ] The external `script` has `src` equal to the pinned URL, `integrity` equal to the pinned `sha384-` value, `crossorigin` equal to `anonymous`, and `referrerpolicy` equal to `no-referrer`.
- [ ] The inline `script` holds the text of `report_assets/diagrams.js`.
- [ ] With `--diagrams`, the policy's `script-src` holds exactly the `sha256-` hash of the inline script text and the pinned URL.
- [ ] With `--diagrams`, the policy's other directives equal the default page's, so `style-src` stays one `sha256-` hash.
- [ ] With `--diagrams`, a `div` with class `note notice-diagrams` follows the untrusted-content notice and reads: `Diagrams are drawn by Mermaid <version>, loaded from cdn.jsdelivr.net. Opening this report sends your IP address, the time, and your browser details to that host; no report text and no page address is sent.`
- [ ] The closed element list admits `script` only in `--diagrams` output.
- [ ] The closed attribute list admits `src`, `integrity`, `crossorigin`, and `referrerpolicy` on a `script` only in `--diagrams` output.
- [ ] The pinned version is one constant in `render_html.py` equal to the `mermaid` version in `docs-site/package.json`, confirmed by a roster check.
- [ ] The pinned URL is `https://cdn.jsdelivr.net/npm/mermaid@<version>/dist/mermaid.min.js`, built from the version constant.
- [ ] The pinned `sha384-` value is one constant in `render_html.py` equal to the value in the ADR, confirmed by a roster check.

### Eligibility

Eligibility reads the fence text after one normalisation: the renderer refuses, as not drawable, any fence holding a character an HTML parser drops or rewrites (NUL, carriage return, U+FEFF, U+2028, U+2029, U+0085) any whitespace character other than ASCII space, tab, and line feed (so U+00A0, U+1680, U+2000–U+200A, U+202F, U+205F, and U+3000), or any other control character except tab and line feed, so the text the rules read equals the browser's `textContent`.

- [ ] With `--diagrams`, a fence is drawn only when its first non-blank line, where blank means ASCII space, tab, and line feed only, starts with `flowchart`, `graph`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`, or `erDiagram`, matched case-sensitively from the first character of that line.
- [ ] With `--diagrams`, a fence is not drawn when any line contains `%%{`.
- [ ] With `--diagrams`, a fence is not drawn when any statement starts with `click`, `link`, `links`, or `callback`, where a statement starts after a line start or a semicolon, after trimming ASCII whitespace, and the match ignores case.
- [ ] With `--diagrams`, a fence is not drawn when its text exceeds 50,000 UTF-8 bytes.
- [ ] With `--diagrams`, the first 20 fences in document order that pass every rule are drawn; a refused fence is not counted.
- [ ] With `--diagrams`, a fence that passes every rule and is among the first 20 has class `diagram-drawn` on its `div.diagram` and the label `Diagram (source below)`.
- [ ] With `--diagrams`, a fence refused by a rule has no `diagram-drawn` class and the label `Diagram source (not drawn: unsafe)`.
- [ ] With `--diagrams`, a fence that passes every rule but follows the first 20 has no `diagram-drawn` class and the label `Diagram source (not drawn: limit)`.
- [ ] Without `--diagrams`, every Mermaid fence keeps the label `Diagram source (not rendered)`.
- [ ] A hostile fence set holding a NUL-split `%%{`, a NUL-split `click`, a U+FEFF-led `---`, a U+00A0-led first line, a U+00A0-led `click` and a U+3000-led `link` after a semicolon, `A-->B; click A href "x"`, a `link` line, a `callback` line, and a frontmatter block is refused by the rules above.

### Script text rules (`diagrams.js`)

- [ ] `diagrams.js` calls `mermaid.initialize` with `securityLevel` `strict`, `startOnLoad` `false`, `suppressErrorRendering` `true`, `htmlLabels` `false`, `maxTextSize` `50000`, and `maxEdges` `500`.
- [ ] `diagrams.js` chooses the theme `dark` when `prefers-color-scheme: dark` matches and `neutral` otherwise.
- [ ] `diagrams.js` draws only `.diagram-drawn` blocks and passes `mermaid.render` exactly the `textContent` of the block's `code` element.
- [ ] `diagrams.js` gives each render an id of the form `mmd_d<number>`, an id the page's heading ids can never take because they hold no underscore.
- [ ] `diagrams.js` holds none of `innerHTML`, `insertAdjacentHTML`, `outerHTML`, `eval`, `Function(`, `document.write`.

### Script behavior (ledger)

- [ ] The inserted SVG holds no `style` element and no `style` attribute.
- [ ] The inserted SVG holds only these elements: `svg`, `g`, `path`, `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, `text`, `tspan`, `defs`, `marker`, `title`, `desc`, `clipPath`, `filter`, `feDropShadow`, `linearGradient`, `stop`, `symbol`; any other element, such as `a`, `use`, `image`, `foreignObject`, or `script`, leaves the block as source.
- [ ] Every `id` inside the inserted SVG equals the SVG's render id or starts with the render id followed by `-` or `_`, because the script rewrites any other `id` to start with the render id and a `-`, and rewrites the same-document `url(#…)` references to match.
- [ ] The inserted SVG holds no `href`, `xlink:href`, `src`, or `on…` attribute, and no `url(` reference except to a fragment of the same document.
- [ ] The page adopts a drawn SVG's stylesheet only when every rule is a style rule, a `@keyframes` rule, or a grouping rule (`@media`, `@supports`, `@layer` block, `@container`) whose contents pass the same test, and each style rule's selectors, split at the commas a CSS parser splits at (quoted text and escaped characters are data, and a list that cannot be split with certainty refuses the sheet), start with exactly that SVG's `#id` followed by nothing, a descendant combinator, or a child combinator, and hold no `~` or `+`.
- [ ] A style rule that holds a nested rule leaves the block as source.
- [ ] A sheet holding a `@keyframes` rule named other than `dash` or `edge-animation-frame` leaves the block as source.
- [ ] `report.css` gives `.diagram-render` horizontal overflow of `auto` and a `max-width` of `100%`, so a drawing cannot paint outside its block.
- [ ] A sheet in which the root rule (the selector `#id` or one ending in `svg`) or any keyframe declares `position`, `inset`, `top`, `right`, `bottom`, `left`, `float`, `transform`, `z-index`, `translate`, `rotate`, `scale`, any `offset` property, or any `margin` property leaves the block as source; descendant rules are exempt because only the outer `svg` takes part in page layout and no HTML element can sit inside the drawing.
- [ ] A sheet holding any other rule, such as `@import`, `@font-face`, `@namespace`, `@property`, or `@page`, or any unscoped rule, leaves the block as source.
- [ ] `diagrams.js` treats the Mermaid global as missing unless `mermaid.initialize` and `mermaid.render` are functions, and any exception at any stage leaves the block as source.
- [ ] On any failure, `diagrams.js` sets the block's label to `Diagram source (not drawn)` and removes every element Mermaid left in the document.
- [ ] A heading whose slug is `mermaid` leaves every drawn-eligible block labelled `Diagram source (not drawn)` and raises no uncaught script error when the CDN script is blocked.

### Asset and caps

- [ ] With `--diagrams`, a `diagrams.js` the confinement helper reports as missing or unsafe, including a symlink or a non-regular file, is refused with exit 3 and the token `render_html: failed: script asset missing or unsafe`.
- [ ] With `--diagrams`, a `diagrams.js` over 64 KiB is refused with exit 3 and the token `render_html: failed: script asset over the size cap`.
- [ ] With `--diagrams`, a `diagrams.js` that is not UTF-8 is refused with exit 3 and the token `render_html: failed: script asset unreadable`.
- [ ] With `--diagrams`, a `diagrams.js` holding `</script`, `<!--`, or a carriage return, matched ignoring case, is refused with exit 3 and the token `render_html: failed: script asset holds forbidden text`.
- [ ] The 2 MiB source cap and the 16 MiB page cap hold with the flag.
- [ ] Fence text and every attribute value stay escaped in both modes.

### Real browser (ledger)

- [ ] Opened with network access to `cdn.jsdelivr.net`, each `div.diagram-drawn` shows a drawn SVG above its source block in light and in dark, with node text legible, recorded with screenshots.
- [ ] A fence using `classDef`, `style`, and `linkStyle` aimed at the notices, the banner, and the state mark leaves all three visible, unchanged, and on top, recorded with screenshots.
- [ ] A fence whose styles use sibling selectors leaves the label and the source block visible, recorded with a screenshot.
- [ ] A fence label carrying a script payload that would set a visible sentinel leaves the sentinel unset, recorded in the ledger.
- [ ] With a stub `mermaid` whose sheet hides a comma inside a quoted string and another behind an escape, the block stays as source, recorded in the ledger.
- [ ] With a stub `mermaid` whose `render` returns an SVG holding an `a`, an `image`, an `href`, an `onclick`, a `style` element, a nested style rule, an `@import`, a root rule with `position`, and a sibling selector, each case leaves its block as source and the page outside the block unchanged, recorded in the ledger.
- [ ] A fence with a syntax error shows the label `Diagram source (not drawn)` and no other graphic, recorded with a screenshot.
- [ ] With the `integrity` value altered, no diagram is drawn and each drawn-eligible block shows the label `Diagram source (not drawn)`, recorded with a screenshot.
- [ ] With the network blocked, the report is fully readable and each drawn-eligible block shows the label `Diagram source (not drawn)`, recorded with a screenshot.
- [ ] With `CSSStyleSheet` removed before the script runs, each drawn-eligible block shows the label `Diagram source (not drawn)`, recorded in the ledger.
- [ ] The ledger records that the tarball's integrity equals the `docs-site` lockfile value.
- [ ] The ledger records that the tarball's `dist/mermaid.min.js` SHA-384 equals the constant.
- [ ] The ledger records that the bytes the CDN serves equal the tarball's `dist/mermaid.min.js`.
- [ ] A `design-review` and an `experience-reviewer` pass over the light and dark screenshots of the drawn page leave no Major or Blocker after adjudication, recorded in the ledger.

### Docs and release

- [ ] The ADR has status Accepted with a date, and states the decision, version, URL, and hash.
- [ ] The ADR states that SRI binds the bytes, that drawing is opt-in, the policy, that `docs-site`'s npm audit covers the pinned version, and the revisit triggers: a published advisory against the pinned version, or a change to the CDN host.
- [ ] Each row of the Amended parent rules table carries the exception text and cites this spec, confirmed by a roster check.
- [ ] `references/html-report.md` names `--diagrams`, the host, the offline default, the new usage token, and the new exit 3 tokens.
- [ ] `references/html-report.md` scopes its statement that diagrams are source blocks, not drawings, to the page without `--diagrams`.
- [ ] `SKILL.md`, the reference guide, and the how-to guide each name `--diagrams` and the host.
- [ ] `SKILL.md`, the reference guide, and the how-to guide each state that drawn reports contact the host and should not be shared with readers who expect the offline default.
- [ ] `SKILL.md` states that `--diagrams` is passed only when the user asks for drawn diagrams.
- [ ] `evals/evals.json` holds one case that asks for drawn diagrams and asserts the flag is used.
- [ ] `evals/evals.json` holds one plain HTML request that asserts the flag is absent.
- [ ] The decision note states the chosen option and that drawing is opt-in.
- [ ] `pack.toml` and `plugin.json` carry matching versions, a patch bump above `origin/main`.
- [ ] A changelog fragment for the release validates.

## Terminal Intent

`code` — add the flag, the script asset, the eligibility rules, the policy change, and the docs, ADR, and release surface.

## Follow-ons

- eugenelim: vendoring or a local `--mermaid-js` file, if offline drawing is wanted later.

## Assumptions

- Product: drawing is opt-in, not the default — whether the default should flip once the owner has seen the page (settled by: the owner).
- Technical: Mermaid 12.2.0 draws the fixture's flowchart and sequence diagram under the strict policy — settled by browser QA, which showed it needs the extra elements and the id rewrite above; cylinder labels sit off-centre with `htmlLabels` off, accepted as a cosmetic limit.
- Technical: `@keyframes` names in an adopted sheet are page-wide, so one diagram can rename another's animation — whether to prefix them (settled by: the owner; no security effect).
- Technical: a browser without constructable stylesheets shows source blocks only with the label `Diagram source (not drawn)` — whether that is acceptable (settled by: the owner).

## Changelog

<!-- Approvals only. -->
- 2026-10-31: spec approved by eugenelim (opt-in flag, pinned CDN with integrity hash)
