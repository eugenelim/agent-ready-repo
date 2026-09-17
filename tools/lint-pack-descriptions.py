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

Pure-stdlib, `--root` flagged, exit 0=pass / 1=violation / 2=scanned nothing.

**Why exit 2 exists.** This lint used to print its pass line whenever
`<root>/packs` was absent, so a `--root` aimed at the wrong tree reported
"no pack description has run away" over zero examined manifests — a run that
checked nothing reading identically to a run that checked everything. Both real
invocations (`tools/repo/build_gate_chain.py`, `build-check.yml`) pass a correct
root, so no green run was ever false; it was a latent hole, and it is now
closed rather than left for the first person to pass a wrong `--root`.

The repository had already settled this question twice before this lint caught
up: `tools/lint-adapter-layer-boundary.py` refuses with "this must not pass
vacuously", and `tools/audit-npm.py` treats zero discovered inputs as an error.
Note the two disagree on the code — the former returns 1, the latter 2. This
lint follows `tools/lint-pack-maintainer-emails.py`, its direct sibling and the
lint that was modelled on this file, in using 2, so that "scanned nothing" stays
distinguishable from "found violations".

Usage:
    python3 tools/lint-pack-descriptions.py [--root .]
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

import lint_harness

# The backstop, deliberately set ABOVE the observed range of good copy rather
# than at the edge of it. The marketplace this catalogue is listed alongside
# runs to a 177-character median and a 665-character maximum across 280 plugin
# descriptions; this catalogue's own rewritten set tops out at 263. 800 clears
# both, so a description has to be a genuine outlier — not merely long — to
# trip it. Raising the number is the correct response to a false positive; the
# authoring standard, not this constant, is what makes a description good.
MAX_DESCRIPTION = 800


def _parse(argv: list[str] | None) -> Path:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root", default=".", help="repository root to lint (default: .)"
    )
    return Path(parser.parse_args(argv).root)


def _manifests(root: Path) -> list[Path] | None:
    """Return each pack's ``pack.toml``, or ``None`` when ``packs/`` is absent.

    Fail closed before reporting anything: a pass line printed over zero
    scanned manifests is the defect, not the absence. Both the absent and the
    empty case answer with the same refusal, so the operator's unmet intent —
    "lint this root" — is what the message names either way.
    """
    packs_dir = root / "packs"
    if not packs_dir.is_dir():
        return None
    return sorted(
        pack / "pack.toml" for pack in packs_dir.iterdir()
        if (pack / "pack.toml").is_file()
    )


def _nothing_scanned(root: Path) -> lint_harness.Outcome:
    return lint_harness.Outcome(
        f"lint-pack-descriptions: no pack.toml found under {root / 'packs'} "
        "— scanned nothing, so this is not a pass. Check --root.",
        2,
    )


def find_violations(packs_dir: Path) -> list[str]:
    """Return one message per pack whose description passes the drift backstop.

    A pack with no `pack.toml`, no `[pack].description`, or an unparseable
    `pack.toml` is not this lint's business — the first two are legitimate and
    the third is already reported by schema validation, so re-reporting it here
    would double-count the same defect.

    Kept as a public function over a directory: the self-test drives it
    directly, and callers predate the move onto the shared driver.
    """
    if not packs_dir.is_dir():
        return []
    violations: list[str] = []
    for pack_dir in sorted(packs_dir.iterdir()):
        manifest = pack_dir / "pack.toml"
        if manifest.is_file():
            violations.extend(_runaway(manifest))
    return violations


def _runaway(manifest: Path) -> list[str]:
    """Return the message for one manifest whose description ran away."""
    pack_dir = manifest.parent
    try:
        parsed = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError):
        return []
    description = parsed.get("pack", {}).get("description")
    if not isinstance(description, str) or len(description) <= MAX_DESCRIPTION:
        return []
    return [
        f"lint-pack-descriptions: {pack_dir.name}: [pack].description has "
        f"run away — {len(description)} chars, past the "
        f"{MAX_DESCRIPTION}-char drift backstop. This is display copy a "
        f"person reads while deciding whether to install, so rewrite it "
        f"against catalogue-authoring-standards.md § 2 (lead with the "
        f"adopter outcome; the component list belongs in "
        f"{pack_dir.name}/README.md). Passing this check is not a sign "
        f"the copy is good — only that it is not runaway."
    ]


RULE = lint_harness.Rule(
    parse=_parse,
    files=_manifests,
    predicate=_runaway,
    pass_line=lambda root, n: (
        "lint-pack-descriptions: no pack description has run away (drift backstop "
        "only — the quality bar is catalogue-authoring-standards.md § 2)."
    ),
    empty_scan=_nothing_scanned,
    absent_root=_nothing_scanned,
    summary=lambda n: (
        f"lint-pack-descriptions: {n} pack(s) past the "
        f"{MAX_DESCRIPTION}-char drift backstop."
    ),
)


def main(argv: list[str] | None = None) -> int:
    """Run the drift backstop and return its process exit status."""
    return lint_harness.run(RULE, argv)


if __name__ == "__main__":
    sys.exit(main())
