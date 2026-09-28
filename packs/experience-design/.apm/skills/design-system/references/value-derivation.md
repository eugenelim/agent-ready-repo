# Resolving a direction into system values

Load this when a route must resolve values — `originate` always, `extend` for
the capability being added, `refine` for the domain the rendered result
exposed. `inherit` loads it only for a gap the incumbent system does not fill.

This page never carries a value. It carries how a value is reached, and how to
tell an axis you have authority over from one you do not.

## Every axis lands in exactly one domain

The direction sheet commits fifteen axes. Each one constrains one system
domain, and a domain with no axis behind it has no direction authority. Read
the axis tokens, not the prose beside them — the prose explains the choice, the
token *is* the choice.

| Direction axis | Domain it constrains |
| --- | --- |
| Grid grammar | spatial structure |
| Alignment and equilibrium | spatial structure |
| Spatial density | spacing and rhythm |
| Whitespace distribution | spacing and rhythm |
| Section and scroll rhythm | spacing and rhythm |
| Hierarchy and scale contrast | typography |
| Type voice | typography |
| Type hierarchy | typography |
| Chromatic intensity | color |
| Containment and boundary strength | shape and containment |
| Form | shape and containment |
| Material and depth | depth |
| Ornament and texture | graphic language |
| Image treatment | graphic language |
| Motion character | motion |

A domain reached by more than one axis is resolved from all of them together.
`Spatial density` saying dense while `Whitespace distribution` says expansive
is a tension to surface, not an average to split.

## Deciding whether you may resolve a domain

Ask this per domain, in order, and stop at the first answer.

1. **Does a stated project constraint name it?** Then it is already decided.
   Record the constraint as the authority and move on.
2. **Does the incumbent system already own it, and is the route `inherit`?**
   Then the incumbent value is the value. Do not restate it as a new decision.
3. **Do the domain's axes carry decided tokens?** Then you have authority.
   Resolve values that make those tokens true for this product.
4. **Is a structural axis sitting at `[platform-default]`?** Then stop here.
   The direction owes that decision, so it is a gap upstream rather than a
   platform deferral. Report it back and do not resolve around it. This test
   comes before step 5 because both match the same cell and they prescribe
   opposite actions.
5. **Do the axes read `[platform-default]` while the direction names a target
   surface?** Then that platform's own convention owns the decision. Resolve
   from the platform's published convention and record the rung as
   `platform-convention`, naming which convention you read.
6. **Otherwise the domain is unresolved.** Record it, name the authority that
   is missing, and say which upstream operation would supply it. Do not choose.

Step 4 exists because `[platform-default]` means two different things upstream.
In exploration it marks an axis the platform genuinely owns. In convergence it
is also the token for undecided, and only the seven structural axes are
forbidden to keep it. Treating both as undecided reports typography, color and
motion unresolved for a perfectly well-converged platform-targeted direction,
which helps nobody.

The **structural** axes step 4 names are grid grammar, alignment and
equilibrium, spatial density, whitespace distribution, hierarchy and scale
contrast, containment and boundary strength, and section and scroll rhythm.
Convergence upstream is required to decide those seven, which is why one left
at `[platform-default]` reads as a gap rather than a deferral.

## What a visual target gives you, and what it does not

An approved visual target is a confirmed composition. It binds arrangement,
proportion and spatial relationships. It **supplies no value at all** — not a
color, not a type size, not a spacing step, not a duration. The skill upstream
of this one says so, and the implementation downstream says so; this page is
the third place the same rule is written, because it is the one most likely to
be broken here.

What you may take from it is relational, and you take it by looking. Relative
scale, density, hierarchy, containment, depth, spacing character, color
relationships and recurrent graphic language are all readable this way:

- how much larger the dominant element reads than the next one — its relative scale
- how tight or open the surface reads overall
- which colors are doing the separating, and which are doing nothing
- what reads as a container and what reads as open field
- whether anything sits above anything else
- how the spacing between groups compares to spacing within a group
- which graphic treatment recurs often enough to be a rule

Turn each of those into a *relationship*, then resolve the relationship into a
value from the direction and the platform. Never report a value as measured.
Nothing here measures anything: there is no image analysis, no pixel sampling,
and no extraction step, so a number presented as read off the target is
invented with a false provenance attached. If you cannot infer a relationship
reliably, make a coherent choice from the direction and say that is what you
did.

## Resolving each domain

Resolve the smallest coherent set. A domain is done when a build could act on
it, not when it has a row for everything the domain could have.

