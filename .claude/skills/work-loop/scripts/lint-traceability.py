#!/usr/bin/env python3
"""Structural-orphan traceability lint.

This is a `work-loop` **skill script**: it lives at
`packs/core/.apm/skills/work-loop/scripts/lint-traceability.py` and projects to
every adapter's `.../skills/work-loop/scripts/`, the same way the sibling
`lint-spec-status.py` does. The agent runs it at the finish-time checklist; it
can also run as a fail-closed **CI gate** where a PR event and Python both
exist. It no-ops gracefully where Python is absent.

What it does — it generalizes `author-delivery-brief continue`'s
`lint-brief-coverage.py` (which
checks the single brief↔spec edge in one repo) to the full nine-layer product
chain **across repositories**:

    outcome → opportunity → capability → screen → action → service
            → contract → spec → component

It flags every **structural orphan** — a node that exists but asserts no
producer above it (a *backward* orphan, the scope-creep / unjustified-artifact
signal) or has no consumer below it (a *forward* orphan, the uncovered-intent
signal). The terminus is `component`, not `code`: `code` is the component's
content, not a separate node.

**Structure only.** Whether a node is parented to the *right* outcome (semantic
scope-creep) is never this lint's call — structural presence is mechanizable,
semantic correctness is not (the established traceability split — semantic
scope-creep is a human call at G1.5, never this lint's).

**The chain spans repos, because the loops do.** `work-loop` builds per module
(one repo, or one `packages/<c>/`); `discovery-loop` and the release loop work
within or across modules, so the upstream discovery artifacts and shared
contracts commonly live in a discovery / value-stream meta-repo. A
single working tree therefore sees only part of the chain. The crossing is
handled by **convention, not path**: every node carries a stable,
location-independent id (a marker slug, a `contract@version`, a Backstage
`kind:namespace/name`) and every cross-repo edge endpoint resolves to one of
three states — **local** (in this root), **satisfied-by-reference** (a
well-formed pointer resolving via a value-stream rollup / sidecar, pinned or
unpinned), or **unresolvable** (reported `unknown / not-yet-catalogued`, the
open-world federated-catalog posture — never fatal, never silently satisfied).

Two sources, one classifier:
  - When a recognized sidecar `traceability.json` (a `schema_version`-stamped
    `_state/` instance) is present it supplies the authoritative
    edge set. The schema *definition* is carried in `product-engineering`'s
    `discovery-loop` skill — this lint reads the produced instance by
    convention + the stamp, it never imports the definition.
  - When absent, the edge set is **derived from the local artifacts** (the
    standalone mode) via the declarative registry below.
  A matrix↔artifact disagreement is reported as **drift, warn-only** until the
  sidecar schema is pinned (deferred: sidecar-drift-hard-fail).

On the authoritative sidecar graph the lint also runs a **root→leaf reachability**
pass (`reachability_sidecar`): a node is reachable iff it is forward-reachable from
`root` AND can reach a clean terminus (a `leaf_kind` node or a rollup-resolved
`satisfied-by-reference` endpoint). A node off every root→leaf path is `UNREACHABLE`
(the disconnected-subtree finding the discovery-loop cascade backstop depends
on) — additive to, and non-overlapping with, the presence orphans. An
*unresolvable* cross-repo hop is **not** a clean terminus (the sidecar is untrusted
input — a forged out-edge must not silently green a stranded subtree); a node whose
only escape is such a hop is surfaced informationally, never fatal. Reachability is
sidecar-only — a standalone derived graph is legitimately partial / multi-root.

Exit codes:
  0 = clean / reported. Structural orphans and `UNREACHABLE` findings are
      informational in default mode; unresolvable cross-repo endpoints, the
      `reaches a leaf only via an unresolved cross-repo reference` finding,
      unpinned references, and drift are never fatal.
  1 = a hard violation — a dangling edge (a pointer to a missing local target,
      or malformed) or a cycle, **in every mode**; or, under `--strict`, any
      structural orphan or `UNREACHABLE` node (the convergence-/CI-gate enforcing
      "traceability closed"). `--strict` degrades gracefully where the
      producer `Discovery:` headers / `type:` markers are absent (a separate
      follow-on in the owning artifact lands those).

No chain artifacts at all → exit 0 with no diagnostic (the
`lint-brief-coverage.py` no-brief precedent).

Usage: lint-traceability.py [--root DIR] [--strict]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

try:  # py311+ stdlib; degrade where a layout config exists but tomllib doesn't.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - py<3.11
    tomllib = None  # type: ignore[assignment]

# The canonical nine-node chain, in order. Index = layer
# depth; used for adjacency, terminal exemption, and the globally-unpopulated
# layer-skip. `outcome` is the root (never a backward orphan); `component` is
# the leaf (never a forward orphan — its cross-repo consumer is the release
# loop).
# Every per-item report line is indented with this prefix; every summary line
# starts with `lint-traceability:`. `main` withholds the former on a passing
# non-verbose run, so a new detail line MUST keep this prefix to stay
# suppressible. `test_every_detail_line_carries_the_detail_prefix` pins that.
_DETAIL_PREFIX = "  - "

CHAIN = (
    "outcome", "opportunity", "capability", "screen", "action",
    "service", "contract", "spec", "component",
)
ROOT_LAYER = CHAIN[0]
LEAF_LAYER = CHAIN[-1]
# The discovery-side layers — populating any one anchors the chain check (see
# `check()`). `contract`, `spec`, `component` are deliberately excluded: they
# exist as ordinary governance artifacts in repos that don't run the model.
_DISCOVERY_LAYERS = frozenset({
    "outcome", "opportunity", "capability", "screen", "action", "service",
})

# Sidecar `schema_version` values this lint understands. An instance carrying an
# unrecognized version is reported and skipped (warn, never hard-fail) — the
# derive-from-artifacts standalone path still runs.
KNOWN_SCHEMA_VERSIONS = frozenset({"0.1"})

# --- path-defaults:start ---------------------------------------------------
# The ONLY home for literal artifact-path segments. Every base location is
# resolved through `resolve_base()` (config → these defaults → discover by
# marker); no discovery logic elsewhere may name a path literal (the no-
# hardcoded-path NFR; the self-test greps this block's exclusivity).
# Each layer: realization, default base (path segments under the root), and the
# layout-config key (`agentbundle-layout.toml`, tier 1).
#
# realization ∈ {file, container, ladder} — mirrors the sidecar's `backed_by`.
_DEFAULT_BASES = {
    "outcome":     ("docs", "product", "intents"),
    "opportunity": ("docs", "product", "intents"),
    "capability":  ("docs", "product", "intents"),
    "screen":      ("docs", "product", "screens"),
    "action":      ("docs", "product", "journeys"),
    "service":     ("docs", "product", "blueprints"),
    "contract":    ("docs", "contracts"),
    "spec":        ("docs", "specs"),
    "component":   ("packages",),
}
# Discovery-side anchor artifacts (not chain layers themselves): a brief stands
# in for a spec's discovery parent (the `author-delivery-brief continue`
# brief↔spec edge this
# generalizes); a sidecar materializes the whole edge set; a rollup carries the
# cross-repo component rows. Presence of ANY anchor (or a populated chain layer)
# is what activates the chain check — absent all, the lint no-ops.
_BRIEFS_BASE = ("docs", "product", "briefs")
_ROLLUPS_BASE = ("docs", "product", "rollups")
_SIDECAR_DEFAULT_BASE = ("docs", "discovery")
_SIDECAR_RELPATH = ("_state", "traceability.json")
# --- path-defaults:end -----------------------------------------------------

# ---------------------------------------------------------------------------
# Delivery resolver — subprocess invocation constants and injectable seam
# ---------------------------------------------------------------------------

# Script directory — used to locate the sibling resolver copy.
_SCRIPT_DIR: Path = Path(__file__).resolve().parent

# Resolver copy shipped beside this file; never derived from the analysed root.
# Tests may pass a different path via _run_resolver's _resolver_path keyword.
_RESOLVER_PATH: Path = _SCRIPT_DIR / "intent_delivery_relations.py"

# Wall-clock budget for the resolver subprocess (seconds).
_RESOLVER_TIMEOUT: int = 60
# Maximum stdout accepted from the resolver (16 MiB, mirrors resolver limit).
_MAX_SNAPSHOT_BYTES: int = 16_777_216
# The one delivery-snapshot schema version this lint consumes.
_SNAPSHOT_SCHEMA_VERSION: int = 1
# Required top-level keys in a valid snapshot.
_SNAPSHOT_REQUIRED_KEYS: frozenset[str] = frozenset({
    "schema_version",
    "complete",
    "relations",
    "classifications",
    "provenance",
    "diagnostics",
    "artifacts",
})

# ---------------------------------------------------------------------------
# Delivery snapshot — per-item validation constants (mirrored from the
# close-work skill; cross-skill import is banned, so re-implemented here).
# ---------------------------------------------------------------------------

# Stable identifier grammar: intent/brief slugs are lower-kebab; spec slugs
# are title-case-tolerant with dots and hyphens (mirrors resolver).
_IDENTIFIER_RE: re.Pattern[str] = re.compile(
    r"^(?:(?:intent|brief):[a-z0-9]+(?:-[a-z0-9]+)*"
    r"|spec:[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)$"
)
# Accepted `type` values for relation items.
_RELATION_TYPES: frozenset[str] = frozenset({"direct-delivery", "coordinated-delivery"})
# Accepted `route` values for relation items.
_DELIVERY_ROUTE_VALUES: frozenset[str] = frozenset(
    {"spec", "brief", "direct-light", "closed-empty"}
)
# Accepted `classification` values for classification items.
_CLASSIFICATION_VALUES: frozenset[str] = frozenset(
    {"direct-delivery", "coordinated-delivery", "no-durable-child", "unresolved"}
)
# Accepted `code` values for diagnostic items.
_SNAPSHOT_DIAGNOSTIC_CODES: frozenset[str] = frozenset({
    "delivery-target-missing",
    "delivery-projection-mismatch",
    "delivery-relation-ambiguous",
    "delivery-reference-malformed",
    "delivery-reference-unsafe",
    "delivery-resource-limit",
})
# Valid artifact-path patterns (intent files and brief files).
_INTENT_PATH_RE: re.Pattern[str] = re.compile(
    r"^docs/product/intents/[A-Za-z0-9][A-Za-z0-9._-]*\.md$"
)
_BRIEF_PATH_RE: re.Pattern[str] = re.compile(
    r"^docs/product/briefs/[A-Za-z0-9][A-Za-z0-9._-]*\.md$"
)
# Closed set of field names a diagnostic item may carry.
_DIAG_FIELD_VALUES: frozenset[str] = frozenset(
    {"Decomposed", "Discovery", "Brief", "Parent intent"}
)
# Canonical date-route form for Decomposed ambiguity diagnostics:
# "YYYY-MM-DD <route>" with exactly one space.
_CANONICAL_DATE_ROUTE_RE: re.Pattern[str] = re.compile(
    r"^\d{4}-\d{2}-\d{2} (?:spec|brief|direct-light|closed-empty)$"
)


def field_re(label: str) -> re.Pattern[str]:
    """Match a rendered bold header field, e.g. `- **Component:** foo`.

    Mirrors `lint-brief-coverage.py`'s `_BRIEF_RE` — pointer fields are matched
    by their rendered on-disk form (the bold label), not a raw frontmatter key,
    case-insensitively. Cross-skill import is banned by the spec's Boundaries,
    so this recognizer is kept in lockstep with the precedent lints by hand.
    """
    # MULTILINE so `$` is end-of-line — fields are matched per rendered line,
    # whether searched line-by-line (`_first`) or over a whole document.
    return re.compile(r"\*\*" + re.escape(label) + r":\*\*\s*(.+?)\s*$",
                      re.IGNORECASE | re.MULTILINE)


_STATUS_RE = field_re("Status")
_SLUG_RE = field_re("Slug")
_KIND_RE = field_re("Kind")
_LEVEL_RE = field_re("Level")
_TOMBSTONE_RE = field_re("Tombstone")
_TYPE_RE = field_re("Type")
# Spec producer (up-edge) pointers: the adjacent `Contract:`, and the discovery
# anchors `Brief:`/`Parent intent:` (the layer-skip shortcut when the
# intervening contract/service/… layers are globally unpopulated).
# `Discovery:` is intentionally absent: feature-delivery Discovery pointers are
# wired exclusively from the canonical snapshot (direct-delivery relations), and
# non-feature Discovery values reach _wire_up via the snapshot provenance list.
# This prevents any local fallback from re-deriving feature delivery edges.
_SPEC_UP_FIELDS = ("Contract", "Brief", "Parent intent")
# Spec forward (down-edge) pointer: the component(s) it is built into.
_COMPONENT_RE = field_re("Component")
# Container-embedded entry markers (journey actions, blueprint services).
_ACTION_RE = field_re("Action")
_SERVICE_RE = field_re("Service")
_OUTCOME_CO_OWNER_FIELD = "Outcome co-owner"


def _visible_intent_preamble(text: str) -> str:
    """Return visible intent text before its first visible level-two heading.

    The work-loop skill is projected independently, so its traceability command
    keeps this small visibility reader self-contained. Field extraction still
    uses ``field_re`` below; this function only removes closed and unclosed HTML
    comment regions and bounds the text those existing matchers may inspect.
    """
    visible_lines: list[str] = []
    inside_comment = False
    for line in text.splitlines():
        visible: list[str] = []
        remainder = line
        while remainder:
            if inside_comment:
                close = remainder.find("-->")
                if close == -1:
                    remainder = ""
                    continue
                remainder = remainder[close + 3:]
                inside_comment = False
                continue

            open_at = remainder.find("<!--")
            if open_at == -1:
                visible.append(remainder)
                break
            visible.append(remainder[:open_at])
            remainder = remainder[open_at + 4:]
            close = remainder.find("-->")
            if close == -1:
                inside_comment = True
                break
            remainder = remainder[close + 3:]

        visible_line = "".join(visible)
        if visible_line.startswith("## "):
            break
        visible_lines.append(visible_line)
    return "\n".join(visible_lines)


def _intent_preamble_field(text: str, label: str) -> str | None:
    """Return one exact visible intent-preamble value.

    Peer declarations resolve against canonical ids, so preserve internal
    whitespace instead of applying the token normalization used by graph
    pointers. Comment hiding happens before matching; one pair of wrapping
    backticks is presentation markup rather than part of the declared id.
    """
    pattern = field_re(label)
    for line in _visible_intent_preamble(text).splitlines():
        match = pattern.search(line)
        if not match:
            continue
        value = match.group(1).strip()
        if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
            value = value[1:-1].strip()
        return None if _is_placeholder(value) else value
    return None


def _is_placeholder(value: str) -> bool:
    """True for an unset/template value — empty, `none`, an HTML comment, or a
    bare angle-bracket placeholder (`<slug>`). Punctuation is tolerated after
    `none` because `_first` checks the normalized leading token."""
    v = value.strip()
    return (
        not v
        or v.lower().rstrip(".,;:") == "none"
        or v.startswith("<!--")
        or (v.startswith("<") and v.endswith(">"))
    )


def _token(raw: str) -> str:
    """Leading token of a header value, truncating at ` (`, ` →`, or `<!--`.

    Mirrors lint-spec-status.py / lint-brief-coverage.py `extract_token` (same
    delimiters); kept in lockstep by hand (cross-skill import is banned)."""
    text = raw
    for delim in (" (", " →", "<!--"):
        idx = text.find(delim)
        if idx != -1:
            text = text[:idx]
    parts = text.strip().split()
    return parts[0].strip("`") if parts else ""


# --------------------------------------------------------------------------
# Layer 0 — three-tier base resolution
# --------------------------------------------------------------------------

def load_layout(root: Path) -> dict:
    """Tier-1 config: `agentbundle-layout.toml` in `root` then `~/.agentbundle/`.

    Returns the parsed `[traceability]` table (layer → base path string) or {}.
    No-ops when the file is absent or `tomllib` is unavailable (py<3.11)."""
    if tomllib is None:
        return {}
    for cfg in (root / "agentbundle-layout.toml",
                Path.home() / ".agentbundle" / "agentbundle-layout.toml"):
        # Confine the root-relative candidate only: a symlink planted at
        # `<root>/agentbundle-layout.toml` in an untrusted tree would otherwise
        # be followed. The user-scope candidate is deliberately outside `root`
        # and is operator-owned, so it is exempt by design, not by oversight.
        if cfg.parent == root:
            canonical = _confined_file(cfg, root)
            if canonical is None:
                continue
            cfg = canonical
        text = _read(cfg)  # stat-size-guarded; None if absent/oversized/unreadable
        if text is None:
            continue
        try:
            data = tomllib.loads(text)
        except (ValueError, TypeError):
            continue
        table = data.get("traceability")
        if isinstance(table, dict):
            return table
    return {}


def resolve_base(layer: str, root: Path, layout: dict) -> tuple[Path | None, str | None]:
    """Resolve a layer's base directory by the three tiers, lazily.

    (1) `agentbundle-layout.toml` `[traceability]` key; (2) the designed default
    in `_DEFAULT_BASES`; (3) discover by marker — globbed only when neither of
    the above exists on disk. Returns (base, ambiguity-note). Base *ambiguity*
    (tier-3 finds more than one candidate) is reported, never guessed; instance
    multiplicity *within* a resolved base is normal and not an ambiguity.
    """
    configured = layout.get(layer)
    if isinstance(configured, str) and configured.strip():
        p = _confined_path(root / configured, root)
        if p is None:
            return None, f"layout base for '{layer}' escapes root — ignored"
        return (p if p.is_dir() else None), None

    default = _confined_path(root / Path(*_DEFAULT_BASES[layer]), root)
    if default is not None and default.is_dir():
        return default, None

    # Tier 3: discover by marker. Only reached when the default is absent — the
    # common case is "this layer is simply unpopulated", so a miss is not an
    # error. A bounded search keeps it from walking vendored trees.
    # `_confined` completes the control here: on Windows `os.path.islink()` is
    # False for NTFS junctions, so `_iter_dirs`' `followlinks=False` does not
    # stop `os.walk` descending one, and a discovered candidate can resolve
    # outside `root`. Every downstream read is `_confined` already, so this is
    # the one asymmetry rather than an exploit path — closed for consistency.
    candidates = _confined(_discover_layer_dirs(root, layer), root)
    if not candidates:
        return None, None
    if len(candidates) > 1:
        rels = ", ".join(sorted(c.relative_to(root).as_posix() for c in candidates))
        return candidates[0], f"layer '{layer}' base ambiguous: {rels}"
    return candidates[0], None


def _iter_dirs(root: Path):
    """Yield directories under `root`, pruning hidden / vendored / scratch trees
    and never following symlinks (the rglob-symlink-version gap, issue #190)."""
    import os
    skip = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist",
            ".worktrees", ".agents", ".claude", ".cursor", ".gemini"}
    canonical_root = root.resolve()
    for dirpath, dirnames, _ in os.walk(canonical_root, followlinks=False):
        current = _confined_path(Path(dirpath), canonical_root)
        if current is None:
            dirnames[:] = []
            continue
        kept: list[str] = []
        for name in dirnames:
            if name in skip or name.startswith("."):
                continue
            child = _confined_path(Path(dirpath) / name, canonical_root)
            if child is not None and child.is_dir():
                kept.append(name)
        dirnames[:] = kept
        yield current


