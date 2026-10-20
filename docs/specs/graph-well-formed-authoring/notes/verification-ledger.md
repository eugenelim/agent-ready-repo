# Verification ledger: graph well-formed authoring

Evidence for each task, bound to the commit that carries it.

## T1: Changed-artifact pointer fixtures pass

- **Suite:** `packs/core/tests/skills/work-loop/test_lint_graph_pointers.py` — 49 passed in 110 s (Python 3.13, macOS, 2026-10-20). Covers VI-1001, VI-1002, and VI-1003.
- **Local gate:** `make lint-ruff lint-mypy` passed.
- **Real repository:** `lint-graph-pointers.py --root . --base-ref origin/main` printed `0 violation(s) in 1 selected artifact(s)` and exited 0.
- **Design notes found while building:**
  - `git diff` rewrote `.git/index` on Git 2.50.1 even with optional locks off. The check therefore diffs against a temporary copy of the index, which keeps repository bytes unchanged. A split-index repository refuses with exit 2.
  - Any failed Git command reports `base-unavailable`. `git-unavailable` is kept for a missing Git binary or a timeout.

## T2: Authoring sources and guidance agree on typed emission

- **Writer inventory:** 25 candidates re-derived from the bounded universe and pinned with roles: 4 templates, 2 examples, 12 instructions, 7 excluded with reasons, and no generated copies in these roots. The derived set equals the manifest.
- **Gaps fixed:** 6 sources offered the repository path as a `Brief:` value to write. They are the new-spec template, its skill, its contract reference, the author-delivery-brief skill, the field guide, and the brief template's `Slug:` comment. Two `Parent intent:` comments no longer say "never interpreted".
- **Suite:** `packs/core/tests/skills/work-loop/test_graph_pointer_authoring.py` — 23 passed in 2.3 s. Reverting each fixed file to its pre-T2 version turned the suite red.
- **Suites pinning edited files:** 646 passed and 79 subtests passed, in 258 s.
- **Guide checks:** `validate_guides.py` 0 errors, `lint-guide-titles.py` OK, `lint-guides-no-repo-only-refs.py` OK.
- **Local gate:** `make lint-ruff lint-mypy` passed.
- **Product-engineering:** no source changed, so that pack needs no version bump.

## T3: Shipped and repository invocation paths reject a bad pointer

- **Wiring:** the work-loop finish checklist's "Artifacts consistent" assertion gains a `lint-graph-pointers.py --root . --base-ref <base>` bullet (exit 1 means fix the pointer; exit 2 is not a pass; untouched artifacts are not checked) and a new eval case `finish-graph-pointer-check`. `build_check` registers three steps after `lint-spec-status`: pytest for `test_lint_graph_pointers.py`, pytest for `test_graph_pointer_authoring.py`, and the projected script with `--root . --base-ref origin/main`. The gate-main job checks out with `fetch-depth: 0`, so `origin/main` resolves there. An unresolved base exits 2, which fails the step.
- **Finding while building:** the first wording of the finish bullet named the two pointer fields literally. That made `work-loop/SKILL.md` a new writer candidate and turned the T2 inventory test red. The bullet now says "intent or brief pointer", so the inventory is unchanged.
- **Versions:** core 3.1.10 to 3.1.11 in `pack.toml` and `plugin.json`. Product-engineering is unchanged. Fragment `docs/product/changelog.d/bf0802b2-7eff-4e8c-904d-e09ffc95090f.md` has four outcome-led Highlights.
- **Projections:** `make build-self` and `self-host --write` refuse a dirty tree, and `FORCE` must not be passed from automation. The projection ran in a disposable clone of HEAD with the T3 diff committed there, and the 16 generated files were copied back. `catalogue verify --root .` printed `ok`. `catalogue lint --root . --deep` printed `ok: 77 finding(s)` (info and warn only). `marketplace.json` carries no pack version, so it did not change.
- **VI-3001 proof** (disposable repo `/tmp/vi3001`, base commit holds a typed-free intent, brief and old spec; the new spec adds untyped `Brief:` and `Parent intent:` lines), projected script `.claude/skills/work-loop/scripts/lint-graph-pointers.py --root /tmp/vi3001 --base-ref main`:
  ```
  docs/specs/new/spec.md: Brief: brief-untyped
  docs/specs/new/spec.md: Parent intent: parent-intent-untyped
  lint-graph-pointers: 2 violation(s) in 1 selected artifact(s)
  exit=1
  ```
  The gate's `_script_step` construction against the same repo printed the same lines and returned exit 1. `--base-ref nope` printed `lint-graph-pointers: base-unavailable`, exit 2. Real repo, `--root . --base-ref origin/main`: `0 violation(s) in 1 selected artifact(s)`, exit 0.
