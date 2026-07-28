# ADR-0059: Pack config uses a three-source cascade baked into `_data/install-defaults.toml` at catalogue build time

- **Status:** Accepted
- **Date:** 2026-07-28
- **Decision-makers:** eugenelim
- **Related:** [RFC-0074](../rfc/0074-pack-config-and-oplog.md), [RFC-0046 convenient-install-defaults](../rfc/0046-convenient-install-defaults.md), [ADR-0036 install-source precedence chain](0036-install-source-resolves-through-trusted-precedence-chain-no-repo-source-no-cwd.md)

## Decision summary

- **Decision:** Pack-source defaults and catalogue operator overrides are merged at catalogue build time (operator wins) and baked into `_data/install-defaults.toml [pack-defaults.<pack>]` sections, extending the RFC-0046 baking pipeline; user overrides in `<pack_dir>/config.toml` are merged at runtime by `load_pack_config`, producing the effective config as a two-layer runtime merge.
- **Because:** Runtime lookup of catalogue defaults requires the catalogue source to be reachable on every pack invocation — offline installs fail and latency is added on every call; baking at build time is offline-safe, zero-latency, and extends the established `install-defaults.toml` pattern.
- **Applies to:** `catalogue.toml` schema, `_data/install-defaults.toml`, `agentbundle/catalogue_tooling/defaults.py` (`compile_defaults`, `check_defaults`), `agentbundle/config.py` (`load_pack_config`), and all future pack capabilities that need catalogue-operator-configurable defaults.
- **Tradeoff accepted:** The baked layer cannot distinguish "pack-source default" from "catalogue operator override" at runtime — both are visible only as "baked default" in `pack-config show`. `compile_defaults` must emit alphabetically sorted pack names and keys to preserve `check_defaults`'s byte-stable drift detection.
- **Revisit if:** A use case arises requiring runtime distinction between pack-source defaults and catalogue-operator overrides (e.g. an "undo operator override" operation), at which point the two sources should be stored as separate sections in `install-defaults.toml`.

## Context

Pack scripts need site-specific configuration (base URLs, project keys, workspace IDs) that catalogue operators know at build time. The question is when and where those operator-supplied values are resolved.

RFC-0046 established `_data/install-defaults.toml` as the mechanism for baking catalogue-level defaults into the agentbundle package — the installer's preferred adapter, the default install source, and (via ADR-0036) the install-source precedence chain. This decision extends the same mechanism to per-pack configuration.

The three sources in precedence order (lowest to highest):

1. **Pack-source defaults** — declared by the pack author as the baseline for their pack; merged first.
2. **Catalogue operator overrides** — declared in `catalogue.toml [pack-defaults.<pack>]` sections; override pack-source defaults; merged at build time.
3. **User overrides** — stored in `<pack_dir>/config.toml`; override both baked layers; merged at runtime.

Sources 1 and 2 are merged by `compile_defaults` at catalogue build time and written as a single `[pack-defaults.<pack>]` section in `_data/install-defaults.toml`. This is the "baked layer". Source 3 is the "user layer". `load_pack_config` performs the final two-layer merge at runtime.

## Decision

`compile_defaults` is extended to:

1. Read `[pack-defaults.*]` sections from `catalogue.toml` (operator overrides).
2. Merge with pack-source defaults (operator wins on key collision).
3. Sort pack names and keys **alphabetically** before emission (required for `check_defaults` byte-stable comparison).
4. Write the merged result as `[pack-defaults.<pack>]` sections in `_data/install-defaults.toml`.

`check_defaults` (the lint that verifies the baked file is not stale) re-runs `compile_defaults` and fails on any byte-level difference — the alphabetical sort guarantee makes this deterministic.

`load_pack_config(pack_name)` merges:

- Layer 1: `_data/install-defaults.toml [pack-defaults.<pack>]` (baked, read via `importlib.resources`).
- Layer 2: `<pack_dir>/config.toml` (user, read from disk).

Shallow merge: layer 2 wins on key collision. Returns `{}` when both are absent. On malformed `config.toml`: logs a warning to stderr and returns the baked layer only.

`catalogue.toml` gains a top-level `[pack-defaults.<pack>]` section (not nested under `[distribution.agentbundle]`). `catalogue.schema.json` and the `CatalogueConfig` dataclass are updated in the `catalogue-pack-defaults` spec to accept these sections.

## Alternatives considered

**Runtime-only cascade (fetch catalogue defaults on every `load_pack_config` call):** Rejected. Requires the catalogue source to be reachable on every pack invocation — offline installs fail, latency is added, and the source URL may have changed since install.

**Per-catalogue runtime config file (`catalogue-defaults.toml` shipped alongside the agentbundle package):** Rejected. Two config files to maintain; drift between them breaks the single-source-of-truth guarantee that `check_defaults` provides. The existing `install-defaults.toml` already serves this role.

**Do nothing (only user `config.toml`; no operator layer):** Rejected. Operators cannot pre-configure enterprise URLs — users must enter them manually on every first run.

## Consequences

- `_data/install-defaults.toml` gains `[pack-defaults.*]` sections alongside its existing content.
- `compile_defaults` requires alphabetical sort of pack names and keys; the `catalogue-pack-defaults` spec includes an AC that runs `compile_defaults` twice and asserts byte-exact equality.
- `load_pack_config` is the single callsite for the two-layer merge — pack scripts do not call `importlib.resources` directly.
- The "baked default" label in `pack-config show` deliberately conflates pack-source and operator-override origins; this is an accepted consequence of build-time merging. Any future need to distinguish them requires a new RFC.
- Future catalogue-configurable capabilities follow this same pattern: declare `[capability-defaults.*]` in `catalogue.toml`, bake via `compile_defaults`, read via a dedicated load function.
