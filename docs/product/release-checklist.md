# Release checklist

> Manual-QA rows that GitHub Actions cannot exercise. Run through this
> before tagging a release; tick each row in the release PR description.

This file is *living* — every spec whose work needs out-of-band
verification should add a row here. The header for a spec's rows is the
spec slug; the row body is the exact behavior being verified.

## How to use this checklist

1. On the release branch, copy each section's checkbox block into the
   release PR description.
2. Run the manual exercise on a fresh machine where the spec applies
   (Windows VM, fresh macOS user, …).
3. Tick the box only when the exercise actually passes. A row that
   fails is a release blocker — file an issue, do not silently leave
   the box unchecked.

## skill-secrets (RFC-0006 / `docs/specs/skill-secrets/spec.md`)

The skill-secrets spec carries three Windows-specific behaviors that
GitHub Actions cannot exercise (no real PTY, single-session runner,
no `LocalSystem` service-account context). Each must be hand-verified
on a Windows host before the spec's work ships in a release.

- [ ] **`getpass.getpass` real-tty refusal** — on a Windows
      developer box with a real tty, run `agentbundle creds setup
      jira` (or any namespace with a schema). The prompt MUST appear,
      MUST hide the typed token (no echo), and the resulting Tier-2
      entry MUST round-trip via `agentbundle creds where jira`. CI
      unit tests monkeypatch `sys.stdin.isatty`; only the real tty
      path is hand-verified.
- [ ] **`CRED_PERSIST_LOCAL_MACHINE` survives logoff** — on a Windows
      box, run `agentbundle creds setup <namespace>`, log out, log
      back in, run `agentbundle creds where <namespace>`. The entry
      MUST still resolve at Tier 2 (CI runners are single-session and
      can't exercise this).
- [ ] **`ERROR_NO_SUCH_LOGON_SESSION` under `LocalSystem`** — schedule
      a Windows Task Scheduler job running as `LocalSystem` that
      invokes `agentbundle creds where <namespace>`. The task MUST
      exit 3 with stderr naming `ERROR_NO_SUCH_LOGON_SESSION (1312)`
      — proving the resolver does *not* silently fall through to
      Tier 3 in a no-logon-session context (AC11 / Boundaries §
      "No silent fallback from hard-fail Win32 error codes").

Cross-ref: `docs/specs/skill-secrets/spec.md` § Testing Strategy
"Visual / manual QA" bullet group.
