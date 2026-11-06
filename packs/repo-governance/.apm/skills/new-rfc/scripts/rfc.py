#!/usr/bin/env python3
"""Start and check RFCs. Standard library only; needs no agent and no skill.

Run it in isolated mode, so a file planted beside it can never shadow the
standard library:

    python3 -I docs/rfc/rfc.py new "Short title" [--author HANDLE] [--number N] [--slug TEXT]
    python3 -I docs/rfc/rfc.py next
    python3 -I docs/rfc/rfc.py renumber FILE NUMBER
    python3 -I docs/rfc/rfc.py check [FILE ...] [--strict]

Add `--dir PATH` before the command to work on another RFC folder, for example
to check a contributor's branch with a trusted copy of this script:

    python3 -I docs/rfc/rfc.py --dir ../their-checkout/docs/rfc check

`next` prints the next free number and is the one place numbering is settled; the
`new-rfc` skill calls it through its own byte-identical copy of this script.

`new` copies template.md.tmpl (from the RFC folder) to the next free
NNNN-slug.md. It never overwrites a file and never edits the table in
README.md. The next number comes from the folder plus the last-fetched
`upstream` and `origin` default branches; it uses no network. Two proposals can
still pick the same number, so a maintainer can run `renumber` at merge.

`check` warns about an RFC that is still open when it is over WORD_LIMIT words
(a length warning; title and header fields excluded, fenced code included) or
lacks a required section (a missing-section warning); about files that share a
number (a number-clash warning); and about unexpected or oddly named files. It
starts no git process. Warnings exit 0 unless --strict is given (then 1).
Unreadable files exit 2.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import os
import re
import stat
import subprocess
import sys
import types
import unicodedata
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
FOLDER = SCRIPT_DIR  # the RFC folder to work on; --dir replaces it
WORD_LIMIT = 5000
MAX_NUMBER = 9999
MAX_BYTES = 1024 * 1024
MAX_SLUG = 60
# RFCs in these statuses are finished; any other status, or none, counts as open.
TERMINAL = {"accepted", "rejected", "withdrawn", "experimental", "superseded"}
REQUIRED_SECTIONS = (
    "Summary", "Motivation", "Proposal",
    "Costs and what could go wrong", "Alternatives", "How we will know it works",
)
# A NNNN-<slug>-research.md sibling shares its RFC's number, so it is not a record.
RECORD = re.compile(r"^(\d{4}|XXXX)-(?!.*-research\.md$)[a-z0-9-]+\.md$")
COMPANION = re.compile(r"^(\d{4}|XXXX)-[a-z0-9-]+-research\.md$")
NOTES_DIR = re.compile(r"^\d{4}-notes$")
NUMBERED = re.compile(r"^(\d{4})-(?:[a-z0-9-]+\.md|notes)$")
KNOWN_FILES = {"README.md", "rfc.py", "file_safety.py", "template.md.tmpl"}
SCRIPT_FILES = {"rfc.py", "file_safety.py"}
CODE_SUFFIXES = (".py", ".pyc", ".pyo", ".pth", ".so", ".pyd", ".sh")
GIT_SUBCOMMANDS = {"rev-parse", "symbolic-ref", "ls-tree"}
HELPER_NAMES = (
    "UnsafeContentError", "validate_confined_directory",
    "read_confined_regular_file", "write_confined_regular_file",
)
CHECK_HELP = ("warn about open RFCs that trigger a length or missing-section warning, "
              "and about files that trigger a number-clash warning")

_fs_module: Any = None


def _fs() -> Any:
    """Load file_safety.py from this script's folder, once, from its own source bytes.

    The file is opened without following a link, must be a regular file, and is
    compiled and run directly, so no bytecode cache is read or written.
    """
    global _fs_module
    if _fs_module is not None:
        return _fs_module
    path = SCRIPT_DIR / "file_safety.py"
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(path, flags)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ImportError("required helper is not a regular file: file_safety.py")
            data = b""
            while chunk := os.read(descriptor, 65536):
                data += chunk
                if len(data) > MAX_BYTES:
                    raise ImportError("required helper is too large: file_safety.py")
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise ImportError("required helper unavailable: file_safety.py") from exc
    name = "_new_rfc_rfc_file_safety"
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    try:
        exec(compile(data, str(path), "exec", dont_inherit=True), module.__dict__)
        missing = [n for n in HELPER_NAMES if not hasattr(module, n)]
        if missing:
            raise ImportError("required helper is incomplete: file_safety.py")
    except BaseException:
        sys.modules.pop(name, None)
        raise
    _fs_module = module
    return module


def show(text: object) -> str:
    """Printable form of a file name or value, with control characters escaped."""
    return "".join(
        c if c.isprintable() else c.encode("unicode_escape").decode() for c in str(text)
    )


def absolute(path: str | Path) -> Path:
    """Absolute, normalised form of a path; unlike resolve(), it never follows a link."""
    return Path(os.path.abspath(path))  # noqa: PTH100


def root() -> Path:
    """The RFC folder as an absolute path with no link resolution."""
    return absolute(FOLDER)


def listing() -> list[tuple[str, str]]:
    """Top-level entries of the RFC folder as (name, kind): file, dir, link or other.

    The folder is validated with the shared helper first. The helper's own
    listing refuses links and descends into folders, which `check` must report
    rather than refuse, so the names come from one scan of that validated folder.
    """
    base = root()
    _fs().validate_confined_directory(base, base)
    found: list[tuple[str, str]] = []
    with os.scandir(base) as scan:
        for entry in scan:
            mode = entry.stat(follow_symlinks=False).st_mode
            kind = ("link" if stat.S_ISLNK(mode) else "dir" if stat.S_ISDIR(mode)
                    else "file" if stat.S_ISREG(mode) else "other")
            found.append((entry.name, kind))
    return sorted(found)


def number_of(name: str) -> int | None:
    """The RFC number in a record file name, or None for a draft not yet numbered (XXXX)."""
    m = RECORD.match(name)
    return int(m.group(1)) if m and m.group(1).isdigit() else None


def records(entries: list[tuple[str, str]]) -> list[str]:
    """Names of regular files that are RFC records."""
    return [n for n, kind in entries if kind == "file" and RECORD.match(n)]


def used_numbers(entries: list[tuple[str, str]]) -> set[int]:
    """Numbers taken by records, research companions and notes folders."""
    used: set[int] = set()
    for name, kind in entries:
        if (kind == "file" and NUMBERED.match(name) and not name.endswith("-notes")) or (
                kind == "dir" and NOTES_DIR.match(name)):
            used.add(int(name[:4]))
    return used


def slugify(title: str) -> str:
    """ASCII slug of lowercase letters, digits and single hyphens, at most MAX_SLUG long."""
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")[:MAX_SLUG].strip("-")


def clean_one_line(text: str) -> str:
    """Drop invisible format characters, then collapse whitespace so a value stays on one line."""
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return re.sub(r"[\x00-\x1f\x7f\s]+", " ", text).strip()


def _spawn(argv: list[str], cwd: str, env: dict[str, str]) -> tuple[int, str]:
    """The one place a process starts: run argv and return (exit code, stdout)."""
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=10, env=env, cwd=cwd,
                              stdin=subprocess.DEVNULL, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return done.returncode, done.stdout


def _git(*args: str) -> str:
    """Read-only git plumbing, run in the RFC folder, running no program named in repo config."""
    if not args or args[0] not in GIT_SUBCOMMANDS:
        raise ValueError(f"git subcommand not allowed: {args[:1]}")
    argv = ["git", "-c", "core.fsmonitor=", "-c", "core.hooksPath=" + os.devnull,
            "-c", "protocol.allow=never", "-c", "safe.bareRepository=explicit", *args]
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"}
    code, out = _spawn(argv, str(root()), env)
    return out if code == 0 else ""


def remote_names() -> set[str] | None:
    """File names on the last-fetched default branch of `upstream`/`origin`, or None if unknown."""
    top = _git("rev-parse", "--show-toplevel").strip()
    if not top:
        return None
    folder = Path(os.path.relpath(root().resolve(), Path(top).resolve())).as_posix()
    found: set[str] = set()
    seen = False
    for remote in ("upstream", "origin"):
        refs = [_git("symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD").strip(),
                f"{remote}/main", f"{remote}/master"]
        ref = next(
            (r for r in refs if r and _git("rev-parse", "--verify", "--quiet", r).strip()), ""
        )
        if not ref:
            continue
        seen = True
        tree = _git("ls-tree", "--full-tree", "--name-only", f"{ref}:{folder}")
        found |= {n for n in tree.split("\n") if n}
    return found if seen else None


def read_text(path: Path) -> str:
    """Read a regular non-link file directly in the RFC folder, capped at MAX_BYTES."""
    return _fs().read_confined_regular_file(root(), path, max_bytes=MAX_BYTES).decode("utf-8")


def next_number(entries: list[tuple[str, str]]) -> int:
    """One more than the highest number in the folder and on the last-fetched default branches."""
    remote = {int(m.group(1)) for name in (remote_names() or set()) if (m := NUMBERED.match(name))}
    return max(used_numbers(entries) | remote, default=0) + 1


def cmd_next(args: argparse.Namespace) -> int:
    """Print the next free number."""
    try:
        number = next_number(listing())
    except (OSError, ValueError) as exc:
        print(f"error: cannot read the RFC folder: {show(exc)}", file=sys.stderr)
        return 2
    if number > MAX_NUMBER:
        print(f"error: the next number would pass {MAX_NUMBER}", file=sys.stderr)
        return 2
    print(f"{number:04d}")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    """Create a numbered draft from the folder's template."""
    title = clean_one_line(args.title)
    slug = slugify(args.slug or title)
    if not title or not slug:
        print("error: need a title and ASCII letters or digits in the slug; pass --slug",
              file=sys.stderr)
        return 2
    if slug.endswith("-research"):
        print("error: a slug ending in -research would name a research companion", file=sys.stderr)
        return 2
    if args.number is not None and not 1 <= args.number <= MAX_NUMBER:
        print(f"error: --number must be between 1 and {MAX_NUMBER}", file=sys.stderr)
        return 2
    try:
        entries = listing()
        number = next_number(entries) if args.number is None else args.number
        if number > MAX_NUMBER:
            print(f"error: the next number would pass {MAX_NUMBER}; pass --number",
                  file=sys.stderr)
            return 2
        if number in used_numbers(entries):
            print(f"error: number {number:04d} is already used; nothing written", file=sys.stderr)
            return 1
        template = read_text(root() / "template.md.tmpl")
    except (OSError, ValueError) as exc:
        print(f"error: {show(exc)}; nothing written", file=sys.stderr)
        return 2
    number_text = f"{number:04d}"
    # Literal placeholders keep the template readable and let a person or an agent fill it by hand.
    # The title goes in last-line-safe: only the first line takes it, so it is never re-expanded.
    head, _, rest = template.partition("\n")
    head = re.sub(r"^# RFC-NNNN:.*$", lambda _m: f"# RFC-{number_text}: {title}", head, count=1)
    rest = rest.replace("YYYY-MM-DD", datetime.date.today().isoformat(), 1)
    if (author := clean_one_line(args.author)):
        rest = rest.replace("<account-handle>", author, 1)  # else keep the neutral placeholder
    target = root() / f"{number_text}-{slug}.md"
    if os.path.lexists(target):
        print(f"error: {show(target.name)} already exists; nothing written", file=sys.stderr)
        return 1
    try:
        _fs().write_confined_regular_file(root(), target, (head + "\n" + rest).encode("utf-8"),
                                          expect_sha256=None)
    except (OSError, ValueError) as exc:
        print(f"error: {show(exc)}; nothing written", file=sys.stderr)
        return 2
    print(f"Created {show(target)}")
    if args.number is None:
        print("Number: next free in this folder and your last fetch of upstream/origin.")
    return 0


