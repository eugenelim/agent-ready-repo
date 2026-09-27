# XD genre-router routing-classification evidence

Date: 2026-09-25

## Owner authorization

The scope owner stopped the live Claude activation experiment after its cost and harness-error rate became clear. On 2026-09-25, the owner explicitly directed this delivery to replace that experiment with a bounded cold-context Codex classification probe, run outside the work-loop and then used as external input to the loop.

This authorization replaces the delivery's Claude Tier-A before/after activation-rate gate. It does not claim that the replacement measures production skill activation.

## Accepted result

All 18 classifications matched the expected route with high confidence.

- Pre-fold accuracy: 9/9
- Post-fold accuracy: 9/9
- Post-fold genre coverage: 7/7
- Post-fold neighbor-boundary retention: 2/2
- Total classifier runs: 18
- Retries: 0
- Pre-fold resident description cost: 15,069 UTF-8 bytes across 20 shipped
  `SKILL.md` frontmatter `description` fields
- Post-fold resident description cost: 10,677 UTF-8 bytes across 14 shipped
  `SKILL.md` frontmatter `description` fields
- Post-fold resident description delta: -4,392 UTF-8 bytes

| Case | Expected pre | Actual pre | Expected post | Actual post |
| --- | --- | --- | --- | --- |
| C1 analytical reporting | `analytical-design` | `analytical-design` (high) | `information-architecture` | `information-architecture` (high) |
| C2 conversion pricing | `conversion-design` | `conversion-design` (high) | `information-architecture` | `information-architecture` (high) |
| C3 documentation site | `documentation-design` | `documentation-design` (high) | `information-architecture` | `information-architecture` (high) |
| C4 informational article | `informational-design` | `informational-design` (high) | `information-architecture` | `information-architecture` (high) |
| C5 marketplace catalogue | `marketplace-design` | `marketplace-design` (high) | `information-architecture` | `information-architecture` (high) |
| C6 sustained-work workspace | `workspace-design` | `workspace-design` (high) | `information-architecture` | `information-architecture` (high) |
| C7 general screen hierarchy | `information-architecture` | `information-architecture` (high) | `information-architecture` | `information-architecture` (high) |
| C8 component interaction | `interaction-design` | `interaction-design` (high) | `interaction-design` | `interaction-design` (high) |
| C9 design-system taxonomy | `design-system` | `design-system` (high) | `design-system` | `design-system` (high) |

## Method

Each case/world pair ran once in a separate Codex subagent with `fork_turns: "none"`. The classifier could read only the fixed input below, selected one route from descriptions alone, returned one JSON object, and did not edit files, browse, or spawn another agent. Pre-fold and post-fold used separate subagents. There were no retries.

The classifier rule was: choose the single candidate whose description most directly owns the request; choose `none` only when no candidate owns it.

The resident-description control was measured before the fold by reading each
`packs/experience-design/.apm/skills/*/SKILL.md` frontmatter `description`,
decoding its quoted scalar, measuring its UTF-8 bytes, and summing all 20
values. The result was 15,069 bytes. T9 repeats this method after the fold and
records the delta; it is a size control, not activation evidence.

## Fixed cases

- C1: Structure this reporting view — from status signal to diagnostic to action
- C2: Structure a pricing page so a qualified visitor understands the offer and can act
- C3: How do we structure a docs site that serves both tutorials and reference docs?
- C4: Design a long-form article template that stays readable through dense material
- C5: What's the right filter and facet architecture for a B2B software catalogue?
- C6: Design a collaborative workspace that preserves context across sessions and interruptions
- C7: Order the content on this settings screen by priority
- C8: Design the individual component interactions for the workspace toolbar
- C9: Derive the token taxonomy for the marketplace design system

## Shared neighboring candidates

