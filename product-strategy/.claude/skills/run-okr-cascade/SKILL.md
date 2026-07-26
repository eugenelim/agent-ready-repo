---
name: run-okr-cascade
description: Use when a strategist needs to cascade company OKRs to team level and identify strategic gaps for the product-engineering shaping queue. Triggers on "run an OKR cascade", "I need to cascade company OKRs", "align team OKRs to company goals", "identify OKR gaps", "what are we missing to hit our objectives". Produces okr-cascade.md and workspace.toml shaping-queue entries. Do NOT use for per-feature goal-setting — cascade is org-wide alignment, not product backlog prioritization.
---

# Skill: run-okr-cascade

Produces an **OKR cascade** — company Objectives and Key Results aligned to team-level OKRs, with strategic gaps identified and routed to the PE pack's shaping queue via `workspace.toml`. The cross-pack routing contract is documented in `references/cross-pack-routing.md`. See `references/agentbundle-layout.md` for artifact path.

## When to invoke

1. **Company OKRs exist or can be elicited** — either as an existing artifact in `docs/product/shaping/` or supplied by the strategist inline.
2. **You need gap identification for PE framing** — the primary output is the shaping-queue entries, not just the cascade document.
3. **No current OKR cascade exists for this cycle** — amend rather than restart.

## Procedure

1. **Elicit or read company OKRs.** Check `docs/product/shaping/` for an existing OKR artifact; if absent, elicit: "What are the company's top 3–5 Objectives this cycle, and the Key Results for each?" Document them verbatim — do not interpret or refine without the strategist's confirmation.
2. **Derive team-level OKRs.** For each company Objective, derive the corresponding team-level Objective and Key Results that roll up to it. The team-level KRs must be measurable at the team's scope. Flag any company Objective that has no credible team-level expression — that is a gap.
3. **Identify strategic gaps.** A gap is any company Objective or Key Result that has no current team-level owner, no credible delivery path, or a current-state vs. target delta that requires new strategic investment. Name each gap with a slug (kebab-case, one to four words).
4. **Commit `okr-cascade.md`.** Resolve the artifact path per `references/agentbundle-layout.md`. Write `okr-cascade.md` with frontmatter `type: okr-cascade` to the resolved path. Include: company OKRs, derived team OKRs per objective, and a gap registry (slug + description + which KR it is blocking).
5. **Resolve target initiative.** Read `workspace.toml` for `["ini-NNN"]` sections with `status = "active"`. If exactly one is active, use it. If multiple are active, list them and ask: "Which initiative should these OKR gaps be routed to?" Do not proceed until the user confirms.
6. **Append gap entries to workspace.toml.** For each named gap, append `{slug = "<gap-slug>", type = "strategy"}` to the active initiative's `["ini-NNN".shaping_queue].backlog` array. No `needs` field — no-dependency entries omit it. If `workspace.toml` is absent, surface: "workspace.toml not found — create it or supply the target initiative manually."
7. **Emit the PE-pack diagnostic if needed.** If `frame-situation` is not found in the installed skills, surface: "frame-situation not found — install PE pack to route OKR gaps into the shaping sequence."

## Anti-patterns

- **Cascading to features.** OKR cascade aligns the organization to strategic objectives; it does not produce a feature backlog. Feature-level goals belong in `frame-intent`, not here.
- **Skipping gap identification.** A cascade without gaps is a reporting exercise. The gaps are the deliverable — they become the shaping-queue entries the PE pack acts on.
- **Assuming a single initiative.** Always check `workspace.toml` for the active initiative count before appending. Appending to the wrong initiative produces routing errors that are hard to detect later.
