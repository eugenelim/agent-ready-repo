"""Resolve loop telemetry layout settings without running the sender."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from agentbundle.catalogue_tooling.file_safety import (
    UnsafeContentError,
    read_confined_regular_file,
    validate_confined_directory,
)

__all__ = [
    "MAX_LAYOUT_BYTES",
    "ResolvedTelemetryLayout",
    "TelemetryLayoutError",
    "resolve",
]

MAX_LAYOUT_BYTES = 64 * 1024
_LAYOUT_NAME = "agentbundle-layout.toml"
# The sender reads exactly one key from `--config`: `[telemetry].endpoint`. Every
# other setting reaches it only as an explicit flag, so a setting with no flag
# here cannot be delivered at all and is refused rather than silently dropped --
# these settings decide where data is sent, and a dropped one fails open.
_ENDPOINT = "endpoint"
_SETTING_FLAGS = {"service_name": "--service-name"}
_DELIVERABLE = {_ENDPOINT, *_SETTING_FLAGS}
_PROFILE_PARTS = (
    "packs",
    "core",
    ".apm",
    "skills",
    "work-loop",
    "profiles",
    "work-loop.toml",
)


class TelemetryLayoutError(ValueError):
    """A telemetry layout exists but cannot be used safely."""


@dataclass(frozen=True)
class ResolvedTelemetryLayout:
    """Merged telemetry settings and arguments for ``jsonl-otlp-export``."""

    settings: dict[str, str]
    config_path: Path | None
    arguments: tuple[str, ...]


def _read_layout(root: Path, path: Path) -> dict[str, str]:
    """Read one bounded layout file and validate its telemetry table."""
    try:
        path.lstat()
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise UnsafeContentError(f"layout file cannot be inspected safely: {path}") from exc

    raw = read_confined_regular_file(root, path, max_bytes=MAX_LAYOUT_BYTES)
    try:
        parsed = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise TelemetryLayoutError(f"layout file does not parse as TOML: {path}") from exc

    telemetry = parsed.get("telemetry")
    if telemetry is None:
        return {}
    if not isinstance(telemetry, dict):
        raise TelemetryLayoutError(f"[telemetry] must be a table: {path}")

    settings: dict[str, str] = {}
    for key, value in telemetry.items():
        if not isinstance(value, str) or not value.strip():
            raise TelemetryLayoutError(
                f"[telemetry].{key} must be a non-empty string: {path}"
            )
        settings[key] = value
    return settings


def resolve(repo_root: Path, user_path: Path) -> ResolvedTelemetryLayout:
    """Resolve repository-first telemetry settings and render sender arguments.

    Both layout files are untrusted. Repository scope uses the catalogue's
    confinement helper with the repository root. User scope uses the same
    descriptor-safe helper with the explicitly supplied layout directory as its
    root, so an out-of-repository config remains supported without following a
    link at that boundary.
    """
    if not repo_root.is_absolute():
        raise TelemetryLayoutError("repo_root must be absolute")
    if not user_path.is_absolute():
        raise TelemetryLayoutError("user_path must be absolute")

    validate_confined_directory(repo_root, repo_root)
    repo_path = repo_root / _LAYOUT_NAME
    repo_settings = _read_layout(repo_root, repo_path)
    user_settings = _read_layout(user_path.parent, user_path)

    # workspace_mcp chooses one whole scope for each section. Telemetry must
    # merge each setting instead: a repository value wins, while only an omitted
    # repository value falls back to the user's file.
    settings = {**user_settings, **repo_settings}

    undeliverable = sorted(set(settings) - _DELIVERABLE)
    if undeliverable:
        raise TelemetryLayoutError(
            "[telemetry] settings the sender cannot receive: "
            + ", ".join(undeliverable)
            + f" (deliverable: {', '.join(sorted(_DELIVERABLE))})"
        )

    config_path: Path | None = None
    if _ENDPOINT in repo_settings:
        config_path = repo_path
    elif _ENDPOINT in user_settings:
        config_path = user_path

    arguments = [
        "--input",
        str(repo_root / ".loop-run" / "events.jsonl"),
        "--root",
        str(repo_root),
    ]
    if config_path is not None:
        arguments.extend(("--config", str(config_path)))
    arguments.extend(("--profile", str(repo_root.joinpath(*_PROFILE_PARTS))))
    # `--config` can only carry the endpoint, and it names ONE file. Without
    # these flags a repository value that lost the endpoint race would be merged
    # here and then never reach the sender, which is AC-0041's actual subject.
    for setting, flag in sorted(_SETTING_FLAGS.items()):
        if setting in settings:
            arguments.extend((flag, settings[setting]))

    return ResolvedTelemetryLayout(
        settings=settings,
        config_path=config_path,
        arguments=tuple(arguments),
    )
