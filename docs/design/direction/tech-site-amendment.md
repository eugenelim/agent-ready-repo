---
type: creative-direction
scope: amendment
surface: responsive-web
surface-genre: marketing
amends: docs/specs/platform-site/aesthetic-direction.md
status: active
gate: approve-aesthetic-direction (passed 2026-09-04)
updated: 2026-09-04
---

# Aesthetic direction — amendment for cohort orientation

**This is an amendment, not a direction.** The direction is
`docs/specs/platform-site/aesthetic-direction.md` and it remains in force. Four
ranked goals — Precision authority (dominant), Staged revelation, Grounded
ambition, Identity specificity — the alternating-band surface model, the single
amber accent, and the resolved decisions on colour mode and hero animation all
**stand unchanged**. None is restated here; a reader needs both documents.

No goal is re-ranked. That is deliberate: three of the three findings below turn
out to be resolvable *inside* the existing arbitration rather than by changing
it, and the fourth adds one goal without displacing any.

No palette, font, spacing, or timing value appears here. Those are
`design-system`'s.

## What this amendment changes

| # | Change | Kind |
| --- | --- | --- |
| 1 | The specified hero visualization is restated as owed, and its scope grows into the operating-model canvas | Unbuilt decision, now larger |
| 2 | Staged revelation's own named violation is confirmed live, and the remedy is a section reorder, not a goal change | Compliance, not amendment |
| 3 | The canvas gets a named metaphor | New requirement |
| 4 | One goal is added: **Portable whole** | New goal, appended at rank 5 |

## 1. The specified visualization was never built, and it is now the centrepiece

The existing direction records a resolved decision: the pipeline visualization is
a static SVG with amber accent on the gate nodes, one-shot entrance acceptable,
continuous looping refused — grounded in a cited comprehension study.

What shipped is a row of HTML pill spans containing internal gate codes, marked
`aria-hidden`. The approved mechanism is absent and its placeholder is the page's
worst accessibility and vocabulary defect at once.

**The amendment is scope, not principle.** The decision was right and is
unchanged; the element it describes grows from a three-node pipeline strip into
the two-level operating-model canvas. Every constraint the original decision set
— static, no looping, at most a one-shot entrance, accent on the decision nodes —
carries over intact and is now *load-bearing* rather than merely preferred,
because the canvas's binding rendering context cannot animate at all.

- *Persona:* the adoption champion, whose job is transfer. Grounding is a
  **measured referral path**: a repository link arriving through the Microsoft
  Teams referrer drew 12 unique visitors in fourteen days, against 6 referred by
  the entire published site. That the sender was a champion is an inference the
  instrument cannot support.
- *Precedent:* Neo4j's graph-visualization hero — taking the principle that the
  hero's concept *is* the product's structure, so decoration and explanation are
  the same object. Leaving its customer-logo saturation strategy, as the original
  direction already does.
- *Standards:* the original's own citation against looping animation stands. Added:
  WCAG 1.1.1 and 1.4.1 now bind this element, because it carries information no
  adjacent text carries.
- *Platform conventions:* responsive-web. The original noted SVG and CSS
  animation were viable for this element. **That is now false for one of its three
  renderings** and is the substantive factual correction in this amendment.

## 2. Staged revelation's named violation is live — and needs no goal change

The Staged revelation goal names its own violation: *"Fourteen packs presented as
equal-weight choices before the visitor has decided to care."* Seven equal-weight
outcome cards are the third section on the live page, above the problem statement.

The goal is not wrong. It is not being kept. The remedy is to move the problem
statement above the outcome router, which is a section reorder, and the
information architecture already specifies it.

**One apparent conflict, already resolved by the existing arbitration.** The
canvas puts the *whole* model above the fold, and Staged revelation says
complexity should earn its way in by scrolling. The existing arbitration table
already decides this: *Staged revelation vs. Precision authority — Precision
authority wins; when a specific claim is more trustworthy visible than hidden,
surface it.* The model's coherence **is** the claim here, and staging it would
destroy the thing being claimed.

So no new arbitration rule is needed for the canvas's placement. The dominant
goal already licenses it. Recording this rather than inventing a rule is what
keeps the amendment small.

The canvas also does not trip the goal's stated violations: it is one object at
low resolution, not a dense bullet list and not a set of equal-weight choices.

## 3. The canvas gets a named metaphor

