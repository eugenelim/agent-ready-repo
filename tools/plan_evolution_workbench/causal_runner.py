#!/usr/bin/env python3
"""Manual handoff adapter for the Codex collaboration causal study."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_JSON_BYTES = 1_000_000
MAX_PROGRESS_BYTES = 4_000_000
MAX_LINE_BYTES = 64_000
MAX_CAPTURE_BYTES = 64_000
MAX_ARTIFACT_BYTES = 262_144
MAX_SUMMARY_BYTES = 32_768
MAX_JSON_DEPTH = 24
MAX_COLLECTION_ITEMS = 2_000
STUDY_ID = "codex-collaboration-r1"
STUDY_CEILING = 600
MAXIMUM_USED = 566
SAFE_STATUSES = {"passed", "failed", "capped", "non-executed"}
PHASE_ORDER = (
    "assignment-frozen",
    "phase-reserved",
    "phase-launched",
    "phase-terminal",
    "candidate-frozen",
    "grade-terminal",
    "slot-terminal",
)
LEGACY_OUTPUT_NAMES = {
    "results.json",
    "evidence-index.json",
    "wave-1.json",
    "w1-gate-memo.json",
    "w2-gate-memo.json",
    "t6-review-memo.json",
}
SUSPECT_MARKERS = (
    "api_key",
    "apikey",
    "authorization:",
    "bearer ",
    "password",
    "private key",
    "secret",
    "token",
)


class WorkbenchError(ValueError):
    """Base exception for terminal adapter refusals."""


class SchemaError(WorkbenchError):
    """A structured input failed strict validation."""


class ReceiptError(WorkbenchError):
    """A phase receipt would create a gap, duplicate, or reordering."""


class PolicyError(WorkbenchError):
    """A command, path, or retention action violates the frozen policy."""


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise SchemaError(f"duplicate JSON key: {key}")
        seen.add(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise SchemaError(f"non-finite JSON value: {value}")


def _check_bounds(value: Any, *, depth: int = 0) -> None:
    if depth > MAX_JSON_DEPTH:
        raise SchemaError("JSON nesting limit exceeded")
    if isinstance(value, dict):
        if len(value) > MAX_COLLECTION_ITEMS:
            raise SchemaError("object field limit exceeded")
        for key, child in value.items():
            if not isinstance(key, str):
                raise SchemaError("object keys must be strings")
            _check_bounds(child, depth=depth + 1)
        return
    if isinstance(value, list):
        if len(value) > MAX_COLLECTION_ITEMS:
            raise SchemaError("array item limit exceeded")
        for child in value:
            _check_bounds(child, depth=depth + 1)
        return
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_LINE_BYTES:
            raise SchemaError("string byte limit exceeded")
        return
    if isinstance(value, float) and not math.isfinite(value):
        raise SchemaError("non-finite JSON number")


def parse_json_bytes(raw: bytes, *, max_bytes: int = MAX_JSON_BYTES) -> Any:
    """Parse bounded strict JSON."""
    if len(raw) > max_bytes:
        raise SchemaError("JSON byte limit exceeded")
    try:
        parsed = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except UnicodeDecodeError as exc:
        raise SchemaError("JSON must be UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise SchemaError(f"malformed JSON: {exc.msg}") from exc
    _check_bounds(parsed)
    return parsed


def _read_regular(path: Path, *, max_bytes: int = MAX_JSON_BYTES) -> bytes:
    resolved_parent = path.parent.resolve(strict=True)
    target = resolved_parent / path.name
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(target, flags)
    try:
        before = os.fstat(fd)
        if not target.is_file() or before.st_nlink != 1:
            raise PolicyError("path is not a single regular file")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 65_536)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise SchemaError("file byte limit exceeded")
            chunks.append(chunk)
        after = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_size) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
        ):
            raise PolicyError("file identity changed while reading")
        return b"".join(chunks)
    finally:
        os.close(fd)


def load_design(path: Path) -> dict[str, Any]:
    """Load a strict bounded design document."""
    data = parse_json_bytes(_read_regular(path))
    if not isinstance(data, dict):
        raise SchemaError("design root must be an object")
    validate_design(data)
    return data


def digest_json(value: Any) -> str:
    """Return a stable SHA-256 digest for a JSON-compatible value."""
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _expect_keys(value: dict[str, Any], keys: set[str], label: str) -> None:
    actual = set(value)
    if actual != keys:
        raise SchemaError(
            f"{label} fields mismatch: missing={sorted(keys - actual)} "
            f"extra={sorted(actual - keys)}"
        )


def _expect_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise SchemaError(f"{label} must be a non-empty string")
    return value


def _expect_pos_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SchemaError(f"{label} must be a positive integer")
    return value


def validate_design(design: dict[str, Any]) -> dict[str, Any]:
    """Validate the frozen causal design and return its allocation summary."""
    _expect_keys(
        design,
        {
            "schema_version",
            "study_id",
            "study_ceiling",
            "maximum_used",
            "seed",
            "models",
            "tasks",
            "runs",
            "allocations",
            "command_policy",
            "raw_artifact_policy",
            "holdout_release",
        },
        "design",
    )
    if design["schema_version"] != 1:
        raise SchemaError("unsupported design schema")
    if design["study_id"] != STUDY_ID:
        raise SchemaError("unexpected study id")
    if design["study_ceiling"] != STUDY_CEILING:
        raise SchemaError("study ceiling must be exactly 600")
    if design["maximum_used"] != MAXIMUM_USED:
        raise SchemaError("maximum used must be exactly 566")
    if sum(design["allocations"].values()) != MAXIMUM_USED:
        raise SchemaError("allocations must sum to 566")
    if design["holdout_release"] is not False:
        raise SchemaError("holdouts must start unreleased")
    _validate_tasks(design["tasks"])
    _validate_runs(design["runs"])
    _validate_policy(design["command_policy"], design["raw_artifact_policy"])
    return {
        "study_id": STUDY_ID,
        "study_ceiling": STUDY_CEILING,
        "maximum_used": MAXIMUM_USED,
        "allocations": dict(design["allocations"]),
    }


def _validate_tasks(tasks: Any) -> None:
    if not isinstance(tasks, list) or len(tasks) != 8:
        raise SchemaError("design must contain six main tasks and two holdouts")
    seen: set[str] = set()
    main = holdout = 0
    complex_main = medium_main = 0
    for task in tasks:
        if not isinstance(task, dict):
            raise SchemaError("task must be an object")
        _expect_keys(task, {"id", "use", "complexity", "provenance"}, "task")
        task_id = _expect_str(task["id"], "task id")
        if task_id in seen:
            raise SchemaError("duplicate task id")
        seen.add(task_id)
        use = task["use"]
        complexity = task["complexity"]
        if use == "main":
            main += 1
            if complexity == "complex":
                complex_main += 1
            elif complexity == "medium":
                medium_main += 1
            else:
                raise SchemaError("main complexity must be medium or complex")
        elif use == "holdout":
            holdout += 1
            if complexity != "medium":
                raise SchemaError("holdouts must be medium")
        else:
            raise SchemaError("task use must be main or holdout")
        if task["provenance"] not in {"pre-build", "reconstructed"}:
            raise SchemaError("unknown task provenance")
    if (main, holdout, medium_main, complex_main) != (6, 2, 3, 3):
        raise SchemaError("unexpected task split")


def _validate_runs(runs: Any) -> None:
    if not isinstance(runs, dict):
        raise SchemaError("runs must be an object")
    required = {"run-0", "run-1", "runs-2-5", "run-6", "run-7", "holdout"}
    _expect_keys(runs, required, "runs")
    if runs["run-1"]["replications"] != 3 or len(runs["run-1"]["policies"]) != 3:
        raise SchemaError("run-1 must have three policies and replications")
    if runs["runs-2-5"]["replications"] != 3 or len(runs["runs-2-5"]["build_arms"]) != 5:
        raise SchemaError("shared panel must have five arms and three replications")
    if runs["run-6"]["replications"] != 3:
        raise SchemaError("run-6 must have three replications")
    if runs["run-7"]["repair_opportunities"] != 2:
        raise SchemaError("run-7 repair opportunities changed")
    if runs["holdout"]["replications"] != 3:
        raise SchemaError("holdout replications changed")


def _validate_policy(command_policy: Any, raw_policy: Any) -> None:
    if not isinstance(command_policy, dict) or not isinstance(raw_policy, dict):
        raise SchemaError("policies must be objects")
    required = {
        "shell_free",
        "network",
        "egress",
        "environment",
        "timeout_seconds",
        "max_output_bytes",
        "process_tree_cleanup",
        "terminal_on_unenforceable",
    }
    _expect_keys(command_policy, required, "command policy")
    if command_policy["shell_free"] is not True:
        raise SchemaError("commands must be shell-free")
    if command_policy["network"] != "denied" or command_policy["egress"] != "denied":
        raise SchemaError("network and egress must be denied")
    if command_policy["environment"] != "explicit-secret-free":
        raise SchemaError("environment policy changed")
    if command_policy["process_tree_cleanup"] is not True:
        raise SchemaError("process-tree cleanup is required")
    if command_policy["terminal_on_unenforceable"] != "non-executed":
        raise SchemaError("unenforceable controls must stop without execution")
    if _expect_pos_int(command_policy["timeout_seconds"], "timeout") > 600:
        raise SchemaError("timeout too large")
    if _expect_pos_int(command_policy["max_output_bytes"], "output cap") > MAX_CAPTURE_BYTES:
        raise SchemaError("output cap too large")
    _expect_keys(raw_policy, {"max_bytes", "retention_days", "privacy_screen"}, "raw policy")
    if _expect_pos_int(raw_policy["max_bytes"], "raw max bytes") > MAX_ARTIFACT_BYTES:
        raise SchemaError("raw artifact cap too large")
    if raw_policy["privacy_screen"] != "digest-only-quarantine":
        raise SchemaError("raw privacy screen changed")


def compile_assignments(design: dict[str, Any]) -> dict[str, Any]:
    """Compile deterministic assignments without releasing holdouts."""
    validate_design(design)
    tasks = list(design["tasks"])
    main_tasks = [task for task in tasks if task["use"] == "main"]
    holdout_tasks = [task for task in tasks if task["use"] == "holdout"]
    rng = random.Random(str(design["seed"]))
    assignments: list[dict[str, Any]] = []
    ordinal = 1

    def add(
        *,
        run: str,
        role: str,
        task_id: str,
        replication: int,
        arm: str,
        released: bool,
    ) -> None:
        nonlocal ordinal
        assignments.append(
            {
                "slot_id": f"{run}:{ordinal:03d}",
                "study_ordinal": ordinal,
                "run": run,
                "role": role,
                "task_id": task_id,
                "replication": replication,
                "blind_arm": arm,
                "requested_model": _requested_model(design, role, arm),
                "telemetry": unavailable_telemetry(),
                "released": released,
            }
        )
        ordinal += 1

    for index in range(1, 9):
        add(
            run="run-0",
            role="calibration",
            task_id=f"disposable-{1 + (index % 2)}",
            replication=index,
            arm="calibration",
            released=True,
        )
    for task in _shuffle(rng, main_tasks):
        for replication in range(1, 4):
            add(
                run="runs-2-5",
                role="planner",
                task_id=task["id"],
                replication=replication,
                arm="shared-plan",
                released=False,
            )
            for arm in _shuffle(rng, list(design["runs"]["runs-2-5"]["build_arms"])):
                add(
                    run="runs-2-5",
                    role="builder",
                    task_id=task["id"],
                    replication=replication,
                    arm=arm,
                    released=False,
                )
    for task in _shuffle(rng, main_tasks):
        for replication in range(1, 4):
            for policy, opportunities in (
                ("full-replay", 3),
                ("delta-affected", 3),
                ("closure", 2),
            ):
                for opportunity in range(1, opportunities + 1):
                    add(
                        run="run-1",
                        role="reviewer",
                        task_id=task["id"],
                        replication=replication,
                        arm=f"{policy}:{opportunity}",
                        released=False,
                    )
    selected_run6 = _balanced_four(main_tasks)
    for task in _shuffle(rng, selected_run6):
        for replication in range(1, 4):
            for planner in ("standard-planner", "frontier-planner"):
                for builder in ("standard-builder", "frontier-builder"):
                    arm = f"{planner}+{builder}"
                    add(
                        run="run-6",
                        role="planner",
                        task_id=task["id"],
                        replication=replication,
                        arm=arm,
                        released=False,
                    )
                    add(
                        run="run-6",
                        role="builder",
                        task_id=task["id"],
                        replication=replication,
                        arm=arm,
                        released=False,
                    )
    for trajectory in range(1, 37):
        task = main_tasks[(trajectory - 1) % len(main_tasks)]
        policy = design["runs"]["run-1"]["policies"][(trajectory - 1) % 3]
        opportunities = 3 if policy != "closure" else 2
        for opportunity in range(1, opportunities + 1):
            add(
                run="run-7",
                role="reviewer",
                task_id=task["id"],
                replication=trajectory,
                arm=f"{policy}:{opportunity}",
                released=False,
            )
    for trajectory in range(1, 37):
        task = main_tasks[(trajectory - 1) % len(main_tasks)]
        for opportunity in range(1, 3):
            add(
                run="run-7",
                role="repairer",
                task_id=task["id"],
                replication=trajectory,
                arm=f"repair:{opportunity}",
                released=False,
            )
    for run in ("run-1", "run-7"):
        for batch in range(1, 13):
            add(
                run=run,
                role="adjudicator",
                task_id=f"{run}-batch-{batch}",
                replication=batch,
                arm="blind-batch",
                released=False,
            )
    holdout_assignments: list[dict[str, Any]] = []
    for task in _shuffle(rng, holdout_tasks):
        for replication in range(1, 4):
            for role in ("planner", "builder", "builder"):
                add(
                    run="holdout",
                    role=role,
                    task_id=task["id"],
                    replication=replication,
                    arm="frozen-selection",
                    released=False,
                )
                holdout_assignments.append(assignments[-1])
    if ordinal - 1 != MAXIMUM_USED:
        raise SchemaError("compiled allocation does not equal 566")
    return {
        "schema_version": 1,
        "study_id": STUDY_ID,
        "study_ceiling": STUDY_CEILING,
        "maximum_used": MAXIMUM_USED,
        "shared_plan_authors": _count(assignments, "runs-2-5", "planner"),
        "shared_build_panel": _count(assignments, "runs-2-5", "builder"),
        "blind_adjudication_starts": {
            "run-1": _count(assignments, "run-1", "adjudicator"),
            "run-7": _count(assignments, "run-7", "adjudicator"),
        },
        "holdout_assignments": holdout_assignments,
        "assignments": assignments,
        "assignment_digest": digest_json(assignments),
    }


def _shuffle(rng: random.Random, values: list[Any]) -> list[Any]:
    result = list(values)
    rng.shuffle(result)
    return result


def _balanced_four(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for candidate in itertools.combinations(tasks, 4):
        medium = sum(1 for task in candidate if task["complexity"] == "medium")
        complex_ = sum(1 for task in candidate if task["complexity"] == "complex")
        prebuild = sum(1 for task in candidate if task["provenance"] == "pre-build")
        reconstructed = sum(
            1 for task in candidate if task["provenance"] == "reconstructed"
        )
        if (medium, complex_, prebuild, reconstructed) == (2, 2, 2, 2):
            return list(candidate)
    raise SchemaError("run-6 task panel cannot satisfy balance constraints")


def _count(assignments: list[dict[str, Any]], run: str, role: str) -> int:
    return sum(1 for item in assignments if item["run"] == run and item["role"] == role)


def _requested_model(design: dict[str, Any], role: str, arm: str) -> str:
    models = design["models"]
    if "frontier" in arm:
        return models["frontier"]
    if role == "adjudicator":
        return models["frontier"]
    return models["standard"]


def unavailable_telemetry() -> dict[str, str]:
    """Return explicit unavailable telemetry fields; never invent usage."""
    return {
        "wall_clock_seconds": "unavailable",
        "provider_tokens": "unavailable",
        "served_model": "unavailable",
        "session_identity": "unavailable",
    }


@dataclass(frozen=True)
class CommandRecord:
    """Validated candidate command record."""

    status: str
    argv: tuple[str, ...]
    cwd: str
    stdout_digest: str
    stderr_digest: str
    timed_out: bool
    note: str


def validate_candidate_command(command: dict[str, Any], *, run_dir: Path) -> None:
    """Validate AC-0007A before a command may execute."""
    required = {
        "argv",
        "cwd",
        "env",
        "timeout_seconds",
        "max_output_bytes",
        "network",
        "egress",
        "read_roots",
        "write_roots",
        "process_tree_cleanup",
    }
    _expect_keys(command, required, "command")
    argv = command["argv"]
    if (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(item, str) and item for item in argv)
    ):
        raise PolicyError("argv must be a non-empty literal list")
    if any(
        any(marker in item for marker in (";", "&&", "||", "|", "$(", "`"))
        for item in argv
    ):
        raise PolicyError("shell-like argv is not permitted")
    cwd = _confined(run_dir, Path(_expect_str(command["cwd"], "cwd")))
    if not cwd.is_dir():
        raise PolicyError("cwd must be a confined directory")
    env = command["env"]
    if not isinstance(env, dict) or any(
        _env_is_sensitive(k, v) for k, v in env.items()
    ):
        raise PolicyError("environment must be explicit and secret-free")
    if command["network"] != "denied" or command["egress"] != "denied":
        raise PolicyError("network and egress must be denied")
    if command["process_tree_cleanup"] is not True:
        raise PolicyError("process-tree cleanup must be enforceable")
    if _expect_pos_int(command["timeout_seconds"], "timeout") > 600:
        raise PolicyError("timeout exceeds cap")
    if _expect_pos_int(command["max_output_bytes"], "output cap") > MAX_CAPTURE_BYTES:
        raise PolicyError("output cap exceeds limit")
    for field in ("read_roots", "write_roots"):
        roots = command[field]
        if not isinstance(roots, list) or not roots:
            raise PolicyError(f"{field} must be a non-empty list")
        for item in roots:
            root = _confined(run_dir, Path(_expect_str(item, field)))
            if not root.exists():
                raise PolicyError(f"{field} entry is absent")


def _env_is_sensitive(key: Any, value: Any) -> bool:
    if not isinstance(key, str) or not isinstance(value, str):
        return True
    text = f"{key}={value}".lower()
    return any(marker in text for marker in SUSPECT_MARKERS)


def execute_candidate_command(command: dict[str, Any], *, run_dir: Path) -> CommandRecord:
    """Run a bounded local command only after all controls validate."""
    try:
        validate_candidate_command(command, run_dir=run_dir)
    except (PolicyError, SchemaError) as exc:
        return CommandRecord(
            status="non-executed",
            argv=tuple(str(item) for item in command.get("argv", ())),
            cwd=str(command.get("cwd", "")),
            stdout_digest="sha256:" + hashlib.sha256(b"").hexdigest(),
            stderr_digest="sha256:" + hashlib.sha256(str(exc).encode()).hexdigest(),
            timed_out=False,
            note=str(exc),
        )
    argv = tuple(command["argv"])
    cwd = _confined(run_dir, Path(command["cwd"]))
    timeout = int(command["timeout_seconds"])
    cap = int(command["max_output_bytes"])
    start = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            env=dict(command["env"]),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        stdout = proc.stdout[:cap]
        stderr = proc.stderr[:cap]
        status = "passed" if proc.returncode == 0 else "failed"
        if len(proc.stdout) > cap or len(proc.stderr) > cap:
            status = "capped"
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"")[:cap]
        stderr = (exc.stderr or b"")[:cap]
        status = "capped"
        return CommandRecord(
            status,
            argv,
            str(cwd),
            _sha(stdout),
            _sha(stderr),
            True,
            "timeout",
        )
    return CommandRecord(
        status,
        argv,
        str(cwd),
        _sha(stdout),
        _sha(stderr),
        False,
        f"{time.monotonic() - start:.3f}s",
    )


def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def retain_raw_artifact(run_dir: Path, name: str, raw: bytes) -> dict[str, Any]:
    """Retain safe bounded raw bytes or persist only a digest quarantine record."""
    if "/" in name or "\\" in name or name.startswith("."):
        raise PolicyError("artifact name must be local and visible")
    digest = _sha(raw)
    lower = raw[:4096].decode("utf-8", errors="ignore").lower()
    suspected = len(raw) > MAX_ARTIFACT_BYTES or any(
        marker in lower for marker in SUSPECT_MARKERS
    )
    if suspected:
        return {
            "name": name,
            "status": "quarantined",
            "digest": digest,
            "retained": False,
            "reason": "privacy-or-byte-limit",
        }
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    target = _confined(raw_dir, Path(name))
    target.write_bytes(raw)
    return {"name": name, "status": "retained", "digest": digest, "retained": True}


def provider_output_path(path: Path) -> Path:
    """Protect legacy records from provider-labelled causal outputs."""
    if path.name in LEGACY_OUTPUT_NAMES:
        raise PolicyError("legacy output cannot be overwritten")
    if not (
        path.name.startswith("codex-collaboration-")
        or path.name.startswith("causal-")
        or path.name == "report.md"
    ):
        raise PolicyError("output must be provider-labelled")
    return path


class PhaseLedger:
    """Append-only phase ledger with strict ordering and terminal accounting."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.events: dict[str, list[str]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        raw = _read_regular(self.path, max_bytes=MAX_PROGRESS_BYTES)
        lines = raw.splitlines(keepends=True)
        for index, line in enumerate(lines):
            if len(line) > MAX_LINE_BYTES:
                raise SchemaError("progress line limit exceeded")
            if not line.endswith(b"\n"):
                if index == len(lines) - 1:
                    break
                raise SchemaError("unterminated progress line before final")
            data = parse_json_bytes(line.rstrip(b"\n"), max_bytes=MAX_LINE_BYTES)
            if not isinstance(data, dict):
                raise SchemaError("progress event must be an object")
            _expect_keys(
                data,
                {"slot_id", "phase", "status", "timestamp", "note"},
                "progress event",
            )
            phase = _expect_str(data["phase"], "phase")
            slot = _expect_str(data["slot_id"], "slot id")
            self._check_next(slot, phase)
            self.events.setdefault(slot, []).append(phase)

    def append(
        self,
        slot_id: str,
        phase: str,
        *,
        status: str = "done",
        note: str = "ok",
    ) -> None:
        """Append exactly the next phase for a slot."""
        if status not in {"done", "failed", "capped", "non-executed"}:
            raise ReceiptError("unknown receipt status")
        self._check_next(slot_id, phase)
        payload = {
            "slot_id": slot_id,
            "phase": phase,
            "status": status,
            "timestamp": time.time(),
            "note": note,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
            )
        self.events.setdefault(slot_id, []).append(phase)

    def _check_next(self, slot_id: str, phase: str) -> None:
        if phase not in PHASE_ORDER:
            raise ReceiptError("unknown phase")
        seen = self.events.get(slot_id, [])
        if phase in seen:
            raise ReceiptError("duplicate phase")
        expected = PHASE_ORDER[len(seen)]
        if phase != expected:
            raise ReceiptError(f"phase gap or reordering: expected {expected}")


