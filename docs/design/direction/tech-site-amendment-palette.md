---
type: creative-direction
scope: amendment
surface: responsive-web
surface-genre: marketing
amends: docs/specs/platform-site/aesthetic-direction.md
builds-on: docs/design/direction/tech-site-amendment.md
status: active
gate: approve-aesthetic-direction — owner-selected in session 2026-09-18; formal gate not separately convened
updated: 2026-09-18
---

# Aesthetic direction — amendment for the register

> **[Superseded 2026-09-18 by `docs/design/direction/marketing-site.md`.]**
> Kept as the record of how the direction reached its current state; it is no
> longer operative on palette or layout.
>
> Two of its decisions were reversed after the owner saw them built. The
> **annotation margin is withdrawn** — "Checked in public" is a sound goal and a
> parallel column was the wrong mechanism for it on a persuasion surface, where
> two columns compete rather than one supporting the other. The **register
> palette is replaced** by a paper-first editorial direction, because the
> green-black ground at 19:1 read as harsh and the counterfactual check found
> the dark-hero-plus-grid-texture structure to be the category default rather
> than a choice.
>
> What survives: the analysis in §1 of why `Identity specificity` was violated
> by the *structure* rather than the hue, the withdrawal of the decorative
> chromatic accent, and the recorded false start showing why monochrome
> restraint was not an answer either.

**This is the second amendment, and the first to reverse a resolved decision.**
The direction is `docs/specs/platform-site/aesthetic-direction.md`. The first
amendment (`tech-site-amendment.md`, gate-passed 2026-09-04) remains in force and
is not restated here; a reader needs all three documents.

The first amendment stated that "the single amber accent … stand[s] unchanged."
**This amendment reverses that**, on owner authorization given 2026-09-18, which
also authorized revising the palette as a whole.

No palette, font, spacing, or timing value appears here. Those are
`design-system`'s.

## Scope boundary — the docs surface is out

**Owner decision, 2026-09-18: `docs-site/` is out of scope for this amendment.**

`docs-site/src/styles/tokens.css` carries its own amber palette, untouched by
this work. That is now a deliberate divergence rather than an oversight, and it
is recorded here so a later cleanup pass does not "finish the job" by extending
the register across it.

**A correction, since an earlier draft of this document cited a rule that no
longer exists.** This amendment first claimed that `docs-site/AGENTS.md`
"forbids aligning docs colour to `web/`'s amber system without a new spec."
**That file carries no palette, colour or token rule today.**

