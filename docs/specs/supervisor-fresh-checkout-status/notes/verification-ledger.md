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

## Gates (2026-10-30)

- Spec approved by eugenelim at `01c13d980`; plan approved by eugenelim at `684f8ed41`.
- `spec-approved` knowledge capture: project-knowledge unavailable (`map_mismatch` from `--capture --producer-profile work-loop`); no fallback file written.

## AC-0007 amendment (2026-10-30)

T4's first attempt found AC-0007 unsatisfiable inside the run: the roster case `test_shipped_pre_pr_runs_no_linter_labels` and the fresh-clone check both run the installed `.claude/skills/work-loop/`, which the supervisor rebuilds only through `regenerate`, issued after every criterion is supported. At `2c179b395` the shipped roster case failed with `supervisor status docs/specs/supervisor-fresh-checkout-status --check failed (exit 1)`; the no-approvals case passed. A fresh clone of that branch with the pack-source scripts copied over its installed skill gave `status --check` exit `0` (`committed-records-only`) and `pre-pr.py` exit `0`. T4's attempt was reported `gate-fail` (retry 1 of 5). The owner (eugenelim) chose to amend AC-0007: in the run, the clone rebuilds its installed skill from the pack source; the final head is proven outside the run by build-check and a plain fresh clone.

## T4: the hook on this branch (2026-10-30)

- `tests/roster/test_core_pre_pr_hook.py::test_pre_pr_passes_when_no_spec_holds_approvals`, with this spec's `delivery/` committed: 1 passed.
- Pushed commit `7f648b1cd984af5e0c67ba3b018644c1f9e36b91`, cloned fresh from `origin` into a temporary directory. In the clone: `PYTHONPATH=packages/agentbundle python -m agentbundle catalogue self-host --root . --write` (exit `0`; it changed only the three `.claude/skills/work-loop/` files), committed in the clone only; no `.git/agentbundle-supervisor` existed. Then `python3 .claude/skills/work-loop/scripts/work-supervisor.py status docs/specs/supervisor-fresh-checkout-status --check` exit `0`, `verification: committed-records-only`, empty `refusal`; and `python3 packs/core/.apm/hooks/pre-pr.py` exit `0`, `pre-pr: ✓ supervisor status docs/specs/supervisor-fresh-checkout-status` and `pre-pr: all checks passed`.
- The first T4 report was refused `attempt-refused: common:config`: `git push -u` wrote branch tracking into the shared `.git/config` during the open attempt. Removing the two `branch.<name>.remote` and `.merge` entries restored it. This is the defect captured in `docs/product/captured/supervisor-common-config-residue.md`.

## Run review and terminal (2026-10-30)

- Reviewers selected: `adversarial-reviewer` (always) and `security-reviewer`; `experience-reviewer`, `frontend-reviewer`, `design-reviewer` and `quality-engineer` omitted with reasons in `delivery/review-selections.jsonl`. Each left one non-material Nit, assessed supported and deferred: F1, the reference names fewer cases for `committed-records-only` than the code reports; S1, no test drives the non-`FileNotFoundError` lookup refusal.
- During the first adversarial review attempt, another session rewrote the shared `.git/config` (3,330 to 3,360 bytes), refusing the attempt `attempt-residue: common:config`. The original bytes could not be restored. The owner (eugenelim) authorized re-baselining that attempt's `common:config` digest to the current bytes after it was checked for code-running keys (none); the baselined bytes and the manifest before the edit are kept under `.context/reviews/supervisor-fresh-checkout-status-impl/`.
- `regenerate` rebuilt `.claude/skills/work-loop/` from the pack source (byte-identical), committed at `ea7ccbbeb`; a second `run-gates` and a delta review of that commit followed. A `regenerate` result carries no facts: the supervisor refuses a `gate` fact there, though the reference's request table lists one.
- The run reached `terminal` at `dd15eab9c`.

## Finish evidence (2026-10-30)

- `make build-self` on `dd15eab9c`: exit `0`, no diff.
- Plain fresh `git clone` of `dd15eab9c` from `origin`, no rebuild, no `.git/agentbundle-supervisor`: `status docs/specs/supervisor-fresh-checkout-status --check` exit `0`, `terminal: true`, `verification: committed-records-only`, empty `refusal`; shipped `pre-pr.py` exit `0`, `pre-pr: ✓ supervisor status docs/specs/supervisor-fresh-checkout-status` and `pre-pr: all checks passed`.
- Pull request #1666, build-check run 41169153777 on `dd15eab9c`: `gate-main` step `pytest catalogue-test carve-out destinations (RFC-0082)` success, which runs `tests/roster/test_core_pre_pr_hook.py` including `test_shipped_pre_pr_runs_no_linter_labels` with this spec's `delivery/` in its sandbox; every check on the pull request passed.
- Locally on `dd15eab9c`: `status --check` exit `0`, `verification: pinned`.

## Release rebase (2026-10-31)

`main` released core 4.0.2 (#1665) while this pull request was open, so the branch merged `origin/main` and re-released core as 4.0.3, one patch above the new merge base; the changelog fragment was replaced. `check-core-release.py --base origin/main` reports the release consistent.
