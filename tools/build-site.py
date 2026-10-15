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
import ast
import importlib.util
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
SITE_DOCS = REPO_ROOT / "docs-site" / "src" / "content" / "docs"
# Astro serves only public/ as static files, so a guide asset (an image beside
# a guide) is published from here at the URL _guide_site_url gives it.
SITE_PUBLIC_GUIDES = REPO_ROOT / "docs-site" / "public" / "guides"
GITHUB_BASE = "https://github.com/eugenelim/agent-ready-repo/blob/main"
SITE_BASE = "/agent-ready-repo/docs"
NOW_PROJECTION = (
    REPO_ROOT / "web" / "src" / "lib" / "now-highlights.generated.json"
)
MARKETING_SHARED_CHROME_PROJECTION = (
    REPO_ROOT / "web" / "src" / "lib" / "shared-chrome.generated.json"
)
DOCS_SHARED_CHROME_PROJECTION = (
    REPO_ROOT / "docs-site" / "src" / "shared-chrome.generated.json"
)
# Seven calendar days ending on launch day, inclusive (brief decision 19): the
# launch date itself plus the six dates before it.
NOW_WINDOW_DAYS = 7

# Guide-specific frontmatter fields that are stripped before writing to the
# docs-site. These are understood by validate_guides.py but not by Starlight.
_GUIDE_ONLY_FIELDS = frozenset({
    "pack", "kind", "summary", "slug", "aliases", "status", "journey", "order",
})
_GUIDE_SLUG_PART_RE = re.compile(r"^[a-z0-9_][a-z0-9_-]*$")


# ---------------------------------------------------------------------------
# Shared chrome contract
# ---------------------------------------------------------------------------

_SHARED_CHROME_KINDS = frozenset({"internal", "external"})
_SHARED_CHROME_FIELDS = frozenset({
    "header", "docs_band", "docs_product_navigation", "destinations", "groups",
})
_SHARED_DESTINATION_FIELDS = frozenset({"id", "label", "target", "kind", "group"})
_SHARED_GROUP_FIELDS = frozenset({"id", "label", "destinations"})


def _shared_chrome_string(value: object, field: str, identifier: str) -> str:
    """Require a non-empty shared-chrome string field with its owning ID named."""
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"shared chrome {identifier} has invalid '{field}'; expected a non-empty string"
        )
    return value


def _validate_internal_shared_target(target: str, destination_id: str) -> None:
    """Require a safe root-relative page target or non-empty fragment target."""
    identifier = f"destination '{destination_id}'"
    if not target.startswith("/"):
        raise ValueError(
            f"shared chrome {identifier} has invalid internal target {target!r}; "
            "expected a root-relative target"
        )
    if target.startswith("//"):
        raise ValueError(
            f"shared chrome {identifier} has invalid internal target {target!r}; "
            "protocol-relative targets are not allowed"
        )
    if "\\" in target:
        raise ValueError(
            f"shared chrome {identifier} has invalid internal target {target!r}; "
            "backslashes are not allowed"
        )
    if ".." in target:
        raise ValueError(
            f"shared chrome {identifier} has invalid internal target {target!r}; "
            "parent-directory segments are not allowed"
        )
    if any(character.isspace() for character in target):
        raise ValueError(
            f"shared chrome {identifier} has invalid internal target {target!r}; "
            "whitespace is not allowed"
        )

    path, separator, fragment = target.partition("#")
    if separator:
        if "#" in fragment:
            raise ValueError(
                f"shared chrome {identifier} has invalid internal target {target!r}; "
                "expected at most one fragment"
            )
        if not fragment:
            raise ValueError(
                f"shared chrome {identifier} has invalid internal target {target!r}; "
                "fragment must be non-empty"
            )
        return
    if not path.endswith("/"):
        raise ValueError(
            f"shared chrome {identifier} has invalid internal target {target!r}; "
            "expected a '/'-terminated path or '#fragment' form"
        )


def _reject_shared_chrome_fields(
    record: dict, allowed: frozenset[str], identifier: str
) -> None:
    """Reject renderer presentation or state from the shared destination contract."""
    for field in record:
        if field not in allowed:
            raise ValueError(
                f"shared chrome {identifier} has unsupported field '{field}'; "
                "presentation and state belong to renderer-local components"
            )


def _validate_shared_chrome_destination_list(
    raw_destination_ids: object, field: str, destinations_by_id: dict[str, dict]
) -> list[str]:
    """Validate an ordered, duplicate-free list of declared destination IDs."""
    if not isinstance(raw_destination_ids, list):
        raise ValueError(
            f"site.toml shared_chrome.{field} must be an ordered destination ID array"
        )

    destination_ids: list[str] = []
    for raw_destination_id in raw_destination_ids:
        destination_id = _shared_chrome_string(raw_destination_id, field, field)
        if destination_id not in destinations_by_id:
            raise ValueError(
                f"shared chrome {field} references missing destination '{destination_id}'"
            )
        if destination_id in destination_ids:
            raise ValueError(
                f"shared chrome {field} repeats destination '{destination_id}'"
            )
        destination_ids.append(destination_id)
    return destination_ids


