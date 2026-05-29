#!/usr/bin/env python3
"""Catalogue-governance lint for spec *metadata* drift (RFC-0016, Tier 1).

This linter is **catalogue-internal**. It has no `packs/` source and does
not project to adopters — adopters get the same invariants through
construction (the new-spec template) and judgment (the `adversarial-reviewer`
"Spec drift" check + the work-loop finish-time checklist). It runs only from
the Makefile `build-check` target, where Python + CI are both present. Do NOT
wire it into `tools/hooks/pre-pr.py`; that hook projects to adopter trees and
would then call a script they don't have.

It checks four invariants over `docs/specs/*/spec.md`, measured against the
contract pinned in `CONVENTIONS.md` § 4 (Spec metadata contract). Only the
header `- **Status:**` field is checked; `plan.md` status is out of v1 scope.

  (i)   status vocabulary — the leading status token is one of
        {Draft, Approved, Implementing, Shipped, Archived}. The token is the
        first word after `Status:`, truncated at the first ` (`, ` →`, or
        `<!--`, so annotated Frozen statuses like `Shipped (2026-05-26)` and
        `Approved → Shipped (…)` pass. HARD (exit non-zero).
  (ii)  ACs at the ship transition (diff-triggered) — a spec whose header
        status *changes to* `Shipped` in the diff against the base ref must
        have every Acceptance Criterion `[x]` or carrying `(deferred: <anchor>)`.
        Specs already `Shipped` on the base are grandfathered. If no base ref
        resolves, the invariant is skipped with a warning. HARD when it runs.
  (iii) dangling intra-repo doc references — markdown links to local `.md`
        paths that don't exist. WARN-ONLY (doc-refs only in v1; code paths
        deferred to v1.1 per RFC-0016).
  (iv)  deferral anchors resolve — every real `(deferred: <slug>)` marker
        resolves to a heading anchor in `docs/backlog.md`. HARD (exit non-zero).

Exit codes: 0 = clean (warnings allowed), 1 = one or more HARD violations.
Usage: lint-spec-status.py [--root DIR] [--base-ref REF]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

CANONICAL_STATUSES: frozenset[str] = frozenset(
    {"Draft", "Approved", "Implementing", "Shipped", "Archived"}
)

# Header status line, e.g. `- **Status:** Shipped (2026-05-26)`.
_STATUS_RE = re.compile(r"\*\*Status:\*\*\s*(.+?)\s*$")
# A real deferral marker carries a slug anchor — NOT the template
# placeholder `(deferred: <anchor>)`, whose `<…>` form is excluded by the
# leading-alphanumeric class.
_DEFERRED_RE = re.compile(r"\(deferred:\s*([A-Za-z0-9][A-Za-z0-9._\-]*)\s*\)")
# Markdown inline link target: [text](target)
_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
# Markdown heading line.
_HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")
# AC checklist items.
_AC_OPEN_RE = re.compile(r"^\s*-\s*\[ \]\s")
_AC_DONE_RE = re.compile(r"^\s*-\s*\[[xX]\]\s")


def extract_status_token(raw: str) -> str:
    """Return the leading status token from a header status value.

    Truncates at the first ` (`, ` →`, or `<!--` so annotated Frozen
    statuses (`Shipped (date)`, `Approved → Shipped (…)`,
    `Draft <!-- ... -->`) reduce to their leading word.
    """
    text = raw
    for delim in (" (", " →", "<!--"):
        idx = text.find(delim)
        if idx != -1:
            text = text[:idx]
    return text.strip().split()[0] if text.strip() else ""


def parse_status(spec_text: str) -> str | None:
    """Return the leading status token from a spec's header, or None."""
    for line in spec_text.splitlines():
        m = _STATUS_RE.search(line)
        if m:
            return extract_status_token(m.group(1))
    return None


def slugify(heading: str) -> str:
    """GitHub-style heading anchor slug: lowercase, drop punctuation
    other than spaces/hyphens, spaces → hyphens."""
    text = heading.strip().lower()
    # Strip inline markdown emphasis/code markers before slugging.
    text = text.replace("`", "")
    text = re.sub(r"[^\w\s-]", "", text)
    # GitHub does NOT collapse consecutive hyphens: a stripped `/` between
    # two spaces yields a double hyphen (`a / b` → `a--b`). Match that —
    # only spaces become hyphens; existing/produced hyphen runs are kept.
    return text.replace(" ", "-")


def backlog_anchors(backlog_text: str) -> set[str]:
    anchors: set[str] = set()
    for line in backlog_text.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            anchors.add(slugify(m.group(1)))
    return anchors


