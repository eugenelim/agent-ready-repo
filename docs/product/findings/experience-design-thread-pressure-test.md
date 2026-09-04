# Finding: does the declared experience-design thread beat ad-hoc design?

- **Status:** Partial — the thread half is measured; the blind comparison did not run
- **Date:** 2026-09-04
- **Subject:** the `experience-design` pack's five-phase, three-gate thread
- **Engagement:** cohort orientation redesign of the marketing home and documentation guides surfaces
- **Artifacts:** `docs/design/` (38 files), `docs/design/screens/team-orientation/operating-model-canvas.svg`

## The test that was designed, and what actually happened

The operator held a sealed control: two independent ad-hoc designs of the same
problem, produced with no pack thread. The protocol was to produce the thread's
recommendation first, then compare all three blind with a fresh reviewer that had
seen none of them.

**The thread half ran to completion. The control was never delivered into the
session, so the blind comparison did not happen.** The operator approved sending
it and it did not arrive; the session continued rather than blocking. No
comparison verdict is available, and none is invented here.

What follows is therefore **one arm of a two-arm test**. It is still a finding,
because several of its measurements do not depend on the comparison.

## What the thread cost

| Measure | Value |
| --- | --- |
| Wall-clock, first read to gate 3 request | **~2 h 35 min** |
| Phases run | 5 (Discover, Define, Design, Validate, Handover) |
| Human gates | 3, plus 2 mid-course decisions = **5 human interactions** |
| Artifacts produced | **38 files, ~8,500 lines of markdown, 1 hand-authored SVG** |
| Skills invoked | 11 (`journey-mapping` ×3, `design-review`, `desk-research`, `content-design`, `copy-direction`, `tone-of-voice`, `information-architecture`, `user-flow`, `conversion-design`, `documentation-design`, `creative-direction`, `design-system`, `ux-writing`, `interaction-design`) |
| Subagents | 3 evidence retrievers (~124k tokens), 1 `experience-reviewer` (175k tokens, **42 min**) |
| Codex worker sessions | 5 (capability probe, content inventory, measurement plan ×2, evidence-audit review) |
| Worker sessions that failed and needed recovery | **1** — blocked by a policy refusal on the repository's own rule-loading instruction |

The engagement's framing was whether a five-phase three-gate thread beats "two
hours of ad-hoc work". **On cost the thread is at rough parity or slightly worse:
2 h 35 min of wall-clock, five human interactions, and 8,500 lines a reader must
navigate.**

## What the thread produced that is demonstrably load-bearing

These are not claims about elegance. Each is a defect or a constraint that would
have shipped without the specific thread step that found it.

| Found by | What it found |
| --- | --- |
| Traffic evidence (Discover) | The marketing page the owner asked us to fix is not where most arrivals begin — the README drew 68 unique readers to the site's 6 outbound referrals. The redesign's reach was overstated. |
| Traffic evidence | The canvas must survive rendering inside `README.md`, because a pasted repository link is the largest identified referral path. **This is the single hardest constraint in the engagement and nothing else in the packet would have surfaced it.** |
| Content inventory (Discover) | The five most load-bearing marketing claims are the five with no evidence beside them. |
| Reading the repository (Discover) | The compliant, job-led explanation already exists in `guides/README.md` with zero gate codes — so most of the "new" vocabulary was already written and reviewed. |
| Heuristic baseline | `HumanGates.astro` is a second, larger gate-code violation the brief had not named. 11 rendered codes, not 5. |
| Peer audit | NN/g caps usable disclosure at two levels; the chat-transfer surface is text, not an image; "two pages stapled together" is **not** a named anti-pattern and must not be cited as one. |
| Information architecture | The approved documentation re-grouping **cannot be implemented without amending a Shipped spec.** A design-tweak assumption was wrong. |
| Token verification | The canvas cannot consume the token system in its binding rendering, so a hand-authored SVG silently diverges from the palette and nothing fails. |
| Token verification | There is no contrast check for the marketing palette — only the docs palette has one. |
| Composition, by rendering | Three non-text contrast breaches, an inverted visual rank, a legend reading as a ninth step. |
| Evidence audit (Validate) | **A false public claim** — that the system will not write status back to a tracker, when the repository documents a narrow confirmed write-back path. |
| Cold design review (Validate) | Six blockers, including a canvas composed on the wrong carrier, a drawing asserting three human decisions where the page asserts seven, and a screen unreachable from the surface its own journey stage names. |

