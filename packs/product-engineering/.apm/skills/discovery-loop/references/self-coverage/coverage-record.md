# Self-coverage gate — the module index + the coverage record

`discovery-loop` is the **primary home of the full seven-module design-convergence
instantiation** of RFC-0051's self-coverage gate. Unlike `work-loop` (which adopts
only the net-new slice atop the passes it already runs), discovery runs the **full
battery** — this is the altitude it was built for. The gate runs as the **pre-G2
phase**, right-sized by this loop's progressive mode (solo runs it lean; a
lens-team run runs it in full). *(AC33.)*

This is `discovery-loop`'s **own co-scoped copy** of the modules; it does not
import `work-loop`'s copy (which carries only `resolve-vs-surface`). A schema/seam
change moves both copies — they conform to the **same cross-loop seam** RFC-0051
fixes (the goal + resolve-vs-surface + a non-skippable coverage record), never
re-worded.

## The discipline

Between human gates, **resolve everything a referent can resolve and surface only
the irreducible** — value origination, irreversible risk, or value conflict. The
gate is a **phase the loop runs, not a step it may skip**; non-skippability rests
on this named phase plus the done-checklist refusal below.

## The seven modules

| Module | When | What it does |
| --- | --- | --- |
| [`pre-mortem`](pre-mortem.md) | divergence + pre-G2 | name how this would fail before it ships |
| [`taxonomy`](taxonomy.md) | convergence | walk the discovery-risk taxonomy (value / usability / feasibility / viability) for blind spots |
| [`scenario-variation`](scenario-variation.md) | divergence + convergence | vary the scenario along axes the happy path hides |
| [`fresh-context`](fresh-context.md) | pre-G2 (REVIEW) | the forked-context discovery reviewers, who never saw the authoring |
| [`domain-grounding`](domain-grounding.md) | pre-convergence (PLAN) | ground a load-bearing domain claim before designing on it |
| [`resolve-vs-surface`](resolve-vs-surface.md) | every gate | the calibration rubric for resolve-with-referent vs surface |
| `coverage-record` (this file) | closed at G2 | the non-skippable disposition record |

## The coverage record (non-skippable)

At G2, before the decision brief is ratified, the loop writes a **coverage
record** — a short, durable artifact (promoted into the decision-log / brief) with:

1. **Disposition of every open item** — each marked **resolved-with-referent**
   (cite the referent) or **surfaced-with-reason** (value origination, irreversible
   risk, value conflict, or a referent that genuinely failed). The
   [`resolve-vs-surface`](resolve-vs-surface.md) module calibrates the call.
2. **Module attestation** — which of the seven modules ran, and (right-sizing) why
   any ran lean.
3. **Open fresh-context findings** — every discovery-reviewer finding is resolved
   or explicitly deferred with a reason.

**Done-checklist refusal.** The loop does **not** declare G2 reached until the
coverage record exists and every fresh-context finding is resolved. This refusal
item is what makes the gate non-skippable — the same backstop RFC-0051's seam
requires of every loop.
