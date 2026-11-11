# Spec review retry cap dead end

- **Status:** Closed
- **Resolution:** superseded
- **Kind:** defect
- **Detail:** docs/specs/acceptance-authority-and-evidence/notes/spec-review-retry-cap-dead-end.md

## Summary

After a contract amendment, spec review inherits the code-review retry count, and findings-remain from SPEC-PLAN-REVIEW refuses the owner override, so an amended spec cannot loop back to drafting

## Resolution

The defect lived in `loop-engine.py`, which the cutover's T2 switch removed
(#1651, Core 4.0.0). The execution supervisor that replaced it has no
equivalent dead end. Spec and plan review run before `work-supervisor.py
start`, and an amendment sends the spec back to `Draft` for the ordinary
pre-execute reviews. The supervisor's only retry count is
`implementation_retry_cap`, and it counts failed task gates, never review
rounds (`_supervisor_loop.py`, `State.retry_count`).
