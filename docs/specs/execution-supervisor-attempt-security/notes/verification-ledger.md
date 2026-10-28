# Verification ledger: execution supervisor attempt security

All five tasks are built. T1 began as a probe inside PR #1557 (`execution-supervisor-core`); T1 to T5 shipped together in PR #1585 as Core 3.1.18 on 2026-10-24. The [acceptance evidence](#acceptance-evidence) section maps every criterion to the test that proves it.

## T1: Windows launches run in a breakaway-denied Job Object

### Host

GitHub Actions `windows-latest`, Python 3.11.9, job `AgentBundle compatibility (windows)` in `build-check-windows.yml`.

### What the Job Object suite verified

`packs/core/tests/skills/work-loop/test_process_safety_windows.py` gates the Windows job. It passed (13 passed, 27 s) on code head `4d7142d8c` (run 39279070391), after the fixes below. Each test pins one behaviour:

- **Kill-on-close, no breakaway (AC-0021).** The child reads its own job's limits: `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` is set, and neither `BREAKAWAY_OK` nor `SILENT_BREAKAWAY_OK` is.
- **Suspended start, assign, then resume.** A forced assignment failure ends the suspended process and refuses with `denied-job-object`, so no code runs outside the job.
- **Timeout leaves no survivor (AC-0023).** A leader and a grandchild that outlive the timeout are both gone after the `denied-timeout` refusal.
- **Contract cases (AC-0024).** Exit codes, environment allowlisting, stdin delivery, redaction of stdin and environment values, truncation at the output bound, and `denied-output-cap-exceeded` for a tree that keeps writing.
- **Handle list (AC-0024).** An inheritable file handle the parent opens does not reach the child. `PROC_THREAD_ATTRIBUTE_HANDLE_LIST` limits inheritance to the three standard-stream pipe ends.
- **Batch files are refused.** `.bat` and `.cmd` executables, including names ending in a dot or a space (which Windows strips), are refused with `denied-non-native-executable`.

### Behaviour found and fixed during the probe

- **Output past one pipe buffer.** An anonymous pipe holds about 4 KB. The first reader stopped reading at the output cap, so a child that wrote 5,000 bytes blocked on its write, and the launch was refused as a flood. The reader now keeps draining and discarding past the cap for the POSIX settle window (0.2 s). Only a tree still running when that window closes is refused. A 1 MiB write that then exits now returns a truncated success.
- **A flood after the leader exits.** The post-exit wait on the pipes fixed its timeout when it started, so a descendant that flooded after the leader exited held the launch until its deadline. The wait now runs in 50 ms slices over a fresh snapshot of the live readers, so the settle window applies and a reader finishing mid-check ends the wait cleanly. A test pins the refusal inside 10 s against a 20 s launch timeout.
- **Hashing the pinned executable** reads it in binary mode, so the identity digest matches the file on disk.

### The POSIX suite on Windows (evidence only)

`test_process_safety.py` runs on Windows as a non-gating step, bounded to 5 minutes. On code head `4d7142d8c` it gave 3 failed, 86 passed, 21 skipped in 3.3 s.

- **Skips (21):** tests that need `os.killpg`, `mkfifo`, `/proc/self/fd`, `/bin/sh`, `waitid`, or POSIX-only environment bytes.
- **Failures (3), all POSIX expectations, not Windows defects:**
  - `TestPostAllowDenialEvents::test_launch_failure_stores_denial_event` and `TestNulByteDenial::test_non_oserror_from_popen_mapped_to_process_denied` patch `subprocess.Popen`, which the Windows branch does not call.
  - `TestExecIdentityMechanism::test_symlink_executable_refused` expects `denied-launch-failed`. Windows answers `denied-executable-identity-changed`, which still refuses the launch.

### Why the Windows job used to hang

