---
type: decision-log
slug: team-orientation-decision-log
status: active
gates_passed:
  - approve-journey (2026-09-04)
  - approve-aesthetic-direction (2026-09-04)
updated: 2026-09-04
---

# Decision log and design rationale

Every decision that would otherwise be re-litigated, with what decided it. No
skill owns this artifact.

## The decisions

### D1 — Adoption dominates; work is nested inside station two

**Decided by:** the design lead, ratified at `approve-journey`.

The unit of adoption is a cohort and the dominant reader is a champion whose job
is transfer, so the reader's job is *get my organisation to take this on*. The
journey's own highest-pain moment is an adoption failure, not a work failure —
the work lifecycle already functions. The work lifecycle is the *evidence* for
the adoption claim, which the second principle wants placed beside a claim rather
than promoted into a competing narrative.

**Independent support found after the decision:** NN/g is explicit that designers
should avoid requiring readers to hold multiple conflicting mental models, and
that the remedy is to teach *one*. The industry's named version is the
inner-loop / outer-loop split, which interfaces at a single handoff rather than
sitting side by side.

**The counter-evidence, recorded rather than buried:** the best-documented
resolution to a dual-audience problem is Stripe's — collapse it by choosing one
audience. That is better evidenced than subordination. Our justification is that
these two lifecycles are genuinely orthogonal, and **that is our assertion about
our own product, not a finding.** If it is wrong, Stripe's route wins.

**Falsified by:** readers describing the work steps as team stages or vice versa,
or being unable to say which contains the other. Kill condition and response are
in the measurement plan.

### D2 — Two disclosure levels, and level two is a page zone rather than a widget

**Decided by:** NN/g's finding that designs beyond two disclosure levels are
typically unusable, plus the sanitised-rendering constraint.

Because the canvas must render as a static image where scripts and stylesheets
are stripped, no part of the model may live behind an interaction. So the work
lifecycle's expansion is a zone in the document, always present, and the canvas
links to it. **Interaction adds emphasis, never information.**

### D3 — The metaphor is a rail line with a depot at station two

**Decided by:** the design lead, ratified at `approve-aesthetic-direction`.

Metaphor is the load-bearing layer and applying polish before it exists is the
named failure mode, so it was named before anything was drawn. The mapping earns
three specific things: a **buffer stop** makes the one-way tracker relationship
readable from geometry; **signals** express human decisions as a shape with no
code; the **depot** makes nesting structural.

Three limits are stated in the spec, not hidden. The owner ruled that identity
coming from the buffer stop, the signals, and the depot nesting — rather than
from transit styling — is a sufficient answer to the Identity-specificity goal.

**Emerged during composition, not specification:** the **change of axis** —
horizontal arc, vertical sequence — does more work than any label. A reader
cannot lose which lifecycle they are in because the two run at ninety degrees.
That was found by drawing, and it is the strongest single element of the design.

### D4 — One canvas with four entry points, tested rather than presumed

**Decided by:** the owner at `approve-aesthetic-direction`, against practitioner
consensus.

Practitioner sales-enablement literature holds that per-stakeholder collateral is
required and generic collateral fails. Every source arguing that has a
client-acquisition incentive and none is independent. The owner chose to ship the
shared model and let the measurement plan's role-stratified comprehension check
falsify it, rather than presume either way.

**Falsified by:** any one role scoring `absent` on the item representing its
central question while champions can answer it from the same artifact. The kill
condition already exists.

### D5 — The install stays the primary action, re-framed as station two of five

**Decided by:** the design lead.

The tension is real: the page's job is Understanding and its conversion happens
off-surface, so sending the reader to a terminal ends the page's contribution.
But the adoption journey records that a champion who has not run it themselves
cannot demonstrate it — station two genuinely precedes station three.

So the action does not change; its *meaning* does. The arc gives the command a
place. The secondary action becomes the route into the ordered paths, for the
platform lead and budget holder who are not the installer.

