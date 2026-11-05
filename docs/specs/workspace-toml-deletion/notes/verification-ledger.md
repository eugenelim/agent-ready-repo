# Verification ledger: workspace-toml-deletion

Execution observations and owner approvals for slice 9G of the workspace.toml retirement. Every approval names the SHA-256 of the file bytes the owner approved.

## Owner approvals

| Date | Approver | What | File | SHA-256 |
| --- | --- | --- | --- | --- |
| 2026-11-03 | eugenelim | spec and plan, at their approval | `docs/specs/workspace-toml-deletion/spec.md`; `docs/specs/workspace-toml-deletion/plan.md` | `df3dec6e444d262a584d8a5f47f38145ce2e09d9a340d95667e7ff15dda4d357`; `8a41b8e11ef277a2e0b9d886e79bf0272265b5aaad4916de0dec06600e05000c` |
| 2026-11-04 | eugenelim | RFC-0105 erratum wording, committed before `start` (commit `c684cde70`) | `docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md` | `0c2daa9ff87792f226058b7e77860b394d66faa5818dbbde17156d934ae21ac1` |
| 2026-11-04 | eugenelim | `workspace-retirement` amendment (criteria 0003, 0011, 0018, 0022 and 0030 to 0033; task T12) | `docs/specs/workspace-retirement/spec.md`; `docs/specs/workspace-retirement/plan.md` | `2eae8467bcf9f93db0b50e276bd3067dcb18e3b0d25283ccf911646a5f61e810`; `3ed06c520ac537e2729f9133fb7d64013170b79816c7f399cb29a6b0ad5ad848` |
| 2026-11-04 | eugenelim | closure checklist rows, 15 rows with 10 met (commit `0c9674da7`) | `docs/specs/workspace-retirement/retirement-record.md` | `7c84bcf9781bcf73cfd4409cd1138f351c6496118e7961b5503afe6996788e4d` |
| 2026-11-04 | eugenelim | moving the 9E and 9F spec-directory row pins to (`historical`, `none`), outside the approved surfaces (commit `3ab253282`) | `tests/roster/test_repair_only_workspace_status.py`; `tests/roster/test_registry_upgrade_notes.py` | `b8020f53c899b6448dbd9f92999985f61a679ab5ec2f7b2aa9739ebbc8e56dd0`; `9e1373011fd5117096e06875c3469dcdbacd7166117138eb78c16e824a8f4fc9` |
| 2026-11-04 | eugenelim | RFC-0064 erratum wording (commit `debe41637`) | `docs/rfc/0064-ini-001-ai-native-ecosystem.md` | `b9fe1b3528ec25957f26d2b7a0f6496bc45eddaa500787bc8a2b9b1824158a2a` |
| 2026-11-05 | eugenelim | activation gate recorded as passed, on the run below | — | — |
| 2026-11-05 | eugenelim | certification text, byte for byte the body of `retirement-record.md` § Certification | `docs/specs/workspace-retirement/retirement-record.md` § Certification | `e1064f3c96a612849a6824e5b1e17d2ddf3e849455016532838de6f7d66aa331` (the text plus a trailing newline) |

Other owner decisions recorded during the run, each given in session on the date shown:

- 2026-11-04: task T3 folded into T2, because T2's real-repository tests need the drafted table.
- 2026-11-04: the `Makefile` comment stays, because `tools/test_local_ci_shared_test_deduplication.py` byte-pins the `Makefile`; the `gemini_command_toml.py` docstring stays, because a package edit needs an engine-change trailer.
- 2026-11-05: `notes/closure-checklist.md`, added by #1687, reduced to a pointer at the record's checklist, so the closure has one home.
- 2026-11-05: the activation run on `bbad114db43c` stands after the base moved, because no skill, description or eval file changed since; the corpus and roster gates repeat on the new tested commit.

## Supervisor run

`run-06ccd3869b30d8bf`, started 2026-11-04 on a branch from `origin/main` at `88c952f49` (slice 9F merged). It went terminal with tasks T1, T2 and T4 to T8 complete, all 11 criteria supported, both reviewer obligations satisfied and 0 retries of a cap of 5. The full run history, `delivery/` records included, is on `evidence/workspace-toml-deletion`.

- Implementation review: adversarial reviewer and quality engineer, three rounds, each adjudicated. Round 1 upheld 8 findings (repaired in T7); round 2 upheld 3 (repaired in T8); round 3 upheld 3 Nits, deferred. Reports under `.context/reviews/workspace-toml-deletion/`.
- Deferred Nits: IA3-1 (a locator-only code span reports an empty token in the criterion 0030 message); QE3-1 (no fixture pins the trailing-slash bare-path arm); QE3-2 (no fixture pins the narrowed URL character class).

## Execution observations

- Frozen fact set: `test_frozen_registry_facts_match_the_registry_at_3b1d0279d` asserts the 19 frozen key paths equal the key paths of `workspace.toml` at `3b1d0279d`.
- Reader probe: deleting `workspace.toml` at `88c952f49` reddened eight reader suites, the inventory check and `tools/test_local_ci_shared_test_deduplication.py` (through the CLI suite's root finder), and nothing else among the 74 test modules that name it.
- Re-ownership: 399 rows `historical`/`none` and 155 `rfc-0067` after T5; T7 moved RFC-0105, RFC-0106 and RFC-0078 to `contract`/`rfc-0067`; the three closeout rows became `historical`/`none` at closeout.

## Gate runs

First tested commit: `bbad114db43c5a416de6e22123ac8a9e910ad83c`, the supervisor run's final product commit.

- `test-roster.yml`: https://github.com/eugenelim/agent-ready-repo/actions/runs/41930300476, success.
- `test-corpus.yml`: https://github.com/eugenelim/agent-ready-repo/actions/runs/41930296968, success.
- `pack-evals.yml` (run 41938172478) measured nothing: `ANTHROPIC_API_KEY` is unset in the repository, so every eval call errored, and the report-only step exits green. The scheduled run on `main` of 2026-11-02 (41470582963) shows the same.
- Activation, measured locally on `bbad114db43c` through the signed-in Claude CLI with the harness's own `ClaudeCodeDetector`, `run_eval` and `grade()`, 1 run per query, 8 at a time; the 102 runs that errored under that load (the 180-second timeout) were rerun with a 600-second timeout, 4 at a time, all clean. 276 of 362 queries passed; all 166 should-not-trigger queries stayed quiet; all 86 failures are should-trigger misses. Per skill: `workspace-status` 28/30, `navigate-intents` 49/59, `author-brief` 16/16, `receive-brief` 16/16, `author-delivery-brief` 20/25, `project-knowledge` 20/24, `adapt-to-project` 19/23, `new-spec` 17/21, `init-project` 15/19, `close-work` 15/19, `bug-fix` 15/27, `work-intake` 14/31, `intake-intent` 12/18, `explain-diff` 10/16, `repository-exploration` 10/18. The harness defines no pass threshold; the owner recorded the gate as passed.
- `git diff --name-only bbad114db43c <merged head>` lists no file under a `.apm/`, `skills/` or `evals/` directory.
