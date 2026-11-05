# Spec: route support claims come from a verification record

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored after the spec is approved
- **Mode:** full (a new contract under `contracts/` and a generated public guide block)
- **Constrained by:** RFC-0092
- **Brief:** brief:claude-manifest-migration-support-claims-delivery
- **Discovery:** none
- **Depends on:** intent:distribution-route-set-opening
- **Contract:** `contracts/route-verification.toml`, `contracts/route-verification.schema.json` (new)
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

Someone reading the adapter support guide sees, for each distribution route, what it carries and how that claim was verified. A claim above `documentation-verified` cannot appear without a dated record that names the client, version, surface, and OS.

## What Changes

- A new contract records one entry per verified claim. Fields come from the programme brief's instrumentation list: client, version, surface, OS, install route, components tested, date, evidence, limitations. No such record exists today (checked 2026-11-05: no file under `contracts/` or `docs/architecture/` carries one).
- A generator writes a marked block, "Distribution route support", into `guides/_shared/reference/adapter-support.md` from `contracts/distribution-routes.toml` and the record. The hand-written adapter matrix in that file stays as written. The file is hand-written today, with no generated marker.
- A check fails when the block differs from regeneration.
- This spec owns the one generator. The [digital-product-guides brief](../../product/briefs/digital-product-guides-delivery.md)'s G2 builds host overlays on a separate page and links to this block.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Applicable | `guides/_shared/reference/adapter-support.md` | eugenelim | Generated block present | Regeneration clean |
| Interface compatibility | Applicable | the new contract and schema | eugenelim | Schema fixtures | Contract tests green |
| Release history | Applicable | changelog entry | eugenelim | One entry | Entry present |

## Agent Rules

### Always do

- Mark the generated block so a hand edit inside it is detectable.
- Default every claim to `documentation-verified` when no record exists.

### Ask first

- Any change to the hand-written adapter matrix.

### Never do

- Never promote a claim above `documentation-verified` from documentation alone.
- Never write generated text outside the marked block.

## Testing Strategy

- **TDD** with schema fixtures: valid record, missing field, unknown status.
- **Goal-based** for regeneration: run the generator and check the file is unchanged.

## Acceptance Criteria

- [ ] A record missing any of client, version, surface, or OS fails schema validation.
- [ ] A route claim with status `runtime-verified` and no matching record fails the check.
- [ ] Running the generator on the committed tree leaves `adapter-support.md` unchanged.
- [ ] Editing a character inside the generated block makes the check fail.
- [ ] The generated block lists each route in `contracts/distribution-routes.toml` with its per-primitive status.
- [ ] Text outside the generated block is byte-identical to the committed file before this change.

## Follow-ons

- eugenelim: [`claude-manifest-migration-support-claims-delivery`](../../product/briefs/claude-manifest-migration-support-claims-delivery.md) slices P2 and P3 — the warning window and field removal.

## Assumptions

- Technical: the record's location. Default: `contracts/route-verification.toml` (settled by: eugenelim). If wrong: only paths move.
- Defaulted: the dependency on FEAT-0020. Default: the generator reads the route contract as it is, so the work can start on the three existing routes; the dependency only ensures routes added later appear without a schema edit (settled by: eugenelim).
