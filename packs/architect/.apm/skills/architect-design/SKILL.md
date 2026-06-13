---
name: architect-design
description: Use when the user is framing a problem, weighing a technical choice, or designing a system or integration without a diagram as the headline ask. Triggers on "how should we", "we need to", "what's the right way to build X", tech-selection, integration design, NFR trade-offs. Shapes a one-page concept first, then produces a Google-style design doc (TL;DR, context, goals/non-goals, proposal, alternatives, risks, rollout, open questions), 2-5 pages, with Mermaid inline, and converges it against review. Cloud well-architected by construction (AWS/Azure/GCP and primitives providers like Hetzner). Do NOT use when the ask is a diagram (use `architect-diagram`) or a critique (use `architect-review`).
---

# Skill: architect-design

Produce a Google-style design doc that names the problem, proposes a solution,
considers alternatives honestly, and surfaces the risks the proposer least wants
to write down — well-architected by construction, then converged against review.

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
   user can't answer one, flag it as an open question rather than blocking.

2. **Consult available knowledge surfaces.** Before shaping the concept,
   establish what enterprise context you can reach, and **state which surface
   you detected (or "none")** in the concept. **If** you detect an *internal*
   knowledge-retrieval surface this session (an enterprise-knowledge MCP tool,
   an internal CLI, an in-repo doc set — public web search does **not** count),
   load `references/knowledge-surfaces.md`, consult the design-relevant areas,
   and treat a single unconfirmed source as lower-confidence. **If not**, ask
   the user for the missing context and lower the confidence of any proposal
   that leaned on it — as you degrade when `research` is absent. **Either way,
   never fabricate** landscape/standards/in-flight facts.

3. **Shape the concept first (Stage 0).** Before the full doc, draft a
   ≤½-page concept from `assets/concept.md` — problem + constraints, 1–2
   candidate shapes, provider / provider-class, top 2–3 prioritized quality
   attributes (rank by business-importance × architectural-risk) — and
   **wait for the user to agree the shape**. This is *shaping* (context +
   constraints + the choice), not the refused "just write the proposal
   section" advocacy (see Anti-patterns). Make it well-architected **by
   construction**: a named provider → `references/well-architected-pillars.md`
   (it routes a Hetzner-class **primitives** provider to
   `references/cloud-primitives.md`'s capability gaps); a **local-first** start
   → `references/local-dev.md`; in all cases name the tradeoff / sensitivity
   points (`references/tradeoffs-and-sensitivity.md`). **No provider** → still
   produce the concept, forcing no provider/pillar scaffolding. **No shipped
   reference fits the domain** → the leading-edge method
   (`references/leading-edge-domains.md`): flag novelty, compose with `research`
   if present (degrade + lower confidence if absent), carry source + confidence.

4. **Draft inline.** Use the skeleton in `assets/design-doc.md` (load it
   when you start the draft). Sections in order: TL;DR (≤3 sentences),
   Context, Goals and Non-goals, Proposal, Alternatives Considered, Risks,
   Rollout, Open Questions. Embed Mermaid diagrams where structural
   reasoning genuinely needs a picture — not as decoration.

5. **Self-check against the rubric** in `references/design-doc-rubric.md`.
   Walk it line by line; fix what fails before showing the draft.
   Common failures:
   - Non-goals empty or unconvincing → load `references/alternatives.md`.
   - Alternatives are strawmen → load `references/alternatives.md` and
     redraft until each could have been chosen by a reasonable engineer.
   - No cross-cutting concerns named → load `references/nfr-checklist.md`.

6. **Converge against review.** After the full draft, run
   `references/convergence-loop.md`: obtain a review pass (from
   `architect-review` if installed, else your embedded rubric self-check),
   **auto-resolve mechanical findings without asking**, re-review, repeat to
   the pass cap / stasis escape. **Never auto-resolve a judgment finding** —
   surface the tradeoff / risk / low-confidence calls as explicit decisions.

7. **Offer to save.** Scan the working directory for an obvious home —
   `docs/design/`, `design/`, `architecture/`, or `docs/`. Suggest a
   kebab-case filename based on the doc's title. If nothing fits, ask
   the user where it should go. Saving is an offer, never automatic.

8. **Decision-moment prompt.** If the doc captures one or more discrete
   decisions (technology choice, structural commitment, interface
   contract), end with one sentence: *"<N> decision(s) here look
   ADR-worthy — capture them with your ADR skill?"* Don't couple to a
   specific ADR implementation; let the user route.

## Anti-patterns to refuse

- **"Just write the proposal section."** A proposal without context,
  non-goals, or alternatives is advocacy, not a design doc. Either write
  the full doc or write a project brief — name which.
- **Treating the Stage-0 concept as a stripped proposal.** The concept is
  *shaping* — context + constraints + the choice, the opposite of a proposal
  with those removed. Don't let it collapse into partial advocacy.
- **Pre-selected alternative pretending to be a choice.** If the user has
  already decided and wants the doc to look like deliberation, that is an
  ADR with a Context section, not a design doc. Push back.
- **Embedding diagrams the proposal doesn't reason about.** Every Mermaid
  block earns its place by being referenced from the prose. Decorative
  diagrams rot first.
- **Skipping risks because the proposal is "obvious".** No proposal is
  obvious to the person who will operate it in two years. Name at least
  three risks even when the proposer is bored of you.
