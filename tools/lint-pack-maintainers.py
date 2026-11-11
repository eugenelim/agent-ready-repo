#!/usr/bin/env python3
"""Require every shipped pack to name a maintainer in `pack.toml`.

RFC-0104 committed a pack to a named maintainer, a stated maturity scope, and an
archiving path, then recorded that nothing mechanical held it to any of them —
the record itself was the only control. This rule makes the first of the three
checkable.

Scope is deliberately one field. Maturity scope and the archiving path stay
human-reviewed, because neither has a form a lint can judge: a maturity label is
a claim about evidence, and an archiving path is a claim about intent. A
maintainer, by contrast, is present or it is not.

A pack whose directory name starts with `_` is a template or fixture, not a
shipped pack, and is skipped — the same boundary every other pack-scope lint in
this repository draws.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path

import lint_harness

_GATE = "lint-pack-maintainers"


def _parse(argv: list[str] | None) -> Path:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    return Path(parser.parse_args(argv).root).resolve()


def _manifests(root: Path) -> Sequence[Path] | None:
    """Return each shipped pack's manifest, or None when there is no packs/.

    The None return is the driver's absent-root signal and is distinct from an
    empty sequence: a catalogue with no `packs/` has nothing to govern, while
    one holding only `_`-prefixed templates scanned a real directory and found
    no shipped pack.
    """
    packs = root / "packs"
    if not packs.is_dir():
        return None
    return sorted(
        manifest
        for manifest in packs.glob("*/pack.toml")
        if not manifest.parent.name.startswith("_")
    )


def _missing_maintainer(manifest: Path) -> list[str]:
    """Return one finding when the manifest names no usable maintainer.

    `[[pack.maintainers]]` is an array of tables, so an absent key, an empty
    array, and an entry carrying no name are three ways to declare nobody. All
    three read the same to an adopter asking who owns the pack.
    """
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"{manifest.parent.name}: manifest unreadable ({exc})"]

    maintainers = data.get("pack", {}).get("maintainers")
    if not isinstance(maintainers, list) or not maintainers:
        return [f"{manifest.parent.name}: no [[pack.maintainers]] entry"]

    named = [
        entry
        for entry in maintainers
        if isinstance(entry, dict) and str(entry.get("name", "")).strip()
    ]
    if not named:
        return [f"{manifest.parent.name}: [[pack.maintainers]] names nobody"]
    return []


def _report(violations: Sequence[str]) -> None:
    print(f"{_GATE}: packs with no named maintainer:", file=sys.stderr)
    for violation in violations:
        print(f"  {violation}", file=sys.stderr)
    print(
        "\nFix: add a [[pack.maintainers]] entry with a `name` to each pack "
        "above. A pack that nobody owns has no one to notice when its "
        "dependency moves or its guidance goes stale.",
        file=sys.stderr,
    )


_NO_PACKS = lint_harness.Outcome(f"{_GATE}: no packs/ directory — nothing to check", 0, "stdout")
_NO_SHIPPED = lint_harness.Outcome(f"{_GATE}: no shipped packs — nothing to check", 0, "stdout")

RULE = lint_harness.Rule(
    parse=_parse,
    files=_manifests,
    predicate=_missing_maintainer,
    pass_line=lambda root, n: f"{_GATE}: ok — {n} pack(s), each with a named maintainer",
    empty_scan=lambda root: _NO_SHIPPED,
    absent_root=lambda root: _NO_PACKS,
    report=_report,
)


def main(argv: list[str] | None = None) -> int:
    """Run the maintainer lint and return its process exit status."""
    return lint_harness.run(RULE, argv)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    raise SystemExit(main())
