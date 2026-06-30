# Plan: install-state-visibility

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is additive plus a messaging fix, all inside `agentbundle/commands/`
and the existing `State` / `safety` surfaces — no schema bump, no new module
boundary. It splits into two independent strands that meet only at the release
task. **Strand A** is a new read-only `list-installed` command modelled on the
existing `list-packs` command (same catalogue-resolution chain, same table
helper shape) but sourcing rows from the *state* files rather than the catalogue,
and joining each row against the catalogue's `pack.toml` version to compute a
status. **Strand B** is three messaging fixes in the existing upgrade flow (and
the parallel disambiguators in `diff`/`uninstall`): enrich the multi-adapter
disambiguator with per-adapter versions, replace the unconditional
`upgraded: X -> X` recap with a three-way verdict (`upgraded` / `re-applied, no
changes` / `re-applied, N companions`), and add an upfront drift notice before
the confirm. The riskiest part is the recap/notice work in `upgrade.py`: the
drift count must be computed from on-disk-vs-state SHAs (via `safety.classify`)
*without* reordering the existing render-after-confirm flow, so it stays cheap
and doesn't change what upgrade writes. Tests are TDD for all pure logic
(status computation, drift counting, message strings) and goal-based
real-subprocess invocations for CLI wiring and end-to-end.

## Constraints

- **RFC-0052 / ADR-0039** — state is keyed `(pack, adapter)`; ownership is
  derived, not stored. `list-installed` iterates `state.packs` and the drift
  count rides the existing derived-ownership `safety.classify`, adding no
  per-file storage.
- **Tier-1/2/3 safety contract** — drift = Tier-2 (on-disk SHA ≠ recorded SHA).
  This plan *reads* that classification; it never changes what the upgrade walk
  writes.
- **AGENTS.md** — new shipped CLI surface ⇒ version bump + README + changelog in
  the same PR; full-mode work-loop.

## Construction tests

Per-task tests live under each task. Cross-cutting:

**Integration tests:** one end-to-end real-subprocess test that installs a pack
into a tmp home/repo, runs `agentbundle list-installed` (default, `--no-check`,
`--scope`, `--check-drift` after editing a file), and asserts the observable
columns and exit code. Lives under `packages/agentbundle/tests/`.

**Manual verification:** reproduce the user's original session — `architect`
installed at user scope for two adapters — and confirm (a) `list-installed`
shows both rows with versions and status, (b) the disambiguator names both
adapters with versions, (c) a same-version `upgrade --adapter codex` prints
`re-applied … (already current; no changes)` not `upgraded … 0.9.0 -> 0.9.0`.

## Design (LLD)

Shape `service`. Stack: Python ≥3.11, stdlib `argparse` sub-command dispatch via
the lazy loader in `cli.py`; no framework. The reference architecture
(`docs/architecture/reference.md`) is absent for this package, so the design
conforms to the established `agentbundle` command pattern: each subcommand is a
`commands/<name>.py` module exposing `run(args) -> int`, wired in `cli.py` via
`subparsers.add_parser(...).set_defaults(func=_lazy("<name>"))`.

### Design decisions
- **Source rows from state, join to catalogue for `latest`** — `list-installed`
  reads both scope state files and, unless `--no-check`, resolves the catalogue
  once (shared across all rows) to read each pack's `pack.toml` version.
  Rejected: storing `latest` in state (drifts immediately; the whole point is a
  live comparison). Traces to: ACs 1, 3, 4 · contracts/none.
- **Status is a pure function of (installed, latest, resolvable?)** — isolate it
  in a small helper so it is TDD-able without I/O. `unknown` covers both an
  unresolvable catalogue and a per-pack major-version mismatch, so one row's bad
  pack never aborts the listing. Detect the mismatch via `config.pack_spec_version`
  + `_common._major` **directly** — *not* `check_spec_version_gate`, which prints
  a refusal to stderr and is wired for the abort-style callers (`list_packs.py`
  `return 1`s on it). Traces to: ACs 3, 4 · contracts/none.
- **Row-scoped drift count, render-free** — for `--check-drift` and the upgrade
  upfront notice, count a row's files whose on-disk SHA ≠ that row's recorded
  `PackState.file_sha`. Do **not** delegate to `safety.classify`: it resolves
  against `state.shas_for` (the SHA set across *all* rows), so a co-owned path
  matching another owner would read Tier-1 and undercount the named row. The
  count needs only the loaded state + on-disk files — no catalogue render — so it
  stays cheap and doesn't perturb upgrade's render-after-confirm ordering.
  Rejected: rendering the new projection to count "files that will change"
  (forces a render before the prompt the user may decline). Traces to: ACs 6, 12
  · contracts/none.