def cmd_renumber(args: argparse.Namespace) -> int:
    """Give a draft or record another number, leaving only the original file on any failure."""
    base = root()
    source = absolute(args.file)  # normalise the text only; never resolve links
    if (source.parent != base or not RECORD.match(source.name)
            or not 1 <= args.number <= MAX_NUMBER):
        print("error: give an RFC file in this folder (not a link) and a number from 1 to "
              f"{MAX_NUMBER}", file=sys.stderr)
        return 2
    target = base / f"{args.number:04d}-{source.name.split('-', 1)[1]}"
    try:
        cwd = Path.cwd()
        anchor = cwd if source.parent.is_relative_to(cwd) else source.parent
        _fs().validate_confined_directory(anchor, source.parent)
        if stat.S_ISLNK(os.lstat(source).st_mode):
            raise OSError("not a regular file")
        if args.number in used_numbers(listing()):
            print(f"error: number {args.number:04d} is already used; nothing changed",
                  file=sys.stderr)
            return 1
        text = read_text(source)
    except (OSError, ValueError) as exc:
        print(f"error: cannot renumber {show(source.name)}: {show(exc)}; nothing changed",
              file=sys.stderr)
        return 2
    text = re.sub(r"^# RFC-(\d+|XXXX):", f"# RFC-{args.number:04d}:", text, count=1,
                  flags=re.MULTILINE)
    created = False
    try:
        _fs().write_confined_regular_file(base, target, text.encode("utf-8"), expect_sha256=None)
        created = True
        source.unlink()
    except (OSError, ValueError) as exc:
        if created:
            target.unlink()  # never leave two copies behind
        print(f"error: {show(exc)}; nothing changed", file=sys.stderr)
        return 2
    print(f"Renamed {show(source.name)} -> {show(target.name)}. "
          "Links to the old number are not rewritten.")
    return 0


