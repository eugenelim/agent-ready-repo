#!/usr/bin/env python3
"""
Aggregate repo content into docs-site/src/content/docs/ for the Starlight build.

Copies:
  packs/*/README.md         → docs-site/src/content/docs/packs/<name>.md
  guides/**                 → docs-site/src/content/docs/guides/**
                              (README.md renamed to index.md; frontmatter injected)
  docs/product/changelog.md → docs-site/src/content/docs/changelog.md (links rewritten)
  CONTRIBUTING.md           → docs-site/src/content/docs/contributing.md (links rewritten)

Generates:
  docs-site/src/content/docs/packs/index.md  (pack catalogue summary page)

Usage:
  python tools/build-site.py
  python tools/build-site.py --dry-run
  python tools/build-site.py --clean
"""
import argparse
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
SITE_DOCS = REPO_ROOT / "docs-site" / "src" / "content" / "docs"
GITHUB_BASE = "https://github.com/eugenelim/agent-ready-repo/blob/main"
SITE_BASE = "/agent-ready-repo/docs"

# Guide-specific frontmatter fields that are stripped before writing to the
# docs-site. These are understood by validate_guides.py but not by Starlight.
_GUIDE_ONLY_FIELDS = frozenset({
    "pack", "kind", "summary", "slug", "aliases", "status", "journey", "order",
})
_GUIDE_SLUG_PART_RE = re.compile(r"^[a-z0-9_][a-z0-9_-]*$")


def discover_packs(root: Path, site_toml: Path) -> list[dict]:
    """Return packs ordered by site.toml groups, ungrouped packs appended alphabetically.

    Each dict: {slug, display_name, version, scope, description, group}.
    """
    with site_toml.open("rb") as f:
        site = tomllib.load(f)
    groups = site.get("groups", [])

    packs_by_slug: dict[str, dict] = {}
    for pack_toml in sorted((root / "packs").glob("*/pack.toml")):
        slug = pack_toml.parent.name
        if slug.startswith("_"):
            continue
        with pack_toml.open("rb") as f:
            data = tomllib.load(f)
        p = data.get("pack", {})
        name = p.get("name", slug)
        display_name = p.get("display_name") or name.replace("-", " ").replace("_", " ").title()
        packs_by_slug[slug] = {
            "slug": slug,
            "display_name": display_name,
            "version": p.get("version", ""),
            "scope": p.get("install", {}).get("default-scope", "repo"),
            "description": p.get("description", ""),
            "group": None,
        }

    ordered: list[dict] = []
    grouped: set[str] = set()
    for group in groups:
        label = group.get("label")
        if not label:
            print("  warn  site.toml group missing 'label' — skipping", file=sys.stderr)
            continue
        for slug in group.get("packs", []):
            if slug not in packs_by_slug:
                print(
                    f"  warn  site.toml slug '{slug}' in group '{label}'"
                    f" has no packs/{slug}/pack.toml",
                    file=sys.stderr,
                )
                continue
            if slug not in grouped:
                packs_by_slug[slug]["group"] = label
                ordered.append(packs_by_slug[slug])
                grouped.add(slug)

    for slug in sorted(packs_by_slug):
        if slug not in grouped:
            print(
                f"  warn  pack '{slug}' not in any site.toml group — placed in 'Other'",
                file=sys.stderr,
            )
            packs_by_slug[slug]["group"] = "Other"
            ordered.append(packs_by_slug[slug])

    return ordered

# ---------------------------------------------------------------------------
# Frontmatter injection
# ---------------------------------------------------------------------------


def _inject_frontmatter(text: str, path: Path) -> str:
    """Prepend minimal Starlight frontmatter (title: ) if none present.

    Starlight's docsSchema() requires a `title` field. Files without YAML
    frontmatter get one derived from a leading H1 heading, or from the
    filename as a fallback.
    """
    if text.startswith("---"):
        return text  # already has frontmatter
    # Take the title from a *leading* H1 and strip that same heading, so
    # Starlight doesn't render it a second time beneath its own page title.
    heading = leading_h1(text)
    if heading is not None:
        title = heading.strip().replace('"', '\\"')
        body = _strip_leading_h1(text)
    else:
        print(
            f"  warn  {_relpath(path)}: no leading H1 — page title derived from "
            "the filename",
            file=sys.stderr,
        )
        title = path.stem.replace("-", " ").replace("_", " ").title()
        body = text
    return f'---\ntitle: "{title}"\n---\n\n' + body


# ---------------------------------------------------------------------------
# Guide frontmatter helpers (for catalogue-facing guide routing)
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from a file's text; return {} if absent or invalid."""
    import yaml
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    yaml_block = text[3:end]
    try:
        data = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _normalise_guide_slug(
    value: object, source_path: Path | None = None, field: str = "slug"
) -> str | None:
    """Return a confined guide slug, or ``None`` when frontmatter is invalid."""
    if value is None:
        return None
    if not isinstance(value, str):
        if source_path is not None:
            print(
                f"  warn  {_relpath(source_path)}: non-string '{field}' ignored",
                file=sys.stderr,
            )
        return None

    slug = value.strip().strip("/")
    if slug.endswith("/index"):
        slug = slug[: -len("/index")]
    parts = slug.split("/")
    valid = (
        len(parts) >= 2
        and parts[0] == "guides"
        and all(_GUIDE_SLUG_PART_RE.fullmatch(part) for part in parts[1:])
    )
    if valid:
        return slug

    if source_path is not None:
        print(
            f"  warn  {_relpath(source_path)}: invalid '{field}' ignored",
            file=sys.stderr,
        )
    return None


