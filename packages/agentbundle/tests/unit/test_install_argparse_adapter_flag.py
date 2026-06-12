"""T6 tests for the install CLI `--adapter` flag and helper-derived
`choices=` (RFC-0011 / pack-allowed-adapters AC11, AC12, AC13, AC23).
"""

from __future__ import annotations

import sys

import pytest


def _parse_install(*extra_args: str):
    """Run argparse on an install invocation and return the namespace."""
    from agentbundle.cli import _build_parser

    p = _build_parser()
    argv = ["install", "--pack", "demo", *extra_args, "."]
    return p.parse_args(argv)


def test_shipped_adapters_choices_stable_alphabetic_tuple() -> None:
    from agentbundle.cli import _shipped_adapters_choices

    result = _shipped_adapters_choices()
    # RFC-0022 (kiro-adapter-split) added `kiro-cli` + `kiro-ide` alongside the
    # retained `kiro` alias; RFC-0026 (cursor-full-parity) added `cursor`;
    # RFC-0027 (gemini-full-parity) added `gemini` (sorts after `cursor`, before
    # `kiro`). This CI-only root isn't gated by `make build-check`. Pinning the
    # full shipped set, sorted.
    assert result == (
        "claude-code",
        "codex",
        "copilot",
        "cursor",
        "gemini",
        "kiro",
        "kiro-cli",
        "kiro-ide",
    )


def test_adapter_claude_code_accepted() -> None:
    ns = _parse_install("--scope", "user", "--adapter", "claude-code")
    assert ns.adapter == "claude-code"


def test_adapter_kiro_accepted() -> None:
    ns = _parse_install("--scope", "user", "--adapter", "kiro")
    assert ns.adapter == "kiro"


def test_adapter_codex_accepted() -> None:
    ns = _parse_install("--scope", "user", "--adapter", "codex")
    assert ns.adapter == "codex"


def test_adapter_copilot_accepted_at_argparse() -> None:
    """Argparse admits copilot — handler-side check refuses it for
    user-scope-incapable adapters (covered by T2's resolver tests)."""
    ns = _parse_install("--scope", "user", "--adapter", "copilot")
    assert ns.adapter == "copilot"


def test_adapter_windsurf_rejected_at_argparse(capsys) -> None:
    with pytest.raises(SystemExit):
        _parse_install("--scope", "user", "--adapter", "windsurf")
    captured = capsys.readouterr()
    assert "invalid choice" in captured.err.lower() or "windsurf" in captured.err.lower()


def test_help_text_includes_pinned_wording(capsys) -> None:
    from agentbundle.cli import _build_parser

    p = _build_parser()
    with pytest.raises(SystemExit):
        p.parse_args(["install", "--help"])
    captured = capsys.readouterr()
    # RFC-0012 widens the flag's help text — admitted at both scopes;
    # the user-scope-only wording is gone. Argparse may wrap the text
    # across lines, so use a contiguous substring that survives the
    # default-width wrap.
    assert "Override the auto-detected adapter" in captured.out
    # The legacy "at user scope" pin is gone.
    assert "at user scope" not in captured.out
