# `experience-design` — I want to… intent index

> **Reference** — look up which pack, skill, and guide to reach for by starting job.
>
> Read left to right: state what you want to achieve, and follow the row to the
> right skill. **Chains** span multiple skills in sequence — each skill's output
> feeds the next; run them in the order listed. **Out-of-scope** rows are included
> explicitly so you know where *not* to reach and what to use instead.

---

## Set up visual identity and brand direction

| I want to… | Pack | Skill | Guide |
|---|---|---|---|
| Name the look and feel — converge a vague vibe into ranked, grounded goals | experience-design | `creative-direction` | [Design system chain](../how-to/design-system-chain.md) |
| Name our marketing copy voice for a specific surface | experience-design | `copy-direction` | [The three-way copy boundary](../how-to/copy-layer-boundary.md) |
| Define our brand voice across all surfaces (formal vs. casual, tone rules) | experience-design | `tone-of-voice` | [The three-way copy boundary](../how-to/copy-layer-boundary.md) |
| Derive a token taxonomy — name tokens by semantic role and organize scales | experience-design | `design-token-taxonomy` | [Design system chain](../how-to/design-system-chain.md) |
| Apply a token foundation to our design system — semantic color, typography, spacing | experience-design | `design-system-foundations` | [Design system chain](../how-to/design-system-chain.md) |
| **Chain:** Full design-system — aesthetic direction → token taxonomy → working foundation | experience-design | `creative-direction` → `design-token-taxonomy` → `design-system-foundations` | [Design system chain](../how-to/design-system-chain.md) |

---

## Discover and define the experience

| I want to… | Pack | Skill | Guide |
|---|---|---|---|
| Map a customer journey — stages, touchpoints, pain points, opportunities | experience-design | `journey-mapping` | [Thread a feature from journey to screens](../how-to/author-design-intent.md) |
| Map an internal process — as-is and to-be swimlanes, no customer-facing layer | experience-design | `process-mapping` | [The skills and the quality floor](experience-design.md) |
| Derive design principles from journey insights and product values | experience-design | `design-principles` | [Thread a feature from journey to screens](../how-to/author-design-intent.md) |
| Derive the screen flow and per-screen briefs from a journey map | experience-design | `user-flow` | [Thread a feature from journey to screens](../how-to/author-design-intent.md) |
| Blueprint the services behind the screens — frontstage, backstage, support | experience-design | `service-blueprint` | [Thread a feature from journey to screens](../how-to/author-design-intent.md) |
| **Chain:** Full design-intent thread — journey → screen flow → service blueprint | experience-design | `journey-mapping` → `user-flow` → `service-blueprint` | [Thread a feature from journey to screens](../how-to/author-design-intent.md) |

---

## Design screens by surface genre

Declare the surface genre in the per-screen brief's `surface-genre:` field; the
right skill applies genre-appropriate methodology for that genre.

| I want to… | Pack | Skill | Guide |
|---|---|---|---|
| Design a marketing or landing page — above-fold conversion surface | experience-design | `conversion-design` | [Page archetypes: when to use which](../how-to/page-archetypes.md) |
| Design a dashboard, KPI view, or monitoring screen | experience-design | `analytical-design` | [The skills and the quality floor](experience-design.md) |
| Design a marketplace — listing grid, filters, buying flow | experience-design | `marketplace-design` | [The skills and the quality floor](experience-design.md) |
| Design a documentation site or help centre | experience-design | `documentation-design` | [The skills and the quality floor](experience-design.md) |
| Design an article, editorial, or long-form content page | experience-design | `informational-design` | [The skills and the quality floor](experience-design.md) |
| Design a collaborative workspace, agentic UI, or task management surface | experience-design | `workspace-design` | [The skills and the quality floor](experience-design.md) |

---

## Screen craft — structure, behavior, and copy

