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
   (`business-unit`, coordinated from a value-stream meta-repo via
   `align-value-stream`).

## Procedure

1. **Decompose one level.** From the intent, produce its children:
   - If the intent is above feature level, produce **child intents** (a lower
     `Level:`), each inheriting the parent's outcome/scope context and a
     `Parent intent:` back-link. Each child re-enters the loop at `frame-intent`
     → `de-risk-intent` → `decompose-intent`. Don't skip levels. When running the
     discovery-traceability chain, carry the `Kind:` (`outcome | opportunity`) and
     `Level:` markers on each child (the same markers `frame-intent`'s template
     ships) so the structural-orphan lint places each decomposed rung on the chain.
   - If the intent is a **feature** (the leaf), produce the **spec/slice** — the
     shippable, agent-buildable unit (one coherent scope, vertical, ships and
     tests on its own). Cut by **shippability**, never by component or layer.

2. **Record the decomposition decision.** Note *why* the cut went the way it did
   on the parent's `Decomposition` — the grouping rationale, and any branch you
   considered and dropped or replaced (with a pointer to the killed child's
   `de-risk-intent` verdict when an upward kill forced the re-cut). This mirrors
   the de-risk trail, which already records why a bet was tested the way it was
   (`de-risk-intent`'s `references/reversibility-triage.md`). Without it the
   parent reads as if the tree were always this shape, and a later reader
   re-litigates a branch you already ruled out. A line or two per decision — a
   log, not a memo.

3. **Project the leaf — by Scale.** A feature-level intent is the leaf; how it
   projects depends on Scale (`references/recursive-decomposition.md`):
   - **`app` Scale** — it *is* a single `core` brief (same outcome, success
     metrics from the input/lagging/guardrail, scope/non-goals, appetite). Write
     it to `docs/product/briefs/<slug>.md` and hand to `receive-brief`. No new
     fields, no slicing — `receive-brief` is level-agnostic and receives a brief
     for its own repo.
   - **`business-unit` Scale** — **slice it per component** into one `core` brief
     per affected repo. Read the affected components and their
     `providesApi`/`consumesApi` edges + the contract references from the
     meta-repo's catalog (`align-value-stream`), and stamp each brief with
     `parent-intent:` (the intent it was projected from), a `contract@version`
     reference + read-only courier snapshot, and a provider/consumer role. Seed
     one rollup row per slice in the meta-repo. Each brief then crosses into its
     component repo, where `receive-brief` → `new-spec` → `work-loop` take over.
     Coordinating across repos this way has hard limits (no atomic cross-repo
     commit, no shared release train) — `align-value-stream` states them honestly.

4. **Keep the contract behavioral here.** Carry only the *interaction* shape (who
   talks to whom, the consumer's expectations) into the brief; the **detailed
   wire contract is pinned at the spec stage** via the existing `Contract:` seam,
   where the component's full context lives. Don't author OpenAPI/AsyncAPI here.

5. **Rank the children (optional).** When a decomposition produces several
   children that compete for the same appetite — and the order they ship in is a
   real call, not obvious from dependencies alone — apply a lightweight
   **prioritization/ranking** step over them: the adopter's own rubric (RICE,
   Torres's opportunity-sizing, a custom decision matrix), recorded as a `rank`
   on each child with its one-line rationale. This is the multi-criteria ranking
   the appetite + Scope Boundary do *not* do (constraint-setting, not ranking). It
   is **optional** — skip it when dependencies already order the children, or when
   there is one child. The rubric is the adopter's; this skill ships the *step*, not
   a fixed scoring formula. Discovery's backlog bridge reads the `rank` to order the
   handoff to `work-loop`.

6. **Project onto a tracker (optional, one-way).** If the team uses a tracker,
   render the tree onto it per `references/tracker-projection.md` — `none`
   (markdown only), Linear (lean; collapse), or Jira Align (deep; expand). The
   canonical tree is the source; the tracker is a render. **One-way only** —
   don't try to round-trip status back.

## Spotting a missing parent — offer, never block

Two prompt-only checks catch a skipped product rung. Both **offer**; neither
gates, and the user can decline and proceed.

- **Sibling-spawn detector.** When decomposition (or framing) produces children
  that won't each reduce to a single shippable slice — they read as several
  independent value bets, not slices of one buildable thing — that is the signal a
  **product parent is missing**. The sibling *count* is a hint, not a fixed
  threshold; the real test is the qualitative shippability test above. **Offer** to
  frame the product parent (`product-vision` / `product-strategy`) and hang the
  siblings beneath it, rather than emitting orphaned siblings.
- **Retroactive parent.** When several intents already exist with no shared parent
  (a rung was skipped earlier), **offer** to reconstruct one and back-link the
  siblings via their `Parent intent:` field. **Infer the altitude and name it for
  the user to correct:** siblings that are *architectural slices of one buildable
  thing* → a `capability` parent; siblings that are *independent value bets that
  together constitute one product* → a `product-vision` / `product-strategy`
  parent. Infer and confirm, never assume.

## Anti-patterns to refuse

- **Decomposing by component or layer instead of shippability.** "Backend then
  frontend" is not two slices; "the slice that lets a user reset their password,
  end to end" is. If a slice can't ship and test on its own, it isn't a slice.
- **Skipping a level.** Jumping a capability intent straight to specs hides the
  feature-level seams and the per-feature bets. Produce child intents first.
- **Decomposing a killed bet.** If `de-risk-intent` killed the riskiest
  assumption, reshape the parent — don't fan out specs that inherit the dead bet.
- **Silently re-shaping the tree.** Dropping or replacing a branch after a kill
  without recording why leaves the parent reading as if it were always cut this
  way — and invites a later reader to re-propose the dead branch. Log the
  decision (step 2).
- **Letting the tracker dictate the model.** Linear's flatness and Jira Align's
  depth are *projection targets*, not the product model. Model in intents; render
  to the tracker. Same canonical spec lands at an Issue (Linear) and a Story
  (Jira Align) — proof the tree must be canonical.
- **Authoring the wire contract here.** Behavioral interaction only; the spec
  stage owns the detailed contract.
