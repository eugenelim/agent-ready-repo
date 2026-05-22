"""Build pipeline: adapter contract, reference adapters, recipes, self-host gate.

`main` is the CLI entrypoint — `python -m agentbundle.build` and the
`tools/build/build.py` shim both call it. Sibling specs (self-hosting,
RFC-0003's CLI) import `agentbundle.build` as a library; the public
surface is `main`, `validate.validate`, and the adapter `project`
functions exposed through `adapters`.

Subcommands landed in T1a:
  - `validate <path>` — load a TOML contract and check it against
    adapter.schema.json. Exit 0 on valid; 1 on invalid with a one-line stderr
    message.

Subcommands landing in later tasks (T6–T8):
  - `build` (default) + `--recipe`, `--self`, `--dry-run`, `--check`,
    `--force`, `--scaffold`, `PACK=`, `RECIPE=`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from agentbundle.build.contract import load as load_contract
from agentbundle.build.validate import validate as validate_instance
from agentbundle.build.main import cmd_build
from agentbundle.build.self_host import cmd_check, cmd_self

__all__ = ["main"]


def _cmd_validate(args: argparse.Namespace) -> int:
    contract_path = Path(args.path)
    if not contract_path.exists():
        print(
            f"validate: contract file not found at {contract_path}",
            file=sys.stderr,
        )
        return 1

    schema_path = (
        Path(__file__).resolve().parent.parent.parent.parent.parent
        / "docs"
        / "contracts"
        / "adapter.schema.json"
    )
    if not schema_path.exists():
        print(
            f"validate: adapter.schema.json not found at {schema_path}",
            file=sys.stderr,
        )
        return 1

    try:
        contract = load_contract(contract_path)
    except Exception as exc:
        print(f"validate: failed to load {contract_path}: {exc}", file=sys.stderr)
        return 1

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = validate_instance(contract, schema)
    if errors:
        print(
            f"validate: {contract_path} failed schema validation:",
            file=sys.stderr,
        )
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentbundle.build",
        description="Build pipeline for the agent-ready-repo catalogue.",
    )
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a TOML file against the adapter-contract schema.",
    )
    validate_parser.add_argument(
        "path",
        help="path to adapter.toml (or any TOML file the schema accepts)",
    )
    validate_parser.set_defaults(func=_cmd_validate)

    build_parser = subparsers.add_parser(
        "build",
        help="Run a recipe (or the three RFC-0001 default recipes).",
    )
    build_parser.add_argument(
        "--recipe",
        help="Recipe name (under build/recipes/) or explicit .toml path.",
    )
    build_parser.add_argument("--pack", help="Limit to one pack by name.")
    build_parser.add_argument(
        "--packs-dir",
        default="packs",
        help="Directory containing pack subdirectories (default: packs/).",
    )
    build_parser.add_argument(
        "--output-dir",
        default="dist",
        help="Where to write build artefacts (default: dist/).",
    )
    build_parser.set_defaults(func=cmd_build)

    self_parser = subparsers.add_parser(
        "self",
        help="Self-host build: render into the working tree (--dry-run for diff).",
    )
    self_parser.add_argument("--dry-run", action="store_true")
    self_parser.add_argument("--force", action="store_true")
    self_parser.add_argument("--packs-dir", default="packs")
    self_parser.add_argument("--output-dir", default=".")
    self_parser.set_defaults(func=cmd_self)

    check_parser = subparsers.add_parser(
        "check",
        help="Strict self-host dry-run; non-zero on any drift.",
    )
    check_parser.add_argument("--packs-dir", default="packs")
    check_parser.add_argument("--output-dir", default=".")
    check_parser.set_defaults(func=cmd_check)

    scaffold_parser = subparsers.add_parser(
        "scaffold",
        help="Drop a pack's seeds/ into the named output directory.",
    )
    scaffold_parser.add_argument("--packs-dir", default="packs")
    scaffold_parser.add_argument("--pack", default="core")
    scaffold_parser.add_argument("--output", required=True)
    scaffold_parser.set_defaults(func=_cmd_scaffold)

    return parser


def _cmd_scaffold(args) -> int:
    pack_seeds = Path(args.packs_dir) / args.pack / "seeds"
    output = Path(args.output)
    if not pack_seeds.exists():
        print(f"scaffold: no seeds/ in pack {args.pack!r}", file=sys.stderr)
        return 1
    output.mkdir(parents=True, exist_ok=True)
    for entry in pack_seeds.iterdir():
        destination = output / entry.name
        if entry.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(entry, destination)
        else:
            shutil.copy2(entry, destination)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return int(args.func(args))
