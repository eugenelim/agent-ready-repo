---
title: Store a credential
summary: Store a service credential from your terminal and check that its skill can resolve it.
pack: credential-brokers
kind: how-to
---

# Store a credential

Store a service credential from your terminal and check that its skill can resolve it.

## Install the broker pack

You run this in your terminal to install the user-scope setup skill:

```bash
agentbundle install --pack credential-brokers --scope user
```

The pack supplies `credential-setup`; the service's consumer skill supplies its credential schema, a `creds-schema.toml` file listing the keys it needs. This task stores static credentials; browser SSO uses a separate flow described in [Credentialed skills](../explanation/credentialed-skills.md).

## Store the required keys

You open the installed `credential-setup` directory in your terminal and run the following, replacing `service-name` with the schema's `[namespace] name` and the schema path with the consumer's file:

```bash
python3 scripts/setup.py service-name --schema-path /path/to/consumer/references/creds-schema.toml
```

The namespace groups that service's keys; `sso` is reserved and cannot be used here. You enter secrets only at the terminal's hidden prompts. Never paste them into chat, command arguments, a pipe, or a here-document. The agent must wait for you to finish; it must not run setup on your behalf.

Setup reports the storage destination without printing values. It uses the OS keyring when available. Without a keyring it uses the encrypted vault when crypto support is installed, otherwise the protected `~/.agentbundle/credentials.env` file. See the [setup reference](../reference/credentialed-skill-walkthrough.md#credential-setup-reference) for flags, permissions, and failures.

## Check resolution

You open the consumer skill's directory and run its documented check command, for a consumer that provides this verb:

```bash
python3 scripts/cli.py check
```

Exit zero confirms the required keys resolve; the check must not print them. Resolution tries environment variables before the keyring and file storage, so an environment value can take precedence over what you stored. Setup does not test service access; use the consumer's documented service check for that result.

Next: [Add credentials to a skill](add-a-credentialed-skill.md).
