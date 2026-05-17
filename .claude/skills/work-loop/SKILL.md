---
name: work-loop
description: Use this skill whenever you're implementing a non-trivial change — a feature, a multi-file bug fix, a refactor, a migration, a framework or dependency upgrade, a schema or API change, performance work, an infrastructure or build-system edit, or anything spec-driven. It enforces the project's plan → execute → self-review → fix loop with mechanical gates (lint, typecheck, tests) and adversarial review. Default to this skill for any task larger than a one-line edit.
dependencies:
  - docs/CONVENTIONS.md#contract-tests-vs-construction-tests
  - docs/CONVENTIONS.md#work-loop-state
  - docs/CONVENTIONS.md#supervisor-mode
  - docs/CONVENTIONS.md#knowledge-base
  - docs/_templates/state.json
  - docs/knowledge/README.md
  - docs/knowledge/patterns.jsonl
  - tools/check-done.py
  - tools/hooks/session-start.sh
  - tools/hooks/pre-pr.sh
  - .claude/agents/adversarial-reviewer.md
  - .claude/agents/security-reviewer.md
  - .claude/agents/quality-engineer.md
  - .claude/agents/implementer.md
  - .claude/skills/new-spec/SKILL.md
  - tools/ralph.sh
  - tools/RALPH.md
---

# Skill: work-loop

This is the project's standard inner loop for non-trivial work. It exists
because LLM self-assessment is unreliable: agents declare victory when they
*feel* done, not when objective gates pass. This skill replaces "feel" with
verifiable termination criteria.

> **Vocabulary.** "Surface" throughout this skill means: stop the
> current loop, emit a short description of the situation in your final
> message (what happened, what you tried, what state things are in),
> and wait for human direction. It is the project's house verb for
> "stop and report." Do not retry, do not redispatch, do not silently
> reset. (Reviewers also "surface" findings in the descriptive sense
> — "raised" — when they return their report; context disambiguates.)

## When this skill applies

- Implementing a spec from `docs/specs/`.
- Bug fixes that touch more than one file — including security patches and incident hot-fixes.
- Refactors.
- Migrations, framework or dependency upgrades, schema or API changes.
- Performance work, or infrastructure / build-system changes beyond a single config tweak.
- Reverting and re-doing a previous change.
- Any task where you'd otherwise be tempted to "just go".

For genuine one-line edits (typo, config tweak), skip the loop — the overhead
isn't worth it.

## The loop

```
   ┌─────────────────────────────────────────────────────────┐
   │                                                         │
   ▼                                                         │
PLAN  ──►  EXECUTE  ──►  GATES  ──►  REVIEW  ──►  DECIDE    │
                          │           │            │         │
                          │           │            └── findings? ──┐
                          │           │                            │
                          └─ failed? ─┴── findings? ────── fix ────┘
                                                              │
                                                              └── back to GATES
```

### 1. PLAN — think before acting

For anything beyond trivial, *think before you write code*. Concretely:

- If the task has a spec, read `spec.md` and `plan.md` first. The plan's task
  list is your work-breakdown — don't invent your own.
- If the task has no spec and is more than a one-file change, **stop and use
  the `new-spec` skill first**. Implementation without a contract drifts.
  Contract tests are part of the spec — write them *during* `new-spec`, not
  later. A spec without its Contract tests section filled in is not finished.
- For architecturally significant work, use extended thinking. In an
  interactive Claude Code session: enter Plan Mode (Shift+Tab twice) and add
  "think hard" or "ultrathink" to your prompt for adaptive thinking depth.
  Other agents have their own facilities — use the equivalent.
- Write down: which files you'll touch, what tests will demonstrate "done",
  and what you are *not* changing. Three sentences is enough for the trio.

  Then, in a short paragraph below the trio, **name what you were tempted
  to add and explicitly declined** — usually one to three items, each with
  a one-sentence reason. *Patterns worth naming* are the structural
  temptations agents drift toward mid-EXECUTE: new abstractions
  (factories, locators, registries), structural choices (new module, new
  layer, new boundary), framework or dependency introductions, defensive
  scaffolding (validation wrappers, error-mapping layers), and
  configurability for hypothetical futures (flags, options, env vars). The
  shape is one line per declination: *"Tempted to add a ServiceLocator;
  declining — direct construction is fine for now."* This is a commitment,
  not a checklist — naming a temptation here means REVIEW can catch drift
  toward it as self-contradiction in the diff. The trio's three-sentence
  cap doesn't bind this paragraph; brevity still does.
