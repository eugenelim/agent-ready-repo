# governance-extras

The RFC/ADR ceremony layer on top of `core`. Adds the skills and templates for
running a lightweight decision-record process.

## What's inside

- `new-rfc`, `new-adr`, and `update-conventions` skills.
- RFC/ADR templates and seed READMEs scaffolded into `docs/`.

## Install

`governance-extras` is **repo-scope** — RFC/ADR ceremony is per-project. It
**requires `core`** (`^0.1`); install `core` first or alongside.

```
agentbundle install --pack governance-extras <catalogue>
```

## Usage

Ask your agent, for example:

- "Draft an RFC proposing we adopt trunk-based development."
- "Record an ADR for the decision to use Postgres over DynamoDB."
- "Update our conventions to require conventional-commit messages."

---

→ **Go deeper:** the [`governance-extras` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/governance-extras/).
