#!/usr/bin/env python3
"""Read-only dispatch: which specs are ready, which are active, and what to do next.

Usage: dispatch.py --root <root> [--start <spec> | --resume <spec>]

The command reads each spec's own `Status:` header, its sibling `plan.md`, its
`Depends on:` targets, and a cooled spec's lifecycle record. From the root's
`workspace.toml` it drops only the repo-origin spec entries whose `needs` is an
empty array, and hands every other entry to the `workspace-status` engine
unchanged, together with one in-memory membership per remaining spec built from
its headers. It writes nothing and never picks between several candidates.

A selector is a slug, `spec/<slug>`, `docs/specs/<slug>`, `docs/specs/<slug>/`
or `docs/specs/<slug>/spec.md`.

Output: one JSON object on standard output with these keys.
  schema_version  1.
  ready           Specs whose entry sits in the work queue and is dispatchable.
  active          Specs in the work-active collection that have no finding.
  blocked         Queue or active specs that are in neither list, with findings.
  findings        Every other finding: cooling, parse, `docs/specs` and
                  unreadable-spec findings.
  decision        What to do next, with the keys below.
Each ready, active and blocked item carries `path`, `slug`, `status` and
`findings`. Each finding carries `code`, `path`, `dispatchable` and
`next_action`. Every list is sorted by `path`.

The `decision` object carries `action`, `path`, `candidates` and `findings`:
  start    Begin the one ready spec, or the named ready spec (`path` is set).
  resume   Continue the one active spec, or the named active spec.
  ask      Several specs qualify: `candidates` lists them and the caller asks.
  none     Nothing is ready or active.
  refuse   A named spec cannot start or resume, or the run is unusable;
           `findings` says why. `candidates` is empty unless the action is `ask`.

Exit codes:
  exit 0  A result was printed, whatever the decision.
  exit 2  A usage error, an invalid selector, a root that is not a real
          directory, or an engine that cannot be loaded (`engine_unavailable`
          on standard error, nothing on standard output).
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import stat  # noqa: E402
import tomllib  # noqa: E402
from pathlib import Path, PurePosixPath  # noqa: E402
from types import ModuleType  # noqa: E402
from typing import Any  # noqa: E402

SCHEMA_VERSION = 1
_WORKSPACE_MAX_BYTES = 8 * 1024 * 1024
_STATUS_COLLECTION = {"Approved": "queue", "Implementing": "active", "Shipped": "shipped"}
_PUBLIC_PATH_CHARS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-/"
)
_ENGINE_NAMES = (
    "run_canonical_reconciliation", "_resolve_cooled_state", "_metadata_from_root",
    "_legacy_canonical_alias", "_is_canonical_spec_artifact_path",
    "extract_legacy_migration_memberships", "_confined_artifact_path", "_finding",
    "WorkspaceEntry", "SourceRecord",
)
_SAFETY_NAMES = ("validate_confined_directory", "read_confined_regular_file")


class _Unavailable(Exception):
    """The engine or the file-safety module cannot be loaded as required."""


class _WorkspaceRefused(Exception):
    """`workspace.toml` cannot be used, so the run is refused."""


class _InvalidSelector(ValueError):
    """The selector is in no form the spec selector accepts."""


# --- the confined load (mirrors the engine's own confined sibling loader) -------


def _confined_module(
    skills: Path, candidate: Path, prefix: str, names: tuple[str, ...]
) -> ModuleType:
    """Load `candidate` by path under a unique name, only from inside `skills`."""
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(skills)
    except (OSError, ValueError, RuntimeError) as exc:
        raise _Unavailable(candidate.name) from exc
    if not resolved.is_file():
        raise _Unavailable(candidate.name)
    name = prefix + hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, resolved)
        if spec is None or spec.loader is None:
            raise _Unavailable(candidate.name)
        module = importlib.util.module_from_spec(spec)
        # Registered before execution so dataclass annotations resolve.
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            sys.modules.pop(name, None)
            raise _Unavailable(candidate.name) from exc
    if any(getattr(module, attribute, None) is None for attribute in names):
        raise _Unavailable(candidate.name)
    return module


def _load_modules() -> tuple[ModuleType, ModuleType]:
    """Return the engine and `file_safety`, or raise `_Unavailable`."""
    here = Path(__file__).resolve()
    scripts = here.parent
    skills = scripts.parent.parent
    if scripts.name != "scripts" or skills.name != "skills":
        raise _Unavailable("layout")
    engine = _confined_module(
        skills,
        skills / "workspace-status" / "scripts" / "workspace_status_engine.py",
        "_work_loop_dispatch_engine_",
        _ENGINE_NAMES + ("_COOLING_PAIRS",),
    )
    safety = _confined_module(
        skills, scripts / "file_safety.py", "_work_loop_dispatch_file_safety_",
        _SAFETY_NAMES + ("UnsafeContentError",),
    )
    return engine, safety


# --- selectors -------------------------------------------------------------------


def _selector_path(selector: str) -> str:
    """Return the canonical spec path a selector names, or raise `_InvalidSelector`."""
    text = selector
    parts = text.split("/")
    if len(parts) == 4 and parts[:2] == ["docs", "specs"] and parts[3] == "":
        text = "/".join(parts[:3])
    if not text or len(text) > 240 or "\\" in text or (len(text) >= 2 and text[1] == ":"):
        raise _InvalidSelector(selector)
    parts = text.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise _InvalidSelector(selector)
    if len(parts) == 1:
        slug = parts[0]
    elif len(parts) == 2 and parts[0] == "spec":
        slug = parts[1]
    elif (len(parts) == 3 and parts[:2] == ["docs", "specs"]) or (
        len(parts) == 4 and parts[:2] == ["docs", "specs"] and parts[3] == "spec.md"
    ):
        slug = parts[2]
    else:
        raise _InvalidSelector(selector)
    if (
        not slug
        or len(slug) > 200
        or not slug[0].isalnum()
        or any(not (char.isascii() and (char.isalnum() or char in "_-")) for char in slug)
    ):
        raise _InvalidSelector(selector)
    return f"docs/specs/{slug}/spec.md"


# --- output shaping --------------------------------------------------------------


def _public_path(value: object) -> str:
    """Keep a path only when it is a plain repository-relative one."""
    if not isinstance(value, str) or not value:
        return "workspace.toml"
    if any(char not in _PUBLIC_PATH_CHARS for char in value):
        return "workspace.toml"
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or value != candidate.as_posix():
        return "workspace.toml"
    if not candidate.parts or any(part in {"", ".", ".."} for part in candidate.parts):
        return "workspace.toml"
    return value


def _finding_dict(finding: Any) -> dict[str, Any]:
    return {
        "code": finding.code,
        "path": _public_path(finding.path),
        "dispatchable": finding.dispatchable,
        "next_action": finding.next_action,
    }


def _sorted(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: (item["path"], item.get("code", "")))


def _slug(path: object) -> str:
    public = _public_path(path)
    parts = public.split("/")
    if len(parts) == 4 and parts[:2] == ["docs", "specs"] and parts[3] == "spec.md":
        return parts[2]
    return public


# --- reading the repository ------------------------------------------------------


def _read_workspace(safety: ModuleType, root: Path) -> dict[str, Any] | None:
    """Read `workspace.toml` once; None when absent, `_WorkspaceRefused` when unusable."""
    path = root / "workspace.toml"
    try:
        os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise _WorkspaceRefused from exc
    try:
        data = safety.read_confined_regular_file(root, path, max_bytes=_WORKSPACE_MAX_BYTES)
        return tomllib.loads(data.decode("utf-8"))
    except (safety.UnsafeContentError, OSError, ValueError, RecursionError) as exc:
        raise _WorkspaceRefused from exc


def _is_dropped(item: object) -> bool:
    """A repo-origin spec entry whose `needs` is an empty array."""
    if not isinstance(item, dict) or item.get("kind") != "spec":
        return False
    source = item.get("source")
    needs = item.get("needs")
    return (
        isinstance(source, dict)
        and source.get("mode") == "repo-origin"
        and isinstance(needs, list)
        and not needs
    )


def _keep(node: Any, named: set[str]) -> Any:
    """Copy `node` without dropped entries, collecting the paths kept entries name."""
    if isinstance(node, dict):
        return {key: _keep(value, named) for key, value in node.items()}
    if isinstance(node, list):
        kept = [item for item in node if not _is_dropped(item)]
        for item in kept:
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                named.add(item["path"])
        return kept
    return node


def _spec_names(safety: ModuleType, root: Path) -> tuple[list[str], bool]:
    """Return the `docs/specs/` entry names, and whether the directory is refused."""
    docs, specs = root / "docs", root / "docs" / "specs"
    try:
        os.lstat(docs)
        os.lstat(specs)
    except FileNotFoundError:
        return [], False
    except OSError:
        return [], True
    try:
        safety.validate_confined_directory(root, specs)
        return sorted(child.name for child in specs.iterdir()), False
    except (safety.UnsafeContentError, OSError):
        return [], True


def _is_spec_file(safety: ModuleType, root: Path, name: str) -> bool:
    """The `docs/specs/<name>/spec.md` conditions beyond the name check."""
    directory = root / "docs" / "specs" / name
    try:
        safety.validate_confined_directory(root, directory)
        info = os.lstat(directory / "spec.md")
        if not stat.S_ISREG(info.st_mode):
            return False
        (directory / "spec.md").resolve(strict=True).relative_to(
            (root / "docs" / "specs").resolve(strict=True)
        )
    except (safety.UnsafeContentError, OSError, ValueError, RuntimeError):
        return False
    return True


def _highest_unused_initiative(used: set[str]) -> str | None:
    for number in range(999, -1, -1):
        slug = f"ini-{number:03d}"
        if slug not in used:
            return slug
    return None


# --- the run ---------------------------------------------------------------------


def _refused(finding_dicts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "ready": [], "active": [], "blocked": [],
        "findings": finding_dicts,
        "decision": _decision("refuse", findings=finding_dicts),
    }


def _decision(
    action: str,
    path: str | None = None,
    candidates: list[str] | None = None,
    findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "action": action,
        "path": path,
        "candidates": candidates or [],
        "findings": _sorted(findings or []),
    }


def dispatch(root: Path, mode: str | None = None, selector: str | None = None) -> dict[str, Any]:
    """Return the dispatch result for `root`.

    `mode` is `start`, `resume` or None; `selector` names a spec when `mode` is set.
    Raises `_Unavailable` when the engine cannot be loaded and `_InvalidSelector`
    for a selector in no accepted form.
    """
    engine, safety = _load_modules()
    target = _selector_path(selector) if mode is not None and selector is not None else None
    root = root.resolve()

    def make(code: str, path: str) -> dict[str, Any]:
        return _finding_dict(engine._finding(code, path))

    try:
        workspace = _read_workspace(safety, root)
        named: set[str] = set()
        kept: dict[str, Any] = _keep(workspace or {}, named)
        slug = _highest_unused_initiative(
            {key for key in kept if isinstance(key, str) and re.fullmatch(r"ini-[0-9]{3}", key)}
        )
        if slug is None:
            raise _WorkspaceRefused("every initiative slug is used")
    except _WorkspaceRefused:
        return _refused([make("invalid_workspace", "workspace.toml")])

    legacy_paths: dict[str, set[str]] = {}
    for membership in engine.extract_legacy_migration_memberships(kept):
        alias = engine._legacy_canonical_alias(membership.entry)
        if alias is not None:
            named.add(alias)
            legacy_paths.setdefault(alias, set()).add(membership.entry.path)

    records: list[Any] = []
    cooled, cooling_findings = engine._resolve_cooled_state(root, records, [])
    memberships: dict[str, list[dict[str, Any]]] = {"queue": [], "active": [], "shipped": []}

    def add(path: str, collection: str, parent: str | None) -> None:
        source: dict[str, Any] = {"mode": "repo-origin"}
        if parent is not None:
            source["parent"] = parent
        memberships[collection].append(
            {"path": path, "kind": "spec", "source": source,
             "summary": path.split("/")[2], "needs": []}
        )

    cooled_paths: set[str] = set()
    for record in records:
        if (record.disposition, record.post_closeout_result) not in engine._COOLING_PAIRS:
            continue
        for locator in (record.locator, *record.aliases):
            if (
                engine._is_canonical_spec_artifact_path(locator)
                and engine._confined_artifact_path(root, locator) in cooled
                and locator not in cooled_paths
            ):
                cooled_paths.add(locator)
                if locator not in named:
                    add(locator, "shipped", getattr(record, "parent", None))

    own_findings: list[dict[str, Any]] = []
    spec_names, specs_refused = _spec_names(safety, root)
    if specs_refused:
        own_findings.append(make("invalid_artifact_path", "docs/specs"))
    refused_entries: set[str] = set()
    listed: set[str] = set()
    unreadable: dict[str, dict[str, Any]] = {}
    statuses: dict[str, str | None] = {}
    for name in spec_names:
        path = f"docs/specs/{name}/spec.md"
        if not engine._is_canonical_spec_artifact_path(path):
            continue
        listed.add(path)
        if not _is_spec_file(safety, root, name):
            refused_entries.add(path)
            own_findings.append(make("invalid_artifact_path", path))
            continue
        if path in named or path in cooled_paths:
            continue
        entry = engine.WorkspaceEntry(
            path=path, kind="spec", source=engine.SourceRecord(mode="repo-origin"),
            summary=name, needs=[],
        )
        metadata = engine._metadata_from_root(root, entry)
        if metadata is None or not metadata.readable:
            unreadable[path] = make("unreadable_artifact", path)
            own_findings.append(unreadable[path])
            continue
        statuses[path] = metadata.status
        collection = _STATUS_COLLECTION.get(metadata.status or "")
        if collection is not None:
            add(path, collection, metadata.parent)

    header_workspace = dict(kept)
    header_workspace[slug] = {"name": "header-derived", "status": "active", "work": memberships}
    try:
        result = engine.run_canonical_reconciliation(header_workspace, root, cooled)
    except Exception as exc:
        raise _Unavailable("engine run failed") from exc

    def status_of(evaluation: Any) -> str | None:
        path = evaluation.entry.path
        if path in statuses:
            return statuses[path]
        if not isinstance(path, str):
            return None
        metadata = engine._metadata_from_root(root, evaluation.entry)
        return metadata.status if metadata is not None and metadata.readable else None

    def item(evaluation: Any) -> dict[str, Any]:
        return {
            "path": _public_path(evaluation.entry.path),
            "slug": _slug(evaluation.entry.path),
            "status": status_of(evaluation),
            "findings": [_finding_dict(f) for f in evaluation.findings],
        }

    ready_e = [e for e in result.evaluations
               if e.entry.kind == "spec" and e.collection == "work.queue" and e.dispatchable]
    active_e = [e for e in result.evaluations
                if e.entry.kind == "spec" and e.collection == "work.active" and not e.findings]
    listed_ids = {id(e) for e in ready_e} | {id(e) for e in active_e}
    blocked_e = [e for e in result.evaluations
                 if e.collection in ("work.queue", "work.active") and id(e) not in listed_ids]
    in_blocked = {id(f) for e in blocked_e for f in e.findings}
    ready, active, blocked = (
        _sorted([item(e) for e in group]) for group in (ready_e, active_e, blocked_e)
    )
    findings = _sorted(
        [
            _finding_dict(f)
            for f in (*cooling_findings, *result.findings)
            if id(f) not in in_blocked
        ]
        + own_findings
    )

    ready_paths, active_paths = [i["path"] for i in ready], [i["path"] for i in active]
    if mode is None:
        if len(active_paths) == 1:
            decision = _decision("resume", active_paths[0])
        elif active_paths:
            decision = _decision("ask", candidates=active_paths)
        elif len(ready_paths) == 1:
            decision = _decision("start", ready_paths[0])
        elif ready_paths:
            decision = _decision("ask", candidates=ready_paths)
        else:
            decision = _decision("none")
    elif mode == "start" and target in ready_paths:
        decision = _decision("start", target)
    elif mode == "resume" and target in active_paths:
        decision = _decision("resume", target)
    else:
        assert target is not None
        decision = _decision("refuse", findings=_refusal(
            make, mode, target, blocked=blocked, result=result, named=named,
            legacy_paths=legacy_paths, cooled_paths=cooled_paths, specs_refused=specs_refused,
            refused_entries=refused_entries, listed=listed, unreadable=unreadable,
            statuses=statuses,
        ))
    return {
        "schema_version": SCHEMA_VERSION,
        "ready": ready, "active": active, "blocked": blocked,
        "findings": findings, "decision": decision,
    }


def _refusal(
    make: Any, mode: str, target: str, **facts: Any
) -> list[dict[str, Any]]:
    """The findings that explain a refused named invocation, by the first rule that applies."""
    for blocked in facts["blocked"]:
        if blocked["path"] == target and blocked["findings"]:
            return list(blocked["findings"])
    result = facts["result"]
    if target in facts["named"]:
        evaluated = [e for e in result.evaluations if e.entry.path == target]
        if evaluated:
            found = [_finding_dict(f) for e in evaluated for f in e.findings]
        else:
            spellings = {target, *facts["legacy_paths"].get(target, set())}
            found = [_finding_dict(f) for f in result.findings if f.path in spellings]
        return found or [make("impossible_transition", target)]
    if target in facts["cooled_paths"]:
        return [make("impossible_transition", target)]
    if facts["specs_refused"]:
        return [make("invalid_artifact_path", "docs/specs")]
    if target in facts["refused_entries"]:
        return [make("invalid_artifact_path", target)]
    if target not in facts["listed"]:
        return [make("missing_artifact", target)]
    if target in facts["unreadable"]:
        return [facts["unreadable"][target]]
    status = facts["statuses"].get(target)
    if (mode == "start" and status in ("Implementing", "Shipped")) or (
        mode == "resume" and status != "Implementing"
    ):
        return [make("impossible_transition", target)]
    return [make("unapproved_spec", target)]


# --- command line ----------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dispatch.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", required=True, help="repository root to read")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--start", metavar="SPEC", help="start the named spec")
    group.add_argument("--resume", metavar="SPEC", help="resume the named spec")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Print the dispatch result as JSON. Exit 0 for any result, 2 for a usage or load error."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")
    args = _parser().parse_args(argv)
    mode = "start" if args.start is not None else "resume" if args.resume is not None else None
    selector = args.start if args.start is not None else args.resume
    root = Path(args.root)
    if not root.is_dir():
        print("invalid_root: --root is not a directory", file=sys.stderr)
        return 2
    try:
        result = dispatch(root, mode, selector)
    except _InvalidSelector:
        print("invalid_selector: the spec selector is in no accepted form", file=sys.stderr)
        return 2
    except _Unavailable as exc:
        print(f"engine_unavailable: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
