#!/usr/bin/env python3
"""Sweep script for T5: type every resolvable `Parent intent:` value.

Spec: docs/specs/intent-reference-grammar-migration/spec.md — AC-0008, AC-0020,
AC-0023.
Plan: docs/specs/intent-reference-grammar-migration/plan.md — T5.

Why this exists: T3's `intent:` recognition makes every unclaimed intent
file's own `Parent intent:` pointer builder-visible, taking the migrated-field
cohort from 23 to 37 (AC-0023). This script re-derives that cohort from the
corpus on every run — never from a recorded list (spec.md's `Always do`) — and
rewrites every value that resolves to a single local node to `<kind>:<slug>`,
using the production recognizers and `resolve_endpoint` verbatim so it cannot
drift from the resolver it is sweeping.

Method: the node-recognition half of `build_standalone` (Layers 1-2) is
replayed here directly — not spied on — because this script needs the id to
path maps `build_standalone` builds and discards (which file backs which node),
not only the final graph. `resolve_endpoint` and `_token`/`_is_placeholder` are
imported from the production module and called unmodified, so classification
never disagrees with the linter's own.

Disposition per value:
- Already `<kind>:<slug>` and present in the local node-id set: left alone,
  recorded `done` (no edit needed).
- Bare-slug or otherwise malformed and `resolve_endpoint` returns `local`: the
  field's value is replaced with the canonical resolved id. This is the
  overwhelming majority of the cohort (25 of 37 today).
- `resolve_endpoint` returns `dangling` (no local-shaped match at all) *and*
  the raw value is a markdown link (`[title](target)`): the link's target is
  resolved relative to the source file and looked up in the same id→path maps.
  `field_re` truncates the value at the first space, so a link with a spaced
  title tokenizes to a leading bracket fragment and misclassifies as
  `dangling` even though the target genuinely resolves (the corpus's 8
  formerly-dangling `Parent intent:` values, all under `docs/product/intents/`,
  all AC-0008). These are swept too: their target resolves, so the Agent Rule
  against sweeping an unresolvable value does not reach them. A markdown link
  whose target does *not* resolve this way is left and reported, per that
  same rule.
- `resolve_endpoint` returns `unresolvable` (a well-formed cross-repo shape —
  `_CROSSREPO_RE` matches any value containing `/`, which a relative markdown
  link path does) or `ambiguous`: left untouched and reported. This is
  deliberate, not an oversight — `_wire_up` already routes an `unresolvable`
  candidate to an edge against an external-reference stub node keyed by the
  raw target string (`lint-traceability.py:1201-1207`); retyping such a value
  would resolve it `local` instead and repoint that edge, which the task's
  Done-when explicitly forbids ("the sweep preserves edges, it does not
  repoint them"). The corpus holds 4 such values today, in
  `docs/product/briefs/`, each a markdown link into `../intents/…` whose
  target contains a path separator.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType

_LINTER_RELPATH = ("packs", "core", ".apm", "skills", "work-loop", "scripts",
                    "lint-traceability.py")
_DEFAULT_STATE_PATH = Path(__file__).resolve().parent / "parent-intent-sweep-state.json"

_FIELD_LABEL = "Parent intent"

# A markdown link value: optional backtick, `[title](target)`, optional
# backtick, nothing else. Matches the two shapes seen in this corpus —
# `[Digital experience doctrine](digital-experience-doctrine.md)` and
# `` [`slug`](../intents/file.md) ``.
_LINK_RE = re.compile(r"^`?\[[^\]]*\]\(([^)]+)\)`?$")


def _load_linter(root: Path) -> ModuleType:
    path = root.joinpath(*_LINTER_RELPATH)
    spec = importlib.util.spec_from_file_location("_t5_sweep_linter", str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _recognize_all(mod: ModuleType, root: Path, layout: dict):
    """Replay `build_standalone`'s Layer 1-2 node recognition (unmodified
    function calls, same order) and return the graph, rollup input, the
    `local_ids` snapshot `resolve_endpoint` sees, and every producer-pointer-
    bearing id's own path — brief, ladder-rung, unclaimed-intent and spec — so
    a markdown link's target can be resolved back to the node it names."""
    g = mod.Graph()
    rollup = mod.load_rollup_ids(root, layout)
    bases: dict[str, Path] = {}
    for layer in mod.CHAIN:
        base, _note = mod.resolve_base(layer, root, layout)
        if base is not None:
            bases[layer] = base

    spec_paths: dict[str, Path] = {}
    if "spec" in bases:
        spec_paths = mod.recognize_specs(bases["spec"], root, g)
    if "component" in bases:
        mod.recognize_components(bases["component"], root, g)
    brief_paths: dict[str, Path] = {}
    brief_base, _ = mod._anchor_base(root, layout, "briefs", mod._BRIEFS_BASE)
    if brief_base is not None:
        brief_paths = mod.recognize_briefs(brief_base, root, g)
    if "screen" in bases:
        mod.recognize_screens(bases["screen"], root, g)
    if "contract" in bases:
        mod.recognize_contracts(bases["contract"], root, g)
    ladder_paths: dict[str, Path] = {}
    intent_paths: dict[str, Path] = {}
    if bases.get("outcome") is not None:
        ladder_paths = mod.recognize_ladder(bases["outcome"], root, g)
        intent_paths = mod.recognize_intents(
            bases["outcome"], root, g, claimed=set(ladder_paths.values())
        )
    if "action" in bases:
        mod.recognize_entries(bases["action"], root, g, "action", mod._ACTION_RE)
    if "service" in bases:
        mod.recognize_entries(bases["service"], root, g, "service", mod._SERVICE_RE)

    local_ids = set(g.nodes)
    return g, rollup, local_ids, brief_paths, ladder_paths, intent_paths, spec_paths


