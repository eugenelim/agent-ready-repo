# Plan: Shared-prefix-aware multi-adapter install

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change has a clear dependency spine: **state schema first, then the gate
that reads it, then the contract data the gate keys on, then the surfaces that
consume the gate's verdict**. The riskiest part is the state-layer change
(`config.py`) — every reader of `State.packs` and `PackState` assumes a single
adapter per pack, so re-keying to `[pack.<name>.adapters.<adapter>]` ripples
into `safety.classify`, `State.projected_paths`, `PackState.file_sha`,
`scan_for_pack_artifacts`, install, uninstall, **and the readers the first
draft under-counted: `upgrade.py`, `diff.py`, `reconcile.py`, `init_state.py`,
and the install union-resolver**. We land the schema and its hard cross-version
refusal first (it is the highest-leverage safety AC and has no upstream
dependency), then build the footprint owner-set derivation as a pure,
TDD-tested helper, then wire it into the install gate and the reference-aware
uninstall, then add the `shared` prefix-class contract data and route the cohort
skills, and finally the disclosure rail. Greenfield migration (RFC-0052
Decision 8) means no converter — a v0.3 file is simply refused, which the
cross-version AC already covers.

**In-memory representation (pre-EXECUTE review decision, 2026-06-26).**
`State.packs` becomes `dict[tuple[str, str], PackState]` keyed by
`(pack_name, adapter)` — a **flat tuple key**, not a nested
`dict[str, dict[str, PackState]]`. The pre-EXECUTE adversarial reviewer's
crux: the nested shape silently preserves `pack_name in state.packs` membership
and `del state.packs[pack_name]`, so every whole-pack site (uninstall's `del`,
the six install/upgrade/diff membership gates) would compile and ship green
while operating at the wrong granularity — uninstall's `del` becomes a
multi-row data-loss bug. The flat tuple key makes each of those sites fail
loudly at the access boundary, forcing a deliberate per-site decision. `State`
gains helpers so the intent at each site is explicit: `has_pack(name)`
(membership across any adapter), `rows_for_pack(name) -> dict[adapter, PackState]`
(grouping), `row(name, adapter) -> PackState | None`, and
`owners_of(relpath) -> list[tuple[pack, adapter]]` (derived ownership). Within
one scope-specific state file `(pack, adapter)` is unique, so the tuple key is
total.

**Disambiguator parity.** A pack can now carry multiple adapter rows at one
scope, so `uninstall`, `upgrade`, and `diff` gain an `--adapter` disambiguator
mirroring the existing `--scope` one: infer when the pack has exactly one row
at the resolved scope; require `--adapter` when it has more than one. This is
the necessary second-caller that justifies the flag (AGENTS.md flag rule) — the
second adapter row *is* the caller that needs to differ. `install` already has
`--adapter`. No new override flag for conflicts — `--force` reuses
`safety.write_companion` (ADR-0039).

**Concurrency.** `write_jailed` is atomic per-write (tmpfile + `os.replace`),
but the command-level read-modify-write of the single `~/.agentbundle/state.toml`
is not: two concurrent installs each load a stale snapshot and the second
`os.replace` drops the first's row (lost update, not file corruption). The
concurrency AC ("both rows land") therefore needs a critical section spanning
**reload → merge-my-row → write**, not just the write. A stdlib, dependency-free,
cross-platform `O_CREAT|O_EXCL` lockfile helper with bounded retry + stale-age
reclaim wraps the user-scope state persist; the merge re-reads the latest state
under the lock so neither row is lost. This is task-zero for T7's concurrency
verification mode (T0 below).

Verification is TDD-heavy for the pure logic (owner-set, verdicts, last-owner,
round-trip) and goal-based for the contract bump, with integration tests for the
two coexistence flows and a real-invocation manual-QA check for the disclosure
rail.

## Constraints

