# agentbundle

[![PyPI](https://img.shields.io/pypi/v/agentbundle)](https://pypi.org/project/agentbundle/)
[![Python](https://img.shields.io/pypi/pyversions/agentbundle)](https://pypi.org/project/agentbundle/)
[![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue)](https://github.com/eugenelim/agent-ready-repo#license)

**The installer for [agent-ready-repo](https://github.com/eugenelim/agent-ready-repo).** Think npm, but for the skills, subagents, and hooks your coding agent runs on. One pack, one command, every major agent — Claude Code, Codex, Cursor, Copilot, Gemini, and Kiro (both the CLI and the IDE).

## Quick start

```bash
pip install agentbundle
```

**Install into a repo** — so everyone who clones it gets the pack. `core` is the flagship pack, the loop itself:

```bash
agentbundle install --pack core
```

No catalogue argument needed: it defaults to the agent-ready-repo catalogue. It lands in the repo's agent config — subagents and skills included — and you commit it like any other project file. This is the default scope: the pack belongs to the project and the whole team.

**Install for yourself, everywhere** — so a pack follows you across every project, with no per-repo setup:

```bash
agentbundle install --pack research --scope user
```

User-scope packs land in your home directory, not the repo — they're yours, not the team's, and they're there in every project you open.

The install auto-detects your agent (`--adapter` overrides). To install from a **different** catalogue, pass it as a trailing argument — a git URL or a local path (`agentbundle install --pack core <catalogue>`); a `config set source <catalogue>` makes that the default, and an editable clone (`pip install -e`) defaults to itself.

## More commands

```bash
# See what the catalogue offers (bare uses the default; or name one explicitly)
agentbundle list-packs
agentbundle list-profiles

# Install a whole curated profile — a single-scope set of packs — in one command
agentbundle install --profile inception

# Preview any install without writing a file
agentbundle install --pack core --dry-run

# Upgrade to the version the catalogue ships — shows installed → target, asks first
agentbundle upgrade --pack core
agentbundle upgrade --pack core --yes  # skip the prompt (CI)

# Uninstall — previews remove (Tier-1) vs keep (your edits), asks first
agentbundle uninstall --pack core --dry-run
agentbundle uninstall --pack core --yes
```

A **profile** is a catalogue-curated, single-scope set of packs you install in one command — it declares its own scope, so `--scope` doesn't apply. **Upgrade takes no version** — the target is whatever the catalogue you point at declares; to pin a past version, point the catalogue at that git ref. Install a pack that's **already there** and `agentbundle` offers to `upgrade` it instead (`--yes` runs it straight away).

**Mutating commands ask first.** `uninstall`, the `--force` cleanup, and the upgrade offer all preview what they'll do and confirm before touching anything; `--dry-run` previews without writing, and `--yes` skips the prompt for non-interactive / CI use (where, without it, they refuse rather than hang).

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
