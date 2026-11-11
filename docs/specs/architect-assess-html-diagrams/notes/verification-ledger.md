# Verification ledger: architect-assess HTML report diagrams

Rendered from `testdata/html-style-sample.md` (a flowchart and a sequence diagram) plus hostile fences, with `render_html.py --diagrams`, opened in Microsoft Edge headless over the DevTools protocol, light and dark emulated through `prefers-color-scheme`. Screenshots were read during the run and are not committed; each row states what was observed. The pinned build is Mermaid 12.2.0 from `cdn.jsdelivr.net`. Each hostile-input row ran twice against the final script: once as a real fence or stub, once with the network blocked as the baseline for comparing page elements.

## Real-browser criteria

| Criterion | Observation | Result |
| --- | --- | --- |
| Drawn SVG above its source, light and dark | Both fixture diagrams draw in both themes (2 of 2 blocks, no left-over elements, no page-level horizontal scroll). Node text reads clearly: dark text on light grey in light mode, light text on near-black in dark mode, because the drawing is the light theme inverted by `report.css`. | Met |
| Drawn `classDef`, `style`, `linkStyle` with notice-named classes | A fence using `classDef notice-untrusted`, `classDef hot`, `style A`, and `linkStyle 0` drew in both themes. The untrusted-content notice, banner, privacy note and state mark kept the same size, display, visibility and opacity as the offline baseline and each stayed on top at its centre point. | Met |
| Script payload sentinel | A node label holding `<img onerror=window.__pwn=1>` and another holding a `<script>` element drew without running either: `window.__pwn` stayed undefined and the page title unchanged. | Met |
| Hostile stub output | Through a stub `mermaid`, an SVG holding `a`, `image`, `foreignObject`, `href`, `onclick`, or an external `url()`, and sheets holding `@import`, a nested rule, root `position`/`inset`/`z-index`, an unscoped `.notice-untrusted`, a sibling `~`, a `+`, a comma hidden in a quoted string, a comma hidden behind an escape, a keyframe named `view-in`, or `@font-face` each left the block as source with the label `Diagram source (not drawn)`, zero such elements in the page, and the source block visible. | Met |
| Style move and id rewrite | A drawn stub SVG held 0 `style` elements and 0 `style` attributes in the page (styles moved into the checked sheet); an id `actor1` became `mmd_d1-actor1` and its `url(#…)` reference was rewritten with it. | Met |
| Syntax-error fence | `flowchart LR / A[ --> B` shows `Diagram source (not drawn)`, no extra SVG, no left-over element. | Met |
| Integrity value altered | No diagram drawn; every drawn-eligible block read `Diagram source (not drawn)`; no uncaught exception. | Met |
| Network blocked | Report fully readable; every drawn-eligible block read `Diagram source (not drawn)`; the privacy note shows. | Met |
| `CSSStyleSheet` removed | Every drawn-eligible block read `Diagram source (not drawn)`. | Met |
| Heading named `Mermaid`, CDN blocked | `window.mermaid` is the heading element; blocks read `Diagram source (not drawn)`; zero uncaught script errors. | Met |
| Hash provenance | The npm tarball's integrity equals the `docs-site` lockfile value; its `dist/mermaid.min.js` SHA-384 equals `MERMAID_SRI`; the bytes the CDN serves equal the tarball's file. | Met |
| Print | With print media emulated in a dark scheme, the drawing's filter is `none` and nothing animates; the drawing fits a 720 px page. | Met |
| Reviews | `experience-reviewer` over the light, dark, 320 px and offline screenshots: no Blocker or Major. `design-review` authoring-time self-review of the same: no Major (same-session, so not independent). | Met |

## Review results and dispositions

- **Experience review, Minors:** cylinder labels sit off-centre (a Mermaid 12.2.0 placement bug; an attempt to correct the anchor broke every rectangle label and was reverted; recorded as an open assumption); the drawing was too small at 320 px (fixed: minimum width with sideways scroll); every region had the same name (fixed: ordinal plus section name); the failure label gives no cause (open: the spec fixes the label wording); no loading state (fixed: the server label reads `not drawn yet` until the script succeeds).
- **Frontend review, Majors, all fixed:** edge animations ignored reduced motion (drawings never animate); the dark theme printed on paper (always the light theme, inverted on a dark screen only); the label claimed a drawing before one existed (server label now `not drawn yet`); the cylinder labels (see above). Minors fixed: region ordinal and name, tab stop only while the drawing scrolls, `defer` on the Mermaid script, no page break inside a drawing in print.
- **Security review:** fixed the selector splitter (quotes and escapes), the id boundary, keyframe names, the property ban (all `margin*`, `inset*`, `offset*`), and `href` matching by local name. Fixed the privacy note: the integrity check needs a cross-origin request, so a served report also sends its web address to the host; the note, docs, and ADR now say so.
- **Quality review:** the confinement text greps are replaced by a node run of the shipped script's pure checks against a hostile table (every mutant tried was caught); near-miss fixtures, exact-once `initialize`, element-list check over hostile input, ADR date, and both guides naming the flag are now pinned.
- **Adversarial review:** the how-to guide now names `--diagrams`; the four exit 3 tokens are quoted and pinned; `linkStyle` now draws while node names starting with `link`, `click`, or `callback` are refused by prefix, stated in the spec; the spec was amended to match the behavior (style handling, labels, theme, holder name, `defer`, minimum width).

## Known limits

- Cylinder-shaped nodes render their labels off-centre.
- The failure label does not say why (offline versus a bad diagram).
- A node whose name starts with `link`, `click`, or `callback` makes its fence stay as source.
- Every drawing is the light theme inverted on a dark screen, so Mermaid's colours show inverted in dark mode.
