---
name: analytical-design
description: "Use when designing an analytical surface — a dashboard, a reporting view, a monitoring screen, or any surface whose primary purpose is to help a user understand a data set and act on it. Triggers on 'design the dashboard', 'structure the reporting view', 'what goes on the analytics screen', 'KPI layout', 'design a monitoring view'. Produces domain-model-first IA and widget hierarchy specifications. Scope boundary — individual chart encoding design is out of scope (use interaction-design for component state machines); this skill handles dashboard IA only. Do NOT use for marketing surfaces (use conversion-design) or workspace productivity surfaces (use workspace-design). Surface genre: analytical. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register."
---

# Skill: analytical-design

Converts business questions and the domain model into a **structural specification for an analytical surface** — the widget hierarchy, the spatial layout grammar, and the role-based view architecture that lets a user move from a status signal to a diagnostic to a corrective action without losing their place. This skill is dashboard IA; it does not design individual chart encodings (that is `interaction-design`'s widget state machine) and does not derive tokens or color (that is `design-system` and `creative-direction`).

## When to invoke

Confirm all three before specifying:

1. **The surface goal is comprehension and action** — the primary measure is whether a user can answer a specific business question and take a next action from the screen. If the primary goal is conversion, use `conversion-design`; if it is task management, use `workspace-design`.
2. **The domain model can be articulated** — objects, attributes, relationships, and actions define what data exists and what a user can do with it. Without a domain model, widget placement is decoration.
3. **Business questions are named** — "give me insights" is not a design brief. The 3–5 explicit questions this screen must answer are the design constraints.

## Domain-model-first

Before placing any widget, name the domain model. This is not a data schema — it is the conceptual model a user already carries:

- **Objects:** what are the entities the user thinks about? (Orders, customers, pipeline stages, deployments, incidents)
- **Attributes:** for each object, what properties matter for the business questions this screen answers?
- **Relationships:** how do objects relate to each other in a way that creates analytical questions? (A customer has many orders; an incident affects multiple services)
- **Actions:** what can a user DO with data on this screen? (Drill into an order, assign an incident, filter by date range, export a report)

Widget placement follows from the domain model. A KPI widget placed on a screen because "it looks good" will fight the user's mental model.

## Business-question anchoring

Name exactly 3–5 questions this screen must answer. These are the design constraints; every widget and layout decision should be traceable to at least one of them:

**Question format:** "[Role] needs to know [fact] so they can [action]."

Examples:
- "The on-call engineer needs to know which services are currently degraded so they can prioritize which runbook to open."
- "The VP of Sales needs to know whether the pipeline is trending toward the quarterly target so they can decide whether to intervene."
- "The support manager needs to know where ticket volume is highest by category this week so they can decide where to add capacity."

A widget that does not answer any of the 3–5 named questions is a candidate for removal.

## 3-tier widget hierarchy

Organize widgets into three tiers based on their role in answering the business questions:

**Tier 1 — Primary KPIs (≤9 widgets)**
The state signals a user checks first to know if anything requires attention. Each answers a binary: "Is this good or not?" Limit to 9 (Miller's Law — cognitive chunking boundary for at-a-glance processing). More than 9 primary KPIs means the screen has no primary signals; everything is equally important, which means nothing is.

**Tier 2 — Secondary diagnostics**
The widgets a user consults after a Tier 1 signal raises a question. These answer "why?" or "where?" — trend lines, breakdowns, distributions. Positioned after Tier 1 in the visual hierarchy.

**Tier 3 — Tertiary details**
The data tables, raw logs, or drill-down panels a user accesses after Tier 2 narrows the question. These are not on the default view; they appear on demand (expandable section, detail panel, drill-down navigation).

## Shneiderman's mantra — applied to layout

Overview first, zoom and filter, then details on demand. Apply at the layout level:

- The **overview** (Tier 1 KPIs) is above the fold without scrolling.
- **Zoom and filter** controls (date range, role filter, service selector) are adjacent to the data they filter — not buried in a sidebar divorced from the widgets.
- **Details on demand** (Tier 3) are accessible from any widget via a consistent affordance (click to expand, click to drill through).

## Role-based views

If the same data serves multiple roles with different business questions, design role-based views rather than a single view that tries to serve everyone:

- Name the roles and their questions before designing any view.
- Define which Tier 1 KPIs differ by role; shared KPIs appear in a shared overview; role-specific KPIs appear in role-specific sections or views.
- Design a view-switching affordance that is visible and immediate — a role selector in a tab or header, not a settings page.

A single screen designed to serve all roles equally serves none of them well.

## Spatial layout grammar

Assign spatial zones to function before placing widgets:

| Zone | Function |
|------|---------|
| **Top** | State signals — the Tier 1 KPI row; status indicators; time-range selector |
| **Left** | Worklist — the enumeration of objects requiring attention (incident list, task queue, open tickets) |
| **Centre** | Primary diagnostic — the Tier 2 widget that answers "why?" for the selected item from the left |
| **Right** | Context and filter — date range, filter controls, metadata about the selected object |

This grammar is not a requirement — it is a starting point. Override it only when the domain model's object relationships make a different layout more legible. Document the override and the reason.

## Per-widget state handling

Each widget must specify its state set before it is designed:

| State | What to show |
|-------|-------------|
| **Loading** | A skeleton that matches the loaded widget's layout — not a spinner that collapses the zone |
| **Empty** | Why there is no data (no data for this date range? no permissions? no activity?) + the next action |
| **Error** | The error in user terms + a recovery action (retry, check filter, contact support) |
| **Populated** | The normal data state — the "happy path" |
| **Stale** | When data is cached and the freshness timestamp matters, show the staleness signal adjacent to the data |

A widget designed only in its "populated" state will surprise users when it loads, fails, or empties.

## Canonical aesthetic reference tier (study subjects, not prescriptive tools)

For grounding creative-direction on an analytical surface, study how these products handle data density and information hierarchy: Linear (high-density status layout), Retool (flexible widget hierarchy clarity), Metabase (progressive disclosure in data exploration). Internalize the structural philosophy — signal vs. noise hierarchy, spatial grammar, progressive disclosure — not the surface treatment.

## Anti-patterns to refuse

- **Widget-first design.** Choosing charts before naming the business questions inverts the design process. The chart type is a downstream decision; the question it answers is the upstream constraint.
- **More than 9 Tier 1 KPIs.** Every signal at the same visual weight means no signal. Limit or collapse into a status row.
- **Filter controls separated from data.** A date range filter in a sidebar while the charts it affects are in the center creates a spatial mismatch that obscures the relationship. Filters live adjacent to the data they filter.
- **Missing empty and error states for widgets.** A dashboard widget with no empty state looks broken when it loads with no data. Specify all states.
- **Role mixing without view separation.** A dashboard designed for both an executive overview and operational triage will satisfy neither. Separate by role or clearly layer the hierarchy.
