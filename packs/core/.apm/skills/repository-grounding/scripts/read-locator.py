#!/usr/bin/env python3
"""Read a provider-returned file locator through confined filesystem access.

This is the one route by which a provider-returned file locator is read.
The locator arrives as the standard base64 encoding of its UTF-8 bytes so
no locator text ever appears raw on a command line. The alphabet
(A-Z, a-z, 0-9, +, /, =) means nothing to a POSIX shell, PowerShell, or
cmd.exe: no locator text can end a quote, run a command, or expand a variable.

Usage::

    read-locator.py --root <repo> [--approved-root <dir>]... --locator-b64 <base64>

Exit codes:
  0  locator read; stdout: received: / root: / source: lines then file bytes
  2  usage error (missing or repeated --locator-b64); usage on stderr, nothing
     on stdout
  3  locator refused; stdout: received: / refused: lines
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path
from typing import NamedTuple

# ── co-located scripts directory ────────────────────────────────────────────

_SCRIPTS = Path(__file__).resolve().parent


# ── lazy-loaded dependencies ─────────────────────────────────────────────────

def _load_explore_grounding():
    """Load explore-grounding.py once; cached in sys.modules after first call."""
    name = "packs_core_repository_grounding_explore_grounding"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(
        name, _SCRIPTS / "explore-grounding.py"
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _load_file_safety():
    """Load the co-located file_safety.py once; cached in sys.modules."""
    name = "packs_core_repository_grounding_file_safety"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(
        name, _SCRIPTS / "file_safety.py"
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# MAX_READ_BYTES is loaded from explore-grounding.py; not copied here.
MAX_READ_BYTES: int = _load_explore_grounding().MAX_READ_BYTES

# ── result type ──────────────────────────────────────────────────────────────


class LocatorResult(NamedTuple):
    """Outcome of reading or refusing one locator.

    Fields:
        status: "read" or "refused"
        reason: refusal reason string, or None when status is "read"
        root:   absolute root Path that served the file, or None
        path:   path relative to root on success, or None
        data:   raw file bytes on success, or None
    """

    status: str
    reason: str | None
    root: Path | None
    path: Path | None
    data: bytes | None


# ── internal helpers ─────────────────────────────────────────────────────────

_DRIVE_LETTER_PATH = re.compile(r"^[A-Za-z]:[/\\]")
_SCHEME_PREFIX = re.compile(r"^([A-Za-z][A-Za-z0-9+\-.]*):(.*)$", re.DOTALL)
_LINE_SUFFIX = re.compile(r":(\d+)(?::\d+)?$")
_HASH_L_SUFFIX = re.compile(r"#L\d+$")
_DIGIT_AFTER_COLON = re.compile(r"^\d+(?::\d+)?$")


def _has_splitlines_char(text: str) -> bool:
    """Return True if text contains any character str.splitlines treats as a boundary.

    str.splitlines() strips those characters; joining the result and comparing
    to the original detects any of them: LF, CR, VT, FF, FS, GS, RS, U+0085,
    U+2028, and U+2029.
    """
    return "".join(text.splitlines()) != text


def _has_parent_segment(path_text: str) -> bool:
    """Return True if path_text contains a '..' component using / or \\ as separators."""
    normalized = path_text.replace("\\", "/")
    return ".." in normalized.split("/")


def _strip_line_suffix(text: str) -> str:
    """Strip a trailing :<line>, :<line>:<col>, or #L<line> suffix from a path string."""
    m = _HASH_L_SUFFIX.search(text)
    if m:
        return text[: m.start()]
    m = _LINE_SUFFIX.search(text)
    if m:
        return text[: m.start()]
    return text


def _strip_uri_line_suffix(text: str) -> str:
    """Strip a trailing :<line> or :<line>:<col> suffix from a URI string."""
    m = _LINE_SUFFIX.search(text)
    if m:
        return text[: m.start()]
    return text


# ── public API ───────────────────────────────────────────────────────────────