It did when the claim was first written. Commit `8238167a2` (the cobalt-theme
change) added a section headed "Styling: the docs palette deliberately diverges
from `web/`", containing `do not "align" docs colors to web/'s amber system
without a…`. Commit `db5a4ed08`, "docs(agents): simplify every AGENTS.md surface
into a map", removed it. So the constraint was real and the `workspace.toml`
backlog comment that recorded it was accurate when written — it went stale when
that file was simplified, and this document inherited the staleness by citing it
without re-reading the file. Verified against `git log -S` on 2026-09-18.

The real record is `docs/specs/docs-site-design-refresh/disposition-record.md`,
under "Surfaced to the human (open at PR)":

> **Marketing-site palette divergence** — `web/` keeps amber/dark-hero while
> docs go cobalt. Re-skinning `web/` to match is a named follow-on decision in
> the PR description; not executed.

Two things follow, and both matter more than the version this replaces:

- It was never a prohibition on the docs side. It is an open divergence item,
  and its named follow-on ran the **opposite** way — re-skin `web/` to match the
  docs, not the reverse.
- That follow-on is now moot as written, because its premise is gone: `web/` no
  longer keeps amber/dark-hero. The divergence survives, but neither side is
  where that record describes.

The two surfaces were always intended to keep separate palettes (see
`spec/docs-site-design-refresh`), so divergence is the standing position and not
a defect introduced here.

## What this amendment changes

| # | Change | Kind |
| --- | --- | --- |
| 1 | `Identity specificity` is found live-violated by a mechanism its violation clause never enumerated | Compliance, not amendment |
| 2 | The surface gains a derived visual language: **the register** | New requirement |
| 3 | One goal is added: **Checked in public** | New goal, appended at rank 6 |
| 4 | The decorative chromatic accent is withdrawn; chroma is retained only as a clearance mark and as functional state | Reversal of a resolved decision |
| 5 | The canvas loses hue as its decision-node differentiator | Consequence, carried to the canvas brief |

## 1. Identity specificity is violated, and the accent hue was never the reason

The goal names its own violation: *"Looking like 'yet another developer tool
site' (the indigo/purple/teal cluster)."* The original direction then chose amber
explicitly to sit "outside the indigo/blue/teal/purple cluster that saturates the
developer-tool space."

That reasoning located the genericness in the **hue**. It is not in the hue.

The recognized default voice for this genre is a *structure*: dark hero, plus
high-contrast display type, plus one chromatic accent. Amber escaped the named
hue cluster and the surface still assembles the formula exactly — and sets it in
Inter, which the same body of guidance names as "a convention, not a
distinction."

This is the same shape as the first amendment's section 2: a live violation whose
remedy is compliance, not a goal change.

**A recorded false start, because it is the instructive part.** The first remedy
proposed was to withdraw the accent and go achromatic. The owner rejected it on
2026-09-18: monochrome restraint is *also* a convention — Vercel's — so the move
swapped one borrowed default for another and satisfied nothing. `Identity
specificity` does not ask for a different reference. It asks for a language
**derived from the product's nature**. That rejection is what produced section 2.

**Two findings that are falsifiable rather than taste**, both against the
direction's own written claims:

- The direction claims amber "reads as precision, craft, and signal — **not
  danger**." The shipped accent sits ~8° from the token set's own *warning* role.
  A brand colour adjacent to the warning colour cannot carry that claim.
- The direction specifies the dark canvas as "neutral-cool near-black — **not
  navy**." The shipped elevated tiers above that canvas are blue-violet.

Neither is an aesthetic preference. Both are the artifact contradicting its own
direction, which is why they are recorded here rather than as Director's notes.

## 2. The derived language — the register

**What the product makes is records of work having been checked by someone who
was not the one doing it.** Gates that refuse, reviews read cold, evidence, and a
merge decision taken by a person. The visual language is derived from that
output, not from the category's house style.

The surface reads as a **register**: a ruled record of checked work.

Direction-level commitments, all structural rather than decorative:

- **A persistent annotation margin.** The surface carries a margin column that
  holds the receipt for the claim beside it — the change, the date, the fact that
  a person cleared it. This is the load-bearing move. It converts
  `tech-site.md`'s principle *"put verifiable evidence beside every meaningful
  claim"* from an editorial aspiration into a layout rule, and it consumes the
  empty right field that currently runs down every band of the live page.
- **Ruled hairlines are structure, not decoration.** Rules run full-bleed and
  mark record boundaries. They are the grid made visible, and they replace the
  current decorative background texture.
- **Figures align.** Numerals are tabular and lining throughout. A register whose
  columns do not align is not a register.
- **Mono is a field face, not a code face.** It sets record fields — labels,
  identifiers, provenance, timestamps. It stops being a decorative "technical"
  signal applied to chips and eyebrows.
- **Chroma is a stamp.** One clearance mark, and it only ever means a human
  cleared something. Functional state keeps its own set. Nothing else is tinted.

Precedent — what is taken and what is left:

- **Certificates of conformance and calibration certificates** — taking the
  authority a filled-in form carries, and the convention that the record's
  credibility comes from its fields being completed and attributed. Leaving the
  officialese and any literal reproduction of a form.
- **Swiss railway timetables** — taking density with total legibility, and the
  discipline that rules and alignment do the organising work. Leaving the
  transit iconography, which the first amendment already reserves for the canvas
  metaphor and warns against over-borrowing.
- **Tufte's tables** — taking data-ink discipline: every rule, tint and label
  must carry information. Leaving the academic register.

**Deliberately not taken:** paper texture, drop shadows imitating stock, sepia,
typewriter faces, or any other skeuomorphic cue. The register is a *structural*
idea. Any nostalgia treatment would re-borrow a reference and reintroduce the
violation this amendment exists to fix.

## 3. One goal added — Checked in public

Ranked **sixth**. It does not displace or outrank any existing goal. It follows
the precedent the first amendment set at rank 5: a low-ranked goal that wins
specific recorded tensions.

**Checked in public** — means: every load-bearing claim shows its receipt beside
it, as a record field, in the margin. The surface does not assert that work is
checked; it displays the check.

**Violated by:** a load-bearing claim with no adjacent receipt; an annotation
margin filled with decoration, restated copy, or pull-quotes; a receipt that
cannot be followed to a real artifact; chroma used for anything other than
clearance or functional state; a "brand colour" reintroduced on a CTA, eyebrow,
stat numeral or chip.

- *Persona:* the senior engineering lead, pattern-matching for risk in a
  fifteen-second scan, who has read five AI-tool landing pages this week and
  discounts prose by default. A receipt survives that scan; a paragraph does not.
- *Precedent:* certificates of conformance, as above — taking attributed,
  completed fields as the carrier of credibility. Also the first amendment's
  citation of Julia Evans's zines for the still-image discipline: a register
  holds its meaning as a static artifact, which is what Portable whole requires.
- *Standards:* WCAG 1.4.1 Use of Color — with chroma reduced to a clearance mark,
  every chromatic mark is required to carry a label or shape, which this goal
  makes structural rather than a per-element check. Nielsen #8 Aesthetic and
  Minimalist Design — every element competes for attention, so a margin field
  must carry information or be cut. Tufte's data-ink ratio is the same rule
  stated for rules and tints.
- *Platform conventions:* responsive-web. The recognized default voice for this
  genre is dark hero + high-contrast type + single chromatic accent, and a
  direction adopting that vocabulary must name its differentiator. The register
  **is** the differentiator: the margin, the rules and the aligned figures are a
  structure no site in the reference tier uses. Reflow (1.4.10) governs the
  margin's behaviour at narrow widths — see the floor check.

**Why a goal and not just a constraint.** It will lose arguments if it is not
one. The first thing anyone says about a dense ruled page is that it looks
bureaucratic, and the cheapest answers are always to drop the margin and to add
a brand colour. Naming it settles both arguments once, here.

## 4. Consequence — the canvas loses hue as its differentiator

The original direction resolved that the hero visualization carries "amber accent
on gate nodes," and the first amendment carried that constraint forward intact
and load-bearing. **That specific mechanism is withdrawn.** The canvas
distinguishes decision nodes by shape and weight instead, and may use the
clearance mark only where a human decision is what the node represents.

This strengthens the canvas: WCAG 1.4.1 already required decision nodes not to be
distinguished by colour alone, so the shape treatment was owed regardless.
Withdrawing the hue removes the option of skipping it.

Every other canvas constraint from the first amendment stands: static, no
looping, at most a one-shot entrance, and Portable whole's full requirement set.
The rail metaphor is unaffected — a rail line with stations and a register of
checked work are the same document in different projections, which is a point in
the metaphor's favour, not a collision.

## New arbitration — four entries

Added to the existing table; nothing in it is replaced.

| Tension | Winner | Reason |
| --- | --- | --- |
| Grounded ambition vs. Checked in public (a platform-scale visual claim wants the field clear, not ruled and annotated) | **Checked in public** | Grounded ambition is served by scale, structure and type. The empty field it currently produces is the defect, not the ambition; a filled margin reads as more substantial, not less. |
| Staged revelation vs. Checked in public (receipts add density above the fold) | **Checked in public** | The existing table already decides the parent case: *when a specific claim is more trustworthy visible than hidden, surface it.* A receipt is the most specific thing on the surface. |
| Identity specificity vs. Checked in public (a register is a borrowed form too) | **Checked in public** | The form is derived from the product's output rather than from a peer product's house style, which is exactly the distinction the goal draws. The take/leave list in section 2 is what keeps it from becoming a costume. |
| Checked in public vs. the quality floor (density, contrast, or a margin that breaks reflow) | **The floor** | Not a trade-off. Density never buys a contrast or reflow failure; the margin reflows beneath its claim rather than disappearing. |

**Not added, because the existing table already decides them:** any goal versus
the quality floor, and Precision authority versus anything it already outranks.

## Quality-floor check

**Three floor items this amendment carries.**

- **Reflow (1.4.10) governs the margin.** At narrow widths the receipt moves
  beneath the claim it belongs to. It is never dropped, never truncated, and
  never collapsed behind an interaction — a receipt that disappears on a phone
  fails the goal that introduced it. This is the single most likely way to build
  the register wrong.
- **Density is bounded by the reading floor.** A register invites more text per
  band. Line length and leading are held to the typographic floor regardless;
  "it is a dense form" is not a licence to exceed the measure.
- **Focus visibility (2.4.7).** The two scoped focus-ring overrides are recorded
  as deliberate and are not touched. Focus is not expressed through the clearance
  mark, because that mark carries a specific meaning this amendment defines.

**Two contrast disciplines carried forward.** The prior baseline read its ratios
from the token file and recorded that as a scope gap; the first amendment already
caught one optimistic figure that way (recorded ~6.0:1, measured 5.43:1). Ratios
for this palette are verified in a browser. And because hairline rules and field
labels are now load-bearing rather than decorative, they are subject to non-text
contrast (1.4.11) where they carry meaning.

No goal in this amendment pulls against the floor.

## Open questions for the gate

1. **Does the register survive the bureaucratic failure mode?** The risk was
   named when the direction was chosen: a ruled, annotated, field-heavy page
   reads as officialese if the typography is not excellent. The mitigation is the
   explicit not-taken list in section 2 and the data-ink rule. This needs an
   owner's verdict on the first rendered band, not a designer's assurance.
2. **Can every load-bearing claim actually get a receipt?** The baseline found
   that "the five most load-bearing claims are the five with no evidence." If a
   claim has no followable artifact, the goal's options are to cut the claim or
   to cut the margin field — never to fill it with prose. Which claims survive is
   unresolved until the receipts are enumerated.
3. **Inter is a convention, not a distinction.** The recognized guidance names
   Inter and Geist as the de-facto "modern web app" signal. The register leans
   hard on tabular figures and a field-setting mono, so the type decision is now
   load-bearing in a way it was not before. Recorded so it is not lost; re-opening
   the type family is out of scope here.
4. **`docs/design/direction/token-verification.md` is invalidated** by this
   amendment. It verifies the prior token set against the first amendment. It
   needs re-running, not editing.
5. **`docs/specs/platform-site/design-system-foundations.md` mirrors the token
   values** and goes stale the moment the tokens change. It is synced from the
   shipped tokens after `design-system` derives them, not edited in parallel.

## Approval record

**The owner selected this direction in session on 2026-09-18**, choosing "the
register" from three derived candidates (the others were a specification-drawing
language and a refusal language), after rejecting two earlier proposals — the
original amber accent and an achromatic-restraint alternative — on the grounds
that both were borrowed conventions rather than derived languages. The owner
also authorized revising the palette as a whole and directed that implementation
proceed autonomously.

That is a real owner decision and this document is operative on the strength of
it. It is **not** the same thing as the named `approve-aesthetic-direction` gate
having been convened, and this record does not claim it was. What the gate would
still add is an independent verdict on the five open questions below —
particularly the bureaucratic failure mode and whether the register satisfies
`Identity specificity` or merely stops violating it. Treat those as live.

## Governance

The first amendment recorded the owner's Route 1 decision, taken 2026-09-04: the
operative instruction lives in a Living file and the frozen
`docs/specs/platform-site/aesthetic-direction.md` is never edited. **The owner
reversed that on 2026-09-18**, directing that the existing documents be updated
where the recorded choices are the cause of the defect. A superseded banner and
inline `[Corrected]` markers were therefore added to the frozen companion
document, which carries no `Status` field and so is not reached by the freeze
mechanism by its own terms — the same check the first amendment ran.

**One escalation the gate should still rule on.** This amendment reverses a
resolved decision, and the convention says a reversal of part of a shipped
decision points at an **ADR**. Recorded rather than decided, because it is a
governance act and the owner takes it.

## Hand-off

`design-system` next, to derive the token set and scales this direction requires
— in particular the margin column, the rule weights, the tabular-figure setting,
the field-face role for mono, and the single clearance mark — and to re-run
`token-verification.md` against the result.