# Counters for the two silent body/frontmatter transforms, reported alongside
# the per-stage counts the rest of this module prints. Without them, a change
# that stops the summary→description mapping firing would drop the meta
# description from 46 pages and leave the build green with nothing to compare.
_TRANSFORM_COUNTS = {"h1_stripped": 0, "summary_mapped": 0}

_LEADING_H1_RE = re.compile(r"\A#[ \t]+(.+?)[ \t]*(?:\n|\Z)")


def leading_h1(body: str) -> str | None:
    """Return the text of the body's *leading* ``# `` heading, or None.

    The single definition of "the page-title H1". ``tools/lint-guide-titles.py``
    imports this rather than re-deriving it: the lint's whole job is to guard an
    invariant this module defines, so a second copy of the rule could drift and
    the gate would stop guarding without failing.

    Anchored to the start deliberately. A free ``re.search`` for ``^# `` would
    also match a shell comment inside a fenced code block — there are 42 such
    lines across 14 guides — so it would promote a bash comment to the page
    title, and, worse, silently delete it from the code sample. Anchoring is
    what keeps this transform lossless.
    """
    m = _LEADING_H1_RE.match(body.lstrip("\n"))
    return m.group(1) if m else None


def _strip_leading_h1(body: str) -> str:
    """Drop a leading ``# `` heading so Starlight's title is the only H1.

    Starlight renders ``title:`` as the page ``<h1>``. A body H1 on top of that
    produces two — and, because the two strings are maintained independently,
    usually two *different* ones.
    """
    stripped = body.lstrip("\n")
    m = _LEADING_H1_RE.match(stripped)
    if not m:
        return body
    _TRANSFORM_COUNTS["h1_stripped"] += 1
    return stripped[m.end():].lstrip("\n")


def _strip_guide_metadata(text: str) -> str:
    """Remove guide-specific frontmatter fields before writing to the docs-site.

    Keeps Starlight-required/compatible fields (title, description, sidebar, etc.).
    Drops the body's leading H1 whenever the frontmatter carries a ``title``,
    which is the field Starlight renders as the page heading — keeping both
    produced 38 double-titled pages. A guide with frontmatter but no ``title``
    keeps its H1, because that heading is then the page's only title source.
    """
    import yaml
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    yaml_block = text[3:end]
    try:
        data = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        return text
    if not isinstance(data, dict):
        return text

    body = text[end + 4:]
    if data.get("title"):
        body = _strip_leading_h1(body)

    # `summary` is the guide-vocabulary name for what Starlight calls
    # `description`. Carry it across rather than dropping it with the other
    # guide-only fields: it feeds <meta name="description">, the search
    # snippet, and the rendered deck. An explicit `description` wins.
    if data.get("summary") and not data.get("description"):
        data = dict(data)
        data["description"] = str(data["summary"]).strip()
        _TRANSFORM_COUNTS["summary_mapped"] += 1

    # Exclude None values so yaml.safe_dump doesn't emit `key: null` noise.
    cleaned = {
        k: v for k, v in data.items()
        if k not in _GUIDE_ONLY_FIELDS and v is not None
    }
    if cleaned == {k: v for k, v in data.items() if v is not None}:
        # Frontmatter needs no rewrite; the body may still have lost its H1.
        return text[: end + 4] + "\n\n" + body.lstrip("\n")

    # Reconstruct frontmatter
    if not cleaned:
        # All fields were guide-only; keep an empty frontmatter block so Starlight
        # doesn't inject a duplicate title from H1 (injection only fires when no ---)
        return "---\n---\n\n" + body.lstrip("\n")

    fm_body = yaml.safe_dump(
        cleaned, default_flow_style=False, sort_keys=False, allow_unicode=True,
    ).rstrip("\n")
    fm_text = "---\n" + fm_body + "\n---"
    return fm_text + "\n\n" + body.lstrip("\n")


def _make_redirect_stub(target_url: str) -> str:
    """Generate a Starlight-compatible page with a meta-refresh redirect."""
    return (
        '---\ntitle: "Redirecting..."\n---\n\n'
        f'<meta http-equiv="refresh" content="0; url={target_url}">\n\n'
        f'This page has moved. [Click here]({target_url}) '
        "if you are not redirected automatically.\n"
    )


# ---------------------------------------------------------------------------
# Guide inventory — the collate step that precedes projection.
# Contract: docs/specs/guides-sidebar-generation/spec.md § Layer 1
# ---------------------------------------------------------------------------

VALID_GUIDE_KINDS = frozenset({"tutorial", "how-to", "reference", "explanation"})

# The on-disk directory is plural; contracts/guide.schema.json's enum is
# singular. Without this, the first page under tutorials/ to gain frontmatter
# splits its pack into a "Tutorial" bucket and a "Tutorials" bucket.
_KIND_DIR_ALIASES = {"tutorials": "tutorial"}

# Maintainer context. Still mirrored — so still reachable by URL — but never
# surfaced in reader navigation.
_NAV_INELIGIBLE_NAMES = frozenset({"AGENTS.md"})


