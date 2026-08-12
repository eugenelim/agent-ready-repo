"""Pack-local contracts for product-documentation."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[2]
AUTHOR_SKILL = PACK_ROOT / ".apm" / "skills" / "author-product-docs" / "SKILL.md"


@pytest.fixture(scope="module")
def author_skill_body() -> str:
    assert AUTHOR_SKILL.is_file(), f"author-product-docs skill not found at {AUTHOR_SKILL}"
    return AUTHOR_SKILL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pack_toml() -> dict:
    return tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))


def test_author_product_docs_skill_exists() -> None:
    assert AUTHOR_SKILL.is_file()


def test_product_documentation_has_no_seeds_dir() -> None:
    assert not (PACK_ROOT / "seeds").exists()


def test_author_skill_declares_portability(author_skill_body: str) -> None:
    assert "This skill is portable" in author_skill_body


def test_author_skill_anti_pattern_forbids_docs_guides_for_external(
    author_skill_body: str,
) -> None:
    lower = author_skill_body.lower()
    start = lower.find("anti-pattern")
    assert start >= 0, "author-product-docs SKILL.md is missing an Anti-patterns section"
    section = lower[start:]
    assert "docs/guides/" in section
    assert "external" in section


def test_product_documentation_allowed_scopes(pack_toml: dict) -> None:
    install = pack_toml.get("pack", {}).get("install", {})
    assert install.get("allowed-scopes") == ["repo", "user"]
