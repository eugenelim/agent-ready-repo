# Spec: Site contract provenance cleanup

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0089, ADR-0055, ADR-0085
- **Brief:** tech-site-completion
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

- Frozen-document integrity uses TDD construction tests because the invariant is
  byte-level: only the permitted Status line changes.
- Living-guidance and backlog dispositions use goal-based checks against the
  canonical files because their outcome is exact text and lifecycle membership.
- Lifecycle integrity uses the full workspace reconciliation and the existing
  rendered-link unit suite.

## Acceptance Criteria

- [ ] The Phase 4b product-docs spec Status names ADR-0055 as the authority for
  the superseded docs URL instruction, identifies only that superseded scope,
  and leaves every other frozen body byte unchanged.
- [ ] After RFC-0089's follow-on palette ADR exists, ADR-0055's Status points
  forward to that ADR for only the superseded token-sharing rationale, and the
  frozen `starlight-migration` spec Status points to it for only the amber
  palette/token assertions; every frozen body byte remains unchanged.
- [ ] Living guidance distinguishes the Pages workflow's current two-phase
  generation order (`--journeys-only`, marketing build, full docs aggregation,
  docs build) from the valid local full-generation sequence; both preserve the
  load-bearing marketing-before-docs render order and run combined page and
  fragment checking after both builds. No living instruction claims the
  repository has no link checker or that the two sequences are identical.
- [ ] The registered `web-docs-link-check-gate` item is closed as already
  shipped and points to `docs/specs/rendered-site-link-debt/spec.md` while
  retaining its original review header and vintage.
- [ ] `site-link-check-contract-docs` is resolved within the same canonical
  closure and does not enter the backlog as a duplicate item.
- [ ] The orphan rendered-link historical comment block is either attached to
  its shipped target or retained in an explicitly historical location; it
  cannot appear to be open membership.
- [ ] The registered `starlight-migration-rfc` item is closed to RFC-0089 after
  that RFC is accepted, with its original source and review provenance intact.
- [ ] A full Type 1/2/3 workspace reconciliation reports no inconsistency
  introduced by the lifecycle transaction.
- [ ] Existing rendered-link unit tests pass and the cleanup changes no emitted
  route or navigation contract.
- [ ] No tracked artifact introduced by this spec names the external visual
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
