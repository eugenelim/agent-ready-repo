# Where repositories document how to launch and drive their product

> Discipline: applied (practitioner-pattern survey)

Commissioned 2026-11-02 while shaping the `verify-entries` spec, to choose a default file name for a per-repository record of how to launch, drive, and verify each product surface, and to list the existing files an agent should check first. It builds on [`subtree-verification-mapping-survey.md`](subtree-verification-mapping-survey.md), which covered CI gate maps and recommended `VERIFICATION.md` for that narrower artifact; this survey does not restate it.

## Recommendation

1. **No convention exists for a dedicated launch-and-drive file.** No host and no community standard names one file for "how to launch, drive, and verify this product". Agent hosts treat it as a section of their general instruction file or as a host-specific skill. Human-facing repositories put it in a developer guide. [moderate]
2. **Detect before creating.** The steps usually already live somewhere: a developer guide linked from `CONTRIBUTING.md`, a README section, a host skill, or tooling such as a Playwright `webServer` block. An agent that writes a new file without checking these duplicates content that then drifts. [moderate]
3. **Default name, used only when nothing covers the surface: `docs/VERIFICATION.md`.** This is a choice, not an existing convention. It keeps the word this repository already chose for verification material, and it sits in `docs/`, which is where developer guides commonly live and one of the three places GitHub searches for community-health files. [low]

## Findings

### Human-facing documents

| File or location | What it usually holds | Examples | Confidence |
| --- | --- | --- | --- |
| `CONTRIBUTING.md` (GitHub searches `.github/`, root, then `docs/`) | The entry point. It sometimes holds setup, launch, and test commands, but often only links to a developer guide | Signal-Desktop holds `pnpm start` and test commands; Neovim, Mastodon, and GitLab link out | [moderate] as entry point |
| Developer guide in the docs tree: `docs/DEVELOPMENT.md`, `docs/development/`, `contribute/developer-guide.md` | Per-environment setup, launch command, ready URL, seeded login, sample data | Mastodon `docs/DEVELOPMENT.md`; Grafana `contribute/developer-guide.md`; GitLab `doc/development/` | [moderate] |
| README "Building from source" / "Running locally" section | Prerequisites and build command, then a pointer elsewhere | Prometheus | [moderate], usually build-only |
| `BUILD.md` / `BUILDING.md` | Build, binary location, how to run uninstalled | Neovim; Signal's mobile apps | [low] — compiled products |
| `DEVELOPMENT.md` at root, `TESTING.md`, `HACKING.md` | Inconsistent; the name does not predict the content | Kong Insomnia's `DEVELOPMENT.md` has no run steps; OpenShift HyperShift keeps all three | [low] |
| Manual test plans and sanity checks | Release-tester checklists, not contributor run steps | VS Code wiki "Sanity Check" | [low] |
| `RUNBOOK.md`, `docs/runbooks/` | Operations and incident response, not local launch | Jan platform runbooks; AdAction engineering runbooks | [low] — do not treat as a launch doc |