def deferred_anchors(spec_text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for lineno, line in enumerate(spec_text.splitlines(), start=1):
        for m in _DEFERRED_RE.finditer(line):
            out.append((lineno, m.group(1)))
    return out


def acceptance_criteria_lines(spec_text: str) -> list[tuple[int, str]]:
    """Return (lineno, line) for every checklist item inside the
    `## Acceptance Criteria` section."""
    lines = spec_text.splitlines()
    out: list[tuple[int, str]] = []
    in_ac = False
    for lineno, line in enumerate(lines, start=1):
        if re.match(r"^##\s+Acceptance Criteria\b", line):
            in_ac = True
            continue
        if in_ac and re.match(r"^##\s+", line):
            break
        if in_ac and (_AC_OPEN_RE.match(line) or _AC_DONE_RE.match(line)):
            out.append((lineno, line))
    return out


def resolve_default_base_ref(root: Path) -> str | None:
    """Resolve the diff base ref, preferring `origin/<default-branch>`."""
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "origin/HEAD"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return None  # git not installed
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    # Fall back to origin/main if it exists.
    r = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", "origin/main"],
        capture_output=True, text=True, check=False,
    )
    return "origin/main" if r.returncode == 0 else None


def base_spec_text(root: Path, relpath: str, base_ref: str) -> str | None:
    """Return the spec's content at `base_ref`, or None if absent/unresolvable."""
    r = subprocess.run(
        ["git", "-C", str(root), "show", f"{base_ref}:{relpath}"],
        capture_output=True, text=True, errors="replace", check=False,
    )
    return r.stdout if r.returncode == 0 else None


def _repo_root() -> Path:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except FileNotFoundError:
        pass
    return Path(__file__).resolve().parent.parent


def check(root: Path, base_ref: str | None) -> tuple[list[str], list[str]]:
    """Return (hard_violations, warnings)."""
    hard: list[str] = []
    warn: list[str] = []

    backlog_path = root / "docs" / "backlog.md"
    anchors = (
        backlog_anchors(backlog_path.read_text(encoding="utf-8", errors="replace"))
        if backlog_path.is_file()
        else set()
    )

    base_resolvable = base_ref is not None
    if not base_resolvable:
        warn.append(
            "invariant (ii): no base ref resolvable — ship-transition AC check "
            "skipped (shallow clone / detached HEAD)"
        )

    specs_dir = root / "docs" / "specs"
    for spec_path in sorted(specs_dir.glob("*/spec.md")):
        rel = spec_path.relative_to(root).as_posix()
        text = spec_path.read_text(encoding="utf-8", errors="replace")

        # (i) status vocabulary
        token = parse_status(text)
        if token is None:
            hard.append(f"{rel}: no `- **Status:**` header field found")
        elif token not in CANONICAL_STATUSES:
            hard.append(
                f"{rel}: invariant (i) — status '{token}' not in "
                f"{{{', '.join(sorted(CANONICAL_STATUSES))}}}"
            )

        # (iv) deferral anchors resolve
        for lineno, anchor in deferred_anchors(text):
            if anchor not in anchors:
                hard.append(
                    f"{rel}:{lineno}: invariant (iv) — (deferred: {anchor}) "
                    f"does not resolve to a heading in docs/backlog.md"
                )

        # (ii) ACs at the ship transition (diff-triggered)
        if base_resolvable and token == "Shipped":
            base_text = base_spec_text(root, rel, base_ref)  # type: ignore[arg-type]
            base_token = parse_status(base_text) if base_text is not None else None
            transitioned = base_token != "Shipped"  # incl. new spec (None)
            if transitioned:
                for lineno, line in acceptance_criteria_lines(text):
                    if _AC_OPEN_RE.match(line) and not _DEFERRED_RE.search(line):
                        hard.append(
                            f"{rel}:{lineno}: invariant (ii) — spec moved to "
                            f"Shipped but AC is unchecked and not deferred"
                        )

        # (iii) dangling intra-repo doc references (warn-only)
        for lineno, line in enumerate(text.splitlines(), start=1):
            for m in _LINK_RE.finditer(line):
                target = m.group(1).split("#", 1)[0].strip()
                if not target or "://" in target or not target.endswith(".md"):
                    continue
                # A link may be spec-relative or repo-root-relative; warn only
                # if it resolves under neither.
                candidates = [spec_path.parent / target, root / target]
                if not any(c.is_file() for c in candidates):
                    warn.append(
                        f"{rel}:{lineno}: invariant (iii) — doc link '{target}' "
                        f"does not resolve (warn-only)"
                    )

    return hard, warn


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--base-ref", default=None)
    args = parser.parse_args(argv)

    root = args.root.resolve() if args.root else _repo_root()
    base_ref = args.base_ref if args.base_ref else resolve_default_base_ref(root)

    hard, warn = check(root, base_ref)

    for w in warn:
        print(f"lint-spec-status: warning: {w}", file=sys.stderr)
    if hard:
        for v in hard:
            print(f"lint-spec-status: {v}", file=sys.stderr)
        print(
            f"lint-spec-status: {len(hard)} hard violation(s).", file=sys.stderr
        )
        return 1
    print("lint-spec-status: spec metadata clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
