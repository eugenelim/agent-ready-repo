#!/usr/bin/env python3
"""Check the `Parent intent:`, `Brief:`, and `Discovery:` pointers of changed artifacts.

Usage: lint-graph-pointers.py --root DIR --base-ref REF

The check selects the intent, brief, and spec artifacts the change adds or
modifies relative to REF (committed, staged, unstaged, and untracked
additions; a rename selects its destination; a deletion selects nothing). It
then checks every active `Parent intent:` and `Brief:` field in the preamble
of each selected artifact, and every active `Discovery:` field in the preamble
of each selected spec. A pointer must be typed and must name exactly one
live target of the field's type:

- `Parent intent:` takes `<kind>:<slug>` where kind is outcome, opportunity,
  capability, or intent and matches the target intent's registered kind.
- `Brief:` takes `brief:<slug>`.
- `Discovery:` in a spec takes the same typed form as `Parent intent:` when it
  points at an intent. A repository path under `product/intents/`, a markdown
  link that resolves there, or a bare slug of a live intent is untyped. The
  path or link is judged by its text and its target is never opened. Any other
  value (research or notes paths, `brief:` or `spec:` values, URLs, free text)
  is non-intent provenance and is not checked.

An empty value, or a value whose first word is `none`, records no pointer.
Artifacts the change does not touch are never validated; they are read only
to resolve targets. Nothing is written to the repository.

Exit codes: 0 complete check with no violations; 1 one or more violations;
2 refusal or incomplete check (the inventory could not be completed safely).

Diagnostics never echo a field value or a host path.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import os
import posixpath
import re
import shutil
import stat as _stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

_SCRIPT_DIR: Path = Path(__file__).resolve().parent

GIT_TIMEOUT_S = 20.0

# Budgets and name grammars below are kept in lockstep by hand with the
# delivery relation resolver that ships beside this script.
MAX_ENTRIES = 50_000
MAX_FILES = 10_000
MAX_DEPTH = 8
MAX_ARTIFACT_BYTES = 1_000_000
MAX_AGGREGATE_BYTES = 67_108_864

_COLLECTION_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.md$")
_SPEC_DIR_RE = re.compile(r"^[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*$")
_SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
_SLUG_RE = re.compile(_SLUG)
_INTENT_KINDS = ("outcome", "opportunity", "capability", "intent")
_PARENT_TYPED_RE = re.compile(rf"({'|'.join(_INTENT_KINDS)}):({_SLUG})")
_OTHER_TYPED_RE = re.compile(rf"(brief|spec):({_SLUG})")
_BRIEF_TYPED_RE = re.compile(rf"brief:({_SLUG})")
_LINK_RE = re.compile(r"\[.*\]\(.*\)")
_INTENT_PREFIXES = tuple(f"{kind}:" for kind in _INTENT_KINDS)
_INTENTS_DIR = "docs/product/intents/"

# Preamble parsing is kept in lockstep by hand with the intent graph reader.
_HEADING_PREFIX = "## "
_FIELD_LINE_RE = re.compile(r"^- \*\*([^*:]+):\*\*\s*(.*)$")
_COMMENT_SUFFIX_RE = re.compile(r"\s*<!--.*?-->\s*$", re.DOTALL)

_COLLECTIONS = {
    "intents": ("docs", "product", "intents"),
    "briefs": ("docs", "product", "briefs"),
}

_file_safety_module: Any = None


class Refusal(Exception):
    """An incomplete check: carries a stable code and an optional safe detail."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


def _get_file_safety() -> Any:
    """Load the co-located _file_safety.py helper at most once."""
    global _file_safety_module
    if _file_safety_module is not None:
        return _file_safety_module
    path = _SCRIPT_DIR / "_file_safety.py"
    try:
        st = os.lstat(path)
    except OSError as exc:
        raise ImportError(f"required helper unavailable: {path.name}") from exc
    if not _stat.S_ISREG(st.st_mode) or _stat.S_ISLNK(st.st_mode):
        raise ImportError(f"required helper is not a regular file: {path.name}")
    name = "_lint_graph_pointers_file_safety"
    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"required helper cannot be loaded: {path.name}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = prev
    required = {
        "UnsafeContentError",
        "BoundExceeded",
        "walk_confined_regular_files",
        "read_confined_regular_file",
    }
    if required - set(vars(mod)):
        sys.modules.pop(name, None)
        raise ImportError(f"required helper lacks expected symbols: {path.name}")
    _file_safety_module = mod
    return mod


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


def _valid_base_ref(ref: str) -> bool:
    if not ref or ref.startswith("-"):
        return False
    return not any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in ref)


