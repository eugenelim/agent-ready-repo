# Supervisor mode — procedure

Loaded on demand by the `work-loop` skill when the plan has **two or
more tasks declaring `Depends on: none`**. The trigger and concept stay
in [`../SKILL.md` § EXECUTE](../SKILL.md); this file owns the
step-by-step procedure once the branch fires.

Throughout this procedure, **"task-id order" means numeric where IDs
look like `T1`, `T2`, … ; lexicographic otherwise.**

The parallel-dispatch discipline (one-message-one-Agent-call-per-target,
barrier-wait, treat harness-level non-returns as failures, merge results
in your own context) is the same as for REVIEW fan-out and lives in
the parent `SKILL.md` body. References to "the parallel-dispatch
discipline" below mean that section.

## The procedure

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
   discipline (see parent SKILL body). Each brief includes: the task
   ID, the plan-task body, the worktree path, and paths to the spec +
   plan.

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
      if it doesn't yet exist.
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
   (with `report_path` pointers), **increment
   `state.json.iteration_count`** so the next attempt's report
   filename won't collide with this one's, then return to PLAN and
   revise the offending task. Do not redispatch the same implementer
   on the same task — the assumption that produced the failure is
   what needs revising, not the attempt.

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
- Rationale, boundary, motivations: see
  `docs/CONVENTIONS.md § Supervisor mode` (in this repo;
  in other repos, the adopter's own conventions doc).
