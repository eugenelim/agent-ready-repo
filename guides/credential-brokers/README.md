---
title: "`credential-brokers` — guides"
summary: Understand and select the credential setup and broker interfaces that keep cleartext secrets out of agent context.
pack: credential-brokers
kind: explanation
---

# `credential-brokers` — guides

These guides help you give a skill access to a service without putting a secret in the repo or in your agent's context.

## Start here

- [Add credentials to a skill](how-to/add-a-credentialed-skill.md) — Keep credentials out of the AI loop: `credbroker` resolves them in-process.

## More

- [Credentialed skills](explanation/credentialed-skills.md) — How a skill calls an authenticated service without exposing secrets.
- [Credentialed skill walkthrough](reference/credentialed-skill-walkthrough.md) — Every broker, step, and rule, from frontmatter to lint.
- [`credbroker` SSO API](reference/credbroker-sso-api.md) — The in-process API for checking, capturing, and using SSO sessions.
