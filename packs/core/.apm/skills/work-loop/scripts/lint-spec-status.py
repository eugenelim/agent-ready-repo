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
        resolves against `workspace.toml [backlog].open` slug fields.
        HARD (exit non-zero).
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

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

CANONICAL_STATUSES: frozenset[str] = frozenset(
    {"Draft", "Approved", "Implementing", "Shipped", "Archived"}
)

# Header status line, e.g. `- **Status:** Shipped (2026-05-26)`.
_STATUS_RE = re.compile(r"\*\*Status:\*\*\s*(.+?)\s*$")
# ATX section heading at level ≥2: 0–3 optional spaces, two or more #, then
# a space/tab or end-of-line.  CommonMark (spec §4.2) allows up to three
# leading spaces before the opening #s; four spaces would be a code block.
_SECTION_HEADING_RE = re.compile(r"^ {0,3}#{2,}(?:[ \t]|$)")
# HTML comment span (including multiline).  Applied to the full spec text
# before line iteration so that a commented-out status like:
#   <!--
#   - **Status:** Approved
#   -->
# does not satisfy a lifecycle guard ahead of the real active field.
# re.DOTALL lets the pattern cross newlines.
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
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
# Segments may not be `.` or `..`: the token is joined onto `--root` and read,
# so a permissive class containing `.` and `/` let `contracts/../../secret.json`
# escape the tree. `_within()` at the join site is the actual control; this
# rejects the traversal earlier so the warning text stays honest. Each segment
# must therefore start with an alphanumeric.
_CONTRACT_SEGMENT = r"[A-Za-z0-9][A-Za-z0-9._-]*"
_CONTRACT_TOKEN_RE = re.compile(rf"contracts/(?:{_CONTRACT_SEGMENT}/)*{_CONTRACT_SEGMENT}")
# Vendor-extension-bearing contract formats (carry `x-spec` inline); other
# formats (e.g. .proto, .graphql) use the REGISTRY.md back-ref channel.
_XSPEC_FORMATS = (".yaml", ".yml", ".json")
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
    """Return the leading status token from a spec's metadata preamble, or None.

    Stops at the first second-level heading (## …) so body text that contains
    **Status:** in examples, task descriptions, or quoted templates cannot
    accidentally satisfy a lifecycle guard.
    """
    # Strip HTML comments from the full text first.  Per-line stripping does
    # not remove multiline comments, so an interior `- **Status:** Approved`
    # inside a block comment would be returned before the live status field.
    cleaned = _HTML_COMMENT_RE.sub("", spec_text)
    for line in cleaned.splitlines():
        if _SECTION_HEADING_RE.match(line):
            break  # preamble ends at the first section heading
        if line.lstrip().startswith("#"):
            continue  # skip ATX heading lines — Status must not live in a heading
        m = _STATUS_RE.search(line)
        if m:
            return extract_status_token(m.group(1))
    return None


def _regex_backlog_slugs(workspace_text: str) -> set[str]:
    """Extract [backlog].open slugs from workspace.toml text via regex fallback.

    Used when tomllib/tomli is unavailable or the TOML is malformed.
    Scans for slug = "..." lines within the [backlog] section only.
    """
    slugs: set[str] = set()
    in_backlog = False
    for line in workspace_text.splitlines():
        if re.match(r"^\s*\[backlog\]", line):
            in_backlog = True
        elif re.match(r"^\s*\[", line) and "[backlog]" not in line:
            in_backlog = False
        if in_backlog:
            m = re.search(r'\bslug\s*=\s*"([^"]+)"', line)
            if m:
                slugs.add(m.group(1))
    return slugs


