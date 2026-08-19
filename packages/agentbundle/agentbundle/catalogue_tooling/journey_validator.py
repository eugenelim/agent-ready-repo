"""Parse and validate the public JOURNEY.md frontmatter convention."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentbundle.catalogue_tooling.file_safety import (
    UnsafeContentError,
    read_confined_regular_file,
)

REQUIRED_KEYS = (
    "journey_id",
    "pack",
    "start_state",
    "end_state",
    "scope",
    "tagline",
    "contract",
)
CONTRACT_KEYS = ("useItWhen", "youProvide", "youReceive", "yourDecisions")
STATE_VALUES = {"read-only", "proposed-write", "confirmed-write"}
SCOPE_VALUES = {"repo", "user"}
EFFECT_KINDS = {
    "credential-read",
    "file-write",
    "git-push",
    "network-call",
    "shell-exec",
}


def _location(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _error(location: str, message: str) -> tuple[None, list[str]]:
    return None, [f"{location}: {message}"]


def _validate_required(data: dict[str, Any], location: str) -> list[str]:
    for key in REQUIRED_KEYS:
        if key not in data:
            return [f"{location}: missing required frontmatter key: {key}"]

    for key in ("journey_id", "pack", "start_state", "end_state", "scope", "tagline"):
        if not isinstance(data[key], str):
            return [f"{location}: {key} must be a string"]
    if data["start_state"] not in STATE_VALUES:
        return [f"{location}: start_state must be one of {sorted(STATE_VALUES)}"]
    if data["end_state"] not in STATE_VALUES:
        return [f"{location}: end_state must be one of {sorted(STATE_VALUES)}"]
    if data["scope"] not in SCOPE_VALUES:
        return [f"{location}: scope must be one of {sorted(SCOPE_VALUES)}"]
    if len(data["tagline"]) > 120:
        return [f"{location}: tagline must be at most 120 characters"]

    contract = data["contract"]
    if not isinstance(contract, dict):
        return [f"{location}: contract must be an object"]
    unknown = sorted(set(contract) - set(CONTRACT_KEYS))
    if unknown:
        return [f"{location}: unknown contract field: {unknown[0]}"]
    for key in CONTRACT_KEYS:
        if key not in contract:
            return [f"{location}: missing required contract key: {key}"]
    for key in ("useItWhen", "youProvide", "youReceive"):
        if not isinstance(contract[key], str):
            return [f"{location}: contract.{key} must be a string"]
    decisions = contract["yourDecisions"]
    if not isinstance(decisions, list) or not all(
        isinstance(item, str) for item in decisions
    ):
        return [f"{location}: contract.yourDecisions must be an array of strings"]

    effects = data.get("effects", [])
    if not isinstance(effects, list):
        return [f"{location}: effects must be an array"]
    for index, effect in enumerate(effects):
        if not isinstance(effect, dict):
            return [f"{location}: effects[{index}] must be an object"]
        if set(effect) != {"kind", "description"}:
            return [f"{location}: effects[{index}] must contain only kind and description"]
        if not all(isinstance(effect[key], str) for key in ("kind", "description")):
            return [f"{location}: effects[{index}] values must be strings"]
        if effect["kind"] not in EFFECT_KINDS:
            return [
                f"{location}: effects[{index}].kind must be one of "
                f"{sorted(EFFECT_KINDS)}"
            ]
    return []


def parse_journey_md(
    catalogue_root: Path,
    path: Path,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Return validated frontmatter and diagnostics for one optional journey file."""
    location = _location(catalogue_root, path)
    try:
        path.lstat()
    except FileNotFoundError:
        return None, []
    except OSError as exc:
        return _error(location, f"cannot inspect journey file: {exc}")

    try:
        import yaml
    except ImportError:
        return _error(location, "PyYAML required — install agentbundle[lint]")

    try:
        text = read_confined_regular_file(catalogue_root, path).decode("utf-8")
    except (UnsafeContentError, UnicodeDecodeError, OSError) as exc:
        return _error(location, f"cannot read journey file safely: {exc}")

    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return _error(location, "missing opening YAML frontmatter delimiter")
    try:
        closing = lines.index("---", 1)
    except ValueError:
        return _error(location, "missing closing YAML frontmatter delimiter")

    try:
        loaded = yaml.safe_load("\n".join(lines[1:closing]))
    except yaml.YAMLError as exc:
        return _error(location, f"malformed YAML frontmatter: {exc}")
    if not isinstance(loaded, dict):
        return _error(location, "YAML frontmatter must be an object")

    diagnostics = _validate_required(loaded, location)
    if diagnostics:
        return None, diagnostics
    return loaded, []
