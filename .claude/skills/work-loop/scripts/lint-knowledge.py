#!/usr/bin/env python3
"""Lints docs/knowledge/patterns.jsonl. Every non-empty line must be a
JSON object with the required keys, the right `kind` value, and an
id that matches the K-NNNN format. Exit non-zero on any error.

The empty file is valid (no learnings yet).

Fixture mode: pass a path argument to lint a different file (used by the
self-test). An argument rather than an environment variable on purpose: the
hook is for a caller that is already invoking this script deliberately, and an
env var flowing into a filesystem target is an unvalidated external-control
path (CWE-22 / CWE-73) that the repo's SAST rule rightly refuses. The argument
is resolved before the chdir below, so a relative path means what the caller
meant by it.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


def _repo_root() -> pathlib.Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return pathlib.Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return pathlib.Path.cwd()


REQUIRED_KEYS = {"id", "kind", "scope", "title", "body", "source"}
OPTIONAL_KEYS = {"tier"}
ALLOWED_KINDS = {"pattern", "gotcha", "antipattern"}
ALLOWED_TIERS = {"invariant", "observation"}
ID_PATTERN = re.compile(r"^K-\d{4,}$")

# Entries must be raw UTF-8, not `\uXXXX`-escaped. Both forms are valid JSON, so
# an author reaching for json.dumps' default (ensure_ascii=True) silently drifts
# the file's encoding — and for a non-BMP character the default emits a
# *surrogate pair* (😀 → 😀), which is valid JSON but not a valid
# TOML/YAML scalar downstream. `append-knowledge.py` writes the correct form;
# this rule catches everything else.
_ESCAPE_RE = re.compile(r"(\\+)u([0-9a-fA-F]{4})")
# Escapes that must stay legal:
#   < 0x20  — JSON requires escaping these.
#   U+0085 / U+2028 / U+2029 — str.splitlines() (used by this linter and by
#   tools/hooks/session-start.py) breaks on them, so the escaped form is the
#   *only* representation that survives a round trip.
_LINE_BREAKERS = frozenset({0x85, 0x2028, 0x2029})


def gratuitous_escapes(raw: str) -> list[tuple[str, str]]:
    """Return (escape, character) for each `\\uXXXX` that should have been literal."""
    found: list[tuple[str, str]] = []
    for m in _ESCAPE_RE.finditer(raw):
        # An escape is real only when the backslash run ending at the matched
        # `\` is odd; an even run is a literal backslash followed by "u1234".
        if len(m.group(1)) % 2 == 0:
            continue
        cp = int(m.group(2), 16)
        if cp < 0x20 or cp in _LINE_BREAKERS:
            continue
        found.append((f"\\u{m.group(2)}", chr(cp)))
    return found


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    # Resolve against the caller's cwd *before* chdir, so a relative override
    # points where the caller meant rather than at the repo root.
    override = pathlib.Path(args[0]).expanduser().resolve() if args else None
    os.chdir(_repo_root())
    knowledge_file = override or pathlib.Path("docs/knowledge/patterns.jsonl")
    error_count = 0

    def err(line_no: int, msg: str) -> None:
        nonlocal error_count
        print(f"✖ {knowledge_file}:{line_no}: {msg}", file=sys.stderr)
        error_count += 1

    if not knowledge_file.exists():
        print(
            f"⚠ {knowledge_file}: file does not exist — knowledge base not initialized",
            file=sys.stderr,
        )
        return 1

    seen_ids: dict[str, int] = {}

    for line_no, raw in enumerate(
        knowledge_file.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw.strip():
            continue

        # Checked on the raw line, before parsing: json.loads decodes the escape
        # away, so the drift is invisible to any check on the parsed object.
        # Reported through err() — a lone surrogate cannot be printed to this
        # script's stdout, which is configured errors="strict".
        for escape, char in gratuitous_escapes(raw):
            err(
                line_no,
                f"{escape} escapes a character that should be written literally "
                f"({char!r}) — write raw UTF-8 "
                f"(json.dumps(..., ensure_ascii=False)), or append via "
                f"append-knowledge.py",
            )

        try:
            entry = json.loads(raw)
        except json.JSONDecodeError as exc:
            err(line_no, f"not valid JSON: {exc.msg}")
            continue

        if not isinstance(entry, dict):
            err(line_no, "must be a JSON object, not a list or scalar")
            continue

        keys = set(entry)
        missing = REQUIRED_KEYS - keys
        if missing:
            err(line_no, f"missing required keys: {sorted(missing)}")

        extra = keys - REQUIRED_KEYS - OPTIONAL_KEYS
        if extra:
            err(
                line_no,
                f"unknown keys: {sorted(extra)} "
                f"(allowed: {sorted(REQUIRED_KEYS | OPTIONAL_KEYS)})",
            )

        # Run remaining content checks against whatever fields are present
        # — surface every problem on the line in one lint pass rather than
        # making the author re-run the linter per fix.

        id_val = entry.get("id")
        if isinstance(id_val, str) and not ID_PATTERN.match(id_val):
            err(line_no, f"id {id_val!r} must match ^K-\\d{{4,}}$ (e.g. K-0001)")
        elif isinstance(id_val, str):
            if id_val in seen_ids:
                err(
                    line_no,
                    f"duplicate id {id_val!r} "
                    f"(first seen on line {seen_ids[id_val]})",
                )
            else:
                seen_ids[id_val] = line_no

        kind_val = entry.get("kind")
        if isinstance(kind_val, str) and kind_val not in ALLOWED_KINDS:
            err(
                line_no,
                f"kind {kind_val!r} must be one of {sorted(ALLOWED_KINDS)}",
            )

        for k in ("scope", "title", "body", "source"):
            if k not in entry:
                continue  # missing-key error already fired above
            v = entry[k]
            if not isinstance(v, str) or not v.strip():
                err(line_no, f"{k!r} must be a non-empty string")
                continue
            if k == "scope":
                segments = [g.strip() for g in v.split(",") if g.strip()]
                if not segments:
                    err(line_no, "'scope' must contain at least one non-empty glob segment")

        if "tier" in entry:
            tier_val = entry["tier"]
            if not isinstance(tier_val, str):
                err(line_no, f"tier must be a string, got {type(tier_val).__name__!r}")
            elif tier_val not in ALLOWED_TIERS:
                err(
                    line_no,
                    f"tier {tier_val!r} must be one of {sorted(ALLOWED_TIERS)}"
                    f" (or omitted, defaulting to 'observation')",
                )

    print(f"\nKnowledge entries checked: {len(seen_ids)}.")
    if error_count:
        print(
            f"Knowledge lint: failed ({error_count} error(s)).",
            file=sys.stderr,
        )
        return 1
    print("Knowledge lint: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