Before the fixes, the evidence step never finished: the job ran to its limit, was cancelled, and its log was lost. Step limits did not end it either. Splitting the suite across one job per test isolated `TestRedactionAtTheCapAndAtScale::test_redaction_cost_stays_linear`. That test launches no process. Its parameters hold 1–2 MiB byte strings, and pytest built each test ID from them, giving IDs of 1–2 million characters. pytest copies the current test ID into the `PYTEST_CURRENT_TEST` environment variable, and Windows caps a variable at 32,767 characters. Naming each case by its label fixed it; the evidence step now takes about 4 s. That edit touches a suite AC-0025 says passes unchanged; its inputs and assertions are identical, and the owner accepted it against AC-0025 on 2026-10-14.

What happened between the oversized ID and the lost runner was not observed, because no log survived. The likeliest account is that the error output carried the multi-megabyte IDs and the Actions runner stalled processing them. That part is inference.

### Owner decision: Windows executable names (2026-10-20)

The T1 security review found two Windows executable forms the launcher accepts: a name carrying an NTFS stream suffix (`tool.cmd::$DATA`), which the batch-file refusal does not recognise, and a UNC or device path (`\\server\share\x.exe`, `\\?\…`, `\\.\…`), which widens the check-to-launch window. The owner (eugenelim) chose to refuse both on Windows with `denied-launch-failed`: any `:` other than a drive-letter colon, and any path starting with `\\`. This makes the launcher stricter and accepts no new risk, so no Windows-host proof of how `CreateProcessW` handles stream names is needed.

## T2: Owner decisions on the Git helper review (2026-10-20)

The owner (eugenelim) settled the three open T2 review findings:

1. **Security events.** Only a check that cannot be verified writes a `security-event.v1` line with its refusal: an unreadable `.git` entry or `commondir`, unreadable config, or `git` unavailable. Verified refusals (`unsupported-git-config`, a control-state mismatch) refuse with their stable code only, as AC-0009 states.
2. **Run id at the store boundary.** The supervisor store path code validates the run id against `run-[0-9a-f]{16}` itself, so no `build_commit` caller can skip the check. The run id is read from committed `delivery/approvals.jsonl` without a pattern check.
3. **User config location.** The Launch grants `git` row was falsified: without `XDG_CONFIG_HOME`, and on Windows `USERPROFILE`, `HOMEDRIVE`, and `HOMEPATH`, an out-of-helper config read cannot see a global filter or commit identity kept there, so AC-0009 misses it. The owner directs a controlled amendment that grants those variables to the out-of-helper config read only; the hardened helper's own environment is unchanged.

## T2: The Git helper as built, beyond the plan's design

The plan's Git helper design names its flags and carried settings. The helper as built adds these, each stricter than the plan:

- **`core.attributesFile`** points at the null device, and `core.excludesFile` defaults to it, so no user-level attributes or ignore file changes what a supervisor call stages.
- **Repository-defined filters are neutralized.** For each `filter.<name>` in repository or worktree config, every helper call passes empty `clean`, `smudge`, and `process` with `required=false`.
- **A graft file refuses.** `--no-replace-objects` does not stop Git reading `info/grafts`, so the helper refuses with `denied-git-control-state` when one exists.
- **Commits are built with `hash-object -t commit`**, identity and date written into the object, because the helper clears every `GIT_*` variable the grants table does not list.
- **`--literal-pathspecs`** replaces the `GIT_LITERAL_PATHSPECS` variable for the same reason.
- **A boolean `core.fsmonitor`** is not a code-running setting; any other value is.
- **Unverifiable checks log after the spec directory is confined.** A failure inside repository discovery, before the spec directory is confined, is a usage error with no security-event line, because no confined `.supervisor/` directory exists yet to hold one.

## T2 and T3: Owner decision on where the made-commit list applies (2026-10-20)

The supervisor integration lane on PR #1585 failed three core tests that rebase a run's history with its messages preserved: `test_rebase_preserving_messages_converges`, `test_a_rebase_after_the_push_does_not_reopen_it`, and `test_a_finish_push_runs_once_and_survives_a_rewrite`. T2 counted a commit as the supervisor's only when its id was in the made-commit list, and a rebase gives every commit a new id, so the shipped core guarantee that a message-preserving rebase converges was falsified.

