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

If you can't find the answer in one of these places, **the answer doesn't
exist yet** — ask, or open an RFC. Don't guess. Lifecycle and mechanics
(living vs. frozen, ADR vs. RFC, etc.) live in
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

## Workflow

For anything beyond a one-line edit, follow the **plan → execute → verify →
review** loop. The full mechanics are in the
[`work-loop`](.claude/skills/work-loop/SKILL.md) skill — load it before
non-trivial work. Summary:

1. **Plan before acting.** For anything spec-shaped, read the spec first. For
   architecturally significant work, use Plan Mode and "think hard" /
   "ultrathink". Phrase every plan task as a verifiable goal, not a list of
   steps — the task name should be the success criterion.
2. **Specs are validation gates, not write-once docs.** If implementation
   diverges from the spec, update the spec in the same PR. Drift is a bug.
3. **Verification before code.** Every plan task declares *how* it'll be
   verified before the implementer touches the keyboard. Pick the mode that
   fits the code shape:
   - **TDD** — pure functions, state machines, protocols, anything with a
     compressible invariant. Contract tests in `spec.md`, construction tests
     in `plan.md`, `Tests:` before `Approach:`, red-green-refactor. Default
     for testable logic. Split detailed in
     [`CONVENTIONS.md`](docs/CONVENTIONS.md#contract-tests-vs-construction-tests).
   - **Goal-based check** — build config, scaffolding, generated-code
     consumption, smoke entry points. The task's `Done when:` is the
     contract; verify with a one-liner (build command, `grep`, typecheck)
     instead of a test file. Don't write a test that just asserts what the
     compiler already proves.
   - **Visual / manual QA** — UI rendering, end-to-end UX flows. The task
     records the manual check explicitly. For user-facing flows that are
     part of the spec's contract, the verification artifact — automated
     or manual — should simulate the user's gesture and assert *what the
     user actually sees* (rendered text, visible elements, navigation),
     not internal state (store contents, mock-call counts, context-
     provider values). A test that passes when the on-screen result is
     wrong is mode-mismatched, regardless of which framework wrote it.
     Add automation when the regression cost (UI bugs ship invisibly)
     outweighs the cost (flakiness, framework brittleness); the choice
     of tool is the adopter's.

   Spikes and throwaway exploration are out of scope.
4. **Run mechanical gates** (lint, typecheck, tests) before declaring done.
5. **Self-review against the spec.** After gates pass, run the
   [`adversarial-reviewer`](.claude/agents/adversarial-reviewer.md)
   subagent. Treat its findings as part of "done", not as optional polish.
   See [§ Specialist subagents](#specialist-subagents) for security and
   quality reviewers to layer on when the change calls for them.
6. **Iterate on findings, with a hard cap of five in-session iterations.**
   If you hit it, stop and re-plan — don't grind.
7. **Capture what you learned** before opening the PR — into the right
   `AGENTS.md`, skill, or doc.
8. **Conventional commits.** Format: `<type>(<scope>): <subject>`. See
   [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md#commits).

For unattended/AFK work, the [Ralph harness](tools/RALPH.md) runs the loop
in fresh sessions. Read it first; Ralph fits *some* tasks, not most.

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
- `work-loop` — **start here for any non-trivial change**
- `new-spec` — start a feature in `docs/specs/`
- `bug-fix` — fix a defect with root-cause discipline
- `new-adr` — record a decision in `docs/adr/`
- `new-rfc` — open a proposal in `docs/rfc/`
- `new-package` — scaffold a package in `packages/`
- `update-conventions` — open an RFC to change governance docs

The full index is in [`.claude/skills/README.md`](.claude/skills/README.md).

## Specialist subagents

`.claude/agents/` contains reviewers with sharp, differentiable lenses.
Pick the ones the diff actually warrants; don't run all three by default.

- [`adversarial-reviewer`](.claude/agents/adversarial-reviewer.md) — spec /
  plan / implementation drift; missing edge cases; scope creep. Default
  reviewer; runs after gates pass.
- [`security-reviewer`](.claude/agents/security-reviewer.md) — OWASP Top
  10 (web + LLM Apps) and STRIDE lens. Use when the diff touches auth,
  secrets, user input, deserialization, file/network I/O, dependencies,
  or LLM/agent code. Complements SAST/SCA scanners; does not replace them.
- [`quality-engineer`](.claude/agents/quality-engineer.md) — testability,
  observability, reliability, and maintainability lens. Also drafts
  contract or construction tests on request.

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

Flag drift in your PR — don't silently work around it. AGENTS.md vs. reality
drift is the biggest cause of agent quality decay. Substantive changes to
this file go through RFC; small fixes are normal PRs.

---

*Generated from the [`agent-ready-repo`](https://github.com/) template. See [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) for the full conventions, or [`docs/architecture/overview.md`](docs/architecture/overview.md) to start exploring.*
