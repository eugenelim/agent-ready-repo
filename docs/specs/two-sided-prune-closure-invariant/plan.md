# Plan: Two-sided prune closure invariant

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` (`_migration_lock` at 1891, `_migration_atomic_replace` at 1569 with its four named fault-injection points, and the pre-replace concurrency guard at 1330-1359); `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` (`selected_membership_status` at 2884, `_extract_canonical_memberships` at 2488, `_legacy_canonical_alias` at 2856); `packs/core/.apm/skills/work-intake/scripts/intake_transaction.py` (`run_intake_transaction` at 32, unlocked callbacks at 67 and 76); analogous construction paths `tests/roster/test_selection_scoped_membership_absence.py` and `tools/test_workspace_status_cli.py:2421` (existing deterministic concurrent-write case); governing constraints `packs/AGENTS.md`, `packs/core/AGENTS.md`, ADR-0114, and RFC-0096 2026-09-13 Errata. Settled at plan approval, previously open: the subcommand is `prune`; the non-mutating challenge route is the same subcommand under `--preview`, not a separate subcommand; selectors are supplied by a repeatable `--select docs/specs/<slug>`; authority is supplied by `--confirmation-file`, reusing `repair-apply`'s existing confirmation shape and its `operation_id`/`operation_digest` binding fields, with the human-authorization fields supplied independently of the preview; the protected manifest is the repository-root file `.workspace-prune-protected.toml`. The manifest lives in the repository rather than under `packs/` because its contents are repository-only paths, which shipped pack content may not carry — the pack ships the mechanism, the repository ships the list.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/two-sided-prune-closure-invariant/notes/verification-ledger.md`.
> A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material.

## Approach

Add one destructive, lock-scoped operation to the existing `workspace-status`
engine and CLI, and bring the one remaining unlocked production writer into the
same lock. The prune fixes an immutable selection, validates authority and
protection, proves the artifact side present, removes the artifact tree and
every resolving membership, and then — still holding the lock — takes one
closure observation over the exact workspace bytes it read, using slice 1's
identity resolvers through a new pure seam. Build the contract first in a new
`tests/roster/` module, add the protected manifest and its derivation test
second, then the engine seam, the CLI route, the intake retrofit, and finally
pack documentation, evals, version pair, changelog, and the generated
projections.

## Constraints

- [ADR-0114](../../adr/0114-prune-success-requires-a-two-sided-post-mutation-invariant.md) fixes the invariant's shape, rejects an atomic prune, and forbids both a one-sided check and a predicate that passes when nothing was removed.
- [RFC-0096](../../rfc/0096-portable-delivery-artifact-lifecycle.md) 2026-09-13 Errata makes Wave 7d depend on these mechanics and keeps reference-free verification a separate Wave 7d condition.
- `packs/AGENTS.md` makes `.apm/` the source, requires self-host projection after edits, forbids internal governance citations in shipped pack content, requires an eval-harness update, and requires matching patch version bumps.
- `packs/core/AGENTS.md` reserves `tomlkit == 0.15.1` for `repair-apply`. The prune rewrites `workspace.toml` and must state which writer it reuses rather than adding a dependency.
- Tests live in `tests/roster/` so both `make test` and the post-build CI route collect them; `tools/` misses the post-build route.
- The engine source is not type-checked directly; mypy sees it only through the generated copy under `packages/agentbundle/`, so `make build-self` must run before type errors can surface.
- Any `.apm/` script output is UTF-8 configured before its first print.
- Pack tests load engine modules under a unique name containing both pack and skill; they never put a skill `scripts/` directory on `sys.path`.
- No shipped file under `packs/` cites this spec, ADR-0114, RFC-0096, an acceptance-criterion number, or a repository-only path.

## Construction tests

Most construction tests live under **Tasks** below (per-task `Tests:` subsections).

**Integration tests:** the focused roster suite drives the projected CLI against
fixtures carrying registered, entry-less, duplicated, legacy-aliased, and
parse-blocked memberships, and forces each named interleaving through the
fault-injection seam.

**Manual verification:** run the prune against a disposable fixture repository
outside this checkout, observe one successful two-sided removal and one forced
half-state failure, and record exit codes, JSON, and before/after byte
snapshots in the verification ledger. Never run the prune against this
repository's own `docs/specs/` or `workspace.toml`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User and maintainer promise in `packs/core/.apm/skills/workspace-status/SKILL.md` | T4, T6 | Focused CLI tests, projected end-to-end invocation, eval behavior case | `close-work` verifies the documented invocation, refusal codes, and closure guarantee against shipped behavior. |
| Interface compatibility note in `packs/core/.apm/skills/work-intake/SKILL.md` | T5, T6 | Forced-interleaving mutual-exclusion tests | `close-work` verifies the documented intake lock participation. |
| Core release history in `docs/product/changelog.md` | T6 | Version-pair assertions and changelog construction test | `close-work` verifies the core-led entry names the capability and version. |

## Design (LLD)

### Data & schema

