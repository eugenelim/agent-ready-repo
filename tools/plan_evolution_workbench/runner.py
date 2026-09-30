#!/usr/bin/env python3
"""Fail-closed dry-run workbench for the plan-evolution pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import signal
import socket
import stat
import subprocess
import sys
import tarfile
import threading
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_ROOT = REPO_ROOT / "docs" / "product" / "research" / "plan-evolution-experiments"
AGENTBUNDLE = REPO_ROOT / "packages" / "agentbundle"
if str(AGENTBUNDLE) not in sys.path:
    sys.path.insert(0, str(AGENTBUNDLE))

from agentbundle.catalogue_tooling.file_safety import (  # noqa: E402
    UnsafeContentError,
    read_confined_regular_file,
    validate_confined_directory,
)

MAX_JSON_BYTES = 1_000_000
MAX_PROGRESS_BYTES = 4_000_000
MAX_PROGRESS_LINE_BYTES = 64_000
MAX_CODEX_CAPTURE_BYTES = 2_000_000
MAX_CODEX_EVENTS = 5_000
MAX_JSON_DEPTH = 24
MAX_ARRAY_ITEMS = 1_000
MAX_STRING_BYTES = 20_000
ORACLE_TIMEOUT_SECONDS = 120
CALIBRATION_TIMEOUT_SECONDS = 180
CODEX_CLI_VERSION = "0.157.0"
LEGAL_CODEX_FLAGS = {
    "codex",
    "exec",
    "--config",
    "--disable",
    "--model",
    "--sandbox",
    "workspace-write",
    "--cd",
    "--add-dir",
    "--ephemeral",
    "--ignore-user-config",
    "--ignore-rules",
    "--json",
    "--strict-config",
}
FORBIDDEN_CODEX_FLAGS = {"--dangerously-bypass-approvals-and-sandbox", "--approve-for-me"}
NETWORK_WORDS = ("http://", "https://", "dns:", "webhook", "curl ", "wget ")
HYPOTHESES = tuple(f"H{i}" for i in range(1, 14))
CORE_DIRECT_HYPOTHESES = ("H1", "H2", "H3", "H4", "H5", "H8", "H10", "H12", "H13")
REVIEW_HYPOTHESES = ("H6", "H7", "H9")
COMMIT_HEX = frozenset("0123456789abcdef")
CALIBRATION_ROLES = (
    ("calibration-planner-standard", "planner_or_probe", "standard"),
    ("calibration-builder-standard", "builder", "standard"),
    ("calibration-reviewer-standard", "reviewer", "standard"),
    ("calibration-adjudicator-standard", "adjudicator", "standard"),
    ("calibration-planner-frontier", "planner_or_probe", "frontier"),
    ("calibration-builder-frontier", "builder", "frontier"),
    ("calibration-reviewer-frontier", "reviewer", "frontier"),
    ("calibration-adjudicator-frontier", "adjudicator", "frontier"),
)
DISABLED_CODEX_FEATURES = (
    "apps",
    "auth_elicitation",
    "guardian_approval",
    "image_generation",
    "multi_agent",
    "network_proxy",
    "plugins",
    "remote_plugin",
    "skill_mcp_dependency_install",
    "skill_search",
    "system_proxy_fallback",
    "tool_call_mcp_elicitation",
    "tool_suggest",
)
MODEL_BY_CLASS = {"standard": "gpt-5.6-luna", "frontier": "gpt-5.6-sol"}
SYNTHETIC_ENV_CANARIES = {
    "PLAN_EVOLUTION_SYNTHETIC_SECRET": "synthetic-secret-deny",
    "PLAN_EVOLUTION_CONTROLLER_ONLY": "synthetic-controller-deny",
}
SYNTHETIC_ROOT_NAMES = (
    "baseline",
    "candidate",
    "controller",
    "credential",
    "hidden_oracle",
    "output",
    "prompt",
    "reference",
    "sibling",
)


class WorkbenchError(ValueError):
    """Base class for terminal workbench input refusals."""


class SchemaError(WorkbenchError):
    """A structured input failed its strict schema."""


class InvocationLimitError(WorkbenchError):
    """A requested invocation is outside the released study interval."""


class SandboxPolicyError(WorkbenchError):
    """A worker command or policy would widen the sandbox."""


class SourcePolicyError(WorkbenchError):
    """A source URL request would perform or imply HTTP-like behavior."""


@dataclass(frozen=True)
class CodexProcessResult:
    """Captured Codex calibration process result."""

    returncode: int | str
    stdout: bytes
    stderr: bytes
    duration_seconds: float
    timed_out: bool
    capture_exceeded: bool = False


@dataclass(frozen=True)
class GitResult:
    """Captured argv-form Git result."""

    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def _reject_duplicate_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
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


def parse_json_bytes(raw: bytes, *, max_bytes: int = MAX_JSON_BYTES) -> Any:
    """Parse strict bounded JSON bytes for every structured input surface."""
    if len(raw) > max_bytes:
        raise SchemaError("JSON byte limit exceeded")
    try:
        data = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_object_pairs,
            parse_constant=_reject_constant,
        )
    except UnicodeDecodeError as exc:
        raise SchemaError("JSON must be UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise SchemaError(f"malformed JSON: {exc.msg}") from exc
    _check_bounds(data)
    return data


def load_json(path: Path, *, max_bytes: int = MAX_JSON_BYTES) -> Any:
    """Read strict JSON, rejecting duplicate keys and non-finite numbers."""
    target = path if path.is_absolute() else REPO_ROOT / path
    raw = read_confined_regular_file(REPO_ROOT, target, max_bytes=max_bytes)
    return parse_json_bytes(raw, max_bytes=max_bytes)


def load_disposable_json(root: Path, path: Path, *, max_bytes: int = MAX_JSON_BYTES) -> Any:
    """Read strict JSON from a disposable run root without following final links."""
    confined = confine_disposable_path(root, path)
    raw = safe_read_bytes(confined, max_bytes=max_bytes)
    return parse_json_bytes(raw, max_bytes=max_bytes)


def load_design(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise SchemaError("design root must be an object")
    return data


def _check_bounds(value: Any, *, depth: int = 0) -> None:
    if depth > MAX_JSON_DEPTH:
        raise SchemaError("JSON nesting limit exceeded")
    if isinstance(value, dict):
        if len(value) > MAX_ARRAY_ITEMS:
            raise SchemaError("object field limit exceeded")
        for key, child in value.items():
            if not isinstance(key, str):
                raise SchemaError("object keys must be strings")
            if len(key.encode("utf-8")) > MAX_STRING_BYTES:
                raise SchemaError("object key is too large")
            _check_bounds(child, depth=depth + 1)
        return
    if isinstance(value, list):
        if len(value) > MAX_ARRAY_ITEMS:
            raise SchemaError("array item limit exceeded")
        for child in value:
            _check_bounds(child, depth=depth + 1)
        return
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_STRING_BYTES:
            raise SchemaError("string limit exceeded")
        return
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SchemaError("non-finite JSON number")
        return
    raise SchemaError("unsupported JSON value")


def _expect_keys(mapping: dict[str, Any], keys: set[str], label: str) -> None:
    actual = set(mapping)
    if actual != keys:
        missing = sorted(keys - actual)
        extra = sorted(actual - keys)
        raise SchemaError(f"{label} fields mismatch: missing={missing} extra={extra}")


def _expect_positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SchemaError(f"{label} must be a positive integer")
    return value


def _expect_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise SchemaError(f"{label} must be a non-empty string")
    return value


def validate_design(design: dict[str, Any]) -> dict[str, Any]:
    """Validate the frozen design surfaces owned by T1."""
    _expect_keys(
        design,
        {
            "schema_version",
            "codex_cli_version",
            "hypotheses",
            "allocations",
            "study_ceiling",
            "fixed_releases",
            "reserve_release",
            "tasks",
            "models",
            "role_limits",
            "source_url_inventory",
            "dry_run_policy",
            "prompt_templates",
            "scoring_rules",
            "seeds",
        },
        "design",
    )
    if design["schema_version"] != 1:
        raise SchemaError("unsupported design schema")
    if design["codex_cli_version"] != CODEX_CLI_VERSION:
        raise SchemaError("unexpected Codex CLI contract slice")

    hypotheses = _validate_hypotheses(design["hypotheses"])
    allocations = _validate_allocations(design["allocations"])
    ceiling = _expect_positive_int(design["study_ceiling"], "study_ceiling")
    if ceiling != sum(allocations.values()):
        raise SchemaError("study ceiling must equal allocation total")
    fixed_releases = _validate_fixed_releases(design["fixed_releases"])
    reserve = _validate_reserve(design["reserve_release"])
    if reserve["study_end"] != ceiling:
        raise SchemaError("reserve release must end at the study ceiling")
    if reserve["study_start"] != fixed_releases[-1]["study_end"] + 1:
        raise SchemaError("reserve release must follow fixed releases")
    if fixed_releases[-1]["study_end"] >= ceiling:
        raise SchemaError("fixed releases leave no adaptive reserve")
    _validate_tasks(design["tasks"])
    _validate_policy(design["dry_run_policy"])
    _validate_sources(design["source_url_inventory"])
    _validate_models(design["models"])
    _validate_role_limits(design["role_limits"])
    _validate_simple_string_map(design["prompt_templates"], "prompt_templates")
    _validate_simple_string_map(design["scoring_rules"], "scoring_rules")
    _validate_seeds(design["seeds"])
    return {
        "hypotheses": hypotheses,
        "allocations": allocations,
        "study_ceiling": ceiling,
        "fixed_releases": fixed_releases,
        "reserve_release": reserve,
    }


def _validate_hypotheses(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) != 13:
        raise SchemaError("design must declare 13 hypotheses")
    labels: list[str] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise SchemaError("hypothesis must be an object")
        _expect_keys(
            item,
            {"id", "comparison", "primary_measure", "evidence_class", "verdict_rule"},
            "hypothesis",
        )
        expected = f"H{index}"
        if item["id"] != expected:
            raise SchemaError("hypotheses must be H1 through H13 in order")
        for key in ("comparison", "primary_measure", "evidence_class", "verdict_rule"):
            _expect_text(item[key], key)
        labels.append(item["id"])
    return tuple(labels)


def _validate_allocations(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        raise SchemaError("allocations must be an object")
    expected = {
        "instrument_calibration": 8,
        "core_experiment": 160,
        "independent_review": 36,
        "blind_adjudication": 12,
        "adaptive_reserve": 24,
    }
    if value != expected:
        raise SchemaError("allocations must match the frozen study table")
    return dict(value)


def _validate_fixed_releases(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != 3:
        raise SchemaError("fixed releases must contain W1, W2, and W3 fixed")
    expected = [("W1", 1, 80), ("W2", 81, 160), ("W3", 161, 216)]
    releases: list[dict[str, Any]] = []
    previous_end = 0
    for item, (wave, start, end) in zip(value, expected, strict=True):
        if not isinstance(item, dict):
            raise SchemaError("release must be an object")
        _expect_keys(item, {"wave", "study_start", "study_end", "prerequisite"}, "release")
        if item["wave"] != wave:
            raise SchemaError("release waves must be W1, W2, W3")
        if item["study_start"] != start or item["study_end"] != end:
            raise SchemaError("fixed release boundary changed")
        if item["study_start"] != previous_end + 1:
            raise SchemaError("fixed releases must be contiguous")
        _expect_text(item["prerequisite"], "prerequisite")
        previous_end = item["study_end"]
        releases.append(dict(item))
    return releases


def _validate_reserve(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SchemaError("reserve release must be an object")
    _expect_keys(value, {"wave", "study_start", "study_end", "prerequisite"}, "reserve")
    if value["wave"] != "W3":
        raise SchemaError("reserve release belongs to W3")
    if value["study_start"] != 217 or value["study_end"] != 240:
        raise SchemaError("reserve release boundary changed")
    _expect_text(value["prerequisite"], "reserve prerequisite")
    return dict(value)


def _validate_tasks(value: Any) -> None:
    if not isinstance(value, list) or len(value) != 12:
        raise SchemaError("design must freeze exactly 12 task blocks")
    seen: set[str] = set()
    strata: dict[str, int] = {}
    for item in value:
        if not isinstance(item, dict):
            raise SchemaError("task must be an object")
        _expect_keys(
            item,
            {
                "id",
                "name",
                "stratum",
                "provenance",
                "baseline",
                "reference",
                "primary_oracle",
                "oracle_argv",
                "complexity",
                "uncertainty",
            },
            "task",
        )
        task_id = _expect_text(item["id"], "task id")
        if task_id in seen:
            raise SchemaError("duplicate task id")
        seen.add(task_id)
        for key in ("name", "stratum", "provenance", "baseline", "reference", "primary_oracle"):
            _expect_text(item[key], key)
        _validate_oracle_argv(item["oracle_argv"])
        _expect_commit_id(item["baseline"], "baseline")
        _expect_commit_id(item["reference"], "reference")
        if item["provenance"] not in {"pre-build", "reconstructed"}:
            raise SchemaError("unknown task provenance")
        if item["complexity"] not in {"medium", "complex"}:
            raise SchemaError("unknown task complexity")
        if item["uncertainty"] not in {"low", "medium", "high"}:
            raise SchemaError("unknown task uncertainty")
        strata[item["stratum"]] = strata.get(item["stratum"], 0) + 1
    if set(strata.values()) != {3} or len(strata) != 4:
        raise SchemaError("task blocks must have four strata with three tasks each")


def _validate_oracle_argv(value: Any) -> None:
    if not isinstance(value, list) or not value:
        raise SchemaError("oracle_argv must be a non-empty argv array")
    if any(not isinstance(item, str) or not item for item in value):
        raise SchemaError("oracle_argv items must be non-empty strings")
    if value == ["manual", "historical-oracle-required"]:
        raise SchemaError("oracle_argv must name a task-specific rule")
    joined = " ".join(value).lower()
    if any(word.strip() in joined for word in NETWORK_WORDS):
        raise SourcePolicyError("oracle argv must not request network behavior")


def _expect_commit_id(value: Any, label: str) -> str:
    text = _expect_text(value, label)
    if len(text) != 40 or any(char not in COMMIT_HEX for char in text):
        raise SchemaError(f"{label} must be a full lowercase 40-character commit")
    return text


def _validate_policy(value: Any) -> None:
    if not isinstance(value, dict):
        raise SchemaError("dry_run_policy must be an object")
    _expect_keys(
        value,
        {
            "sandbox_mode",
            "allowed_tools",
            "allow_network",
            "allow_web",
            "allow_mcp",
            "allow_delegation",
            "allow_approval_escalation",
            "allow_apps",
            "allow_plugins",
            "allow_multi_agent",
            "environment_allowlist",
        },
        "dry_run_policy",
    )
    if value["sandbox_mode"] != "workspace-write":
        raise SandboxPolicyError("sandbox must be workspace-write")
    for key in (
        "allow_network",
        "allow_web",
        "allow_mcp",
        "allow_delegation",
        "allow_approval_escalation",
        "allow_apps",
        "allow_plugins",
        "allow_multi_agent",
    ):
        if value[key] is not False:
            raise SandboxPolicyError(f"{key} must be false")
    if not isinstance(value["allowed_tools"], list) or value["allowed_tools"] != ["shell"]:
        raise SandboxPolicyError("allowed tools must be restricted to shell")
    env = value["environment_allowlist"]
    if not isinstance(env, list) or any(not isinstance(item, str) for item in env):
        raise SandboxPolicyError("environment allowlist must be strings")
    forbidden = {"HOME", "AWS_ACCESS_KEY_ID", "GITHUB_TOKEN", "OPENAI_API_KEY", "PATH"}
    if forbidden.intersection(env):
        raise SandboxPolicyError("environment allowlist exposes controller values")


def _validate_sources(value: Any) -> None:
    if not isinstance(value, list) or not value:
        raise SourcePolicyError("source inventory must be a non-empty list")
    source_ids: set[str] = set()
    origins: set[str] = set()
    for source in value:
        if not isinstance(source, dict):
            raise SourcePolicyError("source record must be an object")
        _expect_keys(source, {"id", "url", "pure_md_recovery", "retrieval_status"}, "source")
        source_id = _expect_text(source["id"], "source id")
        if source_id in source_ids:
            raise SourcePolicyError("duplicate source id")
        source_ids.add(source_id)
        url = _expect_text(source["url"], "source url")
        if url in origins:
            raise SourcePolicyError("duplicate source URL")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise SourcePolicyError("source inventory accepts HTTPS URLs only")
        origins.add(url)
        recovery = _expect_text(source["pure_md_recovery"], "pure.md recovery")
        if not recovery.startswith("https://pure.md/"):
            raise SourcePolicyError("recovery URL must use pure.md")
        embedded = recovery.removeprefix("https://pure.md/")
        if embedded != url:
            raise SourcePolicyError("pure.md URL must embed the exact inventoried origin")
        _expect_text(source["retrieval_status"], "retrieval status")


def _validate_models(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != {"standard", "frontier"}:
        raise SchemaError("models must declare standard and frontier")
    if value["standard"] != "gpt-5.6-luna" or value["frontier"] != "gpt-5.6-sol":
        raise SchemaError("provisional model ids changed")


def _validate_role_limits(value: Any) -> None:
    if not isinstance(value, dict):
        raise SchemaError("role_limits must be an object")
    expected = {
        "planner_or_probe": (100000, 8000, 15),
        "builder": (400000, 24000, 45),
        "reviewer": (150000, 12000, 20),
        "repair_or_escalation": (250000, 16000, 30),
        "adjudicator": (120000, 8000, 15),
    }
    if set(value) != set(expected):
        raise SchemaError("role limit set changed")
    for role, limits in value.items():
        if not isinstance(limits, dict):
            raise SchemaError("role limit must be an object")
        _expect_keys(limits, {"input_tokens", "output_tokens", "wall_clock_minutes"}, role)
        if (
            limits["input_tokens"],
            limits["output_tokens"],
            limits["wall_clock_minutes"],
        ) != expected[role]:
            raise SchemaError("role limit values changed")


def _validate_simple_string_map(value: Any, label: str) -> None:
    if not isinstance(value, dict) or not value:
        raise SchemaError(f"{label} must be a non-empty object")
    for key, child in value.items():
        _expect_text(key, label)
        _expect_text(child, label)


def _validate_seeds(value: Any) -> None:
    if not isinstance(value, list) or len(value) < 12:
        raise SchemaError("seeds must cover the task frame")
    seen: set[int] = set()
    for seed in value:
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise SchemaError("seeds must be integers")
        if seed in seen:
            raise SchemaError("duplicate seed")
        seen.add(seed)


class InvocationLedger:
    """Append-only study ledger with fixed-wave and reserve releases."""

    def __init__(
        self,
        path: Path,
        *,
        study_ceiling: int,
        fixed_releases: list[dict[str, Any]],
        reserve_release: dict[str, Any],
    ) -> None:
        self.path = path
        self.study_ceiling = study_ceiling
        self.fixed_releases = fixed_releases
        self.reserve_release = reserve_release
        self._truncate_at: int | None = None
        self._records = self._load_records()

    def _load_records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        raw = safe_read_bytes(self.path, max_bytes=MAX_PROGRESS_BYTES)
        trailing_newline = raw.endswith(b"\n")
        records: list[dict[str, Any]] = []
        line_start = 0
        lines = raw.splitlines(keepends=True)
        for index, raw_line in enumerate(lines):
            line = raw_line.rstrip(b"\r\n")
            if not line.strip():
                line_start += len(raw_line)
                continue
            try:
                record = parse_json_bytes(
                    line,
                    max_bytes=MAX_PROGRESS_LINE_BYTES,
                )
            except SchemaError as exc:
                if index == len(lines) - 1 and not trailing_newline:
                    records.append({"event": "torn-final-line", "note": "ignored"})
                    self._truncate_at = line_start
                    continue
                raise SchemaError("malformed progress record before final line") from exc
            if not isinstance(record, dict):
                raise SchemaError("progress record must be an object")
            records.append(record)
            line_start += len(raw_line)
        self._validate_progress(records)
        return records

    def _validate_progress(self, records: list[dict[str, Any]]) -> None:
        ordinals: set[int] = set()
        started: set[str] = set()
        terminal: set[str] = set()
        fixed_releases_seen: set[str] = set()
        reserve_release_seen = False
        wave_ordinals: dict[str, int] = {}
        releases_by_wave = {
            release["wave"]: release for release in self.fixed_releases
        }
        for record in records:
            if record.get("event") == "torn-final-line":
                continue
            event = record.get("event")
            item = record.get("item")
            if not isinstance(event, str) or not isinstance(item, str):
                raise SchemaError("progress record requires event and item")
            if event == "reserve":
                reserve_keys = {
                    "event",
                    "item",
                    "wave",
                    "study_ordinal",
                    "wave_ordinal",
                    "timestamp",
                }
                if "replacement_of" in record:
                    reserve_keys.add("replacement_of")
                _expect_keys(record, reserve_keys, "reserve record")
                if item in started:
                    raise SchemaError("item cannot be reserved twice")
                wave = _expect_text(record["wave"], "reserve wave")
                release = releases_by_wave.get(wave)
                if release is None:
                    raise SchemaError("reserve wave is not declared")
                ordinal = _expect_positive_int(record.get("study_ordinal"), "study_ordinal")
                if ordinal in ordinals:
                    raise SchemaError("duplicate study ordinal")
                if ordinal != len(ordinals) + 1:
                    raise SchemaError("study ordinals must be contiguous")
                in_fixed_release = (
                    release["study_start"] <= ordinal <= release["study_end"]
                )
                in_adaptive_release = (
                    wave == self.reserve_release["wave"]
                    and self.reserve_release["study_start"]
                    <= ordinal
                    <= self.reserve_release["study_end"]
                )
                if not (in_fixed_release or in_adaptive_release):
                    raise SchemaError("reserve ordinal is outside its declared wave")
                wave_ordinal = _expect_positive_int(
                    record.get("wave_ordinal"), "wave_ordinal"
                )
                expected_wave_ordinal = wave_ordinals.get(wave, 0) + 1
                if wave_ordinal != expected_wave_ordinal:
                    raise SchemaError("wave ordinals must be contiguous")
                _expect_timestamp(record.get("timestamp"))
                if "replacement_of" in record:
                    replacement = _expect_positive_int(
                        record["replacement_of"],
                        "replacement_of",
                    )
                    if replacement >= ordinal:
                        raise SchemaError("replacement must point to an earlier ordinal")
                ordinals.add(ordinal)
                started.add(item)
                wave_ordinals[wave] = wave_ordinal
            elif event == "terminal":
                _expect_keys(
                    record,
                    {"event", "item", "status", "note", "timestamp"},
                    "terminal record",
                )
                if record.get("status") not in {"done", "failed"}:
                    raise SchemaError("terminal status must be done or failed")
                if item not in started:
                    raise SchemaError("terminal item was never reserved")
                if item in terminal:
                    raise SchemaError("item cannot terminate twice")
                _expect_text(record.get("note"), "terminal note")
                _expect_timestamp(record.get("timestamp"))
                terminal.add(item)
            elif event == "release-fixed":
                _expect_keys(
                    record,
                    {"event", "item", "wave", "gate_memo_digest", "timestamp"},
                    "fixed release record",
                )
                wave = _expect_text(record["wave"], "fixed release wave")
                legal_fixed_waves = [
                    release["wave"] for release in self.fixed_releases[1:]
                ]
                if wave not in legal_fixed_waves:
                    raise SchemaError("fixed release wave is not declared")
                if record["item"] != f"release-{wave}":
                    raise SchemaError("fixed release item does not match its wave")
                if wave in fixed_releases_seen:
                    raise SchemaError("fixed interval cannot be released twice")
                expected_wave = legal_fixed_waves[len(fixed_releases_seen)]
                if wave != expected_wave:
                    raise SchemaError("fixed intervals must be released in order")
                _expect_digest(record["gate_memo_digest"])
                _expect_timestamp(record["timestamp"])
                fixed_releases_seen.add(wave)
            elif event == "release-reserve":
                _expect_keys(
                    record,
                    {
                        "event",
                        "item",
                        "wave",
                        "items",
                        "gate_memo_digest",
                        "timestamp",
                    },
                    "reserve release record",
                )
                wave = _expect_text(record["wave"], "reserve release wave")
                if wave != self.reserve_release["wave"]:
                    raise SchemaError("reserve release wave is not declared")
                if record["item"] != "release-reserve":
                    raise SchemaError("reserve release item is invalid")
                if reserve_release_seen:
                    raise SchemaError("adaptive reserve cannot be released twice")
                items = record["items"]
                if not isinstance(items, list) or not items:
                    raise SchemaError("reserve release items must be a non-empty list")
                if any(not isinstance(child, str) or not child for child in items):
                    raise SchemaError("reserve release items must be non-empty strings")
                if len(items) != len(set(items)):
                    raise SchemaError("reserve release items must be unique")
                _expect_digest(record["gate_memo_digest"])
                _expect_timestamp(record["timestamp"])
                reserve_release_seen = True
            else:
                raise SchemaError(f"unknown progress event: {event}")

    def _released_fixed_end(self) -> int:
        released = self.fixed_releases[0]["study_end"]
        released_waves = {
            record["wave"]
            for record in self._records
            if record.get("event") == "release-fixed"
        }
        for release in self.fixed_releases[1:]:
            if release["wave"] in released_waves:
                released = release["study_end"]
        return released

    def _reserve_items(self) -> tuple[str, ...]:
        for record in reversed(self._records):
            if record.get("event") == "release-reserve":
                items = record.get("items")
                if not isinstance(items, list) or any(not isinstance(item, str) for item in items):
                    raise SchemaError("reserve release items must be strings")
                return tuple(items)
        return ()

    def _reserved_records(self) -> list[dict[str, Any]]:
        return [record for record in self._records if record.get("event") == "reserve"]

    def reservation_for_item(self, item: str) -> dict[str, Any] | None:
        for record in self._records:
            if record.get("event") == "reserve" and record.get("item") == item:
                return dict(record)
        return None

    def is_terminal(self, item: str) -> bool:
        return any(
            record.get("event") == "terminal" and record.get("item") == item
            for record in self._records
        )

    def _append(self, record: dict[str, Any]) -> None:
        self._validate_progress([*self._records, record])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self._truncate_at is not None:
            safe_truncate_file(self.path, self._truncate_at)
            self._records = [
                existing
                for existing in self._records
                if existing.get("event") != "torn-final-line"
            ]
            self._truncate_at = None
        safe_append_text(
            self.path,
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n",
        )
        self._records.append(record)

    def reserve(
        self,
        item: str,
        *,
        wave: str,
        replacement_of: int | None = None,
    ) -> tuple[int, int]:
        if self.was_started(item):
            raise InvocationLimitError("item already started")
        next_ordinal = len(self._reserved_records()) + 1
        if next_ordinal > self.study_ceiling:
            raise InvocationLimitError("study ceiling exceeded")
        fixed_end = self._released_fixed_end()
        if next_ordinal > fixed_end:
            reserve_items = self._reserve_items()
            if not reserve_items:
                raise InvocationLimitError("next ordinal is not released")
            reserve_index = next_ordinal - self.reserve_release["study_start"]
            if reserve_index < 0 or reserve_index >= len(reserve_items):
                raise InvocationLimitError("reserve item is not released")
            if item != reserve_items[reserve_index]:
                raise InvocationLimitError("reserve items must use the admitted prefix")
        release = self._release_for_ordinal(next_ordinal)
        if wave != release["wave"]:
            raise InvocationLimitError("wave does not match next released ordinal")
        wave_ordinal = self._wave_ordinal(wave) + 1
        record: dict[str, Any] = {
            "event": "reserve",
            "item": item,
            "wave": wave,
            "study_ordinal": next_ordinal,
            "wave_ordinal": wave_ordinal,
            "timestamp": time.time(),
        }
        if replacement_of is not None:
            record["replacement_of"] = replacement_of
        self._append(record)
        return next_ordinal, wave_ordinal

    def _release_for_ordinal(self, ordinal: int) -> dict[str, Any]:
        for release in self.fixed_releases:
            if release["study_start"] <= ordinal <= release["study_end"]:
                return release
        if self.reserve_release["study_start"] <= ordinal <= self.reserve_release["study_end"]:
            return self.reserve_release
        raise InvocationLimitError("ordinal is outside study bounds")

    def _wave_ordinal(self, wave: str) -> int:
        return sum(
            1
            for record in self._reserved_records()
            if record.get("wave") == wave
        )

    def was_started(self, item: str) -> bool:
        return any(
            record.get("event") == "reserve" and record.get("item") == item
            for record in self._records
        )

    def release_next(self, wave: str, *, gate_memo_digest: str) -> None:
        target = next(
            (release for release in self.fixed_releases if release["wave"] == wave),
            None,
        )
        if target is None or wave == self.fixed_releases[0]["wave"]:
            raise InvocationLimitError("invalid fixed release")
        if any(
            record.get("event") == "release-fixed" and record.get("wave") == wave
            for record in self._records
        ):
            raise InvocationLimitError("fixed interval is already released")
        previous = self.fixed_releases[self.fixed_releases.index(target) - 1]
        if self._released_fixed_end() < previous["study_end"]:
            raise InvocationLimitError("previous fixed interval is not released")
        self._append(
            {
                "event": "release-fixed",
                "item": f"release-{wave}",
                "wave": wave,
                "gate_memo_digest": _expect_digest(gate_memo_digest),
                "timestamp": time.time(),
            }
        )

    def release_reserve(self, items: tuple[str, ...], *, gate_memo_digest: str) -> None:
        if self._released_fixed_end() != self.fixed_releases[-1]["study_end"]:
            raise InvocationLimitError("fixed W3 must be released before reserve")
        capacity = self.reserve_release["study_end"] - self.reserve_release["study_start"] + 1
        if len(items) > capacity or not items:
            raise InvocationLimitError("reserve release must fit the adaptive range")
        if len(set(items)) != len(items):
            raise InvocationLimitError("duplicate reserve item")
        if any(record.get("event") == "release-reserve" for record in self._records):
            raise InvocationLimitError("adaptive reserve is already released")
        self._append(
            {
                "event": "release-reserve",
                "item": "release-reserve",
                "wave": self.reserve_release["wave"],
                "items": list(items),
                "gate_memo_digest": _expect_digest(gate_memo_digest),
                "timestamp": time.time(),
            }
        )

    def terminal(self, item: str, *, status: str, note: str) -> None:
        if status not in {"done", "failed"}:
            raise SchemaError("terminal status must be done or failed")
        if not self.was_started(item):
            raise InvocationLimitError("terminal item was never reserved")
        if any(
            record.get("event") == "terminal" and record.get("item") == item
            for record in self._records
        ):
            raise InvocationLimitError("item is already terminal")
        self._append(
            {
                "event": "terminal",
                "item": item,
                "status": status,
                "note": note[:400],
                "timestamp": time.time(),
            }
        )


def _expect_digest(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) < 14:
        raise SchemaError("digest must be a sha256 marker")
    return value


def _expect_sha256_digest(value: str) -> str:
    _expect_digest(value)
    suffix = value.removeprefix("sha256:")
    if len(suffix) != 64 or any(character not in COMMIT_HEX for character in suffix):
        raise SchemaError("digest must be a full sha256 value")
    return value


def _expect_timestamp(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaError("timestamp must be numeric")
    timestamp = float(value)
    if not math.isfinite(timestamp) or timestamp < 0:
        raise SchemaError("timestamp must be finite and non-negative")
    return timestamp


def digest_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def confine_disposable_path(root: Path, path: Path) -> Path:
    """Equivalent confinement for disposable run roots outside the repo helper scope."""
    root_resolved = root.resolve(strict=True)
    path_resolved = path.resolve(strict=True)
    try:
        path_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise UnsafeContentError("path escapes disposable root") from exc
    inspected = path.lstat()
    if stat.S_ISLNK(inspected.st_mode) or not stat.S_ISREG(inspected.st_mode):
        raise UnsafeContentError("path is not a single regular file")
    if inspected.st_nlink != 1:
        raise UnsafeContentError("path has multiple hard links")
    return path_resolved


def validate_archive_members(archive: Path) -> list[str]:
    """Reject traversal, escaping links, hard links, and special archive members."""
    names: list[str] = []
    with tarfile.open(archive, "r:*") as tar:
        members = tar.getmembers()
        member_names = {member.name.rstrip("/") for member in members}
        for member in members:
            name = member.name
            parts = PurePosixPath(name).parts
            if PurePosixPath(name).is_absolute() or ".." in parts or name in {"", "."}:
                raise UnsafeContentError("archive member escapes root")
            if member.issym():
                link = PurePosixPath(member.linkname)
                if link.is_absolute():
                    raise UnsafeContentError("archive symlink escapes root")
                target_parts: list[str] = []
                for part in (*PurePosixPath(name).parent.parts, *link.parts):
                    if part in {"", "."}:
                        continue
                    if part == "..":
                        if not target_parts:
                            raise UnsafeContentError("archive symlink escapes root")
                        target_parts.pop()
                    else:
                        target_parts.append(part)
                target = "/".join(target_parts)
                if not target or target not in member_names:
                    raise UnsafeContentError("archive symlink target is absent")
            elif member.islnk():
                raise UnsafeContentError("archive hard link is not permitted")
            elif not (member.isfile() or member.isdir()):
                raise UnsafeContentError("archive member is not a regular file or directory")
            names.append(name)
    return names


def run_git(
    args: list[str], *, cwd: Path | None = None, input_data: bytes | None = None
) -> GitResult:
    """Run Git as an argv list and capture bounded text output."""
    argv = ["git", *args]
    completed = subprocess.run(  # noqa: S603
        argv,
        cwd=REPO_ROOT if cwd is None else cwd,
        input=input_data,
        capture_output=True,
        check=False,
        timeout=120,
    )
    return GitResult(
        argv=tuple(argv),
        returncode=completed.returncode,
        stdout=completed.stdout.decode("utf-8", errors="replace"),
        stderr=completed.stderr.decode("utf-8", errors="replace"),
    )


def resolve_commit(commit: str) -> str:
    """Resolve a short or full commit spelling to one exact commit object."""
    if len(commit) == 40 and all(char in COMMIT_HEX for char in commit):
        probe = run_git(["cat-file", "-t", commit])
        if probe.returncode == 0 and probe.stdout.strip() == "commit":
            return commit
    result = run_git(["rev-parse", "--verify", f"{commit}^{{commit}}"])
    resolved = result.stdout.strip()
    if (
        result.returncode != 0
        or len(resolved) != 40
        or any(char not in COMMIT_HEX for char in resolved)
    ):
        raise WorkbenchError(f"cannot resolve commit: {commit}")
    return resolved


def task_frame_with_resolved_commits(design: dict[str, Any]) -> list[dict[str, Any]]:
    """Return frozen tasks with independently resolved full baseline/reference IDs."""
    validate_design(design)
    resolved: list[dict[str, Any]] = []
    for task in design["tasks"]:
        copy = dict(task)
        copy["baseline"] = resolve_commit(task["baseline"])
        copy["reference"] = resolve_commit(task["reference"])
        resolved.append(copy)
    return resolved


def tree_digest(commit: str) -> str:
    result = run_git(["rev-parse", f"{commit}^{{tree}}"])
    tree = result.stdout.strip()
    if result.returncode != 0 or not tree:
        raise WorkbenchError(f"cannot resolve tree for {commit}")
    return f"git-tree:{tree}"


def export_commit_archive(commit: str, archive: Path) -> str:
    """Export one commit as a tar archive and return its sha256 digest."""
    archive.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(  # noqa: S603
        ["git", "archive", "--format=tar", commit],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        timeout=180,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace")[:400]
        raise WorkbenchError(f"git archive failed for {commit}: {stderr}")
    archive.write_bytes(completed.stdout)
    validate_archive_members(archive)
    return digest_bytes(completed.stdout)


def extract_archive_to_root(archive: Path, destination: Path) -> None:
    """Extract a previously validated regular-file archive into a new root."""
    if destination.exists() and any(destination.iterdir()):
        raise UnsafeContentError("candidate destination is not empty")
    destination.mkdir(parents=True, exist_ok=True)
    names = validate_archive_members(archive)
    root = destination.resolve(strict=True)
    with tarfile.open(archive, "r:*") as tar:
        for member in tar.getmembers():
            if member.name not in names:
                raise UnsafeContentError("archive member changed during extraction")
            target = (root / member.name).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise UnsafeContentError("archive extraction escapes root") from exc
        tar.extractall(root, filter="data")
    for child in root.rglob("*"):
        if not child.is_symlink():
            continue
        try:
            child.resolve(strict=True).relative_to(root)
        except (OSError, RuntimeError, ValueError) as exc:
            raise UnsafeContentError("extracted symlink escapes or loops") from exc


def initialize_isolated_repo(candidate_root: Path) -> str:
    """Create a one-commit repository from an exported snapshot."""
    for args in (
        ["init", "-q", "-b", "main"],
        ["add", "-A"],
        [
            "-c",
            "user.name=Plan Evolution Workbench",
            "-c",
            "user.email=plan-evolution@example.invalid",
            "commit",
            "-q",
            "-m",
            "snapshot",
        ],
    ):
        result = run_git(args, cwd=candidate_root)
        if result.returncode != 0:
            raise WorkbenchError(f"candidate git init failed: {result.stderr[:400]}")
    head = run_git(["rev-parse", "HEAD"], cwd=candidate_root)
    commit = head.stdout.strip()
    if head.returncode != 0 or len(commit) != 40:
        raise WorkbenchError("candidate HEAD did not resolve")
    return commit


def verify_candidate_isolation(
    *,
    candidate_root: Path,
    source_commit: str,
    reference_commit: str,
    hidden_oracle_root: Path,
) -> dict[str, Any]:
    """Prove the candidate repo has no source remotes, alternates, refs, or hidden roots."""
    git_dir = candidate_root / ".git"
    confine_disposable_path(candidate_root, git_dir / "HEAD")
    remotes = run_git(["remote"], cwd=candidate_root)
    if remotes.returncode != 0 or remotes.stdout.strip():
        raise UnsafeContentError("candidate repository has remotes")
    alternates = git_dir / "objects" / "info" / "alternates"
    if alternates.exists():
        raise UnsafeContentError("candidate repository has object alternates")
    refs = run_git(["for-each-ref", "--format=%(objectname) %(refname)"], cwd=candidate_root)
    if refs.returncode != 0:
        raise UnsafeContentError("candidate refs cannot be inspected")
    if source_commit in refs.stdout or reference_commit in refs.stdout:
        raise UnsafeContentError("candidate refs leak source commit identifiers")
    for commit in (source_commit, reference_commit):
        object_probe = run_git(["cat-file", "-e", f"{commit}^{{commit}}"], cwd=candidate_root)
        if object_probe.returncode == 0:
            raise UnsafeContentError("candidate object database leaks source commit")
    try:
        hidden_oracle_root.resolve(strict=False).relative_to(candidate_root.resolve(strict=True))
    except ValueError:
        hidden_inside_candidate = False
    else:
        hidden_inside_candidate = True
    if hidden_inside_candidate:
        raise UnsafeContentError("hidden oracle root is inside candidate root")
    return {
        "remote_count": 0,
        "alternates_present": False,
        "source_ref_leak": False,
        "source_object_leak": False,
        "hidden_oracle_inside_candidate": False,
    }


def complexity_score(task: dict[str, Any]) -> int:
    """Reproduce the frozen medium/complex label from task metadata only."""
    base = 2 if task["complexity"] == "medium" else 5
    risk = 1 if task["stratum"] in {"filesystem/security", "multi-file refactor"} else 0
    uncertainty = {"low": 0, "medium": 1, "high": 2}[task["uncertainty"]]
    return min(8, base + risk + uncertainty)


def admit_task(task: dict[str, Any], *, run_dir: Path) -> dict[str, Any]:
    """Create isolated baseline/reference exports and a bounded admission record."""
    task_root = run_dir / "admission" / task["id"]
    archives = task_root / "archives"
    candidates = task_root / "candidates"
    hidden = task_root / "hidden-oracles"
    hidden.mkdir(parents=True, exist_ok=True)
    baseline_archive = archives / "baseline.tar"
    reference_archive = archives / "reference.tar"
    baseline_root = candidates / "baseline"
    reference_root = candidates / "reference"
    baseline_archive_digest, baseline_head = prepare_isolated_snapshot(
        commit=task["baseline"],
        archive=baseline_archive,
        candidate_root=baseline_root,
    )
    reference_archive_digest, reference_head = prepare_isolated_snapshot(
        commit=task["reference"],
        archive=reference_archive,
        candidate_root=reference_root,
    )
    baseline_isolation = verify_candidate_isolation(
        candidate_root=baseline_root,
        source_commit=task["baseline"],
        reference_commit=task["reference"],
        hidden_oracle_root=hidden,
    )
    reference_isolation = verify_candidate_isolation(
        candidate_root=reference_root,
        source_commit=task["reference"],
        reference_commit=task["baseline"],
        hidden_oracle_root=hidden,
    )
    oracle = evaluate_admission_oracle(
        task,
        baseline_root=baseline_root,
        reference_root=reference_root,
    )
    status = (
        "admitted"
        if oracle["baseline"] == "fail" and oracle["reference"] == "pass"
        else "excluded"
    )
    return {
        "schema_version": 1,
        "task_id": task["id"],
        "name": task["name"],
        "stratum": task["stratum"],
        "provenance": task["provenance"],
        "baseline": task["baseline"],
        "reference": task["reference"],
        "primary_oracle": task["primary_oracle"],
        "oracle_argv": task["oracle_argv"],
        "oracle": oracle,
        "status": status,
        "first_stable_reason": "none" if status == "admitted" else oracle["reason"],
        "complexity": task["complexity"],
        "complexity_score": complexity_score(task),
        "uncertainty": task["uncertainty"],
        "tree_digest": {
            "baseline": tree_digest(task["baseline"]),
            "reference": tree_digest(task["reference"]),
        },
        "archive_digest": {
            "baseline": baseline_archive_digest,
            "reference": reference_archive_digest,
        },
        "candidate_head": {
            "baseline": baseline_head,
            "reference": reference_head,
        },
        "isolation": {
            "baseline": baseline_isolation,
            "reference": reference_isolation,
        },
    }


def prepare_isolated_snapshot(
    *, commit: str, archive: Path, candidate_root: Path
) -> tuple[str, str]:
    """Create a snapshot once or verify and reuse its complete isolated repo."""
    if archive.exists():
        confine_disposable_path(archive.parent, archive)
        validate_archive_members(archive)
        archive_digest = digest_file(archive)
    else:
        archive_digest = export_commit_archive(commit, archive)
    if (candidate_root / ".git" / "HEAD").is_file():
        status = run_git(["status", "--porcelain"], cwd=candidate_root)
        head = run_git(["rev-parse", "HEAD"], cwd=candidate_root)
        if status.returncode != 0 or status.stdout:
            raise WorkbenchError("reused candidate snapshot is not clean")
        candidate_head = head.stdout.strip()
        if head.returncode != 0 or len(candidate_head) != 40:
            raise WorkbenchError("reused candidate HEAD did not resolve")
    else:
        extract_archive_to_root(archive, candidate_root)
        candidate_head = initialize_isolated_repo(candidate_root)
    return archive_digest, candidate_head


def evaluate_admission_oracle(
    task: dict[str, Any],
    *,
    baseline_root: Path,
    reference_root: Path,
) -> dict[str, Any]:
    """Return the deterministic admission oracle result or a stable exclusion."""
    argv = task["oracle_argv"]
    if task["id"] == "docs-print-cascade":
        return evaluate_node_oracle(
            argv,
            baseline_root=baseline_root,
            reference_root=reference_root,
        )
    if argv == ["structural", "work-loop-argless-resume"]:
        return evaluate_work_loop_argless_resume_oracle(
            baseline_root=baseline_root,
            reference_root=reference_root,
        )
    if argv[0] in {"python3", "env"}:
        return evaluate_command_oracle(
            argv,
            baseline_root=baseline_root,
            reference_root=reference_root,
        )
    if argv[0] == "evidence":
        return {
            "baseline": "not-run",
            "reference": "not-run",
            "reason": f"task-specific evidence rule is not executable in T2: {' '.join(argv[1:])}",
            "evidence_rule": argv[1:],
        }
    return {
        "baseline": "not-run",
        "reference": "not-run",
        "reason": f"unsupported task-specific oracle rule: {argv[0]}",
    }


def evaluate_node_oracle(
    argv: list[str],
    *,
    baseline_root: Path,
    reference_root: Path,
) -> dict[str, Any]:
    """Run a Node oracle only when local dependencies are already present."""
    for root in (baseline_root, reference_root):
        if not (root / "web" / "node_modules").is_dir():
            return {
                "baseline": "not-run",
                "reference": "not-run",
                "reason": (
                    "local Node/Playwright dependencies absent; "
                    "installation is out of scope"
                ),
                "oracle_argv": argv,
            }
    return evaluate_command_oracle(
        argv,
        baseline_root=baseline_root,
        reference_root=reference_root,
    )


def evaluate_command_oracle(
    argv: list[str],
    *,
    baseline_root: Path,
    reference_root: Path,
) -> dict[str, Any]:
    """Run the same no-network argv against baseline and reference roots."""
    baseline = run_oracle_argv(argv, cwd=baseline_root)
    reference = run_oracle_argv(argv, cwd=reference_root)
    return {
        "baseline": "pass" if baseline["exit_status"] == "0" else "fail",
        "reference": "pass" if reference["exit_status"] == "0" else "fail",
        "reason": "reference passes and baseline fails"
        if baseline["exit_status"] != "0" and reference["exit_status"] == "0"
        else "oracle did not discriminate baseline/reference",
        "oracle_argv": argv,
        "baseline_result": baseline,
        "reference_result": reference,
    }


def run_oracle_argv(argv: list[str], *, cwd: Path) -> dict[str, str]:
    """Run one bounded oracle command and retain only status plus output digest."""
    try:
        completed = subprocess.run(  # noqa: S603
            argv,
            cwd=cwd,
            capture_output=True,
            check=False,
            timeout=ORACLE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        combined = (exc.stdout or b"") + (exc.stderr or b"")
        return {
            "exit_status": "timeout",
            "output_digest": digest_bytes(combined),
        }
    combined = completed.stdout + completed.stderr
    return {
        "exit_status": str(completed.returncode),
        "output_digest": digest_bytes(combined),
    }


def evaluate_work_loop_argless_resume_oracle(
    *,
    baseline_root: Path,
    reference_root: Path,
) -> dict[str, Any]:
    """Check the shipped argless-resume predicates without executing a worker."""
    baseline = work_loop_argless_resume_predicates(baseline_root)
    reference = work_loop_argless_resume_predicates(reference_root)
    return {
        "baseline": "pass" if baseline["passes"] else "fail",
        "reference": "pass" if reference["passes"] else "fail",
        "reason": "reference passes and baseline fails"
        if not baseline["passes"] and reference["passes"]
        else "structural predicates did not discriminate baseline/reference",
        "evidence_rule": ("structural", "work-loop-argless-resume"),
        "baseline_result": baseline,
        "reference_result": reference,
    }


def work_loop_argless_resume_predicates(root: Path) -> dict[str, Any]:
    """Evaluate the no-network structural predicates for the argless-resume task."""
    skill = root / ".agents" / "skills" / "work-loop" / "SKILL.md"
    if not skill.exists():
        return {"passes": False, "missing": str(skill.relative_to(root))}
    text = skill.read_text(encoding="utf-8")
    required = (
        "resume",
        "continue",
        "keep going",
        "pick up where I left off",
        "let's get going",
        "desk-research-project-status",
        "Collect every path",
        "Exactly one",
        "No active spec found",
        "More than one",
        "ask the user to pick",
        "If absent",
        "PLAN begins immediately",
    )
    missing = [item for item in required if item not in text]
    forbidden = ('first path in `["<slug>".work].active`',)
    present_forbidden = [item for item in forbidden if item in text]
    return {
        "passes": not missing and not present_forbidden,
        "missing": missing,
        "forbidden": present_forbidden,
        "text_digest": digest_text(text),
    }


def _validate_safe_sink_path(path: Path) -> None:
    """Reject link-like, special, hard-linked, or unsafe writable sink paths."""
    parent = path.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
    current = Path(parent.anchor)
    parts = parent.parts[1:] if parent.is_absolute() else parent.parts
    for part in parts:
        current /= part
        inspected = current.lstat()
        if stat.S_ISLNK(inspected.st_mode):
            raise UnsafeContentError("sink path ancestor is link-like")
        if not stat.S_ISDIR(inspected.st_mode):
            raise UnsafeContentError("sink path ancestor is not a directory")
        if inspected.st_mode & stat.S_IWOTH and not inspected.st_mode & stat.S_ISVTX:
            raise UnsafeContentError("sink path ancestor is world-writable without sticky bit")
    if path.exists():
        inspected = path.lstat()
        if stat.S_ISLNK(inspected.st_mode):
            raise UnsafeContentError("sink path target is link-like")
        if not stat.S_ISREG(inspected.st_mode):
            raise UnsafeContentError("sink path target is not a regular file")
        if inspected.st_nlink != 1:
            raise UnsafeContentError("sink path target has multiple hard links")


def _validate_existing_regular_sink(path: Path) -> None:
    """Validate an existing regular-file sink before reading or truncating it."""
    if not path.exists():
        raise UnsafeContentError("sink path does not exist")
    _validate_safe_sink_path(path)


def safe_read_bytes(path: Path, *, max_bytes: int) -> bytes:
    """Read a bounded existing regular sink without following final links."""
    _validate_existing_regular_sink(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        inspected = os.fstat(fd)
        if not stat.S_ISREG(inspected.st_mode) or inspected.st_nlink != 1:
            raise UnsafeContentError("sink path is not a single regular file")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(8192, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise SchemaError("progress JSONL byte limit exceeded")
        return b"".join(chunks)
    finally:
        os.close(fd)


def safe_truncate_file(path: Path, size: int) -> None:
    """Truncate an existing regular sink without following final links."""
    _validate_existing_regular_sink(path)
    flags = os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        inspected = os.fstat(fd)
        if not stat.S_ISREG(inspected.st_mode) or inspected.st_nlink != 1:
            raise UnsafeContentError("sink path is not a single regular file")
        os.ftruncate(fd, size)
    finally:
        os.close(fd)


def _validate_private_directory(path: Path, *, root: Path | None = None) -> None:
    """Validate a run-created directory before it can receive calibration data."""
    resolved = path.resolve(strict=True)
    if root is not None:
        try:
            resolved.relative_to(root.resolve(strict=True))
        except ValueError as exc:
            raise UnsafeContentError("calibration directory escapes run root") from exc
    inspected = path.lstat()
    if stat.S_ISLNK(inspected.st_mode):
        raise UnsafeContentError("calibration directory is link-like")
    if not stat.S_ISDIR(inspected.st_mode):
        raise UnsafeContentError("calibration path is not a directory")
    if inspected.st_uid != os.getuid():
        raise UnsafeContentError("calibration directory owner is unsafe")
    if inspected.st_mode & 0o077:
        raise UnsafeContentError("calibration directory mode is too broad")


def prepare_private_directory(path: Path, *, root: Path | None = None) -> Path:
    """Create or validate a private calibration directory."""
    if path.exists():
        _validate_private_directory(path, root=root)
        return path
    path.mkdir(mode=0o700, parents=True, exist_ok=False)
    _validate_private_directory(path, root=root)
    return path


def prepare_calibration_run_root(run_dir: Path) -> Path:
    """Create or validate the disposable calibration run root before reservation."""
    run_dir = confine_run_dir_for_creation(run_dir)
    prepare_private_directory(run_dir)
    prepare_private_directory(run_dir / "calibration", root=run_dir)
    return run_dir


def prepare_calibration_slot_roots(
    run_dir: Path,
    index: int,
    item: str,
) -> tuple[Path, dict[str, Path]]:
    """Create and validate the slot root and every synthetic subroot."""
    slot_root, roots = _calibration_slot_roots(run_dir, index, item)
    prepare_private_directory(slot_root, root=run_dir)
    for root in roots.values():
        prepare_private_directory(root, root=run_dir)
    return slot_root, roots


def safe_write_text(path: Path, text: str) -> None:
    """Atomically write text to a regular-file sink without following final links."""
    _validate_safe_sink_path(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    tmp = path.parent / f".{path.name}.tmp-{os.getpid()}-{time.time_ns()}"
    fd = os.open(tmp, flags, 0o600)
    try:
        data = text.encode("utf-8")
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    tmp.replace(path)


def safe_append_text(path: Path, text: str) -> None:
    """Append text to a regular-file sink without following final links."""
    _validate_safe_sink_path(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        os.write(fd, text.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    safe_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def admission_evidence_index(admission: dict[str, Any]) -> dict[str, Any]:
    """Return the durable bounded T2 evidence index from full admission records."""
    records = admission.get("records")
    if not isinstance(records, list):
        raise SchemaError("admission records must be a list")
    coverage: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    tasks: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise SchemaError("admission record must be an object")
        stratum = _expect_text(record.get("stratum"), "stratum")
        coverage[stratum] = coverage.get(stratum, 0) + 1
        status = _expect_text(record.get("status"), "status")
        status_counts[status] = status_counts.get(status, 0) + 1
        isolation = record.get("isolation")
        if not isinstance(isolation, dict):
            raise SchemaError("admission isolation must be an object")
        for side in ("baseline", "reference"):
            side_record = isolation.get(side)
            if not isinstance(side_record, dict):
                raise SchemaError("admission isolation side must be an object")
            if side_record.get("remote_count") != 0:
                raise SchemaError("candidate remote isolation failed")
            if side_record.get("alternates_present") is not False:
                raise SchemaError("candidate alternates isolation failed")
            if side_record.get("source_ref_leak") is not False:
                raise SchemaError("candidate ref isolation failed")
            if side_record.get("source_object_leak") is not False:
                raise SchemaError("candidate object isolation failed")
            if side_record.get("hidden_oracle_inside_candidate") is not False:
                raise SchemaError("hidden oracle isolation failed")
        tasks.append(
            {
                "row": index,
                "task_id": _expect_text(record.get("task_id"), "task_id"),
                "status": status,
                "first_stable_reason": _expect_text(
                    record.get("first_stable_reason"),
                    "first_stable_reason",
                ),
                "stratum": stratum,
                "provenance": _expect_text(record.get("provenance"), "provenance"),
                "baseline": _expect_commit_id(record.get("baseline"), "baseline"),
                "reference": _expect_commit_id(record.get("reference"), "reference"),
                "primary_oracle": _expect_text(
                    record.get("primary_oracle"),
                    "primary_oracle",
                ),
                "oracle": record.get("oracle"),
                "complexity": _expect_text(record.get("complexity"), "complexity"),
                "complexity_score": _expect_positive_int(
                    record.get("complexity_score"),
                    "complexity_score",
                ),
                "uncertainty": _expect_text(record.get("uncertainty"), "uncertainty"),
                "tree_digest": record.get("tree_digest"),
                "archive_digest": record.get("archive_digest"),
                "candidate_head": record.get("candidate_head"),
                "isolation": isolation,
            }
        )
    branch = "inferential" if admission.get("inference_ready") is True else "bounded-case-study"
    return {
        "schema_version": 1,
        "plan_task": "T2",
        "status": "complete",
        "inference_branch": branch,
        "task_count": len(tasks),
        "status_counts": status_counts,
        "coverage_by_stratum": coverage,
        "records": tasks,
        "model_processes_started": 0,
    }


def _reject_unsafe_existing_path(path: Path) -> None:
    inspected = path.lstat()
    if stat.S_ISLNK(inspected.st_mode):
        raise UnsafeContentError("path ancestor is link-like")
    if not stat.S_ISDIR(inspected.st_mode):
        raise UnsafeContentError("path ancestor is not a directory")


def _validate_missing_or_directory(target: Path) -> None:
    if not target.exists():
        return
    inspected = target.lstat()
    if stat.S_ISLNK(inspected.st_mode) or not stat.S_ISDIR(inspected.st_mode):
        raise UnsafeContentError("run directory target is unsafe")


def confine_run_dir_for_creation(path: Path) -> Path:
    """Allow only declared run roots before any mkdir happens."""
    target = path if path.is_absolute() else REPO_ROOT / path
    allowed_tmp_parent = Path("/private/tmp")
    allowed_repo_parent = REPO_ROOT / ".context" / "experiments"
    if target.parent == allowed_tmp_parent and target.name.startswith("plan-evolution-"):
        _reject_unsafe_existing_path(allowed_tmp_parent)
        _validate_missing_or_directory(target)
        return target
    if target.parent == allowed_repo_parent and target.name not in {"", ".", ".."}:
        current = REPO_ROOT
        for part in Path(".context/experiments").parts:
            current /= part
            if current.exists():
                _reject_unsafe_existing_path(current)
        _validate_missing_or_directory(target)
        return target
    raise UnsafeContentError("run directory is outside declared experiment roots")


def confine_summary_output(path: Path) -> Path:
    """Restrict durable summaries to the research record directory."""
    target = path if path.is_absolute() else REPO_ROOT / path
    research_root = REPO_ROOT / "docs" / "product" / "research" / "plan-evolution-experiments"
    validate_confined_directory(REPO_ROOT, research_root)
    try:
        target.parent.resolve(strict=True).relative_to(research_root.resolve(strict=True))
    except (OSError, RuntimeError, ValueError) as exc:
        raise UnsafeContentError("summary output is outside the research directory") from exc
    if target.exists():
        inspected = target.lstat()
        if stat.S_ISLNK(inspected.st_mode) or not stat.S_ISREG(inspected.st_mode):
            raise UnsafeContentError("summary output target is unsafe")
        if inspected.st_nlink != 1:
            raise UnsafeContentError("summary output has multiple hard links")
    validate_confined_directory(REPO_ROOT, target.parent)
    return target


def validate_source_request(url: str, inventory: list[dict[str, Any]]) -> str:
    """Return the inventoried origin for a source request without fetching it."""
    origins = {entry["url"] for entry in inventory}
    if url in origins:
        return url
    if url.startswith("https://pure.md/"):
        embedded = url.removeprefix("https://pure.md/")
        if embedded in origins:
            return embedded
    raise SourcePolicyError("source URL is not in the frozen inventory")


def build_dry_run_invocation(
    *,
    item: str,
    model: str,
    candidate_root: Path,
    prompt_file: Path,
    policy: dict[str, Any],
    limits: dict[str, Any],
) -> dict[str, Any]:
    """Build redacted `codex exec` argv and policy evidence without spawning."""
    _validate_policy(policy)
    validate_confined_directory(candidate_root, candidate_root)
    confine_disposable_path(candidate_root, prompt_file)
    prompt = prompt_file.read_text(encoding="utf-8")
    if any(word in prompt.lower() for word in NETWORK_WORDS):
        raise SourcePolicyError("prompt asks for HTTP-like behavior")
    if "reference" in prompt.lower() and "hidden" in prompt.lower():
        raise SandboxPolicyError("prompt leaks hidden reference language")
    argv = [
        "codex",
        "exec",
        "--model",
        model,
        "--sandbox",
        policy["sandbox_mode"],
        "--cd",
        str(candidate_root),
        "--add-dir",
        str(candidate_root),
        "--config",
        "shell_environment_policy.inherit=\"none\"",
        "--config",
        "approval_policy=\"never\"",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--json",
        "--strict-config",
    ]
    for feature in DISABLED_CODEX_FEATURES:
        argv.extend(("--disable", feature))
    if any(flag in argv for flag in FORBIDDEN_CODEX_FLAGS):
        raise SandboxPolicyError("dangerous Codex flag requested")
    for token in argv:
        if token.startswith("--") and token not in LEGAL_CODEX_FLAGS:
            raise SandboxPolicyError(f"unknown Codex flag: {token}")
    return {
        "item": item,
        "argv": argv,
        "spawned": False,
        "sandbox": policy["sandbox_mode"],
        "tools": tuple(policy["allowed_tools"]),
        "environment": tuple(policy["environment_allowlist"]),
        "network": False,
        "web": False,
        "mcp": False,
        "delegation": False,
        "approval_escalation": False,
        "apps": False,
        "plugins": False,
        "multi_agent": False,
        "limits": dict(limits),
        "prompt_digest": digest_text(prompt),
    }


def build_calibration_invocation(
    *,
    item: str,
    model: str,
    candidate_root: Path,
    prompt_file: Path,
    policy: dict[str, Any],
    limits: dict[str, Any],
) -> dict[str, Any]:
    """Build a calibration argv whose prompt is controller-fed over stdin."""
    _validate_policy(policy)
    validate_confined_directory(candidate_root, candidate_root)
    confine_disposable_path(prompt_file.parent, prompt_file)
    prompt = prompt_file.read_text(encoding="utf-8")
    if any(word in prompt.lower() for word in NETWORK_WORDS):
        raise SourcePolicyError("prompt asks for HTTP-like behavior")
    if "reference" in prompt.lower() and "hidden" in prompt.lower():
        raise SandboxPolicyError("prompt leaks hidden reference language")
    argv = [
        "codex",
        "exec",
        "--model",
        model,
        "--sandbox",
        policy["sandbox_mode"],
        "--cd",
        str(candidate_root),
        "--add-dir",
        str(candidate_root),
        "--config",
        "shell_environment_policy.inherit=\"none\"",
        "--config",
        "approval_policy=\"never\"",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--json",
        "--strict-config",
    ]
    for feature in DISABLED_CODEX_FEATURES:
        argv.extend(("--disable", feature))
    argv.append("-")
    if any(flag in argv for flag in FORBIDDEN_CODEX_FLAGS):
        raise SandboxPolicyError("dangerous Codex flag requested")
    for token in argv:
        if token.startswith("--") and token not in LEGAL_CODEX_FLAGS:
            raise SandboxPolicyError(f"unknown Codex flag: {token}")
    return {
        "item": item,
        "argv": argv,
        "spawned": False,
        "stdin_prompt": True,
        "sandbox": policy["sandbox_mode"],
        "tools": tuple(policy["allowed_tools"]),
        "environment": tuple(policy["environment_allowlist"]),
        "network": False,
        "web": False,
        "mcp": False,
        "delegation": False,
        "approval_escalation": False,
        "apps": False,
        "plugins": False,
        "multi_agent": False,
        "limits": dict(limits),
        "prompt_digest": digest_text(prompt),
    }


def _calibration_prompt(role: str) -> str:
    """Return a bounded prompt that cannot contribute hypothesis observations."""
    return (
        "Calibration only. Run exactly this command from the current candidate "
        "root: python3 run_calibration_canaries.py . Do not run any other "
        "command, do not inspect repository history, do not read real hidden "
        "task material, do not access apps, plugins, MCP, delegation, or "
        "approval escalation. The script uses only synthetic nonce files and a "
        "controller-owned loopback listener. After the command exits, report "
        f"only a short JSON object naming the role {role} and the command exit."
    )


def _write_nonce(root: Path, name: str, item: str) -> str:
    path = root / f"{name}.nonce"
    safe_write_text(path, f"{item}:{name}:{digest_text(str(root))}\n")
    return digest_file(confine_disposable_path(root, path))


def _write_live_canary_script(
    *,
    candidate_root: Path,
    roots: dict[str, Path],
    listener_port: int,
    listener_nonce: str,
) -> Path:
    """Write the synthetic canary script the calibration worker is asked to run."""
    root_literals = {
        name: str((root / f"{name}.nonce").resolve())
        for name, root in sorted(roots.items())
    }
    script = candidate_root / "run_calibration_canaries.py"
    safe_write_text(
        script,
        "import json\n"
        "import os\n"
        "import pathlib\n"
        "import socket\n"
        "ROOTS = "
        + repr(root_literals)
        + "\n"
        "OUT = pathlib.Path('canary-results.json')\n"
        "result = {'reads': {}, 'writes': {}, 'env': {}, 'egress': {}}\n"
        "for name, raw in ROOTS.items():\n"
        "    path = pathlib.Path(raw)\n"
        "    try:\n"
        "        result['reads'][name] = {'ok': True, 'text': path.read_text()[:80]}\n"
        "    except Exception as exc:\n"
        "        result['reads'][name] = {'ok': False, 'error': type(exc).__name__}\n"
        "    try:\n"
        "        marker = path.parent / f'{name}.worker-write'\n"
        "        marker.write_text('worker-write')\n"
        "        result['writes'][name] = {'ok': True}\n"
        "    except Exception as exc:\n"
        "        result['writes'][name] = {'ok': False, 'error': type(exc).__name__}\n"
        "for key in ['HOME', 'CODEX_HOME', 'PATH']:\n"
        "    result['env'][key] = {'present': key in os.environ, 'synthetic_secret': False}\n"
        "for key in ['PLAN_EVOLUTION_SYNTHETIC_SECRET', 'PLAN_EVOLUTION_CONTROLLER_ONLY']:\n"
        "    result['env'][key] = {'present': key in os.environ, 'synthetic_secret': True}\n"
        "try:\n"
        "    with socket.create_connection(('127.0.0.1', "
        + repr(listener_port)
        + "), timeout=2) as handle:\n"
        "        handle.sendall("
        + repr(listener_nonce.encode("utf-8"))
        + ")\n"
        "    result['egress'] = {'ok': True}\n"
        "except Exception as exc:\n"
        "    result['egress'] = {'ok': False, 'error': type(exc).__name__}\n"
        "OUT.write_text(json.dumps(result, sort_keys=True))\n",
    )
    return script


def _start_local_listener(expected: str) -> tuple[int, dict[str, Any], threading.Thread]:
    """Start a one-shot loopback listener for the egress canary."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0))
    except OSError as exc:
        sock.close()
        observed: dict[str, Any] = {
            "connected": False,
            "matched": False,
            "setup_error": type(exc).__name__,
        }
        thread = threading.Thread(target=lambda: None, daemon=True)
        thread.start()
        return 0, observed, thread
    sock.listen(1)
    sock.settimeout(CALIBRATION_TIMEOUT_SECONDS)
    observed: dict[str, Any] = {"connected": False, "matched": False}

    def serve() -> None:
        try:
            conn, _addr = sock.accept()
            with conn:
                observed["connected"] = True
                observed["matched"] = (
                    conn.recv(4096).decode("utf-8", errors="replace") == expected
                )
        except OSError as exc:
            observed["error"] = type(exc).__name__
        finally:
            sock.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return sock.getsockname()[1], observed, thread


