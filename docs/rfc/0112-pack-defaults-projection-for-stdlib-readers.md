# RFC-0112: Project pack defaults to a file that standard-library-only scripts can read

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-11-05
- **Date closed:** 2026-11-05
- **Decision weight:** standard — it draws a trust boundary for credential-pack and telemetry readers, so it carries a security review; it adds no public API and reverses by deleting the projected files
- **Related:** [RFC-0101 pack config and operation log](0101-pack-config-and-oplog.md) (the cascade this extends), [ADR-0059](../adr/0059-pack-config-cascade-via-install-defaults-baking.md) (where baked defaults live), [RFC-0046 convenient install defaults](0046-convenient-install-defaults.md) (the baking pipeline), intents [`credential-pack-defaults-projection`](../product/intents/credential-pack-defaults-projection.md) and [`FEAT-0017`](../product/intents/FEAT-0017-catalogue-level-telemetry-endpoint-default.md) (the two consumers)

## Reviewer brief

- **Decision:** Let `agentbundle install` write a pack's catalogue defaults to the destination its standard-library-only reader already uses, limited to keys the pack itself marks as projectable, so scripts that may import only the Python standard library can read them.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - The installer projects only pack-declared, non-sensitive keys from the RFC-0101 cascade (baked `[pack-defaults.<pack>]` layer merged with the user's `config.toml`) to the reader's destination.
  - Sign-in destinations and authentication defaults can never be projected, whatever a catalogue operator writes.
  - The projected file is treated as untrusted, catalogue-derived configuration by every reader.
- **Affected surface:** `packages/agentbundle` install path, pack manifests (a new declaration of projectable keys), `packs/credential-brokers` and the core telemetry hook as first readers.
- **Stakes:** Reversible. The file is derived at install time and can be deleted or regenerated. The costly part is the trust rule, which this RFC fixes before any code exists.
- **Review focus:** Whether "pack declares, operator only supplies values" is enough to keep a catalogue operator from widening what gets projected, and whether the untrusted-file rule is stated strongly enough.
- **Not in scope:** Each destination's exact path and update behaviour (the follow-on ADR decides those, carrying the owner decisions already recorded in `FEAT-0017`: user-scope `[telemetry]` section, precedence layer 4, no write at local scope); headed automatic sign-in refresh; secrets (these stay with `credbroker`, the agentbundle credential module).

## The ask

**Recommendation:** Accept the projection with a pack-declared allowlist and an always-refused set of sign-in and authentication keys.

**Why now:** [RFC-0101](0101-pack-config-and-oplog.md) baked catalogue defaults into `_data/install-defaults.toml`, but only agentbundle's own code (`load_pack_config` and the `pack-config` command) reads that layer. Skill scripts run on their own and may import only the standard library, so they cannot call it. Two features wait on the same missing hop: a catalogue operator baking one telemetry endpoint for every user (`FEAT-0017`), and credential packs reading site defaults such as a Jira base URL.

| ID | Question | Recommendation | Why | Owner | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | Project the merged defaults to the reader's destination at install time? | Yes | The only route that keeps scripts standard-library-only and offline-safe | eugenelim | 2026-11-19 | Confirm or reject |
| D2 | Who decides which keys are projected? | The pack declares projectable keys; the operator only supplies values | The pack source is the reviewed trust anchor, so an operator who edits only the baked values cannot widen the set | eugenelim | 2026-11-19 | Confirm or propose another authority |
| D3 | What is never projected? | Sign-in URLs, success patterns, and any authentication default | A projected value that steers a sign-in becomes an attacker-chosen destination for a credential | eugenelim | 2026-11-19 | Confirm the refused set |

## Problem & goals

A script that must run with only the standard library has no supported way to read catalogue-baked defaults. Today the baked layer sits inside the installed `agentbundle` package, and finding it from a standalone script means guessing an install path and assuming the package is present.

Goals:

- Standard-library-only readers get the baked defaults with no network call and no import of `agentbundle`.
- The route cannot carry a sign-in destination or authentication default, whatever an operator writes into the baked values.

Non-goals, each plausible and deliberately excluded:

