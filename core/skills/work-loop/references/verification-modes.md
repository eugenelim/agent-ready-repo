# verification-modes — the visual / manual-QA mode (full doctrine)

> **Loaded when:** a plan task picks the **visual / manual-QA** verification
> mode — UI rendering, an end-to-end UX flow, or any other artifact a user
> invokes directly (a CLI, a library's public API, an agent or skill, a service
> endpoint). The other three modes (TDD, goal-based, infra/deploy) don't need
> this; infra/deploy has its own depth in
> [`infra-verification.md`](infra-verification.md).
> **What this is:** the progressive-disclosure depth behind `work-loop`'s
> visual / manual-QA verification mode. `SKILL.md` keeps the load-bearing
> contract one-liner (exercise the real built artifact end-to-end through its
> documented happy path and record what you observed, asserting on that result
> and never on a passing unit gate); the full doctrine — the per-surface shapes,
> the accelerants, when to automate, and the exploratory flavor — lives here.

## Exercise the real artifact, assert on the observed result

When a change ships something a user invokes, verification **includes exercising
the real built artifact end-to-end the way a user would — through the documented
happy path — and recording what you observed**: the actual stdout and exit code,
the returned value, the file written, the on-screen result. **Assert on that
observed result, not on internal state** (store contents, mock-call counts,
context-provider values), and **don't let a passing unit gate stand in for the
real invocation**. A test or check that passes while the artifact, run as
documented, produces the wrong result is **mode-mismatched**, regardless of
which framework wrote it.

## What "what you observed" means per surface

The observed result is read at the surface the *user* uses, never a private
internal:

- **UI flows** — *what the user actually sees*: rendered text, visible elements,
  navigation.
- **CLI** — the command's real output and exit status.
- **Library** — the public call's result and effects **through its documented
  entry point**, not a private internal.

## Harness-agnostic, with optional accelerants

This is **harness-agnostic doctrine** — exercise the artifact by hand on any
agent. In Claude Code the native `/verify` and `/run` commands perform it, an
**optional accelerant and never a dependency**, so adapters without them lose
only the shortcut, not the step.

## When to automate

Add automation when the **regression cost** (a broken invocation ships
invisibly) outweighs the cost (flakiness, brittleness); the choice of tool is
the adopter's.

## QA session isolation safety

Manual-QA verification fails reproducibly when the session itself is not isolated. Before running, check three things:

- **Process isolation.** QA must run against the actual implementation tree — including uncommitted edits — not a checkout of HEAD. What requires isolation is the *process environment*: keep the CWD that the artifact's documented usage requires (when the artifact discovers config from CWD, preserve it); isolate environment variables, temporary state, and in-flight staged files so partial installs or open file handles in the editing context do not leak into the QA result. A separate git branch would lose the very changes under test.
- **Fixture completeness.** Synthetic fixtures must include every file the code under test reads. A fixture that works locally because it falls back to files in the real repo produces false-pass results in CI (where the repo may be absent) and false-fail results in isolated worktrees (where sibling files are absent). Name each file the code reads; add it to the fixture or document the dependency explicitly.
- **Artifact-copy direction.** When copying artifacts for testing, verify the copy direction and the working directory before executing `cp`, `rsync`, or equivalent. Source and destination look symmetric; the wrong direction silently overwrites the artifact under test.
- **Session scope boundary.** Declare explicitly where the session ends and what is documented-but-not-exercised. A QA note that describes full end-to-end behavior without a declared stop point causes reviewers to flag every out-of-scope behavior as untested — each round costs an iteration. A one-line "this session verifies X; Y and Z are deferred" prevents multiple rounds of scope clarification.

## Exploratory / visual fuzz (a third flavor)

A third flavor — *exploratory / visual fuzz* — drives the UI with varied or
random input and asserts **invariants** ("didn't crash, didn't render garbage,
layout holds, no overflow") rather than specific outputs. Reach for it when the
failure mode is open-ended and you can't enumerate the gestures up front.
