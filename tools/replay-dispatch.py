#!/usr/bin/env python3
"""Replay header-derived dispatch over a tree and list where it differs from the base engine.

Read-only. Run it once over a `git worktree` of the snapshot commit, and record
its output in the verification ledger of docs/specs/header-derived-dispatch
(AC-0019). It has no CI job, schedule, or make target.

    python3 tools/replay-dispatch.py --root TREE --base-engine PATH

PATH is the tree's own `workspace_status.py` (the base engine, whose sibling
modules must be that commit's). The tool runs `workspace_status.py reconcile`
and this repository's `work-loop` `dispatch.py` over TREE, then prints:

  - the base `canonical.ready` and `canonical.active`, and dispatch's `ready`
    and `active`, as lists of spec paths;
  - the sha256 of TREE's `workspace.toml` and the number of lifecycle records
    (`*.json` under docs/lifecycle/);
  - each spec whose dispatch result differs from the base result: ready,
    active, and the decision (action, path, candidates) of an argless start, an
    argless resume, a named start and a named resume.

The base decision transcribes `work-loop`'s SKILL.md lines 168-195 at the
snapshot commit, the same transcription test_header_derived_dispatch_replay.py
uses (reimplemented here identically). The tool never classifies a difference:
the author does that by hand in the ledger and the owner approves it. A spec
whose directory name `dispatch.py` refuses as a selector (for example one with a
dot) is recorded with the decision action `invalid_selector` for the named shapes.

Exit codes:
  0  the lists were written
  2  refused: bad arguments, an unreadable root, or an engine that fails; one
     stderr line `refused: <input>: <reason>` and nothing on stdout

The tool writes no file, bytecode included.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # the tool writes no file

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
from concurrent.futures import ThreadPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, NoReturn  # noqa: E402

SOURCE_ROOT = Path(__file__).resolve().parent.parent
DISPATCH = SOURCE_ROOT / "packs/core/.apm/skills/work-loop/scripts/dispatch.py"
ENGINE_TIMEOUT_S = 300
WORKERS = 8
Decision = dict[str, Any]


class Refusal(Exception):
    """A refused input: prints `refused: <input>: <reason>` and exits 2."""

    def __init__(self, input_name: str, reason: str) -> None:
        super().__init__(reason)
        self.input_name = input_name
        self.reason = reason


def _one_line(text: str, limit: int = 300) -> str:
    """Escape *text* onto one printable ASCII line, bounded."""
    return json.dumps(str(text), ensure_ascii=True)[1:-1][:limit]


def _run(name: str, command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run *command*, refusing when it cannot run or times out."""
    try:
        return subprocess.run(
            command, capture_output=True, text=True, check=False,
            timeout=ENGINE_TIMEOUT_S, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as exc:
        raise Refusal(name, f"timed out after {ENGINE_TIMEOUT_S}s") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise Refusal(name, f"could not run: {type(exc).__name__}") from exc


def _json_object(name: str, done: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    """Return a zero-exit run's standard output as a JSON object."""
    if done.returncode != 0:
        raise Refusal(name, f"exited {done.returncode}: {done.stderr.strip()[:120]}")
    try:
        data = json.loads(done.stdout)
    except ValueError as exc:
        raise Refusal(name, "output is not JSON") from exc
    if not isinstance(data, dict):
        raise Refusal(name, "output is not a JSON object")
    return data


# ── The base decision (SKILL.md lines 168-195 at the snapshot commit) ─────────


def _decision(
    action: str, path: str | None = None, candidates: list[str] | None = None
) -> Decision:
    return {"action": action, "path": path, "candidates": sorted(candidates or [])}


def _matches(canonical: dict[str, Any], target: str) -> list[dict[str, Any]]:
    """The `canonical.blocked` and `canonical.findings` entries that name `target`."""
    slug = target.split("/")[2]
    spellings = {target, f"spec/{slug}", slug}
    return [
        item for item in (*canonical["blocked"], *canonical["findings"])
        if item["path"] in spellings
    ]


def base_named(canonical: dict[str, Any], mode: str, target: str) -> Decision:
    """A supplied spec path continues only with a matching evaluation and no matching block."""
    pool = canonical["ready"] if mode == "start" else canonical["active"]
    if any(item["path"] == target for item in pool) and not _matches(canonical, target):
        return _decision(mode, target)
    return _decision("refuse")


def base_argless(canonical: dict[str, Any]) -> Decision:
    """One active resumes, several ask, none falls to the first ready, else none."""
    active = [item["path"] for item in canonical["active"]]
    if len(active) == 1:
        return _decision("resume", active[0])
    if active:
        return _decision("ask", candidates=active)
    if canonical["ready"]:
        first = canonical["ready"][0]["path"]
        return _decision("refuse") if _matches(canonical, first) else _decision("start", first)
    return _decision("none")


# ── Replay ────────────────────────────────────────────────────────────────────


def spec_paths(root: Path) -> list[str]:
    """Every `docs/specs/<name>/spec.md` under *root*, symbolic links included."""
    specs = root / "docs/specs"
    if not specs.is_dir():
        return []
    return sorted(
        f"docs/specs/{child.name}/spec.md"
        for child in specs.iterdir()
        if (child / "spec.md").exists() or (child / "spec.md").is_symlink()
    )


def _slim(decision: dict[str, Any]) -> Decision:
    candidates = list(decision.get("candidates", []))
    return _decision(decision["action"], decision.get("path"), candidates)


def _paths(items: list[dict[str, Any]]) -> list[str]:
    return sorted(str(item["path"]) for item in items)


def replay(root: Path, engine: Path) -> dict[str, Any]:
    """Run both sides over *root*; return the lists, the digest, the count and the differences."""
    command = [sys.executable, "-B", str(engine), "reconcile", "--root", str(root)]
    base = _json_object("base engine", _run("base engine", command))
    canonical = base.get("canonical")
    if not isinstance(canonical, dict) or not all(
        isinstance(canonical.get(k), list) for k in ("ready", "active", "blocked", "findings")
    ):
        raise Refusal("base engine", "output lacks canonical ready, active, blocked and findings")

    def dispatch(*extra: str) -> dict[str, Any]:
        command = [sys.executable, "-B", str(DISPATCH), "--root", str(root), *extra]
        return _json_object("dispatch", _run("dispatch", command))

    def named_decision(flag: str, path: str) -> Decision:
        """A named start or resume; an invalid selector is recorded, not fatal."""
        command = [sys.executable, "-B", str(DISPATCH), "--root", str(root), flag, path]
        done = _run("dispatch", command)
        if done.returncode == 2 and done.stderr.startswith("invalid_selector"):
            return _decision("invalid_selector")
        return _slim(_json_object("dispatch", done)["decision"])

    header = dispatch()
    argless = _slim(header["decision"])
    base_argless_decision = base_argless(canonical)
    base_ready = set(_paths(canonical["ready"]))
    base_active = set(_paths(canonical["active"]))
    head_ready = set(_paths(header["ready"]))
    head_active = set(_paths(header["active"]))
    paths = spec_paths(root)
    jobs = [(mode, path) for path in paths for mode in ("--start", "--resume")]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:  # each call is its own subprocess
        results = pool.map(lambda job: named_decision(*job), jobs)
        named = dict(zip(jobs, results, strict=True))
    differing: list[dict[str, Any]] = []
    for path in paths:
        base_side = {
            "ready": path in base_ready, "active": path in base_active,
            "start": base_named(canonical, "start", path),
            "resume": base_named(canonical, "resume", path),
        }
        head_side = {
            "ready": path in head_ready, "active": path in head_active,
            "start": named[("--start", path)], "resume": named[("--resume", path)],
        }
        fields = {
            k: [base_side[k], head_side[k]] for k in base_side if base_side[k] != head_side[k]
        }
        if fields:
            differing.append({"path": path, "fields": fields})
    argless_fields = {}
    if base_argless_decision != argless:
        argless_fields = {"argless_start": [base_argless_decision, argless],
                          "argless_resume": [base_argless_decision, argless]}
    return {
        "base_ready": sorted(base_ready), "base_active": sorted(base_active),
        "dispatch_ready": sorted(head_ready), "dispatch_active": sorted(head_active),
        "argless": argless_fields, "differing": differing,
    }


def registry_digest(root: Path) -> str:
    """The sha256 of `root/workspace.toml`."""
    try:
        return hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
    except OSError as exc:
        raise Refusal("workspace.toml", f"cannot be read: {type(exc).__name__}") from exc


def lifecycle_count(root: Path) -> int:
    """The number of `*.json` lifecycle records under `docs/lifecycle/`."""
    directory = root / "docs/lifecycle"
    return sum(1 for p in directory.rglob("*.json") if p.is_file()) if directory.is_dir() else 0


def render(result: dict[str, Any], digest: str, records: int) -> str:
    """The output: four lists, digest, record count, then each differing spec."""
    dump = lambda value: json.dumps(value, ensure_ascii=True)  # noqa: E731
    lines = [
        f"base canonical.ready {len(result['base_ready'])} {dump(result['base_ready'])}",
        f"base canonical.active {len(result['base_active'])} {dump(result['base_active'])}",
        f"dispatch ready {len(result['dispatch_ready'])} {dump(result['dispatch_ready'])}",
        f"dispatch active {len(result['dispatch_active'])} {dump(result['dispatch_active'])}",
        f"workspace.toml sha256 {digest}",
        f"lifecycle records {records}",
        f"differing specs {len(result['differing'])}",
    ]
    for field, (base, head) in result["argless"].items():
        lines.append(f"DIFF * {field} base={dump(base)} dispatch={dump(head)}")
    for item in result["differing"]:
        for field, (base, head) in item["fields"].items():
            lines.append(f"DIFF {item['path']} {field} base={dump(base)} dispatch={dump(head)}")
    return "\n".join(lines) + "\n"


# ── Command line ──────────────────────────────────────────────────────────────


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        """Route usage errors to the one-line refusal."""
        raise Refusal("arguments", message)


def run(argv: list[str]) -> int:
    """Check the inputs, replay, print, and return the exit code."""
    parser = _Parser(
        prog="replay-dispatch.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", required=True, help="tree to replay over")
    parser.add_argument("--base-engine", required=True, help="that tree's workspace_status.py")
    args = parser.parse_args(argv)
    root, engine = Path(args.root), Path(args.base_engine)
    if not root.is_dir():
        raise Refusal("root", "is not a readable directory")
    if not engine.is_file():
        raise Refusal("base-engine", "is not a file")
    digest = registry_digest(root)
    result = replay(root, engine)
    sys.stdout.write(render(result, digest, lifecycle_count(root)))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the replay; every refusal and error is one stderr line, exit 2."""
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except SystemExit as exc:  # `--help` only: usage errors are a Refusal
        return exc.code if isinstance(exc.code, int) else 0
    except Refusal as exc:
        sys.stderr.write(f"refused: {_one_line(exc.input_name)}: {_one_line(exc.reason)}\n")
        return 2
    except Exception as exc:  # noqa: BLE001 - an error must never read as exit 0
        sys.stderr.write(f"refused: internal: {_one_line(f'{type(exc).__name__}: {exc}')}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