**Typography.** Name the family or families the type voice asks for, or the
incumbent family where one exists. Name the roles the product actually has —
usually a display role, a reading role, and a functional interface role — and
say what separates them. `Type hierarchy` sets how far apart the roles sit;
`Hierarchy and scale contrast` sets how hard the largest works. Resolve size
relationships, weight use, line height, letter spacing where it is doing work,
and the measure reading text should hold. Three or four sizes that mean
something beat nine that do not.

**Color.** Start from roles, not from a palette: what a surface is, what sits
on it, what separates two things, what marks the one action that matters, what
reports a state. `Chromatic intensity` decides how much of the surface carries
color at all. Resolve every role to a value, check each text-on-surface pairing
against the floor, and keep the contrast budget — decide where the eye lands
first, second and third, and let the rest sit quiet. A large palette is a sign
the roles were not named.

**Spacing and rhythm.** One base, one ratio, and the steps the product's real
layouts need. `Spatial density` and `Whitespace distribution` set the base and
the ratio between them; `Section and scroll rhythm` sets how sections separate
against how controls pack. Resolve the container behaviour and gutters, and say
which step serves which situation. Most products need four or five steps.

**Shape and containment.** `Containment and boundary strength` decides whether
this product has cards at all, and `Form` decides whether its corners are sharp
or softened. Resolve the corner treatment, the border and divider treatment,
and the rule for when a region becomes a bounded panel and when it stays open
field. A direction that rejects the category default rejects its containment
habit too; do not hand back panels because panels are common.

**Depth.** `Material and depth` decides whether this world is flat or layered.
If flat, say so and resolve nothing further — a flat system with no shadow
value is complete, not unfinished. If layered, resolve only the elevation
levels that exist: what floats, what sits above what, and what separates them.

**Motion.** `Motion character` decides whether motion is present at all. When
it is, resolve the duration families the product needs, the easing behaviour,
and what each transition is telling the reader. Always resolve the
reduced-motion behaviour: the information the motion carried must survive when
the platform's reduced-motion signal is set. Resolve nothing decorative.

**Graphic language.** Resolve this only when `Ornament and texture` or
`Image treatment` carries a decided token and the treatment recurs. Then say
what the rule is — how images are cropped and toned, what the recurring mark
is, where it may and may not appear. Most products have no such subsystem and
should not be given one.

**Spatial structure.** `Grid grammar` and `Alignment and equilibrium` resolve
into the column behaviour, the alignment the surface holds to, and whether the
composition is balanced or deliberately weighted. This domain often binds to
layout rules rather than to named tokens; record it as rules where that is
true.

## Relationships first, then values

The relationship is the part that must survive implementation; the value is
what makes it executable today. Write both, in that order, and keep the
relationship in language a person can check by looking:

```text
display type reads markedly larger and tighter than reading text
functional interface type stays neutral and compact at every size

sections separate generously; controls inside a section pack tightly

most of the surface is open field
only an interactive working region becomes a bounded panel
```

A build that changes a value but keeps the relationship has not broken the
system. A build that keeps every value and inverts a relationship has.

## Prove it against real product needs

A system that is internally tidy can still fail the first time it meets a real
screen. Before writing the artifact, apply the resolved system to a **proving
set** — the smallest group of real product needs that exercises every resolved
domain at least once.

Draw candidates from what the product actually has: the primary surface, its
navigation, a dense content hierarchy, a form control, a data display, an
interactive state, the narrow channel, and an overlay or floating surface. Pick
the fewest that cover your resolved domains, not all of them.

This is not building the interface. It is checking each need against the system
and answering one question: does the system say what to do here, and is the
answer any good? Two failures are common and both are findings, not details —
a domain that turns out to have no answer, and a relationship that inverts the
moment it meets a real amount of content.

Record the proving set in the artifact. A system nobody tested reads the same
as one that passed.

## The floor is not one of the rungs

Accessibility constrains every value you resolve and supplies none of them. It
is not ranked against a goal and it does not lose an arbitration, because it is
not in the arbitration. The criteria live in the shared checklist at
`../design-review/references/quality-floor.md`; read them there rather than
from memory, and read any threshold from the standard itself.

When a resolved value cannot clear the floor, keep the *relationship* the
direction asked for and move the value until it clears. A direction asking for
a quiet, low-contrast surface still gets a quiet surface — the quietest one
that stays readable. Record the adaptation: what the direction asked for, what
the floor required, and what you resolved instead. An adaptation recorded is a
decision someone can revisit; an adaptation made silently reads as the
direction having asked for the compromise.

Never resolve the other way. Fidelity to a target or a goal does not buy an
exemption.
