Choose a pack by the work you want done, in [Find a pack by goal](#find-a-pack-by-goal). To start from a request you can paste, use [Skills by job](/agent-ready-repo/docs/packs/skills/).

A pack is a set of agent workflows you install together. Each pack does one kind of work, such as research, architecture design, or building and reviewing a change.

## What a pack installs

A pack can add four kinds of files to your agent:

- **Skills** — workflows your agent starts when your request matches them.
- **Subagents** — specialists the agent hands one task, such as an independent review.
- **Hooks and commands** — automatic checks and named entry points, where your agent supports them.
- **Seeds** — starter files a pack needs in the repository.

They are plain files you can read and edit. `agentbundle` installs and upgrades them; it does not run your agent.

## Install for the team

Install a pack into the repository when the whole team should work the same way. Run it from the repository's folder:

```bash
cd path/to/your-repo
agentbundle install --pack core
```

The files are committed with the code, so everyone who clones the repository gets the same skills, hooks, and checks at the same version. Changing them goes through review like any other change. Some packs, such as `core`, install only this way.

## Install for yourself

Install a pack into your home folder when it is your own tool:

```bash
agentbundle install --pack desk-research --scope user
```

It follows you into every repository, and nobody else sees it. Each pack sets a default scope; `--scope` chooses the other one where the pack allows it.

## Install as a Claude plugin

In Claude Code, packs you install for yourself are also available as plugins:

```bash
claude plugin marketplace add eugenelim/agent-ready-repo
claude plugin install desk-research@agent-ready-repo
```

Packs that install only into the repository are not plugins.

## Install a set of packs

A profile installs several packs in one command:

```bash
agentbundle install --profile inception
```

`agentbundle list-profiles` shows the sets and what each one installs.

## Find a pack by goal

### Decide what to build

- [`desk-research`](/agent-ready-repo/docs/packs/desk-research/) — Answer a question with sources you can check.
- [`product-strategy`](/agent-ready-repo/docs/packs/product-strategy/) — Run SWOT, Five Forces, PESTLE, BCG, OKRs and a PRFAQ before funding work.
- [`product-engineering`](/agent-ready-repo/docs/packs/product-engineering/) — Turn a raw idea into a tested bet and a shaped intent.
- [`architect`](/agent-ready-repo/docs/packs/architect/) — Assess, design, diagram and review architecture.
- [`code-intelligence`](/agent-ready-repo/docs/packs/code-intelligence/) — Find out what is true in a codebase before you change it.

### Design

- [`experience-design`](/agent-ready-repo/docs/packs/experience-design/) — Go from a customer journey to screens someone can build.
- [`frontend-engineering`](/agent-ready-repo/docs/packs/frontend-engineering/) — Build web surfaces that meet accessibility and performance targets.
- [`figma`](/agent-ready-repo/docs/packs/figma/) — Read a Figma file from its share link.
- [`contracts`](/agent-ready-repo/docs/packs/contracts/) — Write the API or event contract before the code.

### Build and review

- [`core`](/agent-ready-repo/docs/packs/core/) — Build a change under a spec, with checks and independent review.
- [`github`](/agent-ready-repo/docs/packs/github/) — Start work from a GitHub Issue and work through pull requests.
- [`iac-terraform`](/agent-ready-repo/docs/packs/iac-terraform/) — Write and check Terraform from a plain-language request.
- [`monorepo-extras`](/agent-ready-repo/docs/packs/monorepo-extras/) — Add a package to a monorepo.
- [`agent-skill-engineering`](/agent-ready-repo/docs/packs/agent-skill-engineering/) — Write, review and improve agent skills.

### Ship and record

- [`release-engineering`](/agent-ready-repo/docs/packs/release-engineering/) — Test a deployed build and set service level objectives.
- [`product-documentation`](/agent-ready-repo/docs/packs/product-documentation/) — Write documentation that matches what shipped.
- [`repo-governance`](/agent-ready-repo/docs/packs/repo-governance/) — Write RFCs and ADRs and find past decisions.

### Connect your tools

- [`atlassian`](/agent-ready-repo/docs/packs/atlassian/) — Work with Jira, Jira Align and Confluence.
- [`linear`](/agent-ready-repo/docs/packs/linear/) — Bring Linear work into your repository.
- [`converters`](/agent-ready-repo/docs/packs/converters/) — Convert documents, emails and Markdown between formats.
- [`credential-brokers`](/agent-ready-repo/docs/packs/credential-brokers/) — Keep credentials out of the repository and the agent's context.

### Maintain a catalogue

- [`catalogue-curation`](/agent-ready-repo/docs/packs/catalogue-curation/) — Bring in outside skills, propose packs and compile pack knowledge.

Next: [Install packs for your agent](/agent-ready-repo/docs/guides/_shared/how-to/install-packs/) covers agents, previews, and upgrades.
