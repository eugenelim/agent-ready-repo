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

For a registered tracker-origin artifact, ask for a refresh rather than a new
intake:

```text
Refresh docs/specs/export-retention/spec.md from its registered source.
Show the field delta and do not write back yet.
```

`work-intake` resolves the exact profile processor and preserves the artifact's
authority record. Local requirement changes need authorized field decisions.
Each optional tracker coordination mutation then needs its own fresh exact
confirmation and pending receipt.

---

## Entry points

| Say this | What happens |
|----------|-------------|
| `work-intake` | Start work, remember it for later, inspect status, or request a requirements refresh |
| `workspace-status` | Orient — what's ready, blocked, and done |
| `work-loop` | Plan → execute → gates → bounded evidence-assisted review → merge |
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

  mode: spec-driven light — no risk triggers

    Problem  Streaming export crashes above 50k rows.
    User     Engineer shipping the bulk-export feature.
    Success  1M rows under 2 GB peak RSS.

  Approve? ›
```

This is a spec-driven light run, so its existing durable spec and plan remain
governing. An eligible explicit direct-light request instead starts `work-loop`
from the current request and keeps its plan in the active session.

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

Authoring gates are producer-owned. `author-brief` and `new-spec` stop at Draft
without a knowledge call. `receive-brief` may capture reusable supporting
practice only after `brief-ready`; `work-loop` does the same after
`spec-approved` and `plan-locked`. Normative brief/spec/plan content stays in
those artifacts. Missing project knowledge emits a named skip and never creates
fallback storage; any terminal distillation uses only receipts returned by that
same gate.

At review planning, `work-loop` may separately declare one consequential
`CQ-REVIEW` enquiry after the target and structural scope are fixed. The same
delimited envelope supplies candidate checks to warranted adversarial,
security, and quality reviewers. Reviewers never write project knowledge, and
every finding remains independently grounded in the current target, governing
review standard, and current canonical sources. An unavailable provider is a
named skip with no fallback file.

---

## Post-install adaptation, and the hooks that only repeat it

A successful direct core install at repository or local scope ends by printing a
verification step and a next action. Follow them, even if a hook also runs — you
do not need the hook and should not wait for it:

```text
Verify:   Run workspace-status and confirm your workspace.toml queue state is displayed.
Next:     Ask your agent to run adapt-to-project for a read-only readiness check; start a new session if the skill is unavailable.
```

`adapt-to-project` is the agent-led workflow for readiness, inferred project
conventions, companion merges, and approved adaptation. `agentbundle adapt` is
the separate deterministic CLI for substitutions and companion bookkeeping; it
has no `--scope` option.

If the skill is not loaded yet, start a fresh agent session first.

Direct `agentbundle` adapters project portable hook wiring into each runtime's
native files; for Codex that means repository `.codex/hooks.json` and a
`SessionStart` entry. A projected file does not prove execution: the active
runtime, managed policy, repository and hook trust, command resolution, output
protocol, and adaptation marker can each affect whether a nudge appears.

APM's HookIntegrator currently deploys hook bundles to Claude Code, Copilot,
Cursor, Gemini, Codex, Antigravity, Windsurf, and Kiro. OpenCode remains
unsupported. See [Install routes](../../guides/_shared/explanation/install-routes.md)
for the route and scope differences.

---

- **How it works:** [DESIGN.md](DESIGN.md) — philosophy, architecture, and decision log.
- **Go deeper:** the `core` guides in `guides/core/`.
- **Route a request:** [start or remember work](../../guides/core/how-to/start-or-remember-work.md).
- **Refresh tracked work:** [review local changes and confirm write-back](../../guides/_shared/how-to/use-work-intake.md).
- **Migrate legacy workspace entries:** [plan, apply, recover, and roll back one reviewed entry](../../guides/core/how-to/migrate-capture-work.md).
- **Headless / harness dispatch:** [run a headless session](../../guides/core/how-to/run-headless-session.md) — drive sessions from a control harness without a human in the loop.
- **Headless / harness dispatch:** [run a headless session with workspace-mcp](../../guides/core/how-to/run-headless-session.md) — drive sessions from a control harness without a human in the loop.