def _discover_layer_dirs(root: Path, layer: str) -> list[Path]:
    """Tier-3 marker discovery: directories whose basename matches the layer's
    default leaf name (e.g. a `specs/` anywhere). Marker-based, never a single
    hardcoded path."""
    leaf = _DEFAULT_BASES[layer][-1]
    return [d for d in _iter_dirs(root) if d.name == leaf]


# --------------------------------------------------------------------------
# Layer 1 — node recognition (file-backed, container-embedded, ladder)
# --------------------------------------------------------------------------

class Graph:
    """The directed product chain. Nodes keyed by stable id → kind; edges are
    (consumer-or-child) → (producer-or-parent) is NOT how we store it; instead
    we store the canonical chain direction up→down as `edges` (from=producer,
    to=consumer) to match the sidecar's `{from, to}`. Endpoint state per edge
    target is recorded for the report."""

    def __init__(self) -> None:
        self.nodes: dict[str, str] = {}          # id → kind
        self.edges: set[tuple[str, str]] = set()  # (from=producer, to=consumer)
        self.root: str | None = None
        self.leaf_kind: str = LEAF_LAYER
        self.populated: set[str] = set()          # chain layers with ≥1 node
        # id → "local" | "satisfied-by-reference" | "unresolvable"; only for ref
        # endpoints (a present local node is implicitly "local").
        self.ref_state: dict[str, str] = {}
        self.ref_pinned: dict[str, bool] = {}
        self.dangling: list[str] = []             # malformed / missing-local edges
        # Nodes whose up- / down-edge is *dangling* (asserted but broken). The
        # break is reported once, as a dangling violation — such a node is NOT
        # also an orphan in that direction (one break, never two classes).
        self.dangling_out: set[str] = set()
        self.dangling_in: set[str] = set()
        self.notes: list[str] = []                # informational degradations
        # Ids two artifacts both derived. Recorded at insertion because the
        # built node set cannot show them: the second write replaces the first,
        # so a check reading `nodes` afterwards is true of every corpus,
        # including a colliding one.
        self.duplicate_ids: list[str] = []
        # Delivery diagnostics from the canonical snapshot.  All items are
        # printed; only items in delivery_strict_diagnostics cause --strict
        # exit failure (codes: delivery-projection-mismatch,
        # delivery-reference-unsafe).  delivery-reference-malformed and other
        # parsing-level codes are informational even under --strict.
        self.delivery_diagnostics: list[str] = []
        self.delivery_strict_diagnostics: list[str] = []

    def add(self, node_id: str, kind: str) -> None:
        if node_id in self.nodes:
            self.duplicate_ids.append(
                f"{node_id}: derived by two artifacts "
                f"(kinds {self.nodes[node_id]!r} and {kind!r})"
            )
        self.nodes[node_id] = kind
        if kind in CHAIN:
            self.populated.add(kind)

    def add_edge(self, producer: str, consumer: str) -> None:
        self.edges.add((producer, consumer))


# Skip implausibly large files — an untrusted repo could ship a multi-GB
# `traceability.json` / `spec.md`; reading it whole is a memory-exhaustion DoS.
_MAX_FILE_BYTES = 8 * 1024 * 1024


def _read(path: Path) -> str | None:
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _within(path: Path, root: Path) -> bool:
    """True when `path` is inside `root` after symlink resolution — the
    confinement check that keeps every read inside `--root`. A hostile
    `agentbundle-layout.toml` value (`../../../etc`) or a symlinked artifact dir
    cannot redirect a read outside the tree (`root` is pre-resolved in `main`)."""
    return _confined_path(path, root) is not None


def _confined_path(path: Path, root: Path) -> Path | None:
    """Return the canonical path only when it remains below ``root``."""
    try:
        resolved = path.resolve()
        resolved.relative_to(root)
        return resolved
    except (OSError, ValueError, RuntimeError):
        return None


def _confined(paths, root: Path) -> list[Path]:
    """Globbed / iterated paths filtered to those confined within `root` — a
    `pathlib.glob` follows symlinked dirs (unlike `os.walk(followlinks=False)`),
    so each result is re-checked before it is read."""
    confined: list[Path] = []
    for path in paths:
        canonical = _confined_path(path, root)
        if canonical is not None:
            confined.append(canonical)
    return confined


def _confined_file(path: Path, root: Path) -> Path | None:
    """Return a canonical in-root regular-file candidate, else ``None``."""
    canonical = _confined_path(path, root)
    return canonical if canonical is not None and canonical.is_file() else None


