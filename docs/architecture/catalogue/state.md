# Catalogue-tree state files

> Two different state files can sit in one tree. They answer different
> questions, are written by different commands, and do not read each other.

| File | Answers | Written by | Schema |
| --- | --- | --- | --- |
| `.agentbundle-state.toml` | Which packs are *installed* into this target, at what version, from where | `install`, `upgrade`, `uninstall`, `init-state` | `0.4` (catalogue route), `0.5` (direct route) |
| `.agentbundle/self-host-state.json` | Which files this tree was *derived from upstream*, the recipe used, and the available source pin | `catalogue init --preset self-hosted` | `3` |

A derived catalogue that also installs packs into itself carries both. Nothing
reconciles them; they describe different relationships.

## Install state — `.agentbundle-state.toml`

Keyed by `(pack_name, adapter)`, so one pack can carry several adapter rows at
one scope. Per-row fields relevant to provenance and safety:

```
installed_version   the pack version this row was installed at
files               {relpath: {sha: ...}} — the Tier contract's comparison basis
artifact_uri        resolved archive URL, or None for a local directory source
archive_sha256      verified digest of that archive, or None
source_revision     upstream revision from the channel descriptor, or None
```

The last three are populated for `catalogue+https://` and `archive+https://`
sources and are `None` for a local directory. They are the existing precedent
for pinning an upstream, and
[`upstream-sync.md`](upstream-sync.md) mirrors them by name rather than
inventing a second vocabulary.

Reading is a **hard refusal** on any unrecognised `schema-version`, on both the
denylist of known-legacy versions and an absent value. There is no best-effort
read.

`files[relpath].sha` is what `safety.classify` compares against disk to produce
a Tier-1, Tier-2, or Tier-3 verdict. That verdict decides whether a write
overwrites, lands as a `.upstream.<ext>` companion, or is refused.

## Derivation state — `.agentbundle/self-host-state.json`

Written after the identity leak check, so it is not part of the checked byte
map. That is deliberate and permanent: every value written here has to be safe
on its own, because no control will scan it.

```
schema_version        "3"
managed_paths         [{path, sha256}] — every file init wrote
adapters              the adapter set the derivation targeted
managed_target_path   the absolute target this state describes
source_pack_identity  under `attributed`, the upstream catalogue's name;
                      under any other attribution mode, the derived one's
source_root_kind      "self-hosted-source"
recipe.packs          selected pack names
recipe.profiles       selected profile names
recipe.guides         guide inclusion mode
recipe.attribution    attribution mode
recipe.tooling        tooling mode
recipe.name           catalogue identifier
recipe.display_name   human-readable catalogue name
recipe.description    catalogue description
recipe.owner_name     maintainer name
recipe.owner_email    maintainer email
recipe.preferred_adapter
                      preferred adapter
recipe.repository_url repository URL, or null
pin.source_revision   resolved source revision, or null
pin.archive_sha256    archive digest, or null
pin.synced_at         UTC time when init wrote the state
pin.source_uri        source URI, only under `attributed`
```

`_source_pack_identity` picks that value, branching on `attributed` rather than
on `white-label` so an attribution mode added later gets the non-disclosing
name by default.

`managed_paths` is the ownership boundary: a path in it is one init wrote, and
a path absent from it belongs to the adopter. `_remove_stale_owned_paths` is
the only consumer today. It removes a path that has left the plan **only** when
the recorded `sha256` matches disk — so an adopter-edited file is never deleted.

Schema-1 entries are permanently inert. `_migrate_managed_paths` converts
  a bare string path to `{path, sha256: None}`. A `None` hash cannot satisfy the
  removal guard, and cannot support a Tier comparison either, so such entries
  can be neither updated safely nor removed.

The recipe preserves the identity fields and pack and profile selections that a
later `init` reuses when those flags are omitted. Explicit flags still win. The
recorded mode fields are not replay inputs, so omitted mode flags use their
safe defaults.

`source_uri`, `source_revision`, and `archive_sha256` reuse `PackState`'s
provenance names deliberately — one vocabulary across both state files. A
local-path source has no resolved revision or archive digest, so both pin
values are null. Under `--attribution white-label`, `source_uri` is omitted;
the remaining pin fields do not identify upstream.

This file has no contract in [`contracts/`](../../../contracts/). It is defined
in code only.
