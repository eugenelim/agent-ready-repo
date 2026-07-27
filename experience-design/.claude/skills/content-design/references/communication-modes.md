# Communication modes

Three modes govern how a surface should be written. The mode is set by the surface's
communication job, not its content type. Declare it in the artifact's `communication_mode:`
frontmatter field so downstream skills (tone-of-voice, conversion-design) apply the
correct editorial register.

## MODE 1 — product-copy

**Surfaces:** homepage, landing page, pack description, feature page, README opening,
product announcement, launch copy, calls to action, pack cards.

**Optimization target:** DESIRE + CLARITY + DIFFERENTIATION

**Information hierarchy — lead in this order:**
1. USER PROBLEM (the reader's pain or goal, in their words)
2. PRODUCT INSIGHT (why existing approaches fail)
3. OUTCOME (what changes for the reader)
4. PROOF (evidence the claim is true)
5. MECHANISM (how the product does it)
6. TECHNICAL DETAIL (only as much as the reader needs to believe)

**Anti-pattern to refuse:** FEATURE → FEATURE → FEATURE → ARCHITECTURE → EXPLANATION → SUMMARY.
The product should be understood before it is fully explained.

**Editorial discipline:** Apply anti-AI-smell criteria and the deletion pass before
closing (load `references/editorial-quality-gates.md`).

---

## MODE 2 — technical-editorial

**Surfaces:** technical deep dives, architecture articles, engineering guides, design
rationale, technical thought leadership, conceptual explanations, feature how-tos.

**Optimization target:** CLARITY + PRECISION + CREDIBILITY

This mode may be detailed. Do not artificially shorten content when detail genuinely
creates understanding. Still:
- Lead with the important idea, not the preamble
- Avoid generic introductory prose ("In today's rapidly evolving...")
- Use concrete examples
- Distinguish essential from optional detail
- Assume an intelligent reader

---

## MODE 3 — reference-documentation

**Surfaces:** APIs, CLI commands, configuration, installation, contracts, troubleshooting,
operational procedures.

**Optimization target:** ACCURACY + FINDABILITY + MINIMAL AMBIGUITY

This mode should not sound like marketing. Precision matters more than personality.
Structure for scanning: heading hierarchy, code blocks, tables over prose where appropriate.
