# Resolve-vs-surface disposition: catalogue small cleanups

Opened at PLAN on 2026-08-10.

## Pre-execution dispositions

- Defer `catalogue-gate-b-no-local-target`: pre-execution review showed that a
  safe workflow-derived filesystem replayer needs unsupported-statement and
  path-confinement tests and therefore is not a mechanical light-mode ride-along.
  It remains in `[backlog].open`.
- Apply `plugin-pages-yml-parity-disposition`: unresolved prose disposition;
  correct the existing scope reason without widening the workflow roster.
- Resolve `plugin-fixture-continuation-indent` as stale metadata: Ruff 0.15.17
  preserves the current equal indentation and rewrites the proposed deeper
  continuation indentation. The user confirmed removing its backlog block while
  leaving source untouched.
- Resolve `ruff-excludes-the-engine-build-package` as stale metadata: local
  `main` already uses the root-anchored `/build` exclusion and explicitly keeps
  the shipped engine build package in Ruff scope. Remove only the backlog block;
  Ruff configuration and engine code remain excluded from implementation.
- Defer `profiles-agents-normative-pointer`: changing the published authoring
  scaffold requires a package version bump and scaffold synchronization, beyond
  the confirmed cleanup boundary. It remains in `[backlog].open`.
- Exclude every item named in the user request, including the already shipped
  Ruff and catalogue-test-carve-out work.

## Review dispositions

- Blocker 1 (wrong light-mode selection): applied by deferring Gate B and
  collapsing the two remaining edits into one independent mechanical task.
- Blocker 2 (Gate B safety behavior untested): resolved by deferring the item;
  no replayer lands in this branch.
- Blocker 3 (vacuous checks): the parity half is applied through a direct
  disposition-content assertion; the fixture half is superseded by resolving
  only its stale backlog metadata.
- Blocker 4 (non-runnable commands): applied by naming the checked-in `.agents`
  skill-script paths.
- Concern 5 (spec index not tied to AC): applied as AC4 with an explicit index
  status check.
- Re-review Blocker 1 (fixture bytes not directly verified): superseded by the
  Ruff probe and final decision to remove only the stale
  `plugin-fixture-continuation-indent` backlog metadata while leaving the
  Ruff-canonical source untouched; no fixture-byte claim remains in the spec.
- Re-review Blocker 2 (backlog preservation not directly verified): applied by
  comparing parsed open-backlog slug sets against local `main` and requiring an
  exact removal set.
- Pre-execution probe after clean review: scope narrowed again because Ruff
  proved the fixture item is stale/misdescribed; user then confirmed removing
  its backlog metadata while keeping source untouched.

Final amended-scope review: Clean — ready to commit.

## Implementation review

Single bounded light-mode pass: Clean — ready to commit.

No implementation-review findings required apply/defer routing.

## Verification

- Direct `WORKFLOW_SCOPE["pages.yml"]` content assertion: passed.
- Parsed `[backlog].open` delta against local `main`: exactly
  `plugin-pages-yml-parity-disposition` and
  `plugin-fixture-continuation-indent` plus
  `ruff-excludes-the-engine-build-package` removed; no additions.
- `python3 tools/test-lint-ci-parity.py`: 99/99 cases passed.
- `make lint-ruff`: passed.
- `python3 -m agentbundle catalogue verify --root .`: passed.
- `make build-check`: complete; every policy, SAST, SCA, and Semgrep leg ran and
  passed. Existing warn-only spec-reference diagnostics remain unchanged.
- After the final stale Ruff queue reconciliation, the exact three-slug delta,
  spec metadata lint, full workspace reconciliation, and `git diff --check`
  passed; no Ruff configuration or source file changed.

## Learning capture

No durable knowledge entry added. The formatter-specific stale-backlog finding
is recorded in this spec and is not broad enough to change repository doctrine.
