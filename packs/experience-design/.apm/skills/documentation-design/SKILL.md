---
name: documentation-design
description: "Use when designing a documentation surface — a docs site, a help centre, an API reference, or a technical guide set. Decides what type of content belongs where, how navigation scales with content volume, and what the first-value-moment is for each content type. Triggers on 'design the docs site', 'structure the help centre', 'what goes on the docs landing page', 'how should we navigate the API reference', 'TTFV for this tutorial'. Produces IA and navigation specifications for documentation surfaces. Do NOT use for marketing surfaces (use conversion-design) or informational editorial pages (use informational-design). Surface genre: documentation. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register."
---

# Skill: documentation-design

Converts the Diátaxis type mapping and the user's learning goal into a **structural specification for a documentation surface** — the content hierarchy, navigation strategy, landing page IA, and machine-readability decisions that shape whether a reader reaches their first value moment or abandons. This skill is IA and structure; it does not write the documentation (that is `new-guide`) and does not derive the token/scale taxonomy (that is `design-token-taxonomy` and `creative-direction`).

## Output rendering

Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.

## When to invoke

Confirm all three before specifying:

1. **The surface goal is reader enablement** — the primary measure is whether the reader can accomplish a task, understand a concept, or locate a reference. If the primary goal is conversion, use `conversion-design`.
2. **The content set has been typed** — or can be typed inline using the Diátaxis mapping below. Navigation and landing page design are downstream of content typing; starting without typing produces structure that fights its content.
3. **A TTFV target has been named** — what does the reader accomplish in the first successful session? The design serves that target.

## Diátaxis type mapping

Each piece of documentation has exactly one primary type. The type determines its density target, its structural shape, and what it points to next:

| Type | Reader's question | Density target | Points to |
|------|------------------|----------------|-----------|
| **Tutorial** | "How do I start?" | Low — step-by-step, success at the end, no branching | How-to guides (next steps) |
| **How-to guide** | "How do I accomplish X?" | Medium — task-focused, assumes prior knowledge, branching for edge cases | Reference (for parameters/options) |
| **Reference** | "What does X do/accept/return?" | High — complete, accurate, machine-readable | Nothing (reader looks up and leaves) |
| **Explanation** | "Why does X work this way?" | Low-medium — conceptual, narrative-friendly, no step-by-step | How-to guides and references that implement the concept |

**Type mixing is a design finding.** A tutorial that mid-step explains "why we designed the API this way" is a tutorial contaminated with explanation. The reader who came for a tutorial will lose the thread; the reader who came for explanation will lose patience with the steps. Separate them.

## Navigation at scale — 3 strategies by page count

Choose navigation architecture before designing individual pages; navigation retrofit is expensive:

| Page count | Strategy | Shape |
|------------|----------|-------|
| < 30 pages | **Flat nav** — top-level categories + one level of children; everything fits in a sidebar that doesn't scroll off screen | Sidebar with expandable sections |
| 30–200 pages | **Hub-and-spoke** — category landing pages (hubs) that describe what's in the section and direct the reader to the right type | Sidebar + per-category landing pages |
| > 200 pages | **Search-first** — search is the primary navigation; sidebar becomes facet-filtered; landing pages are curated entry points, not exhaustive indexes | Persistent search bar + curated landing pages + faceted sidebar |

**The strategy governs the landing page design.** A flat-nav site's landing page is a category index; a hub-and-spoke site's landing page is an orientation map; a search-first site's landing page is a curated "start here" — three different structures serving three different navigational behaviors.

## Docs landing page — the hub structure

The docs landing page is an **orientation map**, not a content index. Its three jobs:

1. **"Start Here" entry point** — for first-time readers: a single path to the tutorial or quickstart. One link, one promise ("You'll have X working in Y minutes").
2. **Content-type entry points** — four visible sections, one per Diátaxis type, each named by what the reader accomplishes there (not by the type name). "Build your first integration" is better than "Tutorials."
3. **Search** — present above the fold; placeholder text names a real example query ("Search for 'rate limits', 'authentication', 'webhooks'").

The landing page does not repeat the product's marketing copy. It assumes the reader has already bought in; its job is orientation, not persuasion.

## TTFV as design target

**Time To First Value (TTFV)** is the elapsed time from a reader's first page load to the moment they accomplish the goal they came for (a working integration, a working query, an understood concept). It is a design target, not a metric to optimize in isolation.

Design decisions that affect TTFV:

- **Tutorial length:** a tutorial longer than 20 minutes of active work loses readers before the success moment. Scope tutorials to produce a specific, recognizable result; split longer journeys into a series.
- **Prerequisites** (visible before the reader starts, not discovered mid-way through a step)
- **Copy-paste accuracy:** code samples that work exactly as pasted, without unstated setup assumptions, remove friction that appears nowhere in the TTFV metric
- **Error recovery:** when a step fails, the "why this might have happened" text is part of the tutorial experience — its absence adds unmeasured time

## Machine-readability as design-phase decision

Documentation that will be consumed by LLMs, IDE extensions, or search indexers has structural requirements that are design decisions, not implementation details:

- **Code blocks** typed with the language identifier (` ```python `, not ` ``` `) are extractable; untyped blocks are noise
- **API parameter tables** with consistent column headers (Parameter / Type / Required / Default / Description) are parseable; prose descriptions are not
- **Structured output examples** (showing both the call and the response) are more valuable than either alone to a machine reader
- **Heading hierarchy** that reflects the content type (H2 = section, H3 = procedure step, H4 = sub-step) enables extraction; flat heading use collapses the structure

Name these as design requirements in the specification, not as implementation notes. They affect IA decisions (column design in tables, code block placement in tutorials) and are invisible to a reader who is looking at rendered output.

## Canonical aesthetic reference tier (study subjects, not prescriptive tools)

For grounding creative-direction on a documentation surface, study how these sites handle navigation clarity and reading density: Stripe Docs (reference density + navigation at scale), Vercel Docs (tutorial clarity + search-first at scale), MDN Web Docs (type-consistency + machine-readability at reference depth). Internalize the structural philosophy — content typing, navigation layering, first-value-moment clarity — not the surface treatment.

## Anti-patterns to refuse

- **Type mixing in a single page.** Tutorial steps contaminated with explanation prose, or reference pages that include tutorial examples, serve neither reader well. Type each piece of content before placing it.
- **Navigation designed before content is typed.** Navigation structure is downstream of content type and volume; building the nav first produces a structure the content will fight.
- **Landing page as marketing copy.** A docs landing page for a reader who is already a customer does not need to sell them again. Orientation and entry points, not persuasion.
- **TTFV ignored in tutorial length.** A tutorial whose success moment comes after an hour of setup has no TTFV; it has an abandonment rate. Scope tutorials to produce success in a single sitting.
- **Machine-readability deferred to engineering.** Heading hierarchy, code-block typing, and table column structure are IA decisions made at design time; retrofitting them is expensive and incomplete.
