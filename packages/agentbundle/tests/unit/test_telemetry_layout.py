"""Tests for repository-first loop telemetry configuration wiring."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.file_safety import (
    BoundExceeded,
    UnsafeContentError,
)
from agentbundle.telemetry_layout import _DELIVERABLE, MAX_LAYOUT_BYTES, resolve

FIXTURES = Path(__file__).parents[1] / "fixtures" / "telemetry-layout"


def _copy_layout_fixtures(tmp_path: Path) -> tuple[Path, Path]:
    """Copy the two checked-in layout fixtures in; return the two ROOTS.

    `resolve` derives each filename itself, so a test that needs the user file
    builds it the same way the resolver does.
    """
    repo_root = tmp_path / "repo"
    user_root = tmp_path / "user"
    repo_root.mkdir()
    user_root.mkdir()
    shutil.copyfile(
        FIXTURES / "repo-agentbundle-layout.toml",
        repo_root / "agentbundle-layout.toml",
    )
    user_path = user_root / "agentbundle-layout.toml"
    shutil.copyfile(
        FIXTURES / "user-agentbundle-layout.toml",
        user_path,
    )
    return repo_root, user_root


def test_the_caller_cannot_choose_which_user_file_is_read(tmp_path: Path) -> None:
    """The user scope names a ROOT; the resolver derives the filename.

    An earlier signature took the user file's path and confined it against its
    own parent, which confines nothing: every absolute path passes a check whose
    root is its own directory. The caller chose the file and the resolver only
    guaranteed it opened safely. This pins that the filename is ours.
    """
    repo_root, user_root = _copy_layout_fixtures(tmp_path)
    (repo_root / "agentbundle-layout.toml").write_text(
        "[telemetry]\n", encoding="utf-8", newline="\n"
    )
    # a second, differently-named file sitting in the same root
    (user_root / "private.toml").write_text(
        '[telemetry]\nendpoint = "https://attacker.example:4318"\n',
        encoding="utf-8",
        newline="\n",
    )

    resolved = resolve(repo_root, user_root)

    assert "https://attacker.example:4318" not in str(resolved.arguments)
    assert resolved.settings.get("endpoint") != "https://attacker.example:4318"


def test_resolve_merges_each_setting_repository_first(tmp_path: Path) -> None:
    """Repository values win while omitted values fall back to user scope."""
    repo_root, user_root = _copy_layout_fixtures(tmp_path)

    resolved = resolve(repo_root, user_root)

    assert resolved.settings == {
        "endpoint": "https://repo-collector.example:4318",
        "service_name": "work-loop-user",
    }
    assert resolved.config_path == repo_root / "agentbundle-layout.toml"


def test_resolve_renders_repository_event_input_and_sender_flags(tmp_path: Path) -> None:
    """AC-0043: the documented invocation resolves `--input` to the repository
    root's `.loop-run/events.jsonl`.

    Also pins the rest of the rendered argument vector, so a flag that stops
    being emitted fails here rather than at the Collector.
    """
    repo_root, user_root = _copy_layout_fixtures(tmp_path)

    resolved = resolve(repo_root, user_root)

    assert resolved.arguments == (
        "--input",
        str(repo_root / ".loop-run" / "events.jsonl"),
        "--root",
        str(repo_root),
        "--config",
        str(repo_root / "agentbundle-layout.toml"),
        "--profile",
        str(
            repo_root
            / "packs"
            / "core"
            / ".apm"
            / "skills"
            / "work-loop"
            / "profiles"
            / "work-loop.toml"
        ),
        "--service-name",
        "work-loop-user",
    )


def test_merged_setting_reaches_the_invocation_not_only_the_settings_dict(
    tmp_path: Path,
) -> None:
    """AC-0041 is about the documented INVOCATION, not the resolver's dict.

    `--config` names one file and the sender reads only `[telemetry].endpoint`
    from it. So when the user file wins the endpoint, a repository-declared
    `service_name` reaches the sender only if it is rendered as a flag. Without
    that, the merge is computed and then discarded, and the sender silently uses
    a different service name than the repository asked for.
    """
    repo_root, user_root = _copy_layout_fixtures(tmp_path)
    user_path = user_root / "agentbundle-layout.toml"
    (repo_root / "agentbundle-layout.toml").write_text(
        '[telemetry]\nservice_name = "work-loop-repo"\n',
        encoding="utf-8",
        newline="\n",
    )

    resolved = resolve(repo_root, user_root)

    # the endpoint came from the user file ...
    config_index = resolved.arguments.index("--config")
    assert resolved.arguments[config_index + 1] == str(user_path)
    # ... while the repository's service_name still reaches the sender.
    name_index = resolved.arguments.index("--service-name")
    assert resolved.arguments[name_index + 1] == "work-loop-repo"


_UNDELIVERABLE = "compression"


def test_the_setting_the_refusal_controls_use_really_has_no_route() -> None:
    """Name the assumption the two refusal controls rest on.

    They refuse a setting the sender cannot receive. If the sender grew a route
    for it, those controls would fail -- loudly, not silently, because they expect
    a raise. This test exists so the failure explains itself: the behaviour is
    still correct and the *test data* needs a different setting.
    """
    assert _UNDELIVERABLE not in _DELIVERABLE, (
        f"{_UNDELIVERABLE!r} now has a route to the sender, so the refusal "
        "controls below no longer exercise a refusal. Pick a setting that still "
        "has no route; the behaviour itself is unaffected."
    )


def test_resolve_refuses_a_setting_the_sender_cannot_receive(tmp_path: Path) -> None:
    """A setting with no route to the sender is refused, never dropped quietly.

    These settings decide where data is sent, so a silently ignored one fails
    open: the adopter believes they configured something that does nothing.
    """
    repo_root, user_root = _copy_layout_fixtures(tmp_path)
    (repo_root / "agentbundle-layout.toml").write_text(
        '[telemetry]\nendpoint = "https://repo.example:4318"\ncompression = "gzip"\n',
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(ValueError, match="compression"):
        resolve(repo_root, user_root)


def test_resolve_refuses_an_undeliverable_setting_from_the_user_scope(
    tmp_path: Path,
) -> None:
    """The refusal covers a setting from EITHER scope, not just the repository's.

    The merge pulls a user-scope value in whenever the repository file omits it,
    so a setting with no route can arrive from either side. A control that only
    exercised the repository side would leave the user side silently dropping it
    — and the user file is the one this catalogue trusts less.
    """
    repo_root, user_root = _copy_layout_fixtures(tmp_path)
    user_path = user_root / "agentbundle-layout.toml"
    (repo_root / "agentbundle-layout.toml").write_text(
        '[telemetry]\nendpoint = "https://repo.example:4318"\n',
        encoding="utf-8",
        newline="\n",
    )
    user_path.write_text(
        '[telemetry]\ncompression = "gzip"\n', encoding="utf-8", newline="\n"
    )

    with pytest.raises(ValueError, match="compression"):
        resolve(repo_root, user_root)


def test_resolve_uses_user_config_when_repo_omits_endpoint(tmp_path: Path) -> None:
    """The one-config sender receives the file that owns the endpoint setting."""
    repo_root, user_root = _copy_layout_fixtures(tmp_path)
    user_path = user_root / "agentbundle-layout.toml"
    (repo_root / "agentbundle-layout.toml").write_text(
        '[telemetry]\nservice_name = "work-loop-repo"\n',
        encoding="utf-8",
        newline="\n",
    )

    resolved = resolve(repo_root, user_root)

    assert resolved.settings["endpoint"] == "https://user-collector.example:4318"
    assert resolved.settings["service_name"] == "work-loop-repo"
    assert resolved.config_path == user_path
    config_index = resolved.arguments.index("--config")
    assert resolved.arguments[config_index + 1] == str(user_path)


@pytest.mark.parametrize(
    "body",
    (
        '[telemetry]\nendpoint = ["not", "a", "string"]\n',
        '[telemetry]\nendpoint = "unterminated\n',
    ),
)
def test_resolve_rejects_invalid_user_layout(tmp_path: Path, body: str) -> None:
    """Unparseable or wrongly typed user settings cannot select a destination."""
    repo_root = tmp_path / "repo"
    user_root = tmp_path / "user"
    repo_root.mkdir()
    user_root.mkdir()
    (repo_root / "agentbundle-layout.toml").write_text(
        "[telemetry]\n", encoding="utf-8", newline="\n"
    )
    user_path = user_root / "agentbundle-layout.toml"
    user_path.write_text(body, encoding="utf-8", newline="\n")

    with pytest.raises(ValueError):
        resolve(repo_root, user_root)


def test_resolve_rejects_oversized_user_layout(tmp_path: Path) -> None:
    """The user-scope read is bounded before TOML parsing."""
    repo_root = tmp_path / "repo"
    user_root = tmp_path / "user"
    repo_root.mkdir()
    user_root.mkdir()
    (repo_root / "agentbundle-layout.toml").write_text(
        "[telemetry]\n", encoding="utf-8", newline="\n"
    )
    user_path = user_root / "agentbundle-layout.toml"
    user_path.write_bytes(b" " * (MAX_LAYOUT_BYTES + 1))

    with pytest.raises(BoundExceeded):
        resolve(repo_root, user_root)


def test_resolve_rejects_user_layout_symlink(tmp_path: Path) -> None:
    """A user layout symlink is refused rather than followed."""
    repo_root = tmp_path / "repo"
    user_root = tmp_path / "user"
    repo_root.mkdir()
    user_root.mkdir()
    (repo_root / "agentbundle-layout.toml").write_text(
        "[telemetry]\n", encoding="utf-8", newline="\n"
    )
    target = tmp_path / "outside.toml"
    target.write_text(
        '[telemetry]\nendpoint = "https://outside.example"\n',
        encoding="utf-8",
        newline="\n",
    )
    user_path = user_root / "agentbundle-layout.toml"
    try:
        user_path.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable")

    with pytest.raises(UnsafeContentError):
        resolve(repo_root, user_root)
