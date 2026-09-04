---
type: discovery-findings
slug: team-orientation-findings
status: active
surface: responsive-web
genres:
  - acquisition
  - documentation
evidence_level: mixed — see the discovery brief
updated: 2026-09-04
---

# Findings and opportunity areas

Synthesis of the Discover packet. No installed skill owns this artifact, so it is
hand-authored. Each finding names the evidence it rests on and the principle it
engages; each opportunity names what it would change.

Sources: the [traffic evidence review](team-orientation-traffic-evidence.md),
the [content inventory](team-orientation-content-inventory.md), the live
rendered surfaces fetched 2026-09-04, and the repository sources.

## The headline finding

**The compliant, job-led explanation of the operating model already exists in
this repository, is already published, and is unreachable from the surface that
needs it.**

`guides/README.md` — served at `/agent-ready-repo/docs/guides/` — contains six
ordered paths, P1 through P6. Each one declares a prerequisite, an audience, a
rough time cost, a **first value**, and an **ends at** that is a handoff rather
than a document:

| Path | For | Cost | First value | Ends at |
| --- | --- | --- | --- | --- |
| P1 · Adopt the catalogue | anyone, first session | ~1 hour | `workspace status` answers what to work on next | a repository whose queues you can read |
| P2 · Shape what to build | PM, product engineer, strategist | ~3 hours | one written intent naming an outcome and the bet behind it | Core intake |
| P3 · Build it | engineer, agent | ~2 hours | a spec and plan you approved before any code was written | a merged change, and the decision to merge is yours |
| P4 · Decide together | tech lead, architect | ~1.5 hours | a circulated proposal with its alternatives written down | an accepted decision that outlives the people who made it |
| P5 · Ship and report | delivery lead, SRE | ~2 hours | a deployed artifact validated in an environment like production | a human ratifying the production ship |
| P6 · Extend the catalogue | AI enablement, catalogue owner | ~3 hours | one skill of your own that your agent can run | a catalogue your organisation owns |

Three things follow, and each one shortens the design work.

**It is already principle-conformant.** P3's *"a spec and plan you approved
before any code was written"* is the plan-approval decision in human phrasing.
P5's *"a human ratifying the production ship"* is the production gate in human
phrasing. Across all six paths there is **not one gate code**. The vocabulary the
redesign needs in order to satisfy the fourth durable application of principle 1
is already written, already shipped, and already reviewed.

**The marketing surface independently re-expresses the same model in
non-compliant vocabulary.** `ThreeLoops.astro` and `HumanGates.astro` describe
the same handoffs using `G0`, `G1.5`, `G2`, `G3`, `G4`, and `G5` — eleven
rendered gate codes on the live home page, confirmed by fetch on 2026-09-04. Two
surfaces describe one model in two vocabularies, and the non-compliant one is the
one a first-time visitor meets.

**Canvas labels should be derived, not invented.** Taking the canvas vocabulary
from the P-path *first value* and *ends at* fields satisfies principle 3 — stable
names across surfaces — for free, and removes the largest source of invented copy
from the design. Anything I write fresh is a new name a reader has to learn
twice.

## Finding 2 — The documentation surface is organised by our taxonomy, not the reader's job

Three independent lines of evidence converge on this, which is why it is stated
as a finding rather than a hypothesis.

**The navigation is generated and flat.** `tools/build-site.py` generates
`docs-site/src/sidebar-config.json`, which is gitignored and untracked. It builds
one sidebar group per pack `group`, then appends **all guide content as a single
group** at the end. The live sidebar confirms the result: Get Started, Pack
Catalogue, Foundation, Agent workflows, Engineering, Integrations, Content and
design, Catalogue operations, Other, **Guides**. Every one of the 21 guide areas
declared in `site.toml [[guide_groups]]` sits inside that last entry — below a
group literally labelled "Other".

