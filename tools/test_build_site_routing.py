"""Tests for guide-routing and /now/ projection in tools/build-site.py.

Covers: shared-chrome contract validation and projection, frontmatter parsing,
guide-metadata stripping, slug-override routing, alias redirect-stub generation,
docs/guides/ exclusion, generation's independence from the marketing
design-token file, and the released-changelog Highlights projection that feeds
the public `/now/` route.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# build-site.py uses a hyphen, so plain `import build_site` won't work.
_SCRIPT = Path(__file__).resolve().parent / "build-site.py"
_spec = importlib.util.spec_from_file_location("build_site", _SCRIPT)
build_site = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["build_site"] = build_site
_spec.loader.exec_module(build_site)  # type: ignore[union-attr]

SITE_BASE = "/agent-ready-repo/docs"

_APPROVED_SHARED_CHROME_HEADER = (
    "how-it-works", "use-cases", "catalogue", "now", "docs", "try-the-build-loop",
)
_APPROVED_SHARED_CHROME_DOCS_BAND = (
    "product", "how-it-works", "use-cases", "catalogue", "now", "docs",
)
_APPROVED_SHARED_CHROME_DOCS_PRODUCT_NAVIGATION = (
    "product-home", "how-it-works", "use-cases", "catalogue", "now",
)
_APPROVED_SHARED_CHROME_GROUPS = (
    (
        "product",
        "Product",
        ("how-it-works", "use-cases", "catalogue", "packs", "journeys"),
    ),
    (
        "docs",
        "Docs",
        ("get-started", "install", "three-loops", "all-docs"),
    ),
    (
        "project",
        "Project",
        ("now", "changelog", "contributing", "claude-plugins", "github", "pypi"),
    ),
)
_APPROVED_SHARED_CHROME_DESTINATIONS = {
    "product": ("Product", "/", "internal"),
    "product-home": ("Product home", "/", "internal"),
    "how-it-works": ("How it works", "/#three-loops", "internal"),
    "use-cases": ("Use cases", "/#use-cases", "internal"),
    "catalogue": ("Catalogue", "/catalogue/", "internal"),
    "now": ("Now", "/now/", "internal"),
    "docs": ("Docs", "/docs/", "internal"),
    "try-the-build-loop": ("Try the build loop", "/#install", "internal"),
    "packs": ("Packs", "/packs/", "internal"),
    "journeys": ("Journeys", "/journeys/", "internal"),
    "get-started": ("Get started", "/docs/getting-started/", "internal"),
    "install": ("Install", "/docs/getting-started/install/", "internal"),
    "three-loops": ("The three loops", "/docs/getting-started/three-loops/", "internal"),
    "all-docs": ("All docs", "/docs/", "internal"),
    "changelog": ("Changelog", "/docs/changelog/", "internal"),
    "contributing": ("Contributing", "/docs/contributing/", "internal"),
    "claude-plugins": ("Claude plugins", "/plugins/", "internal"),
    "github": ("GitHub", "https://github.com/eugenelim/agent-ready-repo", "external"),
    "pypi": ("PyPI", "https://pypi.org/project/agentbundle/", "external"),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_guide(tmp_path: Path, rel: str, content: str) -> tuple[Path, Path]:
    """Create a guide source file and return (guide_src, guides_root)."""
    guides_root = tmp_path / "guides"
    src = guides_root / rel
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(content, encoding="utf-8")
    return src, guides_root


def _shared_chrome_fixture() -> dict:
    """Return a fresh copy of the approved site.toml shared-chrome contract."""
    return copy.deepcopy(
        build_site.load_shared_chrome_contract(
            Path(__file__).resolve().parent.parent / "site.toml"
        )
    )


def _assert_shared_chrome_rejected(contract: dict, expected: str) -> None:
    """Assert validation fails before it can return renderer projection data."""
    try:
        build_site.project_shared_chrome(contract)
    except ValueError as exc:
        assert expected in str(exc), str(exc)
    else:  # pragma: no cover - the raise below is the failure report
        raise AssertionError(f"shared chrome contract unexpectedly projected: {contract!r}")


def _link(destination_id: str, label: str, target: str, kind: str) -> dict:
    return {"id": destination_id, "label": label, "target": target, "kind": kind}


# ---------------------------------------------------------------------------
# Shared chrome contract — T1 of spec/site-shared-chrome
# ---------------------------------------------------------------------------

def test_shared_chrome_contract_anchor_matches_approved_vocabulary():
    """Pin the approved IA vocabulary outside the renderer-neutral source."""
    contract = _shared_chrome_fixture()

    assert tuple(contract["header"]) == _APPROVED_SHARED_CHROME_HEADER
    assert tuple(contract["docs_band"]) == _APPROVED_SHARED_CHROME_DOCS_BAND
    assert (
        tuple(contract["docs_product_navigation"])
        == _APPROVED_SHARED_CHROME_DOCS_PRODUCT_NAVIGATION
    )
    assert tuple(
        (group["id"], group["label"], tuple(group["destinations"]))
        for group in contract["groups"]
    ) == _APPROVED_SHARED_CHROME_GROUPS
    assert {
        destination["id"]: (
            destination["label"], destination["target"], destination["kind"]
        )
        for destination in contract["destinations"]
    } == _APPROVED_SHARED_CHROME_DESTINATIONS


def _expected_renderer_projection(contract: dict) -> dict:
    """Build projection expectations from the source contract, not a second taxonomy."""
    destinations = {
        destination["id"]: _link(
            destination["id"],
            destination["label"],
            destination["target"],
            destination["kind"],
        )
        for destination in contract["destinations"]
    }
    return {
        "header": [
            destinations[destination_id] for destination_id in contract["header"]
        ],
        "footer": [
            {
                "id": group["id"],
                "label": group["label"],
                "destinations": [
                    destinations[destination_id]
                    for destination_id in group["destinations"]
                ],
            }
            for group in contract["groups"]
        ],
    }


def _expected_docs_renderer_projection(contract: dict) -> dict:
    """Build docs expectations from the source's docs-specific ordered lists."""
    destinations = {
        destination["id"]: _link(
            destination["id"],
            destination["label"],
            destination["target"],
            destination["kind"],
        )
        for destination in contract["destinations"]
    }
    return {
        "product_orientation_band": [
            destinations[destination_id]
            for destination_id in contract["docs_band"]
        ],
        "product_navigation": [
            destinations[destination_id]
            for destination_id in contract["docs_product_navigation"]
        ],
        "footer": _expected_renderer_projection(contract)["footer"],
    }


def test_shared_chrome_projects_independently_allocated_renderer_data():
    """Renderers receive their own ordered, separately allocated projection data."""
    contract = _shared_chrome_fixture()
    marketing_expected = _expected_renderer_projection(contract)
    docs_expected = _expected_docs_renderer_projection(contract)

    first = build_site.project_shared_chrome(contract)
    second = build_site.project_shared_chrome(contract)
    assert first == second == {"marketing": marketing_expected, "docs": docs_expected}
    assert first["marketing"] is not first["docs"]
    assert first["marketing"]["header"] is not first["docs"]["product_orientation_band"]
    assert first["marketing"]["footer"] is not first["docs"]["footer"]

    first["marketing"]["header"][0]["label"] = "Changed only in marketing"
    assert first["docs"]["product_orientation_band"][1]["label"] == "How it works"


def test_marketing_shared_chrome_projection_writes_the_marketing_contract(tmp_path):
    """The pre-build marketing input contains no docs renderer projection."""
    output = tmp_path / "shared-chrome.generated.json"
    contract = _shared_chrome_fixture()

    payload = build_site.generate_marketing_shared_chrome_projection(contract, output)

    assert json.loads(output.read_text(encoding="utf-8")) == payload
    assert payload == build_site.project_shared_chrome(contract)["marketing"]
    assert "product_orientation_band" not in payload


def test_marketing_shared_chrome_projection_dry_run_does_not_write(tmp_path):
    """Dry runs calculate the marketing projection without changing its input file."""
    output = tmp_path / "shared-chrome.generated.json"

    build_site.generate_marketing_shared_chrome_projection(
        _shared_chrome_fixture(), output, dry_run=True
    )

    assert not output.exists()


def test_marketing_shared_chrome_projection_rejects_a_seeded_stale_literal(tmp_path):
    """AC1 guard: hand-edited renderer input cannot drift from the sole source."""
    output = tmp_path / "shared-chrome.generated.json"
    contract = _shared_chrome_fixture()
    payload = build_site.generate_marketing_shared_chrome_projection(contract, output)
    payload["header"][0]["label"] = "Stale marketing literal"
    output.write_text(json.dumps(payload), encoding="utf-8")

    try:
        build_site.assert_marketing_shared_chrome_projection_current(contract, output)
    except ValueError as exc:
        assert "is stale" in str(exc)
    else:  # pragma: no cover - the raise below is the failure report
        raise AssertionError("a stale marketing shared-chrome literal passed consistency")


def test_docs_shared_chrome_projection_writes_only_the_docs_contract(tmp_path):
    """The post-web-build docs input has no marketing header projection."""
    output = tmp_path / "shared-chrome.generated.json"
    contract = _shared_chrome_fixture()

    payload = build_site.generate_docs_shared_chrome_projection(contract, output)

    assert json.loads(output.read_text(encoding="utf-8")) == payload
    assert payload == build_site.project_shared_chrome(contract)["docs"]
    assert "header" not in payload


