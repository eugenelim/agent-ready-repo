"""Tests for generated sidebar assembly in tools/build-site.py.

Covers T7 of docs/specs/guides-sidebar-generation. These are the criteria that
actually deliver the feature, asserted against the real tree:

- AC2  set equality, not a subset — a subset check passes while dropping pages
- AC9  (slug, label) pair equality — a slug-only check is blind to the 90
       label regressions filename derivation would cause
- AC10 determinism under a shuffled enumerator
"""
from __future__ import annotations

import importlib.util
import json
import random
import sys
import tomllib
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent / "build-site.py"
_spec = importlib.util.spec_from_file_location("build_site", _SCRIPT)
build_site = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["build_site"] = build_site
_spec.loader.exec_module(build_site)  # type: ignore[union-attr]

REPO_ROOT = Path(__file__).resolve().parent.parent
with (REPO_ROOT / "site.toml").open("rb") as _f:
    # Read rather than hand-copy: a seventh super-group must not leave the
    # AC8 nesting guard silently blind to it.
    SUPER_GROUP_LABELS = {g["label"] for g in tomllib.load(_f).get("groups", [])}


def _pairs(node) -> list[tuple[str, str]]:
    out = []
    for item in node.get("items", []):
        if "slug" in item:
            out.append((item["slug"], item["label"]))
        else:
            out.extend(_pairs(item))
    return out


def _guides_group() -> dict:
    return build_site.build_guides_sidebar_group(REPO_ROOT, REPO_ROOT / "site.toml")


# ---------------------------------------------------------------------------

def test_sidebar_includes_pack_catalogue_and_guides(tmp_path):
    packs = [{"slug": "core", "display_name": "Core", "group": "Foundation"}]
    out = tmp_path / "sidebar-config.json"
    build_site.generate_sidebar_config(packs, out, guides_group=_guides_group())
    sidebar = json.loads(out.read_text(encoding="utf-8"))
    labels = [g["label"] for g in sidebar]
    assert "Pack Catalogue" in labels
    assert "Foundation" in labels
    assert labels[-1] == "Guides"


def test_guides_group_slugs_equal_eligible_slugs():
    """Set equality over the Guides groups only — pack-catalogue and top-level
    slugs are outside this set."""
    records = build_site.build_guide_inventory(REPO_ROOT / "guides")
    eligible = {r["slug"] for r in records if r["nav_eligible"]}
    projected = {slug for slug, _ in _pairs(_guides_group())}
    assert projected == eligible
    assert "guides/AGENTS" not in projected


def test_no_baseline_pair_regressed():
    """Every frozen (slug, label) pair survives generation unchanged."""
    baseline = build_site.load_guide_baseline(REPO_ROOT / "guide-nav-baseline.toml")
    # No count assertion: guides/AGENTS.md documents the registry as
    # shrinking as pages adopt `title:`, so pinning its size would forbid
    # the workflow. The pair loop below is the actual guard.
    assert baseline
    projected = dict(_pairs(_guides_group()))
    regressed = {
        slug: (label, projected.get(slug, "<ABSENT>"))
        for slug, label in baseline.items()
        if projected.get(slug) != label
    }
    assert not regressed, f"labels or pages regressed: {regressed}"


def test_guides_nesting_is_one_group_level():
    """Pack groups sit directly under Guides; the six site.toml super-group
    labels are not inherited, which would push nesting to five levels."""
    guides = _guides_group()
    for item in guides["items"]:
        assert item.get("label") not in SUPER_GROUP_LABELS
        for child in item.get("items", []):
            # A pack group's children are pages or kind buckets — never groups
            # of groups.
            for grandchild in child.get("items", []):
                assert "slug" in grandchild, "kind buckets must contain pages only"


