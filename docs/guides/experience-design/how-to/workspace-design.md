# Design a workspace surface

**Use this when:** you are designing a productivity tool, collaborative environment, agentic UI, or any surface whose primary purpose is to support sustained professional work across sessions.
**Prerequisites:** `experience-design` pack installed; a session arc and collaboration model named.
**Result:** a structural specification for the workspace surface — context-persistence architecture, attention zone layout, collaboration state IA, interrupt design, and the agentic patterns that make the surface feel controllable.

> **How-to** — task-oriented. Pick `workspace-design` when the surface supports sustained professional work; pick `interaction-design` when the surface is a conventional screen state machine. For *why* the thread is shaped this way, read [The experience thread](../explanation/the-experience-thread.md).

## workspace-design vs. interaction-design — the key decision

Both skills design *how* a surface behaves, but they operate at different scopes and for different surface genres:

| Signal | Skill |
|---|---|
| Surface supports repeated, cross-session professional work | `workspace-design` |
| Surface includes autonomous agents running tasks on the user's behalf | `workspace-design` |
| Surface coordinates multiple agents with a visible dependency structure | `workspace-design` |
| Dashboard or monitoring view for data comprehension and action | `analytical-design` |
| Component needs a finite-state behavioral model (form, button, wizard step) | `interaction-design` |
| Screen needs feedback timing, validation flow, and micro-interactions | `interaction-design` |
| Cross-screen navigation routes are being decided | `user-flow` |

`workspace-design` is IA and structure — it specifies *how the workspace is organized* so that context, collaboration state, and agent activity are legible. `interaction-design` is behavioral — it specifies how a specific component or screen *responds* to user actions within that structure. They are complementary: run `workspace-design` first to set the structural frame, then run `interaction-design` for the individual components that inhabit it.

Do **not** use `workspace-design` for dashboards and monitoring views — those belong to `analytical-design`. Do **not** use it for marketplace surfaces — those belong to `marketplace-design`.

## The agentic-UI surface constraint

A workspace surface becomes an agentic UI when autonomous agents run tasks on the user's behalf. What makes this distinct from a standard product screen:

- **Agent activity must be legible without demanding constant attention.** The user needs to know what the agent is doing, in what order, and where they need to intervene — without a live notification stream demanding focus.
- **Every consequential agentic output needs a review surface before it is applied.** An agent that writes files, sends messages, or modifies data without a review step between output and application has no undo.
- **HITL confirmations must name the consequence before the action.** A human-in-the-loop confirmation dialog names the action clearly, makes the consequence visible (how many files? which ones?), and offers a "show me what this affects" affordance before the user approves.
- **Multi-agent coordination must be visible.** When multiple agents run in parallel or in a chain, the dependency graph — which agents are running, which is waiting for which, where the current bottleneck is — must be visible from the workspace surface. A coordination graph hidden from the user produces a surface that feels unpredictable.

These are structural constraints, not component-level decisions. They determine the workspace's zone layout — where the task queue lives, where the output review surface sits, how the HITL confirmation is positioned — before any individual component is designed.

## How to author a workspace brief

Before running `workspace-design`, name three things:

**1. The session arc** — what does a complete work session look like? Walk all five stages:

| Stage | What the user needs |
|---|---|
| Arrive | Context re-establishment — where was I? |
| Orient | What requires attention — what's new? |
| Work | Uninterrupted focus on the primary task |
| Persist | My work is safe when I leave |
| Collaborate | Share, hand off, or review with another person |

Decisions made for the Work stage often break the Arrive and Persist stages. Walk the arc explicitly before designing any zone.

**2. The collaboration model** — single-user, asynchronously collaborative, or real-time collaborative. The answer drives presence indicators, live-editing state IA (whose cursor is where, whether two users can edit the same object simultaneously), and the sharing model.

**3. The agentic patterns in scope** — task queue visibility, agent status indicators (running / waiting for input / error / complete), HITL confirmation surfaces, output review surfaces, multi-agent coordination visibility — or none, if the surface is non-agentic.

Then invoke `workspace-design`:

> "Design the workspace for [surface name]. The session arc is [arrive/orient/work/persist/collaborate description]. The collaboration model is [single-user / async / real-time]. The agentic patterns in scope are [task queue / HITL / output review / multi-agent coordination / none]."

`workspace-design` produces: the context-persistence architecture (last-location persistence, returning-session re-orientation, breadcrumb/recents/activity), the attention zone layout, the collaboration state IA, the interrupt escalation ladder, and the agentic pattern specifications.

## The multi-agent coordination pattern

When multiple agents run in parallel or in a chain, the workspace surface must make the dependency structure visible at a glance:

- **Which agents are running** — named, not anonymous
- **Which agent is waiting for which other agent** — dependency direction made visible
- **Where the current bottleneck is** — blocked items surface without requiring the user to poll
- **Where the user can intervene** — a recoverable action is reachable at every blocked or errored agent

The coordination IA is designed at the structural level first — the zone that shows the graph, the ambient vs. focal signals, the intervention affordance — before any individual agent status indicator is designed. `interaction-design` handles the per-component state machines (the indicator's own running / waiting / error / complete transitions); `workspace-design` sets the structural frame those components inhabit.

## Common mistakes

**Using `interaction-design` for workspace IA.** If you reach for `interaction-design` to design the zone layout, context-persistence model, or agent activity visibility, the output will be a component behavioral model, not a structural specification. Run `workspace-design` for the structure; run `interaction-design` for the components that live in it.

**Designing the Work stage only.** A workspace surface that looks good in the focused-work state but has no designed Arrive or Persist stage will lose users' context on every return. Walk the session arc explicitly.

**Omitting the task queue.** An agentic workspace with no visible task queue leaves the user guessing what the agent is doing. The task queue is the agent's working memory made visible: pending, active, completed, blocked.

**Making agentic output non-reviewable before application.** An output applied before the user can review it is an output without an undo. Design the output review surface before designing the output itself.

**Using focal interrupts for ambient information.** Notification modality inflation — sound, motion, or modal overlays for non-urgent information — trains users to dismiss focal interrupts without reading them. The default posture for all notification types in a workspace is ambient; escalate to focal only when the information is time-sensitive and action-required.
