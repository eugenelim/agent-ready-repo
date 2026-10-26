#!/usr/bin/env python3
"""Show, preview and write a repository's governance files under confinement.

Usage:
    python3 governance.py show    --root <repo> --target <target>
    python3 governance.py preview --root <repo> --target <target>
                                  [--after-line <n>] [--approved-by <text>]
    python3 governance.py write   --root <repo> --target <target>
                                  [--after-line <n>] --current <absent|sha256:hex>
                                  --proposed sha256:<hex> [--approved-by <text>]

``preview`` and ``write`` read the proposed input from standard input.  The
targets are a fixed allowlist: three governance files, three CODEOWNERS files
and two charter files.  Every read and the one write go through the co-located
``file_safety.py``.  A refusal prints ``refused: <reason>`` and exits 3; a
usage error exits 2; success exits 0.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import posixpath
import re
import stat as _stat
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, NoReturn

_SCRIPT_DIR = Path(__file__).resolve().parent
_file_safety_module: Any | None = None


def _end_line(text: str) -> str:
    """Return *text* ending in exactly the newline it needs before an end marker."""
    return text if text.endswith("\n") or not text else text + "\n"


def _get_file_safety() -> Any:
    """Load the co-located file_safety.py at most once and return it."""
    global _file_safety_module
    if _file_safety_module is not None:
        return _file_safety_module
    path = _SCRIPT_DIR / "file_safety.py"
    try:
        inspected = os.lstat(path)
    except OSError as exc:
        raise ImportError(f"required helper unavailable: {path.name}") from exc
    if not _stat.S_ISREG(inspected.st_mode):
        raise ImportError(f"required helper is not a regular file: {path.name}")
    name = "_new_rfc_governance_file_safety"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:  # pragma: no cover
            raise ImportError(f"required helper cannot be loaded: {path.name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    except BaseException:  # pragma: no cover
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    required = {
        "UnsafeContentError", "BoundExceeded",
        "read_confined_regular_file", "write_confined_regular_file",
    }
    missing = required - set(vars(module))
    if missing:  # pragma: no cover
        sys.modules.pop(name, None)
        raise ImportError(f"required helper is incomplete: {', '.join(sorted(missing))}")
    _file_safety_module = module
    return module


# -- Constants ---------------------------------------------------------------

GOVERNANCE_TARGETS = ("GOVERNANCE.md", "docs/GOVERNANCE.md", ".github/GOVERNANCE.md")
CODEOWNERS_TARGETS = (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")
CHARTER_TARGETS = ("docs/CHARTER.md", "CHARTER.md")
DEFAULT_MODEL = "single maintainer or small group by consensus"
MAX_INPUT_BYTES = 65_536
MAX_READ_BYTES = 2_999_999
MAX_APPROVAL_CODE_POINTS = 200
_GIT_ENV_OVERRIDES = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")

# Unicode Default_Ignorable_Code_Point members outside category Cf, as ranges.
HIDDEN_RANGES: tuple[tuple[int, int], ...] = (
    (0x00AD, 0x00AD), (0x034F, 0x034F), (0x115F, 0x1160), (0x17B4, 0x17B5),
    (0x180B, 0x180F), (0x3164, 0x3164), (0xFE00, 0xFE0F), (0xFFA0, 0xFFA0),
    (0xFFF0, 0xFFF8), (0x1BCA0, 0x1BCA3), (0x1D173, 0x1D17A), (0xE0000, 0xE0FFF),
)
_HIDDEN_CATEGORIES = frozenset({"Cf", "Zl", "Zp", "Cn", "Co", "Cs"})
_BIDI_REFUSED = frozenset(
    {0x061C, 0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A)}
)
# Code points with the Unicode White_Space property.
_WHITE_SPACE = frozenset(
    {0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x20, 0x85, 0xA0, 0x1680, *range(0x2000, 0x200B),
     0x2028, 0x2029, 0x202F, 0x205F, 0x3000}
)
_USER_PART = re.compile(r"[A-Za-z0-9](?:-?[A-Za-z0-9])*")
_TEAM_PART = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}")
_MODEL_LINE = re.compile(r"- \*\*Decision model:\*\* (\S.*)")
_LINK_LINE = re.compile(
    r"Roles and decision-making: \[GOVERNANCE\.md\]\(([^\s()]+)\)\n?"
)
_MD_LINK = re.compile(r"\]\(([^()\s]*)\)")
_URL_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*:")
_CURRENT_ARG = re.compile(r"absent|sha256:[0-9a-f]{64}")
_PROPOSED_ARG = re.compile(r"sha256:[0-9a-f]{64}")
_DIGITS = re.compile(r"[0-9]+")
_REASONS = (
    "codeowners ownership change",
    "a GOVERNANCE.md is present",
    "decision model is not the default",
)


class Refusal(Exception):
    """A checked refusal; ``reason`` is the fixed token printed to the user."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


