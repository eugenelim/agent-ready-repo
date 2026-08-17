# Spec: Site contract provenance cleanup

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0089](../../rfc/0089-starlight-docs-boundary.md), [ADR-0055](../../adr/0055-starlight-replaces-mkdocs-for-reference-docs.md), [ADR-0085](../../adr/0085-docs-rendering-is-site-local.md)
- **Brief:** docs/product/briefs/tech-site-completion.md
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what done means. The implementing
> change matches this spec or updates it before merge.

## Objective

Maintainers can determine the current site-generation and link-verification
contract from canonical living guidance without being misled by frozen route
or palette text, stale backlog membership, or orphaned historical comments.
Historical review provenance remains recoverable while current dispatch state
contains no duplicate or already-shipped site debt.

## Boundaries

### Always do

- Preserve the complete historical comment block and review vintage for every
  legacy item whose lifecycle membership changes.
- Annotate frozen documents only through their mutable Status field.
- Reference the shipped rendered-site link checker as the implementation
  authority instead of restating its behavior.

### Ask first

- Reopen any shipped route, navigation, or checker decision.
- Change a legacy disposition from the approved brief.
- Alter frozen text outside an allowed status annotation.

### Never do

- Rewrite a shipped spec body to make its historical language look current.
- Remove provenance because an item is stale, duplicated, or already shipped.
- Add a dependency, route, navigation destination, or new artifact hierarchy.

## Testing Strategy

- Frozen-document integrity is verified goal-based, as a one-changed-line delta
  per document (`git diff --numstat`), because that is exactly what the
  byte-level invariant asserts. A durable construction test is deliberately not
  written: it could only anchor on a git base ref (unavailable post-merge) or a
  committed hash, and a committed hash would reject the meaning-preserving
  mechanical rewrites `docs/CONVENTIONS.md` § Superseding a frozen document
  explicitly licenses.
- Living-guidance and backlog dispositions use goal-based checks against the
  canonical files because their outcome is exact text and lifecycle membership.
- Lifecycle integrity uses the full workspace reconciliation and the existing
  rendered-link unit suite.
- The external-visual-reference prohibition (AC10) is a manual reviewer check,
  recorded as performed-and-clean; the term is never written into a tracked
  file, commit message, or PR body.

## Acceptance Criteria

- [x] The Phase 4b product-docs spec Status names ADR-0055 as the standing
  authority for the corrected docs URL instruction and names the spec that
  applied the correction, identifies only that scope, states plainly that it is
  not a supersession of a decision made in that spec (ADR-0055 was already
  Accepted when it shipped, so the instruction was contrary to it rather than
  superseded by it), and leaves every other frozen body byte unchanged.
- [x] After RFC-0089's follow-on palette ADR exists, ADR-0055's Status points
  forward to that ADR for only the superseded token-sharing rationale, and the
  frozen `starlight-migration` spec Status points to it for only the amber
  palette/token assertions; every frozen body byte remains unchanged.
- [x] Living guidance distinguishes the Pages workflow's current two-phase
  generation order (`--journeys-only`, marketing build, full docs aggregation,
  docs build) from the valid local full-generation sequence; both preserve the
  load-bearing marketing-before-docs render order and run combined page and
  fragment checking after both builds. No living instruction claims the
  repository has no link checker or that the two sequences are identical.
- [x] The registered `web-docs-link-check-gate` item is closed as already
  shipped and points to `docs/specs/rendered-site-link-debt/spec.md` while
  retaining its original review header and vintage.
- [x] `site-link-check-contract-docs` is resolved within the same canonical
  closure and does not enter the backlog as a duplicate item.
- [x] The orphan rendered-link historical comment block is either attached to
  its shipped target or retained in an explicitly historical location; it
  cannot appear to be open membership.
- [x] The registered `starlight-migration-rfc` item is recorded as satisfied by
  accepted RFC-0089 and retained in `[backlog].open` — removal would break
  `lint-spec-status.py` invariant (iv), whose anchor lives in a frozen body this
  spec may not edit — with its original source and review provenance intact.
- [x] A full Type 1/2/3 workspace reconciliation reports no inconsistency
  introduced by the lifecycle transaction.
- [x] Existing rendered-link unit tests pass and the cleanup changes no emitted
  route or navigation contract.
- [x] No tracked artifact introduced by this spec names the external visual
  reference.

## Assumptions

- Technical: combined page and fragment checking already runs after both site
  builds (source: `.github/workflows/pages.yml` and `Makefile`).
- Technical: ADR-0055 is the accepted authority for the Starlight docs boundary
  and build order, while RFC-0089 D2 owns the evidence-backed palette
  reconciliation (source: ADR-0055, RFC-0089, and the shipped
  `docs-site-design-refresh` spec).
- Product: stale items close without reopening shipped behavior (source: user
  confirmation 2026-08-17).
- Process: frozen bodies change only through the documented Status annotation
  mechanism (source: `docs/CONVENTIONS.md`).
- Process: lifecycle membership is changed through canonical work intake after
  its target artifact exists (source: `docs/product/briefs/tech-site-completion.md`).
- Process: AC7's closure is a disposition, not a membership removal.
  `lint-spec-status.py` invariant (iv) resolves a `(deferred: <slug>)` anchor
  against `[backlog].open` only and fails hard, and the frozen
  `starlight-migration` spec carries that anchor in a body this spec may not
  edit — so the entry stays in `[backlog].open`, recorded as satisfied by
  RFC-0089 with its source and review provenance intact. Widening invariant (iv)
  is a published-interface change requiring an RFC and is out of scope (source:
  `docs/CONVENTIONS.md` § Spec metadata contract; the brief's registered-debt
  note that open membership remains for this compatibility pointer).
- Technical: AC4's closure and AC6's comment disposition already landed in
  commit `0455eea1`; this spec verifies them and normalises AC4's pointer to the
  repository-relative spec path rather than re-performing the closure (source:
  `workspace.toml` rendered-link comment block, which records that canonical
  closure verification remains here).
