# verification-modes — doctrine for the modes that need more than SKILL.md

> **Loaded when:** a plan task picks a verification mode whose doctrine runs
> longer than `work-loop` SKILL.md can carry: **visual / manual QA** (UI
> rendering, an end-to-end UX flow, or any artifact a user invokes directly: a
> CLI, a library's public API, an agent or skill, a service endpoint),
> **behavior pin**, or **measurement**. `work-loop` PLAN step 7 owns the mode
> list; infra/deploy has its own depth in
> [`infra-verification.md`](infra-verification.md).
> **What this is:** the progressive-disclosure depth behind those modes.
> `SKILL.md` keeps the load-bearing one-liner for each; the full doctrine lives
> here. For visual / manual QA that means the per-surface shapes, the
> accelerants, when to automate, and the exploratory flavor.

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

## Behavior pin

Use this mode for a behavior-preserving restructure: a refactor, move, rename,
or dedupe. The claim is "nothing observable changed", so the proof is a check
of current behavior, not a new feature test.

- Write the pin first and run it on the base commit. The pin passes on the
  base commit before any structure moves; a pin that has never passed there
  proves nothing.
- Pin observable behavior at the boundary a caller sees: outputs, exit codes,
  rendered text, public return values. Do not pin internals the restructure is
  meant to change.
- The pin stays green after each step, not only at the end. A step that turns
  it red is reverted or fixed before the next step starts.
- Lint and typecheck are not a pin. They prove the code parses and types
  agree, not that behavior held.
- A restructure that names no branch, layer, or invalid state it removed is
  reverted. Moving code without removing something is churn.
- The pin writes no red test: it passes by design at the base commit, so
  there is no red to earn.

## Measurement

Use this mode when the claim is a number: latency, throughput, size, or
runtime. A number from one run is an anecdote, so the doctrine is about making
the number trustworthy.

- The baseline comes from the base commit, with the same command, data, and
  environment as the after run. Change one thing between the two sides.
- Each side runs at least 5 times, alternating baseline and after so drift
  hits both sides alike.
- The report gives the median, the range, and the run count for each side.
- A difference inside the run-to-run range is reported as no measurable
  difference. Do not claim a win the noise can produce.
- The run records its error count and a count of the work done (requests
  served, items processed). A faster run that did less work or failed more
  often is not faster.
- Report one vetted number per claim, with the command that produced it.
- The measurement writes no red test: there is no red to earn.
