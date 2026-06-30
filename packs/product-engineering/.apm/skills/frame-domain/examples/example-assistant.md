# Example — framing the domain for a 0-to-1 product (app scale, greenfield)

> **This is an example, not a schema.** It demonstrates the *shape* of a
> `frame-domain` run and the two typed artifacts it produces. Your domain will
> look different; copy the *moves*, not the wording.

A worked example — `example-assistant`, a secure personal-assistant
agent that helps an owner plan recurring tasks, track resource state, generate a
derived list, and improve through approved learning. After `decompose-intent`
produced its capabilities, the agent runs `frame-domain` at **G1.5 Domain &
MVP**, standalone (no coordinator present).

Intake resolves **greenfield** (a 0-to-1 product — there is no current system to
reverse-engineer), so Domain Framing's brownfield current-system half is omitted
and the artifact says so.

## The run

1. **Real-world-activity half** — `frame-domain` invokes `research` in `applied`
   mode against *how owners actually plan, act, and restock*. It consumes and
   shapes the survey findings (it does **not** treat the survey as the artifact)
   into the *Real-world activity* section, and carries what research could not
   ground into *Residual assumptions*.
2. **Current-system half** — greenfield, so it is omitted with a note.
3. **Out-of-scope register** — bounds the appetite and lists each tempting-but-
   excluded capability with its appetite reason (the third-party fulfillment
   integration is the classic over-scope this rejects).
4. **Resolve + write** — the discovery key is unbound, so resolution falls to the
   designed default `docs/discovery/example-assistant/`; the directory is created
   lazily and the two artifacts are written, each carrying its marker.

## Produced artifact 1 — `docs/discovery/example-assistant/domain-framing.md`

```markdown
---
type: domain-framing
initiative: example-assistant
brownfield: false
---

# Domain framing — example-assistant

## Real-world activity
- **How the activity is really done.** It runs on a cadence/horizon (e.g.
  weekly); the high-deliberation slice is a subset — the MVP anchors on that
  slice, not everything. The plan is **not followed exactly**: substitutions,
  skips, carry-overs. "Planned" and "actually done" diverge, so the plan must be
  editable and "mark what you did" is a first-class action. Carry-over is
  first-class (do once, benefit twice) and affects both next-cycle planning and
  resource decrement. Quantities scale to the owner's context.
- **Best practice** (applied-mode, confidence-tagged). Constraints that bind real
  choices: preferences, exclusions, variety (no repeats), and
  use-what-you-have / use-before-threshold — the last is the lever for the
  waste-↓ outcome. *(confidence: moderate — practitioner sources triangulated.)*
- **Naive-design failure modes** (the anti-pattern frame). Demanding precise
  inventory: owners will not maintain it, and demanding precision is exactly why
  such tools fail. Coarse, approximate state with surfaced uncertainty is the
  pattern that survives.

## Current system (brownfield)
(greenfield — no current system to reverse-engineer; this half is omitted.)

## Residual assumptions
- The exact replenishment cadence owners tolerate before state feels stale —
  research surfaced ranges, not a settled number; surfaced for the human, not
  asserted.
- Whether owners accept a single "anything run out / low?" prompt as sufficient
  decrement signal — plausible from grey literature but unconfirmed for this
  owner segment.
```

## Produced artifact 2 — `docs/discovery/example-assistant/scope-boundary.md`

```markdown
---
type: scope-boundary
initiative: example-assistant
---

# Scope boundary — example-assistant

## Out-of-scope register
- Third-party fulfillment / external-service integration — out because the
  appetite is the owner-driven plan→act→restock loop; external fulfillment is a
  separate value bet the owner did not ask for.
- Precise inventory capture — out because demanding precision is the named
  naive-design failure mode; the MVP accepts coarse, approximate state.
- Analytics / optimization — out because the MVP proves the loop, not its tuning.
- Multi-user collaboration — out because the product is single-owner by appetite.
- Budget optimization — out because it is a distinct outcome outside the
  waste-↓ / time-to-plan-↓ appetite.
- Large-scale external import — out because seeding is rough-by-design in the MVP.
```

The brief inherits and refines this register at G3 (the `scope-boundary → brief`
edge).
