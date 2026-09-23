---
type: creative-direction
slug: "marketing-site"
surface: "responsive-web"
date: "2026-09-18"
---

# Aesthetic direction: agent-ready-repo marketing site

**This is the current, consolidated direction for `web/` (surface-genre:
marketing).** It supersedes the amendment chain that preceded it, which stays on
disk as the record of how the direction got here:

| Document | Status |
| --- | --- |
| `docs/specs/platform-site/aesthetic-direction.md` | Superseded. Original four goals; amber accent |
| `docs/design/direction/tech-site-amendment.md` | Carried forward. Adds the operating-model canvas and **Portable whole** |
| `docs/design/direction/tech-site-amendment-palette.md` | Superseded on palette and layout. Introduced the register and **Checked in public** |

Nothing approved in those documents is silently dropped. What changed, and why,
is in the Counterfactual check and the What changed section below.

## Audience (ranked)

- **Primary — senior engineering lead evaluating adoption.** When my team is
  already running coding agents unsupervised and I am accountable for what
  merges, I want to judge in about fifteen seconds whether this is a serious
  option my team can own, so that I can decide whether to spend an afternoon on
  it. Cognitive mode: pattern-match, scanning for risk signals.
- **Secondary — the IC who will actually install it.** When someone sends me
  this link, I want the real command and what it does to my repository, so that
  I can try it without committing my team. Cognitive mode: sequential, wants a
  concrete artifact.
- **Tertiary — the champion re-explaining it.** When I have to re-tell this to
  people who will never visit the page, I want one artifact that survives being
  pasted somewhere else. Cognitive mode: transfer. This is the persona
  `tech-site-amendment.md` grounds **Portable whole** in.

## What changed, and why

Three pieces of owner feedback on the built register direction, 2026-09-18:

1. **Pure white on near-black reads too harsh.** Measured 19:1. That is a
   terminal, not authority, and display type at that contrast shimmers.
2. **Padding is off.** The content column was narrower than its container, so
   the right of every band voided. The defect was the measure, not a missing
   column.
3. **The right-margin receipts look out of place, and they cause drift.**

Item 3 is the substantive one. **Checked in public is a sound goal and the
annotation margin was the wrong mechanism for it.** Evidence beside a claim is
right; a parallel column on a persuasion surface is apparatus, and two columns
compete for the same attention instead of one supporting the other. Research run
before building it found *no precedent for an annotation margin on any marketing
page* and could not distinguish "opportunity" from "the reason nobody does it."
The owner's reaction settles that: it is the latter. The goal survives, narrowed
to inline placement; the margin is withdrawn.

## Named goals (ranked)

1. **Precision authority** *(dominant)*
2. **Identity specificity**
3. **Staged revelation**
4. **Grounded ambition**
5. **Portable whole**
6. **Checked in public** *(narrowed — see below)*

Identity specificity is promoted above Staged revelation and Grounded ambition.
It has now been violated twice by the same mechanism — adopting the category's
default structure — and a goal that keeps losing needs to outrank what beats it.

## What each goal means

- **Precision authority** — means: the surface reads as built by people who are
  exactly right about the problem; every claim is specific and traceable.
  Violated by: superlatives, vague claims, decoration standing in for content.
  - *Persona:* the senior lead, fifteen-second scan, already sceptical of AI claims.
  - *Precedent:* Stripe marketing — taking conviction-led copy and total accuracy; leaving its pure-light chrome-free treatment. Linear — taking specificity over illustration; leaving the single-accent formula.
  - *Standards:* Nielsen information-scent; Hemingway's iceberg — specifics over adjectives.
  - *Platform conventions:* responsive-web; no platform constraint on precision.

- **Identity specificity** — means: the visual language is derived from the
  product's nature, not borrowed from the category. Violated by: adopting the
  genre's default structure whatever the hue; substituting one borrowed
  reference for another.
  - *Persona:* the visitor who has seen five AI-tool landing pages this week.
  - *Precedent:* the editorial-broadsheet preset — taking rules as structural devices, strong type hierarchy as the navigation system, and explicit story ranking; leaving the five-column grid, the photographic treatment, and the feed-like density.
  - *Standards:* recognized guidance names dark hero + high-contrast type + one chromatic accent as the genre's default voice, and names Inter and Geist as "a convention, not a distinction." A direction adopting that vocabulary must state its differentiator.
  - *Platform conventions:* responsive-web. The differentiator is the ground and the display voice: paper-first with a serif display, against a category that is sans-on-dark almost without exception.

