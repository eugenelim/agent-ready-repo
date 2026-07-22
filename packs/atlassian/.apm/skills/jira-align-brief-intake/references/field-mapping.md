# Jira Align → Brief field mapping

> **Before first use on a new Jira Align instance:** fill in the
> "Customize for your org" sections below. Jira Align workflow state names
> and Program Increment cadences are org-specific — the defaults here are
> common but are not guaranteed to match your instance. A wrong state name
> will produce a misleading brief context sentence.

## Standard Feature fields → Brief fields

| Jira Align field | Brief field | Notes |
|---|---|---|
| `title` | Brief heading (`# Brief: <title>`) | Direct |
| `description` | `## Outcome` (lead paragraph) | |
| `notes` | `## Outcome` (appended context) | Combine with `description`; lead with `description` |
| `acceptanceCriteria` | `## Scope / In scope` | Carry verbatim; `receive-brief` refines |
| `id` | `Epic:` provenance pointer | Full URL: `<JIRAALIGN_BASE_URL>/features/<id>` |
| `programID` | Context note (not a brief field) | Include in `## Context` if useful |
| `points` | `## Success metrics` (optional) | Surface as size signal, not a target |
| `ownerUser` (expanded) | `- **Owner:**` header field | Use `name` from expanded record |
| `milestones` (expanded) | `## Context` — PI note | See PI section below |

Fields absent or empty in the API response → leave the corresponding brief
heading empty (do not invent). `receive-brief` elicits missing values during
Elicit.

## Customize for your org — workflow state vocabulary

Jira Align state names are configured per instance. Replace or extend the
table below with your instance's actual state names. The `Brief handling`
column tells the skill what to surface in the Outcome context sentence.

| Jira Align state (your instance) | Standard equivalent | Brief handling |
|---|---|---|
| `Planned` | Not started | Mention in Outcome as context: "currently Planned" |
| `In Progress` | Active delivery | Mention in Outcome as context: "currently In Progress" |
| `Completed` | Done | Note: verify scope is accurate before intake; mention in Outcome |
| `Not Started` | Not started | Mention in Outcome as context: "not yet started" |
| *(add your org's custom states here)* | | |

**How to find your states:** In Jira Align, go to Administration → Workflow
States (or check with your Jira Align administrator). Each state name must
match exactly what appears in the `state` field of a Feature API response.

## Customize for your org — Program Increment (PI) cadence

Program Increment names follow your org's naming convention. Common patterns:

| Pattern | Example | When to use |
|---|---|---|
| Quarterly (`YYYY-Qn`) | `PI 2026-Q1` | Most common for Scaled Agile orgs |
| Numbered | `PI 24`, `PI 25` | Sequential numbering since program start |
| Named | `PI Orion`, `PI Acme` | Thematic or project-specific naming |
| Custom | *(your format)* | Fill in your org's convention |

When the Feature's `milestones` expand to a PI record, extract the PI `name`
field and include it in the brief's `## Context` section as an appetite
signal. Example:

```
> **Program Increment:** PI 2026-Q2 — carry forward as appetite signal;
> confirm with `receive-brief`.
```

When `milestones` is absent or empty, omit the PI note.

## Child → US-n provenance format

Each child item (story, task, or defect) maps to one Shape B user story
line. The format is pinned — downstream `Satisfies: US-n` traces depend on
it:

```
- **US-n.** (<resource-type>/<id>) <story text>
```

Where:
- `<resource-type>` is `stories`, `tasks`, or `defects`
- `<id>` is the integer ID from the Jira Align response
- `<story text>` is the child's `title` reshaped into *As a … / I want … /
  so that …* grammar **only when the title itself states a role**; otherwise
  the title carried verbatim — do not invent a role from `ownerID` alone
  (an integer ID yields no name)

Examples:
```
- **US-1.** (stories/4521) As a PM, track PI velocity to forecast capacity.
- **US-2.** (tasks/892) Update onboarding documentation to reflect Q2 process changes.
- **US-3.** (defects/301) Critical authentication timeout not surfaced to users on session expiry.
```

Index (`US-n`) is sequential across all resource types, ordered: stories →
tasks → defects.

## What to do when fields are missing

| Situation | Action |
|---|---|
| `description` and `notes` both empty | Write `[Outcome not provided — receive-brief will elicit]`; do not invent |
| `acceptanceCriteria` absent | Leave `## Scope / In scope` heading with empty placeholder |
| `milestones` absent or empty | Omit the PI context note |
| Custom field present in response but not in this table | Include it in `## Context` with the raw field name; note it needs mapping |
| Custom field mentioned here but absent from API response | Skip it; note the gap in the brief if material |
