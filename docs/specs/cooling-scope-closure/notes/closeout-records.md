# Records closeout reads

Three items the spec's Durable Outputs or the plan's mutation table point at,
which have no other durable home.

## `project-knowledge`: not applicable — no reusable learning

The spec's Durable Outputs row admits exactly two outcomes: the gate's receipt,
or an explicit not-applicable finding. This is the finding.

Nothing in this delivery generalises past it. The two derivations it merges are
this repository's own `workspace_status.py`; the cooled-set semantics are Wave
5's, consumed unchanged; and the one transferable lesson — that two consumers of
the same question must read one derivation — is already written into the spec's
Objective and into RFC-0096's erratum, which are the surfaces a reader reaches.
A knowledge topic restating it would be a second home for a fact that already
has one.

The session's genuinely reusable observations are about gate topology rather
than this feature, and belong to the repository's own guidance rather than a
project-knowledge topic:

- `make build-check` does not chain `make lint-ruff`; `make ci` composes
  `build-check lint-ruff lint-mypy test-after-build-check`.
- No Python gate reaches `web/`'s vitest suite, and that suite cannot run in a
  worktree that has not had `make bootstrap-sites`.
- Remote Gate A-packs runs a curated suite list; `packs/core/tests/skills/new-spec/`
  is in no remote job, so a failure there is invisible to CI.

The third is registered in `workspace.toml [backlog].open` as
`pre-existing-new-spec-exact-clean-phrase-drift`.

## AC28's mutation row: how it is discharged

The plan's table states every row as an obligation whose "named test is
confirmed red". AC28's row cannot meet that literally: it mutates a scratch copy
outside the repository tree, while `test_ac28_...` digests the in-tree RFC and
reads nothing else, so no permitted application reaches the assertion.

It is discharged instead by showing the mutated scratch copy's §9 byte-range
digest differs from the pinned constant
`e49f49f12fc7dccff4cd962cecff7be003672283d8a750097a238001b222a45e`. This note
recorded the real method because the plan was sealed when AC28 was discharged.
The 2026-09-01 amendment reopened the plan, but the row's wording still stands:
the mutation table records a discharged row where it was discharged, and moving
this one would rewrite history the amendment is required to preserve.

## AC31's recorded class

The plan's verdict table records AC31 as `no stub (mode)`, and a test exists. The
test is kept, narrowed to what no other gate pins: that the `[core]` changelog
heading is dated, and that the version clears the floor. Its two equality
assertions were dropped because `tests/conformance/test_pack_metadata.py` already
pins pack↔plugin agreement and
`tests/roster/test_security_checklists_okf_projection.py` already pins
pack↔topmost-`[core]`. The class deviation was recorded here rather than in the
plan because the plan was sealed at the time.

The 2026-09-01 amendment supersedes the narrowing this section records. AC31 now
states datedness as a failure condition rather than a description, fixes the
topmost-heading selection so a heading naming a second artifact is not skipped,
and is discharged by T9 after T8's release edit rather than by T8. Read this
section as the pre-amendment state; the amended criterion governs.
