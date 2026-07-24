---
name: user-flow
description: "Use when a customer journey needs to become the screens that realize it — sequencing the screens, the transitions between them, and the error/edge flows (a failed action lands the user where?), then emitting one self-contained brief per screen. Triggers on map the screen flow, what screens do we need, sequence the screens for this journey, design the screen-to-screen flow, what happens when this action fails, turn this journey into screens. Carries a platform/surface axis and ends in a whole-journey walk that never skips. Do NOT use to map the journey itself (use journey-mapping), to design how one screen behaves internally (use interaction-design), or to blueprint the backing services (use service-blueprint). Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register."
---

# Skill: user-flow

Produces a **screen flow** — the journey's screens *sequenced*, with the
transitions between them and the **error/edge flows** (when an action fails,
which screen or state the user lands in), the **per-screen state matrix**, and
the **platform/surface axis** — plus **one self-contained brief per screen**.
This is the *interaction flow across screens*, not a bare list: the enumerated
screen inventory is the spine the flow is drawn over. The method foregrounds the
**macro flow** (sequence, transitions, cross-screen error routing); the *micro*
behavior *within* one screen — feedback, validation flow, the in-component state
machine, motion — is `interaction-design`'s, not this skill's. See
`references/screen-flow.md`.

**Inputs:** a customer journey (from `journey-mapping`, or elicited inline —
this skill is standalone-useful without an upstream artifact) and the backing
services (from `service-blueprint`, or named textually when it is absent).
**Consumed by:** `creative-direction` / `design-system` /
`information-architecture` / `interaction-design` (each enriches a
per-screen brief), `product-engineering`'s `ux-writing` (writes copy per
screen × state, keyed to the state matrix), the `experience-reviewer` agent
(reviews the flow + briefs), and — through the optional handover — a generative
design tool (realization).

## When to invoke

Confirm all four before drafting; if any fails, resolve it first.

1. **There is a journey or an outcome to realize as screens** — name the journey
   (or the outcome) the screens serve. If no journey map exists, elicit the
   stages and the customer goal inline before sequencing screens.
2. **The scope is the flow *across* screens** — the behavior *within* a screen
   (feedback, input/validation timing, the component state machine, motion) is
   `interaction-design`; the backing services are `service-blueprint`. Route
   those separately; this skill owns the cross-screen routing.
3. **You know the surface** — confirm `surface` before drafting:
   `responsive-web | iOS | Android | cross-platform`. Surface changes the
   navigation model and the per-screen chrome the flow assumes; see step 1.
4. **No current screen flow exists for this journey and surface** — if one
   exists, you are amending it. Check the path resolved in step 6.
5. **You know the surface genre.** Before drafting briefs, confirm the genre from
   `marketing | documentation | informational | analytical | transactional-journey | marketplace | workspace`.
   If absent from context, elicit inline: "What kind of surface is this?" Genre is
   orthogonal to platform — a marketplace surface on iOS is both `marketplace` AND `iOS`.
   Genre determines which design pattern families and IA approaches apply downstream.
   Record it as `surface-genre:` in the per-screen brief frontmatter.

> **Standalone elicitation fallback.** When invoked without a screen brief (e.g.
> enriching a single screen ad hoc), check context for a declared `surface-genre:`.
> If none exists, ask "What kind of surface is this?" before proceeding. Genre
> determination is not optional — it routes every downstream skill in the chain.

## Procedure

1. **Set the surface.** Confirm the target surface
   (`responsive-web | iOS | Android | cross-platform`). Note the navigation
   model and platform conventions the flow must honor — consult `references/screen-flow.md`
   § Platform/surface axis. Point to the platform conventions (Apple HIG /
   Material 3 / MDN responsive); do not reprint their values.
2. **Enumerate the screens — the spine.** From the journey stages, list the
   screens each stage implies. This inventory is the spine; it is not the
   deliverable. Name each screen by the job it does, not by a widget. Load
   `references/screen-flow.md` § The screen inventory.
3. **Sequence the flow and route the edges.** Draw the screens in journey order;
   for each, name the transitions out (what the user does → which screen next)
   and the **error/edge flows** (a failed or denied action → which screen or
   state). A flow with no error edges is a happy-path sketch, not a screen flow.
   Author the flow as a mermaid `flowchart`. Load `references/screen-flow.md`
   § Sequencing and edge routing.
4. **Build the per-screen state matrix.** For each screen, name which floor
   states apply (empty / loading / error / success / partial / disabled, plus
   `permission/denied` when gated). **Defer to the shared quality floor** for the
   state set — do not restate it: see `../design-review/references/quality-floor.md`.
   The matrix is *which* states each screen handles; the *behavior between* them
   is `interaction-design`'s.
