"""Shipped agentbundle content carries no internal-governance citations.

`packages/agentbundle/` reaches adopters through the wheel and the sdist, and
the sdist carries the engine's own test suite. An adopter has none of this
repository's decision records, so a citation of one reads as a broken pointer.
`packages/AGENTS.local.md` § "No internal-governance markers in source" owns
the rule; this module is its mechanical half.

Two checks, each scoped to what it can decide without false positives:

- A zero-padded `RFC-0NNN` / `ADR-0NNN` ordinal anywhere in a shipped file.
  IETF RFC numbers never start with `0`, so `RFC 9106` stays legal.
- A `docs/specs|rfc|adr/<name>` path in a Python comment or docstring, or in
  shipped prose, when `<name>` is a real record in this repository. String
  literals are code, and placeholder paths such as `docs/specs/<slug>/spec.md`
  or `docs/specs/example/` describe the adopter's own layout, so neither is a
  citation.

Out of scope: `CHANGELOG.md` and `AGENTS*.md`, which ship to nobody, and JSON
schemas, whose `x-spec` key is the contracts tree's backward pointer to its
defining spec and is byte-pinned to `contracts/`.
"""

from __future__ import annotations

import ast
import io
import re
import subprocess
import tokenize
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "packages/agentbundle"
_ORDINAL = re.compile(r"\b(?:RFC|ADR)-0[0-9]{3}\b")
_RECORD_PATH = re.compile(r"docs/(specs|rfc|adr)/([A-Za-z0-9][A-Za-z0-9._-]*)")
_UNSHIPPED_NAMES = re.compile(r"^(?:CHANGELOG\.md|AGENTS.*\.md)$")
_PROSE_SUFFIXES = {".md", ".toml", ".txt", ".cfg", ".ini", ".yaml", ".yml"}


def _shipped_files() -> list[Path]:
    """Return every tracked file under the package that adopters receive."""
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--", PACKAGE],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    return [
        REPO_ROOT / rel
        for rel in listed.split("\0")
        if rel and not _UNSHIPPED_NAMES.match(Path(rel).name)
    ]


def _comment_and_docstring_text(source: str) -> list[tuple[int, str]]:
    """Return ``(line, text)`` for every comment and docstring in *source*."""
    found = [
        (tok.start[0], tok.string)
        for tok in tokenize.generate_tokens(io.StringIO(source).readline)
        if tok.type == tokenize.COMMENT
    ]
    for node in ast.walk(ast.parse(source)):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                found.append((body[0].lineno, body[0].value.value))
    return found


def _is_record(kind: str, name: str) -> bool:
    """Return whether ``docs/<kind>/<name>`` names a real record here."""
    if name.lower().startswith("readme"):
        return False
    return (REPO_ROOT / "docs" / kind / name).exists()


def test_no_rfc_or_adr_ordinals_in_shipped_files() -> None:
    """No shipped file names an internal RFC or ADR by ordinal."""
    hits = []
    for path in _shipped_files():
        if path.suffix == ".json":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _ORDINAL.search(line):
                hits.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}")
    assert not hits, "internal RFC/ADR ordinals in shipped files:\n" + "\n".join(hits)


def test_no_internal_record_paths_in_shipped_prose() -> None:
    """No shipped comment, docstring or prose file cites a real internal record."""
    hits = []
    for path in _shipped_files():
        if path.suffix == ".py":
            chunks = _comment_and_docstring_text(path.read_text(encoding="utf-8"))
        elif path.suffix in _PROSE_SUFFIXES:
            chunks = [(1, path.read_text(encoding="utf-8"))]
        else:
            continue
        for lineno, text in chunks:
            for match in _RECORD_PATH.finditer(text):
                if _is_record(match.group(1), match.group(2)):
                    hits.append(
                        f"{path.relative_to(REPO_ROOT)}:{lineno}: {match.group(0)}"
                    )
    assert not hits, "internal record paths in shipped prose:\n" + "\n".join(hits)


def test_the_path_check_recognises_a_real_record() -> None:
    """The path check fires on a real record and ignores a placeholder.

    Without this control, a renamed records tree would leave `_is_record`
    false for every path and the check above green while it checks nothing.
    """
    real = next(p for p in (REPO_ROOT / "docs" / "specs").iterdir() if p.is_dir())
    source = f"# see docs/specs/{real.name}/spec.md\nx = 1\n"
    chunks = _comment_and_docstring_text(source)
    matches = [m for _, t in chunks for m in _RECORD_PATH.finditer(t)]
    assert matches and _is_record(matches[0].group(1), matches[0].group(2))
    assert not _is_record("specs", "<slug>")
