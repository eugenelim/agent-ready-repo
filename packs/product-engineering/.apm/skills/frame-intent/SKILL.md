---
name: frame-intent
description: Use when shaping a piece of product work before it becomes a spec — turning an idea, a request, or a strategy into a level-tagged `intent` (an outcome + the opportunity behind it). Triggers on "shape this", "what's the intent here", "frame the problem", "before we build X", "turn this into a brief/PRD". Authors an `intent` at any altitude in the open recognized set — product-vision, product-strategy, capability, or feature — resolves Scale (app ↔ business-unit) at intake, and offers current-state inputs only when brownfield. Do NOT use to test an assumption (use `de-risk-intent`) or to break an intent down (use `decompose-intent`).
---

# Skill: frame-intent

Shape a piece of product work into an `intent` — a level-tagged statement of an
outcome and the opportunity behind it — *before* it becomes a spec. A
product-vision, a product-strategy, a capability, and a feature intent are the
same artifact at different levels; a PRD is just a feature intent written as a
document. This is the entry point of the
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
   Resolve where to write it using the config-driven procedure below, then
   write it to `<parent>/intents/<slug>.md`; fill what you have.

## Procedure

1. **Intake — resolve Scale, then maturity.** Run the routine in
   `references/scale-intake.md`: **infer** Scale from the workspace (app code +
   a single component → `app`; no app code / many component pointers →
   `business-unit`), **confirm** it with the user, and **ask** only when it's
   genuinely ambiguous. Stamp `Scale:` on the intent (and the `docs/product/`
   root on first run). Then ask **greenfield or brownfield** for *this* intent —
   it gates one thing only (step 5).

