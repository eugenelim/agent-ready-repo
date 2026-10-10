---
type: information-architecture
slug: guides-lifecycle
date: 2026-10-09
surface-genre: documentation
surface: responsive-web
governed_by:
  - docs/design/journeys/docs-guides-champion-current-state.md
  - docs/design/journeys/team-orientation-future-state.md
  - docs/design/screens/team-orientation-canvas.md
---

# Information architecture: the lifecycle across the guides

A reader should know which part of the software lifecycle their work is in,
and reach the guide for it, without first knowing which pack to pick. This doc
places one lifecycle model in three layers of the guide set: a strip on the
index, a "where this fits" marker on each pack page, and the full swimlane in
the three-loops explanation.

## Frame

**Surface.** The `guides/` tree as published: `guides/README.md` (the index),
the 22 pack folders, and `guides/_shared/`. About 243 pages, so the site is
hub-and-spoke: the index and each pack README are hubs.

**Job.** Turn "I don't know which pack my problem is in" into "my work is in
*Shape it*, and this is the path for it."

**Audience.** Three arrivals, all named in the champion journey:

- **The champion** lands on the index and needs something to hand a team.
- **The cold arrival** lands on a pack page from search or a colleague's link,
  with no context.
- **The returning reader** comes back for one detail: which skill, which gate,
  what comes next.

**Success metric.** From any pack README, a reader reaches the ordered path for
their lane in at most two links, and can name the human decision that ends that
lane. Proxy we can check in review: every lane-owning pack README carries a marker
that links to the full flow, and every P-path heading names its stage.

## The model, in the reader's words

Four lanes, each ending on a decision a person makes. The words reuse the
operating-model canvas, so the marketing page and the guides say the same
thing in different forms.

| Lane | What happens | Ends when | Ordered path |
| --- | --- | --- | --- |
| **Decide what to build** | Evidence, then a strategic choice | You commit to an outcome | P2b steps 1–2 |
| **Shape it** | Frame, de-risk, and break down the bet; design the experience, system, and contracts | You ratify the outcome and hand it to build | P2, or P2b steps 3–4 |
| **Build it** | Intake, spec and plan, the work loop | You merge the pull request | P3 |
| **Ship it** | Deploy off production, validate, report | You ratify the production ship | P5 |

Three things sit outside the lanes on purpose:

- **P1 · Adopt** comes before any lane.
- **P4 · Decide together** cuts across *Shape it* and *Build it*. Decisions get
  recorded wherever they are made.
- **P6 · Extend** is about the catalogue, not one piece of work.

Gate codes (G0, G1.5, G2, G3, G4, G5) never appear in the strip or the markers.
Agents print them, so the deep layer carries a key that translates each one.

## Ranked content

1. **Primary — the lane the reader is in, and its path.** This is the answer to
   the highest-opportunity pain.
2. **Secondary — what you receive and what you hand on.** The named artifact
   at each lane boundary, and who decides there.
3. **Tertiary — which skill and pack act at each step, and the gate codes.**
   Needed for reference, but noise on first contact.

## Disclosure stages

| Stage | Where | Shows | Hides |
| --- | --- | --- | --- |
| 1. Glance | `guides/README.md`, directly under "Start here" | The four lanes as one line of text, each linking to its path | Skills, packs, gates |
| 2. Locate | Each pack README, near the top | Which lane(s) the pack serves, what it receives, what it hands on, one link up | Other packs' detail |
| 3. Detail | `guides/_shared/explanation/the-three-loops.md` | The full swimlane, a step → skill → pack → artifact → decider table, and the gate key | Nothing |

Stage 1 and 2 are plain Markdown text, not images. They must render the same
on github.com, the docs site, and a chat paste. Only stage 3 uses a diagram,
and its table is the text alternative when the diagram fails to render.

## Navigation shape

No new page and no new sidebar group. The model attaches to hubs that already
exist:

- **Index.** The strip sits between "Start here" and "Walk a pack". Each P-path
  heading gains a one-line lane tag, so the strip and the paths visibly match.
