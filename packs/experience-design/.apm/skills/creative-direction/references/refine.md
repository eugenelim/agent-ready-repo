# refine — mapping a requested change to the axes that may move

> **Question:** which axes does this change request put in play, and which must stay fixed?

## One operation

`refine` is a single operation. It takes a requested change stated in plain words and returns the set of axes that may move, with all other axes locked.

The wordings below are request wordings, not separate operations.

## Request-wording to axis map

Each row names a common request wording and the axes it puts in play. Axis names are taken from the fifteen axes the direction sheet carries.

| Request wording | Axes in play |
| --- | --- |
| bolder | Hierarchy and scale contrast, Type hierarchy, Chromatic intensity |
| quieter | Spatial density, Whitespace distribution, Chromatic intensity, Ornament and texture |
| distill | Ornament and texture, Image treatment, Spatial density |
| typeset | Type voice, Type hierarchy |
| layout | Grid grammar, Alignment and equilibrium, Containment and boundary strength, Section and scroll rhythm |
| colorize | Chromatic intensity |
| delight | Ornament and texture, Motion character, Image treatment |

A request may invoke more than one wording; the axes in play are the union of the rows matched.

## Stability contract

Every axis not named by the request wording stays fixed. In addition, each of the following stays fixed regardless of which axes move:

- **Ranked goals and the dominant goal** — the priority order the work was built around; changing it reopens `frame`.
- **Grounding referents** — the persona, precedent, standards, and platform conventions that anchor each goal.
- **The signature device** — the single visual decision that makes the direction recognisable; moving it is a direction change, not a refinement.
- **Every unnamed axis** — its token does not change.

## Recording the amendment

The result of `refine` is recorded as an amendment to the existing direction doc. A second direction doc must not be written for the same surface. The amendment names which axes moved, the token each held before, the token it holds after, and the reason the change serves the ranked goals.

## Scope boundary

`refine` does not reopen goals, audience, or product strategy. Goals and audience belong to `frame`; product strategy belongs outside this skill entirely. A request that asks for any of these is returned to the appropriate owner rather than resolved here.

## Quality floor

`refine` holds the quality floor at `../design-review/references/quality-floor.md` before recording its amendment. A refinement that moves a chromatic or type axis can breach the floor, and `refine` writes without passing through `converge`, so the floor check must be explicit here. If a proposed token change fails the floor, the change is refused and the reason is named.

## Axis vocabulary

The fifteen axes are the complete vocabulary for refinement. A request that names an axis outside the fifteen is refused; the axis vocabulary is the answer.

---

**References:** `references/divergence-audit.md`, `references/refusals.md`
