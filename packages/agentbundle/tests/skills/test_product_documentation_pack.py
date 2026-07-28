"""T14: deterministic validators for the product-documentation pack.

Verifies the structural and behavioural invariants that cannot be caught
by reading the skill at inference time:

- AC1  (spec): author-product-docs SKILL.md exists at the expected source path.
- AC2  (spec): the compat pack (user-guide-diataxis) declares product-documentation
              as a required dependency in its pack.toml; new-guide shim routes
              to author-product-docs.
- AC4  (spec): skill body explicitly states portability ("This skill is portable")
              and anti-patterns section forbids writing to docs/guides/ for
              external product users.
- AC6  (spec): no seeds/ directory under packs/product-documentation/
              (four-quadrant scaffold removed).
- AC25 (spec): skill names are distinct — new-guide vs author-product-docs —
              so a simultaneous install produces no file-level collision.
- AC26 (spec): allowed-scopes = ["repo", "user"].
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
PRODUCT_DOC_PACK = REPO_ROOT / "packs" / "product-documentation"
COMPAT_PACK = REPO_ROOT / "packs" / "user-guide-diataxis"
AUTHOR_SKILL = PRODUCT_DOC_PACK / ".apm" / "skills" / "author-product-docs" / "SKILL.md"
NEW_GUIDE_SHIM = COMPAT_PACK / ".apm" / "skills" / "new-guide" / "SKILL.md"


@pytest.fixture(scope="module")
def author_skill_body() -> str:
    assert AUTHOR_SKILL.exists(), f"author-product-docs SKILL.md not found at {AUTHOR_SKILL}"
    return AUTHOR_SKILL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def new_guide_shim_body() -> str:
    assert NEW_GUIDE_SHIM.exists(), f"new-guide SKILL.md shim not found at {NEW_GUIDE_SHIM}"
    return NEW_GUIDE_SHIM.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def compat_pack_toml() -> dict:
    path = COMPAT_PACK / "pack.toml"
    assert path.exists(), f"user-guide-diataxis pack.toml not found at {path}"
    return tomllib.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def product_pack_toml() -> dict:
    path = PRODUCT_DOC_PACK / "pack.toml"
    assert path.exists(), f"product-documentation pack.toml not found at {path}"
    return tomllib.loads(path.read_text(encoding="utf-8"))


# ── AC1: SKILL.md exists ──────────────────────────────────────────────────────


def test_author_product_docs_skill_exists():
    """AC1: author-product-docs SKILL.md must exist at the expected source path."""
    assert AUTHOR_SKILL.exists(), (
        f"author-product-docs SKILL.md not found at {AUTHOR_SKILL}; "
        "the skill must be authored before the pack can ship."
    )


# ── AC6: no seeds/ directory ──────────────────────────────────────────────────


def test_product_documentation_has_no_seeds_dir():
    """AC6: packs/product-documentation/ must not contain a seeds/ directory.

    The four-quadrant scaffold (tutorials/, how-to/, reference/, explanation/)
    was the central anti-pattern of user-guide-diataxis.  product-documentation
    treats Diátaxis as a page contract, not a mandatory directory structure.
    A seeds/ dir would re-impose the scaffold on every new install.
    """
    seeds_dir = PRODUCT_DOC_PACK / "seeds"
    assert not seeds_dir.exists(), (
        f"packs/product-documentation/seeds/ must not exist; "
        f"found {seeds_dir}.  Remove it — the four-quadrant scaffold is "
        f"explicitly rejected by the spec (AC6)."
    )


# ── AC2: compat pack declares dependency ─────────────────────────────────────


def test_compat_pack_depends_on_product_documentation(compat_pack_toml):
    """AC2: user-guide-diataxis pack.toml must declare product-documentation
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


# ── AC2: new-guide shim routes to author-product-docs ────────────────────────


def test_new_guide_shim_references_author_product_docs(new_guide_shim_body):
    """AC2: the new-guide SKILL.md body must name author-product-docs
    so the LLM reading the shim can route the request correctly.
    """
    assert "author-product-docs" in new_guide_shim_body, (
        "new-guide SKILL.md shim does not reference 'author-product-docs'; "
        "the shim must name the replacement skill so the LLM can route."
    )


# ── AC25: distinct skill names → no install collision ────────────────────────


def test_skill_names_are_distinct():
    """AC25: new-guide and author-product-docs use different skill dir names,
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


# ── AC4: portability clause ───────────────────────────────────────────────────


def test_author_skill_declares_portability(author_skill_body):
    """AC4: the skill body must state that it is portable (does not hardcode
    this catalogue's specific paths).
    """
    assert "This skill is portable" in author_skill_body, (
        "author-product-docs SKILL.md is missing the portability declaration "
        "('This skill is portable').  Adopters reading the skill must know "
        "they should inspect their own repo layout rather than assuming "
        "this catalogue's guides/<pack>/ structure."
    )


# ── AC4: anti-pattern guards external docs/guides/ misrouting ────────────────


def test_author_skill_anti_pattern_forbids_docs_guides_for_external(author_skill_body):
    """AC4: the anti-patterns section must explicitly forbid writing external
    product documentation to docs/guides/.

    Background: docs/guides/ is the internal maintainer tree; external
    catalogue-facing guides live in guides/.  The skill body must name this
    distinction so the LLM doesn't silently misroute a pack guide into the
    internal tree.
    """
    lower = author_skill_body.lower()
    start = lower.find("anti-pattern")
    assert start >= 0, "author-product-docs SKILL.md is missing an Anti-patterns section"
    section = lower[start:]
    assert "docs/guides/" in section, (
        "The Anti-patterns section does not mention 'docs/guides/'; "
        "it must explicitly call out the misrouting risk (writing external "
        "product docs to the internal tree)."
    )
    assert "external product user" in section or "external" in section, (
        "The Anti-patterns section must name the external-user / internal-maintainer "
        "distinction when forbidding docs/guides/ for product guides."
    )


# ── AC26: allowed-scopes = ["repo", "user"] ──────────────────────────────────


def test_product_documentation_allowed_scopes(product_pack_toml):
    """AC26: product-documentation must declare allowed-scopes = ["repo", "user"]
    so the skill can be installed at user scope for cross-project use.
    """
    install = product_pack_toml.get("pack", {}).get("install", {})
    assert install.get("allowed-scopes") == ["repo", "user"], (
        f"product-documentation [pack.install] allowed-scopes must be "
        f'["repo", "user"]; got {install.get("allowed-scopes")!r}'
    )
