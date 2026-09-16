---
type: token-taxonomy
slug: "<kebab-case-slug — the system this taxonomy serves>"
direction: "<name of the aesthetic direction this taxonomy derives from>"
date: "<YYYY-MM-DD>"
---

# Token taxonomy: <system or product name>

<!--
  Written by the `design-system` skill. Fill the angle-bracket prompts and
  delete this comment. This doc holds the *taxonomy* — the roles, the layering,
  and the scale relationships expressed symbolically. It holds NO resolved
  values: no palette, no spacing sheet, no type sheet, no timing table. You
  record the method and the shape; whoever builds resolves the numbers for
  their medium and density, and records them in the interchange file, not here.
-->

## Direction this derives from

<!-- Name the goals from the aesthetic direction. Every role and every scale
     decision below traces back to one of them. A taxonomy with no named goal
     behind it is arbitrary. -->

- **<goal 1>** — <one line on what it asks of the system>
- **<goal 2>** — <one line>
- **<goal 3>** — <one line>

## Layering

<!-- Two layers, always. Primitives are few and carry no context; semantic
     roles reference primitives and are what consumers bind to. Re-pointing a
     semantic role at a different primitive is how a direction change lands
     without a rename. -->

| Layer | What it holds | Who may reference it |
|---|---|---|
| Primitive | <the raw decisions, named without context — e.g. "the deepest surface tone"> | Semantic roles only |
| Semantic | <the jobs, each pointing at one primitive> | Every consumer |

## Semantic roles

<!-- One row per role. Name the job, not the appearance: if a visual refresh
     would force a rename, the name was literal — fix it here. Leave the value
     column as a prompt; resolving it is the builder's step, not this doc's. -->

| Role name | The job it does | Primitive it points at | Traces to goal | Value (builder fills) |
|---|---|---|---|---|
| `<surface.primary>` | <the surface a primary action sits on> | `<primitive name>` | <goal> | <unresolved> |
| `<text.default>` | <the reading text on the default surface> | `<primitive name>` | <goal> | <unresolved> |
| `<emphasis.warning>` | <the emphasis level a warning carries> | `<primitive name>` | <goal> | <unresolved> |
| `<…>` | <…> | `<…>` | <…> | <unresolved> |

## Scale relationships

<!-- One base and one ratio per scale. The ratio IS the decision; the steps
     fall out of it. Name the ratio as a concept derived from a goal — tighter
     reads dense and calm, wider reads bold and spacious — and leave the number
     to the builder. Steps stay symbolic. -->

### Spacing

- **Base:** `<what the base anchors — e.g. the default gap between related items>`
- **Ratio as concept:** <how fast the scale should grow, and which goal asks for that>
- **Steps:** `step −2` · `step −1` · `base` · `step +1` · `step +2`
- **Where each step is used:** <step → the density situation it serves>

### Type

- **Base:** `<what the base anchors — e.g. body reading text>`
- **Ratio as concept:** <how fast headings should separate, and which goal asks for that>
- **Steps:** `step −1` · `base` · `step +1` · `step +2` · `step +3`
- **Where each step is used:** <step → the heading or supporting-text job it serves>
- **Relationship to spacing:** <shared ratio, or a named deliberate divergence and why>

## Accessibility floor

<!-- The floor is a constraint at derivation time, not a later pass. Read the
     threshold from the recognized standard at the conformance level your
     context requires; never reprint it here. -->

- **Standard and conformance level:** <named standard, level your context requires>
- **Pairings checked:** <which role-against-role pairings were derived against the floor>
- **Tensions found:** <any role that cannot clear the floor without breaking a goal — surface it, do not wave it through>

## Contrast budget

<!-- Contrast is finite. Decide where the eye lands first, second, third, and
     spend the strongest contrast there; most of the surface sits quiet. -->

1. <what the eye should land on first, and the role carrying it>
2. <second>
3. <third>

- **Quiet majority:** <which roles deliberately sit low in the budget>

## Serialization

<!-- The taxonomy travels as an interchange file, not as this prose. Point at
     the W3C Design Tokens interchange shape and record where the file lives. -->

- **Interchange file:** `<path to the serialized token file>`
- **Shape:** W3C Design Tokens interchange (name, type, value; groups nest)
- **What lives where:** this doc holds roles and relationships; the interchange file holds the resolved values

## Open questions

- <unresolved role, missing goal, or a tension between a goal and the floor>