`site.toml` itself records how the order arose, in a comment at line 122:
*"Undeclared in the pre-change hand tree — their pages published but never
appeared in navigation. Appended so no existing group moves."* The order is
declaration history, not reader priority.

**Nothing on the marketing surface points into it.** The content inventory
checked every marketing destination: exactly one links to a guide, and it links
to a single `_shared` how-to. Twenty-one of twenty-two guide areas have no direct route from marketing at all. The generated docs index links seven.

**Readers route around it.** One raw `SKILL.md` file in the repository file
browser drew 12 unique readers in 14 days; a skill reference tree drew 7;
`/tree/main/docs` drew 6. Twelve people chose an unrendered source file over
anything the documentation surface offers.

The engagement diagnosed a seam: marketing ends at *install*, documentation
begins at *catalogue selection*. That is correct and it is also too kind. The
reader who does cross the seam lands on a nav that asks them to pick a pack —
and the good job-led content, P1 through P6, is on the page they land on but
below the fold, while the nav beside it is a pack list.

**Principle engaged:** principle 1, lead with the reader's job. The
documentation surface violates it in the same way the marketing surface does, one
level down.

## Finding 3 — The marketing page is not where most arrivals begin

68 unique visitors read the repository README in the 14-day window — 46 percent
of all 149 unique visitors. The published site referred 6.

The owner's diagnosis stands: the landing page does not show how the model maps
together. Its **reach** is what was overstated. A canvas that lives only above the
marketing fold reaches a minority of arrivals.

**Opportunity:** the canvas has to be portable to the README. That is a
constraint on the artifact, not a second deliverable — see Finding 4.

## Finding 4 — Champion transfer is a pasted link, and that constrains the canvas

51 views from 12 unique visitors arrived via the Microsoft Teams link-unfurling
CDN. Someone pasted a repository URL into a work conversation and twelve distinct
people opened it — double what the entire published site referred.

This is a referral path **consistent with** the champion-transfer behaviour the
engagement premise assumes — not proof of it. The API reports a referrer and a
count; it identifies no sender, no role, and no intent, and it cannot show
whether understanding transferred. What is observed is that a repository link
arrived through a chat client and twelve distinct people opened it. The
attribution to a champion is an assumption the interview tests.

**Consequence for the canvas specification.** It must hold up in three contexts:

1. the marketing home page, where it may be interactive;
2. `README.md` on github.com, rendered as a static image through a sanitising
   Markdown pipeline — no script, no external stylesheet, no hover, no focus;
3. a link-unfurl preview in Teams or Slack, where it may be cropped or dropped.

Context 2 binds. No part of the canvas's meaning may depend on hover, focus,
scroll position, or client-side script, and it needs a legible static form at
small size. Every state must therefore be reachable without interaction, with
interaction adding emphasis rather than information.

This was not visible before the traffic pull and it is the single largest change
to the canvas brief.

## Finding 5 — Eleven gate codes ship today, in two components, one unnamed

Confirmed by fetch against the live page on 2026-09-04: eleven rendered
occurrences.

| Component | Rendered codes | How they appear |
| --- | --- | --- |
| `ThreeLoops.astro` | 5 | `G3`, `G4` in the decorative pipeline chain; `G3`, `G4`, `G5` opening each loop's human-gate line |
| `HumanGates.astro` | 6 | `G0`, `G1.5`, `G2`, `G3`, `G4`, `G5` as the most prominent element on six of seven cards |

The engagement named only `ThreeLoops`. `HumanGates` is the larger violation: it
sets the code in `--ds-weight-heavy` at `--ds-type-body-lg` in accent colour, so
the machine contract is the visual entry point to every card.

`HumanGates` also already carries compliant replacement copy in its own `decide`
field — *"Is this idea worth exploring?"*, *"Is this safe to put in front of
users?"*. The codes are redundant with content already on the card.

