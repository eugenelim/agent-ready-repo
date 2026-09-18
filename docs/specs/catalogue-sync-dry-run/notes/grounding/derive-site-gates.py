"""Derive § Grounding's authored-versus-rendered site-gate representations."""

from __future__ import annotations

import re
import sys

from _common import fail, read_text


def main() -> int:
    try:
        makefile = read_text("Makefile")
        docs_agent = read_text("docs-site/AGENTS.md")
        entry_test = read_text("tools/test_documentation_entry_links.py")
        rendered_checker = read_text("tools/check-rendered-site-links.py")
        target = re.search(r"^site-link-check:.*$", makefile, re.MULTILINE)
        if target is None or "check-rendered-site-links.py" not in makefile:
            return fail("Makefile does not define the rendered link gate")
        if "authored sources only" not in entry_test:
            return fail("entry-link test does not identify its authored input")
        if "build" not in rendered_checker or "make site-link-check" not in docs_agent:
            return fail("rendered link checker representation is not established")
        print("entry-link gate: authored guides and documentation sources")
        print("rendered-link gate: generated build tree")
        print("residual: none")
        return 0
    except Exception as exc:  # pragma: no cover - one-line probe boundary
        return fail(f"site-gate derivation failed: {exc}")


if __name__ == "__main__":
    sys.exit(main())
