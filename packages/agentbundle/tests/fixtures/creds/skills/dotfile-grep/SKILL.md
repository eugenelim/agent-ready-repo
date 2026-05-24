---
name: dotfile-grep
description: Credentialed fixture whose script opens `.agent-ready/credentials.env` directly without the opt-out marker; AC26(c) finding expected.
credentialed: true
primitive-class: credentialed-cli
---

Body with the full "Don't" block so only AC26(c) fires:

### Security rules (non-negotiable)

- Secrets live only in `~/.agent-ready/credentials.env`
  (mode 0600 on POSIX; DACL-restricted on Windows), the OS keyring,
  or process environment variables.
  **Never** read that file, print it, or echo the token.
- **Never** put the token on the command line. The primitive
  refuses flags like `--token` / `--api-token` / `--bearer` /
  `--pat` / `--password` and exits — do not work around it.
- If `check` exits with the "missing credentials" code, tell the
  user to run `agentbundle creds setup <namespace>` themselves.
  It's interactive — do not run it for them.