Note the seventh card: its identifier is `Plan`, not a code. One card in seven
already does the right thing, which is the proof that the pattern survives the
removal.

## Finding 6 — Unevidenced claims cluster on the load-bearing ones

The content inventory ranked every marketing claim by how much adoption weight it
carries. The ranking is inverted against the evidence:

| Rank | Claim | Evidence beside it |
| --- | --- | --- |
| 1 | `core` cannot approve its own work | none |
| 2 | Unattended loops self-certify and require non-bypassable gates | none |
| 3 | The complete seven-gate human-control map | none |
| 4 | One install works across every major agent | none |
| 5 | Three loops, seven adapters, one pip install | none |

The five most load-bearing claims on the page are the five with nothing beside
them. The sections that *do* carry evidence — `PackCatalogue` with per-pack
routes, `InstallTerminal` with runnable commands, `BuildYourOrg` with a command
and a destination — carry the least consequential claims.

**Principle engaged:** principle 2 directly. The remedy is not to invent proof.
For each of the five, either place a real checkable artifact beside it or weaken
the claim to what can be shown. The hero claim is the hard case and it is
addressed in the messaging framework, not here.

## Finding 7 — Every marketing section describes both lifecycles at once

The content inventory's lifecycle column returned "Both" for six of the nine
sections and "Team adopting" for three. Not one section describes only the work
lifecycle, and not one separates the two.

This is the mechanism behind the owner's complaint. The reader is not given two
things to hold; they are given nine things each of which mixes two things. There
is no point on the page where either lifecycle is stated whole.

**Principle engaged:** principle 1. It also explains why adding a diagram to the
current page would not fix it — the ambiguity is distributed across every
section, so the canvas has to *replace* structure, not annotate it.

## Opportunity areas

Ranked by how much comprehension they buy per unit of build.

1. **Promote the P-path structure to the marketing surface as the adoption
   spine.** The content exists, is conformant, and is already written in the
   reader's terms. This is the highest-value, lowest-invention move available.
   Marketing gets the ordered adoption arc; documentation keeps the executable
   detail. Both share one vocabulary, which is principle 3 satisfied by
   construction rather than by discipline.

2. **Make the canvas the above-the-fold element, portable to the README.** One
   artifact serving the two highest-traffic entry points, built to the static
   constraint from the start.

3. **Re-group the documentation navigation by job, not pack.** The change is
   authored in `site.toml [[guide_groups]]` and consumed by
   `generate_sidebar_config`. This is a data change with a generated
   projection, not a component rewrite — cheap for the comprehension it buys.
   It carries a route-identity cost that principle 3 requires be paid
   deliberately.

4. **Remove all eleven gate codes and substitute the decision phrasing already
   present.** Mechanical, bounded, and required by a binding constraint.

5. **Place evidence beside the five load-bearing claims, or weaken them.** The
   honest option is available for all five: the repository contains real
   transcripts, real gate output, and a real adapter contract.

6. **Give the marketing surface a route into the documentation paths.** Twenty
   of twenty-two guide areas currently have no marketing route. This is the seam
   fix, and it is the smallest of the six because opportunity 1 largely
   subsumes it.

## Deliberately not pursued

- **Reworking the README.** Finding 3 shows it is the dominant entry point, which
  makes it tempting. It is outside the engagement's two named surfaces, and the
  canvas's portability requirement already delivers most of the benefit. Recorded
  as a follow-on, not absorbed.
- **Gate codes in generated pack journey content.** Thirteen files, same
  violation, fixable only at `packs/*/JOURNEY.md`. Recorded in the discovery
  brief.
- **A token "duplicate" that is not one.** An early count read three
  `--ds-focus-ring` declarations as a defect. They are one `:root` default plus
  two deliberate scoped overrides, each documented in `tokens.css` with its
  measured contrast ratio. The real baseline is 97 unique semantic tokens with
  no duplicates. Recorded here so the design-system pass does not "fix" a
  working control.
