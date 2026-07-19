---
name: design-principles
description: Use when a design team needs shared, durable decision rules — converting journey-map insights and opportunity pains into 3–5 named principles that resolve design disputes and persist across sprints. Triggers on "what are our design principles", "how do we make design decisions consistently", "we keep relitigating the same tradeoffs", "write our design principles", "derive principles from this journey". Produces principles in the form [Imperative verb] + [what] + [why/for whom] with an arbitration test. Do NOT use to set visual direction (use `creative-direction`), to derive tokens or scales (use `design-system`), or to evaluate an existing screen (use `design-review`).
---

# Skill: design-principles

Converts journey-map peak moments and highest-opportunity pains into **3–5 named design principles** — decision rules that resolve disputes, survive sprint boundaries, and let every later screen point back to a principle rather than relitigating taste. The principles are **not brand values** (those belong in `creative-direction`) and **not interaction heuristics** (Nielsen's apply universally; these are specific to this product and this audience).

## When to invoke

Confirm all three before drafting:

1. **A journey map exists or can be elicited** — principles derived without user insight are editorial preferences, not design decisions. If no journey exists, offer to run `journey-mapping` first.
2. **The team is relitigating the same design decisions** — the signal is "we keep arguing about this" or "this looks good but I can't say why it's wrong." Principles stop that loop.
3. **The output will be used to make decisions, not decorate a presentation** — principles that no one applies in design review are not principles; they are posters. Confirm the team commits to using them in `design-review`.

## What a good principle looks like

Form: **[Imperative verb] + [what] + [why/for whom]**

- Too vague (unusable): "Be clear." — what does clarity mean for THIS product?
- Too specific (not a principle): "Use small body type." — that is a value/style rule, not a decision principle.
- Well-formed: "Surface the number the analyst already knows — reduce the cognitive step between their mental model and the screen." — Imperative verb (Surface), what (the number they know), why (reduce cognitive step for THIS persona).

**Arbitration test:** given two wireframes, can this principle distinguish between them? If both wireframes pass the principle, it is not specific enough to do work.

**Three well-formed examples (from RFC-0066 D3):**

1. *"Earn trust before asking for commitment"* — surfaces the principle that sign-up gates, paywalls, and data-collection prompts should follow demonstrated value, not precede it. Distinguishes a design that gates immediately (fails) from one that lets the user see value first (passes).
2. *"Make the expert fast, not just the novice safe"* — surfaces the principle that power users are first-class citizens. Distinguishes a design that buries expert actions behind safety guardrails (fails) from one that exposes them at appropriate depth (passes).
3. *"Surface the cost before the commitment"* — for any destructive or irreversible action, the consequence is visible before the trigger. Distinguishes a design that names consequences only in a post-action undo toast (fails) from one that makes the consequence visible in the affordance itself (passes).

## Procedure — NNGroup 4-step model

Map each step to its stage label before writing principles:

1. **Identify core product values → insight.** From the journey map's pains and highest-opportunity moments: what does this product owe its users? List 5–8 candidate values as raw statements ("users feel anxious during the upload wait"). These are observations, not principles yet.

2. **Articulate why each matters to users → user-grounded.** For each candidate, add a user clause: "...because they can't tell if progress is happening, and they leave before the upload finishes." This is the step that converts a preference into a principle: the "why for whom" clause.

3. **Surface known tradeoffs → arbitration-aware.** For each candidate, name the opposing pull it will lose to: "Speed vs. reassurance — if we optimize for speed alone, we skip the progress signal; this principle says we don't." This step is what makes a principle arbitrate rather than just aspire.

4. **Draft collaboratively, converge through critique → team-owned.** Generate candidate principles in draft form, then run each through the arbitration test with the team. A principle that everyone agrees is "nice" but that no one can use to reject a wireframe is not finished. Converge when each principle can distinguish between two real design options from your current problem space.

## Evidence-level carry-through

If the source journey map is marked `evidence-level: assumption-based`, derived principles are **hypotheses** — mark them as such in the principles doc:

> ⚠ Assumption-based: this principle is derived from an assumption-based journey map. Treat it as a testable hypothesis until validated by observational or survey-backed data.

An assumption-based principle is not a defect — it is honest about its epistemic status. The team should prioritize validating it through usability testing or user interviews.

## Chain position

**Consumes:** `journey-mapping` peak moments (step 5b) and highest-opportunity pains.

**Consumed by:**
- `creative-direction` — principles anchor aesthetic arbitration (which direction choice serves which principle)
- `information-architecture` — principles guide hierarchy decisions (what deserves prominence)
- `content-design` — principles shape narrative arc choices
- `design-review` — every finding must map to the principle it violates (mandatory procedure step per D5e)

## Output

A principles doc at `docs/design/principles/<slug>.md` with frontmatter `type: design-principles`. Each principle entry:

```markdown
## <Principle title>

> [Imperative verb] + [what] + [why/for whom]

**Arbitration test:** given two wireframes — one that [does X] and one that [does Y] — this principle favors the one that [resolution].

**Traces from:** journey stage <stage>, pain: "<verbatim pain statement>"
```

The doc ends with a `## Known tradeoffs` section naming what each principle loses to (the opposing pull that would override it), so the team can apply them without pretending they have no cost.

## Anti-patterns to refuse

- **Brand values masquerading as design principles.** "Be human." / "Be trustworthy." / "Be bold." are brand identity, not design-decision tools. They cannot distinguish between two wireframes. Route brand values to `creative-direction`.
- **Heuristics reprinted.** "Visibility of system status" is Nielsen heuristic 1. It is universal and not a principle derived for this product. Do not reprint it; reference it. Principles are specific to this product and audience.
- **More than 5 principles.** A set of 8 principles is a decoration, not a tool — the team won't hold 8 in working memory during a design review. Converge to 3–5, ranked by which ones will resolve the most disputes in this product.
- **Principles with no team commitment.** If the team will not use a principle in `design-review` to reject a finding that contradicts it, it is not a principle. Establish the commitment before writing the doc, not after.
