# The derived catalogue

> What `agentbundle catalogue init --preset self-hosted` copies out of an
> upstream catalogue, what it deliberately leaves behind, and what the adopter
> owns afterwards. For taking *later* upstream changes, read
> [`upstream-sync.md`](upstream-sync.md).

A derived catalogue is a second catalogue built from a first one. The adopter
gets their own `catalogue.toml`, their own pack tree, and their own identity,
then edits it. It is a copy with a new name, not a fork and not a mirror.

`init` writes the copy once, records the recipe and an ownership map, and keeps
upstream identity out of white-label output. Re-running `init` is unsafe for an
edited tree, so later upstream changes arrive through `catalogue sync`.

The command is `agentbundle catalogue init --preset self-hosted --source <path>`.
The implementation is
[`catalogue_tooling/initialise_self_hosted.py`](../../../packages/agentbundle/agentbundle/catalogue_tooling/initialise_self_hosted.py).[^1]

## What gets copied

Selection is by default inclusive. With no `--pack`, `--profile`, or `--adapter`
flags, `select_packs` returns every directory under `packs/` except tooling
packs (`catalogue-curation`) and `_`-prefixed ones, and every top-level
`profiles/*.toml` file.[^3]

| Source | Target | Controlled by |
| --- | --- | --- |
| `packs/<name>/` | `packs/<name>/` | `--pack` (repeatable); all non-tooling packs by default |
| `profiles/<name>.toml` | `profiles/<name>.toml` | `--profile` (repeatable); all by default |
| `guides/_shared/` | `guides/_shared/` | `--guides selected`; `--guides none` copies nothing |
| `tests/conformance/` | `tests/conformance/` | always, in both tooling modes |
| `packages/credbroker/` | `packages/credbroker/` | selection of the `credential-brokers` pack, in both tooling modes; `tests/` excluded |
| generated | `catalogue.toml` | `--name`, `--display-name`, `--owner-*`, `--repository-url` |

Two more targets exist in `--tooling vendored` mode only:

| Source | Target |
| --- | --- |
| `packages/agentbundle/` | `.agentbundle/tooling/agentbundle/` |
| `packs/catalogue-curation/` | `.agentbundle/tooling/packs/catalogue-curation/` |

The vendored engine copy is **wheel-class, not a source tree**: the command
tells the adopter to `pip install -e` it, so `_VENDORED_ENGINE_EXCLUDE` prunes
`tests/`, `conftest.py`, and root-relative `build/` and `dist/`. A second
name-matched exclusion removes build residue at any depth. `_collect_dir_bytes`
walks the filesystem rather than the git index, so `__pycache__/*.pyc` files
would otherwise carry a real username and absolute path into the adopter's
repository.

Guide granularity is all-or-nothing. `guides/_shared/` moves as one unit; there
is no per-guide flag.

## What is not copied

`docs/`, `contracts/`, `tools/`, `web/`, and `packs/catalogue-curation/`
(outside vendored mode) stay upstream. The derived tree is a filtered subset,
and which filter produced it is knowledge that lives only in the init
invocation — not in the tree.

## How credbroker reaches a derived catalogue

Selecting the `credential-brokers` pack delivers credbroker twice: the runnable
copy rides inside the pack, and the package source that generates that copy is
copied alongside it, so the projection that keeps the two in step keeps working
downstream.

[`build/user_libs.py`](../../../packages/agentbundle/agentbundle/build/user_libs.py)
projects `packages/credbroker/credbroker/` byte-faithfully into
`packs/credential-brokers/.apm/user-libs/credbroker/`, a committed target that
is drift-gated like the `adapter-root-bins` staging beside it. Because init
copies each selected pack's whole `.apm/` tree, an adopter who takes
`credential-brokers` takes credbroker with it. It is delivered as a `sys.path`
*floor* at `~/.agentbundle/lib/credbroker/` — a pip-installed `credbroker` in
site-packages always wins; the floor answers only when nothing else did.

Four packs depend on it: `atlassian`, `figma`, `linear`, and
`credential-brokers` itself. They declare the requirement in per-skill
`requirements.txt` files. Floors run from none (`linear`) to `credbroker>=0.5.0`
(`atlassian` `jira` and `confluence-crawler`).

`atlassian`, `figma`, and
`linear` also declare a `[pack.dependencies.required]` edge on
`credential-brokers ^0.3`. No machine-readable edge links any pack to the
`credbroker` *library version*.[^4]

### Where the credbroker source lands

`user_libs._package_source_dir` resolves the source of truth by relative path:
`packs_dir.parent / "packages/credbroker/credbroker"`, that is
`<catalogue-root>/packages/credbroker/credbroker/`. Init therefore copies
`packages/credbroker/` into the target whenever the `credential-brokers` pack is
selected, in **both** tooling modes, because `catalogue self-host` needs the
resolver to land in either mode. Two details keep the copy in shape:

- The destination is derived from the resolver's own constant
  (`_USER_LIBS_PACKAGE_DIR = PACKAGE_SUBPATH.parent.as_posix()`) rather than
  re-spelled, so the copy follows the resolver.
- `tests/` is excluded, matching `user_libs.collect_sources`, which already
  skips `tests` subtrees. The drift gate therefore compares the same file set
  on both sides, and the exclusion costs it nothing.

Absent the package, `compute_projections` returns an empty list and **both**
consumers become silent no-ops: `apply_projection` writes no
`.agentbundle/lib/credbroker/` floor, and `check_drift` compares nothing and
reports clean. The `.apm/user-libs/credbroker/` copy still arrives with the
pack, so credbroker runs as frozen content with no source and no drift signal.
`tests/conformance/` has no user-libs coverage to catch that difference.

Init
emits a diagnostic when the source directory is missing.

The two packages take different paths. `packages/agentbundle/` is an *install
source* the adopter `pip install -e`s, so it lands in
`.agentbundle/tooling/agentbundle/`. `packages/credbroker/` is a *build input
resolved by relative path*, so it lands at `packages/credbroker/`.

## Identity and the leak boundary

`--attribution white-label` rewrites upstream identity anchors throughout the
copied bytes; `--attribution attributed` permits upstream identity in two
declared surfaces only, `catalogue.toml` and `ATTRIBUTION.md`.

The transform runs **in memory, before any write**. A leak check then verifies
the transformed bytes in a temporary directory, and violations fail the run
with nothing written — so `--dry-run` surfaces the same violations a real run
would. This ordering is why white-label safety does not depend on cleanup.

**The leak check has a structural blind spot, and it is deliberate.** The check
scans only the planned byte map. The state file at
`.agentbundle/self-host-state.json` is written after that check, so it is never
scanned.

Every field written there must therefore be safe on its own.

`source_pack_identity` follows that rule.
`_source_pack_identity(source_meta, cfg)` records the source catalogue's name
under `attributed`, where attribution promises no anonymity, and the **derived**
catalogue's name otherwise. The branch tests for `attributed` rather than for
`white-label`, so any attribution mode added later fails closed to the
non-disclosing value.

This section owns the rule. [`state.md`](state.md) owns the field-level shape,
and [`upstream-sync.md`](upstream-sync.md) § Pin records which pin fields the
rule omits.

## Re-running `init`

Re-running `init` at an existing target is not safe for a tree the adopter has
edited. `catalogue sync` is the supported update path.[^2]

- **Managed files are overwritten unconditionally.** The write loop over the
  owned plan compares no hash, writes no companion, and reports nothing.
  Adopter edits are lost.
- **One unmanaged file aborts the run.** `classify_conflicts` runs over every
  planned file absent from the ownership state, and any pre-existing one is a
  `CONFLICT` that fails the command.
- **Stale removal respects edits where updating does not.**
  `_remove_stale_owned_paths` compares the recorded `sha256` and skips any file
  whose content moved.
- **The recipe is remembered and read back.** State records the selected packs,
  profiles, and identity fields. `collect_fields` falls back to the recorded
  value for each one whenever the caller passes none, so a re-run with fewer
  flags keeps the adopter's selection. The attribution, tooling, and guides
  modes always resolve from an explicit flag or its safe default, never from the
  recorded recipe, so a recorded mode cannot reach a replay silently.
- **The source is local-only.** `commands/catalogue_init.py` resolves `--source`
  with `Path(...).resolve()`, so the URI forms `resolve_catalogue()` supports are
  unreachable from `init`.

[`upstream-sync.md`](upstream-sync.md) owns `sync`, the verb that answers these
failures without changing `init`.

[^1]: `catalogue_tooling/initialise_self_hosted.py` (`select_packs`, `_VENDORED_ENGINE_EXCLUDE`, `_TOOLING_PACKS`); `commands/catalogue_init.py`.

[^2]: `catalogue_tooling/initialise_self_hosted.py` (`classify_conflicts` call, `_remove_stale_owned_paths`, `collect_fields`, `_source_pack_identity`); `commands/catalogue_init.py`.

[^3]: `catalogue_tooling/initialise_self_hosted.py` (`select_packs`, `_TOOLING_PACKS`).

[^4]: `packs/atlassian/pack.toml`, `packs/figma/pack.toml`, `packs/linear/pack.toml` (`[pack.dependencies.required]`); `packs/*/.apm/skills/*/requirements.txt`; `build/user_libs.py` (`_package_source_dir`, `_USER_LIBS_PACKAGE_DIR`, `compute_projections`).
