"""Validation for Claude-plugin-publishable pack hook wiring.

The rules in this module run before adapter dispatch for packs that qualify for
the Claude-plugin route and are shared by the direct render path,
``agentbundle validate``, the repository lint, and the Claude-plugin compiler.
Other adapter shapes and packs withheld from that route are deliberately
ignored by the ingress wrapper. Repository lint calls the compiler directly so
withheld packs still receive a publication-readiness check.
"""

from __future__ import annotations

import re
import shlex
import stat
import tomllib
from dataclasses import dataclass
from pathlib import Path

KNOWN_EVENTS: frozenset[str] = frozenset(
    {
        "SessionStart",
        "Setup",
        "UserPromptSubmit",
        "UserPromptExpansion",
        "PreToolUse",
        "PermissionRequest",
        "PermissionDenied",
        "PostToolUse",
        "PostToolUseFailure",
        "PostToolBatch",
        "Notification",
        "MessageDisplay",
        "SubagentStart",
        "SubagentStop",
        "TaskCreated",
        "TaskCompleted",
        "Stop",
        "StopFailure",
        "TeammateIdle",
        "InstructionsLoaded",
        "ConfigChange",
        "CwdChanged",
        "DirectoryAdded",
        "FileChanged",
        "WorktreeCreate",
        "WorktreeRemove",
        "PreCompact",
        "PostCompact",
        "Elicitation",
        "ElicitationResult",
        "SessionEnd",
    }
)
_UNPUBLISHABLE_EVENTS = frozenset(
    {"Setup", "PreToolUse", "PermissionRequest", "PermissionDenied"}
)
PUBLISHABLE_EVENTS: frozenset[str] = KNOWN_EVENTS - _UNPUBLISHABLE_EVENTS

_INTERPRETER_SUFFIX = {
    "python": ".py",
    "python3": ".py",
    "sh": ".sh",
    "bash": ".sh",
}
_BASENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_MATCHER_RE = re.compile(r"^[A-Za-z0-9_-]+(?:\|[A-Za-z0-9_-]+)*$")
_OUTER_KEYS = frozenset({"matcher", "hooks"})
_INNER_KEYS = frozenset({"type", "command", "timeout"})
MAX_HOOKS_PER_EVENT = 4
MAX_HOOKS_PER_PACK = 16
DEFAULT_TIMEOUT = 60


@dataclass(frozen=True)
class ValidatedHook:
    """One command hook after pack-source validation."""

    event: str
    matcher: str | None
    timeout: int
    interpreter: str
    body_name: str
    source_file: Path


def is_claude_shaped(entry: object) -> bool:
    """Return whether an outer hook entry uses Claude's nested shape."""
    return isinstance(entry, dict) and "hooks" in entry


def _location(pack_name: str, source_file: Path) -> str:
    return f"pack {pack_name} hook-wiring {source_file.name}"


def _invalid_command(
    pack_name: str, source_file: Path, command: object, reason: str
) -> ValueError:
    return ValueError(
        f"{_location(pack_name, source_file)} command {command!r}: {reason}"
    )


def _validate_body(
    *,
    pack_path: Path,
    hook_source_path: str,
    body_name: str,
    pack_name: str,
    source_file: Path,
    command: object,
) -> None:
    body_root = pack_path / hook_source_path.rstrip("/")
    body_path = body_root / body_name
    try:
        pack_resolved = pack_path.resolve(strict=True)
        cursor = pack_path
        for part in Path(hook_source_path.rstrip("/")).parts:
            cursor /= part
            if cursor.is_symlink():
                raise OSError("hook source path traverses a symlink")
        root_resolved = body_root.resolve(strict=True)
        root_resolved.relative_to(pack_resolved)
        if body_path.is_symlink():
            raise OSError("hook body is a symlink")
        body_resolved = body_path.resolve(strict=True)
        body_resolved.relative_to(root_resolved)
        mode = body_path.stat(follow_symlinks=False).st_mode
    except (OSError, RuntimeError, ValueError):
        raise _invalid_command(
            pack_name,
            source_file,
            command,
            f"hook body {body_name!r} is missing, non-regular, symlinked, or "
            "outside the hook-body source directory",
        ) from None
    if not stat.S_ISREG(mode):
        raise _invalid_command(
            pack_name,
            source_file,
            command,
            f"hook body {body_name!r} is not a regular file",
        )


