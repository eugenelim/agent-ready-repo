#!/usr/bin/env python3
"""Site user-capability parity: `web/src/content/packs/*.md` vs `packs/*/pack.toml`.

`web/src/content/packs/*.md` are hand-authored — `tools/build-site.py` feeds
`docs-site/`, not `web/` — so the `pluginInstallable` field on each page is a
copy of a value that lives in `pack.toml`. This gate is what keeps the copy
honest. Without it the site can advertise `claude plugin install` for a pack
whose `allowed-scopes` forbids user scope, indefinitely and silently.

Note `scope` is *not* the field to gate on: it mirrors `default-scope`, so
`product-documentation` (`default-scope = "repo"`, `allowed-scopes =
["repo", "user"]`) would be wrongly hidden.

Iterates the **union** of both sides over non-`_`-prefixed slugs, so a pack
added on either side alone is caught rather than skipped.

Runs in `make build-check` — the only required, path-unfiltered gate, and the
only one that sees both a `web/**` edit and a `packs/**/pack.toml` edit. The
built-output half of this check lives in `pages.yml`; see
docs/specs/claude-plugin-route-scope AC8 for why it is not here.

Usage:
    python tools/lint-site-scope-parity.py [--root .]
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

GATE = "lint-site-scope-parity"
_FIELD = re.compile(r"^pluginInstallable:\s*(true|false)\s*$", re.M)


def allowed_scopes(pack_meta: dict) -> list[str]:
    """Mirror of ``commands/validate.py:_allowed_scopes`` (stdlib-only tool)."""
    pack = pack_meta.get("pack", {})
    if not isinstance(pack, dict):
        return ["repo"]
    contract = pack.get("adapter-contract")
    version = contract.get("version") if isinstance(contract, dict) else None
    if version is None or version == "0.1":
        return ["repo"]
    install = pack.get("install", {})
    if not isinstance(install, dict):
        return ["repo"]
    declared = install.get("allowed-scopes")
    if isinstance(declared, list) and declared:
        return [s for s in declared if isinstance(s, str)]
    default = install.get("default-scope")
    return [default] if isinstance(default, str) else ["repo"]


def check(root: Path) -> list[str]:
    packs_dir, pages_dir = root / "packs", root / "web" / "src" / "content" / "packs"
    if not pages_dir.is_dir():
        return []  # no site in this checkout — nothing to keep in parity

    pack_slugs = {
        d.name for d in packs_dir.iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "pack.toml").exists()
    } if packs_dir.is_dir() else set()
    page_slugs = {p.stem for p in pages_dir.glob("*.md") if not p.stem.startswith("_")}

    failures: list[str] = []
    for slug in sorted(pack_slugs | page_slugs):
        page = pages_dir / f"{slug}.md"
        if slug not in page_slugs:
            failures.append(f"{GATE}: packs/{slug}/ has no web/src/content/packs/{slug}.md")
            continue
        if slug not in pack_slugs:
            failures.append(f"{GATE}: web/src/content/packs/{slug}.md has no packs/{slug}/")
            continue
        match = _FIELD.search(page.read_text(encoding="utf-8"))
        if match is None:
            failures.append(
                f"{GATE}: {slug}.md has no `pluginInstallable` field — it is "
                "required with no default so an omission cannot silently "
                "advertise the plugin route"
            )
            continue
        declared = match.group(1) == "true"
        meta = tomllib.loads((packs_dir / slug / "pack.toml").read_text(encoding="utf-8"))
        actual = "user" in allowed_scopes(meta)
        if declared != actual:
            failures.append(
                f"{GATE}: {slug}.md says pluginInstallable: {str(declared).lower()} "
                f"but packs/{slug}/pack.toml resolves "
                f"allowed-scopes={allowed_scopes(meta)!r} "
                f"(user-capable: {str(actual).lower()})"
            )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    failures = check(Path(args.root).resolve())
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(f"{GATE}: FAIL ({len(failures)} issue(s))", file=sys.stderr)
        return 1
    print(f"{GATE}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
