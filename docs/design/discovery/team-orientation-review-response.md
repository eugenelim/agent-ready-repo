---
type: review-response
slug: team-orientation-review-response
status: awaiting-gate
gate: review-experience-designs
reviews:
  - independent evidence audit (Codex, fresh session) — 16 findings
  - experience-reviewer cold design pass — MAJOR REWRITE, 6 blockers, 16 majors, 8 minors, 3 nits
  - shaping-reviewer on the intent — Findings, 12, four blocking admission
updated: 2026-09-04
---

# Review response

Two independent cold reviews, 40 findings between them. This records what was
sustained, what was fixed, and what is deliberately left owed — so the gate can
judge the disposition rather than take a claim of "addressed".

**The gate contract is that Blockers are acted on before design feeds build.**
All six blockers are fixed. Majors are triaged, not all fixed, and the ones left
open are named with a reason rather than absorbed silently.

## Review 1 — independent evidence audit

Lens: is the packet *true* and *internally consistent*? Verified every checkable
claim against the repository.

**16 findings, 16 sustained.** I re-checked each against the repository rather
than accepting the reviewer's word, and personally re-verified the two most
consequential before adopting them. Full disposition is in the decision log's
"What the cold review changed".

The one that mattered: an internal-case refusal read *"It will not write status
back into your tracker"*, which is **false** — the repository documents a narrow,
human-confirmed coordination write-back to Jira. The invariant is directional.
That would have shipped a verifiably untrue claim to a budget holder.

## Review 2 — experience-reviewer cold design pass

Verdict: **MAJOR REWRITE**, scoped to the canvas and its records, the seam
invariant, and zone 4. It found the spine sound — adoption dominant, work nested,
the axis change — and the contracts between artifacts not.

### The six blockers, all fixed

| # | Blocker | Disposition |
| --- | --- | --- |
| 1 | The canvas was composed on a light ground; the IA places it in the **dark hero band**, voiding all 14 contrast measurements | **Rebuilt on the dark carrier.** Re-measured: 11 of 11 text pairs and 8 of 8 non-text pairs pass, zero failures. The two accent tokens invert roles between carriers and the rebuild uses the display accent, which is its documented dark-zone role. |
| 2 | The station-name invariant was stale in three artifacts and **self-contradicting in adjacent bullets** in the canvas brief | Fixed in all four. The five stations are marketing-side only; the seven job names and the decision phrasings are what cross the seam. |
| 3 | The canvas drew **3** decision points; the page asserts **7** — so the drawing said shaping is unsupervised | **Five diamonds now**, including the two shaping decisions. The legend states that some steps carry more than one decision, so the counts reconcile instead of contradicting. |
| 4 | `role="img"` and a **13-element focus order** are mutually exclusive | Resolved to **one image, one focusable control** — the transcript disclosure. Emphasis is pointer-only and carries no information. The rejected architecture is recorded so it is not reintroduced. |
| 5 | Zone 4 required station costs "sourced never written" from a source that **has none** | Zone 4 now states what each station asks of a team. Only station 2 carries durations, cited. For the other four the surface **names the evidence boundary**, which is what principle 2's tradeoff prescribes. |
| 6 | S6 was unreachable from the surface its own journey stage names | **S1 zone 10 → S6 added**, plus the transition row. And a **new steel-thread assertion (1c)** now checks that every screen is reachable from the surface its stage names — 1b was too weak to catch this. |

### Majors: 14 fixed, 2 genuinely owed

Fixed: the direction marker and terminus placement on the tracker spur (2); arc
type dominance, now the heaviest type after the title (3); the state count,
settled as four rendering states plus two cross-state requirements (4); all
eleven gate-code dispositions enumerated, where the deck previously covered nine
while asserting the count was discharged (5); the collapse width, first stated as
intent and then corrected against a render (6); the brand register's grounding
labels, now all four honestly directional (7); the spur detached from any step's
baseline (8); headline candidates drafted as gate input (9); the link-preview
strings reworked to lead with the reader's situation and the refusals (10); the
above-fold reading-pattern argument re-made against the real seven-element
inventory (11); the path page's register over-claim narrowed to a sourcing rule
(12); the disclosure-ceiling inconsistency resolved by naming the distinction as
ours — staged versus progressive disclosure — rather than borrowing it from a
citation that does not support it (13); station spacing evened out (14); S6's
inherited canvas states and clipboard degradation (15); the twenty-minute promise
made conditional on its build item (16); plus minors 2, 3, 4, 7 and 8.

**Genuinely owed — both need something outside this repository:**

