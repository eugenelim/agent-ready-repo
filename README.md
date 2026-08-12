# agent-ready-repo

**The supervised agentic build loop—and the catalogue of workflows around it.**

Decide what to build, design the product and system, implement and review software, plan infrastructure, validate releases, document what ships, and govern the catalogue your organization owns.

```text
Reversible agent work → mechanical checks → independent review → human decision
```

[![PyPI](https://img.shields.io/pypi/v/agentbundle)](https://pypi.org/project/agentbundle/) [![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue)](#license) [![OWASP Agentic Skills Top 10](https://img.shields.io/badge/OWASP-Agentic%20Skills%20Top%2010%20v1.0-blue)](https://owasp.org/www-project-agentic-skills-top-10/)

[Build with `core`](#build-with-core) · [Explore use cases](https://eugenelim.github.io/agent-ready-repo/#use-cases) · [Get started](https://eugenelim.github.io/agent-ready-repo/docs/getting-started/) · [Browse the catalogue](https://eugenelim.github.io/agent-ready-repo/catalogue/) · [Contribute](CONTRIBUTING.md)

## Choose a use case

- **Product managers and strategists:** move from strategy and evidence to a bounded decision brief with `product-strategy`, `desk-research`, and `product-engineering`.
- **Platform, infrastructure, and SRE teams:** design the boundary, author contracts, produce reviewable Terraform, and validate the deployed result with `architect`, `contracts`, `iac-terraform`, and `release-engineering`.
- **Software teams:** take a brief or spec through implementation, hard gates, independent review, and a human merge decision with `core`.
- **Design, research, documentation, and enablement teams:** [explore the use cases](https://eugenelim.github.io/agent-ready-repo/#use-cases) that map your work to the relevant packs.

Packs are composable units, not departments. Install only what you need, or use a profile when a curated starting set fits. The [complete catalogue](https://eugenelim.github.io/agent-ready-repo/catalogue/) remains the source for current pack inventory and install commands.

## Build with `core`

`core` is the catalogue's flagship and its strongest reason to start. It is a complete build system for coding agents: spec and plan before code, mechanical gates before claims, a cold independent review before handoff, and a human decision before merge.

```bash
python -m pip install agentbundle
agentbundle install --pack core
```

Then ask your coding agent:

```text
Implement <small, testable feature> with the work-loop.
```

The loop keeps fixing until the checks and review are clean. If it repeats the same failure, crosses a boundary, or reaches an irreversible decision, it stops and surfaces the choice instead of self-certifying. [See how `core` compares with prompt-and-approve coding, Spec Kit, and Kiro](guides/core/explanation/core-pack.md).

Using Claude? You can also [add this catalogue as a plugin marketplace](https://eugenelim.github.io/agent-ready-repo/docs/getting-started/install/#route-2-claude-plugins) and install any user-scope pack directly. Repo-scoped packs such as `core` install with `agentbundle` so the whole team shares the same loop.

## Own the system

`agentbundle` projects portable skills, subagents, hooks, commands, and seeds into the layout each supported agent expects. Installed files remain readable and editable; upgrades preserve local changes as explicit companions instead of silently clobbering them.

Create an organization-owned catalogue without forking this repository:

```bash
agentbundle catalogue init my-catalogue --name my-catalogue
agentbundle catalogue verify --root my-catalogue
```

[Understand packs, profiles, adapters, composition, and self-hosting](guides/_shared/explanation/pack-catalogue.md) · [Create a catalogue](guides/_shared/how-to/create-a-catalogue.md) · [Read the authoring standards](guides/_shared/reference/catalogue-authoring-standards.md)

## Go deeper

- **Use the catalogue:** [technical docs](https://eugenelim.github.io/agent-ready-repo/docs/) · [install routes](guides/_shared/explanation/install-routes.md) · [adapter support](guides/_shared/reference/adapter-support.md) · [`agentbundle` reference](guides/_shared/reference/agentbundle.md)
- **Understand the operating model:** [the three supervised loops](guides/_shared/explanation/the-three-loops.md) · [file safety](guides/_shared/explanation/file-safety-contract.md)
- **Inspect the implementation:** [architecture](docs/architecture/) · [machine contracts](contracts/) · [security model](docs/architecture/security.md)
- **Contribute:** [contribution lanes and gates](CONTRIBUTING.md) · [pack authoring](packs/) · [repository conventions](docs/CONVENTIONS.md)

## License

Licensed under either [Apache 2.0](LICENSE-APACHE) or [MIT](LICENSE-MIT) at your option. Contributions are dual-licensed under the same terms unless you state otherwise.