FIELD = re.compile(r"^- \*\*[^*]+:\*\*")


def counted_text(text: str) -> str:
    """Text that counts toward the length warning: all but the title and header field block.

    Prose between the header and the first section counts, and so do fenced code blocks.
    """
    out: list[str] = []
    state = "top"
    for line in text.split("\n"):
        if state == "top":
            if line.startswith("# ") and not out:
                continue
            if FIELD.match(line):
                state = "header"
                continue
            out.append(line)
        elif state == "header":
            if not line.strip():
                state = "body"
        else:
            out.append(line)
    return "\n".join(out)


def status_word(text: str) -> str:
    """The first word of the Status header field, lowercased, or an empty string."""
    m = re.search(r"^-?\s*\*\*Status:\*\*\s*[*_]*(\w+)", text, re.MULTILINE)
    return m.group(1).lower() if m else ""


def folder_warnings(entries: list[tuple[str, str]]) -> list[str]:
    """Warnings about links, code, odd names and shared numbers at the top of the folder."""
    out: list[str] = []
    for name, kind in entries:
        if kind == "link":
            out.append(f"warning: {show(name)} is a link and is ignored.")
        elif kind == "dir":
            if not NOTES_DIR.match(name):
                out.append(f"warning: unexpected folder {show(name)}/ in the RFC folder.")
        elif kind == "other":
            out.append(f"warning: {show(name)} is not a regular file and is ignored.")
        elif name in SCRIPT_FILES or name in KNOWN_FILES:
            continue
        elif name.endswith(CODE_SUFFIXES):
            out.append(f"warning: unexpected code file {show(name)} beside the script.")
        elif not RECORD.match(name) and not COMPANION.match(name):
            out.append(f"warning: unexpected file name {show(name)}.")
    owners: dict[int, list[str]] = collections.defaultdict(list)
    for name in records(entries):
        if (n := number_of(name)) is not None:
            owners[n].append(show(name))
    for number, names in sorted(owners.items()):
        if len(names) > 1:
            out.append(f"warning: number {number:04d} is used by {', '.join(names)}.")
    return out


