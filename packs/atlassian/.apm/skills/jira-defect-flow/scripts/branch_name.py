#!/usr/bin/env python3
"""Generate a deterministic fix-branch name from a Jira key and summary.

Two agents working the same ticket should converge on the same branch name
instead of forking. That convergence is the whole point of this helper —
it is intentionally tiny.

Usage:
    python branch_name.py PROJ-123 "Null pointer in cart checkout"
    -> fix/proj-123-null-pointer-in-cart-checkout

    python branch_name.py PROJ-123 "Null pointer in cart checkout" --prefix hotfix
    -> hotfix/proj-123-null-pointer-in-cart-checkout

Exit codes:
    0  success, branch name printed to stdout (no trailing newline)
    2  invalid Jira key shape
"""

from __future__ import annotations

import argparse
import os
import re
import sys

JIRA_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]+-\d+$")


def slugify(text: str, max_words: int = 6) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    parts = [p for p in text.split("-") if p]
    return "-".join(parts[:max_words])


def build_branch_name(key: str, summary: str, prefix: str, max_words: int) -> str:
    slug = slugify(summary, max_words)
    base = f"{prefix}/{key.lower()}"
    return f"{base}-{slug}" if slug else base


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("key", help="Jira issue key, e.g. PROJ-123")
    p.add_argument("summary", help="Issue summary (will be slugified)")
    p.add_argument(
        "--prefix",
        default=os.environ.get("JIRA_DEFECT_FIX_PREFIX", "fix"),
        help="Branch prefix (default: fix, or $JIRA_DEFECT_FIX_PREFIX)",
    )
    p.add_argument("--max-words", type=int, default=6, help="Max slug words (default: 6)")
    args = p.parse_args(argv)

    if not JIRA_KEY_RE.match(args.key):
        print(f"error: {args.key!r} is not a Jira key (expected e.g. PROJ-123)", file=sys.stderr)
        return 2

    sys.stdout.write(build_branch_name(args.key, args.summary, args.prefix, args.max_words))
    return 0


if __name__ == "__main__":
    sys.exit(main())
