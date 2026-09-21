# An enterprise catalogue configures the telemetry endpoint once, for all its users

- **Slug:** `catalogue-level-telemetry-endpoint-default`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim

## Outcome

An enterprise operator sets a telemetry endpoint once in its catalogue, and every user who installs the core pack from that catalogue exports to it with no configuration step of their own.

## Boundary

- Admits: carrying a telemetry endpoint and service name through the RFC-0101 pack-defaults cascade, and making the baked layer readable by the standard-library-only consumers that actually send.
- Admits: how an end user sees which endpoint their enterprise chose, and whether they may override or decline it.
- Excludes: the two-scope `[telemetry]` resolution in `agentbundle-layout.toml`. That ships with `telemetry-sender-owns-its-configuration` and already covers the adopter-authored case in both scopes.
- Excludes: `pack.layout` and `_append_layout_section`. That channel places an output directory, not configuration, and is not the mechanism here.
- Excludes: secrets. An endpoint is not a credential; an authenticated endpoint is a separate, already-refused scope in the sender's contract.

## Owner

- AgentBundle distribution maintainers, jointly with the owner of [`credential-pack-defaults-projection`](credential-pack-defaults-projection.md), which names the same missing projection for a different consumer.

## Future state

The target chain, highest precedence first. Layers 1-4 ship with
`telemetry-sender-owns-its-configuration`; layer 5 is what this intent adds.

| # | Layer | Where it lives | Who reads it | Ships |
| --- | --- | --- | --- | --- |
| 1 | Operator, per run | `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` | sender | now |
| 2 | Operator, per run | `OTEL_EXPORTER_OTLP_ENDPOINT` | sender | now |
| 3 | Repository, per setting | `<repo>/agentbundle-layout.toml` `[telemetry]`, via `--config` | sender | now |
| 4 | User, per setting | `~/.agentbundle/agentbundle-layout.toml` `[telemetry]`, via `--user-config` | sender | now |
| 5 | Enterprise | `catalogue.toml` `[pack-defaults.core]`, baked into `_data/install-defaults.toml` | nothing that can send | this intent |

A setting absent from a layer falls through to the next; a setting present only
in the user scope applies, endpoint included. Nothing in layers 1-4 needs the
caller to read a value: it builds two paths from a repository root and a home
directory and passes both.

### Where layer 5 enters, and why the answer decides the sender's shape

The cheapest target is the **user-scope `[telemetry]` section the sender already
reads**. If the installer projects the baked defaults there, layer 5 needs no
sender change at all — `--user-config` already carries it, and the resolution
chain above is unaltered. That is the only option costing zero on the sender
side, and it is why this intent does not ask
`telemetry-sender-owns-its-configuration` to reserve a slot it cannot yet fill.

Three consequences have to be accepted or solved, and none is solved here.

- **Precedence — settled 2026-09-16 by the intent owner.** An enterprise default
  binds the **individual user**, not a team repository: it occupies layer 4, and a
  repository file may legitimately override it for that repository. So projecting
  into the user-scope `[telemetry]` section is correct as it stands, and layer 5
  costs the sender nothing. Had it needed to bind a repository too, it would have
  had to rank above layer 3, which no projection target can grant itself — that
  would have been a sender change, and it is the reason the question was decided
  before `telemetry-sender-owns-its-configuration` was approved rather than after.
- **The value can never be updated.** `_append_layout_section` is
  never-overwrite, so a section the adopter already has is left alone, and
  `upgrade.py` does not call it — `install.py:1931` is its only caller. An
  enterprise changing its endpoint reaches nobody who has already installed.
  Same shape as the `collect_pack_root_bins` gap in
  `loop-telemetry-export`'s Follow-ons: delivered once, never refreshed.
- **It never fires at `local` scope** (`install.py:1907`), so an ephemeral
  install gets no enterprise default.

### What the projection has to carry

`load_pack_config("core")` merges the baked layer with a user layer at
`<pack_dir>/config.toml`. Whatever the installer writes must be the *merged*
result, not the baked layer alone, or a user override set through
`agentbundle pack-config set` is silently discarded on the path that sends.

## Unresolved questions

- The baked layer is reachable only through `agentbundle.config.load_pack_config()`. Both consumers that would read a telemetry endpoint are deliberately standard-library-only — the sender, whose contract forbids any runtime dependency beyond the standard library, and the hook that invokes it. `credential-pack-defaults-projection` already records that no safe installer projection exists. Is telemetry a second consumer of that one projection, or does it need its own?
- If the installer projects the merged cascade to a file, what is that file and how does a consumer that must not import `agentbundle` locate it without being told a path? `pack_dir()` resolves `user_root` from `state.toml` and falls back to `~/.agentbundle`, but resolving it is itself an `agentbundle` call.
- Consent and visibility. In this model the enterprise is the consenting party and the end user is expected to use what it configured, so installing does begin sending — the opposite of the adopter-authored case. What tells a user that telemetry is on and where it goes, and may they decline? The sender's Objective currently states installing is the first consent and configuring is the second; an enterprise default needs that sentence to admit an operator acting for its users, or it is simply contradicted.
- Whether a catalogue-supplied default belongs in a per-pack config file at all rather than in `[telemetry]`, given a user-authored `agentbundle-layout.toml` already has a defined precedence the sender honours.

## Projection

- Most likely an RFC-0101 addendum shared with `credential-pack-defaults-projection`, covering one installer projection both consumers read, then a focused spec for the telemetry precedence and its disclosure. No queue entry is implied and nothing is blocked on this.

## Opportunity

The enterprise half already ships. `catalogue.toml`'s `[pack-defaults.<pack>]` is typed as an open map of string keys (`contracts/catalogue.schema.json`), so `[pack-defaults.core] telemetry_endpoint = "..."` is schema-legal today with no schema change at all — unlike `pack.layout`, which is closed over four keys. RFC-0101 names exactly this case: the gap between build-time operator knowledge and runtime access is "the primary adoption friction for enterprise catalogues". What is missing is only the last hop to a standard-library-only reader, which a second consumer now also needs.

## Assumptions

- The enterprise default binds the individual user and not a team repository, so it sits at layer 4 and needs no change to the sender shipped by `telemetry-sender-owns-its-configuration` (owner decision, 2026-09-16).

- RFC-0101 is Accepted and both its specs — `catalogue-pack-defaults` and `pack-config-api` — are Shipped, so the cascade and `load_pack_config()` exist rather than needing to be built.
- This catalogue bakes no `[pack-defaults]` today, so nothing depends on current values and the first use sets the pattern.
- This would be the catalogue's first enterprise-baked telemetry default. It is not the first pack-defaults consumer: credentials got there first, which is why the projection is shared rather than invented here.

## Source

- Mode: repo-origin
- Locator: docs/product/intents/credential-pack-defaults-projection.md
- Revision: sha256-bytes-v1:3f46dfefa8cb2d765dc50528e902e844e9feae2f504e86158a44c2f25e616fe0
- Authority: repo-origin
