# analytical-design vs. interaction-design: pick the right skill

**Use this when:** a task touches data layout, chart selection, or visualization — and you need to decide whether `analytical-design` or `interaction-design` is the right skill.
**Prerequisites:** `experience-design` pack installed.
**Result:** a clear routing decision, so data-encoding and visualization work lands in the right skill and no step is done twice.

> **How-to** — task-oriented. Pick the right skill using the triggers below. For *why* the thread is shaped this way, read [The experience thread](../explanation/the-experience-thread.md).

## The boundary

**`analytical-design`** owns the structural specification for analytical surfaces: the widget hierarchy, the spatial layout grammar, and the role-based view architecture that lets a user move from a status signal to a diagnostic to a corrective action without losing their place. It is dashboard IA. It does not design individual chart encodings or component interactions.

**`interaction-design`** owns the behavioral layer for a screen or component: how it responds to actions, validates input, transitions between states, and guides users through gesture and cognitive fit. When a chart or widget has interactive behavior — drill-through, hover tooltips, filter state changes, animated data updates — that behavior belongs to `interaction-design`.

The two skills are complementary. Run `analytical-design` to set the structural frame (widget hierarchy, zone layout, role-based views, per-widget state set). Then run `interaction-design` for the interactive components that inhabit that frame.

## Decision triggers

| Stimulus | Skill |
|---|---|
| "What chart type should go here?" | `analytical-design` |
| "How should the KPI row be organized?" | `analytical-design` |
| "What goes above vs. below the fold on this dashboard?" | `analytical-design` |
| "What views do we need for the executive vs. the on-call engineer?" | `analytical-design` |
| "What should a widget show when it has no data?" | `analytical-design` (per-widget state spec) |
| "How does a drill-through click behave step by step?" | `interaction-design` |
| "What happens when the user hovers over a data point?" | `interaction-design` |
| "Design the filter panel — how does it open, apply, and reset?" | `interaction-design` |
| "How does form validation work on a report-configuration form?" | `interaction-design` |
| "What is the feedback timing when a chart is refreshing?" | `interaction-design` |
| "Design the animated transition when data updates." | `interaction-design` |

## The split-ownership case

A chart widget on a dashboard spans both skills:

- **`analytical-design`** owns where the widget sits in the hierarchy, which business question it answers, and its required state set (loading / empty / error / populated / stale).
- **`interaction-design`** owns what happens *inside* the widget once it is placed: the state machine for hover, click, drill-through, and tooltip; the feedback timing for data refresh; the animated transition between data states (if any).

Run `analytical-design` first. Placement and state-set decisions are structural constraints; the behavioral decisions build on top of them.

## Common mistakes

**Using `interaction-design` to choose chart types.** Chart type selection follows from the domain model and the business question the widget answers — it is an `analytical-design` decision, not a component behavioral one. Routing chart-type work to `interaction-design` produces a behavioral spec with no structural grounding.

**Using `analytical-design` for form validation on a filter panel.** If the task is about how a filter input validates, what happens on a submit error, or the tab order through a configuration form, that is `interaction-design` territory. `analytical-design` defines the filter panel's placement and its business-question role; `interaction-design` defines how interacting with the panel feels.

**Conflating "widget states" with "widget behavior."** `analytical-design` names which states a widget must handle (the quality floor: loading, empty, error, populated, stale). `interaction-design` designs the transitions and feedback that animate those states. One names the set; the other models the machine.
