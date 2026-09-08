---
type: information-architecture
slug: team-orientation-ia
status: active
surfaces: 2
genres:
  - marketing
  - documentation
governed_by:
  - docs/design/principles/tech-site.md
  - docs/specs/guides-sidebar-generation/spec.md (Status: Shipped)
  - docs/adr/0020-per-pack-diataxis-hierarchy-for-guides.md
gate_approved: approve-journey, 2026-09-04
updated: 2026-09-04
---

# Information architecture — marketing and documentation

Reasoning and structure only. No layout, no markup, no values.

## Surface inventory

| Surface | Genre | This pass | Needs its own pass |
| --- | --- | --- | --- |
| Marketing home `/` | marketing | sitemap, scroll order, wayfinding | above-fold contract → `conversion-design` |
| Documentation guides | documentation | nav model, job grouping, migration | Diátaxis type map, TTFV → `documentation-design` |
| Catalogue, journeys, `/now/` | mixed | no | yes — out of engagement scope |

**An ordering conflict, stated rather than worked around.** This skill's step 1
routes by genre and requires reading `conversion-design` output before designing
marketing hierarchy, and `documentation-design` output before documentation
hierarchy. The standard enterprise packet puts both of those in Design, *after*
IA in Define. I have resolved it by splitting ownership rather than reordering
the packet: this document owns the **sitemap, navigation tree, and wayfinding**;
the two genre skills own the **above-fold contract, scroll-story zone
specification, Diátaxis type map, and first-value targets**. Nothing here decides
what the hero says. Recorded as Gap H.

## Success metrics, named before hierarchy

Hierarchy choices that cannot be traced to these are decoration.

**Marketing.** Primary: the explain-it-back score, out of five, for a reader who
has seen only this page. Secondary: five-second-scan completeness — can a
first-time reader answer *what is this / who is it for / should I care* from
visible content alone? Baseline is two of three unanswerable.

Explicitly **not** install conversion. That metric optimises the try-one-thing
framing this engagement exists to move past, and the approved dominance decision
makes the cohort decision the commitment worth earning.

**Documentation.** Primary: can a platform lead who has never spoken to the
champion complete the adopt path from the index alone? Secondary: the proportion
of guide-area arrivals that come through the index rather than through raw
repository source — currently the wrong way round, with 12 unique readers on one
`SKILL.md` against 6 on `/tree/main/docs`.

---

# Part 1 — Marketing surface

**Job.** Make a champion able to explain the operating model to an engineer, a
platform team, and a budget holder.

**Audience rank.** Champion primary; engineer and platform lead secondary; budget
holder tertiary on the page and decisive in the room.

## Content rank

Forced to a single primary, because two things competing for first place stalls
the eye.

| Rank | Content | Why here |
| --- | --- | --- |
| **Primary** | The operating-model canvas | It is the only element that answers the page's job. Everything else supports or proves it. |
| Secondary | The problem sentence; three checkable proofs | The reason to care, and the evidence that the primary claim is real. |
| Tertiary | Station detail, work-lifecycle detail, decision points, outcome router, adapter matrix, install, route into the paths, catalogue closer | Each answers a follow-on question. None competes for the lead. |

## Reading pattern

**Z-pattern above the fold**, then **layer-cake for the scroll.**

**Corrected after cold review.** An earlier draft argued the Z from a sparseness
the above-fold contract contradicts. The real inventory is the canvas plus the
six-element contract `conversion-design` specifies — headline, subheadline,
primary action, transitional action, proof signal, friction microcopy — so
**seven elements, two of them actions**, not "one canvas, one line, one action".

The Z still holds, and for a better reason than sparseness: the region has **one
dominant object** and a small number of supporting elements arranged around it,
which is what the Z rewards. F would reward text-dense rows, and the region has
none. Orientation and headline at the top-left of the scan, the canvas carrying
the diagonal, the primary action where the Z ends, and the transitional action
subordinate to it.

**A budget the packet had not checked.** A 1200×630 canvas at content width plus
seven further elements does not fit above a laptop fold. So the canvas's
above-fold height is a constraint, not a free variable, and it must be stated as
design intent so the "two things complete in five seconds" requirement is
testable. Owed to `conversion-design`; recorded here because it is an IA
consequence.

Layer-cake below: the page is strongly sectioned with distinct headings, and
readers move heading-to-heading rather than reading through. Each zone heading
must therefore state its own point, front-loaded, because a heading that buries
its point past the first few words gets skipped.