- `interaction-design`: Use when someone asks how one screen or component should respond to actions, validate input, transition, recover, or feel in use. Produces behavioral and state specifications for the interaction. Use `information-architecture` for hierarchy, `user-flow` for cross-screen routes, and `creative-direction` for visual mood; `ux-writing` owns the strings shown in those states. Product strategy is upstream; framing and scoping the feature belongs to `frame-intent`; implementing the state machine, motion, or component code belongs to `frontend-engineering`. Triggers on "design how this search component validates, loads, and recovers", "map the state transitions inside this checkout form", "spec the feedback and motion for this async button".
- `design-system`: Use when an approved aesthetic direction exists and someone asks how to name and organize semantic tokens, spacing, type, or color scales. Produces a token taxonomy and rationale; it does not implement token values. Use `creative-direction` to establish the vibe, `information-architecture` for page hierarchy, and `design-review` to evaluate an existing surface. Product differentiation belongs to product strategy; framing a design-system initiative belongs to `frame-intent`; implementing tokens or components belongs to `frontend-engineering`. Triggers on "derive a semantic token taxonomy from this aesthetic direction", "organize our spacing, type, and color scales by role", "design the token system without choosing implementation values".
- `design-review`: Use when someone asks to critique an existing rendered screen, flow, or mockup for usability, quality-floor, clarity, and aesthetic-fit problems. Produces a severity-rated findings list grounded in the actual artifact. Use `creative-direction` to name a new visual direction, `information-architecture` to design hierarchy, and `design-system` to derive tokens. Reviewing product strategy or choosing a bet is upstream strategy work; framing the work belongs to `frame-intent`; reviewing code defects or implementation quality belongs to frontend engineering. Triggers on "review this checkout flow for usability problems", "critique this landing page mockup against our design principles", "what's wrong with this rendered dashboard".
- `creative-direction`: Use when someone says a digital surface should feel premium, calm, playful, or otherwise has a vibe but no shared visual direction. Also use when refining or amending an existing direction, or when inheriting it into a new section, component, or feature. Produces ranked aesthetic goals and, when due, a direction record grounded in referents and arbitration rules. Use `design-system` after the direction to derive tokens, `information-architecture` for page hierarchy, and `design-review` to critique existing work. Product positioning belongs to product strategy; framing or scoping the bet belongs to `frame-intent`; implementing colors, type, or components belongs to `frontend-engineering`.

## Pre-fold candidates

- `analytical-design`: Use when someone asks how a dashboard, report, or monitoring view should help a user understand data and act. Produces domain-model-first information architecture and a widget hierarchy for the analytical surface, not individual chart implementations. Use `interaction-design` for component behavior, `conversion-design` for marketing surfaces, and `workspace-design` for sustained-work tools. Metric and outcome strategy belongs upstream; shaping the analytics product belongs to `frame-intent`; implementing charts and data bindings belongs to frontend engineering. Triggers on "design a dashboard that helps on-call engineers spot and act on service degradation", "structure this sales report around the questions leaders need answered", "define the widget hierarchy for our monitoring view".
- `conversion-design`: Use when someone asks how to structure a landing page, product homepage, pricing page, or acquisition flow so a qualified visitor understands the offer and can act. Produces information architecture and structural specifications for a conversion surface. Use `content-design` for its message hierarchy and `copy-direction` for its copy goals; use `user-flow` and `interaction-design` for product UI. Go-to-market strategy belongs upstream; shaping the acquisition initiative belongs to `frame-intent`; writing final copy or building the page is not this skill's job. Triggers on "structure our pricing page to turn qualified visitors into trials", "design the conversion flow for our product homepage", "spec the hero and scroll story for this landing page".
- `documentation-design`: Use when someone asks how a documentation site, help center, API reference, or guide set should be organized so readers reach first value. Produces content-type, information-architecture, and navigation specifications that scale with the corpus. Use `conversion-design` for marketing surfaces and `informational-design` for editorial reading surfaces. Organization-level documentation strategy is upstream; shaping a docs-platform initiative belongs to product engineering; authoring the technical content or building the site and theme belongs elsewhere. Triggers on "design the navigation and content types for our API docs", "structure this help center so readers reach first value", "choose the right information architecture for our 250-page guide set".
- `informational-design`: Use when someone asks how an article, news page, editorial feature, or other long-form informational surface should support sustained reading. Produces typography, hierarchy, and reading-flow specifications for the surface. Use `documentation-design` for task/reference systems, `conversion-design` for acquisition pages, and `workspace-design` for tools. Editorial or product strategy is upstream; shaping a publishing-product bet belongs to product engineering; writing the article or building its template belongs to content authors and frontend engineering. Triggers on "design the reading experience for this long-form article", "structure this editorial page for sustained reading", "spec the typography and reading flow for our news feature".
- `marketplace-design`: Use when someone asks how a catalogue, listing grid, comparison view, detail page, or transaction bridge should help participants discover and choose in a marketplace. Produces information-architecture specifications for search, filters, listings, comparison, and the path to transaction. Use `conversion-design` for a single-product marketing page and `workspace-design` for an internal management tool. Marketplace strategy is upstream; framing and sizing the marketplace bet belongs to product engineering; implementing search, filters, transactions, or listing copy belongs elsewhere. Triggers on "design the filters and listing hierarchy for our contractor marketplace", "structure this catalogue for browse-first buyers", "spec the comparison and transaction path for our service listings".
- `workspace-design`: Use when someone asks how a productivity, collaboration, or agentic workspace should support sustained professional work across sessions. Produces a workspace-surface specification covering context persistence, collaboration state, ambient attention, interruptions, and session arcs. Use `analytical-design` for dashboards and monitoring views and `marketplace-design` for exchange surfaces. Product strategy is upstream; choosing the appetite and scope belongs to product engineering; implementing the workspace or writing its UI strings belongs to frontend engineering and `ux-writing`. Triggers on "design the session flow for our collaborative editor", "how should this agent workspace preserve context between sessions", "structure interruptions and handoffs in our team workspace".
- `information-architecture`: Use when someone asks what goes where on a screen or flow, in what order, and how users stay oriented. Produces an information-architecture and layout-reasoning document covering hierarchy, reading flow, progressive disclosure, navigation, and wayfinding. Use `creative-direction` for visual mood, `interaction-design` for within-screen behavior, `user-flow` for screen sequence, and `design-review` for critique. Product direction belongs to product strategy; scoping the feature belongs to `frame-intent`; writing markup and styles belongs to `frontend-engineering`. Triggers on "decide what goes where on this settings screen", "design the hierarchy and wayfinding for this flow", "organize this account settings content around the user's primary task".

