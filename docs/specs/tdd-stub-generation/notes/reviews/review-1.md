# Adversarial review — round 1 (implementation-stage)

## Blockers

**1. Spec Status stale at Draft.** `docs/specs/tdd-stub-generation/spec.md:3`. Implementation complete but Status=Draft, plan.md=Drafting. Fix: flip spec→Shipped, plan→Done (T7).

**2. All 10 ACs unchecked on a shipping spec.** `docs/specs/tdd-stub-generation/spec.md:54`. Each AC met but `[ ]`. Fix: tick each `[x]` from named evidence (T7).

**3. README row status stale.** `docs/specs/README.md:82`. Row reads Draft; will drift once spec flips. Fix: update README row status to Shipped (T7).

## Nits

**4. Spike stub header omits canonical `# STUB: AC<n>` marker form.** `docs/specs/tdd-stub-generation/notes/spike.md:52`. Catalogue-internal note, no adopter-genericity impact; authored before T2 canonicalized the marker. Fix: retrofit per-test comments to `# STUB: ACn` to model the convention.

## Clean findings (verified)
Adopter-genericity (AC2) clean; marker convention consistent reference↔CONVENTIONS↔spike; pytest worked example a faithful red→green shape stub; scope clean (edits land only on named insertion points); spike honestly supports AC9 with Shipped-target caveat and exclusion-AC limit recorded.
