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

`next` prints the next free number and is the one place numbering is decided; the
`new-rfc` skill calls it through its own byte-identical copy of this script.

`new` copies template.md.tmpl (from this script's own folder) to the next free
NNNN-slug.md. It never overwrites a file and never edits the table in
README.md. The next number comes from the folder plus the last-fetched
`upstream` and `origin` default branches; it uses no network. Two proposals can
still pick the same number, so a maintainer can run `renumber` at merge.

`check` warns about an RFC that is still being decided when it is over
WORD_LIMIT words (title and header fields excluded, fenced code included) or lacks a required section; about a decided RFC that is not
on the last-fetched default branch; about files that share a number; and about
unexpected or oddly named files. Warnings exit 0 unless --strict is given
(then 1). Unreadable files exit 2.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FOLDER = SCRIPT_DIR  # the RFC folder to work on; --dir replaces it
WORD_LIMIT = 5000
MAX_NUMBER = 9999
MAX_BYTES = 1024 * 1024
# Decided RFCs are left alone; any other status, or none, counts as still in flight.
DECIDED = {"accepted", "rejected", "withdrawn", "experimental", "superseded"}
REQUIRED_SECTIONS = (
    "Summary", "Motivation", "Proposal",
    "Costs and what could go wrong", "Alternatives", "How we will know it works",
)
# A NNNN-<slug>-research.md sibling shares its RFC's number, so it is not a record.
RECORD = re.compile(r"^(\d{4}|XXXX)-(?!.*-research\.md$)[a-z0-9-]+\.md$")
KNOWN_NAME = re.compile(r"^(\d{4}|XXXX)-[a-z0-9-]+\.md$")
KNOWN_FILES = {"README.md", "rfc.py", "file_safety.py", "template.md.tmpl"}
CODE_SUFFIXES = (".py", ".pyc", ".pth", ".so", ".pyd", ".sh")


def show(text: object) -> str:
    """Printable form of a file name or value, with control characters escaped."""
    return "".join(c if c.isprintable() else c.encode("unicode_escape").decode() for c in str(text))


def is_plain_file(path: Path) -> bool:
    """A regular file that is not a link and sits directly in the RFC folder."""
    try:
        return (not path.is_symlink() and path.is_file()
                and path.resolve(strict=True).parent == FOLDER.resolve(strict=True))
    except OSError:
        return False


def number_of(name: str) -> int | None:
    """The RFC number in a file name, or None for a record not yet numbered (XXXX)."""
    m = RECORD.match(name)
    return int(m.group(1)) if m and m.group(1).isdigit() else None


def entries() -> list[Path]:
    try:
        return sorted(FOLDER.iterdir())
    except OSError:
        return []


def records() -> list[Path]:
    return [p for p in entries() if RECORD.match(p.name) and is_plain_file(p)]


def slugify(title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")[:60].strip("-")


def clean_one_line(text: str) -> str:
    """Drop invisible format characters, then collapse whitespace so a value stays on one line."""
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return re.sub(r"[\x00-\x1f\x7f\s]+", " ", text).strip()


def _git(*args: str) -> str:
    """Read-only git plumbing that runs no program named in repository config."""
    hardened = ["-c", "core.fsmonitor=", "-c", "core.hooksPath=" + os.devnull, "-c", "protocol.allow=never"]
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"}
    try:
        out = subprocess.run(["git", "-C", str(FOLDER), *hardened, *args],
                             capture_output=True, text=True, timeout=10, env=env)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out.stdout if out.returncode == 0 else ""


def remote_names() -> set[str] | None:
    """File names on the last-fetched default branch of `upstream` and `origin`, or None if unknown."""
    top = _git("rev-parse", "--show-toplevel").strip()
    if not top:
        return None
    folder = Path(os.path.relpath(FOLDER.resolve(), Path(top).resolve())).as_posix()
    found: set[str] = set()
    seen = False
    for remote in ("upstream", "origin"):
        refs = [_git("symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD").strip(),
                f"{remote}/main", f"{remote}/master"]
        ref = next((r for r in refs if r and _git("rev-parse", "--verify", "--quiet", r).strip()), "")
        if not ref:
            continue
        seen = True
        found |= {n for n in _git("ls-tree", "--full-tree", "--name-only", f"{ref}:{folder}").split("\n") if n}
    return found if seen else None


def number_in_use(number: int) -> str | None:
    return next((p.name for p in records() if number_of(p.name) == number), None)


def read_text(path: Path) -> str:
    """Read a plain file in the RFC folder, capped in size."""
    if not is_plain_file(path):
        raise OSError("not a regular file inside the RFC folder")
    with open(path, "rb") as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise OSError(f"larger than {MAX_BYTES} bytes")
    return data.decode("utf-8")


def next_number() -> int:
    """One more than the highest number in the folder and on the last-fetched default branches."""
    remote = {n for name in (remote_names() or set()) if (n := number_of(name)) is not None}
    used = {n for p in records() if (n := number_of(p.name)) is not None} | remote
    return max(used, default=0) + 1


def cmd_next(args: argparse.Namespace) -> int:
    number = next_number()
    if number > MAX_NUMBER:
        print(f"error: the next number would pass {MAX_NUMBER}", file=sys.stderr)
        return 2
    print(f"{number:04d}")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    title = clean_one_line(args.title)
    slug = slugify(args.slug or title)
    if not slug:
        print("error: no ASCII letters or digits in the title; pass --slug", file=sys.stderr)
        return 2
    if args.number is not None and not 1 <= args.number <= MAX_NUMBER:
        print(f"error: --number must be between 1 and {MAX_NUMBER}", file=sys.stderr)
        return 2
    if args.number is None:
        number = next_number()
        if number > MAX_NUMBER:
            print(f"error: the next number would pass {MAX_NUMBER}; pass --number", file=sys.stderr)
            return 2
    else:
        number = args.number
    if (clash := number_in_use(number)):
        print(f"error: number {number:04d} is already used by {show(clash)}; nothing written", file=sys.stderr)
        return 1
    template = SCRIPT_DIR / "template.md.tmpl"
    try:
        if template.is_symlink() or not template.is_file():
            raise OSError("not a regular file")
        text = template.read_text(encoding="utf-8")
    except OSError:
        print("error: template.md.tmpl is missing or not a regular file; nothing written", file=sys.stderr)
        return 2
    # Literal placeholders keep the template readable and let a person or an agent fill it by hand.
    # str.replace with count=1 never re-expands a title that happens to contain a placeholder.
    number_text = f"{number:04d}"
    text = text.replace("# RFC-NNNN: <short title>", f"# RFC-{number_text}: {title}", 1)
    text = text.replace("YYYY-MM-DD", datetime.date.today().isoformat(), 1)
    if (author := clean_one_line(args.author)):
        text = text.replace("<account-handle>", author, 1)  # otherwise leave the neutral placeholder
    target = FOLDER / f"{number_text}-{slug}.md"
    try:
        with open(target, "x", encoding="utf-8") as handle:
            handle.write(text)
    except FileExistsError:
        print(f"error: {show(target.name)} already exists; nothing written", file=sys.stderr)
        return 1
    print(f"Created {show(target)}")
    if args.number is None:
        print("Number: next free in this folder and your last fetch of upstream/origin.")
    return 0


def cmd_renumber(args: argparse.Namespace) -> int:
    given = Path(args.file)
    source = given.parent.resolve() / given.name  # resolve the folder, never the file itself
    if (source.parent != FOLDER.resolve() or not RECORD.match(source.name)
            or not 1 <= args.number <= MAX_NUMBER or not is_plain_file(source)):
        print("error: give an RFC file in this folder (not a link) and a number from 1 to "
              f"{MAX_NUMBER}", file=sys.stderr)
        return 2
    if (clash := number_in_use(args.number)):
        print(f"error: number {args.number:04d} is already used by {show(clash)}; nothing changed", file=sys.stderr)
        return 1
    target = FOLDER / f"{args.number:04d}-{source.name.split('-', 1)[1]}"
    with open(source, encoding="utf-8", newline="") as handle:
        text = handle.read(MAX_BYTES + 1)
    if len(text) > MAX_BYTES:
        print(f"error: {show(source.name)} is larger than {MAX_BYTES} bytes; nothing changed", file=sys.stderr)
        return 2
    text = re.sub(r"^# RFC-(\d+|XXXX):", f"# RFC-{args.number:04d}:", text, count=1, flags=re.MULTILINE)
    try:
        with open(target, "x", encoding="utf-8", newline="") as handle:
            handle.write(text)
        source.unlink()
    except OSError:
        if target.exists() and source.exists():
            target.unlink()  # never leave two copies behind
        raise
    print(f"Renamed {show(source.name)} -> {show(target.name)}. Links to the old number are not rewritten.")
    return 0


FIELD = re.compile(r"^- \*\*[^*]+:\*\*")


def counted_text(text: str) -> str:
    """Text that counts toward the length warning: everything but the title and the header field block.

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
    m = re.search(r"^-?\s*\*\*Status:\*\*\s*[*_]*(\w+)", text, re.MULTILINE)
    return m.group(1).lower() if m else ""


def cmd_check(args: argparse.Namespace) -> int:
    paths = [Path(f) for f in args.files] or records()
    warnings = 0
    for p in entries():
        if p.is_symlink():
            print(f"warning: {show(p.name)} is a link and is ignored.")
            warnings += 1
        elif p.name in KNOWN_FILES or p.is_dir():
            continue
        elif p.name.endswith(CODE_SUFFIXES):
            print(f"warning: unexpected code file {show(p.name)} beside the script.")
            warnings += 1
        elif not KNOWN_NAME.match(p.name) and not p.name.endswith("-research.md"):
            print(f"warning: unexpected file name {show(p.name)}.")
            warnings += 1
    owners: dict[int, list[str]] = collections.defaultdict(list)
    for p in records():
        if (n := number_of(p.name)) is not None:
            owners[n].append(show(p.name))
    for number, names in sorted(owners.items()):
        if len(names) > 1:
            print(f"warning: number {number:04d} is used by {', '.join(names)}.")
            warnings += 1
    remote = remote_names()
    unreadable = 0
    for path in paths:
        try:
            text = read_text(path)
        except (OSError, UnicodeDecodeError) as exc:
            print(f"error: cannot read {show(path.name)}: {show(exc)}", file=sys.stderr)
            unreadable += 1
            continue
        if status_word(text) in DECIDED:
            if remote is not None and path.name not in remote:
                print(f"warning: {show(path.name)} is marked decided but is not on the default branch.")
                warnings += 1
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
    global FOLDER
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
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
    check = sub.add_parser("check", help="warn about in-flight RFCs that are too long or incomplete")
    check.add_argument("files", nargs="*")
    check.add_argument("--strict", action="store_true", help="exit 1 when a warning is raised")
    check.set_defaults(run=cmd_check)
    args = parser.parse_args(argv)
    if args.dir:
        FOLDER = Path(args.dir)
        if not FOLDER.is_dir():
            print("error: --dir is not a folder", file=sys.stderr)
            return 2
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