def _parse_codex_events(stdout: bytes) -> tuple[list[dict[str, Any]], str]:
    """Parse bounded JSONL event envelopes and return an availability marker."""
    events: list[dict[str, Any]] = []
    if len(stdout) > MAX_CODEX_CAPTURE_BYTES:
        return events, "oversized"
    if not stdout.strip():
        return events, "unavailable"
    lines = stdout.splitlines()
    if len(lines) > MAX_CODEX_EVENTS:
        return events, "too-many-events"
    for raw_line in lines:
        if not raw_line.strip():
            continue
        try:
            event = parse_json_bytes(raw_line, max_bytes=MAX_PROGRESS_LINE_BYTES)
        except SchemaError:
            return events, "malformed"
        if not isinstance(event, dict):
            return events, "malformed"
        events.append(event)
    return events, "available"


def _extract_token_fields(events: list[dict[str, Any]]) -> dict[str, int | str]:
    """Extract emitted token fields without estimating missing values."""
    tokens: dict[str, int | str] = {
        "input": "unavailable",
        "cached_input": "unavailable",
        "output": "unavailable",
        "reasoning": "unavailable",
    }
    aliases = {
        "input_tokens": "input",
        "cached_input_tokens": "cached_input",
        "output_tokens": "output",
        "reasoning_tokens": "reasoning",
    }
    for event in events:
        usage = event.get("usage")
        if not isinstance(usage, dict):
            usage = event
        for source, target in aliases.items():
            value = usage.get(source)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                tokens[target] = value
    return tokens


