---
name: frame-intent
description: Use when shaping a piece of product work before it becomes a spec — turning an idea, a request, or a strategy into a level-tagged `intent` (an outcome + the opportunity behind it). Triggers on "shape this", "what's the intent here", "frame the problem", "before we build X", "turn this into a brief/PRD". Authors a capability or feature intent, resolves Scale (app ↔ business-unit) at intake, and offers current-state inputs only when brownfield. Do NOT use to test an assumption (use `de-risk-intent`) or to break an intent down (use `decompose-intent`).
---

# Skill: frame-intent

Shape a piece of product work into an `intent` — a level-tagged statement of an
outcome and the opportunity behind it — *before* it becomes a spec. A capability
intent and a feature intent are the same artifact at different levels; a PRD is
just a feature intent written as a document. This is the entry point of the
product-engineering loop: frame here, then `de-risk-intent`, then
`decompose-intent`. The intent model is in `references/intent-model.md`.

## When to invoke

Before framing, confirm:

1. The ask is *shaping*, not *testing* or *breaking down*. If the user wants to
   probe whether a bet holds, route to `de-risk-intent`; if they want to split a
   shaped intent into the next level, route to `decompose-intent`.
2. There is an outcome worth naming — something that changes for a user or the
   business. If the work is a pure refactor or chore with no user-facing
   outcome, it doesn't need an intent; say so.
3. This skill ships the `intent` template at `assets/intent-template.md`.
   Copy it to `docs/product/intents/<slug>.md`; fill what you have.

## Procedure

1. **Intake — resolve Scale, then maturity.** Run the routine in
   `references/scale-intake.md`: **infer** Scale from the workspace (app code +
   a single component → `app`; no app code / many component pointers →
   `business-unit`), **confirm** it with the user, and **ask** only when it's
   genuinely ambiguous. Stamp `Scale:` on the intent (and the `docs/product/`
   root on first run). Then ask **greenfield or brownfield** for *this* intent —
   it gates one thing only (step 4).

2. **Pick the level.** `capability` (spans several features / components) or
   `feature` (one shippable capability). At `app` Scale most intents are
   `feature`-level; at `business-unit` Scale you usually start at `capability`
   and let `decompose-intent` produce feature intents beneath it.

3. **Write the outcome — three parts.** A *steerable input metric* you can move,
   the *lagging outcome* it should drive, and a *guardrail* that must not get
   worse. A quantified target is not the same as outcome-thinking; in 0-to-1 a
   **qualitative-but-falsifiable** outcome is first-class — name the signal
   you'd accept as proof. Never bolt a metric onto a feature already decided.

4. **Write the opportunity — solution-independent.** Frame what the user is
   trying to get done (a job / opportunity), not a solution. The default
   outside-in lens is a JTBD job map. **Only in brownfield**, offer the
   current-state inputs in `references/current-state-inputs.md` (a journey map,
   or an L3 process map as a *constraint*) — in greenfield, skip them so you
   don't pave cow paths.

5. **Seed the assumptions.** List what must be true for the bet to pay off — one
   line each. Don't test them here; `de-risk-intent` picks the riskiest and
   predeclares a kill condition. Leave `Decomposition` empty.

6. **Hand off.** Record the intent at `docs/product/intents/<slug>.md` and point
   the user at `de-risk-intent` (to test the riskiest assumption) or, once it
   survives, `decompose-intent` (to break it down). See
   `examples/feature-intent-to-brief.md` for a worked app-scale walk-through.

## Anti-patterns to refuse

- **Mandating a schema / rejecting a half-formed intent.** The template is a
  prompt sheet. An intent missing metrics is normal input — offer a default,
  don't block.
- **Baking a solution into the opportunity.** "Add a reset-link button" is a
  solution; "get back into my account on my own" is the opportunity. Keep the
  opportunity solution-independent so de-risk and decomposition stay open.
- **A quantified target standing in for outcome-thinking.** A number retrofitted
  onto a feature already chosen is theatre; name the input you can steer and the
  guardrail you're watching, not just a scoreboard.
- **Mapping the current process in greenfield.** There's nothing to pave yet —
  current-state inputs are a brownfield-only tool.
- **Framing at the wrong altitude.** A cross-component bet written as one feature
  intent hides the seams; raise it to a capability intent and decompose.
