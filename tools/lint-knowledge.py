#!/usr/bin/env python3
"""Lints docs/knowledge/patterns.jsonl. Every non-empty line must be a
JSON object with the required keys, the right `kind` value, and an
id that matches the K-NNNN format. Exit non-zero on any error.

The empty file is valid (no learnings yet).

Fixture mode: set KNOWLEDGE_FILE=<path> to lint a different file
(used by the self-test).
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys


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
ALLOWED_KINDS = {"pattern", "gotcha", "antipattern"}
ID_PATTERN = re.compile(r"^K-\d{4,}$")


def main() -> int:
    os.chdir(_repo_root())
    knowledge_file = pathlib.Path(
        os.environ.get("KNOWLEDGE_FILE", "docs/knowledge/patterns.jsonl")
    )
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

    for line_no, raw in enumerate(knowledge_file.read_text().splitlines(), start=1):
        if not raw.strip():
            continue

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

        extra = keys - REQUIRED_KEYS
        if extra:
            err(
                line_no,
                f"unknown keys: {sorted(extra)} "
                f"(allowed: {sorted(REQUIRED_KEYS)})",
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