The owner (eugenelim) chose to apply the made-commit list only during an open worker attempt, where every commit after the manifest's `HEAD` must be listed. Outside an open attempt the supervisor reads its commits by their trailers, as core does, and replace refs and graft files are still never honored. A packed-ref move or a rewritten gitfile or `commondir` is a forgery only a worker could make, and a worker acts only during an attempt, so those cases move from T2 to T3. AC-0012 is narrowed to match, by controlled amendment.

T3 also edits the core crash-corpus variant `test_supervisor_commit_during_a_live_lease`: its spec edit moves from inside the open attempt to after the report, because an edit to a trusted file during an open attempt cannot be told apart from a worker's and is now refused as attempt residue.

## T3: Existing core tests changed by the attempt checks

The attempt checks run before core's own refusals and refuse any trusted-file change during an open attempt, so four existing core integration tests change. Each keeps what it asserts:

- `test_supervisor_step_loop.py`: the worker-edit cases now expect `attempt-refused`. Core's `protected-path-changed` and `authority-changed` refusals stay asserted by `test_supervisor_effects.py` and the VI-4030 rows.
- `test_supervisor_crash_corpus.py::test_supervisor_commit_during_a_live_lease`: the spec edit moves to after the report, as the owner decision above records.
- `test_supervisor_commit.py`: the foreign `delivery/` edit during an open attempt now expects `attempt-residue`, and a new sibling, `test_a_foreign_delivery_edit_with_no_open_attempt_is_refused_by_next_and_report`, keeps core's `foreign-delivery-edit` refusal asserted when no attempt is open.
- `test_supervisor_commit.py::test_returning_to_earlier_spec_content_is_a_new_replan`: each spec edit now follows the report of the issued attempt, with its replan assertions unchanged.

A re-approval `start` during an open attempt advances `HEAD` only when the spec declares no `## Terminal Intent` and a `spec-plan` start follows a `code` approval; the kill-point tests cover that path, and the other two `start` outcomes, `current` and `attempt-residue`, make no commit and fire no kill point.

## Owner direction: close the deferred nits (2026-10-21)

The owner (eugenelim) directed that the deferred review nits be worked:

- **Kill-on-close in the contract.** AC-0021 now states that the Job Object ends every member when its last handle closes. That a supervisor crash then leaves no launched descendant is an inference from this flag and the job handle being unnamed and non-inheritable; no test ends the supervisor and checks for survivors. The plan's Windows Job Object design already sets `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, and the T1 suite's `test_child_is_in_a_kill_on_close_job_without_breakaway` already asserts the flag on a real Windows host.
- **`Owned by:` names T5.** T5 also changes the LLD's surfaces (`_supervisor_git.py`, `_supervisor_loop.py`), so the LLD's owner list includes it.
- **T3 also touched `_supervisor_admission.py`.** T3 is complete, and a completed task's section is not edited by amendment, so this is recorded here instead: T3 builds `ws.attempts` and calls `guard("start")` in `_supervisor_admission.py`, the admission path AC-0004 requires.

## T4: Owner decisions on the review of pinning and the untrusted gate (2026-10-21)

The owner (eugenelim) settled two points from the T4 review:

1. **Which issuances are attempts.** AC-0013 needs a baseline for code the supervisor launches, so a `run-gates` request, a `regenerate` request, and a red proof or scratch receipt launched with no attempt open each record a manifest and count as an open attempt, as worker requests do. A trusted-file edit by anyone while one of them is open is therefore attempt residue. The source digests a `regenerate` is checked against are the ones the supervisor records from the pack source at `HEAD` when it issues the request, because an entry point can read no Git object before its pin check; `report` recomputes them from `HEAD` and admits only an exact match. The spec's Manifest and Open attempt definitions and AC-0014 are amended to match.
2. **A regenerate with the installed skill tracked in the work tree.** The regenerated skill is a working-tree change the supervisor does not commit, so after the `regenerate` is admitted `next` answers `uncommitted-changes` until the controller commits it. AC-0016 states this step, and VI-5032 covers the tracked-install case.

