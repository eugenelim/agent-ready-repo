---
type: documentation-design
slug: team-orientation-docs-structure
surface: responsive-web
surface-genre: documentation
communication_mode: technical-editorial
status: active
gate_approved: approve-aesthetic-direction, 2026-09-04
measured: 2026-09-04 at 047bf0192
updated: 2026-09-04
---

# Documentation surface structure and first value per content type

Structure only. The navigation model and job grouping are decided in
`docs/design/discovery/team-orientation-ia.md` and are not redone here.

Every count below was measured against the tree, not estimated.

## Navigation strategy — confirmed, not chosen

207 guide markdown files plus 22 pack reference pages: **roughly 229 published
pages**. Over 200 puts this surface in the search-first tier, where search is
primary navigation, the sidebar is a faceted or grouped filter, and landing pages
are **curated entry points rather than exhaustive indexes**.

The surface ships flat navigation with search as a header widget — two tiers
below what its volume requires. That is finding 13 in the heuristic baseline and
the IA fixes it. Restated here only because the tier governs the landing-page
design that follows.

## The measured Diátaxis type map

**202 of 207 files carry `kind:` frontmatter.** Distribution:

| Type | Files | Share | Reader's question |
| --- | --- | --- | --- |
| How-to | 91 | 45% | "How do I accomplish X?" |
| Explanation | 56 | 28% | "Why does X work this way?" |
| Reference | 38 | 19% | "What does X do or accept?" |
| **Tutorial** | **17** | **8%** | **"How do I start?"** |

### Finding 1 — the scarcest type is the one that owns first value

Tutorial is 8 per cent of the corpus, and **10 of the 21 guide areas contain no
tutorial at all**: atlassian, contracts, converters, credential-brokers,
experience-design, github, iac-terraform, linear, monorepo-extras, and
product-documentation.

A how-to *assumes prior knowledge* by definition. So a reader arriving cold at
any of those ten areas meets content written for somebody who already has the
knowledge they came to get. There is no first-value path in half the surface.

**This explains the strongest behavioural signal in the engagement.** One raw
`SKILL.md` drew 12 unique readers in fourteen days while the repository's docs
directory drew 6. Given a how-to that assumes knowledge the reader lacks, the
executable source *is* the next best thing — it is at least complete and
certainly true. Readers are not being perverse; they are routing around a missing
content type.

**The structural response is not "write ten tutorials."** That is a content
programme, not a design decision, and this engagement does not own it. The design
response is that the six ordered paths function as the surface's tutorial layer:
each one is a sequence with a prerequisite, a cost, and a stated first result,
which is what a tutorial provides. Promoting them is therefore not only a
wayfinding fix — it is how the surface acquires a first-value path without
writing new content.

Recorded as a follow-on with an owner question: which of the ten areas most need
a real tutorial, given the paths now cover the common routes.

### Finding 2 — every area hub is mistyped, and inconsistently

All 21 area `README.md` files function as navigation hubs. Their declared types:
**18 declare `explanation`**, and three — iac-terraform, release-engineering,
product-documentation — declare `reference`.

Two problems. A hub is neither: explanation answers "why does this work this
way" and a hub answers "what is here and where do I go." And the three
`reference` hubs differ from the other eighteen for no structural reason, so the
same page shape carries two different types.

Type mixing is a design finding, not a cosmetic one: it drives density targets
and what a page points to next. A hub typed as explanation inherits a
low-to-medium density target and a "points to how-to and reference" rule, which
is roughly right by accident.

**Recommendation:** add a `hub` kind to the guide source model, or accept
`explanation` as the deliberate convention and make all 21 consistent. Either is
defensible; the current split is not. This is the guide source model's decision,
not this document's — flagged with evidence rather than resolved.

### Finding 3 — a Shipped spec's stated premise is now stale

`docs/specs/guides-sidebar-generation/spec.md` relaxes the rule that a physical
directory does not determine kind, **only for pages carrying no `kind:`
frontmatter**, and justifies the relaxation with a measured figure: *"162 files
carry none, 157 of them nav-eligible."*

Measured today: **5 files carry no `kind:`** — the four
`guides/_shared/<kind>/README.md` section-authoring templates and
`guides/AGENTS.md`.

Those five are precisely the pages the same spec defines as **not
reader-facing** and therefore not nav-eligible. So **zero nav-eligible files now
fall through to the directory fallback.** The frontmatter migration the spec
named as the long-term fix has effectively completed, and the relaxation it
justified is vacuous in practice.

This is not a defect — the fallback is harmless and correctly scoped. It is a
stale premise inside a Shipped contract, and it matters because the same spec
needs amending anyway for the job-grouping change. Both belong in one amendment.

## First value, per content type

What the reader accomplishes, and the design decision that protects it.

| Type | First value | Design decision |
| --- | --- | --- |
| **Tutorial** | A specific, recognisable result produced in one sitting | Scoped to under twenty minutes of active work, prerequisites visible before the first step, samples that work exactly as pasted, and a "why this might have happened" path when a step fails |
| **How-to** | The stated goal achieved, with edge cases branched rather than inlined | Names its assumed prior knowledge **explicitly at the top**, and links the tutorial or explanation that supplies it. This is the single change that would most help the ten tutorial-less areas. |
| **Reference** | The fact found and the reader gone | Complete, consistently structured, and parseable. Points nowhere — a reference that tries to teach has become an explanation. |
| **Explanation** | The concept understood well enough to make a decision | Narrative, no step-by-step, and it points at the how-tos and references that implement the concept |

