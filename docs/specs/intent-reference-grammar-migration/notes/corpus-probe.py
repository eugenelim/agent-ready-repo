#!/usr/bin/env python3
"""Corpus-impact probe for the intent reference-grammar migration.

Spec: docs/specs/intent-reference-grammar-migration/spec.md.
Plan: docs/specs/intent-reference-grammar-migration/plan.md — T4.

Why this exists: T7 asserts that no spec's producer (in-)edge is won by a
field other than `Brief:`. `Graph.add_edge` (`lint-traceability.py:357`)
stores only `(producer, consumer)` — the built edge set alone cannot answer
which candidate field supplied a winning producer. This probe re-derives the
graph through the production recognizers, unchanged, and additionally
replays `_wire_up`'s own winner-selection logic per consumer, recording the
field beside each resolved endpoint. That recording is T7's only oracle.

Method: `build_standalone` is called once, for real, to produce the
authoritative graph (node count, edge count, dangling, orphans). `_wire_up`
is spied on during that single call — not reimplemented — so the exact
`local_ids` / `rollup` snapshots it used are captured verbatim; the
field-origin winner is then recomputed from those snapshots with
`resolve_endpoint`, both pure functions taken from the production module
rather than re-derived, so this probe cannot silently drift from the
resolver it is measuring.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

_LINTER_RELPATH = ("packs", "core", ".apm", "skills", "work-loop", "scripts",
                    "lint-traceability.py")

# Pre-delivery baseline (measured on the tree before T2, recorded in
# plan.md's Design section and notes/verification-ledger.md): 488 structural
# orphans. AC-0025 asserts the post-sweep --strict figure is no greater.
_BASELINE_ORPHAN_COUNT = 488


def _load_linter(root: Path) -> ModuleType:
    path = root.joinpath(*_LINTER_RELPATH)
    spec = importlib.util.spec_from_file_location("_corpus_probe_linter", str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _collisions(nodes: dict[str, str]) -> dict[str, list[str]]:
    """Group *local* node ids sharing the same post-kind slug.

    This is the exact suffix `resolve_endpoint` bare-slug-matches a pointer
    against (`nid.endswith(f":{target}")`): two ids differing only by kind
    but sharing a slug make any bare pointer naming that slug ambiguous.
    External reference stubs (kind `"external"`, registered by `_wire`/
    `_wire_up` against a resolved cross-repo target) are excluded — the
    Design section's counts (594 / 711 / 744 nodes, 1 / 7 / 39 collisions)
    are over registered local nodes, not the ad hoc external ids a resolved
    pointer's own target string becomes.
    """
    by_slug: dict[str, list[str]] = {}
    for nid, kind in nodes.items():
        if kind == "external":
            continue
        _, _, slug = nid.partition(":")
        by_slug.setdefault(slug, []).append(nid)
    return {slug: sorted(ids) for slug, ids in sorted(by_slug.items()) if len(ids) > 1}


def _ambiguous_pointers(dangling: list[str]) -> list[str]:
    return sorted(d for d in dangling if "is ambiguous" in d)


def _winner(mod: ModuleType, field_values: list[tuple[str, str]],
            local_ids: set[str], rollup: dict[str, bool]) -> dict[str, str | None]:
    """Replay `_wire_up`'s own two-pass winner choice: skip dangling/ambiguous
    candidates as hard violations (reported elsewhere), then prefer the first
    `local`-resolving candidate over an earlier one resolving only to an
    external reference; among non-local candidates the first still wins."""
    resolved: list[tuple[str, str, str]] = []  # (field, state, resolved-id)
    has_dangling = False
    for field, value in field_values:
        state, _pinned, resolved_id = mod.resolve_endpoint(value, local_ids, rollup)
        if state in ("dangling", "ambiguous"):
            has_dangling = True
            continue
        resolved.append((field, state, resolved_id))
    winner = next((r for r in resolved if r[1] == "local"), None)
    if winner is None and resolved:
        winner = resolved[0]
    if winner is not None:
        field, state, resolved_id = winner
        return {"field": field, "state": state, "resolved-id": resolved_id}
    if has_dangling:
        return {"field": None, "state": "dangling-or-ambiguous", "resolved-id": None}
    return {"field": None, "state": "no-candidate-resolves", "resolved-id": None}


def _field_origins(
    mod: ModuleType, root: Path, layout: dict,
    calls: list[tuple[str, list[str], set[str], dict[str, bool]]],
) -> dict[str, dict[str, str | None]]:
    """For every `_wire_up` call captured during the real build, determine
    which candidate field supplied the winning producer.

    A spec call carries multiple candidates, in `_SPEC_UP_FIELDS` priority
    order, filtered to the fields present on that spec — reconstructed here
    from the same spec text via the same `_first`/`field_re` calls
    `_spec_up_values` makes, then asserted equal to the spied candidate list
    as a drift guard. A brief / ladder-rung / unclaimed-intent call always
    carries exactly one candidate, always `Parent intent:` — the single-field
    loop in `build_standalone`."""
    spec_base, _ = mod.resolve_base("spec", root, layout)
    spec_text_by_id: dict[str, str] = {}
    if spec_base is not None:
        scratch = mod.Graph()
        for slug, path in mod.recognize_specs(spec_base, root, scratch).items():
            spec_text_by_id[mod._slug_id("spec", slug)] = mod._read(path) or ""

    origins: dict[str, dict[str, str | None]] = {}
    for consumer, candidates, local_ids, rollup in calls:
        if consumer in spec_text_by_id:
            text = spec_text_by_id[consumer]
            field_values: list[tuple[str, str]] = []
            for field in mod._SPEC_UP_FIELDS:
                val = mod._first(text, mod.field_re(field))
                if val:
                    field_values.append((field, val))
            observed = [v for _, v in field_values]
            if observed != candidates:
                raise AssertionError(
                    f"{consumer}: re-derived up-field values {observed!r} != "
                    f"spied candidates {candidates!r} — the probe has drifted "
                    f"from _spec_up_values"
                )
        else:
            if len(candidates) != 1:
                raise AssertionError(
                    f"{consumer}: expected exactly one Parent-intent candidate, "
                    f"got {candidates!r}"
                )
            field_values = [("Parent intent", candidates[0])]
        origins[consumer] = _winner(mod, field_values, local_ids, rollup)
    return origins


def probe(root: Path) -> tuple[dict, ModuleType]:
    mod = _load_linter(root)
    layout = mod.load_layout(root)
    rollup = mod.load_rollup_ids(root, layout)
    g = mod.Graph()

    sidecar = mod.discover_sidecar(root, layout)
    using_sidecar = False
    if sidecar is not None:
        using_sidecar = mod.load_sidecar(sidecar, g)

    calls: list[tuple[str, list[str], set[str], dict[str, bool]]] = []
    if not using_sidecar:
        original_wire_up = mod._wire_up

        def spy_wire_up(graph, *, consumer, candidates, local_ids, rollup):
            calls.append((consumer, list(candidates), set(local_ids), dict(rollup)))
            return original_wire_up(graph, consumer=consumer, candidates=candidates,
                                     local_ids=local_ids, rollup=rollup)

        mod._wire_up = spy_wire_up
        try:
            mod.build_standalone(root, layout, g, rollup)
        finally:
            mod._wire_up = original_wire_up
    else:
        mod.resolve_sidecar_endpoints(g, rollup)

    orphans = (mod.classify_sidecar(g) if using_sidecar
               else mod.classify_standalone(g, mod._has_briefs(root, layout)))

    reachability_ran = using_sidecar
    unreachable: list[tuple[str, str, str]] = []
    if reachability_ran:
        unreachable, _soft, _notes = mod.reachability_sidecar(g)

    result = {
        "using_sidecar": using_sidecar,
        "node_count": len(g.nodes),
        "edge_count": len(g.edges),
        "collisions": _collisions(g.nodes),
        "ambiguous_pointers": _ambiguous_pointers(g.dangling),
        "dangling": sorted(g.dangling),
        "orphans": sorted(orphans),
        "reachability_ran": reachability_ran,
        "unreachable": sorted(unreachable),
        "field_origins": (_field_origins(mod, root, layout, calls)
                          if not using_sidecar else {}),
    }
    return result, mod


def render(root: Path, result: dict) -> str:
    out: list[str] = [
        "# Corpus-impact probe — the intent reference-grammar migration",
        "",
        "Generated by `corpus-probe.py` (T4). Do not hand-edit: re-run the script.",
        "Spec: docs/specs/intent-reference-grammar-migration/spec.md, Task: T4.",
        "",
        f"- posture: {'sidecar' if result['using_sidecar'] else 'standalone'} "
        f"({'authoritative' if result['using_sidecar'] else 'derived from artifacts'})",
        f"- node count: {result['node_count']}",
        f"- edge count: {result['edge_count']}",
        f"- structural orphan count: {len(result['orphans'])}",
        f"- pre-delivery baseline (plan.md Design section): {_BASELINE_ORPHAN_COUNT}",
        f"- AC-0025 (--strict orphan non-increase): "
        f"{'PASS' if len(result['orphans']) <= _BASELINE_ORPHAN_COUNT else 'FAIL'} "
        f"({len(result['orphans'])} <= {_BASELINE_ORPHAN_COUNT})",
        "",
    ]

    out.append("## Reachability")
    out.append("")
    if result["reachability_ran"]:
        out.append(
            f"`reachability_sidecar` ran: {len(result['unreachable'])} unreachable node(s)."
        )
    else:
        out.append(
            "Not run. `check()` (`lint-traceability.py:1292`) guards "
            "`reachability_sidecar` with `if using_sidecar:`, and "
            "`discover_sidecar` (`:727`) returns `None` in this repository — "
            "measured directly, not assumed. No sidecar `_state/traceability.json` "
            "exists in this tree, so the standalone (derived-from-artifacts) path "
            "runs instead and the reachability pass never executes. There is no "
            "reachability figure to record for this corpus."
        )
    out.append("")

    out.append(f"## Collision set ({len(result['collisions'])} slug(s))")
    out.append("")
    out.append(
        "Local node ids (excluding external reference stubs) sharing the same "
        "post-kind slug — the exact suffix a bare-slug pointer's ambiguity scan "
        "matches against."
    )
    out.append("")
    if result["collisions"]:
        for slug, ids in sorted(result["collisions"].items()):
            out.append(f"- `{slug}`: {', '.join(f'`{i}`' for i in ids)}")
    else:
        out.append("_none_")
    out.append("")

    out.append(f"## Ambiguous-pointer set ({len(result['ambiguous_pointers'])})")
    out.append("")
    out.append("Live pointers whose target actually suffix-matched more than one local id.")
    out.append("")
    if result["ambiguous_pointers"]:
        out.extend(f"- {d}" for d in result["ambiguous_pointers"])
    else:
        out.append("_none_")
    out.append("")

    out.append(f"## Dangling edges ({len(result['dangling'])})")
    out.append("")
    out.append(
        "Every hard violation `check()` reports, ambiguous ones included (a "
        "superset of the ambiguous-pointer set above, for full context)."
    )
    out.append("")
    if result["dangling"]:
        out.extend(f"- {d}" for d in result["dangling"])
    else:
        out.append("_none_")
    out.append("")

    out.append(f"## Structural orphans ({len(result['orphans'])})")
    out.append("")
    if result["orphans"]:
        out.extend(f"- {nid} [{kind}]: {why}" for nid, kind, why in result["orphans"])
    else:
        out.append("_none_")
    out.append("")

    out.append(f"## Winning producer field, per consumer ({len(result['field_origins'])})")
    out.append("")
    out.append(
        "For every consumer wired through `_wire_up` (specs via the four "
        "up-fields; briefs, ladder rungs, and unclaimed intent files via "
        "`Parent intent:` alone): which field supplied the winning producer, "
        "the state it resolved to, and the resolved id. `field: none` means "
        "every candidate was dangling/ambiguous (reported above) or absent — "
        "this is T7's only oracle for 'no in-edge is won by a field other "
        "than `Brief:`', because `Graph.add_edge` stores only "
        "`(producer, consumer)`."
    )
    out.append("")
    if result["field_origins"]:
        for consumer, origin in sorted(result["field_origins"].items()):
            field = origin["field"] or "none"
            resolved = origin["resolved-id"] or "—"
            out.append(
                f"- {consumer}: field={field}, state={origin['state']}, "
                f"resolved-id={resolved}"
            )
    else:
        out.append("_none_")
    out.append("")

    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="repository root")
    ap.add_argument("--out", default=None, help="report path (default: beside this script)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    out = Path(args.out) if args.out else Path(__file__).resolve().parent / "corpus-probe.md"

    result, _mod = probe(root)
    out.write_text(render(root, result), encoding="utf-8")

    ac0025 = len(result["orphans"]) <= _BASELINE_ORPHAN_COUNT
    print(
        f"corpus-probe: {out.relative_to(root)} written — "
        f"{result['node_count']} node(s), {result['edge_count']} edge(s), "
        f"{len(result['orphans'])} orphan(s) "
        f"(AC-0025 {'PASS' if ac0025 else 'FAIL'} against baseline "
        f"{_BASELINE_ORPHAN_COUNT})."
    )
    return 0 if ac0025 else 1


if __name__ == "__main__":
    sys.exit(main())
