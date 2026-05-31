"""Interactive credential setup — credential-broker-contract T7.

Walks the user through writing each required key in a skill's
``creds-schema.toml`` to the highest-available tier (OS keychain on
Darwin/Windows; 0600 dotfile floor on Linux or with
``--allow-insecure-fallback``).

Refuses the reserved ``sso`` namespace. Refuses
argv-borne credential flags and non-tty stdin.

This script is interactive, user-invoked, do not auto-run.
"""

from __future__ import annotations

import argparse
import getpass
import pathlib
import sys

# Bootstrap when invoked as ``python scripts/setup.py`` (Python sets
# ``__package__`` to None for file-path invocation, which breaks the
# ``from .credentials_shim import …`` line below). Gated on
# ``__spec__ is None`` so the block only fires for true file-path
# invocation; an importlib-based test harness (which sets ``__spec__``
# but may leave ``__package__`` empty) is not disturbed — the harness
# is responsible for its own package context.
if __package__ in (None, "") and __spec__ is None:
    _here = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(_here.parent))
    __package__ = _here.name

from .credentials_shim import (
    PermissiveAclError,
    SchemaError,
    Tier2HardFailError,
    _dotfile_write,
    _parse_schema,
    _tier2_backend,
    _tier2_backend_label,
)


RESERVED_NAMESPACES = frozenset({"sso"})

# Argv-borne credential flags refused per the argv ban.
_ARGV_BAN = frozenset({
    "--token",
    "--api-token",
    "--api-key",
    "--bearer",
    "--pat",
    "--password",
})

_ARGV_REFUSAL = "tokens cannot be passed via argv"

# Adapter-skill roots searched when ``--schema-path`` is not supplied.
_SKILL_ROOTS = (
    pathlib.Path.home() / ".claude" / "skills",
    pathlib.Path.home() / ".kiro" / "skills",
    pathlib.Path.home() / ".agents" / "skills",
)


def _refuse_argv_ban(argv: list[str]) -> None:
    for arg in argv:
        head = arg.split("=", 1)[0]
        if head in _ARGV_BAN:
            sys.stderr.write(f"credential-setup: argv-refusal: {_ARGV_REFUSAL}\n")
            sys.exit(3)


def _find_schema(namespace: str) -> pathlib.Path | None:
    """Walk adapter skill roots for a ``creds-schema.toml`` whose
    ``[namespace] name`` matches. Return the first match or ``None``."""
    for root in _SKILL_ROOTS:
        if not root.is_dir():
            continue
        for schema in root.glob("*/references/creds-schema.toml"):
            try:
                parsed = _parse_schema(schema)
            except SchemaError:
                continue
            if parsed.namespace == namespace:
                return schema
    return None


def _prompt(schema) -> dict[str, str]:
    values: dict[str, str] = {}
    sys.stderr.write(f"Enter values for namespace '{schema.namespace}':\n")
    for keydef in schema.keys:
        prompt = f"  {keydef.label} ({keydef.name}): "
        if keydef.secret:
            value = getpass.getpass(prompt)
        else:
            sys.stderr.write(prompt)
            sys.stderr.flush()
            value = input()
        if not value:
            sys.stderr.write(f"credential-setup: empty value for {keydef.name}\n")
            sys.exit(3)
        values[keydef.name] = value
    return values


def _write_tier3(
    namespace: str,
    values: dict[str, str],
    *,
    label: str,
    allow_permissive_acl: bool = False,
) -> int:
    try:
        for key, value in values.items():
            _dotfile_write(
                namespace, key, value,
                allow_permissive_acl=allow_permissive_acl,
            )
    except PermissiveAclError as exc:
        sys.stderr.write(
            f"credential-setup: DACL too permissive — {exc}; "
            "pass --allow-permissive-acl to override\n"
        )
        return 3
    sys.stderr.write(f"{label}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    _refuse_argv_ban(argv)

    parser = argparse.ArgumentParser(
        prog="credential-setup",
        description="Interactive credential setup. user-invoked.",
    )
    parser.add_argument(
        "namespace",
        help="The credential namespace to set up (e.g. 'jira', 'figma').",
    )
    parser.add_argument(
        "--schema-path",
        type=pathlib.Path,
        default=None,
        help="Explicit path to creds-schema.toml (skips auto-discovery).",
    )
    parser.add_argument(
        "--allow-insecure-fallback",
        action="store_true",
        help=(
            "Force Tier-3 dotfile write on Tier-2-capable platforms. "
            "For corporate machines where the keychain is unavailable."
        ),
    )
    parser.add_argument(
        "--allow-permissive-acl",
        action="store_true",
        help="Windows only: accept DACL not yet locked down (override).",
    )
    args = parser.parse_args(argv)

    namespace: str = args.namespace
    if namespace in RESERVED_NAMESPACES:
        sys.stderr.write(
            f"credential-setup: namespace '{namespace}' is reserved "
            f"(reserved set: {sorted(RESERVED_NAMESPACES)})\n"
        )
        return 2

    if args.schema_path is not None:
        try:
            schema = _parse_schema(args.schema_path)
        except SchemaError as exc:
            sys.stderr.write(f"credential-setup: {exc}\n")
            return 3
        if schema.namespace != namespace:
            sys.stderr.write(
                f"credential-setup: schema at {args.schema_path} declares "
                f"namespace '{schema.namespace}', not '{namespace}'\n"
            )
            return 3
    else:
        schema_path = _find_schema(namespace)
        if schema_path is None:
            sys.stderr.write(
                f"credential-setup: no creds-schema.toml found for "
                f"namespace '{namespace}' under any adapter skills root "
                f"({', '.join(str(r) for r in _SKILL_ROOTS)}); "
                f"pass --schema-path to point at one explicitly\n"
            )
            return 3
        schema = _parse_schema(schema_path)

    if not sys.stdin.isatty():
        sys.stderr.write(
            "credential-setup: stdin-not-tty: token entry requires an "
            "interactive prompt\n"
        )
        return 3

    values = _prompt(schema)

    if _tier2_backend is None:
        return _write_tier3(
            namespace, values,
            label="wrote to dotfile (Linux — Tier 2 deferred to v2 RFC)",
            allow_permissive_acl=args.allow_permissive_acl,
        )

    if args.allow_insecure_fallback:
        return _write_tier3(
            namespace, values,
            label="wrote to dotfile (insecure fallback)",
            allow_permissive_acl=args.allow_permissive_acl,
        )

    # Default Tier-2 path on Darwin/Windows.
    try:
        for key, value in values.items():
            _tier2_backend.write_credential(namespace, key, value)
    except Tier2HardFailError as exc:
        sys.stderr.write(
            f"credential-setup: Tier 2 hard fail — {exc}; "
            "pass --allow-insecure-fallback to write to the dotfile instead\n"
        )
        return 3
    except PermissiveAclError as exc:
        sys.stderr.write(f"credential-setup: {exc}\n")
        return 3
    sys.stderr.write(f"wrote to keyring ({_tier2_backend_label()})\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
