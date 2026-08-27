# Spec: Confine activation-eval runs to a projection outside the repository

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none — this corrects implementation drift from
  [`docs/specs/pack-activation-evals/spec.md`](../pack-activation-evals/spec.md) AC (line 210)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** tool

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

**Mode:** full — the *security boundary* risk trigger fires (file I/O; this change is
specifically about write confinement). The `loop-engine`/`loop-cohort` state machine is
**not** run: it mandates two human approval gates, and the maintainer's instruction was to
fix the defect in this session. Full-mode rigor is delivered as ACs + testing strategy +
security review + adversarial review to clean + full regression.

## Objective

`agentbundle pack evals run` writes into the host repository it is measuring. A *negative*
eval query — `"Spec out the rate-limiting feature"` in `new-adr`'s
`eval_queries.json` — fired the `new-spec` skill, which created
`docs/specs/rate-limiting/spec.md` **at the worktree root** during a measurement run.

This is not litter. In this repository a spec appearing under `docs/specs/<slug>/` with no
`workspace.toml` entry registers as workspace drift, so the harness can manufacture phantom
governance artifacts with no author.

**The correct behaviour is already specified.** Three places say the projection must be an
ephemeral temp dir distinct from the persistent eval-workspace:

- `packages/agentbundle/agentbundle/commands/pack_evals.py:52-53` — its own comment:
  "Distinct from the ephemeral temp dir a pack is *projected* into for discovery"
- `docs/specs/pack-activation-evals/spec.md:210` (Shipped) — "**distinct from the isolated
  temp dir the pack is *projected* into for discovery** (the projection is ephemeral; the
  eval-workspace persists across passes)"
- `docs/specs/pack-activation-evals/plan.md:96,107` — "`.eval-workspace/<pack>/` #
  repo-relative, gitignored (**NOT the temp projection dir**)"

The implementation instead sets the projection to `iter_dir / ".projection"` — inside
`.eval-workspace`, inside the repository — so `run_cwd` is a repo subdirectory. A dispatched
skill that resolves the repository root (which `new-spec` does deliberately) walks up from
that cwd, finds the host repo, and writes there.

This spec closes the drift. It does **not** change where results are stored.

## Acceptance Criteria

- [x] **AC1 — the run cwd is outside the repository.** When `run_pack_evals` performs its own
  projection (`project_root` not supplied), the directory passed to
  `detector.run_and_parse(..., cwd, ...)` is not `repo_root` and is not a descendant of
  `repo_root`. Verified by a test that supplies a recording fake detector, runs without
  `project_root`, and asserts the captured cwd is outside `repo_root.resolve()`.
- [x] **AC2 — outputs are unchanged and stay repo-relative.** `.eval-workspace/<pack>/
  iteration-<N>/` continues to hold `<skill>/<query-id>/with_skill/run-<r>/outputs/result.txt`
  and `summary.json`, rooted at `repo_root`. `EVAL_WORKSPACE` keeps the value
  `".eval-workspace"`. The existing output-path tests
  (`tools/test-run-pack-evals.py` lines ~286, 348, 381, 666, 684) pass unmodified.
- [x] **AC3 — the projection is cleaned up.** The temp projection is removed when the run
  ends, including on exception, so repeated runs do not accumulate projections on disk.
  Verified by a test asserting the captured projection path no longer exists after the call
  returns.
- [x] **AC4 — the `project_root` injection seam is preserved.** When a caller supplies
  `project_root`, that path is used as the run cwd verbatim and no projection or temp dir is
  created. The existing tests that pass `project_root=repo_root` keep passing unmodified.
- [x] **AC5 — no `stdin` stall.** `ClaudeCodeDetector.run_and_parse` passes
  `stdin=subprocess.DEVNULL` to `subprocess.run`, so each invocation stops emitting
  "Warning: no stdin data received in 3s, proceeding without it" and stops paying a flat
  3-second penalty that also pushes runs toward the timeout. Verified by a test asserting the
  `stdin` kwarg reaches `subprocess.run`.
- [x] **AC6 — CI and ignore surfaces untouched.** `.github/workflows/pack-evals.yml`'s
  artifact path `.eval-workspace/**/summary.json` and the `.gitignore` entry
  `.eval-workspace/` are unchanged, and `packs/core/seeds/.gitignore` is not modified by this
  change. Verified by `git diff --stat` naming neither file.
- [x] **AC8 — the confinement cannot be defeated by `TMPDIR`.** `tempfile.mkdtemp()` honours
  `TMPDIR`, so an operator or CI system whose `TMPDIR` points inside the repository would put
  the projection back inside it and restore the leak. Verified empirically: with `TMPDIR` set
  under a fake repo root, `mkdtemp()` returns a path inside that root. `run_eval` therefore
  resolves the candidate projection path and **refuses before projecting** if it is at or
  below `repo_root.resolve()`, with an error naming `TMPDIR` and the repository path. A
  confinement control that silently degrades is worse than none, so this fails loudly rather
  than falling back to another location. Verified by a test that points the temp directory
  beneath the fake repo and asserts the refusal happens before `detector.project()` is called.
- [x] **AC9 — cleanup failure is observable.** `shutil.rmtree(..., ignore_errors=True)` must
  not mask a retained projection: when the directory still exists after removal, the harness
  emits a warning to stderr naming the path. It must not raise, because that would mask an
  otherwise-good measurement result. (The directory is mode 0700 — verified — so a retained
  projection is a cleanup and observability issue, not an exposure one.)
- [x] **AC10 — the security claim is scoped honestly.** The code comment and the test's `✓`
  line describe the protection as *against cwd- and ancestor-based repository discovery*, not
  as OS-level write confinement. The subprocess is not sandboxed and retains the invoking
  user's filesystem access; a skill that locates the repo by explicit path, environment, or
  filesystem search is out of this control's scope and the prose must not imply otherwise.
- [x] **AC7 — gates green.** `python3 tools/test-run-pack-evals.py` passes, the full
  `packages/agentbundle/tests/` suite passes, and `make build-check` passes with SAST.

## Boundaries

**In scope:** `packages/agentbundle/agentbundle/commands/pack_evals.py` (projection location
and the `stdin` kwarg) and `tools/test-run-pack-evals.py` (new tests).

**Out of scope:** moving `.eval-workspace` itself; the `summary.json` schema; the in-harness
and judge modes' own workspace handling beyond the shared projection change; any change to
what the evals measure; `packs/core/seeds/.gitignore`.

## Testing strategy

**TDD** — the invariant is compressible ("the run cwd is not inside the repo") and the module
already exposes the seam: `tools/test-run-pack-evals.py` injects a fake detector whose
`run_and_parse(query, cwd, timeout)` receives the cwd. The existing fake's `project()` raises,
because every current test supplies `project_root` to skip projection; the new tests need a
fake whose `project()` records its `output_root` and succeeds, and which accepts the
`catalogue_root` keyword the real call site passes.

Red first: AC1's assertion fails against today's `iter_dir / ".projection"`.