# -- Character rules ---------------------------------------------------------


def is_hidden(char: str) -> bool:
    """Whether *char* is a hidden code point shown in visible form."""
    code = ord(char)
    category = unicodedata.category(char)
    if category == "Cc":
        return char not in "\t\n"
    if category in _HIDDEN_CATEGORIES:
        return True
    return any(low <= code <= high for low, high in HIDDEN_RANGES)


def visible_form(text: str) -> tuple[str, int]:
    """Replace each hidden code point with ``⟨U+XXXX⟩``; return text and count."""
    pieces: list[str] = []
    count = 0
    for char in text:
        if is_hidden(char):
            pieces.append(f"⟨U+{ord(char):04X}⟩")
            count += 1
        else:
            pieces.append(char)
    return "".join(pieces), count


def has_refused_character(text: str) -> bool:
    """Whether *text* holds a refused character."""
    for index, char in enumerate(text):
        if char == "\r":
            if text[index + 1:index + 2] != "\n":
                return True
            continue
        category = unicodedata.category(char)
        if category == "Cc" and char not in "\t\n":
            return True
        if category in ("Zl", "Zp") or ord(char) in _BIDI_REFUSED:
            return True
    return False


# -- CODEOWNERS --------------------------------------------------------------


def is_handle(text: str) -> bool:
    """Whether *text* is ``@user`` or ``@user/team``."""
    if not text.startswith("@"):
        return False
    user, slash, team = text[1:].partition("/")
    if not 1 <= len(user) <= 39 or _USER_PART.fullmatch(user) is None:
        return False
    return not slash or _TEAM_PART.fullmatch(team) is not None


def rule_lines(content: str) -> list[tuple[int, str, list[str], bool]]:
    """Return ``(line number, pattern, owners, valid)`` for each rule line."""
    found: list[tuple[int, str, list[str], bool]] = []
    for number, raw in enumerate(content.split("\n"), start=1):
        line = raw[:-1] if raw.endswith("\r") else raw
        stripped = line.strip(" \t")
        if not stripped or stripped.startswith("#"):
            continue
        tokens = re.split(r"[ \t]+", stripped)
        pattern, owners = tokens[0], tokens[1:]
        valid = (
            not any(ch in pattern for ch in "#\\[]")
            and not any(ord(ch) in _WHITE_SPACE for ch in pattern)
            and not pattern.startswith("!")
            and all(is_handle(owner) for owner in owners)
        )
        found.append((number, pattern, owners, valid))
    return found


def _valid_rules(content: str | None) -> list[tuple[str, tuple[str, ...]]]:
    """The rule list of CODEOWNERS content: pairs of pattern and owners."""
    if content is None:
        return []
    return [(pattern, tuple(owners)) for _, pattern, owners, _ in rule_lines(content)]


def _github_reads(states: dict[str, str | None]) -> str | None:
    """The first present codeowners target, or None."""
    for path in CODEOWNERS_TARGETS:
        if states.get(path) is not None:
            return path
    return None


