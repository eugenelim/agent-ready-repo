# ADR-0066: Reactive git at TurnEnd

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision-makers:** eugenelim

## Decision summary

- **Decision:** The harness (control plane) calls `git_status()` after each AI turn ends (TurnEnd) and commits any uncommitted artifacts; no `git_managed` flag is declared per lifecycle type in the manifest. The `git_commit` and `git_push` MCP tools are available for the AI agent to call directly, but the harness drives the commit lifecycle reactively rather than requiring each skill to declare its artifacts as `git_managed`.
- **Because:** Declarative `git_managed` flags would require the lifecycle manifest to correctly identify every file a skill might produce, and to declare whether each should be committed. Skills already produce files in well-known output directories; `git_status()` discovers all uncommitted artifacts in those directories without requiring per-type declarations. The reactive approach is simpler, more robust to new or renamed output types, and requires no manifest updates when skills are extended.
- **Applies to:** `packages/agentbundle/agentbundle/workspace_mcp.py` (the `git_status`, `git_commit`, `git_push` tool surface); the lifecycle manifest design (ADR-0067); any control-plane integration that manages the git lifecycle via workspace-mcp.
- **Tradeoff accepted:** The harness must call `git_status()` after every turn to decide whether to commit, rather than receiving a push-based signal when artifacts are ready. This adds one `git_status()` round-trip per turn. For sessions with many short turns (e.g., a clarification exchange), this is redundant overhead; for sessions with artifact-producing turns it is the minimal correct call.
- **Revisit if:** The lifecycle manifest grows to include per-type commit semantics (e.g., "commit immediately when artifact appears" vs. "commit at gate only"), at which point a declarative `git_managed` flag per type would enable push-based commit scheduling without `git_status()` polling.

## Context

When a control plane drives a work-loop session via ACP, the AI agent produces artifacts (spec.md, plan.md, code files, ADR files) that the control plane must commit and push for the PR workflow to work. workspace-mcp provides `git_status()`, `git_commit()`, `git_push()` as MCP tools that the AI agent (via session instruction) or the control plane (via `session/prompt`) can call directly.

The question is whether the commit lifecycle should be:
- **Declarative:** the lifecycle manifest flags each type as `git_managed: true/false`, and workspace-mcp automatically commits files when an artifact of a `git_managed` type appears (detected by the artifact watcher).
- **Reactive:** the control plane calls `git_status()` after each turn and decides whether to commit, using the result to determine what is uncommitted and whether a commit is appropriate.

The reactive approach is more robust: it does not require the manifest to be exhaustive, does not create race conditions between the artifact watcher and the commit tool, and gives the control plane full agency over commit timing (e.g., wait until a gate is reached before committing, rather than committing every intermediate file).

## Alternatives rejected

**Declarative `git_managed` flag per lifecycle type.** Each type in the manifest declares whether its artifacts should be committed automatically when they appear. workspace-mcp listens for artifact watcher events and calls `git_commit` when a `git_managed` artifact appears. Rejected because it creates a race between artifact creation (the watcher fires when the file appears) and artifact completion (the AI may still be writing the file); requires the manifest to be exhaustive; and requires manifest updates whenever a skill adds a new output type.

**Push-based TurnEnd signal.** The AI host emits a standard MCP event at turn end; workspace-mcp listens and calls `git_status()` then. This is equivalent to the reactive model but requires MCP turn-end event support that is not currently standard across all adapters. The reactive model (harness polls `git_status()` after turn end) achieves the same result without requiring a new MCP event type.

**Skill-level git commit calls.** Each skill calls `git_commit` via the MCP tool at its own completion point. This would require every skill to be aware of the MCP tool surface — the same coupling problem ADR-0063 rejects for elicitation. Rejected for the same reason: skills must remain adapter-agnostic.
