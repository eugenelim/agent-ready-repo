# `agentbundle` — reference

> The three operations a fresh PyPI user actually performs, plus the
> built-in help surface. For the full subcommand catalogue, run
> `agentbundle --help`.

## Install `agentbundle`

```bash
pip install agentbundle
```

To install from a clone instead — for repo contributors or for users
on an offline / corporate network — see
[`../how-to/install-agentbundle-from-clone.md`](../how-to/install-agentbundle-from-clone.md).

After install, every subcommand is reachable via `agentbundle <verb>`
or `python -m agentbundle <verb>`. `agentbundle --help` lists the
full set.

## Install a pack

```bash
agentbundle install <catalogue-uri> --pack <pack-name>
```

`<catalogue-uri>` is a local path to a checked-out pack catalogue, or
a `git+https://…` URL. `--pack` selects which pack from the catalogue
to install.

Common flags:

| Flag                       | Effect                                                                                  |
| -------------------------- | --------------------------------------------------------------------------------------- |
| `--scope {repo,user}`      | Target install scope; default `repo`.                                                   |
| `--adapter <name>`         | Override the resolved adapter per-invocation (e.g. `claude-code`, `codex`, `kiro`).     |
| `--output <dir>`           | Output root; default depends on scope.                                                  |

Run `agentbundle install --help` for the complete set.

## Configure the default adapter

Once installed, `agentbundle` resolves the target adapter on every
install via a fixed cascade:

1. The `--adapter` flag, if passed.
2. The state-hint from a prior install of the same pack (so an
   upgrade stays on the adapter it was originally installed under).
3. The user-config file, if you've set one.
4. At user scope only: an on-disk IDE probe — if you have `~/.claude/`,
   `~/.codex/`, or `~/.kiro/` populated, the matching adapter is
   picked. This is the auto-detection layer for users who never ran
   `agentbundle config set` and don't pass `--adapter`.
5. The built-in default (`scope.DEFAULT_ADAPTER`, currently
   `claude-code`).

`agentbundle config` reads and writes layer 3. Four actions:

```bash
agentbundle config path                   # where the file lives
agentbundle config get [<key>]            # show effective value + provenance
agentbundle config set <key> <value>      # validate and write
agentbundle config unset <key>            # remove (deletes file if empty)
```

Today the only registered key is `adapter`. Future keys would be
added by the framework; the command surface stays the same.

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

You can hand-edit it; `agentbundle config` is a convenience over the
file, not a gate.

### When `agentbundle install` will refuse

If you have `adapter = "<name>"` configured and either:

- `<name>` is not supported at the install scope (e.g. `copilot`
  configured but installing at user scope — Copilot is repo-only), or
- the pack's `[pack.install] allowed-adapters` doesn't include
  `<name>`,

then `agentbundle install` refuses with a message naming the conflict
and listing the escape hatches (`--scope`, `--adapter`,
`agentbundle config set`, `agentbundle config unset`). The configured
value is preserved — the install just doesn't proceed under a value
you didn't pick.

Upgrades preserve their existing adapter regardless of user-config.
If you installed a pack under `claude-code`, then ran
`agentbundle config set adapter codex`, then upgraded that pack, the
upgrade stays on `claude-code` — `agentbundle config` shapes fresh
installs, not relayouts of existing ones.

## Other subcommands

See `agentbundle --help` for the full set (`validate`, `render`,
`adapt`, `diff`, `upgrade`, `uninstall`, `reconcile`, etc.). Each has
its own `--help` page documenting its flags.
