# Amendment 1 — supervisor red proof and the in-envelope revision route

- **Date:** 2026-10-28
- **Owner authority:** eugenelim chose "Amend now" at the CODE-IMPLEMENTATION gate, before any task started.
- **Reason:** a cross-session conflict check found that the approved contract leaves stub-less tasks with no supervisor-observed red once `execution-supervisor-cutover` makes the supervisor authoritative (ADR-0144), and that the widened verification-ledger route for an `implementation-discovered` means duplicates ADR-0144's in-envelope task change after cutover.

## Changes

1. A `stub` fence is not required content of the approved plan, but where a supervisor run executes a TDD task the plan author carries it in that task, so the supervisor still observes red before green (ADR-0150 D3).
2. An `implementation-discovered` means and its corrections go to the verification ledger (ADR-0150 D5).
3. Both post-lock routes — a controller-written task-start fence revision and the in-envelope working-plan change for a design correction — are left to `execution-supervisor-cutover`, recorded as a Follow-on in `spec.md`. ADR-0150 cites ADR-0144 and states no rule for them.

No task had started; no evidence is carried.
