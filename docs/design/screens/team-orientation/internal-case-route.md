---
type: screen-flow-brief
screen: internal-case-route
flow: team-orientation
surface: responsive-web
surface-genre: marketing
---

# Screen brief: internal-case-route · agent-ready-repo · surface: responsive-web

# The screen that closes Crossing B

**Entirely new, and the reason it exists is a diagnosed blocker.** A reader who
has understood the operating model on the documentation surface and now has to
convince a budget holder has nowhere to go. `information-architecture`'s own
cross-surface wayfinding check instructs that the absence of a documentation-to-
marketing bridge be flagged as a blocker; the seam artifact identified the same
gap independently as Crossing B. This screen is that bridge.

It is a **marketing-genre** screen reached from the documentation surface. That
is deliberate: the fourth tech-site principle says the documentation surface must
not acquire a persuasion register, so the persuasion happens on a marketing page
the documentation *points at* rather than inside documentation itself.

## Place in the whole

- **Type:** screen-brief
- Journey step(s): future-state Stage 3 (Win buy-in), Stage 5 (Make it the default — renewing the case for a second team or a budget cycle)
- Enters from: **S1 zone 10 (marketing, the reader who is not the installer)** · S3 (needs the internal case) · guide page (needs to sell it internally)
- Exits to: S2 unfurl rendering (shares the artifact) · S1 (back to the whole model)
- Traces to outcome: the champion stops improvising in front of a budget holder
- Surface genre: marketing

## Job

Give a champion what to hand a budget holder, and what to say.

## States

- **success/default:** the only state of the *page*. Static content, no data
  dependency.
- **the canvas's failure and narrow-viewport states are inherited**, because this
  screen embeds S2. It gets the same exit: the semantic ordered list, present in
  the document rather than fetched. An earlier draft declared `error` inapplicable
  here while also showing the canvas, which was a contradiction.
- empty / loading / partial / disabled: not applicable to the page itself.
- permission/denied: not applicable — not gated. Worth noting explicitly: it is
  tempting to gate this behind a form. It must not be, because gating it breaks
  the pasted-link transfer path that is the only observed transfer mechanism.

## Data & actions

- **Shows:** the canvas; the five stations with their real costs; the human
  decision points as the questions a person answers; **what the system refuses to
  do on its own**, which is the budget holder's decisive question and appears on
  no current surface; the tracker's one-way relationship; and the three checkable
  proofs.
- **Actions:**
  - Share the artifact → S2 unfurl rendering. Backing service: link-preview
    metadata plus a raster export. **The raster export does not exist yet.**
  - Return to the whole model → S1. Backing service: static marketing page.
    - Copy a proof link → client-side clipboard. On failure the link stays
    selectable as text, matching S1's degradation for the same component.
  - ⚠ Narrow viewport, or the canvas does not render → S2's text alternative,
    which is present in this document.

**The whole screen's backing service does not exist.** S6 is a new static
marketing page. Named rather than assumed.

## Interaction & behavior

See `interaction-design` enrichment. Minimal by design: whatever a champion
needs must survive being screenshotted, pasted, or read aloud, so no behaviour
may carry information. This is the same constraint the canvas operates under and
for the same reason.

## Copy

Follows `docs/design/copy/marketing-home.md` — this is a marketing-genre screen,
so the four ranked copy goals apply, and **"the refusal up front" is the goal
that dominates this screen specifically.** Its job is the question that ends
these meetings.

`ux-writing` owns the strings. No gate codes.

**One honest caveat carried from the peer audit:** the practitioner literature on
champion enablement holds that generic collateral fails and that finance, an
engineering VP, and IT each need different proof types. This screen is one page
for one audience — the budget holder — reached by the champion. Whether that is
sufficient, or whether the other two audiences need their own, is an open
question at the aesthetic-direction gate. Every source arguing for
per-stakeholder collateral has a client-acquisition incentive, which is why it is
an open question rather than a settled requirement.

## Shared contract — REFERENCE, do not restate

- Design system: `web/src/styles/tokens.css`. **This screen introduces no new
  component** — it reuses S1's entirely.
- Aesthetic direction: `docs/specs/platform-site/aesthetic-direction.md`.
- Navigation / chrome: the marketing header and footer, so a reader arriving from
  documentation lands somewhere recognisably part of the same product.
- Quality floor: WCAG at the level this context requires · reduced-motion ·
  handle-all-states.

## Consistency invariants

- **Reuse, never reinvent:** marketing header, footer, section band, CTA, and the
  canvas. Introducing a component here would be the clearest sign this screen has
  overgrown its job.
- **Must stay consistent with:** S1 (shares every component and the copy
  direction), S2 (embeds it), S3 and guide pages (which link here and must not
  themselves adopt a persuasion register).
- **The load-bearing invariant:** the five station names and the work-lifecycle decision phrasing, identical to S1 and S2. S3's job groups are a separate seven-name axis.
- **The principle-4 invariant:** this screen may be *reached from* documentation
  but must not be *inside* it. If documentation copy starts making the argument,
  the seam has been closed the wrong way.

## Done

- [ ] default state designed
- [ ] every action wired to a named service, including the two that do not exist
- [ ] error/edge flows route to a real screen or state
- [ ] copy in, with the refusal answered explicitly
- [ ] WCAG + reduced-motion honored
- [ ] uses the design system, and introduces zero new components
- [ ] interaction/behavior section enriched
- [ ] not gated behind a form
- [ ] zero gate-code strings
- [ ] design-review clean

### If marketing

- **Hero approach:** statement. Unlike S1, this reader arrives already convinced
  that the problem is real — they were sent here by somebody who believes it. The
  job is conviction and limits, not problem-agitation.
- **Above-fold contract:** a statement headline · a subheadline that adds the
  commitment shape · one primary action, which is *share this* rather than
  *install* · no second action · a proof signal that is checkable · friction
  microcopy naming what the reader is not committing to.
- **Scroll story:** short. One zone for the model, one for the refusals, one for
  the proofs, one for the share. A long page here defeats a five-minute reader.
- **IC-first check:** the reader is the champion, not the budget holder. The copy
  must lead with the champion's recognized problem — *I need something to hand
  over* — rather than addressing the budget holder directly over their shoulder.
