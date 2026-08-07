#!/usr/bin/env python3
"""Repo-policy lint: cap `[pack].description` at an editorially readable length.

A pack's `description` is **display copy**. It is what a person reads in a
marketplace browser or catalogue listing while deciding whether to install, so
what constrains it is how much prose someone will read in a list — not any
tool's ingest limit.

This is deliberately NOT the same ceiling as the per-target
`description-max-length` in `contracts/target-vocab.toml`, which caps *skill and
agent* frontmatter. That text is read by the **model**, which uses it to decide
whether to activate a primitive; length there is load-bearing and shortening it
degrades activation. Two fields named `description`, two audiences, two rules.
Sharing one number would let a target vocabulary that permits a 1024-character
skill description silently permit a 1024-character pack description.

**Why this lives in `tools/` and not in the `agentbundle` package.** Both
`pack.schema.json` and `agentbundle.build.lint_packs` ship inside the published
package and run against *adopter* catalogues (`agentbundle validate`,
`agentbundle catalogue lint`). An editorial house-style rule in either place
would turn this repository's taste into a third party's build break. `tools/`
lints run only on this repository's own `make build-check`, which is the correct
blast radius for a style rule. Pack discoverability is unaffected either way:
that is carried by the separate `[pack].keywords` and `[pack].categories`.

Pure-stdlib, `--root` flagged, exit 0=pass / 1=violation — matching the other
`tools/` lints.

Usage:
    python3 tools/lint-pack-descriptions.py [--root .]
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

# The ceiling. Calibrated against the marketplace this catalogue is listed
# alongside, whose 280 plugin descriptions run to a 177-character median and a
# 665-character maximum. 400 leaves generous room for a two-sentence entry while
# refusing the component-inventory paragraphs this lint was added to stop.
MAX_DESCRIPTION = 400


def find_violations(packs_dir: Path) -> list[str]:
    """Return one message per pack whose description exceeds the ceiling.

    A pack with no `pack.toml`, no `[pack].description`, or an unparseable
    `pack.toml` is not this lint's business — the first two are legitimate and
    the third is already reported by schema validation, so re-reporting it here
    would double-count the same defect.
    """
    violations: list[str] = []
    if not packs_dir.is_dir():
        return violations
    for pack_dir in sorted(packs_dir.iterdir()):
        manifest = pack_dir / "pack.toml"
        if not manifest.is_file():
            continue
        try:
            parsed = tomllib.loads(manifest.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError):
            continue
        description = parsed.get("pack", {}).get("description")
        if not isinstance(description, str):
            continue
        if len(description) > MAX_DESCRIPTION:
            violations.append(
                f"lint-pack-descriptions: {pack_dir.name}: [pack].description is "
                f"{len(description)} chars (max {MAX_DESCRIPTION}). A pack "
                f"description is marketplace display copy — lead with the "
                f"outcome an adopter gets, and move the component list to "
                f"{pack_dir.name}/README.md."
            )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root", default=".", help="repository root to lint (default: .)"
    )
    args = parser.parse_args(argv)

    violations = find_violations(Path(args.root) / "packs")
    for violation in violations:
        print(violation, file=sys.stderr)
    if violations:
        print(
            f"lint-pack-descriptions: {len(violations)} pack(s) over the "
            f"{MAX_DESCRIPTION}-char ceiling.",
            file=sys.stderr,
        )
        return 1
    print("lint-pack-descriptions: all pack descriptions within the ceiling.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