- Letting the file act as trusted configuration. It stays catalogue-derived data that readers validate.
- Solving per-user overrides. [RFC-0101](0101-pack-config-and-oplog.md)'s `config.toml` layer already does that.

## Proposal

**D1. Project at install.** After install resolves a pack, the installer reads the pack's effective configuration by calling `load_pack_config` (so [ADR-0059](../adr/0059-pack-config-cascade-via-install-defaults-baking.md) D5 keeps one merge) and writes only the pack's projectable keys to the destination the consuming reader declares. There are two kinds of destination, with separate rules.

1. **A per-pack file** under the pack's user directory, read by credential packs. The installer owns the whole file. It is written with `write_confined_regular_file` under a root checked by `validate_confined_directory` (the blessed helpers in `agentbundle.catalogue_tooling.file_safety`). The file lives under the validated user directory (`user-dir`) only, and any other root is refused. The write refuses a symlinked or non-regular target or parent. The helper rewrites in place and restores the file if the write fails, and that restore-on-failure behaviour is the accepted standard; the follow-on spec proves it with a failed-write fixture. Uninstall removes the file when the last adapter row for the pack is removed.
2. **A section inside a file the adopter owns**, read by the telemetry hook: the user-scope `[telemetry]` section it already receives through `--user-config`. The installer owns and removes only a section it wrote; a section the adopter wrote belongs to the adopter, and the follow-on ADR decides how install tells the two apart. The installer never deletes or rewrites the rest of the file. At minimum the write refuses a symlinked or non-regular target or parent and restores the file if the write fails; the ADR adds any further rules for editing part of an existing file.

A malformed user `config.toml` is a refusal for projection: `load_pack_config` only warns and returns the baked layer in that case, and projecting it would silently drop the user's override. Both kinds fail closed. On any refusal, the installer writes nothing and leaves the destination as it was. On a write error, a new file is not left behind, and an existing file is restored to its previous bytes. If the restore itself fails, the installer records a durable untrusted marker for that destination. The marker is written separately from the destination and kept even when the restore fails. Readers treat a marked destination as absent and use their built-in defaults. Install refuses to project anywhere else until it has rewritten the destination and cleared the marker. For a section inside an adopter-owned file, the follow-on ADR decides who clears the marker. Scope rules: user scope projects as above. Repo scope either does not project or writes to a destination the ADR names under the confined repository root, and the ADR chooses one. Local scope does not project, matching the owner decision recorded in `FEAT-0017`.

This RFC does not decide update behaviour. The follow-on ADR decides whether and how an installed value is refreshed, and it carries `FEAT-0017`'s recorded requirement that an existing adopter section is never overwritten.

**D2. Pack declares, operator supplies.** A pack lists in its own manifest the keys that may be projected. Each key declares a scalar type (`string`, `https-url`, `int` or `bool`) and a `purpose` drawn from a closed enumeration in the schema (the build refuses an unknown value), and its name matches ASCII `[a-z0-9_]`. The installer projects the intersection of that list and the effective configuration, top-level keys only and by exact match. The catalogue build already stringifies every baked value (`catalogue_tooling/config.py`), so the checks apply to the form that exists at each stage. At build time the manifest is checked for names, types and purposes, and the build rejects a baked table or array under any declared key before it can be stringified. At install time each effective value, from whichever layer it came from, is checked against its declared type after conversion, and a value that does not parse as that type, or a table or array from any layer, is refused and install reports the refusal. A catalogue operator can change a value but cannot add a key to the list, because the list ships with the reviewed pack source and not with the catalogue.

Threat model: the defence holds against an operator who controls only the baked values in `install-defaults.toml` (a mistaken or hostile `catalogue.toml` entry). An operator who controls the pack source is out of scope, because that operator already controls the pack's code. The installer reads the manifest from the pack it is installing, so the allowlist travels with the pack source and not with the baked layer.

