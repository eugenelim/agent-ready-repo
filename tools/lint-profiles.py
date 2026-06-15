#!/usr/bin/env python3
"""Lint the catalogue's install profiles (RFC-0034 / spec pack-profiles, T2).

A *profile* is a hand-authored ``profiles/<name>.toml`` listing a single-scope,
deps-first set of packs an adopter installs in one command. This lint enforces
the three author-time invariants RFC-0034 fixes (D5 / §24) against the live
``packs/`` tree:

  1. **Scope-homogeneity** — the profile's declared ``scope`` is in every named
     pack's ``allowed-scopes`` *membership* (not ``default-scope``; the
     ``solution-architect`` packs are dual-scope). A ``scope = "user"`` profile
     naming a repo-only pack, or vice-versa, fails.

  2. **Dependency-completeness** — every required dep of every pack in the
     profile is itself in the profile's pack set, at a catalogue version that
     satisfies the declared ``^X.Y`` range. A dep missing from the set, or
     present at an unsatisfying version, fails.

  3. **Order-validity** — a pack's required dep is listed *earlier* than it
     (deps-first), since the orchestrator installs in authored order.

Adapter-homogeneity is deliberately **not** a lint invariant — RFC-0034 D5
step 2 designs an install-time resolve-once + refuse-and-suggest for adapter
mismatch instead.

Pure-stdlib (no ``agentbundle`` import) so it runs standalone on every OS,
matching the other ``tools/`` lints. The ``^X.Y`` caret-minor grammar mirrors
``agentbundle.commands.install.validate_dependencies_required`` — the canonical
runtime gate — kept in sync by hand (the grammar is frozen).

Usage:
    python tools/lint-profiles.py [--root .]

``--root`` contains ``profiles/`` and ``packs/`` (default: the repo root). A
catalogue with no ``profiles/`` directory lints clean (nothing to check).

Exit codes: 0 = pass, 1 = one or more violations.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]

_CARET_RE = re.compile(r"^\^([0-9]+)\.([0-9]+)$")


def _allowed_scopes(pack_toml: dict) -> list[str]:
    """Resolve a pack's allowed-scopes membership (legacy/v0.1 → ['repo'])."""
    install = pack_toml.get("pack", {}).get("install")
    if isinstance(install, dict):
        scopes = install.get("allowed-scopes")
        if isinstance(scopes, list) and scopes:
            return [s for s in scopes if isinstance(s, str)]
        default = install.get("default-scope")
        if isinstance(default, str):
            return [default]
    return ["repo"]


def _required_deps(pack_toml: dict) -> list[tuple[str, str]]:
    """Return [(dep_pack_name, version_range), ...] from [pack.dependencies.required]."""
    deps = pack_toml.get("pack", {}).get("dependencies", {})
    out: list[tuple[str, str]] = []
    if isinstance(deps, dict):
        for entry in deps.get("required") or []:
            if isinstance(entry, dict):
                out.append((entry.get("pack", ""), entry.get("version", "")))
    return out


def _satisfies(installed_version: str, dep_range: str) -> bool | None:
    """``^X.Y`` caret-minor satisfaction. None ⇒ unsupported range grammar.

    Mirrors ``validate_dependencies_required``: ``A.B.C`` satisfies ``^X.Y``
    when ``A == X`` and version ``>= X.Y.0`` (and ``< (X+1).0.0`` implied).
    """
    m = _CARET_RE.match(dep_range)
    if m is None:
        return None
    req_major, req_minor = int(m.group(1)), int(m.group(2))
    parts = installed_version.split(".")
    try:
        ima = int(parts[0]) if len(parts) > 0 else 0
        imi = int(parts[1]) if len(parts) > 1 else 0
        ipa = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        return False
    return ima == req_major and (imi > req_minor or (imi == req_minor and ipa >= 0))


