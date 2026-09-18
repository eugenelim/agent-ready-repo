# Supervisor mode — procedure

> **Phase 1:** `dispatch-decision`, `worktree {add, record, list, merge, cleanup, preflight}`,
> and `auto-parallel` are **disabled** — those verbs exit non-zero. The parallel
> fan-out path in this document is unavailable until Phase 2. Run tasks
> sequentially; use `loop-cohort schedule <spec-dir> --expect-run-id "$run_id"` for
> topological order.

**Default is sequential implementer dispatch.** Supervisor mode computes the
plan's full `Depends on:` DAG (`loop-cohort schedule <spec-dir>`) and, when an
`implementer` subagent is installed, dispatches each plan task in topological
order with one implementer at a time. It does *not* auto-fan-out. `schedule`
stops the run on a dependency cycle. It reports a forward reference (a task
whose declared dependency is authored later) on stderr, corrects the wave order
so the dependency runs first, and continues. A `Depends on:` entry that
names no task in the plan is refused: `schedule` exits non-zero and names every
offending task→dependency pair without persisting any state. The field is read
up to its first `(`, so an ID written inside or after parenthetical prose is
commentary rather than a declared dependency — it is neither scheduled as an
edge nor reported as unknown.

This file owns the **opt-in parallel-write path** only. It is entered
deliberately — never automatically — and only for a wave that clears the
**dispatch gate**, which has two halves checked at two points:

- **Category half — auto-derived from the diff.** You **don't hand-classify**:
  omit `--category` and `dispatch-decision` derives each task's category from
  its branch's committed diff, fail-closed (only an all-added, no-danger-path
  diff is `cannot-collide`; rename/delete, danger-paths, modified-existing, and
  cross-branch basename/dir collisions all serialize). Pass `--category` only
  to **override** — the sole way to assert the two human-judged safe categories,
  neither auto-derived: `typed-group-b` (a type-shaped change) and `textual-loud`
  (append-mostly textual edits whose collisions surface as *loud* merge-tree
  conflicts rather than silent semantic breakage). Deciding either isn't
  fail-closed-mechanizable, which is why neither is auto-derived. (The three
  together are the `SAFE_CATEGORIES` the dispatch gate accepts.)
- **Disjointness half — on populated branches.** A clean `git merge-tree`
  file-disjointness check is only meaningful once the implementers have
  written and committed, so it is enforced at the **merge** step (step 5's
  `git merge --no-ff` aborts on any collision — the loud backstop). The
  read-only **preview** of that check is `loop-cohort dispatch-decision
  --branch <b> …` (categories auto-derived), which classifies each branch and
  then calls `dispatch_decision(categories, merge_tree_clean=…)` to print
  `parallel` or `serial`. Read that signature carefully: the function
  **consumes** a merge-tree verdict its caller hands it — it does not compute
  one, and no part of the shipped scripts runs `git merge-tree`. The producer
  of that verdict is **unbuilt**, so the preview cannot be relied on for
  disjointness; step 5's aborting merge is where the check actually runs.
- **Even earlier — `Touches:` screen (optional).** If the plan's tasks declare
  `Touches:` globs, `loop-cohort schedule` prints `predicted-disjoint:
  yes|no|unknown` per wave. Treat a `no` as a reason to keep the wave serial
  *before* dispatch; `yes`/`unknown` change nothing — they **never** greenlight
  (the merge-tree check above stays the sole authority). Serialize-only screen.

Any non-safe category, or any merge-tree conflict, stays serial. Reviewer
(read) fan-out is a separate, always-safe path.

**Present the cleared-gate opportunity.** When `dispatch-decision` returns
`parallel`, branch on `state.json.auto_parallel` (set per-run via `loop-cohort
auto-parallel`, default off):

- **`auto_parallel` unset (default):** do not enter the procedure below
  silently — **present the cleared-gate opportunity to the human** (the
  parallel-eligible wave and its tasks; the verb's stderr rationale is the line
  to relay) and take the parallel path **only on an explicit opt-in**. Absent
  one, run the wave sequentially — the safe default. Present-and-default-safe,
  not the halt-and-wait Surface verb, so — *with `auto_parallel` unset* — an
  unattended run proceeds sequentially rather than blocking.
