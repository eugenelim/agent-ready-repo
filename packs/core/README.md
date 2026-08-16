# core

Route work into the right durable artifact, then carry approved specs through a
supervised build loop.

---

## Start here

Start with an ordinary request. You do not need to know which artifact or skill
owns it.

```text
Start work on adding export retention controls for workspace owners.
```

`work-intake` classifies the request from its content. It creates the canonical
artifact, registers it in `workspace.toml`, and invokes a processor only after
both writes succeed. Ambiguous or deferred work stays Draft and cannot dispatch.

```text
  action      start
  artifact    docs/specs/export-retention/spec.md
  membership  awaiting approval
  processor   new-spec
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
| `work-intake` | Start work, remember it for later, inspect status, or request a requirements refresh |
| `workspace-status` | Orient — what's ready, blocked, and done |
| `work-loop` | Plan → execute → gates → adversarial review → merge |
| `bug-fix` | Diagnose and fix a specific bug |
| `new-spec` | Author a spec directly, without the brief layer |
| `capture-work` | Compatibility alias for `work-intake`; new guidance should not use it |
| `project-knowledge` | Capture, distill, or enquire over reviewed project lessons |

---

## How a session runs

```text
work-intake [describe the outcome or change]

  artifact    docs/product/briefs/data-export.md
  membership  draft · non-dispatchable
  processor   author-brief
```

```text
receive-brief docs/product/briefs/data-export.md

  brief  Ready
  slice  streaming-csv-export

new-spec streaming-csv-export

  spec  docs/specs/data-export/spec.md
  plan  docs/specs/data-export/plan.md
```

```text
work-loop docs/specs/data-export/spec.md

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

- **How it works:** [DESIGN.md](DESIGN.md) — philosophy, architecture, and decision log.
- **Go deeper:** the `core` guides in `guides/core/`.
- **Route a request:** [start or remember work](../../guides/core/how-to/start-or-remember-work.md).
- **Headless / harness dispatch:** [run a headless session](../../guides/core/how-to/run-headless-session.md) — drive sessions from a control harness without a human in the loop.
