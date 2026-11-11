# Verification ledger: proof-by-run evidence

Execution observations for this delivery. `<checkout>` is the worktree root. The supervised run's full history, including its `delivery/` records, is kept on the branch `<branch>-evidence`. The pull-request branch holds one squashed commit without `delivery/`.

## Supervised run

- **Run:** `run-ff526115ca1f3d9d`, intent `code`, code trust `trusted`.
- **Approval pairs:** 3. Pair 1 is the original approval. Pair 2 is the amendment of AC-0008 and AC-0033 with repair tasks T9 to T13. Pair 3 is the amendment of AC-0009, AC-0013, AC-0016, AC-0031, AC-0034 and AC-0035 with repair task T15. Each pair was approved by the owner.
- **Tasks:** all 14 complete (T1 to T6, T8 to T15), with retry count 0 of a cap of 5.
- **Terminal readiness:** `work-supervisor.py status --check` exits 0. All 35 criteria are `supported`. Adversarial, security and quality-engineer reviews ended `terminal-clean`, with no open findings.
- **Review rounds on the implementation:** 5, the last bounded to the regenerated projections.
- **Deferred Nit:** a comma splice in AC-0034 (round 4). It was fixed at closeout as punctuation only, with no change in meaning.

## Attempt residue re-baseline

At 17:29 on 2026-11-03, a fetch from outside this worktree rewrote `<common-dir>/info/refs` while the T5 attempt was open. The supervisor refused the report with `attempt-residue: common:info/refs`.

- **Why the old bytes were lost:** the manifest records only their size and SHA-256 (24217 bytes, `1abe4ed5…`), and a rebuild from reflogs did not reproduce them.
- **What the owner authorized:** editing only that one entry of attempt `000005.json` to the current file's size and digest. The report was then re-issued and admitted.

## Proof-by-run dogfood

The adversarial reviewer's finding `adversarial-1-1` carried a command: a scratch script that runs `evidence-gate.py proof-run` twice with 1 MiB inflating inputs.

| Run | Command | Exit | Observed | Record |
| --- | --- | --- | --- | --- |
| Before the fix, inside the open `assess-finding` request | the reviewer's command | 0 | the identical rerun refused `denied-envelope-exists` (defect shown) | `supported`, `proof-by-run.v1`, reference `proof-run:v1:19439f9d24dc89581e5a2cad08462d576a4be4c3:fail:bbe3b808ee7463cb544950756404ea1307236a8401f8cb272240105d0b590b18` |
| After the T9 fix | the same command | 0 | the identical rerun exits 0 (defect gone) | this ledger, per the FIX step |

Finding `adversarial-1-3` was recorded the same way. Its command, `evidence-gate.py git-history` run from a subdirectory, exited 2 with a generic `denied-git-control-state` detail, so the run was observed `fail`.

## Release history

Upstream released core 4.0.10 (#1680) during the run, so after the rebase this delivery ships as 4.0.11. The changelog fragment carries the same version and the date 2026-11-04.

## Delivery-time checks

These ran once after the final rebase, against merge base `3b1d0279d86d98824b8dd1c81ef1cf6702e1ab04` with freshly fetched `origin/main`.

| Check | Command | Exit |
| --- | --- | --- |
| AC-0016: every sentence of § Bounded evidence retry at the merge base is still present | sentence comparison of the section at `<merge-base>` against the working tree | 0 (0 missing) |
| AC-0019: adjudicator unchanged | `git diff --exit-code <merge-base> HEAD -- packs/core/.apm/agents/finding-adjudicator.md` | 0 |
| AC-0022: contracts and roster unchanged | `git diff --exit-code <merge-base> HEAD -- contracts/delivery/finding-assessment.v1.schema.json contracts/delivery/evidence-receipt.v1.schema.json contracts/delivery/finding-disposition.v1.schema.json packs/core/.apm/skills/work-loop/review-rules.json` | 0 |
| AC-0023: captured amendment present and linked | `docs/product/captured/proof-by-run-after-fix-run-binding.md` exists; the spec's Follow-ons links it | 0 |
| AC-0024: version one patch above the merge base | `pack.toml` and `plugin.json` both `4.0.11`; `<merge-base>` holds `4.0.10` | 0 |
| AC-0025: core release consistent | `python3 tools/check-core-release.py --base <merge-base>` | 0 |
| AC-0026: catalogue lint, verify, and self-host clean | `agentbundle catalogue lint --root . --deep`; `agentbundle catalogue verify --root .`; `agentbundle catalogue self-host --root . --write && git diff --exit-code` | 0, 0, 0 |