def backlog_open_slugs(workspace_path: Path) -> set[str]:
    """Return the set of slugs from workspace.toml [backlog].open.

    Uses tomllib (Python 3.11+ stdlib) or tomli (backport) when available;
    falls back to regex for all other cases including malformed TOML.
    Returns an empty set when workspace.toml is absent.
    """
    if not workspace_path.is_file():
        return set()
    text = workspace_path.read_text(encoding="utf-8", errors="replace")
    try:
        try:
            import tomllib  # type: ignore[import]
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[import,no-redef]
            except ImportError:
                return _regex_backlog_slugs(text)
        data = tomllib.loads(text)
        return {
            e["slug"]
            for e in data.get("backlog", {}).get("open", [])
            if isinstance(e, dict) and "slug" in e
        }
    except ValueError:
        return _regex_backlog_slugs(text)


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
    `## Acceptance Criteria` section.

    The heading match is case-INSENSITIVE, and that is the whole point. It was
    case-sensitive, so a spec whose heading read `## Acceptance criteria`
    collected zero criteria and its AC-completeness invariant passed
    *vacuously* — the check reported success on a spec it had not read. That
    silently un-gated 18 specs before it was noticed, and the number only grows,
    because nothing tells an author which casing the linter wants.

    A vacuous pass is the worst failure mode a gate has: it is indistinguishable
    from a real one at the call site.
    """
    lines = spec_text.splitlines()
    out: list[tuple[int, str]] = []
    in_ac = False
    for lineno, line in enumerate(lines, start=1):
        if re.match(r"^##\s+Acceptance Criteria\b", line, re.IGNORECASE):
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


# Skip implausibly large files — an untrusted repo could ship a multi-GB
# spec.md or contract; reading it whole is a memory-exhaustion DoS. Mirrors
# lint-traceability.py's guard of the same name.
_MAX_FILE_BYTES = 8 * 1024 * 1024


def _read(path: Path) -> str | None:
    """Size-guarded read. Returns None when the file is too large or unreadable."""
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _within(path: Path, root: Path) -> bool:
    """True when `path` is inside `root` after symlink resolution.

    Ported from lint-traceability.py, which has carried this confinement since
    it was written. This file did not, and that was a real gap, not a stylistic
    one: `Contract:` header tokens are matched by `_CONTRACT_TOKEN_RE`, whose
    character class contains `.` and `/`, so a header reading
    `contracts/../../secret.json` in an untrusted spec.md resolved outside
    `--root` and was read. That produced both an existence oracle (two distinct
    warnings depending on whether the target existed) and a content-substring
    oracle. `docs/architecture/security.md` declares `filesystem_read_untrusted`
    a boundary, so hostile repo content is in scope.
    """
    return _confined_path(path, root) is not None


def _confined_path(path: Path, root: Path) -> Path | None:
    """Return the canonical path only when it remains below ``root``."""
    try:
        resolved = path.resolve()
        resolved.relative_to(root)
        return resolved
    except (OSError, ValueError, RuntimeError):
        return None


def _confined(paths, root: Path) -> list[Path]:
    """Globbed / iterated paths filtered to those within `root`.

    `pathlib.glob` follows symlinked directories, so each result is re-checked
    before it is read — a symlinked `docs/specs/<slug>` cannot pull in a
    spec.md from outside the tree.
    """
    confined: list[Path] = []
    for path in paths:
        canonical = _confined_path(path, root)
        if canonical is not None:
            confined.append(canonical)
    return confined


def _confined_file(path: Path, root: Path) -> Path | None:
    """Return a canonical in-root regular-file candidate, else ``None``."""
    canonical = _confined_path(path, root)
    return canonical if canonical is not None and canonical.is_file() else None


def _validated_root(candidate: Path | None) -> Path:
    """Resolve the CLI-supplied root, or fall back to `_repo_root()`.

    The normalise-then-check is deliberately kept *in one function, adjacent to
    the argv read*, because that is the shape taint analysers recognise. Same
    pattern as `check-spec-status.py:72-80`.

    Normalises and asserts directory-ness only — it does not confine the root
    to a fixed prefix, since `--root` is the caller-supplied scan scope. Note
    this also fixes a real usability trap: before the check, a typo'd `--root`
    scanned an empty tree and reported "spec metadata clean".
    """
    raw = candidate if candidate is not None else _repo_root()
    # `_within()` in the sibling script already catches this trio; resolve()
    # raises ValueError on an embedded null and OSError on a Windows reserved
    # name, neither of which is an OSError-only case. Letting them through
    # would produce the traceback this function exists to replace.
    try:
        root = raw.resolve()
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(
            f"lint-spec-status: --root is not a usable path: {raw!r} ({exc})"
        ) from exc
    if not root.exists():
        raise SystemExit(f"lint-spec-status: --root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"lint-spec-status: --root is not a directory: {root}")
    return root


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

    workspace_path = _confined_file(root / "workspace.toml", root)
    anchors = backlog_open_slugs(workspace_path) if workspace_path is not None else set()

    base_resolvable = base_ref is not None
    if not base_resolvable:
        warn.append(
            "invariant (ii): no base ref resolvable — ship-transition AC check "
            "skipped (shallow clone / detached HEAD)"
        )

    specs_dir = root / "docs" / "specs"
    for spec_path in sorted(_confined(specs_dir.glob("*/spec.md"), root)):
        rel = spec_path.relative_to(root).as_posix()
        text = _read(spec_path)
        if text is None:
            continue

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
                    f"does not resolve in workspace.toml [backlog].open"
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
                if not any(_confined_file(c, root) is not None for c in candidates):
                    warn.append(
                        f"{rel}:{lineno}: invariant (iii) — doc link '{target}' "
                        f"does not resolve (warn-only)"
                    )
        for lineno, path in code_references(text):
            candidates = [spec_path.parent / path, root / path]
            if not any(_confined_file(c, root) is not None for c in candidates):
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
            registry_path = _confined_file(root / "contracts" / "REGISTRY.md", root)
            registry_text = _read(registry_path) if registry_path is not None else ""
            registry_text = registry_text or ""
            for lineno, token in contract_refs:
                contract_file = _confined_file(root / token, root)
                # Confinement precedes the existence probe: an unconfined
                # is_file() is itself an existence oracle for files outside root.
                if contract_file is None:
                    warn.append(
                        f"{rel}:{lineno}: invariant (v) — Contract: '{token}' does "
                        f"not resolve to a file (warn-only)"
                    )
                    continue
                backward = False
                if token.endswith(_XSPEC_FORMATS):
                    ctext = _read(contract_file) or ""
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

    root = _validated_root(args.root)
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
