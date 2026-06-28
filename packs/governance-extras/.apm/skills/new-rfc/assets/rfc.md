# RFC-NNNN: <proposal title>
<!-- short, identifying title (e.g. "Coordinator contract"); the fuller
explanation goes in "The ask", not the title — a scannable index depends on it -->

- **Status:** Draft <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental (optional: trial running, results pending — see the Experiment / validation section) -->
- **Author:** <github-handle>
- **Approver:** <github-handle who signs off — the one person whose yes starts implementation>
- **Date opened:** YYYY-MM-DD
- **Date closed:** <!-- filled in when status reaches a terminal state -->
- **Decision weight:** standard <!-- light | standard | heavy — right-sizes research depth + the pre-handoff gate. Pick it yourself by reading work-loop's risk triggers (a prose heuristic, not a computed value); default `standard` when unsure. light = a reversible, narrow change (one research sweep, sections collapse to one-liners); standard = a normal multi-decision RFC (full per-subpoint research + full gate); heavy = reverses a frozen ADR/RFC, crosses a governance/charter/security boundary, or is a one-way door (full gate + a de-risk spike + explicit Approver sign-off). The gate's checks never drop by tier — weight changes how much research/draft, not whether a mandated check runs. -->
- **Related:** <!-- ADRs, specs, prior RFCs -->

## Reviewer brief

<!--
First-screen orientation for the reviewer — a fixed, scannable grid they read
before anything else. Keep each line short; this orients, "The ask" argues. Do
NOT restate the BLUF here — these are different jobs. (For a `light` RFC, a few
lines suffice.)

- **Decision:** the one thing being decided, in a sentence.
- **Recommended outcome:** accept / reject / amend.
- **Change if accepted:** ≤3 bullets — what actually changes.
- **Affected surface:** code / docs / packs / interfaces touched.
- **Stakes:** reversible / costly-to-reverse / one-way door.
- **Review focus:** the one or two things most worth a reviewer's scrutiny.
- **Not in scope:** the dog that didn't bark — what this deliberately doesn't do.
-->

## The ask

<!--
Answer-first. After this section a reviewer should know exactly what they are
being asked to approve, in plain language, without hunting through the design.

- **Recommendation (BLUF):** one or two sentences — what to approve.
- **Why now (SCQA):** Situation (agreed context) → Complication (what changed /
  the problem) → the Question it raises. Three or four lines.
- **Decisions requested:** render as a table — one row per decision — so a
  reviewer can scan what they must decide and what action each needs:

  | ID | Question | Recommendation | Why | Decide by | Reviewer action |
  | --- | --- | --- | --- | --- | --- |
  | D1 | <the decision> | <recommended option> | <one-line why> | <this review / date> | <what the reviewer must do — confirm X, rule on Y> |

Right-size to the stakes: a small, reversible change keeps this short and
collapses the sections below to one-liners (see the `Decision weight` header).
-->

## Problem & goals

<!--
Diagnosis before any solution — name the problem first; if you can't, you have
a wishlist, not a proposal. Then:

- **Goals.**
- **Non-goals** — things that could reasonably have been goals but you are
  deliberately choosing not to pursue. Negated goals ("won't crash") don't
  count; this section is where scoping work shows.
-->

## Proposal

<!--
The design. Concrete enough that a reviewer can disagree with the substance,
not just the framing. Cascade the detail under each requested decision.
Include the migration path if there's existing state to convert.
-->

## Options considered

<!--
This section is mandatory and load-bearing.

- Enumerate the option/scenario space to be **collectively exhaustive (MECE)
  along a stated axis** — say what the axis is and why these options exhaust
  it. A small round count (e.g. exactly 3) with no exhaustiveness argument is
  a smell, not a finish line.
- **Ground each option in prior art** (how have others solved this shape of
  problem?) rather than inventing categories.
- Include the **do-nothing** option and its cost of delay. Sometimes it wins.
- State each option's trade-offs up front, against the goals — not retrofitted
  after the choice. A starred/recommended-option table is encouraged.
-->

## Risks & what would make this wrong

