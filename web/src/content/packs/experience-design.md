---
name: Experience Design
scope: user
tagline: "The design/UX seat for product teams."
skills:
  - journey-mapping
  - user-flow
  - service-blueprint
  - process-mapping
  - creative-direction
  - design-token-taxonomy
  - design-system-foundations
  - information-architecture
  - interaction-design
  - design-review
  - content-design
  - copy-direction
  - tone-of-voice
  - design-principles
  - conversion-design
  - documentation-design
  - analytical-design
  - marketplace-design
  - informational-design
  - workspace-design
  - experience-status
installCommand: "agentbundle install --pack experience-design --scope user"
docsUrl: /docs/guides/experience-design/
journeyUrl: /journeys/experience-design/
---

Experience Design installs the full design thread from outcome to realization — 21 skills covering journey mapping, screen flow derivation, service blueprinting, surface-genre design (marketing, documentation, analytical, marketplace, informational, workspace), design principles, content design, copy direction, design token taxonomy, design system foundations, and continuous review. Connective skills walk journey-mapping → user-flow → service-blueprint and the inside-out sibling (process-mapping). Genre skills handle each surface type: conversion-design for marketing surfaces, documentation-design for docs sites, analytical-design for dashboards, and more. Craft skills design each screen (creative-direction, design-token-taxonomy, design-system-foundations, information-architecture, interaction-design) and review it (design-review, design-principles), all held to one shared quality floor — handle-all-states, WCAG 2.2 AA, reduced-motion. A forked-context `experience-reviewer` gives every design an independent review.

**Design system chain — near-miss guard:** `design-token-taxonomy` names the taxonomy — semantic roles, scale ratios, and the accessibility floor. `design-system-foundations` applies it as a working foundation — semantic color roles, typography, spacing, radius, focus, status tokens, responsive breakpoints, and core component tokens. Run them in sequence. Near-miss: don't invoke either in isolation — `design-token-taxonomy` without `design-system-foundations` leaves no working foundation to build on; `design-system-foundations` without a prior `design-token-taxonomy` run has no principled basis. Don't confuse `design-token-taxonomy` (derives the taxonomy) with `design-system-foundations` (applies it).

**Copy direction — near-miss guard:** `copy-direction` fires on marketing and acquisition surfaces — landing pages, hero copy, above-fold narrative, and positioned headlines. It is not for general brand tone work; use `tone-of-voice` for that. Near-miss: don't invoke `copy-direction` for general brand voice (use `tone-of-voice`) or for product UI strings such as error messages, labels, and empty states (use `ux-writing` in the product-engineering pack).