The operation record contains the immutable selection (ordered canonical
directories and their `spec.md` paths); a per-target tree manifest recording
every entry below each selected directory by repository-relative path, entry
type, and tracked mode bits, with a SHA-256 for each regular file and the
literal target text for each symlink; a digest over that manifest; the
pre-mutation `workspace.toml` byte digest; the pre-mutation membership
occurrences from the shared observer; and the confirmation binding over the
single operation digest computed from selection, tree manifest, and workspace
hash together. The closure result carries, per
selector, artifact absence, membership absence, and any surviving occurrence
with slice 1's provenance fields. Traces to: AC-0003, AC-0004, AC-0009,
AC-0012, AC-0014, AC-0015.

### Interfaces & contracts

The engine gains a pure membership-resolution seam accepting already-parsed
workspace state, which both `selected_membership_status` and the prune call, so
slice 1's public behavior is preserved while closure binds to locked bytes. The
CLI adds one destructive subcommand with a repeatable selector argument and a
confirmation file, following `repair-apply`'s existing confirmation shape, plus a
non-mutating preview route emitting the operation identity and digest a caller
needs to build that confirmation, so the authority path is reachable from shipped
commands alone. Traces to: AC-0001, AC-0002, AC-0004, AC-0012, AC-0020, AC-0021,
AC-0022, AC-0023, AC-0029.

### Failure, edge cases & resilience

Every refusal precedes mutation and leaves the tree byte-identical. A busy lock
refuses before validation. A half-state is reported, never rolled back and
never laundered into success. Artifact absence requires directory
nonexistence under a symlink-refusing lookup. ABA is excluded only for lock
participants, and that residual is documented rather than denied. Traces to:
AC-0005, AC-0008, AC-0010, AC-0013, AC-0015, AC-0016, AC-0024, AC-0025.

### Quality attributes (NFRs)

Deterministic, offline, repository-confined, UTF-8, and fail-closed. Output
carries no absolute root, traceback, or instruction-like payload. Traces to:
AC-0024, AC-0025.

## Tasks

### T1: The roster contract fails on every unproven closure and unsafe selection

**Depends on:** none

**Touches:** `tests/roster/test_two_sided_prune_closure_invariant.py`

**Tests:**
- Add named TDD cases for every acceptance criterion, using the fixtures those criteria name, including a valid prune control alongside each rejection matrix.
- Load engine modules with `importlib.util.spec_from_file_location` under the unique name `core_workspace_status_prune_closure`; do not alter `sys.path`.

**Approach:**
- Build fixture writers for registered, entry-less, duplicate-canonical, legacy-alias, and parse-blocked memberships, and for protected and unprotected targets.
- Start from one compilable red assertion against the discovered engine seam, then fill the matrix.

**Done when:** The module collects and fails only because the prune engine, CLI, manifest, and intake lock do not yet exist.

### T2: The protected manifest refuses the repository's own pinned artifacts

**Depends on:** T1

**Touches:** `.workspace-prune-protected.toml`, `tests/roster/test_two_sided_prune_closure_invariant.py`

**Tests:**
- Make AC-0005, AC-0006, and AC-0007 pass.
- The derivation test scans the live roster suite for repository spec-directory dependencies with the standard library and fails when the manifest omits one.

**Approach:**
- Seed the manifest from the measured dependency set and the two spec directories holding four SHA-256-pinned files, then let the derivation test own its continued accuracy.
- Include this spec's own directory and `notes/` subtree.

**Done when:** Protected refusal and manifest-derivation cases are green, and removing an entry from the manifest turns the derivation test red.

### T3: The engine proves two-sided closure under one held lock

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, `tests/roster/test_two_sided_prune_closure_invariant.py`

**Tests:**
- Make AC-0003, AC-0008, AC-0009, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0020, AC-0021, AC-0022, AC-0027, and AC-0028 pass.
- Add a source-level assertion that closure reuses slice 1's resolvers rather than a parallel parser.
- Mutation proof: delete the artifact-presence precondition and prove the no-op case turns green, which must fail the suite.
- Mutation proof: weaken per-target presence to any-target presence and prove the mixed present/absent case turns green, which must fail the suite.
- Mutation proof: widen removal to the parent of a selected directory and prove AC-0027's unselected-neighbour snapshot turns red.
- Mutation proof: replace the manifest digest with a constant and prove AC-0028's stale-baseline case turns red.

**Approach:**
- Extract the pure membership seam over parsed workspace state and have `selected_membership_status` call it unchanged.
- Fix the selection, record both sides, mutate, then observe once under the lock.

**Done when:** Engine closure cases are green and each named mutation turns the suite red.

### T4: The projected CLI exposes the prune without changing existing commands

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, `packs/core/.apm/skills/workspace-status/SKILL.md`, `tests/roster/test_two_sided_prune_closure_invariant.py`

**Tests:**
- Make AC-0001, AC-0002, AC-0004, AC-0010, AC-0023, AC-0024, AC-0025, and AC-0029 pass, plus an end-to-end projected invocation.
- Snapshot the whole fixture tree around every refusal path and around the non-mutating preview.
- Mutation proof: make the preview emit a digest that omits the workspace hash and prove the round-trip case turns red.

