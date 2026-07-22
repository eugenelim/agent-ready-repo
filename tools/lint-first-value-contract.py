#!/usr/bin/env python3
"""Lint the pack first-value contract (RFC-0064 Amendment #4).

Every pack under `packs/*/pack.toml` must carry a `[pack.first-value]`
section. This lint enforces:

  Level A (required for all packs):
    audience-posture  — one of: "non-technical" | "mixed" | "technical"
    surfaces          — list of strings; ≥ 1 entry; ⊆ [pack.install].allowed-adapters
    prerequisites     — list of strings; each entry ≤ 80 chars
    verification      — string; ≤ 160 chars
    recovery          — string; ≤ 300 chars

  Level B (required when level-b = true):
    starter-task      — string; ≤ 120 chars
    starter-prompt    — string; ≤ 500 chars; no <word> placeholder tokens
    expected-result   — string; ≤ 200 chars
    next-action       — string; ≤ 120 chars

  writes-to-repo gate (required when writes-to-repo = true):
    safety-gate       — string; ≤ 200 chars

  tutorial (enforced only when declared):
    must resolve to an existing .md file (relative to --root)

The Level B membership check uses each pack's own `level-b` field — no
hardcoded pack list.  Discovery is glob-based: packs/*/pack.toml.

Usage:
    python tools/lint-first-value-contract.py [--root .]

Exit codes: 0 = all packs clean, 1 = one or more violations.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover — Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]

_AUDIENCE_POSTURES = frozenset({"non-technical", "mixed", "technical"})
_PLACEHOLDER_RE = re.compile(r"<[a-zA-Z][a-zA-Z0-9 _-]*>")


def _check_pack(pack_path: Path, root: Path) -> list[str]:
    """Return violation strings for one pack (empty = clean)."""
    violations: list[str] = []
    pack_name = pack_path.parent.name

    try:
        data = tomllib.loads(pack_path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError) as exc:
        return [f"{pack_name}: cannot parse pack.toml: {exc}"]

    fv = data.get("pack", {}).get("first-value")
    if fv is None:
        return [f"{pack_name}: [pack.first-value] section missing"]

    def v(msg: str) -> None:
        violations.append(f"{pack_name}: {msg}")

    # ── Level A ──────────────────────────────────────────────────────────────

    ap = fv.get("audience-posture")
    if ap is None:
        v("audience-posture: missing")
    elif ap not in _AUDIENCE_POSTURES:
        v(f"audience-posture: {ap!r} not in {sorted(_AUDIENCE_POSTURES)}")

    surfaces = fv.get("surfaces")
    if surfaces is None:
        v("surfaces: missing")
    elif not isinstance(surfaces, list):
        v("surfaces: must be a list")
    elif len(surfaces) == 0:
        v("surfaces: must have at least one entry")
    else:
        allowed_adapters = (
            data.get("pack", {})
            .get("install", {})
            .get("allowed-adapters")
        )
        if isinstance(allowed_adapters, list):
            for s in surfaces:
                if s not in allowed_adapters:
                    v(f"surfaces: {s!r} not in allowed-adapters {allowed_adapters}")

    prereqs = fv.get("prerequisites")
    if prereqs is None:
        v("prerequisites: missing")
    elif not isinstance(prereqs, list):
        v("prerequisites: must be a list")
    else:
        for i, entry in enumerate(prereqs):
            if isinstance(entry, str) and len(entry) > 80:
                v(f"prerequisites[{i}]: {len(entry)} chars (max 80): {entry!r}")

    verification = fv.get("verification")
    if verification is None:
        v("verification: missing")
    elif not isinstance(verification, str):
        v("verification: must be a string")
    elif len(verification) > 160:
        v(f"verification: {len(verification)} chars (max 160)")

    recovery = fv.get("recovery")
    if recovery is None:
        v("recovery: missing")
    elif not isinstance(recovery, str):
        v("recovery: must be a string")
    elif len(recovery) > 300:
        v(f"recovery: {len(recovery)} chars (max 300)")

    # ── Level B ──────────────────────────────────────────────────────────────

    if fv.get("level-b") is True:
        starter_task = fv.get("starter-task")
        if starter_task is None:
            v("starter-task: missing (required when level-b = true)")
        elif not isinstance(starter_task, str):
            v("starter-task: must be a string")
        elif len(starter_task) > 120:
            v(f"starter-task: {len(starter_task)} chars (max 120)")

        starter_prompt = fv.get("starter-prompt")
        if starter_prompt is None:
            v("starter-prompt: missing (required when level-b = true)")
        elif not isinstance(starter_prompt, str):
            v("starter-prompt: must be a string")
        else:
            if len(starter_prompt) > 500:
                v(f"starter-prompt: {len(starter_prompt)} chars (max 500)")
            m = _PLACEHOLDER_RE.search(starter_prompt)
            if m:
                v(f"starter-prompt: placeholder token {m.group()!r} not allowed")

        expected_result = fv.get("expected-result")
        if expected_result is None:
            v("expected-result: missing (required when level-b = true)")
        elif not isinstance(expected_result, str):
            v("expected-result: must be a string")
        elif len(expected_result) > 200:
            v(f"expected-result: {len(expected_result)} chars (max 200)")

        next_action = fv.get("next-action")
        if next_action is None:
            v("next-action: missing (required when level-b = true)")
        elif not isinstance(next_action, str):
            v("next-action: must be a string")
        elif len(next_action) > 120:
            v(f"next-action: {len(next_action)} chars (max 120)")

    # ── writes-to-repo gate ──────────────────────────────────────────────────

    if fv.get("writes-to-repo") is True:
        safety_gate = fv.get("safety-gate")
        if safety_gate is None:
            v("safety-gate: missing (required when writes-to-repo = true)")
        elif not isinstance(safety_gate, str):
            v("safety-gate: must be a string")
        elif len(safety_gate) > 200:
            v(f"safety-gate: {len(safety_gate)} chars (max 200)")

    # ── tutorial existence (only when declared) ──────────────────────────────

    tutorial = fv.get("tutorial")
    if tutorial is not None:
        tutorial_path = root / tutorial
        if not tutorial_path.is_file():
            v(f"tutorial: {tutorial!r} does not exist (relative to root)")
        elif tutorial_path.suffix != ".md":
            v(f"tutorial: {tutorial!r} must be a .md file (got {tutorial_path.suffix!r})")

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        default=".",
        help="Repo root directory containing packs/ (default: .).",
    )
    args = parser.parse_args(argv)
    root = Path(args.root)
    packs_dir = root / "packs"

    if not packs_dir.is_dir():
        print("lint-first-value-contract: no packs/ directory; nothing to lint.")
        return 0

    all_violations: list[str] = []
    checked = 0
    for pack_toml in sorted(packs_dir.glob("*/pack.toml")):
        checked += 1
        all_violations.extend(_check_pack(pack_toml, root))

    if all_violations:
        for vio in all_violations:
            print(f"lint-first-value-contract: {vio}", file=sys.stderr)
        print(
            f"lint-first-value-contract: {len(all_violations)} violation(s) "
            f"across {checked} pack(s).",
            file=sys.stderr,
        )
        return 1

    print(f"lint-first-value-contract: {checked} pack(s) OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
