# Spec: Shared-prefix-aware multi-adapter install

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0052, ADR-0039, ADR-0040, ADR-0002
- **Brief:** none
- **Contract:** none <!-- the adapter projection contract (_data/adapter.toml, mirrored under docs/) is an internal projection contract, not a repo-root API surface under the contracts/ tree -->
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter can install one pack for several adapters at the same scope, and the
cohort of adapters that all read `.agents/skills/` (codex, cursor, gemini,
copilot) shares a single skill copy instead of fighting over it. The unit of
install identity is the **footprint** — the relpaths a `(pack, adapter, scope)`
install writes, each with its content SHA — not the pack name. Installing
`research` for `codex` after installing it for `claude-code` succeeds, because
their footprints are disjoint. Installing it for `cursor` after `codex` succeeds
and *shares* the existing `.agents/skills/` skill files, because both rows belong
to the same pack and the content matches. A genuine collision — the same path at
different content, or two different packs claiming one path — is refused, naming
the conflicting paths, with `--force` dropping a `.upstream` companion. A stale
binary can never silently mis-read the new state file. Success, for the adopter,
is that multi-IDE setups stop being blocked by an adapter-blind "already
installed" gate, without ever silently deleting a file another adapter still
needs.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Derive a path's owner-set by scanning installed `[pack.<name>.adapters.*]`
  rows' `files` maps; resolve ownership across **all** adapter rows of a pack,
  never first-hit.
- Co-own a shared path only when the rows belong to the **same pack** and the
  content SHA is identical.
- Capture the last-owner / removal decision once against the persisted union of
  rows, then act on it without re-derivation (mirror the existing capture-once
  discipline in `uninstall.py`).
- Path-jail-validate each removed or written file against **its own adapter
  row's** `allowed-prefixes`, never a sibling's.
- Name the conflicting relpaths whenever an install refuses on a footprint
  conflict.
- Reuse the existing Tier-2 `.upstream` companion writer (`safety.write_companion`)
  for the `--force` conflict path — do not invent a new override flag.

### Ask first

- Any change to the credential / secrets storage tiers or order (out of scope
  here, but the rule stands if the work strays near `safety.write_jailed`'s
  jail contract).
- Adding a migration / auto-converter for existing v0.3 installs — this spec is
  greenfield (RFC-0052 Decision 8); an auto-converter is a separate decision.
- Adding any adapter to a `shared` prefix's reader cohort beyond the four named
  for `.agents/skills/` and the two for `.kiro/skills/`.

### Never do

- Never key co-ownership on SHA-equality alone across **different** packs — two
  unrelated packs shipping a byte-identical file must not silently co-own it.
- Never remove a file while any other adapter row (of the same pack) still owns
  it.
- Never let a v0.4 file be silently parse-through-able by a reader that does not
  recognise `schema-version` — refuse on both read and write.
- Never introduce a symlink representation of co-ownership (the `lint-packs`
  no-symlink posture).
- Never add a new top-level directory or a new third-party dependency for this
  work — it lives inside `packages/agentbundle/` and the existing contract files.
- Never widen an adapter's `allowed-prefixes` beyond what the routed skill path
  requires.

## Testing Strategy

The verification modes (per the `work-loop` skill):

- **TDD** — the footprint gate logic (owner-set derivation, co-own vs conflict
  verdict, aggregate already-installed/proceed/refuse), the last-owner uninstall
  decision, the `safety.classify` / `projected_paths` / `file_sha` multi-row
  resolution, and the v0.4 TOML emitter / nested-key round-trip. These have
  compressible invariants and are the bulk of the suite.
- **TDD (falsifier-style)** — the cross-version refusal (round-trip a v0.4 file
  through a v0.3 reader and assert it raises), the orphan-scan-does-not-sweep
  regression, the Tier-2 co-owned-edit classification, and the last-owner
  survival/removal pair. Each is a named pre-mortem falsifier from RFC-0052.
- **Goal-based check** — the contract bump (prefix-class + reader-cohort fields
  present in `_data/adapter.toml` and mirrored to `docs/contracts/adapter.toml`;
  cursor/gemini/copilot skill target = `.agents/skills/`; cursor/gemini/copilot
  `allowed-prefixes` include `.agents/skills/` at both repo and user scope),
  verified by reading the contract and by the contract-version assertion sweep.