def read_locator(
    root: Path | str,
    locator: str,
    approved_roots: tuple[Path | str, ...] | list[Path | str] = (),
) -> LocatorResult:
    """Read a provider-returned locator against confined filesystem roots.

    Parameters
    ----------
    root:
        Repository root. Made absolute with os.path.abspath (no link resolution
        inside it).
    locator:
        Decoded locator text. The CLI decodes it from base64+UTF-8; callers
        pass the already-decoded string.
    approved_roots:
        Additional roots the user or calling workflow explicitly approved. Never
        populated from provider output.

    Returns
    -------
    LocatorResult with status "read" or "refused" and supporting fields.
    """
    fs = _load_file_safety()
    UnsafeContentError = fs.UnsafeContentError
    BoundExceeded = fs.BoundExceeded
    read_confined_regular_file = fs.read_confined_regular_file

    # ── step 0: line-boundary check on the locator ──────────────────────────
    # Refuse any character str.splitlines treats as a line boundary (LF, CR,
    # VT, FF, FS, GS, RS, U+0085, U+2028, U+2029).
    if _has_splitlines_char(locator):
        return LocatorResult("refused", "line-break", None, None, None)

    # ── step 1: classify the locator form ───────────────────────────────────
    # Priority: drive-letter path > file URI > digit-suffix path > scheme > plain path
    is_drive_path = False
    form: str  # "path" or "uri"

    if _DRIVE_LETTER_PATH.match(locator):
        # C:\ or C:/ — a drive-letter path
        form = "path"
        is_drive_path = True
    else:
        m = _SCHEME_PREFIX.match(locator)
        if m:
            scheme = m.group(1)
            after_colon = m.group(2)
            if scheme.lower() == "file":
                form = "uri"
            elif _DIGIT_AFTER_COLON.match(after_colon):
                # e.g. src.py:3 or Makefile:12:4 — colon is a line suffix
                form = "path"
            else:
                return LocatorResult("refused", "scheme", None, None, None)
        else:
            form = "path"

    # ── step 2: split before decoding ───────────────────────────────────────
    if form == "uri":
        # Remove fragment (first raw #)
        raw = locator
        frag_idx = raw.find("#")
        if frag_idx != -1:
            raw = raw[:frag_idx]

        # Strip trailing :<line> or :<line>:<col>
        raw = _strip_uri_line_suffix(raw)

        # Parse authority from "file://[authority]/..."
        # Anything after "file:" is the hier-part.
        hier = raw[len("file:"):]
        if hier.startswith("//"):
            rest = hier[2:]  # drop "//"
            slash_pos = rest.find("/")
            if slash_pos == -1:
                authority = rest
                path_str = ""
            else:
                authority = rest[:slash_pos]
                path_str = rest[slash_pos:]  # retains leading /
        else:
            # "file:/path" or "file:relative" — no authority section
            authority = ""
            path_str = hier

        if authority.lower() not in ("", "localhost"):
            return LocatorResult("refused", "authority", None, None, None)

        # Percent-decode the path exactly once
        path_str = urllib.parse.unquote(path_str)

        # On Windows, a URI path of the form /C:/... drops its leading /
        if os.name == "nt" and re.match(r"^/[A-Za-z]:[/\\]", path_str):
            path_str = path_str[1:]

    else:
        # Plain path form: strip line suffix, never percent-decode
        path_str = _strip_line_suffix(locator)

    # ── step 3: check the final path ────────────────────────────────────────
    if "\x00" in path_str:
        return LocatorResult("refused", "nul", None, None, None)
    if _has_splitlines_char(path_str):
        return LocatorResult("refused", "line-break", None, None, None)
    if _has_parent_segment(path_str):
        return LocatorResult("refused", "parent-segment", None, None, None)

    # ── step 4: place the path ──────────────────────────────────────────────
    abs_root = str(Path(root).resolve())
    all_roots: list[str] = [abs_root] + [
        str(Path(r).resolve()) for r in approved_roots
    ]

    # On POSIX, a drive-letter path or a drive-letter URI path (e.g. /C:/x
    # that was not stripped because we are not on Windows) can name no file
    # under any real POSIX root.
    if is_drive_path and os.name != "nt":
        return LocatorResult("refused", "outside-roots", None, None, None)

    # Build the absolute candidate path
    candidate = os.path.normpath(
        path_str if Path(path_str).is_absolute() else str(Path(abs_root) / path_str)
    )

    # Match candidate against each root (absolute and realpath spellings)
    matched_root: str | None = None
    for r in all_roots:
        abs_r = r
        real_r = os.path.realpath(abs_r)
        if os.name == "nt":
            # Windows: case-insensitive comparison via normcase
            cand_nc = os.path.normcase(candidate)
            abs_r_nc = os.path.normcase(abs_r)
            real_r_nc = os.path.normcase(real_r)
            if cand_nc in (abs_r_nc, real_r_nc) or cand_nc.startswith(
                (abs_r_nc + os.sep, real_r_nc + os.sep)
            ):
                matched_root = r
                break
        else:
            if candidate in (abs_r, real_r) or candidate.startswith(
                (abs_r + os.sep, real_r + os.sep)
            ):
                matched_root = r
                break

    if matched_root is None:
        return LocatorResult("refused", "outside-roots", None, None, None)

    # ── step 5: read through the co-located file_safety helper ──────────────
    root_path = Path(matched_root)
    file_path = Path(candidate)

    try:
        data = read_confined_regular_file(
            root_path, file_path, max_bytes=MAX_READ_BYTES
        )
    except BoundExceeded:
        # ── step 6: classify refusal ────────────────────────────────────────
        return LocatorResult("refused", "oversize", root_path, file_path, None)
    except UnsafeContentError as exc:
        cause = exc.__cause__
        reason = "missing" if isinstance(cause, FileNotFoundError) else "unsafe-file"
        return LocatorResult("refused", reason, root_path, file_path, None)

    rel_path = file_path.relative_to(root_path)
    return LocatorResult("read", None, root_path, rel_path, data)


