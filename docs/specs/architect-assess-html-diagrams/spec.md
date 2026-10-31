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
| Release history | A pack change ships by version bump | `pack.toml`, `plugin.json`, changelog fragment | eugenelim | parity test, fragment validates | minor bump (a new flag and asset) above `origin/main`, fragment `Highlights` set to `false` |

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
- Drawing, theme, style confinement, hostile fences, integrity failure, offline fallback, syntax-error fence: manual QA in a real browser over the sample fixture, with `design-review` and `experience-reviewer` passes.

## Acceptance Criteria

### Arguments and default page

- [ ] `render_html.py <dir>` and `render_html.py <dir> --diagrams` each exit 0 on a valid report.
- [ ] Zero arguments, more than two arguments, or a second argument other than `--diagrams` exit 2 with the usage token `render_html: usage: render_html.py <effort-dir> [--diagrams]`; a first argument of `--diagrams` is treated as a path and refused as today.
- [ ] Without `--diagrams`, the output has no `script` element and no `src` attribute.
- [ ] Without `--diagrams`, the policy is `default-src 'none'; style-src 'sha256-` plus the hash of the page's own `<style>` text, then `'; base-uri 'none'; form-action 'none'`.
- [ ] Without `--diagrams`, `diagrams.js` is not read, and a missing `diagrams.js` does not change the output or the exit code.

### Diagrams page markup

- [ ] With `--diagrams`, the last two children of `body`, after `main`, are two `script` elements in this order: first external with `src` equal to the pinned URL, `integrity` equal to the pinned `sha384-` value, `crossorigin` equal to `anonymous`, and `referrerpolicy` equal to `no-referrer`; then inline holding the text of `report_assets/diagrams.js`.
- [ ] With `--diagrams`, the policy's `script-src` holds exactly the `sha256-` hash of the inline script text and the pinned URL, and no other source.
- [ ] With `--diagrams`, the policy's other directives equal the default page's, so `style-src` stays one `sha256-` hash.
- [ ] With `--diagrams`, a `div` with class `note notice-diagrams` follows the untrusted-content notice and reads: `Diagrams are drawn by Mermaid <version>, loaded from cdn.jsdelivr.net. Opening this report sends your IP address, the time, and your browser details to that host; no report text and no page address is sent.`
- [ ] The closed element list admits `script`, and the closed attribute list admits `src`, `integrity`, `crossorigin`, and `referrerpolicy` on a `script`, only in `--diagrams` output.
- [ ] The pinned version equals the `mermaid` version in `docs-site/package.json`, and the pinned URL is `https://cdn.jsdelivr.net/npm/mermaid@<version>/dist/mermaid.min.js`, each a single constant in `render_html.py`, and a roster check confirms both.
- [ ] The pinned `sha384-` value is a single constant in `render_html.py` equal to the value in the ADR, confirmed by a roster check.

### Eligibility

- [ ] With `--diagrams`, a Mermaid fence is not drawn when its first non-blank line, after trimming whitespace, is `---`.
- [ ] With `--diagrams`, a Mermaid fence is not drawn when any line contains `%%{`.
- [ ] With `--diagrams`, a Mermaid fence is not drawn when the first word of any line, after trimming whitespace and ignoring case, is `click`, `link`, `links`, or `callback`.
- [ ] With `--diagrams`, a Mermaid fence is not drawn when its text exceeds 50,000 UTF-8 bytes, and no more than 20 fences per page are drawn, the first 20 in document order.
- [ ] With `--diagrams`, a fence that passes all rules has class `diagram-drawn` on its `div.diagram` and the label `Diagram (source below)`.
- [ ] With `--diagrams`, a fence refused by a rule has no `diagram-drawn` class and the label `Diagram source (not drawn: unsafe)`, or `Diagram source (not drawn: limit)` for the twenty-first and later fences.
- [ ] Without `--diagrams`, every Mermaid fence keeps the label `Diagram source (not rendered)`.
- [ ] For the fixture and for hostile fences holding CRLF, NUL, HTML entities, and Mermaid entity codes, the string the eligibility rules read equals the unescaped text of the emitted `code` element.

### Script text rules (`diagrams.js`)

