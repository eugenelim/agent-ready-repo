"""enriched-pack-manifest T6: soft `categories` vocabulary in `validate`.

`categories` is a *soft* vocabulary (RFC-0031 D3): an unknown slug produces
a warning on stderr and exit 0; a known slug is silent. The schema owns the
shape (array of ≤5 strings); this rail only nudges taxonomy consistency.
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path
from unittest import mock

from agentbundle.categories import DEFAULT_CATEGORIES


def _write_pack(tmp_path: Path, categories_line: str) -> Path:
    pack = tmp_path / "pack"
    pack.mkdir()
    (pack / "pack.toml").write_text(
        '[pack]\n'
        'name = "demo"\n'
        'version = "0.1.0"\n'
        'description = "Demo pack."\n'
        f"{categories_line}\n",
        encoding="utf-8",
    )
    return pack


def _run(pack_path: Path):
    from agentbundle.commands import validate as validate_mod

    ns = argparse.Namespace(pack_path=str(pack_path), strict=False)
    captured = io.StringIO()
    with mock.patch("sys.stderr", captured):
        rc = validate_mod.run(ns)
    return rc, captured.getvalue()


def test_known_slug_is_silent_exit_0(tmp_path):
    pack = _write_pack(tmp_path, 'categories = ["research", "documentation"]')
    rc, stderr = _run(pack)
    assert rc == 0, stderr
    assert "warning" not in stderr.lower(), f"unexpected warning: {stderr!r}"


def test_unknown_slug_warns_exit_0(tmp_path):
    pack = _write_pack(tmp_path, 'categories = ["research", "made-up-slug"]')
    rc, stderr = _run(pack)
    assert rc == 0, f"unknown category must not fail validate; got {rc}"
    assert "warning" in stderr.lower()
    # The warning names the unknown slug in its flagged-list. (The message
    # also echoes the full default vocabulary for context, so we don't assert
    # on the *absence* of any known slug.)
    assert "made-up-slug" in stderr


def test_no_categories_is_silent_exit_0(tmp_path):
    pack = _write_pack(tmp_path, "")
    rc, stderr = _run(pack)
    assert rc == 0, stderr
    assert "warning" not in stderr.lower()


def test_default_vocabulary_has_the_sixteen_rfc_0031_slugs():
    expected = {
        "code-review",
        "testing",
        "documentation",
        "architecture",
        "security",
        "research",
        "product-management",
        "project-management",
        "integrations",
        "file-conversion",
        "api-design",
        "governance",
        "credentials",
        "devops",
        "data",
        "ai-agent",
    }
    assert set(DEFAULT_CATEGORIES) == expected
    assert len(DEFAULT_CATEGORIES) == 16
