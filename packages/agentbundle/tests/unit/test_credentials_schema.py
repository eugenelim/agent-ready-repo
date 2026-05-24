"""T7: ``creds-schema.toml`` parser + canonical-path resolver
(skill-secrets spec § AC24, AC24b).
"""

from __future__ import annotations

import pathlib
from types import SimpleNamespace

import pytest

from agentbundle.creds.exceptions import SchemaError
from agentbundle.creds.loader import (
    CredsSchema,
    KeyDef,
    _parse_schema,
    _relative_schema_path,
)


def _write(tmp_path: pathlib.Path, content: str) -> pathlib.Path:
    target = tmp_path / "creds-schema.toml"
    target.write_text(content, encoding="utf-8")
    return target


def test_parse_valid_schema(tmp_path):
    """AC24: a well-formed schema parses into ``CredsSchema`` with the
    expected ``namespace`` and ``KeyDef`` entries."""
    path = _write(tmp_path, """
        [namespace]
        name = "jira"

        [[namespace.keys]]
        name = "API_TOKEN"
        label = "Jira API token"
        secret = true

        [[namespace.keys]]
        name = "BASE_URL"
        label = "Jira instance base URL"
        secret = false
    """)
    schema = _parse_schema(path)
    assert isinstance(schema, CredsSchema)
    assert schema.namespace == "jira"
    assert len(schema.keys) == 2
    assert schema.keys[0] == KeyDef(name="API_TOKEN", label="Jira API token", secret=True)
    assert schema.keys[1] == KeyDef(name="BASE_URL", label="Jira instance base URL", secret=False)


def test_credentials_schema_is_immutable():
    """``CredsSchema`` and ``KeyDef`` are frozen dataclasses."""
    schema = CredsSchema(namespace="x", keys=(KeyDef("A", "lbl", True),))
    with pytest.raises(dataclasses_FrozenInstanceError := __import__("dataclasses").FrozenInstanceError):
        schema.namespace = "y"  # type: ignore[misc]
    with pytest.raises(dataclasses_FrozenInstanceError):
        schema.keys[0].name = "B"  # type: ignore[misc]


def test_parse_missing_namespace_table_raises(tmp_path):
    """``SchemaError`` names the file path."""
    path = _write(tmp_path, "")
    with pytest.raises(SchemaError, match="missing \\[namespace\\]"):
        _parse_schema(path)


def test_parse_missing_namespace_name_raises(tmp_path):
    path = _write(tmp_path, "[namespace]\n")
    with pytest.raises(SchemaError, match="namespace.name"):
        _parse_schema(path)


def test_parse_empty_keys_list_raises(tmp_path):
    path = _write(tmp_path, """
        [namespace]
        name = "x"
        keys = []
    """)
    with pytest.raises(SchemaError, match="declare at least one key"):
        _parse_schema(path)


def test_parse_missing_keys_table_raises(tmp_path):
    path = _write(tmp_path, """
        [namespace]
        name = "x"
    """)
    with pytest.raises(SchemaError, match="declare at least one key"):
        _parse_schema(path)


def test_parse_non_boolean_secret_raises(tmp_path):
    path = _write(tmp_path, """
        [namespace]
        name = "x"
        [[namespace.keys]]
        name = "A"
        label = "A label"
        secret = "yes"
    """)
    with pytest.raises(SchemaError, match="secret must be boolean"):
        _parse_schema(path)


def test_parse_missing_label_raises(tmp_path):
    path = _write(tmp_path, """
        [namespace]
        name = "x"
        [[namespace.keys]]
        name = "A"
        secret = true
    """)
    with pytest.raises(SchemaError, match="label"):
        _parse_schema(path)


def test_parse_missing_name_raises(tmp_path):
    path = _write(tmp_path, """
        [namespace]
        name = "x"
        [[namespace.keys]]
        label = "lbl"
        secret = true
    """)
    with pytest.raises(SchemaError, match=r"keys\[0\]\.name"):
        _parse_schema(path)


