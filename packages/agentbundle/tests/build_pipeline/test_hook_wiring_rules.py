"""Fail-closed rules for Claude-shaped hook wiring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from agentbundle.build.hook_wiring_rules import (
    KNOWN_EVENTS,
    PUBLISHABLE_EVENTS,
    collect_validated_claude_hooks,
)


def _pack(tmp_path: Path, command: str, *, event: str = "SessionStart", extra: str = "") -> Path:
    pack = tmp_path / "fixture-pack"
    (pack / ".apm" / "hooks").mkdir(parents=True)
    (pack / ".apm" / "hook-wiring").mkdir(parents=True)
    suffix = ".py" if command.split()[0].startswith("python") else ".sh"
    body_name = "run" + suffix
    (pack / ".apm" / "hooks" / body_name).write_text("pass\n", encoding="utf-8")
    (pack / ".apm" / "hook-wiring" / "one.toml").write_text(
        f"[[hooks.{event}]]\n"
        f"hooks = [{{ type = \"command\", command = {json.dumps(command)}{extra} }}]\n",
        encoding="utf-8",
    )
    return pack


def _collect(pack: Path):
    return collect_validated_claude_hooks(
        pack,
        repo_hook_prefix="tools/hooks/",
        hook_source_path=".apm/hooks/",
        wiring_source_path=".apm/hook-wiring/",
        pack_name=pack.name,
    )


def test_event_snapshot_and_restricted_split() -> None:
    assert len(KNOWN_EVENTS) == 31
    assert {
        "Setup",
        "PreToolUse",
        "PermissionRequest",
        "PermissionDenied",
    } == KNOWN_EVENTS - PUBLISHABLE_EVENTS
    snapshot_path = (
        Path(__file__).resolve().parents[4]
        / "docs"
        / "specs"
        / "claude-plugin-hook-parity"
        / "claude-code-2.1.226-hook-events.json"
    )
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert set(snapshot["accepted_events"]) == KNOWN_EVENTS
    assert set(snapshot["known_but_unpublishable"]) == KNOWN_EVENTS - PUBLISHABLE_EVENTS


@pytest.mark.parametrize(
    ("interpreter", "body"),
    [("python", "run.py"), ("python3", "run.py"), ("sh", "run.sh"), ("bash", "run.sh")],
)
def test_allowed_interpreter_suffix_pairs(tmp_path: Path, interpreter: str, body: str) -> None:
    pack = _pack(tmp_path, f"{interpreter} tools/hooks/{body}")
    assert _collect(pack)[0].body_name == body


def test_optional_leading_dot_slash_is_absorbed(tmp_path: Path) -> None:
    pack = _pack(tmp_path, "python ./tools/hooks/run.py")
    assert _collect(pack)[0].body_name == "run.py"


@pytest.mark.parametrize(
    "command",
    [
        "python3 -c tools/hooks/run.py",
        "python3 tools/hooks/run.py trailing",
        "ENV=x python3 tools/hooks/run.py",
        "python3 /tools/hooks/run.py",
        "python3 vendor/tools/hooks/run.py",
        "python3 tools/hooks/../hooks/run.py",
        "python3 tools/hooks/run.py;",
        "python3 $(tools/hooks/run.py)",
        "python3 `tools/hooks/run.py`",
        "python3 tools/hooks/run.sh",
    ],
)
def test_exact_command_grammar_rejects_expansion(tmp_path: Path, command: str) -> None:
    pack = _pack(tmp_path, command)
    with pytest.raises(ValueError, match=r"fixture-pack.*one\.toml.*command"):
        _collect(pack)


@pytest.mark.parametrize(
    "event", ["Setup", "PreToolUse", "PermissionRequest", "PermissionDenied"]
)
def test_known_control_events_are_unpublishable(tmp_path: Path, event: str) -> None:
    pack = _pack(tmp_path, "python tools/hooks/run.py", event=event)
    with pytest.raises(ValueError, match=rf"{event!s}.*known but unpublishable"):
        _collect(pack)


def test_unknown_event_is_distinct(tmp_path: Path) -> None:
    pack = _pack(tmp_path, "python tools/hooks/run.py", event="FutureEvent")
    with pytest.raises(ValueError, match=r"FutureEvent.*unknown Claude hook event"):
        _collect(pack)


def test_non_command_and_non_string_command_fail(tmp_path: Path) -> None:
    pack = _pack(tmp_path, "python tools/hooks/run.py")
    wiring = pack / ".apm" / "hook-wiring" / "one.toml"
    wiring.write_text(
        "[[hooks.SessionStart]]\n"
        'hooks = [{ type = "prompt", command = "python tools/hooks/run.py" }]\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="only command hooks"):
        _collect(pack)
    wiring.write_text(
        "[[hooks.SessionStart]]\n"
        'hooks = [{ type = "command", command = 7 }]\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="command must be a string"):
        _collect(pack)


def test_hook_body_basename_allowlist(tmp_path: Path) -> None:
    pack = _pack(tmp_path, "python tools/hooks/run.py")
    wiring = pack / ".apm" / "hook-wiring" / "one.toml"
    wiring.write_text(
        "[[hooks.SessionStart]]\n"
        'hooks = [{ type = "command", command = "python tools/hooks/a$bad.py" }]\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="basename is not portable"):
        _collect(pack)


@pytest.mark.parametrize("matcher", ["^Bash|Edit$", "Bash.*", "Bash||Edit", ""])
def test_matcher_allowlist(tmp_path: Path, matcher: str) -> None:
    pack = _pack(
        tmp_path,
        "python tools/hooks/run.py",
    )
    wiring = pack / ".apm" / "hook-wiring" / "one.toml"
    wiring.write_text(
        "[[hooks.SessionStart]]\n"
        f"matcher = {json.dumps(matcher)}\n"
        'hooks = [{ type = "command", command = "python tools/hooks/run.py" }]\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="matcher"):
        _collect(pack)


@pytest.mark.parametrize("timeout", [0, 61, -1, True])
def test_timeout_bounds(tmp_path: Path, timeout: object) -> None:
    rendered = str(timeout).lower() if isinstance(timeout, bool) else str(timeout)
    pack = _pack(
        tmp_path,
        "python tools/hooks/run.py",
        extra=f", timeout = {rendered}",
    )
    with pytest.raises(ValueError, match="timeout"):
        _collect(pack)


def test_missing_body_fails_locating(tmp_path: Path) -> None:
    pack = _pack(tmp_path, "python tools/hooks/run.py")
    body = pack / ".apm" / "hooks" / "run.py"
    body.unlink()
    with pytest.raises(ValueError, match=r"fixture-pack.*one\.toml.*missing"):
        _collect(pack)


def test_symlinked_body_fails_locating(tmp_path: Path) -> None:
    pack = _pack(tmp_path, "python tools/hooks/run.py")
    body = pack / ".apm" / "hooks" / "run.py"
    body.unlink()
    target = tmp_path / "outside.py"
    target.write_text("pass\n", encoding="utf-8")
    try:
        body.symlink_to(target)
    except OSError:
        pytest.skip("symlinks not available")
    with pytest.raises(ValueError, match="symlinked"):
        _collect(pack)


def test_flat_and_lowercase_adapter_shapes_are_skipped(tmp_path: Path) -> None:
    pack = tmp_path / "fixture-pack"
    wiring = pack / ".apm" / "hook-wiring"
    wiring.mkdir(parents=True)
    (wiring / "other.toml").write_text(
        '[[hooks.UserPromptSubmit]]\ncommand = "$HOOK_BODY_PATH"\n'
        '[[hooks.agentSpawn]]\ncommand = "tools/hooks/run.sh"\n',
        encoding="utf-8",
    )
    assert _collect(pack) == []


@pytest.mark.parametrize("count", [4, 5])
def test_per_event_fanout_boundary(tmp_path: Path, count: int) -> None:
    pack = _pack(tmp_path, "python tools/hooks/run.py")
    hooks = ",\n".join(
        '{ type = "command", command = "python tools/hooks/run.py" }'
        for _ in range(count)
    )
    (pack / ".apm" / "hook-wiring" / "one.toml").write_text(
        f"[[hooks.SessionStart]]\nhooks = [{hooks}]\n", encoding="utf-8"
    )
    if count == 4:
        assert len(_collect(pack)) == 4
    else:
        with pytest.raises(ValueError, match="more than 4"):
            _collect(pack)


@pytest.mark.parametrize("count", [16, 17])
def test_per_pack_fanout_boundary(tmp_path: Path, count: int) -> None:
    pack = _pack(tmp_path, "python tools/hooks/run.py")
    events = sorted(PUBLISHABLE_EVENTS - {"SessionStart"})[: count - 4]
    blocks = [
        "[[hooks.SessionStart]]\n"
        "hooks = [\n"
        + ",\n".join(
            '  { type = "command", command = "python tools/hooks/run.py" }'
            for _ in range(4)
        )
        + "\n]\n"
    ]
    blocks.extend(
        f"[[hooks.{event}]]\n"
        'hooks = [{ type = "command", command = "python tools/hooks/run.py" }]\n'
        for event in events
    )
    (pack / ".apm" / "hook-wiring" / "one.toml").write_text(
        "\n".join(blocks), encoding="utf-8"
    )
    if count == 16:
        assert len(_collect(pack)) == 16
    else:
        with pytest.raises(ValueError, match="more than 16"):
            _collect(pack)
