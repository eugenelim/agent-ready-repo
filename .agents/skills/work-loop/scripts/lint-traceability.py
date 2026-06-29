#!/usr/bin/env python3
"""Structural-orphan traceability lint.

This is a `work-loop` **skill script**: it lives at
`packs/core/.apm/skills/work-loop/scripts/lint-traceability.py` and projects to
every adapter's `.../skills/work-loop/scripts/`, the same way the sibling
`lint-spec-status.py` does. The agent runs it at the finish-time checklist; it
can also run as a fail-closed **CI gate** where a PR event and Python both
exist. It no-ops gracefully where Python is absent.

What it does — it generalizes `receive-brief`'s `lint-brief-coverage.py` (which
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
semantic correctness is not (the established traceability split; RFC-0048
Decision 6, deferred to the coordinator spike O10, a human call at G1.5).

**The chain spans repos, because the loops do.** `work-loop` builds per module
(one repo, or one `packages/<c>/`); `discovery-loop` and the release loop work
within or across modules, so the upstream discovery artifacts and shared
contracts commonly live in a discovery / value-stream meta-repo (ADR-0022). A
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
    `_state/` instance, RFC-0053 D7) is present it supplies the authoritative
    edge set. The schema *definition* is carried in `product-engineering`'s
    `discovery-loop` skill — this lint reads the produced instance by
    convention + the stamp, it never imports the definition.
  - When absent, the edge set is **derived from the local artifacts** (the
    standalone mode) via the declarative registry below.
  A matrix↔artifact disagreement is reported as **drift, warn-only** until the
  sidecar schema is pinned (deferred: sidecar-drift-hard-fail).

Exit codes:
  0 = clean / reported. Structural orphans are informational in default mode;
      unresolvable cross-repo endpoints, unpinned references, and drift are
      never fatal.
  1 = a hard violation — a dangling edge (a pointer to a missing local target,
      or malformed) or a cycle, **in every mode**; or, under `--strict`, any
      structural orphan (the convergence-/CI-gate enforcing "traceability
      closed", RFC-0048 O6). `--strict` degrades gracefully where the producer
      `Discovery:` headers / `type:` markers are absent (a separate CONVENTIONS
      follow-on lands those).

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

try:  # py311+ stdlib; degrade where a layout config exists but tomllib doesn't.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - py<3.11
    tomllib = None  # type: ignore[assignment]

# The canonical nine-node chain, in order (RFC-0048 note 08). Index = layer
# depth; used for adjacency, terminal exemption, and the globally-unpopulated
# layer-skip. `outcome` is the root (never a backward orphan); `component` is
# the leaf (never a forward orphan — its cross-repo consumer is the release
# loop, RFC-0049).
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
# hardcoded-path NFR, AC1/AC2; the self-test greps this block's exclusivity).
# Each layer: realization, default base (path segments under the root), and the
# layout-config key (RFC-0040 `agentbundle-layout.toml`, tier 1).
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
# in for a spec's discovery parent (the `receive-brief` brief↔spec edge this
# generalizes); a sidecar materializes the whole edge set; a rollup carries the
# cross-repo component rows. Presence of ANY anchor (or a populated chain layer)
# is what activates the chain check — absent all, the lint no-ops.
_BRIEFS_BASE = ("docs", "product", "briefs")
_ROLLUPS_BASE = ("docs", "product", "rollups")
_SIDECAR_DEFAULT_BASE = ("docs", "discovery")
_SIDECAR_RELPATH = ("_state", "traceability.json")
# --- path-defaults:end -----------------------------------------------------


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
_TYPE_RE = field_re("Type")
# Spec producer (up-edge) pointers: the adjacent `Contract:`, and the discovery
# anchors `Discovery:`/`Brief:`/`Parent intent:` (the layer-skip shortcut when
# the intervening contract/service/… layers are globally unpopulated).
_SPEC_UP_FIELDS = ("Contract", "Discovery", "Brief", "Parent intent")
# Spec forward (down-edge) pointer: the component(s) it is built into.
_COMPONENT_RE = field_re("Component")
# Container-embedded entry markers (journey actions, blueprint services).
_ACTION_RE = field_re("Action")
_SERVICE_RE = field_re("Service")


def _is_placeholder(value: str) -> bool:
    """True for an unset/template value — empty, `none`, an HTML comment, or a
    bare angle-bracket placeholder (`<slug>`). Mirrors lint-brief-coverage.py."""
    v = value.strip()
    return (
        not v
        or v.lower() == "none"
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
# Layer 0 — three-tier base resolution (RFC-0040)
# --------------------------------------------------------------------------

def load_layout(root: Path) -> dict:
    """Tier-1 config: `agentbundle-layout.toml` in `root` then `~/.agentbundle/`.

    Returns the parsed `[traceability]` table (layer → base path string) or {}.
    No-ops when the file is absent or `tomllib` is unavailable (py<3.11)."""
    if tomllib is None:
        return {}
    for cfg in (root / "agentbundle-layout.toml",
                Path.home() / ".agentbundle" / "agentbundle-layout.toml"):
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
        p = (root / configured).resolve()
        if not _within(p, root):
            return None, f"layout base for '{layer}' escapes root — ignored"
        return (p if p.is_dir() else None), None

    default = root / Path(*_DEFAULT_BASES[layer])
    if default.is_dir() and _within(default, root):
        return default, None

    # Tier 3: discover by marker. Only reached when the default is absent — the
    # common case is "this layer is simply unpopulated", so a miss is not an
    # error. A bounded search keeps it from walking vendored trees.
    candidates = _discover_layer_dirs(root, layer)
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
    for dirpath, dirnames, _ in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        yield Path(dirpath)


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
        # also an orphan in that direction (AC9: one break, never two classes).
        self.dangling_out: set[str] = set()
        self.dangling_in: set[str] = set()
        self.notes: list[str] = []                # informational degradations

    def add(self, node_id: str, kind: str) -> None:
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
    try:
        return path.resolve().is_relative_to(root)
    except (OSError, ValueError, RuntimeError):
        return False


def _confined(paths, root: Path) -> list[Path]:
    """Globbed / iterated paths filtered to those confined within `root` — a
    `pathlib.glob` follows symlinked dirs (unlike `os.walk(followlinks=False)`),
    so each result is re-checked before it is read."""
    return [p for p in paths if _within(p, root)]


def _first(text: str, pat: re.Pattern[str]) -> str | None:
    for line in text.splitlines():
        m = pat.search(line)
        if m and not _is_placeholder(m.group(1)):
            return _token(m.group(1))
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
    marker, AC1) is a component, identified by its `kind:namespace/name`. A
    sub-directory with no `catalog-info.yaml` is *not yet catalogued* — a
    polyglot `packages/` tree's build-tooling / config dirs are deliberately
    not flagged as chain components."""
    for child in sorted(_confined(base.iterdir(), root)):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if (child / "catalog-info.yaml").is_file():
            g.add(_component_id(child, root), "component")