T4 changed two existing core tests, each keeping what it asserts:

- `test_supervisor_admission.py`: the helper `_start` takes a code-trust value, and the interrupted-start test starts `trusted`, because an `untrusted` start with stubs now answers a human decision (AC-0017) instead of a `write-stub` request.
- `test_supervisor_commit.py::test_a_malformed_record_is_one_json_refusal`: the damaged approval line keeps the run's own id, because a line naming an unpinned run is refused `supervisor-changed` first; the test still asserts `malformed-record`.

The pre-import pin check runs before any sibling can load, so it writes its `security-event.v1` line by hand in the shape `_security_events.py` defines, not through that module; this is where AC-0014's "before importing any sibling" and the rule to reuse Slice 1 primitives for events meet.

## T4: Owner decisions on the second review round (2026-10-21)

The owner (eugenelim) settled two more points:

1. **Runs admitted before pinning shipped.** Such a run has a supervisor store (its made-commit list) but no pin record, so every entry point refuses it, and its unpinned store directory also blocks every other spec in the worktree. A controller-run `start --repin-legacy-run` pins it from the installed bytes, writes a `security-event.v1` line, and only acts when the run's store has made-commit ids and no pin record; it never overwrites or accepts a differing pin record. The release note names this path and the worktree-wide refusal.
2. **The `regenerate` exemption is no wider than what admission checks.** Admission compares every file of the installed skill directory with the pack source at `HEAD`, not only the pinned modules and policy files, and when the installed skill is tracked in the work tree the next issuance first confirms that the committed installed skill equals what was admitted.

This entry also supersedes the scope of the 2026-10-20 decision on the made-commit list: that list now applies during every open attempt as the amended Open attempt definition names them, so a rebase during an open `run-gates`, `regenerate`, or supervisor launch is refused and converges only outside an open attempt (AC-0012).

## T4: Owner re-decision on runs admitted before pinning (2026-10-21)

The second-round decision rested on a wrong premise: no released Core version writes the supervisor store, which first ships with this spec, so a run admitted by Core 3.1.14 or earlier has committed approvals and no store at all, and `start --repin-legacy-run` could not reach it. The supervisor is dark (no skill invokes it), so no adopter holds such a run in practice. The owner (eugenelim) therefore withdrew the legacy re-pin: there is no recovery path, and a run admitted by an earlier release is refused `supervisor-changed` on its own spec and must be started over. The release note says so.

A run store directory with no pin record exists only in the window between the first admission's made-commit write and its pin write, and after a crash inside that window. While it stands, every entry point except `start` refuses `supervisor-changed` on its own spec, which the directory records when it is created; that run's `start` records the pins and lifts it. AC-0014 states this.

## T4: Owner decisions on the fourth review round (2026-10-21)

The owner (eugenelim) settled two scope questions:

1. **The pin check guards the whole worktree.** Every entry point, on every spec, refuses `supervisor-changed` when the installed supervisor files differ from the pins of any run whose store holds an open attempt, so a worker's edit during spec A's attempt cannot run, or be pinned, under spec B.
2. **The untrusted gate covers `regenerate`.** Under an `untrusted` classification with no verified containment, `next` emits no `regenerate` request and answers the same `human-decision` as for gates.

The same round also settles, without an owner choice: the pinned file set is every file under the installed `scripts/` except `__pycache__`, plus the two policy files; a first pin needs the run's store to already hold its made-commit record, so a released run (no store) is refused even when it stopped after its first approval; each store directory records its spec when created, so an unpinned run directory blocks only its own spec, and that spec's `start` ignores (not deletes) one none of whose made-commit ids is reachable from `HEAD`, judged through the hardened helper because no `git` call may run outside it before the pin check; and a `<spec-dir>` whose case differs from the tracked path is refused. T4 also changed `_supervisor_admission.py` (the first-pin call and the code-trust re-approval), which its Touches line omits.

