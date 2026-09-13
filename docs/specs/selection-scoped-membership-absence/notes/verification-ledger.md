# Verification ledger — selection-scoped membership absence

Execution observations for the Wave 7c slice 1 delivery. The spec and plan are
approved and pinned; anything learned by running the work is recorded here.

Commit under test: `198560b2d`. Date: 2026-09-13.

## T5 required gates

| Gate | Result |
| --- | --- |
| `lint-contract-item-alignment.py` on this spec | exit 0 — 1 spec checked, 0 skipped |
| `lint-spec-status.py --root .` | exit 0 |
| `pytest tests/roster/test_selection_scoped_membership_absence.py` | exit 0 — 31 passed |
| `make build-self` | exit 0; re-run on a clean tree writes nothing, so the projection is idempotent |
| `make bootstrap-sites` | exit 0 |
| `make build-check` | exit 0 — "every leg of this target was invoked, SAST/SCA included" |
| `make test` | **not green locally** — environmental, see *Dispositions* |

Projection byte-identity was checked directly rather than inferred: the pack
source, both adapter projections, and the packaged runtime copy under
`packages/agentbundle/` are identical.

## End-to-end evidence

A fixture repository with one registered spec and one unregistered spec, both
passed to the shipped command in one invocation.

- Exit code 0.
- `present-spec` → `membership_present: true`, one occurrence carrying
  `initiative`, `collection`, `entry_index`, and `form: "canonical"`.
- `absent-spec` → `membership_present: false`, no occurrences.
- Results returned in the order supplied.
- Fixture digest identical before and after the run, so the read-only promise
  holds in a real invocation and not only under test.

An earlier attempt used an entry missing `summary`. The command reported it as
`form: "parse-blocked"` rather than absent, which is the intended behaviour: a
matching but malformed entry must not read as absence.

## Defects found while gating

Two were caught by remote CI after the local chain reported the work ready.

**`zip()` without an explicit `strict=`.** Selectors and resolved artifact
paths are one-to-one by construction, so a length mismatch is a defect. The
loose form truncates to the shorter sequence and returns fewer results than
selectors were supplied — the exact failure the ordering criterion exists to
prevent. Fixed to fail loudly.

**One loop variable reused across three loops over three membership types.**
Canonical, legacy, and parse-blocked bind different types, and one of them
lacks an attribute the others carry. Each loop now has its own name.

## Dispositions

**`make test` — environmental, not a code failure.** It stops at
`lint-editable-install`: an editable install of `agentbundle` points at a peer
worktree, so every worktree imports that checkout's code. The guard's preferred
remedy is `pip uninstall -y agentbundle`, which repairs every worktree at once.
It was not run here because a peer session was executing gates at the time, and
the guard states that changing this pointer mid-run kills a peer's gates.

Evidence accepted in its place, on the same commit: remote `test-corpus`, which
runs `make test` in an environment with no stale editable, completed
successfully. Remote `build-check` (all four gates) and `test-roster` also
passed. The roster run collected 1447 passed plus 6 skipped against 1453
collected locally, so the new suite was included rather than skipped.

Owner decision, 2026-09-13: accept the remote result for this leg and close on
the remaining gates.

**Semgrep timeout — load, not a finding.** The local SAST leg failed once on a
timeout in `loop-cohort.py`, a file outside this changeset, at load 35.5 on 10
CPUs. `gate-sast` then passed on quiet CI runners twice, and a later local
`make build-check` passed with SAST included. No exclusion was added.

## Recorded for the plan's owner

The plan's required-local-gate list omits `lint-ruff` and `lint-mypy`. Both
live in `make ci`, not in `make build-check`, so following the list exactly
would have shipped both defects above. The repository's own build-command
reference also omits them. This delivery ran the superset. Correcting the list
is an amendment, not an edit, because the plan is pinned.

Type errors in pack engine code cannot surface before `make build-self` runs:
mypy checks typed packages, `packs/` is not one, and the engine reaches mypy
only through its generated copy under `packages/agentbundle/`. Both mypy
findings cited the generated copy, never the file that was edited.
