---
initiative: INI-001
type: vision
status: draft
shaped: 2026-07-18
---

# Product Vision — INI-001 AI-Native Ecosystem

## Headline

A product OS for engineering teams — the coordination layer that closes the gap between one AI assistant and a thousand coordinated agents.

## The problem

Most engineering teams today are at Step 1 — our working hypothesis, to be validated by adopter-persona research. Models capable of sustained multi-step engineering work became widely available in 2024–2025. The bottleneck is no longer individual capability. It is coordination.

When a session ends, the context is gone. When a second agent starts, it knows nothing of the first. When ten engineers each run their own AI assistant, there is no coordination layer: duplicate work, conflicting decisions, no visibility into what is in flight. The gap between what a single agent can do and what a hundred coordinated agents could do — Step 3, the ecosystem-level first target — is not a model capability gap. It is a product OS gap.

The maturity ladder makes this concrete:

| Step | Mode | Scale | Characteristic |
|---|---|---|---|
| 0 | Gated | — | No AI; waiting for approval or tooling |
| 1 | Assisted | ~1 agent | Human-in-loop for every action; the most common starting point |
| 2 | Parallel | ~10 agents | Batch review; fast-moving startups |
| 3 | Supervised | ~100 agents | Exception-based review; leading AI-native orgs |
| 4 | AI-native | 1000+ agents | Intent-steered, monitored by exception |

The cliff between Step 1 and Step 4 is not a capability cliff — it is the same infrastructure gap that separated individual programmers from scalable engineering organizations in the 1990s. What built the latter was not better individual programmers. It was the OS, the toolchain, and the coordination patterns.

## The solution

An open, harness-agnostic product OS platform. A multi-pack catalogue that any team can install and compose — from a solo engineer to a hundred-person platform team. The platform provides four interlocking layers:

**The three loops.** The heartbeat of an AI-native organization. A discovery loop (G0→G3) that turns raw product ideas into ratified, build-ready decisions. A work loop (G3→G5) that executes specs through plan → build → verify → review. A release loop (G4→G5) that ships. All three loops are proven and shipped. Gate density decreases as teams mature: the loops provide the structure; exception-based review at Step 3 requires INI-003 (harness runtime), INI-005 (observability), and INI-004 (control plane) — in that dependency order.

**The shaping room.** Structured product thinking before any agent touches code. The six-step sequence (Outcome → Problem → Diverge → Validate → Bet → Spec) is applied at each altitude, producing a hierarchy of artifacts: product vision → strategy → capability map → initiative brief → brief. The brief is the shaped work unit — problem statement, appetite, rabbit holes, instrumentation — that hands off to the work loop. **The shaping room is where human judgment is injected into the pipeline; the build room** (the work and release loops) **is where agents execute under it.**

**The work queue.** `workspace.toml` — the coordination layer. A committed file on an initiative umbrella branch that declares what is being shaped, what is ready to build, what specs are executing, and what has shipped. Not execution state (that lives in the platform); declared intent that any agent can read to orient itself at session start.

**The vocabulary.** A common language that maps to every team's existing tools. Brief ≈ Linear Issue ≈ Jira Story ≈ GitHub Issue. Project ≈ Linear Project ≈ Jira Epic. Milestone ≈ Linear Milestone ≈ GitHub Milestone. Initiative ≈ Linear Initiative ≈ Jira Initiative. Spec ≈ Sub-issue ≈ Sub-task. Teams do not abandon their trackers; the platform connects to them.

## The adopter

Any engineering team that wants to run more agents than it has engineers. INI-002 is useful at Step 1 (one engineer, one agent, structured specs) and lays the foundation for the INI-001 ecosystem to scale to Step 4. Primary early adopters are platform-oriented engineering teams — internal tooling, developer platforms, multi-component systems — because they feel the coordination gap most acutely. Consumer product teams are secondary adopters, where the structured shaping machinery is the primary draw. Solo engineers are a long-tail but real cohort: the platform's discipline pays dividends even at one-agent scale.

## Why now

Models capable of sustained multi-step engineering work became widely available in 2024–2025 — the bottleneck shifted from model capability to coordination infrastructure. Every team has the ingredients; almost no team has the infrastructure to combine them. The three-loop OS pattern is proven. The `workspace.toml` coordination layer is the last missing primitive at the project level. The strategy and planning layer is the next wave.

## What this is not

Not a harness or agent runtime. Not a UI or dashboard. Not a cloud service — the platform runs wherever the agent runs, across any harness. Not a tracker replacement — it integrates with Linear, GitHub, Jira, and Jira Align. Not prescriptive about which AI model is used. Not a manager of execution state — platforms manage their own execution; this platform manages intent.

## Time horizon

At twelve months, teams using INI-002 have structured shaping workflows, coordinated brief queues, and `workspace.toml` as the session-start orientation artifact — the foundation for Step 2: parallel autonomy with ~10 agents coordinated. Reaching Step 3 (supervised autonomy, exception-based review, ~100 agents) requires INI-003, INI-005, and INI-004 — in that dependency order. The full Step 4 stack — intent-steered, monitored by exception, 1000+ agent scale — requires all five initiatives. The thirty-six-month horizon is the full INI-001 ecosystem, not this repo alone.

## Initiative structure

| ID | Name | Scope | Trigger |
|---|---|---|---|
| INI-001 | AI-Native Ecosystem | Umbrella initiative — never directly built | — |
| INI-002 | Platform Core | Skills, packs, governance, workspace management, PE capabilities (this repo) | Now |
| INI-003 | Coding CLI Adapter Pack | Headless CLI adapters: Claude Code `-p`, Codex CLI, Kiro CLI, Copilot CLI, Gemini CLI | INI-002 M1 shipped |
| INI-004 | Remote Agent Runtime | Cloud/VM-hosted and orchestration harnesses: Devin, Manus, Omnigent + sandbox providers | INI-002 M2 shipped |
| INI-005 | Infra & Observability | State persistence, telemetry, monitoring | INI-004 M1 shipped |
| INI-006 | Control Plane | UI dashboards, management interfaces, dispatch surface | INI-005 M1 shipped |
