"""Subcommand modules — each exports `run(args) -> int`.

One module per F-cli subcommand. Modules are imported lazily by the CLI
dispatcher (`agentbundle.cli._lazy`) so `--version` / `--help` stay cheap.
"""
