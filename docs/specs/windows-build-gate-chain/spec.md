# Spec: Make-free cross-platform self-host gate chain

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Contract:** none
- **Shape:** service
- **Mode:** full — risk triggers fire: a structural change (a new repo-native
  tool plus a Makefile/CI rewire that reroutes the self-host gate targets). The
  chain is *not* added to the published `agentbundle` package CLI — it lives in
  `tools/`, because it orchestrates repo-only gates (see Objective).

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A Windows contributor regenerating or verifying the self-host projection runs
the **whole gate chain in one command**, without `make` and without invoking
bash. `python tools/build_gate_chain.py build-self` chains lint-packs → self;
`python tools/build_gate_chain.py build-check` chains lint-packs → build →
check → pre-pr-catalogue → the projected `lint-spec-status` and `brief-coverage`
gates — the same steps in the same order as the corresponding Makefile targets.
Each chain stops at the first failing step and exits non-zero with that step's
code, so a failure is as legible as a failed `make` target. The chain logic is
single-sourced: the `Makefile` `build-self` and `build-check` targets route
through this script rather than re-listing the steps, so the two surfaces cannot
drift. The script runs Python-native steps in-process by calling the existing
`cmd_lint_packs` / `cmd_build` / `cmd_check` / `cmd_self` handlers, and
out-of-process steps (pre-pr-catalogue, the projected skill linters) by spawning
`sys.executable` — never bash, never a shell. It self-inserts
`packages/agentbundle` on `sys.path` and `chdir`s to the repo root, so it is one
command with no environment setup, run from anywhere.

The script lives in `tools/`, a sibling of `tools/pre-pr-catalogue.py`, and is
**deliberately not a subcommand of the published `agentbundle` package**:
`build-check` spawns repo-only scripts (`tools/pre-pr-catalogue.py` and the
projected `.claude/skills/.../*.py` linters) that never ship to adopters, so the
chain is meaningless — and would crash — in a `pip install agentbundle`
consumer's tree. The reusable engine (`lint-packs` / `build` / `check` / `self`)
stays in the package as public subcommands; only the repo-specific *wiring*
lives here. Keeping it out of the package leaves the published CLI surface
unchanged.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Reuse the existing gate handlers (`cmd_lint_packs`, `cmd_build`, `cmd_check`,
  `cmd_self`) and the `tools/pre-pr-catalogue.py` entry — call them, never
  reimplement their logic.
- Apply the leg-inclusion discriminator: a Makefile gate step belongs **inside**
  a chaining subcommand if and only if it is Windows-clean (pure Python, no
  shell/bash) **and** unconditional. A conditional, tool-gated, or
  platform-specific leg (today: SAST/Semgrep) stays Makefile-appended after the
  subcommand. This rule governs the next leg added, not just today's set.
- Spawn child Python processes with `sys.executable` and a `pathlib`-built
  script path, so the chain runs identically on Windows, macOS, and Linux.
- Stop at the first non-zero step and propagate that step's exit code as the
  chain's exit code.
- Honor the existing `ALLOW_FIXTURE_PACKS` override and the fixture-overwrite
  guard already in `cmd_self` (the `build-self` chain reaches `self` through
  `cmd_self`, so the guard fires unchanged).

### Ask first

- Adding any gate step the Makefile targets do not run, or removing a Windows-
  clean step they do run.
- Changing the meaning, name, or default of an existing build subcommand or its
  flags.

### Never do

- **No new third-party dependency** — pure stdlib (`argparse`, `subprocess`,
  `sys`, `pathlib`).
- **No bash, `sh`, `.sh` shelling, or shell=True** — and no POSIX-only path
  assumptions (no hardcoded `/` separators; build paths with `pathlib`).
- Do not pull the SAST leg into the subcommands — Semgrep has no Windows
  support and the leg is conditional and tool-gated; it stays Makefile-only.
- Do not reimplement, fork, or copy any gate's logic into the new script.
- **Do not add the chain to the shipped `agentbundle` package CLI** (no new
  `python -m agentbundle.build` subcommand) — it orchestrates repo-only gates
  and would be dead/broken surface for adopters; it lives in `tools/`.
- No new top-level directory.

## Testing Strategy

- **Chain ordering and first-failure short-circuit (TDD).** The load-bearing
  invariant is "run these steps, in this order, stop at the first failure,
  return its code." It is a compressible invariant over a step list, verified by
  driving the chain with stubbed step outcomes and asserting on the recorded
  call order and returned exit code. Unit level.
- **CLI wiring (goal-based check).** That `build-self` and `build-check` parse
  and dispatch to the chain handlers is verified by constructing the parser and
  asserting `func` resolves — a one-shot check, not a behavior with an
  invariant.
- **End-to-end real invocation (manual QA).** Because this ships a command a
  user invokes, the built artifact is exercised end-to-end: run `python
  tools/build_gate_chain.py build-check` and `... build-self --dry-run` on a
  clean tree and confirm the observed exit code and step output match `make
  build-check` / `make build-self DRY_RUN=1`. Recorded in the plan's
  verification notes.

