#!/usr/bin/env python3
"""Intent delivery relation resolver.

Builds a typed, deterministic delivery-relation snapshot from confined
preamble headers in a repository's intent, brief, and spec artifacts.
Every read is confined to the repository root via the repository
file-safety contract loaded co-located. The result is deterministic:
identical artifact trees produce identical serialized bytes.

Relations:
- direct-delivery: a feature intent with route 'spec' (or 'brief' via
  Discovery) whose Discovery field resolves to exactly one matching spec.
- coordinated-delivery: a feature intent with route 'brief' whose single
  matching brief is referenced by at least one spec's Brief field.

Classifications record the delivery outcome for each feature intent with
a declared delivery route. Provenance records contextual references that
do not yield delivery relations. Diagnostics report structural problems.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import stat as _stat
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Co-located file-safety helper loader
# ---------------------------------------------------------------------------

_SCRIPT_DIR: Path = Path(__file__).resolve().parent
_file_safety_module: object | None = None


def _get_file_safety() -> Any:
    """Load the co-located _file_safety.py helper at most once.

    Uses the same discipline as close-work's file_safety loader: lstat
    confirms the helper is a regular non-symlink file before loading, and
    required symbols are asserted after exec.
    """
    global _file_safety_module
    if _file_safety_module is not None:
        return _file_safety_module

    path = _SCRIPT_DIR / "_file_safety.py"
    try:
        st = os.lstat(path)
    except OSError as exc:
        raise ImportError(f"required helper unavailable: {path.name}") from exc
    if not _stat.S_ISREG(st.st_mode) or _stat.S_ISLNK(st.st_mode):
        raise ImportError(f"required helper is not a regular file: {path.name}")

    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("_resolver_file_safety", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"required helper cannot be loaded: {path.name}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop("_resolver_file_safety", None)
        raise
    finally:
        sys.dont_write_bytecode = prev

    _required = {
        "UnsafeContentError", "BoundExceeded",
        "walk_confined_regular_files", "read_confined_regular_file",
    }
    missing = _required - set(vars(mod))
    if missing:
        sys.modules.pop("_resolver_file_safety", None)
        raise ImportError(
            f"required helper is incomplete: {path.name}: {', '.join(sorted(missing))}"
        )
    _file_safety_module = mod
    return mod


# Reconfigure streams to UTF-8 before any I/O.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")  # type: ignore[union-attr]
sys.stderr.reconfigure(encoding="utf-8", errors="strict")  # type: ignore[union-attr]

# ---------------------------------------------------------------------------
# Budget constants
# ---------------------------------------------------------------------------

MAX_ENTRIES: int = 50_000
MAX_FILES: int = 10_000
MAX_DEPTH: int = 8
MAX_ARTIFACT_BYTES: int = 1_000_000
MAX_AGGREGATE_BYTES: int = 67_108_864
MAX_JSON_BYTES: int = 16_777_216

SCHEMA_VERSION: int = 1

# ---------------------------------------------------------------------------
# Regex constants
# ---------------------------------------------------------------------------

_FIELD_LINE = re.compile(r"^- \*\*([^*:]+):\*\*\s*(.*)$")
_COMMENT_SUFFIX = re.compile(r"\s*<!--.*?-->\s*$", re.DOTALL)
_HEADING_PREFIX = "## "
_DECOMPOSED_DATE_ROUTE = re.compile(r"^\d{4}-\d{2}-\d{2}\s+(\S+)$")
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# A spec is named by its directory; an intent or brief file by its file name.
# Anything outside these forms is not admitted, so it never reaches output.
_SPEC_DIR_RE = re.compile(r"^[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*$")
_ARTIFACT_FILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.md$")
_MARKDOWN_LINK = re.compile(r"^\[.*?\]\((.+?)\)\s*$")
_PROVENANCE_TARGET_RE = re.compile(r"^[A-Za-z0-9._/:@#-]{1,200}$")
_INTENTS_PATH_RE = re.compile(r"^docs/product/intents/([^/]+\.md)$")

_DELIVERY_ROUTES: frozenset[str] = frozenset({"spec", "brief", "direct-light", "closed-empty"})

# Canonical diagnostic target forms:
# (a) identifier:   intent/brief:<slug>, spec:<dir>
# (b) artifact path: docs/product/intents/<name>.md or docs/product/briefs/<name>.md
#     (brief paths are emitted by corpus-level slug-ambiguity diagnostics and
#      are already grammar-checked by _ARTIFACT_FILE_RE during traversal)
# (c) date-route:   YYYY-MM-DD <closed-route>  (exactly one space, route in _DELIVERY_ROUTES)
_CANONICAL_IDENTIFIER_RE = re.compile(
    r"^(?:(?:intent|brief):[a-z0-9]+(?:-[a-z0-9]+)*"
    r"|spec:[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)$"
)
_CANONICAL_DATE_ROUTE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2} (?:spec|brief|direct-light|closed-empty)$"
)
_BRIEFS_PATH_TARGET_RE = re.compile(
    r"^docs/product/briefs/[A-Za-z0-9][A-Za-z0-9._-]*\.md$"
)

_PARENT_INTENT_KINDS: tuple[str, ...] = (
    "outcome",
    "opportunity",
    "capability",
    "intent",
)

# ---------------------------------------------------------------------------
# Artifact-root path safety check
# ---------------------------------------------------------------------------


def _check_root_path(root: Path, dir_path: Path) -> str:
    """Check existence and safety of an artifact-root directory path.

    Returns "ok" (exists, no symlinks on the path), "missing" (absent with
    no symlinks on the way), or "unsafe" (a symlink at some component or an
    unexpected OS error accessing it).
    """
    try:
        st = os.lstat(dir_path)
    except FileNotFoundError:
        # Could be truly missing or a dangling/intermediate symlink.
        # Walk components from root to dir_path to distinguish them.
        try:
            rel = dir_path.relative_to(root)
        except ValueError:
            return "unsafe"
        current = root
        for part in rel.parts:
            current = current / part
            try:
                cst = os.lstat(current)
                if _stat.S_ISLNK(cst.st_mode):
                    return "unsafe"
            except FileNotFoundError:
                return "missing"
        return "missing"
    except OSError:
        return "unsafe"
    if _stat.S_ISLNK(st.st_mode):
        return "unsafe"
    return "ok"


# ---------------------------------------------------------------------------
# Preamble helpers
# ---------------------------------------------------------------------------


def _normalize(raw: str) -> str:
    """Strip trailing HTML comment, then one pair of surrounding backticks."""
    value = raw.strip()
    value = _COMMENT_SUFFIX.sub("", value).strip()
    if len(value) >= 2 and value[0] == "`" and value[-1] == "`":
        value = value[1:-1].strip()
    return value


def _preamble_all(text: str) -> dict[str, list[str]]:
    """Return all preamble occurrences as {field_name: [normalized_value, ...]}."""
    fields: dict[str, list[str]] = {}
    for line in text.splitlines():
        if line.startswith(_HEADING_PREFIX):
            break
        m = _FIELD_LINE.match(line)
        if m:
            name = m.group(1).strip()
            value = _normalize(m.group(2))
            fields.setdefault(name, []).append(value)
    return fields


def _first(fields: dict[str, list[str]], key: str) -> str:
    """Return first occurrence of a field, or empty string."""
    values = fields.get(key, [])
    return values[0] if values else ""


# ---------------------------------------------------------------------------
# Discovery value classification
# ---------------------------------------------------------------------------


def _is_unsafe_ref(target: str) -> bool:
    """True when the target is absolute or contains '..' segments."""
    if target.startswith(("/", "\\")):
        return True
    if len(target) >= 2 and target[1] == ":" and target[0].isalpha():
        return True  # Windows drive letter
    parts = re.split(r"[/\\]", target)
    return ".." in parts


def _is_canonical_target(t: str) -> bool:
    """Return True iff ``t`` matches a canonical diagnostic target form.

    (a) A canonical identifier: ``intent/<brief>:<slug>`` or ``spec:<dir>``.
    (b) An artifact path: ``docs/product/intents/<name>.md`` or
        ``docs/product/briefs/<name>.md`` where ``<name>`` matches
        ``_ARTIFACT_FILE_RE``.  Brief paths appear in corpus-level slug-ambiguity
        diagnostics; their filenames are already grammar-checked by
        ``_ARTIFACT_FILE_RE`` during traversal.
    (c) A date-route string: ``YYYY-MM-DD <route>`` with route in
        ``_DELIVERY_ROUTES`` and exactly one space separator.
    """
    if _CANONICAL_IDENTIFIER_RE.fullmatch(t):
        return True
    m = _INTENTS_PATH_RE.fullmatch(t)
    if m and _ARTIFACT_FILE_RE.fullmatch(m.group(1)):
        return True
    if _BRIEFS_PATH_TARGET_RE.fullmatch(t):
        return True
    return bool(_CANONICAL_DATE_ROUTE_RE.fullmatch(t))


def _classify_discovery(value: str) -> tuple[str, str | None]:
    """Classify a normalized Discovery value.

    Returns (classification, extra) where classification is one of:
    - 'none': empty or 'none', skip
    - 'not-intent-shaped': contextual provenance candidate
    - 'unsafe': absolute path or '..' segment
    - 'malformed': intent-shaped but wrong form
    - 'valid-intent': exactly 'intent:<slug>' with valid slug
    - 'valid-path': exactly 'docs/product/intents/<file>.md'
    """
    if not value or value.lower() == "none":
        return "none", None

    # Check for markdown link form (extract target for safety check, then report malformed)
    md_match = _MARKDOWN_LINK.match(value)
    if md_match:
        inner = md_match.group(1).strip()
        # Even markdown links with intent paths are malformed per spec
        if "product/intents/" in inner:
            if _is_unsafe_ref(inner):
                return "unsafe", None
            return "malformed", None
        return "not-intent-shaped", None

    # Intent-shaped: starts with 'intent:' OR contains 'product/intents/'
    if value.startswith("intent:"):
        slug = value[len("intent:"):]
        if not _SLUG_RE.match(slug):
            return "malformed", None
        return "valid-intent", slug

    if "product/intents/" in value:
        if _is_unsafe_ref(value):
            return "unsafe", None
        m = _INTENTS_PATH_RE.match(value)
        if m:
            return "valid-path", m.group(1)
        return "malformed", None

    return "not-intent-shaped", None


# ---------------------------------------------------------------------------
# Decomposed parsing
# ---------------------------------------------------------------------------


def _parse_decomposed(value: str) -> tuple[str | None, bool]:
    """Parse a Decomposed: value.

    Returns (route_token, is_malformed).
    route_token is None when absent/no or non-delivery well-formed token.
    is_malformed is True when value doesn't match the date pattern and isn't
    'no' or empty.
    """
    if not value or value == "no":
        return None, False
    m = _DECOMPOSED_DATE_ROUTE.match(value)
    if m:
        return m.group(1), False
    return None, True


# ---------------------------------------------------------------------------
# Provenance target safety check
# ---------------------------------------------------------------------------


def _safe_provenance_target(value: str) -> str | None:
    """Return value if safe for inclusion in a provenance target field, else None.

    Applies the same absolute-path rule as ``_is_unsafe_ref``, covering leading
    slash, backslash, drive letters (``C:``), and ``..`` segments.
    """
    if not value:
        return None
    if not _PROVENANCE_TARGET_RE.match(value):
        return None
    if _is_unsafe_ref(value):
        return None
    return value


# ---------------------------------------------------------------------------
# Sort helper
# ---------------------------------------------------------------------------


def _dict_sort_key(d: dict[str, Any]) -> str:
    """Total sort key: serialize dict with sorted keys."""
    return json.dumps(
        d, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _sorted_list(lst: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(lst, key=_dict_sort_key)


# ---------------------------------------------------------------------------
# Main resolver
# ---------------------------------------------------------------------------


def resolve_repository(
    root: Path,
    *,
    limits: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Build and return the delivery relation snapshot for the repository at root.

    Returns a dict with schema_version, complete, relations, classifications,
    provenance, diagnostics, and artifacts.
    """
    file_safety = _get_file_safety()

    lim: dict[str, int] = {
        "entries": MAX_ENTRIES,
        "files": MAX_FILES,
        "depth": MAX_DEPTH,
        "artifact-bytes": MAX_ARTIFACT_BYTES,
        "aggregate-bytes": MAX_AGGREGATE_BYTES,
        "json-bytes": MAX_JSON_BYTES,
    }
    if limits:
        lim.update(limits)

    def _incomplete(limit_name: str, root_rel: str) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "complete": False,
            "relations": [],
            "classifications": [],
            "provenance": [],
            "diagnostics": [
                {
                    "code": "delivery-resource-limit",
                    "limit": limit_name,
                    "root": root_rel,
                }
            ],
            "artifacts": {},
        }

    def _unsafe_incomplete() -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "complete": False,
            "relations": [],
            "classifications": [],
            "provenance": [],
            "diagnostics": [],
            "artifacts": {},
        }

    intents_root = root / "docs" / "product" / "intents"
    briefs_root = root / "docs" / "product" / "briefs"
    specs_root = root / "docs" / "specs"

    # Walk all roots with shared budgets
    entries_remaining = lim["entries"]
    files_remaining = lim["files"]

    _budget_name_map = {
        "entries": "entries",
        "files": "files",
        "depth": "depth",
        "per-file-bytes": "artifact-bytes",
        "total-bytes": "aggregate-bytes",
    }

    corpus_files: dict[str, list[Path]] = {}
    for dir_key, dir_path in [
        ("intents", intents_root),
        ("briefs", briefs_root),
        ("specs", specs_root),
    ]:
        # Missing root is empty; a symlink at any component is unsafe.
        root_status = _check_root_path(root, dir_path)
        if root_status == "missing":
            corpus_files[dir_key] = []
            continue
        if root_status == "unsafe":
            return _unsafe_incomplete()

        try:
            walk = file_safety.walk_confined_regular_files(
                root,
                dir_path,
                max_entries=entries_remaining,
                max_files=files_remaining,
                max_depth=lim["depth"],
            )
        except file_safety.BoundExceeded as exc:
            limit_name = _budget_name_map.get(exc.budget, exc.budget)
            rel_root = dir_path.relative_to(root).as_posix()
            return _incomplete(limit_name, rel_root)
        except file_safety.UnsafeContentError:
            return _unsafe_incomplete()

        entries_remaining -= walk.entries_seen
        files_remaining -= len(walk.files)
        corpus_files[dir_key] = walk.files

    # Read and parse artifacts
    aggregate_bytes = 0

    _LIMIT_ARTIFACT = "__LIMIT_ARTIFACT__"
    _LIMIT_AGGREGATE = "__LIMIT_AGGREGATE__"
    _UNSAFE = "__UNSAFE__"

    def _read(path: Path) -> str:
        nonlocal aggregate_bytes
        try:
            raw = file_safety.read_confined_regular_file(
                root, path, max_bytes=lim["artifact-bytes"]
            )
        except file_safety.BoundExceeded:
            return _LIMIT_ARTIFACT
        except file_safety.UnsafeContentError:
            return _UNSAFE
        aggregate_bytes += len(raw)
        if aggregate_bytes > lim["aggregate-bytes"]:
            return _LIMIT_AGGREGATE
        try:
            return raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return _UNSAFE

    # Build intent index
    # slug -> {id, path, rel_path, fields}
    intent_by_slug: dict[str, dict[str, Any]] = {}
    # path-relative -> slug (for path-based Discovery resolution)
    intent_by_path: dict[str, str] = {}
    # Slugs seen more than once: slug -> sorted list of rel_paths
    slug_paths: dict[str, list[str]] = {}

    for f in corpus_files.get("intents", []):
        if f.parent != intents_root or not _ARTIFACT_FILE_RE.fullmatch(f.name):
            continue
        text = _read(f)
        if text == _LIMIT_ARTIFACT:
            return _incomplete("artifact-bytes", "docs/product/intents")
        if text == _LIMIT_AGGREGATE:
            return _incomplete("aggregate-bytes", "docs/product/intents")
        if text == _UNSAFE:
            return _unsafe_incomplete()

        fields = _preamble_all(text)
        slug = _first(fields, "Slug")
        if not slug or _first(fields, "Tombstone"):
            continue
        if not _SLUG_RE.match(slug):
            continue

        rel_path = f.relative_to(root).as_posix()
        slug_paths.setdefault(slug, []).append(rel_path)
        if slug not in intent_by_slug:
            intent_by_slug[slug] = {
                "id": f"intent:{slug}",
                "path": f,
                "rel_path": rel_path,
                "fields": fields,
            }
        intent_by_path[rel_path] = slug

    # Build brief index
    brief_by_slug: dict[str, dict[str, Any]] = {}
    brief_slug_paths: dict[str, list[str]] = {}  # slug -> [rel_path, ...]

    for f in corpus_files.get("briefs", []):
        if f.parent != briefs_root or not _ARTIFACT_FILE_RE.fullmatch(f.name):
            continue
        text = _read(f)
        if text == _LIMIT_ARTIFACT:
            return _incomplete("artifact-bytes", "docs/product/briefs")
        if text == _LIMIT_AGGREGATE:
            return _incomplete("aggregate-bytes", "docs/product/briefs")
        if text == _UNSAFE:
            return _unsafe_incomplete()

        fields = _preamble_all(text)
        slug = _first(fields, "Slug")
        if not slug:
            continue
        if not _SLUG_RE.match(slug):
            continue
        rel_path = f.relative_to(root).as_posix()
        brief_slug_paths.setdefault(slug, []).append(rel_path)
        if slug not in brief_by_slug:
            brief_by_slug[slug] = {
                "id": f"brief:{slug}",
                "path": f,
                "rel_path": rel_path,
                "fields": fields,
            }

    # Build spec index
    spec_by_id: dict[str, dict[str, Any]] = {}

    for f in corpus_files.get("specs", []):
        if f.name != "spec.md" or f.parent.parent != specs_root:
            continue
        text = _read(f)
        if text == _LIMIT_ARTIFACT:
            return _incomplete("artifact-bytes", "docs/specs")
        if text == _LIMIT_AGGREGATE:
            return _incomplete("aggregate-bytes", "docs/specs")
        if text == _UNSAFE:
            return _unsafe_incomplete()

        fields = _preamble_all(text)
        dir_name = f.parent.name
        if not _SPEC_DIR_RE.fullmatch(dir_name):
            continue
        spec_id = f"spec:{dir_name}"
        spec_by_id[spec_id] = {
            "id": spec_id,
            "path": f,
            "rel_path": f.relative_to(root).as_posix(),
            "fields": fields,
        }

    # Collect outputs
    relations: list[dict[str, Any]] = []
    classifications: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []

    # Corpus-level ambiguous intent slugs (two files claiming the same slug)
    ambiguous_slugs: dict[str, list[str]] = {
        slug: sorted(paths)
        for slug, paths in slug_paths.items()
        if len(paths) > 1
    }
    for slug, sorted_paths in sorted(ambiguous_slugs.items()):
        # Keep only canonical target forms (intent paths are form-b; file names
        # must match _ARTIFACT_FILE_RE).
        canonical_ts = [p for p in sorted_paths if _is_canonical_target(p)]
        diagnostics.append({
            "code": "delivery-relation-ambiguous",
            "targets": canonical_ts,
        })
        # Remove from usable index
        intent_by_slug.pop(slug, None)

    # Corpus-level ambiguous brief slugs (two files claiming the same slug)
    ambiguous_brief_slugs: dict[str, list[str]] = {
        slug: sorted(paths)
        for slug, paths in brief_slug_paths.items()
        if len(paths) > 1
    }
    for slug, sorted_paths in sorted(ambiguous_brief_slugs.items()):
        # Brief paths (docs/product/briefs/…) are canonical form-b targets;
        # filenames were already validated by _ARTIFACT_FILE_RE during traversal.
        canonical_ts = [p for p in sorted_paths if _is_canonical_target(p)]
        diagnostics.append({
            "code": "delivery-relation-ambiguous",
            "targets": canonical_ts,
        })
        brief_by_slug.pop(slug, None)

    # Identify feature intents and their delivery routes
    # slug -> {id, route, fields}
    feature_intents: dict[str, dict[str, Any]] = {}

    for slug, intent in intent_by_slug.items():
        fields = intent["fields"]
        level = _first(fields, "Level")
        if level.lower() != "feature":
            continue

        intent_id = f"intent:{slug}"
        decomposed_values = fields.get("Decomposed", [])
        distinct_dec = list(dict.fromkeys(decomposed_values))

        if len(distinct_dec) > 1:
            # Emit only canonical "YYYY-MM-DD <route>" forms; reconstruct
            # from parsed components to exclude hostile whitespace or chars.
            safe_targets = []
            for dv in distinct_dec:
                m = _DECOMPOSED_DATE_ROUTE.match(dv)
                if m:
                    route_token = m.group(1)
                    if route_token in _DELIVERY_ROUTES:
                        date_part = dv[:10]  # "YYYY-MM-DD" is always 10 chars
                        safe_targets.append(f"{date_part} {route_token}")
            diagnostics.append({
                "code": "delivery-relation-ambiguous",
                "subject": intent_id,
                "field": "Decomposed",
                "targets": sorted(safe_targets),
            })
            continue

        raw_dec = distinct_dec[0] if distinct_dec else ""
        route_token, is_malformed = _parse_decomposed(raw_dec)

        if is_malformed:
            diagnostics.append({
                "code": "delivery-reference-malformed",
                "subject": intent_id,
                "field": "Decomposed",
            })
            continue

        if route_token is None or route_token not in _DELIVERY_ROUTES:
            continue

        feature_intents[slug] = {
            "id": intent_id,
            "route": route_token,
            "fields": fields,
        }

    # Resolve a Discovery value against the index.
    # Returns (resolved_slug, classification) where classification is one of:
    # 'resolved', 'ambiguous-slug', 'not-found', 'unsafe', 'malformed',
    # 'not-intent-shaped', 'none'
    def _resolve_disc(dv: str) -> tuple[str | None, str]:
        cls, extra = _classify_discovery(dv)
        if cls in ("none", "not-intent-shaped"):
            return None, cls
        if cls == "unsafe":
            return None, "unsafe"
        if cls == "malformed":
            return None, "malformed"
        if cls == "valid-intent":
            slug = extra
            if slug in ambiguous_slugs:
                return None, "ambiguous-slug"
            if slug in intent_by_slug:
                return slug, "resolved"
            return None, "not-found"
        if cls == "valid-path":
            filename = extra
            rel = f"docs/product/intents/{filename}"
            slug = intent_by_path.get(rel)
            if slug is None:
                return None, "not-found"
            if slug in ambiguous_slugs:
                return None, "ambiguous-slug"
            return slug, "resolved"
        return None, "none"

    # Process each spec's Contract: and Discovery: values
    # Returns list of feature slugs this spec contributes to via Discovery
    spec_delivery_intents: dict[str, set[str]] = {}  # spec_id -> feature slugs
    spec_brief_slugs: dict[str, set[str]] = {}  # spec_id -> brief slugs (non-ambiguous)

    for spec_id, spec in spec_by_id.items():
        fields = spec["fields"]

        # Contract: provenance
        for cv in fields.get("Contract", []):
            if cv and cv.lower() != "none":
                prov: dict[str, Any] = {"subject": spec_id, "field": "Contract"}
                t = _safe_provenance_target(cv)
                if t:
                    prov["target"] = t
                provenance.append(prov)

        # Discovery: analysis
        disc_raw = fields.get("Discovery", [])
        distinct_disc = list(dict.fromkeys(disc_raw))

        # Classify each distinct Discovery value
        disc_classified: list[tuple[str, str | None, str]] = []
        # (normalized_value, resolved_slug_or_None, classification)
        for dv in distinct_disc:
            resolved_slug, cls = _resolve_disc(dv)
            disc_classified.append((dv, resolved_slug, cls))

        # Emit diagnostics for unsafe / malformed values
        for dv, _resolved_slug, cls in disc_classified:
            if cls == "unsafe":
                diagnostics.append({
                    "code": "delivery-reference-unsafe",
                    "subject": spec_id,
                    "field": "Discovery",
                })
            elif cls == "malformed":
                diagnostics.append({
                    "code": "delivery-reference-malformed",
                    "subject": spec_id,
                    "field": "Discovery",
                })
            elif cls == "not-intent-shaped":
                prov = {"subject": spec_id, "field": "Discovery"}
                t = _safe_provenance_target(dv)
                if t:
                    prov["target"] = t
                provenance.append(prov)

        # Valid contributions: resolved or not-found
        valid_disc = [(dv, slug, cls) for dv, slug, cls in disc_classified
                      if cls in ("resolved", "not-found")]

        delivery_feature_slugs: set[str] = set()

        if valid_disc:
            # Compute canonical IDs for ambiguity check
            # resolved -> intent slug; not-found -> unique key per value
            canonical_ids: list[str] = []
            for dv, slug, cls in valid_disc:
                if cls == "resolved" and slug is not None:
                    canonical_ids.append(slug)
                else:
                    canonical_ids.append(f"\x00not-found\x00{dv}")

            if len(set(canonical_ids)) > 1:
                # Ambiguous Discovery: emit only canonical identifier or path forms.
                # For resolved entries use the canonical identifier; for not-found
                # entries keep the raw value only when it already is canonical.
                safe_targets = []
                for dv, slug, cls in valid_disc:
                    if cls == "resolved" and slug is not None:
                        safe_targets.append(f"intent:{slug}")
                    elif _is_canonical_target(dv):
                        safe_targets.append(dv)
                diagnostics.append({
                    "code": "delivery-relation-ambiguous",
                    "subject": spec_id,
                    "field": "Discovery",
                    "targets": sorted(safe_targets),
                })
            else:
                # Not ambiguous: process single canonical target
                for dv, slug, cls in valid_disc:
                    if cls == "not-found":
                        diagnostics.append({
                            "code": "delivery-target-missing",
                            "subject": spec_id,
                            "field": "Discovery",
                        })
                    elif cls == "resolved" and slug is not None:
                        if slug in feature_intents:
                            route = feature_intents[slug]["route"]
                            if route in ("spec", "brief"):
                                delivery_feature_slugs.add(slug)
                            else:
                                # Feature with non-delivery route (direct-light,
                                # closed-empty) => contextual provenance with
                                # the resolved intent identifier.
                                prov: dict[str, Any] = {
                                    "subject": spec_id,
                                    "field": "Discovery",
                                    "intent": feature_intents[slug]["id"],
                                }
                                t = _safe_provenance_target(dv)
                                if t:
                                    prov["target"] = t
                                provenance.append(prov)
                        else:
                            # Resolves to a non-feature intent => provenance with intent
                            intent_id_ref = f"intent:{slug}"
                            prov = {
                                "subject": spec_id,
                                "field": "Discovery",
                                "intent": intent_id_ref,
                            }
                            t = _safe_provenance_target(dv)
                            if t:
                                prov["target"] = t
                            provenance.append(prov)

        if delivery_feature_slugs:
            spec_delivery_intents[spec_id] = delivery_feature_slugs

        # Brief: analysis
        brief_raw = fields.get("Brief", [])
        distinct_brief = list(dict.fromkeys(brief_raw))
        valid_brief: list[tuple[str, str | None]] = []  # (value, slug_or_None)

        for bv in distinct_brief:
            if not bv or bv.lower() == "none":
                continue
            if _is_unsafe_ref(bv):
                diagnostics.append({
                    "code": "delivery-reference-unsafe",
                    "subject": spec_id,
                    "field": "Brief",
                })
                continue
            if not bv.startswith("brief:"):
                diagnostics.append({
                    "code": "delivery-reference-malformed",
                    "subject": spec_id,
                    "field": "Brief",
                })
                continue
            brief_slug = bv[len("brief:"):]
            if not _SLUG_RE.match(brief_slug):
                diagnostics.append({
                    "code": "delivery-reference-malformed",
                    "subject": spec_id,
                    "field": "Brief",
                })
                continue
            valid_brief.append((bv, brief_slug))

        if len(valid_brief) > 1:
            safe_targets = [bv for bv, _ in valid_brief]
            diagnostics.append({
                "code": "delivery-relation-ambiguous",
                "subject": spec_id,
                "field": "Brief",
                "targets": sorted(safe_targets),
            })
        else:
            resolved_brief_slugs: set[str] = set()
            for _bv, brief_slug in valid_brief:
                if brief_slug is None:
                    continue
                if brief_slug in brief_by_slug:
                    resolved_brief_slugs.add(brief_slug)
                else:
                    diagnostics.append({
                        "code": "delivery-target-missing",
                        "subject": spec_id,
                        "field": "Brief",
                    })
            if resolved_brief_slugs:
                spec_brief_slugs[spec_id] = resolved_brief_slugs

    # Process each brief's Parent intent:
    # brief_slug -> set of feature intent slugs it links to
    brief_feature_slugs: dict[str, set[str]] = {}

    for brief_slug, brief in brief_by_slug.items():
        fields = brief["fields"]
        parent_raw = fields.get("Parent intent", [])
        distinct_parents = list(dict.fromkeys(parent_raw))
        valid_parents: list[tuple[str, str]] = []  # (value, intent_slug)

        for pv in distinct_parents:
            if not pv or pv.lower().startswith("none"):
                continue
            if _is_unsafe_ref(pv):
                diagnostics.append({
                    "code": "delivery-reference-unsafe",
                    "subject": f"brief:{brief_slug}",
                    "field": "Parent intent",
                })
                continue
            matched_kind = None
            for kind in _PARENT_INTENT_KINDS:
                if pv.startswith(f"{kind}:"):
                    matched_kind = kind
                    break
            if matched_kind is None:
                diagnostics.append({
                    "code": "delivery-reference-malformed",
                    "subject": f"brief:{brief_slug}",
                    "field": "Parent intent",
                })
                continue
            intent_slug = pv[len(matched_kind) + 1:]
            if not _SLUG_RE.match(intent_slug):
                diagnostics.append({
                    "code": "delivery-reference-malformed",
                    "subject": f"brief:{brief_slug}",
                    "field": "Parent intent",
                })
                continue
            valid_parents.append((pv, intent_slug))

        if len(valid_parents) > 1:
            safe_targets = [pv for pv, _ in valid_parents]
            diagnostics.append({
                "code": "delivery-relation-ambiguous",
                "subject": f"brief:{brief_slug}",
                "field": "Parent intent",
                "targets": sorted(safe_targets),
            })
        else:
            feat_slugs: set[str] = set()
            for _pv, intent_slug in valid_parents:
                if intent_slug in feature_intents:
                    feat_slugs.add(intent_slug)
            if feat_slugs:
                brief_feature_slugs[brief_slug] = feat_slugs

    # Derive relations and classifications for each feature intent
    for feat_slug, feat in sorted(feature_intents.items()):
        feat_id = feat["id"]
        route = feat["route"]

        if route in ("direct-light", "closed-empty"):
            classifications.append({
                "classification": "no-durable-child",
                "intent": feat_id,
                "route": route,
            })
            continue

        if route == "spec":
            matching_specs = sorted(
                spec_id for spec_id, slugs in spec_delivery_intents.items()
                if feat_slug in slugs
            )
            if len(matching_specs) == 0:
                diagnostics.append({
                    "code": "delivery-target-missing",
                    "subject": feat_id,
                })
                classifications.append({
                    "classification": "unresolved",
                    "intent": feat_id,
                    "route": route,
                })
            elif len(matching_specs) == 1:
                spec_id = matching_specs[0]
                relations.append({
                    "basis": {"intent": "Decomposed", "spec": "Discovery"},
                    "intent": feat_id,
                    "route": "spec",
                    "spec": spec_id,
                    "type": "direct-delivery",
                })
                classifications.append({
                    "classification": "direct-delivery",
                    "intent": feat_id,
                    "route": route,
                })
            else:
                diagnostics.append({
                    "code": "delivery-projection-mismatch",
                    "subject": feat_id,
                    "targets": matching_specs,
                })
                classifications.append({
                    "classification": "unresolved",
                    "intent": feat_id,
                    "route": route,
                })

        elif route == "brief":
            # Discovery-backed direct relations co-exist with coordinated ones
            direct_specs = sorted(
                spec_id for spec_id, slugs in spec_delivery_intents.items()
                if feat_slug in slugs
            )
            for spec_id in direct_specs:
                relations.append({
                    "basis": {"intent": "Decomposed", "spec": "Discovery"},
                    "intent": feat_id,
                    "route": "brief",
                    "spec": spec_id,
                    "type": "direct-delivery",
                })

            # Coordinated delivery: find briefs whose Parent intent points to this feature
            matching_briefs = sorted(
                bs for bs, feat_slugs in brief_feature_slugs.items()
                if feat_slug in feat_slugs
            )
            if len(matching_briefs) == 0:
                diagnostics.append({
                    "code": "delivery-target-missing",
                    "subject": feat_id,
                })
                if not direct_specs:
                    classifications.append({
                        "classification": "unresolved",
                        "intent": feat_id,
                        "route": route,
                    })
                else:
                    classifications.append({
                        "classification": "direct-delivery",
                        "intent": feat_id,
                        "route": route,
                    })
            elif len(matching_briefs) > 1:
                diagnostics.append({
                    "code": "delivery-projection-mismatch",
                    "subject": feat_id,
                    "targets": [f"brief:{bs}" for bs in matching_briefs],
                })
                if not direct_specs:
                    classifications.append({
                        "classification": "unresolved",
                        "intent": feat_id,
                        "route": route,
                    })
                else:
                    classifications.append({
                        "classification": "direct-delivery",
                        "intent": feat_id,
                        "route": route,
                    })
            else:
                brief_slug = matching_briefs[0]
                brief_id = f"brief:{brief_slug}"
                coord_specs = sorted(
                    spec_id for spec_id, bslugs in spec_brief_slugs.items()
                    if brief_slug in bslugs
                )
                for spec_id in coord_specs:
                    relations.append({
                        "basis": {
                            "brief": "Parent intent",
                            "intent": "Decomposed",
                            "spec": "Brief",
                        },
                        "brief": brief_id,
                        "intent": feat_id,
                        "route": "brief",
                        "spec": spec_id,
                        "type": "coordinated-delivery",
                    })
                if coord_specs or direct_specs:
                    cls_val = "coordinated-delivery" if coord_specs else "direct-delivery"
                    classifications.append({
                        "classification": cls_val,
                        "intent": feat_id,
                        "route": route,
                    })
                else:
                    classifications.append({
                        "classification": "unresolved",
                        "intent": feat_id,
                        "route": route,
                    })

    # Build artifacts map: every identifier that appears in a relation or
    # provenance record, mapped to its repo-relative artifact path.
    def _get_artifact_path(ident: str) -> str | None:
        if ident.startswith("intent:"):
            slug = ident[len("intent:"):]
            entry = intent_by_slug.get(slug)
            return entry["rel_path"] if entry else None
        if ident.startswith("spec:"):
            entry = spec_by_id.get(ident)
            return entry["rel_path"] if entry else None
        if ident.startswith("brief:"):
            slug = ident[len("brief:"):]
            entry = brief_by_slug.get(slug)
            return entry["rel_path"] if entry else None
        return None

    artifacts: dict[str, str] = {}
    for rel in relations:
        for key in ("intent", "spec", "brief"):
            val = rel.get(key)
            if val and val not in artifacts:
                p = _get_artifact_path(val)
                if p:
                    artifacts[val] = p
    for prov_rec in provenance:
        for key in ("subject", "intent"):
            val = prov_rec.get(key)
            if val and val not in artifacts:
                p = _get_artifact_path(val)
                if p:
                    artifacts[val] = p

    # Assemble and check JSON size
    snapshot: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "complete": True,
        "relations": _sorted_list(relations),
        "classifications": _sorted_list(classifications),
        "provenance": _sorted_list(provenance),
        "diagnostics": _sorted_list(diagnostics),
        "artifacts": dict(sorted(artifacts.items())),
    }

    json_str = (
        json.dumps(
            snapshot,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )
    if len(json_str.encode("utf-8")) > lim["json-bytes"]:
        return _incomplete("json-bytes", ".")

    return snapshot


# ---------------------------------------------------------------------------
# Serializer (shared by the CLI and in-process callers)
# ---------------------------------------------------------------------------


def serialize(snapshot: dict[str, Any]) -> str:
    """Return the canonical JSON serialization of a snapshot."""
    return (
        json.dumps(
            snapshot,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; returns exit code."""
    parser = argparse.ArgumentParser(
        prog="intent_delivery_relations.py",
        description=(
            "What delivery relations does this repository declare? "
            "Reads the header lines of specs, briefs, and intents to build a "
            "typed JSON snapshot and prints it to stdout. "
            "Exit 0: complete snapshot. Exit 1: incomplete snapshot "
            "(JSON still printed; caused by a resource limit, reported in "
            "`diagnostics` as `delivery-resource-limit` with its `limit` and "
            "`root` values, or an unsafe file such as a link, special file, or "
            "non-UTF-8 file, which leaves `diagnostics` empty). "
            "Exit 2: usage error or required helper missing."
        ),
    )
    parser.add_argument(
        "--root",
        metavar="DIR",
        default=".",
        help="Repository root directory (default: current directory).",
    )
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        raise
    try:
        _get_file_safety()
    except ImportError as exc:
        sys.stderr.write(f"intent_delivery_relations: {exc}\n")
        return 2
    root = Path(args.root).resolve()
    snapshot = resolve_repository(root)
    sys.stdout.write(serialize(snapshot))
    return 0 if snapshot.get("complete") else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        sys.stderr.write(
            "intent_delivery_relations: unexpected error; check arguments and try again\n"
        )
        sys.exit(2)
