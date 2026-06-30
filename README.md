# agent-ready-repo

**A loop your coding agent can't cut corners in — and a catalogue of kits for the jobs around the code.**

The sharpest **loop engineering** for coding agents: plan, execute, verify, review — with gates it can't pass on red and a reviewer that reads every diff cold. Any repo, any agent.

[![PyPI](https://img.shields.io/pypi/v/agentbundle)](https://pypi.org/project/agentbundle/) [![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue)](#license)

[Quick Start](#quick-start) · [The Loop](#the-loop) · [The Catalogue](#the-catalogue) · [Build a Pack](#how-a-pack-is-laid-out) · [Docs](docs/guides/) · [Contributing](CONTRIBUTING.md)

> "You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents." — [Peter Steinberger](https://x.com/steipete/status/2063697162748260627)

The leverage in agent coding moved from the prompt to the **loop** — it plans, executes, verifies, and decides what comes next, so you stop babysitting every turn. But a loop running unattended is also a loop making mistakes unattended, so it has to check its own work harder than you would.

`core` is the flagship pack: that discipline made concrete — planning, hard gates, cold-eyed review, working as one loop the agent can't self-certify its way out of.

```bash
pip install agentbundle
agentbundle install --pack core
```

One line lands the loop in your repo — no catalogue argument needed; it defaults to this catalogue. Any agent that reads a skill file inherits it: Claude Code, Codex, Cursor, Copilot, Gemini, Kiro.

Behind `core` is a **catalogue of kits** — research, integration contract authoring, solution architecture, product shaping, and more — each a cohesive set of skills, subagents, and hooks that delivers one whole job, installed one line at a time. [See the catalogue.](#the-catalogue)

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

## The loop

Most agent workflows are `prompt → code → ship`. `core` replaces that one-shot path: it splits the maker from the verifier, and it won't skip a step.

1. **Plan, and surface the assumptions.** Before any code, the agent writes down what it's building, what it won't touch, and what it's assuming. When an assumption breaks mid-run, the loop stops and says so — no guessing past the problem.
2. **Hard gates between "done" and done.** Lint, typecheck, and tests run as gates. No path through the loop lets the agent claim success on a red gate.
3. **Adversarial review in a fresh session.** Once the gates pass, specialist reviewer agents read the diff cold — no attachment to the design, no sunk cost in the code. The loop fixes and re-reviews until the reviewers say `Clean — ready to commit.`
4. **Capture what it learned.** The model forgets between sessions; the repo doesn't. A run that trips over an undocumented convention lands the gap as a proposed edit to `CONVENTIONS.md`. Mistakes become the project's memory instead of evaporating.

The reviewers aren't generic critics. Each reviewer has its own unique sharp lenses, picked by what the change actually touches:

| Reviewer | Lens | When it runs |
| --- | --- | --- |
| `adversarial-reviewer` | spec/plan/impl drift, scope creep, missing edge cases | every diff |
| `security-reviewer` | OWASP 2025 + ASVS, STRIDE + LINDDUN — depth pulled per boundary | security-boundary work, at spec stage *and* on the diff |
| `quality-engineer` | testability, observability, reliability — the "cost to live with this code" | logic and interfaces worth maintaining |

The security lens **shifts left**: on security-boundary work it also runs at spec stage, catching a missing control as a one-sentence acceptance criterion instead of a post-implementation round-trip, and pulls its depth from a progressive-disclosure checklist library scoped to the boundaries a change crosses (OWASP 2025, ASVS, CWE Top 25) — current without bloating the prompt. The quality lens holds every diff to a raised maintainability floor by doctrine, whether or not a strict static-analysis gate is wired in. A fourth subagent, `implementer`, is the loop's own executor: it runs independent tasks in parallel.

→ [The core pack as a system](docs/guides/core/explanation/core-pack.md) walks through how the parts compose, and how it compares to vibe-coding, GitHub's Spec Kit, and Kiro's spec mode.

## The catalogue

The flagship `core` pack brings loop engineering to supercharge development in your code repos. Each other pack is a **kit** that delivers a use case end to end — a cohesive set of related skills, subagents, and hooks. Install only the kits needed at user scope or needed by your repo.

| Pack | Scope | Agentic use case |
| --- | --- | --- |
| [`core`](docs/guides/core/) | **repo** | **The flagship loop, on every change.** `work-loop`, `new-spec`, `bug-fix`, `adapt-to-project`, the four reviewer/executor subagents, `pre-pr` + `session-start` hooks, governance seeds. **Install this even if you install nothing else.** |
| [`governance-extras`](docs/guides/governance-extras/) | repo | **Keep a written trail of decisions.** RFC/ADR ceremony for teams and long-lived repos — `new-rfc`, `new-adr`, `update-conventions`, plus the `docs/rfc/` and `docs/adr/` shapes. |
| [`user-guide-diataxis`](docs/guides/user-guide-diataxis/) | repo | **Stand up a docs site.** Diátaxis skeleton — `docs/guides/{tutorials,how-to,reference,explanation}` plus `new-guide`. |
| [`monorepo-extras`](docs/guides/monorepo-extras/) | repo | **Scaffold packages in a monorepo.** `new-package` and a `packages/_example/` template. |
| [`research`](docs/guides/research/) | user / repo | **Go from a question to an evidence-grounded answer.** `research`, `source-map`, `compare-hypotheses`, `devils-advocate`, and more, plus two retrieval subagents. |
| [`contracts`](docs/guides/contracts/) | user / repo | **Author an API contract.** `api-contract` for OpenAPI 3.1. |
| [`converters`](docs/guides/converters/) | user / repo | **Move documents in and out of Markdown.** `file-to-markdown` (PDF/DOCX/PPTX/XLSX + images), `markdown-to-html`, `markdown-to-docx`/`-pptx`/`-xlsx` (branded Word/PowerPoint/Excel by template-fill), `msg-to-markdown`, `mermaid-renderer`. |
| [`atlassian`](docs/guides/atlassian/) | user / repo | **Work Jira and Confluence from the agent.** `jira`, `jira-align`, `confluence-crawler`, `confluence-publisher` (credentialed), plus `flow-metrics`, `ai-adoption-report`, `jira-defect-flow`. |
| [`figma`](docs/guides/figma/) | user / repo | **Read and render Figma designs.** Figma REST primitive (credentialed) — files/nodes/comments/variables, frame renders, FigJam → Mermaid. |
| [`architect`](docs/guides/architect/) | user / repo | **Design a system and pressure-test it.** `architect-design`, `architect-diagram`, `architect-review`, plus a read-only, forked-context `design-reviewer` subagent. |
| [`product-engineering`](docs/guides/product-engineering/) | user / repo | **Shape product intent into shippable specs.** `frame-intent`, `de-risk-intent`, `decompose-intent` over a recursive, level-tagged `intent`; `voice-and-microcopy` for UI copy; `align-value-stream` for the business-unit cross-component layer. |
| [`experience`](docs/guides/experience/) | user / repo | **Carry the whole design thread — journey to realization.** `map-customer-journey`, `map-screen-flow`, `blueprint-service`, `map-internal-process`, `aesthetic-direction`, `design-system-foundations`, `layout-and-information-architecture`, `interaction-design`, `design-critique`, a shared `quality-floor` checklist, and a forked-context `experience-reviewer` agent. Points to WCAG / W3C Design Tokens / Apple HIG / Material 3 / APQC / BPMN, never a stack. |

Swap `core` for any pack name in the command above. Repo-scope packs build on `core`; user-scope packs follow you across every project.

**Or stack several kits in one command.** A profile is a blessed combination of packs: `full-ceremony` adds the repo governance packs to `core`; `solution-architect` lands the `architect` + `research` + `contracts` toolkit; `inception` lands `research` + `product-engineering` + `architect` for taking an idea from zero to a buildable repo. `agentbundle list-profiles <catalogue>` shows them all — see the [install-a-profile how-to](docs/guides/_shared/how-to/install-a-profile.md).

## Ecosystem building blocks

Nothing here is a black box. Your skills, subagents, and hooks are files you own — no SDK, runtime, or service to run, nothing proprietary to lock into. Version and compose them like any other code.

- **Harness-agnostic.** One adapter pipeline projects the same primitives into Claude Code, Codex, Copilot, Cursor, Gemini, and Kiro layouts.
- **Inspectable and forkable.** The mechanics are prose you can read and `git diff`. Outgrow a default? Edit the file instead of filing a feature request.
- **Composable.** Packs layer cleanly, and your edits are never silently overwritten — colliding files land as `*.upstream` companions to merge, not clobber.

The two packages underneath are standalone, pip-installable, and useful well beyond this repo:

- **[`agentbundle`](https://pypi.org/project/agentbundle/)** — the bundler. Installs and upgrades packs, projects each primitive into the layout every agent expects, and builds catalogues of your own.
- **[`credbroker`](https://pypi.org/project/credbroker/)** — the credential resolver behind credentialed skills. Resolves secrets in-process through environment variable → OS keyring → dotfile, and never lets cleartext reach the model. See [credential handling](docs/architecture/credentials.md).

Loop engineering relocates judgment, it doesn't remove it — keeping every piece inspectable keeps that judgment where you can exercise it. You stay the engineer, not just the person who presses go.

## A foundation to build on

Adopt the catalogue as-is, or fork it as your own. The same bundler that installs these packs can publish yours: write your house conventions and review standards into `core`, add skills for your stack, and ship one catalogue every engineer installs in a single line — the loop, the reviewers, and the standards come out identical on every machine and in every agent. That makes this a foundation for an organization's AI dev kit, not just a set of defaults to consume.

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

Full documentation lives in **[`docs/guides/`](docs/guides/)**, organized by pack with tutorials, how-tos, reference, and explanation ([Diátaxis](https://diataxis.fr/)). The table jumps straight to the cross-cutting topics.

| Topic | Link |
| --- | --- |
| All four install routes (CLI, APM, Claude plugins, local clone) | [install routes](docs/guides/_shared/how-to/install-agentbundle-from-clone.md) |
| What each agent tool supports — skill / subagent / command / hook — and where it degrades | [adapter support matrix](docs/guides/_shared/reference/adapter-support.md) |
| Your edits are never silently overwritten — the file-safety contract | [file-safety contract](docs/guides/_shared/explanation/file-safety-contract.md) |
| Tailor freshly-installed primitives to your repo | [`adapt-to-project`](docs/guides/core/how-to/adapt-to-project.md) |
| Upgrading an installed pack | [upgrade packs](docs/guides/_shared/how-to/upgrade-packs.md) |
| Updating the agentbundle CLI itself — `pip install --upgrade agentbundle` | [PyPI](https://pypi.org/project/agentbundle/) |
| Mission, scope, and the four principles | [`docs/CHARTER.md`](docs/CHARTER.md) |
| The catalogue distribution model | [RFC-0001](docs/rfc/0001-bundle-distribution-by-adapter-spec.md) |

Skills follow the [agentskills.io specification](https://agentskills.io/specification) — each a self-contained folder with closed frontmatter and no hidden cross-skill dependencies, so they install, copy, and audit cleanly.

## Contributing

Adding a pack, skill, or subagent? [`CONTRIBUTING.md`](CONTRIBUTING.md) has the three contribution lanes, the pack source-of-truth split, and the gates your PR has to pass.

## License

Licensed under either of [Apache 2.0](LICENSE-APACHE) or [MIT](LICENSE-MIT) at your option. Contributions are dual-licensed under the same terms unless you state otherwise.
