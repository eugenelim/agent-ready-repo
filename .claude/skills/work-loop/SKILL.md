---
name: work-loop
description: Use this skill whenever you're implementing a non-trivial change -- a feature, a multi-file bug fix, a refactor, a migration, a framework or dependency upgrade, a schema or API change, performance work, an infrastructure or build-system edit, or anything spec-driven. It enforces the project's plan -> execute -> self-review -> fix loop with mechanical gates (lint, typecheck, tests) and adversarial review. Default to this skill for any task larger than a one-line edit.
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
  The contract is part of the spec — `Acceptance Criteria` and
  `Testing Strategy` are written *during* `new-spec`, not later. A spec with
  either section left empty is not finished.
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
    compressible invariant. The contract lives in `spec.md` (Acceptance
    Criteria + Testing Strategy); construction tests live in `plan.md`,
    `Tests:` before `Approach:`, red-green-refactor.
    Default for testable logic.
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
- **Design tests up front, before any code.** The contract lives in
  `spec.md` (Acceptance Criteria + Testing Strategy) and is written when
  the spec is written (see the `new-spec` step above). During PLAN, write
  construction tests for **every** task into `plan.md` (under each task's
  `Tests:` subsection) before EXECUTE begins. If you can't write the
  test, the task is too vague to implement — sharpen the plan first. Discovering a missing or wrong construction test
  during EXECUTE is fine, but the fix is "update plan.md, then resume
  EXECUTE", not "skip ahead".
- **Pre-EXECUTE adversarial review.** Select a subagent matching
  `adversarial-reviewer` and ask it to review the spec + plan in
  spec/plan-review mode. Iterate to clean before EXECUTE begins when
  **either** trigger fires (fallback if no such subagent is installed:
  proceed but note the missing review in the final summary):

  1. **Spec amendment.** PLAN produced or modified a spec — you ran
     `new-spec`, or you sharpened an existing `spec.md` / `plan.md`.
  2. **Structural change.** Any plan task introduces structural surface
     area. Walk this checklist; if **any** condition matches, the
     trigger fires:
     - New module boundary — a new directory under `packages/` or
       `apps/`.
     - New dependency added to package code — especially a framework,
       ORM, or runtime.
     - New abstraction layer — a new interface mediating between two
       existing concrete things; a new factory, registry, locator, or
       service-locator pattern.
     - New top-level directory — the most expensive of the four to
       undo. Many projects already gate this through their own RFC or
       ADR process; the trigger fires here either way.

  The structural-change trigger fires even when no spec is amended in
  this PR — the trigger is the **plan's task shape**, not a spec edit.
  Both triggers route to the same reviewer mode and the same spec-stage
  checklist; what differs is the standard the reviewer measures against.
  When the structural-change trigger fires, the reviewer checks the
  plan against the spec's **Boundaries** section (defined by the
  `new-spec` skill's bundled `spec.md` template) —
  primarily `Never do` for hard structural rules and `Ask first` for
  the ones that require sign-off; `Always do` for positive defaults
  the plan must honour. If `Boundaries` is empty, that's the
  finding to surface first — an empty Boundaries section is a
  spec-stage gap, not a fallback cue. Only when the spec has no
  Boundaries section at all (an unmigrated template, say) fall back
  in order to: the PLAN step's **declined-pattern register** (above),
  and the AGENTS.md **"Check before acting"** list (when installed
  elsewhere this slug arrives as a fragment under
  `docs/AGENTS.fragments/`; merge the items the adopter wants into their
  own AGENTS.md).

  **Re-fire on mid-EXECUTE re-plan.** If EXECUTE discovers a missing or
  wrong task and updates `plan.md` per the *Design tests up front* rule
  above, re-evaluate the structural-change checklist against the
  updated plan. If a re-plan introduces any of the four conditions that
  the original plan did not, the trigger re-fires and the reviewer
  re-runs before EXECUTE resumes. This is where most over-engineering
  emerges in practice — a tempting abstraction surfaces mid-flight, not
  during the original PLAN — so the one-shot trigger is not enough.

  Cheap-to-fix-early applies harder to specs and structural decisions
  than to code — catching a vague behavior, a missing `Depends on:`,
  a mismatched verification mode, or a misplaced module boundary here
  costs a sentence; catching it post-EXECUTE costs a re-do. Gate
  mechanism is unchanged: the `loop-cohort approve-plan` verb flips
  `state.json.plan_review_status` to `approved` once the reviewer is
  clean; `loop-cohort check <spec-dir> --phase plan` unlocks EXECUTE.
  No new state fields. **Both triggers respect the Profile-A opt-out:**
  skip if the project doesn't use the reviewer at all.
