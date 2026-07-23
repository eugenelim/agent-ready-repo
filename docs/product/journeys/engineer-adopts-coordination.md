---
type: customer-journey
slug: engineer-adopts-coordination
persona: engineering-team-adopter
outcome: run-coordinated-ai-native-operations
surface: cross-platform
status: planned
initiative_links:
  - id: INI-002
    name: Platform Core
    milestones: M1–M6
    role: primary
updated: 2026-07-19
---

# Journey: Engineer adopts AI-native coordination

**Use it when:** your team hits the coordination gap — sessions expire, context is lost, or a second agent has no idea what the first one did.
**You provide:** your repo with core pack installed, an existing working rhythm with 1–2 agents, and willingness to commit `workspace.toml` as the session-start artifact.
**You receive:** a DAG-resolved queue any agent can cold-start from, parallel specs that execute without collision, and a team lead view that shows exceptions rather than every action.
**Your decisions:** shape and prioritise work (Stage 2); answer DoR prompts when briefing (Stage 3); approve plans and handle gate failures during execution (Stage 4).

**Persona:** A platform-oriented engineering team — internal tooling, multi-component systems, or a developer platform group — that already runs one or two AI agents but has no coordination layer. Sessions expire and context is lost. A second agent knows nothing about the first. The team has no visibility into what is in flight.

**Outcome:** Any agent can cold-start a session, run `workspace-status`, know exactly what to work on, and the team lead only reviews what diverged. Multiple specs execute in parallel without collision. Shaping artifacts survive sessions. The team operates at Step 2 maturity reliably.

**Surface:** cross-platform — CLI/terminal, harness-agnostic.

**Trigger:** The team hits the coordination gap — session context lost, duplicate work, or a colleague joins and has no idea what is in flight.

**End state:** `workspace-status` is the standard session-start command. Briefs flow through the queue from any source. Specs are coordinated via `workspace.toml`. The team lead reviews exceptions, not every action.

---

## Prerequisites

| Pack | Scope | Status | Provides |
|---|---|---|---|
| core | repo | current | `work-loop`, `new-spec`, `receive-brief`, `workspace-status` (M1.5), `author-brief` (M1 Batch 4) |

**One-time setup:**
1. Install core pack at repo scope.
2. After M1 Batch 2 ships: `workspace.toml` is committed to `main` pre-populated with the INI-002 queue — no branch setup needed. Run `workspace-status` to verify.

**Scale:** the full journey (shaping + brief + build) requires all M1 ACs. If the team only needs build-room coordination (Stages 3–5), core pack + `work-loop` alone is sufficient; `workspace.toml` and `workspace-status` add queue visibility.

---

## Interaction model

```mermaid
sequenceDiagram
    participant H as Engineer
    participant A as Agent
    participant SK as Skills (packs)
    participant WS as workspace.toml

    Note over H,WS: Session start (M1.5+)
    H->>SK: workspace-status
    SK->>WS: Read [shaping_queue]+[brief_queue]+[work], resolve DAG
    WS-->>SK: Active initiative · parallel candidates · blocked items
    SK-->>H: spec/m1-work-loop is ready · spec/m1-receive-brief blocked on brief-template

    Note over H,WS: Brief intake (M1 — author-brief)
    H->>SK: author-brief [pastes external brief text]
    SK-->>H: Appetite? Rabbit holes? Instrumentation?
    H->>SK: [answers DoR prompts]
    SK->>WS: [brief_queue].draft += briefs/new-brief.md
    SK-->>H: Brief queued — run receive-brief to decompose into specs

    Note over H,WS: Execute and ship (M1.7)
    H->>SK: work-loop · spec/m1-work-loop
    SK->>WS: Confirm spec in [work].active
    Note over SK: plan → build → verify → review
    SK->>WS: active → shipped · surface next ready item
    SK-->>H: Shipped · Next: spec/m1-receive-brief · Update roadmap.md?
```

---

## Stage 1: Install & Orient

| Row | Content |
|-----|---------|
| **Actions** | Discovers the platform. Installs agentbundle. Reads AGENTS.md. Runs `workspace-status` — orients from `workspace.toml` and surfaces the next item without reading any other file. |
| **Emotions** | Curious then oriented (neutral → positive). First action is clear. |
| **Remaining pains** | "I don't understand the vocabulary — Brief vs Spec vs Project." The vocabulary page (M6) is not yet available; the glossary in `docs/CONVENTIONS.md` is the current reference. |