- **RFC-0052** — the accepted proposal; Decisions 1-8 are the contract for this work.
- **ADR-0039** — install identity is the content-addressed footprint; the
  `shared` prefix class; derived (not stored) ownership; intra-pack co-ownership;
  conflict → refuse / `--force` → `.upstream`.
- **ADR-0040** — route cohort skills to `.agents/skills/`; agents/hooks/commands
  stay native; supersedes the skill-home sub-decision of ADR-0013/0015/0016.
- **ADR-0002** — install scope is a per-pack default + allowance; this work adds
  the *identity* dimension without touching the *scope* model.
- **No new dependency, no new top-level directory** (spec Boundaries). The
  no-symlink posture (`lint-packs`) rules out a symlink co-ownership model.
- Two test roots per repo convention: `packages/agentbundle/tests/` (CLI /
  install / uninstall integration) and `packages/agentbundle/agentbundle/build/tests/`
  (contract / adapter projection). Tasks split their Tests accordingly.

## Construction tests

Most construction tests live under **Tasks** below. Cross-cutting:

- **Integration:** the two end-to-end coexistence flows (kiro family;
  `.agents/skills/` cohort) and the concurrent-install race, each spanning the
  state, gate, and uninstall tasks.
- **Manual verification:** run a real `agentbundle install` for a cohort adapter
  and read the stderr disclosure rail (spec AC: disclosure wording).

## Design (LLD)

Shape is `mixed`; the sub-sections below are the ones this work actually touches.
Stack derived from the established repo (no `docs/architecture/reference.md`
present): Python 3.12, stdlib-only `agentbundle` package, hand-emitted TOML state
+ TOML contract, `unittest`-style tests across the two test roots.

### Design decisions
- **Footprint = identity, ownership derived not stored** (ADR-0039). Reuse the
  per-relpath SHA already in `PackState.files`; add no per-file owner field.
  Traces to: AC "ownership is derived" · no contract file.
- **State re-keyed `[pack.<name>.adapters.<adapter>]`** rather than a parallel
  rows list — keeps the TOML human-diffable and lets a pack's adapter rows nest
  under one table. Traces to: AC "schema v0.4 keyed by adapters".
- **In-memory `State.packs: dict[tuple[str, str], PackState]`** keyed
  `(pack, adapter)` — flat tuple, not nested dict, so whole-pack `del`/`[]`/`in`
  sites fail loudly and are each revisited (pre-EXECUTE review). `State` grows
  `has_pack` / `rows_for_pack` / `row` / `owners_of` accessors. Traces to: AC
  "multi-row resolution".
- **Hard cross-version refusal is an allowlist, not a denylist** — `load_state`
  raises unless `schema-version == "0.4"`, and an **absent** `schema-version`
  raises rather than defaulting to the current constant (security review
  Blocker 1). This makes the legacy v0.1/v0.2/v0.3 read-time-default code
  unreachable; it is **deleted** in T1 (a v0.3 file is now refused on read and
  write, per greenfield D8). Traces to: AC "cross-version refusal".
- **Co-ownership is intra-pack + SHA-equal**; cross-pack same-path always
  refuses. Prevents accidental boilerplate-file co-ownership. Traces to: AC
  "co-own only same-pack same-SHA", AC "cross-pack refuse".
- **Reuse `safety.write_companion` for `--force`** — no new override flag
  (ADR-0039). Traces to: AC "`--force` → `.upstream`".

### Data & schema
- State schema v0.3 → v0.4. New key shape:
  `[pack.<name>.adapters.<adapter>]` with `installed-version`, `scope`, and the
  existing `files` map (relpath → sha), plus existing per-adapter fields
  (`target-file`, `hook-wiring-owned`) moving under the adapter row.
- `STATE_SCHEMA_VERSION` constant in `config.py` → `"0.4"`.
- Hard cross-version refusal: `load_state` raises `StateFileLegacy`-style unless
  `schema-version == "0.4"` (allowlist); an absent `schema-version` raises (no
  fallback to the current constant), on read and write. The v0.1/v0.2/v0.3
  read-time-default branches are deleted as unreachable dead code.
