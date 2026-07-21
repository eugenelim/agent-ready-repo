# Example: signal → situation framing

A product engineer holds a signal surfaced by `work-loop` during a
maintenance PR and runs `frame-situation` to decide whether and where to
route it into the shaping sequence.

---

## The raw signal

> "Engineering reported that every team in the org hand-rolls its own agent
> skill discovery mechanism — three separate implementations found across two
> squads, no standard emerging. Symptoms: onboarding friction, duplicate
> maintenance overhead, subtle incompatibilities when sharing skills."

---

## Step 1 — Intake and altitude confirmation

The signal affects multiple teams and their shared agent skill infrastructure.
That is initiative/capability level — proceed.

*(If a team had asked "can we add a skill discovery flag to our CLI?" that
would be feature-scoped → altitude mismatch → redirect to `frame-intent`.)*

---

## Step 2 — Classify the finding

**Type: gap**

Three independent implementations exist, no standard is emerging, and
coordination overhead is growing. This is a convergence gap — the org is
spending custom-build budget where a shared standard would serve it better.

---

## Step 3 — Wardley maturity assessment

| Capability | Stage | Evidence | Strategic implication |
|---|---|---|---|
| Agent skill discovery | Custom-built | Three hand-rolled implementations; no shared protocol or registry | Approaching the Product boundary — watch for emerging standards (e.g., SKILL.md frontmatter conventions becoming a de-facto norm). Invest in a lightweight shared convention rather than a full product; avoid over-engineering at this stage. |
| Inter-team skill coordination | Genesis | No established pattern; teams resort to Slack DMs and manual copying | Explore first; no standard exists to adopt yet. A lightweight convention (stable marker + registry) may be sufficient before committing to a heavier coordination mechanism. |

*(Third capability area: not identified — only two strongly implicated.)*

> **Residual assumptions:** "Approaching the Product boundary" for skill discovery
> rests on the assumption that the SKILL.md convention is gaining traction
> beyond this org. If it is still isolated internal practice, the placement
> may be early Custom-built rather than late Custom-built. Confirm via external
> signals (GitHub stars, adapter adoption) before over-investing.

---

## Step 4 — Recommended entry point

**Step 2 — `identify-opportunities`**

The problem is confirmed (coordination overhead, duplicate implementations),
but the functional, emotional, and social jobs of the engineers and adopters
affected have not been documented. Start at step 2 to map the jobs before
diverging on solutions — the gap's root cause may be deeper than "we need a
registry."

---

## Artifact written

Path: `docs/product/shaping/agent-skill-discovery-gap/situation-framing.md`

```markdown
---
type: situation-framing
slug: agent-skill-discovery-gap
signal: "Three hand-rolled skill discovery mechanisms found; no standard emerging; growing coordination overhead"
finding-type: gap
date: 2026-07-20
shaping-entry: identify-opportunities
---

## Signal
Engineering reported that every team hand-rolls its own agent skill discovery
mechanism — three implementations found across two squads, no standard emerging.
Symptoms: onboarding friction, duplicate maintenance, subtle incompatibilities.

## Finding
**Type:** gap · **Rationale:** A convergence gap — the org is spending
custom-build budget where a shared standard would serve it better. The problem
is confirmed; the solution space is open.

## Wardley Capability Assessment

| Capability | Stage | Evidence | Strategic implication |
|---|---|---|---|
| Agent skill discovery | Custom-built | Three hand-rolled impls; no shared protocol | Watch for emerging standards; invest in a lightweight convention now |
| Inter-team skill coordination | Genesis | No established pattern | Explore first; no standard to adopt yet |

> **Residual assumptions:** "Approaching Product boundary" for skill discovery
> requires confirmation via external signals (GitHub/adapter adoption).

## Recommended Entry Point
**Step:** identify-opportunities · **Rationale:** Problem confirmed; jobs not yet mapped.

## Step 2 readiness
`identify-opportunities` is not yet detected in available skills. Step 2 maps
the functional, emotional, and social jobs of the people affected by the signal
— grounding solution divergence in real user needs. Resume shaping there when
the skill becomes available.

## Suggested workspace.toml entry
```toml
{slug = "agent-skill-discovery-gap", type = "shape"},
```
Add to `[ini-NNN.shaping_queue]` backlog via `queue-add` or manually.
```

---

## Step 6 — Workspace.toml suggestion printed

The agent prints:

```toml
{slug = "agent-skill-discovery-gap", type = "shape"},
```

> Add this to your active initiative's `[shaping_queue]` backlog in
> `workspace.toml`. Use `queue-add` or edit manually. Once added,
> `workspace-status` will surface it as a ready shaping item pointing to
> `identify-opportunities`.