## What the thread cost in defects it created

This is the half a favourable write-up would omit.

**40 review findings across two cold reviews. Almost all are one class: contracts
between artifacts, not reasoning inside them.** Four wrong counts, five
cross-artifact contradictions, three overstated-evidence claims, three
self-contradictions, one over-claimed sourcing rule — plus six blockers, four of
which were disagreements *between the packet's own documents*.

**The sharpest instance is causal, not incidental.** The canvas was composed on a
light background. The information architecture — written earlier, by the same
author, in a different file — places that element in the dark hero band. A
careful contrast pass was run, measured correctly, and documented honestly
against the wrong carrier. All 14 measurements were void.

That defect is **produced by the thread's own structure.** Twenty artifacts
written in sequence, each locally correct, with no mechanism that reads one
skill's output against another's. Two hours of ad-hoc work produces two
artifacts, and two artifacts cannot contradict each other forty ways.

**The thread also required a full rebuild of its centrepiece after review.** The
verdict was MAJOR REWRITE. A process whose own validation stage returns MAJOR
REWRITE on the primary deliverable has not obviously outperformed a shorter one —
it has demonstrated that it has a validation stage.

## The finding

**Three things are supported by this arm alone.**

**1. The thread's value concentrates in Discover and Validate, not in Define and
Design.** Every load-bearing discovery in the table above came from evidence
gathering, repository reading, the peer audit, or a cold review. The Define and
Design skills produced structure and vocabulary — useful, and mostly
re-derivable by a competent designer in less time. The two gates that earned
their cost are the ones with an outside input: real data, and a reviewer who did
not write the thing.

**2. The pack has no cross-artifact consistency mechanism, and that is its
largest defect.** Every authoring skill validates its own output against its own
contract. None reads another's. The result is a defect class the thread reliably
produces and cannot itself detect — 40 findings' worth. A linter that checked
declared numbers and named invariants across `docs/design/**` would have caught
most of them mechanically.

**3. Rendering beat specifying, twice.** Four composition defects were invisible
in a specification that said the right thing and visible immediately in a raster.
Any design thread that ends at prose has an undetectable failure mode, and this
one nearly shipped four.

**What this arm cannot establish** — and the engagement was explicit that an
honest answer matters more than a flattering one:

- Whether the ad-hoc designs would have made the same errors. The carrier
  mistake, for instance, may be *specific* to having a separate IA document to
  contradict.
- Whether they would have found the README constraint, the false tracker claim,
  or the Shipped-spec blocker. My expectation is that the traffic evidence and
  the evidence audit are the two steps least likely to occur ad hoc — but that is
  an expectation, not a result.
- Whether a champion could explain the model from either. Untested for all three,
  because the explain-it-back instrument has no baseline yet.

## Recommendations

1. **Add a cross-artifact consistency check to the pack.** Declared counts,
   named invariants, and state sets should be machine-checkable across a design
   packet. This is the highest-value change and it addresses the defect class the
   thread produces.
2. **Make "render it and look at it" a required step**, not a practice. Four
   defects, none catchable in prose.
3. **Keep Discover and Validate; compress Define and Design.** The gates with an
   outside input earned their cost. The middle produced more artifacts than
   decisions.
4. **Run the comparison when the control is available.** This finding should be
   superseded, not cited as a verdict.

## Gaps recorded against the pack

Ten, from this engagement. A–D were anticipated; E–J were found in flight.

| Gap | Missing capability |
| --- | --- |
| A | No skill gathers primary evidence; `journey-mapping` admits one evidence level per map |
| B | No skill owns a cross-surface journey |
| C | No skill designs an explanatory information graphic |
| D | No skill validates comprehension after ship |
| E | No design skill knows about build-time projection boundaries — the packet fell into this itself |
| F | No skill reconciles a stale prior design spec against shipped reality |
| G | `[design] output_dir` unconfigured, so `experience-status` reports zero artifacts against 38 on disk |
| H | `information-architecture` declares a read-first dependency on two skills the standard packet places downstream |
| I | No skill covers an acquisition surface whose conversion happens off-surface |
| J | **No skill writes the marketing headline** — the thread can fully specify the most important string on the page and cannot produce it |
