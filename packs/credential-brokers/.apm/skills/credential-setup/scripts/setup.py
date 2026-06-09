"""Interactive credential setup.

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
import re
import sys

# credbroker is a pip-installed package (RFC-0023), so this is an absolute
# import — no ``__package__`` bootstrap is needed (the former relative
# sibling-resolver import did require one for file-path invocation).
#
# Unlike the five API CLIs, setup.py has no ``__package__`` bootstrap and
# imports credbroker at module top, so the vendored-floor append must run
# *before* this import (or it runs too late). Append ~/.agentbundle/lib at
# LOWEST precedence: a no-repo user-scope install resolves credbroker from
# the floor, while a pip-installed credbroker (already on sys.path) still
# wins. Append, never insert(0); guarded on the dir existing.
# (credbroker-user-scope T1.)
_floor = pathlib.Path("~/.agentbundle/lib").expanduser()
if _floor.is_dir() and str(_floor) not in sys.path:
    sys.path.append(str(_floor))

from credbroker import (
    PermissiveAclError,
    SchemaError,
    Tier2HardFailError,
    VaultUnavailableError,
    crypto_available,
    keyring_available,
    parse_schema,
    source_vault_master,
    store_in_dotfile,
    store_in_keyring,
    store_in_vault,
    store_vault_master,
    tier2_backend_label,
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


class _ScrubbingArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that scrubs token-shaped values from error messages.

    ``_refuse_argv_ban`` above rejects the canonical banned flags before the
    parse, but a token passed under a flag it doesn't enumerate
    (``--credential SECRET``, ``--apikey SECRET``) would reach argparse,
    whose stock ``error()`` echoes ``--credential SECRET`` verbatim to stderr
    / the agent transcript. This subclass redacts any argv token of length
    >= 20 on a likely-credential character set before chaining to the stock
    error handler.
    """

    # Credential-shaped token: >= 20 chars on a base64 / base64url / JWT /
    # percent-encoded charset. `.` and `~` are included so dotted bearer /
    # JWT tokens (header.payload.signature) match — without `.` the anchored
    # regex fails on the separators and the value would leak. The >= 20 floor
    # is deliberate (modern PATs/tokens exceed it); a shorter value under an
    # out-of-set flag is not redacted.
    _CREDENTIAL_LOOKING_RE = re.compile(r"^[A-Za-z0-9_/+=%.~-]{20,}$")
    _STRIP_CHARS = "'\"`(),;:."

    def error(self, message: str) -> None:  # type: ignore[override]
        def _check(value: str) -> bool:
            core = value.strip(self._STRIP_CHARS)
            return bool(self._CREDENTIAL_LOOKING_RE.match(core))

        def _scrub(match: re.Match[str]) -> str:
            tok = match.group(0)
            if tok.startswith("-"):
                # Glued ``--flag=VALUE`` — check the RHS of the first ``=``
                # for credential shape and replace only that half.
                if "=" in tok:
                    flag, _, value = tok.partition("=")
                    if _check(value):
                        return f"{flag}=<scrubbed>"
                return tok
            if _check(tok):
                return "<scrubbed>"
            return tok

        scrubbed = re.sub(r"\S+", _scrub, message)
        super().error(scrubbed)


def _find_schema(namespace: str) -> pathlib.Path | None:
    """Walk adapter skill roots for a ``creds-schema.toml`` whose
    ``[namespace] name`` matches. Return the first match or ``None``."""
    for root in _SKILL_ROOTS:
        if not root.is_dir():
            continue
        for schema in root.glob("*/references/creds-schema.toml"):
            try:
                parsed = parse_schema(schema)
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
    context: str,
    allow_permissive_acl: bool = False,
) -> int:
    """Write the Tier-3 floor: the encrypted vault when the ``[crypto]`` extra
    is available, else the plaintext ``0600`` dotfile. ``context`` names why
    Tier 3 was chosen (no keyring / insecure fallback)."""
    if crypto_available():
        # VaultError (wrong master / tampered existing vault) is crypto-gated, so
        # import it lazily here — setup.py must import cleanly without [crypto].
        from credbroker._vault import VaultError

        try:
            master = source_vault_master()
        except VaultUnavailableError as exc:
            sys.stderr.write(f"credential-setup: {exc}\n")
            return 3
        if master is None:
            # Establish a vault master interactively (no echo). store_vault_master
            # is keyring-first; on a no-keyring box it writes the 0600 vault.master
            # so a later `load_credentials` can re-source it.
            master = getpass.getpass(
                "Set a vault master passphrase (encrypts the credential floor): "
            )
            if not master:
                sys.stderr.write("credential-setup: empty vault master\n")
                return 3
            try:
                store_vault_master(master)
            except (Tier2HardFailError, PermissiveAclError) as exc:
                sys.stderr.write(
                    f"credential-setup: could not store the vault master — {exc}\n"
                )
                return 3
        try:
            for key, value in values.items():
                store_in_vault(namespace, key, value, master=master)
        except VaultError as exc:
            # Wrong master against an already-existing vault (or a tampered one).
            sys.stderr.write(
                f"credential-setup: could not write the encrypted vault — {exc} "
                "(wrong vault master?)\n"
            )
            return 3
        except PermissiveAclError as exc:
            sys.stderr.write(
                f"credential-setup: DACL too permissive — {exc}; "
                "pass --allow-permissive-acl to override\n"
            )
            return 3
        sys.stderr.write(f"wrote to encrypted vault ({context})\n")
        return 0

    try:
        for key, value in values.items():
            store_in_dotfile(
                namespace, key, value,
                allow_permissive_acl=allow_permissive_acl,
            )
    except PermissiveAclError as exc:
        sys.stderr.write(
            f"credential-setup: DACL too permissive — {exc}; "
            "pass --allow-permissive-acl to override\n"
        )
        return 3
    sys.stderr.write(
        f"wrote to plaintext dotfile ({context}; install credbroker[crypto] "
        "for an encrypted floor)\n"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    _refuse_argv_ban(argv)

    parser = _ScrubbingArgumentParser(
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
            schema = parse_schema(args.schema_path)
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
        schema = parse_schema(schema_path)

    if not sys.stdin.isatty():
        sys.stderr.write(
            "credential-setup: stdin-not-tty: token entry requires an "
            "interactive prompt\n"
        )
        return 3

    values = _prompt(schema)

    if not keyring_available():
        return _write_tier3(
            namespace, values,
            context="no OS keyring on this platform",
            allow_permissive_acl=args.allow_permissive_acl,
        )

    if args.allow_insecure_fallback:
        return _write_tier3(
            namespace, values,
            context="insecure fallback",
            allow_permissive_acl=args.allow_permissive_acl,
        )

    # Default Tier-2 path on Darwin/Windows.
    try:
        for key, value in values.items():
            store_in_keyring(namespace, key, value)
    except Tier2HardFailError as exc:
        sys.stderr.write(
            f"credential-setup: Tier 2 hard fail — {exc}; "
            "pass --allow-insecure-fallback to write to the dotfile instead\n"
        )
        return 3
    except PermissiveAclError as exc:
        sys.stderr.write(f"credential-setup: {exc}\n")
        return 3
    sys.stderr.write(f"wrote to keyring ({tier2_backend_label()})\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
