#!/usr/bin/env python3
"""Appends one entry to docs/knowledge/patterns.jsonl — the canonical writer.

The knowledge base is line-delimited JSON, and both `\\u2014` and a literal `—`
are valid JSON, so an author reaching for `json.dumps(entry)` (whose
`ensure_ascii` defaults to True) silently drifts the file's encoding while
passing every gate. This script is the one path that always writes raw UTF-8,
so the question never arises. `lint-knowledge.py` catches anything written by
another route.

Safety shape, in the order it happens — the order is the design:

  1. Resolve the repo root from git, with GIT_DIR / GIT_WORK_TREE /
     GIT_COMMON_DIR / GIT_CEILING_DIRECTORIES stripped from the child
     environment. Those variables relocate what `rev-parse` answers, and a
     confinement root an attacker can move is not a confinement root.
  2. Confine ``--file`` to ``<root>/docs/knowledge`` — expanduser, resolve,
     *then* verify the prefix. The order matters: checking before resolution
     accepts a symlink that escapes at its real location (CWE-73, the depth
     that a bare ``..``-strip misses). Same shape as the repo's blessed helper,
     ``tools/hooks/session-start.py:_safe_override_path``.
  3. Validate every field value *before* anything is opened. Entries are
     replayed verbatim into every future agent session by session-start, so
     this is a durable-instruction channel: no C0 controls (an ESC would be
     replayed as an ANSI sequence), no U+0085/U+2028/U+2029 (they break
     ``str.splitlines()``, which is how both readers parse the file), no lone
     surrogates, and length caps.
  4. Pre-lint the existing file so a knowledge base that was *already* broken
     is reported as such, rather than the caller's entry taking the blame. A
     non-existent target is not a failure — it is an empty file to create.
  5. Allocate the next id as max(existing) + 1. Gaps are fine; the linter
     enforces uniqueness, not density.
  6. Write the full new content to a temp file beside the target.
  7. Lint the *temp* file, and only ``os.replace`` it over the target on
     success. There is no window in which a rejected entry is live on disk, so
     there is nothing to roll back.

Usage:
    append-knowledge.py --kind gotcha --scope 'packs/core/**' \\
        --title '...' --body '...' --source 'PR#42' [--tier invariant]
        [--file <path under docs/knowledge>]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

SCRIPT_DIR = Path(__file__).resolve().parent
LINTER = SCRIPT_DIR / "lint-knowledge.py"

# The confinement root, relative to the repo root.
KNOWLEDGE_DIR = ("docs", "knowledge")
DEFAULT_FILENAME = "patterns.jsonl"

# Field order as documented in docs/knowledge/README.md's field table.
FIELD_ORDER = ("id", "kind", "scope", "tier", "title", "body", "source")

TITLE_CAP = 120
BODY_CAP = 2000

# str.splitlines() splits on these; the raw form would turn one entry into two
# unparseable lines. Refused here rather than escaped, because a knowledge entry
# has no business carrying a line separator mid-field.
_LINE_BREAKERS = frozenset("  ")

# Environment that steers `git rev-parse --show-toplevel` away from the cwd.
_GIT_ENV_OVERRIDES = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_CEILING_DIRECTORIES",
)


def fail(reason: str, code: int = 1) -> int:
    print(f"append-knowledge: {reason}", file=sys.stderr)
    return code


def _load_linter():
    """Import lint-knowledge.py for its enforced sets — one source of truth."""
    spec = importlib.util.spec_from_file_location("_lint_knowledge", str(LINTER))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {LINTER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def repo_root() -> Path | None:
    """The git top level for the cwd, immune to GIT_* relocation."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_OVERRIDES}
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False, env=env,
        )
    except (OSError, FileNotFoundError):
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    return Path(proc.stdout.strip())


def confine(raw: str, base: Path) -> Path | None:
    """Resolve *raw* and return it only if it stays under *base*.

    The containment check runs after ``resolve()``, so a symlink is validated
    at its real location rather than its lexical form.
    """
    try:
        resolved = Path(raw).expanduser().resolve()
        base_resolved = base.resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    if not resolved.is_relative_to(base_resolved):
        return None
    return resolved