def _effective_rules(states: dict[str, str | None]) -> list[tuple[str, tuple[str, ...]]]:
    """The rule list of the file GitHub reads."""
    reads = _github_reads(states)
    return _valid_rules(states[reads]) if reads else []


def _has_invalid_rule(content: str | None) -> bool:
    """Whether *content* holds a rule line that is not valid."""
    return content is not None and any(not ok for *_, ok in rule_lines(content))


def is_ownership_change(
    before: dict[str, str | None], target: str, proposed: str
) -> bool:
    """Whether writing *proposed* to *target* changes ownership."""
    after = {**before, target: proposed}
    reads_before = _github_reads(before)
    return (
        _valid_rules(before[target]) != _valid_rules(proposed)
        or reads_before != _github_reads(after)
        or _effective_rules(before) != _effective_rules(after)
        or _has_invalid_rule(before[target])
        or (reads_before is not None and _has_invalid_rule(before[reads_before]))
    )


def _render_rules(content: str) -> list[str]:
    """Render each rule line as GitHub would read it."""
    lines = []
    for number, pattern, owners, valid in rule_lines(content):
        if valid:
            lines.append(f"{number}: {pattern} → {' '.join(owners) or '(no owners)'}")
        else:
            lines.append(f"{number}: skipped")
    return lines


# -- Governance draft --------------------------------------------------------


def _section(lines: list[str], heading: str) -> list[str] | None:
    """Lines under a level-2 *heading*, up to the next level-2 heading."""
    for index, line in enumerate(lines):
        if line.rstrip(" \t") == heading:
            body = []
            for later in lines[index + 1:]:
                if later.startswith("## "):
                    break
                body.append(later)
            return body
    return None


def decision_model(text: str) -> str | None:
    """The decision model value of a draft, or None without exactly one marker."""
    found = [
        match.group(1).strip()
        for line in text.split("\n")
        if (match := _MODEL_LINE.fullmatch(line.rstrip("\r")))
    ]
    return found[0] if len(found) == 1 else None


def is_governance_draft(text: str) -> bool:
    """Whether *text* is a governance draft."""
    if decision_model(text) is None:
        return False
    lines = [line.rstrip("\r") for line in text.split("\n")]
    maintainers = _section(lines, "## Maintainers")
    if maintainers is None:
        return False
    items = [line for line in maintainers if line.startswith("- ")]
    if not items or not all(is_handle(item[2:].strip(" \t")) for item in items):
        return False
    owned = _section(lines, "## Owned paths")
    if owned is None:
        return False
    body = "\n".join(owned)
    return all(f"`{name}`" in body for name in ("GOVERNANCE.md", "CODEOWNERS", "AGENT_RULES.md"))


# -- Charter -----------------------------------------------------------------


def _is_governance_path(charter_dir: str, path: str) -> bool:
    """Whether *path*, joined to the charter's directory, is a governance target."""
    return posixpath.normpath(posixpath.join(charter_dir, path)) in GOVERNANCE_TARGETS


def _is_link_line(text: str, charter_dir: str) -> bool:
    """Whether *text* is a link line for a charter in *charter_dir*."""
    match = _LINK_LINE.fullmatch(text)
    if match is None:
        return False
    path = match.group(1)
    if path.startswith("/") or _URL_SCHEME.match(path):
        return False
    return _is_governance_path(charter_dir, path)


def _charter_links_to_governance(charter: str, charter_dir: str) -> bool:
    """Whether the charter already links to a governance target."""
    return any(_is_governance_path(charter_dir, m.group(1)) for m in _MD_LINK.finditer(charter))


def _line_count(text: str) -> int:
    """Number of lines: each ``\\n`` plus one for an unterminated last line."""
    return text.count("\n") + (1 if text and not text.endswith("\n") else 0)