def test_docs_shared_chrome_projection_dry_run_does_not_write(tmp_path):
    """Dry runs calculate the docs projection without changing its input file."""
    output = tmp_path / "shared-chrome.generated.json"

    build_site.generate_docs_shared_chrome_projection(
        _shared_chrome_fixture(), output, dry_run=True
    )

    assert not output.exists()


def test_docs_shared_chrome_projection_rejects_a_seeded_stale_literal(tmp_path):
    """AC1 guard: hand-edited docs input cannot drift from the sole source."""
    output = tmp_path / "shared-chrome.generated.json"
    contract = _shared_chrome_fixture()
    payload = build_site.generate_docs_shared_chrome_projection(contract, output)
    payload["product_orientation_band"][0]["label"] = "Stale docs literal"
    output.write_text(json.dumps(payload), encoding="utf-8")

    try:
        build_site.assert_docs_shared_chrome_projection_current(contract, output)
    except ValueError as exc:
        assert "is stale" in str(exc)
    else:  # pragma: no cover - the raise below is the failure report
        raise AssertionError("a stale docs shared-chrome literal passed consistency")


def test_shared_chrome_rejects_duplicate_destination_ids():
    contract = _shared_chrome_fixture()
    duplicate = copy.deepcopy(
        next(
            destination
            for destination in contract["destinations"]
            if destination["id"] == "how-it-works"
        )
    )
    contract["destinations"].append(duplicate)

    _assert_shared_chrome_rejected(contract, "duplicate destination ID 'how-it-works'")


def test_shared_chrome_rejects_duplicate_group_ids():
    contract = _shared_chrome_fixture()
    duplicate = copy.deepcopy(contract["groups"][0])
    contract["groups"].append(duplicate)

    _assert_shared_chrome_rejected(contract, "duplicate group ID 'product'")


def test_shared_chrome_rejects_missing_group_members():
    contract = _shared_chrome_fixture()
    contract["groups"][0]["destinations"][-1] = "missing-journeys"

    _assert_shared_chrome_rejected(contract, "destination 'missing-journeys'")


def test_shared_chrome_rejects_a_group_repeating_a_member():
    contract = _shared_chrome_fixture()
    contract["groups"][0]["destinations"].append("how-it-works")

    _assert_shared_chrome_rejected(contract, "group 'product' repeats destination 'how-it-works'")


def test_shared_chrome_rejects_a_group_listing_a_destination_from_another_group():
    contract = _shared_chrome_fixture()
    contract["groups"][0]["destinations"][-1] = "all-docs"

    _assert_shared_chrome_rejected(
        contract,
        "destination 'all-docs' references group 'docs', not 'product'",
    )


def test_shared_chrome_rejects_a_destination_omitted_from_its_declared_group():
    contract = _shared_chrome_fixture()
    contract["groups"][0]["destinations"].pop(0)

    _assert_shared_chrome_rejected(
        contract,
        "destination 'how-it-works' references group 'product' but is missing",
    )


def test_shared_chrome_rejects_destination_referencing_a_missing_group():
    contract = _shared_chrome_fixture()
    contract["groups"].pop(0)

    _assert_shared_chrome_rejected(contract, "destination 'how-it-works' references missing group 'product'")


def test_shared_chrome_rejects_unsupported_target_kinds():
    contract = _shared_chrome_fixture()
    next(
        destination
        for destination in contract["destinations"]
        if destination["id"] == "how-it-works"
    )["kind"] = "mailto"

    _assert_shared_chrome_rejected(contract, "destination 'how-it-works' has unsupported kind 'mailto'")


def test_shared_chrome_rejects_invalid_internal_target_shapes():
    invalid_targets = {
        "https://example.test/": "expected a root-relative target",
        "//example.test/": "protocol-relative targets are not allowed",
        "/docs\\getting-started/": "backslashes are not allowed",
        "/docs/../getting-started/": "parent-directory segments are not allowed",
        "/docs/has space/": "whitespace is not allowed",
        "/#": "fragment must be non-empty",
        "/docs/getting-started": "expected a '/'-terminated path or '#fragment' form",
    }
    for target, expected in invalid_targets.items():
        contract = _shared_chrome_fixture()
        contract["destinations"][0]["target"] = target

        _assert_shared_chrome_rejected(contract, expected)


def test_shared_chrome_rejects_header_references_and_duplicates():
    contract = _shared_chrome_fixture()
    contract["header"][0] = "missing-destination"

    _assert_shared_chrome_rejected(contract, "header references missing destination 'missing-destination'")

    contract = _shared_chrome_fixture()
    contract["header"][1] = "how-it-works"

    _assert_shared_chrome_rejected(contract, "header repeats destination 'how-it-works'")


def test_shared_chrome_rejects_invalid_docs_band_entries():
    contract = _shared_chrome_fixture()
    contract["docs_band"] = "product"

    _assert_shared_chrome_rejected(
        contract,
        "site.toml shared_chrome.docs_band must be an ordered destination ID array",
    )

    contract = _shared_chrome_fixture()
    contract["docs_band"][0] = ""

    _assert_shared_chrome_rejected(
        contract,
        "shared chrome docs_band has invalid 'docs_band'",
    )

    contract = _shared_chrome_fixture()
    contract["docs_band"][0] = "missing-destination"

    _assert_shared_chrome_rejected(
        contract,
        "docs_band references missing destination 'missing-destination'",
    )

    contract = _shared_chrome_fixture()
    contract["docs_band"][1] = "product"

    _assert_shared_chrome_rejected(
        contract,
        "docs_band repeats destination 'product'",
    )


def test_shared_chrome_rejects_invalid_docs_product_navigation_entries():
    contract = _shared_chrome_fixture()
    contract["docs_product_navigation"] = "product-home"

    _assert_shared_chrome_rejected(
        contract,
        "site.toml shared_chrome.docs_product_navigation must be an ordered destination ID array",
    )

    contract = _shared_chrome_fixture()
    contract["docs_product_navigation"][0] = ""

    _assert_shared_chrome_rejected(
        contract,
        "shared chrome docs_product_navigation has invalid 'docs_product_navigation'",
    )

    contract = _shared_chrome_fixture()
    contract["docs_product_navigation"][0] = "missing-destination"

    _assert_shared_chrome_rejected(
        contract,
        "docs_product_navigation references missing destination 'missing-destination'",
    )

    contract = _shared_chrome_fixture()
    contract["docs_product_navigation"][1] = "product-home"

    _assert_shared_chrome_rejected(
        contract,
        "docs_product_navigation repeats destination 'product-home'",
    )


def test_shared_chrome_rejects_presentation_and_state_fields():
    contract = _shared_chrome_fixture()
    contract["state"] = "renderer-owned"
    _assert_shared_chrome_rejected(contract, "contract has unsupported field 'state'")

    contract = _shared_chrome_fixture()
    next(
        destination
        for destination in contract["destinations"]
        if destination["id"] == "how-it-works"
    )["breakpoint"] = "renderer-owned"
    _assert_shared_chrome_rejected(
        contract,
        "destination 'how-it-works' has unsupported field 'breakpoint'",
    )

    contract = _shared_chrome_fixture()
    contract["groups"][0]["state"] = "renderer-owned"
    _assert_shared_chrome_rejected(contract, "group 'product' has unsupported field 'state'")

    contract = _shared_chrome_fixture()
    contract["unexpected"] = "renderer-owned"
    _assert_shared_chrome_rejected(contract, "contract has unsupported field 'unexpected'")