Sources: [GitHub community-health lookup](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file), [Signal-Desktop CONTRIBUTING](https://github.com/signalapp/Signal-Desktop/blob/main/CONTRIBUTING.md), [Neovim CONTRIBUTING](https://github.com/neovim/neovim/blob/master/CONTRIBUTING.md), [Neovim BUILD.md](https://github.com/neovim/neovim/blob/master/BUILD.md), [Mastodon CONTRIBUTING](https://github.com/mastodon/mastodon/blob/main/CONTRIBUTING.md), [Mastodon DEVELOPMENT.md](https://github.com/mastodon/mastodon/blob/main/docs/DEVELOPMENT.md), [Grafana developer guide](https://github.com/grafana/grafana/blob/main/contribute/developer-guide.md), [GitLab CONTRIBUTING](https://github.com/gitlabhq/gitlabhq/blob/master/CONTRIBUTING.md), [Prometheus README](https://github.com/prometheus/prometheus/blob/main/README.md), [Insomnia DEVELOPMENT.md](https://github.com/Kong/insomnia/blob/develop/DEVELOPMENT.md), [HyperShift DEVELOPMENT.md](https://github.com/openshift/hypershift/blob/main/DEVELOPMENT.md), [VS Code How to Contribute](https://github.com/microsoft/vscode/wiki/How-to-Contribute), [VS Code Sanity Check](https://github.com/microsoft/vscode/wiki/Sanity-Check), [Jan runbooks](https://platform.jan.ai/docs/runbooks), [AdAction runbooks](https://eng.adaction.com/runbooks/).

Only Mastodon and Grafana publish a ready signal (a URL plus a seeded login). None of the sampled guides has a doctor check, isolation rules, an evidence location, or cleanup. Those fields are the gap a verify entry fills; the launch command is usually already written down. [synthesis]

### Agent-facing files

| Host | Where launch steps go | Dedicated run/verify file? |
| --- | --- | --- |
| AGENTS.md open format (read by Codex, Cursor, Copilot, Devin; Gemini by configuration) | Free-form "Dev environment tips", "Setup commands", or "Testing instructions" sections | No |
| Claude Code | Built-in `/run` and `/verify` infer launch from README, `package.json`, or `Makefile`; `/verify` may write `.claude/skills/verify/SKILL.md`, and `/run-skill-generator` writes `.claude/skills/run-<name>/`. A project skill named `verify` runs before each commit | Yes, but Claude-only |
| Cursor | `.cursor/rules/*.mdc` and AGENTS.md; the `cursor-team-kit` plugin ships `control-cli`, `control-ui`, `verify-this`, and `run-smoke-tests` skills, which build a harness but write no named repository file | No |
| GitHub Copilot | `.github/copilot-instructions.md`, which GitHub recommends should document bootstrap, build, test, run, and lint steps; `.github/workflows/copilot-setup-steps.yml` prepares the agent environment, not the product launch | No |
| Gemini CLI | `GEMINI.md`, concatenated into every prompt | No |
| Aider | `CONVENTIONS.md`, for coding guidelines | No |

Sources: [agents.md](https://agents.md), [Codex AGENTS.md guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Claude Code skills](https://code.claude.com/docs/en/skills), [Cursor rules](https://cursor.com/docs/context/rules), [cursor/plugins](https://github.com/cursor/plugins), [cursor-team-kit](https://github.com/cursor/plugins/tree/main/cursor-team-kit), [control-cli skill](https://github.com/cursor/plugins/blob/main/cursor-team-kit/skills/control-cli/SKILL.md), [Copilot repository instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions), [Copilot agent environment](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment), [GEMINI.md](https://geminicli.com/docs/cli/gemini-md/), [Aider conventions](https://aider.chat/docs/usage/conventions.html).

The cross-host finding is [moderate]: every host is covered by one primary page, and same-vendor pages count once. The Claude Code `/run` and `/verify` behavior is [low]: one official page, not corroborated.

### Machine-readable launch definitions

These define launch and sometimes readiness; an entry points at them rather than copying them.

| Definition | Readiness signal | Pitfall |
| --- | --- | --- |
| Playwright `webServer` (`command`, `url`, `wait`, `reuseExistingServer`) | Polls `url`; accepts 2xx, 3xx, and 400–403 | `reuseExistingServer: true` drives whatever instance is already listening; a 401 counts as ready |
| Compose `healthcheck` with `depends_on: condition: service_healthy` | As good as the probe command | `service_started` checks only that the container runs; a port-only probe can pass before init finishes |
| Dev Containers `devcontainer.json` (`postStartCommand`, `forwardPorts`, `waitFor`) | None for the app | `forwardPorts` cannot tell whether anything listens |
| `start-server-and-test` | Polls a URL, then tears down | — |
| VS Code `launch.json` `serverReadyAction` | Log pattern; IDE-only | — |
| `package.json` scripts, `Makefile`, `Taskfile.yml`, `justfile`, `Procfile` / `Procfile.dev`, Rails `bin/dev`, `script/server` | None — process up only | Target names are not standardized; a `smoke` target means different things in different repositories |

Sources: [Playwright webServer](https://playwright.dev/docs/test-webserver), [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/), [Dev Container JSON reference](https://containers.dev/implementors/json_reference/), [Scripts to Rule Them All](https://github.blog/engineering/scripts-to-rule-them-all/). The rows for npm scripts, Taskfile, just, Procfile, `launch.json`, and `start-server-and-test` rest on retriever background knowledge, not fetched pages. [low] for those rows; [high] for the Playwright and Compose rows, which are primary documentation.

## Detection list

An agent checks these, in order, before creating a file. When one already covers the surface, it offers to extend that file instead.

1. A verify file already routed from `AGENT_RULES.md`.
2. `CONTRIBUTING.md` in `.github/`, the root, or `docs/`, and the guides it links to.
3. Developer guides: `DEVELOPMENT.md`, `docs/DEVELOPMENT.md`, `docs/development/`, `contribute/`, `BUILD.md`, `BUILDING.md`, `TESTING.md`, `HACKING.md`, `VERIFICATION.md`.
4. README sections on running, building, or developing locally.
5. Agent instruction files: `AGENTS.md` setup or testing sections, `.github/copilot-instructions.md`, `GEMINI.md`, and host skills such as `.claude/skills/verify/` or `.claude/skills/run-*/`.
6. Launch and readiness tooling (the table above), which the entry points at for commands rather than for prose.

`RUNBOOK.md` and `docs/runbooks/` are operations documents; an agent does not extend them with local launch steps.

## Known unknowns

- **Known-unknown:** how often each file name appears across repositories. Would be closed by: a counted sample, for example a code search over a fixed set of popular repositories.
- **Known-unknown:** whether Cursor publishes a `create-verification-skill` outside `cursor-team-kit`, and what file it writes. Would be closed by: a full scan of the `cursor/plugins` tree at a pinned commit.
- **Known-unknown:** how often a healthcheck passes before initialization completes. Would be closed by: incident data or a measured sample; only the Compose documentation's caveat supports it here.
- **Known-unknown:** Windsurf and Jules conventions. Would be closed by: fetching their current documentation.