- **Staged revelation** — means: above the fold makes one claim; complexity
  earns its way in by scrolling. Violated by: many equal-weight choices before
  the visitor has decided to care; a dense list above the fold.
  - *Persona:* the same lead mid-scroll, now evaluating fit rather than orienting.
  - *Precedent:* Linear — taking sequential staging of one idea per section; leaving the product-screenshot cadence.
  - *Standards:* Miller's Law (chunking); Hick's Law at decision points.
  - *Platform conventions:* responsive-web; progressive disclosure is first-class and mobile-first makes staging load-bearing.

- **Grounded ambition** — means: the language makes a product-platform claim,
  not a document claim. Violated by: framework defaults visible on the marketing
  anchor; document-scale type.
  - *Persona:* any first-time visitor.
  - *Precedent:* the editorial-broadsheet preset again — taking display-scale confidence; leaving the broadsheet's density.
  - *Standards:* display type scale via `clamp()`; optical sizing where the face offers it.
  - *Platform conventions:* responsive-web; `prefers-reduced-motion` governs any entrance.

- **Portable whole** — means: the artifact carrying the model stays whole when
  it leaves the page — legible with no interaction, script, stylesheet or
  animation. Violated by: meaning carried by hover, focus, scroll or script;
  presentation held in a stylesheet rather than element attributes.
  - *Persona:* the champion transferring by pasted link. Carried unchanged from `tech-site-amendment.md`, including its measured referral-path grounding.
  - *Precedent:* Julia Evans's zines — taking the discipline that the artifact is complete as a still image; leaving the informality.
  - *Standards:* GitHub's Markdown sanitiser strips `<style>` inside SVG, `class`, `id`, `<script>` and `<foreignObject>`, and plays no animation.
  - *Platform conventions:* responsive-web plus two non-web rendering contexts.

- **Checked in public** *(narrowed)* — means: a load-bearing claim shows its
  evidence **in the reading path**, directly beneath the sentence it supports,
  as a quiet mono line. Violated by: evidence in a parallel column or any
  apparatus beside the text; a receipt that cannot be followed to a real
  artifact; prose dressed as evidence; filling the field because it looks empty.
  - *Persona:* the senior lead, who discounts prose by default and will read one short attributable line.
  - *Precedent:* the editorial-broadsheet preset's byline and caption conventions — taking the convention that attribution sits immediately under its content; leaving the multi-column story furniture.
  - *Standards:* WCAG 1.3.2 Meaningful Sequence — inline placement makes reading order and visual order the same thing by construction, which the margin had to work to preserve.
  - *Platform conventions:* responsive-web. Inline evidence needs no breakpoint behaviour, which removes the reflow risk the margin carried.

## Owner decisions, 2026-09-18 — the two retrofit blockers

A brownfield inspection before the retrofit found two contradictions that had to
be settled before any component was written. Both are recorded here because
either one, decided late, means rewriting components.

### The mark means state, and nothing else

An earlier draft of this direction permitted the mark on rules and eyebrows.
That contradicted an invariant already shipped in `tokens.css`, which states in
two places that chroma means clearance and functional state only, and that the
accent tokens having no consumer **is** the invariant rather than a gap.

**Resolved: the mark is reserved for state — a refusal, a hold, a block.**
Eyebrows take `--ds-field-label`; eyebrow and section rules take the neutral
rule tokens. The direction sheet's Chromatic intensity row is amended to match,
and no amendment to the `tokens.css` invariant is needed, because the narrower
rule does not violate it.

