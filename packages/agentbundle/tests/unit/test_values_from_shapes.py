"""T7: tests for ``load_values_from`` accepting [markers], [values], or
flat-fallback shapes, and refusing files with both [markers] and [values].

Spec: docs/specs/adapt-to-project/spec.md AC15.
"""

from __future__ import annotations

import pytest

from agentbundle.config import ConfigError, load_values_from


def _write(tmp_path, body: str):
    p = tmp_path / "values.toml"
    p.write_text(body, encoding="utf-8")
    return p


def test_accepts_markers_table(tmp_path):
    p = _write(
        tmp_path,
        '[markers]\nproject-name = "myproj"\nowner = "octocat"\n',
    )
    assert load_values_from(p) == {"project-name": "myproj", "owner": "octocat"}


def test_accepts_values_table(tmp_path):
    p = _write(
        tmp_path,
        '[values]\nPROJECT_NAME = "myproj"\nOWNER = "octocat"\n',
    )
    assert load_values_from(p) == {"PROJECT_NAME": "myproj", "OWNER": "octocat"}


def test_accepts_flat_table_skipping_discovery_keys(tmp_path):
    p = _write(
        tmp_path,
        'discovery-schema-version = "0.1"\n'
        'marker-schema-version = "0.1"\n'
        'project-name = "p"\n',
    )
    # discovery- and marker-schema-version keys are skipped; the
    # remaining flat entry comes through.
    assert load_values_from(p) == {"project-name": "p"}


def test_refuses_files_with_both_markers_and_values(tmp_path):
    p = _write(
        tmp_path,
        '[markers]\nproject-name = "a"\n[values]\nPROJECT_NAME = "b"\n',
    )
    with pytest.raises(ConfigError, match="ambiguous --values-from file"):
        load_values_from(p)


def test_accepts_user_scope_file_yielding_empty(tmp_path):
    # User-scope `.adapt-discovery.toml`: no [markers], no [values],
    # only discovery-schema-version + findings arrays. Should load
    # cleanly as an empty mapping.
    p = _write(
        tmp_path,
        'discovery-schema-version = "0.1"\n'
        '[[findings.accepted]]\n'
        'finding-id = "x/restructure:00000000"\n'
        'kind = "restructure"\n'
        'source-path = "a"\n'
        'destination-path = "b"\n',
    )
    assert load_values_from(p) == {}
