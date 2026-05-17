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

## Keeping changes minimal

Scope each change precisely to the request.

- **Limit the diff to what the request requires — extra changes hide
  the real one from review.** If the request needs it — or would ship
  broken without it — it's in scope, even discoveries you make
  mid-implementation.
- **Add a flag or option only when a second caller actually needs to
  differ.** Today's one caller is enough to define the shape.
- **Add docstrings and types to code the change actually touches.**
  Leave nearby untouched code as it is.
- **Validate at boundaries the request crosses** (user input, external
  APIs). Trust internal callers and framework guarantees.
- **Inline a single-use operation.** Extract a helper once a second
  caller actually appears.

When you defer something out of this PR — unrelated find or same-area
cleanup — note it in the PR description with a one-line reason.

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

## How we work

For anything beyond a one-line edit, follow the **plan → execute → verify →
review** loop. The mechanics — verification modes, gate sequence, iteration
cap, capture-learnings, specialist-reviewer pass — live in the
[`work-loop`](.claude/skills/work-loop/SKILL.md) skill. Load it before
non-trivial work; that is the canonical source for *how* the loop runs.
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md#how-we-do-non-trivial-work)
covers the *why*. Commits follow Conventional Commits — format and footer
rules are in [`CONVENTIONS.md § Commits`](docs/CONVENTIONS.md#commits).

Specs are validation gates, not write-once docs. If implementation diverges
from the spec, update the spec in the same PR — drift is a bug.

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

## Check before acting

- **Get user confirmation for destructive commands** (`rm -rf`,
  `git push --force`, dropping database tables) before running them.
- **Route substantive `docs/CHARTER.md` edits through an RFC.** Trivial
  fixes (typos, broken links) are fine as normal PRs.
- **Record new dependencies in the package's `AGENTS.md` or an ADR**
  before adding them. Dependencies are forever.
- **Grep to verify a function exists** before importing it. Imports
  that "look right" but aren't waste the time of everyone who hits the
  broken build.
- **Propose new top-level directories via RFC.** The structure is
  intentional.

## When this file is wrong

Flag drift in your PR — don't silently work around it. AGENTS.md vs. reality
drift is the biggest cause of agent quality decay. Substantive changes to
this file go through RFC; small fixes are normal PRs.

---

*Generated from the [`agent-ready-repo`](https://github.com/) template. See [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) for the full conventions, or [`docs/architecture/overview.md`](docs/architecture/overview.md) to start exploring.*
