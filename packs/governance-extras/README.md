# governance-extras

What this pack helps your team do — and keep a durable record of:

- **Record a decision you've made** — capture *what* you chose and *why*, so
  it outlives the people who made it.
- **Propose a change for discussion** — put a proposal in front of reviewers
  before anyone builds it.
- **Change your team's rules through review** — update shared conventions
  deliberately, not by drift.

It layers on top of `core`, adding the skills and templates that give those
outcomes a home: **`new-adr`** (record a decision), **`new-rfc`** (propose a
change), **`update-conventions`** (change the rules), and **`rfc-status`** (see
where proposals stand). *ADR = Architecture Decision Record; RFC = Request For
Comments* — you introduce them once you need them, not before.

## Install

`governance-extras` installs at **repo scope** — decision records are
per-project — which means **installing it adds capabilities and files to the
current project**: the skills, plus RFC/ADR templates and seed READMEs
scaffolded into `docs/`. It **requires `core`** (`^0.1`); install `core` first
or alongside.

```
# <catalogue> is your catalogue URI: a local clone path or a git+https://… URL.
agentbundle install --pack governance-extras <catalogue>
```

**Preview before you commit.** Because this writes into your project, run a
dry-run first to see exactly which files it would create — it prints a per-file
plan and writes nothing:

```
agentbundle install --pack governance-extras <catalogue> --dry-run
```

## Usage

Ask your agent, for example:

- "Record an ADR for the decision to use Postgres over DynamoDB."
- "Draft an RFC proposing we adopt trunk-based development."
- "Update our conventions to require conventional-commit messages."

Each skill shows you a preview of what it will write — the identifier, the
target path, and the content — and waits for your confirmation before creating
the file or updating any index.

---

→ **Go deeper:** the [`governance-extras` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/governance-extras/).
