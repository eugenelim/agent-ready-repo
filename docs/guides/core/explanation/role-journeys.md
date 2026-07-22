# Role journeys

How the three primary personas — PM (and strategist), engineer, and AI agent — navigate the workspace coordination system at their operating altitude.

## First install and orientation

If you are new to this coordination system, start with the [Your first workspace](../tutorials/your-first-workspace.md) tutorial — it walks you through arriving at a repo that uses `workspace.toml`, running `workspace-status`, reading the queue, and completing your first agent session. To orient at any subsequent session start, the [orient at session start](../how-to/orient-at-session-start.md) how-to gives you the repeatable recipe. The [two-room model](two-room-model.md) explains why shaping work (deciding what to build) and build work (building it) live in separate rooms — that separation is the architectural premise behind every section below.

This guide picks up after first install. It explains how each persona fits into the system at their altitude, what their primary touchpoints are, and where to go next.

---

## PM

The "PM" section covers the full shaping-room human path across altitudes 0 and 1 — three sub-personas whose work converges on the same output: a DoR-ready brief in `[brief_queue]`. The product strategist sets direction at altitude 0. The product engineer shapes initiatives at altitude 1. The intake PM routes tracker issues into the brief queue.

### Altitude 0: Direction-setting

The workspace coordination system treats strategic direction as a committed artifact, not a meeting outcome. A product strategist works at altitude 0 — years, portfolio, company OKRs — using the product-strategy skills to commit market context, portfolio position, and strategic direction to `docs/product/shaping/`. The key output is the OKR cascade: the skill translates company OKRs into team-level OKRs, identifies the gaps between current state and targets, and routes each gap as a `{type = "strategy"}` entry into `[shaping_queue].backlog`. These entries become the altitude-1 inputs the product engineer picks up next. Other committed artifacts from this altitude — PRFAQ, SWOT analysis, competitive landscape, UX strategy, content strategy — give the shaping room a traceable altitude-0 anchor that any team member or agent can read without attending the planning meeting that produced it.

### Altitude 1: Shaping

A product engineer (PE) works in the shaping room, moving a signal through the shaping sequence: `frame-situation` classifies the signal and produces a typed situation finding; `identify-opportunities` surfaces the JTBD structure (functional, emotional, and social jobs); `diverge-solutions` generates at least three structured comparable options; `de-risk-intent` identifies the riskiest assumption and suggests a prototype approach; the PE validates through research, user contact, or internal review; `place-bet` commits a betting table with rationale and accepted risks; `map-capabilities` maps all capability areas the initiative touches. Each step produces a committed artifact in `docs/product/shaping/` that survives the session — when the shaping chain is complete, `author-brief` synthesises it into a brief that enters `[brief_queue].draft`.

The reason the chain of committed artifacts matters: when an engineer or agent picks up the spec six weeks later, they can trace the bet back to the original signal without asking anyone. The shaping chain is the provenance of the brief.

Before a signal enters this sequence, it is triaged. The [capture work](../how-to/capture-work.md) how-to covers how a surfaced item is classified (build vs. shaping, mode) and routed into the shaping queue — the entry point that precedes `frame-situation`.

### Tracker intake

A PM who lives in a tracker (Linear, Jira, GitHub Issues) takes a shorter path into the brief queue. The tracker-brief-intake skill fetches the issue, maps its metadata to DoR fields, and prompts interactively for anything the tracker issue does not capture (Appetite, Rabbit holes, Instrumentation). The brief enters `[brief_queue].draft` with an `Epic:` back-link to the originating tracker issue. When the spec ships, "Fixes #NNN" in the PR body auto-closes the issue. The PM does not need to leave their tracker — the platform adapts to the tracker, not the other way around.

All three paths converge here: a DoR-ready brief in the queue. From there, `receive-brief` decomposes it into specs and routes them to `[work].queue` for an engineer or agent to execute.

**Source journey maps:**
[product-strategist-sets-direction](../../../product/journeys/product-strategist-sets-direction.md) ·
[product-engineer-shapes-initiative](../../../product/journeys/product-engineer-shapes-initiative.md) ·
[pm-intakes-from-tracker](../../../product/journeys/pm-intakes-from-tracker.md)

---

## Engineer

An engineer using this coordination system works primarily at altitude 2 — the build room — running the work-loop on specs drawn from the initiative queue. The altitude-2 touchpoints are session orientation, spec execution, and ship write-back.

### Session orientation

