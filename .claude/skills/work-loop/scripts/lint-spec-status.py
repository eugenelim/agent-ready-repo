#!/usr/bin/env python3
"""Spec *metadata* drift lint.

This is a `work-loop` **skill script**: it lives at
`packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` and projects to
every adapter's `.../skills/work-loop/scripts/`, the same way `loop-cohort.py`
does. The agent runs it at the work-loop's finish-time checklist — *available
and agent-invoked, not fail-closed* (there is no PR-open hook event in an
adopter repo). It no-ops gracefully where Python is absent.

It can also run as a **fail-closed CI gate** where a PR event and Python both
exist. Do NOT wire it into the projected `pre-pr` hook body: that body projects
to adopter trees and would mis-fire — the finish-time skill checklist and a CI
gate are the two invocation surfaces. (An earlier design shipped this as a
standalone linter; it now ships as a skill script so it projects to adopters
too.)

It checks five invariants over `docs/specs/*/spec.md`, measured against the
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
  (iii) dangling intra-repo references — both **doc** references (markdown
        links to local `.md` paths) and, since v1.1, repo-relative **code**
        references (full paths rooted at a known top-level dir or an explicit
        relative link, ending in `.py`/`.toml`/`.sh`/`.json`, locator suffix
        stripped) that don't resolve to a file. WARN-ONLY (never changes the
        exit code); promoting it to a hard invariant stays deferred pending
        the observed warn rate.
  (iv)  deferral anchors resolve — every real `(deferred: <slug>)` marker
        resolves to a heading anchor in `docs/backlog.md`. HARD (exit non-zero).
  (v)   spec↔contract traceability — a spec's
        `- **Contract:**` header (forward ref) names contract file(s) under
        `contracts/<type>/`; each must exist and carry a backward pointer — an
        `x-spec` extension (OpenAPI/AsyncAPI YAML/JSON) or a `contracts/REGISTRY.md`
        row (extensionless formats). WARN-ONLY (never changes the exit code;
        mirrors invariant (iii)). No-ops where the spec names no contract
        (non-API features: empty / "none" / the template placeholder) or no
        `contracts/` tree exists — the common case in repos with no API surface.

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
# Backticked span: `…` — the dominant carrier of code references in specs.
_BACKTICK_RE = re.compile(r"`([^`]+)`")
# Invariant (iii) v1.1: repo-relative *code* references. A reference is only
# resolvable if it's a full repo-relative path — rooted at a known top-level
# directory (or an explicit ../ / ./ relative link target) and ending in a
# recognised code extension. Bare basenames, placeholders, and globs are out.
_CODE_ROOTS = ("packages/", "tools/", "packs/", "apps/", "docs/", ".github/")
_CODE_EXTS = (".py", ".toml", ".sh", ".json")
# Header contract line (invariant v), e.g. `- **Contract:** `contracts/openapi/orders.yaml``.
_CONTRACT_HEADER_RE = re.compile(r"\*\*Contract:\*\*\s*(.+?)\s*$")
# A repo-relative contract path token under the `contracts/` tree.
_CONTRACT_TOKEN_RE = re.compile(r"contracts/[A-Za-z0-9._/-]+")
# Vendor-extension-bearing contract formats (carry `x-spec` inline); other
# formats (e.g. .proto, .graphql) use the REGISTRY.md back-ref channel.
_XSPEC_FORMATS = (".yaml", ".yml", ".json")
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


def _candidate_code_path(token: str) -> str | None:
    """Return the repo-relative code path from a raw reference token, or None
    if the token is not a full repo-relative code reference (invariant iii v1.1).

    Accepts: contains `/`, ends in a recognised code extension (after stripping
    a trailing `:<line>` / `:<range>` / `#<anchor>` locator), and is either
    rooted at a known top-level directory or an explicit `../` / `./` relative
    link target. Rejects bare basenames, placeholders (`<>`), globs (`*`),
    and prose ellipses (`...`).
    """
    # Reject placeholders (`<>`), globs (`*`), brace-expansion shorthand
    # (`{a,b}.py`), and prose ellipses (`...`, e.g. an abbreviated path like
    # `packs/core/...session-start.toml`) — none denote a single literal path.
    if (any(c in token for c in "<>*{}") or "://" in token
            or "..." in token or "/" not in token):
        return None
    path: str | None = None
    for ext in _CODE_EXTS:
        idx = token.find(ext)
        if idx == -1:
            continue
        end = idx + len(ext)
        rest = token[end:]
        # The extension must terminate the path or be followed only by a
        # locator (`:` line/range or `#` anchor) — so `.python` won't match `.py`.
        if rest == "" or rest[0] in ":#":
            path = token[:end]
            break
    if path is None:
        return None
    if not (path.startswith(_CODE_ROOTS) or path.startswith(("../", "./"))):
        return None
    return path


def code_references(text: str) -> list[tuple[int, str]]:
    """Yield (lineno, repo-relative path) for full repo-relative code
    references in backticked spans or markdown links. De-duplicated per path
    so a file referenced many times warns once."""
    out: list[tuple[int, str]] = []
    seen: set[str] = set()
    for lineno, line in enumerate(text.splitlines(), start=1):
        tokens = [m.group(1) for m in _BACKTICK_RE.finditer(line)]
        tokens += [m.group(1) for m in _LINK_RE.finditer(line)]
        for tok in tokens:
            path = _candidate_code_path(tok.strip())
            if path is not None and path not in seen:
                seen.add(path)
                out.append((lineno, path))
    return out


def contract_header_refs(spec_text: str) -> list[tuple[int, str]]:
    """Return (lineno, contract-path) for each `contracts/...` token on the
    spec's `- **Contract:**` header line. Returns [] for a non-API feature —
    an empty value, `none`, or the template placeholder (an HTML comment)."""
    for lineno, line in enumerate(spec_text.splitlines(), start=1):
        m = _CONTRACT_HEADER_RE.search(line)
        if not m:
            continue
        value = m.group(1).strip()
        if not value or value.lower() == "none" or value.startswith("<!--"):
            return []
        return [(lineno, tm.group(0)) for tm in _CONTRACT_TOKEN_RE.finditer(value)]
    return []


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
        # `git` may be unavailable on PATH; fall through to the
        # script-relative root, which is the intended fallback.
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

        # (iii) dangling intra-repo references (warn-only) — doc links (.md)
        # and, since v1.1, repo-relative code references.
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
        for lineno, path in code_references(text):
            candidates = [spec_path.parent / path, root / path]
            if not any(c.is_file() for c in candidates):
                warn.append(
                    f"{rel}:{lineno}: invariant (iii) — code reference '{path}' "
                    f"does not resolve (warn-only)"
                )

        # (v) spec↔contract traceability (warn-only). Forward `Contract:` header
        # must point at an existing contract carrying a backward ref. No-ops when
        # the spec names no contract (non-API) or no `contracts/` tree exists.
        contract_refs = contract_header_refs(text)
        if contract_refs:
            feature_dir = spec_path.parent.relative_to(root).as_posix()
            registry_path = root / "contracts" / "REGISTRY.md"
            registry_text = (
                registry_path.read_text(encoding="utf-8", errors="replace")
                if registry_path.is_file()
                else ""
            )
            for lineno, token in contract_refs:
                contract_file = root / token
                if not contract_file.is_file():
                    warn.append(
                        f"{rel}:{lineno}: invariant (v) — Contract: '{token}' does "
                        f"not resolve to a file (warn-only)"
                    )
                    continue
                backward = False
                if token.endswith(_XSPEC_FORMATS):
                    ctext = contract_file.read_text(encoding="utf-8", errors="replace")
                    backward = "x-spec" in ctext and feature_dir in ctext
                if not backward:
                    backward = token in registry_text and feature_dir in registry_text
                if not backward:
                    warn.append(
                        f"{rel}:{lineno}: invariant (v) — contract '{token}' lacks a "
                        f"backward x-spec/REGISTRY.md ref to {feature_dir} (warn-only)"
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
