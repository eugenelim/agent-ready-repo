---
type: customer-journey
slug: agent-executes-spec
persona: ai-agent
outcome: spec-executed-and-shipped-autonomously
surface: cross-platform
status: shipped
initiative_links:
  - id: INI-002
    name: Platform Core
    milestones: M1 (delivered — workspace-status M1.5, work-loop M1.7)
    role: primary
  - id: INI-003
    name: Coding CLI Adapter Pack
    milestones: M1+ (headless dispatch variant — pending)
    role: extends
updated: 2026-07-19
---

# Journey: Agent executes a spec autonomously

**Use it when:** an agent session starts and needs to orient, claim a spec, execute it through the work-loop, and exit with committed state.
**You provide:** a workspace with `workspace.toml` on `main` and write access to the spec branch.
**You receive:** a shipped spec, a PR passing gates, and `workspace.toml` updated so the next agent orients immediately.
**Your decisions:** None — this journey runs headless.

**Persona:** An AI agent — Claude Code, Codex CLI, Kiro CLI, or any headless harness — starting a fresh session with no persistent memory of prior sessions. The agent has no human in the loop for the execution phase. It must orient itself, pick up the right spec, execute it through the work-loop, navigate gates, submit a PR, mark the spec shipped, and exit cleanly.

**Outcome:** The spec is in `[work].shipped`. A PR is submitted and passing. `workspace.toml` reflects the new state. The next ready item is surfaced. The next agent starting a session can orient immediately without reading any prior session's context.

**Surface:** cross-platform — runs identically across Claude Code (`claude`), Codex CLI (`codex`), Kiro CLI (`kiro`), GitHub Copilot CLI, Gemini CLI. The skill surface (`workspace-status`, `work-loop`) is harness-agnostic; harness-specific conventions (MCP vs static `.md`, context window limits) are adapter concerns (INI-003).

**Trigger:** Agent session starts — invoked by a human running `claude`, by a CI/CD job dispatching a headless agent, or by a swarm supervisor allocating a spec.

**End state:** Spec shipped. PR submitted. `[work].active` updated to `[work].shipped`. Next ready item surfaced. Session exits cleanly with committed state — the next agent picks up from a known-good position.

---

## Prerequisites

| Pack | Scope | Status | Provides |
|---|---|---|---|
| core | repo | current | `workspace-status`, `work-loop` (workspace integration), `new-spec` |
| coding CLI adapter pack | user | planned (INI-003) | Harness-specific invocation, write-back contract implementation; one adapter per harness (Claude Code, Codex CLI, Kiro, etc.) |

**One-time setup:**
1. Install core pack at repo scope.
2. Install the harness-specific coding CLI adapter pack at user scope (when INI-003 ships).
3. `workspace.toml` must be committed to `main` and pre-populated (M1 Batch 2); no branch configuration needed — headless agents read it from the local working directory.
4. Agent must have write access to the spec branch — edits to `workspace.toml` commit with the spec PR (resolved write protocol; RFC-0064 Known Unknowns).

**Scale:** all harness shapes (interactive Claude Code, headless CI, remote agents via INI-004) use the same write protocol: edit `workspace.toml` locally in the working directory and commit in the same spec PR. Adapter-specific concerns (CLI invocation, tool surface, context window) are INI-003's scope.

---

## Interaction model

```mermaid
sequenceDiagram
    participant A as Agent
    participant SK as Skills
    participant WS as workspace.toml
    participant WL as work-loop (extended M1.7)
    participant R as Repo (spec branch)

    Note over A,WS: Session start — M1.5+
    A->>SK: workspace-status
    SK->>WS: Read [shaping_queue]+[brief_queue]+[work], resolve DAG
    WS-->>SK: Active initiative · spec/m1-work-loop is ready · spec/m1-receive-brief blocked (needs brief-template)
    SK-->>A: Oriented · next action: work-loop spec/m1-work-loop

    Note over A,WS: Claim spec (atomic — M1 convention / INI-003 adapter enforces)
    A->>WS: Confirm spec/m1-work-loop in [work].queue (not already active)

    Note over A,R: Execution — M1.7
    A->>WL: work-loop spec/m1-work-loop
    WL->>WS: Read workspace.toml at step 0 (context: initiative, milestone, spec)
    Note over A: plan → build → verify → review
    WL->>WS: On ship: active → shipped · surface next ready item
    WL-->>A: Shipped · next: spec/m1-receive-brief · Update roadmap.md?
    A->>R: Submit PR

    Note over A,WS: Exit — next agent starts from known-good state
    A->>SK: workspace-status (final — confirms shipped state visible)
    SK-->>A: spec/m1-work-loop: shipped · spec/m1-receive-brief: ready
```

---

## Stage 1: Orient

| Row | Content |
|-----|---------|
| **Actions** | Runs `workspace-status`. Reads `workspace.toml`, resolves DAG across all queues, surfaces the active initiative, ready specs, blocked items with reasons, and parallel candidates. |
| **Failure modes** | Context assembled incorrectly (wrong spec inferred — rare with `workspace-status`); spec already claimed by another agent (no atomic claiming until INI-003 adapter ships); stale `workspace.toml` if a prior agent did not write back on ship. |
| **Remaining pains** | "I can see the spec is ready but I can't confirm no other agent has claimed it — atomic claiming is an INI-003 adapter concern." |