The pre-fold candidate set was the seven entries above plus all four shared neighboring candidates.

## Post-fold candidate

`information-architecture`: Use when someone asks what goes where on a screen or flow, in what order, or how a genre-specific surface should help people understand, navigate, decide, or act. Produces information-architecture and layout specifications for general screens and flows plus analytical dashboards, reports, and monitoring; conversion landing, home, and pricing pages; documentation sites, help centers, and API references; informational articles, news, and editorial pages; marketplace catalogues, listings, comparison, and transaction paths; and sustained-work collaboration or agentic workspaces. Selects the genre from the brief and applies its method for hierarchy, reading flow, navigation, wayfinding, filters, comparison, context persistence, or action-oriented reporting. Use `interaction-design` for within-screen behavior and transactional journeys, `design-system` for tokens and components, `design-review` for critique, and `creative-direction` for visual mood. Strategy and scope stay upstream; final copy and implementation belong elsewhere.

The post-fold candidate set was this entry plus all four shared neighboring candidates.

## Shipped fold checks

The shipped `information-architecture` description is 1,004 UTF-8 bytes. It
therefore fits the 1,024-character cap, names all seven genre vocabularies, and
retains the four named neighboring boundaries: `interaction-design`,
`design-system`, `design-review`, and `creative-direction`.

The pooled routing-query corpus contains 71 positive queries and 67 negative
queries, with no query kept on both sides. It also retains the two exact
boundary negatives: `Design the individual component interactions for the
workspace toolbar` and
`Derive the token taxonomy for the marketplace design system`.

The post-fold resident-description total was measured with the same method as
the pre-fold 15,069-byte control: read each shipped
`packs/experience-design/.apm/skills/*/SKILL.md` frontmatter `description`,
decode the quoted scalar, measure its UTF-8 bytes, and sum the fields. The
post-fold tree ships 14 resident descriptions totaling 10,677 UTF-8 bytes, a
signed delta of -4,392 UTF-8 bytes from the 15,069-byte control.

## Delivery decision

Decision: `proceed`.

The owner accepts this bounded proxy as sufficient evidence to proceed with the
fold. The delivery makes no production-activation claim.

The remaining abort triggers are the approximately three-week window from
`Approved` elapsing before the fold lands, or an explicit owner decision to stop
the fold.
Neither permitted abort trigger applies: the owner approved proceeding, and
there is no explicit owner stop decision or elapsed appetite-window abort.
On abort, the six source skill directories remain and the cross-pack repair
ships alone: the `frontend-engineering` routing-table repair, the
`design-system-foundations` slug correction, that pack's patch version bump,
its regenerated marketplace entry, and its changelog entry. The deciding owner
is `eugenelim`.

## Limits

This is a classification proxy, not a Claude `Skill` activation event. Codex still had platform system context despite inheriting no dialogue turns. One sample per case/world does not establish broad recall, false-positive rates, repeated-sampling stability, or production activation behavior.

The tested post-fold description was 1,039 characters, so it was not the exact
shipped description under the contract's 1,024-character cap. The shipped
1,004-character description compresses it without changing the seven genre
routes or the four named neighboring boundaries. That compression was not
rerun through the classification proxy and does not claim a repeated probe.
