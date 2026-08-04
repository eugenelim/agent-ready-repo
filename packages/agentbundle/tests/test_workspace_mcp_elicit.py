"""Tests for _ElicitTool — elicitation/create path and response-file fallback."""
from __future__ import annotations

import pytest


class TestElicitViaMCP:
    """elicitation/create path: server sends request, blocks, resolves when client responds (AC11)."""

    def test_elicit_sends_elicitation_create_to_client(self) -> None:
        pytest.skip('STUB: AC11 — call elicit(); capture outgoing message; assert method="elicitation/create"')

    def test_elicit_resolves_when_response_delivered(self) -> None:
        pytest.skip("STUB: AC11 — simulate client response on request_map; assert elicit() returns")

    def test_elicit_cancelled_on_shutdown(self) -> None:
        pytest.skip("STUB: AC11 — set shutdown_event; assert elicit() returns error within 2 s")


class TestElicitResponseFile:
    """Response-file fallback: O_EXCL creation, polling, 300s timeout (AC12)."""

    def test_response_file_created_with_0600_mode(self) -> None:
        pytest.skip("STUB: AC12 — call elicit() (no-elicitation mode); response file created with mode 0600")

    def test_response_file_polled_until_control_plane_responds(self) -> None:
        pytest.skip('STUB: AC12 — write {"response": "yes"} to file within 1 s; assert elicit() returns')

    def test_elicit_timeout_returns_error_after_300s(self) -> None:
        pytest.skip("STUB: AC12 — patch time.monotonic to fast-forward; assert timeout error returned")

    def test_preexisting_response_file_returns_error(self) -> None:
        pytest.skip("STUB: AC12 — pre-create the file; assert O_EXCL raises and error returned")

    def test_tmp_dir_created_with_0700_mode(self) -> None:
        pytest.skip("STUB: AC12 — setup_response_dir(); assert tmp dir mode == 0o700")

    def test_cleanup_removes_tmp_dir(self) -> None:
        pytest.skip("STUB: AC12 — cleanup() removes the directory")


class TestElicitCapabilityNegotiation:
    """elicitation capability is never advertised in ServerCapabilities (AC13)."""

    def test_initialize_response_has_no_elicitation_capability(self) -> None:
        pytest.skip('STUB: AC13 — parse initialize response "capabilities"; assert "elicitation" absent')
