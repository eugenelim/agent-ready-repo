# Core

> The build loop — a repo-scope pack of skills, specialist subagents, hooks, and a full repo scaffold that gives any project a structured, verifiable implementation workflow.

## Why this pack exists

Without a shared implementation structure, every task starts from scratch: no plan contract, no verification gates, no way to tell when "done" is actually done. Core replaces that void with a mechanical loop (plan → execute → gate → review) where termination is determined by objective gates passing, not by the agent deciding it feels finished.

Install this first. All other packs assume it is present at repo scope.

## What it is

**Skills:** `work-intake` (route start, remember, status, and refresh requests into canonical workspace state), `work-loop` (the plan-execute-gate-review loop with an iteration cap), `new-spec` (write a spec and drive implementation from it), `bug-fix` (diagnose and fix a behavioral deviation), `adapt-to-project` (post-install configuration walkthrough), `init-project` (scaffold a new repo from an idea), `receive-brief` (validate a brief and cut confirmed slices into specs), `author-brief` (turn a coherent multi-feature outcome into a Draft brief), `capture-work` (compatibility alias for `work-intake`), `workspace-status` (orient at session start), `contract-acquisition` (acquire a platform's real contract before building against it), `operational-safety` (blast-radius and idempotency checklists for the reviewer), `security-checklists` (OWASP-anchored depth modules for the security reviewer).

**Subagents:** `adversarial-reviewer` (spec/plan/implementation drift finder), `finding-adjudicator` (independently sustains or refutes reviewer findings before repair, and stops for your decision when the evidence is insufficient), `quality-engineer` (testability, observability, maintainability lens), `security-reviewer` (OWASP multi-framework threat model), `implementer` (single-task executor for supervisor mode).

**Hooks:** `pre-pr` (pre-commit gate runner), `session-start` (orient on wakeup), `work-loop-check` (iteration-cap enforcement).

**Seeds:** `AGENTS.md`, `CLAUDE.md`, `CHARTER.md`, `CONVENTIONS.md`, `docs/architecture/`, `docs/knowledge/`, `docs/product/` (including the minimal-intent template), `docs/specs/`, `workspace.toml` — the full repo scaffold installed on first install.

See the README for the complete manifest table.

## What it is not

- Not a project management tool — it doesn't track epics, assign tickets, or report velocity.
- Not a runtime framework — it installs no production code into your application.
- Not a code generator — it structures the process of writing code, not the code itself.

## How it relates to other packs

Core is the foundation every other pack builds on. `governance-extras` and `catalogue-curation` list core as a required dependency. `atlassian`, `architect`, `desk-research`, and `experience-design` are complementary user-scope packs that work alongside core without depending on it.
