#!/usr/bin/env python3
"""Compare the outstanding work the artifacts show with workspace.toml.

Read-only. Run it once, just before each registration stop (slices 3, 7 and 8
of the workspace-registry-retirement brief), and record its summary in the spec
that stops that registration. It has no CI job, schedule, or make target.

    python3 tools/compare-registry.py --root DIR [--format text|json]

The outstanding side is every item in navigate-intents' `outstanding` result
plus every captured-item file whose Status is Open. The registry side is every
entry in workspace.toml. Each difference falls in one of eight classes
(FEAT-0034, "Registry comparison"):

  captured_item          allowed  registry-only entry naming another existing file
  legacy_shape           allowed  registry-only `spec/<slug>` string, or slug table
                                  naming no captured-item file
  registry_stale         allowed  registry-only entry whose file is terminal
  registry_closed_stale  allowed  outstanding item only in terminal collections
  registry_omission      allowed  outstanding item in no collection
  registry_live_only     FAILS    registry-only entry whose file is not terminal
  result_terminal        FAILS    outstanding item whose own status is terminal
  unclassified           FAILS    any other difference (missing or unreadable file,
                                  non-canonical path, entry with no target)

Exit codes:
  0  no failing row: the type's registration may stop
  1  at least one failing row (registry_live_only, result_terminal, unclassified)
  2  refused: bad arguments, unreadable input, or an internal error; one stderr
     line `refused: <input>: <reason>` and nothing on stdout

What to record: the default output, in full (the result line, the eight counts,
each FAIL line, the commit, and the workspace.toml sha256), and the exit code.
The tool writes no file, bytecode included.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # before any import by path: the tool writes no file

import argparse  # noqa: E402
import dataclasses  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import tomllib  # noqa: E402
from pathlib import Path, PurePosixPath  # noqa: E402
from types import ModuleType  # noqa: E402
from typing import Any, NoReturn  # noqa: E402

SOURCE_ROOT = Path(__file__).resolve().parent.parent
AGENTBUNDLE = SOURCE_ROOT / "packages" / "agentbundle"
if str(AGENTBUNDLE) not in sys.path:
    sys.path.insert(0, str(AGENTBUNDLE))

from agentbundle.catalogue_tooling.file_safety import (  # noqa: E402
    BoundExceeded,
    UnsafeContentError,
    read_confined_regular_file,
)

_SKILLS = SOURCE_ROOT / "packs/core/.apm/skills"
NAVIGATOR = _SKILLS / "navigate-intents/scripts/navigate_intents.py"
_INTENT_GRAPH = _SKILLS / "navigate-intents/scripts/intent_graph.py"
_ENGINE = _SKILLS / "workspace-status/scripts/workspace_status_engine.py"
_TERMINALITY = _SKILLS / "close-work/scripts/closure_terminality.py"

CLASSES = (
    "captured_item",
    "legacy_shape",
    "registry_stale",
    "registry_closed_stale",
    "registry_omission",
    "registry_live_only",
    "result_terminal",
    "unclassified",
)
FAILING_CLASSES = frozenset({"registry_live_only", "result_terminal", "unclassified"})

# FEAT-0034 § Registry comparison names these two sets; the thirteen collections
# together are the engine's collection tables (a test pins that equality).
NON_TERMINAL = frozenset({
    "backlog.open", "shaping_queue.backlog", "shaping_queue.active",
    "brief_queue.draft", "brief_queue.ready", "brief_queue.executing",
    "work.queue", "work.active",
})
TERMINAL = frozenset({
    "work.shipped", "brief_queue.shipped", "brief_queue.withdrawn",
    "brief_queue.cancelled", "backlog.closed",
})

NAVIGATOR_TIMEOUT_S = 120
MAX_FILE_BYTES = 64 * 1024 * 1024
_CAPTURED_DIR = "docs/product/captured"
_STATUS_LINE = re.compile(r"^- \*\*Status:\*\*(.*)$", re.MULTILINE)


class Refusal(Exception):
    """A refused input: prints `refused: <input>: <reason>` and exits 2."""

    def __init__(self, input_name: str, reason: str) -> None:
        super().__init__(reason)
        self.input_name = input_name
        self.reason = reason


def _one_line(text: str, limit: int = 300) -> str:
    """Escape *text* onto one printable ASCII line, bounded."""
    return json.dumps(str(text), ensure_ascii=True)[1:-1][:limit]


def _load(name: str, path: Path) -> ModuleType:
    """Import the module at *path* under *name* (a sibling skill's module)."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"{path}: not importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_modules: dict[str, ModuleType] = {}


def _module(name: str, path: Path) -> ModuleType:
    """Return the cached by-path import of *name*."""
    if name not in _modules:
        _modules[name] = _load(name, path)
    return _modules[name]


def engine() -> Any:
    """The workspace-status engine, loaded by path as `workspace_status_engine`."""
    return _module("workspace_status_engine", _ENGINE)


def terminality() -> Any:
    """close-work's `closure_terminality`, loaded by path."""
    return _module("closure_terminality", _TERMINALITY)


def _is_terminal(kind: str, status: str) -> bool:
    """Whether *status* is terminal for a navigator item type *kind*."""
    module = terminality()
    check = {
        "intent": module.is_intent_terminal,
        "brief": module.is_brief_terminal,
        "spec": module.is_spec_terminal,
    }[kind]
    return bool(check(status))


@dataclasses.dataclass(frozen=True)
class Row:
    """One difference row (spec Terms: Difference row)."""

    cls: str
    failing: bool
    target: str
    location: str
    id: str
    collections: tuple[str, ...]
    status: str

    def as_json(self) -> dict[str, Any]:
        """The row as the seven-key JSON object."""
        return {
            "class": self.cls, "failing": self.failing, "target": self.target,
            "location": self.location, "id": self.id,
            "collections": list(self.collections), "status": self.status,
        }


@dataclasses.dataclass(frozen=True)
class Outstanding:
    """An outstanding-side item: a navigator item or an Open captured-item file."""

    path: str
    id: str
    kind: str  # intent | brief | spec | captured
    status: str


@dataclasses.dataclass(frozen=True)
class Entry:
    """One registry entry in one collection."""

    collection: str
    location: str
    value: Any


# ── Inputs ────────────────────────────────────────────────────────────────────


def _array(table: dict[str, Any], key: str, label: str) -> list[Any]:
    """Return `table[key]` as a list, refusing when present and not an array."""
    value = table.get(key, [])
    if not isinstance(value, list):
        raise Refusal("workspace.toml", f"{label} is not an array")
    return value


def registry_entries(registry: dict[str, Any]) -> list[Entry]:
    """Every registry entry the engine's collection tables place.

    Refuses when a placed section or initiative table is not a table, or a
    collection is not an array.
    """
    eng = engine()
    found: list[Entry] = []
    for section, collections in eng._TOP_LEVEL_ENTRY_COLLECTIONS.items():
        if section not in registry:
            continue
        table = registry[section]
        if not isinstance(table, dict):
            raise Refusal("workspace.toml", f"{section} is not a table")
        for name in collections:
            for index, value in enumerate(_array(table, name, f"{section}.{name}")):
                found.append(Entry(f"{section}.{name}", f"{section}.{name}[{index}]", value))
    for key in sorted(k for k in registry if eng._CANONICAL_INITIATIVE_RE.match(k)):
        initiative = registry[key]
        if not isinstance(initiative, dict):
            raise Refusal("workspace.toml", f"{key} is not a table")
        for section, collections in eng._INITIATIVE_ENTRY_COLLECTIONS.items():
            if section not in initiative:
                continue
            table = initiative[section]
            if not isinstance(table, dict):
                raise Refusal("workspace.toml", f"{key}.{section} is not a table")
            for name in collections:
                label = f"{key}.{section}.{name}"
                for index, value in enumerate(_array(table, name, label)):
                    location = f"{key}.{section}.{name}[{index}]"
                    found.append(Entry(f"{section}.{name}", location, value))
    return found


def load_registry(root: Path) -> tuple[dict[str, Any], bytes]:
    """Read and parse `root/workspace.toml`; return the table and its bytes."""
    try:
        raw = read_confined_regular_file(root, root / "workspace.toml", max_bytes=MAX_FILE_BYTES)
    except (UnsafeContentError, OSError, ValueError) as exc:
        raise Refusal("workspace.toml", f"cannot be read: {type(exc).__name__}") from exc
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise Refusal("workspace.toml", "is not UTF-8") from exc
    except tomllib.TOMLDecodeError as exc:
        raise Refusal("workspace.toml", f"is not valid TOML: {exc}") from exc
    registry_entries(data)  # structure check, in AC-0019's first position
    return data, raw


def run_outstanding(root: Path) -> object:
    """Run the navigator's `outstanding` operation and return its parsed JSON."""
    command = [
        sys.executable, "-B", str(NAVIGATOR),
        "query", "--root", str(root), "--operation", "outstanding",
    ]
    try:
        done = subprocess.run(
            command, capture_output=True, text=True, check=False,
            timeout=NAVIGATOR_TIMEOUT_S, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as exc:
        raise Refusal("navigator", f"timed out after {NAVIGATOR_TIMEOUT_S}s") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise Refusal("navigator", f"could not run: {type(exc).__name__}") from exc
    if done.returncode != 0:
        raise Refusal("navigator", f"exited {done.returncode}")
    try:
        return json.loads(done.stdout)
    except ValueError as exc:
        raise Refusal("navigator", "output is not JSON") from exc


def check_envelope(envelope: object) -> tuple[list[dict[str, str]], str]:
    """Validate the navigator envelope; return its items and `generated_at`."""
    if not isinstance(envelope, dict):
        raise Refusal("navigator", "output is not a JSON object")
    if envelope.get("schema") != "intent-navigation.query.v1":
        raise Refusal("navigator", "schema is not intent-navigation.query.v1")
    if envelope.get("status") != "ok":
        raise Refusal("navigator", "status is not ok")
    items: list[dict[str, str]] = []
    for key in ("placed", "no_parent"):
        group = envelope.get(key)
        if not isinstance(group, list):
            raise Refusal("navigator", f"{key} is not an array")
        for item in group:
            if not isinstance(item, dict) or not all(
                isinstance(item.get(field), str) for field in ("id", "type", "status")
            ):
                raise Refusal("navigator", f"a {key} item lacks string id, type, and status")
            items.append(item)
    provenance = envelope.get("provenance")
    stamp = provenance.get("generated_at") if isinstance(provenance, dict) else None
    return items, stamp if isinstance(stamp, str) else ""


def graph_paths(root: Path) -> dict[str, str]:
    """Map each navigator id to its root-relative path, from `derive(root)`."""
    graph = _module("intent_graph", _INTENT_GRAPH)
    try:
        derived = graph.derive(root)
    except graph.DerivationError as exc:
        raise Refusal("graph", f"cannot be derived: {getattr(exc, 'code', 'error')}") from exc
    return {str(node["id"]): str(node["path"]) for node in derived["nodes"]}


def captured_listing(root: Path) -> list[dict[str, Any]]:
    """The captured-item files, refusing on any finding or unreadable/invalid file."""
    listing = engine().list_captured_items(root, frozenset())
    if listing.findings:
        raise Refusal("captured-items", "the directory or a file is not a readable item")
    for item in listing.items:
        if item.get("unreadable") or item.get("invalid") or "status" not in item:
            raise Refusal("captured-items", f"{item.get('path', '')} is unreadable or invalid")
    return [dict(item) for item in listing.items]


# ── Classification ────────────────────────────────────────────────────────────


def _is_canonical(target: str) -> bool:
    """A relative POSIX path with no empty, `.`, or `..` segment and no backslash."""
    if "\\" in target or target.startswith("/"):
        return False
    return all(part not in ("", ".", "..") for part in target.split("/"))


def _spelled_as_on_disk(root: Path, target: str) -> bool:
    """Whether every part of *target* equals a real directory entry name exactly.

    A case- or normalization-insensitive filesystem opens `Docs/x.md` as
    `docs/x.md`. Classing by the written path would then let an alias of a live
    typed file pass as `captured_item`, so any other spelling counts as missing.
    """
    directory = root
    for part in target.split("/"):
        try:
            if part not in {entry.name for entry in directory.iterdir()}:
                return False
        except OSError:
            return False
        directory = directory / part
    return True


def _typed_kind(target: str) -> str | None:
    """The typed-file kind for a canonical target (workspace-retirement Terms)."""
    parts = PurePosixPath(target).parts
    if len(parts) == 4 and parts[3].endswith(".md"):
        if parts[:3] == ("docs", "product", "intents"):
            return "intent"
        if parts[:3] == ("docs", "product", "briefs"):
            return "brief"
    if len(parts) == 4 and parts[:2] == ("docs", "specs") and parts[3] == "spec.md":
        return "spec"
    return None


def _row(cls: str, target: str, location: str, collections: set[str] | list[str],
         out: Outstanding | None = None, status: str = "") -> Row:
    return Row(
        cls, cls in FAILING_CLASSES, target, location, out.id if out else "",
        tuple(sorted(collections)), out.status if out else status,
    )


def _classify_target(root: Path, target: str, collections: set[str],
                     captured: dict[str, dict[str, Any]]) -> Row:
    """Class one registry-only target that is in a non-terminal collection."""
    def unclassified(status: str = "") -> Row:
        return _row("unclassified", target, "", collections, status=status)

    if not _is_canonical(target):
        return unclassified()
    item = captured.get(target)
    if item is not None:
        status = str(item["status"])
        cls = "registry_stale" if status == "Closed" else "registry_live_only"
        return _row(cls, target, "", collections, status=status)
    if not _spelled_as_on_disk(root, target):
        return unclassified()
    kind = _typed_kind(target)
    try:
        # A non-typed file's content is never needed: a zero cap still runs every
        # confinement and regular-file check, then stops before reading.
        raw = read_confined_regular_file(
            root, root / target, max_bytes=MAX_FILE_BYTES if kind else 0
        )
    except BoundExceeded:
        if kind is None:
            return _row("captured_item", target, "", collections)
        return unclassified()
    except (UnsafeContentError, OSError, ValueError):
        return unclassified()
    if kind is None:
        return _row("captured_item", target, "", collections)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return unclassified()
    match = _STATUS_LINE.search(text)
    status = terminality()._extract_status_token(match.group(1)) if match else ""
    cls = "registry_stale" if match and _is_terminal(kind, status) else "registry_live_only"
    return _row(cls, target, "", collections, status=status)


def classify(registry: dict[str, Any], outstanding: list[Outstanding],
             captured: list[dict[str, Any]], root: Path) -> list[Row]:
    """Apply every class rule; return the difference rows in row order."""
    by_slug = {str(item["path"]): item for item in captured}
    slugs = {str(item["slug"]): str(item["path"]) for item in captured}
    eng = engine()
    targeted: dict[str, set[str]] = {}
    untargeted: list[Entry] = []
    for entry in registry_entries(registry):
        value = entry.value
        target: str | None = None
        if isinstance(value, dict):
            if isinstance(value.get("path"), str):
                target = value["path"]
            elif "path" not in value and isinstance(value.get("slug"), str):
                target = slugs.get(value["slug"])
        if target is None:
            untargeted.append(entry)
        else:
            targeted.setdefault(target, set()).add(entry.collection)

    rows: list[Row] = []
    outstanding_paths = {item.path for item in outstanding}
    for item in outstanding:
        cols = targeted.get(item.path, set())
        terminal = (
            item.status == "Closed" if item.kind == "captured"
            else _is_terminal(item.kind, item.status)
        )
        if terminal:
            rows.append(_row("result_terminal", item.path, "", cols, item))
        elif not cols:
            rows.append(_row("registry_omission", item.path, "", cols, item))
        elif cols <= TERMINAL:
            rows.append(_row("registry_closed_stale", item.path, "", cols, item))
    for target, cols in targeted.items():
        if target not in outstanding_paths and cols & NON_TERMINAL:
            rows.append(_classify_target(root, target, cols, by_slug))
    for entry in untargeted:
        if entry.collection not in NON_TERMINAL:
            continue
        value = entry.value
        legacy = eng._is_legacy_spec_path(value) or (
            isinstance(value, dict) and "path" not in value and isinstance(value.get("slug"), str)
        )
        cls = "legacy_shape" if legacy else "unclassified"
        rows.append(_row(cls, "", entry.location, [entry.collection]))
    order = {name: index for index, name in enumerate(CLASSES)}
    return sorted(rows, key=lambda r: (order[r.cls], r.target, r.location))


# ── Output ────────────────────────────────────────────────────────────────────


def _counts(rows: list[Row]) -> dict[str, int]:
    return {name: sum(1 for r in rows if r.cls == name) for name in CLASSES}


def render_text(rows: list[Row], commit: str, workspace_sha256: str) -> str:
    """The default output: result, counts, FAIL lines, commit, registry digest."""
    failing = [r for r in rows if r.failing]
    lines = ["registry comparison: " + ("fail" if failing else "pass")]
    lines += [f"{name} {count}" for name, count in _counts(rows).items()]
    for r in failing:
        dump = lambda value: json.dumps(value, ensure_ascii=True)  # noqa: E731
        lines.append(
            f"FAIL {r.cls} {dump(r.target)} {dump(r.location)} {dump(list(r.collections))}"
        )
    lines.append(f"commit {commit}")
    lines.append(f"workspace.toml sha256 {workspace_sha256}")
    return "\n".join(lines) + "\n"


def render_json(rows: list[Row], commit: str, workspace_sha256: str, generated_at: str) -> str:
    """The `--format json` output: one `registry-comparison.v1` object."""
    result = "fail" if any(r.failing for r in rows) else "pass"
    payload = {
        "schema": "registry-comparison.v1",
        "result": result,
        "counts": _counts(rows),
        "differences": [r.as_json() for r in rows],
        "inputs": {
            "commit": commit, "workspace_sha256": workspace_sha256,
            "generated_at": generated_at,
        },
    }
    return json.dumps(payload, ensure_ascii=True, indent=2) + "\n"


def git_head(root: Path) -> str:
    """`git rev-parse HEAD` in *root*, or `unknown`."""
    try:
        done = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True,
            check=False, timeout=30, stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    head = done.stdout.strip()
    return head if done.returncode == 0 and re.fullmatch(r"[0-9a-f]{40,64}", head) else "unknown"


# ── Command line ──────────────────────────────────────────────────────────────


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        """Route usage errors to the one-line refusal."""
        raise Refusal("arguments", message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="compare-registry.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", required=True, help="repository root to compare")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def run(argv: list[str]) -> int:
    """Gather the inputs in AC-0019's order, classify, print, and return the exit code."""
    args = _parser().parse_args(argv)
    root = Path(args.root)
    registry, raw = load_registry(root)
    items, generated_at = check_envelope(run_outstanding(root))
    paths = graph_paths(root)
    outstanding: list[Outstanding] = []
    seen: set[str] = set()
    for item in items:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        if item["id"] not in paths:
            raise Refusal("graph", "an outstanding item's id has no path in the graph")
        outstanding.append(
            Outstanding(paths[item["id"]], item["id"], item["type"], item["status"])
        )
    captured = captured_listing(root)
    outstanding += [
        Outstanding(str(c["path"]), "", "captured", "Open")
        for c in captured if c["status"] == "Open"
    ]
    rows = classify(registry, outstanding, captured, root)
    commit = git_head(root)
    digest = hashlib.sha256(raw).hexdigest()
    if args.format == "json":
        text = render_json(rows, commit, digest, generated_at)
    else:
        text = render_text(rows, commit, digest)
    sys.stdout.write(text)
    return 1 if any(r.failing for r in rows) else 0


def main(argv: list[str] | None = None) -> int:
    """Run the comparison; every refusal and error is one stderr line, exit 2."""
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except SystemExit as exc:  # `--help` only: usage errors are a Refusal
        return exc.code if isinstance(exc.code, int) else 0
    except Refusal as exc:
        sys.stderr.write(f"refused: {_one_line(exc.input_name)}: {_one_line(exc.reason)}\n")
        return 2
    except Exception as exc:  # noqa: BLE001 - an error must never read as exit 1
        sys.stderr.write(f"refused: internal: {_one_line(f'{type(exc).__name__}: {exc}')}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
