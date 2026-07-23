---
status: Shipped
type: enhancement
created: 2026-07-16
---

# Mermaid rendering improvements — markdown-to-html + render-proof

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->

Mode: full (security boundary trigger: securityLevel change, CDN injection, user input rendered as HTML)

## Objective

Upgrade Mermaid rendering in both HTML-output converters skills to support all 16
diagram types, add pan/zoom and toolbar UX to `markdown-to-html`, add Mermaid
rendering to `render-proof` (previously zero support), and improve error recovery
across both.

## Acceptance Criteria

- [x] AC1 — `markdown-to-html` CDN bumped from `mermaid@10` to `mermaid@11`
- [x] AC2 — `securityLevel` changed from `'strict'` to `'antiscript'` in both skills
  (allows HTML in node labels; blocks `<script>` execution)
- [x] AC3 — All major Mermaid 11 diagram types configured with `useMaxWidth: true`:
  `flowchart`, `sequence`, `gantt`, `er`, `pie`, `gitGraph`, `quadrantChart`,
  `xyChart`, `block`, `timeline`, `mindmap`, `packet`, `requirement`, `kanban`,
  `class`, `state`, `journey` — authoritative list is the `mermaid.initialize()` call
- [x] AC4 — `markdown-to-html`: diagram card redesign (border-radius 12px, drop shadow,
  no overflow bleed)
- [x] AC5 — `markdown-to-html`: toolbar per diagram with `+`, `-`, `fit`, `copy SVG` buttons
- [x] AC6 — `markdown-to-html`: pan/zoom via drag and scroll wheel (0.25×–4×)
- [x] AC7 — `markdown-to-html`: inline error card on Mermaid parse failure (shows
  parse error text; no silent blank)
- [x] AC8 — `markdown-to-html`: toolbar hidden in `@media print`
- [x] AC9 — `render-proof`: `mermaid` fence blocks wrapped in `.mermaid-wrap` /
  `.mermaid-source` (HTML-escaped via `mdi.utils.escapeHtml`; safe before DOMPurify)
- [x] AC10 — `render-proof`: `hasMermaid` detection on raw markdown; Mermaid CDN +
  init injected into page wrapper only when diagrams are present
- [x] AC11 — `render-proof`: source `<pre>` is the JS-disabled fallback (visible by
  default; hidden by JS after render)
- [x] AC12 — `render-proof`: `@media print` hides `.mermaid-source`, shows SVG canvas
- [x] AC13 — `render-proof`: inline error card on parse failure
- [x] AC14 — Test (p) added to `renderer.test.js` verifying mermaid fence handling
- [x] AC15 — `lint-packs` passes clean (node_modules not committed)

## Testing Strategy

**Client-side JS (toolbar, pan/zoom, error card, copy SVG):** Manual QA mode.
Browser JS cannot be exercised in Node.js without a headless browser. Observed results:
- `make build-check` (lint-packs): passes clean
- `render-proof` test suite (renderer, pipeline, security): all pass (17 tests incl. new (p), (q))
- `markdown-to-html` goal-based smoke: rendered multi-type Mermaid file; confirmed `mermaid@11`
  CDN tag, 17 per-type configs, toolbar CSS, `makePanZoom` function, and `mermaid-error` class
  present in output HTML

**Server-side detection (`hasMermaid`) and fence wrapping:** Automated via test (p) (renderMarkdown)
and test (q) (renderProof CDN injection / suppression) in `renderer.test.js`.

## Boundaries

**In scope:** `markdown-to-html/scripts/render.js`, `markdown-to-html/scripts/template.html`,
`render-proof/scripts/render-proof.js`, `render-proof/test/renderer.test.js`.

**Not in scope:** Offline/bundled Mermaid.js, mobile touch/pinch-zoom, shared
pan-zoom module across skills, SKILL.md prose updates.

## Security notes

- **`securityLevel: 'antiscript'` (deliberate posture)** — `strict` blocks `htmlLabels`
  in flowcharts, which is required for most diagram types to render node labels correctly.
  `antiscript` allows HTML labels while blocking `<script>` execution. The remaining
  XSS surface (attribute-based handlers in HTML labels) is accepted for a trusted-author
  local rendering context — users render their own Markdown files. If the skill is ever
  adapted for untrusted input, revert to `strict` and disable `htmlLabels`.
- Mermaid source is HTML-escaped before insertion (`escapeHtml(text)` in
  `render.js`; `mdi.utils.escapeHtml(code)` in `render-proof.js`). Reading back via
  `textContent` recovers the original unescaped source for Mermaid's parser.
- Mermaid CDN script is added to the page wrapper, not the DOMPurify-sanitized
  markdown body. `render-proof` FORBID_TAGS applies to the markdown body only.
- **Shipped: CDN SRI pinning** — both skills now load `mermaid@11.16.0` from jsDelivr
  with `integrity="sha384-..."` and `crossorigin="anonymous"`. Shipped in `cdn-sri-mermaid`.
