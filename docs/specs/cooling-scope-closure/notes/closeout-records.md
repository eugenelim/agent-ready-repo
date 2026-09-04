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

Observed on 2026-09-03: the in-tree RFC-0096 §9 range (from `## 9. Initiative waves` to before `## 10. Risks and revisit conditions`) was 2861 bytes and SHA-256 `e49f49f12fc7dccff4cd962cecff7be003672283d8a750097a238001b222a45e`, equal to the pinned constant. On a scratch copy outside the repository tree, changing byte offset 15534—the `I` of `Initiative` in the section heading—to `i` changed one byte and produced SHA-256 `a94a9a7c0a7cea65deced5b2f764aacb6b1987b758ca33538ef62ae0fa8dadbf`. The mutated copy does not equal the pin, so the mutation is detected.

The plan's table states every row as an obligation whose "named test is
confirmed red". AC28's row cannot meet that literally: it mutates a scratch copy
outside the repository tree, while `test_ac28_...` digests the in-tree RFC and
reads nothing else, so no permitted application reaches the assertion.

It is discharged instead by showing the mutated scratch copy's §9 byte-range
digest differs from the pinned constant
`e49f49f12fc7dccff4cd962cecff7be003672283d8a750097a238001b222a45e`. The plan is
sealed, so the row's wording stands and this note records the real method.

## AC31's recorded class

The plan's verdict table records AC31 as `no stub (mode)`, and a test exists. The
test is kept, narrowed to what no other gate pins: that the `[core]` changelog
heading is dated, and that the version clears the floor. Its two equality
assertions were dropped because `tests/conformance/test_pack_metadata.py` already
pins pack↔plugin agreement and
`tests/roster/test_security_checklists_okf_projection.py` already pins
pack↔topmost-`[core]`. The class deviation is recorded here rather than by
amending the sealed plan.
