#!/usr/bin/env python3
"""Refuse a built artifact that carries test content.

RFC-0082 / ADR-0075: `packages/<pkg>/<pkg>/` is the engine's runtime export
boundary. A wheel or zipapp that regains a test tree should fail the release
build, not be caught by whoever happens to read the diff.

Usage: python3 tools/check-artifact-contents.py <artifact> [<artifact> ...]

Accepts `.whl` and `.pyz` — both are zip archives, so one reader covers them.
Exits 1 and prints the offending entries to stderr when any artifact carries
test content; exits 0 otherwise.

**The sdist is deliberately out of scope.** Its rule is the inverse — it should
carry the engine suite, complete and runnable — and that half lands with the
catalogue carve-out spec, which grows this script a presence mode. Asserting
absence here would reject the carve-out's correct artifact.

Why not `check-wheel-contents` or `pydistcheck`: this repo's rule is that new
`tools/` scripts are pure-stdlib Python, and both were measured against the real
artifacts first. `check-wheel-contents`' test-name check (W005) applies only at
the library toplevel and never fires on a nested tree. `pydistcheck` can detect
it, but only via `--expected-files`; its natural-reading `--expected-directories`
form passes while the property is violated, because setuptools wheels carry no
directory entries. Transcripts: docs/rfc/0082-notes/enforcement-tool-trials.md.
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

# A `tests`/`test` path component, or a test-shaped module at any depth.
_TEST_ENTRY = re.compile(
    r"(^|/)tests?(/|$)"                     # a tests/ or test/ component
    r"|(^|/)(test_[^/]*|[^/]*_test|conftest)\.py$"  # pytest's default python_files
)

# The bundled catalogue scaffold is inert template material: it ships in the
# wheel by design (pyproject `package-data`) and is never collected or executed
# here. Without this carve-out the carve-out spec's scaffold test template would
# turn an already-released gate red on a correct artifact.
#
# Anchored at the top-level package's own `_data/`. An unanchored match would
# exempt e.g. `pkg/build/tests/_data/catalogue-scaffold/test_p.py` — a real
# test tree inside the importable package, whitelisted by a directory name
# appearing further down the path.
_EXEMPT = re.compile(r"^[^/]+/_data/catalogue-scaffold/")


def offending_entries(artifact: Path) -> list[str]:
    """Return the test-content entries in *artifact*, sorted."""
    with zipfile.ZipFile(artifact) as zf:
        names = zf.namelist()
    return sorted(
        n for n in names if _TEST_ENTRY.search(n) and not _EXEMPT.search(n)
    )


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            f"usage: {argv[0]} <artifact.whl|artifact.pyz> [...]",
            file=sys.stderr,
        )
        return 2

    failed = False
    for raw in argv[1:]:
        artifact = Path(raw)
        if artifact.suffix not in (".whl", ".pyz"):
            print(
                f"check-artifact-contents: {artifact.name}: expected .whl or "
                ".pyz (the sdist is deliberately not checked here)",
                file=sys.stderr,
            )
            return 2
        entries = offending_entries(artifact)
        if entries:
            failed = True
            print(
                f"check-artifact-contents: {artifact.name} carries "
                f"{len(entries)} test entr{'y' if len(entries) == 1 else 'ies'}:",
                file=sys.stderr,
            )
            for e in entries:
                print(f"  {e}", file=sys.stderr)
        else:
            print(f"check-artifact-contents: {artifact.name} clean")

    if failed:
        print(
            "check-artifact-contents: tests must not ship in an installed "
            "artifact (RFC-0082). Move them out of the importable package.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
