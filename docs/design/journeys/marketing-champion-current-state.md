---
type: customer-journey
slug: marketing-champion-current-state
persona: adoption-champion
outcome: decide-i-can-take-this-to-my-organisation
surface: responsive-web
genre: marketing
state: current
evidence-level: assumption-based
evidence_note: >-
  Mixed by class. Arrival, referral, and reading behaviour are observational,
  from the GitHub traffic window 2026-08-21 to 2026-09-03. Every emotion and
  pain is assumption-based, inherited from docs/product/journeys/team-evaluates-and-adopts.md
  (status: planned). Frontmatter carries the honest floor; each stage carries its
  own tag. See docs/design/discovery/team-orientation-brief.md.
updated: 2026-09-04
---

# Journey: the champion meets the marketing home page

**Persona:** An adoption champion. Sometimes a senior engineer at a small
company deciding for themselves; more often someone inside a larger organisation
tasked with evaluating this, who cannot authorise its adoption and must convince
three other audiences — engineers who will use it daily, a platform team who will
own the install, and a budget holder who will fund it. They have used a coding
agent. They have not used a supervised operating model.

**Outcome:** Decide that they can take this to their organisation, and know what
they would say.

**Surface:** responsive-web. Progressive disclosure is load-bearing here: the
reader arrives with no commitment and the page must earn each further scroll.

**Trigger:** A peer recommendation, a search result, a package page, or a link someone pasted into a work chat. No single channel dominates: the largest *identified* referrer is a chat-client link at 12 unique visitors, and 61 percent of arrivals carry no referrer at all.

**End state:** The champion can state what the model is, what it asks of a team,
and what it refuses to do, well enough to repeat it to somebody who has not seen
the page.

**Genre note.** The marketing scaffold ends at *Converting* with *Advocating* as
a post-conversion referral stage. That ordering does not hold for this product.
The unit of adoption is a cohort, so the commitment action is taken by a budget
holder who is not on this page. The champion's conversion *is* the transfer. The
final stage is therefore named **Transferring** and carries the weight the
scaffold assigns to Converting.

**Evidence tags.** Each stage is tagged `[observational]`, `[assumption-based]`,
or `[mixed]`. Nothing tagged observational rests on anything other than the
14-day traffic window.

---

## Stage 1: Aware `[mixed]`

| Row | Content |
|-----|---------|
| **Actions** | Arrives from a pasted chat link, a search, a package page, or directly. Reads the hero headline and one paragraph. Scans the three numbers beneath it. Decides in seconds whether this is a tool or something bigger. |
| **Emotions** | Curious, and already braced. Neutral. They have seen several AI-tool landing pages recently and are looking for a reason to discount this one. |
| **Pains** | "It says it's a build loop that can't approve its own work. I don't know what a build loop is yet, so I can't tell if that's impressive." The hero names a mechanism before naming a job. The three numbers — three loops, seven adapters, one pip install — size an install, not an operating model, and nothing beside them is checkable. |
| **Opportunities** | Say what a team gets before naming what the system is. Make the first screen the whole model, at low resolution, rather than one claim about one component. |

Observational component: the README drew 68 unique visitors against the published site's 6 outbound referrals, and 61 percent of arrivals carried no referrer. So a large share of people meeting this product do not meet it here first, and those who do arrive largely arrive cold. The emotions and pains in this stage are assumption-based, which is why the tag is `[mixed]` rather than `[observational]`.

## Stage 2: Interested `[mixed]`

| Row | Content |
|-----|---------|
| **Actions** | Scrolls into the use-case section. Reads seven outcome cards, each naming an audience and listing pack names. Clicks one or two pack links. Comes back. Reads "An unattended loop makes unattended mistakes." |
| **Emotions** | Engaged, then diffuse. Neutral. The outcome framing lands; the immediate follow-up is a menu of fourteen-odd names, which converts interest into inventory. |
| **Pains** | "I now know there are packs. I still don't know what happens to a piece of work, or what happens to my team." Seven cards presented as equal-weight choices before the reader has decided to care. The problem statement arrives *after* the menu, so the reason to care is given after the thing to choose from. |
| **Opportunities** | Put the reason before the menu. Let the reader recognise the shape of the whole model before any component is nameable. |

Observational component: `/tree/main/packs` drew 4 unique visitors and two
individual skill files drew 12 and 7. Readers who go looking do not stop at the
pack level; they descend to the executable file. The pack menu is a waypoint
nobody wants to stand on.

## Stage 3: Evaluating `[assumption-based]` — **negative peak**

| Row | Content |
|-----|---------|
| **Actions** | Reads the three loops. Reads the seven decision cards. Tries to work out how a loop relates to a decision card, and how either relates to the pack names from two sections ago. Scrolls back up. Scrolls back down. |
| **Emotions** | Working hard, then deflating. Negative, and this is the deepest dip in the journey. The material is clearly serious, which makes the failure to assemble it feel like the reader's fault. |
| **Pains** | "There are three loops and seven gates and I can't tell which gate belongs to which loop, or where the packs fit." Eleven internal gate codes — G0, G1.5, G2, G3, G4, G5 — appear as the visual entry point to the material, and the codes are the most prominent element on six of seven decision cards. The reader is asked to learn a private notation in order to read a public page. Six of nine sections describe both lifecycles at once, so neither is ever stated whole. Every load-bearing claim on the page — that the loop cannot approve its own work, that unattended loops self-certify, that the gate map is complete, that one install covers every agent — has nothing checkable beside it. |
| **Opportunities** | State each lifecycle whole, once, with one dominant. Replace the notation with the decision it stands for. Put a real artifact beside each of the four claims that carry adoption weight, or weaken the claim to what can be shown. |

