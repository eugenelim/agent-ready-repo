# Plan: Make-free cross-platform self-host gate chain

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done --> (T1–T4 all complete)

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Add one new **repo-native** script, `tools/build_gate_chain.py` (a sibling of
`tools/pre-pr-catalogue.py`), with two subcommands — `build-self` and
`build-check` — and a tiny generic chain runner `_run_chain(steps)`. A *step* is
a `(label, thunk)` pair where `thunk` is a zero-arg callable returning an `int`
exit code; `_run_chain` runs them in order, stops at the first non-zero, prints
a `✖ <label>` line to stderr, and returns that code. In-process steps wrap the
existing package handlers — `_handler_step("lint-packs", cmd_lint_packs, …)` —
where the namespace carries exactly the attributes that handler reads.
Out-of-process steps (`tools/pre-pr-catalogue.py`, the projected
`lint-spec-status` / `brief-coverage` self-test+lint scripts) wrap a
`_script_step` helper that spawns `[sys.executable, str(Path(*parts))]` via
`subprocess.run(..., check=False)` — `pathlib`-built path, no shell, no bash.
The script self-inserts `packages/agentbundle` on `sys.path` and `chdir`s to the
repo root in `main`, so it imports the handlers and resolves repo-relative paths
with no environment setup, from any cwd.

**It is a `tools/` script, not an `agentbundle` package subcommand**, because
`build-check` spawns repo-only scripts that never ship to adopters — a package
subcommand would be dead/broken surface in a consumer's tree and would expand
the published CLI for no one. The reusable engine (`lint-packs` / `build` /
`check` / `self`) stays in the package; only the repo-specific wiring lives
here. The riskiest part is *fidelity*: the two chains must list the same steps
in the same order as the Makefile targets; the Makefile is then rewritten to
call the script so the lists exist once. SAST stays appended in the Makefile
after the `build-check` target's script call (Semgrep is Windows-incompatible
and tool-gated), preserving `SKIP_SAST` and run-last order.

## Constraints

- No prior ADR/RFC governs this; it is the direct follow-on to the shipped
  `windows-build-self-entry` spec (which ported the fixture guard into
  `cmd_self`). This spec chains the steps that spec left to manual ordering.
- AGENTS.md *Keeping changes minimal* and the spec's Boundaries: pure stdlib,
  no new dependency, no reimplemented gate logic, no bash.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** run `python tools/build_gate_chain.py build-check` and
`python tools/build_gate_chain.py build-self --dry-run` on a clean tree; confirm
exit 0 and that the step sequence/output matches `make build-check` and
`make build-self DRY_RUN=1` (AC7).

**Recorded AC7 run (2026-06-25, clean tree, no `PYTHONPATH` set — the script
self-bootstraps):**
- `python tools/build_gate_chain.py build-self --dry-run` (run from `/tmp` to
  prove cwd-independence) → **exit 0**; emitted the `[info] unclassified: …`
  dry-run projection report (lint-packs silent-pass then `self --dry-run`),
  matching `make build-self DRY_RUN=1`.
- `python tools/build_gate_chain.py build-check` → **exit 0**: lint-packs,
  build, check, then `pre-pr: ✓ …` for every catalogue linter,
  `test-lint-spec-status: all invariant cases pass.` + `lint-spec-status: spec
  metadata clean.` (with the pre-existing warn-only invariant-(iii) warnings on
  other specs), and `test-lint-brief-coverage: all cases pass.` — i.e. the full
  `make build-check` sequence minus the SAST leg.

## Design (LLD)

### Design decisions

- **Repo-native `tools/` script, not a package subcommand.** `build-check`
  spawns repo-only scripts (`tools/pre-pr-catalogue.py`, the projected skill
  linters) that never ship to adopters, so it is meaningless and would crash in
  a `pip install agentbundle` tree; putting it in the package would expand the
  published CLI surface (forcing a release) for surface no adopter can use.
  Rejected the package-subcommand shape from the original brief for exactly this
  reason. The script is a sibling of `tools/pre-pr-catalogue.py` — the same
  established pattern (a repo-native, Windows-runnable Python orchestrator the
  Makefile calls). Traces to: AC8.
