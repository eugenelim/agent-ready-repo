# Architecture Overview

> The map of this monorepo. Read this first when exploring. Updated whenever
> the directory layout or major dependencies change.

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

## The catalogue

`packs/` is the source catalogue. Each pack owns its manifest, portable
primitives, tests, seeds, README, and journey; `profiles/` composes those packs
without introducing new primitives. The complete current inventory belongs to
the [generated catalogue](https://eugenelim.github.io/agent-ready-repo/catalogue/)
and [technical pack reference](https://eugenelim.github.io/agent-ready-repo/docs/packs/),
not to a hand-maintained architecture table.

[`core`](../../guides/core/explanation/core-pack.md) is the flagship build
system. Other packs may depend on it, integrate with it, or remain independently
useful; composition is declared in `pack.toml`, not inferred from directory
adjacency. Each pack's full metadata lives in that manifest and is projected
into catalogue listings — see [`pack-manifest.md`](pack-manifest.md).

What it means for `core` to be load-bearing: its
`session-start.py` is the single read-side of the install→adapt chain —
every install route (CLI, APM, Claude plugins) drops the same
`.adapt-install-marker.toml`, and `core`'s hook is what surfaces it to the
agent on next session. Pull `core` out and the chain doesn't close.

## Subsystems

One file per non-trivial subsystem:

- [`workspace-mcp/design.md`](workspace-mcp/design.md) — the per-session MCP
  server shipped with `core`: spawn forms (trusted / CI), session modes, ACP
  adapter classes, notification contract, FSM observability, and security
  constraints. Harness operators should read this alongside the operator
  how-to guide at
  [`guides/core/how-to/run-headless-session.md`](../../guides/core/how-to/run-headless-session.md).
- [`pack-layout.md`](pack-layout.md) — the canonical shape of a single
  pack: `pack.toml`, `.claude-plugin/`, `.apm/<primitive>/`, `seeds/`,
  and how the bundler reads them.
- [`agentbundle.md`](agentbundle.md) — the Python package: CLI verbs,
  build pipeline (recipes → adapters → projections), the adapter contract
  at v0.18 (Claude-plugin hook parity adds route-scoped hook-body and
  hook-wiring fields; RFC-0052 added the shared-prefix registry and routed the
  cursor/gemini/copilot skill cohort to the shared `.agents/skills/` home;
  RFC-0031 carries the enriched-manifest projection at v0.14; RFC-0011
  added `[adapter.codex.scope]` and the user-scope adapter resolver),
  self-host overlay.
- [`credentials.md`](credentials.md) — the credentialed-resolver model
  (the `credbroker` library since RFC-0023, formerly the build-projected
  `credentials_shim`, RFC-0013), three-tier storage
  (env / OS keyring / `~/.agentbundle/credentials.env`), the four
  brokers (`creds` / `env` / `cli` / `sso-cookie`), the
  credentialed-primitive contract, and the substring trap.
- [`knowledge-capture.md`](knowledge-capture.md) — the `core` pack's current
  capture and read boundaries plus the target lifecycle: free-form scratch,
  semantic-gate triage, typed observation journals, progressive capture,
  topic distillation, file-based storage, explicit enquiry, and intentional
  retirement.
- [`work-intake-and-artifact-routing.md`](work-intake-and-artifact-routing.md)
  — the implemented architecture for separating source intake, canonical
  intents/briefs/specs/defects, lifecycle membership in `workspace.toml`, and
  processor dispatch. Jira, Jira Align, Linear, and GitHub adapters now converge
  on its `normalized-intake.v1` boundary: acquisition and versioned profile
  hints stay tracker-specific, while content classification and every repository
  write stay in `work-intake`. Tracker intake is read-only; refresh conflicts,
  execution locks, and tracker write-back remain later integrations.

## Packages

- [`packages/agentbundle/`](../../packages/agentbundle/) — the reference
  CLI and build pipeline. Stdlib-only, distributed as a zipapp and as
  an editable pip install. As of 0.2.0 it no longer ships a credential-
  resolution module; credentialed primitives in the `atlassian` and
  `figma` packs resolve credentials through the pip-installable
  `credbroker` library (RFC-0023), not the agentbundle wheel. See
  [`agentbundle.md`](agentbundle.md) and [`credentials.md`](credentials.md).
- [`packages/_example/`](../../packages/_example/) — a minimal package
  template the `new-package` skill (in `monorepo-extras`) copies when an
  adopter scaffolds a new package.

## Where to start

1. Read [`docs/CHARTER.md`](../CHARTER.md) — mission, scope, four principles.
2. Read this file.
3. Pick a recent spec under [`docs/specs/`](../specs/) and read its
   `spec.md` + `plan.md` next to the resulting code under
   `packages/agentbundle/` or `packs/`. The
   [`agent-spec-cli`](../specs/agent-spec-cli/spec.md),
   [`distribution-adapters`](../specs/distribution-adapters/spec.md),
   and [`skill-secrets`](../specs/skill-secrets/spec.md) specs are the
   three load-bearing ones.
4. Skim the two ADRs —
   [ADR-0001](../adr/0001-adopt-agents-md-and-doc-hierarchy.md)
   (AGENTS.md + the doc hierarchy this repo runs on) and
   [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md)
   (the per-pack default-plus-allowance install-scope model) — plus the
   most recent accepted RFCs ([0008](../rfc/0008-claude-plugins-install-route-parity.md),
   [0010](../rfc/0010-apm-install-route-parity.md)) for current direction.
5. Run `make build-check` once — it's the self-host drift gate, and
   tripping it explains the seed/projection split better than prose can.
