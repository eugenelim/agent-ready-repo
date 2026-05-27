---
name: architect-design
description: Use when the user is framing a problem, weighing a technical choice, or designing a system or integration without a diagram as the headline ask. Triggers on "how should we", "we need to", "what's the right way to build X", tech-selection, integration design, NFR trade-offs. Produces a Google-style design doc (TL;DR, context, goals/non-goals, proposal, alternatives, risks, rollout, open questions), 2-5 pages, with Mermaid inline. Do NOT use when the ask is a diagram (use `architect-diagram`) or a critique (use `architect-review`).
---

# Skill: architect-design

Produce a Google-style design doc that names the problem, proposes a solution,
considers alternatives honestly, and surfaces the risks the proposer is least
keen to write down.

## When to invoke

Before drafting, confirm:

1. The ask is *design*, not *drawing* — if the user wants a picture more than
   a proposal, route to `architect-diagram` (if installed) or tell the user
   to invoke a diagramming skill directly.
2. There is a *real choice* to make. If only one option is on the table and
   the user just wants it written up, the artifact is a project brief, not a
   design doc. Say so and offer to write a shorter brief instead.
3. The *audience* is human — peers, a tech-lead, an architecture review.
   Design docs are read; they are not configuration.

If any check fails, push back rather than proceeding.

## Procedure

1. **Frame the problem.** Ask only what is *genuinely missing* — what we're
   building, who's affected, why now, what would count as success. Skip
   anything the user already said. Three to five questions max; if the
   user can't answer one, write the doc with the gap flagged as an open
   question rather than blocking on it.

2. **Draft inline.** Use the skeleton in `assets/design-doc.md` (load it
   when you start the draft). Sections in order: TL;DR (≤3 sentences),
   Context, Goals and Non-goals, Proposal, Alternatives Considered, Risks,
   Rollout, Open Questions. Embed Mermaid diagrams where structural
   reasoning genuinely needs a picture — not as decoration.

3. **Self-check against the rubric** in `references/design-doc-rubric.md`.
   Walk it line by line; fix what fails before showing the draft.
   Common failures:
   - Non-goals empty or unconvincing → load `references/alternatives.md`
     for the *what's not in scope* pattern.
   - Alternatives are strawmen → load `references/alternatives.md` and
     redraft until each alternative could have been chosen by a
     reasonable engineer.
   - No cross-cutting concerns named → load `references/nfr-checklist.md`
     and add the ones that matter.

4. **Offer to save.** Scan the working directory for an obvious home —
   `docs/design/`, `design/`, `architecture/`, or `docs/`. Suggest a
   kebab-case filename based on the doc's title. If nothing fits, ask
   the user where it should go. Saving is an offer, never automatic.

5. **Decision-moment prompt.** If the doc captures one or more discrete
   decisions (technology choice, structural commitment, interface
   contract), end with one sentence: *"<N> decision(s) here look
   ADR-worthy — capture them with your ADR skill?"* Don't couple to a
   specific ADR implementation; let the user route.

## Anti-patterns to refuse

- **"Just write the proposal section."** A proposal without context,
  non-goals, or alternatives is advocacy, not a design doc. Either write
  the full doc or write a project brief — name which.
- **Pre-selected alternative pretending to be a choice.** If the user has
  already decided and wants the doc to look like deliberation, that is an
  ADR with a Context section, not a design doc. Push back.
- **Embedding diagrams the proposal doesn't reason about.** Every Mermaid
  block earns its place by being referenced from the prose. Decorative
  diagrams rot first.
- **Skipping risks because the proposal is "obvious".** No proposal is
  obvious to the person who will operate it in two years. Name at least
  three risks even when the proposer is bored of you.
