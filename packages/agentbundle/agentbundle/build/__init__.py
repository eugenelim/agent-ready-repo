"""Build pipeline: adapter contract, reference adapters, recipes, self-host gate.

`main` is the CLI entrypoint — `python -m agentbundle.build` and the
`tools/build/build.py` shim both call it. Sibling specs (self-hosting,
RFC-0003's CLI) import `agentbundle.build` as a library; the public
surface is `main`, `validate.validate`, and the adapter `project`
functions exposed through `adapters`.

Subcommands landed in T1a:
  - `validate <path>` — load a TOML contract and check it against
    schema.json. Exit 0 on valid; 1 on invalid with a one-line stderr
    message.

Subcommands landing in later tasks (T6–T8):
  - `build` (default) + `--recipe`, `--self`, `--dry-run`, `--check`,
    `--force`, `--scaffold`, `PACK=`, `RECIPE=`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agentbundle.build.contract import load as load_contract
from agentbundle.build.validate import validate as validate_instance
from agentbundle.build.main import cmd_build

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
        / "specs"
        / "adapter-contract"
        / "schema.json"
    )
    if not schema_path.exists():
        print(f"validate: schema.json not found at {schema_path}", file=sys.stderr)
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
        help="path to contract.toml (or any TOML file the schema accepts)",
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return int(args.func(args))
