# Verification ledger: supervisor-fresh-checkout-status

## Owner decisions (2026-10-30)

The owner (eugenelim) settled four points before the spec body was written:

1. **Design.** In a checkout without the run's store, `status` alone verifies the committed records and says so; every other verb still refuses. The exception holds whatever the run's state, because a squash merge drops the supervisor's trailered commits and a finished run then derives as non-terminal. Committing the pins was declined: a later `core` release changes the installed digests on `main`, so every merged run would refuse, and a pin committed in the tree it checks adds no tamper signal.
2. **Vehicle.** A new spec that amends `execution-supervisor-attempt-security` AC-0014, rather than reopening that Shipped spec.
3. **Output.** Every `status` view carries `verification`, `pinned` or `committed-records-only`; the degraded path writes nothing.
4. **Side defect.** The `attempt-residue: common:config` defect is captured, not fixed, here.

## Reproduction (2026-10-30)

- A fresh clone of `evidence/tracker-origin-registration-stop-run`: `status docs/specs/tracker-origin-registration-stop --check` exit `1`, `supervisor-changed`, `the supervisor's pin record is missing`.
- The same clone with both pin checks bypassed (throwaway, uncommitted): exit `0`, `terminal: true`, no `.git/agentbundle-supervisor` created.
- The same tree squashed into one commit on its merge base: exit `0`, stage `implementing`, empty `refusal`.
