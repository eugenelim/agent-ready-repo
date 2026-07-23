# Spec: cdn-sri-mermaid

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim

**Mode:** light (no risk trigger fired — additive attribute change, no logic change)

## Objective

Pin both mermaid CDN loads in `markdown-to-html` and `render-proof` from the
floating `mermaid@11` specifier to `mermaid@11.16.0` with an SRI `integrity=`
hash and `crossorigin="anonymous"`. Today a CDN compromise or MITM can inject
arbitrary JS into any generated page's origin, bypassing DOMPurify entirely.
Bundle: pin `@a2ui/web_core` to `^0.10.5` in render-proof's `package.json`
to match what `@a2ui/react@0.10.2` now explicitly requires (upstream fix for
the dep-chain pinning issue we raised — SSR fallback unchanged, still needed).

## Acceptance Criteria

- [x] AC1: `render.js` mermaidScript tag uses `mermaid@11.16.0` URL, adds
  `integrity="sha384-T/0lMUdJpd2S1ZHtRiofG3htU3xPCrFVeAQ1UUE2TJwlEJSV5NUwn30kP28n238E"`,
  and adds `crossorigin="anonymous"`.
- [x] AC2: `render-proof.js` mermaidRuntime tag uses same pinned URL + same
  integrity + crossorigin.
- [x] AC3: SRI hash matches `mermaid@11.16.0/dist/mermaid.min.js` exactly —
  verified by two independent methods (openssl + Python hashlib), both yielding
  `T/0lMUdJpd2S1ZHtRiofG3htU3xPCrFVeAQ1UUE2TJwlEJSV5NUwn30kP28n238E`.
- [x] AC4: `render-proof/package.json` pins `@a2ui/web_core` to `"^0.10.5"`.
- [x] AC5: `node test/pipeline.test.js` passes in `render-proof/`.

## Tasks

1. Update `render.js` mermaidScript string — pin version + add integrity + crossorigin.
2. Update `render-proof.js` mermaidRuntime string — pin version + add integrity + crossorigin.
3. Update `render-proof/package.json` — bump `@a2ui/web_core` from `^0.10` to `^0.10.5`.
4. Verify: grep rendered output for exact script tag; `node test/pipeline.test.js`.
