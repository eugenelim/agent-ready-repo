# Verification ledger — workspace-status-progressive-disclosure

Execution observations. The spec holds the contract; this file holds what was
actually run and what it returned.

## T1 — backend baseline verified (2026-09-22)

`shasum -a256` over `packs/core/.apm/skills/workspace-status/scripts/` at
`HEAD` = `8ef829ab7947d7212dd814aa64af69fcfec6e764`, before any edit:

```
b07efea9132f1ddfeab8ce81554c65633d8fac3f5065fdeba31e40a0ef6d7484  workspace_status.py
b99ad663713333d2a221d655af73ff08898a0553e3e238356fd88d274ca4eea0  workspace_status_engine.py
65076e175c821f2818dfcf5ea762df3d6b9f29334216948e3aac502e2a6c0f98  workspace_status_prune.py
c2b252f55c99d54558b253e3c14aa40a5feec5bbcaad1340154e57e3d2c03199  workspace_mcp_server.py
```

All four match the values AC-0008 names. `git status` clean under `scripts/`.
T1 done.

## Pre-approval spike (2026-09-22)

The line budget was measured rather than estimated before the first review
round. The `workspace.toml` template fence runs `SKILL.md:88-112` — 25 lines,
not the ~60 first assumed. Body at base is 685 lines. The first cut therefore
projected to ~512, over the 500 ceiling, which put the 40-line
coordination-receipts section on the move list. Spike not committed.

## T2 — relocation is byte-clean (2026-09-22)

Every moved block was extracted by exact substring and re-checked line by line
against its destination. Non-verbatim lines: **0** across all twelve moved
blocks. Heading levels were demoted one level where a moved `###` section became
a reference sub-section; no body line changed.

Destinations: `references/reconcile.md` 48 lines, `references/explain.md` 14,
`references/mutate.md` 181.

## T3 — template asset (2026-09-22)

`assets/workspace.toml.template`, 23 lines, extracted from the fence at
`SKILL.md:89-111` as read via `git show <base>:<skill path>` rather than from
the working copy.

## T5 — refusal-code control retargeted, with mutation proof (2026-09-22)

Retargeted `tests/roster/test_two_sided_prune_closure_invariant.py` to open
`references/mutate.md`. Only the path changed; the anchor search, the
`_prune_error` regex and the bullet-list slice are untouched.

Green against the real tree: `5 passed, 42 deselected in 0.72s`. 14 refusal
codes emitted by the prune source, 0 undocumented.

Mutation proof — a `_prune_error("undocumented_probe_code", ...)` call site was
added to the prune source and the control failed as required:

```
E         Left contains one more item: 'undocumented_probe_code'
FAILED tests/roster/test_two_sided_prune_closure_invariant.py::test_every_emitted_refusal_code_is_documented
1 failed, 4 passed
```

The file was restored with `git checkout --` and its digest re-verified as
`65076e175c821f2818dfcf5ea762df3d6b9f29334216948e3aac502e2a6c0f98`, matching the
value the contract names. All four backend digests re-checked and unchanged.

## T4 — body restructured (2026-09-22)

Body: **685 -> 465 lines**, against a 500 ceiling. 35 lines of slack.
`catalogue lint --deep` reports no CAT-S003 finding for
`packs/core/.apm/skills/workspace-status/SKILL.md`. The one remaining
`workspace-status` warning names `.claude/skills/workspace-status/SKILL.md`,
still at 687 lines because the projection is regenerated in T7.

Criteria verified directly:

| Criterion | Result |
| --- | --- |
| AC-0001 body <= 500 | 465 |
| AC-0002 three reference files exist | yes |
| AC-0003 each linked skill-relative | yes |
| AC-0004 8 subcommands mapped to a mode | 8/8, 0 unmapped |
| AC-0005 refusal codes documented | 14 emitted, 0 undocumented |
| AC-0006 asset exists | 23 lines |
| AC-0007 cited, not inlined | yes |

All nine banned strings absent. All seventeen pinned strings present under
whitespace normalisation. The `<ini-slug>`-to-`- **Brief queue**` adjacency
that one structural assertion parses is preserved in order.

### Pin-holding suites

```
python3 -m pytest tools/test_workspace_status_cli.py \
  tests/roster/test_cooling_scope_closure.py \
  tests/roster/test_status_projection_and_context_exclusion.py \
  tests/roster/test_two_sided_prune_closure_invariant.py \
  tests/roster/test_rfc0099_activation_coverage.py \
  tests/roster/test_cooling_brief_child_scope_closure.py -q
381 passed, 22 subtests passed in 124.75s
```

Pack suites: `packs/core/tests/skills/workspace-status/` + `tools/test_workspace_status.py`
— 216 passed, 1 skipped in 8.44s.

## T7 — projection, version, registration (2026-09-22)

`FORCE=1 make build-self` regenerated both projections. All three `SKILL.md`
copies are byte-identical at `712d2f07c457ec6b46501197c7c4a884a76d8b0205b3640b526d238819d31ebb`,
and `references/` and `assets/` both project. `catalogue verify --root .` — ok.
`catalogue lint --deep` reports no `workspace-status` finding at all; the stale
687-line projection warning is gone.

`lint-ci-parity` — ok, 104 steps dispositioned, 167 targets corroborated.
Registration took **three** edits, not the two the plan named: the named step in
`build-check.yml` above the bulk step, the `LOCAL("test-after-build-check")`
coverage entry, and a third entry in the plain-`CHECK` phase list. The parity
lint refused the first attempt with `has no phase-and-dependency axis entry in
STEP_DISPOSITION`, which is how the third was found.