5. **Emit one per-screen brief per screen.** Use `assets/screen-brief-template.md`.
   Each brief splits into a **shared design contract** — authored once per product
   (design system, the grounded aesthetic direction, the navigation model,
   `interaction-design`'s behavioral conventions, the quality floor) and
   *referenced*, never copied — and a **per-screen spec** (this screen's job,
   states, data, actions, copy pointer). The shared contract is what keeps N
   independently-generated screens coherent. Each action names its backing
   service (the tie down to `service-blueprint`); each screen names the journey
   step it serves (the tie up to `journey-mapping`). Each brief carries the
   bold-body `- **Type:** screen-brief` traceability marker the template ships — the
   structural-orphan lint reads it to recognize the brief as a `screen` chain node.
6. **Resolve the path and surface it.** Resolve `<output_dir>` following the
   config-driven, two-branch elicitation procedure in `references/agentbundle-layout.md`.
   Resolution order: (1) repo-root `./agentbundle-layout.toml`
   `[design] output_dir` — repo-scope takes priority; (2) user-profile
   `~/.agentbundle/agentbundle-layout.toml` `[design] output_dir`; when neither resolves,
   two-branch elicitation runs — never a silent default: **(a) Repo branch** —
   suggest `docs/design/` and offer to write `output_dir` to
   `./agentbundle-layout.toml [design]`; **(b) Personal/vault branch** — ask for
   an absolute path (e.g. `~/Documents/<VaultName>/design/`) and write to
   `~/.agentbundle/agentbundle-layout.toml [design]`. Expand to a full absolute
   path (`~`-expand, realpath-resolve, reject `..` escapes); a repo-root-sourced
   `output_dir` that resolves outside the repo tree is untrusted-origin — confirm
   before writing. **Surface the resolved path before writing.** Write the flow
   to `<output_dir>/screens/<slug>-flow.md` (frontmatter `type: screen-flow`) and
   each brief to `<output_dir>/screens/<slug>/<screen>.md`; create the dirs lazily.
7. **Run the cross-brief consistency pass.** Before declaring the briefs done,
   check the set as a whole: shared components reused (never reinvented), states
   uniform across screens, copy voice aligned, navigation non-contradictory. A
   set of briefs that each read well but contradict each other is not a screen
   flow. Load `references/screen-flow.md` § Consistency pass.
8. **Walk the whole journey — this step always runs.** Verify the flow holds
   end-to-end *before* handing off, and **never end at "briefs emitted."** Reach
   for the cheapest whole-journey verification available, degrading but never
   skipping: if a wireframe/prototyping MCP tool is connected, assemble a low-fi
   clickable prototype and walk the journey; **else build the text-only steel
   thread** — a scripted walk through the briefs in journey order asserting
   **every transition resolves** (no screen routes to one that doesn't exist) and
   **every action has a backing service**. The steel thread degrades from
   prototype → text-only, **never to nothing**. Load `references/screen-flow.md`
   § The steel thread.
9. **(Optional) Emit the design-tool handover.** If the adopter wants to realize
   the screens: detect-and-degrade. A generative design-tool MCP connected (Figma
   AI, Claude, v0, or another) → trigger it with the handover; none present →
   emit `<output_dir>/screens/<slug>/<screen>.handover.md` (from
   `assets/design-tool-handover-template.md`) for the adopter to paste into
   whichever tool they use. The handover is **instructions keyed to the brief**,
   never pixels or values; it names tool *categories*, endorses none.
10. **Hand off.** Point the craft skills (`creative-direction`,
    `design-system`, `information-architecture`,
    `interaction-design`) at the briefs to enrich, `ux-writing` at the
    state matrix for copy, and the `experience-reviewer` for the independent review.

## Anti-patterns to refuse

- **Ending at "briefs emitted."** The whole-journey walk (step 8) is the pack's
  guarantee that being coarser-grained than a maximalist catalogue never leaves a
  *flow* gap. It is **non-droppable**: it degrades from an MCP prototype to a
  text-only steel thread, never to nothing. A flow handed off without the walk is
  unverified.
- **A bare screen list.** Screens without transitions and error/edge flows are an
  inventory, not a screen flow. The edges — especially where a failed action
  routes — are the work.
- **Designing in-screen behavior here.** Feedback, input-validation timing, the
  component state machine, and motion are `interaction-design`'s. This skill owns
  *which* screens, in *what* order, with *what* cross-screen routing — the macro
  flow. Macro-flow (here) vs micro-behavior (`interaction-design`) is the line.
- **Restating the state set.** The state enumeration lives once, in the shared
  quality floor. Reference it; do not copy empty/loading/error/… into each brief.
- **Copying the shared contract into every brief.** The shared design contract is
  authored once and *referenced* by every brief — copying it is how N screens
  drift out of coherence. Reference, never restate.
- **Reprinting platform values.** The surface axis changes the navigation model
  and the questions; it never prints breakpoints, HIG spacing, or Material values
  into the flow. Point to the conventions; let the method derive the shape.