- **Integration** — the kiro-family coexistence flow and the `.agents/skills/`
  cohort coexistence flow, each installing a pack for one adapter then a sibling
  and asserting shared files are co-owned (not rewritten, not swept) while
  private primitives are written.
- **Visual / manual QA** — the install-time cross-adapter disclosure rail: run a
  real install that writes to a `shared` prefix and observe the stderr names the
  other shipped cohort adapters with the pinned wording.
- **Integration (concurrency)** — two simultaneous `install` runs writing
  different adapter rows of one pack to the single `~/.agentbundle/state.toml`.

## Acceptance Criteria

State schema & cross-version safety:

- [x] The state schema version is `0.4`, and the state file is keyed
  `[pack.<name>.adapters.<adapter>]`, so one pack carries multiple adapter rows
  at one scope.
- [x] A v0.4 reader refuses any unrecognised `schema-version` on **both read and
  write**, raising the existing `StateFileLegacy`-style error (not the
  parse-through default that exists today).
- [x] A v0.4 file round-tripped through a v0.3 reader raises rather than
  mis-parsing adapter rows as a zero-file pack. (RFC-0052 falsifier)
- [x] The v0.4 TOML emitter round-trips a nested `[pack.<name>.adapters.<adapter>]`
  structure: emit → load → emit is byte-stable.

Footprint install gate:

- [x] Installing one pack for two adapters with **disjoint** footprints at the
  same scope succeeds (the reported bug: `research` for `codex` after
  `claude-code`).
- [x] For an incoming relpath already owned by **another adapter row of the same
  pack at the same SHA**, the install co-owns it — records it in the incoming
  row's `files`, skips the write.
- [x] An incoming `(pack, adapter)` that already owns every relpath at matching
  SHA is reported as *already installed* (upgrade path); some-new-no-conflict
  *proceeds*; any conflict *refuses*.
- [x] A same-path / **different-SHA** collision is refused with the conflicting
  relpaths named.
- [x] A same-path collision across **different packs** is refused even at equal
  SHA, with the conflicting relpaths named.
- [x] `--force` on a footprint conflict calls the existing Tier-2
  `safety.write_companion` `.upstream` writer; no new override flag is added.

Derived ownership & uninstall:

- [x] Ownership is derived by scanning rows' `files` maps; nothing is stored
  per-file beyond the SHA already recorded.
- [x] Uninstall removes a relpath only when the removed row is its **last**
  owner; the decision is captured once against the persisted union of all rows.
- [x] Install a pack for two same-pack adapter rows, uninstall one → the shared
  skill survives; uninstall the second → it is removed. (RFC-0052 falsifier)
- [x] `State.projected_paths`, `PackState.file_sha`, and `safety.classify`
  resolve ownership across **all** adapter rows — `classify` no longer takes the
  first owner via a `break`.
- [x] `safety.scan_for_pack_artifacts` is keyed by pack-across-its-adapter-rows:
  a file owned by any sibling adapter row of the same pack is not an orphan.
- [x] During a second cohort install, the orphan scan does **not** sweep the
  first row's shared files (kiro-ide does not wipe kiro-cli `.json` agents; a
  cursor install does not sweep codex's `.agents/skills/`). (RFC-0052 falsifier)
- [x] Each removed file is path-jail-validated against its own adapter row's
  `allowed-prefixes`, never a sibling's.

Contract & cohort routing:

- [x] Each `allowed-prefixes` entry in the adapter contract carries a class —
  `private` or `shared` — and each `shared` prefix declares its reader cohort
  (shipped adapters). `_data/adapter.toml` and `docs/contracts/adapter.toml`
  agree byte-for-byte.
- [x] `.agents/skills/` is declared `shared` with cohort
  {codex, cursor, gemini, copilot}; `.kiro/skills/` is declared `shared` with
  cohort {kiro-ide, kiro-cli}; every other prefix is `private`.
- [x] cursor, gemini, and copilot write the `skill` primitive to `.agents/skills/`
  (codex already does); their agent / hook / command projection is unchanged.
- [x] cursor, gemini, and copilot include `.agents/skills/` in `allowed-prefixes`
  at **both repo and user scope** (codex already lists it at both), so the routed
  skill path is jail-admissible at the default repo scope as well as user scope.
  Concretely: `cursor.repo`/`cursor.user`, `gemini.repo`/`gemini.user`, and
  `copilot.repo`/`copilot.user` each gain `.agents/skills/`.
- [x] The adapter-contract version is bumped, and the version-assertion sweep
  (tests + any pinned constants) is updated to match.

