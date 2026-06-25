# Plan: Make-free cross-platform self-host gate chain

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done --> (T1–T4 all complete)

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Add one new module, `agentbundle/build/gate_chains.py`, holding two argparse
handlers — `cmd_build_self` and `cmd_build_check` — and a tiny generic chain
runner `_run_chain(steps)`. A *step* is a `(label, thunk)` pair where `thunk`
is a zero-arg callable returning an `int` exit code; `_run_chain` runs them in
order, stops at the first non-zero, prints a `✖ <label>` line to stderr, and
returns that code. In-process steps wrap the existing handlers — `thunk =
lambda: cmd_lint_packs(ns)` etc., where `ns` is an `argparse.Namespace` carrying
exactly the attributes that handler reads. Out-of-process steps
(`tools/pre-pr-catalogue.py`, the projected `lint-spec-status` /
`brief-coverage` self-test+lint scripts) wrap a `_run_script` helper that spawns
`[sys.executable, str(Path(*parts))]` via `subprocess.run(..., check=False)` —
`pathlib`-built path, no shell, no bash. The riskiest part is *fidelity*: the
two chains must list the same steps in the same order as the Makefile targets;
the Makefile is then rewritten to call the subcommands so the lists exist once.
SAST stays appended in the Makefile after the `build-check` subcommand (Semgrep
is Windows-incompatible and tool-gated), preserving `SKIP_SAST` and run-last
order.

## Constraints

- No prior ADR/RFC governs this; it is the direct follow-on to the shipped
  `windows-build-self-entry` spec (which ported the fixture guard into
  `cmd_self`). This spec chains the steps that spec left to manual ordering.
- AGENTS.md *Keeping changes minimal* and the spec's Boundaries: pure stdlib,
  no new dependency, no reimplemented gate logic, no bash.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** run `python -m agentbundle.build build-check` and
`python -m agentbundle.build build-self --dry-run` on a clean tree; confirm exit
0 and that the step sequence/output matches `make build-check` and
`make build-self DRY_RUN=1` (AC7).

**Recorded AC7 run (2026-06-25, `PYTHONPATH=packages/agentbundle`, clean tree):**
- `python -m agentbundle.build build-self --dry-run --packs-dir packs` → **exit 0**;
  emitted the `[info] unclassified: …` dry-run projection report (lint-packs
  silent-pass then `self --dry-run`), matching `make build-self DRY_RUN=1`.
- `python -m agentbundle.build build-check --packs-dir packs --output-dir dist`
  → **exit 0**; ran lint-packs, build, check, then `pre-pr: ✓ …` for every
  catalogue linter, `test-lint-spec-status: all invariant cases pass.` +
  `lint-spec-status: spec metadata clean.` (with the pre-existing warn-only
  invariant-(iii) warnings on other specs), and `test-lint-brief-coverage: all
  cases pass.` — i.e. the full `make build-check` sequence minus the
  SAST leg, which by design stays Makefile-appended.

## Design (LLD)

### Design decisions

- **Two subcommands, named 1:1 with the Makefile targets** (`build-self`,
  `build-check`), not one overloaded `self --check`. Rejected the single-flag
  shape: `build-self` *writes* the projection while `build-check` is a
  read-only verify chain that additionally runs build + pre-pr + linters —
  conflating them behind a flag hides the write/verify distinction. Traces to:
  AC1, AC2.
- **`(label, thunk)` step list + generic `_run_chain`.** Separates the *what/
  order* (the per-chain step list) from the *how* (sequential, first-failure,
  code-propagating run), so the short-circuit invariant is tested once against
  synthetic steps. Rejected inlining a sequence of `if rc: return rc` blocks
  per chain — that duplicates the short-circuit logic and is harder to test.
  Traces to: AC3.
- **In-process for packaged handlers, subprocess only for repo scripts.** The
  four handlers live in the package and are called directly (no process
  spawn); only `tools/pre-pr-catalogue.py` and the projected skill linters —
  repo-relative scripts not importable as package modules — are spawned, via
  `sys.executable`. Traces to: AC4.

### Interfaces & contracts

- New CLI surface on `python -m agentbundle.build`: subcommands `build-self`
  (`--dry-run`, `--force`, `--no-symlink`, `--packs-dir`) and `build-check`
  (`--packs-dir`, `--output-dir` default `dist`). Wired in `_build_parser`
  (`agentbundle/build/__init__.py`), `set_defaults(func=cmd_build_self |
  cmd_build_check)`. `build-check`'s `--output-dir` feeds the **build (dist)
  leg only** — it preserves the Makefile's `OUTPUT_DIR` override; the `check`
  leg always projects against the working tree (`output_dir="."`). Traces to:
  AC1, AC2, AC4.