def prepare_slot(run_dir: Path, slot_id: str) -> dict[str, Any]:
    """Prepare a disposable slot root from a compiled assignment."""
    compiled = _load_run_compiled(run_dir)
    assignment = _find_assignment(compiled, slot_id)
    slot_root = _confined(run_dir, Path("slots") / slot_id.replace(":", "_"))
    if slot_root.exists():
        raise PolicyError("slot root already exists")
    (slot_root / "candidate").mkdir(parents=True)
    (slot_root / "receipts").mkdir()
    PhaseLedger(run_dir / "progress.jsonl").append(slot_id, "assignment-frozen")
    return {
        "slot_id": slot_id,
        "slot_root": str(slot_root),
        "assignment_digest": digest_json(assignment),
    }


def record_launch(run_dir: Path, slot_id: str, agent_id: str) -> dict[str, Any]:
    """Record a simulated controller launch without invoking a model."""
    _expect_str(agent_id, "agent id")
    ledger = PhaseLedger(run_dir / "progress.jsonl")
    ledger.append(slot_id, "phase-reserved")
    ledger.append(slot_id, "phase-launched", note=f"agent:{agent_id}")
    return {
        "slot_id": slot_id,
        "agent_id": agent_id,
        "telemetry": unavailable_telemetry(),
    }


