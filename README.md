# agent-ready-repo

**The supervised AI operating model for software teams.**

```
Raw idea → Gate: Idea → Spec → Gate: Spec → Shipped code → Gate: PR → Production
```

[![PyPI](https://img.shields.io/pypi/v/agentbundle)](https://pypi.org/project/agentbundle/) [![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue)](#license) [![OWASP Agentic Skills Top 10](https://img.shields.io/badge/OWASP-Agentic%20Skills%20Top%2010%20v1.0-blue)](https://owasp.org/www-project-agentic-skills-top-10/)

[Quick Start](#quick-start) · [The Three Loops](#the-three-loops) · [The Catalogue](#the-catalogue) · [Docs](guides/) · [Contributing](CONTRIBUTING.md)

> "You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents." — [Peter Steinberger](https://x.com/steipete/status/2063697162748260627)

Agent coding tools moved the leverage from the prompt to the loop. But an unattended loop also makes unattended mistakes — and it will self-certify its way out of every check you give it. The answer is a supervised loop with mechanical gates the agent cannot bypass.

Three peer loops span the full SDLC. Discovery takes a raw idea to a ratified brief. The build loop runs spec to shipped code with hard gates and cold-read reviewers. The release loop validates the deployed whole before any human touches a prod switch. Human gates sit at every irreversible handoff; nothing runs past them automatically.

`core` is the flagship pack — the build loop, in one command:

```bash
python -m pip install agentbundle
agentbundle install --pack core
```

## Quick start

**Install via Claude Code** (no extra tooling required). This route installs at
user scope, so it carries the packs that permit it — repo-scoped packs like
`core` install with `agentbundle` instead:

```bash
# Add the marketplace once
claude plugin marketplace add eugenelim/agent-ready-repo

# Install any *user-scope* pack by name
claude plugin install architect@agent-ready-repo

# Browse all available packs with install commands
# → https://eugenelim.github.io/agent-ready-repo/plugins/
```

**Or install via agentbundle CLI** (supports all agent adapters):

```bash
# Install the CLI (one-time)
python -m pip install agentbundle

# See the catalogue
agentbundle list-packs

# See what you have installed — version + whether an upgrade is available
agentbundle list-installed

# Install the flagship loop into this repo
agentbundle install --pack core

# Install a pack at user scope — follows you across every project
agentbundle install --pack desk-research --scope user

# Install a whole curated profile in one command
agentbundle install --profile solution-architect

# Upgrade a pack to the catalogue's version (asks before writing; --yes for CI)
agentbundle upgrade --pack core

# Preview any install without writing a file
agentbundle install --pack core --dry-run
```

`--dry-run` previews every file before anything is written — one line per file, then a `create`/`overwrite` count. Installs auto-detect your agent and fall back to Claude Code; [configure a different default →](guides/_shared/how-to/configure-adapter.md)

Every source verb defaults to this catalogue when you don't name one; pass a git URL or local path to use a different one, or `agentbundle config set source <catalogue>` to change the default.

**Machine-readable catalogue:** `https://raw.githubusercontent.com/eugenelim/agent-ready-repo/claude-plugins-dist/marketplace.json`

## The three loops

```
product-engineering              core                    release-engineering
───────────────────              ────                    ───────────────────
discovery-lead                   work-loop               release-lead
Raw idea → Brief  ─Gate: Idea─▶  Spec → Shipped code  ─Gate: PR─▶  Production
```

Each loop is autonomous where the work is reversible and surfaces to a human at every irreversible step.

### Discovery — `product-engineering`

Raw idea → ratified brief. Five candidate shapes explored in parallel, collapsed through product, UX, architecture, and safety lenses.

**Human gate.** You approve a ratified decision brief, not a validated solution. The loop never advances past Gate: Idea automatically.

→ [Discovery loop guide](guides/product-engineering/) · [Walk a discovery end-to-end](guides/product-engineering/tutorials/walk-a-discovery-end-to-end.md)

### Build — `core`

Spec → shipped code. Lint, typecheck, and tests must pass. Three specialist reviewers each read the diff cold, in a fresh session — adversarial by design. Gate: Spec sits between the approved spec and the first line of implementation.

**Human gate.** You merge only when adversarial review is clean and all gates pass.

→ [The `core` pack as a system](guides/core/explanation/core-pack.md)

### Release — `release-engineering`

Built → production. Autonomous e2e convergence on ephemeral environments; deployed findings feed back to the build loop automatically.

**Human gate.** Prod ship always surfaces to a human. Always.

→ [Release loop guide](guides/release-engineering/) · [The release loop explained](guides/release-engineering/explanation/the-release-loop.md)

## The catalogue

Three packs form the operating model. The rest are curated kits — each distilled from the best practices of its discipline. Install only what your team needs.

| Pack | Scope | What it does |
| --- | --- | --- |
| [`core`](guides/core/) | **repo** | The build loop. `work-loop`, `new-spec`, `bug-fix`, the four reviewer/executor subagents, hooks, governance seeds. **Install this first.** |
| [`product-engineering`](guides/product-engineering/) | user | The discovery loop — raw idea to build-ready brief. |
| [`release-engineering`](guides/release-engineering/) | **repo** | The release loop — build to production. Hard-depends on `core`. |
| [`governance-extras`](guides/governance-extras/) | repo | RFC/ADR ceremony for teams and long-lived repos. |
| [`product-documentation`](guides/product-documentation/) | user / repo | Create, revise, audit, and verify product documentation. |
| [`monorepo-extras`](guides/monorepo-extras/) | repo | Scaffold packages in a monorepo. |
| [`desk-research`](guides/desk-research/) | user / repo | Go from a question to an evidence-grounded answer. |
| [`contracts`](guides/contracts/) | user / repo | Author an API contract (OpenAPI 3.1). |
| [`converters`](guides/converters/) | user / repo | Move documents in and out of Markdown. |
| [`atlassian`](guides/atlassian/) | user / repo | Work Jira and Confluence from the agent. |
| [`figma`](guides/figma/) | user / repo | Read and render Figma designs. |
| [`architect`](guides/architect/) | user / repo | Design a system and pressure-test it. |
| [`experience-design`](guides/experience-design/) | user / repo | Carry the whole design thread — journey to realization. |

A profile is a blessed combination of packs: `full-ceremony` adds the governance packs to `core`; `solution-architect` lands `architect` + `desk-research` + `contracts`; `inception` takes an idea from zero to a buildable repo. `agentbundle list-profiles` shows them all — see the [install-a-profile how-to](guides/_shared/how-to/install-a-profile.md).

Run `agentbundle catalogue init` to create a new catalogue from the managed scaffold. Write your conventions and review standards into `core`, add skills for your stack, and ship one catalogue every engineer installs in a single line — identical across every machine and every agent. The same bundler works for any domain, not just software delivery. [How to build your org's catalogue →](guides/_shared/how-to/create-a-catalogue.md)

## Ecosystem

Your skills, subagents, and hooks are files you own. No SDK, no runtime, no service. Version and compose them like any other code.

- Works with Claude Code, Codex, Cursor, Copilot, Gemini, and Kiro. One adapter pipeline projects the same primitives into the layout each agent expects.
- The mechanics are prose you can read and `git diff`. Outgrow a default? Edit the file.
- Packs layer cleanly. Colliding files land as `*.upstream` companions to merge, not clobber.
- Every pack is shaped through practitioner research and an RFC-and-ADR governance process.

Two standalone packages underpin it:

- **[`agentbundle`](https://pypi.org/project/agentbundle/)** — installs and upgrades packs, projects each primitive into the layout every agent expects, and builds catalogues of your own.
- **[`credbroker`](https://pypi.org/project/credbroker/)** — resolves secrets in-process through environment variable → OS keyring → dotfile. Cleartext never reaches the model. See [credential handling](docs/architecture/credentials.md).

## Contributing

Adding a pack, skill, or subagent? [`CONTRIBUTING.md`](CONTRIBUTING.md) has the three contribution lanes, the pack source-of-truth split, and the gates your PR has to pass.

## License

Licensed under either of [Apache 2.0](LICENSE-APACHE) or [MIT](LICENSE-MIT) at your option. Contributions are dual-licensed under the same terms unless you state otherwise.
