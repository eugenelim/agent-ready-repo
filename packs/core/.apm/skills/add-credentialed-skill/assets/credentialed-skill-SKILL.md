# Template: credentialed-skill SKILL.md body

Two variants below. Pick the one matching your `metadata.primitive-class`
frontmatter and copy *everything under* the variant heading verbatim
into your skill's `SKILL.md` body. Replace `<namespace>` and `<service>`
placeholders; leave the rest unchanged. The lint
(`tools/lint-credentialed-skills.sh`) checks for the verbatim phrases
inside the `### Security rules (non-negotiable)` section.

---

### Variant: credentialed-cli

For primitives invoked as a Python CLI from skill bodies. The storage
convention (Tier 1 → 2 → 3) applies; the argv ban refuses
`--token` / `--api-token` / `--api-key` / `--bearer` / `--pat` /
`--password` flags.

```markdown
# Skill: <your-skill-name>

<one-line description of what the skill helps the user accomplish>

## How this skill works

This skill calls the `<service>` API via the credentialed primitive
at `scripts/cli.py`. The primitive owns the token; the skill body
never sees it.

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

## Usage

Invoke the primitive via `subprocess.run([sys.executable,
"scripts/cli.py", "<verb>", ...])`. The primitive resolves
credentials inside its own process and constructs the API call
without surfacing the token to the LLM.
```

---

### Variant: mcp-server

For primitives that run as a long-lived MCP server. The storage
convention does **not** apply (the server holds no on-disk credential
state); header-naming flags (`--bearer-header`, `--auth-header`,
`--header-prefix`) are explicitly allowed because they name *which*
header to consult per-request, not the credential value.

```markdown
# Skill: <your-skill-name>

<one-line description>

## How this skill works

This skill drives the `<service>` MCP server. The server is wired
into the user's MCP host configuration; the skill body issues
tool calls through the MCP transport.

### Security rules (non-negotiable)

- The server may accept tokens per-request via headers (the
  `--bearer-header`, `--auth-header`, `--header-prefix` flags name
  *which* header to consult, not the value). **Never** log header
  values.
- The storage convention (Tier 1/2/3 dotfile, keyring) does **not**
  apply because nothing is persisted on disk by the server.
- **Never** put the token on the command line of any process this
  skill spawns. Header-naming flags are not value-shaped flags
  and are not banned, but a value-shaped flag like `--bearer`
  is.
- If the server returns an authentication error, tell the user
  to refresh the credential at its source — do not run any
  setup helper for them.

## Usage

The skill issues MCP tool calls. Configuration (host endpoint,
header names, auth scheme) is the user's responsibility and is
established out-of-band — the skill body does not write to the
host config.
```

---

## Notes for the author

- The credentialed-cli variant's "Don't" block is the verbatim
  three-bullet text from RFC-0006 § 4; the lint greps for those
  substrings. Editing the block breaks the lint.
- The mcp-server variant's "Don't" block is the parallel form
  (also from RFC-0006 § 4); the lint scopes its argv-ban
  enforcement to `metadata.primitive-class: credentialed-cli` only,
  so the mcp-server variant's header-naming flags are not flagged.
- Both variants live under one section in the template (this file)
  by design — drift between variants is easier to catch when both
  read at once.