<!--
- **Pre-mortem:** assume this shipped and failed — list the top failure modes
  and their mitigations.
- **Key assumptions (falsifiable):** phrase each so a reviewer can point at one
  and say "that's wrong, because…".
- **Drawbacks:** what it costs, what you're giving up. "None" is not an
  answer — push back on yourself.
-->

## Evidence & prior art

<!--
- **Spike / de-risk result.** Identify the assumption that, if false, sinks the
  proposal; run a small/timeboxed check and report the result here — or state
  why no spike was needed. Do your own experimentation; don't hand the reviewer
  an untested guess.
- **Repo precedent.** Related ADRs, RFCs, specs the proposal touches.
- **External prior art.** What other projects/processes did with this shape of
  problem. Every citation must be fetched and confirmed to contain the claim it
  supports — a link that merely loads is not enough. Empty prior art is itself
  a finding (no one has tried this) — say so rather than leaving it blank, and
  never fabricate.
- **Promoted research (optional `NNNN-notes/` companion).** If this proposal
  rests on a sustained investigation, keep the distilled brief and supporting
  material in a sibling `docs/rfc/NNNN-notes/` folder; summarize its conclusions
  here and link it, rather than pasting the corpus into the RFC body.

Split rule: a section that changes the reviewer's decision stays in the body;
one that mainly proves the work was done is summarized here and its detail moved
to `NNNN-notes/`. The body is the argument; the notes are the audit trail.
-->


## Experiment / validation

<!--
OPTIONAL — delete this section unless the proposal genuinely needs an
experiment. Frame the experiment here; do NOT paste raw results into the RFC
(that bloats the proposal into a lab notebook).

- **Hypothesis.**
- **What we measure.**
- **Success / failure criteria.**

Capture the results in a separate, linked spike note (or a follow-up RFC / a
superseding ADR), and mark the RFC `Experimental` while they're pending (see
docs/CONVENTIONS.md § RFC lifecycle); move it to a terminal status once they
land.
-->

## Open questions

<!--
Aim for ≤3. Each carries a **recommended default + owner + decide-by** — never
a bare question. Anything you could resolve by research must already be
answered in the body, not parked here; a bare question means the research
phase wasn't done.
-->

## Follow-on artifacts

<!--
Filled in when the RFC is accepted. The bridge from "we agreed" to "we did it".

- ADR-NNNN: <title>
- Spec: docs/specs/<feature>/
- Convention change: docs/CONVENTIONS.md, section X
-->

<!--
CORRECTIONS — DELETE THIS WHOLE BLOCK unless this RFC is accumulating
post-publication corrections. Do NOT ship it as an empty section on a fresh
RFC. See the new-rfc skill, "Recording corrections (Errata / Amendments)", for
the full rules; the shape below is the optional, threshold-gated scaffold.

Pick the heading by lifecycle class: `## Errata` for a Frozen RFC
(Accepted/Rejected), `## Amendments` for an in-flight Open one. (Rename
`## Amendments` → `## Errata` if this RFC is later Accepted.)

A single one-line correction stays a plain dated bullet under the heading — no
table — like this:

## Errata        (or ## Amendments)

- **YYYY-MM-DD — <short title>.** <what was corrected and why>.

Split into the two layers below ONLY once the section crosses the threshold:
more than one entry, or any entry supersedes another. Heading wording is your
call; the two-layer split (authoritative current state over a dated audit trail,
current state wins on disagreement) is the contract.

## Errata        (or ## Amendments)

### Current state

The corrections in force today — read these, not the log, for the present
contract. Where this layer disagrees with a historical entry below, this layer
wins.

| Area | Current rule | Owner / note |
| --- | --- | --- |
| <area> | <the rule in force> | <owner / blocker> |

### History / audit trail

Dated, append-only entries explaining how each correction was reached. Never
delete an entry — it is the audit trail. (On an in-flight `## Amendments` you
MAY reword a stale entry in place, tagging it `*(Superseded: …)*`; on a Frozen
`## Errata` the entries are immutable.)

- **YYYY-MM-DD — <short title>.** <what was corrected and why>.
-->
