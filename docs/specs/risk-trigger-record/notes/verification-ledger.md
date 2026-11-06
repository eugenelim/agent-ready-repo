# Verification ledger: risk-trigger-record

Execution observations, 2026-11-05 to 2026-11-06. Run `run-5ce4ce0aa72fe354`,
tasks T1 to T7, terminal; `work-supervisor.py status --check` exits 0.

## Criteria at the last run-gates

All 13 criteria passed on real checks at the fourth `run-gates`, after T7:

- AC-0001, AC-0002, AC-0008, AC-0009: `test_risk_trigger_record_contract.py`
  (6 tests) pins the contract table against the risk-trigger block, the lint
  token set against the table, the template line, the PLAN step 2 sentence and
  one eval case per skill.
- AC-0003 to AC-0007: `test_lint_spec_status.py` (120 tests, 29 of them for
  invariant (vii)) covers each malformed value, the second line, the new
  `Draft` warning, the silent cases, and lines that are bare, commented, fenced,
  in the body or empty.
- AC-0010: `grep -n "Risk triggers:"` finds the how-to sentence.
- AC-0011: the note has 3 sections, each with one `Baseline`, one
  `Re-measure when` and one `Method` line.
- AC-0012: `tools/check-core-release.py --base origin/main` exits 0; Core is
  4.0.18 and `origin/main` was 4.0.17 when fetched.
- AC-0013: `agentbundle catalogue self-host --root . --check` exits 0.

## AC-0013 and the regenerate step

The run pins the installed `work-loop` skill, so its `.claude/` and `.agents/`
copies stay stale until the supervisor's own `regenerate` step. At the first
two `run-gates` requests, `self-host --check` exited 1 with 8 installed-copy
drifts; AC-0013 was reported `pass` there under the owner's conditional
approval of 2026-11-06. The condition was met first: the supervisor's code
issues `run-gates` again after regenerate (`_supervisor_attempt.py` pinned-name
rule and `pending_regeneration`; `_supervisor_loop.py` `decide` and the
regenerate commit; `_supervisor_readiness.py` `delivery_subject` and
`readiness_action`).

The supervisor commits a regenerate step only when every change is a copy of
its pinned skill, so the two `new-spec` eval copies were restored to let it
commit. The third `run-gates` then checked AC-0013 for real: exit 1, 2 drifts
(those two copies). It was reported `fail`; repair task T7 rebuilt the two
copies, and the fourth `run-gates` passed.

## Gates run locally (targeted only)

- Core suites, one pytest call each: `packs/core/tests/pack` 460 passed,
  `skills/new-spec` 307 passed, `skills/work-loop` 3093 passed with 817 skipped.
- `make lint-ruff lint-mypy` with the pinned `ruff==0.16.10` passes. A newer
  local ruff flags `close-work/scripts/closure_index.py`, a file outside this
  diff.
- `tools/lint-agents-md.py` passes. `make precheck` passes after T7.
- `lint-spec-status.py --root . --all --verbose` over 631 specs exits 0 with no
  (vii) finding; `docs/specs/ast10-pack-compliance/spec.md`, whose preamble has
  a bare `**Risk triggers:**` prose line, draws none.
- Not run locally, left to CI: `make test`, the full roster, `make ci`.

## Task notes

- T1 also carries the Core bump, its changelog fragment and the
  `tests/roster/test_registry_upgrade_notes.py` release pin, so the core
  release check passes from T1 on. T5 then only verified the release.
- T6 is a review repair. Three `git grep` hits for `unfamiliar` remain in the
  work-loop `evals.json`; they are case ids that predate this change
  (`unfamiliar-trigger-predict-the-design` and two others), not token lists.

## Review

Three rounds of `adversarial-reviewer`; no conditional role was selected, with
a recorded reason for each omission. Findings by round: 4, 0, 0. All four
round-1 findings were assessed supported and repaired in T6: an eval case
spelled tokens in pack content; the note's method counted lines the lint
treats as no line; the lint trimmed all whitespace where AC-0006 allows only
spaces; and the base-ref skip warnings said all of (vii) was skipped. Round 3
covered only the rebuilt installed copies, each byte-identical to its source.

## Heads-up for the pull request

Core is 4.0.18 here. Re-run `tools/check-core-release.py --base origin/main`
right before merging, since `main` can ship another core patch meanwhile.
