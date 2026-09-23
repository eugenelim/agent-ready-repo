#!/usr/bin/env python3
"""Sweep script for T7: type every resolvable `Brief:` value.

Spec: docs/specs/intent-reference-grammar-migration/spec.md — AC-0008.
Plan: docs/specs/intent-reference-grammar-migration/plan.md — T7.

Why this exists: T6 made `brief:<slug>` the canonical `Brief:` form across the
guide, the templates, the coverage join and the dispatch check; this script
migrates the data — every spec's `Brief:` value — to match. It re-derives the
34-spec cohort from the corpus on every run — never from a recorded list
(spec.md's `Always do`) — so a `Brief:` value added after this plan was
written is swept too.

Method: this script never re-derives the recognized graph itself. T5's
`sweep-parent-intent.py` already replays `build_standalone`'s Layer 1-2 node
recognition (`_recognize_all`, unmodified production functions) to produce
the exact `local_ids` / `spec_paths` maps `_wire_up` uses; that replay does
not depend on which field is being swept, so this script imports and calls it
directly rather than re-implementing it — the two scripts share the
recognition replay and differ only in which field they read and how a
left-over candidate maps back to a local id. `resolve_endpoint`, `field_re`,
`_token` and `_is_placeholder` are likewise imported from the production
linter module and called unmodified, so classification here cannot drift from
the resolver it is sweeping.

Disposition per spec's `Brief:` value:
- Absent, blank, an HTML comment, or `none` (AC-0024): outside the cohort,
  skipped entirely — this is not a value to sweep.
- Already `brief:<slug>` and present in the local node-id set: left alone,
  recorded `done` (no edit needed).
- `resolve_endpoint` returns `local` directly (the raw value already matches a
  local id, e.g. a bare slug that happens to suffix-match exactly one node):
  rewritten to that canonical id.
- Otherwise (today, every one of the 34 cohort values takes this path): the
  raw value is repository-relative-path shaped
  (`docs/product/briefs/<slug>.md`, which `resolve_endpoint` classifies
  `unresolvable` because it contains `/` and is cross-repo shaped by
  `_CROSSREPO_RE`). The slug is extracted from the path and the candidate
  `brief:<slug>` is looked up directly in the local node-id set (built from
  `recognize_briefs`, which keys a brief's id on its filename stem — AC-0021).
  If the candidate is a real local node, the value is rewritten to it.
- If neither path resolves a real local brief node, the value is left and
  reported, per the Agent Rule against sweeping a target the corpus cannot
  resolve. No such case exists in the corpus today: all 8 brief targets this
  cohort's 34 specs point at are recognized nodes.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType

_SWEEP_PARENT_INTENT_RELPATH = (
    "docs", "specs", "intent-reference-grammar-migration", "notes",
    "sweep-parent-intent.py",
)
_DEFAULT_STATE_PATH = Path(__file__).resolve().parent / "brief-sweep-state.json"

_FIELD_LABEL = "Brief"

# The repository-relative path form (`docs/product/briefs/<slug>.md`), the
# one shape this corpus's 34 cohort values carry today. `<slug>` matches the
# repository's single-segment identifier rule (AC-0016).
_BRIEF_PATH_RE = re.compile(r"^docs/product/briefs/([A-Za-z0-9_-]+)\.md$")

_TYPED_ID_RE = re.compile(r"[a-z]+:[A-Za-z0-9_-]+")


def _load_sweep_parent_intent(root: Path) -> ModuleType:
    path = root.joinpath(*_SWEEP_PARENT_INTENT_RELPATH)
    spec = importlib.util.spec_from_file_location("_t5_sweep_parent_intent", str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def sweep(root: Path, state_path: Path) -> tuple[int, list[dict], list[dict]]:
    t5 = _load_sweep_parent_intent(root)
    linter = t5._load_linter(root)
    layout = linter.load_layout(root)
    (_g, rollup, local_ids, _brief_paths, _ladder_paths, _intent_paths,
     spec_paths) = t5._recognize_all(linter, root, layout)

    pat = linter.field_re(_FIELD_LABEL)

    state: dict[str, dict] = {}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))

    rewritten: list[dict] = []
    left: list[dict] = []
    edits_by_path: dict[Path, list[tuple[str, str]]] = {}

    for spec_id, path in spec_paths.items():
        text = linter._read(path)
        if text is None:
            continue
        raw: str | None = None
        for line in text.splitlines():
            m = pat.search(line)
            if m:
                raw = m.group(1)
                break
        if raw is None:
            continue  # no `Brief:` header line at all

        token = linter._token(raw)
        if linter._is_placeholder(token):
            continue  # absent/blank/comment/`none` — outside the cohort, AC-0024

        rel = path.relative_to(root).as_posix()

        if _TYPED_ID_RE.fullmatch(token) and token in local_ids:
            state[rel] = {"status": "done", "value": token, "reason": "already-typed"}
            continue

        result_state, _pinned, resolved = linter.resolve_endpoint(token, local_ids, rollup)
        new_value: str | None = None

        if result_state == "local":
            new_value = resolved
        else:
            m2 = _BRIEF_PATH_RE.match(token)
            if m2:
                candidate = f"brief:{m2.group(1)}"
                if candidate in local_ids:
                    new_value = candidate

        entry = {"path": path, "spec_id": spec_id, "raw": raw, "token": token}

        if new_value is not None:
            edits_by_path.setdefault(path, []).append((raw, new_value))
            rewritten.append({**entry, "new_value": new_value})
            state[rel] = {"status": "done", "value": new_value,
                          "reason": f"resolved-{result_state}"}
        else:
            reason = {
                "ambiguous": f"ambiguous — matches {resolved}",
                "unresolvable": "unresolvable — no local brief node for this "
                                "target; leaving per Agent Rule",
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

    # Remainder per AC-0008: every resolvable value that is not `<kind>:<slug>`
    # after this run. Unlike T5's `Parent intent:` cohort, no `Brief:` value in
    # this corpus is deliberately left forever (there is no cross-repo-shaped
    # value that must keep its external-stub edge) — every left entry here is
    # a genuine remainder.
    remainder = list(left)

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

    print(f"sweep-brief: {len(rewritten)} value(s) rewritten, "
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
