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
import tomllib
from pathlib import Path
from typing import Iterable


# The spec's only legal scope values; ``global`` is deliberately absent
# (RFC-0004 § Alternatives considered §6). Keep this single-sourced so
# argparse's `choices=` and the runtime resolver agree.
LEGAL_SCOPES: frozenset[str] = frozenset({"repo", "user"})

# RFC-0011 / pack-allowed-adapters: greenfield-fallback default when
# no adapter CLI home is present and the pack declares no preferred
# first adapter. Downstream catalogues can monkey-patch this constant
# at startup to flip the default for their own distribution.
DEFAULT_USER_SCOPE_ADAPTER: str = "claude-code"


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


# ---------------------------------------------------------------------------
# Adapter-contract introspection (RFC-0011 / pack-allowed-adapters)
# ---------------------------------------------------------------------------
#
# Three pure-data helpers that derive their answers from the bundled
# `agentbundle/_data/adapter.toml` shipped inside the wheel. The schema
# validator (`commands/validate.py`) and the CLI argparse setup
# (`cli.py`) both consume these so the schema enum, the argparse
# `choices=` list, and the runtime resolver all read from one place.


def _load_bundled_contract() -> dict:
    """Read `_data/adapter.toml` from the installed package.

    Kept private; callers go through the three high-level helpers
    below. Re-reads on every call (cheap; ~5KB TOML parse) so a
    monkeypatch in tests can swap the bundled file without leaking
    a cached parse.
    """
    contract_path = Path(__file__).parent / "_data" / "adapter.toml"
    return tomllib.loads(contract_path.read_text(encoding="utf-8"))


def shipped_adapters_from_contract() -> tuple[str, ...]:
    """Return every adapter declared in `[adapter.<name>]` blocks of
    the bundled contract, alphabetic-sorted.

    Consumers: the install CLI's argparse `--adapter` `choices=` list.
    Sorted-tuple shape so `argparse --help` renders stably across
    runs and Python versions.
    """
    contract = _load_bundled_contract()
    return tuple(sorted(contract.get("adapter", {}).keys()))


def user_scope_capable_adapters_from_contract() -> tuple[str, ...]:
    """Return adapters that declare `[adapter.<name>.scope].user` —
    the set that can target user scope at all.

    Consumers: the schema validator's `allowed-adapters` cross-field
    refusal; the install handler's `--adapter` user-scope-capability
    check. Sorted-tuple for the same stability reason as above.
    """
    contract = _load_bundled_contract()
    capable = []
    for name, block in contract.get("adapter", {}).items():
        scope = block.get("scope")
        if isinstance(scope, dict) and "user" in scope:
            capable.append(name)
    return tuple(sorted(capable))


# Contract versions that pre-date hook-wiring (RFC-0005). The
# `_kiro_target_adapters` rail and any future hook-related code path
# checks this; a literal-set check would silently break on the next
# contract bump (v0.7+), so the predicate is the load-bearing form.
_PRE_HOOK_WIRING_CONTRACT_VERSIONS: frozenset[str] = frozenset({"0.1", "0.2"})


def contract_supports_hook_wiring(version: str | None) -> bool:
    """True for any contract version that ships hook-wiring as a
    first-class primitive (v0.3 and later).

    The semantic predicate replaces the literal `version != "0.3"`
    check that lived at `validate.py:379` pre-RFC-0011 — that check
    silently dropped v0.6+ packs from the kiro-targeting rail and
    would re-break on v0.7. None / unknown values return False
    (conservative: a pack with no declared contract version is
    treated as pre-hook-wiring).
    """
    if not isinstance(version, str):
        return False
    return version not in _PRE_HOOK_WIRING_CONTRACT_VERSIONS