## T4: Owner decisions on the closing review round (2026-10-21)

The owner (eugenelim) chose to fix all three closing-round findings:

1. **A refusal keeps guarding other specs.** A run whose latest issuance is refused and not yet cleared guards every spec as an open attempt does, so an installed-file edit that a launch or worker attempt was refused for cannot run, or be pinned, under another spec while its residue stands.
2. **A store directory is never visible without its spec record.** The supervisor builds a new run's store directory under a temporary name with its spec record inside, then renames it into place, so no crash leaves a spec-less directory. A spec-less run directory can only come from tampering; it refuses every spec, fail closed, and is lifted only by removing it.
3. **The case-variant check runs on every host.** The VI-5031 case-variant test asserts the exact refusal on case-sensitive and case-insensitive filesystems alike.

## T5: Owner decision on the implement-task result row (2026-10-22)

The sealed Result acceptance row let an `implement-task` or `write-stub` result assert nothing, but shipped core reads the task's gate outcome from that result: `report_task` needs `gate.passed`, and core's `gate-fail` line, its implementation retry cap, and the crash corpus depend on it, while `execution-result.v1` describes `gate` as the controller-run gate outcome. The owner (eugenelim) chose to admit exactly that controller-run gate outcome on those rows; the result still asserts nothing about the change set, which the supervisor computes, and every other fact on it is refused.

The pre-EXECUTE security review of that amendment (round 13) found that under `untrusted` with no verified containment, a task with no stubs was still issued as `implement-task`, so a gate run outside containment could earn a pass receipt around AC-0017. The owner (eugenelim) chose to give it the same AC-0017 `human-decision` as `run-gates`: AC-0017 now withholds `implement-task` too, proved by VI-5042 under T5. The review's nit is folded in: `write-stub` admits no asserted facts. The adjudicator refuted the request to back "controller-run" with gate evidence, because ADR-0144 D11 already trusts the controller and makes a relayed worker claim inadmissible.

## T5: Owner decision on the supervisor's launch routing (2026-10-23)

T5 routed the red proof through the Slice 1 safe-process primitive. The primitive refuses a link as the program, so the implementation resolved the link itself. Every virtual environment's `python` is a link to the base interpreter, so the child lost that environment's packages: `python -m pytest` answered `No module named pytest` and exited 1, which is the exit a red stub declares. The supervisor recorded a red proof for a stub that never ran, and the conftest fixtures of VI-5030 and VI-5031 stopped detecting their attack because the conftest never ran either. The runners did not show this, and cannot: their interpreter is a real file with the packages installed.

Three repairs were drafted and reviewed across rounds 15 to 17, and each was holed on one point — whatever decides the child's import surface is writable by the code the supervisor launches. Running the link and pinning its target fails on Linux, where the primitive execs the resolved descriptor. Passing the environment's `site-packages` on `PYTHONPATH` puts a directory inside the execution root on the import path of the supervisor's own evidence. Keeping the program name and bounding where it may point checks location rather than writability, admits the temp and home trees that launched code can also write, and its other clause cannot fail, because the pinned file is derived by resolving the located name.

The owner (eugenelim) chose on 2026-10-23 to defer rather than draft a fourth design. Two further drafts were needed to state the deferral correctly. The first kept AC-0019 for `git` alone; round 18 refuted it from the repository's own record, since `docs/architecture/runtime-security-primitives.md` already states the hardened helper does not launch through the primitive "because the primitive redacts every environment value from the output it returns, which would alter Git's data output", `HOME` prefixes a normal repository path, and the helper's `cat-file --batch` calls carry stdin the launcher has no parameter for. The second deferred AC-0019 and AC-0020 together; round 19 refuted that too, because T2 already built the bounded `git` child environment (`_supervisor_git._INHERITED_ENV`), so dropping AC-0020 would have de-specified a shipped control and accepted a risk the slice does not carry.