### D6 — The re-tasked proof band, and the tier this product can actually earn

**Decided by:** the owner at `approve-journey` (re-task rather than cut).

There is no social proof at any tier — no logos, no customer outcomes, no press,
no analyst recognition. Higher-tier proof on a lower-maturity product reads as
fabricated, so the honest tier is **evidence-by-artifact**: one real merged
change, the gate output from that same change, and a generated adapter matrix.

Two constraints: **generated, never pasted**, because a snapshot of a changing
system decays into a false claim; and **never invented**, because the second
principle's own tradeoff says an unshowable artifact gets its boundary named
instead.

### D7 — Documentation navigation groups by job, using vocabulary that already exists

**Decided by:** the owner at `approve-journey`.

The job taxonomy already exists twice — seven job-named outcomes in the marketing
catalogue module and the same seven names in the guides achieve-table. Zero new
vocabulary needed. Six areas serve two jobs each, resolved to one canonical home
with body cross-references rather than duplicate nav entries, because a page under
multiple parents fights breadcrumbs.

**Two corrections to how this was priced at the gate.** The route-identity cost
is essentially **zero** — no URL changes, because grouping and slugs are
independent. But implementing it requires **amending a Shipped spec**, which is a
governance step rather than a data edit. The owner approved the cheaper cost and
should know about the larger one.

### D8 — The amendment stays a Living artifact; the frozen direction is untouched

**Decided by:** the design lead; route confirmed by the owner on 2026-09-04.

Only `spec.md` and `plan.md` in the platform-site spec directory carry a Status
line, and the freeze mechanism works exclusively through that field — so the
aesthetic direction is not reached by the rule. Amending it in place would
nonetheless change a constraint a shipped implementation was built against, and
the convention explicitly prefers the operative instruction to live in a Living
file rather than in a patched frozen record. So the amendment is separate and the
original is unedited.

### D9 — Zero new semantic tokens

**Decided by:** measurement. Every role the canvas needs already exists among the
97. One component-tier set, following the existing focus-ring override pattern.

A verification pass that had ended up adding tokens would have been evidence the
amendment was misread.

## What the cold review changed

The evidence-audit review returned **16 findings and all 16 were sustained** —
verified against the repository rather than accepted on the reviewer's word. Two
were checked personally before adoption because they were the most consequential.

**The two that mattered most:**

**A false public claim.** The internal-case screen's third refusal read *"It will
not write status back into your tracker."* That is **false** — the repository
documents a narrow, human-confirmed coordination write-back to Jira. The real
invariant is directional: the repository holds truth and status does not flow
*from* the tracker *into* the work. The canvas's own wording was already right;
the copy had reversed it. This is the finding that would have shipped a
verifiably untrue statement to a budget holder.

**An invariant that could not hold.** The packet declared that the five adoption
station names were also the documentation job groups. They are not — five
stations answer *how far along is this team*, seven job groups answer *what does
this reader want to achieve*. Different axes, different counts. The invariant was
restated to name what actually crosses the seam: the work-lifecycle decision
phrasings and the seven job names.

**The rest, by class:**

| Class | Findings | Examples |
| --- | --- | --- |
| Overstated evidence | 3 | referral data promoted into observed champion intent; "most people" for 46 per cent; a stage tagged observational whose emotions are assumed |
| Wrong counts | 4 | 92→91 how-to files; 13→9 generated files; 20→21 of 22 areas; nine→eight work steps |
| Cross-artifact contradiction | 5 | three different six-state sets; two different third proofs; two names for one hero approach; membership parity that had already drifted; a stale route-identity price |
| Self-contradiction | 1 | the projection-boundary brief told authors to edit a generated file |
| Incomplete self-correction | 2 | a contrast figure and a route-identity claim survived in older artifacts |
| Over-claimed sourcing | 1 | "labels derived, never invented" was true of three labels out of thirteen |

