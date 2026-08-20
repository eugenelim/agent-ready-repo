# Architecture Overview

> The directory map of this monorepo. For its systems, boundaries, flows, and
> state ownership, read [`ARCHITECTURE.md`](../../ARCHITECTURE.md).

## Layout

```
.
├── AGENTS.md             # canonical agent context (CLAUDE.md is a symlink)
├── AGENTS.local.md       # repo-specific addendum — self-host drift rules etc.
├── packages/
│   ├── agentbundle/      # the reference CLI + runtime library (Python, stdlib-only)
│   ├── credbroker/       # credential resolver used by credentialed pack helpers
│   └── _example/         # template package consumed by the new-package skill
├── packs/                # catalogue sources — one directory per pack
├── profiles/             # curated single-scope combinations of packs
├── guides/               # public adopter guidance, mirrored into the docs site
├── contracts/            # portable TOML/JSON contracts and schemas
├── docs/
│   ├── CHARTER.md        # mission, scope, principles
│   ├── CONVENTIONS.md    # how we work
│   ├── rfc/              # proposals (governance)
│   ├── adr/              # architecture decisions (frozen history)
│   ├── specs/            # feature specs and plans
│   ├── architecture/     # this directory — internals for contributors
│   ├── knowledge/        # living practitioner observations captured by core
│   ├── product/          # roadmap + changelog
│   └── guides/           # maintainer-only tooling and repository guidance
├── web/                  # authored marketing and catalogue site
├── docs-site/            # technical-doc shell; most content is generated
├── tools/                # build/lint/test scripts (.py preferred; .sh grandfathered)
├── .claude/              # Claude Code self-host projection — local only
├── .codex/               # Codex self-host agents + hook wiring — local only
└── .agents/              # Codex self-host skills — local only
```

`.claude/`, `.codex/`, and `.agents/` are generated from each pack's
`.apm/` sources by `make build-self` **solely so the catalogue eats its
own dog food** — the Claude Code and Codex projections are active when
you open this repo in those tools. They are **not** part of any pack's
deployment surface; adopters never see this exact self-host directory
set. The adopter-facing equivalents are produced by `make build` into
`dist/` (gitignored build output, regenerated on every CI run) under
`dist/claude-plugins/<pack>/.claude-plugin/` and
`dist/apm/<pack>/`; the install routes project equivalent content
straight into the adopter's own repo without needing to expose `dist/`.
Edit seeds under `packs/<pack>/.apm/...`, not these projections. See
[`AGENTS.local.md`](../../AGENTS.local.md) for the full drift workflow.

## Subsystems

The subsystem index and deeper links are in
[`ARCHITECTURE.md` § 8](../../ARCHITECTURE.md#8-deeper-current-state-pages).