def _first(text: str, pat: re.Pattern[str]) -> str | None:
    for line in text.splitlines():
        m = pat.search(line)
        if m:
            value = _token(m.group(1))
            return None if _is_placeholder(value) else value
    return None


def _slug_id(kind: str, slug: str) -> str:
    """Typed stable id `<kind>:<slug>` (the sidecar form, e.g. `spec:foo`)."""
    return f"{kind}:{slug}"


def recognize_specs(base: Path, root: Path, g: Graph) -> dict[str, Path]:
    """File-backed `spec` nodes: `<specs-base>/<slug>/spec.md` carrying a
    rendered `**Status:**`. Id `spec:<slug>`. Returns slug→path for edge build."""
    found: dict[str, Path] = {}
    for spec_path in sorted(_confined(base.glob("*/spec.md"), root)):
        text = _read(spec_path)
        if text is None or not _STATUS_RE.search(text):
            continue
        slug = spec_path.parent.name
        g.add(_slug_id("spec", slug), "spec")
        found[slug] = spec_path
    return found


def recognize_components(base: Path, root: Path, g: Graph) -> None:
    """File-backed `component` nodes: an immediate sub-directory of the
    components base carrying a `catalog-info.yaml` (the Backstage canonical
    marker) is a component, identified by its `kind:namespace/name`. A
    sub-directory with no `catalog-info.yaml` is *not yet catalogued* — a
    polyglot `packages/` tree's build-tooling / config dirs are deliberately
    not flagged as chain components."""
    for child in sorted(_confined(base.iterdir(), root)):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if _confined_file(child / "catalog-info.yaml", root) is not None:
            g.add(_component_id(child, root), "component")


def _component_id(component_dir: Path, root: Path) -> str:
    """Backstage `kind:namespace/name` from `catalog-info.yaml`, else
    `component:<dirname>` (a stdlib-only, line-based read — no YAML dep). The
    `catalog-info.yaml` read is confined: a symlink pointing outside `--root` is
    not followed (completing the `_confined` guard for this nested read)."""
    cat = _confined_file(component_dir / "catalog-info.yaml", root)
    text = _read(cat) if cat is not None else None
    if text:
        kind = name = namespace = None
        for line in text.splitlines():
            s = line.strip()
            if s.lower().startswith("kind:"):
                kind = s.split(":", 1)[1].strip().lower()
            elif s.lower().startswith("name:") and name is None:
                name = s.split(":", 1)[1].strip()
            elif s.lower().startswith("namespace:") and namespace is None:
                namespace = s.split(":", 1)[1].strip()
        if kind and name:
            return f"{kind}:{namespace or 'default'}/{name}"
    return _slug_id("component", component_dir.name)


def recognize_briefs(base: Path, root: Path, g: Graph) -> dict[str, Path]:
    """Discovery-anchor `brief` nodes: `<briefs-base>/*.md` (non-`_`), keyed by
    their `**Slug:**` (the id a spec's `Brief:` back-link names; mirrors
    lint-brief-coverage.py). Kind 'brief' is outside CHAIN — a brief is never
    orphan-checked itself; it is the producer a spec attaches to."""
    found: dict[str, Path] = {}
    for p in sorted(_confined(base.glob("*.md"), root)):
        if p.name.startswith("_"):
            continue
        text = _read(p)
        if text is None:
            continue
        slug = _first(text, _SLUG_RE) or p.stem
        bid = _slug_id("brief", slug)
        # Through `add`, not a direct assignment: a direct write bypasses the
        # duplicate guard, and a brief can collide with any other kind.
        g.add(bid, "brief")
        found[bid] = p
    return found


def recognize_screens(base: Path, root: Path, g: Graph) -> None:
    """File-backed `screen` nodes carrying `**Type:** screen-brief`, found
    **recursively** under `<screens-base>`. `user-flow` nests a per-screen
    brief at `screens/<slug>/<screen>.md`, so the walk mirrors
    `recognize_contracts` (symlink-safe `_iter_dirs`, the issue #190 rglob gap)
    rather than a flat `*.md` glob. Id `screen:<stem>`. A screen-flow *index*
    file (`type: screen-flow` frontmatter, no bold-body `**Type:** screen-brief`)
    is not matched."""
    for d in _iter_dirs(base):
        if not _within(d, root):
            continue
        for p in sorted(_confined(d.glob("*.md"), root)):
            if p.name.startswith("_"):
                continue
            text = _read(p)
            if text and (_first(text, _TYPE_RE) or "").lower() == "screen-brief":
                g.add(_slug_id("screen", p.stem), "screen")


def recognize_contracts(base: Path, root: Path, g: Graph) -> None:
    """File-backed `contract` nodes under `<contracts-base>/<type>/`. Stable id
    `contract:<name>@<version>` parsed from the filename `name.vN` / `name@N`,
    degrading to `contract:<stem>` when no version is encoded."""
    # Walk symlink-safe (the issue #190 rglob-symlink gap), one dir at a time.
    for d in _iter_dirs(base):
        if not _within(d, root):
            continue
        for p in sorted(_confined(d.glob("*"), root)):
            if (
                not p.is_file()
                or p.name.startswith("_")
                or p.suffix not in {".md", ".yaml", ".yml", ".json"}
            ):
                continue
            stem = p.stem
            m = re.match(r"(.+?)[.@]v?(\d+)$", stem)
            cid = f"contract:{m.group(1)}@{m.group(2)}" if m else _slug_id("contract", stem)
            g.add(cid, "contract")


def recognize_ladder(base: Path, root: Path, g: Graph) -> dict[str, Path]:
    """Container/ladder `outcome`/`opportunity`/`capability` nodes from the
    intent ladder `<intents-base>/*.md`. The ladder tags
    `outcome`/`opportunity` *kinds* across `vision`/`strategy`/`capability`/
    `feature` *levels*, so `capability` is a level while the other two are
    kinds. The extractor maps `**Kind:** outcome|opportunity` → that chain node,
    and `**Level:** capability` → the `capability` node — the producer format the
    `frame-intent`/`decompose-intent` intent template now emits (see
    `product-engineering`'s `intent-model.md` § Placing an intent on the
    traceability chain). Returns slug→path for edge build."""
    found: dict[str, Path] = {}
    for p in sorted(_confined(base.glob("*.md"), root)):
        if p.name.startswith("_"):
            continue
        text = _read(p)
        if text is None:
            continue
        slug = _first(text, _SLUG_RE) or p.stem
        kind = (_first(text, _KIND_RE) or "").lower()
        level = (_first(text, _LEVEL_RE) or "").lower()
        node_kind = None
        if kind in ("outcome", "opportunity"):
            node_kind = kind
        elif level == "capability":
            node_kind = "capability"
        if node_kind:
            g.add(_slug_id(node_kind, slug), node_kind)
            found[_slug_id(node_kind, slug)] = p
    return found


def _is_tombstone(text: str) -> bool:
    """True when the preamble (text before the first `## ` heading) carries a
    `Tombstone:` field. A tombstone keeps its retired `Slug:` so old links
    resolve, but it names no live intent; deriving a node from it would collide
    with the reissued record that carries the same slug. A `Tombstone:` line in
    the body does not retire a live intent."""
    preamble = re.split(r"^## ", text, maxsplit=1, flags=re.MULTILINE)[0]
    return _TOMBSTONE_RE.search(preamble) is not None


def recognize_intents(base: Path, root: Path, g: Graph,
                      claimed: set[Path]) -> dict[str, Path]:
    """File-backed `intent` nodes: `<intents-base>/*.md` that no ladder rung
    already claims (`claimed` is `recognize_ladder`'s own recognized paths —
    the `outcome`/`opportunity`/`capability` files). Covering the whole
    directory would give each of those 33 files a second id, taking every live
    bare `Parent intent:` pointer to ambiguous against its own target
    measured against a real corpus; the exclusion is the whole design.

    Id `intent:<slug>`, where `slug` is the **`Slug:` field value, never the
    filename stem** — 5 of the 117 filenames carry an ordinal prefix, and
    an ordinal identifies a record's place in a series, and a series position
    is not a name — two records can swap places without either changing what it
    is about, so a pointer keyed on one can be silently wrong. A file carrying
    no `Slug:` field is reported via `g.notes` and contributes no node; it does
    not fall back to the stem, because the stem is the form just ruled out.

    Returns id→path for edge build, so an unclaimed intent file's own
    `Parent intent:` pointer joins the same producer-pointer wiring pass as
    briefs and ladder rungs — registration alone leaves that pointer unbuilt."""
    found: dict[str, Path] = {}
    for p in sorted(_confined(base.glob("*.md"), root)):
        if p.name.startswith("_") or p in claimed:
            continue
        text = _read(p)
        if text is None:
            continue
        if _is_tombstone(text):
            continue
        slug = _first(text, _SLUG_RE)
        if not slug:
            g.notes.append(
                f"{p.relative_to(root).as_posix()}: no Slug: field — "
                f"no intent: node created"
            )
            continue
        iid = _slug_id("intent", slug)
        g.add(iid, "intent")
        found[iid] = p
    return found


def outcome_co_owner_findings(
    declarations: dict[str, str], intent_ids: set[str]
) -> list[str]:
    """Report co-owner declarations that do not name a different intent artifact.

    ``declarations`` maps each source canonical intent id to its visible
    ``Outcome co-owner:`` value. Resolution is deliberately not graph wiring: a
    peer declaration validates against the already-derived intent id registry
    and never calls ``Graph.add_edge``.
    """
    findings: list[str] = []
    for source, target in sorted(declarations.items()):
        if target == source:
            findings.append(
                f"{source}: Outcome co-owner self-reference names itself ({target})"
            )
        elif target not in intent_ids:
            findings.append(
                f"{source}: Outcome co-owner names unresolved target {target}"
            )
    return findings


def _outcome_co_owner_declarations(intent_paths: dict[str, Path]) -> dict[str, str]:
    declarations: dict[str, str] = {}
    for intent_id, path in sorted(intent_paths.items()):
        text = _read(path) or ""
        value = _intent_preamble_field(text, _OUTCOME_CO_OWNER_FIELD)
        if value:
            declarations[intent_id] = value
    return declarations


def _sidecar_outcome_co_owner_findings(root: Path, layout: dict) -> list[str]:
    """Validate on-disk co-owner peers while a sidecar owns graph structure.

    A sidecar replaces structural node and edge derivation, but it does not
    replace the intent artifacts that declare peer ownership. Build only the
    canonical intent-id registry needed for peer validation; keep the result
    separate from the authoritative graph so the declaration cannot add an
    edge or alter sidecar drift semantics.
    """
    base, _ = resolve_base("outcome", root, layout)
    if base is None:
        return []

    registry = Graph()
    ladder_paths = recognize_ladder(base, root, registry)
    intent_paths = recognize_intents(
        base, root, registry, claimed=set(ladder_paths.values())
    )
    artifact_paths = {**ladder_paths, **intent_paths}
    return outcome_co_owner_findings(
        _outcome_co_owner_declarations(artifact_paths),
        set(artifact_paths),
    )


def recognize_entries(base: Path, root: Path, g: Graph, kind: str,
                      pat: re.Pattern[str]) -> dict[str, Path]:
    """Container-embedded `action` (journey-map) / `service` (service-blueprint)
    nodes — entries extracted from a container by a rendered `**Action:**` /
    `**Service:**` marker. Degrades to "unpopulated" on an unrecognized shape.
    Returns id→containing-file for edge build."""
    found: dict[str, Path] = {}
    for p in sorted(_confined(base.glob("*.md"), root)):
        if p.name.startswith("_"):
            continue
        text = _read(p)
        if text is None:
            continue
        for line in text.splitlines():
            m = pat.search(line)
            if m and not _is_placeholder(m.group(1)):
                slug = _token(m.group(1))
                if slug:
                    g.add(_slug_id(kind, slug), kind)
                    found[_slug_id(kind, slug)] = p
    return found


# --------------------------------------------------------------------------
# Layer 3 — cross-repo endpoint resolution (three states)
# --------------------------------------------------------------------------

