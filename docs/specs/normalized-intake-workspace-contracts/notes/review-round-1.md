# Review round 1

The installed `adversarial-reviewer` runtime stalled on three dispatches without
returning content. The orchestrator therefore records that reviewer as a named
skip for this round and performed the bounded fallback review required to keep
the full-mode loop evidence-based.

## Findings

**1. Major — refresh existence and confinement are not exercised** `contracts/jsonschema/normalized-intake.schema.json:37`

The schema can enforce only the lexical shape of `refresh_target`, while AC4
also requires an existing canonical artifact and AC10 requires resolved-path
confinement. The current normalized-intake fixtures and cross-contract harness
do not evaluate that contextual boundary. Add an oracle test with a real
existing in-root target, a missing target, and a symlink escape.
**Disposition: apply.**

**2. Major — compaction verification repeats expected labels** `packs/core/tests/pack/test_work_intake_contracts.py:293`

This test and the focused workspace-entry test assert the fixture's `expected`
strings directly. They do not derive retain/remove behavior from live `needs`,
open-parent references, and closure evidence as required by AC22 and the plan's
construction-test contract. Add a small reference oracle and make every matrix
row explicit. **Disposition: apply.**