def _component_id(component_dir: Path, root: Path) -> str:
    """Backstage `kind:namespace/name` from `catalog-info.yaml`, else
    `component:<dirname>` (a stdlib-only, line-based read — no YAML dep). The
    `catalog-info.yaml` read is confined: a symlink pointing outside `--root` is
    not followed (completing the `_confined` guard for this nested read)."""
    cat = component_dir / "catalog-info.yaml"
    text = _read(cat) if (cat.is_file() and _within(cat, root)) else None
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
        g.nodes[bid] = "brief"
        found[bid] = p
    return found


def recognize_screens(base: Path, root: Path, g: Graph) -> None:
    """File-backed `screen` nodes: `<screens-base>/*.md` carrying
    `**Type:** screen-brief`. Id `screen:<stem>`."""
    for p in sorted(_confined(base.glob("*.md"), root)):
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
            if not p.is_file() or p.name.startswith("_") or p.suffix not in {".md", ".yaml", ".yml", ".json"}:
                continue
            stem = p.stem
            m = re.match(r"(.+?)[.@]v?(\d+)$", stem)
            cid = f"contract:{m.group(1)}@{m.group(2)}" if m else _slug_id("contract", stem)
            g.add(cid, "contract")


def recognize_ladder(base: Path, root: Path, g: Graph) -> dict[str, Path]:
    """Container/ladder `outcome`/`opportunity`/`capability` nodes from the
    intent ladder `<intents-base>/*.md`. Per RFC-0048 note 04 the ladder tags
    `outcome`/`opportunity` *kinds* across `vision`/`strategy`/`capability`/
    `feature` *levels*, so `capability` is a level while the other two are
    kinds. The extractor maps `**Kind:** outcome|opportunity` → that chain node,
    and `**Level:** capability` → the `capability` node — reconciled against the
    `frame-intent`/`decompose-intent` format, degrading until it lands. Returns
    slug→path for edge build."""
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
    Reused verbatim — never a parallel mechanism (ADR-0022)."""
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


def resolve_endpoint(target: str, local_ids: set[str],
                     rollup: dict[str, bool]) -> tuple[str, bool, str]:
    """Classify an edge target into one of the three endpoint states.

    Returns (state, pinned, resolved-id). `local` when the id (or its bare-slug
    form) is in the local node set — `resolved-id` is then the *canonical* local
    node id, so the edge attaches to the node, not the bare token.
    `satisfied-by-reference` when it resolves through the rollup (pinned if it
    carries `@version`); `unresolvable` for a well-formed cross-repo reference
    with no resolution; `dangling` for a missing *local-shaped* target (the
    caller treats that as a hard violation). For non-local states `resolved-id`
    is the target itself (the external stable-id)."""
    if target in local_ids:
        return "local", False, target
    # Bare-slug match against any local node id ending in `:<slug>` / `/<slug>`,
    # sorted for determinism (a slug could in principle suffix-match >1 id). The
    # O(N log N)-per-miss scan is intentional at chain scale (hundreds of nodes,
    # not thousands); a suffix index is the move only if a monorepo outgrows it.
    for nid in sorted(local_ids):
        if nid.endswith(f":{target}") or nid.endswith(f"/{target}"):
            return "local", False, nid
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
        p = (root / configured).resolve()
        return p if (p.is_file() and _within(p, root)) else None
    default = root / Path(*_SIDECAR_DEFAULT_BASE)
    if default.is_dir() and _within(default, root):
        for d in _iter_dirs(default):
            cand = d / Path(*_SIDECAR_RELPATH)
            if cand.is_file() and _within(cand, root):
                return cand
    for d in _iter_dirs(root):
        if d.name == "_state":
            cand = d / "traceability.json"
            if cand.is_file() and _within(cand, root):
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
    color: dict[str, int] = {n: WHITE for n in g.nodes}
    seen_cycle: set[frozenset[str]] = set()

    for start in list(g.nodes):
        if color.get(start, WHITE) != WHITE:
            continue
        color[start] = GREY
        path = [start]
        stack: list[tuple[str, "object"]] = [(start, iter(adj.get(start, ())))]
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
    receive-brief brief↔spec edge): a spec with no producer is then a backward
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
    `check_sidecar` rule (RFC-0053 spike): `root` is exempt from an in-edge,
    `leaf_kind` from an out-edge, everything else needs both. The sidecar's
    edges already encode any layer-skip explicitly, so no populated-layer
    inference is applied."""
    has_in = {to for _, to in g.edges}
    has_out = {frm for frm, _ in g.edges}
    orphans: list[tuple[str, str, str]] = []
    for nid, kind in sorted(g.nodes.items()):
        missing: list[str] = []
        if nid != g.root and nid not in has_in:
            missing.append("no producer (up-edge)")
        if kind != g.leaf_kind and nid not in has_out:
            missing.append("no consumer (down-edge)")
        if missing:
            orphans.append((nid, kind, "; ".join(missing)))
    return orphans