def load_rollup_ids(root: Path, layout: dict) -> dict[str, bool]:
    """Cross-repo component rows from a value-stream rollup
    (`docs/product/rollups/*.md`). Returns referenced stable-id → pinned?
    The rollup row schema is
    `| Component | Brief (repo+slug) | Contract@version | Status | Coverage |`;
    a `<contract>@<version>` cell is a pinned reference, a bare id is unpinned.
    Reused verbatim — never a parallel mechanism."""
    refs: dict[str, bool] = {}
    base, _ = _anchor_base(root, layout, "rollups", _ROLLUPS_BASE)
    if base is None:
        return refs
    for p in sorted(_confined(base.glob("*.md"), root)):
        if p.name.startswith("_"):
            continue
        text = _read(p)
        if text is None:
            continue
        for line in text.splitlines():
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
            for cell in cells:
                if not cell or cell.lower() in ("component", "status (snapshot)"):
                    continue
                if set(cell) <= set("-: "):
                    continue
                if "@" in cell:  # contract@version — a pinned reference
                    refs[cell] = True
                    refs[cell.split("@", 1)[0]] = refs.get(cell.split("@", 1)[0], False)
                elif "/" in cell or "·" in cell:  # kind:ns/name or repo·slug
                    refs[cell] = False
    return refs


_CROSSREPO_RE = re.compile(r".+/.+|.+@.+|.+·.+")

# An ordinal (`FEAT-0001`) or an ordinal-prefixed filename stem
# (`FEAT-0001-intent-identity-and-registration`) — never accepted as a pointer
# value (a series position is not a name). Checked ahead of the
# bare-slug suffix scan so an ordinal-shaped target refuses even where it would
# otherwise suffix-match a local id derived — wrongly — from a filename stem.
_ORDINAL_RE = re.compile(r"^[A-Z]+-\d{4}(-.+)?$")


def resolve_endpoint(target: str, local_ids: set[str],
                     rollup: dict[str, bool]) -> tuple[str, bool, str]:
    """Classify an edge target into one of the five endpoint states.

    Returns (state, pinned, resolved-id). `local` when the id (or its bare-slug
    form) is in the local node set — `resolved-id` is then the *canonical* local
    node id, so the edge attaches to the node, not the bare token.
    `ambiguous` when a bare slug suffix-matches more than one local node id —
    `resolved-id` is then every matching candidate, sorted and comma-joined, so
    the caller can name them without a second scan. It is its own state, not a
    reuse of `dangling`: `dangling` means the target names *no* local node and
    its message says so, while `ambiguous` means it names *several* — a caller
    cannot otherwise tell one from the other, and no candidate is chosen on the
    author's behalf (the caller treats this as a hard violation, same as
    `dangling`). `satisfied-by-reference` when it resolves through the rollup
    (pinned if it carries `@version`); `unresolvable` for a well-formed
    cross-repo reference with no resolution; `dangling` for a missing
    *local-shaped* target, which also covers an ordinal or an ordinal-prefixed
    filename stem (the caller treats that as a hard violation). For non-local,
    non-ambiguous states `resolved-id` is the target itself (the external
    stable-id)."""
    if target in local_ids:
        return "local", False, target
    if _ORDINAL_RE.fullmatch(target):
        return "dangling", False, target
    # Bare-slug match against every local node id ending in `:<slug>` /
    # `/<slug>`. A slug can suffix-match more than one id — the old comment
    # here only conceded the risk before silently taking the sorted-first
    # match; now every match is collected and, when there is more than one,
    # the caller refuses rather than choosing one on the author's behalf.
    matches = sorted(
        nid for nid in local_ids
        if nid.endswith((f":{target}", f"/{target}"))
    )
    if len(matches) > 1:
        return "ambiguous", False, ", ".join(matches)
    if matches:
        return "local", False, matches[0]
    if target in rollup:
        return "satisfied-by-reference", rollup[target], target
    base = target.split("@", 1)[0]
    if base in rollup:
        return "satisfied-by-reference", "@" in target, target
    if _CROSSREPO_RE.fullmatch(target):
        # Well-formed cross-repo shape but unresolved — open-world honest gap.
        return "unresolvable", "@" in target, target
    return "dangling", False, target


# --------------------------------------------------------------------------
# Sidecar path (authoritative when present)
# --------------------------------------------------------------------------

def discover_sidecar(root: Path, layout: dict) -> Path | None:
    """Three-tier discovery of a `_state/traceability.json`: (1) layout
    `[traceability].sidecar`; (2) under the default discovery base; (3) glob
    `**/_state/traceability.json` (bounded). Never a single hardcoded path."""
    configured = layout.get("sidecar")
    if isinstance(configured, str) and configured.strip():
        return _confined_file(root / configured, root)
    default = _confined_path(root / Path(*_SIDECAR_DEFAULT_BASE), root)
    if default is not None and default.is_dir():
        for d in _iter_dirs(default):
            cand = _confined_file(d / Path(*_SIDECAR_RELPATH), root)
            if cand is not None:
                return cand
    for d in _iter_dirs(root):
        if d.name == "_state":
            cand = _confined_file(d / "traceability.json", root)
            if cand is not None:
                return cand
    return None


def load_sidecar(path: Path, g: Graph) -> bool:
    """Populate `g` from a sidecar instance, read by convention + the
    `schema_version` stamp (never importing the definition). Returns True when a
    recognized instance was loaded; on an unreadable / unrecognized-schema /
    malformed instance it appends a note and returns False (warn, never crash)."""
    text = _read(path)
    if text is None:
        g.notes.append(f"sidecar unreadable: {path.name}")
        return False
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        g.notes.append(f"sidecar malformed JSON: {path.name}")
        return False
    version = str(data.get("schema_version", ""))
    if version not in KNOWN_SCHEMA_VERSIONS:
        g.notes.append(
            f"sidecar schema_version '{version}' unrecognized — skipped "
            f"(deriving from artifacts)"
        )
        return False
    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        g.notes.append(f"sidecar missing nodes/edges: {path.name}")
        return False
    for n in nodes:
        if isinstance(n, dict) and "id" in n:
            g.nodes[str(n["id"])] = str(n.get("kind", ""))
    for e in edges:
        if isinstance(e, dict) and "from" in e and "to" in e:
            g.add_edge(str(e["from"]), str(e["to"]))
    g.root = str(data["root"]) if data.get("root") else None
    g.leaf_kind = str(data.get("leaf_kind", LEAF_LAYER))
    return True


# --------------------------------------------------------------------------
# Layer 4 — classification (orphan, dangling, cycle)
# --------------------------------------------------------------------------

def _find_cycles(g: Graph) -> list[str]:
    """Detect self-edges and cycles in the producer→consumer graph with an
    **iterative** (explicit-stack) DFS — no recursion limit, so a deep chain
    from an untrusted sidecar terminates rather than overflowing. Returns one
    description per distinct cycle, deduplicated by node-set (two different
    cycles over the same nodes collapse to one line — for a hard-fail lint one
    is enough)."""
    self_edges = sorted({a for a, b in g.edges if a == b})
    cycles = [f"self-referential edge: {nid} → {nid}" for nid in self_edges]

    adj: dict[str, list[str]] = {}
    for a, b in g.edges:
        if a != b:
            adj.setdefault(a, []).append(b)

    WHITE, GREY, BLACK = 0, 1, 2
    color: dict[str, int] = dict.fromkeys(g.nodes, WHITE)
    seen_cycle: set[frozenset[str]] = set()

    for start in list(g.nodes):
        if color.get(start, WHITE) != WHITE:
            continue
        color[start] = GREY
        path = [start]
        stack: list[tuple[str, object]] = [(start, iter(adj.get(start, ())))]
        while stack:
            node, it = stack[-1]
            descended = False
            for nxt in it:  # type: ignore[assignment]
                state = color.get(nxt, WHITE)
                if state == GREY:  # back-edge → cycle from nxt to node
                    cyc = path[path.index(nxt):]
                    key = frozenset(cyc)
                    if key not in seen_cycle:
                        seen_cycle.add(key)
                        cycles.append("cycle: " + " → ".join(cyc + [nxt]))
                elif state == WHITE:
                    color[nxt] = GREY
                    path.append(nxt)
                    stack.append((nxt, iter(adj.get(nxt, ()))))
                    descended = True
                    break
            if not descended:
                color[node] = BLACK
                stack.pop()
                path.pop()
    return cycles


def _nearest_populated_above(layer: str, populated: set[str]) -> str | None:
    idx = CHAIN.index(layer)
    for i in range(idx - 1, -1, -1):
        if CHAIN[i] in populated:
            return CHAIN[i]
    return None


def _nearest_populated_below(layer: str, populated: set[str]) -> str | None:
    idx = CHAIN.index(layer)
    for i in range(idx + 1, len(CHAIN)):
        if CHAIN[i] in populated:
            return CHAIN[i]
    return None


def classify_standalone(g: Graph, briefs_present: bool) -> list[tuple[str, str, str]]:
    """Orphan classification for the derived (standalone) graph.

    A node is a *backward (up) orphan* when it has no producer edge, is not the
    root layer, and a producer layer is populated above it (the
    globally-unpopulated layer-skip: an empty intervening layer everywhere is
    skipped to the nearest populated one; skipping a *populated* layer is a real
    orphan). A *forward (down) orphan* is the mirror (no consumer, non-leaf,
    consumer layer populated). Terminal exemption: `outcome` is never a backward
    orphan, `component` never a forward orphan.

    `briefs_present` makes the brief the spec's producer layer (the
    author-delivery-brief continue brief↔spec edge): a spec with no producer is
    then a backward
    orphan even when no CHAIN producer layer is populated above it. Returns
    (id, kind, reason)."""
    has_in = {to for _, to in g.edges}
    has_out = {frm for frm, _ in g.edges}
    orphans: list[tuple[str, str, str]] = []
    for nid, kind in sorted(g.nodes.items()):
        if kind not in CHAIN:
            continue
        missing: list[str] = []
        producer_above = _nearest_populated_above(kind, g.populated) is not None
        if kind == "spec" and briefs_present:
            producer_above = True
        if (kind != ROOT_LAYER and nid not in has_in and producer_above
                and nid not in g.dangling_in):
            missing.append("no producer (up-edge)")
        if (kind != LEAF_LAYER and nid not in has_out
                and nid not in g.dangling_out
                and _nearest_populated_below(kind, g.populated) is not None):
            missing.append("no consumer (down-edge)")
        if missing:
            orphans.append((nid, kind, "; ".join(missing)))
    return orphans


def classify_sidecar(g: Graph) -> list[tuple[str, str, str]]:
    """Orphan classification for the authoritative sidecar graph — the
    `check_sidecar` rule: `root` is exempt from an in-edge,
    `leaf_kind` from an out-edge, everything else needs both. The sidecar's
    edges already encode any layer-skip explicitly, so no populated-layer
    inference is applied. A **reference (external) endpoint** registered by
    `resolve_sidecar_endpoints` is never orphan-checked — it is the cross-repo
    boundary, not a chain node owing a local producer/consumer."""
    has_in = {to for _, to in g.edges}
    has_out = {frm for frm, _ in g.edges}
    orphans: list[tuple[str, str, str]] = []
    for nid, kind in sorted(g.nodes.items()):
        if nid in g.ref_state:  # external reference endpoint — never orphan-checked
            continue
        missing: list[str] = []
        if nid != g.root and nid not in has_in:
            missing.append("no producer (up-edge)")
        if kind != g.leaf_kind and nid not in has_out:
            missing.append("no consumer (down-edge)")
        if missing:
            orphans.append((nid, kind, "; ".join(missing)))
    return orphans


def sidecar_dangling(g: Graph) -> list[str]:
    """Sidecar edge endpoints naming a node absent from the inventory. After
    `resolve_sidecar_endpoints` has run, a well-formed cross-repo reference is in
    the inventory as an `external` node, so only a bare/malformed missing-local
    token remains here — a hard violation in every mode."""
    return sorted({
        p for e in g.edges for p in e if p not in g.nodes
    })


