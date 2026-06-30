# Spec: install-state-visibility

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0052, ADR-0039
- **Contract:** none <!-- the agentbundle CLI is not a typed contract surface (no OpenAPI/proto/event interface); the table output is human-facing, not a published machine contract -->
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A person using the `agentbundle` CLI can see the state of the world for their
installed packs — what they have, what version each is, and whether an upgrade
is available — and, when they upgrade, the CLI tells them honestly what it did.
Today that information is invisible: no command lists *installed* packs (the
`list-packs` and `list-profiles` commands query a *catalogue* of what's
*available*, and `list-targets` queries the adapter registry — none read the
state files of what's *installed*), the multi-adapter upgrade
disambiguator names the
adapters but not their versions, and the upgrade recap says `upgraded: X 0.9.0
-> 0.9.0` even when nothing changed because the installed version already
matched. Success means: a `list-installed` command that reports
pack · adapter · scope · installed-version · latest-version · status across both
scopes; a multi-adapter disambiguator that shows each adapter's installed
version inline; an upgrade recap that distinguishes a real version change from a
no-change re-apply; and an upfront notice, before the upgrade confirm, when local
edits will be preserved as companions — so the user knows what re-applying does
before they answer.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Read both scope state files (`~/.agentbundle/state.toml` and the repo's
  `.agentbundle-state.toml`) **read-only**; `list-installed` never writes.
- Degrade gracefully when the catalogue can't be resolved: report status
  `unknown` for affected rows and keep listing — never abort the listing on a
  catalogue or spec-version-gate failure.
- Reuse the existing `State` API (`state.packs`, `rows_for_pack`,
  `installed_version`); compute drift per row by comparing each file's on-disk
  SHA against that row's own recorded SHA (`PackState.file_sha`) — the same
  Tier-2 definition `safety.classify` uses, but row-scoped so co-owned paths
  aren't conflated. The drift baseline is the SHA recorded in *state* at install,
  not anything in `pack.toml`.
- Sort all tabular output deterministically (by pack, then adapter, then scope)
  so runs are stable and diff-able.

### Ask first

- Any change to the upgrade *write* behavior (the Tier-1/2/3 contract, what gets
  overwritten vs. parked as a companion) — this spec changes upgrade's
  *messaging*, not its writes.
- Any change to existing exit codes or the install→upgrade routing contract that
  current tests pin.
- Adding any dependency.

### Never do

- No new top-level dependency, and no new module boundary or top-level directory
  — the work lands in `agentbundle/commands/` and the existing `safety` / `State`
  surfaces.
- No state-schema version bump — `list-installed` reads the v0.4 schema as-is.
- No network write or any mutation from `list-installed` or from the new
  upgrade messaging; the catalogue resolution for the up-to-date check is
  read-only.
- Do not change what `upgrade` writes to disk, the per-adapter (one adapter per
  invocation) upgrade contract, or the `*.upstream` companion mechanism — only
  the text it prints before and after.

## Testing Strategy

- **`list-installed` row/status computation** (installed-version, latest-version,
  `up-to-date` / `upgrade-available` / `unknown`): **TDD** — pure logic over a
  constructed `State` plus a fixture catalogue; the status is a compressible
  invariant of (installed, latest, resolvable?).
- **Offline / unresolvable-catalogue degradation**: **TDD** — an unresolvable
  catalogue URI yields `unknown` status and a successful (exit 0) listing.
- **`--no-check` fast path and `--scope` filter**: **goal-based**, exercised by a
  real-subprocess invocation — the column set and scope filtering are observable
  in stdout.
- **`--check-drift` column**: **TDD** — a tmp file edited away from its recorded
  SHA classifies Tier-2 and surfaces in the drift count.
- **Multi-adapter disambiguator enrichment** (upgrade, and the parallel diff /
  uninstall messages): **TDD** — assert the message names each adapter with its
  installed version.
- **Upgrade recap vocabulary** (`upgraded A→B` vs `re-applied … no changes` vs
  `re-applied … N kept as companions`): **TDD** — assert the recap string per
  case.
- **Upfront drift notice before confirm**: **TDD** — a state with one edited file
  produces the pre-confirm notice line.
- **CLI wiring and end-to-end**: **goal-based**, exercised by a real-subprocess
  invocation against a tmp install (per the project's "test the documented
  invocation, not a synthesised import" rule).

## Acceptance Criteria

- [x] `agentbundle list-installed` prints a deterministic table with columns
  PACK, ADAPTER, SCOPE, INSTALLED, LATEST, STATUS, covering every
  `(pack, adapter)` row across **both** user and repo scope by default.
- [x] `--scope user` / `--scope repo` filters the listing to that scope.
- [x] STATUS is `up-to-date` when installed == latest, `upgrade-available` when
  latest > installed, and `unknown` when the catalogue (or that pack's
  catalogue entry) can't be resolved or fails its spec-version gate.
- [x] When the catalogue is unresolvable, `list-installed` still lists every
  installed row (LATEST `—`, STATUS `unknown`) and exits 0 — it does not fail.
- [x] `--no-check` (alias `--offline`) skips catalogue resolution and prints the
  state-only columns (PACK, ADAPTER, SCOPE, INSTALLED) without LATEST/STATUS.
- [x] `--check-drift` adds a DRIFT column reporting, per row, the count of
  installed files whose on-disk SHA differs from the SHA recorded in state
  (Tier-2 / locally edited); `0` when clean.
- [x] With no packs installed at the selected scope(s), `list-installed` prints a
  clear "no packs installed" line and exits 0.
- [x] The upgrade multi-adapter disambiguator names each installed adapter **with
  its installed version**, e.g. `… pass --adapter to pick one: claude-code
  (0.9.0), codex (0.9.0)`; the parallel `diff` and `uninstall` disambiguators
  carry the same enrichment.
- [x] When upgrade changes the version, the recap reads
  `upgraded: <pack> @ <scope> <from> -> <to>`.
- [x] When the installed version already equals the catalogue version and the
  re-apply preserved no locally edited files (no `*.upstream` companions dropped),
  the recap reads `re-applied: <pack> @ <scope> <version> (already current)` — it
  never prints `upgraded: … X -> X`. (The recap does not claim "no changes":
  the walk re-writes bundle-owned files unconditionally, so the honest signal is
  "already at this version, no local edits preserved", not "nothing touched disk".)
- [x] When a same-version re-apply preserves locally edited files, the recap names
  the count kept as `*.upstream` companions (e.g.
  `re-applied: <pack> @ <scope> <version> — N file(s) had local edits, kept as
  .upstream companions`).
- [x] The same-version confirm prompt replaces the bare "repairs local drift"
  text with a plain description of what re-applying does and that local edits are
  preserved (e.g. `… is already at <version>. Re-apply to restore missing or
  reset unmodified bundle files? Your local edits are preserved as .upstream
  companions. [y/N]`).
- [x] Before a **whole-pack** upgrade confirm (both the version-change and
  re-apply prompts), when one or more installed files have local edits, the CLI
  prints an upfront notice naming the count that will be preserved as companions;
  the notice is computed from on-disk-vs-state SHAs (no catalogue render required)
  and is suppressed when the count is zero. A per-primitive upgrade
  (`--skill`/`--agent`/…) re-applies only that primitive's files, so the
  whole-pack notice is deliberately not printed there (a whole-pack count would
  mislead a single-primitive run).
- [x] `agentbundle list-installed --help` documents the command and its flags;
  the PyPI README (`packages/agentbundle/README.md`) and
  `docs/product/changelog.md` record the new command and the upgrade-messaging
  change; `pyproject.toml` version and `agentbundle/version.py` `CLI_VERSION` are
  bumped together to 0.10.0.

## Assumptions

- Technical: state files live at user `~/.agentbundle/state.toml` and repo
  `<root>/.agentbundle-state.toml` (source: `commands/upgrade.py:246-249`,
  `scope.py`).
- Technical: `State` exposes per-`(pack, adapter)` rows via `state.packs`, and
  `PackState` carries `installed_version`, `scope`, `source`, `install_route`,
  `files` (with `PackState.file_sha(relpath)`) — `list-installed` reads this API
  with no schema change (source: `config.py:119-201`).
- Technical: drift = on-disk SHA ≠ recorded SHA (Tier-2). `safety.classify`
  computes this against `state.shas_for` — the SHA set across *all* rows — so a
  per-row drift count compares against the row's own `PackState.file_sha`
  instead; `pack.toml` carries no per-file SHAs (source: `safety.py:76-119`,
  `config.py:143`; `grep sha packs/architect/pack.toml` → none).
- Technical: "latest" version is the catalogue pack's `pack.toml` `version`,
  resolved via `resolve_catalogue` + `resolve_catalogue_uri` (the four-layer
  chain), which may be a remote `git+https` URI requiring network (source:
  `commands/list_packs.py`).
- Technical: the upgrade multi-adapter disambiguator returns before the from→to
  computation, and the `upgraded: A -> B` recap is unconditional even for a
  same-version re-apply (source: `commands/upgrade.py:184-190, 291-317,
  734-738`).
- Technical: runtime is Python ≥3.11; agentbundle is at 0.9.0, with the version
  pinned in both `pyproject.toml` and `agentbundle/version.py` `CLI_VERSION`
  (source: `pyproject.toml`, `version.py:17`).
- Process: a new/changed shipped CLI surface is Surfaced as a PLAN decision with
  its release implication; the version bump touches `pyproject.toml` +
  `CLI_VERSION` + the PyPI README + the changelog (source: AGENTS.md; user
  confirmation 2026-06-30).
- Process: this is a structural / public-interface change → work-loop full mode
  (source: AGENTS.md risk triggers).
- Product: command name is `list-installed`; the up-to-date check runs by default
  and degrades to `unknown` offline with a `--no-check`/`--offline` fast path;
  drift is opt-in via `--check-drift`; both scopes show by default; the
  multi-adapter case enriches the message only (upgrade stays one adapter per
  invocation, no all-adapters mode); the version bump rides the implementing PR
  (source: user confirmation 2026-06-30).