def sidecar_dangling(g: Graph) -> list[str]:
    """Sidecar edge endpoints naming a node absent from the inventory."""
    return sorted({
        p for e in g.edges for p in e if p not in g.nodes
    })


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def _anchor_base(root: Path, layout: dict, key: str,
                 default: tuple[str, ...]) -> tuple[Path | None, str | None]:
    configured = layout.get(key)
    if isinstance(configured, str) and configured.strip():
        p = (root / configured).resolve()
        return (p if (p.is_dir() and _within(p, root)) else None), None
    p = root / Path(*default)
    return (p if (p.is_dir() and _within(p, root)) else None), None


def _has_briefs(root: Path, layout: dict) -> bool:
    base, _ = _anchor_base(root, layout, "briefs", _BRIEFS_BASE)
    if base is None:
        return False
    return any(not p.name.startswith("_") for p in base.glob("*.md"))


def build_standalone(root: Path, layout: dict, g: Graph,
                     rollup: dict[str, bool]) -> None:
    """Layers 1–3 for the derive-from-artifacts mode: recognize nodes, build
    edges from conventional pointers, resolve each pointer endpoint to one of
    the three states (recording dangling targets as hard candidates)."""
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
    # Briefs are the discovery anchor a spec back-links (the receive-brief
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
    if bases.get("outcome") is not None:  # intents share one base
        ladder_paths = recognize_ladder(bases["outcome"], root, g)
    if "action" in bases:
        recognize_entries(bases["action"], root, g, "action", _ACTION_RE)
    if "service" in bases:
        recognize_entries(bases["service"], root, g, "service", _SERVICE_RE)

    local_ids = set(g.nodes)

    # Edge: spec → component (forward `Component:` on a spec, reverse-indexed so
    # the producer is the spec and the consumer is the component) — one edge per
    # `Component:` line; and spec ← producer (up) via the up-fields.
    for slug, path in spec_paths.items():
        spec_id = _slug_id("spec", slug)
        text = _read(path) or ""
        for line in text.splitlines():
            m = _COMPONENT_RE.search(line)
            if m and not _is_placeholder(m.group(1)):
                _wire(g, origin=spec_id, target=_token(m.group(1)),
                      local_ids=local_ids, rollup=rollup, origin_is_producer=True)
        _wire_up(g, consumer=spec_id, candidates=_spec_up_values(text),
                 local_ids=local_ids, rollup=rollup)

    # Edge: brief ← parent intent, and ladder rungs ← parent intent — both via
    # the rendered `**Parent intent:**` up-pointer.
    for origin_id, path in {**brief_paths, **ladder_paths}.items():
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

    The two questions the candidates answer are independent (AC9):
    - **Is a producer asserted?** (the orphan question) The candidates are
      *alternatives* — the first that resolves (local / satisfied-by-reference /
      unresolvable) wins and gives the consumer an in-edge, so a valid `Brief:`
      parents the spec even when an adjacent `Contract:` is absent.
    - **Is any asserted pointer broken?** A candidate that is *dangling* (a
      missing local-shaped target) is a hard violation **in every mode**, fired
      regardless of whether a sibling resolves — a broken pointer is broken.
    When no candidate resolves but one is dangling, the consumer is flagged
    `dangling_in` so the break is reported once (dangling), not also as a
    backward orphan."""
    resolving: str | None = None
    has_dangling = False
    for target in candidates:
        state, pinned, resolved = resolve_endpoint(target, local_ids, rollup)
        if state == "dangling":
            g.dangling.append(
                f"{consumer}: producer pointer names missing/malformed target "
                f"'{target}'"
            )
            has_dangling = True
            continue
        if resolving is None:
            resolving = resolved
            if state in ("satisfied-by-reference", "unresolvable"):
                g.ref_state[resolved] = state
                g.ref_pinned[resolved] = pinned
                g.nodes.setdefault(resolved, "external")
    if resolving is not None:
        g.add_edge(resolving, consumer)
    elif has_dangling:
        g.dangling_in.add(consumer)  # break already reported as dangling


def _wire(g: Graph, *, origin: str, target: str, local_ids: set[str],
          rollup: dict[str, bool], origin_is_producer: bool) -> None:
    """Resolve `target`'s endpoint state and record a forward (down) edge + its
    state. `origin` is a local producer naming a consumer `target` (a spec's
    forward `Component:`). A `dangling` target (missing local-shaped) is recorded
    as a hard violation against `origin` and `origin` is flagged `dangling_out`
    (so it is not *also* a forward orphan — AC9: one break, one class); a
    reference endpoint is registered as an external node so the edge has an end
    and `origin` counts as connected."""
    state, pinned, resolved = resolve_endpoint(target, local_ids, rollup)
    if state == "dangling":
        g.dangling.append(
            f"{origin}: forward pointer names missing/malformed target '{target}'"
        )
        g.dangling_out.add(origin)
        return
    if state in ("satisfied-by-reference", "unresolvable"):
        g.ref_state[resolved] = state
        g.ref_pinned[resolved] = pinned
        g.nodes.setdefault(resolved, "external")
    g.add_edge(origin, resolved)


def check(root: Path, strict: bool) -> tuple[list[str], list[str], int]:
    """Run the lint. Returns (stdout-lines, stderr-violations, exit-hint).

    exit-hint: 0 unless a hard violation (dangling/cycle, always) or — under
    `--strict` — a structural orphan."""
    layout = load_layout(root)
    g = Graph()

    sidecar = discover_sidecar(root, layout)
    using_sidecar = False
    if sidecar is not None:
        using_sidecar = load_sidecar(sidecar, g)

    rollup = load_rollup_ids(root, layout)

    if not using_sidecar:
        build_standalone(root, layout, g, rollup)

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

    # Drift cross-check: sidecar present AND artifacts derivable — warn-only
    # until the matrix schema is pinned (deferred: sidecar-drift-hard-fail).
    if using_sidecar:
        drift = _drift_check(root, layout, g)
        for d in drift:
            out.append(f"  - DRIFT (warn-only): {d}")

    if orphans:
        verb = "structural orphan(s)" + (" — FAIL (--strict)" if strict else " (informational)")
        out.append(f"lint-traceability: {len(orphans)} {verb}.")
    else:
        out.append("lint-traceability: no structural orphans — every node has "
                   "a producer and a consumer.")

    for d in dangling:
        hard.append(f"DANGLING — {d}")
    for c in cycles:
        hard.append(f"CYCLE — {c}")

    exit_hint = 0
    if hard:
        exit_hint = 1
    elif orphans and strict:
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
    args = parser.parse_args(argv)
    root = (args.root.resolve() if args.root else _repo_root()).resolve()

    try:
        out, hard, exit_hint = check(root, args.strict)
    except Exception as exc:  # degrade, never crash (the spec's firm posture)
        print(f"lint-traceability: degraded — unexpected error ({type(exc).__name__}): "
              f"{exc}", file=sys.stderr)
        return 0

    for line in out:
        print(line)
    if hard:
        for v in hard:
            print(f"lint-traceability: {v}", file=sys.stderr)
        print(f"lint-traceability: {len(hard)} hard violation(s).", file=sys.stderr)
    return exit_hint


if __name__ == "__main__":
    sys.exit(main())
