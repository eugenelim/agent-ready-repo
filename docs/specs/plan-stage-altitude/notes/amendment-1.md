# Amendment 1 — supervisor red proof and the in-envelope revision route

- **Date:** 2026-10-28
- **Owner authority:** eugenelim chose "Amend now" at the CODE-IMPLEMENTATION gate, before any task started.
- **Reason:** a cross-session conflict check found that the approved contract leaves stub-less tasks with no supervisor-observed red once `execution-supervisor-cutover` makes the supervisor authoritative (ADR-0144), and that the widened verification-ledger route for an `implementation-discovered` means duplicates ADR-0144's in-envelope task change after cutover.

## Changes

1. A `stub` fence leaves the approved plan but is written into the task as a task revision when the task starts, so the supervisor observes red before green.
2. The `implementation-discovered` → verification-ledger route for a design means applies while the whole-plan lock exists; after cutover, ADR-0144's in-envelope task change carries the correction. ADR-0150 cites ADR-0144 rather than adding a second rule.

No task had started; no evidence is carried.
