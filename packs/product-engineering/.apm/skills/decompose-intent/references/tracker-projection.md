# Tracker projection — one-way, profile-driven

The canonical intent tree is **deeper than any tracker**. Trackers are **lossy,
one-way projections** of it, via a per-mode profile that maps `level → tracker
object`. The tree is the source of truth; the tracker is a render. **Never
round-trip** status back from the tracker — bidirectional sync across mismatched
hierarchies silently corrupts data; that's why this is one-way by default.

## The profiles

| Canonical | `none` | Linear (lean — collapse) | Jira Align (deep — expand) |
| --- | --- | --- | --- |
| top (capability) intent | markdown | Initiative | Epic (Portfolio) |
| feature-level intent | markdown | Project | Feature (Program) |
| extra intervening intents | markdown | labels / sub-issues | (Capability, Solution tier — multi-ART) |
| **spec / slice (leaf)** | a `core` brief | **Issue** | **Story** (Team) |
| story-as-trace (optional) | AC checklist | sub-issue / checklist | Story / sub-task |

- **`none`** — stay in `docs/product/`. The intent tree + the leaf brief are the
  whole record. The right default for a solo dev or a team without a shared
  tracker.
- **Linear (lean)** — three native levels (no Epic/Feature type), so the tree
  **collapses**: top → Initiative, feature → Project, leaf → Issue. Intervening
  levels flatten to labels.
- **Jira Align (deep)** — six levels, so the tree **expands** near 1:1: capability
  → Epic, feature → Feature, leaf → Story. (A Jira Align *Feature* is a Jira
  Software *Epic* on sync — the same word names different levels in adjacent
  tools, which is exactly why the model must be canonical.)

## The impedance is the point

The *same* canonical feature intent lands at a **Project** in Linear and a
**Feature** in Jira Align; the same leaf spec lands at an **Issue** and a
**Story**. If you modelled the work in the tracker, the tool's shape would
corrupt the product model. Model in intents; render to whichever tracker the team
uses; keep `none` a first-class option.

## What v1 ships — and doesn't

v1 ships the **mapping + export shape** (this profile table, applied by hand or by
a one-shot export). It does **not** ship a **live API integration** — auth, rate
limits, idempotency, and conflict rules make that infrastructure, not a habit. A
live Linear/Jira-Align sync is a separate, later pack. Stories are a **traceability
lens** projected *from* a spec, never the decomposition primitive — the spec/slice
is the unit; a story is a view of it.
