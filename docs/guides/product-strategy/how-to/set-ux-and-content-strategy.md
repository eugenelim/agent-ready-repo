# Set UX and content strategy

Design is about to start, and you want the experience and content direction fixed
first — so the journey maps and screens that follow have a vision to serve rather
than inventing one per surface. This guide covers the two skills that set that
direction: `define-ux-strategy` and `define-content-strategy`.

It assumes the pack is installed. It also assumes you know the line this guide
draws hard: strategy here sets the *system*, not the surface. Per-surface content
design is out of scope, and this guide says exactly where that boundary sits.

## Set the experience direction: `define-ux-strategy`

Run this before journey mapping, not after.

> Define the UX strategy for the onboarding redesign.

`define-ux-strategy` sets the experience vision, the goals and measures, and the
plan to get there, committing `ux-strategy.md` to `docs/product/shaping/`. It
draws on three sources at once:

- the **NN/g three-layer model** — separating the durable experience vision from
  the goals beneath it and the plan beneath those;
- **Jaime Levy's four tenets** of UX strategy — the business-strategy,
  value-innovation, validated-user-research, and killer-UX framing;
- **Gothelf/Seiden** — linking UX outcomes to OKRs so the strategy has measures,
  not aspirations alone.

The failure mode is a UX strategy that is really a design brief — screen-level
opinions dressed as vision. Keep it at the altitude of *what kind of experience
this is and how we'll know it worked*. If the OKR cascade has run, link the UX
measures to those objectives rather than inventing parallel ones; the point of
the Gothelf/Seiden framing is that experience outcomes and company objectives
share a spine.

## Set the content system: `define-content-strategy`

Run this alongside UX strategy when content is a first-class part of the product.

> Define the content strategy for the help centre.

`define-content-strategy` works Halvorson's content-strategy quad — **Purpose**,
**Process**, **Structure**, **Governance** — and commits `content-strategy.md` to
`docs/product/shaping/`. The quad is the whole point: it forces you to decide not
only what content is *for* (Purpose) but how it gets *made* (Process), how it's
*organized* (Structure), and how it stays true over time (Governance). A content
strategy that only covers Purpose is a mission statement; the value is in the
Process and Governance halves that most teams skip.

## The boundary: this is not content design

Be explicit with yourself and your reviewers about the line. `define-content-strategy`
sets the organizational and governance layer — the system content lives in. It
does **not** write the copy for any one surface. That is the `content-design`
skill in the experience-design pack, which decides what a specific landing page or
help article says.

Same split on the UX side. `define-ux-strategy` sets the experience vision; the
journey maps, screen flows, and service blueprints that realize it are the
experience-design pack's work. If you find yourself specifying a screen or writing
a headline, you've crossed out of this pack.

## Sequencing with the rest of the seat

UX and content strategy usually run after the market picture and the OKR cascade,
because the experience vision should serve objectives strategy already committed.
But they don't depend on those artifacts to run — each commits independently. Run
them when design is the next thing that will happen and you want it pointed in one
direction.

## See also

- [Cascade OKRs into the shaping queue](cascade-okrs-into-the-shaping-queue.md) — the objectives the UX measures should link to.
- [Run a market and competitive analysis](run-a-market-and-competitive-analysis.md) — the market picture the experience vision serves.
- [Frameworks and artifacts](../reference/frameworks-and-artifacts.md) — the complete skill-to-artifact map.
- [Why strategy is its own seat](../explanation/why-strategy-is-its-own-seat.md) — the strategy-versus-design boundary in full.
<!-- TODO: link the experience-design pack's content-design skill guide once it exists -->
