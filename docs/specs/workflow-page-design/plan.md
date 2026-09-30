# Plan: workflow-page-design

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** [`../docs-site-design-refresh/creative-direction.md`](../docs-site-design-refresh/creative-direction.md), `docs-site/src/content/docs/index.mdx`, `guides/core/how-to/start-or-remember-work.md`, `docs-site/src/styles/starlight.css`, `web/src/test/rendered-output.test.ts`, `web/src/test/e2e/docs-wayfinding.spec.ts`; no new component boundary.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> execution observations go in `notes/verification-ledger.md`.

## Approach

First rewrite the authoring convention and the representative Core source so
the content contract is clear without relying on styling. Then reorganize the
handwritten home page around two primary choices and add a home-scoped category
palette in the existing Starlight stylesheet. Update source-level and browser
tests to assert the new hierarchy, build the generated site, and hand the final
artifact to a real browser for the required inspection matrix. The riskiest
choice is categorical color inside a site whose global direction is
single-accent, so the palette stays confined to route orientation and never
replaces cobalt for actions or links.

## Constraints

- The existing docs creative direction remains authoritative. Its
  single-accent rule receives one narrow exception for redundant route-category
  cues; its typography, restraint, contrast, and focus rules stay intact.
- `guides/` and `docs-site/src/content/docs/index.mdx` are sources.
  `docs-site/src/content/docs/guides/**` is generated output.
- Product Engineering guides own shaping behavior; Core skills and guides own
  intake, delivery, approval, and state behavior.
- Git metadata is read-only in this environment. Base freshness is a named skip
  because the check force-fetches a remote-tracking ref.
- Design handoff is a named skip: no `[design]` section is configured.
- Frontend mode is **retrofit**. The aesthetic reference is the existing docs
  creative direction grounded in the user-supplied reference site;
  `documentation-design` supplies the documentation-genre routing.

## Construction tests

**Integration tests:** the existing rendered-output suite parses the generated
home and workflow page, checks route sets and content order, and resolves their
links.

**Manual verification:** inspect the built docs home and representative Core
page in both themes at 480×600, 480×900, 1024×600, and 1024×900. Pair every
at-rest capture with a scrolled capture or an explicit `page-scrollable: no`
record. Record navigation, overflow, focus, accessibility, console, and layout
observations. This Codex session has no browser runtime, so the browser step
uses the repository's established `.context/` handoff to a runtime that exposes
headless Chromium.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Public task chooser | T2, T3 | Rendered-output and Playwright assertions | Built home and browser inspection |
| Core workflow page | T1, T3 | Guide linters and generated HTML assertions | Built page and browser inspection |
| Workflow-page convention | T1 | Maintainer-guide diff and documentation review | Convention remains scoped and points to the representative page |
| Scoped palette direction | T2 | Theme tokens, contrast calculation, browser checks | Both themes pass contrast and layout gates |
| Regression evidence | T3, T4 | Passing automated suites and verification ledger | Work-loop gates and review are clean |

## Design (LLD)

### Design decisions

Owned by: T1, T2

- The homepage decision is binary at the first level: **Shape an idea** when
  the product problem or outcome is open; **Build a known change** when the
  desired change is known. Bug, architecture, research, release, adaptation,
  setup, and reference routes remain lower-level choices.
- The workflow convention specifies answers and order, not seven headings. A
  page can use prose, a short list, a table, or selective labels when that form
  makes the operation easiest to scan.
- The Core page keeps its stable route but changes its visible title. Remember
  and resume behavior remains discoverable in deeper state/reference material,
  not in the main promise.
- A restrained four-category palette may mark route groups on orientation
  surfaces: build (blue), shape (violet), investigate (teal), operate (amber).
  Titles and group labels carry the category name, so color is redundant.

### Component / module decomposition

Owned by: T1, T2

- `index.mdx` uses existing `LinkCard` and `CardGrid` components. Wrapper
  classes express route prominence and category; no generic component or API
  is added.
- `starlight.css` defines semantic route tokens for light and dark themes and
  scopes their use beneath the docs-home route wrappers. Existing global
  Starlight slots remain cobalt.
- The Core guide uses portable Markdown constructs already supported by the
  guide pipeline. It adds no page-specific component dependency.

### State & control flow

Owned by: T1, T2, T3

The home page sends a reader into one of two flows:

1. An open product question enters Product Engineering: frame the intent,
   explore options when direction is open, de-risk the riskiest assumption,
   decompose a buildable slice, and obtain human commitment.
2. A known change enters Core: understand the request and repository state,
   choose the shortest safe route, then build, check, review, and stop for the
   human merge decision. Durable work may pause for brief, spec, or plan
   approval first.

The Product Engineering flow hands a committed feature-level result to the
same Core entry rather than bypassing Core's gates.

No new asynchronous component is introduced. The applicable static-surface
states are:

| State | Treatment |
| --- | --- |
| content | The two primary routes, supporting groups, and workflow narrative render without client-side data. |
| long-content | The Core page keeps a table of contents and places the operational path before deeper reference. |
| high-zoom | Text reflows and navigation remains operable without horizontal body overflow. |
| reduced-motion | The slice adds no required animation and preserves the site's reduced-motion behavior. |
| keyboard-only | Both primary routes and guide navigation remain reachable with visible focus. |

Loading, empty, error, partial, offline, and permission states are inapplicable
because this slice adds no data request, mutation, gated view, or custom
interactive component. Existing Starlight search and navigation states are not
changed.

### Behavior & rules

Owned by: T1

The Core opening uses this order:

1. outcome title and one-sentence promise;
2. one natural-language starter prompt;
3. a three-step narrative spine;
4. the Product Engineering fork and human commitment boundary;
5. a concrete route/result example;
6. completion signal and next action;
7. deeper state, invocation, and routing reference.

The page names exact artifacts only where current behavior creates them. It
does not claim that immediate work creates a workspace entry.

### Quality attributes (NFRs)

Owned by: T2, T3, T4

- The first decision and both primary routes fit at rest at 1024×900.
- The home and workflow pages have no horizontal body overflow at 375×812.
- Category text/fill pairs meet 4.5:1 contrast in both themes; focus treatment
  retains the existing 2px and 3:1 floor.
- Motion remains within the existing reduced-motion rules; this slice adds no
  required animation.

## Tasks

### T1: Rewrite the workflow contract and representative Core page

**Depends on:** none

**Tests:**
- Run the four guide linters against the edited public guide.
- Add or update a rendered-output assertion that the built page preserves the
  current route and places its prompt, three-step account, shaping fork,
  completion signal, and next action before deep reference material. Covers
  AC-0003, AC-0004, AC-0005, AC-0006, AC-0009, and AC-0010.

**Approach:** Replace the seven-label opening with the narrative spine in the
LLD. Rewrite the maintainer convention as an answer-based pattern. Keep route
and runtime facts aligned with the Product Engineering and Core sources.

**Done when:** the source page and convention satisfy the corresponding
acceptance criteria without changing another workflow page.

### T2: Recompose the docs home and scoped category palette

**Depends on:** T1

**Tests:**
- Update rendered-output assertions for exactly two primary route cards and
  the unchanged complete task-route set. Covers AC-0001 and AC-0002.
- Compute WCAG contrast for every category text/fill pair in both themes.
  Covers AC-0007, AC-0008, and AC-0013.

**Approach:** Place the shape/build fork first, group supporting tasks by user
intent, and add semantic wrapper classes. Add route tokens and wrapper styles
to `starlight.css`; amend the creative direction with the scoped exception.

**Done when:** the built home exposes the two primary routes before all
supporting tasks and category styling never changes global link/action color.

### T3: Update regression and browser contracts

**Depends on:** T1, T2

**Tests:**
- Run the rendered-output test that owns docs-home routes and content order.
- Run the Playwright wayfinding suite in both themes at its declared viewports.
- Run the rendered-site link checker after the complete site build.
  Covers AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007,
  AC-0008, AC-0009, AC-0013, AC-0014, and AC-0015.

**Approach:** Point the nested-guide browser case at the representative page,
assert both primary route cards and their order, and retain accessibility,
focus, breadcrumb, and overflow checks. Avoid brittle assertions on prose that
does not establish the contract.

**Done when:** the automated site tests fail for a missing route, inverted
primary hierarchy, broken link, inaccessible focus, or narrow overflow and
pass on the built design.

### T4: Verify and review the built slice

**Depends on:** T3

**Tests:**
- Run the docs build, rendered-site link check, relevant documentation tests
  and linters, Ruff, and mypy.
- Inspect repository status to confirm no other workflow page or unrelated
  generated documentation changed.
- Complete the rendered-page inspection matrix and record observations in the
  verification ledger. Covers AC-0010, AC-0011, AC-0012, AC-0014, and
  AC-0015.

**Approach:** Build through the canonical sequence, send one bounded browser
handoff prompt through `.context/`, then run the work-loop's adversarial and
quality reviews over the final diff.

**Done when:** every acceptance criterion has recorded evidence, all warranted
reviews are clean, and the only remaining migration work is listed as a
follow-on.

## Rollout

This is a documentation-only change with no feature flag or runtime migration.
Rollback is a source revert. The stable Core URL prevents inbound-link churn.

## Risks

- Too many category colors could weaken the site's restrained visual language.
  Scoping them to orientation wrappers and retaining cobalt for interaction
  contains that risk.
- Shortening the guide could erase important routing or approval facts. The
  deeper reference remains linked and rendered assertions pin the essential
  route distinctions.
- A source-only review could miss layout defects. The browser matrix is a
  release gate rather than optional evidence.

## Changelog

- 2026-09-26: scope contract approved by the owner.
- 2026-09-26: implementation strategy approved by the owner.