New requirement, because the existing direction specified a *treatment* (static
SVG, accent on decision nodes) without a *concept*, and the element has grown to
the point where treatment alone cannot carry it.

**A rail line with five stations, where the second station is a depot that work
cycles through.** The full mapping, and its three stated limits, are in
`docs/design/screens/team-orientation-canvas.md` and are not restated here.

- *Persona:* the champion again, plus the platform lead — whose decisive question
  is whether the system writes back to their tracker. The metaphor answers it
  with a spur that ends at a buffer stop, so the one-way property is readable
  from the geometry rather than from a caption.
- *Precedent:* Maggie Appleton's framework for drawing invisible concepts —
  taking the ordering that metaphor is the load-bearing layer and colour is
  elaboration. Leaving the hand-drawn register, which would fight Precision
  authority.
- *Standards:* metaphor inversion — applying polish before the metaphor is
  established — is the named failure mode this requirement exists to prevent.
- *Platform conventions:* responsive-web. Replace-at-breakpoint rather than
  viewBox scaling, because a text-bearing diagram scaled down is the named
  near-universal mobile failure.

**How this serves Identity specificity rather than fighting it.** Rail
iconography is well-worn in technical marketing, and the goal warns against
borrowing a reference wholesale. The identity here comes from three things the
product actually has and no transit map does: the buffer stop, the decision
signals, and the depot nesting. The requirement is therefore that the metaphor be
derived from the product's structure — which is precisely what Identity
specificity asks — and **not** that it imitate any named transit system's
styling. That distinction is the whole of the goal's application here, and it is
the open question the gate should rule on.

## 4. One goal added — Portable whole

Ranked **fifth**. It does not displace or outrank any existing goal.

**Portable whole** — means: the artifact that carries the model stays whole when
it leaves the page. It must be legible with no interaction, no script, no
stylesheet, and no animation, because the measured transfer path takes it into
contexts that provide none of those.

**Violated by:** meaning carried by hover, focus, scroll position, or client-side
script; presentation held in a stylesheet or classes rather than in element-level
attributes; a composition whose small static form is illegible; a diagram that
looks finished in the authoring context and strips to nothing in a sanitising
pipeline.

- *Persona:* the champion, transferring by pasted link. The **referral path is
  measured**; the attribution to a champion is not. The constraint holds either
  way, because it follows from where links get pasted rather than from who pastes
  them.
- *Precedent:* Julia Evans's zines — taking the discipline that the artifact is
  complete as a still image, because that is the only form it ever has. Leaving
  the informality.
- *Standards:* GitHub's Markdown sanitiser strips `<style>` blocks inside SVG,
  `class`, `id`, `<script>`, and `<foreignObject>`, and plays no animation of any
  kind. Link previews on every major chat platform require a raster image, and
  Slack fetches only a small prefix of the page, so the text payload outweighs
  the picture.
- *Platform conventions:* responsive-web, plus two non-web rendering contexts the
  original direction did not contemplate.

**Why a goal and not just a constraint.** It behaves as a constraint on one
element rather than a page-wide aesthetic aim, and it was tempting to record it
that way. It is a goal because it will lose arguments if it is not one: every
instinct Grounded ambition encourages — display-scale type, full-bleed sections,
a platform-sized visual claim — pushes toward a canvas that cannot survive a
sanitised render. Naming it means that argument is settled once, here.

**Its scope is bounded, and stated so it is not over-applied.** Portable whole
governs the canvas and any future artifact intended to leave the page. It does
**not** govern the rest of the marketing surface, which may freely use hover,
motion, and stylesheets. Reading it page-wide would be a misapplication.

## New arbitration — two entries only

Added to the existing table, not replacing it.

| Tension | Winner | Reason |
| --- | --- | --- |
| Grounded ambition vs. Portable whole (a platform-scale visual claim that cannot survive a sanitised static render) | **Portable whole** | The constraint is a hard property of the destination, not an aesthetic preference. A canvas that looks like a platform and breaks in the README fails the reader who is most likely to meet it there. |
| Identity specificity vs. Portable whole (a distinctive treatment that needs a stylesheet to read) | **Portable whole** | Distinctiveness that only exists in one of three renderings is not identity; it is decoration in two of them. Identity must be carried by structure, which survives. |