- **Pack READMEs.** One short "Where this fits" section on the eight packs that
  own a lane: `desk-research`, `product-strategy`, `product-engineering`,
  `experience-design`, `architect`, `contracts`, `core`, and
  `release-engineering`. Packs used in any lane — the trackers, `converters`,
  `code-intelligence`, `frontend-engineering`, `iac-terraform`,
  `governance-extras`, `product-documentation` — are listed once, with the
  moment each is reached for, on the three-loops page. A marker on each of them
  would force a lane that isn't true.
- **Three-loops explanation.** Its ASCII handoff chain is replaced by the full
  swimlane. It already owns "the company operating model", so the detail layer
  is a revision of that page, not a sibling of it.

Grouping the sidebar by job is a separate, larger change. It alters route
identity for 21 groups in `site.toml [[guide_groups]]` and needs its own
migration argument. This design works with the sidebar as it is.

## Wayfinding

Every pack page answers three questions with the marker:

- **Where am I?** "This pack works in *Shape it*."
- **Where can I go?** "You receive a framed intent from Product Engineering.
  You hand a reviewed screen set to the build loop."
- **How do I get back?** "See the whole lifecycle" links to the index strip.

The guidebooks already state hand-offs at both ends. The marker generalizes
that rule to every pack, using the same "receive / hand on" wording.

## States

- **Default.** Strip, markers, and swimlane all present.
- **Cold arrival.** A reader lands on a pack page from search. The marker is the
  recovery path: it names the lane and links up to the index.
- **Partial install.** A reader has only some packs. The strip still reads in
  order; each lane links to its path, and each path already lists what it needs
  first. Nothing hides a lane because a pack is missing.
- **Diagram fails to render.** The step table in stage 3 carries the same
  content.
- **Narrow viewport.** The strip is one wrapping line of text, so it reflows
  without losing order.

## The detail-layer swimlane

The swimlane follows the `discovery-loop` gate table, not a blend of routes.
These are the points it must keep, each checked against pack source:

1. **Three routes through *Shape it*.** The short route (`frame-intent` →
   `de-risk-intent` → `decompose-intent`) is the default. The longer route is
   the six-step shaping sequence (`frame-situation`, `identify-opportunities`,
   `diverge-solutions`, `place-bet`, `map-capabilities`). The supervised
   `discovery-loop` is the full sequence. The first two are dashed bypasses that
   join at the commit-to-build decision.
2. **Every gate.** G0, G1 (automatic unless a risk trigger fires), G1.5, G2, G3,
   G4 (merge, then release), and G5.
3. **The convergence lenses as the loop runs them.** Product is
   `decompose-intent`. Experience is `journey-mapping`, `service-blueprint`,
   `user-flow`, and `ux-writing`. Architecture is `architect-design` and
   `architect-diagram`. Contracts are `api-contract` and `event-contract`. The
   threat and reliability reviewers reconcile them before G2.
   `map-capabilities` is not a lens.
4. **`desk-research` and `product-strategy`** upstream, as optional input.
5. **Build intake through `work-intake`**, with the direct-light shortcut for
   small, low-risk changes that skips the spec.
6. **`define-slo` as optional**, and `close-work` for any finished or abandoned
   work rather than only shipped work.
7. **One gate vocabulary.** A key maps each code to the plain question it asks,
   and to Product Engineering's own gate names where one exists: Approve the
   intent (G0), Approve the decision brief (G2), Commit to build (G3).
8. **ADRs and RFCs come from any lane.** They are not a step after G2.

The diagram is Mermaid, follows the rules in `docs/AGENTS.md`, and is checked
in the docs-site renderer before merge. Its pack table is the text alternative.

## Voice

The strip, the markers, and the new three-loops sections are written as a
teacher talking to a new teammate. That means second person, plain verbs, and
varied sentence length. It also means no stacked labels, no gate codes in the
strip, and no claim a reader can't check against the pack.

## Handoff to authoring

`author-product-docs` builds three changes from this doc:

1. The strip and lane tags in `guides/README.md`.
2. The "Where this fits" marker in the eight lane-owning pack READMEs.
3. The swimlane, step table, and gate key in
   `guides/_shared/explanation/the-three-loops.md`.
