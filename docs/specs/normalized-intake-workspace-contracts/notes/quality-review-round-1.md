# Quality review round 1

**1. Blocker — source decisions are under-specified and in the wrong contract** `contracts/jsonschema/normalized-intake.schema.json:104`

Transient normalized content accepts `source_decisions`, while artifact-owned
fixture rows omit required durable review evidence. Remove source decisions
from normalized intake and require artifact rows to record source revision,
field, decision, local approver, and date. **Disposition: apply.**

**2. Blocker — work lifecycle fixtures do not prove fixed status/plan rules** `packs/core/tests/pack/fixtures/work-intake-contracts/workspace/context/lifecycle.toml:35`

Queue, active, and shipped entries lack spec-status and sibling-plan evidence,
and the oracle cannot reject Draft-active or queued-without-plan cases. Add
contextual spec metadata, invalid cases, and direct lifecycle assertions.
**Disposition: apply.**