def guide_slug_for(rel_parts: list[str]) -> str:
    """Starlight slug of the file ``mirror_guides`` writes for these parts.

    ``mirror_guides`` renames ``README.md`` to ``index.md`` before deriving its
    ``canonical_slug``, so a pack README's canonical slug is
    ``guides/<pack>/index``. Starlight serves that at ``guides/<pack>``, which
    is the value navigation needs — hence the trailing ``/index`` strip.
    """
    parts = list(rel_parts)
    if parts[-1] == "README.md":
        parts[-1] = "index.md"
    if parts[-1].endswith(".md"):
        parts[-1] = parts[-1][:-3]
    if parts[-1] == "index":
        parts.pop()
    return "guides/" + "/".join(parts) if parts else "guides"


def build_guide_inventory(guides_root: Path, enumerator=None) -> list[dict]:
    """Collate every ``.md`` file under ``guides_root`` into one record each.

    Path structure is the source and frontmatter refines it: most guides carry
    no frontmatter, so a frontmatter-sourced inventory would omit them.

    ``enumerator`` is the determinism seam — a callable taking the root and
    returning an iterable of paths. Output order does not depend on it; the
    records are sorted by slug before returning.
    """
    paths = enumerator(guides_root) if enumerator else guides_root.rglob("*.md")

    records: list[dict] = []
    for path in paths:
        if path.suffix != ".md" or not path.is_file():
            continue
        rel_parts = list(path.relative_to(guides_root).parts)
        fm = _parse_frontmatter(path.read_text(encoding="utf-8"))

        # A file directly under guides/ has no pack segment — the root README
        # belongs to the tree itself, not to a pack called "README.md".
        pack = rel_parts[0] if len(rel_parts) > 1 else None

        kind = fm.get("kind") if fm.get("kind") in VALID_GUIDE_KINDS else None
        if kind is None and len(rel_parts) >= 3:
            candidate = _KIND_DIR_ALIASES.get(rel_parts[1], rel_parts[1])
            kind = candidate if candidate in VALID_GUIDE_KINDS else None

        # bool is an int subclass; a YAML `order: true` must not sort as 1.
        raw_order = fm.get("order")
        is_int = isinstance(raw_order, int) and not isinstance(raw_order, bool)
        order = raw_order if is_int else None

        # Frontmatter is adopter-authored: invalid route metadata must degrade
        # to the derived value, not crash or write outside the guide route tree.
        override = _normalise_guide_slug(fm.get("slug"), path)

        title = fm.get("title") or None
        if title is not None and not isinstance(title, str):
            print(f"  warn  {_relpath(path)}: non-string 'title' ignored", file=sys.stderr)
            title = None

        # Every navigation exclusion is announced — a silently missing page is
        # the defect this whole change exists to remove.
        is_section_index = path.name == "README.md" and len(rel_parts) >= 3
        nav_eligible = path.name not in _NAV_INELIGIBLE_NAMES and not is_section_index
        if not nav_eligible:
            why = ("section index (README more than one directory below guides/)"
                   if is_section_index else "maintainer context")
            print(f"  note  {_relpath(path)}: {why}; mirrored but not in navigation",
                  file=sys.stderr)

        records.append({
            "source_path": path,
            "pack": pack,
            "kind": kind,
            "order": order,
            "title": title,
            "slug": override or guide_slug_for(rel_parts),
            "is_index": path.name == "README.md",
            # A README below kind level is a section-authoring template
            # ("Writing a how-to"), addressed to whoever writes the guides — not
            # to the adopter this tree serves. None was in the pre-change
            # sidebar, so keeping them out preserves the status quo.
            "nav_eligible": nav_eligible,
        })

    # Secondary key on the path: a duplicate slug would otherwise resolve by
    # enumerator arrival order, breaking determinism.
    records.sort(key=lambda r: (r["slug"], str(r["source_path"])))

    # A repeated slug renders twice and orders by enumerator arrival, which
    # would break determinism. Set-equality tests cannot see it.
    seen: dict[str, Path] = {}
    for rec in records:
        if rec["slug"] in seen:
            print(
                f"  warn  duplicate guide slug '{rec['slug']}':"
                f" {_relpath(rec['source_path'])} also claimed by"
                f" {_relpath(seen[rec['slug']])}",
                file=sys.stderr,
            )
        seen[rec["slug"]] = rec["source_path"]

    return records


# ---------------------------------------------------------------------------
# Guide sidebar projection — inventory becomes Starlight groups.
# Contract: docs/specs/guides-sidebar-generation/spec.md § Layer 2
# ---------------------------------------------------------------------------

# Reader-visible bucket labels, in the canonical sequence.
_KIND_BUCKETS = (
    ("tutorial", "Tutorials"),
    ("how-to", "How-to"),
    ("reference", "Reference"),
    ("explanation", "Explanation"),
)


def _guide_label(record: dict, baseline: dict) -> str:
    """Resolve a sidebar label: frozen baseline, then the page's own title,
    then the filename.

    Baseline first is deliberate. Thirteen pages carry a ``title:`` that differs
    from the label they show in navigation today, so putting frontmatter first
    would rewrite them silently. Removing a baseline entry is the reviewable act
    that adopts a page's own title.
    """
    if record["slug"] in baseline:
        return baseline[record["slug"]]
    if record["title"]:
        return record["title"]
    if record["is_index"]:
        # Filename derivation would read "Readme"; every index entry in the
        # pre-change tree reads "Overview".
        return "Overview"
    return record["slug"].rsplit("/", 1)[-1].replace("-", " ").title()


