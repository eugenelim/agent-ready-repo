# AgentBundle

`agentbundle` is the catalogue engine and CLI. It reads pack source, builds
package artifacts through declared distribution routes, and installs, upgrades,
and removes adapter projections in an adopter's tree. Every install is recorded
in a per-scope state file, and every later write is checked against that record.

A file the CLI projected and the adopter has not touched may be overwritten, an
edited one gets a `.upstream.<ext>` companion, and a file the state does not
name is never touched. Pack source under `packs/` stays the only authoring
input; generated output is rebuilt from it.

This page covers the CLI surface, install and upgrade, install state, and
install-time configuration. Catalogue source, trust, and derivation live in
[`catalogue/`](catalogue/README.md); route declarations live in
[`distribution-routes.md`](distribution-routes.md); the state file fields live in
[`catalogue/state.md`](catalogue/state.md).

## 1. Surface and ownership

**The CLI has 23 top-level verbs, grouped by what they touch.** Read-only
inspection: `list-packs`, `list-profiles`, `list-targets`, `list-installed`,
`show`, `docs`, `diff`, `reconcile`, `validate`. Install lifecycle: `install`,
`upgrade`, `uninstall`, `init-state`, `adapt`, `scaffold`.

Configuration:
`config`, `pack-config`, `oplog`. Build and catalogue authoring: `render`,
`package-catalogue`, `lint`, `pack` (evals), and `catalogue`, whose subcommands
are `lint`, `verify`, `build`, `self-host`, `package`, `sync-defaults`, `init`,
`sync`, `index`, and `contracts`.[^1]

**Each piece of state has one writer.**

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Pack source | `packs/<pack>/` | Pack maintainers | Build, lint, install |
| Portable contracts | `contracts/`, bundled copy in `agentbundle/_data/` | Contract maintainers | Validators, build, install (bundled copy only) |
| Projection output | `dist/`, `.claude/`, `.codex/`, `.agents/` | `catalogue build`, `catalogue self-host` | Install routes, agent runtimes |
| Install state | One file per scope (§ 2) | `install`, `upgrade`, `uninstall`, `init-state` | `list-installed`, `show`, `diff`, `reconcile`, `upgrade` |
| Derivation state | `.agentbundle/self-host-state.json` | `catalogue init --preset self-hosted` | A later `init` run |
| Adaptation marker | `.adapt-install-marker.toml` | `install`; `install-marker.py` on plugin and APM routes | `core` session-start hook, `adapt-to-project` |
| Adopter layout config | `agentbundle-layout.toml` | The adopter; `install` appends one section (§ 7) | Consuming skills, workspace MCP |
| Pack user config | `<pack dir>/config.toml` | `pack-config set` | `load_pack_config` |

**Consumer commands never write catalogue source.** `install`, `upgrade`, and
`uninstall` write their target, state, and permitted configuration only.[^2]

[^1]: `packages/agentbundle/agentbundle/cli.py` — `main` parser construction, `catalogue` sub-parsers.

[^2]: `packages/agentbundle/agentbundle/safety.py` — module docstring on `write_jailed` and `write_files_no_follow`.

## 2. Install state