- **Suites:** `tools/test_build_gate_chain.py` plus the two pointer suites, 112 passed and 28 subtests in 77 s. Work-loop and pack suites that read `SKILL.md` or `evals.json` (37 files), 1421 passed and 24 subtests in 399 s.
- **Roster:** `tools/lint-ci-parity.py` printed ok for both rosters. No `build-check.yml` step or Makefile suite line changed, so no entry was due.
- **Portable-citation grep:** no match in lines added under `packs/`.
- **Local gate:** `make lint-ruff lint-mypy` passed.

## Revision binding

- T1 is `fba607d84`, T2 is `6cc3d2f65`, and T3 is `03e1a9701`. Review ran on `03e1a9701`.
- After T3, `make build-self` gave a zero diff and `catalogue verify` passed.
- The combined suites passed 112 of 112 on four consecutive runs, in 42–93 s each. One earlier run under heavy machine load had 2 failures that did not reproduce. The likeliest cause is the check's 20 s Git timeout.

## Review

All reviews ran on `03e1a9701`, and every finding was refuted by an independent adjudicator.

- `adversarial-reviewer`: 5 findings, all refuted.
- `security-reviewer`: 3 findings, all refuted.
- `quality-engineer`: 7 findings, all refuted.

## Slice PR CI

Run identifiers are added after the PR opens.

## T4: Repository-level checks pass on the slice PR

- **Trigger:** PR #1582's first CI pass. `docs` run 39481284344 failed `lint-pack-test-boundary.py` on the T2 pins. `test-corpus` run 39481298710 and `build-check` run 39481284362 failed the work-loop finish-checklist hash anchor, and `build-check` stopped there before the pointer steps ran. `test-roster` run 39481305228 and the other 5 PR workflows passed.
- **VI-4001:** the pins moved to `tests/roster/test_graph_pointer_authoring.py` with the same assertions, re-anchored at the repository root. The roster step is in `build-check.yml`, the `STEP_DISPOSITION` and `_GATE_MAIN_CHECKS` entries are in `lint-ci-parity.py`, and the gate-chain step points at the new path.
  - `lint-pack-test-boundary.py` and its self-test: pass.
  - `lint-ci-parity.py`: both rosters ok.
  - `ruff check .`: clean.
  - `tools/test_build_gate_chain.py`: 40 passed in 54 s.
- **VI-4002:** the hash is now `90d06f1c…`, with a review comment citing `workspace_status_engine.py:4988`. The engine is unchanged. The moved suite and `tools/test_workspace_status.py` together: 109 passed in 5 s.
- **VI-4003:** a local `make build-check` ran every chain step through to SAST, and all of them passed, including `lint-graph-pointers` with 0 violations. SAST exited 2 on two Semgrep rule timeouts, in `loop-cohort.py` and `arxiv-retriever.py`. Neither file is in this diff, and the 1-minute load average was 246.8 on 10 CPUs. Re-run alone with the Makefile's arguments, both exit 0. CI delegates SAST to `ci-security`, which passed (run 39481284028).
- **T3 re-verification:** `catalogue verify` ok. The projected check on an untyped `Brief:` exits 1. The repository has 0 violations. Core is at 3.1.11 in both files.
