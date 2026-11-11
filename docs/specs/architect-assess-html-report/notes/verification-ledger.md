# Verification ledger

## Real-browser QA (acceptance criterion: shaded heat cells, evidence badges, hostile markup as text)

Run on 2026-10-30 against the final renderer (renderer version 1, pack 0.15.24).

- **Browser:** Microsoft Edge 156.0.4314.50, headless (`--headless=new`), loading each page from a `file://` URL. It was driven for a screenshot and a post-load DOM dump. No other browser was exercised.
- **Inputs:** two reports rendered from resolved effort directories. `sample` holds the three orientation subsections with `Sources checked` tables in all four evidence classes, a `not assessed` Physical subsection, a Mermaid fence, a heat map with three rows, and `Checkpoints: accepted-without-pause`. `hostile` is the same report plus a raw `<script>` that sets `document.title`, an `<img onerror>` that sets it, a `<meta http-equiv="refresh">`, a `javascript:` link, a fenced `</script><script>`, and a title of `<b>Hostile</b> assessment`.

Observed on `sample`:

- The banner `Map and hotspot set not user-confirmed` and the `Unverified: built from repository text and model analysis; not redacted` notice sit above the first section.
- The charter's three lines show on separate lines.
- 15 heat cells (3 rows by the 5 dimension columns) carry a class: 2 `heat-high`, 5 `heat-low`, 6 `heat-medium`, 2 `heat-unknown`. The Confidence and Evidence columns carry none.
- 12 evidence-class cells carry a badge: 3 each of observed, inferred, reported, and unknown, each with a coloured left edge and its word visible.
- The Mermaid fence shows under `Diagram source (not rendered)` as plain source.

Observed on `hostile`:

- The page title is still `<b>Hostile</b> assessment` as visible text, not `PWNED-SCRIPT`, `PWNED-IMG`, or `PWNED-LINK`.
- The post-load DOM holds 0 `<script` elements, 0 `<meta http-equiv="refresh">` elements, and 0 `href="javascript:` attributes. The four `PWNED-` strings appear once each, as visible text.
- The planted markup shows as visible escaped text.

Limits of this check: headless Chromium only; no console output was captured, so a CSP violation message was not read directly (the evidence is that nothing planted ran). Firefox and Safari were not tested. Earlier runs of the same two inputs, before the parser repairs, gave the same results and also led to two fixes: charter lines were running together, and links were hard to read on the dark theme.

## Hostile-input mutation checks

Each behavioral test added during review was run against the renderer as it stood before the repair and failed there (for the fence, scope, link, bidi, output-cap, and memory shapes). The quadratic-time shapes were shown by the old renderer not finishing within the time bound.
