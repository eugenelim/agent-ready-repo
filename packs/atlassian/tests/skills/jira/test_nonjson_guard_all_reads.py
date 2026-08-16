"""An expired SSO session is diagnosed on *every* read path, not just `whoami`.

On the cookie path a `2xx` is not evidence of a live session: an SSO reverse
proxy commonly answers an expired one with `200` plus the IdP login page.
`whoami` guarded that; every other read called `resp.json()` directly, so the
same login page arrived as a bare `ValueError` and surfaced as a generic exit 1
— "invalid JSON" where the true cause is "your session expired". That sends the
operator to debug a parser instead of re-authenticating, which is the whole cost
of the bug.

The guard now lives in one shared `_json`, and these tests are what keep it
covering the whole surface: a new read method added tomorrow that calls
`resp.json()` directly fails `test_no_read_path_calls_resp_json_directly`.

Symmetry matters as much as coverage. On the **token** path a non-JSON 2xx is a
genuine server or proxy fault, not an expired session — reporting it as one
would be its own wrong answer — so the original error propagates there.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_SKILL_ROOT = _PACK_ROOT / ".apm/skills/jira"
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

pytest.importorskip("httpx")

import scripts._client as _client  # noqa: E402

SsoSessionUnavailable = _client.SsoSessionUnavailable


class _LoginPageResponse:
    """What an SSO proxy returns for an expired session: 200 + HTML."""

    status_code = 200
    content = b"<html><body>Sign in to continue</body></html>"

    def json(self):
        raise ValueError("Expecting value: line 1 column 1 (char 0)")


class _Client:
    """A JiraClient stand-in carrying only what `_json` reads."""

    def __init__(self, auth_mode: str) -> None:
        self._auth_mode = auth_mode
        self._profile = "corp-jira"

    _json = _client.JiraClient._json


def test_a_login_page_on_the_cookie_path_is_reported_as_an_expired_session() -> None:
    with pytest.raises(SsoSessionUnavailable) as exc:
        _Client("sso-cookie")._json(_LoginPageResponse())
    message = str(exc.value)
    assert "session has expired" in message
    assert "corp-jira" in message, "the message must name the profile to re-auth"
    assert "login page" in message, "name the usual cause, not just the symptom"


def test_the_token_path_does_not_claim_an_expired_session() -> None:
    """A non-JSON 2xx without a cookie session is a server fault, not an expiry.

    Reporting it as an expired session would send the operator to re-register a
    session that was never involved — a wrong answer delivered confidently.
    """
    with pytest.raises(ValueError) as exc:
        _Client("creds")._json(_LoginPageResponse())
    assert not isinstance(exc.value, SsoSessionUnavailable)


def test_a_valid_body_is_returned_unchanged() -> None:
    class _Ok:
        def json(self):
            return {"key": "PROJ-1"}

    assert _Client("sso-cookie")._json(_Ok()) == {"key": "PROJ-1"}


def _json_body_end(source: str) -> int:
    """Line number where `_json`'s own body ends — the one sanctioned caller."""
    lines = source.splitlines()
    start = next(i for i, ln in enumerate(lines, 1) if "def _json(self, resp)" in ln)
    for i in range(start, len(lines)):
        if lines[i].startswith("    async def ") or lines[i].startswith("    def "):
            return i
    return start + 40


def test_no_read_path_calls_resp_json_directly() -> None:
    """The guard is only worth having if it covers the whole surface.

    `whoami` was guarded and fourteen sibling reads were not, which is exactly
    what one-site-at-a-time fixing produces. This fails if a new method calls
    `resp.json()` instead of `self._json(resp)`.
    """
    source = (_SKILL_ROOT / "scripts" / "_client.py").read_text(encoding="utf-8")
    # Only the ONE legitimate site — inside `_json` itself — may call it.
    # Prose in a docstring mentioning `resp.json()` is not a call site, so the
    # scan requires the line to actually look like a statement.
    offenders = [
        f"{i}: {line.strip()}"
        for i, line in enumerate(source.splitlines(), start=1)
        if re.search(r"^\s*(return|[\w.]+\s*=)\s.*\bresp\.json\(\)", line)
        and "self._json" not in line
        and i > _json_body_end(source)
    ]
    assert not offenders, (
        "these lines decode a response without the expired-session guard:\n  "
        + "\n  ".join(offenders)
    )


def test_the_guard_lives_in_exactly_one_place() -> None:
    """One decoder, so the two paths cannot drift back apart."""
    source = (_SKILL_ROOT / "scripts" / "_client.py").read_text(encoding="utf-8")
    assert source.count("def _json(self, resp)") == 1
    # The SSO diagnosis text must not be duplicated back into a call site.
    assert source.count("non-JSON body (an IdP login page is the usual cause)") == 1