- Emitter: the `[pack.<name>.adapters.<adapter>]` table header and every key
  segment route through `_toml_key` (the adapter name as well as the pack name),
  so a non-`[alnum-_]` name cannot inject phantom TOML structure. A construction
  test feeds a pack/adapter name with `"` / `.` / a control char and asserts the
  emitted header round-trips through `tomllib` (security review Concern 3).
- Per-row fields (`scope`, `target-file`, `hook-wiring-owned`, `installed-version`,
  `primitives`, `files`, `primitive_versions`) live **under** the adapter row.
- Traces to: AC "schema v0.4", AC "cross-version refusal", AC "round-trip raises",
  AC "emitter round-trips".

### Interfaces & contracts
- Adapter contract (`_data/adapter.toml`, mirrored `docs/contracts/adapter.toml`):
  each `allowed-prefixes` entry gains a `class` (`private`/`shared`); each
  `shared` prefix gains a `reader-cohort` list. Contract version bumped.
- cursor/gemini/copilot `skill` output path → `.agents/skills/`; cursor, gemini,
  and copilot `allowed-prefixes` gain `.agents/skills/` at both repo and user
  scope (codex already lists it at both).
- Traces to: AC "prefix class + cohort fields", AC "`.agents/skills/` shared
  cohort", AC "cohort skill routing", AC "cohort prefix admissibility", AC "version bump".

### Component / module decomposition
- New pure helper(s) for footprint ownership — owner-set derivation over rows and
  the per-relpath verdict (co-own / conflict / new) — sited in `config.py`
  (which both install and uninstall already import; `safety` imports `config`,
  so siting here avoids an import cycle — pre-EXECUTE nit 9). Reused:
  `safety.write_companion`, the existing path-jail (`assert_under` /
  `write_jailed`), the capture-once uninstall discipline.
- New stdlib lockfile helper (`O_CREAT|O_EXCL` + bounded retry + stale reclaim)
  for the user-state read-merge-write critical section — cross-platform, no new
  dependency, no symlink.
- **Full updated-reader inventory** (the first draft named four; review found
  more). Each must resolve across all `(pack, *)` rows or be re-keyed to a
  specific `(pack, adapter)` row:
  - `config.py`: `State.projected_paths` (all rows), `PackState.file_sha`
    (per-row; the multi-row resolution lives in `classify` and `owners_of`).
  - `safety.py`: `classify` (drop first-owner `break`; on-disk SHA is Tier-1 if
    it matches **any** owner-row's recorded SHA — co-owned rows hold equal SHA
    by construction, so this is well-defined; a mismatch against all is Tier-2),
    `scan_for_pack_artifacts` (keyed by pack-across-rows — a sibling row's file
    is not an orphan), `projected_files_in_state`.
  - `install.py`: the gate (`installed_at_repo/user`, ~450), the row write
    (~920/1086 — construct + store the `(pack, adapter)` row), the union
    resolver (~3557/3631-3633), the profile already-set (~3868/3888), the
    recommend check (~2596-2597), the orphan/diff reads (~1806/1876/1978).
  - `uninstall.py`: `--adapter` disambiguator; remove the single `del`; per-file
    last-owner + per-row-scope path-jail.
  - `upgrade.py`: `--adapter` disambiguator; `pack_state = row(pack, adapter)`.
  - `diff.py`: `--adapter` disambiguator (read-only) + multi-row reads.
  - `reconcile.py` (~87) and `init_state.py` (~133/228): adapt to the keyed
    shape; `init_state --migrate` from a legacy version refuses with re-install
    guidance (greenfield D8 — no v0.3→v0.4 converter).
- Traces to: AC "multi-row resolution", AC "orphan scan keyed by pack-across-rows".

### State & control flow
- **Install gate:** for each incoming relpath compare against the union of
  installed footprints at this scope → {absent→write+claim, same-pack same-SHA→
  co-own+skip-write, different-SHA or cross-pack→conflict}. Aggregate →
  {already-installed | proceed | refuse}.
