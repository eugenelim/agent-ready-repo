# Pack eval-harness disposition

`packs/AGENTS.md` requires a non-cosmetic pack update to move that pack's eval
harness with it. Two `packs/core` skills change non-cosmetically here, so the
rule applies twice. `plan.md` is hash-pinned once `loop-cohort approve-plan` persists
it, so each disposition is recorded here instead. One row per changed skill,
filled in during EXECUTE.

A row is complete either way: an added case, or the measured reason no case can
be written. An empty row is an undischarged obligation, not a skip.

| Skill | Owning task | What changed | Disposition |
| --- | --- | --- | --- |
| `workspace-status` | T2 | The `invalid_completion_receipt` finding code and the satisfaction-time receipt path | Eval 8 drives a malformed local completion receipt through the backend and requires the stable code, safe next action, and backend-owned verdict. |
| `close-work` | T4 | The receipt paragraph's contract — carrier, closed vocabulary, and the lifecycle record's grammars, replacing "a short outcome statement" | _pending_ |
