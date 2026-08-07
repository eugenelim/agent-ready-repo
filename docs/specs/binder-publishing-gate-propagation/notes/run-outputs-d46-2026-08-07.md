# Adopted-mechanism (D46) run outputs — 2026-08-07

Captured verbatim. Reproduce with make_fixture.py + main.html.a11y-shim, the two
fixture-*.md variants, and z6_a11y_probe.py; egress blocked by aborting every
non-file:// request in the driver.

## Ordering isolated to the MutationObserver, 60-edge fence (Z6j)
```
=== AX nodes for graphics ===
   role='image'              name='' desc=''
   role='image'              name='' desc=''
   role='graphics-document'  name='Diagram 3.1 long fence' desc='A sixty-edge chain, long enough to span a parse chunk.'
   role='graphics-document'  name='Diagram 3.2 short fence' desc='Diagram 3.2 short fence'
   role='image'              name='' desc=''
   role='image'              name='' desc=''
=== SVG <title>/<desc> inside the closed shadow root ===
    <title id="chart-title-__mermaid_0">Diagram 3.1 long fence
    <desc id="chart-desc-__mermaid_0">A sixty-edge chain, long enough to span a parse chunk.
    <title id="chart-title-__mermaid_1">Diagram 3.2 short fence
=== diagram rendered? div heights: [6313, 73]
=== remote requests: []
=== page errors: []
```

## The Mermaid-source sink: what escaping does not cover (Z6i)
```
AX names on the SVGs:
    "Diagram 3.1 — Réseau : l'architecture 漢字"
    'Diagram 3.2 with <b>angle</b> brackets'
    'Diagram 3.3 payload'
diagrams rendered (heights): [177, 177, 177]
page errors: []
```

## Escaping round-trips international text exactly (Z6h)
```
getAttribute BEFORE mount: None
AX name AFTER mount : 'Ledger & payments "3.1" — l\'architecture réseau'
```
