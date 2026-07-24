---
name: run-okr-cascade
description: Use when a strategist needs to cascade company OKRs to team level, identify strategic gaps, and derive the causal metric tree that connects user behavior to outcomes. Triggers on "run an OKR cascade", "I need to cascade company OKRs to the team", "align team OKRs to company goals", "identify gaps in our OKR coverage", "what metrics causally predict our north-star". Produces okr-cascade.md and workspace.toml shaping-queue entries. Do NOT use for per-feature goal-setting — cascade is org-wide alignment, not product backlog prioritization.
---

# Skill: run-okr-cascade

Produces an **OKR cascade** — company Objectives and Key Results aligned to team-level OKRs, with strategic gaps identified, a causal metric tree derived, and gap entries routed to the PE pack's shaping queue via `workspace.toml`. The cross-pack routing contract is documented in `references/cross-pack-routing.md`. See `references/agentbundle-layout.md` for artifact path.

## When to invoke

1. **Company OKRs exist or can be elicited** — either as an existing artifact in `docs/product/shaping/` or supplied by the strategist inline.
2. **You need gap identification for PE framing** — the primary output is the shaping-queue entries, not just the cascade document.
3. **No current OKR cascade exists for this cycle** — amend rather than restart.

## Procedure

1. **Elicit or read company OKRs.** Check `docs/product/shaping/` for an existing OKR artifact; if absent, elicit: "What are the company's top 3–5 Objectives this cycle, and the Key Results for each?" Document them verbatim — do not interpret or refine without the strategist's confirmation.
2. **Derive team-level OKRs.** For each company Objective, derive the corresponding team-level Objective and Key Results that roll up to it. The team-level KRs must be measurable at the team's scope. Flag any company Objective that has no credible team-level expression — that is a gap.
3. **Identify strategic gaps.** A gap is any company Objective or Key Result that has no current team-level owner, no credible delivery path, or a current-state vs. target delta that requires new strategic investment. Name each gap with a slug (kebab-case, one to four words).
4. **Derive the causal metric tree.** From the OKR structure and gap analysis:
   - Name the **north-star metric** — the one outcome metric that captures value delivery for the most strategic Objective. It must be measurable, user-behavioral, and causally connected to the customer outcome (not an output metric like "features shipped").
   - Name **2–4 leading indicators** that causally predict the north-star. Each leading indicator must: (a) be earlier in the causal chain than the north-star, (b) connect to a specific OKR gap or Key Result, (c) be measurable at the team's scope. A leading indicator that cannot be traced to an OKR gap is not part of the causal tree — it is a candidate metric at best.
   - If no credible north-star can be derived, surface: "North-star metric unclear — the OKR structure does not name a user-behavioral outcome metric. Recommend specifying one before committing the cascade."
5. **Commit `okr-cascade.md`.** Resolve the artifact path per `references/agentbundle-layout.md`. Write `okr-cascade.md` with frontmatter `type: okr-cascade`. Include: company OKRs, derived team OKRs per objective, gap registry (slug + description + which KR it is blocking), and the causal metric tree (north-star + leading indicators with their OKR connections).
6. **Complete the strategy-to-experience section.** After committing okr-cascade.md, populate the Metric Tree field in the Digital Experience Contract if one exists in `docs/product/shaping/digital-experience-contract.md`. Surface the values regardless:
   - **Metric Tree**: the north-star metric and 2–4 leading indicators with their causal connections (from step 4). Format: north-star first, then each leading indicator with its causal connection and OKR gap link.
   If other Strategy fields are empty in the contract (Adoption Hypothesis, Value Loop, Differentiation), surface them as provisional entries derived from the OKR structure — marked `[provisional — derive from PRFAQ]` if the PRFAQ has not yet been run.
7. **Resolve target initiative.** Read `workspace.toml` for `["ini-NNN"]` sections with `status = "active"`. If exactly one is active, use it. If multiple are active, list them and ask: "Which initiative should these OKR gaps be routed to?" Do not proceed until the user confirms.
8. **Append gap entries to workspace.toml.** For each named gap, append `{slug = "<gap-slug>", type = "strategy"}` to the active initiative's `["ini-NNN".shaping_queue].backlog` array. If `workspace.toml` is absent, surface: "workspace.toml not found — create it or supply the target initiative manually."
9. **Emit the PE-pack diagnostic if needed.** If `frame-situation` is not found in the installed skills, surface: "frame-situation not found — install PE pack to route OKR gaps into the shaping sequence."

## Anti-patterns

- **Cascading to features.** OKR cascade aligns the organization to strategic objectives; it does not produce a feature backlog. Feature-level goals belong in `frame-intent`, not here.
- **Skipping gap identification.** A cascade without gaps is a reporting exercise. The gaps are the deliverable — they become the shaping-queue entries the PE pack acts on.
- **Assuming a single initiative.** Always check `workspace.toml` for the active initiative count before appending. Appending to the wrong initiative produces routing errors.
- **Metric-list-without-causal-tree.** A list of metrics without causal connections is not a metric tree. Naming "DAU, MAU, NPS, revenue, churn" without specifying which are leading indicators, which is the north-star, and what the causal chain is, produces measurement theater. Every metric in the tree must have its causal position named.
- **Polished-but-choice-free.** A cascade that produces equal-weight gap entries for every OKR without ranking them by strategic priority has made no choices. The gap entries should be ranked by OKR weight so the PE pack's shaping queue has a priority signal, not a flat list.