def test_shuffled_enumerator_is_byte_identical():
    """Shuffle the injected enumerator, not a re-glob — otherwise the test
    passes because sorted() is stable, having exercised nothing."""
    guides_root = REPO_ROOT / "guides"
    paths = list(guides_root.rglob("*.md"))
    rng = random.Random(1234)

    renders = []
    for _ in range(2):
        shuffled = list(paths)
        rng.shuffle(shuffled)
        records = build_site.build_guide_inventory(
            guides_root, enumerator=lambda _root, p=shuffled: p)
        with (REPO_ROOT / "site.toml").open("rb") as f:
            groups = tomllib.load(f).get("guide_groups", [])
        baseline = build_site.load_guide_baseline(REPO_ROOT / "guide-nav-baseline.toml")
        renders.append(json.dumps(
            build_site.project_guide_sidebar(records, groups, baseline), indent=2))

    assert renders[0] == renders[1]


def test_missing_baseline_degrades_without_raising(tmp_path):
    assert build_site.load_guide_baseline(tmp_path / "absent.toml") == {}


# ---------------------------------------------------------------------------
# Real-tree invariants.
#
# The synthetic fixtures below/elsewhere document intent; these constrain it.
# Two reviewers independently showed that deleting the nav-eligibility rule or
# the duplicate-slug tie-break left every other test green while the published
# sidebar regressed — a test that only moves with the code cannot catch the
# code being wrong.
# ---------------------------------------------------------------------------

def _all_groups(node):
    """Yield every group node (anything carrying `items`), depth-first."""
    for item in node.get("items", []):
        if "items" in item:
            yield item
            yield from _all_groups(item)


def test_nav_ineligible_set_is_exactly_the_declared_exceptions():
    """Pinned against an independent expectation, not against the projection —
    AC2's set equality compares the generator with itself, so it moves with an
    eligibility bug rather than catching one."""
    records = build_site.build_guide_inventory(REPO_ROOT / "guides")
    ineligible = {
        r["source_path"].relative_to(REPO_ROOT / "guides").as_posix()
        for r in records if not r["nav_eligible"]
    }
    assert ineligible == {
        "AGENTS.md",
        "_shared/explanation/README.md",
        "_shared/how-to/README.md",
        "_shared/reference/README.md",
        "_shared/tutorials/README.md",
    }, "the reader-facing carve-out changed — update spec § Intent in the same PR"


def test_no_sibling_label_collision_anywhere_in_the_real_tree():
    """The collision that shipped twice was a kind-index page named "How-to"
    sitting beside the "How-to" bucket. It only arises in the real tree, so a
    synthetic fixture cannot reproduce it."""
    guides = _guides_group()
    for group in [guides, *_all_groups(guides)]:
        labels = [i["label"] for i in group.get("items", [])]
        assert len(labels) == len(set(labels)), (
            f"sibling label collision in {group.get('label')!r}: {labels}")


def test_every_guides_directory_is_declared_in_site_toml():
    """AC8. An undeclared directory silently takes the title-cased fallback and
    is appended last — `iac-terraform` would read "Iac Terraform" rather than
    its curated "IaC (Terraform)"."""
    dirs = {p.name for p in (REPO_ROOT / "guides").iterdir() if p.is_dir()}
    with (REPO_ROOT / "site.toml").open("rb") as f:
        declared = {g["dir"] for g in tomllib.load(f).get("guide_groups", [])}
    assert dirs == declared, (
        f"undeclared: {sorted(dirs - declared)}; "
        f"stale: {sorted(declared - dirs)}")


def test_atlassian_cross_kind_run_survives():
    """The independent regression witness — a threaded sequence this PR did not
    author, so it cannot be tautological with the arc it added."""
    guides = _guides_group()
    atlassian = next(g for g in guides["items"] if g.get("label") == "Atlassian")
    direct = [i["slug"] for i in atlassian["items"] if "slug" in i]
    assert direct[:5] == [
        "guides/atlassian",
        "guides/atlassian/tutorials/review-your-team-backlog",
        "guides/atlassian/how-to/work-with-jira",
        "guides/atlassian/reference/atlassian-skills",
        "guides/atlassian/explanation/atlassian-pack",
    ], "the ordered run must stay flat and ahead of the kind buckets"


