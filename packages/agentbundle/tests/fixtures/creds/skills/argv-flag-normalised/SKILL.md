---
name: argv-flag-normalised
description: Credentialed-CLI fixture exercising the AC27 normalisation paths — casing, kebab, and string-add obfuscation; AC26(b)+AC27 findings expected.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
---

Body with the full "Don't" block so only AC26(b) variants fire:

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
