"""Fail-closed identity and CI-boundary verification for catalogue init.

Migrated from packs/catalogue-curation/.apm/skills/export-catalogue/scripts/export_verify.py
and extended for use by the self-hosted init engine.

Two entry points:

  verify(target, anchors, *, mode, attribution_paths) → list[Violation]
    Scans text files in *target* for surviving identity anchor literals.
    Empty result means the mode's policy is satisfied.

  check_ci_boundary(target) → list[Violation]
    Scans *target* for CI implementation files (workflows, badges, unknown
    dot-directories) that must not travel to derivative catalogues.

Both are byte-level, case-insensitive, declared-literals-only — binary files
are skipped by extension; encoded / case-folded-split forms are out of scope.

Python 3.11 stdlib only.  No network, no subprocess, no third-party deps.
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = [
    "Violation",
    "verify",
    "check_ci_boundary",
    "BINARY_EXT",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Extensions treated as binary and skipped (out-of-scope, declared).
BINARY_EXT: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".woff",
    ".woff2", ".pyc", ".so", ".dylib", ".class", ".jar", ".wasm",
})

# Dot-directories legitimately projected by adapters or agentbundle infrastructure.
# .github included: .github/workflows/ is caught by check_ci_boundary check 1
# (path-parts), and .github/skills|agents|hooks|instructions/ are legitimate
# Copilot adapter projection paths.
# .agentbundle included: agentbundle infrastructure directory (state, vendored tooling).
_ALLOWED_DOT_DIRS: frozenset[str] = frozenset({".claude", ".agents", ".github", ".agentbundle"})

# Known root-level CI config file names.
_CI_ROOT_FILES: frozenset[str] = frozenset({".gitlab-ci.yml", ".travis.yml", "Jenkinsfile"})

# GitHub Actions badge URL pattern (owner+repo+/actions/workflows/ form).
_BADGE_RE: re.Pattern[str] = re.compile(
    r"https?://[^)\s]*github[^)\s]*/[^)\s]+/[^)\s]+/actions/workflows/",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Violation
# ---------------------------------------------------------------------------

class Violation:
    """A single identity or CI-boundary hit inside the target tree."""

    __slots__ = ("path", "anchor", "line")

    def __init__(self, path: str, anchor: str, line: int) -> None:
        self.path = path
        self.anchor = anchor
        self.line = line

    def __repr__(self) -> str:  # pragma: no cover
        return f"Violation({self.path!r}, {self.anchor!r}, line={self.line})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Violation):
            return NotImplemented
        return (self.path, self.anchor, self.line) == (other.path, other.anchor, other.line)

    def __hash__(self) -> int:
        return hash((self.path, self.anchor, self.line))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _skip_by_ext(p: Path) -> bool:
    return p.suffix.lower() in BINARY_EXT


def _in_attribution(rel: str, allowed: set[str]) -> bool:
    """True when *rel* is an exact match or under a listed directory prefix."""
    return any(rel == a or rel.startswith(a.rstrip("/") + "/") for a in allowed)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def verify(
    target: Path,
    anchors: dict[str, str],
    *,
    mode: str = "white-label",
    attribution_paths: list[str] | None = None,
) -> list[Violation]:
    """Return anchor hits that violate *mode*'s policy.  Empty list ⇒ pass.

    Scans all non-binary files under *target* for each anchor literal in
    *anchors* (a dict of {anchor_name: literal_value}).  Search is byte-level
    and case-insensitive; only declared literals are checked.

    Modes:
      "white-label" — zero hits allowed anywhere.
      "attributed"  — hits allowed only inside *attribution_paths* files/dirs.

    Never persists bearer tokens; anchors must be stripped of credentials
    before passing to this function.
    """
    target = Path(target)
    allowed: set[str] = {str(a) for a in (attribution_paths or [])}
    needles: dict[str, bytes] = {
        name: val.lower().encode("utf-8", "surrogatepass")
        for name, val in anchors.items()
        if val
    }
    violations: list[Violation] = []
    for p in sorted(target.rglob("*")):
        if not p.is_file() or _skip_by_ext(p):
            continue
        rel = str(p.relative_to(target))
        if mode == "attributed" and _in_attribution(rel, allowed):
            continue
        try:
            blob = p.read_bytes().lower()
        except OSError:
            continue
        for name, needle in needles.items():
            idx = blob.find(needle)
            if idx != -1:
                lineno = blob.count(b"\n", 0, idx) + 1
                violations.append(Violation(rel, name, lineno))
    return violations


def check_ci_boundary(target: Path) -> list[Violation]:
    """Return violations for CI implementation files found in *target*.

    Checks:
    1. Files under .github/workflows/ (path-parts, cross-platform).
    2. Root-level known CI config files (.gitlab-ci.yml, Jenkinsfile, .travis.yml).
    3. Files under a dot-directory not in _ALLOWED_DOT_DIRS (structural unknown-
       provider detection; only files *inside* a dot-dir, not root dotfiles).
    4. Files containing a GitHub Actions badge URL.

    Does NOT flag .github/skills/, .github/agents/, .github/hooks/, or
    .github/instructions/ — legitimate Copilot adapter projection paths.
    """
    target = Path(target)
    violations: list[Violation] = []
    for p in sorted(target.rglob("*")):
        if not p.is_file() or _skip_by_ext(p):
            continue
        rel = str(p.relative_to(target))
        parts = Path(rel).parts
        root = parts[0] if parts else ""

        # Check 1: .github/workflows/ by path parts.
        if len(parts) >= 2 and parts[0] == ".github" and parts[1] == "workflows":
            violations.append(Violation(rel, "ci_path", 0))
            continue

        # Check 2: known root-level CI config files.
        if root in _CI_ROOT_FILES:
            violations.append(Violation(rel, "ci_path", 0))
            continue

        # Check 3: files inside unknown dot-directories.
        if len(parts) > 1 and root.startswith(".") and root not in _ALLOWED_DOT_DIRS:
            violations.append(Violation(rel, "ci_path", 0))
            continue

        # Check 4: GitHub Actions badge URL.
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = _BADGE_RE.search(content)
        if m:
            lineno = content[: m.start()].count("\n") + 1
            violations.append(Violation(rel, "ci_badge_url", lineno))

    return violations