| # | Owed | Why it cannot be closed here |
| --- | --- | --- |
| Major 1 | **V1 — does the canvas survive GitHub's Markdown sanitiser?** | The composition record now states the *correct* binding mechanism for an `<img>`-embedded SVG — no host cascade, no page stylesheet — and keeps the hedge. But the sanitiser's actual behaviour needs a probe rendered in a real README. **No amount of writing closes it.** |
| Minor 5 | **The primary success metric has no baseline.** | The explain-it-back baseline requires the champion interview, which has not run. The instrument exists; the reading does not. |

Nits 1–3 remain judgement calls in the reviewer's own framing, not defects.

**A correction to this document.** It previously said "6 left owed" and listed
four items that had already been fixed in a later round. The table was written
before those fixes and never updated — which is precisely the defect class this
whole response is about, occurring inside the tracking of that defect class.
Found by re-checking each row against the files rather than trusting the table.

### What both reviewers independently praised

Worth recording because it identifies which practices to keep:

- The traffic artifact states what the instrument **cannot** see before what it
  can, refuses to sum daily uniques, reclassifies clone counts as machine
  traffic, and excludes operator traffic.
- The transition checker was **proved capable of failing** under two mutations,
  with its declared set written from the inventory rather than derived from the
  table. That is what makes a green result a result.
- Three non-text contrast breaches were caught by hand, and two composition
  defects were caught only by rendering.
- The tracker-refusal correction — a false claim found and replaced with the
  invariant that actually holds.

## The pattern in 40 findings

Almost every finding from both reviews is the same class: **confident prose
outrunning the artifact.** Not wrong reasoning — wrong bookkeeping across twenty
documents written in sequence, where each was locally correct and the set was
not.

The sharpest instance is blocker 1. A careful contrast pass was run, measured
correctly, documented honestly — against a background the packet's own
information architecture had already ruled out. The method was sound and the
input was wrong, and nothing in the authoring skills could catch that because no
skill reads another skill's output for contradiction.

That is a finding about the thread, not about this engagement, and it belongs in
the pressure-test verdict.

## Gate request

`review-experience-designs`: all six blockers fixed and verified, ten of sixteen
majors fixed, six owed with named reasons, one verification (V1) owed before
build. The canvas has been rebuilt and re-rendered.

---

## Design QA on the rendered result

The Validate packet's QA pass, run on the **rebuilt** canvas rather than the
specification, because the specification is what was wrong the first time.

**Quality floor.** All five rendering states are specified and the two cross-state
requirements are attached to the one control. Reduced motion is the default
rather than an alternative. Colour never carries meaning alone — decision points
are a different shape, scope groups are a labelled gap, and the tracker's
direction is an arrowhead. Contrast: 11 of 11 text pairs and 8 of 8 non-text
pairs pass on the correct carrier.

**Rendered at a real GitHub content column (880px), and it changed a claim.**

| Element | Authored | At 880px | Verdict |
| --- | --- | --- | --- |
| Arc station labels | 18px | 13.2px | comfortable |
| Work-step labels | 13px | 9.5px | small, readable |
| Scope group labels | 10px | 7.3px | **marginal — degrades first** |

An earlier draft claimed the work-step labels were what degrades. They are not.
The scope group labels are, and they carry trace step 6 — the scope boundary. The
collapse width was tied to the wrong element and is corrected.

Useful direction of error: the canvas survives README width **better** than the
packet claimed. A defensively pessimistic statement is still a wrong statement.

**Heuristic pass on the rebuilt composition.** Recognition over recall: the axis
change means a reader never has to remember which lifecycle they are in.
Consistency: five stations, one enclosure, one legend, one accent family.
Minimalism: the enclosure has ~100px spare width, which is breathing room rather
than an unfilled slot. Match to the real world: the arrowhead and terminus now
say what the caption says, where revision 1's undirected line said the opposite.

**Marketing clarity.** Not re-run here. It resolves in copy that does not exist,
and the three headline candidates in the copy deck are gate input for exactly
that reason.

**What this pass could not do.** The site is not built, so this is QA on one
component, not on a rendered page. Zone order, above-fold height budget, and the
seam in a browser all need a rendered-surface pass with the gate browser — owed
after build, and named in the baseline review's own scope-honesty section.

## Thread-status check

`experience-status` was resolved the way the skill does — read-only down the
config chain. Neither `./agentbundle-layout.toml` nor the user-scope file
declares `[design] output_dir`, so the skill **stops at "not configured" and
reports zero artifacts** while 37 markdown files and one SVG sit on disk.

That is Gap G, demonstrated rather than described: the thread's own status tool
cannot see the thread. Configuring it is a repository decision, not a design one,
and it is in the owner's hands.