def _git(root: Path, args: list[str], index_file: Path | None = None) -> bytes:
    """Run a read-only git command; raise Refusal on any failure.

    ``git diff`` against a commit may refresh the stat cache and rewrite the
    index even with optional locks off, so the caller can point it at a
    private copy of the index.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")
           or k in ("GIT_EXEC_PATH", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    if index_file is not None:
        env["GIT_INDEX_FILE"] = str(index_file)
    cmd = ["git", "-C", str(root), "-c", "core.fsmonitor=false", *args]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, check=False, timeout=GIT_TIMEOUT_S, env=env
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Refusal("git-unavailable") from exc
    if proc.returncode != 0:
        raise Refusal("git-failed")
    return proc.stdout


def _is_admitted(path: str) -> bool:
    parts = path.split("/")
    if len(parts) == 4 and parts[:3] in (
        ["docs", "product", "intents"],
        ["docs", "product", "briefs"],
    ):
        return bool(_COLLECTION_NAME_RE.fullmatch(parts[3]))
    if len(parts) == 4 and parts[0] == "docs" and parts[1] == "specs":
        return parts[3] == "spec.md" and bool(_SPEC_DIR_RE.fullmatch(parts[2]))
    return False


def _select(root: Path, base_ref: str) -> list[str]:
    if not _valid_base_ref(base_ref):
        raise Refusal("base-unavailable")
    try:
        commit = _git(root, ["rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}"])
        base = _git(root, ["merge-base", commit.decode().strip(), "HEAD"])
    except Refusal as exc:
        if exc.code == "git-unavailable":
            raise
        raise Refusal("base-unavailable") from exc
    base_sha = base.decode().strip()
    if not base_sha:
        raise Refusal("base-unavailable")
    try:
        index_path = Path(
            _git(root, ["rev-parse", "--git-path", "index"]).decode().strip()
        )
        if not index_path.is_absolute():
            index_path = root / index_path
        with tempfile.TemporaryDirectory(prefix="lint-graph-pointers-") as scratch:
            private_index = Path(scratch) / "index"
            if index_path.is_file():
                shutil.copyfile(index_path, private_index)
            changed = _git(
                root,
                ["diff", "--name-only", "-z", "--relative", "--no-renames",
                 "--diff-filter=d", "--no-ext-diff", base_sha, "--"],
                index_file=private_index,
            )
        untracked = _git(
            root, ["ls-files", "--others", "--exclude-standard", "-z", "--"]
        )
    except (Refusal, OSError) as exc:
        if isinstance(exc, Refusal) and exc.code == "git-unavailable":
            raise
        raise Refusal("base-unavailable") from exc
    selected: set[str] = set()
    for blob in (changed, untracked):
        for raw in blob.split(b"\0"):
            if not raw:
                continue
            path = raw.decode("utf-8", errors="surrogateescape")
            if _is_admitted(path):
                selected.add(path)
    return sorted(selected)


# ---------------------------------------------------------------------------
# Preamble parsing
# ---------------------------------------------------------------------------


def _visible_line(line: str, inside_comment: bool) -> tuple[str, bool]:
    """Return the visible part of a line and the updated HTML-comment state."""
    visible: list[str] = []
    remainder = line
    while remainder:
        if inside_comment:
            close = remainder.find("-->")
            if close == -1:
                return "".join(visible), True
            remainder = remainder[close + 3:]
            inside_comment = False
            continue
        open_at = remainder.find("<!--")
        if open_at == -1:
            visible.append(remainder)
            break
        visible.append(remainder[:open_at])
        remainder = remainder[open_at + 4:]
        inside_comment = True
    return "".join(visible), inside_comment


def _clean(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == "`" and value[-1] == "`":
        value = value[1:-1]
    return value.strip()


def _preamble(text: str) -> dict[str, list[str]]:
    """Every active preamble field value, in order, with comments hidden."""
    fields: dict[str, list[str]] = {}
    inside = False
    for line in text.splitlines():
        visible, inside = _visible_line(line, inside)
        if visible.startswith(_HEADING_PREFIX):
            break
        match = _FIELD_LINE_RE.match(visible)
        if match:
            fields.setdefault(match.group(1).strip(), []).append(_clean(match.group(2)))
    return fields


def _normalize_kind_level(raw: str) -> str:
    value = _COMMENT_SUFFIX_RE.sub("", raw.strip()).strip()
    for sentinel in (" (", " →", "<!--"):
        idx = value.find(sentinel)
        if idx >= 0:
            value = value[:idx]
    if len(value) >= 2 and value[0] == "`" and value[-1] == "`":
        value = value[1:-1].strip()
    parts = value.split()
    return parts[0].lower() if parts else ""


def _registered_kind(fields: dict[str, list[str]]) -> str:
    kind = _normalize_kind_level((fields.get("Kind") or [""])[0])
    if kind in ("outcome", "opportunity"):
        return kind
    if _normalize_kind_level((fields.get("Level") or [""])[0]) == "capability":
        return "capability"
    return "intent"


# ---------------------------------------------------------------------------
# Target inventory
# ---------------------------------------------------------------------------


class _Index:
    """Slug -> registered kind for live files, plus retired and ambiguous sets."""

    def __init__(self) -> None:
        self.live: dict[str, str] = {}
        self.retired: set[str] = set()
        self.ambiguous: set[str] = set()

    def add(self, fields: dict[str, list[str]], kind: str) -> None:
        slug = (fields.get("Slug") or [""])[0]
        if not _SLUG_RE.fullmatch(slug):
            return
        if any(fields.get("Tombstone", [])):
            self.retired.add(slug)
        elif slug in self.live:
            self.ambiguous.add(slug)
        else:
            self.live[slug] = kind


def _collection_dir(root: Path, parts: tuple[str, ...]) -> Path | None:
    """Return the collection directory, None when absent; refuse an unsafe one."""
    current = root
    for part in parts:
        current = current / part
        try:
            st = os.lstat(current)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise Refusal("unsafe-artifact", "/".join(parts)) from exc
        if _stat.S_ISLNK(st.st_mode) or not _stat.S_ISDIR(st.st_mode):
            raise Refusal("unsafe-artifact", "/".join(parts))
    return current


def _build_indexes(root: Path) -> tuple[_Index, _Index]:
    fs = _get_file_safety()
    indexes = {"intents": _Index(), "briefs": _Index()}
    entries_left, files_left, aggregate = MAX_ENTRIES, MAX_FILES, 0
    for name, parts in _COLLECTIONS.items():
        directory = _collection_dir(root, parts)
        if directory is None:
            continue
        label = "/".join(parts)
        try:
            walk = fs.walk_confined_regular_files(
                root, directory, max_entries=entries_left,
                max_files=files_left, max_depth=MAX_DEPTH,
            )
        except fs.BoundExceeded as exc:
            raise Refusal("resource-limit", label) from exc
        except fs.UnsafeContentError as exc:
            raise Refusal("unsafe-artifact", label) from exc
        entries_left -= walk.entries_seen
        files_left -= len(walk.files)
        for path in walk.files:
            if path.parent != directory or not _COLLECTION_NAME_RE.fullmatch(path.name):
                continue
            rel = f"{label}/{path.name}"
            try:
                raw = fs.read_confined_regular_file(
                    root, path, max_bytes=MAX_ARTIFACT_BYTES
                )
            except fs.BoundExceeded as exc:
                raise Refusal("resource-limit", rel) from exc
            except fs.UnsafeContentError as exc:
                raise Refusal("unsafe-artifact", rel) from exc
            aggregate += len(raw)
            if aggregate > MAX_AGGREGATE_BYTES:
                raise Refusal("resource-limit", label)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise Refusal("invalid-utf8", rel) from exc
            fields = _preamble(text)
            indexes[name].add(fields, _registered_kind(fields))
    return indexes["intents"], indexes["briefs"]


# ---------------------------------------------------------------------------
# Field rules
# ---------------------------------------------------------------------------


def _is_no_pointer(value: str) -> bool:
    parts = value.split()
    return not parts or parts[0].lower() == "none"


def _lookup(index: _Index, slug: str) -> str:
    """Return '' when the slug names one live target, else the failure suffix."""
    if slug in index.ambiguous:
        return "ambiguous"
    if slug in index.live:
        return ""
    if slug in index.retired:
        return "retired"
    return "missing"


def _check_parent(value: str, intents: _Index) -> str:
    typed = _PARENT_TYPED_RE.fullmatch(value)
    if typed:
        kind, slug = typed.groups()
        result = _lookup(intents, slug)
        if result:
            return f"parent-intent-{result}"
        if slug not in intents.ambiguous and intents.live[slug] != kind:
            return "parent-intent-wrong-kind"
        return ""
    if _OTHER_TYPED_RE.fullmatch(value):
        return "parent-intent-wrong-kind"
    if _LINK_RE.fullmatch(value) or "/" in value or value.endswith(".md") \
            or _SLUG_RE.fullmatch(value):
        return "parent-intent-untyped"
    return "parent-intent-malformed"


def _check_brief(value: str, briefs: _Index) -> str:
    typed = _BRIEF_TYPED_RE.fullmatch(value)
    if typed:
        result = _lookup(briefs, typed.group(1))
        return f"brief-{result}" if result else ""
    return "brief-malformed" if value.startswith("brief:") else "brief-untyped"


def _resolves_under_intents(target: str, spec_dir: str) -> bool:
    """Lexically resolve a link target against the spec's directory.

    No filesystem access: the target is never opened.
    """
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target):
        return False
    joined = target.lstrip("/") if target.startswith("/") else f"{spec_dir}/{target}"
    resolved = posixpath.normpath(joined)
    if resolved == ".." or resolved.startswith("../"):
        return False
    return (resolved + "/").startswith(_INTENTS_DIR)


def _link_targets(value: str) -> list[str]:
    """Markdown link targets in one linear pass (no backtracking pattern)."""
    targets = []
    for chunk in value.split("](")[1:]:
        target = chunk.split(")", 1)[0].strip().lstrip("<").strip()
        targets.append(target.split(None, 1)[0].split(">", 1)[0] if target else "")
    return targets


def _check_discovery(value: str, intents: _Index, spec_dir: str) -> str:
    """Classify a spec's Discovery value; only intent-valued forms can fail."""
    if value.startswith(_INTENT_PREFIXES):
        typed = _PARENT_TYPED_RE.fullmatch(value)
        if not typed:
            return "discovery-malformed"
        kind, slug = typed.groups()
        result = _lookup(intents, slug)
        if result:
            return f"discovery-{result}"
        return "discovery-wrong-kind" if intents.live[slug] != kind else ""
    if "product/intents/" in value or any(
        _resolves_under_intents(t, spec_dir) for t in _link_targets(value)
    ):
        return "discovery-untyped"
    if _SLUG_RE.fullmatch(value) and value in intents.live:
        return "discovery-untyped"
    return ""


