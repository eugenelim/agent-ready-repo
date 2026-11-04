"""Approval-gate digest for the work-loop supervisor.

`gate_digest` hashes a spec.md or plan.md the way an approval pins it: the
text is checked for hidden or control characters, a trailing `## Changelog`
section is validated and dropped, and the rest goes through the single
canonicaliser in `_loop_guards.canonical_contract`.

Standard library only. Sibling modules are loaded by path, unregistered.
This module writes nothing to stdout or stderr.
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
import stat
import sys
import unicodedata
from pathlib import Path
from types import ModuleType

_SCRIPTS_DIR = Path(__file__).resolve().parent
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_LINE_SEPARATORS = frozenset({0x2028, 0x2029, 0xFFF9, 0xFFFA, 0xFFFB})

_modules: dict[str, ModuleType] = {}


class GateDigestRefused(Exception):
    """Raised when gate text cannot be digested; `code` names the reason."""

    def __init__(self, code: str) -> None:
        """Store the refusal *code* and use it as the message."""
        super().__init__(code)
        self.code = code


def _load_sibling(alias: str, filename: str) -> ModuleType:
    """Load a sibling script by path under a unique name, cached, unregistered."""
    cached = _modules.get(alias)
    if cached is not None:
        return cached
    path = _SCRIPTS_DIR / filename
    try:
        info = path.lstat()
    except OSError as exc:
        raise ImportError(f"cannot locate {filename}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise ImportError(f"{filename} is not a regular file")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(alias, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"no import spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    _modules[alias] = module
    return module


def _unsafe(text: str, is_hidden_char) -> bool:  # type: ignore[no-untyped-def]
    """True when *text* holds a control, format, hidden or separator character."""
    for i, ch in enumerate(text):
        if ch in ("\t", "\n"):
            continue
        if ch == "\r":
            if text[i + 1 : i + 2] == "\n":
                continue
            return True
        if unicodedata.category(ch) in ("Cc", "Cf") or ord(ch) in _LINE_SEPARATORS:
            return True
        if is_hidden_char(ch):
            return True
    return False


def _strip_changelog(text: str) -> str:
    """Validate and drop a trailing `## Changelog` section from LF-normalised *text*."""
    lines = text.split("\n")
    headings: list[int] = []
    fence: str | None = None
    for idx, line in enumerate(lines):
        m = _FENCE_RE.match(line)
        if m:
            marker = m.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is None and line.startswith("## "):
            headings.append(idx)
    changelog = [i for i in headings if lines[i].strip() == "## Changelog"]
    if not changelog:
        return text
    start = changelog[0]
    if len(changelog) != 1 or headings[-1] != start:
        raise GateDigestRefused("gate-changelog-shape")
    body = _HTML_COMMENT_RE.sub("", "\n".join(lines[start + 1 :]))
    for line in body.split("\n"):
        if line.strip() == "" or line.startswith("- ") or line[:1].isspace():
            continue
        raise GateDigestRefused("gate-changelog-shape")
    return "\n".join(lines[:start])


def gate_digest(text_or_bytes: str | bytes, *, name: str) -> str:
    """Return the lowercase hex SHA-256 pinning *text_or_bytes* as `spec.md` or `plan.md`.

    Raises `GateDigestRefused` with code `gate-unsafe-content` or
    `gate-changelog-shape`.
    """
    if isinstance(text_or_bytes, bytes):
        try:
            text = text_or_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise GateDigestRefused("gate-unsafe-content") from exc
    else:
        text = text_or_bytes
    lint = _load_sibling("core_work_loop_gates_lint_knowledge", "lint-knowledge.py")
    if _unsafe(text, lint.is_hidden_char):
        raise GateDigestRefused("gate-unsafe-content")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    remaining = _strip_changelog(text)
    guards = _load_sibling("core_work_loop_gates_loop_guards", "_loop_guards.py")
    canonical = guards.canonical_contract(remaining, ac_section_only=(name != "plan.md"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
