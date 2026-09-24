#!/usr/bin/env python3
"""Probe: which recorded selection values widen to everything the source ships?

`_read_recipe_selection` collapses EVERY value that is not a list of shipped
names to `None`, and both `select_packs` and `_select_profiles` read a falsy
`explicit` argument as "no narrowing requested" and return everything. So a
recorded selection that fails its own read-time constraint fails OPEN.

Two axes matter and both are easy to get wrong:

* **Value type and validity**, not presence and emptiness. A selection carrying
  one name the source does not ship reads as a well-formed non-empty list and
  is the sharp case; a presence-and-emptiness sweep reports it as covered.
* **Both selection fields.** `packs` and `profiles` carry the identical
  widening, so a packs-only sweep prices half the criterion.

The field under test is varied while the other field is held at a valid value,
so the underivable check fires for the value under test rather than for an
unrelated absence.

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
VALID = "<a name the source ships>"
PACKS = ("alpha", "beta", "gamma")
PROFILES = ("p", "q")

CASES: list[tuple[object, str, str]] = [
    (ABSENT, "absent", "presence"),
    ([], "empty list", "presence"),
    ([VALID], "valid non-empty list", "presence"),
    (None, "explicit null", "type"),
    ("", "empty string", "type"),
    ("alpha", "bare string", "type"),
    ({}, "empty object", "type"),
    ({"a": 1}, "object", "type"),
    (0, "zero", "type"),
    (42, "int", "type"),
    (True, "bool", "type"),
    ([1, 2], "list of non-strings", "type"),
    ([""], "list of empty string", "validity"),
    ([VALID, "nope"], "one name the source does not ship", "validity"),
    (["nope"], "no name the source ships", "validity"),
    ([VALID, VALID], "duplicate shipped name", "validity"),
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
    for name in PROFILES:
        (src / "profiles" / f"{name}.toml").write_text(
            f'[profile]\nname = "{name}"\n', encoding="utf-8"
        )
    return src


def concrete(value: object, shipped: str) -> object:
    if isinstance(value, list):
        return [shipped if item == VALID else item for item in value]
    return value


def main() -> int:
    widened: list[str] = []
    print(f"{'field':>8} {'axis':>9} {'recorded value':>34} | {'refused?':>8} | resolves to")
    print("-" * 104)
    for field, shipped, whole, other in (
        ("packs", PACKS[0], PACKS, ("profiles", [PROFILES[0]])),
        ("profiles", PROFILES[0], PROFILES, ("packs", [PACKS[0]])),
    ):
        for value, label, axis in CASES:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                src = build(root)
                target = root / "derived"
                (target / ".agentbundle").mkdir(parents=True)
                # Hold the sibling field valid so a refusal is attributable to
                # the value under test.
                recipe: dict = {other[0]: other[1]}
                if value is not ABSENT:
                    recipe[field] = concrete(value, shipped)
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
                if field == "packs":
                    resolved = ish.select_packs(
                        src, loaded.packs if loaded else None
                    )
                else:
                    resolved = ish._select_profiles(
                        src, loaded.profiles if loaded else None
                    )
                is_wide = len(resolved) == len(whole) and condition is None
                if is_wide:
                    widened.append(f"{field}:{label}")
                mark = "  <-- WIDENS" if is_wide else ""
                refused = "no" if condition is None else "yes"
                print(
                    f"{field:>8} {axis:>9} {label:>34} | {refused:>8} | "
                    f"{resolved}{mark}"
                )

    print(f"\nwidens with no refusal: {len(widened)} of {len(CASES) * 2}")
    print("only a valid, non-empty list of shipped names narrows the selection")
    print(
        "the sharp case is a selection that fails its own read-time constraint: "
        "it reads as a well-formed non-empty list and widens rather than refusing"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
