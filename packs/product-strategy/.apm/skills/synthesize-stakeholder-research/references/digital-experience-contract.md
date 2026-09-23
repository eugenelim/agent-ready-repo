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

#### Shared state-coverage map

One row per state in the frontend quality floor's eighteen-state set, so both
disciplines name the same states and owe the same ones at the same depth.

- **Screen-brief line** names the line a per-screen brief already carries for
  that state, or `-` where the state is frontend-owned and no brief line names
  it. One brief line resolves to two states.
- **Tier** is the lowest risk tier at which the state is owed, and is
  cumulative: a tier owes its own states and every lower tier's. `conditional`
  means the state is owed at every tier whenever its trigger fires, and at no
  tier otherwise.
- **Fails WCAG 2.2 AA when absent** records whether leaving the state undesigned
  breaches the success criterion named beside it. A state marked `yes` is never
  dropped by a tier: it is assigned to `explore`, or it is conditional and binds
  at every tier its trigger reaches.

| State | Screen-brief line | Tier | Fails WCAG 2.2 AA when absent | Success criterion, or the trigger that binds it |
|---|---|---|---|---|
| loading | `loading` | explore | yes | 4.1.3 Status Messages (AA) - work in flight with no announced status |
| empty | `empty` | explore | no | - |
| error | `error` | explore | yes | 3.3.1 Error Identification (A); 3.3.3 Error Suggestion (AA) |
| success | `success/default` | explore | yes | 4.1.3 Status Messages (AA) - completion with no announced status |
| content | `success/default` | explore | no | - |
| partial | `partial` | explore | no | - |
| disabled | `disabled` | explore | yes | 4.1.2 Name, Role, Value (A) - an unavailable control whose state is not programmatically determinable |
| keyboard-only | - | explore | yes | 2.1.1 Keyboard (A); 2.4.3 Focus Order (A); 2.4.7 Focus Visible (AA) |
| reduced-motion | - | explore | yes | 2.2.2 Pause, Stop, Hide (A); 2.3.1 Three Flashes or Below Threshold (A) - motion with no calmed alternative |
| high-zoom | - | explore | yes | 1.4.4 Resize Text (AA); 1.4.10 Reflow (AA) |
| first-run | - | pilot | no | - |
| no-results | - | pilot | no | - |
| blocked | - | pilot | no | - |
| large-data-set | - | pilot | no | - |
| offline | - | production | no | - |
| long-content | - | production | no | - |
| permission/denied | `permission/denied (if gated)` | conditional | no | Trigger: the surface is behind authorization. Both the brief line and the quality floor carry it as a gated-screen extension, not a base state. |
| destructive-confirmation | - | conditional | yes | 3.3.4 Error Prevention (Legal, Financial, Data) (AA). Trigger: the primary action is irreversible or destroys data the user controls. |

Explore owns ten states, pilot adds four, production adds two, and two are
conditional. Explore therefore drops six of the sixteen banded states and none
of the eight marked `yes`.

### Responsive Behavior
<!-- Required: production+ -->
<!-- Breakpoint strategy; cross-channel continuity -->

### Design System Reference
<!-- Required: pilot+ -->
<!-- Which token taxonomy and design-system-foundations output this surface uses -->

## Frontend Engineering [owner: frontend-engineering]

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
     Production: WCAG 2.2 AA is the target. Record the automated wcag21aa
     result, the two named manual checks (2.5.8 Target Size (Minimum), AA;
     2.4.13 Focus Appearance, AAA enhancement), and the stated WCAG 2.2 AA
     gap (2.4.11, 2.5.7, 3.2.6, 3.3.7, 3.3.8) rather than claiming a
     complete audit. -->

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
