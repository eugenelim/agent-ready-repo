#!/usr/bin/env python3
"""Repo-policy lint: a runaway-drift backstop on `[pack].description`.

**This lint is not the quality bar, and cannot be.** The authoring standard is —
`guides/_shared/reference/catalogue-authoring-standards.md` § 2. A pack
description fails review when it opens on a component inventory, leans on
repo-insider vocabulary, references sibling packs, name-drops frameworks, or
cites internal paths. None of those is a length, so no length check detects any
of them: a 799-character component inventory passes this lint and is still
wrong, and a rich 900-character description would fail it while being fine.

What this catches is the one thing that *is* objective — a field that has run
away. It reached 1122 characters here before anything governed it, at which
point no reviewer was reading it as display copy any more. The ceiling is set
deliberately loose (see `MAX_DESCRIPTION`) so it only ever fires on an outlier,
never on a judgment call. Treat a failure as "this drifted", not "this is bad
copy"; treat passing as nothing at all.

This is deliberately NOT the per-target `description-max-length` in
`contracts/target-vocab.toml`, which caps *skill and agent* frontmatter. That
text is read by the **model** to decide whether to activate a primitive; length
there is load-bearing and shortening it degrades activation. Two fields named
`description`, two audiences, two rules. Sharing one number would let a target
vocabulary that permits a 1024-character skill description silently permit a
1024-character pack description.

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

# The backstop, deliberately set ABOVE the observed range of good copy rather
# than at the edge of it. The marketplace this catalogue is listed alongside
# runs to a 177-character median and a 665-character maximum across 280 plugin
# descriptions; this catalogue's own rewritten set tops out at 263. 800 clears
# both, so a description has to be a genuine outlier — not merely long — to
# trip it. Raising the number is the correct response to a false positive; the
# authoring standard, not this constant, is what makes a description good.
MAX_DESCRIPTION = 800


def find_violations(packs_dir: Path) -> list[str]:
    """Return one message per pack whose description passes the drift backstop.

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
                f"lint-pack-descriptions: {pack_dir.name}: [pack].description has "
                f"run away — {len(description)} chars, past the "
                f"{MAX_DESCRIPTION}-char drift backstop. This is display copy a "
                f"person reads while deciding whether to install, so rewrite it "
                f"against catalogue-authoring-standards.md § 2 (lead with the "
                f"adopter outcome; the component list belongs in "
                f"{pack_dir.name}/README.md). Passing this check is not a sign "
                f"the copy is good — only that it is not runaway."
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
            f"lint-pack-descriptions: {len(violations)} pack(s) past the "
            f"{MAX_DESCRIPTION}-char drift backstop.",
            file=sys.stderr,
        )
        return 1
    print(
        "lint-pack-descriptions: no pack description has run away (drift backstop "
        "only — the quality bar is catalogue-authoring-standards.md § 2)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
