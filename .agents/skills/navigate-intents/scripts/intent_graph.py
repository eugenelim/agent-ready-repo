"""Intent edge graph derivation for the navigate-intents skill.

Entry point: ``derive(root)`` returns the graph as a plain dict with
``nodes`` and ``edges`` keys.  All file reads are confined through the
co-located ``_file_safety.py``.  Standard-library-only; no third-party
packages.

Node shape
----------
Every node carries ``id``, ``type`` (``intent`` / ``brief`` / ``spec``),
``path`` (repo-relative), and ``status`` (raw ``Status:`` value).
Intent and brief nodes also carry ``slug``.  Intent nodes also carry
``level`` (raw ``Level:`` value) and ``kind`` (raw ``Kind:`` value).

Edge shape
----------
Every edge carries ``from``, ``field``, ``form``, ``trust_class``, and
``basis``.  Resolved edges add ``to`` and ``value``.  Refused edges add
``state`` and ``value``.  ``multiple_values`` edges omit ``form``,
``basis``, and ``value``.  ``retired_target`` edges also carry
``reissued_as`` when the tombstone records it.
"""

from __future__ import annotations

import importlib.util
import os
import re
import stat as _stat
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCRIPT_DIR: Path = Path(__file__).resolve().parent
_HEADING_PREFIX = "## "
_FIELD_LINE_RE = re.compile(r"^- \*\*([^*:]+):\*\*\s*(.*)$")
_COMMENT_SUFFIX_RE = re.compile(r"\s*<!--.*?-->\s*$", re.DOTALL)
_MARKDOWN_LINK_RE = re.compile(r"^\[.*?\]\((.+?)\)\s*$")

#: Maximum per-artifact size; a larger file fails the whole derivation.
MAX_ARTIFACT_BYTES: int = 1_000_000

#: Trust class for every derivation edge: no forward check governs these fields yet.
_TRUST_CLASS = "pointer_unchecked"

# ---------------------------------------------------------------------------
# Integrity failure
# ---------------------------------------------------------------------------