def validate_shared_chrome_contract(contract: object) -> dict:
    """Validate and normalize the renderer-neutral shared-chrome contract.

    The result contains only the fields a renderer may receive. Validation is
    deliberately complete before projection so malformed source cannot produce
    partial renderer data.
    """
    if not isinstance(contract, dict):
        raise ValueError("site.toml shared_chrome must be a table")
    _reject_shared_chrome_fields(contract, _SHARED_CHROME_FIELDS, "contract")

    raw_destinations = contract.get("destinations")
    raw_groups = contract.get("groups")
    raw_header = contract.get("header")
    raw_docs_band = contract.get("docs_band")
    raw_docs_product_navigation = contract.get("docs_product_navigation")
    if not isinstance(raw_destinations, list):
        raise ValueError("site.toml shared_chrome.destinations must be an ordered table array")
    if not isinstance(raw_groups, list):
        raise ValueError("site.toml shared_chrome.groups must be an ordered table array")

    destinations: list[dict] = []
    destinations_by_id: dict[str, dict] = {}
    for index, raw_destination in enumerate(raw_destinations):
        if not isinstance(raw_destination, dict):
            raise ValueError(f"shared chrome destination at position {index + 1} must be a table")
        raw_id = raw_destination.get("id")
        identifier = (
            f"destination '{raw_id}'"
            if isinstance(raw_id, str) and raw_id
            else f"destination at position {index + 1}"
        )
        _reject_shared_chrome_fields(
            raw_destination, _SHARED_DESTINATION_FIELDS, identifier
        )
        destination_id = _shared_chrome_string(raw_id, "id", identifier)
        if destination_id in destinations_by_id:
            raise ValueError(f"shared chrome duplicate destination ID '{destination_id}'")
        label = _shared_chrome_string(raw_destination.get("label"), "label", identifier)
        target = _shared_chrome_string(raw_destination.get("target"), "target", identifier)
        kind = _shared_chrome_string(raw_destination.get("kind"), "kind", identifier)
        if kind not in _SHARED_CHROME_KINDS:
            raise ValueError(
                f"shared chrome destination '{destination_id}' has unsupported kind "
                f"'{kind}'; expected 'internal' or 'external'"
            )
        if kind == "internal":
            _validate_internal_shared_target(target, destination_id)
        group = raw_destination.get("group")
        if group is not None and (not isinstance(group, str) or not group):
            raise ValueError(
                f"shared chrome destination '{destination_id}' has invalid 'group'; "
                "expected a non-empty group ID"
            )
        destination = {
            "id": destination_id,
            "label": label,
            "target": target,
            "kind": kind,
            "group": group,
        }
        destinations.append(destination)
        destinations_by_id[destination_id] = destination

    groups: list[dict] = []
    groups_by_id: dict[str, dict] = {}
    for index, raw_group in enumerate(raw_groups):
        if not isinstance(raw_group, dict):
            raise ValueError(f"shared chrome group at position {index + 1} must be a table")
        raw_id = raw_group.get("id")
        identifier = (
            f"group '{raw_id}'"
            if isinstance(raw_id, str) and raw_id
            else f"group at position {index + 1}"
        )
        _reject_shared_chrome_fields(raw_group, _SHARED_GROUP_FIELDS, identifier)
        group_id = _shared_chrome_string(raw_id, "id", identifier)
        if group_id in groups_by_id:
            raise ValueError(f"shared chrome duplicate group ID '{group_id}'")
        label = _shared_chrome_string(raw_group.get("label"), "label", identifier)
        raw_members = raw_group.get("destinations")
        if not isinstance(raw_members, list):
            raise ValueError(
                f"shared chrome group '{group_id}' has invalid 'destinations'; "
                "expected an ordered destination ID array"
            )
        members: list[str] = []
        for raw_member in raw_members:
            member = _shared_chrome_string(
                raw_member, "destinations", f"group '{group_id}'"
            )
            if member in members:
                raise ValueError(
                    f"shared chrome group '{group_id}' repeats destination '{member}'"
                )
            members.append(member)
        group = {"id": group_id, "label": label, "destinations": members}
        groups.append(group)
        groups_by_id[group_id] = group

    for group in groups:
        for member in group["destinations"]:
            destination = destinations_by_id.get(member)
            if destination is None:
                raise ValueError(
                    f"shared chrome group '{group['id']}' references missing "
                    f"destination '{member}'"
                )
            if destination["group"] != group["id"]:
                raise ValueError(
                    f"shared chrome destination '{member}' references group "
                    f"'{destination['group']}', not '{group['id']}'"
                )

    for destination in destinations:
        group_id = destination["group"]
        if group_id is None:
            continue
        if group_id not in groups_by_id:
            raise ValueError(
                f"shared chrome destination '{destination['id']}' references missing "
                f"group '{group_id}'"
            )
        if destination["id"] not in groups_by_id[group_id]["destinations"]:
            raise ValueError(
                f"shared chrome destination '{destination['id']}' references group "
                f"'{group_id}' but is missing from that group's destinations"
            )

    header = _validate_shared_chrome_destination_list(
        raw_header, "header", destinations_by_id
    )
    docs_band = _validate_shared_chrome_destination_list(
        raw_docs_band, "docs_band", destinations_by_id
    )
    docs_product_navigation = _validate_shared_chrome_destination_list(
        raw_docs_product_navigation, "docs_product_navigation", destinations_by_id
    )

    return {
        "header": header,
        "docs_band": docs_band,
        "docs_product_navigation": docs_product_navigation,
        "destinations": destinations,
        "groups": groups,
    }


def load_shared_chrome_contract(site_toml: Path) -> dict:
    """Load and validate the shared-chrome table from the site recipe."""
    with site_toml.open("rb") as f:
        site = tomllib.load(f)
    return validate_shared_chrome_contract(site.get("shared_chrome"))


def project_shared_chrome(contract: object) -> dict[str, dict]:
    """Create independent renderer-local data from one validated contract."""
    canonical = validate_shared_chrome_contract(contract)
    destinations_by_id = {
        destination["id"]: destination for destination in canonical["destinations"]
    }

    def link(destination_id: str) -> dict:
        destination = destinations_by_id[destination_id]
        return {
            "id": destination["id"],
            "label": destination["label"],
            "target": destination["target"],
            "kind": destination["kind"],
        }

    def footer_projection() -> list[dict]:
        return [
            {
                "id": group["id"],
                "label": group["label"],
                "destinations": [
                    link(destination_id) for destination_id in group["destinations"]
                ],
            }
            for group in canonical["groups"]
        ]

    marketing = {
        "header": [link(destination_id) for destination_id in canonical["header"]],
        "footer": footer_projection(),
    }
    docs = {
        "product_orientation_band": [
            link(destination_id) for destination_id in canonical["docs_band"]
        ],
        "product_navigation": [
            link(destination_id)
            for destination_id in canonical["docs_product_navigation"]
        ],
        "footer": footer_projection(),
    }

    return {"marketing": marketing, "docs": docs}


