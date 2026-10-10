"""Build an intent-graph provider from in-memory fixture text.

A migrated close-work test describes its intents as text in a dict keyed by
path. ``graph_provider_from_files`` turns the live intents in that dict into
the ``nodes`` and ``edges`` shape the bundled derivation returns, so the
closure's ``children`` arm runs against the same text the test's reader serves.

Load it under a unique ``sys.modules`` key; it is not a test module.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Mapping

_FIELD_LINE = re.compile(r"^- \*\*([^*:]+):\*\*\s*(.*)$")
_KINDS = ("outcome", "opportunity", "capability", "intent")


def _fields(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("## "):
            break
        m = _FIELD_LINE.match(line)
        if m and m.group(1).strip() not in out:
            out[m.group(1).strip()] = m.group(2).strip()
    return out


def _node_id(fields: dict[str, str], slug: str) -> str:
    kind = fields.get("Kind", "").split()[:1]
    if kind and kind[0].lower() in ("outcome", "opportunity"):
        return f"{kind[0].lower()}:{slug}"
    level = fields.get("Level", "").split()[:1]
    if level and level[0].lower() == "capability":
        return f"capability:{slug}"
    return f"intent:{slug}"


def graph_provider_from_files(
    files: Mapping[str, str], root: Path
) -> Callable[[Path], dict[str, Any]]:
    """Return a provider deriving nodes and resolved parent edges from *files*.

    Only live intents directly under ``docs/product/intents/`` become nodes; a
    tombstone is skipped. A ``Parent intent:`` value of ``<kind>:<slug>`` with a
    live target becomes a resolved edge. Any other value yields no edge.
    """
    intents_dir = str(root / "docs" / "product" / "intents")

    def provider(_root: Path) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = []
        parsed: list[tuple[dict[str, Any], dict[str, str]]] = []
        for key in sorted(files):
            if str(Path(key).parent) != intents_dir:
                continue
            f = _fields(files[key])
            slug = f.get("Slug", "")
            if not slug or "Tombstone" in f:
                continue
            node = {
                "id": _node_id(f, slug),
                "type": "intent",
                "slug": slug,
                "path": Path(key).relative_to(root).as_posix(),
                "status": f.get("Status", ""),
            }
            nodes.append(node)
            parsed.append((node, f))
        by_slug = {n["slug"]: n for n in nodes}
        edges: list[dict[str, Any]] = []
        for node, f in parsed:
            value = f.get("Parent intent", "")
            kind, _, slug = value.partition(":")
            target = by_slug.get(slug)
            if kind in _KINDS and target is not None:
                edges.append({
                    "from": node["id"],
                    "field": "Parent intent",
                    "form": "typed",
                    "to": target["id"],
                    "value": value,
                    "trust_class": "pointer_unchecked",
                    "basis": {"field": "Parent intent", "form": "typed"},
                })
        return {"nodes": nodes, "edges": edges}

    return provider
