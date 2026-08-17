# Implementation review — round 2

## Blockers

**1. Pack release notes are not synchronized with version bumps.** `docs/product/changelog.md:41`

Fix: add dated release sections for the resulting core patch and
governance-extras 0.9.7. After rebasing over core 2.7.0, the combined core
release is 2.7.1.

**2. Legacy writer documentation still contradicts the retired append path.** `docs/knowledge/README.md:187`

Fix: state that the legacy corpus is curation/migration input only and every
new observation uses the public capture seam or a named no-write outcome.

**3. Receive-brief does not test the complete private-writer boundary.** `packs/core/tests/skills/receive-brief/test_project_knowledge_handoff.py:34`

Fix: pin the public-only handoff, every forbidden producer responsibility, and
the absence of legacy/private implementation names.

**4. Work-loop does not require a redacted refusal diagnostic.** `packs/core/.apm/skills/work-loop/SKILL.md:249`

Fix: require the diagnostic in shipped gate prose and its construction test.

## Concerns

**5. Gate-owning producers omit security boundary metadata.** `packs/core/.apm/skills/receive-brief/SKILL.md:1`

Fix: declare untrusted file reads and filesystem writes on the four producers
that now own capture gates, then regenerate projections.

**6. The plan echoes a stale spec lifecycle state.** `docs/specs/project-knowledge-authoring-integrations/plan.md:3`

Disposition: defer this lifecycle-only edit until the reviewer-clean transition.
The approved plan baseline is immutable while the loop is active, and changing
the echo now invalidates the recorded approval hash. Final closeout will move
the spec link and both artifact statuses to their terminal states together.