def project_guide_sidebar(records: list[dict], guide_groups: list[dict],
                          baseline: dict) -> dict:
    """Project inventory records into the Starlight ``Guides`` sidebar group.

    Emission order within a pack group is fixed: index pages, then records
    declaring ``order`` (ascending, across kinds), then kind-less non-index
    records, then the kind buckets in canonical sequence.
    """
    eligible = [r for r in records if r["nav_eligible"]]

    # Warn and skip on a malformed entry rather than raising a bare KeyError
    # mid-build, matching discover_packs()'s handling of the sibling table.
    valid_groups = []
    for i, g in enumerate(guide_groups):
        if not g.get("dir") or not g.get("label"):
            print(
                f"  warn  site.toml [[guide_groups]] entry {i} missing 'dir' or"
                " 'label' — skipping",
                file=sys.stderr,
            )
            continue
        valid_groups.append(g)

    declared = [g["dir"] for g in valid_groups]
    labels = {g["dir"]: g["label"] for g in valid_groups}
    # An undeclared directory still gets a group rather than vanishing.
    extra = sorted({r["pack"] for r in eligible if r["pack"] and r["pack"] not in labels})
    for d in extra:
        labels[d] = d.replace("-", " ").replace("_", " ").strip().title()

    items: list[dict] = []

    # Files directly under guides/ belong to the tree itself, not to any pack.
    # Index first, then any other loose page — otherwise a future
    # guides/CONTRIBUTING.md would be eligible and emitted nowhere.
    root_level = [r for r in eligible if r["pack"] is None]
    for rec in sorted(root_level, key=lambda r: (not r["is_index"], r["slug"])):
        items.append({"label": _guide_label(rec, baseline), "slug": rec["slug"]})

    for pack in [d for d in declared if d in {r["pack"] for r in eligible}] + extra:
        members = [r for r in eligible if r["pack"] == pack]
        group_items: list[dict] = []

        def entry(r):
            return {"label": _guide_label(r, baseline), "slug": r["slug"]}

        for rec in sorted((r for r in members if r["is_index"]), key=lambda r: r["slug"]):
            group_items.append(entry(rec))
        for rec in sorted((r for r in members if r["order"] is not None and not r["is_index"]),
                          key=lambda r: (r["order"], r["slug"])):
            group_items.append(entry(rec))
        for rec in sorted((r for r in members
                           if r["order"] is None and not r["is_index"] and r["kind"] is None),
                          key=lambda r: r["slug"]):
            group_items.append(entry(rec))

        for kind, bucket_label in _KIND_BUCKETS:
            bucket = [r for r in members
                      if r["kind"] == kind and r["order"] is None and not r["is_index"]]
            if not bucket:
                continue
            bucket.sort(key=lambda r: (_guide_label(r, baseline).casefold(), r["slug"]))
            group_items.append({
                "label": bucket_label,
                "items": [entry(r) for r in bucket],
            })

        if group_items:
            items.append({"label": labels[pack], "items": group_items})

    return {"label": "Guides", "items": items}


# ---------------------------------------------------------------------------
# Guide-aware mirror (replaces the bare mirror_dir call for guides/)
# ---------------------------------------------------------------------------

