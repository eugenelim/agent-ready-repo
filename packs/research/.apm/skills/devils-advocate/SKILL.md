---
name: devils-advocate
description: Adversarially review a research artifact (`research.md`) or a user-supplied claim. Searches for counter-evidence, names the strongest objections, and proposes confidence-rating downgrades. Grounded in ACH (evidence-against column — the discipline that catches premature closure) and GIJN investigative-journalism practice ("what does the other side say"). Auto-invoked by `/research` deep mode against `research.md`; runs standalone against any user-supplied claim. Produces `counterpoints.md` linking back to the source artifact. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for the strongest objections; `comprehensively`, `exhaustively`, `in depth`, `extensive` for the full set.
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
4. **Propose rating downgrades** — for each finding whose evidence-
   against is substantive, propose the new confidence rating
   (`[high]` → `[moderate]`, or `[moderate]` → `[low]`, etc., per
   `references/confidence-schema.md`). Name the downgrade factor.
5. **Moderator pass** — before declaring done, scan retrieved-but-
   uncited counter-material and consider one more query from the
   highest-signal unused snippet (Co-STORM contribution).
6. **Write `counterpoints.md`**, linking back to the source artifact.

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