- **Initialize the loop's state file.** Run this skill's bundled
  `scripts/loop-cohort.py init docs/specs/<feature>`; the tool copies
  the bundled `assets/state.json` template into place, sets `feature`
  to the spec slug, and writes atomically. The file is gitignored —
  session-scratch, not history. Then run `loop-cohort.py check
  docs/specs/<feature> --phase plan`; on the first invocation it will
  exit 1 with `plan not approved` — **this is the expected cue to run
  the pre-EXECUTE reviewer**, not a stop-and-surface signal. Once the
  reviewer is clean, run `loop-cohort.py approve-plan docs/specs/<feature>`
  and re-run check; exit 0 unlocks EXECUTE. Every state mutation —
  template copy, status flip, atomic write — is owned by the tool; do
  not edit `state.json` by hand. Schema reference:
  [`references/state-schema.md`](references/state-schema.md).

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

<!-- Bundled-fixes carve-out — canonical site. Mirrored by
     implementer.md (operating envelope) and adversarial-reviewer.md
     (scope check #4). Keep all three in sync. -->
**Bundled-fixes carve-out.** Same-area, same-concern, mechanical
ride-alongs land in the change — dead import, stale comment that now
contradicts the new code, unused local the change orphaned, typo in a
sibling file. *Same area* means a file in a directory that already
contains a file the change is editing — siblings in the touched
directory, not a walk-up to the parent and not a sideways jump to a
directory the change isn't editing. "The change" = the current plan
task for the executor; the merged PR diff for the reviewer. The
reviewer is loading that directory's context for the primary change;
tagging along is cheap. List ride-alongs in the PR description under
`Bundled fixes:`, one line each, so the reviewer can scan them at a
glance. The carve-out fails closed on any of: a file outside a
touched directory, a design call, a behavior change. Those still go
to `notes/` (EXECUTE-phase surplus, picked up by a future plan task);
contrast with the DECIDE-phase `Deferred:` bucket below, which holds
reviewer findings the loop chose not to fix — different lifecycle,
different reader. **Volume guard** — bundled fixes are individually small
(a line or two each). The bundle should also be visibly smaller than
the primary change: if a reviewer reading the PR couldn't immediately
tell which part is the primary change and which are ride-alongs, you
sprawled — move the surplus to `notes/`. In supervisor mode, the
dispatch brief explicitly authorizes the carve-out and restates the
gates so the implementer applies them per its own task; without that
authorization line the implementer defaults to no-carve-out.

**`Bundled fixes:` in the PR description.** The work-loop emits a
named `Bundled fixes:` section in the PR description that doesn't
appear in the project's PR template — one line per ride-along landed
under the carve-out above. Append it as a standalone section below
the standard template content; do not modify the template itself.
(See step 5 for the companion `Deferred:` section.)

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
supervisor; for each independent task, select a subagent matching
`implementer` and dispatch it against the task in its own worktree per
the parallel-dispatch discipline above.

**The full 7-step procedure** (pre-flight, worktree setup, dispatch,
report persistence, non-ready handling, merge, cleanup) lives in
[`references/supervisor-mode.md`](references/supervisor-mode.md) — load
it on demand when this branch fires. The single-agent fallback (when no
`implementer`-matching subagent is installed) is documented there too.

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

After gates pass, run adversarial review against the spec. Select a
subagent matching `adversarial-reviewer` and pass it the diff plus the
spec path (e.g. `docs/specs/<feature>/spec.md`). Fallback if no such
subagent is installed: proceed but note the missing review in the final
summary — the gates step is the mechanical termination criterion; this
step is judgmental and the loop degrades to gates-only without it.

The subagent reads adversarially — it's looking for what you missed, not
celebrating what you did. Findings come back grouped by severity
(Blockers / Concerns / Nits), each with a one-sentence `Fix:`. Iterate
until the agent returns `Clean — ready to commit.`

**After each reviewer pass, record findings via the tool** before
iterating. Write the reviewer's report to disk, then run:

```
loop-cohort.py review record docs/specs/<feature> --report <report-path>
loop-cohort.py check docs/specs/<feature> --phase review
```

`review record` parses the report's findings (anchored on the
adversarial-reviewer's documented `**N. <title>.** \`file:line\`. … Fix: …`
format), computes `sha1("<file>|<line>|<title>")` per the canonical
algorithm, rotates `finding_fingerprints` → `previous_finding_fingerprints`,
sets the new list, increments `iteration_count`, and writes atomically —
one transaction, no by-hand JSON. If the parser surfaces zero findings on
a non-clean report it exits non-zero; pass `--fingerprint <hex>` repeated
to override. `check --phase review` then enforces stasis detection: exit
1 with `no progress` means the same findings landed two iterations in a
row; stop and surface to a human rather than spinning a third.

