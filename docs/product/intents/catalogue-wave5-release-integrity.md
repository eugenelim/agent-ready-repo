# Catalogue release integrity

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0076 D8](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)

## Outcome

Catalogue publishers can package releases with content digests, compare them with a prior archive, and refuse same-version archive mutation unless they explicitly override it.

## Opportunity

The neutral index describes catalogue contents, but the release process still needs durable evidence and a guard against silently changing an already-versioned archive.

## Assumptions

- The archive-level mutation boundary in RFC-0076 remains the baseline scope to refine.

## What the decision requires

- Add a SHA-256 digest for every pack and profile to `catalogue-manifest.json`, calculated from the sorted, normalized file list of the normalized content tree and excluding generated outputs (RFC-0076 D8).
- Refuse, with exit 2, to package a version whose catalogue archive already exists unless `--force` is passed; first-party CI must not use `--force` in the publish pipeline (RFC-0076 D8).
- Add `--compare <archive>` to `agentbundle catalogue package` for added, removed, and changed packs with version and digest changes, in default human output and `--format json` (RFC-0076 D8).

## Non-goals

- The refusal applies to packaged catalogue `.tar.gz` archives, not local development re-builds (RFC-0076 D8).

## Open questions the RFC left

- Wave 5 determines whether pack-level archives, if any, also fall within the mutation-refusal scope (RFC-0076 OQ3).

## Source

- Mode: repo-origin
- Locator: docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
