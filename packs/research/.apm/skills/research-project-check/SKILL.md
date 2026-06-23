---
name: research-project-check
description: "Passive stop-signal for a research project — reads the synthesis matrix and memos by eye and reports whether the corpus has stopped changing the structure (theoretical saturation), plus a recommendation. Triggers on project-lifecycle phrasing — \"is this project saturated\", \"should I keep gathering\", \"check the stop signal\" — inside an existing project folder. It NEVER advances phase and computes no counter, score, or metric; the saturation judgment is qualitative and the human decides. It MAY optionally write a verdict_status string into overview.md (the single permitted light state write) — nothing more. Prompt-only by construction."
---

# /research-project-check

The **passive stop-signal** of a research project. It answers one question —
*has the corpus stopped changing the picture?* (theoretical saturation) — and
makes a recommendation. It is deliberately **passive**: it reads, judges, and
reports; it never advances the lifecycle and never computes a number. The human
decides what to do with the signal.

## When to invoke

Inside an existing project folder, on phrasing like *"is this project
saturated?"*, *"should I keep gathering sources?"*, *"check the stop signal"*.
Run it whenever you want a read on whether more capture is worth it.

## What it reads

- `synthesis-matrix.md` — is its **structure** still changing? Are recent
  sources adding new columns, or just filling existing rows?
- `memos.md` — are load-bearing claims corroborated, or still resting on one or
  two sources?

## The saturation judgment — read by eye, qualitative

Report a **qualitative** judgment across three questions, read by eye:

1. **Is the corpus still changing the matrix structure?** New sources that keep
   introducing new columns mean the picture is still forming. New sources that
   only confirm existing columns mean the structure has stabilised.
2. **Are recent sources adding columns or just confirming?** Confirmation
   without new structure is the saturation signal (grounded theory's
   theoretical saturation).
3. **Are load-bearing claims corroborated?** A claim the whole verdict rests on,
   still single-sourced, is a reason to keep gathering regardless of structural
   saturation.

Then give a **recommendation** — *"looks saturated; move to synthesize"* or
*"not yet; the cost dimension is still single-sourced — gather more there"* —
and stop. **The human decides.**

There is **no counter, no score, no metric, no derived number** anywhere in this
skill. Saturation is a reading of the matrix and memos, not a computed
threshold. "Three sources per claim" informs the triangulation rail at synthesis
time; it is not a saturation formula this skill evaluates.

## The one permitted state write

This skill **MAY** optionally write a single string — `verdict_status` — into
`overview.md`'s frontmatter (e.g. `verdict_status: looks-saturated` or
`verdict_status: keep-gathering-on-cost`), as a convenience marker of its last
read. That is the **only** state it is permitted to write.

It **NEVER advances `phase`** — it does not move the project from `digest` to
`synthesize` or anywhere else. Phase progression is human-driven; this skill
only recommends. Writing anything other than `verdict_status` into `overview.md`
is an *Ask-first* deviation.

## What this skill is not

- Not a phase-advancer — it recommends; the human moves the project.
- Not an engine — no counter, score, metric, or saturation threshold; the
  judgment is qualitative, read by eye (Charter Principle 3).
- Not a synthesis — it reads the digest and reports a stop-signal; it writes no
  findings and no brief.

## Next

Act on the recommendation by hand: keep gathering (back to capture/digest), or
move to `/research-project-synthesize`. This skill changes nothing but the
optional `verdict_status` marker.
