---
name: credential-setup
description: Interactive credential setup for skills declaring `metadata.auth` of creds. Walks the user through entering each required key from the skill's `creds-schema.toml` and writes to the highest-available tier (OS keychain on Darwin/Windows; 0600 dotfile floor on Linux). Triggers on "set up credentials", "credential setup", "credential broker setup". This is interactive, user-invoked, do not auto-run.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: creds
---

# Skill: credential-setup

This skill is the **single LLM-cooperative exception** to the
brokers-not-skills rule (per RFC-0013 § 4e). It lives at
`<skills-dir>/credential-setup/` rather than at adapter-root because
its job is to *prompt the user for a token* — an LLM-discoverable
operation by design. The skill's body says, explicitly: this is
interactive, user-invoked, do not auto-run.

> **Do not invoke this skill on the user's behalf.** Tell the user to
> run it themselves; pause for their action; resume your task when
> they confirm the credential is in place.

### Security rules (non-negotiable)

- Secrets live only in `~/.agentbundle/credentials.env`
  (mode 0600 on POSIX; DACL-restricted on Windows), the OS keyring,
  or process environment variables.
  **Never** read that file, print it, or echo the token.
- **Never** put the token on the command line. This script
  refuses flags like `--token` / `--api-token` / `--bearer` /
  `--pat` / `--password` and exits — do not work around it.
- This script is interactive only. It refuses non-tty stdin with
  exit code 3 — do not run it for them via pipe, here-doc, or any
  other non-interactive mechanism.

## When the user runs this

After installing a credentialed skill that declares `auth: creds`,
the user runs:

```bash
python3 scripts/setup.py <namespace>
```

Or, with an explicit schema path:

```bash
python3 scripts/setup.py <namespace> --schema-path <path>
```

The script:

1. Refuses the reserved `sso` namespace (per RFC-0013 § 4b — the
   `sso-cookie` broker owns the `agentbundle:sso:*` keychain
   target-name prefix and the `credential-brokers` pack reserves
   the `sso` namespace globally for that broker's use).
2. Locates `creds-schema.toml` (explicit `--schema-path`, or walks
   the configured adapter's skills directories looking for a
   matching `[namespace] name`).
3. Prompts via `getpass.getpass` for keys declared `secret = true`;
   via `input()` for `secret = false`.
4. Writes each `(namespace, key)` to value to:
   - **macOS / Windows**: OS keyring (Tier 2). Default behaviour.
   - **Linux** (no Tier-2 backend): 0600 dotfile at
     `~/.agentbundle/credentials.env` (Tier 3 floor).
   - **macOS / Windows + `--allow-insecure-fallback`**: Tier 3
     dotfile. The flag exists for adopters on corporate machines
     where the keychain is unavailable to scripted callers.
5. Prints a one-line stderr announcement of where the credential
   landed (`wrote to keyring (macOS Keychain)`, etc.). Never
   prints the entered value.

## Exit codes

- `0` — every key written successfully.
- `2` — reserved namespace (`sso`) refused.
- `3` — schema not found, stdin not a tty, Tier-2 hard fail,
  permissive DACL on Windows, or any other interactive precondition
  unmet.

## Inverse — verifying resolution

To verify resolution after setup, invoke the consumer skill's own
`check` verb (e.g. `python3 scripts/cli.py check` for a credentialed-
CLI primitive). The consumer's `check` walks Tier 1 → Tier 2 → Tier 3
through the build-projected `credentials_shim` and exits 0 when every
declared key resolves. This skill writes; the consumer's `check`
reads. Do not write a `get` verb in this skill — the RFC-0006 § 5
wrap-and-leak shape is explicitly refused.
