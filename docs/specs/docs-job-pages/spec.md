# Spec: docs-job-pages

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs-site-rail-shell`](../docs-site-rail-shell/spec.md), [`docs/design/direction/docs-site.md`](../../design/direction/docs-site.md), `guides/AGENTS.md` § Job pages
- **Brief:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** `Agent Rules`, `Testing Strategy` and `Acceptance Criteria`
> are contract; the rest is working material.

## Outcome

Every page a reader reaches from the docs sidebar meets one standard (`guides/AGENTS.md` § Job pages): it opens with what the reader can do, shows the packs it needs as pills under the title, gives each step as a lead-in, one command or prompt, and one sentence on what happens, and leaves flags, edge cases, and history to reference pages. Each pack guidebook becomes one job page whose steps are sections, so the sidebar never opens a walk at step 3. Each pack page follows one template.

## What Changes

- **Docs tab.** Set up a repository: Start a project, Connect your tracker. Decide what to build: Research a question, Understand the code, Analyse the market, Set direction and goals. Shape it: Shape an idea, Design the architecture, Design the experience, Design an API contract. Build it: Build a change, Fix a bug, Review a pull request, Build a page or component, Record a decision, Write the docs. Ship it: Release a change, Change infrastructure, Measure delivery. The four product-engineering, five experience-design, three product-strategy, four desk-research, and four core guidebook steps merge into their job pages; merged pages leave an `aliases:` redirect.
- **Operating model.** Title "Operating model"; one storyline from the four stages to where you decide.
- **Author and Catalogue System tabs.** Each page rewritten to the standard.
- **Pack pages.** Each `packs/<pack>/README.md` follows the template: name, one sentence, install, what your agent can do, skills, works with, questions, details. The H1 is the pack's `display_name`.
- **Page furniture.** A `uses:` frontmatter list renders as pack pills under the title; the grey line under the title is the page's outcome in one sentence, and the Intro has none.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User documentation | The change is the documentation | the pages above | this spec | built pages | link check clean |
| Authoring rule | The standard governs future pages | `guides/AGENTS.md` § Job pages | this spec | the section | present |
| Route continuity | Merged pages move | `aliases:` on absorbing pages | this spec | redirect stubs | every old URL resolves |
| Core release | `packs/core/README.md` changes | `packs/core/pack.toml`, plugin manifest, changelog | release | core patch version | roster core-release test passes |

## Agent Rules

### Always do

- Ground every command, skill name, and artifact path in the pack's source.
- Keep every pinned phrase that a test or lint requires on its page.

### Ask first

- Deleting a page that no job page absorbs.

### Never do

- Name an agent host outside the supported agents.
- Assume a pack is installed without showing it.

## Testing Strategy

- **Goal-based check** — build both sites; `validate_guides.py`; `lint-guide-titles.py`; guide and build-site pytest suites; web vitest; `make site-link-check`; a filler-word scan over the sidebar pages.
- **Visual / manual QA** — screenshots of one page per tab and one pack page.

## Acceptance Criteria

- [ ] **AC1 — Sidebar pages meet the standard.** Every page the four tabs list opens with a sentence on what the reader can do, has no "Use this when", "Prerequisites:", or "Result:" header block, and is 500 words or fewer, except reference pages.
- [ ] **AC2 — No mid-walk entry.** No sidebar link opens a page that shows a "Step N of M" position with N greater than 1.
- [ ] **AC3 — Pack pills.** Every sidebar page that needs a pack shows it as a pill linking to the pack's page.
- [ ] **AC4 — Pack template.** Every pack page has the sections Install, What your agent can do, Skills, Works with, Questions, and Details, and its H1 equals its `display_name`.
- [ ] **AC5 — Old URLs resolve.** Every merged page's URL redirects to the page that absorbed it, and `make site-link-check` is clean.
- [ ] **AC6 — Plain prose.** No sidebar page uses "surface", "canonical", "converge", "bounded", "durable", "load-bearing", "genuinely", "first-class", "seamless", "robust", "leverage", "Pillar", or "Conductor" outside a code span.
