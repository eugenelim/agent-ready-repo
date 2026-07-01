# agent-ready-repo

**The complete AI operating model for software teams — from first idea to production.**

Three supervised loops covering the full software lifecycle. Fourteen curated packs for every job role. One installer. Any agent, any stack.

[![PyPI](https://img.shields.io/pypi/v/agentbundle)](https://pypi.org/project/agentbundle/) [![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue)](#license)

[Quick Start](#quick-start) · [The Three Loops](#the-three-loops) · [The Catalogue](#the-catalogue) · [Build a Pack](#how-a-pack-is-laid-out) · [Docs](docs/guides/) · [Contributing](CONTRIBUTING.md)

> "You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents." — [Peter Steinberger](https://x.com/steipete/status/2063697162748260627)

The leverage in agent coding moved from the prompt to the **loop** — it plans, executes, verifies, and decides what comes next, so you stop babysitting every turn. But a loop running unattended is also a loop making mistakes unattended, so it has to check its own work harder than you would.

Software delivery needs more than one loop. Product managers shape ideas into build-ready briefs; engineers build and gate their changes; SRE teams validate what reaches production. This repository makes all three concrete: a **discovery loop** that takes a raw idea through multi-lens convergence to a ratified brief, a **build loop** that gates every change with hard mechanical checks and cold-eyed review, and a **release loop** that validates the deployed whole end-to-end before any human touches a prod switch. Three peer supervisors. One handoff chain. Human gates only where the decision is irreversible.

`core` is the flagship pack: the build discipline made concrete — planning, hard gates, cold-eyed review, working as one loop the agent can't self-certify its way out of.

```bash
pip install agentbundle
agentbundle install --pack core
```

One line lands the loop in your repo — no catalogue argument needed; it defaults to this catalogue. Any agent that reads a skill file inherits it: Claude Code, Codex, Cursor, Copilot, Gemini, Kiro.

Behind `core` is a **catalogue of curated kits** — each pack distilled from the best practices of its discipline through research, RFCs, and architecture decisions. Research, architecture, product discovery, experience design, integration contracts, and more — each is a cohesive set of skills, subagents, and hooks that delivers one whole job, installed in one line. [See the catalogue.](#the-catalogue)

## Quick start

```bash
# Install the CLI (one-time)
pip install agentbundle

# See the catalogue (bare uses the default; or name one explicitly)
agentbundle list-packs

# See what YOU have installed — version + whether an upgrade is available
agentbundle list-installed

# Install the flagship loop into this repo
agentbundle install --pack core

# Install a pack at user scope — follows you across every project
agentbundle install --pack research --scope user

# Install a whole curated profile in one command
agentbundle install --profile solution-architect

# Upgrade a pack to the catalogue's version (asks before writing; --yes for CI)
agentbundle upgrade --pack core

# Preview any install without writing a file
agentbundle install --pack core --dry-run
```

`--dry-run` previews every file before anything is written — one line per file (skills, the four reviewer/executor subagents, the hooks), then a `create`/`overwrite` summary count — so you see exactly what would land in your repo.

Every source verb — `install`, `upgrade`, `list-packs`, `list-profiles` — defaults to this catalogue when you don't name one; pass an explicit catalogue (a git URL or local path) as a trailing argument to use a different one, or `agentbundle config set source <catalogue>` to change the default (an editable `pip install -e` clone defaults to itself). Installs auto-detect your agent — [target another, or change the default](#adapters). Repo scope writes into the current repo; user scope (`--scope user`) installs once into your home so the pack is available everywhere.

## Adapters

Out of the box, installs auto-detect the agent you're working in and fall back to **Claude Code** when there's nothing to detect. If you work across several IDEs — or just want a different default — point agentbundle at the one you want:

```bash
# Pin a default once — every later install targets it
agentbundle config set adapter cursor

# Or override for a single install, leaving the default untouched
agentbundle install --pack core --adapter codex                  # repo scope
agentbundle install --pack research --scope user --adapter codex  # user scope
```

The default is user-global: set it once and it applies whether you install into a repo or at user scope. The supported agents are `claude-code`, `cursor`, `codex`, `copilot`, `gemini`, `kiro-ide`, and `kiro-cli`.

When more than one is in play, the most specific wins: a per-install `--adapter` beats the pinned default, which beats auto-detect — and re-running an install keeps whatever adapter that install already uses.

## The three loops

Three packs form the **company operating model** — peer supervisors spanning the full software lifecycle:

```
product-engineering              core                    release-engineering
───────────────────              ────                    ───────────────────
discovery-lead                   work-loop supervisor    release-lead
Raw idea → Decision brief  ─G3─▶ Spec → Shipped code ─G4─▶ Built → Production
```

Each loop is autonomous where the work is reversible and surfaces to a human where it isn't. No loop is a mode of another — each is a **peer supervisor** with its own agent, its own skill doctrine, and its own consent gates.

→ [The three loops as a system](docs/guides/_shared/explanation/the-three-loops.md)

### The discovery loop — `product-engineering`

`discovery-lead` takes a raw product idea and walks it through a structured diverge/converge cycle: five candidate shapes explored in parallel, then collapsed through product, UX, architecture, and safety lenses simultaneously — results written to a shared blackboard, no chat relay. A ratified **decision brief** exits at G2; a decomposed feature-level plan exits at G3 into `work-loop`.

The result isn't a validated solution — it's a **connected hypothesis with validation hooks**: the riskiest bets named explicitly, the MVP boundary set by a human, the decision log append-only and hash-chained. Recursion is data: sub-problems are nodes in a tree, not separate projects.

Three human consent gates: **G0** (ratify the value seed), **G1.5** (ratify the MVP boundary), **G2** (ratify the decision). The loop never auto-advances past an irreversible gate.

→ [Discovery loop guide](docs/guides/product-engineering/) · [Walk a discovery end-to-end](docs/guides/product-engineering/tutorials/walk-a-discovery-end-to-end.md)

### The build loop — `core`

Every change goes through: plan (name the assumptions and what won't be touched), hard gates (lint, typecheck, tests — no path through the loop passes on red), adversarial review in a fresh session (specialist reviewers with no sunk cost in the design), and capture what was learned (gaps land as proposed `CONVENTIONS.md` edits, not as evaporated knowledge).

The loop scales by risk: **light mode** for low-risk work (lean inline spec, single adversarial pass); **full mode** when any risk trigger fires — unfamiliar territory, new dependency, compliance surface, multi-person work, destructive operation. The mode is chosen by the work's risk profile, not by file count.

Three specialist reviewers each read every diff cold:

| Reviewer | Lens | When it runs |
| --- | --- | --- |
| `adversarial-reviewer` | spec/plan/impl drift, scope creep, missing edge cases | every diff |
| `security-reviewer` | OWASP 2025 + ASVS, STRIDE + LINDDUN — depth pulled per boundary | security-boundary work, at spec stage *and* on the diff |
| `quality-engineer` | testability, observability, reliability — the "cost to live with this code" | logic and interfaces worth maintaining |

The security lens **shifts left**: on security-boundary work it also runs at spec stage, catching a missing control as a one-sentence acceptance criterion instead of a post-implementation round-trip, and pulls its depth from a progressive-disclosure checklist library scoped to the boundaries a change crosses — current without bloating the prompt. The quality lens holds every diff to a raised maintainability floor by doctrine, whether or not a strict static-analysis gate is wired in. A fourth subagent, `implementer`, is the loop's own executor: it runs independent tasks in parallel.

→ [The `core` pack as a system](docs/guides/core/explanation/core-pack.md) walks through how the parts compose, and how it compares to vibe-coding, GitHub's Spec Kit, and Kiro's spec mode.

### The release loop — `release-engineering`

`release-lead` takes the locally built, deploy-ready artifact and validates it deployed: deploy to an **ephemeral environment** (no real data, isolated from prod, teardownable), run e2e against the real artifact, observe telemetry, feed deployed findings back to `work-loop` as build tasks (no human relay), redeploy, and iterate until the deployed whole converges by policy. Then surface a **release-readiness record** for the prod-ship consent gate.

Autonomy is carved by **minimum-regret**: reversible operations (deploy to ephemeral, e2e, observe, iterate, teardown) run unattended. Irreversible operations (first real users, data migrations, spend over threshold, the **prod ship**) always surface to a human. The G5 prod-ship gate is never autonomous.

The outer loop hard-depends on `core` and reuses its `quality-engineer` (in operational mode), `security-reviewer`, and `operational-safety` modules — no new reviewer agents needed. Deploy credentials are broker-mediated and scoped to the ephemeral tier only; no credential can reach prod.

→ [Release loop guide](docs/guides/release-engineering/) · [The release loop explained](docs/guides/release-engineering/explanation/the-release-loop.md)

## The catalogue

The three loop packs anchor the operating model. The remaining packs are **curated kits** — each distilled from the best practices of its discipline, shaped through practitioner research and governed through the RFC and architecture-decision process. Install only the kits your team and repo need.

| Pack | Scope | Agentic use case |
| --- | --- | --- |
| [`core`](docs/guides/core/) | **repo** | **The build loop, on every change.** `work-loop`, `new-spec`, `bug-fix`, `adapt-to-project`, the four reviewer/executor subagents, `pre-pr` + `session-start` hooks, governance seeds. **Install this even if you install nothing else.** |
| [`product-engineering`](docs/guides/product-engineering/) | user | **The discovery loop — raw idea to build-ready brief.** `discovery-loop`, `frame-intent`, `de-risk-intent`, `decompose-intent`; `voice-and-microcopy` for UI copy; `align-value-stream` for multi-repo capability coordination. |
| [`release-engineering`](docs/guides/release-engineering/) | **repo** | **The release loop — build to production.** `release-loop`, `release-lead`; autonomous e2e convergence on ephemeral environments; inner↔outer feedback seam; release-readiness record at the G5 prod-ship gate. Hard-depends on `core`. |
| [`governance-extras`](docs/guides/governance-extras/) | repo | **Keep a written trail of decisions.** RFC/ADR ceremony for teams and long-lived repos — `new-rfc`, `new-adr`, `update-conventions`, plus the `docs/rfc/` and `docs/adr/` shapes. |
| [`user-guide-diataxis`](docs/guides/user-guide-diataxis/) | repo | **Stand up a docs site.** Diátaxis skeleton — `docs/guides/{tutorials,how-to,reference,explanation}` plus `new-guide`. |
| [`monorepo-extras`](docs/guides/monorepo-extras/) | repo | **Scaffold packages in a monorepo.** `new-package` and a `packages/_example/` template. |
| [`research`](docs/guides/research/) | user / repo | **Go from a question to an evidence-grounded answer.** `research`, `source-map`, `compare-hypotheses`, `devils-advocate`, and more, plus two retrieval subagents. |
| [`contracts`](docs/guides/contracts/) | user / repo | **Author an API contract.** `api-contract` for OpenAPI 3.1. |
| [`converters`](docs/guides/converters/) | user / repo | **Move documents in and out of Markdown.** `file-to-markdown` (PDF/DOCX/PPTX/XLSX + images), `markdown-to-html`, `markdown-to-docx`/`-pptx`/`-xlsx` (branded Word/PowerPoint/Excel by template-fill), `msg-to-markdown`, `mermaid-renderer`. |
| [`atlassian`](docs/guides/atlassian/) | user / repo | **Work Jira and Confluence from the agent.** `jira`, `jira-align`, `confluence-crawler`, `confluence-publisher` (credentialed), plus `flow-metrics`, `ai-adoption-report`, `jira-defect-flow`. |
| [`figma`](docs/guides/figma/) | user / repo | **Read and render Figma designs.** Figma REST primitive (credentialed) — files/nodes/comments/variables, frame renders, FigJam → Mermaid. |
| [`architect`](docs/guides/architect/) | user / repo | **Design a system and pressure-test it.** `architect-design`, `architect-diagram`, `architect-review`, plus a read-only, forked-context `design-reviewer` subagent. |
| [`experience`](docs/guides/experience/) | user / repo | **Carry the whole design thread — journey to realization.** `map-customer-journey`, `map-screen-flow`, `blueprint-service`, `map-internal-process`, `aesthetic-direction`, `design-system-foundations`, `layout-and-information-architecture`, `interaction-design`, `design-critique`, a shared `quality-floor` checklist, and a forked-context `experience-reviewer` agent. Points to WCAG / W3C Design Tokens / Apple HIG / Material 3 / APQC / BPMN, never a stack. |

Swap `core` for any pack name in the install command above. Repo-scope packs build on `core`; user-scope packs follow you across every project.

**Or stack several kits in one command.** A profile is a blessed combination of packs: `full-ceremony` adds the repo governance packs to `core`; `solution-architect` lands the `architect` + `research` + `contracts` toolkit; `inception` lands `research` + `product-engineering` + `architect` for taking an idea from zero to a buildable repo. `agentbundle list-profiles <catalogue>` shows them all — see the [install-a-profile how-to](docs/guides/_shared/how-to/install-a-profile.md).

## Ecosystem building blocks

Nothing here is a black box. Your skills, subagents, and hooks are files you own — no SDK, runtime, or service to run, nothing proprietary to lock into. Version and compose them like any other code.

- **Harness-agnostic.** One adapter pipeline projects the same primitives into Claude Code, Codex, Copilot, Cursor, Gemini, and Kiro layouts.
- **Inspectable and forkable.** The mechanics are prose you can read and `git diff`. Outgrow a default? Edit the file instead of filing a feature request.
- **Composable.** Packs layer cleanly, and your edits are never silently overwritten — colliding files land as `*.upstream` companions to merge, not clobber.
- **Curated by discipline.** Every pack is shaped through practitioner research and an RFC-and-ADR governance process — not random defaults, but the best available practices for each job role encoded as runnable skills.

The two packages underneath are standalone, pip-installable, and useful well beyond this repo:

- **[`agentbundle`](https://pypi.org/project/agentbundle/)** — the bundler. Installs and upgrades packs, projects each primitive into the layout every agent expects, and builds catalogues of your own.
- **[`credbroker`](https://pypi.org/project/credbroker/)** — the credential resolver behind credentialed skills. Resolves secrets in-process through environment variable → OS keyring → dotfile, and never lets cleartext reach the model. See [credential handling](docs/architecture/credentials.md).

Loop engineering relocates judgment, it doesn't remove it — keeping every piece inspectable keeps that judgment where you can exercise it. You stay the engineer, not just the person who presses go.

## A foundation to build on

Adopt the catalogue as-is, or fork it as your own. The same bundler that installs these packs can publish yours: write your house conventions and review standards into `core`, add skills for your stack, and ship one catalogue every engineer installs in a single line — the loop, the reviewers, and the standards come out identical on every machine and in every agent. That makes this a foundation for an organization's AI dev kit, not just a set of defaults to consume. [What a catalogue is, and how to stand up your own →](docs/architecture/catalogue.md)

## How a pack is laid out

Every pack is a directory under `packs/<name>/` — a manifest plus two source trees:

- `pack.toml` — the manifest: name, version, install scope.
- `.apm/` — upstream for projected primitives: `skills/`, `agents/`, `hooks/`, `commands/`.
- `seeds/` — upstream for seed files: README, governance docs.

A skill is a self-contained folder — `.apm/skills/<name>/SKILL.md` plus optional `scripts/`, `references/`, `assets/`, `evals/` ([agentskills.io](https://agentskills.io/specification)). No skill imports from another's folder.

One rule governs every change: **edit the upstream, never the projection.** Change `packs/<pack>/.apm/skills/<name>/SKILL.md`, run `make build-self`, and commit the source and the regenerated `.claude/…` together — `make build-check` bounces any projected path edited without its source moving.

- **Add a skill to a pack** → drop a folder under `packs/<pack>/.apm/skills/`, build, commit.
- **Add a new pack** → an RFC, then a `packs/<name>/` with `pack.toml` + `.apm/` + `seeds/`, then a row in the catalogue table above.

[`CONTRIBUTING.md`](CONTRIBUTING.md) has the full steps for all three lanes — pack, skill, subagent — with the frontmatter contracts and the gates your PR must pass.

## Going deeper

Full documentation lives in **[`docs/guides/`](docs/guides/)**, organized by goal and role with tutorials, how-tos, reference, and explanation. The table below jumps straight to the cross-cutting topics.

| Topic | Link |
| --- | --- |
| The three loops as a system — company OS, the inner/outer split, peer supervisors | [the three loops](docs/guides/_shared/explanation/the-three-loops.md) |
| All four install routes (CLI, APM, Claude plugins, local clone) | [install routes](docs/guides/_shared/how-to/install-agentbundle-from-clone.md) |
| What each agent tool supports — skill / subagent / command / hook — and where it degrades | [adapter support matrix](docs/guides/_shared/reference/adapter-support.md) |
| Your edits are never silently overwritten — the file-safety contract | [file-safety contract](docs/guides/_shared/explanation/file-safety-contract.md) |
| Tailor freshly-installed primitives to your repo | [`adapt-to-project`](docs/guides/core/how-to/adapt-to-project.md) |
| Upgrading an installed pack | [upgrade packs](docs/guides/_shared/how-to/upgrade-packs.md) |
| Updating the agentbundle CLI itself — `pip install --upgrade agentbundle` | [PyPI](https://pypi.org/project/agentbundle/) |
| Mission, scope, and the four principles | [`docs/CHARTER.md`](docs/CHARTER.md) |
| What a catalogue is, and how to stand up your own | [the catalogue](docs/architecture/catalogue.md) |
| The skill & pack format, layer by layer | [skill & pack format](docs/architecture/skill-and-pack-format.md) |
| The catalogue distribution model | [RFC-0001](docs/rfc/0001-bundle-distribution-by-adapter-spec.md) |

Skills follow the [agentskills.io specification](https://agentskills.io/specification) — each a self-contained folder with closed frontmatter and no hidden cross-skill dependencies, so they install, copy, and audit cleanly.

## Contributing

Adding a pack, skill, or subagent? [`CONTRIBUTING.md`](CONTRIBUTING.md) has the three contribution lanes, the pack source-of-truth split, and the gates your PR has to pass.

## License

Licensed under either of [Apache 2.0](LICENSE-APACHE) or [MIT](LICENSE-MIT) at your option. Contributions are dual-licensed under the same terms unless you state otherwise.
