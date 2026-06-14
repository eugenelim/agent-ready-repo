---
name: devils-advocate
description: Adversarially review a research artifact (`research.md`) or a user-supplied claim. Searches for counter-evidence, names the strongest objections, and proposes confidence-rating downgrades — or, for a productive/irreducible tension, a do-not-resolve verdict that preserves the disagreement instead of collapsing it. Grounded in ACH (evidence-against column — the discipline that catches premature closure) and GIJN investigative-journalism practice ("what does the other side say"). Auto-invoked by `/research` deep mode against `research.md`; runs standalone against any user-supplied claim. Produces `counterpoints.md` linking back to the source artifact. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for the strongest objections; `comprehensively`, `exhaustively`, `in depth`, `extensive` for the full set.
---

# /devils-advocate

The adversarial review pass. Reads a finding, an artifact, or a claim,
and tries to take it down with cited counter-evidence.

## When to invoke

- **Auto-invoked** by `/research` deep mode against `research.md`.
- **Standalone** against a user-supplied claim ("argue against this
  finding"). The skill body handles both invocations.
- **In the decision pipeline**, against `hypotheses.md` to surface the
  counter-evidence each hypothesis must answer.

## Invocation shapes

This skill runs in two shapes:

- **Pipeline invocation** — expects a target artifact in the working
  directory (`research.md` from `/research`, or `hypotheses.md` from
  `/compare-hypotheses`). The artifact's findings are the input set.
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
4. **Fork the verdict** — for each finding whose evidence-against is
   substantive, decide between two outcomes (see *Two verdicts* below):
   - **Downgrade** — propose the new confidence rating (`[high]` →
     `[moderate]`, or `[moderate]` → `[low]`, etc., per
     `references/confidence-schema.md`) and name the downgrade factor.
   - **Do-not-resolve** — when the finding and its counter-position are
     *both* well-supported and hold under different conditions, return a
     do-not-resolve verdict instead of a downgrade. Name the regime
     split; do not pick a winner.
5. **Moderator pass** — before declaring done, scan retrieved-but-
   uncited counter-material and consider one more query from the
   highest-signal unused snippet (Co-STORM contribution).
6. **Write `counterpoints.md`**, linking back to the source artifact.

## Two verdicts: downgrade vs do-not-resolve

A confidence downgrade and a do-not-resolve verdict are different
outcomes, and conflating them is the failure this section exists to
prevent.

- **Downgrade** says the finding is *weaker* than rated — the
  counter-evidence erodes it, one answer still stands, just less
  confidently. The artifact still collapses to a single rated answer.
- **Do-not-resolve** says the finding and its counter-position are
  *both* well-supported and each holds under different conditions. The
  tension is productive: collapsing it to one rated answer would be
  false precision, not added confidence, and forcing a winner would
  destroy real information about *when* each holds.

Reach for do-not-resolve when the evidence-against is roughly as strong
as the evidence-for **and** the two hold in different regimes (different
scale, context, time horizon, or value frame). This is ACH's discipline
taken to its conclusion: ACH refuses *premature* closure, and the
do-not-resolve verdict refuses closure where closure itself is the
error. Where `/identify-perspectives` produced a tension map, a
do-not-resolve verdict is its downstream echo — cite the matching
tension if one exists.

## `counterpoints.md` output schema

```markdown
# Counterpoints — <target artifact or claim>

## Finding: <quoted from target>

- **Counter-position:** <strongest objection, one paragraph>.
- **Counter-evidence:** <citations>.
- **Proposed rating change:** `[high]` → `[moderate]`. Reason:
  contested-in-field.

## Finding: <next>

(same shape)

## Finding: <quoted from target> — do-not-resolve

- **Verdict:** do-not-resolve (productive tension).
- **Counter-position:** <the equally-supported opposing finding>.
- **Holds when:** original finding under <regime A>; counter-position
  under <regime B>.
- **Why not collapse:** <what a forced single answer would destroy>.
```

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
