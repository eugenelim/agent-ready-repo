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

## Find a pack

Every pack has its own page under Pack listing in the sidebar. [Install packs for your agent](/agent-ready-repo/docs/guides/_shared/how-to/install-packs/) covers agents, previews, and upgrades.
