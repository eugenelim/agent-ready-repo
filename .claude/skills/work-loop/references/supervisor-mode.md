# Supervisor mode — procedure

**Default is sequential.** Supervisor mode computes the plan's full
`Depends on:` DAG (`loop-cohort schedule <spec-dir>`) and runs tasks in
**topological order, single-agent, on every adapter** — it does *not*
auto-fan-out. `schedule` also fails loud on a dependency cycle or a
forward-reference (a task whose declared dep is authored later), so an
ill-formed plan is caught at PLAN, not run out of order.

This file owns the **opt-in parallel-write path** only. It is entered
deliberately — never automatically — and only for a wave that clears the
**dispatch gate**, which has two halves checked at two points:

- **Category half — auto-derived from the diff.** You **don't hand-classify**:
  omit `--category` and `dispatch-decision` derives each task's category from
  its branch's committed diff, fail-closed (only an all-added, no-danger-path
  diff is `cannot-collide`; rename/delete, danger-paths, modified-existing, and
  cross-branch basename/dir collisions all serialize). Pass `--category` only
  to **override** — the sole way to assert `typed-group-b`, which is never
  auto-derived (deciding a change is type-shaped isn't fail-closed-mechanizable).
- **Disjointness half — on populated branches.** A clean `git merge-tree`
  file-disjointness check is only meaningful once the implementers have
  written and committed, so it is enforced at the **merge** step (step 5's
  `git merge --no-ff` aborts on any collision — the loud backstop). Run
  `loop-cohort dispatch-decision --branch <b> …` (categories auto-derived) as a
  read-only **preview** of that check (it classifies each branch + runs
  `wave_is_disjoint`, printing `parallel` or `serial`) before paying for a
  merge you expect to abort.
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

The parallel-dispatch discipline (one-message-one-Agent-call-per-target,
barrier-wait, treat harness-level non-returns as failures, merge results
in your own context) is the same as for REVIEW fan-out and lives in
the parent `SKILL.md` body. References to "the parallel-dispatch
discipline" below mean that section.

Every state mutation — worktree creation, report persistence, status
updates, merges, cleanup — is owned by the `loop-cohort` tool at
`../scripts/loop-cohort.py`. The tool guarantees the match-first /
write-second / state-update-last ordering and atomic JSON writes; do
not edit `state.json` or invoke `git worktree` directly.

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

2. **Dispatch implementers in parallel** per the parallel-dispatch
   discipline (see parent SKILL body). Each brief includes: the task
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
      where `<iteration>` is the current `state.json.iteration_count`.
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
   on the surrounding loop) will bump `iteration_count`, so report
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

## Single-agent fallback

If no `implementer`-matching subagent is installed in the consumer's
IDE, drop back to single-agent mode: execute the independent tasks
yourself, sequentially, in task-id order. Note the degradation in the
final summary so the user sees the loop ran without parallelism.

## Cross-references

- `state.json.worktrees` field shape: see
  [`state-schema.md`](state-schema.md).
- Tool verb surface: `loop-cohort.py --help` (script at
  [`../scripts/loop-cohort.py`](../scripts/loop-cohort.py)).
- Rationale, boundary, motivations: see
  `docs/CONVENTIONS.md § Supervisor mode` (in this repo;
  in other repos, the adopter's own conventions doc).
