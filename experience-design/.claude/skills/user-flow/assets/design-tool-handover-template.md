# Design-tool handover — the experience → realization seam (optional)

A structured, machine-consumable **instruction set**, keyed to one per-screen
brief, that a **generative design tool** consumes to realize a low- or
high-fidelity design. It is **instructions, never a comp** — it points to the
brief and the grounded aesthetic reference and reprints no values. It names tool
*categories* (a generative-UI / wireframing / design-AI tool), endorses none, and
requires none.

**Detect-and-degrade.** If a design-tool MCP is connected (Figma AI, Claude, v0,
or another generative-UI tool), trigger it with this handover and walk the result.
If none is present, emit this file at
`<parent>/screens/<slug>/<screen-name>.handover.md` for the adopter to paste into
whichever tool they use. No tool is required; none is endorsed.

## Template

```markdown
---
type: design-tool-handover
screen: <screen-name>
flow: <slug>
surface: <responsive-web | iOS | Android | cross-platform>
brief: ../<screen-name>.md
---

# Handover: <screen-name>   ·   <product-slug>   ·   surface: <surface>

## Job
<the single job this screen does — from the brief>

## States to realize
<the states from the brief's state matrix — empty / loading / error / success /
partial / disabled / permission-denied, as applicable to this screen>

## Layout intent
<the structural intent from information-architecture — hierarchy,
regions, reading order — described, not pixel-specified>

## Navigation
<where this screen sits in the shared nav model; entry/exit; persistent chrome>

## Copy pointer
<pointer to the per-state copy from voice-and-microcopy — not restated here>

## Platform surface
<the surface and the platform conventions to honor — point to Apple HIG /
Material 3 / responsive conventions; reprint no values>

## Grounded aesthetic reference
<pointer to the grounded aesthetic direction — the named goals and what grounds
them — so the realized screen reflects the product's taste, not a generic default>

## Components to reuse
<named shared components from the design system — reuse, never reinvent>

## What this handover is NOT
- not a pixel comp, not a values table — instructions keyed to the brief
- not tied to one tool — paste into whichever generative-UI tool you use
```
