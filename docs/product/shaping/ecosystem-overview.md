---
initiative: INI-001
type: overview
status: draft
shaped: 2026-07-18
---

# INI-001 AI-Native Ecosystem — Initiative Overview

Six initiatives that together enable AI-native engineering maturity. INI-002 starts now. Each subsequent initiative is triggered by a specific milestone in the prior one; none starts speculatively.

## The six initiatives

| ID | Name | Scope | Status |
|---|---|---|---|
| INI-001 | AI-Native Ecosystem | Umbrella — coordinates the others; never directly built | Active (umbrella) |
| INI-002 | Platform Core | Skills, packs, governance, workspace coordination, PE capabilities | Active — M1–M5 shipped; P5 (Adopt) in progress |
| INI-003 | Coding CLI Adapter Pack | Headless CLI adapters: Claude Code `-p`, Codex CLI, Kiro CLI, Copilot CLI, Gemini CLI | Not started |
| INI-004 | Remote Agent Runtime | Cloud/VM-hosted and orchestration harnesses: Devin, Manus, Omnigent, and pluggable sandbox providers | Not started |
| INI-005 | Infra & Observability | State persistence, telemetry, monitoring, alerting | Not started |
| INI-006 | Control Plane | Dashboards, brief-to-agent dispatch, exception-surfacing UI | Not started |

### INI-002 · Platform Core

The foundation the others build on. An open, harness-agnostic catalogue of skills and packs that any team can install — from a solo engineer to a hundred-person platform team.

**Already shipped:** three loops that form the operational heartbeat — the discovery loop (G0→G3: raw idea → ratified decision brief), the work loop (G3→G5: spec → plan → build → verify → review), and the release loop (G4→G5: verified build → shipped). All three are proven in production.

**Milestone delivery (RFC-0064):** M1–M5 shipped. M6 re-sequenced by Amendment #3 into P1–P5 journey-phase slices: P1 (Orient + Capture), P2 (Shape — M2 PE skills), P3 (Brief → Build), and P4 (Intake edges — M5 trackers) shipped; P5 (Adopt) in progress, gated on `research:adopter-persona` desk-research completing.

**Pack architecture:** a multi-pack catalogue — core (workspace coordination, brief lifecycle, foundational skills), PE pack (product engineering: frame-intent, frame-domain, explore-options, de-risk-intent, decompose-intent), governance-extras (ADR, RFC, rfc-status), desk-research pack (structured research lifecycle), experience-design pack (journey maps, screen flows, creative direction), architect pack (C4 diagrams, ADRs, architecture review), and connector packs (atlassian, linear). Teams compose from the catalogue; no pack is mandatory.

**Harness-agnostic design:** the skill surface runs unchanged across Claude Code (local), Devin (VM-snapshot), Copilot Agent (cloud-session), and Kiro today — each harness reads the same `.md` skill files; MCP-capable harnesses consume them as registered tools. INI-003 and INI-004 wire this more deeply; INI-002 already works with manual session pickup.

**Governance machinery:** ADRs (immutable architectural decisions), RFCs (reviewed decisions with full lifecycle), specs (technical decomposition with traceability lint). The traceability lint enforces that every spec links to a brief and every brief links to an intent — structural orphans are caught at CI.

**Delivers:** the shaping room (six-step product thinking at initiative altitude — Outcome → Problem → Diverge → Validate → Bet → Spec), the work queue (`workspace.toml` + brief queues), and the vocabulary (Project / Milestone / Brief / Spec mapped to Linear, Jira, GitHub, Azure DevOps, Asana).

### INI-003 · Coding CLI Adapter Pack

The first harness tier. Adapters for headless CLI-invoked agents — the execution model where a language model is called as a subprocess, reads a task, executes work, and writes back. No persistent session, no cloud VM — a CLI invocation orchestrated by CI/CD, a supervisor agent, or a human running a command.

**Target harnesses:**

