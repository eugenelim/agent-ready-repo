"""Tests for _StdioLoop — frame-size cap, JSON robustness, initialize handshake, stdin-close exit."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_MODULE = Path(__file__).resolve().parents[1] / "agentbundle" / "workspace_mcp.py"


class TestFrameSizeCap:
    """Frames exceeding 1 MiB are quarantined; server continues (AC16a)."""

    def test_oversized_frame_discarded_and_error_returned(self) -> None:
        assert False  # STUB: AC16a — send 1 MiB + 1 byte line; assert error response code -32600

    def test_subsequent_frame_processed_after_oversized_quarantine(self) -> None:
        assert False  # STUB: AC16a — oversized frame followed by valid frame; valid frame handled


class TestMalformedJSON:
    """Malformed JSON is discarded with -32700 error (AC16b)."""

    def test_malformed_json_returns_parse_error(self) -> None:
        assert False  # STUB: AC16b — send "{bad json"; assert error code -32700

    def test_valid_frame_after_malformed_is_processed(self) -> None:
        assert False  # STUB: AC16b — malformed followed by valid initialize; valid handled


class TestUnknownRequestId:
    """Unknown request_id on elicitation/create response is discarded (AC16c)."""

    def test_unknown_request_id_discarded(self) -> None:
        assert False  # STUB: AC16c — send result with id not in request_map; no exception raised


class TestInitializeHandshake:
    """initialize → initialized → tools/list sequence produces correct capability shape (AC1)."""

    def test_initialize_response_contains_tools_key(self) -> None:
        assert False  # STUB: AC1 — send initialize; assert result["tools"] is a list

    def test_tools_list_includes_workspace_status(self) -> None:
        assert False  # STUB: AC1 — tools/list response contains workspace_status

    def test_tools_list_includes_elicit(self) -> None:
        assert False  # STUB: AC1 — tools/list response contains elicit

    def test_server_capabilities_has_no_elicitation(self) -> None:
        assert False  # STUB: AC13 — ServerCapabilities never includes "elicitation"


class TestStdinClose:
    """Stdin close → process exit within 5 s (AC22)."""

    def test_process_exits_within_5s_on_stdin_close(self) -> None:
        assert False  # STUB: AC22 — launch workspace_mcp.py as subprocess; close stdin; assert exits within 5 s


class TestModuleEntryPoint:
    """python3 -m agentbundle.workspace_mcp --help exits 0 (AC1)."""

    def test_help_flag_exits_zero(self) -> None:
        r = subprocess.run(
            [sys.executable, "-m", "agentbundle.workspace_mcp", "--help"],
            capture_output=True, encoding="utf-8",
            cwd=str(Path(__file__).resolve().parents[1]),
        )
        assert r.returncode == 0
