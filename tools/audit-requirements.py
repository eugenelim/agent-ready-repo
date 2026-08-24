#!/usr/bin/env python3
"""Run `pip-audit` over a requirements file, minus this repo's own packages.

`pip-audit` resolves every pin against the public index so it can walk the
dependency tree. For a first-party pin that is fine right up until a change
raises the floor to the version it is itself releasing — then the audit cannot
resolve it, the required gate fails, and the merge is coupled to the release.
That inverts this repo's order, which is merge first and tag after.

Skipping those pins costs no coverage. Both shipped distributions declare
`dependencies = []`, so a first-party pin contributes no third-party tree to
audit, and `make sast` separately extracts each audited optional group from its
package contract. What is left in each file — the genuinely third-party pins —
is audited exactly as before.

Nothing is dropped silently: every skipped pin is printed with its reason, and a
file whose remainder is empty says so rather than passing quietly.

Usage:
    audit-requirements.py <requirements.txt> [<requirements.txt> ...]
    audit-requirements.py --tools-manifests
    audit-requirements.py --optional-group <name> <pyproject.toml> [...]
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Generous against a measured 7-17s per invocation. The failure this bounds is an
# indefinite CI hang, not a slow audit, so the number only has to be well clear of
# normal.
_PIP_AUDIT_TIMEOUT_S = 300

# Environment variables that can re-point pip-audit's advisory feed, or the pip
# index the resolution venv uses. A stale local export is the realistic trigger,
# not an attacker: either one can produce "No known vulnerabilities found" at
# exit 0 without touching a tracked file.
_SCRUBBED_ENV_PREFIXES = ("PIP_AUDIT_",)
_SCRUBBED_ENV_NAMES = ("PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL")

# requirements-sast.txt has its own direct pip-audit invocation in Makefile,
# where four accepted Semgrep transitive-dependency CVEs are suppressed. Do not
# include it here: removing those suppressions or auditing the file twice would
# respectively regress the accepted allowlist or duplicate SCA findings.
_DIRECT_SAST_MANIFEST = "requirements-sast.txt"


def _scrubbed_env() -> dict[str, str]:
    """os.environ minus the variables that can silently re-aim this gate."""
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(_SCRUBBED_ENV_PREFIXES) and key not in _SCRUBBED_ENV_NAMES
    }


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


def tools_requirements_manifests(tools_dir: Path) -> list[Path]:
    """Return every tools requirements manifest except the direct SAST manifest."""
    return [
        path
        for path in sorted(tools_dir.glob("requirements*.txt"))
        if path.is_file() and not path.is_symlink() and path.name != _DIRECT_SAST_MANIFEST
    ]


# Option lines that pull in dependencies pip-audit would have to resolve. A
# manifest containing only these is NOT "no third-party requirements" — it is a
# manifest whose content lives elsewhere. `--index-url` and friends are excluded
# deliberately: they configure resolution, they do not add a requirement.
_DEPENDENCY_BEARING_OPTIONS = ("-r", "--requirement", "-c", "--constraint",
                               "-e", "--editable", "-f", "--find-links")


def _is_dependency_bearing(stripped: str) -> bool:
    """True when a `-`-prefixed requirements line contributes dependencies.

    Matches on the option token only, so `-r nested.txt`, `--requirement=x.txt`
    and `-e .` all count while `--index-url https://…` does not.
    """
    token = stripped.split("=", 1)[0].split()[0]
    return token in _DEPENDENCY_BEARING_OPTIONS


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
    # A line is content when it is a real pin OR a dependency-bearing option. The
    # old test excluded every `-` line, so a manifest whose only content was
    # `-r nested.txt` / `-c constraints.txt` / `-e .` printed
    # "no third-party requirements to audit" and was audited ZERO times, at
    # exit 0. Latent — no such manifest exists today — but self-test case 4
    # already blesses `-r other.txt` as a supported shape.
    if not any(
        stripped
        and (not stripped.startswith("#"))
        and (not stripped.startswith("-") or _is_dependency_bearing(stripped))
        for stripped in (line.strip() for line in audited)
    ):
        print("  no third-party requirements to audit")
        return 0
    # Write the filtered manifest inside a per-run 0700 directory, not the shared
    # system temp dir. NamedTemporaryFile's own mode was already safe (O_EXCL,
    # 0600); the DIRECTORY was the issue, because a relative `-r` / `-c` /
    # `--find-links` / local-path reference inside a manifest re-resolves against
    # the file's own directory — which was world-writable.
    with tempfile.TemporaryDirectory() as tmpdir:
        temp = Path(tmpdir) / "filtered-requirements.txt"
        temp.write_text("\n".join(audited) + "\n", encoding="utf-8")
        try:
            return subprocess.run(  # noqa: S603
                [
                    sys.executable, "-m", "pip_audit",
                    "-r", str(temp),
                    # A dependency the advisory service cannot serve (a PyPI 404
                    # for that name+version) is otherwise SKIPPED while pip-audit
                    # still exits 0 — the "a silent no-op is not a pass" class
                    # ADR-0084 already gated for bandit. Measured free to adopt:
                    # the nine-manifest audit ran 11.3s with --strict vs 11.1s
                    # without, same input, both green.
                    "--strict",
                    # Pin the advisory source and output shape in code. Without
                    # these, PIP_AUDIT_* environment variables select them, so a
                    # stale shell export could re-point the feed and yield
                    # "No known vulnerabilities found" at exit 0. `-s`, not
                    # `--service`: the long form is `--vulnerability-service`
                    # (pip-audit 2.10.1), and `--service` is not accepted —
                    # verified by invocation, and it is what the first revision of
                    # this change got wrong.
                    "-s", "pypi",
                    "--format", "columns",
                ],
                check=False,
                env=_scrubbed_env(),
                # No timeout meant a pathological pip resolver backtrack hung the
                # gate instead of failing it. Each invocation measures 7-17s.
                timeout=_PIP_AUDIT_TIMEOUT_S,
            ).returncode
        except subprocess.TimeoutExpired:
            print(
                f"audit-requirements: pip-audit exceeded "
                f"{_PIP_AUDIT_TIMEOUT_S}s on {label} — failing the gate rather "
                f"than hanging it",
                file=sys.stderr,
            )
            return 1


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


def optional_dependency_requirements(paths: list[Path], group: str) -> list[str]:
    """Return one declared optional-dependency group from *paths*."""

    requirements: list[str] = []
    for path in paths:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        declared = data.get("project", {}).get("optional-dependencies", {}).get(group)
        if not isinstance(declared, list) or not declared or not all(
            isinstance(item, str) and item.strip() for item in declared
        ):
            raise ValueError(f"{path}: missing or invalid optional-dependency group {group!r}")
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

    if argv == ["--tools-manifests"]:
        paths = tools_requirements_manifests(_REPO_ROOT / "tools")
        if not paths:
            print(
                "audit-requirements: found no tools/requirements*.txt manifests",
                file=sys.stderr,
            )
            return 2
        failed = 0
        for path in paths:
            failed |= audit(path, first_party)
        return 1 if failed else 0

    if argv[0] == "--optional-group":
        if len(argv) < 3:
            print(
                "audit-requirements: --optional-group requires a group and pyproject.toml paths",
                file=sys.stderr,
            )
            return 2
        group = argv[1]
        paths = [Path(raw) for raw in argv[2:]]
        for path in paths:
            if not path.is_file():
                print(f"audit-requirements: no such file: {path}", file=sys.stderr)
                return 2
        try:
            requirements = optional_dependency_requirements(paths, group)
        except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
            print(f"audit-requirements: {exc}", file=sys.stderr)
            return 2
        return audit_lines(f"optional-dependency:{group}", requirements, first_party)

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
