#!/usr/bin/env python3
"""Check the optional `Priority:` header field on every intent, brief, spec, and captured item.

Usage: lint-priority-field.py --root DIR

The check reads four kinds of artifact under DIR:

- each file directly in `docs/product/intents/` or `docs/product/briefs/`
  whose name matches `^[A-Za-z0-9][A-Za-z0-9._-]*\\.md$`;
- each captured-item file directly in `docs/product/captured/` whose name
  matches `^[a-z0-9][a-z0-9-]*\\.md$`;
- each `docs/specs/<dir>/spec.md` whose directory name matches
  `^[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*$`.

Every other entry is ignored. In the preamble of each artifact (the lines
before the first `## ` heading, outside fenced blocks, with HTML comments
hidden) a `- **Priority:** <value>` line is valid when its value is exactly
`urgent`, `high`, `medium`, or `low`. A trailing HTML comment and one pair of
surrounding backticks are not part of the value. An artifact with no such line,
or whose value is empty, has no priority and is valid. Each artifact gives at
most one violation:

- `duplicate_priority`: two or more `Priority:` lines, whatever their values.
- `invalid_priority`: one line with any other value.

The field never decides readiness, dispatch, or order of work; this script is
its only reader. Nothing is written to the repository.

Output: one `<path>: <code>` line on stdout per violation, sorted by path, and
nothing else. A refusal prints one `<code>: <path>` line on stderr and nothing
on stdout. Codes: `unsafe-artifact` (a symlink, a non-regular file or
directory), `resource-limit` (a walk bound exceeded), `invalid-utf8`.
A carrier directory that does not exist is skipped.

Exit codes: 0 complete check with no violations; 1 one or more violations;
2 refusal or incomplete check.

Diagnostics never echo a field value or a host path.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import os
import re
import stat as _stat
import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR: Path = Path(__file__).resolve().parent

PRIORITY_VALUES = ("urgent", "high", "medium", "low")

# Walk bounds are kept in step by hand with lint-graph-pointers.py.
MAX_ENTRIES = 50_000
MAX_FILES = 10_000
MAX_DEPTH = 8
MAX_ARTIFACT_BYTES = 1_000_000
MAX_AGGREGATE_BYTES = 67_108_864

# Name grammars: the first and last are kept in step by hand with
# lint-graph-pointers.py.
_COLLECTION_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.md$")
_SPEC_DIR_RE = re.compile(r"^[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*$")
_CAPTURED_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*\.md$")

_HEADING_PREFIX = "## "
_PRIORITY_LINE_RE = re.compile(r"^- \*\*Priority:\*\*\s*(.*)$")
_FENCE_MARKERS = ("```", "~~~")

# Directory parts and name grammar per flat carrier; specs are handled separately.
_FLAT_CARRIERS: dict[str, tuple[tuple[str, ...], re.Pattern[str]]] = {
    "intents": (("docs", "product", "intents"), _COLLECTION_NAME_RE),
    "briefs": (("docs", "product", "briefs"), _COLLECTION_NAME_RE),
    "captured": (("docs", "product", "captured"), _CAPTURED_NAME_RE),
}
_SPECS_PARTS = ("docs", "specs")

_file_safety_module: Any = None


class PriorityError(Exception):
    """A priority violation: carries the stable code `duplicate_priority` or `invalid_priority`."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class Refusal(Exception):
    """An incomplete check: carries a stable code and the repository-relative path."""

    def __init__(self, code: str, path: str = ".") -> None:
        super().__init__(code)
        self.code = code
        self.path = path


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
    name = "_lint_priority_field_file_safety"
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
        "list_confined_directories",
        "read_confined_regular_file",
    }
    if required - set(vars(mod)):
        sys.modules.pop(name, None)
        raise ImportError(f"required helper lacks expected symbols: {path.name}")
    _file_safety_module = mod
    return mod


# ---------------------------------------------------------------------------
# Reader
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
    """Trim a field value and strip one pair of surrounding backticks."""
    value = value.strip()
    if len(value) >= 2 and value[0] == "`" and value[-1] == "`":
        value = value[1:-1]
    return value.strip()


def _priority_lines(text: str) -> list[str]:
    """Field values of every active `Priority:` preamble line, in order."""
    values: list[str] = []
    inside_comment = False
    fence = ""
    for line in text.splitlines():
        if fence:
            if line.lstrip().startswith(fence):
                fence = ""
            continue
        was_inside = inside_comment
        visible, inside_comment = _visible_line(line, inside_comment)
        if not was_inside:
            opener = visible.lstrip()
            marker = next((m for m in _FENCE_MARKERS if opener.startswith(m)), "")
            if marker:
                fence = marker
                continue
        if visible.startswith(_HEADING_PREFIX):
            break
        match = _PRIORITY_LINE_RE.match(visible)
        if match:
            values.append(_clean(match.group(1)))
    return values


def read_priority(text: str) -> str | None:
    """Return the item's priority, or None when it has none.

    Raises PriorityError with `duplicate_priority` for two or more lines and
    `invalid_priority` for one line whose value is outside PRIORITY_VALUES.
    """
    values = _priority_lines(text)
    if len(values) > 1:
        raise PriorityError("duplicate_priority")
    if not values or not values[0]:
        return None
    if values[0] not in PRIORITY_VALUES:
        raise PriorityError("invalid_priority")
    return values[0]


# ---------------------------------------------------------------------------
# Walk
# ---------------------------------------------------------------------------