def generate_marketing_shared_chrome_projection(
    contract: object,
    output: Path = MARKETING_SHARED_CHROME_PROJECTION,
    dry_run: bool = False,
) -> dict:
    """Project the marketing chrome input before and after its site build."""
    payload = project_shared_chrome(contract)["marketing"]
    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def assert_marketing_shared_chrome_projection_current(
    contract: object, output: Path = MARKETING_SHARED_CHROME_PROJECTION
) -> None:
    """Reject a marketing input at ``output`` that no longer matches ``site.toml``."""
    expected = project_shared_chrome(contract)["marketing"]
    actual = json.loads(output.read_text(encoding="utf-8"))
    if actual != expected:
        raise ValueError(
            f"{output} is stale — run `python3 tools/build-site.py --journeys-only`"
        )


def generate_docs_shared_chrome_projection(
    contract: object,
    output: Path = DOCS_SHARED_CHROME_PROJECTION,
    dry_run: bool = False,
) -> dict:
    """Project the docs chrome input in the full pre-docs-build pass."""
    payload = project_shared_chrome(contract)["docs"]
    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def assert_docs_shared_chrome_projection_current(
    contract: object, output: Path = DOCS_SHARED_CHROME_PROJECTION
) -> None:
    """Reject a docs input at ``output`` that no longer matches ``site.toml``."""
    expected = project_shared_chrome(contract)["docs"]
    actual = json.loads(output.read_text(encoding="utf-8"))
    if actual != expected:
        raise ValueError(
            f"{output} is stale — run `python3 tools/build-site.py`"
        )


def discover_packs(root: Path, site_toml: Path) -> list[dict]:
    """Return packs ordered by site.toml groups, ungrouped packs appended alphabetically.

    Each dict: {slug, name, display_name, version, scope, description, group}.
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
            "name": name,
            "display_name": display_name,
            "version": p.get("version", ""),
            "scope": p.get("install", {}).get("default-scope", "repo"),
            "allowed_scopes": list(p.get("install", {}).get("allowed-scopes", [])),
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

    # A guidebook step's position, carried into the projected page so the
    # in-page navigation can say "Step 3 of 5" instead of "On this page". The
    # source is the body's own declaration, so the heading, the sidebar number
    # and the page text can never disagree. Non-steps carry neither field and
    # keep the default heading.
    # The packs a page needs render as pills above its title. A page that
    # declares none falls back to the pack that owns it.
    if data.get("pack") and not data.get("uses") and not str(data["pack"]).startswith("_"):
        data = dict(data)
        data["uses"] = [data["pack"]]

    position = _STEP_OF.search(body)
    if position:
        data = dict(data)
        data["step"] = int(position.group(1))
        data["steps"] = int(position.group(2))

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
# surfaced in reader navigation. `CLAUDE.md` is the Claude Code import shim
# beside `AGENTS.md`: one line reading `@AGENTS.md`, with no reader-facing
# content to put in a sidebar.
_NAV_INELIGIBLE_NAMES = frozenset({"AGENTS.md", "CLAUDE.md"})


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
        text = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)

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

        # A guidebook step declares its own position in its body. That
        # declaration -- not `order:` -- is what makes a page a step, because
        # `order:` also carries a cross-kind reading thread (Atlassian's runs
        # tutorial, how-to, reference, explanation) whose members are not steps
        # and must not be numbered as if they were.
        step = _declared_step(text)

        records.append({
            "source_path": path,
            "pack": pack,
            "kind": kind,
            "order": order,
            "step": step,
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


_STEP_DECLARATION = re.compile(r"^\*\*Step (\d+) of \d+ — ", re.M)
_STEP_OF = re.compile(r"^\*\*Step (\d+) of (\d+) — ", re.M)


def _declared_step(text: str) -> int | None:
    """The step number a guidebook page declares in its own body, if any.

    Taken from the body rather than frontmatter so navigation and the page can
    never disagree: the reader sees "Step 3 of 5" on the page and "3." in the
    sidebar because both come from the same statement.
    """
    match = _STEP_DECLARATION.search(text)
    return int(match.group(1)) if match else None


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
        # A guidebook step is numbered in the sidebar, because the run is flat
        # and a reader otherwise sees consecutive siblings with nothing marking
        # them as a sequence. The number comes from the page's own "Step N of M"
        # declaration, so nav and body cannot disagree, and a page that never
        # calls itself a step is left alone. Applied here rather than in
        # `_guide_label` so pack index link text keeps the plain title.
        ordered = sorted((r for r in members if r["order"] is not None and not r["is_index"]),
                         key=lambda r: (r["order"], r["slug"]))
        for rec in ordered:
            item = entry(rec)
            if rec.get("step") is not None:
                item["label"] = f"{rec['step']}. {item['label']}"
            group_items.append(item)
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

def mirror_guides(
    src: Path,
    site_docs: Path,
    dry_run: bool = False,
    public_guides: Path | None = None,
) -> int:
    """Mirror src/ into site_docs/guides/ with frontmatter-aware routing.

    - Files with ``slug:`` frontmatter are written to site_docs/<slug>.md
      (overriding the default path-based placement).
    - Files with ``aliases:`` frontmatter get meta-refresh redirect stubs.
    - Guide-specific metadata (pack, kind, summary, slug, aliases, status,
      journey, order) is stripped before writing so Starlight doesn't see it.
    - Files without frontmatter receive the existing title-injection treatment.
    - docs/guides/ is not the src here and is never mirrored.
    - Non-Markdown files (guide images) are also copied under
      ``public_guides`` when given, because links to them are rewritten to
      ``SITE_BASE/guides/<path>`` and only the site's public/ tree serves that.
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
                if public_guides is not None:
                    public_target = public_guides / rel
                    public_target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, public_target)
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