def ingest_terminal(run_dir: Path, slot_id: str, report_path: Path) -> dict[str, Any]:
    """Ingest one terminal report as inert bounded JSON."""
    report = parse_json_bytes(_read_regular(report_path, max_bytes=MAX_JSON_BYTES))
    if not isinstance(report, dict):
        raise SchemaError("terminal report must be an object")
    _expect_keys(
        report,
        {"slot_id", "status", "summary", "deviations", "telemetry"},
        "terminal report",
    )
    if report["slot_id"] != slot_id:
        raise SchemaError("terminal report slot mismatch")
    if report["status"] not in SAFE_STATUSES:
        raise SchemaError("unknown terminal status")
    if report["telemetry"] != unavailable_telemetry():
        raise SchemaError("telemetry must remain explicitly unavailable")
    target = _confined(run_dir, Path("terminals") / f"{slot_id.replace(':', '_')}.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(target, report)
    PhaseLedger(run_dir / "progress.jsonl").append(
        slot_id,
        "phase-terminal",
        status="done",
    )
    return {"slot_id": slot_id, "report_digest": digest_json(report)}


def grade_slot(run_dir: Path, slot_id: str) -> dict[str, Any]:
    """Write a deterministic simulated grade over a terminal receipt."""
    terminal = _confined(run_dir, Path("terminals") / f"{slot_id.replace(':', '_')}.json")
    if not terminal.exists():
        raise SchemaError("terminal report is required before grading")
    report = parse_json_bytes(_read_regular(terminal))
    grade = {
        "slot_id": slot_id,
        "status": "graded",
        "candidate_digest": digest_json({"slot_id": slot_id, "simulated": True}),
        "terminal_digest": digest_json(report),
        "oracle": "simulated-no-model",
    }
    target = _confined(run_dir, Path("grades") / f"{slot_id.replace(':', '_')}.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(target, grade)
    ledger = PhaseLedger(run_dir / "progress.jsonl")
    ledger.append(slot_id, "candidate-frozen")
    ledger.append(slot_id, "grade-terminal")
    ledger.append(slot_id, "slot-terminal")
    return grade


def summarize_run(run_dir: Path, output: Path) -> dict[str, Any]:
    """Produce a bounded provider-labelled summary from local receipts."""
    output = provider_output_path(output)
    compiled = _load_run_compiled(run_dir)
    progress = PhaseLedger(run_dir / "progress.jsonl")
    grades = (
        sorted((run_dir / "grades").glob("*.json"))
        if (run_dir / "grades").exists()
        else []
    )
    summary = {
        "schema_version": 1,
        "study_id": STUDY_ID,
        "compiled_digest": digest_json(compiled),
        "slots_terminal": sum(
            1 for phases in progress.events.values() if phases == list(PHASE_ORDER)
        ),
        "grades": len(grades),
        "telemetry": unavailable_telemetry(),
    }
    encoded = json.dumps(summary, indent=2, sort_keys=True).encode("utf-8")
    if len(encoded) > MAX_SUMMARY_BYTES:
        raise SchemaError("summary byte limit exceeded")
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(output, summary)
    return summary


def _load_run_compiled(run_dir: Path) -> dict[str, Any]:
    path = _confined(run_dir, Path("compiled-assignments.json"))
    data = parse_json_bytes(_read_regular(path))
    if not isinstance(data, dict) or data.get("study_id") != STUDY_ID:
        raise SchemaError("compiled assignments missing")
    return data


def _find_assignment(compiled: dict[str, Any], slot_id: str) -> dict[str, Any]:
    for assignment in compiled["assignments"]:
        if assignment["slot_id"] == slot_id:
            return assignment
    raise SchemaError("unknown slot")


def _confined(root: Path, candidate: Path) -> Path:
    base = root.resolve(strict=False)
    target = candidate if candidate.is_absolute() else base / candidate
    resolved = target.resolve(strict=False)
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise PolicyError("path escapes declared root") from exc
    return resolved


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _cmd_validate_design(args: argparse.Namespace) -> dict[str, Any]:
    return validate_design(load_design(Path(args.design)))


def _cmd_compile(args: argparse.Namespace) -> dict[str, Any]:
    design = load_design(Path(args.design))
    compiled = compile_assignments(design)
    if args.run_dir:
        run_dir = Path(args.run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        _write_json_atomic(run_dir / "compiled-assignments.json", compiled)
    return compiled


def _cmd_prepare(args: argparse.Namespace) -> dict[str, Any]:
    return prepare_slot(Path(args.run_dir), args.slot)


def _cmd_launch(args: argparse.Namespace) -> dict[str, Any]:
    return record_launch(Path(args.run_dir), args.slot, args.agent_id)


def _cmd_ingest(args: argparse.Namespace) -> dict[str, Any]:
    return ingest_terminal(Path(args.run_dir), args.slot, Path(args.report))


def _cmd_grade(args: argparse.Namespace) -> dict[str, Any]:
    return grade_slot(Path(args.run_dir), args.slot)


def _cmd_summarize(args: argparse.Namespace) -> dict[str, Any]:
    return summarize_run(Path(args.run_dir), Path(args.output))


def build_parser() -> argparse.ArgumentParser:
    """Build the causal-runner CLI."""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-design")
    validate.add_argument("--design", required=True)
    validate.set_defaults(func=_cmd_validate_design)
    compile_p = sub.add_parser("compile-assignments")
    compile_p.add_argument("--design", required=True)
    compile_p.add_argument("--run-dir", required=False)
    compile_p.set_defaults(func=_cmd_compile)
    prepare = sub.add_parser("prepare-slot")
    prepare.add_argument("--run-dir", required=True)
    prepare.add_argument("--slot", required=True)
    prepare.set_defaults(func=_cmd_prepare)
    launch = sub.add_parser("record-launch")
    launch.add_argument("--run-dir", required=True)
    launch.add_argument("--slot", required=True)
    launch.add_argument("--agent-id", required=True)
    launch.set_defaults(func=_cmd_launch)
    ingest = sub.add_parser("ingest-terminal")
    ingest.add_argument("--run-dir", required=True)
    ingest.add_argument("--slot", required=True)
    ingest.add_argument("--report", required=True)
    ingest.set_defaults(func=_cmd_ingest)
    grade = sub.add_parser("grade-slot")
    grade.add_argument("--run-dir", required=True)
    grade.add_argument("--slot", required=True)
    grade.set_defaults(func=_cmd_grade)
    summarize = sub.add_parser("summarize")
    summarize.add_argument("--run-dir", required=True)
    summarize.add_argument("--output", required=True)
    summarize.set_defaults(func=_cmd_summarize)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
    except (WorkbenchError, OSError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
