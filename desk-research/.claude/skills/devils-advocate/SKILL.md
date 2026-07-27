---
name: devils-advocate
description: Adversarially review a research artifact (`<topic-slug>-survey.md`) or a user-supplied claim. Searches for counter-evidence, names the strongest objections, and routes each to a verdict — either a confidence-rating downgrade or a do-not-resolve verdict for an irreducible tension where both sides are well-evidenced under different conditions. Grounded in ACH (evidence-against column — the discipline that catches premature closure) and GIJN investigative-journalism practice ("what does the other side say"). Auto-invoked by `/desk-research` deep mode against `<topic-slug>-survey.md`; runs standalone against any user-supplied claim. Produces `<topic-slug>-counterpoints.md` linking back to the source artifact. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for the strongest objections; `comprehensively`, `exhaustively`, `in depth`, `extensive` for the full set.
---

# /devils-advocate

The adversarial review pass. Reads a finding, an artifact, or a claim,
and tries to take it down with cited counter-evidence.

## Output rendering

Severity list — Lead each finding with a severity glyph — 🟥 blocker, 🟧 major, 🟨 minor, ⚪ advisory — worst first, one finding per line, file:line anchor aligned.

## When to invoke

- **Auto-invoked** by `/desk-research` deep mode against `<topic-slug>-survey.md`.
- **Standalone** against a user-supplied claim ("argue against this
  finding"). The skill body handles both invocations.
- **In the decision pipeline**, against `<topic-slug>-hypotheses.md` to surface
  the counter-evidence each hypothesis must answer.

## Invocation shapes

This skill runs in two shapes:

- **Pipeline invocation** — expects a target artifact in the working
  directory (`<topic-slug>-survey.md` from `/desk-research`, or
  `<topic-slug>-hypotheses.md` from `/compare-hypotheses`). The artifact's
  findings are the input set.
- **Standalone invocation** — targets a user-supplied claim. The user
  supplies the claim explicitly; no upstream artifact is required.

## Methodology

Two convergent disciplines:

1. **ACH evidence-against column** — Analysis of Competing Hypotheses
   forces the analyst to list evidence *against* each hypothesis,
   alongside evidence for. The discipline catches premature closure:
   the model finds three supporting sources, stops, declares done. ACH
   refuses that move.

2. **GIJN investigative-journalism practice** — Global Investigative
   Journalism Network's standard rule: before publication, ask "what
   does the other side say?" and seek it out. The pack borrows the
   *seek-the-other-side* discipline as a final-step gate.

## Procedure

1. **Read the target.** Pipeline mode: load the upstream artifact.
   Standalone mode: take the user's claim verbatim.
2. **Enumerate counter-positions** — for each finding or claim, what
   would a serious critic say? Generate the strongest version of the
   objection, not the weakest.
3. **Retrieve counter-evidence** — dispatch `evidence-retriever`
   subagent against each counter-position. The main session does the
   reasoning; the subagent supplies the material.
4. **Route each substantive evidence-against to a verdict** — for each
   finding whose evidence-against is substantive, pick one of two
   verdicts:
   - **Rating downgrade** — the evidence-against weakens the finding:
     propose the new confidence rating (`[high]` → `[moderate]`, or
     `[moderate]` → `[low]`, etc., per `references/confidence-schema.md`)
     and name the downgrade factor. This is the default verdict.
   - **Do-not-resolve** — the evidence-against does *not* weaken the
     finding; it establishes a credible *opposing* position that is
     itself well-evidenced, so the finding and its counter are both
     right under different conditions. See *The do-not-resolve verdict*
     below. Reach for this only when a downgrade would misrepresent the
     situation.
5. **Moderator pass** — before declaring done, scan retrieved-but-
   uncited counter-material and consider one more query from the
   highest-signal unused snippet (Co-STORM contribution).
6. **Write `<topic-slug>-counterpoints.md`**, linking back to the source
   artifact. `<topic-slug>` matches the survey it reviews; the naming rule
   lives in the `/desk-research` skill body (§ Typed, topic-named artifacts).

## The do-not-resolve verdict

A rating downgrade says *"trust this finding less — the evidence is
weaker than it was rated."* It is the right verdict when the
counter-evidence undercuts the finding: a single source where three
were claimed, an unaccounted contested-in-field factor, a benchmark
that doesn't replicate.

But sometimes the counter-evidence is not a weakness in the finding —
it is a credible, well-evidenced position that *opposes* it, and both
survive scrutiny because they are right under **different conditions**.
The disagreement is in the world, not in a gap in the evidence.
Downgrading the finding here is wrong twice over: it implies the
finding is shaky (it isn't), and it implies that more evidence would
settle the question (it won't). The honest verdict is **do-not-resolve**:
name the productive tension, state the conditions under which each side
holds, and leave both standing.

Use the test: *would more or better evidence collapse this to one
answer?* If yes, it is a confidence question — downgrade. If no — if
the two positions are answers to subtly different questions, or hold in
different regimes — it is an irreducible tension, and you record it
rather than adjudicate it. Do-not-resolve is the `/devils-advocate`
counterpart to the tension map `/identify-perspectives` builds upstream:
the same irreducibility, surfaced adversarially against a finding rather
than enumerated across camps.

Do-not-resolve is **not** an escape hatch for "the evidence is thin so I
won't commit." Thin evidence is `[uncertain]` (a `/desk-research` rating) or
a known-unknown (a `/desk-research` gap entry) — not a tension. A
do-not-resolve verdict requires *substantive evidence on both sides*.

## `<topic-slug>-counterpoints.md` output schema

```markdown
# Counterpoints — <target artifact or claim>

## Finding: <quoted from target>

- **Counter-position:** <strongest objection, one paragraph>.
- **Counter-evidence:** <citations>.
- **Verdict:** rating downgrade — `[high]` → `[moderate]`. Reason:
  contested-in-field.

## Finding: <next>

- **Counter-position:** <a credible, well-evidenced opposing position>.
- **Counter-evidence:** <citations — substantive, on both sides>.
- **Verdict:** do-not-resolve. Both hold under different conditions:
  <finding> holds when <conditions>; <counter-position> holds when
  <conditions>. More evidence would not collapse this to one answer.
```

The `Verdict` line carries exactly one of the two outcomes from step 4 —
a rating downgrade *or* do-not-resolve, never both for the same finding.

## Citation discipline

Every counter-evidence claim carries a citation. A counter-position
that the model invents without cited backing is marked `[inference]`
and tagged as such in the counterpoints.

## Depth cues

- `quickly`, `top three`, `briefly`, `summary only` — return the
  strongest one or two objections per finding only.
- `comprehensively`, `exhaustively`, `in depth`, `extensive` —
  enumerate every credible counter-position; include weaker objections
  for completeness.