- **Three-way recap verdict from the signals actually available** — `upgraded`
  when `from != to`; otherwise `re-applied`, sub-cased on whether the walk dropped
  any `*.upstream` companions (the existing `companions` list collected in
  `upgrade.run`). The walk writes every projected path unconditionally and tracks
  no per-file change, so the recap does **not** claim "no changes on disk"; the
  honest same-version verdict is "already current" (+ companion count when
  edits were preserved). Traces to: ACs 8, 9, 10 · contracts/none.

### Interfaces & contracts
No machine contract (`Contract: none`). The human-facing surfaces are: the
`list-installed` stdout table + flags (`--scope`, `--no-check`/`--offline`,
`--check-drift`), and the upgrade/​diff/​uninstall stderr messages. Column order
and status vocabulary are pinned by ACs 1, 3, 5, 6. Traces to: ACs 1, 2, 5, 6.

### Component / module decomposition
- **New:** `agentbundle/commands/list_installed.py` (`run` + private helpers:
  `_collect_rows`, `_status_for`, `_drift_count`, `_print_table`), wired in
  `cli.py`. Reuses `resolve_catalogue` / `resolve_catalogue_uri` /
  `load_pack_toml` (from `list_packs`'s imports), `scope` helpers for the user
  state path, and `State` / `safety.classify`.
- **Changed:** `commands/upgrade.py` (disambiguator message, recap verdict,
  upfront notice), `commands/diff.py` + `commands/uninstall.py` (disambiguator
  message only). A shared message helper for the per-adapter-version string lives
  next to the existing disambiguator code (inline a single helper; extract only
  if a fourth caller appears).
Traces to: ACs 1, 7, 8-12.

### Failure, edge cases & resilience
- Unresolvable catalogue / `$HOME` unset / missing state file → list what is
  resolvable, mark the rest `unknown`, exit 0 (never crash). Traces to: AC 4.
- No packs installed at the selected scope → friendly line, exit 0. Traces to:
  AC 7.
- A file recorded in state but absent on disk → not drift (it is Tier-1 "about
  to write"); the drift count counts only Tier-2. Traces to: ACs 6, 12.

## Tasks

### T1: `list-installed` command — state rows, scope filter, table

**Depends on:** none

**Tests:**
- TDD: `_collect_rows` over a constructed two-scope `State` returns one entry per
  `(pack, adapter, scope)`, deterministically sorted (AC 1).
- TDD: `--scope user` / `--scope repo` filters rows (AC 2).
- Goal-based (subprocess): empty state prints the "no packs installed" line, exit
  0 (AC 7).

**Approach:**
- Add `commands/list_installed.py` with `run(args)`: resolve both scope state
  paths (user via `scope.resolve_user_root`, repo via `root/.agentbundle-state.toml`),
  `load_state` each (read-only), build rows from `state.packs`.
- Wire the subparser in `cli.py` next to `list-packs`/`list-targets`, with
  `--scope {user,repo}`.
- `_print_table` for PACK/ADAPTER/SCOPE/INSTALLED (LATEST/STATUS added in T2).

**Done when:** subprocess `agentbundle list-installed` prints the state-only
table for a tmp install; T1 tests green.

### T2: catalogue join — LATEST + STATUS, with offline degradation

**Depends on:** T1

**Tests:**
- TDD: `_status_for(installed, latest, resolvable)` → `up-to-date` /
  `upgrade-available` / `unknown` across the cases (AC 3).
- TDD: unresolvable catalogue → every row `unknown`, run returns 0 (AC 4).
- Goal-based (subprocess): `--no-check` (and alias `--offline`) prints only the
  state-only columns (AC 5).

**Approach:**
- Resolve the catalogue once via `resolve_catalogue_uri`/`resolve_catalogue`
  (mirroring `list_packs`); on `CatalogueError`, set a `catalogue=None` sentinel
  rather than returning 1.
- Per pack, `load_pack_toml` for `version`; a load error or a major-version
  mismatch (checked via `config.pack_spec_version` + `_common._major`, **not**
  `check_spec_version_gate` — that prints and is for abort-style callers) → that
  pack's rows are `unknown` (do not abort, do not print a refusal).
- Add `--no-check`/`--offline`; when set, skip resolution and drop LATEST/STATUS
  columns.

**Done when:** default run shows LATEST/STATUS; offline/unresolvable degrade to
`unknown` with exit 0; T2 tests green.

### T3: `--check-drift` column

**Depends on:** T1

**Tests:**
- TDD: `_drift_count` over a state row with one file edited away from its
  recorded SHA returns 1; clean returns 0 (AC 6).
- Goal-based (subprocess): after editing an installed file, `--check-drift` shows
  the nonzero count in a DRIFT column (AC 6).

**Approach:**
- `_drift_count(pack_state, root)` counts the row's files whose on-disk SHA ≠
  `pack_state.file_sha(relpath)` (absent-on-disk is not drift). Row-scoped — does
  **not** call `safety.classify` (which resolves against all rows' SHAs and would
  undercount co-owned paths).
- `--check-drift` appends the DRIFT column.

**Done when:** drift column reflects edited vs clean files; T3 tests green.

### T4: multi-adapter disambiguator — per-adapter versions

**Depends on:** none

**Tests:**
- TDD: the upgrade disambiguator message for a two-adapter pack names each
  adapter with its `installed_version` (AC 8).
- TDD: the parallel `diff` and `uninstall` disambiguator messages carry the same
  enrichment (AC 8).

**Approach:**
- A small helper formats `adapter (version)` pairs from a `{adapter: PackState}`
  mapping (the `rows_for_pack(...)` return each site already has —
  `PackState.installed_version`); use it in `upgrade.py:184-190`,
  `diff.py:117-119`, `uninstall.py:145-146`.

**Done when:** the three disambiguator messages show versions; T4 tests green.

### T5: upgrade recap verdict + honest re-apply prompt

**Depends on:** none

**Tests:**
- TDD: `from != to` → recap `upgraded: … <from> -> <to>` (AC 9).
- TDD: same version, no companions dropped → `re-applied: … (already current)`;
  never `upgraded: … X -> X` and never a "no changes" claim (AC 10).
- TDD: same version, companions dropped → recap names the companion count (AC 11).
- TDD: the same-version confirm prompt text describes restore/reset + companion
  preservation, with no "repairs local drift" string (AC 12, prompt half).

**Approach:**
- Replace the unconditional recap at `upgrade.py:734-738` with a verdict computed
  from `already_current` + whether `companions` is non-empty.
- Reword the same-version prompt at `upgrade.py:333-334` and the `--yes`/`--dry-run`
  stderr line at `upgrade.py:352-359` consistently.

**Done when:** the three recap cases and the reworded prompt assert green; T5
tests green.

### T6: upfront drift notice before the upgrade confirm

**Depends on:** T5

**Tests:**
- TDD: a state with one edited file emits the pre-confirm notice naming the
  count; zero edits → no notice line (AC 12, notice half).

**Approach:**
- Before the confirm block (`upgrade.py:330`), compute the Tier-2 count via the
  same `_drift_count`-style classification over the loaded state (render-free)
  and, when >0, print the upfront notice. Shared with T3's counting logic — keep
  one helper (in `safety` or a small `commands/_common` function) and call it
  from both list-installed and upgrade.

**Done when:** the notice appears only when edits exist; T6 tests green; upgrade's
write behavior and existing exit-code tests unchanged.

### T7: release — version bump, README, changelog

**Depends on:** T1, T2, T3, T4, T5, T6

**Tests:**
- Goal-based: `agentbundle --version` reports 0.10.0; `pyproject.toml` version ==
  `CLI_VERSION`; `list-installed --help` exits 0 and documents the flags (AC 13).

**Approach:**
- Bump `pyproject.toml` version and `agentbundle/version.py` `CLI_VERSION` to
  0.10.0 together.
- Add the `list-installed` command and the upgrade-messaging change to
  `packages/agentbundle/README.md` and `docs/product/changelog.md`.

**Done when:** version sweep consistent, README + changelog updated, help text
present; AC 13 green.

## Rollout

- **Delivery:** big bang within one PR; fully reversible (additive command +
  message strings). No flag.
- **Infrastructure:** none.
- **External-system integration:** none — catalogue resolution reuses the
  existing chain.
- **Deployment sequencing:** publish to PyPI on tag after merge (the release task
  bumps the version; the existing release workflow publishes). No migration.

## Risks

- **Catalogue resolution latency** — the default up-to-date check can hit the
  network for a remote `git+https` catalogue, making `list-installed` slower than
  expected. Mitigated by `--no-check`/`--offline` and by resolving the catalogue
  once (not per row).
- **Drift-count cost on large installs** — hashing every projected path under
  `--check-drift` / for the upgrade notice scales with file count. Acceptable
  (install footprints are small) and opt-in for the list command.
- **Recap-string test brittleness** — asserting exact message strings can break
  on wording tweaks; assert the load-bearing tokens (verb, versions, scope,
  companion count) rather than the whole sentence.

## Changelog

- 2026-06-30: initial plan.
