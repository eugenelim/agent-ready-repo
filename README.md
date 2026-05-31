# agent-ready-repo

A catalogue of agentbundle primitives — skills, reviewer subagents, hooks, governance scaffolding — installed à la carte into any repo. Each pack lands a coherent slice: a workflow you can run, a reviewer that pulls its weight, or the document shape that makes downstream agents work well. 

Skills follow the [agentskills.io specification](https://agentskills.io/specification) — each one is a self-contained folder (SKILL.md plus optional `scripts/`, `references/`, `assets/`, `evals/`) with the closed top-level frontmatter set and no hidden cross-skill dependencies, so they install, copy, and audit cleanly.

The `core` pack carries what makes this catalogue worth adopting — a plan → execute → verify → review loop that runs lint, typecheck, and tests as hard gates, then dispatches specialist reviewer subagent(s) in a *fresh session* to read the diff adversarially before anything ships. Most agent workflows go *prompt → code → ship*; `core` replaces that with a loop the agent cannot self-certify out of. 

The rest of the packs add governance ceremony, user-docs structure, monorepo scaffolding, contract authoring, file conversion, Atlassian workflows, and Figma file access — the repo-only ones build on `core`, the portable ones stand alone.

See [`docs/CHARTER.md`](docs/CHARTER.md) for the mission, scope, and four principles, and [RFC-0001](docs/rfc/0001-bundle-distribution-by-adapter-spec.md) for the catalogue model.

## Packs

| Pack | Scope | What it ships |
| --- | --- | --- |
| [`core`](packs/core/) | **repo only** | Spec-driven workflow, reviewer subagents, pre-pr + session-start hooks, governance seeds. The foundation the other repo-only packs build on. |
| [`governance-extras`](packs/governance-extras/) | repo only | RFC and ADR ceremony — `new-rfc`, `new-adr`, `update-conventions` skills plus `docs/rfc/` and `docs/adr/` shapes. |
| [`user-guide-diataxis`](packs/user-guide-diataxis/) | repo only | Diátaxis-shaped user-docs skeleton — `docs/guides/{tutorials,how-to,reference,explanation}` plus the `new-guide` skill. |
| [`monorepo-extras`](packs/monorepo-extras/) | repo only | Monorepo scaffolding — `new-package` skill and a `packages/_example/` template. |
| [`contracts`](packs/contracts/) | user (default) or repo | Contract-authoring skills — `api-contract` for OpenAPI 3.1. Portable across projects. |
| [`converters`](packs/converters/) | user (default) or repo | File-format converters — `file-to-markdown` (PDF/DOCX/PPTX/XLSX + images), `markdown-to-html`, `msg-to-markdown`, `mermaid-renderer` (bakes ` ```mermaid ` fences into PNG/SVG via `mmdc`). |
| [`atlassian`](packs/atlassian/) | user (default) or repo | Atlassian primitives — `jira`, `jira-align`, `confluence-crawler`, `confluence-publisher` (all credentialed CLIs) plus the `flow-metrics`, `ai-adoption-report`, and `jira-defect-flow` workflows that compose them. |
| [`figma`](packs/figma/) | user (default) or repo | Figma REST API primitive (credentialed CLI) — reads files / nodes / metadata / versions / comments / variables / dev resources, renders frames to PNG/SVG/JPG/PDF, posts comments, converts FigJam connector graphs to Mermaid. Requires a Personal Access Token. |
| [`architect`](packs/architect/) | user (default) or repo | Solution-architecture skills — `architect-design` (Google-style design docs), `architect-diagram` (Mermaid diagrams routed by intent, cloud- and agentic-platform-aware), `architect-review` (severity-tagged critique with rubric routing). Workspace-agnostic, no required configuration. |

**Scope** is where the pack lands. *Repo-only* packs install into the current repo's `.claude/`, `docs/`, and root files — they ship hooks and seeds that only make sense per-project. *User-scope* packs install into `~/.claude/` and follow you across every repo on the machine; the install routes default to user scope for these but `--scope repo` works too.

Pick `core` plus whichever add-ons fit your repo. The detailed breakdown of `core`'s contents is in [The core pack](#the-core-pack) below.

## Install

The reference CLI `agentbundle` is the catalogue's foundation — install it once, then every pack install is one line at either scope.

**One-time setup** (until [RFC-0003](docs/rfc/0003-spec-and-cli.md) § F-cli-dist ships a release artifact, install from a clone):

```bash
git clone https://github.com/eugenelim/agent-ready-repo
pip install -e agent-ready-repo/packages/agentbundle/
```

**Then one line per pack, either scope:**

```bash
agentbundle install --pack core      git+https://github.com/eugenelim/agent-ready-repo   # repo-scope: into the current repo
agentbundle install --pack architect git+https://github.com/eugenelim/agent-ready-repo   # user-scope: into ~/.claude/
```

`core` lands under the current repo's `.claude/`; `architect` lands under `~/.claude/` so it follows you across every project on the machine. Scope is read from each pack's `default-scope` — swap either pack name for any row in the [Packs](#packs) table.

APM and Claude-plugin routes will land the same markdown content without the `pip install` step, but `adapt-to-project` substitution, credentialed skills (`jira`, `figma`, `confluence-publisher`, ...), and upgrade-time safety (`agentbundle init-state`) all require the `agentbundle` CLI on PATH — so the one-time pip step is effectively part of the setup either way.

### All four install routes

Four routes, depending on the agent harness you use and whether you want the catalogue's CLI on your PATH. They install the same packs.

**Where to run these.** The first three commands run from inside *your own* repo and let the install verb fetch the catalogue itself — you don't `git clone agent-ready-repo` first. For a brand-new project, `mkdir my-project && cd my-project && git init` before installing; for a brownfield repo, just `cd` into its root. The fourth route is the exception: you clone the catalogue, build the CLI inside it, and project outward via `--output`. Either way, repo-only packs land under the target repo; user-scope packs land under `~/.claude/` (the adapter target for each non-Claude harness is in the [`Where primitives land`](#where-primitives-land) table).

**Claude Code** — marketplace + plugins:

```
/plugin marketplace add eugenelim/agent-ready-repo
/plugin install core@agent-ready-repo
```

`/plugin install` lands the markdown and scripts but not the `agentbundle` Python module those scripts import — see [installing `agentbundle` from a clone](docs/guides/how-to/install-agentbundle-from-clone.md) before invoking `jira`, `figma`, or any credentialed skill.

**Any IDE via APM:**

```bash
apm install eugenelim/agent-ready-repo/core
```

`apm install` lands the same pack content but not the `agentbundle` module credentialed skills import — same pip-install step the clone route documents, see [installing `agentbundle` from a clone](docs/guides/how-to/install-agentbundle-from-clone.md).

**Reference CLI** ([RFC-0003](docs/rfc/0003-spec-and-cli.md)) — once you've pip-installed `agentbundle` (see route 4):

```bash
agentbundle install --pack core git+https://github.com/eugenelim/agent-ready-repo
```

Route 3 still requires route 4's pip install today — RFC-0003 § F-cli-dist's release artifact (zipapp / wheel / Homebrew) isn't shipped yet, so "on your PATH" resolves to the editable install from the clone. The route's distinction from route 4 — fetching the catalogue from a remote `git+https://` URL instead of a local clone — still applies once `agentbundle` is importable.

**From a local clone** — clone the catalogue, install the runtime library, and project straight into your target repo:

```bash
git clone https://github.com/eugenelim/agent-ready-repo
cd agent-ready-repo
pip install -e packages/agentbundle/                     # one install, two surfaces (module + CLI on PATH)
agentbundle --version                                              # smoke: CLI on PATH?
agentbundle install --pack core . --output /path/to/your/project
```

**The clone does double duty.** `packs/` is the catalogue the install verb projects into your target repo; `packages/agentbundle/` is the runtime CLI plus the build pipeline. As of 0.2.0 the runtime library no longer exposes a credential-resolution module — credentialed skills (`jira`, `figma`, `confluence-publisher`, and others) import a build-projected `credentials_shim` sibling that the `credential-brokers` pack drops alongside each consumer's `scripts/`. The `pip install -e` step drops the `agentbundle` launcher on PATH; `git pull` against the clone cascades to the catalogue and the CLI. See [installing `agentbundle` from a clone](docs/guides/how-to/install-agentbundle-from-clone.md) for the full mental model, the editable-vs-snapshot choice, and venv guidance.

The catalogue argument is `.` because you're inside the clone; `--output` points at the target repo's root. Use `git checkout <tag>` in the clone first to pin a specific release. If `pip install` is blocked in your environment, see the [zipapp fallback](docs/guides/how-to/install-agentbundle-from-clone.md#fallback-build-the-zipapp).

Swap `core` for any pack from the table above. Most adopters install `core` plus the add-ons that fit their repo, then run the `adapt-to-project` skill (shipped in `core`) to customize the freshly-installed primitives to local conventions.

## Your edits are never silently overwritten

Pack content that collides with files you've edited lands as `*.upstream.<ext>` companions for the `adapt-to-project` skill to merge — not as overwrites. The CLI install route is covered end-to-end; APM and Claude-plugin routes need a one-time `agentbundle init-state` after install to get upgrade-time safety. See [the file-safety contract](docs/guides/explanation/file-safety-contract.md) for the Tier-1/2/3 model, per-route mechanics, and the authoritative RFC reference.

## After install — adapt to your project

**Where seeds land, by route.** The pack's governance seeds (`AGENTS.md`, `docs/CHARTER.md`, `docs/CONVENTIONS.md`, …) travel inside every artifact. The **CLI route** (`agentbundle install`) writes them straight into your repo with the file-safety guarantee below — an edited file at a seed path keeps a `*.upstream.<ext>` companion, never an overwrite. On the **plugin** and **APM** routes the seeds ride along inside the installed artifact (a Claude-managed cache / the APM package); you land them in your working tree with `agentbundle install` or `agentbundle scaffold --pack <name> --output .` — the same `agentbundle` CLI those routes already need on PATH for credentialed skills and upgrade-safety.

Seed content lands generic; the `adapt-to-project` skill (shipped in `core`) tailors it to your repo's name, stack, and existing conventions. In Claude Code or any harness that loads skills:

```
/adapt-to-project
```

The skill walks four classes of change with per-item approval — substitution (project name, build commands, etc.), companion merges (your existing file vs. the pack's seed), discovery + restructuring (folding a stray `DESIGN.md` into `docs/CHARTER.md`), and within-layout consolidation (your `docs/howto/` into the diátaxis pack's `docs/guides/how-to/`). It's safe to re-invoke; it dedupes against prior declines and exits clean when nothing remains.

See [how to adapt a freshly-installed pack](docs/guides/how-to/adapt-to-project.md) for the greenfield vs. brownfield differences, the install-route caveats around companion files, and the LLM-skill / `agentbundle adapt` CLI split.

## Upgrades

Upgrades follow your install route's native verb — `apm update <pack>`, `/plugin update <pack>@agent-ready-repo`, or `agentbundle upgrade --pack <name> --to <version> <catalogue>`. See [how to upgrade an installed pack](docs/guides/how-to/upgrade-packs.md) for the three granularities (whole pack / one primitive / one file), the `*.upstream.<ext>` merge flow, and the v0.1 downgrade workaround.

## Where primitives land

Each install route projects pack sources through a per-IDE adapter into the shape your harness expects. `agentbundle list-targets` reports four shipped adapters (`claude_code`, `codex`, `copilot`, `kiro`); three of them shown below — Copilot omitted for brevity, see [`docs/contracts/`](docs/contracts/) for its mapping.

| Adapter | Repo-scope skills | User-scope skills | Subagents | Hooks | Governance docs |
| --- | --- | --- | --- | --- | --- |
| **Claude Code** | `.claude/skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` | `.claude/agents/<name>.md` | bodies in `tools/hooks/`; wiring merged into `.claude/settings.local.json` | top-level `AGENTS.md`, `docs/CHARTER.md`, `docs/CONVENTIONS.md` |
| **Codex** | `.agents/skills/<name>/SKILL.md` (RFC-0009 direct-directory) | `~/.agents/skills/<name>/SKILL.md` | dropped (Codex has no subagent concept) | bodies in `tools/hooks/`; wiring dropped | top-level as above |
| **Kiro** | `.kiro/skills/<name>/SKILL.md` | `~/.kiro/skills/<name>/SKILL.md` | `.kiro/agents/<name>.md` (frontmatter remapped) | bodies in `tools/hooks/`; wiring degraded to a build-time info log | `.kiro/steering/*.md` (with `inclusion: always`) plus top-level governance |
| **Copilot** | `.github/instructions/<name>.md` (repo scope only — no user-scope analogue) | — | dropped | bodies in `tools/hooks/`; wiring dropped | top-level as above |

Per RFC-0011, a user-scope pack's `pack.toml` lists which of the three user-scope-capable adapters above it travels with (`allowed-adapters`). Per RFC-0012, `--adapter` is admitted at **both scopes** — `agentbundle install --pack <name> --scope repo --adapter kiro .` lands the pack at `<repo>/.kiro/skills/` instead of the legacy dist-tree shape. The dist-tree producer is opt-in via `--emit-install-routes` for catalogue-publishing workflows. See [install a user-scope pack into Kiro](docs/guides/how-to/install-user-scope-pack-into-kiro.md) and [install a user-scope pack into Codex](docs/guides/how-to/install-user-scope-pack-into-codex.md).

The mapping is defined in [`docs/contracts/`](docs/contracts/); the contract is the authoritative source when an adapter and this table disagree.

## The core pack

Core is the load-bearing pack. Everything else extends what it ships, and if you install nothing else, install this. **Core installs into the repo only** — its hooks, governance seeds, and `AGENTS.md` template are per-project by design and the pack refuses a user-scope install.

### Why it earns the load-bearing slot

Two pieces carry the weight: the `work-loop` skill, and the four reviewer subagents the loop dispatches. Together they replace one-shot agent coding with a loop the agent cannot shortcut:

1. **Plan with surfaced assumptions.** Before writing code, the agent writes a short PLAN naming what it's about to build, what it's *not* going to touch, and the assumptions it's making. When an assumption turns out wrong mid-implementation, the loop's prose tells the agent to stop and surface — not guess past it.
2. **Mechanical gates between every "done" claim and the actual finish.** Lint, typecheck, and tests run after the implementation phase. The agent cannot self-certify past a failing gate; there is no path forward in the loop that lets it.
3. **Adversarial review in a fresh session.** Once gates pass, the loop dispatches a specialist reviewer agent in a clean context. That reviewer has no investment in the original design decisions and no sunk cost in the implementation — it reads the diff cold. The loop iterates (fix findings, re-review) until the reviewer reports `Clean — ready to commit.`
4. **Capture-learnings closes the loop on the project, not the agent.** When the run surfaces a convention gap — something undocumented that caused the agent to stumble — a candidate change to `docs/CONVENTIONS.md` lands as a follow-up. The agent's mistakes become the project's documentation rather than the agent's silent retraining data.

The reviewer is not one generic agent — three sharp lenses cover different attack surfaces, and `work-loop` picks which to dispatch based on what the diff actually touches:

- **`adversarial-reviewer`** — spec / plan / implementation drift, scope creep, missing edge cases. The default reviewer; runs on every diff.
- **`security-reviewer`** — OWASP Top 10 (web + LLM Apps 2025) and STRIDE. Dispatched when the diff touches auth, secrets, user input, deserialization, file/network I/O, dependencies, or LLM/agent code. Complements SAST/SCA scanners; doesn't replace them.
- **`quality-engineer`** — testability, observability, reliability, maintainability. The "cost to live with this code" pass.

The fourth subagent, `implementer`, is the loop's own executor in supervisor mode — used when a plan has independent tasks that can run in parallel.

### Why the bundler matters here

The `work-loop` skill is a Markdown file. Each reviewer is a Markdown file. The bundler installs both into your repo as plain-text primitives — no SDK, no runtime, no service to host, no proprietary harness. Any agent that can read a skill (Claude Code, Codex, Cursor, Copilot, Kiro) inherits the same loop. The mechanics are inspectable, modifiable, and `git diff`-able; when you outgrow a default, you edit the prose.

### What's in core

- **Skills**
  - `work-loop` — the plan → execute → gates → review loop described above.
  - `new-spec` — opens a feature directory with paired spec and plan; assumptions surface up front.
  - `bug-fix` — reproduce, root-cause, write a failing test, ship the minimum diff.
  - `adapt-to-project` — walks the adopter through customizing freshly-installed primitives to local conventions.
- **Subagents** — the four reviewer / executor lenses described above.
- **Hooks**
  - `session-start` — runs at session start; surfaces context the agent needs before its first action.
  - `pre-pr` — runs before a PR is opened; the last gate before review.
- **Command**
  - `conventions-check` — runs the agent-artifact and conventions linters in one shot.
- **Governance seeds** — `AGENTS.md` (canonical agent context, symlinked from `CLAUDE.md`), `CHARTER`, `CONVENTIONS`, and the `docs/specs/` + `docs/architecture/` shapes with README seeds.

For the longer-form walkthrough of how these parts compose into one loop — plus how the result compares to vibe-coding, GitHub's Spec Kit, and Kiro IDE's spec-driven mode — see [The core pack as a system](docs/guides/explanation/core-pack.md).

## Contributing

Adding a pack, a skill, or a subagent? See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the three contribution lanes, the pack source-of-truth split, and the build/lint gates your PR has to pass.

## License

Licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
- MIT License ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option. Contributions are dual-licensed under the same terms unless you state otherwise.
