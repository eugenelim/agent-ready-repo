# Review round 1 (adversarial + quality-engineer)

**1. Spec Status not Shipped; ACs unchecked.** `docs/specs/windows-build-gate-chain/spec.md:3`. Fix: flip to Shipped, check ACs. [APPLIED]
**2. Plan Status not Done; AC7 record absent.** `docs/specs/windows-build-gate-chain/plan.md:4`. Fix: Status Done, record AC7. [APPLIED]
**3. AC7 manual-QA artifact absent.** `docs/specs/windows-build-gate-chain/spec.md:88`. Fix: record run. [APPLIED]
**4. Doc drops read-only-vs-writes distinction.** `docs/architecture/agentbundle.md:103`. Fix: note build-self writes, build-check verifies. [APPLIED]
**5. Failure-legibility line untested.** `packages/agentbundle/agentbundle/build/gate_chains.py:50`. Fix: assert stderr names label+code. [APPLIED]
**6. Missing-script test asserts non-zero not rc==2.** `packages/agentbundle/agentbundle/build/tests/test_gate_chains.py:196`. Fix: assert rc==2. [APPLIED]
**7. Test comment four-vs-five inconsistency.** `packages/agentbundle/agentbundle/build/tests/test_gate_chains.py:130`. Fix: five. [APPLIED]
