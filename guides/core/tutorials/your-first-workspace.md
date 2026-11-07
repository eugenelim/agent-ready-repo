---
title: Your first workspace session
summary: Ask what is ready, read the answer, remember a follow-on with work-intake, and see what the next session starts from.
pack: core
kind: tutorial
---

# Your first workspace session

In this tutorial you build a small example repository, ask your agent what is ready to work on, remember a follow-on as its own file, and see how the answer changes after a spec ships. You need a git repository with [the `core` pack installed](../how-to/start-a-project.md) and a fresh agent session open in it. The outputs below come from a real run.[^run]

## Create the example repository

Run this once in the repository root. It writes three approved specs, one of which waits on another, and two captured items, which are notes about work that is not a spec yet:

```bash
mkdir -p docs/specs/workspace-core docs/specs/capture-work-v2 docs/specs/status-phase2 docs/product/captured
for s in workspace-core capture-work-v2; do printf '# Spec: %s\n\n- **Status:** Approved\n- **Brief:** none\n' "$s" > "docs/specs/$s/spec.md"; done
printf '# Spec: status-phase2\n\n- **Status:** Approved\n- **Brief:** none\n- **Depends on:** spec:workspace-core\n' > docs/specs/status-phase2/spec.md
for s in workspace-core capture-work-v2 status-phase2; do printf '# Plan\n\n- **Status:** Approved\n' > "docs/specs/$s/plan.md"; done
printf '# Captured: auth strategy\n\n- **Status:** Open\n- **Kind:** research\n- **Type:** strategy\n' > docs/product/captured/auth-strategy.md
printf '# Captured: infra cost monitoring\n\n- **Status:** Open\n- **Kind:** research\n- **Type:** signal\n' > docs/product/captured/infra-cost-monitoring.md
```

The specs are stubs that hold only the header lines the script below reads.

## Ask what is ready

Start every session with this question:

```text
What is ready to work on in this repo?
```

The agent runs `dispatch.py` from the `work-loop` skill, `<skill-dir>/scripts/dispatch.py --root . --captured`, where `<skill-dir>` is the installed skill folder, such as `.claude/skills/work-loop` for Claude Code. The script reads each spec's `Status:` and `Depends on:` headers and writes nothing. It prints one JSON object, and your agent turns it into plain words. The part that matters most is the decision:

```json
"decision": {
  "action": "ask",
  "path": null,
  "candidates": [
    "docs/specs/capture-work-v2/spec.md",
    "docs/specs/workspace-core/spec.md"
  ],
  "findings": []
}
```

`ready` lists `capture-work-v2` and `workspace-core`. `blocked` lists `status-phase2` with an `unsatisfied_dependency` on `workspace-core`, because it declares `Depends on: spec:workspace-core`. Under `captured`, `auth-strategy` routes to `frame-situation`, the skill that frames a strategy question, and `infra-cost-monitoring` is a signal with no action. With two ready specs the decision is `ask`: dispatch lists the candidates and never picks one for you. Answer it:

```text
Start workspace-core.
```

## Build the spec

The example specs are stubs with nothing to build, so this is where you switch to a real approved spec. A real spec has Outcome, What Changes, Agent Rules, Testing Strategy, and Acceptance Criteria sections; skim the Outcome and the acceptance criteria, and confirm the status is not `Shipped`. Then start the loop:

```text
use the work-loop skill to implement docs/specs/workspace-core/
```

The loop plans, builds task by task, runs your checks, and sends the diff to an independent reviewer. [Run the build loop](../how-to/start-the-work.md) covers what it does and where it stops for you.

## Remember a follow-on

While the loop runs, review may find an improvement that the current spec does not need. Capture it without stopping the loop:

```text
work-intake: remember the configurable retry backoff follow-on from docs/specs/workspace-core; stop without implementation
```

In the real run, the agent wrote one file, `docs/product/captured/configurable-retry-backoff.md`, as a captured item of kind `design`, and changed nothing else. Check it by asking what is ready again. `dispatch.py` validates every captured item, and the real run produced this finding for the new file:

```json
{
  "code": "invalid_captured_item",
  "path": "docs/product/captured/configurable-retry-backoff.md",
  "dispatchable": false,
  "next_action": "Fix the named field of that captured-item file, then run `dispatch.py` again.",
  "field": "Status"
}
```

The agent had written the header lines as `Status: Open` and `Kind: design`. The other captured items use the bullet form, `- **Status:** Open` and `- **Kind:** design`. Rewrite the two lines that way, and the item lists as valid, with kind `design`.

## See the state after the spec ships

When `workspace-core` ships, its `Status:` becomes `Shipped` and its plan `Done`. In the example, set those two lines by hand and ask what is ready again. The real answer: `ready` now lists `capture-work-v2` and `status-phase2`, `blocked` is empty, and the decision is again `ask`. The follow-on stays a file until someone picks it up.

Shipping is not closeout. [Close work without losing lasting context](../how-to/close-and-disposition-work.md) previews what the spec and plan still hold that no other document does.

Next, [orient faster at the start of every session](../how-to/orient-at-session-start.md).

[^run]: Run on 2026-11-07 in a scratch repository with the `core` pack installed by `agentbundle install --pack core --adapter claude-code`. The `dispatch.py` outputs were captured from the installed script. The follow-on was a headless `claude -p` session using the installed `work-intake` skill with the prompt shown. Agent wording and the item's `Kind` can differ between runs.