| Harness | CLI invocation | Key characteristic |
|---|---|---|
| Claude Code | `claude -p "<prompt>"` | Reads `.claude/` skills; MCP tool integration |
| Codex CLI | `codex "<task>"` | OpenAI function calling; sandbox isolation |
| Kiro CLI | `kiro "<task>"` | Kiro CLI 2.0: formal headless mode (`--no-interactive`, `KIRO_API_KEY`); MCP startup validation; trust tiers; AWS-positioned (CodeBuild + Bedrock AgentCore Runtime) |
| GitHub Copilot CLI | `gh copilot suggest` / agent mode | GitHub-integrated; PR-aware |
| Gemini CLI | `gemini "<task>"` | Google Workspace integration; long-context |

**What each adapter does:**
1. Reads `workspace.toml` active work item at session start
2. Formats the task as the harness-specific CLI invocation with appropriate context
3. Captures output and maps it back to `workspace.toml` (progress, gate outcomes, completion)
4. Handles harness-specific quirks: tool format, context window limits, output parsing, skill discovery path

**Swarm capability:** INI-003 enables running a coordinated swarm of headless CLI agents in parallel — each agent reads from `[work].active` and takes an unblocked spec. `workspace.toml` is the collision-free coordination layer: each spec has exactly one active agent. A CI/CD supervisor (or a human) launches N agents; `workspace.toml` determines who works on what.

**Why separate from INI-004:** CLI adapters are stateless (each invocation is fresh), portable (run locally, in CI/CD, or on any compute), and straightforward to write (thin wrapper around a CLI command). Cloud runtimes (INI-004) have stateful session management, proprietary execution environments, and more complex integration surfaces.

**Trigger met (INI-002 M1 shipped).** Harness adapter specs for Kiro, Codex, Copilot CLI, and Gemini CLI shipped inside INI-002, establishing the per-adapter pattern. INI-003 as a formal initiative picks up the layer above those individual adapters: adapter factory, atomic claim protocol (`workspace.toml`-coordinated), and completion-signal conventions that the per-adapter specs deferred. INI-003 RFC not yet opened.

**Namespace note:** `workspace.toml` reuses the INI-003 identifier for the Digital Experience Doctrine internal repo initiative — a separate namespace. The ecosystem framework's INI-003 (Coding CLI Adapter Pack) is unstarted as a formal initiative and is not tracked in `workspace.toml`.

### INI-004 · Remote Agent Runtime

The cloud and orchestration harness tier. Wires INI-002's skill surface into runtimes that own their own execution environment and session lifecycle — agents that persist state across sessions without manual `workspace.toml` reads.

**Execution models in scope:**

| Harness | Category | Execution model | State persistence |
|---|---|---|---|
| Devin | Standalone cloud agent | Sandboxed cloud VM, long-running | VM snapshots; session resumes from snapshot |
| Devin Outposts | On-prem / customer infra | Executes on workstations, VMs, Kubernetes, Apple silicon (launched July 2026) | Customer-controlled compute; Devin-managed state |
| GitHub Copilot Coding Agent | Cloud coding session | Platform-managed, GitHub-integrated | Session-scoped; GitHub context |
| Omnigent | Meta-harness / orchestration | Pluggable sandbox providers; routes to underlying agents (Beta, July 2026) | Omnigent server state; delegates to Modal, E2B, Daytona, Databricks Sandboxes, Kubernetes |
| Anthropic Managed Agents | Managed agent service | Scheduler + dreaming pass + rubric grading on Agent SDK | Anthropic-managed; partial scope overlap with INI-004 — assess before RFC |

**Omnigent in detail:** Released by Databricks in June 2026 (Apache 2.0); PyPI-published 2026-07-21; still Beta as of July 2026 with no GA date announced — INI-004 integration gates on GA. Omnigent is an orchestration layer that sits *above* other agents (Claude Code, Codex, Cursor, Pi) and routes work to pluggable sandbox providers. Key capabilities: swap harnesses without rewriting, enforce policies and sandboxing, collaborate in real time. A managed Databricks enterprise tier (currently Beta) provisions sandboxes inside a Databricks workspace with Unity AI Gateway integration. Omnigent is not a peer of Devin — it orchestrates agents across sandbox providers. For this initiative, Omnigent is interesting as the **dispatch and routing layer** that INI-002's `workspace.toml` can feed: Omnigent reads intent, selects the appropriate underlying agent and sandbox, and executes. This aligns naturally with the `workspace.toml` coordination model.