def test_duplicate_slug_resolves_deterministically(tmp_path):
    """The tie-break AC10 depends on. The real tree has no duplicates, so the
    shuffled-enumerator test exercises nothing about it."""
    root = tmp_path / "guides"
    for name, title in (("a.md", "A"), ("b.md", "B")):
        p = root / "pack" / "how-to" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"---\ntitle: {title}\nsummary: s\npack: pack\nkind: how-to\n"
                     f"slug: guides/pack/how-to/same\n---\n", encoding="utf-8")

    paths = sorted(root.rglob("*.md"))
    forward = build_site.build_guide_inventory(root, enumerator=lambda _r: paths)
    reverse = build_site.build_guide_inventory(
        root, enumerator=lambda _r: list(reversed(paths)))
    assert [r["title"] for r in forward] == [r["title"] for r in reverse]


# --- Degradation (not real-tree) ---------------------------------------------

def test_malformed_baseline_entry_is_skipped_not_raised(tmp_path):
    p = tmp_path / "baseline.toml"
    p.write_text('[[entry]]\nslug = "guides/a"\n\n'
                 '[[entry]]\nslug = "guides/b"\nlabel = "Bee"\n', encoding="utf-8")
    assert build_site.load_guide_baseline(p) == {"guides/b": "Bee"}


# --------------------------------------------------------------------------
# spec/guide-title-clarity — the nine reviewed title decisions
# --------------------------------------------------------------------------
#
# Raw-string comparison on purpose. `tools/lint-guide-titles.py` enforces only the
# RELATIONAL title↔H1 match through a `normalise()` that casefolds and strips
# punctuation, so it passes just as happily on `Run an Audit` / `# Run an Audit`.
# Three of the four decisions here are substantially casing changes, so a
# normalised comparison would accept `Run A Frontend Audit` and pin nothing.
#
# Without these, reverting any approved title, any of the five controls, or the
# two baseline deletions fails nothing in the suite: four of the five controls
# have no `guide-nav-baseline.toml` entry, so the pair guard does not reach them.

# The four approved strings, frozen by the brief's decision 7.
APPROVED_TITLES = {
    "guides/frontend-engineering/how-to/page-screen-contract.md":
        "Write a page or screen contract",
    "guides/frontend-engineering/how-to/run-an-audit.md":
        "Run a frontend audit",
    "guides/frontend-engineering/tutorials/scaffold-a-component.md":
        "Scaffold a component from a screen brief",
    "guides/iac-terraform/README.md":
        "Terraform and OpenTofu guides",
}
# The five reviewed titles the same decision holds UNCHANGED.
# Read from the tree, not from memory: an earlier draft of this dict guessed the
# wording and the test caught it.
CONTROL_TITLES = {
    "guides/_shared/how-to/install-user-scope-pack-into-codex.md":
        "How to install a user-scope pack into Codex",
    "guides/_shared/how-to/install-user-scope-pack-into-kiro.md":
        "How to install a user-scope pack into Kiro",
    "guides/atlassian/how-to/authenticate-jira-confluence-with-sso-cookies.md":
        "Authenticate Jira and Confluence with an SSO web session",
    "guides/frontend-engineering/reference/frontend-engineering.md":
        "Frontend Engineering Pack",
    "guides/governance-extras/how-to/new-adr.md":
        "How to record a decision with an ADR",
}
# Slugs whose baseline entry was DELETED so the label resolves from frontmatter.
# The expected label is looked up in APPROVED_TITLES rather than restated: two
# copies of a string that must stay identical is one copy too many.
DEBASELINED_SLUGS = {
    "guides/frontend-engineering/tutorials/scaffold-a-component":
        "guides/frontend-engineering/tutorials/scaffold-a-component.md",
    "guides/frontend-engineering/how-to/run-an-audit":
        "guides/frontend-engineering/how-to/run-an-audit.md",
}
# AC9: the pack index's link TEXT for the three retitled guides. Distinct from
# the frontmatter pins above — a reader arrives through this table, and nothing
# else in the repo compares Markdown link text against anything.
PACK_INDEX_LINKS = (
    "how-to/page-screen-contract.md",
    "how-to/run-an-audit.md",
    "tutorials/scaffold-a-component.md",
)
PACK_INDEX = "guides/frontend-engineering/README.md"
# The retired wording, which must not survive in the four sources.
RETIRED_STRINGS = (
    "Write a Page/Screen Contract",
    "Run an Audit",
    "Scaffold a Component",
    "IaC (Terraform) guides",
)


