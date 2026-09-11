# docs/design/

Design artifacts for this repository's surfaces. Artifact-kind first, then slug —
`journeys/`, `screens/`, `blueprints/`, `principles/`, `content/`, `copy/`, plus
`discovery/` and `direction/` added by the cohort-orientation engagement.

**Durable, cross-engagement:** [`principles/tech-site.md`](principles/tech-site.md)
governs every surface listed below and outlives any one piece of work.

---

# Cohort orientation — the current packet

One engagement, 2026-09-04: redesigning the marketing home and the documentation
guides index so a champion can explain the whole operating model to an engineer,
and a platform team. (Narrowed 2026-09-10 on the de-risk; the budget holder is a gatekeeper needing evidence this packet does not carry.)

**38 files, ~8,900 lines, one hand-authored SVG.** That is roughly six hours of
reading end to end, which nobody should do. The tiers below exist so you can
spend 35 minutes and make every decision that is actually open.

## Tier 1 — read this to decide · ~35 min · 4 files

Everything the owner needs, and nothing else.

| File | Lines | Why |
| --- | --- | --- |
| [`discovery/team-orientation-review-response.md`](discovery/team-orientation-review-response.md) | 174 | Two cold reviews, 40 findings, what was fixed and what is owed. **The gate decision lives here.** |
| [`discovery/team-orientation-decision-log.md`](discovery/team-orientation-decision-log.md) | 255 | Nine decisions and what decided each. Also every correction the packet made to itself. |
| [`discovery/team-orientation-build-handoff.md`](discovery/team-orientation-build-handoff.md) | 189 | What to build, in dependency order. Three governance items gate all code. |
| [`../product/findings/experience-design-thread-pressure-test.md`](../product/findings/experience-design-thread-pressure-test.md) | 154 | Whether the thread was worth it. Honest about both halves. |

**Five things are open and only you can close them.** They are listed at the end
of the decision log; nothing else in this packet needs a decision.

## Tier 2 — read to check the reasoning · ~50 min · 6 files

If you want to know *why* rather than *what*.

| File | Lines | Answers |
| --- | --- | --- |
| [`discovery/team-orientation-traffic-evidence.md`](discovery/team-orientation-traffic-evidence.md) | 180 | The only real behavioural data. Read its limits section first — it is the model for how to state an instrument's blind spots. |
| [`discovery/team-orientation-findings.md`](discovery/team-orientation-findings.md) | 250 | The seven diagnostic findings the design answers |
| [`discovery/team-orientation-seam.md`](discovery/team-orientation-seam.md) | 155 | The marketing→documentation crossing, and the three crossings that exist |
| [`discovery/team-orientation-ia.md`](discovery/team-orientation-ia.md) | 455 | Sitemap, navigation, the job grouping, and the Shipped-spec blocker |
| [`discovery/team-orientation-marketing-structure.md`](discovery/team-orientation-marketing-structure.md) | 232 | The above-the-fold decision, argued |
| [`discovery/team-orientation-docs-structure.md`](discovery/team-orientation-docs-structure.md) | 223 | Diátaxis map, and why 10 of 21 guide areas have no starting point |

## Tier 3 — build reference · read when implementing

Not for review. Whoever builds this reads these; the owner does not need to.

**The centrepiece** — [`screens/team-orientation/`](screens/team-orientation/)

| File | Lines | Contents |
| --- | --- | --- |
| `operating-model-canvas.svg` | 111 | The hand-authored SVG. **Reference composition, not the shipped asset** — it must be regenerated from the token source. |
| `operating-model-canvas-composition.md` | 298 | What it does, every measurement, the text alternative, the three renderings |
| `../team-orientation-canvas.md` | 345 | The deep spec: metaphor, trace order, labels, states, screen-reader equivalence |
| `operating-model-canvas.md` | 299 | Its per-screen brief and interaction spec |

**Flow and screens** — [`screens/team-orientation-flow.md`](screens/team-orientation-flow.md) (293) plus five more per-screen briefs: `marketing-home`, `guides-index`, `path-page`, `search-results`, `internal-case-route`.

**Copy and content** — [`copy/copy-deck.md`](copy/copy-deck.md) (416, every string plus the headline candidates), [`copy/brand-register.md`](copy/brand-register.md), [`copy/marketing-home.md`](copy/marketing-home.md), [`content/`](content/) (four briefs, including [`content/journeys-index.md`](content/journeys-index.md), added 2026-09-11 outside the packet), and [`../product/voice/agent-ready-repo.md`](../product/voice/agent-ready-repo.md).

**Direction** — [`direction/tech-site-amendment.md`](direction/tech-site-amendment.md) (262, amends the aesthetic direction; **this is the operative document**, not the frozen original) and [`direction/token-verification.md`](direction/token-verification.md) (209).

## Tier 4 — audit trail · read only if a claim is challenged

Kept because the packet's claims trace to them. Nobody needs to read these to
act.

`discovery/team-orientation-peer-audit.md` (441) · `discovery/team-orientation-heuristic-baseline.md` (426) · `discovery/team-orientation-measurement-plan.md` (510) · `journeys/` (four maps, 641 + the practitioner current-state map) · `discovery/team-orientation-personas.md` (155) · `discovery/team-orientation-champion-interview.md` (152) · `discovery/team-orientation-content-inventory.md` (67) · `discovery/team-orientation-brief.md` (279) · `discovery/team-orientation-screen-list.md` (125)

---

## State

| | |
| --- | --- |
| `approve-journey` | passed 2026-09-04; **re-gated 2026-09-10** for the future-state map's Stage 2 amendment (the terminal-only dependency) |
| `approve-aesthetic-direction` | passed 2026-09-04 |
| `review-experience-designs` | **passed 2026-09-10** — 6 blockers fixed, 14 of 16 majors fixed. Major 1/V1 closed by a live GitHub render probe. Minor 5 **retired**, not deferred: the champion interview it waited on was retired as theatre, so M2 carries no pre-redesign baseline and will not get one. |
| Build intent | [`../product/intents/cohort-orientation-surfaces.md`](../product/intents/cohort-orientation-surfaces.md) — `Draft` |
| Implemented | **Partly, and not by this packet.** Slice S6 of `sdlc-guide-uplift-and-learning-paths` shipped the journeys index grouping and `guides/README.md` P2b on 2026-09-11, touching `web/` and `guides/`. That surface was **never in this packet's scope** — see the note below. Everything this packet itself specifies remains unbuilt; all three gates are passed, so delivery is unblocked. |

**The journeys index is outside this packet, and that had a cost.** This packet
briefs the marketing home, the guides index, a path page, search results, the
internal-case route and the canvas. It does not brief `/journeys/`. When S6
redesigned that surface it had no brief to anchor on, and an independent design
review found its groups "feel added above an existing catalogue grid". A content
brief now exists at [`content/journeys-index.md`](content/journeys-index.md),
authored after the fact, and it records that the surface still has no owner.

**One verification blocks build and cannot be closed by writing:** whether the
canvas survives GitHub's Markdown sanitiser was probed 2026-09-10 against
GitHub's own renderer and is closed: the `<img>` binding works, inline embedding
is removed outright.

## Two things to know before reading anything

**`experience-status` cannot see this packet.** `[design] output_dir` is
unconfigured, so the tool stops at "not configured" and reports zero artifacts
against 38 on disk. Configuring it is a repository decision.

**The packet corrects itself in public.** Eleven claims were corrected before
review and forty findings after it, each recorded with what found it. Where a
document says an earlier draft was wrong, that is the record working, not
residue to tidy.
