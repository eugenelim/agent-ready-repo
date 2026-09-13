#!/usr/bin/env python3
"""Generate a decision-record index from the records in a directory.

The index is derived from each record's own front matter, so it cannot
disagree with the corpus it describes. Point it at the directory holding the
records; it writes that directory's ``README.md``.

    index-records.py <record-dir>            # write the index
    index-records.py --check <record-dir>    # exit non-zero if it would change
    index-records.py --type adr <record-dir> # required only when empty

The record type is inferred from the records present. An empty directory
carries no evidence of its own type, and the two types publish different
placeholder text, so ``--type`` is required there.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import stat
import subprocess
import sys

# Git reads these from the environment and would answer for another repository.
_GIT_REDIRECT_VARIABLES = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_CEILING_DIRECTORIES",
)

# Per record type: what a record looks like and what its index publishes.
DESCRIPTORS: dict[str, dict[str, object]] = {
    "adr": {
        "h1": re.compile(r"^#\s+ADR-(\d{4}):\s*(.+?)\s*$"),
        "prefix": re.compile(r"^#\s+ADR-"),
        "heading": "Architecture Decision Records",
        "sentinel": "<!-- no ADRs yet -->",
        "columns": ("#", "Title", "Status", "Date"),
        "dates": ("Date",),
    },
    "rfc": {
        "h1": re.compile(r"^#\s+RFC-(\d{4}):\s*(.+?)\s*$"),
        "prefix": re.compile(r"^#\s+RFC-"),
        "heading": "Requests For Comments",
        "sentinel": "<!-- no RFCs yet -->",
        "columns": ("#", "Title", "Status", "Opened", "Closed"),
        "dates": ("Date opened", "Date closed"),
    },
}

# A qualifying clause may follow the lifecycle token; the table carries the token.
_STATUS = re.compile(r"^-?\s*\*\*Status:\*\*\s*(.+?)\s*$", re.MULTILINE)
_TOKEN_END = re.compile(r"\.\s|\s+(?:—|--|\(|<!--)")


# The bundled record templates ship this literal for an unfilled date, so a
# record still carrying it has no date rather than a date of that text.
_DATE_PLACEHOLDER = "YYYY-MM-DD"


def _field(text: str, name: str) -> str | None:
    r"""A field's value: None when the field is absent, "" when present and empty.

    The whitespace class is spaces and tabs, never `\s`: under MULTILINE that
    matches a newline, so an empty field would capture the following line as its
    value — which is how a Decision weight line reached a Closed date column.
    """
    match = re.search(rf"^-?[ \t]*\*\*{re.escape(name)}:\*\*[ \t]*(.*?)[ \t]*$",
                      text, re.MULTILINE)
    if match is None:
        return None
    value = match.group(1).split("<!--")[0].strip()
    if value == _DATE_PLACEHOLDER:
        # An unfilled template placeholder is not a value.
        return None
    return value


def _status_token(text: str) -> str | None:
    """The lifecycle token alone, with any qualifying clause removed."""
    match = _STATUS.search(text)
    if match is None:
        return None
    raw = match.group(1).strip()
    cut = _TOKEN_END.search(raw)
    if cut is not None:
        raw = raw[: cut.start()]
    # A supersession pointer is part of the token, but its link markup is not.
    return re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", raw).strip()


def _escape_cell(text: str) -> str:
    """Escape the delimiters that would otherwise split or break a table cell."""
    for char in ("\\", "|", "[", "]"):
        text = text.replace(char, "\\" + char)
    return text


def _escape_destination(name: str) -> str:
    """A link destination no filename byte can terminate early.

    Percent-encoding covers the delimiters that end a `(...)` destination, split
    a table row, or break it across lines. The result still resolves: a reader
    percent-decodes it back to the filename on disk.
    """
    for char, encoded in (("%", "%25"), (" ", "%20"), ("(", "%28"), (")", "%29"),
                          ("<", "%3C"), (">", "%3E"), ("|", "%7C"),
                          ("\n", "%0A"), ("\r", "%0D")):
        name = name.replace(char, encoded)
    return name


def _warn(message: str) -> None:
    print(f"index-records: {message}", file=sys.stderr)


def _git_added(directory: pathlib.Path, name: str) -> str:
    """The file's first-commit date, or empty when git cannot answer."""
    environment = os.environ.copy()
    for variable in _GIT_REDIRECT_VARIABLES:
        environment.pop(variable, None)
    try:
        result = subprocess.run(
            # --literal-pathspecs: `--` stops option parsing but not pathspec
            # magic, so a record named `:(exclude)x.md` would otherwise make Git
            # answer for every file except itself.
            ["git", "--literal-pathspecs", "log", "--diff-filter=A",
             "--format=%ad", "--date=short", "--", name],
            cwd=directory, env=environment, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, check=False, shell=False, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if result.returncode != 0:
        return ""
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return lines[-1].strip() if lines else ""


def _records(directory: pathlib.Path, pattern: re.Pattern[str],
             prefix: re.Pattern[str]) -> list[tuple[int, str, str]]:
    """Every record in the directory as (ordinal, filename, body)."""
    found: list[tuple[int, str, str]] = []
    for entry in sorted(directory.iterdir(), key=lambda p: p.name):
        if entry.suffix != ".md":
            continue
        # One lstat, not is_symlink()/is_file(): those return False on any
        # OSError, so an entry removed between listing and classification would
        # be treated as a regular file and read.
        try:
            mode = entry.lstat().st_mode
        except OSError as error:
            _warn(f"{entry.name}: cannot classify ({error})")
            continue
        if stat.S_ISLNK(mode):
            _warn(f"{entry.name}: record-looking symlink refused")
            continue
        if not stat.S_ISREG(mode):
            # A FIFO or device would block read_text() with no timeout.
            _warn(f"{entry.name}: not a regular file")
            continue
        try:
            body = entry.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            _warn(f"{entry.name}: unreadable ({error})")
            continue
        first = body.splitlines()[0] if body.splitlines() else ""
        match = pattern.match(first)
        if match is None:
            # A heading carrying the record prefix but no usable ordinal is a
            # malformed record, not a non-record: say so rather than dropping it
            # silently. `# ADR-10000: T` and `# ADR-x: T` both land here.
            if prefix.match(first):
                _warn(f"{entry.name}: record heading carries no four-digit ordinal")
            continue
        found.append((int(match.group(1)), entry.name, body))
    return sorted(found, key=lambda item: item[0])


def infer_type(directory: pathlib.Path) -> str | None:
    """The record type the directory's own records evidence, or None."""
    seen = {
        name for name, spec in DESCRIPTORS.items()
        if _records(directory, spec["h1"], spec["prefix"])  # type: ignore[arg-type]
    }
    return seen.pop() if len(seen) == 1 else None


def render(directory, record_type: str | None = None) -> str:
    """The index document for the records in *directory*."""
    directory = pathlib.Path(directory)
    if record_type is None:
        record_type = infer_type(directory)
        if record_type is None:
            raise ValueError("record type could not be determined; supply --type")
    spec = DESCRIPTORS[record_type]
    columns: tuple[str, ...] = spec["columns"]  # type: ignore[assignment]

    lines = [f"# {spec['heading']}", "", "| " + " | ".join(columns) + " |",
             "| " + " | ".join("---" for _ in columns) + " |"]

    records = _records(directory, spec["h1"], spec["prefix"])  # type: ignore[arg-type]
    if not records:
        lines.append(str(spec["sentinel"]))
        return "\n".join(lines) + "\n"

    for ordinal, name, body in records:
        title = spec["h1"].match(body.splitlines()[0]).group(2)  # type: ignore[union-attr]
        status = _status_token(body)
        if status is None:
            _warn(f"{name}: no Status field")
            status = ""
        cells = [f"{ordinal:04d}",
                 f"[{_escape_cell(title)}]({_escape_destination(name)})",
                 _escape_cell(status)]
        for field in spec["dates"]:  # type: ignore[union-attr]
            value = _field(body, field)
            if value is None:
                # Absent entirely: a legacy record predating the field. Ask git.
                value = _git_added(directory, name)
                if not value:
                    _warn(f"{name}: no {field} field and no git history")
            elif not value:
                # Present and deliberately empty — an RFC with no terminal status.
                # Never fill this from a commit date: that would label an open
                # record closed, and would change the row once it is committed.
                value = ""
            cells.append(_escape_cell(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    # The pack rule requires UTF-8 on both streams before the first print. Guard
    # the call: a wrapped or redirected stream has no reconfigure, and failing
    # there would make the CLI unusable under any harness that substitutes one.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Generate a record index from its records.")
    parser.add_argument("--check", action="store_true",
                        help="write nothing; exit non-zero if the index would change")
    parser.add_argument("--type", dest="record_type", choices=sorted(DESCRIPTORS),
                        help="record type; required when the directory holds no records")
    parser.add_argument("dir")
    args = parser.parse_args(argv)

    directory = pathlib.Path(args.dir)
    if not directory.is_dir():
        _warn(f"{args.dir}: not a directory")
        return 1
    try:
        generated = render(directory, args.record_type)
    except ValueError as error:
        _warn(str(error))
        return 1

    target = directory / "README.md"
    # The reader refusing a record-shaped symlink while the writer follows one is
    # how an index target pointing outside the directory gets overwritten with
    # record-derived content. Re-check the target itself, and abort rather than warn.
    try:
        mode = target.lstat().st_mode
    except FileNotFoundError:
        mode = None
    except OSError as error:
        _warn(f"{target}: cannot classify ({error})")
        return 1
    if mode is not None:
        if stat.S_ISLNK(mode):
            _warn(f"{target}: index target is a symlink; refusing to read or write through it")
            return 1
        if not stat.S_ISREG(mode):
            _warn(f"{target}: index target is not a regular file")
            return 1
    current = target.read_text(encoding="utf-8") if mode is not None else ""
    if args.check:
        if current == generated:
            return 0
        for number, (old, new) in enumerate(zip(current.splitlines(), generated.splitlines()), 1):
            if old != new:
                _warn(f"{target}: line {number} differs\n  on disk:   {old}\n  generated: {new}")
                return 1
        _warn(f"{target}: differs in length ({len(current.splitlines())} vs "
              f"{len(generated.splitlines())} lines)")
        return 1
    target.write_text(generated, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
