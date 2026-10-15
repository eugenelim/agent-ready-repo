---
title: "Build a pack"
summary: "Give every team your organization's standards in one install command."
pack: _shared
kind: how-to
---

# Build a pack

Package your organization's standards as a pack in a catalogue you own, so every team installs them in one command.

## Create the pack

For a single repository you do not need a pack: keep its sources where they are and let `adapt-to-project` route them from `AGENTS.md`. For many repositories, add a folder under `packs/` with a manifest, seeds (files an install writes into a repository), and skills:

```text
packs/acme-stack/
├── pack.toml
├── .apm/skills/
└── seeds/
```

In `pack.toml`, set `default-scope = "repo"` and require your copy of `core`. Leave out `lint-seeds = true`, because your seeds hold real content.

## Add your standards

Put your standards at the paths teams already use, and ask your agent to draft them:

```text
Help me package our backend standards as an organization-owned stack pack. Preserve the files we already use, and route backend-only commands from the backend subtree.
```

Repository-wide guidance goes in a `seeds/AGENTS.md` that is delta-only, meaning it links your sources instead of copying the core scaffold. If an install keeps it as `AGENTS.upstream.md`, `adapt-to-project` proposes a selective merge and never uses raw concatenation. Guidance for one subtree goes in a scoped `AGENTS.md` there, also delta-only. For each internal framework, add a skill under `.apm/skills/` so agents read its real contract; see [Author a skill](author-a-skill.md).

## Add a profile

Create `profiles/acme-golden-path.toml` with `core` first, because a profile installs in the order you list:

```toml
scope = "repo"
description = "Acme's golden path: the core workflow plus Acme's standard stack."

[[packs]]
pack = "core"

[[packs]]
pack = "acme-stack"
```

## Install from your copy

Each team clones your copy, installs `agentbundle` from it with `python -m pip install -e packages/agentbundle/`, and runs:

```bash
agentbundle install --profile acme-golden-path
```

Blank the `source` value in `packages/agentbundle/agentbundle/_data/install-defaults.toml` first, so a bare install cannot reach upstream.

Next, [design a profile](design-a-profile.md) for other roles. The [org-stack walkthrough](../reference/org-stack-pack-walkthrough.md) has the full manifest, a skill example, and common pitfalls.