The canvas has its own internal scan order, specified separately in
[the canvas screen brief](../screens/team-orientation-canvas.md). It is neither
Z nor F; it is a traced path.

## Scroll order

Eleven zones, each with one job. Zone count and any merging is
`conversion-design`'s call; the *order* and each zone's *job* are IA's.

| # | Zone | Single job | Band | Change |
| --- | --- | --- | --- | --- |
| 1 | Canvas, orientation, one action | Show the whole model and name the reader | dark | **New structure** |
| 2 | Three checkable proofs | Prove the biggest claim is real | dark, continuous | **Re-tasked** from the stat strip |
| 3 | The problem | Give the reason, before any menu | light | **Relocated up** from position 4 |
| 4 | What changes for a team | The five stations, and **what each asks of a team** | light | **New.** See the cost note below. |
| 5 | What happens to one piece of work | Station 2 expanded, end to end | light | Absorbs the three-loops zone; **all gate codes removed** |
| 6 | Where a person decides | What each handoff asks of a human | light | Existing decision cards; **all six gate codes removed** |
| 7 | Recognise your work | Route by outcome before pack names | light | **Relocated down**, below the problem |
| 8 | Works with your agent | Confirm my agent is supported | light | Unchanged |
| 9 | Start in one command | Give the one runnable thing | dark | Unchanged |
| 10 | Roll it out to your team | Route into the ordered paths | light | **New — this is the seam fix** |
| 11 | Own the catalogue your team runs | Closing commitment | dark, merges with footer | Unchanged |

**Zone 2 keeps its position and changes its content.** The gate decision was to
re-task the three numbers as real evidence rather than cut them. Position is
load-bearing: the aesthetic direction assigns this band to sit immediately below
the primary action, continuous with the dark hero, and moving it would break the
alternating-band model. So the band stays and the content becomes three things a
skeptic can check. What those three are is a `content-design` decision; the IA
requirement is that each is a real artifact, command, route, or output — not a
self-reported count.

**Zone 4 carries no invented durations.** An earlier draft required "the five
stations with their real costs, sourced never written". The published costs are
**work-path** durations (P1 ~1 h, P3 ~2 h); there is no published cost for
*Evaluate*, *Win buy-in*, *Roll out a cohort*, or *Make it the default*, and no
mapping from six paths to five stations exists. Three of five rows could only be
invented, which the evidence principle forbids.

So zone 4 states, per station, **what the station asks of a team** — a commitment
shape rather than a number. Only station 2 carries durations, and it cites their
provenance: the on-ramp's under-twenty-minutes to a first answer, and P3's ~2 h
to a shipped change. For the other four, the surface **names the evidence
boundary** rather than substituting a figure, which is what principle 2's own
tradeoff prescribes.

**Zones 4 and 5 must not merge.** Their separation *is* the two-lifecycle design.
Zone 4 is what happens to a team; zone 5 is what happens to one piece of work.
Collapsing them reintroduces the diagnosed failure — six of nine current sections
describe both at once and neither whole.

## Disclosure staging

Two levels, and no more. NN/g finds designs beyond two disclosure levels
typically unusable because readers lose their place between them.

- **Level 1** — the canvas: five adoption stations, with station 2 visibly
  containing the work steps at low resolution so the *nesting* is legible
  without any interaction.
- **Level 2** — zone 5: the work lifecycle expanded to its full sequence,
  anchored from station 2.

**Level 2 is a page zone, not a disclosure widget.** This is the load-bearing
choice. Because the canvas must render as a static image inside `README.md` where
GitHub strips scripts and styles, no part of the model may live behind an
interaction. So the expansion lives in the document, always present, and the
canvas links to it. Interaction adds emphasis — highlight, scroll, focus — never
information.

Nothing essential is disclosed away: a reader who never interacts and never
scrolls still gets the whole model's shape, and a reader who scrolls gets all of
it.

## Wayfinding

*Where am I* — the canvas is the page's landmark and its "you are here" for the
whole model. Zones 4 and 5 each state which lifecycle they belong to in their
heading, so a reader who lands mid-page by anchor is never ambiguous about which
one they are in.

*Where can I go* — one action above the fold. Zone 10 is the only route into the
documentation surface, and it is placed where the current page strands the reader
rather than in the footer.

*How do I get back* — the canvas is reachable from any zone, and station names
recur as the zone headings for 4 and 5, so the reader can always map a zone back
to its position in the whole.