def _insert_link(current: str, link_line: str, after: int) -> str:
    """Insert *link_line* after line *after* of *current*."""
    ends = current.split("\n")
    pieces = [part + "\n" for part in ends[:-1]] + ([ends[-1]] if ends[-1] else [])
    head = "".join(pieces[:after])
    if after == len(pieces) and current and not current.endswith("\n"):
        head += "\n"
    return head + link_line + "\n" + "".join(pieces[after:])


# -- Reading -----------------------------------------------------------------


def _present(root: Path, relative: str) -> bool:
    """Whether *relative* exists under *root*; an unsafe component refuses.

    A missing component is absence.  A component that is a link, or a
    directory position held by a file, is never reported as absent.
    """
    parts = relative.split("/")
    current = root
    for index, part in enumerate(parts):
        current = current / part
        try:
            inspected = os.lstat(current)
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise Refusal("unsafe-path") from exc
        if index < len(parts) - 1 and not _stat.S_ISDIR(inspected.st_mode):
            raise Refusal("unsafe-path")
    return True


def _read_files(root: Path, targets: tuple[str, ...]) -> dict[str, bytes | None]:
    """Read each target through the confined helper; None marks an absent file."""
    helper = _get_file_safety()
    found: dict[str, bytes | None] = {}
    for relative in targets:
        if not _present(root, relative):
            found[relative] = None
            continue
        try:
            found[relative] = helper.read_confined_regular_file(
                root, root / relative, max_bytes=MAX_READ_BYTES
            )
        except helper.BoundExceeded as exc:
            raise Refusal("too-large") from exc
        except helper.UnsafeContentError as exc:
            raise Refusal("unsafe-path") from exc
    return found


def _decode_current(raw: bytes | None) -> str | None:
    """Decode current bytes losslessly; invalid bytes become lone surrogates."""
    return None if raw is None else raw.decode("utf-8", errors="surrogateescape")


def _digest(data: bytes) -> str:
    """``sha256:<hex>`` of *data*."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _kind(target: str) -> str:
    """The kind of an allowed target."""
    if target in GOVERNANCE_TARGETS:
        return "governance"
    return "codeowners" if target in CODEOWNERS_TARGETS else "charter"


def _reads_for(target: str) -> tuple[str, ...]:
    """The files a run reads for *target*."""
    if target in CODEOWNERS_TARGETS:
        return CODEOWNERS_TARGETS
    return GOVERNANCE_TARGETS + CHARTER_TARGETS


# -- Root check --------------------------------------------------------------


def _check_root(root_arg: str, cwd: Path) -> Path:
    """Return the resolved root when it is the worktree top level, else refuse."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_OVERRIDES}
    try:
        done = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd, env=env, stdin=subprocess.DEVNULL, capture_output=True,
            timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refusal("root-not-worktree") from exc
    if done.returncode != 0:
        raise Refusal("root-not-worktree")
    top = os.fsdecode(done.stdout).rstrip("\r\n")
    try:
        resolved = (cwd / root_arg).resolve()
        if not top or Path(top).resolve() != resolved:
            raise Refusal("root-not-worktree")
    except (OSError, RuntimeError) as exc:
        raise Refusal("root-not-worktree") from exc
    return resolved


# -- Blocks ------------------------------------------------------------------


def _show_block(target: str, raw: bytes | None) -> str:
    """The show block for *target*."""
    text, count = visible_form(_decode_current(raw) or "")
    current = "absent" if raw is None else _digest(raw)
    return (
        f"GOVERNANCE CURRENT:\n- Target: {target}\n- Current: {current}\n"
        f"- Characters made visible: {count}\n--- content ---\n"
        f"{_end_line(text)}--- end content ---\n"
    )


