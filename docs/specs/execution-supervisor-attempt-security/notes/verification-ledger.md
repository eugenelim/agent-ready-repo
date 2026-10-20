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