def _derive_cohort(mod: ModuleType, root: Path,
                    id_path_maps: dict[str, dict[str, Path]],
                    ) -> list[dict]:
    """Every builder-visible `Parent intent:` value: the producer-side maps
    (brief, ladder-rung, unclaimed-intent) via the rendered field on their own
    file, plus every spec via `_SPEC_UP_FIELDS`'s `Parent intent` slot — the
    same two sources `build_standalone` wires from
    (`lint-traceability.py:1118-1136`). One entry per file; every file in this
    corpus carries at most one `Parent intent:` line."""
    pat = mod.field_re(_FIELD_LABEL)
    entries: list[dict] = []
    seen_paths: set[Path] = set()
    for source in ("brief", "ladder", "intent", "spec"):
        for node_id, path in id_path_maps[source].items():
            if path in seen_paths:
                continue
            text = mod._read(path)
            if text is None:
                continue
            for line in text.splitlines():
                m = pat.search(line)
                if not m:
                    continue
                raw = m.group(1)
                token = mod._token(raw)
                if mod._is_placeholder(token):
                    break  # first match only, mirrors `_first`
                seen_paths.add(path)
                entries.append({
                    "path": path,
                    "origin_id": node_id,
                    "origin_source": source,
                    "raw": raw,
                    "token": token,
                    "line": line,
                })
                break
    return entries


def _resolve_link_target(mod: ModuleType, raw: str, source_path: Path, root: Path,
                          path_to_id: dict[Path, str]) -> str | None:
    """If `raw` is a markdown link, resolve its target relative to the
    source file and return the id of the node backed by that file, else
    `None`. Confined to `root` the same way every other read in the linter
    is — a target escaping the repository resolves to nothing here."""
    m = _LINK_RE.match(raw.strip())
    if not m:
        return None
    target = m.group(1)
    candidate = (source_path.parent / target)
    resolved = mod._confined_path(candidate, root)
    if resolved is None:
        return None
    return path_to_id.get(resolved)


