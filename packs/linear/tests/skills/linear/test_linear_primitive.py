"""TDD stubs for the linear primitive script.

T2 invariants:
  - MAX_PAGES=5: _get_project_pages stops after 5 pages regardless of hasNextPage.
  - Retry-After: on HTTP 429, the client reads Retry-After, sleeps, and retries once.

The module is loaded via importlib so it does not need to be installed as a
package. credbroker is stubbed before exec to prevent import-time failures.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

httpx = pytest.importorskip("httpx")

PACK_ROOT = Path(__file__).resolve().parents[3]
LINEAR_SCRIPT = (
    PACK_ROOT
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

        monkeypatch.setattr(linear_mod, "_bounded_post", _mock_post)

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
                return _rate_limit_response(retry_after=30)
            return _page_response("proj-uuid", has_next=False)

        monkeypatch.setattr(linear_mod, "_bounded_post", _mock_post)
        monkeypatch.setattr(linear_mod.time, "sleep", lambda s: sleep_args.append(float(s)))

        result = linear_mod._get_project_pages("fake-key", "proj-uuid")

        assert len(post_calls) == 2, (
            f"Expected 2 HTTP calls (initial + 1 retry after 429); got {len(post_calls)}"
        )
        assert sleep_args == [1.0], (
            f"Expected profile-clamped time.sleep(1); got {sleep_args}"
        )
        assert result["id"] == "proj-uuid"


class TestIntakeAcquisitionContract:
    """The sibling read primitive preserves strict, bounded intake provenance."""

    def test_queries_request_comparable_revision(self, linear_mod: types.ModuleType) -> None:
        assert "updatedAt" in linear_mod._GET_ISSUE_QUERY
        assert "updatedAt" in linear_mod._GET_PROJECT_QUERY

    def test_retry_constants_match_profile(self, linear_mod: types.ModuleType) -> None:
        profile_path = (
            Path(__file__).resolve().parents[3]
            / ".apm/skills/linear-brief-intake/references/intake-profile.json"
        )
        budget = json.loads(profile_path.read_text(encoding="utf-8"))["budget"]
        assert budget["max_retries"] == linear_mod.MAX_RETRIES
        assert list(linear_mod.RETRY_BACKOFF_SECONDS) == budget["backoff_seconds"]

    def test_response_byte_budget_fails_closed(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        oversized = httpx.Response(200, content=b"x" * (linear_mod.MAX_RESPONSE_BYTES + 1))
        monkeypatch.setattr(linear_mod, "_bounded_post", lambda *args, **kwargs: oversized)

        with pytest.raises(SystemExit) as exc_info:
            linear_mod._graphql_request("opaque-key", "{ viewer { id } }")

        assert exc_info.value.code == linear_mod.EXIT_ERROR

    def test_response_byte_budget_stops_streaming_at_cap(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        chunks_read = 0

        class ChunkStream(httpx.SyncByteStream):
            def __iter__(self):
                nonlocal chunks_read
                chunks_read += 1
                yield b"x" * linear_mod.MAX_RESPONSE_BYTES
                chunks_read += 1
                yield b"y"
                raise AssertionError("reader continued after crossing the byte cap")

        response = httpx.Response(
            200,
            stream=ChunkStream(),
            request=httpx.Request("POST", linear_mod.GRAPHQL_URL),
        )

        class ResponseContext:
            def __enter__(self):
                return response

            def __exit__(self, *_args: object) -> None:
                response.close()

        monkeypatch.setattr(
            linear_mod.httpx, "stream", lambda *args, **kwargs: ResponseContext()
        )
        with pytest.raises(SystemExit) as exc_info:
            linear_mod._bounded_post(
                linear_mod.GRAPHQL_URL,
                json_body={"query": "{}"},
                headers={},
                timeout=1,
            )

        assert exc_info.value.code == linear_mod.EXIT_ERROR
        assert chunks_read == 2

    def test_non_standard_json_fails_closed(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        invalid = httpx.Response(
            200,
            content=json.dumps({"data": {"value": None}}).replace("null", "NaN").encode(),
        )
        monkeypatch.setattr(linear_mod, "_bounded_post", lambda *args, **kwargs: invalid)

        with pytest.raises(SystemExit) as exc_info:
            linear_mod._graphql_request("opaque-key", "{ viewer { id } }")

        assert exc_info.value.code == linear_mod.EXIT_ERROR

    def test_project_marks_max_page_truncation_incomplete(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            linear_mod,
            "_bounded_post",
            lambda *args, **kwargs: _page_response("proj-uuid", has_next=True),
        )

        result = linear_mod._get_project_pages("opaque-key", "proj-uuid")

        assert result["intake_budget"] == {"complete": False, "result": "marked-incomplete"}
