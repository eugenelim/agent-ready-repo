---
name: work-loop
description: Use this skill whenever you're implementing a non-trivial change — a feature, a bug fix that touches more than one file, a refactor, or anything spec-driven. It enforces the project's plan → execute → self-review → fix loop with mechanical gates (lint, typecheck, tests) and adversarial review. Default to this skill for any task larger than a one-line edit.
---

# Skill: work-loop

This is the project's standard inner loop for non-trivial work. It exists
because LLM self-assessment is unreliable: agents declare victory when they
*feel* done, not when objective gates pass. This skill replaces "feel" with
verifiable termination criteria.

## When this skill applies

- Implementing a spec from `docs/specs/`.
- Bug fixes that touch more than one file.
- Refactors.
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
  and what you are *not* changing. Three sentences is enough.
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
    adopter's.

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
2. **Same finding two iterations in a row** — you're going in circles. Stop.
   Either the fix is wrong or the finding is. Surface it to a human.
3. **Diff is shrinking but findings aren't** — you're spot-fixing without
   addressing root cause. Stop and rethink the approach (back to PLAN).
4. **Iteration cap reached** — the project's hard cap of 5 in-session
   iterations. If you hit the cap, the task is bigger than you thought.
   Stop, write down what you learned, and re-plan.

Never silently expand scope to make a finding go away.

## Capture what was learned

Before the PR is opened, ask: *what would have made this loop go faster?*
Common answers and where they go:

- "I had to grep for `<thing>` repeatedly" → add a pointer in
  `docs/architecture/<subsystem>.md`.
- "The test command for this package is unusual" → add it to the package's
  `AGENTS.md`.
- "I made the same wrong assumption twice" → add a line to the relevant
  `AGENTS.md` (root or per-package) so the next agent doesn't repeat it.
  If it's a vocabulary issue (a term that means something specific here),
  it goes in `docs/guides/reference/` as a glossary entry.
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
