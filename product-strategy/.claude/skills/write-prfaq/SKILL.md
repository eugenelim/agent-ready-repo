---
name: write-prfaq
description: Use when a strategist needs to write the press release before the product exists — the altitude-0 forcing function that surfaces what the product must be and who must adopt it before any engineering begins. Triggers on "write a PRFAQ", "I need to write the press release before the product", "altitude-0 forcing function", "press release FAQ format", "Amazon PRFAQ", "what does first success look like for this product". Produces a committed prfaq.md. Do NOT use as a product spec or backlog — PRFAQ is a direction artifact, not an implementation contract. Do NOT use to write homepage copy or marketing materials — that belongs to copy-direction (experience-design pack).
---

# Skill: write-prfaq

Produces a **PRFAQ** — a press release written as if the product already exists, followed by a customer FAQ and an internal FAQ — using the Amazon PRFAQ format as the direction-setting convention. The press release forces specificity about who the customer is, what problem they have, and how the product solves it in their terms. See `references/agentbundle-layout.md` for artifact path.

## When to invoke

1. **A product concept exists but has not yet been committed to engineering** — PRFAQ is a pre-spec forcing function, not a post-spec documentation exercise.
2. **The strategist needs to align stakeholders on a direction** before engineering begins.
3. **No current PRFAQ exists for this product concept** — amend rather than duplicate.

## Procedure

1. **Elicit the product concept.** Ask: "Who is the customer? What is the painful problem they have today? What does the product do differently?" Confirm all three before drafting. A PRFAQ without a clear customer and problem produces a marketing document, not a forcing function.
2. **Author the press release.** Structure: (a) Headline — product name and the customer benefit in one sentence; (b) Sub-headline — the key detail the headline compressed; (c) Problem — the customer's current pain in their words, not industry jargon; (d) Solution — what the product does and why it is better than existing alternatives; (e) Call to action — what the customer does next; (f) Leadership quote — one sentence that names the strategic rationale, attributed to a role (not a placeholder name).
3. **Derive the adoption hypothesis.** From the solution definition, name: (a) **First-success event** — the one action the customer takes that proves first value was delivered; (b) **Repeat-value behavior** — what brings the customer back after first success. These must be behavioral and observable, not attitudinal. If you cannot name a first-success event, the problem statement is too vague — revise step 1 before continuing.
4. **Author the internal FAQ.** Three to five questions the engineering, design, or business team must resolve before this product can ship: the riskiest assumption, the hardest technical challenge, the customer acquisition path, and the **success metric** — which must be traceable to the first-success event named in step 3. A success metric that is not traceable to a first-success event is a vanity metric.
5. **Author the customer FAQ.** Three to five questions a real customer would ask before adopting: pricing, switching cost, reliability, comparison to the alternative they already use. Answer each honestly, including trade-offs.
6. **Apply the quality bar.** Read the press release aloud: Is it jargon-free? Is the customer benefit specific and measurable? Would a non-technical reader understand the problem and solution? Is the first-success event observable — can you tell within one session whether it happened? If not, revise before committing.
7. **Complete the strategy-to-experience section.** After committing prfaq.md, summarize the 7 Strategy fields for the Digital Experience Contract. Populate each field in the contract if one exists in `docs/product/shaping/digital-experience-contract.md`; otherwise surface the field values as a standalone summary:
   - **Target User and Context**: from the press release customer definition (step 1 and press release Customer section)
   - **Diagnosis and Strategic Choices**: what is being addressed and what was ruled out (from the PRFAQ solution's differentiation and trade-offs)
   - **Adoption Hypothesis**: the first-success event + repeat-value behavior (from step 3)
   - **Value Loop**: how value compounds after first success (from step 3 repeat-value behavior)
   - **Metric Tree**: the success metric from the internal FAQ, expanded into a north-star + at least one leading indicator
   - **Differentiation**: the mechanism named in the leadership quote (from step 2f)
   - **Assumptions and Kill Criteria**: the riskiest assumption from the internal FAQ and what would falsify it
8. **Resolve the artifact path** following `references/agentbundle-layout.md`. Surface the path, then commit `prfaq.md` with frontmatter `type: prfaq`.

## Anti-patterns

- **PRFAQ as a spec.** The PRFAQ is not an implementation contract — it does not define API boundaries, architecture, or feature-level acceptance criteria. Those belong in `frame-intent` and downstream specs.
- **Jargon-filled problem statements.** The problem section must be written in the customer's words. "Lack of operational visibility into cross-functional dependencies" is not a customer problem; "I can't tell if my team's work is blocked by another team" is.
- **Leadership quote as a placeholder.** A "TBD" or "[CEO name]" quote defeats the purpose — the quote should force the author to articulate the strategic rationale clearly enough to attribute to a role.
- **Launch-as-adoption.** Naming "ship the product" or "launch to beta users" as the first-success event conflates delivery with adoption. First success is something the *customer* does, not something the team does.
- **Moat-without-mechanism.** A press release that claims competitive advantage without naming the mechanism — why this product is hard to replicate, what network effect or data advantage or proprietary capability makes it defensible — is a wish, not a strategy. Push until the mechanism is named.
