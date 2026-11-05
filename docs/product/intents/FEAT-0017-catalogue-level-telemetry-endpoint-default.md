# An enterprise catalogue configures the telemetry endpoint once, for all its users

- **Slug:** `catalogue-level-telemetry-endpoint-default`
- **Status:** Accepted
- **De-risked:** 2026-11-05
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** none
- **Depends on:** intent:credential-pack-defaults-projection

## Outcome

An enterprise operator sets a telemetry endpoint once in its catalogue, and every user who installs the core pack from that catalogue exports to it with no configuration step of their own.

## Boundary

- Admits: carrying a telemetry endpoint and service name through the RFC-0101 pack-defaults cascade, and making the baked layer readable by the standard-library-only consumers that actually send.
- Admits: how an end user sees which endpoint their enterprise chose, and whether they may override or decline it.
- Excludes: the two-scope `[telemetry]` resolution in `agentbundle-layout.toml`. That ships with `telemetry-sender-owns-its-configuration` and already covers the adopter-authored case in both scopes.
- Excludes: `pack.layout` and `_append_layout_section`. That channel places an output directory, not configuration, and is not the mechanism here.
- Excludes: secrets. An endpoint is not a credential; an authenticated endpoint is a separate, already-refused scope in the sender's contract.
- Excludes: loop telemetry governance. This feature uses the shipped sender, but its product lineage is the RFC-0101 defaults-projection path and no sender change is currently expected.

## Owner

- eugenelim.

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
  `upgrade.py` does not call it — `_run` in `install.py` is its only caller. An
  enterprise changing its endpoint reaches nobody who has already installed.
  Same shape as the `collect_pack_root_bins` gap in
  `loop-telemetry-export`'s Follow-ons: delivered once, never refreshed.
- **It never fires at `local` scope** (`_run` skips marker and layout writes for local installs), so an ephemeral
  install gets no enterprise default.

### What the projection has to carry

`load_pack_config("core")` merges the baked layer with a user layer at
`<pack_dir>/config.toml`. Whatever the installer writes must be the *merged*
result, not the baked layer alone, or a user override set through
`agentbundle pack-config set` is silently discarded on the path that sends.

## Resolved questions — recommended answers, checked 2026-11-05

Checked: `telemetry-sender-owns-its-configuration` is Shipped, RFC-0101 is Accepted, `_append_layout_section` exists in `commands/install.py`, and `catalogue.toml` bakes no `[pack-defaults]` today. `credential-pack-defaults-projection` is still Draft.

- **One projection or two:** one. Telemetry is a second consumer of the projection that `credential-pack-defaults-projection` needs, so the two share one installer step and one RFC (RFC-0112).
- **Where the file lives:** the user-scope `[telemetry]` section the sender already reads through `--user-config`. The sender needs no new lookup, because it already receives that path.
- **Catalogue default or `[telemetry]`:** the catalogue default is the source, and the installer writes the merged result into the user-scope `[telemetry]` section.
- **Consent and visibility:** the enterprise is the consenting party. The installer prints one line naming the endpoint it configured, and the user declines by removing the section; the sender honours no disable variable today (`OTEL_SDK_DISABLED` appears nowhere in the sender), so the spec decides whether to add a documented decline setting. The sender's Objective sentence on consent must be amended to admit an operator acting for its users.

## Projection

- RFC-0112, shared with `credential-pack-defaults-projection`, covering one installer projection both consumers read, then a focused spec for the telemetry precedence and its disclosure. No queue entry is implied and nothing is blocked on this.

## Opportunity

The enterprise half already ships. `catalogue.toml`'s `[pack-defaults.<pack>]` is typed as an open map of string keys (`contracts/catalogue.schema.json`), so `[pack-defaults.core] telemetry_endpoint = "..."` is schema-legal today with no schema change at all — unlike `pack.layout`, which is closed over four keys. RFC-0101 names exactly this case: the gap between build-time operator knowledge and runtime access is "the primary adoption friction for enterprise catalogues". What is missing is only the last hop to a standard-library-only reader, which a second consumer now also needs.

## Assumptions

- **Riskiest assumption:** the enterprise default binds the individual user and not a team repository, so it sits at layer 4 and needs no change to the sender shipped by `telemetry-sender-owns-its-configuration` (owner decision, 2026-09-16).

- RFC-0101 is Accepted and both its specs — `catalogue-pack-defaults` and `pack-config-api` — are Shipped, so the cascade and `load_pack_config()` exist rather than needing to be built.
- **Knowledge surface:** In-repository RFC-0101, telemetry sender contracts, credential projection intent, and installer configuration evidence.
- This catalogue bakes no `[pack-defaults]` today, so nothing depends on current values and the first use sets the pattern.
- This would be the catalogue's first enterprise-baked telemetry default. It is not the first pack-defaults consumer: credentials got there first, which is why the projection is shared rather than invented here.

## De-risk result

- **Date:** 2026-11-05.
- **Ran:** `pytest packages/jsonl-otlp-exporter/tests/unit/test_two_scope_config.py`, which covers the sender's two-scope `[telemetry]` merge, and `-k user` over the sender tests.
- **Observed:** 48 passed in 0.56 seconds in the two-scope file, and the `-k user` run passed 25. The tests include that each scope contributes the setting the other omits, that the repository scope wins a setting both declare, and that an absent file contributes nothing.
- **Verdict:** supported for the technical half: an enterprise default projected into the user scope reaches the sender with no sender change, and a repository file can override it. The decision that the default binds the user and not a team repository is the owner's (2026-09-16). The update gap, local scope and consent wording stay open.

## Readiness

- **Route:** brief, shared with `credential-pack-defaults-projection`. Neither can ship alone, and the second consumer should not invent a second projection.
- **Deferred:** nothing is blocked on it, and no catalogue sets a default yet. Start it after the credential projection is shaped.
- **First slice, when started:** the shared RFC-0112, then the installer step that writes the merged cascade to the user-scope `[telemetry]` section.
- **Agent-only proof:** installer tests with fixture `catalogue.toml` and an existing user section (never overwritten), local scope (no write), and a user override set through `pack-config set` (kept).
- **Still open for the owner:** whether the update gap (a section the user already has is never refreshed) is accepted for the first version.

## Source

- Mode: repo-origin
- Locator: docs/product/intents/credential-pack-defaults-projection.md
- Revision: sha256-bytes-v1:3f46dfefa8cb2d765dc50528e902e844e9feae2f504e86158a44c2f25e616fe0
- Authority: repo-origin