**Not added, because the existing table already decides them:** Staged
revelation versus the canvas above the fold (Precision authority wins, and see
section 2), and any goal versus the quality floor (the floor wins, and it is not
a trade-off).

## Quality-floor check

The direction must not fight the shared quality floor, and accessibility is not
negotiable against aesthetics.

**Portable whole and the floor point the same way, which is the useful finding.**
Because meaning may not depend on interaction, the canvas needs a complete
non-interactive text form — and WCAG 1.1.1 independently requires exactly that
for a diagram carrying information absent from adjacent text. The mobile
replace-at-breakpoint artifact, the screen-reader text alternative, and the
render-failure fallback are one artifact serving three jobs. Build it once.

Two floor items the amendment carries, both corrected against measurement:

**The accent roles invert by carrier, and the canvas sits on the dark one.** The
original direction resolved the light-ground case: the display accent fails the
body-text requirement there and a text-safe accent is used instead. On the **dark
hero carrier**, where IA zone 1 places the canvas, the reverse holds — the display
accent passes as text and as a meaningful mark at 8.07, which is its documented
role, and the text-safe accent **fails** as text at 3.41. The canvas therefore
uses the display accent for every accent mark and white neutrals for all text.

**A measured correction to the original's own figure.** It records the text-safe
accent as "verified ~6.0:1" on the light ground. Measured: **5.43:1**. It still
passes and no arbitration changes, but the figure in the frozen document is
optimistic — and because Route 1 leaves that document unedited, the correction
lives here, in the operative one.

No goal in this amendment pulls against the floor. Nothing to record as an
unresolved floor tension.

## A governance note the gate needs

The document this amends sits in a **Shipped** spec directory
(`docs/specs/platform-site/`) as one of its *Constrained by* artifacts.

Checked rather than assumed: only `spec.md` and `plan.md` in that directory carry
a `- **Status:**` field. The convention's freeze mechanism works exclusively
through that field — a Status-line supersession pointer is the only edit a frozen
document accepts, and an append counts as a body edit. `aesthetic-direction.md`
carries no Status field, so the mechanism does not reach it by its own terms.

That makes amending the original defensible but not obviously licensed, so this
amendment is a separate Living artifact and the original is untouched. Landing it
into the owning source is a governance act, and the convention says a reversal of
part of a shipped decision points at an **ADR**, not at a spec. Two clean routes:

1. Keep this amendment as the operative document and reference it from the point
   of use — which is what the convention prefers, since it says the operative
   instruction should live in a Living file rather than in a patched frozen
   record.
2. Raise an ADR for the amendment and add a Status-line pointer to the spec.

**Route 1 is the owner's decision, taken 2026-09-04.** This amendment remains the operative Living document, referenced from the point of use; `docs/specs/platform-site/aesthetic-direction.md` is never edited. That is what the convention prescribes — the operative instruction lives in a Living file rather than in a patched frozen record — and it keeps the frozen record honest. No ADR is raised and no Status-line pointer is added.

**One consequence to carry into the build handoff:** because the frozen document is unedited, a reader who arrives there first sees the original direction with no pointer to this amendment. The convention accepts that residue explicitly. The mitigation is that the operative reference sits at the point of use — so the build handoff and the canvas brief must both cite this amendment, not the original alone.

## Open questions for the gate

1. **Does the rail metaphor survive Identity specificity?** It is well-worn. The
   mitigation is that identity comes from the buffer stop, the signals, and the
   depot nesting rather than from transit styling. This needs an owner's verdict,
   not a designer's assurance — and a vague answer here is a rejection, so: the
   question is whether *that specific mitigation* is sufficient.
2. **Can one canvas serve four audiences?** Practitioner literature on champion
   enablement holds that per-stakeholder collateral is required and generic
   collateral fails. Our position is that the canvas is the shared model and the
   per-audience answers are entry points into it. Untested, and every source
   arguing the other way has a client-acquisition incentive.
3. **Is the raster export path in scope?** Portable whole's third rendering needs
   one and it does not exist. It is a pipeline change, not a design artifact.
4. ~~**Route 1 or route 2** for landing this amendment.~~ **Resolved: Route 1**, 2026-09-04.

## Hand-off

`design-system` next, to verify the existing token set against this amendment and
derive only what Portable whole genuinely requires — which should be very little,
since the constraint pushes toward fewer expressive mechanisms rather than more.
