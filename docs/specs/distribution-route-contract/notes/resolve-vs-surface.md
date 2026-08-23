# Resolve-vs-surface record

## PLAN

- Resolve: contract shape, route ownership, compatibility oracle, version target,
  test seams, and review depth from RFC-0092, ADR-0090, current code, and the
  approved spec/plan.
- Resolve: the RFC-0092 Claude capability-table conflict through the approved,
  zero-output erratum path; do not implement the three absent projections.
- Surface only if: an external consumer of removed adapter fields is discovered,
  a golden tree cannot be made lossless, or a gate exposes a requirement outside
  Phase 0.
- Domain grounding: not required; no external domain claim underpins the build.

## DECIDE

Open. Close after every review finding has an `apply`, `exclude`, or explicit
owner decision and the accepted Phase 0 intent is complete.

## Pre-EXECUTE review round 1

- Apply: materialize AC5/AC6 red tests and expand AC1/AC4/AC8/AC9 stubs to the
  exact contract surface.
- Apply: add the omitted admission-policy mismatch case.
- Apply: make the two security-review checkpoints explicit.
- Apply in bounded form: specify route-derived path confinement and unchanged
  non-dereferencing behavior as AC14.
- Exclude: blanket rejection of source symlinks and hard links. APM intentionally
  preserves confined relative links as links, and AC8 freezes that behavior.
- Apply: reject symlinked copy roots plus absolute or escaping nested source links.
  This is the path-confinement control for links that a downstream package
  consumer could follow; it does not reject or dereference confined relative
  links and therefore does not broaden into a general package-content policy.
- Apply: add explicit traversal/absolute, symlink-parent, pre-mutation, and
  preserved-link red tests for AC14; keep private helper placement in the plan.

## Post-gate review round 1

- Apply: catch malformed explicit recipe values at the CLI boundary and name the
  recipe plus offending route field without a traceback.
- Apply: construct compiled/dropped Claude projection rows without stale
  direct-install destinations or merge policy.
- Apply: replace the monolithic route-object enum with closed field-level schemas
  and localized validation diagnostics.
- Apply: validate route copy roots before writes, validate nested links as path
  capabilities, and route lint through the same schema-validated contract loader.
- Apply: make targeted render selection route-aware so Claude, APM, and unrelated
  direct-install adapter targets cannot select each other's package routes.
- Apply: require aggregate recipes to select a route with a marketplace projector
  and reject any aggregate adapter that disagrees with the route.
- Apply: compute Claude admission first, then preflight all admitted packs before
  projecting any of them; excluded repo-only packs retain their skip behavior.
- Apply: make route-resolution diagnostics consistently name the recipe and exact
  field.
- Resolve reviewer tension on nested links in favor of the security boundary:
  reject only absolute/escaping links while retaining the approved confined-link
  golden witness. AC14 and the plan now state this distinction explicitly.
- Exclude: remove `STUB: AC<n>` construction-test markers. The cited scoped
  instruction contains no such prohibition, while `docs/CONVENTIONS.md` expressly
  requires the marker and the plan retains `stub: true` for those tests.
