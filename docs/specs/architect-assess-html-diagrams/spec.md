# Spec: architect-assess HTML report draws diagrams on request

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs/specs/architect-assess-html-report/spec.md`](../architect-assess-html-report/spec.md) and [`docs/specs/architect-assess-html-report-style/spec.md`](../architect-assess-html-report-style/spec.md) — escaped values, closed element and attribute lists, one `<style>` named by a hash, confined I/O, fixed exit tokens. This spec relaxes only the "no script, no network" rule, and only when the reader asks for diagrams. The exact-version CDN load with an integrity hash follows [`docs/specs/cdn-sri-mermaid/spec.md`](../cdn-sri-mermaid/spec.md). The decision record is [`docs/specs/architect-assess-html-report/notes/diagram-rendering-decision.md`](../architect-assess-html-report/notes/diagram-rendering-decision.md).
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

A maintainer who runs the renderer with `--diagrams` opens a report whose Mermaid diagrams are drawn in place, in the page's light or dark theme, with the source still shown beneath each drawing. Without the flag nothing changes: the page runs no script and makes no network request. With the flag, the page loads one pinned Mermaid build from one named host, checked by an integrity hash, runs one small script of this pack's own, and tells the reader that opening the report contacts that host. A diagram that is unsafe to draw, or that fails to draw, stays as source with a visible note.

Drawing is opt-in because a report is built from untrusted repository text, and each opened report would otherwise tell the CDN host who opened it and when.

## What Changes

- The renderer accepts an optional `--diagrams` flag after the effort directory — `scripts/render_html.py`.
- A script asset draws the diagrams, loaded through the confinement helper and named in the content-security policy by hash — `scripts/report_assets/diagrams.js`.
- Eligible Mermaid blocks get a drawing marker; unsafe ones do not — `render_html.py`.
- Heat glyphs and the `high` fill change, so the three levels differ in shape and neighbouring `high` cells keep a divider — `report_assets/report.css`.
- The decision, the pinned dependency, the docs, the eval, and the release surface — an ADR, `references/html-report.md`, `SKILL.md`, `evals/evals.json`, `pack.toml`, `plugin.json`, a changelog fragment.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | A third-party script now runs in a generated page, opt-in, pinned and hashed | `docs/adr/` (new record) | eugenelim | the ADR | names the version, host, hash, opt-in rule, CSP, and the revisit trigger |
| Dependency record | A pinned runtime dependency loaded by a shipped page | the same ADR | eugenelim | the ADR | names `mermaid` at the pinned version and the audit path |
| Interface compatibility | The parent specs say "no script, no network" | `docs/specs/architect-assess-html-report/spec.md`, `docs/specs/architect-assess-html-report-style/spec.md` | eugenelim | diff | each affected criterion cites this spec as the owner of the opt-in exception |
| Current product truth | The decision note is the open question this answers | `docs/specs/architect-assess-html-report/notes/diagram-rendering-decision.md` | eugenelim | diff | the note states the chosen option |
| User-facing promise | The mode gains a flag and a privacy note | `references/html-report.md`, `SKILL.md`, `guides/architect/reference/architecture-assessment.md` | eugenelim | grep | all three name `--diagrams`, the host, and the offline default |
| Token record | The heat glyphs and high-cell divider change | `docs/design/tokens/skill-html-views.md` | eugenelim | diff | the heat table shows the new glyphs and divider |
| Verification record | Real-browser drawing, CSP blocking, and offline fallback are manual | `docs/specs/architect-assess-html-diagrams/notes/verification-ledger.md` | eugenelim | the ledger | holds the observations and review results |
| Release history | A pack change ships by version bump | `pack.toml`, `plugin.json`, changelog fragment | eugenelim | parity test, fragment validates | bump above `origin/main`, `Highlights` decided |

## Agent Rules

### Always do

- Treat every byte of `assessment.md` as untrusted. Drawing never relaxes escaping, the closed lists, or the size caps.
- Set Mermaid's `securityLevel` to `strict` in pack code only; no report text reaches the Mermaid configuration.
- Keep the page without a script or a network reference when `--diagrams` is absent.

### Ask first

- Any script source, CSP source, element, or attribute beyond those the acceptance criteria name.
- Changing the pinned version or hash; a bump is its own change with its own check of the fetched file.

### Never do

- Allow `unsafe-inline`, `unsafe-eval`, a wildcard, or a host-only source in `script-src`.
- Draw a fence that holds a Mermaid directive, a frontmatter `config:` block, or a `click` callback.
- Load any other third-party file, font, image, or style.

## Testing Strategy

- Flag parsing, markup, eligibility filter, CSP text, script-tag attributes, asset loading and refusals, notice, size caps, heat rules: TDD, because each is an input-to-output rule over the rendered HTML or a text rule over a file.
- Parity of the version, URL, and hash between the renderer and the ADR: goal-based roster check outside the pack tree.
- Drawing, theme, hostile fence blocked, integrity mismatch blocked, offline fallback, heat look: manual QA in a real browser over the sample fixture, with `design-review` and `experience-reviewer` passes.

## Acceptance Criteria

### Default page

- [ ] Run without `--diagrams`, the renderer's output contains no `<script`, no `http://` or `https://` text outside content links the author wrote, and a content-security policy exactly as before.
- [ ] Run with one argument, the usage token and exit code 2 are unchanged for any argument count other than one or two, and a second argument other than `--diagrams` exits 2 with the usage token.