**Sandbox providers (as of July 2026):** Modal ($355M Series C; GPU-inside sandboxes, high-throughput compute); Daytona ($24M Series A; ~90ms cold start, compliance-first secure environments); E2B (pause/resume with filesystem and memory state intact); Databricks Sandboxes (integrated with Unity AI Gateway); Kubernetes (self-managed).

**Anthropic Managed Agents:** Scheduler, dreaming pass, and rubric grading on the Agent SDK. Partial scope overlap with INI-004 around dispatch, state management, and evaluation. The scope boundary between Managed Agents and INI-004's adapter layer needs to be drawn explicitly before opening the INI-004 RFC.

**The harness adapter pattern:** a thin, harness-specific wrapper that maps INI-002 skill invocations (via agent-readable `.md` + MCP tool registration) to each runtime's tool surface. Handles: reading `workspace.toml` at session start, identifying active work, orienting the agent, executing via the work-loop, and writing completion state back.

**Session pickup protocol:** on session start — (1) read `workspace.toml` from the initiative umbrella branch, (2) identify `[work].active` specs and `blocked_on` dependencies, (3) orient the agent to the current task, (4) execute via INI-002 work-loop, (5) write completion state back.

**MCP as the cross-harness bridge:** harnesses that support Model Context Protocol consume INI-002 skills as registered MCP tools, enabling dynamic skill discovery without per-harness packaging.

**Trigger met (INI-002 M2 shipped).** Concurrent window with INI-003 is open; both can progress in parallel. INI-004 RFC not yet opened; assess Anthropic Managed Agents scope overlap before opening.

### INI-005 · Infra & Observability

The observability floor. Closes the gap between INI-002's declared intent (`workspace.toml`) and actual execution continuity — state that survives session boundaries, telemetry that makes exceptions visible, and alerting that surfaces them upward.

**State persistence:** the specific state that must survive session boundaries — `workspace.toml` (declared intent), spec execution progress (plan step, current file, intermediate artifacts), agent context (decisions made mid-task not yet committed), and gate outcomes (what passed, what failed, what was waived). Without INI-005, this state resets at every session end; with INI-003/INI-004's session pickup it is read from git; with INI-005 it is persisted with full fidelity.

**Telemetry events:** the schema matters for exception-based review. Core events: `spec-started`, `gate-reached`, `gate-passed`, `gate-failed`, `gate-waived`, `budget-exceeded` (time or token), `spec-stalled` (no progress past a threshold), `spec-shipped`. Each event carries: spec slug, milestone, agent identity, timestamp, gate name (where applicable), and outcome metadata.

**Exception detection:** anomaly patterns that trigger alerts — repeated gate failures on the same step, budget overrun beyond a threshold, spec stalled for N consecutive sessions, dependency cycle detected in `blocked_on`. Detection logic reads the telemetry stream; thresholds are configurable per project.

**The monitoring feedback loop:** telemetry stream → INI-005 pattern detection → anomaly event → INI-006 surfaces to team lead → human decision (resume / redirect / reassign) → feedback written back to `workspace.toml` → agent picks up on next session.

Trigger: INI-004 M1 shipped — the remote runtime must exist before persistent state and telemetry have an execution surface to observe.

### INI-006 · Control Plane

The dispatch and monitoring surface. Translates INI-005's telemetry and INI-002's intent model into a human-facing interface so a team lead can manage ~100 agents by exception rather than by constant review.

**Three user roles and what each needs:**

| Role | Primary need | Key view |
|---|---|---|
| PM / product lead | Shaping progress visibility; brief queue health | Shaping queue status, brief DoR, milestone burndown |
| Team lead | Exception review; agent dispatch decisions | Exception alerts, active spec map, reassignment controls |
| Engineer | Spec assignment clarity; code review surface | My active specs, gate outcomes, PR queue |

