# Verification ledger: execution supervisor attempt security

This spec stays `Draft`. Only T1, the Windows launch branch, has been built, as a probe inside PR #1557 (`execution-supervisor-core`). The records below are what that probe established on a real Windows host.

## T1: Windows launches run in a breakaway-denied Job Object

### Host

GitHub Actions `windows-latest`, Python 3.11.9, job `AgentBundle compatibility (windows)` in `build-check-windows.yml`.

### What the Job Object suite verified

`packs/core/tests/skills/work-loop/test_process_safety_windows.py` gates the Windows job. It passed (12 passed, about 29 s) on the branch head after the fixes below. Each test pins one behaviour:

- **Kill-on-close, no breakaway (AC-0021).** The child reads its own job's limits: `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` is set, and neither `BREAKAWAY_OK` nor `SILENT_BREAKAWAY_OK` is.
- **Suspended start, assign, then resume.** A forced assignment failure ends the suspended process and refuses with `denied-job-object`, so no code runs outside the job.
- **Timeout leaves no survivor (AC-0023).** A leader and a grandchild that outlive the timeout are both gone after the `denied-timeout` refusal.
- **Contract cases (AC-0024).** Exit codes, environment allowlisting, stdin delivery, redaction of stdin and environment values, truncation at the output bound, and `denied-output-cap-exceeded` for a tree that keeps writing.
- **Handle list (AC-0024).** An inheritable file handle the parent opens does not reach the child. `PROC_THREAD_ATTRIBUTE_HANDLE_LIST` limits inheritance to the three standard-stream pipe ends.
- **Batch files are refused.** `.bat` and `.cmd` executables, including names ending in a dot or a space (which Windows strips), are refused with `denied-non-native-executable`.

### Behaviour found and fixed during the probe

- **Output past one pipe buffer.** An anonymous pipe holds about 4 KB. The first reader stopped reading at the output cap, so a child that wrote 5,000 bytes blocked on its write, and the launch was refused as a flood. The reader now keeps draining and discarding past the cap for the POSIX settle window (0.2 s). Only a tree still running when that window closes is refused. A 1 MiB write that then exits now returns a truncated success.
- **A flood after the leader exits.** The post-exit wait on the pipes fixed its timeout when it started, so a descendant that flooded after the leader exited held the launch until its deadline. The wait now runs in 50 ms slices, so the settle window applies. A test pins the refusal inside 10 s against a 20 s launch timeout.
- **Hashing the pinned executable** reads it in binary mode, so the identity digest matches the file on disk.

### The POSIX suite on Windows (evidence only)

`test_process_safety.py` runs on Windows as a non-gating step, bounded to 5 minutes. On the branch head it gave 3 failed, 86 passed, 21 skipped in 4.4 s.

- **Skips (21):** tests that need `os.killpg`, `mkfifo`, `/proc/self/fd`, `/bin/sh`, `waitid`, or POSIX-only environment bytes.
- **Failures (3), all POSIX expectations, not Windows defects:**
  - `TestPostAllowDenialEvents::test_launch_failure_stores_denial_event` and `TestNulByteDenial::test_non_oserror_from_popen_mapped_to_process_denied` patch `subprocess.Popen`, which the Windows branch does not call.
  - `TestExecIdentityMechanism::test_symlink_executable_refused` expects `denied-launch-failed`. Windows answers `denied-executable-identity-changed`, which still refuses the launch.

### Why the Windows job used to hang

Before the fixes, the evidence step never finished: the job ran to its limit, was cancelled, and its log was lost. Step limits did not end it either. Splitting the suite across one job per test isolated `TestRedactionAtTheCapAndAtScale::test_redaction_cost_stays_linear`. That test launches no process. Its parameters hold 1–2 MiB byte strings, and pytest built each test ID from them, giving IDs of 1–2 million characters. pytest copies the current test ID into the `PYTEST_CURRENT_TEST` environment variable, and Windows caps a variable at 32,767 characters. Naming each case by its label fixed it; the evidence step now takes 4.4 s. That edit touches a suite AC-0025 says passes unchanged; its inputs and assertions are identical, and the owner accepted it against AC-0025 on 2026-10-14.

What happened between the oversized ID and the lost runner was not observed, because no log survived. The likeliest account is that the error output carried the multi-megabyte IDs and the Actions runner stalled processing them. That part is inference.
