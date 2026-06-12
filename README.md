# agent-ready-repo

**A loop your coding agent can't cut corners in.**
Loop engineering for any repo, any agent — a plan → execute → verify → review loop with gates it can't pass on red and a reviewer that reads every diff cold.

[![PyPI](https://img.shields.io/pypi/v/agentbundle)](https://pypi.org/project/agentbundle/)
[![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue)](#license)

> "You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents." — [Peter Steinberger](https://x.com/steipete/status/2063697162748260627)

The leverage in agent coding has moved from the prompt to the **loop** — the system that plans, executes, verifies, and decides what's next without you babysitting each turn. The catch is the part everyone skips: *a loop running unattended is also a loop making mistakes unattended.* So the loop has to verify its own work harder than you would.

The `core` pack **is** that loop — built so the agent **cannot self-certify its way out of it**, and shipped as Markdown you can read, edit, and `git diff`. Not a framework, not a service. Files.

```bash
pip install agentbundle
agentbundle install --pack core git+https://github.com/eugenelim/agent-ready-repo
```

One line lands the loop in your repo. Any agent that reads a skill file — Claude Code, Codex, Cursor, Copilot, Kiro — inherits it.

## The loop

Most agent workflows are `prompt → code → ship`. `core` replaces that one-shot path with a loop that separates the *maker* from the *verifier* and refuses to skip a step:

1. **Plan with surfaced assumptions.** Before any code, the agent writes what it's building, what it's *not* touching, and the assumptions it's making. When an assumption breaks mid-flight, the loop tells it to **stop and surface** — not guess past it.
2. **Mechanical gates between every "done" and the actual finish.** Lint, typecheck, and tests run as hard gates. There is no path through the loop that lets the agent declare success past a red gate.
3. **Adversarial review in a fresh session.** Once gates pass, a specialist reviewer reads the diff *cold* — no investment in the design, no sunk cost in the code. The loop iterates (fix → re-review) until the reviewer reports `Clean — ready to commit.`
4. **Capture-learnings, because the model forgets and the repo doesn't.** When a run trips over an undocumented convention, the gap lands as a candidate edit to `CONVENTIONS.md`. The agent's mistakes become the project's memory instead of evaporating at the end of the session.

The reviewer isn't one generic critic — three sharp lenses, dispatched by what the diff actually touches:

| Reviewer | Lens | When it runs |
| --- | --- | --- |
| `adversarial-reviewer` | spec/plan/impl drift, scope creep, missing edge cases | every diff |
| `security-reviewer` | OWASP Top 10 (web + LLM Apps) and STRIDE | auth, secrets, user input, I/O, deps, agent code |
| `quality-engineer` | testability, observability, reliability, "cost to live with this code" | logic and interfaces worth maintaining |

A fourth subagent, `implementer`, is the loop's own executor for running independent tasks in parallel.

→ The full walkthrough — how the parts compose, and how it compares to vibe-coding, GitHub's Spec Kit, and Kiro's spec mode — is in [The core pack as a system](docs/guides/explanation/core-pack.md).

## The catalogue

`core` is the loop. Everything else is à la carte — install only what your repo needs, at repo or user scope, one line each.

| Pack | Scope | What it ships |
| --- | --- | --- |
| [`core`](packs/core/) | **repo** | The loop: `work-loop`, `new-spec`, `bug-fix`, `adapt-to-project` skills, the four reviewer/executor subagents, `pre-pr` + `session-start` hooks, and governance seeds. **Install this even if you install nothing else.** |
| [`governance-extras`](packs/governance-extras/) | repo | RFC/ADR ceremony — `new-rfc`, `new-adr`, `update-conventions` plus the `docs/rfc/` and `docs/adr/` shapes. |
| [`user-guide-diataxis`](packs/user-guide-diataxis/) | repo | Diátaxis docs skeleton — `docs/guides/{tutorials,how-to,reference,explanation}` plus `new-guide`. |
| [`monorepo-extras`](packs/monorepo-extras/) | repo | Monorepo scaffolding — `new-package` and a `packages/_example/` template. |
| [`contracts`](packs/contracts/) | user / repo | Contract authoring — `api-contract` for OpenAPI 3.1. |
| [`converters`](packs/converters/) | user / repo | `file-to-markdown` (PDF/DOCX/PPTX/XLSX + images), `markdown-to-html`, `msg-to-markdown`, `mermaid-renderer`. |
| [`atlassian`](packs/atlassian/) | user / repo | `jira`, `jira-align`, `confluence-crawler`, `confluence-publisher` (credentialed) plus `flow-metrics`, `ai-adoption-report`, `jira-defect-flow`. |
| [`figma`](packs/figma/) | user / repo | Figma REST primitive (credentialed) — reads files/nodes/comments/variables, renders frames, FigJam → Mermaid. |
| [`architect`](packs/architect/) | user / repo | Solution architecture — `architect-design`, `architect-diagram`, `architect-review`. |

*Repo-scope* packs install into the current repo and build on `core`. *User-scope* packs install into `~/.claude/` (or your harness's home root) and follow you across every project. Swap `core` for any pack name in the install command above.

## An ecosystem building block

The `work-loop` skill is a Markdown file. Each reviewer is a Markdown file. The bundler installs them as plain-text primitives — **no SDK, no runtime, no service to host, no proprietary harness to lock into.** That's what makes this a building block and not a walled garden:

- **Harness-agnostic.** One adapter pipeline projects the same primitives into Claude Code, Codex, Copilot, and Kiro layouts. Cursor reads `AGENTS.md` directly.
- **Inspectable and forkable.** The mechanics are prose you can read and `git diff`. When you outgrow a default, you edit the file — you don't file a feature request.
- **Composable.** Packs layer cleanly; your edits are never silently overwritten — colliding files land as `*.upstream` companions to merge, not clobber.

Loop engineering relocates judgment rather than removing it. Plain-text primitives keep that judgment where you can exercise it — *build the loop like someone who intends to stay the engineer, not just the person who presses go.*

## Going deeper

| Topic | Link |
| --- | --- |
| All four install routes (CLI, APM, Claude plugins, local clone) | [install routes](docs/guides/how-to/install-agentbundle-from-clone.md) |
| What each agent tool supports — skill / subagent / command / hook — and where it degrades | [adapter support matrix](docs/guides/reference/adapter-support.md) |
| Your edits are never silently overwritten — the file-safety contract | [file-safety contract](docs/guides/explanation/file-safety-contract.md) |
| Tailor freshly-installed primitives to your repo | [`adapt-to-project`](docs/guides/how-to/adapt-to-project.md) |
| Upgrading an installed pack | [upgrade packs](docs/guides/how-to/upgrade-packs.md) |
| Mission, scope, and the four principles | [`docs/CHARTER.md`](docs/CHARTER.md) |
| The catalogue distribution model | [RFC-0001](docs/rfc/0001-bundle-distribution-by-adapter-spec.md) |

Skills follow the [agentskills.io specification](https://agentskills.io/specification) — each is a self-contained folder with closed frontmatter and no hidden cross-skill dependencies, so they install, copy, and audit cleanly.

## Contributing

Adding a pack, skill, or subagent? See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the three contribution lanes, the pack source-of-truth split, and the gates your PR has to pass.

## License

Licensed under either of [Apache 2.0](LICENSE-APACHE) or [MIT](LICENSE-MIT) at your option. Contributions are dual-licensed under the same terms unless you state otherwise.
