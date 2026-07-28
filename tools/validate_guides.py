#!/usr/bin/env python3
"""
Validate guide frontmatter in guides/ against contracts/guide.schema.json.

Usage:
  python tools/validate_guides.py                      # scan guides/ (default)
  python tools/validate_guides.py guides/product-documentation/
  python tools/validate_guides.py guides/product-documentation/getting-started.md
  python tools/validate_guides.py --help

Exit codes:
  0  — all checked files valid (warnings may be emitted to stderr)
  1  — one or more validation errors
  2  — usage error
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent.resolve()
DEFAULT_GUIDES_ROOT = REPO_ROOT / "guides"
DEFAULT_PACKS_ROOT = REPO_ROOT / "packs"
DEFAULT_SCHEMA_PATH = REPO_ROOT / "contracts" / "guide.schema.json"

# _shared is the only approved shared-doc identifier beyond real pack IDs.
APPROVED_SHARED_IDS = {"_shared"}
# _reference is undesignated; validate_paths emits a warning, not an error.
WARN_ONLY_PACK_IDS = {"_reference"}

VALID_KINDS = {"tutorial", "how-to", "reference", "explanation"}


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> dict | None:
    """Return the YAML frontmatter dict, or None if the file has none.

    Frontmatter is between the first pair of '---' delimiters at the start.
    """
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    yaml_block = text[3:end]
    try:
        data = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    return data


# ---------------------------------------------------------------------------
# Pack ID discovery
# ---------------------------------------------------------------------------

def _discover_pack_ids(packs_root: Path) -> set[str]:
    """Return the set of valid pack IDs from packs/*/pack.toml."""
    ids: set[str] = set()
    for pack_toml in packs_root.glob("*/pack.toml"):
        ids.add(pack_toml.parent.name)
    return ids


# ---------------------------------------------------------------------------
# Slug derivation
# ---------------------------------------------------------------------------

def _derive_slug(path: Path, guides_root: Path) -> str:
    """Derive the canonical slug from a guide's source path.

    If the file is at guides/core/explanation/core-pack.md, returns
    'guides/core/explanation/core-pack'. Strips the .md extension.
    """
    rel = path.relative_to(guides_root)
    parts = list(rel.with_suffix("").parts)
    return "/".join(["guides"] + parts)


# ---------------------------------------------------------------------------
# Single-file validation
# ---------------------------------------------------------------------------

def _validate_file(
    path: Path,
    guides_root: Path,
    valid_pack_ids: set[str],
    schema: dict,
    errors: list[str],
    warnings: list[str],
    canonical_slugs: dict[str, Path],
    all_aliases: dict[str, Path],
) -> None:
    """Validate one guide file, appending to errors/warnings and updating slug registries."""
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)

    if fm is None:
        warnings.append(
            f"migration warning: {path} has no frontmatter — "
            "add title, summary, pack, kind to complete migration"
        )
        return

    # JSON Schema validation
    try:
        import jsonschema  # noqa: PLC0415
        validator = jsonschema.Draft7Validator(schema)
        schema_errors = list(validator.iter_errors(fm))
        for e in schema_errors:
            field = ".".join(str(p) for p in e.absolute_path) or e.schema_path[-1]
            errors.append(f"{path}: schema error — {field}: {e.message}")
    except ImportError:
        # Fallback: field-by-field check
        for field in ("title", "summary", "pack", "kind"):
            if field not in fm or not fm[field]:
                errors.append(f"{path}: missing required field '{field}'")
        unknown = set(fm.keys()) - {
            "title", "summary", "pack", "kind",
            "slug", "journey", "order", "aliases", "status",
        }
        for k in sorted(unknown):
            errors.append(f"{path}: unknown field '{k}' (additionalProperties not allowed)")

    # pack ID validation (after schema check so missing-pack is already reported)
    pack = fm.get("pack", "")
    if pack and pack not in valid_pack_ids and pack not in APPROVED_SHARED_IDS:
        if pack in WARN_ONLY_PACK_IDS:
            warnings.append(
                f"{path}: pack '{pack}' is undesignated — "
                "add it to packs/ or use '_shared'; treated as warning for now"
            )
        else:
            errors.append(
                f"{path}: pack '{pack}' is not a valid pack ID "
                f"(not in packs/ directory or '_shared')"
            )

    # kind validation (schema already catches this, but belt-and-suspenders)
    kind = fm.get("kind", "")
    if kind and kind not in VALID_KINDS and not any("kind" in e for e in errors):
        errors.append(f"{path}: invalid kind '{kind}' (must be one of {sorted(VALID_KINDS)})")

    # Slug derivation and duplicate detection
    slug = fm.get("slug") or _derive_slug(path, guides_root)

    if slug in canonical_slugs:
        errors.append(
            f"{path}: duplicate canonical slug '{slug}' — "
            f"also claimed by {canonical_slugs[slug]}"
        )
    else:
        canonical_slugs[slug] = path

    # Alias processing
    aliases = fm.get("aliases") or []
    if isinstance(aliases, list):
        for alias in aliases:
            if alias == slug:
                errors.append(
                    f"{path}: redirect loop — alias '{alias}' equals the canonical slug"
                )
                continue
            if alias in all_aliases:
                errors.append(
                    f"{path}: duplicate alias '{alias}' — "
                    f"already declared by {all_aliases[alias]}"
                )
            else:
                # Alias-vs-canonical collision is checked post-scan in
                # _check_alias_canonical_collisions, once all canonical slugs
                # are known (inline check is order-dependent).
                all_aliases[alias] = path


