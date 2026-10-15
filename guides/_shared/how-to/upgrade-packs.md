---
title: "Upgrade packs"
summary: "Move an installed pack to a newer version, preview the change, and merge the upstream copies of files you edited."
pack: _shared
kind: how-to
---

# Upgrade packs

Move an installed pack to a newer version and keep your own edits. You need a pack installed from the catalogue and the `agentbundle` command.

## Upgrade a pack

```bash
agentbundle list-installed
agentbundle upgrade --pack <name> <catalogue>
agentbundle upgrade --pack core
```

`list-installed` shows each installed pack, its version, and whether an upgrade is available. `<catalogue>` is the URI you installed from, such as `git+https://github.com/<owner>/<catalogue>` or a local path.

`upgrade` takes no version. The target is whatever the catalogue declares.

Move one primitive and leave the rest of the pack at its installed version:

```bash
agentbundle upgrade --pack <name> --skill <skill-name> <catalogue>
```

`--agent`, `--hook`, `--seed <path>`, and `--command` work the same way. The mixed-version state goes in `.agentbundle-state.toml`, and the next whole-pack upgrade flags it.

If the pack is installed for more than one adapter at the scope, pass `--adapter`. The refusal lists each adapter with its version.

For packs installed with APM or as Claude plugins, use the tool's own verb:

```bash
apm update <pack>
```

In Claude Code, run `/plugin update <pack>@<catalogue>`. These follow that tool's conflict rules, not the file-safety contract. Run `agentbundle init-state` once after the original install so `agentbundle` has a baseline for those packs.

:::caution
`agentbundle install --pack` refuses an in-place re-install. Use `upgrade --pack` to change a version.
:::

## Preview an upgrade

```bash
agentbundle upgrade <catalogue-uri> --pack core --dry-run
agentbundle upgrade <catalogue-uri> --pack core --skill work-loop --dry-run
```

The preview writes nothing. It lists each file as `overwrite` or `companion`. See [Preview before you install](install-packs.md#preview-before-you-install) for how to read it.

## What upgrade reports

Before it writes, `upgrade` tells you how many of your edited files it will keep as companions. Then it reports one of:

- A real change: `upgraded: <pack> @ <scope> <from> -> <to>`.
- No version change: `re-applied: <pack> @ <scope> <version> (already current)`. It names the count of edited files kept as companions when there were edits.

## When you edited an installed file

If you changed a file since install, `upgrade` never overwrites it. It writes the new upstream version next to yours as `<name>.upstream.<ext>`. For example, `SKILL.md` gets `SKILL.upstream.md`.

Merge the companions one file at a time. Ask your agent to run the `adapt-to-project` skill. For each companion it offers accept, edit, skip, or decline. See [Adapt a freshly installed pack](../../core/how-to/adapt-to-project.md).

Files outside the pack's projected paths are never touched. The [file-safety contract](../explanation/file-safety-contract.md) defines the three tiers.

`upgrade` does not go back a version. To roll back, uninstall, then install from the earlier version's git ref:

```bash
agentbundle uninstall --pack <pack>
agentbundle install --pack <pack> git+https://github.com/<owner>/<catalogue>@<ref>
```

Your edited files and files outside the pack's paths survive an uninstall. Only the files the pack owns are removed.

## Upgrade agentbundle itself

Upgrade the command with the tool you installed it with:

```bash
python -m pip install --upgrade agentbundle
```

For an editable install from a clone, pull the clone. The CLI and the pack content both update with no reinstall.

```bash
git pull
```