**State is recorded per scope.** A scope is where an install lands. The three
state files and the schema-version rule are in
[`catalogue/state.md`](catalogue/state.md#install-state); the scope semantics are
here.[^3]

- `repo` — committed with the repository. The default. Seeds and the adaptation
  marker are delivered here.
- `user` — the adopter's home. The state directory is created `0700`; the CLI
  refuses when it is a symlink or not a directory.
- `local` — this clone only, never committed. Files are hidden from git through
  an exclude block; the CLI refuses when a target path is already tracked and
  writes no marker and no layout section.

**A row is keyed by `(pack, adapter)`.** One pack can hold several adapter rows
at one scope. Each row records the installed version, the SHA-256 of every file
it projected, and provenance (§ 3).

Ownership of a path is derived by scanning
rows; a path co-owned by several rows carries an identical SHA. Adapter orphan
sweeps share the schema refusal, because an unreadable state file would
otherwise read as "nothing is owned" and delete every installed skill.[^4][^5]

**Writes follow the Tier contract.** For each projected path, the CLI compares
the on-disk SHA with the recorded one:

- Tier 1 — recorded and unchanged, or absent from disk: the CLI writes it.
- Tier 2 — recorded and edited by the adopter: the CLI writes a
  `<stem>.upstream.<ext>` companion and leaves the file.
- Tier 3 — not recorded under any pack: never touched.

`install` classifies its own incoming projection with `_classify_for_install`
rather than `safety.classify`, because on a first install every path is
unrecorded and would otherwise read as Tier 3.[^6]

**Concurrent writers are serialized for the main install path only.** `install`
and direct install persist state through `persist_state_locked`, which re-reads
the latest state under a cross-process lockfile so two simultaneous installs of
different adapter rows both land. Four writes bypass it: the legacy dist-tree
clean-up write in `install`, `init-state`, `upgrade`, and `uninstall` serialize
the state they loaded earlier, so a concurrent writer can lose an update
(§ 4).[^7]

[^3]: `agentbundle/scope.py` — `LEGAL_SCOPES`; `commands/_common.py` — `resolve_state_path`; `commands/install.py` — `_local_preflight_refusal`.

[^4]: `agentbundle/config.py` — `PackState`, `State.owners_of`; `agentbundle/scope.py` — `LEGAL_SCOPES`.

[^5]: `agentbundle/config.py` — `load_state`, `StateFileLegacy`, `SUPPORTED_STATE_SCHEMA_VERSIONS`; `build/adapters/_sweep_guard.py` — `refuse_unreadable_state`.

[^6]: `agentbundle/safety.py` — `Tier`, `classify`, `companion_path`; `commands/install.py` — `_classify_for_install`.

[^7]: `agentbundle/statelock.py` — `persist_state_locked`; callers in `commands/install.py` and `direct_install.py`; unlocked `dump_state` writes in `commands/install.py` (legacy dist-tree clean-up), `commands/init_state.py`, `commands/upgrade.py`, and `commands/uninstall.py`.

## 3. Sources: where a pack or skill comes from

**An install names its source one of three ways, and only the catalogue chain
has defaults.**

| Source | Form | Used by |
| --- | --- | --- |
| Catalogue directory | local path | `install --pack`, `--profile`, `upgrade` |
| Catalogue archive | `git+https://`, `catalogue+https://`, `archive+https://…#sha256=<digest>` | same |
| Direct skill or pack | local directory or `git+https://` GitHub source | `install <source>`, `upgrade --skill` |

**When the catalogue argument is omitted, a five-layer chain resolves it, first
match wins:** the explicit argument verbatim; the user `[settings].source`
value; the packaged org Artifactory bootstrap (fails closed when enabled and
malformed); an editable install's PEP 610 location; the packaged
`_data/install-defaults.toml` default. The chain writes nothing, never falls
back to the working directory, and never reads a repository-committed source.
`AGENTBUNDLE_NO_REMOTE` skips layers 3 and 4.[^8]

**Archive sources carry provenance into state.** For `catalogue+https://` and
`archive+https://` sources each row records `artifact_uri`, `archive_sha256`,
and `source_revision`; a local directory records none. Direct rows record
`source_kind`, `source_path`, and `source_digest` instead.[^9]

**STATUS: PLANNED — default-source integrity.** The packaged default is a
`git+https` reference to a mutable branch tip, and no post-acquisition check
binds the fetched archive to a commit. Resolving the branch to a commit SHA and
verifying the archive digest is owned by
[`convenient-install-defaults-followons`](../product/intents/convenient-install-defaults-followons.md).

[^8]: `agentbundle/source_defaults.py` — `resolve_default_source`; `agentbundle/_data/install-defaults.toml`.

[^9]: `agentbundle/config.py` — `PackState` provenance fields; `agentbundle/https_catalogue.py`; `agentbundle/direct_source_state.py`.

## 4. Install

**`install` runs every precondition for every scope before it writes any
scope.** A user-scope refusal after a repo write would leave a half-applied
install, so the order is resolve, check, write.[^10]

1. Resolve the catalogue source and locate the pack; refuse an incompatible
   contract version.
2. Resolve scope: CLI flag, then the pack's `default-scope`, then `repo`; refuse
   a scope outside `allowed-scopes`.
3. Load state at both scopes. Refuse when the pack is already installed at the
   requested scope (use `upgrade`), or at the other scope without `--force`.
4. Check `[pack.dependencies.required]` against installed names and version
   ranges.
5. Resolve the target adapter (§ 5), build one plan per scope, and render the
   projection.
6. For user scope, apply Rails A, B, and C: a pack that allows user scope may
   not ship `seeds/`, hook primitives, or `<adapt:…>` markers.
7. Probe every projected path against the path jail.
8. Write through `write_jailed`, then persist state under the state lock.
9. Append the layout section (§ 6) and write the install marker, for non-local
   scopes only.
10. Chain `adapt` in process at repo scope, print `installed:` lines (repo
    first), and emit the first-value handoff.

**`install --profile` is a batch over the same path.** A profile (`profiles/*.toml`)
declares one scope and an ordered pack list. The orchestrator runs each pack's
dry-run preflight for every pack, then writes in declared order; it reimplements
no write logic.

Three profiles ship: `full-ceremony` (repo scope),
`inception` and `solution-architect` (user scope). Profiles are read by the CLI
only; package routes never read them.[^11]

**Direct install takes a skill or pack from a repository the adopter chooses.**
The source is a skill folder, a `skills/` collection, or a direct pack, from a
local path or a credential-free GitHub archive. A narrower admission profile
than a catalogue pack's runs first.

The adopter then sees the declared
capability surface (`allowed-tools`, boundaries, credentialed flags, digests),
framed as publisher-supplied data and marked "admissible—not safe", and the
install refuses without confirmation. Rows land in schema `0.5` state with
per-file SHA-256 digests and source coordinates.[^12]

**Install does not lint the pack before rendering.** The route validates
metadata shape, rails, and the path jail, but `lint_pack` is not part of the
install path; `validate` and `catalogue lint` are the pre-publish gates.[^13]

**STATUS: PLANNED — install integrity.** Four gaps are open, each owned by
[`agentbundle-install-integrity`](../product/intents/agentbundle-install-integrity.md):
required dependencies match on name and version without catalogue identity;
dependency checks union repo and user state, so a repo-scope dependency can
satisfy a user-scope consumer that cannot reach it; `upgrade`, `uninstall`,
`init-state`, and one `install` clean-up write bypass the state lock; and install renders before `lint_pack`.
[`agentbundle-install-artifact-layout`](../product/intents/agentbundle-install-artifact-layout.md)
owns a YAML-merge conflict mode for shared policy files, which does not exist.

[^10]: `agentbundle/commands/install.py` — module docstring, `_run` step comments.

[^11]: `agentbundle/commands/install.py` — `_run_profile`; `agentbundle/commands/profile.py`; `profiles/`.

[^12]: `agentbundle/direct_source.py`, `direct_install.py` — `capability_block`, `ADMISSIBILITY_VERDICT`; `direct_source_acquisition.py`.

[^13]: `agentbundle/commands/install.py` — no `lint_pack` reference; `agentbundle/build/scope_rails.py`.

## 5. Which adapter and which scope an install targets

**Eight adapters are declared** in `contracts/adapter.toml` and implemented
under `build/adapters/`; `kiro` is a deprecated alias of `kiro-ide`. The adapter
set and its relation to routes are in
[`distribution-routes.md`](distribution-routes.md#3-routes-and-runtime-adapters-are-separate-layers).
Projection mechanics live under `build/projections/`; a projection may not
import an adapter, and neither layer may be imported by pack source or by a
target-runtime file.[^14]

**`_resolve_target_adapter` applies one ordered lookup.** The first step that
yields an adapter wins; an inadmissible value refuses rather than falling
through, except in step 2.[^15]

0. *Drift refusal.* Where a pack declares `allowed-adapters`, the list is
   checked against the contract's shipped set (and, at user scope, the
   user-capable set) first, so neither `--adapter` nor the state hint can carry
   a no-longer-shipped adapter through. It refuses on the first miss.
1. `--adapter` override, validated against the pack's list and the scope's
   admissible set.
2. The adapter recorded in state, when admissible; otherwise the lookup
   continues and `upgrade` refuses a cross-adapter change.
3. User configuration (`agentbundle config set adapter`), only when no state
   adapter exists. It refuses when the configured adapter is not admissible at
   the scope or not in the pack's list.
4. The org `preferred_adapter` from the packaged `_data/install-defaults.toml`,
   under the same gate and refusals as step 3.
5. Scope default for a pack that declares `allowed-adapters`: user scope walks
   a per-adapter probe table and the first match wins; repo scope does not
   probe and takes the default adapter when the pack admits it, otherwise the
   first entry in `allowed-adapters`.
6. A repo-scope pack that declares no `allowed-adapters` and predates contract
   `0.7` falls to the legacy heuristic; a newer one returns the default
   adapter.

**Hook-wiring drop behaviour is decided per adapter.** Whether an incompatible
hook-wiring file is dropped, passed through, or fails the render, how malformed
TOML is handled, and the stage at which it is detected are set in
`build/adapters/<adapter>.py` and the `build/projections/` mergers.
`commands/_drop_warning.py` composes the install warning.[^15]

[^14]: `contracts/adapter.toml`; `tools/lint-adapter-layer-boundary.py` (fixes the projection-to-adapter direction).

[^15]: `agentbundle/commands/install.py` — `_resolve_target_adapter`, steps 0 to 5 in its body, including the user-config and org-hint steps its docstring omits; `agentbundle/commands/_drop_warning.py`; `agentbundle/build/adapters/`; `agentbundle/build/projections/`.

## 6. Upgrade and uninstall

**`upgrade` takes four shapes, selected by flags.**

| Shape | Selector | Behaviour |
| --- | --- | --- |
| Whole pack | `--pack` | Re-renders from the resolved catalogue and applies the Tier contract. Target version is the catalogue's `[pack] version`; there is no `--to`. |
| One primitive | `--pack` with `--skill`, `--agent`, `--hook`, `--seed`, or `--command` | Applies the Tier contract to that primitive's files and records `primitive_versions`; `installed_version` is unchanged. |
| Bulk | `--all --scope <scope>` | Classifies every row (`up-to-date`, `upgrade-available`, `ahead`, `unknown`), prints a plan table, confirms, applies. Rejects `--adapter` and a catalogue argument. |
| Direct skill | `--skill <name>` with no `--pack` | Re-resolves the recorded source (or `--source`), re-runs admission, previews the file plan, replaces the projection, deletes owned files the new revision no longer ships. Refuses a revision that widens a declared capability axis. Repository and user scope. |

An install that names a different revision of an installed direct skill is
refused as a different source (`CAT-D009`); the revision moves through
`upgrade`.[^16]

**Whole-pack upgrade does not remove files the new projection stopped
shipping.** Only the direct-skill route deletes superseded owned files. After an
adapter changes its projection shape, a pack upgrade leaves the old owned file
in place; uninstall plus reinstall clears it.

**STATUS: PLANNED** — owned by
[`upgrade-orphan-removal-on-projection-shape-change`](../product/intents/upgrade-orphan-removal-on-projection-shape-change.md).
Capability re-consent for a widening direct upgrade, receipts, local-scope
upgrade, and an old-to-new capability delta are follow-ons recorded in
[`direct-skill-lifecycle`](../product/intents/direct-skill-lifecycle.md).

**`uninstall` removes only what state proves the CLI wrote.** It classifies each
recorded file: unchanged files (Tier 1) are removed; edited files (Tier 2) are
kept with a warning; unrecorded paths (Tier 3) are never touched. It then
unprojects owned hook wiring, prunes empty parent directories, and drops the
targeted adapter row.

It confirms first (`--yes` skips; a non-TTY refuses) and
`--dry-run` prints the plan without writing.[^17]

[^16]: `agentbundle/commands/upgrade.py` — module docstring, `_validate_route_grammar`, `_run_all`, `_classify_row`, `_run_direct_skill`; `agentbundle/direct_install.py` — `_delete_removed_projection`; `agentbundle/direct_source.py`.

[^17]: `agentbundle/commands/uninstall.py` — module docstring.

## 7. Install-time configuration

**Two mechanisms put defaults in an adopter's hands, and they are separate.**
The layout default places an output directory. The pack-defaults cascade carries
catalogue-operator configuration to pack code.

### 7.1 The install-time layout default

**`install` appends at most one section to an adopter-owned file and never
creates or overwrites one.** `_append_layout_section` runs once, from `install`
only (not `upgrade`, not local scope). A pack declares both halves:

```toml
[pack.layout.repo]
section    = "design"
output_dir = "docs/design"
```

The section name is declared rather than derived (`experience-design` writes
`[design]`, `desk-research` writes `[research]`). Six packs declare
`[pack.layout.repo]` — `architect`, `desk-research`, `experience-design`,
`product-engineering`, `product-strategy`, `repo-governance` — and none declares
`[pack.layout.user]`. `tests/conformance/test_pack_layout_declared_section.py`
compares each declared pair against the pairs the pack's own reference docs
state.[^18]

**The append is byte-preserving and best-effort.** It parses a throwaway copy
only to decide occupancy, then writes the original bytes plus one table, so
comments, key order, quoting, line endings, unknown keys, and file mode survive
the atomic replace. It never raises and never fails the install: a layout
problem is reported and the install completes.

**The install marker keeps a fatal handler.** `_append_install_marker` shares
the call site, but uninstall and `adapt` read what it writes. `output_dir` is
catalogue-sourced, so it is confined to the same root as the write jail for that
scope, and `section` carries the pack-name character class.[^19]

**A default install creates no layout file.** Two routes create one: the adopter
by hand, or a consuming skill on consent, which scaffolds its own section.
`_append_layout_section` only maintains an existing file.[^20]

**Reachability decides which tier a session can read.** A session rooted in a
repository reads `./agentbundle-layout.toml` without a grant.
`~/.agentbundle/agentbundle-layout.toml` is outside the working root, so an
ordinary repository session cannot read it unless granted, and resolution falls
past it.

Hand-off paths (`docs/product/briefs/`, `docs/product/intents/`) are
pinned by the skills that read them, not by this file.

**A pack's `output_dir` enters resolution only once written into the adopter's
file.** Layout resolution follows RFC-0096 § 4, which has no pack-default tier
([ADR-0120](../adr/0120-layout-config-resolution-follows-rfc-0096.md)).

### 7.2 Pack-defaults cascade

**`load_pack_config(pack)` merges two layers, user over baked.** The baked layer
is `[pack-defaults.<pack>]` from `catalogue.toml`, written into the packaged
`_data/install-defaults.toml` by `catalogue sync-defaults`. The user layer is
`<pack dir>/config.toml`, edited with `pack-config set`.

Merge is shallow; a
malformed user file warns and yields the baked layer.[^21]

**The baked layer is reachable only by importing `agentbundle`.** Pack scripts
that are standard-library-only cannot read it, and the installer projects it
nowhere. This catalogue bakes no `[pack-defaults]`.

**STATUS: PLANNED** —
one installer projection serving both credential packs and telemetry is owned by
[`credential-pack-defaults-projection`](../product/intents/credential-pack-defaults-projection.md)
and its consumer
[`catalogue-level-telemetry-endpoint-default`](../product/intents/FEAT-0017-catalogue-level-telemetry-endpoint-default.md).

The projected file stays untrusted catalogue configuration and cannot supply a
sign-in destination or authentication default.

[^18]: `agentbundle/commands/install.py` — `_append_layout_section`; `packs/*/pack.toml` `[pack.layout]`; `docs/specs/layout-install-sections/spec.md`.

[^19]: `agentbundle/commands/install.py` — `_append_layout_section`, `_append_install_marker`.

[^20]: [RFC-0040](../rfc/0040-consolidated-pack-layout-config.md) — creation routes; [ADR-0030](../adr/0030-consolidated-pack-output-layout-contract.md) D9, D10.

[^21]: `agentbundle/config.py` — `load_pack_config`, `pack_dir`; `agentbundle/commands/pack_config_cmd.py`; `agentbundle/commands/catalogue_sync_defaults.py`.

## 8. Build and distribution

Build code never names a route. Route dispatch, route modules, build order, and
the steps to add a route are in
[`distribution-routes.md` § 2](distribution-routes.md#2-build-dispatch-reads-the-contract-route-code-lives-in-three-modules).

## 9. Evidence and invariants

**Inspection commands answer from state and disk.** `list-installed`, `show`,
`diff`, `reconcile`, and `validate` report installed state, source content,
projection drift, orphaned user-scope configuration, and conformance. `reconcile`
reports and applies nothing.

`adapt` reports upstream companions instead of
overwriting them. Install emits one composed warning per root, pack, adapter,
and scope. Lint exits non-zero only on an ERROR finding; a WARN-only run exits
zero.

**These checks hold the contract mechanically.**

- `agentbundle catalogue verify` checks projected artifacts and adapter
  conformance; the self-host drift gate raises `CAT-V-015` for source drift and
  `CAT-V-014` for generated `dist/` drift.
- `tools/catalogue/check_contract_parity.py` requires each contract in
  `contracts/catalogue-spec.toml` to match its `_data/` copy byte for byte. The
  CLI loads contracts only from `_data/`.
- `tools/check_distribution_route_decisions.py --check` reports shared build
  code that decides by route, by name or by contract-derived value; its `limits`
  list records what it does not follow. Golden tests pin complete APM, Claude,
  and Agent Plugin trees by path, bytes, link target, and mode.[^22]
- `tools/lint-adapter-layer-boundary.py` and `tools/lint-generated-path-ownership.py`
  hold the layer edge and one-producer-per-generated-path rules.

**Known gap: the per-target metadata constraints are declared but unenforced.**
`contracts/target-vocab.toml` sets metadata limits per target, and the strictest
applies. Only `build/lint_packs.py` `cmd_lint_packs` loads the vocabulary, and
no entrypoint reaches it: `make lint-packs` and `agentbundle lint packs` route to
`catalogue lint`, which calls `lint_pack(pack_dir)` without `constraints`, and
the `agentbundle.build lint-packs` shim also routes to `catalogue lint`.[^23]

[^22]: `packages/agentbundle/tests/build_pipeline/test_distribution_route_golden.py`; `tools/check_distribution_route_decisions.py`.

[^23]: `agentbundle/catalogue_tooling/lint.py` — `lint_pack` call; `agentbundle/build/lint_packs.py` — `lint_pack`, `cmd_lint_packs`; `agentbundle/build/__init__.py` — `_cmd_lint_packs_shim`; `Makefile` — `lint-packs`.

## 10. Governing decisions

- [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md) — per-pack install scope.
- [ADR-0030](../adr/0030-consolidated-pack-output-layout-contract.md) — pack output layout contract; D8 is superseded in part by ADR-0120.
- [RFC-0040](../rfc/0040-consolidated-pack-layout-config.md) — layout config creation routes.
- [RFC-0096](../rfc/0096-portable-delivery-artifact-lifecycle.md) — § 4 surface-resolution order.
- [ADR-0120](../adr/0120-layout-config-resolution-follows-rfc-0096.md) — which order governs layout resolution.

## 11. Last verified against commit

`3fe5f2760e516620182aad4a2aa4704bcd2d8bdd`
