# The derived catalogue

> What `agentbundle catalogue init --preset self-hosted` copies out of an
> upstream catalogue, what it deliberately leaves behind, and what the adopter
> owns afterwards. For taking *later* upstream changes, read
> [`upstream-sync.md`](upstream-sync.md).

A derived catalogue is a second catalogue built from a first one. The adopter
gets their own `catalogue.toml`, their own pack tree, and their own identity —
then edits it. It is a copy with a new name, not a fork and not a mirror.

The command is `agentbundle catalogue init --preset self-hosted --source <path>`.
The implementation is
[`catalogue_tooling/initialise_self_hosted.py`](../../../packages/agentbundle/agentbundle/catalogue_tooling/initialise_self_hosted.py).

## What gets copied

Selection is by default inclusive. With no `--pack`, `--profile`, or `--adapter`
flags, `select_packs` returns every directory under `packs/` except tooling
packs (`catalogue-curation`) and `_`-prefixed ones. Measured against this
repository on 2026-09-14: **21 packs and 3 profiles** — 24 pack directories
less `catalogue-curation` and the two `_`-prefixed ones, and the three
top-level `profiles/*.toml` files.

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
name-matched exclusion removes build residue at any depth, because
`_collect_dir_bytes` walks the filesystem rather than the git index — without
it, `__pycache__/*.pyc` would carry a real username and absolute filesystem
path into the adopter's repository, which the privacy convention forbids.

Guide granularity is all-or-nothing. `guides/_shared/` moves as one unit; there
is no per-guide flag.

## What is not copied

`docs/`, `contracts/`, `tools/`, `web/`, and `packs/catalogue-curation/`
(outside vendored mode) stay upstream. The derived tree is a filtered subset,
and which filter produced it is knowledge that lives only in the init
invocation — not in the tree.

## How credbroker reaches a derived catalogue

Two ways, both keyed to one flag-free condition: the `credential-brokers` pack
being selected. The runnable copy rides inside the pack. The package source
that generates that copy is copied alongside it, so the projection that keeps
the two in step keeps working downstream.

[`build/user_libs.py`](../../../packages/agentbundle/agentbundle/build/user_libs.py)
projects `packages/credbroker/credbroker/` byte-faithfully into
`packs/credential-brokers/.apm/user-libs/credbroker/`, a committed target that
is drift-gated like the `adapter-root-bins` staging beside it. Because init
copies each selected pack's whole `.apm/` tree, an adopter who takes
`credential-brokers` takes credbroker with it. It is delivered as a `sys.path`
*floor* at `~/.agentbundle/lib/credbroker/` — a pip-installed `credbroker` in
site-packages always wins; the floor answers only when nothing else did.

The four packs that depend on it — `atlassian`, `figma`, `linear`, and
`credential-brokers` itself — declare the requirement in per-skill
`requirements.txt` files (`credbroker>=0.5.0` at the highest floor), and
`linear` also declares a `[pack.dependencies.required]` edge on
`credential-brokers`. There is no machine-readable edge from any pack to the
`credbroker` *library version*.

### Why credbroker source follows its pack

`user_libs._package_source_dir` resolves the source of truth by relative path:
`packs_dir.parent / "packages/credbroker/credbroker"`, that is
`<catalogue-root>/packages/credbroker/credbroker/`. A derived tree must carry
the package at exactly that path or the resolver finds nothing.

So init copies `packages/credbroker/` into the target whenever the
`credential-brokers` pack is selected, in **both** tooling modes — an
external-tooling adopter running `catalogue self-host` needs the resolver to
land just as much as a vendored one. Two details keep the copy in shape:

- The destination is derived from the resolver's own constant
  (`_USER_LIBS_PACKAGE_DIR = PACKAGE_SUBPATH.parent.as_posix()`) rather than
  re-spelled, so the copy follows the resolver if that path ever moves.
- `tests/` is excluded, matching `user_libs.collect_sources`, which already
  skips `tests` subtrees. The drift gate therefore compares the same file set
  on both sides, and the exclusion costs it nothing.