**Approach:**
- Settle the subcommand and confirmation-flag spelling at plan approval, then extend dispatch and the serializer without touching compatibility-alias routing.
- Document selection, authority, refusal codes, the closure guarantee, and the lock residual in portable language.

**Done when:** CLI cases and the projected invocation are green while frozen existing-command outputs stay identical.

### T5: Work-intake participates in the shared lock

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/work-intake/scripts/intake_transaction.py`, `packs/core/.apm/skills/work-intake/SKILL.md`, `tests/roster/test_two_sided_prune_closure_invariant.py`

**Tests:**
- Make AC-0017, AC-0018, and AC-0019 pass, covering every named writer in both orders.
- Mutation proof: remove the lock from the intake transaction and prove the mutual-exclusion cases turn red.
- Mutation proof: release the shared lock early in one other named writer and prove its interleaving case turns red while its frozen-output check stays green, demonstrating why AC-0019 cannot rest on frozen output.
- Re-run the existing work-intake roster suites unchanged.

**Approach:**
- Wrap the whole materialize/register/rollback interval in the shared lock, reusing the existing lock helper rather than adding a second implementation.
- Keep the busy result a structured refusal consistent with the existing writers.

**Done when:** Mutual-exclusion cases are green in both orders and every pre-existing work-intake suite still passes.

### T6: Pack projection, evals, version pair, and release record agree

**Depends on:** T5

**Touches:** `packs/core/.apm/skills/workspace-status/evals/`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`, generated self-host projections

**Tests:**
- Make AC-0026 pass, including identical core/plugin versions, a strict increase over the merge-base core version, and a core-led changelog entry.
- Run self-host in write mode and verify the generated projections match the `.apm/` sources byte for byte.

**Approach:**
- Add one triggering query and one behavior case for the prune.
- Re-derive the free patch version immediately before opening the PR, never at branch start.
- Treat every generated projection change as build output.

**Done when:** Eval, version-pair, changelog, and projection checks pass with no source/projection drift.

### T7: Focused and repository gates prove the slice without pruning this repository

**Depends on:** T1-T6

**Tests:**
- Required local gate: `python3 .agents/skills/new-spec/scripts/lint-contract-item-alignment.py docs/specs/two-sided-prune-closure-invariant` exits 0.
- Required local gate: `python3 .agents/skills/work-loop/scripts/lint-spec-status.py --root .` exits 0.
- Required local gate: `python3 -m pytest tests/roster/test_two_sided_prune_closure_invariant.py -q` exits 0.
- Required local gate: `make lint-ruff lint-mypy` exits 0, run after `make build-self` so engine type errors can surface.
- Required local gate: `make build-self` and `make bootstrap-sites` exit 0 with source and generated projections byte-identical.
- Required local gate: `make build-check` exits 0.
- Optional remote evidence: `test-corpus.yml` and `test-roster.yml` dispatched when available; unavailable dispatch is recorded and does not block.
- Exercise the prune against a disposable fixture outside this checkout and record exit codes, JSON, and byte snapshots in the verification ledger.

**Approach:**
- Run narrowest checks first, then self-host, then repository gates.
- Inspect the final diff and reject any change to this repository's `workspace.toml` or `docs/specs/` beyond this spec's own directory.

**Done when:** Every required local gate is green and the end-to-end evidence is recorded.

## Rollout

This is an additive but destructive core-pack capability. It ships behind an
explicit subcommand requiring a bound confirmation, has no flag,
infrastructure, or migration dependency, and is removed by reverting the
source, manifest, test, eval, version, changelog, and generated projection
changes. It performs irreversible deletion only on an explicitly confirmed,
protected-filtered selection.

## Risks

- A closure observation evaluated from pre-mutation or intended in-memory bytes would report absence for a membership write that silently no-opped or was reverted on disk; closure must read the post-mutation bytes back from the file, still under the same lock, and the no-op-write fault case makes that red.
- A success predicate scoped only to the selection cannot see collateral destruction: an implementation deleting all of `docs/specs/` would satisfy every selection-scoped criterion. AC-0027's exact-delta snapshot is the control that catches it.
- Frozen-output equality cannot detect a writer that stopped taking the shared lock, because its isolated behavior is unchanged; AC-0019 therefore requires interleaving entered inside each writer's mutation interval.
- A hand-maintained protected manifest silently leaks as roster tests are added; the derivation test is the control that prevents it.
- Retrofitting the intake lock can deadlock against a caller that already holds it; the non-waiting lock turns a nested acquisition into a visible busy refusal rather than a hang, and the mutual-exclusion cases pin both orders.
- Claiming ABA protection the lock cannot deliver would be a false assurance; the characterization test and the documented residual keep the claim honest.
- Running the prune against this repository during development would be irreversible; manual verification is confined to a disposable fixture.

## Changelog

- 2026-09-13: Initial Drafting plan for Wave 7c Slice 2, taking the whole-operation shared lock as the closure mechanism and bringing work-intake into it.