def mirror_guides(src: Path, site_docs: Path, dry_run: bool = False) -> int:
    """Mirror src/ into site_docs/guides/ with frontmatter-aware routing.

    - Files with ``slug:`` frontmatter are written to site_docs/<slug>.md
      (overriding the default path-based placement).
    - Files with ``aliases:`` frontmatter get meta-refresh redirect stubs.
    - Guide-specific metadata (pack, kind, summary, slug, aliases, status,
      journey, order) is stripped before writing so Starlight doesn't see it.
    - Files without frontmatter receive the existing title-injection treatment.
    - docs/guides/ is not the src here and is never mirrored.
    """
    guides_out = site_docs / "guides"
    count = 0
    if not src.exists():
        src_display = (
            src.relative_to(REPO_ROOT) if src.is_relative_to(REPO_ROOT) else src
        )
        print(f"  warn  source dir missing: {src_display}", file=sys.stderr)
        return 0
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        rel_parts = list(rel.parts)
        if rel_parts[-1] == "README.md":
            rel_parts[-1] = "index.md"

        if path.suffix != ".md":
            target = guides_out / Path(*rel_parts)
            if dry_run:
                print(f"  copy  {_relpath(path)} → {_relpath(target)}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            count += 1
            continue

        text = path.read_text(encoding="utf-8")
        text = _rewrite_guide(text, path)
        fm = _parse_frontmatter(text)

        # Determine canonical slug and output path
        override = _normalise_guide_slug(fm.get("slug"), path) if fm else None
        if override:
            canonical_slug = override
            target = site_docs / (canonical_slug + ".md")
        else:
            # Derive slug from the (possibly renamed) relative parts
            slug_parts = list(rel_parts)
            if slug_parts[-1].endswith(".md"):
                slug_parts[-1] = slug_parts[-1][:-3]
            canonical_slug = "guides/" + "/".join(slug_parts)
            target = guides_out / Path(*rel_parts)

        # Strip guide-specific metadata; fall through to title injection if needed
        if fm:
            text = _strip_guide_metadata(text)

        if not text.startswith("---"):
            text = _inject_frontmatter(text, path)

        if dry_run:
            action = "rename" if path.name == "README.md" else "copy"
            if override:
                action = "route"
            print(f"  {action} {_relpath(path)} → {_relpath(target)}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        count += 1

        # Generate redirect stubs for aliases
        aliases = fm.get("aliases") if fm else None
        if isinstance(aliases, list):
            canonical_url = f"{SITE_BASE}/{canonical_slug}/"
            for alias in aliases:
                alias_slug = _normalise_guide_slug(alias, path, "aliases")
                if not alias_slug:
                    continue
                stub_target = site_docs / (alias_slug + ".md")
                stub_content = _make_redirect_stub(canonical_url)
                if dry_run:
                    print(f"  stub  {alias_slug} → {canonical_slug}")
                else:
                    stub_target.parent.mkdir(parents=True, exist_ok=True)
                    stub_target.write_text(stub_content, encoding="utf-8")
        elif aliases is not None:
            print(
                f"  warn  {_relpath(path)}: non-list 'aliases' ignored",
                file=sys.stderr,
            )

    return count


def _relpath(p: Path) -> str:
    try:
        return str(p.relative_to(REPO_ROOT))
    except ValueError:
        return str(p)


# ---------------------------------------------------------------------------
# Link rewriters
# ---------------------------------------------------------------------------

def _strip_md_suffixes(text: str) -> str:
    """Strip .md suffixes from intra-site markdown links.

    Starlight serves content at clean URLs (no .md). Links like
    [label](other-file.md) and [label](path/README.md) must become
    [label](other-file/) and [label](path/) so they resolve correctly.

    External links (http/https) are never touched.
    """
    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        # Skip external links and anchor-only links
        if not path or path.startswith(("http://", "https://", "#")):
            return m.group(0)
        if path.endswith(".md"):
            # README.md → ../../ style; otherwise strip .md, add /
            if path.endswith("/README.md"):
                path = path[: -len("README.md")]  # e.g. "foo/README.md" → "foo/"
            elif path == "README.md":
                path = "./"
            else:
                path = path[:-3] + "/"  # strip .md, add /
        return f"{prefix}{path}{anchor})"

    return re.sub(r"(\]\()([^)#\"'\s]+)(#[^)]+)?\)", replace, text)


def _rewrite_changelog(text: str) -> str:
    """Fix links in changelog.md when moved from docs/product/ to docs-site content.

    In source: relative to docs/product/changelog.md
      ../guides/... → base-qualified technical guide route
      ../rfc/...    → GitHub URL  (not in site)
      ../specs/...  → GitHub URL  (not in site)
    """
    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        if path.startswith("../guides/"):
            return f"{prefix}{SITE_BASE}/{path[3:]}{anchor})"
        if path.startswith("../"):
            # Convert to GitHub URL
            clean = path[3:]  # remove ../
            return f"{prefix}{GITHUB_BASE}/{clean}{anchor})"
        return m.group(0)

    result = re.sub(r"(\]\()(\.\./[^)#]*)(#[^)]+)?\)", replace, text)
    return _strip_md_suffixes(result)


def _rewrite_pack_readme(text: str, pack_src_path: Path) -> str:
    """Rewrite links in pack READMEs moved from packs/<slug>/README.md
    to docs-site/src/content/docs/packs/<slug>.md.

    Pack-home links (../other-pack/README.md) → base-qualified pack route.
    Other repository files, including files beside the README → GitHub URL.
    """
    packs_root = (REPO_ROOT / "packs").resolve()
    repo_root = REPO_ROOT.resolve()

    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        if not path or path.startswith(("http://", "https://", "#")):
            return m.group(0)
        try:
            resolved = (pack_src_path.parent / path).resolve()
        except Exception:
            return m.group(0)

        if _is_relative_to(resolved, packs_root):
            # A pack README is served at /docs/packs/<slug>/, so a bare sibling
            # slug would incorrectly nest below the current pack route.
            rel = resolved.relative_to(packs_root)
            pack_name = rel.parts[0]
            if resolved.is_dir() or rel.parts[1:] == ("README.md",):
                return f"{prefix}{SITE_BASE}/packs/{pack_name}/{anchor})"
            repo_rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{repo_rel}{anchor})"

        if _is_relative_to(resolved, repo_root):
            rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{rel}{anchor})"

        return m.group(0)

    result = re.sub(r"(\]\()([^)#\"'\s]+)(#[^)]+)?\)", replace, text)
    return _strip_md_suffixes(result)


def _rewrite_guide(text: str, guide_src_path: Path) -> str:
    """Rewrite links in guide files that exit the guides tree.

    Links within guides/ are normalised to relative Starlight URLs.
    Links that resolve within the repo but outside guides/ are
    converted to GitHub URLs so they don't produce dead references.
    """
    guides_root = (REPO_ROOT / "guides").resolve()
    repo_root = REPO_ROOT.resolve()

    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        if not path or path.startswith(("http://", "https://", "#")):
            return m.group(0)

        # Resolve the link relative to the guide file's source position
        try:
            resolved = (guide_src_path.parent / path).resolve()
        except Exception:
            return m.group(0)

        # Within guides/ → route to the mirrored page from the docs root.
        # A relative source link cannot be preserved: Starlight serves each
        # Markdown file as a directory route, so `sibling.md` from
        # `/guide-name/` would incorrectly become `/guide-name/sibling/`.
        if _is_relative_to(resolved, guides_root) and resolved.exists():
            site_url = _guide_site_url(resolved, guides_root)
            return f"{prefix}{site_url}{anchor})"
        # Stale link within guides/ — fall through

        # Within repo but outside guides/ → GitHub URL
        if _is_relative_to(resolved, repo_root):
            rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{rel}{anchor})"

        return m.group(0)

    result = re.sub(r"(\]\()([^)#\"'\s]+)(#[^)]+)?\)", replace, text)
    return _strip_md_suffixes(result)


