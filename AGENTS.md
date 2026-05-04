# AGENTS.md

> **This is the canonical agent context file.** `CLAUDE.md` is a symlink to this file.
> Cursor, Codex, Gemini CLI, and Copilot also read it (via their own discovery rules).
>
> Keep this file under ~200 lines. If you're tempted to add to it, ask first whether
> the content belongs in `docs/`, `.claude/skills/`, or a subdirectory `AGENTS.md`.

## What this repo is

<!-- ONE sentence. Replace this. -->
A monorepo for `<project-name>` — a `<one-line description of what it does and for whom>`.

The detailed map of what lives where is in [`docs/architecture/overview.md`](docs/architecture/overview.md).
**Read it before exploring.** It will save you 20 minutes of grep.

## Source of truth

For each kind of decision, there is exactly one place it lives:

| Question                                  | Where it lives                       |
| ----------------------------------------- | ------------------------------------ |
| What is this project, and what's in/out of scope? | `docs/CHARTER.md`             |
| Why did we choose X over Y?               | `docs/adr/`     (Architecture Decision Records) |
| What should we change, and how?           | `docs/rfc/`     (Request For Comments) |
| What exactly does this feature do?        | `docs/specs/<feature>/spec.md`       |
| How will we build it, step by step?       | `docs/specs/<feature>/plan.md`       |
| How is the code organized today?          | `docs/architecture/`                 |
| What is the product doing today?          | `docs/product/` (roadmap, changelog) |
| How do users use the product?             | `docs/guides/` (Diátaxis: tutorials, how-to, reference, explanation) |
| How do agents do `<repeating task>`?      | `.claude/skills/<task>/SKILL.md`     |

If you can't find the answer in one of these places, **the answer doesn't exist yet** —
don't guess. Ask, or open an RFC.

The lifecycle and mechanics of these docs (which are *living* vs. *frozen*,
how to write a spec, when to open an ADR vs. an RFC, etc.) are in
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

## Workflow

For anything beyond a one-line edit, follow the **plan → execute → verify →
review** loop. The full mechanics are in the
[`work-loop`](.claude/skills/work-loop/SKILL.md) skill — load it before
non-trivial work. Summary:

1. **Plan before acting.** For anything spec-shaped, read the spec first. For
   architecturally significant work, use Plan Mode and "think hard" /
   "ultrathink" — Opus 4.7's adaptive thinking earns its keep on the hard 20%
   of tasks.
2. **Specs are validation gates, not write-once docs.** If implementation
   diverges from the spec, update the spec in the same PR. Drift is a bug.
3. **Run mechanical gates** (lint, typecheck, tests) before declaring done.
   Self-assessment is unreliable; gates are objective.
4. **Self-review against the spec.** After gates pass, run the
   [`spec-reviewer`](.claude/agents/spec-reviewer.md) subagent. Treat its
   findings as part of "done", not as optional polish.
5. **Iterate on findings, with a hard cap.** Five in-session iterations is
   the default. If you hit it, the task is bigger than you thought — stop
   and re-plan, don't grind.
6. **Capture what you learned** before opening the PR — into the right
   `AGENTS.md`, skill, or doc. The loop should make the *project* smarter,
   not just this PR.
7. **Conventional commits.** Format: `<type>(<scope>): <subject>`. See
   [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md#commits).

For unattended/AFK work — overnight runs, large mechanical task lists — the
[Ralph harness](tools/RALPH.md) at `tools/ralph.sh` runs the loop with each
iteration as a fresh session. Read `tools/RALPH.md` first; Ralph is the
right tool for *some* tasks, not most.

## Commands you'll need

<!-- Keep this short. Detailed command reference goes in docs/. -->

```bash
<install command>           # one-time setup
<test command>              # run tests for the package you're in
<test all command>          # run all tests (slow — usually CI's job)
<lint command>              # lint + format check
<build command>             # produce build artifacts
```

## Code style

We don't list style rules here — the linter does that job better than prose can.
Run `<lint command>` and follow what it tells you. If something is genuinely
ambiguous to a linter (naming, file organization, error handling philosophy),
it's covered in [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

## Skills available to you

`.claude/skills/` contains workflows that have been used enough to deserve a name.
Use them when relevant — they encode constraints you would otherwise re-derive:

<!-- Keep this list short. The full skill index is .claude/skills/README.md -->
- `work-loop` — the standard plan/execute/verify/fix loop for non-trivial work; **start here for any feature, fix, or refactor**
- `new-spec` — open a spec in `docs/specs/` from the template, with the right links
- `new-adr` — open an ADR with a fresh number and the template
- `new-rfc` — open an RFC and link it from the index
- `new-package` — scaffold a new package in `packages/` with the right defaults
- `update-conventions` — open an RFC to change governance docs

The full index is in [`.claude/skills/README.md`](.claude/skills/README.md).

## Things you should not do without asking

- **Don't run destructive commands** (`rm -rf`, `git push --force`, dropping
  database tables) without explicit confirmation in the same turn.
- **Don't edit `docs/CHARTER.md` directly** — substantive changes go through
  an RFC. Trivial edits (typos, broken links) are fine as a normal PR.
- **Don't add dependencies in package code** without recording the why in the
  package's `AGENTS.md` or an ADR. Dependencies are forever.
- **Don't fabricate APIs.** If you're not sure a function exists, grep first.
  Inventing imports that "look right" wastes everyone's time when the build fails.
- **Don't create new top-level directories.** The structure is intentional. If you
  think a new one is needed, propose it in an RFC.

## When this file is wrong

If you (an agent or a human) notice this file is outdated or contradicts the code,
**flag it in your PR**. Don't silently work around it. Drift between AGENTS.md and
reality is the single biggest reason agent quality degrades over time.

To propose a change to this file itself, edit it in a PR like any other file.
Substantive changes (new sections, removed sections) go through RFC review.

---

*Generated from the [`agent-ready-repo`](https://github.com/) template. See [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) for the full conventions, or [`docs/architecture/overview.md`](docs/architecture/overview.md) to start exploring.*
