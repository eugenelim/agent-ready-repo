#!/usr/bin/env python3
"""Derive which recipe selection shapes `init` actually writes.

Constructing a `SelfHostRecipe` by hand and reading `to_dict` proves only what
the dataclass emits for the arguments you chose — it cannot answer what the
state writer passes. The writer records the RESOLVED lists
(`packs=pack_names, profiles=profile_names`), and both selectors widen a falsy
argument to everything the source ships, so an `init` that omits `--profile`
records every profile name rather than an empty list.

This drives real `init_self_hosted` runs and reads the state file off disk.

Run from the repository root:
    python3 docs/specs/catalogue-sync-apply/notes/grounding/derive-recorded-recipe-shapes.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "packages" / "agentbundle"))

from agentbundle.catalogue_tooling.initialise_self_hosted import (  # noqa: E402
    SelfHostedInitConfig,
    init_self_hosted,
)


def make_source(root: Path, packs: list[str], profiles: list[str] | None) -> Path:
    src = root / "src"
    (src / "packs").mkdir(parents=True)
    (src / "catalogue.toml").write_text(
        '[catalogue]\nname = "up"\ndisplay_name = "Up"\ndescription = "d"\n',
        encoding="utf-8",
    )
    for name in packs:
        pack = src / "packs" / name
        pack.mkdir()
        (pack / "pack.toml").write_text(
            f'[pack]\nname = "{name}"\nversion = "1.0.0"\n', encoding="utf-8"
        )
    if profiles is not None:
        (src / "profiles").mkdir()
        for name in profiles:
            (src / "profiles" / f"{name}.toml").write_text(
                f'[profile]\nname = "{name}"\n', encoding="utf-8"
            )
    return src


CASES = [
    ("source ships packs and profiles, no selection flags", ["a", "b"], ["p", "q"], None, None),
    ("source ships both, --pack a", ["a", "b"], ["p", "q"], ["a"], None),
    ("source ships both, --profile p", ["a", "b"], ["p", "q"], None, ["p"]),
    ("source ships NO profiles/ directory", ["a", "b"], None, None, None),
]


def main() -> int:
    print(f"{'case':<52} | recorded packs / profiles")
    print("-" * 96)
    empties = 0
    for label, packs, profiles, sel_packs, sel_profiles in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = make_source(root, packs, profiles)
            target = root / "derived"
            cfg = SelfHostedInitConfig(
                target=target,
                source=src,
                name="derived",
                display_name="Derived",
                description="d",
                owner_name="o",
                owner_email="o@example.invalid",
                packs=sel_packs,
                profiles=sel_profiles,
            )
            init_self_hosted(cfg)
            recipe = json.loads(
                (target / ".agentbundle" / "self-host-state.json").read_text(
                    encoding="utf-8"
                )
            )["recipe"]
            empties += [recipe["packs"], recipe["profiles"]].count([])
            print(f"{label:<52} | {recipe['packs']!r} / {recipe['profiles']!r}")

    print(f"\nempty recorded lists across these cases: {empties}")
    print(
        "an empty list is written only when the source ships no such directory; "
        "it never means 'the adopter selected none', because the selectors widen "
        "a falsy argument to everything the source ships"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
