---
name: informational-design
description: "Use when designing an informational surface — an article page, a news or editorial page, a long-form content page, or a content-rich page whose primary purpose is to inform, not to convert or enable tasks. Triggers on 'design the article page', 'structure the editorial page', 'how should the blog look', 'long-form content design', 'reading experience design'. Uses typography as the primary design tool. Do NOT use for documentation (use documentation-design), marketing (use conversion-design), or tool/app surfaces (use workspace-design). Surface genre: informational."
---

# Skill: informational-design

Converts the editorial structure and reading goal into a **structural specification for an informational surface** — the typographic hierarchy, the reading-pattern calibration, the editorial grid, and the "what's next" chain that sustains reader engagement after the primary content is consumed. This skill uses **typography as the primary design tool**; layout, grid, and navigation are typography's support structure. It does not write the content (that is `content-design`) and does not derive tokens or color (that is `design-system` and `creative-direction`).

## When to invoke

Confirm all three before specifying:

1. **The surface goal is to inform** — the reader arrives to understand something, not to accomplish a task or make a purchase. If the primary goal is conversion, use `conversion-design`; if it is task enablement, use `documentation-design`.
2. **The content is text-primary** — typography is the primary design tool only when text carries the content. An image gallery, a data table, or a video page has a different primary tool; this skill handles the text-dominant case.
3. **A reading goal is named** — what will the reader know or be able to do after reading this piece that they didn't know or couldn't do before? The reading goal governs what the content hierarchy foregrounds.

## Typography as primary design tool

On an informational surface, typography IS the design. Visual design choices that are not grounded in reading legibility are decoration.

**Line length: 45–75 characters per line**
Line length governs reading speed and comprehension. Below 45 characters, the eye saccades too frequently; above 75, it struggles to find the next line. The optimal range for sustained reading is 45–75 characters. Measure from column content edge to edge; do not include padding.

Specify the maximum content width as a design constraint, not a layout value. The constraint is: the column width that produces 45–75 characters per line at the chosen type scale.

**Line height: 1.4–1.6× the type size**
Line height governs vertical rhythm and the sense of spaciousness. Below 1.4×, lines crowd and leading fatigue sets in. Above 1.6×, lines drift apart and the reader loses the thread. The constraint is expressed as a multiplier; the resolved value follows from the chosen type scale.

**Scale contrast between heading levels**
The heading hierarchy must be visually unambiguous at a glance — a reader scanning should distinguish H1 from H2 from H3 without reading the text. Specify the minimum contrast between adjacent heading levels as a design constraint. A heading hierarchy where H2 and H3 are visually similar has failed its navigational job.

## F-pattern and Z-pattern calibration

The dominant reading pattern on a page informs how content is structured and where hierarchy signals are placed:

**F-pattern (information-dense pages)**
The reader scans the first paragraph fully (the top bar of the F), then scans the beginning of subsequent paragraphs (the left stroke of the F), looking for the line that matches their need. Apply when:
- The content is long-form, reference-heavy, or research-oriented
- The reader is looking for a specific section rather than reading straight through
- Design implication: **subheadings carry the majority of navigation work** — they must be informative, not decorative ("How to configure the database" not "Configuration"). The first sentence of each paragraph must carry the paragraph's thesis.

**Z-pattern (conversational or single-topic pages)**
The reader scans from top-left to top-right (the first bar of the Z), diagonally to bottom-left, then left to right again (the second bar). Apply when:
- The content is short, single-topic, or narrative
- The reader is reading rather than scanning
- Design implication: **hierarchy signals are at the top and the call-to-action at the bottom**. Subheadings serve visual breathing room more than navigation.

## Editorial grid

The editorial grid is a column structure that gives text and visual elements a consistent spatial relationship. Specify the grid before placing content:

- **Column structure:** how many columns? Informational pages typically use a center column (the reading lane) flanked by margin zones. The reading lane is sized to produce the line-length constraint; the margins hold annotations, pull quotes, or white space.
- **Asymmetric grid:** when the content benefits from a sidebar (table of contents, related links, secondary information), the grid is asymmetric. Specify the ratio of primary column to secondary column; the secondary column width is constrained by readability at its type scale, not by aesthetics.
- **Breakpoint behavior:** how does the grid respond when the reading lane can no longer hold its minimum width? The columns collapse in a specified order; the reading lane is the last to collapse.

## Article page structure

The canonical informational article page has these structural zones:

1. **Headline + deck** — the conviction statement (headline) + the orienting sentence (deck) that tells the reader what they will know after reading.
2. **Author + date + estimated reading time** — trust signals; reading time sets the commitment expectation.
3. **Body** — organized by the F or Z pattern appropriate to the content. Subheadings are navigational tools on F-pattern pages; breathing-room tools on Z-pattern pages.
4. **"What's next" chain** — see below.

## "What's next" chain design — 4 category types

After the primary content is consumed, the reader's next decision is: do I go deeper, explore sideways, take action, or discover something new? The "what's next" zone serves one or more of these:

| Category | Reader intent | Design shape |
|---------|--------------|-------------|
| **Related topic** | "I want more context on a theme this article touched" | Topic-cluster links, tagged content by theme |
| **Deeper dive** | "I want to go further on THIS topic" | A curated sequence: the next article in a series, a related long-form piece, the primary reference on this subject |
| **Action** | "I now know enough to do something about this" | A contextual CTA that connects the content to a next action (relevant feature, tool, or resource) |
| **Discovery** | "I didn't know I wanted this until I saw it" | Editorially curated "you might also like" — personalized or recency-based |

Name which categories the "what's next" zone serves and design each category's visual weight accordingly. A zone that tries to serve all four with equal weight serves none of them.

**Entry point diversity:** readers arrive at an informational surface from search, from social, from email, and from within the site. Design the entry points for all four: the article page must be legible to a first-time visitor from search (no assumed context) AND to a returning reader from email (contextual familiarity). The headline and deck carry the first-time visitor; internal context carries the returning reader.

## Canonical aesthetic reference tier (study subjects, not prescriptive tools)

For grounding creative-direction on an informational surface, study how these publications handle reading legibility and typographic hierarchy: The Elements of Typographic Style (Bringhurst) for line length, leading, and scale principles; Stripe's blog for code-adjacent editorial clarity; The Pudding for narrative + visualization integration. Internalize the structural philosophy — typographic hierarchy, reading pattern calibration, grid discipline — not the surface treatment.

## Anti-patterns to refuse

- **Line length outside 45–75 characters.** Full-width text blocks on wide viewports produce line lengths that break reading rhythm. Constrain the content column; don't let text fill the viewport.
- **Heading hierarchy that is visually ambiguous.** If H2 and H3 look similar, the reader navigating by scan cannot distinguish them. Increase scale contrast or use a different weight.
- **"What's next" zone that tries to do everything.** A single zone with four equal-weight categories creates visual confusion and serves no reader intent clearly. Prioritize; pick the one or two categories most aligned with the reader's post-read intent for this content type.
- **No estimated reading time on long-form content.** A reader who does not know whether they are committing to 3 minutes or 20 minutes cannot make an informed decision about whether to start. State it.
- **Typography as decoration.** Large display type, colored headings, or irregular spacing that serves visual variety rather than reading hierarchy is decoration masquerading as typography. Every typographic decision must be traceable to a reading-legibility or hierarchy goal.