- **Uninstall:** target one `(pack, adapter)` row (inferred or `--adapter`).
  Capture per-relpath remove/keep decision once against the persisted union of
  all rows (a relpath is removed only when the targeted row is its **last**
  owner across all `(pack, *)` rows), then execute without re-derivation.
  Path-jail each removal against the **removing row's own** `allowed-prefixes`
  **at the row's own scope** (`.repo`/`.user`) under the **same root the file
  was written under** — never the union, never a sibling's (security review
  Blocker 2). Then drop only the targeted row from state.
- Traces to: AC "footprint gate verdicts", AC "last-owner uninstall", AC
  "capture-once", AC "per-row jail".

### Failure, edge cases & resilience
- Cross-version stale-binary read (v0.3 reads v0.4) → refuse, not silent
  mis-parse.
- Orphan scan during a second cohort install must treat sibling-row files as
  owned. Concurrent installs to the single user state file must not corrupt it.
- Traces to: AC "round-trip raises", AC "orphan scan", AC "concurrent install".

### Dependencies & integration
- No new external dependency. Integrates the two adapter registries
  (`build/adapters/__init__.py`) and the contract-version sweep (`version.py`
  `SPEC_VERSION` + pinned tests).

> **Rollout & deployment** is realized by [`## Rollout`](#rollout) below.

## Tasks

### T1: State schema v0.4 + hard cross-version refusal

**Depends on:** none

**Tests:** (root: `packages/agentbundle/tests/`)
- Emitting a `State` with two adapter rows for one pack produces
  `[pack.<name>.adapters.<a>]` / `[...adapters.<b>]` and `schema-version = "0.4"`.
- emit → load → emit is byte-stable for the nested structure. (AC "emitter round-trips")
- emitter routes pack/adapter names through `_toml_key`: a name containing `"`
  / `.` / a control char emits a header `tomllib` can re-parse, and round-trips.
  (security review Concern 3)
- `load_state` raises unless `schema-version == "0.4"` — on **read** and on
  **write** — including an **absent** `schema-version` (no fallback) and a v0.3
  file. (AC "cross-version refusal", security review Blocker 1)
- A v0.4 file's `[pack.<name>.adapters.<adapter>]` shape cannot be mis-read as a
  zero-file pack by the v0.3 parse rules — asserted against a frozen copy of the
  v0.3 parse logic / fixture, not the live post-bump reader (which is v0.4).
  (AC "round-trip raises", RFC falsifier; pre-EXECUTE nit 10)

**Approach:**
- Bump `STATE_SCHEMA_VERSION` to `"0.4"` in `config.py:30`.
- Re-key `State.packs` to `dict[tuple[str, str], PackState]`; add `has_pack` /
  `rows_for_pack` / `row` / `owners_of` accessors. `PackState` keeps its fields;
  `adapter`/`scope` become per-row identity components.
- Parse/emit `[pack.<name>.adapters.<adapter>]` in `load_state` / `dump_state`;
  delete the now-unreachable v0.1/v0.2/v0.3 read-time-default branches.
- Replace the parse-through default with an allowlist raise (`!= "0.4"` →
  `StateFileLegacy`-style, read and write; absent version → raise).
- Sweep the test-fixture surface: every v0.1/v0.2/v0.3 state fixture/builder in
  both test roots either bumps to v0.4 shape or asserts the new refusal.

**Done when:** the tests above are green and the version-pin tests assert `"0.4"`.

### T0: Cross-process state-write lock (task-zero for T7 concurrency)

**Depends on:** T1

**Tests:** (root: `packages/agentbundle/tests/`)
- two threads/processes each acquire the lock for the same path; the second
  blocks until the first releases, then proceeds (mutual exclusion).
- a stale lock older than the reclaim age is reclaimed rather than deadlocking.
- lock acquire/release leaves no lockfile behind on the happy path.

**Approach:**
- Add a stdlib `O_CREAT|O_EXCL` lockfile context manager (sibling-of-state
  `.lock`), bounded spin-retry with a short sleep, stale reclaim by mtime age.
  No new dependency, no symlink, cross-platform (`os.open` flags only).
- Provide a `persist_state_locked(state_path, mutate_fn, *, scope, prefixes)`
  helper that, under the lock, re-reads the latest state, applies `mutate_fn`
  (insert/replace this run's `(pack, adapter)` row), and writes via
  `write_jailed` — so a concurrent run's row is merged, not lost.

**Done when:** the mutual-exclusion + stale-reclaim tests are green.

### T2: Footprint ownership helpers (pure, TDD)

**Depends on:** T1

**Tests:** (root: `packages/agentbundle/tests/`)
- owner-set derivation: given rows across adapters/packs, returns the correct
  owner-set per relpath. (AC "ownership derived")
- per-relpath verdict: absent→new; same-pack+same-SHA→co-own; same-pack+different
  SHA→conflict; cross-pack same path even at equal SHA→conflict. (AC "co-own", AC
  "cross-pack refuse", AC "different-SHA refuse")
- aggregate verdict: all-owned-matching→already-installed; some-new-no-conflict→
  proceed; any-conflict→refuse. (AC "aggregate verdict")

**Approach:**
- Add pure functions (owner-set + verdict) near the state model; no I/O, fully
  unit-testable. Co-ownership predicate = same pack AND equal SHA.

**Done when:** the verdict matrix tests are green.

### T3: Footprint-aware install gate + `--force` `.upstream` wiring

**Depends on:** T2

**Tests:** (root: `packages/agentbundle/tests/` — install integration)
- disjoint-footprint second install succeeds (`research` codex after claude-code). (AC "disjoint coexist")
- same-pack same-SHA incoming relpath is co-owned (recorded, write skipped). (AC "co-own")
- different-SHA / cross-pack conflict refuses, naming the relpaths. (AC "refuse named")
- `--force` on a footprint conflict calls `safety.write_companion`; no new flag. (AC "`--force` → `.upstream`")

**Approach:**
- Replace `installed_at_user = pack_name in user_state.packs` (install.py:450-451)
  with the T2 aggregate verdict against the union of footprints at scope, keyed
  by `(pack, adapter)`. Enumerate and re-key every other whole-pack membership
  site so the second-adapter install is not re-blocked: install 2596-2597, the
  union resolver 3631-3633, the profile already-set 3868/3888, and the
  cross-scope refusal at 498-507 (now "(pack, adapter) at other scope"). Each
  site states whether it stays pack-level (`has_pack`) or becomes
  `(pack, adapter)`-aware. (pre-EXECUTE Blocker 2)
- Construct/store the row at `(pack, adapter)` (install.py:920/1086); for an
  incoming relpath co-owned by a sibling row at equal SHA, record it in the new
  row's `files` and **skip the physical write**.
- Persist the row through `persist_state_locked` (T0) so concurrent installs
  merge rather than overwrite.
- Wire the conflict verdict to `safety.write_companion` under `--force` — the same
  writer already called on the Tier-2-squatter branch at `install.py:940`; reuse it,
  add no new override flag.

**Done when:** the install-integration tests above are green.

### T4: Reference-aware uninstall + multi-row per-file readers + disambiguators

**Depends on:** T2

**Tests:** (root: `packages/agentbundle/tests/` + `build/tests/` for classify)
- last-owner: two same-pack rows, uninstall one → shared file survives; uninstall
  the second → removed. (AC "last-owner", RFC falsifier)
- decision captured once against the persisted union (no re-derivation in the
  execute pass). (AC "capture-once")
- `safety.classify` / `projected_paths` / `file_sha` resolve across all rows
  (`classify` no longer first-owner `break`; Tier-1 iff on-disk SHA matches any
  owner-row's recorded SHA). (AC "multi-row resolution")
- `scan_for_pack_artifacts` keyed by pack-across-rows; a sibling-row file is not
  an orphan. (AC "orphan scan keyed by pack")
- two rows with **different** `allowed-prefixes`: each removal is jailed against
  its own row's prefixes at the row's own scope — a path admissible only under a
  sibling's prefixes is refused. (AC "per-row jail")
- uninstall/upgrade/diff with two adapter rows and no `--adapter` refuses asking
  for one; with one row, infers. (disambiguator parity)

**Approach:**
- Update the per-file readers (full inventory in Design § Component) to iterate
  all `(pack, *)` rows or take an explicit `(pack, adapter)`.
- Uninstall: `--adapter` disambiguator; compute last-owner once against the
  persisted union; jail each removal against the removing row's own prefixes at
  its own scope; drop only the targeted row (not the whole pack).
- upgrade/diff: `--adapter` disambiguator + multi-row reads; `reconcile`
  adapts to the keyed shape.
- `init_state --migrate`: retarget the `_run_migrate` `source_version in
  ("0.2","0.3")` **header-only** branch (`init_state.py:209-217`) — today it
  rewrites only the `schema-version` line, which would relabel a flat
  `[pack.<name>]` v0.3 body as v0.4 and slip a v0.3-shaped body past the
  allowlist reader. Under greenfield D8 every legacy version (v0.1/v0.2/v0.3)
  refuses with re-install guidance; the `else` full-reserialize branch (which
  now hits the allowlist raise via `load_state`) is removed too. Construction
  test: `init-state --migrate` on a v0.3 file refuses rather than emitting a
  v0.4-labelled v0.3 body. (pre-EXECUTE iter-2 Concern 1)

**Done when:** the uninstall + classify + disambiguator tests above are green.

### T5: `shared` prefix class + cohort routing in the contract

**Depends on:** T1

**Tests:** (root: `packages/agentbundle/agentbundle/build/tests/` — contract)
- every `allowed-prefixes` entry has a `class`; `.agents/skills/` is `shared` with
  cohort {codex,cursor,gemini,copilot}; `.kiro/skills/` is `shared` with cohort
  {kiro-ide,kiro-cli}; all others `private`. (AC "prefix class + cohort", AC "shared cohorts")
- cursor/gemini/copilot skill output path = `.agents/skills/`; agents/hooks/commands
  unchanged. (AC "cohort skill routing")
- cursor, gemini, and copilot `allowed-prefixes` include `.agents/skills/` at
  **both** repo and user scope (codex already does). (AC "cohort prefix admissibility")
- `_data/adapter.toml` and `docs/contracts/adapter.toml` agree byte-for-byte;
  contract version bumped; version-assertion sweep updated. (AC "byte-for-byte", AC "version bump")

**Approach:**
- Add `class` + `reader-cohort` to the contract prefix data; retarget cursor/
  gemini/copilot skill modes to `.agents/skills/`; add `.agents/skills/` to
  cursor/gemini/copilot `allowed-prefixes.repo` **and** `.user` (codex already
  has it); bump contract version; update `version.py`/pinned tests; mirror to
  `docs/contracts/adapter.toml`.

**Done when:** contract tests + version sweep green; `make build`/projection clean.

### T6: Install-time cross-adapter disclosure rail

**Depends on:** T3, T5

**Tests:**
- goal-based: after an install writing to a `shared` prefix, the disclosure
  helper returns the pinned string naming the other shipped cohort adapters. (AC "disclosure")
- manual QA: run a real `agentbundle install <pack> --adapter codex` and observe
  the stderr rail end-to-end.

**Approach:**
- After a successful install touching a `shared` prefix, emit the pinned stderr
  block naming the cohort's other shipped adapters and the skills-shared /
  private-needs-own-install boundary.
- The pinned wording's path is **scope-aware** (pre-EXECUTE Concern 8): user
  scope renders `~/.agents/skills/` and `~/.<adapter>/`; repo scope renders the
  repo-relative `.agents/skills/` and `.<adapter>/`. The cohort named is the
  prefix's *other shipped* adapters; the native prefix is the installed
  adapter's own.

**Done when:** the pinned-string test is green (both scopes) and the manual-QA run shows the rail.

### T7: End-to-end coexistence flows + concurrent-install race

**Depends on:** T0, T3, T4, T5

**Tests:** (root: `packages/agentbundle/tests/` — integration)
- kiro family: install kiro-cli then kiro-ide → skills co-owned, `.md` agents
  written, `.json` survive; uninstall kiro-cli → `.json` removed, skills remain. (AC "kiro coexist")
- `.agents/skills/` cohort: install for codex then cursor → skills co-owned,
  cursor private primitives written, codex skills not swept. (AC "cohort coexist", RFC falsifier)
- two simultaneous installs of different adapter rows of one pack to the single
  `~/.agentbundle/state.toml`: the test asserts **both rows are present** after
  the race (not merely that the file parses) — a lost row is corruption of
  intent. (AC "concurrent install"; pre-EXECUTE Concern 7)

**Approach:**
- Assemble the integration flows against fixture trees; assert co-ownership,
  non-sweep, and per-row private writes; drive two installs concurrently through
  the T0 lock and assert both `(pack, adapter)` rows survive.

**Done when:** the three integration tests are green.

## Rollout

- **Delivery:** big-bang within `agentbundle`; the gate is internal, no flag.
  **Greenfield (RFC-0052 Decision 8)** — no migration of existing v0.3 installs;
  a v0.3 state file is refused (T1), and the adopter re-installs. The
  irreversible edge is that a v0.4 file cannot be read by an older binary — which
  is the intended hard refusal, not a regression.
- **Infrastructure:** none — no new services, storage, or secrets.
- **External-system integration:** none beyond the adapter contract's declared
  cohort tools (codex/cursor/gemini/copilot reading `.agents/skills/`); that
  reliance is re-verified at each future contract bump (ADR-0040).
- **Deployment sequencing:** schema (T1) before the gate (T3) and uninstall (T4);
  contract data (T5) before the disclosure rail (T6); flows (T7) last. This is
  the `Depends on:` DAG above.

## Risks

- **State re-key ripples wider than the four named readers.** A missed reader
  silently mis-classifies a co-owned, adopter-edited file. Mitigation: T4's
  classify/scan tests plus a grep for every `state.packs` access during EXECUTE.
- **Contract bump drifts the two adapter.toml copies or the version sweep.**
  Mitigation: T5's byte-for-byte and version-sweep ACs; run `make build` /
  projection gates.
- **Concurrent writes to the single user state file** corrupt it under load.
  Mitigation: T7's race test; the spike (RFC-0052 Evidence) found no lock today,
  so this test is the gate on whether one is needed.
- **Copilot routing leaves a stale `.github/skills/` / `.copilot/skills/` tree**
  for existing installs — greenfield re-install covers it, but call it out in the
  changelog as a user-visible behaviour change.

## Changelog

- 2026-06-26: initial plan, authored from RFC-0052 + ADR-0039/0040.
- 2026-06-26: absorbed pre-EXECUTE adversarial + security-design review.
  Pinned the in-memory representation to a flat `dict[tuple[str, str], PackState]`
  (loud-failure over the nested dict). Added T0 (cross-process state-write lock,
  task-zero for the concurrency AC — lost-update, not just file corruption).
  Expanded the updated-reader inventory to include `upgrade.py`, `diff.py`,
  `reconcile.py`, `init_state.py`, and all install membership sites. Added an
  `--adapter` disambiguator to uninstall/upgrade/diff. Specified the
  cross-version refusal as an allowlist (`!= "0.4"` → raise; absent → raise) and
  the deletion of the now-dead legacy read-time-default code. Pinned the per-row
  removal jail to the removing row's own prefixes at its own scope/root. Made the
  disclosure rail scope-aware. Routed the v0.4 emitter's adapter key through
  `_toml_key`.