def _preview_block(
    *, target: str, kind: str, current: str, proposed_bytes: bytes, proposed_text: str,
    approval: str, approved_by: str | None, states: dict[str, str | None],
    inserted_at: int | None,
) -> str:
    """The preview block."""
    content, count = visible_form(proposed_text)
    approved, _ = visible_form(approved_by) if approved_by is not None else ("none", 0)
    reads_now = ""
    extra: list[str] = []
    if kind == "codeowners":
        after = {**states, target: proposed_text}
        others = [p for p in CODEOWNERS_TARGETS if p != target and states[p] is not None]
        now_text, now_count = visible_form(
            "\n".join(_render_rules(states[_github_reads(states) or ""] or ""))
            if _github_reads(states) else ""
        )
        count += now_count
        proposed_rules = rule_lines(proposed_text)
        no_owners = sum(1 for _, _, owners, _ in proposed_rules if not owners)
        extra = [
            f"- GitHub reads: {_github_reads(after) or 'none'}",
            f"- Also present: {', '.join(others) or 'none'}",
            f"- Rules with no owners: {no_owners}",
        ]
        reads_now_lines = now_text.split("\n") if now_text else []
        as_read, _ = visible_form("\n".join(_render_rules(proposed_text)))
        reads_now = (
            "--- GitHub reads now ---\n"
            + "".join(f"{line}\n" for line in reads_now_lines)
            + "--- as GitHub reads it ---\n"
            + "".join(f"{line}\n" for line in (as_read.split("\n") if as_read else []))
            + "--- end ---\n"
        )
    if kind == "charter":
        extra = [f"- Inserted at line: {inserted_at}"]
    head = [
        "GOVERNANCE PREVIEW:", f"- Target: {target}", f"- Kind: {kind}",
        f"- Current: {current}",
        f"- Proposed: {_digest(proposed_bytes)} ({len(proposed_bytes)} bytes)",
        f"- Approval required: {approval}", f"- Approved by: {approved}",
        f"- Characters made visible: {count}", *extra,
    ]
    body = f"\n--- content ---\n{_end_line(content)}--- end content ---\n"
    return "\n".join(head) + body + reads_now


# -- Command line ------------------------------------------------------------


