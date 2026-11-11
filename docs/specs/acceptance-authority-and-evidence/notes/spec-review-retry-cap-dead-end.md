# Engine defect: spec review cannot loop after a contract amendment

Found on 2026-10-05 while re-approving this spec's Accepted Risk.

A `contract-amendment` keeps the run's review counters. The spec-review
stage then reads the code-review retry count (19, against a cap of 5) when
`findings-remain` fires from `SPEC-PLAN-REVIEW`:

- the `spec-plan` `findings-remain` guard (`_guard_check_phase_review` in
  `loop-engine.py`) stops on the retry cap and names
  `--allow-retry-cap-override` as the only way past it;
- the transition handler refuses `--allow-retry-cap-override` and
  `--fingerprint` from `SPEC-PLAN-REVIEW` ("does not accept review-effect
  payload").

So an amended spec whose first pre-execute review has findings cannot return
to `SPEC-PLAN-DRAFTING`. This run worked around it by fixing and re-reviewing
in `SPEC-PLAN-REVIEW` until a round came back clean, then firing
`reviewers-clean`. The review records are under the run's
`.context/reviews/` directory, rounds 14 onward.

Fix direction: either reset or separate the spec-review counter at
`contract-amendment`, or let the spec-review `findings-remain` accept the
owner override.
