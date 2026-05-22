"""`agentbundle` CLI dispatcher — argparse over the eleven F-cli subcommands.

Subcommand order on the parser matches the canonical install-workflow order
from the spec (discovery-first): `list-packs`, `list-targets`, `scaffold`,
`install`, `validate`, `render`, `adapt`, `diff`, `upgrade`, `uninstall`,
`init-state`.

Each subcommand's `run(args) -> int` lives under `agentbundle.commands.*`;
this module wires `argparse` and prints `--version`. No business logic here.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from agentbundle.version import CLI_VERSION, SPEC_VERSION


def _version_string() -> str:
    return f"agentbundle {CLI_VERSION} (spec {SPEC_VERSION})"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentbundle",
        description=(
            "Reference CLI for the agent-ready-repo adapter contract. "
            "Library-first counterpart to the `adapt-to-project` LLM skill."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=_version_string(),
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    # --- list-packs ---
    sp = subparsers.add_parser(
        "list-packs",
        help="List packs available in a catalogue URI (local path or git+https).",
    )
    sp.add_argument("catalogue", help="Catalogue URI (local path or git+https://...).")
    sp.set_defaults(func=_lazy("list_packs"))

    # --- list-targets ---
    sp = subparsers.add_parser(
        "list-targets",
        help="List adapter targets the CLI supports (claude-code, kiro, copilot, codex).",
    )
    sp.set_defaults(func=_lazy("list_targets"))

    # --- scaffold ---
    sp = subparsers.add_parser(
        "scaffold",
        help="Drop a pack's seeds/ into --output, honouring Tier-1/2/3 file-safety.",
    )
    sp.add_argument("--pack", default="core")
    sp.add_argument("--packs-dir", default="packs")
    sp.add_argument("--output", required=True)
    sp.set_defaults(func=_lazy("scaffold"))

    # --- install ---
    sp = subparsers.add_parser(
        "install",
        help="Install a pack from a catalogue URI into the adopter repo.",
    )
    sp.add_argument("--pack", required=True)
    sp.add_argument("catalogue", help="Catalogue URI (local path or git+https://...).")
    sp.add_argument("--output", default=".")
    sp.set_defaults(func=_lazy("install"))

    # --- validate ---
    sp = subparsers.add_parser(
        "validate",
        help="Validate a pack's pack.toml against the schemas; --strict for conformance.",
    )
    sp.add_argument("pack_path", help="Path to a pack directory containing pack.toml.")
    sp.add_argument("--strict", action="store_true")
    sp.set_defaults(func=_lazy("validate"))

    # --- render ---
    sp = subparsers.add_parser(
        "render",
        help="Render a pack to --output via the F-build pipeline (byte-identical to `make build`).",
    )
    sp.add_argument("pack_path", help="Path to a pack directory.")
    sp.add_argument("--output", required=True)
    sp.add_argument(
        "--target",
        help="Optional adapter target (claude-code, kiro, copilot, codex); default: all.",
    )
    sp.add_argument(
        "--self-host",
        action="store_true",
        help=(
            "Treat --output as an adopter root: honour Tier-2 paths (write "
            ".upstream.<ext> companions on collision rather than overwriting). "
            "Requires a .agent-ready-state.toml at --output. Default: off "
            "(wholesale rewrite, matching `make build` dist/ semantics)."
        ),
    )
    sp.set_defaults(func=_lazy("render"))

    # --- adapt ---
    sp = subparsers.add_parser(
        "adapt",
        help="Resolve <adapt:NAME> markers in projected files; report .upstream.* companions.",
    )
    sp.add_argument("--values-from", help="TOML file with marker values.")
    sp.add_argument("--ci", action="store_true",
                    help="Exit non-zero if any .upstream.<ext> companion remains on disk.")
    sp.add_argument("--root", default=".")
    sp.set_defaults(func=_lazy("adapt"))

    # --- diff ---
    sp = subparsers.add_parser(
        "diff",
        help="Diff the on-disk projection against a fresh render; non-zero on drift.",
    )
    sp.add_argument("pack_path", help="Path to the pack to diff against.")
    sp.add_argument("--root", default=".")
    sp.set_defaults(func=_lazy("diff"))

    # --- upgrade ---
    sp = subparsers.add_parser(
        "upgrade",
        help="Upgrade a pack or a single primitive within a pack.",
    )
    sp.add_argument("--pack", required=True)
    sp.add_argument("--to", required=True, dest="to_version", help="Target pack version.")
    sp.add_argument("--skill")
    sp.add_argument("--agent")
    sp.add_argument("--hook")
    sp.add_argument("--seed")
    sp.add_argument("--command")
    sp.add_argument("catalogue", help="Catalogue URI to fetch the new version from.")
    sp.add_argument("--root", default=".")
    sp.set_defaults(func=_lazy("upgrade"))

    # --- uninstall ---
    sp = subparsers.add_parser(
        "uninstall",
        help="Uninstall a pack; remove Tier-1 files; preserve Tier-2 and Tier-3.",
    )
    sp.add_argument("--pack", required=True)
    sp.add_argument("--root", default=".")
    sp.set_defaults(func=_lazy("uninstall"))

    # --- init-state ---
    sp = subparsers.add_parser(
        "init-state",
        help="Hash an existing projection into .agent-ready-state.toml.",
    )
    sp.add_argument("--pack", required=True)
    sp.add_argument("--packs-dir", default="packs")
    sp.add_argument("--root", default=".")
    sp.set_defaults(func=_lazy("init_state"))

    return parser


def _lazy(module_name: str):
    """Lazy import of `agentbundle.commands.<module_name>:run`.

    Lets `agentbundle --version` and `--help` run before any command module
    is imported — important because some command modules (e.g. `install`)
    pull in `urllib.request`, `tarfile`, etc. that we don't want loaded for
    a `--version` print. Also keeps unit-test import paths cheap.
    """

    def _runner(args: argparse.Namespace) -> int:
        import importlib

        mod = importlib.import_module(f"agentbundle.commands.{module_name}")
        return int(mod.run(args))

    return _runner


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
