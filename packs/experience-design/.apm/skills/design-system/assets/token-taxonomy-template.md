---
type: token-taxonomy
slug: "<kebab-case-slug — the system this serves>"
direction: "<name of the aesthetic direction this derives from>"
route: "<inherit | extend | originate | refine>"
date: "<YYYY-MM-DD>"
---

# Design system: <system or product name>

<!--
  Written by the `design-system` skill. Fill the angle-bracket prompts and
  delete this comment.

  This doc holds the system: the relationships that must survive
  implementation, and the values that make them executable for THIS product.
  Resolve a domain when the authority table gave you the right to; record it
  unresolved when nothing did. Do not leave a domain the direction reached as
  a prompt for whoever builds — that is the decision this document exists to
  make. Delete any section the product does not need; an empty section is
  worse than an absent one. Four sections are never deletable: Authority,
  Accessibility, Proving set, and Unresolved decisions. They are what makes the
  rest checkable.
-->

## Authority

<!-- Where every decision below came from. A reader must be able to tell an
     inherited value from an invented one. -->

- **Route:** <inherit | extend | originate | refine> — <why this one>
- **Direction source:** <path or name of the approved direction, or "none">
- **Incumbent source:** <the file or module the interface actually reads its
  visual values from, or "none found — searched <where>">
- **Visual target:** <what it is and what it was read for, or "none". It binds
  composition and relationships; it supplies no value>
- **Stated constraints:** <any constraint that arrived already decided, or "none">

A domain nothing resolved is marked `unresolved` here *and* explained under
Unresolved decisions. Both are required: this table says which domains are
open, that one says why and who closes them.

| Domain | Rung that supplied it |
|---|---|
| Typography | `<stated-constraint \| approved-direction \| incumbent-system \| platform-convention \| derivation \| unresolved>` |
| Color | `<…>` |
| Spacing and rhythm | `<…>` |
| Shape and containment | `<…>` |
| Depth | `<…>` |
| Motion | `<…>` |
| Graphic language | `<…>` |
| Spatial structure | `<…>` |

## Direction this derives from

<!-- The ranked goals, and the axis tokens that gave you authority. Every
     decision below traces to one of them. -->

- **<goal 1>** — <what it asks of the system>
- **<goal 2>** — <…>
- **<goal 3>** — <…>

**Axes this direction decided:** <list the axes carrying a decided token>
**Axes left to the platform:** <axes at `[platform-default]` the named target surface owns>
**Axes nobody decided:** <axes with no authority — these become unresolved decisions below>

## System commitments

<!-- One block per domain you resolved. In each: the relationship first, then
     the values that make it executable. Skip a domain you did not resolve and
     record it under Unresolved decisions instead. -->

### Typography

- **Relationship:** <how the roles relate — what reads larger, tighter, quieter>
- **Families:** <the family or families, and which role each serves>
- **Roles and values:**

| Role | Job it does | Resolved value | Traces to |
|---|---|---|---|
| `<display>` | <…> | <size, weight, line height, tracking, measure> | <goal or axis> |
| `<body>` | <…> | <…> | <…> |
| `<ui>` | <…> | <…> | <…> |

### Color

- **Relationship:** <how much of the surface carries color; what separates what>
- **Roles and values:**

| Role | Job it does | Resolved value | Traces to |
|---|---|---|---|
| `<surface.default>` | <…> | <…> | <…> |
| `<text.default>` | <…> | <…> | <…> |
| `<accent.action>` | <the one action that matters> | <…> | <…> |
| `<border.divider>` | <…> | <…> | <…> |
| `<state.*>` | <…> | <…> | <…> |

- **Contrast budget:** <where the eye lands first, second, third — and which
  roles deliberately sit quiet>

### Spacing and rhythm

- **Relationship:** <section rhythm against control rhythm; density character>
- **Base and ratio:** <what the base anchors, and the ratio that generates the steps>
- **Steps and their use:** <step → the situation it serves, with the resolved value>
- **Container and gutters:** <how the content area behaves, and at what widths>

### Shape and containment

- **Relationship:** <what is a bounded panel and what stays open field>
- **Corner treatment:** <resolved>
- **Borders and dividers:** <resolved, or "none — separation is by spacing">
- **When a region becomes a panel:** <the rule>

### Depth

- **Relationship:** <flat, or layered — and what that means here>
- **Levels:** <only the elevation levels that exist, with resolved values. A
  flat system records "none" and is complete, not unfinished>

### Motion

- **Relationship:** <what motion is telling the reader; none is valid>
- **Durations:** <the families the product needs, resolved>
- **Easing:** <the behaviour, resolved>
- **Reduced motion:** <how the information the motion carried survives when the
  platform's reduced-motion signal is set>

### Graphic language

<!-- Only when the direction made imagery or ornament systematic. Most products
     have none; delete this section rather than inventing a subsystem. -->

- **Rule:** <how images are cropped and toned; what the recurring mark is;
  where it may and may not appear>

### Spatial structure

- **Column behaviour:** <resolved>
- **Alignment:** <what the surface holds to>
- **Balance:** <symmetric, or deliberately weighted, and why>

## Rules implementation must preserve

<!-- The relationships a build may not break, and the treatments this direction
     rules out. Values may be adapted; these may not. -->

- <relationship that must survive, stated so a person can check it by looking>
- <…>

**Prohibited treatments:** <a default this direction explicitly rejects — say
it here so a build does not reach for it. "none" is valid>

**May adapt responsively:** <what a build is free to move across channels>

## Proving set

<!-- The real product needs this system was checked against, and what each
     exposed. A system nobody tested reads the same as one that passed. -->

| Product need | Domains it exercised | What it exposed |
|---|---|---|
| <the primary surface> | <…> | <held, or the finding> |
| <a form control> | <…> | <…> |
| <the narrow channel> | <…> | <…> |

## Accessibility

<!-- Criteria live in the shared quality floor at
     `../design-review/references/quality-floor.md`; read thresholds from the
     standard itself. Where the context does not fix a level, the product owner
     chooses it and is named here. -->

- **Standard and conformance level:** <the named standard, at the level your context requires — and who chose it when the context did not>
- **Pairings checked:** <which resolved role-against-role pairings were checked>
- **Adaptations made:** <what the direction asked for, what the floor required,
  and what you resolved instead. "none required" is valid>

## Binding

<!-- How these values reach the interface, following whatever the project
     already uses. Where binding happens later or elsewhere, say so. -->

- **Architecture:** <the project's existing shape — layered token source, a
  custom-property file, a theme object, a platform token source, a constants
  module, or design-only with binding deferred>
- **Where the values live:** <path, or "not yet bound">
- **Naming convention followed:** <the incumbent one, named>

## Changes to the incumbent system

<!-- Required on inherit, extend and refine. Delete on a confirmed-greenfield
     originate. A change with nothing retained is a replacement wearing an
     extension's name. -->

- **Retained:** <incumbent values and relationships carried unchanged>
- **Extended:** <what was added, on which incumbent scale, at which naming>
- **Replaced:** <what changed, what it was, and which approved commitment required it>

## Unresolved decisions

<!-- Genuine gaps only: a domain no authority reached. Name what is missing,
     who resolves it, and the operation that supplies it. A routine decision
     parked here is the failure this document exists to prevent. -->

| Domain | Authority that is missing | Who resolves it | Operation that supplies it |
|---|---|---|---|
| <…> | <…> | <…> | <…> |
