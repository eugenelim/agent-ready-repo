---
type: behavioural-evidence-review
slug: team-orientation-traffic-evidence
status: active
surface: cross-platform
evidence_level: observational
instrument: GitHub repository traffic API
window: 2026-08-21 to 2026-09-03
captured: 2026-09-04T11:46:25Z
updated: 2026-09-04
---

# Behavioural evidence — GitHub repository traffic

Real behavioural data for the cohort-orientation redesign, captured because the
GitHub traffic API keeps only a rolling 14-day window. Everything below was
pulled once, at 2026-09-04T11:46:25Z, covering 2026-08-21 through 2026-09-03.
Re-running the same calls after 2026-09-17 returns a different window and cannot
reproduce these numbers.

**Read the instrument limits before the findings.** This instrument measures
github.com, not the published site. Two of the questions the redesign most wants
answered are outside what it can see.

## What the instrument can and cannot measure

| Question | Answerable here | Why |
| --- | --- | --- |
| Do people arrive at the repository, and from where? | Yes | Referrer and view endpoints report it directly. |
| Which repository pages do humans read? | Yes | The popular-paths endpoint reports github.com paths. |
| Do visitors reach `/agent-ready-repo/docs/guides/`? | **No** | The API reports github.com paths only. GitHub Pages has no analytics API, and this deploy has no third-party analytics. |
| How much traffic does the published site receive? | **No** | Only its outbound referrals to the repository are visible, which is a floor on its readership, not a measure of it. |
| Why did anyone leave, or what did they fail to understand? | **No** | No instrument in this repository measures comprehension or intent. |

Three further cautions on the numbers themselves:

- **Do not sum daily uniques.** GitHub de-duplicates uniques across the whole
  window by an undisclosed method. The daily unique figures for views total 194,
  while the window total the API reports is 149. Use the window totals.
- **Clone counts are machine traffic, not evaluators.** 22,787 clone events
  against 553 unique cloners is 41 clone events per cloner — the signature of
  CI, mirroring, and agent installs, not of people assessing the repository.
  The single-day peak of 4,412 events on 2026-09-01 reinforces this. Do not
  read 553 as 553 evaluating teams.
- **One path is operator traffic.** `/commits/main` shows 36 views against 1
  unique visitor. That is the maintainer. It is excluded from the findings.

## The raw window

**Views:** 725 views, 149 unique visitors.
**Clones:** 22,787 events, 553 unique cloners.

### Referrers

| Referrer | Views | Uniques |
| --- | --- | --- |
| github.com | 101 | 20 |
| eugenelim.github.io | 94 | 6 |
| teams.public.onecdn.static.microsoft | 51 | 12 |
| Google | 22 | 13 |
| pypi.org | 17 | 2 |
| buildwithclaude.com | 3 | 3 |
| chatgpt.com | 3 | 2 |

Named referrers account for 58 of the 149 unique visitors. The remaining 91
visitors — 61 percent — arrived with no referrer: direct navigation, a bookmark,
or a client that strips the header.

### Most-read repository paths

| Path | Views | Uniques |
| --- | --- | --- |
| Overview (repository root, renders `README.md`) | 226 | 68 |
| `/tree/main` | 21 | 12 |
| `/pulls` | 21 | 8 |
| `/blob/main/packs/experience-design/.apm/skills/process-mapping/SKILL.md` | 16 | 12 |
| `/tree/main/packs/architect/.apm/skills/architecture-lenses-reference` | 13 | 7 |
| `/tree/main/docs` | 9 | 6 |
| `/issues` | 8 | 5 |
| `/tree/main/packs` | 8 | 4 |
| `/tags` | 8 | 2 |

## Findings

### 1. The README is the front door, not the marketing home page

68 unique visitors read the repository Overview — 46 percent of every unique
visitor in the window, and more than three times the next-largest destination.
The published marketing home page referred 6 unique visitors to the repository
in the same fortnight.

This confirms, from behaviour rather than assumption, the Awareness-stage
description already recorded in `docs/product/journeys/team-evaluates-and-adopts.md`:
*"Both read README and documentation."* It also means the owner's diagnosis —
that the landing page fails to show how the model maps together — sits on a
surface most arrivals never see first.

The redesign is still correct. Its reach is the thing that was overstated.

### 2. Champions transfer the model by pasting a repository link into chat

51 views from 12 unique visitors arrived through
`teams.public.onecdn.static.microsoft` — the Microsoft Teams link-unfurling CDN.
Someone pasted a repository URL into a Teams conversation and twelve distinct
people opened it.

Twelve people is double the six the entire published site referred.

This is the champion-transfer behaviour the engagement premise assumes, observed
directly. The mechanism is not *send them to the site*. It is *paste a GitHub
link into a work chat*. Whatever the champion pastes is doing the explaining.

### 3. Readers bypass the documentation surface to read skill source

One raw skill file — `packs/experience-design/.apm/skills/process-mapping/SKILL.md`
— drew 12 unique readers. A second skill reference tree drew 7. Meanwhile
`/tree/main/docs` drew 6, and no route this instrument can see indicates anyone
reached the published guides at all.

Twelve people chose to read an unrendered `SKILL.md` in a file browser over
anything the documentation surface offers.

The diagnosed problem was a seam: marketing ends at *install*, documentation
begins at *catalogue selection*. The measured problem is larger. Readers are not
falling into the gap between the two surfaces; a material share are skipping
both and reading source. That is a discovery failure in the documentation
surface, not only a handoff failure at its entrance.

### 4. Search and package traffic are small but real

Google referred 13 unique visitors and PyPI referred 2. Both are lower than the
README's 68 and lower than Teams' 12. No single acquisition channel dominates;
the largest identified one is a link pasted by a human into a conversation.

## What this changes in the design

**The canvas must work in three contexts, not one.** The engagement specifies a
hand-crafted SVG above the fold on the marketing home. The measured
champion-transfer path is a repository link in a chat client. So the canvas has
to survive:

1. the marketing home page, where it can be interactive;
2. `README.md` on github.com, where it renders as a static image inside a
   sanitised Markdown pipeline with no scripts, no external CSS, and no hover;
3. an unfurled link preview in Teams or Slack, where it may be cropped to a
   thumbnail or dropped entirely.

Context 2 is the binding constraint. It forbids any composition whose meaning
depends on hover, focus, scroll position, or client-side script, and it means the
canvas needs a legible static form at small size. This is a specification input,
not a nice-to-have, and it was not visible before this data.

**The documentation surface needs a discovery answer, not only a seam fix.** A
reader who reaches for `SKILL.md` in the file tree is looking for the executable
truth. The documentation IA has to intercept that intent — which is a
`documentation-design` question about first-value moment per content type, and a
reason the seam artifact alone would not have caught it.

## Reproduction

The four calls that produced this artifact, all read-only:

```bash
gh api repos/eugenelim/agent-ready-repo/traffic/views
gh api repos/eugenelim/agent-ready-repo/traffic/clones
gh api repos/eugenelim/agent-ready-repo/traffic/popular/paths
gh api repos/eugenelim/agent-ready-repo/traffic/popular/referrers
```

They require a token with push access to the repository. They return the trailing
14 days only, so they cannot reproduce the window above after 2026-09-17.

## Evidence level of the journeys derived from this

`observational` for arrival, referral, and repository-reading behaviour.
`assumption-based` for every stage emotion, pain, and motivation, none of which
this instrument measures. The current-state journey maps carry per-stage
evidence tags for exactly this reason; see
[the discovery brief](team-orientation-brief.md) for how the mixed level is
declared without presenting an assumption as grounded.