**Consistent placement, and one correction.** The five station names appear in **four** places: the canvas, zone 4, the anchor
for zone 5, and the internal-case route. They are **not** the documentation job groups — an earlier draft claimed they were, and that was wrong. The stations answer *how far along adoption is this team*; the seven job groups answer *what does this reader want to achieve*. Different axes, different counts, both legitimate. What actually crosses the seam is the **work-lifecycle decision phrasing**, which is identical on both surfaces, plus the seven job names, which already exist on both. Crossing invariant 1 is restated accordingly in the seam artifact.

## States

Per the shared quality floor. The marketing page is mostly static, so most states
land on two elements.

| Element | State | Behaviour |
| --- | --- | --- |
| Canvas | default | Whole model legible, no interaction needed |
| Canvas | emphasis | Hover and keyboard focus highlight a station; adds no information |
| Canvas | reduced motion | Static; at most a one-shot entrance, per the existing aesthetic decision |
| Canvas | narrow viewport | Replaced by a semantic ordered list — the same artifact that serves as its text alternative |
| Canvas | sanitised static | What `README.md` renders; verified, not assumed |
| Adapter matrix | overflow | Horizontal scroll in a focusable region with an accessible name — already correct, do not regress |
| Install block | copy success | Confirmation proportionate to the action — existing behaviour |

No loading, empty, or error states: the page has no data dependency and no gated
content. Stated so the omission is a finding-free decision rather than a gap.

---

# Part 2 — Documentation surface

**Job.** Get a reader to a followable sequence they can hand to someone else.

**Content reality.** 207 guide markdown files across 21 pack directories, plus 22
pack reference pages — roughly 229 published pages. That is the search-first
tier, two tiers above the flat navigation shipped today.

## The finding that decides this section

**The job taxonomy already exists, twice, and the sidebar is the one place that
ignores it.**

`web/src/lib/catalogue-navigation.ts` declares seven job-named outcomes with pack
membership, and its own header states the intent: *"Homepage and catalogue copy
can differ in depth, but pack membership and anchors must not drift between those
two entry surfaces."* The same seven job **names** appear in `guides/README.md`'s "Choose what you want to achieve" table. Both are hand-maintained in parallel — one in TypeScript, one in Markdown — and **their pack membership has already drifted**, which is the strongest argument for a single source. Three of the seven disagree: `operate` names architect and contracts in TypeScript but `core` in the guide table; `evidence` includes desk-research in TypeScript and not in the guide; `govern` includes agent-skill-engineering in TypeScript and not in the guide.

The documentation sidebar uses neither. It groups by pack `group` values —
Foundation, Agent workflows, Engineering, Integrations, Content and design,
Catalogue operations, Other — and then nests every guide two levels deep inside a
single trailing group.

So the job grouping this engagement needs requires **no new vocabulary at all.**
Reusing the seven existing job names aligns three surfaces on one taxonomy and
satisfies principle 3 by construction.

**The structural recommendation that follows:** promote the job taxonomy into
`site.toml`, which principle 3 already names as the mechanism for sharing
destination IDs, labels, targets, groups, order, and target kind across renderers
while sharing no presentation. Today it lives in a marketing-only TypeScript
module and a Markdown table. One source, three consumers.

## Navigation tree

Eight top-level choices — seven jobs plus a start-here group. Depth is three:
job → pack area → page.

Eight is a handful of distinct choices, and every common destination sits within
three steps. Twenty-one top-level entries would be too broad to scan; the current
single trailing group is too deep to find.

| Job group | Guide areas (canonical home) |
| --- | --- |
| Start here | `_shared` |
| Decide what to build | `product-strategy`, `desk-research`, `product-engineering` |
| Design the product and system | `experience-design`, `architect`, `contracts`, `frontend-engineering` |
| Build and review software | `core`, `governance-extras`, `monorepo-extras` |
| Provision and release safely | `iac-terraform`, `release-engineering` |
| Work with team systems and evidence | `atlassian`, `github`, `linear`, `figma`, `converters`, `credential-brokers` |
| Document what ships | `product-documentation` |
| Build and govern a catalogue | `catalogue-curation` |

Twenty-one areas, each appearing exactly once.

## Polyhierarchy, resolved to one canonical home each

Six areas legitimately serve two jobs. NN/g's finding is that a page under
multiple parents fights breadcrumbs, which can show only one canonical path, and
the remedy is either one canonical placement or faceting. Placement is chosen
here; faceting is a larger change than this engagement should make.

