#!/usr/bin/env python3
"""Run `pip-audit` over a requirements file, minus this repo's own packages.

`pip-audit` resolves every pin against the public index so it can walk the
dependency tree. For a first-party pin that is fine right up until a change
raises the floor to the version it is itself releasing — then the audit cannot
resolve it, the required gate fails, and the merge is coupled to the release.
That inverts this repo's order, which is merge first and tag after.

Skipping those pins costs no coverage. Both shipped distributions declare
`dependencies = []`, so a first-party pin contributes no third-party tree to
audit, and `make sast` already audits the one optional extra either package can
pull. What is left in each file — the genuinely third-party pins — is audited
exactly as before.

Nothing is dropped silently: every skipped pin is printed with its reason, and a
file whose remainder is empty says so rather than passing quietly.

Usage:
    audit-requirements.py <requirements.txt> [<requirements.txt> ...]
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_REPO_ROOT = Path(__file__).resolve().parents[1]

# A requirement line's distribution name: everything before the first extras
# bracket, version specifier, marker, or whitespace.
_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _canonical(name: str) -> str:
    """PEP 503 normalisation, so `python_slugify` and `python-slugify` match."""
    return re.sub(r"[-_.]+", "-", name).lower()


def first_party_names(root: Path) -> set[str]:
    """Distribution names built from this repository, read from pyproject."""
    names: set[str] = set()
    for pyproject in sorted((root / "packages").glob("*/pyproject.toml")):
        for line in pyproject.read_text(encoding="utf-8").splitlines():
            match = re.match(r'^\s*name\s*=\s*"([^"]+)"', line)
            if match:
                names.add(_canonical(match.group(1)))
                break
    return names


def partition(lines: list[str], first_party: set[str]) -> tuple[list[str], list[str]]:
    """Split into (audited, skipped-first-party).

    Comments, blank lines and pip options travel with the audited half so the
    file pip-audit sees stays as close to the original as possible.
    """
    audited: list[str] = []
    skipped: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "-")):
            audited.append(line)
            continue
        match = _NAME.match(stripped)
        if match and _canonical(match.group(1)) in first_party:
            skipped.append(stripped)
        else:
            audited.append(line)
    return audited, skipped


def audit_lines(label: str, lines: list[str], first_party: set[str]) -> int:
    """Audit requirement *lines* after applying the first-party filter."""
    audited, skipped = partition(lines, first_party)
    print(f"pip-audit -r {label}")
    for pin in skipped:
        print(f"  skipped (built in this repo, declares no dependencies): {pin}")
    if not any(
        line.strip() and not line.strip().startswith(("#", "-")) for line in audited
    ):
        print("  no third-party requirements to audit")
        return 0
    with tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8"
    ) as handle:
        handle.write("\n".join(audited) + "\n")
        temp = Path(handle.name)
    try:
        return subprocess.run(  # noqa: S603
            [sys.executable, "-m", "pip_audit", "-r", str(temp)], check=False
        ).returncode
    finally:
        temp.unlink(missing_ok=True)


def audit(path: Path, first_party: set[str]) -> int:
    """Audit one requirements file."""
    return audit_lines(
        str(path), path.read_text(encoding="utf-8").splitlines(), first_party
    )


def build_system_requirements(paths: list[Path]) -> list[str]:
    """Return declared PEP 517 backend requirements from *paths*.

    Missing or malformed ``build-system.requires`` is a gate configuration
    error: silently auditing an empty set would leave the build backend outside
    SCA while reporting success.
    """
    requirements: list[str] = []
    for path in paths:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        declared = data.get("build-system", {}).get("requires")
        if not isinstance(declared, list) or not declared or not all(
            isinstance(item, str) and item.strip() for item in declared
        ):
            raise ValueError(f"{path}: missing or invalid build-system.requires")
        requirements.extend(declared)
    return requirements


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: audit-requirements.py <requirements.txt> ...", file=sys.stderr)
        return 2
    first_party = first_party_names(_REPO_ROOT)
    if not first_party:
        # Fail closed: an empty set would silently audit nothing differently,
        # but it also means the discovery broke and nobody would notice.
        print(
            "audit-requirements: found no first-party package names under "
            "packages/*/pyproject.toml — refusing to run with broken discovery",
            file=sys.stderr,
        )
        return 2
    if argv[0] == "--build-system":
        paths = [Path(raw) for raw in argv[1:]]
        if not paths:
            print(
                "audit-requirements: --build-system requires pyproject.toml paths",
                file=sys.stderr,
            )
            return 2
        for path in paths:
            if not path.is_file():
                print(f"audit-requirements: no such file: {path}", file=sys.stderr)
                return 2
        try:
            requirements = build_system_requirements(paths)
        except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
            print(f"audit-requirements: {exc}", file=sys.stderr)
            return 2
        return audit_lines("build-system-requirements", requirements, first_party)

    failed = 0
    for raw in argv:
        path = Path(raw)
        if not path.is_file():
            print(f"audit-requirements: no such file: {path}", file=sys.stderr)
            return 2
        failed |= audit(path, first_party)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
