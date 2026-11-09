# Verification ledger — run grant, run run-cf63dab6371c9ea2

## Approvals and start

- Spec gate parked at commit 83eaa3350 (spec digest d05e6c91…); the owner approved it on 2026-11-08. Plan gate parked at 1b1f606b0 (plan digest c141bd5c…); the owner approved it the same day. `start` admitted approval pair 1 with authority refs `owner` and `plan-reviewer`.
- Spec-stage reviews before approval: security-reviewer and adversarial-reviewer, three rounds each, ending `Clean`.
- The RFC-0113 link (AC-0027) landed as a controller commit before `start`, because the RFC is a cited record and is worker-protected during the run.

## Task gates

- T1 grant judge: lint pair clean; grant units and runner units, 240 passed.
- T2 binding, Ready-only and grant answers: lint clean; units and guidance 260 passed; grant and runner integration suites with `WORK_SUPERVISOR_INTEGRATION=1`, 249 passed in 14 min 55 s.
- T3 guard: lint clean; guard, units, guidance and grant units 296 passed; `tools/test-build-check-workflow.py` posture OK; `tools/test-lint-ci-parity.py` 218 cases; `tools/lint-ci-parity.py` ok. Smoke: `guard --from origin/main --to HEAD` passed on this branch; on PR #1697 (531654f41) it fails `grant-change-mixed`, as AC-0018 intends.
- T4 guidance, evals, trust model: lint clean; 384 passed; pack-test boundary 158 cases; catalogue lint no errors. The roster pin for AC-0024 got its named build-check step and parity entry.
- T5 release: `tools/check-core-release.py --base 513c64b68` "release is consistent" (4.0.25 over the run's merge base 4.0.24); `tools/changelog.py validate` exit 0.
- T6 review round 1 repairs: lint clean; units, guidance, guard and author-delivery-brief 490 passed; integration suites 256 passed in 15 min 32 s; posture, parity and pack-test boundary checks green.
- T7 author-delivery-brief projections: `catalogue self-host --write` changed only the four author-delivery-brief copies; `catalogue verify` and `catalogue lint --deep` exit 0.

## run-gates

- Rounds 1 and 2: AC-0001–AC-0025, AC-0027, AC-0028 pass on the task gates above. AC-0026 was reported pass before regenerate with the owner's explicit yes (2026-11-08), because the only failure was projection drift (CAT-V-015) that regenerate fixes.
- Round 3, after regenerate: the real AC-0026 check failed on the four author-delivery-brief copies that the work-loop regenerate step does not commit. It was reported `fail`, which opened `criteria-unsupported`, and T7 repaired it.
- Round 4: all 28 criteria pass; `catalogue verify` and `catalogue lint --deep` exit 0.

## Review

- Round 1: adversarial (4 findings, 1 non-material), security (2), quality (9, 4 non-material). All were assessed supported, and T6 repaired every one. Blockers: shallow-clone binding fail-open; quoted datetimes in the grant template.
- Round 2: adversarial and security `Clean`; quality 2 non-material Nits (duplicated `ls-tree` parsing in `_strict_entry`; five fake-failure cases build their own worlds), deferred.
- Round 3, after regenerate and T7: adversarial and security confirmed the projected copies equal their sources byte for byte; quality carried the same 2 Nits.
- The run reached `terminal`; `status --check` exit 0.

## Known flaky test

- `test_brief_runner.py::test_the_runner_starts_only_read_only_git_and_supervisor_gates_and_status` failed once under load, failed the same way on the untouched base 513c64b68, then passed in later runs. It is pre-existing and not caused by this change.

## Closeout after terminal

- Main moved during the run (PR #1723, Slice 7, Core 4.0.25). The run finished on its own base, and the closeout merges origin/main, bumps Core to 4.0.26, rebuilds the projections and reruns the suites.
