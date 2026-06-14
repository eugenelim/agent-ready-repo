# agent-ready-repo

**A loop your coding agent can't cut corners in.**

Loop engineering for any repo, any agent. Plan, execute, verify, review. Gates it can't pass on red. A reviewer that reads every diff cold.

[![PyPI](https://img.shields.io/pypi/v/agentbundle)](https://pypi.org/project/agentbundle/)
[![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue)](#license)

> "You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents." — [Peter Steinberger](https://x.com/steipete/status/2063697162748260627)

The leverage in agent coding moved from the prompt to the **loop**. The loop plans, executes, verifies, and decides what comes next. You stop babysitting every turn.

Here's the part most people skip. A loop running unattended is also a loop making mistakes unattended. So it has to check its own work harder than you would.

`core` is the flagship pack. It's loop engineering made concrete: the planning discipline, the hard gates, and the cold-eyed review, working as one loop. The agent can't self-certify its way out of it.

```bash
pip install agentbundle
agentbundle install --pack core git+https://github.com/eugenelim/agent-ready-repo
```

One line lands the loop in your repo. Any agent that reads a skill file inherits it: Claude Code, Codex, Cursor, Copilot, Gemini, Kiro.

## The loop

Most agent workflows are `prompt → code → ship`. `core` replaces that one-shot path. It splits the maker from the verifier, and it won't skip a step.

1. **Plan, and surface the assumptions.** Before any code, the agent writes down what it's building, what it won't touch, and what it's assuming. When an assumption breaks mid-run, the loop makes it stop and say so. No guessing past the problem.
2. **Hard gates between "done" and done.** Lint, typecheck, and tests run as gates. No path through the loop lets the agent claim success on a red gate.
3. **Adversarial review in a fresh session.** Once the gates pass, a specialist reviewer reads the diff cold. No attachment to the design. No sunk cost in the code. The loop fixes and re-reviews until the reviewer says `Clean — ready to commit.`
4. **Capture what it learned.** The model forgets between sessions. The repo doesn't. When a run trips over an undocumented convention, the gap lands as a proposed edit to `CONVENTIONS.md`. Mistakes become the project's memory instead of evaporating when the session ends.

The reviewer isn't one generic critic. It's three sharp lenses, picked by what the change actually touches:

| Reviewer | Lens | When it runs |
| --- | --- | --- |
| `adversarial-reviewer` | spec/plan/impl drift, scope creep, missing edge cases | every diff |
| `security-reviewer` | OWASP 2025 + ASVS, STRIDE + LINDDUN — depth pulled per boundary | security-boundary work, at spec stage *and* on the diff |
| `quality-engineer` | testability, observability, reliability — the "cost to live with this code", held to a raised default quality floor | logic and interfaces worth maintaining |

The security lens **shifts left**: on security-boundary work it runs at spec stage as design guidance — catching a missing control as a one-sentence acceptance criterion instead of a post-implementation round-trip — and pulls its depth from a progressive-disclosure checklist library scoped to the boundaries a change actually crosses, so the review stays current (OWASP 2025, ASVS, CWE Top 25) without bloating the prompt. The quality lens holds every diff to a default quality floor — the universal maintainability smells and the mutation-testing mindset a strict static-analysis gate would enforce — applied by doctrine, whether or not such a gate is wired in.

A fourth subagent, `implementer`, is the loop's own executor. It runs independent tasks in parallel.

→ Want the whole picture? [The core pack as a system](docs/guides/core/explanation/core-pack.md) walks through how the parts compose, and how it compares to vibe-coding, GitHub's Spec Kit, and Kiro's spec mode.

## The catalogue

`core` is the flagship pack. It's the loop itself. Everything else is à la carte. Install only what your repo needs, at repo or user scope, one line each.

| Pack | Scope | What it ships |
| --- | --- | --- |
| [`core`](docs/guides/core/) | **repo** | **The flagship pack.** The loop: `work-loop`, `new-spec`, `bug-fix`, `adapt-to-project` skills, the four reviewer/executor subagents, `pre-pr` + `session-start` hooks, and governance seeds. **Install this even if you install nothing else.** |
| [`governance-extras`](docs/guides/governance-extras/) | repo | RFC/ADR ceremony for teams and long-lived repos that need a written trail for decisions — `new-rfc`, `new-adr`, `update-conventions` plus the `docs/rfc/` and `docs/adr/` shapes. |
| [`user-guide-diataxis`](docs/guides/user-guide-diataxis/) | repo | Diátaxis docs skeleton — `docs/guides/{tutorials,how-to,reference,explanation}` plus `new-guide`. |
| [`monorepo-extras`](docs/guides/monorepo-extras/) | repo | Monorepo scaffolding — `new-package` and a `packages/_example/` template. |
| [`research`](docs/guides/research/) | user / repo | Evidence-grounded research — `research`, `source-map`, `compare-hypotheses`, `devils-advocate`, and more, plus two retrieval subagents. |
| [`contracts`](docs/guides/contracts/) | user / repo | Contract authoring — `api-contract` for OpenAPI 3.1. |
| [`converters`](docs/guides/converters/) | user / repo | `file-to-markdown` (PDF/DOCX/PPTX/XLSX + images), `markdown-to-html`, `msg-to-markdown`, `mermaid-renderer`. |
| [`atlassian`](docs/guides/atlassian/) | user / repo | `jira`, `jira-align`, `confluence-crawler`, `confluence-publisher` (credentialed) plus `flow-metrics`, `ai-adoption-report`, `jira-defect-flow`. |
| [`figma`](docs/guides/figma/) | user / repo | Figma REST primitive (credentialed) — reads files/nodes/comments/variables, renders frames, FigJam → Mermaid. |
| [`architect`](docs/guides/architect/) | user / repo | Solution architecture — `architect-design`, `architect-diagram`, `architect-review`, plus a read-only, forked-context `design-reviewer` subagent for independent design critique. |
| [`product-engineering`](docs/guides/product-engineering/) | user / repo | Shape product intent into shippable specs — `frame-intent`, `de-risk-intent`, `decompose-intent` over a recursive, level-tagged `intent`; `voice-and-microcopy` for UI copy (error/empty/button/label) against a voice chart; and `align-value-stream` for the business-unit cross-component value-stream layer. Feeds the briefs/specs your delivery loop already builds. |

Repo-scope packs install into the current repo and build on `core`. User-scope packs install into `~/.claude/` (or your harness's home root) and follow you across every project. Swap `core` for any pack name in the command above.

## Ecosystem building blocks

Nothing here is a black box. Every piece is something you can pick up and use on its own.

Your skills, subagents, and hooks are files you own, with no SDK, runtime, or service to run, and nothing proprietary to lock into. You version and compose them like any other code in your repo.

- **Harness-agnostic.** One adapter pipeline projects the same primitives into Claude Code, Codex, Copilot, Cursor, Gemini, and Kiro layouts.
- **Inspectable and forkable.** The mechanics are prose you can read and `git diff`. When you outgrow a default, you edit the file instead of filing a feature request.
- **Composable.** Packs layer cleanly. Your edits are never silently overwritten. Colliding files land as `*.upstream` companions for you to merge, not clobber.

The two packages underneath are building blocks in their own right. Both are pip-installable, standalone, and useful well beyond this repo:

- **[`agentbundle`](https://pypi.org/project/agentbundle/)** — the bundler. It installs and upgrades packs, projects each primitive into the layout every agent expects, and builds catalogues of your own. `pip install agentbundle`
- **[`credbroker`](https://pypi.org/project/credbroker/)** — the credential resolver behind credentialed skills. It resolves secrets in-process through environment variable → OS keyring → dotfile, and never lets cleartext reach the model. Drop it into any Python project. `pip install credbroker`

Loop engineering relocates judgment, it doesn't remove it. Keeping every piece inspectable and composable keeps that judgment where you can exercise it. You stay the engineer, not just the person who presses go.

## A foundation to build on

Adopt the catalogue as-is, or use it as the base for your own. The same bundler that installs these packs can publish yours: fork them, write your house conventions and review standards into `core`, add skills for your own stack, and ship one catalogue that every engineer installs in a single line. The loop, the reviewers, and the standards come out identical on every machine and in every agent.

That makes this a foundation for an organization's AI dev kit, not just a set of defaults to consume.

## Going deeper

| Topic | Link |
| --- | --- |
| All four install routes (CLI, APM, Claude plugins, local clone) | [install routes](docs/guides/_shared/how-to/install-agentbundle-from-clone.md) |
| What each agent tool supports — skill / subagent / command / hook — and where it degrades | [adapter support matrix](docs/guides/_shared/reference/adapter-support.md) |
| Your edits are never silently overwritten — the file-safety contract | [file-safety contract](docs/guides/_shared/explanation/file-safety-contract.md) |
| Tailor freshly-installed primitives to your repo | [`adapt-to-project`](docs/guides/core/how-to/adapt-to-project.md) |
| Upgrading an installed pack | [upgrade packs](docs/guides/_shared/how-to/upgrade-packs.md) |
| Mission, scope, and the four principles | [`docs/CHARTER.md`](docs/CHARTER.md) |
| The catalogue distribution model | [RFC-0001](docs/rfc/0001-bundle-distribution-by-adapter-spec.md) |

Skills follow the [agentskills.io specification](https://agentskills.io/specification). Each is a self-contained folder with closed frontmatter and no hidden cross-skill dependencies. They install, copy, and audit cleanly.

## Contributing

Adding a pack, skill, or subagent? [`CONTRIBUTING.md`](CONTRIBUTING.md) has the three contribution lanes, the pack source-of-truth split, and the gates your PR has to pass.

## License

Licensed under either of [Apache 2.0](LICENSE-APACHE) or [MIT](LICENSE-MIT) at your option. Contributions are dual-licensed under the same terms unless you state otherwise.
