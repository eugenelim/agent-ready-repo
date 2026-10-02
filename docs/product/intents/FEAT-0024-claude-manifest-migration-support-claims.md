# Claude manifest migration and support claims

- **Slug:** `claude-manifest-migration-support-claims`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:first-class-distribution-routes

## Outcome

Generated-equivalent Claude manifest fields are retired safely and public support claims derive from machine-readable route capability and runtime-verification records.

## Opportunity

Hand-authored Claude manifests duplicate derivable data and published support claims lack the completed route-layer record.

## Boundary

This feature owns retiring generated-equivalent Claude manifest fields and
deriving public support claims from route capability and runtime-verification
records.

It does not remove the compatibility alias before its approved window ends or
promote documentation-only evidence to runtime-verified support.

## Assumptions

- **Riskiest assumption:** migration can retire generated-equivalent fields while preserving enough compatibility for existing Claude consumers.
- **Knowledge surface:** In-repository RFC-0092, distribution-routes programme brief, route capability records, and support-claim evidence.

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:329d3aec010ffd0f0b090022bac7faf35b85f337d9b3c719ab8063b7c74dbc45