- **`auto_parallel` set:** the human pre-authorized this run; a **gate-cleared**
  wave enters the parallel procedure below **without** the opt-in (this is what
  lets a plan finish unattended). **GO-approval-only** — it skips only the
  human-confirm step for an **already-cleared** wave; it is never a gate input,
  never enters the parallel path for a wave the gate didn't clear, and a failed
  parallel wave (step-5 merge-abort, or a blocked/failed implementer at step 4)
  still **Surfaces and stops** — never auto-retries or relaxes a gate.

The trigger and concept stay in [`../SKILL.md` § EXECUTE](../SKILL.md); this
file owns the step-by-step procedure once the opt-in parallel path is taken.

Throughout this procedure, **"task-id order" means numeric where IDs
look like `T1`, `T2`, … ; lexicographic otherwise.** The `loop-cohort`
tool sorts by the same rule when merging.

The [parallel-dispatch discipline](#parallel-dispatch-discipline) is the same
as for REVIEW fan-out. References to it below mean that section.

Every state mutation — worktree creation, report persistence, status
updates, merges, cleanup — is owned by the `loop-cohort` tool at
`../scripts/loop-cohort.py`. The tool guarantees the match-first /
write-second / state-update-last ordering and atomic JSON writes; do
not edit `state.json` or invoke `git worktree` directly.

> **Phase 2 only.** The procedure below describes the parallel dispatch path,
> which is unavailable in Phase 1. The verbs `dispatch-decision`, `worktree`,
> and `auto-parallel` all exit non-zero in Phase 1 — run tasks sequentially
> using the topological order from `loop-cohort schedule`. This section is
> retained as the Phase 2 specification target.

## The procedure

0. **Pre-flight: surface stale worktrees.** Run

   ```
   loop-cohort.py worktree preflight docs/specs/<feature> <task-id> ...
   ```

   The tool runs `git worktree prune`, then checks for `.worktrees/<task-id>/`
   directories or `<base-branch>-<task-id>` branches left behind by a
   prior session. Non-zero exit means a previous run left scratch
   behind — **surface to a human; do not silently reuse or destroy.**
   The scratch may carry in-flight work the previous run was about to
   commit. Resume happens manually.

1. **Set up worktrees.** For each independent task `<task-id>`, run

   ```
   loop-cohort.py worktree add docs/specs/<feature> <task-id>
   ```

   The tool creates `.worktrees/<task-id>/` on branch
   `<base-branch>-<task-id>` and appends an
   `{task_id, branch, path, status: "in-progress", report_path: null}`
   entry to `state.json.worktrees`, atomically.

2. **Dispatch implementers in parallel** per the
   [parallel-dispatch discipline](#parallel-dispatch-discipline) below.
   Each brief includes: the task
   ID, the plan-task body, the worktree path, paths to the spec +
   plan, and an explicit **bundled-fixes authorization line** —
   "Bundled fixes authorized per the carve-out in `work-loop/SKILL.md`
   (EXECUTE phase); apply same-area, same-concern, mechanical
   ride-alongs only and report under `Bundled fixes:` in your output."
   If a particular task should run without the carve-out (e.g. a
   high-blast-radius migration), omit the authorization line; the
   implementer defaults to no-carve-out and routes everything to
   "Out of scope observed".

3. **Persist each report and update state.** For each returning
   subagent, write its markdown report to disk, then run

   ```
   loop-cohort.py worktree record docs/specs/<feature> <task-id> \
     --status {ready|blocked|failed} --report <path>
   ```

   The tool:
   1. Parses the report's opening `## Task <task-id>` heading and
      checks it matches the `<task-id>` argument. Mismatched or missing
      heading exits non-zero — never silently writing under an
      unvalidated name.
   2. Copies the report verbatim to
      `docs/specs/<feature>/notes/implementer-<task-id>-<iteration>.md`,
      where `<iteration>` is the current `state.json.implementation_retry_count`
      (Phase-1 field; Phase-2 may introduce a dedicated counter).
      On a fresh loop the value is `0`, so the first attempt lands as
      `…-0.md`; subsequent re-plans see the counter bumped (see step 4
      below) so reports never overwrite one another.
   3. Atomically updates the matching `state.json.worktrees[i]` entry:
      sets `status` and `report_path`.

   The match-first / write-second / state-update-last ordering is the
   tool's invariant; a crash between steps 2 and 3 leaves a recoverable
   signal — the report file exists, the entry still says
   `in-progress`, and the next supervisor session's pre-flight surfaces
   it as stale scratch.

4. **Handle non-ready tasks first.** Inspect `loop-cohort worktree list
   docs/specs/<feature>`. If any entry shows `blocked` or `failed`, do
   not merge. Surface the failed-task list (with `report_path`
   pointers), then return to PLAN and revise the offending task. The
   next supervisor pass's `worktree record` call (or `review record`
   on the surrounding loop) will bump `implementation_retry_count`, so report
   filenames won't collide. Do not redispatch the same implementer on
   the same task — the assumption that produced the failure is what
   needs revising, not the attempt.

5. **Merge ready tasks sequentially.** From the primary worktree, run

   ```
   loop-cohort.py worktree merge docs/specs/<feature>
   ```

   The tool sorts ready entries in task-id order and runs
   `git merge --no-ff <branch>` for each. A conflict means the tasks
   weren't actually independent — the tool runs `git merge --abort`,
   exits non-zero, and names the offending task ID. Return to PLAN and
   fix the `Depends on:` declarations.

   **Lift `Bundled fixes:` into the PR body.** Each implementer report
   may carry a `Bundled fixes:` section listing ride-alongs landed
   under the carve-out. After merge succeeds, collect those lines
   from every ready report, dedupe by exact-string match (falling
   back to operator judgment when two lines describe the same change
   in different words), and emit a single `Bundled fixes:` section
   in the PR description below the standard template. If no
   implementer landed ride-alongs, omit the section.

6. **Clean up worktrees.** After all merges succeed, run

   ```
   loop-cohort.py worktree cleanup docs/specs/<feature>
   ```

   The tool runs `git worktree remove` for each entry, retries once
   with `--force` on failure, and leaves stuck directories in place
   with their paths on stderr (exit 2). Surface those in your
   end-of-loop summary, but don't block on cleanup — the loop should
   still proceed to gates. Worktree entries in `state.json.worktrees`
   keep their terminal status for the rest of the loop so the next
   reader can reconstruct what each task did.

7. **Run gates yourself** (next phase in the parent SKILL). The
   implementers' gate results were advisory; the gates of record run
   in the primary against the merged state.

## Parallel-dispatch discipline

Both EXECUTE fan-out (supervisor mode) and REVIEW fan-out share these rules:

- Issue all subagent invocations in a single message (one Agent use per target).
  Do not call sequentially.
- Barrier-wait: don't issue follow-on Agent calls until every subagent in the
  round has returned.
- Timeout, tool error, or missing report = `failed` for that target. Same as
  substantive failure; don't retry silently.
- EXECUTE fan-out: merge implementer results in your own context. REVIEW
  fan-out: persist each raw report, classify it with `review raw-classify`,
  adjudicate by path every one that is not footer-free `clean`, and merge only the
  sustained main-loop results; never read N raw reviewer reports into the
  controller to aggregate them. Persistence is unconditional — a fan-out round
  where every reviewer returned clean still leaves one artifact per reviewer.

## Phase 1 supervisor procedure

Read `loop-cohort status docs/specs/<feature> --json` for
`current_wave_index` and `schedule_waves[current_wave_index]` to get the active
task set. (`schedule` runs once during the G-plan sequence and persists the
wave list; re-calling it resets `current_wave_index` to 0, erasing prior `wave
advance` progress.) Dispatch `implementer` tasks sequentially — **parallel fan-out
(`dispatch-decision`, `worktree`, `auto-parallel`) is disabled in Phase 1**;
those verbs exit non-zero. After all wave tasks are done, fire `wave-complete`
before proceeding to GATES:

```
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> wave-complete
```

## Single-agent fallback

If no `implementer`-matching subagent is installed in the consumer's
IDE, drop back to single-agent mode: execute the independent tasks
yourself, sequentially, in task-id order. Note the degradation in the
final summary so the user sees the loop ran without implementer dispatch.
The missing capability is the subagent, not parallelism — the installed path
is sequential too.

## Cross-references

- `state.json.worktrees` field shape: see
  [`state-schema.md`](state-schema.md).
- Tool verb surface: `loop-cohort.py --help` (script at
  [`../scripts/loop-cohort.py`](../scripts/loop-cohort.py)).
- Rationale, boundary, motivations: see
  this reference's own § Why a separate mode, and its boundary (in this repo;
  in other repos, the adopter's own conventions doc).

## Why a separate mode, and its boundary

**Supervisor mode is wave-scheduled and sequential in Phase 1.** The
work-loop builds the plan's full `Depends on:` DAG (`loop-cohort schedule`) and
dispatches plan tasks in topological order with one `implementer` at a time —
failing loud on a cycle and warning on a forward-reference. Parallel
`implementer` fan-out (`dispatch-decision`, `worktree`, `auto-parallel`) is
**disabled in Phase 1** — those verbs exit non-zero without touching
`state.json`. The design intent for opt-in parallel fan-out and the step-by-step
worktree procedure live in the `work-loop` skill §EXECUTE and
`references/supervisor-mode.md`. This section is the why and the boundary.

**Why a separate mode instead of a separate skill.** The trigger is
structural (the plan's shape), not a choice the user makes. Branching
inside `work-loop` means contributors never pick the wrong skill, and
the 80% overlap with single-agent flow stays single-sourced.

**Why an implementer subagent, not a recursive work-loop.** The
implementer's job is narrow — build one task, run gates, report.
Reviewing, dispatch decisions, and merge belong to the supervisor. A
recursive work-loop would let an implementer spawn its own
implementers; that's nested coordination overhead with no clear win.
Keep the tree two levels deep: supervisor → leaf implementers.

**Worktrees as the coordination primitive.** Each independent task gets
`.worktrees/<task-id>/` checked out on its own branch
(`<base-branch>-<task-id>`). Worktrees are git-native, support parallel
checkout of the same repo, and avoid lockfile contention. The directory
is gitignored ([`.gitignore`](../.gitignore)); branches live in git
history for traceability.

**Merge discipline.** The supervisor merges with `git merge --no-ff
<base>-<task-id>` into the primary branch, **sequentially in task-id
order**. The procedure file
(`references/supervisor-mode.md` in the `work-loop` skill)
has the executable form (including how to order non-numeric IDs). If a
sequential merge conflicts, the tasks weren't actually independent —
the plan was wrong. Surface that as a PLAN-level escalation, not a
`git mergetool` session.

**Gates run in the primary, not the worktree.** Each implementer runs
gates inside its worktree and reports the result, but those results are
**advisory**. The supervisor reruns lint / typecheck / tests against
the merged state — that's the only signal that counts.

**Escalating implementer failures.** If an implementer reports
`blocked` or `failed`, the supervisor surfaces the failure list to a
human and returns to PLAN. It does **not** redispatch the same
implementer on the same task — the assumption that produced the
failure is what needs revising, not the attempt.

**Known limitation.** The procedure has been validated by prose
walk-through, not by an executed end-to-end dry-run. Any change to
**pre-flight (procedure step 0)**, **worktree creation (step 1)**,
**report persistence ordering (step 3)**, **merge order (step 5)**,
**cleanup recovery (step 6)**, or the **`state.json` `worktrees`
schema** must perform an actual `git worktree add` + parallel-dispatch
round against a throwaway spec before merging — read-only walk-through
is not sufficient for those surfaces. Step numbers refer to the
procedure at `references/supervisor-mode.md` in the `work-loop` skill.
