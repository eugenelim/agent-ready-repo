"""Cross-pack compatibility contracts for product-documentation."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

# tests/roster/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCT_DOC_PACK = REPO_ROOT / "packs" / "product-documentation"
COMPAT_PACK = REPO_ROOT / "packs" / "user-guide-diataxis"
NEW_GUIDE_SHIM = COMPAT_PACK / ".apm" / "skills" / "new-guide" / "SKILL.md"


@pytest.fixture(scope="module")
def new_guide_shim_body() -> str:
    assert NEW_GUIDE_SHIM.exists(), f"new-guide SKILL.md shim not found at {NEW_GUIDE_SHIM}"
    return NEW_GUIDE_SHIM.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def compat_pack_toml() -> dict:
    path = COMPAT_PACK / "pack.toml"
    assert path.exists(), f"user-guide-diataxis pack.toml not found at {path}"
    return tomllib.loads(path.read_text(encoding="utf-8"))


# ── Compat pack declares dependency ──────────────────────────────────────────


def test_compat_pack_depends_on_product_documentation(compat_pack_toml):
    """User-guide-diataxis pack.toml must declare product-documentation
    as a required dependency so a plain `agentbundle install --pack
    user-guide-diataxis` still delivers author-product-docs.
    """
    required_deps = compat_pack_toml.get("pack", {}).get("dependencies", {}).get("required", [])
    dep_names = [d.get("pack") for d in required_deps]
    assert "product-documentation" in dep_names, (
        "user-guide-diataxis pack.toml is missing a [[pack.dependencies.required]] "
        "entry with pack = 'product-documentation'.  Without it, existing "
        "user-guide-diataxis installs do not pull in author-product-docs."
    )


# ── New-guide shim routes to author-product-docs ─────────────────────────────


def test_new_guide_shim_references_author_product_docs(new_guide_shim_body):
    """The new-guide SKILL.md body must name author-product-docs
    so the LLM reading the shim can route the request correctly.
    """
    assert "author-product-docs" in new_guide_shim_body, (
        "new-guide SKILL.md shim does not reference 'author-product-docs'; "
        "the shim must name the replacement skill so the LLM can route."
    )


# ── Distinct skill names → no install collision ──────────────────────────────


def test_skill_names_are_distinct():
    """New-guide and author-product-docs use different skill dir names,
    so co-installing both packs does not overwrite either skill at
    .claude/skills/<name>/SKILL.md.
    """
    compat_skill_dir = COMPAT_PACK / ".apm" / "skills"
    product_skill_dir = PRODUCT_DOC_PACK / ".apm" / "skills"
    compat_names = (
        {p.name for p in compat_skill_dir.iterdir() if p.is_dir()}
        if compat_skill_dir.exists() else set()
    )
    product_names = (
        {p.name for p in product_skill_dir.iterdir() if p.is_dir()}
        if product_skill_dir.exists() else set()
    )
    collision = compat_names & product_names
    assert not collision, (
        f"user-guide-diataxis and product-documentation share skill dir name(s): "
        f"{collision}.  A co-install would overwrite one skill with the other."
    )
