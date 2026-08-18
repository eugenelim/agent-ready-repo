---
title: "`credential-brokers` — guides"
summary: Understand and select the credential setup and broker interfaces that keep cleartext secrets out of agent context.
pack: credential-brokers
kind: explanation
---

# `credential-brokers` — guides

The credential layer behind every skill that touches a private API. A skill never holds a secret: it invokes a credentialed primitive — a CLI, an MCP server, a Python module — that resolves the secret in-process (environment variable → OS keyring → dotfile) and makes the API call itself. Cleartext never reaches the model. The `credential-setup` skill walks a user through entering the keys a skill declares.

New here? Read [Credentialed skills](explanation/credentialed-skills.md) for the two-layer model, then [add a credentialed skill](how-to/add-a-credentialed-skill.md) when you're authoring one.

## How-to

- [Add a credentialed skill](how-to/add-a-credentialed-skill.md) — pick a broker, declare the credentials, and wire the verbatim security-rules blocks.

## Reference

- [`credbroker` SSO API](reference/credbroker-sso-api.md) — the consumer surface for `auth: sso-cookie`: resolving a jar, re-establishing an expired session, first capture, destination derivation, and which failures a consumer may recover from.

## Explanation

- [Credentialed skills](explanation/credentialed-skills.md) — the two-layer architecture, why skills don't hold tokens, and how it differs by install route.

---

Installing and upgrading live in [`../_shared/`](../_shared/). The shipped `jira` and `figma` skills are runnable references for the pattern.