def _frontmatter_title(rel: str) -> str:
    """The parsed title, via the same parser the generator uses.

    NOT the raw right-hand side: that pins YAML quoting as well as wording, so
    requoting a title without changing a character of it would fail a test whose
    subject is the wording. `guide-metadata-completion` rewrites 125 guide
    frontmatter rows next, which is exactly when that would have misfired.
    """
    fm = build_site._parse_frontmatter(
        (REPO_ROOT / rel).read_text(encoding="utf-8")
    )
    title = fm.get("title")
    return title if isinstance(title, str) else ""


def _body_h1(rel: str) -> str:
    for line in (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def test_approved_guide_titles_are_exact():
    """The four decisions, compared raw — casing and punctuation included."""
    actual = {rel: _frontmatter_title(rel) for rel in APPROVED_TITLES}
    assert actual == APPROVED_TITLES


def test_approved_titles_match_their_body_h1():
    """Frontmatter and H1 move together; a CI gate asserts it, so does this."""
    mismatched = {rel: (_frontmatter_title(rel), _body_h1(rel))
                  for rel in APPROVED_TITLES
                  if _frontmatter_title(rel) != _body_h1(rel)}
    assert not mismatched, f"title/H1 drift: {mismatched}"


def test_reviewed_control_titles_are_unchanged():
    """The five titles the same decision reviewed and chose to KEEP.

    Four of these carry no baseline entry, so nothing else in the suite would
    notice them being reworded alongside a future title sweep.
    """
    actual = {rel: _frontmatter_title(rel) for rel in CONTROL_TITLES}
    assert actual == CONTROL_TITLES


def test_retired_title_strings_absent_from_the_four_sources():
    """Path-scoped: the retired wording legitimately survives as provenance in the
    changelogs, the brief, `workspace.toml`, and the lint fixtures."""
    offenders = []
    for rel in APPROVED_TITLES:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        offenders += [f"{rel}: {s}" for s in RETIRED_STRINGS if s in text]
    assert not offenders, offenders


def test_debaselined_slugs_resolve_their_label_from_frontmatter():
    """The baseline entries were DELETED, not relabelled.

    Relabelling would have been tautological — `test_no_baseline_pair_regressed`
    loads the same file it compares against — so this asserts the emitted sidebar
    label equals the frontmatter title with no baseline entry backing it.
    """
    baseline = build_site.load_guide_baseline(REPO_ROOT / "guide-nav-baseline.toml")
    projected = dict(_pairs(_guides_group()))
    for slug, source in DEBASELINED_SLUGS.items():
        want = APPROVED_TITLES[source]
        assert slug not in baseline, f"{slug} must have no baseline entry"
        assert projected.get(slug) == want, (slug, projected.get(slug), want)


def test_pack_index_link_text_names_the_approved_titles():
    """AC9: the three link labels in the frontend-engineering pack index.

    Separate from the frontmatter pins: a reader reaches these guides through
    this table, and no other check in the repo compares Markdown link TEXT
    against anything — `check-rendered-site-links.py` validates targets only.
    The expected wording is looked up in APPROVED_TITLES so the label and the
    page title cannot drift apart.
    """
    text = (REPO_ROOT / PACK_INDEX).read_text(encoding="utf-8")
    for target in PACK_INDEX_LINKS:
        want = APPROVED_TITLES[f"guides/frontend-engineering/{target}"]
        assert f"[{want}]({target})" in text, (
            f"{PACK_INDEX} must link to {target} with the text {want!r}"
        )
