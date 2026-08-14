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
# Table rows, list items, blockquotes, and fence/indent markers cannot be the
# text half of a setext heading.
_NOT_A_HEADING_RE = re.compile(r"^(\||[-*+]\s|\d+[.)]\s|>|#|=|\s{4,})")


def _rel(path: Path) -> Path:
    """Repo-relative path when possible; a fixture outside the repo prints in full."""
    try:
        return path.relative_to(REPO_ROOT)
    except ValueError:
        return path


def _stray_message(path: Path, body: str, title: str | None) -> str | None:
    """Report a non-leading body H1, which the build cannot strip."""
    stray = _stray_body_h1(body)
    if stray is None:
        return None
    source = f"    title: {title}\n" if title else ""
    return (
        f"{_rel(path)}: body H1 is not the first block, so the build cannot "
        "strip it\n"
        f"{source}"
        f"    H1:    {stray}\n"
        "    It will render as a second <h1> beneath the page title. Move it to\n"
        "    the top of the body, demote it to '##', or delete it."
    )


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
        if _SETEXT_H1_RE.match(line) and i > 0:
            prev = lines[i - 1].strip()
            # A run of `=` only underlines a heading when the line above could
            # be one. Without this guard an ASCII divider under a table row,
            # list item, or blockquote reads as a setext H1 and fails CI on a
            # file that renders perfectly.
            if prev and not _NOT_A_HEADING_RE.match(prev):
                return prev
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
    """Return an error message when a guide would render two `<h1>`s, else None."""
    text = path.read_text(encoding="utf-8")
    parts = split_frontmatter(text)

    if parts is None:
        # No frontmatter: build-site.py derives the title from a *leading* H1,
        # so there is no title to diverge from — but a non-leading H1 still
        # survives the build and renders beneath the generated title. Checked
        # unconditionally; the strip is anchored, so anything past the first
        # block is a second heading regardless of where the title came from.
        return _stray_message(path, text, title=None)
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
    title = title if isinstance(title, str) and title.strip() else None

    # A stray (non-leading) H1 renders as a second <h1> whether or not the
    # leading one matches, so this runs unconditionally — checking it only when
    # there is no leading H1 misses `# Alpha` … `# A Second Real H1`.
    stray = _stray_message(path, body, title)
    if stray is not None:
        return stray

    if title is None:
        return None  # no title — the leading H1 is the only title source

    h1 = leading_h1(body)
    if h1 is None or normalise(title) == normalise(h1):
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
