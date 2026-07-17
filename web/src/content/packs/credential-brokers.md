---
name: Credential Brokers
scope: user
tagline: "Credential resolution — env → OS keyring → dotfile. Never cleartext."
skills:
  - credential-setup
installCommand: "agentbundle install --pack credential-brokers --scope user"
docsUrl: /docs/guides/credential-brokers/
---

Credential Brokers installs user-scope credential brokering: the `credbroker` library (pip-installed, in-process resolver for `auth: creds` skills) and `sso-broker` (subprocess-based resolver for `auth: sso-cookie` skills). The `credential-setup` skill walks through establishing credentials for a service. Cleartext credentials never reach the model — the broker resolves at invocation time and passes the value directly to the skill.
