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
> accelerants, when to automate, and the exploratory flavor. It also holds the
> doctrine for verify entries: saved recipes for driving a surface.

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

## Verify entries

A verify entry is a saved, repository-owned recipe for launching and driving
one surface so a run can prove a change by using it. The template is
`assets/verify-entry.md`.

### When an entry is needed

- At PLAN, a task whose verification mode is visual / manual QA, behavior pin,
  or measurement looks for a verify entry for each surface the task changes or
  must drive to prove its outcome.
- When no entry exists for such a surface, creating it is the task's first step.
- A surface the change neither touches nor must drive is recorded as uncovered.
  Do not map, draft, or fix it.

### Where entries live

Look in this order before creating a file:

1. A verify file an `AGENT_RULES.md` row already routes to.
2. `CONTRIBUTING.md` in `.github/`, the root, or `docs/`, and the guides it
   links to.
3. Developer guides: `DEVELOPMENT.md`, `docs/DEVELOPMENT.md`,
   `docs/development/`, `contribute/`, `BUILD.md`, `BUILDING.md`, `TESTING.md`,
   `HACKING.md`, and `VERIFICATION.md`.
4. README sections on running or building locally.
5. Agent instruction files and host skills: `AGENTS.md`,
   `.github/copilot-instructions.md`, `GEMINI.md`, and `.claude/skills/verify/`.

A file covers the surface when it already states how to launch or drive it. A
human-facing file is any place in the list above other than agent instruction
files and host skills.

- Read agent instruction files and host skills for commands to map into an
  entry. They are mapped, never hosted: an entry is never written into one.
- When an existing human-facing file covers the surface, offer to add the entry
  there. The offer names the file and the fields to add.
- Create `docs/VERIFICATION.md` only when no human-facing file covers the
  surface or the adopter declines.
- An unanswered or ambiguous offer writes nothing.
- While an offer is unanswered, the surface's grade is `blocked`. The run names
  the pending offer and records no receipt, because no command ran. The task
  does not claim its mode.
- Write an accepted entry under a `## Verify: <surface>` heading.
- After writing an entry in a file no `AGENT_RULES.md` row routes to, add one
  row under the same adopter acceptance as the entry. Its `read` cell is that
  file's repository-relative path. Its `when` is limited to verifying the
  surfaces that file covers.
- The verify file never mentions `AGENT_RULES.md`, so routing stays one hop.
- `RUNBOOK.md` and `docs/runbooks/` are not extended with launch steps.

### Building an entry

- An entry for a surface with existing tooling points at that tooling. It
  records only what the tooling lacks: the exact invocation, the ready signal,
  which output is the evidence, and cleanup.
- Draft new commands from the repository's manifests, scripts, CI, and docs
  only where no tooling covers the surface.

### Proving an entry

- An entry is a draft until it has run once from start to finish.
- It also needs one recorded failing run. That run's `mutation-proof.md`
  record names the entry's evidence check as its catching test and one
  deliberate break of the driven subject as its exact mutation. The break
  stands in for that reference's revert to the pre-fix implementation.
- The failing proof run reports no grade and no receipt.
- The task does not claim its mode before both runs exist.

### Recording and promoting

- Record drive commands in the verification ledger.
- When a second run drives the same surface by hand, move its commands into
  the verify file, a test, or the repository's own tooling.

### Drift

An in-scope entry that fails at run start is one of three things:

- **Doc drift:** the entry or its source doc is stale. Update it.
- **Harness gap:** the tooling lacks something the entry needs. Fix a gap in
  mapped tooling in that tooling.
- **Product bug:** the product is wrong. Report it. Never write it into the
  entry as expected behavior.

A run stopped at run start reports `blocked` for doc drift or a harness gap and
`failed` for a product bug.

### Fields

An entry holds these twelve fields, in this order:

- **Surface:** the one surface the entry drives.
- **Launch:** the exact command that starts it.
- **Ready:** the signal that it is usable.
- **Doctor:** one read-only check that the setup is sound.
- **Isolation:** how the run keeps its instance, state, and files apart.
- **Drive:** the ordered steps that exercise the surface.
- **Features:** the features the drive covers.
- **Evidence:** which output proves the result, and where it is kept.
- **Proof limits:** what the evidence does not prove.
- **Cleanup:** how the run removes what it started.
- **Helpers:** scripts or tooling the entry relies on.
- **Stand-in gap:** where a stand-in replaces the real thing, and what stays
  uncovered.

### Rules

- Ready means usable, not that the process answers.
- Never drive an instance this run did not start.
- Drive by stable handles such as roles, labels, and prompt strings, never
  coordinates.
- Evidence survives cleanup, and the run checks that it did.
- Test-only endpoints and internal setters are not proof.
- A dry-run is checked by observing what it skips.
- Cleanup stops or removes only processes, containers, and directories this run
  started or created. It finds them by the handle the run recorded, never by
  process name or pattern.

### Grades

Each run other than the failing proof run reports exactly one of five grades:

- `live-verified`: the real surface ran and showed the result.
- `test-verified`: a targeted test showed the result.
- `build-only`: the surface built, and nothing more ran.
- `blocked`: the run could not complete a needed step.
- `failed`: the run ran and the result was wrong.

A grade its recorded commands and output do not support is reported as
`blocked`. Which criterion a run proves comes from the task and the
criterion's approved evidence policy, never from the verify entry.

### Receipt mapping

| Grade | observation.type | outcome |
| --- | --- | --- |
| `live-verified` | `command-result` | `live-verified` |
| `build-only` | `command-result` | `build-only` |
| `blocked` | `command-result` | `blocked` |
| `failed` | `command-result` | `failed` |
| `test-verified` | `test-result` | `test-verified` |
| `failed` | `test-result` | `failed` |

A `blocked` receipt records the command that could not complete, such as a
failed doctor or launch.

- `schema_version` is `1`.
- `receipt_id` is `verify:<surface>:<run-id>`.
- `freshness_mode` is `exact-subject`.
- The producer is `{"class": "verify-entry", "identity": "verify:<surface>"}`.

`acceptance_fingerprint` is the supervised run's current fingerprint, or
`git:<commit>` of the tree driven when no supervisor runs. A receipt with the
latter is audit-only. The criterion reference and selector term come from the
task.

### Placeholders and trust

- Keep raw transcripts in an evidence directory version control ignores.
- Recorded commands, and any output copied into the verification ledger or
  another committed record, use placeholders such as `<checkout>`, `<scratch>`,
  and `<evidence-dir>` for paths, hostnames, and usernames.
- Never include a credential value. Name a credential only by its environment
  variable.
- A verify entry is agent guidance. Editing it changes a tool surface.
- Its commands run only under the host's permission mode.
- An entry never widens network, credential, or write scope beyond what the
  task's verification needs.

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
