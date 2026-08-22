## Blockers

**1. Full `make ci` completion is still claimed instead of deferred.**
`docs/specs/local-ci-orchestration/spec.md:116` and
`docs/specs/local-ci-orchestration/plan.md:226`. AC12/T3 still require
`SKIP_SAST=1 make ci` to complete successfully, but the current run stopped at
the registered pre-existing enterprise `.pem` denials, so the unmet tail is not
represented as `(deferred: pre-existing-enterprise-agentbundle-full-suite)`.
Fix: Split or revise AC12 so the verified route/lint/build-check evidence can be
checked, and mark only the blocked full-suite `make ci` completion with
`(deferred: pre-existing-enterprise-agentbundle-full-suite)` while updating T3
evidence to say the run reached tests through one route before the pre-existing
denial.

## Concerns

**2. Spec index status is stale.** `docs/specs/README.md:22`. The index row says
`Draft` while the spec itself is `Implementing`, so the living specs index now
disagrees with the feature lifecycle state. Fix: Update the row status to match
the spec's current status, and keep it aligned when the spec later ships.