Absent the package, `compute_projections` returns an empty list and **both**
consumers become silent no-ops: `apply_projection` writes no
`.agentbundle/lib/credbroker/` floor, and `check_drift` compares nothing and
reports clean. The `.apm/user-libs/credbroker/` copy still arrives with the
pack either way, so credbroker would keep **running** — as frozen content with
no source and no drift signal, the shape that hides a change rather than
announcing it. `tests/conformance/`, the four-file suite init copies, has no
user-libs coverage to catch that difference. Init emits a diagnostic when the
source directory is missing, naming that outcome rather than passing quietly.

This is deliberately **not** the `packages/agentbundle/` treatment.
`packages/agentbundle/` is vendored to `.agentbundle/tooling/agentbundle/`
because it is an *install source* the adopter `pip install -e`s. credbroker is
a *build input resolved by relative path*. Same principle, different mechanics:
the two paths are not interchangeable and **must not be reconciled**. The
shipped code carries that warning as a comment on `_USER_LIBS_PACKAGE_DIR`, for
the same reason it appears here.

## Identity and the leak boundary

`--attribution white-label` rewrites upstream identity anchors throughout the
copied bytes; `--attribution attributed` permits upstream identity in two
declared surfaces only, `catalogue.toml` and `ATTRIBUTION.md`.

The transform runs **in memory, before any write**. A leak check then verifies
the transformed bytes in a temporary directory, and violations fail the run
with nothing written — so `--dry-run` surfaces the same violations a real run
would. This ordering is why white-label safety does not depend on cleanup.

**The leak check has a structural blind spot, and that part is deliberate.**
The check scans only the planned byte map. The state file at
`.agentbundle/self-host-state.json` is written four steps later, is never in
that map, and so is never scanned. That is still true. Bringing the state file
inside the check would make a usable pin impossible in the very mode that most
needs control over what ships, so the scope stays as it is.

What closed is the one leak that ran through it. `source_pack_identity` used to
be assigned from the upstream catalogue's `name` unconditionally — the exact
string white-label mode bans everywhere else in the tree, sitting in a file the
adopter commits and ships. `_source_pack_identity(source_meta, cfg)` now
decides the value: the source catalogue's name under `attributed`, where
attribution makes no promise of anonymity, and the **derived** catalogue's name
otherwise. The branch tests for `attributed` rather than for `white-label`, so
any other attribution mode added later fails closed to the non-disclosing
value.

The blind spot therefore still bounds what may be written there: any future
field in this file has to be safe on its own, because no control will check it.
See [`state.md`](state.md) for the field-level shape, and
[`upstream-sync.md`](upstream-sync.md) § White-label pins carry no upstream
identity for the pin fields a later phase adds under the same constraint.

## What a re-run does today

Re-running `init` at an existing target is the only update path that exists,
and it is not safe for a tree the adopter has edited:

- **Managed files are overwritten unconditionally**
  (`initialise_self_hosted.py:1145`). No hash is compared, no companion is
  written, nothing is reported. Adopter edits are lost.
- **One unmanaged file aborts the whole run** (`:1137`). `classify_conflicts`
  runs over every planned file absent from the ownership state, and any
  pre-existing one is a `CONFLICT` that fails the command.
- **Stale removal disagrees with both.** `_remove_stale_owned_paths` compares
  the recorded `sha256` and skips any file whose content moved, so deletion
  respects adopter edits while updating does not.
- **The recipe is not remembered.** State records adapters but not the selected
  packs, profiles, guides mode, attribution mode, or identity fields.
  `collect_fields` re-derives identity from the *source*, so a re-run with
  fewer flags rewrites the adopter's `catalogue.toml` from upstream defaults.
- **The source is local-only.** `commands/catalogue_init.py:202` does
  `Path(source_raw).resolve()`. The URI forms `resolve_catalogue()` already
  supports are unreachable from `init`.

[`upstream-sync.md`](upstream-sync.md) is the planned answer to all five.
