---
slug: catalogue-manifest-schema
title: "A schema for the catalogue release archive manifest (RFC-0109 S2)"
status: Shipped
---

# Spec: A schema for the catalogue release archive manifest

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0109](../../rfc/0109-catalogue-specification-publication.md) D1 (membership) and D5 (the archive manifest schema), with its [2026-10-21 errata entry](../../rfc/0109-catalogue-specification-publication.md#errata) on the boolean `schema` check
- **Contract:** `contracts/catalogue-manifest.schema.json`
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

**Mode:** full. It adds a public contract file.

## Outcome

Adopters who verify release archives get a machine-readable schema for
`catalogue-manifest.json` that, in a standard draft 2020-12 validator, accepts
exactly the manifests `catalogue verify` accepts. The archive guide stops calling the SHA-256 sidecar and channel
descriptor provenance evidence, and says what each one does and does not prove.

## What Changes

- New contract `contracts/catalogue-manifest.schema.json`, a specification member, with a byte copy in the package's `_data/`
- `contracts/catalogue-spec.toml` gains its member row; `public-contracts.txt` gains its name
- The verifier's manifest check rejects a boolean `schema` — `catalogue_tooling/archive.py`
- The provenance paragraph in `docs/guides/reference/catalogue-archive.md`
- agentbundle 0.55.0

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | A new public contract | `contracts/catalogue-manifest.schema.json`, `contracts/README.md`, `contracts/catalogue-spec.toml` | eugenelim | Parity gate green | Member row and README row present |
| User promise | Adopters read the archive guide to verify archives | `docs/guides/reference/catalogue-archive.md` | eugenelim | Corrected provenance paragraph; schema linked | Guide names the schema and states what proves origin |
| Release history | Package data and verifier behaviour change | the six files `docs/guides/how-to/cut-a-package-release.md` names | eugenelim | 0.54.0 → 0.55.0 | `tests/roster/test_okf_catalogue_discovery.py` passes |

## Agent Rules

### Always do

- Use only JSON Schema keywords both the package's validator (`agentbundle.build.validate`) and a standard draft 2020-12 validator support.
- Keep the schema and `catalogue verify` in agreement under standard draft 2020-12 semantics. The package's validator differs in one known case: it rejects an integer-valued number such as `1.0` for `schema`, which the standard and the verifier accept. A test pins that case.
- Keep top-level and item objects open to extra keys, as the verifier does.
- Add `Engine-Change-RFC: RFC-0109` to every commit touching `packages/agentbundle/`, and bump `version.py` and `pyproject.toml` together.
- State rules in shipped package source and messages without citing RFC, ADR or spec identifiers.

### Ask first

- Any verifier behaviour change beyond rejecting a boolean `schema`.
- Making the schema stricter than the verifier anywhere else.

### Never do

- Make the CLI load or enforce `catalogue-manifest.schema.json` at runtime; the verifier keeps its own checks.
- Add a third-party dependency or a new top-level directory.
- Claim in any guide or schema description that a schema-valid manifest proves who published an archive, or that the archive's contents are intact.

## Testing Strategy

- Schema and verifier agreement: **TDD**. The package suite validates with the package's validator against the bundled schema. A roster test validates the same cases with a standard draft 2020-12 validator (`jsonschema`, already a dev-only tool requirement, as other roster schema-parity tests use) and compares each verdict with the verifier's.
- The boolean `schema` rejection: **TDD** against `verify_archive` on a written archive.
- Membership and parity: **goal-based** — the parity gate and inventory check pass.
- Guide wording: **TDD** in `tools/test_catalogue_tooling_docs.py`, which asserts the old claim is absent and each required statement and the schema link are present.

## Acceptance Criteria

- [x] `contracts/catalogue-manifest.schema.json` exists, declares `"$schema": "https://json-schema.org/draft/2020-12/schema"`, and is a `member` row in `contracts/catalogue-spec.toml`.
- [x] Every manifest that `catalogue package` writes for the starter catalogue from `catalogue init`, and for a catalogue with one pack and one profile, validates against the schema with no error.
- [x] A schema-1 manifest, a manifest whose `packs[]` items carry only `name` and `version`, a manifest whose `profiles[]` items are plain strings, and a manifest with no `profiles` key each validate with no error.
- [x] Each malformed manifest in the verifier's existing CAT-V-ARC-019 shape table, and each CAT-V-ARC-011 case (missing or non-string `bundle`, `release` or `generated_at`; non-list `files` or `packs`; `schema` absent or not 1 or 2), fails schema validation.
- [x] For every manifest in the two criteria above, plus `schema: true`, `schema: 1.0` and `schema: 3`, validity under a standard draft 2020-12 validator equals the absence of CAT-V-ARC-011 and CAT-V-ARC-019 diagnostics from the verifier's manifest check.
- [x] Under the package's validator, the same equality holds for every case except `schema: 1.0`, which the package's validator rejects and the verifier accepts.
- [x] `catalogue verify` on a written archive whose manifest has `schema: true` reports CAT-V-ARC-011, and on one whose manifest has `schema: 1.0` reports no CAT-V-ARC-011.
- [x] The schema's top-level `description` states that it checks shape only, that a valid manifest is neither archive verification nor evidence of who published it, and that origin is established only by `catalogue verify --sha256-file` with a sidecar, or a signature, obtained through a separately authenticated channel.
- [x] A manifest carrying an extra top-level key, and pack and profile items carrying extra keys, validate against the schema.
- [x] `docs/guides/reference/catalogue-archive.md` no longer calls the sidecar or channel descriptor "the provenance evidence". It states that they prove only that the bytes arrived intact, that origin needs a sidecar or signature obtained through a separately authenticated channel, and that a schema-valid manifest is not evidence of origin. It links the schema.
- [x] The parity gate and `sync_contract_inventory.py --check` pass, with `catalogue-manifest.schema.json` in `public-contracts.txt` and a byte-identical `_data/` copy.
- [x] `agentbundle --version` reports `0.55.0`.

## Follow-ons

- eugenelim: RFC-0109 S3 — the docs-site specification section at `draft/`.
- eugenelim: RFC-0109 S4 — release 0.1 and drift checks 2–4.

## Assumptions

none