**D3. Refused set.** The refusal is a closed rule. The build fails if a listed key's declared purpose is sign-in or authentication. A key is also refused when, after casefolding and treating `-` as `_`, it equals `login_url` or `success_url_pattern` or matches `auth_*`, `*_token` or `*_cookie`. The check runs at build time on the pack manifest and again at install time on the effective configuration, so the same rule holds on both sides. The `purpose` enumeration includes `credential-destination`, and the build applies this rule to every key declared with it: a key whose value decides where a credential or token is sent (a site base URL a broker binds a credential to) is refused, unless the broker binds the credential only to a host the user confirmed or the broker itself wrote. A projected host that differs from that host never receives a credential. Binding compares the normalized origin (scheme, host and port) at every send against the stored origin the user confirmed, and a confirmation never offers a projected value as a pre-accepted default. Automatic refresh stays pinned to state the broker itself wrote.

**Reader rule.** The projected value is untrusted. A standard-library reader opens its file without following links, refuses a non-regular file, and caps its size at 64 KiB before parsing. It validates each value for its own use and falls back to its built-in default when a value is absent or invalid.

**Endpoints.** A projected endpoint never turns telemetry on and never changes the payload. It only replaces the destination after the user has opted in. The URL must be `https`, with no userinfo, no query or fragment, and no private, loopback or link-local host. The sender follows no redirects and applies the private-range block to the exact address the connection uses. The opt-in prompt shows the endpoint's host, and a projected host that differs from the one the user agreed to needs fresh consent before any send.

**First readers.** The core telemetry hook reads one endpoint key (`FEAT-0017`). Credential packs read non-sensitive site defaults. Neither reads a sign-in value from the projection.

## Options considered

Axis: where a standard-library-only script finds baked defaults.

| Option | Trade-off |
| --- | --- |
| **Install-time projection (recommended)** | One extra file per pack to keep in step. Works offline and without agentbundle. |
| Script reads the packaged `install-defaults.toml` directly | No new file, but the script must locate an install path it does not own, and fails when the package is absent or relocated. |
| Do nothing | Both features stay blocked, or each ships its own ad hoc copy of the hop, each with its own trust rule. |

## Risks & what would make this wrong

- **A catalogue supplies a sign-in URL under an allowed-looking key.** The follow-on spec must include fixture catalogues that try `login_url`, `LOGIN_URL`, `login-url`, a Unicode lookalike, `auth.login_url` as a dotted key, a table-valued baked key (refused at build), and a site base URL pointed at an attacker host (the credential must not be sent there), and expect refusal at each check that can see them. It also covers a bad value set in the user layer, a symlinked target or parent, uninstall cleanup, a failed create that leaves no file, a failed update that restores the previous bytes, a failed restore that is reported, and an endpoint that redirects or resolves to a private address.
- **The pack allowlist grows into a back door.** Mitigation: the list is reviewed with the pack source, and the refused set overrides it.
- **A reader trusts a projected value.** Mitigation: the reader rule above, and a test that a reader ignores an invalid value.
- **Drift between the cascade and the projected value.** Update behaviour is the ADR's decision. Known gap carried by `FEAT-0017`: a destination the user already has is not refreshed unless the ADR says so.
- Honest drawback: one more installed artifact per participating pack.

## Evidence & prior art

- `docs/rfc/0101-pack-config-and-oplog.md` § D2 fixes the build-time baking this RFC builds on.
- `packages/agentbundle/agentbundle/config.py` `load_pack_config` and `commands/pack_config_cmd.py` `_load_baked_only` are the in-package readers of the baked layer today; neither is usable from a standard-library-only script.
- `docs/product/intents/FEAT-0017-catalogue-level-telemetry-endpoint-default.md` records the owner decisions on the telemetry destination, precedence and merged content that D1 follows.
- Credential-broker sign-in behaviour stays governed by its own broker contract (RFC-0013) and SSO RFC-0035. This RFC adds no sign-in authority, and the follow-on spec must show the projection stays within them.

## Open questions

None. Destination paths and update behaviour are decisions for the follow-on ADR, not open here.

## Follow-on artifacts

- ADR extending [ADR-0059](../adr/0059-pack-config-cascade-via-install-defaults-baking.md): projected file location, precedence, provenance and update behaviour. Draft it once this RFC is accepted.
- One specification for installer projection and first-reader consumption, in full mode with a security review (it touches `packages/agentbundle` and `packs/credential-brokers`).