**The how-to row is the load-bearing one.** Ninety-one files — 45 per cent of the corpus — assume prior knowledge, and none of them currently names what it
assumes. Adding that one line per page is cheap, mechanical, and closes the gap
the missing tutorials leave open.

## TTFV and the P1 on-ramp split

The engagement flagged that the first ordered path is stated at about an hour
against a twenty-minute first-value budget. A tutorial whose success moment
arrives after an hour has an abandonment rate rather than a TTFV.

**The path is not too long. It is four things, and only the first is a tutorial.**
Its steps are: choose an install route, install the lifecycle, adapt an existing
repository or start a new one, and orient at session start. Its stated first
value is that `workspace status` answers what to work on next.

**Split the on-ramp out, do not shorten the path.**

| | Scope | Cost | First value |
| --- | --- | --- | --- |
| **On-ramp** (new) | Install, and get one real answer out of the tool | under 20 minutes | `workspace status` answers what to work on next |
| **Remainder of P1** | Adapt a repository or start a project, and establish the session-start habit | the balance of the hour | a repository whose queues you can read |

The on-ramp inherits the path's existing stated first value, which is already
scoped to a single recognisable result. The remainder keeps the path's existing
end state. **Nothing new is written** — the split is a boundary drawn through
content that exists, which is why it is a design decision rather than a content
programme.

The on-ramp becomes the landing page's single "start here" promise, which is the
one job that page currently fails.

## Landing page — the hub structure

An orientation map, not a content index, and at the search-first tier a
**curated** entry point rather than an exhaustive one. It assumes the reader has
already bought in; its job is orientation, not persuasion.

Ordered by the Pyramid Principle, because the reader is making a Decision at high
prior knowledge: the answer comes first.

| Order | Element | Job |
| --- | --- | --- |
| 1 | **Start here** — the on-ramp, one link, one promise | The landing page's first missing job. One promise with a time and a result. |
| 2 | **The six ordered paths** | The answer to "which sequence do I hand over." Currently below a navigation instruction; the Pyramid Principle puts it here. |
| 3 | **Search**, above the fold, placeholder naming a real example query | The second missing job. At 229 pages, browsing cannot be the only route. |
| 4 | **Four content-type entry points**, each named by what the reader accomplishes | The third missing job — and it serves the *recurring* reader, not the starting one |
| 5 | The seven job groups and the role list | The two existing alternate ways in, kept and demoted |
| 6 | Which hierarchy answers which question | Guides versus pack reference, stated at the point of choice |

**Reconciling the paths with the content-type entry points.** The canonical
structure wants four entry points, one per Diátaxis type. The Pyramid Principle
wants the paths first. Both fit because they serve different readers: the paths
serve somebody starting or handing over, the content-type entry points serve
somebody returning for a specific kind of thing. Paths at position 2, types at
position 4.

**The type entry points are named by accomplishment, never by type name.** "Learn
it by doing it" rather than "Tutorials." The type names are our taxonomy, and
leading with taxonomy is the failure this whole engagement is fixing — one level
further down.

The landing page carries no marketing copy and no persuasion register. The route
to the internal case is a *destination* it points at, not an argument it makes.

## Machine-readability — design requirements, not implementation notes

Named here because they are IA decisions that are invisible in rendered output
and expensive to retrofit. This surface has a specific reason to care: its
readers include coding agents, and its own product is an agent platform.

| Requirement | Why it is a design decision |
| --- | --- |
| **The six paths marked up as ordered sequences**, not prose with numbers | A path's value is its order. Prose numbering is unextractable, and the paths are the surface's most-reused structure. |
| **Code blocks carry a language identifier** | An untyped block is noise to an extractor. Non-negotiable for a surface whose readers include agents. |
| **The path contract fields carry a consistent structure across all six** — prerequisite, audience, cost, first value, ends at | This makes the paths comparable and extractable, and it is what lets the marketing canvas source its labels from them instead of inventing new ones. The cross-surface vocabulary invariant depends on it. |
| **Heading hierarchy reflects content type** — section, procedure step, sub-step | Flat heading use collapses the structure an extractor needs. Uneven today across 207 files; enforce for new and changed pages rather than retrofitting all of them. |
| **Reference tables keep consistent column headers** | 38 reference files exist; inconsistent columns make them unparseable as a set. |

Deliberately **not** required: an `llms.txt` or similar machine index. It is a
publishing decision rather than an IA one, and adding it would not fix any
finding above.

## Open questions

1. **Which of the ten tutorial-less areas need a real tutorial?** The paths now
   cover the common routes, so the answer may be "few". Owner: whoever holds the
   content programme. Not a design decision.
2. **`hub` kind, or `explanation` by convention?** Twenty-one hubs are mistyped
   and three are mistyped differently. Owner: the guide source model.
3. **Does the stale fallback premise get corrected in the same amendment as the
   job grouping?** Both touch one Shipped spec and both are small.

## Hand-off

`ux-writing` for the search placeholder — which must name a query that actually
returns results — the no-results recovery, the partial-path marker, and the four
accomplishment-named type entry points. `information-architecture` already owns
the navigation model. The build handoff carries the spec amendment, now with two
items rather than one.
