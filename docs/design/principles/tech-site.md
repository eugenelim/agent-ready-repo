---
type: design-principles
slug: tech-site
status: active
applies_to:
  - web
  - docs-site
  - guides
  - catalogue
  - journeys
source_brief: docs/product/briefs/tech-site-completion.md
---

# Tech-site design principles

These principles govern design decisions across the marketing site,
documentation, published guides, catalogue, and journey pages. They complement
the existing surface-specific aesthetic directions: they arbitrate product
decisions without making the two renderers share a palette, component system,
or reading mode.

The source journeys are planned rather than observation-backed. Treat these
principles as testable hypotheses and revisit them when usability or adoption
evidence contradicts their arbitration tests.

## Lead with the user's job; reveal the system second

> Lead with the outcome the reader is trying to achieve, then reveal packs,
> loops, gates, and implementation structure only as they become useful.

**Arbitration test:** given one surface that opens with internal taxonomy and
one that opens with the reader's next meaningful outcome, this principle favors
the outcome-led surface; system vocabulary appears at the first decision where
it helps the reader act.

**Durable application:** journey semantic IDs, `globalGate`, and legacy gate
codes are machine contracts, not adopter copy. Decision navigation displays
human labels and derived order only. Public Now content describes released
outcomes, never the queue, plans, commits, or what the team is “working on.”

**Traces from:** `team-evaluates-and-adopts`, Stage 1 pain: “The README
explains what it does but not how to get started on a real project.”

## Put verifiable evidence beside every meaningful claim

> Pair claims with the concrete artifact, behavior, transcript, or destination
> that lets a skeptical technical reader verify them without taking marketing
> copy on trust.

**Arbitration test:** given one design that asks the reader to accept a broad
claim and one that places a real output, route, command, or bounded example next
to it, this principle favors the evidence-bearing design even when it is less
visually dramatic.

**Durable application:** `/now/` projects only reviewed Highlights from dated,
versioned changelog releases. Unreleased work cannot become public evidence;
AI-assisted drafting may use implementation diffs and verification evidence,
but deterministic site generation never invents or refreshes the copy.

**Traces from:** `team-evaluates-and-adopts`, Stage 3 pain: “Decision makers
want to see it on our code, not a toy example.”

## Keep readers oriented through stable names, paths, and destinations

> Use consistent destination language and preserve route identity so readers
> can move among marketing, catalogue, journeys, guides, and docs without
> rebuilding their mental map.

**Arbitration test:** given one design that renames, relocates, or presents the
same destination differently per surface and one that preserves its name,
route, and place in the information architecture, this principle favors the
stable map unless repository evidence proves the existing map is harmful.

**Durable application:** `site.toml` may share destination IDs, labels,
targets, groups, order, and target kind across renderers, but no presentation.
The approved replacement of public `/work/` with `/now/` is a deliberate
contract amendment, not permission for further route churn. Source ownership
may move only when compatibility preserves the public route.

**Traces from:** `team-evaluates-and-adopts`, Stage 2 pain: “The value was
visible but I can't reproduce it reliably yet because I'm self-discovering the
path.”

## Preserve each surface's reading mode within one product identity

> Keep marketing persuasive, journeys explanatory, and documentation optimized
> for sustained technical reading while using shared product vocabulary and
> orientation cues to make them recognizably one system.

**Arbitration test:** given one design that forces visual sameness across
renderers and one that preserves each surface's task-specific hierarchy while
sharing product destinations and terminology, this principle favors the
task-specific design. Shared identity never overrides readability,
accessibility, or framework-native affordances.

**Durable application:** the docs product-orientation band and Product mobile
disclosure remain distinct from Starlight's documentation header, Docs menu,
search, theme control, sidebar, breadcrumbs, table of contents, and pagination.
Marketing and docs do not share CSS, components, palettes, tokens, breakpoints,
focus implementation, disclosure state, or Starlight internals.

**Traces from:** `team-evaluates-and-adopts`, Stage 1 pain: “Every team member
will ask me what this is before they try it — I need a one-sentence answer.”

## Known tradeoffs

- **Job first** loses to required safety or governance context when hiding that
  context would misrepresent the action or its consequences.
- **Evidence beside claims** loses to privacy, security, or legibility when the
  real artifact cannot be shown safely; in that case the surface names the
  evidence boundary rather than substituting an invented example.
- **Stable orientation** loses to a demonstrated harmful route or vocabulary
  contract, but changing that contract requires explicit approval and a
  migration plan.
- **Distinct reading modes** loses to the accessibility quality floor and to
  product-wide terminology consistency; renderer-specific styling never
  excuses an inaccessible or contradictory outcome.

## Design-review commitment

Every future finding on these surfaces names the principle it violates or says
that it is a universal quality-floor finding instead. A proposed change that
cannot state which principle decides the tradeoff remains shaping work rather
than entering implementation.
