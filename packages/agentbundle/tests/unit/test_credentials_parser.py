"""T2: stdlib ``.env`` parser — construction tests (skill-secrets spec § AC2)."""

from __future__ import annotations

import pathlib

import pytest

from agentbundle.creds.loader import EnvParseError, parse_env_file


def _write(tmp_path: pathlib.Path, content: str) -> pathlib.Path:
    target = tmp_path / "credentials.env"
    target.write_text(content, encoding="utf-8", newline="")
    return target


def test_parses_unquoted_key_value(tmp_path):
    path = _write(tmp_path, "KEY=value\n")
    assert parse_env_file(path) == {"KEY": "value"}


def test_parses_quoted_value_with_spaces(tmp_path):
    path = _write(tmp_path, 'KEY="value with spaces"\n')
    assert parse_env_file(path) == {"KEY": "value with spaces"}


def test_strips_trailing_cr_on_crlf_line(tmp_path):
    path = _write(tmp_path, "KEY=value\r\n")
    assert parse_env_file(path) == {"KEY": "value"}


def test_preserves_cr_inside_quoted_value(tmp_path):
    # AC2 carve-out: \r inside a quoted value is preserved; only the
    # trailing line terminator is stripped.
    path = _write(tmp_path, 'KEY="a\rb"\n')
    assert parse_env_file(path) == {"KEY": "a\rb"}


def test_ignores_comments_and_blank_lines(tmp_path):
    path = _write(
        tmp_path,
        "# comment line\n\nKEY=value\n\n# trailing comment\n",
    )
    assert parse_env_file(path) == {"KEY": "value"}


def test_refuses_export_prefix(tmp_path):
    path = _write(tmp_path, "export KEY=value\n")
    with pytest.raises(EnvParseError, match="export"):
        parse_env_file(path)


def test_refuses_variable_expansion(tmp_path):
    path = _write(tmp_path, "KEY=$OTHER\n")
    with pytest.raises(EnvParseError, match="variable expansion"):
        parse_env_file(path)


def test_refuses_multi_line_quoted_value(tmp_path):
    path = _write(tmp_path, 'KEY="line1\nline2"\n')
    with pytest.raises(EnvParseError, match="multi-line"):
        parse_env_file(path)


def test_accepts_value_with_equals(tmp_path):
    path = _write(tmp_path, "KEY=value=with=equals\n")
    assert parse_env_file(path) == {"KEY": "value=with=equals"}
