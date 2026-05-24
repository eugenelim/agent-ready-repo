# Architecture Overview

> The map of this monorepo. Read this first when exploring. Updated whenever
> the directory layout or major dependencies change.

## Layout

```
.
├── AGENTS.md             # canonical agent context (CLAUDE.md is a symlink)
├── apps/                 # deployable applications
│   └── <app-name>/       # one directory per app
├── packages/             # shared libraries (consumed by apps and other packages)
│   └── <package-name>/
├── tools/                # build, dev, and ops tooling — not shipped to users
├── docs/
│   ├── CHARTER.md        # mission, scope, principles (one page)
│   ├── CONVENTIONS.md    # how we work
│   ├── adr/              # architecture decisions (frozen history)
│   ├── rfc/              # proposals (governance)
│   ├── specs/            # feature specs and plans
│   ├── architecture/     # this directory — current code structure (for contributors)
│   ├── product/          # current product state (roadmap, changelog) — for maintainers
│   └── guides/           # user-facing docs (Diátaxis: tutorials, how-to, reference, explanation)
├── .claude/
│   ├── skills/           # agent workflows for repeating tasks (each skill owns its templates under `assets/`)
│   ├── agents/           # subagent definitions
│   └── commands/         # custom slash commands
└── .github/              # CI, issue and PR templates
```

## Apps and packages

<!--
Replace this section with a real listing of your apps and packages.
The ideal entry tells an agent: what is this, what does it depend on, and
where do I look first?

- `apps/web/` — the public-facing web app (Next.js). Depends on `packages/api-client`,
  `packages/ui`. Entry point: `app/page.tsx`.
- `packages/api-client/` — typed HTTP client for the API. Generated from
  the OpenAPI spec in `apps/api/openapi.yaml`.
- ...
-->

## Conventions you'll see across packages

<!--
Things that are true of every package in the monorepo. Example:

- Every package has its own `AGENTS.md` describing package-specific rules.
- Every package exports a `package.json` with `main`, `module`, and `types`.
- Every package has a `README.md` aimed at human consumers.

Add yours here.
-->

## Where to start

<!--
A short, opinionated path for someone new to the repo. Example:

1. Read [`docs/CHARTER.md`](../CHARTER.md) — the project's mission and scope.
2. Read this file (architecture overview).
3. Skim [`docs/product/roadmap.md`](../product/roadmap.md) for current direction.
4. Pick a recent feature in `docs/specs/` and read its `spec.md` and `plan.md`
   side by side with the resulting code in `apps/` or `packages/`.
5. Look at the latest 3 ADRs in `docs/adr/` to see the kinds of decisions
   we record.
-->