- No data contract; stdlib only. Traces to: AC4.

### Failure, edge cases & resilience

- First non-zero step short-circuits; its code is the chain's code (AC3).
- `build-self` reaches `self` through `cmd_self`, so `_refuse_fixture_packs_dir`
  + `ALLOW_FIXTURE_PACKS` fire unchanged — no new guard, no bypass (AC6).
- A repo script missing on disk (e.g. run outside the repo root): `sys.executable`
  exists, so `subprocess.run([sys.executable, "<missing>.py"], check=False)`
  launches the interpreter, which prints `can't open file ...` and exits
  non-zero. That non-zero returncode flows back as the step's code, the chain
  prints its `✖ <label>` line and stops (AC3 holds). `check=False` means no
  exception is raised for the script's failure; a genuine `FileNotFoundError`
  would only arise if `sys.executable` itself were missing, which does not
  happen. Verified by the missing-script test in T1.

### Quality attributes (NFRs)

- Windows-clean (AC4): no bash/`sh`/`.sh`/`shell=True`, paths via `pathlib`.
  Verified by a test that asserts the assembled argv lists start with
  `sys.executable` and contain no shell tokens, plus source-level review.

## Tasks

### T1: chain runner + two handlers in `gate_chains.py`

**Depends on:** none

**Tests:** (TDD — `packages/agentbundle/agentbundle/build/tests/test_gate_chains.py`)
- `_run_chain` runs steps in order and returns 0 when all return 0 (records
  call order). Verifies AC3 (happy path).
- `_run_chain` stops at the first step returning non-zero, does **not** run
  later steps, and returns that exact code. Verifies AC3.
- `cmd_build_self(ns)` assembles steps `["lint-packs", "self"]` in that order
  and threads `--dry-run`/`--force`/`--no-symlink`/`--packs-dir` into the
  namespaces passed to `cmd_lint_packs`/`cmd_self`; the `lint-packs` namespace
  carries `packs_dir`, the `self` namespace carries
  `packs_dir`+`output_dir="."`+`dry_run`/`force`/`no_symlink` (monkeypatch both
  in the module namespace, record the `args` each received and assert these
  attributes are present). Verifies AC1, AC6.
- `cmd_build_check(ns)` assembles steps `["lint-packs","build","check",
  "pre-pr-catalogue","test-lint-spec-status","lint-spec-status",
  "test-lint-brief-coverage","lint-brief-coverage"]` in that order; the
  `lint-packs` namespace carries `packs_dir`; the `build` namespace carries
  `packs_dir`+`output_dir`(from `args.output_dir`)+`recipe=None`+`pack=None`;
  the `check` namespace carries `packs_dir`+`output_dir="."`; no SAST step is
  present. Verifies AC2. (Asserting every consumed attribute is present guards
  the AttributeError class the reviewer flagged.)
- The five script steps build argv `[sys.executable, <pathlib path>]` with no
  shell token and `check=False` (monkeypatch `subprocess.run`, assert argv[0]
  is `sys.executable` and no entry is `bash`/`sh`/`-c`). Verifies AC4.
- A `_script_step` whose path does not exist returns a non-zero code and the
  chain prints its `✖ <label>` line and stops (drive `_run_chain` with a real
  `subprocess.run` against a `<tmp>/nope.py`; assert non-zero + later steps not
  run). Verifies AC3 on the missing-script edge.

**Approach:**
- New module imports `cmd_lint_packs` (lint_packs), `cmd_build` (main),
  `cmd_check`/`cmd_self` (self_host) — cycle-free (none import this module).
- `_run_chain(steps: list[tuple[str, Callable[[], int]]]) -> int`.
- `_handler_step(label, func, **ns_kwargs)` → `(label, lambda: int(func(Namespace(**ns_kwargs))))`. Each call site passes **every** attribute the target handler reads (`packs_dir` for all; `output_dir` for build/check/self; `recipe`/`pack` for build; `dry_run`/`force`/`no_symlink` for self).
- `_script_step(label, *path_parts)` → `(label, lambda: subprocess.run([sys.executable, str(Path(*path_parts))], check=False).returncode)`.
- `cmd_build_self(args)` and `cmd_build_check(args)` build their lists and
  `return _run_chain(...)`.

**Done when:** `test_gate_chains.py` is green.