def test_journeys_only_validates_shared_chrome_before_projection(monkeypatch):
    """A malformed contract blocks journeys-only projections before they run."""
    def fail_validation(_site_toml: Path) -> None:
        raise ValueError("invalid shared chrome")

    def unexpected_projection(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("journeys-only projection ran before shared-chrome validation")

    monkeypatch.setattr(build_site, "load_shared_chrome_contract", fail_validation)
    monkeypatch.setattr(build_site, "sync_pack_journeys", unexpected_projection)
    monkeypatch.setattr(
        build_site, "generate_marketing_shared_chrome_projection", unexpected_projection
    )
    monkeypatch.setattr(build_site, "_report_now_projection", unexpected_projection)
    monkeypatch.setattr(sys, "argv", ["build-site.py", "--journeys-only"])

    try:
        build_site.main()
    except ValueError as exc:
        assert str(exc) == "invalid shared chrome"
    else:  # pragma: no cover - the raise below is the failure report
        raise AssertionError("journeys-only build unexpectedly projected invalid shared chrome")


def test_journeys_only_emits_marketing_shared_chrome_before_the_web_build(monkeypatch):
    """The pre-web-build path emits the generated marketing renderer input."""
    contract = _shared_chrome_fixture()
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(build_site, "load_shared_chrome_contract", lambda _path: contract)
    monkeypatch.setattr(build_site, "sync_pack_journeys", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(
        build_site,
        "generate_marketing_shared_chrome_projection",
        lambda received, **kwargs: calls.append(("shared_chrome", (received, kwargs))),
    )
    monkeypatch.setattr(
        build_site,
        "generate_docs_shared_chrome_projection",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("journeys-only must not emit the post-web docs input")
        ),
    )
    monkeypatch.setattr(
        build_site,
        "_report_now_projection",
        lambda *_args, **_kwargs: calls.append(("now", None)),
    )
    monkeypatch.setattr(sys, "argv", ["build-site.py", "--journeys-only", "--dry-run"])

    build_site.main()

    assert calls == [
        ("shared_chrome", (contract, {"dry_run": True})),
        ("now", None),
    ]


# ---------------------------------------------------------------------------
# 1 — slug override changes the output path
# ---------------------------------------------------------------------------

def test_slug_override_changes_output_path(tmp_path):
    src, guides_root = _make_guide(tmp_path, "product-documentation/getting-started.md", """\
---
title: "Getting Started"
summary: "Learn the basics."
pack: product-documentation
kind: tutorial
slug: guides/product-documentation/how-to/getting-started
---

Content here.
""")
    site_docs = tmp_path / "docs"
    site_docs.mkdir()

    # Default: site_docs/guides/product-documentation/getting-started.md
    # Slug-override: site_docs/guides/product-documentation/how-to/getting-started.md
    build_site.mirror_guides(guides_root, site_docs, dry_run=False)

    overridden = site_docs / "guides" / "product-documentation" / "how-to" / "getting-started.md"
    default = site_docs / "guides" / "product-documentation" / "getting-started.md"

    assert overridden.exists(), f"Expected file at overridden path {overridden}"
    assert not default.exists(), "Default path should not exist when slug is overridden"


# ---------------------------------------------------------------------------
# 2 — alias generates a meta-refresh redirect stub
# ---------------------------------------------------------------------------

def test_alias_generates_redirect_stub(tmp_path):
    src, guides_root = _make_guide(tmp_path, "product-documentation/new-guide.md", """\
---
title: "New Guide"
summary: "Useful."
pack: product-documentation
kind: how-to
slug: guides/product-documentation/new-guide
aliases:
  - guides/product-documentation/old-guide
---

Content.
""")
    site_docs = tmp_path / "docs"
    site_docs.mkdir()

    build_site.mirror_guides(guides_root, site_docs, dry_run=False)

    stub = site_docs / "guides" / "product-documentation" / "old-guide.md"
    assert stub.exists(), f"Expected redirect stub at {stub}"
    content = stub.read_text(encoding="utf-8")
    assert "meta http-equiv" in content.lower() or "refresh" in content.lower(), \
        "Redirect stub should contain meta-refresh"
    assert "new-guide" in content, "Redirect stub should point to canonical slug"


# ---------------------------------------------------------------------------
# 3 — guide-metadata fields are stripped from output
# ---------------------------------------------------------------------------

def test_guide_metadata_stripped_from_output(tmp_path):
    # Include slug: and aliases: so the test pins that they are also stripped.
    # slug: guides/core/my-guide keeps the output path identical to the default.
    src, guides_root = _make_guide(tmp_path, "core/my-guide.md", """\
---
title: "My Guide"
summary: "Summary text."
pack: core
kind: explanation
journey: core-first-run
order: 3
status: stable
slug: guides/core/my-guide
aliases:
  - guides/core/my-guide-old
---

Body content.
""")
    site_docs = tmp_path / "docs"
    site_docs.mkdir()

    build_site.mirror_guides(guides_root, site_docs, dry_run=False)

    out = site_docs / "guides" / "core" / "my-guide.md"
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    # All guide-specific fields must be absent from the written file
    stripped_fields = (
        "pack:", "kind:", "summary:", "journey:", "order:", "status:", "slug:", "aliases:",
    )
    for field in stripped_fields:
        assert field not in content, (
            f"Field '{field}' should be stripped from output, but was found"
        )
    # title must be preserved
    assert "title:" in content


# ---------------------------------------------------------------------------
# 4 — file without frontmatter: title injected, content unchanged
# ---------------------------------------------------------------------------

def test_no_frontmatter_passthrough_unchanged(tmp_path):
    src, guides_root = _make_guide(tmp_path, "core/legacy.md", """\
# Legacy Guide

Some existing content without frontmatter.
""")
    site_docs = tmp_path / "docs"
    site_docs.mkdir()

    build_site.mirror_guides(guides_root, site_docs, dry_run=False)

    out = site_docs / "guides" / "core" / "legacy.md"
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    # Frontmatter should have been injected
    assert content.startswith("---")
    assert "title:" in content
    # Original body content must be present
    assert "Some existing content without frontmatter." in content


# ---------------------------------------------------------------------------
# 5 — docs/guides/ is not mirrored (integration test against real repo)
# ---------------------------------------------------------------------------

def test_docs_guides_not_mirrored_from_real_guides_root(tmp_path):
    """mirror_guides(real guides/, …) must not include any docs/guides/ content."""
    guides_root = build_site.REPO_ROOT / "guides"
    docs_guides = build_site.REPO_ROOT / "docs" / "guides"

    docs_guide_files = list(docs_guides.glob("*.md"))
    assert docs_guide_files, (
        "Expected at least one .md in docs/guides/ for this assertion to be meaningful"
    )

    site_docs = tmp_path / "site"
    site_docs.mkdir()
    build_site.mirror_guides(guides_root, site_docs, dry_run=False)

    for doc in docs_guide_files:
        assert not (site_docs / "guides" / doc.name).exists(), (
            f"{doc.name} from docs/guides/ must not appear in the mirrored docs site"
        )
    # Sanity: some actual guides/ content was mirrored
    assert any(site_docs.rglob("*.md")), "Expected mirrored guides to produce at least one file"


# --------------------------------------------------------------------------
# spec/site-shared-chrome AC10 — the two renderers stay independent
# --------------------------------------------------------------------------
#
# Shared chrome means shared destination vocabulary and NOTHING else. Both
# renderers now consume the same canonical contract, which is exactly the
# condition under which someone reaches for "just import the other one's
# helper" — so the boundary needs a check rather than a convention. The
# existing marketing-token tests below cover the palette half of AC10; these
# cover source imports and the separateness of the two projected inputs.

_MARKETING_CHROME_SOURCES = (
    "web/src/components/layout/SiteNav.astro",
    "web/src/components/layout/SiteFooter.astro",
    "web/src/lib/shared-chrome.ts",
)
_DOCS_CHROME_SOURCES = (
    "docs-site/src/components/PageFrame.astro",
    "docs-site/src/components/Footer.astro",
    "docs-site/src/components/shared-chrome.ts",
)


# Any construct that makes one tree depend on a file in another: JS/TS imports and
# re-exports, CSS `@import`, and `url()` asset references. A named-file allowlist
# would only cover the files someone remembered, so the sweep walks both trees.
_DEPENDENCY_RE = re.compile(
    r"""(?:\bfrom\s*|\bimport\s*|\brequire\s*\(\s*|@import\s*|\burl\s*\()['"]([^'"]+)['"]"""
)
_RENDERER_TREES = (
    # (tree scanned, the other renderer's directory it may not reach into)
    ("web/src", "docs-site"),
    ("docs-site/src", "web"),
)
# The emitted-output suites deliberately read BOTH build trees to compare them;
# they are assertions about the boundary, not a crossing of it.
_CROSS_TREE_TEST_FILES = frozenset({
    "web/src/test/rendered-output.test.ts",
})


def _renderer_source_files(tree: str):
    """Every hand-written source file under a renderer tree."""
    root = _REPO_ROOT / tree
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "node_modules" in path.parts:
            continue
        if path.suffix not in {".astro", ".ts", ".tsx", ".js", ".mjs", ".css", ".json"}:
            continue
        if path.name.endswith(".generated.json"):
            continue
        yield path


def test_neither_renderer_imports_the_other_renderers_chrome():
    """AC10: no shared components, helpers, tokens, CSS, or state across renderers.

    Swept over both trees rather than a list of the files someone thought of: a
    cross-renderer `@import` in a stylesheet, or an import added to a component
    this guard never named, is the same violation as one in the chrome files.
    """
    offenders = []
    for tree, forbidden in _RENDERER_TREES:
        for path in _renderer_source_files(tree):
            relative = str(path.relative_to(_REPO_ROOT))
            if relative in _CROSS_TREE_TEST_FILES:
                continue
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                for target in _DEPENDENCY_RE.findall(line):
                    # Only a path that climbs out of this tree can reach the other.
                    if ".." not in target and not target.startswith("/"):
                        continue
                    if re.search(rf"(^|/){re.escape(forbidden)}/", target):
                        offenders.append(f"{relative}:{number}: {line.strip()}")
    assert not offenders, (
        "a renderer depends on the other renderer's files: " + "; ".join(offenders)
    )


def test_the_chrome_files_this_guard_names_still_exist():
    """A stale path would silently drop a file from the AC10 sweep's spot-checks."""
    missing = [
        relative
        for relative in _MARKETING_CHROME_SOURCES + _DOCS_CHROME_SOURCES
        if not (_REPO_ROOT / relative).is_file()
    ]
    assert not missing, f"AC10 guard names files that no longer exist: {missing}"


def test_each_renderer_reads_its_own_projected_input():
    """AC10: one canonical source, two independently allocated renderer inputs."""
    marketing = _REPO_ROOT / "web" / "src" / "lib" / "shared-chrome.generated.json"
    docs = _REPO_ROOT / "docs-site" / "src" / "shared-chrome.generated.json"
    assert marketing.is_file() and docs.is_file()
    assert marketing != docs

    marketing_payload = json.loads(marketing.read_text(encoding="utf-8"))
    docs_payload = json.loads(docs.read_text(encoding="utf-8"))
    # The docs projection deliberately exposes no `header`: the docs band is not
    # the marketing header, and inferring one from the other is the drift this
    # separation exists to prevent.
    assert set(marketing_payload) == {"header", "footer"}
    assert "header" not in docs_payload
    assert set(docs_payload) == {
        "product_orientation_band", "product_navigation", "footer",
    }

    # Each renderer reads its own file and only its own file.
    for relative, own, other in (
        ("web/src/components/layout/SiteFooter.astro",
         "lib/shared-chrome.generated.json", "docs-site"),
        ("docs-site/src/components/PageFrame.astro",
         "shared-chrome.generated.json", "web/src"),
    ):
        text = (_REPO_ROOT / relative).read_text(encoding="utf-8")
        assert own in text, f"{relative} no longer reads its own projected input"
        assert other not in text, f"{relative} reaches into the other renderer"


# --------------------------------------------------------------------------
# spec/docs-site-build-contract-hardening AC1/AC2 — no marketing-token dependency
# --------------------------------------------------------------------------
#
# These two run the generator as a SUBPROCESS inside a temp tree rather than
# calling `main()` in-process. `REPO_ROOT` is module-level and the token copy lived
# inline in `main()`, so an in-process call would read the real
# `web/src/styles/tokens.css` and write into the real
# `docs-site/src/content/docs/` — no isolation, and a dirtied worktree. Copying
# `build-site.py` plus `site.toml` into the fixture makes `REPO_ROOT` the fixture.
#
# Before this change the generator exited 1 with
# `error  web/src/styles/tokens.css missing — docs-site CSS depends on it`. That
# claim was false: `docs-site/src/styles/starlight.css` stopped importing the copied
# file, so the copy was vestigial and the hard failure was a false dependency.


def _generator_fixture(tmp_path):
    """A minimal tree where the generator can run with REPO_ROOT == tmp_path."""
    (tmp_path / "tools").mkdir()
    shutil.copy2(_SCRIPT, tmp_path / "tools" / "build-site.py")
    real_site_toml = _SCRIPT.parent.parent / "site.toml"
    if real_site_toml.is_file():
        shutil.copy2(real_site_toml, tmp_path / "site.toml")
    # The trees the generator reads and writes. Empty is fine: this asserts the
    # token contract, not mirroring behaviour, which the tests above cover.
    for d in ("guides", "packs", "docs-site/src/content/docs", "docs-site/src/styles",
              "web/src/styles", "docs/product", "web/src/lib"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    # The generator refuses to run without a changelog rather than leaving the
    # marketing build to render a stale committed `/now/` projection, so the
    # fixture supplies a minimal one. Content is irrelevant here — these two
    # tests assert the design-token contract.
    (tmp_path / "docs" / "product" / "changelog.md").write_text(
        "# Changelog\n\n## [Unreleased]\n", encoding="utf-8"
    )
    return tmp_path


def _run_generator(root):
    return subprocess.run(
        [sys.executable, str(root / "tools" / "build-site.py")],
        cwd=root, capture_output=True, text=True,
    )


def test_generation_succeeds_without_the_marketing_token_file(tmp_path):
    """AC2: no marketing token file present, and generation still succeeds.

    This is the criterion's whole point — the previous contract exited 1 here.
    """
    root = _generator_fixture(tmp_path)
    tokens = root / "web" / "src" / "styles" / "tokens.css"
    assert not tokens.exists(), "fixture must not provide the marketing token file"
    r = _run_generator(root)
    assert r.returncode == 0, (
        "generation must not depend on the marketing token file:\n"
        + r.stdout + r.stderr
    )
    assert "tokens.css missing" not in (r.stdout + r.stderr), r.stdout + r.stderr


def test_generation_writes_no_docs_token_copy(tmp_path):
    """AC1/AC2: even WITH a marketing token file present, no copy is emitted.

    Asserted with the source present, because a test that only removes the source
    cannot distinguish "the copy was deleted" from "the copy was skipped for lack of
    input" — the mutation that reintroduces the copy would then still pass.
    """
    root = _generator_fixture(tmp_path)
    src = root / "web" / "src" / "styles" / "tokens.css"
    src.write_text(":root { --brand: #f59e0b; }\n", encoding="utf-8")
    r = _run_generator(root)
    assert r.returncode == 0, r.stdout + r.stderr
    copied = root / "docs-site" / "src" / "styles" / "tokens.css"
    assert not copied.exists(), (
        "generation must not copy marketing tokens into docs-site: the docs palette "
        "is self-contained per ADR-0085"
    )
    assert "copying design tokens" not in r.stdout, r.stdout


# ---------------------------------------------------------------------------
# /now/ — released changelog Highlights projection (spec/site-now-surface)
#
# Eligibility is structural: versioned + dated + not beneath `[Unreleased]`.
# Every fixture below is mutation-sensitive — each asserts a DIFFERENT payload
# for a one-token source change, so a parser that ignored placement or ordering
# could not pass them.
# ---------------------------------------------------------------------------

_RELEASED = """# Changelog

## [Unreleased]

### [pkg-a][9.9.9] — 2026-08-18

#### Highlights

- Unreleased highlight that must never publish.

## [pkg-b][1.0.0] — 2026-08-17

### Highlights

- Released highlight that must publish.

### Changed

- A technical note that must not publish.
"""


def _groups(text):
    return build_site.project_now_highlights(text)["groups"]


def _bullets(group):
    return [h["source"] for h in group["highlights"]]


def test_unreleased_highlights_never_project_even_when_dated():
    """A date beneath `[Unreleased]` does not make an entry released.

    The real changelog nests dated, version-shaped `###` entries inside its
    first `## [Unreleased]` region, so this is the live shape rather than a
    hypothetical one. Placement decides eligibility; a positional "everything
    after the first release heading" rule would publish all of them.
    """
    groups = _groups(_RELEASED)
    assert [g["packages"][0]["name"] for g in groups] == ["pkg-b"]
    assert _bullets(groups[0]) == ["Released highlight that must publish."]


def test_promoting_an_entry_out_of_unreleased_publishes_it():
    """The same bytes, one heading level up, publish — proving rule 2 is live."""
    promoted = _RELEASED.replace(
        "### [pkg-a][9.9.9] — 2026-08-18", "## [pkg-a][9.9.9] — 2026-08-18"
    ).replace("#### Highlights", "### Highlights")
    names = [g["packages"][0]["name"] for g in _groups(promoted)]
    assert names == ["pkg-a", "pkg-b"], names


def test_a_released_entry_without_highlights_is_absent_from_now():
    """Missing Highlights is valid and simply does not publish."""
    text = _RELEASED.replace(
        "### Highlights\n\n- Released highlight that must publish.\n\n", ""
    )
    assert _groups(text) == []


def test_only_the_highlights_subsection_publishes():
    """Sibling groups such as `Changed` stay in the technical changelog."""
    published = " ".join(_bullets(_groups(_RELEASED)[0]))
    assert "technical note" not in published


def test_highlights_are_read_at_the_level_relative_to_their_entry():
    """A `Highlights` heading is found relative to its entry, not at a fixed depth.

    Both entries below are released; they sit at different heading levels, so a
    parser hard-coding `###` would silently drop one release's copy.
    """
    text = """# Changelog

## [pkg-a][1.0.0] — 2026-08-02

### Highlights

- Deep entry highlight.

# [pkg-b][2.0.0] — 2026-08-01

## Highlights

- Shallow entry highlight.
"""
    got = {g["packages"][0]["name"]: _bullets(g) for g in _groups(text)}
    assert got == {
        "pkg-a": ["Deep entry highlight."],
        "pkg-b": ["Shallow entry highlight."],
    }, got


def test_groups_sort_by_release_date_descending():
    text = """# Changelog

## [old][1.0.0] — 2026-08-01

### Highlights

- Older.

## [new][2.0.0] — 2026-08-09

### Highlights

- Newer.
"""
    assert [g["date"] for g in _groups(text)] == ["2026-08-09", "2026-08-01"]


def test_equal_dates_preserve_source_order():
    """Ties keep source order — the contract's tiebreak, and a real case.

    `changelog.md` carries many same-day releases, so a sort that reversed ties
    would reorder most of the page.
    """
    text = """# Changelog

## [first][1.0.0] — 2026-08-05

### Highlights

- First in source.

## [second][1.0.0] — 2026-08-05

### Highlights

- Second in source.
"""
    assert [g["packages"][0]["name"] for g in _groups(text)] == ["first", "second"]


def test_one_entry_releasing_two_packages_keeps_both_identities():
    """`[core][2.7.4] and [architect][0.14.5] — …` is a real heading shape."""
    text = """# Changelog

## [core][2.7.4] and [architect][0.14.5] — 2026-08-17

### Highlights

- Joint release.
"""
    got = _groups(text)[0]["packages"]
    assert got == [
        {"name": "core", "version": "2.7.4"},
        {"name": "architect", "version": "0.14.5"},
    ], got


def test_a_release_heading_without_a_trailing_date_fails_generation():
    """Package identity but no trailing date is malformed, not "not a release".

    Treating it as an ordinary heading is worse than failing: its Highlights are
    either dropped without a word or attached to whichever entry happens to be
    open, publishing copy under a release that does not claim it. Verified
    against the real changelog — no heading there carries a version without a
    trailing date, so this can only fire on an authoring mistake.
    """
    for title in ("## [pkg][1.0.0]", "## [pkg][1.0.0] — 2026-08-17 (yanked)"):
        text = f"""# Changelog

{title}

### Highlights

- Would be misfiled.
"""
        try:
            build_site.project_now_highlights(text)
        except ValueError as exc:
            assert "trailing release date" in str(exc), str(exc)
        else:  # pragma: no cover - the raise below is the failure report
            raise AssertionError(f"{title!r} did not fail generation")


def test_an_impossible_date_fails_generation_loudly():
    """A malformed release date raises rather than silently dropping the entry.

    Dropping it would under-report the launch window while looking successful.
    """
    text = """# Changelog

## [pkg][1.0.0] — 2026-13-01

### Highlights

- Impossible month.
"""
    try:
        build_site.project_now_highlights(text)
    except ValueError as exc:
        assert "impossible date" in str(exc)
    else:  # pragma: no cover - the assertion below is the failure report
        raise AssertionError("a 13th month did not fail generation")


def test_a_decorated_unreleased_heading_still_opens_an_unreleased_region():
    """The Unreleased test must not be defeated by decoration.

    An exact-match anchor fails OPEN here: a decorated heading stops registering
    as Unreleased, its region is recorded as released, and every dated child
    beneath it publishes. The emitted vocabulary check cannot catch that — the
    leaked bullet need not contain the word "unreleased" anywhere. Each variant
    below leaked in-progress copy before this was fixed.
    """
    for title in (
        "## [Unreleased]",
        "## Unreleased",
        "## [Unreleased] — 2026-08-18",
        "## Unreleased (2.9.0)",
        "## [Unreleased] (agentbundle)",
        "## Unreleased:",
        # Decoration. Each of these leaked before the test stopped being anchored
        # to the start of the heading.
        "## (Unreleased)",
        "## **Unreleased**",
        "## _Unreleased_",
        "## 🚧 Unreleased",
        "## — Unreleased —",
        # And the forms where the word is not the leading token at all. A
        # leading-token rule misses these three.
        "## Next (unreleased)",
        "## The unreleased queue",
        "## Pending / unreleased",
        "## Work not yet released — unreleased",
    ):
        # The dated child carrying Highlights is the load-bearing part of this
        # fixture: a bare prose heading with nothing beneath it cannot leak, so a
        # fixture without the child passes even while the leak is wide open.
        text = f"""# Changelog

{title}

### [pkg][9.9.9] — 2026-08-18

#### Highlights

- In-progress content that must never publish.
"""
        assert _groups(text) == [], f"{title!r} leaked its Highlights"


def test_the_reference_link_unreleased_heading_opens_a_region_not_an_entry():
    """`## [Unreleased][unreleased]` is release-SHAPED and means the opposite.

    It is the Markdown reference-link form older Keep a Changelog templates ship,
    and `docs/product/changelog.md` still carries the matching
    `[Unreleased]: https://…compare/v1.0.0...HEAD` definition it pairs with — so
    this is an upstream-canonical spelling, not a contrived one.

    It regressed when release identity was moved ahead of the region test: the
    guard that used to catch it compared through the Unreleased pattern, which had
    just been broadened to a bare `unreleased`, and `re.match` against a string
    starting with `[` can never succeed. Both halves of that change were right on
    their own; the interaction was the defect.
    """
    for title in (
        "## [Unreleased][unreleased] — 2026-08-18",
        "## [Unreleased][HEAD] — 2026-08-18",
        "## [unreleased][main] — 2026-08-18",
        # The VERSION slot, not just the name. A version left as `unreleased`
        # while the number is still being cut published its Highlights and
        # rendered the public label "agentbundle unreleased".
        "## [agentbundle][unreleased] — 2026-08-18",
        "## [core][UNRELEASED] — 2026-08-18",
        # And the multi-package form, which this changelog actually uses. Scoping
        # the guard to a single pair skipped these entirely.
        "## [Unreleased][unreleased] and [core][2.7.4] — 2026-08-17",
        "## [core][2.7.4] and [architect][unreleased] — 2026-08-17",
    ):
        text = f"""# Changelog

{title}

### [pkg][9.9.9] — 2026-08-18

#### Highlights

- In-progress content that must never publish.
"""
        assert _groups(text) == [], f"{title!r} leaked its Highlights"

    # And the undated form must not hard-fail the build on the missing date.
    undated = """# Changelog

## [Unreleased][unreleased]

### [pkg][9.9.9] — 2026-08-18

#### Highlights

- In-progress content that must never publish.
"""
    assert _groups(undated) == []


def test_a_package_named_unreleased_something_still_releases():
    """Release identity is decided FIRST, so a pack name cannot suppress its entry."""
    text = """# Changelog

## [unreleased-tools][1.0.0] — 2026-08-05

### Highlights

- Should publish.
"""
    groups = _groups(text)
    assert [g["packages"][0]["name"] for g in groups] == ["unreleased-tools"]


def test_prose_headings_are_not_release_entries_and_do_not_fail_the_build():
    """Ordinary prose must not be mistaken for a RELEASE, and must not break the build.

    Deliberately NOT "and must not open an Unreleased region": a heading like
    `### Fixed an unreleased regression` now does open one, on purpose, because
    failing closed beats guessing. It is reported so the withholding is
    diagnosable. What must never happen is the build stopping on a sentence —
    Markdown reference links share the `[a][b]` shape a release heading uses, so
    an unanchored search read these as malformed releases and raised.

    These fixtures carry no dated child, so they prove only the no-raise half.
    The leak half is `test_a_decorated_unreleased_heading_still_opens_an_unreleased_region`,
    whose fixtures do carry one — a child-less fixture cannot leak, which is
    exactly how an earlier round's hole stayed green.
    """
    for title in (
        "## Thanks to [everyone][credits] who filed issues",
        "## Migrating from [v1][v1-docs] to [v2][v2-docs]",
        "### Fixed an unreleased regression",
        "## Notes on unreleased material",
    ):
        text = f"""# Changelog

{title}

- a bullet
"""
        assert build_site.project_now_highlights(text)["groups"] == [], title


def test_a_heading_mentioning_unreleased_outside_a_region_is_reported():
    """Surfaced as a diagnostic, because it is a real near-miss worth seeing."""
    text = """# Changelog

## Notes on unreleased material

### Highlights

- Ambiguous.
"""
    parsed = build_site.parse_changelog_releases(text)
    assert [t for _, t in parsed.diagnostics["unreleased_regions"]] == [
        "Notes on unreleased material"
    ]


def test_a_misplaced_highlights_block_is_reported_rather_than_dropped_in_silence():
    """A refusal that says nothing is indistinguishable from writing nothing."""
    text = """# Changelog

## [pkg][1.0.0] — 2026-08-05

### Changed

#### Highlights

- Nested too deep to publish.
"""
    assert _groups(text) == []
    parsed = build_site.parse_changelog_releases(text)
    assert [
        (level, title) for _, level, title in parsed.diagnostics["misplaced_highlights"]
    ] == [(4, "Highlights")]


def test_a_release_entry_closes_at_the_next_heading_of_its_own_level():
    """A later sibling heading must not donate its Highlights to an earlier release.

    Before the entry scope was tracked, `current` survived every following
    non-release heading, so these bullets were appended to `[old][0.1.0]` and
    published under a release that does not claim them.
    """
    text = """# Changelog

## [old][0.1.0] — 2026-08-01

### Highlights

- Legitimately belongs to old 0.1.0.

## Notes for maintainers

### Highlights

- Belongs to no release at all.
"""
    groups = _groups(text)
    assert len(groups) == 1
    assert _bullets(groups[0]) == ["Legitimately belongs to old 0.1.0."]


def test_a_child_group_heading_does_not_close_its_own_release_entry():
    """`### Added` is deeper than its entry, so the entry stays open.

    The guard against the previous test must close a SIBLING, not a child.
    """
    text = """# Changelog

## [pkg][1.0.0] — 2026-08-05

### Added

- technical note

### Highlights

- Still attaches to pkg 1.0.0.
"""
    groups = _groups(text)
    assert len(groups) == 1
    assert _bullets(groups[0]) == ["Still attaches to pkg 1.0.0."]


def test_a_highlights_heading_below_the_entrys_immediate_child_level_is_ignored():
    """Only the entry's immediate child may be its Highlights block."""
    text = """# Changelog

## [pkg][1.0.0] — 2026-08-05

### Changed

#### Highlights

- Nested two levels down; belongs to `Changed`, not to the release.
"""
    assert _groups(text) == []


def test_a_nested_fence_does_not_close_its_outer_block():
    """A ``` inside a ````-fenced sample must not end the fence.

    This was the one fail-open that survived two review rounds. The inner ```
    closed the block, the sample's release heading became a real release, and the
    trailing markers restored parity so the unterminated-fence raise never
    fired — `fake copy` published as a public highlight.
    """
    text = """# Changelog

## [real][1.0.0] — 2026-08-05

### Highlights

- Real.

````markdown
```
## [fake][9.9.9] — 2026-08-06

### Highlights

- fake copy
```
````
"""
    groups = _groups(text)
    assert [g["packages"][0]["name"] for g in groups] == ["real"]
    assert _bullets(groups[0]) == ["Real."]


def test_a_marker_run_with_an_info_string_does_not_close_a_fence():
    """CommonMark's third closer rule: nothing but whitespace after the run.

    Without it ```` ```bash ```` closes a ```` ``` ```` block, the sample's
    release heading becomes a real entry, and the trailing marker restores parity
    so the unterminated-fence raise never fires.
    """
    text = """# Changelog

## [real][1.0.0] — 2026-08-05

### Highlights

- Real.

```markdown
```bash
## [fake][9.9.9] — 2026-08-06

### Highlights

- fake copy
```
"""
    assert [g["packages"][0]["name"] for g in _groups(text)] == ["real"]


def test_an_indented_fence_is_still_skipped():
    """A fence indented under a list item is ordinary Markdown.

    Tightening the opener to `^ {0,3}` while fixing the closer rule regressed
    these into published copy — sample lines and literal backticks reaching the
    public page. The opener stays LOOSE on indentation, which fails closed.
    """
    for indent, label in ((" " * 2, "two spaces"), (" " * 4, "four spaces"), ("\t", "a tab")):
        text = (
            "# Changelog\n\n## [pkg][1.0.0] — 2026-08-05\n\n### Highlights\n\n"
            "- Example config:\n\n"
            f"{indent}```toml\n{indent}not-a-highlight = true\n{indent}```\n"
        )
        assert _bullets(_groups(text)[0]) == ["Example config:"], label


def test_a_tilde_fence_is_not_closed_by_a_backtick_run():
    """A closing fence must use the SAME marker character."""
    text = """# Changelog

## [real][1.0.0] — 2026-08-05

### Highlights

- Real.

~~~markdown
```
## [fake][9.9.9] — 2026-08-06

### Highlights

- fake copy
```
~~~
"""
    assert [g["packages"][0]["name"] for g in _groups(text)] == ["real"]


def test_an_unterminated_code_fence_fails_instead_of_swallowing_the_file():
    """One stray fence would otherwise silently discard every later release.

    The drift gate cannot notice, because expected and committed values both
    come from this parser — it would agree with its own blind spot.
    """
    text = """# Changelog

## [a][1.0.0] — 2026-08-05

### Highlights

- First.

```bash
echo "fence never closed"

## [b][2.0.0] — 2026-08-06

### Highlights

- Would vanish.
"""
    try:
        build_site.project_now_highlights(text)
    except ValueError as exc:
        assert "unterminated code fence" in str(exc)
        assert "line 9" in str(exc), str(exc)
    else:  # pragma: no cover
        raise AssertionError("an unterminated fence did not fail generation")


def test_a_commented_out_release_entry_does_not_publish():
    """`changelog.md` ships a commented-out release template, so this is its real shape.

    Before comments were skipped, the entry below published its Highlights —
    trailing `-->` included — and consumed a slugger slot that `github-slugger`
    never sees, which shifts every later `-N` duplicate suffix and points source
    links at the wrong release.
    """
    text = """# Changelog

<!--
## [draft][9.9.9] — 2026-08-18

### Highlights

- Commented out; must never publish.
-->

## [real][1.0.0] — 2026-08-05

### Highlights

- Real.
"""
    groups = _groups(text)
    assert [g["packages"][0]["name"] for g in groups] == ["real"]
    assert _bullets(groups[0]) == ["Real."]


def test_a_commented_heading_consumes_no_duplicate_slug_slot():
    """Anchor suffixes must count only headings the renderer actually emits."""
    text = """# Changelog

<!--
## [core][2.3.0] — 2026-08-07
-->

## [core][2.3.0] — 2026-08-07

### Highlights

- The only real one.
"""
    releases = build_site.parse_changelog_releases(text).releases
    assert [r["anchor"] for r in releases] == ["core230--2026-08-07"]


def test_a_comment_inside_a_fenced_block_is_sample_text_not_a_comment():
    """Fenced code wins over comment syntax."""
    text = """# Changelog

## [pkg][1.0.0] — 2026-08-05

### Highlights

- Real.

```html
<!-- a sample comment that never closes
```

## [later][2.0.0] — 2026-08-06

### Highlights

- Must still publish.
"""
    assert [g["packages"][0]["name"] for g in _groups(text)] == ["later", "pkg"]


def test_a_backticked_comment_opener_does_not_swallow_later_releases():
    """A code-span mention must not open a comment or trigger the final raise.

    Without code-span precedence, this prose opened an unterminated HTML
    comment and generation failed instead of publishing the later release.
    """
    text = """# Changelog

## [first][1.0.0] — 2026-08-05

### Highlights

- First.

A note mentioning `<!--` in backticks.

## [later][2.0.0] — 2026-08-06

### Highlights

- Later.
"""
    assert [g["packages"][0]["name"] for g in _groups(text)] == ["later", "first"]


def test_backticked_comment_markers_on_separate_lines_are_both_inert():
    """Separate code-span mentions must not hide a release between them.

    A code-span-blind parser paired these mentions as an HTML comment and
    published only one of the three releases.
    """
    text = """# Changelog

## [first][1.0.0] — 2026-08-05

A note mentioning `<!--` in backticks.

## [middle][2.0.0] — 2026-08-06

A note mentioning `-->` in backticks.

## [last][3.0.0] — 2026-08-07
"""
    releases = build_site.parse_changelog_releases(text).releases
    assert [release["packages"][0]["name"] for release in releases] == [
        "first", "middle", "last",
    ]


def test_backticks_inside_a_real_comment_do_not_mask_its_closer():
    """Backticks are literal inside HTML comments, so `-->` still closes one.

    Applying the code-span mask while already inside a comment would leave this
    real comment unterminated and swallow both releases below it.
    """
    text = """# Changelog

<!--
Backticks are literal inside a comment, so this `-->` closes it.

## [first][1.0.0] — 2026-08-05

## [later][2.0.0] — 2026-08-06
"""
    releases = build_site.parse_changelog_releases(text).releases
    assert [release["packages"][0]["name"] for release in releases] == [
        "first", "later",
    ]


def test_a_backticked_comment_opener_inside_a_fence_remains_sample_text():
    """Fence handling must stay ahead of code-span-aware comment handling.

    The backtick here is deliberately UNMATCHED, so it forms no code span and
    the new mask cannot rescue this line. Only the fence can, which is what
    makes the assertion discriminating: hoisting comment handling ahead of the
    fence state machine turns this sample into a real unterminated comment and
    the later release vanishes.

    Written with a matched pair first, it was inert for two independent reasons
    and passed under both that hoist and the code-span-blind parser it was
    added to catch — a test that could not go red for the reason it named.
    """
    text = """# Changelog

```markdown
A sample mentions `<!-- without a closing backtick or closer.
```

## [real][1.0.0] — 2026-08-05
"""
    releases = build_site.parse_changelog_releases(text).releases
    assert [release["packages"][0]["name"] for release in releases] == ["real"]


def test_comment_mentions_respect_matching_backtick_run_lengths():
    """Only an equal-length backtick run closes an inline code span.

    Treating any nearby backtick as a delimiter would miss the double-backtick
    span and the single-backtick span nested inside a longer run.
    """
    text = """# Changelog

## [first][1.0.0] — 2026-08-05

A double-backtick span mentions ``<!--`` safely.

## [middle][2.0.0] — 2026-08-06

A longer span contains a single-backtick span: ``` `<!--` ```.

## [last][3.0.0] — 2026-08-07
"""
    releases = build_site.parse_changelog_releases(text).releases
    assert [release["packages"][0]["name"] for release in releases] == [
        "first", "middle", "last",
    ]


def test_an_unterminated_html_comment_fails_instead_of_swallowing_the_file():
    text = """# Changelog

<!-- opened and never closed

## [b][2.0.0] — 2026-08-06

### Highlights

- Would vanish.
"""
    try:
        build_site.project_now_highlights(text)
    except ValueError as exc:
        assert "unterminated HTML comment" in str(exc)
        assert "line 3" in str(exc), str(exc)
    else:  # pragma: no cover
        raise AssertionError("an unterminated comment did not fail generation")


def test_an_impossible_calendar_day_fails_generation():
    """`2026-02-31` passes a 1..31 range and renders as "31 February 2026"."""
    text = """# Changelog

## [pkg][1.0.0] — 2026-02-31

### Highlights

- Feb 31st.
"""
    try:
        build_site.project_now_highlights(text)
    except ValueError as exc:
        assert "impossible date" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("2026-02-31 did not fail generation")


def test_headings_inside_a_fenced_block_are_not_release_entries():
    """`#` inside a shell sample is a comment, and `-` is not a bullet."""
    text = """# Changelog

## [pkg][1.0.0] — 2026-08-05

### Highlights

- Real highlight.

```bash
## [fake][9.9.9] — 2026-08-06
- not a highlight
```
"""
    groups = _groups(text)
    assert [g["packages"][0]["name"] for g in groups] == ["pkg"]
    assert _bullets(groups[0]) == ["Real highlight."]


def test_a_wrapped_bullet_keeps_its_continuation_text():
    """Changelog bullets wrap; truncating one would cut public copy mid-sentence."""
    text = """# Changelog

## [pkg][1.0.0] — 2026-08-05

### Highlights

- A highlight whose sentence
  continues on the next line.
"""
    assert _bullets(_groups(text)[0]) == [
        "A highlight whose sentence continues on the next line."
    ]


def test_the_projection_payload_matches_a_frozen_expectation():
    """Pin the exact payload shape, not merely that a pure function is pure.

    Calling the projection twice in one process cannot fail unless module state
    mutates, so a today-based filter added to the projection would pass a
    same-process equality check. Freezing the expected payload is what actually
    fails: any clock, window, build stamp, or renamed field changes it.
    """
    assert build_site.project_now_highlights(_RELEASED) == {
        "schemaVersion": 1,
        "groups": [
            {
                "packages": [{"name": "pkg-b", "version": "1.0.0"}],
                "date": "2026-08-17",
                "heading": "[pkg-b][1.0.0] — 2026-08-17",
                "changelogAnchor": "pkg-b100--2026-08-17",
                "highlights": [
                    {
                        "source": "Released highlight that must publish.",
                        "segments": [
                            {
                                "type": "text",
                                "value": "Released highlight that must publish.",
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_markdown_emphasis_becomes_typed_segments_not_raw_html():
    """The renderer receives typed segments, never a Markdown or HTML string.

    Raw Markdown would print literal asterisks on a public page; a raw HTML
    string would give an authored changelog an injection seam into that page.
    """
    segs = build_site.highlight_segments("**Lead.** Body with `code`.")
    assert segs == [
        {"type": "strong", "value": "Lead."},
        {"type": "text", "value": " Body with "},
        {"type": "code", "value": "code"},
        {"type": "text", "value": "."},
    ], segs


def test_an_unsupported_inline_form_stays_literal_rather_than_vanishing():
    """Text on the page is never less than the source says."""
    segs = build_site.highlight_segments("Plain _em_ text")
    assert "".join(s["value"] for s in segs) == "Plain _em_ text"


# ── The launch-seed window (AUTHORING rule, not a render filter) ───────────

def test_the_launch_window_is_seven_calendar_days_and_inclusive_at_both_ends():
    """Launch day and launch-day-minus-six are in; minus-seven is out."""
    start, end = build_site.launch_window("2026-08-18")
    assert (start, end) == ("2026-08-12", "2026-08-18")
    assert start <= "2026-08-18" <= end          # launch day itself
    assert start <= "2026-08-12" <= end          # day minus six
    assert not (start <= "2026-08-11" <= end)    # day minus seven


def test_the_window_does_not_filter_the_projection():
    """A released highlight older than the window still publishes.

    The window governs which entries should have GAINED a Highlights block by
    launch, not what `/now/` may show afterwards. Filtering at render time would
    make the page change at midnight from unchanged source.
    """
    old = """# Changelog

## [pkg][1.0.0] — 2020-01-01

### Highlights

- An old but released highlight.
"""
    assert len(_groups(old)) == 1


# ---------------------------------------------------------------------------
# /now/ against the real repository tree
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CHANGELOG = _REPO_ROOT / "docs" / "product" / "changelog.md"
# Measured at 171 releases on 2026-08-27. A floor of 130 is about 76% of that,
# leaving headroom for ordinary changelog churn while still detecting collapse.
_MIN_REAL_CHANGELOG_RELEASES = 130
_PROJECTION = _REPO_ROOT / "web" / "src" / "lib" / "now-highlights.generated.json"
_MARKETING_SHARED_CHROME_PROJECTION = (
    _REPO_ROOT / "web" / "src" / "lib" / "shared-chrome.generated.json"
)
_DOCS_SHARED_CHROME_PROJECTION = (
    _REPO_ROOT / "docs-site" / "src" / "shared-chrome.generated.json"
)
_EMITTED_CHANGELOG = _REPO_ROOT / "build" / "docs" / "changelog" / "index.html"

# The day `/now/` launched. A historical fact, deliberately pinned rather than
# computed: the seven-day rule selected which entries were seeded AT LAUNCH, and
# a rolling window would turn "a released entry may omit Highlights" — which the
# contract explicitly allows — into a CI failure every time one did.
_LAUNCH_DATE = "2026-08-18"


def test_the_committed_now_projection_matches_the_changelog_source():
    """The committed projection is in sync with the changelog it derives from.

    The marketing build reads the committed JSON, and the workflow projects it in
    a pass that runs BEFORE that build. Without this gate a changelog edit could
    ship with a stale public page and nothing would say so.
    """
    import json

    expected = build_site.project_now_highlights(
        _CHANGELOG.read_text(encoding="utf-8")
    )
    committed = json.loads(_PROJECTION.read_text(encoding="utf-8"))
    assert committed == expected, (
        "web/src/lib/now-highlights.generated.json is stale — "
        "run `python3 tools/build-site.py --journeys-only`"
    )


def test_the_committed_marketing_shared_chrome_projection_matches_site_toml():
    """The committed marketing renderer input remains derived from site.toml."""
    build_site.assert_marketing_shared_chrome_projection_current(
        _shared_chrome_fixture(), _MARKETING_SHARED_CHROME_PROJECTION
    )


def test_the_committed_docs_shared_chrome_projection_matches_site_toml():
    """The docs build input remains derived from the renderer-neutral source."""
    build_site.assert_docs_shared_chrome_projection_current(
        _shared_chrome_fixture(), _DOCS_SHARED_CHROME_PROJECTION
    )


def test_the_real_changelog_has_no_silently_withheld_highlights():
    """Turn two advisory diagnostics into a required-suite failure.

    Failing closed means a highlight can stop publishing without anything going
    red — the note lands in the `pages.yml` DEPLOY log, not on a PR check, so the
    author sees a missing paragraph on the page and no failure anywhere. Both of
    these are zero on the real changelog today, so pinning them is free and makes
    every future occurrence an actionable failure naming the heading and line.

    Deliberately NOT `withheld_unreleased`: highlights sitting under
    `[Unreleased]` are the normal pre-release state the changelog preamble tells
    authors to expect, and they publish when the entry is promoted at release
    time. Pinning that would fail the build for doing the documented thing.
    """
    rel = _CHANGELOG.relative_to(_REPO_ROOT).as_posix()
    parsed = build_site.parse_changelog_releases(
        _CHANGELOG.read_text(encoding="utf-8")
    )
    # The message is built from the diagnostics rather than left to pytest's
    # tuple repr: `[(813, 4, 'Highlights')] == []` surfaces the line number but
    # makes the reader guess which number is the line and which the level.
    misplaced = [
        f"{rel}:{lineno}: '{'#' * level} {title}' is not its release entry's "
        "immediate child, so its bullets do not publish — move it one level up"
        for lineno, level, title in parsed.diagnostics["misplaced_highlights"]
    ]
    assert not misplaced, "\n".join(misplaced)

    regions = [
        f"{rel}:{lineno}: heading {title!r} reads as Unreleased, so every entry "
        "beneath it is withheld from /now/ — reword it, or use the canonical "
        "'## [Unreleased]' if that is what you meant"
        for lineno, title in parsed.diagnostics["unreleased_regions"]
    ]
    assert not regions, "\n".join(regions)


def test_the_real_changelog_parser_keeps_a_sane_release_population():
    """A parser state leak must not silently collapse the real release history."""
    parsed = build_site.parse_changelog_releases(
        _CHANGELOG.read_text(encoding="utf-8")
    )
    actual = len(parsed.releases)
    assert actual >= _MIN_REAL_CHANGELOG_RELEASES, (
        f"the real changelog parsed only {actual} releases, below the safety floor "
        f"of {_MIN_REAL_CHANGELOG_RELEASES}; parser state likely swallowed the "
        "remaining release history — inspect HTML-comment and fenced-code handling "
        "in tools/build-site.py::parse_changelog_releases"
    )


def test_no_projected_release_heading_lives_under_an_unreleased_region():
    """Check the page's provenance against the RAW source, not the parser again.

    Re-asserting the parser's own predicate over the parser's own output cannot
    fail for the reason that matters. This instead walks the raw file, tracking
    `## [Unreleased]` regions by heading level independently, and requires every
    projected heading to appear outside all of them.
    """
    import re

    text = _CHANGELOG.read_text(encoding="utf-8")
    payload = build_site.project_now_highlights(text)
    assert payload["groups"], "the real changelog projects no highlight at all"

    released_headings, unreleased_headings = set(), set()
    region_level = None
    for raw in text.splitlines():
        m = re.match(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", raw)
        if m is None:
            continue
        level, title = len(m.group(1)), m.group(2).strip()
        if region_level is not None and level <= region_level:
            region_level = None
        if re.match(r"^\[?unreleased\]?(\W|$)", title, re.IGNORECASE):
            region_level = level
            continue
        (unreleased_headings if region_level is not None else released_headings).add(title)

    assert unreleased_headings, "fixture drift: no Unreleased region found in the source"
    for group in payload["groups"]:
        assert group["heading"] in released_headings, group["heading"]
        assert group["heading"] not in unreleased_headings, group["heading"]


def test_the_launch_seed_covers_exactly_the_released_entries_in_its_window():
    """AC5, recorded as measured fact rather than restated as a rule.

    On the launch date the seven-day window held exactly ONE released entry —
    `governance-extras 0.9.7`. Every other entry dated inside that window sits
    beneath `[Unreleased]` and is therefore ineligible however recent it looks.
    Both halves are asserted: the eligible entry was seeded, and the ineligible
    ones were not silently promoted to make the page look busier.
    """
    text = _CHANGELOG.read_text(encoding="utf-8")
    start, end = build_site.launch_window(_LAUNCH_DATE)
    releases = build_site.parse_changelog_releases(text).releases
    in_window = [r for r in releases if start <= r["date"] <= end]

    released = [r for r in in_window if not r["unreleased"]]
    assert [r["anchor"] for r in released] == [
        "governance-extras097--2026-08-16"
    ], [r["heading"] for r in released]
    assert all(r["highlights"] for r in released), "a seeded entry lost its Highlights"

    unreleased = [r for r in in_window if r["unreleased"]]
    assert unreleased, "fixture drift: the window should still hold Unreleased entries"
    groups = build_site.project_now_highlights(text)["groups"]
    projected = {g["changelogAnchor"] for g in groups}
    assert not projected & {r["anchor"] for r in unreleased}

    # AC5 says "all AND ONLY", and the "only" half is about the LAUNCH SEED, not
    # about everything `/now/` will ever show. Quantifying over `groups` would
    # make the first post-launch highlight fail a required gate, and would
    # contradict both `test_the_window_does_not_filter_the_projection` and the
    # spec clause saying the projection applies no date window. Scoped to the
    # seeded anchors instead: every entry seeded AT LAUNCH came from the window.
    seeded = {r["anchor"] for r in released}
    assert seeded <= projected, sorted(seeded - projected)
    for group in groups:
        if group["changelogAnchor"] in seeded:
            assert start <= group["date"] <= end, group["heading"]


def test_release_anchors_match_the_emitted_page_one_for_one_in_order():
    """Full-corpus, ORDER-SENSITIVE correspondence against every emitted heading.

    Three weaker forms were tried and each let a real defect through:

    - Membership ("every anchor exists somewhere on the page") passes when two
      identical headings swap their `-N` suffixes, because both ids exist either
      way.
    - Resolving each anchor to its heading TEXT cannot separate duplicates —
      duplicates are duplicates precisely because their text is identical.
    - Checking only the anchors that actually PROJECT shrinks the corpus from 122
      release headings to the one group `/now/` currently shows, whose base is
      unique. Deleting `_Slugger`'s duplicate handling outright passed every
      test in both suites under that form.

    So this compares the whole sequence, in document order, against the emitted
    page. `pages.yml` runs it after the docs build; `build-check.yml` has no site
    build, hence the skip.
    """
    import re

    if not _EMITTED_CHANGELOG.exists():
        import os

        import pytest

        # Keyed on a DEDICATED variable, not on `CI`. GitHub Actions sets `CI` in
        # every job, and this module also runs in `gate-main`, which has no site
        # build — so gating on `CI` failed that job for a legitimately absent
        # artifact. Only the `pages.yml` step that builds the site sets
        # `REQUIRE_EMITTED_CHANGELOG`, and there a missing artifact means the
        # wiring broke: a fully-skipped pytest selection exits 0, which would
        # report success for the only check holding the duplicate-slug counter
        # against reality.
        message = (
            "needs the combined build: python3 tools/build-site.py && "
            "npm run build --prefix web && npm run build --prefix docs-site"
        )
        if os.environ.get("REQUIRE_EMITTED_CHANGELOG"):
            raise AssertionError(
                f"emitted changelog absent where it is required — {message}"
            )
        pytest.skip(message)

    page = _EMITTED_CHANGELOG.read_text(encoding="utf-8")
    emitted: list[tuple[str, str]] = []
    for match in re.finditer(
        r"<h[1-6][^>]*\bid=\"([^\"]+)\"[^>]*>(.*?)</h[1-6]>", page, re.S
    ):
        anchor, inner = match.group(1), match.group(2)
        if anchor.startswith("starlight__"):
            continue
        text = re.sub(r"<[^>]+>", "", inner)
        text = (
            text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&#39;", "'")
        )
        emitted.append((anchor, " ".join(text.split())))

    releases = build_site.parse_changelog_releases(
        _CHANGELOG.read_text(encoding="utf-8")
    ).releases
    assert releases, "no release entries parsed from the real changelog"

    expected = [(r["anchor"], " ".join(r["heading"].split())) for r in releases]
    # Starlight appends an anchor-link affordance, so match on the heading text
    # the parser saw being a prefix of the emitted text.
    actual = [
        (anchor, text)
        for anchor, text in emitted
        if any(anchor == want for want, _ in expected)
        or any(text.startswith(want_text) and want_text for _, want_text in expected)
    ]
    got_anchors = [a for a, _ in actual]
    want_anchors = [a for a, _ in expected]
    assert got_anchors == want_anchors, (
        "release anchors diverge from the emitted page in id or order:\n"
        f"  first mismatch at {next((i for i, (g, w) in enumerate(zip(got_anchors, want_anchors, strict=False)) if g != w), 'length')}\n"
        f"  parser: {want_anchors[:6]}\n  emitted: {got_anchors[:6]}"
    )
    # And the duplicates specifically, since they are the only place the parser's
    # `-N` counter and github-slugger can disagree.
    suffixed = [a for a in want_anchors if a.endswith("-1")]
    assert suffixed, "fixture drift: the changelog should still repeat two headings"
    for anchor in suffixed:
        base = anchor[: -len("-1")]
        assert base in got_anchors, base
        assert got_anchors.index(base) < got_anchors.index(anchor)


def test_the_public_work_surface_is_gone_from_marketing_inputs():
    """`/work/` is removed from routes and the generated marketing input.

    Asserted over source rather than the build so it holds in the required suite,
    which runs without a site build.
    """
    forbidden = [
        _REPO_ROOT / "web" / "src" / "pages" / "work",
        _REPO_ROOT / "web" / "src" / "components" / "work",
        _REPO_ROOT / "web" / "src" / "lib" / "work-index.ts",
        _REPO_ROOT / "web" / "src" / "test" / "work-index.test.ts",
        _REPO_ROOT / "tools" / "export_work_index.py",
        _REPO_ROOT / "tools" / "test_export_work_index.py",
    ]
    present = [str(p.relative_to(_REPO_ROOT)) for p in forbidden if p.exists()]
    assert not present, f"retired work-index surface still present: {present}"

    projection = json.loads(
        _MARKETING_SHARED_CHROME_PROJECTION.read_text(encoding="utf-8")
    )
    destinations = [
        link
        for section in (
            projection["header"],
            *(group["destinations"] for group in projection["footer"]),
        )
        for link in section
    ]
    assert all(link["target"] != "/work/" for link in destinations)
    assert any(link["id"] == "now" and link["target"] == "/now/" for link in destinations)

    # The projection check above cannot see a hand-written literal reintroduced
    # into a component, and the emitted-output check that would runs only when a
    # build exists. Keep a source-level scan so the required suite still fails.
    layout = _REPO_ROOT / "web" / "src" / "components" / "layout"
    marketing_chrome = [layout / "SiteNav.astro", layout / "SiteFooter.astro"]
    with_work = [
        str(path.relative_to(_REPO_ROOT))
        for path in marketing_chrome
        if "/work/" in path.read_text(encoding="utf-8")
    ]
    assert not with_work, f"marketing chrome reintroduced a /work/ literal: {with_work}"


# Git blob hashes of the frozen m6 artifacts, recorded from `origin/main` at
# `0152c1da` before this spec shipped. AC11 promises they stay BYTE-unchanged, so
# the gate has to compare bytes: asserting the files exist and still say
# "Shipped" leaves every paragraph free to be rewritten.
_FROZEN_M6_BLOBS = {
    "docs/specs/m6-astro-work-index/spec.md": "7432ed7f5be1a744a2371c659bbe2456fc4f765b",
    "docs/specs/m6-astro-work-index/plan.md": "cc00d0b577120423d0e746a797a532462422cb26",
}


def test_the_frozen_work_index_spec_remains_byte_unchanged():
    """AC11: the shipped m6 spec and plan are historical provenance, not living docs.

    Compared by content hash rather than by "does it still exist and say
    Shipped", which cannot fail for a rewrite. Uses git's own blob-id function so
    the recorded values are reproducible with `git hash-object <path>`.
    """
    import hashlib

    for rel, expected in _FROZEN_M6_BLOBS.items():
        raw = (_REPO_ROOT / rel).read_bytes()
        # git blob id = sha1("blob <len>\0" + bytes). `usedforsecurity=False`
        # because this is content ADDRESSING, not a security control — the
        # algorithm is dictated by git's object format, not chosen here.
        actual = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw,
            usedforsecurity=False,
        ).hexdigest()
        assert actual == expected, (
            f"{rel} is no longer byte-identical to its frozen record "
            f"(expected {expected}, got {actual}); AC11 forbids rewriting it"
        )

    # AC11's other half: the LIVING index is where supersession is recorded,
    # since the frozen artifacts may not be annotated. Nothing else asserts it,
    # so the pointer could be reverted silently.
    index = (_REPO_ROOT / "docs" / "specs" / "README.md").read_text(encoding="utf-8")
    m6_row = next(
        line for line in index.splitlines() if "m6-astro-work-index/" in line
    )
    assert "site-now-surface/spec.md" in m6_row, m6_row
