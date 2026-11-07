---
title: Your first workspace session
summary: Ask what is ready, read the answer, remember a follow-on with work-intake, and see what the next session starts from.
pack: core
kind: tutorial
---

# Your first workspace session

In this tutorial you build a small example repository, ask your agent what is ready to work on, remember a follow-on as its own file, and see how the answer changes after a spec ships. A spec is a short document that says what done means. You need a git repository with [the `core` pack installed](../how-to/start-a-project.md) and a fresh agent session open in it. The outputs below come from a real run.[^run]

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

The agent runs `dispatch.py` from the `work-loop` skill, `<skill-dir>/scripts/dispatch.py --root . --captured`, where `<skill-dir>` is the installed skill folder, such as `.claude/skills/work-loop` for Claude Code. The script reads each spec's `Status:` and `Depends on:` headers, writes nothing, and prints one JSON object that your agent turns into plain words. The part that matters most is the decision:

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

`ready` lists `capture-work-v2` and `workspace-core`. `blocked` lists `status-phase2` with an `unsatisfied_dependency` on `workspace-core`, because it declares `Depends on: spec:workspace-core`. Under `captured`, `auth-strategy` routes to `frame-situation`, a skill in the `product-engineering` pack that sorts out a signal before anyone shapes work, and `infra-cost-monitoring` is a signal with no action.

## Choose a spec

With two ready specs the decision is `ask`: dispatch lists the candidates and never picks one for you. Answer it:

```text
Start workspace-core.
```

## Build the spec

This tutorial does not run the loop. The example specs are stubs with nothing to build, and the real run covered only the dispatch and intake steps. With your own approved spec, skim its Outcome and acceptance criteria, then start the loop:

```text
use the work-loop skill to implement docs/specs/<slug>/
```

The loop plans, builds task by task, runs your checks, and sends the diff to independent reviewers. [Run the build loop](../how-to/start-the-work.md) covers what it does and where it stops for you.

## Remember a follow-on

While the loop runs, review may find an improvement the current spec does not need. Capture it without stopping the loop:

```text
work-intake: remember the configurable retry backoff follow-on from docs/specs/workspace-core; stop without implementation
```

In the real run, the agent wrote one file, `docs/product/captured/configurable-retry-backoff.md`, as a captured item of kind `design`, and changed nothing else. Ask what is ready again, because `dispatch.py` validates every captured item. It rejected the new file:

```json
{
  "code": "invalid_captured_item",
  "path": "docs/product/captured/configurable-retry-backoff.md",
  "dispatchable": false,
  "next_action": "Fix the named field of that captured-item file, then run `dispatch.py` again.",
  "field": "Status"
}
```

The skill's current contract describes the header as bare `Status: Open` and `Kind: design` lines, and the script accepts only the bullet form the other captured items use, `- **Status:** Open` and `- **Kind:** design`. Rewrite the two lines that way and run it again; the item lists as valid, with kind `design`.

## See the state after the spec ships

When `workspace-core` ships, its `Status:` is `Shipped` and its plan `Done`. In the example, set those two lines by hand and ask what is ready again. The real answer: `ready` holds `capture-work-v2` and `status-phase2`, `blocked` is empty, and the decision is `ask` again. The follow-on stays a file until someone picks it up.

Shipping is not closeout. [Close work without losing lasting context](../how-to/close-and-disposition-work.md) previews what the spec and plan still hold that no other document does.

Next, [orient faster at the start of every session](../how-to/orient-at-session-start.md).

[^run]: Run on 2026-11-07 in a scratch repository with `core` 4.0.21 installed by `agentbundle install --pack core --adapter claude-code`. Each `dispatch.py` output was captured from the installed script, in the order shown. The follow-on was a headless `claude -p` session using the installed `work-intake` skill with the prompt shown; its wording and the item's `Kind` can differ between runs. The build loop was not run.