- **One script, two subcommands** (`build-self` / `build-check`), not two files.
  They share `_run_chain` / `_handler_step` / `_script_step`; two files would
  duplicate the runner or need a third shared module. Traces to: AC1, AC2.
- **`(label, thunk)` step list + generic `_run_chain`.** Separates the *what/
  order* (the per-chain step list) from the *how* (sequential, first-failure,
  code-propagating run), so the short-circuit invariant is tested once against
  synthetic steps. Rejected inlining a sequence of `if rc: return rc` blocks
  per chain — that duplicates the short-circuit logic and is harder to test.
  Traces to: AC3.
- **In-process for packaged handlers, subprocess only for repo scripts.** The
  four handlers are imported from the package and called directly (no process
  spawn); only `tools/pre-pr-catalogue.py` and the projected skill linters —
  repo-relative scripts — are spawned, via `sys.executable`. Traces to: AC4.

### Interfaces & contracts

- New repo-tool CLI: `python tools/build_gate_chain.py build-self` (`--dry-run`,
  `--force`, `--no-symlink`, `--packs-dir`) and `... build-check` (`--packs-dir`,
  `--output-dir` default `dist`). Argparse subparsers in the script's
  `_build_parser`, `set_defaults(func=build_self | build_check)`. `build-check`'s
  `--output-dir` feeds the **build (dist) leg only** — it preserves the
  Makefile's `OUTPUT_DIR` override; the `check` leg always projects against the
  working tree (`output_dir="."`). The published `agentbundle` package CLI is
  **unchanged**. Traces to: AC1, AC2, AC4, AC8.
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

### T1: chain runner + two subcommands in `tools/build_gate_chain.py`

**Depends on:** none

**Tests:** (TDD — `tools/test_build_gate_chain.py`)
- `_run_chain` runs steps in order and returns 0 when all return 0 (records
  call order). Verifies AC3 (happy path).
- `_run_chain` stops at the first step returning non-zero, does **not** run
  later steps, returns that exact code, **and** prints a `✖ <label>` stderr line
  naming the failing label and its code (capture via `redirect_stderr`).
  Verifies AC3 + failure legibility.
- `build_self(ns)` assembles steps `["lint-packs", "self"]` in that order and
  threads `--dry-run`/`--force`/`--no-symlink`/`--packs-dir` into the namespaces
  passed to `cmd_lint_packs`/`cmd_self`; the `lint-packs` namespace carries
  `packs_dir`, the `self` namespace carries
  `packs_dir`+`output_dir="."`+`dry_run`/`force`/`no_symlink` (monkeypatch both
  in the module, record the `args` each received and assert these attributes are
  present). Verifies AC1, AC6.
- `build_check(ns)` assembles steps `["lint-packs","build","check",
  "pre-pr-catalogue","test-lint-spec-status","lint-spec-status",
  "test-lint-brief-coverage","lint-brief-coverage"]` in that order; the
  `lint-packs` namespace carries `packs_dir`; the `build` namespace carries
  `packs_dir`+`output_dir`(from `args.output_dir`)+`recipe=None`+`pack=None`;
  the `check` namespace carries `packs_dir`+`output_dir="."`; no SAST step is
  present. Verifies AC2.
- The five script steps build argv `[sys.executable, <pathlib path>]` with no
  shell token and `check=False`. Verifies AC4.
