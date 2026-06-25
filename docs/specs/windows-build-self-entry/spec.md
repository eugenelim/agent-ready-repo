# Spec: First-class cross-platform build-self entry (port the fixture guard)

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Mode:** light — evaluated the destructive-operation trigger: this strengthens
  an existing guard and is behavior-preserving on the real-write refusal path;
  the inner destructive function (`run_self_host`) and its dirty-tree+`--force`
  protection are untouched.

## Objective

`build-self` overwrites the working tree. Its guard against pointing
`--packs-dir` into `tests/fixtures/` (which would overwrite the tree with
fixture data) lives **only in Makefile bash** (`@case … ALLOW_FIXTURE_PACKS …`).
On Windows there is no `make`, so the only way to run build-self —
`python -m agentbundle.build self` — bypasses that guard entirely. Port the
guard into the CLI handler (`cmd_self`) so the cross-platform invocation is
safe, and remove the now-redundant Makefile bash guard so it is single-sourced.

## Acceptance Criteria

- [x] AC1: A real-write `cmd_self` invocation (`--packs-dir` under
  `tests/fixtures/`, no `--dry-run`, `ALLOW_FIXTURE_PACKS` unset) refuses with a
  clear stderr message and a non-zero exit, and does **not** call `run_self_host`.
- [x] AC2: The guard is bypassed when `ALLOW_FIXTURE_PACKS` is set, on
  `--dry-run` (non-destructive), and for a non-fixtures `--packs-dir` — matching
  the historical Makefile semantics. Path matching is Windows-safe (`as_posix`).
- [x] AC3: The guard lives in the CLI handler (`cmd_self`), not `run_self_host`,
  so existing tests that drive `run_self_host` directly against fixture packs
  are unaffected.
- [x] AC4: The redundant Makefile bash guard is removed; `make build-self`
  real-write still refuses a fixtures `PACKS_DIR` (now via the Python guard),
  and `make build-check` stays green.
- [x] AC5: `python -m agentbundle.build self --packs-dir packs` is documented as
  the make-free (Windows) entry in `docs/architecture/agentbundle.md`.

## Tasks

1. Add a pure `_refuse_fixture_packs_dir(packs_dir, *, dry_run) -> int | None`
   helper to `self_host.py` and call it at the top of `cmd_self` before
   `run_self_host`.
2. Remove the `@case … esac` bash guard from the Makefile `build-self` target.
3. Document the cross-platform invocation in `docs/architecture/agentbundle.md`.
4. Tests: the helper's four branches (refuse / env-override / dry-run /
   non-fixtures) + a `cmd_self` wiring test that the guard fires and
   `run_self_host` is not called.

## Declined

- Tempted to add a `--allow-fixture-packs` CLI flag; declining — `ALLOW_FIXTURE_PACKS`
  is the existing override and no second caller needs a flag.
- Tempted to put the guard in `run_self_host`; declining — tests drive that
  function directly against fixtures with `force=True`, and the guard is a
  CLI-entry concern (where the Makefile equivalent lived).
- Tempted to guard `--dry-run` too; declining — dry-run writes to a shadow temp
  dir (non-destructive), matching the existing dirty-tree guard's `not dry_run`
  condition; the only behavior delta is `make build-self DRY_RUN=1` on a
  fixtures dir now proceeding harmlessly.
