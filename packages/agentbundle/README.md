# agentbundle

[![PyPI](https://img.shields.io/pypi/v/agentbundle)](https://pypi.org/project/agentbundle/)
[![Python](https://img.shields.io/pypi/pyversions/agentbundle)](https://pypi.org/project/agentbundle/)
[![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue)](https://github.com/eugenelim/agent-ready-repo#license)

**The installer for [agent-ready-repo](https://github.com/eugenelim/agent-ready-repo).** Think npm, but for the skills, subagents, and hooks your coding agent runs on.

`agentbundle` installs packs of agent primitives into your repo or your home directory. It projects each primitive into the layout every agent expects. One pack. One command. Every major agent.

```bash
pip install agentbundle
agentbundle install --pack core git+https://github.com/eugenelim/agent-ready-repo
```

That lands `core`, the flagship pack and the loop itself, in your repo. Claude Code, Codex, Cursor, Copilot, Gemini, and Kiro — both the CLI and the IDE — all read it, subagents and skills included.

## Common commands

```bash
# See what's in a catalogue
agentbundle list-packs git+https://github.com/eugenelim/agent-ready-repo

# See the catalogue's curated install profiles
agentbundle list-profiles git+https://github.com/eugenelim/agent-ready-repo

# Install a whole curated profile — a single-scope set of packs — in one command
agentbundle install --profile inception git+https://github.com/eugenelim/agent-ready-repo

# Install the flagship loop into this repo
agentbundle install --pack core git+https://github.com/eugenelim/agent-ready-repo

# Install a pack at user scope, so it follows you across every project
agentbundle install --pack research git+https://github.com/eugenelim/agent-ready-repo --scope user

# Preview an install without writing a file
agentbundle install --pack core git+https://github.com/eugenelim/agent-ready-repo --dry-run

# Upgrade a pack; it reports the .upstream files you need to reconcile
agentbundle upgrade --pack core --to 0.4.0 git+https://github.com/eugenelim/agent-ready-repo
```

A catalogue is a git URL or a local path. Installs auto-detect your agent; pass `--adapter` to override. A **profile** is a catalogue-curated, single-scope set of packs you install in one command — it declares its own scope, so `--scope` doesn't apply.

## Build your own catalogue

`agentbundle` isn't tied to the agent-ready-repo catalogue. Any repo that lays its packs out the same way can use it. A pack is a directory:

```text
my-pack/
  pack.toml                  # name, version, adapter-contract, install scope,
                             # plus rich metadata (license, maintainers, links,
                             # categories, keywords) and a README pointer
  .claude-plugin/
    plugin.json              # Claude Code plugin manifest (hand-authored)
  README.md                  # the pack's portable doc — projected with the pack
  .apm/                      # primitives — projected by the build pipeline
    skills/<name>/
      SKILL.md               # the skill body; one folder per skill
      references/            # progressive-disclosure docs, loaded on demand
      assets/                # templates the skill copies into the repo
    agents/<name>.md         # subagents
    hooks/<name>.py          # lifecycle hooks
  seeds/                     # files scaffolded into the adopter repo
```

`pack.toml` is the **single source of truth** for a pack's metadata. Declare
`license`, `[[pack.maintainers]]`, `[pack.links]`, `categories`, and
`keywords` once; the build projects the cleanly-mappable subset — plus the
pack's `README.md` — into each distribution route's manifest (the `plugin.json`
/ `marketplace.json` entry), so the catalogue describes each pack richly rather
than with a single sentence. Extra fields stay in `pack.toml`; the projection
is deliberately lossy per tool.

Point a catalogue URI (a git URL or a local path) at the repo that holds your packs. Then `validate` a pack against the adapter contract, `render` it to preview the projection, and `install` it into a target repo. `scaffold` drops a pack's seeds into a fresh directory to start from. The build pipeline (`agentbundle.build`) is the same engine `make build` runs.

See the [pack layout reference](https://github.com/eugenelim/agent-ready-repo/blob/main/docs/architecture/pack-layout.md) and [authoring a skill](https://github.com/eugenelim/agent-ready-repo/blob/main/docs/guides/_shared/how-to/author-a-skill.md).

## Credentials

`agentbundle` doesn't resolve secrets. Credentialed skills use [`credbroker`](https://pypi.org/project/credbroker/), a standalone resolver that keeps cleartext out of the model's reach.

## Learn more

The full story — the loop, the reviewers, the pack catalogue — is in the [agent-ready-repo README](https://github.com/eugenelim/agent-ready-repo#readme).