What ships: AC-0019 is removed and owned by `supervisor-launch-routing-for-plan-authored-commands`, which carries all three launch kinds and the measured obstacle for each. AC-0020 stays, narrowed to the `git` child's environment, which the helper enforces today. `_supervisor_launch.py` is removed from all three projections. The Launch grants table is adopted per column and per kind, and the spec says which. `GIT_CONFIG_SYSTEM` is added to the `git` row, because the shipped out-of-helper read forwards it and the row did not list it.

Accepted Risk records two residuals with the owner's acceptance of 2026-10-23: a `red-proof` or `scratch` child runs the worker's own stub with the supervisor's whole environment and no egress denial, and a worker can declare a `run` line that cannot start and earn a red proof with no failing test behind it. The second is owned by `red-proof-discriminates-a-stub-that-ran`. Rather than record a one-off observation on a host with a virtual environment, T5 adds VI-5043: the planted conftest records that it executed, and both cases assert that record. The refusal assertions already failed once the attack stopped running, so the marker names the cause rather than adding detection.

The owner also noted that a Shipped spec is a historical record and not binding, so `safe-process.v1`'s ownership by `acceptance-authority-and-evidence` was never a reason to defer.

## Closeout: the review-role pair (2026-10-28)

PR #1585 left one gap open against AC-0018. `accept_facts` admitted a `review-role` result that carried both a report and a selection, where the Result acceptance row admits one or the other. Both downstream readers already refused the pair with `invalid-result`, so no such result was ever admitted. `accept_facts` now refuses it first with `result-fact-refused`, and VI-5040 carries the case.

## Owner decision: Git-directory discovery is a helper call (2026-10-28)

`discover` in `_supervisor_git.py` runs `git rev-parse` before any directory is pinned, so it cannot pass `--git-dir` or compare control state. It carries the helper-call environment and fixed flags. The owner (eugenelim) classed it as the helper's first call, not as a third out-of-helper call. AC-0010's pre-check has no baseline until discovery returns the pins it then holds every later call to.

## Acceptance evidence

Every test below lives in `packs/core/tests/skills/work-loop/`. The integration suites run only with `WORK_SUPERVISOR_INTEGRATION=1`; CI runs them in the `Gate A-supervisor` lane of `catalogue-tooling-ci-gates.yml`.

The binding runs are on `main` at `449151c4c` (2026-10-28):

- `catalogue-tooling-ci-gates.yml` run 40636854667: `Gate A-supervisor` and both `Gate A-packs` lanes passed.
- `build-check-windows.yml` run 40636854664: `test_process_safety_windows.py` gave 18 passed in 27.6 s on `windows-latest`.

The closeout branch reran every suite below locally on macOS, Python 3.11, with the integration lane on.

### Attempt checks and residue

| Criterion | Evidence |
| --- | --- |
| AC-0001 | VI-5020: `test_supervisor_attempt.py::test_a_forged_change_is_refused_at_report` (plan, cited ADR, `evidence.jsonl`, branch ref, `refs/replace/`, config, hook), `test_a_modified_installed_skill_is_refused_at_report`, `test_a_rewritten_gitfile_is_refused_at_report`, `test_a_packed_ref_move_is_refused_at_report` |
| AC-0002 | VI-5021: `test_next_after_an_edit_is_residue_before_any_envelope_refusal` |
| AC-0003 | VI-5021: the same test, for an implementer and a reviewer, on a first issuance and on the re-issuance after the refusal clears; `HEAD`, the made-commit list, and `run.json` stay unchanged, so no `replan` commit or projection change lands |
| AC-0004 | VI-5022: `test_a_resolve_effect_during_an_open_attempt_does_not_refuse_it`, `test_a_resolve_effect_killed_during_an_open_attempt_converges`, `test_a_re_approval_start_during_an_open_attempt_advances_head_and_passes`, `test_a_re_approval_start_killed_during_an_open_attempt_converges`, `test_a_re_approval_start_refused_for_a_changed_trusted_file_fires_no_kill_point`; core's `test_supervisor_crash_corpus.py` |
| AC-0026 | VI-5025: `test_a_rewrite_or_a_commit_with_copied_trailers_refuses_the_attempt` (`reset --soft`, `commit --amend`, `commit -C`) |
| AC-0027 | VI-5025: `test_deleting_the_local_caches_neither_admits_a_forgery_nor_clears_residue` |
| AC-0005 | VI-5023: `test_residue_persists_until_every_path_is_restored` |
| AC-0006 | VI-5023: the same test asserts that `HEAD` and the made-commit list stay unchanged through the refused ADR and plan edits, and that no `replan` commit appears |
| AC-0007 | VI-5024: `test_a_link_in_the_change_set_is_refused` (out of the root, into a trusted file, into `.git`) |
| AC-0008 | VI-5024: `test_an_honest_attempt_that_imports_the_installed_scripts_passes`, `test_a_link_inside_the_root_to_an_ordinary_file_is_admitted` |