def _check_alias_canonical_collisions(
    canonical_slugs: dict[str, Path],
    all_aliases: dict[str, Path],
    errors: list[str],
) -> None:
    """Error when an alias matches any canonical slug (order-independent post-scan check)."""
    for alias, source in all_aliases.items():
        if alias in canonical_slugs:
            errors.append(
                f"{source}: alias '{alias}' collides with "
                f"canonical slug of {canonical_slugs[alias]}"
            )


def _check_dangling_aliases(
    canonical_slugs: dict[str, Path],
    all_aliases: dict[str, Path],
    warnings: list[str],
) -> None:
    """Warn about aliases pointing to slugs not in the canonical set."""
    for alias, source in all_aliases.items():
        if alias not in canonical_slugs:
            warnings.append(
                f"{source}: dangling alias '{alias}' — "
                "no canonical guide has this slug (migration staging allowed)"
            )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_paths(
    paths: list[str],
    *,
    guides_root: str | None = None,
    packs_root: str | None = None,
    schema_path: str | None = None,
    exclude_paths: list[str] | None = None,
) -> tuple[int, list[str], list[str]]:
    """Validate guide files at the given paths.

    Returns (exit_code, errors, warnings).
    exit_code 0 = pass, 1 = errors found.
    """
    gr = Path(guides_root) if guides_root else DEFAULT_GUIDES_ROOT
    pr = Path(packs_root) if packs_root else DEFAULT_PACKS_ROOT
    sp = Path(schema_path) if schema_path else DEFAULT_SCHEMA_PATH

    schema = json.loads(sp.read_text(encoding="utf-8"))
    valid_pack_ids = _discover_pack_ids(pr)

    exclude_resolved: set[Path] = set()
    if exclude_paths:
        for ep in exclude_paths:
            exclude_resolved.add(Path(ep).resolve())

    # Collect .md files to validate
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_file() and p.suffix == ".md":
            files.append(p)
        elif p.is_dir():
            files.extend(sorted(p.rglob("*.md")))

    errors: list[str] = []
    warnings: list[str] = []
    canonical_slugs: dict[str, Path] = {}
    all_aliases: dict[str, Path] = {}

    for f in files:
        resolved = f.resolve()
        # Exclusion check: skip files that are inside any excluded path
        skip = False
        for ex in exclude_resolved:
            try:
                resolved.relative_to(ex)
                skip = True
                break
            except ValueError:
                pass
        if skip:
            continue

        # Use the guides root for slug derivation; fall back to the file's parent if outside.
        # Always pass the resolved (absolute) path so relative_to() works correctly.
        effective_root = gr.resolve()
        try:
            resolved.relative_to(effective_root)
        except ValueError:
            effective_root = resolved.parent

        _validate_file(
            resolved,
            effective_root,
            valid_pack_ids,
            schema,
            errors,
            warnings,
            canonical_slugs,
            all_aliases,
        )

    _check_alias_canonical_collisions(canonical_slugs, all_aliases, errors)
    _check_dangling_aliases(canonical_slugs, all_aliases, warnings)

    return (1 if errors else 0), errors, warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=[str(DEFAULT_GUIDES_ROOT)],
        help="Files or directories to validate. Defaults to guides/.",
    )
    parser.add_argument(
        "--guides-root",
        default=str(DEFAULT_GUIDES_ROOT),
        help="Root path for slug derivation (default: guides/).",
    )
    parser.add_argument(
        "--packs-root",
        default=str(DEFAULT_PACKS_ROOT),
        help="Root path for pack ID discovery (default: packs/).",
    )
    args = parser.parse_args(argv)

    # Always exclude docs/guides/ — internal maintainer material, not the external corpus.
    # This guards against accidentally passing docs/ or docs/guides/ as a scan target.
    exclude = [str(REPO_ROOT / "docs" / "guides")]

    code, errors, warnings = validate_paths(
        args.paths,
        guides_root=args.guides_root,
        packs_root=args.packs_root,
        exclude_paths=exclude,
    )

    for w in warnings:
        print(f"warn: {w}", file=sys.stderr)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)

    total = len(errors)
    if code == 0:
        print(f"validate-guides: OK (0 errors, {len(warnings)} warnings)")
    else:
        suffix = "s" if total != 1 else ""
        print(f"validate-guides: FAIL ({total} error{suffix}, {len(warnings)} warnings)")

    return code


if __name__ == "__main__":
    sys.exit(main())
