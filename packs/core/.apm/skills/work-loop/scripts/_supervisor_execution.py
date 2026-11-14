"""Closed gate-execution.v1 records and gate-command validation.

These pure codecs confer no execution authority: the supervisor must write and
bind records itself. Records have schema_version 1 and type gate-execution.v1;
unknown, missing and extra fields refuse, including per-command fields. Digests
are lowercase SHA-256. task_revision is null for a run-wide gate. outcome is
started, passed or failed; a started record has no command results, and only a
nonempty set of successful, non-timeout results can pass. A null exit_code means
no process exit was observed. stdout_digest and stderr_digest describe bounded
captured bytes, not an unbounded output stream. Filesystem storage and command
execution belong to the caller. Standard library only. Python 3.11+.
"""

from __future__ import annotations

import json
import re
from typing import Any

_COMMAND_FIELDS = {"argv", "cwd", "expected_exit"}
_RESULT_FIELDS = _COMMAND_FIELDS | {
    "exit_code", "timed_out", "stdout_digest", "stderr_digest",
}
_RECORD_FIELDS = {
    "schema_version", "type", "execution_id", "run_id", "request_id", "issuance_id",
    "task_revision", "candidate_tree_digest", "gate_declaration_digest", "commands", "outcome",
}
_DIGEST = re.compile(r"[0-9a-f]{64}")


class ExecutionRefused(ValueError):
    """An unreadable or invalid execution record cannot serve as proof."""

    code = "gate-execution-invalid"


def _unique_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON fields rather than choosing one interpretation."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ExecutionRefused(f"duplicate field: {key}")
        result[key] = value
    return result


def load_json(data: str | bytes) -> Any:
    """Decode strict JSON used by declarations and records; refuse unreadable data."""
    try:
        text = data.decode("utf-8") if isinstance(data, bytes) else data
        return json.loads(text, object_pairs_hook=_unique_fields)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ExecutionRefused("unreadable gate JSON") from exc


def _text(value: Any) -> bool:
    """Require nonempty text that can be passed to a process as UTF-8."""
    if not isinstance(value, str) or not value or "\0" in value:
        return False
    try:
        value.encode("utf-8")
    except UnicodeError:
        return False
    return True


def _digest(value: Any) -> bool:
    """Recognize an exact lowercase SHA-256 digest."""
    return isinstance(value, str) and _DIGEST.fullmatch(value) is not None


def validate_command(command: Any, *, observed: bool = False) -> None:
    """Validate a literal argv, confined relative cwd and optional observed result."""
    fields = _RESULT_FIELDS if observed else _COMMAND_FIELDS
    if not isinstance(command, dict) or set(command) != fields:
        raise ExecutionRefused("gate command fields differ from schema")
    argv, cwd, expected = command["argv"], command["cwd"], command["expected_exit"]
    if (
        not isinstance(argv, list) or not argv or not _text(argv[0])
        or not all(arg == "" or _text(arg) for arg in argv)
    ):
        raise ExecutionRefused("argv must be a string array with a nonempty executable")
    if not _text(cwd) or (cwd != "." and (
        "\\" in cwd or ":" in cwd or any(part in ("", ".", "..") for part in cwd.split("/"))
    )):
        raise ExecutionRefused("cwd must be . or a repository-relative directory")
    if type(expected) is not int or not 0 <= expected <= 255:
        raise ExecutionRefused("expected_exit must be an integer from 0 to 255")
    if observed and (
        (command["exit_code"] is not None and type(command["exit_code"]) is not int)
        or type(command["timed_out"]) is not bool
        or not _digest(command["stdout_digest"])
        or not _digest(command["stderr_digest"])
    ):
        raise ExecutionRefused("invalid observed command result")


def validate_execution(record: Any) -> None:
    """Refuse any record outside the closed execution schema or claiming a false pass."""
    if not isinstance(record, dict) or set(record) != _RECORD_FIELDS:
        raise ExecutionRefused("execution fields differ from schema")
    if type(record["schema_version"]) is not int or record["schema_version"] != 1:
        raise ExecutionRefused("unsupported execution schema version")
    if record["type"] != "gate-execution.v1":
        raise ExecutionRefused("unsupported execution record type")
    identities = ("execution_id", "run_id", "request_id", "issuance_id")
    if not all(_text(record[key]) for key in identities):
        raise ExecutionRefused("execution identities must be nonempty strings")
    if (
        not _digest(record["candidate_tree_digest"])
        or not _digest(record["gate_declaration_digest"])
        or (record["task_revision"] is not None and not _digest(record["task_revision"]))
    ):
        raise ExecutionRefused("execution binding digests must be SHA-256")
    commands, outcome = record["commands"], record["outcome"]
    if not isinstance(commands, list) or outcome not in ("started", "passed", "failed"):
        raise ExecutionRefused("invalid execution commands or outcome")
    for command in commands:
        validate_command(command, observed=True)
    if outcome == "started" and commands:
        raise ExecutionRefused("started execution cannot contain results")
    if outcome == "passed" and (not commands or any(
        command["timed_out"] or command["exit_code"] != command["expected_exit"]
        for command in commands
    )):
        raise ExecutionRefused("passing execution requires successful command results")


def encode_execution(record: dict[str, Any]) -> bytes:
    """Validate and encode a record as deterministic UTF-8 JSON."""
    validate_execution(record)
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")


def decode_execution(data: bytes) -> dict[str, Any]:
    """Decode and validate a stored record, failing closed on unreadable bytes."""
    record = load_json(data)
    validate_execution(record)
    return record