def resolve_sidecar_endpoints(g: Graph, rollup: dict[str, bool]) -> None:
    """Resolve each sidecar edge endpoint absent from the local inventory against
    the value-stream rollup (the open-world cross-repo posture, extended from
    endpoint *resolution* to *reachability*). A well-formed cross-repo reference
    becomes a `satisfied-by-reference` / `unresolvable` **external** node — so it is
    no longer a `sidecar_dangling` endpoint and can serve as a reachability terminus
    — while a bare / malformed token is left out of inventory for `sidecar_dangling`
    to flag (hard, every mode). An `ambiguous` bare slug is reported here, by name
    and with every matching candidate, and registered as an external node so
    `sidecar_dangling` does not also flag it with a bare, candidate-less message —
    one break, one class. Mirrors the standalone `_wire` endpoint handling; reuses
    `resolve_endpoint`, never a parallel scheme. The sidecar graph is untrusted
    input, so this only ever *adds* a clearly-labelled external node — it never
    silences a missing-local target."""
    local_ids = set(g.nodes)
    for a, b in sorted(g.edges):
        for ep in (a, b):
            if ep in local_ids or ep in g.ref_state or ep in g.nodes:
                continue
            state, pinned, resolved = resolve_endpoint(ep, local_ids, rollup)
            if state in ("satisfied-by-reference", "unresolvable"):
                g.ref_state[ep] = state
                g.ref_pinned[ep] = pinned
                g.nodes.setdefault(ep, "external")
            elif state == "ambiguous":
                g.dangling.append(
                    f"sidecar edge endpoint '{ep}' is ambiguous — matches "
                    f"{resolved}"
                )
                g.nodes.setdefault(ep, "external")


def _reach(seeds: set[str], adj: dict[str, list[str]]) -> set[str]:
    """Iterative (explicit-stack) reachability over adjacency `adj` from `seeds`
    (seeds included). A visited set bounds it to **O(V+E)** and terminates on a
    cyclic or deep untrusted graph — the same posture as `_find_cycles`, no
    recursion-limit DoS."""
    seen = set(seeds)
    stack = list(seeds)
    while stack:
        node = stack.pop()
        for nxt in adj.get(node, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def reachability_sidecar(
    g: Graph,
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]], list[str]]:
    """Root→leaf reachability over the authoritative sidecar graph (sidecar mode
    only — `root` + `leaf_kind` are declared there and the graph is a closed,
    single-rooted DAG; the standalone derived graph is legitimately partial /
    multi-root and keeps presence + layer-skip).

    A node is *reachable* iff it is **forward-reachable from `root`** AND **can reach
    a clean terminus** — a node of `leaf_kind`, or a rollup-resolved
    `satisfied-by-reference` endpoint. Returns `(unreachable, soft, notes)`:

    - `unreachable` — `(id, kind, reason)` for a node not on any root→leaf path
      (not forward-reachable, or reaches no terminus at all): the `UNREACHABLE`
      disconnected-subtree finding. The caller subtracts presence orphans + dangling
      sources so the two diagnostics stay non-overlapping (one break, one class).
    - `soft` — `(id, kind, reason)` for a node whose only escape from a dead branch
      is an **`unresolvable`** cross-repo hop. Because the sidecar is untrusted
      input, a forged `x/y` out-edge must not silently green a stranded subtree, so
      an unresolvable hop is **not** a clean terminus: it is surfaced as a distinct
      informational finding (never fatal — `--strict` does not promote it), making
      the fabricated-edge gap *visible* rather than forgeably green.

    Degrades in isolation (a note, empty findings) when no `root` is declared / in
    inventory, or no `leaf_kind` terminus exists — never a crash, never the
    whole-lint exit-0 backstop."""
    notes: list[str] = []
    if not g.root or g.root not in g.nodes:
        notes.append(
            f"reachability skipped — declared root '{g.root}' absent from inventory"
            if g.root else "reachability skipped — sidecar declares no root"
        )
        return [], [], notes

    clean_termini = {nid for nid, kind in g.nodes.items() if kind == g.leaf_kind}
    clean_termini |= {nid for nid, st in g.ref_state.items()
                      if st == "satisfied-by-reference"}
    if not clean_termini:
        # No leaf to reach — presence (a bottom node with no consumer is a forward
        # orphan) already covers a leaf-less chain; flagging every node here is noise.
        notes.append("reachability skipped — no leaf_kind terminus in inventory")
        return [], [], notes
    soft_termini = {nid for nid, st in g.ref_state.items() if st == "unresolvable"}

    fwd: dict[str, list[str]] = {}
    rev: dict[str, list[str]] = {}
    for a, b in g.edges:
        fwd.setdefault(a, []).append(b)
        rev.setdefault(b, []).append(a)
    forward = _reach({g.root}, fwd)              # forward-reachable from root
    reach_clean = _reach(clean_termini, rev)     # can reach a clean terminus
    reach_any = _reach(clean_termini | soft_termini, rev)  # … incl. via unresolved

    unreachable: list[tuple[str, str, str]] = []
    soft: list[tuple[str, str, str]] = []
    for nid, kind in sorted(g.nodes.items()):
        # The root anchors the graph (never "unreachable"); a reference endpoint is
        # the cross-repo boundary — neither is itself reachability-checked.
        if nid == g.root or nid in g.ref_state or kind == "external":
            continue
        in_fwd = nid in forward
        if in_fwd and nid in reach_clean:
            continue  # cleanly on a root→leaf path
        if in_fwd and nid in reach_any:
            soft.append((nid, kind,
                         "reaches a leaf only via an unresolved cross-repo reference"))
            continue
        why: list[str] = []
        if not in_fwd:
            why.append("not forward-reachable from root")
        if nid not in reach_any:
            why.append("reaches no leaf")
        unreachable.append((nid, kind, "; ".join(why) or "off the root→leaf path"))
    return unreachable, soft, notes


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def _anchor_base(root: Path, layout: dict, key: str,
                 default: tuple[str, ...]) -> tuple[Path | None, str | None]:
    configured = layout.get(key)
    if isinstance(configured, str) and configured.strip():
        p = _confined_path(root / configured, root)
        return (p if p is not None and p.is_dir() else None), None
    p = _confined_path(root / Path(*default), root)
    return (p if p is not None and p.is_dir() else None), None


def _has_briefs(root: Path, layout: dict) -> bool:
    base, _ = _anchor_base(root, layout, "briefs", _BRIEFS_BASE)
    if base is None:
        return False
    return any(not p.name.startswith("_") for p in _confined(base.glob("*.md"), root))


# ---------------------------------------------------------------------------
# Delivery resolver — parse, validate, and invoke
# ---------------------------------------------------------------------------


def _is_canonical_target(t: str) -> bool:
    """Return True iff ``t`` is a canonical diagnostic target form.

    (a) A canonical identifier: ``intent/<brief>:<slug>`` or ``spec:<dir>``.
    (b) An artifact path: ``docs/product/intents/<name>.md`` or
        ``docs/product/briefs/<name>.md``.
    (c) A date-route string: ``YYYY-MM-DD <route>`` (exactly one space).
    """
    if _IDENTIFIER_RE.fullmatch(t):
        return True
    if _INTENT_PATH_RE.fullmatch(t):
        return True
    if _BRIEF_PATH_RE.fullmatch(t):
        return True
    return bool(_CANONICAL_DATE_ROUTE_RE.fullmatch(t))


def _require_identifier(value: object, what: str) -> None:
    """Raise ``ValueError`` when ``value`` is not a grammar-valid identifier string.

    Accepts intent, brief, and spec identifiers per ``_IDENTIFIER_RE``.  Only
    ``what`` (a trusted field name) appears in the error message; the untrusted
    value is never echoed so hostile resolver output cannot reach ``g.dangling``.
    """
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise ValueError(
            f"delivery-resolver-unavailable: {what} is not a valid identifier"
        )


def _require_member(value: object, allowed: frozenset[str], what: str) -> None:
    """Raise ``ValueError`` when ``value`` is not a string in the ``allowed`` set.

    The ``isinstance`` guard prevents ``TypeError`` from unhashable values
    (lists, dicts) that a malfunctioning resolver could inject.  Only ``what``
    (a trusted field name) appears in the error message; the untrusted value is
    never echoed so hostile resolver output cannot reach ``g.dangling``.
    """
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(
            f"delivery-resolver-unavailable: {what} has an unrecognised value"
        )


def _is_safe_artifact_path(path: str) -> bool:
    """Return True when ``path`` is a safe, non-escaping relative artifact path.

    Rejects empty paths, absolute paths, backslash-containing paths, and paths
    with any ``..`` segment.  Does not validate against the filesystem —
    confinement is the caller's responsibility.
    """
    if not path:
        return False
    if path.startswith(("/", "\\")):
        return False
    parts = path.replace("\\", "/").split("/")
    return ".." not in parts


def _artifact_path_matches(key: str, path: str) -> bool:
    """True when ``path`` is a valid artifact location for identifier ``key``.

    Mirrors close-work's ``_artifact_path_matches`` exactly (cross-skill import
    is banned, so re-implemented here).  Spec identifiers must map to
    ``docs/specs/<slug>/spec.md``; intent and brief identifiers must match
    their respective directory patterns.
    """
    kind, _, slug = key.partition(":")
    if kind == "spec":
        return path == f"docs/specs/{slug}/spec.md"
    if kind == "intent":
        return bool(_INTENT_PATH_RE.fullmatch(path))
    if kind == "brief":
        return bool(_BRIEF_PATH_RE.fullmatch(path))
    return False