- A `_script_step` whose path does not exist returns `rc == 2` (interpreter
  can't-open-file) and the chain stops. Verifies AC3 on the missing-script edge.
- `_build_parser().parse_args(["build-self"]).func is build_self` and `…
  ["build-check"]).func is build_check`; `build-check` `--output-dir` defaults
  `dist`. Verifies AC1, AC2 wiring.

**Approach:**
- New `tools/build_gate_chain.py`: `REPO_ROOT = Path(__file__).resolve().parent.parent`;
  `sys.path.insert(0, REPO_ROOT/"packages"/"agentbundle")`; import
  `cmd_lint_packs`/`cmd_build`/`cmd_check`/`cmd_self`.
- `_run_chain`, `_handler_step(label, func, **ns_kwargs)` (passes **every**
  attribute the handler reads), `_script_step(label, *parts)`.
- `build_self`/`build_check` assemble lists and `return _run_chain(...)`;
  `_build_parser` wires the two subcommands; `main` does `os.chdir(REPO_ROOT)`
  then dispatches.

**Done when:** `python tools/test_build_gate_chain.py` is green.

### T2: revert the package CLI surface

**Depends on:** none

**Tests:** (goal-based)
- `python -m agentbundle.build --help` lists no `build-self`/`build-check`;
  full `agentbundle/build/tests/` suite still green. Verifies AC8.

**Approach:**
- Delete the earlier `packages/agentbundle/agentbundle/build/gate_chains.py` and
  its test; remove the two `add_parser` blocks + import from
  `agentbundle/build/__init__.py`, restoring the package CLI to its `main`
  state. No version bump.

**Done when:** the package diff vs `main` is empty except for nothing — the
package is untouched.

### T3: route the Makefile targets through the script

**Depends on:** T1

**Tests:** (manual QA / goal-based)
- `make build-self DRY_RUN=1` and `make build-check` run to exit 0 on a clean
  tree. Verifies AC5, AC7.
- `grep` confirms the `build-self`/`build-self-dry-run`/`build-check` recipes
  call `tools/build_gate_chain.py` and **no chained step survives outside the
  script** — the recipes no longer name `check`, `pre-pr-catalogue`,
  `lint-spec-status`, or `lint-brief-coverage` directly (only the SAST leg
  remains after `build-check`). Durable anti-drift gate. Verifies AC5.

**Approach:**
- Rewrite `build-self`, `build-self-dry-run`, `build-check` to call
  `$(PYTHON) tools/build_gate_chain.py build-self|build-check …`; keep the
  `DRY_RUN`/`FORCE` flag mapping and the conditional SAST block appended after
  the `build-check` script call. Drop the old `lint-packs build` prereqs.
- Keep `build`, `pre-pr`, `sast` targets as-is.

**Done when:** both targets pass on a clean tree and the recipe bodies delegate.

### T4: docs + CI test wiring

**Depends on:** T1, T3

**Tests:** (goal-based)
- `make build-check` green (drift gates + projection).
- CI step added: `python -m pytest tools/test_build_gate_chain.py` in
  `build-check.yml` (the suite gates — `make build-check` runs no pytest).

**Approach:**
- `docs/architecture/agentbundle.md` § Self-host overlay: document `python
  tools/build_gate_chain.py build-self` / `build-check` as the make-free,
  one-command Windows entry, and why it lives in `tools/`. AC7.
- `.github/workflows/build-check.yml`: wire the tools test path explicitly.
- **No changelog entry and no `packages/agentbundle/README.md` change** — the
  shipped package is untouched, so there is no adopter-visible change to record.

**Done when:** `make build-check` green, CI step present, docs updated.

## Rollout

- **Delivery:** additive, big-bang, fully reversible (delete the `tools/`
  script + revert Makefile/CI/docs). No flag, no data migration, no published
  event. **No package change → no release.**
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** none — ships in one PR.

## Risks

- **Fidelity drift between the script and the Makefile.** Mitigated by routing
  the Makefile through the script (the step list exists once) and by AC7's
  end-to-end parity check + the T3 anti-drift grep.
- **Repo-relative script paths.** The script `chdir`s to the repo root computed
  from `__file__`, so cwd-independence is handled; it assumes the standard repo
  layout (a sibling of `tools/pre-pr-catalogue.py`). Acceptable for a repo-dev
  gate; documented in the spec's Failure section.

## Changelog

- 2026-06-25: initial plan.
- 2026-06-25: pre-EXECUTE review fixes (thread every consumed namespace
  attribute; add `--output-dir` to `build-check`; discriminator → Boundaries;
  missing-script edge test; AC4 scoped to the chain's own spawning).
- 2026-06-25: implemented T1–T4; Status → Done; recorded AC7 run.
- 2026-06-25: **moved the chain from a package subcommand to a repo-native
  `tools/build_gate_chain.py` script** (reviewer/user: `build-check` orchestrates
  repo-only gates, so it doesn't belong on the published `agentbundle` CLI — that
  was an unsurfaced adopter-surface change). Package CLI reverted to its `main`
  state; no version bump; changelog entry dropped (no adopter-visible change).
  Tasks/ACs reworked accordingly (AC8 added).