def guidebook_index(repo_root: Path) -> dict[str, dict]:
    """Map each pack to its guidebook's first step, when it ships one.

    Built from the same inventory the sidebar uses, so the pack page, the
    top-level anchor and the right-hand rail all name one walk and cannot
    disagree about where it starts.
    """
    guides_root = repo_root / "guides"
    if not guides_root.exists():
        return {}
    steps: dict[str, list[dict]] = {}
    for record in build_guide_inventory(guides_root):
        if record["nav_eligible"] and record["pack"] and record.get("step") is not None:
            steps.setdefault(record["pack"], []).append(record)
    index = {}
    for pack, records in steps.items():
        walk = sorted(records, key=lambda r: r["step"])
        index[pack] = {
            "slug": walk[0]["slug"],
            "title": walk[0]["title"] or walk[0]["slug"].rsplit("/", 1)[-1],
            "count": len(walk),
        }
    return index


def _guidebook_banner(entry: dict) -> str:
    """The line a pack page leads with when that pack ships a guidebook.

    A reader who has just found the pack cannot find the walk: the pack README
    says which skill to type first, which is useful only if you already know a
    guided sequence exists. Nothing on the page said one did, and the guides
    tree was reachable only through a link that left for GitHub.
    """
    return (
        f"**New to this pack?** Walk the guidebook — {entry['count']} steps, "
        f"starting at [{entry['title']}]({SITE_BASE}/{entry['slug']}/). "
        "Each step shows what to type, what comes back, and what it writes.\n"
    )


def _rewrite_pack_readme(text: str, pack_src_path: Path,
                         guidebook: dict | None = None) -> str:
    """Rewrite links in pack READMEs moved from packs/<slug>/README.md
    to docs-site/src/content/docs/packs/<slug>.md.

    Pack-home links (../other-pack/README.md) → base-qualified pack route.
    Other repository files, including files beside the README → GitHub URL.

    When the pack ships a guidebook, a pointer to its first step is inserted
    after the tagline. Generated rather than authored into each README so it
    cannot drift from the walk it names, and so the pack sources stay portable
    — the link is a site route that means nothing outside this site.
    """
    if guidebook:
        lines = text.splitlines(keepends=True)
        cut = next(
            (i for i, line in enumerate(lines)
             if i > 0 and line.startswith(("---", "## "))),
            len(lines),
        )
        text = "".join(lines[:cut]) + _guidebook_banner(guidebook) + "\n" + "".join(lines[cut:])
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
    Most targets (AGENTS.md, docs/README.md, etc.) aren't in the site,
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


PACKS_PAGE_SOURCE = REPO_ROOT / "docs-site" / "src" / "packs-page.md"


def build_pack_index(packs: list[dict], out_dir: Path, dry_run: bool = False) -> None:
    """Write the Packs page from its hand-written source. It explains packs and
    lists none: the sidebar's Pack listing is generated, so a second list here
    would only drift."""
    del packs  # the listing lives in the sidebar
    content = (
        '---\ntitle: "Packs"\n'
        'description: "What a pack installs, and when to install it '
        'for the team or for yourself."\n'
        "---\n\n"
        + PACKS_PAGE_SOURCE.read_text(encoding="utf-8").strip()
        + "\n"
    )
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


# ---------------------------------------------------------------------------
# Released changelog Highlights -> the public /now/ projection.
# ---------------------------------------------------------------------------

_CHANGELOG_MODULE = Path(__file__).with_name("changelog.py")
_changelog_spec = importlib.util.spec_from_file_location(
    "product_changelog", _CHANGELOG_MODULE
)
if _changelog_spec is None or _changelog_spec.loader is None:
    raise ImportError(f"cannot load shared changelog module at {_CHANGELOG_MODULE}")
_changelog = importlib.util.module_from_spec(_changelog_spec)
sys.modules[_changelog_spec.name] = _changelog
_changelog_spec.loader.exec_module(_changelog)

ChangelogHeading = _changelog.ChangelogHeading
ParsedChangelog = _changelog.ParsedChangelog
_parse_release_identity = _changelog._parse_release_identity
_project_parsed = _changelog._project_parsed
_Slugger = _changelog._Slugger
_slug_base = _changelog._slug_base
_strip_changelog_comments = _changelog._strip_changelog_comments
highlight_segments = _changelog.highlight_segments
launch_window = _changelog.launch_window
parse_changelog_releases = _changelog.parse_changelog_releases
project_now_highlights = _changelog.project_now_highlights
collect_validated_fragments = _changelog.collect_validated_fragments
collect_changelog_records = _changelog.collect_changelog_records
assemble_changelog = _changelog.assemble_changelog
project_fragment_now_highlights = _changelog.project_fragment_now_highlights
_LOOSE_RELEASED_WARN = _changelog.LOOSE_RELEASED_WARN_THRESHOLD
_LOOSE_RELEASED_REFUSE = _changelog.LOOSE_RELEASED_REFUSE_THRESHOLD
_PENDING_WARN = _changelog.PENDING_WARN_THRESHOLD


def generate_now_projection(
    out: Path,
    changelog: Path,
    dry_run: bool = False,
) -> tuple[dict, dict]:
    """Write the `/now/` projection JSON; return (payload, diagnostics).

    Diagnostics come back with the payload so the caller does not parse a
    4,000-line file a second time to report them.
    """
    parsed = parse_changelog_releases(changelog.read_text(encoding="utf-8"))
    payload = _project_parsed(parsed)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if not dry_run:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
    return payload, parsed.diagnostics


def _released_versions_from_parsed(parsed: ParsedChangelog) -> dict[str, set[str]]:
    """Return every released package version present in historical changelog.

    Thin alias for ``_changelog.released_versions_from_parsed`` (moved to
    changelog.py so that compact and the site build share one inventory,
    preserving AC1's import direction: build-site imports changelog, never
    the reverse).
    """
    return _changelog.released_versions_from_parsed(parsed)


