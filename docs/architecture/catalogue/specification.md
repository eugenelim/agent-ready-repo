# The catalogue specification

> The contracts a catalogue author needs form one versioned specification.
> `contracts/catalogue-spec.toml` names its members, each release freezes a
> snapshot, and the docs site serves every released version at a stable URL. Four
> checks keep the published bytes equal to the bytes the CLI enforces.

An adopter reads the specification at
`https://eugenelim.github.io/agent-ready-repo/docs/spec/catalogue/<MAJOR.MINOR>/`.
Release `0.1` is the first, dated 2026-10-23 and paired with adapter contract
`0.18`.[^1] Governing decision: [RFC-0109](../../rfc/0109-catalogue-specification-publication.md).

## Membership

One manifest declares every contract file's role. It is the single input for the
CLI's bundled copies, the packaged inventory, and the site.[^2]

| Role | Count | Meaning |
| --- | --- | --- |
| `member` | 10 | In the specification: published, versioned, and served |
| `bundled` | 9 | Shipped inside the CLI for offline use, not part of the specification |
| `vendored` | 2 | Third-party schemas pinned under `contracts/vendor/` |

The ten members are the `pack`, `catalogue`, `profile`, `skill`,
`skill-manifest`, `catalogue-index`, `adapter`, and `catalogue-manifest` schemas,
plus `target-vocab.toml` and `adapter.toml`. Work-loop, delivery, workspace, and
work-intake contracts are not members and stay unpublished.

`contracts/` remains the authored source. The CLI loads contracts only from its
bundled `agentbundle/_data/` copies, never from the repository `contracts/`
folder.[^3]

## Versions and URLs

Each release is an immutable `<MAJOR.MINOR>/` path. A member's `$id` equals its
served URL, so a schema resolves where it names itself. `latest/` and `draft/`
are aliases and carry no identity.[^4]

A release row in the manifest records the date, the adapter-contract version,
and a SHA-256 digest for every member and page. The frozen files live under
`contracts/releases/catalogue/<version>/`.

## Site projection

`tools/catalogue_spec_site.py` projects the member rows into the docs site, and
`tools/build-site.py` calls it.[^5]

- JSON members render as generated field tables, and TOML members render as code
  blocks.
- Narrative pages link to fields and never define them.
- Each released version is served from its frozen snapshot.
- `latest/` is a byte copy of the newest release plus generated redirects.

Rules that exist only in code, such as the `CAT-V-ARC-*` archive checks and the
`JOURNEY.md` validator, are described by the pages. The byte checks below do not
cover them.

## Drift checks

| Check | Proves | Runs in |
| --- | --- | --- |
| Manifest parity | Every member and bundled row has a byte-identical `_data/` copy, the packaged inventory matches the manifest, and `contracts/README.md` lists each row under its role | `make build-check` (`tools/catalogue/check_contract_parity.py`) |
| `$id` version consistency | Member bytes equal the latest snapshot when they name the latest version, and name an unreleased version otherwise | `make build-check` (`check_spec_version.py`) |
| Append-only snapshots | A released member and its page source never change against the anchor commit | `make build-check` (`check_release_immutability.py`) and the Pages workflow (`tools/check-deployed-release-parity.py`, against the deployed index) |
| Release gate | A tagged CLI bundles exactly the member bytes the site serves for the version it reports | `release-agentbundle.yml` (`check_release_gate.py`) |

The deployed-index check fetches the live site over HTTPS with redirects
refused, a 30-second timeout, and a 1 MiB read bound. The release gate reads the
member set from the release row alone and not from the bundled inventory.[^6]

## Planned

The evaluator page that links into this specification belongs to
[`catalogue-wave7-marketing-evaluator`](../../product/intents/catalogue-wave7-marketing-evaluator.md),
which is STATUS: PLANNED.

[^1]: `contracts/catalogue-spec.toml` (`[[release]]`, version `0.1`).

[^2]: `contracts/catalogue-spec.toml`; `packages/agentbundle/agentbundle/_data/public-contracts.txt` and `catalogue-members.txt` are generated from it by `tools/catalogue/sync_contract_inventory.py`.

[^3]: `tools/catalogue/check_contract_parity.py`; root `ARCHITECTURE.md` § 7.

[^4]: `contracts/releases/catalogue/0.1/pack.schema.json` (`$id`); `tools/catalogue/rewrite_member_ids.py`.

[^5]: `tools/catalogue_spec_site.py`; `docs-site/astro.config.ts` (generated redirects).

[^6]: `tools/check-deployed-release-parity.py`, `tools/catalogue/check_release_gate.py`.
