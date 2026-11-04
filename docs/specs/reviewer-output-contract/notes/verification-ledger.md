# Verification ledger: reviewer output contract

Execution observations from the supervisor run `run-cea8b64917d2cc9c`, on 2026-11-04.

## Base probe

On base `2fe8d6512`, a report of numbered findings without anchors was refused by `raw-classify` as `sentinel-absent`. Flagless `inspect` refused it as `no-actionable-result`. The four AC-0003 reports and the AC-0004 mixed report gave the results the spec states.

## Delivery checks

- AC-0013: core moves from 4.0.11 to 4.0.12, and experience-design from 4.2.0 to 4.2.1. Both are measured from merge base `2fe8d6512` with freshly fetched `origin/main`. `pack.toml` equals `plugin.json` in both packs.
- AC-0015: `tools/check-core-release.py --base 2fe8d6512` printed `release is consistent` and exited 0.
- AC-0016: `git diff --exit-code 2fe8d6512 -- contracts/delivery/review-report.v1.schema.json contracts/delivery/finding.v1.schema.json` exited 0.
- AC-0017: during the run, self-host differed only in the supervisor's pinned install, `.claude/skills/work-loop/` and `.agents/skills/work-loop/`. Rewriting that install refuses every verb with `supervisor-changed`. The owner approved reporting AC-0017 as `pass`, to be checked at the delivery commit. After the supervisor's `regenerate` step, `agentbundle catalogue self-host --root . --write` left 0 changed files, and `agentbundle catalogue verify --root .` printed `ok`.

## Review

- Post-code adversarial review, round 1, raised one supported finding. The eval case rewarded redispatching the reviewer after an `invalid` report. Repair task T5 made the case surface and stop.
- Rounds 2 and 3 were clean.
- Conditional reviewers were not selected. Each omission is recorded in the run with its reason.

## Scope note

T2 also edits `packs/core/.apm/agents/quality-engineer.md`, with owner approval. Its `## Typed report` section is pinned byte-identical to `adversarial-reviewer.md`'s.
