"""Unit tests for `commands/_common.confirm_or_refuse` (CLI-hygiene AC17).

The shared confirm/refuse/--yes helper that `uninstall`, `install --force`, the
`install`→`upgrade` offer, and `upgrade` all call. Pins the four-way decision:
yes → proceed (no stdin); non-TTY → refuse; TTY accept → proceed; TTY decline /
EOF → abort.
"""

from __future__ import annotations

import pytest

from agentbundle.commands._common import confirm_or_refuse


def test_yes_proceeds_without_touching_stdin(monkeypatch):
    def _boom(prompt=""):
        raise AssertionError("input() must not be called with yes=True")

    monkeypatch.setattr("builtins.input", _boom)
    # isatty must not even be consulted under --yes, but patch it defensively.
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    assert confirm_or_refuse(
        yes=True, question="Q? ", refuse_message="REFUSE", abort_message="ABORT"
    ) is True


def test_non_tty_refuses_and_never_prompts(monkeypatch, capsys):
    def _boom(prompt=""):
        raise AssertionError("input() must not be called on a non-TTY")

    monkeypatch.setattr("builtins.input", _boom)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert confirm_or_refuse(
        yes=False, question="Q? ", refuse_message="REFUSE-LINE", abort_message="ABORT"
    ) is False
    assert "REFUSE-LINE" in capsys.readouterr().err


@pytest.mark.parametrize("reply", ["y", "yes", "YES", "  Yes  ", "  y\n"])
def test_tty_accept_proceeds(monkeypatch, reply):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": reply)
    assert confirm_or_refuse(
        yes=False, question="Q? ", refuse_message="REFUSE", abort_message="ABORT"
    ) is True


@pytest.mark.parametrize("reply", ["n", "no", "", "  ", "anything"])
def test_tty_decline_aborts(monkeypatch, capsys, reply):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": reply)
    assert confirm_or_refuse(
        yes=False, question="Q? ", refuse_message="REFUSE", abort_message="ABORT-LINE"
    ) is False
    assert "ABORT-LINE" in capsys.readouterr().err


def test_tty_eof_treated_as_decline(monkeypatch, capsys):
    def _raise(prompt=""):
        raise EOFError

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _raise)
    assert confirm_or_refuse(
        yes=False, question="Q? ", refuse_message="REFUSE", abort_message="ABORT-LINE"
    ) is False
    assert "ABORT-LINE" in capsys.readouterr().err
