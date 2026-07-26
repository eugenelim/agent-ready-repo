# Credential Brokers

> A user-scope pack that gives credentialed skills secure in-process credential resolution through the OS keychain — cleartext never reaches the model context.

## Why this pack exists

Skills that need API tokens have to get them from somewhere. Without a credential broker, the options are bad: prompt the user each time (insecure and fragile), hard-code them (dangerous), or require environment variables that disappear across terminal sessions. With this pack, credentials are stored once in the OS native keychain and resolved silently at runtime through a four-layer chain — environment variable, keyring, dotfile, interactive prompt — without ever surfacing the raw secret in the conversation.

## What it is

**Skills (1):** `credential-setup` — an interactive walkthrough that helps users store API keys and tokens into the OS native keychain for later silent resolution.

**Libraries (2):** The `credbroker` pip-installable library provides in-process resolution for skills that declare `auth: creds` — it is what skills call at runtime to retrieve a credential without asking the user. The `sso-broker` subprocess binary provides SSO-cookie resolution for skills that declare `auth: sso-cookie` (primarily Atlassian SSO flows).

No subagents. No seeds.

See the README for the complete manifest table.

## What it is not

- Not a secrets manager or vault — it delegates storage to the OS keychain; it does not provide its own encrypted store.
- Not a multi-user or team credential store — credentials are stored per-user on the local machine.
- Not a replacement for proper secrets management in CI/CD environments — it is designed for interactive development contexts, not headless pipelines.

## How it relates to other packs

No required pack dependencies. The `atlassian` pack's SSO-authenticated skills (`jira`, `confluence-crawler`, etc.) rely on the `sso-broker` binary this pack installs. Other credentialed packs that declare `auth: creds` in their skill manifests consume the `credbroker` library at runtime.
