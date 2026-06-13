# credential-brokers

User-scope credential brokering so credentialed skills never touch a repo's
files for secrets. This is the pack the other credentialed packs (`atlassian`,
`figma`) depend on.

## What's inside

- `credentials_shim` — a build-projected Python module that `auth: creds`
  skills import.
- `sso-broker` — a subprocess at `~/.agentbundle/bin/` for `auth: sso-cookie`
  skills.
- `credential-setup` — one LLM-cooperative skill that walks a user through
  storing credentials.

## Install

`credential-brokers` is **user-scope by default** — credentials belong to the
user, not the project. The broker is written to `~/.agentbundle/bin/` behind
the `.agentbundle/` user-prefix fence (RFC-0013).

```
agentbundle install --pack credential-brokers <catalogue>
```

## Set up credentials

After installing a credentialed pack, tell your agent **"set up credentials"**.
That triggers the interactive `credential-setup` skill, which prompts you for
each key the skill needs and stores it at the highest-available tier — your OS
keychain on macOS/Windows, or a `0600` dotfile (`~/.agentbundle/credentials.env`)
on Linux.

```
You: set up credentials
Agent: (runs credential-setup; prompts you for each token interactively)
```

Two rules the broker enforces, by design: **secrets never go on the command
line** (the setup script refuses `--token` / `--pat` / `--password` flags), and
the agent **never runs the setup for you** — it's interactive and user-invoked,
so the token is entered by you and never echoed back into the transcript.

## Usage

You don't invoke the broker directly — credentialed skills (e.g. `jira`,
`figma`) resolve their token through it automatically once `credential-setup`
has stored it. Re-run **"set up credentials"** any time you need to add or
rotate a key.