def _version_parts(version: str) -> tuple[int, ...] | None:
    """Return comparable dotted integer version parts, or None if ambiguous."""
    if not re.fullmatch(r"\d+(?:\.\d+)*", version):
        return None
    return tuple(int(part) for part in version.split("."))


def _version_lte(candidate: str, current: str) -> bool:
    """Deterministically compare two pack versions, failing closed on ambiguity."""
    if candidate == current:
        return True
    candidate_parts = _version_parts(candidate)
    current_parts = _version_parts(current)
    if candidate_parts is None or current_parts is None:
        return False
    length = max(len(candidate_parts), len(current_parts))
    padded_candidate = candidate_parts + (0,) * (length - len(candidate_parts))
    padded_current = current_parts + (0,) * (length - len(current_parts))
    return padded_candidate <= padded_current


def _released_versions_from_packs(
    *,
    root: Path,
    site_toml: Path,
    fragments: list,
    historical: dict[str, set[str]],
) -> dict[str, set[str]]:
    """Build the exact release inventory from pack manifests and known history.

    Delegates to ``_changelog.released_versions_from_packs`` with ``discover_packs``
    injected to preserve the import direction: build-site imports changelog, never reverse.
    """
    return _changelog.released_versions_from_packs(
        root=root,
        site_toml=site_toml,
        fragments=fragments,
        historical=historical,
        discover_packs_fn=discover_packs,
    )


def _combined_now_payload(
    parsed: ParsedChangelog, fragments: list, released_versions: dict[str, set[str]]
) -> dict:
    """Project historical and fragment Highlights into one schema-v1 payload."""
    historical = _project_parsed(parsed)
    fragment_payload = project_fragment_now_highlights(fragments, released_versions)
    groups = historical["groups"] + fragment_payload["groups"]
    return {
        "schemaVersion": 1,
        "groups": sorted(groups, key=lambda group: group["date"], reverse=True),
    }


def _changelog_records(fragments: Path) -> tuple[list, list]:
    """Return ``(loose, bundled)`` records through the one reader (AC-B8).

    The bundle directory and retraction list are the fragment directory's
    siblings. An absent fragment directory still yields every bundled record:
    Git keeps no empty directory, so a fully compacted checkout has none.
    """
    return collect_changelog_records(
        fragment_dir=fragments,
        bundle_dir=fragments.parent / "changelog.months",
        retraction_path=fragments.parent / "changelog-retractions.toml",
    )


def generate_changelog_views(
    *,
    changelog: Path,
    fragments: Path,
    now_out: Path,
    changelog_out: Path | None = None,
    dry_run: bool = False,
    root: Path = REPO_ROOT,
    site_toml: Path | None = None,
) -> tuple[dict, dict]:
    """Generate `/now` and optionally the site changelog from one model pass."""
    if not changelog.exists():
        raise FileNotFoundError(f"{changelog} is missing; /now/ cannot be projected")
    historical_text = changelog.read_text(encoding="utf-8")
    parsed = parse_changelog_releases(historical_text)
    loose_records, bundled_records = _changelog_records(fragments)
    fragment_records = loose_records + bundled_records
    historical_inventory = _released_versions_from_parsed(parsed)
    inventory = _released_versions_from_packs(
        root=root,
        site_toml=site_toml or root / "site.toml",
        fragments=fragment_records,
        historical=historical_inventory,
    )
    # AC-B8: the ceiling counts loose fragments only; bundled records never do.
    normalized_inv = _changelog._normalize_released_versions(inventory)
    loose_released = [
        f for f in loose_records
        if _changelog._fragment_in_released_inventory(f, normalized_inv)
    ]
    loose_pending = [
        f for f in loose_records
        if not _changelog._fragment_in_released_inventory(f, normalized_inv)
    ]
    if len(loose_released) > _LOOSE_RELEASED_REFUSE:
        raise _changelog.FragmentValidationError(
            f"{fragments}: {len(loose_released)} released loose fragments exceed the "
            f"hard ceiling of {_LOOSE_RELEASED_REFUSE}; run compact for closed months"
        )
    if len(loose_released) > _LOOSE_RELEASED_WARN:
        import warnings as _warnings
        _warnings.warn(
            f"{fragments}: {len(loose_released)} released loose fragments exceed the "
            f"warning threshold of {_LOOSE_RELEASED_WARN}; consider compacting",
            stacklevel=2,
        )
    if len(loose_pending) > _PENDING_WARN:
        import warnings as _warnings  # noqa: F811  # may already be imported
        _warnings.warn(
            f"{fragments}: {len(loose_pending)} pending loose fragments exceed the "
            f"warning threshold of {_PENDING_WARN}",
            stacklevel=2,
        )
    complete = assemble_changelog(
        historical_text,
        fragment_records,
        released_versions=inventory,
    )
    payload = _combined_now_payload(parsed, fragment_records, inventory)
    rendered_now = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    rendered_changelog = _rewrite_changelog(complete) if changelog_out is not None else None
    # The destination is a Starlight content entry, so docsSchema() requires a
    # title. copy_file injects it for every other .md it writes; this writer
    # must too, or the docs-site build fails the collection schema.
    # _inject_frontmatter also strips the leading H1 it took the title from, so
    # the page does not show its title twice.
    if (
        rendered_changelog is not None
        and changelog_out is not None
        and changelog_out.suffix == ".md"
        and not rendered_changelog.startswith("---")
    ):
        rendered_changelog = _inject_frontmatter(rendered_changelog, changelog)
    if not dry_run:
        now_out.parent.mkdir(parents=True, exist_ok=True)
        if changelog_out is not None:
            changelog_out.parent.mkdir(parents=True, exist_ok=True)
        now_out.write_text(rendered_now, encoding="utf-8")
        if changelog_out is not None and rendered_changelog is not None:
            changelog_out.write_text(rendered_changelog, encoding="utf-8")
    diagnostics = dict(parsed.diagnostics)
    diagnostics["fragment_count"] = len(fragment_records)
    diagnostics["loose_count"] = len(loose_records)
    diagnostics["bundled_count"] = len(bundled_records)
    diagnostics["release_group_count"] = len(payload["groups"])
    diagnostics["highlight_count"] = sum(len(group["highlights"]) for group in payload["groups"])
    return payload, diagnostics


