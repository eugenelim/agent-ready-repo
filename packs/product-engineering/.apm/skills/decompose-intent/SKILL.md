---
name: decompose-intent
description: Use when a de-risked intent needs breaking into the next level down — child intents, or a shippable spec/slice at the leaf — and optionally projecting onto a tracker. Triggers on "decompose this", "break this down", "slice this", "what specs come out of this", "push this to Linear/Jira". Recursive (one level at a time); at app scale the leaf is an ordinary `core` brief. Do NOT use to author an intent (use `frame-intent`) or to test a bet (use `de-risk-intent`).
---

# Skill: decompose-intent

Break a de-risked `intent` into the **next level down** — child intents, or, at
the leaf, a shippable spec/slice — and optionally project the tree onto a tracker.
Decomposition is recursive: it produces one level at a time, until the leaf is a
unit your delivery loop can build. At `app` Scale the leaf feature intent *is* a
`core` brief, so the hand-off is `receive-brief` → `new-spec` → `work-loop` with
no new machinery. The recursion + the brief projection are in
`references/recursive-decomposition.md`.

## When to invoke

Before decomposing, confirm:

1. The intent's riskiest assumption has **survived** `de-risk-intent`. Don't fan
   a bet out into children you haven't de-risked at its own level — a killed
   assumption should reshape the parent, not spawn doomed specs.
2. You know the intent's **Scale** (set by `frame-intent`). It decides whether
   the leaf is a same-repo brief (`app`) or a per-component slice crossing repos
   (`business-unit` — phase 2, out of scope for v1).

## Procedure

1. **Decompose one level.** From the intent, produce its children:
   - If the intent is above feature level, produce **child intents** (a lower
     `Level:`), each inheriting the parent's outcome/scope context and a
     `Parent intent:` back-link. Each child re-enters the loop at `frame-intent`
     → `de-risk-intent` → `decompose-intent`. Don't skip levels.
   - If the intent is a **feature** (the leaf), produce the **spec/slice** — the
     shippable, agent-buildable unit (one coherent scope, vertical, ships and
     tests on its own). Cut by **shippability**, never by component or layer.

2. **Project the leaf to a brief (`app` Scale).** A feature-level intent *is* a
   `core` brief — the same outcome, success metrics (from the input/lagging/
   guardrail), scope/non-goals, and an appetite. Write it to
   `docs/product/briefs/<slug>.md` and hand to `receive-brief`. No new fields, no
   slicing — `receive-brief` is level-agnostic and receives a brief for its own
   repo. (At `business-unit` Scale the leaf is sliced per component into one brief
   per repo — phase 2.)

3. **Keep the contract behavioral here.** Carry only the *interaction* shape (who
   talks to whom, the consumer's expectations) into the brief; the **detailed
   wire contract is pinned at the spec stage** via the existing `Contract:` seam,
   where the component's full context lives. Don't author OpenAPI/AsyncAPI here.

4. **Project onto a tracker (optional, one-way).** If the team uses a tracker,
   render the tree onto it per `references/tracker-projection.md` — `none`
   (markdown only), Linear (lean; collapse), or Jira Align (deep; expand). The
   canonical tree is the source; the tracker is a render. **One-way only** —
   don't try to round-trip status back.

## Anti-patterns to refuse

- **Decomposing by component or layer instead of shippability.** "Backend then
  frontend" is not two slices; "the slice that lets a user reset their password,
  end to end" is. If a slice can't ship and test on its own, it isn't a slice.
- **Skipping a level.** Jumping a capability intent straight to specs hides the
  feature-level seams and the per-feature bets. Produce child intents first.
- **Decomposing a killed bet.** If `de-risk-intent` killed the riskiest
  assumption, reshape the parent — don't fan out specs that inherit the dead bet.
- **Letting the tracker dictate the model.** Linear's flatness and Jira Align's
  depth are *projection targets*, not the product model. Model in intents; render
  to the tracker. Same canonical spec lands at an Issue (Linear) and a Story
  (Jira Align) — proof the tree must be canonical.
- **Authoring the wire contract here.** Behavioral interaction only; the spec
  stage owns the detailed contract.