class _Parser(argparse.ArgumentParser):
    """A parser whose usage errors carry no echoed argument text."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        sys.stderr.write("governance.py: usage error\n")
        raise SystemExit(2)


def _build_parser() -> argparse.ArgumentParser:
    """The command-line parser."""
    parser = _Parser(prog="governance.py", description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    for name in ("show", "preview", "write"):
        sub = subs.add_parser(name)
        sub.add_argument("--root", required=True)
        sub.add_argument("--target", required=True)
        if name != "show":
            sub.add_argument("--after-line")
            sub.add_argument("--approved-by")
        if name == "write":
            sub.add_argument("--current", required=True)
            sub.add_argument("--proposed", required=True)
    return parser


def _read_stdin(stdin: Any) -> bytes:
    """Read at most one byte more than the input limit."""
    data = stdin.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise Refusal("too-large")
    return bytes(data)


def _validate_approval(value: str | None) -> None:
    """Refuse an unusable ``--approved-by`` value."""
    if value is None:
        return
    if (
        not value
        or len(value) > MAX_APPROVAL_CODE_POINTS
        or "\n" in value
        or has_refused_character(value)
    ):
        raise Refusal("invalid-approval")


def _run(args: argparse.Namespace, stdin: Any, cwd: Path) -> str:
    """Run one subcommand and return its stdout text, or raise a refusal."""
    root = _check_root(args.root, cwd)
    target: str = args.target
    if target not in GOVERNANCE_TARGETS + CODEOWNERS_TARGETS + CHARTER_TARGETS:
        raise Refusal("target-not-allowed")
    kind = _kind(target)
    command: str = args.command
    if command == "show":
        return _show_block(target, _read_files(root, _reads_for(target))[target])

    data = _read_stdin(stdin)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Refusal("not-utf8") from exc
    if has_refused_character(text):
        raise Refusal("refused-character")
    approved_by: str | None = args.approved_by
    _validate_approval(approved_by)

    raw = _read_files(root, _reads_for(target))
    states = {path: _decode_current(raw[path]) for path in raw}
    current_raw = raw[target]
    current = "absent" if current_raw is None else _digest(current_raw)

    inserted_at: int | None = None
    if kind == "governance":
        if not is_governance_draft(text):
            raise Refusal("governance-draft-incomplete")
        proposed_text = text
    elif kind == "codeowners":
        for number, _, _, valid in rule_lines(text):
            if not valid:
                raise Refusal(f"invalid-codeowners-line {number}")
        proposed_text = text
    else:
        charters = [p for p in CHARTER_TARGETS if states[p] is not None]
        if not charters:
            raise Refusal("charter-missing")
        if target != charters[0]:
            raise Refusal("not-the-charter")
        charter_dir = posixpath.dirname(target)
        if not _is_link_line(text, charter_dir):
            raise Refusal("not-a-link-line")
        current_text = states[target] or ""
        after = args.after_line
        if (
            after is None
            or _DIGITS.fullmatch(after) is None
            or int(after) > _line_count(current_text)
        ):
            raise Refusal("bad-line-number")
        if _charter_links_to_governance(current_text, charter_dir):
            raise Refusal("charter-already-links")
        link = text[:-1] if text.endswith("\n") else text
        proposed_text = _insert_link(current_text, link, int(after))
        inserted_at = int(after) + 1
    proposed_bytes = proposed_text.encode("utf-8", errors="surrogateescape")

    reason: str | None = None
    if kind == "codeowners" and is_ownership_change(states, target, proposed_text):
        reason = _REASONS[0]
    elif kind == "governance" and any(states[p] is not None for p in GOVERNANCE_TARGETS):
        reason = _REASONS[1]
    elif kind == "governance" and decision_model(text) != DEFAULT_MODEL:
        reason = _REASONS[2]

    if command == "preview":
        return _preview_block(
            target=target, kind=kind, current=current, proposed_bytes=proposed_bytes,
            proposed_text=proposed_text,
            approval="no" if reason is None else f"yes — {reason}",
            approved_by=approved_by, states=states, inserted_at=inserted_at,
        )

    if _digest(proposed_bytes) != args.proposed:
        raise Refusal("bytes-differ-from-preview")
    if current != args.current:
        raise Refusal("target-changed")
    if reason is not None and approved_by is None:
        raise Refusal("approval-required")
    helper = _get_file_safety()
    expect = None if args.current == "absent" else args.current.removeprefix("sha256:")
    try:
        helper.write_confined_regular_file(
            root, root / target, proposed_bytes, expect_sha256=expect
        )
    except helper.UnsafeContentError as exc:
        raise Refusal("target-changed") from exc
    return f"written: {target} {_digest(proposed_bytes)}\n"


def _use_utf8_streams() -> None:
    """Reconfigure stdout and stderr to UTF-8 before anything is printed."""
    for stream, errors in ((sys.stdout, "strict"), (sys.stderr, "backslashreplace")):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors=errors)


def main(argv: list[str], stdin: Any = None, cwd: Path | None = None) -> int:
    """Run the command line; *stdin* is bytes or an object with ``read``."""
    _use_utf8_streams()
    try:
        args = _build_parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    if isinstance(stdin, (bytes, bytearray)):
        stdin = _BytesStdin(bytes(stdin))
    elif stdin is None:
        stdin = sys.stdin.buffer
    if args.command == "write" and (
        _CURRENT_ARG.fullmatch(args.current) is None
        or _PROPOSED_ARG.fullmatch(args.proposed) is None
    ):
        sys.stderr.write("governance.py: usage error\n")
        return 2
    try:
        out = _run(args, stdin, cwd or Path.cwd())
    except Refusal as refusal:
        sys.stdout.write(f"refused: {refusal.reason}\n")
        return 3
    sys.stdout.write(out)
    return 0


class _BytesStdin:
    """A minimal binary reader over bytes."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self, size: int = -1) -> bytes:
        """Return up to *size* bytes."""
        return self._data if size < 0 else self._data[:size]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