## Acceptance Criteria

- [x] AC1: `python tools/build_gate_chain.py build-self` runs, in order,
  `lint-packs` then `self` (via `cmd_lint_packs` then `cmd_self`), passing
  through `--dry-run`, `--force`, and `--packs-dir`. Same steps, order, and flags
  as `make build-self`, plus the `--no-symlink` pass-through the `self`
  subcommand already supports. The `self` step is invoked with `output_dir="."`
  (the working tree, matching the `self` subparser default).
- [x] AC2: `python tools/build_gate_chain.py build-check` runs, in order,
  `lint-packs` → `build` → `check` → `tools/pre-pr-catalogue.py` →
  `lint-spec-status` self-test + lint → `brief-coverage` self-test + lint —
  i.e. every Windows-clean step `make build-check` runs, in the same order. It
  does **not** run the SAST leg. The `build` step receives `--packs-dir` and an
  `--output-dir` (default `dist`, the artifact dir, overridable to preserve the
  Makefile's `OUTPUT_DIR`); the `check` step projects against the working tree
  (`output_dir="."`).
- [x] AC3: Each chain stops at the first step that exits non-zero and returns
  that step's exit code; later steps do not run after a failure.
- [x] AC4: The chain's **own** process spawning uses pure stdlib and never
  invokes bash, `sh`, a `.sh` script, or `shell=True`: out-of-process steps are
  spawned via `[sys.executable, <pathlib path>]`. (The Windows-cleanliness of the
  spawned scripts themselves — `pre-pr-catalogue.py` and the projected linters —
  is the predecessor gates' responsibility, not re-verified here.)
- [x] AC5: The `Makefile` `build-self`, `build-self-dry-run`, and `build-check`
  targets route through `tools/build_gate_chain.py` (the steps are listed once,
  in the script); the SAST leg remains appended after the `build-check` target's
  script call in the Makefile, preserving `SKIP_SAST` and its run-last ordering.
- [x] AC6: The `build-self` chain honors the `ALLOW_FIXTURE_PACKS` override and
  the `tests/fixtures/` overwrite guard (inherited from `cmd_self`, unchanged).
- [x] AC7: `python tools/build_gate_chain.py build-check` run on a clean tree
  exits 0 and its observed step output matches `make build-check` (SAST aside);
  the cross-platform entry is documented in `docs/architecture/agentbundle.md`.
- [x] AC8: The published `agentbundle` package CLI is unchanged — `python -m
  agentbundle.build --help` lists no `build-self` / `build-check` subcommand, and
  no agentbundle version bump is required. The chain is invoked only via
  `tools/build_gate_chain.py`.

## Assumptions

- Technical: runtime is Python ≥3.11; package `agentbundle` 0.8.0 (source: `packages/agentbundle/pyproject.toml`)
- Technical: CLI entry is `python -m agentbundle.build` → `main()`; handlers `cmd_lint_packs`/`cmd_build`/`cmd_check`/`cmd_self` exist and are wired in `_build_parser` (source: `agentbundle/build/__init__.py`, `main.py`, `self_host.py`, `lint_packs.py`)
- Technical: hyphenated subcommand names parse cleanly in argparse (source: probe `python -c "...add_parser('build-check')..."` → `ok build-check`)
- Technical: the fixture-overwrite guard + `ALLOW_FIXTURE_PACKS` already live in `cmd_self` via `_refuse_fixture_packs_dir`; predecessor spec shipped it (source: `agentbundle/build/self_host.py:1518`, `docs/specs/windows-build-self-entry/spec.md`)
- Technical: `make build-check` chains lint-packs → build → check → pre-pr-catalogue → lint-spec-status pair → brief-coverage pair → SAST(conditional); `make build-self` chains lint-packs → self (source: `Makefile`)
- Technical: the SAST leg is Linux/macOS-only (Semgrep no Windows support), conditional via `SKIP_SAST`, and tool-gated (source: `Makefile` SAST comments)
- Process: `make build-check` runs no package pytest; CI wires each test path explicitly in `build-check.yml` (source: `.github/workflows/build-check.yml`)
- Process: this work is full mode — new public CLI surface + structural build-entrypoint change (source: `work-loop` risk triggers)
- Product: the users are Windows contributors to this repo, not PyPI/adopter end users — the command is a repo-dev gate run from repo root (source: scope decision 2026-06-25)
- Process: the `build-check` chain includes the Windows-clean `lint-spec-status`/`brief-coverage` projected-script pairs (beyond the brief's named handler set) for behavioral identity with `make build-check`; SAST is the only excluded leg (source: user confirmation 2026-06-25)
- Process: the chain is a repo-native `tools/` script, NOT a subcommand on the shipped `agentbundle` package CLI — `build-check` spawns repo-only scripts that never reach adopters, so a package subcommand would be dead/broken surface; this keeps the published CLI unchanged and needs no release (source: user confirmation 2026-06-25 — "don't just change the adopter surface without explicitly surfacing")