def _validate_snapshot_dict(data: dict[str, Any]) -> None:
    """Validate the full shape of a snapshot dict, including per-item records.

    Mirrors close-work's ``_validate_snapshot_dict`` exactly (cross-skill import
    is banned, so re-implemented here).  Raises ``ValueError`` with a
    ``delivery-resolver-unavailable:`` prefix on any violation.

    Applies to both the text-parsing path (called from
    ``_parse_and_validate_snapshot`` after basic structure checks) and injected
    test providers (called from ``build_standalone`` on the raw provider return
    value, performing ALL checks including top-level structure).
    """
    if not isinstance(data, dict):
        raise ValueError("delivery-resolver-unavailable: top-level not a dict")
    if set(data.keys()) != _SNAPSHOT_REQUIRED_KEYS:
        raise ValueError("delivery-resolver-unavailable: wrong keys")
    if data["schema_version"] != _SNAPSHOT_SCHEMA_VERSION:
        raise ValueError("delivery-resolver-unavailable: unsupported schema_version")
    if data["complete"] is not True:
        raise ValueError("delivery-resolver-unavailable: incomplete snapshot")
    for _k in ("relations", "classifications", "provenance", "diagnostics"):
        if not isinstance(data[_k], list):
            raise ValueError(f"delivery-resolver-unavailable: {_k} not a list")
    if not isinstance(data["artifacts"], dict):
        raise ValueError("delivery-resolver-unavailable: artifacts not a dict")

    # --- relations -----------------------------------------------------------
    for _item in data["relations"]:
        if not isinstance(_item, dict):
            raise ValueError("delivery-resolver-unavailable: relation item not a dict")
        _require_member(_item.get("type"), _RELATION_TYPES, "relation type")
        _require_member(_item.get("route"), _DELIVERY_ROUTE_VALUES, "relation route")
        _require_identifier(_item.get("intent"), "relation intent")
        _require_identifier(_item.get("spec"), "relation spec")
        if _item["type"] == "coordinated-delivery":
            _require_identifier(_item.get("brief"), "relation brief")

    # --- classifications -----------------------------------------------------
    for _item in data["classifications"]:
        if not isinstance(_item, dict):
            raise ValueError(
                "delivery-resolver-unavailable: classification item not a dict"
            )
        _require_identifier(_item.get("intent"), "classification intent")
        _require_member(_item.get("route"), _DELIVERY_ROUTE_VALUES, "classification route")
        _require_member(
            _item.get("classification"), _CLASSIFICATION_VALUES, "classification"
        )

    # --- provenance ----------------------------------------------------------
    for _item in data["provenance"]:
        if not isinstance(_item, dict):
            raise ValueError(
                "delivery-resolver-unavailable: provenance item not a dict"
            )
        _require_identifier(_item.get("subject"), "provenance subject")
        _pf = _item.get("field")
        _require_member(
            _pf,
            frozenset({"Contract", "Discovery", "Parent intent"}),
            "provenance field",
        )
        if _pf == "Parent intent":
            # Parent intent records require a brief:-typed subject and a
            # required intent:-typed intent field; no target field is used.
            if not isinstance(_item.get("subject"), str) or not _item["subject"].startswith("brief:"):
                raise ValueError(
                    "delivery-resolver-unavailable: Parent intent provenance subject must be brief-typed"
                )
            _pi_intent = _item.get("intent")
            if not isinstance(_pi_intent, str) or not _pi_intent.startswith("intent:"):
                raise ValueError(
                    "delivery-resolver-unavailable: Parent intent provenance requires intent-typed intent"
                )
        else:
            if "intent" in _item:
                _require_identifier(_item["intent"], "provenance intent")
            if "target" in _item and not isinstance(_item["target"], str):
                raise ValueError("delivery-resolver-unavailable: bad provenance target")

    # --- diagnostics ---------------------------------------------------------
    for _item in data["diagnostics"]:
        if not isinstance(_item, dict):
            raise ValueError(
                "delivery-resolver-unavailable: diagnostic item not a dict"
            )
        _require_member(_item.get("code"), _SNAPSHOT_DIAGNOSTIC_CODES, "diagnostic code")
        if "subject" in _item:
            _require_identifier(_item["subject"], "diagnostic subject")
        if "field" in _item:
            _require_member(_item["field"], _DIAG_FIELD_VALUES, "diagnostic field")
        _targets = _item.get("targets", [])
        if not isinstance(_targets, list) or not all(
            isinstance(_x, str) and _is_canonical_target(_x) for _x in _targets
        ):
            raise ValueError("delivery-resolver-unavailable: bad diagnostic targets")

    # --- artifacts -----------------------------------------------------------
    for _key, _path in data["artifacts"].items():
        _require_identifier(_key, "artifacts key")
        if not isinstance(_path, str) or not _is_safe_artifact_path(_path):
            raise ValueError("delivery-resolver-unavailable: artifacts path unsafe")
        if not _artifact_path_matches(_key, _path):
            raise ValueError("delivery-resolver-unavailable: artifacts path mismatch")


def _parse_and_validate_snapshot(text: str) -> dict[str, Any]:
    """Parse and strictly validate a resolver JSON snapshot.

    Returns the snapshot dict on success.  Raises ``ValueError`` with a
    ``delivery-resolver-unavailable:`` prefix on any structural or schema
    violation: bad JSON, NaN/Infinity payload, wrong schema_version,
    incomplete flag, missing or extra keys, non-list collection, or a
    malformed per-item record.  Never raises for a structurally valid
    complete snapshot.
    """
    try:
        data = json.loads(text)
    except (ValueError, RecursionError):
        raise ValueError("delivery-resolver-unavailable: bad JSON") from None
    # Reject NaN/Infinity by round-tripping through a strict encoder.
    try:
        json.dumps(data, allow_nan=False)
    except (ValueError, TypeError):
        raise ValueError(
            "delivery-resolver-unavailable: NaN/Infinity in payload"
        ) from None
    _validate_snapshot_dict(data)  # type: ignore[arg-type]
    return data


