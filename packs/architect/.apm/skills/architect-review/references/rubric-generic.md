# Generic rubric — for `architect-review` (fallback)

Load when the artifact doesn't fit a named rubric — a hybrid doc, a
strategy memo, a one-pager, a comparison table, a non-Mermaid
diagram, or anything where the genre is unclear.

> Note: when in doubt, route to a specific rubric anyway. Generic
> reviews are weaker than rubric-anchored ones.

## First, name the genre

Before reviewing, decide what the artifact is *trying* to be:

- A proposal? Route to `rubric-design-doc.md`.
- A picture of a system? Route to one of the diagram rubrics.
- An ADR? This skill doesn't have an ADR rubric — name what's
  missing using the four ADR sections (Context, Decision,
  Consequences, Alternatives) and route the user to their ADR
  tooling.
- A strategy memo or one-pager? Use the generic checks below.
- An RFC? Same as proposal but with more context on
  alternatives — use the design-doc rubric and note any
  RFC-specific gaps in the executive summary.

## Generic checks (when no specific rubric fits)

### Audience and verdict

- [ ] **Who is the audience?** Named or implied. An artifact with no
      audience drifts.
- [ ] **What does the audience need to do** after reading? Decide
      something? Build something? Approve something? If unclear,
      that's the first finding.

### Claim shape

- [ ] **Top-line claim is one sentence,** at the top, and falsifiable.
      "We should adopt X" passes; "We are exploring X" fails as a
      claim.
- [ ] **Claim supported by evidence,** not just assertions. Where
      the evidence sits matters — close to the claim or in an
      appendix it references.

### Honesty

- [ ] **Trade-offs named.** Every proposal trades something away;
      if the artifact pretends otherwise, that's a finding.
- [ ] **Counter-arguments engaged.** Either rebutted on evidence or
      acknowledged as live concerns.
- [ ] **Risks acknowledged.** At least one is operational ("what
      goes wrong in production").

### Structure

- [ ] **Sections in a sensible order** for the audience.
- [ ] **No gratuitous repetition.** If section 4 restates section
      2, collapse them.
- [ ] **Length proportional to stakes.** A 12-page memo for a
      reversible $200/mo SaaS choice is over-engineered.

### Surface artifacts of LLM drafting

- [ ] **No "comprehensive" / "robust" / "leverage" / "ensure" / "in
      summary"** filler. These are LLM tells.
- [ ] **No three-bullet sections** where one would do.
- [ ] **No promises about future work** that aren't tied to a
      person or a date.

## Severity mapping (typical)

- 🟥 **Blocker** — No audience identifiable; top-line claim
  missing or contradicted by the body; major trade-off concealed.
- 🟧 **Major** — Counter-arguments ignored; structure obscures the
  ask; key risks unnamed.
- 🟨 **Minor** — Padding; weak section ordering; one filler
  paragraph.
- ⚪ **Nit** — Phrasing, headings, capitalization.