def sweep(root: Path, state_path: Path) -> tuple[int, list[dict], list[dict]]:
    mod = _load_linter(root)
    layout = mod.load_layout(root)
    (g, rollup, local_ids, brief_paths, ladder_paths, intent_paths,
     spec_paths) = _recognize_all(mod, root, layout)

    id_path_maps = {
        "brief": brief_paths, "ladder": ladder_paths,
        "intent": intent_paths, "spec": spec_paths,
    }
    path_to_id: dict[Path, str] = {}
    for maps in id_path_maps.values():
        for node_id, path in maps.items():
            path_to_id[path.resolve()] = node_id

    cohort = _derive_cohort(mod, root, id_path_maps)

    state: dict[str, dict] = {}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))

    rewritten: list[dict] = []
    left: list[dict] = []
    edits_by_path: dict[Path, list[tuple[str, str]]] = {}

    for entry in cohort:
        path = entry["path"]
        rel = path.relative_to(root).as_posix()
        token = entry["token"]
        raw = entry["raw"]

        # Already canonical: nothing to do.
        if re.fullmatch(r"[a-z]+:[A-Za-z0-9_-]+", token) and token in local_ids:
            state[rel] = {"status": "done", "value": token, "reason": "already-typed"}
            continue

        result_state, _pinned, resolved = mod.resolve_endpoint(token, local_ids, rollup)
        new_value: str | None = None

        if result_state == "local":
            new_value = resolved
        elif result_state == "dangling":
            link_id = _resolve_link_target(mod, raw, path, root, path_to_id)
            if link_id is not None and link_id in local_ids:
                new_value = link_id

        if new_value is not None:
            edits_by_path.setdefault(path, []).append((raw, new_value))
            rewritten.append({**entry, "new_value": new_value})
            state[rel] = {"status": "done", "value": new_value,
                          "reason": f"resolved-{result_state}"}
        else:
            reason = {
                "ambiguous": f"ambiguous — matches {resolved}",
                "unresolvable": "unresolvable — cross-repo shaped, no local "
                                "resolution; leaving per Agent Rule",
                "dangling": "dangling — target does not resolve; leaving per "
                            "Agent Rule",
            }.get(result_state, f"unhandled state {result_state}")
            left.append({**entry, "reason": reason})
            state[rel] = {"status": "failed", "value": token, "reason": reason}

    for path, edits in edits_by_path.items():
        text = path.read_text(encoding="utf-8")
        for old_raw, new_val in edits:
            old_line_fragment = f"**{_FIELD_LABEL}:** {old_raw}"
            new_line_fragment = f"**{_FIELD_LABEL}:** {new_val}"
            if old_line_fragment not in text:
                raise AssertionError(
                    f"{path}: expected fragment {old_line_fragment!r} not found "
                    f"— cohort derivation and file contents disagree"
                )
            text = text.replace(old_line_fragment, new_line_fragment, 1)
        path.write_text(text, encoding="utf-8")

    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")

    # Remainder per AC-0008: every resolvable value in the cohort that is not
    # `<kind>:<slug>` after this run. A left/`ambiguous` or left/`unresolvable`
    # value is not resolvable to one target, so it is not part of the
    # remainder the criterion asserts empty — it is the Agent Rule's carve-out,
    # reported separately.
    remainder = [e for e in left if e["reason"].startswith("dangling — target")]

    return len(remainder), rewritten, left


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="repository root")
    ap.add_argument("--state", default=str(_DEFAULT_STATE_PATH),
                     help="pending/done/failed tracking file")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    state_path = Path(args.state)

    remainder_count, rewritten, left = sweep(root, state_path)

    print(f"sweep-parent-intent: {len(rewritten)} value(s) rewritten, "
          f"{len(left)} left (reported below), {remainder_count} in the "
          f"unresolved remainder.")
    for entry in rewritten:
        rel = entry["path"].relative_to(root).as_posix()
        print(f"  - {rel}: {entry['token']!r} -> {entry['new_value']}")
    for entry in left:
        rel = entry["path"].relative_to(root).as_posix()
        print(f"  ! {rel}: {entry['token']!r} left — {entry['reason']}")

    return 0 if remainder_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