def _check_artifact(
    text: str, intents: _Index, briefs: _Index, rel: str = ""
) -> list[tuple[str, str]]:
    fields = _preamble(text)
    found: list[tuple[str, str]] = []
    if rel.startswith("docs/specs/"):
        spec_dir = posixpath.dirname(rel)
        for value in fields.get("Discovery", []):
            if not _is_no_pointer(value):
                code = _check_discovery(value, intents, spec_dir)
                if code:
                    found.append(("Discovery", code))
    for value in fields.get("Parent intent", []):
        if not _is_no_pointer(value):
            code = _check_parent(value, intents)
            if code:
                found.append(("Parent intent", code))
    for value in fields.get("Brief", []):
        if not _is_no_pointer(value):
            code = _check_brief(value, briefs)
            if code:
                found.append(("Brief", code))
    return found


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _run(root_arg: str, base_ref: str) -> int:
    root_path = Path(root_arg)
    if not root_path.is_dir():
        raise Refusal("root-invalid")
    root = root_path.resolve()
    selected = _select(root, base_ref)
    violations: list[tuple[str, str, str]] = []
    if selected:
        fs = _get_file_safety()
        intents, briefs = _build_indexes(root)
        for rel in selected:
            try:
                raw = fs.read_confined_regular_file(
                    root, root / rel, max_bytes=MAX_ARTIFACT_BYTES
                )
            except fs.BoundExceeded as exc:
                raise Refusal("resource-limit", rel) from exc
            except (fs.UnsafeContentError, OSError) as exc:
                raise Refusal("unsafe-artifact", rel) from exc
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise Refusal("invalid-utf8", rel) from exc
            for field, code in _check_artifact(text, intents, briefs, rel):
                violations.append((rel, field, code))
    for rel, field, code in sorted(set(violations)):
        print(f"{rel}: {field}: {code}")
    print(
        f"lint-graph-pointers: {len(violations)} violation(s) "
        f"in {len(selected)} selected artifact(s)"
    )
    return 1 if violations else 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lint-graph-pointers.py",
        description=(
            "Check the Parent intent and Brief pointers of intent, brief, and "
            "spec artifacts, and the Discovery pointer of specs, changed since "
            "a base ref. Exit 0: complete check, "
            "no violations. Exit 1: one or more violations. Exit 2: refusal "
            "or incomplete check."
        ),
    )
    parser.add_argument("--root", required=True, help="repository directory to check")
    parser.add_argument(
        "--base-ref", required=True,
        help="git ref to compare against; changes since its merge-base with HEAD are checked",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the check; return the exit code."""
    for stream, errors in ((sys.stdout, "strict"), (sys.stderr, "backslashreplace")):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8", errors=errors)  # type: ignore[union-attr]
    args = _build_parser().parse_args(argv)
    try:
        _get_file_safety()
        return _run(args.root, args.base_ref)
    except Refusal as exc:
        detail = f" {exc.detail}" if exc.detail else ""
        code = "base-unavailable" if exc.code == "git-failed" else exc.code
        print(f"lint-graph-pointers: {code}{detail}", file=sys.stderr)
        return 2
    except ImportError:
        print("lint-graph-pointers: internal-error", file=sys.stderr)
        return 2
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        print("lint-graph-pointers: internal-error", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
