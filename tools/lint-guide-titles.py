#!/usr/bin/env python3
"""Fail when a guide's frontmatter `title` and its body H1 say different things.

Starlight renders `title:` as the page heading, and `tools/build-site.py` drops
the body H1 so only one heading survives. That makes the body H1 invisible in
the published page — which is fine, until someone edits it and expects the
change to show. Before the strip landed, both rendered, and 38 pages had
quietly drifted into two different titles ("How to adapt a freshly installed
pack" over "How to adapt a freshly-installed pack").

This lint keeps the two in sync so the invisible one cannot rot: either the H1
matches the frontmatter title, or it should not be there.

Comparison is deliberately forgiving — case, hyphens/dashes, backticks, smart
quotes, inner whitespace, and trailing punctuation are all normalised away, so
only a genuine wording difference fails.

Usage:
    python3 tools/lint-guide-titles.py [--root DIR] [PATH ...]

Exits 0 when every guide agrees, 1 on the first divergence (all are reported).
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
import unicodedata
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent.resolve()


def _load_build_site():
    """Import build-site.py (hyphenated, so not importable by name)."""
    spec = importlib.util.spec_from_file_location(
        "build_site", Path(__file__).parent / "build-site.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The definition of "the page-title H1" lives in build-site.py and is imported,
# not re-derived. This lint exists to guard an invariant that module owns; a
# second copy of the rule could drift out of step and the gate would quietly
# stop guarding anything.
leading_h1 = _load_build_site().leading_h1

_DASHES = dict.fromkeys(map(ord, "-‐‑‒–—−"), " ")
_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def normalise(text: str) -> str:
    """Reduce a heading to the form used for comparison.

    Case, dash flavour, backticks, smart quotes, inner whitespace runs, and
    trailing punctuation are not divergences worth failing a build over.
    """
    text = unicodedata.normalize("NFKC", text).strip()
    text = text.translate(_QUOTES).translate(_DASHES)
    text = text.replace("`", "").replace("*", "")
    text = re.sub(r"\s+", " ", text)
    return text.casefold().rstrip(" .:;!?").strip()


_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_ATX_H1_RE = re.compile(r"^#[ \t]+(.+?)[ \t]*$")
_SETEXT_H1_RE = re.compile(r"^=+\s*$")


def _rel(path: Path) -> Path:
    """Repo-relative path when possible; a fixture outside the repo prints in full."""
    try:
        return path.relative_to(REPO_ROOT)
    except ValueError:
        return path


def _stray_body_h1(body: str) -> str | None:
    """Return a body H1 that is *not* the leading block, skipping code fences.

    Fence-aware because 42 `# ` lines across 14 guides are shell comments inside
    bash samples. Covers setext (``Title`` over ``=====``) as well as ATX, since
    the build's leading-block matcher recognises neither.
    """
    lines = body.lstrip("\n").splitlines()
    in_fence = False
    for i, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _ATX_H1_RE.match(line)
        if m and i > 0:
            return m.group(1)
        if _SETEXT_H1_RE.match(line) and i > 0 and lines[i - 1].strip():
            return lines[i - 1].strip()
    return None


def split_frontmatter(text: str) -> tuple[str, str] | None:
    """Return (yaml_block, body) or None when the file has no frontmatter."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return text[3:end], text[end + 4:]


def check_file(path: Path) -> str | None:
    """Return an error message when title and body H1 diverge, else None."""
    parts = split_frontmatter(path.read_text(encoding="utf-8"))
    if parts is None:
        return None  # no frontmatter — build-site.py derives the title from the H1
    yaml_block, body = parts

    # Parsed with yaml, not a line regex: build-site.py parses the same block
    # with yaml.safe_load, and a regex would disagree with it on folded (`>-`)
    # and wrapped-quoted scalars — reporting a divergence on frontmatter the
    # build handles fine, i.e. reddening CI over nothing.
    try:
        data = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        return None  # malformed frontmatter is the build's problem, not this gate's
    if not isinstance(data, dict):
        return None

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        return None  # no title — the H1 is the only title source

    h1 = leading_h1(body)
    if h1 is None:
        # The build only strips a *leading* H1, so a body H1 that sits after a
        # comment, a badge line, or as a setext underline survives and renders
        # as a second <h1> — the exact defect this gate exists to prevent. Look
        # for one, skipping fenced code (42 `# ` lines across 14 guides are
        # shell comments in bash samples, not headings).
        stray = _stray_body_h1(body)
        if stray is None:
            return None
        rel = _rel(path)
        return (
            f"{rel}: body H1 is not the first block, so the build cannot strip "
            "it\n"
            f"    title: {title}\n"
            f"    H1:    {stray}\n"
            "    It will render as a second <h1> beneath the page title. Move it\n"
            "    to the top of the body, or delete it."
        )

    if normalise(title) == normalise(h1):
        return None

    return (
        f"{_rel(path)}: frontmatter title and body H1 differ\n"
        f"    title: {title}\n"
        f"    H1:    {h1}\n"
        "    Starlight renders `title:` as the page heading and the build strips\n"
        "    the body H1, so only `title:` is published.\n"
        "    Prefer making them agree. Deleting the H1 also satisfies this lint,\n"
        "    but guides/_shared/** ships verbatim into adopter catalogues and\n"
        "    bundles, where frontmatter never renders — a deleted H1 leaves those\n"
        "    files opening with no heading at all."
    )


def collect(paths: list[str], root: Path) -> list[Path]:
    if paths:
        return [Path(p).resolve() for p in paths]
    return sorted(root.rglob("*.md"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        default=str(REPO_ROOT / "guides"),
        help="directory to walk when no explicit paths are given",
    )
    parser.add_argument("paths", nargs="*", help="specific files to check")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    files = collect(args.paths, root)
    errors = [msg for f in files if (msg := check_file(f))]

    for msg in errors:
        print(msg, file=sys.stderr)

    if errors:
        print(
            f"\nlint-guide-titles: {len(errors)} divergent title(s) "
            f"in {len(files)} file(s)",
            file=sys.stderr,
        )
        return 1

    print(f"lint-guide-titles: OK ({len(files)} file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