- **Pick the verification mode for each plan task** before writing code.
  The mode is the task's contract for "how do we know this is done":
  - **TDD** — pure functions, state machines, protocols, anything with a
    compressible invariant. Contract tests in `spec.md`, construction
    tests in `plan.md`, `Tests:` before `Approach:`, red-green-refactor.
    Default for testable logic. Split detailed in
    [`CONVENTIONS.md`](../../../docs/CONVENTIONS.md#contract-tests-vs-construction-tests).
  - **Goal-based check** — build config, scaffolding, generated-code
    consumption, smoke entry points. The task's `Done when:` is the
    contract; verify with a one-liner (build command, `grep`, typecheck)
    instead of a test file. Don't write a test that just asserts what
    the compiler already proves.
  - **Visual / manual QA** — UI rendering, end-to-end UX flows. The task
    records the manual check explicitly. For user-facing flows that are
    part of the spec's contract, the verification artifact — automated or
    manual — should simulate the user's gesture and assert *what the user
    actually sees* (rendered text, visible elements, navigation), not
    internal state (store contents, mock-call counts, context-provider
    values). A test that passes when the on-screen result is wrong is
    mode-mismatched, regardless of which framework wrote it. Add
    automation when the regression cost (UI bugs ship invisibly) outweighs
    the cost (flakiness, framework brittleness); the choice of tool is the
    adopter's. A third flavor — *exploratory / visual fuzz* — drives the
    UI with varied or random input and asserts **invariants** ("didn't
    crash, didn't render garbage, layout holds, no overflow") rather than
    specific outputs. Reach for it when the failure mode is open-ended and
    you can't enumerate the gestures up front.

  Spikes and throwaway exploration are out of scope.
- **Design tests up front, before any code.** Contract tests live in
  `spec.md` and are written when the spec is written (see the `new-spec`
  step above). During PLAN, write construction tests for **every** task
  into `plan.md` (under each task's `Tests:` subsection) before EXECUTE
  begins. If you can't write the test, the task is too vague to implement —
  sharpen the plan first. Discovering a missing or wrong construction test
  during EXECUTE is fine, but the fix is "update plan.md, then resume
  EXECUTE", not "skip ahead".
- **Spec-mode adversarial review before EXECUTE.** If PLAN produced or
  modified a spec (i.e. you ran `new-spec`, or you sharpened an existing
  `spec.md` / `plan.md`), invoke `adversarial-reviewer` in spec mode
  against the spec + plan and iterate to clean before EXECUTE begins.
  Cheap-to-fix-early applies harder to specs than to code — catching a
  vague behavior, a missing `Depends on:`, or a mismatched verification
  mode here costs a sentence, not a re-plan. Same Profile-A caveat as
  the post-impl review: skip if the project doesn't use the reviewer.
- **Initialize the loop's state file.** Copy `docs/_templates/state.json`
  to `docs/specs/<feature>/state.json` and set `feature` to the spec
  slug. The file is gitignored — it's session-scratch, not history. Write
  it atomically (tmp-file + rename) on every update so a mid-write read
  never produces malformed JSON. Run
  `tools/check-done.py docs/specs/<feature>/state.json --phase plan`; on
  the first invocation it will exit 1 with `plan not approved` — **this
  is the expected cue to run the spec-mode reviewer**, not a stop-and-
  surface signal. Once the reviewer is clean, flip
  `plan_review_status` to `approved` and re-run; exit 0 unlocks EXECUTE.
  Schema reference:
  [`CONVENTIONS.md`](../../../docs/CONVENTIONS.md#work-loop-state).

The output of this step is a written plan (with tests) you can return to.
Don't keep it in your head — your context will turn over and you'll lose it.

### 2. EXECUTE — make the change

Match the discipline to the verification mode you picked during PLAN:

- **TDD-mode tasks** — red-green-refactor:
  1. Write the failing test first (red). Commit it if non-trivial.
  2. Write the minimum code to make it pass (green). Commit.
  3. Refactor with the test as your safety net. Commit.
- **Goal-based check** — write the code, then run the one-liner from
  `Done when:`. No production test file.
- **Visual / manual QA** — implement, then run the manual check recorded
  in the task. Record the result.

For each task, implement the smallest coherent unit of work toward the
goal. Resist the urge to fix unrelated things you notice along the way;
note them in `notes/` for later. Scope creep is the single biggest source
of plan-vs-implementation drift.

#### Parallel dispatch discipline

When this skill fans out — multiple implementers in supervisor mode, or
multiple specialist reviewers in REVIEW — the rules are the same and
they live here, single-sourced. Both call sites below reference this
discipline rather than restating it.

- **One tool-call message, one Agent use per target.** Issue all
  subagent invocations in a single message. Do not call them
  sequentially. The participants are independent, the lenses are
  independent, and sequencing tempts you to react to the first return
  before the rest land — which gives each subagent a different state.
- **Barrier-wait.** Don't issue follow-on Agent calls until every
  subagent in the round has returned.
- **Harness-level non-returns are failures.** A timeout, a tool error,
  or a missing report counts as `failed` for that target. Treat it the
  same as a substantive `failed` status; do not retry silently.
- **Merge results in your own context.** The subagents return markdown.
  You read N reports, group findings or status by your own bookkeeping
  (state.json for implementers; severity buckets for reviewers), then
  decide.

#### Supervisor mode (parallel implementers)

If the plan has **two or more tasks declaring `Depends on: none`**, the
loop branches into supervisor mode for EXECUTE. You become the
supervisor; each independent task gets an `implementer` subagent (see
[`.claude/agents/implementer.md`](../../../.claude/agents/implementer.md))
in its own worktree. The full rationale, boundary, and merge discipline
live in
[`CONVENTIONS.md § Supervisor mode`](../../../docs/CONVENTIONS.md#supervisor-mode).
Throughout this procedure, **"task-id order" means numeric where IDs
look like `T1`, `T2`, … ; lexicographic otherwise.**

The procedure:

0. **Pre-flight: check for stale worktrees.** Run `git worktree list`
   and `git worktree prune`. If `.worktrees/<task-id>/` exists or the
   branch `<base-branch>-<task-id>` exists for any task you're about
   to dispatch, a prior session left scratch behind. **Surface to a
   human; do not silently reuse or destroy** — the scratch may carry
   in-flight work the previous run was about to commit. Resume happens
   manually.
1. **Set up worktrees.** For each independent task `<task-id>`:
   ```bash
   git worktree add .worktrees/<task-id> \
     -b "$(git branch --show-current)-<task-id>"
   ```
   Append
   `{task_id, branch, path, status: "in-progress", report_path: null}`
   to `state.json.worktrees`.
2. **Dispatch implementers in parallel** per the parallel-dispatch
   discipline above. Each brief includes: the task ID, the plan-task
   body, the worktree path, and paths to the spec + plan.
3. **Persist each report and update state.** For each returning
   subagent, in this order — match first, write second, update state
   last:
   1. Parse the report's opening `## Task <task-id>` heading and match
      that `<task-id>` against `state.json.worktrees[i].task_id`. If
      no entry matches, surface as `failed` for an unknown task —
      never silently append a new entry, and never write the file
      under an unvalidated name.
   2. Write the report verbatim to
      `docs/specs/<feature>/notes/implementer-<task-id>-<iteration>.md`,
      where `<iteration>` is the current `state.json.iteration_count`.
      On a fresh loop the value is `0`, so the first attempt lands as
      `…-0.md` ("before any review iteration has run"); subsequent
      re-plans see the counter bumped (see step 4 below) so reports
      never overwrite one another. Create `docs/specs/<feature>/notes/`
      if it doesn't yet exist (the directory is optional per the
      [Specs and Plans](#4-specs-and-plans--docs-specs-feature)
      convention).
   3. Atomically update `state.json.worktrees[i]`: set `status`
      (`ready` / `blocked` / `failed`) and `report_path` to the path
      you just wrote.

   The match-first ordering means a parse failure never produces an
   orphan report on disk; the write-before-update means a crash
   between substeps 2 and 3 leaves a recoverable signal — the report
   file exists, the entry still says `in-progress`, and the next
   supervisor session's stale-worktree pre-flight treats that as
   leftover scratch and surfaces it.
4. **Handle non-ready tasks first.** If any implementer reports
   `blocked` or `failed`, do not merge. Surface the failed-task list
   (with `report_path` pointers), **increment `state.json.iteration_count`**
   so the next attempt's report filename won't collide with this
   one's, then return to PLAN and revise the offending task. Do not
   redispatch the same implementer on the same task — the assumption
   that produced the failure is what needs revising, not the attempt.
5. **Merge ready tasks sequentially.** From the primary worktree, in
   task-id order:
   ```bash
   git merge --no-ff "$(git branch --show-current)-<task-id>"
   ```
   A conflict means the tasks weren't actually independent. Abort
   (`git merge --abort`), return to PLAN, fix the `Depends on:`
   declarations.
6. **Clean up worktrees.** After all merges succeed:
   ```bash
   git worktree remove .worktrees/<task-id>
   ```
   If that fails (uncommitted files, locked index, build artifacts),
   retry once with `--force`. On persistent failure, leave the
   directory in place, note the path in your end-of-loop summary, and
   proceed to gates — don't block on cleanup. Worktree entries in
   `state.json.worktrees` keep their terminal status for the rest of
   the loop so the next reader can reconstruct what each task did.
7. **Run gates yourself** (next phase). The implementers' gate results
   were advisory; the gates of record run in the primary against the
   merged state.

In single-agent mode (no independent tasks), skip the supervisor branch
entirely and execute as the sole agent — that's the default flow above.

### 3. GATES — mechanical verification

Run, in order, and only proceed if each passes:

```bash
<lint command>      # style and basic correctness
<typecheck command> # type safety (if applicable)
<test command>      # behavior
```

These are the project's **objective** completion criteria. If a gate fails,
go to FIX. Don't move past a failing gate by editing the gate.

### 4. REVIEW — adversarial self-review

After gates pass, run adversarial review against the spec. Use the
`adversarial-reviewer` subagent (in `.claude/agents/adversarial-reviewer.md`):

```
Use the adversarial-reviewer subagent to review my changes against
docs/specs/<feature>/spec.md
```

The subagent reads adversarially — it's looking for what you missed, not
celebrating what you did. Findings come back grouped by severity
(Blockers / Concerns / Nits), each with a one-sentence `Fix:`. Iterate
until the agent returns `Clean — ready to commit.`

**After each reviewer pass, update `state.json`** before iterating:

1. Move `finding_fingerprints` → `previous_finding_fingerprints`.
2. For each surviving finding the reviewer surfaced, compute
   `sha1("<file>|<line>|<title>")` where:
   - `<file>` is the cited path exactly as the reviewer wrote it.
   - `<line>` is the first integer after the first colon in the citation,
     as a decimal string. `foo.py:88` → `88`; `foo.py:88-92` → `88`.
   - `<title>` is the reviewer's bolded heading for the finding, e.g.
     `**3. PLAN-phase exit-1 conflates "not yet done" with "stop".**` —
     keep the surrounding `**` markers and everything between them.

   Write the resulting hex digests to `finding_fingerprints` (order
   doesn't matter — `check-done.py` sorts before comparing).
3. Increment `iteration_count`.
4. Write the file atomically (tmp + rename).
5. Run `tools/check-done.py <state-path> --phase review`. Exit 1 with
   `no progress` means the same findings landed two iterations in a row;
   stop and surface to a human rather than spinning a third.

**Specialist reviewers — use after adversarial-reviewer is clean.** Pick
the ones the diff actually warrants; don't run all three by default.

- `security-reviewer` — for diffs that cross a security boundary (auth,
  secrets, user input, deserialization, file/network I/O, dependencies,
  LLM/agent code). OWASP + STRIDE lens. Complements SAST/SCA scanners;
  does not replace them.
- `quality-engineer` — testability, observability, reliability, and
  maintainability lens. Also drafts contract or construction tests on
  request. Different lens from adversarial-reviewer — don't skip it
  because the spec already shipped.

**Dispatch reviewers in parallel when you invoke more than one** per
the [Parallel dispatch discipline](#parallel-dispatch-discipline)
documented under EXECUTE — the same rules cover both fan-out sites in
this skill. Fan-out works here because reviewer output is markdown the
orchestrator reads, not a structured contract: you read N reports,
group findings by severity yourself, deduplicate where two reviewers
caught the same thing, then iterate on the merged list. Fingerprint
computation (state.json) happens once per fan-out round, not once per
reviewer.

If reviewing a spec-less change (a refactor, say), self-review against this
checklist instead:

- Does the diff match the plan you wrote in step 1? Note divergences.
- For each touched function: is the test coverage no worse than before?
- Did anything outside the planned scope get touched? Why?
- What's the dog that didn't bark — what *should* have changed and didn't?

### 5. DECIDE — fix or finish

- **Blockers from review** → go to FIX, then re-run GATES and REVIEW.
- **Concerns from review** → fix the ones you can in this PR; capture the
  rest as follow-up issues. Don't let "concerns" rot in chat.
- **Gates green and review clean** → ready to ship. Walk this end-of-session
  checklist; refuse to declare done until every line is true:
  - GATES were clean (lint, typecheck, tests).
  - `adversarial-reviewer` returned `Clean — ready to commit.` Plus
    `security-reviewer` (security boundary) and `quality-engineer`
    (maintenance lens) when the diff warrants.
  - For the final loop of a multi-loop spec: `quality-engineer` ran
    against the whole spec, not just the last diff, and returned clean.
    Per-task gates verify N contracts; this is the pass that verifies the
    integrated journey.
  - `git status` shows no uncommitted or untracked files (except
    gitignored scratch).
  - Conventional commit format used; no force-push to shared branches.
  - Learnings captured per the next section (AGENTS.md, skill, or doc).
  - PR opened — or merged directly, if that's your workflow — with the
    four-question template filled in.

## FIX phase

Fixing is the same loop, scoped to a single finding:

1. Read the finding carefully. Don't fix the symptom — fix what the reviewer
   actually flagged.
2. Make the smallest change that addresses it.
3. Re-run GATES.
4. Re-run REVIEW only if the fix touched logic the reviewer hadn't already
   approved. Otherwise, you can skip review and move on.

## Termination — when to stop iterating

The loop must terminate. Iteration without termination is how Ralph loops
(see below) burn money. Stop when **any** of these is true:

1. **Gates green AND review clean** — the normal exit. Ship.
2. **`tools/check-done.py` exits non-zero.** The script is the mechanical
   side of termination, reading from `state.json` (see
   [`CONVENTIONS.md`](../../../docs/CONVENTIONS.md#work-loop-state)). It
   fires on iteration cap, token-budget cap, consecutive-error counter,
   pending plan approval (PLAN phase only), and fingerprint stasis
   (REVIEW phase only). The exit message tells you which.
3. **Diff is shrinking but findings aren't** — you're spot-fixing without
   addressing root cause. This is a judgment call, not in `check-done.py`.
   Stop and rethink the approach (back to PLAN).

If you hit any of these and the work isn't done, the task is bigger than
you thought. Stop, write down what you learned, and re-plan. Never
silently expand scope to make a finding go away.

## Capture what was learned

Before the PR is opened, ask: *what would have made this loop go faster?*
Where the answer goes depends on the *shape* of the learning:

- **Practitioner lessons** — a repeatable pattern that worked, a
  gotcha that bit you, or an antipattern that looked good but rotted —
  go in [`docs/knowledge/patterns.jsonl`](../../../docs/knowledge/patterns.jsonl)
  as a new entry. The schema is in
  [`docs/knowledge/README.md`](../../../docs/knowledge/README.md);
  one JSON object per line, scoped to a file glob. The
  `session-start` hook reads these so the next agent starts with the
  relevant ones already in context.
- "I had to grep for `<thing>` repeatedly" → add a pointer in
  `docs/architecture/<subsystem>.md`.
- "The test command for this package is unusual" → add it to the package's
  `AGENTS.md`.
- "I made the same wrong assumption twice" → if it's a
  knowledge-base-shaped lesson (a pattern/gotcha/antipattern), record
  it in `patterns.jsonl`; if it's project-conventions context, add a
  line to the relevant `AGENTS.md` (root or per-package) so the next
  agent doesn't repeat it. If it's a vocabulary issue (a term that
  means something specific here), it goes in `docs/guides/reference/`
  as a glossary entry.
- "This workflow is now the third time I've done it" → propose it as a new
  skill in `.claude/skills/`.

This is the part of the loop that makes the *project* smarter, not just the
current PR. Skipping it means the next agent (or you, next month) will
re-derive the same insight.

## Ralph loops — the AFK variant

The work-loop above is an *in-session* loop: one Claude Code conversation,
state in working memory plus the repo. **Ralph loops** are a different shape:
each iteration is a *fresh* Claude Code instance, with state living entirely
in files (PROMPT.md, progress notes, git history, AGENTS.md updates).

Ralph is the right tool when:

- You want unattended, long-running work — overnight, weekend, AFK.
- The completion criterion is *fully mechanical* — tests pass, a spec
  checklist is fully ticked, a benchmark hits a threshold.
- The task can be sliced into items each small enough for a single
  context window.
- You can afford the spend (set hard caps).

Ralph is the wrong tool when:

- "Done" is fuzzy or aesthetic ("make it feel polished").
- The task needs human judgment mid-flight (architectural choices,
  ambiguous requirements, security-sensitive decisions).
- Verification is flaky — flaky tests turn Ralph into a slot machine.
- You haven't already done the work-loop above on a similar task at
  least once. Ralph amplifies whatever your conventions are; if those
  aren't tight, Ralph just produces more bad code faster.

This repo includes a Ralph harness at `tools/ralph.sh` for when those
conditions are met. See [`tools/RALPH.md`](../../../tools/RALPH.md) for
operating instructions, hard limits, and the cost/safety rules. **Read it
before running Ralph.** AFK doesn't mean *unconsidered* — it means
*pre-considered*.

## Anti-patterns to refuse

- **Skipping PLAN because "the task is small."** If it's truly small, the
  plan is one sentence — write it anyway. The discipline is the point.
- **Declaring an empty declined-pattern register on a non-trivial task.**
  On any non-trivial change something was tempting — a layer, a flag, a
  helper, a defensive wrapper, a tidy abstraction. A register with nothing
  in it means you weren't looking, not that there was nothing to find.
- **Writing code before deciding how it'll be verified.** "I'll figure out
  the test after" is how features ship with the wrong contract. Every task
  picks its verification mode (TDD / goal-based / manual QA) during PLAN;
  for TDD-mode tasks, the test exists before the production code does.
- **Editing the test until it passes.** This makes the gate green by lying.
  If a test is wrong, fix the test in a separate commit with a justification.
- **Deferring a test because the code fails it.** The inverse of editing
  the test — same lie, opposite direction. If a red test fails because the
  code under test is wrong, fix the code; plausible-sounding rationales
  ("flaky", "out of scope for this PR", "covered elsewhere") are how
  regressions ship. If the test is genuinely wrong, fix it in a separate
  commit with the reason; if the test is right and the code can't pass it
  this session, the task isn't done — surface it, don't bury it.
- **Declaring victory because gates pass.** Gates are necessary, not
  sufficient. Review catches what gates can't (missing edge cases, scope
  creep, spec drift).
- **Declaring spec-complete from per-task gates.** When a spec is
  decomposed into N loops, per-task gates verify N contracts — not the
  integrated journey. Before the final loop's DECIDE, run
  `quality-engineer` against the whole spec rather than just the last
  diff, so scenarios the parts test but the whole doesn't get caught.
- **Running Ralph on a fresh task instead of work-loop.** Ralph compounds
  bad foundations. Do at least one in-session pass first to validate the
  approach.
- **Looping without capturing learnings.** Every loop that ends without
  updating *some* doc, skill, or note is a loop whose lessons are lost.