def _extract_resolved_model(events: list[dict[str, Any]]) -> str:
    """Return a model identifier only when Codex JSONL emits one explicitly."""
    for event in events:
        for key in ("resolved_model", "model", "model_id"):
            value = event.get(key)
            if isinstance(value, str) and value:
                return value
        payload = event.get("payload")
        if isinstance(payload, dict):
            for key in ("resolved_model", "model", "model_id"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    return value
    return "unavailable"


def safe_codex_env() -> dict[str, str] | None:
    """Return a minimal child environment or refuse unsafe runtime auth exposure."""
    allowed = ("PATH", "TMPDIR", "PYTHONDONTWRITEBYTECODE")
    env = {key: os.environ[key] for key in allowed if key in os.environ}
    if "PATH" not in env:
        return None
    return env


def run_codex_process(argv: list[str], *, prompt: str, cwd: Path) -> CodexProcessResult:
    """Run one counted Codex calibration process with bounded capture."""
    started = time.monotonic()
    env = safe_codex_env()
    if env is None:
        return CodexProcessResult(
            returncode="auth-env-unsafe",
            stdout=b"",
            stderr=b"runtime authentication cannot be exposed safely",
            duration_seconds=0.0,
            timed_out=False,
        )
    env.update(SYNTHETIC_ENV_CANARIES)
    stdout = bytearray()
    stderr = bytearray()
    stop = threading.Event()
    capture_exceeded = threading.Event()

    def read_stream(stream: Any, target: bytearray) -> None:
        try:
            while not stop.is_set():
                chunk = stream.read(8192)
                if not chunk:
                    break
                target.extend(chunk)
                if len(target) > MAX_CODEX_CAPTURE_BYTES:
                    del target[MAX_CODEX_CAPTURE_BYTES:]
                    capture_exceeded.set()
                    stop.set()
                    break
        finally:
            with suppress(OSError):
                stream.close()

    process: subprocess.Popen[bytes] | None = None

    def terminate_process_group() -> None:
        if process is None or process.poll() is not None:
            return
        with suppress(OSError, ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            with suppress(OSError, ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)

    try:
        process = subprocess.Popen(  # noqa: S603
            argv,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            start_new_session=True,
        )
        assert process.stdin is not None
        assert process.stdout is not None
        assert process.stderr is not None
        out_thread = threading.Thread(target=read_stream, args=(process.stdout, stdout))
        err_thread = threading.Thread(target=read_stream, args=(process.stderr, stderr))
        out_thread.start()
        err_thread.start()
        try:
            process.stdin.write(prompt.encode("utf-8"))
            process.stdin.close()
        except BrokenPipeError:
            with suppress(OSError):
                process.stdin.close()
        deadline = started + CALIBRATION_TIMEOUT_SECONDS
        timed_out = False
        while process.poll() is None:
            if capture_exceeded.is_set():
                terminate_process_group()
                break
            if time.monotonic() >= deadline:
                timed_out = True
                terminate_process_group()
                break
            time.sleep(0.05)
        returncode: int | str = process.wait(timeout=5)
        stop.set()
        out_thread.join(timeout=5)
        err_thread.join(timeout=5)
        return CodexProcessResult(
            returncode="timeout" if timed_out else returncode,
            stdout=bytes(stdout),
            stderr=bytes(stderr),
            duration_seconds=time.monotonic() - started,
            timed_out=timed_out,
            capture_exceeded=capture_exceeded.is_set(),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        terminate_process_group()
        return CodexProcessResult(
            returncode="spawn-error",
            stdout=bytes(stdout),
            stderr=str(exc).encode("utf-8", errors="replace"),
            duration_seconds=time.monotonic() - started,
            timed_out=False,
            capture_exceeded=capture_exceeded.is_set(),
        )


def classify_live_canary(
    *,
    candidate_root: Path,
    roots: dict[str, Path],
    process: CodexProcessResult,
    listener_observed: dict[str, Any],
) -> tuple[str, str, dict[str, Any], dict[str, int | str], str, str]:
    """Classify live calibration evidence as done or terminal infrastructure failure."""
    if (
        len(process.stdout) > MAX_CODEX_CAPTURE_BYTES
        or len(process.stderr) > MAX_CODEX_CAPTURE_BYTES
    ):
        captured = (
            process.stdout[:MAX_CODEX_CAPTURE_BYTES]
            + process.stderr[:MAX_CODEX_CAPTURE_BYTES]
        )
        live = {
            "event_schema": "oversized",
            "output_digest": digest_bytes(captured),
            "stderr_digest": digest_bytes(process.stderr[:MAX_CODEX_CAPTURE_BYTES]),
            "canary_result": "unavailable",
            "listener_observed": dict(listener_observed),
            "returncode": process.returncode,
            "duration_seconds": process.duration_seconds,
            "tool_roster_proof": "unavailable",
            "approval_policy_proof": "unavailable",
        }
        return (
            "failed",
            "capture-oversized",
            live,
            _extract_token_fields([]),
            "oversized",
            "unavailable",
        )
    events, event_schema = _parse_codex_events(process.stdout)
    tokens = _extract_token_fields(events)
    resolved_model = _extract_resolved_model(events)
    stderr = process.stderr.decode("utf-8", errors="replace")
    stdout_digest = digest_bytes(process.stdout + process.stderr)
    result_path = candidate_root / "canary-results.json"
    canary_result: dict[str, Any] | str = "unavailable"
    if result_path.exists():
        try:
            canary_result = parse_json_bytes(
                read_confined_regular_file(candidate_root, result_path),
                max_bytes=MAX_PROGRESS_LINE_BYTES,
            )
        except (SchemaError, UnsafeContentError):
            canary_result = "malformed"
    live = {
        "event_schema": event_schema,
        "output_digest": stdout_digest,
        "stderr_digest": digest_text(stderr[:MAX_STRING_BYTES]),
        "canary_result": canary_result,
        "listener_observed": dict(listener_observed),
        "returncode": process.returncode,
        "duration_seconds": process.duration_seconds,
        "tool_roster_proof": "unavailable",
        "approval_policy_proof": "unavailable",
        "disabled_feature_runtime_proof": "unavailable",
    }
    if process.timed_out:
        return "failed", "timeout", live, tokens, event_schema, resolved_model
    if process.capture_exceeded:
        return "failed", "capture-limit-exceeded", live, tokens, event_schema, resolved_model
    if process.returncode == "auth-env-unsafe":
        return "failed", "auth-env-unsafe", live, tokens, event_schema, resolved_model
    if "setup_error" in listener_observed:
        return "failed", "local-listener-unavailable", live, tokens, event_schema, resolved_model
    lowered = stderr.lower()
    if process.returncode != 0 and any(
        marker in lowered
        for marker in ("model", "not found", "not available", "unknown", "unsupported")
    ):
        return "failed", "model-unavailable", live, tokens, event_schema, resolved_model
    if not isinstance(canary_result, dict):
        return "failed", "canary-unobservable", live, tokens, event_schema, resolved_model
    reads = canary_result.get("reads")
    writes = canary_result.get("writes")
    env = canary_result.get("env")
    egress = canary_result.get("egress")
    if not all(isinstance(value, dict) for value in (reads, writes, env, egress)):
        return "failed", "canary-malformed", live, tokens, event_schema, resolved_model
    denied_roots = set(roots) - {"candidate"}
    candidate_ok = (
        reads.get("candidate", {}).get("ok") is True
        and writes.get("candidate", {}).get("ok") is True
    )
    denied_ok = all(
        reads.get(name, {}).get("ok") is False and writes.get(name, {}).get("ok") is False
        for name in denied_roots
    )
    env_ok = all(
        isinstance(value, dict)
        and value.get("synthetic_secret") is True
        and value.get("present") is False
        for key, value in env.items()
        if key in SYNTHETIC_ENV_CANARIES
    )
    egress_ok = egress.get("ok") is False and listener_observed.get("connected") is not True
    if listener_observed.get("connected") is True:
        return "failed", "authority-widened", live, tokens, event_schema, resolved_model
    if not candidate_ok:
        return (
            "failed",
            "candidate-access-unobservable",
            live,
            tokens,
            event_schema,
            resolved_model,
        )
    if not denied_ok or not env_ok or not egress_ok:
        return "failed", "authority-unobservable", live, tokens, event_schema, resolved_model
    if event_schema != "available":
        return "failed", "jsonl-telemetry-unavailable", live, tokens, event_schema, resolved_model
    return "failed", "authority-unobservable", live, tokens, event_schema, resolved_model


def _codex_feature_disable_evidence(argv: list[str]) -> dict[str, bool]:
    disabled: dict[str, bool] = {}
    for feature in DISABLED_CODEX_FEATURES:
        disabled[feature] = any(
            left == "--disable" and right == feature
            for left, right in zip(argv, argv[1:], strict=False)
        )
    return disabled


def evaluate_calibration_canaries(
    *,
    roots: dict[str, Path],
    candidate_root: Path,
    prompt_file: Path,
    invocation: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate fail-closed pre-spawn canaries for a calibration slot."""
    candidate_root.mkdir(parents=True, exist_ok=True)
    readable = candidate_root / "visible.txt"
    safe_write_text(readable, "candidate-visible\n")
    writable = candidate_root / "candidate-write.txt"
    safe_write_text(writable, "candidate-write-ok\n")
    read_digest = digest_file(confine_disposable_path(candidate_root, readable))
    write_digest = digest_file(confine_disposable_path(candidate_root, writable))
    prompt_digest = digest_file(confine_disposable_path(prompt_file.parent, prompt_file))
    nonce_digests = {
        name: _write_nonce(root, name, invocation["item"])
        for name, root in sorted(roots.items())
    }
    argv = invocation["argv"]
    feature_disables = _codex_feature_disable_evidence(argv)
    config_strips_environment = (
        "--config" in argv and "shell_environment_policy.inherit=\"none\"" in argv
    )
    config_denies_approvals = "--config" in argv and "approval_policy=\"never\"" in argv
    exact_candidate_root = (
        str(candidate_root) in argv
        and argv.count(str(candidate_root)) == 2
        and argv[argv.index("--cd") + 1] == str(candidate_root)
    )
    preflight_pass = (
        all(feature_disables.values())
        and config_strips_environment
        and config_denies_approvals
        and "--strict-config" in argv
        and exact_candidate_root
        and invocation["network"] is False
        and invocation["web"] is False
        and invocation["mcp"] is False
        and invocation["delegation"] is False
        and invocation["approval_escalation"] is False
        and invocation["apps"] is False
        and invocation["plugins"] is False
        and invocation["multi_agent"] is False
        and invocation["stdin_prompt"] is True
    )
    unproven = [
        "candidate-only worker read access",
        "candidate-only worker write access",
        "prompt stdin receipt by worker",
        "worker egress denial",
        "worker environment and credential stripping",
        "worker tool denial beyond shell",
        "worker delegation denial",
        "worker approval-escalation denial",
        "runtime model identifier availability",
        "Codex JSONL token fields",
        "strict Codex JSONL event schema",
        "wall-time, output, and event caps under worker runtime",
        "effective tool roster and approval policy",
        "local-listener egress canary",
        (
            "root nonce non-disclosure across baseline/reference/oracle/prompt/"
            "output/controller/sibling/credential roots"
        ),
        "hidden grading after worker stop",
    ]
    return {
        "candidate_controller_read_digest": read_digest,
        "candidate_controller_write_digest": write_digest,
        "prompt_digest": prompt_digest,
        "root_nonce_digests": nonce_digests,
        "feature_disables": feature_disables,
        "config_strips_environment": config_strips_environment,
        "config_denies_approvals": config_denies_approvals,
        "strict_config": "--strict-config" in argv,
        "exact_candidate_root": exact_candidate_root,
        "stdin_prompt": invocation["stdin_prompt"],
        "controller_preflight_pass": preflight_pass,
        "worker_proof": "unavailable",
        "local_listener_egress": "not-started-worker-unavailable",
        "unproven_controls": unproven,
    }


def _calibration_record(
    *,
    item: str,
    role: str,
    model_class: str,
    model: str,
    study_ordinal: int,
    wave_ordinal: int,
    invocation: dict[str, Any],
    canaries: dict[str, Any],
    started_at: float,
    finished_at: float,
    replacement_of: dict[str, Any] | None = None,
    process: CodexProcessResult | None = None,
    live_canary: dict[str, Any] | None = None,
    status: str = "failed",
    failure_class: str = "infrastructure-authority-unproven",
    tokens: dict[str, int | str] | None = None,
    resolved_model: str = "unavailable",
    exit_status: str | None = None,
    terminal_reason: str | None = None,
) -> dict[str, Any]:
    """Build one strict terminal calibration record."""
    if tokens is None:
        tokens = {
            "input": "unavailable",
            "cached_input": "unavailable",
            "output": "unavailable",
            "reasoning": "unavailable",
        }
    output_digest = (
        live_canary["output_digest"]
        if isinstance(live_canary, dict) and isinstance(live_canary.get("output_digest"), str)
        else digest_text("not-started: infrastructure authority and telemetry unproven")
    )
    record = {
        "schema_version": 1,
        "item": item,
        "allocation": "instrument_calibration",
        "phase": role,
        "role": role,
        "study_ordinal": study_ordinal,
        "wave_ordinal": wave_ordinal,
        "hypothesis_observation": False,
        "requested_model": model,
        "model_class": model_class,
        "resolved_model": resolved_model,
        "status": status,
        "failure_class": failure_class,
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_status": exit_status
        if exit_status is not None
        else ("not-started" if process is None else str(process.returncode)),
        "session_id": "unavailable",
        "tokens": tokens,
        "output_digest": output_digest,
        "snapshot": {
            "before_tool_boundary": canaries["root_nonce_digests"]["candidate"],
            "after_prompt_boundary": invocation["prompt_digest"],
            "after_controller_canary_boundary": canaries[
                "candidate_controller_write_digest"
            ],
            "after_worker_boundary": output_digest if process is not None else "unavailable",
            "after_hidden_grade_boundary": output_digest if process is not None else "unavailable",
        },
        "argv_policy": {
            "codex_cli_version": CODEX_CLI_VERSION,
            "argv": invocation["argv"],
            "sandbox": invocation["sandbox"],
            "tools": list(invocation["tools"]),
            "environment": list(invocation["environment"]),
            "network": invocation["network"],
            "web": invocation["web"],
            "mcp": invocation["mcp"],
            "delegation": invocation["delegation"],
            "approval_escalation": invocation["approval_escalation"],
            "apps": invocation["apps"],
            "plugins": invocation["plugins"],
            "multi_agent": invocation["multi_agent"],
            "stdin_prompt": invocation["stdin_prompt"],
            "effective_runtime_config": "unavailable-before-live-worker-canary",
            "effective_tool_roster": "unavailable-before-live-worker-canary",
            "effective_environment": "unavailable-before-live-worker-canary",
            "approval_policy": "unavailable-before-live-worker-canary",
        },
        "canaries": canaries,
        "live_canary": live_canary if live_canary is not None else "not-started",
        "terminal_reason": terminal_reason
        or (
            "calibration stopped before Codex launch because worker authority, "
            "model availability, and token telemetry could not be proven without "
            "the counted calibration canary itself"
        ),
    }
    if replacement_of is not None:
        record["replacement_of"] = replacement_of
    return record


def _crash_resume_canaries(item: str) -> dict[str, Any]:
    return {
        "candidate_controller_read_digest": "unavailable",
        "candidate_controller_write_digest": "unavailable",
        "prompt_digest": "unavailable",
        "root_nonce_digests": dict.fromkeys(SYNTHETIC_ROOT_NAMES, "unavailable"),
        "feature_disables": dict.fromkeys(DISABLED_CODEX_FEATURES, True),
        "config_strips_environment": True,
        "config_denies_approvals": True,
        "strict_config": True,
        "exact_candidate_root": True,
        "stdin_prompt": True,
        "controller_preflight_pass": False,
        "worker_proof": "unavailable",
        "local_listener_egress": "not-started-crash-resume",
        "live_script_digest": "not-written-crash-resume",
        "unproven_controls": [f"crash recovery for reserved item {item}"],
    }


def _terminal_record_path(run_dir: Path, slot_index: int, item: str) -> Path:
    slot_root, _roots = _calibration_slot_roots(run_dir, slot_index, item)
    return slot_root / "terminal.json"


def _validate_replayed_terminal_binding(
    *,
    record: dict[str, Any],
    reservation: dict[str, Any],
    run_dir: Path,
    slot_index: int,
    item: str,
    role: str,
    model_class: str,
    replacement_of: dict[str, Any] | None,
) -> None:
    """Bind a replayed terminal record to the current reservation and slot."""
    if record["item"] != item:
        raise SchemaError("terminal replay item does not match reservation")
    if record["study_ordinal"] != reservation["study_ordinal"]:
        raise SchemaError("terminal replay study ordinal does not match reservation")
    if record["wave_ordinal"] != reservation["wave_ordinal"]:
        raise SchemaError("terminal replay wave ordinal does not match reservation")
    if record["role"] != role or record["phase"] != role:
        raise SchemaError("terminal replay role does not match slot assignment")
    if record["model_class"] != model_class:
        raise SchemaError("terminal replay model class does not match slot assignment")
    if record["requested_model"] != MODEL_BY_CLASS[model_class]:
        raise SchemaError("terminal replay requested model does not match slot assignment")
    if replacement_of is None:
        if "replacement_of" in record:
            raise SchemaError("terminal replay has unexpected replacement link")
    elif record.get("replacement_of") != replacement_of:
        raise SchemaError("terminal replay replacement link does not match reservation")
    expected_candidate = (
        run_dir
        / "calibration"
        / f"{slot_index:02d}-{item}"
        / "candidate"
    ).resolve(strict=True)
    argv = record["argv_policy"]["argv"]
    for flag in ("--cd", "--add-dir"):
        if flag not in argv:
            raise SchemaError("terminal replay argv missing slot root")
        if Path(argv[argv.index(flag) + 1]).resolve(strict=True) != expected_candidate:
            raise SchemaError("terminal replay argv root does not match slot path")


def close_reserved_calibration_crash(
    *,
    ledger: InvocationLedger,
    run_dir: Path,
    slot_index: int,
    item: str,
    role: str,
    model_class: str,
    replacement_of: dict[str, Any] | None,
) -> dict[str, Any]:
    reservation = ledger.reservation_for_item(item)
    if reservation is None:
        raise InvocationLimitError("cannot close crash state without reservation")
    if ledger.is_terminal(item):
        terminal_path = _terminal_record_path(run_dir, slot_index, item)
        if not terminal_path.exists():
            raise InvocationLimitError("terminal ledger item lacks durable terminal record")
        loaded = load_disposable_json(run_dir, terminal_path)
        if not isinstance(loaded, dict):
            raise SchemaError("terminal record must be an object")
        _validate_calibration_record(loaded)
        _validate_replayed_terminal_binding(
            record=loaded,
            reservation=reservation,
            run_dir=run_dir,
            slot_index=slot_index,
            item=item,
            role=role,
            model_class=model_class,
            replacement_of=replacement_of,
        )
        return loaded
    slot_root, roots = prepare_calibration_slot_roots(run_dir, slot_index, item)
    candidate_root = roots["candidate"]
    invocation = {
        "item": item,
        "argv": [
            "codex",
            "exec",
            "--model",
            MODEL_BY_CLASS[model_class],
            "--sandbox",
            "workspace-write",
            "--cd",
            str(candidate_root),
            "--add-dir",
            str(candidate_root),
            "--json",
            "-",
        ],
        "sandbox": "workspace-write",
        "tools": ("shell",),
        "environment": ("TMPDIR", "PYTHONDONTWRITEBYTECODE"),
        "network": False,
        "web": False,
        "mcp": False,
        "delegation": False,
        "approval_escalation": False,
        "apps": False,
        "plugins": False,
        "multi_agent": False,
        "stdin_prompt": True,
        "prompt_digest": "unavailable",
    }
    started_at = time.time()
    live_canary = {
        "event_schema": "unavailable-after-crash",
        "output_digest": digest_text(
            f"unknown-started crash recovery for reserved calibration item {item}"
        ),
        "listener_observed": "unavailable-after-crash",
        "canary_result": "unavailable-after-crash",
        "tool_roster_proof": "unavailable-after-crash",
        "approval_policy_proof": "unavailable-after-crash",
    }
    record = _calibration_record(
        item=item,
        role=role,
        model_class=model_class,
        model=MODEL_BY_CLASS[model_class],
        study_ordinal=reservation["study_ordinal"],
        wave_ordinal=reservation["wave_ordinal"],
        invocation=invocation,
        canaries=_crash_resume_canaries(item),
        started_at=started_at,
        finished_at=started_at,
        replacement_of=replacement_of,
        live_canary=live_canary,
        status="failed",
        failure_class="crash-resume-unknown-started",
        exit_status="unknown-started",
        terminal_reason=(
            "reserved calibration item recovered after crash with no durable prelaunch "
            "proof; conservatively counted as an unknown-started model process"
        ),
    )
    write_json(slot_root / "terminal.json", record)
    ledger.terminal(item, status="failed", note=record["failure_class"])
    return record


def calibration_results_index(
    results: dict[str, Any],
    prior_index: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return the durable T3 evidence index without dropping T2 admission evidence."""
    admission_evidence = prior_index
    if isinstance(prior_index, dict) and prior_index.get("plan_task") == "T3":
        admission_evidence = prior_index.get("admission_evidence")
    calibration = {
        "status": results["status"],
        "allocation": "instrument_calibration",
        "calibration_slots": results["calibration_slots"],
        "replacement_reservations": results["replacement_reservations"],
        "terminal_slots": results["terminal_slots"],
        "failed_slots": results["failed_slots"],
        "instrument_loss_rate": results["instrument_loss_rate"],
        "inference_launch_permitted": results["inference_launch_permitted"],
        "inferential_processes_started": results["inferential_processes_started"],
        "model_processes_started": results["model_processes_started"],
        "records": [
            {
                "item": record["item"],
                "role": record["role"],
                "study_ordinal": record["study_ordinal"],
                "wave_ordinal": record["wave_ordinal"],
                "requested_model": record["requested_model"],
                "resolved_model": record["resolved_model"],
                "status": record["status"],
                "failure_class": record["failure_class"],
                "replacement_of": record.get("replacement_of"),
                "hypothesis_observation": record["hypothesis_observation"],
                "tokens": record["tokens"],
                "snapshot": record["snapshot"],
                "unproven_controls": record["canaries"]["unproven_controls"],
                "live_canary": record.get("live_canary"),
            }
            for record in results["records"]
        ],
    }
    return {
        "schema_version": 1,
        "plan_task": "T3",
        "status": "complete",
        "inference_branch": "bounded-case-study",
        "admission_evidence": admission_evidence,
        "calibration": calibration,
    }


def _calibration_payload(results: dict[str, Any]) -> dict[str, Any]:
    """Return the T3 calibration block from a T3 or later composite result."""
    if results.get("plan_task") == "T3":
        return results
    if results.get("plan_task") in {"T4", "T5", "T6"}:
        calibration = results.get("calibration")
        if not isinstance(calibration, dict):
            raise SchemaError("later results must embed calibration evidence")
        return calibration
    raise SchemaError("results do not contain calibration evidence")


def _admission_payload(index: dict[str, Any]) -> dict[str, Any]:
    """Return the T2 admission block from a T2/T3/T4 evidence index."""
    if index.get("plan_task") == "T2":
        return index
    admission = index.get("admission_evidence")
    if not isinstance(admission, dict):
        raise SchemaError("evidence index lacks admission evidence")
    return admission


def _derived_admission_summary(
    admission: dict[str, Any],
) -> tuple[dict[str, int], dict[str, int]]:
    records = admission["records"]
    status_counts: dict[str, int] = {}
    coverage_by_stratum: dict[str, int] = {}
    for record in records:
        if not isinstance(record, dict):
            raise SchemaError("admission record must be an object")
        status = _expect_text(record.get("status"), "admission record status")
        stratum = _expect_text(record.get("stratum"), "admission record stratum")
        status_counts[status] = status_counts.get(status, 0) + 1
        coverage_by_stratum[stratum] = coverage_by_stratum.get(stratum, 0) + 1
    return status_counts, coverage_by_stratum


def _validate_admission_summary(admission: dict[str, Any]) -> tuple[int, int]:
    _expect_keys(
        admission,
        {
            "schema_version",
            "plan_task",
            "status",
            "task_count",
            "status_counts",
            "coverage_by_stratum",
            "inference_branch",
            "model_processes_started",
            "records",
        },
        "admission evidence",
    )
    if admission["schema_version"] != 1 or admission["plan_task"] != "T2":
        raise SchemaError("unsupported admission evidence")
    if admission["status"] != "complete":
        raise SchemaError("admission evidence is not complete")
    task_count = _expect_positive_int(admission["task_count"], "task count")
    records = admission["records"]
    if not isinstance(records, list) or len(records) != task_count:
        raise SchemaError("admission record count mismatch")
    counts, coverage = admission["status_counts"], admission["coverage_by_stratum"]
    if not isinstance(counts, dict):
        raise SchemaError("admission status counts must be an object")
    if not isinstance(coverage, dict):
        raise SchemaError("admission coverage by stratum must be an object")
    derived_counts, derived_coverage = _derived_admission_summary(admission)
    if counts != derived_counts:
        raise SchemaError("admission status counts drift from records")
    if coverage != derived_coverage:
        raise SchemaError("admission coverage by stratum drifts from records")
    admitted = counts.get("admitted", 0)
    excluded = counts.get("excluded", 0)
    for label, value in (("admitted", admitted), ("excluded", excluded)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SchemaError(f"{label} count must be a non-negative integer")
    if admitted + excluded != task_count:
        raise SchemaError("admission status counts do not cover all tasks")
    if task_count != 12:
        raise SchemaError("admission evidence must cover the frozen 12-task frame")
    expected_branch = "inferential" if admitted == 12 else "bounded-case-study"
    if admission["inference_branch"] != expected_branch:
        raise SchemaError("admission inference branch drifts from records")
    if admission["model_processes_started"] != 0:
        raise SchemaError("admission must not start model processes")
    return task_count, admitted


def _blocked_core_by_task(admission: dict[str, Any], blocked_count: int) -> list[dict[str, Any]]:
    admitted = [
        _expect_text(record.get("task_id"), "admitted task id")
        for record in admission["records"]
        if isinstance(record, dict) and record.get("status") == "admitted"
    ]
    if not admitted:
        return []
    quotient, remainder = divmod(blocked_count, len(admitted))
    return [
        {
            "task_id": task_id,
            "blocked_would_be_reservations": quotient + (1 if index < remainder else 0),
        }
        for index, task_id in enumerate(admitted)
    ]


def build_w1_gate_memo(
    *,
    design: dict[str, Any],
    design_digest: str,
    calibration: dict[str, Any],
    admission: dict[str, Any],
    calibration_digest: str,
    evidence_index_digest: str,
) -> dict[str, Any]:
    """Build the deterministic W1 gate memo from frozen aggregate rules."""
    summary = validate_design(design)
    records = validate_calibration_results(calibration)
    task_count, admitted = _validate_admission_summary(admission)
    first_release = summary["fixed_releases"][0]
    if first_release["wave"] != "W1":
        raise SchemaError("first fixed release must be W1")
    telemetry_loss = float(calibration["instrument_loss_rate"])
    telemetry_threshold = 0.05
    required_tasks = 12
    first_unspent = calibration["terminal_slots"] + 1
    released_end = first_release["study_end"]
    blocked_count = max(0, released_end - first_unspent + 1)
    reasons = []
    if telemetry_loss > telemetry_threshold:
        reasons.append("telemetry/instrument loss exceeds 5%")
    if admitted < required_tasks:
        reasons.append("admitted task coverage is below 12")
    if calibration["inference_launch_permitted"] is not False:
        reasons.append("calibration did not refuse inference")
    if calibration["inferential_processes_started"] != 0:
        reasons.append("inferential process already started")
    if not reasons:
        reasons.append("no stop rule fired")
    gate_decision = "W2-unavailable" if reasons != ["no stop rule fired"] else "W2-released"
    memo = {
        "schema_version": 1,
        "plan_task": "T4",
        "gate": "W1",
        "status": "complete",
        "gate_decision": gate_decision,
        "release_w2": gate_decision == "W2-released",
        "no_inferential_success_claim": True,
        "inputs": {
            "design_digest": design_digest,
            "calibration_results_digest": calibration_digest,
            "evidence_index_digest": evidence_index_digest,
        },
        "thresholds": {
            "instrument_loss_stop_above": telemetry_threshold,
            "required_task_coverage": required_tasks,
        },
        "observed": {
            "terminal_calibration_reservations": len(records),
            "calibration_terminal_slots": calibration["terminal_slots"],
            "calibration_model_processes_started": calibration["model_processes_started"],
            "calibration_new_model_processes_started": calibration["new_model_processes_started"],
            "instrument_loss_rate": telemetry_loss,
            "task_count": task_count,
            "admitted_tasks": admitted,
            "excluded_tasks": task_count - admitted,
            "inference_launch_permitted": calibration["inference_launch_permitted"],
            "inferential_processes_started": calibration["inferential_processes_started"],
        },
        "w1_core": {
            "released_study_ordinals": [
                first_release["study_start"],
                first_release["study_end"],
            ],
            "spent_terminal_ordinals": calibration["terminal_slots"],
            "would_be_inferential_ordinals": [first_unspent, released_end]
            if blocked_count
            else [],
            "would_be_inferential_reservations": blocked_count,
            "reservation_policy": "blocked-without-reservation",
            "terminal_state": "unavailable",
            "blocked_by_task": _blocked_core_by_task(admission, blocked_count),
        },
        "w2": {
            "availability": "unavailable" if gate_decision != "W2-released" else "available",
            "release_memo_digest": "not-issued",
        },
        "process_accounting": {
            "t4_model_processes_started": 0,
            "t4_inferential_processes_started": 0,
            "t4_ordinals_reserved": 0,
        },
        "stop_reasons": reasons,
    }
    validate_w1_gate_memo(memo)
    return memo


def validate_w1_gate_memo(memo: dict[str, Any]) -> None:
    """Validate the strict W1 gate memo schema and frozen stop rules."""
    _check_bounds(memo)
    _expect_keys(
        memo,
        {
            "schema_version",
            "plan_task",
            "gate",
            "status",
            "gate_decision",
            "release_w2",
            "no_inferential_success_claim",
            "inputs",
            "thresholds",
            "observed",
            "w1_core",
            "w2",
            "process_accounting",
            "stop_reasons",
        },
        "W1 gate memo",
    )
    if memo["schema_version"] != 1 or memo["plan_task"] != "T4":
        raise SchemaError("unsupported W1 gate memo")
    if memo["gate"] != "W1" or memo["status"] != "complete":
        raise SchemaError("W1 gate memo is not complete")
    if memo["gate_decision"] not in {"W2-unavailable", "W2-released"}:
        raise SchemaError("unknown W1 gate decision")
    if memo["release_w2"] is not (memo["gate_decision"] == "W2-released"):
        raise SchemaError("W2 release flag disagrees with gate decision")
    if memo["no_inferential_success_claim"] is not True:
        raise SchemaError("W1 gate must not make an inferential success claim")
    _expect_keys(
        memo["inputs"],
        {"design_digest", "calibration_results_digest", "evidence_index_digest"},
        "W1 gate inputs",
    )
    for digest in memo["inputs"].values():
        _expect_digest(digest)
    _expect_keys(
        memo["thresholds"],
        {"instrument_loss_stop_above", "required_task_coverage"},
        "W1 gate thresholds",
    )
    if memo["thresholds"]["instrument_loss_stop_above"] != 0.05:
        raise SchemaError("W1 instrument-loss threshold changed")
    if memo["thresholds"]["required_task_coverage"] != 12:
        raise SchemaError("W1 task-coverage threshold changed")
    observed = memo["observed"]
    _expect_keys(
        observed,
        {
            "terminal_calibration_reservations",
            "calibration_terminal_slots",
            "calibration_model_processes_started",
            "calibration_new_model_processes_started",
            "instrument_loss_rate",
            "task_count",
            "admitted_tasks",
            "excluded_tasks",
            "inference_launch_permitted",
            "inferential_processes_started",
        },
        "W1 observed",
    )
    terminal = _expect_positive_int(
        observed["terminal_calibration_reservations"],
        "terminal calibration reservations",
    )
    if observed["calibration_terminal_slots"] != terminal:
        raise SchemaError("calibration terminal slot count changed")
    loss = observed["instrument_loss_rate"]
    if not isinstance(loss, (int, float)) or isinstance(loss, bool) or not math.isfinite(loss):
        raise SchemaError("W1 instrument loss must be finite")
    task_count = _expect_positive_int(observed["task_count"], "task count")
    admitted = observed["admitted_tasks"]
    excluded = observed["excluded_tasks"]
    if (
        isinstance(admitted, bool)
        or not isinstance(admitted, int)
        or admitted < 0
        or isinstance(excluded, bool)
        or not isinstance(excluded, int)
        or excluded < 0
        or admitted + excluded != task_count
    ):
        raise SchemaError("W1 task coverage counts are inconsistent")
    accounting = memo["process_accounting"]
    _expect_keys(
        accounting,
        {
            "t4_model_processes_started",
            "t4_inferential_processes_started",
            "t4_ordinals_reserved",
        },
        "W1 process accounting",
    )
    if any(accounting[key] != 0 for key in accounting):
        raise SchemaError("T4 must not start processes or reserve ordinals")
    core = memo["w1_core"]
    _expect_keys(
        core,
        {
            "released_study_ordinals",
            "spent_terminal_ordinals",
            "would_be_inferential_ordinals",
            "would_be_inferential_reservations",
            "reservation_policy",
            "terminal_state",
            "blocked_by_task",
        },
        "W1 core",
    )
    if core["reservation_policy"] != "blocked-without-reservation":
        raise SchemaError("W1 core must be blocked without reservation")
    if core["terminal_state"] != "unavailable":
        raise SchemaError("W1 core terminal state must be unavailable")
    blocked_count = core["would_be_inferential_reservations"]
    if isinstance(blocked_count, bool) or not isinstance(blocked_count, int) or blocked_count < 0:
        raise SchemaError("blocked W1 reservation count is invalid")
    if core["spent_terminal_ordinals"] != terminal:
        raise SchemaError("spent ordinals must equal terminal calibration slots")
    ordinals = core["released_study_ordinals"]
    if not isinstance(ordinals, list) or ordinals != [1, 80]:
        raise SchemaError("W1 released ordinal range changed")
    expected_blocked = 80 - terminal
    if blocked_count != expected_blocked:
        raise SchemaError("blocked W1 reservation count does not match unspent release")
    would_be = core["would_be_inferential_ordinals"]
    if blocked_count and would_be != [terminal + 1, 80]:
        raise SchemaError("blocked W1 ordinal range does not match unspent release")
    if not blocked_count and would_be != []:
        raise SchemaError("empty blocked range must be an empty list")
    blocked_by_task = core["blocked_by_task"]
    if not isinstance(blocked_by_task, list):
        raise SchemaError("blocked-by-task must be a list")
    blocked_by_task_total = sum(
        item.get("blocked_would_be_reservations", 0) for item in blocked_by_task
    )
    if blocked_by_task_total != blocked_count:
        raise SchemaError("blocked-by-task counts do not add up")
    stop_reasons = memo["stop_reasons"]
    if not isinstance(stop_reasons, list) or not stop_reasons:
        raise SchemaError("W1 gate needs at least one stop reason")
    if memo["gate_decision"] == "W2-unavailable":
        if memo["w2"] != {"availability": "unavailable", "release_memo_digest": "not-issued"}:
            raise SchemaError("W2 must remain unavailable without a release memo")
        if loss <= 0.05 and admitted >= 12:
            raise SchemaError("W2 cannot be unavailable without a frozen stop rule")
    else:
        if loss > 0.05 or admitted < 12:
            raise SchemaError("W2 cannot release when W1 stop rules fire")


def validate_w1_results(results: dict[str, Any]) -> dict[str, Any]:
    """Validate the T4 composite result while preserving embedded T3 evidence."""
    _check_bounds(results)
    _expect_keys(
        results,
        {
            "schema_version",
            "plan_task",
            "status",
            "inference_branch",
            "calibration",
            "w1_gate",
        },
        "W1 results",
    )
    if results["schema_version"] != 1 or results["plan_task"] != "T4":
        raise SchemaError("unsupported W1 results")
    if results["status"] != "complete":
        raise SchemaError("W1 results are not complete")
    if results["inference_branch"] != "bounded-case-study":
        raise SchemaError("W1 results must remain in bounded case-study branch")
    calibration = results["calibration"]
    if not isinstance(calibration, dict):
        raise SchemaError("W1 results calibration must be an object")
    validate_calibration_results(calibration)
    memo = results["w1_gate"]
    if not isinstance(memo, dict):
        raise SchemaError("W1 results gate must be an object")
    validate_w1_gate_memo(memo)
    return results


def w1_results_index(
    *,
    results: dict[str, Any],
    prior_index: dict[str, Any],
    memo_path: Path,
    wave_path: Path,
) -> dict[str, Any]:
    """Return the durable T4 evidence index without dropping T2/T3 evidence."""
    admission = _admission_payload(prior_index)
    calibration_index = prior_index.get("calibration")
    if not isinstance(calibration_index, dict):
        calibration_index = calibration_results_index(results["calibration"], admission)[
            "calibration"
        ]

    def label(path: Path) -> str:
        with suppress(ValueError):
            return str(path.relative_to(REPO_ROOT))
        return str(path)

    return {
        "schema_version": 1,
        "plan_task": "T4",
        "status": "complete",
        "inference_branch": "bounded-case-study",
        "admission_evidence": admission,
        "calibration": calibration_index,
        "w1_gate": {
            "status": "complete",
            "gate_decision": results["w1_gate"]["gate_decision"],
            "release_w2": results["w1_gate"]["release_w2"],
            "memo": label(memo_path),
            "wave_record": label(wave_path),
            "memo_digest": digest_file(memo_path),
            "blocked_would_be_inferential_reservations": results["w1_gate"]["w1_core"][
                "would_be_inferential_reservations"
            ],
            "t4_model_processes_started": 0,
            "t4_ordinals_reserved": 0,
            "stop_reasons": results["w1_gate"]["stop_reasons"],
        },
    }


def _t4_results_payload(results: dict[str, Any]) -> dict[str, Any]:
    """Return immutable T4 evidence from T4 results or a later T5 wrapper."""
    if results.get("plan_task") == "T4":
        validate_w1_results(results)
        return results
    if results.get("plan_task") == "T5":
        t4_results = results.get("t4_results")
        if not isinstance(t4_results, dict):
            raise SchemaError("T5 results must embed T4 evidence")
        validate_w1_results(t4_results)
        return t4_results
    if results.get("plan_task") == "T6":
        t5_results = results.get("t5_results")
        if not isinstance(t5_results, dict):
            raise SchemaError("T6 results must embed T5 evidence")
        return _t4_results_payload(t5_results)
    raise SchemaError("results do not contain T4 W1 evidence")


def _t4_index_payload(index: dict[str, Any]) -> dict[str, Any]:
    """Return immutable T4 evidence-index data from a T4 index or T5 wrapper."""
    if index.get("plan_task") == "T4":
        return validate_t4_evidence_index(index)
    if index.get("plan_task") == "T5":
        _expect_keys(
            index,
            {
                "schema_version",
                "plan_task",
                "status",
                "inference_branch",
                "t4_evidence_index",
                "admission_evidence",
                "calibration",
                "w1_gate",
                "w2_gate",
            },
            "T5 evidence index",
        )
        if (
            index["schema_version"] != 1
            or index["status"] != "complete"
            or index["inference_branch"] != "bounded-case-study"
        ):
            raise SchemaError("unsupported T5 evidence index")
        t4_index = index.get("t4_evidence_index")
        if not isinstance(t4_index, dict):
            raise SchemaError("T5 evidence index must embed T4 evidence")
        t4_index = validate_t4_evidence_index(t4_index)
        if index["admission_evidence"] != t4_index["admission_evidence"]:
            raise SchemaError("T5 admission evidence drifted from embedded T4 index")
        if index["calibration"] != t4_index["calibration"]:
            raise SchemaError("T5 calibration evidence drifted from embedded T4 index")
        if index["w1_gate"] != t4_index["w1_gate"]:
            raise SchemaError("T5 W1 evidence drifted from embedded T4 index")
        _validate_t5_w2_index(index["w2_gate"])
        return t4_index
    if index.get("plan_task") == "T6":
        t5_index = _t5_index_payload(index)
        return _t4_index_payload(t5_index)
    raise SchemaError("evidence index does not contain T4 W1 evidence")


def validate_calibration_evidence_index(calibration: dict[str, Any]) -> dict[str, Any]:
    """Validate the bounded T3 calibration evidence-index block."""
    _expect_keys(
        calibration,
        {
            "status",
            "allocation",
            "calibration_slots",
            "replacement_reservations",
            "terminal_slots",
            "failed_slots",
            "instrument_loss_rate",
            "inference_launch_permitted",
            "inferential_processes_started",
            "model_processes_started",
            "records",
        },
        "calibration evidence",
    )
    if (
        calibration["status"] != "complete"
        or calibration["allocation"] != "instrument_calibration"
    ):
        raise SchemaError("unsupported calibration evidence")
    terminal_slots = _expect_positive_int(calibration["terminal_slots"], "terminal slots")
    for key in (
        "calibration_slots",
        "replacement_reservations",
        "failed_slots",
        "model_processes_started",
    ):
        value = calibration[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SchemaError(f"{key} must be a non-negative integer")
    if calibration["inferential_processes_started"] != 0:
        raise SchemaError("calibration evidence cannot include inferential starts")
    if calibration["inference_launch_permitted"] is not False:
        raise SchemaError("calibration evidence must refuse inference")
    loss = calibration["instrument_loss_rate"]
    if not isinstance(loss, (int, float)) or isinstance(loss, bool) or not math.isfinite(loss):
        raise SchemaError("calibration evidence loss rate must be finite")
    records = calibration["records"]
    if not isinstance(records, list) or len(records) != terminal_slots:
        raise SchemaError("calibration evidence record count mismatch")
    for record in records:
        if not isinstance(record, dict):
            raise SchemaError("calibration evidence record must be an object")
        _expect_keys(
            record,
            {
                "item",
                "role",
                "study_ordinal",
                "wave_ordinal",
                "requested_model",
                "resolved_model",
                "status",
                "failure_class",
                "replacement_of",
                "hypothesis_observation",
                "tokens",
                "snapshot",
                "unproven_controls",
                "live_canary",
            },
            "calibration evidence record",
        )
        _expect_text(record["item"], "calibration item")
        _expect_positive_int(record["study_ordinal"], "study ordinal")
        _expect_positive_int(record["wave_ordinal"], "wave ordinal")
    return calibration


def validate_t4_w1_index(w1_gate: dict[str, Any]) -> dict[str, Any]:
    """Validate the bounded W1 evidence-index block."""
    _expect_keys(
        w1_gate,
        {
            "status",
            "gate_decision",
            "release_w2",
            "memo",
            "wave_record",
            "memo_digest",
            "blocked_would_be_inferential_reservations",
            "t4_model_processes_started",
            "t4_ordinals_reserved",
            "stop_reasons",
        },
        "W1 evidence index",
    )
    if w1_gate["status"] != "complete":
        raise SchemaError("W1 evidence index must be complete")
    if w1_gate["gate_decision"] not in {"W2-unavailable", "W2-released"}:
        raise SchemaError("unsupported W1 evidence gate decision")
    if w1_gate["release_w2"] is not (w1_gate["gate_decision"] == "W2-released"):
        raise SchemaError("W1 evidence release flag drifted")
    _expect_text(w1_gate["memo"], "W1 memo path")
    _expect_text(w1_gate["wave_record"], "W1 wave path")
    _expect_sha256_digest(w1_gate["memo_digest"])
    if (
        w1_gate["t4_model_processes_started"] != 0
        or w1_gate["t4_ordinals_reserved"] != 0
    ):
        raise SchemaError("W1 evidence must not record T4 starts or reservations")
    blocked = w1_gate["blocked_would_be_inferential_reservations"]
    if isinstance(blocked, bool) or not isinstance(blocked, int) or blocked < 0:
        raise SchemaError("W1 blocked reservation count is invalid")
    if not isinstance(w1_gate["stop_reasons"], list) or not w1_gate["stop_reasons"]:
        raise SchemaError("W1 evidence requires stop reasons")
    return w1_gate


def validate_t4_evidence_index(index: dict[str, Any]) -> dict[str, Any]:
    """Validate the full T4 evidence index before T5 preserves or digests it."""
    _expect_keys(
        index,
        {
            "schema_version",
            "plan_task",
            "status",
            "inference_branch",
            "admission_evidence",
            "calibration",
            "w1_gate",
        },
        "T4 evidence index",
    )
    if (
        index["schema_version"] != 1
        or index["plan_task"] != "T4"
        or index["status"] != "complete"
        or index["inference_branch"] != "bounded-case-study"
    ):
        raise SchemaError("unsupported T4 evidence index")
    admission = index["admission_evidence"]
    calibration = index["calibration"]
    w1_gate = index["w1_gate"]
    if not isinstance(admission, dict):
        raise SchemaError("T4 evidence admission must be an object")
    if not isinstance(calibration, dict):
        raise SchemaError("T4 evidence calibration must be an object")
    if not isinstance(w1_gate, dict):
        raise SchemaError("T4 evidence W1 gate must be an object")
    _validate_admission_summary(admission)
    validate_calibration_evidence_index(calibration)
    validate_t4_w1_index(w1_gate)
    return index


def _validate_t5_w2_index(w2_gate: Any) -> dict[str, Any]:
    if not isinstance(w2_gate, dict):
        raise SchemaError("T5 evidence W2 gate must be an object")
    _expect_keys(
        w2_gate,
        {
            "status",
            "gate_decision",
            "release_w3_fixed",
            "release_reserve",
            "reserve_item_ids",
            "memo",
            "memo_digest",
            "analysis_inputs",
            "t5_model_processes_started",
            "t5_ordinals_reserved",
            "stop_reasons",
        },
        "W2 evidence index",
    )
    if w2_gate["status"] != "complete" or w2_gate["gate_decision"] != "stopped-before-core":
        raise SchemaError("unsupported W2 evidence index")
    if w2_gate["release_w3_fixed"] is not False or w2_gate["release_reserve"] is not False:
        raise SchemaError("W2 evidence must not release W3 or reserve")
    if w2_gate["reserve_item_ids"] != []:
        raise SchemaError("W2 evidence must release zero reserve IDs")
    _expect_text(w2_gate["memo"], "W2 memo path")
    _expect_sha256_digest(w2_gate["memo_digest"])
    if (
        w2_gate["t5_model_processes_started"] != 0
        or w2_gate["t5_ordinals_reserved"] != 0
    ):
        raise SchemaError("W2 evidence must not record T5 starts or reservations")
    if not isinstance(w2_gate["analysis_inputs"], dict):
        raise SchemaError("W2 evidence analysis inputs must be an object")
    if not isinstance(w2_gate["stop_reasons"], list) or not w2_gate["stop_reasons"]:
        raise SchemaError("W2 evidence requires stop reasons")
    return w2_gate


def validate_w1_chain(
    *,
    design_digest: str,
    wave_path: Path,
    memo_path: Path,
    t4_results: dict[str, Any],
    t4_index: dict[str, Any],
) -> dict[str, str]:
    """Validate and digest the exact W1 design, memo, results, and index chain."""
    if digest_file(wave_path) != design_digest:
        raise SchemaError("frozen W1 wave design does not match gate design")
    w1_memo = load_json(memo_path)
    if not isinstance(w1_memo, dict):
        raise SchemaError("W1 gate memo must be an object")
    validate_w1_gate_memo(w1_memo)
    if t4_results.get("w1_gate") != w1_memo:
        raise SchemaError("durable T4 results drift from W1 memo")
    w1_index = t4_index.get("w1_gate")
    if not isinstance(w1_index, dict):
        raise SchemaError("T4 evidence index lacks W1 gate evidence")
    memo_digest = digest_file(memo_path)
    if w1_index.get("memo_digest") != memo_digest:
        raise SchemaError("T4 evidence index W1 memo digest drifted")
    if w1_index.get("release_w2") is not w1_memo["release_w2"]:
        raise SchemaError("T4 evidence index W2 release drifted")
    if w1_memo["inputs"]["design_digest"] != design_digest:
        raise SchemaError("W1 memo design digest does not match frozen design")
    if w1_memo["release_w2"] is not False:
        raise SchemaError("truthful T5 stopped branch requires W2 unavailable")
    return {
        "design_digest": design_digest,
        "w1_gate_memo_digest": memo_digest,
        "t4_results_digest": digest_text(json.dumps(t4_results, sort_keys=True)),
        "t4_evidence_index_digest": digest_text(json.dumps(t4_index, sort_keys=True)),
    }


def build_w2_gate_memo(
    *,
    design: dict[str, Any],
    chain_digests: dict[str, str],
    w1_memo: dict[str, Any],
) -> dict[str, Any]:
    """Build the deterministic T5 W2 allocation memo for the stopped branch."""
    summary = validate_design(design)
    releases = summary["fixed_releases"]
    w2_release = releases[1]
    w3_release = releases[2]
    reserve = summary["reserve_release"]
    if w2_release["wave"] != "W2" or w3_release["wave"] != "W3":
        raise SchemaError("fixed releases changed")
    if w1_memo["release_w2"] is not False:
        raise SchemaError("W2 gate cannot run stopped branch when W2 is released")
    stop_reasons = [
        "W1 gate left W2 unavailable",
        "instrument calibration loss was above the W1 threshold",
        "admitted task coverage was below the 12-task inference threshold",
    ]
    unavailable_reason = (
        "W1 gate did not release W2, so no core inferential slots were legal to "
        "reserve or launch before the W2 decision gate."
    )
    memo = {
        "schema_version": 1,
        "plan_task": "T5",
        "gate": "W2",
        "status": "complete",
        "gate_decision": "stopped-before-core",
        "release_w3_fixed": False,
        "release_reserve": False,
        "reserve_item_ids": [],
        "no_inferential_success_claim": True,
        "inputs": {
            "design_digest": chain_digests["design_digest"],
            "w1_gate_memo_digest": chain_digests["w1_gate_memo_digest"],
            "t4_results_digest": chain_digests["t4_results_digest"],
            "t4_evidence_index_digest": chain_digests["t4_evidence_index_digest"],
        },
        "observed": {
            "w1_gate_decision": w1_memo["gate_decision"],
            "w2_released_by_w1": w1_memo["release_w2"],
            "w2_core_slots_terminal": 0,
            "legal_core_slots_completed": 0,
            "builder_self_audits_captured": 0,
            "harm_checks_available": False,
            "futility_checks_available": False,
            "task_coverage_checks_available": False,
            "censoring_checks_available": False,
            "token_checks_available": False,
            "predictive_resolution_checks_available": False,
        },
        "w2_core": {
            "unavailable_study_ordinals": [
                w2_release["study_start"],
                w2_release["study_end"],
            ],
            "terminal_state": "unavailable",
            "reservation_policy": "blocked-without-reservation",
            "ordinals_reserved_in_t5": 0,
            "model_processes_started_in_t5": 0,
            "inferential_processes_started_in_t5": 0,
        },
        "w3_fixed": {
            "unavailable_study_ordinals": [
                w3_release["study_start"],
                w3_release["study_end"],
            ],
            "availability": "unavailable",
            "release_memo_digest": "not-issued",
        },
        "adaptive_reserve": {
            "unavailable_study_ordinals": [
                reserve["study_start"],
                reserve["study_end"],
            ],
            "availability": "unavailable",
            "released_item_ids": [],
            "released_contiguous_prefix": 0,
        },
        "analysis_inputs": {
            hypothesis: {
                "status": "unavailable",
                "reason": unavailable_reason,
            }
            for hypothesis in CORE_DIRECT_HYPOTHESES
        },
        "process_accounting": {
            "t5_model_processes_started": 0,
            "t5_inferential_processes_started": 0,
            "t5_ordinals_reserved": 0,
        },
        "stop_reasons": stop_reasons,
    }
    validate_w2_gate_memo(memo)
    return memo


def validate_w2_gate_memo(memo: dict[str, Any]) -> None:
    """Validate the strict W2 stopped-branch allocation memo."""
    _check_bounds(memo)
    _expect_keys(
        memo,
        {
            "schema_version",
            "plan_task",
            "gate",
            "status",
            "gate_decision",
            "release_w3_fixed",
            "release_reserve",
            "reserve_item_ids",
            "no_inferential_success_claim",
            "inputs",
            "observed",
            "w2_core",
            "w3_fixed",
            "adaptive_reserve",
            "analysis_inputs",
            "process_accounting",
            "stop_reasons",
        },
        "W2 gate memo",
    )
    if memo["schema_version"] != 1 or memo["plan_task"] != "T5":
        raise SchemaError("unsupported W2 gate memo")
    if memo["gate"] != "W2" or memo["status"] != "complete":
        raise SchemaError("W2 gate memo is not complete")
    if memo["gate_decision"] != "stopped-before-core":
        raise SchemaError("W2 stopped branch decision changed")
    if memo["release_w3_fixed"] is not False or memo["release_reserve"] is not False:
        raise SchemaError("T5 stopped branch cannot release W3 work")
    if memo["reserve_item_ids"] != []:
        raise SchemaError("T5 stopped branch must release zero reserve item IDs")
    if memo["no_inferential_success_claim"] is not True:
        raise SchemaError("T5 stopped branch must not make inferential claims")
    _expect_keys(
        memo["inputs"],
        {
            "design_digest",
            "w1_gate_memo_digest",
            "t4_results_digest",
            "t4_evidence_index_digest",
        },
        "W2 gate inputs",
    )
    for digest in memo["inputs"].values():
        _expect_digest(digest)
    observed = memo["observed"]
    _expect_keys(
        observed,
        {
            "w1_gate_decision",
            "w2_released_by_w1",
            "w2_core_slots_terminal",
            "legal_core_slots_completed",
            "builder_self_audits_captured",
            "harm_checks_available",
            "futility_checks_available",
            "task_coverage_checks_available",
            "censoring_checks_available",
            "token_checks_available",
            "predictive_resolution_checks_available",
        },
        "W2 observed",
    )
    if (
        observed["w1_gate_decision"] != "W2-unavailable"
        or observed["w2_released_by_w1"] is not False
    ):
        raise SchemaError("W2 stopped branch must be bound to W1 unavailability")
    for key in (
        "w2_core_slots_terminal",
        "legal_core_slots_completed",
        "builder_self_audits_captured",
    ):
        if observed[key] != 0:
            raise SchemaError("T5 stopped branch must have zero core observations")
    for key in (
        "harm_checks_available",
        "futility_checks_available",
        "task_coverage_checks_available",
        "censoring_checks_available",
        "token_checks_available",
        "predictive_resolution_checks_available",
    ):
        if observed[key] is not False:
            raise SchemaError("T5 stopped branch cannot mark W2 checks available")
    core = memo["w2_core"]
    _expect_keys(
        core,
        {
            "unavailable_study_ordinals",
            "terminal_state",
            "reservation_policy",
            "ordinals_reserved_in_t5",
            "model_processes_started_in_t5",
            "inferential_processes_started_in_t5",
        },
        "W2 core",
    )
    if core["unavailable_study_ordinals"] != [81, 160]:
        raise SchemaError("W2 ordinal range changed")
    if core["terminal_state"] != "unavailable":
        raise SchemaError("W2 core must remain unavailable")
    if core["reservation_policy"] != "blocked-without-reservation":
        raise SchemaError("W2 core must be blocked without reservation")
    if (
        core["ordinals_reserved_in_t5"] != 0
        or core["model_processes_started_in_t5"] != 0
        or core["inferential_processes_started_in_t5"] != 0
    ):
        raise SchemaError("T5 must not reserve ordinals or start processes")
    if memo["w3_fixed"] != {
        "unavailable_study_ordinals": [161, 216],
        "availability": "unavailable",
        "release_memo_digest": "not-issued",
    }:
        raise SchemaError("W3 fixed work must remain unavailable")
    if memo["adaptive_reserve"] != {
        "unavailable_study_ordinals": [217, 240],
        "availability": "unavailable",
        "released_item_ids": [],
        "released_contiguous_prefix": 0,
    }:
        raise SchemaError("adaptive reserve must release zero items")
    accounting = memo["process_accounting"]
    _expect_keys(
        accounting,
        {
            "t5_model_processes_started",
            "t5_inferential_processes_started",
            "t5_ordinals_reserved",
        },
        "W2 process accounting",
    )
    if any(accounting[key] != 0 for key in accounting):
        raise SchemaError("T5 process accounting must stay zero")
    analysis_inputs = memo["analysis_inputs"]
    if (
        not isinstance(analysis_inputs, dict)
        or set(analysis_inputs) != set(CORE_DIRECT_HYPOTHESES)
    ):
        raise SchemaError("T5 analysis inputs must cover the frozen core hypotheses")
    for hypothesis, entry in analysis_inputs.items():
        if not isinstance(entry, dict):
            raise SchemaError(f"{hypothesis} analysis input must be an object")
        _expect_keys(entry, {"status", "reason"}, f"{hypothesis} analysis input")
        if entry["status"] != "unavailable":
            raise SchemaError(f"{hypothesis} analysis input must be unavailable")
        _expect_text(entry["reason"], f"{hypothesis} unavailable reason")
    stop_reasons = memo["stop_reasons"]
    if not isinstance(stop_reasons, list) or not stop_reasons:
        raise SchemaError("W2 gate needs at least one stop reason")


def validate_t5_results(results: dict[str, Any]) -> dict[str, Any]:
    """Validate T5 composite results while preserving embedded T4 evidence."""
    _check_bounds(results)
    _expect_keys(
        results,
        {
            "schema_version",
            "plan_task",
            "status",
            "inference_branch",
            "t4_results",
            "calibration",
            "w1_gate",
            "w2_gate",
        },
        "T5 results",
    )
    if results["schema_version"] != 1 or results["plan_task"] != "T5":
        raise SchemaError("unsupported T5 results")
    if results["status"] != "complete" or results["inference_branch"] != "bounded-case-study":
        raise SchemaError("T5 results must be complete bounded-case-study evidence")
    t4_results = results["t4_results"]
    if not isinstance(t4_results, dict):
        raise SchemaError("T5 results T4 evidence must be an object")
    validate_w1_results(t4_results)
    if results["calibration"] != t4_results["calibration"]:
        raise SchemaError("T5 calibration evidence drifted from T4")
    if results["w1_gate"] != t4_results["w1_gate"]:
        raise SchemaError("T5 W1 evidence drifted from T4")
    memo = results["w2_gate"]
    if not isinstance(memo, dict):
        raise SchemaError("T5 results W2 gate must be an object")
    validate_w2_gate_memo(memo)
    return results


def w2_results_index(
    *,
    results: dict[str, Any],
    t4_index: dict[str, Any],
    memo_path: Path,
) -> dict[str, Any]:
    """Return durable T5 evidence without dropping earlier evidence."""
    validate_t5_results(results)

    def label(path: Path) -> str:
        with suppress(ValueError):
            return str(path.relative_to(REPO_ROOT))
        return str(path)

    return {
        "schema_version": 1,
        "plan_task": "T5",
        "status": "complete",
        "inference_branch": "bounded-case-study",
        "t4_evidence_index": t4_index,
        "admission_evidence": _admission_payload(t4_index),
        "calibration": t4_index["calibration"],
        "w1_gate": t4_index["w1_gate"],
        "w2_gate": {
            "status": "complete",
            "gate_decision": results["w2_gate"]["gate_decision"],
            "release_w3_fixed": results["w2_gate"]["release_w3_fixed"],
            "release_reserve": results["w2_gate"]["release_reserve"],
            "reserve_item_ids": results["w2_gate"]["reserve_item_ids"],
            "memo": label(memo_path),
            "memo_digest": digest_file(memo_path),
            "analysis_inputs": results["w2_gate"]["analysis_inputs"],
            "t5_model_processes_started": 0,
            "t5_ordinals_reserved": 0,
            "stop_reasons": results["w2_gate"]["stop_reasons"],
        },
    }


def _t5_results_payload(results: dict[str, Any]) -> dict[str, Any]:
    """Return immutable T5 evidence from T5 results or a later T6 wrapper."""
    if results.get("plan_task") == "T5":
        validate_t5_results(results)
        return results
    if results.get("plan_task") == "T6":
        t5_results = results.get("t5_results")
        if not isinstance(t5_results, dict):
            raise SchemaError("T6 results must embed T5 evidence")
        validate_t5_results(t5_results)
        return t5_results
    raise SchemaError("results do not contain T5 W2 evidence")


def _t5_index_payload(index: dict[str, Any]) -> dict[str, Any]:
    """Return immutable T5 evidence-index data from T5 or T6 wrappers."""
    if index.get("plan_task") == "T5":
        _t4_index_payload(index)
        return index
    if index.get("plan_task") == "T6":
        _expect_keys(
            index,
            {
                "schema_version",
                "plan_task",
                "status",
                "inference_branch",
                "t5_evidence_index",
                "t4_evidence_index",
                "admission_evidence",
                "calibration",
                "w1_gate",
                "w2_gate",
                "t6_review",
            },
            "T6 evidence index",
        )
        if (
            index["schema_version"] != 1
            or index["status"] != "complete"
            or index["inference_branch"] != "bounded-case-study"
        ):
            raise SchemaError("unsupported T6 evidence index")
        t5_index = index["t5_evidence_index"]
        if not isinstance(t5_index, dict):
            raise SchemaError("T6 evidence index must embed T5 evidence")
        _t4_index_payload(t5_index)
        if index["t4_evidence_index"] != t5_index["t4_evidence_index"]:
            raise SchemaError("T6 T4 evidence drifted from embedded T5 index")
        if index["admission_evidence"] != t5_index["admission_evidence"]:
            raise SchemaError("T6 admission evidence drifted from embedded T5 index")
        if index["calibration"] != t5_index["calibration"]:
            raise SchemaError("T6 calibration evidence drifted from embedded T5 index")
        if index["w1_gate"] != t5_index["w1_gate"]:
            raise SchemaError("T6 W1 evidence drifted from embedded T5 index")
        if index["w2_gate"] != t5_index["w2_gate"]:
            raise SchemaError("T6 W2 evidence drifted from embedded T5 index")
        _validate_t6_review_index(index["t6_review"])
        return t5_index
    raise SchemaError("evidence index does not contain T5 W2 evidence")


def validate_t5_chain(
    *,
    design_digest: str,
    wave_path: Path,
    memo_path: Path,
    t5_results: dict[str, Any],
    t5_index: dict[str, Any],
) -> dict[str, str]:
    """Validate and digest the exact T5 design, memo, results, and index chain."""
    if digest_file(wave_path) != design_digest:
        raise SchemaError("frozen W1 wave design does not match review design")
    w2_memo = load_json(memo_path)
    if not isinstance(w2_memo, dict):
        raise SchemaError("W2 gate memo must be an object")
    validate_w2_gate_memo(w2_memo)
    if t5_results.get("w2_gate") != w2_memo:
        raise SchemaError("durable T5 results drift from W2 memo")
    w2_index = t5_index.get("w2_gate")
    if not isinstance(w2_index, dict):
        raise SchemaError("T5 evidence index lacks W2 gate evidence")
    memo_digest = digest_file(memo_path)
    if w2_index.get("memo_digest") != memo_digest:
        raise SchemaError("T5 evidence index W2 memo digest drifted")
    if w2_memo["release_w3_fixed"] is not False or w2_memo["release_reserve"] is not False:
        raise SchemaError("truthful T6 stopped branch requires unavailable W3 and reserve")
    return {
        "design_digest": design_digest,
        "w2_gate_memo_digest": memo_digest,
        "t5_results_digest": digest_text(json.dumps(t5_results, sort_keys=True)),
        "t5_evidence_index_digest": digest_text(json.dumps(t5_index, sort_keys=True)),
    }


def build_t6_review_memo(
    *,
    design: dict[str, Any],
    chain_digests: dict[str, str],
    w2_memo: dict[str, Any],
) -> dict[str, Any]:
    """Build the deterministic T6 unavailable review-allocation memo."""
    summary = validate_design(design)
    review_capacity = summary["allocations"]["independent_review"]
    unavailable_reason = (
        "T5 stopped before any legal core builder output, so no unchanged blinded "
        "subject or builder self-audit existed for review assignment."
    )
    unavailable_measure = {
        "status": "unavailable",
        "reason": unavailable_reason,
    }
    memo = {
        "schema_version": 1,
        "plan_task": "T6",
        "gate": "review-allocation",
        "status": "complete",
        "review_decision": "unavailable-before-subject-selection",
        "no_review_performance_claim": True,
        "inputs": {
            "design_digest": chain_digests["design_digest"],
            "w2_gate_memo_digest": chain_digests["w2_gate_memo_digest"],
            "t5_results_digest": chain_digests["t5_results_digest"],
            "t5_evidence_index_digest": chain_digests["t5_evidence_index_digest"],
        },
        "review_allocation": {
            "capacity_processes": review_capacity,
            "availability": "unavailable",
            "release_flag": False,
            "reservation_policy": "blocked-without-reservation",
        },
        "observed": {
            "w2_gate_decision": w2_memo["gate_decision"],
            "w3_fixed_available": w2_memo["release_w3_fixed"],
            "reserve_available": w2_memo["release_reserve"],
            "eligible_subjects": 0,
            "builder_self_audits_available": 0,
            "review_processes_started": 0,
            "review_ordinals_reserved": 0,
            "review_terminal_slots": 0,
            "unique_sustained_findings": dict(unavailable_measure),
            "duplicate_findings": dict(unavailable_measure),
            "refuted_findings": dict(unavailable_measure),
            "indeterminate_findings": dict(unavailable_measure),
            "reviewer_churn_items": dict(unavailable_measure),
            "reviewer_churn_tokens": dict(unavailable_measure),
        },
        "unavailable_inputs": {
            "subjects": unavailable_reason,
            "self_audits": unavailable_reason,
            "reviews": unavailable_reason,
            "findings": unavailable_reason,
            "churn": unavailable_reason,
        },
        "analysis_inputs": {
            hypothesis: {
                "status": "unavailable",
                "reason": unavailable_reason,
            }
            for hypothesis in REVIEW_HYPOTHESES
        },
        "process_accounting": {
            "t6_model_processes_started": 0,
            "t6_review_processes_started": 0,
            "t6_ordinals_reserved": 0,
        },
        "stop_reasons": [
            "T5 stopped before legal core builder outputs existed",
            "no blinded review subjects were eligible",
            "no builder self-audits were available for H7 comparison",
        ],
    }
    validate_t6_review_memo(memo)
    return memo


def validate_t6_review_memo(memo: dict[str, Any]) -> None:
    """Validate the strict T6 unavailable review-allocation memo."""
    _check_bounds(memo)
    _expect_keys(
        memo,
        {
            "schema_version",
            "plan_task",
            "gate",
            "status",
            "review_decision",
            "no_review_performance_claim",
            "inputs",
            "review_allocation",
            "observed",
            "unavailable_inputs",
            "analysis_inputs",
            "process_accounting",
            "stop_reasons",
        },
        "T6 review memo",
    )
    if memo["schema_version"] != 1 or memo["plan_task"] != "T6":
        raise SchemaError("unsupported T6 review memo")
    if memo["gate"] != "review-allocation" or memo["status"] != "complete":
        raise SchemaError("T6 review memo is not complete")
    if memo["review_decision"] != "unavailable-before-subject-selection":
        raise SchemaError("T6 review decision changed")
    if memo["no_review_performance_claim"] is not True:
        raise SchemaError("T6 must not make a review performance claim")
    _expect_keys(
        memo["inputs"],
        {
            "design_digest",
            "w2_gate_memo_digest",
            "t5_results_digest",
            "t5_evidence_index_digest",
        },
        "T6 inputs",
    )
    for digest in memo["inputs"].values():
        _expect_sha256_digest(digest)
    allocation = memo["review_allocation"]
    _expect_keys(
        allocation,
        {"capacity_processes", "availability", "release_flag", "reservation_policy"},
        "T6 review allocation",
    )
    if allocation["capacity_processes"] != 36:
        raise SchemaError("T6 review capacity changed")
    if allocation["availability"] != "unavailable" or allocation["release_flag"] is not False:
        raise SchemaError("T6 review allocation must remain unavailable")
    if allocation["reservation_policy"] != "blocked-without-reservation":
        raise SchemaError("T6 review reservation policy changed")
    observed = memo["observed"]
    _expect_keys(
        observed,
        {
            "w2_gate_decision",
            "w3_fixed_available",
            "reserve_available",
            "eligible_subjects",
            "builder_self_audits_available",
            "review_processes_started",
            "review_ordinals_reserved",
            "review_terminal_slots",
            "unique_sustained_findings",
            "duplicate_findings",
            "refuted_findings",
            "indeterminate_findings",
            "reviewer_churn_items",
            "reviewer_churn_tokens",
        },
        "T6 observed",
    )
    if (
        observed["w2_gate_decision"] != "stopped-before-core"
        or observed["w3_fixed_available"] is not False
        or observed["reserve_available"] is not False
    ):
        raise SchemaError("T6 review memo must be bound to stopped T5 evidence")
    for key in (
        "eligible_subjects",
        "builder_self_audits_available",
        "review_processes_started",
        "review_ordinals_reserved",
        "review_terminal_slots",
    ):
        if observed[key] != 0:
            raise SchemaError("T6 unavailable branch must keep review counts at zero")
    for key in (
        "unique_sustained_findings",
        "duplicate_findings",
        "refuted_findings",
        "indeterminate_findings",
        "reviewer_churn_items",
        "reviewer_churn_tokens",
    ):
        value = observed[key]
        if not isinstance(value, dict):
            raise SchemaError(f"{key} must be an unavailable measure")
        _expect_keys(value, {"status", "reason"}, f"{key} unavailable measure")
        if value["status"] != "unavailable":
            raise SchemaError(f"{key} must be unavailable")
        _expect_text(value["reason"], f"{key} unavailable reason")
    unavailable_inputs = memo["unavailable_inputs"]
    if not isinstance(unavailable_inputs, dict) or set(unavailable_inputs) != {
        "subjects",
        "self_audits",
        "reviews",
        "findings",
        "churn",
    }:
        raise SchemaError("T6 unavailable inputs changed")
    for reason in unavailable_inputs.values():
        _expect_text(reason, "T6 unavailable reason")
    analysis_inputs = memo["analysis_inputs"]
    if (
        not isinstance(analysis_inputs, dict)
        or set(analysis_inputs) != set(REVIEW_HYPOTHESES)
    ):
        raise SchemaError("T6 analysis inputs must cover review hypotheses")
    for hypothesis, entry in analysis_inputs.items():
        if not isinstance(entry, dict):
            raise SchemaError(f"{hypothesis} review input must be an object")
        _expect_keys(entry, {"status", "reason"}, f"{hypothesis} review input")
        if entry["status"] != "unavailable":
            raise SchemaError(f"{hypothesis} review input must be unavailable")
        _expect_text(entry["reason"], f"{hypothesis} unavailable reason")
    accounting = memo["process_accounting"]
    _expect_keys(
        accounting,
        {
            "t6_model_processes_started",
            "t6_review_processes_started",
            "t6_ordinals_reserved",
        },
        "T6 process accounting",
    )
    if any(accounting[key] != 0 for key in accounting):
        raise SchemaError("T6 process accounting must stay zero")
    if not isinstance(memo["stop_reasons"], list) or not memo["stop_reasons"]:
        raise SchemaError("T6 review memo requires stop reasons")


def validate_t6_results(results: dict[str, Any]) -> dict[str, Any]:
    """Validate T6 composite results while preserving embedded T5 evidence."""
    _check_bounds(results)
    _expect_keys(
        results,
        {
            "schema_version",
            "plan_task",
            "status",
            "inference_branch",
            "t5_results",
            "t4_results",
            "calibration",
            "w1_gate",
            "w2_gate",
            "t6_review",
        },
        "T6 results",
    )
    if results["schema_version"] != 1 or results["plan_task"] != "T6":
        raise SchemaError("unsupported T6 results")
    if results["status"] != "complete" or results["inference_branch"] != "bounded-case-study":
        raise SchemaError("T6 results must be complete bounded-case-study evidence")
    t5_results = results["t5_results"]
    if not isinstance(t5_results, dict):
        raise SchemaError("T6 results T5 evidence must be an object")
    validate_t5_results(t5_results)
    if results["t4_results"] != t5_results["t4_results"]:
        raise SchemaError("T6 T4 evidence drifted from T5")
    if results["calibration"] != t5_results["calibration"]:
        raise SchemaError("T6 calibration evidence drifted from T5")
    if results["w1_gate"] != t5_results["w1_gate"]:
        raise SchemaError("T6 W1 evidence drifted from T5")
    if results["w2_gate"] != t5_results["w2_gate"]:
        raise SchemaError("T6 W2 evidence drifted from T5")
    memo = results["t6_review"]
    if not isinstance(memo, dict):
        raise SchemaError("T6 review evidence must be an object")
    validate_t6_review_memo(memo)
    return results


def _validate_t6_review_index(t6_review: Any) -> dict[str, Any]:
    if not isinstance(t6_review, dict):
        raise SchemaError("T6 review index must be an object")
    _expect_keys(
        t6_review,
        {
            "status",
            "review_decision",
            "memo",
            "memo_digest",
            "analysis_inputs",
            "t6_model_processes_started",
            "t6_review_processes_started",
            "t6_ordinals_reserved",
            "stop_reasons",
        },
        "T6 review index",
    )
    if t6_review["status"] != "complete":
        raise SchemaError("T6 review index must be complete")
    if t6_review["review_decision"] != "unavailable-before-subject-selection":
        raise SchemaError("unsupported T6 review index decision")
    _expect_text(t6_review["memo"], "T6 memo path")
    _expect_sha256_digest(t6_review["memo_digest"])
    if not isinstance(t6_review["analysis_inputs"], dict):
        raise SchemaError("T6 review index analysis inputs must be an object")
    if (
        t6_review["t6_model_processes_started"] != 0
        or t6_review["t6_review_processes_started"] != 0
        or t6_review["t6_ordinals_reserved"] != 0
    ):
        raise SchemaError("T6 review index must not record starts or reservations")
    if not isinstance(t6_review["stop_reasons"], list) or not t6_review["stop_reasons"]:
        raise SchemaError("T6 review index requires stop reasons")
    return t6_review


def t6_results_index(
    *,
    results: dict[str, Any],
    t5_index: dict[str, Any],
    memo_path: Path,
) -> dict[str, Any]:
    """Return durable T6 evidence without dropping earlier evidence."""
    validate_t6_results(results)

    def label(path: Path) -> str:
        with suppress(ValueError):
            return str(path.relative_to(REPO_ROOT))
        return str(path)

    return {
        "schema_version": 1,
        "plan_task": "T6",
        "status": "complete",
        "inference_branch": "bounded-case-study",
        "t5_evidence_index": t5_index,
        "t4_evidence_index": t5_index["t4_evidence_index"],
        "admission_evidence": t5_index["admission_evidence"],
        "calibration": t5_index["calibration"],
        "w1_gate": t5_index["w1_gate"],
        "w2_gate": t5_index["w2_gate"],
        "t6_review": {
            "status": "complete",
            "review_decision": results["t6_review"]["review_decision"],
            "memo": label(memo_path),
            "memo_digest": digest_file(memo_path),
            "analysis_inputs": results["t6_review"]["analysis_inputs"],
            "t6_model_processes_started": 0,
            "t6_review_processes_started": 0,
            "t6_ordinals_reserved": 0,
            "stop_reasons": results["t6_review"]["stop_reasons"],
        },
    }


CALIBRATION_FAILURE_CLASSES = {
    "auth-env-unsafe",
    "authority-unobservable",
    "authority-widened",
    "canary-malformed",
    "canary-unobservable",
    "candidate-access-unobservable",
    "capture-limit-exceeded",
    "capture-oversized",
    "crash-resume-infrastructure-failure",
    "crash-resume-unknown-started",
    "infrastructure-authority-unproven",
    "jsonl-telemetry-unavailable",
    "local-listener-unavailable",
    "model-unavailable",
    "none",
    "safety-stop-authority-widened",
    "spawn-error",
    "timeout",
}
NON_REPLACEABLE_FAILURE_CLASSES = {
    "authority-widened",
    "crash-resume-unknown-started",
    "local-listener-unavailable",
    "safety-stop-authority-widened",
}


def _expect_calibration_tokens(value: Any) -> None:
    if not isinstance(value, dict):
        raise SchemaError("calibration tokens must be an object")
    _expect_keys(value, {"input", "cached_input", "output", "reasoning"}, "tokens")
    for token_value in value.values():
        if token_value == "unavailable":
            continue
        if isinstance(token_value, bool) or not isinstance(token_value, int) or token_value < 0:
            raise SchemaError("token values must be non-negative integers or unavailable")


def _expect_calibration_snapshot(value: Any) -> None:
    if not isinstance(value, dict):
        raise SchemaError("calibration snapshot must be an object")
    _expect_keys(
        value,
        {
            "before_tool_boundary",
            "after_prompt_boundary",
            "after_controller_canary_boundary",
            "after_worker_boundary",
            "after_hidden_grade_boundary",
        },
        "snapshot",
    )
    for child in value.values():
        _expect_text(child, "snapshot digest")


def _expect_calibration_argv_policy(value: Any) -> None:
    if not isinstance(value, dict):
        raise SchemaError("argv policy must be an object")
    _expect_keys(
        value,
        {
            "codex_cli_version",
            "argv",
            "sandbox",
            "tools",
            "environment",
            "network",
            "web",
            "mcp",
            "delegation",
            "approval_escalation",
            "apps",
            "plugins",
            "multi_agent",
            "stdin_prompt",
            "effective_runtime_config",
            "effective_tool_roster",
            "effective_environment",
            "approval_policy",
        },
        "argv_policy",
    )
    if value["codex_cli_version"] != CODEX_CLI_VERSION:
        raise SchemaError("calibration Codex CLI version changed")
    argv = value["argv"]
    if not isinstance(argv, list) or not argv or any(not isinstance(item, str) for item in argv):
        raise SchemaError("calibration argv must be a string list")
    for flag in ("--cd", "--add-dir"):
        if flag not in argv:
            raise SchemaError("calibration argv missing candidate root flag")
        root = argv[argv.index(flag) + 1]
        if not root.startswith("/private/tmp/plan-evolution-"):
            raise UnsafeContentError("calibration argv root is outside declared run roots")
    if value["sandbox"] != "workspace-write":
        raise SchemaError("calibration sandbox changed")
    for key in (
        "network",
        "web",
        "mcp",
        "delegation",
        "approval_escalation",
        "apps",
        "plugins",
        "multi_agent",
    ):
        if value[key] is not False:
            raise SchemaError(f"calibration policy widened {key}")
    if value["stdin_prompt"] is not True:
        raise SchemaError("calibration prompt must be stdin-fed")


def _expect_calibration_canaries(value: Any) -> None:
    if not isinstance(value, dict):
        raise SchemaError("calibration canaries must be an object")
    required = {
        "candidate_controller_read_digest",
        "candidate_controller_write_digest",
        "prompt_digest",
        "root_nonce_digests",
        "feature_disables",
        "config_strips_environment",
        "exact_candidate_root",
        "stdin_prompt",
        "controller_preflight_pass",
        "worker_proof",
        "local_listener_egress",
        "unproven_controls",
    }
    optional = {"config_denies_approvals", "strict_config", "live_script_digest"}
    actual = set(value)
    if not required.issubset(actual) or actual - required - optional:
        raise SchemaError("calibration canary fields mismatch")
    roots = value["root_nonce_digests"]
    if not isinstance(roots, dict) or set(roots) != set(SYNTHETIC_ROOT_NAMES):
        raise SchemaError("calibration root nonce set changed")
    for digest in roots.values():
        _expect_text(digest, "root nonce digest")
    features = value["feature_disables"]
    if not isinstance(features, dict) or any(child is not True for child in features.values()):
        raise SchemaError("calibration feature disables must all be true")
    unproven = value["unproven_controls"]
    if not isinstance(unproven, list) or any(not isinstance(item, str) for item in unproven):
        raise SchemaError("unproven controls must be a string list")


def _expect_replacement_of(value: Any, ordinal: int) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SchemaError("replacement_of must be an object")
    _expect_keys(
        value,
        {"study_ordinal", "wave_ordinal", "item", "reason"},
        "replacement_of",
    )
    original = _expect_positive_int(value["study_ordinal"], "replacement study ordinal")
    if original >= ordinal:
        raise SchemaError("replacement must point to an earlier ordinal")
    _expect_positive_int(value["wave_ordinal"], "replacement wave ordinal")
    _expect_text(value["item"], "replacement item")
    _expect_text(value["reason"], "replacement reason")
    return dict(value)


def _validate_calibration_record(record: dict[str, Any]) -> None:
    keys = {
        "schema_version",
        "item",
        "allocation",
        "phase",
        "role",
        "study_ordinal",
        "wave_ordinal",
        "hypothesis_observation",
        "requested_model",
        "model_class",
        "resolved_model",
        "status",
        "failure_class",
        "started_at",
        "finished_at",
        "exit_status",
        "session_id",
        "tokens",
        "output_digest",
        "snapshot",
        "argv_policy",
        "canaries",
        "terminal_reason",
    }
    if "live_canary" in record:
        keys.add("live_canary")
    if "replacement_of" in record:
        keys.add("replacement_of")
    _expect_keys(record, keys, "calibration record")
    if record["schema_version"] != 1:
        raise SchemaError("unsupported calibration record schema")
    if record["allocation"] != "instrument_calibration":
        raise SchemaError("calibration allocation changed")
    item = _expect_text(record["item"], "calibration item")
    role = _expect_text(record["role"], "calibration role")
    if record["phase"] != role:
        raise SchemaError("calibration phase must equal role")
    ordinal = _expect_positive_int(record["study_ordinal"], "study ordinal")
    _expect_positive_int(record["wave_ordinal"], "wave ordinal")
    if record["hypothesis_observation"] is not False:
        raise SchemaError("calibration cannot be a hypothesis observation")
    if record["model_class"] not in {"standard", "frontier"}:
        raise SchemaError("unknown calibration model class")
    requested = _expect_text(record["requested_model"], "requested model")
    if requested != MODEL_BY_CLASS[record["model_class"]]:
        raise SchemaError("requested model does not match model class")
    _expect_text(record["resolved_model"], "resolved model")
    if record["status"] not in {"done", "failed"}:
        raise SchemaError("unknown calibration status")
    if record["failure_class"] not in CALIBRATION_FAILURE_CLASSES:
        raise SchemaError("unknown calibration failure class")
    if record["failure_class"].startswith("crash-resume-") and (
        record["failure_class"] != "crash-resume-unknown-started"
        or record["exit_status"] != "unknown-started"
    ):
        raise SchemaError("crash-resume records must be unknown-started")
    _expect_timestamp(record["started_at"])
    _expect_timestamp(record["finished_at"])
    if float(record["started_at"]) > float(record["finished_at"]):
        raise SchemaError("calibration finish time precedes start time")
    _expect_text(record["exit_status"], "exit status")
    _expect_text(record["session_id"], "session id")
    _expect_calibration_tokens(record["tokens"])
    _expect_text(record["output_digest"], "output digest")
    _expect_calibration_snapshot(record["snapshot"])
    _expect_calibration_argv_policy(record["argv_policy"])
    _expect_calibration_canaries(record["canaries"])
    if "live_canary" in record and not (
        isinstance(record["live_canary"], dict) or record["live_canary"] == "not-started"
    ):
        raise SchemaError("live canary must be an object or not-started")
    if "live_canary" not in record and not (
        record["exit_status"] == "not-started"
        and record["failure_class"] == "infrastructure-authority-unproven"
    ):
        raise SchemaError("live canary is required for started calibration records")
    _expect_text(record["terminal_reason"], "terminal reason")
    if "replacement_of" in record:
        replacement = _expect_replacement_of(record["replacement_of"], ordinal)
        if not item.endswith("-replacement"):
            raise SchemaError("replacement item must be named as a replacement")
        if not item.startswith(replacement["item"]):
            raise SchemaError("replacement item does not match original")


def validate_calibration_results(results: dict[str, Any]) -> list[dict[str, Any]]:
    _check_bounds(results)
    if results.get("plan_task") == "T4":
        results = _calibration_payload(results)
    _expect_keys(
        results,
        {
            "schema_version",
            "plan_task",
            "status",
            "allocation",
            "calibration_slots",
            "replacement_reservations",
            "terminal_slots",
            "failed_slots",
            "instrument_loss_rate",
            "inference_launch_permitted",
            "inferential_processes_started",
            "model_processes_started",
            "new_model_processes_started",
            "progress_digest",
            "records",
        },
        "calibration results",
    )
    if results["schema_version"] != 1 or results["plan_task"] != "T3":
        raise SchemaError("unsupported calibration results")
    if results["status"] != "complete" or results["allocation"] != "instrument_calibration":
        raise SchemaError("calibration results are not terminal")
    if results["calibration_slots"] != 8:
        raise SchemaError("calibration slot count changed")
    _expect_digest(results["progress_digest"])
    records = results["records"]
    if not isinstance(records, list) or not records:
        raise SchemaError("calibration records must be a non-empty list")
    if len(records) not in {8, 16}:
        raise SchemaError("calibration reuse requires exactly 8 or 16 terminal records")
    expected_originals = {
        item: {"role": role, "model_class": model_class}
        for item, role, model_class in CALIBRATION_ROLES
    }
    ordinals: set[int] = set()
    items: set[str] = set()
    records_by_ordinal: dict[int, dict[str, Any]] = {}
    replacements = 0
    failed = 0
    model_starts = 0
    for expected_ordinal, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise SchemaError("calibration record must be an object")
        _validate_calibration_record(record)
        ordinal = record["study_ordinal"]
        if ordinal != expected_ordinal:
            raise SchemaError("calibration study ordinals must be contiguous and ordered")
        if record["wave_ordinal"] != expected_ordinal:
            raise SchemaError("calibration wave ordinals must be contiguous and ordered")
        if ordinal in ordinals:
            raise SchemaError("duplicate calibration study ordinal")
        ordinals.add(ordinal)
        item = record["item"]
        if item in items:
            raise SchemaError("duplicate calibration item")
        items.add(item)
        if record["exit_status"] != "not-started":
            model_starts += 1
        base_item = item.removesuffix("-replacement")
        expected = expected_originals.get(base_item)
        if expected is None:
            raise SchemaError("calibration item is outside the frozen role matrix")
        if record["role"] != expected["role"]:
            raise SchemaError("calibration role changed for item")
        if record["model_class"] != expected["model_class"]:
            raise SchemaError("calibration model class changed for item")
        if "replacement_of" in record:
            if expected_ordinal <= 8:
                raise SchemaError("original calibration assignments cannot be replacements")
            replacements += 1
            original_ordinal = record["replacement_of"]["study_ordinal"]
            if original_ordinal not in ordinals:
                raise SchemaError("replacement points to an absent earlier record")
            original = records_by_ordinal[original_ordinal]
            if record["replacement_of"]["item"] != original["item"]:
                raise SchemaError("replacement item link does not match original")
            if record["replacement_of"]["wave_ordinal"] != original["wave_ordinal"]:
                raise SchemaError("replacement wave link does not match original")
            if record["role"] != original["role"]:
                raise SchemaError("replacement role differs from original")
            if record["model_class"] != original["model_class"]:
                raise SchemaError("replacement model class differs from original")
            if record["requested_model"] != original["requested_model"]:
                raise SchemaError("replacement requested model differs from original")
        if record["status"] == "failed":
            failed += 1
        records_by_ordinal[ordinal] = record
    if len(records) == 8 and replacements != 0:
        raise SchemaError("partial replacement state is illegal")
    if len(records) == 16 and replacements != 8:
        raise SchemaError("complete replacement state must contain exactly 8 replacements")
    if results["terminal_slots"] != len(records):
        raise SchemaError("terminal slot count does not match records")
    if results["replacement_reservations"] != replacements:
        raise SchemaError("replacement count does not match records")
    if results["failed_slots"] != failed:
        raise SchemaError("failed slot count does not match records")
    loss = results["instrument_loss_rate"]
    if not isinstance(loss, (int, float)) or isinstance(loss, bool) or not math.isfinite(loss):
        raise SchemaError("instrument loss rate must be finite")
    if not math.isclose(float(loss), failed / len(records), rel_tol=0.0, abs_tol=1e-12):
        raise SchemaError("instrument loss rate does not match failed/terminal slots")
    if results["model_processes_started"] != model_starts:
        raise SchemaError("model process count does not match started records")
    new_starts = results["new_model_processes_started"]
    if (
        isinstance(new_starts, bool)
        or not isinstance(new_starts, int)
        or new_starts < 0
        or new_starts > model_starts
    ):
        raise SchemaError("new model process count is out of bounds")
    if results["inference_launch_permitted"] is not False:
        raise SchemaError("calibration cannot permit inference on instrument loss")
    if results["inferential_processes_started"] != 0:
        raise SchemaError("T3 results must not start inference")
    return list(records)


def _validate_existing_results_binding(
    *,
    records: list[dict[str, Any]],
    results: dict[str, Any],
    run_dir: Path,
) -> None:
    progress = run_dir / "calibration-progress.jsonl"
    if not progress.exists():
        raise InvocationLimitError(
            "existing durable calibration requires its original progress ledger"
        )
    if digest_file(progress) != results["progress_digest"]:
        raise InvocationLimitError(
            "progress ledger digest does not match durable calibration results"
        )
    root = str(run_dir.resolve(strict=True))
    for record in records:
        argv = record["argv_policy"]["argv"]
        for flag in ("--cd", "--add-dir"):
            if flag not in argv:
                raise SchemaError("calibration record missing run-root argv")
            path = Path(argv[argv.index(flag) + 1]).resolve(strict=True)
            try:
                path.relative_to(root)
            except ValueError as exc:
                raise InvocationLimitError(
                    "calibration record belongs to a different run root"
                ) from exc


def _load_existing_calibration_results(run_dir: Path) -> list[dict[str, Any]]:
    if not (RESEARCH_ROOT / "results.json").exists():
        return []
    existing = load_json(RESEARCH_ROOT / "results.json")
    if not isinstance(existing, dict) or existing.get("plan_task") not in {
        "T3",
        "T4",
        "T5",
        "T6",
    }:
        return []
    calibration = _calibration_payload(existing)
    records = validate_calibration_results(calibration)
    _validate_existing_results_binding(records=records, results=calibration, run_dir=run_dir)
    return records


def _calibration_slot_roots(run_dir: Path, index: int, item: str) -> tuple[Path, dict[str, Path]]:
    slot_root = run_dir / "calibration" / f"{index:02d}-{item}"
    roots = {name: slot_root / name for name in SYNTHETIC_ROOT_NAMES}
    return slot_root, roots


def calibrate(design_path: Path, run_dir: Path) -> dict[str, Any]:
    """Reserve and terminally capture T3 calibration slots and replacements."""
    design = load_design(design_path)
    summary = validate_design(design)
    run_dir = prepare_calibration_run_root(run_dir)
    progress = run_dir / "calibration-progress.jsonl"
    ledger = InvocationLedger(
        progress,
        study_ceiling=summary["study_ceiling"],
        fixed_releases=summary["fixed_releases"],
        reserve_release=summary["reserve_release"],
    )
    existing_records = _load_existing_calibration_results(run_dir)
    records: list[dict[str, Any]] = list(existing_records)
    existing_by_ordinal = {
        record.get("study_ordinal"): record
        for record in existing_records
        if isinstance(record.get("study_ordinal"), int)
    }
    if any("replacement_of" in record for record in existing_records):
        raise InvocationLimitError("calibration replacements are terminal and cannot be replaced")
    if any(
        record.get("failure_class") in NON_REPLACEABLE_FAILURE_CLASSES
        for record in existing_records
    ):
        raise InvocationLimitError("non-replaceable calibration terminal cannot be replaced")
    replacement_mode = all(ordinal in existing_by_ordinal for ordinal in range(1, 9))
    launched = 0
    safety_stop = False
    slot_specs: list[tuple[int, str, str, str, dict[str, Any] | None]] = []
    for index, (base_item, role, model_class) in enumerate(CALIBRATION_ROLES, start=1):
        if replacement_mode:
            original = existing_by_ordinal[index]
            replacement = {
                "study_ordinal": original["study_ordinal"],
                "wave_ordinal": original["wave_ordinal"],
                "item": original["item"],
                "reason": "identical replacement after pre-spawn infrastructure failure",
            }
            slot_specs.append(
                (index + 8, f"{base_item}-replacement", role, model_class, replacement)
            )
        else:
            slot_specs.append((index, base_item, role, model_class, None))
    for slot_index, item, role, model_class, replacement_of in slot_specs:
        if ledger.was_started(item):
            record = close_reserved_calibration_crash(
                ledger=ledger,
                run_dir=run_dir,
                slot_index=slot_index,
                item=item,
                role=role,
                model_class=model_class,
                replacement_of=replacement_of,
            )
            if record not in records:
                records.append(record)
            continue
        slot_root, roots = prepare_calibration_slot_roots(run_dir, slot_index, item)
        study_ordinal, wave_ordinal = ledger.reserve(
            item,
            wave="W1",
            replacement_of=None
            if replacement_of is None
            else replacement_of["study_ordinal"],
        )
        started_at = time.time()
        candidate_root = roots["candidate"]
        prompt_file = roots["prompt"] / "prompt.txt"
        safe_write_text(prompt_file, _calibration_prompt(role))
        invocation = build_calibration_invocation(
            item=item,
            model=design["models"][model_class],
            candidate_root=candidate_root,
            prompt_file=prompt_file,
            policy=design["dry_run_policy"],
            limits=design["role_limits"][role],
        )
        canaries = evaluate_calibration_canaries(
            roots=roots,
            candidate_root=candidate_root,
            prompt_file=prompt_file,
            invocation=invocation,
        )
        if safety_stop:
            listener_observed = {"connected": False, "matched": False, "not_started": True}
            canaries["live_script_digest"] = "not-started"
            process = None
            status = "failed"
            failure_class = "safety-stop-authority-widened"
            live_canary: dict[str, Any] | None = {
                "event_schema": "not-started",
                "output_digest": digest_text("not-started: prior authority widened"),
                "listener_observed": dict(listener_observed),
                "canary_result": "not-started",
                "tool_roster_proof": "not-started",
                "approval_policy_proof": "not-started",
            }
            tokens: dict[str, int | str] = {
                "input": "unavailable",
                "cached_input": "unavailable",
                "output": "unavailable",
                "reasoning": "unavailable",
            }
            resolved_model = "unavailable"
            terminal_reason = (
                "replacement calibration stopped before launch because an earlier "
                "live synthetic canary proved widened worker authority"
            )
        else:
            listener_nonce = digest_text(f"{item}:{study_ordinal}:listener")
            port, listener_observed, listener_thread = _start_local_listener(listener_nonce)
            if "setup_error" in listener_observed:
                listener_thread.join(timeout=1)
                canaries["live_script_digest"] = "not-written-listener-unavailable"
                process = None
                status = "failed"
                failure_class = "local-listener-unavailable"
                live_canary = {
                    "event_schema": "not-started",
                    "output_digest": digest_text("not-started: listener unavailable"),
                    "listener_observed": dict(listener_observed),
                    "canary_result": "not-started",
                    "tool_roster_proof": "not-started",
                    "approval_policy_proof": "not-started",
                }
                tokens = {
                    "input": "unavailable",
                    "cached_input": "unavailable",
                    "output": "unavailable",
                    "reasoning": "unavailable",
                }
                resolved_model = "unavailable"
                terminal_reason = (
                    "live synthetic calibration stopped before script creation "
                    "because the controller loopback listener could not bind"
                )
            else:
                script = _write_live_canary_script(
                    candidate_root=candidate_root,
                    roots=roots,
                    listener_port=port,
                    listener_nonce=listener_nonce,
                )
                canaries["live_script_digest"] = digest_file(
                    confine_disposable_path(candidate_root, script)
                )
                process = run_codex_process(
                    invocation["argv"],
                    prompt=prompt_file.read_text(encoding="utf-8"),
                    cwd=candidate_root,
                )
                launched += 1
                listener_thread.join(timeout=1)
                (
                    status,
                    failure_class,
                    live_canary,
                    tokens,
                    event_schema,
                    resolved_model,
                ) = classify_live_canary(
                    candidate_root=candidate_root,
                    roots=roots,
                    process=process,
                    listener_observed=listener_observed,
                )
                terminal_reason = (
                    "live synthetic calibration canary completed"
                    if status == "done"
                    else f"live synthetic calibration terminal failure: {failure_class}"
                )
                if failure_class == "authority-widened":
                    safety_stop = True
        finished_at = time.time()
        record = _calibration_record(
            item=item,
            role=role,
            model_class=model_class,
            model=design["models"][model_class],
            study_ordinal=study_ordinal,
            wave_ordinal=wave_ordinal,
            invocation=invocation,
            canaries=canaries,
            started_at=started_at,
            finished_at=finished_at,
            replacement_of=replacement_of,
            process=process,
            live_canary=live_canary,
            status=status,
            failure_class=failure_class,
            tokens=tokens,
            resolved_model=resolved_model,
            terminal_reason=terminal_reason,
        )
        records.append(record)
        write_json(slot_root / "terminal.json", record)
        ledger.terminal(item, status=status, note=record["failure_class"])
    if len(records) == len(existing_records):
        raise InvocationLimitError("calibration slots were already started")
    failed = sum(1 for record in records if record["status"] == "failed")
    replacement_count = sum(1 for record in records if "replacement_of" in record)
    result = {
        "schema_version": 1,
        "plan_task": "T3",
        "status": "complete",
        "allocation": "instrument_calibration",
        "calibration_slots": summary["allocations"]["instrument_calibration"],
        "replacement_reservations": replacement_count,
        "terminal_slots": len(records),
        "failed_slots": failed,
        "instrument_loss_rate": failed / len(records),
        "inference_launch_permitted": False,
        "inferential_processes_started": 0,
        "model_processes_started": sum(
            1
            for record in records
            if record.get("exit_status") != "not-started"
        ),
        "new_model_processes_started": launched,
        "progress_digest": digest_file(progress),
        "records": records,
    }
    validate_calibration_results(result)
    write_json(run_dir / "calibration-results.json", result)
    write_json(RESEARCH_ROOT / "results.json", result)
    prior_index = load_json(RESEARCH_ROOT / "evidence-index.json")
    write_json(
        RESEARCH_ROOT / "evidence-index.json",
        calibration_results_index(result, prior_index),
    )
    return {
        "status": "complete",
        "calibration_slots": result["calibration_slots"],
        "terminal_slots": result["terminal_slots"],
        "instrument_loss_rate": result["instrument_loss_rate"],
        "inference_launch_permitted": result["inference_launch_permitted"],
        "model_processes_started": result["model_processes_started"],
    }


def admit(design_path: Path, run_dir: Path) -> dict[str, Any]:
    design = load_design(design_path)
    validate_design(design)
    run_dir = confine_run_dir_for_creation(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    tasks = task_frame_with_resolved_commits(design)
    records = [admit_task(task, run_dir=run_dir) for task in tasks]
    status_counts: dict[str, int] = {}
    for record in records:
        status_counts[record["status"]] = status_counts.get(record["status"], 0) + 1
    result = {
        "schema_version": 1,
        "status": "complete",
        "tasks": len(records),
        "status_counts": status_counts,
        "records": records,
        "inference_ready": status_counts.get("admitted", 0) == 12,
    }
    write_json(run_dir / "admission.json", result)
    write_json(RESEARCH_ROOT / "evidence-index.json", admission_evidence_index(result))
    return {
        "status": "complete",
        "tasks": len(records),
        "admitted": status_counts.get("admitted", 0),
        "excluded": status_counts.get("excluded", 0),
        "inference_ready": result["inference_ready"],
    }


def gate_w1(design_path: Path) -> dict[str, Any]:
    """Emit the deterministic T4 W1 gate from existing T2/T3 evidence."""
    design = load_design(design_path)
    validate_design(design)
    design_digest = digest_file(design_path)
    wave_path = RESEARCH_ROOT / "wave-1.json"
    if digest_file(wave_path) != design_digest:
        raise SchemaError("frozen W1 wave design does not match gate design")
    existing_results = load_json(RESEARCH_ROOT / "results.json")
    if not isinstance(existing_results, dict):
        raise SchemaError("durable results must be an object")
    calibration = _calibration_payload(existing_results)
    validate_calibration_results(calibration)
    prior_index = load_json(RESEARCH_ROOT / "evidence-index.json")
    if not isinstance(prior_index, dict):
        raise SchemaError("durable evidence index must be an object")
    admission = _admission_payload(prior_index)
    _validate_admission_summary(admission)
    calibration_digest = digest_text(json.dumps(calibration, sort_keys=True))
    evidence_index_digest = digest_text(json.dumps(admission, sort_keys=True))
    memo = build_w1_gate_memo(
        design=design,
        design_digest=design_digest,
        calibration=calibration,
        admission=admission,
        calibration_digest=calibration_digest,
        evidence_index_digest=evidence_index_digest,
    )
    results = {
        "schema_version": 1,
        "plan_task": "T4",
        "status": "complete",
        "inference_branch": "bounded-case-study",
        "calibration": calibration,
        "w1_gate": memo,
    }
    validate_w1_results(results)
    memo_path = RESEARCH_ROOT / "w1-gate-memo.json"
    write_json(memo_path, memo)
    write_json(RESEARCH_ROOT / "results.json", results)
    write_json(
        RESEARCH_ROOT / "evidence-index.json",
        w1_results_index(
            results=results,
            prior_index=prior_index,
            memo_path=memo_path,
            wave_path=wave_path,
        ),
    )
    return {
        "status": "complete",
        "gate": "W1",
        "gate_decision": memo["gate_decision"],
        "w2_available": memo["release_w2"],
        "blocked_would_be_inferential_reservations": memo["w1_core"][
            "would_be_inferential_reservations"
        ],
        "t4_model_processes_started": 0,
        "t4_ordinals_reserved": 0,
    }


def gate_w2(design_path: Path) -> dict[str, Any]:
    """Emit the deterministic T5 W2 stopped-branch allocation memo."""
    design = load_design(design_path)
    validate_design(design)
    design_digest = digest_file(design_path)
    wave_path = RESEARCH_ROOT / "wave-1.json"
    memo_path = RESEARCH_ROOT / "w1-gate-memo.json"
    existing_results = load_json(RESEARCH_ROOT / "results.json")
    if not isinstance(existing_results, dict):
        raise SchemaError("durable results must be an object")
    t4_results = _t4_results_payload(existing_results)
    prior_index = load_json(RESEARCH_ROOT / "evidence-index.json")
    if not isinstance(prior_index, dict):
        raise SchemaError("durable evidence index must be an object")
    t4_index = _t4_index_payload(prior_index)
    chain_digests = validate_w1_chain(
        design_digest=design_digest,
        wave_path=wave_path,
        memo_path=memo_path,
        t4_results=t4_results,
        t4_index=t4_index,
    )
    w1_memo = t4_results["w1_gate"]
    memo = build_w2_gate_memo(
        design=design,
        chain_digests=chain_digests,
        w1_memo=w1_memo,
    )
    results = {
        "schema_version": 1,
        "plan_task": "T5",
        "status": "complete",
        "inference_branch": "bounded-case-study",
        "t4_results": t4_results,
        "calibration": t4_results["calibration"],
        "w1_gate": w1_memo,
        "w2_gate": memo,
    }
    validate_t5_results(results)
    w2_memo_path = RESEARCH_ROOT / "w2-gate-memo.json"
    write_json(w2_memo_path, memo)
    write_json(RESEARCH_ROOT / "results.json", results)
    write_json(
        RESEARCH_ROOT / "evidence-index.json",
        w2_results_index(
            results=results,
            t4_index=t4_index,
            memo_path=w2_memo_path,
        ),
    )
    return {
        "status": "complete",
        "gate": "W2",
        "gate_decision": memo["gate_decision"],
        "w3_fixed_available": memo["release_w3_fixed"],
        "reserve_item_ids_released": len(memo["reserve_item_ids"]),
        "t5_model_processes_started": 0,
        "t5_ordinals_reserved": 0,
    }


def gate_t6(design_path: Path) -> dict[str, Any]:
    """Emit the deterministic T6 unavailable review-allocation memo."""
    design = load_design(design_path)
    validate_design(design)
    design_digest = digest_file(design_path)
    wave_path = RESEARCH_ROOT / "wave-1.json"
    memo_path = RESEARCH_ROOT / "w2-gate-memo.json"
    existing_results = load_json(RESEARCH_ROOT / "results.json")
    if not isinstance(existing_results, dict):
        raise SchemaError("durable results must be an object")
    t5_results = _t5_results_payload(existing_results)
    prior_index = load_json(RESEARCH_ROOT / "evidence-index.json")
    if not isinstance(prior_index, dict):
        raise SchemaError("durable evidence index must be an object")
    t5_index = _t5_index_payload(prior_index)
    chain_digests = validate_t5_chain(
        design_digest=design_digest,
        wave_path=wave_path,
        memo_path=memo_path,
        t5_results=t5_results,
        t5_index=t5_index,
    )
    w2_memo = t5_results["w2_gate"]
    memo = build_t6_review_memo(
        design=design,
        chain_digests=chain_digests,
        w2_memo=w2_memo,
    )
    results = {
        "schema_version": 1,
        "plan_task": "T6",
        "status": "complete",
        "inference_branch": "bounded-case-study",
        "t5_results": t5_results,
        "t4_results": t5_results["t4_results"],
        "calibration": t5_results["calibration"],
        "w1_gate": t5_results["w1_gate"],
        "w2_gate": w2_memo,
        "t6_review": memo,
    }
    validate_t6_results(results)
    t6_memo_path = RESEARCH_ROOT / "t6-review-memo.json"
    write_json(t6_memo_path, memo)
    write_json(RESEARCH_ROOT / "results.json", results)
    write_json(
        RESEARCH_ROOT / "evidence-index.json",
        t6_results_index(
            results=results,
            t5_index=t5_index,
            memo_path=t6_memo_path,
        ),
    )
    return {
        "status": "complete",
        "gate": "review-allocation",
        "review_decision": memo["review_decision"],
        "review_capacity_processes": memo["review_allocation"]["capacity_processes"],
        "t6_model_processes_started": 0,
        "t6_review_processes_started": 0,
        "t6_ordinals_reserved": 0,
    }


def run_design(design_path: Path, run_dir: Path, *, dry_run: bool) -> dict[str, Any]:
    design = load_design(design_path)
    validate_design(design)
    if not dry_run:
        raise SandboxPolicyError("T1 implements dry-run only; model spawn is refused")
    run_dir = confine_run_dir_for_creation(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    return {"status": "dry-run", "spawned": False, "tasks": len(design["tasks"])}


def summarize(design_path: Path, run_dir: Path, output: Path) -> dict[str, Any]:
    design = load_design(design_path)
    summary = validate_design(design)
    confine_run_dir_for_creation(run_dir)
    output = confine_summary_output(output)
    result = {"status": "validated", "study_ceiling": summary["study_ceiling"]}
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--design", required=True)
    admit_cmd = sub.add_parser("admit")
    admit_cmd.add_argument("--design", required=True)
    admit_cmd.add_argument("--run-dir", required=True)
    run_cmd = sub.add_parser("run")
    run_cmd.add_argument("--design", required=True)
    run_cmd.add_argument("--run-dir", required=True)
    run_cmd.add_argument("--dry-run", action="store_true")
    calibrate_cmd = sub.add_parser("calibrate")
    calibrate_cmd.add_argument("--design", required=True)
    calibrate_cmd.add_argument("--run-dir", required=True)
    gate_w1_cmd = sub.add_parser("gate-w1")
    gate_w1_cmd.add_argument("--design", required=True)
    gate_w2_cmd = sub.add_parser("gate-w2")
    gate_w2_cmd.add_argument("--design", required=True)
    gate_t6_cmd = sub.add_parser("gate-t6")
    gate_t6_cmd.add_argument("--design", required=True)
    summary = sub.add_parser("summarize")
    summary.add_argument("--design", required=True)
    summary.add_argument("--run-dir", required=True)
    summary.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.command == "validate":
            result = validate_design(load_design(Path(args.design)))
        elif args.command == "admit":
            result = admit(Path(args.design), Path(args.run_dir))
        elif args.command == "run":
            result = run_design(Path(args.design), Path(args.run_dir), dry_run=args.dry_run)
        elif args.command == "calibrate":
            result = calibrate(Path(args.design), Path(args.run_dir))
        elif args.command == "gate-w1":
            result = gate_w1(Path(args.design))
        elif args.command == "gate-w2":
            result = gate_w2(Path(args.design))
        elif args.command == "gate-t6":
            result = gate_t6(Path(args.design))
        elif args.command == "summarize":
            result = summarize(Path(args.design), Path(args.run_dir), Path(args.output))
        else:
            raise AssertionError(args.command)
    except (WorkbenchError, UnsafeContentError, OSError, subprocess.SubprocessError) as exc:
        print(f"plan-evolution-workbench: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
