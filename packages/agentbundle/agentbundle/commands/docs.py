"""``agentbundle docs <pack>`` subcommand.

Display pack documentation from the pack's docs/ directory.

  agentbundle docs <pack>           — display index.md
  agentbundle docs <pack> --list    — list available .md files by stem
  agentbundle docs <pack> <file>    — display a specific file by stem

Resolution uses the same four-layer source chain as install. The docs/
directory travels inside Artifactory archives, so this verb works across
all four source types (local path, editable install, git+https, archive).

Exit codes:
  0  — success
  1  — catalogue unavailable, pack not found, no docs/ directory, or file
       not found
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

_BOLD_ON = "\x1b[1m"
_BOLD_OFF = "\x1b[0m"


def run(args: "argparse.Namespace") -> int:
    from agentbundle.catalogue import CatalogueError, resolve_catalogue
    from agentbundle.commands._common import resolve_catalogue_uri
    from agentbundle.commands.show import _find_pack_dir

    pack_name: str = args.pack
    file_stem: str | None = getattr(args, "file", None)
    list_mode: bool = getattr(args, "list_docs", False)

    try:
        catalogue_dir = resolve_catalogue(resolve_catalogue_uri(args))
    except CatalogueError as exc:
        print(f"docs: {exc}", file=sys.stderr)
        return 1

    match = _find_pack_dir(catalogue_dir, pack_name)
    if match is None:
        print(f"docs: pack {pack_name!r} not found in catalogue", file=sys.stderr)
        return 1

    pack_dir, _ = match
    docs_dir = pack_dir / "docs"
    if not docs_dir.is_dir():
        print(f"docs: {pack_name}: no docs directory in pack source", file=sys.stderr)
        return 1

    md_files = sorted(
        p for p in docs_dir.iterdir()
        if p.suffix == ".md" and not p.name.startswith("_")
    )

    if list_mode:
        for f in md_files:
            print(f.stem)
        return 0

    stem = file_stem or "index"
    target: Path | None = None
    for f in md_files:
        if f.stem == stem:
            target = f
            break

    if target is None:
        available = ", ".join(f.stem for f in md_files) or "none"
        print(
            f"docs: {pack_name}: file {stem!r} not found. Available: {available}",
            file=sys.stderr,
        )
        return 1

    text = target.read_text(encoding="utf-8")
    tty = sys.stdout.isatty()
    print(_render_md(text, tty=tty), end="")
    return 0


def _render_md(text: str, *, tty: bool) -> str:
    """Render Markdown as plain text, optionally with ANSI bold headings.

    Preserves code blocks verbatim. Strips heading # markers (bold on tty,
    plain text otherwise). Strips link syntax [text](url) to bare text.
    """
    import re

    lines = text.splitlines(keepends=False)
    out: list[str] = []
    in_code = False

    for line in lines:
        if line.startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if in_code:
            out.append(line)
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            content = m.group(2)
            out.append(f"{_BOLD_ON}{content}{_BOLD_OFF}" if tty else content)
            continue
        processed = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
        out.append(processed)

    return "\n".join(out) + ("\n" if out else "")
