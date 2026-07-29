#!/usr/bin/env python3
"""Fail-closed export verify (RFC-0059, spec "Export verify honest bounds").

The load-bearing outbound control: after an export, grep the target tree for any
surviving upstream identity anchor. Honest bounds, stated so the guarantee is
not overstated:

  * **case-insensitive** matching,
  * **text files only** (binary artifacts are out of scope — declared),
  * **declared literals only** (not case-folded-split / URL-encoded / base64
    derived forms) after a light normalization pass.

Mode-aware: in `white-label` mode **zero** hits are allowed anywhere; in
`attributed` mode hits are allowed **only** inside the declared attribution
surface (a NOTICE/README credit block). Any other hit is a violation, and the
caller **hard-fails the export** on a non-empty result.

Pure-stdlib; reads the target tree, writes nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

# Extensions we treat as binary and skip (out-of-scope, declared).
BINARY_EXT = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".woff",
    ".woff2", ".pyc", ".so", ".dylib", ".class", ".jar", ".wasm",
})


class Violation:
    __slots__ = ("path", "anchor", "line")

    def __init__(self, path: str, anchor: str, line: int) -> None:
        self.path, self.anchor, self.line = path, anchor, line

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Violation({self.path!r}, {self.anchor!r}, line={self.line})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Violation) and (self.path, self.anchor, self.line) == (
            other.path, other.anchor, other.line)


def _skip_by_ext(p: Path) -> bool:
    return p.suffix.lower() in BINARY_EXT


def _in_attribution(rel: str, allowed: set[str]) -> bool:
    """Exact-file match OR under a listed directory prefix — so an operator can
    list either `legal/NOTICE` or `legal/` and have it work."""
    return any(rel == a or rel.startswith(a.rstrip("/") + "/") for a in allowed)


# GitHub Actions badge URL pattern (owner+repo+/actions/workflows/ form).
_BADGE_RE = re.compile(
    r"https?://[^)\s]*github[^)\s]*/[^)\s]+/[^)\s]+/actions/workflows/",
    re.IGNORECASE,
)

# Dot-directories legitimately projected by adapters into export targets.
# .github is included: .github/workflows/ is caught by check_ci_boundary's
# Check 1 (path-parts), and .github/skills|agents|hooks|instructions/ are
# legitimate Copilot adapter projection paths.
_ALLOWED_DOT_DIRS = frozenset({".claude", ".agents", ".github"})

# Known root-level CI config file names (not directories).
_CI_ROOT_FILES = frozenset({".gitlab-ci.yml", ".travis.yml", "Jenkinsfile"})


def check_ci_boundary(target: Path) -> list[Violation]:
    """Check for CI implementation files in the export output.

    Returns Violations for:
    - Files under .github/workflows/ (GitHub Actions; path-parts, cross-platform)
    - Root-level known CI config files (.gitlab-ci.yml, Jenkinsfile, .travis.yml)
    - Files under a dot-directory not in _ALLOWED_DOT_DIRS (structural
      unknown-provider detection; len(parts) > 1 guard skips root dotfiles)
    - Files containing a GitHub Actions badge URL (all text files)

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

        # Check 1: .github/workflows/ by path parts — cross-platform.
        # str(p.relative_to(target)) is \-separated on Windows; parts[] is safe.
        if len(parts) >= 2 and parts[0] == ".github" and parts[1] == "workflows":
            violations.append(Violation(rel, "ci_path", 0))
            continue

        # Check 2: known root-level CI config files.
        if root in _CI_ROOT_FILES:
            violations.append(Violation(rel, "ci_path", 0))
            continue

        # Check 3: files *under* dot-directories not in the projected-tool allowlist.
        # len(parts) > 1: root-level dotfiles (.gitignore, .editorconfig) are not
        # CI suspects — only files inside an unknown dot-directory are.
        if len(parts) > 1 and root.startswith(".") and root not in _ALLOWED_DOT_DIRS:
            violations.append(Violation(rel, "ci_path", 0))
            continue

        # Check 4: GitHub Actions badge URL in any text file.
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = _BADGE_RE.search(content)
        if m:
            lineno = content[: m.start()].count("\n") + 1
            violations.append(Violation(rel, "ci_badge_url", lineno))

    return violations


def verify(
    target: Path,
    anchors: dict[str, str],
    *,
    mode: str = "white-label",
    attribution_paths: list[str] | None = None,
) -> list[Violation]:
    """Return the anchor hits that violate the mode's policy. Empty ⇒ pass.

    Byte-level, case-insensitive substring search for each declared anchor
    literal (the four anchors are ASCII), skipping only known-binary extensions —
    so a stray NUL never disables scanning of an otherwise-text file. Declared
    literals only: encoded/case-folded-split/base64 forms are out of scope
    (stated bound), and binary artifacts are out of scope by extension."""
    target = Path(target)
    allowed = {str(a) for a in (attribution_paths or [])}
    needles = {
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
            continue  # attributed mode permits anchors only in the notice surface
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
