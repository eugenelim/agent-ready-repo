---
type: cross-surface-seam
slug: team-orientation-seam
status: active
surfaces:
  - marketing (acquisition genre)
  - documentation guides (documentation genre)
genre_crossing: true
evidence_level: mixed — see the discovery brief
gap: B
updated: 2026-09-04
---

# The marketing-to-documentation seam

**Why this artifact exists.** `journey-mapping` takes one surface and one genre;
all seven of its genre scaffolds are per-surface, and each produces a map whose
unit of analysis is a *stage*. This engagement is two genres with a crossing, and
the crossing is the diagnosed failure. No installed skill owns it. This document
is hand-authored and its unit of analysis is the **transition**, not the stage.

**The division of labour.** The two journey maps stay canonical for their own
surface. This document owns only the edges between them, and it may not
contradict either map — where it appears to, the map wins and this document is
wrong.

- [Marketing journey](../journeys/marketing-champion-current-state.md)
- [Documentation journey](../journeys/docs-guides-champion-current-state.md)

**What arbitrates.** The fourth tech-site principle: *preserve each surface's
reading mode within one product identity.* It rules out the obvious fix. Making
the two surfaces look, read, or navigate alike is a violation, not a repair. The
seam must be closed with shared **vocabulary and destinations**, never shared
presentation. `site.toml` is the existing mechanism for exactly that — it already
carries destination IDs, labels, targets, groups, order, and target kind across
renderers while sharing no presentation.

## The three crossings, and which one actually carries traffic

### Crossing A — marketing to documentation, the designed path

| | |
| --- | --- |
| **Last marketing state** | The reader has copied an install command. Marketing journey Stage 4, its highest positive moment. |
| **First documentation state** | "Choose the pack and guide that matches your outcome." Documentation journey Stage 2. |
| **What the reader carries across** | An outcome frame, a handful of pack names, and one command they have run or intend to run. |
| **What the design drops** | The model they were trying to assemble in marketing Stage 3, and the reason they came — needing something to hand to other people. Neither survives the crossing. |
| **Route that exists** | One link, from the closing section, to a single `_shared` how-to. Plus a global "Docs" link to `/docs/`. |
| **Route that does not exist** | Any link from marketing to the guides index, or to any of the six ordered paths. Twenty-one of twenty-two guide areas have no direct marketing route. |

The crossing is diagnosed as *marketing ends at install, documentation begins at
catalogue selection*. That is accurate. It is also symmetrical in a way the
diagnosis does not say: **both sides open with our taxonomy.** Marketing's
Stage 2 hands the reader a pack menu; documentation's Stage 2 hands them a pack
nav. The reader crosses a seam and meets the same failure twice.

### Crossing B — documentation back to marketing, the path nobody designed

| | |
| --- | --- |
| **Last documentation state** | The reader has found an ordered path — P1 through P6 — and knows what to give an engineer. Documentation journey Stage 3, the highest positive moment across both surfaces. |
| **What they now need** | To convince a budget holder. That is a persuasion job in the acquisition genre. |
| **Route that exists** | None. |

This crossing is absent from the diagnosis and it is the champion's actual
blocker. A reader who has understood the model in the documentation surface has
no way back to a surface that helps them sell it — and the surface they came from
would not have helped anyway, because it never stated the model whole.

The consequence is that the champion improvises. Marketing journey Stage 5 is
this crossing's failure mode.

### Crossing C — marketing to repository source, the path that carries the traffic

| | |
| --- | --- |
| **Observed** | One raw `SKILL.md` in the github.com file browser drew 12 unique readers in 14 days. A skill reference tree drew 7. `/tree/main/docs` drew 6. |
| **For comparison** | The published site referred 6 unique visitors to the repository in the same window. A repository link pasted into Microsoft Teams drew 12. |
| **Owned by** | Neither surface. |

This is the crossing with the most measured traffic and it is not in the design at
all. Readers leave both published surfaces and read executable source, because
source is the thing they trust and because the file tree is a better index than
the sidebar.

It cannot be closed by blocking it, and should not be — reading the source is a
legitimate and healthy behaviour for this audience, and the second tech-site
principle actively wants readers able to check claims against real artifacts. It
can only be closed by making the published surfaces worth arriving at, and by
accepting that the repository is a first-class entry point rather than a leak.

That acceptance is what makes the canvas's README portability a requirement
rather than a nicety.

## The crossing contract

Four invariants the design must satisfy at the boundary. Each is checkable, and
each names what would falsify it.

**1. Vocabulary continuity.** Two vocabularies cross, and they are different axes — an earlier draft conflated them. (a) The **work-lifecycle decision phrasings** are identical wherever they appear on either surface, and the three human-decision labels are adapted from the published P-path *first value* and *ends at* fields. (b) The **seven job names** are identical across the marketing outcome router, the guides achieve-table, and the documentation sidebar. The **five adoption station names** are marketing-side only; they are not job groups and must not be forced into the documentation navigation. *Falsified by:* a decision phrasing or a job name that differs between the two surfaces — not by the stations being absent from the docs nav, which is correct.

**2. Positional continuity.** A reader arriving on either surface can tell, without
scrolling, which lifecycle they are looking at and roughly where in it they are.
*Falsified by:* a landing state where the reader cannot answer "is this about my
work or about my team".

**3. Directional completeness.** Both directions have a route. Marketing offers a
route into the ordered paths; documentation offers a route back to the artifact a
champion can hand upward.
*Falsified by:* Crossing B remaining absent.

**4. Genre integrity.** Marketing stays persuasive and documentation stays
optimized for sustained technical reading. Shared vocabulary and shared
destinations cross the seam; palettes, components, breakpoints, reading modes,
and navigation patterns do not.
*Falsified by:* any shared CSS, component, palette, or navigation pattern between
the two renderers, or documentation copy that acquires a persuasion register.

Invariant 4 is the one most likely to be violated in the name of fixing the seam,
which is why it is stated as a refusal rather than a preference.

## What crosses, and what must not

| Crosses the seam | Stays on its own side |
| --- | --- |
| The seven job names — already on both surfaces | Palettes and tokens — the two renderers are deliberately separate |
| The five adoption station names — **marketing-side only**, not a docs taxonomy | The five stations as documentation navigation |
| The work-lifecycle step names | Components, breakpoints, focus implementation |
| Human decision phrasing, never gate codes | Reading mode and information density |
| `site.toml` destination IDs, labels, targets, groups, order, target kind | Any presentation of those destinations |
| The canvas, as a static portable artifact | Navigation patterns — one canvas versus a job-grouped sidebar |
| Time costs and stated first results from the P-paths | Persuasion register |

## Handoff

**For `information-architecture`:** the seam is a navigation problem in both
directions, and Crossing B needs a destination that does not exist today.

**For `conversion-design`:** the marketing surface owes the documentation surface
one route into the ordered paths, placed where marketing Stage 3 currently
strands the reader, not in the footer.

**For `documentation-design`:** the documentation surface owes the marketing
surface Crossing B — a route from "I understand this" to "help me sell this" —
and it must be built without the documentation surface acquiring a persuasion
register.

**For the canvas specification:** Crossing C makes README portability a hard
requirement. The canvas is the one artifact that has to work on all three sides
of these crossings.

**Recorded as a gap.** Gap B in the discovery brief. The workaround used here —
run the per-surface skill twice, then hand-author a transition-scoped artifact
whose invariants are falsifiable — is the pattern a future cross-surface skill
would need to own.