| Area | Also serves | Canonical home | Cross-referenced from |
| --- | --- | --- | --- |
| `architect` | operate | Design the product and system | Provision and release safely |
| `contracts` | operate | Design the product and system | Provision and release safely |
| `desk-research` | evidence | Decide what to build | Work with team systems and evidence |
| `converters` | document | Work with team systems and evidence | Document what ships |
| `governance-extras` | govern | Build and review software | Build and govern a catalogue |
| `product-documentation` | govern | Document what ships | Build and govern a catalogue |

Cross-references live in page bodies, never as duplicate navigation entries. A
second nav entry for one area is the polyhierarchy defect, not the fix.

## Two drift findings

- **`agent-skill-engineering` is named in the `govern` outcome and has no guide
  directory.** The taxonomy points at a destination with no documentation
  content. Either the pack needs a guide area or the outcome membership is
  wrong. Not resolvable from design; routed to the owner of the taxonomy.
- **`_shared` is unmapped to any outcome**, correctly — it is cross-cutting. It
  needs its own home in a job grouping, which is what "Start here" provides.
  Today `site.toml` labels it "Cross-cutting" and places it seventeenth.

## Nav-label migration — and a correction to the gate framing

**Good news first: no URL changes.** The shipped spec requires each record's slug to *equal the Starlight slug of the file the mirror step writes*, and `[[guide_groups]]` controls grouping and group labels only. Re-grouping changes navigation, not destinations.

**One precision, from cold review.** A page's slug is *usually* derived from its directory path, but a valid `slug:` frontmatter field overrides the derived path — `guides/atlassian/review-your-team-backlog.md` is a live example. That does not change the conclusion, because `[[guide_groups]]` touches neither derivation path. It does mean "URLs come from the directory tree" is an over-simplification and any future move of a *file* must check for a `slug:` override.

The route-identity cost I priced at the gate is therefore much smaller than I
stated. No redirects are needed. What is owed is a **nav-label migration table**,
below, plus a check that the frozen no-regression baseline survives.

| Today's group label | Position | Becomes |
| --- | --- | --- |
| The Build Loop (core) | 1 | Build and review software |
| Product Strategy | 2 | Decide what to build |
| Product Discovery | 3 | Decide what to build |
| Release Engineering | 4 | Provision and release safely |
| Desk Research | 5 | Decide what to build |
| Architect | 6 | Design the product and system |
| Experience Design | 7 | Design the product and system |
| Frontend Engineering | 8 | Design the product and system |
| Contracts | 9 | Design the product and system |
| Converters | 10 | Work with team systems and evidence |
| Atlassian | 11 | Work with team systems and evidence |
| Figma | 12 | Work with team systems and evidence |
| Governance Extras | 13 | Build and review software |
| Monorepo Extras | 14 | Build and review software |
| Credential Brokers | 15 | Work with team systems and evidence |
| Product Documentation | 16 | Document what ships |
| Cross-cutting | 17 | Start here |
| Terraform and OpenTofu | 18 | Provision and release safely |
| Catalogue Curation | 19 | Build and govern a catalogue |
| GitHub | 20 | Work with team systems and evidence |
| Linear | 21 | Work with team systems and evidence |

The pack-level labels are retained as the second tier inside each job group, so
no existing label disappears — it moves down one level.

**The no-regression check.** `guide-nav-baseline.toml` freezes 17 `(slug, label)`
pairs that every generation must reproduce. All 17 pin *pages*, not groups, and
re-grouping changes neither page slugs nor page labels — so the guard should
survive. That is stated as a check owed at implementation, not as an assumption.

## The blocker: this needs a Shipped spec amended

`docs/specs/guides-sidebar-generation/spec.md` is **Status: Shipped** and it
governs exactly this surface. Two of its provisions block the design as
specified:

1. **The data model has no job tier.** Each `[[guide_groups]]` entry is `dir`
   plus `label`, and table order is group order. It expresses a flat ordered
   list of directory-labelled groups. There is no field that can put several
   pack directories inside one job group.
2. **"An entry is required for every directory under `guides/`."** So the
   grouping cannot be achieved by removing or merging entries.

The change is therefore not a data edit. It is an amendment to a shipped
contract, and per the repository convention a conflict between documented
guidance and a proposed change gets stated with its trade-off rather than
silently resolved.

**Recommended amendment, minimal and additive:** one optional `job` field on each
`[[guide_groups]]` entry. Generation emits job groups containing pack groups.
Entries without `job` keep today's behaviour, so the change is backward
compatible; every directory still requires an entry, so provision 2 is untouched;
table order still sets order within a job. `ADR-0020` mandates the per-pack
Diátaxis hierarchy *within* an area and is not engaged by how areas group above
themselves — but that reading needs the ADR owner's confirmation, not mine.