At the start of every session, the engineer runs `workspace-status`. It reads `workspace.toml`, resolves the dependency DAG across all queues, and surfaces in one command: the active initiative, ready specs in priority order, blocked items with their blocking reasons, and parallel candidates — specs whose dependencies are all satisfied and which can therefore proceed concurrently. Running `workspace-status` before touching any code is what distinguishes coordinated work from ad-hoc work: the queue state in `workspace.toml` is the source of truth, and a stale local mental model is the largest single source of coordination waste on multi-person or multi-agent teams.

### The work-loop

The engineer's primary execution pattern is the work-loop: plan → build → verify → review. The plan step surfaces assumptions and writes a task breakdown before any code is written. The build step implements the smallest coherent change per task. Verify runs the project's gates (lint, typecheck, tests) and any manual QA the spec requires. Review is an adversarial pass in a fresh context — it reads the diff against the spec and catches what the implementer missed.

The [plan and execute non-trivial work](../how-to/plan-and-execute-non-trivial-work.md) how-to is the step-by-step recipe for running the loop. This guide explains why the loop is structured the way it is: gates are necessary but not sufficient — an adversarial reviewer in a fresh context catches scope creep, spec drift, and missing edge cases that passing automated gates cannot. The loop's termination criterion is "gates green and review clean," not "the engineer feels done."

### Initiative path vs. ad-hoc path

The initiative path and the ad-hoc path differ at session start and at ship. On the initiative path, the engineer orients via `workspace-status`, invokes `work-loop` with the spec slug, and on ship the spec transitions `active → shipped` in `workspace.toml` — the next engineer or agent starting a session sees the correct queue state immediately. On the ad-hoc path, the engineer picks a task from memory, a ticket, or a team discussion; `work-loop` reads the spec in isolation; no queue state is updated on ship.

The initiative path is the right default whenever the spec belongs to an initiative queue — the coordination overhead is near-zero and the write-back makes the team's queue state reliable for everyone who comes next. The ad-hoc path is appropriate for genuinely standalone tasks that would not belong in a brief.

**Source journey maps:**
[engineer-adopts-coordination](../../../product/journeys/engineer-adopts-coordination.md) ·
[engineer-runs-work-loop](../../../product/journeys/engineer-runs-work-loop.md)

---

## Agent

An AI agent using this coordination system works at altitude 2 — autonomously, without a human in the loop during the execution phase. Its operating pattern differs from an engineer's in one fundamental way: it must orient entirely from committed state, because it carries no memory of prior sessions and no human will answer a question mid-execution.

### Cold-start orientation

When a headless agent starts a session, its first action is `workspace-status`. This is cold-start orientation: no context from a prior session, no human to ask "what should I work on?" The command reads `workspace.toml`, resolves the DAG, and surfaces the active initiative and the next ready spec in one step. If a spec is already in `[work].active`, the agent confirms its position and begins. If nothing is in `active`, the agent picks the first unblocked item from `[work].queue` and claims it before starting. The committed state in `workspace.toml` is what makes autonomous session handoff work — each agent exits having written back its progress, so the next agent can orient in a single command without reading any prior session's context.

### Headless execution

Autonomous execution runs the same work-loop (plan → build → verify → review) that an engineer uses, with one operational difference: there is no human to intervene on gate failures. A gate failure requires the agent to diagnose and resolve it within the loop; if the failure is not diagnosable within the loop's iteration cap, the agent surfaces the situation in the PR description and stops. The loop terminates either at "gates green and review clean" or at a stated surface reason — it does not loop without bound.

The distinction between the agent's loop and the engineer's loop is not capability but accountability: an engineer's loop has human judgment available at every gate; the agent's loop is pre-authorized to proceed through gates autonomously, within the rules the `work-loop` skill encodes.

### The ship signal

When the spec is done, the agent submits a PR and moves the spec from `[work].active` to `[work].shipped` in `workspace.toml`. The ship signal is the committed write-back — not the PR submission itself, but the state transition in `workspace.toml`. This is what allows the next agent (or the engineer reviewing the session) to see what shipped without reading any prior session's context. `workspace-status` run at the start of the next session will show the shipped spec and surface whatever comes next.

The swarm extension of this journey — coordinated pipelines where a supervisor agent allocates specs to executor agents in parallel — is not yet covered here. (deferred: role-journey-agent-swarm-section)

**Source journey map:**
[agent-executes-spec](../../../product/journeys/agent-executes-spec.md)