### T2: wire `build-self` / `build-check` subcommands into the parser

**Depends on:** T1

**Tests:** (goal-based)
- `_build_parser().parse_args(["build-self"]).func is cmd_build_self` and
  `... ["build-check"]).func is cmd_build_check` (add to existing parser test or
  `test_gate_chains.py`). Verifies AC1, AC2 wiring.

**Approach:**
- In `agentbundle/build/__init__.py` `_build_parser`, add two `add_parser`
  blocks. `build-self`: `--dry-run`/`--force` (`store_true`), `--no-symlink`
  (`store_true`), `--packs-dir` (default `packs`). `build-check`: `--packs-dir`
  (default `packs`), `--output-dir` (default `dist`, feeds the build leg only).
  `set_defaults(func=...)`. Import the two handlers.

**Done when:** the parse-args assertions pass and `python -m agentbundle.build
build-check --help` prints help.

### T3: route the Makefile targets through the subcommands

**Depends on:** T1, T2

**Tests:** (manual QA / goal-based)
- `make build-self DRY_RUN=1` and `make build-check` run to the same outcome as
  before (exit 0 on a clean tree). Verifies AC5, AC7.
- `grep` confirms the `build-self`/`build-check` recipes call
  `agentbundle.build build-self|build-check` and that **no chained step survives
  outside the subcommand** — the recipes no longer name `check`,
  `pre-pr-catalogue`, `lint-spec-status`, or `lint-brief-coverage` directly
  (only the SAST leg remains after `build-check`). This grep is the durable
  anti-drift gate complementing AC7's recorded manual run. Verifies AC5.

**Approach:**
- Rewrite `build-self`: `$(PYTHON) -m agentbundle.build build-self
  --packs-dir $(PACKS_DIR)` plus the `DRY_RUN`/`FORCE` flag mapping
  (`--dry-run`/`--force`). Drop the `lint-packs` prereq (now in the subcommand).
- Rewrite `build-check`: `$(PYTHON) -m agentbundle.build build-check
  --packs-dir $(PACKS_DIR)` then the existing conditional SAST block
  (`SKIP_SAST` → skip / `$(MAKE) sast`) unchanged. Drop the now-duplicated
  `check`/`pre-pr`/`lint-spec-status`/`brief-coverage` lines and the
  `lint-packs build` prereqs.
- Keep `build-self-dry-run`, `build`, `pre-pr`, `sast` targets as-is.

**Done when:** both targets pass on a clean tree and the recipe bodies delegate.

### T4: docs, changelog, README, CI test wiring

**Depends on:** T1, T2, T3

**Tests:** (goal-based)
- `make build-check` green (drift gates + projection).
- CI step added: `python -m pytest agentbundle/build/tests/test_gate_chains.py`
  in `build-check.yml` (the suite gates — `make build-check` runs no pytest).

**Approach:**
- `docs/architecture/agentbundle.md` § Self-host overlay: document `python -m
  agentbundle.build build-self` / `build-check` as the make-free, one-command
  Windows entry (replacing/extending the existing single-command note). AC7.
- `docs/product/changelog.md` `[Unreleased] > Added`: one entry for the two new
  subcommands.
- `packages/agentbundle/README.md`: add the two subcommands to the build-CLI
  surface if it enumerates subcommands.
- Add the explicit pytest path to `.github/workflows/build-check.yml` next to
  the sibling self-host wiring (`test_self_host_fixture_guard.py`).
- Consider an `agentbundle` version bump + changelog under release decision
  (surface to user, do not auto-cut).

**Done when:** `make build-check` green, CI step present, docs/changelog updated.

## Rollout

- **Delivery:** additive, big-bang, fully reversible (delete the module + parser
  blocks + revert Makefile). No flag. No data migration, no published event.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** none — ships in one PR.

## Risks

- **Fidelity drift between subcommand and Makefile.** Mitigated by routing the
  Makefile through the subcommands (the step list exists once) and by AC7's
  end-to-end parity check.
- **Repo-relative script paths.** The subcommands assume cwd = repo root (same
  as `cmd_self`/`cmd_check` and the Makefile). Acceptable for a repo-dev gate;
  documented in the spec's Failure section.

## Changelog

- 2026-06-25: initial plan.
- 2026-06-25: pre-EXECUTE review fixes (thread every consumed namespace
  attribute; add `--output-dir` to `build-check`; discriminator → Boundaries;
  missing-script edge test; AC4 scoped to the chain's own spawning).
- 2026-06-25: implemented T1–T4; Status → Done; recorded AC7 run.