Two alternatives, both worse:

- **Reorder `[[guide_groups]]` only.** No schema change; job-adjacent runs of pack
  groups with no job labels. Cheap, and it is a flat list pretending to be a
  tree — the reader gets better adjacency and no grouping.
- **Promote the 21 pack groups to top level.** Fixes the buried-last-group
  defect with a smaller code change, and produces 21 top-level choices, which is
  the too-broad failure the depth-versus-breadth reasoning rejects.

This goes to the build handoff as a spec amendment, which is what `intake-intent`
routes. It is a scope fact the owner should know: the approved re-grouping is not
a design tweak.

## Reading pattern and disclosure — documentation

**F-pattern with layer-cake section markers** for the index. It is text-dense and
scanned, so heading and link text must be front-loaded: the highest-value words
first in each row and first down the left rail.

**Disclosure staging.** Level 1 is the "Start here" promise and the six ordered
paths. Level 2 is a path's own page. Level 3 is an individual guide.

**Three levels here, two on marketing — and the distinction is ours, not the
source's.** An earlier draft cited the two-level ceiling as if it licensed the
difference. It does not: the guidance draws no marketing/reference distinction,
and the peer audit records it as single-source and downgraded.

The real distinction is one the peer audit *does* draw. NN/g separates **staged**
disclosure — a linear sequence a reader moves through — from **progressive**
disclosure, a hierarchy a reader descends into. The marketing canvas is
progressive: one artifact the reader opens deeper, where getting lost between
levels is the risk the ceiling addresses. The documentation paths are staged:
index → path → guide is a sequence with a stable position and breadcrumbs at
every step, so the failure mode the ceiling guards against does not apply.

Stated as our judgement, with the mechanism named, rather than borrowed from a
citation that does not support it.

**Search is not a disclosure level; it is a parallel entry.** At 229 pages,
browsing cannot be the only route. Raising search to a first-class element of the
index is what moves this surface to its correct tier.

## Wayfinding — documentation, and the blocker this skill names

*Where am I* — job group and pack area both visible in the nav position, plus the
page's own title. Three levels of "you are here".

*Where can I go* — the six ordered paths from the index; the next page in a path
from any page in it.

*How do I get back* — up to the path, up to the job group, home to the index.

**Cross-surface wayfinding: the docs-to-marketing bridge is absent, and this
skill instructs that its absence be flagged as a blocker.** It is flagged.

A reader arriving from search lands with no context and no exit. Worse for this
engagement, a champion who has understood the model here and now needs to sell it
internally has no route to a surface that helps — the seam artifact's Crossing B,
independently identified by this skill's own check.

The minimum is a footer link on every page. The standard this skill names is a
persistent header element. The existing docs product-orientation band is the
natural home, and principle 4 requires it stay distinct from Starlight's own
chrome — which it already does.

## States — documentation

| Element | State | Behaviour |
| --- | --- | --- |
| Search | empty | First-run: placeholder naming a real example query, not "Search" |
| Search | no results | Show recovery — nearest job group and the six paths |
| Sidebar | narrow viewport | Collapses; navigation must remain reachable without it |
| Path page | partial | A path whose steps are not all written shows what exists and marks what does not, rather than hiding the path |
| Index | loading | Layout preserved so the page does not jump |

---

# Handoff

**To `conversion-design`:** zones and order are fixed above; the above-fold
contract, the three checkable proofs' content, and any zone merging are yours.

**To `documentation-design`:** the Diátaxis type map, the first-value target per
content type, and the P1 on-ramp split. The nav model above is the frame.

**To `interaction-design`:** the canvas's six states, and the emphasis-only rule.

**To `content-design` and `ux-writing`:** the five station names are load-bearing
in **four** places — the canvas, marketing zone 4, the anchor for zone 5, and the
internal-case route, which reuses them. Changing one changes all four. They are
not the documentation job groups; that is a separate seven-name axis.

**To the build handoff:** the `guides-sidebar-generation` spec amendment, the
`agent-skill-engineering` taxonomy drift, and the proposal to move the job
taxonomy into `site.toml`.

**Recorded as Gap H:** `information-architecture` declares a hard read-first
dependency on `conversion-design` and `documentation-design` output, which the
standard enterprise packet order places downstream of it. Either the skill's
dependency or the packet order is wrong; the split used here is a workaround, not
a resolution.
