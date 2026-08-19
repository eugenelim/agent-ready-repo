"""Jira Align refresh processor composed with the shared work-intake runtime."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Collection, Mapping, cast

with suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
with suppress(AttributeError, ValueError):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

PROFILE_ID = "jira-align-default"
PROFILE_VERSION = "1.0"
PROFILE_PATH = Path(__file__).resolve().parents[1] / "references" / "refresh-profile.json"
_REFRESH_RUNTIME: Any | None = None


@dataclass(frozen=True)
class WriteBackResult:
    """Redacted result of one Jira Align write-back attempt."""

    code: str
    action: str
    target: str
    payload: object | None = None


def _load_refresh_runtime() -> Any:
    global _REFRESH_RUNTIME
    if _REFRESH_RUNTIME is not None:
        return _REFRESH_RUNTIME
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
    module_name = "_work_intake_refresh_runtime_" + hashlib.sha256(
        str(runtime).encode("utf-8")
    ).hexdigest()
    module = sys.modules.get(module_name)
    if module is not None:
        _REFRESH_RUNTIME = module
        return _REFRESH_RUNTIME
    spec = importlib.util.spec_from_file_location(module_name, runtime)
    if spec is None or spec.loader is None:
        raise RuntimeError("work-intake refresh runtime is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _REFRESH_RUNTIME = module
    return _REFRESH_RUNTIME


def register(
    registry: object,
    refresh_runtime: object | None = None,
    *,
    acquire: Callable[[str, str], Mapping[str, object]],
) -> None:
    """Register the exact Jira Align read-refresh profile with work-intake."""

    refresh = refresh_runtime or _load_refresh_runtime()
    profile = _load_profile(PROFILE_PATH)
    registry.register(
        refresh.ProcessorRegistration(
            name="jira-align-refresh",
            profile_id=profile["id"],
            profile_version=profile["version"],
            capabilities=frozenset(profile["capabilities"]),
            acquire=acquire,
            revision_field=profile["revision_field"],
            field_mapping=tuple(profile["field_mapping"].items()),
        )
    )


def validate_destination(
    url: str,
    *,
    refresh_runtime: object | None = None,
    resolver: Callable[[str], Collection[str]] | None = None,
    profile_path: Path = PROFILE_PATH,
) -> object:
    """Validate the configured Jira Align destination before credentials."""

    refresh = refresh_runtime or _load_refresh_runtime()
    profile = _load_profile(profile_path)
    destination = profile["destination"]
    policy = refresh.DestinationPolicy(
        schemes=frozenset({destination["scheme"]}),
        hosts=frozenset({destination["host"]}),
        ports=frozenset({destination["port"]}),
        credentials_attached=True,
    )
    kwargs = {"policy": policy}
    if resolver is not None:
        kwargs["resolver"] = resolver
    return refresh.validate_destination(url, **kwargs)


def _load_profile(path: Path) -> dict[str, Any]:
    """Load the resolved adopter profile that owns the Jira Align destination."""

    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
        destination = profile["destination"]
        if (
            not isinstance(profile, dict)
            or profile.get("id") != PROFILE_ID
            or profile.get("version") != PROFILE_VERSION
            or set(profile) != {
                "contract_version", "id", "version", "revision_field", "field_mapping",
                "capabilities", "destination",
            }
            or profile.get("contract_version") != "tracker-refresh-profile.v1"
            or not isinstance(profile.get("revision_field"), str)
            or not isinstance(profile.get("field_mapping"), dict)
            or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in profile["field_mapping"].items()
            )
            or not isinstance(profile.get("capabilities"), list)
            or any(not isinstance(value, str) for value in profile["capabilities"])
            or len(profile["capabilities"]) != len(set(profile["capabilities"]))
            or profile["capabilities"] != ["acquire"]
            or not isinstance(destination, dict)
            or destination.get("scheme") != "https"
            or not isinstance(destination.get("host"), str)
            or not isinstance(destination.get("port"), int)
        ):
            raise ValueError
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("invalid_refresh_profile") from exc
    return cast(dict[str, Any], profile)


async def write_back(
    *,
    client: object,
    action: str,
    target: str,
    **_kwargs: object,
) -> WriteBackResult:
    """Fail closed until Jira Align has narrow write-back commands."""

    return WriteBackResult("unsupported_capability", action, target)
