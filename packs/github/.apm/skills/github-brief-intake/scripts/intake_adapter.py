#!/usr/bin/env python3
"""Fail-closed policy, argv, and normalized-envelope checks for GitHub intake."""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

PROFILE_PATH = Path(__file__).resolve().parents[1] / "references" / "intake-profile.json"
NORMALIZED_KEYS = {
    "contract_version",
    "action",
    "content",
    "source",
    "constraints",
    "proposed_authority",
}
CONTENT_KEYS = {"outcomes", "constraints", "evidence", "behaviors", "assumptions", "named_gaps"}
SENSITIVE_MARKERS = ("credential", "secret", "password", "token", "raw_payload", "instruction")
HOST_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
CONSTRAINT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
CONSTRAINT_SENSITIVE_PATTERN = re.compile(
    r"(?:^|_)(?:raw|payload|prompt|instruction|credential|credentials|secret|secrets|"
    r"password|passwords|passwd|pwd|(?:api|access|private)?_?(?:token|tokens|key|keys))"
    r"(?:_|$)"
)


class IntakePolicyError(ValueError):
    """A tracker intake boundary refused untrusted input."""


def load_profile(path: Path = PROFILE_PATH) -> dict[str, Any]:
    """Load one strict, versioned fixed-host intake profile."""
    profile = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    if not isinstance(profile, dict) or set(profile) != {"id", "version", "destination", "budget"}:
        raise IntakePolicyError("invalid intake profile")
    if not profile["id"] or not profile["version"]:
        raise IntakePolicyError("intake profile id and version are required")
    if profile["destination"].get("boundary") != "approved-gh-fixed-host":
        raise IntakePolicyError("unapproved GitHub transport boundary")
    budget = profile.get("budget")
    if (
        not isinstance(budget, dict)
        or not isinstance(budget.get("max_retries"), int)
        or budget["max_retries"] < 0
        or not isinstance(budget.get("backoff_seconds"), list)
        or len(budget["backoff_seconds"]) < budget["max_retries"]
    ):
        raise IntakePolicyError("invalid GitHub retry budget")
    return profile


def validate_configured_target(
    configured_host: str,
    repository: str,
    profile: dict[str, Any],
    *,
    payload_host: str | None = None,
) -> tuple[str, str]:
    """Accept host and repository only from trusted configuration."""
    host = configured_host.rstrip(".").lower()
    allowed = {str(value).rstrip(".").lower() for value in profile["destination"]["allowed_hosts"]}
    if not HOST_PATTERN.fullmatch(host) or host not in allowed:
        raise IntakePolicyError("configured GitHub host is not allowed")
    if payload_host is not None:
        raise IntakePolicyError("payload-derived GitHub host is forbidden")
    if not REPOSITORY_PATTERN.fullmatch(repository) or "://" in repository:
        raise IntakePolicyError("repository must be trusted owner/name configuration")
    return host, repository


def build_gh_argv(
    action: str,
    *,
    configured_host: str,
    repository: str,
    selector: str,
    profile: dict[str, Any],
    payload_host: str | None = None,
) -> list[str]:
    """Build one shell-free, read-only gh invocation from trusted configuration."""
    host, trusted_repository = validate_configured_target(
        configured_host, repository, profile, payload_host=payload_host
    )
    if not selector or "://" in selector or selector.startswith("--"):
        raise IntakePolicyError("selector cannot supply a host, URL, or option")
    if action == "milestone":
        if not selector.isdecimal():
            raise IntakePolicyError("milestone API selector must be a numeric identifier")
        return [
            "gh",
            "api",
            "--hostname",
            host,
            f"repos/{trusted_repository}/milestones/{selector}",
        ]
    if action == "issues":
        return [
            "gh",
            "issue",
            "list",
            "--hostname",
            host,
            "--repo",
            trusted_repository,
            "--milestone",
            selector,
            "--state",
            "all",
            "--limit",
            str(profile["budget"]["max_items"]),
            "--json",
            "number,title,body,labels,url,state,updatedAt",
        ]
    raise IntakePolicyError("unsupported read-only gh action")


