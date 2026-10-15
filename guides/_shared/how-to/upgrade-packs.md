---
title: "Upgrade packs"
summary: "Upgrade installed packs without losing your edits."
pack: _shared
kind: how-to
---

# Upgrade packs

Move a pack to its latest version. Files you edited stay yours.

## See what is out of date

List installed packs and whether an upgrade is available:

```bash
agentbundle list-installed
```

## Upgrade a pack

Upgrade one pack:

```bash
agentbundle upgrade --pack core
```

Add `--dry-run` to see which files would change first.

## Keep your edits

When you have edited an installed file, the upgrade leaves it alone. The new version lands beside it as `<name>.upstream.<ext>`, for example `SKILL.upstream.md`.

Ask your agent to merge them:

```text
Run adapt-to-project and walk me through the upstream files.
```

The agent offers to accept, edit, skip, or decline each one.

## Roll back

`upgrade` does not go back a version. To roll back, uninstall and install from the earlier version:

```bash
agentbundle uninstall --pack core
agentbundle install --pack core git+https://github.com/<owner>/<catalogue>@<ref>
```

## Upgrade agentbundle

Upgrade the command itself:

```bash
python -m pip install --upgrade agentbundle
```

In a clone, `git pull` upgrades it.
