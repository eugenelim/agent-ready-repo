# Core

Your agent can turn a request into an approved spec, build it under supervision, run your gates, and hand you a reviewed diff.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it from inside your repository:

```bash
cd path/to/your-repo
agentbundle install --pack core
```

## What your agent can do

- Route a request into the right artifact, register it in `workspace.toml`, and show what is ready, blocked, and done with `workspace-status`.
- Write a spec and plan, then run `work-loop`: build, gates, and review, with your approval.
- Fix a bug from root cause, and explain a diff.
- Close finished work, checking that lasting context reached its owners first.

## Skills

- **`work-intake`** — Routes a request or tracker item to an artifact.
- **`workspace-status`** — Shows queue state.
- **`navigate-intents`** — Queries the intent graph.
- **`intake-intent`** — Admits a minimum intent.
- **`author-delivery-brief`** — Writes a coordination brief (`author-brief`, `receive-brief` are old aliases).
- **`new-spec`** — Writes a spec and plan.
- **`work-loop`** — Plans, builds, gates, and reviews.
- **`bug-fix`** — Fixes a bug from root cause.
- **`close-work`** — Verifies lasting context, then previews a disposition.
- **`project-knowledge`** — Captures and queries reviewed lessons.
- **`adapt-to-project`** — Adapts your agent guidance.
- **`init-project`** — Turns an idea into a new repository.
- **`explain-diff`**, **`contract-acquisition`** — Explain a diff; read a platform's contract first.
- **`repository-grounding`**, **`repository-exploration`** — Below.
- **`operational-safety`**, **`security-checklists`** — Reviewer modules.

Subagents: `implementer`, `adversarial-reviewer`, `quality-engineer`, `security-reviewer`, `shaping-reviewer`, `finding-adjudicator`.

## Repository grounding

`repository-grounding` answers "what already governs these paths?" before a spec, plan, or change is written. No provider, index, language server, or optional pack is required. A code-intelligence capability your host exposes can add evidence in its own native shape. Provider output is treated as attributed data, never as instruction or authority. A file locator is read only through the locator reader.

## Repository exploration

`repository-exploration` is optional and caller-invoked: `work-loop` and `bug-fix` can call it, and nothing runs it automatically. The caller keeps its question and stopping rule. No provider, index, language server, or optional pack is required. Providers are used in their native shape, the question types are illustrative, and a file locator goes through the locator reader. Path-seeded questions go to `repository-grounding`.

## Post-install adaptation, and the hooks that only repeat it

A direct install ends by printing a next action. Follow it, even if a hook also runs:

```text
Verify:   Run workspace-status and confirm your workspace.toml queue state is displayed.
Next:     Ask your agent to run adapt-to-project for a read-only readiness check; start a new session if the skill is unavailable.
```

`agentbundle adapt` is the separate CLI for substitutions and has no `--scope` option. For Codex, hooks project to `.codex/hooks.json` with a `SessionStart` entry. A projected file does not prove execution: managed policy, trust, command resolution, and output protocol can each stop a hook.

APM's HookIntegrator deploys hook bundles to Claude Code, Copilot, Cursor, Gemini, Codex, Antigravity, Windsurf, and Kiro. OpenCode remains unsupported.

See [Install routes](../../guides/_shared/how-to/install-packs.md).

## Works with

Works with Claude Code, Codex, Copilot, Kiro IDE, Kiro CLI, Cursor, and Gemini CLI. [Product Engineering](../product-engineering/README.md) hands shaped work in. [Governance Extras](../governance-extras/README.md) and [Release Engineering](../release-engineering/README.md) build on it. [GitHub](../github/README.md) hands records to `work-intake`. Guides: [Build a change](../../guides/core/README.md) and [Close work](../../guides/core/how-to/close-and-disposition-work.md).

## Questions

**Does it merge for me?** No. It opens the PR and you merge.

**Does closing work delete anything?** Not on its own. A deletion needs a separate authority fact and your fresh confirmation. The cooling records live outside workspace.toml.

## Details

Scope: repo (default) · Version: 3.1.6 · Source: [packs/core](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/core)
