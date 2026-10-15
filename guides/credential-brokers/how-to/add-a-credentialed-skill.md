---
title: "Add credentials to a skill"
summary: "Keep credentials out of the AI loop: never in the repo, never in the agent's context. credbroker resolves them in-process."
pack: credential-brokers
uses: [credential-brokers]
kind: how-to
---

# Add credentials to a skill

Your skill can call an authenticated service while the credential stays out of the AI loop: never in the repository, never in the agent's context. A script in your skill resolves it with `credbroker`, inside its own process.

## Declare the credential

Name the broker and the keys in your skill's `SKILL.md` frontmatter:

```yaml
metadata:
  credentialed: true
  auth: creds
  namespace: your-namespace
  keys: ["API_TOKEN"]
```

The skill declares the key names only. The values never appear in the repository.

## The credentialed-skill contract

`metadata.auth` names how the credential reaches your script. Pick one of four brokers:

- `env` — a plain environment variable, for CI runners and containers.
- `cli` — a vendor command that is already signed in, such as `gh` or `aws`.
- `creds` — a static token you store once, read from your OS keychain. The example above uses it.
- `sso-cookie` — a browser session for a corporate single sign-on.

## Resolve it in your script

Call `credbroker` from the skill's `scripts/` code, not from the agent:

```python
from credbroker import load_credentials

creds = load_credentials("your-namespace", required_keys=["API_TOKEN"])
```

The script builds the API request itself. The agent sees the result, not the token.

## Set it up on first run

Say "set up credentials" in your agent. That starts the `credential-setup` skill from the [Credential Brokers](../../../packs/credential-brokers/README.md) pack. It prompts you for each key you declared and stores it in your OS keychain, so you type it once and it stays out of chat.

## Where the rest lives

Corporate SSO cookies, the other brokers, install options, and every lint rule are in the [credentialed skill walkthrough](../reference/credentialed-skill-walkthrough.md). For why the design works this way, read [Credentialed skills](../explanation/credentialed-skills.md).
