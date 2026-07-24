---
name: de-risk-intent
description: Use when an intent is framed and you need to test whether the bet holds before building it out — naming the riskiest assumption, predeclaring a kill condition, and running it under a chosen prototype-approach. Triggers on "de-risk this", "is this assumption true", "what would have to be true", "should we validate or just build it", "test the bet". Routes by reversibility (one-way vs two-way door) and ends in a survive/kill verdict. Do NOT use to author the intent (use `frame-intent`) or to break it down (use `decompose-intent`).
---

# Skill: de-risk-intent

Test whether a framed `intent`'s bet holds before you build it out. The flow:
**reversibility triage → riskiest assumption → predeclared kill condition →
prototype-approach → survive/kill verdict.** It operates on *this* intent at
*its* level — the kind of assumption that dominates follows the level:
**product-level** (`product-vision` / `product-strategy`) → **market-existence**;
**capability** → architectural / adoption; **feature** → **desirability**. The
predeclared kill condition is the load-bearing guard against validation theatre.

**`market-existence` — the product-level kind.** At `product-vision` /
`product-strategy` the bet is not "do users want this feature" but
**market-existence**: *will anyone want this at all* (market desirability) **and**
*can this be a business* (viability). It is **categorically distinct** from
feature-level `desirability` — a different token for a different question, named so
the viability half cannot quietly drop out — and it is tested **once at the top**,
not re-litigated per sibling feature. It reuses the existing pre-PMF **qualitative
bar** in `references/kill-condition.md` (no new mechanism): predeclare a clear
qualitative line, in 0-to-1 terms, before you probe.

## Output rendering

Key–value / one record — For a single record's fields, use an aligned key: value list, not a two-row table.

## When to invoke

Before de-risking, confirm:

1. The intent is **framed** (outcome + opportunity + assumptions seeded by
   `frame-intent`). If not, frame it first — you can't de-risk a bet you haven't
   stated.
2. There is a **riskiest assumption worth testing** — one that, if wrong, sinks
   the bet. If every assumption is low-risk and cheap to reverse, say so and go
   straight to `decompose-intent`; ceremony on a safe bet is waste.

## Procedure

1. **Reversibility triage.** Classify the bet: a **one-way door** (expensive or
   irreversible — a public API, a data migration, a contract many teams depend
   on) or a **two-way door** (cheap to undo — behind a flag, a small cohort).
   The full triage is in `references/reversibility-triage.md`. This sets the
   *default* prototype-approach (step 4) — it does not lock it.

2. **Name the riskiest assumption — "what would have to be true".** From the
   intent's assumptions, pick the one with the highest risk × least evidence.
   Classify each assumption on the evidence ladder (`observed` — confirmed by
   direct measurement; `supported` — backed by analogous data or research;
   `inferred` — derived from adjacent signals; `assumed` — team consensus without
   external data; `unknown` — no signal exists yet). The riskiest assumption to
   test is the one at the lowest evidence level — `unknown` before `assumed`,
   `assumed` before `inferred`. Front it with *what would have to be true* for
   the bet to pay off, then restate the single riskiest condition as the test target.

3. **Predeclare the kill condition — in the test's own currency.** Write down,
   **before** running anything, what result would kill the bet — a number where
   you have traffic (an MDE / conversion line), a **qualitative bar** where you
   don't ("proceed only if ≥ 4 of 6 target users do X"). See
   `references/kill-condition.md`. Declaring the line *before* the result is what
   separates real validation from theatre.

4. **Choose the prototype-approach and run it.** This is the choosable, per-intent
   mode — defaulted by the triage, overridable — and it changes how you work
   (`references/prototype-approach.md`):
   - **`validate-first`** (default for one-way / outcome-led): the kill condition
     is set; build the cheapest probe that tests it; take the result.
   - **`prototype-led`** (default for two-way / taste-led): build a cheap
     prototype early and let what it reveals **drive** refinement — the build *is*
     the test. Feed findings back into the intent as you go.

5. **Verdict — survive or kill.** Compare the result to the predeclared line.
   **Survived** → the intent is ready for `decompose-intent`. **Killed** → record
   what you learned, and either reframe the intent (`frame-intent`) or, if this is
   a child intent, let the kill bubble up to its parent. Either way, fold what the
   prototype revealed back into the intent.

## The validation-hook field — desk-grounding is not validation

The predeclared kill condition answers *what result would kill the bet*; a
**validation hook** pairs it with **the real-world activity that would confirm or
enrich it** — the interview, diary study, Wizard-of-Oz pilot, or usability test a
human would run. Carry it as a **validation-hook field** on the de-risked intent:

```
validation_hook:
  assumption: <the riskiest assumption, restated>
  kill_condition: <the predeclared line, in the test's own currency>
  activity: <the real-world activity that confirms or enriches it>
  evidence_level: observed | supported | inferred | assumed | unknown
```

This is the field `plan-validation` consumes to build the validation plan, and the
field the discovery loop's provisional spine (G2) reads to label each node
**grounded** / **surfaced** / **to-validate** — making *converged ≠ validated* a
structural property, not a footnote. **Running the activity is out of charter** —
`de-risk-intent` *names* the hook; a human (or `plan-validation` scaffolding)
runs it. A surviving bet whose only evidence is desk-grounding still carries a
`to-validate` hook: desk-grounding is not validation.

## Anti-patterns to refuse

- **Declaring the kill condition after seeing the result.** Post-hoc thresholds
  rationalize whatever happened. The line is set *before* the test, full stop.
- **Testing the cheapest assumption instead of the riskiest.** Comfort-testing
  produces a green light that wouldn't have changed the decision. Test the one
  that sinks the bet.
- **A number where you have no traffic.** In 0-to-1, a fabricated conversion
  threshold is fake rigor; use a qualitative bar and say so.
- **Prototype as theatre.** A prototype that can't fail tells you nothing — if it
  doesn't sting when the bet is wrong, it isn't a test. (`prototype-led` still has
  a predeclared bar; the build being the test doesn't mean the test is skipped.)
- **Formal assumption-testing on a cheap, reversible bet.** If the build *is* the
  test and reversal is free, ship the probe — don't manufacture an experiment.
