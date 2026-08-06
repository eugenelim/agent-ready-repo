---
name: argv-flag
description: Credentialed-CLI fixture whose script accepts `--token` on argv; an argv-flag finding is expected.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
---

Body content with the full "Don't" block (so the missing-block check is silent and the
argv finding is the only one fired):

### Security rules (non-negotiable)

- Secrets live only in `~/.agentbundle/credentials.env`
  (mode 0600 on POSIX; DACL-restricted on Windows), the OS keyring,
  or process environment variables.
  **Never** read that file, print it, or echo the token.
- **Never** put the token on the command line. The primitive
  refuses flags like `--token` / `--api-token` / `--bearer` /
  `--pat` / `--password` and exits — do not work around it.
- If `check` exits with the "missing credentials" code, tell the
  user to run `agentbundle creds setup <namespace>` themselves.
  It's interactive — do not run it for them.
