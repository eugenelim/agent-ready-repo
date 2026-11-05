# Brief: public support claims come from route records, and Claude manifest residue is retired

- **Slug:** `claude-manifest-migration-support-claims-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** [`FEAT-0024-claude-manifest-migration-support-claims.md`](../intents/FEAT-0024-claude-manifest-migration-support-claims.md), under [RFC-0092](../../rfc/0092-first-class-distribution-routes.md) and the [distribution-routes programme](distribution-routes-programme.md), Phase 5
- **Parent intent:** intent:claude-manifest-migration-support-claims

## Outcome

The public route support matrix, the generated block in `guides/_shared/reference/adapter-support.md`, is generated from a machine-readable capability and runtime-verification record. Hand-authored Claude manifest fields that the build can derive are retired behind a compatibility alias with a stated end date.

## Success metrics

- The published support matrix is generated, and a hand edit to it fails a check.
- No route claims above `documentation-verified` without a record naming client, version, surface, and OS.
- A pack whose hand-authored manifest field equals the generated value is flagged, then removed after the alias window.

## Scope / Non-goals

In scope: the verification-record schema, the generated matrix, and the manifest field migration with its alias.

Out of scope: promoting any claim by documentation alone, and removing the alias before its window ends (P3 owns removal).

## Constraints / Appetite

Three slices. P1 needs only the route contract, so it can start once [FEAT-0020](../intents/FEAT-0020-distribution-route-set-opening.md) lands; it does not wait for the Codex or Kiro routes. The owner decided on 2026-11-05 that the compatibility alias window is one minor release of warning, then removal. The public matrix to generate is `guides/_shared/reference/adapter-support.md`. It is hand-written today (no generated marker), so P1 adds a marked generated block and a check that regenerating it changes nothing.

## Proposed slices

| # | Slice | Primary owning surface | Verification | Gating |
| --- | --- | --- | --- | --- |
| P1 | Runtime-verification record schema and a generated block in `guides/_shared/reference/adapter-support.md` | `contracts/`, docs generation | Schema fixtures; regeneration is clean; a hand edit inside the block fails the check | After FEAT-0020 |
| P2 | Warn on a hand-authored Claude manifest field equal to the generated value, record the release that opens the window and the release that ends it, and keep the alias | pack manifests, build | Fixtures: equal field warned, differing field kept, alias accepted | After P1 |
| P3 | Remove the retired fields once the build's own version reaches the recorded end release; the build decides the window is closed by comparing its version with that record | pack manifests, build | Fixtures: a version before the end release accepts the alias, a version at or after it refuses | After P2, in a later minor release than P2 |

## Assumptions / Risks

- **Riskiest assumption:** retiring fields keeps existing Claude consumers working. De-risk with a fixture that installs a pre-migration manifest through the alias.

## Ready gaps (Draft only)

None open.

## Rabbit holes

- Do not treat the matrix as hand-written prose with a generator bolted on.

## Manual residue (named, non-blocking)

- Real client runs that would raise a claim above `documentation-verified`. They fill records after P1 exists and block nothing.

## Spec map

| Spec | Status |
| --- | --- |

## Provenance

Derived from FEAT-0024 and the programme brief's Phase 5 row.