- [ ] `diagrams.js` calls `mermaid.initialize` with `securityLevel` `strict`, `startOnLoad` `false`, `suppressErrorRendering` `true`, `maxTextSize` `50000`, and `maxEdges` `500`.
- [ ] `diagrams.js` chooses the theme `dark` when `prefers-color-scheme: dark` matches and `neutral` otherwise.
- [ ] `diagrams.js` draws only `.diagram-drawn` blocks and passes `mermaid.render` exactly the `textContent` of the block's `code` element.
- [ ] `diagrams.js` holds none of `innerHTML`, `insertAdjacentHTML`, `outerHTML`, `eval`, `Function(`, `document.write`.
- [ ] `diagrams.js` removes every `style` attribute from the parsed SVG, and adds a drawn SVG's stylesheet to the page only when every rule is a style rule whose selectors all begin with that SVG's `#id`; otherwise it leaves the block as source.
- [ ] On a render error, a missing `mermaid` global, or no constructable-stylesheet support, `diagrams.js` leaves the source block, adds a visible note `Diagram not drawn` to the block, and removes any element Mermaid left in the document.

### Asset and caps

- [ ] With `--diagrams`, a missing, over-64-KiB, non-UTF-8, symlinked, or non-regular `diagrams.js` is refused with exit 3 and a distinct fixed token each, none naming a stylesheet.
- [ ] With `--diagrams`, a `diagrams.js` holding `</script`, `<!--`, or a carriage return, matched ignoring case, is refused with exit 3 and a fixed token.
- [ ] The 2 MiB source cap, the 16 MiB page cap, and the asset-read rules of the parent specs hold with the flag.
- [ ] Fence text and every attribute value stay escaped in both modes.

### Real browser (ledger)

- [ ] Opened with network access to `cdn.jsdelivr.net`, each `div.diagram-drawn` shows a drawn SVG above its source block in light and in dark, with node text legible, recorded with screenshots.
- [ ] A fence using `classDef`, `style`, and `linkStyle` aimed at the notices, the banner, and the state mark leaves all three unchanged, recorded with screenshots.
- [ ] A fence label carrying a script payload that would set a visible sentinel leaves the sentinel unset, recorded in the ledger.
- [ ] A fence with a syntax error stays as source with the note `Diagram not drawn` and no other graphic, recorded with a screenshot.
- [ ] With the `integrity` value altered, no diagram is drawn and each drawn-eligible block shows the note `Diagram not drawn`, recorded with a screenshot.
- [ ] With the network blocked, the report is fully readable and each drawn-eligible block shows the note `Diagram not drawn`, recorded with a screenshot.
- [ ] The ledger records that the tarball's integrity equals the `docs-site` lockfile value and that its `dist/mermaid.min.js` SHA-384 equals the constant and the bytes served by the CDN.
- [ ] A `design-review` and an `experience-reviewer` pass over the light and dark screenshots of the drawn page leave no Major or Blocker after adjudication, recorded in the ledger.

### Docs and release

- [ ] The ADR exists before the renderer change merges, and states the decision, version, URL, hash, that SRI binds the bytes, the opt-in rule, the policy, that `docs-site`'s audit covers the pinned version, and the revisit triggers: a published advisory against the pinned version, or a change to the CDN host.
- [ ] Each row of the Amended parent rules table carries the exception text and cites this spec, confirmed by a roster check.
- [ ] `references/html-report.md` names `--diagrams`, the host, the offline default, the new usage token, and the new exit 3 reasons.
- [ ] `SKILL.md`, the reference guide, and the how-to guide each name `--diagrams` and the host, and state that drawn reports contact the host and should not be shared with readers who expect the offline default.
- [ ] `SKILL.md` states that `--diagrams` is passed only when the user asks for drawn diagrams.
- [ ] `evals/evals.json` holds one case that asks for drawn diagrams and asserts the flag is used, and one plain HTML request that asserts the flag is absent.
- [ ] The decision note states the chosen option and that drawing is opt-in.
- [ ] `pack.toml` and `plugin.json` carry matching versions, a minor bump above `origin/main`, and a changelog fragment validates.

## Terminal Intent

`code` — add the flag, the script asset, the eligibility rules, the policy change, and the docs, ADR, and release surface.

## Follow-ons

- eugenelim: vendoring or a local `--mermaid-js` file, if offline drawing is wanted later.

## Assumptions

- Product: drawing is opt-in, not the default — whether the default should flip once the owner has seen the page (settled by: the owner).
- Technical: Mermaid 12.2.0 draws the fixture's flowchart and sequence diagram under the strict policy — settled by browser QA.
- Technical: a browser without constructable stylesheets shows source blocks only and the note — whether that is acceptable (settled by: the owner).

## Changelog

<!-- Approvals only. -->
