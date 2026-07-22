"""TDD stubs for the linear primitive script.

Spec: docs/specs/m5-linear-brief-intake-and-sync/spec.md
T2 invariants:
  - MAX_PAGES=5: _get_project_pages stops after 5 pages regardless of hasNextPage.
  - Retry-After: on HTTP 429, the client reads Retry-After, sleeps, and retries once.

The module is loaded via importlib so it does not need to be installed as a
package. credbroker is stubbed before exec to prevent import-time failures.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
LINEAR_SCRIPT = (
    REPO_ROOT
    / "packs"
    / "linear"
    / ".apm"
    / "skills"
    / "linear"
    / "scripts"
    / "linear.py"
)


@pytest.fixture(scope="module")
def linear_mod() -> types.ModuleType:
    """Load linear.py once per session; stub credbroker to avoid import-time auth."""
    credbroker_stub = types.ModuleType("credbroker")
    credbroker_stub.CredentialsMissingError = Exception  # type: ignore[attr-defined]
    credbroker_stub.load_credentials = lambda *a, **kw: None  # type: ignore[attr-defined]
    sys.modules.setdefault("credbroker", credbroker_stub)

    spec = importlib.util.spec_from_file_location("linear_script", LINEAR_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _page_response(project_id: str, *, has_next: bool, cursor: str = "cur-1") -> httpx.Response:
    """200 response with one issue per page."""
    body = {
        "data": {
            "project": {
                "id": project_id,
                "name": "Test Project",
                "issues": {
                    "nodes": [{"identifier": "ENG-1", "title": "Issue", "description": ""}],
                    "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
                },
            }
        }
    }
    return httpx.Response(200, json=body)


def _rate_limit_response(retry_after: int = 1) -> httpx.Response:
    return httpx.Response(429, headers={"Retry-After": str(retry_after)}, text="rate limited")


# ---------------------------------------------------------------------------
# T2a: pagination bound
# ---------------------------------------------------------------------------

class TestGetProjectMaxPages:
    """MAX_PAGES=5: the function stops after 5 pages even when hasNextPage is always True."""

    def test_get_project_stops_at_max_pages(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        post_calls: list[int] = []

        def _mock_post(url: str, **kwargs: object) -> httpx.Response:
            post_calls.append(1)
            return _page_response("proj-uuid", has_next=True, cursor=f"cur-{len(post_calls)}")

        monkeypatch.setattr(linear_mod.httpx, "post", _mock_post)

        result = linear_mod._get_project_pages("fake-key", "proj-uuid")

        assert len(post_calls) == linear_mod.MAX_PAGES, (
            f"Expected exactly MAX_PAGES={linear_mod.MAX_PAGES} HTTP calls; got {len(post_calls)}"
        )
        # 1 issue per page × 5 pages
        assert len(result["issues"]["nodes"]) == linear_mod.MAX_PAGES


# ---------------------------------------------------------------------------
# T2b: Retry-After handling
# ---------------------------------------------------------------------------

class TestRetryAfterOn429:
    """On HTTP 429 with Retry-After, the client sleeps and makes exactly one retry."""

    def test_get_project_respects_retry_after_on_429(
        self,
        linear_mod: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        post_calls: list[int] = []
        sleep_args: list[float] = []

        def _mock_post(url: str, **kwargs: object) -> httpx.Response:
            post_calls.append(1)
            if len(post_calls) == 1:
                return _rate_limit_response(retry_after=1)
            return _page_response("proj-uuid", has_next=False)

        monkeypatch.setattr(linear_mod.httpx, "post", _mock_post)
        monkeypatch.setattr(linear_mod.time, "sleep", lambda s: sleep_args.append(float(s)))

        result = linear_mod._get_project_pages("fake-key", "proj-uuid")

        assert len(post_calls) == 2, (
            f"Expected 2 HTTP calls (initial + 1 retry after 429); got {len(post_calls)}"
        )
        assert sleep_args == [1.0], (
            f"Expected time.sleep(1) from Retry-After: 1 header; got {sleep_args}"
        )
        assert result["id"] == "proj-uuid"
