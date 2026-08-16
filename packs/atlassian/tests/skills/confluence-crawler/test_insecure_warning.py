"""`--insecure` must disclose itself on stderr, on both auth paths.

`docs/CONVENTIONS.md` § *Five anti-patterns rejected by name* requires
``--insecure`` to be opt-in and to "emit a stderr warning". This CLI was silent.

The two paths carry **different** messages, and the difference is the point:

* token path — the flag fires, verification is genuinely off;
* SSO-cookie path — the flag is inert (``from_sso_cookies`` builds its own SSL
  context and never receives it), so the warning says it is being *ignored*.

A single shared message would tell an operator on the cookie path that TLS
verification was disabled when it was not, which is worse than saying nothing.

Both tests drive ``main_async`` and let the run fail afterwards on absent
credentials — the assertion is on what reached stderr before that, so no
network, credential store, or browser profile is involved.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import sys
from pathlib import Path
from typing import Any

import pytest

# Import route: the SKILL root on sys.path, then ``import scripts.crawl_space``.
# A flat ``import crawl_space`` raises "attempted relative import with no known
# parent package" — the bootstrap block at the top of crawl_space.py is gated on
# ``__spec__ is None`` while the relative imports below it are unconditional.
# (The conftest adds the scripts/ dir, which serves the flat-import suites in
# this directory; this file needs the package route instead.)
_SKILL_ROOT = Path(__file__).resolve().parents[3] / ".apm/skills/confluence-crawler"
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

pytest.importorskip("httpx")

import scripts.crawl_space as crawl_space  # noqa: E402


def _args(**overrides: Any) -> argparse.Namespace:
    """A parsed-args stand-in carrying only what main_async reads before the
    warning. Built explicitly rather than through parse_args so the test does
    not depend on unrelated flags keeping their defaults."""
    base = {
        "insecure": True,
        "check": False,
        "verbose": False,
        "concurrency": 1,
        "min_delay_ms": 0,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def _run(args: argparse.Namespace) -> None:
    """Drive main_async far enough to pass the warning; swallow the later
    failure on absent credentials/config, which is not what is under test."""
    with contextlib.suppress(BaseException):
        asyncio.run(crawl_space.main_async(args))


def test_token_path_warns_that_verification_is_disabled(monkeypatch, capsys) -> None:
    monkeypatch.setattr(crawl_space, "_select_auth_path", lambda *a, **k: ("token", None))
    _run(_args())
    err = capsys.readouterr().err
    assert "--insecure disables TLS certificate verification" in err
    assert "is ignored" not in err, "the token path honours the flag; it is not ignored"


def test_token_path_is_silent_without_the_flag(monkeypatch, capsys) -> None:
    monkeypatch.setattr(crawl_space, "_select_auth_path", lambda *a, **k: ("token", None))
    _run(_args(insecure=False))
    assert "--insecure" not in capsys.readouterr().err


def test_sso_cookie_path_warns_that_the_flag_is_ignored(monkeypatch, capsys) -> None:
    sso = object()  # main_async only forwards it before the warning
    monkeypatch.setattr(
        crawl_space, "_select_auth_path", lambda *a, **k: ("sso-cookie", sso)
    )
    _run(_args())
    err = capsys.readouterr().err
    assert "--insecure is ignored on the SSO-cookie path" in err
    assert "disables TLS certificate verification" not in err, (
        "the cookie path must not claim verification was turned off — it stays on"
    )


def test_sso_cookie_check_subcommand_also_warns(monkeypatch, capsys) -> None:
    """The ignored-flag notice cannot be scoped to the non-check subcommands.

    `--check` returns early on this path, so a warning placed after that branch
    would be skipped for the one subcommand an operator is most likely to run
    while debugging a TLS problem. jira.py records the same reasoning.
    """
    sso = object()
    monkeypatch.setattr(
        crawl_space, "_select_auth_path", lambda *a, **k: ("sso-cookie", sso)
    )
    _run(_args(check=True))
    assert "--insecure is ignored on the SSO-cookie path" in capsys.readouterr().err


@pytest.mark.parametrize("auth_path", ["token", "sso-cookie"])
def test_some_warning_is_emitted_on_every_auth_path(monkeypatch, capsys, auth_path) -> None:
    """Guard against a third auth path being added with no disclosure at all."""
    monkeypatch.setattr(
        crawl_space,
        "_select_auth_path",
        lambda *a, **k: (auth_path, object() if auth_path == "sso-cookie" else None),
    )
    _run(_args())
    assert "--insecure" in capsys.readouterr().err
