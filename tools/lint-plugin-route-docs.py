#!/usr/bin/env python3
"""Assert install-route documentation does not make false catalogue claims.

Per-site `(path, pattern, expected)` rather than one repo-wide grep, because the
plugin-route sites do not share a pattern — `README.md` writes `claude plugin
install`, several guides write `/plugin install`, and two files name the
dist-tree path `<output>/claude-plugins/core/…`. A single `! grep -q 'claude
plugin install'` would pass green on most of them. The retired-pack guard is
the exception: it scans every guide because the false install claim could be
introduced anywhere in the adopter-facing tree.

Each entry also asserts its file **exists**, so a rename is not a silent pass —
the failure mode of every absence-only check.

The `forbidden` patterns are literal substrings; `required` ones pin the
canonical statement so the precondition cannot quietly vanish.

Usage:
    python tools/lint-plugin-route-docs.py [--root .]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

GATE = "lint-plugin-route-docs"

# A repo-only pack must never be named as the subject of a plugin install.
#
# Literal rather than derived because `SITES` below is built at import time,
# before `--root` is known. `tools/test-lint-plugin-route-docs.py` compares
# this tuple against `packs/*/pack.toml` on every run, so a pack narrowing its
# scopes reddens there — the drift this list could otherwise carry silently
# while a doc kept offering the pack.
REPO_ONLY = ("core", "governance-extras", "iac-terraform", "monorepo-extras",
             "release-engineering", "user-guide-diataxis", "catalogue-curation")


# Both spellings. A doc may write either; a site constrained for only one is
# green while it regresses in the other — which is how five sites shipped with
# an empty `forbidden` list and no assertion against a regression at all.
def _offers(pack: str) -> list[str]:
    return [f"claude plugin install {pack}@", f"/plugin install {pack}@"]


_NO_REPO_ONLY_OFFER = [pat for p in REPO_ONLY for pat in _offers(p)]

# `research` was renamed to `desk-research`. Keep command detection separate
# from pack-argument detection: `--pack` may appear after the catalogue URI,
# while the legacy positional spelling appeared immediately after `install`.
# The explicit bounds treat hyphens as part of an id, unlike ``\b``.
_INSTALL_COMMAND_RE = re.compile(r"\bagentbundle\s+install\b")
_RETIRED_PACK_FLAG_RE = re.compile(
    r"--pack(?:\s+|=)(?<![A-Za-z0-9_-])research(?![A-Za-z0-9_-])"
)
_RETIRED_LEGACY_PACK_RE = re.compile(
    r"\bagentbundle\s+install\s+(?<![A-Za-z0-9_-])research(?![A-Za-z0-9_-])"
)

SITES: list[tuple[str, list[str], list[str]]] = [
    # (path, forbidden substrings, required substrings)
    ("README.md", _NO_REPO_ONLY_OFFER, ["user-scope"]),
    # The prose enumerates the repo-only set by name. Pin each slug so widening
    # a pack — which `lint-plugin-roster` already forces you to notice — also
    # forces the prose, rather than leaving it silently wrong.
    # "all N packs" is the shape the enumeration missed once already: a count
    # that silently re-asserts whole-catalogue coverage without naming a pack.
    ("docs-site/src/content/docs/getting-started/install.md",
     _NO_REPO_ONLY_OFFER + ["all 20 packs", "all 21 packs", "for all packs"],
     ["Repo-scoped packs"] + [f"`{p}`" for p in REPO_ONLY if p != "catalogue-curation"]),
    # Two entries: the route-table row and the marker-writer paragraph are
    # separate claims, and pinning one string that lives in both means deleting
    # either is green.
    ("guides/_shared/explanation/install-routes.md",
     _NO_REPO_ONLY_OFFER,
     ["**Carries only packs whose `allowed-scopes` admits `user`**"]),
    ("guides/_shared/explanation/install-routes.md",
     [], ["The plugin route is user-scope only",
          "derived into each **published** pack's"]
        + [f"`{p}`" for p in REPO_ONLY if p != "catalogue-curation"]),
    ("guides/_shared/explanation/pack-catalogue.md",
     _NO_REPO_ONLY_OFFER, ["install-routes.md"]),
    ("guides/core/how-to/adapt-to-project.md",
     _NO_REPO_ONLY_OFFER, ["repo-scoped"]),
    (".github/workflows/publish-claude-plugins.yml",
     ["so adopters can install any pack with"] + _NO_REPO_ONLY_OFFER,
     ["user-scope"]),
    ("tools/hooks/README.md", _NO_REPO_ONLY_OFFER,
     ["`claude-plugins/core/` subtree"]),
    ("packs/core/.apm/hook-wiring/session-start.toml", _NO_REPO_ONLY_OFFER,
     ["There is no `claude-plugins/core/` dist-tree copy"]),
]


def _offers_retired_research_install(line: str) -> bool:
    """Return whether one line offers either retired ``research`` install form."""

    return bool(_INSTALL_COMMAND_RE.search(line)) and bool(
        _RETIRED_PACK_FLAG_RE.search(line) or _RETIRED_LEGACY_PACK_RE.search(line)
    )


def _retired_guide_install_failures(root: Path) -> list[str]:
    """Return guide diagnostics for the retired ``research`` pack install form."""

    guides_root = root / "guides"
    if not guides_root.is_dir():
        return []

    failures: list[str] = []
    for path in sorted(guides_root.rglob("*.md")):
        body = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(body.splitlines(), start=1):
            if _offers_retired_research_install(line):
                failures.append(
                    f"{GATE}: {path.relative_to(root)}:{line_number} offers retired "
                    "pack id `research`; use `desk-research`"
                )
    return failures


def check(root: Path) -> list[str]:
    failures: list[str] = []
    for rel, forbidden, required in SITES:
        path = root / rel
        if not path.is_file():
            failures.append(
                f"{GATE}: {rel} does not exist — this list is stale, or a site "
                f"was renamed and its assertion silently stopped running"
            )
            continue
        body = path.read_text(encoding="utf-8", errors="replace")
        for pat in forbidden:
            if pat in body:
                failures.append(
                    f"{GATE}: {rel} contains {pat!r} — that pack cannot be "
                    f"installed by the user-scope plugin route"
                )
        for pat in required:
            if pat not in body:
                failures.append(
                    f"{GATE}: {rel} is missing {pat!r} — the scope precondition "
                    f"is stated once and referenced; this reference is gone"
                )
    failures.extend(_retired_guide_install_failures(root))
    return failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    failures = check(Path(args.root).resolve())
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(f"{GATE}: FAIL ({len(failures)} issue(s))", file=sys.stderr)
        return 1
    print(f"{GATE}: ok — {len(SITES)} site(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
