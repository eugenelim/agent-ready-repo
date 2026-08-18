"""Tests for guide-routing and /now/ projection in tools/build-site.py.

Covers: frontmatter parsing, guide-metadata stripping, slug-override routing,
alias redirect-stub generation, docs/guides/ exclusion, generation's
independence from the marketing design-token file, and the released-changelog
Highlights projection that feeds the public `/now/` route.
"""
from __future__ import annotations

import importlib.util
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
              "web/src/styles"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
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


def test_an_entry_without_a_date_is_not_a_release():
    """Version but no date is not publishable — the contract requires both."""
    text = """# Changelog

## [pkg][1.0.0]

### Highlights

- No date, so not released.
"""
    assert _groups(text) == []


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


def test_the_projection_is_deterministic_for_identical_source():
    """Repeated projection of the same bytes yields byte-identical output.

    This is what lets the page be generated in CI without a clock: the payload
    carries no date-of-build and no window evaluated at build time.
    """
    import json

    once = json.dumps(build_site.project_now_highlights(_RELEASED), sort_keys=False)
    twice = json.dumps(build_site.project_now_highlights(_RELEASED), sort_keys=False)
    assert once == twice
    assert "launchDate" not in once


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
_PROJECTION = _REPO_ROOT / "web" / "src" / "lib" / "now-highlights.generated.json"
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


def test_every_projected_release_is_released_and_carries_highlights():
    """Nothing on the public page comes from an `[Unreleased]` entry."""
    releases = build_site.parse_changelog_releases(
        _CHANGELOG.read_text(encoding="utf-8")
    )
    by_anchor = {r["anchor"]: r for r in releases}
    payload = build_site.project_now_highlights(
        _CHANGELOG.read_text(encoding="utf-8")
    )
    assert payload["groups"], "the real changelog projects no highlight at all"
    for group in payload["groups"]:
        source = by_anchor[group["changelogAnchor"]]
        assert not source["unreleased"], group["heading"]
        assert source["highlights"], group["heading"]


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
    releases = build_site.parse_changelog_releases(text)
    in_window = [r for r in releases if start <= r["date"] <= end]

    released = [r for r in in_window if not r["unreleased"]]
    assert [r["anchor"] for r in released] == [
        "governance-extras097--2026-08-16"
    ], [r["heading"] for r in released]
    assert all(r["highlights"] for r in released), "a seeded entry lost its Highlights"

    unreleased = [r for r in in_window if r["unreleased"]]
    assert unreleased, "fixture drift: the window should still hold Unreleased entries"
    projected = {
        g["changelogAnchor"]
        for g in build_site.project_now_highlights(text)["groups"]
    }
    assert not projected & {r["anchor"] for r in unreleased}


def test_the_slugger_reproduces_every_emitted_changelog_anchor():
    """Source links must land on the heading Starlight actually emitted.

    Starlight anchors headings with `github-slugger`, including its `-N` suffix
    for repeats — `changelog.md` repeats `[core][2.3.0] — 2026-08-07`, so a slug
    derived from heading text alone would send a Now link to the wrong release.
    Reproducing the algorithm is only credible if checked against the real
    emitted page, which is what this does.
    """
    import html
    import re

    if not _EMITTED_CHANGELOG.exists():
        import pytest

        pytest.skip(
            "needs the combined build: python3 tools/build-site.py && "
            "npm run build --prefix web && npm run build --prefix docs-site"
        )

    emitted = set()
    page = _EMITTED_CHANGELOG.read_text(encoding="utf-8")
    for level in (1, 2, 3, 4, 5, 6):
        for anchor, _ in re.findall(
            rf'<h{level}[^>]*id="([^"]+)"[^>]*>(.*?)</h{level}>', page, re.S
        ):
            emitted.add(anchor)

    releases = build_site.parse_changelog_releases(
        _CHANGELOG.read_text(encoding="utf-8")
    )
    assert releases, "no release entries parsed from the real changelog"
    missing = [r["anchor"] for r in releases if r["anchor"] not in emitted]
    assert not missing, f"anchors absent from the emitted page: {missing[:5]}"
    assert html  # the import documents why the emitted text is unescaped upstream


def test_the_public_work_surface_is_gone_from_the_marketing_source():
    """`/work/` is removed outright — no page, no component, no exporter, no redirect.

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

    nav = (
        _REPO_ROOT / "web" / "src" / "components" / "layout" / "SiteNav.astro"
    ).read_text(encoding="utf-8")
    assert "/work/" not in nav
    assert "withBase('/now/')" in nav


def test_the_frozen_work_index_spec_remains_intact_as_provenance():
    """The shipped m6 spec/plan stay as history; only the living index moves on."""
    spec = _REPO_ROOT / "docs" / "specs" / "m6-astro-work-index" / "spec.md"
    plan = _REPO_ROOT / "docs" / "specs" / "m6-astro-work-index" / "plan.md"
    assert spec.exists() and plan.exists()
    assert "**Status:** Shipped" in spec.read_text(encoding="utf-8")