| I want to… | Pack | Skill | Guide |
|---|---|---|---|
| Structure a screen's information hierarchy — reading flow, progressive disclosure | experience-design | `information-architecture` | [Page archetypes: when to use which](../how-to/page-archetypes.md) |
| Design how a screen behaves — feedback loops, state machines, motion | experience-design | `interaction-design` | [The skills and the quality floor](experience-design.md) |
| Write the copy for a screen — labels, CTAs, error messages, empty states | experience-design | `content-design` | [The three-way copy boundary](../how-to/copy-layer-boundary.md) |

---

## Review and quality-check

| I want to… | Pack | Skill | Guide |
|---|---|---|---|
| Critique a design in the current session — heuristic eval against the quality floor | experience-design | `design-review` | [Run a design review before the independent pass](../how-to/design-review.md) |
| Check all 18 quality-floor states across every screen | experience-design | `design-review` | [State coverage — the 18-state set](state-coverage.md) |
| Run an independent, forked-context design review of the full screen set | experience-design | `experience-reviewer` (agent) | [Run a design review before the independent pass](../how-to/design-review.md) |
| Run the cross-pack deterministic experience eval checker | experience-design | `check-xd-chain.py` (script) | [How to run the cross-pack experience eval](../how-to/run-cross-pack-eval.md) |

---

## Understand the chain and orient

| I want to… | Pack | Skill | Guide |
|---|---|---|---|
| Orient to the current design thread — see what artifacts exist and which skill to run next | experience-design | `experience-status` | [The skills and the quality floor](experience-design.md) |
| Decide which copy skill to run — copy-direction vs. content-design vs. tone-of-voice | experience-design | — | [The three-way copy boundary](../how-to/copy-layer-boundary.md) |
| Pick the right page archetype before designing a screen | experience-design | — | [Page archetypes: when to use which](../how-to/page-archetypes.md) |

---

## Discover, research, and set strategy (cross-pack)

These jobs involve skills from other packs. The chain row shows the full arc
across packs; each individual row covers a single starting job.

| I want to… | Pack | Skill | Guide |
|---|---|---|---|
| Set up a sustained market or domain research project | desk-research | `desk-research-project-start` | [Your first research project](../../desk-research/tutorials/your-first-research-project.md) |
| Synthesize existing stakeholder research into strategic themes | product-strategy | `synthesize-stakeholder-research` | [Set UX and content strategy](../../product-strategy/how-to/set-ux-and-content-strategy.md) |
| Write a PRFAQ — the press release before the product exists | product-strategy | `write-prfaq` | [Run your first SWOT](../../product-strategy/tutorials/run-your-first-swot.md) |
| Define the UX strategy before design begins | product-strategy | `define-ux-strategy` | [Set UX and content strategy](../../product-strategy/how-to/set-ux-and-content-strategy.md) |
| **Chain:** Full digital product thread — strategy → journey → screens → review | product-strategy + experience-design | `define-ux-strategy` → `journey-mapping` → `user-flow` → [surface skill] → `design-review` → `experience-reviewer` | [Thread a feature from journey to screens](../how-to/author-design-intent.md) |

---

## Out of scope — use the right pack

| I want to… | Resolution |
|---|---|
| Generate CI/CD pipelines or infrastructure scaffolding | Out of scope — use the **core** pack |
| Write application code | Out of scope — use the **core** or **product-engineering** pack |
| Build or wire a design into a frontend framework | Out of scope — use the **product-engineering** pack (`frontend-engineering` skill) |
| Conduct qualitative user interviews or usability testing | Out of scope — `desk-research` covers secondary research; primary research facilitation is not covered by any current pack |
| Run competitor keyword research or SEO analysis | Out of scope — use `desk-research` for secondary research; SEO tooling setup is not in scope |
| Build or maintain the agentbundle CLI or pack machinery | Out of scope — see the **core** pack and [AGENTS.local.md](../../../../AGENTS.local.md) |
