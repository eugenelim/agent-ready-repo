#!/usr/bin/env python3
"""Claude-plugin route membership tripwire.

Asserts that every marketplace the repo publishes lists exactly the packs whose
`[pack.install] allowed-scopes` admits `"user"`.

**Why this is a lint and not a pytest.** `make build-check` — the only required
status check on `main`, and the only one that sees both `web/**` and
`packs/**/pack.toml` edits — runs no pytest, and in `build-check.yml` the make
step executes before pytest is installed. A membership assertion living in the
test suite would never run in the gate that blocks merge.

**What turning red here means.** After
docs/specs/claude-plugin-route-scope, widening a pack's `allowed-scopes` to
include `"user"` is a decision to publish that pack's code to a public
marketplace, not a metadata tweak. If this gate fails because a pack you widened
is now listed, that is the gate working. Regenerate with `make build-self` and
make sure publishing it is what you meant — see the spec's `Ask first` boundary.

Stdlib-only and self-contained: `tools/` scripts must run from a clean checkout
with no `agentbundle` on the path. The scope resolver below is a deliberate
mirror of `commands/validate.py:_allowed_scopes`, kept in sync by
`tools/test-lint-plugin-membership.py`.

Usage:
    python tools/lint-plugin-membership.py [--root .]
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

GATE = "lint-plugin-membership"


def allowed_scopes(pack_meta: dict) -> list[str]:
    """Mirror of ``commands/validate.py:_allowed_scopes``.

    The gate is ``[pack.adapter-contract].version``, **not** ``[pack.install]``:
    a pack declaring ``allowed-scopes`` with no contract version resolves
    ``["repo"]``.
    """
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


def publishable(packs_dir: Path) -> set[str]:
    """The derived set: non-underscore slug, both manifests, user-admitting."""
    names: set[str] = set()
    if not packs_dir.is_dir():
        return names
    for pack_dir in sorted(packs_dir.iterdir()):
        if not pack_dir.is_dir() or pack_dir.name.startswith("_"):
            continue
        pack_toml = pack_dir / "pack.toml"
        if not pack_toml.exists():
            continue
        if not (pack_dir / ".claude-plugin" / "plugin.json").exists():
            continue
        meta = tomllib.loads(pack_toml.read_text(encoding="utf-8"))
        if "user" in allowed_scopes(meta):
            names.add(pack_dir.name)
    return names


def listed(marketplace: Path) -> set[str]:
    if not marketplace.exists():
        return set()
    payload = json.loads(marketplace.read_text(encoding="utf-8"))
    return {p.get("name") for p in payload.get("plugins", []) if p.get("name")}


def check(root: Path) -> list[str]:
    """Return failure strings; empty means pass."""
    expected = publishable(root / "packs")
    failures: list[str] = []

    root_marketplace = root / ".claude-plugin" / "marketplace.json"
    if not root_marketplace.exists():
        # Vacuously green is the failure shape this gate exists to prevent:
        # a missing marketplace must not read as "nothing to check" while the
        # dist branch keeps publishing.
        if expected:
            failures.append(
                f"{GATE}: .claude-plugin/marketplace.json is missing, but "
                f"{len(expected)} pack(s) are publishable — run `make build-self`"
            )
    else:
        actual = listed(root_marketplace)
        # Both directions: extras are the fail-open bug this gate exists for,
        # and missing entries are the fail-closed truncation only equality
        # catches.
        for name in sorted(actual - expected):
            failures.append(
                f"{GATE}: .claude-plugin/marketplace.json lists {name!r}, whose "
                f"allowed-scopes does not admit 'user' — the route installs at "
                f"user scope and cannot honour it"
            )
        for name in sorted(expected - actual):
            failures.append(
                f"{GATE}: .claude-plugin/marketplace.json is missing {name!r}, "
                f"which is publishable — run `make build-self`"
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
        print(
            f"{GATE}: FAIL ({len(failures)} issue(s)). Widening a pack's "
            "allowed-scopes publishes its code to a public marketplace — see "
            "docs/specs/claude-plugin-route-scope § Ask first.",
            file=sys.stderr,
        )
        return 1
    print(f"{GATE}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