### Git hardening

| Criterion | Evidence |
| --- | --- |
| AC-0009 | VI-5010: `test_supervisor_git.py::test_start_refuses_a_code_running_key_in_repository_config`, `test_every_listed_code_running_key_is_refused_by_name_never_by_value`, `test_start_refuses_a_code_running_key_in_worktree_config`, `test_start_refuses_a_global_filter_that_an_attributes_file_uses`, `test_start_refuses_a_global_filter_kept_under_xdg_config_home`, `test_a_global_filter_that_no_attribute_uses_does_not_refuse`; VI-5044: `test_start_refuses_a_system_filter_that_an_attributes_file_uses` |
| AC-0010 | VI-5011: `test_planted_code_runs_nothing_during_any_supervisor_git_call`, `test_carried_autocrlf_stages_the_bytes_plain_git_add_stages`, `test_a_global_excludes_file_is_carried_into_the_change_set_read` (a user `core.excludesFile` keeps its file out of the change set; removing the carry turns it red); the open-attempt pre-check by VI-5020's gitfile and packed-ref cases |
| AC-0011 | VI-5011: `test_planted_code_runs_nothing_during_any_supervisor_git_call` (hook, fsmonitor, filter, textconv, external diff, SSH signing, include) |
| AC-0012 | VI-5012: `test_a_replaced_supervisor_commit_is_read_as_the_original`, `test_a_graft_is_never_read`, `test_a_message_preserving_rebase_still_reads_the_supervisor_commits`; open-attempt clause by VI-5020's `test_a_packed_ref_move_is_refused_at_report`, `test_a_gitfile_or_commondir_aimed_at_a_decoy_is_never_admitted`, `test_an_attempt_already_reported_stays_closed_after_a_message_preserving_rebase` |

### Launched code, pinning, and trust

| Criterion | Evidence |
| --- | --- |
| AC-0013 | VI-5030 with VI-5043's marker: `test_supervisor_pinning.py::test_a_conftest_that_writes_plan_md_during_a_red_proof_is_refused`, `test_a_conftest_that_writes_plan_md_during_a_gate_run_is_refused`. The supervisor has one launch path, `_supervisor_tdd.observe`, which runs each stub on a scratch copy of `HEAD`; a scratch receipt has no launch of its own, so the red-proof case covers it |
| AC-0014 | VI-5031: `test_the_first_admitted_start_records_the_pins`, `test_a_second_start_neither_overwrites_nor_accepts_a_differing_record`, `test_a_missing_or_malformed_pin_record_after_admission_is_refused`, `test_an_edited_installed_file_is_refused_at_every_entry_point`, `test_a_run_admitted_before_pinning_is_refused_and_blocks_no_other_spec`, `test_an_unpinned_run_directory_blocks_only_its_own_spec_until_its_start_pins`, `test_an_installed_file_edit_during_an_open_attempt_is_refused_on_every_spec`, `test_a_worker_attempt_refused_at_report_guards_other_specs`, `test_a_kill_before_the_store_rename_leaves_no_run_directory_and_blocks_nothing`, `test_a_run_directory_without_a_spec_record_refuses_every_spec_until_removed`, `test_a_case_variant_spec_dir_is_refused_before_any_sibling_loads` |
| AC-0015 | VI-5031: `test_a_planted_bytecode_file_is_never_executed`, `test_a_module_planted_in_scripts_never_runs_and_is_refused` |
| AC-0016 | VI-5032: `test_one_regenerate_is_emitted_admitted_and_repinned`, `test_a_tracked_install_waits_for_the_controller_to_commit_the_regenerated_skill`, `test_a_committed_skill_that_differs_from_the_admitted_one_is_refused`, `test_an_install_whose_other_files_differ_from_the_source_is_refused`, `test_a_mismatched_install_is_refused`, `test_no_regenerate_without_the_pack_source_at_head` |
| AC-0017 | VI-5033: `test_untrusted_trust_with_stubs_asks_a_human_instead_of_a_red_proof`, `test_untrusted_trust_never_issues_run_gates_and_re_approval_clears_it`, `test_untrusted_trust_never_issues_regenerate`, `test_verified_containment_lifts_the_gate`; VI-5042: `test_supervisor_results.py::test_untrusted_trust_issues_no_implement_task_for_a_task_without_stubs` |