def test_parse_malformed_toml_raises(tmp_path):
    path = _write(tmp_path, "this is not = valid toml [[")
    with pytest.raises(SchemaError, match="malformed"):
        _parse_schema(path)


def test_parse_missing_file_raises(tmp_path):
    path = tmp_path / "does-not-exist.toml"
    with pytest.raises(SchemaError, match="not found"):
        _parse_schema(path)


# ── Canonical-path resolution (AC24b) ──────────────────────────────────


def test__relative_schema_path_locates_skill_md_and_joins_references():
    """AC24b: ``_relative_schema_path`` walks ``state.packs[pack].files``
    for ``.claude/skills/<name>/SKILL.md``, takes the parent directory,
    and joins ``references/creds-schema.toml``."""
    pack_state = SimpleNamespace(files={
        ".claude/skills/jira/SKILL.md": {"sha": "deadbeef"},
        ".claude/skills/jira/scripts/cli.py": {"sha": "cafef00d"},
        ".claude/skills/example/SKILL.md": {"sha": "00000000"},
    })
    state = SimpleNamespace(packs={"core": pack_state})
    resolved = _relative_schema_path(state, "core", "jira")
    assert str(resolved) == ".claude/skills/jira/references/creds-schema.toml"


def test__relative_schema_path_disambiguates_by_skill_name():
    """Two skills under the same pack — the resolver picks the right one."""
    pack_state = SimpleNamespace(files={
        ".claude/skills/jira/SKILL.md": {"sha": "a"},
        ".claude/skills/github/SKILL.md": {"sha": "b"},
    })
    state = SimpleNamespace(packs={"core": pack_state})
    assert str(_relative_schema_path(state, "core", "jira")) == \
        ".claude/skills/jira/references/creds-schema.toml"
    assert str(_relative_schema_path(state, "core", "github")) == \
        ".claude/skills/github/references/creds-schema.toml"


def test__relative_schema_path_missing_skill_raises():
    """AC24b: a missing SKILL.md row raises ``SchemaError`` naming the
    offending pack + skill so the message is actionable."""
    pack_state = SimpleNamespace(files={
        ".claude/skills/jira/SKILL.md": {"sha": "a"},
    })
    state = SimpleNamespace(packs={"core": pack_state})
    with pytest.raises(SchemaError, match="not found at expected path"):
        _relative_schema_path(state, "core", "absent-skill")


def test__relative_schema_path_missing_pack_raises():
    state = SimpleNamespace(packs={})
    with pytest.raises(SchemaError, match="pack 'core' not present"):
        _relative_schema_path(state, "core", "jira")


def test__relative_schema_path_ignores_non_skill_md_entries():
    """The regex must match exactly ``.claude/skills/<name>/SKILL.md`` —
    nested or differently-named files are skipped."""
    pack_state = SimpleNamespace(files={
        ".claude/skills/jira/scripts/cli.py": {"sha": "a"},
        ".claude/agents/foo.md": {"sha": "b"},
        ".claude/skills/jira/SKILL.md": {"sha": "c"},  # the right one
    })
    state = SimpleNamespace(packs={"core": pack_state})
    assert ".claude/skills/jira" in str(_relative_schema_path(state, "core", "jira"))


# ── ``load_credentials(schema_path=...)`` kwarg (T3 + T7) ──────────────


def test_load_credentials_accepts_schema_path_kwarg(tmp_path, monkeypatch):
    """Primitive authors can pass ``schema_path`` for their own schema
    file — verified by signature inspection (the resolver-vs-passthrough
    logic is exercised by the CLI in T8)."""
    import inspect

    from agentbundle.creds.loader import load_credentials
    sig = inspect.signature(load_credentials)
    assert "schema_path" in sig.parameters
    param = sig.parameters["schema_path"]
    # Keyword-only per AC3.
    assert param.kind == inspect.Parameter.KEYWORD_ONLY
    assert param.default is None
