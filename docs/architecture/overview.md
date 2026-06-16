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
│   └── _example/         # template package consumed by the new-package skill
├── packs/                # the catalogue — one directory per shippable pack
│   ├── core/             # the load-bearing pack; every other pack composes against it
│   ├── governance-extras/
│   ├── user-guide-diataxis/
│   ├── monorepo-extras/
│   ├── contracts/
│   ├── converters/
│   ├── atlassian/
│   └── figma/
├── docs/
│   ├── CHARTER.md        # mission, scope, principles
│   ├── CONVENTIONS.md    # how we work
│   ├── backlog.md        # open spec items, top-level index
│   ├── rfc/              # proposals (governance)
│   ├── adr/              # architecture decisions (frozen history)
│   ├── specs/            # feature specs and plans
│   ├── architecture/     # this directory — internals for contributors
│   ├── contracts/        # adapter.toml, JSON schemas — the publishable spec
│   ├── product/          # roadmap + changelog
│   └── guides/           # Diátaxis: tutorials, how-to, reference, explanation
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

`packs/` is a catalogue of reference packs. The relationship is
"compose around `core`", not "subclass": every other pack assumes `core`'s
seeds and reviewer-agents are available, but they don't import code from
each other. Each pack's full metadata (license, maintainers, links,
categories, keywords) lives in its `pack.toml` and is projected into the
catalogue listing — see [`pack-manifest.md`](pack-manifest.md).

| Pack | Scope | Carries |
| --- | --- | --- |
| `core` | repo only | `work-loop`, `new-spec`, `bug-fix`, `adapt-to-project`, the four reviewer agents (`adversarial-reviewer`, `security-reviewer`, `quality-engineer`, `implementer`), `session-start.py` + `pre-pr.py` hooks, `conventions-check`, layer-0 seeds (`AGENTS.md`, `docs/CHARTER.md`, `docs/CONVENTIONS.md`). |
| `governance-extras` | repo only | `new-rfc`, `new-adr`, `update-conventions` skills + `docs/rfc/` and `docs/adr/` shapes. Requires `core`. |
| `user-guide-diataxis` | repo only | Diátaxis user-docs scaffolding + the `new-guide` skill. Requires `core`. |
| `monorepo-extras` | repo only | `new-package` skill + `packages/_example/` template. Requires `core`. |
| `contracts` | user (default) or repo | `api-contract` (OpenAPI 3.1) and `event-contract` (AsyncAPI). |
| `converters` | user (default) or repo | Document/image → Markdown, Markdown → styled HTML, Outlook `.msg` → Markdown. |
| `atlassian` | user (default) or repo | `jira`, `jira-align`, `confluence-crawler` (credentialed CLIs) + the `flow-metrics`, `ai-adoption-report`, `jira-defect-flow`, `jira-brief-intake` workflows that compose them. |
| `figma` | user (default) or repo | `figma` credentialed CLI (REST API reads, frame renders, FigJam → Mermaid). |
| `research` | user (default) or repo | Seven research skills (scoping → synthesis → decision support) + two read-only retrieval subagents. |
| `architect` | user (default) or repo | `architect-design`, `architect-diagram`, `architect-review` (Mermaid + Google-style design docs). |
| `credential-brokers` | user (default) or repo | `credentials_shim`, the `sso-broker` subprocess, and the `credential-setup` skill — user-scope credential brokering for credentialed packs. |
| `product-engineering` | user (default) or repo | `frame-intent`, `de-risk-intent`, `decompose-intent` — shaping product intent into shippable specs. |

What it means for `core` to be load-bearing: its
`session-start.py` is the single read-side of the install→adapt chain —
every install route (CLI, APM, Claude plugins) drops the same
`.adapt-install-marker.toml`, and `core`'s hook is what surfaces it to the
agent on next session. Pull `core` out and the chain doesn't close.

## Subsystems

One file per non-trivial subsystem:

- [`pack-layout.md`](pack-layout.md) — the canonical shape of a single
  pack: `pack.toml`, `.claude-plugin/`, `.apm/<primitive>/`, `seeds/`,
  and how the bundler reads them.
- [`agentbundle.md`](agentbundle.md) — the Python package: CLI verbs,
  build pipeline (recipes → adapters → projections), the adapter contract
  at v0.14 (RFC-0011 added `[adapter.codex.scope]` and the user-scope
  adapter resolver; RFC-0031 carries the enriched-manifest projection),
  self-host overlay.
- [`credentials.md`](credentials.md) — the credentialed-resolver model
  (the `credbroker` library since RFC-0023, formerly the build-projected
  `credentials_shim`, RFC-0013), three-tier storage
  (env / OS keyring / `~/.agentbundle/credentials.env`), the four
  brokers (`creds` / `env` / `cli` / `sso-cookie`), the
  credentialed-primitive contract, and the substring trap.

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
