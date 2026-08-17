# Plan: Site contract provenance cleanup

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

## Approach

Pin the allowed frozen-document delta with a construction test, correct the two
living guidance sources, then perform the legacy lifecycle closures through the
canonical intake transaction. Finish by running the focused link tests and a
full workspace reconciliation. The spec, not the historical backlog prose,
remains the present-tense implementation contract. Palette supersession work
starts only after RFC-0089's focused follow-on ADR exists.

## Constraints

- Follow RFC-0089, ADR-0055, ADR-0085, and the
  frozen-document supersession rules in `docs/CONVENTIONS.md`.
- Preserve the provenance blocks registered in `workspace.toml`.
- Do not change routes, navigation, or checker behavior.

## Construction tests

**Integration tests:** focused rendered-link tests followed by full
`workspace-status reconcile`.

**Manual verification:** review the final workspace diff to confirm that each
closed item retains its original header, vintage, and canonical target.

## Design (LLD)

### Design decisions

The transaction closes or merges membership only after the canonical target is
present. Historical prose stays historical; living guidance contains the
current operational instruction. Traces to: all acceptance criteria.

### Dependencies & integration

The frozen Phase 4b spec points upward to ADR-0055. The earlier ADR and frozen
Starlight migration spec point to RFC-0089's follow-on ADR for only their
superseded palette/token scope. Living guidance points to the existing combined
checker. Workspace changes use work-intake rather than an ad hoc TOML rewrite.
Traces to: AC1-AC8.

## Tasks

### T1: Frozen-spec and guidance construction tests pin the allowed contract

**Depends on:** none

**Touches:** tools/test_*.py, docs/specs/phase4b-product-docs-completion/spec.md, docs/adr/0055-starlight-replaces-mkdocs-for-reference-docs.md, docs/specs/starlight-migration/spec.md, guides/AGENTS.md, docs-site/AGENTS.md

**Tests:**
- TDD: prove fixtures permit only the three approved Status annotations and
  reject a frozen body rewrite or an unscoped supersession (AC1-AC2).
- TDD: prove living guidance names the exact Pages two-phase generation order,
  distinguishes it from the valid local full-generation sequence, names the
  combined-build checker, and contains no obsolete no-checker or false
  sequence-equivalence claim (AC3).

**Approach:**
- Add focused construction assertions in the nearest existing policy-test
  module.
- Pin the exact canonical checker path rather than duplicating its algorithm.

**Done when:** both tests fail on the current stale guidance and pass only for
the approved contract.

### T2: Frozen status and living guidance describe current authority

**Depends on:** T1

**Touches:** docs/specs/phase4b-product-docs-completion/spec.md, docs/adr/0055-starlight-replaces-mkdocs-for-reference-docs.md, docs/specs/starlight-migration/spec.md, guides/AGENTS.md, docs-site/AGENTS.md

**Tests:**
- Goal-based: run the T1 construction tests (AC1-AC3).
- Goal-based: run the rendered-link checker unit suite (AC9).

**Approach:**
- Amend only the Phase 4b Status line.
- After the follow-on ADR exists, amend only ADR-0055's and the Starlight
  migration spec's Status lines with narrow partial-supersession pointers.
- Replace obsolete link-check guidance with the two-build ordering and checker
  reference, documenting CI's split generation stages separately from the
  local full-generation sequence.

**Done when:** the allowed delta and link-check guidance tests pass.

### T3: Legacy memberships close with provenance intact

**Depends on:** T2

**Touches:** workspace.toml

**Tests:**
- Goal-based: reconcile shows no duplicate, invalid, or missing membership
  caused by the transaction (AC4-AC8).
- Manual QA: compare the preserved comments with their pre-transaction review
  headers and vintages (AC4-AC7).

**Approach:**
- Use work-intake's canonical transaction path to close
  `web-docs-link-check-gate`, merge the living-guidance gap, and attach or
  classify the orphan comment.
- Close `starlight-migration-rfc` to accepted RFC-0089 without flattening its
  original registration context.
- Keep the shipped rendered-link spec as the canonical target.

**Done when:** all dispositions are durable, non-dispatchable as intended, and
retain provenance.

### T4: Combined contract verification is green

**Depends on:** T3

**Tests:**
- Goal-based: focused rendered-link tests pass (AC9).
- Goal-based: full Type 1/2/3 reconciliation is clean (AC8).
- Goal-based: repository search finds no newly introduced forbidden reference
  name (AC10).

**Approach:**
- Run the smallest focused test set first, then the full reconciliation.
- Record the emitted commands and results in the implementation handoff.

**Done when:** all spec acceptance criteria have recorded evidence.

## Rollout

This is a repository-governance and guidance change with no runtime rollout.
Rollback is a normal patch reversal, except that frozen-body integrity must
remain preserved.

## Risks

- A manual TOML edit could detach provenance from its item.
- Over-broad wording could imply that Starlight itself checks generated links.
- A frozen-spec edit could accidentally change more than its Status line.

## Changelog

- 2026-08-17: initial plan derived from the approved tech-site completion brief.