class DerivationError(Exception):
    """Integrity failure raised by ``derive()``; carries the integrity failure code.

    The code is one of ``unsafe_input``, ``input_too_large``,
    ``malformed_record``, or ``duplicate_identity``, checked in that order
    by ``derive()``.  The CLI (T3) converts this to a ``status: error``
    envelope.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------------------
# Co-located helper loaders
# ---------------------------------------------------------------------------

_file_safety_mod: Any = None
_resolver_mod: Any = None


def _get_file_safety() -> Any:
    """Load the co-located ``_file_safety.py`` helper at most once."""
    global _file_safety_mod
    if _file_safety_mod is not None:
        return _file_safety_mod
    path = _SCRIPT_DIR / "_file_safety.py"
    try:
        st = os.lstat(path)
    except OSError as exc:
        raise ImportError("required helper unavailable: _file_safety.py") from exc
    if not _stat.S_ISREG(st.st_mode) or _stat.S_ISLNK(st.st_mode):
        raise ImportError("required helper is not a regular file: _file_safety.py")
    name = "core_navigate_intents_file_safety"
    if name in sys.modules:
        _file_safety_mod = sys.modules[name]
        return _file_safety_mod
    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec_obj = importlib.util.spec_from_file_location(name, path)
        if spec_obj is None or spec_obj.loader is None:
            raise ImportError("cannot load _file_safety.py")
        mod = importlib.util.module_from_spec(spec_obj)
        sys.modules[name] = mod
        spec_obj.loader.exec_module(mod)  # type: ignore[union-attr]
    except BaseException:
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = prev
    required = {
        "UnsafeContentError", "BoundExceeded",
        "read_confined_regular_file", "walk_confined_regular_files",
    }
    missing = required - set(vars(mod))
    if missing:
        sys.modules.pop(name, None)
        raise ImportError(
            f"_file_safety.py missing symbols: {', '.join(sorted(missing))}"
        )
    _file_safety_mod = mod
    return mod


def _get_resolver() -> Any:
    """Load the co-located ``intent_delivery_relations.py`` at most once.

    Calls the resolver's primitives: ``_ARTIFACT_FILE_RE``,
    ``_SPEC_DIR_RE``, ``_SLUG_RE``, ``_PARENT_INTENT_KINDS``,
    ``_preamble_all``, ``_normalize``, ``_is_unsafe_ref``.
    """
    global _resolver_mod
    if _resolver_mod is not None:
        return _resolver_mod
    path = _SCRIPT_DIR / "intent_delivery_relations.py"
    try:
        st = os.lstat(path)
    except OSError as exc:
        raise ImportError(
            "required helper unavailable: intent_delivery_relations.py"
        ) from exc
    if not _stat.S_ISREG(st.st_mode) or _stat.S_ISLNK(st.st_mode):
        raise ImportError(
            "required helper is not a regular file: intent_delivery_relations.py"
        )
    name = "core_navigate_intents_resolver"
    if name in sys.modules:
        _resolver_mod = sys.modules[name]
        return _resolver_mod
    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec_obj = importlib.util.spec_from_file_location(name, path)
        if spec_obj is None or spec_obj.loader is None:
            raise ImportError("cannot load intent_delivery_relations.py")
        mod = importlib.util.module_from_spec(spec_obj)
        sys.modules[name] = mod
        spec_obj.loader.exec_module(mod)  # type: ignore[union-attr]
    except BaseException:
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = prev
    required = {
        "_ARTIFACT_FILE_RE", "_SPEC_DIR_RE", "_SLUG_RE", "_PARENT_INTENT_KINDS",
        "_preamble_all", "_normalize", "_is_unsafe_ref",
    }
    missing = required - set(vars(mod))
    if missing:
        sys.modules.pop(name, None)
        raise ImportError(
            f"intent_delivery_relations.py missing symbols: {', '.join(sorted(missing))}"
        )
    _resolver_mod = mod
    return mod


# ---------------------------------------------------------------------------
# Preamble parser — comment-hiding (for non-brief Parent intent: fields)
# ---------------------------------------------------------------------------


def _visible_line(line: str, inside_comment: bool) -> tuple[str, bool]:
    """Return the visible portion of *line* and the updated comment state.

    Multi-line HTML comment regions (``<!-- ... -->``) are suppressed.
    Each call advances the state machine one line.
    """
    visible: list[str] = []
    remainder = line
    while remainder:
        if inside_comment:
            close = remainder.find("-->")
            if close == -1:
                return "".join(visible), True
            remainder = remainder[close + 3:]
            inside_comment = False
            continue
        open_at = remainder.find("<!--")
        if open_at == -1:
            visible.append(remainder)
            break
        visible.append(remainder[:open_at])
        remainder = remainder[open_at + 4:]
        inside_comment = True
    return "".join(visible), inside_comment


def _preamble_visible(text: str) -> dict[str, list[str]]:
    """Parse the preamble, hiding multi-line HTML comment regions.

    Matches ``intent_shape.read_preamble``: stops at the first ``## ``
    heading, hides comment blocks, keeps every value of each field.
    Uses the resolver's ``_normalize`` for value normalisation.
    """
    normalize = _get_resolver()._normalize
    fields: dict[str, list[str]] = {}
    inside_comment = False
    for line in text.splitlines():
        visible, inside_comment = _visible_line(line, inside_comment)
        if visible.startswith(_HEADING_PREFIX):
            break
        m = _FIELD_LINE_RE.match(visible)
        if m:
            name = m.group(1).strip()
            value = normalize(m.group(2))
            fields.setdefault(name, []).append(value)
    return fields


# ---------------------------------------------------------------------------
# Kind / Level normalisation
# ---------------------------------------------------------------------------


def _normalize_kind_level(raw: str) -> str:
    """Normalise a ``Kind:`` or ``Level:`` value for node-id computation.

    Strips a trailing HTML comment, strips surrounding
    backticks, cuts at `` (`` / `` →`` / ``<!--``, and returns the first
    word lowercased.
    """
    value = raw.strip()
    value = _COMMENT_SUFFIX_RE.sub("", value).strip()
    if len(value) >= 2 and value[0] == "`" and value[-1] == "`":
        value = value[1:-1].strip()
    for sentinel in (" (", " →", "<!--"):
        idx = value.find(sentinel)
        if idx >= 0:
            value = value[:idx]
    parts = value.split()
    return parts[0].lower() if parts else ""


def _compute_node_id(fields: dict[str, list[str]], slug: str) -> str:
    """Compute an intent node id (Kind before Level, preamble only)."""
    kind_vals = fields.get("Kind", [])
    kind_raw = kind_vals[0] if kind_vals else ""
    kind_norm = _normalize_kind_level(kind_raw)

    if kind_norm in ("outcome", "opportunity"):
        return f"{kind_norm}:{slug}"

    level_vals = fields.get("Level", [])
    level_raw = level_vals[0] if level_vals else ""
    level_norm = _normalize_kind_level(level_raw)

    if level_norm == "capability":
        return f"capability:{slug}"

    return f"intent:{slug}"


# ---------------------------------------------------------------------------
# Value form detection
# ---------------------------------------------------------------------------


def _value_form_intent_parent(value: str, resolver: Any) -> str:
    """Classify a value in an intent's ``Parent intent:`` field.

    Returns one of ``typed``, ``path``, ``bare_slug``, ``markdown_link``,
    or ``unrecognized``.  For intent's Parent intent:, only
    ``_PARENT_INTENT_KINDS`` prefixes constitute ``typed`` form.
    """
    for kind in resolver._PARENT_INTENT_KINDS:
        if value.startswith(f"{kind}:"):
            return "typed"
    if _MARKDOWN_LINK_RE.match(value):
        return "markdown_link"
    if resolver._SLUG_RE.fullmatch(value):
        return "bare_slug"
    if "/" in value and not value.startswith("/") and "\\" not in value:
        return "path"
    return "unrecognized"


def _value_form_generic(value: str, resolver: Any) -> str:
    """Classify a value in a spec's ``Brief:`` or ``Discovery:`` field.

    Uses a broader ``typed`` definition: any ``<word>:`` prefix (covers
    ``brief:``, ``intent:``, ``outcome:`` etc.).
    """
    # typed: any <word>:<rest> pattern (not starting with /)
    if not value.startswith("/") and ":" in value:
        prefix = value.split(":")[0]
        if prefix and prefix.replace("-", "").isalnum() and prefix.islower():
            return "typed"
    if _MARKDOWN_LINK_RE.match(value):
        return "markdown_link"
    if resolver._SLUG_RE.fullmatch(value):
        return "bare_slug"
    if "/" in value and not value.startswith("/") and "\\" not in value:
        return "path"
    return "unrecognized"


# ---------------------------------------------------------------------------
# Markdown link target resolution helper
# ---------------------------------------------------------------------------


def _resolve_link_target(link_target: str, spec_rel_dir: str, root: Path) -> str | None:
    """Resolve a markdown link target relative to *spec_rel_dir*.

    Returns the repository-relative path string if the resolved path is
    inside *root*, or ``None`` if it escapes (signalling ``unparseable``).
    Uses string-only path arithmetic to avoid filesystem access.
    """
    if link_target.startswith(("http://", "https://", "//", "#")):
        return None  # escapes
    if link_target.startswith("/"):
        return None  # absolute → escapes
    # Combine the spec dir with the link target component by component
    parts = spec_rel_dir.split("/") + link_target.split("/")
    normalized: list[str] = []
    for part in parts:
        if part == "..":
            if normalized:
                normalized.pop()
            else:
                return None  # escaped above root
        elif part and part != ".":
            normalized.append(part)
    return "/".join(normalized) if normalized else ""


# ---------------------------------------------------------------------------
# File reading (raises DerivationError in integrity-check order)
# ---------------------------------------------------------------------------


def _read_artifact_bytes(root: Path, path: Path, fs: Any) -> bytes:
    """Read raw bytes via the confinement helper, raising on integrity failure."""
    try:
        return fs.read_confined_regular_file(
            root, path, max_bytes=MAX_ARTIFACT_BYTES
        )
    except fs.BoundExceeded as exc:
        rel = path.relative_to(root).as_posix()
        raise DerivationError(
            "input_too_large", f"file exceeds {MAX_ARTIFACT_BYTES} bytes: {rel}"
        ) from exc
    except fs.UnsafeContentError as exc:
        rel = path.relative_to(root).as_posix()
        raise DerivationError("unsafe_input", f"unsafe file: {rel}") from exc


def _decode_utf8(raw: bytes, rel: str) -> str:
    """Decode bytes as UTF-8 or raise ``malformed_record``."""
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise DerivationError("malformed_record", f"not valid UTF-8: {rel}") from exc


# ---------------------------------------------------------------------------
# Intent parent-edge resolution helpers
# ---------------------------------------------------------------------------


def _resolve_intent_typed(
    slug: str,
    expected_kind: str,
    intent_by_slug: dict[str, Any],
    tombstones_by_slug: dict[str, Any],
) -> dict[str, str]:
    """Resolve a typed intent reference ``kind:slug`` for an intent parent."""
    candidate = intent_by_slug.get(slug)
    if candidate is not None:
        if candidate["id"] != f"{expected_kind}:{slug}":
            return {"state": "kind_mismatch"}
        return {"to": candidate["id"]}
    tomb = tombstones_by_slug.get(slug)
    if tomb is not None:
        result: dict[str, str] = {"state": "retired_target"}
        if tomb.get("reissued_as"):
            result["reissued_as"] = tomb["reissued_as"]
        return result
    return {"state": "dangling"}


def _resolve_intent_path(
    rel_path: str,
    intent_by_path: dict[str, Any],
    tombstones_by_path: dict[str, Any],
) -> dict[str, str]:
    """Resolve a path-form intent reference for an intent parent."""
    parts = rel_path.split("/")
    if ".." in parts:
        return {"state": "unparseable"}
    if not rel_path.startswith("docs/product/intents/"):
        if rel_path.startswith(("docs/product/briefs/", "docs/specs/")):
            return {"state": "out_of_type"}
        return {"state": "dangling"}
    candidate = intent_by_path.get(rel_path)
    if candidate is not None:
        return {"to": candidate["id"]}
    tomb = tombstones_by_path.get(rel_path)
    if tomb is not None:
        result: dict[str, str] = {"state": "retired_target"}
        if tomb.get("reissued_as"):
            result["reissued_as"] = tomb["reissued_as"]
        return result
    return {"state": "dangling"}


def _make_intent_parent_edge(
    from_id: str,
    raw_value: str,
    resolver: Any,
    intent_by_slug: dict[str, Any],
    intent_by_path: dict[str, Any],
    tombstones_by_slug: dict[str, Any],
    tombstones_by_path: dict[str, Any],
) -> dict[str, Any]:
    """Build one edge dict for a single intent's ``Parent intent:`` value."""
    form = _value_form_intent_parent(raw_value, resolver)
    base: dict[str, Any] = {
        "from": from_id,
        "field": "Parent intent",
        "form": form,
        "trust_class": _TRUST_CLASS,
        "basis": {"field": "Parent intent", "form": form},
        "value": raw_value,
    }
    if form == "typed":
        for kind in resolver._PARENT_INTENT_KINDS:
            prefix = f"{kind}:"
            if raw_value.startswith(prefix):
                slug = raw_value[len(prefix):]
                if not resolver._SLUG_RE.match(slug):
                    base["state"] = "unparseable"
                    return base
                resolution = _resolve_intent_typed(
                    slug, kind, intent_by_slug, tombstones_by_slug
                )
                base.update(resolution)
                return base
        base["state"] = "unparseable"
        return base
    if form == "bare_slug":
        candidate = intent_by_slug.get(raw_value)
        if candidate is not None:
            base["to"] = candidate["id"]
        else:
            tomb = tombstones_by_slug.get(raw_value)
            if tomb is not None:
                base["state"] = "retired_target"
                if tomb.get("reissued_as"):
                    base["reissued_as"] = tomb["reissued_as"]
            else:
                base["state"] = "dangling"
        return base
    if form == "path":
        resolution = _resolve_intent_path(
            raw_value, intent_by_path, tombstones_by_path
        )
        base.update(resolution)
        return base
    # markdown_link and unrecognized → unparseable
    base["state"] = "unparseable"
    return base


# ---------------------------------------------------------------------------
# Brief parent-edge resolution
# ---------------------------------------------------------------------------


def _make_brief_parent_edges(
    brief_id: str,
    all_parent_values: list[str],
    resolver: Any,
    intent_by_slug: dict[str, Any],
    tombstones_by_slug: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build brief ``Parent intent:`` edges.

    Re-implements the resolver's accept / reject / merge-by-slug loop
    using the resolver's own primitives, so the navigator's derived parent
    equals the relation the resolver would name.
    """
    edges: list[dict[str, Any]] = []
    accepted: list[tuple[str, str]] = []  # (value, slug)
    refused: list[dict[str, Any]] = []

    for pv in all_parent_values:
        if not pv or pv.lower().startswith("none"):
            continue
        # Determine form using generic classifier
        form = _value_form_intent_parent(pv, resolver)
        edge_base: dict[str, Any] = {
            "from": brief_id,
            "field": "Parent intent",
            "form": form,
            "trust_class": _TRUST_CLASS,
            "basis": {"field": "Parent intent", "form": form},
            "value": pv,
        }
        if resolver._is_unsafe_ref(pv):
            edge_base["state"] = "unparseable"
            refused.append(edge_base)
            continue
        # Check for accepted kind prefix
        matched_kind = None
        for kind in resolver._PARENT_INTENT_KINDS:
            if pv.startswith(f"{kind}:"):
                matched_kind = kind
                break
        if matched_kind is None:
            edge_base["state"] = "unparseable"
            refused.append(edge_base)
            continue
        slug = pv[len(matched_kind) + 1:]
        if not resolver._SLUG_RE.match(slug):
            edge_base["state"] = "unparseable"
            refused.append(edge_base)
            continue
        accepted.append((pv, slug))

    # Merge by slug: values of different kinds but same slug count as one
    seen_slugs: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for pv, slug in accepted:
        if slug not in seen_slugs:
            seen_slugs.add(slug)
            deduped.append((pv, slug))

    if len(deduped) > 1:
        edges.append({
            "from": brief_id,
            "field": "Parent intent",
            "state": "multiple_values",
            "trust_class": _TRUST_CLASS,
        })
    elif len(deduped) == 1:
        pv, slug = deduped[0]
        form = _value_form_intent_parent(pv, resolver)
        matched_kind = next(
            (k for k in resolver._PARENT_INTENT_KINDS if pv.startswith(f"{k}:")),
            None,
        )
        edge: dict[str, Any] = {
            "from": brief_id,
            "field": "Parent intent",
            "form": form,
            "trust_class": _TRUST_CLASS,
            "basis": {"field": "Parent intent", "form": form},
            "value": pv,
        }
        # Resolve among live intents (no kind check)
        candidate = intent_by_slug.get(slug)
        if candidate is not None:
            edge["to"] = candidate["id"]
        else:
            tomb = tombstones_by_slug.get(slug)
            if tomb is not None:
                edge["state"] = "retired_target"
                if tomb.get("reissued_as"):
                    edge["reissued_as"] = tomb["reissued_as"]
            else:
                edge["state"] = "dangling"
        edges.append(edge)

    # Add all refused edges (one per malformed/unsafe value)
    edges.extend(refused)
    return edges


# ---------------------------------------------------------------------------
# Spec edge resolution
# ---------------------------------------------------------------------------


def _make_spec_brief_edges(
    spec_id: str,
    brief_values: list[str],
    resolver: Any,
    brief_by_slug: dict[str, Any],
    brief_by_path: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build ``Brief:`` edges for a spec.

    Admitted forms: ``brief:<slug>`` (typed) and a repository-relative path
    under ``docs/product/briefs/``.  A value matching no admitted form is
    refused as ``unparseable``; ``out_of_type`` applies when a typed or path
    reference names an intent or spec.
    """
    edges: list[dict[str, Any]] = []
    seen_values = list(dict.fromkeys(brief_values))  # preserve order, deduplicate

    for bv in seen_values:
        if not bv or bv.lower().split()[0] == "none":
            continue
        form = _value_form_generic(bv, resolver)
        edge: dict[str, Any] = {
            "from": spec_id,
            "field": "Brief",
            "form": form,
            "trust_class": _TRUST_CLASS,
            "basis": {"field": "Brief", "form": form},
            "value": bv,
        }
        if form == "typed":
            if bv.startswith("brief:"):
                slug = bv[len("brief:"):]
                if not resolver._SLUG_RE.match(slug):
                    edge["state"] = "unparseable"
                elif slug in brief_by_slug:
                    edge["to"] = f"brief:{slug}"
                else:
                    edge["state"] = "dangling"
            elif any(bv.startswith(f"{k}:") for k in resolver._PARENT_INTENT_KINDS):
                edge["state"] = "out_of_type"
            else:
                edge["state"] = "unparseable"
        elif form == "path":
            if ".." in bv.split("/"):
                edge["state"] = "unparseable"
            elif bv.startswith("docs/product/briefs/"):
                candidate = brief_by_path.get(bv)
                if candidate is not None:
                    edge["to"] = candidate["id"]
                else:
                    edge["state"] = "dangling"
            elif bv.startswith(("docs/product/intents/", "docs/specs/")):
                edge["state"] = "out_of_type"
            else:
                edge["state"] = "dangling"
        else:
            edge["state"] = "unparseable"
        edges.append(edge)

    if len([e for e in edges if "state" not in e or e.get("state") == "multiple_values"]) > 1:
        # Multiple admitted values → multiple_values
        edges = [{
            "from": spec_id,
            "field": "Brief",
            "state": "multiple_values",
            "trust_class": _TRUST_CLASS,
        }]

    return edges


def _make_spec_discovery_edges(
    spec_id: str,
    spec_path: Path,
    discovery_values: list[str],
    resolver: Any,
    intent_by_slug: dict[str, Any],
    intent_by_path: dict[str, Any],
    tombstones_by_slug: dict[str, Any],
    tombstones_by_path: dict[str, Any],
    root: Path,
) -> list[dict[str, Any]]:
    """Build ``Discovery:`` edges for a spec.

    Admitted forms: typed intent reference, path under
    ``docs/product/intents/``, and markdown link landing on such a path.
    Non-intent-shaped values are provenance (no edge).  A markdown link
    escaping the repo is ``unparseable``.

    Path-form and markdown-link pointers that name a tombstone intent file
    path produce ``retired_target``, not ``dangling``.
    """
    edges: list[dict[str, Any]] = []
    spec_rel_dir = spec_path.parent.relative_to(root).as_posix()

    seen_values = list(dict.fromkeys(discovery_values))

    for dv in seen_values:
        if not dv or dv.lower().split()[0] == "none":
            continue
        form = _value_form_intent_parent(dv, resolver)
        edge_base: dict[str, Any] = {
            "from": spec_id,
            "field": "Discovery",
            "form": form,
            "trust_class": _TRUST_CLASS,
            "basis": {"field": "Discovery", "form": form},
            "value": dv,
        }

        if form == "typed":
            # Must be one of the _PARENT_INTENT_KINDS prefixes
            resolved_slug: str | None = None
            for kind in resolver._PARENT_INTENT_KINDS:
                prefix = f"{kind}:"
                if dv.startswith(prefix):
                    s = dv[len(prefix):]
                    if resolver._SLUG_RE.match(s):
                        resolved_slug = s
                    break
            if resolved_slug is None:
                # bad slug grammar → provenance (no edge)
                continue
            candidate = intent_by_slug.get(resolved_slug)
            if candidate is not None:
                edge_base["to"] = candidate["id"]
            else:
                tomb = tombstones_by_slug.get(resolved_slug)
                if tomb is not None:
                    edge_base["state"] = "retired_target"
                    if tomb.get("reissued_as"):
                        edge_base["reissued_as"] = tomb["reissued_as"]
                else:
                    edge_base["state"] = "dangling"
            edges.append(edge_base)

        elif form == "path":
            if not dv.startswith("docs/product/intents/"):
                # Not an intent path → provenance, no edge
                continue
            parts = dv.split("/")
            if ".." in parts:
                continue  # provenance
            candidate = intent_by_path.get(dv)
            if candidate is not None:
                edge_base["to"] = candidate["id"]
            else:
                tomb = tombstones_by_path.get(dv)
                if tomb is not None:
                    edge_base["state"] = "retired_target"
                    if tomb.get("reissued_as"):
                        edge_base["reissued_as"] = tomb["reissued_as"]
                else:
                    edge_base["state"] = "dangling"
            edges.append(edge_base)

        elif form == "markdown_link":
            m = _MARKDOWN_LINK_RE.match(dv)
            if not m:
                continue
            link_target = m.group(1).strip()
            resolved_rel = _resolve_link_target(link_target, spec_rel_dir, root)
            if resolved_rel is None:
                # Escapes repo → unparseable
                edge_base["state"] = "unparseable"
                edges.append(edge_base)
                continue
            if not resolved_rel.startswith("docs/product/intents/"):
                # Inside repo but not intent path → provenance, no edge
                continue
            candidate = intent_by_path.get(resolved_rel)
            if candidate is not None:
                edge_base["to"] = candidate["id"]
            else:
                tomb = tombstones_by_path.get(resolved_rel)
                if tomb is not None:
                    edge_base["state"] = "retired_target"
                    if tomb.get("reissued_as"):
                        edge_base["reissued_as"] = tomb["reissued_as"]
                else:
                    edge_base["state"] = "dangling"
            edges.append(edge_base)

        else:
            # unrecognized, bare_slug → provenance, no edge
            continue

    return edges


# ---------------------------------------------------------------------------
# Cycle detection
# ---------------------------------------------------------------------------


def _find_refused_cycle_edges(
    resolved_parents: dict[str, str],
    slug_map: dict[str, str],
) -> set[str]:
    """Return node ids whose outgoing parent edge is refused as ``cycle``.

    Within each cycle the refused edge leaves the member
    whose slug sorts first by code point.  A self-parent is a one-member
    cycle.  Uses iterative chain-following; each node has at most one
    outgoing edge.
    """
    refused: set[str] = set()
    visited: set[str] = set()

    for start in list(resolved_parents.keys()):
        if start in visited:
            continue
        path: list[str] = []
        seen_in_path: dict[str, int] = {}
        node: str | None = start

        while node is not None and node not in visited:
            if node in seen_in_path:
                # Cycle: from seen_in_path[node] to end of path
                cycle = path[seen_in_path[node]:]
                lowest = min(cycle, key=lambda n: slug_map.get(n, n))
                refused.add(lowest)
                break
            seen_in_path[node] = len(path)
            path.append(node)
            node = resolved_parents.get(node)

        visited.update(path)

    return refused


# ---------------------------------------------------------------------------
# Directory walk helper
# ---------------------------------------------------------------------------


def _walk_artifact_dir(root: Path, dir_path: Path, fs: Any) -> list[Path]:
    """Walk *dir_path* under *root* via the confinement helper.

    Returns an empty list when the directory is absent.  Raises
    ``DerivationError("unsafe_input", ...)`` for any unsafe entry.
    """
    if not dir_path.exists():
        return []
    try:
        result = fs.walk_confined_regular_files(root, dir_path)
        return result.files
    except (fs.UnsafeContentError, fs.BoundExceeded) as exc:
        rel = dir_path.relative_to(root).as_posix()
        raise DerivationError("unsafe_input", f"unsafe directory: {rel}") from exc


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def derive(root: Path) -> dict[str, Any]:
    """Derive the intent graph from the repository at *root*.

    Returns a dict with two keys:

    ``nodes``
        List of node dicts; one per live intent, brief, and spec.
    ``edges``
        List of edge dicts: resolved edges (carry ``to``) and refused
        edges (carry ``state``).

    Raises :class:`DerivationError` on any integrity failure.
    All file reads go through the co-located ``_file_safety.py``.
    Never reads ``workspace.toml``.
    """
    fs = _get_file_safety()
    resolver = _get_resolver()

    root = root.resolve()
    intents_root = root / "docs" / "product" / "intents"
    briefs_root = root / "docs" / "product" / "briefs"
    specs_root = root / "docs" / "specs"

    # ── Intent index ─────────────────────────────────────────────────────────

    intent_nodes: list[dict[str, Any]] = []
    intent_by_slug: dict[str, dict[str, Any]] = {}
    intent_by_path: dict[str, dict[str, Any]] = {}
    tombstones_by_slug: dict[str, dict[str, Any]] = {}
    tombstones_by_path: dict[str, dict[str, Any]] = {}

    for f in sorted(_walk_artifact_dir(root, intents_root, fs),
                    key=lambda p: p.relative_to(root).as_posix()):
        if f.parent != intents_root or not resolver._ARTIFACT_FILE_RE.fullmatch(f.name):
            continue
        rel = f.relative_to(root).as_posix()
        raw = _read_artifact_bytes(root, f, fs)
        text = _decode_utf8(raw, rel)
        fields = _preamble_visible(text)
        tombstone_vals = fields.get("Tombstone", [])
        slug_vals = fields.get("Slug", [])

        if tombstone_vals:
            # Tombstone: still needs a valid Slug:
            slug = slug_vals[0] if slug_vals else ""
            if not slug:
                raise DerivationError(
                    "malformed_record", f"tombstone missing Slug: in {rel}"
                )
            if not resolver._SLUG_RE.match(slug):
                raise DerivationError(
                    "malformed_record",
                    f"tombstone has invalid Slug: '{slug}' in {rel}",
                )
            reissued_vals = fields.get("Reissued as", [])
            tomb_data: dict[str, Any] = {
                "slug": slug,
                "reissued_as": reissued_vals[0] if reissued_vals else "",
                "rel_path": rel,
            }
            tombstones_by_slug[slug] = tomb_data
            tombstones_by_path[rel] = tomb_data
            continue

        # Live intent: Slug: must be present and valid
        if not slug_vals or not slug_vals[0]:
            raise DerivationError(
                "malformed_record", f"missing Slug: in {rel}"
            )
        slug = slug_vals[0]
        if not resolver._SLUG_RE.match(slug):
            raise DerivationError(
                "malformed_record", f"invalid Slug: '{slug}' in {rel}"
            )

        node_id = _compute_node_id(fields, slug)
        if node_id in {n["id"] for n in intent_nodes}:
            raise DerivationError(
                "duplicate_identity", f"duplicate intent id {node_id}"
            )

        status_vals = fields.get("Status", [])
        level_vals = fields.get("Level", [])
        kind_vals = fields.get("Kind", [])

        node: dict[str, Any] = {
            "id": node_id,
            "type": "intent",
            "slug": slug,
            "path": rel,
            "status": status_vals[0] if status_vals else "",
            "level": level_vals[0] if level_vals else "",
            "kind": kind_vals[0] if kind_vals else "",
            "_fields": fields,  # kept for edge building; stripped from output
        }
        intent_nodes.append(node)
        intent_by_slug[slug] = node
        intent_by_path[rel] = node

    # ── Brief index ───────────────────────────────────────────────────────────

    brief_nodes: list[dict[str, Any]] = []
    brief_by_slug: dict[str, dict[str, Any]] = {}
    brief_by_path: dict[str, dict[str, Any]] = {}

    for f in sorted(_walk_artifact_dir(root, briefs_root, fs),
                    key=lambda p: p.relative_to(root).as_posix()):
        if f.parent != briefs_root or not resolver._ARTIFACT_FILE_RE.fullmatch(f.name):
            continue
        rel = f.relative_to(root).as_posix()
        raw = _read_artifact_bytes(root, f, fs)
        text = _decode_utf8(raw, rel)
        fields = _preamble_visible(text)
        slug_vals = fields.get("Slug", [])

        if not slug_vals or not slug_vals[0]:
            raise DerivationError(
                "malformed_record", f"missing Slug: in {rel}"
            )
        slug = slug_vals[0]
        if not resolver._SLUG_RE.match(slug):
            raise DerivationError(
                "malformed_record", f"invalid Slug: '{slug}' in {rel}"
            )

        brief_id = f"brief:{slug}"
        if brief_id in {n["id"] for n in brief_nodes}:
            raise DerivationError(
                "duplicate_identity", f"duplicate brief id {brief_id}"
            )

        status_vals = fields.get("Status", [])
        node = {
            "id": brief_id,
            "type": "brief",
            "slug": slug,
            "path": rel,
            "status": status_vals[0] if status_vals else "",
            "_text": text,  # kept for resolver's _preamble_all; stripped from output
        }
        brief_nodes.append(node)
        brief_by_slug[slug] = node
        brief_by_path[rel] = node

    # ── Spec index ────────────────────────────────────────────────────────────

    spec_nodes: list[dict[str, Any]] = []
    spec_by_id: dict[str, dict[str, Any]] = {}

    for f in sorted(_walk_artifact_dir(root, specs_root, fs),
                    key=lambda p: p.relative_to(root).as_posix()):
        if f.name != "spec.md" or f.parent.parent != specs_root:
            continue
        dir_name = f.parent.name
        if not resolver._SPEC_DIR_RE.fullmatch(dir_name):
            continue
        rel = f.relative_to(root).as_posix()
        raw = _read_artifact_bytes(root, f, fs)
        text = _decode_utf8(raw, rel)
        fields = _preamble_visible(text)
        spec_id = f"spec:{dir_name}"
        status_vals = fields.get("Status", [])
        node = {
            "id": spec_id,
            "type": "spec",
            "path": rel,
            "status": status_vals[0] if status_vals else "",
            "_fields": fields,
            "_file_path": f,
        }
        spec_nodes.append(node)
        spec_by_id[spec_id] = node

    # ── Edge building ─────────────────────────────────────────────────────────

    edges: list[dict[str, Any]] = []

    # Intent parent edges
    # Collect resolved parents first for cycle detection
    resolved_intent_parents: dict[str, str] = {}  # intent_id -> parent_intent_id
    slug_map: dict[str, str] = {n["id"]: n["slug"] for n in intent_nodes}

    intent_raw_edges: list[dict[str, Any]] = []

    for node in intent_nodes:
        node_id = node["id"]
        fields = node["_fields"]
        parent_vals = fields.get("Parent intent", [])

        if len(parent_vals) > 1:
            # Multiple distinct values → multiple_values
            # But first check if they are all the same (de-duplicate)
            distinct = list(dict.fromkeys(parent_vals))
            if len(distinct) > 1:
                intent_raw_edges.append({
                    "from": node_id,
                    "field": "Parent intent",
                    "state": "multiple_values",
                    "trust_class": _TRUST_CLASS,
                    "_is_cycle_candidate": False,
                })
                continue
            parent_vals = distinct

        if not parent_vals or not parent_vals[0]:
            continue  # no edge
        raw_value = parent_vals[0]
        first_word = raw_value.split()[0].lower() if raw_value.split() else ""
        if first_word == "none":
            continue  # empty or `none` value: no edge

        edge = _make_intent_parent_edge(
            node_id, raw_value, resolver,
            intent_by_slug, intent_by_path,
            tombstones_by_slug, tombstones_by_path,
        )
        edge["_is_cycle_candidate"] = "to" in edge
        if "to" in edge:
            resolved_intent_parents[node_id] = edge["to"]
        intent_raw_edges.append(edge)

    # Cycle detection
    refused_cycle_ids = _find_refused_cycle_edges(
        resolved_intent_parents, slug_map
    )

    for edge in intent_raw_edges:
        if edge.get("_is_cycle_candidate") and edge.get("from") in refused_cycle_ids:
            edge = dict(edge)  # copy
            del edge["_is_cycle_candidate"]
            to_val = edge.pop("to", None)
            _ = to_val
            edge["state"] = "cycle"
        else:
            edge = {k: v for k, v in edge.items() if k != "_is_cycle_candidate"}
        edges.append(edge)

    # Brief parent edges
    for node in brief_nodes:
        brief_id = node["id"]
        text = node["_text"]
        # Use resolver's _preamble_all (reads inside HTML comment regions)
        all_fields = resolver._preamble_all(text)
        parent_vals = all_fields.get("Parent intent", [])
        brief_edges = _make_brief_parent_edges(
            brief_id, parent_vals, resolver, intent_by_slug, tombstones_by_slug
        )
        edges.extend(brief_edges)

    # Spec edges: Brief: and Discovery:
    for node in spec_nodes:
        spec_id = node["id"]
        fields = node["_fields"]
        spec_file_path: Path = node["_file_path"]

        # Brief: field
        brief_vals = fields.get("Brief", [])
        if brief_vals:
            spec_brief_edges = _make_spec_brief_edges(
                spec_id, brief_vals, resolver, brief_by_slug, brief_by_path
            )
            edges.extend(spec_brief_edges)

        # Discovery: field
        disc_vals = fields.get("Discovery", [])
        if disc_vals:
            spec_disc_edges = _make_spec_discovery_edges(
                spec_id, spec_file_path, disc_vals, resolver,
                intent_by_slug, intent_by_path,
                tombstones_by_slug, tombstones_by_path, root,
            )
            edges.extend(spec_disc_edges)

    # ── Strip internal fields from nodes ─────────────────────────────────────

    def _strip_node(n: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in n.items() if not k.startswith("_")}

    all_nodes = (
        [_strip_node(n) for n in intent_nodes]
        + [_strip_node(n) for n in brief_nodes]
        + [_strip_node(n) for n in spec_nodes]
    )

    return {"nodes": all_nodes, "edges": edges}