def validate_wiring_entry(
    *,
    event: str,
    entry: dict,
    pack_path: Path,
    pack_name: str,
    source_file: Path,
    repo_hook_prefix: str,
    hook_source_path: str,
) -> list[ValidatedHook]:
    """Validate one Claude-shaped outer entry and return its command hooks."""
    where = _location(pack_name, source_file)
    if event not in KNOWN_EVENTS:
        raise ValueError(f"{where} event {event!r}: unknown Claude hook event")
    if event not in PUBLISHABLE_EVENTS:
        raise ValueError(
            f"{where} event {event!r}: known but unpublishable instruction-"
            "injection or permission-control event"
        )

    unknown_outer = set(entry) - _OUTER_KEYS
    if unknown_outer:
        raise ValueError(
            f"{where} event {event!r}: unsupported outer key(s) "
            f"{sorted(unknown_outer)}"
        )
    matcher = entry.get("matcher")
    if matcher is not None and (
        not isinstance(matcher, str) or _MATCHER_RE.fullmatch(matcher) is None
    ):
        raise ValueError(
            f"{where} event {event!r}: matcher must be a bare literal or "
            "literal alternation"
        )

    hooks = entry.get("hooks")
    if not isinstance(hooks, list) or not hooks:
        raise ValueError(f"{where} event {event!r}: hooks must be a non-empty array")

    validated: list[ValidatedHook] = []
    prefix = repo_hook_prefix.rstrip("/") + "/"
    for hook in hooks:
        if not isinstance(hook, dict):
            raise ValueError(f"{where} event {event!r}: hook must be an object")
        unknown_inner = set(hook) - _INNER_KEYS
        if unknown_inner:
            raise ValueError(
                f"{where} event {event!r}: unsupported hook key(s) "
                f"{sorted(unknown_inner)}"
            )
        if hook.get("type") != "command":
            raise ValueError(f"{where} event {event!r}: only command hooks publish")
        command = hook.get("command")
        if not isinstance(command, str):
            raise _invalid_command(
                pack_name, source_file, command, "command must be a string"
            )
        try:
            tokens = shlex.split(command, posix=True)
        except ValueError:
            raise _invalid_command(
                pack_name, source_file, command, "command is not valid shell syntax"
            ) from None
        if len(tokens) != 2 or tokens[0] not in _INTERPRETER_SUFFIX:
            raise _invalid_command(
                pack_name,
                source_file,
                command,
                "expected exactly '<python|python3|sh|bash> <hook-body-path>'",
            )
        interpreter, source_token = tokens
        if source_token.startswith("./"):
            source_token = source_token[2:]
        if not source_token.startswith(prefix):
            raise _invalid_command(
                pack_name,
                source_file,
                command,
                f"path must name exactly one body under {prefix!r}",
            )
        body_name = source_token[len(prefix):]
        if "/" in body_name or not body_name:
            raise _invalid_command(
                pack_name,
                source_file,
                command,
                f"path must name exactly one body under {prefix!r}",
            )
        if _BASENAME_RE.fullmatch(body_name) is None:
            raise _invalid_command(
                pack_name, source_file, command, "hook-body basename is not portable"
            )
        suffix = _INTERPRETER_SUFFIX[interpreter]
        if not body_name.endswith(suffix):
            raise _invalid_command(
                pack_name,
                source_file,
                command,
                f"{interpreter} requires a {suffix} hook body",
            )
        timeout = hook.get("timeout", DEFAULT_TIMEOUT)
        if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 60:
            raise ValueError(
                f"{where} event {event!r}: timeout must be an integer from 1 to 60"
            )
        _validate_body(
            pack_path=pack_path,
            hook_source_path=hook_source_path,
            body_name=body_name,
            pack_name=pack_name,
            source_file=source_file,
            command=command,
        )
        validated.append(
            ValidatedHook(
                event=event,
                matcher=matcher,
                timeout=timeout,
                interpreter=interpreter,
                body_name=body_name,
                source_file=source_file,
            )
        )
    return validated


