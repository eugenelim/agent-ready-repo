---
schema-version: "1.0"
risk-tier: explore     # explore | pilot | production
product-slug: <replace-with-product-slug>
---

<!-- Digital Experience Contract
     Owner map: each section is owned by one discipline. Skills in that pack
     fill their section; skills in other packs may READ all sections.
     Skills must not silently rewrite another discipline's section — mark
     proposed changes with a [provisional — <pack> not installed] label and
     state what specialist work remains.
     Graceful capability detection: if a required skill is not installed,
     perform the smallest safe fallback, label the output provisional, and
     name what specialist work remains.
-->

# Digital Experience Contract: <replace-with-product-slug>

## Strategy [owner: product-strategy]

### Target User and Context
<!-- Required: explore+ -->
<!-- Who the product is for; their situation; what they are trying to accomplish -->

### Diagnosis and Strategic Choices
<!-- Required: explore+ -->
<!-- What is broken or underserved; the choices made and what was ruled out -->

### Adoption Hypothesis
<!-- Required: explore+ -->
<!-- First-success event: the one action that proves first value
     Repeat-value behavior: what brings the user back -->

### Value Loop
<!-- Required: explore+ -->
<!-- How value compounds with each successive use; the reinforcing mechanism -->

### Metric Tree
<!-- Required: pilot+ -->
<!-- The causal chain from user behavior to outcome; north-star metric + leading indicators -->

### Differentiation
<!-- Required: pilot+ -->
<!-- What this product does distinctly; the mechanism of the moat -->

### Assumptions and Kill Criteria
<!-- Required: explore+ -->
<!-- Core bets; what would falsify each; kill threshold per assumption -->

## Product Engineering [owner: product-engineering]

### Opportunity and Bet
<!-- Required: explore+ -->
<!-- The problem being addressed; the bet made; evidence base (lightweight at explore) -->

### Evidence Ladder
<!-- Required: explore+ -->
<!-- Each claim classified: observed | supported | inferred | assumed | unknown -->

### First-Success Operationalization
<!-- Required: explore+ -->
<!-- Concretely what first success looks like end-to-end for one user -->

### Thin Slice
<!-- Required: pilot+ -->
<!-- One user can: begin a real task, reach a meaningful result,
     encounter and recover from one material failure, produce instrumentation -->

### Capabilities
<!-- Required: pilot+ -->
<!-- What the product must do to deliver the thin slice and first success -->

### Rollout and Recovery Plan
<!-- Required: pilot+ -->
<!-- Staged rollout; support plan; rollback trigger; recovery path -->

### Learning Plan
<!-- Required: pilot+ -->
<!-- What signals confirm or refute the bet; review cadence; decision thresholds -->

## Experience Design [owner: experience-design]

### Primary Journey
<!-- Required: explore+ -->
<!-- The end-to-end user journey from first contact to first-success event -->

### Surface Map
<!-- Required: pilot+ -->
<!-- Every surface in the product; surface type per page-archetypes taxonomy -->

### Information Architecture
<!-- Required: pilot+ -->
<!-- Structure, hierarchy, navigation, wayfinding -->

### Content Hierarchy
<!-- Required: pilot+ -->
<!-- What the product must say at each surface; content brief references -->

### Product Objects
<!-- Required: pilot+ -->
<!-- The core objects the user acts on; their identity, relationships, states -->

### Interaction and Attention Model
<!-- Required: production+ -->
<!-- How the user moves through the product; what the product draws attention to -->

### States and Permissions
<!-- Required: pilot+ -->
<!-- All states per quality-floor (18-state set); permission matrix per surface -->

### Responsive Behavior
<!-- Required: production+ -->
<!-- Breakpoint strategy; cross-channel continuity -->

### Design System Reference
<!-- Required: pilot+ -->
<!-- Which token taxonomy and design-system-foundations output this surface uses -->

## Frontend Engineering [owner: core]

### Prototype or Representation
<!-- Required: explore+ -->
<!-- Earliest rendered evidence: wireframe, clickable prototype, or first built surface.
     At explore tier: a static mockup or prototype is sufficient. -->

### Implemented Behavior
<!-- Required: production+ -->
<!-- What the built surface does; how it matches the design contract above -->

### Accessibility Evidence
<!-- Required: pilot+ -->
<!-- Pilot: accessibility requirements stated; known a11y gaps listed.
     Production: complete WCAG 2.2 AA audit; automated + manual results. -->

### Browser Behavior
<!-- Required: production+ -->
<!-- Baseline Widely Available browser matrix; per-browser test results -->

### Performance
<!-- Required: production+ -->
<!-- LCP / INP / CLS at p75 (mobile + desktop separately where field data exists).
     Asset budget: JS, images, fonts, third-party scripts. -->

### Security and Privacy
<!-- Required: production+ -->
<!-- Data handled; privacy controls; security review status -->

### Reliability
<!-- Required: production+ -->
<!-- Error rates; SLOs; monitoring and alerting; recovery path -->

### Instrumentation
<!-- Required: pilot+ -->
<!-- Events tracked; dashboards; how learning-plan signals are measured.
     Production: measurement dashboard confirmed live. -->

### Rendered Evidence
<!-- Required: pilot+ -->
<!-- Screenshot, recording, or live URL of the rendered and working surface.
     Production: must be the deployed, live surface — not a staging snapshot. -->