def _guide_site_url(path: Path, guides_root: Path) -> str:
    """Return the base-qualified technical-doc URL for a guide source path."""
    source = path / "README.md" if path.is_dir() else path
    rel = source.relative_to(guides_root)

    if source.suffix == ".md" and source.exists():
        frontmatter = _parse_frontmatter(source.read_text(encoding="utf-8"))
        slug = _normalise_guide_slug(frontmatter.get("slug"), source)
        if not slug:
            parts = list(rel.parts)
            if parts[-1] == "README.md":
                parts = parts[:-1]
            else:
                parts[-1] = Path(parts[-1]).stem
            slug = "/".join(("guides", *parts))
        return f"{SITE_BASE}/{slug}/"

    return f"{SITE_BASE}/guides/{rel.as_posix()}"


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _rewrite_contributing(text: str) -> str:
    """Fix links in CONTRIBUTING.md when placed at docs-site content root.

    CONTRIBUTING.md lives at the repo root; links are repo-root-relative.
    Most targets (AGENTS.md, docs/CONVENTIONS.md, etc.) aren't in the site,
    so we convert them to GitHub URLs using proper Path resolution.
    """
    contributing_src = REPO_ROOT / "CONTRIBUTING.md"
    repo_root = REPO_ROOT.resolve()
    guides_root = (REPO_ROOT / "guides").resolve()

    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        if not path or path.startswith(("http://", "https://", "#")):
            return m.group(0)
        try:
            resolved = (contributing_src.parent / path).resolve()
        except Exception:
            return m.group(0)

        # Links within guides/ → base-qualified mirrored guide route.
        # CONTRIBUTING is served from /docs/contributing/, so a `guides/...`
        # href would otherwise nest under that page.
        if _is_relative_to(resolved, guides_root) and resolved.exists():
            site_url = _guide_site_url(resolved, guides_root)
            return f"{prefix}{site_url}{anchor})"

        # Any other repo-relative link → GitHub URL
        if _is_relative_to(resolved, repo_root):
            rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{rel}{anchor})"

        return m.group(0)

    result = re.sub(r"(\]\()([^)#\"'\s]+)(#[^)]+)?\)", replace, text)
    return _strip_md_suffixes(result)


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def copy_file(src: Path, dst: Path, rewriter=None, dry_run: bool = False) -> None:
    """Copy src to dst, applying an optional rewriter(text) → text transform.

    For .md files, injects Starlight frontmatter (title:) if none present.
    """
    if dry_run:
        print(f"  copy  {src.relative_to(REPO_ROOT)} → {dst.relative_to(REPO_ROOT)}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8")
    if rewriter:
        text = rewriter(text)
    if dst.suffix == ".md" and not text.startswith("---"):
        text = _inject_frontmatter(text, src)
    dst.write_text(text, encoding="utf-8")