def _carrier_dir(root: Path, parts: tuple[str, ...]) -> Path | None:
    """Return the carrier directory, None when absent; refuse an unsafe one."""
    label = "/".join(parts)
    current = root
    for part in parts:
        current = current / part
        try:
            st = os.lstat(current)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise Refusal("unsafe-artifact", label) from exc
        if _stat.S_ISLNK(st.st_mode) or not _stat.S_ISDIR(st.st_mode):
            raise Refusal("unsafe-artifact", label)
    return current


class _Budget:
    """The walk bounds shared across every carrier directory."""

    def __init__(self) -> None:
        self.entries_left = MAX_ENTRIES
        self.files_left = MAX_FILES
        self.aggregate = 0


def _decide(
    fs: Any, root: Path, path: Path, budget: _Budget, label: str
) -> tuple[str, str] | None:
    """Read one carrier file; return its violation, or None when it is valid."""
    rel = path.relative_to(root).as_posix()
    try:
        raw = fs.read_confined_regular_file(root, path, max_bytes=MAX_ARTIFACT_BYTES)
    except fs.BoundExceeded as exc:
        raise Refusal("resource-limit", rel) from exc
    except fs.UnsafeContentError as exc:
        raise Refusal("unsafe-artifact", rel) from exc
    budget.aggregate += len(raw)
    if budget.aggregate > MAX_AGGREGATE_BYTES:
        raise Refusal("resource-limit", label)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Refusal("invalid-utf8", rel) from exc
    try:
        read_priority(text)
    except PriorityError as exc:
        return rel, exc.code
    return None


def _flat_carriers(
    fs: Any, root: Path, directory: Path, pattern: re.Pattern[str], budget: _Budget
) -> list[Path]:
    """The carrier files directly in one flat carrier directory."""
    label = directory.relative_to(root).as_posix()
    try:
        walk = fs.walk_confined_regular_files(
            root, directory, max_entries=budget.entries_left,
            max_files=budget.files_left, max_depth=MAX_DEPTH,
        )
    except fs.BoundExceeded as exc:
        raise Refusal("resource-limit", label) from exc
    except fs.UnsafeContentError as exc:
        raise Refusal("unsafe-artifact", label) from exc
    budget.entries_left -= walk.entries_seen
    budget.files_left -= len(walk.files)
    return [
        path for path in walk.files
        if path.parent == directory and pattern.fullmatch(path.name)
    ]


def _spec_carriers(fs: Any, root: Path, directory: Path, budget: _Budget) -> list[Path]:
    """Each `<dir>/spec.md` one level under the specs directory.

    Only the spec directories themselves are inspected, so a link-like entry
    deeper inside a spec directory, such as under its notes, is never reached.
    """
    label = directory.relative_to(root).as_posix()
    try:
        children = fs.list_confined_directories(root, directory)
    except fs.UnsafeContentError as exc:
        raise Refusal("unsafe-artifact", label) from exc
    carriers: list[Path] = []
    for child in children:
        budget.entries_left -= 1
        if budget.entries_left < 0:
            raise Refusal("resource-limit", label)
        if not _SPEC_DIR_RE.fullmatch(child.name):
            continue
        spec = child / "spec.md"
        try:
            st = os.lstat(spec)
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise Refusal("unsafe-artifact", spec.relative_to(root).as_posix()) from exc
        if _stat.S_ISLNK(st.st_mode) or not _stat.S_ISREG(st.st_mode):
            raise Refusal("unsafe-artifact", spec.relative_to(root).as_posix())
        budget.files_left -= 1
        if budget.files_left < 0:
            raise Refusal("resource-limit", label)
        carriers.append(spec)
    return carriers


def _scan(root: Path) -> list[tuple[str, str]]:
    """Read every carrier, one directory at a time; return (path, code) violations."""
    fs = _get_file_safety()
    budget = _Budget()
    violations: list[tuple[str, str]] = []
    plan: list[tuple[tuple[str, ...], re.Pattern[str] | None]] = [
        *_FLAT_CARRIERS.values(), (_SPECS_PARTS, None),
    ]
    for parts, pattern in plan:
        directory = _carrier_dir(root, parts)
        if directory is None:
            continue
        label = "/".join(parts)
        files = (
            _flat_carriers(fs, root, directory, pattern, budget)
            if pattern is not None
            else _spec_carriers(fs, root, directory, budget)
        )
        for path in files:
            violation = _decide(fs, root, path, budget, label)
            if violation is not None:
                violations.append(violation)
    return violations


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lint-priority-field.py",
        description=(
            "Check the optional Priority field of intents, briefs, specs, and "
            "captured items. Exit 0: no violations. Exit 1: one or more "
            "violations. Exit 2: refusal or incomplete check."
        ),
    )
    parser.add_argument("--root", required=True, help="repository directory to check")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the check; return the exit code."""
    for stream, errors in ((sys.stdout, "strict"), (sys.stderr, "backslashreplace")):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8", errors=errors)  # type: ignore[union-attr]
    args = _build_parser().parse_args(argv)
    try:
        root_path = Path(args.root)
        if not root_path.is_dir():
            raise Refusal("root-invalid")
        _get_file_safety()
        violations = _scan(root_path.resolve())
    except Refusal as exc:
        print(f"{exc.code}: {exc.path}", file=sys.stderr)
        return 2
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        print("internal-error: .", file=sys.stderr)
        return 2
    for rel, code in sorted(violations):
        print(f"{rel}: {code}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
