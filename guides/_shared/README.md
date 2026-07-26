# Shared guides

Guides about the catalogue itself — installing it, upgrading it, seeing what each agent tool supports, authoring new skills — rather than any one pack. Pack-specific guides live under each pack's own home; these are the cross-cutting ones.

## How-to

- [Install `agentbundle` from a clone](how-to/install-agentbundle-from-clone.md) — the fastest route to the CLI.
- [Install a user-scope pack into Codex](how-to/install-user-scope-pack-into-codex.md) — and what travels with you across projects.
- [Install a user-scope pack into Kiro](how-to/install-user-scope-pack-into-kiro.md) — the Kiro-specific layout.
- [Preview an install or upgrade with `--dry-run`](how-to/preview-install-or-upgrade.md) — see every file that would change before it changes.
- [Upgrade an installed pack](how-to/upgrade-packs.md) — pull new pack content without clobbering your edits.
- [Author a skill](how-to/author-a-skill.md) — write a new skill for any pack, to the catalogue's standards.
- [Choose a tracker integration](how-to/choose-a-tracker-integration.md) — pick the right brief-intake skill for your tracker (GitHub, Linear, Jira, Jira Align, or none).

## Reference

- [`agentbundle` reference](reference/agentbundle.md) — install the CLI, install a pack, configure the default adapter.
- [Adapter support matrix](reference/adapter-support.md) — which primitives each agent tool receives, and where it degrades.
- [Tracker vocabulary](reference/tracker-vocabulary.md) — how brief and spec levels map across GitHub, Linear, Jira, and Jira Align; skill routing table.

## Explanation

- [The three loops as a system](explanation/the-three-loops.md) — how discovery, build, and release compose into a complete operating model, and why each loop is a peer supervisor.
- [Install routes](explanation/install-routes.md) — the four ways pack content reaches a repo, and where each lands.
- [The pack catalogue](explanation/pack-catalogue.md) — what a pack is, how the catalogue is composed, and how you build your own.
- [The file-safety contract](explanation/file-safety-contract.md) — why your edits are never silently overwritten.
- [Shaping a new engagement](explanation/shaping-a-new-engagement.md) — how a product vision, a product strategy, and an architecture concept co-shape each other at the start of a new engagement.

---

Each quadrant subdirectory also carries a short writing-rules README ([tutorials](tutorials/README.md) · [how-to](how-to/README.md) · [reference](reference/README.md) · [explanation](explanation/README.md)) — what belongs in that kind of guide, for anyone authoring one.