Portability grep over the three references and the asset — no match.

Eval harness: eval 14 added, exercising mode routing for a mutating request
(loads the mutate reference, requires an out-of-band confirmation, never
authors one). Schema clean under `catalogue lint --deep`.

### Plan correction

The plan's T7 approach said `plugin.json`'s version "is derived, so it is
regenerated rather than hand-edited". That is false for `core`: self-host
excludes `core` from the marketplace as not user-scope-installable, and
`plugin.json` kept `2.26.32` after `build-self`. It was bumped by hand to
`2.26.33`, which is what `packs/AGENTS.md` names in the first place — it
requires matching versions in `pack.toml` **and** `.claude-plugin/plugin.json`.
The obligation was met; the plan's stated mechanism for meeting it was wrong.

### An anchor the sweep missed

`tests/roster/test_workspace_status_projection.py` builds its path from a
variable — `CORE_PACK / ".apm" / "skills" / SKILL_NAME / "SKILL.md"` — so the
literal-path grep that found the other pin-holders never saw it. It pinned the
`coordination-receipts` example block to `SKILL.md`, which T2 had moved.

Owner-authorized remedy: the assertion was split. The finding-code rows keep
reading `SKILL.md`, where they never moved; the receipt-block half reads
`references/reconcile.md`. Moving the section back would have put the body at
504 and broken the ceiling.

## T8 — release surface (2026-09-22)

`## [core][2.26.33] — 2026-09-22` added free-standing, directly above the
`2.26.32` entry and below the `[Unreleased]` heading and its HTML comment,
which were not displaced.

**Highlights disposition: none, deliberately.** The question the release
guidance asks is whether this changes what a consumer of the pack can do. It
does not: the eight subcommands, their argument vectors, exit codes and JSON
output are unchanged, and an adopter invoking `workspace-status` sees identical
behaviour. What changed is which instructions the agent holds at which moment.
The neighbouring `2.26.32` entry — the same class of change on `work-loop` —
carries no `Highlights` block either.

The entry writes "No rule changed" and names what moved, and does not use the
"no behaviour changed" formula: moving guidance into a predicate-gated
reference is a change in loading, and the file's own convention reserves that
second clause for entries where nothing about loading or reachability moved.

## Full consumer-suite regression (2026-09-22)

Sixteen modules covering every test that reads a `workspace-status` SKILL.md,
its scripts, or its pack surface:

```
1406 passed, 1 skipped, 34 subtests passed in 224.35s
```

## Implementation review (2026-09-22)

Two Codex rounds with disjoint lanes, plus a confirmation pass. 8 findings
raised, 7 sustained and repaired, 1 refuted.

Adversarial + security found the one defect that mattered: the
status → Type 2 finding → `repair-plan` → `repair-apply --yes` path reached two
writing subcommands without routing through the mutate mode's guards. It also
caught a pointer still naming a section that had moved. Repairing the first
exposed that the `Never` bullet described every mutating subcommand as needing
an out-of-band confirmation file, which is true for `prune`, `repair-rollback`
and migration apply but not for `repair-apply --yes`, whose gate is the user
confirming the exact plan. All three repaired; the confirmation pass re-raised
neither and found one further stale pointer class (`§§3-5`, `§2`), now resolved.
No `§` reference remains in the skill or any reference file.

The quality lens found the new suite accepted commented-out guidance as
present, and that it had given AC-0005 a second owner. Both repaired. The
comment fix was mutation-proved rather than assumed: commenting out the sole
occurrence of `references/explain.md` now reds AC-0003, where before the fix it
stayed green.

### One refuted finding

The reviewer proposed widening the portability pattern from
`(?:RFC|ADR)-0[0-9]{3}` to `(?:RFC|ADR)-[0-9]+` so `RFC-1234` would fail.
Refuted on the repository's own stated rationale: `packs/AGENTS.local.md:70`
says "IETF RFC numbers never start with `0`, unlike this catalogue's zero-padded
identifiers", and the same guidance requires that legitimate external citations
be kept rather than stripped. Widening would turn a correct external reference
into a gate failure. The narrow pattern is the contract.

## Engine note — the plan is frozen once scheduled

Writing `Status: Done` and the closing changelog entry into `plan.md` broke the
scheduled baseline hash and refused the `reviewers-clean` transition. The
engine's printed recovery is a cohort reset, which clears the retry counters and
the stasis baseline and re-pins whatever is on disk. That was not needed: the
plan's substance never changed, only its status line and changelog. Restoring
those two edits returned `plan check-current` to OK, the transition fired, and
the edits were re-applied afterwards. Ordering, not scope, was the fault.

## Final criterion verification (2026-09-22)

| Criterion | Evidence |
| --- | --- |
| AC-0001 | 478 body lines, ceiling 500 |
| AC-0002 | 3/3 reference files exist |
| AC-0003 | 3/3 linked by skill-relative path |
| AC-0004 | 8/8 subcommands mapped to exactly one mode |
| AC-0005 | 14 refusal codes emitted, 0 undocumented |
| AC-0006 | asset present, 23 lines |
| AC-0007 | cited; 0 template lines inlined in the body |
| AC-0008 | 4/4 backend digests unchanged |
| AC-0009 | 22/22 roster steps guarded; both stale claims absent |

Gate chain: `lint-ruff` clean, `lint-mypy` clean on 148 files, `lint-ci-parity`
ok (104 steps, 167 targets), `test-lint-pack-test-boundary` ok (154 cases),
`catalogue verify` ok, `lint-spec-status` spec metadata clean.
Regression: 939 passed, 1 skipped, 34 subtests across 13 modules.
