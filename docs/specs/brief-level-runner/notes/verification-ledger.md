# Verification ledger — brief-level runner, run run-3602f673069eaa18

## Run restart (2026-11-06)

Owner call: take main in even if it means restarting. Main 6fe5a6be7 (Core 4.0.20) merged; Core bumped to 4.0.21. The earlier run run-02cd0b018dc06f9c could not continue on the newer supervisor; its store is kept under round-1/old-run-store-run-02cd0b018dc06f9c/ with SHA256SUMS.txt, and its history on local branch c-backup-pre-restart. Its ledger is round-1/verification-ledger-staged.md, which also records the T16 false gate pass and its superseding admission.

The new run started on a base of main plus ADR-0159, the spec and the plan, at the owner-approved digests 46313976… (spec) and 2d91ba4d… (plan). T1's report committed the whole implementation; T2–T9 changed no code beyond one test repair.

## Task gates

- T1: lint clean; test_supervisor_policy_lease.py + test_supervisor_tdd.py with WORK_SUPERVISOR_INTEGRATION=1, 52 passed in 10 min 15 s (t1-tests.txt). A first run without the variable skipped 39 and was not used.
- T2–T9: all-gates-1.txt, one run over every suite the tasks name. One failure: test_brief_runner.py::test_git_calls_are_read_only_and_hardened. Cause: after the main merge, the supervisor's Git helper (borrowed for the filter-name read) also makes a version probe, a discovery rev-parse and a plain config listing, and the test began recording them. Repair: the test checks each source in its own hardened form (brief-runner-rerun.txt holds the failure). Re-gate: lint clean, test_brief_runner.py 143 passed in 21 min 57 s (t2-brief-runner-tests.txt).

## run-gates 1 (gates:dc76e8cf8f8620c80955fc77)