**What this says about the packet.** Every one of these was introduced by writing
twenty confident artifacts over many steps, and none was caught by the authoring
skills. Long internally-consistent-sounding prose is where unearned claims hide,
and the only thing that found them was a reviewer with a verification lens and no
stake in the conclusions.

**What it says about the thread**, honestly, in both directions: the thread
*produced* these defects and the thread *caught* them. A shorter process would
have produced fewer artifacts and therefore fewer contradictions — but it would
also not have had a cold evidence audit, and the false tracker claim would have
shipped.

## Corrections this engagement made to its own earlier claims

Recorded because a packet that hides its corrections cannot be trusted about
anything else.

| Claim | Correction | Found by |
| --- | --- | --- |
| `--ds-focus-ring` is declared twice — a defect | One `:root` default plus two deliberate documented scoped overrides. Not a defect. | Own re-check before asserting |
| The token baseline is 90 | 97 unique semantic tokens over 50 primitives | Measurement |
| The gate-code rule is the fourth principle | It is a durable application of the first; the fourth is "preserve each surface's reading mode" | Reading the principles |
| The transition table has 28 rows | 27 | Machine check of own claim |
| Text-safe accent measures ~6.0:1 | 5.43:1 | Own contrast computation |
| Re-grouping carries a route-identity cost | No URL changes; the real cost is a Shipped-spec amendment | Reading the generator |
| The unfurl needs a raster of the canvas | The text payload does more work; a chat client reads a small prefix | Peer audit |
| The enclosure and the arc are correctly ranked | The enclosure dominated, inverting the rank | **Rendering the SVG and looking at it** |
| "Two pages stapled together" is a named anti-pattern | It is our phrase for a real risk; not in the IA/UX canon | Peer audit |
| Plus the 16 review findings above | — | Cold evidence audit |

The rendering entry is the one worth dwelling on: the defect was invisible in the
specification, which said the right thing, and obvious in the raster. Two defects
were found that way.

## Gaps recorded

A gap in our own packs is a finding about the pack, not a failure of the work.
A–D were named in the engagement; E–J were found during it.

| Gap | What is missing |
| --- | --- |
| A | No skill gathers primary evidence, and `journey-mapping` admits one `evidence-level` for a whole map |
| B | No skill owns a cross-surface journey; all seven genre scaffolds are per-surface |
| C | No skill designs an explanatory information graphic |
| D | No skill validates comprehension after ship |
| E | No design skill knows about build-time projection boundaries — and this packet fell into that trap itself |
| F | No skill reconciles a stale prior design spec against shipped reality |
| G | `[design] output_dir` is unconfigured, so `experience-status` cannot see any of this |
| H | `information-architecture` declares a read-first dependency on two skills the standard packet places downstream of it |
| I | No skill covers an acquisition surface whose conversion is made off-surface by a third party |
| J | No skill writes the marketing headline — `copy-direction` names goals and stops, `ux-writing` excludes positioned copy |

Gap J is the sharpest: the thread can fully specify the most important string on
the page and cannot produce it.

## Still open

1. **The champion interview has not run.** It is the only primary evidence in the
   engagement and every emotion and pain stays assumption-based until it does.
2. **Who writes the headline** (Gap J).
3. **Who defines "pack" in plain words, and where** — unfamiliar product
   vocabulary in navigation on both surfaces, and the plain-language floor bars it
   until defined.
4. **Does the self-serve reader survive the copy direction?** *Sayable in a
   meeting* optimises for a reader who has a meeting; a solo engineer has none.
5. ~~Route 1 or route 2 for landing the aesthetic amendment.~~ **Resolved: Route 1.** The amendment stays Living; the frozen direction is unedited; both the build handoff and the canvas brief must cite the amendment rather than the original alone.
6. **The three search placeholder queries** must be verified against the live
   index, and the "4 minutes" read time either measured or cut.
7. **The sanitiser probe** — the canvas's binding constraint is read from
   documentation and owed a real render in a real README.