The reasoning is the one the register palette already taught us and this
document nearly repeated: in the built preview the mark had **two jobs** —
decorating eyebrows and marking `HELD`. Two jobs is precisely how the amber
accent failed, and the alternative on the table ("chroma means something, or
it's an eyebrow") is the rationalisation that would have reopened it. One job
also makes the refusal the loudest thing on the page, which is the product's
central claim.

### "Own the catalogue" is a light band, not part of the close

**Owner decision, 2026-09-18 (later the same day).** The closing band —
organisation-level catalogue ownership — was built dark and continuous with the
footer. It moves to the **light alternate ground**, as a band in its own right.

The commitment in Section and scroll rhythm is unchanged and this is why the
change is admissible: the dark ground still appears **exactly once**, and the
band that carries it is the footer. What changes is which element is "the
close." Previously the closing content band and the footer merged into one dark
mass; now the content band is a call-out with its own job and its own ground,
and the footer alone is the close.

The reason is that merging them cost the band its job. A call-out that dissolves
into the site furniture beneath it reads as furniture. Its content — the end
state for an organisation rather than an individual — is the page's last
substantive claim, and it needs to be legible as a claim.

### The nav and footer move to paper

Both `--ds-focus-ring` override blocks in `tokens.css` exist only because their
eleven listed carriers are dark. On paper a white ring measures about **1.1:1**
— every focus indicator in the hero would silently disappear, and no gate in the
suite catches it.

**Resolved: the whole page is paper; the dark ground appears exactly once, at
the close, with the footer continuous with it.** That is what the Section and
scroll rhythm row already commits to, so the alternative — dark nav bracketing a
paper page — would have broken a commitment this document makes elsewhere.

Both ring blocks are **re-derived per carrier and measured**, not edited in
place: ink on paper carriers, off-white on the dark close. A ring inherited from
a block whose premise has changed is the defect this decision exists to prevent.

### The press state is a ground shift — owner decision, 2026-09-23

**Resolved: a press moves the control's ground, and that is the whole idiom.**
One behaviour across every control, because a surface whose controls each press
differently is worse than one that does not press at all.

The direction made the usual answer illegal, and that is the reason this needed
a decision rather than an implementation. Containment is `[ruled]`, Material is
`[flat]`, Ornament is `[none]` — so transform, scale, shadow and every other
elevation cue is out, and a press state normally uses one of those. What is left
is a shift of ink, of rule weight, or of ground. Ground was taken because it is
the only one available to all three carrier kinds without changing the box: ten
of the controls carry no rule to thicken, and several already move their ink on
hover, so an ink shift would have had nowhere left to go on them.

Three tokens, chosen by the control's own carrier rather than by a list of class
names:

| Carrier | Token | Value | Measured |
| --- | --- | --- | --- |
| hover ground is already ink | `--ds-cta-primary-bg-active` | `--prim-record-700` | text 10.03:1 |
| the dark close band (two carriers) | `--ds-surface-pressed-dk` | `--prim-ink-700` | text 6.76:1, ground shift 1.94:1 |
| everything else | `--ds-surface-pressed` | `--prim-record-200` | text 10.03–13.16:1 |

**The paper ramp gains `--prim-record-700` and `--prim-record-250`.** The ramp
jumped 600 to 800, so an ink-filled control had no step beyond its hover fill;
and the pressed ground could not be `record-200`, which is `--ds-border`'s value
— two controls whose hover already set `--ds-border` rendered no press at all.
Both are additions to what this document calls the measured set from the
approved preview, and they are recorded here for that reason.

**The rule is one direction, not two: every press moves its ground toward
mid-tone.** Measured relative luminance, rest to pressed: paper 0.914 → 0.587,
the alternate band 0.840 → 0.587, an ink-filled control 0.006 → 0.046, the dark
close band 0.006 → 0.059. Each moves toward the middle and away from the extreme
it sits at, which is the only direction available at the ends of the ramp. Read
as lightness alone it looks like two rules — paper darkens, ink lightens — and an
earlier draft of this section described only the ink case, which invited exactly
that misreading.

**The dark band is the weak case, deliberately.** 1.94:1 is the strongest ground
shift that ramp affords while keeping footer link text above 4.5:1.
`--prim-record-600` would give 3.24:1 against the ground and drop the text to
4.06:1. The press is quieter at the close than on paper, measurably rather than
accidentally.

**Two controls raise their ink as well, and only because the floor demands it.**
The two on `--ds-state-warn-bg` have no headroom: `record-200` leaves them at
3.64:1, `orange-300` at 3.07:1, and the only ground that keeps them legible is
the panel's own colour, which is no press at all. They take the paper ground with
the ink raised. This document's own arbitration rule settles it — when any goal
conflicts with the quality floor, the floor wins.

**Under forced colors the press does not survive — and neither does hover.**
Measured in Chromium's `forced-colors: active` emulation on 2026-09-23: on
`.nav__link`, `.nav__cta`, `.hero__cta--primary` and `.footer__list a`, the
hovered computed style is identical to the resting one. Every transient state on
this surface is carried by colour, and forced colors reassigns
`background-color`, `color` and `border-color` alike, so the whole layer is
erased rather than the press specifically. No WCAG success criterion requires
hover or press feedback to be perceivable under forced colors — 2.4.7 and 2.4.13
govern focus only — and the practitioner literature on forced colors develops
its survival pattern for focus indicators exclusively, without treating hover and
press as separate cases. Giving the press a forced-colors channel while hover has
none would make a press louder than a hover for one cohort and quieter for every
other, so the boundary is recorded here rather than closed on one side of it.
Focus is unaffected: its ring is re-derived per carrier and measured.

**The mark is not reachable from here.** `--ds-clearance` means a refusal, a hold
or a block. A press is none of those, and a third consumer would make the mark
mean "state, and also this", which is how the amber accent failed.

**The magnitude is deliberate, and it is above the category's.** A press state
is not required by any accessibility standard: WCAG 2.2 mandates a visible
indicator for focus (2.4.7, and 2.4.13 at AAA) and for nothing else, and of ten
surveyed design systems none frames press feedback as a conformance requirement
— every accessibility statement in their own documentation is about focus.
1.4.11 Non-text Contrast names press as a state, but its test is the component
against the colours adjacent to it, not one state against another; the
state-to-state reading is refused explicitly for hover in the Understanding
document and by a working-group editor for `:active`. That test passes here by
construction, because no press rule changes a border: a ghost button's edge
measures 3.53:1 against the page at rest and 3.53:1 while pressed, and a filled
control's own fill moves 17.16:1 to 10.03:1, both far above the floor.

For scale, the press layer four independent vendors converge on — Adobe
Spectrum, Microsoft Fluent 2, IBM Carbon and Google Material 3 — is a further
step along the same axis hover already moved, which is exactly the shape this
direction takes. Material 3's pressed state layer is a 10% overlay, which
computes to about **1.17:1** against a white ground. This surface's paper press
measures **1.51:1**. The press here is quieter than a shadow and louder than the
category's own answer.

**Refused: closing this as "not wanted on a `[flat]` surface".** That was a real
option. It was not taken because the surface's dominant goal is Precision
authority, and a control that does not acknowledge being pressed is imprecise in
the one moment the reader is acting rather than reading.

## Direction sheet

| Axis | This direction commits to |
| --- | --- |
| Grid grammar | `[manuscript]` `[relaxed]` One reading column at a generous measure. No parallel content track; the annotation track is withdrawn. Transformations may vary the measure, never add a second column of content. |
| Alignment and equilibrium | `[edge]` `[asymmetric]` One dominant left axis. Every element — wordmark, display, deck, controls, fine print, evidence — starts on it. One axis only. |
| Spatial density | `[comfortable]` One information group per screenful; the lead must never share the fold with a menu. |
| Whitespace distribution | `[expansive]` Generous macro margins and section gaps; tight, consistent micro spacing. The open field is the composition, not a gap to be filled — that mistake is what produced the margin. |
| Hierarchy and scale contrast | `[steep]` Serif display dominates; functional sans and mono sit well below it. Two clear jumps, not a ramp. |
| Containment and boundary strength | `[ruled]` Rules divide and rank. No cards, no tinted panels, no shadows, no overlap. A rule is structure; it never decorates. |
| Section and scroll rhythm | `[episodic]` `[regular]` Each band does one job at an even cadence. The dark ground appears exactly once, at the close. |
| Type voice | `[mixed]` Serif display; sans body; mono for every field, command, identifier and piece of evidence. The mono is a record face, not a "technical" flourish. |
| Type hierarchy | `[dramatic]` Display, section head, body, field. Four levels, unmistakably separated. |
| Chromatic intensity | `[restrained]` Paper and ink, plus one mark. **The mark means state and nothing else** — a refusal, a hold, a block. Never an eyebrow, never a section rule, never a fill, never a control, never body text. On the single dark band, ink is off-white, never pure white: 19:1 display type shimmers and reads as a terminal. |
| Form | `[rectilinear]` 2px on fields and chips, 6px on controls and containers. Rules are square. |
| Material and depth | `[flat]` Separation comes from rules, space and alignment. No elevation, no shadow. |
| Ornament and texture | `[none]` No grid texture, no grain, no pattern. The faint hero grid is withdrawn as a category default — see the counterfactual check. |
| Image treatment | `[abstract]` The operating-model canvas is the only image on the surface. No photography, no stock illustration, no decorative figure. |
| Motion character | `[still]` At most a one-shot entrance, guarded by `prefers-reduced-motion`. No looping, ever. |

## Counterfactual check

**Comparator brief:** *"Design the marketing site for a developer CLI tool whose
selling point is safety and governance — it stops before doing anything
irreversible."* This is a real test rather than a convenient one: it shares this
product's audience, its genre, and its central claim, so anything that survives
unchanged is a category default rather than a choice.

| Axis or goal | What the comparator produced | What it became | Why |
| --- | --- | --- | --- |
| Type voice | `[sans-geometric]`, Inter | `[mixed]`, serif display + sans body + mono fields | Recognized guidance names Inter as "a convention, not a distinction." Serif display is the largest departure available in this category. |
| Ornament and texture | `[pattern]` — the faint 28px hero grid | `[none]` | The faint grid is on nearly every developer-tool hero. It reads as texture and functions as a tell. |
| Section and scroll rhythm | `[episodic]` `[regular]`, dark hero → light body → dark close | `[episodic]` `[regular]`, paper throughout, dark **once** at the close | The cadence survives; which ground dominates does not. Inverting it is the structural departure. |
| Chromatic intensity | `[monochrome]` on dark, or one neon accent | `[restrained]`, paper + ink + one ink-red mark | Both comparator outputs are defaults — monochrome-on-dark is Vercel's, neon-accent is everyone else's. |
| Grid grammar | `[column]` `[relaxed]` with a feature column | `[manuscript]` `[relaxed]` | The second column produced observed drift on this surface. Owner-verified, not predicted. |
| Hierarchy: the fold | Dark hero, display sans, two pill CTAs | Paper, serif display, one filled control on the same left axis | The comparator's fold is the genre's fold. |
| **Checked in public** (goal) | Evidence in a right-hand margin | Evidence inline, beneath its claim | The margin is apparatus on a persuasion surface. Also simplifies 1.3.2 and removes the reflow risk. |

**Survived unchanged, and defensible:** `[edge]` `[asymmetric]` alignment,
`[flat]` depth, `[still]` motion, and `[rectilinear]` form. Each is shared with
the comparator but follows from Precision authority rather than from imitation —
and the alternative in each case (centred, layered, expressive, organic) would
actively fight the dominant goal.

## Dominant goal for arbitration

**Dominant goal:** Precision authority.

Resolved trade-offs — new in this direction:

- When **Identity specificity** and **Grounded ambition** conflict on the hero
  treatment, **Identity specificity** wins. A serif display on paper makes a
  smaller platform-scale claim than a full-bleed dark hero; that is the trade
  being taken, because the dark hero is the category's, not ours.
- When **Checked in public** and **Staged revelation** conflict on how much
  evidence appears early, **Staged revelation** wins. Evidence appears with the
  claim it serves, never gathered above the fold.
- When **Checked in public** and **Precision authority** conflict because a
  claim has no followable artifact, **Precision authority** wins: cut the claim
  or leave the evidence line absent. Never fill it with prose.
- When any goal conflicts with the quality floor, **the floor wins.** Not a
  trade-off, not ranked.

Carried forward unchanged from the earlier documents: Precision authority beats
Staged revelation when a specific claim is more trustworthy visible than hidden;
Portable whole beats both Grounded ambition and Identity specificity on the
canvas.

## Open questions

- **Does serif-on-paper read as a technical product, or as a publication?** This
  is the direction's central risk and the reason it is the largest departure.
  The mitigation is that mono carries every field, command and identifier, so
  the technical register is continuous underneath the editorial voice. Needs an
  owner verdict on the first rendered band, not a designer's assurance.
- **Six goals exceeds the three-to-five this method asks for.** The set is
  inherited across three documents and none has been retired by an owner. Worth
  consolidating — but dropping an approved goal is an owner act, not an editing
  convenience.
- **Ink red on paper must be measured, not assumed.** It appears only on rules
  and eyebrows, so it is bound by non-text contrast for the rules and by normal
  text contrast for the eyebrows. Ratios are verified in a browser, never read
  off the token file — an earlier pass recorded "~6.0:1" for a value that
  measured 5.43:1.
- **The canvas now sits on paper, not on the dark ground.** The earlier
  amendment resolved its accent treatment against a dark carrier. That analysis
  is void and must be re-derived, along with whether **Portable whole** still
  holds when the canvas's ground is light.
- **The dark band appears once, at the close.** Confirm that is enough for
  Grounded ambition, and that the off-white ink rule holds there.

## Hand-off

`design-system` next, to derive the token set and scales this direction
requires — the paper and ink ramps, the single mark, the serif display face and
its optical-size behaviour, the mono field face, the rule weights, and the
inline evidence treatment that replaces the withdrawn margin.
