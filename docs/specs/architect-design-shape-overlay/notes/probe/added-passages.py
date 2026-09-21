#!/usr/bin/env python3
"""Split two design documents on their shared spine and report both difference sets.

Both directions, deliberately. A one-directional list identifies the routed
document by the direction it was computed in, whatever the documents are
labelled, so a reviewer handed only "passages in A absent from B" can infer
which arm carried the overlay from the list alone.

A passage is a top-level block: a paragraph, a list item at column zero, a
table, or a fenced block. Blocks are matched within the same spine heading and
compared on normalized text, so a reflowed line is not a difference.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

FENCE = "```"


def blocks(body: str) -> list[str]:
    """Return the top-level blocks of one section body."""
    out: list[str] = []
    current: list[str] = []
    fenced = False
    for line in body.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(FENCE):
            if not fenced:
                if current:
                    out.append("\n".join(current))
                    current = []
                fenced = True
                current.append(line)
                continue
            fenced = False
            current.append(line)
            out.append("\n".join(current))
            current = []
            continue
        if fenced:
            current.append(line)
            continue
        if not line.strip():
            if current:
                out.append("\n".join(current))
                current = []
            continue
        starts_item = line.startswith(("- ", "* ", "| "))
        if starts_item and current and not current[0].startswith(("- ", "* ", "| ")):
            out.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        out.append("\n".join(current))
    return [block for block in out if block.strip()]


def sections(text: str) -> dict[str, list[str]]:
    """Return each `##` section's blocks, keyed by heading."""
    out: dict[str, list[str]] = {}
    head = "(preamble)"
    buf: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(FENCE):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            out[head] = blocks("\n".join(buf))
            head = re.sub(r"^\d+[.)]\s*", "", line[3:].strip())
            buf = []
            continue
        buf.append(line)
    out[head] = blocks("\n".join(buf))
    return out


def normalize(block: str) -> str:
    """Return a block's text with whitespace and case collapsed."""
    return " ".join(block.split()).lower()


def only_in(left: dict[str, list[str]], right: dict[str, list[str]]) -> list[dict]:
    """Return blocks present in `left` and absent from `right`, per heading."""
    found: list[dict] = []
    for head, candidates in left.items():
        seen = {normalize(block) for block in right.get(head, [])}
        found.extend(
            {"section": head, "text": block}
            for block in candidates
            if normalize(block) not in seen
        )
    return found


def main() -> None:
    """Print both difference sets as JSON."""
    first = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    second = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
    left, right = sections(first), sections(second)
    print(
        json.dumps(
            {"a_only": only_in(left, right), "b_only": only_in(right, left)},
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
