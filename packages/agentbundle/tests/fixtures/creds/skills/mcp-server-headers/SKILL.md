---
name: mcp-server-headers
description: MCP-server class fixture using header-naming flags (`--bearer-header`); AC26(b) ban is scoped to credentialed-cli only — lint must NOT flag this fixture.
credentialed: true
primitive-class: mcp-server
---

MCP-server class primitives legitimately accept header-naming flags
(`--bearer-header`, `--auth-header`, `--header-prefix`). The storage
convention does not apply because nothing is persisted; the SKILL.md
"Don't" block has a parallel form noted in RFC-0006 § 4.

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