def validate_value(field: str, value: str) -> str | None:
    """Return an error string, or None when *value* is safe to write."""
    for ch in value:
        if ch in _LINE_BREAKERS:
            return (f"{field} contains U+{ord(ch):04X}, which str.splitlines() "
                    "treats as a line break — it would split this entry in two")
        if unicodedata.category(ch) == "Cc":
            return (f"{field} contains the control character U+{ord(ch):04X}; "
                    "knowledge entries are replayed verbatim into every future "
                    "session, so control sequences are refused")
        if 0xD800 <= ord(ch) <= 0xDFFF:
            return f"{field} contains a lone surrogate U+{ord(ch):04X}"
    cap = {"title": TITLE_CAP, "body": BODY_CAP}.get(field)
    if cap is not None and len(value) > cap:
        return f"{field} is {len(value)} characters; the limit is {cap}"
    if not value.strip():
        return f"{field} must be a non-empty string"
    return None


def next_id(text: str) -> str:
    """max(existing) + 1, zero-padded. Gaps are fine — uniqueness is enforced."""
    highest = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry_id = json.loads(line).get("id", "")
        except (json.JSONDecodeError, AttributeError):
            continue
        if isinstance(entry_id, str) and entry_id.startswith("K-"):
            try:
                highest = max(highest, int(entry_id[2:]))
            except ValueError:
                continue
    return f"K-{highest + 1:04d}"


def run_linter(target: Path) -> subprocess.CompletedProcess:
    """Lint *target* out of process.

    A subprocess, not an import: lint-knowledge.py chdirs to the repo root at
    module scope, which would relocate this process's relative paths. The
    absolute path is passed as the sole argument — no ``--`` separator, which
    that script (which has no argparse) would take as the target path.
    """
    return subprocess.run(
        [sys.executable, str(LINTER), str(target)],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )


def main(argv: list[str] | None = None) -> int:
    linter = _load_linter()
    ap = argparse.ArgumentParser(
        prog="append-knowledge.py",
        description="Append one entry to the knowledge base, in raw UTF-8.",
    )
    ap.add_argument("--kind", required=True, choices=sorted(linter.ALLOWED_KINDS))
    ap.add_argument("--scope", required=True,
                    help="comma-separated path glob(s), e.g. 'packs/core/**'")
    ap.add_argument("--title", required=True, help=f"one line, <= {TITLE_CAP} chars")
    ap.add_argument("--body", required=True, help=f"the lesson, <= {BODY_CAP} chars")
    ap.add_argument("--source", required=True, help="provenance, e.g. PR#42")
    ap.add_argument("--tier", choices=sorted(linter.ALLOWED_TIERS), default=None)
    ap.add_argument("--file", default=None,
                    help="target path; must resolve under <repo>/docs/knowledge")
    args = ap.parse_args(argv)

    root = repo_root()
    if root is None:
        return fail(
            "not inside a git repository (or git is unavailable) — the "
            "confinement root cannot be established, so no write is attempted"
        )
    base = root.joinpath(*KNOWLEDGE_DIR)

    raw_target = args.file or str(base / DEFAULT_FILENAME)
    target = confine(raw_target, base)
    if target is None:
        return fail(
            f"refusing {raw_target!r}: the target must resolve inside {base} "
            "(checked after symlink resolution)"
        )

    if target.exists() and not target.is_file():
        return fail(f"{target} exists but is not a regular file")

    fields = {"kind": args.kind, "scope": args.scope, "title": args.title,
              "body": args.body, "source": args.source}
    if args.tier:
        fields["tier"] = args.tier
    for field, value in fields.items():
        problem = validate_value(field, value)
        if problem is not None:
            return fail(problem)

    existing = target.read_text(encoding="utf-8") if target.is_file() else ""

    # A file that does not exist yet is an empty knowledge base, not a broken
    # one — pre-linting it would report "does not exist" and make a fresh base
    # uncreatable.
    if target.is_file():
        pre = run_linter(target)
        if pre.returncode != 0:
            return fail(
                f"{target} already fails lint; fix it first — this append was "
                f"not attempted.\n{pre.stdout}{pre.stderr}"
            )

    entry = {"id": next_id(existing), **fields}
    ordered = {k: entry[k] for k in FIELD_ORDER if k in entry}
    line = json.dumps(ordered, ensure_ascii=False, allow_nan=False)

    if existing and not existing.endswith("\n"):
        existing += "\n"
    candidate = existing + line + "\n"

    fd, tmp_name = tempfile.mkstemp(
        prefix=".append-", suffix=".jsonl.tmp", dir=str(target.parent)
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(candidate)
        post = run_linter(tmp)
        if post.returncode != 0:
            return fail(
                f"the new entry does not lint; {target} is unchanged.\n"
                f"{post.stdout}{post.stderr}"
            )
        tmp.replace(target)
    finally:
        if tmp.exists():
            tmp.unlink()

    print(entry["id"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
