#!/usr/bin/env python3
"""Assert the built site offers `claude plugin install` only for user-capable packs.

The built-output half of docs/specs/claude-plugin-route-scope AC8. Reads the
rendered HTML, not the source: a source check would pass while the gating
conditional is broken, which is the failure this exists to catch.

Runs in `pages.yml`, not the required gate — see the criterion's accepted
residual. Non-blocking by design; the silent-drift half is what blocks merge.

Usage:
    python3 tools/check-site-plugin-offers.py [--build-dir build] [--root .]
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

GATE = "check-site-plugin-offers"
_OFFER = re.compile(r"claude plugin install ([a-z0-9][a-z0-9-]*)@")


def allowed_scopes(meta: dict) -> list[str]:
    pack = meta.get("pack", {})
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build-dir", default="build")
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    root, build = Path(args.root).resolve(), Path(args.build_dir).resolve()

    if not build.is_dir():
        print(f"{GATE}: no build dir at {build} — run the site build first", file=sys.stderr)
        return 1

    capable = {
        d.name for d in (root / "packs").iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "pack.toml").exists()
        and "user" in allowed_scopes(tomllib.loads((d / "pack.toml").read_text(encoding="utf-8")))
    }

    failures, offered = [], set()
    for html in build.rglob("*.html"):
        for slug in _OFFER.findall(html.read_text(encoding="utf-8", errors="replace")):
            offered.add(slug)
            if slug not in capable:
                failures.append(
                    f"{GATE}: {html.relative_to(build)} offers "
                    f"`claude plugin install {slug}@…`, but {slug} is not "
                    f"installable at user scope"
                )
    # The positive half: a user-capable pack's page must still offer it, or the
    # conditional has been inverted rather than removed.
    for slug in sorted(capable):
        # No `page.exists()` guard: lint-site-scope-parity guarantees every
        # pack has a page, so a missing one means the output layout moved — and
        # skipping the assertion there would print `ok` while it was disabled.
        if slug not in offered:
            failures.append(
                f"{GATE}: packs/{slug}/ offers no plugin install command, but "
                f"{slug} is user-capable"
            )

    for line in sorted(set(failures)):
        print(line, file=sys.stderr)
    if failures:
        print(f"{GATE}: FAIL ({len(set(failures))} issue(s))", file=sys.stderr)
        return 1
    print(f"{GATE}: ok — {len(offered)} pack(s) offered, all user-capable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
