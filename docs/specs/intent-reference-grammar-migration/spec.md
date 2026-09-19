# Spec: Cross-artifact reference grammar and pointer migration

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** docs/product/briefs/intent-identity-and-registration.md
- **Discovery:** docs/product/intents/FEAT-0001-intent-identity-and-registration.md
- **Constrained by:** ADR-0108; ADR-0112

## Objective

Make a written reference name exactly one artifact. `resolve_endpoint` in `lint-traceability.py` suffix-matches a bare slug against every node id and picks among multiple hits by sort order; the corpus holds 6 cross-type slug collisions, and one fired during this brief's own shaping.

Canonical form is `<kind>:<slug>`. A bare slug stays readable as a legacy fallback that refuses on ambiguity. The migration exists not because bare slugs fail today but because one that is unique now can be made ambiguous by any later artifact, so storing one stores a latent failure.

## Testing Strategy

- Resolve canonical pointers, unique bare slugs, and ambiguous bare slugs; assert one artifact, one artifact, and refusal.
- Assert the migration sweep leaves no untyped resolvable value in the derived cohort.
- Assert the cohort is derived from the corpus at run time rather than from a fixed count.

## Acceptance Criteria

- [ ] A canonical `<kind>:<slug>` pointer resolves to exactly one artifact.
- [ ] An unambiguous bare slug still resolves; fail-closed does not mean rejecting every legacy reference.
- [ ] An ambiguous bare slug refuses rather than choosing among candidates by sort order or any other tiebreak.
- [ ] After the sweep, the derived migration cohort holds no untyped resolvable value.
- [ ] **Decision owed by this spec:** which fields are in the migration cohort and each one's canonical target kind. `Brief:` and `Parent intent:` are clear; `Contract:` and `Discovery:` are overloaded and carry prose in some artifacts, so the cohort derives by whether a value resolves, not by field name.
- [ ] An ordinal is a display alias and is not an accepted pointer value, because it does not exist for a refused altitude or a forward-only legacy artifact.