**Specialist reviewers — use after adversarial-reviewer is clean.** Pick
the ones the diff actually warrants; don't run all three by default.
Select each via the same "subagent matching `<role>`" pattern as
adversarial-reviewer above; absence of any specialist subagent is a
note in the summary, not a blocker.

- Match `security-reviewer` — for diffs that cross a security boundary
  (auth, secrets, user input, deserialization, file/network I/O,
  dependencies, LLM/agent code). OWASP + STRIDE lens. Complements
  SAST/SCA scanners; does not replace them.
- Match `quality-engineer` — testability, observability, reliability,
  and maintainability lens. Also drafts contract or construction tests
  on request. Different lens from adversarial-reviewer — don't skip it
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

Route each reviewer finding into one of two resolution modes — `apply`
(fix in this PR) or `defer` (capture as a follow-up). This is the
work-loop's interpretation of reviewer output; the reviewer keeps its
narrow Blockers / Concerns / Nits contract. Once routed, act on each
mode below, then evaluate the terminal-state bullet last.

- **Blockers** → `apply`. Re-run GATES and REVIEW after each fix.
- **Concerns** → `apply` if mechanical and in scope (default for any
  Concern whose fix meets the bundled-fixes gates above). `defer` if
  the fix would cross files outside the plan, require a design call,
  or change user-visible behavior the spec didn't authorize. Don't let
  Concerns rot in chat — every Concern resolves into one of the two.
- **Nits** → same two modes as Concerns. `apply` if they meet the
  bundled-fixes gates above (ride along in `Bundled fixes:`).
  Otherwise `defer` — one line in `Deferred:`. Every Nit resolves
  into one of the two; the `Deferred:` line *is* the acknowledgement
  that the loop saw the Nit and chose not to fix.
- **Deferred items** → one-line follow-up note in the PR description
  under `Deferred:` so they don't rot. Append it as a standalone
  section below the standard template content alongside the
  `Bundled fixes:` section from EXECUTE; do not modify the template
  itself. Don't open separate issues by default — the PR is the
  durable record.