def run_gh_read(
    action: str,
    *,
    configured_host: str,
    repository: str,
    selector: str,
    profile: dict[str, Any],
    payload_host: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> subprocess.CompletedProcess[str]:
    """Build and run one approved read without accepting a caller-supplied argv."""
    argv = build_gh_argv(
        action,
        configured_host=configured_host,
        repository=repository,
        selector=selector,
        profile=profile,
        payload_host=payload_host,
    )
    budget = profile["budget"]
    result: subprocess.CompletedProcess[str] | None = None
    last_error: subprocess.SubprocessError | None = None
    for attempt in range(budget["max_retries"] + 1):
        try:
            if runner is None:
                result = _run_gh_bounded(
                    list(argv),
                    timeout=float(budget["timeout_seconds"]),
                    max_bytes=int(budget["max_bytes"]),
                )
            else:
                result = runner(
                    list(argv),
                    check=True,
                    capture_output=True,
                    text=True,
                    shell=False,
                    timeout=budget["timeout_seconds"],
                )
            break
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            last_error = exc
            if attempt >= budget["max_retries"]:
                raise IntakePolicyError("approved gh read exhausted its retry budget") from exc
            sleeper(float(budget["backoff_seconds"][attempt]))
    if result is None:
        raise IntakePolicyError("approved gh read failed") from last_error
    if len(result.stdout.encode("utf-8")) > budget["max_bytes"]:
        raise IntakePolicyError("GitHub response exceeded the profile byte budget")
    try:
        json.loads(result.stdout, parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise IntakePolicyError("GitHub returned invalid strict JSON") from exc
    return result


def _run_gh_bounded(
    argv: list[str], *, timeout: float, max_bytes: int
) -> subprocess.CompletedProcess[str]:
    """Run approved gh argv while bounding stdout and stderr before buffering."""
    process = subprocess.Popen(  # noqa: S603 — argv is built by build_gh_argv
        list(argv),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )
    assert process.stdout is not None and process.stderr is not None
    captures: dict[str, tuple[bytes, bool]] = {}

    def stop_process() -> None:
        with contextlib.suppress(OSError):
            process.kill()

    def capture(name: str, pipe: Any) -> None:
        captures[name] = _read_bounded_pipe(pipe, max_bytes, stop_process)

    threads = [
        threading.Thread(target=capture, args=("stdout", process.stdout), daemon=True),
        threading.Thread(target=capture, args=("stderr", process.stderr), daemon=True),
    ]
    for thread in threads:
        thread.start()
    try:
        returncode = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        stop_process()
        process.wait()
        raise
    finally:
        for thread in threads:
            thread.join()

    stdout, stdout_exceeded = captures["stdout"]
    stderr, stderr_exceeded = captures["stderr"]
    if stdout_exceeded or stderr_exceeded:
        raise IntakePolicyError("GitHub response exceeded the profile byte budget")
    try:
        stdout_text = stdout.decode("utf-8")
        stderr_text = stderr.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IntakePolicyError("GitHub returned malformed UTF-8") from exc
    result = subprocess.CompletedProcess(argv, returncode, stdout_text, stderr_text)
    if returncode != 0:
        raise subprocess.CalledProcessError(
            returncode, argv, output=stdout_text, stderr=stderr_text
        )
    return result


def _read_bounded_pipe(
    pipe: Any, max_bytes: int, on_exceeded: Callable[[], Any]
) -> tuple[bytes, bool]:
    """Read at most max_bytes plus one detection byte from one process pipe."""
    content = bytearray()
    while True:
        chunk = pipe.read(min(65536, max_bytes - len(content) + 1))
        if not chunk:
            return bytes(content), False
        remaining = max_bytes - len(content)
        if len(chunk) > remaining:
            content.extend(chunk[:remaining])
            on_exceeded()
            return bytes(content), True
        content.extend(chunk)


def normalize_record(record: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Minimize and validate an adapter-produced normalized intake envelope."""
    if not isinstance(record, dict) or set(record) != NORMALIZED_KEYS:
        raise IntakePolicyError("normalized intake has missing or unknown fields")
    if record.get("contract_version") != "normalized-intake.v1":
        raise IntakePolicyError("unsupported normalized intake contract")
    if record.get("action") not in {"start", "remember"}:
        raise IntakePolicyError("unsupported normalized intake action")
    if record.get("proposed_authority") not in {"repo-origin", "tracker-origin"}:
        raise IntakePolicyError("invalid proposed authority")
    content = record.get("content")
    source = record.get("source")
    if not isinstance(content, dict) or set(content) != CONTENT_KEYS:
        raise IntakePolicyError("normalized content has missing or unknown fields")
    for values in content.values():
        if (
            not isinstance(values, list)
            or len(values) > 50
            or any(
                not isinstance(value, str) or not value or len(value) > 2000
                for value in values
            )
        ):
            raise IntakePolicyError("normalized content violates the shared schema")
    if not isinstance(source, dict) or not all(
        source.get(name) for name in ("locator", "revision", "object_type")
    ):
        raise IntakePolicyError("trusted locator, revision, and object type are required")
    if not all(isinstance(source[name], str) for name in ("locator", "revision", "object_type")):
        raise IntakePolicyError("normalized source fields must be strings")
    expected_profile = {"id": profile["id"], "version": profile["version"]}
    if source.get("tracker_profile") != expected_profile:
        raise IntakePolicyError("tracker profile does not match the selected version")
    if set(source) != {"mode", "locator", "revision", "tracker_profile", "object_type"}:
        raise IntakePolicyError("normalized source has missing or unknown fields")
    if source.get("mode") not in {"repo-origin", "tracker-origin"}:
        raise IntakePolicyError("invalid source mode")
    if (
        len(source["locator"]) > 1000
        or any(char in source["locator"] for char in "@?#")
        or len(source["revision"]) > 200
        or len(source["object_type"]) > 120
    ):
        raise IntakePolicyError("normalized source violates the shared schema")
    _validate_constraints(record.get("constraints"))
    _reject_sensitive_keys(record)
    serialized = json.dumps(record, ensure_ascii=False, allow_nan=False)
    return json.loads(serialized)


def _validate_constraints(value: Any) -> None:
    if not isinstance(value, dict) or len(value) > 40:
        raise IntakePolicyError("constraints violate the shared schema")
    for name, item in value.items():
        if not CONSTRAINT_NAME_PATTERN.fullmatch(str(name)) or CONSTRAINT_SENSITIVE_PATTERN.search(
            str(name)
        ):
            raise IntakePolicyError("constraint name violates the shared schema")
        items = item if isinstance(item, list) else [item]
        if len(items) > 20:
            raise IntakePolicyError("constraint array violates the shared schema")
        for scalar in items:
            if isinstance(scalar, (dict, list)) or (
                isinstance(scalar, str) and len(scalar) > 1000
            ) or (
                isinstance(scalar, float) and not math.isfinite(scalar)
            ):
                raise IntakePolicyError("constraint value violates the shared schema")
            if scalar is not None and not isinstance(scalar, (str, int, float, bool)):
                raise IntakePolicyError("constraint value violates the shared schema")


def emit_and_handoff(
    *,
    content: dict[str, Any],
    requested_locator: str,
    acquired: dict[str, Any],
    constraints: dict[str, Any],
    profile: dict[str, Any],
    invoke_work_intake: Callable[[dict[str, Any]], Any],
) -> Any:
    """Build from trusted acquisition metadata and invoke the shared intake seam."""
    _assert_grounded(acquired, content, constraints)
    source = trusted_source(acquired, profile)
    if requested_locator != source["locator"]:
        raise IntakePolicyError("acquired source does not match the requested object")
    record = {
        "contract_version": "normalized-intake.v1",
        "action": "start",
        "content": content,
        "source": source,
        "constraints": constraints,
        "proposed_authority": "tracker-origin",
    }
    return invoke_work_intake(normalize_record(record, profile))


def _assert_grounded(
    acquired: dict[str, Any], content: dict[str, Any], constraints: dict[str, Any]
) -> None:
    """Require every interpreted value to be evidenced by the raw response."""
    raw_strings: list[str] = []
    raw_scalars: set[str | int | float | bool | None] = set()

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
        elif isinstance(value, str):
            raw_strings.append(value)
            raw_scalars.add(value)
        elif value is None or isinstance(value, (int, float, bool)):
            raw_scalars.add(value)

    collect(acquired)
    for values in content.values():
        if not isinstance(values, list) or any(
            not isinstance(item, str)
            or not any(item in source_text for source_text in raw_strings)
            for item in values
        ):
            raise IntakePolicyError("normalized content is not grounded in acquisition data")
    for value in constraints.values():
        values = value if isinstance(value, list) else [value]
        if any(
            item not in raw_scalars
            and not (
                isinstance(item, str)
                and any(item in source_text for source_text in raw_strings)
            )
            for item in values
        ):
            raise IntakePolicyError("normalized constraints are not grounded in acquisition data")


def trusted_source(acquired: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Derive provenance only from the trusted GitHub response envelope."""
    number = acquired.get("number")
    object_type = acquired.get("type")
    revision = acquired.get("updatedAt")
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise IntakePolicyError("trusted GitHub response lacks a stable number")
    if object_type == "Issue":
        kind = "items"
    elif object_type == "Milestone" and acquired.get("selectionKind") in {
        "container", "collection"
    }:
        kind = "containers" if acquired["selectionKind"] == "container" else "collections"
    else:
        raise IntakePolicyError("trusted GitHub response lacks a supported object type")
    if not isinstance(revision, str) or not revision:
        raise IntakePolicyError("trusted GitHub response lacks a revision")
    return {
        "mode": "tracker-origin",
        "locator": f"gh://{kind}/{number}",
        "revision": revision,
        "tracker_profile": {"id": profile["id"], "version": profile["version"]},
        "object_type": object_type,
    }


def budget_result(
    *, pages: int, items: int, response_bytes: int, profile: dict[str, Any]
) -> dict[str, Any]:
    """Return a deterministic complete or explicitly incomplete budget result."""
    budget = profile["budget"]
    exceeded = any((
        pages > budget["max_pages"],
        items > budget["max_items"],
        response_bytes > budget["max_bytes"],
    ))
    return {
        "complete": not exceeded,
        "result": "complete" if not exceeded else budget["exhaustion"],
    }


def _reject_sensitive_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(marker in normalized for marker in SENSITIVE_MARKERS):
                raise IntakePolicyError("sensitive or instruction-shaped field refused")
            _reject_sensitive_keys(child)
    elif isinstance(value, list):
        for child in value:
            _reject_sensitive_keys(child)


def _reject_constant(value: str) -> None:
    raise IntakePolicyError(f"non-standard JSON constant: {value}")


def main(argv: list[str] | None = None) -> int:
    """Expose deterministic validation and argv construction without credentials."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    command = subparsers.add_parser("build-argv")
    command.add_argument("action", choices=("milestone", "issues"))
    command.add_argument("host")
    command.add_argument("repository")
    command.add_argument("selector")
    record = subparsers.add_parser("validate-record")
    record.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        profile = load_profile()
        if args.command == "build-argv":
            built = build_gh_argv(
                args.action,
                configured_host=args.host,
                repository=args.repository,
                selector=args.selector,
                profile=profile,
            )
            print(json.dumps(built, ensure_ascii=False, allow_nan=False))
            return 0
        candidate = json.loads(
            args.path.read_text(encoding="utf-8"), parse_constant=_reject_constant
        )
        normalized = normalize_record(candidate, profile)
        print(json.dumps(normalized, ensure_ascii=False, allow_nan=False))
        return 0
    except (IntakePolicyError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"error: intake policy refused input ({type(exc).__name__})\n")


if __name__ == "__main__":
    raise SystemExit(main())
