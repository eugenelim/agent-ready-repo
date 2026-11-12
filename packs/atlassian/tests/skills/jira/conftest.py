"""Resolve the jira skill's runtime tree for the tests that exercise it.

Tests live outside the runtime payload (ADR-0071); the modules they exercise
live under `.apm/`. Nothing in this directory is projected into an installed
environment.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pytest

SKILL = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "jira"
SCRIPTS = SKILL / "scripts"
if not SCRIPTS.is_dir():                      # wrong parents[] depth after a move
    raise SystemExit(f"skill scripts dir not found at {SCRIPTS}")
sys.path.insert(0, str(SCRIPTS))


# --- recording fake Jira transport (preserve-first write tests) -------------------------

@dataclass
class Recorded:
    """One request the fake saw."""

    method: str
    url: str
    path: str
    query: str
    body: Any
    headers: dict[str, str]


class FakeJira:
    """A recording fake transport for one Jira instance; ``issues`` maps key to fields."""

    def __init__(self, base: str, flavor: str, issues: dict[str, dict[str, Any]]) -> None:
        self.base = base
        self.flavor = flavor
        self.api = "/rest/api/3" if flavor == "cloud" else "/rest/api/2"
        self.issues = issues
        self.requests: list[Recorded] = []
        # Return a response to take over a request; return None to fall through.
        self.override: Callable[[Recorded], httpx.Response | None] | None = None
        # Called with each non-GET request just before it is answered.
        self.on_write: Callable[[Recorded], None] | None = None

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
        return self._route(rec, request)

    def _route(self, rec: Recorded, request: httpx.Request) -> httpx.Response:
        parts = rec.path.removeprefix(self.api).strip("/").split("/")
        if rec.path == f"{self.api}/myself":
            return httpx.Response(200, json={"displayName": "Tester"})
        if parts[0] == "issue" and len(parts) == 2:
            key = parts[1]
            if key not in self.issues:
                return httpx.Response(404, json={"errorMessages": ["not found"]})
            if rec.method == "GET":
                names = request.url.params.get("fields", "").split(",")
                return httpx.Response(
                    200,
                    json={"key": key, "fields": {n: self.issues[key].get(n) for n in names if n}},
                )
            if rec.method == "PUT":
                self.issues[key].update((rec.body or {}).get("fields", {}))
                return httpx.Response(204)
            if rec.method == "DELETE":
                return httpx.Response(204)
        if parts == ["issue"] and rec.method == "POST":
            return httpx.Response(201, json={"key": "PROJ-99"})
        if len(parts) == 3 and parts[0] == "issue":
            if parts[2] == "transitions":
                if rec.method == "GET":
                    found = {"transitions": [{"id": "31", "name": "Done"}]}
                    return httpx.Response(200, json=found)
                return httpx.Response(204)
            if parts[2] == "comment" and rec.method == "POST":
                return httpx.Response(201, json={"id": "10000"})
            if parts[2] == "attachments" and rec.method == "POST":
                return httpx.Response(200, json=[{"id": "1"}])
        if parts == ["search", "jql"] and rec.method == "POST":
            return httpx.Response(200, json={"issues": [{"key": "PROJ-1"}], "isLast": True})
        return httpx.Response(404, json={"errorMessages": ["unrouted"]})

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
def make_fake_jira(monkeypatch):
    """Build and install a ``FakeJira``."""

    def _make(base: str, flavor: str, issues: dict[str, dict[str, Any]]) -> FakeJira:
        fake = FakeJira(base, flavor, issues)
        fake.install(monkeypatch)
        return fake

    return _make
