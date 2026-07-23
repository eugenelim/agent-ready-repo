# How to preview an install or upgrade with `--dry-run`

**Use this when:** You want to see exactly which files an install or upgrade would create, overwrite, or preserve as companions before committing any writes.
**Prerequisites:** `agentbundle` CLI on your PATH; for upgrades, the pack already installed; see [Prerequisites](#prerequisites).
**Result:** A printed plan of every file action (`create`, `overwrite`, `companion`) the real run would perform, with nothing written to disk.

See exactly what `agentbundle install` or `agentbundle upgrade` *would* do to your working tree — which files it creates, which it overwrites, and which of your edits it would preserve as `.upstream.<ext>` companions — without writing a single byte.

## When to reach for it

- Before the **first install** of a pack into a repo that already has hand-authored files at projection paths (`.claude/…`, `tools/…`), to see which of yours would be kept as companions.
- Before an **upgrade**, to see how many files moved and whether any of your local edits collide with the new version.
- In review or CI scripting, when you want the plan as plain text on stdout without committing to the change.

`--dry-run` is read-only: it runs the same pre-flight a real run does (resolve the catalogue, build the scope plan, render the projection, probe the path-jail), prints the plan, and stops **before** the first write. It writes no projected file, no companion, no `.agentbundle-state.toml`, and no install marker; it runs no chained `adapt` and prints no `installed:` / `upgraded:` recap.

## Prerequisites

- The `agentbundle` CLI on your PATH.
- For `upgrade`: the pack already installed (and, for APM / Claude-plugin installs, a one-time `agentbundle init-state` so the tier check has a baseline — see [upgrade-packs](upgrade-packs.md)).

## Preview an install

```bash
agentbundle install <catalogue-uri> --pack core --dry-run
```

A fresh install previews every file in the rendered adapter projection as a `create`:

```
create    tier-1 .claude/agents/adversarial-reviewer.md
create    tier-1 .claude/skills/work-loop/SKILL.md
create    tier-1 tools/hooks/pre-pr.py
dry-run: 29 file(s) — 29 create. Nothing written.
```

## Preview an upgrade

```bash
agentbundle upgrade <catalogue-uri> --pack core --dry-run
```

When you've edited a projected file since install, that file shows as a `companion` line naming the `.upstream.<ext>` the real run would drop alongside your edit (your file is never overwritten):

```
overwrite tier-1 .claude/agents/reviewer.md
overwrite tier-1 .claude/commands/deploy.md
companion tier-2 .claude/skills/work-loop/SKILL.md -> .claude/skills/work-loop/SKILL.upstream.md
dry-run: 20 file(s) — 19 overwrite, 1 companion. Nothing written.
```

A per-primitive preview narrows the plan to one primitive:

```bash
agentbundle upgrade <catalogue-uri> --pack core --skill work-loop --dry-run
```

## How to read the plan

Each line is `<action> <tier> <target path>`:

| Column   | Meaning                                                                 |
| -------- | ----------------------------------------------------------------------- |
| `action` | `create` (new file), `overwrite` (Tier-1 file the bundle owns), or `companion` (your edit is kept; the upstream version lands at `<path>.upstream.<ext>`). |
| `tier`   | `tier-1` (bundle-owned, safe to write), `tier-2` (you edited it — preserved). See the [file-safety contract](../explanation/file-safety-contract.md) for the full tier model. |
| target   | The path the file would land at, relative to the install root — the "where". For a `companion` line, ` -> ` names the companion path too. |

The closing `dry-run: … Nothing written.` line counts the plan by action and restates the no-write guarantee.

## What `--dry-run` does *not* do

- It previews the **rendered adapter projection** (the `.claude/…`, `tools/…` files). It does **not** yet enumerate the governance **seeds** an install also delivers at repo scope (`AGENTS.md`, `docs/CHARTER.md`, `docs/CONVENTIONS.md`) — those use a different, content-equality delivery path. A real install still creates them; the preview just doesn't list them (tracked in `workspace.toml [backlog]` as `projection-dry-run-governance-seeds`).
- It does **not** preview `--force`'s destructive cleanup. `agentbundle install --dry-run --force` is refused up front, because `--force` removes leftover files and rewrites state — operations a read-only preview must not perform. Run `--dry-run` without `--force` to preview, or `--force` without `--dry-run` to apply.
- A present Tier-2 collision does **not** change the exit code — a successful preview exits 0 even with companions in the plan. `--dry-run` is informational; `agentbundle diff` is the verb that gates on drift.
- If the read-only pre-flight itself would fail (catalogue unresolvable, spec-version mismatch, adapter resolution refused, a path that escapes the jail, pack not installed for `upgrade`, or a pre-RFC-0012 / orphan state install would refuse), `--dry-run` reports it on stderr and exits non-zero — exactly as the real run would at that stage, still writing nothing.

## Related

- [Upgrade an installed pack](upgrade-packs.md) — the real upgrade, once the preview looks right.
- [The file-safety contract](../explanation/file-safety-contract.md) — why edited files become `.upstream.<ext>` companions.
- [`agentbundle` reference](../reference/agentbundle.md) — the full flag set.