---

## Stage 2: Shape Work

### Now

| Row | Content |
|-----|---------|
| **Actions** | Uses `frame-intent` and `de-risk-intent` to scope an initiative. Produces framing artifacts in-session. Tries to figure out when shaping is done enough to write a brief. |
| **Emotions** | Engaged but uncertain (neutral). Output lives in session context, not the repo. |
| **Pains** | "My shaping output doesn't survive the session." "I don't know when shaping is done enough to graduate to a brief." "I have no artifact I can hand to someone else." |
| **Opportunities** | Committed shaping artifacts in `docs/product/shaping/` with a visible graduation criterion (Outcome + Appetite + ≥1 Rabbit hole = ready to brief). |

> **With M2** — `frame-situation`, `place-bet`, `map-capabilities` ship: skills write committed artifacts to `docs/product/shaping/`; `[shaping_queue]` items move through the six-step sequence with write-back; graduation criterion: `author-brief` creates the brief from the bet + capability map and writes to `[brief_queue].draft`.

---

## Stage 3: Brief & Queue

| Row | Content |
|-----|---------|
| **Actions** | Receives a brief externally (email, Linear Issue, verbal). Runs `author-brief` — elicits DoR fields interactively, creates brief file, writes to `[brief_queue].draft`. Runs `receive-brief` — moves brief to ready and writes specs into `[work].queue`. |
| **Emotions** | Efficient (positive). External input → queued specs in one flow; no manual reformatting. |
| **Remaining pains** | "Linear issues still need the `author-brief` step — there is no automatic intake from the tracker until M5." |

---

## Stage 4: Execute & Ship

| Row | Content |
|-----|---------|
| **Actions** | Picks up a spec from `workspace-status`. Runs `work-loop`. Completes the spec. Submits PR. `work-loop` moves spec `active → shipped` in `workspace.toml`; surfaces next ready item from the DAG; prompts `roadmap.md` update. |
| **Emotions** | Satisfied and oriented (positive). Spec shipped and the queue reflects it. |
| **Remaining pains** | "`roadmap.md` update is prompted but still requires a manual PR — it is not auto-written (per CONVENTIONS)." |

---

## Stage 5: Session Continuity

| Row | Content |
|-----|---------|
| **Actions** | Session ends. New session — next day, a colleague, or a new agent. Runs `workspace-status`. One command surfaces active initiative, queued specs, DAG state, blocked reasons. Reads `workspace.toml` from the local working directory (file lives on `main`; consistent on any branch). |
| **Emotions** | Confident (positive). Context is committed; orientation is immediate. |
| **Remaining pains** | "An agent starting fresh still has no context about mid-session decisions that weren't committed." Partial-progress capture feeds INI-005. |

---

## Frontstage actions

- **Skill:** install-agentbundle
- **Skill:** read-agents-md
- **Skill:** run-frame-intent
- **Skill:** run-de-risk-intent
- **Skill:** receive-external-brief
- **Skill:** run-author-brief
- **Skill:** run-receive-brief
- **Skill:** pick-spec-from-queue
- **Skill:** run-work-loop
- **Skill:** submit-pr
- **Skill:** run-workspace-status
- **Skill:** resume-from-session-start

---

## Emotional arc

The M1 flow — Stage 1 through Stage 5 — is now positive end-to-end. The remaining friction lives in Stage 2 (Shape Work) where M2 skills are still pending, and in Stage 3 where tracker intake (M5) is still manual.

**Remaining gap:** "My shaping output doesn't survive the session." Committed shaping artifacts (`frame-situation`, `place-bet`, `map-capabilities`) and `[shaping_queue]` write-back are M2 scope.

---

## Handoff notes

**For `map-screen-flow`:** Stage 3 (Brief & Queue) and Stage 5 (Session Continuity) carry the highest-opportunity pains. The `author-brief` flow (external input → DoR elicitation → queue write) and the `workspace-status` output view are the highest-priority screen-level inputs for any future web surface.

**For `blueprint-service`:** backstage dependencies include `workspace.toml` on `main` (skills edit locally and commit in the same spec PR per the resolved write protocol — RFC-0064 Known Unknowns), `docs/product/briefs/` (brief file store), `docs/product/shaping/` (shaping artifact store), agentbundle skill loader.
