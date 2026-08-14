#!/usr/bin/env python3
"""Tests for tools/lint-guide-titles.py and build-site.py's H1/summary transforms.

Both are load-bearing and neither was covered: `_strip_leading_h1` rewrites every
one of the 216 generated docs pages, and the lint is the gate that keeps the
frontmatter title and the body H1 from drifting apart again.

Run directly (`python3 tools/test_lint_guide_titles.py`) or via `make test`.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).parent
REPO_ROOT = TOOLS.parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lint = _load("lint_guide_titles", "lint-guide-titles.py")
build_site = _load("build_site", "build-site.py")

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        FAILURES.append(f"{name}{': ' + detail if detail else ''}")
        print(f"  FAIL {name}{': ' + detail if detail else ''}")


def write(tmp: Path, filename: str, text: str) -> Path:
    path = tmp / filename
    path.write_text(text, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# leading_h1 / _strip_leading_h1 — the transform that rewrites every page
# ---------------------------------------------------------------------------

def test_leading_h1() -> None:
    print("leading_h1 / _strip_leading_h1")

    check(
        "leading H1 is found",
        build_site.leading_h1("# The Title\n\nbody\n") == "The Title",
    )
    check(
        "leading blank lines are tolerated",
        build_site.leading_h1("\n\n# The Title\n\nbody\n") == "The Title",
    )
    check(
        "a non-leading '#' is NOT treated as the page title",
        build_site.leading_h1("Intro paragraph.\n\n# Later Heading\n") is None,
    )
    check(
        "a '#' inside a code fence is not the page title",
        build_site.leading_h1("Intro.\n\n```bash\n# a shell comment\n```\n") is None,
        "42 such lines exist across 14 guides; promoting or deleting one loses content",
    )
    check(
        "'##' is not an H1",
        build_site.leading_h1("## Section\n\nbody\n") is None,
    )
    check(
        "a body with no heading returns None",
        build_site.leading_h1("just prose\n") is None,
    )

    stripped = build_site._strip_leading_h1("# The Title\n\nbody text\n")
    check("strip removes the leading H1", stripped == "body text\n", repr(stripped))

    keep = "Intro.\n\n# Later Heading\n\nmore\n"
    check("strip leaves a non-leading '#' alone", build_site._strip_leading_h1(keep) == keep)

    fenced = "Intro.\n\n```bash\n# a shell comment\n```\n"
    check("strip leaves a fenced '#' alone", build_site._strip_leading_h1(fenced) == fenced)


# ---------------------------------------------------------------------------
# _strip_guide_metadata — H1 removal + summary -> description
# ---------------------------------------------------------------------------

def test_strip_guide_metadata() -> None:
    print("_strip_guide_metadata")

    out = build_site._strip_guide_metadata(
        '---\ntitle: "Alpha"\npack: core\nkind: how-to\n---\n\n# Alpha\n\nbody\n'
    )
    check("H1 stripped when frontmatter carries a title", "# Alpha" not in out, out)
    check("title survives the strip", "title: Alpha" in out or 'title: "Alpha"' in out)

    out = build_site._strip_guide_metadata(
        '---\nsummary: "Only a summary here"\npack: core\n---\n\n# Kept Heading\n\nbody\n'
    )
    check(
        "H1 kept when frontmatter has no title (it is the only title source)",
        "# Kept Heading" in out,
        out,
    )

    out = build_site._strip_guide_metadata(
        '---\ntitle: "Alpha"\nsummary: "The one-line summary."\npack: core\n---\n\nbody\n'
    )
    check("summary is mapped onto description", "description: The one-line summary." in out, out)
    check("guide-only summary key is dropped", "summary:" not in out, out)

    out = build_site._strip_guide_metadata(
        '---\ntitle: "Alpha"\nsummary: "From summary"\n'
        'description: "Explicit wins"\npack: core\n---\n\nbody\n'
    )
    check("an explicit description beats summary", "Explicit wins" in out, out)
    check("summary does not overwrite it", "From summary" not in out, out)

    # Frontmatter carrying only Starlight-compatible keys takes the early-return
    # path; the H1 must still go.
    out = build_site._strip_guide_metadata(
        '---\ntitle: "Alpha"\ndescription: "d"\n---\n\n# Alpha\n\nbody\n'
    )
    check("H1 stripped on the no-frontmatter-rewrite path", "# Alpha" not in out, out)
    check("body survives that path", "body" in out, out)

    unchanged = "no frontmatter here\n\n# Heading\n"
    check(
        "text without frontmatter is returned untouched",
        build_site._strip_guide_metadata(unchanged) == unchanged,
    )


# ---------------------------------------------------------------------------
# the lint
# ---------------------------------------------------------------------------

def test_lint() -> None:
    print("lint-guide-titles")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        p = write(tmp, "match.md", '---\ntitle: "A Matching Title"\n---\n\n# A Matching Title\n')
        check("(a) identical pair passes", lint.check_file(p) is None)

        p = write(
            tmp,
            "normalised.md",
            '---\ntitle: "How to adapt a freshly installed pack"\n---\n\n'
            "# How to adapt a freshly-installed pack.\n",
        )
        check(
            "(a2) case/dash/punctuation differences pass",
            lint.check_file(p) is None,
            str(lint.check_file(p)),
        )

        p = write(
            tmp,
            "backticks.md",
            '---\ntitle: "iac-terraform — guides"\n---\n\n# `iac-terraform` — guides\n',
        )
        check("(a3) backticks and dashes normalise", lint.check_file(p) is None)

        p = write(
            tmp,
            "divergent.md",
            '---\ntitle: "Run an Audit"\n---\n\n# How-to: Run a frontend-engineering audit\n',
        )
        msg = lint.check_file(p)
        check("(b) genuine divergence fails", msg is not None)
        check("(b2) the message names both strings", bool(msg) and "Run an Audit" in msg and "frontend-engineering audit" in msg)

        p = write(tmp, "no-h1.md", '---\ntitle: "No H1 Here"\n---\n\nJust prose.\n')
        check("(c) no body H1 passes", lint.check_file(p) is None)

        p = write(tmp, "no-fm.md", "# Only an H1\n\nbody\n")
        check("(d) no frontmatter passes", lint.check_file(p) is None)

        p = write(tmp, "no-title.md", '---\nsummary: "s"\n---\n\n# Body Is The Title\n')
        check("(e) frontmatter without a title passes", lint.check_file(p) is None)

        p = write(
            tmp,
            "folded.md",
            "---\ntitle: >-\n  Folded Title Here\n---\n\n# Folded Title Here\n",
        )
        check(
            "(f) a folded YAML scalar is parsed, not regexed",
            lint.check_file(p) is None,
            str(lint.check_file(p)),
        )

        p = write(
            tmp,
            "fenced.md",
            '---\ntitle: "Alpha"\n---\n\nIntro.\n\n```bash\n# a shell comment\n```\n',
        )
        check("(g) a '#' inside a code fence is not reported", lint.check_file(p) is None)

        p = write(
            tmp,
            "stray.md",
            '---\ntitle: "Alpha"\n---\n\nIntro paragraph.\n\n# Stray Heading\n',
        )
        msg = lint.check_file(p)
        check("(h) a non-leading body H1 IS reported", msg is not None)
        check(
            "(h2) with the distinct not-first-block message",
            bool(msg) and "not the first block" in msg,
            str(msg),
        )

        p = write(
            tmp,
            "setext.md",
            '---\ntitle: "Alpha"\n---\n\nIntro.\n\nStray Setext\n============\n',
        )
        check("(i) a setext H1 is reported too", lint.check_file(p) is not None)

        p = write(tmp, "broken.md", '---\ntitle: "A\n  bad: [\n---\n\n# X\n')
        check("(j) malformed frontmatter is not this gate's problem", lint.check_file(p) is None)


def main() -> int:
    test_leading_h1()
    test_strip_guide_metadata()
    test_lint()
    print()
    if FAILURES:
        print(f"test-lint-guide-titles: {len(FAILURES)} failure(s)", file=sys.stderr)
        return 1
    print("test-lint-guide-titles: all passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