def report_changelog_views(
    *,
    changelog: Path,
    fragments: Path,
    now_out: Path,
    changelog_out: Path | None = None,
    dry_run: bool = False,
) -> tuple[dict, dict]:
    """Generate changelog views and print parity-friendly counts."""
    payload, diagnostics = generate_changelog_views(
        changelog=changelog,
        fragments=fragments,
        now_out=now_out,
        changelog_out=changelog_out,
        dry_run=dry_run,
    )
    print(
        f"  {diagnostics['fragment_count']} fragment(s), "
        f"{diagnostics['release_group_count']} released highlight group(s), "
        f"{diagnostics['highlight_count']} highlight(s)"
        + (" (dry run)" if dry_run else "")
    )
    return payload, diagnostics


def _report_now_projection(changelog: Path, dry_run: bool = False) -> None:
    """Emit the `/now/` projection and print what reached the public page.

    Also names what did NOT publish. Writing a `Highlights` block under an entry
    that is still `[Unreleased]` is the overwhelmingly likely authoring mistake,
    and it is indistinguishable from writing nothing at all if generation only
    reports successes — the author is left reading the parser to find out why
    their copy never appeared.
    """
    if not changelog.exists():
        # Returning here would leave the marketing build rendering whatever
        # projection was last committed — a stale public page reported as a
        # successful build.
        raise FileNotFoundError(
            f"{changelog} is missing; /now/ cannot be projected"
        )
    _, diagnostics = report_changelog_views(
        changelog=changelog,
        fragments=REPO_ROOT / "docs" / "product" / "changelog.d",
        now_out=NOW_PROJECTION,
        dry_run=dry_run,
    )
    for heading, count in diagnostics["withheld_unreleased"]:
        print(
            f"  note  {count} highlight(s) not published — "
            f"beneath [Unreleased]: {heading}"
        )
    for lineno, level, title in diagnostics["misplaced_highlights"]:
        print(
            f"  note  line {lineno}: '{'#' * level} {title}' is not a release "
            "entry's immediate child, so its bullets do not publish"
        )
    for lineno, title in diagnostics["unreleased_regions"]:
        print(
            f"  note  line {lineno}: heading {title!r} reads as Unreleased, so "
            "nothing beneath it publishes; reword it if that is wrong"
        )


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


def project_guidebooks_group(records: list[dict], guide_groups: list[dict],
                             baseline: dict) -> dict | None:
    """Project the packs that ship a guidebook into a top-level anchor group.

    The problem this removes: a reader on a pack page could not find the walk.
    The guides tree is one group of two hundred entries nested among the packs,
    so a guidebook's five steps were reachable only by scrolling to the right
    pack and recognising five consecutive titles as a sequence. Nothing named
    them, and nothing said a walk existed.

    One entry per guidebook, pointing at its first step, placed above the pack
    catalogue — because starting the walk is the thing most readers arriving
    here want to do, and it had no anchor at all.
    """
    labels = {g["dir"]: g.get("label", g["dir"]) for g in guide_groups if g.get("dir")}
    steps: dict[str, list[dict]] = {}
    for record in records:
        if record["nav_eligible"] and record["pack"] and record.get("step") is not None:
            steps.setdefault(record["pack"], []).append(record)
    if not steps:
        return None

    items = []
    for pack in sorted(steps, key=lambda p: labels.get(p, p).casefold()):
        walk = sorted(steps[pack], key=lambda r: r["step"])
        label = labels.get(pack, pack.replace("-", " ").title())
        items.append({"label": label, "slug": walk[0]["slug"]})
    return {"label": "Guidebooks", "items": items}


def build_guides_sidebar_group(
    repo_root: Path, site_toml: Path
) -> tuple[dict | None, dict | None]:
    """Collate the guides tree into the ``Guides`` group and the ``Guidebooks`` anchor."""
    guides_root = repo_root / "guides"
    if not guides_root.exists():
        return None, None
    with site_toml.open("rb") as f:
        site = tomllib.load(f)
    guide_groups = site.get("guide_groups", [])
    # A promoted guide is linked by hand from the Get Started sidebar group, so
    # it is left out of its generated group rather than listed twice.
    promoted = set(site.get("promoted_guides", []))
    records = build_guide_inventory(guides_root)
    baseline = load_guide_baseline(repo_root / "guide-nav-baseline.toml")
    group = project_guide_sidebar(
        [r for r in records if r["slug"] not in promoted], guide_groups, baseline
    )
    guidebooks = project_guidebooks_group(records, guide_groups, baseline)

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
    if guidebooks:
        print(f"  guides  {len(guidebooks['items'])} guidebook(s) anchored at the top level")
    return group, guidebooks


def generate_sidebar_config(packs: list[dict], out: Path, dry_run: bool = False,
                            guides_group: dict | None = None,
                            guidebooks_group: dict | None = None) -> None:
    """Write docs-site/src/sidebar-config.json — an array of Starlight sidebar groups."""
    groups_seen: list[str] = []
    groups_map: dict[str, list[dict]] = {}
    for p in packs:
        g = p["group"]
        if g not in groups_map:
            groups_seen.append(g)
            groups_map[g] = []
        groups_map[g].append({"label": p["display_name"], "slug": f"packs/{p['slug']}"})

    sidebar: list[dict] = []
    if guidebooks_group:
        sidebar.append(guidebooks_group)
    sidebar.append(
        {"label": "Pack Catalogue", "items": [{"label": "All Packs", "slug": "packs"}]}
    )
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
# Receipts
# ---------------------------------------------------------------------------
#
# Every value below is counted from repository files at build time. Nothing
# here is pasted from prose, and no count is written down twice.