### Diagrams page

- [ ] Run with `--diagrams`, the output holds exactly two `<script>` elements, in this order: one external with `src` equal to `https://cdn.jsdelivr.net/npm/mermaid@11.16.0/dist/mermaid.min.js`, `integrity` equal to the pinned `sha384-` value, and `crossorigin` equal to `anonymous`; then one inline holding the bytes of `report_assets/diagrams.js`.
- [ ] With `--diagrams`, the policy's `script-src` lists exactly the `sha256-` hash of the inline script bytes and the exact external URL, and holds no other source; every other directive is as before.
- [ ] With `--diagrams`, the policy still has `default-src 'none'` and a `style-src` of one `sha256-` hash only.
- [ ] With `--diagrams`, a note after the untrusted-content notice states that diagrams are drawn by Mermaid 11.16.0 loaded from `cdn.jsdelivr.net` and that opening the report contacts that host.
- [ ] With `--diagrams`, each Mermaid fence of at most 65,536 bytes that holds no `%%{`, no frontmatter `config:` key, and no line matching `click … call|callback|href` gets the class `diagram-drawn` on its `div.diagram`; a fence that fails any test does not, and its label reads `Diagram source (not drawn: unsafe)`.
- [ ] The pinned version, URL, and hash are single constants in `render_html.py`, and a roster check confirms they equal the values recorded in the ADR.

### Script behavior (real browser)

- [ ] Opened over the network in a real browser, each `div.diagram-drawn` shows a drawn SVG above its source block, in light and in dark, with node text legible, recorded with screenshots in the verification ledger.
- [ ] `diagrams.js` calls `mermaid.initialize` with `securityLevel` `strict`, `startOnLoad` `false`, and a theme of `dark` when `prefers-color-scheme: dark` matches and `neutral` otherwise, and draws only `.diagram-drawn` blocks.
- [ ] `diagrams.js` moves each drawn SVG's `<style>` text into a constructable stylesheet before insertion, so the page's `style-src` stays one hash, recorded as styled output in the verification ledger.
- [ ] A planted `<script>` or `onerror` inside a fence label does not execute, recorded in the ledger with the console CSP report.
- [ ] With the file's integrity attribute altered, the script does not run and every diagram stays as source, recorded in the ledger.
- [ ] With the network blocked, the report is fully readable, every diagram stays as source, and each drawn-eligible block shows the visible note `Diagram not drawn`, recorded in the ledger.

### Asset and caps

- [ ] `diagrams.js` loads through the confinement helper with a 64 KiB cap, and the renderer refuses a missing, oversize, symlinked, or non-regular copy with a fixed token and exit 3.
- [ ] The renderer refuses a `diagrams.js` that holds `</script` or `<!--`.
- [ ] The page-size caps and the asset-read rules of the parent specs still hold with the flag.

### Heat glyphs and divider

- [ ] `report.css` gives `heat-low`, `heat-medium`, `heat-high` the level glyphs ◔, ◑, ◕ (alternative text empty) and `heat-unknown` the glyph `?`, and none appears among the evidence glyphs or the family's eight state glyphs.
- [ ] `report.css` gives `heat-medium` and `heat-high` a `border-bottom-color` of `var(--c-bg)` and gives no heat class any other `border` or `outline` property.

### Docs and release

- [ ] The ADR exists, states the decision, the pinned version, host, and hash, the opt-in rule, the CSP, the audit path, and a revisit trigger, and is cited by the parent specs' affected criteria.
- [ ] `references/html-report.md`, `SKILL.md`, and the guide name `--diagrams`, the host, and the offline default.
- [ ] The decision note states the chosen option and that drawing is opt-in.
- [ ] The token file's heat table shows the new glyphs and the divider.
- [ ] `pack.toml` and `plugin.json` carry matching versions above `origin/main`, a changelog fragment validates, and `evals/evals.json` holds a case that runs the flag.

## Terminal Intent

`code` — add the flag, the script asset, the eligibility filter, the CSP change, the heat tweaks, and the docs and release surface.

## Follow-ons

- eugenelim: vendoring or a local `--mermaid-js` file, if offline drawing is wanted later.

## Assumptions

- Technical: the CDN `mermaid@11.16.0` build at the pinned hash still draws the fixture's flowchart and sequence diagram under the strict policy — whether a later minor version still works (settled by: the owner, when the pin is bumped).
- Technical: moving Mermaid's `<style>` into a constructable stylesheet keeps `style-src` at one hash because stylesheet objects are not governed by `style-src` — whether every supported browser agrees (settled by: browser QA; a browser without constructable stylesheets shows the source only).
- Product: drawing is opt-in, not the default — whether the default should flip once the owner has seen the page (settled by: the owner).
- Technical: Mermaid's own inline `style` attributes on SVG elements are removed by Mermaid's sanitizer or ignored under the policy — whether any visual loss results (settled by: browser QA).

## Changelog

<!-- Approvals only. -->