def _run_resolver(
    root: Path,
    *,
    _resolver_path: Path | None = None,
) -> dict[str, Any]:
    """Invoke the co-located resolver subprocess and return a validated snapshot.

    Raises ``ValueError`` with a ``delivery-resolver-unavailable:`` prefix on
    any failure: binary absent, non-zero exit, timeout, OSError, oversized
    stdout, bad UTF-8, bad JSON, wrong schema, or incomplete snapshot.
    Captured stderr is never forwarded.

    ``_resolver_path`` overrides the module-level ``_RESOLVER_PATH`` constant.
    Pass a custom path in tests to exercise absent or non-regular resolver cases
    without removing the real sibling copy.

    The caller (``build_standalone``) gates invocation behind ``_has_any_anchor``
    so that repos with no discovery-side artifacts never reach this function;
    the "delivery not configured" opt-out is at that level, not here.
    """
    resolver_path = _resolver_path if _resolver_path is not None else _RESOLVER_PATH
    try:
        resolver_path.lstat()
    except FileNotFoundError:
        raise ValueError(
            "delivery-resolver-unavailable: resolver absent beside consumer"
        ) from None
    except OSError:
        raise ValueError(
            "delivery-resolver-unavailable: resolver not accessible"
        ) from None
    # Reject symlinks: the binary must be a regular file.
    if resolver_path.is_symlink() or not resolver_path.is_file():
        raise ValueError(
            "delivery-resolver-unavailable: resolver is not a regular file"
        )
    try:
        proc = subprocess.run(
            [sys.executable, str(resolver_path), "--root", str(root)],
            capture_output=True,
            timeout=_RESOLVER_TIMEOUT,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        raise ValueError(
            "delivery-resolver-unavailable: subprocess timed out"
        ) from None
    except OSError:
        raise ValueError(
            "delivery-resolver-unavailable: subprocess OSError"
        ) from None
    if proc.returncode != 0:
        raise ValueError("delivery-resolver-unavailable: non-zero exit")
    stdout: bytes = proc.stdout
    if len(stdout) > _MAX_SNAPSHOT_BYTES:
        raise ValueError(
            "delivery-resolver-unavailable: stdout exceeds size limit"
        )
    try:
        text = stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise ValueError(
            "delivery-resolver-unavailable: stdout not valid UTF-8"
        ) from None
    return _parse_and_validate_snapshot(text)


def build_standalone(root: Path, layout: dict, g: Graph,
                     rollup: dict[str, bool], *, snapshot_provider=None) -> None:
    """Layers 1–3 for the derive-from-artifacts mode: recognize nodes, build
    edges from conventional pointers, resolve each pointer endpoint to one of
    the three states (recording dangling targets as hard candidates).

    ``snapshot_provider`` is the injectable seam for tests.  When ``None``,
    ``_run_resolver`` is used.  The provider is called only when a chain anchor
    exists.  ``_run_resolver`` raises ``ValueError`` on any failure (including
    a resolver missing from beside this script, or not a regular file); the
    caller records it as a
    hard DANGLING violation and continues non-delivery checks.  When no valid
    snapshot exists and the resolver failed, specs are wired only from Contract:
    and Parent intent: (not Brief: — delivery status is unknown).  When delivery
    is not anchored at all, this function's anchor check short-circuits and the
    ``check()`` level also exits 0 silently.
    """
    bases: dict[str, Path] = {}
    for layer in CHAIN:
        base, note = resolve_base(layer, root, layout)
        if note:
            g.notes.append(note)
        if base is not None:
            bases[layer] = base

    spec_paths: dict[str, Path] = {}
    if "spec" in bases:
        spec_paths = recognize_specs(bases["spec"], root, g)
    if "component" in bases:
        recognize_components(bases["component"], root, g)
    # Briefs are the discovery anchor a spec back-links (the
    # author-delivery-brief continue
    # brief↔spec edge this generalizes) — registered as producer-anchor nodes
    # (kind 'brief', outside CHAIN, so never orphan-checked themselves).
    brief_paths: dict[str, Path] = {}
    brief_base, _ = _anchor_base(root, layout, "briefs", _BRIEFS_BASE)
    if brief_base is not None:
        brief_paths = recognize_briefs(brief_base, root, g)
    if "screen" in bases:
        recognize_screens(bases["screen"], root, g)
    if "contract" in bases:
        recognize_contracts(bases["contract"], root, g)
    ladder_paths: dict[str, Path] = {}
    intent_paths: dict[str, Path] = {}
    if bases.get("outcome") is not None:  # intents share one base
        ladder_paths = recognize_ladder(bases["outcome"], root, g)
        intent_paths = recognize_intents(
            bases["outcome"], root, g, claimed=set(ladder_paths.values())
        )
    if "action" in bases:
        recognize_entries(bases["action"], root, g, "action", _ACTION_RE)
    if "service" in bases:
        recognize_entries(bases["service"], root, g, "service", _SERVICE_RE)

    local_ids = set(g.nodes)
    intent_artifact_paths = {**ladder_paths, **intent_paths}
    g.dangling.extend(
        outcome_co_owner_findings(
            _outcome_co_owner_declarations(intent_artifact_paths),
            set(intent_artifact_paths),
        )
    )

    # -----------------------------------------------------------------------
    # Delivery snapshot: invoke the canonical resolver to get typed delivery
    # relations.  Only attempted when a chain anchor exists.  Resolver absent
    # or failing → hard DANGLING; non-delivery checks continue.
    # When no valid snapshot exists and the resolver failed, specs are wired
    # only from Contract: and Parent intent: (not Brief: — delivery status is
    # unknown).
    # -----------------------------------------------------------------------
    _snapshot: dict[str, Any] | None = None
    _resolver_failed = False
    _has_any_anchor = (
        bool(rollup)
        or bool(brief_paths)
        or bool(g.populated & _DISCOVERY_LAYERS)
    )
    if _has_any_anchor:
        # If the resolved spec or intent base differs from the resolver's
        # fixed defaults, the resolver would silently operate on different
        # paths than the lint. Fail closed with a hard DANGLING violation
        # so non-delivery checks still run but delivery edges are not
        # silently dropped.
        _spec_default = _confined_path(root / Path(*_DEFAULT_BASES["spec"]), root)
        _intent_default = _confined_path(
            root / Path(*_DEFAULT_BASES["outcome"]), root
        )
        _configured_spec_differs = (
            bases.get("spec") is not None
            and _spec_default is not None
            and bases["spec"] != _spec_default
        )
        _configured_intent_differs = (
            bases.get("outcome") is not None
            and _intent_default is not None
            and bases["outcome"] != _intent_default
        )
        if _configured_spec_differs or _configured_intent_differs:
            g.dangling.append(
                "delivery-resolver-unavailable: configured spec or intent base "
                "differs from resolver defaults; delivery edges are unavailable"
            )
            _resolver_failed = True
        else:
            _effective_provider = (
                snapshot_provider if snapshot_provider is not None else _run_resolver
            )
            try:
                _raw_snapshot = _effective_provider(root)
                # Validate dict shape for injected providers; _run_resolver
                # already validates via _parse_and_validate_snapshot.
                if snapshot_provider is not None:
                    if _raw_snapshot is None:
                        raise ValueError(
                            "delivery-resolver-unavailable: provider returned None"
                        )
                    _validate_snapshot_dict(_raw_snapshot)  # type: ignore[arg-type]
                _snapshot = _raw_snapshot
            except ValueError as _exc:
                _msg = str(_exc)
                _safe = (
                    _msg
                    if _msg.startswith("delivery-resolver-unavailable")
                    else "delivery-resolver-unavailable"
                )
                g.dangling.append(_safe)
                _resolver_failed = True

    # Spec ids that have a delivery relation in the snapshot.  For these specs,
    # delivery edges come from the snapshot; _wire_up receives only non-delivery
    # candidates (Contract:, Parent intent:, contextual-provenance local values).
    _delivery_spec_ids: set[str] = set()
    # Spec IDs mentioned in a qualifying delivery diagnostic (delivery-
    # projection-mismatch or delivery-reference-unsafe) — added to dangling_in
    # so they are excluded from backward-orphan reporting (one break, one class).
    # Component: wiring and other non-delivery checks still run for these specs.
    _delivery_diag_specs: set[str] = set()
    # Per-spec map of fields the snapshot classified as contextual.
    # The lint reads local text for these fields instead of using provenance
    # `target`. Provenance `target` values are NOT used as candidates (one
    # source rule): local text is the single source of truth.
    _contextual_prov: dict[str, set[str]] = {}

    if _snapshot is not None:
        for _rel in _snapshot["relations"]:
            _stype = _rel.get("type", "")
            _intent_id = str(_rel.get("intent", ""))
            _spec_rel_id = str(_rel.get("spec", ""))
            _brief_id = str(_rel.get("brief", ""))

            if _spec_rel_id:
                _delivery_spec_ids.add(_spec_rel_id)

            if _stype == "direct-delivery" and _intent_id and _spec_rel_id:
                # Feature intent is the producer; spec is the consumer.
                g.add_edge(_intent_id, _spec_rel_id)

            elif _stype == "coordinated-delivery" and _brief_id and _spec_rel_id:
                # Brief is the spec's immediate producer.
                g.add_edge(_brief_id, _spec_rel_id)
                if _intent_id:
                    # Intent produces the brief.  May duplicate the brief's own
                    # Parent intent: wiring below; g.edges is a set, no harm.
                    g.add_edge(_intent_id, _brief_id)

        # Apply snapshot diagnostics with sanitized output.  _validate_snapshot_dict
        # has already checked: codes against the closed code set, subjects as
        # canonical identifiers, fields against the closed field set, and every
        # target against the three canonical target forms.  No untrusted value
        # reaches the label.
        # Collect spec IDs for the two qualifying codes that indicate a
        # delivery-routing break for the spec itself:
        #   delivery-projection-mismatch — specs listed as `targets` that the
        #     intent claims to deliver but whose routes do not match.
        #   delivery-reference-unsafe   — specs whose Discovery: value resolves
        #     to a delivery intent but cannot be used safely.
        # Other codes (e.g. delivery-reference-malformed for a structural
        # Brief: field) do not indicate a delivery-routing break and must not
        # suppress Component: wiring or structural orphan checks.
        for _diag in _snapshot["diagnostics"]:
            _code = str(_diag.get("code", ""))
            _subject = str(_diag.get("subject", ""))
            _field = str(_diag.get("field", ""))
            _targets = _diag.get("targets", [])

            # Collect spec-shaped IDs for the two qualifying codes.
            if _code == "delivery-projection-mismatch":
                if isinstance(_targets, list):
                    for _dt in _targets:
                        if isinstance(_dt, str) and _dt.startswith("spec:"):
                            _delivery_diag_specs.add(_dt)
            elif _code == "delivery-reference-unsafe" and _subject.startswith("spec:"):
                _delivery_diag_specs.add(_subject)

            # Build a label: code, subject, field, and targets are all
            # validated by _validate_snapshot_dict; print only the closed-set
            # field and canonical targets, each capped to 200 characters so
            # an oversized slug cannot flood the log.
            _MAX_LABEL_PART = 200
            _label_parts = [_code] if _code else ["delivery-diagnostic"]
            if _subject:
                _s_disp = _subject if len(_subject) <= _MAX_LABEL_PART else (
                    _subject[:_MAX_LABEL_PART] + "…"
                )
                _label_parts.append(f"subject={_s_disp}")
            if _field:
                _label_parts.append(f"field={_field}")
            if isinstance(_targets, list):
                # Targets are already canonical; sort for deterministic output.
                _safe_ts = sorted(
                    t for t in _targets
                    if isinstance(t, str)
                )
                if _safe_ts:
                    _capped_ts = [
                        t if len(t) <= _MAX_LABEL_PART else t[:_MAX_LABEL_PART] + "…"
                        for t in _safe_ts
                    ]
                    _label_parts.append(f"targets=[{', '.join(_capped_ts)}]")
            _label = " ".join(_label_parts)

            if _code == "delivery-target-missing" and _subject.startswith(("spec:", "brief:")):
                # Hard DANGLING: a local spec or brief pointer names a missing target.
                g.dangling.append(f"{_subject}: {_label}")
            else:
                # Informational in default mode; delivery-projection-mismatch and
                # delivery-reference-unsafe also fail under --strict.
                # delivery-reference-malformed and other parsing-level codes remain
                # informational even under --strict.
                g.delivery_diagnostics.append(_label)
                if _code in ("delivery-projection-mismatch", "delivery-reference-unsafe"):
                    g.delivery_strict_diagnostics.append(_label)

        # Mark delivery-diagnostic specs as dangling_in so they are excluded
        # from backward-orphan reporting (one break, one class). All other
        # edge checks (Component:, _wire_up) still run for these specs.
        for _dds in _delivery_diag_specs:
            g.dangling_in.add(_dds)

        # Build the contextual-provenance field map per spec.
        # Parent intent provenance records have brief: subjects and are not
        # contextual-provenance entries for specs; skip them to leave lint
        # results unchanged.
        for _prov in _snapshot["provenance"]:
            _ps = _prov.get("subject", "")
            _pf = _prov.get("field", "")
            if _ps and _pf and _pf != "Parent intent":
                _contextual_prov.setdefault(_ps, set()).add(_pf)

    # -----------------------------------------------------------------------
    # Edge: spec → component (forward `Component:` on a spec) and
    # spec ← producer (up) via the up-fields.
    #
    # When a valid snapshot is present AND a spec has a delivery relation,
    # delivery edges already came from the snapshot; _wire_up receives only
    # non-delivery candidates so that feature-delivery Discovery:/Brief:
    # pointers are never fed into the local winner-selection path.
    # Specs in _delivery_diag_specs keep their dangling_in guard (backward-
    # orphan suppression) but continue through all edge checks — the `continue`
    # that used to skip them entirely; skipping them suppressed their
    # component and dangling checks, which must still run.
    # -----------------------------------------------------------------------
    for slug, path in spec_paths.items():
        spec_id = _slug_id("spec", slug)

        text = _read(path) or ""
        for line in text.splitlines():
            m = _COMPONENT_RE.search(line)
            if m and not _is_placeholder(m.group(1)):
                _wire(g, origin=spec_id, target=_token(m.group(1)),
                      local_ids=local_ids, rollup=rollup, origin_is_producer=True)

        if _snapshot is not None and spec_id in _delivery_spec_ids:
            # Delivery spec: snapshot supplied the delivery edge.  Wire only
            # non-delivery structural candidates — Contract: and Parent intent:
            # from spec text. Contextual-provenance fields are read locally;
            # provenance `target` is never used as a candidate.
            # Brief: is excluded: for a delivery spec the brief is captured via
            # coordinated-delivery edges.
            _candidates: list[str] = []
            for _label_field in ("Contract", "Parent intent"):
                _fval = _first(text, field_re(_label_field))
                if _fval:
                    _candidates.append(_fval)
            # Add local values for contextual-provenance fields not already
            # covered by the delivery candidate set (e.g. "Discovery").
            for _cp_field in _contextual_prov.get(spec_id, set()):
                if _cp_field not in {"Contract", "Parent intent"}:
                    _cv = _first(text, field_re(_cp_field))
                    if _cv:
                        _candidates.append(_cv)
            _wire_up(g, consumer=spec_id, candidates=_candidates,
                     local_ids=local_ids, rollup=rollup)
        elif _resolver_failed:
            # Resolver was configured but failed: Brief: delivery status is
            # unknown — omit it to avoid silently wiring a feature-delivery
            # brief as a structural parent.  Wire only the unambiguously
            # structural pointers: Contract: and Parent intent:.
            # Discovery: is always excluded (removed from _SPEC_UP_FIELDS).
            _no_snap: list[str] = []
            for _label_field in ("Contract", "Parent intent"):
                _fval = _first(text, field_re(_label_field))
                if _fval:
                    _no_snap.append(_fval)
            _wire_up(g, consumer=spec_id, candidates=_no_snap,
                     local_ids=local_ids, rollup=rollup)
        else:
            # General product-graph up-candidates (Contract:, Brief:, Parent intent:).
            # Applies when: (a) the snapshot is valid and this spec has no delivery
            # relation — Brief: confirmed not a delivery vehicle; or (b) no chain
            # anchor exists so the delivery check was skipped — Brief: retains its
            # structural role.  Discovery: is excluded (removed from
            # _SPEC_UP_FIELDS); only the snapshot may wire feature-delivery edges.
            _nd_candidates: list[str] = list(_spec_up_values(text))
            # Add local values for contextual-provenance fields not already
            # covered by _spec_up_values (e.g. "Discovery").
            if _snapshot is not None:
                for _cp_field in _contextual_prov.get(spec_id, set()):
                    if _cp_field not in set(_SPEC_UP_FIELDS):
                        _cv = _first(text, field_re(_cp_field))
                        if _cv:
                            _nd_candidates.append(_cv)
            _wire_up(g, consumer=spec_id, candidates=_nd_candidates,
                     local_ids=local_ids, rollup=rollup)

    # Edge: brief ← parent intent, ladder rungs ← parent intent, and unclaimed
    # intent files ← parent intent — all via the rendered `**Parent intent:**`
    # up-pointer.
    for origin_id, path in {**brief_paths, **ladder_paths, **intent_paths}.items():
        parent = _first(_read(path) or "", field_re("Parent intent"))
        if parent:
            _wire_up(g, consumer=origin_id, candidates=[parent],
                     local_ids=local_ids, rollup=rollup)


def _spec_up_values(spec_text: str) -> list[str]:
    """Every present producer-pointer value, in up-field priority order
    (adjacent `Contract:` first, then the discovery anchors). They are
    *alternatives* — the spec asserts a producer if any one resolves."""
    out: list[str] = []
    for label in _SPEC_UP_FIELDS:
        val = _first(spec_text, field_re(label))
        if val:
            out.append(val)
    return out


def _wire_up(g: Graph, *, consumer: str, candidates: list[str],
             local_ids: set[str], rollup: dict[str, bool]) -> None:
    """Wire a node's producer (up) edge from its candidate up-pointers.

    The two questions the candidates answer are independent:
    - **Is a producer asserted?** (the orphan question) The candidates are
      *alternatives*. Among those that resolve (local / satisfied-by-reference /
      unresolvable), a second pass over the already-resolved states prefers a
      **local** candidate over an earlier one that resolves only to an
      external reference — a typed `Brief:` parents the spec even behind an
      earlier `Contract:` or `Discovery:` that resolves only to an external
      stub. This is a preference over resolved states, not a reordering of
      `_SPEC_UP_FIELDS`: among non-local resolving candidates the first still
      wins, unchanged, so field priority is untouched for every consumer whose
      candidates never resolve local.
    - **Is any asserted pointer broken?** A candidate that is *dangling* (a
      missing local-shaped target) or *ambiguous* (a bare slug matching more
      than one local id) is a hard violation **in every mode**, fired
      regardless of whether a sibling resolves or where it sits in the
      candidate order — a broken pointer is broken.
    When no candidate resolves but one is dangling, the consumer is flagged
    `dangling_in` so the break is reported once (dangling), not also as a
    backward orphan."""
    has_dangling = False
    resolved_candidates: list[tuple[str, bool, str]] = []
    for target in candidates:
        state, pinned, resolved = resolve_endpoint(target, local_ids, rollup)
        if state == "dangling":
            g.dangling.append(
                f"{consumer}: producer pointer names missing/malformed target "
                f"'{target}'"
            )
            has_dangling = True
            continue
        if state == "ambiguous":
            g.dangling.append(
                f"{consumer}: producer pointer '{target}' is ambiguous — "
                f"matches {resolved}"
            )
            has_dangling = True
            continue
        resolved_candidates.append((state, pinned, resolved))

    # Second pass: a local candidate wins over an earlier one that resolved
    # only to an external reference; among non-local candidates the first
    # still wins (the pre-existing order).
    winner = next((c for c in resolved_candidates if c[0] == "local"), None)
    if winner is None and resolved_candidates:
        winner = resolved_candidates[0]

    if winner is not None:
        state, pinned, resolved = winner
        if state in ("satisfied-by-reference", "unresolvable"):
            g.ref_state[resolved] = state
            g.ref_pinned[resolved] = pinned
            g.nodes.setdefault(resolved, "external")
        g.add_edge(resolved, consumer)
    elif has_dangling:
        g.dangling_in.add(consumer)  # break already reported as dangling


def _wire(g: Graph, *, origin: str, target: str, local_ids: set[str],
          rollup: dict[str, bool], origin_is_producer: bool) -> None:
    """Resolve `target`'s endpoint state and record a forward (down) edge + its
    state. `origin` is a local producer naming a consumer `target` (a spec's
    forward `Component:`). A `dangling` target (missing local-shaped) is recorded
    as a hard violation against `origin` and `origin` is flagged `dangling_out`
    (so it is not *also* a forward orphan — one break, one class); a
    reference endpoint is registered as an external node so the edge has an end
    and `origin` counts as connected."""
    state, pinned, resolved = resolve_endpoint(target, local_ids, rollup)
    if state == "dangling":
        g.dangling.append(
            f"{origin}: forward pointer names missing/malformed target '{target}'"
        )
        g.dangling_out.add(origin)
        return
    if state == "ambiguous":
        g.dangling.append(
            f"{origin}: forward pointer '{target}' is ambiguous — matches "
            f"{resolved}"
        )
        g.dangling_out.add(origin)
        return
    if state in ("satisfied-by-reference", "unresolvable"):
        g.ref_state[resolved] = state
        g.ref_pinned[resolved] = pinned
        g.nodes.setdefault(resolved, "external")
    g.add_edge(origin, resolved)


def check(
    root: Path,
    strict: bool,
    *,
    snapshot_provider=None,
) -> tuple[list[str], list[str], int]:
    """Run the lint. Returns (stdout-lines, stderr-violations, exit-hint).

    exit-hint: 0 unless a hard violation (dangling/cycle, always) or — under
    `--strict` — a structural orphan.

    ``snapshot_provider`` is the injectable delivery resolver seam.  When
    ``None`` (the default), the production ``_run_resolver`` is used.  Tests
    pass an inline callable to isolate individual functions without mutating
    module-level state.
    """
    layout = load_layout(root)
    g = Graph()

    sidecar = discover_sidecar(root, layout)
    using_sidecar = False
    if sidecar is not None:
        using_sidecar = load_sidecar(sidecar, g)

    rollup = load_rollup_ids(root, layout)

    if not using_sidecar:
        build_standalone(root, layout, g, rollup,
                         snapshot_provider=snapshot_provider)
    else:
        # Resolve any cross-repo edge endpoint against the rollup so a federated
        # sidecar's external leaf is a reachability terminus, not a dangling edge.
        resolve_sidecar_endpoints(g, rollup)
        g.dangling.extend(_sidecar_outcome_co_owner_findings(root, layout))

    # No chain anchor at all → no-op clean (the lint-brief-coverage no-brief
    # precedent). The anchor is a *discovery-side* artifact — a sidecar, a
    # rollup, a brief, or a populated discovery layer (intent ladder, journey,
    # blueprint, screens) — the artifacts that exist only when a repo runs the
    # autonomous-product-team model. Specs, contracts, and components alone are
    # ordinary governance artifacts present in any repo, never an anchor: a
    # repo with `docs/specs/`, `docs/contracts/`, and `packages/` but no
    # discovery side is not running the chain, so there is nothing to trace.
    anchor = (
        using_sidecar
        or bool(rollup)
        or _has_briefs(root, layout)
        or bool(g.populated & _DISCOVERY_LAYERS)
    )
    if not anchor:
        return [], [], 0

    out: list[str] = []
    hard: list[str] = []

    posture = "meta-repo/federated" if (using_sidecar or rollup) else "single-repo"
    src = "sidecar (authoritative)" if using_sidecar else "derived from artifacts"
    out.append(f"lint-traceability: posture={posture}, source={src}, "
               f"{len(g.nodes)} node(s), {len(g.edges)} edge(s).")

    orphans = (classify_sidecar(g) if using_sidecar
               else classify_standalone(g, _has_briefs(root, layout)))
    dangling = list(g.dangling)
    if using_sidecar:
        dangling += [f"sidecar edge endpoint not in inventory: {d}"
                     for d in sidecar_dangling(g)]
    cycles = _find_cycles(g)

    # Root→leaf reachability (sidecar-authoritative mode only). The reported set is
    # additive: stranded nodes minus the presence orphans and dangling-edge sources
    # already reported, so a single break is one class, never two. Its own
    # degradations are notes; it never crashes or fails the whole lint.
    unreachable: list[tuple[str, str, str]] = []
    soft_unresolved: list[tuple[str, str, str]] = []
    if using_sidecar:
        unreach, soft, rnotes = reachability_sidecar(g)
        g.notes.extend(rnotes)
        orphan_ids = {nid for nid, _, _ in orphans}
        dangling_set = set(sidecar_dangling(g))
        # One break, one class: a node adjacent to a dangling edge — whether
        # the edge's source (its target is missing) or its consumer (its producer
        # is missing) — is already surfaced by that DANGLING violation, so it is not
        # also reported as UNREACHABLE.
        dangling_adjacent = ({a for a, b in g.edges if b in dangling_set}
                             | {b for a, b in g.edges if a in dangling_set})
        skip = orphan_ids | dangling_adjacent
        unreachable = [t for t in unreach if t[0] not in skip]
        soft_unresolved = [t for t in soft if t[0] not in skip]

    for nid, st in sorted(g.ref_state.items()):
        if st == "satisfied-by-reference":
            flag = "pinned" if g.ref_pinned.get(nid) else "unpinned (soft warning)"
            out.append(f"  - {nid}: satisfied-by-reference ({flag})")
        else:
            out.append(f"  - {nid}: unknown / not-yet-catalogued (cross-repo, "
                       f"unresolvable — informational)")

    for note in g.notes:
        out.append(f"  - note: {note}")

    for nid, kind, why in orphans:
        out.append(f"  - ORPHAN {nid} [{kind}]: {why}")

    for nid, kind, why in unreachable:
        out.append(f"  - UNREACHABLE {nid} [{kind}]: {why}")

    for nid, kind, why in soft_unresolved:
        out.append(f"  - {nid} [{kind}]: {why} (informational)")

    # Drift cross-check: sidecar present AND artifacts derivable — warn-only
    # until the matrix schema is pinned (deferred: sidecar-drift-hard-fail).
    if using_sidecar:
        drift = _drift_check(root, layout, g)
        for d in drift:
            out.append(f"  - DRIFT (warn-only): {d}")

    # Delivery diagnostics from the canonical snapshot.  delivery-projection-mismatch
    # and delivery-reference-unsafe fail under --strict; all others (including
    # delivery-reference-malformed) remain informational even under --strict.
    # Never print raw resolver stderr.
    _strict_dd_set = set(g.delivery_strict_diagnostics)
    for _dd in g.delivery_diagnostics:
        _is_strict_dd = _dd in _strict_dd_set
        _dd_verb = "— FAIL (--strict)" if (strict and _is_strict_dd) else "(informational)"
        out.append(f"  - delivery: {_dd} {_dd_verb}")

    if orphans:
        verb = "structural orphan(s)" + (" — FAIL (--strict)" if strict else " (informational)")
        out.append(f"lint-traceability: {len(orphans)} {verb}.")
    else:
        out.append("lint-traceability: no structural orphans — every node has "
                   "a producer and a consumer.")

    # Reachability summary on its own line — a --strict exit caused by a
    # disconnected subtree is legible, not folded into the orphan count.
    if unreachable:
        verb = ("disconnected subtree — FAIL (--strict)" if strict
                else "disconnected subtree (informational)")
        out.append(f"lint-traceability: {len(unreachable)} unreachable node(s), "
                   f"{verb}.")

    for d in dangling:
        hard.append(f"DANGLING — {d}")
    for dup in sorted(set(g.duplicate_ids)):
        hard.append(f"DUPLICATE ID — {dup}")
    for c in cycles:
        hard.append(f"CYCLE — {c}")

    exit_hint = 0
    _strict_exit = bool(orphans) or bool(unreachable) or bool(g.delivery_strict_diagnostics)
    if hard or (strict and _strict_exit):
        exit_hint = 1
    return out, hard, exit_hint


def _drift_check(root: Path, layout: dict, sidecar_g: Graph) -> list[str]:
    """Compare the authoritative sidecar's `spec` nodes against what the
    standalone recognizer finds on disk; report disagreements as drift
    (warn-only). Best-effort and scoped to `spec` — the only kind locally
    resolvable by a stable id without a catalog, since the upstream layers and
    components are commonly cross-repo / catalogued elsewhere."""
    derived = Graph()
    build_standalone(root, layout, derived, {})
    side = {nid for nid, k in sidecar_g.nodes.items() if k == "spec"}
    loc = {nid for nid, k in derived.nodes.items() if k == "spec"}
    return [f"{missing} present on disk but absent from sidecar"
            for missing in sorted(loc - side)]


def _validated_root(candidate: Path | None) -> Path:
    """Resolve the CLI-supplied scan root, or fall back to `_repo_root()`.

    The normalise-then-check is deliberately kept *in one function, adjacent to
    the argv read*. Taint analysers recognise that shape; they do not follow
    the `_within()` / `_confined()` confinement applied to every path derived
    from this root, because that check is interprocedural and expressed as a
    comprehension filter. Same pattern as `_loop_guards.check_artifact_status`.

    This normalises and asserts directory-ness; it deliberately does **not**
    confine the root to a fixed prefix. `--root` *is* the caller-supplied scan
    scope of a repo linter (see the module docstring), so restricting which
    directory may be scanned would break the tool's purpose. The security
    control remains `_within()`: every path *derived* from this root is
    re-checked against it before being read.
    """
    raw = candidate if candidate is not None else _repo_root()
    # `_within()` in the sibling script already catches this trio; resolve()
    # raises ValueError on an embedded null and OSError on a Windows reserved
    # name, neither of which is an OSError-only case. Letting them through
    # would produce the traceback this function exists to replace.
    try:
        root = raw.resolve()
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(
            f"lint-traceability: --root is not a usable path: {raw!r} ({exc})"
        ) from exc
    if not root.exists():
        raise SystemExit(f"lint-traceability: --root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"lint-traceability: --root is not a directory: {root}")
    return root


def _repo_root() -> Path:
    """Best-effort root for a bare manual run (git toplevel, else the script's
    grandparent). The CI gate and self-tests always pass `--root` explicitly."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except (FileNotFoundError, OSError):
        # `git` may be unavailable on PATH (or the subprocess otherwise
        # fails); fall through to the script-relative root, which is the
        # intended fallback.
        pass
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Structural-orphan traceability lint.")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument(
        "--strict", action="store_true",
        help="structural orphans exit 1 (the convergence-/CI-gate posture); "
             "dangling edges and cycles exit 1 in every mode.",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="list every per-item detail line; without it a passing run prints "
             "only its summary lines and a count of what it withheld.",
    )
    args = parser.parse_args(argv)
    root = _validated_root(args.root)

    try:
        out, hard, exit_hint = check(root, args.strict)
    except Exception as exc:  # degrade, never crash (the spec's firm posture)
        print(f"lint-traceability: degraded — unexpected error ({type(exc).__name__}): "
              f"{exc}", file=sys.stderr)
        return 0

    # A passing run withholds the per-item detail lines, which are informational
    # and dominate the byte count; the `lint-traceability:` summary lines always
    # print. Any non-zero exit prints in full, so a failure is never truncated.
    hidden = 0
    if args.verbose or exit_hint != 0:
        emitted = out
    else:
        emitted = [ln for ln in out if not ln.startswith(_DETAIL_PREFIX)]
        hidden = len(out) - len(emitted)

    for line in emitted:
        print(line)
    if hidden:
        print(f"lint-traceability: {hidden} detail line(s) hidden — re-run with "
              "--verbose to list them.")
    if hard:
        for v in hard:
            print(f"lint-traceability: {v}", file=sys.stderr)
        print(f"lint-traceability: {len(hard)} hard violation(s).", file=sys.stderr)
    return exit_hint


if __name__ == "__main__":
    sys.exit(main())
