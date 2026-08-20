# Plan: Confine activation-eval runs to a projection outside the repository

- **Status:** Shipped
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files touched:** `packages/agentbundle/agentbundle/commands/pack_evals.py`;
`tools/test-run-pack-evals.py`. Nothing else.

**Tests that demonstrate done:** a new test capturing the cwd handed to the detector and
asserting it is outside `repo_root.resolve()` (AC1); a test asserting the projection path is
gone after the call returns (AC3); a test asserting `stdin` reaches `subprocess.run` (AC5);
and the 22 existing tests in `tools/test-run-pack-evals.py` passing unmodified — including the
five that assert `.eval-workspace/...` output paths (AC2) and those that inject
`project_root` (AC4).

**Not changing:** `EVAL_WORKSPACE`'s value or location; the `summary.json` schema; the CI
artifact path; either `.gitignore`; what the evals measure; the `project_root` seam's
semantics.

## Declined — tempted, and why not

- **Move `.eval-workspace/` itself outside the repo.** Would fix the symptom too, but breaks
  `.github/workflows/pack-evals.yml`'s `.eval-workspace/**/summary.json` artifact path and
  both `.gitignore` entries, and contradicts the shipped AC that wants the workspace
  *repo-relative*. The workspace was never the problem — the run cwd was.
- **`git init` the projection so repo-root discovery stops there.** Clever and small, but it
  only defeats git-based root discovery; a skill resolving a root by marker file or by
  `os.getcwd()` walk-up still escapes. Confinement by location is the honest fix.
- **Tighten `--allowed-tools` to deny writes.** Cannot work: once `Skill` is allowed, the
  dispatched skill's own writes go through. It would also change what the eval measures.
- **Add a post-run stray-file detector that fails the run.** Detects the damage after it has
  been done to the user's tree, and would have to encode a list of paths skills might write.
- **Fix the `new-adr` eval query that triggered it** (`"Spec out the rate-limiting feature"`).
  That query is a legitimate negative case and should stay; the harness must be safe for any
  query, including ones authors add later.

## Tasks

1. **Projection moves to a temp dir outside the repo.** (AC1, AC3, AC4)
   *Tests:* `test_projection_runs_outside_the_repository` — recording fake detector, no
   `project_root`, assert captured cwd is not `repo_root.resolve()` and not relative to it;
   `test_projection_is_cleaned_up` — assert the captured projection path does not exist after
   the call. Red against `iter_dir / ".projection"`.
   *Approach:* create the projection under `tempfile.mkdtemp()` (or a
   `TemporaryDirectory` bound to the run's lifetime), project into it, use it as `run_cwd`,
   and remove it in a `finally` so an exception mid-run still cleans up. Leave the
   `project_root` branch untouched.

2. **`stdin=subprocess.DEVNULL` on the detector's `subprocess.run`.** (AC5)
   *Tests:* `test_run_and_parse_passes_devnull_stdin` — monkeypatch `subprocess.run`, assert
   the `stdin` kwarg is `subprocess.DEVNULL`.
   *Approach:* one kwarg. Same function, same concern (invocation hygiene) — a bundled
   ride-along on the confinement fix, and the thing that made the timeout worse.

3. **Verify the untouched surfaces.** (AC2, AC6, AC7)
   *Done when:* `git diff --stat` names neither `.github/workflows/pack-evals.yml` nor any
   `.gitignore`; `python3 tools/test-run-pack-evals.py` passes; `packages/agentbundle/tests/`
   passes; `make build-check` passes with SAST.
   *no stub (goal-based)*

## Risks

- **The three other call sites** (`_next_iteration(pack_workspace)` at lines ~664, ~811, ~938
  — the in-harness and judge modes) may construct their own projection the same way. If they
  do, the same fix applies there; if they do not project at all, they are out of scope. Check
  before assuming.
- **Windows temp semantics**: `tempfile` is stdlib and portable, but cleanup of a directory
  a subprocess still holds open can fail on Windows. Prefer best-effort removal
  (`ignore_errors`) over an exception that fails an otherwise-good measurement run.
