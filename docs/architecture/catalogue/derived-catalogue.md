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
repository: **25 packs and 7 profiles**.

| Source | Target | Controlled by |
| --- | --- | --- |
| `packs/<name>/` | `packs/<name>/` | `--pack` (repeatable); all non-tooling packs by default |
| `profiles/<name>.toml` | `profiles/<name>.toml` | `--profile` (repeatable); all by default |
| `guides/_shared/` | `guides/_shared/` | `--guides selected`; `--guides none` copies nothing |
| `tests/conformance/` | `tests/conformance/` | always, in both tooling modes |
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

`docs/`, `contracts/`, `tools/`, `web/`, `packages/credbroker/`, and
`packs/catalogue-curation/` (outside vendored mode) stay upstream. The derived
tree is a filtered subset, and which filter produced it is knowledge that lives
only in the init invocation — not in the tree.

`packages/credbroker/` is on that list by omission rather than by design, and it
has consequences the others do not — see § Gap below.

## How credbroker reaches a derived catalogue

Through the `credential-brokers` pack, not through `packages/`.

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

### Gap: the user-libs gate goes silent in a derived catalogue

`packages/credbroker/` is not copied in either tooling mode, and
`user_libs._package_source_dir` resolves its source of truth as
`packs_dir.parent / "packages/credbroker/credbroker"` — that is,
`<catalogue-root>/packages/credbroker/credbroker/`. In a derived tree that path
does not exist, so `compute_projections` returns an empty list and **both**
consumers become no-ops:

- `apply_projection` writes nothing, so `catalogue self-host` never produces the
  `.agentbundle/lib/credbroker/` floor staging that this repository commits.
- `check_drift` compares nothing and returns clean.

The module docstring names this outcome exactly: *"if the package source were
ever deleted, the gate goes silent."* A derived catalogue reaches it by
omission rather than deletion.

The `.apm/user-libs/credbroker/` copy still arrives with the pack, so credbroker
**runs**. What the adopter loses is every other property: they cannot regenerate
it, cannot patch it from source, and get no drift signal if they or an upstream
sync modify it. The copy is a generated projection upstream and frozen,
unmanaged content downstream — and `tests/conformance/`, the four-file suite
init does copy, has no user-libs coverage to catch the difference.

The agentbundle precedent resolves this. `packages/agentbundle/` is vendored to
`.agentbundle/tooling/agentbundle/` because it is an *install source* — the
adopter `pip install -e`s it. `packages/credbroker/` is a *build input resolved
by relative path*, so the equivalent move is to copy it to
`packages/credbroker/` in the target, where the existing resolver already looks.
That reactivates projection and drift gate with no code change. The natural rule
is that **credbroker source follows its pack** — copied whenever
`credential-brokers` is selected, independent of `--tooling` — because an
external-tooling adopter running `catalogue self-host` hits the same silent gate
as a vendored one. [`upstream-sync.md`](upstream-sync.md) carries this as a
decision, not an open question.

## Identity and the leak boundary

`--attribution white-label` rewrites upstream identity anchors throughout the
copied bytes; `--attribution attributed` permits upstream identity in two
declared surfaces only, `catalogue.toml` and `ATTRIBUTION.md`.

The transform runs **in memory, before any write**. A leak check then verifies
the transformed bytes in a temporary directory, and violations fail the run
with nothing written — so `--dry-run` surfaces the same violations a real run
would. This ordering is why white-label safety does not depend on cleanup.

**The leak check has a blind spot, and it is a live defect.** The check scans
only the planned byte map. The state file at
`.agentbundle/self-host-state.json` is written four steps later and is never in
that map, so it is never scanned — and it records `source_pack_identity`,
assigned from the upstream catalogue's `name`. That is the exact string
white-label mode bans everywhere else in the tree, sitting in a file the
adopter commits and ships.

The decided fix is the opaque-pin rule in
[`upstream-sync.md`](upstream-sync.md) § White-label pins carry no upstream
identity. See [`state.md`](state.md) for the field-level shape.

## What a re-run does today

Re-running `init` at an existing target is the only update path that exists,
and it is not safe for a tree the adopter has edited:

- **Managed files are overwritten unconditionally**
  (`initialise_self_hosted.py:1059`). No hash is compared, no companion is
  written, nothing is reported. Adopter edits are lost.
- **One unmanaged file aborts the whole run** (`:1051`). `classify_conflicts`
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