---

## Stage 2: Validate Spec Context

| Row | Content |
|-----|---------|
| **Actions** | Reads the spec file. `work-loop` reads `workspace.toml` at step 0 to confirm the spec is in `[work].active` (or moves it there). Reads the brief it decomposes to understand scope. |
| **Failure modes** | Spec file doesn't exist yet (no `new-spec` has been run — agent runs `new-spec` first); brief is ambiguous; prior session's decisions were not committed (agent starts from scratch on uncommitted state). |
| **Remaining pains** | "If a prior agent made decisions mid-session that weren't committed, I have no way to see them." Partial-progress capture (gate-boundary handoff notes) is a post-M1 backlog item deferred to INI-005. |

---

## Stage 3: Plan

### Now and to-be (unchanged — work-loop already handles this)

| Row | Content |
|-----|---------|
| **Actions** | Runs `new-spec` if spec file doesn't exist, or reads existing spec. Writes or validates plan. Surfaces assumptions. |
| **Emotions** | N/A. **Failure modes:** plan makes assumptions that conflict with prior decisions; spec AC is too vague to plan against. |
| **Pains** | "The spec AC doesn't tell me what 'done' looks like precisely enough — I have to make assumptions that may conflict with the reviewer's expectations." "If the plan has multiple parallel tasks, I have no way to know which can run in parallel and which must sequence." |
| **Opportunities** | Spec AC written precisely enough for an agent to plan without ambiguity; `work-loop` plan step surfaces assumptions explicitly before build starts. Already partially addressed by work-loop's plan gate. |

---

## Stage 4: Build & Verify

### Now and to-be (unchanged — work-loop already handles this)

| Row | Content |
|-----|---------|
| **Actions** | Executes plan tasks. Runs gates: lint, typecheck, tests, traceability lint. Iterates on failures. |
| **Emotions** | N/A. **Failure modes:** gate failure not diagnosed (agent retries blindly); budget exceeded (too many tokens spent on a failing gate); traceability lint fails because spec or brief is missing a marker. |
| **Pains** | "A gate fails and I retry the same approach three times before trying something different." "I don't know how much budget I've consumed or how close I am to the limit." "The traceability lint fails but the error message doesn't tell me which marker is missing where." |
| **Opportunities** | Gate failure diagnostics that name the specific cause and suggest a corrective action; budget tracking surfaced to the agent mid-execution; traceability lint error messages that name the missing marker and the file. |

---

## Stage 5: Ship & Exit

| Row | Content |
|-----|---------|
| **Actions** | Submits PR. `work-loop` moves spec `active → shipped` in `workspace.toml` on ship; surfaces next ready item; prompts `roadmap.md` update. Exit state is committed — next agent orients in one `workspace-status` call. |
| **Failure modes** | PR submitted but write-back skipped (agent interrupted before `work-loop` completes write-back); `roadmap.md` update skipped. Next agent should run `workspace-status` to confirm state before starting. |
| **Remaining pains** | Partial-progress capture if the agent was interrupted mid-build (not committed). Full session continuity feeds INI-005. |

---

## Frontstage actions

- **Skill:** run-workspace-status
- **Skill:** validate-spec-in-active-queue
- **Skill:** run-new-spec-if-needed
- **Skill:** write-plan
- **Skill:** execute-plan-tasks
- **Skill:** run-gates
- **Skill:** submit-pr
- **Skill:** update-workspace-on-ship
- **Skill:** run-workspace-status-exit-state

---

## Failure mode arc (replaces emotional arc for agent persona)

Most critical failure: **Stage 1 (Orient)** — spec already claimed by another agent, or `workspace.toml` stale because a prior agent didn't write back. `workspace-status` catches the second; atomic claiming (INI-003) closes the first.

Second most critical: **Stage 5 (Ship & Exit)** — PR submitted but `work-loop` write-back interrupted. Next agent re-picks the same spec. Mitigation: always run `workspace-status` at session start to confirm state before claiming.

Remaining failure modes (partial-progress capture, budget tracking, gate diagnostics) are post-M1 backlog items — some feed INI-005 design.

---

## Handoff notes

**For `blueprint-service`:** backstage services include `workspace.toml` on `main` (spec claiming — INI-003 adapter concern; write-back on ship via resolved write protocol: agent edits locally and commits with the spec PR), spec branch (plan and build), gates (lint, typecheck, tests, traceability lint), PR submission. Atomic claiming across concurrent headless agents is an open INI-003 design question.

**For INI-003:** the headless dispatch variant of this journey (agent invoked via `claude -p` or equivalent) adds the adapter layer between Stage 1 (Orient) and Stage 2 (Validate Spec Context). The adapter reads `workspace.toml`, formats the invocation, and handles write-back. Stages 3–5 are identical.
