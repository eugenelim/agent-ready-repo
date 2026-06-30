# `agentbundle` — reference

> The three operations a fresh PyPI user actually performs, plus the built-in help surface. For the full subcommand catalogue, run `agentbundle --help`.

## Install `agentbundle`

```bash
pip install agentbundle
```

To install from a clone instead — for repo contributors or for users on an offline / corporate network — see [`../how-to/install-agentbundle-from-clone.md`](../how-to/install-agentbundle-from-clone.md).

After install, every subcommand is reachable via `agentbundle <verb>` or `python -m agentbundle <verb>`. `agentbundle --help` lists the full set.

## Install a pack

```bash
agentbundle install <catalogue-uri> --pack <pack-name>
```

`<catalogue-uri>` is a local path to a checked-out pack catalogue, or a `git+https://…` URL. `--pack` selects which pack from the catalogue to install.

Common flags:

| Flag                       | Effect                                                                                  |
| -------------------------- | --------------------------------------------------------------------------------------- |
| `--scope {repo,user}`      | Target install scope; default `repo`.                                                   |
| `--adapter <name>`         | Override the resolved adapter per-invocation (e.g. `claude-code`, `codex`, `kiro`).     |
| `--output <dir>`           | Output root; default depends on scope.                                                  |
| `--dry-run`                | Preview the per-file plan (action + tier + target path) to stdout and exit 0 without writing anything. Refused with `--force`. See [Preview before applying](#preview-before-applying). |

Run `agentbundle install --help` for the complete set.

## See what's installed

`agentbundle list-installed` reads your state files (not a catalogue) and reports every installed `(pack, adapter)` row across both scopes, with its version and whether an upgrade is available:

```bash
agentbundle list-installed
```

```
PACK        ADAPTER      SCOPE  INSTALLED  LATEST  STATUS
architect   claude-code  user   0.9.0      0.10.0  upgrade-available
architect   codex        user   0.9.0      0.10.0  upgrade-available
core        claude-code  repo   0.5.0      0.5.0   up-to-date
```

The `STATUS` is computed against the resolved catalogue: `up-to-date`, `upgrade-available`, or `unknown` (when the catalogue can't be resolved, or doesn't carry that pack). When the catalogue is unreachable the command still lists every row — `LATEST` shows `—` and `STATUS` is `unknown` — and exits 0; it never fails just because it couldn't reach a catalogue.

| Flag                  | Effect                                                                                       |
| --------------------- | -------------------------------------------------------------------------------------------- |
| `--scope {repo,user}` | Limit the listing to one scope; default lists both.                                          |
| `--no-check` / `--offline` | Skip the catalogue check entirely (no network): print only `PACK ADAPTER SCOPE INSTALLED`. |
| `--check-drift`       | Add a `DRIFT` column counting installed files edited locally since install (on-disk SHA differs from the recorded one). |

## Preview before applying

Both `agentbundle install` and `agentbundle upgrade` accept `--dry-run`: it runs the full read-only pre-flight, prints a per-file plan to stdout (one `<action> <tier> <target>` line each — `create` / `overwrite` / `companion`, with Tier-2 lines naming the `.upstream.<ext>` companion), and exits 0 without writing anything. Diagnostics and pre-flight failures go to stderr.

```bash
agentbundle install <catalogue-uri> --pack core --dry-run
agentbundle upgrade <catalogue-uri> --pack core --dry-run
```

`install --dry-run --force` is refused — `--force`'s destructive cleanup is incompatible with a read-only preview. See the [preview how-to](../how-to/preview-install-or-upgrade.md) for how to read the plan.

## Configure the default adapter

Once installed, `agentbundle` resolves the target adapter on every install via a fixed cascade:

1. The `--adapter` flag, if passed.
2. The state-hint from a prior install of the same pack (so an upgrade stays on the adapter it was originally installed under).
3. The user-config file, if you've set one.
4. At user scope only: an on-disk IDE probe — if you have `~/.claude/`, `~/.codex/`, or `~/.kiro/` populated, the matching adapter is picked. This is the auto-detection layer for users who never ran `agentbundle config set` and don't pass `--adapter`.
5. The built-in default (`scope.DEFAULT_ADAPTER`, currently `claude-code`).

`agentbundle config` reads and writes layer 3. Four actions:

```bash
agentbundle config path                   # where the file lives
agentbundle config get [<key>]            # show effective value + provenance
agentbundle config set <key> <value>      # validate and write
agentbundle config unset <key>            # remove (deletes file if empty)
```

Today the only registered key is `adapter`. Future keys would be added by the framework; the command surface stays the same.

### Example

```bash
$ agentbundle config path
/Users/alice/Library/Application Support/agentbundle/config.toml

$ agentbundle config get adapter
adapter	claude-code	(builtin)

$ agentbundle config set adapter codex
$ agentbundle config get adapter
adapter	codex	(file)

$ agentbundle install ./my-catalogue --pack demo
# resolves to codex unless overridden by --adapter or a state-hint.

$ agentbundle config unset adapter
$ agentbundle config get adapter
adapter	claude-code	(builtin)
```

### File location

| Platform | Path                                                                |
| -------- | ------------------------------------------------------------------- |
| macOS    | `~/Library/Application Support/agentbundle/config.toml`             |
| Linux    | `${XDG_CONFIG_HOME:-~/.config}/agentbundle/config.toml`             |
| Windows  | `%APPDATA%\agentbundle\config.toml`                                 |

The file is plain TOML with a single `[settings]` table:

```toml
[settings]
adapter = "codex"
```

You can hand-edit it; `agentbundle config` is a convenience over the file, not a gate.

### When `agentbundle install` will refuse

If you have `adapter = "<name>"` configured and either:

- `<name>` is not supported at the install scope (e.g. `copilot` configured but installing at user scope — Copilot is repo-only), or
- the pack's `[pack.install] allowed-adapters` doesn't include `<name>`,

then `agentbundle install` refuses with a message naming the conflict and listing the escape hatches (`--scope`, `--adapter`, `agentbundle config set`, `agentbundle config unset`). The configured value is preserved — the install just doesn't proceed under a value you didn't pick.

Upgrades preserve their existing adapter regardless of user-config. If you installed a pack under `claude-code`, then ran `agentbundle config set adapter codex`, then upgraded that pack, the upgrade stays on `claude-code` — `agentbundle config` shapes fresh installs, not relayouts of existing ones.

## What `upgrade` reports

`agentbundle upgrade` takes **no version** — the target is whatever the catalogue you point at declares (to pin a past version, point the catalogue at that git ref). It tells you honestly what it did:

- A real version change reports `upgraded: <pack> @ <scope> <from> -> <to>`.
- Re-running against the version you already have is a **re-apply**, not an upgrade: it reports `re-applied: <pack> @ <scope> <version> (already current)` — or names the count of locally edited files it kept as `.upstream` companions, when there were edits. Before it acts, it tells you up front how many of your edits will be preserved.
- A pack installed for **more than one adapter** at a scope needs `--adapter` to disambiguate; the refusal lists each adapter with its installed version, e.g. `pass --adapter to pick one: claude-code (0.9.0), codex (0.9.0)`. The same applies to `diff` and `uninstall`.

## Other subcommands

See `agentbundle --help` for the full set (`list-packs`, `list-profiles`, `list-targets`, `list-installed`, `validate`, `render`, `adapt`, `diff`, `upgrade`, `uninstall`, `reconcile`, etc.). Each has its own `--help` page documenting its flags.
