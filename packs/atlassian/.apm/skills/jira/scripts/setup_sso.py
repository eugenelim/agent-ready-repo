#!/usr/bin/env python3
"""Seed the sso-broker profile from references/sso-config.toml.

Reads and **validates** the ``[sso]`` config through the loader (which applies
the credbroker grammar / scheme / root-relative primitives *before* the broker
is touched), then hands the validated connection parameters to
``credbroker.register_sso_session``. No cookie value is ever passed on argv —
only validated connection parameters (path-not-value). The headed-browser
capture and at-rest storage are the broker's job.

**This helper is the escape hatch, not the ordinary path.** Two cases, and only
two:

1. a scripted pre-bake, where an enterprise has already written
   ``references/sso-config.toml`` and no operator is present to answer a prompt;
2. the case where the skill's primary check requests operator-assisted capture
   or cannot attest the configured sign-in destination.

An ordinary first run belongs in the primary check command documented by the
active ``SKILL.md``. Use this helper only when that check requests it; the
helper is safe only because an operator types it::

    python '<skill-dir>/scripts/setup_sso.py'
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sibling modules importable when run as ``python '<skill-dir>/scripts/setup_sso.py'`` and
# append the credbroker user-scope floor (lowest precedence) so the loader's
# validation primitives resolve in a no-repo install.
_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))
_floor = Path("~/.agentbundle/lib").expanduser()
if _floor.is_dir() and str(_floor) not in sys.path:
    sys.path.append(str(_floor))

from _sso_config import load_sso_config  # noqa: E402

# The recapture verbs landed in 0.5.0.
_CREDBROKER_REQUIREMENT = "credbroker>=0.5.0"


def main(argv: list[str] | None = None) -> int:
    """Register the configured profile. ``0`` on success, ``2`` on any refusal.

    The exit contract is the skill's credential band: every failure a human can
    act on is ``2``. Previously this returned the broker's own exit code
    verbatim, so an engine ``3`` surfaced as a functional error rather than a
    credential one.
    """
    # Imported here, not at module top: the credbroker floor is only on
    # sys.path after the bootstrap above.
    #
    # `ImportError`, not just `ModuleNotFoundError`: a half-projected floor
    # raises the parent class. And the *feature* detect matters as much as the
    # import — the pip layer precedes the vendored floor on `sys.path`, so an
    # adopter pinned below 0.5.0 imports a module that lacks
    # `register_sso_session`. Calling it would raise `AttributeError`, which is
    # not an `SsoError`, so it would escape `main` as exit 1 with a traceback
    # instead of this helper's exit-2 contract.
    try:
        import credbroker
    except ImportError:
        print(
            "error: credbroker is not installed — install the credential-brokers "
            f"pack, or run: python -m pip install '{_CREDBROKER_REQUIREMENT}'",
            file=sys.stderr,
        )
        return 2
    if not hasattr(credbroker, "register_sso_session"):
        found = getattr(credbroker, "__version__", "an older release")
        print(
            f"error: registering a session needs {_CREDBROKER_REQUIREMENT}, found "
            f"{found}. Run: python -m pip install --upgrade "
            f"'{_CREDBROKER_REQUIREMENT}'",
            file=sys.stderr,
        )
        return 2

    try:
        cfg = load_sso_config()  # validates before we touch the broker
    except Exception as exc:  # noqa: BLE001 — malformed config → don't register
        print(f"error: invalid sso-config.toml: {exc}", file=sys.stderr)
        return 2

    if cfg is None:
        print(
            'sso-config.toml: auth_default = "creds" — nothing to register '
            "(token auth is in effect).",
            file=sys.stderr,
        )
        return 0

    print(
        f"running: sso-broker register {cfg.profile} "
        "(opens a headed browser for SSO sign-in; the cookie jar is captured and "
        "stored by the broker — no cookie value passes through this helper). "
        "This helper performs no destination attestation; "
        "use the active skill's documented primary check when destination "
        "attestation is required.",
        file=sys.stderr,
    )

    try:
        credbroker.register_sso_session(
            cfg.profile,
            login_url=cfg.login_url,
            success_url_pattern=cfg.success_url_pattern,
            cookie_domains=cfg.cookie_domains,
            validation_endpoint=cfg.validation_endpoint,
            session_filename=cfg.session_filename,
            ttl_hint_minutes=cfg.ttl_hint_minutes,
        )
    except credbroker.SsoError as exc:
        # Every branch is a credential-band failure the operator must act on:
        # the engine is missing, playwright is missing, or the sign-in was not
        # completed. The engine's own stderr has already reached them.
        print(f"error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
