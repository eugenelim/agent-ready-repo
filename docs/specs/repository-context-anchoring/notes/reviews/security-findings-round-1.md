# Security implementation review — round 1

## Blockers

**1. [reason] Repository-anchor consumers do not preserve the instruction/data boundary.** `packs/core/.apm/skills/new-spec/SKILL.md:53`. Discovered repository material could widen agent authority. Fix: add the doctor's evidence-only authority rule to every consumer and pin it in tests.

**2. [reason] Repository-anchor consumers do not confine local source discovery.** `packs/core/.apm/skills/work-loop/SKILL.md:211`. An adopter-controlled link could route discovery outside the repository. Fix: canonicalize and symlink-resolve local anchors, reject outside-root results, and pin absolute, parent, and symlink escapes in tests.

## Concerns

**3. [reason] Boundary-crossing skills still lack metadata.boundaries.** `packs/core/.apm/skills/adapt-to-project/SKILL.md:1`. Security automation cannot identify the skill's untrusted-file and write boundaries. Fix: add the established machine-readable filesystem/network boundary declarations and verify they survive projection.

## Not Checked

SAST/SCA/secret scanners, path fuzzing, and generated projection parity were
not checked by this reasoning-level review.
