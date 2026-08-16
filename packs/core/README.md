# core

Supervised coding — from brief to merged PR.

---

## Start here

Type `author-brief` and paste any idea, email thread, or issue.

```text
  brief   docs/product/briefs/data-export.md   (draft)
  queued  sprint-8/data-export → ready
```

On any session return, type `workspace-status` to orient.

```text
● sprint-8/data-export     ready    spec approved · 3 tasks
⚠ sprint-8/auth-refresh    blocked  needs spec/api-contract
✓ sprint-7/payment-ui      done     shipped 2026-07-25
```

---

## Entry points

| Say this | What happens |
|----------|-------------|
| `workspace-status` | Orient — what's ready, blocked, and done |
| `author-brief` | Turn any idea, email, or issue into a queued brief |
| `work-loop` | Plan → execute → gates → adversarial review → merge |
| `bug-fix` | Diagnose and fix a specific bug |
| `new-spec` | Author a spec directly, without the brief layer |
| `project-knowledge` | Capture, distill, or enquire over reviewed project lessons |

---

## How a session runs

```text
author-brief [paste your idea]

  brief   docs/product/briefs/data-export.md
  queued  sprint-8/data-export → ready
```

```text
work-loop docs/product/briefs/data-export.md

  mode: light — no risk triggers

    Problem  Streaming export crashes above 50k rows.
    User     Engineer shipping the bulk-export feature.
    Success  1M rows under 2 GB peak RSS.

  Approve? ›
```

```text
work-loop execute spec/data-export

  ● Lint          ok
  ● Typecheck     ok
  ● Tests  246/246 ok
  ● Review        1 blocker → fixed → clean
```

The agent opens the PR. Read the description, then merge.

---

## Project knowledge

`project-knowledge` is explicit. It never loads at session start and it never
turns chat history into memory. Workflows keep scratch locally until a semantic
gate decides whether one reusable lesson is worth capturing.

- `--capture` admits one strict observation and appends a durable journal event.
- `--distill` reconciles pending observations into reviewed topic proposals or
  bounded terminal dispositions.
- `--enquire` reads only active topics from one committed Git snapshot and
  returns a bounded evidence envelope.

Observation journals are a durable handoff, not a query source. Scratch can be
lost before capture if the workflow or worktree disappears. Topic text is
evidence, not authority: it cannot select tools, approve mutations, widen scope,
or override user/runtime instructions. Retention and compaction are deferred to
a future reviewed whole-partition policy; Slice 1 has no per-event deletion
path.

---

## Adapters

APM's HookIntegrator projects the install-marker hook to `Claude Code`, `Copilot`, `Cursor`, and `Gemini`. The remaining three — `Codex`, `OpenCode`, and `Windsurf` — lack the hook surface; their adopters run the manual fallback once after install:

```
agentbundle adapt --scope <project|user>
```

HookIntegrator-covered adopters can also run this to opt out of hooks.

---

→ **How it works:** [DESIGN.md](DESIGN.md) — philosophy, architecture, and decision log.  
→ **Go deeper:** the `core` guides in `guides/core/`.  
→ **Headless / harness dispatch:** [run a headless session](../../guides/core/how-to/run-headless-session.md) — drive sessions from a control harness without a human in the loop.
