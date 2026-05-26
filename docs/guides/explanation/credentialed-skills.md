# Credentialed skills

The `atlassian` and `figma` packs ship credentialed primitives — `jira`,
`figma`, `confluence-publisher`, `confluence-crawler`. Each one calls an
authenticated API on your behalf. None of them ever take your token on
argv, in an env-var the agent can echo, or in a string the LLM can see.

This page explains the model: why skills don't hold secrets, what a
credentialed primitive actually is, where your token lives, and why the
CLI has no `creds get` subcommand. The authoritative source is
[RFC-0006](../../rfc/0006-skill-secrets-storage.md); the implementation
spec is [`docs/specs/skill-secrets/spec.md`](../../specs/skill-secrets/spec.md).

## Skills don't hold secrets — primitives do

The catalogue draws a hard line between two things:

- A **skill** is an agent-facing workflow file. It tells the agent
  *what to do*: "to fetch a Jira issue, shell out to `python -m
  atlassian.jira get <issue-key>`." The skill itself never reads a
  token. It can't — the LLM reading the skill would see the token in
  the file.
- A **credentialed primitive** is a subprocess the skill shells out to.
  It loads its own credentials inside its own process, makes the API
  call, and writes the result to stdout. The token never crosses the
  agent's view.

The split means a skill is safe to commit, share, and audit. The
secret-handling lives one layer down, in code the LLM never sees.

## What a credentialed primitive looks like

Every credentialed primitive declares itself in frontmatter:

```yaml
metadata:
  credentialed: true
  primitive-class: credentialed-cli   # or: mcp-server
```

Two primitive classes:

- **`credentialed-cli`** — a Python module run as `python -m <pkg>`.
  It calls `load_credentials()` internally. It *refuses* any
  value-shaped credential flag (`--token`, `--api-key`, `--bearer`,
  `--pat`, `--password`) — passing one is a runtime error, not a
  silent acceptance. The skill that uses it knows to never construct
  such a flag.
- **`mcp-server`** — an MCP server that holds the secret across calls.
  May accept *header-naming* flags (`--bearer-header`,
  `--auth-header`) but never value-shaped flags. The token is loaded
  at server start and used internally.

`conventions-check` lints both rules — if you author a primitive that
accepts `--token`, the lint catches it before merge.

## Where your token lives

Three storage tiers, walked in order, first-hit-wins per key:

| Tier | Where | When it fires |
| --- | --- | --- |
| **Tier 1** | `<NAMESPACE>_<KEY>` env vars (e.g. `JIRA_API_TOKEN`) | CI runners. Wrapper scripts that inject secrets per-command. |
| **Tier 2** | OS keyring — macOS Keychain or Windows Credential Manager | Your daily-driver developer machine. The default. |
| **Tier 3** | `~/.agentbundle/credentials.env`, mode `0600` | Locked-down environments where you can't reach a keyring. Opt-in. |

You don't pick the tier — `agentbundle creds setup <namespace>` walks
top-down and writes to the highest-available tier. On macOS and Windows
that's Tier 2; on Linux today that's Tier 3 (libsecret support is
deferred to a future RFC).

On the wire, the tiers are stdlib-only. macOS uses
`/usr/bin/security` with the token passed via child stdin (never
argv). Windows uses `ctypes` against `advapi32` directly. The dotfile
gets POSIX `0600` (or a DACL-verified equivalent on Windows). The
catalogue ships no native dependencies.

## Why there's no `creds get`

You can run:

```bash
agentbundle creds setup jira       # interactive prompt, writes to keyring
agentbundle creds check jira       # confirms keys are present; never prints them
agentbundle creds where jira       # tells you which tier the token lives in
agentbundle creds rm jira          # removes from keyring
```

You **cannot** run `agentbundle creds get jira` — the verb doesn't
exist. Adding it would create a tool an agent could invoke to print
your token. The design hinge of the whole subsystem is: there is no
code path that returns cleartext to anything but the primitive that
needs it for the next outbound HTTP call.

If you need to verify your token interactively, run the primitive
itself with a low-stakes call (`python -m atlassian.jira whoami`).

## How this changes day-to-day usage

The first time you install `atlassian` or `figma`, the
`adapt-to-project` skill notices the new credentialed primitive and
prompts you through `agentbundle creds setup <namespace>`. That gesture
needs the `agentbundle` Python module on `$PATH` — if you installed via
`/plugin install` or `apm install`, follow
[the pip-install guide](../how-to/install-agentbundle-from-clone.md)
once to wire it in. After that, nothing changes: you ask the agent to
fetch a Jira issue, the agent calls the skill, the skill shells out to
the primitive, the primitive loads the token and makes the call. You
never see the token; the agent never sees the token; it lives in your
keyring until you `creds rm` it.

If you switch machines or rotate the token, you re-run `creds setup`.
If you hit the dotfile fallback on a locked-down workstation, the CLI
prints which tier it landed at and exits non-zero unless you passed
`--allow-insecure-fallback` — the surface telling you "you're on Tier 3,
make sure that's what you meant."

## Where to read next

- [How to add a credentialed skill](../how-to/add-a-credentialed-skill.md) —
  if you're authoring a new credentialed primitive.
- [`docs/architecture/credentials.md`](../../architecture/credentials.md) —
  the contributor-facing internals of the loader.
- [RFC-0006](../../rfc/0006-skill-secrets-storage.md) — the
  authoritative source on the three-tier design.
- [The example credentialed skill](../../../packs/core/.apm/skills/example-credentialed-skill/) —
  a runnable, no-op reference shipped in `core`.