def mirror_dir(src: Path, dst: Path, rewriter=None, dry_run: bool = False) -> int:
    """Mirror src into dst, applying an optional per-file rewriter to .md files.

    README.md files are renamed to index.md to preserve directory-index URLs
    in Starlight (prevents /guides/core/readme/ instead of /guides/core/).
    Starlight frontmatter (title:) is injected into .md files that lack it.
    """
    count = 0
    if not src.exists():
        print(f"  warn  source dir missing: {src.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 0
    for path in sorted(src.rglob("*")):
        if path.is_file():
            rel = path.relative_to(src)
            # Rename README.md → index.md to preserve Starlight directory-index URLs
            rel_parts = list(rel.parts)
            if rel_parts[-1] == "README.md":
                rel_parts[-1] = "index.md"
            target = dst / Path(*rel_parts)
            if dry_run:
                action = "rename" if path.name == "README.md" else "copy"
                print(
                    f"  {action} {path.relative_to(REPO_ROOT)}"
                    f" → {target.relative_to(REPO_ROOT)}"
                )
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix == ".md":
                    text = path.read_text(encoding="utf-8")
                    if rewriter:
                        text = rewriter(text, path)
                    if not text.startswith("---"):
                        text = _inject_frontmatter(text, path)
                    target.write_text(text, encoding="utf-8")
                else:
                    shutil.copy2(path, target)
            count += 1
    return count


def build_pack_index(packs: list[dict], out_dir: Path, dry_run: bool = False) -> None:
    header = (
        '---\ntitle: "Pack Catalogue"\n'
        f'description: "{len(packs)} curated packs for the AI operating model."\n'
        "---\n\n"
        # No body H1 — Starlight renders `title:` as the page heading.
        f"{len(packs)} curated packs — each distilled from the best practices of its discipline\n"
        "through practitioner research and RFC-and-ADR governance.\n\n"
        "Install any pack in one command:\n\n"
        "```bash\n"
        "agentbundle install --pack <name>               # repo scope (default)\n"
        "agentbundle install --pack <name> --scope user  # user scope\n"
        "```\n\n"
        "| Pack | Scope | Description |\n"
        "|---|---|---|\n"
    )
    lines = [header]
    for p in packs:
        lines.append(
            f"| [**{p['display_name']}**]({p['slug']}/) |"
            f" `{p['scope']}` | {p['description']} |\n"
        )

    content = "".join(lines)
    index_md = out_dir / "index.md"
    if dry_run:
        print(f"  gen   docs-site/src/content/docs/packs/index.md ({len(content)} bytes)")
    else:
        index_md.write_text(content, encoding="utf-8")


def _fm_split(text: str) -> tuple[str, str]:
    """Return (frontmatter_body, rest). Empty string if no frontmatter block."""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[3:end], text[end + 4:]


def _fm_scalar(fm: str, key: str) -> str | None:
    """Extract a simple scalar value from raw frontmatter text."""
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip() if m else None


def _inject_generated_marker(text: str) -> str:
    """Inject or set generated: true in the JOURNEY.md frontmatter block."""
    if not text.startswith("---\n"):
        return text
    fm_end = text.find("\n---", 3)
    if fm_end == -1:
        return text
    fm = text[3:fm_end]
    if re.search(r"^generated:", fm, re.MULTILINE):
        fm = re.sub(r"^generated:.*$", "generated: true", fm, flags=re.MULTILINE)
        return "---" + fm + text[fm_end:]
    return "---\ngenerated: true" + text[3:]


def sync_pack_journeys(
    packs_dir: Path,
    journey_dir: Path,
    dry_run: bool = False,
) -> int:
    """Generate central journey files from packs/*/JOURNEY.md.

    Performs dual-ownership checks before writing. Returns count of files synced.
    """
    sources = sorted(packs_dir.glob("*/JOURNEY.md"))
    if not sources:
        return 0

    central: dict[str, tuple[str, str]] = {}
    if journey_dir.exists():
        for jf in journey_dir.glob("*.md"):
            cfm, _ = _fm_split(jf.read_text(encoding="utf-8"))
            central[jf.stem] = (
                _fm_scalar(cfm, "pack") or "",
                _fm_scalar(cfm, "generated") or "",
            )

    count = 0
    for src in sources:
        pack_name = src.parent.name
        text = src.read_text(encoding="utf-8")
        fm, _ = _fm_split(text)

        journey_id = _fm_scalar(fm, "journey_id")
        if not journey_id:
            print(f"error  {src}: missing journey_id — cannot sync", file=sys.stderr)
            sys.exit(1)

        for stem, (cf_pack, cf_generated) in central.items():
            if cf_generated == "true":
                continue
            if stem == journey_id:
                print(
                    f"error  dual canonical ownership: {src} (journey_id={journey_id!r})"
                    f" and non-generated central file '{stem}.md' share the same slug",
                    file=sys.stderr,
                )
                sys.exit(1)
            if cf_pack == pack_name:
                print(
                    f"error  dual canonical ownership: {src} and non-generated"
                    f" central file '{stem}.md' both claim pack {pack_name!r}",
                    file=sys.stderr,
                )
                sys.exit(1)

        target = journey_dir / f"{journey_id}.md"
        out_text = _inject_generated_marker(text)

        if dry_run:
            print(
                f"  sync  {src.relative_to(REPO_ROOT)}"
                f" → {target.relative_to(REPO_ROOT)}"
            )
        else:
            journey_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(out_text, encoding="utf-8")
            print(
                f"  sync  {src.relative_to(REPO_ROOT)}"
                f" → {target.relative_to(REPO_ROOT)}"
            )
        count += 1

    return count


def load_guide_baseline(path: Path) -> dict:
    """Read the frozen pre-change ``(slug, label)`` navigation baseline.

    Missing file returns ``{}`` — the generator still produces a sidebar, it
    just derives every label instead of preserving the curated ones.
    """
    if not path.exists():
        return {}
    with path.open("rb") as f:
        data = tomllib.load(f)
    baseline = {}
    for i, e in enumerate(data.get("entry", [])):
        if not e.get("slug") or not e.get("label"):
            print(
                f"  warn  {path.name} entry {i} missing 'slug' or 'label' — skipping",
                file=sys.stderr,
            )
            continue
        baseline[e["slug"]] = e["label"]
    return baseline


def build_guides_sidebar_group(repo_root: Path, site_toml: Path) -> dict | None:
    """Collate the guides tree and project it into the ``Guides`` sidebar group."""
    guides_root = repo_root / "guides"
    if not guides_root.exists():
        return None
    with site_toml.open("rb") as f:
        guide_groups = tomllib.load(f).get("guide_groups", [])
    records = build_guide_inventory(guides_root)
    baseline = load_guide_baseline(repo_root / "guide-nav-baseline.toml")
    group = project_guide_sidebar(records, guide_groups, baseline)

    # The failure this change removes — pages published but unreachable — was
    # invisible precisely because nothing counted. Report on every run.
    eligible = sum(1 for r in records if r["nav_eligible"])
    declared = {g.get("dir") for g in guide_groups}
    fallback = sorted({r["pack"] for r in records
                       if r["nav_eligible"] and r["pack"] and r["pack"] not in declared})
    n_groups = sum(1 for i in group["items"] if "items" in i)
    print(f"  guides  {eligible} navigable page(s) in {n_groups} group(s)")
    if fallback:
        print(f"  warn    undeclared in site.toml [[guide_groups]]: {', '.join(fallback)}",
              file=sys.stderr)
    return group


def generate_sidebar_config(packs: list[dict], out: Path, dry_run: bool = False,
                            guides_group: dict | None = None) -> None:
    """Write docs-site/src/sidebar-config.json — an array of Starlight sidebar groups."""
    groups_seen: list[str] = []
    groups_map: dict[str, list[dict]] = {}
    for p in packs:
        g = p["group"]
        if g not in groups_map:
            groups_seen.append(g)
            groups_map[g] = []
        groups_map[g].append({"label": p["display_name"], "slug": f"packs/{p['slug']}"})

    sidebar: list[dict] = [
        {"label": "Pack Catalogue", "items": [{"label": "All Packs", "slug": "packs"}]},
    ]
    for g in groups_seen:
        sidebar.append({"label": g, "items": groups_map[g]})

    if guides_group:
        sidebar.append(guides_group)

    payload = json.dumps(sidebar, indent=2)
    if dry_run:
        print(
            f"  gen   docs-site/src/sidebar-config.json"
            f" ({len(payload)} bytes, {len(sidebar)} groups)"
        )
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument(
        "--journeys-only",
        action="store_true",
        help="Sync pack-local JOURNEY.md files only; skip Starlight aggregation.",
    )
    args = parser.parse_args()

    packs_dir = REPO_ROOT / "packs"

    if args.journeys_only:
        journey_dir = REPO_ROOT / "web" / "src" / "content" / "journeys"
        n = sync_pack_journeys(packs_dir, journey_dir, dry_run=args.dry_run)
        print(
            f"build-site: synced {n} pack journey(s)"
            + (" (dry run)" if args.dry_run else "")
        )
        return

    packs_out = SITE_DOCS / "packs"
    guides_src = REPO_ROOT / "guides"
    guides_out = SITE_DOCS / "guides"

    if args.clean and not args.dry_run:
        for d in (packs_out, guides_out):
            if d.exists():
                shutil.rmtree(d)
                print(f"  clean {d.relative_to(REPO_ROOT)}/")

    site_toml = REPO_ROOT / "site.toml"
    packs = discover_packs(REPO_ROOT, site_toml)

    print("build-site: copying pack READMEs …")
    # Guarded: every other write in this script honours --dry-run, and this one
    # did not, so `--dry-run` created generated directories on its way to
    # reporting that it would create them. That makes the flag useless as a
    # read-only check — it fails outright against a non-writable tree, and
    # against a writable one it leaves directories behind.
    if not args.dry_run:
        packs_out.mkdir(parents=True, exist_ok=True)
    for p in packs:
        src = packs_dir / p["slug"] / "README.md"
        dst = packs_out / f"{p['slug']}.md"
        if src.exists():
            copy_file(
                src, dst,
                rewriter=lambda t, s=src: _rewrite_pack_readme(t, s),
                dry_run=args.dry_run,
            )
        else:
            print(f"  warn  packs/{p['slug']}/README.md missing", file=sys.stderr)

    print("build-site: generating packs/index.md …")
    build_pack_index(packs, packs_out, dry_run=args.dry_run)

    print("build-site: syncing pack journeys …")
    _n_journeys = sync_pack_journeys(
        packs_dir,
        REPO_ROOT / "web" / "src" / "content" / "journeys",
        dry_run=args.dry_run,
    )
    if _n_journeys:
        print(f"  {_n_journeys} pack-local JOURNEY.md files synced")

    print("build-site: generating sidebar-config.json …")
    sidebar_out = REPO_ROOT / "docs-site" / "src" / "sidebar-config.json"
    guides_group = build_guides_sidebar_group(REPO_ROOT, site_toml)
    generate_sidebar_config(packs, sidebar_out, dry_run=args.dry_run,
                            guides_group=guides_group)

    print("build-site: mirroring guides …")
    n = mirror_guides(guides_src, SITE_DOCS, dry_run=args.dry_run)
    print(f"  {n} files from guides/")

    print("build-site: copying changelog …")
    changelog_src = REPO_ROOT / "docs" / "product" / "changelog.md"
    changelog_dst = SITE_DOCS / "changelog.md"
    if changelog_src.exists():
        copy_file(changelog_src, changelog_dst, rewriter=_rewrite_changelog, dry_run=args.dry_run)
    else:
        print("  warn  docs/product/changelog.md missing", file=sys.stderr)

    print("build-site: copying contributing guide …")
    contributing_src = REPO_ROOT / "CONTRIBUTING.md"
    contributing_dst = SITE_DOCS / "contributing.md"
    if contributing_src.exists():
        copy_file(
            contributing_src, contributing_dst,
            rewriter=_rewrite_contributing,
            dry_run=args.dry_run,
        )
    else:
        print("  warn  CONTRIBUTING.md missing", file=sys.stderr)

    # No design-token copy. `docs-site/src/styles/starlight.css` is a self-contained
    # token sheet and stopped importing the copied file; ADR-0085 makes docs
    # rendering site-local, superseding ADR-0055's token-sharing sub-decision. The
    # copy was vestigial, and the accompanying hard failure —
    # "web/src/styles/tokens.css missing — docs-site CSS depends on it" — asserted a
    # dependency that no longer existed, so a marketing-side change could stop
    # generation for a file the docs site does not read.

    # Whole-build totals, printed last: the two transforms run across the guide
    # mirror AND the pack-README copies, so a per-stage line would attribute
    # pack strips to the guides stage. `--dry-run` short-circuits copy_file
    # before the transform, so its totals are lower by design.
    print(
        f"build-site: {_TRANSFORM_COUNTS['h1_stripped']} body H1(s) stripped, "
        f"{_TRANSFORM_COUNTS['summary_mapped']} summary→description"
        + (" (dry run — copies short-circuited)" if args.dry_run else "")
    )
    print("build-site: done." + (" (dry run)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