2. **Consult the enterprise's knowledge — only if a surface is present.** If you
   detect a knowledge-retrieval surface in this session (an MCP knowledge tool,
   an internal CLI, an in-repo doc set — reason about *capabilities*, name no
   specific tool; a public web search/fetch tool is **not** an internal surface,
   so don't count it), load `references/knowledge-surfaces.md` and consult the
   problem-framing areas this intent turns on — **business domain & meaning** (so
   the outcome and opportunity use the org's real terms and rules) and
   **in-flight & roadmap** (so you don't frame a bet already being delivered); in
   brownfield, the **current-landscape** area is consulted at step 5, where the
   maturity gate offers current-state inputs. **Name the surface you used (or
   "none detected") in the intent's `Assumptions`**, so detection stays
   auditable. If no surface is present, *compose-if-present, degrade-if-absent*:
   ask the user for the missing domain / in-flight context and lower the
   confidence of any outcome or opportunity that leaned on it (carry the marker
   into `Assumptions`); never fabricate; treat sensitive or read-only sources as
   ask-before-quoting.

3. **Pick the altitude — Scale only *suggests* it.** The recognized set runs
   `product-vision › product-strategy › capability › feature` and is **open**
   (name an intervening altitude if your org has one — see
   `references/intent-model.md`). Scale suggests where to start, it does not stamp
   it: an `app` **greenfield product concept** → `product-vision` (the existence
   bet); an `app` **known feature** → `feature`; a `business-unit` effort →
   `product-strategy` or `capability`. **For concept-shaped or greenfield input,
   ask the altitude explicitly** — "is this a product bet, or a feature you've
   already scoped?" — rather than defaulting to `feature`; the user overrides the
   suggestion in one word. A clearly-scoped feature proceeds at `feature` without
   ceremony, and `decompose-intent` produces the levels beneath whatever altitude
   you start at.

4. **Write the outcome — three parts.** A *steerable input metric* you can move,
   the *lagging outcome* it should drive, and a *guardrail* that must not get
   worse. A quantified target is not the same as outcome-thinking; in 0-to-1 a
   **qualitative-but-falsifiable** outcome is first-class — name the signal
   you'd accept as proof. Never bolt a metric onto a feature already decided.

5. **Write the opportunity — solution-independent.** Frame what the user is
   trying to get done (a job / opportunity), not a solution. The default
   outside-in lens is a JTBD job map. **Only in brownfield**, offer the
   current-state inputs in `references/current-state-inputs.md` (a journey map,
   or an L3 process map as a *constraint*) — in greenfield, skip them so you
   don't pave cow paths.

6. **Seed the assumptions.** List what must be true for the bet to pay off — one
   line each. Don't test them here; `de-risk-intent` picks the riskiest and
   predeclares a kill condition. Leave `Decomposition` empty.

7. **Hand off.** Resolve `parent` using the config-driven procedure below and
   record the intent at `<parent>/intents/<slug>.md` (file-per-slug — a single
   file handed downstream, not a per-topic folder). Point the user at
   `de-risk-intent` (to test the riskiest assumption) or, once it survives,
   `decompose-intent` (to break it down). See
   `examples/feature-intent-to-brief.md` for a worked app-scale walk-through.

## Where the intent lives — config-driven, `docs/product` by default

Resolve the intent **parent** directory in this order, **in this skill body**.
Reading is **prompt-only** (Charter Principle 3): this skill reads a file and
reasons about a path — there is no engine, index, daemon, or watcher behind it,
and the only code that ever *writes* the layout file is the install-time append.
See [`references/agentbundle-layout.md`](references/agentbundle-layout.md) for the
`[product-engineering]` section's full schema.

1. **Read `agentbundle-layout.toml`'s `[product-engineering]` table** if the
   adopter created one. Two locations, **repo-root overrides user-profile per
   table**: the repo-root `./agentbundle-layout.toml` `[product-engineering]`
   table if present, else the user-profile
   `~/.agentbundle/agentbundle-layout.toml` `[product-engineering]` table. The
   file is **adopter-owned**, never shipped into a projected path. Its `parent`
   key is a **base** directory under which intents are written as individual
   files — never a per-topic folder:

   ```toml
   # agentbundle-layout.toml (adopter-created; optional)
   [product-engineering]
   parent = "docs/product"   # a base; intents land at <parent>/intents/<slug>.md
   ```

2. **Fall back to the pack's own default** — `docs/product`.
3. **Elicit** if neither resolves — ask the user where intents should live.

**Anchor `parent` by the layout file's own location**, never against the ambient
cwd: a **repo-root** file's `parent` is **repo-root-relative** (an absolute value
is permitted but warn it as non-portable); a **user-profile** file's `parent`
**must be an explicit absolute path** (`~`-anchored is fine), and a *relative*
value there is an Ask-first deviation, never silently resolved.

**Resolve, then surface, then write.** After anchoring, resolve `parent` to its
**full absolute path** — `~`-expand it and **realpath-resolve it** so any symlink
in the path is made visible and never silently followed out of the intended root
— and **reject any `..` escape**. The `..` rejection and the realpath happen
**after** anchoring, so a relative repo-file value that escapes via `..` (e.g.
`parent = "../../etc"`) is caught regardless of which file supplied it; anchoring
never blesses a `..`-bearing value as in-tree. Then **surface the resolved
absolute path to the adopter before creating the intent file** — the first write
is always preceded by the path you are about to write under.

**A repo-root-sourced `parent` that resolves outside the repo tree** — or whose
resolution required following a symlink out of the intended root — is
**untrusted-origin**: a cloned, untrusted repo can carry a hostile `parent`
(`../../etc`, `~/.ssh`, an out-of-tree symlink). **Confirm the resolved absolute
path with the adopter before writing.** The user-profile file is foot-gun-only
(the adopter authored it), but still surface its resolved path.

**Output shape — file-per-slug, not a per-topic folder.** Intent files live
directly under `<parent>/intents/<slug>.md`. A per-topic folder is deliberately
**not** used: each intent is a single file handed downstream to `de-risk-intent`
and `decompose-intent`. `decompose-intent`'s `docs/product/briefs/<slug>.md`
output stays **pinned** — that path is the hand-off to core's `receive-brief`
and is not governed by this config (a deliberate non-goal of this layout config).

## Spotting a missing parent — offer, never block

When a concept won't reduce to a single shippable slice — it implies several
independent value bets, not one buildable thing — that is the signal a **product
parent is missing**. **Offer** to frame the product parent (`product-vision` /
`product-strategy`) and shape the rest beneath it, rather than letting the user
emit orphaned siblings. The sibling *count* is a hint, not a fixed threshold; the
real test is the qualitative shippability one. It is an **offer** — never a block;
the user can decline and proceed. `decompose-intent` carries the same detector,
plus a retroactive-parent affordance for intents that already exist.

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