This is the stage the owner's verdict describes: *"it's not obvious from the
landing page how everything maps together on one page."*

Assumption basis: no instrument measures comprehension or abandonment on this
surface. The mechanism is grounded — the eleven gate codes, the both-lifecycle
mixing, and the five unevidenced claims are all verified in the rendered page —
but the reader's felt experience of them is inferred, not observed.

## Stage 4: Intending `[assumption-based]`

| Row | Content |
|-----|---------|
| **Actions** | Reads the adapter matrix and finds their own agent. Reads the install commands. Copies one. Possibly installs it and tries it alone. |
| **Emotions** | Reassured, and narrowed. Neutral to positive. This is the first part of the page that answers a question with something testable, and the relief is real. |
| **Pains** | "I can install it. I still can't explain it." The page's most concrete, most trustworthy moment is about a single command on one machine, which is the try-one-thing framing the whole engagement is trying to move past. Nothing here addresses a cohort, a rollout, or a budget conversation. |
| **Opportunities** | Keep the command — it is the page's best evidence. Stop letting it be the destination. The commitment this page should earn is a cohort decision, not a personal install. |

## Stage 5: Transferring `[mixed]` — the stage the page does not serve

| Row | Content |
|-----|---------|
| **Actions** | Copies a link and pastes it into a work chat. Books time with a budget holder. Tries to summarise the model from memory. Improvises a demonstration. Sends people to the repository rather than to the page. |
| **Emotions** | Exposed. Negative. They believe the platform is good and cannot reliably make somebody else believe it. |
| **Pains** | "I've done three live demos and every one felt like I was improvising. The platform is genuinely good — the demo isn't." There is no single artifact on the page a champion can hand to a budget holder. There is nothing that survives being pasted into a chat window. Three audiences need three different answers and the page offers one register. |
| **Opportunities** | Give the champion one artifact that carries the whole model and survives being pasted. Make it work as a static image with no interaction, because that is the observed transfer path. Answer the budget holder's question — what does this refuse to do — somewhere the champion can point at. |

Observational component: 51 views from 12 unique visitors arrived through the
Microsoft Teams link-unfurling CDN — double the 6 the published site referred.
Twelve distinct people opened a repository link that arrived through a chat client. The *referral path* is measured; that a champion sent it and that understanding transferred are not — the instrument reports a referrer, never an intent. Both that attribution and the improvising quote remain assumptions until the champion interview is run.

---

## Frontstage actions

- **Action:** arrive-from-pasted-link
- **Action:** read-hero-and-headline-claim
- **Action:** scan-the-three-numbers
- **Action:** scan-outcome-cards
- **Action:** open-a-pack-page
- **Action:** read-the-problem-statement
- **Action:** read-the-three-loops
- **Action:** read-the-decision-cards
- **Action:** trace-a-gate-to-its-loop
- **Action:** find-my-agent-in-the-matrix
- **Action:** copy-the-install-command
- **Action:** paste-a-link-into-work-chat
- **Action:** summarise-the-model-from-memory
- **Action:** demonstrate-to-a-budget-holder

---

## Emotional arc

Lowest point: Stage 3 — deflated — because the material is visibly serious and
the reader still cannot assemble it, which reads as personal failure rather than
as a design fault. Stage 5 is nearly as low and lasts longer, because it recurs
every time the champion has to explain the model again.

Highest point: Stage 4, the install command — the only moment on the page where a
claim is answered with something the reader can run.

Highest-opportunity pain: *"There are three loops and seven gates and I can't
tell which gate belongs to which loop, or where the packs fit."*

Second-highest, and the one with the longer tail: *"I've done three live demos
and every one felt like I was improvising. The platform is genuinely good — the
demo isn't."*

The arc is diagnostic. It dips hardest where the page tries to explain the model
and recovers only where it stops explaining and offers a command. That is the
shape of a page that can demonstrate a tool and cannot teach a system.

---

## Handoff notes

**For `user-flow`:** the highest-opportunity pains are in Stage 3 (Evaluating)
and Stage 5 (Transferring). Stage 3 is the negative peak and takes design
priority. Stage 5 is the stage with no current surface at all — it needs a screen
that does not exist today, and that screen is the operating-model canvas.

Every action from `read-the-three-loops` through `trace-a-gate-to-its-loop`
collapses into the canvas. `paste-a-link-into-work-chat` and
`summarise-the-model-from-memory` are the two actions that impose the canvas's
static-portability constraint.

**For `conversion-design`:** the above-the-fold decision is decided by Stage 1
and Stage 5 together, not by Stage 4. The page currently optimises for Stage 4.

**For the cross-surface seam:** Stage 2's descent past the pack menu into
individual skill files, and Stage 4's ending at a copied command, are the two
places this journey touches the documentation genre. Both are handled in
`docs/design/discovery/team-orientation-seam.md`, because no single-surface
journey can express a crossing.

**For `service-blueprint`:** not run in this engagement. The backstage
capabilities the champion's actions depend on are the pack install path, the
generated pack and guide navigation, and the journey page generator — all named
textually.