**Brief-to-agent dispatch:** reads `workspace.toml [brief_queue].ready` → presents available specs → team lead or system assigns to an available agent session in the harness (via INI-004's dispatch API). Pull model (agents claim work) and push model (team lead assigns) both supported. Omnigent's routing layer is a natural integration point here — INI-006 dispatch can delegate to Omnigent, which selects the appropriate underlying agent and sandbox.

**Multi-agent visibility:** a real-time view of every active spec across all agent sessions — what step each is on, what gate is pending, what has stalled. Data model: `workspace.toml` + INI-005 telemetry.

**Exception routing flow:** INI-005 anomaly event → INI-006 surfaces alert to team lead with context (spec slug, what failed, how many times, budget consumed) → team lead chooses: resume as-is / redirect with new context / reassign to different agent / escalate → decision written back to `workspace.toml` as a `blocked_on` or context note → agent picks up on next session.

**Web surface:** INI-002 M6 builds the Astro project index (non-engineer PM visibility). INI-006 extends this with real-time dispatch and monitoring — the Astro site is the natural UI foundation.

Trigger: INI-005 M1 shipped — the control plane is only meaningful when the observability floor it reads from exists.

## How the initiatives connect

Both INI-003 and INI-004 trigger conditions are now met and the concurrent window is open:

```
INI-002 M1–M5 shipped ✓ (P5 in progress)
  ↓ M1 trigger met → INI-003 window open (Coding CLI Adapters) — RFC not opened
  ↓ M2 trigger met → INI-004 window open (Remote Agent Runtime) — RFC not opened
  [INI-003 and INI-004 may progress concurrently]
  ↓ INI-004 M1 ships
INI-005 starts (Infra & Observability)
  ↓ M1 ships
INI-006 starts (Control Plane)
```

Each step adds one capability layer. INI-003 and INI-004 are independent of each other and can progress in parallel. INI-005 requires INI-004 M1 specifically (the observability surface has no execution layer to observe until INI-004 ships).

| Initiatives active | Maturity ceiling |
|---|---|
| INI-002 only | Step 2 foundation; disciplined teams can approach Step 3 manually |
| INI-002 + INI-003 | Step 2 with CLI-driven agent swarms; multiple headless agents coordinated via `workspace.toml` |
| INI-002 + INI-003 + INI-004 | Structured session handoff across cloud runtimes; agents resume automatically; Omnigent dispatch |
| + INI-005 | Observable exceptions; Step 3 with monitoring |
| All six | Step 4: intent-steered, monitored by exception, 1000+ agent scale |

## How INI-002 ties to each sister initiative

**→ INI-003 (Coding CLI Adapters):** INI-003 wraps INI-002's skill surface for CLI invocation. The adapter reads `workspace.toml`, invokes the harness-specific CLI command with the appropriate context, and writes back. INI-002's `workspace.toml` schema (M1) is the stable contract INI-003 targets.

**→ INI-004 (Remote Agent Runtime):** INI-004 wraps INI-002's skills for cloud/VM-hosted runtimes. It handles session pickup, harness-specific tool surface mapping (MCP or static), and completion write-back. INI-002 M2 (stable shaping + coordination surface) is the trigger.

**→ INI-005 (Infra & Observability):** INI-005 reads INI-002's declared intent (`workspace.toml`, brief status, spec outcomes) and persists it across session boundaries into telemetry. INI-002 writes the intent; INI-005 ensures it survives and is measurable.

**→ INI-006 (Control Plane):** INI-006 surfaces INI-002's brief queue and workspace state as a dashboard. The project index (`docs/product/projects/`) and `workspace.toml` are the read model. INI-002 provides the data structure; INI-006 provides the human-facing UI.

## INI-002 independence

INI-002 is fully self-contained. Nothing in this repo depends on INI-003, INI-004, INI-005, or INI-006 existing.

**Without the sister initiatives, INI-002 alone delivers:**

- **Step 1 → Step 2, fully.** Multiple specs executing in parallel, coordinated through `workspace.toml`, with structured shaping and human review at each gate.
- **Disciplined approach toward Step 3.** The three loops and shaping room create the structural conditions for exception-based human oversight. Without automated telemetry, exceptions are surfaced manually — a team lead reads workspace state and reviews only what diverged. Demanding but achievable for disciplined teams.
- **Step 3 true completion: blocked on INI-004 + INI-005.** Automated session pickup and observable telemetry are required for exception-based review to work at ~100-agent scale.
- **Step 4: blocked on all six initiatives.**

The practical ceiling for INI-002 alone is **Step 2, reliably, with disciplined operation toward Step 2.5** — many agents in parallel, coordinated intent, structured shaping, human review at gates. This is independently valuable and the correct starting point for any team not yet at Step 2.
