# Plan: Shared-prefix-aware multi-adapter install

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

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
`scan_for_pack_artifacts`, install, and uninstall. We land the schema and its
hard cross-version refusal first (it is the highest-leverage safety AC and has
no upstream dependency), then build the footprint owner-set derivation as a
pure, TDD-tested helper, then wire it into the install gate and the
reference-aware uninstall, then add the `shared` prefix-class contract data and
route the cohort skills, and finally the disclosure rail. Greenfield migration
(RFC-0052 Decision 8) means no converter — a v0.3 file is simply refused, which
the cross-version AC already covers.

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
- Hard cross-version refusal: `load_state` raises `StateFileLegacy`-style on any
  unrecognised `schema-version`, on read and write.
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
  the per-relpath verdict (co-own / conflict / new) — sited alongside the state
  model so both install and uninstall import them. Reused: `safety.write_companion`,
  the existing path-jail (`assert_under` / `write_jailed`), the capture-once
  uninstall discipline.
- Updated readers: `safety.classify` (drop first-owner `break`),
  `State.projected_paths`, `PackState.file_sha`, `scan_for_pack_artifacts`.
- Traces to: AC "multi-row resolution", AC "orphan scan keyed by pack-across-rows".

### State & control flow
- **Install gate:** for each incoming relpath compare against the union of
  installed footprints at this scope → {absent→write+claim, same-pack same-SHA→
  co-own+skip-write, different-SHA or cross-pack→conflict}. Aggregate →
  {already-installed | proceed | refuse}.
- **Uninstall:** capture per-relpath remove/keep decision once against the
  persisted union of all rows (last-owner only removes), then execute without
  re-derivation; path-jail each removal against its own row's prefixes.
- Traces to: AC "footprint gate verdicts", AC "last-owner uninstall", AC
  "capture-once".

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
- `load_state` on a file whose `schema-version` is unrecognised raises the
  `StateFileLegacy`-style error on **read** and on **write** (`for_write=True`). (AC "cross-version refusal")
- A v0.4 file loaded by the v0.3 code path raises rather than yielding a
  zero-file pack — simulated by feeding a v0.4-shaped TOML to the legacy reader
  expectation. (AC "round-trip raises", RFC falsifier)

**Approach:**
- Bump `STATE_SCHEMA_VERSION` to `"0.4"` in `config.py:30`.
- Re-key `State.packs` to hold per-pack adapter rows; parse/emit
  `[pack.<name>.adapters.<adapter>]` in `load_state` / `dump_state`.
- Replace the parse-through default for unrecognised versions with a raise
  (extend the `StateFileLegacy` gate to fire on any non-`0.4` version, read and write).
- Update `tests/unit/test_state_v0_3_schema.py` and friends to the v0.4 pin.

**Done when:** the four tests above are green and the version-pin tests assert `"0.4"`.

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
- Replace `installed_at_user = pack_name in user_state.packs` with the T2
  aggregate verdict against the union of footprints at scope.
- Wire the conflict verdict to `safety.write_companion` under `--force` — the same
  writer already called on the Tier-2-squatter branch at `install.py:940`; reuse it,
  add no new override flag.

**Done when:** the install-integration tests above are green.

### T4: Reference-aware uninstall + multi-row per-file readers

**Depends on:** T2

**Tests:** (root: `packages/agentbundle/tests/` + `build/tests/` for classify)
- last-owner: two same-pack rows, uninstall one → shared file survives; uninstall
  the second → removed. (AC "last-owner", RFC falsifier)
- decision captured once against the persisted union (no re-derivation in the
  execute pass). (AC "capture-once")
- `safety.classify` / `projected_paths` / `file_sha` resolve across all rows
  (`classify` no longer first-owner `break`). (AC "multi-row resolution")
- `scan_for_pack_artifacts` keyed by pack-across-rows; a sibling-row file is not
  an orphan. (AC "orphan scan keyed by pack")
- each removal path-jailed against its own row's `allowed-prefixes`. (AC "per-row jail")

**Approach:**
- Update the four per-file readers to iterate all `[pack.<name>.adapters.*]` rows.
- Uninstall computes last-owner once against the persisted union, then executes.

**Done when:** the uninstall + classify tests above are green.

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

**Done when:** the pinned-string test is green and the manual-QA run shows the rail.

### T7: End-to-end coexistence flows + concurrent-install race

**Depends on:** T3, T4, T5

**Tests:** (root: `packages/agentbundle/tests/` — integration)
- kiro family: install kiro-cli then kiro-ide → skills co-owned, `.md` agents
  written, `.json` survive; uninstall kiro-cli → `.json` removed, skills remain. (AC "kiro coexist")
- `.agents/skills/` cohort: install for codex then cursor → skills co-owned,
  cursor private primitives written, codex skills not swept. (AC "cohort coexist", RFC falsifier)
- two simultaneous installs of different adapter rows of one pack to the single
  `~/.agentbundle/state.toml` both land without corruption. (AC "concurrent install")

**Approach:**
- Assemble the integration flows against fixture trees; assert co-ownership,
  non-sweep, and per-row private writes; drive two installs concurrently.

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
