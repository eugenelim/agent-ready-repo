#!/usr/bin/env python3
"""Probe: which recorded recipe selections widen to every pack the source ships?

Clause 1 of the write-set definition unions the recorded recipe's selection
with any name a scoping flag introduces. Two shipped behaviours compose badly:
`_read_recipe_selection` collapses EVERY value that is not a list of shipped
names to `None`, and `select_packs` reads a falsy `explicit` argument as "no
narrowing requested" and returns every pack the source ships. A recorded
selection that fails its own read-time constraint therefore fails OPEN.

The axis that matters is value TYPE and VALIDITY, not presence and emptiness:
branching on presence alone reports four well-behaved shapes and hides the
validation-failure case, which is the sharp one. On phase 2's read-only path
this produced a wrong plan; on an apply path it writes every pack the source
ships into an adopter tree that recorded fewer, under a consent prompt taken
against the widened plan.

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

CASES: list[tuple[object, str, str]] = [
    (ABSENT, "absent", "presence"),
    ([], "empty list", "presence"),
    (["alpha"], "valid non-empty list", "presence"),
    (None, "explicit null", "type"),
    ("", "empty string", "type"),
    ("alpha", "bare string", "type"),
    ({}, "empty object", "type"),
    ({"a": 1}, "object", "type"),
    (0, "zero", "type"),
    (42, "int", "type"),
    (True, "bool", "type"),
    ([1, 2], "list of ints", "type"),
    ([""], "list of empty string", "validity"),
    (["alpha", "nope"], "one name the source does not ship", "validity"),
    (["nope"], "no name the source ships", "validity"),
    (["alpha", "alpha"], "duplicate shipped name", "validity"),
]


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
    return src


def main() -> int:
    widened: list[str] = []
    print(f"{'axis':>9} {'recorded packs':>34} | {'refused?':>9} | resolves to")
    print("-" * 96)
    for value, label, axis in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = build(root)
            target = root / "derived"
            (target / ".agentbundle").mkdir(parents=True)
            recipe: dict = {"profiles": []}
            if value is not ABSENT:
                recipe["packs"] = value
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
            if is_wide:
                widened.append(label)
            mark = "  <-- WIDENS" if is_wide else ""
            refused = "no" if condition is None else "yes"
            print(f"{axis:>9} {label:>34} | {refused:>9} | {resolved}{mark}")

    print(f"\nwidens with no refusal: {len(widened)} of {len(CASES)}")
    print("only a valid, non-empty list of shipped names narrows the selection")
    print(
        "the validity axis is the sharp one: a recorded selection that fails its "
        "own read-time constraint widens rather than refusing"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