Every criterion is checked for real; the old run's AC-0026/0027 conditional no longer applies.
- AC-0001–AC-0025, AC-0028–AC-0033: all-gates-1.txt (lint clean; brief-runner 151 unit, 16 guidance; lease 13; parked-gates 10; narrow-full-mode 11; step0 eval 4; human-approval pin 6; tdd failed_attempts 2; roster registry 32; ci parity ok; spec status clean) plus the test_brief_runner.py re-gate (143 passed).
- AC-0026: tools/check-core-release.py --base origin/main: "release is consistent" (4.0.21 over main's 4.0.20).
- AC-0027: agentbundle catalogue lint --root . --deep ok; catalogue verify ok; self-host --write left the tree clean.

## Round 1 repairs and amendment 1 (2026-11-06)

- Round-1 review (adversarial, security, quality): 24 findings, 13 material (A1–A5, S1–S3, Q1–Q4, Q8), recorded with supported assessments; the 11 non-material ones are recorded as such.
- Amendment 1 (A2 option 1, A5, submodule rule, internal-error) was approved by the owner ("spec and plan approved") at commit c645b946, spec digest a3cf8de0…, plan digest 78be9f15… The digests were re-confirmed on the pending gate before use. The amendment commit changed only spec.md and plan.md, with 0 product paths, so I answered adopt-history (history-adoption-request-1.json, history-adoption-answer-1.json). Approval pair 2 was admitted.
- T10: lint clean; test_brief_runner.py 153 passed (15 min 36 s); units 169; guidance 18; every other named suite green (t10-all-gates.txt). Mutation checks: without `--ignore-submodules=dirty`, the staged-submodule filter ran (mutation-no-ignore-submodules.txt); without `-I`, the planted module loaded (mutation-no-isolated-interpreter.txt). The runner was restored byte for byte.
- T11: main shipped Core 4.0.21 (PR #1705), so the release moved to 4.0.22. check-core-release: "release is consistent"; roster registry 32 passed (t11-gates.txt).

## run-gates 2 (gates:2a0b4612136a4b9ce64a6890)

- AC-0001–AC-0026 and AC-0028–AC-0033: t10-all-gates.txt plus t11-gates.txt (AC-0026 real: 4.0.22 over main's 4.0.21).
- AC-0027: conditional pass under the owner's decision (relayed 2026-11-06: "C: yes, same condition as before"). Before regenerate, `agentbundle catalogue verify --root .` exits 1 with CAT-V-015, drift only in the installed copies of brief-runner.py, references/brief-runner.md and evals/evals.json (ac0027-before-regenerate.txt, ac0027-drift-paths.txt). catalogue lint --deep passes.
- The pinned supervisor issues run-gates again after regenerate. The regenerate commit changes the subject manifest (_supervisor_readiness.py:120-148), verdicts count only for the current fingerprint (:723-731), readiness_action issues run-gates when no gates ran for the subject (:806-818), and decide() checks readiness before issuing regenerate (_supervisor_loop.py:445-458). Paths are under .claude/skills/work-loop/scripts/. At that second run-gates, catalogue lint --deep and catalogue verify are run again for real and reported as they come out.

## Review round 2 (2026-11-06)

- Every round-1 finding was confirmed fixed except A6, which closes at closeout. 7 new findings: A8, Q15, Q16, S5 and S6 are material; A9 and Q14 are not.
- S5 (security, Major, reproduced by the reviewer) was accepted as risk by risk-owner eugenelim on 2026-11-06 (owner decision relayed by the planner, option 1). The finding: the runner's read-once filter-name read and its later `git status` are separate Git calls. A filter set in between by a worker with write access to the shared Git directory, racing a set/unset/back-date loop, can run as the operator. Git has no flag that disables `.git/info/attributes` filters; `--attr-source` with an empty tree was tested on Git 2.56. The supervisor's own Git helper has the same pattern. Recorded with `accept-risk` (accept-risk-s5.json). Follow-on: docs/product/captured/read-once-filter-names-race.md (via T12), which fixes the runner and the supervisor's Git helper together.
- The owner (direct message, 2026-11-06) allowed exactly one more review round for A8, A9, Q14, Q15, Q16 and S6, with any residue after round 3 to come back to the owner. The supervisor issued `review-not-eligible`, not `review-cap`: a protected unit has no cap. So the limit is held by the controller.
- Repairs: T10 was reissued (its slice-head test line was corrected for A8), and T12 was added. Mutation check: without `hidden_change`, both S6 tests fail (mutation-no-hidden-change.txt).

## T10 (reissued), T12 and run-gates 3 (gates:6535fbea33158c904769fd51)

- T10 reissued: lint clean; test_brief_runner.py 155 passed (20 min 6 s); units 170; guidance 18; every other named suite green; ci parity ok; check-core-release "release is consistent" (t10r2-all-gates.txt). The first run was stopped at the 1-hour background limit during the spec-status lint. The remaining checks were then rerun: spec status clean, catalogue lint --deep ok, catalogue verify CAT-V-015 on the same three installed files only (t10r2-rest-gates.txt). Projections were restored after self-host.
- T12: the follow-on docs/product/captured/read-once-filter-names-race.md is read by dispatch.py as an open defect with no findings; the captured-item roster tests passed (126).
- run-gates 3: AC-0001–AC-0026 and AC-0028–AC-0033 pass on the evidence above. AC-0027 is a conditional pass under the same owner decision, still before regenerate. The pinned supervisor files are unchanged, so the re-issue citations above still hold. At the run-gates after regenerate, catalogue lint --deep and catalogue verify are run again for real.

## Review round 3, amendment 3, T13 and run-gates 4 (2026-11-07)

- Round 3: A8, A9, Q14–Q16 and S6 are fixed. New findings: A10, A11, Q17 and S7 are material; S8, S9, Q18 and Q19 are Nits. The owner (direct, 2026-11-07) chose to keep `git status` and settle the contract around it. S7 (a forged index stat cache in the shared Git directory) was accepted as risk by risk-owner eugenelim on 2026-11-07 (accept-risk-s7.json) and added to the follow-on item. The owner first picked a full filter-free rewrite. Its pre-review found 3 Major issues (symlinked parent folders, the confined-read rule, mode changes), so the owner switched to the narrower option.
- Amendment 3 was approved by the owner ("amendment 3 approved") at commit cc2f5fe4, spec digest 517e4532…, plan digest 40de0e39…. The digests were re-confirmed on the pending gate first. The adoption covered only spec.md and plan.md, with 0 product paths (history-adoption-request-3.json, -answer-3.json). Approval pair 3 is admitted.
- T13: lint clean; test_brief_runner.py 159 passed (11 min 5 s); units 173; guidance 18; every other named suite green; check-core-release "release is consistent"; spec status clean; catalogue lint --deep ok (t13-all-gates.txt). Mutation check: with the two stat pins removed, the weakened-stat test fails (mutation-no-stat-pins.txt). It first failed with the pins in place, because the refresh and the edit fell in one second; a 1.1 s wait before the edit fixed that.
- run-gates 4 (gates:15379d29473c40ef6bc8659f): AC-0027 is a conditional pass under the same owner decision, still before regenerate (CAT-V-015 on the same three installed files). The re-issue citations still hold, since the pinned supervisor files are unchanged.

## Round 4, amendments 4 and 5, T14, T15 and run-gates 5 (2026-11-07)

- Round 4: security and quality clean; adversarial left A12 (Minor; a self-ignoring untracked `.gitignore` hid a spec from the base check) and Nits A13, S10, Q20. The owner chose to fix A12 (option 2).
- Amendment 4: AC-0002 refuses an untracked file named `.gitignore` in any letter case under the checked paths, except the supervisor's own `docs/specs/<slug>/.supervisor/.gitignore` holding exactly `*`. Its pre-review found a mixed-case `.GITIGNORE` bypass on case-insensitive disks (Blocker), fixed with `:(glob,icase)`. The owner approved ("amendment 4 approved"): commit 1e24109c, spec bdb2eb7b…, plan 36d5bbcd… The adoption covered the spec and plan only.
- T14: test_brief_runner.py 167 passed (19 min 29 s); units 173; guidance 18; all other gates green except the expected CAT-V-015 (t14-all-gates.txt). Mutation check: without the untracked-.gitignore check, 6 tests fail (mutation-no-gitignore-check.txt).
- Amendment 5 (owner request, relayed by the architecture session and confirmed directly by the owner): every `next` answer, a refusal included, carries `schema_version` 1; every action carries `base`; slice-naming actions and blocked rows carry `spec_path`; `await-merge` carries `spec_paths`. ADR-0159 is unchanged, because no decision there names output fields. The owner approved ("amendment 5 approved"): commit 28d650dc, spec 25bbfe08…, plan df5ccad0… The adoption covered the spec and plan only.
- T15: test_brief_runner.py 167 passed (6 min 26 s); units 181; guidance 19; release consistent (main at 4.0.21 at 6e58fe19b); all other gates green except the expected CAT-V-015 (t15-all-gates.txt).
- run-gates 5 (gates:0c5ff97ea10fa4d853837042): AC-0027 is a conditional pass under the same owner decision, still before regenerate. The re-issue citations still hold.

## Round 5, amendment 6, T16 and run-gates 6 (2026-11-07)

- Round 5: A13, Q20 and S10 fixed; T15 fields match AC-0009 for every action kind. Open: A12 / S11 (S11 recorded as A12's duplicate; an ignore file above the checked paths hid an untracked spec), Q21, Q22 and Nit A14. The owner chose to fix all four (option 1).
- Amendment 6: AC-0002 checks the `.gitignore` of every folder above the checked paths, up to the repository root. A change to one, an untracked one in any letter case, or a flagged one whose bytes differ refuses. Its pre-review found 1 Major (the letter-case match on parent paths was untested), 2 Minor and 2 Nits, all folded in. Approved by the owner ("amendment 6 approved"): commit 625f645f, spec b9edaaac…, plan b8312fed… The adoption covered the spec and plan only.
- T16: test_brief_runner.py 173 passed (7 min 10 s); units 184; guidance 20; all other gates green except the expected CAT-V-015; release consistent with main at 4.0.21 (131b17958) (t16-all-gates.txt). Mutation check: without `icase` on the parent paths, the uppercase parent test fails (mutation-no-parent-icase.txt).
- run-gates 6: AC-0027 is a conditional pass under the same owner decision, still before regenerate.

## Round 6, amendment 7, T17 and run-gates 7 (2026-11-07)

- Round 6: security clean; A12, A14, S11, Q21 and Q22 fixed. Open: A15 (a parent ignore file in another letter case escaped the status and flag checks), Q23, Q24, and Nit S12 (glob characters in a skill path). The owner: "fix all 4 and finish".
- Amendment 7: AC-0002 matches parent `.gitignore` files in any letter case for every check. Approved by the owner ("amendment 7 approved"): commit 66c3e5c7, spec afb2ac74…, plan 0957c7d0… The adoption covered the spec and plan only. No separate amendment check; round 7 reviews it.
- T17: test_brief_runner.py 177 passed (9 min 24 s); units 185; guidance 20; all other gates green except the expected CAT-V-015; release consistent (t17-all-gates.txt). Mutation check: with `icase` removed from the three parent checks, the 3 letter-case tests fail (mutation-no-parent-icase-all.txt). A scratch repository showed the escaped glob finds a hidden ignore file under a `ven[d]or` path and the unescaped one does not.
- run-gates 7: AC-0027 is a conditional pass under the same owner decision, still before regenerate.

## Round 7, regenerate and run-gates 8: the real AC-0027 check (2026-11-07)

- Round 7: adversarial and security clean (A15, S12, Q24 fixed); Nits A16 (a doubled comma in AC-0002, fixed at closeout) and S13 (a skill path beginning with `:` is read as pathspec magic; added to the follow-on). Q23 (Minor, narrowed: the parent letter-case match in the untracked listing is untested on a case-sensitive filesystem when only that one check loses it) was accepted as risk by risk-owner eugenelim on 2026-11-07 (accept-risk-q23.json).
- Regenerate: `make build-self && make bootstrap-sites` rebuilt only the six installed work-loop copies of brief-runner.py, references/brief-runner.md and evals/evals.json. The gates on the rebuilt tree passed: test_brief_runner.py 177 (8 min 20 s), units 185, guidance 20, every other suite, release consistent, catalogue lint --deep ok, catalogue verify ok (regenerate-gates.txt). The first report carried a `gate` field and was refused (`result-fact-refused`). A `next` call then replaced the open request with an `uncommitted-changes` decision. Recovery: restored the copies to HEAD, took a fresh regenerate request, rebuilt the same bytes, and reported the envelope only (admitted). The supervisor committed the copies as 140ab0af5.
- run-gates 8 (gates:b86f7ef039ad96b8b695c885) is the run-gates after regenerate. AC-0027 was checked for real on HEAD 140ab0af5: catalogue lint --deep ok (rc 0), catalogue verify ok (rc 0), self-host --write left the tree clean (ac0027-after-regenerate.txt). AC-0026: check-core-release "release is consistent". Every criterion passes for real, and the AC-0027 conditional is closed.

## Closeout (2026-11-07)

- Run run-3602f673069eaa18 reached `terminal` at 671e44198 with readiness ready. Reviews: 8 rounds across adversarial-reviewer, security-reviewer and quality-engineer (protected classes `security-boundary` and `public-interface`, so no round cap applied). The owner bounded the rounds directly from round 3 on. The last two rounds, 7 and the round 8 that runs after regenerate, were clean apart from Nits.
- Accepted risks (risk-owner eugenelim): S5 (2026-11-06), the read-once filter-name race; S7 (2026-11-07), a forged index stat cache; Q23 (2026-11-07), the parent letter-case match in the untracked listing is untested on a case-sensitive filesystem when only that check loses it. Follow-on: docs/product/captured/read-once-filter-names-race.md, which also names Nit S13.
- Durable outputs: ADR-0159 is Accepted and cited in `Constrained by:`. The work-loop `SKILL.md`, `references/brief-runner.md` and the `unattended-loops.md` pointer are covered by the guidance tests (green). `docs/architecture/work-loop-execution-supervisor.md` § 9 names the `lease` table and what stays planned. `references/state-schema.md` lists no policy keys, so that row resolves to none. The release goes through check-core-release (AC-0026, green at 4.0.22).
- Non-material findings left open, by owner direction or as Nits outside the accepted criteria: Q5 (`classify` reads the whole brief and has no overall time limit); Q6 (the measured CI headroom of the shared integration job, checked on the PR's CI run); Q7 (function-scoped fixture cost); Q12 (process-global filter cache); Q13 (private supervisor names); S13 (a skill path beginning with `:`, in the follow-on). Fixed at closeout: A6 (spec Shipped, checkboxes). Left open: A16, AC-0002's doubled comma. Correcting it changes a protected criterion's text, and a fresh clone's `status --check` then refuses `criteria-changed`, so the fix waits for the next amendment of this spec.

## Appendix: the earlier run, run-02cd0b018dc06f9c

That run could not move to the newer supervisor after main was merged. Its store is kept under the planner's evidence folder as old-run-store-run-02cd0b018dc06f9c/, with SHA256SUMS.txt. Its history is kept on local branch c-backup-pre-restart. Its ledger follows unchanged. It includes the T16 false gate pass, recorded in commit 74e0f1e9b and superseded by a real admission.

### Verification ledger (staged) — brief-level-runner

Staged outside the spec directory while a supervisor attempt is open; copied to docs/specs/brief-level-runner/notes/verification-ledger.md at closeout.

## Run-gates 1 (run run-02cd0b018dc06f9c, after T7 45eab5084), 2026-11-06

Owner decision (relayed by the planner, msg-66cf861b-5a9e-4405-8709-b114656a76bc): report AC-0026 and AC-0027 as pass now, conditional on proof that run-gates is issued again after regenerate, then check both for real.

Proof that run-gates runs again after regenerate (installed copy, .claude/skills/work-loop/scripts/):
- _supervisor_loop.py:410-425 — `decide` returns readiness work (run-gates, review) first; `regenerate` is issued only once readiness has no request.
- _supervisor_attempt.py:1291-1303 — `pending_regeneration` is due while HEAD holds the pack source and the installed skill differs. This branch changes pinned supervisor files (_supervisor_loop.py, _supervisor_admission.py, supervisor-policy.json, new brief-runner.py), and .claude/ and .agents/ installs are tracked, so regenerate is due.
- _supervisor_readiness.py:113-142 — the delivery subject's manifest is every tree entry of the result commit outside the spec directory, and the acceptance fingerprint derives from it; the regenerate commit rewrites the tracked installs, so the fingerprint changes.
- _supervisor_readiness.py:239-242 and :305-318 — gate receipts count only for the current fingerprint; with none, `run-gates` is issued again for every criterion.
- SKILL.md:391 states the same: after regenerate the run reruns run-gates and the reviews once.

State before regenerate:
- AC-0026: pending the merge with origin/main. Branch version 4.0.18; merge base 28098e32b at 4.0.16; origin/main at 4.0.17 (task F's PR #1699 also targets 4.0.18, so the final number is re-derived after the main merge). check-core-release --base origin/main: "release is consistent" (t7-core-release.txt).
- AC-0027: `agentbundle catalogue verify --root .` exit 1, CAT-V-015 self-host projection out of date, drift only in the work-loop installed copies (ac0027-before-verify.txt).
- Reported pass in run-gates 1 under that decision. Other 29 criteria: real evidence in run-gates-1.txt.

Owed after regenerate and the main merge (not reusable from this entry): run catalogue lint --deep, catalogue verify and check-core-release for real; record results here; stop if either fails.

## Run-gates 2 (after T8 44cab25b3, review round 1 repairs), 2026-11-06

Same owner decision (still before regenerate). Real evidence for the other 29 criteria: run-gates-2.txt (lint clean; brief-runner 147 unit + 123 integration + 11 guidance; lease 13; contract and guidance 25; approval pin 6; failed_attempts 2; release-pin roster 32; CI parity ok; spec-status clean).
- AC-0026: still pending the main merge. origin/main now carries Core 4.0.18 (task F); check-core-release --base origin/main reports "version is 4.0.18, expected the patch successor 4.0.19". The bump to 4.0.19 (pack.toml, plugin.json, fragment version and anchor, roster release pin) is made after the main merge, then check-core-release is re-run.
- AC-0027: unchanged (projection drift until regenerate).

## Run-gates 3 (after T9 3593caac1, review round 2 repairs; approval pair 2 admitted db880feb6), 2026-11-06

Same owner decision (still before regenerate). Real evidence for the other 30 criteria (AC-0033 now included): run-gates-3.txt (lint clean; brief-runner 151 unit + 136 integration + 11 guidance; lease 13; contract and guidance 25; approval pin 6; failed_attempts 2; release-pin roster 32; CI parity ok; spec-status clean).
- AC-0026: still pending the main merge; check-core-release --base origin/main: "version is 4.0.18, expected the patch successor 4.0.19".
- AC-0027: unchanged (projection drift until regenerate).

## Run-gates 4 (after T10 03da82567, review round 3 repairs), 2026-11-06

Same owner decision (still before regenerate). Real evidence for the other 30 criteria: run-gates-4.txt (lint clean; brief-runner 151 unit + 141 integration + 11 guidance; lease 13; contract and guidance 25; approval pin 6; failed_attempts 2; release-pin roster 32; CI parity ok; spec-status clean).
- AC-0026: pending the main merge; check-core-release: "version is 4.0.18, expected the patch successor 4.0.19".
- AC-0027: unchanged (projection drift until regenerate).

## Run-gates 5 (after T11 97429bc74, review round 4 repair), 2026-11-06

Same owner decision (still before regenerate). Real evidence for the other 30 criteria: run-gates-5.txt. AC-0026 pending the main merge (check-core-release expects 4.0.19); AC-0027 projection drift until regenerate.

## Run-gates 6 (after T12 67c783c9d, review round 5 repair), 2026-11-06

Same owner decision (still before regenerate). Real evidence for the other 30 criteria: run-gates-6.txt. AC-0026 pending the main merge (check-core-release expects 4.0.19); AC-0027 projection drift until regenerate.

## Run-gates 7 (after T13 6ca53999f, review round 6 repair), 2026-11-06

Same owner decision (still before regenerate). Real evidence for the other 30 criteria: run-gates-7.txt. AC-0026 pending the main merge (check-core-release expects 4.0.19); AC-0027 projection drift until regenerate.

## Run-gates 8 (after T14 535bba1bd, review round 7 repair; T12/T13 re-traced as guidance content pins by owner decision 2026-11-06), 2026-11-06

Same owner decision (still before regenerate). Real evidence for the other 30 criteria: run-gates-8.txt. AC-0026 pending the main merge (check-core-release expects 4.0.19); AC-0027 projection drift until regenerate.

## Run-gates 9 (after T15 6428302e3, review round 8 repair), 2026-11-06

Same owner decision (still before regenerate). Real evidence for the other 30 criteria: run-gates-9.txt. AC-0026 pending the main merge (check-core-release expects 4.0.19); AC-0027 projection drift until regenerate.

## Controller error: false gate pass on T16 (2026-11-06)

- Commit 74e0f1e9b ("work-supervisor: implement T16 Review round 9 repairs") records T16's implement-task gate as passed. That record is false: the controller started the report before reading the gate result, and the gate run had 1 failed, 166 passed (t16-tests.txt; reproduced in t16-false-pass-evidence.txt). The controller killed the report process, but the supervisor had already admitted it.
- The failure: `test_the_refusal_section_names_exactly_the_runners_codes`. T16's new sentence puts the backticked `resume-slice` inside the "When a verb refuses" section, and the test read every backticked hyphenated token in the section as a refusal code. The guidance text is correct; the test's scope was too wide.
- Correction: a working-plan edit to T16's `Tests:` (code-list scope limited to the section's code-list sentence; no protected section touched) gives T16 a new revision, which the supervisor reissues. The superseding admission records the real gate result (see the next entry). No ref was moved by hand. The later run-gates re-runs the full suite independently.
- Process fix: no report is started until the gate result has been read and passed.
- Superseding admission: T16 revision 2 admitted as c41002e0e with a real passing gate (lint exit 0; guidance + unit suites 167 passed, t16-revision2-tests.txt), after the code-list test was scoped to the section's code-list sentence. A mutation removing `git-unavailable` from that sentence turns the test red.

## Run-gates 10 (after T16 c41002e0e), 2026-11-06

Same owner decision (still before regenerate). Real evidence for the other 30 criteria: run-gates-10.txt (rc=0; every suite passed). AC-0026 pending the main merge: origin/main moved again, check-core-release now expects 4.0.20; AC-0027 projection drift until regenerate.
