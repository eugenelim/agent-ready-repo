#!/usr/bin/env python3
"""Blocker detection for spec-retirement eligibility projection.

T5: detect each blocker the schema enumerates and attach it to the candidates
it holds back.  Functions in this module are pure (no I/O): they take
already-parsed data structures and return detection results.  Every filesystem
read must flow through the confinement helpers in
:mod:`workspace_status_retirement`.

The :data:`BLOCKER_CODES` constant mirrors the schema's ``reason.code`` enum.
T7 pins it to the schema enum so a code added to the schema without a
corresponding fixture entry in T5 fails T7's divergence test rather than being
silently uncovered.

Spec: docs/specs/spec-retirement-eligibility/spec.md  §§ Blocker emission,
      Status vocabulary, Age reporting
Plan: docs/specs/spec-retirement-eligibility/plan.md  § T5
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Canonical sets
# ---------------------------------------------------------------------------

#: The five statuses ``lint-spec-status.py``'s ``CANONICAL_STATUSES`` carries.
#: A test in this suite asserts both sets are equal so they cannot drift silently.
CANONICAL_STATUSES: frozenset[str] = frozenset(
    {"Draft", "Approved", "Implementing", "Shipped", "Archived"}
)

#: Terminal statuses — a spec at one of these has completed its delivery.
TERMINAL_STATUSES: frozenset[str] = frozenset({"Shipped", "Archived"})

#: Blocker codes — mirrors the ``reason.code`` enum in the schema.
#: T7 pins this constant to the schema enum.
BLOCKER_CODES: frozenset[str] = frozenset({
    "evidence-unread",
    "needed-by",
    "inbound-cited",
    "shipped-brief-member",
    "lasting-facts-unsettled",
    "protected",
    "xspec-pinned",
    "inflight",
    "status-not-terminal",
    "recently-changed",
    "history-missing",
    "references-unresolved",
})

# ---------------------------------------------------------------------------
# Status vocabulary
# ---------------------------------------------------------------------------

# Both line formats the corpus carries (T0b enumeration):
#   majority:  - **Status:** X   (list item)
#   16 specs:  **Status:** X     (bare bold line, no list marker)
_STATUS_LIST_RE = re.compile(r"^-\s+\*\*Status:\*\*\s+(.+?)\s*$", re.MULTILINE)
_STATUS_BARE_RE = re.compile(r"^\*\*Status:\*\*\s+(.+?)\s*$", re.MULTILINE)

# Trailing HTML comment, e.g. "Approved <!-- Draft | Approved | ... -->"
_TRAILING_COMMENT_RE = re.compile(r"\s*<!--.*?-->\s*", re.DOTALL)


def parse_spec_status(body: str) -> tuple[str, str] | None:
    """Parse the ``Status:`` line from a spec body.

    Recognises both line formats the corpus carries — list item (the majority)
    and bare bold line (16 specs in T0b's enumeration).

    The raw value is the text after ``**Status:**``, with trailing HTML
    comments stripped (e.g. ``"Approved <!-- Draft | Approved -->"``) The
    leading token is the first whitespace-separated word of the stripped raw
    value, so ``"Shipped (2026-05-26)"`` → ``"Shipped"``.

    Args:
        body: Spec body text.

    Returns:
        ``(leading_token, raw_value)`` pair, or ``None`` when no ``Status:``
        line is found in either recognised format.
    """
    m = _STATUS_LIST_RE.search(body) or _STATUS_BARE_RE.search(body)
    if not m:
        return None
    raw = m.group(1)
    # Strip trailing HTML comment so "Approved <!-- ... -->" → "Approved"
    raw = _TRAILING_COMMENT_RE.sub(" ", raw).strip()
    parts = raw.split()
    token = parts[0] if parts else raw
    return token, raw


# ---------------------------------------------------------------------------
# Cutoff computation
# ---------------------------------------------------------------------------


def compute_cutoff_date(run_date: str, stale_after_days: int) -> str:
    """Compute the age-cutoff calendar date.

    Args:
        run_date:         ISO calendar date, e.g. ``"2026-09-25"``.
        stale_after_days: Non-negative integer days.

    Returns:
        ISO calendar date string for the cutoff date (run_date − stale_after_days).

    Raises:
        ValueError: When ``run_date`` is not a valid calendar date or
                    ``stale_after_days`` is negative.
    """
    if stale_after_days < 0:
        raise ValueError(f"stale_after_days must be non-negative, got {stale_after_days}")
    dt = datetime.date.fromisoformat(run_date)
    return (dt - datetime.timedelta(days=stale_after_days)).isoformat()


# ---------------------------------------------------------------------------
# Collection classification
# ---------------------------------------------------------------------------

#: Known terminal collection suffixes for the ``inflight`` check.
#: A spec in one of these is considered done and is not inflight.
_TERMINAL_COLLECTION_SUFFIXES: frozenset[str] = frozenset({
    "work.shipped",
})

#: Known non-terminal (active / inflight) collection suffixes.
_NONTERMINAL_COLLECTION_SUFFIXES: frozenset[str] = frozenset({
    "work.queue",
    "work.active",
    "backlog.open",
    "backlog.closed",
    "shaping_queue.backlog",
    "shaping_queue.active",
    "brief_queue.draft",
    "brief_queue.ready",
    "brief_queue.executing",
    "brief_queue.shipped",
    "brief_queue.withdrawn",
    "brief_queue.cancelled",
})

_INI_PREFIX_RE = re.compile(r"^ini-\d{3}\.")


def _collection_suffix(collection_name: str) -> str:
    """Strip the initiative prefix from a collection name.

    ``"ini-002.work.active"`` → ``"work.active"``; ``"backlog.open"``
    is returned unchanged since it has no initiative prefix.
    """
    return _INI_PREFIX_RE.sub("", collection_name)


def classify_collection(collection_name: str) -> str:
    """Classify a workspace collection as terminal, non-terminal, or unrecognised.

    Returns:
        ``"terminal"`` — the collection is a known terminal state (a spec
        there is done); ``"non-terminal"`` — a known active/inflight state;
        ``"unrecognised"`` — the name matches no known pattern and a
        ``collection-unrecognised`` refusal must be emitted rather than
        defaulting to either.
    """
    suffix = _collection_suffix(collection_name)
    if suffix in _TERMINAL_COLLECTION_SUFFIXES:
        return "terminal"
    if suffix in _NONTERMINAL_COLLECTION_SUFFIXES:
        return "non-terminal"
    return "unrecognised"


# ---------------------------------------------------------------------------
# needs parsing
# ---------------------------------------------------------------------------

# Bare string pattern: "<room>:<kind>/<slug>"
# All three components contain alphanumerics, hyphens, dots, or underscores.
_NEEDS_BARE_RE = re.compile(
    r"^[A-Za-z0-9._-]+:[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$"
)


def _slug_from_spec_path(path: str) -> str | None:
    """Extract the spec slug from a ``docs/specs/<slug>/...`` path string.

    Returns the slug component, or ``None`` when the path does not name a spec
    (i.e. does not start with ``docs/specs/`` or has an empty slug).

    The bare-directory shape ``docs/specs/<slug>`` occurs zero times in the
    corpus (T0b enumeration), so this function requires at least one component
    after the slug (``len(parts) >= 4``).
    """
    parts = path.split("/")
    if len(parts) >= 4 and parts[0] == "docs" and parts[1] == "specs":
        slug = parts[2]
        return slug if slug else None
    return None


def parse_needs_edges(
    needs_raw: object,
) -> list[tuple[str, str]] | None:
    """Parse a ``needs`` value into ``(target_slug, edge_repr)`` pairs.

    Recognises all four shapes enumerated in T0b:
    - ``list`` of ``dict`` tables — each table may name a spec via ``path``.
    - bare ``<room>:<kind>/<slug>`` string — names a spec when ``kind == "spec"``.
    - empty ``list`` — no dependencies (none refused).
    - ``None`` (key absent) — no dependencies (none refused).

    A table whose ``path`` points outside ``docs/specs/`` yields no edge and is
    not refused: it names a non-spec artifact and this run ignores it.

    Args:
        needs_raw: The raw value from the ``needs`` field, or ``None`` when
                   the key is absent.

    Returns:
        List of ``(target_slug, edge_repr)`` pairs on success, or ``None``
        when the shape is unrecognised (signals ``needs-shape-unrecognised``).
    """
    # Key absent → no edges, no refusal
    if needs_raw is None:
        return []

    # List shape (empty list or list of tables)
    if isinstance(needs_raw, list):
        if not needs_raw:
            return []  # empty list → no edges, no refusal
        edges: list[tuple[str, str]] = []
        for item in needs_raw:
            if not isinstance(item, dict):
                # List element is not a table — unrecognised shape
                return None
            path = item.get("path", "")
            if not isinstance(path, str):
                return None
            slug = _slug_from_spec_path(path)
            if slug:
                edges.append((slug, path))
            # else: points outside docs/specs/ → no edge, not refused
        return edges

    # Bare string shape: "<room>:<kind>/<slug>"
    if isinstance(needs_raw, str):
        if not _NEEDS_BARE_RE.match(needs_raw):
            return None  # string shape does not match — unrecognised
        colon = needs_raw.index(":")
        rest = needs_raw[colon + 1:]
        slash = rest.index("/")
        kind = rest[:slash]
        slug = rest[slash + 1:]
        if kind == "spec" and slug:
            return [(slug, needs_raw)]
        return []  # non-spec kind → no spec edge, not refused

    return None  # any other type (int, bool, …) → unrecognised


# ---------------------------------------------------------------------------
# Blocker detectors — pure functions (no I/O)
# ---------------------------------------------------------------------------


def detect_status_not_terminal(status_token: str) -> bool:
    """Return ``True`` when the status token is a non-terminal canonical status.

    The caller must have already verified ``status_token`` is in
    :data:`CANONICAL_STATUSES`; unrecognised tokens are refused before this is
    called, not passed here.
    """
    return status_token not in TERMINAL_STATUSES


def detect_protected(slug: str, protected_slugs: frozenset[str]) -> bool:
    """Return ``True`` when the slug is named in the protected manifest."""
    return slug in protected_slugs


def detect_xspec_pinned(slug: str, xspec_slugs: frozenset[str]) -> bool:
    """Return ``True`` when the slug is named by an ``x-spec`` key in any contract."""
    return slug in xspec_slugs


def detect_recently_changed(last_touched: str, cutoff_date: str) -> bool:
    """Return ``True`` when the spec was changed at or after the cutoff.

    A spec changed *on* the cutoff date is still considered recently changed.
    Both arguments must be ISO calendar date strings (``YYYY-MM-DD``).
    """
    return last_touched >= cutoff_date


def detect_history_missing(last_touched: str | None) -> bool:
    """Return ``True`` when the last-touched date could not be determined."""
    return last_touched is None


# ---------------------------------------------------------------------------
# needed-by detection
# ---------------------------------------------------------------------------


def build_needed_by_index(
    workspace_data: dict,
) -> tuple[dict[str, list[str]], list[str]]:
    """Walk workspace.toml data and build a slug → [declaring entry descs] map.

    Entries without a ``path`` key, or whose ``path`` does not name a
    ``docs/specs/<slug>/spec.md``, are skipped without a refusal (per the AC
    "an entry carrying no path key holds no spec and is skipped").

    An unrecognised ``needs`` shape for an otherwise valid entry returns a
    ``needs-shape-unrecognised`` sentinel string in the declaring list
    so the caller can emit the appropriate refusal.

    Args:
        workspace_data: Parsed workspace.toml dict.

    Returns:
        ``(needed_by_map, refusal_sources)`` where:
        - ``needed_by_map[target_slug]`` is a list of human-readable
          declaring-entry descriptions (one per dependency edge).
        - ``refusal_sources`` is a list of strings naming the entries whose
          ``needs`` value was unrecognised (for ``needs-shape-unrecognised``).
    """
    from collections import defaultdict

    needed_by: dict[str, list[str]] = defaultdict(list)
    refusal_sources: list[str] = []

    def _walk(node: object, trail: list[str]) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                _walk(v, trail + [k])
        elif isinstance(node, list):
            for item in node:
                if not isinstance(item, dict):
                    continue
                path = item.get("path")
                if not isinstance(path, str):
                    continue
                slug = _slug_from_spec_path(path)
                if slug is None:
                    continue  # path doesn't name a spec
                collection = ".".join(trail[-2:]) if len(trail) >= 2 else ""
                entry_desc = f"{collection}:{path}" if collection else path

                needs_raw = item.get("needs")  # None when key is absent
                edges = parse_needs_edges(needs_raw)
                if edges is None:
                    # Unrecognised needs shape on this entry
                    refusal_sources.append(entry_desc)
                    continue
                for target_slug, edge_repr in edges:
                    # Only record edges to docs/specs/ paths
                    needed_by[target_slug].append(
                        f"{entry_desc} needs {edge_repr}"
                    )

    _walk(workspace_data, [])
    return dict(needed_by), refusal_sources


def detect_needed_by(
    slug: str,
    needed_by_map: dict[str, list[str]],
) -> list[str]:
    """Return the declaring-entry descriptions for the needed-by blocker.

    Returns an empty list when the slug has no inbound ``needs`` edges.
    """
    return list(needed_by_map.get(slug, []))


# ---------------------------------------------------------------------------
# inflight detection
# ---------------------------------------------------------------------------


def build_inflight_index(
    workspace_data: dict,
) -> tuple[dict[str, list[str]], list[str]]:
    """Walk workspace.toml data and build a slug → [collections] map.

    Returns ``(inflight_map, unrecognised_collections)`` where:
    - ``inflight_map[slug]`` is a list of collection names holding that spec.
    - ``unrecognised_collections`` names collections the run cannot classify.
    """
    from collections import defaultdict

    slug_collections: dict[str, list[str]] = defaultdict(list)
    unrecognised: list[str] = []

    def _walk(node: object, trail: list[str]) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                _walk(v, trail + [k])
        elif isinstance(node, list):
            for item in node:
                if not isinstance(item, dict):
                    continue
                path = item.get("path")
                if not isinstance(path, str):
                    continue
                # Only consider entries whose path names a spec's spec.md
                if not path.endswith("/spec.md"):
                    continue
                slug = _slug_from_spec_path(path)
                if slug is None:
                    continue
                collection = ".".join(trail[-2:]) if len(trail) >= 2 else ""
                if not collection:
                    continue
                kind = classify_collection(collection)
                if kind == "unrecognised":
                    if collection not in unrecognised:
                        unrecognised.append(collection)
                else:
                    slug_collections[slug].append(collection)

    _walk(workspace_data, [])
    return dict(slug_collections), unrecognised


def detect_inflight(
    slug: str,
    slug_collections: dict[str, list[str]],
) -> bool:
    """Return ``True`` when any collection holding this slug is non-terminal."""
    collections = slug_collections.get(slug, [])
    return any(classify_collection(c) == "non-terminal" for c in collections)


# ---------------------------------------------------------------------------
# inbound-cited detection
# ---------------------------------------------------------------------------

#: Surfaces the inbound-cited scan reaches.
#: See RFC-0096 Wave 7d carve-out (docs/rfc/0096-...:513-522).
INBOUND_CITED_SURFACES: list[str] = [
    "workspace.toml",
    "tools/",
    "packages/",
    "packs/",
    "docs/knowledge/",
    "docs/adr/",
    "docs/rfc/",
    "docs/product/",
    "guides/",
    "docs-site/",
    "docs/specs/",  # other specs
]

#: Forms the inbound-cited scan matches.
INBOUND_FORMS_RECOGNISED: list[str] = [
    "docs/specs/<slug>",
    "docs/specs/<slug>/",
    "docs/specs/<slug>#fragment",
]

#: Forms the scan does not reach.
INBOUND_FORMS_NOT_REACHED: list[str] = [
    "constructed/indirect references",
    "alias-based references",
    "unsearched-file references",
]


def _inbound_surface_label(rel_path: str, slug: str) -> str:
    """Return a human-readable surface label for a citing file."""
    if rel_path == "workspace.toml":
        return "workspace.toml"
    for prefix in ("docs/adr/", "docs/rfc/"):
        if rel_path.startswith(prefix):
            return prefix.rstrip("/")
    if rel_path.startswith("docs/product/"):
        return "docs/product"
    if rel_path.startswith("docs/knowledge/"):
        return "docs/knowledge"
    if rel_path.startswith("docs/specs/"):
        # Other spec citing this one
        return f"docs/specs (from {rel_path.split('/')[2]})"
    for prefix in ("tools/", "packages/", "packs/", "guides/", "docs-site/"):
        if rel_path.startswith(prefix):
            return prefix.rstrip("/")
    return rel_path


def _file_cites_slug(text: str, slug: str) -> bool:
    """Return ``True`` when ``text`` contains a literal reference to ``docs/specs/<slug>``.

    A spec whose slug is a strict prefix of another spec's slug is not cited
    by the longer slug's citations alone: the pattern anchors on a word
    boundary after the slug to avoid prefix confusion.
    """
    # Match docs/specs/<slug> followed by end-of-string, /, #, or a non-word char
    pattern = re.compile(
        r"docs/specs/" + re.escape(slug) + r"(?:/|#|(?![A-Za-z0-9._-]))"
    )
    return bool(pattern.search(text))


def detect_inbound_cited(
    slug: str,
    scanned_files: list[tuple[str, str]],  # (rel_path, content)
) -> list[str]:
    """Return a list of surface labels that cite this spec.

    Args:
        slug:          The spec slug to search for.
        scanned_files: List of ``(repository_relative_path, file_content)``
                       pairs to scan.  Self-references (files inside the spec's
                       own directory) are excluded.

    Returns:
        List of surface label strings (one per citing surface group); empty
        when the spec carries no inbound citation.
    """
    self_prefix = f"docs/specs/{slug}/"
    surface_labels: set[str] = set()
    for rel_path, content in scanned_files:
        if rel_path.startswith(self_prefix):
            continue  # self-reference
        if _file_cites_slug(content, slug):
            surface_labels.add(_inbound_surface_label(rel_path, slug))
    return sorted(surface_labels)


# ---------------------------------------------------------------------------
# shipped-brief-member detection
# ---------------------------------------------------------------------------

# The Spec map section heading and its table rows
_SPEC_MAP_SECTION_RE = re.compile(r"##\s+Spec\s+map", re.IGNORECASE)
_TABLE_ROW_RE = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|", re.MULTILINE)


def _parse_brief_spec_map(body: str) -> list[str]:
    """Return a list of spec slugs named in the brief's Spec map table.

    The Spec map is a markdown table under a ``## Spec map`` heading.  Each
    row's first column is the spec slug (or link to it).  The header and
    separator rows are skipped.
    """
    m = _SPEC_MAP_SECTION_RE.search(body)
    if not m:
        return []
    # Take only the text after the heading
    section = body[m.end():]
    # Cut at the next section heading
    next_heading = re.search(r"^##\s+", section, re.MULTILINE)
    if next_heading:
        section = section[: next_heading.start()]

    slugs: list[str] = []
    for row_m in _TABLE_ROW_RE.finditer(section):
        cell = row_m.group(1).strip()
        # Skip header/separator rows
        if set(cell.replace("-", "").replace(" ", "")) <= set("-| "):
            continue
        if cell.lower() == "spec":
            continue  # header row
        # Extract slug from plain text or markdown link: [slug](path) or slug
        link_m = re.match(r"\[(.+?)\]\(", cell)
        slug = link_m.group(1) if link_m else cell
        slug = slug.strip()
        if slug and slug not in ("-", "---"):
            slugs.append(slug)
    return slugs


def detect_shipped_brief_member(
    slug: str,
    shipped_brief_entries: list[tuple[str, str]],  # (brief_rel_path, brief_body)
) -> list[str]:
    """Return a list of brief paths whose Spec map names this slug.

    Args:
        slug:                  The spec slug to check.
        shipped_brief_entries: List of ``(rel_path, body)`` pairs for briefs
                               whose own status is ``Shipped``.

    Returns:
        List of relative paths of shipped briefs that name this slug.
    """
    citing_briefs: list[str] = []
    for rel_path, body in shipped_brief_entries:
        if slug in _parse_brief_spec_map(body):
            citing_briefs.append(rel_path)
    return citing_briefs


# ---------------------------------------------------------------------------
# lasting-facts-unsettled detection and obligation payload
# ---------------------------------------------------------------------------

#: The ten semantic roles RFC-0096 §2's "Other roles are separate" sentence
#: names.  Enumerated from the schema's ``$defs/obligation.semantic_role``
#: enum.  T6 pins this constant to the schema enum so they cannot drift.
SEMANTIC_ROLE_ENUM: frozenset[str] = frozenset({
    "current-product-truth",
    "user-documentation",
    "product-history",
    "release-history",
    "current-architecture",
    "architecture-design",
    "decision-record",
    "operations",
    "interface-contract",
    "project-knowledge",
})

# Pattern-based role classification for notes files.
#
# Where RFC-0096 §4's precedence order resolves the role to a known
# destination in this repository, the destination is returned; where it does
# not, ``None`` is returned so the caller omits the field — emitting a
# guessed path would present an unmade decision as a made one.
#
# §4 resolves ``project-knowledge`` to ``docs/knowledge/`` in this repository
# per ADR-0081's per-topic model (RFC-0096 §4 and the 2026-09-13 Errata).
# §4 resolves ``current-architecture`` to ``docs/architecture/`` per the
# established in-repository convention for architecture documents.
# Other roles have no single resolved destination in this repository: a
# destination for them requires a human decision.
#
# Patterns are checked in order; the first match wins.
_NOTES_ROLE_PATTERNS: list[tuple[re.Pattern[str], str, str | None]] = [
    (re.compile(r"survey|knowledge|learning|ledger", re.IGNORECASE),
     "project-knowledge", "docs/knowledge/"),
    (re.compile(r"arch", re.IGNORECASE),
     "current-architecture", "docs/architecture/"),
    (re.compile(r"policy|invariant|truth|product", re.IGNORECASE),
     "current-product-truth", None),
    (re.compile(r"decision|rationale|findings|adr", re.IGNORECASE),
     "decision-record", None),
    (re.compile(r"operations|runbook|ops", re.IGNORECASE),
     "operations", None),
    (re.compile(r"user.doc|user.manual|guide", re.IGNORECASE),
     "user-documentation", None),
    (re.compile(r"release|changelog", re.IGNORECASE),
     "release-history", None),
    (re.compile(r"history", re.IGNORECASE),
     "product-history", None),
    (re.compile(r"interface|contract|schema", re.IGNORECASE),
     "interface-contract", None),
]

#: Default role for notes files matching no named pattern.
#: ``project-knowledge`` is the most common role for delivery notes; its
#: destination resolves per ADR-0081.
_NOTES_DEFAULT_ROLE: str = "project-knowledge"
_NOTES_DEFAULT_DESTINATION: str | None = "docs/knowledge/"


def classify_notes_obligation(notes_path: str) -> tuple[str, str | None]:
    """Classify a notes file into a semantic role and optional destination.

    The classification is **advisory**: the mechanical trigger for
    ``lasting-facts-unsettled`` is the uncited notes file, not this judgement.
    The role names the RFC-0096 §2 surface that should receive the content.

    Where §4's precedence order resolves the role to a location in this
    repository, the destination is returned.  Where it does not, ``None`` is
    returned and the caller omits the ``destination`` field from the emitted
    obligation — emitting a guessed path would present an unmade decision as
    a made one.

    Args:
        notes_path: Repository-relative path to the notes file
                    (e.g. ``"docs/specs/foo/notes/bar.md"``).

    Returns:
        ``(semantic_role, destination | None)`` pair where ``semantic_role``
        is one of the ten roles in :data:`SEMANTIC_ROLE_ENUM`.
    """
    filename = Path(notes_path).name
    for pattern, role, destination in _NOTES_ROLE_PATTERNS:
        if pattern.search(filename):
            return role, destination
    return _NOTES_DEFAULT_ROLE, _NOTES_DEFAULT_DESTINATION


def _uncited_notes_files(
    notes_files: list[str],
    scanned_files: list[tuple[str, str]],
    spec_slug: str,
) -> list[str]:
    """Return the notes files not cited from outside the spec directory.

    A notes file is considered cited when at least one file outside the
    spec's own directory (``docs/specs/<spec_slug>/``) contains the notes
    file's repository-relative path as a literal string.

    Args:
        notes_files:   Relative paths of files under the spec's ``notes/``
                       directory.
        scanned_files: Corpus of ``(rel_path, content)`` pairs to scan.
        spec_slug:     The spec slug (used to exclude self-references).

    Returns:
        List of notes file paths with no external citation.
    """
    self_prefix = f"docs/specs/{spec_slug}/"
    uncited: list[str] = []
    for notes_path in notes_files:
        cited = False
        for rel_path, content in scanned_files:
            if rel_path.startswith(self_prefix):
                continue  # self-reference excluded
            if notes_path in content:
                cited = True
                break
        if not cited:
            uncited.append(notes_path)
    return uncited


def detect_lasting_facts_unsettled(
    notes_files: list[str],  # rel paths of notes files in the spec directory
    scanned_files: list[tuple[str, str]],  # (rel_path, content) of corpus files
    spec_slug: str,
) -> bool:
    """Return ``True`` when any notes file is not cited from outside the spec directory.

    A spec carrying a ``notes/`` file that no surface outside its own directory
    cites is considered to have lasting facts unsettled.

    Args:
        notes_files:   Relative paths of files under the spec's ``notes/``
                       directory (e.g. ``"docs/specs/foo/notes/bar.md"``).
        scanned_files: Corpus of ``(rel_path, content)`` pairs to scan.
        spec_slug:     The spec slug (used to exclude self-references).

    Returns:
        ``True`` when at least one notes file is uncited from outside the
        spec's own directory.
    """
    return bool(_uncited_notes_files(notes_files, scanned_files, spec_slug))


def build_lasting_facts_obligations(
    notes_files: list[str],
    scanned_files: list[tuple[str, str]],
    spec_slug: str,
) -> list[dict]:
    """Build obligation objects for notes files not cited from outside the spec.

    For each uncited notes file, creates an obligation dict naming the
    RFC-0096 §2 semantic role and, where §4's precedence order resolves one
    in this repository, the destination.

    The obligation payload is the **advisory** part of
    ``lasting-facts-unsettled``: the mechanical proxy that fires the blocker
    is the uncited notes file; the role is advisory classification, not the
    trigger.

    Args:
        notes_files:   Relative paths of files under the spec's ``notes/``
                       directory.
        scanned_files: Corpus of ``(rel_path, content)`` pairs to scan.
        spec_slug:     The spec slug (used to exclude self-references).

    Returns:
        List of obligation dicts, one per uncited notes file.  Each dict
        carries ``semantic_role`` (one of the ten RFC-0096 §2 roles) and
        ``source_path`` (the notes file path), plus ``destination`` when §4
        resolves one.
    """
    uncited = _uncited_notes_files(notes_files, scanned_files, spec_slug)
    obligations: list[dict] = []
    for notes_path in uncited:
        role, destination = classify_notes_obligation(notes_path)
        obligation: dict[str, str] = {
            "semantic_role": role,
            "source_path": notes_path,
        }
        if destination is not None:
            obligation["destination"] = destination
        obligations.append(obligation)
    return obligations


# ---------------------------------------------------------------------------
# references-unresolved detection
# ---------------------------------------------------------------------------

# Markdown link pattern targeting non-URL, non-anchor paths
_MD_LINK_RE = re.compile(r"\[(?:[^\[\]]*)\]\(([^)#\s]+)(?:[#][^)]*)?\)")


def _extract_named_paths(spec_body: str) -> list[str]:
    """Extract repository-relative paths named by markdown links in a spec body.

    Returns paths that look like repository-relative paths (not HTTP/HTTPS
    URLs, not bare anchors, not empty strings).
    """
    paths: list[str] = []
    for m in _MD_LINK_RE.finditer(spec_body):
        target = m.group(1)
        if not target:
            continue
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("#"):
            continue
        # Normalise: strip leading "./" or "/"
        if target.startswith("/"):
            continue  # absolute path → skip (would always be "unresolvable" in a relative check)
        # Only consider docs/specs/ paths (to match the criterion's scope)
        if target.startswith(("docs/", "../")):
            paths.append(target)
    return paths


def detect_references_unresolved(
    slug: str,
    spec_body: str,
    existing_rel_paths: frozenset[str],
) -> list[str]:
    """Return a list of named paths that do not resolve in the repository.

    A spec is reported ``references-unresolved`` when it names a path that does
    not exist.  Only ``docs/`` paths and ``../``-relative paths are checked to
    keep the scope bounded.

    Args:
        slug:               The spec slug (for context, not used in detection).
        spec_body:          The spec body text.
        existing_rel_paths: Set of repository-relative paths known to exist.

    Returns:
        List of unresolved path strings named in the spec body.
    """
    unresolved: list[str] = []
    spec_dir = f"docs/specs/{slug}"
    for raw_path in _extract_named_paths(spec_body):
        # Resolve ../ relative to the spec directory
        if raw_path.startswith("../"):
            # Resolve relative to docs/specs/<slug>/
            parts = (spec_dir + "/" + raw_path).split("/")
            resolved_parts: list[str] = []
            for part in parts:
                if part == "..":
                    if resolved_parts:
                        resolved_parts.pop()
                elif part != ".":
                    resolved_parts.append(part)
            resolved = "/".join(resolved_parts)
        else:
            resolved = raw_path

        # Check if the resolved path (or a spec.md inside it) exists
        if (
            resolved not in existing_rel_paths
            and resolved + "/spec.md" not in existing_rel_paths
        ):
            unresolved.append(raw_path)
    return unresolved


# ---------------------------------------------------------------------------
# x-spec slug extraction (for building xspec_slugs index)
# ---------------------------------------------------------------------------


def extract_xspec_slugs(schema_data: dict) -> frozenset[str]:
    """Walk a parsed JSON schema and extract all slugs named by ``x-spec`` keys.

    The ``x-spec`` value may be a string or a list of strings.  Each string
    is expected to be a ``docs/specs/<slug>/`` path or ``docs/specs/<slug>``
    path; the slug is the third ``/``-separated component.

    Args:
        schema_data: Parsed JSON schema dict.

    Returns:
        Frozenset of spec slug strings.
    """
    slugs: set[str] = set()

    def _walk(node: object) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "x-spec":
                    for s in ([v] if isinstance(v, str) else (v if isinstance(v, list) else [])):
                        if isinstance(s, str):
                            # Normalise: strip leading/trailing slashes
                            s = s.strip("/")
                            parts = s.split("/")
                            if len(parts) >= 3 and parts[:2] == ["docs", "specs"]:
                                slug = parts[2]
                                if slug:
                                    slugs.add(slug)
                else:
                    _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(schema_data)
    return frozenset(slugs)


# ---------------------------------------------------------------------------
# Protected slug extraction (from the manifest)
# ---------------------------------------------------------------------------


def extract_protected_slugs(manifest_data: dict) -> frozenset[str]:
    """Extract protected spec slugs from the parsed protected manifest dict.

    The manifest contains a ``protected`` list of ``docs/specs/<slug>``
    directory paths.  The slug is the last path component.

    Args:
        manifest_data: Parsed ``.workspace-prune-protected.toml`` dict.

    Returns:
        Frozenset of spec slug strings.
    """
    protected = manifest_data.get("protected", [])
    if not isinstance(protected, list):
        return frozenset()
    slugs: set[str] = set()
    for entry in protected:
        if isinstance(entry, str):
            parts = entry.strip("/").split("/")
            if parts:
                slugs.add(parts[-1])
    return frozenset(slugs)