# The review loop's completion sentinel. A core agent that iterates a cold
# review of a diff to a verdict declares it in its own frontmatter
# `description`; the agents that do other work (write code, adjudicate
# findings, review a contract rather than a diff) do not. That declaration —
# not a filename list — is what selects the set, so adding a seventh agent
# cannot silently leave this count behind.
_REVIEW_SENTINEL = "Clean — ready to commit."

_CORE_AGENTS_DIR = REPO_ROOT / "packs" / "core" / ".apm" / "agents"
_ADAPTERS_REGISTRY = (
    REPO_ROOT / "packages" / "agentbundle" / "agentbundle"
    / "build" / "adapters" / "__init__.py"
)
_PACKS_DIR = REPO_ROOT / "packs"

RECEIPTS_PROJECTION = REPO_ROOT / "web" / "src" / "lib" / "receipts.generated.json"


def _agent_frontmatter(path: Path) -> dict[str, str]:
    """Return the top-level scalar keys of one agent file's YAML frontmatter.

    Only `key: value` lines at column zero are read. Nested blocks and list
    bodies are skipped, which is all this caller needs: it reads `name` and
    `description`, both of which are top-level scalars in every core agent.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line or line[0].isspace():
            continue
        key, separator, value = line.partition(":")
        if not separator:
            continue
        fields[key.strip()] = value.strip().strip('"')
    return fields


def discover_cold_reviewers(agents_dir: Path = _CORE_AGENTS_DIR) -> list[str] | None:
    """Names of the core agents that iterate a cold diff review to `Clean`.

    Selected by the declared review-loop sentinel in each agent's frontmatter
    `description`, sorted by agent name.

    Returns `None` when `agents_dir` is absent — a tree without the core pack
    has no such receipt to publish. An empty result from a directory that IS
    present is drift and raises, because that is the case where a stale number
    would otherwise reach the page.
    """
    if not agents_dir.is_dir():
        return None
    names = [
        fields["name"]
        for path in sorted(agents_dir.glob("*.md"))
        for fields in [_agent_frontmatter(path)]
        if "name" in fields and _REVIEW_SENTINEL in fields.get("description", "")
    ]
    if not names:
        raise ValueError(
            f"{agents_dir}: no agent declares the review sentinel "
            f"{_REVIEW_SENTINEL!r} — the receipt would publish an empty set"
        )
    return sorted(names)


def discover_adapter_targets(registry: Path = _ADAPTERS_REGISTRY) -> list[str] | None:
    """Contract names in `ADAPTERS` that project through an adapter module.

    Read from the registry's source with `ast`, so no import side effect is
    taken. An entry is counted only when its value is `<module>.project` — the
    form a real adapter takes. `kiro` is excluded on that rule: it is bound to
    a locally defined deprecation wrapper that forwards to `kiro_ide`, and
    `kiro.py` itself is the implementation layer `kiro_cli` and `kiro_ide`
    share, not a target the bundle installs into.

    Returns `None` when the registry file is absent; an empty `ADAPTERS` in a
    registry that IS present is drift and raises.
    """
    if not registry.is_file():
        return None
    tree = ast.parse(registry.read_text(encoding="utf-8"), filename=str(registry))
    names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.AnnAssign | ast.Assign):
            continue
        targets = [node.target] if isinstance(node, ast.AnnAssign) else node.targets
        if not any(isinstance(t, ast.Name) and t.id == "ADAPTERS" for t in targets):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        for key, value in zip(node.value.keys, node.value.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                continue
            if (
                isinstance(value, ast.Attribute)
                and value.attr == "project"
                and isinstance(value.value, ast.Name)
            ):
                names.append(key.value)
    if not names:
        raise ValueError(f"{registry}: no `<module>.project` entries found in ADAPTERS")
    return sorted(names)


def discover_catalogue_packs(
    packs_dir: Path = _PACKS_DIR,
) -> tuple[list[str], list[str]] | None:
    """Return (declared, published) pack directory names under `packs/`.

    Declared: every directory carrying a `pack.toml`. Published: the declared
    subset whose directory name does not start with `_`. The underscore prefix
    is the repository-wide publication marker — `catalogue_tooling`'s packaging,
    index generation, verification and lint passes all skip a pack directory on
    exactly that test, so an underscore pack is declared but never shipped.

    Returns `None` when no directory under `packs_dir` declares a `pack.toml`,
    which is a tree that has no catalogue rather than one of size zero.
    """
    if not packs_dir.is_dir():
        return None
    declared = sorted(
        path.name for path in packs_dir.iterdir() if (path / "pack.toml").is_file()
    )
    if not declared:
        return None
    published = [name for name in declared if not name.startswith("_")]
    return declared, published


def project_receipts() -> dict:
    """Project the receipt records the marketing surface displays beside claims.

    Each record names its machine key, its human label, one or more counted
    values, the enumerated population behind those values, and the repository
    path the count was walked from. A record whose source tree is absent is
    omitted rather than published as zero.
    """
    receipts: list[dict] = []

    reviewers = discover_cold_reviewers()
    if reviewers is not None:
        receipts.append({
            "key": "reviewers",
            "label": "Cold reviewers per diff",
            "source": "packs/core/.apm/agents",
            "values": [{
                "key": "reviewers",
                "label": "Core agents that iterate a diff review to Clean",
                "value": len(reviewers),
            }],
            "items": reviewers,
        })

    adapters = discover_adapter_targets()
    if adapters is not None:
        receipts.append({
            "key": "adapters",
            "label": "Coding agents installed into",
            "source": "packages/agentbundle/agentbundle/build/adapters",
            "values": [{
                "key": "adapters",
                "label": "Adapter targets in the build registry",
                "value": len(adapters),
            }],
            "items": adapters,
        })

    catalogue = discover_catalogue_packs()
    if catalogue is not None:
        declared, published = catalogue
        skills = [
            skill
            for name in published
            for skill in (_PACKS_DIR / name).rglob("SKILL.md")
        ]
        receipts.append({
            "key": "catalogue",
            "label": "Catalogue size",
            "source": "packs",
            "values": [
                {
                    "key": "publishedPacks",
                    "label": "Packs published from packs/",
                    "value": len(published),
                },
                {
                    "key": "declaredPacks",
                    "label": "Directories under packs/ carrying a pack.toml",
                    "value": len(declared),
                },
                {
                    "key": "publishedSkills",
                    "label": "SKILL.md files in published packs",
                    "value": len(skills),
                },
            ],
            "items": published,
        })

    return {"schemaVersion": 1, "receipts": receipts}


def generate_receipts_projection(
    output: Path = RECEIPTS_PROJECTION,
    dry_run: bool = False,
) -> dict:
    """Write the receipts renderer input; return the payload."""
    payload = project_receipts()
    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return payload


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
    parser.add_argument(
        "--renderer-inputs",
        action="store_true",
        help=(
            "Project the four generated renderer inputs and nothing else. "
            "The npm pre-build/pre-test hooks call this: the inputs are not "
            "committed, so each entry point must be able to produce exactly "
            "what it imports without writing any other repository surface."
        ),
    )
    args = parser.parse_args()

    packs_dir = REPO_ROOT / "packs"

    changelog_src = REPO_ROOT / "docs" / "product" / "changelog.md"
    changelog_fragments = REPO_ROOT / "docs" / "product" / "changelog.d"
    changelog_dst = SITE_DOCS / "changelog.md"
    site_toml = REPO_ROOT / "site.toml"
    # Validate the complete shared vocabulary before either build path can
    # project or clean renderer inputs.
    shared_chrome_contract = load_shared_chrome_contract(site_toml)

    if args.renderer_inputs:
        generate_marketing_shared_chrome_projection(
            shared_chrome_contract, dry_run=args.dry_run
        )
        generate_docs_shared_chrome_projection(
            shared_chrome_contract, dry_run=args.dry_run
        )
        _report_now_projection(changelog_src, dry_run=args.dry_run)
        generate_receipts_projection(dry_run=args.dry_run)
        print("build-site: projected 4 renderer input(s)"
              + (" (dry run)" if args.dry_run else ""))
        return

    if args.journeys_only:
        journey_dir = REPO_ROOT / "web" / "src" / "content" / "journeys"
        n = sync_pack_journeys(packs_dir, journey_dir, dry_run=args.dry_run)
        print(
            f"build-site: synced {n} pack journey(s)"
            + (" (dry run)" if args.dry_run else "")
        )
        # Both marketing-renderer inputs are projected in this pre-build phase.
        # Ordering is load-bearing: the workflow runs this pass BEFORE
        # `npm run build --prefix web`, and the full pass only afterwards, so a
        # projection emitted solely by the full pass would always be one build
        # stale for the renderer that consumes it.
        generate_marketing_shared_chrome_projection(
            shared_chrome_contract, dry_run=args.dry_run
        )
        _report_now_projection(changelog_src, dry_run=args.dry_run)
        generate_receipts_projection(dry_run=args.dry_run)
        return

    packs_out = SITE_DOCS / "packs"
    guides_src = REPO_ROOT / "guides"
    guides_out = SITE_DOCS / "guides"

    if args.clean and not args.dry_run:
        for d in (packs_out, guides_out, SITE_PUBLIC_GUIDES):
            if d.exists():
                shutil.rmtree(d)
                print(f"  clean {d.relative_to(REPO_ROOT)}/")

    packs = discover_packs(REPO_ROOT, site_toml)

    print("build-site: copying pack READMEs …")
    # Guarded: every other write in this script honours --dry-run, and this one
    # did not, so `--dry-run` created generated directories on its way to
    # reporting that it would create them. That makes the flag useless as a
    # read-only check — it fails outright against a non-writable tree, and
    # against a writable one it leaves directories behind.
    if not args.dry_run:
        packs_out.mkdir(parents=True, exist_ok=True)
    guidebooks = guidebook_index(REPO_ROOT)
    for p in packs:
        src = packs_dir / p["slug"] / "README.md"
        dst = packs_out / f"{p['slug']}.md"
        if src.exists():
            guidebook = guidebooks.get(p["slug"])
            copy_file(
                src, dst,
                rewriter=lambda t, s=src, g=guidebook: _rewrite_pack_readme(t, s, g),
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
    guides_group, guidebooks_group = build_guides_sidebar_group(REPO_ROOT, site_toml)
    generate_sidebar_config(packs, sidebar_out, dry_run=args.dry_run,
                            guidebooks_group=guidebooks_group,
                            guides_group=guides_group)

    print("build-site: mirroring guides …")
    n = mirror_guides(
        guides_src, SITE_DOCS, dry_run=args.dry_run, public_guides=SITE_PUBLIC_GUIDES
    )
    print(f"  {n} files from guides/")

    print("build-site: projecting released changelog highlights …")
    report_changelog_views(
        changelog=changelog_src,
        fragments=changelog_fragments,
        now_out=NOW_PROJECTION,
        changelog_out=changelog_dst,
        dry_run=args.dry_run,
    )

    print("build-site: projecting marketing shared chrome …")
    generate_marketing_shared_chrome_projection(
        shared_chrome_contract, dry_run=args.dry_run
    )

    print("build-site: projecting receipts …")
    generate_receipts_projection(dry_run=args.dry_run)

    # Docs runs last in the load-bearing build order, so its generated input is
    # refreshed here, immediately before `npm run build --prefix docs-site`;
    # unlike marketing, it is not needed in the journeys-only pass. The input is
    # not committed — `--renderer-inputs` is what an entry point calls to obtain
    # it without running this whole aggregation.
    print("build-site: projecting docs shared chrome …")
    generate_docs_shared_chrome_projection(
        shared_chrome_contract, dry_run=args.dry_run
    )

    print("build-site: changelog projected from shared model")

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
    # rendering site-local, superseding ADR-0109's token-sharing sub-decision. The
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
