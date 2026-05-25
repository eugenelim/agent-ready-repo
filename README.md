# agent-ready-repo

A catalogue of agentbundle primitives — skills, reviewer subagents, hooks, governance scaffolding — installed à la carte into any repo. Each pack lands a coherent slice: a workflow you can run, a reviewer that pulls its weight, or the document shape that makes downstream agents work well. 

Skills follow the [agentskills.io specification](https://agentskills.io/specification) — each one is a self-contained folder (SKILL.md plus optional `scripts/`, `references/`, `assets/`, `evals/`) with the closed top-level frontmatter set and no hidden cross-skill dependencies, so they install, copy, and audit cleanly.

The `core` pack carries what makes this catalogue worth adopting — a plan → execute → verify → review loop that runs lint, typecheck, and tests as hard gates, then dispatches specialist reviewer subagent(s) in a *fresh session* to read the diff adversarially before anything ships. Most agent workflows go *prompt → code → ship*; `core` replaces that with a loop the agent cannot self-certify out of. 

The rest of the packs add governance ceremony, user-docs structure, monorepo scaffolding, contract authoring, file conversion, and Atlassian workflows — but they all assume `core`.

See [`docs/CHARTER.md`](docs/CHARTER.md) for the mission, scope, and four principles, and [RFC-0001](docs/rfc/0001-bundle-distribution-by-adapter-spec.md) for the catalogue model.

## Packs

| Pack | Scope | What it ships |
| --- | --- | --- |
| [`core`](packs/core/) | **repo only** | Spec-driven workflow, reviewer subagents, pre-pr + session-start hooks, governance seeds. The foundation; everything else assumes it. |
| [`governance-extras`](packs/governance-extras/) | repo only | RFC and ADR ceremony — `new-rfc`, `new-adr`, `update-conventions` skills plus `docs/rfc/` and `docs/adr/` shapes. |
| [`user-guide-diataxis`](packs/user-guide-diataxis/) | repo only | Diátaxis-shaped user-docs skeleton — `docs/guides/{tutorials,how-to,reference,explanation}` plus the `new-guide` skill. |
| [`monorepo-extras`](packs/monorepo-extras/) | repo only | Monorepo scaffolding — `new-package` skill and a `packages/_example/` template. |
| [`contracts`](packs/contracts/) | user (default) or repo | Contract-authoring skills — `api-contract` for OpenAPI 3.1. Portable across projects. |
| [`converters`](packs/converters/) | user (default) or repo | File-format converters — `file-to-markdown` (PDF/DOCX/PPTX/XLSX + images), `markdown-to-html`, `msg-to-markdown`. |
| [`atlassian`](packs/atlassian/) | user (default) or repo | Atlassian primitives — `jira`, `jira-align`, `confluence-crawler` (credentialed CLI) plus the `flow-metrics`, `ai-adoption-report`, and `jira-defect-flow` workflows that compose them. |

**Scope** is where the pack lands. *Repo-only* packs install into the current repo's `.claude/`, `docs/`, and root files — they ship hooks and seeds that only make sense per-project. *User-scope* packs install into `~/.claude/` and follow you across every repo on the machine; the install routes default to user scope for these but `--scope repo` works too.

Pick `core` plus whichever add-ons fit your repo. The detailed breakdown of `core`'s contents is in [The core pack](#the-core-pack) below.

## Install

Four routes, depending on the agent harness you use and whether you want the catalogue's CLI on your PATH. They install the same packs.

**Where to run these.** The first three commands run from inside *your own* repo and let the install verb fetch the catalogue itself — you don't `git clone agent-ready-repo` first. For a brand-new project, `mkdir my-project && cd my-project && git init` before installing; for a brownfield repo, just `cd` into its root. The fourth route is the exception: you clone the catalogue, build the CLI inside it, and project outward via `--output`. Either way, repo-only packs land under the target repo; user-scope packs land under `~/.claude/` (the adapter target for each non-Claude harness is in the [`Where primitives land`](#where-primitives-land) table).

**Claude Code** — marketplace + plugins:

```
/plugin marketplace add eugenelim/agent-ready-repo
/plugin install core@agent-ready-repo
```

**Any IDE via APM:**

```bash
apm install eugenelim/agent-ready-repo/core
```

**Reference CLI** ([RFC-0003](docs/rfc/0003-spec-and-cli.md)) — once `agentbundle` is on your PATH:

```bash
agentbundle install --pack core git+https://github.com/eugenelim/agent-ready-repo
```

**From a local clone, no global install** — clone the catalogue, build the bundled CLI as a self-contained zipapp, and project straight into your target repo:

```bash
git clone https://github.com/eugenelim/agent-ready-repo
cd agent-ready-repo
make zipapp                                              # builds dist/agentbundle.pyz
./dist/agentbundle.pyz install --pack core . --output /path/to/your/project
```

The catalogue argument is `.` because you're inside the clone; `--output` points at the target repo's root. Use `git checkout <tag>` in the clone first to pin a specific release.

Swap `core` for any pack from the table above. Most adopters install `core` plus the add-ons that fit their repo, then run the `adapt-to-project` skill (shipped in `core`) to customize the freshly-installed primitives to local conventions.

## Your edits are never silently overwritten

Pack content that collides with files you've edited lands as `*.upstream.<ext>` companions for the `adapt-to-project` skill to merge — not as overwrites. The CLI install route is covered end-to-end; APM and Claude-plugin routes need a one-time `agentbundle init-state` after install to get upgrade-time safety. See [the file-safety contract](docs/guides/explanation/file-safety-contract.md) for the Tier-1/2/3 model, per-route mechanics, and the authoritative RFC reference.

## After install — adapt to your project

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

| Adapter | Skills | Subagents | Hooks | Governance docs |
| --- | --- | --- | --- | --- |
| **Claude Code** | `.claude/skills/<name>/SKILL.md` | `.claude/agents/<name>.md` | bodies in `tools/hooks/`; wiring merged into `.claude/settings.local.json` | top-level `AGENTS.md`, `docs/CHARTER.md`, `docs/CONVENTIONS.md` |
| **Codex** | inline managed block in root `AGENTS.md` (`<!-- agent-skills:start -->` … `<!-- agent-skills:end -->`); full bodies stay in `.apm/skills/` | dropped (Codex has no subagent concept) | bodies in `tools/hooks/`; wiring dropped | top-level as above |
| **Kiro** | `.kiro/skills/<name>/SKILL.md` | `.kiro/agents/<name>.md` (frontmatter remapped) | bodies in `tools/hooks/`; wiring degraded to a build-time info log | `.kiro/steering/*.md` (with `inclusion: always`) plus top-level governance |

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
  - `add-credentialed-skill` — scaffolds a new skill that calls an authenticated external API on the user's behalf.
- **Subagents** — the four reviewer / executor lenses described above.
- **Hooks**
  - `session-start` — runs at session start; surfaces context the agent needs before its first action.
  - `pre-pr` — runs before a PR is opened; the last gate before review.
- **Command**
  - `conventions-check` — runs the agent-artifact and conventions linters in one shot.
- **Governance seeds** — `AGENTS.md` (canonical agent context, symlinked from `CLAUDE.md`), `CHARTER`, `CONVENTIONS`, and the `docs/specs/` + `docs/architecture/` shapes with README seeds.

## Contributing

Adding a pack, a skill, or a subagent? See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the three contribution lanes, the pack source-of-truth split, and the build/lint gates your PR has to pass.

## License

Licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
- MIT License ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option. Contributions are dual-licensed under the same terms unless you state otherwise.
