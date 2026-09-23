#!/usr/bin/env python3
"""Probe: which recorded recipe shapes widen the selection to every source pack?

Clause 1 of the write-set definition unions the recorded recipe's selection
with any name a scoping flag introduces. `select_packs` reads a falsy
`explicit` argument as "no narrowing requested" and returns every pack the
source ships, so an empty list and `None` are indistinguishable to it. On phase
2's read-only path that produces a wrong plan; on an apply path it would write
every pack the source ships into the adopter's tree.

Walks all nine shapes the recorded `packs` and `profiles` can take, rather than
the subset that happens to behave.

Run from the repository root:
    python3 docs/specs/catalogue-sync-apply/notes/grounding/probe-empty-recipe-widening.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "packages" / "agentbundle"))

from agentbundle.catalogue_tooling import initialise_self_hosted as ish  # noqa: E402
from agentbundle.commands.catalogue_sync import _underivable_condition  # noqa: E402

ABSENT = object()
PACKS = ("alpha", "beta", "gamma")


def build(root: Path) -> Path:
    src = root / "source"
    (src / "packs").mkdir(parents=True)
    (src / "profiles").mkdir()
    (src / "catalogue.toml").write_text(
        '[catalogue]\nname = "up"\ndisplay_name = "Up"\ndescription = "d"\n',
        encoding="utf-8",
    )
    for name in PACKS:
        pack = src / "packs" / name
        pack.mkdir()
        (pack / "pack.toml").write_text(
            f'[pack]\nname = "{name}"\nversion = "1.0.0"\n', encoding="utf-8"
        )
    (src / "profiles" / "p.toml").write_text('[profile]\nname = "p"\n', encoding="utf-8")
    return src


def main() -> int:
    widened = 0
    print(f"{'packs':>10} {'profiles':>10} | {'underivable?':>36} | resolves to")
    print("-" * 94)
    for packs in (ABSENT, [], ["alpha"]):
        for profiles in (ABSENT, [], ["p"]):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                src = build(root)
                target = root / "derived"
                (target / ".agentbundle").mkdir(parents=True)
                recipe: dict = {}
                if packs is not ABSENT:
                    recipe["packs"] = packs
                if profiles is not ABSENT:
                    recipe["profiles"] = profiles
                state = {
                    "schema_version": "3",
                    "managed_paths": [],
                    "recipe": recipe,
                    "pin": {},
                }
                (target / ".agentbundle" / "self-host-state.json").write_text(
                    json.dumps(state), encoding="utf-8"
                )
                condition = _underivable_condition(target, src)
                loaded = ish._load_self_host_recipe(state, src, [])
                resolved = ish.select_packs(src, loaded.packs if loaded else None)
                is_wide = len(resolved) == len(PACKS) and condition is None
                widened += is_wide
                pl = "absent" if packs is ABSENT else repr(packs)
                fl = "absent" if profiles is ABSENT else repr(profiles)
                mark = "  <-- WIDENS" if is_wide else ""
                print(
                    f"{pl:>10} {fl:>10} | {str(condition)[:36]:>36} | "
                    f"{resolved}{mark}"
                )
    print(f"\nshapes that widen with no refusal: {widened} of 9")
    print(
        "the existing underivable check fires only when packs and profiles are "
        "both absent"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
