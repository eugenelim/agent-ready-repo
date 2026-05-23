"""Scope resolution + user-scope root expansion (RFC-0004 T17).

Two helpers:

  - :func:`resolve` resolves the install scope per the spec precedence
    rule **CLI flag > pack default > built-in ``"repo"``**, and refuses
    when the resolved value is not in the pack's ``allowed-scopes`` with
    :class:`ScopeRefused`. Used by every write-capable subcommand once
    the pack manifest is loaded.

  - :func:`resolve_user_root` runs ``pathlib.Path.expanduser("~")`` once
    and refuses with :class:`UserScopeUnresolvable` when the result is
    the literal ``"~"`` (expansion failed) or ``"/"`` (corporate sandbox
    with ``$HOME=/``). The CLI's top-level handler maps the exception
    to the documented stderr text ``cannot resolve user scope: $HOME
    unset or invalid``.

The exceptions carry just enough context for the formatter at the call
site to render the spec's exact stderr without per-call-site
introspection: ``ScopeRefused`` holds the pack name, the requested
scope, and the declared set; ``UserScopeUnresolvable`` holds the
diagnostic value (``"~"`` or ``"/"``).

This module is import-cheap (no I/O at import time) so the CLI's
``--version`` print path stays fast.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


# The spec's only legal scope values; ``global`` is deliberately absent
# (RFC-0004 § Alternatives considered §6). Keep this single-sourced so
# argparse's `choices=` and the runtime resolver agree.
LEGAL_SCOPES: frozenset[str] = frozenset({"repo", "user"})


class ScopeRefused(Exception):
    """Raised when the resolved scope is not in the pack's allowed-scopes.

    Attributes carry the three pieces the spec stderr names; the CLI's
    top-level handler formats them as
    ``<pack>: scope '<requested>' not in allowed-scopes <declared-set>``.
    """

    def __init__(
        self,
        pack_name: str,
        requested: str,
        allowed: Iterable[str],
    ) -> None:
        self.pack_name = pack_name
        self.requested = requested
        # Preserve the declared order — adopters reading the message
        # want to see what *they* wrote, not a re-sorted set.
        self.allowed = list(allowed)
        super().__init__(
            f"{pack_name}: scope {requested!r} not in allowed-scopes {self.allowed}"
        )


class UserScopeUnresolvable(Exception):
    """Raised when ``expanduser('~')`` cannot produce a usable user root.

    The two failure modes the spec names:

      - expansion returned literal ``"~"`` (no home directory at all),
      - expansion returned ``"/"`` ($HOME=/ — corporate sandbox).

    The CLI's top-level handler formats this as
    ``cannot resolve user scope: $HOME unset or invalid``.
    """


def resolve(
    cli_flag: str | None,
    pack_install: dict | None,
    builtin_default: str = "repo",
    *,
    pack_name: str = "<pack>",
) -> str:
    """Resolve the install scope per the spec precedence rule.

    Precedence: **CLI flag > pack ``default-scope`` > built-in ``repo``.**
    The resolved value must be in the pack's ``allowed-scopes`` (resolved
    from the install table, with the implied default
    ``[default-scope]`` when ``allowed-scopes`` is omitted).

    Args:
        cli_flag: the ``--scope`` argparse value (``None`` if omitted).
        pack_install: the ``[pack.install]`` table from the pack's TOML
            (``None`` when the pack is v0.1 — see RFC-0004 § *Install-
            scope dimension*; treated as ``{}``).
        builtin_default: the fallback when neither CLI nor pack declares.
        pack_name: the pack name for refusal text; the caller passes the
            real name when known so :class:`ScopeRefused` carries the
            spec-shaped message.

    Returns:
        The resolved scope (``"repo"`` or ``"user"``).

    Raises:
        :class:`ScopeRefused` if the resolved value is not in
        ``allowed-scopes``.
    """
    install = pack_install if isinstance(pack_install, dict) else {}
    pack_default = install.get("default-scope")
    if not isinstance(pack_default, str) or pack_default not in LEGAL_SCOPES:
        pack_default = builtin_default

    raw_allowed = install.get("allowed-scopes")
    if isinstance(raw_allowed, list) and raw_allowed:
        allowed = [s for s in raw_allowed if isinstance(s, str)]
    else:
        # Implied default: `[default-scope]` per RFC-0004 § *Per-pack
        # default and allowance*. v0.1 packs (no install table) fall
        # through to `[builtin_default]` which is `"repo"`.
        allowed = [pack_default]

    requested = cli_flag if isinstance(cli_flag, str) else pack_default

    if requested not in allowed:
        raise ScopeRefused(pack_name, requested, allowed)
    return requested


def resolve_user_root(home: Path | None = None) -> Path:
    """Expand the user-scope root once at scope-resolution time.

    Calls ``Path.expanduser("~")`` (or accepts a stub ``home`` for
    tests) and refuses when the result is the literal ``"~"`` (no
    home directory) or ``"/"`` ($HOME=/ — corporate sandbox).

    Returns:
        The resolved absolute :class:`Path` for ``~``.

    Raises:
        :class:`UserScopeUnresolvable` on either documented failure.
    """
    if home is None:
        try:
            expanded = Path("~").expanduser()
        except RuntimeError as exc:
            # Python 3.13+ raises RuntimeError when expanduser cannot
            # resolve (no $HOME and no pwd entry); older Pythons would
            # return the literal "~". Both signals normalise to "user
            # scope is unresolvable" — wrap.
            raise UserScopeUnresolvable(
                "expanduser('~') could not determine the home directory"
            ) from exc
    else:
        expanded = Path(home)
    if str(expanded) == "~":
        raise UserScopeUnresolvable("expanduser returned literal '~'")
    # Normalise before the root-check so a hostile `$HOME=/etc/..` is
    # caught (it resolves to `/`). We use Path.resolve(strict=False)
    # so a non-existent home doesn't raise — that's a separate failure
    # the downstream caller can surface.
    try:
        normalised = expanded.resolve(strict=False)
    except OSError as exc:
        raise UserScopeUnresolvable(
            f"could not resolve $HOME path {expanded}: {exc}"
        ) from exc
    if str(normalised) == "/":
        raise UserScopeUnresolvable("expanduser resolved to '/' ($HOME=/)")
    return normalised