# ── CLI ──────────────────────────────────────────────────────────────────────


class _OnceAction(argparse.Action):
    """Argparse action that rejects a second occurrence of an option (exit 2)."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: str | None = None,
    ) -> None:
        if getattr(namespace, self.dest, None) is not None:
            parser.error(
                f"{option_string or '--' + self.dest} may only appear once"
            )
        setattr(namespace, self.dest, values)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: decode --locator-b64, run read_locator, emit output.

    Stdout output contract:
      - Every run that parses its arguments prints ``received: <json>`` first.
        On encoding failure ``received: null`` (JSON null) is printed.
      - Exit 0: ``root: <json>`` then ``source: <json>`` then raw file bytes.
      - Exit 3: ``refused: <reason>``.
      - Exit 2: usage error, usage on stderr only, nothing on stdout.
    """
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    parser = argparse.ArgumentParser(
        prog="read-locator.py",
        description="Read a provider-returned file locator through confined access.",
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Repository root.",
    )
    parser.add_argument(
        "--approved-root",
        action="append",
        dest="approved_root",
        default=[],
        metavar="DIR",
        help="Additional approved root (repeatable).",
    )
    parser.add_argument(
        "--locator-b64",
        required=True,
        action=_OnceAction,
        dest="locator_b64",
        metavar="BASE64",
        help="Standard base64 encoding of the locator's UTF-8 bytes.",
    )
    args = parser.parse_args(argv)

    # Decode base64, then UTF-8; both failures are refused as "encoding".
    raw_b64: str = args.locator_b64
    try:
        raw_bytes = base64.b64decode(raw_b64, validate=True)
    except Exception:
        print("received: null")
        print("refused: encoding")
        return 3
    try:
        locator_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        print("received: null")
        print("refused: encoding")
        return 3

    # Print the decoded locator as an ASCII-only JSON string so every
    # non-ASCII character, U+0085, U+2028, and U+2029 appears only as a
    # \u escape.  No hostile text can forge a later output line.
    print(f"received: {json.dumps(locator_text, ensure_ascii=True)}")

    root = Path(args.root)
    approved_roots = [Path(r) for r in args.approved_root]
    result = read_locator(root, locator_text, approved_roots)

    if result.status == "read":
        assert result.root is not None
        assert result.path is not None
        assert result.data is not None
        print(f"root: {json.dumps(str(result.root), ensure_ascii=True)}")
        print(f"source: {json.dumps(result.path.as_posix(), ensure_ascii=True)}")
        sys.stdout.buffer.write(result.data)
        return 0
    print(f"refused: {result.reason}")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
