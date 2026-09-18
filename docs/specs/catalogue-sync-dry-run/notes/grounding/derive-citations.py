"""Derive § Grounding's self-hosted-init citation set and unresolved residual."""

from __future__ import annotations

import re
import sys

from _common import fail, read_text

TARGET = "initialise_self_hosted.py"
LINE_CITATION = re.compile(r"initialise_self_hosted\.py(?::|#L)(\d+)")
BARE_LINE = re.compile(r"`:(\d+)`")
SOURCES = (
    "docs/specs/catalogue-sync-dry-run/spec.md",
    "docs/specs/catalogue-sync-dry-run/plan.md",
    "docs/architecture/catalogue/upstream-sync.md",
    "docs/architecture/catalogue/derived-catalogue.md",
)


def main() -> int:
    try:
        citations: list[str] = []
        residual: list[str] = []
        for relative in SOURCES:
            text = read_text(relative)
            for match in LINE_CITATION.finditer(text):
                citations.append(f"{relative}:{match.group(1)}")
            if TARGET in text:
                residual.extend(
                    f"{relative}:{match.group(1)}" for match in BARE_LINE.finditer(text)
                )
        print("citation set: " + (", ".join(sorted(set(citations))) or "none"))
        print("residual unresolvable: " + (", ".join(sorted(set(residual))) or "none"))
        return 0
    except Exception as exc:  # pragma: no cover - one-line probe boundary
        return fail(f"citation derivation failed: {exc}")


if __name__ == "__main__":
    sys.exit(main())