- **Gates green and review clean** → ready to ship. Walk this end-of-session
  checklist; refuse to declare done until every line is true:
  - GATES were clean (lint, typecheck, tests).
  - For each reviewer the diff warranted (`adversarial-reviewer`
    always; `security-reviewer` on security-boundary diffs;
    `quality-engineer` on every loop, plus a whole-spec pass on the
    final loop of a multi-loop spec): either the subagent returned
    `Clean — ready to commit.`, **or** no matching subagent was
    installed and the final summary names the missing review by its
    role label — e.g. `adversarial-reviewer: no matching subagent
    installed; review skipped`. *Silently skipping the reviewer is not
    allowed* — the select-or-note discipline applies here, not just at
    invocation time.
  - Whole-spec `quality-engineer` pass (final loop of a multi-loop
    spec only): same select-or-note rule. Per-task gates verify N
    contracts; this is the pass that verifies the integrated journey.
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
2. **`scripts/loop-cohort.py check` exits non-zero.** The script is the
   mechanical side of termination, reading from `state.json` (see
   [`references/state-schema.md`](references/state-schema.md)). It
   fires on iteration cap, token-budget cap, consecutive-error counter,
   pending plan approval (PLAN phase only), and fingerprint stasis
   (REVIEW phase only). The exit message tells you which.
3. **Diff is shrinking but findings aren't** — you're spot-fixing without
   addressing root cause. This is a judgment call, not in `loop-cohort`.
   Stop and rethink the approach (back to PLAN).

If you hit any of these and the work isn't done, the task is bigger than
you thought. Stop, write down what you learned, and re-plan. Never
silently expand scope to make a finding go away.

## Capture what was learned

Before the PR is opened, ask: *what would have made this loop go faster?*
Where the answer goes depends on the *shape* of the learning:

- **Practitioner lessons** — a repeatable pattern that worked, a
  gotcha that bit you, or an antipattern that looked good but rotted.
  Check `docs/CONVENTIONS.md` for a `Knowledge base` section: if
  present, follow what it says for schema, file location, and how the
  session-start hook surfaces these on the next loop. If the section
  isn't there, fall back to a one-line note in the relevant
  `AGENTS.md` (root or per-package) — the next agent still sees it.
- "I had to grep for `<thing>` repeatedly" → add a pointer in
  `docs/architecture/<subsystem>.md`.
- "The test command for this package is unusual" → add it to the package's
  `AGENTS.md`.
- "I made the same wrong assumption twice" → if it's a
  knowledge-base-shaped lesson (a pattern/gotcha/antipattern), follow
  the routing in the first bullet; if it's project-conventions
  context, add a line to the relevant `AGENTS.md` (root or
  per-package) so the next agent doesn't repeat it. If it's a
  vocabulary issue (a term that means something specific here), it
  goes in `docs/guides/reference/` as a glossary entry.
- "This workflow is now the third time I've done it" → propose it as a new
  skill.

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
conditions are met; the companion `tools/RALPH.md` documents
operating instructions, hard limits, and the cost/safety rules. **Read
it before running Ralph.** AFK doesn't mean *unconsidered* — it means
*pre-considered*.

## Anti-patterns to refuse

- **Skipping PLAN because "the task is small."** If it's truly small, the
  plan is one sentence — write it anyway. The discipline is the point.
- **Declaring an empty declined-pattern register on a non-trivial task.**
  On any non-trivial change something was tempting — a layer, a flag, a
  helper, a defensive wrapper, a tidy abstraction. A register with nothing
  in it means you weren't looking, not that there was nothing to find.
- **Skipping pre-EXECUTE review on a structural change because "the plan
  looks fine".** That's exactly when it doesn't. The cost of catching a
  misplaced module boundary or an unjustified abstraction layer at PLAN
  is a sentence; at REVIEW it's a re-do. The four structural triggers
  (new module boundary, new dependency, new abstraction layer, new
  top-level directory) are the cases where over-engineering is most
  expensive to undo — that's the whole reason the trigger exists.
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
  regressions ship. (Beyoncé Rule: if you liked it, you should have put
  a test on it.) If the test is genuinely wrong, fix it in a separate
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
