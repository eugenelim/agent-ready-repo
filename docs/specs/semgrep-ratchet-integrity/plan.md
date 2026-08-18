# Plan: semgrep-ratchet-integrity

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `tools/test-semgrep-argv-boundary.py` — the whole change.
- `workspace.toml` — remove the two closed `[backlog].open` entries.
- `docs/specs/semgrep-ratchet-integrity/{spec.md,plan.md}` — this contract.

**What demonstrates done**
- Goal-based, with a mutation battery standing in for the disabled adversarial pass.
- `python3 tools/test-semgrep-argv-boundary.py` → `7/7 passed`, exit 0 read
  **unpiped** (zsh `PIPESTATUS` is unreliable here).
- Each of the four mutations in spec AC4 applied, its named failure observed, then
  reverted; `git diff --stat tools/semgrep/argv-path-boundary.yml` empty afterwards.
- Skip posture checked both ways (spec AC6).
- `python3 tools/lint-build.py`, `make lint-ruff`, `make ci` green.

**What I am NOT changing**
- `tools/semgrep/argv-path-boundary.yml` — the subject under test. Byte-identical.
- No production script, no `paths.include` membership, no Makefile invocation.
- Not the three remaining semgrep entries (`sast-semgrep-unparseable-target-reads-clean`,
  `sast-nosemgrep-has-no-form-lint`, `lint-nosec-form-require-id-registry`) — each
  needs a decision its own entry names.

## Declined patterns

- **Tempted:** while the file is open, also add the `nosemgrep` assertion from
  `sast-nosemgrep-has-no-form-lint` — it is three lines and the same file.
  **Declined:** that entry's fix is an `and/or` between a local assertion and
  extending the ADR-0084 form-lint; taking half silently leaves the entry open and
  makes the next author think it is done. It needs its own decision.
- **Tempted:** add `--strict` while touching `scan_all`, per
  `sast-semgrep-unparseable-target-reads-clean`. **Declined:** that entry records
  adopting `--strict` as an ADR-shaped decision, precedent ADR-0084, not a detail.
- **Tempted:** regex the `paths.include` block instead of importing yaml, to honour
  AGENTS.md's pure-stdlib line literally. **Declined:** it re-creates the
  parse-YAML-with-regex antipattern that caused five of six review rounds on
  `test-build-check-workflow.py`, and the rule is scoped to *new* tools scripts while
  seven existing ones already import yaml. Recorded as Assumption 2 with the
  stdlib-audit scope confirmed by reading `lint-build.py`.
- **Tempted:** drop the `check_id` filter once `ratcheted_scope()` refused multi-rule
  files, since it is then unreachable. **Declined:** two guards that fail on different
  mutations, both protecting against a silently-green ratchet. Kept, with the
  redundancy stated in AC5 rather than hidden.
- **Tempted:** keep the scope derivation at module level — it reads more cleanly as a
  constant. **Declined:** it made a malformed rule file exit 1 on a machine with no
  semgrep, silently changing the documented optional-tool posture. Threaded as a
  parameter instead (AC6).
- **Tempted:** add `_loop_guards.py` to `FIXED_SCRIPTS` and stop there — it closes the
  live drift in one line. **Declined:** it fixes the instance and leaves the
  mechanism, which is the entry's whole point. The next added path drifts again.

## Tasks

### T1 — Reproduce the fail-open before changing anything
- **Mode:** goal-based. `Done when:` `FIXED_SCRIPTS = []` is observed passing at
  exit 0, and the `_loop_guards.py` omission is confirmed against the rule.
- **Tests:** no stub — this task *is* the test of the old control.
- **Status:** done. `2/2 passed`, exit 0. `_loop_guards.py` in `paths.include`,
  absent from `FIXED_SCRIPTS`.

### T2 — Confirm the newly-covered script is clean before covering it
- **Mode:** goal-based. `Done when:` a direct semgrep run reports
  `_loop_guards.py` scanned with zero findings.
- **Tests:** no stub (goal-based).
- **Status:** done. Ordered before T3 deliberately: if it had findings, the fix
  would redden the gate on arrival and the task list would need a different shape.

### T3 — Confirm the parser is available where the gate runs
- **Mode:** goal-based. `Done when:` the invocation context is identified and PyYAML's
  presence there is established from the manifests, not assumed.
- **Tests:** no stub (goal-based).
- **Status:** done. `make sast` is the only invocation; its job installs
  `requirements-sast.txt`; `bandit` requires `PyYAML>=5.3.1`. Recorded as Assumption 1.

### T4 — Derive the scope; key findings by rule
- **Mode:** goal-based. `Done when:` `7/7 passed` at exit 0 and no `FIXED_SCRIPTS`
  reference remains except in explanatory comments.
- **Tests:** no stub — the file under change is itself the test.
- **Touches:** `tools/test-semgrep-argv-boundary.py`.

### T5 — Mutate the new control
- **Mode:** goal-based. `Done when:` all four AC4 mutations produce their named
  failure and the tree is restored.
- **Tests:** no stub (goal-based).

### T6 — Close the two backlog entries
- **Mode:** goal-based. `Done when:` both slugs are gone from `[backlog].open`, the
  slug-set delta against `HEAD~1` is exactly those two, and `lint-spec-status` is clean.
- **Tests:** no stub (goal-based).
- **Touches:** `workspace.toml`.