def collect_validated_claude_hooks(
    pack_path: Path,
    *,
    repo_hook_prefix: str,
    hook_source_path: str,
    wiring_source_path: str,
    pack_name: str,
) -> list[ValidatedHook]:
    """Load and validate every Claude-shaped wiring entry in stable order."""
    wiring_dir = pack_path / wiring_source_path.rstrip("/")
    if not wiring_dir.is_dir():
        return []
    try:
        pack_resolved = pack_path.resolve(strict=True)
        cursor = pack_path
        for part in Path(wiring_source_path.rstrip("/")).parts:
            cursor /= part
            if cursor.is_symlink():
                raise OSError("hook-wiring source path traverses a symlink")
        wiring_dir.resolve(strict=True).relative_to(pack_resolved)
    except (OSError, RuntimeError, ValueError):
        raise ValueError(
            f"pack {pack_name} hook-wiring source is symlinked or outside the pack"
        ) from None

    result: list[ValidatedHook] = []
    per_event: dict[str, int] = {}
    try:
        source_files = sorted(wiring_dir.iterdir())
    except (OSError, RuntimeError) as exc:
        raise ValueError(
            f"pack {pack_name} hook-wiring source cannot be enumerated: {exc}"
        ) from None
    for source_file in source_files:
        try:
            is_file = source_file.is_file()
        except OSError:
            raise ValueError(
                f"{_location(pack_name, source_file)}: wiring source cannot be statted"
            ) from None
        if not is_file or source_file.suffix != ".toml":
            continue
        if source_file.is_symlink():
            raise ValueError(
                f"{_location(pack_name, source_file)}: wiring source is a symlink"
            )
        try:
            payload = tomllib.loads(source_file.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ValueError(
                f"{_location(pack_name, source_file)}: cannot read valid TOML: {exc}"
            ) from None
        events = payload.get("hooks")
        if not isinstance(events, dict):
            continue
        for event, entries in events.items():
            if not isinstance(event, str):
                continue
            if not isinstance(entries, list):
                if event and event[0].isupper():
                    raise ValueError(
                        f"{_location(pack_name, source_file)} event {event!r}: "
                        "entries must be an array"
                    )
                continue
            for entry in entries:
                if not is_claude_shaped(entry):
                    continue
                hooks = validate_wiring_entry(
                    event=event,
                    entry=entry,
                    pack_path=pack_path,
                    pack_name=pack_name,
                    source_file=source_file,
                    repo_hook_prefix=repo_hook_prefix,
                    hook_source_path=hook_source_path,
                )
                new_event_count = per_event.get(event, 0) + len(hooks)
                if new_event_count > MAX_HOOKS_PER_EVENT:
                    raise ValueError(
                        f"{_location(pack_name, source_file)} event {event!r}: "
                        f"more than {MAX_HOOKS_PER_EVENT} authored hooks"
                    )
                if len(result) + len(hooks) > MAX_HOOKS_PER_PACK:
                    raise ValueError(
                        f"{_location(pack_name, source_file)}: more than "
                        f"{MAX_HOOKS_PER_PACK} authored hooks in the pack"
                    )
                per_event[event] = new_event_count
                result.extend(hooks)
    return result


def claude_projection_paths(contract: dict) -> tuple[str, str, str, str]:
    """Return hook prefixes/source paths from the adapter contract."""
    entries = {
        item["primitive"]: item
        for item in contract["adapter"]["claude-code"].get("projection", [])
    }
    body = entries["hook-body"]
    return (
        body["target-path"],
        body["plugin-target-path"],
        contract["primitive"]["hook-body"]["source-path"],
        contract["primitive"]["hook-wiring"]["source-path"],
    )


def validate_pack_hook_wiring(pack_path: Path, contract: dict, pack_name: str) -> None:
    """Gate Claude-shaped wiring when the pack can reach the plugin route.

    The direct Claude, Copilot, and compatibility routes accept broader wiring
    vocabularies and command paths. Applying the plugin publisher's restricted
    contract to packs withheld from that route would change those established
    interfaces even though their hook wiring is never compiled into a plugin.
    Import lazily to keep ``build.main``'s adapter imports acyclic.
    """
    from agentbundle.build.main import pack_is_publishable

    if not pack_is_publishable(pack_path):
        return
    repo_prefix, _plugin_prefix, hook_source, wiring_source = (
        claude_projection_paths(contract)
    )
    collect_validated_claude_hooks(
        pack_path,
        repo_hook_prefix=repo_prefix,
        hook_source_path=hook_source,
        wiring_source_path=wiring_source,
        pack_name=pack_name,
    )
