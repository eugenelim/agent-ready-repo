# Verification ledger: execution supervisor attempt security

This spec stays `Draft`. Only T1, the Windows launch branch, has been built, as a probe inside PR #1557 (`execution-supervisor-core`). The records below are what that probe established on a real Windows host.

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
