---
name: de-risk-intent
description: Use when an intent is framed and you need to test whether the bet holds before building it out — naming the riskiest assumption, predeclaring a kill condition, and running it under a chosen prototype-approach. Triggers on "de-risk this", "is this assumption true", "what would have to be true", "should we validate or just build it", "test the bet". Routes by reversibility (one-way vs two-way door) and ends in a survive/kill verdict. Do NOT use to author the intent (use `frame-intent`) or to break it down (use `decompose-intent`).
---

# Skill: de-risk-intent

Test whether a framed `intent`'s bet holds before you build it out. The flow:
**reversibility triage → riskiest assumption → predeclared kill condition →
prototype-approach → survive/kill verdict.** It operates on *this* intent at
*its* level — the kind of assumption that dominates follows the level
(capability → architectural / adoption; feature → desirability). The predeclared
kill condition is the load-bearing guard against validation theatre.

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
   Front it with *what would have to be true* for the bet to pay off, then
   restate the single riskiest condition as the test target.

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
