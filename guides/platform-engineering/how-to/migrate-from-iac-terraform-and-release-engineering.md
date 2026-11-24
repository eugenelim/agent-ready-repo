---
title: Migrate your platform packs
summary: Move installed packs in two phases, preserve edits, and roll back from a pinned catalogue.
pack: platform-engineering
kind: how-to
uses: [platform-engineering]
---

# Migrate your platform packs

Move your installed infrastructure and release workflows to `platform-engineering` while keeping your edits.

## Inventory installed rows

In a terminal inside your repository, list installed packs:

```bash
agentbundle list-installed
```

You see installed rows by adapter and scope, the agent host and file location for each install.

Record every old-pack row and its original adapter and scope for rollback. Replace `<a>` and `<s>` below with that row's adapter and scope (`repo` or `local`). For an adapter with old packs at different scopes, choose one scope for the new pack before phase 1. Core is optional.

## Remove every old row

For phase 1, run the matching uninstall for every installed old-pack row, across all adapters and scopes, before any install:

```bash
agentbundle uninstall --pack iac-terraform --adapter <a> --scope <s>
agentbundle uninstall --pack release-engineering --adapter <a> --scope <s>
```

Uninstall removes unchanged files and keeps edited files.

The installer refuses the new pack only where an old row owns the same files: the same adapter and scope, or another adapter sharing `.agents/skills/`. An old row for another adapter or at another scope is not refused, so phase 1 must remove every row first. An install beside an old row at another scope also leaves `.upstream` companions next to the old files; delete those companions after phase 2, because the files beside them already hold the new content. Upgrade does not replace this phase.

## Install the combined pack

For phase 2, choose a `<catalogue>` source containing `platform-engineering`, update any older source pin, and install for each adapter at its chosen scope:

```bash
agentbundle install <catalogue> --pack platform-engineering --adapter <a> --scope <s>
```

The new workflows install, and new content beside a kept edit lands as an `.upstream` companion for you to merge.

After an interruption, recheck installed rows, finish phase 1 for remaining old rows, and complete missing phase 2 installs. There is no automatic backup; files you delete during migration are not recovered.

## Roll back to the pinned catalogue

To reverse the move, uninstall every combined-pack row across all adapters and scopes first:

```bash
agentbundle uninstall --pack platform-engineering --adapter <a> --scope <s>
```

Edited files stay in place. Merge each `.upstream` companion beside them into its file, then delete the companion: the old install refuses while one remains.

Then restore each old-pack row at its original adapter and scope from the catalogue pinned to `42849d1e7`:

```bash
agentbundle install git+https://github.com/eugenelim/agent-ready-repo@42849d1e7 --pack iac-terraform --adapter <a> --scope <s>
agentbundle install git+https://github.com/eugenelim/agent-ready-repo@42849d1e7 --pack release-engineering --adapter <a> --scope <s>
```

The old workflows return with your kept edits, and old content beside an edit lands as a fresh `.upstream` companion.

Next: [Release a change](run-a-release.md).
