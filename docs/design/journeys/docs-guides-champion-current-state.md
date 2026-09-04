---
type: customer-journey
slug: docs-guides-champion-current-state
persona: adoption-champion
outcome: find-what-i-can-hand-to-my-team
surface: responsive-web
genre: documentation
state: current
evidence-level: assumption-based
evidence_note: >-
  Mixed by class. Reading behaviour in the repository file browser is
  observational, from the GitHub traffic window 2026-08-21 to 2026-09-03. The
  navigation structure, group ordering, and page content are verified against
  the live surface fetched 2026-09-04 and against site.toml and
  tools/build-site.py. Every emotion and pain is assumption-based. Frontmatter
  carries the honest floor; each stage carries its own tag.
updated: 2026-09-04
---

# Journey: the champion reaches the documentation guides

**Persona:** The same adoption champion as
[the marketing journey](marketing-champion-current-state.md), arriving at the
documentation surface in a different mode. On the marketing page they were
deciding whether to care. Here they have decided, and they need something they
can hand to other people: engineers who will use it, a platform team who will
install it, a budget holder who wants to know what it costs and what it refuses
to do.

**Outcome:** Find the thing they can hand to their team, and know it will work
without them standing next to it.

**Surface:** responsive-web, documentation genre. Sustained technical reading,
persistent navigation, and search are the native affordances. The fourth
tech-site principle requires this reading mode stay distinct from marketing's.

**Trigger:** A marketing link, a search result, or — most often — arriving from
somewhere other than the marketing page. In practice the champion often skips
this surface entirely and browses the repository file tree instead.

**End state:** The champion has a named, ordered thing to give somebody, with a
time cost and a stated first result, and does not have to invent the sequence
themselves.

---

## Stage 1: Discovering `[mixed]` — **negative peak**

| Row | Content |
|-----|---------|
| **Actions** | Looks for documentation. Finds no route from the marketing page except one link to a single how-to. Falls back to the site's global "Docs" link, or to a search engine, or gives up on the site and opens the repository file tree on github.com. |
| **Emotions** | Impatient, then resigned. Negative, and this is the deepest dip in the journey. The champion is not confused about what they want; they cannot find where it lives. |
| **Pains** | "I know there are guides. I can't get to them from the page that told me about them." Twenty-one of the twenty-two guide areas have no direct route from the marketing surface. The one marketing link that does exist points at a single `_shared` how-to, not at the guides index. |
| **Opportunities** | Give the marketing surface a real route into the documentation paths. The destination already exists and is good; only the route is missing. |

Observational component, and it is the strongest signal in the engagement: in the
14-day window one raw `SKILL.md` file in the repository file browser drew **12
unique readers**, a skill reference tree drew **7**, and `/tree/main/docs` drew
**6**. Twelve people chose an unrendered source file over anything this surface
offers. The published documentation drew no traffic this instrument can attribute
to it at all.

The failure is not that readers cross the seam badly. A material share never
reach the surface, and route around it to source.

## Stage 2: Orienting `[mixed]`

| Row | Content |
|-----|---------|
| **Actions** | Lands on the guides index. Reads the opening line: "Choose the pack and guide that matches your outcome." Looks at the left sidebar. Sees ten group labels — Get Started, Pack Catalogue, Foundation, Agent workflows, Engineering, Integrations, Content and design, Catalogue operations, Other, Guides. Tries to work out which one holds what they came for. |
| **Emotions** | Deflated in a familiar way. Negative. This is the same experience as the marketing page's pack menu, one level down: a taxonomy where a job was expected. |
| **Pains** | "The nav wants me to pick a pack. I don't know which pack my problem is in — that's why I'm reading the docs." All twenty-one guide areas sit inside a single sidebar group, placed last, beneath a group labelled "Other". The first sentence of the page asks the reader to choose a pack before it tells them anything. |
| **Opportunities** | Group the navigation by the reader's job rather than by our product structure, and lead the page with the ordered paths that are already written further down it. |

Verified in source, not inferred. `tools/build-site.py` generates
`docs-site/src/sidebar-config.json` — untracked and gitignored — creating one
group per pack `group` and then appending **all** guide content as a single
final group. `site.toml` records at line 122 why the order looks the way it
does: *"Undeclared in the pre-change hand tree — their pages published but never
appeared in navigation. Appended so no existing group moves."* The order is
declaration history.

## Stage 3: First value `[assumption-based]` — **highest positive peak**

| Row | Content |
|-----|---------|
| **Actions** | Scrolls past the opening line. Finds "Follow a path". Reads P1 through P6 — six ordered paths, each with a prerequisite, an audience, a time cost, a first value, and an end state that is a handoff rather than a document. Recognises P1 as the thing to give the platform team and P3 as the thing to give an engineer. |
| **Emotions** | Relieved, then slightly annoyed. Positive — this is the highest point of the whole two-surface experience. The annoyance is at how long it took to get here. |
| **Pains** | "This is what I needed. Why was it below a nav that told me to pick a pack?" The best content on either surface is below the fold on a page most readers never reach, under an opening sentence that describes it as a pack chooser. |
| **Opportunities** | This structure is the answer, not a candidate for one. Promote it: make it the opening of this page, and make its vocabulary the vocabulary of the marketing surface too. |

