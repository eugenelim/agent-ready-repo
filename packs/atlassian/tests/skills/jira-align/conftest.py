"""Resolve the jira-align skill's runtime tree for the tests that exercise it.

Tests live outside the runtime payload (ADR-0071); the modules they exercise live
under ``.apm/``. Nothing in this directory is projected into an installed environment.

The jira and jira-align skills both ship ``_client.py`` and ``_preserve_write.py``, so
the jira-align scripts are registered as the package ``align_skill_scripts`` instead of
going to the front of ``sys.path`` (that would shadow the jira skill's flat imports).
Inside the package the relative imports resolve to this skill's own copies.
"""

from __future__ import annotations

import json
import sys
import types
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pytest

SKILL = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "jira-align"
SCRIPTS = SKILL / "scripts"
if not SCRIPTS.is_dir():                      # wrong parents[] depth after a move
    raise SystemExit(f"skill scripts dir not found at {SCRIPTS}")

PACKAGE = "align_skill_scripts"
if PACKAGE not in sys.modules:
    _pkg = types.ModuleType(PACKAGE)
    _pkg.__path__ = [str(SCRIPTS)]
    sys.modules[PACKAGE] = _pkg
# Flat fallback for tests that load ``_client.py`` by path: last on the path, so the
# jira skill's copies keep precedence when both folders run in one session.
if str(SCRIPTS) not in sys.path:
    sys.path.append(str(SCRIPTS))

API = "/rest/align/api/2"


# --- recording fake Jira Align transport (preserve-first write tests) --------------------


@dataclass
class Recorded:
    """One request the fake saw."""

    method: str
    url: str
    path: str
    query: str
    body: Any
    headers: dict[str, str]


class FakeAlign:
    """A recording fake transport for one Jira Align instance.

    ``records`` maps ``"resource/id"`` to the record as the server holds it. ``PATCH``
    merges the body into the record; ``PUT`` replaces the record with the body (so every
    field the body omits is cleared, like a real full replace).
    """

    def __init__(self, base: str, records: dict[str, dict[str, Any]]) -> None:
        self.base = base
        self.records = records
        self.requests: list[Recorded] = []
        # Return a response to take over a request; return None to fall through.
        self.override: Callable[[Recorded], httpx.Response | None] | None = None
        # Called with each non-GET request just before it is answered.
        self.on_write: Callable[[Recorded], None] | None = None
        # Called after a PATCH or PUT is applied, to model server-side side effects.
        self.after_write: Callable[[dict[str, Any]], None] | None = None

    @property
    def writes(self) -> list[Recorded]:
        return [r for r in self.requests if r.method not in ("GET", "HEAD")]

    def handler(self, request: httpx.Request) -> httpx.Response:
        raw = request.content
        rec = Recorded(
            request.method,
            str(request.url),
            request.url.path,
            request.url.query.decode(),
            json.loads(raw) if raw and request.headers.get("content-type", "").startswith(
                "application/json"
            ) else None,
            {k.lower(): v for k, v in request.headers.items()},
        )
        self.requests.append(rec)
        if rec.method not in ("GET", "HEAD") and self.on_write is not None:
            self.on_write(rec)
        if self.override is not None:
            taken = self.override(rec)
            if taken is not None:
                return taken
        return self._route(rec)

    def _route(self, rec: Recorded) -> httpx.Response:
        parts = rec.path.removeprefix(API).strip("/").split("/")
        if len(parts) == 2:
            key = "/".join(parts)
            if key not in self.records:
                return httpx.Response(404, json={"message": "not found"})
            held = self.records[key]
            if rec.method == "GET":
                return httpx.Response(200, json=held)
            if rec.method in ("PATCH", "PUT"):
                body = rec.body or {}
                if rec.method == "PATCH":
                    held.update(body)
                else:
                    keep_id = {"id": held["id"]} if "id" in held else {}
                    held.clear()
                    held.update({**keep_id, **body})
                if self.after_write is not None:
                    self.after_write(held)
                return httpx.Response(200, json=held)
            if rec.method == "DELETE":
                return httpx.Response(204)
        if len(parts) == 1 and rec.method == "POST":
            return httpx.Response(201, json={"id": 99})
        return httpx.Response(404, json={"message": "unrouted"})

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Route every ``httpx.AsyncClient`` through this fake."""

        real = httpx.AsyncClient
        transport = httpx.MockTransport(self.handler)
        monkeypatch.setattr(
            httpx, "AsyncClient", lambda *a, **k: real(*a, **{**k, "transport": transport})
        )


@pytest.fixture
def tracker_home(tmp_path, monkeypatch):
    """Redirect the user's home to a temp dir so nothing touches the real ``~/.agentbundle``."""

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    assert Path.home() == home
    return home


@pytest.fixture
def make_fake_align(monkeypatch):
    """Build and install a ``FakeAlign``."""

    def _make(base: str, records: dict[str, dict[str, Any]]) -> FakeAlign:
        fake = FakeAlign(base, records)
        fake.install(monkeypatch)
        return fake

    return _make