def cmd_check(args: argparse.Namespace) -> int:
    """Report length, missing-section, number-clash and unexpected-file warnings."""
    try:
        entries = listing()
    except (OSError, ValueError) as exc:
        print(f"error: cannot read the RFC folder: {show(exc)}", file=sys.stderr)
        return 2
    lines = folder_warnings(entries)
    warnings = len(lines)
    for line in lines:
        print(line)
    base = root()
    paths = [absolute(f) for f in args.files] or [base / n for n in records(entries)]
    unreadable = 0
    for path in paths:
        if path.parent == base and (COMPANION.match(path.name) or path.name in KNOWN_FILES):
            continue
        if path.parent == base and not RECORD.match(path.name):
            print(f"warning: {show(path.name)} is not an RFC record and was not read.")
            warnings += 1
            continue
        try:
            if path.parent != base:
                raise OSError("not inside the RFC folder")
            text = read_text(path)
        except (OSError, ValueError) as exc:
            print(f"error: cannot read {show(path.name)}: {show(exc)}", file=sys.stderr)
            unreadable += 1
            continue
        if status_word(text) in TERMINAL:
            continue
        words = len(counted_text(text).split())
        if words > WORD_LIMIT:
            print(f"warning: {show(path.name)} is {words:,} words, over {WORD_LIMIT:,}. "
                  "Move detail into a spec or ADR and link it.")
            warnings += 1
        for name in REQUIRED_SECTIONS:
            if not re.search(rf"^##\s+{re.escape(name)}\s*$", text, re.MULTILINE):
                print(f"warning: {show(path.name)} has no '## {name}' section.")
                warnings += 1
    if unreadable:
        return 2
    return 1 if (warnings and args.strict) else 0


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and run one command; return its exit code."""
    global FOLDER
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("--dir", help="RFC folder to work on (default: this script's folder)")
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="create a numbered draft from template.md.tmpl")
    new.add_argument("title")
    new.add_argument("--author", default="")
    new.add_argument("--number", type=int, help="use this number instead of the next free one")
    new.add_argument("--slug", default="", help="file name text; needed for non-ASCII titles")
    new.set_defaults(run=cmd_new)
    nxt = sub.add_parser("next", help="print the next free number")
    nxt.set_defaults(run=cmd_next)
    renum = sub.add_parser("renumber", help="give a draft a different number")
    renum.add_argument("file")
    renum.add_argument("number", type=int)
    renum.set_defaults(run=cmd_renumber)
    check = sub.add_parser("check", help=CHECK_HELP, description=CHECK_HELP)
    check.add_argument("files", nargs="*")
    check.add_argument("--strict", action="store_true", help="exit 1 when a warning is raised")
    check.set_defaults(run=cmd_check)
    args = parser.parse_args(argv)
    FOLDER = Path(args.dir) if args.dir else SCRIPT_DIR
    if not FOLDER.is_dir():
        print("error: the RFC folder is not a folder", file=sys.stderr)
        return 2
    try:
        _fs()
    except ImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return int(args.run(args))


if __name__ == "__main__":
    sys.exit(main())