The P-paths deserve naming precisely because the design should not replace them:

| Path | Cost | First value | Ends at |
| --- | --- | --- | --- |
| P1 · Adopt the catalogue | ~1 h | `workspace status` answers what to work on next | a repository whose queues you can read |
| P2 · Shape what to build | ~3 h | one written intent naming an outcome and the bet behind it | Core intake |
| P3 · Build it | ~2 h | a spec and plan you approved before any code was written | a merged change, and the decision to merge is yours |
| P4 · Decide together | ~1.5 h | a circulated proposal with its alternatives written down | an accepted decision that outlives the people who made it |
| P5 · Ship and report | ~2 h | a deployed artifact validated in an environment like production | a human ratifying the production ship |
| P6 · Extend the catalogue | ~3 h | one skill of your own that your agent can run | a catalogue your organisation owns |

Not one of the six uses a gate code. P3 and P5 express the two human decisions
the marketing surface renders as `G4` and `G5`, in the reader's own terms. The
conformant vocabulary the redesign needs already exists here.

## Stage 4: Recurring reference `[assumption-based]`

| Row | Content |
|-----|---------|
| **Actions** | Comes back for a specific detail — which install route, which adapter supports commands, what a particular skill actually does. Uses search or the sidebar. Sometimes lands on a pack reference page instead of a guide. |
| **Emotions** | Functional. Neutral. Search works, and the reference content is accurate when found. |
| **Pains** | "I can never remember whether the thing I want is a guide or a pack page." Two parallel generated hierarchies — pack reference and guides — cover overlapping ground with no stated division of labour, and the sidebar presents them as peers. |
| **Opportunities** | State which hierarchy answers which kind of question, at the point where the reader chooses between them. |

## Stage 5: Mastery `[assumption-based]`

| Row | Content |
|-----|---------|
| **Actions** | Stops using the guides index and navigates straight to the page they want, or to the repository file. Sends colleagues direct links. |
| **Emotions** | Confident, and slightly proprietary. Positive. They have built a private map of a surface that did not give them one. |
| **Pains** | "I know where everything is now, and nobody I onboard does." Mastery here is a personal workaround, so it does not transfer. Each new cohort member repeats Stage 1 and Stage 2 in full. |
| **Opportunities** | Make the map the surface provides good enough that mastery is transferable. This is the cohort requirement: the champion's competence has to become the team's, and today it cannot. |

---

## Frontstage actions

- **Action:** look-for-documentation-from-marketing
- **Action:** fall-back-to-repository-file-tree
- **Action:** read-a-raw-skill-file
- **Action:** land-on-the-guides-index
- **Action:** read-the-opening-line
- **Action:** scan-the-sidebar-groups
- **Action:** choose-a-pack-group
- **Action:** find-the-follow-a-path-section
- **Action:** read-an-ordered-path
- **Action:** pick-a-path-for-someone-else
- **Action:** search-for-a-specific-detail
- **Action:** choose-between-guide-and-pack-page
- **Action:** send-a-colleague-a-direct-link

---

## Emotional arc

Lowest point: Stage 1 — resigned — because the champion cannot get from the
surface that advertised the guides to the guides, and routes around both to read
source. Stage 2 immediately repeats the marketing surface's taxonomy failure one
level down, so the dip is wide as well as deep.

Highest point: Stage 3, the ordered paths. It is the highest positive moment
across *both* surfaces, and it is below the fold on a page most readers never
reach.

Highest-opportunity pain: *"The nav wants me to pick a pack. I don't know which
pack my problem is in — that's why I'm reading the docs."*

The arc is the inverse of the marketing journey's. Marketing peaks where it stops
explaining and gives a command. Documentation peaks where it explains the model
in ordered, job-led form — and buries that peak under a taxonomy.

---

## Handoff notes

**For `documentation-design`:** the first-value moment is already built and
mislocated. The work is wayfinding, not authoring. Two changes carry nearly all
of it: lead the index with "Follow a path", and re-group the sidebar by job. The
second is authored in `site.toml [[guide_groups]]` and consumed by
`generate_sidebar_config` in `tools/build-site.py` — a data change with a
generated projection, never an edit to `docs-site/src/content/docs/guides/`,
which is itself a build projection of `guides/`.

**For `information-architecture`:** re-grouping the sidebar changes route
identity for twenty-one groups. The third tech-site principle allows this only as
a deliberate contract amendment with a migration path, never as churn. That cost
must be argued explicitly or the change is refused.

**For the fourth tech-site principle:** the fix for this surface is *not* to make
it look like marketing. Both surfaces fail the same principle — lead with the
reader's job — and each must fix it in its own reading mode. Marketing gets one
canvas. Documentation gets ordered paths and a job-grouped nav. They share
vocabulary, not presentation.

**For the cross-surface seam:** Stage 1 and Stage 2 are the crossing, and both
are on the documentation side of it. See
`docs/design/discovery/team-orientation-seam.md`.
