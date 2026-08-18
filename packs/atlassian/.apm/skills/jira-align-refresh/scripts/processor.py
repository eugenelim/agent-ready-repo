"""Jira Align refresh processor composed with the shared work-intake runtime."""

from __future__ import annotations

import importlib.util
import sys
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Collection, Mapping

with suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
with suppress(AttributeError, ValueError):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

PROFILE_ID = "jira-align-default"
PROFILE_VERSION = "1.0"


@dataclass(frozen=True)
class WriteBackResult:
    """Redacted result of one Jira Align write-back attempt."""

    code: str
    action: str
    target: str
    payload: object | None = None
    transport_calls: int = 0


def _load_refresh_runtime() -> Any:
    skills_root = Path(__file__).resolve().parents[2]
    try:
        resolved_root = skills_root.resolve(strict=True)
        runtime = (skills_root / "work-intake" / "scripts" / "refresh.py").resolve(
            strict=True
        )
        runtime.relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise RuntimeError("work-intake refresh runtime is unavailable") from exc
    if not runtime.is_file():
        raise RuntimeError("work-intake refresh runtime is unavailable")
    spec = importlib.util.spec_from_file_location("work_intake_refresh_runtime", runtime)
    if spec is None or spec.loader is None:
        raise RuntimeError("work-intake refresh runtime is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def register(
    registry: object,
    refresh_runtime: object | None = None,
    *,
    acquire: Callable[[str, str], Mapping[str, object]],
) -> None:
    """Register the exact Jira Align read-refresh profile with work-intake."""

    refresh = refresh_runtime or _load_refresh_runtime()
    registry.register(
        refresh.ProcessorRegistration(
            name="jira-align-refresh",
            profile_id=PROFILE_ID,
            profile_version=PROFILE_VERSION,
            capabilities=frozenset({"acquire"}),
            acquire=acquire,
            revision_field="modifiedDate",
            field_mapping=(("Outcome", "title"), ("User stories", "description")),
        )
    )


def validate_destination(
    url: str,
    *,
    refresh_runtime: object | None = None,
    resolver: Callable[[str], Collection[str]] | None = None,
) -> object:
    """Validate the configured Jira Align destination before credentials."""

    refresh = refresh_runtime or _load_refresh_runtime()
    policy = refresh.DestinationPolicy(
        schemes=frozenset({"https"}),
        hosts=frozenset({"portfolio-tracker.example.test"}),
        ports=frozenset({443}),
        credentials_attached=True,
    )
    kwargs = {"policy": policy}
    if resolver is not None:
        kwargs["resolver"] = resolver
    return refresh.validate_destination(url, **kwargs)


async def write_back(
    *,
    client: object,
    action: str,
    target: str,
    **_kwargs: object,
) -> WriteBackResult:
    """Fail closed until Jira Align has narrow write-back commands."""

    return WriteBackResult(
        "unsupported_capability",
        action,
        target,
        transport_calls=_transport_calls(client),
    )


def _transport_calls(client: object) -> int:
    calls = getattr(client, "calls", ())
    try:
        return len(calls)
    except TypeError:
        return 0