def _load_packs(packs_dir: Path) -> dict[str, dict]:
    """Map pack name → parsed pack.toml for every packs/<name>/pack.toml."""
    out: dict[str, dict] = {}
    if not packs_dir.is_dir():
        return out
    for pack_dir in sorted(packs_dir.iterdir()):
        toml_path = pack_dir / "pack.toml"
        if not toml_path.exists():
            continue
        try:
            data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError):
            continue
        name = data.get("pack", {}).get("name") or pack_dir.name
        out[name] = data
    return out


def _lint_profile(
    profile_id: str, raw: dict, packs: dict[str, dict]
) -> list[str]:
    """Return a list of violation strings for one parsed profile (empty = clean)."""
    violations: list[str] = []
    scope = raw.get("scope")
    if scope not in ("user", "repo"):
        violations.append(
            f"profile {profile_id!r}: scope must be 'user' or 'repo', got {scope!r}"
        )
    entries = raw.get("packs")
    if not isinstance(entries, list) or not entries:
        violations.append(f"profile {profile_id!r}: 'packs' must be a non-empty list")
        return violations

    names = [e.get("pack") for e in entries if isinstance(e, dict) and e.get("pack")]
    index = {name: i for i, name in enumerate(names)}

    for i, name in enumerate(names):
        pack_toml = packs.get(name)
        if pack_toml is None:
            violations.append(
                f"profile {profile_id!r}: pack {name!r} not found in packs/"
            )
            continue

        # 1. Scope-homogeneity (membership of the declared scope).
        if scope in ("user", "repo"):
            allowed = _allowed_scopes(pack_toml)
            if scope not in allowed:
                violations.append(
                    f"profile {profile_id!r}: pack {name!r} does not allow scope "
                    f"{scope!r} (allowed-scopes: {allowed})"
                )

        # 2 + 3. Dependency-completeness + order-validity.
        for dep_name, dep_range in _required_deps(pack_toml):
            if dep_name not in index:
                violations.append(
                    f"profile {profile_id!r}: pack {name!r} requires {dep_name!r} "
                    f"({dep_range}), which is not in the profile "
                    f"(dependency-incomplete)"
                )
                continue
            if index[dep_name] >= i:
                violations.append(
                    f"profile {profile_id!r}: pack {dep_name!r} (required by "
                    f"{name!r}) is listed at or after it; required deps must come "
                    f"first (mis-ordered)"
                )
            dep_toml = packs.get(dep_name)
            if dep_toml is not None:
                dep_version = dep_toml.get("pack", {}).get("version", "")
                sat = _satisfies(dep_version, dep_range)
                if sat is None:
                    violations.append(
                        f"profile {profile_id!r}: pack {name!r} declares an "
                        f"unsupported version range {dep_range!r} for {dep_name!r} "
                        f"(only ^X.Y is supported)"
                    )
                elif sat is False:
                    violations.append(
                        f"profile {profile_id!r}: pack {name!r} requires "
                        f"{dep_name!r} {dep_range}, but the catalogue ships "
                        f"{dep_name} v{dep_version}, which does not satisfy it "
                        f"(dependency-incomplete)"
                    )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        default=".",
        help="Directory containing profiles/ and packs/ (default: repo root).",
    )
    args = parser.parse_args(argv)
    root = Path(args.root)

    profiles_dir = root / "profiles"
    packs = _load_packs(root / "packs")

    if not profiles_dir.is_dir():
        print("lint-profiles: no profiles/ directory; nothing to lint.")
        return 0

    all_violations: list[str] = []
    checked = 0
    for toml_path in sorted(profiles_dir.glob("*.toml")):
        profile_id = toml_path.stem
        try:
            raw = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError) as exc:
            all_violations.append(f"profile {profile_id!r}: cannot parse: {exc}")
            continue
        checked += 1
        all_violations.extend(_lint_profile(profile_id, raw, packs))

    if all_violations:
        for v in all_violations:
            print(f"lint-profiles: {v}", file=sys.stderr)
        print(
            f"lint-profiles: {len(all_violations)} violation(s) across "
            f"{checked} profile(s).",
            file=sys.stderr,
        )
        return 1

    print(f"lint-profiles: {checked} profile(s) OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