Coexistence flows & disclosure:

- [x] Kiro family: install kiro-cli (`.kiro/skills/...` + `.kiro/agents/<a>.json`)
  then kiro-ide → skills co-owned, `.kiro/agents/<a>.md` written; uninstall
  kiro-cli → `.json` agents removed, shared skills remain.
- [x] `.agents/skills/` cohort: install a pack for codex then cursor → skills
  co-owned at the shared prefix, cursor's private `.cursor/` agents/hooks/commands
  written.
- [x] After an install that writes to a `shared` prefix, stderr names the other
  **shipped** adapters in that prefix's cohort and states the boundary (skills
  shared; private primitives need a separate per-adapter install), using the
  pinned wording below (interpolating the installed pack, adapter, scope, and the
  cohort's *other* shipped adapters; the per-adapter native prefix is the
  installed adapter's own):

  ```
  Installed <pack> for <adapter> (<scope>).
    Skills → ~/.agents/skills/ — also read by <other cohort adapters>.
    Hooks & subagents → ~/.<adapter>/ — <adapter> only; install those adapters
    separately to get them there.
  ```
- [x] Two simultaneous `install` runs writing different adapter rows of one pack
  to the single `~/.agentbundle/state.toml` both land without corrupting the file.

## Assumptions

- Technical: state model is `State` (schema_version default `"0.3"`, `packs:
  dict[str, PackState]`) and `PackState` (carries `files: dict[relpath→sha]`,
  single `adapter`, `scope`); `STATE_SCHEMA_VERSION = "0.3"` in
  `config.py:30` (source: `packages/agentbundle/agentbundle/config.py:30,108-153`).
- Technical: `load_state(for_write=…)` reads `schema-version` and only refuses
  v0.1/v0.2 on write via `StateFileLegacy`; an unrecognised version currently
  parses through — the unsafe default Decision 4 fixes (source:
  `config.py:156-283`, esp. line 193).
- Technical: the install gate computes `installed_at_user = pack_name in
  user_state.packs` (source: `commands/install.py` ~line 451); the `.upstream`
  companion is written via `safety.write_companion` (`safety.py:548`), called today
  on the Tier-2-squatter branch at `install.py:940`, and tracked in
  `_InstallPlan.new_companions`. The footprint-conflict verdict this spec adds
  reuses that same `write_companion` writer — no new override (source: probe of
  install.py:935-945 / safety.py, 2026-06-26).
- Technical: `safety.classify` takes the first owner via a `break` over
  `state.packs.values()` (source: `safety.py:76-117`); `scan_for_pack_artifacts`
  at `safety.py:452-545`; `projected_paths` is a `State` method, `file_sha` a
  `PackState` method (source: `config.py:137-153`).
- Technical: the adapter contract lives in `_data/adapter.toml` (version `0.16`)
  mirrored to `docs/contracts/adapter.toml`; current skill outputs — codex
  `.agents/skills/`, cursor `.cursor/skills/`, gemini `.gemini/skills/`, copilot
  `.github/skills/` (repo) + `.copilot/skills/` (user). cursor (`.cursor/`),
  gemini (`.gemini/`), and copilot (`.github/...` repo, `.copilot/...` user) all
  **lack** `.agents/skills/` in `allowed-prefixes` at **both** scopes; only codex
  lists it at both (source: `_data/adapter.toml:520,525,570-571,653-654,747-748`,
  probe 2026-06-26).
- Technical: two adapter registries in `build/adapters/__init__.py` (`ADAPTERS`
  callables + module `registry`); `SPEC_VERSION` derived from adapter.toml in
  `version.py` (source: probe 2026-06-26).
- Process: RFC-0052 is Accepted (2026-06-25); Decisions 1-2,4-8 adopt by silence,
  Decision 3 carried the explicit Approver yes. This spec is the
  RFC-named follow-on; ADR-0039/0040 record the architectural decisions (source:
  `docs/rfc/0052-shared-prefix-aware-multi-adapter-install.md`, user direction 2026-06-26).
- Process: this is full-mode work-loop (governance + structural + multi-feature
  triggers); spec/plan ship as a docs PR, code implementation is a later PR
  (source: RFC-0052 Follow-on artifacts; `docs/CONVENTIONS.md`).
- Product: the target user is a multi-IDE adopter blocked today from installing
  one pack for a second adapter at the same scope (source: RFC-0052 Problem &
  goals).
