---
name: dotfile-with-optout
description: Credentialed primitive that legitimately reads the dotfile, with the opt-out marker on the same line; lint must NOT flag it.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
---

The credentialed-primitive itself (not a skill) legitimately reads the
dotfile. The opt-out comment names the relaxation explicitly so PR review
can see and approve.

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