### Result facts and the git environment

| Criterion | Evidence |
| --- | --- |
| AC-0018 | VI-5040: `test_supervisor_results.py::test_a_row_admits_the_facts_it_lists`, `test_a_row_refuses_everything_else` (now including the report-and-selection pair), `test_an_unknown_kind_asserts_nothing`, `test_report_refuses_before_any_write` |
| AC-0020 | VI-5041: `test_supervisor_git.py::test_a_helper_call_carries_exactly_the_helper_form`, `test_an_out_of_helper_config_read_carries_exactly_the_hosts_location_values` |

### Windows and POSIX

| Criterion | Evidence |
| --- | --- |
| AC-0021 | VI-5001: `test_process_safety_windows.py::test_child_is_in_a_kill_on_close_job_without_breakaway` |
| AC-0022 | VI-5001: `test_assignment_failure_refuses_and_ends_the_process` |
| AC-0023 | VI-5002: `test_timeout_leaves_no_survivor` (plain tree, exited intermediate, breakaway request) |
| AC-0024 | VI-5003: `test_launch_contract_cases`, `test_an_inheritable_parent_handle_does_not_reach_the_child` |
| AC-0025 | VI-5004: `test_process_safety.py` passes in both `Gate A-packs` lanes. Its last change is PR #1557's test-ID relabel, which keeps every input and assertion and which the owner accepted against AC-0025 on 2026-10-14 |

### Plan Done-when checks

- **Architecture review (2026-10-28).** A design review of the "Execution supervisor controls" section of `docs/architecture/runtime-security-primitives.md` returned SHIP WITH CHANGES. After adjudication it held four findings, all fixed in this change. The page's Result acceptance table now carries the spec's nine rows and three columns, so the page's tables match the spec's. Discovery and the two config reads are described in their own environment forms. The Launch grants references and the owning intent are linked. The control-state check names the open attempt's manifest as its baseline.
- **T5 security review (2026-10-28).** No clean T5 result had been recorded in PR #1585, so security-reviewer reviewed T5's controls at this change's head. After adjudication it held one Nit and no Blocker or Concern. The Nit, deferred: the helper relies on Git 2.32 or later to honour an empty `GIT_CONFIG_GLOBAL`, and no version floor is checked, so on Git 2.31 a helper call still reads the user's global config. AC-0009's filter refusal and the fixed `-c` overrides leave no code-running path in that case.
- T5's architecture page and changelog fragment make no claim that a `red-proof` or `scratch` launch is routed through the primitive, records a grant, or runs with a bounded environment. The page's "Launch grants" paragraph states that no supervisor launch goes through the process primitive.
- AC-0019 appears outside this spec only in `docs/product/intents/supervisor-launch-routing-for-plan-authored-commands.md`, the intent that owns it. That line records the removal; it does not claim the criterion is live. The owner (eugenelim) accepted that reference against this clause on 2026-10-28.
