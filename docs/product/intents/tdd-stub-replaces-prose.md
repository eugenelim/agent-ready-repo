# A TDD stub replaces its prose bullet rather than accompanying it

- **Status:** Draft
- **Level:** feature

## Outcome

A TDD-mode plan task carries an executable red stub in place of its prose test
bullet, and an obligation that cannot be stubbed carries `no stub (mode)` with a
reason instead of more prose.

## Opportunity

`docs/CONVENTIONS.md` already requires a compilable red stub at PLAN for
TDD-mode tasks, carrying `# STUB: AC<n>` and `stub: true`. It does not say the
stub *replaces* the prose bullet, so plans accumulate both: a stub that fails
executably and a bullet that restates the same property in prose. A stub is an
executable claim that fails; a bullet is not, and the pair creates two homes for
one fact with nothing keeping them in sync.

The observed cost was a plan that mirrored 122 acceptance-criterion conjuncts in
prose. Four repair passes each left a different conjunct behind — the defect was
the mirror, not the passes.

## Assumptions

- This is cross-surface: it moves `docs/CONVENTIONS.md` § *Stub → EXECUTE
  handoff* and `work-loop`'s `references/tdd-stubs.md`, and only then the
  `new-spec` step-5 guidance that cites them. It is deliberately not folded into
  a `new-spec`-only change.
- A top-level convention change may need the repository decision process before
  it can land; scope that before implementation rather than during.
- The related rule that a plan bullet must name a mechanism rather than restate a
  criterion ships separately in `docs/specs/spec-authoring-discipline/`; this
  intent is the stub half only.

## Source

- Mode: repo-origin
- Locator: docs/specs/spec-authoring-discipline/spec.md
- Revision: local-2026-08-28
